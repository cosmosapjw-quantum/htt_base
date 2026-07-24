"""PR-126 contract tests: one-way FLRW/EGS + counterexample registry."""
from __future__ import annotations

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.egs_oneway import (
    ALMOST_EGS_PREMISES,
    COMPARATOR_FORWARD_PREMISES,
    FORWARD_STATEMENT,
    FORWARD_THEOREM_ID,
    ComparatorState,
    EgsOnewayError,
    check_forward,
    lint_theorem_text,
    safe_theorem_text,
    seeded_cancellation_states,
    theorem_id,
    validate_counterexample,
    validate_theorem_claim,
)
from scripts.codex_harness import run_pr126_egs_oneway as pr126_runner

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_forward_holds_on_flrw_states() -> None:
    states = [ComparatorState(beta=0, sigma2=0, w2=0, omega_tilt=0,
                              delta_omega_k=0)]
    result = check_forward(states)
    assert result["theorem_id"] == FORWARD_THEOREM_ID
    assert result["states_checked"] == 1


def test_incomplete_premise_set_is_refuted_by_witness() -> None:
    with pytest.raises(EgsOnewayError, match="incomplete premise set"):
        check_forward([], premise_ids=tuple(
            p for p in COMPARATOR_FORWARD_PREMISES
            if p != "CMP-P4-delta_omega_k_zero"))


def test_counterexamples_cancel_and_fail_flrw() -> None:
    ce1 = ComparatorState(beta=0, sigma2=Fraction(1, 10**8), w2=0,
                          omega_tilt=0,
                          delta_omega_k=Fraction(-1, 10**8))
    verdict = validate_counterexample(ce1)
    assert verdict["flrw_limit"] is False
    assert "sigma2" in verdict["nonzero_components"]
    # an actually-FLRW state witnesses nothing
    with pytest.raises(EgsOnewayError, match="witnesses nothing"):
        validate_counterexample(ComparatorState(
            beta=0, sigma2=0, w2=0, omega_tilt=0, delta_omega_k=0))
    # a non-cancelling state is not a counterexample
    with pytest.raises(EgsOnewayError, match="cancel exactly"):
        validate_counterexample(ComparatorState(
            beta=0, sigma2=Fraction(1, 10**8), w2=0, omega_tilt=0,
            delta_omega_k=0))


def test_seeded_cancellation_family_is_deterministic() -> None:
    a = seeded_cancellation_states(16)
    b = seeded_cancellation_states(16)
    assert a == b
    for state in a:
        assert state.x_c() == 0
        assert not state.satisfies_forward_premises()


def test_theorem_ids_are_content_addressed() -> None:
    base = theorem_id(tuple(COMPARATOR_FORWARD_PREMISES), FORWARD_STATEMENT)
    assert base == FORWARD_THEOREM_ID
    edited = theorem_id(
        tuple(p for p in COMPARATOR_FORWARD_PREMISES
              if p != "CMP-P2-sigma2_zero"),
        FORWARD_STATEMENT)
    assert edited != base
    with pytest.raises(EgsOnewayError, match="NEW theorem id"):
        validate_theorem_claim({
            "theorem_id": base,
            "statement": FORWARD_STATEMENT,
            "premise_ids": [p for p in COMPARATOR_FORWARD_PREMISES
                            if p != "CMP-P2-sigma2_zero"],
        })


def test_exact_and_almost_claims_never_merge() -> None:
    premises = list(COMPARATOR_FORWARD_PREMISES) + list(ALMOST_EGS_PREMISES)[:1]
    with pytest.raises(EgsOnewayError, match="never merge"):
        validate_theorem_claim({
            "theorem_id": theorem_id(premises, FORWARD_STATEMENT),
            "statement": FORWARD_STATEMENT,
            "premise_ids": premises,
        })


def test_safe_text_lint() -> None:
    text = safe_theorem_text()
    assert "ONE-WAY" in text
    with pytest.raises(EgsOnewayError, match="forbidden"):
        lint_theorem_text("this result certifies FLRW isotropy")


def test_manifest_source_hashes_are_generation_time_provenance() -> None:
    stored = {
        "input_hashes": [
            f"htt/src/common/egs_oneway.py:{'1' * 64}",
            f"htt/src/common/frame_contract.py:{'2' * 64}",
        ],
        "owner": "COMMON",
    }
    current = {
        "input_hashes": [
            f"htt/src/common/egs_oneway.py:{'3' * 64}",
            f"htt/src/common/frame_contract.py:{'4' * 64}",
        ],
        "owner": "COMMON",
    }
    manifest = pr126_runner.OUTPUTS["manifest"]
    assert pr126_runner._semantic_artifact(
        manifest, stored
    ) == pr126_runner._semantic_artifact(manifest, current)

    current["owner"] = "BASS"
    assert pr126_runner._semantic_artifact(
        manifest, stored
    ) != pr126_runner._semantic_artifact(manifest, current)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr126_egs_oneway.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_sealed_pair() -> None:
    registry = json.loads(
        (REPO_ROOT / "docs/generated/pr126_counterexample_registry.json")
        .read_text(encoding="utf-8"))
    assert registry["bound_forward_theorem_id"] == FORWARD_THEOREM_ID
    assert len(registry["counterexamples"]) == 2
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr126_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 5
