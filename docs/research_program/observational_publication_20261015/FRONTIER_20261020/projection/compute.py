"""Conditional response geometry on the retained D03 selected Pantheon rows.

This computes design geometry only. It neither fits observations nor evolves a
Boltzmann/Einstein system. The cached zCMB values are fiducial depths, not an
asserted normal-frame redshift match to the analytic optical model.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.linalg import solve_triangular

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
D03 = ROOT / "docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D03_PANTHEON_CF4/results/host_SN.npz"
EXPECTED_SHA256 = "dbe691cbaaf99f18c1515df1c7955e0e3520edac738ad64d83b4e867941a4a97"
C_KM_S = 299792.458
MU_FACTOR = 5.0 / np.log(10.0)
OMEGA_M, OMEGA_R = 0.3, 9.0e-5
OMEGA_L = 1.0 - OMEGA_M - OMEGA_R


def background(z: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Flat fiducial background via a distance integral, with H0 cancelling."""
    z = np.asarray(z, dtype=float)
    if z.ndim != 1 or not np.all(np.isfinite(z)) or np.any(z <= 0):
        raise ValueError("finite strictly positive fiducial redshifts required")

    def e(x: float) -> float:
        return np.sqrt(OMEGA_M * (1 + x) ** 3 + OMEGA_R * (1 + x) ** 4 + OMEGA_L)

    hz = np.array([e(float(x)) for x in z])
    dimensionless_chi = np.array([quad(lambda x: 1.0 / e(x), 0.0, float(v), epsabs=1e-12)[0] for v in z])
    a = (1.0 + z) / (hz * dimensionless_chi)
    h = 1.0 + z - z * a
    return a, h, dimensionless_chi


def directions(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra, dec = np.deg2rad(ra_deg), np.deg2rad(dec_deg)
    if not (np.all(np.isfinite(ra)) and np.all(np.isfinite(dec))):
        raise ValueError("finite directions required")
    return np.column_stack((np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)))


def rank_and_angles(cov: np.ndarray, nuisance: np.ndarray, blocks: dict[str, np.ndarray]) -> dict:
    """Whiten once, remove the nuisance span, and compare 3D subspaces."""
    n = cov.shape[0]
    if cov.shape != (n, n) or nuisance.shape[0] != n or any(b.shape != (n, 3) for b in blocks.values()):
        raise ValueError("design/covariance shape mismatch")
    chol = np.linalg.cholesky(cov)
    whiten = lambda x: solve_triangular(chol, x, lower=True, check_finite=True)
    wn = whiten(nuisance)
    un, sn, _ = np.linalg.svd(wn, full_matrices=False)
    nr = int(np.sum(sn > sn[0] * max(wn.shape) * np.finfo(float).eps))
    qn = un[:, :nr]
    projected = {k: (lambda w: w - qn @ (qn.T @ w))(whiten(v)) for k, v in blocks.items()}
    bases = {}
    norms = {}
    for key, arr in projected.items():
        u, s, _ = np.linalg.svd(arr, full_matrices=False)
        bases[key] = u[:, :3]
        norms[key] = [float(v) for v in np.linalg.norm(arr, axis=0)]
        unprojected_scale = np.linalg.svd(whiten(blocks[key]), compute_uv=False)[0]
        if s[-1] <= unprojected_scale * 1e-10:
            raise ValueError(f"{key} single-block rank below three")

    angles = {}
    names = list(projected)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            cosine = np.linalg.svd(bases[left].T @ bases[right], compute_uv=False)
            angles[f"{left}__{right}"] = [float(x) for x in np.rad2deg(np.arccos(np.clip(cosine, -1, 1)))]

    def combined(keys: list[str]) -> dict:
        arr = np.column_stack([projected[k] for k in keys])
        scales = np.linalg.norm(arr, axis=0)
        scaled = arr / scales
        s = np.linalg.svd(scaled, compute_uv=False)
        rank = int(np.sum(s > s[0] * 1e-10))
        return {"keys": keys, "rank": rank, "columns": int(s.size), "unit_column_singular_values": [float(v) for v in s], "unit_column_condition": float(s[0] / s[-1]) if rank == s.size else None}

    return {"nuisance_rank": nr, "nuisance_columns": nuisance.shape[1], "projected_column_norms": norms, "principal_angles_deg": angles,
            "models": {"optical": combined(["optical_local", "optical_history"]),
                       "calibration_flow": combined(["calibration", "flow_constant", "flow_linear"]),
                       "joint": combined(names)}}


def optical_after_flow_nuisance(cov: np.ndarray, nuisance: np.ndarray, blocks: dict[str, np.ndarray]) -> dict:
    """Check the analytic local/history columns after calibration/flow profiling."""
    extended = np.column_stack([nuisance, blocks["calibration"], blocks["flow_constant"], blocks["flow_linear"]])
    w = solve_triangular(np.linalg.cholesky(cov), extended, lower=True)
    u, s, _ = np.linalg.svd(w, full_matrices=False)
    rank_n = int(np.sum(s > s[0] * 1e-10))
    q = u[:, :rank_n]
    x = np.column_stack([blocks["optical_local"], blocks["optical_history"]])
    wx = solve_triangular(np.linalg.cholesky(cov), x, lower=True)
    px = wx - q @ (q.T @ wx)
    sv = np.linalg.svd(px, compute_uv=False)
    return {"nuisance_rank": rank_n, "nuisance_columns": extended.shape[1],
            "remaining_optical_rank": int(np.sum(sv > np.linalg.svd(wx, compute_uv=False)[0] * 1e-10)),
            "optical_residual_singular_values": [float(v) for v in sv],
            "local_residual_column_norms": [float(v) for v in np.linalg.norm(px[:, :3], axis=0)],
            "history_residual_column_norms": [float(v) for v in np.linalg.norm(px[:, 3:], axis=0)]}


