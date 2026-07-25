"""PR-149 contract tests: Planck K1 convention + BiPoSH structural-zero theorem."""
from __future__ import annotations

import importlib.util
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


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr149_k1_convention.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr149", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance_only() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    stored_contract = {
        "content_address": "contract",
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current_contract = {
        "content_address": "contract",
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
            },
        },
    }
    contract_rel = runner.OUTPUTS["contract"]
    assert runner._semantic_artifact(
        contract_rel, stored_contract
    ) == runner._semantic_artifact(contract_rel, current_contract)
    current_contract["content_address"] = "changed"
    assert runner._semantic_artifact(
        contract_rel, stored_contract
    ) != runner._semantic_artifact(contract_rel, current_contract)
    current_contract["content_address"] = "contract"
    current_contract["negative_scan"]["targets"][source]["hits"] = [
        {"line": 1},
    ]
    assert runner._semantic_artifact(
        contract_rel, stored_contract
    ) != runner._semantic_artifact(contract_rel, current_contract)

    stored_manifest = {
        "input_hashes": [f"{source}:{'1' * 64}"],
        "raw_data_pins": {"smica": "raw"},
    }
    current_manifest = {
        "input_hashes": [f"{source}:{'2' * 64}"],
        "raw_data_pins": {"smica": "raw"},
    }
    manifest_rel = runner.OUTPUTS["manifest"]
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["smica"] = "changed"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["smica"] = "raw"
    current_manifest["input_hashes"][0] = f"{source}:not-a-sha"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)


def test_runner_rejects_fractional_theorem_multipole_before_map_io(
    monkeypatch
) -> None:
    runner = _load_runner()
    config = runner.yaml.safe_load(
        runner.SPEC_PATH.read_text(encoding="utf-8")
    )
    config["model"]["structural_zero_l_values"] = [2.5]

    def fail_if_map_io_is_reached(*args, **kwargs):
        pytest.fail("invalid theorem multipole reached Planck map I/O")

    monkeypatch.setattr(
        runner, "load_downgrade_mask_alm", fail_if_map_io_is_reached
    )
    with pytest.raises(K1ConventionError, match="unique integer multipoles"):
        runner.build_reports(config)


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


@pytest.mark.parametrize("l_values, tol, message", [
    ([], 1e-10, "unique integer multipoles"),
    ([0], 1e-10, "unique integer multipoles"),
    ([2, 2], 1e-10, "unique integer multipoles"),
    ([2.5], 1e-10, "unique integer multipoles"),
    ([2], float("nan"), "finite and positive"),
])
def test_structural_zero_theorem_rejects_vacuous_domain(
    l_values, tol: float, message: str
) -> None:
    with pytest.raises(K1ConventionError, match=message):
        structural_zero_theorem(l_values, tol=tol)


def test_convention_contract_content_addressed() -> None:
    c = canonical_convention_contract(proc_nside=64, lmax=32)
    assert verify_convention_frozen(c, "") == c["content_address"]
    # a tampered contract fails the content address
    tampered = {**c, "proc_nside": 128}
    with pytest.raises(K1ConventionError, match="content address"):
        verify_convention_frozen(tampered, "")


@pytest.mark.parametrize("proc_nside", [64.5, True, 0, -64])
def test_convention_contract_rejects_invalid_proc_nside(proc_nside) -> None:
    with pytest.raises(K1ConventionError, match="positive integer"):
        canonical_convention_contract(proc_nside=proc_nside, lmax=32)


@pytest.mark.parametrize("lmax", [32.5, True, -1])
def test_convention_contract_rejects_invalid_lmax(lmax) -> None:
    with pytest.raises(K1ConventionError, match="non-negative integer"):
        canonical_convention_contract(proc_nside=64, lmax=lmax)


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


@pytest.mark.parametrize("l_values", [[], [0], [2, 2], [2.5], [True]])
def test_scan_family_rejects_invalid_multipoles(l_values) -> None:
    with pytest.raises(K1ConventionError, match="unique integer multipoles"):
        scan_family_ledger(l_values=l_values, orientation_grid_n=12)


@pytest.mark.parametrize("orientation_grid_n", [-12, 0, 3, 2.5, True])
def test_scan_family_rejects_invalid_orientation_grid(
    orientation_grid_n
) -> None:
    with pytest.raises(K1ConventionError, match="positive even integer"):
        scan_family_ledger(
            l_values=[2, 3, 4, 5],
            orientation_grid_n=orientation_grid_n,
        )


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
