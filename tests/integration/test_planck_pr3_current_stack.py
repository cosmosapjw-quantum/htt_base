from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import healpy as hp
import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "scripts/observed_runs/run_planck_pr3.py"


def test_direct_worker_context_can_import_the_preparer(tmp_path: Path) -> None:
    pythonpath = os.pathsep.join(
        str(ROOT / relative) for relative in ("htt", "htt/src", "htt/htt")
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                f"import runpy; runpy.run_path({str(WORKER)!r}, "
                "run_name='pr314_worker'); "
                "import scripts.observed_runs.prepare_planck_pr3_admission"
            ),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": pythonpath},
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


@pytest.mark.requires_healpy
def test_smica_only_context_and_complete_300_row_calibration_are_explicit() -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    nside = 8
    npix = hp.nside2npix(nside)
    mask = np.ones(npix)
    mask[:24] = np.linspace(0.2, 0.95, 24)
    beam = np.linspace(1.0, 0.91, 6)
    pixel = hp.pixwin(nside, lmax=5)
    context = worker.build_smica_operator_context(
        smica_map=np.zeros(npix),
        mask=mask,
        beam=beam,
        window={
            "source_pixel_window": pixel,
            "target_beam": beam,
            "target_pixel_window": pixel,
        },
        declared_nside=nside,
    )
    rng = np.random.default_rng(314)
    nulls = rng.normal(size=(300, 12))
    observed = rng.normal(size=12)

    result = worker.analyze_smica_feature_rows(
        observed_features=observed,
        null_features=nulls,
        row_ids=worker.SMICA_EXISTING_ROW_IDS,
    )

    assert context["pipeline_scope"] == "SMICA_ONLY"
    assert result["feature_order"] == list(worker.COMPONENT_FEATURE_IDS)
    assert result["covariance_rank"] == 12
    assert result["null_rows"] == 300
    assert result["resolution_floor"] == "1/301"
    assert result["commander_robustness"] == "NOT_EVALUATED"
    assert result["joint_covariance"] == "NOT_APPLICABLE_SMICA_ONLY"
    assert result["global_response_status"] == "MISSING"


def test_smica_only_partial_or_pooled_inventory_cannot_emit_a_p_value() -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    rng = np.random.default_rng(315)
    observed = rng.normal(size=12)
    nulls = rng.normal(size=(299, 12))
    partial = worker.SMICA_EXISTING_ROW_IDS[:-1]

    with pytest.raises(worker.PlanckWorkerError, match="exact 300"):
        worker.analyze_smica_feature_rows(
            observed_features=observed,
            null_features=nulls,
            row_ids=partial,
        )
    pooled = tuple(f"FFP10-CMB-ONLY-{index:05d}" for index in range(300))
    with pytest.raises(worker.PlanckWorkerError, match="row identity"):
        worker.analyze_smica_feature_rows(
            observed_features=observed,
            null_features=rng.normal(size=(300, 12)),
            row_ids=pooled,
        )


def test_smica_covariance_gate_is_invariant_to_feature_units() -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    rng = np.random.default_rng(316)
    observed = rng.normal(size=12)
    nulls = rng.normal(size=(300, 12))
    scales = np.geomspace(1.0e-3, 1.0e3, 12)

    baseline = worker.analyze_smica_feature_rows(
        observed_features=observed,
        null_features=nulls,
        row_ids=worker.SMICA_EXISTING_ROW_IDS,
    )
    rescaled = worker.analyze_smica_feature_rows(
        observed_features=observed * scales,
        null_features=nulls * scales,
        row_ids=worker.SMICA_EXISTING_ROW_IDS,
    )

    assert rescaled["covariance_condition_basis"] == "DIAGONAL_STANDARDIZED"
    assert rescaled["covariance_condition"] == pytest.approx(
        baseline["covariance_condition"], rel=1.0e-12
    )
    assert rescaled["finite_feature_family_p"] == baseline["finite_feature_family_p"]
    assert rescaled["local_feature_p"] == baseline["local_feature_p"]


