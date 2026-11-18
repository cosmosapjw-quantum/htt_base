"""R68: mathematical geometry of typed five-view summaries, not a new likelihood.

No data-independent physical shear inference. Exact R66 retained-sky stress
readout is explicitly not an end-to-end Commander measurement.
"""
from __future__ import annotations
from pathlib import Path
import json
import math
import hashlib
import numpy as np
from scipy.stats import chi2

E = np.stack([
    np.diag([1, -1, 0])/np.sqrt(2),
    np.diag([1, 1, -2])/np.sqrt(6),
    np.array([[0,1,0],[1,0,0],[0,0,0]])/np.sqrt(2),
    np.array([[0,0,1],[0,0,0],[1,0,0]])/np.sqrt(2),
    np.array([[0,0,0],[0,0,1],[0,1,0]])/np.sqrt(2)
])


def stf_matrix(v):
    v = np.asarray(v,float)
    if v.shape[-1] != 5 or not np.all(np.isfinite(v)):
        raise ValueError("Five finite STF coordinates required")
    return np.einsum("...a,aij->...ij",v,E)


def stf_coordinates(S):
    S = np.asarray(S,float)
    if S.shape[-2:] != (3,3) or not np.all(np.isfinite(S)):
        raise ValueError("Symmetric finite 3x3 expected")
    # Test the tensor *relative to its own scale*. An absolute 1e-12 test
    # would falsely admit 1e-13*I as STF and corrupt small physical signals.
    scale=np.max(np.abs(S),axis=(-2,-1))
    tol=1e-12
    if np.any(np.abs(S-np.swapaxes(S,-1,-2)) > tol*scale[...,None,None]):
        raise ValueError("Not symmetric")
    if np.any(np.abs(np.trace(S,axis1=-2,axis2=-1)) > tol*scale):
        raise ValueError("Not trace-free")
    return np.einsum("...ij,aij->...a",S,E)


def stf_shape(S):
    """Scalar orbit invariants: I2, I3, signed chi, cubic discriminant.

    SO(3) orbit is determined by I2 and I3; chi undefined at zero.
    """
    S=np.asarray(S,float)
    stf_coordinates(S)
    # Normalize before taking the ratio: signed shape remains meaningful
    # for very small nonzero tensors (but I2/I3/D may underflow in float64).
    scale=np.max(np.abs(S),axis=(-2,-1))
    T=np.divide(S,scale[...,None,None],out=np.zeros_like(S),
                where=(scale[...,None,None]>0))
    q2=np.trace(T@T,axis1=-2,axis2=-1)
    q3=np.trace(T@T@T,axis1=-2,axis2=-1)
    chi=np.where(scale>0,np.sqrt(6)*q3/np.maximum(q2,1e-300)**1.5,np.nan)
    I2=(scale**2)*q2
    I3=(scale**3)*q3
    discriminant=(scale**6)*(q2**3/2-3*q3**2)
    return {"I2":I2,"I3":I3,"signed_chi":chi,"discriminant":discriminant}


def radiation_stress_gauge(S):
    """Minkowski gauge for K={S traceless symmetric; I/3+S PSD}.

    Exact normalized anisotropic pressure S=pi/rho of nonnegative intensity.
    Not a norm: Q(S) != Q(-S) generally; Q<=1 iff physically realizable.
    """
    S=np.asarray(S,float)
    stf_coordinates(S)
    return np.maximum(0.,-3*np.linalg.eigvalsh(S)[...,0])


