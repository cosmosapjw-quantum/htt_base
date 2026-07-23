"""PR-197 gates: cluster-exchangeable finite-null rank (R2, H11)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.cluster_exchangeable_rank import (  # noqa: E402
    exact_rejection_probability,
    max_exact_rejection,
)

CARD = REPO / "docs/generated/pr197_result_card.json"
SPEC = REPO / "docs/research_program/strengthening/pr197_spec.yaml"
ALPHA = 0.05


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_bound_and_terminal() -> None:
    c = _card()
    assert c["metadata"]["spec_sha256"] == hashlib.sha256(SPEC.read_bytes()).hexdigest()
    assert c["metadata"]["public_use"] is False
    assert c["metadata"]["independence_gate"] == "OPEN"
    assert c["terminal"] == "CLUSTER_EXACT_RANK_VERIFIED_NAIVE_LABEL_REFUSED"


def test_exact_enumeration_size_control() -> None:
    enum = _card()["result"]["exact_enumeration"]
    assert enum["all_le_alpha"] is True
    # independently: worst-case rejection over tie patterns never exceeds alpha
    for n in range(1, 40):
        assert max_exact_rejection(n, ALPHA) <= ALPHA + 1e-12
    # ties only lower the rejection probability
    assert exact_rejection_probability(19, ALPHA, ties=5) <= exact_rejection_probability(19, ALPHA, ties=0)


def test_size_monte_carlo_and_budget() -> None:
    mc = _card()["result"]["size_monte_carlo"]
    assert mc["all_cells_pass"] is True
    assert mc["worst_safe_cp_upper_99"] <= ALPHA + mc["tolerance"]
    assert mc["publication_budget"]["n_dgp"] == 20
    assert mc["publication_budget"]["reps_each"] == 20000


def test_pipeline_no_leakage_and_variants() -> None:
    pv = _card()["result"]["pipeline_and_variants"]
    assert pv["scoring_pipeline_identical_after_fixed_training"] is True
    assert pv["cluster_variant_agreement"]["agree_within_2se"] is True
    assert pv["observation_leakage_changes_scorer"] is True


def test_naive_label_refused() -> None:
    r = _card()["result"]
    assert r["naive_exact_label"] is False


def test_card_byte_stable_under_check() -> None:
    import subprocess
    proc = subprocess.run(
        [str(REPO / "venv/bin/python"), "-B",
         str(REPO / "scripts/codex_harness/run_pr197_cluster_rank.py"), "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=600,
        env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin", "OPENBLAS_NUM_THREADS": "4"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
