"""Acceptance tests 2, 3, 4, 5 for R49 GBI-02 multi-congruence tilted state and constraints."""
from __future__ import annotations

import math
import numpy as np
import pytest

from bass.background.bianchi_types import build_bianchi_algebra
from bass.background.convention_bridge import (
    ALL_TWELVE_FAMILIES,
    exact_momentum_divergence,
)
from bass.background.geometry import pstf_rank2
from bass.background.initial_conditions import CodazziProjectionError
from bass.background.tilted_bianchi_state import (
    FAMILY_ADMISSIBILITY_REGISTRY,
    SpeciesFluidCongruence,
    aberrate_direction_and_stokes,
    build_frame_transport_bundle,
    compute_species_congruence_kinematics,
    construct_admissible_tilted_state,
    project_stress_tensor_4d_oracle,
    solve_compensating_tilt_velocity,
    wigner_rotate_stf5_on,
)
from common.relativistic_velocity_closure import BetaTruncationError
from common.stf_metric_bridge import (
    orthonormal_to_stf_matrix,
    stf_matrix_to_orthonormal,
)


def test_acceptance_2_4d_lorentz_stress_oracle_and_multi_species_vector_cancellation() -> None:
    """Acceptance Test 2: 4D Lorentz T^{ab} matches analytic boosts & vector tilts cancel cleanly."""
    sp_rad = SpeciesFluidCongruence(
        species="photon",
        eps_hat=0.3,
        p_hat=0.1,
        v_vec=np.array([0.15, -0.08, 0.04], dtype=np.float64),
    )
    oracle = project_stress_tensor_4d_oracle(sp_rad.eps_hat, sp_rad.p_hat, sp_rad.v_vec)
    assert oracle.analytic_vs_4d_max_abs_error < 1.0e-14

    proj = sp_rad.to_projected_state()
    assert abs(proj.rho - oracle.eps_normal) < 1.0e-14
    assert abs(proj.p - oracle.p_normal) < 1.0e-14
    assert np.max(np.abs(proj.q - oracle.q_normal)) < 1.0e-14
    assert np.max(np.abs(proj.pi - oracle.pi_normal)) < 1.0e-14

    # Equal and opposite momentum flux in Bianchi I: non-zero |v_rad|, |v_m| but vector sum == 0
    target_q = oracle.q_normal
    v_mat = solve_compensating_tilt_velocity(-target_q, eps_hat=0.9, p_hat=0.0)
    sp_mat = SpeciesFluidCongruence(species="cdm", eps_hat=0.9, p_hat=0.0, v_vec=v_mat)
    sp_lam = SpeciesFluidCongruence(
        species="lambda", eps_hat=1.8, p_hat=-1.8, v_vec=np.array([0.2, 0.3, 0.0])
    )
    assert sp_lam.speed == 0.0  # Lorentz-invariant vacuum energy

    state = construct_admissible_tilted_state(
        family="I",
        species=[sp_rad, sp_mat, sp_lam],
        sigma_ab=pstf_rank2(np.diag([-0.02, 0.01, 0.01])),
        observer_tilt_vec=np.array([0.001, -0.0005, 0.0002]),
    )
    assert state.constraints.is_admissible is True
    assert float(np.linalg.norm(state.total_matter.q)) < 1.0e-14
    # Relative drift and quadratic anisotropic pressure survive despite zero net momentum!
    assert float(np.linalg.norm(sp_rad.v_vec - sp_mat.v_vec)) > 0.1
    assert float(np.linalg.norm(state.total_matter.pi)) > 1.0e-3

    # Subluminal guard must fail closed for |v| >= 1
    with pytest.raises(BetaTruncationError):
        SpeciesFluidCongruence(species="photon", eps_hat=0.2, p_hat=0.2 / 3.0, v_vec=[0.8, 0.7, 0.0])


def test_acceptance_3_bianchi_i_single_perfect_fluid_tilt_forbidden() -> None:
    """Acceptance Test 3: Single tilted perfect fluid (eps+p>0) in Bianchi I fails Codazzi."""
    assert FAMILY_ADMISSIBILITY_REGISTRY["I"].divergence_rank_on_stf5 == 0
    assert FAMILY_ADMISSIBILITY_REGISTRY["I"].allows_uncompensated_single_perfect_fluid_tilt is False
    assert FAMILY_ADMISSIBILITY_REGISTRY["IX"].divergence_rank_on_stf5 == 0

    single_tilted = SpeciesFluidCongruence(
        species="cdm",
        eps_hat=1.0,
        p_hat=0.0,
        v_vec=np.array([0.05, 0.0, 0.0], dtype=np.float64),
    )
    for fam in ("FLRW", "I", "IX"):
        with pytest.raises(CodazziProjectionError):
            construct_admissible_tilted_state(family=fam, species=[single_tilted])


