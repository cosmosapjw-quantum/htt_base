from __future__ import annotations

import importlib.util
import copy
import json
import math
import os
from pathlib import Path
import subprocess

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr176_spec.yaml"
RUNNER_PATH = REPO / "scripts/codex_harness/run_pr176_affine_divergence.py"
GENERATED = REPO / "docs/generated"

_RUNNER_SPEC = importlib.util.spec_from_file_location("pr176_runner_test", RUNNER_PATH)
assert _RUNNER_SPEC is not None and _RUNNER_SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(_RUNNER_SPEC)
_RUNNER_SPEC.loader.exec_module(RUNNER)


def _json(name: str) -> dict:
    payload = json.loads((GENERATED / name).read_text())
    assert isinstance(payload, dict)
    return payload


def _runner_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": f"{REPO / 'htt'}:{REPO / 'htt/src'}",
        "PYTHONHASHSEED": "0",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }


def test_prospective_spec_is_frozen_and_response_gates_precede_result() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    assert spec["schema"] == "htt.pr176.spec.v1"
    assert spec["frozen_before_result"] is True
    assert spec["prospective_review"]["observed_velocity_or_divergence_values_seen_before_freeze"] is False
    assert spec["catalogue_domain"]["cumulative_physical_radius_mpc"] == [75.0, 100.0, 125.0]
    assert spec["catalogue_domain"]["harmonic_scale_convention"] == "lambda_physical=2*catalogue_ball_radius"
    assert spec["q_response_bridges"]["legacy_beta_closure_is_forbidden"] is True
    assert spec["dependence_contract"]["pr148_covariance_reuse_forbidden"] is True
    erratum = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr176_spec_erratum.yaml").read_text()
    )
    assert erratum["parent_spec"]["sha256"] == RUNNER.FROZEN_SPEC_SHA256
    assert erratum["result_integrity"]["thresholds_changed"] is False
    assert erratum["result_integrity"]["frozen_coverage_failures_preserved"] is True


def test_current_preflight_blocks_on_relocated_frozen_authority() -> None:
    assert not (REPO / "htt/src/common/cf4_velocity_estimators.py").exists()
    assert (REPO / "htt/obsstat/cf4_velocity_estimators.py").is_file()
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(RUNNER_PATH),
            "--preflight",
        ],
        cwd=REPO,
        env=_runner_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert json.loads(completed.stderr) == {
        "error": "missing authority: htt/src/common/cf4_velocity_estimators.py",
        "ok": False,
    }


def test_read_only_check_blocks_on_relocated_frozen_authority() -> None:
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(RUNNER_PATH),
            "--check",
        ],
        cwd=REPO,
        env=_runner_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert json.loads(completed.stderr) == {
        "error": "missing authority: htt/src/common/cf4_velocity_estimators.py",
        "ok": False,
    }


def test_raw_cf4_divergence_is_measured_at_all_frozen_radii() -> None:
    result = _json("pr176_divergence_measurement.json")
    assert result["all_divergence_response_gates_pass"] is True
    assert result["theta_is_scalar_without_apex"] is True
    assert result["theta_apex"] is None
    assert result["structurally_distinct_not_leakage_immune"] is True
    assert result["legacy_beta_closure_used"] is False
    rows = result["candidate_coefficients_by_radius"]
    assert [row["radius_mpc"] for row in rows] == [75.0, 100.0, 125.0]
    assert [row["diagnostics"]["rows"] for row in rows] == [447, 685, 913]
    for row in rows:
        assert row["diagnostics"]["rank"] == 10
        assert row["diagnostics"]["response_gate_pass"] is True
        assert row["diagnostics"]["theta_retained_information"] > 0.68
        assert math.isfinite(row["coefficient_summary"]["theta"]["estimate"])
        assert row["coefficient_summary"]["theta"]["marginal_sd"] > 0.0
        assert row["q_point_estimate"] is None
        assert row["q_interval"] is None
    assert result["coefficient_rows_are_accepted_measurement"] is False


