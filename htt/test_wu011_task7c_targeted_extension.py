"""RED/GREEN contract for the WU-011 Task-7C-R1 source-band extension."""

from __future__ import annotations

import pytest


pytest.importorskip("healpy", reason="healpy is required by WU-011 Task-7C-R1")
pytestmark = pytest.mark.requires_healpy


def test_task7c_r1_extends_only_the_primary_wide_n16_source_band() -> None:
    from obsstat import processed_boost_nuisance_span as api

    assert api.TARGETED_EXTENSION_CASE_IDS == ("WIDE_N16_IDENTITY_EXTENDED",)
    specs = api.task7c_case_specs("TARGETED_EXTENSION")
    assert len(specs) == 1
    spec = specs[0]
    assert spec.case_id == "WIDE_N16_IDENTITY_EXTENDED"
    assert spec.nside == 16
    assert spec.processing_lmax == 21
    assert spec.mask_kind == "APODIZED_Z_WIDE"
    assert spec.transfer_kind == "IDENTITY"
    assert spec.source_cutoffs == (12, 16, 20)
