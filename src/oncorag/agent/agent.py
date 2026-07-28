"""The Phase 3 agent: a hand-rolled tool-use loop (not the Anthropic Tool
Runner - see docs/phase-3-agent-layer.md for why), because the transparency
contract needs every tool call's query/filter/results intercepted, which a
manual loop gives for free since it's the one executing the tool.
"""

from dataclasses import dataclass, field

import anthropic

from oncorag.agent.citations import build_citation, object_ref
from oncorag.agent.tools import TOOL_SCHEMA, run_search_tool
from oncorag.config.settings import settings

MODEL = "claude-sonnet-5"
MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """You are an oncology knowledge assistant over a real, curated database \
covering five cancers: NSCLC, breast, colorectal, melanoma, and AML. Your data comes from \
CIViC (clinical evidence), ClinicalTrials.gov, and openFDA drug labels.

Rules, non-negotiable:
- This is an informational/research tool, not clinical advice. Never give patient-specific \
recommendations.
- Always call the search tool before answering a factual oncology question. Never answer from \
memory - if you didn't retrieve it this turn, don't state it.
- Cite what you retrieved: reference the [object_type:id] tag shown with each search result \
for every claim.
- Never state a structured fact (evidence level, approval status, trial phase, direction) that \
isn't present in what you actually retrieved this turn.
- Trial location data is limited to a facility name only - there is no structured city/country \
field. Never make geographic or country-availability claims (e.g. "available in India") from \
facility names; if asked, say this data isn't reliably available.
- If nothing relevant is retrieved, say so plainly rather than guessing or filling the gap from \
general knowledge.
"""


@dataclass
class AgentResult:
    answer: str
    trace: list[dict] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)
    # Full retrieved properties keyed by ref - not needed by API consumers,
    # but the eval harness uses it for the grounding/field-echo check.
    retrieved_by_ref: dict[str, dict] = field(default_factory=dict)


def run_agent(weaviate_client, question: str, use_tools: bool = True) -> AgentResult:
    anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": question}]
    trace: list[dict] = []
    retrieved_by_ref: dict[str, dict] = {}
    tools = [TOOL_SCHEMA] if use_tools else []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = anthropic_client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
            output_config={"effort": "medium"},
        )

        if response.stop_reason != "tool_use":
            answer = next((b.text for b in response.content if b.type == "text"), "")
            citations = [build_citation(props) for props in retrieved_by_ref.values()]
            return AgentResult(
                answer=answer, trace=trace, citations=citations, retrieved_by_ref=retrieved_by_ref
            )

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            text, trace_entry, retrieved_props = run_search_tool(weaviate_client, block.input)
            trace.append(trace_entry)
            for props in retrieved_props:
                retrieved_by_ref[object_ref(props)] = props
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": text}
            )
        messages.append({"role": "user", "content": tool_results})

    # Hit the iteration cap without a final answer - return what we have rather than raising.
    citations = [build_citation(props) for props in retrieved_by_ref.values()]
    return AgentResult(
        answer="(Reached max tool-call iterations without a final answer.)",
        trace=trace,
        citations=citations,
        retrieved_by_ref=retrieved_by_ref,
    )
