"""Tests for TSC no-overclaim lint."""
from __future__ import annotations

from tsc.audit.no_overclaim import (
    build_no_overclaim_flags,
    lint_claim_text,
    lint_metadata,
    quarantine_reasons_from_flags,
)


def test_no_full_polarization_claim_detected():
    hits = lint_claim_text("TSC validates BB and full polarization solved by TSC.")
    assert "full_polarization" in hits


def test_no_bianchi_family_claim_detected():
    hits = lint_claim_text("Bianchi family identified by TSC in this artifact.")
    assert "bianchi_family" in hits


def test_no_source_implies_observable_claim_detected():
    hits = lint_claim_text("Source adequate therefore observable adequate.")
    assert "source_implies_observable" in hits


def test_metadata_lint_and_quarantine_reasons():
    flags = build_no_overclaim_flags(
        texts=("clean text",),
        metadata={"summary": "HTT evidence corrected by TSC"},
    )
    assert not flags["htt_evidence_correction"]
    quarantine = quarantine_reasons_from_flags(flags)
    assert "no_overclaim:htt_evidence_correction" in quarantine
    meta_hits = lint_metadata({"summary": "MIO truth certificate"})
    assert "mio_truth" in meta_hits
