"""Cosmological integrator config helpers (V5 Blocker 3).

Implements Blocker 3 of the V5 runtime-track (see
``docs/V5_RUNTIME_TRACK_DIAGNOSIS.md``): convenience constructors that
derive ``eta_initial_mpc`` and ``eta_final_mpc`` from a species
registry's real background table rather than relying on the toy
``eta_initial=0.5 Mpc`` sentinel that legacy runtime tests use.

The IMEX runtime stability over the cosmological range
``η ∈ [261, 14147] Mpc`` was established in commit ``bce0eb9`` (Round-1/2
residual-joint operator patches). This module is the caller-facing
constructor that makes the cosmological range ergonomic: instead of
hard-coding ``261.0`` and ``14147.0`` in every call site, callers pass
a ``SpeciesBackgroundRegistry`` and the helper extracts the real
``η(z_*)`` from the HYREC-backed recombination visibility and the
``η_today`` from the background table.

References
----------
- ``docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`` — Round-1/2 operator patches.
- ``docs/V5_HANDOFF_NEXT_SESSION.md`` — Blocker 3 description.
- ``CLAUDE.md §5`` — Planck-2018 ``z_* = 1089.94`` anchor.
- ``bass.hierarchy.event_detection`` — ``detect_critical_events``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bass.hierarchy.integrator import IntegratorConfig
    from bass.species.registry import SpeciesBackgroundRegistry


__all__ = [
    "PLANCK_2018_Z_STAR",
    "DEFAULT_PRE_RECOMBINATION_MARGIN_MPC",
    "cosmological_critical_etas",
    "build_cosmological_integrator_config",
]


# Planck 2018 canonical z_* (recombination / last-scattering).
# Matches CLAUDE.md §5 semantic anchor and the
# find_z_star_from_visibility target on the shipped HYREC fixture
# (expected range [1089, 1091]).
PLANCK_2018_Z_STAR: float = 1089.94

# Pre-recombination margin (Mpc). The IMEX integrator was validated
# (commit bce0eb9) on η ∈ [261, 14147] Mpc — approximately 20 Mpc before
# η_*(z_*) ≈ 281 Mpc for Planck-2018. The margin gives the IMEX a brief
# pre-recombination ramp before Thomson fully couples photons to baryons.
DEFAULT_PRE_RECOMBINATION_MARGIN_MPC: float = 20.0


def cosmological_critical_etas(
    species: "SpeciesBackgroundRegistry",
    *,
    z_injection: float = PLANCK_2018_Z_STAR,
    pre_recombination_margin_mpc: float = DEFAULT_PRE_RECOMBINATION_MARGIN_MPC,
) -> dict[str, float]:
    """Return real-physics conformal-time anchors for a cosmological run.

    Extracts from the species registry's background table:

    - ``eta_star`` = η(z_injection) from
      ``bg_table.eta_at_a(1 / (1 + z_injection))``.
    - ``eta_today`` = ``bg_table.eta_today``.
    - ``eta_initial_mpc`` = ``eta_star - pre_recombination_margin_mpc``.

    The ``eta_initial_mpc`` value is what the IMEX integrator should
    receive as its lower bound; the margin gives Thomson coupling a
    brief pre-recombination interval to ramp up before the visibility
    peak.

    For Planck-2018 ``z_* = 1089.94`` the expected values are approximately
    ``eta_star ≈ 281 Mpc``, ``eta_today ≈ 14147 Mpc``, and
    ``eta_initial_mpc ≈ 261 Mpc`` — matching the commit bce0eb9 success
    criterion.

    **Validation (post Round-17 P3.5 PR-V0d-pre3, 2026-04-27).** The
    legacy hard guard ``z_injection ∈ [100, 5000]`` was lifted; the
    helper now queries ``species.bg_table`` for its actual a/z coverage
    and rejects only z values outside that physical range. The default
    ``build_flrw_background_table`` uses ``a_start = 1e-8`` → z up to
    ~10⁸; sufficient to anchor at any pre-recombination redshift the
    table covers. For deeper z (e.g., z = 10⁹ for D-2 closure δ), the
    species table itself must be extended (PR-V0d-pre2).

    Note: this helper validates only the **bg_table** range. Downstream
    species components (visibility ``g(η)``, Thomson rate ``Γ_T``,
    HYREC recombination history) may have tighter coverage (e.g.,
    HYREC fixture caps at z ≈ 8000); a deep z_injection that passes
    bg_table validation may still produce degenerate results from
    those secondary tables. Pre2 (species-extension) addresses that.
    """

    if not (float(z_injection) > 0.0):
        raise ValueError(
            f"z_injection must be positive (z = 0 corresponds to today, "
            f"the integration endpoint, not the start); got {z_injection}"
        )
    if float(pre_recombination_margin_mpc) < 0.0:
        raise ValueError(
            f"pre_recombination_margin_mpc must be non-negative; got "
            f"{pre_recombination_margin_mpc}"
        )

    bg_table = species.bg_table
    a_injection = 1.0 / (1.0 + float(z_injection))
    a_min = float(bg_table.a[0])
    a_max = float(bg_table.a[-1])

    if a_injection < a_min or a_injection > a_max:
        z_max_supported = (1.0 / a_min) - 1.0
        z_min_supported = (1.0 / a_max) - 1.0
        raise ValueError(
            f"z_injection={z_injection!r} maps to a={a_injection:.6e}, "
            f"which lies outside the species background table range "
            f"a ∈ [{a_min:.6e}, {a_max:.6e}] (z ∈ "
            f"[{z_min_supported:.3e}, {z_max_supported:.3e}]). "
            f"Extend the species registry (Round-17 PR-V0d-pre2) for "
            f"deeper anchors."
        )

    eta_star = float(bg_table.eta_at_a(a_injection))
    eta_today = float(bg_table.eta_today)

    eta_initial = eta_star - float(pre_recombination_margin_mpc)
    if eta_initial <= 0.0:
        raise ValueError(
            f"pre_recombination_margin_mpc={pre_recombination_margin_mpc} "
            f"drives eta_initial below zero (eta_star={eta_star:.3f} Mpc). "
            f"Reduce the margin or raise z_injection."
        )
    if eta_today <= eta_star:
        raise ValueError(
            f"bg_table.eta_today={eta_today:.3f} Mpc must exceed "
            f"eta_star={eta_star:.3f} Mpc — species.bg_table is inconsistent."
        )

    return {
        "z_injection": float(z_injection),
        "eta_star": eta_star,
        "eta_today": eta_today,
        "eta_initial_mpc": eta_initial,
        "pre_recombination_margin_mpc": float(pre_recombination_margin_mpc),
    }


def build_cosmological_integrator_config(
    species: "SpeciesBackgroundRegistry",
    *,
    z_injection: float = PLANCK_2018_Z_STAR,
    eta_final_mpc: float | None = None,
    pre_recombination_margin_mpc: float = DEFAULT_PRE_RECOMBINATION_MARGIN_MPC,
    **integrator_overrides: Any,
) -> "IntegratorConfig":
    """Return an ``IntegratorConfig`` anchored at real Planck-2018 recombination.

    Replaces the legacy ``eta_initial_mpc=0.5`` toy sentinel with the
    real ``η(z_*) - pre_recombination_margin_mpc`` derived from the
    species' recombination visibility. This is the ergonomic entry
    point for end-to-end CMB comparison runs (Tier-B cosmological IMEX).

    Parameters
    ----------
    species
        A ``SpeciesBackgroundRegistry`` — typically built via
        ``SpeciesBackgroundRegistry.from_planck2018()``.
    z_injection
        Injection redshift; default ``z_* = 1089.94`` (Planck-2018
        last-scattering). Must lie in ``[100, 5000]``.
    eta_final_mpc
        Final conformal time (Mpc). If ``None``, defaults to
        ``species.bg_table.eta_today`` (~14147 Mpc for Planck-2018).
    pre_recombination_margin_mpc
        Margin to start the integration before ``η(z_*)``. Default
        20 Mpc gives the IMEX a brief pre-recombination ramp; matches
        the commit bce0eb9 success criterion of ``eta_initial=261 Mpc``.
    **integrator_overrides
        Forwarded to ``IntegratorConfig`` (e.g. ``L_max``, ``rtol``,
        ``atol``, ``bianchi_cosmo``, ``Sigma_plus_initial``,
        ``solver_method``). ``eta_initial_mpc`` and ``eta_final_mpc``
        in overrides are forbidden — use the helper's dedicated
        parameters instead.

    Returns
    -------
    IntegratorConfig
        Ready for ``execute_tier_b_solver``.

    Raises
    ------
    ValueError
        If ``z_injection`` is outside ``[100, 5000]``, if the
        pre-recombination margin drives ``eta_initial`` below zero, or
        if ``eta_final_mpc`` is smaller than the derived
        ``eta_initial_mpc``.
    """

    from bass.hierarchy.integrator import IntegratorConfig

    if "eta_initial_mpc" in integrator_overrides:
        raise ValueError(
            "'eta_initial_mpc' is derived by "
            "build_cosmological_integrator_config from z_injection and "
            "pre_recombination_margin_mpc; it cannot be passed as an "
            "override."
        )

    anchors = cosmological_critical_etas(
        species,
        z_injection=z_injection,
        pre_recombination_margin_mpc=pre_recombination_margin_mpc,
    )

    if eta_final_mpc is None:
        eta_final = anchors["eta_today"]
    else:
        eta_final = float(eta_final_mpc)
    if eta_final <= anchors["eta_initial_mpc"]:
        raise ValueError(
            f"eta_final_mpc={eta_final} must exceed derived "
            f"eta_initial_mpc={anchors['eta_initial_mpc']:.3f} Mpc."
        )

    return IntegratorConfig(
        eta_initial_mpc=anchors["eta_initial_mpc"],
        eta_final_mpc=eta_final,
        **integrator_overrides,
    )
