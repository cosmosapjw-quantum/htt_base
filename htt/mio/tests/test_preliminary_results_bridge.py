from __future__ import annotations

import mio.bridges.preliminary_results as preliminary_results
from mio.bridges.preliminary_results import build_preliminary_mio_handoff


def test_preliminary_mio_handoff_loads_certificate_and_overlay() -> None:
    handoff = build_preliminary_mio_handoff()
    assert handoff.pack_id == "D"
    assert handoff.topic == "mio_residual_atlas"
    assert handoff.claim_tier == "conditional"
    assert handoff.production_status == "production_candidate"
    assert handoff.certificate.manifest is not None
    assert handoff.certificate.manifest.owner == "MIO"
    assert handoff.overlay.manifest.owner == "TSC"
    assert handoff.certificate.tsc_overlay_ref == handoff.overlay.manifest.artifact_id
    assert handoff.certificate.manifest.artifact_id in handoff.artifact_ids
    assert handoff.overlay.manifest.artifact_id in handoff.artifact_ids
    assert handoff.summary_lines
    assert "no_runtime_decision_ownership" in handoff.caveats


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
