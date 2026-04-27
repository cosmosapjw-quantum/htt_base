"""Unit tests for V5 Blocker 3 cosmological-config helper.

Verifies that ``build_cosmological_integrator_config`` extracts
physically meaningful conformal-time anchors from a Planck-2018 species
registry — matching the commit bce0eb9 success criterion where the
cosmological IMEX ran over ``η ∈ [261, 14147] Mpc`` in 130 s.

The 1366/1366 handoff baseline uses ``eta_initial_mpc=0.5`` in all its
legacy test fixtures; this module is purely additive and does not
touch the baseline.
"""
from __future__ import annotations

import pytest

from bass.runtime.cosmological_config import (
    DEFAULT_PRE_RECOMBINATION_MARGIN_MPC,
    PLANCK_2018_Z_STAR,
    build_cosmological_integrator_config,
    cosmological_critical_etas,
)
from bass.species.registry import SpeciesBackgroundRegistry


@pytest.fixture(scope="module")
def species() -> SpeciesBackgroundRegistry:
    """Planck-2018 species registry shared across tests.

    Uses the production default fixture / bg_table (a_start=1e-8,
    recombination z_max=8000). Tests of opt-in deep-extension behaviour
    use the separate ``species_extended`` fixture below.
    """
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def species_extended() -> SpeciesBackgroundRegistry:
    """Planck-2018 species registry with opt-in deep-z extension to z=10⁹.

    Round-17 P3.5 PR-V0d-pre2 introduced the deep-extension fixture
    ``recombination_ref_planck2018_z1e10.csv`` and a deeper bg_table
    (``a_start=1e-10``). The default registry was reverted to the
    original z_max=8000 baseline because the natural-BC CubicSpline
    interpolator distorted recombination-era values when the fixture
    extended to z=10¹⁰. Callers that explicitly need deep coverage
    (δ work) opt in here, accepting the spline-BC distortion until
    a clamped-BC or PCHIP migration of ``build_interpolators`` lands.
    """
    from pathlib import Path

    from bass.recombination.recombination_ingest import (
        build_interpolators,
        load_recombination_table,
    )
    from bass.recombination.reionization import (
        ReionizationParameters,
        extend_table_with_reionization,
    )
    from bass.species.background_table import build_flrw_background_table

    repo_htt = Path(__file__).resolve().parents[2]
    extended_path = (
        repo_htt
        / "bass" / "recombination" / "fixtures"
        / "recombination_ref_planck2018_z1e10.csv"
    )
    table = load_recombination_table(extended_path)
    table = extend_table_with_reionization(table, ReionizationParameters())
    recomb = build_interpolators(table)

    bg_table = build_flrw_background_table(a_start=1.0e-10)

    return SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        recombination=recomb,
        recombination_warning_policy="ignore",
    )


def test_planck2018_z_star_default_matches_claude_md_anchor() -> None:
    """Default z_* matches the CLAUDE.md §5 semantic anchor (z_* = 1089.94)."""
    assert PLANCK_2018_Z_STAR == pytest.approx(1089.94, abs=1e-6)


def test_default_pre_recombination_margin_matches_bce0eb9_validation() -> None:
    """Default margin of 20 Mpc matches the IMEX validation at commit bce0eb9
    where eta_initial=261 Mpc ≈ η_* - 20 was verified to run in 130 s."""
    assert DEFAULT_PRE_RECOMBINATION_MARGIN_MPC == pytest.approx(20.0, abs=1e-6)


def test_cosmological_critical_etas_returns_planck_2018_values(species) -> None:
    """Extracted eta_star ≈ 281 Mpc, eta_today ≈ 14147 Mpc for Planck-2018;
    eta_initial = eta_star - 20 ≈ 261 Mpc matches the commit bce0eb9 range."""
    anchors = cosmological_critical_etas(species)
    # Planck-2018 η_* (from detect_critical_events baseline tests):
    # 270 ≤ η_* ≤ 290 Mpc.
    assert 270.0 <= anchors["eta_star"] <= 290.0, (
        f"eta_star={anchors['eta_star']} outside Planck-2018 band"
    )
    # η_today is the canonical 14147 Mpc target.
    assert 14000.0 <= anchors["eta_today"] <= 14300.0, (
        f"eta_today={anchors['eta_today']} outside Planck-2018 band"
    )
    # Derived eta_initial = eta_star - 20 Mpc.
    assert anchors["eta_initial_mpc"] == pytest.approx(
        anchors["eta_star"] - 20.0, abs=1e-9
    )
    assert anchors["z_injection"] == pytest.approx(PLANCK_2018_Z_STAR, abs=1e-9)
    assert anchors["pre_recombination_margin_mpc"] == pytest.approx(20.0, abs=1e-9)