def test_acceptance_4_non_zero_curvature_class_a_and_b_tilt_fibres_and_vorticity() -> None:
    """Acceptance Test 4: Class A & B Codazzi fibres, Class-B a @ sigma forcing, and vorticity."""
    # All 12 families have registry metadata
    assert set(FAMILY_ADMISSIBILITY_REGISTRY.keys()) == set(ALL_TWELVE_FAMILIES)

    # Class B family (V, VII_h, III, IV, VI_h): diagonal shear along axis 0 triggers a @ sigma != 0
    for fam in ("III", "IV", "V", "VI_h", "VII_h"):
        alg = build_bianchi_algebra(fam)
        # Shear proportional to [-2, 1, 1] has non-zero a @ sigma since a is along axis 0
        sigma_diag = np.diag([-0.04, 0.02, 0.02])
        div_sig = exact_momentum_divergence(sigma_diag, alg.a, alg.n, a_sign=1)
        assert float(np.linalg.norm(div_sig)) > 1.0e-4

        # Orthogonal fluid with this Class-B shear fails Codazzi
        orth_mat = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=[0.0, 0.0, 0.0])
        with pytest.raises(CodazziProjectionError):
            construct_admissible_tilted_state(
                family=fam, sigma_ab=sigma_diag, species=[orth_mat], lambda_value=1.0, codazzi_mode="strict"
            )

        # Compensating single-fluid tilt matching q = -div_sig / kappa satisfies 4D Einstein Codazzi (G^{0i} = kappa q^i)
        v_req = solve_compensating_tilt_velocity(-div_sig, eps_hat=1.0, p_hat=0.0)
        tilted_mat = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=v_req)
        st = construct_admissible_tilted_state(
            family=fam, sigma_ab=sigma_diag, species=[tilted_mat], lambda_value=1.0, codazzi_mode="strict"
        )
        assert st.constraints.is_admissible is True
        assert st.constraints.codazzi_residual_norm < 1.0e-13
        assert abs(st.constraints.hamiltonian_residual) < 1.0e-13

    # Class A with non-zero rank (II, VI_0, VII_0, VIII): off-diagonal shear generates non-zero q
    for fam in ("II", "VI_0", "VII_0", "VIII"):
        alg = build_bianchi_algebra(fam)
        sigma_od = pstf_rank2(
            np.array([[0.01, 0.02, -0.015], [0.02, -0.005, 0.012], [-0.015, 0.012, -0.005]])
        )
        div_sig = exact_momentum_divergence(sigma_od, alg.a, alg.n, a_sign=1)
        assert float(np.linalg.norm(div_sig)) > 1.0e-5
        v_req = solve_compensating_tilt_velocity(-div_sig, eps_hat=1.0, p_hat=0.1)
        sp = SpeciesFluidCongruence(species="baryon", eps_hat=1.0, p_hat=0.1, v_vec=v_req)
        st = construct_admissible_tilted_state(family=fam, sigma_ab=sigma_od, species=[sp], lambda_value=0.5)
        assert st.constraints.is_admissible is True

    # Vorticity test in Bianchi V: tilt parallel to a is irrotational; transverse tilt is rotational
    alg_v = build_bianchi_algebra("V")
    sp_par = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=[0.05, 0.0, 0.0])
    sp_perp = SpeciesFluidCongruence(species="cdm", eps_hat=1.0, p_hat=0.0, v_vec=[0.05, 0.04, 0.0])
    kin_par = compute_species_congruence_kinematics(sp_par, H=0.7, sigma_ab=np.zeros((3, 3)), C_spatial=alg_v.C)
    kin_perp = compute_species_congruence_kinematics(sp_perp, H=0.7, sigma_ab=np.zeros((3, 3)), C_spatial=alg_v.C)
    assert kin_par.vorticity_norm < 1.0e-14
    assert kin_par.u_orthogonality_max_err < 1.0e-14
    assert kin_perp.vorticity_norm > 1.0e-4
    assert kin_perp.u_orthogonality_max_err < 1.0e-14


def test_acceptance_5_boost_composition_wigner_stf5_and_stokes_qu() -> None:
    """Acceptance Test 5: multi-frame SR boosts & Wigner rotation on vectors, STF-5, and Stokes (Q, U)."""
    b_nm = np.array([0.08, -0.03, 0.02], dtype=np.float64)
    b_mr = np.array([0.12, 0.05, -0.04], dtype=np.float64)
    b_mo = np.array([-0.06, 0.14, 0.03], dtype=np.float64)
    ft = build_frame_transport_bundle(
        beta_normal_to_matter=b_nm,
        beta_matter_to_radiation=b_mr,
        beta_matter_to_observer=b_mo,
    )
    assert np.allclose(ft.wigner_matrix @ ft.wigner_matrix.T, np.eye(3), atol=1.0e-14)
    assert ft.wigner_angle_rad > 1.0e-4  # non-collinear boosts produce genuine Wigner rotation

    # STF-5 transformation under Wigner rotation matches full 3x3 similarity R S R^T
    S_raw = np.array([[0.3, -0.1, 0.05], [-0.1, -0.2, 0.07], [0.05, 0.07, -0.1]])
    s5_in = stf_matrix_to_orthonormal(S_raw, convention="kinematic_response")
    s5_rot = ft.transport_stf5_on(s5_in)
    S_expected = ft.wigner_matrix @ S_raw @ ft.wigner_matrix.T
    assert np.allclose(orthonormal_to_stf_matrix(s5_rot, convention="kinematic_response"), S_expected, atol=1.0e-14)

    # Spin-2 Stokes transformation under observer aberration preserves fractional polarization degree (Q^2 + U^2)
    n_hat = np.array([0.4, -0.6, 0.6928203230275509], dtype=np.float64)
    q_in, u_in = 0.035, -0.022
    n_obs, q_obs, u_obs, chi = aberrate_direction_and_stokes(
        n_hat, q_in, u_in, beta=b_mo, wigner_R=ft.wigner_matrix
    )
    assert abs(float(np.linalg.norm(n_obs)) - 1.0) < 1.0e-14
    assert abs(math.hypot(q_obs, u_obs) - math.hypot(q_in, u_in)) < 1.0e-14
    # Non-collinear boost & Wigner rotation alters polarization angle chi consistently
    assert math.isfinite(chi)
