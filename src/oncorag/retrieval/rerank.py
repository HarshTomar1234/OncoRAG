"""Local, free cross-encoder reranking (no API key, runs on CPU).

Feeds the reranker a composed string of the object's identifying
structured properties plus content_text - not content_text alone. For an
evidence_item, content_text is CIViC's free-text description, which often
doesn't literally name the variant/disease/therapy; handing the reranker
only that text would mean scoring it against terms it structurally can't
contain.
"""

from sentence_transformers import CrossEncoder

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(_MODEL_NAME)
    return _model


def compose_rerank_text(properties: dict) -> str:
    object_type = properties.get("object_type", "")
    content_text = properties.get("content_text", "") or ""

    if object_type == "evidence_item":
        therapies = ", ".join(properties.get("therapy_names") or [])
        prefix = f"{properties.get('variant_name', '')} in {properties.get('disease_name', '')}. Therapies: {therapies}."
    elif object_type == "clinical_trial":
        conditions = ", ".join(properties.get("conditions") or [])
        prefix = f"{properties.get('title', '')}. Conditions: {conditions}."
    elif object_type in ("drug_label", "drug_label_chunk"):
        prefix = f"{properties.get('drug_name', '')}."
    elif object_type == "gene":
        prefix = f"{properties.get('gene_name', '')}."
    elif object_type == "trial_eligibility_chunk":
        prefix = f"Trial {properties.get('nct_id', '')} eligibility."
    else:
        prefix = ""

    return f"{prefix} {content_text}".strip()


def rerank(query: str, objects: list, top_k: int) -> list:
    """objects: Weaviate query result objects (each with .properties).
    Returns the same objects, reordered, truncated to top_k."""
    if not objects:
        return objects
    model = _get_model()
    pairs = [(query, compose_rerank_text(obj.properties)) for obj in objects]
    scores = model.predict(pairs)
    ranked = [obj for _, obj in sorted(zip(scores, objects), key=lambda x: x[0], reverse=True)]
    return ranked[:top_k]
