# OncoPilot

Production-grade RAG + agentic oncology knowledge system, built on Weaviate.

**Status: active rebuild.** The previous version of this repo was a regex/
keyword-based MongoDB query router with mock fallback data — no real vector
search, retrieval, or LLM agent reasoning behind it. It's being rebuilt from
scratch on top of Weaviate: real oncology data (CIViC, ClinicalTrials.gov,
openFDA, PubMed), tuned hybrid search, and a transparent, citation-backed
agent layer.

Work is tracked in phases; details will land here as each phase ships.