def test_cosmological_critical_etas_custom_injection_redshift(species) -> None:
    """A lower z_injection gives a LATER conformal time (universe is older
    at z = 500 than at z = 1089.94), so eta_star strictly increases as
    z_injection decreases."""
    later = cosmological_critical_etas(species, z_injection=500.0)
    default = cosmological_critical_etas(species)
    assert later["eta_star"] > default["eta_star"], (
        "lower redshift z=500 corresponds to later conformal time than "
        "z_*=1089.94, so eta(z=500) > eta(z=1089.94)"
    )
    assert later["z_injection"] == pytest.approx(500.0, abs=1e-9)
    # eta_today is independent of z_injection.
    assert later["eta_today"] == pytest.approx(default["eta_today"], abs=1e-9)


def test_cosmological_critical_etas_rejects_non_positive_z(species) -> None:
    """z_injection must be strictly positive (z = 0 is the integration endpoint).

    Round-17 P3.5 PR-V0d-pre3 (2026-04-27) lifted the legacy hard guard
    ``z_injection ∈ [100, 5000]`` in favour of species-table-aware validation.
    The remaining hard rejections are non-positive z and z outside the
    species ``bg_table`` coverage.
    """
    with pytest.raises(ValueError, match="z_injection must be positive"):
        cosmological_critical_etas(species, z_injection=0.0)
    with pytest.raises(ValueError, match="z_injection must be positive"):
        cosmological_critical_etas(species, z_injection=-100.0)


def test_cosmological_critical_etas_rejects_z_outside_bg_table(species) -> None:
    """z_injection outside the bg_table's actual a/z range is rejected.

    The default ``build_flrw_background_table`` uses ``a_start = 1e-8`` →
    z up to ~10⁸. A z far above that should be rejected with a clear
    message pointing at PR-V0d-pre2 (species extension).
    """
    very_deep_z = 1.0e10  # well beyond a_start = 1e-8 (z ≈ 1e8)
    with pytest.raises(
        ValueError,
        match="outside the species background table range",
    ):
        cosmological_critical_etas(species, z_injection=very_deep_z)


def test_cosmological_critical_etas_accepts_z_inside_bg_table_below_legacy_floor(
    species,
) -> None:
    """z_injection = 50 is below the lifted hard floor of 100 but inside
    the bg_table's a/z range; PR-V0d-pre3 must accept it.

    Pre-PR-V0d-pre3 this raised; post-PR-V0d-pre3 it returns valid anchors.
    """
    anchors = cosmological_critical_etas(species, z_injection=50.0)
    assert anchors["z_injection"] == pytest.approx(50.0, abs=1e-9)
    # eta_star at z=50 is much later than at z=1089.94 (universe older).
    default_anchors = cosmological_critical_etas(species)
    assert anchors["eta_star"] > default_anchors["eta_star"]


def test_cosmological_critical_etas_accepts_z_inside_bg_table_above_legacy_ceiling(
    species,
) -> None:
    """z_injection = 10000 is above the lifted hard ceiling of 5000 but
    well inside the bg_table's a/z range; PR-V0d-pre3 must accept it.

    Post-PR-V0d-pre2 (2026-04-27) the bg_table extends to a_start=1e-10
    (z_max ≈ 10¹⁰) and the recombination fixture extends to z_max=10¹⁰,
    so z = 10000 sits comfortably inside both tables.
    """
    anchors = cosmological_critical_etas(species, z_injection=10000.0)
    assert anchors["z_injection"] == pytest.approx(10000.0, abs=1e-9)
    # eta_star at z=10000 is much earlier than at z=1089.94.
    default_anchors = cosmological_critical_etas(species)
    assert anchors["eta_star"] < default_anchors["eta_star"]


