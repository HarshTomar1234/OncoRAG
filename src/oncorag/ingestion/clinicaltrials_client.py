"""ClinicalTrials.gov API v2 client. Public REST API, no auth required.

https://clinicaltrials.gov/data-api/api
"""

from typing import Any, Iterator

import httpx

from oncorag.ingestion.http_utils import with_retries

CTGOV_STUDIES_URL = "https://clinicaltrials.gov/api/v2/studies"


def studies_for_condition(condition: str, page_size: int = 100) -> Iterator[dict[str, Any]]:
    """Yield every ClinicalTrials.gov study for a condition, paginating through all pages."""
    params = {"query.cond": condition, "pageSize": page_size, "format": "json"}
    page_token = None
    while True:
        request_params = dict(params)
        if page_token:
            request_params["pageToken"] = page_token

        def do_request() -> dict[str, Any]:
            response = httpx.get(CTGOV_STUDIES_URL, params=request_params, timeout=60.0)
            response.raise_for_status()
            return response.json()

        payload = with_retries(do_request)
        yield from payload.get("studies", [])
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
