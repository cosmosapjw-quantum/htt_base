"""Contract: the root research-evaluation package is deterministic, self-contained,
and research-content-complete (report + code + tests + result records + prompt),
content-addressed (no git-state churn), and claim-gated.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/build_research_evaluation_package.py"


def _load():
    spec = importlib.util.spec_from_file_location("build_research_evaluation_package", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_research_evaluation_package"] = mod
    spec.loader.exec_module(mod)
    return mod


def _payload():
    mod = _load()
    payload, entries = mod.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_research_evaluation_package.py",
    )
    return mod, payload, entries


def test_build_types_historical_report_and_uses_current_block_as_authority():
    _mod, payload, entries = _payload()
    assert payload["failed_gates"] == []
    report = payload["cf4_p0_quarantine"]
    assert report["ok"] is True
    assert report["issues"] == []
    a = payload["required_assertions"]
    assert a["legacy_report_pdf_included"]
    assert a["legacy_report_tex_included"]
    assert a["legacy_report_manifest_included"]
    assert a["legacy_report_non_public"]
    assert a["current_quarantine_controls_included"]
    assert a["research_code_present"] and a["gate_tests_present"] and a["result_records_present"]
    assert a["joint_artifact_included"] and a["results_table_included"] and a["blockers_included"]
    assert a["review_prompt_included"]
    assert len(entries) == payload["archive_entry_count"]
    legacy_rows = [row for row in payload["archive_entries"] if row["group"] == "legacy_report"]
    assert legacy_rows
    assert all(row["content_mode"] == "immutable_historical_evidence" for row in legacy_rows)
    assert all(row["public_use"] is False for row in legacy_rows)
    binary_rows = [
        row
        for row in payload["archive_entries"]
        if row["source_path"].lower().endswith((".png", ".pdf", ".zip"))
    ]
    assert binary_rows
    assert all(
        row.get("binary_binding", {}).get("sha256") == row["sha256"]
        for row in binary_rows
    )
    assert payload["legacy_report_binding"]["public_use"] is False
    controls = [
        row
        for row in payload["archive_entries"]
        if row["source_path"] in _mod.CURRENT_QUARANTINE_CONTROLS
    ]
    assert controls
    assert all(row["content_mode"] == "active_public" for row in controls)
    assert all(row["public_use"] is True for row in controls)


def test_reproducibility_refs_are_bundled_self_contained():
    # external-audit pr08_reassessment: the report's Reproducibility section cited
    # commands/records that were NOT shipped in the package. They must now all be
    # present under the research_evaluation/ subtree so check_report_references passes.
    _mod, payload, _entries = _payload()
    assert payload["required_assertions"]["reproducibility_refs_present"]
    archive_paths = {r["archive_path"] for r in payload["archive_entries"]}
    referenced = [
        "scripts/prove_egs_lowell_theorems.py",
        "scripts/make_egs_lowell_theorem_figures.py",
        "scripts/make_pr04_paper_figures.py",
        "scripts/make_lowell_morphology_real_map.py",
        "scripts/make_cf4_bulkflow_apex_depth.py",
        "scripts/make_cf4_bulkflow_likelihood.py",
        "scripts/make_cf4_affine_flow.py",
        "scripts/generate_transfer_sensitivity_report.py",
        "scripts/run_pr07_experiments.py",
        "scripts/cove_verify_pr07.py",
        "docs/generated/egs_lowell_theorem_proofs.json",
        "docs/generated/pr04_paper_theorem_proofs.json",
    ]
    for rel in referenced:
        assert f"research_evaluation/{rel}" in archive_paths, rel
    # the research_gates/pr04/tests directory is represented by its files
    assert any(p.startswith("research_evaluation/research_gates/pr04/tests/") for p in archive_paths)


def test_claim_firewall_and_content_addressed():
    _mod, payload, _entries = _payload()
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["family_identification"] is False
    assert payload["native_solver_result"] is False
    # content-addressed provenance -> no HEAD churn across commits
    assert payload["git_commit_or_worktree_state"] == "content-addressed"
    assert payload["config_hash"].startswith("sha256:")


def test_pre_quarantine_package_snapshot_is_preserved_in_legacy_only():
    legacy_root = REPO_ROOT / "legacy/cf4_p0/packages/research_evaluation"
    assert (legacy_root / "htt_base_research_evaluation_package.zip").is_file()
    assert (legacy_root / "htt_base_research_evaluation_package_manifest.json").is_file()
    assert (legacy_root / "htt_base_research_evaluation_prompt.md").is_file()


def test_pdf_manifest_digest_mismatch_fails_closed(tmp_path: Path):
    mod = _load()
    pdf = tmp_path / "report.pdf"
    manifest = tmp_path / "manifest.json"
    pdf.write_bytes(b"%PDF-1.4\nmutation\n")
    manifest.write_text(
        json.dumps(
            {
                "archive_entries": [
                    {
                        "source_path": "docs/final_report/main.pdf",
                        "sha256": "sha256:" + "0" * 64,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    try:
        mod.verify_pdf_manifest_pair(
            tmp_path,
            pdf_path="report.pdf",
            manifest_path="manifest.json",
            manifest_member_path="docs/final_report/main.pdf",
        )
    except ValueError as exc:
        assert "digest mismatch" in str(exc)
    else:
        raise AssertionError("mismatched PDF companion manifest must fail closed")


def test_copied_legacy_binary_at_active_path_fails_closed():
    mod = _load()
    entry = mod.Entry(
        archive_path="research_evaluation/docs/final_report/main.pdf",
        group="legacy_report",
        source_path=Path("legacy/cf4_p0/packages/final_report/main.pdf"),
    )

    try:
        mod._entry_rows(REPO_ROOT, (entry,))
    except ValueError as exc:
        assert "immutable_historical_evidence" in str(exc)
    else:
        raise AssertionError("copied legacy PDF at an active archive path must fail")


def test_prompt_is_context_independent_and_critical_constructive():
    mod = _load()
    prompt = mod.render_prompt()
    # explains the project from scratch
    assert "no prior knowledge" in prompt.lower()
    assert "from scratch" in prompt.lower()
    # both critical and constructive
    assert "critical" in prompt.lower() and "constructive" in prompt.lower()
    # states the hard claim boundaries
    assert "Bianchi family" in prompt and "native" in prompt.lower()
    assert prompt.index("cf4_p0_quarantine_block.json") < prompt.index("main.pdf")
