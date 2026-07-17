from __future__ import annotations

import importlib.util
from io import BytesIO
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import zipfile

from common.artifact_manifest import validate_manifest_payload
from common.cf4_p0_quarantine import CF4P0QuarantineViolation
from common.release_evidence_binding import DEFAULT_RELEASE_EVIDENCE_PIN


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_external_audit_package.py"
SOURCE_ONLY_LAUNCHER = REPO_ROOT / "scripts/codex_harness/run_pr122_source_only.sh"
SOURCE_ONLY_TARGET = "scripts/build_external_audit_package.py"
CLAIM_EVIDENCE_ARCHIVE_PATHS = {
    "docs/generated/pr122_claim_evidence_graph.json": (
        "status/pr122_claim_evidence_graph.json"
    ),
    "docs/generated/pr122_claim_closure_report.json": (
        "status/pr122_claim_closure_report.json"
    ),
    "docs/generated/pr122_claim_closure_report.md": (
        "status/pr122_claim_closure_report.md"
    ),
    "docs/generated/pr122_release_receipt.json": ("status/pr122_release_receipt.json"),
    "docs/generated/pr122_parent_receipt.json": ("status/pr122_parent_receipt.json"),
    "docs/generated/pr122_artifact_manifest.json": (
        "status/pr122_artifact_manifest.json"
    ),
    "docs/generated/pr122_mes_successor_scan.json": (
        "status/pr122_mes_successor_scan.json"
    ),
    "docs/generated/pr122_test_execution.json": ("status/pr122_test_execution.json"),
}


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_package"] = module
    spec.loader.exec_module(module)
    return module


def _cli(*args: str) -> list[str]:
    return [str(SOURCE_ONLY_LAUNCHER), SOURCE_ONLY_TARGET, *args]


@lru_cache(maxsize=1)
def _cached_payload_json() -> str:
    """Build once for read-only assertion tests; mutation/CLI tests stay fresh."""

    module = _load_module()
    payload = module.build_audit_package_payload(
        repo_root=REPO_ROOT,
        output_zip=Path("docs/generated/external_audit_package.zip"),
        output_manifest=Path("docs/generated/external_audit_package_manifest.json"),
        generating_command="python scripts/build_external_audit_package.py --dry-run",
        worktree_state="test-worktree",
    )
    return json.dumps(payload, sort_keys=True)


def _payload():
    # Return an independent object so an assertion test cannot contaminate the
    # shared immutable fixture for a later test.
    return json.loads(_cached_payload_json())


@lru_cache(maxsize=1)
def _cached_archive_bytes() -> bytes:
    """Share one immutable archive only between read-only content assertions."""

    module = _load_module()
    return module.build_zip_bytes(REPO_ROOT, _payload())


def test_entry_rows_loads_one_build_local_reviewed_pin_snapshot(monkeypatch):
    module = _load_module()
    calls = {"snapshot": 0, "recheck": 0}
    original_snapshot = module.reviewed_active_binary_sidecar_pin_snapshot
    original_recheck = module.assert_reviewed_active_binary_pin_snapshot_current

    def counted_snapshot(repo_root):
        calls["snapshot"] += 1
        return original_snapshot(repo_root)

    def counted_recheck(repo_root, snapshot):
        calls["recheck"] += 1
        return original_recheck(repo_root, snapshot)

    monkeypatch.setattr(
        module,
        "reviewed_active_binary_sidecar_pin_snapshot",
        counted_snapshot,
    )
    monkeypatch.setattr(
        module,
        "assert_reviewed_active_binary_pin_snapshot_current",
        counted_recheck,
    )
    rows = module._entry_rows(
        REPO_ROOT,
        (
            module._entry("AGENTS.md", "controls/AGENTS.md", "control", "control"),
            module._entry(".gitignore", "controls/gitignore", "control", "control"),
        ),
    )

    assert len(rows) == 2
    assert calls == {"snapshot": 1, "recheck": 1}


def _assert_no_forbidden_language(text: str) -> None:
    lowered = text.lower()
    assert ("mio " + "posterior") not in lowered
    assert ("posterior " + "odds") not in lowered
    assert ("truth " + "certificate") not in lowered
    assert ("native " + "solver result") not in lowered
    assert ("family " + "identified") not in lowered
    assert ("geometry " + "detected") not in lowered
    assert ("external transfer " + "validated " + "as native") not in lowered


