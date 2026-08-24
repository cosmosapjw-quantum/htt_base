from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from obsstat import jwst_distance_consistency as science


ROOT = Path(__file__).resolve().parents[2]
WORKER_PATH = ROOT / "scripts/observed_runs/run_jwst_sn.py"
DISPATCHER_PATH = (
    ROOT / "scripts/codex_harness/run_authorized_observational_program.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_FIXTURE_WORKER = _load(WORKER_PATH, "pr309_fixture_worker")


def _payloads(rows: int = 24) -> tuple[dict, dict, dict, dict, dict]:
    return _FIXTURE_WORKER._synthetic_payloads(rows)


def _build(source_rows, host_rows, errors, covariance, competitors):
    return science.build_pr309_inputs(
        source_rows=source_rows,
        host_rows=host_rows,
        individual_errors=errors,
        covariance=covariance,
        competitor_model=competitors,
    )


def _inputs(rows: int = 24):
    return _build(*_payloads(rows))


def test_pr309_builds_typed_rows_and_full_shared_covariance() -> None:
    inputs = _inputs()

    assert inputs.row_ids[0] == "SYNTH-JWST-000"
    assert inputs.feature_order == science.PR309_FEATURE_ORDER
    assert inputs.competitor_order == ("CF4", "2MRS")
    assert inputs.total_covariance_mag2.shape == (24, 24)
    assert np.count_nonzero(
        inputs.total_covariance_mag2
        - np.diag(np.diag(inputs.total_covariance_mag2))
    ) > 0
    assert set(inputs.calibration_groups) == {"CAL-0", "CAL-1", "CAL-2", "CAL-3"}
    assert all(
        row["source_id"].startswith("synthetic:source:") for row in inputs.row_report
    )
    assert all(row["host_linkage_probability"] == 1.0 for row in inputs.row_report)
    assert all(row["host_linkage_sigma_mag"] == 0.0 for row in inputs.row_report)
    assert all(
        row["host_identity_status"] == "ADMITTED_NON_POSITIONAL_IDENTITY_EVIDENCE"
        for row in inputs.row_report
    )
    expected_same_group = 1.6e-4 + covariance_value(0, 4, rows=24)
    assert inputs.total_covariance_mag2[0, 4] == pytest.approx(expected_same_group)
    expected_different_group = 1.0e-5 + covariance_value(0, 1, rows=24)
    assert inputs.total_covariance_mag2[0, 1] == pytest.approx(expected_different_group)


def covariance_value(left: int, right: int, *, rows: int) -> float:
    separation = np.abs(np.subtract.outer(np.arange(rows), np.arange(rows)))
    return float(5.0e-5 * np.exp(-separation[left, right] / 5.0))


def test_pr309_rejects_positional_host_identity() -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    host_rows["rows"][0]["host_linkage_basis"] = "POSITIONAL_COINCIDENCE"

    with pytest.raises(science.JWSTSNCurrentStackError, match="positional"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    host_rows["rows"][0]["host_linkage_basis"] = (
        "NON_POSITIONAL_CATALOGUE_CROSS_ID"
    )
    assert _build(source_rows, host_rows, errors, covariance, competitors).row_ids[
        0
    ] == "SYNTH-JWST-000"


def test_pr309_rejects_row_order_or_provenance_drift() -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    host_rows["row_order"] = list(reversed(host_rows["row_order"]))
    with pytest.raises(science.JWSTSNCurrentStackError, match="row order"):
        _build(source_rows, host_rows, errors, covariance, competitors)


def test_pr309_direction_redshift_depth_semantics_are_frozen() -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    host_rows["rows"][0]["coordinate_frame"] = "ICRS"
    with pytest.raises(science.JWSTSNCurrentStackError, match="semantic"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    host_rows["rows"][0]["redshift_frame"] = "HELIOCENTRIC"
    with pytest.raises(science.JWSTSNCurrentStackError, match="semantic"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    source_rows["rows"][0]["source_locator"] = ""
    with pytest.raises(science.JWSTSNCurrentStackError, match="source provenance"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    source_rows["rows"][0]["observable_delta_definition"] = "METHOD_B_MINUS_METHOD_A_MAG"
    with pytest.raises(science.JWSTSNCurrentStackError, match="observable"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    competitors["competitors"][1]["frame_transformation_role"] = "RAW_NO_TRANSFORM"
    with pytest.raises(science.JWSTSNCurrentStackError, match="frame"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    competitors["competitors"][1]["frame_transformation_identity"] = ""
    with pytest.raises(science.JWSTSNCurrentStackError, match="transformation identity"):
        _build(source_rows, host_rows, errors, covariance, competitors)


def test_pr309_rejects_diagonalized_shared_covariance() -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    covariance["shared_zero_point_covariance_mag2"] = np.diag(
        np.diag(covariance["shared_zero_point_covariance_mag2"])
    ).tolist()
    covariance["peculiar_velocity_covariance_mag2"] = np.diag(
        np.diag(covariance["peculiar_velocity_covariance_mag2"])
    ).tolist()

    with pytest.raises(science.JWSTSNCurrentStackError, match="off-diagonal"):
        _build(source_rows, host_rows, errors, covariance, competitors)

    source_rows, host_rows, errors, covariance, competitors = _payloads()
    covariance["maximum_condition_number"] = 1.0e12
    with pytest.raises(science.JWSTSNCurrentStackError, match="ill-conditioned"):
        _build(source_rows, host_rows, errors, covariance, competitors)


def test_pr309_accepts_scientifically_identified_2mrs_provider() -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    row = competitors["competitors"][1]
    row["model_identity"] = "2mrs-distance-prediction-forward-model-v1"
    row["source_release"] = "NASA_HEASARC_2MRS"
    row["frame_transformation_identity"] = "barycentric-to-cmb-forward:v1"

    inputs = _build(source_rows, host_rows, errors, covariance, competitors)

    assert inputs.competitor_metadata["2MRS"]["model_identity"] == (
        "2mrs-distance-prediction-forward-model-v1"
    )
    assert inputs.competitor_metadata["2MRS"]["frame_transformation_identity"] == (
        "barycentric-to-cmb-forward:v1"
    )


def test_pr309_missing_2mrs_stops_before_response_rank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    competitors["competitors"].pop()
    reached_rank = False

    def forbidden(*_args, **_kwargs):
        nonlocal reached_rank
        reached_rank = True
        raise AssertionError("rank reached")

    monkeypatch.setattr(science, "_whitened_rank", forbidden)
    with pytest.raises(science.JWSTSNCurrentStackError, match="CF4.*2MRS"):
        _build(source_rows, host_rows, errors, covariance, competitors)
    assert reached_rank is False


def test_pr309_rejects_a_disguised_duplicate_competitor() -> None:
    source_rows, host_rows, errors, covariance, competitors = _payloads()
    competitors["competitors"][1]["model_identity"] = (
        competitors["competitors"][0]["model_identity"]
    )
    with pytest.raises(science.JWSTSNCurrentStackError, match="identities"):
        _build(source_rows, host_rows, errors, covariance, competitors)


def test_pr309_synthetic_closure_keeps_competitors_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        science.np.linalg,
        "inv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("normal-matrix inversion is unstable")
        ),
    )
    result = science.analyze_pr309_current_stack(_inputs(), observed=False)

    assert result["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
    assert result["response_rank"]["rank"] == len(science.PR309_FEATURE_ORDER)
    assert list(result["competitor_conditioned_diagnostics"]) == ["CF4", "2MRS"]
    assert all(
        item["status"] == "NUMERICALLY_FULL_RANK_DIAGNOSTIC_ONLY"
        for item in result["competitor_conditioned_diagnostics"].values()
    )
    assert all(
        "point_estimate" not in item
        and "standard_error" not in item
        and "whitened_residual_sum_squares" not in item
        for item in result["competitor_conditioned_diagnostics"].values()
    )
    assert "combined_competitor" not in json.dumps(result)
    assert result["forced_source_label"] is None
    assert result["p_value"] is None
    assert result["observed_statistic_seen"] is False
    assert result["observed_science_executed"] is False


def test_pr309_rank_loss_abstains_without_point_estimate() -> None:
    inputs = _inputs(rows=24)
    collapsed = science.JWSTSNCurrentStackInputs(
        **{
            **inputs.__dict__,
            "direction_unit_vectors": np.tile(np.asarray([[1.0, 0.0, 0.0]]), (24, 1)),
            "redshift": np.ones(24),
            "depth_mpc": np.ones(24),
        }
    )

    result = science.analyze_pr309_current_stack(collapsed, observed=False)
    assert result["terminal_disposition"] == "RANK_DEFICIENT_ABSTAIN"
    assert result["competitor_conditioned_diagnostics"] == {}
    assert result["forced_source_label"] is None
    assert result["p_value"] is None


def test_pr309_rank_is_invariant_to_nonzero_competitor_scaling() -> None:
    inputs = _inputs()
    baseline = science.analyze_pr309_current_stack(inputs, observed=False)
    scales = (1.0e-6, 1.0e-3, 1.0, 1.0e3, 1.0e6)

    for competitor_id in science.PR309_COMPETITOR_ORDER:
        expected = baseline["competitor_conditioned_diagnostics"][competitor_id]
        for scale in scales:
            competitors = dict(inputs.competitor_predictions_mag)
            competitors[competitor_id] = competitors[competitor_id] * scale
            changed = science.JWSTSNCurrentStackInputs(
                **{**inputs.__dict__, "competitor_predictions_mag": competitors}
            )

            result = science.analyze_pr309_current_stack(changed, observed=False)
            diagnostic = result["competitor_conditioned_diagnostics"][competitor_id]

            assert result["terminal_disposition"] == baseline["terminal_disposition"]
            assert diagnostic["status"] == expected["status"]
            assert diagnostic["response_rank"]["rank"] == expected["response_rank"]["rank"]
            assert diagnostic["response_rank"]["expected_rank"] == expected[
                "response_rank"
            ]["expected_rank"]
            assert diagnostic["response_rank"]["whitening"] == "cholesky_left"
            assert diagnostic["response_rank"]["column_scaling"] == (
                "covariance_whitened_l2"
            )
            assert diagnostic["response_rank"]["threshold_basis"] == (
                "largest_singular_value_after_column_scaling"
            )


def test_pr309_nonexact_host_linkage_abstains_before_rank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("response rank reached before host abstention")

    monkeypatch.setattr(science, "_whitened_rank", forbidden)
    mutations = (
        ("SOURCE_REPORTED_HOST_IDENTITY", 0.96, 0.008),
        ("AMBIGUOUS_HOST_MARGINALIZED", 1.0, 0.008),
    )
    for basis, probability, sigma in mutations:
        source_rows, host_rows, errors, covariance, competitors = _payloads()
        host_rows["rows"][0].update(
            {
                "host_linkage_basis": basis,
                "host_linkage_probability": probability,
                "host_linkage_sigma_mag": sigma,
            }
        )
        inputs = _build(source_rows, host_rows, errors, covariance, competitors)

        result = science.analyze_pr309_current_stack(inputs, observed=False)

        assert result["terminal_disposition"] == (
            "HOST_LINKAGE_COVARIATE_MARGINALIZATION_REQUIRED"
        )
        assert result["response_rank"] is None
        assert result["competitor_conditioned_diagnostics"] == {}


def test_pr309_competitor_collinearity_abstains_only_that_lane() -> None:
    inputs = _inputs()
    response = science._response_design(inputs)
    competitors = dict(inputs.competitor_predictions_mag)
    competitors["2MRS"] = response[:, 0].copy()
    changed = science.JWSTSNCurrentStackInputs(
        **{**inputs.__dict__, "competitor_predictions_mag": competitors}
    )

    result = science.analyze_pr309_current_stack(changed, observed=False)
    assert result["terminal_disposition"] == "WEAK_COMPETITOR_IDENTIFICATION_ABSTAIN"
    assert result["competitor_conditioned_diagnostics"]["CF4"]["status"] == (
        "NUMERICALLY_FULL_RANK_DIAGNOSTIC_ONLY"
    )
    assert result["competitor_conditioned_diagnostics"]["2MRS"]["status"] == (
        "NON_IDENTIFIED_ABSTAIN"
    )
    assert "point_estimate" not in result["competitor_conditioned_diagnostics"][
        "2MRS"
    ]
    assert result["forced_source_label"] is None

    inputs = _inputs()
    response = science._response_design(inputs)
    trial = np.sin(np.arange(len(inputs.row_ids), dtype=float) * 1.2345)
    trial -= response @ np.linalg.lstsq(response, trial, rcond=None)[0]
    trial /= np.linalg.norm(trial)
    competitors = dict(inputs.competitor_predictions_mag)
    competitors["2MRS"] = response[:, 0] + 1.0e-7 * trial
    changed = science.JWSTSNCurrentStackInputs(
        **{**inputs.__dict__, "competitor_predictions_mag": competitors}
    )
    result = science.analyze_pr309_current_stack(changed, observed=False)
    assert result["terminal_disposition"] == "WEAK_COMPETITOR_IDENTIFICATION_ABSTAIN"
    assert result["competitor_conditioned_diagnostics"]["2MRS"]["status"] == (
        "NON_IDENTIFIED_ABSTAIN"
    )


def test_pr309_above_floor_rank_diagnostic_does_not_become_a_point_fit() -> None:
    inputs = _inputs()
    response = science._response_design(inputs)
    trial = np.sin(np.arange(len(inputs.row_ids), dtype=float) * 1.2345)
    trial -= response @ np.linalg.lstsq(response, trial, rcond=None)[0]
    trial /= np.linalg.norm(trial)
    competitors = dict(inputs.competitor_predictions_mag)
    competitors["2MRS"] = response[:, 0] + 1.0e-5 * trial
    changed = science.JWSTSNCurrentStackInputs(
        **{**inputs.__dict__, "competitor_predictions_mag": competitors}
    )

    result = science.analyze_pr309_current_stack(changed, observed=False)
    diagnostic = result["competitor_conditioned_diagnostics"]["2MRS"]

    assert diagnostic["response_rank"]["minimum_singular_value_ratio"] > 1.0e-6
    assert diagnostic["status"] == "NUMERICALLY_FULL_RANK_DIAGNOSTIC_ONLY"
    assert "point_estimate" not in diagnostic
    assert "standard_error" not in diagnostic
    assert "whitened_residual_sum_squares" not in diagnostic


def test_pr309_does_not_call_historical_pr153_result_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        science,
        "build_distance_result",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("historical")),
    )
    result = science.analyze_pr309_current_stack(_inputs(), observed=False)
    assert result["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"


def test_pr309_dispatcher_profile_is_exact_and_single_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dispatcher = _load(DISPATCHER_PATH, "pr309_dispatcher")
    profile = dispatcher._lane_profile("JWST_SN")
    monkeypatch.setattr(
        dispatcher,
        "_tracked_file",
        lambda root, value, _label: root / value,
    )

    assert profile.analysis_plan_id == "plan:PR293-JWST-SN-V1"
    assert profile.science_execution_mode == "jwst_sn_row_covariance_operator"
    assert profile.science_worker_relative == "scripts/observed_runs/run_jwst_sn.py"
    assert profile.science_worker_arguments == ("--run-admitted",)
    assert profile.result_filename == "jwst_sn_result.json"
    assert set(dispatcher.REGISTERED_LANE_PROFILES) == {
        "PLANCK",
        "CF4",
        "ACT",
        "JWST_SN",
    }

    plan = {
        "analysis_plan_id": profile.analysis_plan_id,
        "bayesian_inference": False,
        "execution_mode": profile.science_execution_mode,
        "lane": "JWST_SN",
        "worker_arguments": ["--run-admitted"],
        "worker_path": profile.science_worker_relative,
    }
    validated = dispatcher.validate_plan_values(plan, root=ROOT, profile=profile)
    assert validated["science_execution"] is True

    plan["worker_path"] = "scripts/observed_runs/run_cf4_current_stack.py"
    with pytest.raises(dispatcher.ObservationalProgramError, match="reviewed"):
        dispatcher.validate_plan_values(plan, root=ROOT, profile=profile)


def test_pr309_acceptance_does_not_open_a_jwst_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dispatcher = _load(DISPATCHER_PATH, "pr309_dispatcher_no_open")
    profile = dispatcher._lane_profile("JWST_SN")
    data_root = (tmp_path / "data").resolve()
    data_root.mkdir()
    observed = data_root / "observed.json"
    observed.write_text("do-not-open\n", encoding="utf-8")
    output = (tmp_path / "output").resolve()
    plan_file = tmp_path / "plan.json"
    admission_file = tmp_path / "admission.json"
    plan = {
        "science_execution": True,
        "worker": WORKER_PATH,
        "worker_arguments": ["--run-admitted"],
    }
    decision = SimpleNamespace(
        records=[SimpleNamespace(record_id="record:jwst:test")],
        lane_admission_bundle_id="bundle:jwst:test",
    )
    monkeypatch.setattr(dispatcher.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        dispatcher,
        "_candidate_identity",
        lambda _root: ("1" * 40, "2" * 40),
    )
    monkeypatch.setattr(
        dispatcher,
        "_load_plan",
        lambda *_args, **_kwargs: (plan, b"plan", plan_file),
    )
    monkeypatch.setattr(
        dispatcher,
        "_load_admission",
        lambda *_args, **_kwargs: (decision, b"admission"),
    )
    monkeypatch.setattr(dispatcher, "_output_path", lambda *_args: output)
    monkeypatch.setattr(
        dispatcher,
        "_science_runtime_contract",
        lambda _profile: {"import_roots": [str(tmp_path)]},
    )
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path == observed or data_root in path.parents:
            raise AssertionError("observed payload opened during acceptance")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    prepared = dispatcher.prepare_execution(
        lane="JWST_SN",
        plan_path=str(plan_file),
        admission_path=admission_file,
        output_dir=output,
        timeout_seconds=300,
        data_root=data_root,
        root=ROOT,
    )

    assert prepared["acceptance_payload"]["lane"] == "JWST_SN"
    assert prepared["acceptance_payload"]["candidate_commit"] == "1" * 40
    assert prepared["acceptance_payload"]["candidate_tree"] == "2" * 40
    assert prepared["acceptance_payload"]["ordered_record_ids"] == [
        "record:jwst:test"
    ]
    assert prepared["acceptance_payload"]["timeout_seconds"] == 300
    assert prepared["acceptance_payload"]["environment_contract_sha256"]
    assert not (output / "start.json").exists()
    assert not (output / dispatcher.OBSERVED_DATA_MARKER).exists()


def test_pr309_worker_requires_exact_registry_components() -> None:
    worker = _load(WORKER_PATH, "pr309_worker_components")
    assert worker.REQUIRED_COMPONENTS == frozenset(
        {
            "source_rows",
            "host_rows",
            "individual_errors",
            "covariance",
            "competitor_model",
        }
    )


def test_pr309_worker_marks_start_before_any_data_open(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    worker = _load(WORKER_PATH, "pr309_worker_order")
    calls: list[str] = []
    fake_decision = SimpleNamespace(
        lane_admission_bundle_id="bundle:test",
        records=[],
    )
    monkeypatch.setattr(worker, "_load_admission", lambda _path: fake_decision)
    monkeypatch.setattr(
        worker, "_mark_observed_data_open_attempt", lambda: calls.append("marker")
    )

    def paths(*_args, **_kwargs):
        calls.append("data_open")
        raise worker.JWSTSNWorkerError("expected stop")

    monkeypatch.setattr(worker, "_admitted_paths", paths)
    with pytest.raises(worker.JWSTSNWorkerError, match="expected stop"):
        worker.run_admitted(
            admission_path=tmp_path / "admission.json",
            data_root=tmp_path,
        )
    assert calls == ["marker", "data_open"]


def test_pr309_synthetic_cli_is_observation_free(tmp_path: Path) -> None:
    worker = _load(WORKER_PATH, "pr309_worker_synthetic")
    output = tmp_path / "profile.json"

    assert worker.main(["--synthetic-profile", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["lane"] == "JWST_SN"
    assert payload["observed_statistic_seen"] is False
    assert payload["observed_science_executed"] is False
    assert payload["report"]["p_value"] is None

    assert worker.main(
        [
            "--synthetic-profile",
            "--admission",
            str(tmp_path / "admission.json"),
            "--output",
            str(output),
        ]
    ) == 2
