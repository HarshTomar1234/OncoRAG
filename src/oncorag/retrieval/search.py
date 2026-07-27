"""Hybrid search wrapper: configurable alpha, fusion type, and BM25 query
property boosts, on top of the single KnowledgeObject collection.
"""

from dataclasses import dataclass, field

from weaviate.classes.query import HybridFusion, MetadataQuery

from oncorag.retrieval.schema import COLLECTION_NAME


# Chosen in Phase 2 by running the golden-set eval harness, not guessed -
# see docs/eval/phase2_results.md. alpha/fusion_type were statistically
# indistinguishable from 0.5-1.0 (paired bootstrap CI spanned zero); 0.75
# keeps a little BM25 signal as a hedge for exact-identifier queries
# without giving up any measured recall. The property boosts measurably
# helped (+0.036 recall@5, one-sided CI, never hurt in testing).
DEFAULT_QUERY_PROPERTIES = ["content_text", "variant_name^2", "disease_name^2", "title^2"]


@dataclass(frozen=True)
class SearchConfig:
    alpha: float = 0.75
    fusion_type: HybridFusion = HybridFusion.RELATIVE_SCORE
    query_properties: list[str] = field(default_factory=lambda: list(DEFAULT_QUERY_PROPERTIES))
    limit: int = 10


def hybrid_search(client, query: str, config: SearchConfig):
    collection = client.collections.get(COLLECTION_NAME)
    return collection.query.hybrid(
        query=query,
        alpha=config.alpha,
        fusion_type=config.fusion_type,
        query_properties=config.query_properties,
        target_vector="content_vector",
        limit=config.limit,
        return_metadata=MetadataQuery(score=True),
    )
