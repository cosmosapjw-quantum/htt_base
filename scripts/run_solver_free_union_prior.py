#!/usr/bin/env python3
"""Conditional Union3 Gaussian node-prior sensitivity; no ODE or solver.

Run with the frozen checkout's existing interpreter and --repo-root. This is
NOT a certified Union3 likelihood correction: release-generator binding is
unresolved. See explanation.md for the public-code/paper conflict.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.stats import multivariate_normal

EXPECTED_HEAD = "89621f4c9a6f63449813587a0fadeb13287f8e10"
EXPECTED_FITTER_SHA = "26cfce541d47fce302c609ca3bdf2b3032c61c1d06aabb99232514ef70638138"
METADATA = dict(owner="HTT", claim_tier="CONDITIONAL_DIAGNOSTIC",
    artifact_mode="ASSUMED_NODE_PRIOR_SENSITIVITY", allowed_use="Assess the blocker under the declared Gaussian assumption",
    transfer_source="NONE_DISTANCE_ONLY", null_status="NOT_EVALUATED",
    covariance_status="FROZEN_RELEASE_PRECISION_WITH_ASSUMED_LAMBDA_I_REMOVAL_RHO_0",
    forbidden_uses=["Certified Union3 likelihood correction", "Physical posterior promotion",
                    "Native Bianchi or family identification", "Cross-scenario model evidence"])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def transform(mu, precision, reference, lam):
    """p_lambda = p_Gaussian / N(reference,I)**lambda, up to constant."""
    if not np.isfinite(lam) or not 0 <= lam <= 1:
        raise ValueError("lambda must be finite in [0,1]")
    if any(np.iscomplexobj(v) for v in (mu, precision, reference, lam)):
        raise ValueError("real Gaussian parameters required")
    mu, reference = np.asarray(mu, float), np.asarray(reference, float)
    p = np.asarray(precision, float)
    if mu.ndim != 1 or not mu.size or p.shape != (mu.size, mu.size) or reference.shape != mu.shape:
        raise ValueError("ordered node arrays required")
    if not all(np.isfinite(v).all() for v in (mu, reference, p)):
        raise ValueError("finite arrays required")
    if not np.allclose(p, p.T, rtol=0, atol=1e-12):
        raise ValueError("symmetric precision required")
    pl = p - lam * np.eye(mu.size)
    factor = cho_factor(pl, lower=True)
    # Center first to avoid subtracting large absolute distance-modulus vectors.
    delta = mu - reference
    dl = cho_solve(factor, p @ delta)
    ml = reference + dl
    # q_original - lambda*log(prior) = q_transformed + additive_constant.
    constant = (-.5 * delta @ p @ delta + .5 * dl @ pl @ dl
                + .5 * (np.linalg.slogdet(p)[1] - np.linalg.slogdet(pl)[1])
                + lam * mu.size / 2 * np.log(2 * np.pi))
    return ml, pl, float(constant)


def identity_check(mu, precision, reference, lam, seed=140326):
    """Independent scipy logpdf check at random nodes and distant offsets."""
    ml, pl, constant = transform(mu, precision, reference, lam)
    rng = np.random.default_rng(seed)
    cov = np.linalg.inv(precision)
    points = np.vstack([rng.multivariate_normal(mu, cov, size=128),
                        mu, reference, reference + .5, reference - .5])
    original = multivariate_normal.logpdf(points, mean=mu, cov=cov)
    prior = multivariate_normal.logpdf(points, mean=reference, cov=np.eye(mu.size))
    transformed = multivariate_normal.logpdf(points, mean=ml, cov=np.linalg.inv(pl))
    residual = original - lam * prior - transformed - constant
    error = float(np.max(np.abs(residual)))
    tolerance = 1e-8
    if error >= tolerance:
        raise ArithmeticError(f"Gaussian division identity failed: {error}")
    return dict(method="Independent scipy.stats.multivariate_normal.logpdf",
                seed=seed, points=len(points), max_abs_logpdf_identity_error=error,
                additive_constant=constant, tolerance=tolerance, status="PASS")


def import_fitter(repo):
    source = repo / "scripts/fit_reboot_joint.py"
    if sha(source) != EXPECTED_FITTER_SHA:
        raise ValueError("frozen fitter source identity mismatch")
    sys.path.insert(0, str(source.parent))
    spec = importlib.util.spec_from_file_location("fit_reboot_joint", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_plot(result, arrays, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.8))
    for lam in (0., .5, 1.):
        key = f"lambda_{lam:.1f}"
        axes[0].plot(arrays["Omega_m"], arrays[key + "_om_density"], label=f"λ = {lam:g}")
        axes[1].plot(arrays["H0_rd"], arrays[key + "_ar_density"], label=f"λ = {lam:g}")
    axes[0].set(xlim=(.25, .5), xlabel="Ωm", ylabel="Conditional marginal density")
    axes[1].set(xlim=(8500, 11000), xlabel="H₀ rd (km/s)")
    axes[0].legend(frameon=False)
    fig.suptitle("Union3 assumed node-prior sensitivity + DESI qiso (ρ = 0)", fontsize=12)
    fig.text(.5, .035,
        "HTT · conditional diagnostic · assumed node-prior sensitivity · distance only\n"
        "Null: not evaluated · covariance: frozen P − λI · allowed: blocker sensitivity\n"
        "Forbidden: certified likelihood correction, physical/native claims, model evidence",
        ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .16, 1, .93))
    for ext in ("svg", "png"):
        fig.savefig(outdir / f"prior_sensitivity.{ext}", dpi=180)
    plt.close(fig)


def run(repo, outdir, orders=(128, 256)):
    if tuple(orders) != (128, 256):
        raise ValueError("this bounded study requires the frozen 128/256 comparison")
    f = import_fitter(repo)
    data = f.load_inputs()
    outdir.mkdir(parents=True, exist_ok=False)
    reference = (5*np.log10((1 + data["z"]) * f.radial([.3], data["z"])[0])
                 + 5*np.log10(f.C_LIGHT / 70.) + 25.)
    tables = {order: f.table(order, data) for order in orders}
    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", EXPECTED_HEAD, head], check=False).returncode:
        raise ValueError("source checkpoint is not an ancestor of this checkout")
    status = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True)
    result = dict(metadata=METADATA, status="SOURCE_BINDING_UNRESOLVED",
        generating_command=f"{sys.executable} {Path(__file__).resolve()} --repo-root {repo} --outdir {outdir}",
        runtime=dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                     numpy=np.__version__, requested_worker="gpt-6.1-sol/high", observed_worker="UNKNOWN"),
        source=dict(repo_head=head, repo_clean_before=(status == ""), fitter_sha256=sha(repo / "scripts/fit_reboot_joint.py"),
                    union_sha256=data["union_sha256"], desi_json_sha256=data["desi_sha256"],
                    desi_source_id=data["desi_source_id"], script_sha256=sha(__file__)),
        assumptions=dict(node_prior="Independent Normal(mu_ref_i,1 mag)",
          reference="flat LCDM Omega_m=.3 H0=70 km/s/Mpc; mu_ref=5log10[(1+z) radial(.3,z)]+5log10(c/70)+25",
          lambdas=[0., .5, 1.], rho=0., Omega_m_prior="Uniform(.01,.99)",
          H0_rd_prior="Uniform(5000,20000) km/s", M_prior="Normal(43,5) mag",
          M_integral="Analytic Gaussian marginal, same proper prior in all scenarios",
          radial="Fixed 96-point Gauss-Legendre quadrature; no ODE/solver"),
        release_code_conflict=dict(paper="Alex G. Kim 2024 arXiv:2412.14181v1 sections II/V and Eq.13",
          paper_claim="Released node Gaussian is a posterior with independent standard-normal perturbation prior",
          public_stan_commit="a141f8f6f72c46b653e4d324f2ecf9c5684bf15a",
          public_stan_date="2024-09-30",
          public_stan_sha256="ed156b739f7bffd208f1dec48ddbe7039b1c88c8ac85ee3703195ae4e5f23c2d",
          public_code="stan_code_fixed.txt lines 427-430: empty branch for cosmo_model in {2,6}; normal(0,1) only in else",
          binding="Public code has not been proved to generate the exact frozen FITS matrix",
          resolution="Neither prior removal nor no-removal is certified as the exact released likelihood"),
        released_precision_min_eigenvalue=float(np.linalg.eigvalsh(data["precision"])[0]),
        scenarios={})
    arrays = dict(Omega_m=tables[256]["om"], H0_rd=tables[256]["ar"])
    final_fits = {}
    for lam in (0., .5, 1.):
        key = f"lambda_{lam:.1f}"
        ml, pl, _ = transform(data["mu"], data["precision"], reference, lam)
        scenario = dict(data, mu=ml, precision=pl)
        fits = {order: f.fit_grid(scenario, tables[order], 0., m_prior=(43.,5.)) for order in orders}
        stats = {order: f.moments(fits[order], tables[order]) for order in orders}
        comparison = f.convergence(stats[128], stats[256])
        converged = all(v < 1e-3 for metric in comparison.values() for v in metric.values())
        logz_delta = abs(fits[128]["log_evidence"] - fits[256]["log_evidence"])
        result["scenarios"][key] = dict(lam=lam, precision_min_eigenvalue=float(np.linalg.eigvalsh(pl)[0]),
            node_mean_max_abs_change_mag=float(np.max(np.abs(ml-data["mu"]))),
            identity=identity_check(data["mu"], data["precision"], reference, lam),
            moments_by_order={str(k):v for k,v in stats.items()}, convergence_128_256=comparison,
            quadrature_status="PASS" if converged else "UNRESOLVED",
            normalized_scenario_log_integral=fits[256]["log_evidence"], log_integral_128_256_abs_delta=logz_delta)
        final_fits[key] = fits[256]
        arrays[key + "_om_density"] = fits[256]["weights"].sum(axis=1) / (tables[256]["prior_w"]*.98)
        arrays[key + "_ar_density"] = fits[256]["weights"].sum(axis=0) / (tables[256]["prior_w"]*15000.)
    base = result["scenarios"]["lambda_0.0"]["moments_by_order"]["256"]
    for key, row in result["scenarios"].items():
        row["relative_to_lambda_0"] = {}
        for param in ("Omega_m", "H0_rd", "M"):
            current, previous = row["moments_by_order"]["256"][param], base[param]
            row["relative_to_lambda_0"][param] = dict(mean_shift=current["mean"]-previous["mean"],
                mean_shift_over_baseline_sd=(current["mean"]-previous["mean"])/previous["sd"],
                posterior_sd_ratio=current["sd"]/previous["sd"])
        row["joint_grid_total_variation_from_lambda_0"] = float(.5*np.abs(final_fits[key]["weights"]-final_fits["lambda_0.0"]["weights"]).sum())
    result["numerical_status"] = "PASS" if all(row["quadrature_status"]=="PASS" for row in result["scenarios"].values()) else "UNRESOLVED"
    result["physical_posterior_promotion"] = "BLOCKED_SOURCE_BINDING"
    result["normalizer_interpretation"] = "Integral of each normalized Gaussian scenario; not calibrated original-data evidence, no Bayes-factor comparison"
    np.savez_compressed(outdir / "marginals.npz", **arrays)
    render_plot(result, arrays, outdir)
    result["output_sha256"] = {name:sha(outdir/name) for name in ("marginals.npz","prior_sensitivity.svg","prior_sensitivity.png")}
    result["source"]["repo_clean_after"] = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True) == ""
    (outdir / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"numerical_status":result["numerical_status"],"output":str(outdir)}), flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()
    run(args.repo_root.resolve(), args.outdir.resolve())
