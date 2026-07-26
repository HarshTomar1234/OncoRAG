"""CIViC GraphQL client. Public API, no auth required for reads.

https://civicdb.org/api/graphql
"""

from typing import Any, Iterator

import httpx

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
      molecularProfile { name }
      disease { name }
      therapies { name }
      source { citation sourceUrl }
    }
  }
}
"""


def _post(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(
        CIVIC_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
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
