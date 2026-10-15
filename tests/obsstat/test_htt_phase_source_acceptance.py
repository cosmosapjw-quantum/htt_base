"""Real Planck phase-only source comparison and all-six-paper selection controls."""
import json
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
SOURCE=BASE/"legacy_modern_obs_integration_20261015/results/planck_fixed_C2C3_phase_v1"


def actual():
    return json.loads((SOURCE/"result.json").read_text())


def test_analytic_fullsky_conditional_mean_matches_same_phase_cohort():
    a=actual()
    theory=a["conditional_multipole_powers_actual_primary"]
    iso=a["conditional_result_by_distinct_law"]["ideal_gaussian_fixed_phase"]
    ff=a["conditional_result_by_distinct_law"]["FFP10_999_phase_reweighted"]
    expected=theory["theoretical_conditional_mean_k4"]
    assert expected==pytest.approx(2.615553437048453,rel=1e-14)
    assert iso["k4"]["mean"]==pytest.approx(expected,abs=.015)
    assert ff["k4"]["mean"]==pytest.approx(expected,abs=.02)
    assert abs(iso["s3"]["mean"])<.015
    assert abs(ff["s3"]["mean"])<.02
    assert iso["k4"]["descriptive_actual_SMICA_rank"]["physical_null_p_value"].startswith("NOT_ADMITTED")


def test_one_observed_cmb_sky_and_disjoint_ideal_vs_actual_ffp_source_id_banks():
    a=actual()
    assert a["sampled_one_physical_observed_sky"]==1
    assert a["observed_processing_product_count"]==9
    assert a["source_ffp10_CMB_only_unique_realizations"]==999
    assert a["ideal_independent_phase_samples"]==16384
    assert a["ideal_phase_random_seed"]==20261015
    with np.load(SOURCE/"phase_conditioned_source_arrays.npz",allow_pickle=False) as q:
        assert q["ideal_s3"].shape==(16384,)
        assert q["source_ffp10_ids"].shape==(999,)
        assert len(set(q["source_ffp10_ids"].tolist()))==999
        assert len(set(q["ideal_id"].tolist()))==16384
        assert q["actual_same_sky_s3"].shape==(9,)
        assert q["actual_same_sky_k4"].shape==(9,)
        assert not np.any(np.isnan(q["ideal_k4"]))
        assert not np.any(np.isnan(q["source_ffp10_reweighted_k4"]))


def test_shape_phase_comparison_is_descriptive_not_false_p():
    a=actual()
    actual_obs=a["observed_SMICA_FULL_shape"]
    assert actual_obs["s3"]==pytest.approx(-.10157208794969412)
    assert actual_obs["k4"]==pytest.approx(3.159552146301615)
    d=a["conditioned_source_vs_ideal_angular_shape_comparison"]
    assert 0<d["conditional_empirical_CDF_distance_s3"]<.08
    assert 0<d["conditional_empirical_CDF_distance_k4"]<.08
    assert abs(d["FFP10_reweighted_mean_k4_minus_analytic_isotropic_phase_expectation"])<.02
    assert a["phase_only_cosmological_detection"]=="WITHHELD"
    assert a["statistical_law_scope"]["multiple_statistics_selection"].startswith("retrospective")
    assert "NOT the actual masked fit law" in a["statistical_law_scope"]["ideal"]
    for val in a["conditional_result_by_distinct_law"].values():
        for name in ("s3","k4"):
            assert val[name]["descriptive_actual_SMICA_rank"]["physical_null_p_value"].startswith("NOT_ADMITTED")


def test_retrospective_selection_ledger_covers_six_papers_and_preserves_no_detection():
    p=BASE/"CLAIM_SELECTION_LEDGER.json"
    assert p.is_file()
    s=json.loads(p.read_text())
    assert "RETROSPECTIVE" in s["status"]
    assert s["prospective_confirmatory_registration_created"] is False
    assert len(s["papers"])==6
    assert {p["id"] for p in s["papers"]}=={"P1","P2","P3","P4","P5","P6"}
    assert all(p["confirmatory"] is False for p in s["papers"])
    assert all(p["future_frozen_protocol_condition"] for p in s["papers"])
    p2=next(p for p in s["papers"] if p["id"]=="P2")
    assert p2["completed_exploratory_phase_protocol"]["ideal_nsim"]==16384
    assert p2["completed_exploratory_phase_protocol"]["ideal_sim_seed"]==20261015
    assert p2["completed_exploratory_phase_protocol"]["statistical_p_claim"]=="NOT_ADMITTED"
    assert s["publication_gates_all"]=="NOT_READY_TO_SUBMIT"
