"""bass/species/lambda_.py (LB-1) — cosmological constant background (Λ).

The file is named ``lambda_.py`` rather than ``lambda.py`` because
``lambda`` is a Python reserved keyword and cannot be used in an
``import`` statement. This is a minor, pragmatic deviation from
``01_species_background_spec.md §2.1``; the public class name remains
``LambdaBackground`` and the registry still iterates under
``SpeciesLabel.LAMBDA``.

Closed-form cosmological constant:

    ρ_Λ(a) = Ω_Λ,0                     (constant in comoving frame)
    p_Λ    = −ρ_Λ                      (w = −1; Ellis §5.1)
    ρ̇_Λ    = 0                         (trivially from ρ̇ + Θ(ρ+p) = 0)

Reference: Ellis §5.1; Baumann §2.5.
"""
from __future__ import annotations

from typing import Optional, Union

import numpy as np

from bass.species.base import (
    SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar,
)
from bass.species.background_table import FLRWBackgroundTable


_Number = Union[float, np.ndarray]


class LambdaBackground(SpeciesBackground):
    """Cosmological constant (Λ) background — constant ρ, w = −1.

    A vacuum-energy fluid with time-independent energy density and
    pressure p = −ρ. Continuity ρ̇ + Θ(ρ + p) = 0 reduces to 0 = 0
    automatically.

    Reference: Ellis §5.1 (perfect fluid, general w);
    Baumann §2.5 (dark energy EoS).
    """
    label = SpeciesLabel.LAMBDA

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        Omega_Lambda_0: float,
    ):
        # Ω_Λ may be negative in exotic (quintessence-flip) cosmologies,
        # but LB-1's flat ΛCDM closure guarantees Ω_Λ ≥ 0. Raise if the
        # caller supplies a non-physical negative value.
        if Omega_Lambda_0 < 0.0:
            raise ValueError(
                f"Omega_Lambda_0 must be non-negative for LB-1 "
                f"flat ΛCDM; got {Omega_Lambda_0}"
            )
        self._bg = bg_table
        self._Omega_Lambda_0 = float(Omega_Lambda_0)

    # --- SpeciesBackground interface --------------------------------------

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def rho_rest(self, eta: _Number) -> _Number:
        """ρ_Λ(η) = Ω_Λ,0 (constant; Ellis §5.1).

        Broadcasts to the shape of ``eta`` for interface consistency.
        Although the value is η-independent, the η-range of the shared
        FLRW table is enforced (spec §3.3) for API uniformity.
        """
        self._bg.ensure_in_range(eta)
        arr_eta, scalar = _as_1d(eta)
        out = np.full_like(arr_eta, self._Omega_Lambda_0)
        return _squeeze_if_scalar(out, scalar)

    def p_rest(self, eta: _Number) -> _Number:
        """p_Λ = −ρ_Λ  (w = −1 exactly; Ellis §5.1)."""
        self._bg.ensure_in_range(eta)
        arr_eta, scalar = _as_1d(eta)
        out = np.full_like(arr_eta, -self._Omega_Lambda_0)
        return _squeeze_if_scalar(out, scalar)

    def dot_rho(self, eta: _Number) -> _Number:
        """ρ̇_Λ = 0  (trivially from ρ̇ + Θ(1+w)ρ = 0 with w = −1)."""
        self._bg.ensure_in_range(eta)
        arr_eta, scalar = _as_1d(eta)
        out = np.zeros_like(arr_eta)
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> Optional[_Number]:
        """Λ has no associated thermal bath; returns None."""
        return None
