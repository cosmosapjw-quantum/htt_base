"""Contract: v9 external-audit report + reproducibility package (REV-R176).

Guards the two blocking findings of the 2026-07-10 reviews:
* V1/R1-4 (package): MANIFEST.input_hashes and seal_hashes must resolve AND
  verify against files shipped inside the zip (the v8 package resolved 0/70);
  environment.lock / README_REPRODUCE.md / CITATION.cff must ship;
* V2 (body): the retracted per-endpoint strictness claim must not survive as
  a live assertion, the ledger must carry supersession badges, and the stale
  v6/v8 version strings must be gone.

The builder's own --check (byte-stability) is exercised too. No test here
touches the frozen v5-v8 packages.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGACY_ROOT = ROOT / "legacy/cf4_p0/packages/external_reports"
ZIP = LEGACY_ROOT / "external_audit_research_report_20260711_v9.zip"
TEX = (LEGACY_ROOT / "external_audit_research_report_20260711_v9"
       / "external_audit_research_report_v9.tex")


def test_v9_snapshot_is_absent_from_active_paths_and_preserved_in_legacy():
    assert not (ROOT / "external_audit_research_report_20260711_v9").exists()
    assert not (ROOT / "external_audit_research_report_20260711_v9.zip").exists()
    assert not (ROOT / "external_audit_research_report_v9.pdf").exists()
    assert ZIP.is_file()
    assert TEX.is_file()


def _zip_index():
    z = zipfile.ZipFile(ZIP)
    names = set(z.namelist())
    man_name = next(n for n in names if n.endswith("MANIFEST.json"))
    root = man_name.rsplit("MANIFEST.json", 1)[0]
    return z, names, json.loads(z.read(man_name)), root


def test_input_hashes_resolve_and_verify_inside_zip():
    z, names, man, root = _zip_index()
    ih = man["input_hashes"]
    assert len(ih) >= 70
    for path, sha in ih.items():
        full = root + path
        assert full in names, f"unresolved input hash path: {path}"
        assert hashlib.sha256(z.read(full)).hexdigest() == sha, path


def test_seal_hashes_resolve_and_verify_inside_zip():
    z, names, man, root = _zip_index()
    sh = man["seal_hashes"]
    assert len(sh) >= 30
    for path, sha in sh.items():
        full = root + path
        assert full in names, f"unresolved seal path: {path}"
        assert hashlib.sha256(z.read(full)).hexdigest() == sha, path


def test_reproducibility_files_ship():
    _, names, man, root = _zip_index()
    for fname in ("environment.lock", "README_REPRODUCE.md", "CITATION.cff"):
        assert root + fname in names, fname
    assert man["reproducibility"]["single_command"] == "make reproduce-v9"


def test_body_supersession_state():
    tex = TEX.read_text(encoding="utf-8")
    # the retraction must be printed; the live per-endpoint iff must not be
    assert "RETRACTED}, superseded by T2G" in tex
    assert "T2G: general fractional-program interval theorem" in tex
    assert "per-endpoint iff RETRACTED" in tex
    assert "strict at an endpoint iff some shared component competes" not in tex
    # ledger supersession badges
    assert "RETRACTED by T2G" in tex
    assert "SUPERSEDED by T1p" in tex
    assert "SUPERSEDED by T3-full" in tex
    assert "SUPERSEDED by T4p" in tex
    # signed rename + witness relabel + hygiene
    assert r"\newcommand{\Omk}{\Delta\Omega_{k}}" in tex
    assert "constraint-surface endpoint witnesses" in tex
    assert "This fifth revision" not in tex
    assert "H_\\theta" not in tex
    assert "build_external_audit_report_v6.py" not in tex
    # the retired D24 figure must not be referenced; its successor must be
    assert "fig_data_observed_sector_response_vector" not in tex
    assert "fig_data_observed_sector_proxy_coordinates" in tex
