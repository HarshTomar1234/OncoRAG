"""Builds docs/eval/golden_set.jsonl from the objects actually sitting in
Weaviate right now - not hand-typed guesses. Each line is a
question -> expected-object pair for retrieval evaluation in Phase 2.

Stores natural-key identifiers (civic_id / nct_id / drug_name), not Weaviate
UUIDs, since UUIDs are ingest-run-specific but these are stable across
re-ingestion (see pipeline.py's deterministic UUID generation).
"""

import json
from pathlib import Path

from weaviate.classes.query import Filter

from oncorag.retrieval.client import weaviate_client

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "eval" / "golden_set.jsonl"

DISEASES = [
    "Lung Non-small Cell Carcinoma",
    "Breast Cancer",
    "Colorectal Cancer",
    "Melanoma",
    "Acute Myeloid Leukemia",
]
EVIDENCE_PER_DISEASE = 15
TRIAL_SAMPLE = 10
DRUG_SAMPLE = 10


def _evidence_question(props: dict) -> str:
    therapies = ", ".join(props.get("therapy_names") or []) or "no listed therapy"
    return (
        f"What evidence links {props['variant_name']} in "
        f"{props['disease_name']} to {therapies}?"
    )


def _trial_question(props: dict) -> str:
    conditions = ", ".join(props.get("conditions", [])[:2])
    return f"Is there a clinical trial for {conditions} titled roughly '{props['title']}'?"


def _drug_question(props: dict) -> str:
    return f"What is the mechanism of action and indication for {props['drug_name']}?"


def main() -> None:
    entries = []
    with weaviate_client() as client:
        collection = client.collections.get("KnowledgeObject")

        for disease in DISEASES:
            result = collection.query.fetch_objects(
                filters=Filter.by_property("object_type").equal("evidence_item")
                & Filter.by_property("disease_name").like(f"*{disease.split()[0]}*"),
                limit=EVIDENCE_PER_DISEASE,
            )
            for obj in result.objects:
                p = obj.properties
                entries.append(
                    {
                        "question": _evidence_question(p),
                        "object_type": "evidence_item",
                        "key_field": "civic_id",
                        "key_value": p["civic_id"],
                    }
                )

        trials = collection.query.fetch_objects(
            filters=Filter.by_property("object_type").equal("clinical_trial"),
            limit=TRIAL_SAMPLE,
        )
        for obj in trials.objects:
            p = obj.properties
            entries.append(
                {
                    "question": _trial_question(p),
                    "object_type": "clinical_trial",
                    "key_field": "nct_id",
                    "key_value": p["nct_id"],
                }
            )

        drugs = collection.query.fetch_objects(
            filters=Filter.by_property("object_type").equal("drug_label"),
            limit=DRUG_SAMPLE,
        )
        for obj in drugs.objects:
            p = obj.properties
            entries.append(
                {
                    "question": _drug_question(p),
                    "object_type": "drug_label",
                    "key_field": "drug_name",
                    "key_value": p["drug_name"],
                }
            )

    # Several distinct records can independently generate the exact same
    # question text (e.g. multiple CIViC evidence items supporting the same
    # gene+variant+disease+drug claim). Group those into one entry with all
    # acceptable answers, so a correct-but-different retrieval isn't scored
    # as wrong during Phase 2 evaluation.
    grouped: dict[str, dict] = {}
    for entry in entries:
        key = entry["question"]
        if key not in grouped:
            grouped[key] = {
                "question": entry["question"],
                "object_type": entry["object_type"],
                "key_field": entry["key_field"],
                "key_values": [],
            }
        grouped[key]["key_values"].append(entry["key_value"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for entry in grouped.values():
            f.write(json.dumps(entry) + "\n")

    print(f"Wrote {len(grouped)} golden-set entries ({len(entries)} source records) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
