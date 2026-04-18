"""bass/species/baryon.py (LB-1) — baryon background (b).

Closed-form dust for the rest-frame energy density (w = 0 at
background) coupled to the existing HyRec-based recombination table
for the matter temperature T_m(z), ionisation fraction x_e(z), and
Thomson-rate τ̇(z).

    ρ_b(a) = Ω_b,0 / a³                   Kolb §3.5
    p_b    = 0                             (background level)
    ρ̇_b    = −Θ ρ_b                        Ellis §5.3
    T_m(z), x_e(z), τ̇(z), g(z) from HyRec fixture + tanh reionization

Note on pressure: the baryon sound speed c_s,b² ~ T_m/m_b is physically
nonzero and enters at the perturbation level. At the strict background
level (Ma-Bertschinger 1995 linear-order isn't an approximation — the
pressure contribution to the Friedmann equation is ~10⁻⁹ compared to
Ω_m), we set p_b = 0 exactly per ``01_species_background_spec §1.3``.

Reference: Kolb §3.3, §5.4; Baumann §3.10; Ma-Bertschinger 1995 eq (68).
"""
from __future__ import annotations

import warnings
from typing import Optional, Union

import numpy as np

from bass.recombination.recombination_ingest import RecombinationInterp
from bass.species.base import (
    SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar,
)
from bass.species.background_table import FLRWBackgroundTable


_Number = Union[float, np.ndarray]


