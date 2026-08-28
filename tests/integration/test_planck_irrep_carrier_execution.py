from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest

from obsstat.planck_irrep_carrier import (
    EXPECTED_DIMENSION,
    EXPECTED_NULL_ROWS,
    PlanckIrrepCarrierError,
    scalar_feature_closure_report,
)
from obsstat.planck_paired300_carrier_execution import (
    Paired300ExecutionError,
    capture_regular_file_identity,
    expected_paired300_row_ids,
    process_paired300_rows_one_pass,
    require_regular_file_identity_unchanged,
)
from scripts.observed_runs.export_planck_paired300_irrep_carrier import (
    CarrierExportError,
    _execute_leakage_probes,
    _leakage_operator_identity_from_metadata,
    evaluate_fixed_leakage_probes,
    fixed_leakage_probe_layout,
    load_private_row_checkpoint,
    replay_committed,
    validate_portable_completion,
    write_private_row_checkpoint,
)


def _rows() -> tuple[str, ...]:
    return expected_paired300_row_ids()


def _process_factory(calls: list[int]):
    def process_map(pixel_map, *, component, context):
        assert component == "SMICA"
        assert context == {"operator": "frozen"}
        value = int(np.asarray(pixel_map)[0])
        calls.append(value)
        features = np.arange(12, dtype=np.float64) + value
        alm = np.arange(EXPECTED_DIMENSION, dtype=np.float64) + 1000.0 * value
        return features, {"fit": 1.0}, alm

    return process_map


def _carrier_from_alm(value) -> np.ndarray:
    return np.asarray(value, dtype=np.float64)


def test_one_pass_execution_preserves_exact_order_and_calls_each_row_once() -> None:
    calls: list[int] = []
    rows = _rows()
    result = process_paired300_rows_one_pass(
        observed_map=np.asarray([-1.0]),
        null_rows=(
            (row_id, np.asarray([index], dtype=np.float64))
            for index, row_id in enumerate(rows)
        ),
        context={"operator": "frozen"},
        process_map=_process_factory(calls),
        carrier_from_alm=_carrier_from_alm,
    )
    assert calls == [-1, *range(EXPECTED_NULL_ROWS)]
    assert result.row_ids == ("PLANCK-PR3-SMICA-OBSERVED", *rows)
    assert result.observed_features.shape == (12,)
    assert result.null_features.shape == (300, 12)
    assert result.observed_real_alm.shape == (32,)
    assert result.null_real_alm.shape == (300, 32)
    assert np.array_equal(result.null_features[:, 0], np.arange(300))
    assert np.array_equal(result.null_real_alm[:, 0], 1000.0 * np.arange(300))


@pytest.mark.parametrize(
    "rows",
    [
        lambda values: values[:-1],
        lambda values: (values[1], values[0], *values[2:]),
        lambda values: (*values[:-1], values[-2]),
    ],
)
def test_one_pass_execution_rejects_missing_reordered_or_duplicate_rows(rows) -> None:
    identifiers = rows(_rows())
    with pytest.raises(Paired300ExecutionError, match="exact registered order"):
        process_paired300_rows_one_pass(
            observed_map=np.asarray([-1.0]),
            null_rows=(
                (row_id, np.asarray([index]))
                for index, row_id in enumerate(identifiers)
            ),
            context={"operator": "frozen"},
            process_map=_process_factory([]),
            carrier_from_alm=_carrier_from_alm,
        )


def test_one_pass_execution_rejects_bad_feature_or_carrier_shape() -> None:
    rows = _rows()

    def bad_process(pixel_map, *, component, context):
        value = int(np.asarray(pixel_map)[0])
        features = np.zeros(11 if value == 17 else 12, dtype=np.float64)
        carrier = np.zeros(EXPECTED_DIMENSION, dtype=np.float64)
        return features, {}, carrier

    with pytest.raises(Paired300ExecutionError, match="feature shape"):
        process_paired300_rows_one_pass(
            observed_map=np.asarray([-1.0]),
            null_rows=(
                (row_id, np.asarray([index]))
                for index, row_id in enumerate(rows)
            ),
            context={"operator": "frozen"},
            process_map=bad_process,
            carrier_from_alm=_carrier_from_alm,
        )


