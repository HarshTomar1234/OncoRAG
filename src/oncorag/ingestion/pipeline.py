"""Phase 1 ingestion pipeline: pulls real data for the 5-cancer vertical
slice from CIViC, ClinicalTrials.gov, and openFDA, and loads it into the
single KnowledgeObject collection.

Deliberately capped per source per cancer - a vertical-slice demo, not an
exhaustive import. Real numbers, chosen to stay well under the Weaviate
Cloud free tier's 2,000 embeddings/day allowance:
  5 cancers x up to 150 evidence items = 750 max
  5 cancers x up to 30 trials          = 150 max
  distinct genes/drugs encountered     = dedup'd, no cap needed at this scale
"""

import itertools
import logging

from weaviate.classes.data import DataObject
from weaviate.util import generate_uuid5

from oncorag.ingestion.civic_client import evidence_items_for_disease
from oncorag.ingestion.clinicaltrials_client import studies_for_condition
from oncorag.ingestion.openfda_client import labels_for_generic_name
from oncorag.ingestion.transform import (
    civic_evidence_to_objects,
    ctgov_study_to_objects,
    dedupe_by_key,
    openfda_label_to_objects,
)
from oncorag.retrieval.client import weaviate_client
from oncorag.retrieval.schema import COLLECTION_NAME

logger = logging.getLogger(__name__)

MAX_EVIDENCE_PER_DISEASE = 150
MAX_TRIALS_PER_DISEASE = 30

# (CIViC diseaseName filter value, ClinicalTrials.gov query.cond value)
# CIViC names verified via GraphQL introspection + real evidenceItems counts.
CANCERS = [
    ("Lung Non-small Cell Carcinoma", "non-small cell lung cancer"),
    ("Breast Cancer", "breast cancer"),
    ("Colorectal Cancer", "colorectal cancer"),
    ("Melanoma", "melanoma"),
    ("Acute Myeloid Leukemia", "acute myeloid leukemia"),
]


def _natural_key_uuid(object_type: str, natural_key: str) -> str:
    return generate_uuid5(f"{object_type}:{natural_key}")


def _uuid_for_object(obj: dict) -> str:
    object_type = obj["object_type"]
    if object_type == "gene":
        return _natural_key_uuid(object_type, obj["gene_name"])
    if object_type == "evidence_item":
        return _natural_key_uuid(object_type, obj["civic_id"])
    if object_type == "clinical_trial":
        return _natural_key_uuid(object_type, obj["nct_id"])
    if object_type == "drug_label":
        return _natural_key_uuid(object_type, obj["drug_name"])
    if object_type == "trial_eligibility_chunk":
        return _natural_key_uuid(object_type, f"{obj['nct_id']}:{obj['chunk_index']}")
    if object_type == "drug_label_chunk":
        return _natural_key_uuid(object_type, f"{obj['drug_name']}:{obj['chunk_index']}")
    raise ValueError(f"Unknown object_type: {object_type}")


def _parent_uuid_for_chunk(obj: dict) -> str:
    if obj["object_type"] == "trial_eligibility_chunk":
        return _natural_key_uuid("clinical_trial", obj["nct_id"])
    if obj["object_type"] == "drug_label_chunk":
        return _natural_key_uuid("drug_label", obj["drug_name"])
    raise ValueError(f"Not a chunk object_type: {obj['object_type']}")


def collect_objects() -> tuple[list[dict], set[str]]:
    """Pull all source data and return (objects, distinct_therapy_names)."""
    objects: list[dict] = []
    therapy_names: set[str] = set()

    for civic_disease, ctgov_condition in CANCERS:
        evidence_items = list(
            itertools.islice(evidence_items_for_disease(civic_disease), MAX_EVIDENCE_PER_DISEASE)
        )
        logger.info("CIViC %s: %d evidence items", civic_disease, len(evidence_items))
        for evidence in evidence_items:
            objects.extend(civic_evidence_to_objects(evidence))
            for therapy in evidence.get("therapies", []):
                therapy_names.add(therapy["name"])

        studies = list(
            itertools.islice(studies_for_condition(ctgov_condition), MAX_TRIALS_PER_DISEASE)
        )
        logger.info("ClinicalTrials.gov %s: %d studies", ctgov_condition, len(studies))
        for study in studies:
            objects.extend(ctgov_study_to_objects(study))

    return objects, therapy_names


def collect_drug_labels(therapy_names: set[str]) -> list[dict]:
    """Fetch openFDA labels one drug at a time, skipping (not aborting on) a
    single drug's failure - a network hiccup partway through ~100+ lookups
    shouldn't discard the rest."""
    objects: list[dict] = []
    for name in sorted(therapy_names):
        try:
            labels = list(itertools.islice(labels_for_generic_name(name), 1))
        except Exception:
            logger.exception("openFDA lookup failed for %r, skipping", name)
            continue
        for label in labels:
            objects.extend(openfda_label_to_objects(label))
    return objects


def _dedupe_by_uuid(objects: list[dict]) -> list[dict]:
    """Drop objects whose deterministic UUID repeats (e.g. the same trial or
    gene turning up while collecting evidence for more than one cancer)."""
    seen = set()
    result = []
    for obj in objects:
        uuid = _uuid_for_object(obj)
        if uuid in seen:
            continue
        seen.add(uuid)
        result.append(obj)
    return result


def load_objects(client, objects: list[dict]) -> None:
    collection = client.collections.get(COLLECTION_NAME)

    genes = dedupe_by_key((o for o in objects if o["object_type"] == "gene"), "gene_name")
    evidence_items = [o for o in objects if o["object_type"] == "evidence_item"]
    trials = dedupe_by_key((o for o in objects if o["object_type"] == "clinical_trial"), "nct_id")
    drug_labels = dedupe_by_key((o for o in objects if o["object_type"] == "drug_label"), "drug_name")
    chunks = _dedupe_by_uuid(
        [o for o in objects if o["object_type"] in ("trial_eligibility_chunk", "drug_label_chunk")]
    )

    parents = genes + evidence_items + trials + drug_labels
    parent_data_objects = [
        DataObject(properties=obj, uuid=_uuid_for_object(obj)) for obj in parents
    ]
    logger.info("Inserting %d parent objects", len(parent_data_objects))
    result = collection.data.insert_many(parent_data_objects)
    if result.has_errors:
        logger.warning("Parent insert errors: %s", result.errors)

    chunk_data_objects = [
        DataObject(
            properties=obj,
            uuid=_uuid_for_object(obj),
            references={"parent": _parent_uuid_for_chunk(obj)},
        )
        for obj in chunks
    ]
    if chunk_data_objects:
        logger.info("Inserting %d chunk objects", len(chunk_data_objects))
        result = collection.data.insert_many(chunk_data_objects)
        if result.has_errors:
            logger.warning("Chunk insert errors: %s", result.errors)


def run() -> None:
    """Two independent stages, each written to Weaviate as soon as it's
    collected - a late failure in one (e.g. an openFDA network hiccup deep
    into ~100+ drug lookups) must not discard the other's already-fetched
    data. This is exactly what happened during Phase 1 testing: a DNS error
    on drug label #~90 killed the whole run *after* 1,973 CIViC/trial
    objects had already been successfully collected but not yet saved.
    """
    objects, therapy_names = collect_objects()
    logger.info("Collected %d source objects, %d distinct therapies", len(objects), len(therapy_names))
    with weaviate_client() as client:
        load_objects(client, objects)

    drug_label_objects = collect_drug_labels(therapy_names)
    logger.info("Collected %d drug label objects", len(drug_label_objects))
    with weaviate_client() as client:
        load_objects(client, drug_label_objects)
