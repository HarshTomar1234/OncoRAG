"""ClinicalTrials.gov API v2 client. Public REST API, no auth required.

https://clinicaltrials.gov/data-api/api
"""

from typing import Any, Iterator

import httpx

CTGOV_STUDIES_URL = "https://clinicaltrials.gov/api/v2/studies"


def studies_for_condition(condition: str, page_size: int = 100) -> Iterator[dict[str, Any]]:
    """Yield every ClinicalTrials.gov study for a condition, paginating through all pages."""
    params = {"query.cond": condition, "pageSize": page_size, "format": "json"}
    page_token = None
    while True:
        request_params = dict(params)
        if page_token:
            request_params["pageToken"] = page_token
        response = httpx.get(CTGOV_STUDIES_URL, params=request_params, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
        yield from payload.get("studies", [])
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
