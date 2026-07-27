"""Sweeps alpha x fusion_type on the realistic golden set (the tuning
target - see docs/phase-2-retrieval-core.md for why the mechanical set
can't be used for this), prints strict/lenient recall@5, recall@10,
success@1, MRR, and a per-object_type breakdown for each config. Also runs
the mechanical set through the same configs for comparison, not as a
tie-breaker.
"""

import logging
from pathlib import Path

from weaviate.classes.query import HybridFusion

from oncorag.eval.harness import GoldenEntry, load_golden_set, run_eval
from oncorag.eval.metrics import mrr, paired_bootstrap_delta_ci, recall_at_k, success_at_1
from oncorag.retrieval.client import weaviate_client
from oncorag.retrieval.search import SearchConfig

logging.basicConfig(level=logging.WARNING)

DOCS_EVAL = Path(__file__).resolve().parent.parent / "docs" / "eval"
ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]
FUSION_TYPES = [HybridFusion.RANKED, HybridFusion.RELATIVE_SCORE]


def _print_report(label: str, entries: list[GoldenEntry], config: SearchConfig, client) -> None:
    result = run_eval(client, entries, config)
    for kind, ranks in (("strict", result.strict_ranks), ("lenient", result.lenient_ranks)):
        r5 = recall_at_k(ranks, 5)
        r10 = recall_at_k(ranks, 10)
        s1 = success_at_1(ranks)
        m = mrr(ranks)
        print(
            f"{label:10s} alpha={config.alpha:<4} fusion={config.fusion_type.name:14s} "
            f"[{kind:7s}] recall@5={r5:.3f} recall@10={r10:.3f} success@1={s1:.3f} MRR={m:.3f}"
        )

    # Per-object_type breakdown (strict only - lenient collapses the
    # distinction the breakdown exists to preserve).
    by_type: dict[str, list] = {}
    for ot, rank in zip(result.object_types, result.strict_ranks):
        by_type.setdefault(ot, []).append(rank)
    for ot, ranks in sorted(by_type.items()):
        print(f"    {ot:24s} n={len(ranks):3d} recall@5={recall_at_k(ranks, 5):.3f} MRR={mrr(ranks):.3f}")


def main() -> None:
    realistic = load_golden_set(DOCS_EVAL / "golden_set_realistic.jsonl")
    mechanical = load_golden_set(DOCS_EVAL / "golden_set.jsonl")

    with weaviate_client() as client:
        print("=== Realistic set (tuning target) ===")
        for alpha in ALPHAS:
            for fusion_type in FUSION_TYPES:
                config = SearchConfig(alpha=alpha, fusion_type=fusion_type)
                _print_report("realistic", realistic, config, client)

        print("\n=== Mechanical set (sanity check only, not tuned against - see spec) ===")
        for alpha in (0.0, 1.0):
            config = SearchConfig(alpha=alpha, fusion_type=HybridFusion.RELATIVE_SCORE)
            _print_report("mechanical", mechanical, config, client)

        print("\n=== Paired bootstrap: is the top of the sweep actually distinguishable? ===")
        candidates = [0.5, 0.75, 1.0]
        results = {}
        for alpha in candidates:
            config = SearchConfig(alpha=alpha, fusion_type=HybridFusion.RELATIVE_SCORE)
            results[alpha] = run_eval(client, realistic, config).strict_ranks
        for a, b in [(0.5, 0.75), (0.75, 1.0), (0.5, 1.0)]:
            observed, (lo, hi) = paired_bootstrap_delta_ci(results[a], results[b])
            significant = lo > 0 or hi < 0
            print(
                f"recall@5(alpha={b}) - recall@5(alpha={a}) = {observed:+.3f}  "
                f"95% CI [{lo:+.3f}, {hi:+.3f}]  {'SIGNIFICANT' if significant else 'not significant (noise)'}"
            )


if __name__ == "__main__":
    main()
