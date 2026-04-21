from __future__ import annotations

from workspace.contracts.preliminary_results import (
    REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID,
    load_exported_artifact,
    load_exported_observable_vector,
    load_exported_tsc_overlay,
    load_preliminary_result_pack,
)


def test_pack_e_lists_representative_family_sweep_artifact() -> None:
    pack = load_preliminary_result_pack("E")
    assert REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID in pack.artifact_ids()
    assert pack.pack_id == "E"


def test_exported_observable_vector_reconstructs_common_contract() -> None:
    observable = load_exported_observable_vector()
    assert observable.manifest.owner == "BASS"
    assert observable.channels
    assert observable.ell_max >= 0


def test_exported_tsc_overlay_reconstructs_overlay_contract() -> None:
    overlay = load_exported_tsc_overlay()
    assert overlay.manifest.owner == "TSC"
    assert overlay.public_caveat_snippet
    assert overlay.channel_budgets


def test_family_sweep_artifact_envelope_keeps_claim_ceiling() -> None:
    envelope = load_exported_artifact(REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID)
    assert envelope.manifest.claim_tier == "conditional"
    assert "representative_tilted_runtime_blocked" in envelope.notes
