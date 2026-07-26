"""openFDA drug label client. Public REST API; a free key raises the rate limit.

https://open.fda.gov/apis/drug/label/
"""

from typing import Any, Iterator

import httpx

from oncopilot.config.settings import settings

OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"
_PAGE_LIMIT = 100


def labels_for_generic_name(generic_name: str) -> Iterator[dict[str, Any]]:
    """Yield every openFDA drug label result for a generic drug name, paginating through all pages."""
    skip = 0
    while True:
        params = {
            "search": f'openfda.generic_name:"{generic_name}"',
            "limit": _PAGE_LIMIT,
            "skip": skip,
            "api_key": settings.openfda_api_key,
        }
        response = httpx.get(OPENFDA_LABEL_URL, params=params, timeout=30.0)
        if response.status_code == 404:
            # openFDA returns 404 for a search with zero results, not an empty list.
            return
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        yield from results
        if len(results) < _PAGE_LIMIT:
            break
        skip += _PAGE_LIMIT