def test_registered_injection_excursion_routes_fail_closed_without_rethresholding() -> None:
    validation = _json("pr176_injection_validation.json")
    assert validation["all_injection_gates_pass"] is False
    rows = validation["channel_injections"]
    assert all(row["deterministic_exact"]["all_pass"] for row in rows)
    failures = []
    for row in rows:
        for component, receipt in row["covariance_self_consistency"]["components"].items():
            if not receipt["pass"]:
                failures.append((row["radius_mpc"], component, receipt))
    assert [(radius, component) for radius, component, _ in failures] == [
        (100.0, "Syy_minus_Szz"),
    ]
    assert all(receipt["coverage_95"] < 0.97 for _, _, receipt in failures)
    assert all(receipt["nominal_inside_wilson"] is False for _, _, receipt in failures)


def test_q_channel_and_dependence_stay_explicitly_unidentified() -> None:
    dependence = _json("pr176_dependence_bound.json")
    assert dependence["nested_radius_independence_assumed"] is False
    assert all(
        bridge["authenticated_for_cf4_window"] is False and bridge["response"] is None
        for bridge in dependence["q_response_bridges"]
    )
    covariance = dependence["matched_divergence_q_covariance"]
    assert covariance == {
        "available": False,
        "pr148_covariance_reused": False,
        "reason": "no matched divergence-q joint replicate or authenticated covariance",
        "source": None,
    }
    assert dependence["evaluated_cross_channel_interval"] is None


def test_terminal_is_reproducible_nonidentification_not_a_detection() -> None:
    result = _json("pr176_cross_falsifier_result.json")
    assert result["terminal"] == "NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE"
    assert result["scientific_result_reproducible"] is True
    assert result["success_dependency_satisfied"] is True
    assert result["divergence_rank_information_gate_pass"] is True
    assert result["deterministic_channel_injection_gate_pass"] is True
    assert result["covariance_self_consistency_gate_pass"] is False
    assert result["validation_axis"] == "FROZEN_COVARIANCE_SELF_CONSISTENCY_GATE_FAILED"
    assert result["divergence_channel_accepted_measurement"] is False
    assert result["q_channel_result"] is None
    assert result["significance"] is None
    assert result["family_identification"] is None
    assert result["native_transfer_validation"] is None
    card = _json("pr176_result_card.json")
    language = card["mandatory_claim_language"].lower()
    assert "structurally distinct" in language
    assert "not leakage-immune" in language
    assert "non_informative" in language
    assert card["public_use"] is False


def test_h0_alias_mutations_and_provenance_are_load_bearing() -> None:
    injection = _json("pr176_injection_validation.json")
    for row in injection["channel_injections"]:
        alias = row["deterministic_exact"]["cases"]["h0_alias"]
        assert alias["pass"] is True
        assert math.isclose(alias["coefficient_difference"][4], -3.75, abs_tol=1e-10)
        assert max(abs(value) for index, value in enumerate(alias["coefficient_difference"]) if index != 4) < 1e-8
    mutation = _json("pr176_mutation_report.json")
    assert mutation["all_killed"] is True
    assert mutation["killed"] == 21
    assert mutation["survived"] == 0
    source = _json("pr176_source_authority.json")
    assert source["authority_ok"] is True
    assert source["raw_reconstruction_values_used"] == []
    assert source["partial_pr151_mock_use"] is False


def test_manifest_carries_complete_metadata_and_hashes_every_payload() -> None:
    manifest = _json("pr176_artifact_manifest.json")
    assert manifest["candidate_cannot_authorize_itself"] is True
    assert manifest["independent_closeout_authorization"] == {
        "policy": "this candidate generation supplies integrity but cannot authorize its own scientific closeout",
        "receipt": None,
        "status": "PENDING_EXTERNAL_ADJUDICATION",
    }
    assert len(manifest["artifacts"]) == 8
    required = {
        "owner", "implementation_scope", "claim_tier", "claim_level",
        "scientific_artifact_mode", "public_use", "transfer_source",
        "config_hash", "input_hashes", "sky_support_status", "mask_status",
        "covariance_status", "null_mock_status", "caveats",
        "generating_command", "git_commit_or_worktree_state",
    }
    assert required <= set(manifest["metadata"])
    assert manifest["metadata"]["public_use"] is False
    for name, receipt in manifest["artifacts"].items():
        path = GENERATED / name
        assert RUNNER._sha256(path) == receipt["sha256"]
        assert path.stat().st_size == receipt["size_bytes"]
    execution = _json("pr176_execution_receipt.json")
    assert execution["full_rehash_of_external_large_payloads"] is False
    assert execution["compact_cf4_rehashed"] is True
    assert execution["relevant_content_root"] == RUNNER._semantic_hash(
        execution["relevant_path_hashes"]
    )


