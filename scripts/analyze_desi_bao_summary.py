#!/usr/bin/env python3
"""Render the retained DESI scalar BAO release as a conditional summary.

Reuses the immutable HDF5 reader and HTT fixed-Gaussian observation law.
No catalogue refit, prior, reference cosmology, or mock campaign is introduced.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT / "htt/src", ROOT / "htt", ROOT / "htt/htt"):
    sys.path.insert(0, str(_path))

from obsstat.r9_product_intake import read_desi_qiso
from htt.infer.r7_desi_law import build_compressed_bao_law


METADATA = {
    "owner": "htt",
    "claim_tier": "C1",
    "status": "CONDITIONAL",
    "evidence_type": "artifact",
    "scope": "RETAINED_RELEASE_FIXED_GAUSSIAN_SCALAR_BAO_SUMMARY",
    "artifact_mode": "RELEASED_SUMMARY_REEXPRESSION",
    "transfer_source": "none",
    "sky_support_status": "NONANGULAR_SUMMARY",
    "null_mock_status": "NOT_RUN_NO_NEW_MOCK_CLAIM",
    "covariance_status": "FIXED_RELEASED_COVARIANCE_CONDITIONAL",
    "allowed_use": "Scalar released-summary measurement and pointwise conditional likelihood",
    "forbidden_uses": ["raw-catalogue coverage", "posterior or evidence", "angular or depth response",
                       "shear or tilt detection", "Bianchi family identification"],
}
CAVEATS = [
    "Conditional on the released fixed Gaussian summary approximation and its covariance.",
    "The retained syst product is used once; its stat alternative and raw rows are not independent factors.",
    "The qiso and D_V/r_d views are deterministic re-expressions of the same scalar observation.",
    "These pointwise intervals do not alter the historical R9 alpha=1/80 or family allocation.",
    "No new catalogue fit, posterior, evidence, holdout, mocks, angular response, or native transfer is supplied.",
]


def log_density_in_dv(log_density_q, fiducial):
    """Change OBSERVED coordinate: p_D(D_obs|q)=p_q(D_obs/fid|q)/fid.

    A reparameterization of the prediction alone has no Jacobian. Both versions
    give the same relative likelihood for the fixed observed data.
    """
    fiducial = float(fiducial)
    if not math.isfinite(fiducial) or fiducial <= 0:
        raise ValueError("fiducial scale must be finite and positive")
    values = np.asarray(log_density_q, dtype=float)
    if np.any(np.isnan(values)) or np.any(np.isposinf(values)):
        raise ValueError("invalid log sampling density")
    return values - math.log(fiducial)


def analyze_payload(payload, grid_points=601):
    """Analyze a reader payload; tests may supply explicitly synthetic payloads."""
    if not isinstance(grid_points, int) or grid_points < 3 or grid_points % 2 == 0:
        raise ValueError("grid_points must be an odd integer of at least 3")
    fiducial, zeff = float(payload["DV_over_rd_fid"]), float(payload["zeff"])
    if not math.isfinite(fiducial) or fiducial <= 0 or not math.isfinite(zeff) or zeff <= 0:
        raise ValueError("fiducial scale and redshift must be finite and positive")
    # Existing law checks likelihood type, scalar shape, finite data, positive
    # covariance and identity window. Unsupported windows must remain errors.
    law = build_compressed_bao_law(payload)
    center, variance = float(law.observed[0]), float(law.covariance[0, 0])
    if center <= 0:
        raise ValueError("this released-summary presentation requires a positive observed qiso")
    sigma = math.sqrt(variance)
    peak = float(law.loglik([center]))
    coverage_1sigma = math.erf(1 / math.sqrt(2))
    intervals = []
    for name, coverage, critical in (("one_sigma", coverage_1sigma, 1.),
                                     ("95_percent", .95, float(norm.ppf(.975)))):
        lower, upper = center - critical * sigma, center + critical * sigma
        bounded_lower = max(0., lower)
        intervals.append({"name": name, "coverage": coverage, "critical_standard_normal": critical,
                          "qiso": [bounded_lower, upper],
                          "DV_over_rd": [bounded_lower * fiducial, upper * fiducial],
                          "lower_endpoint_included": lower > 0,
                          "construction": "central fixed-Gaussian acceptance inversion intersected with qiso>0"})
    lower = max(center - 4 * sigma, np.nextafter(0., 1.))
    grid = np.unique(np.r_[np.linspace(lower, center + 4 * sigma, grid_points), center])
    loglik = np.array([law.loglik([float(q)]) for q in grid], dtype=float)
    relative = np.exp(loglik - peak)
    result = {
        **METADATA, "caveats": CAVEATS,
        "source": dict(payload),
        "law": {"specification_id": law.specification_id,
                "conditioning_target": law.conditioning_target,
                "approximation": law.approximation,
                "domain": "qiso_prediction > 0; Gaussian observed-variable support is real",
                "reader": "obsstat.r9_product_intake.read_desi_qiso",
                "factory": "htt.infer.r7_desi_law.build_compressed_bao_law"},
        "measurement": {"qiso": center, "qiso_sigma": sigma, "qiso_variance": variance,
                        "DV_over_rd": center * fiducial, "DV_over_rd_sigma": sigma * fiducial,
                        "DV_over_rd_variance": variance * fiducial ** 2,
                        "DV_over_rd_fid": fiducial, "zeff": zeff, "units": "dimensionless"},
        "conditional_intervals": intervals,
        "curve": {"points": len(grid), "extent_sigma": 4,
                  "meaning": "fixed observed data, varying scalar prediction; relative likelihood has peak 1",
                  "log_density_q": "normalized in qiso_observed at fixed prediction, not in prediction",
                  "log_density_D": "normalized in D_observed at fixed prediction; log_density_q-log(fiducial)",
                  "prediction_reparameterization": "D_prediction=fiducial*qiso_prediction; no likelihood Jacobian",
                  "no_parameter_probability": True},
        "historical_reference": "scripts/observed_runs/run_tensor_joint_r9_product.py (unchanged; not rerun)",
    }
    curve = {"qiso_prediction": grid, "DV_over_rd_prediction": grid * fiducial,
             "log_sampling_density_q_at_observed": loglik,
             "log_sampling_density_D_at_observed": log_density_in_dv(loglik, fiducial),
             "relative_likelihood": relative, "delta_chi_square": -2 * (loglik - peak)}
    return result, curve


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(*arguments):
    completed = subprocess.run(["git", "-C", str(ROOT), *arguments], capture_output=True, text=True)
    return completed.stdout.strip() if completed.returncode == 0 else None


def provenance(input_path, output_dir):
    source_paths = [Path(__file__), ROOT / "htt/obsstat/r9_product_intake.py",
                    ROOT / "htt/htt/htt/infer/r7_desi_law.py",
                    ROOT / "htt/htt/htt/infer/r7_gaussian_law.py", ROOT / "htt/src/common/r7_contracts.py"]
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "matplotlib", "h5py")}
    command = [sys.executable, str(Path(__file__).resolve()), "--input", str(input_path),
               "--output-dir", str(output_dir)]
    return {"generated_utc": datetime.now(timezone.utc).isoformat(),
            "git_head": _git("rev-parse", "HEAD"),
            "git_status_porcelain": _git("status", "--porcelain=v1"),
            "source_sha256": {str(p.relative_to(ROOT)): _sha256(p) for p in source_paths},
            "environment": {"python": platform.python_version(), "executable": sys.executable,
                            "platform": platform.platform(), "packages": versions},
            "cwd": str(Path.cwd()), "command": shlex.join(command)}


def _plot(result, curve, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    m = result["measurement"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), sharey=True)
    for ax, key, label, center in ((axes[0], "qiso", r"Predicted $q_{\rm iso}$", m["qiso"]),
                                  (axes[1], "DV_over_rd", r"Predicted $D_V/r_d$", m["DV_over_rd"])):
        for interval, color, text in ((result["conditional_intervals"][1], "#dceaf4", "95% conditional interval"),
                                     (result["conditional_intervals"][0], "#9cc8df", "68.27% conditional interval")):
            ax.axvspan(*interval[key], color=color, label=text)
        ax.plot(curve[key + "_prediction"], curve["relative_likelihood"], color="#173c55", lw=2,
                label="Relative likelihood")
        ax.axvline(center, color="#be5e38", ls="--", lw=1.25, label="Released central value")
        ax.set(xlabel=label, ylim=(0, 1.05))
        ax.grid(axis="y", alpha=.2)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel(r"Relative likelihood $L/L_{\max}$")
    axes[0].legend(loc="upper left", fontsize=8, frameon=False)
    axes[0].set_title(f"qiso = {m['qiso']:.6f} ± {m['qiso_sigma']:.6f}", fontsize=11)
    axes[1].set_title(f"D_V/r_d = {m['DV_over_rd']:.5f} ± {m['DV_over_rd_sigma']:.5f}", fontsize=11)
    fig.suptitle(f"DESI DR1 BGS Bright: released scalar BAO summary (z_eff = {m['zeff']:.5f})", fontsize=13)
    fig.text(.5, .135, "Both panels use the same observation. Fixed released Gaussian covariance; syst alternative only.",
             ha="center", fontsize=8)
    fig.text(.5, .105, "Owner: htt | C1 | Released-summary re-expression | Transfer: none | Null mocks: not run", ha="center", fontsize=8)
    fig.text(.5, .075, "Use: scalar conditional likelihood. No posterior/evidence, catalogue coverage, angular response, or tilt/Bianchi detection.",
             ha="center", fontsize=8)
    fig.text(.5, .045, f"Input SHA256: {result['source']['source_sha256']}", ha="center", fontsize=7)
    fig.subplots_adjust(left=.08, right=.98, top=.81, bottom=.26, wspace=.13)
    for suffix in ("png", "pdf"):
        fig.savefig(output_dir / f"desi_bao_summary.{suffix}", dpi=200)
    plt.close(fig)


def _report(result):
    m, s, p = result["measurement"], result["source"], result["provenance"]
    lines = ["# DESI DR1 BGS Bright: retained scalar BAO summary", "",
             f"At z_eff = {m['zeff']:.9f}, the released summary gives **D_V/r_d = {m['DV_over_rd']:.6f} ± {m['DV_over_rd_sigma']:.6f}** (one standard deviation).",
             f"The corresponding qiso is {m['qiso']:.9f} ± {m['qiso_sigma']:.9f}. All quantities are dimensionless.", "",
             "This is a re-expression of the retained BGS Bright v1.2 syst likelihood using its fixed Gaussian covariance.",
             "D_V/r_d = qiso × (D_V/r_d)_fid and sigma_D = sigma_q × (D_V/r_d)_fid; the released fiducial ratio is " + f"{m['DV_over_rd_fid']:.9f}.", "",
             "| Pointwise conditional coverage | qiso interval | D_V/r_d interval |",
             "|---|---|---|"]
    for interval in result["conditional_intervals"]:
        lines.append(f"| {100 * interval['coverage']:.6f}% | [{interval['qiso'][0]:.9f}, {interval['qiso'][1]:.9f}] | [{interval['DV_over_rd'][0]:.6f}, {interval['DV_over_rd'][1]:.6f}] |")
    lines += ["", "The intervals invert the scalar Gaussian acceptance rule and intersect with the positive prediction domain; a zero lower endpoint is open.",
              "They are pointwise confidence summaries conditional on the released approximation, not posterior credible intervals or simultaneous family coverage.",
              "The historical R9 alpha=1/80 and family allocation remain unchanged; that campaign was not rerun.", "",
              "![Two views of the same scalar likelihood](desi_bao_summary.png)", "",
              "The figure holds the observed datum fixed and varies the prediction. Its ordinate is L/L_max, with peak 1; the curve is not a probability density over predictions.",
              "The CSV also retains normalized log sampling densities in the observed qiso and observed D_V/r_d coordinates.",
              "Changing the observed variable gives p_D(D_obs | q_pred) = p_q(D_obs/fid | q_pred)/fid. Changing only the prediction coordinate introduces no Jacobian; relative likelihood is identical in both panels.", "",
              "| Artifact field | Value |", "|---|---|",
              *[f"| {key} | {result[key]} |" for key in ("owner", "claim_tier", "status", "artifact_mode", "allowed_use", "transfer_source", "null_mock_status", "covariance_status")],
              "| Forbidden uses | " + "; ".join(result["forbidden_uses"]) + " |", "",
              *[f"- {item}" for item in result["caveats"]], "", "## Source and execution", "",
              f"- Input: `{s['source_path']}`", f"- Source ID: `{s['source_id']}`",
              f"- SHA256: `{s['source_sha256']}`; bytes: {s['source_bytes']}",
              f"- Git HEAD: `{p['git_head']}`; exact active source hashes and worktree status are in `analysis.json`.",
              f"- Python: {p['environment']['python']}; executable: `{p['environment']['executable']}`.",
              f"- Package versions: `{json.dumps(p['environment']['packages'], sort_keys=True)}`.",
              "- Existing intake and Gaussian law are reused; the immutable source is never modified.", "",
              "```sh", p["command"], "```", "", "Outputs: [analysis.json](analysis.json), [likelihood_curve.csv](likelihood_curve.csv), [PNG](desi_bao_summary.png), [PDF](desi_bao_summary.pdf).", ""]
    return "\n".join(lines)


def run(input_path, output_dir):
    input_path, output_dir = Path(input_path).resolve(), Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError("output directory already exists; choose a new run-specific directory")
    result, curve = analyze_payload(read_desi_qiso(input_path))
    result["provenance"] = provenance(input_path, output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    with (output_dir / "likelihood_curve.csv").open("x", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(curve)
        writer.writerows(zip(*curve.values()))
    _plot(result, curve, output_dir)
    (output_dir / "analysis.md").write_text(_report(result), encoding="utf-8")
    result["output_sha256"] = {name: _sha256(output_dir / name) for name in
                               ("likelihood_curve.csv", "desi_bao_summary.png", "desi_bao_summary.pdf", "analysis.md")}
    with (output_dir / "analysis.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run(args.input, args.output_dir)
    except (ValueError, OSError, ImportError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": "COMPLETE_CONDITIONAL_RELEASE_SUMMARY", "output_dir": str(args.output_dir.resolve()),
                      "measurement": result["measurement"]}, allow_nan=False))


if __name__ == "__main__":
    main()
