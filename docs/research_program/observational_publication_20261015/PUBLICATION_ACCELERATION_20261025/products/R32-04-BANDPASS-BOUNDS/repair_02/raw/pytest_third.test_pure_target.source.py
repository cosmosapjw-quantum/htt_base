"""BP-03 regressions for a future formal repair packet; source only for now.

The prior 29-test module is preserved separately as old_29_regressions.py.
"""
from __future__ import annotations

import hashlib
import importlib.util
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
spec = importlib.util.spec_from_file_location("bandpass_bp03_candidate", HERE / "consumer.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


@pytest.fixture(scope="module")
def branches():
    import json

    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    data = json.loads(SOURCE.read_text())
    assert tuple(data["branches"]) == candidate.BRANCHES
    return data["branches"]


def inputs(branches, name, metric):
    branch = branches[name]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.asarray(branch["cmb_unity_responses"], float)
    d = candidate.D if metric == "common" else np.ones(9)
    assert np.array_equal(a, np.ones(7))
    return F, a, d, candidate.solve_metric(F, a, d)


def independent_svd_J0(Y, F, a, d):
    """Independent retained-matrix SVD: no call to identified or its K solve."""
    left, singular, _ = np.linalg.svd(F / d[None, :], full_matrices=False)
    Z = (left.T @ Y) / singular[:, None]
    b = (left.T @ a) / singular
    q = b / np.linalg.norm(b)
    return float(np.linalg.norm(Z - np.outer(q, q @ Z))**2)


def independent_high_precision_J0(Y, F, a, d):
    """120-digit Schur complement, distinct from the consumer residual solve."""
    mp = pytest.importorskip("mpmath")
    with mp.workdps(120):
        G = mp.matrix([[mp.mpf(float(F[i, j])) / mp.mpf(float(d[j]))
                        for j in range(9)] for i in range(7)])
        Kinv = (G * G.T)**-1
        aa = mp.matrix([mp.mpf(float(x)) for x in a])
        yy = mp.matrix([[mp.mpf(float(Y[i, j])) for j in range(24)]
                        for i in range(7)])
        z = Kinv * aa
        weighted = Kinv * yy
        ell2 = (aa.T * z)[0]
        quadratic = sum(yy[i, j] * weighted[i, j]
                        for i in range(7) for j in range(24))
        projection = yy.T * z
        return float(quadratic - sum(projection[j]**2 for j in range(24)) / ell2)


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
@pytest.mark.parametrize("scale", (1e-6, 1.0, 1e6))
@pytest.mark.parametrize("carrier", ("single", "mixed"))
def test_exact_repeated_rows_have_structural_set(branches, name, metric, scale, carrier):
    F, a, d, sol = inputs(branches, name, metric)
    s = np.zeros(24)
    if carrier == "single":
        s[0] = scale
    else:
        s = scale * np.array([(-1)**i * (i+1)/24 for i in range(24)])
    Y = np.tile(s, (7, 1))
    at_zero = candidate.identified(Y, F, a, d, sol, 0.0)
    assert at_zero["status"] == "SINGLETON_EXACT_STRUCTURAL"
    assert at_zero["J0"] == at_zero["radius"] == 0.0
    assert np.array_equal(at_zero["center"], s)
    for rho in (scale * 1e-200, scale):
        result = candidate.identified(Y, F, a, d, sol, rho)
        assert result["status"] == "BALL"
        assert result["radius"] > 0
        assert math.isclose(result["radius"], rho / sol["ell"], rel_tol=1e-12,
                            abs_tol=0)
        assert result["J0"] == 0
        assert np.array_equal(result["center"], s)
    unequal = Y.copy()
    unequal[6, 0] = np.nextafter(unequal[6, 0], math.inf)
    assert not np.all(unequal == unequal[0:1, :])
    result = candidate.identified(unequal, F, a, d, sol, 0.0)
    assert result["status"] == "EMPTY"
    assert result["radius"] is None


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
@pytest.mark.parametrize("scale", (1e-6, 1.0, 1e6))
def test_resolvable_near_target_sides_match_independent_svd(branches, name, metric, scale):
    F, a, d, sol = inputs(branches, name, metric)
    s = np.zeros(24)
    s[0] = scale
    Y = np.outer(a, s)
    Y[0, 0] += scale * 1e-4
    Y[6, 0] -= scale * 1e-4
    J0_svd = independent_svd_J0(Y, F, a, d)
    assert J0_svd > 0
    low = candidate.identified(Y, F, a, d, sol, .5 * math.sqrt(J0_svd))
    high = candidate.identified(Y, F, a, d, sol, 2 * math.sqrt(J0_svd))
    assert low["status"] == "EMPTY"
    assert high["status"] == "BALL"
    assert high["radius"] == pytest.approx(math.sqrt(3 * J0_svd) / sol["ell"],
                                            rel=1e-5)


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
@pytest.mark.parametrize("scale", (1e-6, 1.0, 1e6))
def test_unresolved_near_target_is_typed_not_false_empty(branches, name, metric, scale):
    F, a, d, sol = inputs(branches, name, metric)
    s = np.zeros(24)
    s[0] = scale
    Y = np.outer(a, s)
    Y[0, 0] += scale * 1e-12
    Y[6, 0] -= scale * 1e-12
    J0_high = independent_high_precision_J0(Y, F, a, d)
    assert J0_high > 0
    result = candidate.identified(Y, F, a, d, sol, math.sqrt(J0_high))
    assert result["status"] in {"BOUNDARY_UNCERTAIN", "NUMERIC_BOUNDARY_HOLD"}
    assert result["radius"] is None
    assert result["radius_uncertainty"]["reason"]
