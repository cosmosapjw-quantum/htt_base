"""D_2 regression anchor tests (Python side).

Two anchor surfaces are enforced here:

1. ``ROUTE_B_C1`` / ``ROUTE_B_C2`` — frozen Michaelis–Menten constants.
2. ``route_b_d2_lookup`` — bit-identical at a set of pinned Σ² points.

The Rust-side FLRW-limit anchor ``D_2 = 1002.086744 μK²`` is enforced by
``bass_rs dump_dl_spectrum_sparse`` (MB-95 production path), not by this
test. It is recorded in ``_d2_anchor_golden.json`` for cross-reference only.
Drift in the Rust oracle must be caught by human review or the Rust test
suite, not by Python.

Markers: ``anchor`` (always on), ``ci`` (safe for every push).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bass.spectrum.cl_assembly import (
    ROUTE_B_C1,
    ROUTE_B_C2,
    ROUTE_B_D2_AT_SIGMA2_1EM8,
    route_b_d2_lookup,
)

_GOLDEN_PATH = Path(__file__).resolve().parent / "_d2_anchor_golden.json"
pytestmark = [pytest.mark.fast, pytest.mark.smoke]


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.mark.anchor
@pytest.mark.ci
def test_route_b_constants_frozen(golden: dict) -> None:
    expected = golden["python_side"]["route_b_constants"]
    assert ROUTE_B_C1 == expected["C1"], (
        f"ROUTE_B_C1 drifted: code={ROUTE_B_C1!r} vs golden={expected['C1']!r}. "
        "Update bass_rs/d2_convention.rs SSoT + golden JSON together via a "
        "v5-oracle-update PR if this is intentional."
    )
    assert ROUTE_B_C2 == expected["C2"], (
        f"ROUTE_B_C2 drifted: code={ROUTE_B_C2!r} vs golden={expected['C2']!r}."
    )


@pytest.mark.anchor
@pytest.mark.ci
def test_route_b_mm_curve_bit_identical(golden: dict) -> None:
    """Every pinned (Σ², D_2) pair must be bit-identical to route_b_d2_lookup."""
    for point in golden["python_side"]["mm_curve_points"]:
        sigma_sq = point["sigma_sq"]
        expected = point["D_2_uK2"]
        actual = route_b_d2_lookup(sigma_sq)
        assert actual == expected, (
            f"D_2 MM-curve anchor broken at Σ²={sigma_sq!r}: "
            f"route_b_d2_lookup={actual!r} vs golden={expected!r}."
        )


@pytest.mark.anchor
@pytest.mark.ci
def test_route_b_sentinel_constant_matches_curve() -> None:
    """Module-level ROUTE_B_D2_AT_SIGMA2_1EM8 must equal route_b_d2_lookup(1e-8)."""
    assert ROUTE_B_D2_AT_SIGMA2_1EM8 == route_b_d2_lookup(1.0e-8)


@pytest.mark.anchor
@pytest.mark.ci
def test_route_b_zero_at_origin() -> None:
    assert route_b_d2_lookup(0.0) == 0.0


@pytest.mark.anchor
@pytest.mark.ci
def test_route_b_negative_input_rejected() -> None:
    with pytest.raises(ValueError, match="sigma_sq must be"):
        route_b_d2_lookup(-1.0)


@pytest.mark.anchor
@pytest.mark.ci
def test_rust_flrw_reference_metadata_present(golden: dict) -> None:
    """Sanity: the golden JSON still documents the Rust-side FLRW anchor.

    We do not *compute* against it — the value comes from a Rust binary.
    But if the metadata block disappears, a human has silently removed the
    cross-reference and future drift would go unnoticed.
    """
    ref = golden["rust_side_reference"]
    assert ref["anchor_value_uK2"] == 1002.086744
    camb = ref["camb_cross_check"]
    assert "camb_d2_TT_tau0_unlensed_uK2" in camb
    assert abs(camb["delta_bass_vs_camb_tau0_percent"]) < 1.0, (
        "BASS vs CAMB(τ=0) delta must stay below 1% or the Rust oracle "
        "has drifted significantly; investigate before updating this test."
    )
