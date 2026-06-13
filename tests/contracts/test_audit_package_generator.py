from __future__ import annotations

import importlib.util
from io import BytesIO
import json
from pathlib import Path
import subprocess
import zipfile

from common.artifact_manifest import validate_manifest_payload


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_external_audit_package.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
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
    assert payload["transfer_source"] == "none"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://external_audit_package_manifest.json",
    ) == ()

    groups = {entry["group"] for entry in payload["archive_entries"]}
    assert {
        "audit_prompts",
        "code_snapshot",
        "framework_reports",
        "manuscript_audit",
        "pr_status",
        "result_packs",
        "transfer_provenance",
    } <= groups
    assertions = payload["required_assertions"]
    assert assertions["claim_ledger_included"] is True
    assert assertions["transfer_provenance_included"] is True
    assert assertions["figure_inventory_included"] is True
    assert assertions["audit_prompts_included"] is True
    assert assertions["code_snapshot_included"] is True
    assert assertions["future_solver_interface_included"] is True
    assert payload["failed_gates"] == []
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
        assert "prompts/README.md" in names
        assert "code_snapshot/scripts/build_external_audit_package.py" in names
        zipped_manifest = json.loads(archive.read("MANIFEST.json").decode("utf-8"))
    assert zipped_manifest == manifest
    _assert_no_forbidden_language(json.dumps(manifest, sort_keys=True))


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
