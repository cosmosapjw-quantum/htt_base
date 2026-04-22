"""bass/species/neutrino.py (LB-1) — massless-neutrino background (ν).

Closed-form FLRW neutrino fluid after e⁺e⁻ annihilation:

    T_ν(a) = (4/11)^{1/3} T_γ(a)          Kolb eq (5.14)
    ρ_ν(a) = Ω_ν,0 / a⁴                    Kolb eq (5.17) + a-scaling
    p_ν    = ρ_ν / 3
    ρ̇_ν    = −(4/3) Θ ρ_ν                  Ellis §5.3

LB-1 assumes **massless** neutrinos; massive-neutrino transition is
deferred. A non-zero ``m_nu_eV`` raises ``NotImplementedError`` with a
pointer to the relevant spec section.

Reference: Kolb §5.5; Baumann §3.6.
"""
from __future__ import annotations

from typing import Union

import numpy as np

from bass.species.base import (
    SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar,
)
from bass.species.background_table import FLRWBackgroundTable


_Number = Union[float, np.ndarray]


class NeutrinoBackground(SpeciesBackground):
    """Massless-neutrino (ν) background — closed-form FLRW fluid.

    Three generations of massless neutrinos decoupled at T ≳ 1 MeV
    (z ≈ 10¹⁰). Their temperature today is (4/11)^{1/3} T_γ,0 after
    the entropy-redistribution caused by e⁺e⁻ annihilation (Kolb eq
    5.14); their energy density is (7/8)(4/11)^{4/3} N_eff × ρ_γ
    (Kolb eq 5.17).

    Reference: Kolb §5.5; Baumann §3.6.
    """
    label = SpeciesLabel.NEUTRINO
    background_readiness = "massless_only"
    massive_neutrino_supported = False

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        Omega_nu_0: float,
        N_eff: float = 3.044,
        m_nu_eV: float = 0.0,
    ):
        if m_nu_eV != 0.0:
            raise NotImplementedError(
                "Massive neutrinos deferred to a future LB session; "
                "see docs/lowell_bianchi/01_species_background_spec.md §1.2. "
                f"Got m_nu_eV={m_nu_eV}. Pass m_nu_eV=0.0 for the LB-1 "
                "massless treatment."
            )
        if Omega_nu_0 < 0.0:
            raise ValueError(
                f"Omega_nu_0 must be non-negative, got {Omega_nu_0}"
            )
        if N_eff <= 0.0:
            raise ValueError(f"N_eff must be positive, got {N_eff}")
        self._bg = bg_table
        self._Omega_nu_0 = float(Omega_nu_0)
        self._N_eff = float(N_eff)
        self._T_nu_0 = (
            bg_table.constants.T_nu_over_T_gamma
            * bg_table.constants.T_gamma_0_K
        )

    # --- SpeciesBackground interface --------------------------------------

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def rho_rest(self, eta: _Number) -> _Number:
        """ρ_ν(η) = Ω_ν,0 / a(η)⁴  (massless limit, Kolb eq (5.17)).

        Exact once the neutrinos are decoupled (z ≪ 10¹⁰) and before
        any massive-neutrino transition (deferred).
        """
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return self._Omega_nu_0 / a ** 4

    def p_rest(self, eta: _Number) -> _Number:
        """p_ν = ρ_ν / 3 (massless radiation EoS). Reference: Kolb §5.5."""
        return np.asarray(self.rho_rest(eta), dtype=np.float64) / 3.0

    def dot_rho(self, eta: _Number) -> _Number:
        """ρ̇_ν = −(4/3) Θ ρ_ν  (collisionless free streaming at z ≪ 10¹⁰).

        Reference: Ellis §5.3. Weak interactions are frozen out on the
        LB-1 η-grid (z < 10⁸ ≪ z_dec,ν ≈ 10¹⁰), so no collision term.
        """
        arr_eta, scalar = _as_1d(eta)
        theta = np.asarray(self._bg.interp_Theta(arr_eta), dtype=np.float64)
        rho = np.asarray(self.rho_rest(arr_eta), dtype=np.float64)
        out = -(4.0 / 3.0) * theta * rho
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> _Number:
        """T_ν(η) = (4/11)^{1/3} × T_γ,0 / a(η)  [K]  (Kolb eq (5.14))."""
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return self._T_nu_0 / a
