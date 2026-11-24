"""Post-REI continuation of the electron history from the rei_bianchi z = 4 endpoint to the observer.

Why
---
rei_bianchi (AXBI driver, pinned 56dc609e) integrates the anisotropic H/He
reionization only on 4 <= z < 20 (``DriverConfig::validate`` and the source-redshift
guard).  The line-of-sight transfer and the optical-depth bookkeeping need n_e(N) down
to N = 0.  Below z = 4 hydrogen and HeI are ionized (x_HI ~ 1e-4 does not change
n_e at the precision used here), so n_e = n_H (x_e^{H+HeI} + x_HeIII f_He) and the
only open physics is the timing of HeII -> HeIII reionization.  This module provides

* ``tau_flrw``: tau(z_lo -> z_hi) = c sigma_T n_H0 int (1+z)^2 x_e(z) / H(z) dz on a
  flat FLRW background (validated against the R105 common-foreground numbers);
* ``DonorMatchedContinuation``: x_e continuous with the donor value at z = 4 and
  reaching 1 + 2 f_He at z = 0 through the CAMB-style tanh in y = (1+z)^{3/2} centred on
  z_HeII; the HeII timing is a declared sensitivity parameter, never fitted here;
* ``opacity_per_efold`` / ``delta_tau_on_nodes``: kappa(N) = c sigma_T n_e / H and the
  interval depths in the form consumed by ``bass.transport.hybrid_los_transfer``.

Scope: homogeneous dilution n proportional to a^-3 of the FLRW (or Bianchi
volume-averaged) background; the anisotropic redshift of the line of sight is applied
by the transfer, not here.  Conditional closure, not an REI computation below z = 4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import quad

from bass.recombination.reionization import C_LIGHT, MPC_M, SIGMA_T

__all__ = ["FlrwBackground", "DonorMatchedContinuation", "tau_flrw", "opacity_per_efold", "delta_tau_on_nodes"]

CM3_TO_M3 = 1.0e6


@dataclass(frozen=True)
class FlrwBackground:
    """Flat FLRW with matter, radiation and a cosmological constant (H0 in km/s/Mpc)."""

    h0_km_s_mpc: float = 67.4
    omega_m: float = 0.315
    omega_r: float = 9.2e-5

    @property
    def omega_l(self) -> float:
        return 1.0 - self.omega_m - self.omega_r

    def hubble_si(self, z: float | np.ndarray) -> np.ndarray:
        zp = 1.0 + np.asarray(z, dtype=float)
        h0 = self.h0_km_s_mpc * 1.0e3 / MPC_M
        return h0 * np.sqrt(self.omega_r * zp ** 4 + self.omega_m * zp ** 3 + self.omega_l)


def tau_flrw(z_lo: float, z_hi: float, xe_of_z, n_h0_cm3: float, background: FlrwBackground,
             *, epsabs: float = 0.0, epsrel: float = 1e-12) -> float:
    """Thomson depth between z_lo and z_hi for n_e = n_H0 (1+z)^3 x_e(z)."""
    if not (0.0 <= z_lo < z_hi):
        raise ValueError("need 0 <= z_lo < z_hi")
    pref = C_LIGHT * SIGMA_T * n_h0_cm3 * CM3_TO_M3

    def integrand(z):
        return (1.0 + z) ** 2 * float(xe_of_z(z)) / float(background.hubble_si(z))

    val, _ = quad(integrand, z_lo, z_hi, epsabs=epsabs, epsrel=epsrel, limit=400)
    return pref * val


def _y(z):
    return np.power(1.0 + np.asarray(z, dtype=float), 1.5)


@dataclass(frozen=True)
class DonorMatchedContinuation:
    """x_e(z) on [0, z_match], continuous with the donor and fully ionized (1 + 2 f_He) at z = 0."""

    x_e_match: float
    f_he: float
    z_match: float = 4.0
    z_heii: float = 3.5
    dz_heii: float = 0.5

    def __post_init__(self) -> None:
        if not (0.0 < self.f_he < 0.2):
            raise ValueError("f_He = n_He/n_H must lie in (0, 0.2)")
        if not (1.0 <= self.x_e_match <= 1.0 + 2.0 * self.f_he):
            raise ValueError("donor x_e at the match point must lie between 1 and 1 + 2 f_He")
        if not (0.0 < self.z_heii and self.dz_heii > 0.0 and self.z_match > 0.0):
            raise ValueError("z_HeII, its width and z_match must be positive")

    def _shape(self, z):
        dy = 1.5 * math.sqrt(1.0 + self.z_heii) * self.dz_heii
        return 0.5 * (1.0 + np.tanh((_y(self.z_heii) - _y(z)) / dy))

    def x_e(self, z: float | np.ndarray) -> np.ndarray:
        z_arr = np.asarray(z, dtype=float)
        if np.any(z_arr < 0.0) or np.any(z_arr > self.z_match + 1e-12):
            raise ValueError("the continuation is defined on 0 <= z <= z_match")
        F, F0, Fm = self._shape(z_arr), self._shape(0.0), self._shape(self.z_match)
        x_full = 1.0 + 2.0 * self.f_he
        return self.x_e_match + (x_full - self.x_e_match) * (F - Fm) / (F0 - Fm)


def opacity_per_efold(N: np.ndarray, xe_of_z, n_h0_cm3: float, background: FlrwBackground) -> np.ndarray:
    """kappa(N) = c sigma_T n_e(N) / H(N) with N = -ln(1+z)."""
    N_arr = np.asarray(N, dtype=float)
    z = np.expm1(-N_arr)
    n_e = n_h0_cm3 * CM3_TO_M3 * (1.0 + z) ** 3 * np.asarray(xe_of_z(z), dtype=float)
    return C_LIGHT * SIGMA_T * n_e / background.hubble_si(z)


def delta_tau_on_nodes(N_nodes: np.ndarray, xe_of_z, n_h0_cm3: float, background: FlrwBackground) -> np.ndarray:
    """Exact (adaptive) Thomson depth of every interval [N_k, N_{k+1}] (nodes increasing, z >= 0)."""
    N = np.asarray(N_nodes, dtype=float)
    if N.ndim != 1 or N.size < 2 or not np.all(np.diff(N) > 0.0) or N[-1] > 1e-12:
        raise ValueError("nodes must increase and end at or before N = 0")
    out = np.empty(N.size - 1)
    for k in range(N.size - 1):
        z_hi, z_lo = math.expm1(-N[k]), max(math.expm1(-N[k + 1]), 0.0)
        out[k] = tau_flrw(z_lo, z_hi, xe_of_z, n_h0_cm3, background)
    return out
