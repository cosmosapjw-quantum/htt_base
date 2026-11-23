"""Tests for R100 Part E (coupled Bianchi + radiation backreaction, Thomson dipole, P2 SHA guard, PHY01-07)."""
from __future__ import annotations

import json
import numpy as np
import pytest

from scripts.r98 import bianchi_history as r98_bh
from scripts.r100 import bianchi_selfconsistent_and_phy as r100_e


def test_dipole_projection_exact_inverse_and_thomson_elasticity():
    """Verify M_dip @ (4*pi*M_dip^H @ v) == v / 3 and covariant Thomson orthogonality u_{b,mu} F^mu == 0."""
    M_dip, _ = r98_bh.radiation_moment_operators()
    v = np.array([1.2e-5, -0.7e-5, 0.4e-5])
    t1m = r100_e.project_vector_to_y1m(v, M_dip)
    assert np.allclose((M_dip @ t1m).real, v / 3.0, rtol=1e-13, atol=1e-18)
    # Reality condition (-1)^m a_{1,-m}^* == a_{1,m}
    assert abs(t1m[2] + np.conj(t1m[0])) < 1e-15
    assert abs(t1m[1].imag) < 1e-15

    T4_rad = np.array([
        [1.0, 2e-4, -1e-4, 5e-5],
        [2e-4, 1.0 / 3.0 + 1e-5, -2e-6, 1e-6],
        [-1e-4, -2e-6, 1.0 / 3.0 - 5e-6, 3e-6],
        [5e-5, 1e-6, 3e-6, 1.0 / 3.0 - 5e-6],
    ])
    vb = np.array([0.05, -0.03, 0.02])
    F = r100_e.covariant_thomson_force_dN(T4_rad, vb, 10.0)
    gb = 1.0 / np.sqrt(1.0 - float(vb @ vb))
    u_cov = np.r_[-gb, gb * vb]
    assert abs(float(u_cov @ F)) < 1e-14


def test_collisionless_radau_vs_r98_dop853_and_flrw_null():
    """Verify collisionless Radau reproduces R98 DOP853 on Bianchi I and FLRW gives zero backreaction."""
    _, tr_radau, diag_i = r100_e.evolve_coupled_bianchi_with_radiation("I", epsilon=1e-5, samples=65, thomson_coupling=False, rtol=1e-10, atol=1e-14)
    _, tr_dop = r98_bh.background("I", epsilon=1e-5, samples=65)
    assert np.max(np.abs(tr_radau.H_grid - tr_dop.H_grid) / tr_dop.H_grid) < 1e-7
    assert np.max(np.abs(tr_radau.sigma_ab_grid - tr_dop.sigma_ab_grid)) < 1e-9
    assert diag_i["max_codazzi_rel"] < 1e-8

    st_f, tr_f, diag_f = r100_e.evolve_coupled_bianchi_with_radiation("FLRW", epsilon=1e-5, samples=65, thomson_coupling=True)
    assert np.max(np.abs(tr_f.sigma_ab_grid)) < 1e-15
    assert np.max(np.abs(tr_f.species_v_grid["baryon"])) < 1e-15
    assert diag_f["max_total_4mom_exchange_defect"] == 0.0


def test_coupled_vih_pi_backreaction_and_p2_guard():
    """Verify DEC-admissible pi_gamma(N) backreacts cleanly preserving Hamiltonian/Codazzi & P2 SHA guard."""
    p2 = r100_e.verify_p2_cmb_sha_guard()
    assert p2["matched_r98_cross_phy_pin"] is True
    assert p2["physical_Pi"] is None

    pi_shape = np.array([[1.0, 0.2, -0.1], [0.2, -0.5, 0.15], [-0.1, 0.15, -0.5]])
    n0 = float(r98_bh.N_INITIAL)
    rho0_rad = float(r98_bh.early_state("VI_h", 1e-5).species_congruences[0].eps_hat)
    # Physical anisotropic stress scaling with a^-4 ~ rho_rad(N) (respecting Dominant Energy Condition)
    pi_phys = lambda N_val: 1.0e-5 * rho0_rad * np.exp(-4.0 * (N_val - n0)) * pi_shape
    _, tr0, d0 = r100_e.evolve_coupled_bianchi_with_radiation("VI_h", epsilon=1e-5, samples=65, pi_rad_fn=None, thomson_coupling=True)
    _, tr1, d1 = r100_e.evolve_coupled_bianchi_with_radiation("VI_h", epsilon=1e-5, samples=65, pi_rad_fn=pi_phys, thomson_coupling=True)
    assert d0["max_codazzi_rel"] < 1e-7 and d1["max_codazzi_rel"] < 1e-7
    assert d0["max_hamiltonian_abs_over_3H2"] < 1e-7 and d1["max_hamiltonian_abs_over_3H2"] < 1e-7
    assert d1["max_total_4mom_exchange_defect"] < 1e-15
    assert d1["max_thomson_elastic_orthog_defect"] < 1e-12
    assert np.max(np.abs(tr1.sigma_ab_grid - tr0.sigma_ab_grid)) > 1e-10
    # Unphysical DEC-violating constant pi >> rho_rad(z=0) must be caught cleanly (never silently accept superluminal v >= c)
    with pytest.raises(Exception):
        r100_e.evolve_coupled_bianchi_with_radiation("VI_h", epsilon=1e-5, samples=33, pi_rad_fn=lambda _n: 1e-10 * pi_shape, thomson_coupling=True)


def test_r100_bianchi_phy_result_contracts():
    """Verify BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json convergence, zero FLRW backreaction, and all PHY01-07."""
    path = r100_e.OUT_DIR / "BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json"
    if not path.exists():
        pytest.skip("BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json not generated yet")
    d = json.loads(path.read_text())
    assert d["physical_Pi"] is None
    assert d["physical_GF"] is None
    assert d["calibrated_p"] is None
    assert d["Bianchi_family_attribution"] is None
    assert len(d["PHY01_to_PHY07"]) == 7

    fams = d["self_consistent_bianchi_radiation_coupling"]["families"]
    assert fams["FLRW"]["fixed_point_iterations_k0_to_4"][-1]["T_norm_2to5"] < 1e-12
    for fam in ("I", "V", "VII_h", "VI_h"):
        its = fams[fam]["fixed_point_iterations_k0_to_4"]
        assert its[-1]["codazzi_rel"] < 1e-6
        assert its[-1]["hamiltonian_abs_over_3H2"] < 1e-6
        assert its[-1]["delta_teb_l2_from_prev"] < 1e-8
        assert its[-1]["momentum_exchange_defect"] < 1e-15
