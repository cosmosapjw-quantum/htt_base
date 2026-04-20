from __future__ import annotations

import numpy as np

from htt.infer.local_global_discrimination import (
    build_discrimination_matrix_stub,
    default_response_library,
)


def test_local_boost_and_global_tilt_are_not_merged():
    lib = default_response_library()
    assert lib["local_boost"].physical_side == "observer_side"
    assert lib["global_tilt"].physical_side == "source_background_side"
    assert lib["local_boost"].amplitude_normalization != lib["global_tilt"].amplitude_normalization
    assert "flrw_isotropic_null" in lib
    assert "bianchi_geometry" in lib
    assert "systematic_template" in lib


def test_discrimination_matrix_stub_is_manifest_backed_and_not_posterior():
    matrix = build_discrimination_matrix_stub()
    assert matrix.manifest.owner == "HTT"
    assert matrix.manifest.production_status == "diagnostic_only"
    assert matrix.hypotheses == ("local_boost", "global_tilt")
    overlap = np.asarray(matrix.overlap_matrix)
    assert overlap.shape == (2, 2)
    assert overlap[0, 0] == 1.0
    assert matrix.claim_tier_by_pair["local_boost|global_tilt"] == "exploratory"