def test_worker_compact_null_path_preserves_carrier_in_the_same_fit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    rows = worker.SMICA_EXISTING_ROW_IDS
    path = tmp_path / "nulls.npz"
    maps = np.arange(EXPECTED_NULL_ROWS, dtype=np.float64).reshape(-1, 1)
    np.savez(path, row_ids=np.asarray(rows, dtype="U27"), smica_maps=maps)
    calls: list[int] = []

    def fake_process(pixel_map, *, component, context):
        assert component == "SMICA"
        assert context == {"operator": "frozen"}
        value = int(np.asarray(pixel_map)[0])
        calls.append(value)
        features = np.arange(12, dtype=np.float64) + value
        vector = np.arange(EXPECTED_DIMENSION, dtype=np.float64) + 1000.0 * value
        alm = worker.real_vector_to_alm(vector, lmin=2, lmax=5)
        return features, {"fit": 1.0}, alm

    monkeypatch.setattr(worker, "_process_map", fake_process)
    features, carrier = worker._process_ffp10_component_with_carrier(
        path,
        array_name="smica_maps",
        row_ids=rows,
        component="SMICA",
        context={"operator": "frozen"},
        chunk_rows=37,
    )
    assert calls == list(range(EXPECTED_NULL_ROWS))
    assert features.shape == (300, 12)
    assert carrier.shape == (300, 32)
    assert np.array_equal(features[:, 0], np.arange(300))
    assert np.array_equal(carrier[:, 0], 1000.0 * np.arange(300))


def test_carrier_feature_projection_roundtrip_is_exact() -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    vector = np.linspace(-0.5, 0.5, EXPECTED_DIMENSION, dtype=np.float64)
    projected = worker._component_features_from_real_carrier(vector)
    alm = worker.real_vector_to_alm(vector, lmin=2, lmax=5)
    vectors2 = worker.extract_multipole_vectors(alm, ell=2, lmax=5)
    vectors3 = worker.extract_multipole_vectors(alm, ell=3, lmax=5)
    expected = worker.component_features_from_vectors(
        alm,
        vectors2=vectors2,
        vectors3=vectors3,
        lmax=5,
    )
    assert np.array_equal(projected, expected)


def test_same_operator_identity_is_required_for_observation_and_null() -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    identity = {
        "estimator_id": "joint",
        "mask_sha256": "sha256:" + "a" * 64,
    }
    assert worker.require_observation_null_operator_identity(identity, identity).startswith(
        "sha256:"
    )
    with pytest.raises(worker.PlanckWorkerError, match="operator identity mismatch"):
        worker.require_observation_null_operator_identity(
            identity,
            {**identity, "mask_sha256": "sha256:" + "b" * 64},
        )


def test_scalar_feature_closure_refuses_forged_carrier_projection() -> None:
    observed = np.arange(12, dtype=np.float64)
    nulls = np.tile(observed, (EXPECTED_NULL_ROWS, 1))
    report = scalar_feature_closure_report(
        observed_expected=observed,
        observed_projected=observed.copy(),
        null_expected=nulls,
        null_projected=nulls.copy(),
    )
    assert report["state"] == "MATCH"
    forged = observed.copy()
    forged[-1] += 1.0e-6
    with pytest.raises(PlanckIrrepCarrierError, match="differ"):
        scalar_feature_closure_report(
            observed_expected=observed,
            observed_projected=forged,
            null_expected=nulls,
            null_projected=nulls,
        )


