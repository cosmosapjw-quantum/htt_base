"""bass/species/cdm.py (LB-1) — cold dark matter background (c).

Closed-form FLRW dust:

    ρ_c(a) = Ω_c,0 / a³                   Kolb §9.1
    p_c    = 0
    ρ̇_c    = −Θ ρ_c                        Ellis §5.3

Pressureless, collisionless, interacts only gravitationally.

Reference: Kolb §9.1 (CDM); Ellis §5.1.
"""
from __future__ import annotations

from typing import Optional, Union

import numpy as np

from bass.species.base import (
    SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar,
)
from bass.species.background_table import FLRWBackgroundTable


_Number = Union[float, np.ndarray]


class CDMBackground(SpeciesBackground):
    """Cold dark matter (c) background — pressureless dust.

    No known non-gravitational interactions at LB-1 scope. Sound speed
    c_s,c = 0, w = 0 exactly. ρ_c(a) follows a⁻³ by standard dust
    dilution.

    Reference: Kolb §9.1; Baumann §3.3.
    """
    label = SpeciesLabel.CDM

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        Omega_c_0: float,
    ):
        if Omega_c_0 < 0.0:
            raise ValueError(
                f"Omega_c_0 must be non-negative, got {Omega_c_0}"
            )
        self._bg = bg_table
        self._Omega_c_0 = float(Omega_c_0)

    # --- SpeciesBackground interface --------------------------------------

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def rho_rest(self, eta: _Number) -> _Number:
        """ρ_c(η) = Ω_c,0 / a(η)³  (dust dilution; Kolb §9.1)."""
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return self._Omega_c_0 / a ** 3

    def p_rest(self, eta: _Number) -> _Number:
        """p_c = 0 at LB-1 scope  (pressureless dust).

        Reference: Kolb §9.1. Shape matches ``eta``; scalar → 0.0.
        Out-of-range η raises ``ValueError`` (spec §3.3).
        """
        self._bg.ensure_in_range(eta)
        arr_eta, scalar = _as_1d(eta)
        out = np.zeros_like(arr_eta)
        return _squeeze_if_scalar(out, scalar)

    def dot_rho(self, eta: _Number) -> _Number:
        """ρ̇_c = −Θ ρ_c  (continuity for w=0; Ellis §5.3)."""
        arr_eta, scalar = _as_1d(eta)
        theta = np.asarray(self._bg.interp_Theta(arr_eta), dtype=np.float64)
        rho = np.asarray(self.rho_rest(arr_eta), dtype=np.float64)
        out = -theta * rho
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> Optional[_Number]:
        """CDM temperature is not defined at background level.

        Reference: Kolb §9.1 — CDM has no associated thermal bath at
        the background level. Returns None unconditionally.
        """
        return None
