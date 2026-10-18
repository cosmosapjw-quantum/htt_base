"""Actual selected CF4 centers, coupled-window working errors and overlap diagnostics.

No physical likelihood, empirical calibration covariance or velocity is inferred.
Only aggregate sufficient statistics are exported; source rows stay local.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent / "P3"))
from calibration_frontier import critical_value, compatible_interval

OLD = ROOT / "docs/research_program/observational_publication_20261015/H02_L03_20261017/src/h02_calibration_fisher.py"
spec = importlib.util.spec_from_file_location("h02_original_geometry", OLD)
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)

SOURCE = ROOT / "docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz"
RAW = Path("/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94")
RAW_SHA = {"table2.dat": "8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f",
           "table3.dat": "c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d",
           "table4.dat": "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94"}
METHODS = geometry.LABELS
BASIS = ["nx", "ny", "nz", "nx^2-nz^2", "ny^2-nz^2", "2nxny", "2nxnz", "2nynz"]
WINDOWS = [("all_selected", None), ("z025", .025), ("z040", .04), ("z060", .06), ("z080", .08)]


def fit_profiled(x, y, sigma, kernel=None):
    """Slope map A and centered sufficient statistics; intercept is profiled.

    Covariance is A diag(sigma^2) A^T, including nonbinary kernel weights.
    For kernel=1 this reduces to G^-1. No residual scale is fitted.
    """
    x, y, sigma = np.asarray(x, float), np.asarray(y, float), np.asarray(sigma, float)
    if (x.ndim != 2 or y.shape != (len(x),) or sigma.shape != y.shape or
            not all(np.isfinite(a).all() for a in (x, y, sigma)) or np.any(sigma <= 0)):
        raise ValueError("finite compatible x,y and positive errors required")
    k = np.ones_like(y) if kernel is None else np.asarray(kernel, float)
    if k.shape != y.shape or not np.isfinite(k).all() or np.any(k < 0) or not k.sum() > 0:
        raise ValueError("finite nonnegative nonempty kernel required")
    w = k / sigma**2
    xmean = np.average(x, axis=0, weights=w)
    ymean = np.average(y, weights=w)
    xc, yc = x-xmean, y-ymean
    gram = (xc.T*w) @ xc
    if np.linalg.matrix_rank(gram) != x.shape[1]:
        raise ValueError("rank-deficient profiled shape fit")
    rhs = xc.T @ (w*yc)
    amap = np.linalg.solve(gram, xc.T*w)
    beta = amap @ yc
    cov = (amap*sigma**2) @ amap.T
    residual = yc-xc@beta
    stats = {"n": len(y), "sum_weights": float(w.sum()), "x_weighted_mean": xmean.tolist(),
             "y_weighted_mean_mag": float(ymean), "gram": gram.tolist(),
             "centered_rhs": rhs.tolist(), "centered_yWy": float(np.dot(w*yc, yc)),
             "coefficients_mag": beta.tolist(), "working_covariance": cov.tolist(),
             "weighted_rms_mag": float(np.sqrt(np.dot(w*residual, residual)/w.sum())),
             "gram_eigen_minmax": np.linalg.eigvalsh(gram)[[0,-1]].tolist()}
    return stats, amap


def minimum_delta(centers, radii):
    """Smallest common relative box radius for one contrast and one window."""
    b, q = np.asarray(centers, float), np.asarray(radii, float)
    if b.ndim != 1 or q.shape != b.shape or not len(b) or not np.isfinite(b).all() or not np.isfinite(q).all() or np.any(q < 0):
        raise ValueError("finite centers and nonnegative radii required")
    return float(max(0., (np.max(b-q)-np.min(b+q))/2))


def fit_selected(path=SOURCE):
    n, family, sigma, z = geometry.read_source(path)
    with np.load(path, allow_pickle=False) as f:
        mu, ids = f["dmzp"].copy(), f["group_id"].copy()
    if mu.shape != z.shape or not np.isfinite(mu).all():
        raise ValueError("invalid observed moduli")
    x = geometry.shape8(n)
    # Reference H=1 in numerical km/s/Mpc units; any fixed H adds only an
    # intercept removed separately within each partition and window.
    y = mu - 25 - 5*np.log10(299792.458*z)
    stats, covariances = {}, {}
    for method in METHODS:
        mask = family == method
        maps, blocks = [], []
        for label, center in WINDOWS:
            kernel = None if center is None else np.exp(-.5*((z[mask]-center)/.012)**2)
            fit, amap = fit_profiled(x[mask], y[mask], sigma[mask], kernel)
            stats.setdefault(label, {})[method] = fit
            maps.append(amap)
        for a in maps:
            blocks.append(np.concatenate([(a*sigma[mask]**2)@b.T for b in maps], axis=1))
        covariances[method] = np.concatenate(blocks, axis=0).tolist()
    reference = json.loads((HERE.parent / "P3/source/H02_ACTUAL_SELECTED_SOURCE_FISHER.json").read_text())
    for method in METHODS:
        fit = stats["all_selected"][method]
        if fit["n"] != reference["conditional_method_counts"][method] or not np.allclose(
            fit["gram_eigen_minmax"], reference["method_gram_eigen_minmax"][method], atol=1e-7, rtol=1e-11):
            raise ValueError("original H02 cohort/geometry replay mismatch")
    return {"fits": stats, "cross_window_working_covariance_by_partition": covariances,
            "original_H02_geometry_replay": "COUNTS_AND_ALL_FOUR_SPECTRAL_ENDPOINTS_MATCH",
            "selected_id_sha256": hashlib.sha256(np.asarray(ids, dtype="<i8").tobytes()).hexdigest()}, (ids, n, z, family)


def intervals(fits, deltas=(0., .01, .02, .03, .05, .075, .1, .15, .2), alpha=.05):
    """Union bound over every displayed window, method and fixed basis contrast.

    Correlations between windows/methods are unrestricted by the union bound.
    The displayed per-contrast sets are projections/outer sets; coupling beyond
    the box bounds is retained as unknown, never silently treated independent.
    """
    comparisons = len(fits)*len(METHODS)*8
    rows, thresholds = [], []
    for law in ("gaussian_marginals", "variance_only"):
        crit = critical_value(alpha, comparisons, law)
        for window, by_method in fits.items():
            centers = np.array([by_method[m]["coefficients_mag"] for m in METHODS])
            errors = np.array([np.sqrt(np.diag(by_method[m]["working_covariance"])) for m in METHODS])
            for j, name in enumerate(BASIS):
                q = crit*errors[:,j]
                thresholds.append({"law": law, "window": window, "contrast": name,
                                   "minimum_relative_delta_mag": minimum_delta(centers[:,j], q)})
                for delta in deltas:
                    interval = compatible_interval(dict(zip(METHODS, centers[:,j])), dict(zip(METHODS, q)), dict.fromkeys(METHODS, delta))
                    rows.append({"law": law, "window": window, "contrast": name, "delta_relative_mag": delta,
                                 "lower_mag": interval["lower"], "upper_mag": interval["upper"], "empty": interval["empty"]})
    return {"alpha": alpha, "simultaneous_comparisons": comparisons,
            "coverage_status": "CONDITIONAL_ON_CENTERED_WORKING_MARGINAL_ERROR_LAW; NOT_EMPIRICALLY_VALIDATED",
            "relative_calibration_model": "b_mw=theta_w+eta+gamma_m+epsilon_mw; |gamma_mj|<=delta; same gamma across windows",
            "shared_calibration": "eta common to methods/windows is not constrained by method overlaps. Sets describe theta_w+eta. For |eta_j|<=rho, expand nonempty endpoints by rho; eta_j unbounded gives R. No empirical rho supplied.",
            "joint_set_scope": "per-window coordinate projections are outer sets when common gamma across windows is imposed; no window-independence assumption",
            "thresholds": thresholds, "rows": rows}


def coupled_box(centers, radii, delta=None):
    """Project the joint box with gamma_m shared across all windows.

    Rows=windows, columns=methods. delta=None minimizes the required bound.
    Infeasibility is preserved, including when no finite delta can work.
    """
    b,q=np.asarray(centers,float),np.asarray(radii,float)
    if b.ndim!=2 or q.shape!=b.shape or not b.size or not np.isfinite(b).all() or not np.isfinite(q).all() or np.any(q<0):
        raise ValueError('finite window-by-method centers and nonnegative radii required')
    if delta is not None and (not np.isfinite(delta) or delta<0):
        raise ValueError('nonnegative finite calibration bound required')
    nw,nm=b.shape;size=nw+nm+(delta is None)
    rows=[];rhs=[]
    for w in range(nw):
        for m in range(nm):
            row=np.zeros(size);row[w]=1;row[nw+m]=1
            rows.extend([row,-row]);rhs.extend([b[w,m]+q[w,m],-b[w,m]+q[w,m]])
    bounds=[(None,None)]*nw
    if delta is None:
        bounds += [(None,None)]*nm+[(0,None)]
        for m in range(nm):
            row=np.zeros(size);row[nw+m]=1;row[-1]=-1
            rows.extend([row,row.copy()]);rows[-1][nw+m]=-1;rhs.extend([0.,0.])
        objective=np.zeros(size);objective[-1]=1
    else:
        bounds += [(-delta,delta)]*nm
        objective=np.zeros(size)
    a=np.array(rows);rhs=np.array(rhs)
    options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9}
    solution=linprog(objective,A_ub=a,b_ub=rhs,bounds=bounds,method='highs',options=options)
    if solution.status==2:
        return {'feasible':False,'status':'EMPTY_UNDER_SHARED_WINDOW_CONSTANT_CALIBRATION', 'minimum_delta_mag':None,'projections':None}
    if not solution.success:
        raise RuntimeError('calibration LP did not resolve: '+solution.message)
    if delta is None:
        return {'feasible':True,'status':'MINIMUM_DELTA_FOUND','minimum_delta_mag':float(solution.x[-1]),'projections':None,
                'max_linear_constraint_violation_mag':float(max(0.,np.max(a@solution.x-rhs)))}
    projections=[]
    for w in range(nw):
        objective=np.zeros(size);objective[w]=1
        lower=linprog(objective,A_ub=a,b_ub=rhs,bounds=bounds,method='highs',options=options)
        upper=linprog(-objective,A_ub=a,b_ub=rhs,bounds=bounds,method='highs',options=options)
        if not lower.success or not upper.success:raise RuntimeError('calibration LP projection failed')
        if max(np.max(a@lower.x-rhs),np.max(a@upper.x-rhs))>1e-7:
            raise RuntimeError('calibration LP numerical constraint residual exceeds 1e-7 mag')
        projections.append([float(lower.fun),float(-upper.fun)])
    return {'feasible':True,'status':'JOINT_BOX_COORDINATE_PROJECTIONS','minimum_delta_mag':None,'projections':projections}


def coupled_intervals(fits,alpha=.05,deltas=(0.,.02,.05,.1)):
    windows=list(fits);comparisons=len(windows)*len(METHODS)*8;result=[]
    for law in ('gaussian_marginals','variance_only'):
        crit=critical_value(alpha,comparisons,law)
        for j,name in enumerate(BASIS):
            b=np.array([[fits[w][m]['coefficients_mag'][j] for m in METHODS] for w in windows])
            q=crit*np.sqrt([[fits[w][m]['working_covariance'][j][j] for m in METHODS] for w in windows])
            result.append({'law':law,'contrast':name,'minimum_bound':coupled_box(b,q),
                           'scenarios':[{'delta_relative_mag':delta,**coupled_box(b,q,delta)} for delta in deltas]})
    return {'window_order':windows,'LP_solver':'SciPy linprog HiGHS; primal/dual feasibility tolerance 1e-9; projection linear residual must not exceed 1e-7 mag',
            'shared_calibration':'same gamma_mj across windows; theta_wj+eta_j free per window; eta_j not anchored',
            'scope':'sharp coordinate projections in declared joint error/calibration boxes for each contrast; not physical confidence and not an empirical calibration estimate',
            'results':result}


def authenticated_lines(directory, name):
    raw = (Path(directory)/name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != RAW_SHA[name]:
        raise ValueError("immutable CF4 raw source SHA mismatch: "+name)
    return raw.decode("ascii").splitlines()


def overlap_diagnostics(directory, selected):
    """Release-level same-group contrasts, not independent recalibration data."""
    from common.cf4_manifest import TABLE3_COLUMNS, TABLE4_COLUMNS
    ids, directions, redshifts, family = selected
    columns = {c.label:c for c in TABLE3_COLUMNS}
    rows = authenticated_lines(directory, "table3.dat")
    ids3 = np.array([columns["1PGC"].value(line) for line in rows], dtype=np.int64)
    if len(rows) != 38053 or len(np.unique(ids3)) != len(ids3):
        raise ValueError("raw group identities/counts changed")
    order = {int(i):k for k,i in enumerate(ids3)}
    if not set(ids).issubset(order):
        raise ValueError("selected ID absent in raw groups")
    selected_order = np.array([order[int(i)] for i in ids])
    def col(name):
        return np.array([np.nan if columns[name].value(l) is None else columns[name].value(l) for l in rows])
    if not np.array_equal(col("Vcmb")[selected_order]/299792.458, redshifts):
        raise ValueError("raw/selected redshift identity mismatch")
    raw_z=col('Vcmb')/299792.458
    redshift_membership_match=set(ids3[(raw_z>=.01)&(raw_z<=.1)])==set(ids)
    if not redshift_membership_match:
        raise ValueError('selected group set differs from recorded .01<=z_CMB<=.1 source cut')
    ra, dec = np.deg2rad(col("RAdeg")[selected_order]), np.deg2rad(col("DEdeg")[selected_order])
    expected_n = np.column_stack((np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)))
    if not np.allclose(expected_n, directions, atol=2e-12, rtol=0):
        raise ValueError("raw/selected J2000 geometry mismatch")
    rows4 = authenticated_lines(directory, "table4.dat")
    columns4 = {c.label:c for c in TABLE4_COLUMNS}
    group4 = {int(columns4["1PGC"].value(l)):l for l in rows4}
    if len(group4)!=38053 or set(group4)!=set(ids3):
        raise ValueError("table3/table4 group parity mismatch")
    with np.load(SOURCE, allow_pickle=False) as f:
        for name, target in (("DMzp", f["dmzp"]), ("e_DMzp", f["e_dmzp"])):
            if not np.array_equal(np.array([columns4[name].value(group4[int(i)]) for i in ids]), target):
                raise ValueError("raw/selected distance field mismatch: "+name)
    definitions = [("CAL", "DMcal", "o_DMcal", None), ("SNIA", "DMsnIa", "o_DMsnIa", "e_DMsnIa"),
                   ("FP", "DMfp", "o_DMfp", "e_DMfp"), ("TF", "DMtf", "o_DMtf", "e_DMtf"),
                   ("SBFO", "DMsbfo", "o_DMsbfo", "e_DMsbfo"), ("SBFI", "DMsbfi", "o_DMsbfi", "e_DMsbfi"),
                   ("SNII", "DMsnII", None, "e_DMsnII")]
    presence, values, errors = [], {}, {}
    for label, value, count, error in definitions:
        v = col(value)
        valid = np.isfinite(v) & (v > 0)
        if count:
            valid &= col(count)>0
        presence.append(valid)
        values[label] = v[selected_order]
        if error:
            errors[label] = col(error)[selected_order]
    p = np.array(presence).T
    ps = p[selected_order]
    # Deterministic five-way split is by entire group, never by measurement.
    holdout = np.array([int(hashlib.sha256(str(int(i)).encode()).hexdigest()[:8],16)%5 == 0 for i in ids])
    pairs = []
    labels = [d[0] for d in definitions]
    x = geometry.shape8(directions)
    for a, left in enumerate(labels):
        for b, right in enumerate(labels[a+1:], a+1):
            keep = ps[:,a] & ps[:,b]
            result = {"left":left,"right":right,"selected_groups":int(keep.sum())}
            if np.any(keep):
                diff = values[left][keep]-values[right][keep]
                result["released_difference_quantiles_16_50_84_mag"] = np.quantile(diff,[.16,.5,.84]).tolist()
            if left in errors and right in errors:
                err = np.hypot(errors[left], errors[right])
                valid = keep & np.isfinite(err) & (err > 0)
                train, test = valid & ~holdout, valid & holdout
                result.update(train_groups=int(train.sum()), heldout_groups=int(test.sum()))
                if train.sum()>=24 and test.sum()>=8:
                    y = values[left]-values[right]
                    try:
                        fit, _ = fit_profiled(x[train],y[train],err[train])
                        beta = np.array(fit["coefficients_mag"])
                        intercept = fit["y_weighted_mean_mag"]-np.dot(fit["x_weighted_mean"], beta)
                        w = 1/err[test]**2
                        result["training_shape_coefficients_mag"] = beta.tolist()
                        result["training_intercept_mag"] = float(intercept)
                        result["heldout_weighted_rms_constant_mag"] = float(np.sqrt(np.average((y[test]-fit["y_weighted_mean_mag"])**2,weights=w)))
                        result["heldout_weighted_rms_shape_mag"] = float(np.sqrt(np.average((y[test]-intercept-x[test]@beta)**2,weights=w)))
                    except ValueError as exc:
                        result["fit_status"] = str(exc)
                else:
                    result["fit_status"] = "INSUFFICIENT_GROUPS_FOR_PREDECLARED_24_TRAIN_8_TEST_RULE"
            pairs.append(result)
    galaxies = authenticated_lines(directory,"table2.dat")
    if len(galaxies)!=55877:
        raise ValueError("raw galaxy row count changed")
    galaxy_ids = np.array([int(l[8:15]) for l in galaxies])
    unique_galaxy = np.unique([int(l[:7]) for l in galaxies])
    unique_groups, counts = np.unique(galaxy_ids, return_counts=True)
    return {"method_labels":labels,"parent_group_count":len(ids3),"selected_group_count":len(ids),
            "source_membership_replay":"EXACT_ID_SET_MATCH: all raw groups with .01<=z_CMB<=.1; this is an analysis cut, not observational completeness",
            "parent_method_overlap_counts":(p.astype(int).T@p.astype(int)).tolist(),
            "selected_method_overlap_counts":(ps.astype(int).T@ps.astype(int)).tolist(),
            "selected_partition_vs_method_presence":{m:ps[family==m].sum(axis=0).tolist() for m in METHODS},
            "parent_method_multiplicity_histogram":np.bincount(p.sum(axis=1),minlength=8).tolist(),
            "selected_method_multiplicity_histogram":np.bincount(ps.sum(axis=1),minlength=8).tolist(),
            "galaxy_rows":len(galaxies),"unique_galaxy_ids":len(unique_galaxy),
            "galaxy_group_ids_not_in_group_release":int(np.sum(~np.isin(unique_groups,ids3))),
            "galaxy_group_count":len(unique_groups),"galaxies_within_selected_groups":int(np.sum(np.isin(galaxy_ids,ids))),
            "galaxies_per_group_quantiles_0_50_90_99_100":np.quantile(counts,[0,.5,.9,.99,1]).tolist(),
            "pairwise_release_diagnostics":pairs,
            "heldout_scope":"group-hash holdout of already jointly calibrated released distances. Upstream preprocessing used the whole release; this is NOT independent calibration validation. Pair errors hypot(e_left,e_right) are diagnostic weights, not admitted variance.",
            "selection_scope":"conditional source membership and method availability only, not parent targeting probabilities or completeness law"}


def run(source=SOURCE, raw=RAW, out=HERE/"results"):
    result, selected = fit_selected(source)
    result.update(schema="htt.h02_actual_centers_overlap/1", owner="htt", claim_tier="CONDITIONAL", transfer_source="none",
                  source_npz_sha256=geometry.SHA, basis=BASIS, windows=WINDOWS, window_width_z=.012,
                  estimand="partition-specific angular coefficients of DMzp-25-5log10(c*z_CMB), mag, with separate method/window intercepts",
                  partition_caveat="FP/TF/SN/OTHER are disjoint pooled-catalogue partitions, NOT pure independent method measurements; table3 overlap is reported separately",
                  noise_assumption="centered errors with released e_DMzp diagonal working covariance; selected likelihood, velocity field and shared calibration covariance UNKNOWN",
                  cross_method_covariance="zero ONLY in the assumed diagonal group error model; physical cross-method covariance UNKNOWN",
                  physical_inference="NOT_PERFORMED", H02_acceptance="HOLD: true selection/shared calibration-velocity law and source null simulations missing",
                  source_table_sha256=RAW_SHA,
                  intervals=intervals(result["fits"]), coupled_intervals=coupled_intervals(result['fits']),
                  overlap=overlap_diagnostics(raw, selected))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"h02_actual_centers.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    with (out/"h02_observed_intervals.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(result["intervals"]["rows"][0]));writer.writeheader();writer.writerows(result["intervals"]["rows"])
    print(json.dumps({"groups":len(selected[0]), "fit_blocks":len(WINDOWS)*len(METHODS),
                      "interval_rows":len(result["intervals"]["rows"]),"geometry_replay":result["original_H02_geometry_replay"],"H02":"HOLD"}))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=SOURCE)
    parser.add_argument("--raw",type=Path,default=RAW)
    parser.add_argument("--out",type=Path,default=HERE/"results")
    args=parser.parse_args();run(args.source,args.raw,args.out)
