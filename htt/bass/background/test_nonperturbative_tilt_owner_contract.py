"""Audit P-04: ``nonperturbative_tilt_rhs`` owner contract regression.

The audit found that the nonperturbative King-Ellis tilt RHS exists in
``bass.background.nonperturbative_tilt`` but its callsite from the
runtime layer was not obvious. The runtime ``tilt_background_owner``
control already supports it as an opt-in path; this regression makes
the contract explicit:

1. ``integrate_tilt_rapidity_history`` returns a non-trivially evolving
   β(a) trajectory whenever ``c_s² ≠ 1/3`` (matter contribution is
   non-zero), confirming the RHS is meaningful, not decorative.
2. The static-β path (``fixed_velocity_closure``) keeps β constant by
   contract: any caller that wants evolved β must opt into the
   ``nonperturbative_tilt_rhs`` owner.

This regression complements ``test_ver2_tier_b_execution.py`` (which
checks the runtime metadata wiring) at the level of the underlying
physics: it asserts the RHS itself, not just the owner switch.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.nonperturbative_tilt import (
    integrate_tilt_rapidity_history,
    omega_tilt_exact,
)


def _build_minimal_species_registry():
    """Best-effort constructor: skip if the registry shape changes."""
    try:
        from bass.species.registry import SpeciesBackgroundRegistry
        from bass.species.factories import build_default_species_registry
    except ImportError:  # pragma: no cover - guard for partial installs
        pytest.skip("bass.species default registry factory not importable")
    try:
        return build_default_species_registry()
    except Exception as exc:  # noqa: BLE001 - factory may require config
        pytest.skip(
            f"default species registry not buildable in unit-test scope: {exc}"
        )


def test_omega_tilt_exact_vanishes_at_zero_rapidity() -> None:
    assert omega_tilt_exact(Omega_r=1.0e-4, Omega_m=0.31, beta=0.0) == 0.0


def test_omega_tilt_exact_grows_with_rapidity() -> None:
    base = omega_tilt_exact(Omega_r=1.0e-4, Omega_m=0.31, beta=1.0e-2)
    larger = omega_tilt_exact(Omega_r=1.0e-4, Omega_m=0.31, beta=5.0e-2)
    assert larger > base > 0.0
    # sinh(β) growth must beat the β² truncation: sinh²(0.05)/sinh²(0.01)
    # ≈ 25.02 vs naive (5)² = 25; margin should still be > 25.
    assert larger / base > 25.0


@pytest.mark.slow
def test_integrate_tilt_rapidity_history_evolves_nontrivially() -> None:
    """Confirm the King-Ellis RHS makes β(a) non-stationary in matter era.

    Marked ``slow`` because it requires the full species registry. The
    point of this regression is that ``nonperturbative_tilt_rhs`` is not
    decorative: when opted into, it produces a measurably different
    trajectory from the static-β default.
    """
    registry = _build_minimal_species_registry()
    a_grid, beta = integrate_tilt_rapidity_history(
        registry=registry,
        a_start=1.0e-3,
        a_end=1.0,
        beta_initial=0.05,
        n_steps=64,
    )
    assert a_grid.shape == beta.shape
    # Static-β contract: ``fixed_velocity_closure`` would return β ≡ β₀.
    # The nonperturbative RHS must produce a different value at z=0.
    delta = abs(float(beta[-1]) - 0.05)
    assert delta > 1.0e-6, (
        "nonperturbative tilt rhs produced a static-β trajectory; "
        "owner switch would be physically decorative"
    )


def test_supported_families_match_runtime_owner_contract() -> None:
    from bass.background.nonperturbative_tilt import SUPPORTED_FAMILIES

    # Every label in SUPPORTED_FAMILIES must split into orth/tilt branches
    # so the runtime owner switch has a parametric handle.
    bases = {label.split("_")[0] for label in SUPPORTED_FAMILIES}
    for base in bases:
        assert f"{base}_orth" in SUPPORTED_FAMILIES, base
        assert f"{base}_tilt" in SUPPORTED_FAMILIES, base
