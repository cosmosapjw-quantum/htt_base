"""Frozen ambient targets detect basis-coordinate confusion in support replay."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[2] / "scripts/observed_runs/check_r9_ambient_fibre.py"
spec = importlib.util.spec_from_file_location("ambient_fibre", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_frozen_ambient_target_survives_basis_changes_and_detects_wrong_target():
    result = module.compare()
    assert result["basis_count"] == 35
    assert result["negative_control"]["same_coordinates_change_ambient_target"]
    assert max(r["support_error"] for r in result["comparisons"]) < 1e-10
    assert max(r["ambient_witness_error"] for r in result["comparisons"]) < 1e-10


def test_cartesian_oracle_has_analytic_minimum_norm_and_feasible_witness():
    q, v, a = module.ambient_case()
    result = module.cartesian_reference(q, v, a)
    assert abs(result["eta"] - 3 * (v @ np.linalg.solve(np.eye(3) + 6 * q @ q / 5, v))) < 1e-10
    assert np.linalg.norm(np.einsum("ijk,jk->i", result["witness"], q) - v) < 1e-10
    assert abs(np.linalg.norm(result["witness"]) - 1) < 1e-10
    assert abs(np.sum(a * result["witness"]) - result["support"]) < 1e-10


def test_nonorthonormal_or_non_stf_coordinates_are_refused():
    q, v, a = module.ambient_case()
    non_stf = np.eye(27)[:7].reshape(7, 3, 3, 3)
    with pytest.raises(ValueError, match="orthonormal and STF"):
        module.check_basis(non_stf, q, v, a)
    with pytest.raises(ValueError, match="finite"):
        module.check_basis(np.full((7, 3, 3, 3), np.nan), q, v, a)
