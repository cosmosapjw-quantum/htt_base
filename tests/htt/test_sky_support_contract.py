from __future__ import annotations

import math

import numpy as np
import pytest

from common.contracts import SkySupport
from common.sky_geometry import (
    assert_no_raw_lonlat_mean_source,
    spherical_mean,
)
from common.sky_support import (
    build_sky_support_from_mask,
    mask_hash_from_array,
    sky_fraction_from_mask,
    validate_sky_facing_artifact_metadata,
)


def test_mask_hash_is_deterministic_and_frame_annotated() -> None:
    mask = np.array([True, False, True, True])

    first = mask_hash_from_array(mask, coordinate_frame="galactic", pixelization="ring")
    second = mask_hash_from_array(mask, coordinate_frame="galactic", pixelization="ring")
    other_frame = mask_hash_from_array(
        mask,
        coordinate_frame="equatorial_icrs",
        pixelization="ring",
    )

    assert first == second
    assert first.startswith("sha256:")
    assert len(first) == len("sha256:") + 64
    assert other_frame != first


def test_sky_fraction_from_equal_area_mask() -> None:
    mask = np.array([True, False, True, True])

    assert math.isclose(sky_fraction_from_mask(mask), 0.75)

    with pytest.raises(ValueError, match="non-empty"):
        sky_fraction_from_mask(np.array([], dtype=bool))
    with pytest.raises(ValueError, match="1-D"):
        sky_fraction_from_mask(np.ones((2, 2), dtype=bool))


def test_build_sky_support_from_mask_records_required_fields() -> None:
    support = build_sky_support_from_mask(
        np.array([True, False, True, True]),
        coordinate_frame="galactic",
        completeness_status="partial_sky",
        selection_mode="zoa_hard_cut",
        mock_coverage_status="not_mocked",
        pixelization="equal_area_ring",
        nside=2,
        scan_volume_hash="scan-test",
    )

    assert isinstance(support, SkySupport)
    assert support.coordinate_frame == "galactic"
    assert support.sky_fraction == 0.75
    assert support.completeness_status == "partial_sky"
    assert support.mask_hash.startswith("sha256:")
    assert support.sky_support_hash.startswith("sha256:")
    assert support.scan_volume_hash == "scan-test"
    assert support.to_metadata()["coordinate_frame"] == "galactic"


def test_sky_facing_artifact_metadata_rejects_missing_support_fields() -> None:
    support = build_sky_support_from_mask(
        np.array([True, True, False, False]),
        coordinate_frame="galactic",
        completeness_status="partial_sky",
        selection_mode="zoa_hard_cut",
        mock_coverage_status="not_mocked",
        pixelization="equal_area_ring",
    )

    validate_sky_facing_artifact_metadata(
        {
            "artifact_id": "axis-summary",
            "sky_support_status": "directional",
            "sky_support": support.to_metadata(),
        }
    )

    with pytest.raises(ValueError, match="not_directional"):
        validate_sky_facing_artifact_metadata(
            {
                "artifact_id": "bad-axis",
                "sky_support_status": "not_directional",
                "sky_support": support.to_metadata(),
            }
        )

    incomplete = support.to_metadata()
    del incomplete["coordinate_frame"]
    with pytest.raises(ValueError, match="coordinate_frame"):
        validate_sky_facing_artifact_metadata(
            {
                "artifact_id": "bad-axis",
                "sky_support_status": "directional",
                "sky_support": incomplete,
            }
        )

    with pytest.raises(ValueError, match="sky_support_status"):
        validate_sky_facing_artifact_metadata(
            {
                "artifact_id": "bad-axis",
                "sky_support_status": "production_validated",
                "sky_support": support.to_metadata(),
            }
        )


def test_spherical_mean_reports_unit_vector_method_not_raw_angle_mean() -> None:
    l = np.array([359.0, 1.0])
    b = np.array([0.0, 0.0])

    result = spherical_mean(l, b)

    assert result["mean_method"] == "unit_vector_resultant"
    assert min(result["l_deg"], 360.0 - result["l_deg"]) < 1e-9
    assert abs(float(np.mean(l)) - 180.0) < 1.0


def test_spherical_mean_rejects_signed_directional_weights() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        spherical_mean(
            np.array([0.0, 180.0]),
            np.array([0.0, 0.0]),
            np.array([2.0, -1.0]),
        )


def test_spherical_mean_rejects_nonfinite_directional_weights() -> None:
    with pytest.raises(ValueError, match="finite"):
        spherical_mean(
            np.array([0.0, 180.0]),
            np.array([0.0, 0.0]),
            np.array([1.0, np.nan]),
        )


def test_raw_longitude_latitude_means_are_rejected_for_production_sources() -> None:
    bad_source = """
def summarize(l_deg, b_deg):
    return {"l": np.mean(l_deg), "b": b_deg.mean()}
"""
    good_source = """
from common.sky_geometry import spherical_mean

def summarize(l_deg, b_deg):
    return spherical_mean(l_deg, b_deg)
"""

    with pytest.raises(ValueError, match="raw longitude/latitude mean"):
        assert_no_raw_lonlat_mean_source(bad_source, path="summary.py")
    assert_no_raw_lonlat_mean_source(good_source, path="summary.py")
