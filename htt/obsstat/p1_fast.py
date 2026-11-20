"""R82 P1 source-coupled finite law preflight, optional C++/Fortran acceleration.

NOT a physical x_C posterior, source-calibrated cosmic null, or four independent
redshift windows. Original R78 science and R79/R81 fast lane remain unchanged.
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

from htt.obsstat.pre_dag_fast import analysis_lane_policy

ROOT=Path(__file__).resolve().parents[2]
_CONFIG=Path(__file__).with_name("p1_lane.json")
_SOURCES={"tails":Path(__file__).parent/"native"/"p1_joint_tails.cpp",
          "floor":Path(__file__).parent/"native"/"p1_floor_grid.f90"}
_RECEIPT=threading.local()


def last_p1_receipt():
    return dict(getattr(_RECEIPT,"last",{"used":"NOT_RUN"}))


def _receipt(**kw):
    _RECEIPT.last=dict(kw)


@lru_cache(maxsize=8)
def _compile_native(kind,source_sha):
    compiler=shutil.which("g++" if kind=="tails" else "gfortran")
    if compiler is None:
        raise RuntimeError("native_compiler_unavailable")
    flags=(["-O3","-std=c++17","-fPIC","-shared","-fopenmp",
            "-ffp-contract=off","-fno-fast-math"] if kind=="tails" else
           ["-O3","-fPIC","-shared","-fopenmp","-fno-fast-math"])
    version=subprocess.check_output([compiler,"--version"],text=True,timeout=10).splitlines()[0]
    key=hashlib.sha256((source_sha+str(flags)+version+platform.machine()).encode()).hexdigest()[:24]
    cached=Path(os.environ.get("HTT_NATIVE_CACHE_DIR",
                str(Path(tempfile.gettempdir())/"htt_r79_native_cache")))/"r82"/kind/key
    cached.mkdir(parents=True,exist_ok=True)
    lib=cached/("libhtt_r82_tails.so" if kind=="tails" else "libhtt_r82_floor.so")
    meta=cached/"manifest.json"
    with (cached/"lock").open("a+b") as fp:
        fcntl.flock(fp,fcntl.LOCK_EX)
        if lib.is_file() and meta.is_file():
            try:
                doc=json.loads(meta.read_text())
                if (doc.get("source_sha256")==source_sha and
                    doc.get("binary_sha256")==hashlib.sha256(lib.read_bytes()).hexdigest()):
                    return str(lib)
            except (OSError,TypeError,ValueError):
                pass
        temp=cached/f"pending_{os.getpid()}.so"
        try:
            subprocess.run([compiler,*flags,str(_SOURCES[kind]),"-o",str(temp)],
                           check=True,capture_output=True,text=True,timeout=90)
            if not temp.is_file() or temp.stat().st_size==0:
                raise RuntimeError("native_compiler_produced_no_binary")
            os.replace(temp,lib)
            meta.write_text(json.dumps({
                "kind":kind,"source_sha256":source_sha,
                "binary_sha256":hashlib.sha256(lib.read_bytes()).hexdigest(),
                "compiler":version,"flags":flags},sort_keys=True)+"\n")
        finally:
            if temp.exists():temp.unlink()
    return str(lib)


def _certified_native(kind):
    if kind not in _SOURCES:raise ValueError("unknown native P1 kernel")
    cfg=json.loads(_CONFIG.read_text())["kernels"][kind]
    dig=hashlib.sha256(_SOURCES[kind].read_bytes()).hexdigest()
    if dig!=cfg["source_sha256"]:
        raise RuntimeError(f"uncertified_{kind}_source_changed")
    lib=Path(_compile_native(kind,dig))
    meta=lib.with_name("manifest.json")
    if not lib.is_file() or not meta.is_file():
        raise RuntimeError("native binary or manifest missing")
    data=json.loads(meta.read_text())
    if data["source_sha256"]!=dig or data["binary_sha256"]!=hashlib.sha256(lib.read_bytes()).hexdigest():
        raise RuntimeError("cached native binary sha256 mismatch")
    return str(lib)


def _select(kind,requested,operations):
    if requested is None:return None,False,"explicit_numpy_reference"
    if requested!="auto":
        return str(requested),False,None
    policy=analysis_lane_policy()["mode"]
    if policy=="numpy":return None,False,"HTT_ANALYSIS_BACKEND_numpy"
    cfg=json.loads(_CONFIG.read_text())["kernels"][kind]
    if policy=="auto" and (not cfg["auto_enabled"] or operations<cfg["min_operations"]):
        return None,False,"not_admitted_or_small_input"
    try:return _certified_native(kind),True,None
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as e:
        if policy=="native":raise RuntimeError(f"required_native_{kind}_unavailable:{e}") from e
        return None,False,str(e)[:240]


def _common_weights(values,weights,*,allow_nan=False):
    q=np.asarray(values,dtype=float)
    if q.ndim!=2 or q.shape[1]!=4 or len(q)==0:
        raise ValueError("one joint (N,4) source array required")
    if np.isinf(q).any() or (not allow_nan and not np.isfinite(q).all()):
        raise ValueError("source array nonfinite")
    w=np.asarray(weights,dtype=float)
    if w.shape!=(len(q),) or not np.isfinite(w).all() or np.any(w<0):
        raise ValueError("one normalized nonnegative weight per original sample")
    if abs(float(np.sum(w,dtype=np.float64))-1)>1e-12:
        raise ValueError("joint source weights must sum to 1 including missing rows")
    return np.ascontiguousarray(q),np.ascontiguousarray(w)


def joint_tail_bounds(values,weights,thresholds,*,missing_codes=None,
                      sample_ids=None,native_lib="auto",threads=8):
    """Source-coupled strict finite-mass intervals [lower,upper], not physical Pi.

    Code 0 known finite, code 1 unmeasured_defined, code 2 domain_uncertified.
    Source windows remain coupled on one row and original all-row masses.
    """
    q,w=_common_weights(values,weights,allow_nan=True)
    if missing_codes is None:
        code=np.zeros(q.shape,dtype=np.int8)
    else:
        x=np.asarray(missing_codes)
        if x.shape!=q.shape or not np.issubdtype(x.dtype,np.integer):
            raise ValueError("explicit 0/1/2 missing reason code required")
        if np.any((x<0)|(x>2)):
            raise ValueError("invalid P1 missing reason")
        code=np.ascontiguousarray(x,dtype=np.int8)
    if (not np.isfinite(q[code==0]).all() or
        not np.isnan(q[code!=0]).all()):
        raise ValueError("known must be finite; unknown must be NaN with typed reason")
    if sample_ids is not None:
        ids=np.asarray(sample_ids)
        if ids.shape!=(len(q),) or len(set(map(str,ids)))!=len(ids):
            raise ValueError("source sample IDs must be unique and 1:1")
    t=np.asarray(thresholds,dtype=float)
    if t.ndim!=1 or len(t)==0 or not np.isfinite(t).all() or np.any(np.diff(t)<=0):
        raise ValueError("strict increasing finite thresholds required")
    if not isinstance(threads,int) or not (1<=threads<=32):
        raise ValueError("native threads 1..32")
    t=np.ascontiguousarray(t)
    native,certified,reason=_select("tails",native_lib,len(t)*len(q))
    if native is not None:
        fn=ctypes.CDLL(str(Path(native).resolve())).htt_p1_joint_tail_v1
        f8=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        i8=np.ctypeslib.ndpointer(dtype=np.int8,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,ctypes.c_int64,f8,f8,i8,f8,ctypes.c_int32,f8]
        fn.restype=ctypes.c_int
        out=np.empty((len(t),2,6),float)
        status=fn(len(q),len(t),q,w,code,t,threads,out)
        if status or not np.isfinite(out).all():
            _receipt(used="native_failed",kernel="tails",code=status)
            raise RuntimeError(f"native P1 strict tail failed status={status}")
        low,up=out[:,0,:],out[:,1,:]
        used="cpp_native_tails"
    else:
        low=np.empty((len(t),6));up=np.empty_like(low)
        known=(code==0)
        for k,thr in enumerate(t):
            yes=known & (q>thr)
            no=known & (q<=thr)
            low[k,:4]=w@yes
            up[k,:4]=w@(~no)
            low[k,4]=w@np.any(yes,axis=1)
            up[k,4]=w@(~np.all(no,axis=1))
            low[k,5]=w@np.all(yes,axis=1)
            up[k,5]=w@(~np.any(no,axis=1))
        used="numpy_reference"
    if np.any(low<-1e-12) or np.any(up>1+1e-12) or np.any(low>up+1e-12):
        raise RuntimeError("P1 event bounds violate finite probability mass")
    _receipt(used=used,kernel="joint_tails",source_certified=certified,
             n_rows=len(q),n_thresholds=len(t),threads=threads if native else 0,
             fallback_reason=reason)
    def masses(reason_code):
        return [float(w@(code[:,j]==reason_code)) for j in range(4)]
    return {"lower":low,"upper":up,"thresholds":t,
            "unknown_mass_per_window":[float(w@(code[:,j]!=0)) for j in range(4)],
            "missing_unmeasured_mass_per_window":masses(1),
            "missing_uncertified_mass_per_window":masses(2),
            "source_count":len(q),"joint_weight_sum":float(w.sum()),
            "four_windows_shared_sample_ID":True,
            "physical_Pi":None,
            "bound_interpretation":"pointwise finite logical completions only; no physics admission"}


def floor_depth_grid(values,weights,anchors,floors,*,native_lib="auto",threads=8):
    """Apparent depth-ratio sensitivity, not a physical sky occupancy G_F."""
    q,w=_common_weights(values,weights)
    if np.any(q<0):raise ValueError("original apparent norms must be nonnegative")
    a=np.asarray(anchors,dtype=float)
    f=np.asarray(floors,dtype=float)
    if (a.ndim!=1 or f.ndim!=1 or not len(a) or not len(f) or
        not np.isfinite(a).all() or not np.isfinite(f).all() or
        np.any(a<=0) or np.any(f<=0)):
        raise ValueError("positive finite anchor/floor arrays required")
    if not isinstance(threads,int) or not (1<=threads<=32):
        raise ValueError("native threads 1..32")
    a=np.ascontiguousarray(a);f=np.ascontiguousarray(f)
    native,certified,reason=_select("floor",native_lib,len(q)*len(a)*len(f))
    if native is not None:
        fn=ctypes.CDLL(str(Path(native).resolve())).htt_p1_floor_grid_v1
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,ctypes.c_int64,ctypes.c_int64,
                     fp,fp,fp,fp,ctypes.c_int32,fp,ctypes.POINTER(ctypes.c_int)]
        fn.restype=None
        out=np.empty((len(a),len(f),3,3),dtype=float)
        status=ctypes.c_int(-1)
        fn(len(q),len(a),len(f),q,w,a,f,threads,out,ctypes.byref(status))
        if status.value or not np.isfinite(out).all():
            _receipt(used="native_failed",kernel="floor",code=status.value)
            raise RuntimeError(f"native P1 floor-grid failed status={status.value}")
        used="fortran_native_floor"
    else:
        out=np.empty((len(a),len(f),3,3),float)
        for i,anchor in enumerate(a):
            for j,floor in enumerate(f):
                threshold=anchor*floor
                z=np.maximum(q[:,1:],threshold)/np.maximum(q[:,:1],threshold)
                out[i,j,:,0]=w@(z>1)
                out[i,j,:,1]=w@(z==1)
                out[i,j,:,2]=w@z
        used="numpy_reference"
    _receipt(used=used,kernel="floor",source_certified=certified,
             n_rows=len(q),n_anchor=len(a),n_floor=len(f),
             threads=threads if native else 0,fallback_reason=reason)
    return {"strict_above_one":out[:,:,:,0],"tie_one":out[:,:,:,1],
            "mean_ratio":out[:,:,:,2],
            "physical_GF":None,"source_unit":"one coupled 4-window sample ID",
            "floor_is_apparent_not_physical":True}


def historical_evidence_21_30():
    """Read-only original source manifest, not a new source or physics claim."""
    pub=json.loads((ROOT/"docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json").read_text())
    dag=json.loads((ROOT/"docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json").read_text())
    checksum=hashlib.sha256(json.dumps(pub["nodes"],sort_keys=True).encode()).hexdigest()
    if checksum!=dag["original_42_payload_sha256"]:
        raise RuntimeError("original 42-node scientific payload changed")
    n={x["id"]:x for x in pub["nodes"]}
    subset=("E2","E3","X01","X02","X03","S01","S02","S03","S04","S05")
    source={
        "E2":ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/results_v2/result.json",
        "E3":ROOT/"htt/htt/htt/departure/posterior_pushforward.py",
        "X01":ROOT/"docs/research_program/observational_publication_20261015/READY_20261016/X01_SOURCE_BINDINGS.json",
        "X02":ROOT/"docs/research_program/observational_publication_20261015/X02_20261016/X02_NOVELTY_MATRIX.md",
        "X03":ROOT/"docs/research_program/observational_publication_20261015/READY_20261016/X03_CLAIM_SELECTION_LEDGER.json",
        "S01":ROOT/"htt/obsstat/publication_functionals.py"}
    hashes={}
    for name,path in source.items():
        if not path.is_file():raise FileNotFoundError(f"{name}: historical evidence missing {path}")
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    e2=json.loads(source["E2"].read_text())
    x03=json.loads(source["X03"].read_text())
    if e2["same_sky_map_count"]!=9 or e2["nside64_selected_T_same_mask_n"]!=26846:
        raise ValueError("historical Planck MES source record drift")
    if n["S02"]["state"]!="blocked_input" or any(n[i]["state"]!="completed_scoped" for i in subset[:6]):
        raise ValueError("science DAG scope and blocked source state changed")
    return {"science_nodes":{i:n[i]["state"] for i in subset},
            "original_42_nodes_sha256":checksum,
            "source_sha256":hashes,"E2_planck_same_sky_maps":e2["same_sky_map_count"],
            "E2_planck_selected_pixels":e2["nside64_selected_T_same_mask_n"],
            "X03_new_observational_null":x03["prospective_new_null"]["current_state"],
            "physical_claim_upgrade":False,"original_R78_science_status_changed":False,
            "actual_observed_physical_x_C":False}
