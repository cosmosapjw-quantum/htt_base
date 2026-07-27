from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from common.artifact_manifest import validate_manifest_payload
from common.statistical_foundations import (
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/result_packs/generate_pack_A_scalar_to_morphology.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pack_a_generator", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pack_a_payload_compares_scalar_and_morphology_surfaces():
    module = _load_module()

    payload = module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/result_packs/generate_pack_A_scalar_to_morphology.py --dry-run",
        worktree_state="test-worktree",
    )

    assert payload["owner"] == "COMMON"
    assert payload["implementation_scope"] == "common"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert payload["artifact_id"] == "result_pack_A_scalar_to_morphology"
    assert validate_manifest_payload(
        payload,
        manifest_path="memory://result_pack_A.md",
    ) == ()

    assert {item["name"] for item in payload["scalar_diagnostics"]} == {
        "Q",
        "F",
        "Pi",
    }
    assert {item["owner"] for item in payload["scalar_diagnostics"]} == {"MIO"}
    assert {
        item["classification"] for item in payload["scalar_diagnostics"]
    } == {BC1_LEGACY_PROJECTION}
    assert {
        item["representation_policy"] for item in payload["scalar_diagnostics"]
    } == {BC2_NO_REPRESENTATION_PROMOTION}
    assert {
        item["status"] for item in payload["scalar_diagnostics"]
    } == {"legacy_projection_only"}
    scalar_text = json.dumps(payload["scalar_diagnostics"], sort_keys=True).lower()
    assert "certified filling-fraction" not in scalar_text
    assert "occupancy-style" not in scalar_text
    assert {"OBSSTAT", "COMMON"} <= {
        item["owner"] for item in payload["morphology_mes_diagnostics"]
    }
    assert payload["dependency_status"]["PR-056"]["implemented"] is True
    assert payload["dependency_status"]["PR-076"]["implemented"] is True
    assert payload["dependency_status"]["PR-092"]["implemented"] is True
    assert payload["comparison_matrix"]
    assert {
        item["artifact_id"] for item in payload["legacy_ver2_context"]["artifacts"]
    } == {
        "bass.ver2.export.solver_core_output_tier_b.observable_vector",
        "bass.ver2.export.solver_core_output_tier_b.atlas_lite",
        "bass.ver2.export.solver_core_output_tier_b.atlas_lite.mes.R_sigma_proxy",
    }
    assert payload["legacy_ver2_context"]["pr110_use"] == (
        "legacy_context_only_not_promoted"
    )
    assert payload["legacy_ver2_context"]["current_public_production_status"] == (
        "diagnostic_only"
    )
    assert payload["legacy_ver2_context"]["legacy_readiness_status"] == (
        "legacy_not_current"
    )
    assert all(
        item["current_public_production_status"] == "diagnostic_only"
        for item in payload["legacy_ver2_context"]["artifacts"]
    )
    assert all(
        item["legacy_readiness_status"] == "legacy_not_current"
        for item in payload["legacy_ver2_context"]["artifacts"]
    )

    text = json.dumps(payload, sort_keys=True).lower()
    assert "production_candidate" not in text
    assert "production-grade" not in text
    assert "atlas_ready" not in text
    assert "atlas_available" not in text
    assert ("posterior " + "odds") not in text
    assert ("native " + "solver result") not in text
    assert "family identified" not in text
    assert "geometry detected" not in text
    assert "mio certificate" not in text


def test_pack_a_default_source_identity_is_content_addressed_and_stable():
    module = _load_module()

    first = module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command="unit-test",
    )
    second = module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command="unit-test",
    )

    identity = first["git_commit_or_worktree_state"]
    assert identity.startswith("declared-input-set:sha256:")
    assert second["git_commit_or_worktree_state"] == identity
    assert first["manifest"]["code_version"] == identity


def test_pack_a_markdown_has_manifest_and_caveated_comparison():
    module = _load_module()
    payload = module.build_result_pack_payload(
        repo_root=REPO_ROOT,
        generating_command="unit-test",
        worktree_state="test-worktree",
    )

    markdown = module.render_markdown(payload)

    assert "# Result Pack A - Scalar To Morphology Upgrade" in markdown
    assert "owner: COMMON" in markdown
    assert "claim_tier: diagnostic_only" in markdown
    assert "| Q | MIO |" in markdown
    assert BC1_LEGACY_PROJECTION in markdown
    assert BC2_NO_REPRESENTATION_PROMOTION in markdown
    scalar_rows = {
        name: next(
            line
            for line in markdown.splitlines()
            if line.startswith(f"| {name} | MIO |")
        )
        for name in ("Q", "F", "Pi")
    }
    assert all(
        BC1_LEGACY_PROJECTION in row
        and BC2_NO_REPRESENTATION_PROMOTION in row
        for row in scalar_rows.values()
    )
    assert "| MES I_morph | COMMON |" in markdown
    assert "bass.ver2.export.solver_core_output_tier_b.atlas_lite" in markdown
    assert "prior_context_only" in markdown
    assert "legacy_not_current" in markdown
    assert "production_candidate" not in markdown
    assert "production-grade" not in markdown
    assert "diagnostic-only comparison" in markdown
    assert "native morphology atlas support remains absent" in markdown
    lowered = markdown.lower()
    assert ("posterior " + "odds") not in lowered
    assert ("native " + "solver result") not in lowered
    assert "family identified" not in lowered
    assert "geometry detected" not in lowered


def test_pack_a_cli_dry_run_does_not_write_output(tmp_path):
    output = tmp_path / "result_pack_A.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN" in result.stdout
    assert "Result Pack A - Scalar To Morphology Upgrade" in result.stdout
    assert not output.exists()


def test_pack_a_cli_writes_report(tmp_path):
    output = tmp_path / "result_pack_A.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    content = output.read_text(encoding="utf-8")
    assert "Result Pack A - Scalar To Morphology Upgrade" in content
    assert "wrote" in result.stdout


def test_pack_a_cli_check_detects_drift(tmp_path):
    output = tmp_path / "result_pack_A.md"

    write_result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert write_result.returncode == 0, write_result.stderr

    check_result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--check",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert check_result.returncode == 0, check_result.stderr
    assert "up-to-date" in check_result.stdout

    output.write_text(output.read_text(encoding="utf-8") + "\nmanual drift\n")
    stale_result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--check",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert stale_result.returncode == 1
    assert "stale result pack" in stale_result.stdout


def test_repository_pack_a_is_current():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "up-to-date" in result.stdout
