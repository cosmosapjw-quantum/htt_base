"""Infinitesimal homogeneous Bianchi beams at measured redshift, signature (-+++).

Normal Fermi tetrad, dimensionless R49 rates H/H_*, sigma/H_*, A and n;
physical distances are Mpc. Observer/source velocities are normal-frame v/c.
The linearized angular and positional geodesics are R99 THEORY_OPTICAL (1)-(4).
"""
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.recombination.reionization import SEC_PER_MPC


def _knot_bounds(spline, lo, hi):
    """Componentwise uniform bounds on an intersected set of cubic segments."""
    take = (spline.x[:-1] < hi) & (spline.x[1:] > lo)
    width = np.diff(spline.x)[take, None]
    co = np.abs(spline.c[:, take, :])
    value = ((co[0] * width + co[1]) * width + co[2]) * width + co[3]
    derivative = (3 * co[0] * width + 2 * co[1]) * width + co[2]
    return value.max(axis=0), derivative.max(axis=0)


class OpticalHistory:
    """Increasing normal-volume e-folds and actual tabulated homogeneous geometry."""

    def __init__(self, N, H, sigma, a_vec, n_mat, *, h_reference_si, emitter_beta=None):
        N, H, sigma, a_vec, n_mat = map(
            lambda v: np.asarray(v, dtype=float), (N, H, sigma, a_vec, n_mat)
        )
        if N.ndim != 1 or len(N) < 4 or not np.all(np.diff(N) > 0):
            raise ValueError("need at least four strictly increasing e-fold samples")
        k = len(N)
        if (H.shape != (k,) or sigma.shape != (k, 3, 3) or
                a_vec.shape != (k, 3) or n_mat.shape != (k, 3, 3)):
            raise ValueError("invalid geometry history shapes")
        if not all(np.isfinite(v).all() for v in (N, H, sigma, a_vec, n_mat)):
            raise ValueError("geometry must be finite")
        if np.any(H <= 0) or not np.isfinite(h_reference_si) or h_reference_si <= 0:
            raise ValueError("expanding H and physical H_* must be positive")
        shear = sigma / H[:, None, None]
        if (not np.allclose(shear, shear.transpose(0, 2, 1), atol=1e-12, rtol=0)
                or np.max(np.abs(np.trace(shear, axis1=1, axis2=2))) > 1e-12
                or not np.allclose(n_mat, n_mat.transpose(0, 2, 1), atol=1e-14, rtol=1e-12)):
            raise ValueError("expected STF shear and symmetric n")
        beta = np.zeros((k, 3)) if emitter_beta is None else np.asarray(emitter_beta, dtype=float)
        if beta.shape != (k, 3) or not np.isfinite(beta).all() or np.any(np.linalg.norm(beta, axis=1) >= 1):
            raise ValueError("invalid emitter velocity history")
        # Separate log H from normalized geometry, preserving small anisotropic rates.
        ratios = np.c_[shear.reshape(k, 9), a_vec / H[:, None],
                       n_mat.reshape(k, 9) / H[:, None], beta]
        self.ratios = CubicSpline(N, ratios, axis=0, extrapolate=False)
        self.log_h = CubicSpline(N, np.log(H), extrapolate=False)
        self.h_reference_si = float(h_reference_si)
        self.domain = (float(N[0]), float(N[-1]))
        self.h_observer = float(H[-1])

    def monotone_margin(self, lo, normal_rays):
        """Lower bound on -d log(1+z)/dN for the requested rays on [lo,N_o]."""
        maximum, derivative = _knot_bounds(self.ratios, lo, self.domain[1])
        shear = np.linalg.norm(maximum[:9])
        structure = np.sqrt(2.) * np.linalg.norm(maximum[12:21]) + 2*np.sqrt(3.) * np.linalg.norm(maximum[9:12])
        speed = np.linalg.norm(maximum[21:])
        speed_derivative = np.linalg.norm(derivative[21:])
        if speed >= 1:
            return -np.inf
        # For null p: |p'| <= ||Sigma||_F + ||Gamma_sp/H||_F and
        # ||Gamma_sp/H||_F <= 3/2 ||C/H||_F. Differentiate gamma(1-beta.p).
        doppler_bound = (speed * speed_derivative / (1 - speed**2)
                         + (speed_derivative + speed * (shear + 1.5*structure)) / (1-speed))
        margin = 1 - shear - doppler_bound
        # Principal-axis rays in diagonal Bianchi I stay on axis, even when
        # another axis contracts (Kasner). Bound the actual eigenvalue there.
        diagonal = [0, 4, 8]
        off_diagonal = [1, 2, 3, 5, 6, 7]
        if (margin <= 0 and np.all(maximum[9:] == 0)
                and np.all(maximum[off_diagonal] == 0)
                and np.all(np.count_nonzero(normal_rays, axis=1) == 1)):
            active = np.argmax(np.abs(normal_rays), axis=1)
            take = (self.ratios.x[:-1] < self.domain[1]) & (self.ratios.x[1:] > lo)
            coeff = self.ratios.c[:, take, :][:, :, diagonal][:, :, active]
            width = np.diff(self.ratios.x)[take, None]
            remainder = ((abs(coeff[0])*width + abs(coeff[1]))*width + abs(coeff[2]))*width
            margin = np.min(1 + coeff[3] - remainder)
        return float(margin)


