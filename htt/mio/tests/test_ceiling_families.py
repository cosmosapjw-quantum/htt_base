"""Tests for the quarantined legacy MIO ceiling-family registry."""
from __future__ import annotations

import pytest

from mio.core.ceiling_families import (
    CEILING_FAMILIES,
    CeilingStatus,
    blocked_families,
    certified_families,
    get_ceiling_family,
)


def test_registry_contains_expected_operational_families():
    assert {
        "irrotational_nonneg_orth",
        "irrotational_nonneg_tilt",
        "irrotational_neg",
        "blocked_momentum",
        "vortical",
    } <= set(CEILING_FAMILIES)


def test_certified_and_blocked_filters_are_disjoint():
    certified = certified_families()
    blocked = blocked_families()
    assert certified == {}
    assert blocked
    assert set(certified).isdisjoint(blocked)
    assert all(
        family.status
        in (
            CeilingStatus.BLOCKED,
            CeilingStatus.LEGACY_REPRODUCTION,
            CeilingStatus.NO_MES_ANCHOR,
        )
        for family in blocked.values()
    )


def test_lookup_rejects_unknown_family():
    with pytest.raises(KeyError, match="Unknown ceiling family"):
        get_ceiling_family("nope")
