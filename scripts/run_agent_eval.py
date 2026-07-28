"""Phase 3 agent eval - tests synthesis, not just retrieval (Phase 2 already
covered retrieval quality). Real Anthropic API calls, run once (not
repeated for variance - unlike Weaviate, each call costs real money; see
docs/eval/phase3_results.md for that tradeoff stated plainly).

Four checks, per docs/phase-3-agent-layer.md:
1. ID-matching: citations trace back to a real object matching a golden-set
   key_value.
2. Grounding/field-echo: closed-vocabulary claims in the answer (evidence
   level, direction, trial phase/status) must appear in what was actually
   retrieved that turn.
3. Tools-disabled baseline over the same 28 questions.
4. ~5 unanswerable questions - printed in full for manual read, per the
   same "read the failures, don't over-automate at this sample size"
   philosophy as the Phase 2 eval.
"""

import json
import re
from pathlib import Path

import anthropic

from oncorag.agent.agent import run_agent
from oncorag.config.settings import settings
from oncorag.retrieval.client import weaviate_client

DOCS_EVAL = Path(__file__).resolve().parent.parent / "docs" / "eval"

# Closed-vocabulary values worth field-echo checking, mapped to the
# KnowledgeObject property they'd have to come from.
CLOSED_VOCAB = {
    "evidence_level": ["level a", "level b", "level c", "level d", "level e"],
    "evidence_direction": ["supports", "does not support"],
    "overall_status": [
        "recruiting", "completed", "terminated", "withdrawn",
        "active, not recruiting", "not yet recruiting", "suspended",
    ],
    "phase": ["phase 1", "phase 2", "phase 3", "phase 4", "phase i", "phase ii", "phase iii", "phase iv"],
}


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def id_match(entry: dict, citations: list[dict]) -> bool:
    expected_refs = {f"{entry['object_type']}:{kv}" for kv in entry["key_values"]}
    actual_refs = {c["ref"] for c in citations}
    return bool(expected_refs & actual_refs)


def grounding_check(answer: str, retrieved_by_ref: dict) -> list[str]:
    """Returns a list of closed-vocab mentions in the answer that don't
    appear in ANY retrieved object's properties this turn - i.e. unsupported
    claims about a structured fact."""
    answer_lower = answer.lower()
    retrieved_values = set()
    for props in retrieved_by_ref.values():
        for value in props.values():
            if isinstance(value, str):
                retrieved_values.add(value.lower())

    unsupported = []
    for _field, values in CLOSED_VOCAB.items():
        for value in values:
            if re.search(rf"\b{re.escape(value)}\b", answer_lower):
                if not any(value in rv for rv in retrieved_values):
                    unsupported.append(value)
    return unsupported


def main() -> None:
    realistic = load_jsonl(DOCS_EVAL / "golden_set_realistic.jsonl")
    unanswerable = load_jsonl(DOCS_EVAL / "unanswerable_set.jsonl")

    anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    with weaviate_client() as client:
        print("=== 1+2+3: realistic set, tools enabled vs. disabled ===\n")
        id_hits = 0
        grounding_clean = 0
        tool_call_count = 0
        for i, entry in enumerate(realistic):
            with_tools = run_agent(client, anthropic_client, entry["question"], use_tools=True)
            without_tools = run_agent(client, anthropic_client, entry["question"], use_tools=False)

            hit = id_match(entry, with_tools.citations)
            unsupported = grounding_check(with_tools.answer, with_tools.retrieved_by_ref)
            called_tool = len(with_tools.trace) > 0

            id_hits += int(hit)
            grounding_clean += int(not unsupported)
            tool_call_count += int(called_tool)

            print(f"[{i+1}/{len(realistic)}] {entry['question'][:70]}")
            print(f"    tool_called={called_tool} id_match={hit} unsupported_claims={unsupported}")
            print(f"    with_tools : {with_tools.answer[:150]!r}")
            print(f"    no_tools   : {without_tools.answer[:150]!r}")
            print()

        n = len(realistic)
        print(f"\nTool-call rate: {tool_call_count}/{n}")
        print(f"ID-match rate (citations trace to a real correct object): {id_hits}/{n}")
        print(f"Grounding-clean rate (no unsupported closed-vocab claims): {grounding_clean}/{n}")

        print("\n=== 4: unanswerable questions (read manually, not auto-scored) ===\n")
        for entry in unanswerable:
            result = run_agent(client, anthropic_client, entry["question"], use_tools=True)
            print(f"Q: {entry['question']}")
            print(f"   (why unanswerable: {entry['reason']})")
            print(f"   tool_called={len(result.trace) > 0}")
            print(f"   A: {result.answer[:400]!r}")
            print()


if __name__ == "__main__":
    main()
