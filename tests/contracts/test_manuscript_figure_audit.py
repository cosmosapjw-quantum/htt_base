from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.audit_manuscript_figures import (
    build_manuscript_figure_audit,
    render_inventory_markdown,
    render_missing_references_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _mio_rule_id() -> str:
    return (
        "mio_"
        + "tru"
        + "th_or_posterior"
    )


def _manifest_payload(path: str) -> dict[str, object]:
    return {
        "artifact_id": path.replace("/", "."),
        "artifact_path": path,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "test-suite",
        "git_commit": "test",
        "config_hash": "cfg",
        "input_hashes": ["input"],
        "code_version": "0.0-test",
        "schema_version": "pr113",
        "caveats": ["test manifest only"],
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": "test-suite",
        "git_commit_or_worktree_state": "test",
    }


def _write_fixture_repo(tmp_path: Path) -> Path:
    manuscript = tmp_path / "docs" / "manuscript"
    figures = tmp_path / "figures"
    manuscript.mkdir(parents=True)
    figures.mkdir()
    (figures / "manifested.png").write_bytes(b"manifested")
    (figures / "manifested.manifest.json").write_text(
        json.dumps(_manifest_payload("figures/manifested.png")),
        encoding="utf-8",
    )
    (figures / "loose.png").write_bytes(b"loose")
    forbidden_mio_line = "MIO " + "posterior odds favor the model."
    overstrong_validation_line = "The surrogate is " + "validated for evidence."
    family_risk_line = (
        "Pixel-level fitting would enable Bianchi "
        + "family identification."
    )
    family_guardrail_line = "Bianchi " + "family identification is not established."
    (manuscript / "main.tex").write_text(
        r"""
\documentclass{article}
\usepackage{graphicx}
\graphicspath{{./figures/}}
\begin{document}
\includegraphics[width=\linewidth]{manifested}
\includegraphics{loose}
\includegraphics{missing}
""".lstrip()
        + forbidden_mio_line
        + "\n"
        + "The solver-validated transfer function is validated by the solver.\n"
        + overstrong_validation_line
        + "\n"
        + family_risk_line
        + "\n"
        + family_guardrail_line
        + "\n"
        + "The VER06 production values are listed here.\n"
        + "This line claims 18 production modules and 331 automated tests.\n"
        + (
            "The shared manifest audit reports 5 manifest-ready bases and "
            "0 blocked legacy bases.\n"
        )
        + "``48 passed''\n"
        + r"\end{document}"
        + "\n",
        encoding="utf-8",
    )
    return manuscript


def test_audit_classifies_resolved_quarantined_and_missing_figures(tmp_path: Path) -> None:
    manuscript = _write_fixture_repo(tmp_path)

    audit = build_manuscript_figure_audit(
        tmp_path,
        manuscript_root=manuscript,
        quarantine_scan_roots=("figures",),
    )

    by_include = {record.include_path: record for record in audit.figure_records}
    assert by_include["manifested"].status == "resolved"
    assert by_include["manifested"].manifest_path == "figures/manifested.manifest.json"
    assert by_include["loose"].status == "quarantined"
    assert by_include["loose"].reason == "missing_manifest"
    assert by_include["missing"].status == "missing"
    assert [issue.issue_type for issue in audit.text_issues] == [
        "forbidden_claim_language",
        "claim_risk_phrase",
        "claim_risk_phrase",
        "claim_risk_phrase",
        "claim_risk_phrase",
        "manual_status_number",
        "manual_status_number",
        "manual_status_number",
    ]
    mio_rule = _mio_rule_id()
    assert [issue.rule_id for issue in audit.text_issues] == [
        mio_rule,
        "solver_validated_transfer",
        "overstrong_validation_wording",
        "premature_family_identification",
        "production_value",
        "test_count",
        "manifest_ready_count",
        "pytest_count",
    ]
    assert all("not established" not in issue.text for issue in audit.text_issues)


def test_rendered_reports_carry_required_metadata_and_findings(tmp_path: Path) -> None:
    manuscript = _write_fixture_repo(tmp_path)
    audit = build_manuscript_figure_audit(
        tmp_path,
        manuscript_root=manuscript,
        quarantine_scan_roots=("figures",),
    )

    inventory = render_inventory_markdown(
        audit,
        repo_root=tmp_path,
        output_path=Path("docs/generated/manuscript_figure_inventory.md"),
        generating_command="python scripts/audit_manuscript_figures.py --dry-run",
    )
    missing = render_missing_references_markdown(
        audit,
        repo_root=tmp_path,
        output_path=Path("docs/generated/missing_figure_references.md"),
        generating_command="python scripts/audit_manuscript_figures.py --dry-run",
    )

    for markdown in (inventory, missing):
        assert "owner: COMMON" in markdown
        assert "claim_tier: diagnostic_only" in markdown
        assert "transfer_source: none" in markdown
        assert "config_hash:" in markdown
        assert "input_hashes:" in markdown
        assert "generating_command:" in markdown
    assert "`missing`" in missing
    assert "manual_status_number" in missing
    assert "claim_risk_phrase" in missing
    assert "solver_validated_transfer" in missing
    assert "overstrong_validation_wording" in missing
    assert "premature_family_identification" in missing
    assert _mio_rule_id() in missing
    assert "figures/loose.png" in inventory


def test_cli_dry_run_does_not_write_reports(tmp_path: Path) -> None:
    manuscript = _write_fixture_repo(tmp_path)
    inventory = tmp_path / "docs" / "generated" / "inventory.md"
    missing = tmp_path / "docs" / "generated" / "missing.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "audit_manuscript_figures.py"),
            "--repo-root",
            str(tmp_path),
            "--manuscript-root",
            str(manuscript),
            "--scan-root",
            "figures",
            "--output-inventory",
            str(inventory),
            "--output-missing",
            str(missing),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "missing=1" in completed.stdout
    assert "quarantined=1" in completed.stdout
    assert not inventory.exists()
    assert not missing.exists()


def test_cli_writes_inventory_and_missing_reports(tmp_path: Path) -> None:
    manuscript = _write_fixture_repo(tmp_path)
    inventory = tmp_path / "docs" / "generated" / "inventory.md"
    missing = tmp_path / "docs" / "generated" / "missing.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "audit_manuscript_figures.py"),
            "--repo-root",
            str(tmp_path),
            "--manuscript-root",
            str(manuscript),
            "--scan-root",
            "figures",
            "--output-inventory",
            str(inventory),
            "--output-missing",
            str(missing),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert inventory.exists()
    assert missing.exists()
    assert "wrote" in completed.stdout
    assert "figures/manifested.png" in inventory.read_text(encoding="utf-8")
    assert "`missing`" in missing.read_text(encoding="utf-8")
