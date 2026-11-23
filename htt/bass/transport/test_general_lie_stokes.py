"""Unit tests for native all-m general-Lie polarized I/Q/U/V transport (N1)."""
from __future__ import annotations

import math
import numpy as np
from numpy.testing import assert_allclose
import pytest
from scipy.linalg import expm
from scipy.spatial.transform import Rotation

from bass.background.convention_bridge import exact_spatial_ricci_from_compact
from bass.background.general_tilted_evolution import _build_default_admissible_state_for_family
from bass.background.geometry import pstf_rank2
from bass.background.bianchi_types import build_bianchi_algebra
from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.transport.general_bianchi_transfer import (
    _fast_scalar_alm_from_gl,
    _spherical_screen_basis,
    gl_sphere_grid,
    integrate_polarized_geodesics,
)
from bass.transport.general_lie_stokes import (
    GeneralLieStokesOperator,
    LieGeometry,
    alm_dict_to_vector,
    max_stokes_reality_error,
    stokes_maps_to_vector,
    validate_lie_algebra,
    vector_to_alm_dict,
    vector_to_stokes_maps,
)
from bass.transport.stokes_fourier import FourierStokesPropagator


def test_jacobi_guard_and_structure_validation() -> None:
    validate_lie_algebra([0.0, 0.0, 0.0], np.zeros((3, 3)))
    alg = build_bianchi_algebra("VII_h", n1=0.05, n3=0.05, a_twist=0.025)
    validate_lie_algebra(alg.a, alg.n)
    # Break Jacobi N @ a == 0
    with pytest.raises(ValueError, match="Jacobi"):
        validate_lie_algebra([0.0, 0.0, 1.0], np.diag([1.0, 1.0, 1.0]))
    # Asymmetric n_mat rejected
    with pytest.raises(ValueError, match="symmetric"):
        validate_lie_algebra([0.0, 0.0, 0.0], np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]))


def test_rank9_thomson_matches_angular_propagator_including_V() -> None:
    L = 5
    op = GeneralLieStokesOperator(L, n_gl_theta=14)
    _, _, d, w = gl_sphere_grid(14)
    n_flat = d.reshape(-1, 3)
    u, v = _spherical_screen_basis(n_flat)
    ang = ThomsonCoherencyPropagator(n_flat, w.ravel(), u, v)

    # Populate arbitrary real sky up to L in all 4 Stokes channels
    rng = np.random.default_rng(10201)
    y = np.zeros(op.dim, dtype=np.complex128)
    for ch, lmin in (("T", 0), ("E", 2), ("B", 2), ("V", 0)):
        for ell in range(lmin, L + 1):
            y[op.idx[ch][(ell, 0)]] = rng.normal()
            for m in range(1, ell + 1):
                c = rng.normal() + 1j * rng.normal()
                y[op.idx[ch][(ell, m)]] = c
                y[op.idx[ch][(ell, -m)]] = ((-1) ** m) * np.conj(c)
    assert max_stokes_reality_error(y, op.idx) < 1e-14

    sky = vector_to_stokes_maps(y, op.idx, L=L, n_gl_theta=14).real.reshape(-1, 4)
    coll_ang = ang.collision(sky)
    coll_vec_from_ang = stokes_maps_to_vector(coll_ang, op.idx, op.dim, L=L, n_gl_theta=14)
    coll_vec_op = op.apply(y, np.zeros(14), 1.0)
    assert_allclose(coll_vec_op, coll_vec_from_ang, atol=2e-14, rtol=1e-13)
    # Check specific eigenvalues: V_00 rate -1, V_1m rate -1/2, T2-E2 offdiag +sqrt(6)/10
    K = op.K_dense_matrix.toarray()
    assert_allclose(K[op.idx["V"][(0, 0)], op.idx["V"][(0, 0)]], -1.0, atol=1e-15)
    assert_allclose(K[op.idx["V"][(1, 1)], op.idx["V"][(1, 1)]], -0.5, atol=1e-15)
    assert_allclose(K[op.idx["T"][(2, 0)], op.idx["E"][(2, 0)]], math.sqrt(6.0) / 10.0, atol=1e-15)


def test_stiff_stage_solver_and_deep_monopole_conservation() -> None:
    op = GeneralLieStokesOperator(4)
    st = _build_default_admissible_state_for_family("VII_h")
    geom = LieGeometry(sigma_N=st.sigma_ab / st.H, a_N=st.algebra.a / st.H, n_N=st.algebra.n / st.H)
    M_base = op.base_operator(geom, k_eff=(0.2, -0.1, 0.3))
    rhs = np.zeros(op.dim, dtype=np.complex128)
    rhs[op.idx["T"][(0, 0)]] = 1.5
    rhs[op.idx["T"][(2, 1)]] = 0.2 - 0.1j
    rhs[op.idx["V"][(1, -1)]] = -0.3 + 0.05j

    for tau in (0.0, 1.0, 1e3, 1e8):
        gamma_h = 0.3
        solve = op.factor_sdirk_stage(M_base, gamma_h, tau)
        x = solve(rhs)
        residual = x - gamma_h * (M_base @ x + tau * (op.K_dense_matrix @ x)) - rhs
        assert np.linalg.norm(residual) / np.linalg.norm(rhs) < 1e-12

    # Isotropic monopole invariant under extreme stiffness s=1e20 even with nontrivial k=0 Lie shear=0
    iso = np.zeros(op.dim, dtype=np.complex128)
    iso[op.idx["T"][(0, 0)]] = 2.725
    out_iso = op.advance_cell(iso, 0.1, np.zeros(14), 1e20, substeps=2)
    assert_allclose(out_iso, iso, atol=1e-13)


