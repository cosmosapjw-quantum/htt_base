"""R67 real-CF4 same-group method-contrast experiment.

Source: Tully et al. Cosmicflows-4 CDS J/ApJ/944/94 table3/table4 (fixed-width).
Pure nuisance-projection/linear model; NOT a calibrated cosmological likelihood.
Frames: sourceward Galactic n. Units: distance modulus mag, distance Mpc.
No global tilt, physical shear or Bianchi identification claimed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.linalg import null_space
from scipy.stats import chi2

METHODS = ("FP", "TF", "SN")
# CDS ReadMe, 0-based half-open columns for table3 DM and error.
SLICES = {"FP": ((117, 123), (124, 129)),
          "TF": ((133, 139), (140, 145)),
          "SN": ((100, 106), (107, 112))}
SOURCE = "J/ApJ/944/94"


def read_float(line: str, span: tuple[int, int]) -> float:
    try:
        return float(line[span[0]:span[1]])
    except ValueError:
        return float("nan")


def read_cf4_groups(root: Path) -> dict:
    """Source rows must have identical group IDs; preserve IDs and invalidity."""
    p3, p4 = root / "table3.dat", root / "table4.dat"
    vals = {x: [] for x in METHODS}
    errs = {x: [] for x in METHODS}
    ids, distance, lon, lat = [], [], [], []
    with p3.open() as a, p4.open() as b:
        for n, (x, y) in enumerate(zip(a, b, strict=True)):
            i, j = int(x[:7]), int(y[:7])
            if i != j:
                raise ValueError(f"CF4 group mismatch line={n+1}: {i}!={j}")
            ids.append(i)
            distance.append(read_float(y, (21, 26)))
            lon.append(read_float(y, (101, 109)))
            lat.append(read_float(y, (110, 118)))
            for method in METHODS:
                val_range, err_range = SLICES[method]
                vals[method].append(read_float(x, val_range))
                errs[method].append(read_float(x, err_range))
    ids = np.asarray(ids, int)
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate group ID")
    deg = np.deg2rad
    l, b = deg(np.asarray(lon, float)), deg(np.asarray(lat, float))
    n = np.column_stack((np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)))
    if not np.allclose(np.linalg.norm(n, axis=1), 1, atol=1.e-10):
        raise ValueError("Invalid source direction")
    return {"id": ids, "distance_mpc": np.asarray(distance), "n": n,
            "mu": {x: np.asarray(vals[x], float) for x in METHODS},
            "err": {x: np.asarray(errs[x], float) for x in METHODS},
            "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (p3, p4)}}


def stf_features(n: np.ndarray) -> np.ndarray:
    """Frobenius-orthonormal STF basis: xx-yy, xx+yy-2zz, xy, xz, yz."""
    x, y, z = np.asarray(n, float).T
    return np.column_stack(((x*x-y*y)/np.sqrt(2),
                            (x*x+y*y-2*z*z)/np.sqrt(6),
                            np.sqrt(2)*x*y, np.sqrt(2)*x*z, np.sqrt(2)*y*z))


def features(dist: np.ndarray, n: np.ndarray, center: float, scale: float) -> np.ndarray:
    """One method's 11 source basis columns: radial 3, signed angular 8."""
    if np.any(dist <= 0) or scale <= 0:
        raise ValueError("Distance/scale")
    u = (np.log(dist)-center)/scale
    return np.column_stack((np.ones(len(dist)), u, u*u, n, stf_features(n)))


def design_diagnostics(X: np.ndarray) -> dict:
    sv = np.linalg.svd(X / np.linalg.norm(X, axis=0), compute_uv=False)
    return {"rank": int(np.linalg.matrix_rank(X)),
            "column_normalized_condition": float(sv[0]/sv[-1]),
            "singular_values_normalized": sv.tolist()}