def test_regular_file_identity_detects_content_and_stat_mutation(tmp_path: Path) -> None:
    source = tmp_path / "source.fits"
    source.write_bytes(b"authority")
    before = capture_regular_file_identity(source, hash_content=True)
    assert require_regular_file_identity_unchanged(source, before) == before
    source.write_bytes(b"mutation")
    with pytest.raises(Paired300ExecutionError, match="mutated"):
        require_regular_file_identity_unchanged(source, before)


def test_regular_file_identity_refuses_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source.fits"
    source.write_bytes(b"authority")
    link = tmp_path / "link.fits"
    link.symlink_to(source)
    with pytest.raises(Paired300ExecutionError, match="regular non-symlink"):
        capture_regular_file_identity(link, hash_content=True)


def test_fixed_leakage_probes_are_preregistered_and_use_one_operator_fit() -> None:
    probes = fixed_leakage_probe_layout()
    expected = tuple(
        (ell, m, component)
        for ell in (6, 7)
        for m in range(ell + 1)
        for component in (("real",) if m == 0 else ("real", "imag"))
    )
    assert probes == expected
    calls: list[tuple[int, int, str]] = []

    def fit_probe(ell: int, m: int, component: str) -> np.ndarray:
        calls.append((ell, m, component))
        value = ell * 100 + m * 10 + (component == "imag")
        return np.full(EXPECTED_DIMENSION, value, dtype=np.float64)

    receipt = evaluate_fixed_leakage_probes(
        operator_identity_sha256="sha256:" + "a" * 64,
        fit_probe=fit_probe,
    )
    assert calls == list(expected)
    assert receipt["probe_definition"] == "COMPLETE_REAL_BASIS_ELL6_ELL7_V1"
    assert receipt["probe_count"] == 28
    assert receipt["operator_identity_sha256"] == "sha256:" + "a" * 64
    assert receipt["correction_applied"] is False
    assert receipt["claim_promotion"] is False
    assert np.asarray(receipt["retained_real_alm"]).shape == (28, 32)


def test_fixed_leakage_probes_reject_wrong_carrier_shape() -> None:
    with pytest.raises(CarrierExportError, match="32-real carrier"):
        evaluate_fixed_leakage_probes(
            operator_identity_sha256="sha256:" + "a" * 64,
            fit_probe=lambda ell, m, component: np.zeros(31, dtype=np.float64),
        )


def test_fixed_leakage_probes_run_through_the_actual_joint_operator() -> None:
    hp = pytest.importorskip("healpy")
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    nside = 4
    pixel_count = hp.nside2npix(nside)
    beam = np.ones(worker.LMAX + 1, dtype=np.float64)
    pixel = np.asarray(hp.pixwin(nside, lmax=worker.LMAX), dtype=np.float64)
    context = worker.build_smica_joint_cutsky_context(
        smica_map=np.zeros(pixel_count, dtype=np.float64),
        mask=np.ones(pixel_count, dtype=np.float64),
        beam=beam,
        window={
            "source_pixel_window": pixel,
            "target_beam": beam,
            "target_pixel_window": pixel,
        },
        declared_nside=nside,
    )
    operator = worker.joint_cutsky_operator_identity(context)
    operator_id = worker.require_observation_null_operator_identity(
        operator, operator
    )
    receipt = _execute_leakage_probes(
        context=context,
        operator_identity_sha256=operator_id,
    )
    assert receipt["probe_count"] == 28
    assert np.asarray(receipt["retained_real_alm"]).shape == (28, 32)


def test_leakage_replay_uses_the_pr315_operator_hash_role() -> None:
    worker = importlib.import_module("scripts.observed_runs.run_planck_pr3")
    operator = {
        "estimator_id": "joint",
        "operator_sha256": "sha256:" + "a" * 64,
    }
    expected = worker.require_observation_null_operator_identity(operator, operator)
    metadata = {
        "operator_identity": operator,
        "operator_identity_sha256": "sha256:" + "b" * 64,
    }
    assert _leakage_operator_identity_from_metadata(metadata) == expected
    assert expected != metadata["operator_identity_sha256"]


