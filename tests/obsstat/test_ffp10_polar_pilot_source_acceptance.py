"""Saved real FFP10 polarized source pilot acceptance, no physical-null pass."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015/results"
PILOT=BASE/"L01_FFP10_QU_12pair_hashed"
SMOKE=BASE/"L01_FFP10_QU_2pair_SMOKE"


def test_real_raw_ffp10_source_cohorts_are_unique_and_hashed():
    d=json.loads((PILOT/"result.json").read_text())
    assert d["simulation_raw_source_cmb_count"]==12
    assert d["simulation_raw_source_noise_count"]==12
    assert d["simulation_unique_pair_count"]==12
    assert d["source_native_pol_mask"]["selected_nside_out_pix"]==30021
    assert d["source_COORDFRAME"]=="UNSPECIFIED_IN_FITS_HEADER"
    assert d["source_POLCONV"]=="UNSPECIFIED_IN_FITS_HEADER"
    assert d["formal_sim_U_sign_chart"]=="U_PLUS_ASSUMED"
    assert "NOT_A_PLANCK" in d["scientific_claim"]
    for kind in ("cmb","noise"):
        rows=d["source_banks"][kind]
        assert [r["mc_id"] for r in rows]==list(range(12))
        assert len(set(r["source_sha256"] for r in rows))==12
        assert all(len(r["source_sha256"])==64 for r in rows)
        assert all(r["source_size_bytes"]==603987840 for r in rows)


def test_saved_real_pilot_has_exact_unique_cohort_rank_and_closure():
    d=json.loads((PILOT/"result.json").read_text())
    assert d["covariance_numerical_rank"]["noise_conditional_cov_rank"]==11
    assert d["covariance_numerical_rank"]["noise_max_empirical_rank"]==11
    assert d["quadratic_closure_maxabs"]<1e-14
    control=d["source_banks"]["cmb"][0]["independent_raw_to_k1_temperature_control"]
    assert control["maxabs_microK"]<1e-9
    with np.load(PILOT/"paired_coefficients_lowell.npz",allow_pickle=False) as z:
        signal=z["signal_microK"]
        noise=z["noise_microK"]
        paired=z["signal_plus_noise_microK"]
        observed=z["observed_microK"]
        assert signal.shape==noise.shape==paired.shape==(12,64)
        assert observed.shape==(64,)
        np.testing.assert_allclose(paired,signal+noise,atol=2e-15,rtol=0)
        assert np.all(np.isfinite(paired))


def test_two_pair_smoke_and_full_hashed_real_cohort_numerical_source_identity():
    with np.load(SMOKE/"paired_coefficients_lowell.npz",allow_pickle=False) as f:
        with np.load(PILOT/"paired_coefficients_lowell.npz",allow_pickle=False) as a:
            for key in ("signal_microK","noise_microK","signal_plus_noise_microK"):
                np.testing.assert_array_equal(f[key],a[key][:2])
            np.testing.assert_array_equal(f["observed_microK"],a["observed_microK"])


def test_observed_band_diagnostic_keeps_unqualified_numerical_result():
    a=json.loads((PILOT/"DESCRIPTIVE_SUMMARY.json").read_text())
    s=json.loads((PILOT/"result.json").read_text())
    assert a["observation_and_MC_exchangeability"]=="NOT_ADMITTED_NO_PHYSICAL_P_VALUE"
    assert a["formal_small_cohort_mc_tail_resolution_if_exchangeable_only"]==1/13
    np.testing.assert_allclose(a["observed_source_bands_microK2"],
                               s["actual_observed_one_sky_four_EB_bands_microK2"],rtol=0)
    assert a["observed_source_bands_microK2"][1] > s["CMB_plus_noise_matched_empirical_bands"]["max"][1]
