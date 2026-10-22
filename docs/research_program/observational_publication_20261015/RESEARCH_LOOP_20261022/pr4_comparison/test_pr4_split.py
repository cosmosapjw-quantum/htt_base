"""Narrow geometry and algebra falsifiers; no full-data replay."""

import importlib.util
from pathlib import Path

import healpy as hp
import numpy as np
import pytest


spec = importlib.util.spec_from_file_location("pr4_split", Path(__file__).with_name("pr4_split.py"))
split = importlib.util.module_from_spec(spec)
spec.loader.exec_module(split)


def test_ring_to_nested_mask_and_exact_lifting():
    nside = 2
    ring = np.zeros(hp.nside2npix(nside), dtype=np.float32)
    ring_indices = np.array([1, 7, 15, 29])
    ring[ring_indices] = 1
    nested = split.nest_mask_from_ring(ring, nside)
    expected = np.zeros_like(nested)
    expected[hp.ring2nest(nside, ring_indices)] = True
    assert np.array_equal(nested, expected)
    assert not np.array_equal(nested, ring.astype(bool))  # catches direct RING/NESTED use
    for parent in np.flatnonzero(nested):
        lo, hi = split.child_bounds(int(parent), nside, 8)
        children = np.arange(lo, hi)
        assert len(children) == 16
        assert np.array_equal(children // 16, np.full(16, parent))
    assert sum(split.child_bounds(int(p), nside, 8)[1]
               - split.child_bounds(int(p), nside, 8)[0]
               for p in np.flatnonzero(nested)) == 4 * 16


def test_split_parallelogram_cross_rotation_and_units():
    aq = np.array([1.2e-4, -3.0e-5, 4.5e-5, 0.0], dtype=np.float32)
    au = np.array([2.4e-5, 6.7e-5, -1.2e-5, 2e-6], dtype=np.float32)
    bq = np.array([-3.3e-5, 2.1e-5, 3.4e-5, -1e-6], dtype=np.float32)
    bu = np.array([4e-5, -8e-6, 2e-6, 3e-6], dtype=np.float32)
    x = split.split_chunk(aq, au, bq, bu)
    assert x["count"] == 4
    assert np.isclose(x["S2"] + x["D2"], (x["A2"] + x["B2"]) / 2, rtol=1e-14, atol=0.0)
    assert np.isclose(x["S2"] - x["D2"], x["AB"], rtol=1e-14, atol=1e-26)
    for key in ("S2", "D2", "A2", "B2", "AB"):
        assert split.check_identity(key, x[f"{key}_rot"], x[key])[
            "relative_with_1e-18_K2_scale_guard"] <= 1e-10
    assert x["D2"] * 1e12 == pytest.approx(x["D2"] / (1e-6 ** 2))
    assert split.positive_power_ratio(x["D2"], x["S2"]) > 0


def test_nonfinite_and_ratio_domain_fail_closed():
    with pytest.raises(ValueError, match="finite"):
        split.split_chunk([0, np.nan], [0, 0], [0, 0], [0, 0])
    for s2 in (0, -1, float("nan")):
        with pytest.raises(ArithmeticError, match="positive S"):
            split.positive_power_ratio(1, s2)
    with pytest.raises(ArithmeticError, match="relative"):
        split.check_identity("manufactured failure", 1e-8, 1.001e-8)


def test_native_geometry_counts():
    assert split.CHILDREN == 4096
    assert split.child_bounds(127, 16, 1024) == (127 * 4096, 128 * 4096)
    assert 1273 * split.CHILDREN == 5_214_208
