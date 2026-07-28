"""The agent's one tool: search the oncology knowledge base.

A second "get object by ID" tool was considered and rejected as YAGNI -
citations come from objects the agent already retrieved and holds in the
trace; verifying one is a dict lookup, not a real need for another round
trip to Weaviate.
"""

from oncorag.agent.citations import object_ref
from oncorag.retrieval.search import SearchConfig, hybrid_search

TOOL_NAME = "search_oncology_knowledge_base"

# Chunk types are internal chunking artifacts (Phase 1), not something the
# model should reason about directly - keeping them out of the enum keeps
# the model's mental model to the four "real" record types.
SEARCHABLE_OBJECT_TYPES = ["gene", "evidence_item", "clinical_trial", "drug_label"]

TOOL_SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Search the oncology knowledge base - real CIViC clinical evidence, "
        "ClinicalTrials.gov trials, and openFDA drug labels for 5 cancers "
        "(NSCLC, breast, colorectal, melanoma, AML). Call this whenever you "
        "need factual information to answer - never answer oncology "
        "questions from memory. Call it multiple times, with different "
        "focused queries, to cover each part of a compound question."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A focused natural-language search query for one specific fact or question.",
            },
            "object_type": {
                "type": "string",
                "enum": SEARCHABLE_OBJECT_TYPES,
                "description": "Optional: restrict results to one record type if you already know which kind you need.",
            },
        },
        "required": ["query"],
    },
}


def run_search_tool(client, tool_input: dict) -> tuple[str, dict, list[dict]]:
    """Executes the search. Returns (text for Claude, trace entry, retrieved
    object properties - the latter feeds citations and eval grounding
    checks, not just the model)."""
    object_type = tool_input.get("object_type")

    try:
        query = tool_input["query"]
        config = SearchConfig()  # tuned Phase 2 default - not model-configurable
        result = hybrid_search(client, query, config, object_type=object_type)
    except Exception as exc:
        # Covers both a Weaviate error and a malformed tool call (e.g. a
        # missing "query" key) - either way this must not crash the agent
        # loop or silently look like an empty result the model could
        # mistake for "nothing found".
        trace_entry = {
            "query": tool_input.get("query"),
            "object_type_filter": object_type,
            "result_count": 0,
            "top_result_ids": [],
            "error": str(exc),
        }
        return f"Search failed: {exc}. Do not answer this as if nothing was found - tell the user the lookup failed.", trace_entry, []

    lines = []
    result_refs = []
    retrieved_props = []
    for obj in result.objects:
        props = obj.properties
        ref = object_ref(props)
        result_refs.append(ref)
        retrieved_props.append(props)
        content = (props.get("content_text") or "")[:500]
        lines.append(f"[{ref}] ({props.get('object_type')}) {content}")

    text = "\n\n".join(lines) if lines else "No matching records found."
    trace_entry = {
        "query": query,
        "object_type_filter": object_type,
        "result_count": len(result.objects),
        "top_result_ids": result_refs,
    }
    return text, trace_entry, retrieved_props
