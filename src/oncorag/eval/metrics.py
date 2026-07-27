"""Retrieval metrics computed from a list of ranks (1-indexed position of
the first acceptable answer in the result list, or None if not found within
the searched limit).

Small sample size (28-86 questions) means aggregate numbers alone can hide
which stratum is actually failing, and can make a noisy difference look
real - per-object_type breakdown and bootstrap CIs are load-bearing here,
not decoration.
"""

import random
from typing import Optional


def recall_at_k(ranks: list[Optional[int]], k: int) -> float:
    if not ranks:
        return 0.0
    hits = sum(1 for r in ranks if r is not None and r <= k)
    return hits / len(ranks)


def success_at_1(ranks: list[Optional[int]]) -> float:
    return recall_at_k(ranks, 1)


def mrr(ranks: list[Optional[int]]) -> float:
    if not ranks:
        return 0.0
    return sum((1.0 / r) if r is not None else 0.0 for r in ranks) / len(ranks)


def paired_bootstrap_delta_ci(
    ranks_a: list[Optional[int]],
    ranks_b: list[Optional[int]],
    metric_fn=lambda ranks: recall_at_k(ranks, 5),
    n_resamples: int = 2000,
    seed: int = 0,
) -> tuple[float, tuple[float, float]]:
    """95% CI for metric(b) - metric(a) via paired bootstrap over the same
    questions. Paired resampling is far more sensitive than independent CIs
    at small n, since it cancels out per-question difficulty variance."""
    assert len(ranks_a) == len(ranks_b)
    rng = random.Random(seed)
    n = len(ranks_a)
    observed = metric_fn(ranks_b) - metric_fn(ranks_a)

    deltas = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        sample_a = [ranks_a[i] for i in idx]
        sample_b = [ranks_b[i] for i in idx]
        deltas.append(metric_fn(sample_b) - metric_fn(sample_a))
    deltas.sort()
    lo = deltas[int(0.025 * n_resamples)]
    hi = deltas[int(0.975 * n_resamples)]
    return observed, (lo, hi)
