"""Weaviate collection schema for the oncology knowledge base.

Single collection by necessity, not preference: the Weaviate Cloud free
tier caps at 1 collection (confirmed empirically - a 6-collection design
hit a 429 USAGE_LIMIT_EXCEEDED after the first collection). So every object
type (gene, evidence item, clinical trial, drug label, and the two chunk
types) lives in one "KnowledgeObject" collection with an `object_type`
discriminator, a superset of properties (unused ones left empty per
object), and a single `content_vector` built from a `content_text` field
that ingestion code populates per type. Chunks self-reference their parent
object via `parent` (a same-collection cross-reference).

Full reasoning: docs/phase-1-data-and-schema.md (gitignored).
"""

from weaviate.classes.config import Configure, DataType, Property, ReferenceProperty, Tokenization

COLLECTION_NAME = "KnowledgeObject"


def create_collections(client) -> None:
    client.collections.create(
        COLLECTION_NAME,
        properties=[
            Property(name="object_type", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            # Text actually sent to the vectorizer - curated per object type at ingest time.
            Property(name="content_text", data_type=DataType.TEXT),
            # Gene
            Property(name="gene_name", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            Property(name="ncbi_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            Property(name="aliases", data_type=DataType.TEXT_ARRAY),
            # EvidenceItem (CIViC)
            Property(name="civic_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            Property(name="variant_name", data_type=DataType.TEXT),
            Property(name="disease_name", data_type=DataType.TEXT),
            Property(name="therapy_names", data_type=DataType.TEXT_ARRAY),
            Property(name="evidence_type", data_type=DataType.TEXT),
            Property(name="evidence_level", data_type=DataType.TEXT),
            Property(name="evidence_direction", data_type=DataType.TEXT),
            Property(name="clinical_significance", data_type=DataType.TEXT),
            # ClinicalTrial
            Property(name="nct_id", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="conditions", data_type=DataType.TEXT_ARRAY),
            Property(name="interventions", data_type=DataType.TEXT_ARRAY),
            Property(name="phase", data_type=DataType.TEXT),
            Property(name="overall_status", data_type=DataType.TEXT),
            Property(name="locations", data_type=DataType.TEXT_ARRAY),
            Property(name="last_update_date", data_type=DataType.TEXT),
            # DrugLabel (openFDA)
            Property(name="drug_name", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            Property(name="manufacturer_name", data_type=DataType.TEXT),
            Property(name="mechanism_of_action", data_type=DataType.TEXT),
            # Shared citation fields (Gene/EvidenceItem/DrugLabel)
            Property(name="source_citation", data_type=DataType.TEXT),
            Property(name="source_pmid", data_type=DataType.TEXT, tokenization=Tokenization.FIELD),
            Property(name="source_url", data_type=DataType.TEXT),
            # Chunk objects (drug_label_chunk / trial_eligibility_chunk)
            Property(name="chunk_field_name", data_type=DataType.TEXT),
            Property(name="chunk_index", data_type=DataType.INT),
        ],
        references=[ReferenceProperty(name="parent", target_collection=COLLECTION_NAME)],
        vector_config=Configure.Vectors.text2vec_weaviate(
            name="content_vector",
            source_properties=["content_text"],
        ),
    )
