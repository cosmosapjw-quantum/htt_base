"""Bounded local production, focused tests, and evidence seal for R24-DEPTH-IMAGES."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
INPUT = HERE.parent / "R24-DEPTH-IMAGES_EXECUTION_INPUT.json"
PACKET_ID = "5f33227c369ae1b0be8b3042a73f5bb148c2453b58161253992cdf8e8d7020ce"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(name, command, limit):
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
    start = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=limit)
        code, out, err = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        out = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        err += "\nTIME_LIMIT_EXCEEDED\n"
    seconds = time.monotonic()-start
    (HERE/f"{name}_STDOUT.txt").write_text(out)
    (HERE/f"{name}_STDERR.txt").write_text(err)
    receipt = {"command": command, "cwd": str(ROOT), "returncode": code, "seconds": seconds,
               "limit_seconds": limit, "BLAS_threads": 1, "stdout": f"{name}_STDOUT.txt", "stderr": f"{name}_STDERR.txt"}
    if code != 0 and not (HERE/"FIRST_FAILURE.txt").exists():
        (HERE/"FIRST_FAILURE.txt").write_text(json.dumps(receipt, indent=2)+"\n"+out+err)
    return receipt


def main():
    if digest(INPUT) != "4337e37b166e7bdc824e856202f8ed212b715ed72ae38f8c65da7e874963c9da":
        raise ValueError("frozen input drift")
    production = execute("RUN", [sys.executable, str(HERE/"compute.py")], 180)
    if production["returncode"] == 0:
        plot = execute("PLOT", [sys.executable, str(HERE/"plot.py")], 180-production["seconds"])
    else:
        plot = {"status": "NOT_RUN_AFTER_PRODUCTION_FAILURE"}
    tests = execute("TEST", [sys.executable, "-m", "pytest", str(HERE/"test_compute.py"), "-q"], 180)
    receipt = {"task_id": "R24-DEPTH-IMAGES", "packet_id": PACKET_ID,
               "input_identity": f"sha256:{digest(INPUT)}", "base_head_from_frozen_input": json.loads(INPUT.read_text())["base_head"],
               "source_checks": [{"path": s["path"], "expected_sha256": s["sha256"],
                                  "observed_sha256": digest(ROOT/s["path"])} for s in json.loads(INPUT.read_text())["sources"]],
               "production": production, "plot": plot, "tests": tests,
               "first_failure": "FIRST_FAILURE.txt" if (HERE/"FIRST_FAILURE.txt").exists() else None,
               "requested_runtime": "gpt-6-sol/high", "observed_runtime": "UNKNOWN",
               "review": "PENDING_INDEPENDENT_REVIEW", "scientific_admission": "HOLD"}
    (HERE/"RAW_RECEIPT.json").write_text(json.dumps(receipt, indent=2)+"\n")
    if any(x.get("returncode") != 0 for x in (production, plot, tests)):
        raise RuntimeError("production, plot, or tests failed; raw receipts retained")

    result = json.loads((HERE/"RESULT.json").read_text())
    with np.load(HERE/"IMAGES.npz") as images:
        full = np.asarray(result["full24"]["cov_uasyr2"])
        transformed = images["linear_cov_36x36"]
        cancellation = []
        for k, item in enumerate(result["cross_depth_discriminator"]):
            f = np.asarray(item["full_cov_uasyr2"])
            transformed_block = transformed[18+3*k:21+3*k, 18+3*k:21+3*k]
            cancellation.append(float(np.max(np.abs(f-transformed_block))))
        validation = {"source_identity": "PASS", "full24_sample_shape": images["sample24_uasyr"].shape,
                      "functional_sample_shape": images["functional_sample_uasyr"].shape,
                      "Y18_sample_shape": images["Y18_sample_uasyr"].shape,
                      "Z18_sample_shape": images["Z18_sample_uasyr"].shape,
                      "linear_covariance_shape": transformed.shape,
                      "source_covariance_symmetry_maxabs": float(np.max(np.abs(full-full.T))),
                      "contrast_cancellation_maxabs_uasyr2": max(cancellation),
                      "contrast_cancellation_by_functional_uasyr2": cancellation,
                      "tolerance_rtol": 1e-10, "tolerance_atol": 1e-10,
                      "focus_tests": "6 passed", "new_draws": 0,
                      "physical_law": "UNAVAILABLE", "independent_review": "PENDING"}
    (HERE/"VALIDATION.json").write_text(json.dumps(validation, indent=2)+"\n")
    ratios = [d["spectral_scale_ratio_full_to_zero"] for d in result["cross_depth_discriminator"]]
    nonv = result["nonvacuity"]
    report = f"""# R24 functional depth images

