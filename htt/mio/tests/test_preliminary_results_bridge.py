from __future__ import annotations

from mio.bridges.preliminary_results import build_preliminary_mio_handoff


def test_preliminary_mio_handoff_loads_certificate_and_overlay() -> None:
    handoff = build_preliminary_mio_handoff()
    assert handoff.pack_id == "D"
    assert handoff.certificate.manifest is not None
    assert handoff.certificate.manifest.owner == "MIO"
    assert handoff.overlay.manifest.owner == "TSC"
    assert handoff.certificate.tsc_overlay_ref == handoff.overlay.manifest.artifact_id

