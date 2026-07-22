"""Contract gates for the EGS3 programme: theorem results + claim discipline."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

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


def test_experiments_frozen_payload_keeps_generation_lineage_separate():
    artifact = REPO / "docs/generated/egs3_experiments.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    lineage = payload["scientific_payload_lineage"]

    assert payload["generating_command"] == (
        "python scripts/run_egs3_experiments.py --metadata-only")
    assert payload["input_hashes_role"] == (
        "metadata_refresh_and_current_compatibility_only")
    assert payload["input_hashes"] == payload["current_compatibility_input_hashes"]
    assert lineage["status"] == "frozen_v7_scientific_payload"
    assert lineage["replay_status"] == (
        "historical_source_bytes_required_not_current_worktree")
    assert lineage["generating_command"] == (
        "python scripts/run_egs3_experiments.py")

    def records_by_path(records):
        return {record.partition(":sha256:")[0]: record for record in records}

    historical = records_by_path(lineage["input_hashes"])
    current = records_by_path(payload["current_compatibility_input_hashes"])
    core_path = "htt/obsstat/egs3_identified_set.py"
    core_digest = hashlib.sha256((REPO / core_path).read_bytes()).hexdigest()
    assert current[core_path] == f"{core_path}:sha256:{core_digest}"
    assert historical[core_path] != current[core_path]

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/run_egs3_experiments.py",
            "--metadata-only",
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_experiments_metadata_refresh_rejects_missing_or_drifted_lineage():
    script = REPO / "scripts/run_egs3_experiments.py"
    spec = importlib.util.spec_from_file_location("run_egs3_experiments", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = json.loads(
        (REPO / "docs/generated/egs3_experiments.json").read_text(
            encoding="utf-8"))

    without_lineage = json.loads(json.dumps(payload))
    without_lineage.pop("scientific_payload_lineage")
    with pytest.raises(ValueError, match="explicit scientific_payload_lineage"):
        module._with_artifact_metadata(without_lineage, metadata_only=True)

    drifted = json.loads(json.dumps(payload))
    drifted["experiments"]["axis_e"]["E1_identified_set"][
        "population_interval"][0] += 1.0e-6
    with pytest.raises(ValueError, match="no longer matches its lineage receipt"):
        module._with_artifact_metadata(drifted, metadata_only=True)


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


def test_v7_population_endpoint_is_sharp_under_column_scale_stress():
    from htt.obsstat.egs3_identified_set import identified_set_report

    response = np.array([
        [400000.0, 1.0],
        [400000.0, -1.0],
        [0.0, 2.0],
    ])
    truth = np.array([0.2, -0.3])
    comparator = np.array([1.0, -0.7])
    report = identified_set_report(
        response @ truth,
        response,
        comparator,
        np.array([-2.0, -2.0]),
        np.array([2.0, 2.0]),
        alpha2=1.0,
    )

    expected = float(comparator @ truth)
    assert report.status == "feasible"
    assert report.reachable_lo == pytest.approx(expected, abs=2e-11)
    assert report.reachable_hi == pytest.approx(expected, abs=2e-11)
    assert report.reachable_lo <= report.reachable_hi


def test_v7_population_box_exclusion_is_empty_without_bounded_solver(monkeypatch):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([0.2, -0.3])
    monkeypatch.setattr(
        identified.optimize,
        "lsq_linear",
        lambda *args, **kwargs: pytest.fail(
            "population branch must not call bounded least squares"),
    )

    report = identified.identified_set_report(
        response @ truth,
        response,
        np.array([0.4, -0.7]),
        np.array([0.200001, -1.0]),
        np.array([1.0, 1.0]),
        alpha2=1.0,
    )

    assert report.spec_pass
    assert report.rank == 2
    assert report.status == identified.STATUS_EMPTY
    assert np.all(np.isnan([
        report.x_lo,
        report.x_hi,
        report.reachable_lo,
        report.reachable_hi,
    ]))


@pytest.mark.parametrize("scale", [1e-12, 1e12])
def test_v7_population_report_is_invariant_to_bidirectional_column_scale(scale):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([0.2, -0.3])
    observed = response @ truth
    comparator = np.array([0.4, -0.7])
    lower = np.array([-1.0, -1.0])
    upper = np.array([1.0, 1.0])
    baseline = identified.identified_set_report(
        observed, response, comparator, lower, upper, alpha2=1.0)

    stressed_response = response.copy()
    stressed_response[:, 0] *= scale
    stressed_comparator = comparator.copy()
    stressed_comparator[0] *= scale
    stressed_lower = lower.copy()
    stressed_upper = upper.copy()
    stressed_lower[0] /= scale
    stressed_upper[0] /= scale
    stressed = identified.identified_set_report(
        observed,
        stressed_response,
        stressed_comparator,
        stressed_lower,
        stressed_upper,
        alpha2=1.0,
    )

    assert stressed.status == baseline.status == identified.STATUS_FEASIBLE
    assert stressed.rank == baseline.rank == 2
    assert stressed.df_reachable == baseline.df_reachable == 2
    assert stressed.df_residual == baseline.df_residual == 1
    assert stressed.tau.r == baseline.tau.r
    assert stressed.tau.tau1 == pytest.approx(baseline.tau.tau1)
    assert (stressed.x_lo, stressed.x_hi) == pytest.approx(
        (baseline.x_lo, baseline.x_hi), abs=2e-11)


@pytest.mark.parametrize("scale", [1e-12, 1.0, 1e12])
def test_v7_population_exclusion_is_invariant_near_a_scaled_bound(scale):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([1.0, 0.2])
    observed = response @ truth
    comparator = np.array([1.0, 0.0])
    lower = np.array([-2.0, -2.0])
    upper = np.array([0.999, 2.0])

    response[:, 0] *= scale
    comparator[0] *= scale
    lower[0] /= scale
    upper[0] /= scale
    report = identified.identified_set_report(
        observed, response, comparator, lower, upper, alpha2=1.0)

    assert report.status == identified.STATUS_EMPTY
    assert report.rank == 2
    assert np.all(np.isnan([
        report.x_lo,
        report.x_hi,
        report.reachable_lo,
        report.reachable_hi,
    ]))


@pytest.mark.parametrize("scale", [1e-12, 1.0, 1e12])
def test_v7_population_exact_boundary_remains_feasible_under_scale(scale):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([1.0, 0.2])
    observed = response @ truth
    comparator = np.array([1.0, 0.0])
    lower = np.array([-2.0, -2.0])
    upper = np.array([1.0, 2.0])

    response[:, 0] *= scale
    comparator[0] *= scale
    lower[0] /= scale
    upper[0] /= scale
    report = identified.identified_set_report(
        observed, response, comparator, lower, upper, alpha2=1.0)

    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == pytest.approx(
        (1.0, 1.0), abs=2e-14)


def test_v7_positive_radius_endpoint_is_scale_invariant_and_analytic():
    from htt.obsstat.egs3_identified_set import (
        identified_set_report,
        reachable_endpoints_closed_form,
    )

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([0.2, -0.3])
    observed = response @ truth
    comparator = np.array([0.4, -0.7])
    lower = np.array([-100.0, -100.0])
    upper = -lower
    baseline = identified_set_report(
        observed, response, comparator, lower, upper, alpha2=0.2)
    analytic = reachable_endpoints_closed_form(
        response, observed, comparator, baseline.tau.tau2)
    assert (baseline.reachable_lo, baseline.reachable_hi) == pytest.approx(
        analytic, abs=1e-9)

    scale = 100000.0
    stressed_response = response.copy()
    stressed_response[:, 0] *= scale
    stressed_comparator = comparator.copy()
    stressed_comparator[0] *= scale
    stressed_lower = lower.copy()
    stressed_upper = upper.copy()
    stressed_lower[0] /= scale
    stressed_upper[0] /= scale
    stressed = identified_set_report(
        observed,
        stressed_response,
        stressed_comparator,
        stressed_lower,
        stressed_upper,
        alpha2=0.2,
    )
    assert (stressed.reachable_lo, stressed.reachable_hi) == pytest.approx(
        (baseline.reachable_lo, baseline.reachable_hi), abs=1e-9)


def test_v7_box_active_endpoint_is_sharp_and_scale_invariant():
    from htt.obsstat.egs3_identified_set import identified_set_report

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([0.2, -0.3])
    observed = response @ truth
    comparator = np.array([0.4, -0.7])
    lower = np.array([0.18, -100.0])
    upper = np.array([100.0, 100.0])
    baseline = identified_set_report(
        observed, response, comparator, lower, upper, alpha2=0.999)

    delta_1 = lower[0] - truth[0]
    delta_2 = (
        -delta_1 + np.sqrt(2.0 * baseline.tau.tau2 - 3.0 * delta_1 ** 2)
    ) / 2.0
    expected_lower = float(
        comparator @ np.array([lower[0], truth[1] + delta_2]))
    assert baseline.reachable_lo == pytest.approx(expected_lower, abs=1e-10)

    scale = 100000.0
    stressed_response = response.copy()
    stressed_response[:, 0] *= scale
    stressed_comparator = comparator.copy()
    stressed_comparator[0] *= scale
    stressed_lower = lower.copy()
    stressed_upper = upper.copy()
    stressed_lower[0] /= scale
    stressed_upper[0] /= scale
    stressed = identified_set_report(
        observed, stressed_response, stressed_comparator,
        stressed_lower, stressed_upper, alpha2=0.999)
    assert (stressed.reachable_lo, stressed.reachable_hi) == pytest.approx(
        (baseline.reachable_lo, baseline.reachable_hi), abs=1e-10)


def test_v7_box_active_endpoint_is_invariant_to_independent_extreme_scales():
    from htt.obsstat.egs3_identified_set import identified_set_report

    response = np.array([
        [0.8798084941547671, 0.041842441409790085],
        [-0.05724763553143051, -1.0812645699206391],
        [-1.118541004266105, 0.45177410139994284],
    ])
    truth = np.array([-0.6584074484182041, -0.981319192706561])
    observed = response @ truth
    comparator = np.array([1.0931103541154148, -0.5751086946412933])
    lower = np.array([-1.0848741170595766, -1.0243292442329566])
    upper = np.array([0.029915924518696735, -0.4300734428128443])
    alpha2 = 0.7585303518326602
    baseline = identified_set_report(
        observed, response, comparator, lower, upper, alpha2=alpha2)

    scale = np.array([579675638156.3582, 9.412188543901518])
    stressed = identified_set_report(
        observed,
        response * scale,
        comparator * scale,
        lower / scale,
        upper / scale,
        alpha2=alpha2,
    )

    assert stressed.status == baseline.status == "feasible"
    assert (stressed.reachable_lo, stressed.reachable_hi) == pytest.approx(
        (baseline.reachable_lo, baseline.reachable_hi), abs=2e-13)


def test_v7_rank_two_face_enumeration_avoids_real_slsqp_failure(monkeypatch):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [-2.096448201956982, 0.6797168074778418],
        [-0.0061956409920737, 0.49144967908892995],
        [-0.7442459285597672, -0.2698996510417867],
        [0.467697641812884, 0.04126766552408576],
        [1.73079173903801, 0.4882029838598173],
    ])
    truth = np.array([0.0064878758068284, -1.2558494528493926])
    comparator = np.array([-0.7601256832753791, -0.28079962967403027])
    lower = np.array([-0.02110834962419701, -1.303923960594401])
    upper = np.array([0.11769164191755827, -1.22158450893779])
    monkeypatch.setattr(
        identified.optimize,
        "minimize",
        lambda *args, **kwargs: pytest.fail(
            "registered rank-2 endpoints must use analytic face enumeration"),
    )

    report = identified.identified_set_report(
        response @ truth,
        response,
        comparator,
        lower,
        upper,
        alpha2=0.9517027729528782,
    )

    assert report.status == identified.STATUS_FEASIBLE
    assert report.reachable_lo == pytest.approx(0.2537189289102975, abs=2e-13)
    assert report.reachable_hi == pytest.approx(0.382186363938911, abs=2e-13)


def test_v7_rank_two_feasible_box_bypasses_approximate_optimizers(monkeypatch):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [-1.21, 0.16],
        [1.74, 0.33],
        [0.67, 1.66],
        [1.37, -1.13],
    ])
    truth = np.array([0.23, -0.7])
    observed = response @ truth
    monkeypatch.setattr(
        identified.optimize,
        "lsq_linear",
        lambda *args, **kwargs: pytest.fail(
            "registered rank-2 feasibility must be analytic"),
    )
    monkeypatch.setattr(
        identified.optimize,
        "minimize",
        lambda *args, **kwargs: pytest.fail(
            "registered rank-2 endpoints must be analytic"),
    )

    report = identified.identified_set_report(
        observed,
        response,
        np.array([0.4, -0.7]),
        np.array([-0.0313, -0.510111]),
        np.array([0.2313, -0.489889]),
        alpha2=0.1,
    )

    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == pytest.approx(
        (0.3304023, 0.4495977), abs=2e-13)


def test_v7_rank_two_full_box_endpoints_survive_large_origin_translation():
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    comparator = np.array([1.0, -1.0])
    centre = np.array([1.0e8, 1.0e8])
    lower = centre - 0.1
    upper = centre + 0.1

    report = identified.identified_set_report(
        response @ centre,
        response,
        comparator,
        lower,
        upper,
        alpha2=0.9,
    )

    expected = (float(lower[0] - upper[1]), float(upper[0] - lower[1]))
    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == expected


def test_v7_ceiling_ambiguity_uses_uncancelled_objective_scale():
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    comparator = np.array([1.0, -1.0])
    centre = np.array([1.0e8, 1.0e8])
    lower = centre - 0.1
    upper = centre + 0.1
    baseline = identified.identified_set_report(
        response @ centre,
        response,
        comparator,
        lower,
        upper,
        alpha2=0.9,
    )

    def report(ceiling):
        return identified.identified_set_report(
            response @ centre,
            response,
            comparator,
            lower,
            upper,
            alpha2=0.9,
            ceiling_U=ceiling,
        )

    with pytest.raises(
            identified.EndpointOptimizationError,
            match="ceiling classification is numerically ambiguous"):
        report(baseline.x_hi + 1.0e-7)
    assert report(baseline.x_hi - 1.0e-4).status == (
        identified.STATUS_CEILING_UNFIT)
    assert report(baseline.x_hi + 1.0e-4).status == identified.STATUS_FEASIBLE


def test_v7_rank_two_continuous_face_endpoint_survives_large_translation():
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    comparator = np.array([1.0, 0.0])
    lower = np.array([-1.0, 0.061])
    upper = np.array([0.08, 1.0])
    translation = np.array([1.0e11, 1.0e11])
    translated_lower = lower + translation
    translated_upper = upper + translation

    report = identified.identified_set_report(
        response @ translation,
        response,
        comparator,
        translated_lower,
        translated_upper,
        alpha2=math.exp(-0.005),
    )

    fixed_delta = float(translated_lower[1] - translation[1])
    continuous_half_width = math.sqrt(report.tau.tau2 - fixed_delta ** 2)
    expected = (
        float(math.fsum((translation[0], -continuous_half_width))),
        float(math.fsum((translation[0], continuous_half_width))),
    )

    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == expected
    assert report.reachable_hi < translated_upper[0]


def test_v7_translated_box_inactive_support_uses_local_centre_refinement():
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [0.1203131746035526, -0.5112050203640084],
        [-0.4053974550451821, -0.40150597869556093],
        [0.9030299412747598, 0.025656376123362527],
        [-0.8399725668667812, -1.3273615652740685],
        [-1.3068623229665421, 0.38352359763066873],
        [-1.2501010214077322, -0.2959033940717367],
    ])
    observed = np.array([
        146338482.12332046,
        -421819897.35554087,
        968760131.05824077,
        -857374811.354383,
        -1416101651.1345346,
        -1332356880.2300694,
    ])
    comparator = np.array([0.3476191044133548, 0.1329409460497445])
    lower = np.array([1073741823.4535451, -33554433.588397063])
    upper = np.array([1073741824.1514452, -33554432.864288345])

    report = identified.identified_set_report(
        observed,
        response,
        comparator,
        lower,
        upper,
        alpha2=0.7428981753119477,
    )

    # Frozen from an exact-Fraction recenter followed by the independent
    # eigen-angle oracle in the O(1) local coordinates.
    expected = (368792413.02217966, 368792413.23354614)
    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == pytest.approx(
        expected, abs=math.ulp(expected[1]))


def test_v7_extreme_scale_and_translation_preserve_local_face_geometry():
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [8004817471.828774, 0.018690837013568846],
        [12609643584.104162, 0.08642363859498135],
        [-4864491049.17721, -0.046943493722058596],
    ])
    observed = np.array([
        1247295332.7680328,
        5764473272.819478,
        -3130909535.5480466,
    ])
    comparator = np.array([27405210386.307533, 0.00017858225761421495])
    lower = np.array([0.00011613293484403472, 66683247434.62355])
    upper = np.array([0.00011613313628519042, 66683247452.089355])

    report = identified.identified_set_report(
        observed,
        response,
        comparator,
        lower,
        upper,
        alpha2=0.8290112676516499,
    )

    # Frozen from exact-Fraction recentering and a 100-digit independent
    # ellipsoid/box optimization.  This combines a 1.8e10 column scale with a
    # 6.7e10 coordinate translation and exercises a box face.
    expected = (15091092.385721145, 15091095.841105761)
    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == pytest.approx(
        expected, abs=2.0e-7)


def test_v7_ceiling_status_fails_closed_inside_endpoint_roundoff_band():
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [8004817471.828774, 0.018690837013568846],
        [12609643584.104162, 0.08642363859498135],
        [-4864491049.17721, -0.046943493722058596],
    ])
    observed = np.array([
        1247295332.7680328,
        5764473272.819478,
        -3130909535.5480466,
    ])
    comparator = np.array([27405210386.307533, 0.00017858225761421495])
    lower = np.array([0.00011613293484403472, 66683247434.62355])
    upper = np.array([0.00011613313628519042, 66683247452.089355])
    exact_upper = 15091095.841105761
    ambiguity = 64.0 * np.finfo(float).eps * exact_upper

    def report(ceiling):
        return identified.identified_set_report(
            observed,
            response,
            comparator,
            lower,
            upper,
            alpha2=0.8290112676516499,
            ceiling_U=ceiling,
        )

    below = report(exact_upper - 4.0 * ambiguity)
    assert below.status == identified.STATUS_CEILING_UNFIT
    assert below.F_hi > 1.0

    with pytest.raises(
            identified.EndpointOptimizationError,
            match="ceiling classification is numerically ambiguous"):
        report(15091095.841105694)

    above = report(exact_upper + 4.0 * ambiguity)
    assert above.status == identified.STATUS_FEASIBLE
    assert above.F_hi < 1.0


def test_v7_rank_two_empty_box_is_certified_analytically(monkeypatch):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    truth = np.array([0.2, -0.3])
    monkeypatch.setattr(
        identified.optimize,
        "lsq_linear",
        lambda *args, **kwargs: pytest.fail(
            "registered rank-2 feasibility must be analytic"),
    )

    report = identified.identified_set_report(
        response @ truth,
        response,
        np.array([0.4, -0.7]),
        np.array([5.0, 5.0]),
        np.array([6.0, 6.0]),
        alpha2=0.999,
    )

    assert report.status == identified.STATUS_EMPTY
    assert np.all(np.isnan([
        report.x_lo,
        report.x_hi,
        report.reachable_lo,
        report.reachable_hi,
    ]))


def test_v7_box_active_higher_rank_is_explicitly_unsupported(monkeypatch):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
    ])
    truth = np.array([0.2, -0.3, 0.1])
    monkeypatch.setattr(
        identified.optimize,
        "minimize",
        lambda *args, **kwargs: pytest.fail(
            "uncertified higher-rank SLSQP must not run"),
    )

    with pytest.raises(
            NotImplementedError,
            match="box-active endpoint sharpness.*rank two"):
        identified.identified_set_report(
            response @ truth,
            response,
            np.array([0.4, -0.7, 0.2]),
            np.array([0.18, -100.0, -100.0]),
            np.array([100.0, 100.0, 100.0]),
            alpha2=0.999,
        )


def test_v7_box_inactive_higher_rank_endpoint_remains_analytic(monkeypatch):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
    ])
    truth = np.array([0.2, -0.3, 0.1])
    observed = response @ truth
    comparator = np.array([0.4, -0.7, 0.2])
    lower = np.full(3, -100.0)
    upper = -lower
    monkeypatch.setattr(
        identified.optimize,
        "minimize",
        lambda *args, **kwargs: pytest.fail(
            "box-inactive endpoints must use the analytic support"),
    )

    report = identified.identified_set_report(
        observed, response, comparator, lower, upper, alpha2=0.999)
    expected = identified.reachable_endpoints_closed_form(
        response, observed, comparator, report.tau.tau2)

    assert report.status == identified.STATUS_FEASIBLE
    assert (report.reachable_lo, report.reachable_hi) == pytest.approx(
        expected, abs=2e-13)


@pytest.mark.parametrize("target", ["y", "R", "c"])
@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_v7_nonfinite_public_arrays_fail_before_scientific_status(
        target, bad_value):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    inputs = {
        "y": response @ np.array([0.2, -0.3]),
        "R": response,
        "c": np.array([0.4, -0.7]),
    }
    inputs[target] = inputs[target].copy()
    inputs[target].flat[0] = bad_value

    with pytest.raises(ValueError, match="finite"):
        identified.identified_set_report(
            inputs["y"],
            inputs["R"],
            inputs["c"],
            np.array([-1.0, -1.0]),
            np.array([1.0, 1.0]),
            alpha2=1.0,
        )


@pytest.mark.parametrize(
    ("bound_name", "bad_value"),
    [
        ("lower", np.nan),
        ("upper", np.nan),
        ("lower", np.inf),
        ("upper", -np.inf),
    ],
)
def test_v7_invalid_component_bounds_fail_before_scientific_status(
        bound_name, bad_value):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    bounds = {
        "lower": np.array([-1.0, -1.0]),
        "upper": np.array([1.0, 1.0]),
    }
    bounds[bound_name][0] = bad_value
    with pytest.raises(ValueError):
        identified.identified_set_report(
            response @ np.array([0.2, -0.3]),
            response,
            np.array([0.4, -0.7]),
            bounds["lower"],
            bounds["upper"],
            alpha2=1.0,
        )


@pytest.mark.parametrize("bad_ceiling", [np.nan, np.inf, -np.inf, 0.0, -1.0])
def test_v7_invalid_ceiling_fails_before_scientific_status(bad_ceiling):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    with pytest.raises(ValueError, match="finite and positive"):
        identified.identified_set_report(
            response @ np.array([0.2, -0.3]),
            response,
            np.array([0.4, -0.7]),
            np.array([-1.0, -1.0]),
            np.array([1.0, 1.0]),
            alpha2=1.0,
            ceiling_U=bad_ceiling,
        )


@pytest.mark.parametrize("bad_tol", [0.0, -1.0, np.nan, np.inf, -np.inf])
def test_v7_invalid_numerical_tolerance_fails_closed(bad_tol):
    from htt.obsstat import egs3_identified_set as identified

    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    with pytest.raises(ValueError, match="tol must be finite and positive"):
        identified.identified_set_report(
            response @ np.array([0.2, -0.3]),
            response,
            np.array([0.4, -0.7]),
            np.array([-1.0, -1.0]),
            np.array([1.0, 1.0]),
            alpha2=1.0,
            tol=bad_tol,
        )


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
