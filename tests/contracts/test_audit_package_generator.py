from __future__ import annotations

import importlib.util
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_external_audit_package.py"
def _load_module():
    spec = importlib.util.spec_from_file_location("audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_package"] = module
    spec.loader.exec_module(module)
    return module


def _payload():
    module = _load_module()
    return module.build_audit_package_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/external_audit_package.zip"),
        output_manifest=Path("docs/generated/external_audit_package_manifest.json"),
        generating_command="python scripts/build_external_audit_package.py --dry-run",
        worktree_state="test-worktree",
    )


def _assert_no_forbidden_language(text: str) -> None:
    lowered = text.lower()
    assert ("mio " + "posterior") not in lowered
    assert ("posterior " + "odds") not in lowered
    assert ("truth " + "certificate") not in lowered
    assert ("native " + "solver result") not in lowered
    assert ("family " + "identified") not in lowered
    assert ("geometry " + "detected") not in lowered
    assert ("external transfer " + "validated " + "as native") not in lowered


def test_payload_includes_required_groups_manifest_and_kill_switches():
    payload = _payload()

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "mixed_none_observed_reference_external_transfer_conditioned_legacy"
    assert payload["sky_support_status"] == "pending_or_unknown_for_existing_directional_artifacts"
    assert payload["null_mock_status"] == "mixed_not_statistical_jackknife_bootstrap_diagnostic_and_legacy_conditioned"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://external_audit_package_manifest.json",
    ) == ()

    groups = {entry["group"] for entry in payload["archive_entries"]}
    assert {
        "audit_prompts",
        "code_snapshot",
        "framework_reports",
        "figure_manifest",
        "figure_payload",
        "manuscript_audit",
        "pr_status",
        "result_packs",
        "transfer_provenance",
    } <= groups
    assertions = payload["required_assertions"]
    assert assertions["claim_ledger_included"] is True
    assert assertions["transfer_provenance_included"] is True
    assert assertions["figure_inventory_included"] is True
    assert assertions["figure_payloads_included"] is True
    assert assertions["figure_manifest_claim_lanes_safe"] is True
    assert assertions["manuscript_pdf_included"] is True
    assert assertions["publication_claim_freeze_included"] is True
    assert assertions["plot_lists_included"] is True
    assert assertions["observed_data_deck_included"] is True
    assert assertions["audit_prompts_included"] is True
    assert assertions["code_snapshot_included"] is True
    assert assertions["future_solver_interface_included"] is True
    assert payload["failed_gates"] == []
    assert payload["report_generation_gates"]["figure_payload_inclusion"] == "pass"
    assert payload["report_generation_gates"]["figure_manifest_claim_lanes"] == "pass"
    assert payload["report_generation_gates"]["known_quarantine_inventory_preserved"] == "warn"
    assert payload["science_promotion_gates"]["native_morphology_atlas"] == "fail"
    assert payload["publication_gates"]["publication_readiness"] == "fail"
    assert "manual_status_number_findings" in payload["manuscript_blockers"]
    assert "repository_quarantined_figures" in payload["manuscript_blockers"]
    assert payload["input_artifacts"]
    assert all(item["included"] is True for item in payload["input_artifacts"])
    _assert_no_forbidden_language(json.dumps(payload, sort_keys=True))


def test_cli_dry_run_does_not_write_outputs(tmp_path: Path):
    output_zip = tmp_path / "audit.zip"
    output_manifest = tmp_path / "manifest.json"

    result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--dry-run",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN" in result.stdout
    assert "claim_ledger_included=True" in result.stdout
    assert "transfer_provenance_included=True" in result.stdout
    assert not output_zip.exists()
    assert not output_manifest.exists()


