from __future__ import annotations

import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr179_spec.yaml"
RESULT_PATH = REPO / "docs/generated/pr179_directional_cosmography_result.json"
NULL_PATH = REPO / "docs/generated/pr179_null_calibration.json"
MANIFEST_PATH = REPO / "docs/generated/pr179_artifact_manifest.json"
RUNNER_PATH = REPO / "scripts/codex_harness/run_pr179_directional_cosmography.py"

_RUNNER_SPEC = importlib.util.spec_from_file_location("pr179_runner_test", RUNNER_PATH)
assert _RUNNER_SPEC is not None and _RUNNER_SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(_RUNNER_SPEC)
_RUNNER_SPEC.loader.exec_module(RUNNER)


def _json(path: Path) -> dict:
    payload = json.loads(path.read_text())
    assert isinstance(payload, dict)
    return payload


def test_spec_was_frozen_before_result_and_preflight_amendment_was_blind() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    assert spec["schema"] == "htt.pr179.spec.v1"
    assert spec["frozen_before_result"] is True
    assert spec["prospective_review"]["observed_directional_values_seen_before_freeze"] is False
    assert spec["prospective_review"]["preflight_amendment"]["observed_directional_values_seen"] is False
    assert spec["finite_rank"]["null_draws"] == 19999
    assert spec["matched_null"]["broad_method_family"] == {
        "FP": "FP",
        "TF": "TF",
        "OTHER": ["CAL", "SN", "SBF", "MIXED_OTHER"],
    }
    forbidden = set(spec["column_firewall"]["hard_forbidden_values"])
    assert {"fV3k", "Hi", "logHi", "Vpds", "Vpwf", "Vpec", "Dist"} <= forbidden


def test_preflight_does_not_import_numerical_evaluator() -> None:
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr179_directional_cosmography.py"),
            "--preflight",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": f"{REPO / 'htt'}:{REPO / 'htt/src'}"},
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["ok"] is True
    assert receipt["numerical_evaluator_imported"] is False
    assert receipt["null_draws"] == 19999


def test_result_pack_is_byte_current_and_read_only_check_passes() -> None:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": f"{REPO / 'htt'}:{REPO / 'htt/src'}",
        "PYTHONHASHSEED": "0",
        "MPLCONFIGDIR": "/tmp/htt-pr179-mpl",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    completed = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr179_directional_cosmography.py"),
            "--check",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["ok"] is True
    assert receipt["checked"] == 10
    assert receipt["read_only"] is True


def test_concrete_result_is_finite_rank_and_claim_bounded() -> None:
    result = _json(RESULT_PATH)
    assert result["analysis_branch"] in {"H_ONLY", "JOINT_H_Q"}
    assert result["selection_systematics_conditional"] is True
    assert result["not_cosmological_anisotropy"] is True
    assert result["terminal"] in {
        "MATCHED_NULL_CONTAINS_DIRECTIONAL_STATISTIC",
        "CATALOGUE_SELECTION_SYSTEMATICS_CONDITIONAL_DIRECTIONAL_RESIDUAL",
        "NUMERICALLY_UNRESOLVED_AT_FROZEN_MC_BUDGET",
        "NON_INFORMATIVE_SELECTION_SYSTEMATICS_DOMINATED",
        "H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL",
    }
    cert = result["rank_certificate"]
    if cert is not None:
        assert cert["n_null"] == 19999
        assert cert["finite_resolution_fraction"] == "1/20000"
        assert cert["tie_policy"] == "conservative_ge"
        assert cert["gaussian_sigma_emitted"] is False
        assert math.isclose(
            cert["estimate"], (1 + cert["exceedance_count"]) / 20000.0,
            abs_tol=1e-15,
        )
    if result["analysis_branch"] == "H_ONLY":
        assert result["q_cat_withheld"] is True
        assert result["coefficient_summary"]["q_cat_dipole_vector"] is None
        assert result["terminal"] == "H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL"
        assert result["supporting_h_only_matched_null_disposition"] in {
            "MATCHED_NULL_CONTAINS_DIRECTIONAL_STATISTIC",
            "CATALOGUE_SELECTION_SYSTEMATICS_CONDITIONAL_DIRECTIONAL_RESIDUAL",
            "NUMERICALLY_UNRESOLVED_AT_FROZEN_MC_BUDGET",
            "NON_INFORMATIVE_SELECTION_SYSTEMATICS_DOMINATED",
        }
    response = result["response_identifiability"]
    assert all(
        "q_directional_cubic_canonical_correlation" in fold
        for fold in response["folds"]
    )


