from __future__ import annotations

import numpy as np
import pytest

from bass.background import (
    build_all_family_branch_validation_matrix,
    build_family_branch_validation_report,
)
from bass.background.bianchi_types import ALL_BIANCHI_TYPES


@pytest.mark.parametrize("family", ["I", "V", "VII_h", "IX"])
@pytest.mark.parametrize("branch", ["orthogonal", "tilted"])
def test_family_branch_validation_report_is_covariant_and_branch_aware(
    family: str,
    branch: str,
) -> None:
    report = build_family_branch_validation_report(
        family,
        branch,
        truncation={"ell_max": 2, "mode_labels": ("m0",)},
    )
    assert report.family == family
    assert report.branch == branch
    assert report.local_boost_present is False
    assert report.global_tilt_present is (branch == "tilted")
    assert report.backend_release_status == "backend-operator-bound"
    assert report.metadata["orthogonal_global_tilt_local_boost_split"] == "frozen"
    assert report.metadata["global_tilt_contract"] == (
        "model_matter_frame_state"
        if branch == "tilted"
        else "orthogonal_branch_zero_global_tilt"
    )
    assert np.isfinite(report.residuals.gauss_over_H2_ref)
    assert np.isfinite(report.residuals.codazzi_over_H2_ref)
    assert np.isfinite(report.residuals.bianchi_over_H2_ref)


def test_all_bianchi_branch_validation_matrix_covers_11_families_with_tilt() -> None:
    matrix = build_all_family_branch_validation_matrix(
        truncation={"ell_max": 1, "mode_labels": ("m0",)},
    )
    assert len(matrix) == 2 * len(ALL_BIANCHI_TYPES)
    for family in ALL_BIANCHI_TYPES:
        orth = matrix[(family, "orthogonal")]
        tilt = matrix[(family, "tilted")]
        assert orth.global_tilt_present is False
        assert tilt.global_tilt_present is True
        assert orth.local_boost_present is False
        assert tilt.local_boost_present is False
        assert orth.hierarchy_size > 0
        assert tilt.hierarchy_size > 0


def test_covariant_validation_matrix_keeps_local_boost_out_of_background_and_backend() -> None:
    matrix = build_all_family_branch_validation_matrix(
        families=("II", "III", "IV", "VI_0", "VI_h", "VIII"),
        truncation={"ell_max": 1, "mode_labels": ("m0",)},
    )
    for report in matrix.values():
        assert report.local_boost_present is False
        assert report.metadata["local_boost_contract"] == (
            "observer_side_only_not_applied_in_background_or_backend"
        )
        assert report.residuals.metadata["local_boost_present"] is False