def test_cli_writes_zip_manifest_and_required_contents(tmp_path: Path):
    output_zip = tmp_path / "audit.zip"
    output_manifest = tmp_path / "manifest.json"

    result = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert output_zip.exists()
    assert output_manifest.exists()
    manifest = json.loads(output_manifest.read_text(encoding="utf-8"))
    assert manifest["required_assertions"]["claim_ledger_included"] is True
    assert manifest["required_assertions"]["transfer_provenance_included"] is True

    with zipfile.ZipFile(output_zip) as archive:
        names = set(archive.namelist())
        assert "MANIFEST.json" in names
        assert "README.md" in names
        assert "status/claim_ledger.json" in names
        assert "status/pr_status.yaml" in names
        assert "reports/result_pack_A.md" in names
        assert "reports/result_pack_B.md" in names
        assert "reports/result_pack_C.md" in names
        assert "reports/transfer_sensitivity_report.md" in names
        assert "manuscript/manuscript_figure_inventory.md" in names
        assert "manuscript/htt_base_research_report.pdf" in names
        assert "manuscript/htt_base_research_report.manifest.json" in names
        latex_byproduct_suffixes = (
            ".aux",
            ".bbl",
            ".blg",
            ".fdb_latexmk",
            ".fls",
            ".log",
            ".out",
            ".toc",
        )
        assert not any(
            name.startswith("manuscript/")
            and name.endswith(latex_byproduct_suffixes)
            for name in names
        )
        assert "manuscript/current_manuscript_plot_list.md" in names
        assert "manuscript/expanded_manuscript_plot_list.md" in names
        assert "manuscript/observed_current_plot_list.md" in names
        assert "manuscript/manuscript_plot_list_index.md" in names
        assert "manuscript/generated/observed_figures_pipeline.tex" in names
        assert "manuscript/generated/observed_figures_results.tex" in names
        assert "reports/observational_data_inventory.json" in names
        assert "reports/observational_data_inventory.md" in names
        assert "reports/observed_longrun_analysis.json" in names
        assert "reports/observed_longrun_analysis.md" in names
        assert "manuscript/pdf_claim_lint_report.md" in names
        assert "status/publication_claim_freeze.md" in names
        assert "status/hostile_review_response_matrix.md" in names
        assert "figures/current/fig_current_transfer_provenance.png" in names
        assert "figures/current/fig_current_transfer_provenance.manifest.json" in names
        assert "figures/observed_current/fig_observed_longrun_jackknife_bootstrap.png" in names
        assert "figures/observed_current/fig_observed_longrun_jackknife_bootstrap.manifest.json" in names
        observed_pngs = {
            name.removesuffix(".png")
            for name in names
            if name.startswith("figures/observed_current/") and name.endswith(".png")
        }
        observed_manifests = {
            name.removesuffix(".manifest.json")
            for name in names
            if name.startswith("figures/observed_current/") and name.endswith(".manifest.json")
        }
        assert observed_pngs
        assert observed_pngs == observed_manifests
        for figure_root in (
            "figures/current/",
            "figures/observed_current/",
            "figures/paper/ver2_generated/",
            "figures/conditioned_legacy/",
        ):
            pngs = {
                name.removesuffix(".png")
                for name in names
                if name.startswith(figure_root) and name.endswith(".png")
            }
            manifests = {
                name.removesuffix(".manifest.json")
                for name in names
                if name.startswith(figure_root) and name.endswith(".manifest.json")
            }
            assert pngs
            assert pngs == manifests
        assert any(name.startswith("figures/conditioned_legacy/") and name.endswith(".png") for name in names)
        assert "prompts/README.md" in names
        assert "code_snapshot/scripts/build_external_audit_package.py" in names
        assert "code_snapshot/scripts/inventory_observational_data.py" in names
        assert "code_snapshot/scripts/make_observed_data_manuscript_figures.py" in names
        assert "code_snapshot/tests/contracts/test_observed_data_figures.py" in names
        zipped_manifest = json.loads(archive.read("MANIFEST.json").decode("utf-8"))
    assert zipped_manifest == manifest
    _assert_no_forbidden_language(json.dumps(manifest, sort_keys=True))


def test_audit_package_uses_only_tracked_sources():
    tracked = set(
        subprocess.check_output(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            text=True,
        ).splitlines()
    )
    payload = _payload()

    assert all(row["source_path"] in tracked for row in payload["archive_entries"])
    assert all(item["path"] in tracked for item in payload["input_artifacts"])


def test_packaged_figure_manifests_do_not_promote_claim_lanes():
    payload = _payload()
    figure_manifest_sources = [
        row["source_path"]
        for row in payload["archive_entries"]
        if row["group"] == "figure_manifest"
    ]

    assert figure_manifest_sources
    for source_path in figure_manifest_sources:
        text = (REPO_ROOT / source_path).read_text(encoding="utf-8")
        payload = json.loads(text)
        assert payload.get("production_status") != "production_candidate"
        assert payload.get("production_status") != "production_validated"
        assert "production_candidate" not in text
        assert "production-grade" not in text


def test_packaged_result_reports_do_not_surface_legacy_readiness_tokens():
    module = _load_module()
    payload = _payload()
    archive_bytes = module.build_zip_bytes(REPO_ROOT, payload)
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
        for name in (
            "reports/result_pack_A.md",
            "reports/result_pack_B.md",
            "reports/result_pack_C.md",
        ):
            text = archive.read(name).decode("utf-8")
            offenders = [token for token in forbidden if token in text]
            assert offenders == [], name
            assert "legacy_not_current" in text


