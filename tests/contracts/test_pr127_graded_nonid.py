"""PR-127 contract tests: graded/PSD-cone non-identification."""
from __future__ import annotations

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.graded_nonid import (
    EXPECTED_KERNEL_BASIS,
    EXPECTED_RANK,
    RESPONSE_ROWS,
    CarrierPoint,
    GradedNonIdError,
    constraint_assignment,
    forbid_psd_projection,
    lint_nonid_text,
    require_engine_agreement,
    sympy_rank_kernel,
    validate_witness_pair,
    witness_label,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_sympy_rank_and_kernel_match_registration() -> None:
    result = sympy_rank_kernel(RESPONSE_ROWS)
    assert result["rank"] == EXPECTED_RANK
    got = sorted(tuple(str(Fraction(e)) for e in vec)
                 for vec in result["kernel_basis"])
    assert got == sorted(tuple(str(x) for x in vec)
                         for vec in EXPECTED_KERNEL_BASIS)


def test_one_engine_claims_are_blocked() -> None:
    with pytest.raises(GradedNonIdError, match="BOTH exact engines"):
        require_engine_agreement([sympy_rank_kernel(RESPONSE_ROWS)])


def test_carrier_rejects_negative_moments_and_psd_clipping() -> None:
    with pytest.raises(GradedNonIdError, match="nonnegative"):
        CarrierPoint(sigma2=Fraction(-1, 10), w2=0, omega_tilt=0,
                     delta_omega_k=0)
    original = CarrierPoint(sigma2=0, w2=0, omega_tilt=0,
                            delta_omega_k=Fraction(-1, 10**8))
    clipped = CarrierPoint(sigma2=0, w2=0, omega_tilt=0, delta_omega_k=0)
    with pytest.raises(GradedNonIdError, match="PSD projection"):
        forbid_psd_projection(original, clipped)


def test_witness_pairs_are_response_indistinguishable() -> None:
    a = CarrierPoint(sigma2=Fraction(1, 10**8), w2=0,
                     omega_tilt=Fraction(1, 10**7),
                     delta_omega_k=Fraction(-1, 10**7))
    b = CarrierPoint(sigma2=Fraction(1, 10**8), w2=Fraction(3, 10**8),
                     omega_tilt=Fraction(1, 10**7),
                     delta_omega_k=Fraction(-1, 10**7))
    verdict = validate_witness_pair(a, b)
    assert verdict["difference"][1] != "0"
    # a pair differing along a NON-kernel direction is rejected
    c = CarrierPoint(sigma2=Fraction(2, 10**8), w2=0,
                     omega_tilt=Fraction(1, 10**7),
                     delta_omega_k=Fraction(-1, 10**7))
    with pytest.raises(GradedNonIdError, match="indistinguishable"):
        validate_witness_pair(a, c)


def test_physical_label_requires_verified_assignment() -> None:
    point = CarrierPoint(sigma2=Fraction(1, 10**8), w2=0,
                         omega_tilt=Fraction(1, 10**7),
                         delta_omega_k=Fraction(-1, 10**7))
    assert witness_label(point, None) == "algebraic_only"
    omega_l = Fraction(7, 10) - point.sigma2 - point.omega_tilt + point.w2
    verdict = constraint_assignment(point, omega_m=Fraction(3, 10),
                                    omega_l=omega_l,
                                    omega_k_total=Fraction(0))
    assert verdict["label"] == "physical"
    with pytest.raises(GradedNonIdError, match="matter positivity"):
        constraint_assignment(point, omega_m=Fraction(-1, 10),
                              omega_l=omega_l, omega_k_total=Fraction(0))
    with pytest.raises(GradedNonIdError, match="parent identity"):
        constraint_assignment(point, omega_m=Fraction(3, 10),
                              omega_l=Fraction(1, 2),
                              omega_k_total=Fraction(0))


def test_isotropy_language_lint() -> None:
    with pytest.raises(GradedNonIdError, match="language violation"):
        lint_nonid_text("therefore non-identification proves isotropy")


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr127_graded_nonid.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_two_engine_receipt() -> None:
    kernel = json.loads(
        (REPO_ROOT / "docs/generated/pr127_response_kernel.json")
        .read_text(encoding="utf-8"))
    assert kernel["rank"] == 2
    assert kernel["engines"] == ["sage_qq", "sympy"]
    table = json.loads(
        (REPO_ROOT / "docs/generated/pr127_rank_api_table.json")
        .read_text(encoding="utf-8"))
    raises = [row["raises_rank"] for row in table["probes"]]
    assert raises == [True, True, False, False]
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr127_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