def test_private_checkpoint_binds_row_order_operator_and_raw_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.fits"
    source.write_bytes(b"raw-authority")
    source_identity = capture_regular_file_identity(source, hash_content=True)
    checkpoint = tmp_path / "row-00017.npz"
    operator_id = "sha256:" + "b" * 64
    row_id = _rows()[17]
    features = np.arange(12, dtype=np.float64)
    carrier = np.arange(EXPECTED_DIMENSION, dtype=np.float64)
    write_private_row_checkpoint(
        path=checkpoint,
        ordinal=18,
        row_id=row_id,
        features=features,
        carrier=carrier,
        source_identities=(source_identity,),
        operator_identity_sha256=operator_id,
    )
    loaded = load_private_row_checkpoint(
        path=checkpoint,
        expected_ordinal=18,
        expected_row_id=row_id,
        expected_source_identities=(source_identity,),
        expected_operator_identity_sha256=operator_id,
    )
    assert np.array_equal(loaded["features"], features)
    assert np.array_equal(loaded["carrier"], carrier)

    with pytest.raises(CarrierExportError, match="row identity"):
        load_private_row_checkpoint(
            path=checkpoint,
            expected_ordinal=19,
            expected_row_id=row_id,
            expected_source_identities=(source_identity,),
            expected_operator_identity_sha256=operator_id,
        )
    source.write_bytes(b"mutated")
    mutated_identity = capture_regular_file_identity(source, hash_content=True)
    with pytest.raises(CarrierExportError, match="source identity"):
        load_private_row_checkpoint(
            path=checkpoint,
            expected_ordinal=18,
            expected_row_id=row_id,
            expected_source_identities=(mutated_identity,),
            expected_operator_identity_sha256=operator_id,
        )


def test_private_checkpoint_rejects_decoded_payload_mutation(tmp_path: Path) -> None:
    source = tmp_path / "source.fits"
    source.write_bytes(b"raw-authority")
    source_identity = capture_regular_file_identity(source, hash_content=True)
    checkpoint = tmp_path / "row-00017.npz"
    operator_id = "sha256:" + "b" * 64
    row_id = _rows()[17]
    features = np.arange(12, dtype=np.float64)
    carrier = np.arange(EXPECTED_DIMENSION, dtype=np.float64)
    write_private_row_checkpoint(
        path=checkpoint,
        ordinal=18,
        row_id=row_id,
        features=features,
        carrier=carrier,
        source_identities=(source_identity,),
        operator_identity_sha256=operator_id,
    )
    np.savez(checkpoint, features=features, carrier=-carrier)
    with pytest.raises(CarrierExportError, match="content identity"):
        load_private_row_checkpoint(
            path=checkpoint,
            expected_ordinal=18,
            expected_row_id=row_id,
            expected_source_identities=(source_identity,),
            expected_operator_identity_sha256=operator_id,
        )


def _portable_terminal(output_dir: Path) -> dict[str, object]:
    artifact_hashes = {
        path.name: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output_dir.iterdir()
        if path.name != "terminal.json"
    }
    return {
        "work_unit": "PMG-WU-005",
        "state": "SUCCEEDED",
        "real_host_execution": True,
        "replay_status": "MATCH",
        "scalar_closure": "MATCH",
        "raw_data_mutation": False,
        "claim_promotion": False,
        "unresolved_blockers": [],
        "next_executable_action": "PMG-WU-006",
        "fresh_review": "PASS",
        "objective_artifact_sha256": artifact_hashes,
    }