def score_model(z: np.ndarray, X0: np.ndarray, Xa: np.ndarray,
                gid: np.ndarray, reps: int, seed: int) -> dict:
    """Group-level wild null resampling, fixed design, pre-specified 8 angular df per method.

    The bootstrap is conditional on independent group clusters and zero-mean
    symmetric errors AFTER the published catalogue's upstream calibration.
    It is not cosmology null/selection calibration.
    """
    z = np.asarray(z, float)
    X0, Xa = np.asarray(X0, float), np.asarray(Xa, float)
    if len(z) != len(X0) or len(z) != len(Xa):
        raise ValueError("Length mismatch")
    # A QR projection is only legitimate when X0 spans *all* of its
    # nominal columns.  Otherwise the arbitrary QR completion steals
    # angular directions and reports a false score improvement.
    if np.linalg.matrix_rank(X0) != X0.shape[1]:
        raise ValueError("Radial nuisance rank deficient")
    q0, _ = np.linalg.qr(X0, mode="reduced")
    Ap = Xa - q0 @ (q0.T @ Xa)
    qa, ra = np.linalg.qr(Ap, mode="reduced")
    if np.linalg.matrix_rank(ra) != Xa.shape[1]:
        raise ValueError("Angular nonidentification")
    beta0 = np.linalg.lstsq(X0, z, rcond=None)[0]
    beta = np.linalg.lstsq(np.column_stack((X0, Xa)), z, rcond=None)[0]
    r0 = z-X0@beta0
    resid = z-np.column_stack((X0, Xa))@beta
    delta = float(np.sum((qa.T @ z)**2))
    raw_chi = float(np.sum(r0*r0))
    full_chi = float(np.sum(resid*resid))
    groups, index = np.unique(gid, return_inverse=True)
    influence = np.zeros((Xa.shape[1], len(groups)))
    np.add.at(influence.T, index, (qa*r0[:, None]))
    rng = np.random.default_rng(seed)
    # Rademacher draws by group, not by contrast row; group multimethod correlations retained.
    signs = rng.choice([-1., 1.], size=(len(groups), reps))
    null = np.sum((influence @ signs)**2, axis=0)
    p = (1+np.count_nonzero(null >= delta))/(reps+1)
    return {"n_contrasts": len(z), "n_groups": len(groups),
            "rank_radial": int(np.linalg.matrix_rank(X0)),
            "rank_all": int(np.linalg.matrix_rank(np.column_stack((X0, Xa)))),
            "radial_chisq_working": raw_chi,
            "full_chisq_working": full_chi, "delta_chisq_working": delta,
            "bootstrap_reps": reps, "seed": seed, "wild_group_p_exploratory": float(p),
            "null_q50_q95_q99": np.quantile(null, [.5,.95,.99]).tolist(),
            "beta_full": beta.tolist(), "beta_radial": beta0.tolist(),
            "naive_chisq_reference_p": float(chi2.sf(delta, Xa.shape[1]))}


def pair_experiment(data: dict, first: str, second: str,
                    reps: int = 2048, seed: int = 20261118) -> dict:
    dist = data["distance_mpc"]
    m1,m2 = data["mu"][first],data["mu"][second]
    e1,e2 = data["err"][first],data["err"][second]
    ok = (np.isfinite(dist)&(dist>0)&np.isfinite(m1)&np.isfinite(m2)
          &np.isfinite(e1)&np.isfinite(e2)&(e1>0)&(e2>0))
    dist,n,ids = dist[ok],data["n"][ok],data["id"][ok]
    y = m1[ok]-m2[ok]
    sigma = np.hypot(e1[ok],e2[ok])  # Working independence; unknown covariance!
    ell = np.log(dist); center,scale=float(ell.mean()),float(ell.std())
    F=features(dist,n,center,scale)
    w=1/sigma
    X0,Xa=F[:,:3]*w[:,None], F[:,3:]*w[:,None]
    fit=score_model(y*w,X0,Xa,ids,reps,seed)
    beta=np.asarray(fit["beta_full"])
    d,q=beta[3:6],beta[6:]
    rms=float(np.sqrt(np.sum(d*d)/3+2*np.sum(q*q)/15))
    allx=np.column_stack((X0,Xa))
    fit["overlap_groups"]=len(y)
    fit["difference_method"]=f"{first}-{second}"
    fit["mean_difference_mag"]=float(y.mean())
    fit["median_difference_mag"]=float(np.median(y))
    fit["median_stat_error_under_independence_mag"]=float(np.median(sigma))
    fit["angular_dipole_norm_mag"]=float(np.linalg.norm(d))
    fit["angular_stf_norm_mag"]=float(np.linalg.norm(q))
    fit["full_sky_model_angular_rms_mag"]=rms
    # The signed pointwise conversion is negative; RMS is nonnegative.
    fit["equivalent_lnH_angular_rms_if_fixed_redshift"]=np.log(10)/5*rms
    fit["matched_sample_angular_rms_mag"]=float(np.std(F[:,3:] @ beta[3:]))
    fit["design_diagnostics"]=design_diagnostics(allx)
    fit["group_id_sha256"]=hashlib.sha256(ids.tobytes()).hexdigest()
    fit["approx_covariance"]="diag(e1^2+e2^2) ONLY, shared method/systematic covariance not available"
    return fit


