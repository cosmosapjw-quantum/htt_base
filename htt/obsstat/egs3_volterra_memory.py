"""EGS3 B2: Volterra depth-memory theorem (upgrade NT2-B2 + couple B4 memory).

The shear-memory law sigma' = -3 H sigma + 3 H^2 Pi(z) (PAPER-B B-shear) has the
exact integrating-factor (Volterra) solution

    sigma(eta) = sigma_0 * K(eta, eta_0) + integral_{eta_0}^{eta} K(eta, s) 3 H^2 Pi(s) ds ,
    K(eta, s) = exp( -3 * integral_s^eta H du ) ,

so the depth gap F_shear(z) = sigma(z)^2 / x_max is a Volterra functional of the
tilt anisotropic stress Pi with an EXPONENTIAL MEMORY KERNEL K. This both
upgrades NT2-B2's "sourced transport" to an explicit integral mechanism and
couples it to the Boltzmann memory bound (B4): the collision/expansion gap
gamma = 3H gives a Gronwall envelope

    |sigma(eta)| <= |sigma_0| e^{-gamma*span} + (Pi_max * 3H^2 / gamma)(1 - e^{-gamma*span}).

We verify the Volterra form equals the RK4 ODE solution and that the Gronwall
bound holds. Diagnostic-only; constant-H here, real H(z) is the to-close.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .egs2_fisher import X_MAX
from .egs2_transport import integrate_shear_memory


def volterra_shear(pi_of_z, z_grid, H: float = 1.0, sigma0: float = 0.0) -> np.ndarray:
    """Exact Volterra (integrating-factor) solution of sigma' = -3H sigma + 3H^2 Pi.

    Constant H => K(eta,s) = exp(-3H(eta-s)). Returns sigma at each node."""
    z = np.asarray(z_grid, dtype=float)
    pi = np.array([float(pi_of_z(zz)) for zz in z])
    sig = np.empty_like(z)
    sig[0] = sigma0
    src = 3.0 * H * H * pi
    for i in range(1, z.size):
        s = z[:i + 1]
        kernel = np.exp(-3.0 * H * (z[i] - s))
        trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        sig[i] = sigma0 * np.exp(-3.0 * H * (z[i] - z[0])) + trap(kernel * src[:i + 1], s)
    return sig


@dataclass(frozen=True)
class VolterraMemory:
    max_abs_diff_vs_ode: float
    gronwall_holds: bool
    kernel_decays: bool
    n_nodes: int


def volterra_memory_check(H: float = 1.0, sigma0: float = 1e-3, pi_level: float = 1e-3,
                          growth: float = 4.0, n_nodes: int = 41) -> VolterraMemory:
    """Verify the Volterra form == the RK4 ODE solution, the Gronwall envelope
    bounds it, and the memory kernel decays."""
    z = np.linspace(0.0, 1.0, n_nodes).tolist()
    pi = lambda zz: pi_level * (1.0 + growth * zz)
    vol = volterra_shear(pi, z, H, sigma0)
    ode = np.array([sigma0] + [s for _, s in integrate_shear_memory(pi, z, H, sigma0)])
    max_diff = float(np.max(np.abs(vol - ode)))
    gamma = 3.0 * H
    span = z[-1] - z[0]
    pi_max = pi(z[-1])
    bound = abs(sigma0) * np.exp(-gamma * span) + (pi_max * 3.0 * H * H / gamma) * (1.0 - np.exp(-gamma * span))
    gronwall = bool(np.max(np.abs(vol)) <= bound + 1e-9)
    # kernel decays with lag
    lags = np.linspace(0, span, 20)
    kernel = np.exp(-gamma * lags)
    kdecay = bool(np.all(np.diff(kernel) <= 0.0))
    return VolterraMemory(max_diff, gronwall, kdecay, int(n_nodes))
