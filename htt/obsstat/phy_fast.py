"""R81 conditional PHY-01..07 / SQ-NATIVE / E0,E1 numerical preflight.

No external low-ell solver, astrophysical joint null, or science DAG mutation.
Existing htt.obsstat.pre_dag_fast is the source/NumPy reference layer.
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
from pathlib import Path
from functools import lru_cache

import numpy as np
from scipy.linalg import eigh, cho_factor, cho_solve
from scipy.stats import chi2

from htt.obsstat.pre_dag_fast import (analysis_lane_policy,
    hemisphere_moments, codazzi_map, radial_design)
from scripts.r68.fiveview_geometry import E, stf_matrix, stf_coordinates

_REPO=Path(__file__).resolve().parents[2]
_CONFIG=Path(__file__).with_name("phy_lane.json")
_SOURCE={
    "mask":Path(__file__).parent/"native"/"multi_axis_mask.f90",
    "gram":Path(__file__).parent/"native"/"weighted_gram.cpp",
}
_RECEIPT=threading.local()


def _array(x,name,ndim,tail=()):
    z=np.asarray(x,dtype=np.float64)
    if z.ndim!=ndim or (tail and z.shape[-len(tail):]!=tail):
        raise ValueError(f"{name}: invalid numeric shape")
    if not np.all(np.isfinite(z)):
        raise ValueError(f"{name}: nonfinite numeric input")
    return np.ascontiguousarray(z)


def _unit(n,name):
    z=_array(n,name,2,(3,))
    if not len(z) or np.any(abs(np.einsum("ij,ij->i",z,z)-1)>2e-10):
        raise ValueError(f"{name}: nonempty unit directions required")
    return z


def _receipt(**info):
    _RECEIPT.last=dict(info)


def last_phy_receipt():
    return dict(getattr(_RECEIPT,"last",{"used":"NOT_RUN"}))


def _certified_native(kind):
    cfg=json.loads(_CONFIG.read_text())
    spec=cfg["kernels"][kind]
    source=_SOURCE[kind]
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if digest!=spec["source_sha256"]:
        raise RuntimeError(f"uncertified_{kind}_source_changed")
    target=_build_library(kind,digest)
    receipt=target.with_name("manifest.json")
    if not target.is_file() or not receipt.is_file():
        raise RuntimeError("native binary/receipt missing")
    info=json.loads(receipt.read_text())
    if (info["source_sha256"]!=digest or
        info["binary_sha256"]!=hashlib.sha256(target.read_bytes()).hexdigest()):
        raise RuntimeError("native_binary_checksum_mismatch")
    return str(target)


@lru_cache(maxsize=8)
def _build_library(kind,digest):
    source=_SOURCE[kind]
    compiler_name="gfortran" if kind=="mask" else "g++"
    compiler=shutil.which(compiler_name)
    if compiler is None:raise RuntimeError(f"missing_{compiler_name}")
    version=subprocess.check_output([compiler,"--version"],text=True,timeout=10).splitlines()[0]
    flags=(["-O3","-fPIC","-shared","-fopenmp","-fno-fast-math"] if kind=="mask" else
           ["-O3","-std=c++17","-fPIC","-shared","-fopenmp","-ffp-contract=off","-fno-fast-math"])
    key=hashlib.sha256((digest+str(flags)+version+platform.machine()).encode()).hexdigest()[:24]
    root=Path(os.environ.get("HTT_NATIVE_CACHE_DIR",
               str(Path(tempfile.gettempdir())/"htt_r79_native_cache")))/"r81"/kind/key
    root.mkdir(parents=True,exist_ok=True)
    output=root/("libhtt_r81_mask.so" if kind=="mask" else "libhtt_r81_gram.so")
    receipt=root/"manifest.json"
    with (root/"lock").open("a+b") as fp:
        fcntl.flock(fp,fcntl.LOCK_EX)
        if output.exists() and receipt.exists():
            try:
                saved=json.loads(receipt.read_text())
                if (saved.get("binary_sha256")==hashlib.sha256(output.read_bytes()).hexdigest()
                        and saved.get("source_sha256")==digest):
                    return output
            except (OSError,ValueError,TypeError):
                pass
        temporary=root/f"tmp_{os.getpid()}.so"
        try:
            subprocess.run([compiler,*flags,str(source),"-o",str(temporary)],
                           capture_output=True,text=True,check=True,timeout=90)
            if temporary.stat().st_size==0:
                raise RuntimeError("compiler produced empty library")
            os.replace(temporary,output)
            receipt.write_text(json.dumps({
                "source_sha256":digest,
                "binary_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                "compiler_version":version,"flags":flags,"kind":kind},sort_keys=True)+"\n")
        finally:
            if temporary.exists():temporary.unlink()
    return output


def _native_path(kind,requested,n,m=1):
    if requested is None:
        return None,False,"explicit_numpy_reference"
    if requested!="auto":
        return str(requested),False,None
    mode=analysis_lane_policy()["mode"]
    if mode=="numpy":return None,False,"HTT_ANALYSIS_BACKEND_numpy"
    config=json.loads(_CONFIG.read_text())["kernels"][kind]
    if mode=="auto" and (not config["auto_enabled"] or n*m<config["threshold_operations"]):
        return None,False,"small_or_unproven_auto"
    try:
        return _certified_native(kind),True,None
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as ex:
        if mode=="native":raise RuntimeError(f"required_{kind}_native_unavailable:{ex}") from ex
        return None,False,str(ex)[:240]


def multi_axis_hemisphere(directions,axes,weights=None,*,native_lib="auto",threads=8):
    """Multi-axis normalized source hemisphere moments, no dense N×axes mask.

    For each axis, exactly n·axis>0 is plus. Emits (axes,2) weights/counts,
    (axes,2,3) weighted means and (axes,2,3,3) second moments.
    """
    n=_unit(directions,"source n")
    a=_unit(axes,"mask axes")
    w=np.ones(len(n)) if weights is None else _array(weights,"source weights",1)
    if w.shape!=(len(n),) or np.any(w<0) or not np.any(w>0):
        raise ValueError("source weights must be nonnegative and not all zero")
    if not isinstance(threads,int) or not (1<=threads<=32):
        raise ValueError("native mask workers 1..32")
    path,certified,reason=_native_path("mask",native_lib,len(n),len(a))
    if path is not None:
        lib=ctypes.CDLL(str(Path(path).resolve()))
        fn=lib.htt_multi_hemi_v1
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,ctypes.c_int64,fp,fp,fp,ctypes.c_int32,fp,ctypes.POINTER(ctypes.c_int)]
        fn.restype=None
        out=np.empty((len(a),2,11),dtype=np.float64)
        status=ctypes.c_int(-1)
        fn(len(n),len(a),n,w,a,threads,out,ctypes.byref(status))
        if status.value or not np.isfinite(out).all():
            _receipt(used="native_failed",kind="mask",code=status.value)
            raise RuntimeError(f"Fortran multi-axis mask kernel failed ({status.value})")
        sums=out[:,:,0]
        counts=np.rint(out[:,:,10]).astype(np.int64)
        if np.any(counts<=0) or np.any(sums<=0) or np.any(abs(out[:,:,10]-counts)>1e-9):
            raise ValueError("empty weighted hemisphere or invalid source count")
        means=out[:,:,1:4]/sums[:,:,None]
        mats=np.zeros((len(a),2,3,3))
        mats[:,:,0,0]=out[:,:,4]
        mats[:,:,0,1]=mats[:,:,1,0]=out[:,:,5]
        mats[:,:,0,2]=mats[:,:,2,0]=out[:,:,6]
        mats[:,:,1,1]=out[:,:,7]
        mats[:,:,1,2]=mats[:,:,2,1]=out[:,:,8]
        mats[:,:,2,2]=out[:,:,9]
        _receipt(used="fortran_batch",source_certified=certified,n_rows=len(n),
                 n_axes=len(a),threads=threads,binary_path=path)
        return {"weights":sums,"counts":counts,"means":means,"second":mats/sums[:,:,None,None]}
    sums=np.empty((len(a),2))
    means=np.empty((len(a),2,3))
    mats=np.empty((len(a),2,3,3))
    counts=np.empty((len(a),2),dtype=np.int64)
    for j,axis in enumerate(a):
        z=hemisphere_moments(n,axis,weights=w,native_lib=None)
        for key,buffer in (("weights",sums),("means",means),("second",mats),("counts",counts)):
            buffer[j]=z[key]
    _receipt(used="numpy_reference",source_certified=False,n_rows=len(n),
             n_axes=len(a),fallback_reason=reason)
    return {"weights":sums,"counts":counts,"means":means,"second":mats}


def inspect_external_native(manifest):
    """Read-only schema+SHA validator, NEVER validates external physical transfer."""
    p=Path(manifest)
    if not p.is_file():raise FileNotFoundError(p)
    obj=json.loads(p.read_text())
    if obj.get("schema")!="htt.external_bianchi_polarized/1" or obj.get("source_kind")!="external_native_result":
        raise ValueError("unsupported external source/manifest schema")
    fields=("solver_commit","model_family","observer_frame","units","data_file","data_sha256")
    if any(not isinstance(obj.get(f),str) or not obj[f] for f in fields):
        raise ValueError("external provenance incomplete")
    file=Path(obj["data_file"])
    if file.is_absolute() or ".." in file.parts or file.suffix!=".npz":
        raise ValueError("external data path must be a confined relative NPZ")
    source=(p.parent/file).resolve()
    if not source.is_relative_to(p.parent.resolve()) or not source.is_file():
        raise FileNotFoundError("external source outside declared manifest folder or missing")
    if hashlib.sha256(source.read_bytes()).hexdigest()!=obj["data_sha256"]:
        raise ValueError("external source sha256 mismatch")
    with np.load(source,allow_pickle=False) as z:
        if set(z.files)!={"ell","m","E","B"}:
            raise ValueError("polarized external output fields incomplete")
        ell,m,E_,B_=(z[f] for f in ("ell","m","E","B"))
        if not all(x.ndim==1 for x in (ell,m,E_,B_)) or not len(ell) or not all(len(x)==len(ell) for x in (m,E_,B_)):
            raise ValueError("external angular data shapes inconsistent")
        if not np.issubdtype(ell.dtype,np.integer) or not np.issubdtype(m.dtype,np.integer):
            raise ValueError("external angular multipole indices invalid")
        if np.any(ell<2) or np.any(abs(m)>ell) or len({(int(i),int(j)) for i,j in zip(ell,m)})!=len(ell):
            raise ValueError("external angular (ell,m) invalid")
        if not np.isfinite(E_).all() or not np.isfinite(B_).all():
            raise ValueError("external angular output nonfinite")
    return {"source_hash_matches":True,"record_count":len(ell),
            "solver_commit":obj["solver_commit"],"source_kind":"external_native_result",
            "schema_verified":True,"physical_transfer_qualified":False,
            "instrument_cosmological_null":"UNAVAILABLE"}


def photon_codazzi_feasibility(S,shear,*,LieM,Omega,eta,f=None):
    S=_array(S,"photon STF",2,(3,3))
    shear=_array(shear,"normal signed STF5",1)
    M=_array(LieM,"Lie Codazzi",2,(3,5))
    if shear.shape!=(5,) or not Omega>0 or not eta>0 or not np.isfinite([Omega,eta]).all():
        raise ValueError("positive Omega, photon energy fraction and STF5 required")
    if abs(np.trace(S))>1e-12 or np.linalg.norm(S-S.T)>1e-12:
        raise ValueError("photon STF sym/trace")
    P=np.eye(3)/3+S
    vals=np.linalg.eigvalsh(P)
    if vals[0]<-1e-12:
        raise ValueError("negative photon pressure")
    u=-M@shear/(3*Omega)
    state={"P_eigen":vals.tolist(),"photon_psd":bool(vals[0]>=-1e-12),
           "photon_flux_missing":f is None,"Codazzi_source_only_conditional":True,
           "source_normal_u_from_Einstein":u.tolist(),"physical_Pi":None}
    if f is not None:
        f=_array(f,"photon f",1)
        if f.shape!=(3,):raise ValueError("photon normal flux3 required")
        moment=P-np.outer(f,f)
        moment_min=float(np.min(np.linalg.eigvalsh(moment)))
        pinv=np.linalg.pinv(P,rcond=1e-12)
        row=u@pinv@u/(eta*eta)
        state.update(moment_cov_min_eigen=moment_min,
            photon_psd=bool(moment_min>=-1e-12 and vals[0]>=-1e-12),
            Q_joint_photon_only_conditional=float(row),
            photon_only_flux_equal=bool(np.linalg.norm(u-eta*f)<1e-10))
    return state


def shared_beta_radio_photon(beta,*,k,kappa):
    b=_array(beta,"same-frame beta",1)
    if b.shape!=(3,) or b@b>=1 or not np.isfinite([k,kappa]).all():
        raise ValueError("subluminal common beta3 and finite selection k,kappa required")
    b2=float(b@b)
    STF=np.outer(b,b)-np.eye(3)*b2/3
    A=.5*(k*k+k+kappa)
    S=4/(3+b2)*STF
    count=A*STF
    logquad=.5*(k+kappa)*STF
    tr2=float(np.trace(S@S))
    chi=None if tr2==0 else float(np.sqrt(6)*np.trace(S@S@S)/tr2**1.5)
    return {"photon_flux":4*b/(3+b2),
            "photon_STF":S,"count_STF":count,"log_count_STF":logquad,
            "radio_first_order_dipole":k*b,"A_selection":A,
            "ratio":A*(3+b2)/4,
            "photon_chi":chi,"source_qualified":False,"physical_Pi":None}


def gaia_eb_mask_alias(C):
    C=_array(C,"Gaia 16D covariance",2,(16,16))
    if np.linalg.norm(C-C.T)>1e-10*max(np.linalg.norm(C),1):
        raise ValueError("Gaia source covariance symmetry")
    np.linalg.cholesky(C)
    F=np.linalg.solve(C,np.eye(16))
    Fn=F[:6,:6]
    projected=F[6:,6:]-F[6:,:6]@np.linalg.solve(Fn,F[:6,6:])
    A,B,D=projected[:5,:5],projected[:5,5:],projected[5:,5:]
    def invsqrt(x):
        w,U=eigh(.5*(x+x.T))
        if w[0]<=0:raise ValueError("non-positive profile Fisher")
        return (U/np.sqrt(w))@U.T
    corr=invsqrt(A)@B@invsqrt(D)
    s=np.linalg.svd(corr,compute_uv=False)
    return {"canonical":s,"maxcanonical":float(s[0]),
            "physical_vorticity_identified":False,"source_instrument_noise_law":"working_Gaia_formal"}


def local_E2_and_Lie_B2(n,S,N):
    n=_unit(n,"common normal sky")
    S=_array(S,"normal shear",2,(3,3))
    N=_array(N,"normal spatial Lie N",2,(3,3))
    if np.linalg.norm(S-S.T)>1e-12 or abs(np.trace(S))>1e-12 or np.linalg.norm(N-N.T)>1e-12:
        raise ValueError("signed STF or symmetric Lie structure required")
    z=n@S
    e=z-n*np.einsum("ni,ni->n",n,z)[:,None]
    b=-np.cross(n,n@N)
    return e,b


def normal_flux_residual(x,u,M,*,Omega,C_joint,independent_source=False,
                         calibrated_null=False):
    x=_array(x,"normal STF5",1)
    u=_array(u,"independent normal flux",1)
    M=_array(M,"normal Lie Codazzi",2,(3,5))
    C=_array(C_joint,"joint normal covariance",2,(8,8))
    if x.shape!=(5,) or u.shape!=(3,) or not Omega>0:
        raise ValueError("normal state/covariance")
    np.linalg.cholesky(C)
    D=np.column_stack([M/(3*Omega),np.eye(3)])
    C_r=D@C@D.T
    eig=np.linalg.eigvalsh(C_r)
    rank=int(np.linalg.matrix_rank(C_r))
    r=u+M@x/(3*Omega)
    out={"residual":r,"covariance":C_r,"rank_covariance":rank,
         "physical_Pi":None,"working_chi2":None,"working_tail":None}
    if independent_source and calibrated_null:
        stat=float(r@np.linalg.solve(C_r,r))
        out.update(working_chi2=stat,working_tail=float(chi2.sf(stat,rank)))
    return out


def shear_shape_rate(S,D,*,H):
    S=_array(S,"normal signed sigma",2,(3,3))
    D=_array(D,"normal signed driver",2,(3,3))
    if np.linalg.norm(S-S.T)>1e-12 or abs(np.trace(S))>1e-12 or np.linalg.norm(D-D.T)>1e-12 or abs(np.trace(D))>1e-12:
        raise ValueError("STF normal shear and driver required")
    if H<=0 or not np.isfinite(H):raise ValueError("positive H required")
    I2=float(np.trace(S@S))
    evolved=-3*H*S+D
    comm=float(np.linalg.norm(S@D-D@S))
    if I2<1e-30:
        return {"chi":None,"dchi":None,"commutator_norm":comm,
                "signed_tensor_evolves":bool(np.linalg.norm(evolved)>0)}
    I3=float(np.trace(S@S@S))
    chi=float(np.sqrt(6)*I3/I2**1.5)
    dchi=float((3*np.sqrt(6)/I2**1.5)*
        (np.trace(S@S@D)-(I3/I2)*np.trace(S@D)))
    return {"chi":chi,"dchi":dchi,"commutator_norm":comm,
            "signed_tensor_evolves":bool(np.linalg.norm(evolved)>0)}


def photon_l4_family(epsilon,*,threshold,shear_s):
    if not np.isfinite([epsilon,threshold,shear_s]).all() or not (0<=threshold<=1) or not (-1<=epsilon<=2):
        raise ValueError("positive first-two-moment photon l4 family parameters")
    # P4(mu)=(35 mu^4-30 mu^2+3)/8; p_epsilon=(1+eps P4)/4pi.
    # epsilon<=2 is conservative for positivity, including eps=1.
    z=threshold
    weighted_cap=(7*(1-z**5)-10*(1-z**3)+3*(1-z))/8
    cap=(1-z)+epsilon*weighted_cap
    dS=-16*shear_s/45+8*epsilon*shear_s/315
    return {"cap_F":float(cap),"source_stress_derivative_zz":float(dS),
            "first_two_photon_moments_identical":True,
            "actual_physical_time_GF_available":False}


def weighted_radial_stats(X,weights,y,*,native_lib="auto",threads=8):
    X=_array(X,"source design",2)
    w=_array(weights,"diagonal weights",1)
    y=_array(y,"scalar source response",1)
    n,p=X.shape
    if n<=0 or not (1<=p<=32) or w.shape!=(n,) or y.shape!=(n,):
        raise ValueError("source linear design/weight shape")
    if np.any(w<0) or not np.any(w>0):
        raise ValueError("source diagonal precision must be nonnegative")
    if not isinstance(threads,int) or not 1<=threads<=32:raise ValueError("native worker count")
    path,certified,reason=_native_path("gram",native_lib,n)
    if path is not None:
        lib=ctypes.CDLL(str(Path(path).resolve()))
        fn=lib.htt_weighted_gram_v1
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,ctypes.c_int32,fp,fp,fp,ctypes.c_int32,fp,fp,fp]
        fn.restype=ctypes.c_int
        F=np.empty((p,p));b=np.empty(p);c=np.empty(1)
        status=fn(n,p,X,w,y,threads,F,b,c)
        if status or not np.isfinite(F).all() or not np.isfinite(b).all() or not np.isfinite(c).all():
            _receipt(used="native_failed",kind="gram",code=status)
            raise RuntimeError("C++ weighted source accumulation failed")
        _receipt(used="cpp_gram",n_rows=n,p=p,threads=threads,certified=certified)
        return F,b,float(c[0])
    F=X.T@(w[:,None]*X)
    b=X.T@(w*y)
    c=float(np.dot(w,y*y))
    _receipt(used="numpy_reference",kind="gram",reason=reason,n_rows=n,p=p)
    return F,b,c


def historical_common_anchors():
    pub=_REPO/"docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json"
    dag=_REPO/"docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
    p=json.loads(pub.read_text());g=json.loads(dag.read_text())
    canonical=hashlib.sha256(json.dumps(p["nodes"],sort_keys=True).encode()).hexdigest()
    if canonical!=g["original_42_payload_sha256"]:
        raise RuntimeError("original 42-node science payload identity changed")
    nodes={q["id"]:q for q in p["nodes"]}
    for nid in ("E0","E1"):
        if nodes[nid]["state"]!="completed_scoped":
            raise ValueError("historical scoped evidence state mutated")
        for item in nodes[nid]["existing_evidence"]:
            if item.startswith("commit:"):
                sh=item.split(":",1)[1]
                subprocess.run(["git","cat-file","-e",sh+"^{commit}"],
                               cwd=_REPO,check=True,stdout=subprocess.DEVNULL)
            elif not (_REPO/item).is_file():
                raise FileNotFoundError(item)
    return {"E0":nodes["E0"],"E1":nodes["E1"],"R78_science_nodes_42_sha":canonical,
            "R78_next_id":g["next_action_id"],"physical_claim_upgrade":False}
