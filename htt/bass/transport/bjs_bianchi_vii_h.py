"""Barrow-Juszkiewicz-Sonoda (BJS) Bianchi VII_h temperature template, independent comparator.

Implements the closed-form, instantaneous-recombination, open-dust template used by
Jaffe et al. (2005), McEwen et al. (2006, MNRAS 369, 1858; Appendix A, eqs. A1-A12) and
the Planck isotropy papers (via McEwen's Bianchi2 code):

    dT/T(theta, phi) = (sigma/H)_0 {[A(theta) + B(theta)] sin(phi) + kappa [B(theta) - A(theta)] cos(phi)}

    A = C1 sin(theta) - C1 C2 {cos psi_E - 3 sqrt(h) sin psi_E} + C3 int s (1 - s^2) sin(psi) dtau / [(1 + s^2)^2 sinh^4(sqrt(h) tau / 2)]
    B = 3 sqrt(h) C1 sin(theta) - C1 C2 {sin psi_E + 3 sqrt(h) cos psi_E} - C3 int s (1 - s^2) cos(psi) dtau / [...]

    x = sqrt(h / (1 - Omega_0)),  C1 = 1 / (3 Omega_0 x),  C2 = 2 s_E (1 + z_E) / (1 + s_E^2),
    C3 = 4 sqrt(h) (1 - Omega_0)^{3/2} / Omega_0^2,
    s(tau) = exp(-sqrt(h) (tau - tau_0)) tan(theta / 2),
    psi(tau) = (tau - tau_0) - ln[sin^2(theta / 2) + exp(2 sqrt(h) (tau - tau_0)) cos^2(theta / 2)] / sqrt(h),
    tau_E = 2 asinh(sqrt((1/Omega_0 - 1) / (1 + z_E))) / sqrt(h),  tau_0 = 2 asinh(sqrt(1/Omega_0 - 1)) / sqrt(h),
    (omega/H)_0 = sqrt(2) sqrt(1 + h) sqrt(1 + 9 h) / (6 x^2 Omega_0) (sigma/H)_0,
    kappa = +1 (right-handed spiral) or -1 (left-handed).

Kogut, Hinshaw & Banday (1997, PRD 55, 1901) print the C2 bracket of A as
cos psi_E + 3 sqrt(h) sin psi_E and combine A sin phi + B cos phi (no handedness
factor; here kappa multiplies the cos term of that variant, so kappa = +1 is the
printed formula and kappa = -1 is this module's extension).  Both published
forms are available (``variant``); deciding which one agrees with exact geodesic
transport is the purpose of the matched comparison with ``hybrid_los_transfer``
(R107 handoff).  The angles are the template's own coordinates (VII_h axis = z); the
relation to an observing direction and a rotation onto the sky are applied by the
caller.

Parameter dictionary for the native H-normalised Lie geometry (isotropic open-dust
limit, derived in R107 THEORY_FOUNDATIONS.md): a/H = sqrt(1 - Omega) along the VII_h
axis, n/H = 1/x on the two transverse axes, h = (a/n)^2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

__all__ = ["BJSParameters", "bjs_coefficients", "bjs_temperature", "bjs_vorticity_over_hubble", "bjs_lie_geometry_today"]

Variant = Literal["mcewen2006", "kogut1997"]


@dataclass(frozen=True)
class BJSParameters:
    """Open-dust BJS template parameters (Omega_0 < 1, x > 0)."""

    omega0: float
    x: float
    z_emission: float = 1100.0
    handedness: int = 1
    sigma_over_h: float = 1.0
    variant: Variant = "mcewen2006"
    n_quadrature: int = 2048

    def __post_init__(self) -> None:
        if not (0.0 < self.omega0 < 1.0):
            raise ValueError("BJS VII_h needs an open background, 0 < Omega_0 < 1")
        if not (self.x > 0.0 and math.isfinite(self.x)):
            raise ValueError("x must be positive and finite")
        if not (self.z_emission > 0.0 and math.isfinite(self.z_emission)):
            raise ValueError("z_emission must be positive and finite")
        if self.handedness not in (1, -1):
            raise ValueError("handedness must be +1 (right) or -1 (left)")
        if self.variant not in ("mcewen2006", "kogut1997"):
            raise ValueError("variant must be 'mcewen2006' or 'kogut1997'")
        if int(self.n_quadrature) < 64:
            raise ValueError("n_quadrature must be at least 64")

    @property
    def h(self) -> float:
        return self.x * self.x * (1.0 - self.omega0)

    @property
    def tau_0(self) -> float:
        return 2.0 * math.asinh(math.sqrt(1.0 / self.omega0 - 1.0)) / math.sqrt(self.h)

    @property
    def tau_E(self) -> float:
        return 2.0 * math.asinh(math.sqrt((1.0 / self.omega0 - 1.0) / (1.0 + self.z_emission))) / math.sqrt(self.h)


def bjs_vorticity_over_hubble(p: BJSParameters) -> float:
    """(omega/H)_0 implied by (sigma/H)_0 (McEwen et al. 2006, eq. A2)."""
    h = p.h
    return math.sqrt(2.0) * math.sqrt(1.0 + h) * math.sqrt(1.0 + 9.0 * h) / (6.0 * p.x ** 2 * p.omega0) * p.sigma_over_h


def bjs_lie_geometry_today(p: BJSParameters) -> tuple[np.ndarray, np.ndarray]:
    """Isotropic-limit H-normalised (a, n) of the VII_h algebra today: a = sqrt(1-Omega) e_z, n = diag(1/x, 1/x, 0)."""
    a = np.array([0.0, 0.0, math.sqrt(1.0 - p.omega0)])
    n = np.diag([1.0 / p.x, 1.0 / p.x, 0.0])
    return a, n


def _s(tau: np.ndarray, theta: np.ndarray, p: BJSParameters) -> np.ndarray:
    return np.exp(-math.sqrt(p.h) * (tau - p.tau_0)) * np.tan(0.5 * theta)


def _psi(tau: np.ndarray, theta: np.ndarray, p: BJSParameters) -> np.ndarray:
    rh = math.sqrt(p.h)
    d = tau - p.tau_0
    return d - np.log(np.sin(0.5 * theta) ** 2 + np.exp(2.0 * rh * d) * np.cos(0.5 * theta) ** 2) / rh


def bjs_coefficients(theta: np.ndarray, p: BJSParameters) -> tuple[np.ndarray, np.ndarray]:
    """A(theta), B(theta) of the published template (dimensionless, per unit (sigma/H)_0).

    The tau integral runs over [tau_E, tau_0] with Gauss-Legendre nodes in
    u = ln sinh(sqrt(h) tau / 2), where the 1/sinh^4 weight is smooth.
    """
    th = np.atleast_1d(np.asarray(theta, dtype=np.float64))
    if np.any(th <= 0.0) or np.any(th >= math.pi):
        raise ValueError("theta must lie strictly inside (0, pi); the template is singular on the axis")
    rh = math.sqrt(p.h)
    om = p.omega0
    C1 = 1.0 / (3.0 * om * p.x)
    C3 = 4.0 * rh * (1.0 - om) ** 1.5 / om ** 2
    sE = _s(np.full_like(th, p.tau_E), th, p)
    psiE = _psi(np.full_like(th, p.tau_E), th, p)
    C2 = 2.0 * sE * (1.0 + p.z_emission) / (1.0 + sE ** 2)
    sign = -1.0 if p.variant == "mcewen2006" else 1.0
    u_lo = math.log(math.sinh(0.5 * rh * p.tau_E))
    u_hi = math.log(math.sinh(0.5 * rh * p.tau_0))
    x_gl, w_gl = np.polynomial.legendre.leggauss(int(p.n_quadrature))
    u = 0.5 * (u_hi - u_lo) * x_gl + 0.5 * (u_hi + u_lo)
    w = 0.5 * (u_hi - u_lo) * w_gl
    sh = np.exp(u)
    tau = 2.0 * np.arcsinh(sh) / rh
    dtau_du = 2.0 * sh / (rh * np.sqrt(1.0 + sh * sh))
    T = tau[None, :]
    I_sin = np.empty_like(th)
    I_cos = np.empty_like(th)
    for lo in range(0, th.size, 256):  # bounded memory: 256 x n_quadrature per block
        blk = th[lo:lo + 256, None]
        S = _s(T, blk, p)
        PSI = _psi(T, blk, p)
        kern = S * (1.0 - S ** 2) / ((1.0 + S ** 2) ** 2 * sh[None, :] ** 4) * (w * dtau_du)[None, :]
        I_sin[lo:lo + 256] = np.sum(kern * np.sin(PSI), axis=1)
        I_cos[lo:lo + 256] = np.sum(kern * np.cos(PSI), axis=1)
    A = C1 * np.sin(th) - C1 * C2 * (np.cos(psiE) + sign * 3.0 * rh * np.sin(psiE)) + C3 * I_sin
    B = 3.0 * rh * C1 * np.sin(th) - C1 * C2 * (np.sin(psiE) + 3.0 * rh * np.cos(psiE)) - C3 * I_cos
    return A, B


def bjs_temperature(theta: np.ndarray, phi: np.ndarray, p: BJSParameters) -> np.ndarray:
    """dT/T on template coordinates (theta, phi) (broadcast shapes)."""
    th, ph = np.broadcast_arrays(np.asarray(theta, dtype=np.float64), np.asarray(phi, dtype=np.float64))
    uniq, inverse = np.unique(th.ravel(), return_inverse=True)  # A, B depend on theta only
    A_u, B_u = bjs_coefficients(uniq, p)
    A = A_u[inverse].reshape(th.shape)
    B = B_u[inverse].reshape(th.shape)
    if p.variant == "mcewen2006":
        out = (A + B) * np.sin(ph) + p.handedness * (B - A) * np.cos(ph)
    else:
        out = A * np.sin(ph) + p.handedness * B * np.cos(ph)
    return p.sigma_over_h * out
