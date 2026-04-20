from __future__ import annotations

import pytest

from bass.hierarchy import TruncationMetadata, make_radiation_state


def test_truncation_metadata_rejects_hidden_l2_promotion() -> None:
    with pytest.raises(ValueError, match="L=2"):
        TruncationMetadata(L=2)


def test_make_radiation_state_records_explicit_override() -> None:
    state = make_radiation_state(
        2,
        diagnostic_only=True,
        closure_name="diagnostic_cutoff",
    )
    assert state.L == 2
    assert state.truncation.diagnostic_only is True
    assert state.truncation.closure_name == "diagnostic_cutoff"
    assert state.frame_metadata.transport_frame == "n_frame"


def test_make_radiation_state_builds_matching_towers() -> None:
    state = make_radiation_state(4, allow_L2_override=False, closure_name="explicit_unset")
    assert state.I.L == 4
    assert state.E.L == 4
    assert state.B.L == 4
