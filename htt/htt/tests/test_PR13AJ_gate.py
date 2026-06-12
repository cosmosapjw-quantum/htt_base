"""HTT-P0-AJ regression gate (INDEPENDENT_TRACKS_PLAN.md §2.3)."""
from __future__ import annotations

import pytest

from common.contracts import PreferredAxis as CommonPreferredAxis, SkySupport
from htt.PR13AJ_full_a2m_restoration import PreferredAxis, restore_full_a2m
from htt.zoa.axis_promotion import AxisPromotionRecord


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
        provenance_hash="1234567890abcdef",
    )
    base.update(overrides)
    return PreferredAxis(**base)


def _sky_support(**overrides) -> SkySupport:
    base = dict(
        selection_mode="mock_calibrated",
        sky_support_hash="sha256:" + "1" * 64,
        mask_hash="sha256:" + "2" * 64,
        mock_coverage_status="adequate",
        scan_volume_hash="sha256:" + "3" * 64,
        coordinate_frame="galactic",
        sky_fraction=0.75,
        completeness_status="mock_calibrated",
        pixelization="healpix",
        nside=8,
    )
    base.update(overrides)
    return SkySupport(**base)


def _promotion_record(axis: PreferredAxis, sky_support: SkySupport) -> AxisPromotionRecord:
    return AxisPromotionRecord(
        axis_provenance_hash=axis.provenance_hash,
        sky_support_hash=sky_support.sky_support_hash,
        mask_hash=sky_support.mask_hash,
        mock_coverage_status=sky_support.mock_coverage_status,
        mock_calibration_hash="sha256:" + "4" * 64,
        posterior_bundle_hash="sha256:" + "5" * 64,
        config_hash="sha256:" + "6" * 64,
        input_hashes=("sha256:" + "7" * 64,),
    )


def test_preferred_axis_gate_blocks_diagnostic():
    """Diagnostic axis (production_allowed=False) → RuntimeError before rotation."""
    axis = _diag_axis()
    with pytest.raises(RuntimeError, match="diagnostic_axis_cannot_rotate_a_2m"):
        restore_full_a2m(axis, a20_seed=complex(1.0, 0.0))


def test_preferred_axis_gate_allows_fiducial():
    """Fiducial axis passes the gate (rotation body is a stub — NotImplementedError)."""
    axis = _fiducial_axis()
    sky_support = _sky_support()
    with pytest.raises(NotImplementedError, match="gate"):
        restore_full_a2m(
            axis,
            a20_seed=complex(1.0, 0.0),
            sky_support=sky_support,
            promotion_record=_promotion_record(axis, sky_support),
        )


def test_preferred_axis_gate_rejects_fiducial_without_promotion_record():
    axis = _fiducial_axis()
    with pytest.raises(RuntimeError, match="sky_support_missing"):
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


def test_pr13aj_preferred_axis_is_common_contract_alias():
    assert PreferredAxis is CommonPreferredAxis
