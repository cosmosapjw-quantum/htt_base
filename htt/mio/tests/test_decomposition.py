"""MIO-HJ-04 — evidence anatomy / redshift decomposition tests."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from mio.decomposition import (
    ARTEFACT_FILENAME,
    REDSHIFT_ARTEFACT_FILENAME,
    RedshiftEvidenceSlice,
    emit_evidence_anatomy_artefact,
    emit_redshift_tomography_artefact,
    summarize_evidence_anatomy,
    summarize_redshift_tomography,
    to_mio_certificate,
)
from mio.decomposition.redshift_tomography import (
    to_mio_certificate as redshift_to_mio_certificate,
)
from mio.tests._overlay_fixtures import build_pending_overlay
from workspace.contracts.mio_certificate import MioCertificate


def test_summarize_evidence_anatomy_reconstructs_total():
    report = summarize_evidence_anatomy(
        {"cmb": 1.2, "cf4": 0.8},
        total_delta_lnB=2.1,
    )
    assert report.reconstructed_delta_lnB == pytest.approx(2.0)
    assert report.residual_delta_lnB == pytest.approx(0.1)
    assert report.consistent_with_total


def test_evidence_anatomy_certificate_has_no_posterior_field():
    report = summarize_evidence_anatomy({"cmb": 1.2, "cf4": 0.8})
    cert = to_mio_certificate(report)
    assert isinstance(cert, MioCertificate)
    for field in dataclasses.fields(cert):
        assert "posterior" not in field.name.lower()
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


def test_emit_evidence_anatomy_artefact_round_trip(tmp_path: Path):
    out = tmp_path / ARTEFACT_FILENAME
    overlay = build_pending_overlay()
    payload = emit_evidence_anatomy_artefact(
        out,
        {"cmb": 1.2, "cf4": 0.8, "biposh": -0.1},
        total_delta_lnB=1.95,
        tsc_overlay=overlay,
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    assert payload["certificate"]["report_type"] == "evidence_anatomy"
    assert payload["certificate"]["tsc_overlay_ref"] == "tsc.overlay"


def test_emit_evidence_anatomy_rejects_non_mio_prefix(tmp_path: Path):
    with pytest.raises(ValueError, match="must start with 'mio_'"):
        emit_evidence_anatomy_artefact(tmp_path / "bad.json", {"cmb": 1.0})


def test_summarize_redshift_tomography_reconstructs_total():
    report = summarize_redshift_tomography(
        (
            RedshiftEvidenceSlice("recomb", 900.0, 1200.0, 1.5),
            RedshiftEvidenceSlice("late", 0.0, 10.0, 0.3),
        ),
        total_delta_lnB=1.9,
    )
    assert report.reconstructed_delta_lnB == pytest.approx(1.8)
    assert report.residual_delta_lnB == pytest.approx(0.1)
    assert report.consistent_with_total


def test_redshift_tomography_certificate_has_no_posterior_field():
    report = summarize_redshift_tomography(
        (
            RedshiftEvidenceSlice("recomb", 900.0, 1200.0, 1.5),
            RedshiftEvidenceSlice("late", 0.0, 10.0, 0.3),
        )
    )
    cert = redshift_to_mio_certificate(report)
    assert isinstance(cert, MioCertificate)
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


def test_emit_redshift_tomography_artefact_round_trip(tmp_path: Path):
    out = tmp_path / REDSHIFT_ARTEFACT_FILENAME
    overlay = build_pending_overlay()
    payload = emit_redshift_tomography_artefact(
        out,
        (
            RedshiftEvidenceSlice("recomb", 900.0, 1200.0, 1.5),
            RedshiftEvidenceSlice("late", 0.0, 10.0, 0.3),
        ),
        total_delta_lnB=1.9,
        tsc_overlay=overlay,
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    assert payload["certificate"]["channel"] == "redshift_tomography"
    assert payload["certificate"]["tsc_overlay_ref"] == "tsc.overlay"


def test_emit_redshift_tomography_rejects_non_mio_prefix(tmp_path: Path):
    with pytest.raises(ValueError, match="must start with 'mio_'"):
        emit_redshift_tomography_artefact(
            tmp_path / "bad_redshift.json",
            (RedshiftEvidenceSlice("late", 0.0, 10.0, 0.3),),
        )