class BaryonBackground(SpeciesBackground):
    """Baryon (b) background — dust + HyRec recombination table wrapper.

    Rest-frame energy density evolves as dust (Kolb §3.5). The
    recombination-related quantities (matter temperature, free-electron
    fraction, Thomson rate, visibility) are delegated to a supplied
    ``RecombinationInterp`` (HyRec-2 fixture + tanh reionization per
    ``bass.recombination``).

    The η-domain is restricted to the intersection of the FLRW table's
    η range and the z range spanned by ``recombination.table``. A
    ``warnings.warn`` is issued once on construction when the FLRW
    η-grid extends outside the recombination table; physically this
    means recombination queries at z > recomb.z_max (very early) or
    z < recomb.z_min are not available, but ``rho_rest`` / ``p_rest``
    / ``dot_rho`` remain well-defined on the full η-grid.

    Reference: Kolb §3.3, §5.4; Baumann §3.10.
    """
    label = SpeciesLabel.BARYON

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        Omega_b_0: float,
        recombination: RecombinationInterp,
    ):
        if Omega_b_0 <= 0.0:
            raise ValueError(
                f"Omega_b_0 must be positive, got {Omega_b_0}"
            )
        self._bg = bg_table
        self._Omega_b_0 = float(Omega_b_0)
        self._recomb = recombination

        # Recombination table z-range. Convert to η-range using the
        # shared FLRW table.  η(z_max_recomb) is in general < η_min_bg
        # only if the recomb table covers deeper radiation era than
        # the FLRW table, which is the normal case; we clip both sides.
        z_max_recomb = float(recombination.table.z_max)
        z_min_recomb = float(recombination.table.z_min)

        # bg grid z range (a[0] is smallest, z[0] is largest).
        z_max_bg = float(bg_table.z[0])
        z_min_bg = float(bg_table.z[-1])

        if z_max_recomb < z_min_bg or z_min_recomb > z_max_bg:
            raise ValueError(
                f"recombination z-range [{z_min_recomb}, {z_max_recomb}] "
                f"does not overlap FLRW table z-range "
                f"[{z_min_bg}, {z_max_bg}]"
            )
        if z_max_recomb < z_max_bg or z_min_recomb > z_min_bg:
            warnings.warn(
                f"recombination table z-range "
                f"[{z_min_recomb}, {z_max_recomb}] does not fully cover "
                f"FLRW η-grid (z ∈ [{z_min_bg}, {z_max_bg}]); queries of "
                f"x_e / T_m / tau_dot outside the table will raise.",
                RuntimeWarning, stacklevel=2,
            )

    # --- SpeciesBackground interface --------------------------------------

    def _a_of_eta(self, eta: _Number) -> _Number:
        return self._bg.interp_a(eta)

    def rho_rest(self, eta: _Number) -> _Number:
        """ρ_b(η) = Ω_b,0 / a(η)³  (dust; Kolb §3.5)."""
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return self._Omega_b_0 / a ** 3

    def p_rest(self, eta: _Number) -> _Number:
        """p_b = 0 at strict background level  (LB-1 spec §1.3).

        Baryon pressure c_s² × ρ_b ~ 10⁻⁹ compared to Ω_m at the
        Friedmann level; it enters at the perturbation level only
        (Ma-Bertschinger 1995). Returns shape-matching zero; out-of-
        range η raises ``ValueError`` (spec §3.3).
        """
        self._bg.ensure_in_range(eta)
        arr_eta, scalar = _as_1d(eta)
        out = np.zeros_like(arr_eta)
        return _squeeze_if_scalar(out, scalar)

    def dot_rho(self, eta: _Number) -> _Number:
        """ρ̇_b = −Θ ρ_b  (continuity for w=0; Ellis §5.3).

        Thomson scattering with photons preserves baryon number and
        energy at the monopole level; the coupling is to the *dipole*
        (bulk velocity), which belongs to the LB-2 multipole hierarchy.
        """
        arr_eta, scalar = _as_1d(eta)
        theta = np.asarray(self._bg.interp_Theta(arr_eta), dtype=np.float64)
        rho = np.asarray(self.rho_rest(arr_eta), dtype=np.float64)
        out = -theta * rho
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> _Number:
        """T_m(η) [K]  from the HyRec recombination table  (Kolb §5.4).

        Before Compton decoupling (z ≳ 150), T_m tracks T_γ; after,
        T_m cools adiabatically as a⁻². Queries outside the table
        z-range raise ``ValueError`` (no silent extrapolation).
        """
        z = self._z_of_eta(eta)
        return self._recomb.query_T_m(z)

    # --- Extra helpers (not part of the abstract interface) ----------------

    def x_e(self, eta: _Number) -> _Number:
        """Free-electron fraction x_e(η) from the HyRec recombination
        table (Kolb §5.4; Ali-Haïmoud-Hirata 2011).

        Domain restricted to the recombination table's z range; passes
        through to the underlying spline.
        """
        z = self._z_of_eta(eta)
        return self._recomb.query_x_e(z)

    def tau_dot(self, eta: _Number) -> _Number:
        """Differential optical depth τ̇(η) = a n_e σ_T   [Mpc⁻¹].

        Reference: Kolb §5.1; Ma-Bertschinger 1995 eq (70). Computed
        by ``bass.recombination`` during ingest and supplied here via
        the ``RecombinationInterp`` spline. The factor of ``a``
        (conformal-time version) is already baked into the table
        values.
        """
        z = self._z_of_eta(eta)
        return self._recomb.query_tau_dot(z)

    def kappa(self, eta: _Number) -> _Number:
        """Cumulative optical depth κ(η) from today's observer (Kolb §5.4).

        Monotone non-decreasing with z; κ(z=0) = 0 in the fixture.
        """
        z = self._z_of_eta(eta)
        return self._recomb.query_kappa(z)

    def visibility(self, eta: _Number) -> _Number:
        """Visibility g(η) = τ̇ × e⁻ᵏ   [Mpc⁻¹] peaking at recombination.

        Reference: Ma-Bertschinger 1995; Baumann §3.10.
        """
        z = self._z_of_eta(eta)
        return self._recomb.query_visibility(z)

    # --- Internal helpers --------------------------------------------------

    def _z_of_eta(self, eta: _Number) -> _Number:
        """η → z via the shared FLRW table."""
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return 1.0 / a - 1.0
