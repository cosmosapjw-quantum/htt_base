#!/usr/bin/env python3
"""Consume the frozen R31 seven-frequency, nine-moment matrices; no integration.

The only data input is the retained R31 RESULT.json.  Outputs are conditional
linear-algebra products under the jointly bounded signed moment class.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import cho_factor, cho_solve, null_space, solve_triangular

HERE = Path(__file__).resolve().parent
P = HERE.parents[2]  # repair_02 is nested one level below the original product
SOURCE = P / "evidence/R31/report/data/RESULT.json"
SOURCE_SHA = "b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f"
BRANCHES = ("A_BT_1e-07", "A_BT_1e-08", "A_BT_1e-06",
            "B_BT_1e-07", "B_BT_1e-08", "B_BT_1e-06")
FREQUENCIES = ("030", "044", "070", "100", "143", "217", "353PSB")
MOMENTS = ("s", "s_beta", "d", "d_beta", "d_t", "s_betabeta",
           "d_betabeta", "d_beta_t", "d_tt")
D = np.array((1.261652382369369, .1777139521270542,
              1.1309894216176297, .09451923139372441,
              .04109240642871376, .1151042544103929,
              .07145402059880916, .022520789584731377,
              .09386151314750793), dtype=float)
RAW_REFERENCE = (59.59210452696802, 59.59209151806858,
                 59.592192355037646, 59.57284170474581,
                 59.57282871526661, 59.57292946657371)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def coord_names() -> list[str]:
    out = []
    for sector, ell in (("E", 2), ("E", 3), ("B", 2), ("B", 3)):
        out.append(f"{sector}{ell}:m0")
        for m in range(1, ell + 1):
            out += [f"{sector}{ell}:sqrt2Re_m{m}", f"{sector}{ell}:-sqrt2Im_m{m}"]
    require(len(out) == 24, "coordinate length")
    return out


def solve_metric(F: np.ndarray, a: np.ndarray, d: np.ndarray) -> dict:
    """SPD K Cholesky solve and independent scaled SVD diagnostics."""
    G = F / d[None, :]
    u, sigma, vt = np.linalg.svd(G, full_matrices=True)
    require(sigma[-1] / sigma[0] > 1e-10, "seven resolved singular values")
    K = G @ G.T
    chol = cho_factor(K, lower=True, check_finite=True)
    z = cho_solve(chol, a)
    Kinv = cho_solve(chol, np.eye(7))
    c = (F.T @ z) / d**2
    ell2 = float(a @ z)
    ell = math.sqrt(ell2)
    projection = u[:, :7].T @ a
    contributions = (projection / sigma) ** 2
    ell_svd = math.sqrt(float(np.sum(contributions)))
    rel_resid = np.linalg.norm(F @ c - a) / np.linalg.norm(a)
    kkt = np.linalg.norm(d**2 * c - F.T @ z) / max(1.0, np.linalg.norm(F.T @ z))
    N_z = null_space(G)
    require(N_z.shape == (9, 2), "coefficient null dimension")
    N_c = N_z / d[:, None]  # z=diag(d)c; only N_c is in moment coordinates.
    orth = np.linalg.norm(N_c.T @ (d**2 * c)) / max(1.0, np.linalg.norm(d * c))
    test_n = N_c @ np.array([.31, -.47])
    increment = float(np.sum((d * (c + test_n)) ** 2) - ell2)
    predicted_increment = float(np.sum((d * test_n) ** 2))
    null_G = np.linalg.norm(G @ N_z) / np.linalg.norm(G)
    null_F = np.linalg.norm(F @ N_c) / np.linalg.norm(F)
    null_metric = np.linalg.norm(N_c.T @ (d[:, None]**2 * N_c) - np.eye(2))
    lift = np.kron(N_c, np.eye(24))
    null_full24 = np.linalg.norm(np.kron(F, np.eye(24)) @ lift) / (
        np.linalg.norm(F) * np.linalg.norm(lift))
    require(rel_resid <= 1e-10, f"Fc=a residual {rel_resid}")
    require(kkt <= 1e-10, f"KKT residual {kkt}")
    require(abs(ell - ell_svd) <= 1e-10 * ell, "SVD/Cholesky budget")
    require(orth <= 1e-10, "null orthogonality")
    require(null_G <= 1e-10, "whitened null equation")
    require(null_F <= 1e-10, "original coefficient null equation")
    require(null_metric <= 1e-10, "M-normalized coefficient nullspace")
    require(null_full24 <= 1e-10, "full24 coefficient null lift")
    require(abs(increment - predicted_increment) <= 1e-9 * max(1, ell2), "positive norm increment")
    return dict(G=G, K=K, Kinv=Kinv, L=np.tril(chol[0]), c=c, ell=ell, ell2=ell2, z=z,
                sigma=sigma, u=u, vt=vt, N_z=N_z, N_c=N_c,
                null_G=null_G, null_F=null_F, null_metric=null_metric,
                null_full24=null_full24, contributions=contributions,
                projections=projection, ell_svd=ell_svd, rel_resid=rel_resid,
                kkt=kkt, orth=orth, norm_increment=increment,
                predicted_increment=predicted_increment)


def high_precision_J0(Y: np.ndarray, F: np.ndarray, a: np.ndarray,
                      d: np.ndarray, condition_K: float,
                      whitened_norm_squared: float) -> tuple[float, float] | None:
    """Two-precision numerical fallback on the same exact binary64 inputs.

    It supplies a conservative retained-matrix policy check, not an all-input
    interval proof. An unavailable or unresolved check returns None.
    """
    try:
        import mpmath as mp
    except ImportError:
        return None

    def compute(dps: int):
        with mp.workdps(dps):
            G = mp.matrix([[mp.mpf(float(F[i, j])) / mp.mpf(float(d[j]))
                            for j in range(9)] for i in range(7)])
            Kinv = (G * G.T)**-1
            aa = mp.matrix([mp.mpf(float(x)) for x in a])
            yy = mp.matrix([[mp.mpf(float(Y[i, j])) for j in range(24)]
                            for i in range(7)])
            z = Kinv * aa
            center = (yy.T * z) / (aa.T * z)[0]
            residual = yy - aa * center.T
            weighted = Kinv * residual
            return sum(residual[i, j] * weighted[i, j]
                       for i in range(7) for j in range(24))

    try:
        j80 = compute(80)
        j120 = compute(120)
        with mp.workdps(120):
            if not mp.isfinite(j120) or j120 < 0:
                return None
            j_float = float(j120)
            if not math.isfinite(j_float) or (j120 > 0 and j_float == 0):
                return None
            # This is a retained-matrix numerical error policy: convergence
            # between 80/120 digits, a conditioned 80-digit solve allowance,
            # and conversion back to binary64 all scale as amplitude squared.
            delta = (abs(j120 - j80)
                     + 16 * mp.mpf(condition_K) * mp.power(10, -76)
                     * mp.mpf(whitened_norm_squared)
                     + 2 * np.finfo(float).eps * abs(j120))
            delta_float = float(delta)
            if not math.isfinite(delta_float):
                return None
            return j_float, delta_float
    except (ArithmeticError, ValueError, OverflowError):
        return None


def identified(Y: np.ndarray, F: np.ndarray, a: np.ndarray,
               d: np.ndarray, sol: dict, rho: float) -> dict:
    """Complete-24-space set with exact frozen-row cases and numeric uncertainty.

    The exact theorem is unchanged: rho**2=J0 gives {s0}. General floating
    near-equality receives a typed uncertainty, not a singleton certificate.
    """
    if not math.isfinite(rho) or rho < 0:
        raise ValueError("rho must be finite and nonnegative")
    if rho > math.sqrt(sys.float_info.max):
        raise ValueError("rho squared must be finite")
    if Y.shape != (7, 24) or not np.all(np.isfinite(Y)):
        raise ValueError("Y must be finite 7x24 data")
    if not np.array_equal(a, np.ones(7)):
        raise ValueError("frozen CMB response must be exactly seven ones")

    # Binary64 entries are the exact supplied reals for this finite task. With
    # a=ones, row equality is an exact structural test, independent of K or rho.
    if np.all(Y == Y[0:1, :]):
        s0 = Y[0].copy()
        status = ("SINGLETON_EXACT_ZERO" if not np.any(Y)
                  else "SINGLETON_EXACT_STRUCTURAL") if rho == 0 else "BALL"
        return {"center": s0, "J0": 0.0,
                "radius": 0.0 if rho == 0 else rho / sol["ell"],
                "status": status, "radius_uncertainty": None,
                "residual_7x24": np.zeros_like(Y)}

    s0 = (Y.T @ sol["z"]) / sol["ell2"]
    R = Y - a[:, None] * s0[None, :]
    L = sol["L"]
    Z = solve_triangular(L, Y, lower=True, check_finite=True)
    b = solve_triangular(L, a, lower=True, check_finite=True)
    q = b / np.linalg.norm(b)
    Ehat = Z - np.outer(q, q @ Z)
    e_norm = float(np.linalg.norm(Ehat))
    z_norm = float(np.linalg.norm(Z))
    Jhat = e_norm * e_norm
    if rho == 0:
        # Unequal exact supplied rows cannot be represented by a pure target.
        return {"center": s0, "J0": Jhat, "radius": None, "status": "EMPTY",
                "radius_uncertainty": None, "residual_7x24": R}
    if z_norm == 0 or not all(math.isfinite(x) for x in (e_norm, z_norm, Jhat)):
        return {"center": s0, "J0": Jhat, "radius": None,
                "status": "NUMERIC_BOUNDARY_HOLD",
                "radius_uncertainty": {"reason": "whitened data norm unavailable"},
                "residual_7x24": R}

    rho2 = rho * rho
    eps = np.finfo(float).eps
    gamma7 = 7 * eps / (1 - 7 * eps)
    gamma24 = 24 * eps / (1 - 24 * eps)
    K = sol["K"]
    k_norm = float(np.linalg.norm(K))
    l_norm = float(np.linalg.norm(L))
    condition_K = float(np.linalg.cond(K))
    factor_relative = float(np.linalg.norm(K - L @ L.T) / k_norm)
    solve_relative = max(
        float(np.linalg.norm(L @ Z - Y) / (l_norm * z_norm)),
        float(np.linalg.norm(L @ b - a) / (l_norm * np.linalg.norm(b))))
    # Backward-error policy: factorization, both triangular solves and the
    # normalized rank-one projection. Conditioning enters through K and L.
    # The safety factors are conservative for the retained matrices; this is
    # not advertised as a rigorous all-input interval certificate.
    relative_delta = ((factor_relative + gamma7) * condition_K
                      + 2 * (solve_relative + gamma7) * math.sqrt(condition_K)
                      + 8 * gamma24)
    delta_E = relative_delta * z_norm
    squared_error = 2 * e_norm * delta_E + delta_E**2
    budget_roundoff = 2 * eps * rho2
    tolerance = 1e-9 * max(rho2, Jhat, z_norm * z_norm)
    uncertainty = {"reason": "whitened residual numerical error policy",
                   "residual_norm_error_scale": delta_E,
                   "squared_residual_error_scale": squared_error,
                   "squared_budget_roundoff": budget_roundoff,
                   "squared_budget_tolerance": tolerance,
                   "condition_K": condition_K,
                   "factor_relative_residual": factor_relative,
                   "solve_relative_residual": solve_relative}
    coverage = (all(math.isfinite(x) for x in (rho2, Jhat, z_norm,
                                             condition_K, factor_relative,
                                             solve_relative, delta_E,
                                             squared_error, tolerance))
                and squared_error + budget_roundoff <= tolerance)
    if coverage:
        lower_J0 = max(0.0, e_norm - delta_E)**2
        upper_J0 = (e_norm + delta_E)**2
        uncertainty["J0_interval_from_error_policy"] = [lower_J0, upper_J0]
        if rho2 + budget_roundoff < lower_J0 - tolerance:
            status, radius, uncertainty = "EMPTY", None, None
        elif rho2 - budget_roundoff > upper_J0 + tolerance:
            status, radius, uncertainty = "BALL", math.sqrt(rho2 - Jhat) / sol["ell"], None
        else:
            status, radius = "BOUNDARY_UNCERTAIN", None
            uncertainty["reason"] = "budget and residual intervals overlap"
    else:
        status, radius = "NUMERIC_BOUNDARY_HOLD", None
        uncertainty["reason"] = "binary64 error coverage unavailable"

    if status in ("NUMERIC_BOUNDARY_HOLD", "BOUNDARY_UNCERTAIN"):
        fallback = high_precision_J0(Y, F, a, d, condition_K, z_norm * z_norm)
        if fallback is not None:
            j_high, error_high = fallback
            high_tolerance = 1e-9 * max(rho2, j_high)
            uncertainty["high_precision_J0"] = j_high
            uncertainty["high_precision_error_scale"] = error_high
            uncertainty["high_precision_squared_budget_tolerance"] = high_tolerance
            if error_high + budget_roundoff <= high_tolerance:
                Jhat = j_high
                if rho2 + budget_roundoff < j_high - error_high - high_tolerance:
                    status, radius, uncertainty = "EMPTY", None, None
                elif rho2 - budget_roundoff > j_high + error_high + high_tolerance:
                    status = "BALL"
                    radius = math.sqrt(rho2 - j_high) / sol["ell"]
                    uncertainty = None
                else:
                    status, radius = "BOUNDARY_UNCERTAIN", None
                    uncertainty["reason"] = "high precision budget interval overlaps zero"
    return {"center": s0, "J0": Jhat, "radius": radius, "status": status,
            "radius_uncertainty": uncertainty, "residual_7x24": R}


def u_min(Y: np.ndarray, s: np.ndarray, F: np.ndarray, a: np.ndarray,
          d: np.ndarray, Kinv: np.ndarray) -> np.ndarray:
    return ((F.T @ (Kinv @ (Y - np.outer(a, s)))) / d[:, None]**2)


def full24_controls(F: np.ndarray, a: np.ndarray, d: np.ndarray,
                    sol: dict) -> tuple[dict, dict[str, np.ndarray]]:
    """Explicit Kronecker actions, witnesses, generic identified set, invariances."""
    eye24 = np.eye(24)
    A = np.kron(a[:, None], eye24)
    B = np.kron(F, eye24)
    C = np.kron(sol["c"][:, None], eye24)
    basis_resid = A - B @ C
    basis_errors = np.linalg.norm(basis_resid, axis=0) / np.linalg.norm(A, axis=0)
    require(np.max(basis_errors) <= 1e-9, "all24 basis actions")
    mixed = np.array([(-1)**i * (i + 1) / 24 for i in range(24)], float)
    mixed /= np.linalg.norm(mixed)
    mixed_resid = np.linalg.norm(A @ mixed - B @ (C @ mixed)) / np.linalg.norm(A @ mixed)
    require(mixed_resid <= 1e-9, "mixed signed action")
    rho = sol["ell"]  # the chosen synthetic tensor norm is A=1
    one_U = -np.outer(sol["c"], mixed)
    pair_s1, pair_s2 = mixed, -mixed
    pair_U1, pair_U2 = -np.outer(sol["c"], mixed), np.outer(sol["c"], mixed)
    one_budget = float(np.linalg.norm(d[:, None] * one_U))
    pair_budget = float(np.linalg.norm(d[:, None] * pair_U1))
    require(abs(one_budget - rho) <= 1e-10 * rho, "one boundary budget")
    require(np.linalg.norm(np.outer(a, mixed) + F @ one_U) <= 1e-9 * np.linalg.norm(a), "one boundary data")
    require(abs(pair_budget - rho) <= 1e-10 * rho, "pair boundary budget")
    require(np.linalg.norm(np.outer(a, pair_s1) + F @ pair_U1) <= 1e-9 * np.linalg.norm(a), "pair first data")
    require(np.linalg.norm(np.outer(a, pair_s2) + F @ pair_U2) <= 1e-9 * np.linalg.norm(a), "pair second data")
    require(sol["ell"] * 1.01 > rho, "one 1pct rejection")
    require(sol["ell"] * 2.02 > 2*rho, "pair 1pct rejection")

    # A nonzero generic synthetic data table: foreground response with component
    # in the K^-1-orthogonal complement of the CMB column.
    Y = np.zeros((7, 24))
    Y[:, 0] = F[:, 0] + .2 * F[:, 3]
    Y[:, 1] = -.4 * F[:, 2]
    Y[:, 13] = .3 * a + .1 * F[:, 8]
    center = identified(Y, F, a, d, sol, 0)
    J0 = center["J0"]
    require(J0 > 1e-8, "synthetic nonzero irreducible budget")
    low = identified(Y, F, a, d, sol, .5 * math.sqrt(J0))
    edge = identified(Y, F, a, d, sol, math.sqrt(J0))
    outer_rho = math.sqrt(J0 + sol["ell2"] * .5**2)
    outer = identified(Y, F, a, d, sol, outer_rho)
    require(low["status"] == "EMPTY", "empty set")
    require(edge["status"] == "BOUNDARY_UNCERTAIN" and edge["radius"] is None,
            "constructed equality needs numeric boundary label")
    require(outer["status"] == "BALL", "nonzero ball")
    require(abs(outer["radius"] - .5) <= 1e-9, "radius .5")
    s_boundary = outer["center"] + .5 * mixed
    U_boundary = u_min(Y, s_boundary, F, a, d, sol["Kinv"])
    boundary_budget = float(np.linalg.norm(d[:, None] * U_boundary))
    reconstruction = np.linalg.norm(Y - np.outer(a, s_boundary) - F @ U_boundary)
    require(abs(boundary_budget - outer_rho) <= 1e-9 * outer_rho, "generic boundary")
    require(reconstruction <= 1e-9 * max(1, np.linalg.norm(Y)), "generic reconstruction")
    zero = identified(np.zeros((7, 24)), F, a, d, sol, 0)
    require(zero["status"] == "SINGLETON_EXACT_ZERO" and np.linalg.norm(zero["center"]) == 0, "rho zero")

    scale = np.array([.7, -1.3, 1.8, .55, -.8, 1.1, 1.5, -.65, 2.0])
    Fnew = F * scale
    dnew = np.abs(d * scale)
    transformed = solve_metric(Fnew, a, dnew)
    scale_K_error = np.linalg.norm(transformed["K"] - sol["K"]) / np.linalg.norm(sol["K"])
    require(scale_K_error <= 1e-12, "metric transported under column scaling")
    scaled_set = identified(Y, Fnew, a, dnew, transformed, outer_rho)
    require(np.linalg.norm(scaled_set["center"] - outer["center"]) <= 1e-11, "scaled center")
    require(abs(scaled_set["J0"] - J0) <= 1e-10 * J0, "scaled J0")
    require(abs(scaled_set["radius"] - outer["radius"]) <= 1e-10, "scaled radius")

    rng = np.random.default_rng(20261025)
    Q, _ = np.linalg.qr(rng.normal(size=(24,24)))
    rotated = identified(Y @ Q, F, a, d, sol, outer_rho)
    require(np.linalg.norm(rotated["center"] - outer["center"] @ Q) <= 1e-10, "24D rotated center")
    require(abs(rotated["J0"] - J0) <= 1e-10 * J0, "24D rotated J0")
    require(abs(rotated["radius"] - outer["radius"]) <= 1e-10, "24D rotated radius")
    controls = {"basis_relative_residuals_24": basis_errors.tolist(),
                "max_basis_relative_residual": float(np.max(basis_errors)),
                "mixed_signed_relative_residual": float(mixed_resid),
                "one_boundary_budget": one_budget,
                "pair_each_boundary_budget": pair_budget,
                "one_one_percent_larger_rejected": True,
                "pair_one_percent_larger_rejected": True,
                "generic_J0": J0, "generic_empty_status": low["status"],
                "generic_constructed_equality_theorem": "SINGLETON_IF_RHO_SQUARED_EQUALS_J0",
                "generic_equality_numeric_status": edge["status"],
                "generic_equality_radius_uncertainty": edge["radius_uncertainty"],
                "generic_ball_status": outer["status"],
                "generic_center": outer["center"].tolist(),
                "generic_radius": outer["radius"],
                "generic_rho": outer_rho,
                "generic_boundary_budget": boundary_budget,
                "generic_reconstruction_residual": float(reconstruction),
                "column_scale_K_relative_error": float(scale_K_error),
                "rotation_J0_relative_error": float(abs(rotated["J0"]-J0)/J0),
                "zero_budget_singleton": True,
                "operator_dimensions": {"A": list(A.shape), "B": list(B.shape),
                                        "C": list(C.shape)}}
    arrays = dict(A=A, B=B, C=C, mixed_signed_v=mixed,
                  synthetic_Y=Y, synthetic_center=outer["center"],
                  synthetic_residual=outer["residual_7x24"],
                  synthetic_boundary_s=s_boundary,
                  synthetic_boundary_U=U_boundary,
                  one_U=one_U, pair_U1=pair_U1, pair_U2=pair_U2,
                  full24_center_linear_operator=np.kron(sol["z"][None,:]/sol["ell2"], eye24),
                  full24_shape_matrix=sol["ell2"] * eye24)
    return controls, arrays


def compact(sol: dict) -> dict:
    return {"minimum_budget_ell": sol["ell"],
            "minimum_budget_ell_squared": sol["ell2"],
            "minimum_coefficients_c9": sol["c"].tolist(),
            "Fc_equals_a_relative_residual": float(sol["rel_resid"]),
            "KKT_relative_residual": float(sol["kkt"]),
            "nullspace_M_orthogonality_relative": float(sol["orth"]),
            "whitened_null_G_relative": float(sol["null_G"]),
            "coefficient_null_F_relative": float(sol["null_F"]),
            "coefficient_null_M_normalization_error": float(sol["null_metric"]),
            "coefficient_null_full24_relative": float(sol["null_full24"]),
            "positive_quadratic_norm_increment": float(sol["norm_increment"]),
            "singular_values_7": sol["sigma"].tolist(),
            "CMB_left_projections_7": sol["projections"].tolist(),
            "budget_squared_contributions_7": sol["contributions"].tolist(),
            "whitened_right_singular_directions_7x9": sol["vt"][:7,:].tolist(),
            "coefficient_nullspace_directions_2x9": sol["N_c"].T.tolist(),
            "whitened_nullspace_directions_2x9": sol["N_z"].T.tolist(),
            "row_Gram_K_7x7": sol["K"].tolist(),
            "row_Gram_inverse_7x7": sol["Kinv"].tolist(),
            "minimum_budget_from_SVD": sol["ell_svd"],
            "one_compensator_radius_per_unit_rho": 1/sol["ell"],
            "pairwise_max_separation_per_unit_rho": 2/sol["ell"]}


def make_figures(rows: dict) -> None:
    rho = np.linspace(0, 4, 201)
    for metric, filename in (("common_reference", "common_frontier.pdf"),
                             ("raw_identity", "raw_metric_sensitivity.pdf")):
        fig, axes = plt.subplots(1, 2, figsize=(9.4,4.2), sharey=True)
        for name in BRANCHES:
            ell = rows[name][metric]["minimum_budget_ell"]
            ax = axes[0 if name.startswith("A") else 1]
            bt = name.split("_BT_")[1]
            color = {"1e-07":"C0", "1e-08":"C1", "1e-06":"C2"}[bt]
            ax.plot(rho, rho/ell, color=color, linestyle="-", lw=1.6,
                    label=f"BT={bt}, single")
            ax.plot(rho, 2*rho/ell, color=color, linestyle="--", lw=1.2,
                    label=f"BT={bt}, pair")
        for ax, convention in zip(axes, ("A", "B")):
            ax.set(xlabel=r"Joint budget $\rho$ (target amplitude units)",
                   title=f"LFI convention {convention}")
            ax.legend(fontsize=6.5, ncol=1, loc="upper left")
            ax.grid(alpha=.2)
        axes[0].set_ylabel(r"Compatible target norm $\|v\|$ (same units)")
        fig.tight_layout()
        fig.savefig(HERE/"report/figures"/filename)
        plt.close(fig)


def make_table(rows: dict) -> None:
    lines = [r"\begin{tabular}{lrrrr}", r"\hline\hline",
             r"Branch & $\ell_{M}$ & $1/\ell_M$ & $\ell_I$ & $1/\ell_I$ \\",
             r"\hline"]
    for name in BRANCHES:
        x, y = rows[name]["common_reference"], rows[name]["raw_identity"]
        lines.append(f"{name.replace('_', r'\_')} & {x['minimum_budget_ell']:.6f} & {1/x['minimum_budget_ell']:.6f} & {y['minimum_budget_ell']:.6f} & {1/y['minimum_budget_ell']:.6f} \\\\")
    lines += [r"\hline\hline", r"\end{tabular}"]
    (HERE/"report/generated/budgets.tex").write_text("\n".join(lines)+"\n")
    checks = [r"\begin{tabular}{lrrrr}", r"\hline\hline",
              r"Branch & $\sigma_{\min}(FM^{-1/2})$ & $\|Fc_M-a\|/\|a\|$ & $\|Fc_I-a\|/\|a\|$ & $\max_j\epsilon_j$ \\",
              r"\hline"]
    for name in BRANCHES:
        x, y = rows[name]["common_reference"], rows[name]["raw_identity"]
        v = rows[name]["full24_controls"]["max_basis_relative_residual"]
        checks.append(f"{name.replace('_', r'\_')} & {x['singular_values_7'][-1]:.7f} & {x['Fc_equals_a_relative_residual']:.2e} & {y['Fc_equals_a_relative_residual']:.2e} & {v:.2e} \\\\")
    checks += [r"\hline\hline", r"\end{tabular}"]
    (HERE/"report/generated/residuals.tex").write_text("\n".join(checks)+"\n")


def main() -> None:
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    require(digest == SOURCE_SHA, "frozen R31 input hash mismatch")
    source = json.loads(SOURCE.read_text())
    require(tuple(source["branches"].keys()) == BRANCHES, "branch order mismatch")
    out = {"task_id":"R32-04-BANDPASS-BOUNDS", "source":str(SOURCE),
           "source_sha256":digest, "dispatch_base_head":"7f313d6c4f2794c484791ed108a7ce231eb824b0",
           "frequencies":FREQUENCIES, "moment_order":MOMENTS,
           "full24_coordinate_order":coord_names(),
           "common_reference_column_scales":D.tolist(),
           "metric_definition":"M=diag(common_reference_column_scales^2); raw sensitivity M=I",
           "tensor_budget_definition":"tr(U.T M U)<=rho^2, U has shape9x24",
           "branches":{}, "checks_status":"PASS",
           "claim_scope":"conditional finite seven-row, nine-free-signed-moment bounded class",
           "diagnostic_bundle":source["diagnostic_bundle"],
           "physical_realizability":"NOT_EVALUATED",
           "real_sky_noise":"NOT_CONSUMED",
           "original42_acceptance":False,
           "independent_scientific_review":"PENDING"}
    for i, name in enumerate(BRANCHES):
        b = source["branches"][name]
        F = np.asarray(b["F2"]["matrix_7xk"], float)
        a = np.asarray(b["cmb_unity_responses"], float)
        require(F.shape == (7,9) and a.shape == (7,), "seven-by-nine or unity shape")
        require(np.array_equal(a, np.ones(7)), "CMB response must be seven ones")
        if name == BRANCHES[0]:
            require(np.allclose(np.asarray(b["F2"]["column_scales"], float), D,
                                rtol=1e-14, atol=0), "frozen common metric reference")
        require(b["F2"]["resolved_rank"] == 7 and b["F2"]["augmented_resolved_rank"] == 7,
                "old finite rank facts")
        require(b["F2"]["full24_identified_target_rank"] == 0, "old target quotient")
        primary = solve_metric(F,a,D)
        raw = solve_metric(F,a,np.ones(9))
        require(abs(raw["ell"]-RAW_REFERENCE[i]) <= 1e-8*RAW_REFERENCE[i],
                "stored raw witness norm")
        controls, arrays = full24_controls(F,a,D,primary)
        np.savez_compressed(HERE/"report/generated"/(name+"_full24.npz"),
                            F=F, a=a, c_primary=primary["c"],
                            Kinv_primary=primary["Kinv"], **arrays)
        out["branches"][name] = {
            "lfi_convention":b["lfi_convention"],
            "hfi_threshold":b["hfi_threshold"],
            "finite_rank_F2":7, "free_target_quotient_rank":0,
            "common_reference":compact(primary),
            "raw_identity":compact(raw),
            "raw_stored_witness_norm":RAW_REFERENCE[i],
            "full24_controls":controls,
            "full24_binary":str(HERE/"report/generated"/(name+"_full24.npz"))}
    make_figures(out["branches"])
    make_table(out["branches"])
    (HERE/"RESULT.json").write_text(json.dumps(out, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status":"PASS", "source_sha256":digest,
                      "branches":{k:{"ell_common":v["common_reference"]["minimum_budget_ell"],
                                     "ell_raw":v["raw_identity"]["minimum_budget_ell"],
                                     "max_basis_residual":v["full24_controls"]["max_basis_relative_residual"]}
                                  for k,v in out["branches"].items()}}, indent=2))


if __name__ == "__main__":
    main()
