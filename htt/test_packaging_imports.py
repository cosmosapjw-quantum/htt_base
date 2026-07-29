from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

try:  # Python 3.11+ stdlib; bass-py metadata supplies tomli on Python 3.10.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by import fallback probe
    import tomli as tomllib

from packaging.version import Version


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "htt" / "pyproject.toml"
COMPAT_PYPROJECT = REPO_ROOT / "htt" / "htt" / "pyproject.toml"
COMPAT_SETUP = REPO_ROOT / "htt" / "htt" / "setup.py"
PACKAGE_ROOT = REPO_ROOT / "htt"


def _requirement_names(requirements: list[str]) -> set[str]:
    return {
        re.split(r"[<>=!~;\s\[]", requirement, maxsplit=1)[0].lower()
        for requirement in requirements
    }


def _source_hashes(root: Path) -> dict[str, str]:
    ignored = {"build", "dist", "__pycache__"}
    hashes: dict[str, str] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in ignored or part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.is_file():
            hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def test_project_version_is_pep440() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    Version(metadata["project"]["version"])


def test_editable_package_set_includes_legacy_htt_package() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    package_find = metadata["tool"]["setuptools"]["packages"]["find"]
    include = package_find["include"]
    exclude = package_find["exclude"]

    assert "htt*" in include
    assert "obsstat*" in include
    assert "tsc_legacy*" in include
    assert "teff*" in include
    assert package_find["namespaces"] is False
    assert {"build*", "*.build*", "*.egg-info*"} <= set(exclude)


def test_runtime_dependencies_cover_import_time_dependencies() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    runtime = _requirement_names(metadata["project"]["dependencies"])
    dev = metadata["project"]["optional-dependencies"]["dev"]

    assert {"emcee", "matplotlib", "numpy", "pyyaml", "scipy", "sympy", "tomli"} <= runtime
    assert (
        "tomli>=1.1.0; python_version < '3.11'"
        in metadata["project"]["dependencies"]
    )
    assert _requirement_names(dev) == {"pytest"}


def test_packaging_entrypoints_fall_back_to_tomli_without_tomllib() -> None:
    code = """
import builtins
import importlib.util
import sys
import types

real_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == "tomllib":
        raise ModuleNotFoundError("simulated Python 3.10")
    return real_import(name, *args, **kwargs)

fallback = types.ModuleType("tomli")
fallback.TOMLDecodeError = ValueError
fallback.loads = lambda value: {"fallback": value}
sys.modules["tomli"] = fallback
builtins.__import__ = guarded_import
sys.path.insert(0, sys.argv[2])
spec = importlib.util.spec_from_file_location(sys.argv[3], sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert module.tomllib is fallback
"""
    module_paths = (
        PACKAGE_ROOT / "src/common/package_topology.py",
        REPO_ROOT / "scripts/codex_harness/hermetic_replay.py",
        Path(__file__),
    )
    for index, module_path in enumerate(module_paths):
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                code,
                str(module_path),
                str(PACKAGE_ROOT / "src"),
                f"package_py310_probe_{index}",
            ],
            cwd=Path.home(),
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, f"{module_path}: {completed.stderr}"


def test_htt_distribution_is_a_package_empty_compatibility_metapackage() -> None:
    metadata = tomllib.loads(COMPAT_PYPROJECT.read_text(encoding="utf-8"))
    setup_source = COMPAT_SETUP.read_text(encoding="utf-8")

    assert metadata["project"]["name"] == "htt"
    assert metadata["project"]["version"] == "8.3.0"
    assert metadata["project"]["dependencies"] == ["bass-py==0.8.2+w8.2"]
    assert metadata["tool"]["setuptools"]["packages"] == []
    assert "find_packages" not in setup_source
    assert setup_source.count("setup()") == 1
    assert "name=" not in setup_source
    assert "version=" not in setup_source
    assert "install_requires=" not in setup_source


def test_package_data_and_cache_exclusions_are_explicit() -> None:
    metadata = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    setuptools = metadata["tool"]["setuptools"]
    package_data = setuptools["package-data"]

    assert setuptools["include-package-data"] is False
    assert package_data["bass.recombination"] == [
        "fixtures/recombination_ref_planck2018.csv",
        "fixtures/recombination_ref_planck2018_z1e10.csv",
    ]
    assert package_data["bass.validation"] == ["_d2_anchor_golden.json"]
    assert package_data["htt.tests"] == [
        "fixtures/pipeline_outputs/FLRW_tilt_results.json",
        "fixtures/pipeline_outputs/IS06_3D_posterior.npz",
        "fixtures/pipeline_outputs/robustness_sweeps_integrated.json",
    ]
    assert package_data["workspace"] == ["data/obs_defaults.json"]
    excluded_data = set(setuptools["exclude-package-data"]["*"])
    assert {"build/**/*", "*/build/**/*", "__pycache__/*", "*.egg-info/*"} <= excluded_data


