from __future__ import annotations

from common.contracts import Owner
from workspace.contracts.preliminary_results import (
    REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID,
    TSC_ACTIVE_SERVICE_BUNDLE_ARTIFACT_ID,
    TSC_POLICY_LEDGER_ARTIFACT_ID,
    load_exported_artifact,
    load_exported_tsc_active_service_bundle,
    load_exported_discrimination_matrix,
    load_exported_observable_vector,
    load_exported_tsc_overlay,
    load_exported_tsc_policy_ledger,
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


def test_exported_discrimination_matrix_recovers_pair_level_state() -> None:
    matrix = load_exported_discrimination_matrix()
    pair = "global_tilt|local_boost"
    assert matrix.manifest.owner == "HTT"
    assert matrix.claim_tier_by_pair[pair] == "conditional"
    assert matrix.degeneracy_flags[pair] is False
    assert matrix.recommended_next_observable[pair] in {
        "depth_direction_coherence",
        "atlas_template_biposh",
        "null_mock_covariance",
        "TE_EE_BB_morphology",
    }


def test_exported_tsc_overlay_reconstructs_overlay_contract() -> None:
    overlay = load_exported_tsc_overlay()
    assert overlay.manifest.owner is Owner.TSC_LEGACY
    assert overlay.public_caveat_snippet
    assert overlay.channel_budgets


def test_exported_tsc_active_service_bundle_recovers_policy_blockers() -> None:
    bundle = load_exported_tsc_active_service_bundle()
    assert bundle.manifest.artifact_id == TSC_ACTIVE_SERVICE_BUNDLE_ARTIFACT_ID
    assert bundle.overlay_ref == "tsc.ver2.export.overlay"
    assert bundle.overlay_artifact_id == "tsc.ver2.export.overlay"
    assert bundle.required_channels == ("TT", "TE", "EE")
    assert bundle.publication_blockers
    assert bundle.publication_blockers == bundle.htt_publication_blockers
    assert bundle.publication_blockers == bundle.mio_publication_blockers


def test_exported_tsc_policy_ledger_recovers_no_overclaim_surface() -> None:
    ledger = load_exported_tsc_policy_ledger()
    assert ledger.manifest.artifact_id == TSC_POLICY_LEDGER_ARTIFACT_ID
    assert ledger.overlay_ref == "tsc.ver2.export.overlay"
    assert ledger.overlay_artifact_id == "tsc.ver2.export.overlay"
    assert ledger.advisory_only is True
    assert ledger.required_channels == ("TT", "TE", "EE")
    assert ledger.publication_blockers
    assert "TT" in ledger.claim_limited_channels
    assert ledger.channel_claim_ceiling["TT"] == "exploratory"


def test_family_sweep_artifact_envelope_keeps_claim_ceiling() -> None:
    envelope = load_exported_artifact(REPRESENTATIVE_FAMILY_SWEEP_ARTIFACT_ID)
    assert envelope.manifest.claim_tier == "conditional"
    assert "representative_tilted_runtime_partial_only" in envelope.notes
