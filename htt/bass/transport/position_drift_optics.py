"""Finite-redshift Bianchi position drift (cosmic parallax / proper motion) and T_C, T_G kernels.

Extends R99 `finite_redshift_optics` without altering any frozen R99 file hashes.
Implements the exact two-observer-time 22-state geodesic bundle variation
dF/dtau_o|_{tau, alpha} = (0, xi) and dq/dtau_o along R49 homogeneous Bianchi
histories `(H, sigma, A, n, beta_e)`, plus observer velocity beta_o and
acceleration beta_dot_o, projected into both tangent sphere drift and ICRS (pmra*, pmdec).
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq, root

from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.recombination.reionization import SEC_PER_MPC
from bass.transport.finite_redshift_optics import OpticalHistory

JULIAN_YEAR_S = 365.25 * 86400.0
RAD_TO_UAS = (180.0 / math.pi) * 3600.0 * 1.0e6
RATE_S_TO_UASYR = JULIAN_YEAR_S * RAD_TO_UAS
C_LIGHT_KMS = 299792.458


def screen_basis_for_directions(sky: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return local spherical (e_ra, e_dec) tangent unit basis for outward sky unit vectors."""
    n = np.asarray(sky, dtype=float)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    x, y, z = n[..., 0], n[..., 1], n[..., 2]
    xy = np.hypot(x, y)
    pole = xy < 1.0e-12
    safe_xy = np.where(pole, 1.0, xy)
    e_ra = np.where(
        pole[..., None],
        np.broadcast_to(np.array([0.0, 1.0, 0.0]), n.shape),
        np.stack([-y / safe_xy, x / safe_xy, np.zeros_like(z)], axis=-1),
    )
    e_dec = np.cross(n, e_ra)
    e_dec /= np.linalg.norm(e_dec, axis=-1, keepdims=True)
    return e_ra, e_dec