def calibration_after_flow_nuisance(cov: np.ndarray, nuisance: np.ndarray, blocks: dict[str, np.ndarray]) -> dict:
    extended = np.column_stack([nuisance, blocks["flow_constant"], blocks["flow_linear"]])
    chol = np.linalg.cholesky(cov)
    w = solve_triangular(chol, extended, lower=True)
    u, s, _ = np.linalg.svd(w, full_matrices=False)
    nr = int(np.sum(s > s[0] * 1e-10))
    x = solve_triangular(chol, blocks["calibration"], lower=True)
    residual = x - u[:, :nr] @ (u[:, :nr].T @ x)
    sv = np.linalg.svd(residual, compute_uv=False)
    full_sv = np.linalg.svd(x, compute_uv=False)
    return {"flow_plus_D03_nuisance_rank": nr, "flow_plus_D03_nuisance_columns": extended.shape[1],
            "conditional_calibration_rank": int(np.sum(sv > full_sv[0] * 1e-10)),
            "conditional_calibration_singular_values": [float(v) for v in sv],
            "unprofiled_calibration_singular_values": [float(v) for v in full_sv],
            "smallest_relative_response": float(sv[-1] / full_sv[0])}


def main() -> None:
    digest = hashlib.sha256(D03.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"D03 immutable cache mismatch: {digest}")
    with np.load(D03, allow_pickle=False) as d:
        z = d["zCMB"]
        n = directions(d["RA"], d["DEC"])
        cov = d["P_full_covariance_subblock"].copy()
        nuisance = d["nuisance_design"].copy()
        rows = d["row_index"].copy()
    if len(np.unique(rows)) != len(rows) or not np.all(np.isfinite(cov)) or not np.allclose(cov, cov.T, rtol=0, atol=1e-12):
        raise ValueError("invalid selected-row or covariance identity")
    a, h, chi = background(z)
    # Optical magnitudes use dimensionless endpoint velocities. Source-model K
    # is mag/(km/s), evaluated with u=u_z=0 (the declared frozen-flow branch).
    k = -MU_FACTOR * (1.0 + a) / C_KM_S
    blocks = {"optical_local": MU_FACTOR * a[:, None] * n,
              "optical_history": MU_FACTOR * h[:, None] * n,
              "calibration": n,
              "flow_constant": k[:, None] * n,
              "flow_linear": (k * (chi / np.median(chi)))[:, None] * n}
    result = {"status": "CONDITIONAL_DESIGN_ONLY", "owner": "htt", "claim_tier": "C0", "source_npz_sha256": digest,
              "selected_rows": len(z), "row_index_sha256": hashlib.sha256(rows.tobytes()).hexdigest(),
              "zCMB_range": [float(z.min()), float(z.max())], "fiducial": {"omega_m": OMEGA_M, "omega_r": OMEGA_R, "omega_lambda": OMEGA_L,
              "flow": "u=u_z=0; constant and chi/median(chi) radial bases", "covariance": "D03 selected public Pantheon total subblock exactly once"},
              "geometry": rank_and_angles(cov, nuisance, blocks),
              "optical_after_calibration_flow": optical_after_flow_nuisance(cov, nuisance, blocks),
              "calibration_after_flow": calibration_after_flow_nuisance(cov, nuisance, blocks),
              "limits": ["zCMB used as fiducial depth, not verified normal-frame optical redshift", "no fitted amplitudes, p-values or coverage",
                         "unknown source/selection/optical remainder", "redshift-distance K excludes full optical Doppler, beaming and aberration", "no CF4 cross-covariance or stochastic PV addition"]}
    HERE.mkdir(exist_ok=True)
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    axes[0].scatter(z, h / a, s=9, alpha=0.55)
    axes[0].set(xlabel="fiducial $z_{CMB}$", ylabel="$h/A$", title="Analytic history versus local")
    pairs = ["optical_local__optical_history", "calibration__flow_constant", "calibration__flow_linear"]
    vals = [min(result["geometry"]["principal_angles_deg"][p]) for p in pairs]
    axes[1].bar(range(len(vals)), vals, color=["#315c83", "#9a6335", "#6b8444"])
    axes[1].set_xticks(range(len(vals)), ["local/history", "cal/const flow", "cal/linear flow"], rotation=28, ha="right")
    axes[1].set(ylabel="smallest projected angle (degrees)", title="Fixed public covariance, D03 nuisance")
    fig.text(0.5, 0.005, "Conditional design only; no frame match, selection law, or physical remainder bound", ha="center", fontsize=8)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(HERE / "PROJECTION.png", dpi=180)
    fig.savefig(HERE / "PROJECTION.pdf")
    plt.close(fig)
    print(json.dumps({"rows": len(z), "result": str(HERE / "RESULT.json"), "geometry": result["geometry"]["models"]}))


if __name__ == "__main__":
    main()
