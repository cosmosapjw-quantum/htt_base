"""bass/species/registry.py (LB-1) — five-species ordered registry.

Collects the five LB-1 species (γ, ν, b, c, Λ) in canonical order and
exposes aggregate quantities: total energy density, total pressure,
and the Friedmann-constraint residual.

Reference: ``docs/lowell_bianchi/01_species_background_spec.md §2.5``.
Convention: ``docs/lowell_bianchi/00_conventions.md §6`` (iteration order).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Mapping, Optional, Union

import numpy as np

from bass.recombination.recombination_ingest import (
    RecombinationInterp,
    build_interpolators,
    load_recombination_table,
)
from bass.species.background_table import FLRWBackgroundTable
from bass.species.base import (
    CANONICAL_ORDER, SpeciesBackground, SpeciesLabel,
)
from bass.species.baryon import BaryonBackground
from bass.species.cdm import CDMBackground
from bass.species.constants import SpeciesConstants, default_constants
from bass.species.lambda_ import LambdaBackground
from bass.species.neutrino import NeutrinoBackground
from bass.species.photon import PhotonBackground


_Number = Union[float, np.ndarray]


def _default_recombination_path() -> Path:
    """Path to the shipped HyRec Planck-2018 fixture."""
    return (
        Path(__file__).resolve().parent.parent
        / "recombination" / "fixtures"
        / "recombination_ref_planck2018.csv"
    )


class SpeciesBackgroundRegistry(Mapping[SpeciesLabel, SpeciesBackground]):
    """Ordered immutable collection of the five LB-1 species.

    Iteration yields species in the canonical order γ → ν → b → c → Λ
    (``00_conventions.md §6``). The object implements the read-only
    ``Mapping[SpeciesLabel, SpeciesBackground]`` protocol so consumers
    can do ``registry[SpeciesLabel.PHOTON]`` and ``for s in registry``.

    Reference: ``01_species_background_spec.md §2.5``.
    """

    def __init__(
        self,
        photon: PhotonBackground,
        neutrino: NeutrinoBackground,
        baryon: BaryonBackground,
        cdm: CDMBackground,
        lambda_: LambdaBackground,
        bg_table: FLRWBackgroundTable,
    ):
        self._species: dict[SpeciesLabel, SpeciesBackground] = {
            SpeciesLabel.PHOTON: photon,
            SpeciesLabel.NEUTRINO: neutrino,
            SpeciesLabel.BARYON: baryon,
            SpeciesLabel.CDM: cdm,
            SpeciesLabel.LAMBDA: lambda_,
        }
        self._bg = bg_table

    # --- Mapping protocol --------------------------------------------------

    def __getitem__(self, label: SpeciesLabel) -> SpeciesBackground:
        return self._species[label]

    def __iter__(self) -> Iterator[SpeciesLabel]:
        # Preserve canonical order explicitly.
        return iter(CANONICAL_ORDER)

    def __len__(self) -> int:
        return len(CANONICAL_ORDER)

    # --- Aggregate physics -------------------------------------------------

    def rho_total(self, eta: _Number) -> _Number:
        """Σ_s ρ_s(η). Sums in canonical order (γ + ν + b + c + Λ)."""
        total = None
        for label in CANONICAL_ORDER:
            rho = np.asarray(self._species[label].rho_rest(eta),
                              dtype=np.float64)
            total = rho if total is None else total + rho
        # total is guaranteed non-None because CANONICAL_ORDER is non-empty.
        assert total is not None
        return total

    def p_total(self, eta: _Number) -> _Number:
        """Σ_s p_s(η) in canonical order."""
        total = None
        for label in CANONICAL_ORDER:
            p = np.asarray(self._species[label].p_rest(eta),
                            dtype=np.float64)
            total = p if total is None else total + p
        assert total is not None
        return total

    def friedmann_residual(
        self,
        eta: _Number,
        H_mpc: Optional[_Number] = None,
    ) -> _Number:
        """Flat-universe Friedmann constraint residual.

        In natural units with ρ in ρ_crit,0 and H in Mpc⁻¹:

            (H / H_0)²  −  Σ_s ρ_s(a)      = 0  at flat ΛCDM.

        When ``H_mpc`` is not supplied, the test is *self-consistency*
        of the species classes: the scale factor is read from
        ``bg_table.interp_a(η)`` and plugged back into both sides —
        the left via the analytic Friedmann formula, the right via
        each species' ``rho_rest``. With the flat-closure Ω_Λ enforced
        in ``constants.py`` the residual is machine-zero up to
        float64 arithmetic, independent of spline accuracy.

        When ``H_mpc`` is supplied (e.g. the explicit grid value), the
        residual probes the numerical consistency between the
        tabulated H and the analytic Friedmann formula.

        Reference: Baumann §2.3; Kolb §3.1.
        """
        a_val = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        rho_tot = self.rho_total(eta)
        H0 = self._bg.H0_mpc
        if H_mpc is None:
            # Analytic Friedmann at the spline-interpolated a.
            c = self._bg.constants
            H_over_H0_sq = (
                c.Omega_r_0 / a_val ** 4
                + c.Omega_m_0 / a_val ** 3
                + c.Omega_Lambda_0
            )
            return H_over_H0_sq - rho_tot
        H_used = np.asarray(H_mpc, dtype=np.float64)
        return (H_used / H0) ** 2 - rho_tot

    @property
    def constants(self) -> SpeciesConstants:
        """The SpeciesConstants bundle shared across all five species."""
        return self._bg.constants

    @property
    def bg_table(self) -> FLRWBackgroundTable:
        """The shared FLRW background table (read-only access)."""
        return self._bg

    # --- Factory -----------------------------------------------------------

    @classmethod
    def from_planck2018(
        cls,
        bg_table: Optional[FLRWBackgroundTable] = None,
        recombination: Optional[RecombinationInterp] = None,
    ) -> "SpeciesBackgroundRegistry":
        """Build the canonical Planck-2018 five-species registry.

        Parameters
        ----------
        bg_table : FLRWBackgroundTable, optional
            Shared FLRW background table. If ``None``, builds one with
            ``default_constants()``.
        recombination : RecombinationInterp, optional
            HyRec recombination interpolator. If ``None``, loads the
            shipped Planck-2018 fixture (recombination only — no
            reionization; tests that need reionization should build
            their own via ``extend_table_with_reionization``).

        Reference: ``01_species_background_spec.md §2.5``.
        """
        if bg_table is None:
            from bass.species.background_table import (
                build_flrw_background_table,
            )
            bg_table = build_flrw_background_table()
        c = bg_table.constants

        if recombination is None:
            table = load_recombination_table(_default_recombination_path())
            recombination = build_interpolators(table)

        photon = PhotonBackground(bg_table, c.Omega_gamma_0)
        neutrino = NeutrinoBackground(
            bg_table, c.Omega_nu_0, N_eff=c.N_eff, m_nu_eV=0.0,
        )
        baryon = BaryonBackground(bg_table, c.Omega_b_0, recombination)
        cdm = CDMBackground(bg_table, c.Omega_c_0)
        lambda_ = LambdaBackground(bg_table, c.Omega_Lambda_0)
        return cls(
            photon=photon, neutrino=neutrino,
            baryon=baryon, cdm=cdm, lambda_=lambda_,
            bg_table=bg_table,
        )