def linear_target_identifiability(A,L,rtol=1e-11):
    """Exact linear identification and Euclidean stability of L theta from A theta.

    Requires the physical state be unconstrained in the linear regime.
    The local derivative analogue is only FIRST-ORDER, not a nonlinear no-go.
    """
    A=np.atleast_2d(np.asarray(A,float));L=np.atleast_2d(np.asarray(L,float))
    if A.shape[1]!=L.shape[1]:raise ValueError("Parameter dimension mismatch")
    if not np.all(np.isfinite(A)) or not np.all(np.isfinite(L)):
        raise ValueError("Nonfinite inputs")
    u,s,vt=np.linalg.svd(A,full_matrices=True)
    rank=int(np.sum(s > (s[0]*rtol if len(s) else 0)))
    null=vt[rank:,:].T
    leakage=float(np.linalg.norm(L@null,ord=2)) if null.shape[1] else 0.
    # EXACT theorem: any genuine nonzero leakage destroys identification.
    # Floating near-zero is NOT a proof of exact zero. Return an explicit
    # indeterminate state, never a false exact PASS.
    threshold=rtol*max(1.,np.linalg.norm(L,ord=2))
    if null.shape[1]==0:
        identified=True
        status="NUMERICALLY_FULL_RANK_AT_RTOL"
    elif leakage==0.:
        identified=True
        status="ZERO_LEAKAGE_IN_REPRESENTED_BASIS"
    elif leakage<=threshold:
        identified=None
        status="NUMERICALLY_AMBIGUOUS_NULL_LEAKAGE"
    else:
        identified=False
        status="RESOLVED_NONZERO_NULL_LEAKAGE"
    modulus=(float(np.linalg.norm(L@np.linalg.pinv(A,rcond=rtol),ord=2))
             if identified is True else (math.inf if identified is False else None))
    return {"identified":identified,"numerical_status":status,"rank":rank,
            "nullity":A.shape[1]-rank,"rank_relative_tolerance":rtol,
            "target_null_leakage":float(leakage),"stability_modulus":modulus}


def nuisance_projected_fisher(J,N,C):
    """Regular linear Gaussian experiment's profiled Fisher.

    This is standard efficient-score geometry, not added information.
    """
    J=np.atleast_2d(np.asarray(J,float));C=np.asarray(C,float)
    N=np.asarray(N,float)
    if C.shape!=(len(J),len(J)):raise ValueError("Covariance dimension")
    if N.ndim==1:N=N[:,None]
    if N.ndim!=2 or N.shape[0]!=len(J):raise ValueError("Nuisance dimension")
    L=np.linalg.cholesky(C)
    X=np.linalg.solve(L,J);Z=np.linalg.solve(L,N)
    if not Z.size:
        Q=np.zeros((len(J),0))
    else:
        # Normalize each NONZERO nuisance column before rank-revealing SVD.
        # Reparametrizing eta -> 1e12 eta must not delete nuisance directions.
        scales=np.max(np.abs(Z),axis=0)
        active=scales>0
        if not np.any(active):
            Q=np.zeros((len(J),0))
        else:
            standardized=Z[:,active]/scales[active]
            standardized/=np.linalg.norm(standardized,axis=0)
            u,s,vt=np.linalg.svd(standardized,full_matrices=False)
            tol=1e-11
            ratio=s/s[0]
            if np.any((ratio>tol/10) & (ratio<tol*10)):
                raise ValueError("Numerically ambiguous nuisance rank")
            rank=int(np.sum(ratio>tol))
            Q=u[:,:rank]
    R=X-Q@(Q.T@X)
    F=R.T@R
    return (F+F.T)/2


def best_axis_quadrupole_statistic(z):
    """Gaussian STF(3) white-noise axisymmetric signed amplitude profile LRT.

    z has five orthonormal coefficients N(0,I5). The fitted physical tensor is
    a *signed* multiple of sqrt(3/2)(n n-I/3), n is free on the sky.
    Optimizing over n and signed amplitude gives 3/2 max eigenvalue(S)^2.
    It is generally NOT chi-square with one degree of freedom.
    """
    S=stf_matrix(z)
    return 1.5*np.max(np.linalg.eigvalsh(S)**2,axis=-1)


