from __future__ import annotations

from tsc.validation.theorem_map import CORE_THEOREM_MAP, build_tsc_validation_witnesses


def test_theorem_map_covers_source_budget_and_export_claims():
    by_theorem = {entry.theorem: entry for entry in CORE_THEOREM_MAP}

    assert "T20_trace_source_adequacy" in by_theorem
    assert "T21_q_normalization_table_convention" in by_theorem
    assert "T22_source_bridge_convention_provenance" in by_theorem
    assert "T29_observable_bridge_requires_state_residual" in by_theorem
    assert "T30_tt_channel_conditional_adequacy" in by_theorem
    assert "T31_spin2_channels_require_external_validation" in by_theorem
    assert "T90_overlay_export_no_overclaim" in by_theorem
    assert "B4" in by_theorem["T21_q_normalization_table_convention"].tests
    assert "quadrupole_convention" in by_theorem[
        "T22_source_bridge_convention_provenance"
    ].metrics
    assert "observable_bound" in by_theorem[
        "T29_observable_bridge_requires_state_residual"
    ].metrics
    assert "claim_ceiling" in by_theorem[
        "T31_spin2_channels_require_external_validation"
    ].metrics
    assert "claim_ceiling" in by_theorem[
        "T90_overlay_export_no_overclaim"
    ].metrics


def test_tsc_validation_witnesses_track_live_theorem_ids_and_paths():
    theorem_ids = {entry.theorem for entry in CORE_THEOREM_MAP}
    witnesses = build_tsc_validation_witnesses()

    assert witnesses
    assert {witness.theorem for witness in witnesses} <= theorem_ids
    assert any(
        witness.theorem == "T29_observable_bridge_requires_state_residual"
        and witness.category == "adversarial_edge"
        for witness in witnesses
    )
    assert any(
        witness.theorem == "T90_overlay_export_no_overclaim"
        and witness.path.endswith(
            "::test_overlay_export_blocks_exploratory_claim_ceiling_even_when_propagation_validated"
        )
        for witness in witnesses
    )
