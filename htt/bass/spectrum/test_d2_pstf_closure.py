"""Audit P-01: Python-side D_2 = 1002.086744 μK² PSTF closure regression.

Per ``htt/bass/validation/test_d2_regression_anchor.py:8-9``, the
``D_2 = 1002.086744 μK²`` anchor is currently *enforced* by the
Rust-side ``bass_rs dump_dl_spectrum_sparse`` (MB-95 production path).
On the Python (PSTF primary) side the anchor is a *target* tracked by
PR-024c (LoS + spectrum assembly). This regression executes the full
PSTF pipeline (``compute_flrw_d_ell``) and asserts bit-equality
against the anchor; until PR-024c lands the test is marked
``xfail("PR-024c open")`` so the gap stays *visible* in CI rather than
hidden in CHANGELOG bullets.

When PR-024c closes:
  1. The ``xfail`` marker becomes ``xpass`` and pytest will flag it.
  2. Promote the test to a strict regression by removing the marker.
  3. Update CLAUDE.md §5 to drop the "Python-side target" caveat.
"""
from __future__ import annotations

import numpy as np
import pytest

D2_ANCHOR_UK2 = 1002.086744
"""Route-B FLRW anchor enforced by the Rust path; PR-024c target."""

D2_PYTHON_TOLERANCE_UK2 = 1.0e-6
"""Bit-identical tolerance: 1e-9 fractional, ~1e-6 μK² absolute."""


@pytest.fixture(scope="module")
def planck2018_species():
    try:
        from bass.species.registry import SpeciesBackgroundRegistry
    except ImportError:  # pragma: no cover - guard for partial installs
        pytest.skip("bass.species.registry not importable in unit-test scope")
    try:
        return SpeciesBackgroundRegistry.from_planck2018(
            recombination_warning_policy="ignore",
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"planck2018 species registry not buildable: {exc}")


@pytest.mark.slow
@pytest.mark.xfail(
    reason="PR-024c open: PSTF Python-side D_2 = 1002.086744 μK² closure "
    "is the Phase-1 target; Rust MB-95 anchor is currently the only "
    "path that produces this number bit-identically.",
    strict=False,
)
def test_python_pstf_d2_matches_route_b_anchor(planck2018_species) -> None:
    """Full PSTF FLRW pipeline must reproduce ``D_2 = 1002.086744 μK²``.

    This is *the* Phase-1 closure assertion. Until PR-024c
    (LoS + spectrum assembly) lands, the integrator's seed amplitude is
    ``max(|Σ_±|, 1e-6)`` (not P(k)-normalized) and the LoS projection
    grid is independent of the IMEX η-grid only since Round-15 P0; so
    the absolute D_2 is expected to drift from the Route-B anchor by a
    primordial-amplitude factor. The xfail marker keeps the gap
    visible.
    """
    try:
        from bass.spectrum.cl_assembly import CLAssemblyConfig
        from bass.spectrum.flrw_pipeline import (
            FLRWPipelineConfig,
            compute_flrw_d_ell,
        )
    except ImportError as exc:  # pragma: no cover - guard for refactor
        pytest.skip(f"flrw_pipeline not importable: {exc}")

    # Use a moderate k-grid; the pipeline parallelizes per-k so this is
    # a few minutes on the 8-worker baseline (matches the existing slow
    # test budget). k_grid length is odd so Simpson quadrature accepts it.
    # L_max_tower must be >= ell_max_transfer (FLRWPipelineConfig __post_init__).
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
    d_tt = bundle["d_tt"]
    d2 = float(d_tt[2])
    np.testing.assert_allclose(
        d2, D2_ANCHOR_UK2,
        atol=D2_PYTHON_TOLERANCE_UK2,
        err_msg=(
            f"Python PSTF pipeline produced D_2 = {d2:.6f} μK² but the "
            f"Route-B anchor is {D2_ANCHOR_UK2:.6f} μK². When this test "
            f"flips to xpass, PR-024c is closed and the xfail marker "
            f"should be removed."
        ),
    )


def test_d2_anchor_constant_does_not_drift() -> None:
    """The anchor literal must not drift silently between commits.

    ``htt/bass/validation/test_d2_regression_anchor.py`` carries the
    same value; this is an internal-consistency cross-check.
    """
    assert D2_ANCHOR_UK2 == 1002.086744
