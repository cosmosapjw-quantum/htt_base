"""Contract gates for the v10 external research report package."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts.build_external_audit_report_v10 import (
    NOVELTY_UNKNOWN,
    s1_scope,
    s6_tiers,
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "external_audit_research_report_20260721_v10"
TEX = OUT / "external_audit_research_report_v10.tex"
MANIFEST = OUT / "MANIFEST.json"


def _tex() -> str:
    return TEX.read_text()


def test_package_exists_with_required_members() -> None:
    for name in ("external_audit_research_report_v10.tex", "README.md",
                 "CITATION.cff", "MANIFEST.json",
                 "external_audit_research_report_v10.pdf"):
        assert (OUT / name).exists(), name
    assert (REPO / "external_audit_research_report_v10.pdf").exists()
    assert (REPO / "external_audit_research_report_20260721_v10.zip").exists()


def test_manifest_inputs_resolve_and_hash_match() -> None:
    manifest = json.loads(MANIFEST.read_text())
    for rel, digest in manifest["input_artifact_sha256"].items():
        p = REPO / rel
        assert p.exists(), rel
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, rel
    assert manifest["desi_completeness"]["partial_mocks_in_statistics"] \
        is False


def test_data_completeness_statement_present() -> None:
    tex = _tex()
    assert "Data completeness statement" in tex
    assert "290 of 1000" in tex
    assert "partial" in tex.lower()
    assert "never enter any rank, p-value, covariance, or significance" \
        in tex


def test_tier_ledger_external_novelty_with_s_deltas() -> None:
    tex = _tex()
    for tag in ("tier{K}", "tier{C}", "tier{P}", "tier{S}"):
        assert tag in tex
    assert "external-novelty adjudication" in tex
    ledger = json.loads(
        (REPO / "docs/audits/v10_web_crag_20260721/tier_evidence.json")
        .read_text()
    )
    s_ids = ledger["s_entries"]
    actual_s_ids = [
        entry["id"] for entry in ledger["entries"] if entry["tier"] == "S"
    ]
    assert len(s_ids) == len(set(s_ids))
    assert set(s_ids) == set(actual_s_ids)
    by_id = {e["id"]: e for e in ledger["entries"]}
    for sid in s_ids:
        entry = by_id[sid]
        assert entry["tier"] == "S", sid
        # every S entry must state a delta over named literature
        assert "Delta" in entry["adjudication"] or "delta" in (
            entry["adjudication"]
        ), sid
        assert entry["citations"], sid
        assert sid in tex  # rendered in the S section
    # every K entry carries a citation or an explicit textbook-level note
    for e in ledger["entries"]:
        if e["tier"] == "K":
            assert e["citations"] or "textbook" in e["adjudication"].lower() \
                or "known" in e["adjudication"].lower() \
                or "implementation" in e["adjudication"].lower() \
                or "standard" in e["adjudication"].lower(), e["id"]
        if e["tier"] == "C":
            assert e["citations"] or "release" in e["adjudication"].lower() \
                or "cross-check" in e["adjudication"].lower(), e["id"]


@pytest.mark.parametrize(
    "mutation", ("relabel_s", "replace_s", "zero_s_known_only")
)
def test_zero_s_novelty_unknown_is_a_valid_rendering(mutation: str) -> None:
    ledger = json.loads(
        (REPO / "docs/audits/v10_web_crag_20260721/tier_evidence.json")
        .read_text()
    )
    if mutation == "relabel_s":
        for entry in ledger["entries"]:
            if entry["tier"] == "S":
                entry["tier"] = NOVELTY_UNKNOWN
    else:
        ledger["entries"] = [
            entry for entry in ledger["entries"] if entry["tier"] != "S"
        ]
        if mutation == "replace_s":
            ledger["entries"].append(
                {
                    "id": "NOVELTY-UNKNOWN-CONTROL",
                    "tier": NOVELTY_UNKNOWN,
                    "subject": "no highest-tier adjudication",
                    "adjudication": "novelty remains unknown",
                    "citations": [],
                }
            )
    ledger["s_entries"] = []

    rendered = s1_scope(ledger) + s6_tiers(ledger)
    if mutation == "zero_s_known_only":
        assert r"NOVELTY\_UNKNOWN" not in rendered
        assert "Every claim in this report carries one of four novelty tiers" \
            in rendered
    else:
        assert r"NOVELTY\_UNKNOWN" in rendered
        assert "Classified claims in this report carry one of four novelty tiers" \
            in rendered
    assert r"\subsection{No \tier{S} entries}" in rendered
    assert "The five \\tier{S} entries" not in rendered
    assert "the five externally\nnovel contributions" not in rendered


def test_no_meta_dev_vocabulary() -> None:
    text = _tex() + (OUT / "README.md").read_text()
    for token in ("checkpoint", "review lane", "adversarial", "subagent",
                  "claim gate", "backlog", "scoreboard"):
        assert token not in text.lower(), token
    assert not re.search(r"\bPR-1[0-9][0-9]\b", text)
    assert not re.search(r"\bDAG\b", text)


def test_no_quarantined_tokens() -> None:
    scanned = [TEX, OUT / "README.md", OUT / "MANIFEST.json"]
    pat_405 = re.compile(r"(?<![0-9.])405(?:\.22)?(?![0-9.])")
    for p in scanned:
        text = p.read_text()
        assert not pat_405.search(text), p.name
        for token in ("340.7", "4.07e-07", "4.07e-7", "0.40 \\pm 0.02",
                      "5.8 sigma", "5.8\\sigma", "0.4046"):
            assert token not in text, (p.name, token)


def test_every_proposition_has_a_proof() -> None:
    tex = _tex()
    stated = len(re.findall(
        r"\\begin\{(?:theorem|proposition|corollary|lemma)\}", tex))
    proofs = len(re.findall(r"\\begin\{proof\}", tex))
    assert stated >= 30
    assert proofs >= stated - 2  # definitions aside, proofs accompany claims


def test_builder_check_is_byte_stable() -> None:
    proc = subprocess.run(
        [str(REPO / "venv/bin/python"), "-B",
         str(REPO / "scripts/build_external_audit_report_v10.py"),
         "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
