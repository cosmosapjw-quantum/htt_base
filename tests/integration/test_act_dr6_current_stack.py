"""PR-308 observation-free ACT DR6 current-stack contracts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "scripts/observed_runs/run_act_dr6.py"
DISPATCHER = ROOT / "scripts/codex_harness/run_authorized_observational_program.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _worker():
    return _load("pr308_act_worker", WORKER)


def _full_rank_case(seed: int = 308):
    rng = np.random.default_rng(seed)
    observed = rng.normal(size=5)
    simulations = rng.normal(size=(400, 5))
    response = np.eye(5)
    truth = rng.normal(scale=0.08, size=(200, 5))
    estimates = truth + rng.multivariate_normal(
        np.zeros(5), np.cov(simulations, rowvar=False, ddof=1), size=200
    )
    return observed, simulations, response, truth, estimates


def test_pr308_freezes_strict_validated_band_and_feature_order() -> None:
    worker = _worker()

    assert worker.EXPECTED_SUPPORT == {
        "inequality": "40 < L < 763",
        "integer_min": 41,
        "integer_max": 762,
        "integer_count": 722,
        "endpoints_40_and_763_included": False,
        "coordinate_frame": "Equatorial",
    }
    assert worker.FEATURE_ORDER == ("Y20", "Y21c", "Y21s", "Y22c", "Y22s")


def test_pr308_cross_fit_mean_field_is_observation_inclusive_and_exchangeable() -> None:
    worker = _worker()
    observed = np.asarray([10.0, -2.0])
    nulls = np.asarray([[1.0, 2.0], [3.0, 4.0], [8.0, 9.0]])

    corrected_observed, corrected_nulls = worker._cross_fit_mean_field(
        observed, nulls, exact_count=3
    )

    assert np.allclose(corrected_observed, observed - nulls.mean(axis=0))
    for index in range(3):
        other_units = np.vstack([observed, np.delete(nulls, index, axis=0)])
        assert np.allclose(
            corrected_nulls[index],
            nulls[index] - other_units.mean(axis=0),
        )


def test_pr308_full_covariance_preserves_cross_feature_terms() -> None:
    worker = _worker()
    rng = np.random.default_rng(30_800)
    x = rng.normal(size=(400, 5))
    x[:, 1] = 0.65 * x[:, 0] + 0.35 * x[:, 1]

    receipt = worker._full_covariance(x)
    covariance = np.asarray(receipt["matrix"])

    assert covariance.shape == (5, 5)
    assert np.allclose(covariance, covariance.T)
    assert abs(covariance[0, 1]) > 0.1
    assert receipt["diagonalized"] is False
    assert receipt["rank"] == 5
    assert receipt["status"] == "FULL_COVARIANCE_VALID"


def test_pr308_response_rank_is_covariance_whitened_and_fail_closed() -> None:
    worker = _worker()
    covariance = np.asarray(
        [
            [2.0, 0.4, 0.1, 0.0, 0.0],
            [0.4, 1.5, 0.2, 0.0, 0.0],
            [0.1, 0.2, 1.2, 0.1, 0.0],
            [0.0, 0.0, 0.1, 1.1, 0.2],
            [0.0, 0.0, 0.0, 0.2, 1.0],
        ]
    )
    full = worker._response_rank(np.eye(5), covariance)
    deficient = worker._response_rank(np.diag([1.0, 1.0, 1.0, 1.0, 0.0]), covariance)
    weak = worker._response_rank(
        np.diag([1.0, 1.0, 1.0, 1.0, 1.0e-12]), covariance
    )

    assert full["rank"] == 5
    assert full["status"] == "FINITE_RESPONSE_RANK"
    assert deficient["rank"] == 4
    assert deficient["status"] == "RANK_DEFICIENT_ABSTAIN"
    assert weak["rank"] == 5
    assert weak["status"] == "WEAK_RESPONSE_ABSTAIN"


def test_pr308_injection_coverage_uses_full_covariance() -> None:
    worker = _worker()
    rng = np.random.default_rng(30_801)
    covariance = np.asarray(
        [
            [0.030, 0.009, 0.0, 0.0, 0.0],
            [0.009, 0.025, 0.004, 0.0, 0.0],
            [0.0, 0.004, 0.020, 0.003, 0.0],
            [0.0, 0.0, 0.003, 0.018, 0.002],
            [0.0, 0.0, 0.0, 0.002, 0.016],
        ]
    )
    truth = rng.normal(scale=0.1, size=(200, 5))
    estimates = truth + rng.multivariate_normal(np.zeros(5), covariance, size=200)

    receipt = worker._injection_coverage(
        truth,
        estimates,
        response=np.eye(5),
        covariance=covariance,
        injection_stage="PRE_QE_END_TO_END",
    )

    assert receipt["acceptance_interval"][0] <= 0.95
    assert receipt["acceptance_interval"][1] >= 0.95
    assert receipt["injection_stage"] == "PRE_QE_END_TO_END"
    assert receipt["status"] == "INJECTION_COVERAGE_PASS"


@pytest.mark.parametrize(
    "injection_stage",
    ("PRE_QE_END_TO_END", "END_TO_END_RELEASE_RECONSTRUCTION"),
)
def test_pr308_injection_stage_is_preserved_exactly(
    injection_stage: str,
) -> None:
    worker = _worker()
    rng = np.random.default_rng(30_802)
    truth = rng.normal(scale=0.1, size=(200, 5))
    estimates = truth + rng.normal(scale=0.1, size=(200, 5))

    receipt = worker._injection_coverage(
        truth,
        estimates,
        response=np.eye(5),
        covariance=np.eye(5),
        injection_stage=injection_stage,
    )

    assert receipt["injection_stage"] == injection_stage


def test_pr308_injection_stage_rejects_a_collapsed_or_post_qe_label() -> None:
    worker = _worker()
    rows = np.zeros((200, 5))

    for stage in ("PRE_QE_OR_END_TO_END_ONLY", "POST_QE_MAP_INJECTION"):
        with pytest.raises(worker.ActWorkerError, match="injection stage"):
            worker._injection_coverage(
                rows,
                rows,
                response=np.eye(5),
                covariance=np.eye(5),
                injection_stage=stage,
            )


def test_pr308_trivially_overconservative_injection_coverage_abstains() -> None:
    worker = _worker()
    truth = np.zeros((200, 5))

    receipt = worker._injection_coverage(
        truth,
        truth,
        response=np.eye(5),
        covariance=np.eye(5),
        injection_stage="END_TO_END_RELEASE_RECONSTRUCTION",
    )

    assert receipt["coverage_fraction"] == 1.0
    assert receipt["status"] == "INJECTION_COVERAGE_FAILED_ABSTAIN"


def test_pr308_complete_inventory_is_exactly_ordered_400() -> None:
    worker = _worker()
    rows = [
        {
            "simulation_id": f"{index:04d}",
            "relative_path": f"sim/{index:04d}.fits",
            "byte_size": index + 10,
            "content_sha256": "sha256:" + f"{index:064x}",
        }
        for index in range(1, 401)
    ]
    payload = {
        "release_id": "ACT_DR6_LENSING_V1",
        "variant": "baseline",
        "ordered_simulations": rows,
    }

    validated = worker._validate_simulation_inventory(payload)
    assert len(validated) == 400
    assert validated[0]["simulation_id"] == "0001"
    assert validated[-1]["simulation_id"] == "0400"

    for mutate in (
        lambda value: value["ordered_simulations"].pop(),
        lambda value: value["ordered_simulations"].__setitem__(
            1, dict(value["ordered_simulations"][0])
        ),
        lambda value: value["ordered_simulations"][0].__setitem__(
            "content_sha256", int("1" * 64)
        ),
        lambda value: value.update({"variant": "extended"}),
    ):
        changed = json.loads(json.dumps(payload))
        mutate(changed)
        with pytest.raises(worker.ActWorkerError):
            worker._validate_simulation_inventory(changed)


def test_pr308_partial_ensemble_stops_before_covariance_or_rank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = _worker()
    observed, simulations, response, truth, estimates = _full_rank_case()
    called = False

    def forbidden(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("rank reached")

    monkeypatch.setattr(worker, "_response_rank", forbidden)
    with pytest.raises(worker.ActWorkerError, match="exactly 400"):
        worker.analyze_feature_ensemble(
            observed,
            simulations[:-1],
            response=response,
            injection_truth=truth,
            injection_estimates=estimates,
            injection_stage="END_TO_END_RELEASE_RECONSTRUCTION",
        )
    assert called is False


def test_pr308_observed_state_and_rank_emission_cannot_diverge() -> None:
    worker = _worker()
    observed, simulations, response, truth, estimates = _full_rank_case()

    with pytest.raises(worker.ActWorkerError, match="observed/rank state"):
        worker.analyze_feature_ensemble(
            observed,
            simulations,
            response=response,
            injection_truth=truth,
            injection_estimates=estimates,
            injection_stage="END_TO_END_RELEASE_RECONSTRUCTION",
            emit_rank=False,
            observed_execution=True,
        )


def test_pr308_synthetic_closure_has_no_scientific_result() -> None:
    worker = _worker()
    observed, simulations, response, truth, estimates = _full_rank_case()

    result = worker.analyze_feature_ensemble(
        observed,
        simulations,
        response=response,
        injection_truth=truth,
        injection_estimates=estimates,
        injection_stage="END_TO_END_RELEASE_RECONSTRUCTION",
    )

    assert result["simulation_count"] == 400
    assert result["covariance"]["status"] == "FULL_COVARIANCE_VALID"
    assert result["response_rank"]["rank"] == 5
    assert result["injection_coverage"]["status"] == "INJECTION_COVERAGE_PASS"
    assert result["injection_coverage"]["injection_stage"] == (
        "END_TO_END_RELEASE_RECONSTRUCTION"
    )
    assert result["analysis_contract"]["analysis_id"] == (
        "ACT_DR6_INBAND_Y2_MODULATION_V1"
    )
    assert result["analysis_contract"]["supersedes"] == "ACT_DR6_KAPPA"
    assert result["analysis_contract"]["multiplicity"] == 2
    assert result["analysis_contract"]["estimand_fingerprint"].startswith(
        "estid-"
    )
    assert result["terminal_disposition"] == "SYNTHETIC_OPERATOR_CLOSURE_PASS"
    assert result["p_value"] is None
    assert result["scientific_result"] is None
    assert result["observed_statistic_seen"] is False
    assert result["observed_science_executed"] is False


def test_pr308_successor_lineage_starts_from_the_exact_pr134_act_contract() -> None:
    worker = _worker()
    canonical = json.loads(
        (ROOT / "docs/generated/pr134_contract_registry.json").read_text(
            encoding="utf-8"
        )
    )["contracts"]["ACT_DR6_KAPPA"]

    predecessor = worker.AnalysisContract.from_payload(
        worker.ACT_PREDECESSOR_CONTRACT
    ).canonical_payload()
    successor = worker._registered_act_estimand()

    assert predecessor == canonical
    assert successor["analysis_id"] == "ACT_DR6_INBAND_Y2_MODULATION_V1"
    assert successor["selection_window"] == (
        "act_dr6_baseline_mask_strict_integer_ell_41_762"
    )
    assert successor["estimand"] == (
        "five_component_real_y2_fractional_variance_modulation_empirical_upper_rank"
    )
    assert successor["supersedes"] == "ACT_DR6_KAPPA"
    assert successor["multiplicity"] == 2


def test_pr308_observed_rank_requires_the_registered_successor_estimand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = _worker()
    observed, simulations, response, truth, estimates = _full_rank_case()

    def refuse(_self: object, _analysis_id: str) -> None:
        raise worker.EstimandRegistryError("forced registry refusal")

    monkeypatch.setattr(
        worker.EstimandRegistry,
        "require_registered_for_inference",
        refuse,
    )
    with pytest.raises(worker.ActWorkerError, match="estimand registry"):
        worker.analyze_feature_ensemble(
            observed,
            simulations,
            response=response,
            injection_truth=truth,
            injection_estimates=estimates,
            injection_stage="END_TO_END_RELEASE_RECONSTRUCTION",
            emit_rank=True,
            observed_execution=True,
        )


@pytest.mark.parametrize("rows", ("1", "8", "32", "128", "full"))
def test_pr308_profile_rows_are_observation_free(rows: str) -> None:
    worker = _worker()

    result = worker.synthetic_profile(rows=rows, mode="serial", workers=1)

    assert result["row_label"] == rows
    assert result["row_count"] == worker.PROFILE_ROWS[rows]
    assert result["observed_statistic_seen"] is False
    assert result["observed_science_executed"] is False
    assert result["wall_seconds"] >= 0.0
    assert result["max_rss_bytes"] > 0


@pytest.mark.parametrize("mode", ("thread", "process"))
def test_pr308_small_parallel_probes_remain_synthetic(mode: str) -> None:
    worker = _worker()

    result = worker.synthetic_profile(rows="32", mode=mode, workers=2)

    assert result["mode"] == mode
    assert result["row_count"] == 32
    assert result["thread_controls"] == worker.THREAD_CONTROLS
    assert result["observed_statistic_seen"] is False


def test_pr308_synthetic_cli_rejects_admission_and_data_root(tmp_path: Path) -> None:
    worker = _worker()
    output = tmp_path / "profile.json"

    assert worker.main(
        [
            "--synthetic-profile",
            "--rows",
            "1",
            "--admission",
            str(tmp_path / "admission.json"),
            "--data-root",
            str(tmp_path),
            "--output",
            str(output),
        ]
    ) == 2
    assert not output.exists()


def test_pr308_admitted_cli_does_not_normalize_a_symlink_data_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worker = _worker()
    real_root = tmp_path / "real-data"
    real_root.mkdir()
    linked_root = tmp_path / "linked-data"
    linked_root.symlink_to(real_root, target_is_directory=True)
    output = tmp_path / "result.json"

    def reject_symlink(*, admission_path: Path, data_root: Path):
        assert admission_path == tmp_path / "admission.json"
        if data_root.is_symlink():
            raise worker.ActWorkerError("symlink data root rejected")
        return {"unexpected": "normalized symlink"}

    monkeypatch.setattr(worker, "_run_admitted", reject_symlink)
    assert worker.main(
        [
            "--run-admitted",
            "--admission",
            str(tmp_path / "admission.json"),
            "--data-root",
            str(linked_root),
            "--output",
            str(output),
        ]
    ) == 2
    assert not output.exists()


def test_pr308_dispatcher_profile_is_exact_and_stale_features_are_not_authority() -> None:
    dispatcher = _load("pr308_dispatcher", DISPATCHER)
    worker_source = WORKER.read_text(encoding="utf-8")
    profile = dispatcher.LANE_PROFILES["ACT"]

    assert set(dispatcher.LANE_PROFILES) == {"PLANCK", "CF4", "ACT"}
    assert profile.analysis_plan_id == "plan:PR204-ACT-LENSING-V1"
    assert profile.science_worker_relative == "scripts/observed_runs/run_act_dr6.py"
    assert profile.science_worker_arguments == ("--run-admitted",)
    assert profile.result_filename == "act_dr6_result.json"
    assert profile.runtime_distributions == ("numpy", "healpy")
    assert "scipy" not in profile.runtime_modules
    assert "pr177_act_inband_feature_card" not in worker_source
    assert "urllib" not in worker_source and "requests" not in worker_source


def test_pr308_max_rss_normalizes_platform_units(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker = _worker()
    monkeypatch.setattr(worker.sys, "platform", "linux")
    monkeypatch.setattr(
        worker.resource,
        "getrusage",
        lambda _kind: SimpleNamespace(ru_maxrss=321),
    )

    assert worker._max_rss_bytes() == 321 * 1024
