"""Synthetic finite-algebra checks for the R2 candidate, not a CMB fit."""
import json
from pathlib import Path

import numpy as np
from scipy.stats import chi2


def main():
    items = {}
    directions = {
        "triaxial": np.diag([1.0, -1.0, 0.0]) / np.sqrt(2),
        "axisymmetric": np.diag([2.0, -1.0, -1.0]) / np.sqrt(6),
    }
    for name, e in directions.items():
        t = 0.6 * e
        f = np.sum(t * t)
        items[name] = {
            "F": float(f),
            "amplitude_fraction": float(np.sqrt(f)),
            "deviation_percent": float(100 * (1 - np.sqrt(f))),
            "shape_chi": float(np.sqrt(6) * np.trace(t @ t @ t) / f**1.5),
        }

    r = np.array([[1.0, 1.0], [0.0, 0.0]])
    h = r.T @ r
    projection = np.linalg.pinv(h) @ h
    true = np.array([0.4, 0.2])
    estimate = np.linalg.pinv(h) @ r.T @ (r @ true)
    vertices = np.array([[x, y] for x in [-1.0, 1.0] for y in [-1.0, 1.0]])
    u = np.array([1.0, 1.0]) / np.sqrt(2)
    null = np.array([1.0, -1.0]) / np.sqrt(2)
    items["identified_subspace"] = {
        "H": h.tolist(),
        "projection": projection.tolist(),
        "estimate": estimate.tolist(),
        "projected_bound_radius": float(np.max(np.abs(vertices @ projection.T @ u))),
        "null_response_norm": float(np.linalg.norm(r @ null)),
    }
    items["rank_fairness"] = {
        "same_amplitude_fraction": 0.6,
        "same_component_noise": 0.2,
        "score": 9.0,
        "chi2_df3_survival": float(chi2.sf(9, 3)),
        "chi2_df5_survival": float(chi2.sf(9, 5)),
    }
    items["marginal_vs_joint"] = {
        "two_fractions": [0.8, 0.8],
        "product_ball_gauge": 0.8,
        "coupled_ellipsoid_gauge": float(np.sqrt(2 * 0.8**2)),
    }
    a, b = np.array([0.3, 0.4]), np.array([0.2, 0.1])
    fa, fb = float(a @ a), float(b @ b)
    growth = np.outer(a, b) / fb
    items["tensor_growth_identity"] = {
        "Fa_over_Fb": fa / fb,
        "G_frobenius_sq": float(np.sum(growth * growth)),
    }
    q = 0.2
    tail_tensor = np.zeros((2, 2))
    tail = 0.0
    for t, w in zip(
        [np.array([0.0, 0.0]), np.array([0.3, 0.4]), np.array([1.0, 0.0])],
        [0.2, 0.5, 0.3],
    ):
        f = float(t @ t)
        if f > q:
            tail_tensor += w * np.outer(t, t) / f
            tail += w
    items["tensor_tail_identity"] = {
        "threshold": q,
        "tensor": tail_tensor.tolist(),
        "trace": float(np.trace(tail_tensor)),
        "scalar_tail": tail,
    }
    nuisance = np.array([[0.0], [1.0]])
    p = np.eye(2) - nuisance @ np.linalg.pinv(nuisance.T @ nuisance) @ nuisance.T
    items["nuisance_rank"] = {
        "P": p.tolist(),
        "H": p.tolist(),
        "rank": int(np.linalg.matrix_rank(p)),
    }
    assert abs(fa / fb - np.sum(growth * growth)) < 1e-12
    assert abs(np.trace(tail_tensor) - tail) < 1e-12
    assert np.linalg.norm(projection @ true - estimate) < 1e-12
    assert items["marginal_vs_joint"]["coupled_ellipsoid_gauge"] > 1
    output = {"status": "NUMERICALLY_CHECKED_SYNTHETIC_ALGEBRA_ONLY", "items": items}
    Path(__file__).with_suffix(".json").write_text(json.dumps(output, indent=2) + "\n")
    print("SYNTHETIC_ALGEBRA_CHECKS_COMPLETED")


if __name__ == "__main__":
    main()
