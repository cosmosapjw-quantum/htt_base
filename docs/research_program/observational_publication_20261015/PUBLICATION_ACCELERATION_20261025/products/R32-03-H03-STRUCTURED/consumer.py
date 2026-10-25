#!/usr/bin/env python3
"""Finite H03 structured-response analysis from hash-bound retained statistics."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import brentq
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]
SOURCE = P / "evidence/sources/H03_SOURCE_TOMOGRAPHY.json"
PHYSICAL = P / "evidence/output/physical_results.json"
SOURCE_SHA = "5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326"
PHYSICAL_SHA = "25342649e30a8d631a5364002ae39ebffae0a5d92e1e4ad25c9e2f8dfe9362cc"
T0_REF = 23.396720522667167
TAU_REF = 12.591587243743977
ETA_REF = 1.2885530036501112
RTOL = 1e-10


def check_sha(path: Path, expected: str) -> None:
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != expected:
        raise ValueError(f"immutable input mismatch: {path}: {got}")


def arr(x):
    return np.asarray(x, dtype=float)


def svd_data(B, r):
    U, s, Vt = np.linalg.svd(B, full_matrices=False)
    if not len(s) or s[0] == 0:
        rank = 0
    else:
        ratios = s / s[0]
        if np.any((ratios > 1e-12) & (ratios < 1e-10)):
            raise ValueError("NUMERIC_RANK_HOLD")
        rank = int(np.sum(ratios >= 1e-10))
    U, ss, Vt = U[:, :rank], s[:rank], Vt[:rank]
    alpha = U.T @ r
    perp = r - U @ alpha
    floor = float(perp @ perp)
    sat = float(np.linalg.norm(alpha / ss)) if rank else 0.0
    return U, s, ss, Vt, alpha, perp, floor, sat, rank


def at_lambda(lam, ss, alpha, floor):
    den = ss * ss + lam
    xi_components = ss * alpha / den
    rho = float(np.linalg.norm(xi_components))
    T = float(floor + np.sum((lam * alpha / den) ** 2))
    return rho, T, xi_components


def bracket_root(fun):
    hi = 1.0
    while fun(hi) <= 0:
        hi *= 2
        if not np.isfinite(hi):
            raise ArithmeticError("root bracket failed")
    return hi


def curve_at_rho(rho, ss, alpha, floor, sat, T0):
    if rho == 0:
        return T0, np.zeros_like(alpha)
    if rho >= sat:
        return floor, alpha / ss
    fun = lambda lam: at_lambda(lam, ss, alpha, floor)[0] - rho
    hi = 1.0
    while fun(hi) > 0:
        hi *= 2
    lam = brentq(fun, 0, hi, xtol=1e-13, rtol=9e-16)
    _, T, x = at_lambda(lam, ss, alpha, floor)
    return T, x


def threshold(ss, alpha, floor, sat, T0, tau):
    eps = 1e-9
    if T0 <= tau - eps:
        return "ALREADY_ADEQUATE", 0.0, 0.0, np.zeros_like(alpha), None
    if abs(T0 - tau) <= eps or abs(floor - tau) <= eps:
        if abs(T0 - tau) <= eps:
            return "NUMERIC_BOUNDARY_BASELINE", None, None, None, None
        return "FINITE_FLOOR_EQUALITY", sat, 0.0, alpha / ss, 0.0
    if floor > tau:
        return "THRESHOLD_UNATTAINABLE_FOR_THIS_D", None, None, None, None
    fun = lambda lam: at_lambda(lam, ss, alpha, floor)[1] - tau
    hi = bracket_root(fun)
    lam = brentq(fun, 0, hi, xtol=1e-13, rtol=9e-16)
    rho, T, x = at_lambda(lam, ss, alpha, floor)
    assert abs(T - tau) <= 1e-8
    return "FINITE_CROSSING", rho, lam, x, T


def analyse(name, D, y, C, L, X, A, Q, Pproj, r, T0, tau):
    B = Pproj @ solve_triangular(L, D, lower=True)
    U, all_s, ss, Vt, alpha, perp, floor, sat, rank = svd_data(B, r)
    status, rho95, lam95, xc, _ = threshold(ss, alpha, floor, sat, T0, tau)
    qmin = float(np.sqrt(T0 - floor) - np.sqrt(tau - floor)) if floor < tau < T0 else (0.0 if T0 <= tau else None)
    rec = {
        "design": name, "D_12xp_km_s_Mpc_per_unit_eta": D.tolist(),
        "B_12xp_whitened": B.tolist(), "rank_B": rank,
        "singular_values_all": all_s.tolist(), "resolved_singular_values": ss.tolist(),
        "U_resolved_12xr": U.tolist(), "Vt_resolved_rxp": Vt.tolist(),
        "alpha_signed": alpha.tolist(), "r_perp_signed_whitened_12": perp.tolist(),
        "T_floor": floor, "rho_sat": sat, "rho95": rho95,
        "q_min_restricted": qmin, "status": status,
        "lambda95": lam95, "T0": T0,
        "dimensionless_rho_bound_check": ETA_REF / float(all_s[0]) if len(all_s) and all_s[0] > 0 else None,
    }
    if rank:
        assert np.linalg.norm(B.T @ perp) <= 1e-10 * max(1., np.linalg.norm(B) * np.linalg.norm(perp))
    if xc is not None:
        eta = Vt.T @ xc
        correction = D @ eta
        corrected = y - correction
        coef = np.linalg.lstsq(A, solve_triangular(L, corrected, lower=True), rcond=None)[0]
        fitted = X @ coef
        residual = corrected - fitted
        white_residual = solve_triangular(L, residual, lower=True)
        q = float(np.linalg.norm(B @ eta))
        T_direct = float(white_residual @ white_residual)
        target = tau if status in ("FINITE_CROSSING", "FINITE_FLOOR_EQUALITY") else T0
        assert abs(T_direct - target) <= 1e-8 * max(1., target)
        assert abs(float(np.linalg.norm(eta)) - rho95) <= 1e-8 * max(1., rho95)
        if status in ("FINITE_CROSSING", "FINITE_FLOOR_EQUALITY"):
            assert q + 1e-9 >= ETA_REF
            assert rho95 + 1e-9 >= rec["dimensionless_rho_bound_check"]
        rec["crossing_witness"] = {
            "eta_dimensionless": eta.tolist(), "D_eta_signed_12_km_s_Mpc": correction.tolist(),
            "projected_correction_signed_whitened_12": (B @ eta).tolist(),
            "q95_projected_whitened": q,
            "bulk_b_km_s": coef[:3].tolist(), "rate_d_km_s_Mpc": coef[3:].tolist(),
            "signal_fit_signed_12_km_s_Mpc": fitted.tolist(),
            "signed_residual_12_km_s_Mpc": residual.tolist(),
            "signed_whitened_residual_12": white_residual.tolist(),
            "T_direct_refit": T_direct,
            "KKT_residual_norm": float(np.linalg.norm((B.T @ B + lam95 * np.eye(D.shape[1])) @ eta - B.T @ r)),
        }
    xs = np.linspace(0, sat * 1.15 if sat else 1., 121)
    Ts = np.array([curve_at_rho(float(x), ss, alpha, floor, sat, T0)[0] if rank else T0 for x in xs])
    assert abs(Ts[0] - T0) <= 1e-9 and np.all(np.diff(Ts) <= 1e-8)
    assert abs(Ts[-1] - floor) <= 1e-8
    rec["curve"] = {"rho": xs.tolist(), "T_min": Ts.tolist()}
    return rec


def controls(y, C, L, X, A, Pproj, r, T0, tau, designs):
    checks = {}
    block = C.copy()
    for i in range(4):
        for j in range(4):
            if i != j:
                block[3*i:3*i+3, 3*j:3*j+3] = 0
    Lb = np.linalg.cholesky(block)
    Ab = solve_triangular(Lb, X, lower=True)
    rb = solve_triangular(Lb, y, lower=True) - Ab @ np.linalg.lstsq(Ab, solve_triangular(Lb, y, lower=True), rcond=None)[0]
    checks["wrong_block_diagonal_T"] = float(rb @ rb)
    assert abs(checks["wrong_block_diagonal_T"] - 8.925712182985682) < 1e-9
    checks["D_equals_X_projected_norm"] = float(np.linalg.norm(Pproj @ A))
    assert checks["D_equals_X_projected_norm"] < 1e-10
    assert threshold(np.array([]),np.array([]),T0,0.,T0,tau)[0] == "THRESHOLD_UNATTAINABLE_FOR_THIS_D"
    checks["D_equals_X_has_no_gain"] = True
    B = Pproj @ solve_triangular(L, designs["depth_slope"], lower=True)
    U, _, ss, Vt, alpha, perp, floor, sat, rank = svd_data(B, r)
    synthetic = U @ alpha + perp
    assert abs(np.linalg.norm(synthetic - B @ (Vt.T @ (alpha / ss))) ** 2 - floor) < 1e-8
    checks["synthetic_nonspanning_floor"] = floor
    # Support witness and the pseudoinverse image test for a thin resolved B.
    unit = U[:,0]
    radius = 0.7
    support = radius * np.linalg.norm(B.T @ unit)
    support_eta = radius * B.T @ unit / np.linalg.norm(B.T @ unit)
    assert abs(float(unit @ B @ support_eta)-support) < 1e-10
    q_in = B @ support_eta
    assert np.linalg.norm(B @ np.linalg.pinv(B) @ q_in-q_in) < 1e-10
    assert np.linalg.norm(np.linalg.pinv(B) @ q_in) <= radius+1e-10
    q_out = q_in + perp/np.linalg.norm(perp)
    assert np.linalg.norm(B @ np.linalg.pinv(B) @ q_out-q_out) > .9
    checks["ellipsoid_support_and_image_membership"] = True
    # Exact equality is a finite attained boundary even when the residual floor equals tau.
    arbitrary = U @ alpha + perp * np.sqrt(tau / floor)
    aa = U.T @ arbitrary
    pp = arbitrary - U @ aa
    assert abs(float(pp @ pp) - tau) < 1e-8
    eq_status, eq_rho, *_ = threshold(ss, aa, float(pp @ pp), float(np.linalg.norm(aa / ss)), float(arbitrary @ arbitrary), tau)
    assert eq_status == "FINITE_FLOOR_EQUALITY" and np.isfinite(eq_rho)
    checks["exact_floor_equals_tau_budget"] = eq_rho
    Bfull = Pproj @ solve_triangular(L, L, lower=True)
    assert np.linalg.norm(Bfull - Pproj) < 1e-10
    Uf, _, sf, Vtf, af, pf, ff, satf, rf = svd_data(Bfull, r)
    assert rf == 6 and ff < 1e-20
    for q in (0., ETA_REF, float(np.sqrt(T0))):
        T, _ = curve_at_rho(q, sf, af, ff, satf, T0)
        assert abs(T - max(0., np.sqrt(T0) - q) ** 2) < 1e-8
    checks["unrestricted_radial_recovery"] = True
    rot = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.]])
    rot12 = np.kron(np.eye(4), rot)
    rot6 = np.kron(np.eye(2), rot)
    yy, CC, XX = rot12 @ y, rot12 @ C @ rot12.T, rot12 @ X @ rot6.T
    LL = np.linalg.cholesky(CC)
    AR = solve_triangular(LL, XX, lower=True)
    yr = solve_triangular(LL, yy, lower=True)
    rr = yr - AR @ np.linalg.lstsq(AR, yr, rcond=None)[0]
    checks["rotation_T_error"] = abs(float(rr @ rr) - T0)
    assert checks["rotation_T_error"] < 1e-8
    for name, D in designs.items():
        DR = rot12 @ D @ np.kron(np.eye(D.shape[1] // 3), rot).T
        QR, _ = np.linalg.qr(AR, mode="reduced")
        BR = (np.eye(12)-QR@QR.T) @ solve_triangular(LL, DR, lower=True)
        _, _, sr, _, ar, _, fr, satr, _ = svd_data(BR, rr)
        _, _, so, _, ao, _, fo, sato, _ = svd_data(Pproj @ solve_triangular(L,D,lower=True), r)
        orig = threshold(so,ao,fo,sato,T0,tau)
        rotated = threshold(sr,ar,fr,satr,T0,tau)
        assert abs(fr-fo) < 1e-8
        if orig[1] is not None:
            assert abs(orig[1]-rotated[1]) < 1e-8
    checks["rotation_all_design_budgets"] = True
    return checks


def plot(records, T0, tau):
    colors = {"depth_slope":"#095a9d", "FP_composition":"#bd521a", "joint":"#26733b"}
    for name, rec in records.items():
        plt.plot(rec["curve"]["rho"], rec["curve"]["T_min"], label=name.replace('_',' '), color=colors[name], lw=2)
        plt.plot([rec["curve"]["rho"][0], rec["curve"]["rho"][-1]], [rec["T_floor"]]*2, color=colors[name], ls=":", lw=1)
        if rec["rho95"] is not None:
            plt.scatter([rec["rho95"]],[tau],color=colors[name],s=24,zorder=4)
    plt.axhline(tau,color="black",ls="--",label=r"fixed $\chi^2_{6,.95}$")
    plt.ylabel(r"Profiled $T_{\min}(\rho)$")
    plt.xlabel(r"Joint coefficient budget $\rho$ (dimensionless)")
    plt.legend(fontsize=8);plt.grid(alpha=.2);plt.tight_layout()
    plt.savefig(HERE/"figures/scientific_budget.pdf");plt.close()
    q = np.linspace(0, max(np.sqrt(T0), 3),200)
    plt.plot(q,np.maximum(0,np.sqrt(T0)-q)**2,color="black",label="unrestricted")
    for name,rec in records.items():
        qq=rec["q_min_restricted"]
        if qq is not None: plt.scatter([qq],[tau],label=name.replace('_',' '),color=colors[name])
    plt.axhline(tau,color="gray",ls="--")
    plt.xlabel(r"Projected whitened effect budget $q$");plt.ylabel(r"Minimum discrepancy")
    plt.legend(fontsize=8);plt.grid(alpha=.2);plt.tight_layout()
    plt.savefig(HERE/"figures/frontier_comparison.pdf");plt.close()
    names=list(records);floors=[records[n]["T_floor"] for n in names]
    fig,ax=plt.subplots(figsize=(7,3.5));ax.bar(names,floors,color=[colors[n] for n in names]);ax.axhline(tau,color="black",ls="--")
    ax.set_ylabel(r"Irreducible $T_\perp$");ax.set_xticks(range(3),[n.replace('_',' ') for n in names]);ax.tick_params(axis="x",labelsize=8)
    fig.tight_layout();fig.savefig(HERE/"figures/irreducible_floor.pdf");plt.close(fig)


def main():
    check_sha(SOURCE,SOURCE_SHA);check_sha(PHYSICAL,PHYSICAL_SHA)
    j=json.loads(SOURCE.read_text());old=json.loads(PHYSICAL.read_text())
    wins=j["monopole_dipole_STF2_windows"]
    I=[9*w+k for w in range(4) for k in (1,2,3)]
    y=np.concatenate([arr(w["dipole_cartesian_km_s_Mpc"]) for w in wins])
    C36=arr(j["joint_covariance_36x36"])
    C=C36[np.ix_(I,I)]
    R=np.vstack([arr(w["bulk_velocity_design_response_9x3_per_Mpc"])[1:4,:] for w in wins])
    G=np.tile(np.eye(3),(4,1));X=np.column_stack((R,G))
    assert np.allclose(y,arr(old["data_dipoles"]),atol=1e-12,rtol=0)
    assert np.allclose(C,arr(old["data_covariance"]),atol=1e-12,rtol=0)
    assert np.allclose(R,arr(old["bulk_response"]),atol=1e-12,rtol=0)
    assert np.max(np.abs(C-C.T)) <= 1e-12*np.max(np.abs(C))
    L=np.linalg.cholesky(C);A=solve_triangular(L,X,lower=True)
    Q,_=np.linalg.qr(A,mode="reduced");Pproj=np.eye(12)-Q@Q.T
    assert np.linalg.matrix_rank(X)==6
    assert np.linalg.norm(Pproj@Pproj-Pproj)<1e-10 and np.linalg.norm(Pproj-Pproj.T)<1e-10
    assert np.linalg.norm(Pproj@A)<1e-10*max(1.,np.linalg.norm(A))
    r=Pproj@solve_triangular(L,y,lower=True);T0=float(r@r)
    tau=float(chi2.ppf(.95,6));eta0=float(np.sqrt(T0)-np.sqrt(tau))
    assert abs(T0-T0_REF)<1e-9 and abs(tau-TAU_REF)<1e-12 and abs(eta0-ETA_REF)<1e-9
    z=arr([w["z_center"] for w in wins]);h=float(j["width_z"])
    t=(z-.04)/h
    fp=arr([w["source_method_distance_weight_fractions"]["FP"] for w in wins]);f=fp-fp[0]
    assert np.allclose(z,[.025,.04,.06,.08],atol=1e-15)
    assert abs(h-.012)<1e-15
    assert np.allclose(fp,[.30371471086623375,.53491723769988,.8024115244860296,.901889873332754],atol=1e-15)
    Dz=np.kron(t[:,None],np.eye(3));Df=np.kron(f[:,None],np.eye(3))
    designs={"depth_slope":Dz,"FP_composition":Df,"joint":np.column_stack((Dz,Df))}
    records={name:analyse(name,D,y,C,L,X,A,Q,Pproj,r,T0,tau) for name,D in designs.items()}
    checks=controls(y,C,L,X,A,Pproj,r,T0,tau,designs)
    plot(records,T0,tau)
    carrier={"source_path":str(SOURCE.relative_to(P)),"source_sha256":SOURCE_SHA,
        "physical_results_path":str(PHYSICAL.relative_to(P)),"physical_results_sha256":PHYSICAL_SHA,
        "window_theta9_all_physical_coefficients_km_s_Mpc":[w["theta9"] for w in wins],
        "source_joint_covariance_36x36":C36.tolist(),
        "physical_rate_tensors":old["rate_tensors"],"window_major_dipole_indices_0based":I,
        "y_signed_12_km_s_Mpc":y.tolist(),"C_dipole_12x12":C.tolist(),
        "R_12x3_inverse_Mpc":R.tolist(),"G_12x3":G.tolist(),"X_12x6":X.tolist(),
        "L_cholesky":L.tolist(),"Q_X_whitened":Q.tolist(),"P_projector":Pproj.tolist(),
        "r_signed_whitened_12":r.tolist(),"FP_distance_weight_fractions":fp.tolist(),
        "z_centers":z.tolist(),"width_z":h}
    (HERE/"generated/source_carrier.json").write_text(json.dumps(carrier,indent=2)+"\n")
    outcome={"schema":"H03-STRUCTURED-v1","task_id":"R32-03-H03-STRUCTURED",
        "source_sha256":SOURCE_SHA,"physical_sha256":PHYSICAL_SHA,
        "T0":T0,"fixed_df":6,"tau95":tau,"working_tail":float(chi2.sf(T0,6)),
        "unrestricted_eta95":eta0,"designs":records,"controls":checks,
        "interpretation":"Conditional finite-window sensitivity designs under retained working covariance; not a physical calibration Jacobian or measured error amplitude.",
        "original42_acceptance":False,"physical_x_F_Pi_Q_GF":"UNDEFINED"}
    (HERE/"generated/analysis.json").write_text(json.dumps(outcome,indent=2)+"\n")
    with (HERE/"generated/table.tex").open("w") as ftex:
        ftex.write("\\begin{table}[t]\\caption{Conditional finite-window designs. All discrepancies use the complete 12D covariance and the unchanged six-degree working threshold. $\\rho_{95}$ is a dimensionless joint coefficient budget; $q_{95}$ is its projected whitened image norm. The depth design has no finite threshold crossing.}\\label{tab:budgets}\\begin{ruledtabular}\\begin{tabular}{lrrrrr}\\text{Design}&$\\operatorname{rank}B$&$T_\\perp$&$\\rho_{95}$&$q_{95}$&$\\rho_{\\rm sat}$\\\\\n")
        for name,v in records.items():
            nice={"depth_slope":"Depth slope","FP_composition":"FP composition","joint":"Joint"}[name]
            rho="---" if v["rho95"] is None else f'{v["rho95"]:.4f}'
            q="---" if "crossing_witness" not in v else f'{v["crossing_witness"]["q95_projected_whitened"]:.4f}'
            ftex.write(f'{nice}&{v["rank_B"]}&{v["T_floor"]:.4f}&{rho}&{q}&{v["rho_sat"]:.4f}\\\\\n')
        ftex.write("\\end{tabular}\\end{ruledtabular}\\end{table}\n")
    with (HERE/"generated/matrix_min_budget.csv").open("w",newline="") as fcsv:
        w=csv.writer(fcsv);w.writerow(["design","rank","singular_values","T_floor","rho_sat","status","rho95","q_min","q95","eta95_over_operator_norm"])
        for name,v in records.items():
            w.writerow([name,v["rank_B"],";".join(map(str,v["singular_values_all"])),v["T_floor"],v["rho_sat"],v["status"],v["rho95"],v["q_min_restricted"],v.get("crossing_witness",{}).get("q95_projected_whitened"),v["dimensionless_rho_bound_check"]])
    for name,v in records.items():
        print(name,v["rank_B"],v["T_floor"],v["status"],v["rho95"],v.get("crossing_witness",{}).get("q95_projected_whitened"))
    print("T0",T0,"tau",tau,"eta95",eta0,"controls",checks)


if __name__=="__main__":
    main()
