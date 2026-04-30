"""PA-1 progressive-closure tracker for the Python PSTF D_2 pipeline.

The strict-closure test in :mod:`test_d2_pstf_closure` is `xfail` until
PR-024c lands. That keeps the *target* visible but leaves a gap: an
optimization that *worsens* the current Python-side D_2 (e.g. by
silently re-routing the LoS quadrature) would not fail any test, since
the strict regression is already failing.

This module installs a **progressive-closure tracker** that:

1. measures the Python PSTF D_2 at a fixed config;
2. records its current ratio to the Rust anchor 1002.086744 μK² in a
   tiered closure ledger (bit / sub-percent / few-percent / order /
   far);
3. asserts the closure tier *does not regress* between commits.

When PR-024c closes the gap, the tracker advances tiers naturally and
the user is alerted when the closure improves — without ever faking it.

The tracker is :mod:`@pytest.mark.slow` and runs at the same config as
the strict-closure test so the two share the same physics surface.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from bass.spectrum.test_d2_pstf_closure import D2_ANCHOR_UK2


# Closure tiers ordered most-permissive → least-permissive.
# A tier is "open" if |D_2_python - D_2_anchor| / D_2_anchor < tier_max_rel.
@dataclass(frozen=True)
class ClosureTier:
    name: str
    max_rel_gap: float


CLOSURE_TIERS: tuple[ClosureTier, ...] = (
    ClosureTier("bit_identical", 1.0e-9),
    ClosureTier("sub_percent", 1.0e-2),
    ClosureTier("ten_percent", 1.0e-1),
    ClosureTier("order_of_magnitude", 1.0e1),
    ClosureTier("two_orders", 1.0e2),
    ClosureTier("six_orders", 1.0e6),
    ClosureTier("ten_orders", 1.0e10),
    ClosureTier("astronomical", float("inf")),
)


#: Last-known closure tier for the Python PSTF pipeline.
#:
#: 2026-04-29 baseline (post R17-P3): the Python pipeline currently
#: sits in the ``ten_orders`` tier (ratio ≈ 6.4 × 10^9; |Δ| ≈ +2.04e10
#: μK²) per CLAUDE.md §3 R17-P2 triangulation. Improving this tier is
#: the explicit Phase-1 closure goal (PR-024c). When the closure
#: shrinks the user must update this constant *down* — and the test
#: asserts the new value is at least as tight as the recorded one.
LAST_KNOWN_CLOSURE_TIER: str = "ten_orders"


def classify_closure(rel_gap: float) -> str:
    """Return the most-permissive tier whose ``max_rel_gap`` covers ``rel_gap``."""
    for tier in CLOSURE_TIERS:
        if abs(rel_gap) <= tier.max_rel_gap:
            return tier.name
    return CLOSURE_TIERS[-1].name


def tier_index(name: str) -> int:
    for i, tier in enumerate(CLOSURE_TIERS):
        if tier.name == name:
            return i
    raise KeyError(f"unknown closure tier {name!r}")


@pytest.fixture(scope="module")
def planck2018_species():
    try:
        from bass.species.registry import SpeciesBackgroundRegistry
    except ImportError:
        pytest.skip("bass.species.registry not importable")
    try:
        return SpeciesBackgroundRegistry.from_planck2018(
            recombination_warning_policy="ignore",
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"planck2018 species registry not buildable: {exc}")


def _measure_python_pstf_d2(planck2018_species) -> float:
    """Run the production-config Python PSTF pipeline and return ``D_2``."""
    try:
        from bass.spectrum.cl_assembly import CLAssemblyConfig
        from bass.spectrum.flrw_pipeline import (
            FLRWPipelineConfig,
            compute_flrw_d_ell,
        )
    except ImportError as exc:
        pytest.skip(f"flrw_pipeline not importable: {exc}")

    # Match the strict-closure config so the two regressions share
    # physics surface.
    k_grid = np.logspace(-4.0, -1.5, 65)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=8, ell_max_transfer=8)
    assembly_cfg = CLAssemblyConfig(ell_max=8, k_grid=k_grid, quadrature="simpson")
    bundle = compute_flrw_d_ell(
        planck2018_species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        assembly_config=assembly_cfg,
        n_workers=4,
    )
    return float(bundle["d_tt"][2])


def test_classify_closure_handles_known_tiers() -> None:
    """The tier classifier must be deterministic and ordered."""
    assert classify_closure(0.0) == "bit_identical"
    assert classify_closure(1.0e-3) == "sub_percent"
    assert classify_closure(1.0e-1) == "ten_percent"  # exactly at upper bound
    assert classify_closure(1.0e2) == "two_orders"
    assert classify_closure(1.0e10) == "ten_orders"


def test_last_known_tier_is_a_valid_label() -> None:
    """The recorded last-known tier must match a real tier name."""
    assert any(t.name == LAST_KNOWN_CLOSURE_TIER for t in CLOSURE_TIERS)


@pytest.mark.slow
def test_python_pstf_closure_does_not_regress(planck2018_species) -> None:
    """The current closure tier must be at least as tight as the last-known.

    "Tighter" means a smaller index in :data:`CLOSURE_TIERS` (lower
    numerical max_rel_gap). If a refactor *worsens* the gap, the
    measured tier index will exceed the last-known index and this test
    fails immediately — the user must investigate before committing.

    When the gap *improves*, this test passes and the user should
    promote :data:`LAST_KNOWN_CLOSURE_TIER` downward (to the new tier)
    as a single-line edit, locking the gain.
    """
    d2 = _measure_python_pstf_d2(planck2018_species)
    rel_gap = (d2 - D2_ANCHOR_UK2) / D2_ANCHOR_UK2
    measured = classify_closure(rel_gap)
    measured_idx = tier_index(measured)
    expected_idx = tier_index(LAST_KNOWN_CLOSURE_TIER)
    assert measured_idx <= expected_idx, (
        f"Python PSTF closure REGRESSED: measured tier "
        f"{measured!r} (rel_gap={rel_gap:.3e}, D_2={d2:.6e} μK²) is "
        f"looser than the last-known tier {LAST_KNOWN_CLOSURE_TIER!r}. "
        f"Investigate the regression *before* committing; do not loosen "
        f"this guard to make the test pass."
    )
    if measured_idx < expected_idx:
        pytest.fail(
            f"Python PSTF closure IMPROVED: measured tier {measured!r} is "
            f"tighter than the last-known tier {LAST_KNOWN_CLOSURE_TIER!r}. "
            f"Update LAST_KNOWN_CLOSURE_TIER to {measured!r} in the same "
            f"PR that produced the improvement, so future regressions are "
            f"caught at the new tier.",
            pytrace=False,
        )
