"""R90 solver-free conditional Bianchi attribution on R62 owned STF carriers.

No Boltzmann solver; no physical class Bayes factors. Every score is the
best found feasible *upper bound* to distance from a fixed Gaussian carrier
to a q_normal=0, canonical-Lie Codazzi shear subspace, after SO(3) rotation.
A score outside the confidence set is NOT a proof of family exclusion.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from scipy.linalg import null_space, solve_triangular
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
R62 = BASE / "R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION"
G07 = BASE / "R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G07_BIANCHI/SOLVER_FREE_RESEARCH_RESULT.json"

# N=diag(n1,n2,n3), a=(a,0,0), N.a=0.
# III is a VI_h=-1 stratum, not another independent continuous family.
# Exception VI_-1/9 is a separate rank stratum, not an additional universe type.
CANONICAL_REPRESENTATIVES = {
    "I": ((0.,0.,0.), 0.),
    "II": ((0.,0.,1.), 0.),
    "III_VIh=-1": ((0.,1.,-1.), 1.),
    "IV": ((0.,0.,1.), 1.),
    "V": ((0.,0.,0.), 1.),
    "VI_0": ((0.,1.,-2.), 0.),
    "VI_h=-1/4": ((0.,1.,-2.), math.sqrt(.5)),
    "VI_h=-1/9_exception": ((0.,1.,-4.), 2./3.),
    "VII_0": ((0.,1.,2.), 0.),
    "VII_h=1/4": ((0.,1.,2.), math.sqrt(.5)),
    "VIII": ((1.,2.,-3.), 0.),
    "IX": ((1.,2.,3.), 0.),
}

# Orthonormal Frobenius STF5 in the same chart as R54/R62 source.
STF = np.array([
 [[1,0,0],[0,-1,0],[0,0,0]],
 [[1,0,0],[0,1,0],[0,0,-2]],
 [[0,1,0],[1,0,0],[0,0,0]],
 [[0,0,1],[0,0,0],[1,0,0]],
 [[0,0,0],[0,0,1],[0,1,0]]
],float) / np.array([2,6,2,2,2],float)[:,None,None]**.5

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for buf in iter(lambda:f.read(2**18), b""):
            h.update(buf)
    return h.hexdigest()

def codazzi_stf(n:tuple[float,float,float], a:float)->np.ndarray:
    """Exact G07/ R49 3x5 map in orthonormal STF basis; normalization of q irrelevant to q=0."""
    n1,n2,n3=n
    m=np.array([
        [3*a,0,0,0,n3-n2],
        [0,0,3*a,n1-n3,0],
        [0,0,n2-n1,3*a,0],
    ],float)
    T=np.stack([[s[0,0],s[1,1],s[0,1],s[0,2],s[1,2]] for s in STF],axis=1)
    return m@T

def rotation_stf(R:np.ndarray)->np.ndarray:
    return np.einsum("aij,ip,bpq,jq->ab",STF,R,STF,R,optimize=True)

def profile_fixed_orientation(y:np.ndarray, C:np.ndarray, B:np.ndarray, R:np.ndarray)->tuple[float,np.ndarray]:
    """Three arbitrary Legendre coefficients, each constrained to rotated Codazzi kernel."""
    k=B.shape[1]
    L=np.linalg.cholesky(C)
    W=rotation_stf(R)@B
    design=np.kron(np.eye(3),W)
    z=solve_triangular(L,y,lower=True,check_finite=False)
    if k:
        A=solve_triangular(L,design,lower=True,check_finite=False)
        beta,*_=np.linalg.lstsq(A,z,rcond=1e-11)
        witness=design@beta
        residual=z-A@beta
    else:
        witness=np.zeros_like(y);residual=z
    return float(residual@residual), witness

def profile_family(y:np.ndarray,C:np.ndarray,n:tuple[float,float,float],a:float,
                   *,optimize_rotation:bool=True)->dict:
    J=codazzi_stf(n,a)
    B=null_space(J,rcond=1e-12)
    rank=int(np.linalg.matrix_rank(J,tol=1e-10))
    if B.shape[1]==5:
        return {"codazzi_rank":rank,"shear_kernel_dim":5,"feasible_distance2_upper":0.,
                "angle_rotvec":[0.,0.,0.], "witness":y.tolist(), "optimization":"full 5D free shear"}
    seeds=np.array([[0,0,0],[.6,0,0],[0,.6,0],[0,0,.6],[1.,1.,0],
                    [0,1.,1.],[1.,0.,1.],[-.6,.3,.2],[1.4,0,0],[0,1.4,0],[0,0,1.4]],float)
    scores=[profile_fixed_orientation(y,C,B,Rotation.from_rotvec(v).as_matrix())[0] for v in seeds]
    i=int(np.argmin(scores))
    v_best=seeds[i].copy()
    if optimize_rotation:
        candidate=minimize(lambda v:profile_fixed_orientation(y,C,B,Rotation.from_rotvec(v).as_matrix())[0],
                           v_best,method="Powell",options={"maxiter":65,"maxfev":320,
                           "ftol":1e-9,"xtol":1e-6,"disp":False})
        if np.isfinite(candidate.fun) and candidate.fun<scores[i]:
            v_best=np.asarray(candidate.x)
    s,wit=profile_fixed_orientation(y,C,B,Rotation.from_rotvec(v_best).as_matrix())
    return {"codazzi_rank":rank,"shear_kernel_dim":int(B.shape[1]),
            "feasible_distance2_upper":float(s),"angle_rotvec":v_best.tolist(),
            "witness":wit.tolist(), "optimization":"finite SO3 multistart+Powell; upper bound only"}

def tensor_chi(k:np.ndarray)->float:
    Q=np.einsum("a,aij->ij",np.asarray(k),STF)
    q2=float(np.trace(Q@Q))
    return float(np.sqrt(6)*np.trace(Q@Q@Q)/q2**1.5) if q2>1e-18 else 0.

def evaluate_variant(variant:str,*,fast:bool=False)->dict:
    source=R62/f"{variant}__J2_coefficients.json"
    j=json.loads(source.read_text())
    if j["variant"]!=variant or j["experiment"]!="J2_coefficients":
        raise ValueError("source variant or experiment drift")
    y=np.array(j["mean"],float)
    C=np.array(j["covariance"],float)
    if y.shape!=(15,) or C.shape!=(15,15):
        raise ValueError("unexpected 3x5 signed STF carrier")
    if np.linalg.eigvalsh(C)[0]<=0:
        raise ValueError("source covariance not positive definite")
    cutoff=float(j["confidence"]["cutoff"])
    if abs(cutoff-chi2.ppf(.95,15))>1e-7:
        raise ValueError("R62 confidence event drift")
    table={}
    for name,(n,a) in CANONICAL_REPRESENTATIVES.items():
        info=profile_family(y,C,n,a,optimize_rotation=not fast)
        # Only a CONSTRUCTIVE witness within the same R62 95% confidence event.
        info["status"]="CANONICAL_WITNESS_COMPATIBLE" if info["feasible_distance2_upper"]<=cutoff+1e-9 else "UNRESOLVED_NOT_EXCLUDED"
        del info["witness"]
        table[name]=info
    # Unrestricted normal flux q_a = codazzi(sigma)_a (up to Einstein normalization)
    # makes every observed STF tensor algebraically admissible, subject to physical
    # matter realization. This is a limitation, NOT typewide nonidentifiability theorem.
    rng=np.random.default_rng(90321)
    samples=rng.multivariate_normal(y,C,size=512,method="cholesky")
    post_positive=float(np.mean([tensor_chi(s[:5])>0 for s in samples]))
    return {
       "variant":variant,"source":str(source.relative_to(ROOT)),"sha256":sha(source),
       "original_R62_sci_note":j["interpretation"],"nuisance_marginalized":True,
       "source_mean_dim":15,"confidence_cutoff95":cutoff,
       "fiveview":{
          "x":"signed 15D R62 J2 tensor coefficients and full C15",
          "Q_statistical_body":float(y@np.linalg.solve(C,y)),
          "F_conditional_gaussian_prob_chi_J0_gt_0":post_positive,
          "F_measure":"512 draws from the FIXED Gaussian estimator law N(y,C), non-cosmological",
          "Pi_physical":None, "G_F_physical":None,
          "auxiliary_signed_shape_chi_J0":tensor_chi(y[:5]),
       },
       "canonical_compatibility":table,
       "finite_witness_count":sum(x["status"]=="CANONICAL_WITNESS_COMPATIBLE" for x in table.values()),
       "inference_limit":"canonical algebra + q_normal=0 + source STF identical to normal shear up to common scale/rotation; NO physical source transport, no typewide exclusion/identification, no family posterior",
       "tilt_flexible_status":"all 5D STF algebraically allowed if normal flux is freely supplied; physical tilt/EOS realization not guaranteed",
    }

def run(*,fast:bool=False)->dict:
    G07_json=json.loads(G07.read_text())
    expected={x["type"]:x["codazzi_rank"] for x in G07_json["part_a_lie_curvature_and_codazzi"]["canonical_families"]}
    aliases={"III_VIh=-1":"III","VI_h=-1/4":"VI_h","VI_h=-1/9_exception":"VI_-1/9*","VII_h=1/4":"VII_h"}
    for name,(n,a) in CANONICAL_REPRESENTATIVES.items():
        k=aliases.get(name,name)
        if int(np.linalg.matrix_rank(codazzi_stf(n,a),tol=1e-10))!=expected[k]:
            raise RuntimeError("G07 Codazzi rank mismatch for "+name)
    variants=["log","log_mono","log_mono_error","log_mono_galactic",
              "log_mono_radial","log_split","log_survey"]
    rec={n:evaluate_variant(n,fast=fast) for n in variants}
    classification_matrix={
        key:{v:rec[v]["canonical_compatibility"][key]["status"] for v in variants}
        for key in CANONICAL_REPRESENTATIVES
    }
    return {
       "schema":"htt.r90.solverfree_canonical_bianchi_compatibility/1",
       "source_R62_history":"R62 source-response-conditional 7-nuisance J2 Gaussian carriers",
       "source_R62_status":"SOURCE_CONDITIONAL_NOT_PHYSICAL_SHEAR",
       "source_R49_model":"Bianchi 11 algebra families, III and exceptional VI rank strata separately represented",
       "source_G07_sha256":sha(G07),
       "canonical_representatives":len(CANONICAL_REPRESENTATIVES),
       "independent_family_count":10,
       "independent_family_count_note":"I,II,IV,V,VI0,VIh,VII0,VIIh,VIII,IX; type III is VIh=-1, and exceptional VIh=-1/9 is a singular stratum. Count is illustrative; old registry conventions may differ.",
       "prior_R62_210_classifications_reused_not_rerun":True,
       "source_variants":rec,"cross_variant_compatibility":classification_matrix,
       "all_models_free_flux_profile_saturated":True,
       "novel_family_attribution":"NOT_ESTABLISHED; finite canonical witness / compatibility only",
       "native_boltzmann_required":False,
       "science_SSOT_unchanged":True,
    }
