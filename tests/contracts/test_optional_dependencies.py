from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_SCRIPT = REPO_ROOT / "scripts" / "codex_harness" / "optional_dep_report.py"


def test_registry_declares_expected_optional_dependencies() -> None:
    from common.optional_dependencies import (
        OPTIONAL_DEPENDENCY_MARKERS,
        OPTIONAL_DEPENDENCIES,
    )

    by_key = {dependency.key: dependency for dependency in OPTIONAL_DEPENDENCIES}
    assert {"healpy", "dynesty", "astropy", "camb"} <= set(by_key)
    assert OPTIONAL_DEPENDENCY_MARKERS == {
        "requires_healpy": "healpy",
        "requires_dynesty": "dynesty",
    }
    assert by_key["astropy"].missing_policy == "documented_blocker"
    assert by_key["healpy"].skip_reason() == (
        "optional dependency 'healpy' not installed; "
        "install it to run tests marked requires_healpy"
    )


def test_dependency_statuses_are_explicit_for_missing_skip_and_blocker() -> None:
    from common.optional_dependencies import dependency_statuses

    def fake_finder(import_name: str):
        if import_name == "dynesty":
            return object()
        return None

    statuses = {status.key: status for status in dependency_statuses(finder=fake_finder)}

    assert statuses["dynesty"].available is True
    assert statuses["dynesty"].status == "available"
    assert statuses["healpy"].available is False
    assert statuses["healpy"].status == "missing_skip"
    assert statuses["healpy"].missing_policy == "skip"
    assert statuses["astropy"].available is False
    assert statuses["astropy"].status == "missing_documented_blocker"
    assert "documented blocker" in statuses["astropy"].explanation


def test_conftest_uses_common_optional_dependency_registry() -> None:
    from common.optional_dependencies import OPTIONAL_DEPENDENCY_MARKERS

    conftest_path = REPO_ROOT / "htt" / "conftest.py"
    spec = importlib.util.spec_from_file_location("htt_pr021_conftest", conftest_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._OPTIONAL_DEPENDENCY_MARKERS == OPTIONAL_DEPENDENCY_MARKERS


def test_optional_dependency_report_writes_metadata_and_attribution(tmp_path: Path) -> None:
    output = tmp_path / "optional_dependency_status.md"

    completed = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), "--output", str(output)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    rendered = output.read_text(encoding="utf-8")
    assert "owner: COMMON" in rendered
    assert "claim_tier: diagnostic_only" in rendered
    assert "transfer_source: none" in rendered
    assert "generating_command: python scripts/codex_harness/optional_dep_report.py" in rendered
    assert "| healpy | healpy |" in rendered
    assert "| dynesty | dynesty |" in rendered
    assert "requires_healpy" in rendered
    assert "pytest.importorskip" in rendered
    assert "not scientific readiness evidence" in rendered


def test_optional_dependency_report_default_path_dry_run() -> None:
    completed = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "docs/generated/optional_dependency_status.md" in completed.stdout
    assert "COMMON optional dependency registry" in completed.stdout
