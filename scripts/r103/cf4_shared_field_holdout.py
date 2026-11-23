"""Score released 6dFGSv marks when the radial-velocity field is shared across folds."""
import argparse
import json
from pathlib import Path

import numpy as np

from htt.infer.cf4_group_holdout import (
    build_group_clusters, fit_probit_with_hessian, group_kfold_indices,
    sixdf_match_ambiguity_policies,
)
from htt.infer.cf4_predictive_response import selected_probit_holdout
from scripts.r99 import cf4_source_law as r99
from scripts.r100 import cf4_upstream_and_kband as r100

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/research_program/observational_publication_20261015"


def run():
    t2 = r100.load_cf4_table2()
    six = r100.load_sixdf_pv()
    source_paths = {"cf4_table2": t2["path"], "sixdf_pv_table1": r100.SIXDF_PATH}
    h = {name: r100.sha256(path) for name, path in source_paths.items()}
    ref = json.loads((r100.OUT_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json").read_text())
    if h != {k: ref["inputs"][k]["sha256"] for k in h}:
        raise ValueError("source mismatch with the R100 catalogues")
    match = sixdf_match_ambiguity_policies(t2, six, arcsec=15., dv_kms=500.)
    inc = match["policies"]["unique_only_r101"]["included"]
    closest = match["closest_table2_indices"]
    mark = np.where(inc, six["delta_d"], np.nan)
    cz = six["cz_gal"]
    x = np.column_stack((np.ones(len(cz)), cz / 1e4 - 1.1, six["delta_d"], six["is_grouped"]))
    # The R102 working model uses a common radial speed (km/s) along each ray.
    field = np.array([-300., -100., 0., 100., 300.])
    sci, *_ = r100.old._load_r30_and_bridge()
    def mean_fields(redshift_kms):
        return np.array([r99.finite_shift(sci, redshift_kms/r100.C, np.arctanh(v/r100.C),
                                          "bolometric") / (5.*r100.MAG) for v in field])

    means = mean_fields(cz)
    # Springob et al. 2014 section 4.3 and Table 1 use group redshift when
    # available. Keep the actual crossmatch and inclusion design fixed while
    # testing this convention in the velocity-to-mark transfer alone.
    group_cz = np.where(six["is_grouped"], six["cz_group_raw"], cz)
    group_means = mean_fields(group_cz)
    reports = {}
    for key in ("pgc", "pgc1"):
        group = np.where(closest >= 0, t2[key][np.maximum(closest, 0)], -1)
        clusters = build_group_clusters(six["groupid_raw"], secondary_keys=group)
        records = []
        seen = np.zeros(len(mark), dtype=int)
        for fold, (itr, ite) in enumerate(group_kfold_indices(clusters, n_splits=5, seed=42)):
            if np.intersect1d(clusters[itr], clusters[ite]).size:
                raise RuntimeError("cluster leakage")
            seen[ite] += 1
            train = np.ones(len(mark), dtype=bool)
            train[ite] = False
            fit = fit_probit_with_hessian(x[itr], inc[itr])
            if not fit.converged:
                raise RuntimeError(f"selection fit failed for {key}, fold {fold}")
            b = fit.beta_hat
            intercept = b[0] + b[1]*x[:, 1] + b[3]*x[:, 3]
            out = selected_probit_holdout(
                mark, means, six["epsilon_d"], intercept, b[2], np.full(len(field), 0.2),
                included=inc, train=train)
            group_out = selected_probit_holdout(
                mark, group_means, six["epsilon_d"], intercept, b[2], np.full(len(field), 0.2),
                included=inc, train=train)
            records.append(dict(group_cz_shared_minus_zero=group_out["shared_minus_zero"],
                                group_cz_fresh_minus_zero=group_out["fresh_minus_zero"], fold=fold, n_test=len(ite), n_test_selected=int(inc[ite].sum()),
                                shared_minus_zero=out["shared_minus_zero"],
                                fresh_minus_zero=out["fresh_minus_zero"],
                                train_field_log_weights=out["train_field_log_weights"].tolist()))
        if not np.all(seen == 1):
            raise RuntimeError("heldout indices must partition the catalogue")
        reports[key] = dict(cv_group_cz_shared_minus_zero=sum(r["group_cz_shared_minus_zero"] for r in records),
                            cv_group_cz_fresh_minus_zero=sum(r["group_cz_fresh_minus_zero"] for r in records),
                            n_clusters=len(np.unique(clusters)), folds=records,
                            cv_shared_minus_zero=sum(r["shared_minus_zero"] for r in records),
                            cv_fresh_minus_zero=sum(r["fresh_minus_zero"] for r in records))
    # Compare against the exact inherited sample/fold implementation for both definitions.
    old_report = json.loads((DOC / "R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123" /
                             "CF4_SELECTION_HOLDOUT_RESULTS.json").read_text())
    reference = old_report["part1_sixdf_holdout_and_selection_uncertainty"]
    replay = {"pgc": reference["five_fold_group_cv"]["sum_heldout_plugin_mix_minus_zero"],
              "pgc1": reference["pgc1_linked_group_cv"]["sum_heldout_plugin_mix_minus_zero"]}
    for k, expected in replay.items():
        err = abs(reports[k]["cv_fresh_minus_zero"] - expected)
        reports[k]["r102_replay_abs_error"] = err
        if err > 1e-7:
            raise ArithmeticError(f"R102 fold baseline differs for {k}: {err}")
    return dict(schema="htt.r103.cf4_shared_field_holdout/1", source_sha256=h, n_parent=len(mark),
                n_selected=int(inc.sum()), n_group_cz_rows=int(six["is_grouped"].sum()),
                n_changed_cz_rows=int(np.sum(group_cz != cz)),
                field_kms=field.tolist(), link_policies=reports,
                score_scope="group-blocked CV log predictive score under a working Gaussian mark "
                            "and training-only plug-in probit; folds share training objects",
                source_qualification="BLOCKED_INPUT", physical_Pi=None, calibrated_p=None,
                physical_GF=None)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, help="write result JSON (otherwise stdout)")
    args = p.parse_args()
    result = json.dumps(run(), indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(result, end="")
    else:
        args.output.write_text(result)


if __name__ == "__main__":
    main()
