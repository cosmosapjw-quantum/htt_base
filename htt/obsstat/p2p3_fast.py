"""R83 Planck P2 / CF4 P3 source-coherent numerical preparation.

All source outputs are CONDITIONAL. No independent Planck nine-sky likelihood,
missing FFP10 matched null, or physical H(z,n)/PV covariance is inferred.
"""
from __future__ import annotations

import ctypes
import fcntl
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from htt.obsstat.pre_dag_fast import analysis_lane_policy

ROOT=Path(__file__).resolve().parents[2]
_SOURCE=Path(__file__).parent/"native"/"p3_multiwindow_info.cpp"
_POLICY=Path(__file__).with_name("p2p3_lane.json")
_RECEIPT=threading.local()


def _receipt(**items):
    _RECEIPT.value=items


def last_p2p3_receipt():
    return dict(getattr(_RECEIPT,"value",{"used":"NOT_RUN"}))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


@lru_cache(maxsize=4)
def _compile_certified(sha_source):
    compiler=shutil.which("g++")
    if compiler is None:raise RuntimeError("g++ compiler missing")
    flags=["-O3","-std=c++17","-fPIC","-shared","-fopenmp",
           "-ffp-contract=off","-fno-fast-math"]
    version=subprocess.check_output([compiler,"--version"],text=True,timeout=10).splitlines()[0]
    key=hashlib.sha256((sha_source+str(flags)+version+platform.machine()).encode()).hexdigest()[:24]
    parent=Path(os.environ.get("HTT_NATIVE_CACHE_DIR",
                       str(Path(tempfile.gettempdir())/"htt_r79_native_cache")))/"r83"/key
    parent.mkdir(parents=True,exist_ok=True)
    lib=parent/"libhtt_r83_multiwindow.so"
    manifest=parent/"manifest.json"
    with (parent/"lock").open("a+b") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if lib.exists() and manifest.exists():
            try:
                m=json.loads(manifest.read_text())
                if m["source_sha256"]==sha_source and m["binary_sha256"]==sha(lib):
                    return str(lib)
            except (ValueError,KeyError,OSError,TypeError):
                pass
        tmp=parent/f"staging_{os.getpid()}.so"
        try:
            subprocess.run([compiler,*flags,str(_SOURCE),"-o",str(tmp)],
                           check=True,capture_output=True,text=True,timeout=90)
            if not tmp.is_file() or tmp.stat().st_size==0:
                raise RuntimeError("compiled empty native artifact")
            os.replace(tmp,lib)
            manifest.write_text(json.dumps({
                "source_sha256":sha_source,"binary_sha256":sha(lib),
                "compiler":version,"flags":flags},sort_keys=True)+"\n")
        finally:
            if tmp.exists():tmp.unlink()
    return str(lib)


def _certified_native():
    cfg=json.loads(_POLICY.read_text())
    src_sha=sha(_SOURCE)
    if cfg["source_sha256"]!=src_sha:
        raise RuntimeError("R83 source hash differs from tested native certificate")
    lib=Path(_compile_certified(src_sha))
    manifest=lib.with_name("manifest.json")
    if not lib.is_file() or not manifest.is_file():
        raise RuntimeError("R83 source/binary manifest missing")
    m=json.loads(manifest.read_text())
    if m["source_sha256"]!=src_sha or m["binary_sha256"]!=sha(lib):
        raise RuntimeError("R83 cached binary integrity mismatch")
    return str(lib)


def _choose_native(requested,n,threads):
    if requested is None:return None,False,"explicit_numpy_reference"
    if requested!="auto":return str(requested),False,None
    mode=analysis_lane_policy()["mode"]
    if mode=="numpy":return None,False,"HTT_ANALYSIS_BACKEND_numpy"
    cfg=json.loads(_POLICY.read_text())
    if mode=="auto" and (not cfg["auto_enabled"] or n<cfg["min_sources"]):
        return None,False,"source_benchmark_numpy_selected_or_small"
    try:return _certified_native(),True,None
    except (RuntimeError,ValueError,OSError,subprocess.SubprocessError) as e:
        if mode=="native":raise RuntimeError(f"R83 required certified native unavailable: {e}") from e
        return None,False,str(e)[:200]


def _check_matrix(X,y,weights,sigma):
    X=np.asarray(X,dtype=np.float64)
    y=np.asarray(y,dtype=np.float64)
    w=np.asarray(weights,dtype=np.float64)
    s=np.asarray(sigma,dtype=np.float64)
    if X.ndim!=2 or X.shape[1]!=9 or len(X)<20 or y.shape!=(len(X),) or w.shape!=(len(X),4) or s.shape!=(len(X),):
        raise ValueError("H03 requires (N,9) X, N y, (N,4) window weights and N working sigma")
    if not all(np.isfinite(v).all() for v in (X,y,w,s)) or np.any(w<0) or np.any(s<=0):
        raise ValueError("nonfinite/negative WLS weights or nonpositive source velocity scatter")
    if np.any(np.count_nonzero(w,axis=0)<10):
        raise ValueError("H03 fewer than ten supported source groups per window")
    return tuple(np.ascontiguousarray(x) for x in (X,y,w,s))