def test_every_runtime_parameter_is_crosswalked_to_frozen_spec() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    kwargs, crosswalk = RUNNER._config_projection(spec)
    assert set(kwargs) == set(crosswalk)
    assert kwargs["radii_mpc"] == (75.0, 100.0, 125.0)
    assert kwargs["coverage_draws"] == 5000
    assert kwargs["coverage_seeds"] == (176000, 176001, 176002)
    assert kwargs["h0_km_s_mpc"] == 74.6
    assert kwargs["minimum_theta_retained_information"] == 0.05
    assert kwargs["exact_injection_tolerance_relative"] == 1.0e-9


def test_terminal_and_numerical_primitives_are_derived_not_resealable() -> None:
    core_names = {
        "pr176_source_authority.json",
        "pr176_divergence_measurement.json",
        "pr176_injection_validation.json",
        "pr176_dependence_bound.json",
        "pr176_cross_falsifier_result.json",
        "pr176_result_card.json",
    }
    core = {name: _json(name) for name in core_names}
    assert RUNNER._semantic_hash(RUNNER._numerical_primitive_projection(core)) == (
        RUNNER.NUMERICAL_PRIMITIVE_SHA256
    )
    wrong_terminal = copy.deepcopy(core)
    wrong_terminal["pr176_cross_falsifier_result.json"]["terminal"] = (
        "NON_INFORMATIVE_DIVERGENCE_RESPONSE"
    )
    with pytest.raises(RUNNER.Pr176RunnerError, match="ordered truth table"):
        RUNNER._validate_core(wrong_terminal, yaml.safe_load(SPEC_PATH.read_text()))
    resealed_theta = copy.deepcopy(core)
    resealed_theta["pr176_divergence_measurement.json"][
        "candidate_coefficients_by_radius"
    ][0]["coefficient_summary"]["theta"]["estimate"] = 1.0e99
    with pytest.raises(RUNNER.Pr176RunnerError):
        RUNNER._validate_core(resealed_theta, yaml.safe_load(SPEC_PATH.read_text()))


def test_interrupted_publication_rolls_back_complete_previous_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(RUNNER, "GENERATED", tmp_path)
    old_bytes = {}
    for name in RUNNER.OUTPUT_NAMES:
        content = (f"old:{name}\n").encode()
        (tmp_path / name).write_bytes(content)
        old_bytes[name] = content
    payloads = {name: {"schema": "test.new", "name": name} for name in RUNNER.OUTPUT_NAMES}
    replacements = 0

    def fail_during_second_install(source: Path, target: Path) -> None:
        nonlocal replacements
        replacements += 1
        if replacements == len(RUNNER.OUTPUT_NAMES) + 2:
            raise OSError("injected mid-publication failure")
        os.replace(source, target)

    with pytest.raises(OSError, match="injected mid-publication"):
        RUNNER._publish_generation(payloads, replace=fail_during_second_install)
    assert (tmp_path / RUNNER.JOURNAL_NAME).is_file()
    receipt = RUNNER._recover_transaction()
    assert receipt == {"recovered": True, "action": "rollback_to_previous_generation"}
    for name, content in old_bytes.items():
        assert (tmp_path / name).read_bytes() == content
    assert not (tmp_path / RUNNER.JOURNAL_NAME).exists()
    assert not (tmp_path / RUNNER.STAGE_NAME).exists()
    assert not (tmp_path / RUNNER.BACKUP_NAME).exists()
