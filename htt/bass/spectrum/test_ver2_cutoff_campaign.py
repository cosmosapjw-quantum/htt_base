from __future__ import annotations

import numpy as np
import pytest

from bass.spectrum import (
    CutoffCampaignSpec,
    build_cutoff_campaign_stub,
    summarize_multipole_norms,
)


def test_cutoff_campaign_rejects_l2_without_override() -> None:
    with pytest.raises(ValueError, match="L=2"):
        CutoffCampaignSpec(cutoffs=(2, 4, 6), closure_name="explicit_unset")


def test_multipole_norm_summary_requires_finite_arrays() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        summarize_multipole_norms(
            4,
            channel_arrays={"TT": np.array([1.0, np.nan])},
            closure_name="explicit_unset",
        )


def test_cutoff_campaign_stub_records_all_requested_cutoffs() -> None:
    summaries = (
        summarize_multipole_norms(
            4,
            channel_arrays={"TT": np.array([1.0, 2.0])},
            closure_name="free_streaming",
        ),
        summarize_multipole_norms(
            6,
            channel_arrays={"TT": np.array([1.0, 2.0, 3.0])},
            closure_name="free_streaming",
        ),
        summarize_multipole_norms(
            8,
            channel_arrays={"TT": np.array([1.0, 2.0, 3.0, 4.0])},
            closure_name="free_streaming",
        ),
    )
    stub = build_cutoff_campaign_stub(
        CutoffCampaignSpec(cutoffs=(4, 6, 8), closure_name="free_streaming"),
        summaries,
    )
    assert stub.ready is False
    assert stub.all_cutoffs_recorded is True
