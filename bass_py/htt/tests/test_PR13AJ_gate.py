"""HTT-P0-AJ regression gate (INDEPENDENT_TRACKS_PLAN.md §2.3)."""
from __future__ import annotations

import pytest

from htt.PR13AJ_full_a2m_restoration import PreferredAxis, restore_full_a2m


def _diag_axis(**overrides) -> PreferredAxis:
    base = dict(
        l_deg=264.0,
        b_deg=48.0,
        label="zoa20_diagnostic",
        source="zoa_masked",
        weight_mode="uniform_fallback",
        selection_mode="zoa_hard_cut",
        production_allowed=False,
    )
    base.update(overrides)
    return PreferredAxis(**base)


def _fiducial_axis(**overrides) -> PreferredAxis:
    base = dict(
        l_deg=264.0,
        b_deg=48.0,
        label="fiducial",
        source="fiducial_posterior",
        weight_mode="native_with_nuisance",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="cafe1234",
    )
    base.update(overrides)
    return PreferredAxis(**base)


def test_preferred_axis_gate_blocks_diagnostic():
    """Diagnostic axis (production_allowed=False) → RuntimeError before rotation."""
    axis = _diag_axis()
    with pytest.raises(RuntimeError, match="diagnostic-only"):
        restore_full_a2m(axis, a20_seed=complex(1.0, 0.0))


def test_preferred_axis_gate_allows_fiducial():
    """Fiducial axis passes the gate (rotation body is a stub — NotImplementedError)."""
    axis = _fiducial_axis()
    with pytest.raises(NotImplementedError, match="gate"):
        restore_full_a2m(axis, a20_seed=complex(1.0, 0.0))


def test_preferred_axis_is_frozen():
    """PreferredAxis is immutable."""
    axis = _diag_axis()
    with pytest.raises(Exception):  # FrozenInstanceError
        axis.production_allowed = True  # type: ignore[misc]


def test_preferred_axis_validates_source():
    with pytest.raises(ValueError, match="source"):
        _diag_axis(source="bogus")


def test_preferred_axis_validates_weight_mode():
    with pytest.raises(ValueError, match="weight_mode"):
        _diag_axis(weight_mode="bogus")


def test_preferred_axis_validates_selection_mode():
    with pytest.raises(ValueError, match="selection_mode"):
        _diag_axis(selection_mode="bogus")


def test_preferred_axis_default_production_allowed_is_false():
    """A bare axis construction defaults to diagnostic (production blocked)."""
    axis = PreferredAxis(
        l_deg=0.0,
        b_deg=0.0,
        label="seed",
        source="raw_diagnostic",
        weight_mode="native",
        selection_mode="none",
    )
    assert axis.production_allowed is False
