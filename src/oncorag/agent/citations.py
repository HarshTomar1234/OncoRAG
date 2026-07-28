"""Shared object-reference and citation helpers.

No single "id" property exists across all six KnowledgeObject object_types
(civic_id only on evidence_item, nct_id only on clinical_trial/
trial_eligibility_chunk, drug_name only on drug_label/drug_label_chunk,
gene_name only on gene) - object_ref() is the one place that mapping lives,
reused for the agent's trace, its citations list, and eval matching.
"""

KEY_FIELD = {
    "gene": "gene_name",
    "evidence_item": "civic_id",
    "clinical_trial": "nct_id",
    "drug_label": "drug_name",
    "drug_label_chunk": "drug_name",
    "trial_eligibility_chunk": "nct_id",
}


def object_ref(props: dict) -> str:
    object_type = props.get("object_type", "unknown")
    key_field = KEY_FIELD.get(object_type)
    key_value = props.get(key_field) if key_field else None
    return f"{object_type}:{key_value or ''}"


def build_citation(props: dict) -> dict:
    object_type = props.get("object_type", "unknown")
    citation = {"ref": object_ref(props), "object_type": object_type}

    if object_type == "evidence_item":
        citation["source_citation"] = props.get("source_citation", "")
        citation["source_url"] = props.get("source_url", "")
        citation["source_pmid"] = props.get("source_pmid", "")
    elif object_type in ("clinical_trial", "trial_eligibility_chunk"):
        citation["nct_id"] = props.get("nct_id", "")
        citation["title"] = props.get("title", "")
    elif object_type in ("drug_label", "drug_label_chunk"):
        citation["drug_name"] = props.get("drug_name", "")
        citation["manufacturer_name"] = props.get("manufacturer_name", "")
    elif object_type == "gene":
        citation["gene_name"] = props.get("gene_name", "")

    return citation