def aberrate_sky_and_derivatives(
    n_norm: np.ndarray, beta: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Lorentz aberration n_obs = A(n_norm, beta) with exact d(n_obs)/d(n_norm) and d(n_obs)/d(beta)."""
    nn = np.asarray(n_norm, dtype=float)
    nn = nn / float(np.linalg.norm(nn))
    b = np.asarray(beta, dtype=float)
    b2 = float(b @ b)
    if b2 >= 1.0:
        raise ValueError("observer beta must be subluminal")
    if b2 == 0.0:
        P_n = np.eye(3) - np.outer(nn, nn)
        return nn.copy(), P_n, P_n, 1.0

    g = 1.0 / math.sqrt(1.0 - b2)
    bn = float(b @ nn)
    d = g * (1.0 + bn)
    c_par = g + (g * g / (g + 1.0)) * bn
    N_vec = nn + c_par * b
    n_obs = N_vec / d
    n_obs /= float(np.linalg.norm(n_obs))

    # d(n_obs)/d(n_norm) restricted to tangent vectors (or any vector):
    J_n = (
        np.eye(3)
        + (g * g / (g + 1.0)) * np.outer(b, b)
        - g * np.outer(n_obs, b)
    ) / d

    # Exact derivative d(n_obs)/d(beta) via chain rule
    dg = (g ** 3) * b
    dd = (1.0 + bn) * dg + g * nn
    dc = (
        dg
        + ((2.0 * g * (g + 1.0) - g * g) / ((g + 1.0) ** 2)) * bn * dg
        + (g * g / (g + 1.0)) * nn
    )
    dN = c_par * np.eye(3) + np.outer(b, dc)
    J_beta = (dN - np.outer(n_obs, dd)) / d
    # Project rows orthogonal to n_obs for numerical tightness
    P_obs = np.eye(3) - np.outer(n_obs, n_obs)
    return n_obs, P_obs @ J_n, P_obs @ J_beta, float(d)


@dataclass(frozen=True)
class PositionDriftBeams:
    """Finite-redshift position drift (cosmic parallax / proper motion) on homogeneous Bianchi histories."""

    normal_sky: np.ndarray
    observed_sky: np.ndarray
    redshift: np.ndarray
    emission_N: np.ndarray
    energy_ratio: np.ndarray
    observer_doppler: np.ndarray
    emitter_doppler: np.ndarray
    angular_distance_mpc: np.ndarray
    luminosity_distance_mpc: np.ndarray
    parity: np.ndarray
    jacobi_matrix_mpc: np.ndarray
    drift_normal_3d_uasyr: np.ndarray
    drift_observed_3d_uasyr: np.ndarray
    pm_observed_uasyr: np.ndarray
    pm_normal_uasyr: np.ndarray
    local_kinematic_limit_3d_uasyr: np.ndarray
    finite_z_remainder_3d_uasyr: np.ndarray
    secular_aberration_3d_uasyr: np.ndarray
    max_null_error: float
    max_longitudinal_invariant_error: float
    max_direction_tangency: float
    max_normalized_connector_tangency: float
    monotone_redshift_margin: float


def finite_redshift_position_drift(
    history: OpticalHistory,
    directions: np.ndarray,
    redshifts: np.ndarray,
    *,
    n_min: float,
    sky_frame: str = "observed",
    observer_beta: tuple[float, float, float] | np.ndarray = (0.0, 0.0, 0.0),
    observer_accel_s_inv: tuple[float, float, float] | np.ndarray = (0.0, 0.0, 0.0),
    rtol: float = 2.0e-10,
    atol: float = 2.0e-13,
    max_step: float = 0.04,
) -> PositionDriftBeams:
    """Compute exact finite-z position drift dn^A/dtau_o alongside Jacobi D_A and D_L.

    Uses the exact 22-state per-ray linear variation (ln E, p, Q1, Q2, X1, X2, q_drift, xi_drift)
    with normal-time slicing xi^0 == 0 and conserved null inner product E (p . xi) == -D_o.
    `observer_accel_s_inv` is d(beta_o)/d(tau_phys) in s^-1 in the observer's Fermi frame.
    """
    sky = np.asarray(directions, dtype=float)
    z = np.asarray(redshifts, dtype=float)
    beta = np.asarray(observer_beta, dtype=float)
    accel = np.asarray(observer_accel_s_inv, dtype=float)
    if (
        sky.ndim != 2
        or sky.shape[1] != 3
        or not len(sky)
        or not np.isfinite(sky).all()
        or not np.allclose(np.linalg.norm(sky, axis=1), 1.0, rtol=0, atol=1e-12)
    ):
        raise ValueError("expected finite unit sky directions with shape (rays, 3)")
    if z.ndim != 1 or not len(z) or not np.isfinite(z).all() or np.any(z <= -1.0):
        raise ValueError("invalid target redshifts")
    if beta.shape != (3,) or not np.isfinite(beta).all() or float(beta @ beta) >= 1.0:
        raise ValueError("observer velocity must be subluminal")
    if accel.shape != (3,) or not np.isfinite(accel).all():
        raise ValueError("observer acceleration must be finite 3-vector")
    if sky_frame not in ("observed", "normal"):
        raise ValueError("sky_frame must be observed or normal")
    if not (
        np.isfinite([n_min, rtol, atol, max_step]).all()
        and history.domain[0] <= n_min < history.domain[1]
        and min(rtol, atol, max_step) > 0
    ):
        raise ValueError("invalid e-fold domain or integration controls")

    p0 = -sky.copy()
    gamma_o = 1.0 / math.sqrt(1.0 - float(beta @ beta))
    if sky_frame == "observed":
        mu = p0 @ beta
        p0 = (p0 + (gamma_o + (gamma_o ** 2) / (gamma_o + 1.0) * mu)[:, None] * beta) / (
            gamma_o * (1.0 + mu)
        )[:, None]
        p0 /= np.linalg.norm(p0, axis=1)[:, None]

    margin = history.monotone_margin(n_min, p0)
    if not margin > 0:
        raise ValueError("uncertified redshift branch; restrict the input interval or velocity history")

    D_o = gamma_o * (1.0 - p0 @ beta)
    normal_sky = -p0
    nr = len(sky)

    seed = np.eye(3)[np.argmin(np.abs(normal_sky), axis=1)]
    s1 = np.cross(seed, normal_sky)
    s1 /= np.linalg.norm(s1, axis=1)[:, None]
    s2 = np.cross(normal_sky, s1)

    start = history.domain[1]
    geom0 = history.ratios(start)
    shear0 = geom0[:9].reshape(3, 3)
    C0 = build_structure_tensor_with_sign(geom0[9:12], geom0[12:21].reshape(3, 3), a_sign=1)
    G0 = build_4d_bianchi_connection(1.0, shear0, C0)
    u0 = np.c_[np.ones(nr), p0]
    B0 = np.einsum("dba,rb,ra->rd", G0, u0, u0)

    # 22 states per ray:
    # 0: ln E, 1:4 p, 4:10 Q, 10:16 X (H_o-rescaled), 16:19 q_drift/H_o, 19:22 xi_drift (dimensionless)
    y0 = np.zeros((nr, 22), dtype=float)
    y0[:, 1:4] = p0
    y0[:, 4:7] = -s1
    y0[:, 7:10] = -s2
    y0[:, 16:19] = gamma_o * (B0[:, 1:] - p0 * B0[:, :1])
    y0[:, 19:22] = gamma_o * (beta[None, :] - p0)

    def rhs(N, state):
        y = state.reshape(nr, 22)
        geom = history.ratios(N)
        shear, A, n = geom[:9].reshape(3, 3), geom[9:12], geom[12:21].reshape(3, 3)
        C = build_structure_tensor_with_sign(A, n, a_sign=1)
        G = build_4d_bianchi_connection(1.0, shear, C)
        p = y[:, 1:4]
        Q = y[:, 4:10].reshape(nr, 2, 3)
        X = y[:, 10:16].reshape(nr, 2, 3)
        qd = y[:, 16:19]
        xi = y[:, 19:22]
        u = np.c_[np.ones(nr), p]
        B = np.einsum("dba,rb,ra->rd", G, u, u)
        dB = (
            np.einsum("dja,rsj,ra->rsd", G[:, 1:, :], Q, u)
            + np.einsum("dbj,rb,rsj->rsd", G[:, :, 1:], u, Q)
        )
        dB_qd = (
            np.einsum("dja,rj,ra->rd", G[:, 1:, :], qd, u)
            + np.einsum("dbj,rb,rj->rd", G[:, :, 1:], u, qd)
        )
        h_ratio = history.h_observer / math.exp(float(history.log_h(N)))
        K_T = (np.eye(3) + shear).T

        out = np.empty_like(y)
        out[:, 0] = -B[:, 0]
        out[:, 1:4] = -B[:, 1:] + p * B[:, :1]
        dQ = -dB[:, :, 1:] + Q * B[:, 0, None, None] + p[:, None, :] * dB[:, :, :1]
        dX = h_ratio * Q + X @ K_T - np.einsum("kij,ri,rsj->rsk", C, p, X)
        out[:, 4:10] = dQ.reshape(nr, 6)
        out[:, 10:16] = dX.reshape(nr, 6)
        out[:, 16:19] = -dB_qd[:, 1:] + qd * B[:, 0, None] + p * dB_qd[:, :1]
        out[:, 19:22] = h_ratio * qd + xi @ K_T - np.einsum("kij,ri,rj->rk", C, p, xi)
        return out.ravel()

    solution = solve_ivp(
        rhs, (start, n_min), y0.ravel(), method="DOP853", dense_output=True,
        rtol=rtol, atol=atol, max_step=max_step
    )
    if not solution.success:
        raise RuntimeError(solution.message)

    def log_redshift(N, ray):
        row = solution.sol(N).reshape(nr, 22)[ray]
        v = history.ratios(N)[21:]
        D_e = (1.0 - v @ row[1:4]) / math.sqrt(1.0 - float(v @ v))
        return row[0] + math.log(D_e / D_o[ray])

    nt = len(z)
    ne = np.empty((nr, nt))
    energy = np.empty((nr, nt))
    em_dopp = np.empty((nr, nt))
    actual_z = np.empty((nr, nt))
    signed_area = np.empty((nr, nt))
    jacobi_mat = np.empty((nr, nt, 2, 2))
    drift_norm_3d = np.empty((nr, nt, 3))
    drift_obs_3d = np.empty((nr, nt, 3))
    obs_sky = np.empty((nr, 3))
    sec_aberr_3d = np.empty((nr, 3))
    local_3d = np.empty((nr, 3))

    length_unit = 1.0 / (history.h_reference_si * history.h_observer * SEC_PER_MPC)
    phys_rate_to_uasyr = history.h_reference_si * history.h_observer * RATE_S_TO_UASYR
    accel_dimless = accel / (history.h_reference_si * history.h_observer)

    e_ra_norm, e_dec_norm = screen_basis_for_directions(normal_sky)
    for r in range(nr):
        n_o, J_n, J_b, d_check = aberrate_sky_and_derivatives(normal_sky[r], beta)
        obs_sky[r] = n_o
        sec_aberr_3d[r] = J_b @ accel_dimless * phys_rate_to_uasyr
        # Exact z -> 0 leading local shear + secular aberration limit (observer velocity fixed or accel separately)
        P_loc = np.eye(3) - np.outer(normal_sky[r], normal_sky[r])
        local_norm = P_loc @ (shear0 @ normal_sky[r])
        local_3d[r] = (J_n @ local_norm + J_b @ accel_dimless) * phys_rate_to_uasyr

    pm_norm = np.empty((nr, nt, 2))
    pm_obs = np.empty((nr, nt, 2))
    e_ra_obs, e_dec_obs = screen_basis_for_directions(obs_sky)

    null_err, long_err, tangent_err, conn_err = 0.0, 0.0, 0.0, 0.0
    for r in range(nr):
        at_o, at_lo = log_redshift(start, r), log_redshift(n_min, r)
        n_o, J_n, _, _ = aberrate_sky_and_derivatives(normal_sky[r], beta)
        for j, target in enumerate(np.log1p(z)):
            if not at_o <= target <= at_lo:
                raise ValueError(f"redshift {z[j]} outside sampled history on ray {r}")
            if target == at_o:
                N = start
                raise ValueError("position drift undefined at exact z=0 vertex (parallax 1/D_A pole)")
            N = brentq(
                lambda nn: log_redshift(nn, r) - target,
                n_min,
                start,
                xtol=np.nextafter(0.0, 1.0),
            )
            error = abs(log_redshift(N, r) - target)
            scale = abs(target - at_o)
            roundoff = 16.0 * np.finfo(float).eps * max(abs(target), abs(at_o))
            if N == start or error > max(5e-10 * scale, roundoff):
                raise ValueError(f"unresolvable redshift event on ray {r}, redshift {z[j]}")

            y = solution.sol(N).reshape(nr, 22)[r]
            p, Q, X = y[1:4], y[4:10].reshape(2, 3), y[10:16].reshape(2, 3)
            xi = y[19:22]
            area = -float(np.dot(p, np.cross(X[0], X[1])))
            norms = np.linalg.norm(X, axis=1)
            if abs(area) <= max(32.0 * np.finfo(float).eps, 4.0 * rtol) * max(np.prod(norms), (N - start) ** 2):
                raise ValueError(f"unresolved singular beam at ray {r}, redshift {z[j]}")

            E_n = math.exp(y[0])
            v_e = history.ratios(N)[21:]
            gamma_e = 1.0 / math.sqrt(1.0 - float(v_e @ v_e))
            D_e = gamma_e * (1.0 - float(v_e @ p))
            z_act = math.expm1(y[0] + math.log(D_e / D_o[r]))

            # Screen basis at emitter orthogonal to p_e (orientation aligned with transported frame doesn't affect screen solve)
            sd_e = np.eye(3)[int(np.argmin(np.abs(p)))]
            b1 = np.cross(sd_e, p)
            b1 /= float(np.linalg.norm(b1))
            b2 = np.cross(p, b1)
            B_screen = np.stack([b1, b2])  # (2, 3)
            J_screen = B_screen @ X.T  # (2, 2), X is rescaled by H_o
            rhs_screen = B_screen @ ((gamma_e / (1.0 + z_act)) * v_e - xi)
            # (b_B . X_ode_A) (d alpha^A / d tau_phys) = H_o * H_* * rhs_screen
            dalpha_scaled = np.linalg.solve(J_screen, rhs_screen)

            d_norm_vec = (s1[r] * dalpha_scaled[0] + s2[r] * dalpha_scaled[1]) * phys_rate_to_uasyr
            d_obs_vec = (J_n @ d_norm_vec) + sec_aberr_3d[r]

            ne[r, j] = N
            energy[r, j] = E_n
            em_dopp[r, j] = D_e
            actual_z[r, j] = z_act
            signed_area[r, j] = area * (length_unit * D_o[r]) ** 2
            jacobi_mat[r, j] = J_screen * length_unit * D_o[r]
            drift_norm_3d[r, j] = d_norm_vec
            drift_obs_3d[r, j] = d_obs_vec
            pm_norm[r, j] = [float(e_ra_norm[r] @ d_norm_vec), float(e_dec_norm[r] @ d_norm_vec)]
            pm_obs[r, j] = [float(e_ra_obs[r] @ d_obs_vec), float(e_dec_obs[r] @ d_obs_vec)]

            null_err = max(null_err, abs(float(p @ p) - 1.0))
            long_err = max(long_err, abs(E_n * float(p @ xi) + D_o[r]))
            tangent_err = max(tangent_err, float(np.max(np.abs(Q @ p))))
            conn_err = max(conn_err, float(np.max(np.abs(X @ p) / np.maximum(norms, 1e-300))))

    DA = np.sqrt(np.abs(signed_area))
    DL = ((1.0 + actual_z) ** 2) * DA
    local_bcast = local_3d[:, None, :]
    remainder_3d = drift_obs_3d - local_bcast

    return PositionDriftBeams(
        normal_sky=normal_sky,
        observed_sky=obs_sky,
        redshift=actual_z,
        emission_N=ne,
        energy_ratio=energy,
        observer_doppler=D_o,
        emitter_doppler=em_dopp,
        angular_distance_mpc=DA,
        luminosity_distance_mpc=DL,
        parity=np.sign(signed_area).astype(int),
        jacobi_matrix_mpc=jacobi_mat,
        drift_normal_3d_uasyr=drift_norm_3d,
        drift_observed_3d_uasyr=drift_obs_3d,
        pm_observed_uasyr=pm_obs,
        pm_normal_uasyr=pm_norm,
        local_kinematic_limit_3d_uasyr=local_3d,
        finite_z_remainder_3d_uasyr=remainder_3d,
        secular_aberration_3d_uasyr=sec_aberr_3d,
        max_null_error=float(null_err),
        max_longitudinal_invariant_error=float(long_err),
        max_direction_tangency=float(tangent_err),
        max_normalized_connector_tangency=float(conn_err),
        monotone_redshift_margin=float(margin),
    )


def bianchi_i_coordinate_drift_oracle(
    scale_factors_fn,
    n_norm: np.ndarray,
    te0: float,
    t0: float = 1.0,
    observer_beta: np.ndarray = np.zeros(3),
    emitter_beta: np.ndarray = np.zeros(3),
    dt_o: float = 1.0e-4,
) -> dict[str, object]:
    """Independent exact Bianchi I 3D coordinate-ray two-time root oracle (in tau_* units with t0=1)."""
    nn = np.asarray(n_norm, dtype=float)
    nn /= np.linalg.norm(nn)
    bo = np.asarray(observer_beta, dtype=float)
    be = np.asarray(emitter_beta, dtype=float)

    def ray_disp(te, ts, p_dir):
        P = p_dir * scale_factors_fn(ts)
        pos = np.empty(3)
        for i in range(3):
            val, _ = quad(
                lambda t: P[i] / ((scale_factors_fn(t)[i] ** 2) * np.sqrt(np.sum((P / scale_factors_fn(t)) ** 2))),
                te, ts, epsabs=1e-13, epsrel=1e-13,
            )
            pos[i] = -val
        Ee = math.sqrt(float(np.sum((P / scale_factors_fn(ts)) ** 2)))  # Wait: E(te)/E(ts)
        Ee_ratio = math.sqrt(float(np.sum((P / scale_factors_fn(te)) ** 2))) / Ee
        pe = (P / scale_factors_fn(te)) / math.sqrt(float(np.sum((P / scale_factors_fn(te)) ** 2)))
        return pos, Ee_ratio, pe

    p0 = -nn
    x_e0, Ee0, pe0 = ray_disp(te0, t0, p0)
    gamma_o = 1.0 / math.sqrt(1.0 - float(bo @ bo))
    gamma_e = 1.0 / math.sqrt(1.0 - float(be @ be))
    Do = gamma_o * (1.0 - float(p0 @ bo))
    De = gamma_e * (1.0 - float(pe0 @ be))
    z_exact = Ee0 * De / Do - 1.0

    seed = np.eye(3)[int(np.argmin(np.abs(nn)))]
    s1 = np.cross(seed, nn); s1 /= np.linalg.norm(s1)
    s2 = np.cross(nn, s1)

    def solve_at(ts):
        xo = np.array(
            [quad(lambda tau: bo[i] / scale_factors_fn(tau)[i], t0, ts, epsabs=1e-14, epsrel=1e-13)[0] for i in range(3)]
        )
        def res(v):
            a1, a2, te = v
            nd = nn + a1 * s1 + a2 * s2
            nd /= np.linalg.norm(nd)
            disp, _, _ = ray_disp(te, ts, -nd)
            xe = x_e0 + np.array(
                [quad(lambda tau: be[i] / scale_factors_fn(tau)[i], te0, te, epsabs=1e-14, epsrel=1e-13)[0] for i in range(3)]
            )
            return (xo + disp) - xe
        rsol = root(res, [0.0, 0.0, te0 + (ts - t0) / (1.0 + z_exact)], tol=1e-12)
        if not rsol.success:
            raise RuntimeError(f"coordinate oracle failed: {rsol.message}")
        return rsol.x

    ap = solve_at(t0 + dt_o)
    am = solve_at(t0 - dt_o)
    dalpha_dtau_norm = gamma_o * (ap[:2] - am[:2]) / (2.0 * dt_o)
    d_norm_3d = s1 * dalpha_dtau_norm[0] + s2 * dalpha_dtau_norm[1]
    _, J_n, _, _ = aberrate_sky_and_derivatives(nn, bo)
    return {
        "redshift": float(z_exact),
        "dalpha_dtau_norm": dalpha_dtau_norm,
        "drift_norm_3d_dimless": d_norm_3d,
        "drift_obs_3d_dimless": J_n @ d_norm_3d,
        "dtau_e_dtau_o": float((gamma_o / gamma_e) * (ap[2] - am[2]) / (2.0 * dt_o)),
        "expected_time_dilation": float(1.0 / (1.0 + z_exact)),
    }