def _assert_claim_evidence_manifest_contract(payload: dict[str, Any]) -> None:
    rows = [
        row for row in payload["archive_entries"] if row["group"] == "claim_evidence"
    ]
    assert {
        row["source_path"]: row["archive_path"] for row in rows
    } == CLAIM_EVIDENCE_ARCHIVE_PATHS
    assert all(row["content_mode"] == "active_public" for row in rows)
    assert all(row["public_use"] is True for row in rows)
    for row in rows:
        source_path = REPO_ROOT / row["source_path"]
        assert row["sha256"] == (
            "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest()
        )
        assert f"{row['source_path']}:{row['sha256']}" in payload["input_hashes"]

    claim_inputs = {
        item["path"]: item["archive_path"]
        for item in payload["input_artifacts"]
        if item["group"] == "claim_evidence"
    }
    assert claim_inputs == CLAIM_EVIDENCE_ARCHIVE_PATHS

    receipt = payload["claim_evidence_receipt"]
    pin = DEFAULT_RELEASE_EVIDENCE_PIN
    assert receipt["mode"] == "audit_disclosure"
    assert receipt["graph_path"] == pin.graph_path
    assert receipt["graph_file_sha256"] == pin.graph_file_sha256
    assert receipt["graph_ref"] == pin.graph_ref
    assert receipt["receipt_path"] == pin.receipt_path
    assert receipt["receipt_file_sha256"] == pin.receipt_file_sha256
    assert receipt["receipt_id"] == pin.receipt_id
    assert receipt["parent_receipt_id"] == pin.parent_receipt_id
    assert receipt["closure_path"] == pin.closure_path
    assert receipt["closure_file_sha256"] == pin.closure_file_sha256
    assert receipt["artifact_manifest_file_sha256"] == (
        pin.artifact_manifest_file_sha256
    )
    assert receipt["authority_registry_ref"] == pin.authority_registry_ref
    assert receipt["process_result"] == "PASS"
    # PR-124: mechanics evidence is PRESENT; the kill switch is
    # claim_release_allowed=False, not a BLOCKED evidence status.
    assert receipt["evidence_status"] == "PRESENT"
    assert receipt["scientific_status"] == "OPEN"
    assert receipt["authority_status"] == "REQUIRES_TRUSTED_REGISTRY_VALIDATION"
    assert receipt["audit_disclosure_allowed"] is True
    assert receipt["claim_release_allowed"] is False


