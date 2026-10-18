"""Fixed HI target-cohort genealogy and two-stage conditional selection diagnostics.

No CF4 parent selection probability or physical velocity covariance is inferred.
Only unambiguous input LEDA Vhel enters the regression. All targets are retained.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import json
import os
import sys

for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_key] = "2"
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PROGRAM = ROOT / "docs/research_program/observational_publication_20261015"
UPSTREAM_CODE = PROGRAM / "CONTINUATION_20261018/H02_UPSTREAM_SELECTION_20261018/upstream_selection.py"
spec = importlib.util.spec_from_file_location("prior_upstream", UPSTREAM_CODE)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
RAW = Path("/mnt/extdrive/workdir/htt_open_data/cf4/HI_646_A113")
EXTERNAL = RAW.parent / "D02_HI_CF4_20261018"
HI_SHA = {"ReadMe": "bb5e9748e2b35d0dbc3271eb739913c1998a024fd00c2457bdf45d03ab83b7a7",
          "table2.dat": "2e7e9f979aeb862ae59ac40b377953de7602c2574515b2c880c0b55cb838249c",
          "table4.dat": "88e453c7c559f663fa61782707e4b47fdc2b752dcfda84d5dccd0d9103c4b8a3"}
OUTCOMES = ("accepted", "other_quality", "confused", "nondetection")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outcome(error):
    if error == 500:
        return "nondetection"
    if error == 100:
        return "confused"
    if 0 < error <= 20:
        return "accepted"
    if 20 < error < 100:
        return "other_quality"
    raise ValueError("unclassified linewidth sentinel")


def load_inputs():
    blobs = {name: prior.sealed(RAW / name, digest) for name, digest in HI_SHA.items()}
    lines = blobs["table2.dat"].decode("ascii").splitlines()
    if len(lines) != 628 or any(len(line) != 63 for line in lines):
        raise ValueError("HI target count/width changed")
    targets = []
    for line in lines:
        targets.append({"pgc": int(line[:7]), "Vhel": int(line[19:24]),
                        "outcome": outcome(int(line[36:39])),
                        "incl_available": bool(line[52:57].strip()),
                        "Bmag_available": bool(line[58:63].strip().strip("-"))})
    if len({r["pgc"] for r in targets}) != 628:
        raise ValueError("nonunique HI target identity")
    fourth = blobs["table4.dat"].decode("ascii").splitlines()
    if len(fourth) != 1274 or any(len(line) != 32 for line in fourth):
        raise ValueError("HI contributor count/width changed")
    gbt = {int(line[:7]) for line in fourth if line[8:14].strip() == "GBT"}
    if gbt != {r["pgc"] for r in targets if r["outcome"] == "accepted"} or len(gbt) != 385:
        raise ValueError("GBT published membership mismatch")
    rd = prior.sealed(prior.UPSTREAM / "ReadMe", prior.UPSTREAM_SHA["ReadMe"]).decode("ascii")
    tf_data = prior.parse_rows(prior.sealed(prior.UPSTREAM / "table1.dat", prior.UPSTREAM_SHA["table1.dat"]),
                               prior.schema(rd, "table1.dat"), 10737, 499)
    tf_dist = prior.parse_rows(prior.sealed(prior.UPSTREAM / "table4.dat", prior.UPSTREAM_SHA["table4.dat"]),
                               prior.schema(rd, "table4.dat"), 9792, 100)
    old = json.loads((prior.PREVIOUS / "results/h02_actual_centers.json").read_text())
    crd = prior.sealed(prior.CF4 / "ReadMe", prior.CF4_README_SHA).decode("ascii")
    galaxy = prior.parse_rows(prior.sealed(prior.CF4 / "table2.dat", old["source_table_sha256"]["table2.dat"]),
                              prior.schema(crd, "table2.dat"), 55877, 190)
    gc = prior.schema(crd, "table3.dat")
    gc["PGC"] = gc.pop("1PGC")
    groups = prior.parse_rows(prior.sealed(prior.CF4 / "table3.dat", old["source_table_sha256"]["table3.dat"]), gc, 38053, 190)
    prior.sealed(prior.SOURCE, prior.SOURCE_SHA)
    with np.load(prior.SOURCE, allow_pickle=False) as npz:
        selected = set(map(int, npz["group_id"]))
    if len(selected) != 35970 or not selected.issubset(groups):
        raise ValueError("selected group identity changed")
    for row in targets:
        p = row["pgc"]
        row["TF2020_data"] = p in tf_data
        row["TF2020_distance_row"] = p in tf_dist
        row["TF2020_DMbest"] = p in tf_dist and tf_dist[p]["DMbest"] is not None
        row["TF_version_status"] = ("data_and_distance" if p in tf_data and p in tf_dist else
                                    "data_only" if p in tf_data else "distance_only" if p in tf_dist else "absent_both")
        row["CF4_galaxy"] = p in galaxy
        gid = galaxy[p]["1PGC"] if p in galaxy else None
        row["CF4_group"] = gid
        row["CF4_group_release"] = gid in groups
        row["CF4_selected_group"] = gid in selected
        row["CF4_registered_TF"] = p in galaxy and galaxy[p]["DMtf"] is not None
        row["CF4_status"] = ("not_in_CF4_galaxy" if p not in galaxy else
                               "group_absent_from_group_release" if gid not in groups else
                               "group_outside_selected" if gid not in selected else "selected_group")
        row["block"] = f"group:{gid}" if gid is not None else f"unresolved_pgc:{p}"
        row["fold"] = fold_for(row["block"])
        row["model_input_status"] = "AMBIGUOUS_SOURCE_VALUE" if row["Vhel"] == -1 else "UNAMBIGUOUS_INPUT_VHEL"
        row.update({"oof_detection": None, "oof_suitable_given_detection": None, "oof_suitable": None})
    source = {"HI": HI_SHA, "TF2020": prior.UPSTREAM_SHA,
              "CF4_ReadMe": prior.CF4_README_SHA, "CF4_tables": old["source_table_sha256"],
              "selected_npz": prior.SOURCE_SHA, "reused_parser": sha(UPSTREAM_CODE)}
    return targets, source


def fold_for(block):
    return int(hashlib.sha256(("D02-group-fold-v1:" + block).encode()).hexdigest()[:16], 16) % 5


def design(velocity):
    # Fixed physical scaling, no fitting or full-sample preprocessing.
    v = np.asarray(velocity, dtype=float)
    if not np.all(np.isfinite(v)):
        raise ValueError("nonfinite pretarget covariate")
    return np.column_stack([np.ones(len(v)), (v - 10000.) / 5000.])


def fit_logistic(x, y):
    """Slope-only fixed L2 penalty 1; intercept is unpenalized."""
    y = np.asarray(y, dtype=float)
    if len(y) == 0 or not 0 < y.sum() < len(y):
        raise ValueError("both endpoint classes required")
    def objective(beta):
        eta = x @ beta
        value = np.sum(np.logaddexp(0., eta) - y * eta) + .5 * beta[1] ** 2
        grad = x.T @ (expit(eta) - y) + np.array([0., beta[1]])
        return value, grad
    p = np.mean(y)
    result = minimize(objective, [np.log(p / (1 - p)), 0.], jac=True, method="BFGS", options={"gtol": 1e-7})
    if not result.success and np.max(np.abs(result.jac)) > 2e-5:
        raise RuntimeError(f"logistic optimization failed: {result.message}, gradient={result.jac}")
    return result.x


def metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.clip(p, 1e-12, 1 - 1e-12)
    npos = y.sum()
    auc = ((rankdata(p)[y == 1].sum() - npos * (npos + 1) / 2) / (npos * (len(y) - npos))
           if 0 < npos < len(y) else None)
    return {"n": len(y), "observed_fraction": float(y.mean()), "predicted_mean": float(p.mean()),
            "brier": float(np.mean((p - y) ** 2)),
            "log_loss": float(np.mean(np.logaddexp(0., np.log(p / (1 - p))) - y * np.log(p / (1 - p)))),
            "auc": None if auc is None else float(auc)}


def model(targets, n_boot=300):
    all_targets = targets
    targets = [r for r in all_targets if r["model_input_status"] == "UNAMBIGUOUS_INPUT_VHEL"]
    v = np.array([r["Vhel"] for r in targets])
    x = design(v)
    det = np.array([r["outcome"] != "nondetection" for r in targets])
    accept = np.array([r["outcome"] == "accepted" for r in targets])
    folds = np.array([r["fold"] for r in targets])
    blocks = np.array([r["block"] for r in targets])
    pd, pq, bd, bq = (np.zeros(len(targets)) for _ in range(4))
    fold_rows = []
    for fold in range(5):
        test, train = folds == fold, folds != fold
        if set(blocks[test]) & set(blocks[train]):
            raise ValueError("group holdout leakage")
        beta_d = fit_logistic(x[train], det[train])
        beta_q = fit_logistic(x[train & det], accept[train & det])
        pd[test], pq[test] = expit(x[test] @ beta_d), expit(x[test] @ beta_q)
        bd[test], bq[test] = det[train].mean(), accept[train & det].mean()
        fold_rows.append({"fold": fold, "test_targets": int(test.sum()), "test_blocks": len(set(blocks[test])),
                          "train_targets": int(train.sum()), "train_detected": int((train & det).sum()),
                          "test_detected": int((test & det).sum()), "test_accepted": int((test & accept).sum()),
                          "detection_beta": beta_d.tolist(), "quality_beta": beta_q.tolist()})
    endpoints = {"detection_inclusive_confusion": (np.ones(len(det), bool), det, pd, bd),
                 "suitable_given_detection": (det, accept, pq, bq),
                 "suitable_all_targets_two_stage": (np.ones(len(det), bool), accept, pd * pq, bd * bq)}
    result = {}
    unique = sorted(set(blocks))
    block_indices = {b: np.where(blocks == b)[0] for b in unique}
    rng = np.random.default_rng(2026101802)
    bootstrap = {name: defaultdict(list) for name in endpoints}
    coefficients = {"detection": [], "suitability_given_detection": []}
    bootstrap_failures = []
    for iteration in range(n_boot):
        sample = np.concatenate([block_indices[b] for b in rng.choice(unique, size=len(unique), replace=True)])
        for name, (mask, y, p, baseline) in endpoints.items():
            ix = sample[mask[sample]]
            m, base = metrics(y[ix], p[ix]), metrics(y[ix], baseline[ix])
            for key in ("observed_fraction", "brier", "log_loss", "auc"):
                if m[key] is not None:
                    bootstrap[name][key].append(m[key])
            bootstrap[name]["brier_minus_baseline"].append(m["brier"] - base["brier"])
        try:
            coefficients["detection"].append(fit_logistic(x[sample], det[sample]))
            good = sample[det[sample]]
            coefficients["suitability_given_detection"].append(fit_logistic(x[good], accept[good]))
        except (ValueError, RuntimeError) as exc:
            bootstrap_failures.append({"iteration": iteration, "error": str(exc)})
    for name, (mask, y, p, baseline) in endpoints.items():
        m = metrics(y[mask], p[mask])
        m["intercept_only_same_folds"] = metrics(y[mask], baseline[mask])
        m["cluster_bootstrap95_fixed_oof_predictions"] = {
            key: np.quantile(value, [.025, .975]).tolist() for key, value in bootstrap[name].items()}
        calibration = []
        for low, high in zip(np.arange(0., 1., .2), np.arange(.2, 1.01, .2)):
            cell = mask & (p >= low) & (p < high + (1e-10 if high > .99 else 0))
            if cell.any():
                calibration.append({"probability_bin": [float(low), float(high)], "n": int(cell.sum()),
                                    "successes": int(y[cell].sum()), "predicted_mean": float(p[cell].mean()),
                                    "observed_fraction": float(y[cell].mean())})
        m["heldout_calibration"] = calibration
        result[name] = m
    full = {}
    for name, mask, y in [("detection", np.ones(len(det), bool), det), ("suitability_given_detection", det, accept)]:
        beta = fit_logistic(x[mask], y[mask])
        full[name] = {"beta_intercept_at_10000_kms_and_slope_per5000_kms": beta.tolist(),
                      "bootstrap95_beta": np.quantile(coefficients[name], [.025, .975], axis=0).tolist(),
                      "odds_ratio_per5000_kms": float(np.exp(beta[1])),
                      "bootstrap95_odds_ratio": np.exp(np.quantile(np.asarray(coefficients[name])[:, 1], [.025, .975])).tolist()}
    for i, row in enumerate(targets):
        row.update({"oof_detection": float(pd[i]), "oof_suitable_given_detection": float(pq[i]),
                    "oof_suitable": float(pd[i] * pq[i])})
    prediction_bounds = {key: [sum(r[key] for r in targets) / len(all_targets),
                               (sum(r[key] for r in targets) + len(all_targets) - len(targets)) / len(all_targets)]
                         for key in ("oof_detection", "oof_suitable")}
    return {"heldout": result, "full_fit": full, "folds": fold_rows,
            "model_domain": {"all_retained_targets": len(all_targets), "scored_targets": len(targets),
                             "unscored_targets": len(all_targets) - len(targets),
                             "unscored_prediction_status": "UNKNOWN; sole source Vhel=-1 is ambiguous, not an asserted official sentinel",
                             "undefined_prediction_mass": (len(all_targets) - len(targets)) / len(all_targets),
                             "628_target_mean_prediction_bounds_missing_in_0_1": prediction_bounds},
            "bootstrap_replicates": n_boot, "bootstrap_failures": bootstrap_failures,
            "predictor": "Unambiguous input LEDA Vhel only (627 scored,1 ambiguous unscored); design=[1,(Vhel-10000)/5000], km/s",
            "penalty": "fixed slope-only L2=1; no tuning; intercept unpenalized",
            "probability_rule": "P(suitable|Vhel,targeted)=P(non500|Vhel,targeted)*P(suitable|non500,Vhel,targeted)",
            "validation": "5 deterministic SHA256 whole-known-group folds; unresolved PGCs use unique-target blocks",
            "uncertainty": "300 seeded whole-block resamples; coefficients refitted, OOF score intervals condition on fitted crossvalidation predictions; exchangeable blocks assumed",
            "limitations": ["Unresolved PGC blocks may have unobserved shared groups; no independence proof.",
                            "Released TF/CF4 distances share calibrations; not used as independent outcomes or predictors.",
                            "No physical peculiar velocity covariance estimated."]}


def summarize(targets):
    result = {}
    for name in ("all_targets",) + OUTCOMES:
        rows = targets if name == "all_targets" else [r for r in targets if r["outcome"] == name]
        known = [r for r in rows if r["CF4_group"] is not None]
        counts = Counter(r["CF4_group"] for r in known)
        result[name] = {"targets": len(rows), "TF2020_version_status": dict(Counter(r["TF_version_status"] for r in rows)),
                        "TF2020_DMbest": sum(r["TF2020_DMbest"] for r in rows),
                        "CF4_status": dict(Counter(r["CF4_status"] for r in rows)),
                        "CF4_registered_TF": sum(r["CF4_registered_TF"] for r in rows),
                        "known_groups": len(counts), "selected_groups": len({r["CF4_group"] for r in rows if r["CF4_selected_group"]}),
                        "groups_with_multiple_targets": sum(n > 1 for n in counts.values()),
                        "velocity_quantiles_0_25_50_75_100_kms": np.quantile([r["Vhel"] for r in rows], [0, .25, .5, .75, 1]).tolist(),
                        "incl_available": sum(r["incl_available"] for r in rows), "Bmag_available": sum(r["Bmag_available"] for r in rows)}
    route_counts = Counter((r["outcome"], r["TF_version_status"], r["CF4_status"], r["CF4_registered_TF"]) for r in targets)
    result["full_route_counts"] = [{"outcome": a, "TF2020_version_status": b, "CF4_status": c,
                                     "CF4_registered_TF": d, "count": n} for (a,b,c,d),n in sorted(route_counts.items())]
    supports = {name: {r["CF4_group"] for r in targets if r["outcome"] == name and r["CF4_selected_group"]} for name in OUTCOMES}
    result["selected_group_outcome_overlap"] = {a: {b: len(supports[a] & supports[b]) for b in OUTCOMES} for a in OUTCOMES}
    result["holdout_blocks"] = len({r["block"] for r in targets})
    return result


def plot(targets):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    targets = [r for r in targets if r["model_input_status"] == "UNAMBIGUOUS_INPUT_VHEL"]
    edges = np.quantile([r["Vhel"] for r in targets], np.linspace(0, 1, 6))
    for outcome_name, color in [("accepted", "#176c87"), ("nondetection", "#a34d48")]:
        centers, fractions = [], []
        for i in range(5):
            rows = [r for r in targets if edges[i] <= r["Vhel"] <= edges[i+1] and (i == 4 or r["Vhel"] < edges[i+1])]
            centers.append(np.mean([r["Vhel"] for r in rows]))
            fractions.append(np.mean([r["outcome"] == outcome_name for r in rows]))
        axes[0].plot(centers, fractions, "o-", label=outcome_name, color=color)
    axes[0].set(xlabel="Input LEDA heliocentric velocity (km/s)", ylabel="Observed fraction in target-velocity quintile", ylim=(0, 1))
    axes[0].legend()
    for key, endpoint, color in [("oof_detection", "non500", "#8a6e2c"), ("oof_suitable", "suitable", "#176c87")]:
        x, y = [], []
        for low in np.arange(0, 1, .2):
            rows = [r for r in targets if low <= r[key] < low + .2 + (1e-10 if low > .79 else 0)]
            if rows:
                x.append(np.mean([r[key] for r in rows]))
                y.append(np.mean([r["outcome"] != "nondetection" if endpoint == "non500" else r["outcome"] == "accepted" for r in rows]))
        axes[1].plot(x, y, "o-", label=endpoint, color=color)
    axes[1].plot([0, 1], [0, 1], ":", color="gray")
    axes[1].set(xlabel="Whole-group heldout predicted probability", ylabel="Observed fraction (fixed probability bins)", xlim=(0, 1), ylim=(0, 1))
    axes[1].legend()
    fig.suptitle("628 GBT targets retained; 627 with unambiguous input velocity scored")
    fig.text(.02, .015, "HTT | DIAGNOSTIC_ONLY | transfer:none | no physical covariance/null | missing prediction mass 1/628", fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, .94))
    for extension in ("png", "pdf"):
        fig.savefig(HERE / f"D02_COHORT.{extension}", dpi=170)
    plt.close(fig)


def run():
    targets, sources = load_inputs()
    result = {"schema": "htt.d02_hi_cf4/1", "owner": "htt", "claim_tier": "DIAGNOSTIC_ONLY",
              "artifact_mode": "exploratory_actual_data", "allowed_use": "628-target-conditioned selection and release genealogy diagnostics",
              "scope": "J/A+A/646/A113 628 GBT targets, TF2020 and CF4 release identity joins",
              "transfer_source": "none", "null_status": "not a cosmological null test", "covariance_status": "block resampling working assumption, no physical covariance",
              "forbidden_uses": ["CF4 parent detection/targeting probability", "independent released calibration", "physical anisotropy admission"],
              "source_identities": sources, "generator_sha256": sha(Path(__file__)),
              "counts_and_joins": summarize(targets), "model": model(targets),
              "runtime": {"requested": "gpt-6.1-sol/high", "observed": "UNKNOWN", "python": sys.version,
                          "numpy": np.__version__, "BLAS_OMP_MKL_threads": 2},
              "prior_acceptance": "Original42 acceptances and H02/S02/K04 HOLD unchanged",
              "source_probe_failures": ["web A&A 403 and CDS inaccessible", "requests module unavailable; no dependency installed", "stdlib A&A article 403; primary CDS ReadMe successfully acquired by parent"],
              "caveats": ["2021 HI and 2020 TF source memberships are different releases; absence is not inferred rejection.",
                          "PGC identity only, no alias guesses; group membership does not prove unchanged measurement ingestion.",
                          "Detection means e_W50!=500 and includes29confused spectra; it is not secure target-specific HI detection.",
                          "Vhel is input LEDA velocity; all observed linewidth, error/sentinel, v50, S/N and flux excluded from predictors.",
                          "Inclination and B magnitude are nullable and excluded; unrecorded target covariates/selection remain unavailable.",
                          "Sole input Vhel=-1 is classified AMBIGUOUS_SOURCE_VALUE; no v50 substitution;627model-scored and1prediction UNKNOWN. First raw-value model retained as sensitivity.",
                          "No conditional target-cohort model identifies global CF4 parent probability."]}
    EXTERNAL.mkdir(exist_ok=True)
    csv_path = EXTERNAL / "TARGET_JOIN_AND_OOF.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(targets[0]))
        writer.writeheader()
        writer.writerows(targets)
    result["external_all_target_ledger"] = {"path": str(csv_path), "sha256": sha(csv_path), "rows": len(targets)}
    (HERE / "D02_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    plot(targets)
    print(json.dumps({"counts": result["counts_and_joins"]["all_targets"], "model_domain": result["model"]["model_domain"],
                      "heldout": result["model"]["heldout"], "full_fit": result["model"]["full_fit"]}, indent=2))
    return result


if __name__ == "__main__":
    run()
