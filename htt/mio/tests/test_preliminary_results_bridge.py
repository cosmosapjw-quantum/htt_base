from __future__ import annotations

import dataclasses

from common.contracts import Owner
import mio.bridges as bridges
import mio.bridges.preliminary_results as preliminary_results
from mio.bridges.preliminary_results import build_preliminary_mio_handoff
from tsc.adapters.mio_certificate import overlay_to_mio_fields


def test_preliminary_mio_handoff_loads_certificate_and_overlay() -> None:
    handoff = build_preliminary_mio_handoff()
    expected_fields = overlay_to_mio_fields(handoff.overlay)
    expected_issues = preliminary_results._tsc_certificate_consistency_issues(
        handoff.certificate,
        expected_fields,
    )
    assert handoff.pack_id == "D"
    assert handoff.pack.pack_id == "D"
    assert handoff.topic == "mio_residual_atlas"
    assert handoff.claim_tier == "conditional"
    assert handoff.production_status == "production_candidate"
    assert handoff.certificate.manifest is not None
    assert handoff.certificate.manifest.owner == "MIO"
    assert handoff.overlay.manifest.owner is Owner.TSC_LEGACY
    assert (
        handoff.artifact_index[preliminary_results.TSC_OVERLAY_ARTIFACT_ID].owner
        == "TSC"
    )
    assert handoff.certificate.tsc_overlay_ref == handoff.overlay.manifest.artifact_id
    assert handoff.certificate.manifest.artifact_id in handoff.artifact_ids
    assert handoff.overlay.manifest.artifact_id in handoff.artifact_ids
    assert handoff.summary_lines
    assert "no_runtime_decision_ownership" in handoff.caveats
    assert handoff.tsc_required_channels == expected_fields.required_channels
    assert handoff.tsc_publication_blockers == expected_fields.publication_blockers
    assert handoff.tsc_claim_ceiling == expected_fields.channel_claim_ceiling
    assert handoff.tsc_trace_source_adequacy == expected_fields.trace_source_adequacy
    assert handoff.tsc_consistency_issues == expected_issues
    assert (
        handoff.artifact_claim_tiers[handoff.certificate.manifest.artifact_id]
        == handoff.certificate.manifest.claim_tier
    )
    assert (
        handoff.artifact_production_statuses[handoff.overlay.manifest.artifact_id]
        == handoff.overlay.manifest.production_status
    )
    assert handoff.artifact_summaries[handoff.overlay.manifest.artifact_id]


def test_preliminary_mio_handoff_loads_artifacts_by_pack_ref(monkeypatch) -> None:
    seen: dict[str, str] = {}
    original_cert = preliminary_results.load_exported_mio_certificate
    original_overlay = preliminary_results.load_exported_tsc_overlay

    def wrapped_cert(*, artifact_id_or_path=preliminary_results.MIO_CERTIFICATE_ARTIFACT_ID, generated_root=None):
        seen["certificate"] = str(artifact_id_or_path)
        return original_cert(
            artifact_id_or_path=artifact_id_or_path,
            generated_root=generated_root,
        )

    def wrapped_overlay(*, artifact_id_or_path=preliminary_results.TSC_OVERLAY_ARTIFACT_ID, generated_root=None):
        seen["overlay"] = str(artifact_id_or_path)
        return original_overlay(
            artifact_id_or_path=artifact_id_or_path,
            generated_root=generated_root,
        )

    monkeypatch.setattr(preliminary_results, "load_exported_mio_certificate", wrapped_cert)
    monkeypatch.setattr(preliminary_results, "load_exported_tsc_overlay", wrapped_overlay)

    handoff = preliminary_results.build_preliminary_mio_handoff()
    assert seen["certificate"] == handoff.certificate.manifest.artifact_id
    assert seen["overlay"] == handoff.overlay.manifest.artifact_id


def test_preliminary_mio_handoff_surfaces_tsc_blocker_mismatch(monkeypatch) -> None:
    original_cert = preliminary_results.load_exported_mio_certificate

    def wrapped_cert(*, artifact_id_or_path=preliminary_results.MIO_CERTIFICATE_ARTIFACT_ID, generated_root=None):
        cert = original_cert(
            artifact_id_or_path=artifact_id_or_path,
            generated_root=generated_root,
        )
        domain_caveats = [
            caveat
            for caveat in cert.domain_caveats
            if not caveat.startswith("tsc_publication_blocker=")
        ]
        return dataclasses.replace(cert, domain_caveats=domain_caveats)

    monkeypatch.setattr(preliminary_results, "load_exported_mio_certificate", wrapped_cert)

    handoff = preliminary_results.build_preliminary_mio_handoff()
    assert "tsc_publication_blockers_mismatch" in handoff.tsc_consistency_issues


def test_package_exports_preliminary_mio_handoff_entrypoint() -> None:
    assert bridges.build_preliminary_mio_handoff is build_preliminary_mio_handoff
    assert bridges.PreliminaryMioHandoff is preliminary_results.PreliminaryMioHandoff
    assert "build_preliminary_mio_handoff" in bridges.__all__
    assert "PreliminaryMioHandoff" in bridges.__all__
