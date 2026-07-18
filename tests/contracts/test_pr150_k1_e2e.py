"""PR-150 contract tests: K1 exchangeable global scan + Planck PR3 FFP10 E2E.

The idealised correlated-GRF pooled-rank super-uniformity (the falsifier), the
guards, the PR4 skip receipt, captions and mutation-exactness run everywhere;
the tests that read the heavy FFP10 E2E max-scan card and the built artifacts
skip when the card is absent (produced once by
``scripts/k1_global_maxscan.py --precision``).
"""
from __future__ import annotations

import json
import subprocess
import sys
import warnings
from fractions import Fraction
from pathlib import Path

import pytest

warnings.filterwarnings("ignore")

from obsstat.k1_e2e_calibration import (
    K1E2EError,
    generate_caption,
    idealised_super_uniformity,
    lint_caption,
    pooled_rank_from_e2e_card,
    pr4_npipe_skip_receipt,
    refuse_idealised_promotion,
    refuse_k1_axis_detection,
    refuse_non_super_uniform,
    refuse_pr3_pr4_joint,
    refuse_pr4_numeric,
    refuse_real_sky_p_without_e2e,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CARD = REPO_ROOT / "docs/generated/k1_global_maxscan_e2e_full.json"
GEN = REPO_ROOT / "docs/generated"
needs_card = pytest.mark.skipif(
    not CARD.is_file(), reason="FFP10 E2E max-scan card absent")


# --------------------------------------------------------------------------
# idealised correlated-GRF pooled-rank super-uniformity (the falsifier)
# --------------------------------------------------------------------------
def test_idealised_pooled_rank_is_super_uniform() -> None:
    idl = idealised_super_uniformity(n_statistics=8, rho=0.35,
                                     n_realizations=400, seed=20260724,
                                     band=0.03)
    assert idl["super_uniform"]
    # the shipped (1+b)/(N+1) pooled rank never over-rejects (conservative)
    assert idl["max_exceedance_above_uniform"] <= 0.03
    # the live anti-conservative b/(N-1) negative control over-rejects the
    # shipped form at the sub-resolution level: the shipped (1+b)/(N+1) form
    # structurally CANNOT reject below its 1/N floor, the naive form CAN -- so
    # the conservativeness check has genuine discriminating power, not a stamp
    assert idl["control_discriminates"]
    assert idl["shipped_subfloor_rejection"] == 0.0
    assert idl["anti_conservative_control_subfloor_rejection"] > 0.0
    # rejection fraction is at or below the nominal at every grid point (+band)
    for rej, a in zip(idl["rejection_fraction"], idl["alpha_grid"]):
        assert rej <= a + 0.03


def test_falsifier_kills_a_non_super_uniform_method() -> None:
    # the exchangeable pooled rank is conservative, so its exceedance is small;
    # setting the band just BELOW the measured exceedance forces rejection ---
    # the falsifier is a real threshold with discriminating power, not a rubber
    # stamp that passes any band
    idl = idealised_super_uniformity(n_statistics=8, rho=0.35,
                                     n_realizations=400, seed=20260724,
                                     band=0.5)
    measured = idl["max_exceedance_above_uniform"]
    with pytest.raises(K1E2EError, match="self-consistency check fails|not "
                       "conservative"):
        idealised_super_uniformity(n_statistics=8, rho=0.35,
                                   n_realizations=400, seed=20260724,
                                   band=measured - 0.01)
    with pytest.raises(K1E2EError, match="falsified"):
        refuse_non_super_uniform(False)


# --------------------------------------------------------------------------
# non-numeric PR4/NPIPE skip receipt
# --------------------------------------------------------------------------
def test_pr4_skip_receipt_is_non_numeric() -> None:
    r = pr4_npipe_skip_receipt()
    assert r["pr4_npipe_status"] == "SKIPPED_BY_USER_SCOPE"
    assert r["numeric_outputs"] == "none"
    assert r["pr3_plus_pr4_joint_result"] == "not_produced"


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def test_guards_reject_the_forbidden_moves() -> None:
    with pytest.raises(K1E2EError, match="promoted to a"):
        refuse_idealised_promotion("idealised_is_planck_calibration")
    with pytest.raises(K1E2EError, match="without the E2E ensemble"):
        refuse_real_sky_p_without_e2e(False, "real_sky_p")
    with pytest.raises(K1E2EError, match="PR4 NPIPE numeric"):
        refuse_pr4_numeric("pr4_p_value")
    with pytest.raises(K1E2EError, match="combined result"):
        refuse_pr3_pr4_joint("pr3_pr4_joint")
    with pytest.raises(K1E2EError, match="directional detection"):
        refuse_k1_axis_detection("k1_axis")
    # admissible inputs do NOT raise
    refuse_idealised_promotion("method_calibration_only")
    refuse_real_sky_p_without_e2e(True, "e2e_conditional_p")
    refuse_k1_axis_detection("feature_extraction_only")


def test_caption_lint_blocks_a_detection_phrase() -> None:
    with pytest.raises(K1E2EError, match="forbidden caption"):
        lint_caption("this establishes shear detected in the K1 sky")


# --------------------------------------------------------------------------
# E2E card -> exchangeable pooled rank (data-gated)
# --------------------------------------------------------------------------
@needs_card
def test_pooled_rank_from_real_e2e_card() -> None:
    pr = pooled_rank_from_e2e_card(CARD)
    n = pr["simulation_count"]
    assert n == 300
    # the global p is the exchangeable (1+b)/(N+1) pooled rank: on the support
    # grid, at or above the resolution floor, never zero
    assert pr["on_exchangeable_support_grid"]
    assert pr["resolution_floor"] == pytest.approx(1.0 / (n + 1))
    assert pr["e2e_global_pooled_rank_p"] >= pr["resolution_floor"]
    # the reported p lands exactly on a (1+b)/(N+1) grid node
    b = round(pr["e2e_global_pooled_rank_p"] * (n + 1)) - 1
    assert 0 <= b <= n
    assert pr["e2e_global_pooled_rank_p"] == pytest.approx(
        float(Fraction(1 + b, n + 1)), abs=1e-9)
    # the observed max-scan score is carried through (not lost to a null)
    assert pr["observed_max_scan_score"] is not None
    assert pr["per_statistic_local_p"]     # per-statistic local p-values present
    # the look-elsewhere global p equals the pooled rank (over the 6 statistics)
    assert pr["look_elsewhere_global_p"] == pr["e2e_global_pooled_rank_p"]


def test_pooled_rank_rejects_off_grid_and_sub_floor_cards(tmp_path) -> None:
    # P1 regression: the grid/floor validation is load-bearing on the ACTUAL
    # reported global_p, not a grid-snapped surrogate. A sub-resolution p that
    # snaps onto the floor node must still be REFUSED (PR-135 forbids it).
    def _card(gp: float) -> Path:
        p = tmp_path / f"card_{gp}.json"
        p.write_text(json.dumps({
            "result": {"global_p": gp, "local_p": {"a": gp},
                       "observed_max_score": 1.0},
            "config": {"n_sims": 300}}))
        return p
    # 0.002 < floor 1/301 (0.00332); round(0.002*301)=1 snaps to 1/301 and would
    # pass a surrogate check, but the raw value is off-grid AND sub-floor -> raise
    with pytest.raises(K1E2EError, match="support grid|resolution floor"):
        pooled_rank_from_e2e_card(_card(0.002))
    # a value strictly between two grid nodes is off-grid -> raise
    with pytest.raises(K1E2EError, match="support grid"):
        pooled_rank_from_e2e_card(_card(0.05))
    # an exact grid node at/above the floor is accepted
    ok = pooled_rank_from_e2e_card(_card(11.0 / 301.0))
    assert ok["e2e_global_pooled_rank_p"] == pytest.approx(11.0 / 301.0)


@needs_card
def test_built_artifacts_are_current_and_honest() -> None:
    # the E2E input manifest records the full available ensemble + sample hashes
    man = json.loads((GEN / "pr150_e2e_input_manifest.json")
                     .read_text(encoding="utf-8"))
    assert man["cmb_mc_count"] == 999
    assert man["noise_mc_count"] == 300
    assert len(man["sample_sha256"]) == 4
    assert man["observed_null_byte_equivalent_path"]
    # the pooled-rank artifact reports the 300 sims that produced the p
    pr = json.loads((GEN / "pr150_e2e_pooled_rank.json")
                    .read_text(encoding="utf-8"))
    assert pr["simulation_count"] == 300
    # the caption names the 300 used and the 999/300 available (honest count)
    cap = json.loads((GEN / "pr150_captions.json")
                     .read_text(encoding="utf-8"))["captions"]["summary"]
    assert "300 CMB" in cap and "999 CMB" in cap
    lint_caption(cap)


@needs_card
def test_runner_check_mode_is_current_and_mutations_killed() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr150_k1_e2e.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((GEN / "pr150_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads((GEN / "pr150_artifact_manifest.json")
                          .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["e2e_card_sha256"]
    # the PR4 skip receipt is a non-numeric artifact on disk
    pr4 = json.loads((GEN / "pr150_pr4_skip_receipt.json")
                     .read_text(encoding="utf-8"))
    assert pr4["numeric_outputs"] == "none"