def test_portable_completion_requires_exact_outputs_and_terminal_boundaries(
    tmp_path: Path,
) -> None:
    names = {
        "carrier.npz",
        "metadata.json",
        "scalar_closure.json",
        "input_identity_receipt.json",
        "leakage_receipt.json",
        "replay.json",
        "terminal.json",
    }
    for name in names - {"terminal.json"}:
        (tmp_path / name).write_bytes(b"portable")
    terminal = _portable_terminal(tmp_path)
    (tmp_path / "terminal.json").write_text(json.dumps(terminal), encoding="ascii")
    assert validate_portable_completion(tmp_path) == terminal

    (tmp_path / "replay.json").unlink()
    with pytest.raises(CarrierExportError, match="exactly seven"):
        validate_portable_completion(tmp_path)


def test_portable_completion_rejects_false_success_or_operator_extras(
    tmp_path: Path,
) -> None:
    for name in (
        "carrier.npz",
        "metadata.json",
        "scalar_closure.json",
        "input_identity_receipt.json",
        "leakage_receipt.json",
        "replay.json",
    ):
        (tmp_path / name).write_bytes(b"portable")
    bad_terminal = {
        "work_unit": "PMG-WU-005",
        "state": "SUCCEEDED",
        "real_host_execution": True,
        "replay_status": "MATCH",
        "scalar_closure": "MATCH",
        "raw_data_mutation": True,
        "claim_promotion": False,
        "unresolved_blockers": [],
        "next_executable_action": "PMG-WU-006",
        "fresh_review": "PASS",
        "objective_artifact_sha256": {},
    }
    (tmp_path / "terminal.json").write_text(
        json.dumps(bad_terminal), encoding="ascii"
    )
    with pytest.raises(CarrierExportError, match="terminal boundary"):
        validate_portable_completion(tmp_path)


def test_portable_completion_rejects_artifact_mutation_and_unreviewed_pass(
    tmp_path: Path,
) -> None:
    for name in (
        "carrier.npz",
        "metadata.json",
        "scalar_closure.json",
        "input_identity_receipt.json",
        "leakage_receipt.json",
        "replay.json",
    ):
        (tmp_path / name).write_bytes(name.encode("ascii"))
    terminal = _portable_terminal(tmp_path)
    terminal["fresh_review"] = "PENDING"
    (tmp_path / "terminal.json").write_text(json.dumps(terminal), encoding="ascii")
    with pytest.raises(CarrierExportError, match="fresh review"):
        validate_portable_completion(tmp_path)

    terminal["fresh_review"] = "PASS"
    (tmp_path / "terminal.json").write_text(json.dumps(terminal), encoding="ascii")
    (tmp_path / "input_identity_receipt.json").write_bytes(b"{}\n")
    with pytest.raises(CarrierExportError, match="artifact identity"):
        validate_portable_completion(tmp_path)


def test_real_host_terminal_stays_pending_until_review_admission() -> None:
    module = importlib.import_module(
        "scripts.observed_runs.export_planck_paired300_irrep_carrier"
    )
    build = getattr(module, "_pending_terminal_payload", None)
    assert build is not None
    payload = build(
        operator_identity_sha256="sha256:" + "a" * 64,
        artifact_hashes={"carrier.npz": "sha256:" + "b" * 64},
    )
    assert payload["state"] == "PENDING_REVIEW"
    assert payload["fresh_review"] == "PENDING"
    assert payload["unresolved_blockers"] == ["FRESH_REVIEW_PENDING"]
    assert payload["next_executable_action"] == "FRESH_REVIEW"


