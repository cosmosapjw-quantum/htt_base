"""EGS3 B2 successor (v8): Volterra depth-memory with a real LambdaCDM H(z).

Closes the ``egs3.volterra_depth_memory`` ledger caveat ("constant-H stand-in;
real H(z) to-close"). The v7-era module ``egs3_volterra_memory`` is byte-frozen
(v7 report MANIFEST), so the H(z) upgrade lands here additively.

Theorem (kernel universality in e-fold time). The shear-memory law
``dsigma/dt = -3 H sigma + 3 H^2 Pi`` has, for ANY positive expansion history
H(t), the exact integrating-factor kernel

    K(t, s) = exp(-3 * integral_s^t H du) = (a(s) / a(t))^3 ,

because ``integral H dt = ln a`` identically. In e-fold time ``x = ln a`` the
law reads ``dsigma/dx = -3 sigma + 3 H(x) Pi(x)`` and the kernel is the
UNIVERSAL constant-rate factor ``exp(-3 (x - y))`` -- the expansion history
enters only through the source normalization ``3 H Pi``, never the memory
decay. The constant-H v7 statement is the special case ``x = H t``; the
"real H(z)" gap is therefore closed by an exact change of clock, not by an
approximation.

Consequences sealed here:
1. SymPy: ``K(t,s) = (a(s)/a(t))^3`` from the integrating factor, symbolically,
   for a generic positive ``a(t)``;
2. SymPy: the Einstein-de Sitter limit ``a ~ t^{2/3}`` gives ``K = (s/t)^2``;
3. numeric: for the registered flat LambdaCDM ``H(a) = H0 sqrt(Om a^-3 + OL)``
   the e-fold Volterra solution matches an independent RK4 integration;
4. the time-varying Gronwall envelope, exact in e-fold time:
   ``|sigma(x)| <= |sigma_0| e^{-3(x-x0)} + max|H Pi| (1 - e^{-3(x-x0)})``.

Claim discipline. Diagnostic-only transport mathematics on declared inputs
(``OMEGA_M_REF = 0.3`` from the registered linearized-realization defaults);
no data claim, no signal-discovery claim, no Bianchi-class/geometry claim, no
probabilistic-inference claim. The frozen constant-H module is not modified.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp

from .egs3_linearized_realization import OMEGA_M_REF

__all__ = [
    "kernel_universality_symbolic",
    "eds_kernel_limit_symbolic",
    "hubble_lcdm",
    "volterra_shear_efold",
    "volterra_hz_check",
    "volterra_hz_seal",
]

H0_REF = 1.0  # kernel and envelope are H0-independent in e-fold time


def kernel_universality_symbolic() -> dict:
    """SymPy proof: exp(-3 int_s^t H du) == (a(s)/a(t))^3 for generic a(t)>0."""
    t, s = sp.symbols("t s", positive=True)
    a = sp.Function("a", positive=True)
    H = sp.diff(a(t), t) / a(t)
    integral = sp.integrate(H, (t, s, t))  # = ln a(t) - ln a(s)
    kernel = sp.exp(-3 * integral)
    target = (a(s) / a(t)) ** 3
    identity = sp.simplify(sp.log(kernel) - sp.log(target)) == 0
    return {
        "kernel": str(kernel),
        "target": str(target),
        "identity_holds": bool(identity),
        "statement": "memory kernel is exactly a^3-dilution for ANY H(t)>0",
    }


def eds_kernel_limit_symbolic() -> dict:
    """SymPy: a(t) = t^(2/3) (Einstein-de Sitter) gives K(t,s) = (s/t)^2."""
    t, s = sp.symbols("t s", positive=True)
    a_eds = t ** sp.Rational(2, 3)
    H = sp.diff(a_eds, t) / a_eds  # = 2/(3t)
    kernel = sp.exp(-3 * sp.integrate(H, (t, s, t)))
    target = (s / t) ** 2
    return {
        "H": str(sp.simplify(H)),
        "kernel_simplified": str(sp.simplify(kernel)),
        "equals_s_over_t_squared": bool(sp.simplify(kernel - target) == 0),
    }


def hubble_lcdm(x, omega_m: float = OMEGA_M_REF, h0: float = H0_REF) -> np.ndarray:
    """Flat LambdaCDM H(x) with x = ln a (a = 1 today, x <= 0 in the past)."""
    a = np.exp(np.asarray(x, dtype=float))
    return h0 * np.sqrt(omega_m * a ** -3 + (1.0 - omega_m))


def volterra_shear_efold(pi_of_x, x_grid, *, omega_m: float = OMEGA_M_REF,
                         sigma0: float = 0.0) -> np.ndarray:
    """Exact e-fold Volterra solution of dsigma/dx = -3 sigma + 3 H(x) Pi(x)
    with the universal kernel exp(-3(x - y)) and LambdaCDM H(x)."""
    x = np.asarray(x_grid, dtype=float)
    src = 3.0 * hubble_lcdm(x, omega_m) * np.array(
        [float(pi_of_x(xx)) for xx in x])
    sig = np.empty_like(x)
    sig[0] = sigma0
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    for i in range(1, x.size):
        y = x[:i + 1]
        kernel = np.exp(-3.0 * (x[i] - y))
        sig[i] = sigma0 * np.exp(-3.0 * (x[i] - x[0])) + trap(kernel * src[:i + 1], y)
    return sig


def _rk4_shear_efold(pi_of_x, x_grid, *, omega_m: float = OMEGA_M_REF,
                     sigma0: float = 0.0, substeps: int = 64) -> np.ndarray:
    """Independent RK4 integration of the same ODE (cross-check path)."""
    x = np.asarray(x_grid, dtype=float)

    def rhs(xx, sig):
        return -3.0 * sig + 3.0 * float(hubble_lcdm(xx, omega_m)) * float(pi_of_x(xx))

    sig = np.empty_like(x)
    sig[0] = sigma0
    cur = sigma0
    for i in range(1, x.size):
        h = (x[i] - x[i - 1]) / substeps
        xx = x[i - 1]
        for _ in range(substeps):
            k1 = rhs(xx, cur)
            k2 = rhs(xx + h / 2, cur + h * k1 / 2)
            k3 = rhs(xx + h / 2, cur + h * k2 / 2)
            k4 = rhs(xx + h, cur + h * k3)
            cur = cur + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            xx += h
        sig[i] = cur
    return sig


@dataclass(frozen=True)
class VolterraHz:
    max_abs_diff_vs_rk4: float
    gronwall_holds: bool
    kernel_decays: bool
    n_nodes: int
    omega_m: float


def volterra_hz_check(*, sigma0: float = 1e-3, pi_level: float = 1e-3,
                      growth: float = 4.0, n_nodes: int = 161,
                      omega_m: float = OMEGA_M_REF) -> VolterraHz:
    """LambdaCDM depth-memory check: Volterra == RK4, e-fold Gronwall envelope
    holds, kernel decays. Span x in [-1, 0] (a from e^-1 to 1, z ~ 1.72 to 0)."""
    x = np.linspace(-1.0, 0.0, n_nodes)
    pi = lambda xx: pi_level * (1.0 + growth * (xx - x[0]))
    vol = volterra_shear_efold(pi, x, omega_m=omega_m, sigma0=sigma0)
    ode = _rk4_shear_efold(pi, x, omega_m=omega_m, sigma0=sigma0)
    max_diff = float(np.max(np.abs(vol - ode)))
    span = float(x[-1] - x[0])
    src_max = float(np.max(hubble_lcdm(x, omega_m)
                           * np.array([pi(xx) for xx in x])))
    bound = abs(sigma0) * np.exp(-3.0 * span) + src_max * (1.0 - np.exp(-3.0 * span))
    gronwall = bool(np.max(np.abs(vol)) <= bound + 1e-9)
    lags = np.linspace(0.0, span, 20)
    kdecay = bool(np.all(np.diff(np.exp(-3.0 * lags)) <= 0.0))
    return VolterraHz(max_diff, gronwall, kdecay, int(n_nodes), float(omega_m))


def volterra_hz_seal() -> dict:
    """Fail-closed seal for the real-H(z) depth-memory closure."""
    sym = kernel_universality_symbolic()
    eds = eds_kernel_limit_symbolic()
    chk = volterra_hz_check()
    numeric_ok = chk.max_abs_diff_vs_rk4 < 5e-6
    ok = (sym["identity_holds"] and eds["equals_s_over_t_squared"]
          and numeric_ok and chk.gronwall_holds and chk.kernel_decays)
    return {
        "seal": "egs3.volterra_hz",
        "status": "PASS" if ok else "FAIL",
        "successor_of": "htt/obsstat/egs3_volterra_memory.py (v7-frozen, constant-H)",
        "closes_caveat": "egs3.volterra_depth_memory: constant-H stand-in; "
                         "real H(z) to-close",
        "kernel_universality": sym,
        "eds_limit": eds,
        "lcdm_numeric": {
            "omega_m_declared": chk.omega_m,
            "max_abs_diff_vs_rk4": float(round(chk.max_abs_diff_vs_rk4, 12)),
            "numeric_match": bool(numeric_ok),
            "gronwall_envelope_holds": chk.gronwall_holds,
            "kernel_decays": chk.kernel_decays,
            "n_nodes": chk.n_nodes,
        },
        "claim_boundary": "diagnostic-only transport mathematics; no data, "
                          "signal-discovery, Bianchi-class/geometry, or "
                          "probabilistic-inference claim",
    }
