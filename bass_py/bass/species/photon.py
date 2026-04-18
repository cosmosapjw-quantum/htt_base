"""bass/species/photon.py (LB-1) — photon background (γ).

Closed-form FLRW photon fluid:

    ρ_γ(a) = Ω_γ,0 / a⁴                  Kolb §3.4 eq (3.94)
    p_γ    = ρ_γ / 3                     Kolb §3.3 eq (3.51)
    T_γ(a) = T_γ,0 / a                   Kolb eq (3.78)
    ρ̇_γ    = −(4/3) Θ ρ_γ                Ellis §5.3

No monopole collision term at background (Thomson scattering couples to
the photon *dipole*, not the monopole — that coupling is resolved in
the LB-2 multipole hierarchy).

Reference: Kolb §3.3-3.4; Ellis §5.1, §5.3.
"""
from __future__ import annotations

from typing import Union

import numpy as np

from bass.species.base import (
    SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar,
)
from bass.species.background_table import FLRWBackgroundTable


_Number = Union[float, np.ndarray]


class PhotonBackground(SpeciesBackground):
    """Photon (γ) background — analytic closed form on the shared η-grid.

    The photon fluid is pure blackbody at all LB-1 epochs (z ≤ 10⁸,
    well after e⁺e⁻ annihilation). Energy density scales as a⁻⁴ by
    entropy conservation (Kolb §3.4); temperature scales as a⁻¹; the
    equation of state is w = 1/3 exactly.

    Reference: Kolb §3.3-3.4; Baumann §3.2.
    """
    label = SpeciesLabel.PHOTON

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        Omega_gamma_0: float,
    ):
        if Omega_gamma_0 <= 0.0:
            raise ValueError(
                f"Omega_gamma_0 must be positive, got {Omega_gamma_0}"
            )
        self._bg = bg_table
        self._Omega_gamma_0 = float(Omega_gamma_0)
        self._T_gamma_0 = float(bg_table.constants.T_gamma_0_K)

    # --- SpeciesBackground interface --------------------------------------

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def rho_rest(self, eta: _Number) -> _Number:
        """ρ_γ(η) = Ω_γ,0 / a(η)⁴  (Kolb §3.4 eq (3.94)).

        Exact entropy-conservation adiabat. No e⁺e⁻ reheating within
        the η-grid (that step is at z ~ 10⁹, before a_start=1e-8).
        """
        a = self._bg.interp_a(eta)
        return self._Omega_gamma_0 / np.asarray(a, dtype=np.float64) ** 4

    def p_rest(self, eta: _Number) -> _Number:
        """p_γ = ρ_γ / 3  (Kolb §3.3 eq (3.51), radiation EoS).

        w = 1/3 exactly at all η in LB-1 scope.
        """
        return np.asarray(self.rho_rest(eta), dtype=np.float64) / 3.0

    def dot_rho(self, eta: _Number) -> _Number:
        """ρ̇_γ = −(4/3) Θ ρ_γ  (Ellis §5.3, radiation continuity).

        Proper-time derivative. Equivalent to ρ_γ' = −4 𝓗 ρ_γ in
        conformal time. No monopole collision term.
        """
        arr_eta, scalar = _as_1d(eta)
        theta = np.asarray(self._bg.interp_Theta(arr_eta), dtype=np.float64)
        rho = np.asarray(self.rho_rest(arr_eta), dtype=np.float64)
        out = -(4.0 / 3.0) * theta * rho
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> _Number:
        """T_γ(η) = T_γ,0 / a(η)  [K]  (Kolb eq (3.78)).

        Blackbody temperature-scale-factor relation past the electron-
        positron epoch.
        """
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return self._T_gamma_0 / a