def test_dense_expm_oracle_sdirk2_convergence_and_3d_fourier_flrw_parity() -> None:
    L = 4
    op = GeneralLieStokesOperator(L)
    # Build VI_{-1/9} geometry (Class B exceptional rank-2 stratum)
    alg = build_bianchi_algebra("VI_h", n1=0.05, n3=-0.20, a_twist=0.10 / 3.0)
    sig = pstf_rank2(np.array([[-0.03, 0.012, -0.008], [0.012, 0.015, 0.009], [-0.008, 0.009, 0.015]]))
    geom = LieGeometry(sig, alg.a, alg.n)
    k_vec = np.array([0.08, -0.05, 0.11])
    dN, dtau = 0.25, 2.4

    rng = np.random.default_rng(10202)
    y0 = rng.normal(size=op.dim) + 1j * rng.normal(size=op.dim)
    src = op.shear_source_vector(sig, amplitude=0.3) + op.dipole_source_vector([0.1, -0.2, 0.05], amplitude=0.2)

    M_tot = dN * op.base_operator(geom, k_eff=k_vec) + dtau * op.K_dense_matrix
    aug = np.zeros((op.dim + 1, op.dim + 1), dtype=np.complex128)
    aug[: op.dim, : op.dim] = M_tot.toarray()
    aug[: op.dim, -1] = src
    y_ref = (expm(aug) @ np.r_[y0, 1.0])[: op.dim]

    errs = []
    for nsub in (4, 8, 16, 32, 64):
        y_num = op.advance_cell(y0, dN, geom, dtau, source_increment=src, k_eff=k_vec, substeps=nsub)
        errs.append(float(np.linalg.norm(y_num - y_ref) / np.linalg.norm(y_ref)))
    assert errs[-1] < 1e-4
    # Second-order SDIRK(2,2) convergence rate ~4 when halving dt
    assert 3.7 < errs[0] / errs[1] < 4.3
    assert 3.85 < errs[2] / errs[3] < 4.15
    assert 3.9 < errs[3] / errs[4] < 4.1

    # Compare flat FLRW 3D Fourier mode against FourierStokesPropagator in angular space!
    # Use small-L bandlimited sky so both representations agree identically
    n_th = 14
    TH, PH, d, w = gl_sphere_grid(n_th)
    n_flat = d.reshape(-1, 3)
    u, v = _spherical_screen_basis(n_flat)
    k_flrw = np.array([0.12, -0.09, 0.15])
    dchi = 3.0
    # Evolve monopole + dipole + quadrupole initial sky with collision + 3D streaming
    y_flrw0 = np.zeros(op.dim, dtype=np.complex128)
    y_flrw0[op.idx["T"][(0, 0)]] = 0.5
    y_flrw0[op.idx["T"][(1, 1)]] = 0.2 - 0.1j
    y_flrw0[op.idx["E"][(2, -1)]] = -0.05 + 0.02j
    y_flrw0[op.idx["V"][(1, 0)]] = 0.07
    sky0 = vector_to_stokes_maps(y_flrw0, op.idx, L=L, n_gl_theta=n_th).reshape(-1, 4)

    fprop = FourierStokesPropagator(n_flat, w.ravel(), k_flrw, u, v)
    # Propagate short distance so L<=4 does not hit Nyquist truncation boundary
    y_lie_end = op.advance_cell(y_flrw0, dchi * 0.05, np.zeros(14), 0.3, k_eff=k_flrw, substeps=16)
    sky_f_end = fprop.advance(sky0, dchi * 0.05, 0.3, substeps=16)
    y_f_end = stokes_maps_to_vector(sky_f_end, op.idx, op.dim, L=L, n_gl_theta=n_th)
    # Modes ell<=2 match cleanly (higher ell feel tiny L=4 truncation boundary leakage)
    for ch, ells in (("T", (0, 1, 2)), ("E", (2,)), ("B", (2,)), ("V", (0, 1, 2))):
        for ell in ells:
            for m in range(-ell, ell + 1):
                assert_allclose(y_lie_end[op.idx[ch][(ell, m)]], y_f_end[op.idx[ch][(ell, m)]], atol=1e-7)


