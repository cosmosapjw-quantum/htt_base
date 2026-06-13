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
    assert "obsstat*" in include
    assert "tsc_legacy*" in include


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
for name in [
    "htt",
    "htt.infer",
    "htt.core",
    "htt.direction",
    "htt.obsstat",
    "htt.obsstat.biposh_features",
    "htt.obsstat.morphology",
    "htt.obsstat.null_ensembles",
    "htt.obsstat.observable_vector",
    "htt.obsstat.scalar_lowell",
    "htt.obsstat.template_fit",
    "htt.zoa",
    "htt.zoa.axis_promotion",
    "htt.mio.formalism.isotropy_gap",
    "bass",
    "bass.atlas",
    "bass.atlas.atlas_entry",
    "bass.atlas.budget_ceiling_optimizer",
    "bass.transfer.native_adapter",
    "bass.transfer.native_schema",
    "common",
    "common.semantic_guards.admissibility_status",
    "common.semantic_guards.source_propagation_status",
    "mio",
    "mio.formalism.isotropy_gap",
    "tsc",
    "tsc_legacy",
    "workspace",
]:
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
    "htt.direction",
    "htt.infer",
    "htt.nulls",
    "htt.obsstat",
    "htt.obsstat.biposh_features",
    "htt.obsstat.morphology",
    "htt.obsstat.null_ensembles",
    "htt.obsstat.observable_vector",
    "htt.obsstat.scalar_lowell",
    "htt.obsstat.template_fit",
    "htt.zoa",
    "htt.zoa.axis_promotion",
    "htt.integration.to_mio",
    "bass",
    "bass.atlas",
    "bass.atlas.atlas_entry",
    "bass.atlas.budget_ceiling_optimizer",
    "bass.transfer.native_adapter",
    "bass.transfer.native_schema",
    "common",
    "common.semantic_guards.admissibility_status",
    "common.semantic_guards.source_propagation_status",
    "mio",
    "mio.formalism.isotropy_gap",
    "tsc",
    "tsc_legacy",
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


def test_nested_htt_cwd_imports_direction_without_pythonpath() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import importlib
for name in ["htt.direction", "htt.zoa.axis_promotion", "common.contracts"]:
    importlib.import_module(name)
"""

    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT / "htt" / "htt",
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_star_import_exposes_pr042_direction_surface() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
namespace = {}
exec("from htt import *", namespace)
assert "direction" in namespace
assert "zoa" in namespace
import htt.direction
import htt.zoa.axis_promotion
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


def test_obsstat_top_level_and_htt_alias_share_scalar_lowell_identity() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    codes = [
        """
import obsstat.scalar_lowell as top_level
import htt.obsstat.scalar_lowell as htt_level
assert top_level is htt_level
assert top_level.LowEllScalarSummary is htt_level.LowEllScalarSummary
""",
        """
import htt.obsstat.scalar_lowell as htt_level
import obsstat.scalar_lowell as top_level
assert top_level is htt_level
assert top_level.LowEllScalarSummary is htt_level.LowEllScalarSummary
""",
    ]

    for code in codes:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_obsstat_top_level_and_htt_alias_share_morphology_identity() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    codes = [
        """
import obsstat.morphology as top_level
import htt.obsstat.morphology as htt_level
assert top_level is htt_level
assert top_level.MorphologyAxisSummary is htt_level.MorphologyAxisSummary
""",
        """
import htt.obsstat.morphology as htt_level
import obsstat.morphology as top_level
assert top_level is htt_level
assert top_level.MorphologyAxisSummary is htt_level.MorphologyAxisSummary
""",
    ]
    for code in codes:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_obsstat_top_level_and_htt_alias_share_template_fit_identity() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    codes = [
        """
import obsstat.template_fit as top_level
import htt.obsstat.template_fit as htt_level
assert top_level is htt_level
assert top_level.TemplateFitDiagnostic is htt_level.TemplateFitDiagnostic
""",
        """
import htt.obsstat.template_fit as htt_level
import obsstat.template_fit as top_level
assert top_level is htt_level
assert top_level.TemplateFitDiagnostic is htt_level.TemplateFitDiagnostic
""",
    ]
    for code in codes:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_obsstat_top_level_and_htt_alias_share_biposh_feature_identity() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    codes = [
        """
import obsstat.biposh_features as top_level
import htt.obsstat.biposh_features as htt_level
assert top_level is htt_level
assert top_level.BiPoSHFeatureSummary is htt_level.BiPoSHFeatureSummary
""",
        """
import htt.obsstat.biposh_features as htt_level
import obsstat.biposh_features as top_level
assert top_level is htt_level
assert top_level.BiPoSHFeatureSummary is htt_level.BiPoSHFeatureSummary
""",
    ]
    for code in codes:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_obsstat_top_level_and_htt_alias_share_null_ensemble_identity() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    codes = [
        """
import obsstat.null_ensembles as top_level
import htt.obsstat.null_ensembles as htt_level
assert top_level is htt_level
assert top_level.NullEnsembleSpec is htt_level.NullEnsembleSpec
""",
        """
import htt.obsstat.null_ensembles as htt_level
import obsstat.null_ensembles as top_level
assert top_level is htt_level
assert top_level.NullEnsembleSpec is htt_level.NullEnsembleSpec
""",
    ]
    for code in codes:
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