def test_payload_includes_required_groups_manifest_and_kill_switches():
    payload = _payload()

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert (
        payload["transfer_source"]
        == "mixed_none_observed_reference_external_transfer_conditioned_legacy"
    )
    assert (
        payload["sky_support_status"]
        == "pending_or_unknown_for_existing_directional_artifacts"
    )
    assert (
        payload["null_mock_status"]
        == "mixed_not_statistical_jackknife_bootstrap_diagnostic_and_legacy_conditioned"
    )
    assert (
        validate_manifest_payload(
            payload,
            manifest_path="memory://external_audit_package_manifest.json",
        )
        == ()
    )

    groups = {entry["group"] for entry in payload["archive_entries"]}
    assert {
        "audit_prompts",
        "code_snapshot",
        "claim_evidence",
        "framework_reports",
        "figure_manifest",
        "figure_payload",
        "manuscript_audit",
        "pr_status",
        "result_packs",
        "quarantine_control",
        "transfer_provenance",
    } <= groups
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
    assert all(
        row["binary_binding"]["method"]
        in {
            "git_head_exact_bytes",
            "git_head_reachable_binary_blob",
            "sidecar_artifact_sha256",
        }
        for row in binary_rows
    )
    assertions = payload["required_assertions"]
    assert assertions["claim_ledger_included"] is True
    assert assertions["claim_evidence_bundle_included"] is True
    assert assertions["exact_claim_evidence_receipt_consumed"] is True
    assert assertions["claim_release_blocked_by_evidence_graph"] is True
    assert assertions["transfer_provenance_included"] is True
    assert assertions["figure_inventory_included"] is True
    assert assertions["figure_payloads_included"] is True
    assert assertions["figure_manifest_claim_lanes_safe"] is True
    assert assertions["manuscript_pdf_withheld"] is True
    assert assertions["cf4_quarantine_controls_included"] is True
    assert assertions["publication_claim_freeze_included"] is True
    assert assertions["plot_lists_included"] is True
    assert assertions["observed_data_deck_included"] is True
    assert assertions["audit_prompts_included"] is True
    assert assertions["code_snapshot_included"] is True
    assert assertions["future_solver_interface_included"] is True
    assert assertions["cf4_p0_quarantine_clean"] is True
    assert payload["cf4_p0_quarantine"]["ok"] is True
    assert payload["cf4_p0_quarantine"]["issues"] == []
    assert payload["failed_gates"] == []
    assert payload["report_generation_gates"]["figure_payload_inclusion"] == "pass"
    assert payload["report_generation_gates"]["figure_manifest_claim_lanes"] == "pass"
    assert (
        payload["report_generation_gates"]["known_quarantine_inventory_preserved"]
        == "warn"
    )
    assert payload["report_generation_gates"]["exact_claim_evidence_receipt"] == "pass"
    assert payload["science_promotion_gates"]["native_morphology_atlas"] == "fail"
    assert (
        payload["science_promotion_gates"]["claim_evidence_release"]
        == "fail_blocked_pending_PR124"
    )
    assert payload["publication_gates"]["publication_readiness"] == "fail"
    assert payload["publication_gates"]["claim_evidence_audit_disclosure"] == "pass"
    assert payload["publication_gates"]["claim_evidence_claim_release"] == "fail"
    assert "manual_status_number_findings" in payload["manuscript_blockers"]
    assert "repository_quarantined_figures" in payload["manuscript_blockers"]
    assert payload["input_artifacts"]
    assert all(item["included"] is True for item in payload["input_artifacts"])
    _assert_claim_evidence_manifest_contract(payload)
    _assert_no_forbidden_language(json.dumps(payload, sort_keys=True))