def test_handedness_parity_geodesic_oracle_and_so3_covariance() -> None:
    L = 6
    op = GeneralLieStokesOperator(L, n_gl_theta=16)
    st = _build_default_admissible_state_for_family("VII_h")
    sig = st.sigma_ab / st.H
    a = st.algebra.a / st.H
    n = st.algebra.n / st.H

    # Collisionless geodesic oracle comparison
    dN_ray = 1e-4
    _, _, n_hat, w = gl_sphere_grid(16)
    rays = integrate_polarized_geodesics(
        n_hat, family="VII_h", H0=1.0, sigma_ab=sig, a_vec=a, n_mat=n, n_efolds_star=-dN_ray, n_steps=32
    )
    n_emit = -rays.p_emit / np.linalg.norm(rays.p_emit, axis=-1, keepdims=True)
    A_T = pstf_rank2(np.array([[1.0, 0.3, -0.2], [0.3, -0.4, 0.5], [-0.2, 0.5, -0.6]]))
    T_in = np.einsum("...i,ij,...j->...", n_hat, A_T, n_hat)
    T_out = np.einsum("...i,ij,...j->...", n_emit, A_T, n_emit)
    sky0 = np.zeros((*n_hat.shape[:-1], 4))
    sky0[..., 0] = T_in
    sky_ray = np.zeros_like(sky0)
    sky_ray[..., 0] = T_out
    v0 = stokes_maps_to_vector(sky0, op.idx, op.dim, L=L, n_gl_theta=16)
    v_ray = stokes_maps_to_vector(sky_ray, op.idx, op.dim, L=L, n_gl_theta=16)
    v_lie = op.advance_cell(v0, dN_ray, LieGeometry(sig, a, n), 0.0, substeps=4)
    assert np.linalg.norm(v_lie - v_ray) / max(np.linalg.norm(v_ray - v0), 1e-30) < 1e-7

    # Handedness flip via spatial reflection P = diag(1, -1, 1): a -> P a, n -> -P n P^T, sig -> P sig P^T
    P = np.diag([1.0, -1.0, 1.0])
    sig_amp = sig / max(float(np.linalg.norm(sig)), 1e-30) * 1e-3
    a_curv = a * 20.0
    n_curv = n * 20.0
    y0 = np.zeros(op.dim, dtype=np.complex128)
    y_pos = op.advance_cell(
        y0, 1.0, LieGeometry(sig_amp, a_curv, n_curv), 0.8,
        source_increment=op.shear_source_vector(sig_amp, amplitude=1.0), substeps=16,
    )
    assert max_stokes_reality_error(y_pos, op.idx) < 1e-13
    sig_m = P @ sig_amp @ P.T
    y_neg = op.advance_cell(
        y0, 1.0, LieGeometry(sig_m, P @ a_curv, -P @ n_curv @ P.T), 0.8,
        source_increment=op.shear_source_vector(sig_m, amplitude=1.0), substeps=16,
    )
    a_pos = vector_to_alm_dict(y_pos, op.idx)
    a_neg = vector_to_alm_dict(y_neg, op.idx)
    cl_tb_p = [sum((a_pos["T"][(ell, m)] * np.conj(a_pos["B"][(ell, m)])).real for m in range(-ell, ell + 1)) for ell in range(2, L + 1)]
    cl_tb_m = [sum((a_neg["T"][(ell, m)] * np.conj(a_neg["B"][(ell, m)])).real for m in range(-ell, ell + 1)) for ell in range(2, L + 1)]
    cl_ee_p = [sum(abs(a_pos["E"][(ell, m)]) ** 2 for m in range(-ell, ell + 1)) for ell in range(2, L + 1)]
    cl_ee_m = [sum(abs(a_neg["E"][(ell, m)]) ** 2 for m in range(-ell, ell + 1)) for ell in range(2, L + 1)]
    assert max(abs(np.array(cl_tb_p) + np.array(cl_tb_m))) / max(np.max(np.abs(cl_tb_p)), 1e-30) < 1e-11
    assert max(abs(np.array(cl_ee_p) - np.array(cl_ee_m))) / max(np.max(np.abs(cl_ee_p)), 1e-30) < 1e-11

    # SO(3) rotational covariance of spectra across T, E, B
    R = Rotation.from_euler("zyx", [0.4, -0.7, 0.9]).as_matrix()
    sig_r = R @ sig_amp @ R.T
    y_rot = op.advance_cell(
        y0, 1.0, LieGeometry(sig_r, R @ a_curv, R @ n_curv @ R.T), 0.8,
        source_increment=op.shear_source_vector(sig_r, amplitude=1.0), substeps=16,
    )
    a_rot = vector_to_alm_dict(y_rot, op.idx)
    cl_tt_p = np.array([sum(abs(a_pos["T"][(ell, m)]) ** 2 for m in range(-ell, ell + 1)) for ell in range(2, L + 1)])
    cl_tt_r = np.array([sum(abs(a_rot["T"][(ell, m)]) ** 2 for m in range(-ell, ell + 1)) for ell in range(2, L + 1)])
    cl_ee_r = np.array([sum(abs(a_rot["E"][(ell, m)]) ** 2 for m in range(-ell, ell + 1)) for ell in range(2, L + 1)])
    assert np.max(np.abs(cl_tt_p - cl_tt_r)) / np.max(cl_tt_p) < 1e-11
    assert np.max(np.abs(np.array(cl_ee_p) - cl_ee_r)) / np.max(cl_ee_p) < 1e-11