def test_cosmological_critical_etas_accepts_z_inside_extended_bg_table_when_opted_in(
    species_extended,
) -> None:
    """When the caller explicitly opts into the deep-extended bg_table
    (a_start=1e-10) AND extended recombination fixture, z = 10⁹ (the
    audit's δ deep anchor target) is reachable.

    PR-V0d-pre2's default-swap was REVERTED post-smoke-test because the
    natural-BC CubicSpline interpolator distorted the recombination
    spline interior values when fixture endpoint moved from z=8000 to
    z=10¹⁰. Production default remains z_max=8000; opt-in callers
    (δ work) explicitly provide the extended fixture + bg_table.
    """
    anchors = cosmological_critical_etas(
        species_extended,
        z_injection=1.0e9,
        pre_recombination_margin_mpc=0.0,
    )
    assert anchors["z_injection"] == pytest.approx(1.0e9, abs=1e-3)
    assert 1.0e-5 < anchors["eta_star"] < 1.0e-2, (
        f"eta_star at z=1e9 should be in [1e-5, 1e-2] Mpc but got "
        f"{anchors['eta_star']}"
    )


def test_cosmological_critical_etas_rejects_z_beyond_default_bg_table(
    species,
) -> None:
    """The production default bg_table (a_start=1e-8 → z_max ≈ 10⁸)
    rejects z > 10⁸. Callers that need deeper anchors must opt into
    the extended bg_table explicitly via ``bg_table=
    build_flrw_background_table(a_start=1e-10)``.
    """
    very_deep_z = 1.0e9  # beyond default a_start=1e-8 (z_max ≈ 10⁸)
    with pytest.raises(
        ValueError,
        match="outside the species background table range",
    ):
        cosmological_critical_etas(species, z_injection=very_deep_z)


def test_cosmological_critical_etas_rejects_negative_margin(species) -> None:
    with pytest.raises(ValueError, match="pre_recombination_margin_mpc must be"):
        cosmological_critical_etas(species, pre_recombination_margin_mpc=-5.0)


def test_cosmological_critical_etas_rejects_excessive_margin(species) -> None:
    """Margin larger than eta_star drives eta_initial negative."""
    with pytest.raises(ValueError, match="drives eta_initial below zero"):
        cosmological_critical_etas(
            species, pre_recombination_margin_mpc=500.0
        )


def test_build_config_defaults_match_commit_bce0eb9_cosmological_range(species) -> None:
    """Default config carries η ∈ [~261, ~14147] Mpc — the exact range
    validated over 130 s in commit bce0eb9."""
    config = build_cosmological_integrator_config(species)
    # 241 ≤ eta_initial ≤ 270 Mpc (eta_star in [270, 290] − 20 Mpc margin).
    assert 241.0 <= config.eta_initial_mpc <= 270.0
    assert 14000.0 <= config.eta_final_mpc <= 14300.0


def test_build_config_forwards_integrator_overrides(species) -> None:
    """L_max, rtol, atol, solver_method pass through to IntegratorConfig."""
    config = build_cosmological_integrator_config(
        species,
        L_max=8,
        rtol=1e-7,
        atol=1e-13,
        solver_method="LSODA",
    )
    assert config.L_max == 8
    assert config.rtol == pytest.approx(1e-7)
    assert config.atol == pytest.approx(1e-13)
    assert config.solver_method == "LSODA"


def test_build_config_rejects_eta_initial_override(species) -> None:
    """eta_initial_mpc is derived and cannot be passed as an override.
    (eta_final_mpc is not reserved — it is an explicit helper parameter.)"""
    with pytest.raises(ValueError, match="eta_initial_mpc.*derived"):
        build_cosmological_integrator_config(species, eta_initial_mpc=100.0)


def test_build_config_accepts_custom_eta_final(species) -> None:
    """eta_final_mpc can be reduced (e.g., to test on a shorter range)."""
    config = build_cosmological_integrator_config(
        species, eta_final_mpc=5000.0
    )
    assert config.eta_final_mpc == pytest.approx(5000.0, abs=1e-6)
    assert config.eta_initial_mpc < 5000.0


def test_build_config_rejects_eta_final_below_eta_initial(species) -> None:
    """Backwards interval is rejected."""
    with pytest.raises(ValueError, match="must exceed derived"):
        build_cosmological_integrator_config(
            species, eta_final_mpc=10.0  # eta_initial ~261 Mpc
        )