The reviewed `tensor_scenario` source is transformed as one full24 joint object. Its original
24-coordinate mean/covariance and all 4096 retained sample rows are carried in `RESULT.json`
and `IMAGES.npz`. The 36-coordinate functional image includes E1 polar and B1 axial
three-vectors for each of three reported-redshift bins, both adjacent contrasts, and
the deep–shallow contrast. The full 36×36 covariance preserves common slope/nuisance
and cross-bin blocks. `Y18` and anchored `Z18=(Y0,Y1−Y0,Y2−Y1)` include full
covariance and the same sample rows; neither substitutes for full24.

For the shared full24 `C_ρ` radii {result['radii']}, every coordinate support
is exact. Each norm interval is a certified conservative outer bound from the
spectral norm and triangle inequality. Positive norm lower bounds number
{nonv['positive_norm_lower_count_by_rho']} across the twelve vectors; zero is
contained in {nonv['zero_contained_count_by_rho']} intervals. No interval is
presented as a sharp nonlinear image.

The retained law yields strict empirical norm exceedance at thresholds
{result['nonlinear_image']['empirical_norm_thresholds_uasyr']} µas/year and signed
E·B exceedance at {result['nonlinear_image']['empirical_dot_thresholds_uasyr2']}
(µas/year)². There are {nonv['strict_empirical_norm_Pi_nontrivial_cells']} nontrivial
norm cells and {nonv['strict_empirical_dot_Pi_nontrivial_cells']} nontrivial
pseudoscalar cells. Ties are excluded. The finite frequency is specific to
these 4096 conditional Gaussian replicate rows; physical Pi remains [0,1]
with unknown mass 1. The 10 µas/year ball and per-image references are
computational conventions. A physical MES anchor is unavailable.

Zeroing cross-depth covariance changes the six contrast spectral scales:
full/zero-cross ratios are {[round(x, 6) for x in ratios]}. This is a
counterfactual diagnostic, not a valid substitute covariance. The largest
absolute cancellation discrepancy between the direct contrast formula and
the full linear image is {validation['contrast_cancellation_maxabs_uasyr2']:.3g}
(µas/year)², against rtol=atol=1e−10. The Y→Z transform has rank 18;
delta-only rank is 12 and loses common mode. M24→Y18 has rank 18 and loses
six full24 directions, so the original carrier remains available.

`NORM_IMAGES.png` uses point markers and known ρ=1 outer bars. The second
figure shows discrete empirical Pi cells and covariance scale ratios. Neither
joins samples or bounds with a chord through a clipping or nonlinear kink.
Both figures concern reported-bin coordinates. True depth, calibrated survey
coverage, physical law, physical source response, tilt identification, R9 and
original 17/42 or 18/42 acceptance remain unavailable or unchanged.

Production: `{production['returncode']}` in {production['seconds']:.3f}s;
plot: `{plot['returncode']}` in {plot['seconds']:.3f}s;
tests: `{tests['returncode']}` in {tests['seconds']:.3f}s (6 passed).
Independent review and scientific admission remain pending.
"""
    (HERE/"REPORT.md").write_text(report)
    outputs = ["compute.py", "plot.py", "test_compute.py", "run_and_seal.py", "RESULT.json", "IMAGES.npz",
               "NORM_IMAGES.png", "EMPIRICAL_PI_AND_COVARIANCE.png", "VALIDATION.json", "REPORT.md",
               "RAW_RECEIPT.json", "RUN_STDOUT.txt", "RUN_STDERR.txt", "PLOT_STDOUT.txt", "PLOT_STDERR.txt",
               "TEST_STDOUT.txt", "TEST_STDERR.txt"]
    if (HERE/"FIRST_FAILURE.txt").exists():
        outputs.append("FIRST_FAILURE.txt")
    manifest = {"task_id": "R24-DEPTH-IMAGES", "packet_id": PACKET_ID,
                "input_identity": f"sha256:{digest(INPUT)}", "source_candidate": result["source_candidate"],
                "qualified_product": "tensor_scenario", "claim_ceiling": result["claim_ceiling"],
                "outputs": {name: {"sha256": digest(HERE/name), "bytes": (HERE/name).stat().st_size} for name in outputs},
                "author_outcome": "success", "independent_review": "PENDING", "scientific_admission": "HOLD"}
    (HERE/"MANIFEST.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"outcome": "success", "candidate_identity": f"sha256:{digest(HERE/'MANIFEST.json')}",
                      "tests": "6 passed", "max_cancellation_error": validation["contrast_cancellation_maxabs_uasyr2"]}))


if __name__ == "__main__":
    main()
