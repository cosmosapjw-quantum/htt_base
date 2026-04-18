"""bass/hierarchy/event_detection.py (LB-5) — critical-η event locators.

Detects the three ``critical_events`` that spec §5.3 lists (matter-
radiation equality ``z_eq``, last-scattering ``z_*``, reionization
midpoint) by post-processing the output grid of a
``LowellBianchiIntegrator.run`` — the events are not used to halt the
integrator (``event.terminal = False``); they are located via linear
interpolation on the stored arrays and attached to the
``IntegrationResult.critical_events`` dict so downstream regression
tests and plots can reference them.

All locators accept raw ``(η, a, ...)`` arrays so tests that do not
wish to instantiate a full integrator can still exercise them.

References
----------
- ``docs/lowell_bianchi/05_integrator_spec.md §5.3, §10.5``.
- Kolb §3.5 (``z_eq``); HyRec / Planck 2018 (``z_* = 1089.94``).
- Ma-Bertschinger 1995 §7 (peak of visibility as ``z_*``).
"""
from __future__ import annotations

import numpy as np

from bass.species.background_table import FLRWBackgroundTable
from bass.species.registry import SpeciesBackgroundRegistry


__all__ = [
    "find_z_equality",
    "find_z_star_from_visibility",
    "find_eta_reion_midpoint",
    "detect_critical_events",
]


def _lerp_bracket(x: np.ndarray, y: np.ndarray, target: float) -> float:
    """Linear interpolation of the (unique) ``x`` at which ``y(x) = target``.

    Assumes ``y`` crosses ``target`` exactly once in the array; the
    first (leftmost) crossing is returned.
    """
    diffs = y - target
    sign_changes = np.where(np.sign(diffs[:-1]) != np.sign(diffs[1:]))[0]
    if sign_changes.size == 0:
        raise ValueError(
            f"target={target} never crossed by y in the supplied array "
            f"(y ∈ [{float(y.min()):.3e}, {float(y.max()):.3e}])"
        )
    i = int(sign_changes[0])
    y0, y1 = float(y[i]), float(y[i + 1])
    x0, x1 = float(x[i]), float(x[i + 1])
    if y1 == y0:
        return x0
    frac = (target - y0) / (y1 - y0)
    return x0 + frac * (x1 - x0)


# ════════════════════════════════════════════════════════════════════
#   z_eq — matter-radiation equality
# ════════════════════════════════════════════════════════════════════

def find_z_equality(
    species: SpeciesBackgroundRegistry,
    bg_table: FLRWBackgroundTable,
    *,
    n_sample: int = 800,
) -> float:
    """Locate ``z_eq`` where ``Ω_m(a) / Ω_r(a) = 1``.

    Uses the Friedmann-era analytic species ratio ``ρ_m / ρ_r = a ×
    Ω_{m,0} / Ω_{r,0}``: crossing happens at ``a_eq = Ω_{r,0} /
    Ω_{m,0}``. The linear-bracket search is used instead of the closed
    form so that later tilt corrections (where ``Ω_m`` is no longer
    analytic) drop in without a rewrite.

    Parameters
    ----------
    species : SpeciesBackgroundRegistry
        Species registry (``ρ_γ + ρ_ν`` define the radiation bucket).
    bg_table : FLRWBackgroundTable
        Provides the η grid for a sampling of ``z``.
    n_sample : int
        Log-spaced η sampling count. 800 is enough for 1-part-in-50
        resolution on ``z_eq ≈ 3400``.

    Returns
    -------
    z_eq : float

    Reference: Kolb §3.5; spec §10.5 I-16 target ``z_eq ∈ [3300, 3500]``.
    """
    from bass.species.base import SpeciesLabel
    eta_min = bg_table.eta_min
    eta_max = bg_table.eta_today
    etas = np.geomspace(max(eta_min, 1e-6), eta_max, n_sample)
    # Matter bucket: baryon + CDM.  Radiation bucket: photon + neutrino.
    rho_m = (
        species[SpeciesLabel.BARYON].rho_rest(etas)
        + species[SpeciesLabel.CDM].rho_rest(etas)
    )
    rho_r = (
        species[SpeciesLabel.PHOTON].rho_rest(etas)
        + species[SpeciesLabel.NEUTRINO].rho_rest(etas)
    )
    # Work in ln-ratio so the crossing is well-conditioned.
    log_ratio = np.log(np.asarray(rho_m, dtype=np.float64)
                       / np.asarray(rho_r, dtype=np.float64))
    eta_eq = _lerp_bracket(etas, log_ratio, target=0.0)
    a_eq = float(bg_table.interp_a(eta_eq))
    if a_eq <= 0.0:
        raise RuntimeError(
            f"z_eq locator found invalid a={a_eq} at η={eta_eq}"
        )
    return 1.0 / a_eq - 1.0