def test_dirty_build_cache_cannot_change_wheel_or_source_payload() -> None:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "1784120280"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_INDEX"] = "1"
    env.pop("PYTHONPATH", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ignored_caches = shutil.ignore_patterns(
            "build", "dist", "*.egg-info", "__pycache__", "*.pyc"
        )
        clean_project = tmp / "clean-project"
        dirty_project = tmp / "dirty-project"
        shutil.copytree(PACKAGE_ROOT, clean_project, ignore=ignored_caches)
        shutil.copytree(PACKAGE_ROOT, dirty_project, ignore=ignored_caches)

        def build_wheel(project: Path, output: Path) -> Path:
            output.mkdir()
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--disable-pip-version-check",
                    "--no-cache-dir",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    str(output),
                    str(project),
                ],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr
            wheels = list(output.glob("*.whl"))
            assert len(wheels) == 1, [wheel.name for wheel in wheels]
            assert wheels[0].name.startswith("bass_py-")
            return wheels[0]

        clean_wheel = build_wheel(clean_project, tmp / "clean-wheel")

        source_cache = dirty_project / "htt" / "build" / "lib" / "htt" / "stale_source.py"
        source_cache.parent.mkdir(parents=True)
        source_cache.write_text("STALE_SOURCE = True\n", encoding="utf-8")

        injected_package_data = (
            dirty_project / "bass" / "validation" / "untracked_matching_name.json",
            dirty_project / "bass" / "recombination" / "fixtures" / "untracked_matching_name.csv",
            dirty_project / "htt" / "tests" / "fixtures" / "pipeline_outputs" / "untracked_matching_name.npz",
        )
        for injected in injected_package_data:
            injected.write_bytes(b"UNTRACKED_PACKAGE_DATA\n")

        source_before = _source_hashes(dirty_project)
        source_cache_before = source_cache.read_bytes()
        dirty_wheel = build_wheel(dirty_project, tmp / "dirty-wheel")

        assert dirty_wheel.read_bytes() == clean_wheel.read_bytes()
        assert hashlib.sha256(dirty_wheel.read_bytes()).digest() == hashlib.sha256(
            clean_wheel.read_bytes()
        ).digest()
        assert _source_hashes(dirty_project) == source_before
        assert source_cache.read_bytes() == source_cache_before
        assert all(path.read_bytes() == b"UNTRACKED_PACKAGE_DATA\n" for path in injected_package_data)

        with zipfile.ZipFile(dirty_wheel) as archive:
            names = archive.namelist()
        assert not any(
            part in {"build", "__pycache__"} or part.endswith(".egg-info")
            for name in names
            for part in Path(name).parts
        )
        assert not any(name.startswith("workspace/results/") for name in names)
        assert not any("untracked_matching_name" in name for name in names)


