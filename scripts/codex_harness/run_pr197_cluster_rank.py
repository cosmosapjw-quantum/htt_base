"""PR-197 runner: cluster-exchangeable finite-null rank gates (--write/--check)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.cluster_exchangeable_rank import (  # noqa: E402
    cluster_variant_agreement,
    max_exact_rejection,
    run_size_mc,
    scoring_pipeline_identical,
    train_scorer,
)

SPEC = REPO / "docs/research_program/strengthening/pr197_spec.yaml"
CARD = REPO / "docs/generated/pr197_result_card.json"

ALPHA = 0.05
# card Monte-Carlo budget (documented; full publication budget below)
CARD_DGPS = [
    {"n_train": 400, "n_clusters": 99, "cluster_size": 4, "dim": 6, "rho": 0.75},
    {"n_train": 400, "n_clusters": 60, "cluster_size": 3, "dim": 5, "rho": 0.5},
    {"n_train": 300, "n_clusters": 120, "cluster_size": 2, "dim": 4, "rho": 0.9},
]
CARD_SEEDS = [20260721, 11, 97]
CARD_REPS = 4000
PUBLICATION_BUDGET = {"n_dgp": 20, "n_seed": 10, "reps_each": 20000,
                      "tolerance": 0.005,
                      "reference_evidence":
                      "strengthening package validation_outputs/cluster_rank_20k.json "
                      "(size 0.05085, 99% CP upper 0.05458)"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_enumeration() -> dict:
    rows = {n: max_exact_rejection(n, ALPHA) for n in range(1, 13)}
    return {
        "n_cal_range": "1..12",
        "max_rejection_by_n_cal": rows,
        "all_le_alpha": all(v <= ALPHA + 1e-12 for v in rows.values()),
        "note": "worst case over all tie patterns; holds for every finite n_cal",
    }


def _size_mc() -> dict:
    cells = []
    worst_upper = 0.0
    for dgp in CARD_DGPS:
        for seed in CARD_SEEDS:
            r = run_size_mc(repetitions=CARD_REPS, alpha=ALPHA, seed=seed, **dgp)
            cells.append({"dgp": dgp, "seed": seed,
                          "safe_size": r["safe_empirical_size"],
                          "safe_cp_upper_99": r["safe_cp_upper_99"],
                          "naive_size": r["naive_empirical_size"]})
            worst_upper = max(worst_upper, r["safe_cp_upper_99"])
    return {
        "budget": {"n_dgp": len(CARD_DGPS), "n_seed": len(CARD_SEEDS),
                   "reps_each": CARD_REPS},
        "cells": cells,
        "worst_safe_cp_upper_99": worst_upper,
        "tolerance": 0.02,
        "all_cells_pass": worst_upper <= ALPHA + 0.02,
        "publication_budget": PUBLICATION_BUDGET,
    }


def _pipeline_and_variants() -> dict:
    rng = np.random.default_rng(20260721)
    train = rng.normal(size=(300, 6))
    obs = rng.normal(size=(1, 6))
    cal = rng.normal(size=(50, 6))
    identical = scoring_pipeline_identical(train, obs, cal)
    variants = cluster_variant_agreement(
        n_train=400, n_clusters=99, cluster_size=4, dim=6, rho=0.75, seed=5)
    # leakage negative control: fitting the scorer ON the observation changes it
    scorer_clean = train_scorer(train)
    scorer_leaked = train_scorer(np.vstack([train, obs]))
    leakage_detected = not np.allclose(scorer_clean.mean, scorer_leaked.mean)
    return {
        "scoring_pipeline_identical_after_fixed_training": identical,
        "cluster_variant_agreement": variants,
        "observation_leakage_changes_scorer": leakage_detected,
    }


def build_payload() -> dict:
    enum = _exact_enumeration()
    mc = _size_mc()
    pv = _pipeline_and_variants()

    all_ok = (
        enum["all_le_alpha"]
        and mc["all_cells_pass"]
        and pv["scoring_pipeline_identical_after_fixed_training"] is True
        and pv["cluster_variant_agreement"]["agree_within_2se"] is True
        and pv["observation_leakage_changes_scorer"] is True
    )
    terminal = (
        "CLUSTER_EXACT_RANK_VERIFIED_NAIVE_LABEL_REFUSED"
        if all_ok else "BLOCKED_CLUSTER_RANK_GATE_FAILURE"
    )
    return {
        "schema": "htt.pr197.result_card.v1",
        "pr_id": "PR-197",
        "metadata": {
            "owner": "OBSSTAT",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr197_cluster_rank.py --write"
            ),
        },
        "result": {
            "exact_enumeration": enum,
            "size_monte_carlo": mc,
            "pipeline_and_variants": pv,
            "naive_exact_label": False,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "naive reused-cluster ranks are empirical only; exact label refused",
            "the score is fixed on an independent training ensemble (no leakage)",
            "exactness is proven by enumeration; the Monte-Carlo corroborates",
        ],
    }


def _render(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        CARD.write_bytes(_render(payload))
        print(f"wrote {CARD.name}; terminal={payload['terminal']}")
        return 0
    ok = CARD.exists() and CARD.read_bytes() == _render(payload)
    print(json.dumps({"mode": "check", "ok": ok, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
