"""Runs a golden-set eval file against Weaviate and returns per-question
ranks, scored two ways:

- strict: the returned object's own object_type must match the question's
  expected object_type.
- lenient: any returned object whose own key_field value matches an
  acceptable answer counts, even if it's a chunk (drug_label_chunk /
  trial_eligibility_chunk carry their parent's nct_id/drug_name directly -
  see transform.py - so no reference traversal is needed to check this).

Reported separately, not blended: the gap between them is itself a finding
(see docs/phase-2-retrieval-core.md).
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from oncorag.retrieval.search import SearchConfig, hybrid_search


@dataclass
class GoldenEntry:
    question: str
    object_type: str
    key_field: str
    key_values: list[str]


def load_golden_set(path: Path) -> list[GoldenEntry]:
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entries.append(
                GoldenEntry(
                    question=data["question"],
                    object_type=data["object_type"],
                    key_field=data["key_field"],
                    key_values=data["key_values"],
                )
            )
    return entries


def _rank_of_match(objects, entry: GoldenEntry, strict: bool) -> Optional[int]:
    for rank, obj in enumerate(objects, start=1):
        props = obj.properties
        if strict and props.get("object_type") != entry.object_type:
            continue
        if props.get(entry.key_field) in entry.key_values:
            return rank
    return None


@dataclass
class EvalResult:
    strict_ranks: list[Optional[int]]
    lenient_ranks: list[Optional[int]]
    object_types: list[str]


def run_eval(client, entries: list[GoldenEntry], config: SearchConfig) -> EvalResult:
    strict_ranks = []
    lenient_ranks = []
    object_types = []
    for entry in entries:
        result = hybrid_search(client, entry.question, config)
        strict_ranks.append(_rank_of_match(result.objects, entry, strict=True))
        lenient_ranks.append(_rank_of_match(result.objects, entry, strict=False))
        object_types.append(entry.object_type)
    return EvalResult(strict_ranks=strict_ranks, lenient_ranks=lenient_ranks, object_types=object_types)
