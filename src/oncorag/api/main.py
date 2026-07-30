"""FastAPI surface for the Phase 3 agent.

Weaviate/Anthropic clients are opened once at startup (lifespan) and shared
across requests - concurrent queries on one shared WeaviateClient are
explicitly tested safe by the client's own test suite (only batch-insert
*results*, which this API never touches, are documented as not
thread-safe). Endpoints are plain `def`, not `async def`, so FastAPI
dispatches each request to its threadpool - required since both the
Weaviate and Anthropic calls inside run_agent() are blocking I/O, which
would otherwise stall the event loop.

Access model (Phase 5 revision, after a security-tradeoff review): a
shared secret typed into the UI doesn't actually bound cost - it's public
after the first forward, and it's exactly the friction that defeats a
"click the link and try it" portfolio demo. Replaced with per-IP + global
daily rate limits (in-memory, single-instance - fine for this scale). The
secret still exists as an admin bypass (Authorization: Bearer <secret>
skips the limits) for this project's own eval/red-team scripts.
"""

import hmac
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from oncorag.agent.agent import run_agent
from oncorag.config.settings import settings
from oncorag.retrieval.client import weaviate_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = "static"
EXAMPLE_QUESTIONS = [
    "What treatment options are supported by evidence for BRAF V600E mutated melanoma?",
    "What is the standard targeted therapy for FLT3-mutated acute myeloid leukemia?",
    "What serious immune-related side effects should patients on pembrolizumab watch for?",
    "Are there clinical trials for MET overexpression in NSCLC?",
    "What treatment options are supported by evidence for HER2-positive breast cancer?",
    "What is the significance of KRAS mutation status for anti-EGFR therapy in colorectal cancer?",
    "What is the difference in indication between midostaurin and gilteritinib?",
    "What warnings and precautions are listed for pembrolizumab?",
    "Are there active recruiting trials for FLT3-mutated AML?",
    "What resistance mechanisms are documented for osimertinib in EGFR-mutated NSCLC?",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    with weaviate_client() as w_client:
        app.state.weaviate_client = w_client
        app.state.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        yield


app = FastAPI(title="OncoRAG", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# auto_error=False: an absent Authorization header is the normal, expected
# case for a public visitor - they're rate-limited below, not rejected.
bearer_scheme = HTTPBearer(auto_error=False)

PER_IP_DAILY_LIMIT = 20
GLOBAL_DAILY_LIMIT = 250
_rate_limit_state = {"day": None, "per_ip": defaultdict(int), "global": 0}


def is_privileged(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> bool:
    if credentials is None:
        return False
    return hmac.compare_digest(credentials.credentials.encode(), settings.api_secret.encode())


def _client_ip(request: Request) -> str:
    # Most hosting platforms *append* to X-Forwarded-For rather than
    # replacing it, so a client that sends its own XFF value can still
    # land at index 0 even behind a real proxy - meaning the per-IP cap is
    # a soft, spoofable signal in any deployment, not just when run
    # directly without a proxy. GLOBAL_DAILY_LIMIT is the real ceiling;
    # this is an accepted limitation for a cost-bounding limit, not a
    # security boundary.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(request: Request) -> None:
    today = date.today()
    if _rate_limit_state["day"] != today:
        _rate_limit_state["day"] = today
        _rate_limit_state["per_ip"] = defaultdict(int)
        _rate_limit_state["global"] = 0

    if _rate_limit_state["global"] >= GLOBAL_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="This demo's quota for today is used up - check back tomorrow.")

    ip = _client_ip(request)
    if _rate_limit_state["per_ip"][ip] >= PER_IP_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="You've hit today's per-visitor limit for this demo.")

    _rate_limit_state["per_ip"][ip] += 1
    _rate_limit_state["global"] += 1


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    trace: list[dict]
    citations: list[dict]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/")
def index() -> FileResponse:
    return FileResponse(f"{STATIC_DIR}/index.html")


@app.get("/health")
def health(request: Request) -> dict:
    ready = request.app.state.weaviate_client.is_ready()
    return {"status": "ok" if ready else "weaviate_unreachable"}


@app.get("/examples")
def examples() -> list[str]:
    return EXAMPLE_QUESTIONS


@app.post("/chat", response_model=ChatResponse)
def chat(request: Request, body: ChatRequest, privileged: bool = Depends(is_privileged)) -> ChatResponse:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    if not privileged:
        _enforce_rate_limit(request)

    result = run_agent(
        request.app.state.weaviate_client,
        request.app.state.anthropic_client,
        body.question,
    )
    logger.info("chat: question_len=%d tool_calls=%d", len(body.question), len(result.trace))
    return ChatResponse(answer=result.answer, trace=result.trace, citations=result.citations)
