"""R24 distance comparison under the predeclared conditional working laws."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
R23 = HERE.parents[1] / "CONTINUOUS_RESEARCH_20261023/execution/R23-DISTANCE"
RAW = Path("/mnt/extdrive/workdir/htt_open_data/cf4")
LEDGER = RAW / "D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv"
CF4 = RAW / "J_ApJ_944_94"
SOURCE_HASHES = {
    HERE.parent / "DISTANCE_INPUT.json": "94ba6ebeeaa029c868663cd873e0626f892976e77a56c9d60ccc54c9cf1e1812",
    R23 / "RELEASED_ROWS.csv": "c7912bd7dd983cdcdf47408a89da9f2b76887a0cc37fd9b5a9a8e83e03d3fe20",
    R23 / "conditional_fit/CONTRACT.json": "e0fc0047e27a7bdc71b8af121820d0948941c673c48cc5cfb8a8add227640cdd",
    R23 / "conditional_fit/RESULT.json": "bc8c75f8e546f3d976610ef49676807b0467abac1e1bf4edf3d552d259e36814",
    LEDGER: "c32885cd2f081ec1bcedfcb98ef18c8c53245c12ac4a5fabb64d68b27a75f48d",
    CF4 / "ReadMe": "2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4",
    CF4 / "table2.dat": "8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f",
}
MISSING_FIVE = (9031, 68715, 84490, 90725, 91648)
FIVE_HASHES = {
    9031: "1b408338842420a01d2b40623fb9f0081941ad79fcc5afbfbbb9d514935a8a89",
    68715: "bccb698b17d08a96986163f40d652f7c590062bc835f5a879665183af3edceeb",
    84490: "b9e5be4a6f7229a08a83df24215f4e8fa99bf427b63d31de0956229ab48a245a",
    90725: "bbe6239bc8ceec461be511f9fac808e428094016cb880bda1b733a829e63662d",
    91648: "fc3b62a9a9b7c25e4fbbf347ab60fffe770ccb332c6a2aac93314eed3cf674ef",
}
STF = np.array([
    np.diag([1, -1, 0]) / math.sqrt(2),
    np.diag([-1, -1, 2]) / math.sqrt(6),
    [[0, 1 / math.sqrt(2), 0], [1 / math.sqrt(2), 0, 0], [0, 0, 0]],
    [[0, 0, 1 / math.sqrt(2)], [0, 0, 0], [1 / math.sqrt(2), 0, 0]],
    [[0, 0, 0], [0, 0, 1 / math.sqrt(2)], [0, 1 / math.sqrt(2), 0]],
])
BASE_NAMES = ["intercept", "log10_vcmb", "measured_logWmxi", "e_logWmxi"]
ANG_NAMES = ["n_x", "n_y", "n_z"]
FLOW_NAMES = ["K_n_x", "K_n_y", "K_n_z"]
STF_NAMES = [f"STF_{j}" for j in range(1, 6)]
MODELS = {
    "A_calibration_flow": BASE_NAMES + ANG_NAMES + FLOW_NAMES,
    "B_optical_STF": BASE_NAMES + ANG_NAMES + STF_NAMES,
    "C_union": BASE_NAMES + ANG_NAMES + FLOW_NAMES + STF_NAMES,
}
RTOL = 1e-9
ATOL = 1e-10


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def require_close(actual, reference, label, rtol=RTOL, atol=ATOL):
    np.testing.assert_allclose(actual, reference, rtol=rtol, atol=atol, err_msg=label)


def load():
    for path, expected in SOURCE_HASHES.items():
        if sha(path) != expected:
            raise ValueError(f"immutable source changed: {path}")
    rows = list(csv.DictReader((R23 / "RELEASED_ROWS.csv").open(newline="")))
    ledger = list(csv.DictReader(LEDGER.open(newline="")))
    if len(rows) != 274 or len(ledger) != 628:
        raise ValueError("cohort size changed")
    ids = [int(r["pgc"]) for r in rows]
    all_ids = [int(r["pgc"]) for r in ledger]
    if len(set(ids)) != 274 or len(set(all_ids)) != 628 or not set(ids) <= set(all_ids):
        raise ValueError("PGC uniqueness/subset failed")
    by_id = {int(r["pgc"]): r for r in ledger}
    count = Counter((r["outcome"], int(r["pgc"]) in set(ids)) for r in ledger)
    if [count[(o, x)] for o in ("accepted", "other_quality", "confused", "nondetection") for x in (False, True)] != [116,269,21,1,26,3,191,1]:
        raise ValueError("outcome/availability marks changed")
    groups = [f'CF4:{by_id[i]["CF4_group"]}' if by_id[i]["CF4_group"] else f"UNASSIGNED_PGC:{i}" for i in ids]
    folded = defaultdict(set)
    for i, g in zip(ids, groups):
        folded[g].add(int(by_id[i]["fold"]))
    if all(len(x) == 1 for x in folded.values()):
        folds = np.array([int(by_id[i]["fold"]) for i in ids])
        fold_rule = "cached ledger fold; each observed CF4 group wholly in one fold"
    else:
        folds = np.array([int(hashlib.sha256(g.encode()).hexdigest(), 16) % 5 for g in groups])
        fold_rule = "sha256(group-label) modulo five"
    if sorted(set(folds)) != list(range(5)):
        raise ValueError("five folds absent")
    coords = {}
    for line in (CF4 / "table2.dat").open():
        if not line[:7].strip():
            continue
        pgc = int(line[:7])
        if pgc in ids:
            if pgc in coords:
                raise ValueError(f"duplicate CF4 direction PGC {pgc}")
            coords[pgc] = (float(line[137:145]), float(line[146:154]), "CF4_J_ApJ_944_94_table2")
    if set(ids) - set(coords) != set(MISSING_FIVE):
        raise ValueError(f"unexpected CF4 direction gap {sorted(set(ids)-set(coords))}")
    for pgc in MISSING_FIVE:
        path = RAW / "r24_distance_models_20261023" / f"PGC_{pgc}.tsv"
        if sha(path) != FIVE_HASHES[pgc]:
            raise ValueError(f"HyperLEDA query identity changed PGC {pgc}")
        lines = [line for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
        if len(lines) != 4:
            raise ValueError(f"HyperLEDA query not unique PGC {pgc}")
        fields = lines[-1].split("\t")
        if int(fields[0]) != pgc or fields[3].strip() != "G":
            raise ValueError(f"HyperLEDA PGC/object type mismatch {pgc}")
        hh, mm, ss = map(float, fields[1].split())
        dd, dm, ds = fields[2].replace("+", "").replace("-", "").split()
        ra = 15 * (hh + mm / 60 + ss / 3600)
        dec = (1 if fields[2][0] == "+" else -1) * (float(dd) + float(dm)/60 + float(ds)/3600)
        coords[pgc] = (ra, dec, "HyperLEDA_VII_237_pgc")
    if len(coords) != 274:
        raise ValueError("full 274 directions not joined")
    angles = np.radians(np.array([[coords[i][0], coords[i][1]] for i in ids]))
    n = np.column_stack((np.cos(angles[:,1])*np.cos(angles[:,0]), np.cos(angles[:,1])*np.sin(angles[:,0]), np.sin(angles[:,1])))
    require_close(np.sum(n*n, axis=1), np.ones(274), "unit directions", 1e-12, 1e-12)
    require_close(np.einsum("aij,bij->ab", STF, STF), np.eye(5), "STF basis", 1e-12, 1e-12)
    require_close(np.trace(STF, axis1=1, axis2=2), np.zeros(5), "STF trace", 1e-12, 1e-12)
    return rows, ledger, ids, groups, folds, fold_rule, coords, n


def features(rows, n):
    y = np.array([float(r["DMbest_mag"]) for r in rows])
    s = np.array([float(r["e_DMbest_mag"]) for r in rows])
    v = np.array([float(r["vcmb_km_s"]) for r in rows])
    w = np.array([float(r["logWmxi"]) for r in rows])
    ew = np.array([float(r["e_logWmxi"]) for r in rows])
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(s)) and np.all(s > 0) and
            np.all(np.isfinite(v)) and np.all(v > 0) and np.all(np.isfinite(w)) and np.all(np.isfinite(ew))):
        raise ValueError("nonfinite/invalid released response or covariate")
    k = -5 / (math.log(10) * v)
    S = np.einsum("ni,aij,nj->na", n, STF, n)
    all_features = dict(zip(BASE_NAMES + ANG_NAMES + FLOW_NAMES + STF_NAMES,
        np.column_stack((np.ones(274), np.log10(v), w, ew, n, k[:,None]*n, S)).T))
    return y, s, v, all_features


def covariance(s, groups, a, b):
    if a > s.min() or a < 0 or b < 0:
        raise ValueError("invalid covariance scenario scales")
    V = np.diag(s*s-a*a) + a*a*np.ones((len(s),len(s)))
    V += b*b*np.equal.outer(groups, groups)
    require_close(V, V.T, "covariance symmetry", 1e-12, 1e-12)
    require_close(np.diag(V), s*s+b*b, "covariance diagonal accounting", 1e-12, 1e-12)
    np.linalg.cholesky(V)
    return V


def design(feats, names):
    return np.column_stack([feats[name] for name in names])


def fit_predict(X, y, V, train, test=None):
    """Full GLS or one complete held-out block; coefficients reported in raw feature units."""
    Xt, yt = X[train], y[train]
    Vtt = V[np.ix_(train,train)]
    center = np.r_[0.0, Xt[:,1:].mean(axis=0)]
    scale = np.r_[1.0, np.sqrt(np.mean((Xt[:,1:]-center[1:])**2,axis=0))]
    if np.any(scale <= 0) or not np.all(np.isfinite(scale)):
        raise ValueError("zero/nonfinite training design scale")
    Z = (X-center)/scale
    Z[:,0] = 1
    Lt = np.linalg.cholesky(Vtt)
    Zw = solve_triangular(Lt,Z[train],lower=True,check_finite=False)
    yw = solve_triangular(Lt,yt,lower=True,check_finite=False)
    U, sing, Vh = np.linalg.svd(Zw,full_matrices=False)
    ranks = {str(t): int(np.sum(sing > t*sing[0])) for t in (1e-8,1e-10,1e-12)}
    rank = ranks[str(1e-10)]
    p = X.shape[1]
    null = Vh[rank:].T
    if rank < p and test is not None:
        effect = np.linalg.norm(Z[test]@null)
        if effect > 1e-10*max(1,np.linalg.norm(Z[test])):
            raise ValueError(f"held-out prediction not identifiable: rank {rank}/{p}, null effect {effect}")
    coeff = Vh[:rank].T @ ((U[:,:rank].T@yw)/sing[:rank])
    rw = yw-Zw@coeff
    rss = float(rw@rw)
    if not math.isfinite(rss) or rss <= 0:
        raise ValueError("invalid train GLS RSS")
    sigma2 = rss/len(train)
    normal = np.linalg.norm(Zw.T@rw)
    normal_scaled = normal/max(1,np.linalg.norm(Zw)*np.linalg.norm(yw))
    if normal_scaled > 1e-10:
        raise ValueError(f"GLS normal equation failed {normal_scaled}")
    transform = np.diag(1/scale)
    transform[0,1:] = -center[1:]/scale[1:]
    rawbeta = transform @ coeff if rank == p else None
    cov_raw = None
    if rank == p:
        cov_z = (Vh.T / (sing*sing)) @ Vh * sigma2
        cov_raw = transform @ cov_z @ transform.T
    out = {"n_train":len(train),"rank":rank,"p":p,"rank_sensitivity":ranks,
           "singular_values_whitened_scaled":sing.tolist(),"centers":center.tolist(),"scales":scale.tolist(),
           "sigma2_ML_train":sigma2,"rss":rss,"normal_equation_scaled":float(normal_scaled),
           "coefficient_raw_units":rawbeta.tolist() if rawbeta is not None else None,
           "coefficient_covariance_raw_units":cov_raw.tolist() if cov_raw is not None else None,
           "coefficient_status":"IDENTIFIABLE" if rank == p else "NOT_IDENTIFIABLE",
           "nullspace_scaled":null.T.tolist() if rank < p else []}
    if test is None:
        return out, None
    Xs, ys = X[test], y[test]
    Vst = V[np.ix_(test,train)]
    Vss = V[np.ix_(test,test)]
    B = solve_triangular(Lt.T,solve_triangular(Lt,Vst.T,lower=True,check_finite=False),lower=False,check_finite=False).T
    training_residual = yt-Z[train]@coeff
    pred = Z[test]@coeff + B@training_residual
    S = Vss-B@Vst.T
    require_close(S,S.T,"Schur covariance symmetry",1e-10,1e-10)
    Ls = np.linalg.cholesky(S)
    innov = solve_triangular(Ls,ys-pred,lower=True,check_finite=False)
    quadratic = float(innov@innov/sigma2)
    logdet = float(2*np.log(np.diag(Ls)).sum()+len(test)*math.log(sigma2))
    score = float(-.5*(len(test)*math.log(2*math.pi)+logdet+quadratic))
    ordered_contributions = -.5*(math.log(2*math.pi*sigma2)+2*np.log(np.diag(Ls))+innov**2/sigma2)
    require_close(np.sum(ordered_contributions),score,"joint score chain sum",1e-10,1e-10)
    # Independent dense Gaussian fixture for the first three held-out coordinates.
    k = min(3,len(test)); z = ys[:k]-pred[:k]
    direct = np.linalg.solve(S[:k,:k],z)
    require_close(np.sum(solve_triangular(np.linalg.cholesky(S[:k,:k]),z,lower=True)**2),z@direct,
                  "dense Schur quadratic",1e-10,1e-10)
    out.update({"n_test":len(test),"joint_log_predictive_score":score,"joint_score_per_row":score/len(test),
                "Schur_min_cholesky_pivot":float(np.diag(Ls).min()),
                "Schur_logdet_sigma2":logdet,"test_quadratic":quadratic,
                "prediction_status":"PLUG_IN_GAUSSIAN_BETA_SIGMA_UNCERTAINTY_OMITTED"})
    return out, (pred,ordered_contributions)


def residual_summaries(rows, v, n, residual):
    q = np.quantile(v,[1/3,2/3])
    depth = np.digitize(v,q,right=True)
    def one(idx):
        x = residual[idx]
        return {"n":int(len(x)),"mean_signed_mag":float(np.mean(x)),"rms_mag":float(np.sqrt(np.mean(x*x)))}
    method = {mark:one(np.array([r["outcome"]==mark for r in rows])) for mark in
              ("accepted","other_quality","confused","nondetection")}
    by_depth = {str(j):one(depth==j) for j in range(3)}
    hemi = {axis:{"positive":one(n[:,j]>=0),"negative":one(n[:,j]<0)} for j,axis in enumerate("xyz")}
    dip = np.linalg.lstsq(n,residual,rcond=None)[0]
    return {"depth_edges_Vcmb_km_s":q.tolist(),"depth_bins":by_depth,"outcome_marks":method,
            "J2000_cartesian_hemispheres":hemi,"least_squares_residual_dipole_mag":dip.tolist(),
            "residual_rms_mag":float(np.sqrt(np.mean(residual**2)))}


def run():
    rows,ledger,ids,groups,folds,fold_rule,coords,n = load()
    y,s,v,feats=features(rows,n)
    result={"task":"R24-DISTANCE-MODELS","claim_tier":"C0_AUTHORED_CONDITIONAL_DIAGNOSTIC",
      "scientific_admission":"HOLD","original_acceptance":"HOLD","observed_runtime":"UNKNOWN",
      "cohort":{"selected":628,"released":274,"undefined":354,"min_Vcmb_km_s":float(v.min()),"max_Vcmb_km_s":float(v.max()),
                "fold_rule":fold_rule,"fold_counts":dict(Counter(map(str,folds)))},
      "direction_sources":{"CF4_J2000":269,"HyperLEDA_J2000":5,"missing":0,"five_PGCs":list(MISSING_FIVE)},
      "historical_residual_failure":{"T":4.555321823822732,"p_plus_one":0.000976324139614352,"status":"RETAINED"},
      "covariance_law":"V(a,b)=diag(s^2-a^2)+a^2 11T+b^2 GGt; authored, physical calibration/PV overlap unresolved",
      "prediction_law":"normalized block-conditional plug-in Gaussian; training ML sigma2; coefficient/scale uncertainty omitted",
      "K_units":"mag per km/s response to scenario flow vector in km/s; low-z approximation unqualified at PGC9031",
      "tensor_status":"optical effective STF on selected finite-z window; no u-to-G or finite-z remainder map",
      "scenarios":{}}
    row_out=[]
    source_out=[{"pgc":i,"ra_J2000_deg":coords[i][0],"dec_J2000_deg":coords[i][1],
                 "direction_source":coords[i][2],"fold":int(folds[j]),"group":groups[j],
                 "Vcmb_km_s":float(v[j]),"outcome":rows[j]["outcome"]} for j,i in enumerate(ids)]
    for a in (0.0,.055):
      for b in (0.0,.29):
        key=f"a_{a:.3f}_b_{b:.3f}"
        V=covariance(s,groups,a,b)
        result["scenarios"][key]={"a_mag":a,"b_mag":b,"models":{}}
        for model,names in MODELS.items():
          X=design(feats,names)
          full, _=fit_predict(X,y,V,np.arange(274))
          if full["coefficient_status"] == "IDENTIFIABLE":
            angular_indices=[names.index(z) for z in ANG_NAMES+FLOW_NAMES+STF_NAMES if z in names]
            full["angular_tensor_state"]={
              "names":[names[j] for j in angular_indices],
              "units":["mag"]*3 + (["km/s"]*3 if "K_n_x" in names else []) +
                      (["mag"]*5 if "STF_1" in names else []),
              "coefficient_vector":[full["coefficient_raw_units"][j] for j in angular_indices],
              "full_joint_covariance_including_cross_blocks":
                np.asarray(full["coefficient_covariance_raw_units"])[np.ix_(angular_indices,angular_indices)].tolist(),
              "meaning":"selected finite-z observational scenario; not G-congruence shear or HTT physical x"
            }
          fold_result=[]
          oof_pred=np.full(274,np.nan)
          oof_score=np.full(274,np.nan)
          for f in range(5):
            tr=np.flatnonzero(folds!=f);te=np.flatnonzero(folds==f)
            fit, prediction=fit_predict(X,y,V,tr,te)
            fold_result.append({"fold":f,**fit})
            oof_pred[te],oof_score[te]=prediction
          if not np.all(np.isfinite(oof_pred)) or not np.all(np.isfinite(oof_score)):
            raise ValueError(f"nonfinite/missing OOF predictions {key}/{model}")
          joint_total=float(sum(z["joint_log_predictive_score"] for z in fold_result))
          require_close(joint_total,float(oof_score.sum()),"all block score chain sum",1e-10,1e-10)
          residual=y-oof_pred
          item={"column_names_raw_units":names,"full_fit":full,"folds":fold_result,
                "total_joint_log_predictive_score":joint_total,"joint_log_score_per_row":joint_total/274,
                "oof_residual_summaries":residual_summaries(rows,v,n,residual),
                "non_calibrated_model_comparison":True}
          result["scenarios"][key]["models"][model]=item
          for j,pgc in enumerate(ids):
            row_out.append({"scenario":key,"model":model,"pgc":pgc,"fold":int(folds[j]),
                            "observed_DMbest_mag":float(y[j]),"OOF_predicted_DMbest_mag":float(oof_pred[j]),
                            "OOF_signed_residual_mag":float(residual[j]),
                            "OOF_ordered_conditional_log_score":float(oof_score[j])})
    (HERE/"RESULT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    for name,items in (("DIRECTION_JOIN.csv",source_out),("OOF_ROWS.csv",row_out)):
      with (HERE/name).open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(items[0]))
        writer.writeheader();writer.writerows(items)
    return result


if __name__ == "__main__":
    r=run()
    print(json.dumps({"status":"EXECUTED_EXPLORATORY","scenarios":len(r["scenarios"]),
      "scores":{s:{m:round(d["total_joint_log_predictive_score"],6)
                     for m,d in v["models"].items()} for s,v in r["scenarios"].items()}},indent=2))
