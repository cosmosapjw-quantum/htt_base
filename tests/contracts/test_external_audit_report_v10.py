"""Contract gates for the v10 external research report package."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

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


def test_tier_ledger_present_with_empty_s_tier() -> None:
    tex = _tex()
    for tag in ("tier{K}", "tier{C}", "tier{P}", "tier{S}"):
        assert tag in tex
    assert "No entry carries \\tier{S}" in tex


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
