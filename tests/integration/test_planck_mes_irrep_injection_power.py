from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/observed_runs/run_planck_mes_irrep_injection_power.py"
REGISTRY = ROOT / "docs/research_program/post_pr327/planck_mes_wu008_experiment.json"


def _api():
    if not SCRIPT.is_file():
        pytest.fail("PMG-WU-008 numerical runner is not implemented", pytrace=False)
    spec = importlib.util.spec_from_file_location("planck_mes_wu008", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exact_registry_is_frozen_and_validated() -> None:
    api = _api()
    registry = api.load_registry(REGISTRY)
    assert registry["schema"] == "PMG_WU008_NUMERICAL_SPEC_V1"
    assert len(registry["calibration_ids"]) == 200
    assert len(registry["evaluation_ids"]["paired300"]) == 100
    assert len(registry["evaluation_ids"]["cmbonly999"]) == 799
    assert set(registry["calibration_ids"]).isdisjoint(
        registry["evaluation_ids"]["cmbonly999"]
    )
    assert registry["observation_used_for_power"] is False
    assert registry["raw_map_access"] is False


def test_committed_map_free_inputs_bind_exact_rows_and_shared_calibration() -> None:
    api = _api()
    inputs = api.load_accepted_inputs(REGISTRY)
    assert inputs.calibration_carriers.shape == (200, 32)
    assert inputs.arms["paired300"].carriers.shape == (100, 32)
    assert inputs.arms["cmbonly999"].carriers.shape == (799, 32)
    assert inputs.arms["paired300"].ids[0] == "00200"
    assert inputs.arms["paired300"].ids[-1] == "00299"
    assert inputs.arms["cmbonly999"].ids[-1] == "00999"
    assert "00970" not in inputs.arms["cmbonly999"].ids
    assert inputs.scale_rms > 0
    assert inputs.raw_maps_reopened is False


def test_adapter_builds_both_frozen_families_from_the_shared_calibration() -> None:
    api = _api()
    from scripts.observed_runs.planck_irrep_power_adapter import make_extractor

    inputs = api.load_accepted_inputs(REGISTRY)
    extractor, references = make_extractor(
        dict(inputs.metadata), inputs.calibration_carriers, inputs.source_identity
    )
    assert set(references) == set(api.FAMILIES)
    assert references[api.FAMILIES[0]].shape == (200, 10)
    assert references[api.FAMILIES[1]].shape == (200, 8)
    values, absence = extractor(inputs.arms["paired300"].carriers[0])
    assert absence == {}
    assert set(values) == set(api.FAMILIES)


def test_cell_plan_computes_zero_once_and_positive_trial_counts_exactly() -> None:
    api = _api()
    plan = api.cell_plan()
    assert len(plan) == 31
    assert [(cell.template_id, cell.amplitude) for cell in plan if cell.amplitude == 0] == [
        ("ZERO_BASELINE", 0.0)
    ]
    assert sum(cell.orientation_count for cell in plan if cell.amplitude > 0) == 30 * 32
    assert api.positive_trial_count("paired300") == 96_000
    assert api.positive_trial_count("cmbonly999") == 767_040


def test_checkpoint_is_bound_to_candidate_tree_registry_input_and_cell(tmp_path: Path) -> None:
    api = _api()
    ranks = np.arange(2 * 3 * 2 * 2 * 2, dtype=np.int32).reshape(2, 3, 2, 2, 2)
    identity = api.CheckpointIdentity(
        candidate_git_head="a" * 40,
        candidate_git_tree="b" * 40,
        registry_sha256="sha256:" + "c" * 64,
        input_content_id="sha256:" + "d" * 64,
        arm="paired300",
        template_id="Q_AXIAL",
        amplitude=1.0,
    )
    api.write_checkpoint(tmp_path / "cell", identity=identity, ranks=ranks, absences=[])
    loaded, absences = api.load_checkpoint(tmp_path / "cell", identity=identity)
    assert np.array_equal(loaded, ranks)
    assert absences == []
    changed = api.CheckpointIdentity(**{**identity.__dict__, "candidate_git_tree": "e" * 40})
    with pytest.raises(api.Wu008Error, match="identity"):
        api.load_checkpoint(tmp_path / "cell", identity=changed)


def test_runner_help_and_source_have_no_raw_map_network_or_github_action_path() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--arm" in result.stdout
    assert "--execute" in result.stdout
    assert "--replay-committed" in result.stdout
    source = SCRIPT.read_text(encoding="utf-8").lower()
    forbidden = ("healpy.read_map", "astropy.io.fits", "requests.", "urllib", "github actions")
    assert not any(token in source for token in forbidden)


def test_reviewed_terminal_cannot_succeed_without_exact_candidate_and_manifest_binding() -> None:
    api = _api()
    pending = {
        "format": api.TERMINAL_FORMAT,
        "state": "EXECUTED_PENDING_REVIEW",
        "work_unit": "PMG-WU-008",
        "candidate_git_head": "a" * 40,
        "candidate_git_tree": "b" * 40,
        "artifact_manifest_content_id": "sha256:" + "c" * 64,
        "real_host_execution": True,
        "replay_status": "MATCH",
        "raw_data_mutation": False,
        "claim_promotion": False,
    }
    review = {
        "format": api.REVIEW_FORMAT,
        "state": "PASS",
        "candidate_git_head": "a" * 40,
        "candidate_git_tree": "b" * 40,
        "artifact_manifest_content_id": "sha256:" + "c" * 64,
        "P0_remaining": 0,
        "P1_remaining": 0,
        "repair_rounds_used": 0,
        "plot_inspection": "PASS",
    }
    final = api.finalize_terminal(pending, review)
    assert final["state"] == "SUCCEEDED"
    assert final["next_executable_action"] == "PMG-WU-009"
    changed = dict(review)
    changed["candidate_git_tree"] = "d" * 40
    with pytest.raises(api.Wu008Error, match="identity|review"):
        api.finalize_terminal(pending, changed)


def test_registry_attachment_copy_is_exact() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["positive_injected_carriers"] == {
        "paired300": 96_000,
        "cmbonly999": 767_040,
    }
    assert payload["scope_limitation"].startswith(
        "Power of the registered functional at 200-reference calibration"
    )