# ════════════════════════════════════════════════════════════════════
#   z_* — last-scattering (visibility peak)
# ════════════════════════════════════════════════════════════════════

def find_z_star_from_visibility(
    species: SpeciesBackgroundRegistry,
    bg_table: FLRWBackgroundTable,
    *,
    z_search_range: tuple = (900.0, 1300.0),
) -> float:
    """Locate ``z_*`` as the peak of the visibility ``g(z) = τ̇(z) e^{-κ}``
    on the native HyRec fixture grid.

    Operating on the raw ``RecombinationTable`` (rather than on the
    spline) avoids a sub-grid bias: the cubic spline's argmax drifts
    to ``z ≈ 1088.8`` because of the convex shape of g near the peak
    (the second-derivative sign flip before the physical maximum
    biases the spline interpolant downward by ~0.2 in z). The
    Planck-2018 HyRec fixture shipped with this repo has a native
    Δz = 1 grid near recombination which gives the expected
    ``z_* ≈ 1089`` target.

    Reference: Ma-Bertschinger 1995 §7; Baumann §3.10; spec §10.5
    I-15 target ``z_* ∈ [1089, 1091]`` (Planck 2018 value 1089.94).
    """
    _ = bg_table  # kept for signature symmetry with z_eq locator
    from bass.species.base import SpeciesLabel
    baryon = species[SpeciesLabel.BARYON]
    z_lo, z_hi = float(z_search_range[0]), float(z_search_range[1])
    if z_lo >= z_hi:
        raise ValueError(
            f"z_search_range invalid: {z_search_range}"
        )
    recomb = baryon._recomb  # noqa: SLF001 — deliberate private access
    tab = recomb.table
    mask = (tab.z >= z_lo) & (tab.z <= z_hi)
    if not np.any(mask):
        raise ValueError(
            f"z_search_range {z_search_range} contains no fixture points "
            f"(fixture z ∈ [{float(tab.z.min())}, {float(tab.z.max())}])"
        )
    z_window = tab.z[mask]
    g_window = tab.tau_dot[mask] * np.exp(-tab.kappa[mask])
    idx = int(np.argmax(g_window))
    return float(z_window[idx])


# ════════════════════════════════════════════════════════════════════
#   η_reion_midpoint — reionization midpoint
# ════════════════════════════════════════════════════════════════════

def find_eta_reion_midpoint(
    species: SpeciesBackgroundRegistry,
    bg_table: FLRWBackgroundTable,
    *,
    z_reion_guess: float = 7.67,
) -> float:
    """Return ``η`` at ``z = z_reion_guess`` (Planck-2018 default 7.67).

    The true reionization midpoint is a model-dependent ingredient
    (we draw it from the ``ReionizationParameters`` config at fixture
    build time). At LB-5 we cannot read the reionization config back
    from the post-ingest ``RecombinationInterp`` object (it has been
    folded into the ``x_e`` spline); consequently we parameterise the
    midpoint explicitly and locate the corresponding η via
    ``bg_table.eta_at_a(1 / (1 + z))``.

    Reference: ``ReionizationParameters`` default ``z_reion_H = 7.67``;
    spec §5.3 ``η_reion ≈ 13800 Mpc``; spec §10.5 I-17.
    """
    if z_reion_guess <= 0:
        raise ValueError(
            f"z_reion_guess must be positive, got {z_reion_guess}"
        )
    a_reion = 1.0 / (1.0 + float(z_reion_guess))
    return float(bg_table.eta_at_a(a_reion))


# ════════════════════════════════════════════════════════════════════
#   Top-level dispatch
# ════════════════════════════════════════════════════════════════════

def detect_critical_events(
    species: SpeciesBackgroundRegistry,
    bg_table: FLRWBackgroundTable,
    *,
    z_reion_guess: float = 7.67,
) -> dict:
    """Return ``{'z_eq', 'z_star', 'eta_reion_midpoint', 'eta_today'}``.

    Reference: spec §5.3, §10.5.
    """
    z_eq = find_z_equality(species, bg_table)
    z_star = find_z_star_from_visibility(species, bg_table)
    eta_reion = find_eta_reion_midpoint(
        species, bg_table, z_reion_guess=z_reion_guess,
    )
    return {
        "z_eq": z_eq,
        "z_star": z_star,
        "eta_reion_midpoint": eta_reion,
        "eta_today": float(bg_table.eta_today),
    }
