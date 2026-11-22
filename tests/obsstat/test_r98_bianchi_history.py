"""Regression contracts for early-slice R49 histories and passive transfer."""
import numpy as np
import pytest

from scripts.r98 import bianchi_history as h


@pytest.fixture(scope="module")
def projection():
    return h.Angular(5)


def test_flat_background_and_zero_sky(projection):
    state, traj = h.background("FLRW",samples=161)
    geom, audit = h.background_checks(state,traj)
    assert audit["max_relative_H_vs_reference_FLRW"] < 2e-8
    assert audit["hamiltonian_abs_over_3H2"] < 3e-8
    assert audit["conformal_simpson_vs_ivp_relative"] < 2e-6
    y,tau = h.evolve(projection,traj,geom,1)
    assert tau > 1
    np.testing.assert_array_equal(y,0.)


@pytest.mark.parametrize("family,h_expected",[("I",None),("V",None),("VII_h",.25),("VI_h",-1/9)])
def test_full_epoch_constraints_and_group_parameter(family,h_expected):
    state,traj = h.background(family,samples=101)
    geom,audit = h.background_checks(state,traj)
    assert audit["hamiltonian_abs_over_3H2"] < 3e-8
    assert audit["codazzi_relative_to_uncancelled_flux"] < 1e-7
    assert audit["jacobi_relative"] < 1e-12
    assert audit["jacobi_over_H2"] < 1e-15
    assert audit["max_normal_baryon_speed_over_c"] < 1e-12
    assert 0 < audit["max_species_speed_over_c"] < 1
    assert np.linalg.norm(geom[-1]-geom[0]) > 1e-6
    if h_expected is not None:
        np.testing.assert_allclose(audit["h_range"],h_expected,rtol=1e-11)


def test_projection_linearity_separate_source_and_quadrature(projection):
    g = np.array([-.031,.009,.004,-.007,.011,.009,.002,-.005,.011,.019,-.001,.002,.009,.013])
    other = -.7*g
    sig,a,n = h.unpack_geometry(g)
    mat = projection.matrix(g,other,0.).toarray()
    direct = h.r97._project_gamma4_to_coupled_m_operators(
        projection.L,projection.m,projection.idx,projection.dim,sig,a,n,n_gl_theta=24)["M_geo_exact"]
    np.testing.assert_allclose(mat[:-1,:-1],direct.toarray(),atol=8e-14,rtol=0)
    # Scalar quadrupole axis check: integral Y20* P2 dOmega = sqrt(4 pi/5).
    source = np.zeros(14)
    source[:2]=-.5
    analytic = projection.matrix(np.zeros(14),source,0.)[projection.idx["T"][2,0],-1]
    np.testing.assert_allclose(analytic,-np.sqrt(4*np.pi/5),atol=1e-13)
    np.testing.assert_allclose(mat[:-1,-1],projection.sources@other,atol=1e-15)


def test_midpoint_rates_and_domain(projection):
    state,traj = h.background("VII_h",samples=161)
    geom,_ = h.background_checks(state,traj)
    dN,_,rate,_ = h.timeline(traj,geom,2)
    assert np.all(dN>0) and np.all(rate>=0)
    np.testing.assert_allclose(dN.sum(),np.log1p(1600.),rtol=1e-14)
    with pytest.raises(ValueError, match="extrapolate"):
        h.timeline(h.replace(traj,N_grid=traj.N_grid+.01),geom,1)
    dynamic,_ = h.evolve(projection,traj,geom)
    frozen,_ = h.evolve(projection,traj,geom,freeze_geometry=True)
    assert np.linalg.norm(dynamic-frozen) > 1e-11
    assert (abs(dynamic[projection.idx["E"][2,0]])>0.)
    assert (abs(dynamic[projection.idx["B"][2,0]])>0.)


def test_protocol_rejects_invalid_early_states():
    with pytest.raises(ValueError):
        h.early_state("I",np.nan)
    with pytest.raises(ValueError):
        h.early_state("unclassified")

def test_one_way_hydrogen_same_physics_expansion_clock():
    _,flat = h.background("FLRW",samples=321)
    _,curved = h.background("VI_h",samples=321)
    ref = h.hydrogen_window(flat)
    row = h.hydrogen_window(curved)
    assert 0 < row["x_H_end"] < row["x_H_start"] < 1
    assert row["tau_window"] > 0
    assert abs(ref["model_minus_same_chemistry_reference_tau"]) < 1e-8
    delta = abs(row["model_minus_same_chemistry_reference_tau"])
    assert delta > 10 * row["max_abs_tau_rtol_refinement"]
    assert row["directional_shear_over_H_rms"] > 0.0
    assert row["perturbative_escape_delta_tau"] != 0.0
    assert not row["fed_into_harmonic_sky"]


def test_radiation_feedback_conservation_and_flrw_null(projection):
    st_f, tr_f = h.background("FLRW", samples=161)
    g_f, _ = h.background_checks(st_f, tr_f)
    _, _, yf, gf, df, rf = h.evolve(projection, tr_f, g_f, 1, return_history=True)
    fb_f = h.radiation_feedback_audit(projection, tr_f, g_f, yf, gf, df, rf)
    assert fb_f["momentum_exchange_conservation_defect_max"] == 0.0
    assert fb_f["max_1loop_delta_sigma_over_H"] == 0.0
    assert fb_f["feedback_sky_delta_norm_T2_to_5"] == 0.0

    st_v, tr_v = h.background("VII_h", samples=161)
    g_v, _ = h.background_checks(st_v, tr_v)
    _, _, yv, gv, dv, rv = h.evolve(projection, tr_v, g_v, 1, return_history=True)
    fb_v = h.radiation_feedback_audit(projection, tr_v, g_v, yv, gv, dv, rv)
    assert fb_v["momentum_exchange_conservation_defect_max"] <= 1e-15
    assert fb_v["max_1loop_delta_sigma_over_H"] > 0.0
    assert fb_v["feedback_sky_delta_norm_T2_to_5"] > 0.0


@pytest.mark.skipif(not h.ANILOS_ARCHIVE.exists(), reason="pinned AniLoS archive required")
def test_anilos_near_isotropic_kappa_zeta_parity(projection):
    atlas = h.anilos_and_ic_atlas_audit(projection)
    assert atlas["kappa_vs_r98_cspin_max_abs_diff"] < 1e-14
    assert atlas["zeta_factor_m0_exact_max_err"] < 1e-15
    assert atlas["zeta_factor_m_parity_max_err"] < 1e-15
    assert set(atlas["primordial_ic_atlas_near_isotropic_I_V_VIIh"]) == {"I", "V", "VII_h"}
