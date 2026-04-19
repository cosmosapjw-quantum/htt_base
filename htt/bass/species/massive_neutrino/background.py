"""FB-9.2 skeleton — massive-neutrino background contract.

The load-bearing invariant is ``Sigma_mnu = 0 -> byte-identical to the
LB-1 massless NeutrinoBackground``: this placeholder reserves the
massive-ν runtime surface without replacing the existing zero-mass path.
"""
from __future__ import annotations

from typing import Union

import numpy as np

from bass.species.background_table import FLRWBackgroundTable
from bass.species.base import SpeciesBackground, SpeciesLabel


_Number = Union[float, np.ndarray]


class MassiveNeutrinoBackground(SpeciesBackground):
    """Future FB-9.2 massive-neutrino background carrier.

    The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
    LB-1 massless NeutrinoBackground`` because the registry must keep the
    zero-mass production path on the existing LB-1 class.
    """

    label = SpeciesLabel.NEUTRINO

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        mass_eV: float,
        N_q: int = 15,
    ) -> None:
        if mass_eV < 0.0:
            raise ValueError(f"mass_eV must be non-negative, got {mass_eV}")
        if N_q <= 0:
            raise ValueError(f"N_q must be positive, got {N_q}")
        self._bg = bg_table
        self.mass_eV = float(mass_eV)
        self.N_q = int(N_q)
        self._T_nu_0 = (
            bg_table.constants.T_nu_over_T_gamma
            * bg_table.constants.T_gamma_0_K
        )

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def rho_rest(self, eta: _Number) -> _Number:
        """Return the future rest-frame massive-ν density.

        The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
        LB-1 massless NeutrinoBackground`` because this skeleton must not
        be consulted on the default zero-mass registry path.
        """
        raise NotImplementedError(
            "FB-9.2 skeleton only: MassiveNeutrinoBackground.rho_rest is "
            "reserved for the future phase-space integral implementation."
        )

    def p_rest(self, eta: _Number) -> _Number:
        """Return the future rest-frame massive-ν pressure.

        The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
        LB-1 massless NeutrinoBackground`` because this skeleton must not
        be consulted on the default zero-mass registry path.
        """
        raise NotImplementedError(
            "FB-9.2 skeleton only: MassiveNeutrinoBackground.p_rest is "
            "reserved for the future phase-space integral implementation."
        )

    def dot_rho(self, eta: _Number) -> _Number:
        """Return the future proper-time density derivative.

        The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
        LB-1 massless NeutrinoBackground`` because the zero-mass runtime
        still belongs to the existing LB-1 class.
        """
        raise NotImplementedError(
            "FB-9.2 skeleton only: MassiveNeutrinoBackground.dot_rho is "
            "reserved for the future continuity implementation."
        )

    def temperature(self, eta: _Number) -> _Number:
        """Return `T_nu(eta) = T_nu,0 / a(eta)` for the skeleton carrier.

        The invariant remains ``Sigma_mnu = 0 -> byte-identical to the
        LB-1 massless NeutrinoBackground`` because exposing the shared
        `T_nu` scaling does not alter the default zero-mass registry path.
        """
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return self._T_nu_0 / a