def four_window_working_gls(X,y,weights,sigma,*,native_lib="auto",threads=4,cond_limit=1e10):
    """Exact conditional H03 shared-source 4x9 GLS and full 36x36 covariance.

    C_jk = F_j^{-1}(X^T diag(w_j w_k sigma^2) X)F_k^{-1}. The only
    admitted noise law is the ORIGINAL diagonal working-group sigma.
    """
    X,y,w,s=_check_matrix(X,y,weights,sigma)
    n,p=X.shape
    if not isinstance(threads,int) or not 1<=threads<=32:
        raise ValueError("native workers must be 1..32")
    if not np.isfinite(cond_limit) or cond_limit<=1:
        raise ValueError("finite normal-information condition limit required")
    path,certified,fallback=_choose_native(native_lib,n,threads)
    F=np.empty((4,p,p),dtype=float)
    B=np.empty((4,p),dtype=float)
    if path is not None:
        fn=ctypes.CDLL(str(Path(path).resolve())).htt_p3_multiwindow_info_v1
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,ctypes.c_int32,ctypes.c_int32,fp,fp,fp,
                     ctypes.c_int32,fp,fp]
        fn.restype=ctypes.c_int
        status=fn(n,p,4,X,w,y,threads,F,B)
        if status or not np.isfinite(F).all() or not np.isfinite(B).all():
            _receipt(used="native_failed",status=status,source_certified=certified)
            raise RuntimeError(f"R83 native multiwindow WLS source reduction failed {status}")
        used="cpp_native_info"
    else:
        for j in range(4):
            W=w[:,j]
            F[j]=X.T@(W[:,None]*X)
            B[j]=X.T@(W*y)
        used="numpy_blas_source"
    invs=[]
    theta=np.empty((4,p))
    condition=[]
    for j in range(4):
        fj=.5*(F[j]+F[j].T)
        ev=np.linalg.eigvalsh(fj)
        if ev[0]<=0 or ev[-1]/ev[0]>cond_limit:
            raise ValueError("H03 source weighted rank/SPD/condition gate violated")
        condition.append(float(ev[-1]/ev[0]))
        fac=cho_factor(fj,lower=True,check_finite=False)
        inv=cho_solve(fac,np.eye(p),check_finite=False)
        theta[j]=cho_solve(fac,B[j],check_finite=False)
        invs.append(inv)
    # Shared 35,970 same-group conditional covariance, NO full N x N matrix.
    C=np.zeros((4*p,4*p),float)
    sig2=s*s
    for j in range(4):
        for k in range(j,4):
            source_w=w[:,j]*w[:,k]*sig2
            G=X.T@(source_w[:,None]*X)
            block=invs[j]@G@invs[k].T
            C[j*p:(j+1)*p,k*p:(k+1)*p]=block
            C[k*p:(k+1)*p,j*p:(j+1)*p]=block.T
    C=(C+C.T)*.5
    C_ev=np.linalg.eigvalsh(C)
    if C_ev[0]<-1e-10*max(1,float(np.linalg.norm(C,2))):
        raise ValueError("H03 conditional covariance violates source PSD")
    _receipt(used=used,source_certified=certified,n_sources=n,
             n_windows=4,features=p,workers=threads if path else 0,
             fallback_reason=fallback)
    return {"F":F,"score":B,"theta":theta,"joint_cov":C,
            "condition_normal":condition,
            "real_physical_H_z_n":None,
            "full_source_PV_calibration_selection_C":None,
            "source_claim_tier":"H03_CF4_GROUP_CONDITIONAL_DIAGONAL_WORKING_NOISE"}


def working_rank_interval(observed,null_values,*,simulation_ids,null_qualified=False):
    """Arithmetic finite rank with ties; never qualified physical p here."""
    if null_qualified:
        raise ValueError("R83 cannot qualify an actual Planck matched null using pilot or caller flag")
    obs=float(observed)
    x=np.asarray(null_values,dtype=float)
    ids=list(map(str,simulation_ids))
    if not np.isfinite(obs) or x.ndim!=1 or not len(x) or not np.isfinite(x).all():
        raise ValueError("finite scalar observed statistic and one finite value per original simulation ID")
    if len(ids)!=len(x) or len(set(ids))!=len(ids):
        raise ValueError("independent simulation IDs not unique or mismatched")
    greater=int(np.count_nonzero(x>obs))
    ge=int(np.count_nonzero(x>=obs))
    n=len(x)
    return {"simulation_count":n,"higher_than_observed":greater,
            "greater_or_equal":ge,"rank_interval":[(greater+1)/(n+1),(ge+1)/(n+1)],
            "rank_resolution":1/(n+1),
            "physical_p_value":None,"source_null_qualified":False,
            "rank_interpretation":"pilot arithmetic only; exchangeability and end-to-end null not established"}