def test_cli_dry_run_does_not_write_outputs(tmp_path: Path):
    output_zip = tmp_path / "audit.zip"
    output_manifest = tmp_path / "manifest.json"

    result = subprocess.run(
        _cli(
            "--dry-run",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN" in result.stdout
    assert "claim_ledger_included=True" in result.stdout
    assert "claim_evidence_bundle_included=True" in result.stdout
    assert "exact_claim_evidence_receipt_consumed=True" in result.stdout
    assert "claim_release_blocked_by_evidence_graph=True" in result.stdout
    assert "transfer_provenance_included=True" in result.stdout
    assert not output_zip.exists()
    assert not output_manifest.exists()


def test_cli_writes_zip_manifest_and_required_contents(tmp_path: Path):
    output_zip = tmp_path / "audit.zip"
    output_manifest = tmp_path / "manifest.json"

    result = subprocess.run(
        _cli(
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ),
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
    assert manifest["required_assertions"]["claim_evidence_bundle_included"] is True
    assert (
        manifest["required_assertions"]["exact_claim_evidence_receipt_consumed"] is True
    )
    assert (
        manifest["required_assertions"]["claim_release_blocked_by_evidence_graph"]
        is True
    )
    assert manifest["required_assertions"]["transfer_provenance_included"] is True
    _assert_claim_evidence_manifest_contract(manifest)

    with zipfile.ZipFile(output_zip) as archive:
        names = set(archive.namelist())
        assert "MANIFEST.json" in names
        assert "README.md" in names
        assert "status/claim_ledger.json" in names
        assert "status/pr_status.yaml" in names
        assert set(CLAIM_EVIDENCE_ARCHIVE_PATHS.values()) <= names
        assert "reports/result_pack_A.md" in names
        assert "reports/result_pack_B.md" in names
        assert "reports/result_pack_C.md" in names
        assert "reports/transfer_sensitivity_report.md" in names
        assert "manuscript/manuscript_figure_inventory.md" in names
        assert "manuscript/htt_base_research_report.pdf" not in names
        assert "manuscript/htt_base_research_report.manifest.json" not in names
        assert "quarantine/cf4_p0_quarantine_block.json" in names
        assert "quarantine/cf4_p0_quarantine_inventory.json" in names
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
            name.startswith("manuscript/") and name.endswith(latex_byproduct_suffixes)
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
        assert (
            "figures/observed_current/fig_observed_longrun_jackknife_bootstrap.png"
            in names
        )
        assert (
            "figures/observed_current/fig_observed_longrun_jackknife_bootstrap.manifest.json"
            in names
        )
        observed_pngs = {
            name.removesuffix(".png")
            for name in names
            if name.startswith("figures/observed_current/") and name.endswith(".png")
        }
        observed_manifests = {
            name.removesuffix(".manifest.json")
            for name in names
            if name.startswith("figures/observed_current/")
            and name.endswith(".manifest.json")
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
        assert any(
            name.startswith("figures/conditioned_legacy/") and name.endswith(".png")
            for name in names
        )
        assert "prompts/README.md" in names
        assert "code_snapshot/scripts/build_external_audit_package.py" in names
        assert "code_snapshot/scripts/inventory_observational_data.py" in names
        assert "code_snapshot/scripts/make_observed_data_manuscript_figures.py" in names
        assert "code_snapshot/tests/contracts/test_observed_data_figures.py" in names
        for source_path, archive_path in CLAIM_EVIDENCE_ARCHIVE_PATHS.items():
            assert archive.read(archive_path) == (REPO_ROOT / source_path).read_bytes()
        readme = archive.read("README.md").decode("utf-8")
        assert "claim_evidence_bundle_included: True" in readme
        assert "exact_claim_evidence_receipt_consumed: True" in readme
        zipped_manifest = json.loads(archive.read("MANIFEST.json").decode("utf-8"))
    assert zipped_manifest == manifest
    assert (
        zipped_manifest["claim_evidence_receipt"] == manifest["claim_evidence_receipt"]
    )
    _assert_no_forbidden_language(json.dumps(manifest, sort_keys=True))


def test_audit_package_uses_only_tracked_sources():
    module = _load_module()
    tracked = set(
        subprocess.check_output(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            text=True,
        ).splitlines()
    )
    payload = _payload()

    allowed_generated = set(module.GENERATED_QUARANTINE_CONTROLS)
    assert all(
        row["source_path"] in tracked or row["source_path"] in allowed_generated
        for row in payload["archive_entries"]
    )
    assert all(
        item["path"] in tracked or item["path"] in allowed_generated
        for item in payload["input_artifacts"]
    )
    assert all(
        "content_mode" in row and "public_use" in row
        for row in payload["archive_entries"]
    )
    by_source = {row["source_path"]: row for row in payload["archive_entries"]}
    for path in module.GENERATED_QUARANTINE_CONTROLS:
        assert by_source[path]["content_mode"] == "active_public"
        assert by_source[path]["public_use"] is True
    for path in (
        "docs/codex_handoff/pr_backlog.yaml",
        "docs/codex_handoff/pr_status.yaml",
    ):
        assert by_source[path]["content_mode"] == "governance_control"


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
    archive_bytes = _cached_archive_bytes()
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
    archive_bytes = _cached_archive_bytes()
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
        if name in {
            "status/claim_ledger.json",
            "status/status_matrix.md",
            "status/status_snapshot.json",
        }:
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
        _cli(
            "--check",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode == 1
    assert "missing audit package output" in missing.stdout

    write = subprocess.run(
        _cli(
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert write.returncode == 0, write.stderr

    fresh = subprocess.run(
        _cli(
            "--check",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ),
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
        _cli(
            "--check",
            "--output-zip",
            str(output_zip),
            "--output-manifest",
            str(output_manifest),
        ),
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


def test_stale_cf4_package_entry_mutation_fails_quarantine_gate():
    module = _load_module()
    stale_entry = module.AuditPackageEntry(
        source_path=Path("legacy/cf4_p0/cards/cf4_mv_bulkflow_card.json"),
        archive_path="reports/cf4_mv_bulkflow_card.json",
        group="result_packs",
        description="mutated active package entry for the quarantine test",
    )

    try:
        module.build_audit_package_payload(
            repo_root=REPO_ROOT,
            output_zip=Path("docs/generated/external_audit_package.zip"),
            output_manifest=Path("docs/generated/external_audit_package_manifest.json"),
            generating_command="pytest",
            package_entries=(stale_entry,),
            worktree_state="test-worktree",
        )
    except ValueError as exc:
        assert "legacy CF4 payload" in str(exc)
    else:
        raise AssertionError("active copy of a legacy CF4 result must fail closed")


def _minimal_virtual_member_payload() -> dict[str, object]:
    return {
        "archive_entries": [],
        "required_assertions": {},
        "manuscript_blockers": {
            "missing_refs": 0,
            "quarantined_refs": 0,
            "claim_risk_findings": 0,
            "manual_status_number_findings": 0,
            "repository_quarantined_figures": 0,
        },
        "caveats": [],
    }


def _archive_open_must_not_start(*_args, **_kwargs):
    raise AssertionError("ZIP archive emission started before quarantine validation")


def test_rendered_readme_mutation_is_rejected_before_archive_emission(monkeypatch):
    module = _load_module()
    stale_text = f"CF4 bulk-flow amplitude {400 + 5 + 0.22:.2f} km/s"
    monkeypatch.setattr(module, "render_readme", lambda _payload: stale_text)
    monkeypatch.setattr(module.zipfile, "ZipFile", _archive_open_must_not_start)

    try:
        module.build_zip_bytes(REPO_ROOT, _minimal_virtual_member_payload())
    except CF4P0QuarantineViolation as exc:
        assert "README.md" in str(exc)
        assert "stale_cf4_p0_consumer" in str(exc)
    else:
        raise AssertionError("mutated generated README must fail closed")


def test_serialized_manifest_mutation_is_rejected_before_archive_emission(monkeypatch):
    module = _load_module()
    stale_value = 1 + 0.4 + 0.04 + 0.002 + 0.0003
    stale_text = f"CF4 velocity-correlation shape correction = {stale_value:.4f}"
    monkeypatch.setattr(module, "render_manifest_json", lambda _payload: stale_text)
    monkeypatch.setattr(module.zipfile, "ZipFile", _archive_open_must_not_start)

    try:
        module.build_zip_bytes(REPO_ROOT, _minimal_virtual_member_payload())
    except CF4P0QuarantineViolation as exc:
        assert "MANIFEST.json" in str(exc)
        assert "stale_cf4_p0_consumer" in str(exc)
    else:
        raise AssertionError("mutated generated manifest must fail closed")


def test_copied_legacy_pdf_at_active_archive_path_is_rejected():
    module = _load_module()
    copied = module.AuditPackageEntry(
        source_path=Path("legacy/cf4_p0/packages/final_report/main.pdf"),
        archive_path="manuscript/current_report.pdf",
        group="manuscript_pdf",
        description="mutation: copied legacy PDF at an active-looking path",
    )

    try:
        module._entry_rows(REPO_ROOT, (copied,))
    except ValueError as exc:
        assert "immutable_historical_evidence" in str(exc)
    else:
        raise AssertionError("copied legacy binary must fail closed")


def test_preserved_manuscript_pdf_pair_is_digest_inconsistent_and_omitted():
    module = _load_module()
    pdf = (
        REPO_ROOT / "legacy/cf4_p0/packages/manuscript_pdf/htt_base_research_report.pdf"
    )
    manifest_path = (
        REPO_ROOT
        / "legacy/cf4_p0/packages/manuscript_pdf/htt_base_research_report.manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = "sha256:" + hashlib.sha256(pdf.read_bytes()).hexdigest()

    assert manifest["artifact_sha256"] != actual
    sources = {entry.source_path.as_posix() for entry in module.DEFAULT_PACKAGE_ENTRIES}
    assert pdf.relative_to(REPO_ROOT).as_posix() not in sources
    assert manifest_path.relative_to(REPO_ROOT).as_posix() not in sources


def test_legacy_package_entry_is_explicitly_non_public_and_legacy_rooted():
    module = _load_module()
    entry = module.AuditPackageEntry(
        source_path=Path("legacy/cf4_p0/packages/final_report/main.pdf"),
        archive_path="legacy/cf4_p0/packages/final_report/main.pdf",
        group="legacy_report",
        description="immutable historical report evidence",
        content_mode=module.ContentMode.IMMUTABLE_HISTORICAL_EVIDENCE,
        public_use=False,
    )

    rows = module._entry_rows(REPO_ROOT, (entry,))
    assert rows[0]["content_mode"] == "immutable_historical_evidence"
    assert rows[0]["public_use"] is False


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
