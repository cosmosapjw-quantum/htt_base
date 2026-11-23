"""Tests for R100 finite-redshift Bianchi position drift, T_C/T_G kernels, and coordinate oracle."""
from __future__ import annotations

import math
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from bass.transport.finite_redshift_optics import OpticalHistory
from bass.transport.position_drift_optics import (
    RATE_S_TO_UASYR,
    SEC_PER_MPC,
    aberrate_sky_and_derivatives,
    bianchi_i_coordinate_drift_oracle,
    finite_redshift_position_drift,
)
from scripts.r100 import optical_drift as r100_opt
from scripts.r98 import bianchi_history as r98


def _unit_dirs():
    v = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [0.5, -0.6, math.sqrt(1.0 - 0.25 - 0.36)],
        [-0.3, 0.7, -math.sqrt(1.0 - 0.09 - 0.49)],
    ])
    return v / np.linalg.norm(v, axis=1)[:, None]


def test_milne_type_v_exact_zero_drift():
    """Open isotropic FLRW in rotated Type V tetrad (C^k_ij != 0, sigma == 0) has zero position drift."""
    N = np.linspace(-1.1, 0.0, 240)
    t = np.exp(N)
    H = 1.0 / t
    sig = np.zeros((len(N), 3, 3))
    a_vec = np.outer(1.0 / t, np.array([0.15, 0.20, 0.0]))
    n_mat = np.zeros((len(N), 3, 3))
    hist = OpticalHistory(N, H, sig, a_vec, n_mat, h_reference_si=1.0 / RATE_S_TO_UASYR)
    res = finite_redshift_position_drift(hist, _unit_dirs(), [0.2, 0.8, 1.5], n_min=-1.05, sky_frame="observed")
    assert np.max(np.abs(res.drift_observed_3d_uasyr)) < 1e-11
    assert np.max(np.abs(res.local_kinematic_limit_3d_uasyr)) == 0.0
    assert res.max_longitudinal_invariant_error < 1e-13
    assert res.max_null_error < 1e-13


def test_flrw_parallax_and_secular_aberration():
    """Exact flat FLRW transverse velocity parallax and secular aberration glide dipole."""
    _, tr = r98.background("FLRW", samples=321)
    href = float(r98.optics()[0].H_of_z(r98.Z_INITIAL))
    be = np.array([0.002, -0.001, 0.0005])
    bo = np.array([0.001, -0.0005, 0.0002])
    accel = np.array([-2e-18, 1e-18, 0.5e-18])
    h = OpticalHistory(
        tr.N_grid, tr.H_grid, tr.sigma_ab_grid, tr.a_grid, tr.n_grid,
        h_reference_si=href, emitter_beta=np.broadcast_to(be, (len(tr.N_grid), 3)).copy(),
    )
    dirs = _unit_dirs()
    zs = np.array([0.05, 0.5, 1.5])
    res = finite_redshift_position_drift(
        h, dirs, zs, n_min=-math.log(3.2), sky_frame="observed",
        observer_beta=bo, observer_accel_s_inv=accel, rtol=2e-11, atol=2e-14,
    )
    # Check exact secular aberration additive decomposition vs zero-accel run:
    res0 = finite_redshift_position_drift(
        h, dirs, zs, n_min=-math.log(3.2), sky_frame="observed",
        observer_beta=bo, rtol=2e-11, atol=2e-14,
    )
    assert np.allclose(res.drift_observed_3d_uasyr - res0.drift_observed_3d_uasyr, res.secular_aberration_3d_uasyr[:, None, :], rtol=0, atol=1e-12)
    # Leading O(beta) FLRW parallax in zero-bo run check: d_n / dt_o = P_perp(be) * c / ((1+z) * D_A)
    res_be_only = finite_redshift_position_drift(
        h, dirs, zs, n_min=-math.log(3.2), sky_frame="observed",
        rtol=2e-11, atol=2e-14,
    )
    c_mpc_per_yr = 299792.458 * 1000.0 * 365.25 * 86400.0 / (3.085677581491367e22)
    rad_to_uas = (180.0 / math.pi) * 3600.0 * 1e6
    for i, nvec in enumerate(dirs):
        P = np.eye(3) - np.outer(nvec, nvec)
        for j, zv in enumerate(res_be_only.redshift[i]):
            gamma_e = 1.0 / math.sqrt(1.0 - float(be @ be))
            # Exact flat FLRW normal-observer rate wrt emitter beta: gamma_e * c / ((1+z_obs) * D_A_norm) * P_perp(beta_e)
            expected = gamma_e * c_mpc_per_yr * rad_to_uas / ((1.0 + zv) * res_be_only.angular_distance_mpc[i, j]) * (P @ be)
            assert np.allclose(res_be_only.drift_normal_3d_uasyr[i, j], expected, rtol=1e-7, atol=1e-11)


