from __future__ import annotations

from scripts.audit_manuscript_figures import build_manuscript_figure_audit


def test_no_manual_status_numbers_remain():
    audit = build_manuscript_figure_audit(".", manuscript_root="docs/manuscript")
    manual = [issue for issue in audit.text_issues if issue.issue_type == "manual_status_number"]
    assert manual == []


def test_status_snippets_carry_source_hashes():
    for rel in [
        "docs/manuscript/generated/ver2_figure_manifest_status.tex",
        "docs/manuscript/generated/ver2_status_snapshot.tex",
        "docs/manuscript/generated/ver2_titlepage_status.tex",
    ]:
        text = open(rel, encoding="utf-8").read()
        assert "generated from" in text.lower()
        assert "sha256:" in text