def calibrate_axis_null(draws=85000,seed=20261118):
    rng=np.random.default_rng(seed)
    Z=rng.standard_normal((draws,5))
    T=best_axis_quadrupole_statistic(Z)
    return {"seed":seed,"draws":draws,
            "q95":float(np.quantile(T,.95)),
            "chi1_false_rejection_at_nominal5pct":float(np.mean(T>chi2.ppf(.95,1))),
            "chi5_false_rejection_at_nominal5pct":float(np.mean(T>chi2.ppf(.95,5))),
            "null":"isotropic Gaussian STF5, unknown axis+signed amplitude",
            "not":"Planck Commander end-to-end null"}


def transported_difference_covariance(Cii,Cjj,Cij,T):
    """Cov(x_j-T x_i) with original paired cross covariance."""
    Cii,Cjj,Cij,T=map(lambda a:np.asarray(a,float),(Cii,Cjj,Cij,T))
    if Cij.shape != (Cii.shape[0],Cjj.shape[0]):
        raise ValueError("Cij shape")
    return Cjj+T@Cii@T.T-T@Cij-Cij.T@T.T


R66_OBSERVABLES_SHA256="6d9c3f11a23995565dca25fe8ae02ef1ad79b3bc3f8ddf99f3c8c0a497b39d01"
R66_CARRIER_SHA256="807b8eb391b6d150596ab431885f4b720bcafedd52fffdfe61c6db132661cc48"


def r66_reused_stress(path):
    raw=Path(path).read_bytes()
    source_sha=hashlib.sha256(raw).hexdigest()
    if source_sha!=R66_OBSERVABLES_SHA256:
        raise ValueError("R66 OBSERVABLES.json byte identity mismatch")
    r=json.loads(raw)
    if (r.get("schema")!="htt.r66.actual_observables/1" or
            r.get("carrier_sha256")!=R66_CARRIER_SHA256):
        raise ValueError("R66 schema or carrier identity mismatch")
    outputs={}
    for label in ("PR3","PR4"):
        part=r["nonlinear"][label]
        b=part["radiation_moment_bundle"]
        if part["status"]!="EXACT_IN_DECLARED_RESTORED_ELL_LE_6_TEMPERATURE_FAMILY":
            raise ValueError("Expected R66 retained-sky physical model")
        v=np.asarray(b["pi5_over_rho"],float)
        S=stf_matrix(v)
        sh=stf_shape(S)
        outputs[label]={"pi5_over_rho":v.tolist(),
            "gauge_from_positive_intensity":float(radiation_stress_gauge(S)),
            "frobenius_stress":float(np.linalg.norm(S)),
            "signed_chi":float(sh["signed_chi"]),
            "discriminant":float(sh["discriminant"]),
            "eigenvalues":np.linalg.eigvalsh(S).tolist(),
            "positivity_body_pass":bool(np.linalg.eigvalsh(S).min()>=-1/3)}
    return {"schema":"htt.r68.reused_r66_physical_geometry/1",
            "R66_source_file_sha256":source_sha,
            "R66_carrier_identity":r["carrier_sha256"],"T0_K":r["T0_K"],
            "reference":"R66 retained ell<=6 temperature moment and same selected mask/operator",
            "qualification":"NOT exact total-sky CMB stress, not cosmic shear or an independently calibrated anomaly",
            "results":outputs}


def main():
    repo=Path(__file__).resolve().parents[2]
    r66=repo/"docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"
    out=repo/"docs/research_program/observational_publication_20261015/R68_FIVEVIEW_GEOMETRIC_RECONSTRUCTION_20261118"
    out.mkdir(exist_ok=True)
    result=r66_reused_stress(r66)
    result["axisymmetry_toy_null"]=calibrate_axis_null()
    (out/"R68_NUMERICAL_CHECKS.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"r66_stress_gauge":{k:v["gauge_from_positive_intensity"] for k,v in result["results"].items()},
                      "r66_signed_shapes":{k:v["signed_chi"] for k,v in result["results"].items()},
                      "axisymmetry_toy_null":result["axisymmetry_toy_null"]},indent=2))

if __name__=="__main__":main()