def test_full_audit_package_legacy_readiness_tokens_are_archival_only():
    module = _load_module()
    payload = _payload()
    archive_bytes = module.build_zip_bytes(REPO_ROOT, payload)
    tokens = (
        "production_candidate",
        "production_validated",
        "production-grade",
        "production grade",
        "public_grade=production-grade",
        "atlas_ready",
        "atlas_available",
    )

    def allowed(name: str, token: str) -> bool:
        if name.startswith("pr_deltas/"):
            return True
        if name in {"status/pr_backlog.yaml", "status/pr_status.yaml"}:
            return True
        if name in {"status/claim_ledger.json", "status/status_snapshot.json"}:
            return token == "production_validated"
        return False

    offenders: list[tuple[str, str]] = []
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        for name in archive.namelist():
            if not name.endswith((".md", ".tex", ".json", ".yaml", ".yml")):
                continue
            text = archive.read(name).decode("utf-8", errors="ignore")
            for token in tokens:
                if token in text and not allowed(name, token):
                    offenders.append((name, token))
    assert offenders == []


def test_zip_bytes_are_deterministic_sorted_and_path_safe():
    module = _load_module()
    payload = _payload()

    first = module.build_zip_bytes(REPO_ROOT, payload)
    second = module.build_zip_bytes(REPO_ROOT, payload)

    assert first == second
    with zipfile.ZipFile(BytesIO(first)) as archive:
        names = archive.namelist()
    assert names == sorted(names)
    assert all(not name.startswith("/") for name in names)
    assert all(".." not in Path(name).parts for name in names)
    assert all(".git" not in Path(name).parts for name in names)
    assert all("venv" not in Path(name).parts for name in names)
    assert all("__pycache__" not in Path(name).parts for name in names)
    assert all(not name.endswith((".pyc", ".tmp")) for name in names)


def test_cli_check_detects_missing_and_stale_outputs(tmp_path: Path):
    output_zip = tmp_path / "audit.zip"
    output_manifest = tmp_path / "manifest.json"

    missing = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode == 1
    assert "missing audit package output" in missing.stdout

    write = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert write.returncode == 0, write.stderr

    fresh = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert fresh.returncode == 0, fresh.stderr
    assert "up-to-date" in fresh.stdout

    output_manifest.write_text(
        output_manifest.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
    stale = subprocess.run(
        [
            str(REPO_ROOT / "venv/bin/python"),
            str(SCRIPT_PATH),
            "--check",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert stale.returncode == 1
    assert "stale audit package manifest" in stale.stdout


def test_check_mode_can_reuse_existing_self_reference_fields(tmp_path: Path):
    module = _load_module()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "git_commit": "old-committed-head",
                "git_commit_or_worktree_state": "old-committed-head+dirty",
            }
        ),
        encoding="utf-8",
    )

    git_commit, worktree_state = module._existing_manifest_self_reference_fields(
        REPO_ROOT,
        manifest,
    )
    payload = module.build_audit_package_payload(
        repo_root=REPO_ROOT,
        output_zip=tmp_path / "audit.zip",
        output_manifest=manifest,
        generating_command="pytest",
        git_commit=git_commit,
        worktree_state=worktree_state,
    )

    assert payload["git_commit"] == "old-committed-head"
    assert payload["git_commit_or_worktree_state"] == "old-committed-head+dirty"
    assert payload["code_version"] == "old-committed-head+dirty"


def test_missing_required_input_fails_closed(tmp_path: Path):
    module = _load_module()
    entry = module.AuditPackageEntry(
        source_path=Path("missing-required.md"),
        archive_path="missing/missing-required.md",
        group="required",
        description="missing required input",
    )

    try:
        module.build_audit_package_payload(
            repo_root=tmp_path,
            output_zip=Path("audit.zip"),
            output_manifest=Path("manifest.json"),
            generating_command="test",
            package_entries=(entry,),
            worktree_state="test-worktree",
        )
    except FileNotFoundError as exc:
        assert "missing-required.md" in str(exc)
    else:
        raise AssertionError("missing package input should fail closed")


def test_static_audit_prompts_carry_scope_and_downclaims():
    prompt_paths = sorted((REPO_ROOT / "docs/audit_prompts").glob("*.md"))
    assert {path.name for path in prompt_paths} >= {
        "README.md",
        "claim_firewall_review.md",
        "future_solver_interface_review.md",
        "local_global_review.md",
        "manuscript_figure_review.md",
        "transfer_provenance_review.md",
    }
    combined = "\n".join(path.read_text(encoding="utf-8") for path in prompt_paths)
    assert "diagnostic-only" in combined
    assert "transfer-conditional" in combined
    assert "native morphology atlas is absent" in combined
    assert "MIO diagnostics are not HTT likelihood/evidence inputs" in combined
    _assert_no_forbidden_language(combined)
