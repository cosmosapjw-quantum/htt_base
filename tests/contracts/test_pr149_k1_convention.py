"""PR-149 contract tests: Planck K1 convention + BiPoSH structural-zero theorem."""
from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

warnings.filterwarnings("ignore")

from obsstat.k1_convention_contract import (
    K1ConventionError,
    canonical_convention_contract,
    generate_caption,
    lint_caption,
    refuse_k1_detection,
    refuse_mask_not_applied,
    refuse_odd_L_trials,
    refuse_raw_deletion_before_frozen,
    refuse_shared_null_hiding,
    refuse_stale_axis_discovery,
    scan_family_ledger,
    structural_zero_theorem,
    verify_convention_frozen,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SMICA = REPO_ROOT / "workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits"
needs_data = pytest.mark.skipif(not SMICA.is_file(),
                                reason="Planck PR3 maps absent")


def test_structural_zero_theorem_odd_L_vanishes() -> None:
    th = structural_zero_theorem([2, 3, 4, 5], tol=1e-10)
    # the TT BiPoSH diagonal is a structural zero for every odd L and
    # generically non-zero for even L (independent Wigner-3j oracle)
    assert th["odd_L_diagonal_all_zero"]
    assert th["even_L_diagonal_all_nonzero"]
    # the zero holds for ANY alm, including reality-violating complex alm
    assert th["holds_for_reality_violating_alm"]
    for row in th["rows"]:
        if row["odd"]:
            assert row["max_abs_diagonal_coefficient"] < 1e-10


def test_convention_contract_content_addressed() -> None:
    c = canonical_convention_contract(proc_nside=64, lmax=32)
    assert verify_convention_frozen(c, "") == c["content_address"]
    # a tampered contract fails the content address
    tampered = {**c, "proc_nside": 128}
    with pytest.raises(K1ConventionError, match="content address"):
        verify_convention_frozen(tampered, "")


def test_guards() -> None:
    with pytest.raises(K1ConventionError, match="stale Planck axis"):
        refuse_stale_axis_discovery("hardcoded_axis")
    refuse_stale_axis_discovery("healpix_discovery_scan")   # fine
    with pytest.raises(K1ConventionError, match="APPLIED"):
        refuse_mask_not_applied("mask_hash_only")
    with pytest.raises(K1ConventionError, match="independent oracle"):
        refuse_shared_null_hiding("shared_null_hides_mutation")
    with pytest.raises(K1ConventionError, match="no detection"):
        refuse_k1_detection("k1_detection")
    with pytest.raises(K1ConventionError, match="structural zero"):
        refuse_odd_L_trials("odd_L_diagonal_trials")
    with pytest.raises(K1ConventionError, match="frozen"):
        refuse_raw_deletion_before_frozen("approve_deletion_unfrozen")


def test_caption_gate() -> None:
    th = {"odd_L_diagonal_all_zero": True}
    checks = {"reality_ok": True}
    ledger = {"effective_scan_family_size": 84}
    text = generate_caption(th, checks, ledger)
    lint_caption(text)
    for bad in (" stale axis is " + "the discovery.",
                " k1 " + "detection.",
                " odd L diagonal " + "trials."):
        with pytest.raises(K1ConventionError, match="forbidden"):
            lint_caption(text + bad)


def test_scan_family_quotients_odd_L() -> None:
    led = scan_family_ledger(l_values=[2, 3, 4, 5], orientation_grid_n=12)
    # the odd-L diagonal is quotiented (structural zero); only even-L terms count
    assert led["effective_scan_family_size"] > 0
    assert len(led["odd_L_diagonal_terms_quotiented_zero"]) > 0
    assert led["effective_orientations_after_antipodal_quotient"] == 6


@needs_data
def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr149_k1_convention.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_data
def test_map_checks_pass_on_real_planck() -> None:
    mc = json.loads(
        (REPO_ROOT / "docs/generated/pr149_map_convention_checks.json")
        .read_text(encoding="utf-8"))
    assert len(mc["maps"]) == 2                # SMICA + Commander
    for row in mc["maps"]:
        assert row["fsky"] > 0.0               # mask applied
        assert row["reality_ok"] and row["round_trip_ok"]
        # the genuine convention cross-check passes AND catches a wrong phase
        assert row["rotation_crosscheck_ok"]
        assert row["wrong_phase_mutation_caught"]


@needs_data
def test_observed_null_path_equality_and_mutations() -> None:
    pe = json.loads(
        (REPO_ROOT / "docs/generated/pr149_observed_null_path_equality.json")
        .read_text(encoding="utf-8"))
    assert pe["feature_schema_identical"]
    # the even-L feature is data-dependent (observed and null norms differ)
    assert pe["observed_and_null_norms_differ"]
    assert pe["odd_L_structural_zero_on_both_paths_relative"]
    report = json.loads((REPO_ROOT / "docs/generated/pr149_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr149_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["smica"]
