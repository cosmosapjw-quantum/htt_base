from __future__ import annotations

from tsc.adapters import build_preliminary_tsc_handoff


def test_preliminary_tsc_handoff_exposes_overlay_and_downstream_views() -> None:
    handoff = build_preliminary_tsc_handoff()
    assert handoff.pack_ids == ("C", "D")
    assert tuple(handoff.pack_index) == ("C", "D")
    assert handoff.pack_claim_tiers["D"] == "conditional"
    assert handoff.pack_production_statuses["D"] == "production_candidate"
    assert handoff.pack_summary_lines["D"]
    assert handoff.pack_artifact_ids["D"]
    assert handoff.overlay.manifest.owner == "TSC"
    assert handoff.bass_suggestion.tsc_overlay_ref == handoff.overlay.manifest.artifact_id
    assert handoff.htt_caveats.tsc_overlay_ref == handoff.overlay.manifest.artifact_id
    assert handoff.bass_suggestion.recommended_label


def test_preliminary_tsc_handoff_can_narrow_required_channel_scope() -> None:
    handoff = build_preliminary_tsc_handoff(required_channels=("TT",))
    assert handoff.htt_caveats.required_channels == ("TT",)
