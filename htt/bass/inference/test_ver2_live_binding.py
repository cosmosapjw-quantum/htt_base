from __future__ import annotations

import numpy as np
import pytest
import yaml

from bass.inference.__main__ import main
from bass.inference.live_binding import (
    build_type_i_native_validation_problem,
    run_type_i_native_validation_posterior,
)


def test_build_type_i_native_validation_problem_is_bound_to_live_bass_outputs() -> None:
    problem = build_type_i_native_validation_problem(21)
    assert problem.solver_output.manifest.owner == "BASS"
    assert problem.observable_vector.manifest.owner == "BASS"
    assert problem.solver_output.metadata["tier_b_core_owner"] == "ver2_s1s2_native"
    assert problem.dataset_kind == "type_i_native_validation"
    assert np.isfinite(problem.log_likelihood(np.zeros(3, dtype=float)))


def test_run_type_i_native_validation_posterior_returns_live_sampler_metadata() -> None:
    problem, posterior = run_type_i_native_validation_posterior(
        seed=22,
        n_walkers=24,
        n_steps=80,
        burnin=20,
        parallel=False,
    )
    assert problem.dataset_kind == "type_i_native_validation"
    assert posterior.samples.shape[-1] == 3
    assert posterior.config["parameter_names"] == ("observer_boost",)
    assert posterior.sampler.startswith("emcee-")


def test_cli_accepts_type_i_native_validation_dataset_kind(tmp_path) -> None:
    config = {
        "dataset": {
            "kind": "type_i_native_validation",
        },
        "sampler": {
            "n_walkers": 24,
            "n_steps": 80,
            "burnin": 20,
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
    assert (tmp_path / "posteriors" / "type_i_native_validation.npz").exists()
