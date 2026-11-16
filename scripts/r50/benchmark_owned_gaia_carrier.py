"""Reanalyse Git-tracked Gaia statistics, without downloads or raw-row invention.

Run: PYTHONPATH=htt/src:htt:. python scripts/r50/benchmark_owned_gaia_carrier.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import chi2

from htt.htt.infer.gaussian_carrier_benchmark import (
    linear_compression_information, log_likelihood_ratio, profile_normal_carrier,
)

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "docs/research_program/observational_publication_20261015"
SOURCE = P / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-03-PM-HISTORY"
OUT = P / "R50_OBSERVED_CONVERGENCE_20261115"
EXPECTED = "4d9406de69546e72dff79d4fc611703e8eb450944c4dcc254f8484c98a22d5da"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    start = time.monotonic()
    stats = SOURCE / "audit_backup/derived_inputs/full_stats.npz"
    before = sha(stats)
    if before != EXPECTED:
        raise ValueError("retained observed statistics identity changed")
    spec = importlib.util.spec_from_file_location("r36_pm", SOURCE / "pm_history.py")
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    with np.load(stats, allow_pickle=False) as z:
        G, b, n = z["G"], z["b"], int(z["n"])
    archived = json.loads((SOURCE / "RESULT.json").read_text())
    # Reuse the already-verified VSH/STF chart from R36. The raw model imports
    # healpy although this retained-statistics calculation needs no map package.
    chart = np.asarray(archived["response"]["vsh_e2_to_stf"], float)
    J = np.zeros((102, 5))
    J[18:23] = chart
    embedding_checks = {"reused_R36_chart": True,
        "chart_metric_error": float(np.max(np.abs(chart.T@chart-np.eye(5)/5))),
        "stf_basis_metric_error": float(np.max(np.abs(np.einsum("aij,bij->ab",old.E,old.E)-np.eye(5))))}
    if max(embedding_checks["chart_metric_error"],embedding_checks["stf_basis_metric_error"]) > 1e-12:
        raise AssertionError(embedding_checks)
    # Whiten by Cholesky independently of the Schur-complement implementation.
    L = np.linalg.cholesky(G)
    W = L.T
    y = np.linalg.solve(L, b)
    results = {}
    for name, N in [("primary_spin_glide6", old.spin_glide()), ("all97_sensitivity", old.all97())]:
        F, t, mean, C = profile_normal_carrier(G, b, J, N)
        nuisance_q, _ = np.linalg.qr(W @ N, mode="reduced")
        A = W @ J - nuisance_q @ (nuisance_q.T @ W @ J)
        yr = y - nuisance_q @ (nuisance_q.T @ y)
        checks = {
            "schur_vs_whitened_F_max_abs": float(np.max(np.abs(F-A.T@A))),
            "schur_vs_whitened_t_max_abs": float(np.max(np.abs(t-A.T@yr))),
            "archived_F_max_abs": float(np.max(np.abs(F-np.asarray(archived["gram"][name]["profile"]["information"])))),
        }
        rng = np.random.default_rng(501115)
        llr_errors = []
        for theta in rng.normal(size=(30, 5)):
            direct = -0.5 * (np.linalg.norm(yr-A@theta)**2-np.linalg.norm(yr)**2)
            llr_errors.append(abs(log_likelihood_ratio(F,t,theta,np.zeros(5))-direct))
        checks["full_vs_tensor_logLR_max_abs"] = max(llr_errors)
        if max(checks.values()) > 1e-8:
            raise AssertionError(checks)
        # Fixed Cartesian STF basis alternatives; never orient alternatives using y.
        I = np.eye(5)
        scalar_F = linear_compression_information(F, I[:1])
        eig, evec = np.linalg.eigh(F)
        Finvhalf = (evec / np.sqrt(eig)) @ evec.T
        retention = np.linalg.eigvalsh(Finvhalf @ scalar_F @ Finvhalf)
        sign_pairs = []
        for j in range(5):
            plus, minus = I[j], -I[j]  # +/-1 microarcsecond/year
            sign_pairs.append({"axis": j, "amplitude_uasyr": 1.0,
                "full_tensor_logLR_plus_vs_minus": log_likelihood_ratio(F,t,plus,minus),
                # Any even statistic T(-y)=T(y) has identical laws for +/-theta.
                "even_norm_summary_logLR_plus_vs_minus": 0.0})
        q = float(t @ mean)
        results[name] = {
            "nuisance_columns": N.shape[1], "information": F.tolist(),
            "score": t.tolist(), "mean_stf5_uasyr": mean.tolist(),
            "covariance_stf5_uasyr2": C.tolist(), "information_eigenvalues": eig.tolist(),
            "zero_E2_chi2": q, "zero_E2_df": 5,
            "zero_E2_working_law_tail": float(chi2.sf(q, 5)),
            "tensor_vs_optimal_linear_score": "TIE: both retain the same F and t",
            "scalar_fixed_axis_generalized_Fisher_retention": retention.tolist(),
            "signed_alternative_results": sign_pairs, "checks": checks,
        }
    dmean = np.asarray(results["primary_spin_glide6"]["mean_stf5_uasyr"]) - np.asarray(results["all97_sensitivity"]["mean_stf5_uasyr"])
    result = {
        "schema_version": "htt.r50.observed_carrier_benchmark/1",
        "status": "completed_conditional_saved_observed_law",
        "owner": "htt", "claim_tier": "C0", "transfer_source": "none",
        "assertion_tested": "Observed normal-equation carrier yields lossless five-component Gaussian target ratios; scalar linear/even summaries lose specified targets; nuisance model materially changes target inference.",
        "input": {"path": str(stats.relative_to(ROOT)), "sha256_before": before,
            "sha256_after": sha(stats), "source_rows": n, "raw_catalogue_reread": False,
            "working_law": archived["source"]["working_noise"]},
        "basis": archived["response"]["basis_matrices"],
        "units": "E2 STF tangent proper-motion coefficients in microarcsecond/year; not sigma/H",
        "physical_response": "A_PM=2*c*(B_o-B_s)/D-dot(B_o), conditional first-order endpoint history",
        "embedding_checks": embedding_checks, "nuisance_models": results,
        "nuisance_mean_shift_norm_uasyr": float(np.linalg.norm(dmean)),
        "limitations": archived["limitations"] + [
            "Conditional Gaussian working-law tails are not calibrated discovery probabilities.",
            "No proper-prior evidence comparison between the two nuisance models.",
            "Scalarization result is a target-specific benchmark, not generic 92.9 percent information loss.",
            "No new cosmological posterior or new general compression theorem is claimed."],
        "execution": {"command": "PYTHONPATH=htt/src:htt:. python scripts/r50/benchmark_owned_gaia_carrier.py",
            "source_base_commit": subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            "numpy": np.__version__, "scipy": scipy.__version__,
            "dependency_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (
                SOURCE/"RESULT.json", SOURCE/"pm_history.py",
                ROOT/"htt/htt/htt/infer/gaussian_carrier_benchmark.py")},
            "code_sha256": sha(Path(__file__)), "elapsed_seconds": time.monotonic()-start},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"OBSERVED_GAIA_BENCHMARK.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:{"chi2":v["zero_E2_chi2"],"tail":v["zero_E2_working_law_tail"],"mean":v["mean_stf5_uasyr"],"checks":v["checks"]} for k,v in results.items()},indent=2))


if __name__ == "__main__":
    run()
