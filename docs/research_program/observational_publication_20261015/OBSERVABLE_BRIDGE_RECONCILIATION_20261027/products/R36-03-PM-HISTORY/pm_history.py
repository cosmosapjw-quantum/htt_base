"""Conditional full-STF proper-motion response and retained-Gram consumer.

Run with the repository interpreter. No catalogue rows or physical depth law are read.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2, ncx2

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
MODEL = REPO / "docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/astrometry/model.py"
STATS = Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry/full_stats.npz")
CONTRACT = Path("/mnt/extdrive/workdir/htt_open_data/r36_pm_history_theory_actual/IMPLEMENTATION_CONTRACT.json")
CLARIFICATION = Path("/mnt/extdrive/workdir/htt_open_data/r36_pm_history_theory_actual/CLARIFICATION.json")
EXTERNAL = Path("/mnt/extdrive/workdir/htt_open_data/r36_pm_history_numeric_actual")
EXPECTED = {"contract": "e940efc6768f6607eeda4f0e2e94a2d73d32d3630e6764f0c7e8069e8c2b708a",
            "clarification": "8e383e93e635a12fe284065fb94d1318a0f8c6ba00ffeef181f9c85b087721aa",
            "stats": "4d9406de69546e72dff79d4fc611703e8eb450944c4dcc254f8484c98a22d5da",
            "model": "c132f01d9d35e267aa67e8465987bb8cfbab94f46e4f8adc32e9c793f5b74659"}
C_KMS = 299792.458
SEC_YEAR = 365.25 * 86400
RAD_TO_UASYR = 180 / math.pi * 3600 * 1e6 * SEC_YEAR
PACKET = "c8d9f6351c42fc6da769c1aaec2c14948806c99319324fec981e48217901637b"
INPUT = "sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def basis():
    s2, s6 = math.sqrt(2), math.sqrt(6)
    e = np.zeros((5, 3, 3))
    e[0] = np.diag([1, -1, 0]) / s2
    e[1] = np.diag([1, 1, -2]) / s6
    for k, (i, j) in enumerate(((0, 1), (0, 2), (1, 2)), 2):
        e[k, i, j] = e[k, j, i] = 1 / s2
    return e


E = basis()


def checked_stf(a):
    a = np.asarray(a, dtype=float)
    if a.shape != (3, 3) or not np.isfinite(a).all():
        raise ValueError("finite symmetric trace-free 3x3 tensor required")
    scale = np.max(np.abs(a))
    if scale:
        normalized = a / scale
        if np.max(np.abs(normalized-normalized.T)) > 1e-12 or abs(np.trace(normalized)) > 1e-12*np.linalg.norm(normalized):
            raise ValueError("finite symmetric trace-free 3x3 tensor required")
    return a


def coefficients(a):
    return np.einsum("kij,ij->k", E, checked_stf(a))


def tensor(coeff):
    coeff = np.asarray(coeff, float)
    if coeff.shape != (5,) or not np.isfinite(coeff).all():
        raise ValueError("finite full-five coefficients required")
    return np.einsum("k,kij->ij", coeff, E)


def tangent(a, ra, dec):
    """Signed (mu_alpha cos(delta), mu_delta) in tensor rate units."""
    a = checked_stf(a)
    ra, dec = np.broadcast_arrays(np.asarray(ra, float), np.asarray(dec, float))
    if not np.isfinite(ra).all() or not np.isfinite(dec).all() or np.any(np.abs(dec) >= 90):
        raise ValueError("finite non-polar equatorial coordinates required")
    alpha, delta = np.deg2rad(ra), np.deg2rad(dec)
    n = np.stack([np.cos(delta) * np.cos(alpha), np.cos(delta) * np.sin(alpha), np.sin(delta)], axis=-1)
    east = np.stack([-np.sin(alpha), np.cos(alpha), np.zeros_like(alpha)], axis=-1)
    north = np.stack([-np.sin(delta) * np.cos(alpha), -np.sin(delta) * np.sin(alpha), np.cos(delta)], axis=-1)
    an = np.einsum("ij,...j->...i", a, n)
    return np.stack([np.einsum("...i,...i->...", east, an), np.einsum("...i,...i->...", north, an)], axis=-1)


def endpoint_response(b_s, b_o, dot_b_o, distance, c=C_KMS):
    if not np.isfinite(distance) or distance <= 0 or not np.isfinite(c) or c <= 0:
        raise ValueError("positive finite distance and speed required")
    return checked_stf(2 * c * (checked_stf(b_o) - checked_stf(b_s)) / distance - checked_stf(dot_b_o))


def history_bound(dot_b_o, delta_t, distance, l_sigma, c=C_KMS):
    if not all(np.isfinite(v) for v in (delta_t, distance, l_sigma, c)) or delta_t <= 0 or distance <= 0 or l_sigma < 0 or c <= 0:
        raise ValueError("finite positive time/distance/speed and nonnegative bound required")
    return (2 * abs(c * delta_t / distance - 1) * np.linalg.norm(checked_stf(dot_b_o))
            + c * l_sigma * delta_t**2 / distance)


def unit_direction_field(a, n):
    a = checked_stf(a)
    n = np.asarray(n, float)
    if n.shape != (3,) or not np.isfinite(n).all() or abs(np.linalg.norm(n) - 1) > 1e-12:
        raise ValueError("unit direction required")
    an = a @ n
    return an - n * (n @ an)


def model_module():
    spec = importlib.util.spec_from_file_location("retained_a22_model", MODEL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(n_z=12, n_phi=24, offset=0):
    x, w = np.polynomial.legendre.leggauss(n_z)
    phi = (np.arange(n_phi) + offset) * 360 / n_phi
    ra = np.tile(phi, n_z)
    dec = np.repeat(np.rad2deg(np.arcsin(x)), n_phi)
    weight = np.repeat(w / (2 * n_phi), n_phi)
    return ra, dec, weight


def embedding(model):
    ra, dec, weight = grid()
    v = model.vsh(ra, dec, [2])[:, :, :5].reshape(-1, 5)
    d = np.stack([tangent(e, ra, dec) for e in E], axis=-1).reshape(-1, 5)
    m = np.linalg.lstsq(v, d, rcond=None)[0]
    ra2, dec2, _ = grid(15, 31, .37)
    v2 = model.vsh(ra2, dec2, [2])[:, :, :5].reshape(-1, 5)
    d2 = np.stack([tangent(e, ra2, dec2) for e in E], axis=-1).reshape(-1, 5)
    relative = float(np.max(np.abs(v2 @ m - d2)) / max(np.max(np.abs(d2)), 1))
    sphere = np.einsum("n,nki,nkj->ij", weight, d.reshape(-1, 2, 5), d.reshape(-1, 2, 5))
    metric_error = float(np.max(np.abs(m.T @ m - np.eye(5)/5)))
    sphere_error = float(np.max(np.abs(sphere - np.eye(5)/5)))
    if max(relative, metric_error, sphere_error) > 1e-12:
        raise AssertionError(f"E2 embedding mismatch {relative=} {metric_error=} {sphere_error=}")
    j = np.zeros((102, 5)); j[18:23] = m
    return m, j, {"separate_grid_max_relative_field_residual": relative,
                   "mapping_metric_max_abs_error": metric_error,
                   "sphere_quadrature_max_abs_error": sphere_error}


def psd_factor(g):
    g = np.asarray(g, float)
    if g.shape != (102, 102) or not np.isfinite(g).all():
        raise ValueError("finite 102x102 retained Gram required")
    scale = np.linalg.norm(g, 2)
    symmetry = np.linalg.norm(g - g.T, 2) / scale
    if symmetry > 1e-10:
        raise ArithmeticError(f"retained Gram asymmetry {symmetry}")
    ev, v = np.linalg.eigh((g + g.T)/2)
    if ev[0] < -1e-10 * scale:
        raise ArithmeticError(f"material negative retained Gram eigenvalue {ev[0]}")
    q = np.sqrt(np.maximum(ev, 0))[:, None] * v.T
    recon = np.linalg.norm(q.T @ q - g, 2) / scale
    if recon > 1e-10:
        raise ArithmeticError(f"retained Gram factor residual {recon}")
    return q, {"eigenvalues": ev.tolist(), "norm2": float(scale),
               "symmetry_relative": float(symmetry), "reconstruction_relative": float(recon)}


def profile(q, j, n, unprofiled_scale=None, rank_tol=1e-10):
    """Orthogonal SVD projection in whitened sufficient-statistic coordinates."""
    a, b = q @ j, q @ n
    da = np.linalg.norm(a, axis=0)
    db = np.linalg.norm(b, axis=0)
    if np.any(db == 0):
        raise ArithmeticError("zero nuisance column")
    u, singular, _ = np.linalg.svd(b/db, full_matrices=False)
    nuisance_rank = int(np.sum(singular > singular[0] * math.sqrt(rank_tol)))
    residual = a - u[:, :nuisance_rank] @ (u[:, :nuisance_rank].T @ a)
    info = residual.T @ residual
    eig, vectors = np.linalg.eigh(info)
    scale = float(unprofiled_scale if unprofiled_scale is not None else np.linalg.norm(a.T @ a, 2))
    rank = int(np.sum(eig > rank_tol * scale))
    return {"information": info, "eigenvalues": eig, "eigenvectors": vectors,
            "rank": rank, "nuisance_rank": nuisance_rank, "nuisance_scaled_singular_values": singular,
            "projected_whitened_columns": residual, "unprofiled_scale": scale}


def spin_glide():
    n = np.zeros((102, 6))
    for cohort in range(3):
        n[6*cohort:6*cohort+6] = np.eye(6)
    return n


def all97():
    return np.eye(102)[:, [*range(18), *range(23, 102)]]


def joint_report(q, j, n, p, score_b):
    a, b = q @ j, q @ n
    joint = np.column_stack([a, b])
    joint_gram = joint.T @ joint
    original_design = np.column_stack([j, n])
    joint_score = original_design.T @ score_b
    scale = np.linalg.norm(joint_gram, 2)
    rank = int(np.sum(np.linalg.eigvalsh(joint_gram) > 1e-10 * scale))
    cov = np.linalg.inv(joint_gram) if rank == joint.shape[1] else None
    info0 = a.T @ a
    cross = a.T @ b
    ev0 = np.linalg.eigvalsh(info0)
    c = np.linalg.svd(np.linalg.solve(np.linalg.cholesky(info0), cross) @ np.linalg.pinv(np.linalg.cholesky(b.T @ b).T), compute_uv=False) if n.shape[1] == 6 else None
    gls = np.linalg.solve(joint_gram, joint_score) if cov is not None else None
    return {"unprofiled_information": info0, "cross_gram": cross, "joint_rank": rank,
            "joint_covariance": cov, "full5_covariance": np.linalg.inv(p["information"]) if p["rank"] == 5 else None,
            "joint_signal_nuisance_covariance": cov[:5, 5:] if cov is not None else None,
            "canonical_correlations": c, "canonical_angles_degrees": np.rad2deg(np.arccos(np.clip(c, -1, 1))) if c is not None else None,
            "joint_score": joint_score, "joint_gls_coefficients": gls,
            "selected_sample_full5_coefficients_uasyr": gls[:5] if gls is not None else None,
            "unprofiled_eigenvalues": ev0}


def power_frontier(info):
    eig, vectors = np.linalg.eigh(info)
    rank = int(np.sum(eig > 1e-10 * np.linalg.norm(info, 2)))
    if rank == 0:
        raise ArithmeticError("power frontier requires nonzero information")
    threshold = float(chi2.ppf(.95, rank))
    power = lambda lam: float(ncx2.sf(threshold, rank, lam))
    lam80 = float(brentq(lambda x: power(x) - .8, 0, 1000, xtol=1e-10))
    rows = []
    for rho in [0, .01, .1, 1, 3, 10, 30, 100]:
        rows.append({"rho_uasyr": rho, "sphere_rms_uasyr": rho/math.sqrt(5),
                     "lambda_best": rho*rho*eig[-1], "lambda_worst": max(0, rho*rho*eig[0]),
                     "power_best": power(rho*rho*eig[-1]), "power_worst": power(max(0, rho*rho*eig[0]))})
    return {"rank": rank, "alpha": .05, "chi2_threshold": threshold, "lambda80": lam80,
            "rho80_best_uasyr": math.sqrt(lam80/eig[-1]),
            "rho80_worst_uasyr": math.sqrt(lam80/eig[0]) if eig[0] > 1e-10*np.linalg.norm(info,2) else None,
            "eigenvalues": eig, "eigenvectors_columns": vectors, "grid": rows}


def history_image(info, k):
    r = np.concatenate([k*np.eye(5), -np.eye(5)], axis=1)
    image = r.T @ info @ r
    null = np.concatenate([np.eye(5), k*np.eye(5)], axis=0)
    return {"k": k, "response_5x10": r, "information_10x10": image,
            "endpoint_derivative_cross_5x5": image[:5, 5:], "null_columns_10x5": null,
            "rank": int(np.sum(np.linalg.eigvalsh(image) > 1e-10 * np.linalg.norm(image, 2))),
            "null_residual_relative": float(np.linalg.norm(image @ null) / max(np.linalg.norm(image), 1))}


def jsonable(x):
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, dict): return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, list): return [jsonable(v) for v in x]
    return x


def build():
    for name, path in (("contract", CONTRACT), ("clarification", CLARIFICATION), ("stats", STATS), ("model", MODEL)):
        if digest(path) != EXPECTED[name]: raise RuntimeError(f"immutable {name} identity drift")
    model = model_module()
    m, j, emb = embedding(model)
    with np.load(STATS, allow_pickle=False) as source:
        g, b, rows = source["G"], source["b"], int(source["n"])
    if g.shape != (102,102) or b.shape != (102,) or rows != 755850: raise RuntimeError("retained sufficient-statistic shape/row drift")
    q, qcheck = psd_factor(g)
    n6, n97 = spin_glide(), all97()
    raw = j.T @ g @ j
    scale = np.linalg.norm(raw, 2)
    p6 = profile(q, j, n6, scale)
    p97 = profile(q, j, n97, scale)
    pe2 = profile(q, j, np.column_stack([n6, np.eye(102)[:,18:23]]), scale)
    pb1 = profile(q, n6[:,3:6], n6, np.linalg.norm((q@n6[:,3:6]).T@(q@n6[:,3:6]),2))
    if pe2["rank"] != 0 or pb1["rank"] != 0: raise AssertionError("nuisance annihilation failure")
    if np.linalg.eigvalsh(p97["information"]-p6["information"])[-1] > 1e-8*scale: raise AssertionError("all97 increased information")
    joint6, joint97 = joint_report(q,j,n6,p6,b), joint_report(q,j,n97,p97,b)
    rank_sensitivity = {}
    for tolerance in (1e-12, 1e-10, 1e-8):
        rank_sensitivity[str(tolerance)] = {"spin_glide6": profile(q,j,n6,scale,tolerance)["rank"],
                                             "all97": profile(q,j,n97,scale,tolerance)["rank"],
                                             "e2_free": profile(q,j,np.column_stack([n6,np.eye(102)[:,18:23]]),scale,tolerance)["rank"]}
    powers = power_frontier(p6["information"])
    histories = [history_image(p6["information"], k) for k in (0,.1,1,2,10)]
    output = {"schema":"htt.r36.pm_history_response/1", "task_id":"R36-03-PM-HISTORY", "parent_packet_id":PACKET,
              "input_identity":INPUT, "contract_sha256":EXPECTED["contract"], "implementation_helper_agent_id":"/root/r36_pm_history_numeric_helper",
              "bounded_validator_clarification":{"path":str(CLARIFICATION),"sha256":EXPECTED["clarification"]},
              "theory_author_agent_id":"/root/rc_c8d9f6351c42fc6d", "requested_helper_runtime":"gpt-6-sol/high",
              "observed_helper_runtime":"UNKNOWN", "acceptance_met":False, "claim_tier":"C0 conditional response/design",
              "proposed_field":"pm_history_response", "transfer_source":"none; first-order kinematic response",
              "source":{"model_sha256":EXPECTED["model"], "full_stats_sha256":EXPECTED["stats"], "selected_rows":rows,
                        "working_noise":"reported marginal 2x2 PM blocks; stipulated cross-source independence; spatial covariance UNKNOWN"},
              "response":{"basis_matrices":E,"vsh_e2_to_stf":m,"embedding_checks":emb,
                          "equation":"A=2c(B_o-B_s)/D-dot B_o; mu=P A n", "near_limit":"+sigma_o", "distant_fixed_endpoint_limit":"-sigma_o",
                          "endpoint_witness_delta_A_coefficients": [5e-5,0,0,0,0], "endpoint_witness_sphere_rms":1e-4/(2*math.sqrt(5))},
              "gram":{"factor_checks":qcheck,"unprofiled_information_5x5":raw,"source_score_b102":b,
                      "rank_sensitivity_relative_to_unprofiled":rank_sensitivity,
                      "primary_spin_glide6":{"profile":p6,"joint":joint6},
                      "all97_sensitivity":{"profile":p97,"joint":joint97},
                      "e2_nuisance_falsifier":{"rank":pe2["rank"],"projected_eigenvalues":pe2["eigenvalues"]},
                      "common_b1_spin_falsifier":{"rank":pb1["rank"],"projected_eigenvalues":pb1["eigenvalues"]}},
              "power_frontier":powers,"history_images":histories,
              "history_family_q_equals_s":[{"k":k,"signed_gain":k-1,"power_multiplier":(k-1)**2} for k in (0,.1,1,2,10)],
              "limitations":["No physical source depth law or arbitrary depth-weighted E2 cross moments", "No optical-centroid-to-matter calibration",
                             "No NNR likelihood, empirical cross-source covariance, or selection coverage", "No native solver or family identification"]}
    return jsonable(output)


def main():
    out = build()
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE/"RESULT.json").write_text(json.dumps(out, indent=2, allow_nan=False)+"\n")
    table = ["# R36-03-PM-HISTORY conditional design table", "",
             "Owner: obsstat response / htt conditional information. Claim tier: C0. Transfer source: none.",
             "Source: retained 755850-row A22 full_stats 102x102 Gram; reported marginal 2x2 errors and stipulated cross-source independence.",
             "Radii are design variables in full-five Frobenius microarcsec/year. Values are fixed-design Gaussian working power, not measured physical limits.", "",
             "| Profile | Rank | Eigenvalues (microarcsec/year)^-2 | rho80 best | rho80 worst |", "|---|---:|---|---:|---:|"]
    for name, block in (("common spin/glide6",out["gram"]["primary_spin_glide6"]),
                        ("all97 sensitivity",out["gram"]["all97_sensitivity"])):
        ev = block["profile"]["eigenvalues"]
        frontier = power_frontier(np.array(block["profile"]["information"]))
        table.append(f"| {name} | {block['profile']['rank']} | {', '.join(f'{v:.6g}' for v in ev)} | {frontier['rho80_best_uasyr']:.6g} | {frontier['rho80_worst_uasyr']:.6g} |")
    table += ["", "| rho (microarcsec/year) | Sphere RMS | Best noncentrality | Worst noncentrality | Best power | Worst power |",
              "|---:|---:|---:|---:|---:|---:|"]
    for r in out["power_frontier"]["grid"]:
        table.append(f"| {r['rho_uasyr']:.6g} | {r['sphere_rms_uasyr']:.6g} | {r['lambda_best']:.6g} | {r['lambda_worst']:.6g} | {r['power_best']:.6g} | {r['power_worst']:.6g} |")
    table += ["", "For q=s, T_ref=Delta_t: k=0,0.1,1,2,10 gives signed gain -1,-0.9,0,+1,+9 respectively; power multiplier is gain squared. This fixed common-history family is conditional.", ""]
    (HERE/"DATA_TABLE.md").write_text("\n".join(table))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = out["power_frontier"]["grid"]
    fig, ax = plt.subplots(figsize=(6.5,4.2))
    x = [r["rho_uasyr"] for r in rows]
    ax.plot(x,[r["power_best"] for r in rows],"o-",label="best STF direction")
    ax.plot(x,[r["power_worst"] for r in rows],"s-",label="worst STF direction")
    ax.axhline(.8,color="gray",ls="--",lw=1)
    ax.set(xscale="symlog",xlabel="full-five tensor radius (microarcsec/year)",ylabel="conditional Gaussian power",ylim=(0,1.02))
    ax.legend(); fig.tight_layout()
    fig.savefig(HERE/"POWER_FRONTIER.svg");fig.savefig(HERE/"POWER_FRONTIER.pdf");plt.close(fig)
    fig, ax = plt.subplots(figsize=(5,4.5))
    im=ax.imshow(out["gram"]["primary_spin_glide6"]["profile"]["information"],cmap="coolwarm")
    ax.set(xlabel="STF coefficient",ylabel="STF coefficient",title="Projected full-five information")
    fig.colorbar(im,ax=ax,label="(microarcsec/year)^-2");fig.tight_layout()
    fig.savefig(HERE/"INFORMATION.svg");fig.savefig(HERE/"INFORMATION.pdf");plt.close(fig)
    print(json.dumps({"result":str(HERE/"RESULT.json"),"rank6":out["gram"]["primary_spin_glide6"]["profile"]["rank"],
                      "rank97":out["gram"]["all97_sensitivity"]["profile"]["rank"],
                      "eigenvalues":out["power_frontier"]["eigenvalues"],"rho80_best":out["power_frontier"]["rho80_best_uasyr"],
                      "rho80_worst":out["power_frontier"]["rho80_worst_uasyr"]}))


if __name__ == "__main__": main()
