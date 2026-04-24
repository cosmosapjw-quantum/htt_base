"""BASS spectrum and convergence-campaign surfaces.

The end-to-end FLRW D_ℓ pipeline (``flrw_pipeline`` submodule) is NOT
re-exported here because it transitively imports
``bass.los.ver2_source_propagator`` which itself imports
``bass.spectrum.lowell_los``; folding the pipeline into this
``__init__`` creates a circular-import path through the partially
initialized spectrum package. Callers reach it explicitly via::

    from bass.spectrum.flrw_pipeline import (
        compute_flrw_d_ell, compute_transfer_function_at_k, ...
    )
"""

from bass.spectrum.tier_b_source_extraction import (
    extract_flrw_sources_from_tier_b,
)
from bass.spectrum.ver2_cutoff_campaign import (
    CutoffCampaignSpec,
    CutoffChannelDelta,
    CutoffCampaignStub,
    ExecutedCutoffCampaign,
    MultipoleNormSummary,
    build_cutoff_campaign_stub,
    run_executed_cutoff_campaign,
    summarize_multipole_norms,
)

__all__ = [
    "MultipoleNormSummary",
    "CutoffCampaignSpec",
    "CutoffChannelDelta",
    "CutoffCampaignStub",
    "ExecutedCutoffCampaign",
    "summarize_multipole_norms",
    "build_cutoff_campaign_stub",
    "run_executed_cutoff_campaign",
    "extract_flrw_sources_from_tier_b",
]
