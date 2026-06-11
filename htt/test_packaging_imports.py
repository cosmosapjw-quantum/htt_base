from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from packaging.version import Version


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "htt" / "pyproject.toml"


def test_project_version_is_pep440() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    Version(metadata["project"]["version"])


def test_editable_package_set_includes_legacy_htt_package() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    include = metadata["tool"]["setuptools"]["packages"]["find"]["include"]

    assert "htt*" in include


def test_dev_extra_covers_collection_time_imports() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dev = metadata["project"]["optional-dependencies"]["dev"]
    normalized = {requirement.split(">=", 1)[0].lower() for requirement in dev}

    assert {"pytest", "matplotlib", "pyyaml"} <= normalized


def test_repo_root_import_surface_without_pythonpath() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import importlib
for name in ["htt", "htt.infer", "htt.core", "bass", "common", "mio", "tsc", "workspace"]:
    importlib.import_module(name)
"""

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_temp_cwd_import_surface_without_pythonpath() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import importlib
for name in [
    "htt",
    "htt.core",
    "htt.infer",
    "htt.nulls",
    "htt.integration.to_mio",
    "bass",
    "common",
    "mio",
    "tsc",
    "workspace",
]:
    importlib.import_module(name)
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=tmpdir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    assert completed.returncode == 0, completed.stderr
