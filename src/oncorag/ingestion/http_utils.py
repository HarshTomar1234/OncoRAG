"""Shared retry wrapper for the ingestion HTTP clients.

External APIs (CIViC, ClinicalTrials.gov, openFDA) occasionally time out or
hiccup transiently - retrying a handful of times with backoff is standard
practice for a real ingestion pipeline, not defensive overkill.
"""

import time
from typing import Callable, TypeVar

import httpx

T = TypeVar("T")

_RETRYABLE_EXCEPTIONS = (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 2.0


def with_retries(fn: Callable[[], T]) -> T:
    last_error: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return fn()
        except _RETRYABLE_EXCEPTIONS as exc:
            last_error = exc
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_BACKOFF_SECONDS * attempt)
    assert last_error is not None
    raise last_error
