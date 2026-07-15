from __future__ import annotations

import importlib.util
from io import BytesIO
import sys
from pathlib import Path
import zipfile

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_research_only_audit_package.py"
REVISION_PROGRAM_REL_PATHS = (
    "docs/audits/revision_program_2026-06-18/package_inventory.json",
    "docs/audits/revision_program_2026-06-18/package_inventory.md",
    "docs/generated/revision_plan_crosswalk.md",
    "docs/generated/revision_novelty_ledger.md",
    "docs/generated/revision_claim_lanes.md",
    "docs/generated/revision_literature_crag.md",
    "docs/generated/revision_defense_dossier.md",
    "docs/codex_handoff/pr_dag_revision.yaml",
)
REV_R087_REQUIRED_RESEARCH_REL_PATHS = (
    "docs/generated/manuscript_audit_repair_matrix.md",
    "docs/generated/qfpi_semantic_reconciliation.md",
    "docs/generated/cf4pp_lnb_provenance_report.md",
    "docs/generated/cf4pp_lnb_provenance_report.json",
    "docs/generated/external_research_input_response_matrix.md",
    "docs/generated/revision_experiment_assets.md",
    "docs/generated/revision_experiment_assets.json",
    "docs/generated/research_program_experiment_registry.yaml",
    "docs/generated/research_program_theorem_registry.yaml",
    "docs/generated/theorem_extension_registry.md",
    "docs/generated/theorem_extension_registry.json",
    "docs/generated/manuscript_rearchitecture_report.md",
    "docs/generated/progress_checkpoints/revision_checkpoint_rev_r086.md",
    "docs/codex_handoff/pr_dag_research_program.yaml",
)
REV_R087_REQUIRED_CODE_SAMPLE_NAMES = (
    "generate_theorem_extension_assets.py",
    "generate_revision_experiment_assets.py",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("research_only_audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["research_only_audit_package"] = module
    spec.loader.exec_module(module)
    return module


def test_research_only_package_manifest_includes_revision_program_files():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="python scripts/build_research_only_audit_package.py --dry-run",
        worktree_state="test-worktree",
    )

    assert validate_manifest_payload(
        payload,
        manifest_path="memory://research_only_external_audit_package_manifest.json",
        expected_artifact_path="docs/generated/research_only_external_audit_package.zip",
    ) == ()
    assert payload["required_assertions"]["revision_program_files_included"] is True
    assert payload["required_assertions"]["compiled_pdf_excluded"] is True
    assert payload["required_assertions"]["cf4_quarantine_controls_included"] is True
    assert payload["required_assertions"]["cf4_p0_quarantine_clean"] is True
    assert (
        payload["required_assertions"][
            "retained_manuscript_sources_historical_nonpublic"
        ]
        is True
    )
    assert (
        payload["required_assertions"][
            "manuscript_hard_stop_stub_only_active_source"
        ]
        is True
    )
    assert payload["cf4_p0_quarantine"]["ok"] is True
    assert payload["cf4_p0_quarantine"]["issues"] == []
    assert all(
        "content_mode" in entry and "public_use" in entry
        for entry in payload["archive_entries"]
    )
    by_source = {entry["source_path"]: entry for entry in payload["archive_entries"]}
    for path in (
        "docs/generated/cf4_p0_quarantine_block.json",
        "docs/generated/cf4_p0_quarantine_inventory.json",
    ):
        assert by_source[path]["content_mode"] == "active_public"
        assert by_source[path]["public_use"] is True
    for path in module.GOVERNANCE_CONTROL_PATHS & set(by_source):
        assert by_source[path]["content_mode"] == "governance_control"
    manuscript_sources = {
        source: row
        for source, row in by_source.items()
        if source.startswith(module.MANUSCRIPT_SOURCE_PREFIX)
        and Path(source).suffix in {".tex", ".bib"}
    }
    assert manuscript_sources[module.MANUSCRIPT_HARD_STOP_STUB]["content_mode"] == "active_public"
    assert manuscript_sources[module.MANUSCRIPT_HARD_STOP_STUB]["public_use"] is True
    for source, row in manuscript_sources.items():
        if source == module.MANUSCRIPT_HARD_STOP_STUB:
            continue
        assert row["content_mode"] == "immutable_historical_evidence", source
        assert row["public_use"] is False, source
    assert payload["active_manuscript_publication_source_authorized"] is False
    assert payload["publication_gates"]["current_manuscript_source_authorized"].startswith(
        "fail_"
    )
    archive_paths = {entry["archive_path"] for entry in payload["archive_entries"]}
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
    assert not any(path.lower().endswith(".pdf") for path in archive_paths)
    for rel_path in REVISION_PROGRAM_REL_PATHS:
        assert f"research_audit_source/{rel_path}" in archive_paths


def test_research_only_package_includes_revision_research_context():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="python scripts/build_research_only_audit_package.py --dry-run",
        worktree_state="test-worktree",
    )

    archive_paths = {entry["archive_path"] for entry in payload["archive_entries"]}
    for rel_path in REV_R087_REQUIRED_RESEARCH_REL_PATHS:
        assert f"research_audit_source/{rel_path}" in archive_paths
    for name in REV_R087_REQUIRED_CODE_SAMPLE_NAMES:
        assert f"research_audit_source/code_samples/{name}" in archive_paths


