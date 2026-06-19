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
    archive_paths = {entry["archive_path"] for entry in payload["archive_entries"]}
    assert not any(path.lower().endswith(".pdf") for path in archive_paths)
    for rel_path in REVISION_PROGRAM_REL_PATHS:
        assert f"research_audit_source/{rel_path}" in archive_paths


def test_research_only_prompt_uses_indirect_rejection_examples():
    module = _load_module()
    prompt = module.render_prompt()
    forbidden_exact_strings = (
        "Bianchi family " + "identified.",
        "Bianchi geometry " + "detected.",
        "External transfer " + "validated as native.",
        "MIO posterior/evidence/" + "truth certificate.",
    )

    for phrase in forbidden_exact_strings:
        assert phrase not in prompt
    assert "an identified Bianchi family" in prompt
    assert "a detected Bianchi geometry" in prompt


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
