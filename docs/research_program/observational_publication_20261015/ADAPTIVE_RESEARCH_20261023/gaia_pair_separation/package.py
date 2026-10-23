"""Package one saved R25 pair traversal without revisiting source pairs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from compute import BINS, CONTRACT, HERE, ROOT, SOURCE, STF, inspect_reference, sha256


RAW = Path("/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/raw")
PACKET = "aa790df7eb0065ca2ab6172316260ada09524cd10a15bfda5ba62d7bfcb3e0f5"
INPUT_SHA = "620d92030d235ee6ed8fb5e6d7ff999f4777f7540abbcb1841c23af50e878d50"


def elapsed(path):
    s = path.read_text()
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\S+)", s)
    parts = [float(x) for x in m.group(1).split(":")]
    return sum(x * 60**i for i, x in enumerate(reversed(parts)))


def rss(path):
    s = path.read_text()
    return 1024 * int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", s).group(1))


def main():
    t0 = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    sources = {x["path"]: x["sha256"] for x in contract["inputs"]}
    if sha256(CONTRACT) != INPUT_SHA:
        raise RuntimeError("contract identity drift")
    for p, h in sources.items():
        if sha256(ROOT / p) != h:
            raise RuntimeError(f"source identity drift: {p}")
    with np.load(RAW / "full_carrier.npz") as a:
        arrays = {k: a[k].copy() for k in a.files}
    Cd = np.load(RAW / "covariance.npy")
    H, D, d = arrays["H"], arrays["D"], arrays["d"]
    B, X, y = arrays["B"], arrays["X"], arrays["y"]
    counts = arrays["counts"]
    checks = {
        "d_Hy_max_abs": float(np.max(np.abs(d.reshape(-1)-H.reshape(117, -1)@y.reshape(-1)))),
        "D_HX_max_abs": float(np.max(np.abs(D.reshape(117, 13)-H.reshape(117, -1)@X.reshape(-1, 13)))),
        "HB_max_abs": float(np.max(np.abs(H.reshape(117, -1)@B.reshape(-1, 3)))),
        "covariance_symmetry_max_abs": float(np.max(np.abs(Cd-Cd.T))),
        "covariance_min_eigenvalue": float(np.linalg.eigvalsh((Cd+Cd.T)/2)[0]),
    }
    checks["normalized_accumulation_error"] = max(
        checks["d_Hy_max_abs"]/max(1, float(np.max(np.abs(d)))),
        checks["D_HX_max_abs"]/max(1, float(np.max(np.abs(D)))),
    )
    if counts.sum() != 11307390 or checks["normalized_accumulation_error"] > 1e-9 or checks["HB_max_abs"] > 1e-10:
        raise RuntimeError(f"saved-carrier control failed: {checks}")
    reference = inspect_reference(d, D, Cd)
    if reference["whitening_residual_spectral"] > 1e-9:
        raise RuntimeError("numerical whitening control failed")
    if reference["E1_full_nesting_spectral"] > 1e-10:
        raise RuntimeError("projector nesting control failed")
    result = json.loads((RAW / "RESULT.json").read_text())
    result["checks"] = checks
    result["reference"] = reference
    result["status"] = "DESCRIPTIVE_CONDITIONAL_CANDIDATE_PENDING_INDEPENDENT_REVIEW"
    result["array_carrier"] = "arrays.npz"
    result["field_description"] = "Saved n,E,X,B,y,C define the tangent field; source identities and bin edges reconstruct every pair kernel without storing pair rows."
    result["typed_response_profile"] = {
        "g_vector":d[:, :3].tolist(),
        "E2_stf_tensor":np.einsum("bk,kij->bij", d[:, 3:8], STF).tolist(),
        "B2_stf_tensor":np.einsum("bk,kij->bij", d[:, 8:13], STF).tolist(),
        "description":"Response tensors in frozen Frobenius-orthonormal STF basis; not fitted field tensors",
    }
    result["direction_matrix_singular_values"] = np.linalg.svd(arrays["n"], compute_uv=False).tolist()
    result["spin_quotient"] = "L B=0 analytically; saved H B checked. Compressed H has a large residual coordinate kernel; no full-kernel completeness claim."
    result["observed_execution_head_preflight"] = "e4dd81068f03d1ee52a6864b661a4104e6336147"
    result["source_hashes"] = sources
    result["input_identity"] = "sha256:" + INPUT_SHA
    result["working_law"] = "Fixed reported within-source C0, Gaussian proxy, actual cross-source Sigma UNKNOWN; outcome-selected source sample."
    result["tail_status"] = reference["tail_status"]
    result["full_coefficient_region_status"] = "UNBOUNDED_AFFINE_FIBER_IN_UNIDENTIFIED_DIRECTIONS; PSEUDOINVERSE_REPRESENTATIVE_ONLY"
    result["projected_mean_region_status"] = reference["projected_mean_ball"]["status"]
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    # One compressed public carrier; the uncompressed first raw record stays external.
    arrays["Cd"] = Cd
    arrays["W"] = np.asarray(reference["W"])
    arrays["covariance_eigenvalues"] = np.asarray(reference["covariance_eigenvalues"])
    arrays["covariance_eigenvectors"] = np.asarray(reference["covariance_eigenvectors"])
    arrays["M"] = np.asarray(reference["M"])
    arrays["z"] = np.asarray(reference["z"])
    candidate_arrays = RAW / "candidate_arrays.npz"
    np.savez_compressed(candidate_arrays, **arrays)
    free = os.statvfs(HERE).f_bavail * os.statvfs(HERE).f_frsize
    if candidate_arrays.stat().st_size + 2_000_000 > free:
        raise RuntimeError(f"repo free bytes {free} insufficient for final array bytes {candidate_arrays.stat().st_size}; external candidate retained")
    shutil.copyfile(candidate_arrays, HERE / "arrays.npz")
    candidate_arrays.unlink()

    centers = np.sqrt(BINS[:-1] * BINS[1:])
    centers[0] = .25
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
    for k, label in enumerate(("g_x", "g_y", "g_z")):
        axes[0].plot(centers, d[:, k], marker=".", label=label)
    axes[0].axhline(0, color="gray", linewidth=.6)
    axes[0].set_ylabel("Observed pair response (µas-equivalent/yr)")
    axes[0].legend()
    axes[1].plot(centers, np.linalg.norm(d[:, 3:8], axis=1), marker="o", label="E2 STF norm")
    axes[1].plot(centers, np.linalg.norm(d[:, 8:13], axis=1), marker="s", label="B2 STF norm")
    axes[1].set_ylabel("Five-coordinate response norm")
    axes[1].set_xlabel("Angular pair separation bin center (degrees)")
    axes[1].legend()
    fig.suptitle("Gaia selected-source angular-pair response; conditional diagnostic")
    fig.savefig(HERE / "figure.png", dpi=150)
    plt.close(fig)

    times = {name + "_" + run: elapsed(RAW / (name + "_time_" + run + ".txt")) for name, run in
             (("test", "01"), ("test", "02"), ("production", "01"), ("whitening_probe", "01"))}
    time_files = [RAW / f"{name}_time_{run}.txt" for name, run in
                  (("test", "01"), ("test", "02"), ("production", "01"), ("whitening_probe", "01"))]
    cumulative = sum(times.values())
    maximum_rss = max(map(rss, time_files))
    receipt = {
        "packet_id": PACKET, "task_id": contract["task_id"], "input_identity":"sha256:"+INPUT_SHA,
        "agent_id":"/root/rc_aa790df7eb0065ca", "requested":"gpt-6-sol/high", "observed_runtime":"UNKNOWN",
        "actual_ack":"/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/GAIA_PAIR_ACTUAL_ACK.json",
        "preflight_head":"e4dd81068f03d1ee52a6864b661a4104e6336147",
        "attempts":[
            {"kind":"toy_control", "ordinal":1, "status":"FAIL", "reason":"NumPy advanced-index shape assignment; raw first failure retained", "elapsed_seconds":times["test_01"]},
            {"kind":"toy_control", "ordinal":2, "status":"PASS", "elapsed_seconds":elapsed(RAW / "test_time_02.txt")},
            {"kind":"full_pair_traversal", "ordinal":1, "status":"PASS", "elapsed_seconds":times["production_01"], "pairs":11307390},
            {"kind":"saved_covariance_whitening_probe", "ordinal":1, "status":"PASS", "elapsed_seconds":times["whitening_probe_01"]},
        ],
        "raw_files_before_packaging": {p.name:sha256(p) for p in sorted(RAW.iterdir())
                                        if p.is_file() and not p.name.startswith("package_")},
        "cumulative_numeric_elapsed_seconds_before_packaging": cumulative,
        "maximum_numeric_rss_bytes":maximum_rss,
        "limits":{"numeric_seconds":300,"rss_bytes":1073741824,"threads":1,"pair_chunk_max":32768},
        "source_hashes":sources,
        "packaging_head_host_reported":"d93605e66adfececa89b90681124b232a5f90220",
        "notes":["One full pair traversal; no replay", "Production stdout saved full carrier before downstream covariance/reference", "Initial eigenbasis whitening residual 1.15e-7; saved-covariance correction reached numerical control without pair replay"],
    }
    (HERE / "RAW_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    report = f"""# Observed Gaia angular-pair spin quotient

