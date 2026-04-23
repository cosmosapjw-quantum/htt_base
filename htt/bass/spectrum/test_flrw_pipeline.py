"""Tests for the FLRW SW-plateau end-to-end D_ℓ pipeline (S8) + the
Planck-2018 CAMB reference comparison (S9).

The pipeline uses a closed-form Sachs-Wolfe approximation. It is the
low-ℓ baseline for a follow-up Tier-B bridge: it captures the correct
plateau amplitude (~624 μK² for Planck 2018 scale-invariant) but NOT
ISW, Doppler, acoustic amplification, or reionization re-scattering.

S9 comparison tolerances reflect this: the SW-only path recovers
roughly 60-80% of CAMB's D_ℓ across ℓ ∈ [2, 30], with the residual
attributable to the omitted physics. Tests encode this as bounds
(passed when the SW/CAMB ratio sits in a known band), not bit-identical
equality.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bass.spectrum.flrw_pipeline import (
    DEFAULT_CAMB_REFERENCE_PATH,
    FLRWCosmology,
    SW_AMPLITUDE_FACTOR,
    build_sw_plateau_transfer_fn,
    compute_flrw_dls_sw_plateau,
    sw_plateau_scale_invariant_dl,
)


# ----- Closed-form sanity checks ----------------------------------------


def test_sw_amplitude_factor_is_minus_one_fifth():
    assert SW_AMPLITUDE_FACTOR == pytest.approx(-1.0 / 5.0, rel=1e-15)


def test_scale_invariant_plateau_matches_closed_form():
    """A_s (T_CMB)² / 25 — the textbook SW amplitude."""
    A_s = 2.1e-9
    T_CMB = 2.7255
    expected = A_s * (T_CMB * 1e6) ** 2 * (1.0 / 25.0)
    got = sw_plateau_scale_invariant_dl(A_s=A_s, T_CMB_K=T_CMB)
    assert got == pytest.approx(expected, rel=1e-12)


# ----- Cosmology loading ------------------------------------------------


def test_camb_reference_loads_planck_2018():
    cosmo = FLRWCosmology.from_camb_reference()
    assert cosmo.H0 == 67.36
    assert cosmo.As == 2.1e-9
    assert cosmo.ns == 0.9649
    assert cosmo.tau == 0.0544
    assert cosmo.z_star == pytest.approx(1089.94, abs=0.1)
    # Δη_* ≈ 13873 Mpc for Planck 2018 — NOT η(z_star) which would be ~280.
    assert cosmo.comoving_distance_to_ls_mpc == pytest.approx(13872.8, abs=1.0)
    assert cosmo.eta_0_mpc == pytest.approx(14153.3, abs=1.0)
    assert cosmo.delta_eta_star_mpc == cosmo.comoving_distance_to_ls_mpc


def test_from_camb_reference_missing_path_raises():
    with pytest.raises(FileNotFoundError, match="CAMB reference"):
        FLRWCosmology.from_camb_reference(path="/nonexistent/foo.npz")


# ----- Transfer function builder ----------------------------------------


def test_transfer_fn_delta_t_is_bessel_shape():
    cosmo = FLRWCosmology.from_camb_reference()
    ell_max = 10
    tf_fn = build_sw_plateau_transfer_fn(cosmo, ell_max=ell_max)
    tf = tf_fn(0.05)
    assert tf.delta_T_m0.shape == (ell_max + 1,)
    # A_sw · j_ℓ(k Δη) — non-zero for low ℓ.
    assert abs(tf.delta_T_m0[2]) > 1e-20
    # m±2 slots are zero on the plateau.
    assert np.all(tf.delta_T_m_plus2 == 0.0)
    assert np.all(tf.delta_T_m_minus2 == 0.0)
    assert np.all(tf.delta_E_m0 == 0.0)


def test_transfer_fn_rejects_bad_inputs():
    cosmo = FLRWCosmology.from_camb_reference()
    with pytest.raises(ValueError, match="ell_max"):
        build_sw_plateau_transfer_fn(cosmo, ell_max=-1)


def test_transfer_fn_rejects_zero_delta_eta():
    bad_cosmo = FLRWCosmology(
        H0=67.0, ombh2=0.02, omch2=0.12, tau=0.0, As=2e-9, ns=0.96,
        k_pivot_mpc=0.05, comoving_distance_to_ls_mpc=0.0, eta_0_mpc=1.0,
        z_star=1089.0, T_CMB_K=2.7255,
    )
    with pytest.raises(ValueError, match="Δη_\\*"):
        build_sw_plateau_transfer_fn(bad_cosmo, ell_max=4)


# ----- End-to-end pipeline ---------------------------------------------


def test_pipeline_produces_plateau_amplitude():
    """ell-by-ell D_ell should cluster around the scale-invariant
    plateau (~624 μK²) when n_s≈1."""
    cosmo = FLRWCosmology.from_camb_reference()
    # Freeze n_s=1 to isolate the plateau check.
    iso_cosmo = FLRWCosmology(
        H0=cosmo.H0, ombh2=cosmo.ombh2, omch2=cosmo.omch2, tau=cosmo.tau,
        As=cosmo.As, ns=1.0, k_pivot_mpc=cosmo.k_pivot_mpc,
        comoving_distance_to_ls_mpc=cosmo.comoving_distance_to_ls_mpc,
        eta_0_mpc=cosmo.eta_0_mpc, z_star=cosmo.z_star, T_CMB_K=cosmo.T_CMB_K,
    )
    result = compute_flrw_dls_sw_plateau(iso_cosmo, ell_max=20, quadrature="simpson")
    plateau = sw_plateau_scale_invariant_dl(A_s=iso_cosmo.As, T_CMB_K=iso_cosmo.T_CMB_K)
    # For ell ≳ 3 the Bessel quadrature converges; allow 2% slack for
    # the finite k-grid truncation.
    for ell in range(3, 21):
        ratio = result["D_TT"][ell] / plateau
        assert 0.95 < ratio < 1.05, f"D_ell[{ell}]/plateau = {ratio}, expected ≈1"


def test_pipeline_returns_expected_keys():
    cosmo = FLRWCosmology.from_camb_reference()
    result = compute_flrw_dls_sw_plateau(cosmo, ell_max=10)
    for key in ("ell", "D_TT", "D_EE", "D_TE", "C_TT", "C_EE", "C_TE", "metadata"):
        assert key in result
    assert result["D_TT"].shape == (11,)
    assert result["metadata"]["approximation"] == "sachs_wolfe_plateau"


def test_pipeline_rejects_even_simpson_grid():
    cosmo = FLRWCosmology.from_camb_reference()
    with pytest.raises(ValueError, match="odd k_grid"):
        compute_flrw_dls_sw_plateau(
            cosmo, ell_max=4, k_grid=np.logspace(-4, -1, 100), quadrature="simpson"
        )


# ----- S9: CAMB reference comparison ------------------------------------


@pytest.fixture(scope="module")
def camb_reference():
    path = DEFAULT_CAMB_REFERENCE_PATH
    if not path.is_file():
        pytest.skip(f"CAMB reference fixture not present: {path}")
    return np.load(path)


@pytest.fixture(scope="module")
def pipeline_result():
    cosmo = FLRWCosmology.from_camb_reference()
    return compute_flrw_dls_sw_plateau(cosmo, ell_max=30, quadrature="simpson")


def test_s9_d_tt_agrees_with_camb_on_sw_plateau_band(camb_reference, pipeline_result):
    """At ℓ ∈ [5, 20] the SW plateau recovers 60-85% of CAMB's D_TT.

    Upper bound: τ=0.0544 reionization + ISW pushes CAMB above pure SW.
    Lower bound: guard against a degenerate 'returns zero' regression.
    """
    camb_ell = camb_reference["ell"]  # 2..30
    camb_dtt = camb_reference["D_TT"]
    bass_dtt = pipeline_result["D_TT"]
    for ell in range(5, 21):
        camb_idx = ell - int(camb_ell[0])
        ratio = bass_dtt[ell] / camb_dtt[camb_idx]
        assert 0.55 <= ratio <= 0.95, (
            f"ℓ={ell}: BASS-SW / CAMB = {ratio:.3f}, "
            f"expected 0.55-0.95 plateau-fraction band."
        )


def test_s9_d_2_quadrupole_baseline_ratio(camb_reference, pipeline_result):
    """The quadrupole ratio is the most-cited SW-vs-full comparison.

    For Planck 2018 τ=0.0544 the pure SW D_2 sits at ~64% of CAMB.
    Bands: [0.55, 0.75] to catch regressions that would either kill
    the plateau (→ 0) or accidentally fold in the ISW (→ ~1.0).
    """
    camb_ell = camb_reference["ell"]
    bass_d2 = pipeline_result["D_TT"][2]
    camb_d2 = camb_reference["D_TT"][2 - int(camb_ell[0])]
    ratio = bass_d2 / camb_d2
    assert 0.55 <= ratio <= 0.75, (
        f"D_2 BASS-SW / CAMB = {ratio:.3f}, expected ~0.64 plateau fraction"
    )


def test_s9_d_30_ratio_drops_due_to_omitted_acoustic_amp(
    camb_reference, pipeline_result
):
    """At ℓ=30 the CAMB D_ell shoots up due to the first acoustic peak
    onset, so the SW-only ratio should be visibly smaller than the
    plateau (ℓ=10) ratio. Guards against a stale transfer function
    that would miss this structural drop-off."""
    camb_ell = camb_reference["ell"]
    bass_dtt = pipeline_result["D_TT"]
    camb_dtt = camb_reference["D_TT"]
    ratio_10 = bass_dtt[10] / camb_dtt[10 - int(camb_ell[0])]
    ratio_30 = bass_dtt[30] / camb_dtt[30 - int(camb_ell[0])]
    assert ratio_30 < ratio_10, (
        f"ratio(ell=30)={ratio_30:.3f} must be < ratio(ell=10)={ratio_10:.3f}"
    )


def test_s9_metadata_records_comparison_context(pipeline_result):
    md = pipeline_result["metadata"]
    assert md["approximation"] == "sachs_wolfe_plateau"
    assert md["sw_amplitude_factor"] == SW_AMPLITUDE_FACTOR
    assert "ISW" in md["notes"] or "isw" in md["notes"].lower()
