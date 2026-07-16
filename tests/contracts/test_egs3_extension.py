"""Contract gates for the EGS3 programme: theorem results + claim discipline."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

REPO = Path(__file__).resolve().parents[2]


def test_a1_graded_rank_two_with_named_null():
    from htt.obsstat.egs3_graded_comparator import identifiable_rank
    r = identifiable_rank()
    assert r.rank == 2
    assert set(r.reachable_sectors) == {"Sigma2", "Omega_tilt"}
    assert set(r.null_sectors) == {"W2", "Omega_k"}


def test_a3_pi_evalue_markov_bound():
    from htt.obsstat.egs3_calibration import evalue_markov_calibration
    cal = evalue_markov_calibration(n_sims=20000, threshold=1.5, seed=71)
    assert abs(cal.null_mean_evalue - 1.0) < 1e-6 and cal.markov_holds


def test_b1_floor_is_k_profile():
    from bass.transfer.shear_quadrupole_seminative import floor_profile_vs_k
    prof = floor_profile_vs_k([1e-5, 2e-3], lmax=40)
    floors = sorted((v["k_chi_star"], v["floor"]) for v in prof.values())
    assert abs(floors[0][1] - (2 / 5) ** 0.5) < 1e-2     # super-horizon -> 0.632
    assert floors[-1][1] < 0.6324555                     # finite k -> below


def test_b3_transverse_reopens_radial_blind():
    from htt.obsstat.egs3_vorticity_channels import vorticity_reopening
    r = vorticity_reopening(n_configs=400, seed=91)
    assert r.radial_max_abs < 1e-12 and r.transverse_design_rank == 3 and r.reopens


def test_experiments_json_claim_boundary():
    p = REPO / "docs/generated/egs3_experiments.json"
    if not p.exists():
        import pytest
        pytest.skip("run make egs3-experiments first")
    d = json.loads(p.read_text())
    assert d["family_identification"] is False
    assert d["native_solver_result"] is False
    assert "no detection" in d["claim_boundary"]
    assert set(d["blockers_kept_open"]) >= {
        "BLOCKED_MISSING_PR4_E2E_ACCESS", "AWAITING_NATIVE_LOWELL_SOLVER"}


def test_v7_signed_curvature_branch_preserves_open_and_adds_all_branch():
    from htt.obsstat.egs3_identified_set import (
        signed_curvature_branch_reports,
        toy_design,
    )

    toy = toy_design()
    y = toy["R"] @ toy["g_true"]
    reports = signed_curvature_branch_reports(
        y, toy["R"], toy["c"], toy["lower"], toy["upper"], alpha2=1.0)

    open_branch = reports["open_branch[0,Uk]"]
    all_branch = reports["all_branch[-Uk,Uk]"]
    assert open_branch.status == "feasible"
    assert all_branch.status == "feasible"
    assert abs(open_branch.x_lo - 0.11) < 1e-9
    assert abs(open_branch.x_hi - 0.17) < 1e-8
    assert abs(all_branch.x_lo - 0.09) < 1e-9
    assert abs(all_branch.x_hi - 0.17) < 1e-8
    assert all_branch.component_bounds[3] == (-0.02, 0.02)


def test_v7_estimated_covariance_f_threshold_policy_is_fail_closed():
    from htt.obsstat.egs3_identified_set import two_stage_tau

    known = two_stage_tau(10, 2, alpha1=0.05, alpha2=0.05)
    assert known.threshold_policy == "known_chi2"
    assert known.n_sim is None
    assert abs(known.tau1 - float(stats.chi2.ppf(0.95, 8))) < 1e-12

    estimated = two_stage_tau(
        10, 2, alpha1=0.05, alpha2=0.05,
        threshold_policy="estimated_covariance_f", n_sim=300)
    expected = 8 * (300 - 1) / (300 - 8) * float(stats.f.ppf(0.95, 8, 292))
    assert estimated.threshold_policy == "estimated_covariance_f"
    assert estimated.n_sim == 300
    assert estimated.df_residual == 8
    assert estimated.df_reachable == 2
    assert abs(estimated.tau1 - expected) < 1e-12
    assert estimated.tau1 > known.tau1

    with pytest.raises(ValueError):
        two_stage_tau(10, 2, threshold_policy="estimated_covariance_f")
    with pytest.raises(ValueError):
        two_stage_tau(10, 2, threshold_policy="estimated_covariance_f", n_sim=9)


def test_v7_gf_strictness_classifier_separates_strict_and_equality():
    from htt.obsstat.egs3_gf_interval import gf_joint_vs_naive, gf_strictness_witness

    strict = gf_joint_vs_naive()
    assert strict.joint_within_naive
    assert strict.strict_lower is True
    assert strict.strict_upper is True
    assert strict.strictness_criterion["conflict_components"] == (0, 1)

    equal = gf_joint_vs_naive(
        num_reach_iv=(1.0, 1.0),
        den_reach_iv=(2.0, 2.0),
        shared_bounds=((0.0, 0.36), (0.0, 0.27), (0.0, 0.43)),
        c_shared_num=(-0.19, 0.39, 0.17),
        c_shared_den=(0.03, -0.23, -0.31),
        witness_id="counterexample_to_universal_strictness",
    )
    assert equal.joint == equal.naive
    assert equal.strict_lower is False
    assert equal.strict_upper is False
    assert "aligned" in equal.equality_reason

    witness = gf_strictness_witness(n_trials=80, seed=20260709)
    assert witness["agreement_exact_1.0"] is True
    assert witness["strict_cases"] > 0
    assert witness["equal_cases"] > 0