def test_smica_attended_acceptance_is_exact_and_mismatch_precedes_start(
    tmp_path: Path,
) -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    observed = tmp_path / "COM_CMB_IQU-smica_2048_R3.00_full.fits"
    observed.write_bytes(b"identified-smica")
    components = {}
    for name in ("mask", "beam", "window", "null", "covariance", "selection"):
        path = tmp_path / f"{name}.bin"
        path.write_bytes(name.encode("ascii"))
        components[name] = {
            "path": str(path),
            "byte_size": path.stat().st_size,
            "sha256": worker._sha256_file(path),
        }
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "format": "PLANCK_PR3_SMICA_EXISTING_PLAN_V1",
                "pipeline_scope": "SMICA_ONLY",
                "release_identity": "Planck PR3 R3.00 plus FFP10 v3",
                "observed_smica": {
                    "path": str(observed),
                    "filename": observed.name,
                    "byte_size": observed.stat().st_size,
                },
                "components": components,
                "ordered_row_ids_sha256": worker.SMICA_EXISTING_INVENTORY_ID,
                "observed_temperature_payload_opened": False,
            }
        ),
        encoding="ascii",
    )
    output = tmp_path / "output"
    candidate_commit, candidate_tree = worker._current_git_identity()
    with pytest.raises(worker.PlanckWorkerError, match="current checkout"):
        worker.smica_existing_acceptance(
            plan_path=plan,
            output_dir=output,
            candidate_commit="a" * 40,
            candidate_tree=candidate_tree,
        )
    acceptance = worker.smica_existing_acceptance(
        plan_path=plan,
        output_dir=output,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )

    assert acceptance["acceptance_hash"].startswith("sha256:")
    with pytest.raises(worker.PlanckWorkerError, match="confirmation"):
        worker.run_smica_existing_attended(
            plan_path=plan,
            output_dir=output,
            candidate_commit=candidate_commit,
            candidate_tree=candidate_tree,
            confirmation="sha256:" + "0" * 64,
        )
    assert not output.exists()


@pytest.mark.requires_healpy
def test_smica_existing_attended_run_and_compact_replay_match(
    tmp_path: Path,
) -> None:
    preparer = importlib.import_module(
        "scripts.observed_runs.prepare_planck_pr3_admission"
    )
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    nside = 4
    npix = hp.nside2npix(nside)
    prepared = tmp_path / "prepared"
    components = prepared / "components"
    components.mkdir(parents=True)
    rng = np.random.default_rng(31_400)
    mask = np.ones(npix)
    mask[:16] = np.linspace(0.2, 0.95, 16)
    beam = np.linspace(1.0, 0.92, 6)
    pixel = hp.pixwin(nside, lmax=5)
    np.save(components / "smica_mask.npy", mask)
    np.save(components / "smica_beam.npy", beam)
    np.savez(
        components / "smica_window_operator.npz",
        source_pixel_window=pixel,
        target_beam=beam,
        target_pixel_window=pixel,
    )
    np.savez(
        components / "smica_ffp10_cmb_plus_noise_300.npz",
        row_ids=np.asarray(worker.SMICA_EXISTING_ROW_IDS),
        smica_maps=rng.normal(size=(300, npix)),
    )
    observed = tmp_path / "COM_CMB_IQU-smica_2048_R3.00_full.fits"
    hp.write_map(
        observed,
        rng.normal(scale=1.0e-6, size=npix),
        dtype=np.float64,
        nest=False,
        column_names=["I_STOKES"],
        column_units=["K_CMB"],
        extra_header=[("COORDSYS", "GALACTIC")],
        overwrite=True,
    )
    mask_source = tmp_path / "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
    mask_source.write_bytes(b"identified-mask-source")
    operator = preparer.write_smica_existing_operator_components(
        output_root=prepared,
        observed_smica=observed,
        temperature_mask=mask_source,
        output_nside=nside,
    )
    plan = Path(operator["plan_path"])
    output = tmp_path / "result"
    candidate_commit, candidate_tree = worker._current_git_identity()
    acceptance = worker.smica_existing_acceptance(
        plan_path=plan,
        output_dir=output,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )
    result = worker.run_smica_existing_attended(
        plan_path=plan,
        output_dir=output,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        confirmation=acceptance["acceptance_hash"],
    )
    replay = worker.replay_smica_existing_result(
        plan_path=plan,
        source_output_dir=output,
        replay_output=tmp_path / "replay.json",
    )

    assert result["pipeline_scope"] == "SMICA_ONLY"
    assert result["null_rows"] == 300
    assert result["resolution_floor"] == "1/301"
    assert json.loads((output / "terminal.json").read_text())["state"] == "SUCCEEDED"
    assert replay["state"] == "REPLAY_MATCH"
    assert replay["observed_raw_reopened"] is False
