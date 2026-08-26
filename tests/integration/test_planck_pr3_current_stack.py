from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

import healpy as hp
import numpy as np
import pytest

from obsstat.planck_pr3_operator import build_joint_cutsky_operator


def _worker():
    return importlib.import_module("scripts.observed_runs.run_planck_pr3")


def _context():
    worker = _worker()
    nside = 8
    mask = np.ones(hp.nside2npix(nside))
    mask[:24] = 0.0
    beam = np.linspace(1.0, 0.91, 6)
    pixel = np.asarray(hp.pixwin(nside, lmax=5), dtype=float)
    return worker.build_smica_joint_cutsky_context(
        smica_map=np.zeros(mask.size),
        mask=mask,
        beam=beam,
        window={
            "source_pixel_window": pixel,
            "target_beam": beam,
            "target_pixel_window": pixel,
        },
        declared_nside=nside,
    )


def test_observation_and_null_joint_operator_identity_is_exact() -> None:
    worker = _worker()
    context = _context()
    observed = worker.joint_cutsky_operator_identity(context)
    null = worker.joint_cutsky_operator_identity(context)
    assert observed == null
    assert observed["estimator_id"] == worker.PR315_JOINT_CUTSKY_ESTIMATOR_ID
    assert observed["basis_dimension"] == 36
    assert observed["retained_dimension"] == 32

    changed = dict(null)
    changed["normal_matrix_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(worker.PlanckWorkerError, match="operator identity"):
        worker.require_observation_null_operator_identity(observed, changed)


def test_partial_or_mismatched_rerun_emits_no_result() -> None:
    worker = _worker()
    rng = np.random.default_rng(324_001)
    with pytest.raises(worker.PlanckWorkerError, match="exact 300"):
        worker.analyze_smica_feature_rows(
            observed_features=rng.normal(size=12),
            null_features=rng.normal(size=(299, 12)),
            row_ids=worker.SMICA_EXISTING_ROW_IDS[:-1],
        )
    with pytest.raises(worker.PlanckWorkerError, match="row identity"):
        worker.analyze_smica_feature_rows(
            observed_features=rng.normal(size=12),
            null_features=rng.normal(size=(300, 12)),
            row_ids=tuple(reversed(worker.SMICA_EXISTING_ROW_IDS)),
        )


def test_portable_feature_package_recomputes_exact_result(tmp_path: Path) -> None:
    worker = _worker()
    rng = np.random.default_rng(324_002)
    observed = rng.normal(size=12)
    nulls = rng.normal(size=(300, 12))
    package = tmp_path / "features.npz"
    metadata = tmp_path / "features.json"
    result = worker.analyze_smica_feature_rows(
        observed_features=observed,
        null_features=nulls,
        row_ids=worker.SMICA_EXISTING_ROW_IDS,
    )
    worker.write_pr315_feature_package(
        package_path=package,
        metadata_path=metadata,
        observed_features=observed,
        null_features=nulls,
        row_ids=worker.SMICA_EXISTING_ROW_IDS,
        operator_identity=worker.joint_cutsky_operator_identity(_context()),
    )

    replay = worker.replay_pr315_feature_package(
        package_path=package,
        metadata_path=metadata,
    )
    assert replay["finite_feature_family_p"] == result["finite_feature_family_p"]
    assert replay["local_feature_p"] == result["local_feature_p"]
    assert replay["scientific_projection_sha256"].startswith("sha256:")

    with np.load(package, allow_pickle=False) as bundle:
        rows = {key: np.asarray(bundle[key]).copy() for key in bundle.files}
    rows["null_features"][9, 4] += 0.25
    np.savez(package, **rows)
    with pytest.raises(worker.PlanckWorkerError, match="package hash"):
        worker.replay_pr315_feature_package(
            package_path=package,
            metadata_path=metadata,
        )


def test_branch_and_tail_registry_are_frozen_before_rerun() -> None:
    worker = _worker()
    registry = worker.pr315_branch_tail_registry()
    validated = worker.validate_pr315_branch_tail_registry(registry)
    assert validated["benchmark_control"]["result_sha256"] == (
        "sha256:898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97"
    )
    assert validated["joint_cutsky"]["role"] == "PREDECLARED_ROBUSTNESS_BRANCH"
    assert validated["tails"] == ["two-sided"] * 12

    changed = deepcopy(registry)
    changed["tails"][0] = "upper"
    with pytest.raises(worker.PlanckWorkerError, match="branch/tail registry"):
        worker.validate_pr315_branch_tail_registry(changed)


def test_joint_context_rejects_sequential_mask_inverse_substitution() -> None:
    worker = _worker()
    context = _context()
    assert context["joint_cutsky_operator"].dimension == 36
    sequential = build_joint_cutsky_operator(
        context["common_mask"], lmin=2, lmax=5
    )
    changed = dict(context)
    changed["joint_cutsky_operator"] = sequential
    with pytest.raises(worker.PlanckWorkerError, match="36-column"):
        worker.joint_cutsky_operator_identity(changed)


def test_frozen_pr314_133_of_301_control_is_preserved_in_comparison() -> None:
    worker = _worker()
    path = Path("docs/generated/pr314_planck_pr3_smica_existing_result.json")
    raw = path.read_bytes()
    assert "sha256:" + hashlib.sha256(raw).hexdigest() == (
        worker.PR314_FROZEN_RESULT_SHA256
    )
    benchmark = json.loads(raw)
    comparison = worker.compare_pr314_pr315_results(
        benchmark=benchmark, joint=benchmark
    )
    assert comparison["benchmark_family_rank"] == "133/301"
    assert comparison["joint_cutsky_family_rank"] == "133/301"
    assert comparison["generic_control_preserved"] is True
    assert comparison["MES_result"] is False
    assert len(comparison["feature_rows"]) == 12


def test_committed_pr315_feature_replay_is_map_free_and_exact() -> None:
    worker = _worker()
    generated = Path("docs/generated")
    package = generated / "pr315_planck_smica_feature_replay.npz"
    metadata = generated / "pr315_planck_smica_feature_replay.json"
    result_path = generated / "pr315_planck_smica_result.json"
    replay = worker.replay_pr315_feature_package(
        package_path=package, metadata_path=metadata
    )
    result = json.loads(result_path.read_text(encoding="ascii"))

    assert replay["raw_maps_reopened"] is False
    assert replay["scientific_projection_sha256"] == (
        result["portable_replay_scientific_projection_sha256"]
    )
    assert replay["feature_package_sha256"] == (
        result["feature_package"]["package_sha256"]
    )
    assert result["source_execution_result_sha256"] == (
        "sha256:e80865e8e48ff49fe72d8db40952cc1598768081526eeac30b63e6308f03a15e"
    )
    assert result["PR314_benchmark_family_rank"] == "133/301"
    assert result["PR315_joint_cutsky_family_rank"] == "133/301"
    assert result["MES_result"] is False
    assert result["generic_control_preserved"] is True
    assert len(result["old_new_comparison"]["feature_rows"]) == 12
