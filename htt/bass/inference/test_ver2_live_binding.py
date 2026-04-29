from __future__ import annotations

import json

import numpy as np
import pytest
import yaml

from bass.inference.__main__ import main
from bass.inference.live_binding import (
    FittingBlockedError,
    build_type_i_native_validation_problem,
    run_type_i_native_validation_posterior,
)


def test_build_type_i_native_validation_problem_is_bound_to_live_bass_outputs() -> None:
    problem = build_type_i_native_validation_problem(21)
    assert problem.solver_output.manifest.owner == "BASS"
    assert problem.observable_vector.manifest.owner == "BASS"
    assert problem.solver_output.metadata["tier_b_core_owner"] == "ver2_s1s2_native"
    assert problem.solver_output.metadata["theory_family"] == "I_orthogonal"
    assert problem.observable_vector.alm_features["bianchi_branch"] == "orthogonal"
    assert (
        problem.observable_vector.alm_features["local_boost_contract"]
        == "observer_side_only_not_applied_in_bass_output"
    )
    assert problem.dataset_kind == "type_i_native_validation"
    assert problem.covariance_readiness == "full"
    assert problem.fitting_ready is False
    assert problem.solver_output.metadata["fitting_gate_enforced"] is True
    assert problem.solver_output.metadata["fitting_gate_allowed"] is False
    assert problem.solver_output.metadata["fitting_allowed"] is False
    assert problem.solver_output.metadata["diagnostic_only"] is True
    assert "production_cutoff_gate" in problem.gate_decision.missing_gates
    assert problem.solver_output.metadata["production_cutoff_status"] == "development_cutoff"
    with pytest.raises(FittingBlockedError):
        problem.log_likelihood(np.zeros(3, dtype=float))


def test_run_type_i_native_validation_posterior_blocks_on_development_cutoff() -> None:
    with pytest.raises(FittingBlockedError) as exc:
        run_type_i_native_validation_posterior(
            seed=22,
            n_walkers=24,
            n_steps=40,
            burnin=10,
            parallel=False,
        )
    assert "production_cutoff_gate" in exc.value.gate_decision.missing_gates


def test_cli_accepts_type_i_native_validation_dataset_kind(tmp_path) -> None:
    config = {
        "dataset": {
            "kind": "type_i_native_validation",
        },
        "sampler": {
            "n_walkers": 24,
            "n_steps": 40,
            "burnin": 10,
            "parallel": False,
        },
        "outputs": {
            "summary_json": str(tmp_path / "bf06_live.json"),
            "summary_markdown": str(tmp_path / "bf06_live.md"),
            "posterior_dir": str(tmp_path / "posteriors"),
        },
    }
    path = tmp_path / "bf06_live.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    exit_code = main(["--config", str(path), "--seed", "23"])
    assert exit_code in {0, 1}
    assert (tmp_path / "bf06_live.json").exists()
    assert (tmp_path / "bf06_live.md").exists()
    assert not (tmp_path / "posteriors" / "type_i_native_validation.npz").exists()
    payload = json.loads((tmp_path / "bf06_live.json").read_text(encoding="utf-8"))
    assert payload["posterior"]["binding_origin"] == "solver_core_output"
    assert payload["dataset"]["kind"] == "type_i_native_validation"
    assert payload["dataset"]["observable_production_status"] == "production_candidate"
    assert payload["posterior"]["fitting_ready"] is False
    assert payload["posterior"]["sampler"] == "blocked_by_fitting_gate"
    assert "production_cutoff_gate" in payload["posterior"]["diagnostics"]["missing_gates"]
