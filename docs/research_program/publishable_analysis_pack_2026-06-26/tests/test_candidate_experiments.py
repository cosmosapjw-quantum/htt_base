import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "candidate_experiments.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("candidate_experiments", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_rank_evalue_witness_passes():
    module = _load_module()
    result = module.rank_evalue_experiment(n_sims=20_000)
    assert result["pass"] is True
    assert result["rank"] == 2
    assert max(result["blind_column_norms"]) <= 1e-12
    assert result["claim_tier"] == "synthetic_theorem_witness"


def test_boltzmann_visibility_witness_passes():
    module = _load_module()
    result = module.boltzmann_visibility_experiment(n_grid=2048)
    assert result["pass"] is True
    assert result["bounds_ok"] is True
    assert result["small_k_scaling_ok"] is True
    assert result["volterra_ode_max_error"] < 2e-3
    assert result["depth_gap_for_growing_source"] > 1.0


def test_local_global_response_witness_passes():
    module = _load_module()
    result = module.local_global_response_experiment()
    assert result["pass"] is True
    assert result["candidate_status"] == "candidate"
    assert result["global_residual_after_local_systematic_projection"] > 0.25


def test_run_all_is_synthetic_and_passes():
    module = _load_module()
    payload = module.run_all()
    assert payload["all_pass"] is True
    assert payload["native_solver_result"] is False
    assert payload["claim_tier"] == "synthetic_mechanics_only"

