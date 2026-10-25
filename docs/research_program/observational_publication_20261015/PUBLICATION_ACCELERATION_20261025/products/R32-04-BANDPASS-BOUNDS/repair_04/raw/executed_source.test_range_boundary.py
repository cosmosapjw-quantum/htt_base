"""BP-05 bounded binary64 range tests with exact-rational row contrasts."""
import importlib.util
import json
import math
import sys
from pathlib import Path

import mpmath as mp
import numpy as np
import pytest
import sympy as sp


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bp05_candidate", HERE / "consumer.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def rat(x):
    return sp.Rational(*float(x).as_integer_ratio())


def finite_json(out):
    return json.loads(json.dumps({k: v.tolist() if isinstance(v, np.ndarray) else v
                                  for k, v in out.items()}, allow_nan=False))


H = sp.zeros(6, 7)
for i in range(6):
    H[i, 0] = -1
    H[i, i + 1] = 1


@pytest.fixture(scope="module")
def branches():
    import hashlib
    assert hashlib.sha256(candidate.SOURCE.read_bytes()).hexdigest() == candidate.SOURCE_SHA
    return json.loads(candidate.SOURCE.read_text())["branches"]


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
def test_bounded_normal_subnormal_matrix(branches, name, metric):
    branch = branches[name]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.ones(7)
    d = candidate.D if metric == "common" else np.ones(9)
    sol = candidate.solve_metric(F, a, d)
    G = sp.Matrix([[rat(F[i, j]) / rat(d[j]) for j in range(9)]
                   for i in range(7)])
    K = G * G.T
    W = (H * K * H.T).inv(method="DM")
    kh = K[0, :] * H.T
    ell2 = 1 / (K[0, 0] - (kh * W * kh.T)[0])
    single = np.zeros(24); single[0] = 1.0
    mixed = np.array([(-1)**j * (j+1)/24 for j in range(24)], float)
    mixed /= np.linalg.norm(mixed)
    cases = 0
    for scale in (1e-148, 1e-150, 1e-154, 1e-160):
        for perturb in (1e-4, 1e-12):
            for carrier in (single, mixed):
                Y = np.tile(scale * carrier, (7, 1))
                Y[0, 0] += scale * perturb
                Y[6, 0] -= scale * perturb
                if carrier is mixed:
                    Y[0, 13] += scale * perturb / 2
                    Y[6, 13] -= scale * perturb / 2
                exact_center = []
                exact_J0 = sp.Rational(0)
                for j in range(24):
                    col = sp.Matrix([rat(x) for x in Y[:, j]])
                    contrast = H * col
                    exact_J0 += (contrast.T * W * contrast)[0]
                    exact_center.append(col[0] - (kh * W * contrast)[0])
                assert exact_J0 > 0
                for factor in (.5, 2.0):
                    with mp.workdps(100):
                        rho = factor * float(mp.sqrt(
                            mp.mpf(int(exact_J0.p)) / int(exact_J0.q)))
                    if rho == 0:
                        # The test input itself cannot encode a positive budget.
                        continue
                    budget = rat(rho)**2
                    out = finite_json(candidate.identified(Y, F, a, d, sol, rho))
                    cases += 1
                    context = (name, metric, scale, perturb, factor, out["status"])
                    if out["status"] == "EMPTY":
                        assert budget < exact_J0, context
                    elif out["status"] == "BALL":
                        assert budget > exact_J0 and out["radius"] > 0, context
                        assert out["geometry_error"]["budget_image_error_bound"] > 0, context
                        with mp.workdps(120):
                            to_mp = lambda q: mp.mpf(int(q.p)) / int(q.q)
                            b = to_mp(budget); j0 = to_mp(exact_J0)
                            e2 = to_mp(ell2); r = mp.mpf(out["radius"])
                            dc = mp.sqrt(sum((mp.mpf(out["center"][j])
                                              - to_mp(exact_center[j]))**2
                                             for j in range(24)))
                            upper = j0 + e2 * (r + dc)**2
                            lower = j0 + e2 * (r - dc)**2
                            deviation = max(abs(upper-b), abs(lower-b))
                            tolerance = mp.mpf('1e-9') * max(b, j0)
                            assert deviation <= tolerance, context
                            assert deviation <= mp.mpf(out["geometry_error"]["budget_image_error_bound"]), context
                            for direction in (single, mixed):
                                witness = np.asarray(out["center"]) + out["radius"] * direction
                                cost = j0 + e2 * sum((mp.mpf(float(witness[j]))
                                                      - to_mp(exact_center[j]))**2
                                                     for j in range(24))
                                assert cost-b <= tolerance, context
                    else:
                        assert out["status"] in {"NUMERIC_RANGE_HOLD",
                                                  "NUMERIC_BOUNDARY_HOLD",
                                                  "BOUNDARY_UNCERTAIN"}, context
                        assert out["radius"] is None and out["radius_uncertainty"]["reason"], context
    assert cases == 32


def test_exact_bp05_subnormal_reproducer(branches):
    branch = branches["A_BT_1e-06"]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.ones(7); d = np.ones(9)
    Y = np.zeros((7, 24))
    Y[:, 0] = [float.fromhex(x) for x in (
        "0x1.a2fe76a3fb140p-499", "0x1.a2fe76a3f9475p-499",
        "0x1.a2fe76a3f9475p-499", "0x1.a2fe76a3f9475p-499",
        "0x1.a2fe76a3f9475p-499", "0x1.a2fe76a3f9475p-499",
        "0x1.a2fe76a3f77aap-499")]
    rho = float.fromhex("0x1.1b1bf25a690e5p-535")
    out = finite_json(candidate.identified(Y, F, a, d,
                                            candidate.solve_metric(F, a, d), rho))
    assert out["status"] == "NUMERIC_RANGE_HOLD"
    assert out["radius"] is None
    assert "tolerance" in out["radius_uncertainty"]["reason"]


@pytest.mark.parametrize("name", candidate.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
def test_minimum_subnormal_structural_radius_is_held(branches, name, metric):
    branch = branches[name]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.ones(7)
    d = candidate.D if metric == "common" else np.ones(9)
    sol = candidate.solve_metric(F, a, d)
    Y = np.zeros((7, 24))
    rho = float.fromhex("0x0.0000000000001p-1022")
    out = finite_json(candidate.identified(Y, F, a, d, sol, rho))
    assert out["status"] == "NUMERIC_RANGE_HOLD"
    assert out["radius"] is None and out["J0"] == 0
    assert out["radius_uncertainty"]["reason"]


def test_overflow_and_nonfinite_domains(branches):
    branch = branches["A_BT_1e-06"]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.ones(7); d = np.ones(9)
    sol = candidate.solve_metric(F, a, d)
    Y = np.zeros((7, 24)); Y[0, 0] = 1
    with pytest.raises(ValueError):
        candidate.identified(Y, F, a, d, sol, sys.float_info.max)
    Y[0, 0] = math.inf
    with pytest.raises(ValueError):
        candidate.identified(Y, F, a, d, sol, 1.0)
    Y[:] = sys.float_info.max / 2
    Y[6, 0] = np.nextafter(Y[6, 0], math.inf)
    out = finite_json(candidate.identified(Y, F, a, d, sol, 1.0))
    assert out["status"] == "NUMERIC_RANGE_HOLD"
    assert out["radius"] is None and out["J0"] is None