def test_scalar_npz_repack_is_numerically_equivalent_but_value_drift_fails(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    generated = root / "docs/generated"
    generated.mkdir(parents=True)
    source = Path(__file__).resolve().parents[2] / "docs/generated"
    shutil.copytree(
        source / "planck_pr3_paired300_irrep_carrier",
        generated / "planck_pr3_paired300_irrep_carrier",
    )
    shutil.copy2(
        source / "pr315_planck_smica_result.json",
        generated / "pr315_planck_smica_result.json",
    )
    with np.load(
        source / "pr315_planck_smica_feature_replay.npz",
        allow_pickle=False,
    ) as bundle:
        arrays = {
            key: np.asarray(bundle[key])
            for key in ("observed_features", "null_features", "row_ids")
        }
    np.savez_compressed(
        generated / "pr315_planck_smica_feature_replay.npz",
        **arrays,
    )
    result = replay_committed(repo_root=root)
    assert result.get("scalar_feature_identity_disposition") == (
        "NUMERICALLY_EQUIVALENT"
    )

    arrays["null_features"] = arrays["null_features"].copy()
    arrays["null_features"][17, 8] += 1.0e-6
    np.savez_compressed(
        generated / "pr315_planck_smica_feature_replay.npz",
        **arrays,
    )
    with pytest.raises(CarrierExportError, match="scientific content"):
        replay_committed(repo_root=root)


def test_execution_provenance_rebinds_intake_stat_identity() -> None:
    module = importlib.import_module(
        "scripts.observed_runs.export_planck_paired300_irrep_carrier"
    )
    validate = getattr(module, "validate_execution_input_provenance", None)
    assert validate is not None
    stat = {"device": 7, "inode": 11, "size": 13, "mtime_ns": 17}
    intake = {
        "format": "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1",
        "entries": [
            {
                "resolved_path": "/raw/row.fits",
                "stat_identity": stat,
                "checksum_status": "DEFERRED_UNTIL_FIRST_SCIENTIFIC_READ",
            }
        ],
    }
    execution = {
        "format": "PLANCK_PR3_PAIRED300_PRIVATE_EXECUTION_MANIFEST_V1",
        "selected_input_identities": [
            {"path": "/raw/row.fits", **stat, "sha256": "sha256:" + "a" * 64}
        ],
    }
    result = validate(intake_manifest=intake, execution_manifest=execution)
    assert result == {
        "required_identity": "INTAKE_STAT_PLUS_EXECUTION_CONTENT",
        "result_validity": "PASS_UNCHANGED",
        "provenance_validity": "MATCH",
        "matched_file_count": 1,
    }
    execution["selected_input_identities"][0]["size"] = 14
    with pytest.raises(CarrierExportError, match="intake stat identity"):
        validate(intake_manifest=intake, execution_manifest=execution)


def test_execution_provenance_uses_selected_manifest_for_observed_inputs() -> None:
    module = importlib.import_module(
        "scripts.observed_runs.export_planck_paired300_irrep_carrier"
    )
    stat = {"device": 7, "inode": 11, "size": 13, "mtime_ns": 17}
    selected = {
        "format": "PLANCK_MES_IRREP_SELECTED_INPUT_MANIFEST_V1",
        "inputs": [
            {
                "resolved_path": "/raw/observed.fits",
                "stat_identity": stat,
            }
        ],
    }
    execution = {
        "format": "PLANCK_PR3_PAIRED300_PRIVATE_EXECUTION_MANIFEST_V1",
        "selected_input_identities": [
            {
                "path": "/raw/observed.fits",
                **stat,
                "sha256": "sha256:" + "a" * 64,
            }
        ],
    }
    result = module.validate_execution_input_provenance(
        intake_manifest={
            "format": "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1",
            "entries": [],
        },
        selected_manifest=selected,
        execution_manifest=execution,
    )
    assert result["matched_file_count"] == 1
    assert result["provenance_validity"] == "MATCH"


def test_documented_replay_cli_runs_without_pythonpath() -> None:
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/observed_runs/export_planck_paired300_irrep_carrier.py",
            "--replay-committed",
        ],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_committed_metadata_declares_nonclaiming_provenance() -> None:
    root = Path(__file__).resolve().parents[2]
    metadata = json.loads(
        (
            root
            / "docs/generated/planck_pr3_paired300_irrep_carrier/metadata.json"
        ).read_text()
    )
    assert {
        "owner",
        "scope",
        "transfer_source",
        "sky_support_status",
        "null_mock_status",
        "caveats",
        "generating_procedure",
        "execution_git_state",
        "scalar_feature_content_id",
    } <= set(metadata)
