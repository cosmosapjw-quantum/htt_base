from __future__ import annotations

import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import zipfile

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_statistical_formalism_audit_package.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("statistical_formalism_audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["statistical_formalism_audit_package"] = module
    spec.loader.exec_module(module)
    return module


def test_statistical_formalism_package_includes_focused_sources():
    module = _load_module()
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/statistical_formalism_audit_package.zip"),
        output_manifest=Path("docs/generated/statistical_formalism_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/statistical_formalism_audit_prompt.md"),
        output_readiness=Path("docs/generated/statistical_formalism_reaudit_readiness.md"),
        generating_command="python scripts/build_statistical_formalism_audit_package.py --dry-run",
        git_commit="test-commit",
        worktree_state="test-worktree",
    )

    assert validate_manifest_payload(
        payload,
        manifest_path="memory://statistical_formalism_audit_package_manifest.json",
        expected_artifact_path="docs/generated/statistical_formalism_audit_package.zip",
    ) == ()
    assert not payload["failed_gates"]
    for assertion in (
        "compiled_pdf_excluded",
        "latex_source_included",
        "statistical_prompt_included",
        "readiness_checklist_included",
        "figure_label_linter_report_included",
        "figure_label_linter_passed",
        "formalism_code_included",
        "formalism_tests_included",
        "formalism_metadata_included",
        "formalism_figures_have_payload_and_manifest",
        "figure_manifest_lanes_safe",
        "minimal_formalism_scope_only",
    ):
        assert payload["required_assertions"][assertion] is True

    archive_paths = {row["archive_path"] for row in payload["archive_entries"]}
    assert "AUDIT_PROMPT_STATISTICAL_FORMALISM.md" in archive_paths
    assert "READINESS_CHECKLIST.md" in archive_paths
    assert "FIGURE_LABEL_LINTER_REPORT.md" in archive_paths
    assert "statistical_formalism_audit/docs/manuscript/ch01_introduction.tex" in archive_paths
    assert "statistical_formalism_audit/docs/manuscript/ch03_framework.tex" in archive_paths
    assert "statistical_formalism_audit/docs/manuscript/ch07_results.tex" in archive_paths
    assert "statistical_formalism_audit/docs/manuscript/ch09_discussion.tex" in archive_paths
    assert "statistical_formalism_audit/docs/manuscript/generated/formalism_methods_claim_ladder.tex" in archive_paths
    assert "statistical_formalism_audit/docs/generated/formalism_audit_originality_response_matrix.md" in archive_paths
    assert "statistical_formalism_audit/docs/generated/hostile_review_response_matrix.md" in archive_paths
    assert "statistical_formalism_audit/htt/mio/formalism/normalized_score.py" in archive_paths
    assert "statistical_formalism_audit/htt/mio/formalism/filling_fraction.py" in archive_paths
    assert "statistical_formalism_audit/tests/mio/test_isotropy_gap.py" in archive_paths
    assert "statistical_formalism_audit/figures/current/fig_current_qfpi_gf_semantic_split.png" in archive_paths
    assert not any(path.lower().endswith(".pdf") for path in archive_paths)

    prompt = next(entry for entry in _entries if entry.archive_path == "AUDIT_PROMPT_STATISTICAL_FORMALISM.md").bytes(REPO_ROOT).decode("utf-8")
    assert "Novelty and substance" in prompt
    assert "Cancellation and magnitude reporting" in prompt
    assert "signed sector components" in prompt
    assert "Legacy lnB leakage" in prompt
    assert "semantic-firewall machinery" in prompt


def test_statistical_formalism_package_self_reference_reuse(tmp_path: Path):
    module = _load_module()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"git_commit":"stored-commit","git_commit_or_worktree_state":"stored-worktree"}',
        encoding="utf-8",
    )

    git_commit, worktree_state = module._existing_manifest_self_reference_fields(
        REPO_ROOT,
        manifest,
    )
    payload, _entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/statistical_formalism_audit_package.zip"),
        output_manifest=manifest,
        output_prompt=Path("docs/generated/statistical_formalism_audit_prompt.md"),
        output_readiness=Path("docs/generated/statistical_formalism_reaudit_readiness.md"),
        generating_command="python scripts/build_statistical_formalism_audit_package.py --check",
        git_commit=git_commit,
        worktree_state=worktree_state,
    )

    assert payload["git_commit"] == "stored-commit"
    assert payload["git_commit_or_worktree_state"] == "stored-worktree"
    assert payload["code_version"] == "stored-worktree"


def test_statistical_formalism_package_missing_inputs_fail_closed(tmp_path: Path):
    module = _load_module()

    try:
        module._file_entries(
            tmp_path,
            ("docs/manuscript/main.tex",),
            group="latex_source",
            description="required",
        )
    except FileNotFoundError as exc:
        assert "required statistical-formalism audit input missing" in str(exc)
        assert "docs/manuscript/main.tex" in str(exc)
    else:
        raise AssertionError("missing statistical-formalism input should fail closed")


def test_statistical_formalism_package_reports_normalize_legacy_readiness():
    module = _load_module()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/statistical_formalism_audit_package.zip"),
        output_manifest=Path("docs/generated/statistical_formalism_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/statistical_formalism_audit_prompt.md"),
        output_readiness=Path("docs/generated/statistical_formalism_reaudit_readiness.md"),
        generating_command="python scripts/build_statistical_formalism_audit_package.py --dry-run",
        git_commit="test-commit",
        worktree_state="test-worktree",
    )
    archive_bytes = module._build_zip_bytes(REPO_ROOT, payload, entries)
    forbidden = (
        "production_candidate",
        "production_validated",
        "production-grade",
        "production grade",
        "public_grade=production-grade",
        "atlas_ready",
        "atlas_available",
    )

    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        report_names = [
            name
            for name in archive.namelist()
            if name.endswith((".md", ".tex", ".json"))
            and (
                name.startswith("statistical_formalism_audit/docs/generated/result_pack_")
                or name.startswith("statistical_formalism_audit/docs/ver2_upgrade/generated/result_pack_")
            )
        ]
        assert report_names
        for name in report_names:
            text = archive.read(name).decode("utf-8")
            offenders = [token for token in forbidden if token in text]
            assert offenders == [], name


def test_statistical_formalism_legacy_readiness_tokens_are_archival_only():
    module = _load_module()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/statistical_formalism_audit_package.zip"),
        output_manifest=Path("docs/generated/statistical_formalism_audit_package_manifest.json"),
        output_prompt=Path("docs/generated/statistical_formalism_audit_prompt.md"),
        output_readiness=Path("docs/generated/statistical_formalism_reaudit_readiness.md"),
        generating_command="python scripts/build_statistical_formalism_audit_package.py --dry-run",
        git_commit="test-commit",
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
        (
            "statistical_formalism_audit/docs/ver2_upgrade/generated/status_snapshot.json",
            "production_validated",
        )
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
