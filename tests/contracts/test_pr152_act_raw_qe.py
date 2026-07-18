"""PR-152 contract tests: ACT DR6 raw-QE gate + release-simulation cross-fit.

The cross-fit mean field, exact rank, injection-law, availability decision,
inventory, guards and captions run everywhere on small synthetic low-multipole
arrays; the tests that read the built artifacts skip when the heavy real-ACT
card is absent.
"""
from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

warnings.filterwarnings("ignore")

from obsstat.act_raw_qe_gate import (
    ACTRawQEError,
    act_dr6_lensing_inventory,
    exact_finite_rank,
    generate_caption,
    injection_law_distinction,
    leave_one_sim_crossfit_mean_field,
    lint_caption,
    refuse_act_detection,
    refuse_bianchi_from_act,
    refuse_naive_self_mean_field,
    refuse_pre_qe_transfer_label,
    refuse_raw_qe_without_inputs,
    refuse_sky_power_limit_without_raw_qe,
    upstream_availability_decision,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN = REPO_ROOT / "docs/generated"
CARD = GEN / "act_raw_qe_card.json"
needs_card = pytest.mark.skipif(
    not CARD.is_file(), reason="real ACT raw-QE card absent")


def _synthetic(nmodes=117, nsim=400, seed=0):
    rng = np.random.default_rng(seed)
    wm = np.ones(nmodes)
    sim = (rng.standard_normal((nsim, nmodes))
           + 1j * rng.standard_normal((nsim, nmodes)))
    data = rng.standard_normal(nmodes) + 1j * rng.standard_normal(nmodes)
    return sim, data, wm


def test_crossfit_removes_self_mean_field_bias() -> None:
    sim, data, wm = _synthetic()
    cf = leave_one_sim_crossfit_mean_field(sim, data, wm)
    # the naive self-inclusive mean field deflates the sim residual band power
    # (biased low) relative to the leave-one-simulation cross-fit
    assert cf["naive_self_mean_field_deflates_residual"]
    assert cf["naive_sim_band_power_mean"] < cf["crossfit_sim_band_power_mean"]
    assert cf["self_mean_field_bias_ratio_naive_over_crossfit"] < 1.0
    # both pooled ranks are on (0, 1]; the cross-fit is the reported one
    assert 0.0 < cf["crossfit_pooled_rank_p"] <= 1.0


def test_exact_finite_rank_low_ell_band() -> None:
    r = exact_finite_rank(n_sims=400, ell_min=2, ell_max=10)
    # sum_{ell=2..10}(2 ell + 1) = 117 real harmonic dof
    assert r["n_real_harmonic_dof"] == 117
    assert r["exact_finite_rank"] == 117          # modes-limited (399 > 117)
    assert r["rank_limited_by"] == "modes"
    # with few sims the sample rank binds
    r2 = exact_finite_rank(n_sims=20, ell_min=2, ell_max=10)
    assert r2["exact_finite_rank"] == 19
    assert r2["rank_limited_by"] == "sample"


def test_injection_law_distinction() -> None:
    sim, data, wm = _synthetic()
    cf = leave_one_sim_crossfit_mean_field(sim, data, wm)
    inj = injection_law_distinction(cf["crossfit_sim_band_powers"],
                                    injection_amplitude=0.2, seed=1)
    # the stochastic injection is absorbed into the same null (~uniform mean p);
    # the fixed-template injection is a coherent offset that shifts the rank
    assert inj["laws_distinct"]
    assert (inj["fixed_template_mean_pooled_rank_p"]
            < inj["stochastic_mean_pooled_rank_p"])


def test_availability_decision_abandons_without_raw_qe() -> None:
    inv = act_dr6_lensing_inventory(
        present={"kappa_alm_data": "x"}, raw_qe_inputs_on_disk=False,
        validated_ell_range=(40, 763), reference_url="u")
    assert "raw_filtered_cmb_maps" in inv["absent_raw_qe_inputs"]
    dec = upstream_availability_decision(inv)
    assert dec["decision"] == "ABANDON_CURRENT_DATASET_FOR_NATIVE_LOW_L_SKY_POWER"
    assert dec["closed_diagnostic"] == "release_simulation_crossfit_only"
    # with raw-QE present the decision flips
    inv2 = act_dr6_lensing_inventory(
        present={}, raw_qe_inputs_on_disk=True,
        validated_ell_range=(40, 763), reference_url="u")
    assert upstream_availability_decision(inv2)["raw_qe_available"]


def test_guards_reject_forbidden_moves() -> None:
    with pytest.raises(ACTRawQEError, match="pre-QE"):
        refuse_pre_qe_transfer_label("pre_qe_transfer")
    with pytest.raises(ACTRawQEError, match="sky-power"):
        refuse_sky_power_limit_without_raw_qe(False, "l2_10_sky_power_limit")
    with pytest.raises(ACTRawQEError, match="leave-one-simulation"):
        refuse_naive_self_mean_field(False)
    with pytest.raises(ACTRawQEError, match="detection"):
        refuse_act_detection("act_kappa_detection")
    with pytest.raises(ACTRawQEError, match="Bianchi-family"):
        refuse_bianchi_from_act("bianchi_family")
    with pytest.raises(ACTRawQEError, match="upstream"):
        refuse_raw_qe_without_inputs(False, "raw_qe_inference")
    # admissible inputs do NOT raise
    refuse_naive_self_mean_field(True)
    refuse_sky_power_limit_without_raw_qe(True, "l2_10_sky_power_limit")
    refuse_raw_qe_without_inputs(True, "raw_qe_inference")


def test_caption_lint_blocks_a_detection_phrase() -> None:
    with pytest.raises(ACTRawQEError, match="forbidden caption"):
        lint_caption("this is an ACT kappa detection with anisotropy detected")


# --------------------------------------------------------------------------
# built artifacts from the real ACT card (data-gated)
# --------------------------------------------------------------------------
@needs_card
def test_runner_check_and_real_artifacts() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr152_act_raw_qe.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    dec = json.loads((GEN / "pr152_availability_decision.json")
                     .read_text(encoding="utf-8"))
    assert dec["decision"] == "ABANDON_CURRENT_DATASET_FOR_NATIVE_LOW_L_SKY_POWER"
    inv = json.loads((GEN / "pr152_inventory.json").read_text(encoding="utf-8"))
    assert not inv["raw_qe_inputs_on_disk"]
    assert "raw_filtered_cmb_maps" in inv["absent_raw_qe_inputs"]
    cf = json.loads((GEN / "pr152_crossfit_mean_field.json")
                    .read_text(encoding="utf-8"))
    assert cf["naive_self_mean_field_deflates_residual"]
    rank = json.loads((GEN / "pr152_exact_rank.json").read_text(encoding="utf-8"))
    assert rank["exact_finite_rank"] == 117
    report = json.loads((GEN / "pr152_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
