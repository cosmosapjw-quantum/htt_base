"""Cold-electron Thomson collision and its finite-optical-depth solution.

Directions and coherencies are in a single electron rest frame. Stokes samples
are ordered I,Q,U,V in an oriented screen (u,v,n), with J_uv=(U-iV)/2.
The input weights are solid angles and must integrate polynomials of degree
four exactly on the unit sphere. The solver uses nine real integrated moments
and never constructs the pairwise angular scattering matrix.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import lu_factor, lu_solve

from bass.collision.electron_frame import _coerce_unit_directions, _validate_screen_basis


def _check_quadrature(directions: np.ndarray, weights: np.ndarray) -> None:
    """Check the sphere moments needed by the continuum spectral projectors."""
    if weights.shape != (len(directions),) or not np.all(np.isfinite(weights)):
        raise ValueError("solid-angle weights must be finite and match the directions")
    if np.any(weights < 0) or not np.isclose(weights.sum(), 4*np.pi, rtol=0, atol=2e-12):
        raise ValueError("solid-angle weights must be nonnegative and sum to 4*pi")
    left, right = np.triu_indices(3)
    pairs = directions[:, left] * directions[:, right]
    weighted = pairs * (weights / (4*np.pi))[:, None]
    eye = np.eye(3)
    fourth = (eye[left, right][:, None] * eye[left, right][None, :]
              + eye[left[:, None], left] * eye[right[:, None], right]
              + eye[left[:, None], right] * eye[right[:, None], left]) / 15.0
    # Contracting two indices in degree four/three also checks degree two/one.
    if (np.max(np.abs(pairs.T @ weighted - fourth)) > 2e-12
            or np.max(np.abs(directions.T @ weighted)) > 2e-12):
        raise ValueError("Thomson spectral evolution requires degree-four sphere quadrature")


def _response(optical_depth: float, gain: float) -> float:
    # (exp(-(1-b)t)-exp(-t))/b, including the conservative b=1 sector.
    return np.exp(-(1-gain)*optical_depth) * (-np.expm1(-gain*optical_depth)) / gain


def _mean_attenuation(t):
    """Integral from 0 to 1 of exp(-t*u)."""
    return -np.expm1(-t)/t if t else 1.


def _source_response(t, gain):
    """Average _response(t*u,gain), retaining the single-rescattering term at t=0."""
    if t < 1e-3:
        # Integral of exp(-t*u) * (exp(gain*t*u)-1) / gain.
        return t*(0.5 + t*((gain-2)/6 + t*((gain*gain-3*gain+3)/24
                    + t*(gain**3-4*gain*gain+6*gain-4)/120)))
    return (_mean_attenuation((1-gain)*t) - _mean_attenuation(t))/gain


def symmetric_screen_columns(u, v):
    """Stokes I,Q,U response to an orthonormal basis of real symmetric tensors."""
    # A symmetric 3x3 tensor has six independent real components. The
    # sqrt(2) factors make the Euclidean inner product equal the trace product.
    a = np.array([0, 1, 2, 0, 0, 1])
    b = np.array([0, 1, 2, 1, 2, 2])
    scale = np.where(a == b, 1., np.sqrt(2.))
    uu = u[:, a]*u[:, b]
    vv = v[:, a]*v[:, b]
    uv = u[:, a]*v[:, b] + v[:, a]*u[:, b]
    return np.stack((uu+vv, uu-vv, uv), axis=1) * scale


class ThomsonCoherencyPropagator:
    """Apply the electron-rest-frame collision generator or its exact flow.

    Scalar, globally shared positive optical depth can vary arbitrarily in
    time. Streaming, electron-frame changes and other source terms belong to
    the calling transport integrator. Signed perturbations and physical
    absolute Stokes intensities use the same linear operator.
    """

    def __init__(self, directions, weights, basis_u=None, basis_v=None):
        n = _coerce_unit_directions(directions, name="directions")
        w = np.array(weights, dtype=float, copy=True)
        _check_quadrature(n, w)
        u, v = _validate_screen_basis(n, basis_u, basis_v)
        if np.any(np.einsum("ni,ni->n", np.cross(u, v), n) < 1 - 2e-10):
            raise ValueError("circular polarization requires a right-handed screen")
        self._linear_screen = symmetric_screen_columns(u, v)
        self._direction = n
        self._weight = 3*w/(16*np.pi)

    def _samples(self, stokes):
        if np.iscomplexobj(stokes):
            raise ValueError("angular Stokes samples must be real")
        s = np.asarray(stokes, dtype=float)
        if s.shape != (len(self._weight), 4) or not np.all(np.isfinite(s)):
            raise ValueError("Stokes samples must be finite with shape (N,4)")
        return s

    def _moments(self, s):
        linear = np.einsum("ncs,nc,n->s", self._linear_screen, s[:, :3], self._weight)
        circular = 2 * (self._direction.T @ (self._weight * s[:, 3]))
        return linear, circular

    def _sky(self, linear, circular):
        sky = np.empty((len(self._weight), 4), dtype=np.result_type(linear, circular))
        sky[:, :3] = self._linear_screen @ linear
        sky[:, 3] = self._direction @ circular
        return sky

    def factor_shifted_collision(self, diagonal, collision_depth):
        """Factor diag(diagonal)-collision_depth*C for repeated complex solves.

        The direction-dependent diagonal acts equally on all Stokes channels.
        A positive real part ensures the dissipative stage is nonsingular.
        Only 6x6 and 3x3 moment systems are factored.
        """
        shift = np.asarray(diagonal, dtype=complex)
        if (shift.shape != self._weight.shape or not np.all(np.isfinite(shift))
                or np.any(shift.real <= 0.)):
            raise ValueError("diagonal must match the sky and have finite positive real part")
        depth = self.validate_optical_depth(collision_depth)
        inv = 1/(shift+depth)
        # I - V diag(depth/(shift+depth)) U = I - VU + V diag(shift/(shift+depth)) U.
        # Keep the small conserved-mode term in shift/(shift+depth) at large depth.
        residual_weight = self._weight * (shift*inv)
        irreps = np.eye(6)
        irreps[:3, :3] = (np.array([[1., 1., 1.], [1., -1., 0.], [1., 1., -2.]])
                           / np.sqrt([[3.], [2.], [6.]]))
        # Separate the exact null trace before adding the residual. A Cartesian
        # matrix with diagonal .2 and off-diagonal -.1 loses the O(1/depth)
        # trace eigenvalue to roundoff when depth is very large.
        screen_irrep = self._linear_screen @ irreps.T
        linear = np.diag([0., .3, .3, .3, .3, .3]) + np.einsum(
            "nci,ncj,n->ij", screen_irrep, screen_irrep, residual_weight)
        trace_pivot = linear[0, 0]
        linear[0, :] /= trace_pivot
        circular = .5*np.eye(3) + 2*(self._direction.T*residual_weight) @ self._direction
        factors = lu_factor(linear), lu_factor(circular)

        def solve(rhs):
            rhs = np.asarray(rhs, dtype=complex)
            if rhs.shape != (len(shift), 4) or not np.all(np.isfinite(rhs)):
                raise ValueError("right hand side must be a finite (N,4) Stokes array")
            base = inv[:, None]*rhs
            q, v = self._moments(base)
            q_irrep = irreps @ q
            q_irrep[0] /= trace_pivot
            gain = self._sky(irreps.T @ lu_solve(factors[0], q_irrep), lu_solve(factors[1], v))
            return base + (depth*inv)[:, None]*gain
        return solve

    def collision(self, stokes):
        """Return dS/ds for increasing optical depth s=integral(n_e sigma_T c dt)."""
        s = self._samples(stokes)
        return self._sky(*self._moments(s)) - s

    @staticmethod
    def validate_optical_depth(delta_tau):
        """Validate a scalar forward electron-rest optical depth."""
        if np.ndim(delta_tau) != 0 or not np.isrealobj(delta_tau):
            raise ValueError("delta_tau must be one real rest-frame optical depth")
        t = float(delta_tau)
        if not np.isfinite(t) or t < 0:
            raise ValueError("delta_tau must be finite and nonnegative")
        return t

    def _resolved_sky(self, s, t, response):
        linear, circular = self._moments(s)
        trace_part = linear[:3].mean()
        linear[:3] -= trace_part
        linear *= response(t, 0.7)
        linear[:3] += response(t, 1.) * trace_part
        return self._sky(linear, response(t, 0.5)*circular)

    def advance(self, stokes, delta_tau: float):
        """Return the Stokes sky after a finite nonnegative optical-depth increment."""
        s = self._samples(stokes)
        t = self.validate_optical_depth(delta_tau)
        if t == 0:
            return s.copy()
        return np.exp(-t)*s + self._resolved_sky(s, t, _response)

    def advance_with_source(self, stokes, delta_tau: float, source_increment):
        """Solve dS/du=delta_tau*C[S]+source_increment on 0<=u<=1.

        The source is a Stokes increment integrated across the cell, e.g.
        the gravity source times delta_N plus the known linear baryon dipole
        times delta_tau. Source and opacity are constant in the cell's u clock.
        At zero opacity this adds the source. At large opacity the damped
        modes approach their forced stationary values.
        """
        initial = self.advance(stokes, delta_tau)
        source = self._samples(source_increment)
        t = float(delta_tau)
        if t == 0:
            return initial + source
        return initial + _mean_attenuation(t)*source + self._resolved_sky(source, t, _source_response)
