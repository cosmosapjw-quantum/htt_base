"""Targeted R32-04 BP-01/BP-02 regressions; execute only after formal GO."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest


HERE = Path(__file__).resolve().parent
SOURCE = Path(
    "/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/"
    "observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/"
    "evidence/R31/report/data/RESULT.json"
)
SOURCE_SHA = "b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f"
spec = importlib.util.spec_from_file_location("bandpass_candidate", HERE / "consumer.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


@pytest.fixture(scope="module")
def frozen_branches():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    source = json.loads(SOURCE.read_text())
    assert tuple(source["branches"]) == candidate.BRANCHES
    return source["branches"]


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
def test_budget_scaling_and_boundary(frozen_branches, name, metric):
    branch = frozen_branches[name]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.asarray(branch["cmb_unity_responses"], float)
    d = candidate.D if metric == "common" else np.ones(9)
    sol = candidate.solve_metric(F, a, d)
    zero = np.zeros((7, 24))
    at_zero = candidate.identified(zero, F, a, d, sol, 0)
    assert at_zero["status"] == "SINGLETON_EXACT_ZERO"
    assert at_zero["radius"] == 0
    assert at_zero["radius_uncertainty"] is None
    for rho in (1.0, 1e-6):
        result = candidate.identified(zero, F, a, d, sol, rho)
        assert result["status"] == "BALL"
        assert result["radius"] == pytest.approx(rho / sol["ell"], rel=1e-12)
        assert np.array_equal(result["center"], np.zeros(24))
    if name == candidate.BRANCHES[0] and metric == "common":
        assert candidate.identified(zero, F, a, d, sol, 1e-6)["radius"] == pytest.approx(
            3.206791803148725e-7, rel=1e-12
        )

    Y = np.zeros((7, 24))
    Y[:, 0] = F[:, 0] + .2 * F[:, 3]
    Y[:, 1] = -.4 * F[:, 2]
    Y[:, 13] = .3 * a + .1 * F[:, 8]
    J0 = candidate.identified(Y, F, a, d, sol, 0)["J0"]
    assert J0 > 0
    rho_low = .5 * math.sqrt(J0)
    rho_edge = math.sqrt(J0)
    rho_ball = math.sqrt(J0 + sol["ell2"] * .5**2)
    base = [candidate.identified(Y, F, a, d, sol, rho)
            for rho in (rho_low, rho_edge, rho_ball)]
    assert [item["status"] for item in base] == [
        "EMPTY", "BOUNDARY_UNCERTAIN", "BALL"
    ]
    assert base[0]["radius"] is None
    assert base[1]["radius"] is None
    assert base[1]["radius_uncertainty"]["squared_budget_tolerance"] > 0
    assert base[2]["radius"] == pytest.approx(.5, rel=1e-9)
    for amplitude_scale in (1e-6, 1e6):
        scaled = [candidate.identified(amplitude_scale * Y, F, a, d, sol,
                                       amplitude_scale * rho)
                  for rho in (rho_low, rho_edge, rho_ball)]
        assert [item["status"] for item in scaled] == [
            "EMPTY", "BOUNDARY_UNCERTAIN", "BALL"
        ]
        assert scaled[2]["radius"] == pytest.approx(amplitude_scale * .5, rel=1e-9)
        assert scaled[2]["center"] == pytest.approx(
            amplitude_scale * base[2]["center"], rel=1e-10, abs=1e-10 * amplitude_scale
        )
        assert scaled[0]["J0"] == pytest.approx(amplitude_scale**2 * J0, rel=1e-10)


@pytest.mark.parametrize("rho", (-1.0, float("nan"), float("inf"), -float("inf"), 1e200))
def test_invalid_budget_rejected(frozen_branches, rho):
    branch = frozen_branches[candidate.BRANCHES[0]]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.asarray(branch["cmb_unity_responses"], float)
    d = candidate.D
    sol = candidate.solve_metric(F, a, d)
    with pytest.raises(ValueError, match="rho"):
        candidate.identified(np.zeros((7, 24)), F, a, d, sol, rho)


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
def test_exported_null_vectors_are_in_declared_coordinates(frozen_branches, name, metric):
    branch = frozen_branches[name]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.asarray(branch["cmb_unity_responses"], float)
    d = candidate.D if metric == "common" else np.ones(9)
    sol = candidate.solve_metric(F, a, d)
    exported = candidate.compact(sol)
    N_c = np.asarray(exported["coefficient_nullspace_directions_2x9"]).T
    N_z = np.asarray(exported["whitened_nullspace_directions_2x9"]).T
    G = F / d[None, :]
    assert N_c.shape == N_z.shape == (9, 2)
    assert N_c == pytest.approx(N_z / d[:, None])
    assert np.linalg.norm(G @ N_z) / np.linalg.norm(G) <= 1e-10
    assert np.linalg.norm(F @ N_c) / np.linalg.norm(F) <= 1e-10
    assert N_c.T @ (d[:, None]**2 * N_c) == pytest.approx(np.eye(2), abs=1e-10)
    assert N_c.T @ (d**2 * sol["c"]) == pytest.approx(np.zeros(2), abs=1e-10)
    lift = np.kron(N_c, np.eye(24))
    assert np.linalg.norm(np.kron(F, np.eye(24)) @ lift) / (
        np.linalg.norm(F) * np.linalg.norm(lift)) <= 1e-10