def test_oblique_bianchi_i_coordinate_oracle_parity():
    """22-state ODE agrees with independent 3D coordinate-ray two-time root oracle to <1e-7 rel."""
    q = np.array([0.28, 0.33, 0.39])
    m = q.mean()
    N = np.linspace(-0.8, 0.0, 400)
    t = np.exp(N / m)
    H = m / t
    sig = np.zeros((len(N), 3, 3))
    for i, tt in enumerate(t):
        sig[i] = np.diag((q - m) / tt)
    be = np.array([-0.0007, 0.0011, -0.0004])
    bo = np.array([0.0012, -0.0008, 0.0005])
    n_norm = np.array([0.5, -0.6, math.sqrt(1.0 - 0.25 - 0.36)])
    hist = OpticalHistory(
        N, H, sig, np.zeros((len(N), 3)), np.zeros((len(N), 3, 3)),
        h_reference_si=1.0 / RATE_S_TO_UASYR,
        emitter_beta=np.broadcast_to(be, (len(N), 3)).copy(),
    )
    ora = bianchi_i_coordinate_drift_oracle(lambda tau: tau ** q, n_norm, 0.65, 1.0, bo, be, dt_o=1e-4)
    beams = finite_redshift_position_drift(
        hist, n_norm[None, :], [ora["redshift"]], n_min=-0.75, sky_frame="normal",
        observer_beta=bo, rtol=2e-11, atol=2e-14,
    )
    rel = np.linalg.norm(ora["drift_obs_3d_dimless"] - beams.drift_observed_3d_uasyr[0, 0]) / np.linalg.norm(ora["drift_obs_3d_dimless"])
    assert rel < 1e-7
    assert beams.max_longitudinal_invariant_error < 1e-13
    assert abs(ora["dtau_e_dtau_o"] - ora["expected_time_dilation"]) < 1e-8


def test_vih_z_to_zero_limit_and_so3_equivariance():
    """Bianchi VI_h position drift converges smoothly to +P_perp(sigma n) as z->0 and is SO(3)-equivariant."""
    _, tr = r98.background("VI_h", samples=321)
    href = float(r98.optics()[0].H_of_z(r98.Z_INITIAL))
    h = OpticalHistory(tr.N_grid, tr.H_grid, tr.sigma_ab_grid, tr.a_grid, tr.n_grid, h_reference_si=href)
    dirs = _unit_dirs()
    b_small = finite_redshift_position_drift(h, dirs, [1e-4, 1e-3, 1.0], n_min=-math.log(3.2), sky_frame="observed")
    r_z1e4 = np.linalg.norm(b_small.finite_z_remainder_3d_uasyr[:, 0]) / np.linalg.norm(b_small.local_kinematic_limit_3d_uasyr)
    r_z1e3 = np.linalg.norm(b_small.finite_z_remainder_3d_uasyr[:, 1]) / np.linalg.norm(b_small.local_kinematic_limit_3d_uasyr)
    assert r_z1e4 < 2e-5
    assert r_z1e3 < 2e-4
    assert r_z1e4 < r_z1e3

    R = Rotation.from_rotvec([-0.3, 0.2, 0.5]).as_matrix()
    h_rot = OpticalHistory(
        tr.N_grid, tr.H_grid,
        np.einsum("ij,tjk,lk->til", R, tr.sigma_ab_grid, R),
        np.einsum("ij,tj->ti", R, tr.a_grid),
        np.einsum("ij,tjk,lk->til", R, tr.n_grid, R),
        h_reference_si=href,
    )
    b1 = finite_redshift_position_drift(h, dirs, [0.5], n_min=-math.log(3.2), sky_frame="observed")
    b2 = finite_redshift_position_drift(h_rot, dirs @ R.T, [0.5], n_min=-math.log(3.2), sky_frame="observed")
    assert np.allclose(np.einsum("ij,nzj->nzi", R, b1.drift_observed_3d_uasyr), b2.drift_observed_3d_uasyr, rtol=1e-9, atol=1e-11)


def test_aberration_jacobian_finite_difference_and_guards():
    """Analytic d(n_obs)/d(n_norm) and d(n_obs)/d(beta) match centered finite differences."""
    n0 = np.array([0.4, -0.7, math.sqrt(1.0 - 0.16 - 0.49)])
    beta = np.array([0.12, -0.05, 0.08])
    n_obs, Jn, Jb, d = aberrate_sky_and_derivatives(n0, beta)
    eps = 1e-6
    tangent = np.cross(n0, [1.0, 0.2, -0.3]); tangent /= np.linalg.norm(tangent)
    np_t = (n0 + eps * tangent); np_t /= np.linalg.norm(np_t)
    nm_t = (n0 - eps * tangent); nm_t /= np.linalg.norm(nm_t)
    dn_fd = (aberrate_sky_and_derivatives(np_t, beta)[0] - aberrate_sky_and_derivatives(nm_t, beta)[0]) / (2 * eps)
    assert np.allclose(dn_fd, Jn @ tangent, rtol=1e-8, atol=1e-10)
    for ax in range(3):
        eb = np.zeros(3); eb[ax] = eps
        db_fd = (aberrate_sky_and_derivatives(n0, beta + eb)[0] - aberrate_sky_and_derivatives(n0, beta - eb)[0]) / (2 * eps)
        assert np.allclose(db_fd, Jb[:, ax], rtol=1e-8, atol=1e-10)

    _, tr = r98.background("FLRW", samples=20)
    href = float(r98.optics()[0].H_of_z(r98.Z_INITIAL))
    h = OpticalHistory(tr.N_grid, tr.H_grid, tr.sigma_ab_grid, tr.a_grid, tr.n_grid, h_reference_si=href)
    with pytest.raises(ValueError, match="z=0 vertex"):
        finite_redshift_position_drift(h, _unit_dirs()[:1], [0.0], n_min=tr.N_grid[0])
    with pytest.raises(ValueError, match="subluminal"):
        finite_redshift_position_drift(h, _unit_dirs()[:1], [0.1], n_min=tr.N_grid[0], observer_beta=[0.8, 0.7, 0.0])