This is a conditional diagnostic on 4,756 outcome-selected Gaia EDR3 frame sources. The single production traversal covered all {int(counts.sum()):,} pairs in the nine frozen angle bins. The retained `arrays.npz` contains full unprojected `H` (9×13×9512), `D` (9×13×13), `d` (9×13), `Cd` (117×117), the 13 g/E2/B2 STF response coordinates, source tangent data and covariance, all covariance modes, and the declared working projection. `compute.py` reconstructs the pair kernel from source directions and tangent bases. `d` is an observed response; its working expectation is `D beta`, so it is not a coefficient estimate.

The numerical controls give `max|d-Hy|={checks['d_Hy_max_abs']:.3g}`, `max|D-HX|={checks['D_HX_max_abs']:.3g}`, and `max|HB|={checks['HB_max_abs']:.3g}`. The common-spin contribution cancels exactly in the analytic pair kernel. The full uncompressed tangent pair kernel has only common rotation in its null space when the source direction matrix has rank 3; the binned operator has at most 117 rows and leaves many tangent directions unmeasured. The working shared-source covariance is `Cd=Σ_i H_i C_i H_i^T`, including cross-bin and cross-component terms. Actual cross-source covariance is unknown.

The fixed, outcome-independent covariance projection retains {len(reference['retained_indices'])} modes by a declared relative 1e-10 numerical threshold; diagnostic counts are {reference['rank_diagnostics']}. All discarded modes remain saved and are positive or ambiguous, never certified exact null. One covariance-only whitening correction reduced the computed spectral residual from {reference['initial_whitening_residual_spectral']:.3g} to {reference['whitening_residual_spectral']:.3g}; this is numerical control, not a certified bound. The E1 and full13 representative projected residuals are {reference['models']['E1']['T']:.6g} and {reference['models']['full13']['T']:.6g}; their descriptive difference is {reference['Delta_E1_minus_full']:.6g}. Projector symmetry, idempotence, nesting, singular spectra, fitted profiles and residuals are recorded in `RESULT.json`.

