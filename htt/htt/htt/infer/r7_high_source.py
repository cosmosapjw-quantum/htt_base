"""Four distinct high-source nuisance experiments, R7 T4."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from scipy.linalg import null_space
from scipy.optimize import brentq, minimize
from common.r7_contracts import finite_array, NumericalUnresolved
from .r7_gaussian_law import decompose_covariance, gaussian_loglik


@dataclass(frozen=True)
class CostResult:
    cost: float
    in_range: bool
    range_witness: np.ndarray
    minimum_nuisance: np.ndarray | None
    numeric_status: str


def cancellation_cost(K,S,d,range_tolerance) -> CostResult:
    k=finite_array(K,ndim=2);s=decompose_covariance(S);v=finite_array(d,shape=(len(k),))
    if s.rank!=k.shape[1] or not s.resolved: raise ValueError("S must be positive definite on nuisance coordinates")
    if not math.isfinite(range_tolerance) or range_tolerance<0: raise ValueError("invalid range tolerance")
    # Use the explicit K image rather than rounding eigenvalues of KSK^T.
    root=s.eigenvectors*np.sqrt(s.eigenvalues)
    m=k@root;u,sv,vt=np.linalg.svd(m,full_matrices=True)
    error=32*max(m.shape)*np.finfo(float).eps*(sv[0] if len(sv) else 0.)
    if np.any((sv!=0)&(sv<=error)): raise NumericalUnresolved("cancellation image rank unresolved")
    rank=int(np.sum(sv>error));witness=u[:,rank:].T@v
    if np.linalg.norm(witness)>range_tolerance:
        return CostResult(math.inf,False,u[:,rank:]@witness,None,"RESOLVED")
    coeff=(u[:,:rank].T@v)/sv[:rank]
    h=root@vt[:rank].T@coeff
    return CostResult(float(coeff@coeff),True,u[:,rank:]@witness,h,"RESOLVED")


@dataclass(frozen=True)
class HighSourcePolicy:
    branch: str
    coverage_target: str
    h0: np.ndarray | None = None
    S: np.ndarray | None = None
    radius: float | None = None
    positivity_matrix: np.ndarray | None = None
    positivity_lower: np.ndarray | None = None
    joint_z: np.ndarray | None = None
    joint_B: np.ndarray | None = None
    joint_covariance: np.ndarray | None = None
    law_id: str = ""

    def __post_init__(self):
        if self.branch not in {"UNRESTRICTED","ELLIPSOID","GAUSSIAN","JOINT_MEASURED"}: raise ValueError("unknown nuisance law")
        if not self.coverage_target or not self.law_id: raise ValueError("each branch requires its law and coverage target")


@dataclass(frozen=True)
class ProfileResult:
    branch: str
    quadratic: float | None
    degrees_of_freedom: int | None
    nuisance_witness: np.ndarray | None
    residual: np.ndarray
    response: np.ndarray
    null_directions: np.ndarray
    covariance: np.ndarray
    loglik: float | None
    numeric_status: str
    coverage_target: str
    law_id: str
    objective_lower_bound: float | None = None


def profile_high_source(y,A,K,noise,policy,theta) -> ProfileResult:
    a=finite_array(A,ndim=2);k=finite_array(K,ndim=2);v=finite_array(y,shape=(len(a),))
    theta=finite_array(theta,shape=(a.shape[1],));n=decompose_covariance(noise)
    if k.shape[0]!=len(v) or n.covariance.shape!=(len(v),len(v)): raise ValueError("high-source dimensions")
    if not n.resolved or n.rank!=len(v): raise ValueError("T4 profile requires positive noise covariance")
    w=(n.eigenvectors/np.sqrt(n.eigenvalues)).T
    h0=np.zeros(k.shape[1]) if policy.h0 is None else finite_array(policy.h0,shape=(k.shape[1],))
    residual=v-a@theta
    if policy.branch=="UNRESTRICTED":
        m=w@k;basis=null_space(m.T);response=basis.T@w@a
        r=basis.T@w@residual;h=np.linalg.lstsq(m,w@residual,rcond=None)[0]
        return ProfileResult(policy.branch,float(r@r),len(r),h,r,response,null_space(response),np.eye(len(r)),
            None,"RESOLVED_QUOTIENT",policy.coverage_target,policy.law_id,float(r@r))
    if policy.branch=="GAUSSIAN":
        s=decompose_covariance(policy.S)
        if s.covariance.shape!=(len(h0),len(h0)): raise ValueError("high-source covariance dimensions")
        c=n.covariance+k@s.covariance@k.T;r=residual-k@h0;d=decompose_covariance(c)
        q=float(r@d.inverse@r)
        return ProfileResult(policy.branch,q,d.rank,None,r,a,null_space(a),c,gaussian_loglik(r,c),
            "RESOLVED_MARGINALIZED_LAW",policy.coverage_target,policy.law_id,q)
    if policy.branch=="JOINT_MEASURED":
        z=finite_array(policy.joint_z,ndim=1);b=finite_array(policy.joint_B,shape=(len(z),len(theta)))
        c=decompose_covariance(policy.joint_covariance);r=np.concatenate((residual,z-b@theta))
        if c.covariance.shape!=(len(r),len(r)): raise ValueError("full joint covariance including cross blocks required")
        ll=gaussian_loglik(r,c.covariance);response=np.vstack((a,b))
        q=float(r@c.inverse@r) if math.isfinite(ll) else math.inf
        return ProfileResult(policy.branch,q,c.rank,None,r,response,null_space(response),c.covariance,ll,
            "RESOLVED_JOINT_LAW",policy.coverage_target,policy.law_id,q)
    s=decompose_covariance(policy.S)
    if not s.resolved or s.rank!=len(h0): raise ValueError("H1 ellipsoid requires positive definite S")
    rho=policy.radius
    if rho is None or not math.isfinite(rho) or rho<0: raise ValueError("nonnegative finite ellipsoid radius required")
    root=s.eigenvectors*np.sqrt(s.eigenvalues);m=w@k@root;target=w@(residual-k@h0)
    u0=np.linalg.lstsq(m,target,rcond=None)[0];lam=0.
    if np.linalg.norm(u0)>rho:
        if rho==0: u0=np.zeros(len(h0));lam=math.inf
        else:
            _,sv,vt=np.linalg.svd(m,full_matrices=False);rhs=vt@(m.T@target)
            def solution(l): return vt.T@(rhs/(sv**2+l))
            hi=max(1.,np.linalg.norm(m.T@target)/rho)
            lam=brentq(lambda l:np.linalg.norm(solution(l))-rho,np.finfo(float).tiny,hi,xtol=1e-14)
            u0=solution(lam)
    status="RESOLVED_ELLIPSOID_PROFILE";lower=None
    if policy.positivity_matrix is not None:
        p=finite_array(policy.positivity_matrix,ndim=2)
        bound=finite_array(policy.positivity_lower,shape=(len(p),))
        if p.shape[1]!=len(h0): raise ValueError("positive-sky linear constraint dimension")
        fit=minimize(lambda u:float(np.linalg.norm(target-m@u)**2),u0,method="SLSQP",
            constraints=[{"type":"ineq","fun":lambda u:rho*rho-u@u},
                         {"type":"ineq","fun":lambda u:p@(h0+root@u)-bound}],
            options={"ftol":1e-12,"maxiter":1000})
        candidate=fit.x
        feasible=np.linalg.norm(candidate)<=rho and np.all(p@(h0+root@candidate)>=bound)
        u0=candidate if feasible else None
        status="OUTER_PROFILE_UNRESOLVED_POSITIVE_SKY"
    h=h0+root@u0 if u0 is not None else None
    r=w@(residual-k@h) if h is not None else target
    if policy.positivity_matrix is None:
        lower=float(r@r)  # analytic trust-region optimum, evaluated in binary64
    return ProfileResult(policy.branch,float(r@r) if h is not None else None,len(v),h,r,w@a,
        null_space(w@a),n.covariance,None,status,policy.coverage_target,policy.law_id,lower)


def gaussian_fisher(mean_derivatives,covariance,covariance_derivatives):
    d=decompose_covariance(covariance)
    if not d.resolved or d.rank!=len(d.covariance): raise ValueError("regular Gaussian Fisher requires fixed positive support")
    j=finite_array(mean_derivatives,ndim=2);derivatives=finite_array(covariance_derivatives,shape=(j.shape[1],len(j),len(j)))
    if len(j)!=d.rank: raise ValueError("Fisher derivative dimension")
    inverse=d.inverse;f=j.T@inverse@j
    for i in range(j.shape[1]):
        for k in range(j.shape[1]): f[i,k]+=.5*np.trace(inverse@derivatives[i]@inverse@derivatives[k])
    return f
