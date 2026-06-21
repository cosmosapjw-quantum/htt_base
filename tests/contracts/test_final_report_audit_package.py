from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_final_report_audit_package.py"
REPORT_TEX = REPO_ROOT / "docs/final_report/main.tex"

# Phrases that would lift the standing blocks if they leaked into the report.
FORBIDDEN_REPORT_SUBSTRINGS = (
    "decisive evidence",
    "decisively preferred",
    "decisively excluded",
    "production solver",
    "production pipeline",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("final_report_audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["final_report_audit_package"] = module
    spec.loader.exec_module(module)
    return module


def test_package_builds_and_passes_all_required_gates():
    module = _load_module()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_final_report_audit_package.py",
    )
    assert payload["failed_gates"] == []
    assert all(payload["required_assertions"].values())
    # The package must carry the report (both source and compiled PDF) and the
    # six manifest-backed figures.
    assert payload["required_assertions"]["report_tex_included"]
    assert payload["required_assertions"]["report_pdf_included"]
    assert payload["required_assertions"]["six_figures_present"]
    assert payload["required_assertions"]["all_figures_have_manifest"]
    assert len(entries) == payload["archive_entry_count"]


def test_manifest_keeps_family_id_and_native_solver_blocked():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_final_report_audit_package.py",
    )
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["family_identification"] is False
    assert payload["native_solver_result"] is False
    gates = payload["science_promotion_gates"]
    assert gates["family_identification_or_geometry_detection"] == "blocked"
    assert gates["model_ranking_or_posterior_odds"] == "forbidden"
    assert gates["native_low_ell_solver_validation"].startswith("fail")


def test_zip_is_deterministic():
    module = _load_module()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_final_report_audit_package.py",
    )
    first = module._build_zip_bytes(REPO_ROOT, payload, entries)
    second = module._build_zip_bytes(REPO_ROOT, payload, entries)
    assert first == second


def test_on_disk_package_is_up_to_date():
    # The committed zip/manifest/prompt must match a fresh build (run the script
    # without --check after editing the report or its inputs).
    module = _load_module()
    assert module.main(["--check"]) == 0


def test_report_source_has_no_forbidden_claim_language():
    text = REPORT_TEX.read_text(encoding="utf-8").lower()
    for phrase in FORBIDDEN_REPORT_SUBSTRINGS:
        assert phrase not in text, f"forbidden claim phrase in final report: {phrase!r}"
    # A bare "Bianchi family identification" is forbidden; the report must
    # instead carry explicit standing-block language for family-ID and geometry.
    assert "bianchi family identification" not in text
    assert "no identified bianchi family" in text
    assert "source-identification claim" in text


def test_report_pdf_passes_claim_lint():
    pytest.importorskip("subprocess")
    import subprocess

    pdf = REPO_ROOT / "docs/final_report/main.pdf"
    if not pdf.exists():
        pytest.skip("report PDF not built")
    out = REPO_ROOT / "docs/final_report/.claim_lint_check.md"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/pdf_claim_lint.py"),
            "--pdf",
            str(pdf),
            "--output",
            str(out),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and "pdftotext" in (result.stderr + result.stdout).lower():
        pytest.skip("pdftotext unavailable for claim lint")
    assert result.returncode == 0, result.stdout + result.stderr
    report = out.read_text(encoding="utf-8")
    out.unlink(missing_ok=True)
    assert "Failed findings: `0`" in report
