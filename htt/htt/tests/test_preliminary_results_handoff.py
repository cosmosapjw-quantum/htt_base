from __future__ import annotations

from htt.integration import build_preliminary_directional_handoff


def test_preliminary_directional_handoff_loads_generated_bundle() -> None:
    handoff = build_preliminary_directional_handoff(required_channels=("TT",))
    assert handoff.pack_ids == ("A", "B", "D")
    assert tuple(handoff.pack_index) == ("A", "B", "D")
    assert handoff.pack_claim_tiers["B"] == "conditional"
    assert handoff.pack_production_statuses["B"] == "production_candidate"
    assert handoff.pack_summary_lines["B"]
    assert handoff.likelihood_input.observable_vector.manifest.owner == "BASS"
    assert handoff.likelihood_input.atlas_entry is not None
    assert handoff.likelihood_input.tsc_caveats is not None
    assert handoff.likelihood_input.tsc_caveats.required_channels == ("TT",)
    assert handoff.discrimination_matrix.manifest.owner == "HTT"
    pair = "global_tilt|local_boost"
    assert handoff.pair_claim_tier[pair] == "conditional"
    assert pair in handoff.conditional_pairs
    assert handoff.blocked_pairs == ()
    assert handoff.pair_degeneracy_flags[pair] is False
    assert handoff.pair_recommended_next_observable[pair] in {
        "depth_direction_coherence",
        "atlas_template_biposh",
        "null_mock_covariance",
        "TE_EE_BB_morphology",
    }
    assert handoff.support_profile == {} or handoff.support_profile["template"] >= 0.75
