"""Falsifiers for the source-bound one-sky PR4 observed pilot."""

from __future__ import annotations

import json
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.io import fits

import pr4_observed_pilot as pilot


def test_mask_native_parent_mapping_and_count():
    report, entries = pilot.source_entries()
    mask, meta, ring_to_nested = pilot.exact_native_mask(
        Path(entries["PR4_LOLLIPOP_NS16_MASK"]["path"]))
    assert report["qualification"] == "TRANSPORT_SCHEMA_PIXEL_ONLY"
    assert mask.sum() == 5_214_208
    assert meta["selected_coarse_pixels"] == 1273
    assert np.array_equal(hp.nest2ring(pilot.NSIDE, ring_to_nested[::10007]),
                          np.arange(len(ring_to_nested))[::10007])
    with fits.open(entries["PR4_LOLLIPOP_NS16_MASK"]["path"], memmap=True) as hdus:
        coarse_ring = np.asarray(hdus[1].data["T"]).reshape(-1)
    sample = np.arange(0, len(mask), 10007)
    parent_nested = ring_to_nested[sample] // 4096
    parent_ring = hp.nest2ring(16, parent_nested)
    np.testing.assert_array_equal(mask[sample], coarse_ring[parent_ring].astype(bool))


def test_saved_views_are_one_linear_coadd_and_scanned_once():
    result = json.loads((pilot.HERE / "RESULT.json").read_text())
    with np.load(result["lowell_alms"]["path"], allow_pickle=False) as data:
        assert set(data.files) == {f"{v}_{s}" for v in "ABC" for s in ("E", "B")}
        for spin in ("E", "B"):
            np.testing.assert_allclose(data[f"C_{spin}"],
                                       (data[f"A_{spin}"] + data[f"B_{spin}"]) / 2,
                                       rtol=0, atol=0)
        for view in "ABC":
            assert data[f"{view}_E"].shape == (hp.Alm.getsize(4),)
            assert np.isfinite(data[f"{view}_E"]).all()
    score = result["single_within_sky_scan"]
    assert score["independent_sky_count"] == 1
    assert score["T"] == max(score["abs_J234_by_view"].values())
    for view in "ABC":
        assert score["abs_J234_by_view"][view] == abs(result["features"][view]["J234"])
    assert result["processed_null_rank"] is None and result["processed_null_p"] is None


def test_broken_source_or_wrong_ordering_fails_before_feature_extraction(tmp_path):
    report, entries = pilot.source_entries()
    assert report["qualification"] != "SCIENTIFIC_NULL_QUALIFIED"
    # A deliberately wrong mask value must fail before the expensive harmonic step.
    original = Path(entries["PR4_LOLLIPOP_NS16_MASK"]["path"])
    target = tmp_path / "bad_mask.fits"
    with fits.open(original, memmap=False) as hdus:
        hdus[1].data["T"][0, 0] = 0.5
        hdus.writeto(target)
    import pytest
    with pytest.raises(ValueError, match="binary"):
        pilot.exact_native_mask(target)
