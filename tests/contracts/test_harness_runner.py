from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import configparser


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts" / "codex_harness" / "run_subset.py"
HARNESS_DOC = REPO_ROOT / "docs" / "codex_handoff" / "test_harness.md"
ROOT_PYTEST_INI = REPO_ROOT / "pytest.ini"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_list_reports_required_deterministic_subsets() -> None:
    completed = _run("--list")

    assert completed.returncode == 0, completed.stderr
    lines = completed.stdout.splitlines()
    assert [line.split(maxsplit=1)[0] for line in lines] == [
        "collect",
        "fast",
        "package",
        "smoke",
    ]
    assert all("PYTHONPATH" not in line for line in lines)


def test_smoke_dry_run_prints_exact_pytest_command() -> None:
    completed = _run("smoke", "--dry-run", "--python", "/tmp/python")

    assert completed.returncode == 0, completed.stderr
    command = completed.stdout.strip()
    assert command.startswith(
        "/tmp/python -m pytest -p no:cacheprovider -o addopts= -q "
    )
    assert "-m smoke" not in command
    assert "test_route_b_constants_frozen" in command
    assert "test_blind_analysis_runs_every_typed_pipeline_stage_deterministically" in command


def test_package_subset_targets_packaging_import_smoke() -> None:
    completed = _run("package", "--dry-run", "--python", "/tmp/python")

    assert completed.returncode == 0, completed.stderr
    command = completed.stdout.strip()
    assert command.startswith(
        "/tmp/python -m pytest -p no:cacheprovider -o addopts= -q "
    )
    assert "test_dirty_build_cache_cannot_change_wheel_or_source_payload" in command
    assert "test_packaged_pr124_receipt_is_byte_identical_to_historical_authority" in command


def test_unknown_subset_exits_nonzero_without_running() -> None:
    completed = _run("not-a-subset")

    assert completed.returncode == 2
    assert "unknown subset: not-a-subset" in completed.stderr


def test_execution_returns_child_exit_code_without_masking_failure() -> None:
    completed = _run("smoke", "--python", "/bin/false")

    assert completed.returncode == 1
    assert "-m pytest -p no:cacheprovider -o addopts= -q" in completed.stdout


def test_default_python_prefers_repo_venv_without_hidden_pythonpath() -> None:
    completed = _run("collect", "--dry-run")

    assert completed.returncode == 0, completed.stderr
    command = completed.stdout.strip()
    expected_python = REPO_ROOT / "venv" / "bin" / "python"
    if expected_python.exists():
        assert command.startswith(str(expected_python))
    else:
        assert command.startswith(sys.executable)
    assert "-p no:cacheprovider -o addopts=" in command


def test_harness_doc_lists_supported_subsets_and_scope() -> None:
    rendered = HARNESS_DOC.read_text(encoding="utf-8")

    for subset in ("collect", "smoke", "fast", "package"):
        assert f"`{subset}`" in rendered
    assert "source-layout roots" in rendered
    assert "Marker-only smoke" in rendered
    assert "not scientific validation" in rendered
    assert "family-identification evidence" in rendered


def test_contract_tests_are_in_root_collect_subset() -> None:
    parser = configparser.ConfigParser()
    parser.read(ROOT_PYTEST_INI, encoding="utf-8")

    testpaths = parser["pytest"]["testpaths"].split()
    assert "tests" in testpaths
