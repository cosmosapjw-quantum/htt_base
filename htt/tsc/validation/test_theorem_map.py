from __future__ import annotations

from tsc.validation.theorem_map import CORE_THEOREM_MAP


def test_theorem_map_covers_source_budget_and_export_claims():
    by_theorem = {entry.theorem: entry for entry in CORE_THEOREM_MAP}

    assert "T20_trace_source_adequacy" in by_theorem
    assert "T21_q_normalization_table_convention" in by_theorem
    assert "T30_tt_channel_conditional_adequacy" in by_theorem
    assert "T31_spin2_channels_require_external_validation" in by_theorem
    assert "T90_overlay_export_no_overclaim" in by_theorem
    assert "B4" in by_theorem["T21_q_normalization_table_convention"].tests
    assert "claim_ceiling" in by_theorem[
        "T31_spin2_channels_require_external_validation"
    ].metrics
