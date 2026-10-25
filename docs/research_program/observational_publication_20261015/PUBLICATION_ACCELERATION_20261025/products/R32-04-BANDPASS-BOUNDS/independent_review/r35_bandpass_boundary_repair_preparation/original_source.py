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
from scipy.linalg import cho_factor, cho_solve, null_space

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]
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
    N = null_space(G)
    require(N.shape == (9, 2), "coefficient null dimension")
    orth = np.linalg.norm(N.T @ (d * c)) / max(1.0, np.linalg.norm(d * c))
    test_n = N @ np.array([.31, -.47]) / d
    increment = float(np.sum((d * (c + test_n)) ** 2) - ell2)
    predicted_increment = float(np.sum((d * test_n) ** 2))
    require(rel_resid <= 1e-10, f"Fc=a residual {rel_resid}")
    require(kkt <= 1e-10, f"KKT residual {kkt}")
    require(abs(ell - ell_svd) <= 1e-10 * ell, "SVD/Cholesky budget")
    require(orth <= 1e-10, "null orthogonality")
    require(abs(increment - predicted_increment) <= 1e-9 * max(1, ell2), "positive norm increment")
    return dict(G=G, K=K, Kinv=Kinv, c=c, ell=ell, ell2=ell2, z=z,
                sigma=sigma, u=u, vt=vt, N=N, contributions=contributions,
                projections=projection, ell_svd=ell_svd, rel_resid=rel_resid,
                kkt=kkt, orth=orth, norm_increment=increment,
                predicted_increment=predicted_increment)


def identified(Y: np.ndarray, F: np.ndarray, a: np.ndarray,
               d: np.ndarray, sol: dict, rho: float) -> dict:
    """Stable center and residual-budget calculation in the complete 24-space."""
    Kinv = sol["Kinv"]
    s0 = (Y.T @ sol["z"]) / sol["ell2"]
    R = Y - a[:, None] * s0[None, :]
    J0 = float(np.sum(R * (Kinv @ R)))
    require(J0 >= -1e-10 * max(1, np.linalg.norm(Y) ** 2), "negative J0")
    require(J0 >= 0, "negative numerical J0")
    gap = rho**2 - J0
    tol = 1e-9 * max(1.0, rho**2, J0)
    if gap < -tol:
        radius = None
        status = "EMPTY"
    elif abs(gap) <= tol:
        radius = 0.0
        status = "SINGLETON_NUMERIC_BOUNDARY"
    else:
        radius = math.sqrt(gap) / sol["ell"]
        status = "BALL"
    return {"center": s0, "J0": J0, "radius": radius, "status": status,
            "residual_7x24": R}


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
    require(edge["status"] == "SINGLETON_NUMERIC_BOUNDARY", "singleton set")
    require(outer["status"] == "BALL", "nonzero ball")
    require(abs(outer["radius"] - .5) <= 1e-9, "radius .5")
    s_boundary = outer["center"] + .5 * mixed
    U_boundary = u_min(Y, s_boundary, F, a, d, sol["Kinv"])
    boundary_budget = float(np.linalg.norm(d[:, None] * U_boundary))
    reconstruction = np.linalg.norm(Y - np.outer(a, s_boundary) - F @ U_boundary)
    require(abs(boundary_budget - outer_rho) <= 1e-9 * outer_rho, "generic boundary")
    require(reconstruction <= 1e-9 * max(1, np.linalg.norm(Y)), "generic reconstruction")
    zero = identified(np.zeros((7, 24)), F, a, d, sol, 0)
    require(zero["status"] == "SINGLETON_NUMERIC_BOUNDARY" and np.linalg.norm(zero["center"]) == 0, "rho zero")

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
                "generic_singleton_status": edge["status"],
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
            "positive_quadratic_norm_increment": float(sol["norm_increment"]),
            "singular_values_7": sol["sigma"].tolist(),
            "CMB_left_projections_7": sol["projections"].tolist(),
            "budget_squared_contributions_7": sol["contributions"].tolist(),
            "whitened_right_singular_directions_7x9": sol["vt"][:7,:].tolist(),
            "coefficient_nullspace_directions_2x9": sol["N"].T.tolist(),
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