def test_null_lineage_mutations_and_artifact_metadata_are_complete() -> None:
    null = _json(NULL_PATH)["matched_null"]
    assert null["lineage"]["complete"] is True
    assert null["lineage"]["draws"] == 19999
    assert len(null["null_scores"]) == 19999
    mutation = _json(REPO / "docs/generated/pr179_mutation_report.json")
    assert mutation["all_killed"] is True
    assert mutation["survived"] == 0
    assert mutation["killed"] >= 18
    manifest = _json(MANIFEST_PATH)
    assert manifest["candidate_cannot_authorize_itself"] is True
    assert len(manifest["artifacts"]) == 9
    required = {
        "owner", "implementation_scope", "claim_tier", "claim_level",
        "scientific_artifact_mode", "public_use", "transfer_source",
        "config_hash", "input_hashes", "sky_support_status", "mask_status",
        "covariance_status", "null_mock_status", "caveats",
        "generating_command", "git_commit_or_worktree_state",
    }
    assert required <= set(manifest["metadata"])
    assert manifest["metadata"]["public_use"] is False
    execution = _json(REPO / "docs/generated/pr179_execution_receipt.json")
    assert execution["argv"][-1] == "--write"
    assert execution["relevant_content_root"] == RUNNER._semantic_hash(
        execution["relevant_path_hashes"]
    )
    assert execution["metadata"]["execution_receipt_core_sha256"] == (
        manifest["metadata"]["execution_receipt_core_sha256"]
    )
    assert isinstance(manifest["metadata"]["git_commit_or_worktree_state"], dict)


def test_result_card_uses_catalogue_coefficient_language() -> None:
    card = _json(REPO / "docs/generated/pr179_result_card.json")
    language = card["mandatory_claim_language"].lower()
    assert "selection/systematics-conditional" in language
    assert "not cosmological anisotropy" in language
    assert "catalogue-fit coefficient" in language
    assert card["public_use"] is False


def test_every_runtime_config_field_is_bound_to_the_frozen_spec() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    kwargs, crosswalk = RUNNER._config_projection(spec)
    assert set(kwargs) == set(crosswalk) == {
        "c_km_s", "z_min", "z_max", "peculiar_velocity_floor_km_s",
        "systematic_floor_mag", "folds", "fold_nside", "stratum_nside",
        "selection_nside", "redshift_bin_edges", "minimum_stratum_groups",
        "minimum_overall_supported_fraction",
        "minimum_broad_method_supported_fraction", "max_condition_number",
        "minimum_information_h", "minimum_information_q",
        "minimum_information_q_cubic", "max_hq_canonical_correlation",
        "null_draws", "null_batch_size", "seed_entropy", "alpha",
        "confidence_level",
    }
    assert kwargs["max_condition_number"] == 1.0e4
    assert kwargs["seed_entropy"] == (20260720, 179)
    mutated = copy.deepcopy(spec)
    mutated["crossfit"]["cluster"] = "HEALPix_Nside4_NESTED_pixel_x_method_family"
    with pytest.raises(RUNNER.Pr179RunnerError, match="Nside2"):
        RUNNER._config_projection(mutated)


def _dummy_generation(prefix: str) -> dict[str, bytes]:
    return {
        name: f"{prefix}:{name}\n".encode("utf-8") for name in RUNNER.OUTPUT_NAMES
    }


def test_generation_publication_is_locked_manifest_last_and_recoverable(tmp_path) -> None:
    old = _dummy_generation("old")
    new = _dummy_generation("new")
    RUNNER._write_generation(old, generated_dir=tmp_path)
    with pytest.raises(OSError, match="injected"):
        RUNNER._write_generation(new, generated_dir=tmp_path, fail_after=4)
    assert all((tmp_path / name).read_bytes() == old[name] for name in RUNNER.OUTPUT_NAMES)
    assert not (tmp_path / RUNNER.JOURNAL_NAME).exists()
    RUNNER._write_generation(new, generated_dir=tmp_path)
    assert all((tmp_path / name).read_bytes() == new[name] for name in RUNNER.OUTPUT_NAMES)
    assert (tmp_path / RUNNER.OUTPUT_NAMES[-1]).read_bytes() == new[RUNNER.OUTPUT_NAMES[-1]]


def test_generation_writer_rejects_concurrent_lock_holder(tmp_path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(tmp_path / RUNNER.LOCK_NAME, os.O_RDWR | os.O_CREAT, 0o660)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RUNNER.Pr179RunnerError, match="writer lock is held"):
            RUNNER._write_generation(_dummy_generation("blocked"), generated_dir=tmp_path)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def test_runtime_access_and_unsupported_stratum_receipts_are_reconstructible() -> None:
    raw = _json(REPO / "docs/generated/pr179_raw_catalogue_receipt.json")
    assert raw["column_firewall"]["runtime_value_access_receipt_complete"] is True
    assert raw["accessed_columns"]["table4"] == ["1PGC", "DMzp", "e_DMzp"]
    unsupported = raw["support"]["unsupported_strata"]
    canonical = json.dumps(
        unsupported, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    assert raw["support"]["unsupported_strata_sha256"] == hashlib.sha256(
        canonical
    ).hexdigest()
    stability = _json(NULL_PATH)["matched_null"]["stability"]
    assert stability["expected_cases"] == (
        stability["evaluated_cases"] + stability["failed_cases"]
    )
    assert stability["failed_cases"] == 0
