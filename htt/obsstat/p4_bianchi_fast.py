"""R84 H04-H06/V01-V06/B01 source-conditional numerical preflight.

This does NOT identify the physical local/global observer velocity, measure a
full transport GF, qualify PV/selection covariance, or create a matched null.
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
from scipy.linalg import solve_triangular

from htt.obsstat.pre_dag_fast import analysis_lane_policy, codazzi_map

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).parent/"native"/"p4_conditional_axis_scan.f90"
POLICY=Path(__file__).with_name("p4_lane.json")
_RECEIPT=threading.local()


def _digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def _receipt(**obj):
    _RECEIPT.value=obj


def last_p4_receipt():
    return dict(getattr(_RECEIPT,"value",{"used":"NOT_RUN"}))


@lru_cache(maxsize=6)
def _compile_native(src_sha):
    compiler=shutil.which("gfortran")
    if compiler is None:
        raise RuntimeError("gfortran unavailable")
    flags=["-O3","-fPIC","-shared","-fopenmp","-fno-fast-math"]
    version=subprocess.check_output([compiler,"--version"],text=True,timeout=10).splitlines()[0]
    key=hashlib.sha256((src_sha+str(flags)+version+platform.machine()).encode()).hexdigest()[:24]
    parent=Path(os.environ.get("HTT_NATIVE_CACHE_DIR",
        str(Path(tempfile.gettempdir())/"htt_r79_native_cache")))/"r84"/key
    parent.mkdir(parents=True,exist_ok=True)
    so=parent/"libhtt_r84_masked_score.so"
    mf=parent/"manifest.json"
    with (parent/"lock").open("a+b") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if so.is_file() and mf.is_file():
            try:
                meta=json.loads(mf.read_text())
                if meta["source_sha256"]==src_sha and meta["binary_sha256"]==_digest(so):
                    return str(so)
            except (OSError,KeyError,TypeError,ValueError):
                pass
        tmp=parent/f"temp_{os.getpid()}.so"
        try:
            subprocess.run([compiler,*flags,str(SOURCE),"-o",str(tmp)],
                           capture_output=True,text=True,timeout=90,check=True)
            if not tmp.is_file() or not tmp.stat().st_size:
                raise RuntimeError("Fortran compiler returned empty source binary")
            os.replace(tmp,so)
            mf.write_text(json.dumps({
                "source_sha256":src_sha,"binary_sha256":_digest(so),
                "compiler":version,"flags":flags},sort_keys=True)+"\n")
        finally:
            if tmp.exists():tmp.unlink()
    return str(so)


def _certified_native():
    cfg=json.loads(POLICY.read_text())
    sha=_digest(SOURCE)
    if sha!=cfg["source_sha256"]:
        raise RuntimeError("uncertified_R84_Fortran_source_SHA_changed")
    binary=Path(_compile_native(sha))
    receipt=binary.with_name("manifest.json")
    if not binary.is_file() or not receipt.is_file():
        raise RuntimeError("R84 certified binary and manifest unavailable")
    meta=json.loads(receipt.read_text())
    if meta["source_sha256"]!=sha or meta["binary_sha256"]!=_digest(binary):
        raise RuntimeError("R84 cached native binary SHA mismatch")
    return str(binary)


def _as_float(value,name,ndim=None):
    x=np.asarray(value,dtype=np.float64)
    if (ndim is not None and x.ndim!=ndim) or not np.isfinite(x).all():
        raise ValueError(f"{name}: finite float64 {ndim}D array required")
    return np.ascontiguousarray(x)


def _unit_vectors(value,name):
    x=_as_float(value,name,2)
    if x.shape[1:]!=(3,) or len(x)==0 or np.max(abs(np.einsum("ij,ij->i",x,x)-1))>2e-10:
        raise ValueError(f"{name}: nonempty Cartesian unit (N,3) vectors required")
    return x


def prepare_ring_source(directions,groups,counts,velocity_xy,k,*,beta=None):
    """Exact original R74 within-ring conditional source weights and score.

    Three bins, original 185 ring totals, baseline signed 2D dipole coefficients
    and k response; beta is optional small SOURCE-CONTROLLED model perturbation.
    """
    n=_unit_vectors(directions,"R65 source directions")
    N=len(n)
    g=np.asarray(groups)
    if g.ndim!=1 or g.shape!=(N,) or not np.issubdtype(g.dtype,np.integer):
        raise ValueError("ring labels must be integer per source pixel")
    g=np.ascontiguousarray(g,dtype=np.int64)
    unique=np.unique(g)
    if len(unique)<1 or not np.array_equal(unique,np.arange(len(unique))):
        raise ValueError("ring IDs must be contiguous zero-based and all populated")
    nb=len(unique)
    c=_as_float(counts,"source pixel count by flux band",2)
    if c.shape!=(3,N) or np.any(c<0):
        raise ValueError("actual 3-band nonnegative source counts required")
    k=_as_float(k,"source fixed k",1)
    v=_as_float(velocity_xy,"original signed 2D fitted count dipoles",2)
    if v.shape!=(3,2) or k.shape!=(3,) or np.any(k<=0):
        raise ValueError("3 bands k and Vxy must follow original source response")
    b=np.zeros(3) if beta is None else _as_float(beta,"conditional small beta",1)
    if b.shape!=(3,) or b@b>=1:
        raise ValueError("source beta perturbation must have |beta|<1")
    w=np.empty((N,3),dtype=float)
    score=np.empty((N,3,3),dtype=float)
    for band in range(3):
        totals=np.bincount(g,weights=c[band],minlength=nb)
        sum_counts=float(totals.sum())
        if not np.isfinite(sum_counts) or sum_counts<=0 or np.any(totals<0):
            raise ValueError("invalid original fixed ring selected counts")
        logw=n[:,:2]@v[band]+float(k[band])*(n@b)
        for ring in range(nb):
            ids=np.flatnonzero(g==ring)
            local=logw[ids]
            expo=np.exp(local-local.max())
            p=expo/expo.sum()
            a=(totals[ring]/sum_counts)*p
            w[ids,band]=a
            mu=p@n[ids]
            score[ids,band,:]=float(k[band])*a[:,None]*(n[ids]-mu[None,:])
    for band in range(3):
        if abs(w[:,band].sum()-1)>2e-12:
            raise RuntimeError("conditional ring weights fail source normalization")
        if np.linalg.norm(score[:,band].sum(axis=0))>3e-12:
            raise RuntimeError("within-ring profiled source score does not cancel on full sky")
    return {"weight":np.ascontiguousarray(w),
            "score":np.ascontiguousarray(score),
            "ring_count":nb,"fixed_source_k":k,"beta":b,
            "original_source_count":N,
            "source_role":"R65/R74 fixed ring counts, conditional first-order beta-score, not physical beta"}


def batch_ring_occ(directions,axes,prepared,*,native_lib="auto",threads=12,block=32):
    n=_unit_vectors(directions,"source directions")
    a=_unit_vectors(axes,"hemisphere axes")
    W=_as_float(prepared["weight"],"three band weights",2)
    S=_as_float(prepared["score"],"three band score",3)
    if W.shape!=(len(n),3) or S.shape!=(len(n),3,3):
        raise ValueError("precomputed weights and source scores inconsistent with source")
    if np.any(W<0) or not np.allclose(W.sum(axis=0),1,atol=2e-12,rtol=0):
        raise ValueError("original source weights no longer normalized")
    if np.max(np.abs(S.sum(axis=0)))>3e-12:
        raise ValueError("ring conditional score is not full-sky centered")
    if not isinstance(threads,int) or threads<1 or threads>32:
        raise ValueError("native threads must be in [1,32]")
    if not isinstance(block,int) or block<1 or block>512:
        raise ValueError("source batch chunk size 1..512 required")
    mode=analysis_lane_policy()["mode"]
    path=None;cert=False;fallback=None
    if native_lib is None or (native_lib=="auto" and mode=="numpy"):
        fallback="explicit_numpy_reference" if native_lib is None else "HTT_ANALYSIS_BACKEND_numpy"
    elif native_lib!="auto":
        path=str(native_lib)
    else:
        config=json.loads(POLICY.read_text())
        if mode=="auto" and (not config["auto_enabled"] or len(n)*len(a)<config["min_operations"]):
            fallback="small_or_unproven_source_numerics"
        else:
            try:
                path=_certified_native();cert=True
            except (OSError,RuntimeError,ValueError,subprocess.SubprocessError) as exc:
                if mode=="native":
                    raise RuntimeError(f"required certified R84 Fortran unavailable: {exc}") from exc
                fallback=str(exc)[:220]
    if path:
        lib=ctypes.CDLL(str(Path(path).resolve()))
        fun=lib.htt_p4_masked_source_score_v1
        f8=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fun.argtypes=[ctypes.c_int64,ctypes.c_int64,f8,f8,f8,f8,ctypes.c_int32,f8,
                      ctypes.POINTER(ctypes.c_int)]
        fun.restype=None
        dest=np.empty((len(a),3,4),dtype=np.float64)
        status=ctypes.c_int(-1)
        fun(len(n),len(a),n,a,W,S,threads,dest,ctypes.byref(status))
        if status.value or not np.isfinite(dest).all():
            _receipt(used="native_failed",status=status.value)
            raise RuntimeError(f"R84 native 3-band source score failed {status.value}")
        F=dest[:,:,0]
        grad=dest[:,:,1:]
        used="fortran_native_ring_score"
    else:
        F=np.empty((len(a),3),float)
        grad=np.empty((len(a),3,3),float)
        flat=S.reshape(len(n),9)
        for i in range(0,len(a),block):
            mask=np.ascontiguousarray((n@a[i:i+block].T)>0,dtype=float)
            F[i:i+block]=mask.T@W
            grad[i:i+block]=(mask.T@flat).reshape(-1,3,3)
        used="numpy_block_blas_ring_score"
    if np.min(F)<-1e-12 or np.max(F)>1+1e-12:
        raise RuntimeError("R84 source-conditional occupancy outside [0,1]")
    _receipt(used=used,n_pixels=len(n),n_axes=len(a),source_certified=cert,
             threads=threads if path else 0,binary_path=path,fallback_reason=fallback)
    return {"F":F,"gradient":grad,"source_meaning":prepared["source_role"],
            "physical_beta_measured":False,"physical_Pi":None,
            "actual_physical_GF":None}


def source_conditional_local_global_rank(local,global_response,covariance,*,rtol=1e-10):
    """Rank after whitening and projecting out already supplied local columns."""
    L=_as_float(local,"local source response",2)
    G=_as_float(global_response,"global source response",2)
    C=_as_float(covariance,"shared-source covariance",2)
    if L.shape[0]!=G.shape[0] or C.shape!=(len(L),len(L)) or L.shape[1]<1 or G.shape[1]<1:
        raise ValueError("local/global response/covariance shape mismatch")
    if not np.allclose(C,C.T,atol=1e-11,rtol=1e-11):
        raise ValueError("source covariance not symmetric")
    if not 0<rtol<.1:
        raise ValueError("bounded singular value rank criterion required")
    try:
        chol=np.linalg.cholesky(C)
    except np.linalg.LinAlgError as exc:
        raise ValueError("source covariance not SPD") from exc
    A=solve_triangular(chol,L,lower=True,check_finite=False)
    B=solve_triangular(chol,G,lower=True,check_finite=False)
    u,s,_=np.linalg.svd(A,full_matrices=False)
    rank=int(np.sum(s>max(s[0]*rtol,1e-14)))
    Q=u[:,:rank]
    projected=B-Q@(Q.T@B)
    sing=np.linalg.svd(projected,compute_uv=False)
    new_rank=int(np.sum(sing>max(np.linalg.svd(B,compute_uv=False)[0]*rtol,1e-14)))
    return {"rank_local":rank,"rank_increment_global":new_rank,
            "projected_global_singular_values":sing.tolist(),
            "physical_tilt_identified":False,"physical_Pi":None,
            "source_qualification":"requires independent same-frame local/global transfer and true noise/null"}


def validate_bianchi_registry():
    """Class A/B sign representatives and exceptional VI_-1/9 source geometry."""
    root=ROOT/"docs/research_program/observational_publication_20261015"
    b=json.loads((root/"READY_20261016/B01_BIANCHI_ATLAS_REGISTRY.json").read_text())
    v=json.loads((root/"R75_P5_LIE_TILT_FIVEVIEW_20261119/RESULTS.json").read_text())
    rows=[]
    valid=True
    for entry in b["canonical_types"]:
        a=np.asarray(entry["Lie_axis_representative_a"],float)
        N=np.diag(np.asarray(entry["Lie_sign_representative_n_diag"],float))
        jac=abs(a@N@a) if False else float(np.linalg.norm(N@a))
        valid &= jac<1e-13
        M=codazzi_map(a,N)
        rank=int(np.linalg.matrix_rank(M,tol=1e-11))
        if entry["class"]=="A" and np.linalg.norm(a)>0:
            raise ValueError("Bianchi Class A source a must vanish")
        if entry["class"]=="B" and np.linalg.norm(a)==0:
            raise ValueError("Bianchi Class B source a must be nonzero")
        rows.append({"type":entry["type"],"class":entry["class"],
                     "Jacobi_N_dot_a_residual":jac,"Lie_codazzi_rank":rank,
                     "polarized_all_m_source_qualified":bool(entry["T_E_B_high_l_all_m_qualified"])})
    if len(rows)!=11 or len({x["type"] for x in rows})!=11 or not valid:
        raise ValueError("Bianchi original 11 canonical Lie source registry invalid")
    exc=b["exceptional_VI_minus_1_over_9"]
    original=v["source_all_Bianchi_atlas"]["VI_minus_1_over_9"]
    return {"canonical_count":11,"canonical":rows,"all_Jacobi_N_a_zero":bool(valid),
            "exceptional_VI_minus_1_over_9":{"distinct_twelfth_type":bool(exc["distinct_twelfth_type"]),
               "h":exc["h"],"source_specific_rank":int(original["Codazzi_signed_STF5_to_normal_flux_rank"])},
            "external_all_m_polarization_verified":False,"physical_Bianchi_family_identified":False}


def historical_41_50_status():
    root=ROOT/"docs/research_program/observational_publication_20261015"
    unified=json.loads((root/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json").read_text())
    original=json.loads((root/"PUBLICATION_DAG.json").read_text())
    payload=hashlib.sha256(json.dumps(original["nodes"],sort_keys=True).encode()).hexdigest()
    if payload!=unified["original_42_payload_sha256"]:
        raise RuntimeError("original 42-node science payload hash changed")
    names=["H04","H05","H06","V01","V02","V03","V04","V05","V06","B01"]
    states={n["id"]:n["state"] for n in unified["nodes"]}
    return {"science_nodes":{name:states[name] for name in names},
            "original_42_node_sha256":payload,
            "next_actual_science_ID":unified["next_action_id"],
            "new_observational_physical_Pi":None,
            "H04_complete_PV_selection_covariance":None,
            "V04_independent_global_transfer":None,
            "B01_all_m_polarized_native_transfer":None,
            "R78_science_state_mutated":False}