@dataclass(frozen=True)
class DistanceBeams:
    """Event arrays have shape (number of rays, number of targets); distances in Mpc."""
    normal_sky: np.ndarray
    redshift: np.ndarray
    emission_N: np.ndarray
    energy_ratio: np.ndarray
    observer_doppler: np.ndarray
    emitter_doppler: np.ndarray
    signed_area_mpc2: np.ndarray
    angular_distance_mpc: np.ndarray
    luminosity_distance_mpc: np.ndarray
    parity: np.ndarray
    max_null_error: float
    max_direction_tangency: float
    max_normalized_connector_tangency: float
    monotone_redshift_margin: float


def finite_redshift_beams(history, directions, redshifts, *, n_min, sky_frame,
                          observer_beta=(0., 0., 0.), rtol=2e-10, atol=2e-13, max_step=.04):
    """Trace a common bundle from the observer to each unique observed-z root.

    'normal' and 'observed' describe input sky directions. Internally every
    variation starts in normal unit angular coordinates. Observer aberration is
    applied once to area. Signed area is oriented in observed angular units.
    The restricted branch requires a certified decreasing z(N). Parity is local
    at each emission event and does not count earlier conjugate points.
    """
    sky = np.asarray(directions, dtype=float)
    z = np.asarray(redshifts, dtype=float)
    beta = np.asarray(observer_beta, dtype=float)
    if (sky.ndim != 2 or sky.shape[1] != 3 or not len(sky) or not np.isfinite(sky).all()
            or not np.allclose(np.linalg.norm(sky, axis=1), 1., rtol=0, atol=1e-12)):
        raise ValueError("expected finite unit sky directions with shape (rays,3)")
    if z.ndim != 1 or not len(z) or not np.isfinite(z).all() or np.any(z <= -1):
        raise ValueError("invalid target redshifts")
    if beta.shape != (3,) or not np.isfinite(beta).all() or beta @ beta >= 1:
        raise ValueError("observer velocity must be subluminal")
    if sky_frame not in ("observed", "normal"):
        raise ValueError("sky_frame must be observed or normal")
    if not (np.isfinite([n_min, rtol, atol, max_step]).all() and
            history.domain[0] <= n_min < history.domain[1] and min(rtol, atol, max_step) > 0):
        raise ValueError("invalid e-fold domain or integration controls")
    p0 = -sky
    gamma = 1 / np.sqrt(1 - beta @ beta)
    if sky_frame == "observed":
        mu = p0 @ beta
        p0 = (p0 + (gamma + gamma**2/(gamma+1)*mu)[:, None]*beta) / (gamma*(1+mu))[:, None]
    margin = history.monotone_margin(n_min, p0)
    if not margin > 0:
        raise ValueError("uncertified redshift branch; restrict the input interval or velocity history")
    D_o = gamma * (1 - p0 @ beta)
    normal_sky = -p0
    seed = np.eye(3)[np.argmin(np.abs(normal_sky), axis=1)]
    s1 = np.cross(seed, normal_sky)
    s1 /= np.linalg.norm(s1, axis=1)[:, None]
    s2 = np.cross(normal_sky, s1)
    nr = len(sky)
    y0 = np.zeros((nr, 16))
    y0[:, 1:4], y0[:, 4:7], y0[:, 7:10] = p0, -s1, -s2
    start = history.domain[1]

    def rhs(N, state):
        y = state.reshape(nr, 16)
        geom = history.ratios(N)
        shear, A, n = geom[:9].reshape(3, 3), geom[9:12], geom[12:21].reshape(3, 3)
        C = build_structure_tensor_with_sign(A, n, a_sign=1)
        G = build_4d_bianchi_connection(1., shear, C)
        p = y[:, 1:4]
        Q = y[:, 4:10].reshape(nr, 2, 3)
        X = y[:, 10:].reshape(nr, 2, 3)
        u = np.c_[np.ones(nr), p]
        B = np.einsum("dba,rb,ra->rd", G, u, u)
        dB = (np.einsum("dja,rsj,ra->rsd", G[:, 1:, :], Q, u)
              + np.einsum("dbj,rb,rsj->rsd", G[:, :, 1:], u, Q))
        out = np.empty_like(y)
        out[:, 0] = -B[:, 0]
        out[:, 1:4] = -B[:, 1:] + p*B[:, :1]
        dQ = -dB[:, :, 1:] + Q*B[:, 0, None, None] + p[:, None, :]*dB[:, :, :1]
        # X is rescaled once by H_o, for O(1) conditioning at late R98 times.
        dX = ((history.h_observer / np.exp(history.log_h(N))) * Q
              + X @ (np.eye(3) + shear).T - np.einsum("kij,ri,rsj->rsk", C, p, X))
        out[:, 4:10], out[:, 10:] = dQ.reshape(nr, 6), dX.reshape(nr, 6)
        return out.ravel()

    solution = solve_ivp(rhs, (start, n_min), y0.ravel(), method="DOP853", dense_output=True,
                         rtol=rtol, atol=atol, max_step=max_step)
    if not solution.success:
        raise RuntimeError(solution.message)

    def log_redshift(N, ray):
        row = solution.sol(N).reshape(nr, 16)[ray]
        v = history.ratios(N)[21:]
        D_e = (1 - v @ row[1:4]) / np.sqrt(1 - v @ v)
        return row[0] + np.log(D_e / D_o[ray])

    shape = (nr, len(z))
    ne, energy, emission_doppler, actual_z, signed = (np.empty(shape) for _ in range(5))
    null, tangent, connector = 0., 0., 0.
    length_unit = 1 / (history.h_reference_si * history.h_observer * SEC_PER_MPC)
    for r in range(nr):
        at_o, at_lo = log_redshift(start, r), log_redshift(n_min, r)
        for j, target in enumerate(np.log1p(z)):
            if not at_o <= target <= at_lo:
                raise ValueError(f"redshift {z[j]} outside sampled history on ray {r}")
            # Physical endpoints are exact branches. An absolute e-fold
            # tolerance near the vertex can otherwise erase a small nonzero ray.
            if target == at_o:
                N = start
            else:
                N = brentq(lambda n: log_redshift(n, r)-target, n_min, start,
                           xtol=np.nextafter(0., 1.))
                error = abs(log_redshift(N, r) - target)
                scale = abs(target - at_o)
                roundoff = 16*np.finfo(float).eps*max(abs(target), abs(at_o))
                if N == start or error > max(5e-10*scale, roundoff):
                    raise ValueError(f"unresolvable redshift event on ray {r}, redshift {z[j]}")
            y = solution.sol(N).reshape(nr, 16)[r]
            p, Q, X = y[1:4], y[4:10].reshape(2, 3), y[10:].reshape(2, 3)
            area = -np.dot(p, np.cross(X[0], X[1]))
            norms = np.linalg.norm(X, axis=1)
            if N != start and abs(area) <= max(32*np.finfo(float).eps, 4*rtol)*max(np.prod(norms), (N-start)**2):
                raise ValueError(f"unresolved singular beam at ray {r}, redshift {z[j]}")
            ne[r, j], energy[r, j] = N, np.exp(y[0])
            v = history.ratios(N)[21:]
            emission_doppler[r, j] = (1-v @ p) / np.sqrt(1-v @ v)
            actual_z[r, j] = np.expm1(log_redshift(N, r))
            signed[r, j] = area * (length_unit * D_o[r])**2
            null = max(null, abs(p @ p - 1))
            tangent = max(tangent, np.max(abs(Q @ p)))
            connector = max(connector, np.max(abs(X @ p) / np.maximum(norms, 1e-300)))
    DA = np.sqrt(abs(signed))
    return DistanceBeams(normal_sky, actual_z, ne, energy, D_o, emission_doppler, signed, DA,
                         (1+actual_z)**2 * DA, np.sign(signed).astype(int), float(null),
                         float(tangent), float(connector), margin)