def test_research_only_package_includes_available_figure_source_json():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="python scripts/build_research_only_audit_package.py --dry-run",
        worktree_state="test-worktree",
    )

    archive_paths = {entry["archive_path"] for entry in payload["archive_entries"]}
    source_paths = {
        path
        for path in (REPO_ROOT / "figures").rglob("*.source.json")
        if f"research_audit_source/{path.with_name(path.name.removesuffix('.source.json') + '.png').relative_to(REPO_ROOT).as_posix()}"
        in archive_paths
    }
    assert source_paths
    for path in source_paths:
        assert f"research_audit_source/{path.relative_to(REPO_ROOT).as_posix()}" in archive_paths
    assert payload["required_assertions"]["available_figure_source_json_included"] is True


def test_research_only_prompt_uses_indirect_rejection_examples():
    module = _load_module()
    prompt = module.render_prompt()
    forbidden_exact_strings = (
        "Bianchi family " + "identified.",
        "Bianchi geometry " + "detected.",
        "External transfer validated " + "as native.",
    )

    for phrase in forbidden_exact_strings:
        assert phrase not in prompt
    assert "an identified Bianchi family" in prompt
    assert "a detected Bianchi geometry" in prompt
    assert "native validation claimed for external-transfer output" in prompt
    assert "model-weight, likelihood-ratio, or adjudication status" in prompt
    assert "not a current manuscript publication source" in prompt
    assert "public_use:false" in module.render_readme()


def test_research_only_package_check_can_reuse_stored_git_metadata():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="python scripts/build_research_only_audit_package.py --check",
        worktree_state="stored-worktree-state",
        git_commit="stored-git-commit",
    )

    assert payload["git_commit"] == "stored-git-commit"
    assert payload["git_commit_or_worktree_state"] == "stored-worktree-state"
    assert payload["code_version"] == "stored-worktree-state"


def test_research_only_revision_program_inputs_fail_closed_when_missing(tmp_path: Path):
    module = _load_module()

    try:
        module._revision_program_entries(tmp_path)
    except FileNotFoundError as exc:
        assert "required revision program input missing" in str(exc)
        assert "docs/audits/revision_program_2026-06-18/package_inventory.json" in str(exc)
    else:
        raise AssertionError("missing revision program input should fail closed")


def test_research_only_package_legacy_readiness_tokens_are_archival_only():
    module = _load_module()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="python scripts/build_research_only_audit_package.py --dry-run",
        worktree_state="test-worktree",
    )
    archive_bytes = module._build_zip_bytes(REPO_ROOT, payload, entries)
    tokens = (
        "production_candidate",
        "production_validated",
        "production-grade",
        "production grade",
        "public_grade=production-grade",
        "atlas_ready",
        "atlas_available",
    )
    allowed = {
        ("research_audit_source/docs/generated/claim_ledger.json", "production_validated")
    }

    offenders: list[tuple[str, str]] = []
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        for name in archive.namelist():
            if not name.endswith((".md", ".tex", ".json", ".yaml", ".yml")):
                continue
            text = archive.read(name).decode("utf-8", errors="ignore")
            for token in tokens:
                if token in text and (name, token) not in allowed:
                    offenders.append((name, token))
    assert offenders == []


def test_research_only_package_includes_line_stable_tex_and_reaudit_matrix():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="pytest",
        worktree_state="test",
    )
    paths = {entry["archive_path"] for entry in payload["archive_entries"]}
    assert "research_audit_source/docs/manuscript/main.tex" in paths
    assert "research_audit_source/docs/generated/audit_ver2_response_matrix.md" in paths
    assert "research_audit_source/docs/generated/audit_ver2_completion_report.md" in paths
    assert not any(path.lower().endswith(".pdf") for path in paths)


def test_stale_cf4_research_package_entry_mutation_fails_quarantine_gate(monkeypatch):
    module = _load_module()
    original_metadata_entries = module._metadata_entries

    def mutated_metadata_entries(repo_root: Path):
        return [
            *original_metadata_entries(repo_root),
            module._virtual_entry(
                f"{module.ARCHIVE_ROOT}/docs/generated/cf4_mv_bulkflow_card.json",
                "research_metadata",
                "mutated active package entry for the quarantine test",
                (
                    '{"claim":"CF4 MV ideal-window bulk flow '
                    '|B|(200 h^-1Mpc) = '
                    + "40"
                    + "5 km/s with LambdaCDM tension "
                    + "4.4"
                    + '-5.4 sigma"}'
                ),
            ),
        ]

    monkeypatch.setattr(module, "_metadata_entries", mutated_metadata_entries)
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/research_only_external_audit_package.zip"),
        output_manifest=Path("docs/generated/research_only_external_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/research_only_external_audit_prompt.md"),
        generating_command="pytest",
        worktree_state="test-worktree",
    )

    assert payload["required_assertions"]["cf4_p0_quarantine_clean"] is False
    assert "cf4_p0_quarantine_clean" in payload["failed_gates"]
    assert payload["cf4_p0_quarantine"]["ok"] is False
    assert payload["cf4_p0_quarantine"]["issues"]