def grouped_network(data: dict, reps: int = 2048, seed: int = 20261119) -> dict:
    """Three-method, group-intercept-profiled Gaussian working model.

    FP is a method-label gauge reference, not a physically calibrated absolute anchor.
    Each multi-method group contributes m-1 orthonormal whitened contrasts, avoiding
    the false independence of its three pair differences.
    """
    d = data["distance_mpc"]
    mask = np.isfinite(d) & (d>0)
    for x in METHODS:
        mask &= True  # missing method handled within group, not a group exclusion
    many = np.column_stack([np.isfinite(data["mu"][x]) &
                            np.isfinite(data["err"][x]) &
                            (data["err"][x]>0) for x in METHODS])
    mask &= many.sum(axis=1)>=2
    ell=np.log(d[mask]);center,scale=float(ell.mean()),float(ell.std())
    allf=features(d[mask],data["n"][mask],center,scale)
    idxall=np.flatnonzero(mask)
    n_profiled = 0;Y=[];design=[];clusters=[]
    ntriple=0; method_graph={}
    for ii,f in zip(idxall,allf):
        present=[x for x in METHODS if many[ii,METHODS.index(x)]]
        if len(present)==3:ntriple+=1
        y=np.asarray([data["mu"][x][ii] for x in present])
        err=np.asarray([data["err"][x][ii] for x in present])
        # Whiten then remove one nuisance parameter shared by all method rows.
        inv=1/err
        w=inv/np.linalg.norm(inv)
        U=null_space(w[None,:])
        Xi=np.zeros((len(present),22))
        for j,x in enumerate(present):
            if x=="TF":Xi[j,:11]=f
            if x=="SN":Xi[j,11:]=f
        Xc=U.T@(inv[:,None]*Xi)
        yc=U.T@(inv*y)
        Y.extend(yc);design.extend(Xc);clusters.extend([int(data["id"][ii])]*len(yc))
        for a in present:
            for b in present:
                if a<b: method_graph[f"{a}-{b}"]=method_graph.get(f"{a}-{b}",0)+1
    z=np.asarray(Y);X=np.asarray(design);clusters=np.asarray(clusters)
    X0=np.column_stack((X[:,:3], X[:,11:14]))
    Xa=np.column_stack((X[:,3:11],X[:,14:22]))
    fit=score_model(z,X0,Xa,clusters,reps,seed)
    beta=np.asarray(fit["beta_full"]);tf=beta[6:14];sn=beta[14:22]
    fit["method_reference"]="FP=0 by method gauge; other methods TF, SN"
    fit["connected_group_count"]=len(idxall)
    fit["triple_method_groups"]=ntriple
    fit["method_overlap_edges"]=method_graph
    fit["profiled_shared_intercepts"]=len(idxall)
    fit["contrast_rows"]=len(z)
    fit["contrast_design"]=design_diagnostics(X)
    fit["angular_coefficients_method_relative_FP"]={"TF":tf.tolist(),"SN":sn.tolist()}
    fit["same_group_mean_cancels_exactly"]=True
    fit["known_covariance_limit"]="Working independent within-method errors; common upstream calibration covariances not supplied"
    return fit


def run(data_root: Path, out: Path, reps: int=2048, seed: int=20261118) -> dict:
    data=read_cf4_groups(data_root)
    results={}
    for j,(a,b) in enumerate((("FP","TF"),("FP","SN"),("TF","SN"))):
        results[f"{a}-{b}"]=pair_experiment(data,a,b,reps,seed+j)
    net=grouped_network(data,reps,seed+3)
    result={"schema":"htt.r67.cf4_method_contrast/1",
        "source":"CF4 full released group table3/table4, CDS J/ApJ/944/94",
        "source_sha256":data["source_sha256"],"original_group_count":len(data["id"]),
        "method_order":METHODS,"pairs":results,"network":net,
        "scientific_scope":"Observed cross-method relative calibration angular structure on same group; nuisance-cancelled, NOT physical global anisotropy detection.",
        "reference_limits":["Upstream group distance method zero points jointly calibrated by CF4", "No actual inter-method shared covariance or survey selection", "Group-wild bootstrap tests only declared group-independent symmetry", "Angular fit selected exploratory after previous study", "No independent cosmological p value"],
        "potential_physical_impact":"At fixed redshift, method-dependent Δµ maps to relative apparent Δln H=-(ln10/5)Δµ. Cosmological same-group mean cancels, not all source/population selection.",
        "bootstrap_count":reps}
    out.mkdir(parents=True,exist_ok=True)
    (out/"CF4_METHOD_CONTRAST.json").write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    return result