def test_compat_sdist_and_editable_wheel_are_metadata_only() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project = tmp / "compat"
        project.mkdir()
        for name in ("MANIFEST.in", "README.md", "pyproject.toml", "setup.py"):
            shutil.copy2(COMPAT_PYPROJECT.parent / name, project / name)
        (project / "tests").mkdir()
        (project / "tests" / "should_not_ship.py").write_text("raise AssertionError\n")
        (project / "htt").mkdir()
        (project / "htt" / "should_not_ship.py").write_text("raise AssertionError\n")
        dist = project / "dist"
        dist.mkdir()

        code = """
from setuptools.build_meta import build_editable, build_sdist
build_sdist("dist")
build_editable("dist")
"""
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=project,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr

        sdist = next(dist.glob("htt-8.3.0.tar.gz"))
        with tarfile.open(sdist, "r:gz") as archive:
            relative_members = {
                Path(member.name).relative_to("htt-8.3.0").as_posix()
                for member in archive.getmembers()
                if member.name != "htt-8.3.0"
            }
        allowed_sdist = {
            "MANIFEST.in",
            "PKG-INFO",
            "README.md",
            "htt.egg-info",
            "htt.egg-info/PKG-INFO",
            "htt.egg-info/SOURCES.txt",
            "htt.egg-info/dependency_links.txt",
            "htt.egg-info/requires.txt",
            "htt.egg-info/top_level.txt",
            "pyproject.toml",
            "setup.cfg",
            "setup.py",
        }
        assert relative_members <= allowed_sdist
        assert not any("tests" in Path(name).parts for name in relative_members)
        assert not any(name.startswith("htt/") for name in relative_members)

        editable = next(dist.glob("htt-8.3.0-0.editable-*.whl"))
        with zipfile.ZipFile(editable) as archive:
            editable_names = archive.namelist()
            finder_name = next(name for name in editable_names if name.endswith("_finder.py"))
            pth_name = next(name for name in editable_names if name.endswith(".pth"))
            finder_source = archive.read(finder_name).decode("utf-8")
            pth_source = archive.read(pth_name).decode("utf-8")
        assert editable_names
        assert all(
            ".dist-info/" in name or name in {finder_name, pth_name}
            for name in editable_names
        )
        assert "MAPPING: dict[str, str] = {}" in finder_source
        assert "NAMESPACES: dict[str, list[str]] = {}" in finder_source
        assert str(project.resolve()) not in finder_source
        assert str(project.resolve()) not in pth_source
        finder_module = Path(finder_name).stem
        assert pth_source == f"import {finder_module}; {finder_module}.install()"


