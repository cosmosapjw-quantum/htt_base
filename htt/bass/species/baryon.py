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
from typing import Literal, Optional, Union

import numpy as np

from bass.recombination.recombination_ingest import RecombinationInterp
from bass.recombination.reionization import (
    CosmologyForRecombination,
    M_H,
    compute_tau_dot_conformal_Mpc,
)
from bass.species.base import (
    SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar,
)
from bass.species.background_table import FLRWBackgroundTable
from bass.species.constants import C_LIGHT_SI, K_B_SI


_Number = Union[float, np.ndarray]
_RecombinationWarningPolicy = Literal["always", "once", "ignore"]
_WARNED_RECOMBINATION_GAPS: set[tuple[float, float, float, float]] = set()


class BaryonBackground(SpeciesBackground):
    """Baryon (b) background — dust + HyRec recombination table wrapper.

    Rest-frame energy density evolves as dust (Kolb §3.5). The
    recombination-related quantities (matter temperature, free-electron
    fraction, Thomson rate, visibility) are delegated to a supplied
    ``RecombinationInterp`` (HyRec-2 fixture + tanh reionization per
    ``bass.recombination``).

    The recombination-query domain is restricted to the intersection of
    the FLRW table's η range and the z range spanned by
    ``recombination.table``. A configurable support-gap warning is
    available when the FLRW η-grid extends outside the recombination
    table; physically this means recombination queries at z >
    recomb.z_max (very early) or z < recomb.z_min are not available,
    but ``rho_rest`` / ``p_rest`` / ``dot_rho`` remain well-defined on
    the full η-grid. The default policy is ``'ignore'`` because actual
    out-of-domain recombination queries raise with η/z context; the
    construction-time support gap is diagnostic metadata, not an
    interpolation event.

    Reference: Kolb §3.3, §5.4; Baumann §3.10.
    """
    label = SpeciesLabel.BARYON

    def __init__(
        self,
        bg_table: FLRWBackgroundTable,
        Omega_b_0: float,
        recombination: RecombinationInterp,
        *,
        recombination_warning_policy: _RecombinationWarningPolicy = "ignore",
    ):
        if Omega_b_0 <= 0.0:
            raise ValueError(
                f"Omega_b_0 must be positive, got {Omega_b_0}"
            )
        if recombination_warning_policy not in {"always", "once", "ignore"}:
            raise ValueError(
                "recombination_warning_policy must be one of "
                "{'always', 'once', 'ignore'}"
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
        if (
            recombination_warning_policy != "ignore"
            and (z_max_recomb < z_max_bg or z_min_recomb > z_min_bg)
        ):
            signature = (
                round(z_min_recomb, 12),
                round(z_max_recomb, 12),
                round(z_min_bg, 12),
                round(z_max_bg, 12),
            )
            should_warn = (
                recombination_warning_policy == "always"
                or signature not in _WARNED_RECOMBINATION_GAPS
            )
            if recombination_warning_policy == "once":
                _WARNED_RECOMBINATION_GAPS.add(signature)
            if should_warn:
                warnings.warn(
                    f"recombination table z-range "
                    f"[{z_min_recomb}, {z_max_recomb}] does not fully cover "
                    f"FLRW η-grid (z ∈ [{z_min_bg}, {z_max_bg}]); queries of "
                    f"x_e / T_m / tau_dot outside the table will raise. "
                    "Use recombination_warning_policy='ignore' for "
                    "high-volume parameter sweeps or inference loops that "
                    "already treat the missing early-time region as expected.",
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
        return self._query_with_eta_context(eta, self._recomb.query_T_m, "T_m")

    def sound_speed_sq(self, eta: _Number) -> _Number:
        """Perturbative baryon sound speed squared ``c_s,b²`` in units of ``c²``.

        The background remains pressureless, but scalar perturbations need the
        MB/CAMB baryon pressure-gradient source. We use the standard ideal-gas
        form

            c_s,b² = (k_B T_m / m_H c²)
                     * (1 + f_He + x_e) / (1 + 4 f_He)
                     * (1 - d ln T_m / 3 d ln a)

        where ``x_e`` is free electrons per hydrogen nucleus and
        ``f_He = n_He/n_H``. Inside the HyRec table, ``T_m`` and ``x_e`` come
        from the table. Above the table ceiling, the physically coupled
        radiation-era fallback is ``T_m = T_gamma`` and
        ``x_e = 1 + 2 f_He``, giving ``d ln T_m / d ln a = -1``.

        Reference: Ma & Bertschinger 1995 Eq. 68 and CAMB baryon sound-speed
        convention.
        """

        arr_eta, scalar = _as_1d(eta)
        z = np.asarray(self._z_of_eta(arr_eta), dtype=np.float64)
        z_min = float(self._recomb.table.z_min)
        z_max = float(self._recomb.table.z_max)
        early_mask = z > z_max
        table_mask = (z >= z_min) & (z <= z_max)
        unsupported_mask = ~(early_mask | table_mask)
        if np.any(unsupported_mask):
            # Preserve the strict HyRec diagnostic for late unsupported queries.
            self.temperature(arr_eta[unsupported_mask])

        cosmo = self._cosmology_for_recombination()
        f_he = float(cosmo.f_He)
        T_m = np.empty_like(z, dtype=np.float64)
        x_e = np.empty_like(z, dtype=np.float64)
        dlnT_dlnA = np.empty_like(z, dtype=np.float64)

        if np.any(table_mask):
            z_table = z[table_mask]
            T_m[table_mask] = np.asarray(
                self._recomb.query_T_m(z_table),
                dtype=np.float64,
            )
            x_e[table_mask] = np.asarray(
                self._recomb.query_x_e(z_table),
                dtype=np.float64,
            )
            dlnT_dlnA[table_mask] = self._dln_temperature_dln_scale_factor(z_table)

        if np.any(early_mask):
            z_early = z[early_mask]
            T_m[early_mask] = float(cosmo.T_cmb) * (1.0 + z_early)
            x_e[early_mask] = 1.0 + 2.0 * f_he
            dlnT_dlnA[early_mask] = -1.0

        particle_factor = (1.0 + f_he + x_e) / (1.0 + 4.0 * f_he)
        derivative_factor = 1.0 - dlnT_dlnA / 3.0
        cs2 = (
            K_B_SI
            * T_m
            / (M_H * C_LIGHT_SI * C_LIGHT_SI)
            * particle_factor
            * derivative_factor
        )
        if not np.all(np.isfinite(cs2)) or np.any(cs2 < 0.0):
            raise RuntimeError("baryon sound_speed_sq became non-finite or negative")
        return _squeeze_if_scalar(cs2, scalar)

    # --- Extra helpers (not part of the abstract interface) ----------------

    def x_e(self, eta: _Number) -> _Number:
        """Free-electron fraction x_e(η) from the HyRec recombination
        table (Kolb §5.4; Ali-Haïmoud-Hirata 2011).

        Domain restricted to the recombination table's z range; passes
        through to the underlying spline.
        """
        return self._query_with_eta_context(eta, self._recomb.query_x_e, "x_e")

    def tau_dot(self, eta: _Number) -> _Number:
        """Differential optical depth τ̇(η) = a n_e σ_T   [Mpc⁻¹].

        Reference: Kolb §5.1; Ma-Bertschinger 1995 eq (70). Computed
        by ``bass.recombination`` during ingest and supplied here via
        the ``RecombinationInterp`` spline. The factor of ``a``
        (conformal-time version) is already baked into the table
        values.
        """
        return self._query_with_eta_context(
            eta, self._recomb.query_tau_dot, "tau_dot",
        )

    def tau_dot_fully_ionized(self, eta: _Number) -> _Number:
        """Fully-ionized high-z conformal Thomson opacity [Mpc⁻¹].

        This is the analytic early-time opacity

            τ̇ = a n_H,0 (1 + 2 f_He) (1 + z)^3 σ_T c

        evaluated from the same Planck-2018 species constants as the
        recombination fixture. It is intentionally separate from
        ``tau_dot``: the HyRec table remains the authority inside its
        support, while this helper supplies the physical asymptotic
        opacity for deep pre-recombination starts where the table has no
        rows.
        """

        arr_eta, scalar = _as_1d(eta)
        z = np.asarray(self._z_of_eta(arr_eta), dtype=np.float64)
        cosmo = self._cosmology_for_recombination()
        x_e_full = np.full_like(z, 1.0 + 2.0 * cosmo.f_He, dtype=np.float64)
        out = np.asarray(
            compute_tau_dot_conformal_Mpc(z, x_e_full, cosmo),
            dtype=np.float64,
        )
        return _squeeze_if_scalar(out, scalar)

    def tau_dot_with_early_fully_ionized_fallback(self, eta: _Number) -> _Number:
        """HyRec τ̇ with a physical fully-ionized fallback above z_max.

        Inside the recombination table support this returns exactly the
        same values as ``tau_dot``. For earlier times
        ``z > recombination.table.z_max`` it uses the fully-ionized
        analytic opacity instead of silently returning zero. Late-time
        requests below the table's z_min still raise through the normal
        ``tau_dot`` path because no late extrapolation is justified.
        """

        arr_eta, scalar = _as_1d(eta)
        z = np.asarray(self._z_of_eta(arr_eta), dtype=np.float64)
        z_min = float(self._recomb.table.z_min)
        z_max = float(self._recomb.table.z_max)
        early_mask = z > z_max
        table_mask = (z >= z_min) & (z <= z_max)
        unsupported_mask = ~(early_mask | table_mask)
        if np.any(unsupported_mask):
            # Re-enter the strict wrapper to preserve its η/z diagnostic.
            return self.tau_dot(eta)

        out = np.empty_like(z, dtype=np.float64)
        if np.any(table_mask):
            out[table_mask] = np.asarray(
                self._recomb.query_tau_dot(z[table_mask]),
                dtype=np.float64,
            )
        if np.any(early_mask):
            cosmo = self._cosmology_for_recombination()
            x_e_full = np.full(
                int(np.count_nonzero(early_mask)),
                1.0 + 2.0 * cosmo.f_He,
                dtype=np.float64,
            )
            out[early_mask] = np.asarray(
                compute_tau_dot_conformal_Mpc(z[early_mask], x_e_full, cosmo),
                dtype=np.float64,
            )
        return _squeeze_if_scalar(out, scalar)

    def kappa(self, eta: _Number) -> _Number:
        """Cumulative optical depth κ(η) from today's observer (Kolb §5.4).

        Monotone non-decreasing with z; κ(z=0) = 0 in the fixture.
        """
        return self._query_with_eta_context(
            eta, self._recomb.query_kappa, "kappa",
        )

    def visibility(self, eta: _Number) -> _Number:
        """Visibility g(η) = τ̇ × e⁻ᵏ   [Mpc⁻¹] peaking at recombination.

        Reference: Ma-Bertschinger 1995; Baumann §3.10.
        """
        return self._query_with_eta_context(
            eta, self._recomb.query_visibility, "visibility",
        )

    def tau_reion_window(
        self,
        z_lo: float = 0.0,
        z_hi: float = 30.0,
        *,
        n_samples: int = 4096,
    ) -> float:
        """Integrated optical depth ``∫ τ̇(η) dη`` over the reionization
        window (LB-4 F1 post-audit helper).

        Default window ``[z_lo, z_hi] = [0, 30]`` matches the Planck-
        2018 τ_reion definition (Aghanim+ 2018 eq 3): the optical
        depth accumulated between today and the onset of reionization.
        Returns the window integral in dimensionless units.

        Requires that the ``RecombinationInterp`` shipped to this
        ``BaryonBackground`` was built from a reionization-extended
        table (``extend_table_with_reionization``); otherwise the
        returned value is the recomb-only fraction in the window
        (typically ~0).

        Implementation: linear-in-η quadrature with ``np.trapezoid``
        on a uniform ``n_samples``-point η-grid between ``η(z_hi)``
        and ``η(z_lo)``. Fast enough to be called inside an integrator
        post-processing step (typical cost ~4 ms per call at default
        ``n_samples``).

        Parameters
        ----------
        z_lo, z_hi : float
            Redshift window. Must satisfy ``0 ≤ z_lo < z_hi`` and
            both must lie inside the recomb fixture's z support.
        n_samples : int
            Quadrature density (default 4096 is ~1e-5 rel accuracy
            against n_samples=65536 on the Planck-2018 HyRec fixture).

        Reference: Planck 2018 I (Aghanim+ 2018) eq (3); LB-6-14
        replaces its manual trapezoid with a call to this helper.
        """
        if z_lo < 0.0 or z_hi <= z_lo:
            raise ValueError(
                f"require 0 ≤ z_lo < z_hi, got z_lo={z_lo}, z_hi={z_hi}"
            )
        a_hi = 1.0 / (1.0 + float(z_hi))  # smaller a, smaller η
        a_lo = 1.0 / (1.0 + float(z_lo))
        eta_hi = float(self._bg.eta_at_a(a_hi))
        eta_lo = float(self._bg.eta_at_a(a_lo))
        if eta_hi >= eta_lo:
            raise ValueError(
                f"η monotonicity violated: η(z={z_hi})={eta_hi} "
                f"≥ η(z={z_lo})={eta_lo}"
            )
        eta_grid = np.linspace(eta_hi, eta_lo, int(n_samples))
        tau_dot = np.asarray(
            [float(self.tau_dot(e)) for e in eta_grid], dtype=np.float64,
        )
        return float(np.trapezoid(tau_dot, eta_grid))

    # --- Internal helpers --------------------------------------------------

    def _z_of_eta(self, eta: _Number) -> _Number:
        """η → z via the shared FLRW table."""
        a = np.asarray(self._bg.interp_a(eta), dtype=np.float64)
        return 1.0 / a - 1.0

    def _dln_temperature_dln_scale_factor(self, z: np.ndarray) -> np.ndarray:
        """Finite-difference ``d ln T_m / d ln a`` inside the HyRec table."""

        z_arr = np.asarray(z, dtype=np.float64)
        z_min = float(self._recomb.table.z_min)
        z_max = float(self._recomb.table.z_max)
        eps = 1.0e-3
        out = np.empty_like(z_arr, dtype=np.float64)
        for index, z_value in np.ndenumerate(z_arr):
            a_mid = 1.0 / (1.0 + float(z_value))
            a_left = a_mid * np.exp(-eps)
            a_right = a_mid * np.exp(eps)
            z_left = 1.0 / a_left - 1.0
            z_right = 1.0 / a_right - 1.0
            if z_left <= z_max and z_right >= z_min:
                z0, z1 = z_left, z_right
            elif z_left > z_max:
                z0, z1 = float(z_value), max(z_right, z_min)
            else:
                z0, z1 = min(z_left, z_max), float(z_value)
            a0 = 1.0 / (1.0 + z0)
            a1 = 1.0 / (1.0 + z1)
            T0 = float(np.asarray(self._recomb.query_T_m(z0)))
            T1 = float(np.asarray(self._recomb.query_T_m(z1)))
            if T0 <= 0.0 or T1 <= 0.0:
                raise RuntimeError(
                    f"matter temperature must stay positive, got {T0!r}, {T1!r}"
                )
            out[index] = (np.log(T1) - np.log(T0)) / (np.log(a1) - np.log(a0))
        return out

    def _cosmology_for_recombination(self) -> CosmologyForRecombination:
        """Build the recombination microphysics cosmology from species SSOT."""

        c = self._bg.constants
        return CosmologyForRecombination(
            h=float(c.h),
            T_cmb=float(c.T_gamma_0_K),
            Omega_b=float(c.Omega_b_0),
            Y_He=float(c.Y_He),
            Omega_m=float(c.Omega_m_0),
            Omega_r=float(c.Omega_r_0),
            Omega_Lambda=float(c.Omega_Lambda_0),
        )

    def _query_with_eta_context(
        self,
        eta: _Number,
        query_fn,
        field: str,
    ) -> _Number:
        """Dispatch to a ``RecombinationInterp`` ``query_*`` method with
        η-context ValueError re-raise on domain misses (LB-1 F6 post-
        audit repair).

        The underlying ``query_*`` methods speak only in ``z`` terms; when
        the caller provides an ``η`` outside the recomb-table support,
        the raw error points at ``z`` (confusing for a species-layer
        caller who supplied ``η``). This wrapper re-raises with the
        η-context attached so diagnostic playbooks can locate the misuse
        without cross-reading the η↔z mapping.
        """
        z = self._z_of_eta(eta)
        try:
            return query_fn(z)
        except ValueError as exc:
            z_arr = np.atleast_1d(np.asarray(z, dtype=np.float64))
            eta_arr = np.atleast_1d(np.asarray(eta, dtype=np.float64))
            raise ValueError(
                f"BaryonBackground.{field}(η) out of recomb table range: "
                f"η ∈ [{float(eta_arr.min()):.3e}, "
                f"{float(eta_arr.max()):.3e}] Mpc mapped to "
                f"z ∈ [{float(z_arr.min()):.3e}, "
                f"{float(z_arr.max()):.3e}]. Underlying error: {exc}"
            ) from exc
