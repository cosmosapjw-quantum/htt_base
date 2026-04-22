from __future__ import annotations

from htt.integration import build_preliminary_directional_handoff


def test_preliminary_directional_handoff_loads_generated_bundle() -> None:
    handoff = build_preliminary_directional_handoff(required_channels=("TT",))
    assert handoff.pack_ids == ("A", "B", "D")
    assert handoff.likelihood_input.observable_vector.manifest.owner == "BASS"
    assert handoff.likelihood_input.atlas_entry is not None
    assert handoff.likelihood_input.tsc_caveats is not None
    assert handoff.likelihood_input.tsc_caveats.required_channels == ("TT",)
    assert handoff.discrimination_matrix.manifest.owner == "HTT"