def test_repo_root_import_surface_without_pythonpath() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import importlib
for name in [
    "htt",
    "htt.metamorphic_symmetry",
    "obsstat.cf4_velocity_estimators",
    "obsstat.cf4_forward_simulator",
    "obsstat.cf4_identified_set",
    "obsstat.cf4_growth_covariance",
    "bass.pr184_axisym_contract",
    "htt.infer",
    "htt.infer.loocv",
    "htt.infer.finite_mock",
    "htt.infer.fisher_compression",
    "htt.infer.nuisance_rank",
    "htt.infer.posterior_predictive",
    "htt.infer.prior_sweep",
    "htt.nulls",
    "htt.nulls.selection_response_depth",
    "htt.nulls.survey_axis_coherence",
    "htt.core",
    "htt.departure",
    "htt.departure.local_global_mixture",
    "htt.departure.posterior_pushforward",
    "htt.departure.response_overlap",
    "htt.departure.velocity_frame_decomposition",
    "htt.direction",
    "htt.obsstat",
    "htt.obsstat.biposh_features",
    "htt.obsstat.catalogs.cf4",
    "htt.obsstat.catalogs.redshift_selection",
    "htt.obsstat.catalogs.spectroscopic_dipole",
    "htt.obsstat.morphology",
    "htt.obsstat.null_ensembles",
    "htt.obsstat.observable_vector",
    "htt.obsstat.scalar_lowell",
    "htt.obsstat.template_fit",
    "htt.statistics",
    "htt.statistics.anchored_response_geometry",
    "htt.statistics.mes_cov_bound",
    "htt.statistics.mes_information_gain",
    "htt.statistics.mes_information_gain_compatibility",
    "htt.statistics.mes_template_bound",
    "htt.rest_frame",
    "htt.rest_frame.cf4_likelihood",
    "htt.rest_frame.cross_survey_covariance",
    "htt.rest_frame.joint_model",
    "htt.rest_frame.validation",
    "htt.zoa",
    "htt.zoa.axis_promotion",
    "htt.mio.formalism.isotropy_gap",
    "mio.formalism.bound_pushforward",
    "mio.formalism.dynamic_budget",
    "bass",
    "bass.atlas",
    "bass.atlas.atlas_entry",
    "bass.atlas.budget_ceiling_optimizer",
    "bass.geometry",
    "bass.geometry.egs_rigidity",
    "bass.kinetic",
    "bass.kinetic.boltzmann_memory",
    "bass.kinetic.tight_coupling_bounds",
    "bass.kinetic.visibility_rigidity",
    "bass.transfer.native_adapter",
    "bass.transfer.evidence_stability",
    "bass.transfer.native_schema",
    "common",
    "common.data_contracts",
    "common.semantic_guards.admissibility_status",
    "common.semantic_guards.source_propagation_status",
    "common.theorem_registry",
    "mio",
    "mio.formalism.channel_occupancy_vector",
    "mio.formalism.isotropy_gap",
    "mio.reports.departure_report",
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
    "htt.metamorphic_symmetry",
    "obsstat.cf4_velocity_estimators",
    "obsstat.cf4_forward_simulator",
    "obsstat.cf4_identified_set",
    "obsstat.cf4_growth_covariance",
    "bass.pr184_axisym_contract",
    "htt.core",
    "htt.departure",
    "htt.departure.local_global_mixture",
    "htt.departure.posterior_pushforward",
    "htt.departure.response_overlap",
    "htt.departure.velocity_frame_decomposition",
    "htt.direction",
    "htt.infer",
    "htt.infer.loocv",
    "htt.infer.finite_mock",
    "htt.infer.fisher_compression",
    "htt.infer.nuisance_rank",
    "htt.infer.posterior_predictive",
    "htt.infer.prior_sweep",
    "htt.nulls",
    "htt.nulls.clustering_dipole_depth",
    "htt.nulls.local_boost_depth_null",
    "htt.nulls.selection_response_depth",
    "htt.nulls.survey_axis_coherence",
    "htt.obsstat",
    "htt.obsstat.biposh_features",
    "htt.obsstat.catalogs.cf4",
    "htt.obsstat.catalogs.redshift_selection",
    "htt.obsstat.catalogs.spectroscopic_dipole",
    "htt.obsstat.morphology",
    "htt.obsstat.null_ensembles",
    "htt.obsstat.observable_vector",
    "htt.obsstat.scalar_lowell",
    "htt.obsstat.template_fit",
    "htt.statistics",
    "htt.statistics.anchored_response_geometry",
    "htt.statistics.mes_cov_bound",
    "htt.statistics.mes_information_gain",
    "htt.statistics.mes_information_gain_compatibility",
    "htt.statistics.mes_template_bound",
    "htt.rest_frame",
    "htt.rest_frame.cf4_likelihood",
    "htt.rest_frame.cross_survey_covariance",
    "htt.rest_frame.joint_model",
    "htt.rest_frame.validation",
    "htt.zoa",
    "htt.zoa.axis_promotion",
    "htt.integration.to_mio",
    "bass",
    "bass.atlas",
    "bass.atlas.atlas_entry",
    "bass.atlas.budget_ceiling_optimizer",
    "bass.geometry",
    "bass.geometry.egs_rigidity",
    "bass.kinetic",
    "bass.kinetic.boltzmann_memory",
    "bass.kinetic.tight_coupling_bounds",
    "bass.kinetic.visibility_rigidity",
    "bass.transfer.native_adapter",
    "bass.transfer.evidence_stability",
    "bass.transfer.native_schema",
    "common",
    "common.data_contracts",
    "common.semantic_guards.admissibility_status",
    "common.semantic_guards.source_propagation_status",
    "common.theorem_registry",
    "mio",
    "mio.formalism.bound_pushforward",
    "mio.formalism.dynamic_budget",
    "mio.formalism.channel_occupancy_vector",
    "mio.formalism.isotropy_gap",
    "mio.reports.departure_report",
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
for name in [
    "htt.departure.response_overlap",
    "htt.departure.local_global_mixture",
    "htt.departure.posterior_pushforward",
    "htt.departure.velocity_frame_decomposition",
    "htt.infer.finite_mock",
    "htt.infer.fisher_compression",
    "htt.infer.nuisance_rank",
    "htt.direction",
    "htt.statistics.anchored_response_geometry",
    "htt.statistics.mes_cov_bound",
    "htt.statistics.mes_information_gain",
    "htt.statistics.mes_information_gain_compatibility",
    "htt.statistics.mes_template_bound",
    "htt.obsstat.catalogs.redshift_selection",
    "htt.obsstat.catalogs.spectroscopic_dipole",
    "htt.rest_frame.cf4_likelihood",
    "htt.rest_frame.cross_survey_covariance",
    "htt.rest_frame.joint_model",
    "htt.rest_frame.validation",
    "htt.nulls.local_boost_depth_null",
    "htt.nulls.selection_response_depth",
    "htt.nulls.survey_axis_coherence",
    "htt.zoa.axis_promotion",
    "common.contracts",
    "common.data_contracts",
    "bass.transfer.evidence_stability",
    "mio.formalism.channel_occupancy_vector",
]:
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
assert "departure" in namespace
assert "statistics" in namespace
assert "zoa" in namespace
assert "rest_frame" in namespace
import htt.departure.response_overlap
import htt.departure.local_global_mixture
import htt.departure.posterior_pushforward
import htt.departure.velocity_frame_decomposition
import htt.direction
import htt.statistics.anchored_response_geometry
import htt.statistics.mes_cov_bound
import htt.statistics.mes_information_gain
import htt.statistics.mes_information_gain_compatibility
import htt.statistics.mes_template_bound
import htt.rest_frame.cf4_likelihood
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


def test_top_level_compatibility_aliases_preserve_identity_across_cwds() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import importlib
import htt

assert htt.__version__ == "8.3.0"
for name in ("bass", "obsstat", "mio", "tsc_legacy", "tsc", "teff", "workspace"):
    canonical = importlib.import_module(name)
    compatibility = importlib.import_module(f"htt.{name}")
    assert compatibility is canonical, name

for name in ("obsstat.scalar_lowell", "teff.representative", "tsc.contracts"):
    canonical = importlib.import_module(name)
    compatibility = importlib.import_module(f"htt.{name}")
    assert compatibility is canonical, name
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        for cwd in (REPO_ROOT, Path(tmpdir)):
            completed = subprocess.run(
                [sys.executable, "-c", code],
                cwd=cwd,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr


def test_deep_compatibility_aliases_preserve_identity_and_metadata_both_orders() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    pairs = (
        (
            "bass.transfer.shear_quadrupole_seminative",
            "htt.bass.transfer.shear_quadrupole_seminative",
        ),
        ("obsstat.velocity_power", "htt.obsstat.velocity_power"),
        ("mio.formalism.dynamic_budget", "htt.mio.formalism.dynamic_budget"),
        ("teff.transport_application", "htt.teff.transport_application"),
        (
            "tsc.admissibility.three_bound_hierarchy",
            "htt.tsc.admissibility.three_bound_hierarchy",
        ),
        ("workspace.contracts", "htt.workspace.contracts"),
    )
    code_template = """
import importlib
import sys

pairs = {pairs!r}
for canonical_name, alias_name in pairs:
    assert canonical_name not in sys.modules
    assert alias_name not in sys.modules
    first_name, second_name = (
        (canonical_name, alias_name)
        if {canonical_first!r}
        else (alias_name, canonical_name)
    )
    first = importlib.import_module(first_name)
    second = importlib.import_module(second_name)
    assert first is second, (canonical_name, first, second)
    assert first.__name__ == canonical_name
    assert first.__spec__ is not None
    assert first.__spec__.name == canonical_name
    assert first.__loader__ is first.__spec__.loader
    expected_package = (
        canonical_name
        if hasattr(first, "__path__")
        else canonical_name.rpartition(".")[0]
    )
    assert first.__package__ == expected_package
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        for cwd in (REPO_ROOT, Path(tmpdir)):
            for canonical_first in (True, False):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        code_template.format(
                            pairs=pairs,
                            canonical_first=canonical_first,
                        ),
                    ],
                    cwd=cwd,
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                assert completed.returncode == 0, completed.stderr


def test_deep_alias_finder_is_lazy_and_scoped_to_declared_htt_prefixes() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import sys
import htt

unrequested = (
    "bass.transfer.shear_quadrupole_seminative",
    "obsstat.velocity_power",
    "mio.formalism.dynamic_budget",
    "teff.transport_application",
    "tsc.admissibility.three_bound_hierarchy",
    "workspace.contracts",
)
for canonical_name in unrequested:
    assert canonical_name not in sys.modules
    assert f"htt.{canonical_name}" not in sys.modules

finders = [
    finder
    for finder in sys.meta_path
    if getattr(finder, "_htt_compat_alias_prefixes", None)
]
assert len(finders) == 1
finder = finders[0]
assert finder.find_spec("json") is None
assert finder.find_spec("htt.core") is None
assert finder.find_spec("mio.formalism.dynamic_budget") is None
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        for cwd in (REPO_ROOT, Path(tmpdir)):
            completed = subprocess.run(
                [sys.executable, "-c", code],
                cwd=cwd,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr


def test_teff_import_surface_is_tsc_legacy_reproduction_only() -> None:
    import htt.teff as compatibility
    import teff as canonical

    assert compatibility is canonical
    assert canonical.TEFF_LEGACY_IMPORT_COMPATIBLE is True
    assert canonical.TEFF_ACTIVE_SCIENCE_OWNER is False
    assert canonical.TEFF_OWNER == "TSC_LEGACY"
    assert canonical.TEFF_IMPLEMENTATION_SCOPE == "tsc_legacy"
    assert canonical.TEFF_CLAIM_TIER == "diagnostic_only"
    assert canonical.TEFF_BUNDLE_KIND == "legacy_reproduction"
    assert canonical.TEFF_DEPRECATION_STATUS == "legacy_reproduction_only"
    assert "not current-owner artifacts" in canonical.TEFF_DEPRECATION_CAVEAT


def test_import_htt_has_no_optional_science_dependency_or_cwd_side_effect() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import importlib.abc
import os
import sys
from pathlib import Path

blocked = {"camb", "dynesty", "healpy", "jax"}
class OptionalScienceDependencyBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition(".")[0] in blocked:
            raise ModuleNotFoundError(f"blocked optional dependency: {fullname}")
        return None

sys.meta_path.insert(0, OptionalScienceDependencyBlocker())
before = tuple(Path.cwd().iterdir())
path_before = tuple(sys.path)
pipeline_outdir_before = os.environ.get("HTT_PIPELINE_OUTDIR")
import htt
after = tuple(Path.cwd().iterdir())
assert before == after == ()
assert tuple(sys.path) == path_before
assert os.environ.get("HTT_PIPELINE_OUTDIR") == pipeline_outdir_before
assert htt.__version__ == "8.3.0"
assert "htt.figures" not in sys.modules
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


def test_packaged_resources_and_consumers_work_outside_repo_cwd() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
from importlib import resources

from htt.core.ssot import load_obs
from obsstat.velocity_power import fiducial

expected = (
    ("bass.recombination", ("fixtures", "recombination_ref_planck2018.csv")),
    ("bass.validation", ("_d2_anchor_golden.json",)),
    ("htt.tests", ("fixtures", "pipeline_outputs", "IS06_3D_posterior.npz")),
    ("workspace", ("data", "obs_defaults.json")),
)
for package, parts in expected:
    resource = resources.files(package)
    for part in parts:
        resource = resource.joinpath(part)
    assert resource.is_file(), (package, parts)

obs = load_obs()
fid = fiducial()
assert float(obs["Omega_m"]) == fid["om"]
assert float(obs["h"]) == fid["h"]
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


def test_active_sources_use_canonical_bass_imports() -> None:
    active_consumers = [
        "htt/bass/transfer/visibility_camb_crosscheck.py",
        "htt/obsstat/egs3_psd_cone.py",
        "htt/obsstat/joint_pv_cmb_forecast.py",
        "research_gates/egs2/tests/test_egs2_camb_crosscheck.py",
        "research_gates/egs3/tests/test_egs3_axis_b.py",
        "scripts/make_egs2_egs3_theorem_figures.py",
        "scripts/run_egs2_camb_crosscheck_seal.py",
        "scripts/run_egs3_experiments.py",
        "tests/contracts/test_egs3_extension.py",
    ]

    for relative_path in active_consumers:
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "htt.bass" not in source, relative_path


def test_obsstat_joint_forecast_import_does_not_boot_bass() -> None:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = """
import sys

import obsstat

assert not any(name == "bass" or name.startswith("bass.") for name in sys.modules)

from obsstat import joint_pv_cmb_forecast as forecast

assert not any(name == "bass" or name.startswith("bass.") for name in sys.modules)
assert forecast.OutOfScopeError.__module__ == "obsstat.joint_pv_cmb_forecast"
try:
    forecast.anisotropic_cmb_covariance({}, l_max=3)
except forecast.OutOfScopeError:
    pass
else:
    raise AssertionError("blocked theory path did not fail closed")
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code],
            cwd=tmpdir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    assert completed.returncode == 0, completed.stderr


def test_legacy_teff_consumers_are_not_canonicalized_into_an_active_owner() -> None:
    legacy_reproduction_consumers = [
        "htt/obsstat/egs3_fingerprint_sum_theorem.py",
        "htt/obsstat/egs3_teff_statistical.py",
        "htt/obsstat/egs3_teff_unification.py",
        "htt/obsstat/egs3_unification_schema.py",
        "research_gates/teff/tests/test_teff_representative.py",
        "research_gates/teff/tests/test_teff_transport_parity.py",
        "scripts/make_egs2_egs3_theorem_figures.py",
        "scripts/run_egs3_v7_seals.py",
        "scripts/run_egs3_v9_seals.py",
    ]

    for relative_path in legacy_reproduction_consumers:
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "htt.teff" in source, relative_path
        assert re.search(
            r"(?m)^\s*(?:from|import)\s+teff(?:\.|\s|$)", source
        ) is None, relative_path
