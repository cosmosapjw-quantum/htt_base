"""BP-04 exact-binary contrast probes of returned 24D set geometry.

The reference eliminates the common target with H rows e_i-e_0 and solves a
6-row rational contrast problem. It never uses consumer K inverse, center,
residual, or J0 as the oracle.
"""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest
import sympy as sp


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bp04_candidate", HERE / "consumer.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def rat(x):
    return sp.Rational(*float(x).as_integer_ratio())


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
def test_exact_contrast_center_and_full24_boundary( branches, name, metric):
    branch = branches[name]
    F = np.asarray(branch["F2"]["matrix_7xk"], float)
    a = np.asarray(branch["cmb_unity_responses"], float)
    d = candidate.D if metric == "common" else np.ones(9)
    sol = candidate.solve_metric(F, a, d)
    G = sp.Matrix([[rat(F[i, j]) / rat(d[j]) for j in range(9)]
                   for i in range(7)])
    K = G * G.T
    W = (H * G * G.T * H.T).inv(method="DM")
    kh = K[0, :] * H.T
    ell2 = 1 / (K[0, 0] - (kh * W * kh.T)[0])
    unit = np.zeros(24)
    unit[0] = 1
    mixed = np.array([(-1)**j * (j+1) / 24 for j in range(24)], float)
    mixed /= np.linalg.norm(mixed)
    ncases = 0
    for scale in (1e-6, 1.0, 1e6):
        for relative_perturbation in (1e-4, 1e-12, 1e-14):
            for carrier in ("single", "mixed"):
                common = scale * (unit if carrier == "single" else mixed)
                Y = np.tile(common, (7, 1))
                Y[0, 0] += scale * relative_perturbation
                Y[6, 0] -= scale * relative_perturbation
                if carrier == "mixed":
                    Y[0, 13] += scale * relative_perturbation / 2
                    Y[6, 13] -= scale * relative_perturbation / 2
                y0 = [rat(x) for x in Y[0]]
                exact_center = []
                exact_J0 = sp.Rational(0)
                for j in range(24):
                    yj = sp.Matrix([rat(x) for x in Y[:, j]])
                    contrast = H * yj
                    exact_J0 += (contrast.T * W * contrast)[0]
                    exact_center.append(y0[j] - (kh * W * contrast)[0])
                assert exact_J0 > 0
                threshold = math.sqrt(float(exact_J0))
                for factor in (.5, 1 - 1e-7, 1.0, 1 + 1e-7, 2.0):
                    rho = factor * threshold
                    budget = rat(rho)**2
                    out = candidate.identified(Y, F, a, d, sol, rho)
                    context = (name, metric, scale, relative_perturbation,
                               carrier, factor, out["status"])
                    ncases += 1
                    if out["status"] == "EMPTY":
                        assert budget < exact_J0, context
                    elif out["status"] == "BALL":
                        assert budget > exact_J0, context
                        assert out["radius"] is not None and out["radius"] > 0, context
                        geometry = out["geometry_error"]
                        tolerance = 1e-9 * max(rho * rho, float(exact_J0))
                        assert geometry is not None, context
                        assert geometry["budget_image_error_bound"] <= tolerance, context
                        serialized_center = [rat(x) for x in out["center"]]
                        center_cost = exact_J0 + ell2 * sum(
                            (serialized_center[j] - exact_center[j])**2
                            for j in range(24))
                        assert float(center_cost - budget) <= tolerance, context
                        for direction in (unit, mixed):
                            witness = np.asarray(out["center"]) + out["radius"] * direction
                            witness_cost = exact_J0 + ell2 * sum(
                                (rat(witness[j]) - exact_center[j])**2
                                for j in range(24))
                            assert float(witness_cost - budget) <= tolerance, context
                        residual = out["residual_7x24"]
                        relation_error = math.sqrt(sum(float(
                            (rat(residual[i, j]) - rat(Y[i, j])
                             + rat(a[i]) * serialized_center[j])**2)
                            for i in range(7) for j in range(24)))
                        assert relation_error <= geometry["residual_relation_error"] * (1 + 1e-12), context
                    else:
                        assert out["status"] in {"NUMERIC_BOUNDARY_HOLD",
                                                  "BOUNDARY_UNCERTAIN"}, context
                        assert out["radius"] is None, context
                        assert out["radius_uncertainty"]["reason"], context
    assert ncases == 90
