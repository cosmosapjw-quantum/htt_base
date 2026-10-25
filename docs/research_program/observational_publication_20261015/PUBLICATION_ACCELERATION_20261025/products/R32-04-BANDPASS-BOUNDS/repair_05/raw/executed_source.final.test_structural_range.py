"""BP-05 exact-rational repeated-row output and rounded full24 witnesses."""
import importlib.util
import json
from pathlib import Path

import mpmath as mp
import numpy as np
import pytest
import sympy as sp

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("structural_candidate", HERE / "consumer.py")
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)
R = lambda x: sp.Rational(*float(x).as_integer_ratio())
H = sp.zeros(6, 7)
for k in range(6):
    H[k, 0], H[k, k + 1] = -1, 1


def exact_ell_squared(F, d):
    """Independent row-contrast inverse, not the candidate's K inverse."""
    G = sp.Matrix([[R(F[i, j]) / R(d[j]) for j in range(9)]
                   for i in range(7)])
    A = H * G
    W = (A * A.T).inv(method="DM")
    h = G[0, :] * A.T
    return 1 / ((G[0, :] * G[0, :].T)[0] - (h * W * h.T)[0])


def serialized(out):
    return json.loads(json.dumps({k: v.tolist() if isinstance(v, np.ndarray) else v
                                  for k, v in out.items()}, allow_nan=False))


@pytest.fixture(scope="module")
def branches():
    import hashlib
    assert hashlib.sha256(consumer.SOURCE.read_bytes()).hexdigest() == consumer.SOURCE_SHA
    return json.loads(consumer.SOURCE.read_text())["branches"]


@pytest.mark.parametrize("branch", consumer.BRANCHES)
@pytest.mark.parametrize("metric", ("common", "raw"))
def test_all_structural_balls_share_full24_output_policy(branches, branch, metric):
    F = np.asarray(branches[branch]["F2"]["matrix_7xk"], float)
    a = np.ones(7)
    d = consumer.D if metric == "common" else np.ones(9)
    sol = consumer.solve_metric(F, a, d)
    ell2 = exact_ell_squared(F, d)
    single = np.zeros(24); single[0] = 1e-6
    mixed = np.asarray([(-1)**j * (j+1) * 1e-6 / 24 for j in range(24)])
    directions = [np.eye(24)[j] for j in range(24)] + [mixed / np.linalg.norm(mixed)]
    normal_ball = False
    for center in (np.zeros(24), single, mixed):
        Y = np.tile(center, (7, 1))
        for rho in (0.0, float.fromhex("0x0.0000000000001p-1022"),
                    float.fromhex("0x0.0000000000040p-1022"),
                    float.fromhex("0x0.00000000007e8p-1022"), 1e-4):
            out = serialized(consumer.identified(Y, F, a, d, sol, rho))
            context = (branch, metric, center[0], rho.hex(), out["status"])
            assert out["center"] == center.tolist() and out["J0"] == 0.0, context
            if rho == 0:
                assert out["status"] in {"SINGLETON_EXACT_ZERO",
                                         "SINGLETON_EXACT_STRUCTURAL"}, context
                assert out["radius"] == 0.0, context
                continue
            if out["status"] == "NUMERIC_RANGE_HOLD":
                assert out["radius"] is None and out["radius_uncertainty"]["reason"], context
                continue
            assert out["status"] == "BALL" and out["radius"] > 0, context
            assert out["geometry_error"]["within_fixed_policy"], context
            if rho == 1e-4 and not np.any(center):
                normal_ball = True
            budget = R(rho)**2
            radius = R(out["radius"])
            tolerance = budget / 10**9
            # Since the exact center equals the serialized row, this is the
            # exact cost on every direction of the entire 24-sphere.
            sphere_error = abs(ell2 * radius**2 - budget)
            assert sphere_error <= tolerance, context
            with mp.workdps(120):
                assert mp.mpf(int(sphere_error.p)) / int(sphere_error.q) <= mp.mpf(
                    out["geometry_error"]["budget_image_error_bound"]), context
            # These are downstream binary64 samples, not members of the
            # abstract returned sphere by definition. Record their behavior
            # separately; the exact all-direction sphere is checked above.
            sampled_relative_errors = []
            for direction in directions:
                for sign in (-1, 1):
                    witness = np.asarray(out["center"]) + sign * out["radius"] * direction
                    exact_cost = ell2 * sum((R(witness[j]) - R(center[j]))**2
                                            for j in range(24))
                    sampled_relative_errors.append(abs(exact_cost - budget) / budget)
            assert len(sampled_relative_errors) == 50, context
    assert normal_ball, (branch, metric, "normal positive BALL control missing")


def test_exact_reviewed_adjacent_hex_inputs_are_typed_holds(branches):
    F = np.asarray(branches["A_BT_1e-06"]["F2"]["matrix_7xk"], float)
    a, d = np.ones(7), np.ones(9)
    sol = consumer.solve_metric(F, a, d)
    Y = np.zeros((7, 24))
    ell2 = exact_ell_squared(F, d)
    reviewed = (("0x0.0000000000040p-1022", "0x0.0000000000001p-1022", -1),
                ("0x0.00000000007e8p-1022", "0x0.0000000000022p-1022", 1))
    for rho_hex, old_radius_hex, sign in reviewed:
        out = serialized(consumer.identified(Y, F, a, d, sol,
                                             float.fromhex(rho_hex)))
        assert out["status"] == "NUMERIC_RANGE_HOLD", rho_hex
        assert out["radius"] is None and out["radius_uncertainty"]["reason"], rho_hex
        old_cost_ratio = (ell2 * R(float.fromhex(old_radius_hex))**2
                          / R(float.fromhex(rho_hex))**2)
        assert sign * (old_cost_ratio - 1) > sp.Rational(1, 10**9), rho_hex


def test_tiny_translated_abstract_ball_has_collapsed_binary64_sample(branches):
    F = np.asarray(branches["A_BT_1e-06"]["F2"]["matrix_7xk"], float)
    a, d = np.ones(7), consumer.D
    sol = consumer.solve_metric(F, a, d)
    center = np.zeros(24); center[0] = 1e-6
    rho = 1e-6 * 1e-200
    out = serialized(consumer.identified(np.tile(center, (7, 1)),
                                         F, a, d, sol, rho))
    assert out["status"] == "BALL" and out["radius"] > 0
    assert out["geometry_error"]["within_fixed_policy"]
    assert mp.mpf(out["geometry_error"]["budget_image_relative_error_bound"]) <= mp.mpf('1e-9')
    # A later float addition can collapse without invalidating the returned
    # real set or the exact-rational all-direction certificate.
    direction = np.zeros(24); direction[0] = 1
    sampled = np.asarray(out["center"]) + out["radius"] * direction
    assert np.array_equal(sampled, np.asarray(out["center"]))
