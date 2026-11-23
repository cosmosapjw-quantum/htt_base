"""Exact relativistic moving electron-frame Thomson collision redistribution (N2).

Works in signature (-, +, +, +) in an orthonormal normal tetrad with photon
propagation directions n_hat, right-handed screens (u, v, n_hat), and subluminal
electron/baryon 3-velocity beta = v_b / c (|beta| < 1, Lorentz factor Gamma).

Two explicitly separated scalar opacity conventions:
- ``rest_time`` increment d tau_0 = sigma_T c n_{e,rest} dt_n (normal time * rest density):
    (d S_bol / d tau_0)_coll = D(n) [ D(n)^{-4} G'(D^4 S_bol)(n') - S_bol(n) ],
  whose 4-force int dOmega (1, n)^mu (d I_bol / d tau_0)_coll equals
    F^mu = -(delta^mu_alpha + u_b^mu u_{b,alpha}) (-T_rad^{alpha beta} u_{b,beta}) = Lambda(+beta) F'^mu.
- ``conserved_anchor`` increment d tau_anchor = sigma_T c N_H e^{-3N} x_e dN / H_n = Gamma d tau_0:
    (d S_bol / d tau_anchor)_coll = (1 - beta . n) [ D(n)^{-4} G'(D^4 S_bol)(n') - S_bol(n) ],
  whose 4-force equals F^mu / Gamma, matching covariant_thomson_force_dN exactly.

In both conventions, the scatter-in gain G' acts on rest-frame aberrated,
Doppler-shifted, screen-rotated D^4 S_bol across ALL rest-frame quadrature
angles n' before boosting back to the normal frame, NEVER multiplying a single
outgoing ray's (1 - beta . n) uniformly into an unboosted scatter-in matrix.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Sequence

import numpy as np

from bass.collision.coherency import ThomsonCoherencyPropagator, _check_quadrature
from bass.collision.electron_frame import _coerce_unit_directions, _validate_screen_basis, rotate_stokes_samples
from bass.transport.general_bianchi_transfer import _spherical_screen_basis, gl_sphere_grid
from common.relativistic_kinematics import lorentz_boost

__all__ = [
    "BoostedRayGeometry",
    "MovingFrameThomsonOperator",
    "boost_photon_and_screen",
    "covariant_thomson_four_force",
    "radiation_stress_tensor_4d",
]


@dataclass(frozen=True)
class BoostedRayGeometry:
    """Exact Lorentz aberration, Doppler factor, Jacobian, and rest-frame screens."""

    directions_normal: np.ndarray
    basis_u_normal: np.ndarray
    basis_v_normal: np.ndarray
    directions_rest: np.ndarray
    basis_u_rest: np.ndarray
    basis_v_rest: np.ndarray
    doppler_D: np.ndarray
    one_minus_beta_dot_n: np.ndarray
    solid_angle_domega_rest_over_normal: np.ndarray
    gamma: float
    beta: np.ndarray


def _validate_beta(beta: Sequence[float] | np.ndarray) -> tuple[np.ndarray, float, float]:
    b = np.asarray(beta, dtype=np.float64)
    if b.shape != (3,) or not np.all(np.isfinite(b)):
        raise ValueError("beta must be a finite real 3-vector")
    b2 = float(b @ b)
    if b2 >= 1.0:
        raise ValueError(f"beta must be strictly subluminal (|beta| < 1), got |beta|^2={b2}")
    gamma = 1.0 / math.sqrt(1.0 - b2)
    return b, b2, gamma


def boost_photon_and_screen(
    directions: np.ndarray,
    beta: Sequence[float] | np.ndarray,
    *,
    basis_u: np.ndarray | None = None,
    basis_v: np.ndarray | None = None,
) -> BoostedRayGeometry:
    """Transform normal-frame propagation directions and screens to electron rest frame.

    Uses Lorentz transformation Lambda(-beta) on null 4-vectors (1, n_hat) and
    polarization 4-vectors (0, u), (0, v) with null gauge shift along k'.
    """
    n = _coerce_unit_directions(directions, name="directions")
    u, v = _validate_screen_basis(n, basis_u, basis_v)
    if np.any(np.einsum("ni,ni->n", np.cross(u, v), n) < 1.0 - 2e-10):
        raise ValueError("input screen (u, v, n) must be right-handed")
    b, b2, gamma = _validate_beta(beta)

    if b2 == 0.0:
        N_rays = len(n)
        ones = np.ones(N_rays, dtype=np.float64)
        return BoostedRayGeometry(
            directions_normal=n.copy(),
            basis_u_normal=u.copy(),
            basis_v_normal=v.copy(),
            directions_rest=n.copy(),
            basis_u_rest=u.copy(),
            basis_v_rest=v.copy(),
            doppler_D=ones,
            one_minus_beta_dot_n=ones.copy(),
            solid_angle_domega_rest_over_normal=ones.copy(),
            gamma=1.0,
            beta=b.copy(),
        )

    # Cancellation-safe 1 - beta . n = 0.5 * ((1 - b^2) + |beta - n|^2)
    diff = n - b[None, :]
    one_minus_bn = 0.5 * ((1.0 - b2) + np.sum(diff * diff, axis=1))
    D = gamma * one_minus_bn

    L = lorentz_boost(-b)
    k4 = np.column_stack((np.ones(len(n), dtype=np.float64), n))
    k4_p = k4 @ L.T
    # Verify k'^0 consistency with cancellation-free D:
    n_p = k4_p[:, 1:] / D[:, None]
    n_p_norm = np.linalg.norm(n_p, axis=1)
    if float(np.max(np.abs(n_p_norm - 1.0))) > 1e-11:
        raise FloatingPointError("boosted photon vector lost null normalization")
    n_p = n_p / n_p_norm[:, None]

    # Null-gauge screen transport: e'^mu = Lambda e^mu - (e'^0 / k'^0) k'^mu
    zeros = np.zeros((len(n), 1), dtype=np.float64)
    u4_p = np.hstack((zeros, u)) @ L.T
    v4_p = np.hstack((zeros, v)) @ L.T
    u_p = u4_p[:, 1:] - (u4_p[:, 0] / D)[:, None] * n_p
    v_p = v4_p[:, 1:] - (v4_p[:, 0] / D)[:, None] * n_p
    # Gram-Schmidt polish to 1e-15 orthogonality while checking deviation < 1e-12
    u_p = u_p - np.sum(u_p * n_p, axis=1, keepdims=True) * n_p
    u_p = u_p / np.linalg.norm(u_p, axis=1, keepdims=True)
    v_p = v_p - np.sum(v_p * n_p, axis=1, keepdims=True) * n_p
    v_p = v_p - np.sum(v_p * u_p, axis=1, keepdims=True) * u_p
    v_p = v_p / np.linalg.norm(v_p, axis=1, keepdims=True)
    if np.any(np.einsum("ni,ni->n", np.cross(u_p, v_p), n_p) < 1.0 - 1e-10):
        raise ArithmeticError("boosted screen lost right-handed orientation")

    return BoostedRayGeometry(
        directions_normal=n,
        basis_u_normal=u,
        basis_v_normal=v,
        directions_rest=n_p,
        basis_u_rest=u_p,
        basis_v_rest=v_p,
        doppler_D=D,
        one_minus_beta_dot_n=one_minus_bn,
        solid_angle_domega_rest_over_normal=1.0 / (D * D),
        gamma=gamma,
        beta=b.copy(),
    )


def radiation_stress_tensor_4d(
    directions: np.ndarray,
    weights_normal: np.ndarray,
    intensity_bol: np.ndarray,
) -> np.ndarray:
    """Assemble T_rad^{mu nu} = int dOmega (1, n)^mu (1, n)^nu I_bol(n) in (-,+,+,+)."""
    n = _coerce_unit_directions(directions, name="directions")
    w = np.asarray(weights_normal, dtype=np.float64)
    I = np.asarray(intensity_bol, dtype=np.float64)
    if w.shape != (len(n),) or I.shape != (len(n),):
        raise ValueError("weights and intensity must match directions length")
    four_k = np.column_stack((np.ones(len(n), dtype=np.float64), n))
    return np.einsum("n,na,nb->ab", w * I, four_k, four_k)


def covariant_thomson_four_force(
    T4_rad: np.ndarray,
    beta: Sequence[float] | np.ndarray,
    *,
    clock: Literal["rest_time", "conserved_anchor"] = "rest_time",
) -> np.ndarray:
    """Exact fluid covariant elastic Thomson 4-force on radiation.

    Returns F_rad^mu obeying u_{b,mu} F_rad^mu == 0 identically:
      F_rest_time^mu = -(delta^mu_alpha + u_b^mu u_{b,alpha}) (-T_rad^{alpha beta} u_{b,beta})
      F_anchor^mu    = F_rest_time^mu / Gamma  (matches covariant_thomson_force_dN)
    """
    T4 = np.asarray(T4_rad, dtype=np.float64)
    if T4.shape != (4, 4):
        raise ValueError("T4_rad must be (4, 4)")
    b, _, gamma = _validate_beta(beta)
    u_b = np.r_[gamma, gamma * b]
    u_b_cov = np.r_[-gamma, gamma * b]
    # Negative electron energy-momentum transfer vector: V^alpha = +T_rad^{alpha beta} u_{b,beta}
    # Check signs: rest frame u_b_cov = (-1, 0), so -(T4 @ u_b_cov) = (rho', q'),
    # projection W = V + u_b (u_b_cov . V) = (0, q'), force on radiation is -W!
    V = -(T4 @ u_b_cov)
    W = V + u_b * float(u_b_cov @ V)
    force_rest_time = -W
    if clock == "rest_time":
        return force_rest_time
    if clock == "conserved_anchor":
        return force_rest_time / gamma
    raise ValueError(f"unknown clock convention {clock!r}")


class MovingFrameThomsonOperator:
    """Exact bolometric moving-electron Thomson collision & linearized perturbation operator.

    Quadrature strategy: starts from a degree >= 4 spherical quadrature (default
    Gauss-Legendre grid `n_theta`) IN THE ELECTRON REST FRAME (n', w'), and maps it
    by exact inverse boost +beta to normal-frame directions n_j and exact normal-frame
    solid-angle weights w_j = D(n_j)^2 w'_j. Thus rest-frame gain moments are EXACT
    for any subluminal speed |beta| < 1 without angular bunching bias.
    """

    def __init__(
        self,
        beta: Sequence[float] | np.ndarray,
        *,
        n_theta_rest: int = 12,
        directions_rest: np.ndarray | None = None,
        weights_rest: np.ndarray | None = None,
        basis_u_rest: np.ndarray | None = None,
        basis_v_rest: np.ndarray | None = None,
    ):
        b, b2, gamma = _validate_beta(beta)
        self.beta = b
        self.beta_sq = b2
        self.gamma = gamma

        if directions_rest is None:
            _, _, n_grid, w_grid = gl_sphere_grid(int(n_theta_rest))
            n_p = n_grid.reshape(-1, 3)
            w_p = w_grid.reshape(-1)
            u_p, v_p = _spherical_screen_basis(n_p)
        else:
            if weights_rest is None:
                raise ValueError("weights_rest required with custom directions_rest")
            n_p = _coerce_unit_directions(directions_rest, name="directions_rest")
            w_p = np.asarray(weights_rest, dtype=np.float64)
            _check_quadrature(n_p, w_p)
            u_p, v_p = _validate_screen_basis(n_p, basis_u_rest, basis_v_rest)

        self.directions_rest = n_p
        self.weights_rest = w_p
        self.basis_u_rest = u_p
        self.basis_v_rest = v_p
        # Exact rest-frame rank-9 Thomson collision/gain operator on (n', w', u', v')
        self._rest_prop = ThomsonCoherencyPropagator(n_p, w_p, u_p, v_p)

        # Boost by (-(-beta)) = +beta from rest frame -> normal frame to obtain normal rays (n, u, v, w)
        inv_geom = boost_photon_and_screen(n_p, -b, basis_u=u_p, basis_v=v_p)
        # Forward boost geometry from normal frame -> rest frame recovers n', u', v', D(n)
        self.geometry = boost_photon_and_screen(
            inv_geom.directions_rest,
            b,
            basis_u=inv_geom.basis_u_rest,
            basis_v=inv_geom.basis_v_rest,
        )
        self.directions_normal = self.geometry.directions_normal
        self.basis_u_normal = self.geometry.basis_u_normal
        self.basis_v_normal = self.geometry.basis_v_normal
        # dOmega_normal = D(n)^2 dOmega_rest (where 1 / inv_geom.doppler_D == self.geometry.doppler_D)
        D = self.geometry.doppler_D
        self.weights_normal = (D * D) * self.weights_rest

    def collision_bolometric(
        self,
        stokes_bol_normal: np.ndarray,
        *,
        clock: Literal["rest_time", "conserved_anchor"] = "rest_time",
    ) -> np.ndarray:
        """Compute exact moving-frame (d S_bol / d tau) on normal-frame rays (N, 4)."""
        s = np.asarray(stokes_bol_normal, dtype=np.float64)
        if s.shape != (len(self.directions_normal), 4) or not np.all(np.isfinite(s)):
            raise ValueError(f"expected finite (N, 4) Stokes array with N={len(self.directions_normal)}")
        D = self.geometry.doppler_D
        # Transform bolometric brightness to electron rest frame: S' = D^4 * R_screen S
        s_prime = (D ** 4)[:, None] * s
        # Note: our normal-frame basis (u_n, v_n) was constructed directly from (u_p, v_p) by inverse
        # null-gauge transport, so under forward Lorentz transport self.geometry.basis_{u,v}_rest
        # agrees with (self.basis_u_rest, self.basis_v_rest) to machine precision; explicitly rotate
        # in case of caller-reoriented screens!
        q_p, u_p = rotate_stokes_samples(
            s_prime[:, 1],
            s_prime[:, 2],
            self.geometry.basis_u_rest,
            self.geometry.basis_v_rest,
            self.basis_u_rest,
            self.basis_v_rest,
        )
        s_prime[:, 1] = q_p
        s_prime[:, 2] = u_p

        # Rest-frame Thomson gain G'[S'] = collision_rest(S') + S'
        coll_prime = self._rest_prop.collision(s_prime)
        # Rotate scattered linear polarization back to geometry.basis_{u,v}_rest (== boosted normal screens)
        qc_p, uc_p = rotate_stokes_samples(
            coll_prime[:, 1],
            coll_prime[:, 2],
            self.basis_u_rest,
            self.basis_v_rest,
            self.geometry.basis_u_rest,
            self.geometry.basis_v_rest,
        )
        coll_prime[:, 1] = qc_p
        coll_prime[:, 2] = uc_p

        # Transform back to normal frame: dS/d(tau_0) = D(n) * D(n)^{-4} * coll_prime = D(n)^{-3} * coll_prime
        D3_inv = (D ** -3)[:, None]
        if clock == "rest_time":
            return D3_inv * coll_prime
        if clock == "conserved_anchor":
            return (D3_inv / self.gamma) * coll_prime
        raise ValueError(f"unknown clock convention {clock!r}")

    def bolometric_equilibrium_sky(self, I0_rest: float = 1.0) -> np.ndarray:
        """Exact normal-frame blackbody sky in kinetic equilibrium with electrons moving at beta."""
        out = np.zeros((len(self.directions_normal), 4), dtype=np.float64)
        out[:, 0] = float(I0_rest) * (self.geometry.doppler_D ** -4)
        return out

    def four_force(
        self,
        stokes_bol_normal: np.ndarray,
        *,
        clock: Literal["rest_time", "conserved_anchor"] = "rest_time",
    ) -> dict[str, np.ndarray | float]:
        """Compare angular integral F^mu = int dOmega (1, n)^mu (dI/dtau)_coll against covariant tensor formula."""
        coll = self.collision_bolometric(stokes_bol_normal, clock=clock)
        four_k = np.column_stack((np.ones(len(self.directions_normal), dtype=np.float64), self.directions_normal))
        F_ang = np.einsum("n,na->a", self.weights_normal * coll[:, 0], four_k)
        T4 = radiation_stress_tensor_4d(
            self.directions_normal, self.weights_normal, np.asarray(stokes_bol_normal, dtype=np.float64)[:, 0]
        )
        F_cov = covariant_thomson_four_force(T4, self.beta, clock=clock)
        u_b_cov = np.r_[-self.gamma, self.gamma * self.beta]
        scale = max(float(np.linalg.norm(F_cov)), 1e-300)
        return {
            "F_angular_4d": F_ang,
            "F_covariant_4d": F_cov,
            "rel_diff": float(np.linalg.norm(F_ang - F_cov) / scale),
            "orthogonality_ub_dot_F_ang": float(abs(u_b_cov @ F_ang)),
            "orthogonality_ub_dot_F_cov": float(abs(u_b_cov @ F_cov)),
            "T4_rad": T4,
        }

    def linearized_perturbation_and_emission(
        self,
        delta_stokes_normal: np.ndarray,
        *,
        clock: Literal["rest_time", "conserved_anchor"] = "conserved_anchor",
    ) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate exact linearized collision around isotropic unpolarized normal background S_bg = (I0,0,0,0).

        Returns (homogeneous_scattering_rate_on_delta, equilibrium_dipole_quadrupole_source)
        where total linear collision is `homogeneous_rate + equilibrium_source * (I0 or 1/4*T_bg)`:
        Specifically, for normalized temperature fluctuation Theta = (1/4) (delta I / I0) in a blackbody:
          total (d S_bol / d tau) / (4 I_0) = C_hom[Theta_stokes] + emission_from_beta
        where at Theta_stokes == 0 (purely isotropic unpolarized normal-frame background),
          emission_from_beta = (d S_bol(I0=0.25) / d tau_coll)
        which equals n . beta + O(beta^2) dipole + O(beta^2) kinematic quadrupole in (I, Q, U)!
        """
        I_bg = np.zeros((len(self.directions_normal), 4), dtype=np.float64)
        I_bg[:, 0] = 0.25
        emission = self.collision_bolometric(I_bg, clock=clock)
        pert = np.asarray(delta_stokes_normal, dtype=np.float64)
        hom = self.collision_bolometric(I_bg + pert, clock=clock) - emission
        return hom, emission
