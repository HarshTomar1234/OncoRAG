"""FastAPI surface for the Phase 3 agent.

Weaviate/Anthropic clients are opened once at startup (lifespan) and shared
across requests - concurrent queries on one shared WeaviateClient are
explicitly tested safe by the client's own test suite (only batch-insert
*results*, which this API never touches, are documented as not
thread-safe). Endpoints are plain `def`, not `async def`, so FastAPI
dispatches each request to its threadpool - required since both the
Weaviate and Anthropic calls inside run_agent() are blocking I/O, which
would otherwise stall the event loop.
"""

import logging
import time
from contextlib import asynccontextmanager

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
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    with weaviate_client() as w_client:
        app.state.weaviate_client = w_client
        app.state.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        yield


app = FastAPI(title="OncoRAG", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

bearer_scheme = HTTPBearer()


def require_api_secret(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> None:
    if credentials.credentials != settings.api_secret:
        raise HTTPException(status_code=401, detail="Invalid or missing API secret")


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


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_secret)])
def chat(request: Request, body: ChatRequest) -> ChatResponse:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")

    result = run_agent(
        request.app.state.weaviate_client,
        request.app.state.anthropic_client,
        body.question,
    )
    logger.info("chat: question_len=%d tool_calls=%d", len(body.question), len(result.trace))
    return ChatResponse(answer=result.answer, trace=result.trace, citations=result.citations)
