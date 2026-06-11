from __future__ import annotations

import configparser
import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_MARKERS = {
    "smoke",
    "fast",
    "slow",
    "requires_healpy",
    "requires_dynesty",
    "anchor",
    "ci",
    "verification",
}


def _marker_names(path: Path) -> set[str]:
    parser = configparser.ConfigParser()
    assert parser.read(path, encoding="utf-8") == [str(path)]
    marker_lines = parser.get("pytest", "markers").splitlines()
    return {
        line.split(":", 1)[0].strip()
        for line in marker_lines
        if line.strip() and not line.lstrip().startswith("#")
    }


def _python_file_patterns(path: Path) -> set[str]:
    parser = configparser.ConfigParser()
    assert parser.read(path, encoding="utf-8") == [str(path)]
    return set(parser.get("pytest", "python_files").split())


def _pyproject_pytest_options() -> dict:
    data = tomllib.loads((REPO_ROOT / "htt" / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["pytest"]["ini_options"]


def _pyproject_marker_names() -> set[str]:
    marker_lines = _pyproject_pytest_options()["markers"]
    return {line.split(":", 1)[0].strip() for line in marker_lines}


def _load_htt_conftest():
    conftest_path = REPO_ROOT / "htt" / "conftest.py"
    spec = importlib.util.spec_from_file_location("htt_taxonomy_conftest", conftest_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _DummyItem:
    def __init__(self, markers: set[str]):
        self._markers = markers
        self.added_markers = []

    def get_closest_marker(self, marker_name: str):
        if marker_name in self._markers:
            return object()
        return None

    def add_marker(self, marker):
        self.added_markers.append(marker)


def _skip_reasons(item: _DummyItem) -> list[str]:
    reasons: list[str] = []
    for marker in item.added_markers:
        mark = getattr(marker, "mark", marker)
        reason = getattr(mark, "kwargs", {}).get("reason")
        if reason is not None:
            reasons.append(reason)
    return reasons


def test_root_pytest_config_registers_required_markers() -> None:
    assert REQUIRED_MARKERS <= _marker_names(REPO_ROOT / "pytest.ini")


def test_nested_pytest_config_registers_required_markers() -> None:
    assert REQUIRED_MARKERS <= _marker_names(REPO_ROOT / "htt" / "pytest.ini")


def test_pyproject_pytest_metadata_registers_required_markers() -> None:
    assert REQUIRED_MARKERS <= _pyproject_marker_names()


def test_pytest_configs_keep_default_file_discovery_patterns() -> None:
    expected = {"test_*.py", "*_test.py"}
    assert expected <= _python_file_patterns(REPO_ROOT / "pytest.ini")
    assert expected <= _python_file_patterns(REPO_ROOT / "htt" / "pytest.ini")
    assert expected <= set(_pyproject_pytest_options()["python_files"])


def test_optional_dependency_collection_hook_adds_named_skip_reasons(monkeypatch) -> None:
    conftest = _load_htt_conftest()
    monkeypatch.setattr(conftest, "_dependency_available", lambda module_name: False)
    healpy_item = _DummyItem({"requires_healpy"})
    dynesty_item = _DummyItem({"requires_dynesty"})
    unmarked_item = _DummyItem(set())

    conftest.pytest_collection_modifyitems(
        config=None,
        items=[healpy_item, dynesty_item, unmarked_item],
    )

    assert _skip_reasons(healpy_item) == [
        "optional dependency 'healpy' not installed; "
        "install it to run tests marked requires_healpy"
    ]
    assert _skip_reasons(dynesty_item) == [
        "optional dependency 'dynesty' not installed; "
        "install it to run tests marked requires_dynesty"
    ]
    assert _skip_reasons(unmarked_item) == []


def test_smoke_subset_runs_without_unknown_marker_warnings() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-m", "smoke", "-q"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PytestUnknownMarkWarning" not in completed.stdout + completed.stderr
    assert "no tests ran" not in completed.stdout + completed.stderr


def test_collect_only_runs_without_unknown_marker_warnings() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "PytestUnknownMarkWarning" not in completed.stdout + completed.stderr


def test_optional_dependency_tests_have_named_skip_gates() -> None:
    healpy_test = (REPO_ROOT / "htt" / "bass" / "forward" / "test_map_producer.py").read_text(
        encoding="utf-8"
    )
    dynesty_test = (
        REPO_ROOT / "htt" / "bass" / "inference" / "test_fb113_bayes_factor_skeleton.py"
    ).read_text(encoding="utf-8")

    assert "pytest.importorskip(\"healpy\"" in healpy_test
    assert "optional dependency 'healpy' not installed" in healpy_test
    assert "pytest.mark.requires_healpy" in healpy_test
    assert "pytest.importorskip(\"dynesty\"" in dynesty_test
    assert "optional dependency 'dynesty' not installed" in dynesty_test
    assert "pytest.mark.requires_dynesty" in dynesty_test
