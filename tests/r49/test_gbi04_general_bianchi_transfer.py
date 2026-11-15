"""GBI-04 tests: family-dispatched polarized transfer & Acceptance Test 8."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.linalg import expm

from bass.background.convention_bridge import ALL_TWELVE_FAMILIES
from bass.background.general_tilted_evolution import (
    TiltedEvolutionConfig,
    _build_default_admissible_state_for_family,
    evolve_general_tilted_bianchi,
)
from bass.transport.general_bianchi_transfer import (
    FAMILY_TRANSFER_METADATA,
    OutOfScopeError,
    TRANSFER_MODE_GEODESIC,
    TRANSFER_MODE_LINEARIZED,
    TiltedTransferParameters,
    build_general_transfer_verification_report,
    compute_general_bianchi_transfer,
    gl_sphere_grid,
    map_from_scalar_alm,
    qu_from_spin2_alm,
    scalar_alm_from_map,
    spin2_alm_from_qu,
)


def test_spin2_and_scalar_harmonic_roundtrip_precision() -> None:
    th, ph, _, w = gl_sphere_grid(18)
    alm_t_in = {(0, 0): 0.0j, (1, 0): 0.3j + 0.0, (2, 0): 0.5 + 0j, (2, 2): 0.2 + 0.4j, (2, -2): 0.2 - 0.4j}
    alm_t_in[(1, 0)] = 0.3 + 0j
    t_map = map_from_scalar_alm(alm_t_in, th, ph, ell_max=4)
    alm_t_out = scalar_alm_from_map(t_map, th, ph, w, ell_max=4)
    for k, val in alm_t_in.items():
        assert abs(alm_t_out[k] - val) < 1.0e-13

    alm_e_in = {(2, 0): 1.0 + 0j, (2, 1): 0.4 - 0.3j, (2, -1): -0.4 - 0.3j, (2, 2): 0.2 + 0.5j, (2, -2): 0.2 - 0.5j}
    alm_b_in = {(2, 0): 0.0j, (2, 1): 0.2 + 0.1j, (2, -1): -0.2 + 0.1j}
    q_map, u_map = qu_from_spin2_alm(alm_e_in, alm_b_in, th, ph, ell_max=4)
    alm_e_out, alm_b_out = spin2_alm_from_qu(q_map, u_map, th, ph, w, ell_max=4)
    for m in range(-2, 3):
        assert abs(alm_e_out[(2, m)] - alm_e_in.get((2, m), 0j)) < 1.0e-13
        assert abs(alm_b_out[(2, m)] - alm_b_in.get((2, m), 0j)) < 1.0e-13


def test_acceptance_8_family_dispatched_polarized_transfer_and_scope() -> None:
    sig_diag = np.diag([1.0e-5, -0.5e-5, -0.5e-5])
    sig_off = np.array(
        [[0.8e-5, 0.4e-5, 0.2e-5], [0.4e-5, -0.3e-5, -0.1e-5], [0.2e-5, -0.1e-5, -0.5e-5]],
        dtype=np.float64,
    )

    # 1. Non-FLRW-limit families MUST fail closed with OutOfScopeError in linearized near-FLRW mode
    for marginal_fam in ("II", "III", "IV", "VI_0", "VI_h", "VIII"):
        assert not FAMILY_TRANSFER_METADATA[marginal_fam].flrw_limit_admissible
        with pytest.raises(OutOfScopeError):
            compute_general_bianchi_transfer(
                TiltedTransferParameters(
                    family=marginal_fam,
                    sigma_N=sig_diag,
                    transfer_mode=TRANSFER_MODE_LINEARIZED,
                )
            )

    # 2. All 12 families succeed in exact_geodesic_background mode with screen orthonormality
    for fam in ALL_TWELVE_FAMILIES:
        out_geo = compute_general_bianchi_transfer(
            TiltedTransferParameters(
                family=fam,
                sigma_N=np.diag([0.04, -0.02, -0.02]),
                omega_k=0.05 if fam not in {"FLRW", "I", "VII_0"} else 0.0,
                n_efolds_star=-1.0,
                ell_max=6,
                n_gl_theta=14,
                transfer_mode=TRANSFER_MODE_GEODESIC,
            )
        )
        assert out_geo.max_screen_ortho_err < 1.0e-12
        assert out_geo.max_null_err < 1.0e-12
        if fam in {"FLRW", "I", "V"}:
            assert out_geo.max_psi_prime < 1.0e-11
            assert float(np.max(out_geo.cl_BB)) < 1.0e-28

    # 3. Bianchi I exact endpoint agreement with analytic [n^T exp(+2 B_*) n]^(-1/2)
    B_end = np.array([[0.04, 0.01, -0.005], [0.01, -0.015, 0.008], [-0.005, 0.008, -0.025]])
    out_b1 = compute_general_bianchi_transfer(
        TiltedTransferParameters(
            family="I",
            sigma_N=B_end,
            n_efolds_star=-1.0,
            n_geodesic_steps=128,
            ell_max=8,
            n_gl_theta=18,
            transfer_mode=TRANSFER_MODE_GEODESIC,
        )
    )
    analytic = np.einsum("...i,ij,...j->...", out_b1.n_hat_grid, expm(2.0 * B_end), out_b1.n_hat_grid) ** -0.5
    analytic = analytic / (np.sum(analytic * out_b1.weights_gl) / (4.0 * np.pi)) - 1.0
    assert float(np.max(np.abs(out_b1.cosmo_T_map - analytic))) < 1.0e-12

    # 4. Helical VII_h handedness chirality: B > 0 and TB/EB flip sign with handedness +1 <-> -1
    out_viih_p = compute_general_bianchi_transfer(
        TiltedTransferParameters(
            family="VII_h",
            sigma_N=sig_off,
            h_bianchi=0.25,
            omega_k=0.1,
            x_curvature=1.5,
            handedness=1,
            ell_max=8,
            n_gl_theta=18,
            transfer_mode=TRANSFER_MODE_LINEARIZED,
        )
    )
    out_viih_m = compute_general_bianchi_transfer(
        TiltedTransferParameters(
            family="VII_h",
            sigma_N=sig_off,
            h_bianchi=0.25,
            omega_k=0.1,
            x_curvature=1.5,
            handedness=-1,
            ell_max=8,
            n_gl_theta=18,
            transfer_mode=TRANSFER_MODE_LINEARIZED,
        )
    )
    assert out_viih_p.cl_BB[2] > 0.0
    assert out_viih_p.cl_TB[2] * out_viih_m.cl_TB[2] < 0.0
    assert out_viih_p.cl_EB[2] * out_viih_m.cl_EB[2] < 0.0

    # 5. Distinct congruence frame channels & exact comoving cancellation (v_obs == v_rad)
    out_comov = compute_general_bianchi_transfer(
        TiltedTransferParameters(
            family="I",
            sigma_N=np.zeros((3, 3)),
            v_matter=(0.0, 0.0, 0.0),
            v_rad=(0.0, 0.0, 1.2e-3),
            v_obs=(0.0, 0.0, 1.2e-3),
            ell_max=6,
            n_gl_theta=14,
            transfer_mode=TRANSFER_MODE_LINEARIZED,
        )
    )
    assert float(np.max(np.abs(out_comov.T_map))) < 1.0e-12
    # And distinct v_matter == v_rad vs v_obs != 0 keeps cosmo_T dipole zero while populating obs_T dipole
    rep = build_general_transfer_verification_report()
    assert rep["all_passed"]


def test_transfer_coupled_to_dynamic_gbi03_evolution_trajectory() -> None:
    st0 = _build_default_admissible_state_for_family("VII_h")
    traj = evolve_general_tilted_bianchi(
        st0,
        eos_by_species={"photon": 1.0 / 3.0, "cdm": 0.0},
        config=TiltedEvolutionConfig(N_start=0.0, N_end=1.0, n_eval=41, method="DOP853", rtol=1e-9, atol=1e-11),
    )
    out_traj = compute_general_bianchi_transfer(
        TiltedTransferParameters(
            family="VII_h",
            sigma_N=traj.sigma_ab_grid[-1] / traj.H_grid[-1],
            trajectory=traj,
            ell_max=6,
            n_gl_theta=14,
            transfer_mode=TRANSFER_MODE_GEODESIC,
        )
    )
    assert out_traj.max_screen_ortho_err < 1.0e-12
    assert out_traj.max_null_err < 1.0e-12
    assert float(out_traj.cl_TT[2]) > 0.0
