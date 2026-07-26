"""CIViC GraphQL client. Public API, no auth required for reads.

https://civicdb.org/api/graphql

Query shape was worked out via schema introspection, not assumed:
`Gene` is reached through `variants -> feature -> featureInstance` (a union,
requires an inline fragment), and the NCBI id field is `entrezId` (not
`ncbiId`/`ncbiGeneId`, which don't exist on this schema).
"""

from typing import Any, Iterator

import httpx

from oncorag.ingestion.http_utils import with_retries

CIVIC_GRAPHQL_URL = "https://civicdb.org/api/graphql"

_EVIDENCE_QUERY = """
query EvidenceItems($diseaseName: String!, $after: String) {
  evidenceItems(diseaseName: $diseaseName, after: $after, first: 100) {
    totalCount
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      description
      evidenceType
      evidenceLevel
      evidenceDirection
      significance
      disease { name }
      therapies { name }
      source { citation citationId sourceUrl }
      molecularProfile {
        name
        variants {
          name
          feature {
            name
            description
            featureInstance { ... on Gene { entrezId } }
          }
        }
      }
    }
  }
}
"""


def _post(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    def do_request() -> dict[str, Any]:
        response = httpx.post(
            CIVIC_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()

    payload = with_retries(do_request)
    if "errors" in payload:
        raise RuntimeError(f"CIViC GraphQL error: {payload['errors']}")
    return payload["data"]


def evidence_items_for_disease(disease_name: str) -> Iterator[dict[str, Any]]:
    """Yield every CIViC evidence item for a disease name, paginating through all pages."""
    after = None
    while True:
        data = _post(_EVIDENCE_QUERY, {"diseaseName": disease_name, "after": after})
        page = data["evidenceItems"]
        yield from page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
