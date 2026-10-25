"""H03 repair regressions. Execute only after the formal controller repair GO."""
import json
from pathlib import Path

import numpy as np
import pytest

import new_candidate as h03


TAU = 12.591587243743977
ORIGINAL = Path(
    "/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/"
    "observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/"
    "products/R32-03-H03-STRUCTURED"
)


@pytest.mark.parametrize(
    "offset,exact,status",
    [
        (0.0, True, "FINITE_FLOOR_EQUALITY"),
        (5e-10, False, "NUMERIC_BOUNDARY_FLOOR"),
        (-5e-10, False, "NUMERIC_BOUNDARY_FLOOR"),
        (0.25, False, "THRESHOLD_UNATTAINABLE_FOR_THIS_D"),
        (-0.25, False, "FINITE_CROSSING"),
    ],
)
def test_floor_status_and_both_budgets(offset, exact, status):
    floor = TAU + offset
    T0 = floor + 1.0
    ss = np.array([1.0])
    alpha = np.array([1.0])
    outcome, rho, lam, witness, _ = h03.threshold(
        ss, alpha, floor, 1.0, T0, TAU, exact_floor_equality=exact
    )
    qmin = h03.image_budget(outcome, T0, floor, TAU)
    assert outcome == status
    if exact:
        assert rho == 1.0 and lam == 0.0
        assert np.array_equal(witness, alpha)
        assert qmin == pytest.approx(np.sqrt(T0 - TAU))
    elif status == "FINITE_CROSSING":
        assert 0 < rho < 1.0 and qmin > 0
    else:
        assert rho is None and witness is None and qmin is None


def test_exact_baseline_adequacy_keeps_zero_budgets():
    outcome, rho, _, _, _ = h03.threshold(
        np.array([1.0]), np.array([1.0]), TAU - 1, 1.0, TAU, TAU,
        exact_baseline_adequate=True,
    )
    assert outcome == "ALREADY_ADEQUATE" and rho == 0
    assert h03.image_budget(outcome, TAU, TAU - 1, TAU) == 0


def test_unknown_projected_roundoff_is_held():
    E = np.eye(2)
    B = np.eye(2) * 1e-14
    with pytest.raises(ValueError, match="NUMERIC_RANK_HOLD"):
        h03.svd_data(B, E, np.ones(2))


def retained_matrices():
    carrier = json.loads((ORIGINAL / "generated/source_carrier.json").read_text())
    return {key: np.asarray(carrier[key], dtype=float) for key in (
        "y_signed_12_km_s_Mpc", "C_dipole_12x12", "L_cholesky", "X_12x6",
        "Q_X_whitened", "P_projector", "r_signed_whitened_12",
        "FP_distance_weight_fractions", "z_centers",
    )}, float(carrier["width_z"])


def test_D_equals_X_uses_production_path_at_zero_finite_and_saturation():
    data, _ = retained_matrices()
    y, C, L, X, Q, Pproj, r, _, _ = data.values()
    A = h03.solve_triangular(L, X, lower=True)
    T0 = float(r @ r)
    with pytest.raises(ValueError, match="NUMERIC_RANK_HOLD"):
        h03.analyse("D_equals_X", X, y, C, L, X, A, Q, Pproj, r, T0, TAU)
    result = h03.analyse(
        "D_equals_X", X, y, C, L, X, A, Q, Pproj, r, T0, TAU,
        known_projected_zero=True,
    )
    assert result["rank_B"] == 0
    assert result["status"] == "THRESHOLD_UNATTAINABLE_FOR_THIS_D"
    assert result["rho95"] is None and result["q_min_restricted"] is None
    assert result["rho_sat"] == 0
    assert np.allclose(result["curve"]["T_min"], T0, atol=1e-9, rtol=0)
    for rho in (0.0, 1.0, 10.0):
        value, coefficients = h03.curve_at_rho(
            rho, np.array([]), np.array([]), result["T_floor"], 0.0, T0
        )
        assert value == pytest.approx(T0, abs=1e-9)
        assert coefficients.size == 0


def test_original_three_design_frontiers_stay_within_frozen_tolerances():
    data, width = retained_matrices()
    y, C, L, X, Q, Pproj, r, fp, z = data.values()
    A = h03.solve_triangular(L, X, lower=True)
    T0 = float(r @ r)
    t = (z - .04) / width
    f = fp - fp[0]
    Dz = np.kron(t[:, None], np.eye(3))
    Df = np.kron(f[:, None], np.eye(3))
    designs = {"depth_slope": Dz, "FP_composition": Df,
               "joint": np.column_stack((Dz, Df))}
    old = json.loads((ORIGINAL / "generated/analysis.json").read_text())["designs"]
    for name, D in designs.items():
        result = h03.analyse(name, D, y, C, L, X, A, Q, Pproj, r, T0, TAU)
        expected = old[name]
        assert result["rank_B"] == expected["rank_B"]
        assert result["status"] == expected["status"]
        assert result["T_floor"] == pytest.approx(expected["T_floor"], abs=1e-8)
        if expected["rho95"] is None:
            assert result["rho95"] is None
        else:
            assert result["rho95"] == pytest.approx(expected["rho95"], abs=1e-8)
        if expected["q_min_restricted"] is None:
            assert result["q_min_restricted"] is None
        else:
            assert result["q_min_restricted"] == pytest.approx(
                expected["q_min_restricted"], abs=1e-8
            )
