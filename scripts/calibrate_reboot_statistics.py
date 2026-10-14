#!/usr/bin/env python3
"""Fixed-budget, joint-null Monte Carlo ranks for predeclared observed features.

CLI input: NPZ arrays `observed` (d,), `null` (B,d), and optional `training`
(n,d), plus a JSON declaration. See ../README.md and demo/declaration.json.
No covariance inverse, fitted-null bootstrap, adaptive stopping or Planck provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import resource
import sys
import time
import textwrap
from pathlib import Path

import numpy as np
from scipy import stats
from common.finite_null_ranking import pooled_rank_p

VERSION = "1.0.0"


def finite_array(value, ndim, name):
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != ndim or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a finite {ndim}-dimensional array")
    return a


def null_tail_interval(k, B, confidence=0.95):
    """Marginal exact CP interval for q, conditional on fixed threshold/training.

    Requires IID Bernoulli exceedances. It is NOT an interval for the realized
    discrete p_rank. Shared-sky feature dependence within rows is allowed.
    """
    if isinstance(B, bool) or not isinstance(B, (int, np.integer)) or B < 1:
        raise ValueError("B must be a positive integer")
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or not 0 <= k <= B:
        raise ValueError("k must be an integer in [0,B]")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0,1)")
    a = (1 - confidence) / 2
    return [0.0 if k == 0 else float(stats.beta.ppf(a, k, B-k+1)),
            1.0 if k == B else float(stats.beta.ppf(1-a, k+1, B-k))]


def conservative_rank(observed_score, null_scores, confidence=0.95):
    """High scores are extreme; ties counted in null exceedance k."""
    scores = finite_array(null_scores, 1, "null_scores")
    if scores.size < 1 or not math.isfinite(float(observed_score)):
        raise ValueError("need finite observed score and nonempty null scores")
    B = scores.size
    k = int(np.count_nonzero(scores >= observed_score))
    exact_p = pooled_rank_p(float(observed_score), scores.tolist(), tie_policy="conservative_ge")
    return {"observed_score": float(observed_score), "B": int(B), "k_ge": k,
            "ties": int(np.count_nonzero(scores == observed_score)),
            "p_rank": float(exact_p), "p_rank_exact": str(exact_p), "q_hat": k/B,
            "q_interval": null_tail_interval(k, int(B), confidence)}


def _ids(value, length, name):
    if (not isinstance(value, list) or len(value) != length or
        any(not isinstance(x, str) or not x.strip() for x in value)):
        raise ValueError(f"{name} must contain {length} nonempty realization IDs")
    if len(set(value)) != length:
        raise ValueError(f"{name}: duplicate latent sky realization (same-sky pseudo-replication)")
    return set(value)


def validate_declaration(meta, observed, null, training):
    """Validate mechanics/provenance declarations, not the actual null physics."""
    if not isinstance(meta, dict):
        raise ValueError("metadata must be a JSON object")
    B, d = null.shape
    if d < 1 or observed.shape != (d,) or B < 1:
        raise ValueError("observed shape (d,) and nonempty joint null shape (B,d) required")
    if type(meta.get("fixed_B")) is not int or meta["fixed_B"] != B:
        raise ValueError("fixed_B must be declared in advance and match all null rows")
    for key in ("fixed_budget_before_scores", "statistics_predeclared",
                "joint_row_generation", "observed_exchangeable_under_null"):
        if meta.get(key) is not True:
            raise ValueError(f"required attestation {key}=true")
    for key in ("declaration_id", "null_model_id", "observed_realization_id",
                "observation_pipeline", "null_pipeline"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ValueError(f"missing {key}")
    if meta.get("null_draw_law") != "iid_joint_vectors":
        raise ValueError("this CLI requires IID joint-null vectors for binomial q intervals")
    if meta.get("independence_unit") != "latent_sky_realization":
        raise ValueError("independence_unit must be latent_sky_realization, never map product")
    if meta["observation_pipeline"] != meta["null_pipeline"]:
        raise ValueError("observation/null feature pipelines must match")
    null_ids = _ids(meta.get("null_realization_ids"), B, "null_realization_ids")
    obs_id = meta["observed_realization_id"]
    if obs_id in null_ids:
        raise ValueError("observation reused as a null sky realization")
    specs = meta.get("statistics")
    if not isinstance(specs, list) or len(specs) != d:
        raise ValueError("one predeclared statistic specification per feature is required")
    names = [s.get("name") if isinstance(s, dict) else None for s in specs]
    if any(not isinstance(s, str) or not s.strip() for s in names) or len(set(names)) != d:
        raise ValueError("statistic names must be distinct nonempty strings")
    if any(s.get("tail") not in ("upper", "lower", "two-sided") for s in specs):
        raise ValueError("tails must be predeclared upper/lower/two-sided")
    transform = meta.get("transformation")
    if transform not in ("fixed_affine", "independent_training_z"):
        raise ValueError("transformation must be fixed_affine or independent_training_z")
    if transform == "independent_training_z":
        if training is None or training.ndim != 2 or training.shape[1] != d or len(training) < 2:
            raise ValueError("independent training matrix with n>=2 and matching d required")
        if meta.get("training_independent_of_observed_and_calibration") is not True:
            raise ValueError("independent training attestation required")
        if meta.get("training_pipeline") != meta["null_pipeline"]:
            raise ValueError("training pipeline must match")
        train_ids = _ids(meta.get("training_realization_ids"), len(training), "training_realization_ids")
        if train_ids & (null_ids | {obs_id}):
            raise ValueError("training/calibration/observation realization IDs overlap")
        if any("center" in s or "scale" in s for s in specs):
            raise ValueError("training transform cannot also supply fixed center/scale")
    elif training is not None:
        raise ValueError("unused training matrix: choose independent_training_z or remove it")


def score_features(observed, null, meta, training=None):
    d = len(observed)
    if meta["transformation"] == "independent_training_z":
        centers, scales = training.mean(axis=0), training.std(axis=0, ddof=1)
        floor = 64*np.finfo(float).eps*np.max(np.abs(training), axis=0)
        if (not np.isfinite(centers).all() or not np.isfinite(scales).all() or
            np.any(scales <= floor)):
            raise ValueError("training scale constant or numerically unresolved; no ridge/inverse fallback")
    else:
        centers = finite_array([s.get("center", 0.0) for s in meta["statistics"]], 1, "centers")
        scales = finite_array([s.get("scale", 1.0) for s in meta["statistics"]], 1, "scales")
        if np.any(scales <= 0):
            raise ValueError("fixed scales must be positive")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        signed_obs, signed_null = (observed-centers)/scales, (null-centers)/scales
    if not np.isfinite(signed_obs).all() or not np.isfinite(signed_null).all():
        raise ValueError("affine transform overflow or nonfinite score")
    score_obs, score_null = signed_obs.copy(), signed_null.copy()
    for j in range(d):
        tail = meta["statistics"][j]["tail"]
        if tail == "lower":
            score_obs[j], score_null[:,j] = -score_obs[j], -score_null[:,j]
        elif tail == "two-sided":
            score_obs[j], score_null[:,j] = abs(score_obs[j]), abs(score_null[:,j])
    return score_obs, score_null, {"method": meta["transformation"],
        "center": centers.tolist(), "scale": scales.tolist(),
        "signed_observed": signed_obs.tolist(), "covariance_inverse_used": False}


def calibrate(observed, null, meta, training=None, alpha=0.05, confidence=0.95):
    if not 0 < alpha < 1 or not 0 < confidence < 1:
        raise ValueError("alpha and confidence must be in (0,1)")
    observed, null = finite_array(observed, 1, "observed"), finite_array(null, 2, "null")
    training = None if training is None else finite_array(training, 2, "training")
    validate_declaration(meta, observed, null, training)
    so, sn, transform = score_features(observed, null, meta, training)
    joint_max = sn.max(axis=1)
    global_result = conservative_rank(so.max(), joint_max, confidence)
    features = []
    for j, s in enumerate(meta["statistics"]):
        features.append({"name": s["name"], "tail": s["tail"],
            "observed_feature": float(observed[j]),
            "signed_transformed_observed": transform["signed_observed"][j],
            "unadjusted": conservative_rank(so[j], sn[:,j], confidence),
            "joint_max_adjusted": conservative_rank(so[j], joint_max, confidence)})
    return {"schema": "htt.reboot.joint-calibration/1", "version": VERSION,
        "analysis_label": meta.get("analysis_label", "UNSPECIFIED"),
        "provenance_status": "DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "declaration": meta, "transformation": transform,
        "alpha": alpha, "confidence": confidence, "fixed_B": len(null),
        "p_rank_resolution": 1/(len(null)+1), "rejection_attainable": alpha >= 1/(len(null)+1),
        "global_joint_null": global_result,
        "global_reject_at_alpha": global_result["p_rank"] <= alpha,
        "features": features,
        "interpretation": {
            "rank": "Conservative finite Monte Carlo p under declared exchangeability conditional on independent training; ties use >=.",
            "interval": "Marginal Clopper-Pearson interval for IID null exceedance probability q conditional on fixed observed threshold and training. Not an interval for realized p_rank; not simultaneous across features.",
            "multiplicity": "Global max-score test and single-step adjusted ranks control error under the complete joint null. Strong FWER under partial alternatives needs extra conditions, not asserted.",
            "physical_scope": "Observed feature calibration; no inferred shear, global tilt, Bianchi family detection, posterior or evidence."}}


def plot_result(result, observed, null, training, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    so, sn, _ = score_features(observed, null, result["declaration"], training)
    fig, ax = plt.subplots(figsize=(7.5,4.5), constrained_layout=True)
    ax.hist(sn.max(axis=1), bins=35, color="#4477aa", alpha=0.85,
            label=f"Joint null maxima (B={len(sn)})")
    ax.axvline(so.max(), color="#cc3311", lw=2,
               label=f"Observed maximum; p_rank={result['global_joint_null']['p_rank']:.4g}")
    ax.set(xlabel="Predeclared transformed maximum score", ylabel="Joint-null realizations",
           title=textwrap.fill(result["analysis_label"], width=60))
    ax.legend(fontsize=9)
    for ext in ("png", "pdf"):
        fig.savefig(outdir/f"joint_null_maximum.{ext}", dpi=170)
    plt.close(fig)


def write_result(result, observed, null, training, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/"calibration.json").write_text(json.dumps(result, indent=2)+"\n")
    rows = [f"# {result['analysis_label']}", "", f"Fixed B={len(null)}; declaration `{result['declaration']['declaration_id']}`.", "",
            "| Feature | Tail | Signed value | p rank | Joint-max adjusted p | q interval (unadjusted) |",
            "|---|---|---:|---:|---:|---|" ]
    for f in result["features"]:
        lo, hi = f["unadjusted"]["q_interval"]
        rows.append(f"| {f['name']} | {f['tail']} | {f['signed_transformed_observed']:.6g} | {f['unadjusted']['p_rank']:.6g} | {f['joint_max_adjusted']['p_rank']:.6g} | [{lo:.6g}, {hi:.6g}] |")
    g = result["global_joint_null"]
    rows.extend(["", f"Global joint-null p_rank={g['p_rank']:.6g} ({g['k_ge']} >= exceedances, {g['ties']} ties).",
                 f"Global q interval={g['q_interval']} at confidence {result['confidence']}.", ""])
    rows.extend(result["interpretation"].values())
    rows.extend(["", "Provenance attestations are validated mechanically and have not been independently verified."])
    (outdir/"calibration.md").write_text("\n".join(rows)+"\n")
    plot_result(result, observed, null, training, outdir)


def demo(outdir, B=999, replicates=1000, seed=20261014):
    """Bounded conditional-null calibration campaign with shared channel dependence."""
    if B < 1 or replicates < 1:
        raise ValueError("positive fixed B and replicates required")
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    d, ntrain, rho = 4, 256, 0.75
    cov = (1-rho)*np.eye(d)+rho*np.ones((d,d))
    L = np.linalg.cholesky(cov)
    training = rng.normal(size=(ntrain,d)) @ L.T
    observed = rng.normal(size=d) @ L.T
    null = rng.normal(size=(B,d)) @ L.T
    meta = {"analysis_label": "SYNTHETIC Gaussian joint-null diagnostic; NOT Planck science",
        "declaration_id": f"synthetic-fixed-v1-seed-{seed}-B-{B}",
        "null_model_id": "zero-mean Gaussian d4 rho0.75, IID latent realizations",
        "fixed_B": B, "fixed_budget_before_scores": True, "statistics_predeclared": True,
        "joint_row_generation": True, "observed_exchangeable_under_null": True,
        "null_draw_law": "iid_joint_vectors", "independence_unit": "latent_sky_realization",
        "observed_realization_id": "demo-observed", "null_realization_ids": [f"demo-null-{i}" for i in range(B)],
        "observation_pipeline": "synthetic-Gaussian-d4-v1", "null_pipeline": "synthetic-Gaussian-d4-v1",
        "training_pipeline": "synthetic-Gaussian-d4-v1",
        "transformation": "independent_training_z", "training_independent_of_observed_and_calibration": True,
        "training_realization_ids": [f"demo-train-{i}" for i in range(ntrain)],
        "statistics": [{"name": f"synthetic_feature_{i}", "tail": tail} for i,tail in enumerate(("upper", "two-sided", "lower", "upper"))]}
    np.savez(outdir/"input.npz", observed=observed, null=null, training=training)
    (outdir/"declaration.json").write_text(json.dumps(meta, indent=2)+"\n")
    result = calibrate(observed, null, meta, training)
    write_result(result, observed, null, training, outdir)
    # One fixed independently learned transform, fresh observed/null draws per replicate.
    pglobal, pnaive = [], []
    for _ in range(replicates):
        pool = rng.normal(size=(B+1,d)) @ L.T
        so, sn, _ = score_features(pool[0], pool[1:], meta, training)
        pglobal.append(float(pooled_rank_p(float(so.max()),sn.max(axis=1).tolist())))
        pnaive.append(min(float(pooled_rank_p(float(so[j]),sn[:,j].tolist())) for j in range(d)))
    pglobal, pnaive = np.asarray(pglobal), np.asarray(pnaive)
    alpha = result["alpha"]
    k = int(np.count_nonzero(pglobal <= alpha))
    campaign = {"schema": "htt.reboot.synthetic-calibration-campaign/1",
        "label": "SYNTHETIC ONLY; no Planck significance or physical-family inference",
        "seed": seed, "B_fixed_per_replicate": B, "replicates_fixed": replicates,
        "feature_count": d, "within_row_covariance": cov.tolist(), "independent_training_count": ntrain,
        "alpha": alpha, "global_rejections": k, "global_rejection_frequency": k/replicates,
        "global_rejection_probability_CP_interval": null_tail_interval(k, replicates),
        "CP_target": "Type I rejection probability over fresh IID campaign replicates, conditional on this fixed training draw; not p_rank uncertainty",
        "continuous_rank_type_I_bound": math.floor(alpha*(B+1))/(B+1),
        "naive_min_unadjusted_rejection_frequency": float(np.mean(pnaive <= alpha)),
        "scientific_test": "Numerical diagnostic only; finite rank validity follows exchangeability rather than an empirical PASS threshold."}
    (outdir/"campaign.json").write_text(json.dumps(campaign, indent=2)+"\n")
    np.savetxt(outdir/"campaign_pvalues.csv", np.column_stack((pglobal,pnaive)),
               delimiter=",", header="global_max_p_rank,naive_selected_min_unadjusted_p_rank", comments="")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1,2,figsize=(10,4), constrained_layout=True)
    for p, label, color in ((pglobal,"Joint max rank","#4477aa"),(pnaive,"Selected minimum (unadjusted)","#cc3311")):
        sp = np.sort(p)
        axs[0].step(sp,np.arange(1,replicates+1)/replicates,where="post",label=label,color=color)
    axs[0].plot([0,1],[0,1],"k--",lw=1,label="Uniform reference")
    axs[0].set(xlabel="Rank / selected rank",ylabel="Empirical CDF",xlim=(0,1),ylim=(0,1))
    axs[0].legend(fontsize=8)
    freqs = [k/replicates,float(np.mean(pnaive<=alpha))]
    axs[1].bar(["Joint max","Selected min"],freqs,color=["#4477aa","#cc3311"])
    ci = np.asarray(campaign["global_rejection_probability_CP_interval"])
    axs[1].errorbar(0,freqs[0],yerr=[[freqs[0]-ci[0]],[ci[1]-freqs[0]]],fmt="none",color="k",capsize=4)
    axs[1].axhline(alpha,color="k",ls="--")
    axs[1].set(ylabel=f"Rejection frequency at alpha={alpha}",ylim=(0,max(.15,2*max(freqs))))
    fig.suptitle(f"SYNTHETIC correlated joint-null calibration; B={B}, repetitions={replicates}")
    for ext in ("png","pdf"):
        fig.savefig(outdir/f"synthetic_calibration_campaign.{ext}",dpi=170)
    plt.close(fig)
    return campaign


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="NPZ with observed/null[/training]")
    parser.add_argument("--metadata", type=Path, help="predeclared JSON with row provenance")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--B", type=int, default=999, help="synthetic fixed B only")
    parser.add_argument("--replicates", type=int, default=1000, help="synthetic fixed repetitions only")
    parser.add_argument("--seed", type=int, default=20261014)
    args = parser.parse_args(argv)
    start = time.perf_counter()
    try:
        if args.demo:
            if args.input or args.metadata or args.alpha != .05 or args.confidence != .95:
                raise ValueError("demo has fixed alpha=.05/confidence=.95; cannot combine with external input")
            result = demo(args.output_dir,args.B,args.replicates,args.seed)
            identities = {"input_sha256":file_sha256(args.output_dir/"input.npz"),
                          "declaration_sha256":file_sha256(args.output_dir/"declaration.json")}
        else:
            if not args.input or not args.metadata:
                raise ValueError("--input and --metadata required unless --demo")
            with np.load(args.input,allow_pickle=False) as data:
                if set(data.files) not in ({"observed","null"},{"observed","null","training"}):
                    raise ValueError("NPZ keys must be observed/null[/training]")
                observed,null = data["observed"],data["null"]
                training = data["training"] if "training" in data.files else None
            meta = json.loads(args.metadata.read_text())
            result = calibrate(observed,null,meta,training,args.alpha,args.confidence)
            write_result(result,observed,null,training,args.output_dir)
            identities = {"input_sha256":file_sha256(args.input),"declaration_sha256":file_sha256(args.metadata)}
        import scipy, matplotlib
        import common.finite_null_ranking as rank_core
        receipt = {"status":"EXECUTED","exit_code":0,"command":sys.argv,
            "elapsed_seconds":time.perf_counter()-start,"peak_rss_platform_units":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "peak_rss_units":"KiB on Linux; bytes on macOS", "python":sys.version,
            "platform":platform.platform(),"numpy":np.__version__,"scipy":scipy.__version__,"matplotlib":matplotlib.__version__,
            "requested_model":"INHERITED_PARENT","observed_model":"UNKNOWN",
            "requested_reasoning_effort":"INHERITED_PARENT","observed_reasoning_effort":"UNKNOWN",
            "source_sha256":file_sha256(__file__), "rank_core_sha256":file_sha256(rank_core.__file__), **identities}
        (args.output_dir/"execution_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
        print(json.dumps({"status":"EXECUTED","output_dir":str(args.output_dir),
                          "elapsed_seconds":receipt["elapsed_seconds"]}))
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        parser.exit(2,f"calibration error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
