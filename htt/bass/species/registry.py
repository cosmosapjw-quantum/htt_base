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
from bass.recombination.reionization import (
    ReionizationParameters,
    extend_table_with_reionization,
)
from bass.species.background_table import FLRWBackgroundTable
from bass.species.base import (
    CANONICAL_ORDER, SpeciesBackground, SpeciesLabel,
)
from bass.species.baryon import BaryonBackground
from bass.species.cdm import CDMBackground
from bass.species.constants import SpeciesConstants, default_constants
from bass.species.lambda_ import LambdaBackground
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.neutrino import NeutrinoBackground
from bass.species.photon import PhotonBackground


_Number = Union[float, np.ndarray]


def _default_recombination_path() -> Path:
    """Path to the shipped HyRec Planck-2018 fixture (z_max = 8000).

    Round-17 P3.5 PR-V0d-pre2 (2026-04-27) initially switched the default
    to the extended z_max=10¹⁰ fixture, but a smoke test on the
    post-pre2 baseline showed an unintended D_2 doubling at the
    Planck-2018 anchor η_init=261 (6.46 → 12.76). Root cause:
    ``build_interpolators`` uses ``CubicSpline`` with **natural BC**
    (2nd derivative = 0 at endpoints), which is a *global* spline —
    appending radiation-era extension rows shifts the BC at the far
    endpoint to z=10¹⁰, and the natural BC at that new endpoint
    propagates back through the spline and distorts values even at
    z ≈ 1089 (the recombination peak). The closed-form τ_dot and κ
    extension grow quadratically with (1+z), but the cubic spline with
    natural BC at z=10¹⁰ tries to bend them down to satisfy 2nd_deriv=0,
    which is incompatible with the physics.

    Reverted to the original z_max = 8000 fixture as default. The
    extended fixture remains available at
    ``recombination_ref_planck2018_z1e10.csv`` for callers that
    explicitly need deep-z coverage AND will accept the natural-BC
    distortion (or first switch ``build_interpolators`` to PCHIP /
    clamped BC). δ deep-anchor work should explicitly select the
    extended fixture and audit its spline behaviour separately.
    """
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
        neutrino: SpeciesBackground,
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
        *,
        source: str = "table",
    ) -> _Number:
        """Flat-universe Friedmann constraint residual.

        In natural units with ρ in ρ_crit,0 and H in Mpc⁻¹:

            (H / H_0)²  −  Σ_s ρ_s(a)      = 0  at flat ΛCDM.

        The left-hand H is drawn from one of three sources, controlled
        by ``H_mpc`` and ``source``:

        * ``H_mpc`` supplied explicitly → probes that value against
          Σρ at the η-corresponding scale factor.
        * ``H_mpc=None`` and ``source="table"`` (default) → uses the
          spline-interpolated ``bg_table.interp_calH(η)/interp_a(η)``.
          This is the **genuine** residual: it catches divergence
          between the stored Hubble history and Σρ built from the
          species constants. Use this as a regression probe of the
          background table itself.
        * ``H_mpc=None`` and ``source="analytic"`` → computes H from
          the analytic Friedmann formula at ``a = interp_a(η)`` using
          the same constants as ``rho_total``. This is a pure
          *constants-consistency* self-check (tautologically zero
          once flat closure holds) and is useful only for verifying
          the arithmetic of ``Omega_Lambda_0 = 1 − Omega_m_0 − Omega_r_0``.

        Historical note (audit 2026-04-18): prior to this patch the
        ``source="analytic"`` path was the default, so the residual
        was tautologically zero regardless of the bg_table's accuracy.
        Tests relying on the default mode did not actually probe the
        Hubble interpolation.

        Reference: Baumann §2.3; Kolb §3.1.
        """
        rho_tot = self.rho_total(eta)
        H0 = self._bg.H0_mpc

        if H_mpc is not None:
            H_used = np.asarray(H_mpc, dtype=np.float64)
            return (H_used / H0) ** 2 - rho_tot

        if source == "table":
            H_val = np.asarray(self._bg.interp_calH(eta), dtype=np.float64)
            a_val = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
            H_used = H_val / a_val
            return (H_used / H0) ** 2 - rho_tot

        if source == "analytic":
            a_val = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
            c = self._bg.constants
            H_over_H0_sq = (
                c.Omega_r_0 / a_val ** 4
                + c.Omega_m_0 / a_val ** 3
                + c.Omega_Lambda_0
            )
            return H_over_H0_sq - rho_tot

        raise ValueError(
            f"source must be 'table' or 'analytic', got {source!r}"
        )

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
        *,
        Sigma_mnu: float = 0.0,
        recombination_warning_policy: str = "once",
        apply_default_reionization: bool = True,
    ) -> "SpeciesBackgroundRegistry":
        """Build the canonical Planck-2018 five-species registry.

        Parameters
        ----------
        bg_table : FLRWBackgroundTable, optional
            Shared FLRW background table. If ``None``, builds one with
            ``default_constants()``.
        recombination : RecombinationInterp, optional
            HyRec recombination interpolator. If ``None``, loads the
            shipped Planck-2018 fixture and, by default, extends it
            with the standard tanh reionization history so the public
            factory matches the late-time visibility / ``tau_reion``
            physics expected from a Planck-2018 background.
        Sigma_mnu : float, optional
            Sum of neutrino masses in eV. ``Sigma_mnu = 0.0`` preserves
            the byte-identical LB-1 massless ``NeutrinoBackground``
            path; positive values populate the
            ``SpeciesLabel.NEUTRINO`` slot with an FB-9
            ``MassiveNeutrinoBackground`` without introducing a new
            enum label.
        recombination_warning_policy : {'always', 'once', 'ignore'}, optional
            Policy for the known HyRec/FLRW support-gap warning emitted
            by ``BaryonBackground``. The default ``'once'`` warns only
            once per distinct support signature in a process; use
            ``'ignore'`` for high-volume parameter sweeps or inference
            loops that intentionally rebuild the registry many times.
        apply_default_reionization : bool, optional
            When ``recombination is None`` and the shipped HyRec table is
            loaded internally, extend it with ``ReionizationParameters()``
            before building interpolators. Set ``False`` only for
            recombination-era regression work that explicitly wants the
            raw pre-reionization table.

        Reference: ``01_species_background_spec.md §2.5``.
        """
        if bg_table is None:
            from bass.species.background_table import (
                build_flrw_background_table,
            )
            # Round-17 P3.5 PR-V0d-pre2 (2026-04-27) initially extended
            # the FLRW bg_table to a_start=1e-10 (z_max=10¹⁰), but a
            # smoke test post-pre2 found this gave a 0.3% η-grid shift
            # (relative integration constant) that compounded with the
            # recombination-fixture default change to produce an
            # unintended D_2 doubling at η_init=261 (6.46 → 12.76).
            #
            # Reverted to the default a_start=1e-8 (z_max=10⁸) for the
            # production registry. Callers that need a deeper bg_table
            # (e.g., δ work at z = 10⁹) should pass an explicit
            # ``bg_table = build_flrw_background_table(a_start=1e-10)``
            # to ``from_planck2018`` AND switch to a recombination
            # fixture / interpolator that can handle the deeper range
            # without spline-BC distortion (see _default_recombination_path
            # docstring).
            bg_table = build_flrw_background_table()
        c = bg_table.constants
        if Sigma_mnu < 0.0:
            raise ValueError(f"Sigma_mnu must be non-negative, got {Sigma_mnu}")

        if recombination is None:
            table = load_recombination_table(_default_recombination_path())
            if apply_default_reionization:
                table = extend_table_with_reionization(
                    table,
                    ReionizationParameters(),
                )
            recombination = build_interpolators(table)

        photon = PhotonBackground(bg_table, c.Omega_gamma_0)
        if Sigma_mnu == 0.0:
            neutrino: SpeciesBackground = NeutrinoBackground(
                bg_table, c.Omega_nu_0, N_eff=c.N_eff, m_nu_eV=0.0,
            )
        else:
            neutrino = MassiveNeutrinoBackground(
                bg_table, mass_eV=Sigma_mnu / 3.0, N_q=15,
            )
        baryon = BaryonBackground(
            bg_table,
            c.Omega_b_0,
            recombination,
            recombination_warning_policy=recombination_warning_policy,
        )
        cdm = CDMBackground(bg_table, c.Omega_c_0)
        lambda_ = LambdaBackground(bg_table, c.Omega_Lambda_0)
        return cls(
            photon=photon, neutrino=neutrino,
            baryon=baryon, cdm=cdm, lambda_=lambda_,
            bg_table=bg_table,
        )
