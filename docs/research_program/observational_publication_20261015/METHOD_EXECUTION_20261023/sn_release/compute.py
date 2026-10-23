"""Public Pantheon+ fixed-covariance conditional mean experiment.

Two stages: freeze the released selection, then run. No CF4 values or additional
stochastic velocity covariance enter the likelihood. The redshift-distance
response is a declared frozen-flow scenario, not a full optical GR response.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.linalg import solve_triangular
from scipy.stats import chi2, ncx2

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
SOURCE = Path("/mnt/extdrive/workdir/htt_open_data/pantheonplus/c447f0f")
TABLE = SOURCE / "Pantheon_SH0ES.dat"
COVARIANCE = SOURCE / "Pantheon_SH0ES_STAT_SYS.cov"
EXPECTED = {
    TABLE: "1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8",
    COVARIANCE: "abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc",
}
SELECTION = HERE / "FROZEN_SELECTION.json"
ROWS = HERE / "RELEASE_ROWS.csv"
C_KM_S = 299792.458
M = 5.0 / np.log(10.0)
OM, OR = 0.3, 9e-5
OL = 1.0 - OM - OR


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_sources() -> tuple[np.ndarray, np.ndarray, float]:
    for path, expected in EXPECTED.items():
        if digest(path) != expected:
            raise ValueError(f"immutable source mismatch: {path}")
    rows = np.genfromtxt(TABLE, names=True, dtype=None, encoding="utf-8")
    raw = np.loadtxt(COVARIANCE)
    n = int(raw[0])
    if n != 1701 or len(rows) != n or raw.size != 1 + n * n:
        raise ValueError("released row/covariance dimension mismatch")
    c = raw[1:].reshape(n, n)
    asym = float(np.max(np.abs(c - c.T)))
    return rows, (c + c.T) / 2.0, asym


def row_key(index: int, row: np.void) -> str:
    return f"{index}|{row['CID']}|{int(row['IDSURVEY'])}"


def freeze() -> None:
    if SELECTION.exists() or ROWS.exists():
        raise FileExistsError("selection already frozen; do not silently replace")
    rows, covariance, asym = checked_sources()
    selected = np.flatnonzero(rows["USED_IN_SH0ES_HF"] == 1)
    if len(selected) != 277 or np.any(rows["IS_CALIBRATOR"][selected] != 0):
        raise ValueError("released Hubble-flow selection changed")
    if not np.all(np.isfinite(rows["zCMB"][selected])) or np.any(rows["zCMB"][selected] <= 0):
        raise ValueError("invalid selected redshift")
    np.linalg.cholesky(covariance[np.ix_(selected, selected)])
    keys = [row_key(i, row) for i, row in enumerate(rows)]
    frozen = {
        "source_release_commit": "c447f0fea703fcd0fff57de5000947b5ca81286b",
        "table_sha256": EXPECTED[TABLE], "covariance_sha256": EXPECTED[COVARIANCE],
        "selection_rule": "released USED_IN_SH0ES_HF == 1; no additional retrospective cut",
        "row_count": 1701, "selected_count": len(selected),
        "selected_indices_0_based": selected.tolist(),
        "all_row_key_sha256": hashlib.sha256("\n".join(keys).encode()).hexdigest(),
        "selected_row_key_sha256": hashlib.sha256("\n".join(keys[i] for i in selected).encode()).hexdigest(),
        "excluded_count": len(rows) - len(selected),
        "covariance_policy": "full released total mag^2 matrix symmetric part once, then original-order selected subblock",
        "raw_covariance_max_asymmetry_mag2": asym,
        "released_fields": ["CID", "IDSURVEY", "IS_CALIBRATOR", "USED_IN_SH0ES_HF", "RA", "DEC", "zCMB", "zHD", "m_b_corr"],
    }
    with ROWS.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["row_index", "CID_literal", "IDSURVEY", "IS_CALIBRATOR", "USED_IN_SH0ES_HF", "selected", "RA_deg", "DEC_deg", "zCMB", "zHD", "m_b_corr_mag"])
        selected_set = set(selected)
        for i, row in enumerate(rows):
            writer.writerow([i, row["CID"], int(row["IDSURVEY"]), int(row["IS_CALIBRATOR"]), int(row["USED_IN_SH0ES_HF"]), int(i in selected_set), row["RA"], row["DEC"], row["zCMB"], row["zHD"], row["m_b_corr"]])
    frozen["row_registry_sha256"] = digest(ROWS)
    SELECTION.write_text(json.dumps(frozen, indent=2) + "\n")
    print(json.dumps({"frozen_selection": str(SELECTION), "selected": len(selected), "excluded": len(rows) - len(selected)}))


def background(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    def e(t: float) -> float:
        return float(np.sqrt(OM * (1 + t) ** 3 + OR * (1 + t) ** 4 + OL))
    chi = np.array([quad(lambda t: 1 / e(t), 0, float(v), epsabs=1e-12)[0] for v in z])
    mu = 5 * np.log10((1 + z) * C_KM_S * chi / 70.0) + 25.0
    a = (1 + z) / (np.array([e(float(v)) for v in z]) * chi)
    return mu, a


def directions(ra: np.ndarray, dec: np.ndarray) -> np.ndarray:
    a, d = np.deg2rad(ra), np.deg2rad(dec)
    return np.column_stack([np.cos(d) * np.cos(a), np.cos(d) * np.sin(a), np.sin(d)])


def fit(whitened_y: np.ndarray, whitened_x: np.ndarray, labels: list[str]) -> dict:
    u, s, vt = np.linalg.svd(whitened_x, full_matrices=False)
    rank = int(np.sum(s > s[0] * 1e-10))
    if rank != len(labels):
        raise ValueError(f"declared model rank loss: {labels}; rank {rank}/{len(labels)}")
    beta = vt.T @ ((u.T @ whitened_y) / s)
    cov = vt.T @ np.diag(1 / s**2) @ vt
    residual = whitened_y - whitened_x @ beta
    normal_residual = np.linalg.norm(whitened_x.T @ residual) / (np.linalg.norm(whitened_x) * max(1.0, np.linalg.norm(whitened_y)))
    return {"labels": labels, "beta": beta.tolist(), "covariance": cov.tolist(),
            "chi2": float(residual @ residual), "dof": int(len(whitened_y) - rank),
            "rank": rank, "singular_values": s.tolist(), "normal_equation_relative_residual": float(normal_residual)}


def contrast(whitened_y: np.ndarray, wbase: np.ndarray, wblock: np.ndarray, block_scale: float) -> dict:
    # Frisch-Waugh quotient: all columns and covariance are from one joint law.
    q, _ = np.linalg.qr(wbase, mode="reduced")
    pblock = wblock - q @ (q.T @ wblock)
    py = whitened_y - q @ (q.T @ whitened_y)
    sv = np.linalg.svd(pblock, compute_uv=False)
    if sv[-1] <= np.linalg.svd(wblock, compute_uv=False)[0] * 1e-10:
        raise ValueError("profiled block rank loss")
    info = pblock.T @ pblock
    coef = np.linalg.solve(info, pblock.T @ py)
    cov = np.linalg.inv(info)
    eigen = np.linalg.eigvalsh(info)
    # Analytic noncentral chi-square power under a declared fixed Gaussian law;
    # no observed-data p-value or matched directional reference law is produced.
    alpha = 0.05
    threshold = float(chi2.isf(alpha, df=3))
    power = {}
    for axis, unit in zip("xyz", np.eye(3)):
        displacement = block_scale * unit
        lam = float(displacement @ info @ displacement)
        power[axis] = {"noncentrality": lam, "power_at_fixed_gaussian_alpha_0p05": float(ncx2.sf(threshold, 3, lam))}
    return {"coefficient": coef.tolist(), "coefficient_covariance": cov.tolist(),
            "coefficient_unit": "mag" if block_scale == 0.01 else "km/s",
            "information_eigenvalues": eigen.tolist(), "singular_values": sv.tolist(),
            "unit_vector_injection": block_scale, "conditional_gaussian_reference_power": power}


def run() -> None:
    frozen = json.loads(SELECTION.read_text())
    if digest(ROWS) != frozen["row_registry_sha256"]:
        raise ValueError("frozen full-row registry mismatch")
    rows, full_cov, asym = checked_sources()
    idx = np.array(frozen["selected_indices_0_based"], dtype=int)
    if len(idx) != 277 or not np.array_equal(idx, np.flatnonzero(rows["USED_IN_SH0ES_HF"] == 1)):
        raise ValueError("frozen selection/source row mismatch")
    if asym != frozen["raw_covariance_max_asymmetry_mag2"]:
        raise ValueError("source covariance asymmetry changed")
    selected = rows[idx]
    cov = full_cov[np.ix_(idx, idx)]
    chol = np.linalg.cholesky(cov)
    z = selected["zCMB"].astype(float)
    fiducial_mu, a = background(z)
    y = selected["m_b_corr"].astype(float) - fiducial_mu
    n = directions(selected["RA"].astype(float), selected["DEC"].astype(float))
    k = -M * (1 + a) / C_KM_S
    common = np.ones((len(z), 1))
    cal = n
    flow = k[:, None] * n
    # Survey intercepts are a separate sensitivity, with one reference survey.
    surveys = np.unique(selected["IDSURVEY"])
    survey = np.column_stack([(selected["IDSURVEY"] == value).astype(float) for value in surveys[1:]])
    whiten = lambda v: solve_triangular(chol, v, lower=True, check_finite=True)
    wy = whiten(y)
    wc, wd, wf, ws = map(whiten, (common, cal, flow, survey))
    models = {}
    designs = {
        "offset": (wc, ["common_offset_mag"]),
        "calibration": (np.column_stack([wc, wd]), ["common_offset_mag", "cal_x_mag", "cal_y_mag", "cal_z_mag"]),
        "flow": (np.column_stack([wc, wf]), ["common_offset_mag", "flow_x_km_s", "flow_y_km_s", "flow_z_km_s"]),
        "joint": (np.column_stack([wc, wd, wf]), ["common_offset_mag", "cal_x_mag", "cal_y_mag", "cal_z_mag", "flow_x_km_s", "flow_y_km_s", "flow_z_km_s"]),
        "survey_joint": (np.column_stack([wc, ws, wd, wf]), ["common_offset_mag"] + [f"survey_{int(v)}_minus_{int(surveys[0])}_mag" for v in surveys[1:]] + ["cal_x_mag", "cal_y_mag", "cal_z_mag", "flow_x_km_s", "flow_y_km_s", "flow_z_km_s"]),
    }
    for name, (wx, labels) in designs.items():
        models[name] = fit(wy, wx, labels)
    cal_after_flow = contrast(wy, np.column_stack([wc, wf]), wd, 0.01)
    flow_after_cal = contrast(wy, np.column_stack([wc, wd]), wf, 100.0)
    cal_after_survey_flow = contrast(wy, np.column_stack([wc, ws, wf]), wd, 0.01)
    flow_after_survey_cal = contrast(wy, np.column_stack([wc, ws, wd]), wf, 100.0)
    # Independent algebraic reference: whitened residual norm and GLS inverse.
    joint_x = designs["joint"][0]
    joint_beta = np.array(models["joint"]["beta"])
    direct_chi2 = float(np.linalg.norm(solve_triangular(chol, y - np.column_stack([common, cal, flow]) @ joint_beta, lower=True)) ** 2)
    inverse_beta = np.linalg.solve(joint_x.T @ joint_x, joint_x.T @ wy)
    solve_error = float(np.max(np.abs(inverse_beta - joint_beta) / np.maximum(1.0, np.abs(joint_beta))))
    chi2_error = abs(direct_chi2 - models["joint"]["chi2"]) / max(1.0, direct_chi2)
    if max(solve_error, chi2_error) > 1e-10:
        raise ValueError(f"independent solve mismatch: {solve_error}, {chi2_error}")
    joint_cov = np.array(models["joint"]["covariance"])
    cal_cov = joint_cov[1:4, 1:4]
    flow_cov = joint_cov[4:7, 4:7]
    cross_cov = joint_cov[1:4, 4:7]
    if np.max(np.abs(cal_cov - np.array(cal_after_flow["coefficient_covariance"]))) > 1e-10 or np.max(np.abs(flow_cov - np.array(flow_after_cal["coefficient_covariance"]))) > 1e-6:
        raise ValueError("Frisch-Waugh covariance reference mismatch")
    result = {
        "status": "CONDITIONAL_RELEASED_SN_EXPERIMENT", "owner": "htt", "claim_tier": "C0", "transfer_source": "none",
        "source_release_commit": frozen["source_release_commit"], "frozen_selection_sha256": digest(SELECTION),
        "rows": len(idx), "excluded_rows_retained_in_registry": frozen["excluded_count"],
        "unique_literal_CIDs_selected": len(set(selected["CID"])), "survey_values": [int(v) for v in surveys],
        "zCMB_range": [float(z.min()), float(z.max())],
        "working_law": {"observation": "released m_b_corr [mag]", "baseline": "flat FLRW mu(zCMB; Om=.3, Or=9e-5, Ol=.69991, H0=70 km/s/Mpc) plus free common offset", "conditional_on": "released Hubble-flow flag, observed zCMB and RA/DEC", "redshift_frame": "CMB catalogue zCMB used as fiducial depth; no source-matched normal-frame assertion", "covariance": "released total STAT_SYS symmetric part in mag^2 once; no added stochastic PV", "flow": "frozen u=du/dz=0 response K=-(5/ln10)(1+A)/c; mag/(km/s)", "calibration": "angular n_x,n_y,n_z in mag", "survey_sensitivity": "one indicator for each other released IDSURVEY relative to lowest survey code"},
        "covariance_checks": {"raw_max_asymmetry_mag2": asym, "selected_min_cholesky_diagonal_mag": float(np.min(np.diag(chol))), "selected_max_asymmetry_mag2": float(np.max(np.abs(cov - cov.T)))},
        "models": models,
        "model_chi2_improvements": {"calibration_vs_offset": models["offset"]["chi2"] - models["calibration"]["chi2"], "flow_vs_offset": models["offset"]["chi2"] - models["flow"]["chi2"], "joint_vs_offset": models["offset"]["chi2"] - models["joint"]["chi2"], "joint_vs_calibration": models["calibration"]["chi2"] - models["joint"]["chi2"], "joint_vs_flow": models["flow"]["chi2"] - models["joint"]["chi2"]},
        "profiled_contrasts": {"calibration_after_flow": cal_after_flow, "flow_after_calibration": flow_after_cal, "calibration_after_flow_and_survey": cal_after_survey_flow, "flow_after_calibration_and_survey": flow_after_survey_cal},
        "full_joint_coefficient_tensor_covariance": {"labels": models["joint"]["labels"], "matrix": models["joint"]["covariance"], "calibration_flow_cross_block": cross_cov.tolist()},
        "reference_checks": {"inverse_vs_SVD_relative_coefficient_max": solve_error, "direct_whitened_vs_SVD_relative_chi2": chi2_error, "normal_equation_max": max(v["normal_equation_relative_residual"] for v in models.values())},
        "claim_limits": ["No observed p value: no matched directional null/selection law", "Gaussian design power is conditional on the declared fixed law, not empirical coverage", "No CF4 joint likelihood or independence; cross-catalog covariance unavailable", "R23 nominal trained-model/FITRES parity remains HOLD", "No physical anisotropy or source-matched full GR optical response", "Repeated released rows are not independent supernovae"],
    }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.7))
    names = ["offset", "calibration", "flow", "joint", "survey_joint"]
    ax[0].bar(names, [models[t]["chi2"] for t in names], color="#56799c")
    ax[0].set(ylabel=r"Generalized residual $\chi^2$ (descriptive)", title="Same public total covariance")
    ax[0].tick_params(axis="x", rotation=28)
    for axis, key, title in [(ax[1], "calibration_after_flow", "Calibration after flow"), (ax[1], "flow_after_calibration", "Flow after calibration")]:
        vals = [result["profiled_contrasts"][key]["conditional_gaussian_reference_power"][v]["power_at_fixed_gaussian_alpha_0p05"] for v in "xyz"]
        x = np.arange(3) + (0 if key == "calibration_after_flow" else 0.34)
        axis.bar(x, vals, width=0.34, label=title)
    ax[1].set(xticks=np.arange(3) + .17, xticklabels=["x", "y", "z"], ylim=(0, 1), ylabel="Conditional Gaussian power", title="Fixed unit-vector injections")
    ax[1].legend(fontsize=8)
    fig.text(.5, .01, "C0 scenario; 0.01 mag calibration / 100 km s$^{-1}$ flow; no matched-null p or physical coverage", ha="center", fontsize=8)
    fig.tight_layout(rect=[0, .045, 1, 1])
    fig.savefig(HERE / "RELEASE_CONTRAST.png", dpi=170)
    fig.savefig(HERE / "RELEASE_CONTRAST.pdf")
    plt.close(fig)
    print(json.dumps({"rows": len(idx), "result": str(HERE / "RESULT.json"), "solve_error": solve_error, "chi2_error": chi2_error}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["freeze", "run"])
    args = parser.parse_args()
    freeze() if args.stage == "freeze" else run()
