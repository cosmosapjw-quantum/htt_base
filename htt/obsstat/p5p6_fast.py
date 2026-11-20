"""R85 B02–B05 and K01–K06 source-conditional numerical preflight.

Original CF4 K02 four-window method-profiled shape source, optional certified
Fortran. Physical Bianchi all-m E/B transfer and real normal-frame observables
are not supplied. No source qualification or R78 gate is changed by this code.
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
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve, solve_triangular
from htt.obsstat.pre_dag_fast import analysis_lane_policy

ROOT=Path(__file__).resolve().parents[2]
CONFIG=Path(__file__).with_name("p5p6_lane.json")
NATIVE_SOURCE=Path(__file__).parent/"native"/"k02_joint_source.f90"
SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
K03=Path("/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz")
SOURCE_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
K03_SHA="70fc2fee88803a7211c1c157ff87b4adb05b0807a00c03dc38d51f31b3842662"
METHODS=("FP","OTHER","SN","TF")
CENTERS=(.025,.040,.060,.080)
C_KMS=299792.458
STF=np.array([
 [[1,0,0],[0,-1,0],[0,0,0]],
 [[1,0,0],[0,1,0],[0,0,-2]],
 [[0,1,0],[1,0,0],[0,0,0]],
 [[0,0,1],[0,0,0],[1,0,0]],
 [[0,0,0],[0,0,1],[0,1,0]]],dtype=np.float64)
STF/=np.array([np.sqrt(2),np.sqrt(6),np.sqrt(2),np.sqrt(2),np.sqrt(2)])[:,None,None]
_LOCAL=threading.local()


def _sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()


def _rec(**kw):
    _LOCAL.receipt=dict(kw)


def last_p5p6_receipt():
    return dict(getattr(_LOCAL,"receipt",{"used":"NOT_RUN"}))


def prepare_cf4_method_source(path=SELECTED,*,expected_sha=SOURCE_SHA):
    """Lock the actual selected group identity and construct original K02 X."""
    source=Path(path)
    if not source.is_file():raise FileNotFoundError(source)
    if _sha(source)!=expected_sha:raise ValueError("K02 original source SHA256 mismatch")
    with np.load(source,allow_pickle=False) as z:
        wanted=("group_id","dmzp","e_dmzp","z_CMB","n_J2000","method_family")
        data={name:z[name].copy() for name in wanted}
    ids=data["group_id"]
    n=data["n_J2000"]
    method=data["method_family"]
    if (len(ids)!=35970 or len(np.unique(ids))!=35970 or
        n.shape!=(len(ids),3) or not np.isfinite(n).all() or
        np.max(abs(np.sum(n*n,axis=1)-1))>2e-10):
        raise ValueError("K02 source group and unit direction identity mismatch")
    if set(np.unique(method))!=set(METHODS):raise ValueError("K02 method family changed")
    vals=[data[f] for f in ("dmzp","e_dmzp","z_CMB")]
    if not all(np.isfinite(a).all() and a.shape==(len(ids),) for a in vals):
        raise ValueError("K02 nonfinite/redshift/distance source")
    if np.any(data["e_dmzp"]<=0):raise ValueError("positive distance error required")
    distance=10.0**((data["dmzp"]-25)/5)
    if not np.isfinite(distance).all() or np.any(distance<=0):
        raise ValueError("finite positive distances required")
    angular=np.column_stack([n,np.einsum("ni,aij,nj->na",n,STF,n,optimize=True)])
    X=distance[:,None]*np.column_stack([(method==m).astype(float) for m in METHODS]+
                                         [angular[:,j] for j in range(8)])
    sigma=np.hypot(250.,70.*np.log(10)/5.*distance*data["e_dmzp"])
    zc=data["z_CMB"]
    ww=np.column_stack([np.exp(-.5*((zc-center)/.012)**2)/sigma**2 for center in CENTERS])
    y=C_KMS*zc
    if not np.allclose(X[:,:4].sum(axis=1),distance,rtol=0,atol=2e-11):
        raise ValueError("K02 monopole/method exact source gauge violated")
    return {
        "N":len(ids),"group_id":ids,"source_sha256":expected_sha,
        "method_names":list(METHODS),
        "X":np.ascontiguousarray(X),"distance_Mpc":np.ascontiguousarray(distance),
        "weights":np.ascontiguousarray(ww),
        "sigma_kms":np.ascontiguousarray(sigma),"y_cz_kms":np.ascontiguousarray(y),
        "window_centers":list(CENTERS),"method_identifiability":"four independent intercepts + eight apparent angular shape modes only",
        "physical_normal_frame":"NOT_QUALIFIED"}


@lru_cache(maxsize=6)
def _compile_fortran(source_sha):
    compiler=shutil.which("gfortran")
    if compiler is None:raise RuntimeError("gfortran compiler missing")
    flags=["-O3","-fPIC","-shared","-fopenmp","-fno-fast-math"]
    version=subprocess.check_output([compiler,"--version"],text=True,timeout=10).splitlines()[0]
    key=hashlib.sha256((source_sha+str(flags)+version+platform.machine()).encode()).hexdigest()[:24]
    folder=Path(os.environ.get("HTT_NATIVE_CACHE_DIR",
        str(Path(tempfile.gettempdir())/"htt_r79_native_cache")))/"r85"/key
    folder.mkdir(parents=True,exist_ok=True)
    library=folder/"libhtt_r85_k02_source.so"
    meta=folder/"manifest.json"
    with (folder/"lock").open("a+b") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if library.is_file() and meta.is_file():
            try:
                a=json.loads(meta.read_text())
                if a["source_sha256"]==source_sha and a["binary_sha256"]==_sha(library):
                    return str(library)
            except (KeyError,ValueError,OSError,TypeError):
                pass
        temp=folder/f"temp_{os.getpid()}.so"
        try:
            subprocess.run([compiler,*flags,str(NATIVE_SOURCE),"-o",str(temp)],
                check=True,capture_output=True,text=True,timeout=90)
            if not temp.is_file() or not temp.stat().st_size:
                raise RuntimeError("Fortran produced empty binary")
            os.replace(temp,library)
            meta.write_text(json.dumps({"source_sha256":source_sha,
                "binary_sha256":_sha(library),"compiler":version,"flags":flags},
                sort_keys=True)+"\n")
        finally:
            if temp.exists():temp.unlink()
    return str(library)


def _certified_fortran():
    cfg=json.loads(CONFIG.read_text())
    source=_sha(NATIVE_SOURCE)
    if source!=cfg["fortran_source_sha256"]:
        raise RuntimeError("uncertified_R85_Fortran_source_SHA")
    lib=Path(_compile_fortran(source))
    meta=lib.with_name("manifest.json")
    if not lib.is_file() or not meta.is_file():raise RuntimeError("R85 native manifest missing")
    a=json.loads(meta.read_text())
    if a["source_sha256"]!=source or a["binary_sha256"]!=_sha(lib):
        raise RuntimeError("R85 Fortran binary_sha256_mismatch")
    return str(lib)


def _select_native(requested,n,threads):
    if requested is None:return None,False,"explicit_numpy_reference"
    if requested!="auto":return str(requested),False,None
    mode=analysis_lane_policy()["mode"]
    if mode=="numpy":return None,False,"HTT_ANALYSIS_BACKEND_numpy"
    cfg=json.loads(CONFIG.read_text())
    if mode=="auto" and (not cfg["auto_enabled"] or n<cfg["min_sources"]):
        return None,False,"small_or_unproven_faster_source"
    try:return _certified_fortran(),True,None
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as err:
        if mode=="native":raise RuntimeError(f"required_R85_native_unavailable:{err}") from err
        return None,False,str(err)[:240]


def _validate_source_packet(packet):
    for key in ("X","weights","sigma_kms","y_cz_kms"):
        if key not in packet:raise ValueError(f"missing K02 source key {key}")
    X=np.asarray(packet["X"],float)
    w=np.asarray(packet["weights"],float)
    s=np.asarray(packet["sigma_kms"],float)
    y=np.asarray(packet["y_cz_kms"],float)
    n=len(X)
    if n<20 or X.shape!=(n,12) or w.shape!=(n,4) or s.shape!=(n,) or y.shape!=(n,):
        raise ValueError("K02 source shape contract failed")
    if not all(np.isfinite(x).all() for x in (X,w,s,y)) or np.any(w<0) or np.any(s<=0):
        raise ValueError("K02 source nonfinite/negative weight/invalid sigma")
    if any(np.count_nonzero(w[:,j])<12 for j in range(4)):
        raise ValueError("K02 source window rank/data support insufficient")
    return tuple(np.ascontiguousarray(x) for x in (X,w,s,y))


def k02_method_profiled(source,*,native_lib="auto",threads=12,cond_limit=1e10):
    X,w,s,y=_validate_source_packet(source)
    if not isinstance(threads,int) or not 1<=threads<=32:
        raise ValueError("threads 1..32 required")
    if not np.isfinite(cond_limit) or cond_limit<=1:
        raise ValueError("positive numerical condition threshold required")
    n=len(X)
    lib,cert,fallback=_select_native(native_lib,n,threads)
    F=np.empty((4,12,12)); b=np.empty((4,12))
    G=np.empty((48,48))
    if lib is None:
        G[:]=0
        for j in range(4):
            F[j]=X.T@(w[:,j,None]*X)
            b[j]=X.T@(w[:,j]*y)
        for j in range(4):
            for k in range(j,4):
                B=X.T@((w[:,j]*w[:,k]*s*s)[:,None]*X)
                G[12*j:12*(j+1),12*k:12*(k+1)]=B
                G[12*k:12*(k+1),12*j:12*(j+1)]=B.T
        backend="numpy_blas_source"
    else:
        fn=ctypes.CDLL(str(Path(lib).resolve())).htt_r85_k02_joint_source_v1
        f8=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,f8,f8,f8,f8,ctypes.c_int32,f8,f8,f8,
                    ctypes.POINTER(ctypes.c_int)]
        fn.restype=None
        status=ctypes.c_int(-1)
        fn(n,X,w,y,s,threads,F,b,G,ctypes.byref(status))
        if status.value or not all(np.isfinite(a).all() for a in (F,b,G)):
            _rec(used="native_failed",error_code=status.value)
            raise RuntimeError(f"R85 k02 native source kernel failed status={status.value}")
        backend="fortran_source_info_cross"
    inv=[]
    coefficients=[]
    condition=[]
    for j in range(4):
        sym=(F[j]+F[j].T)/2
        eigen=np.linalg.eigvalsh(sym)
        if eigen[0]<=0 or eigen[-1]/eigen[0]>cond_limit:
            raise ValueError("K02 method-profiled SPD/rank/condition gate violated")
        condition.append(float(eigen[-1]/eigen[0]))
        fac=cho_factor(sym,lower=True,check_finite=False)
        coefficients.append(cho_solve(fac,b[j],check_finite=False))
        inv.append(cho_solve(fac,np.eye(12),check_finite=False))
    C32=np.zeros((32,32))
    for j in range(4):
        for k in range(j,4):
            B=G[12*j:12*j+12,12*k:12*k+12]
            cov=(inv[j]@B@inv[k].T)[4:,4:]
            C32[j*8:j*8+8,k*8:k*8+8]=cov
            C32[k*8:k*8+8,j*8:j*8+8]=cov.T
    C32=(C32+C32.T)/2
    ev=np.linalg.eigvalsh(C32)
    if ev[0]<-1e-10*max(1,float(np.linalg.norm(C32,2))):
        raise ValueError("source shared-group covariance negative beyond roundoff")
    _rec(used=backend,source_certified=cert,threads=threads if lib else 0,
         original_source_count=n,fallback_reason=fallback,binary=lib)
    return {"shape8":np.asarray(coefficients)[:,4:],
            "intercepts4":np.asarray(coefficients)[:,:4],
            "joint_cov32":C32,"F12":F,"score12":b,"raw_source_cross_G48":G,
            "condition_F":condition,"source_eig_min":float(ev[0]),
            "physical_shear":None,"physical_Pi":None,
            "physical_omega":None,"physical_GF":None,
            "interpretation":"CF4 fixed method 12D source working law, not normal-frame GR observation"}


def inspect_k03_cross_moments(path=K03,*,expected_sha=K03_SHA):
    p=Path(path)
    if not p.is_file():raise FileNotFoundError(p)
    if _sha(p)!=expected_sha:raise ValueError("K03 external source SHA256 mismatch")
    with np.load(p,allow_pickle=False) as z:
        if set(z.files)!={"A","K","qH","n","zmin","zmax"}:
            raise ValueError("K03 external original source fields changed")
        A=z["A"];K=z["K"];q=z["qH"]
        count=int(z["n"]);zmin=float(z["zmin"]);zmax=float(z["zmax"])
    if A.shape!=(6,6) or K.shape!=(6,102) or q.shape!=(6,) or count<1:
        raise ValueError("K03 source moments shape invalid")
    if not all(np.isfinite(x).all() for x in (A,K,q)) or not np.isfinite([zmin,zmax]).all():
        raise ValueError("K03 source moments contain nonfinite values")
    if np.linalg.norm(A-A.T)>1e-10*np.linalg.norm(A):
        raise ValueError("K03 source moment A not symmetric")
    try:C=np.linalg.cholesky(A)
    except np.linalg.LinAlgError as exc:raise ValueError("K03 original A not SPD") from exc
    whitened=solve_triangular(C,K,lower=True,check_finite=False)
    return {"source_n":count,"source_z_range":[zmin,zmax],
            "A_min_eigen":float(np.linalg.eigvalsh(A)[0]),
            "rank_whitened_K":int(np.linalg.matrix_rank(whitened)),
            "observed_raw_cross_moment_qH":q.tolist(),
            "actual_normal_vorticity":None,
            "physical_congruence_identified":False,
            "conditional_source_SHA256":expected_sha}


def observer_radial_kinematics(n,*,theta,sigma,acceleration_over_c,omega):
    n=np.asarray(n,float);S=np.asarray(sigma,float);a=np.asarray(acceleration_over_c,float)
    w=np.asarray(omega,float)
    if n.ndim!=2 or n.shape[1]!=3 or not len(n) or any(z.shape!=(3,) for z in (a,w)) or S.shape!=(3,3):
        raise ValueError("single congruence radial tensor/units")
    if not all(np.isfinite(x).all() for x in (n,S,a,w)) or not np.isfinite(theta):
        raise ValueError("nonfinite congruence source")
    if np.max(abs(np.sum(n*n,axis=1)-1))>1e-11 or np.linalg.norm(S-S.T)>1e-12 or abs(np.trace(S))>1e-12:
        raise ValueError("unit n and signed STF sigma required")
    wx,wy,wz=w
    anti=np.array([[0,-wz,wy],[wz,0,-wx],[-wy,wx,0]])
    radial=np.einsum("ni,ij,nj->n",n,anti,n)
    H=theta/3-n@a+np.einsum("ni,ij,nj->n",n,S,n)
    return {"local_H_values":H,"radial_omega_response_maxabs":float(np.max(abs(radial))),
            "observed_physical_omega":None,"true_optical_transfer_calibrated":False,
            "units":"theta/sigma/omega/A_over_c are inverse seconds, metric (-,+,+,+)"}


def inspect_external_Bianchi_atlas(manifest,max_uncompressed_bytes=80_000_000):
    """Only structural digest/coverage validation. Never physics qualification."""
    p=Path(manifest)
    if not p.is_file():raise FileNotFoundError(p)
    doc=json.loads(p.read_text())
    required=("schema","source_kind","data_file","data_sha256","solver_commit",
      "family","mode","ell_min","ell_max","frame","units","spin_convention",
      "history","primordial_mode_normalization","initial_conditions","beam")
    if any(k not in doc or not doc[k] for k in required):
        raise ValueError("incomplete external polarized source provenance")
    if doc["schema"]!="htt.bianchi_external_polarized_allm/1" or doc["source_kind"]!="external_result":
        raise ValueError("invalid B02 external result schema")
    candidate=Path(doc["data_file"])
    if candidate.is_absolute() or ".." in candidate.parts or candidate.suffix!=".npz":
        raise ValueError("external atlas NPZ must be a confined relative source path")
    payload=(p.parent/candidate).resolve()
    if not payload.is_relative_to(p.parent.resolve()) or not payload.is_file():
        raise FileNotFoundError(payload)
    if payload.stat().st_size>max_uncompressed_bytes:
        raise ValueError("external Bianchi archive byte cap")
    if _sha(payload)!=doc["data_sha256"]:raise ValueError("external Bianchi source SHA256 mismatch")
    with zipfile.ZipFile(payload) as z:
        info=z.infolist()
        if len(info)!=5 or {x.filename for x in info}!={"ell.npy","m.npy","T.npy","E.npy","B.npy"}:
            raise ValueError("external Bianchi complete NPZ arrays required")
        if any(x.flag_bits & 1 for x in info) or sum(x.file_size for x in info)>max_uncompressed_bytes:
            raise ValueError("Bianchi input uncompressed source size/encryption limit")
    with np.load(payload,allow_pickle=False) as z:
        ell=z["ell"];m=z["m"];T=z["T"];E=z["E"];B=z["B"]
    if any(x.ndim!=1 or len(x)!=len(ell) for x in (ell,m,T,E,B)) or not len(ell):
        raise ValueError("external Bianchi harmonic shapes invalid")
    if not np.issubdtype(ell.dtype,np.integer) or not np.issubdtype(m.dtype,np.integer):
        raise ValueError("Bianchi (ell,m) integer indices required")
    if not all(np.isfinite(x).all() for x in (T,E,B)):
        raise ValueError("external Bianchi nonfinite T/E/B")
    lo,hi=int(doc["ell_min"]),int(doc["ell_max"])
    indices={(int(l),int(j)) for l,j in zip(ell,m)}
    required_set={(l,j) for l in range(lo,hi+1) for j in range(-l,l+1)}
    if lo<2 or hi<lo or indices!=required_set or len(indices)!=len(ell):
        raise ValueError("external Bianchi source incomplete all m support")
    return {"structure_verified":True,"physical_transfer_qualified":False,
            "claim_tier":"SCHEMA_AND_BYTE_AUTHENTICITY_ONLY_NOT_EXTERNAL_SOLVER_PROVENANCE",
            "harmonic_count":len(ell),"ell_range":[lo,hi],"source_SHA256":doc["data_sha256"]}


def conditional_template_projection(response,template,*,source_qualified=False):
    M=np.asarray(response,float);T=np.asarray(template,float)
    if M.ndim!=2 or T.ndim!=2 or M.shape[1]!=T.shape[0] or not np.isfinite([M,T]).all():
        raise ValueError("source response/template dimensions")
    return {"working_observables":M@T,"physical_planck_match":False,
            "actual_physical_Pi":None,"source_qualified":bool(source_qualified and False)}


def conditional_template_subspace_overlap(A,B,C):
    A=np.asarray(A,float);B=np.asarray(B,float);C=np.asarray(C,float)
    if A.ndim!=2 or B.ndim!=2 or A.shape[0]!=B.shape[0] or C.shape!=(len(A),len(A)):
        raise ValueError("Bianchi family templates common source covariance shape")
    if not all(np.isfinite(x).all() for x in (A,B,C)):raise ValueError("nonfinite family source")
    try:L=np.linalg.cholesky(C)
    except np.linalg.LinAlgError as err:raise ValueError("Bianchi source covariance not SPD") from err
    x=solve_triangular(L,A,lower=True);y=solve_triangular(L,B,lower=True)
    Qx,sx,_=np.linalg.svd(x,full_matrices=False)
    Qy,sy,_=np.linalg.svd(y,full_matrices=False)
    rank_x=int(np.linalg.matrix_rank(x));rank_y=int(np.linalg.matrix_rank(y))
    scores=np.linalg.svd(Qx[:,:rank_x].T@Qy[:,:rank_y],compute_uv=False)
    return {"singular_cosines":np.clip(scores,0,1).tolist(),
            "rank_A":rank_x,"rank_B":rank_y,"physical_family_evidence":None}


def conditional_kinematic_identification(J,C,*,source_qualified=False):
    J=np.asarray(J,float);C=np.asarray(C,float)
    if J.ndim!=2 or C.shape!=(len(J),len(J)) or not np.isfinite(J).all() or not np.isfinite(C).all():
        raise ValueError("kinematic source Jacobian/covariance mismatch")
    try:L=np.linalg.cholesky(C)
    except np.linalg.LinAlgError as err:raise ValueError("unqualified K04 covariance") from err
    singular=np.linalg.svd(solve_triangular(L,J,lower=True),compute_uv=False)
    return {"rank":int(np.linalg.matrix_rank(solve_triangular(L,J,lower=True))),
            "working_singular_values":singular.tolist(),
            "physical_shear":None,"source_qualified":False}


def joint_same_congruence_gate(sources):
    required=("CF4","Gaia","CMB")
    matched=all(isinstance(sources.get(k),dict) and sources[k].get("physical_frame_qualified") is True for k in required)
    return {"scientific_admission":False,"all_frame_tokens_present":matched,
            "physical_joint_Pi":None,
            "missing":"real same-congruence optical nonradial source covariance/null"}


def historical_BK_statuses():
    root=ROOT/"docs/research_program/observational_publication_20261015"
    o=json.loads((root/"PUBLICATION_DAG.json").read_text())
    u=json.loads((root/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json").read_text())
    sha=hashlib.sha256(json.dumps(o["nodes"],sort_keys=True).encode()).hexdigest()
    if sha!=u["original_42_payload_sha256"]:raise RuntimeError("original 42-node science DAG altered")
    states={i["id"]:i["state"] for i in u["nodes"]}
    names=[f"B{i:02d}" for i in range(2,6)]+[f"K{i:02d}" for i in range(1,7)]
    return {"science_nodes":{k:states[k] for k in names},"original_42_science_SHA":sha,
            "next_actual_science_ID":u["next_action_id"],"science_gates_modified":False}
