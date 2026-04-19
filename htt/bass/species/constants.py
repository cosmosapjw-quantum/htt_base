"""bass/species/constants.py (LB-1) — physical constants for species
evolution.

This module is the species-layer wrapper around the project SSOT
(``bass.htt.htt.core.ssot``; imported as ``htt.core.ssot`` inside
``bass_py/``). It exposes the exact subset of constants needed by the
five-species background (photon, neutrino, baryon, CDM, Λ) together
with a small number of derived thermodynamic quantities that are NOT
stored in ``ssot.C`` but follow from it by closed-form equations
(Kolb-Turner §3.3-3.4, §5.5).

Conventions (see ``docs/lowell_bianchi/00_conventions.md §7-8``):

- Natural geometric units. Lengths in Mpc, temperatures in Kelvin,
  energy densities as fractions of today's critical density ρ_crit,0.
- Speed of light ``C_KMS = 299792.458 km/s`` is the SSOT from
  ``bass.spectrum.flrw_boltzmann`` and is re-exported here verbatim.
- The flat-ΛCDM closure ``Ω_Λ = 1 − Ω_m − Ω_r`` is enforced so the
  Friedmann-constraint residual (T-18) is zero to machine precision.

Citation map (per §10 of the species spec):

- T_γ,0:  Fixsen 2009, reported in ``ssot.C.T0_K``
- Ω_γ,0:  Kolb §3.3 eq (3.54) + §3.4 eq (3.94); blackbody + a-scaling
- T_ν/T_γ: Kolb §5.5 eq (5.14); (4/11)^{1/3}
- Ω_ν,0:  Kolb §5.5 eq (5.17); (7/8)(4/11)^{4/3} N_eff Ω_γ,0
- Y_He:   Kolb Chapter 4 (BBN)
- σ_T:    CODATA
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------
# SSOT re-export — bit-exact mirror of the Planck 2018 parameter block
# --------------------------------------------------------------------

from htt.htt.core import ssot as _ssot  # type: ignore[import-untyped]


# Re-exported directly from ``ssot.C`` (tested bit-exact in test_constants).
T_GAMMA_0_K: float = _ssot.C.T0_K           # Fixsen 2009
OMEGA_M_0: float = _ssot.C.Omega_m           # Planck 2018
H0_KM_S_MPC: float = _ssot.C.h * 100.0       # Planck 2018  (h × 100)
H_DIMLESS: float = _ssot.C.h

# Speed of light in km/s — matches ``flrw_boltzmann.C_KMS``.
C_KMS: float = 299792.458


# --------------------------------------------------------------------
# Values not (yet) in ssot.C — cite source inline.
# --------------------------------------------------------------------

# Effective number of relativistic neutrino species. Mangano et al.
# (2005) give 3.046; Planck 2018 + QED corrections give 3.044. We use
# 3.044 to match the species-spec table (00_conventions §8).
N_EFF: float = 3.044

# Helium mass fraction. BBN + Planck consistency.
Y_HE: float = 0.245

# Baryon physical density ω_b = Ω_b h² (Planck 2018).
OMEGA_B_H2: float = 0.02237

# CODATA 2018.
SIGMA_T_M2: float = 6.6524587321e-29     # Thomson cross-section
G_NEWTON_SI: float = 6.67430e-11         # N m²/kg²
K_B_SI: float = 1.380649e-23             # J/K (exact)
HBAR_SI: float = 1.054571817e-34         # J·s
C_LIGHT_SI: float = 299792458.0          # m/s (exact)

# Megaparsec in metres (CODATA/IAU).
MPC_M: float = 3.0856775814913673e22


# --------------------------------------------------------------------
# Derived fractions — single closed-form evaluation per constant.
# --------------------------------------------------------------------


def _omega_gamma_0_from_T_and_cosmo(
    T_gamma_0_K: float, h: float,
) -> float:
    """Photon density fraction today from the Stefan-Boltzmann formula.

    Kolb eq (3.54) for a bosonic thermal species:
        u_γ = (π² / 30) × g_*γ × (k_B T)⁴ / (ℏ c)³
    with ``g_*γ = 2`` (two photon polarisations). Combining,
        u_γ = (π² / 15) × (k_B T)⁴ / (ℏ c)³            [J/m³]
    and the equivalent mass density  ρ_γ = u_γ / c²  [kg/m³].

    Critical density today:
        ρ_crit,0 = 3 H_0² / (8π G)       [kg/m³]

    Ω_γ,0 = ρ_γ,0 / ρ_crit,0 with H_0 = h × 100 km/s/Mpc converted
    to s⁻¹ via H_0 [1/s] = h × 100 × 1000 / MPC_M.

    Reference: Kolb §3.3 eq (3.54); Baumann §3.2; Fixsen 2009.
    """
    H0_SI = h * 100.0 * 1000.0 / MPC_M  # 1/s
    rho_crit_0 = 3.0 * H0_SI ** 2 / (8.0 * np.pi * G_NEWTON_SI)  # kg/m³
    # Photon energy density (SI, J/m³): (π²/30) × g × (k_B T)⁴ / (ℏc)³
    # with g = 2 → prefactor (π²/15).
    u_gamma = (
        (np.pi ** 2) / 15.0
        * (K_B_SI * T_gamma_0_K) ** 4
        / (HBAR_SI * C_LIGHT_SI) ** 3
    )
    # Mass-equivalent density (ρ = u/c²)
    rho_gamma = u_gamma / C_LIGHT_SI ** 2
    return float(rho_gamma / rho_crit_0)


# ρ_γ,0 / ρ_crit,0 — derived once, cached.
OMEGA_GAMMA_0: float = _omega_gamma_0_from_T_and_cosmo(
    T_GAMMA_0_K, H_DIMLESS,
)

# T_ν / T_γ post e⁺e⁻ annihilation — Kolb eq (5.14).
T_NU_OVER_T_GAMMA: float = (4.0 / 11.0) ** (1.0 / 3.0)

# Massless neutrino fraction today — Kolb eq (5.17).
OMEGA_NU_0: float = (
    (7.0 / 8.0)
    * (4.0 / 11.0) ** (4.0 / 3.0)
    * N_EFF
    * OMEGA_GAMMA_0
)

# Total radiation fraction today.
OMEGA_R_0: float = OMEGA_GAMMA_0 + OMEGA_NU_0

# Baryon fraction today — Ω_b = ω_b / h² (Planck 2018 convention).
OMEGA_B_0: float = OMEGA_B_H2 / H_DIMLESS ** 2

# Cold dark matter fraction today — Ω_c = Ω_m − Ω_b.
OMEGA_C_0: float = OMEGA_M_0 - OMEGA_B_0

# Dark energy today — enforce flat closure Σ Ω = 1.  This makes the
# Friedmann-constraint residual (spec T-18) exactly zero when all
# species use this module as their source of truth.
OMEGA_LAMBDA_0: float = 1.0 - OMEGA_M_0 - OMEGA_R_0


# --------------------------------------------------------------------
# Public container — one import point for the whole subpackage.
# --------------------------------------------------------------------


@dataclass(frozen=True)
class SpeciesConstants:
    """Immutable bundle of the constants used by LB-1 species classes.

    Using a dataclass rather than bare module globals lets tests build
    variant cosmologies (e.g. for ``from_planck2018`` alternatives)
    without monkey-patching the module.

    Reference: ``docs/lowell_bianchi/00_conventions.md §8``.
    """
    # Cosmology fractions today
    Omega_gamma_0: float
    Omega_nu_0: float
    Omega_b_0: float
    Omega_c_0: float
    Omega_Lambda_0: float

    # Combined matter / radiation
    @property
    def Omega_r_0(self) -> float:
        return self.Omega_gamma_0 + self.Omega_nu_0

    @property
    def Omega_m_0(self) -> float:
        return self.Omega_b_0 + self.Omega_c_0

    # Hubble
    H0_km_s_mpc: float = H0_KM_S_MPC
    h: float = H_DIMLESS
    c_km_s: float = C_KMS

    @property
    def H0_mpc(self) -> float:
        """H_0 in natural-units Mpc⁻¹ (H_0/c)."""
        return self.H0_km_s_mpc / self.c_km_s

    # Thermodynamics
    T_gamma_0_K: float = T_GAMMA_0_K
    T_nu_over_T_gamma: float = T_NU_OVER_T_GAMMA
    N_eff: float = N_EFF
    Y_He: float = Y_HE

    # Microphysics (not used in LB-1 closed forms but published so
    # downstream collision / recombination modules can import in one
    # place without circular deps).
    sigma_T_m2: float = SIGMA_T_M2
    G_SI: float = G_NEWTON_SI
    k_B_SI: float = K_B_SI
    hbar_SI: float = HBAR_SI
    c_SI: float = C_LIGHT_SI
    Mpc_m: float = MPC_M


def default_constants() -> SpeciesConstants:
    """Return the canonical Planck-2018 + SSOT constants bundle.

    Reference: Kolb §3.3-3.4 (radiation), §5.5 (neutrinos);
    Planck 2018 VI (Ω_m, h); SSOT ``C.T0_K`` (Fixsen 2009).
    """
    return SpeciesConstants(
        Omega_gamma_0=OMEGA_GAMMA_0,
        Omega_nu_0=OMEGA_NU_0,
        Omega_b_0=OMEGA_B_0,
        Omega_c_0=OMEGA_C_0,
        Omega_Lambda_0=OMEGA_LAMBDA_0,
    )
