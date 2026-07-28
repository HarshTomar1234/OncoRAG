# OncoRAG

Production-grade RAG + agentic oncology knowledge system, built on Weaviate.

Real oncology data (CIViC, ClinicalTrials.gov, openFDA) in a Weaviate hybrid
search index, tuned empirically against a golden eval set, behind a
transparent, citation-backed LLM agent (Claude Sonnet 5) — every answer
comes with the full search trace and the actual sources behind it, not a
black-box response. Covers five cancers: NSCLC, breast, colorectal,
melanoma, and AML.

Built in phases, each with its own spec/eval and a PR: see `docs/` for the
full history (gitignored — internal planning notes, not published).

## Run it

Requires a `.env` with `WEAVIATE_URL`, `WEAVIATE_API_KEY`, `OPENFDA_API_KEY`,
`ANTHROPIC_API_KEY`, and `API_SECRET` (see `.env.example`) — the schema and
data must already be populated (`scripts/create_schema.py`,
`scripts/ingest.py`).

```bash
docker build -t oncorag-api .
docker run --env-file .env -p 8000:8000 oncorag-api
```

Then open `http://localhost:8000`.

## Architecture

```
static/index.html  →  FastAPI (/chat, /health)  →  agent tool-use loop
                                                      ├── Weaviate hybrid search
                                                      └── Claude Sonnet 5
```

- `src/oncorag/ingestion/` — CIViC/ClinicalTrials.gov/openFDA clients, chunking
- `src/oncorag/retrieval/` — Weaviate schema, tuned hybrid search
- `src/oncorag/agent/` — the tool-use loop, citations, safety framing
- `src/oncorag/api/` — FastAPI surface
- `static/` — the chat UI