def family_rank_interval(observed,simulations,*,simulation_ids,null_qualified=False):
    """Fix a predeclared extreme family; ONE score per genuine simulation ID."""
    obs=np.asarray(observed,dtype=float)
    sims=np.asarray(simulations,dtype=float)
    if obs.ndim!=2 or sims.ndim!=3 or sims.shape[1:]!=obs.shape:
        raise ValueError("observed (variants,features), null (IDs,variants,features) required")
    if not np.isfinite(obs).all() or not np.isfinite(sims).all():
        raise ValueError("nonfinite family statistics")
    result=working_rank_interval(float(np.max(obs)),sims.max(axis=(1,2)),
                                simulation_ids=simulation_ids,null_qualified=null_qualified)
    result.update(processing_variants=obs.shape[0],features=obs.shape[1],
                  family_statistic="max_over_selected_family_within_simulation_ID")
    return result


def historical_planck_science_status():
    """Read and type actual L02/L03 and R78, not nine independent skies."""
    root=ROOT/"docs/research_program/observational_publication_20261015"
    l02=root/"CONTINUATION_20261018/L02_EXECUTION_20261018/results/L02_ACTUAL_STATISTICS.json"
    l03=root/"CONTINUATION_20261018/L03_EXECUTION_20261018/results/L02_ON_EIGHT_PAIR_PILOT.json"
    dag=root/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
    a,b,g=[json.loads(p.read_text()) for p in (l02,l03,dag)]
    fields=a["field_rows"]
    if len(fields)!=25 or len(a["same_product_cross_fields"])!=24:
        raise ValueError("L02 original signed morphology source count drift")
    if {x["sky_id"] for x in fields}!={"ONE_PHYSICAL_PLANCK_SKY"}:
        raise ValueError("L02 source variant sky identifiers not common")
    ids=list(b["independent_pair_ids"])
    rows=list(b["rows"])
    if len(ids)!=8 or len(set(ids))!=8 or len(rows)!=40:
        raise ValueError("L03 pilot identity count mismatch")
    variants=set(x["variant"] for x in rows)
    if len(variants)!=5:
        raise ValueError("L03 original five processing variants missing")
    for ident in ids:
        selected=[x for x in rows if x["simulation_id"]==ident]
        if len(selected)!=5 or {x["variant"] for x in selected}!=variants:
            raise ValueError("L03 pilot variants are not 1:1 by paired simulation ID")
    signed_negative=False
    for row in fields:
        for key,v in row["SO3_signed"].items():
            if isinstance(v,(float,int)) and np.isfinite(v):
                w=row["O3_summaries"][key]
                if isinstance(w,(float,int)):
                    # Source L02 parity table: B is an axial STF field.
                    # Its chirality is O(3)-even and MUST RETAIN its sign.
                    # T/E chirality is O(3)-odd and has |h|. All s summaries
                    # use |s|. See source STATISTIC_FAMILY.md, not an
                    # indiscriminate abs() transformation.
                    expected=(float(v) if key=="chirality" and row["field"]=="B"
                              else abs(float(v)))
                    if abs(expected-float(w))>4e-13:
                        raise ValueError("L02 field-specific polar/axial O3 parity mismatch")
                signed_negative|=v<0
    nodes={x["id"]:x["state"] for x in g["nodes"]}
    return {"L02_fields":len(fields),"L02_same_sky_pairs":len(a["same_product_cross_fields"]),
            "one_physical_observed_sky":True,
            "L02_signed_vs_absolute_parity_verified":True,
            "L02_negative_signed_shapes_preserved":bool(signed_negative),
            "L03_pilot_pair_ids":len(ids),"L03_variants_per_pair":len(variants),
            "L03_complete_source_matched_null_qualified":False,
            "L04_physical_p_value":None,
            "R78_science_next_ID":g["next_action_id"],
            "R78_original_science_states_changed":False,
            "science_nodes":{k:nodes[k] for k in ("S06","L01","L02","L03","L04","L05","L06","H01","H02","H03")},
            "actual_correlated_PV_calibration_selection_C":None,
            "real_physical_H_z_n":None,
            "source_sha256":{str(path):sha(path) for path in (l02,l03,dag)}}