Full-model tails are **TAIL_UNRESOLVED** because complete projected model-image certification is unavailable. The 95% joint projected-mean ball is only a numerical Gaussian/C0 working approximation. Coefficient pseudoinverse output is a representative, never a finite 13-coordinate confidence region. The selected-source law and actual cross-source correlations are uncalibrated. `Pi` is a formal working law, `Q` has no physical MES anchor, and `G_F` is `DEPTH_UNAVAILABLE`; angular separation is not depth. No physical boost/shear, native solver, family identification, or original acceptance follows.

The first toy-control failure and subsequent pass, the one production traversal, the saved-covariance whitening probe, RSS and cumulative numerical time are in `RAW_RECEIPT.json`. This candidate awaits fresh independent read-only review.
"""
    (HERE / "REPORT.md").write_text(report)
    public = ["compute.py", "test_compute.py", "package.py", "RESULT.json", "arrays.npz", "figure.png", "REPORT.md", "RAW_RECEIPT.json"]
    manifest = {
        "task_id":contract["task_id"], "packet_id":PACKET,
        "status":"CANDIDATE_PENDING_INDEPENDENT_REVIEW", "claim_tier":"diagnostic_only_conditional",
        "owner":"HTT", "scope":"R25 selected-source angular-pair working law",
        "input_identity":"sha256:"+INPUT_SHA, "source_hashes":sources,
        "transfer_source":"NONE_ANGULAR_GAIA_PROPER_MOTION",
        "sky_support_status":"SELECTED_SOURCES_NONUNIFORM",
        "null_mock_status":"NO_CALIBRATED_NULL",
        "cross_source_covariance":"UNKNOWN", "generating_procedure":"compute.py one pair traversal; package.py saved-carrier only",
        "preflight_head":"e4dd81068f03d1ee52a6864b661a4104e6336147",
        "file_hashes":{p:sha256(HERE / p) for p in public},
        "external_raw_carrier":str(RAW / "full_carrier.npz"),
        "external_raw_carrier_sha256":sha256(RAW / "full_carrier.npz"),
    }
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    result_return = {
        "packet_id":PACKET, "task_id":contract["task_id"], "input_identity":"sha256:"+INPUT_SHA,
        "agent_id":"/root/rc_aa790df7eb0065ca", "outcome":"SUCCESS_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
        "candidate_identity":"sha256:"+sha256(HERE / "MANIFEST.json"),
        "validation_evidence":["4/4 toy controls pass after preserved first failure", "11,307,390 pairs once", "d=Hy, D=HX, HB=0 actual controls", "fixed covariance whitening numerical control", "projector nesting checked"],
        "raw_receipt":str(HERE / "RAW_RECEIPT.json"), "qualified_products":[],
        "actual_numeric_elapsed_seconds_before_packaging":cumulative,
        "actual_numeric_max_rss_bytes":maximum_rss,
        "limits":receipt["limits"], "source_hashes":sources,
        "scientific_status":"CONDITIONAL_DIAGNOSTIC; TAIL_UNRESOLVED; ORIGINAL_ACCEPTANCE_UNCHANGED",
    }
    (HERE / "RETURN.json").write_text(json.dumps(result_return, indent=2) + "\n")
    print(json.dumps({"stage":"packaged", "elapsed_seconds":time.monotonic()-t0, "cumulative_before_packaging":cumulative,
                      "max_rss_bytes":maximum_rss, "array_bytes":(HERE / "arrays.npz").stat().st_size,
                      "candidate_identity":result_return["candidate_identity"]}), flush=True)


if __name__ == "__main__":
    main()
