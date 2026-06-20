from __future__ import annotations

import numpy as np
import pytest


def _sha(char: str = "a") -> str:
    return "sha256:" + char * 64


def test_observed_redshift_selection_requires_correction_metadata() -> None:
    from obsstat.catalogs.redshift_selection import RedshiftSelectionCorrectionSpec

    spec = RedshiftSelectionCorrectionSpec(
        z_bin_id="z0p8_1p2",
        selection_basis="observed_redshift",
        correction_status="not_bound",
        config_hash=_sha("1"),
        input_hashes=(_sha("2"),),
        generating_command="pytest redshift-selection",
        worktree_state="test",
    )
    payload = spec.to_metadata()

    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert payload["required_for_observed_redshift_bins"] is True
    assert payload["is_bound"] is False
    assert payload["config_hash"] == _sha("1")
    assert payload["input_hashes"] == [_sha("2")]
    assert payload["generating_command"] == "pytest redshift-selection"
    assert payload["git_commit_or_worktree_state"] == "test"
    assert "redshift_selection_correction_not_bound" in payload["blockers"]
    assert "von_hausegger_dalang_2025_prd111_123547" in payload["references"]


def test_bound_redshift_selection_correction_hook_is_metadata_only() -> None:
    from obsstat.catalogs.redshift_selection import (
        RedshiftSelectionCorrectionSpec,
        apply_redshift_selection_correction,
    )

    spec = RedshiftSelectionCorrectionSpec(
        z_bin_id="z0p8_1p2",
        selection_basis="observed_redshift",
        correction_status="toy_correction_bound",
        correction_vector=(0.01, -0.02, 0.0),
        config_hash=_sha("3"),
        input_hashes=(_sha("4"),),
        generating_command="pytest redshift-selection",
        worktree_state="test",
    )

    corrected = apply_redshift_selection_correction(np.asarray([0.2, 0.1, 0.0]), spec)

    assert np.allclose(corrected, np.asarray([0.19, 0.12, 0.0]))
    payload = spec.to_metadata()
    assert payload["is_bound"] is True
    assert payload["is_survey_bound"] is False
    assert payload["publication_ready"] is False
    assert payload["transfer_source"] == "none"
    assert payload["correction_vector"] == [0.01, -0.02, 0.0]
    assert "redshift_selection_correction_not_bound" in payload["blockers"]
    text = str(payload).lower()
    assert "evidence" not in text
    assert ("family " + "identified") not in text


def test_redshift_selection_rejects_bad_hashes_and_shapes() -> None:
    from obsstat.catalogs.redshift_selection import RedshiftSelectionCorrectionSpec

    with pytest.raises(ValueError, match="config_hash"):
        RedshiftSelectionCorrectionSpec(
            z_bin_id="z0p8_1p2",
            selection_basis="observed_redshift",
            correction_status="toy_correction_bound",
            config_hash="sha256:not-real",
            input_hashes=(_sha("5"),),
            generating_command="pytest redshift-selection",
            worktree_state="test",
        )
    with pytest.raises(ValueError, match="correction_vector"):
        RedshiftSelectionCorrectionSpec(
            z_bin_id="z0p8_1p2",
            selection_basis="observed_redshift",
            correction_status="toy_correction_bound",
            correction_vector=(0.0, 0.0),
            config_hash=_sha("6"),
            input_hashes=(_sha("7"),),
            generating_command="pytest redshift-selection",
            worktree_state="test",
        )
