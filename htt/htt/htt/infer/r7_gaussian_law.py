"""Known-law Gaussian inference with explicit singular support (R7 T4/T6).

No estimated-covariance plug-in law, jitter, Wilks approximation or empirical
eligibility is supplied by these kernels.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import math
import hashlib
import marshal
import types
import numpy as np
from scipy.linalg import null_space
from scipy.stats import chi2

from common.r7_contracts import (AcceptanceResult, ConditionalGaussian,
    InformationResult, ScopeKey, NumericalUnresolved, finite_array, content_id)


@dataclass(frozen=True)
class PSDDecomposition:
    covariance: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    positive: np.ndarray
    error_bound: float
    resolved: bool

    @property
    def rank(self): return int(np.sum(self.positive))

    @property
    def inverse(self):
        if not self.resolved: raise NumericalUnresolved("covariance rank is unresolved")
        u = self.eigenvectors[:, self.positive]
        return (u / self.eigenvalues[self.positive]) @ u.T

    @property
    def null(self): return self.eigenvectors[:, ~self.positive]


def decompose_covariance(covariance) -> PSDDecomposition:
    c = finite_array(covariance, ndim=2, name="covariance")
    if c.shape[0] != c.shape[1] or not c.shape[0]: raise ValueError("covariance must be nonempty square")
    scale = float(np.linalg.norm(c, ord=2))
    error = 32 * len(c) * np.finfo(float).eps * scale
    if np.max(np.abs(c-c.T)) > error:
        raise ValueError("covariance is asymmetric beyond floating-point error")
    symmetric = (c+c.T)/2
    vals, vecs = np.linalg.eigh(symmetric)
    if np.any(vals < -error): raise ValueError("covariance is not positive semidefinite")
    # Exact zero is retained. A nonzero eigenvalue inside the eigensolver error
    # enclosure has unknown sign/rank; it cannot be silently truncated or lifted.
    unresolved = np.any((vals != 0) & (np.abs(vals) <= error))
    return PSDDecomposition(symmetric, vals, vecs, vals > error, error, not unresolved)


def gaussian_acceptance(residual, covariance, alpha, support_tol) -> AcceptanceResult:
    if not math.isfinite(alpha) or not 0 < alpha < 1: raise ValueError("alpha must lie in (0,1)")
    if not math.isfinite(support_tol) or support_tol < 0: raise ValueError("invalid support tolerance")
    d = decompose_covariance(covariance)
    r = finite_array(residual, shape=(len(d.covariance),), name="residual")
    if not d.resolved:
        return AcceptanceResult(False,None,None,None,False,"NUMERICALLY_UNRESOLVED")
    numeric_bound=32*len(r)*np.finfo(float).eps*(np.linalg.norm(r)+math.sqrt(np.linalg.norm(d.covariance,2)))
    if support_tol>numeric_bound:raise ValueError("support tolerance exceeds numerical error bound; bounded measurement error requires a separate law")
    support_residual=float(np.linalg.norm(d.null.T@r)) if d.null.size else 0.
    if 0<support_residual<=support_tol:
        return AcceptanceResult(False,None,d.rank,None,False,"NUMERICALLY_UNRESOLVED")
    inside = support_residual==0.
    u = d.eigenvectors[:,d.positive].T @ r
    quadratic = float(np.sum(u*u/d.eigenvalues[d.positive]))
    threshold = float(chi2.ppf(1-alpha,d.rank)) if d.rank else 0.
    return AcceptanceResult(bool(inside),quadratic,d.rank,threshold,
        bool(inside and quadratic <= threshold),"RESOLVED")


def gaussian_loglik(residual, covariance, support_tol=0.):
    d = decompose_covariance(covariance)
    result = gaussian_acceptance(residual,covariance,.05,support_tol)
    if not d.resolved or result.numeric_status=="NUMERICALLY_UNRESOLVED": raise NumericalUnresolved("Gaussian density support/rank is unresolved")
    if not result.inside_support: return -math.inf
    return -.5*(d.rank*math.log(2*math.pi) +
                 np.log(d.eigenvalues[d.positive]).sum()+result.quadratic)


def condition_gaussian(mean_y, mean_z, Cyy, Cyz, Czz, z) -> ConditionalGaussian:
    my = finite_array(mean_y,ndim=1,name="mean_y")
    mz = finite_array(mean_z,ndim=1,name="mean_z")
    z = finite_array(z,shape=mz.shape,name="z")
    yy=finite_array(Cyy,shape=(len(my),len(my)),name="Cyy")
    yz=finite_array(Cyz,shape=(len(my),len(mz)),name="Cyz")
    zz=decompose_covariance(Czz)
    if zz.covariance.shape != (len(mz),len(mz)): raise ValueError("Czz dimension mismatch")
    joint = decompose_covariance(np.block([[yy,yz],[yz.T,zz.covariance]]))
    if not zz.resolved: raise NumericalUnresolved("conditioning covariance rank unresolved")
    # Validate joint PSD, but its roundoff-uncertain duplicate eigenvalues do not
    # alter the declared Czz support or the block-conditioning identity.
    delta=z-mz
    support_error=32*np.finfo(float).eps*max(float(np.linalg.norm(delta)),math.sqrt(np.linalg.norm(zz.covariance,2)))
    if zz.null.size and np.linalg.norm(zz.null.T@delta)>support_error:
        raise ValueError("conditioning observation is outside Gaussian support")
    W=yz@zz.inverse
    c=yy-W@yz.T
    # A computed Schur complement carries a cancellation-error bound. Only a
    # whole zero block proven by exact duplicate block identity is set to zero.
    duplicate=yy.shape==zz.covariance.shape and np.array_equal(yy,yz) and np.array_equal(yz,zz.covariance)
    if duplicate:
        c=np.zeros_like(yy)
    c=(c+c.T)/2
    cancellation_error=64*(len(my)+len(mz))*np.finfo(float).eps*(np.linalg.norm(yy,2)+np.linalg.norm(W,2)*np.linalg.norm(yz,2))
    eig=np.linalg.eigvalsh(c)
    uncertain=not duplicate and np.any(eig<=cancellation_error)
    status="NUMERICALLY_UNRESOLVED" if uncertain else "RESOLVED"
    return ConditionalGaussian(my+W@delta,c,W,zz.rank,status)


def conditional_mean_derivative(mu_y_i, mu_z_i, W, W_i, z_minus_mu_z):
    y=finite_array(mu_y_i,ndim=1);z=finite_array(mu_z_i,ndim=1)
    gain=finite_array(W,shape=(len(y),len(z)))
    deriv=finite_array(W_i,shape=gain.shape)
    residual=finite_array(z_minus_mu_z,shape=z.shape)
    return y-gain@z+deriv@residual


def _kernel(matrix):
    return null_space(matrix,rcond=32*max(matrix.shape)*np.finfo(float).eps)


def calibration_information_gain(U,V,E,G) -> InformationResult:
    u=finite_array(U,ndim=2);v=finite_array(V,ndim=2)
    e=decompose_covariance(E);g=decompose_covariance(G)
    if u.shape!=(v.shape[0],v.shape[0]) or v.shape[1]!=len(e.covariance) or g.covariance.shape!=e.covariance.shape:
        raise ValueError("information block dimensions disagree")
    if not e.resolved or e.rank!=len(e.covariance):
        raise ValueError("T6 requires a positive-definite identified nuisance block")
    decompose_covariance(np.block([[u,v],[v.T,e.covariance]]))
    newer=decompose_covariance(e.covariance+g.covariance)
    old=u-v@e.inverse@v.T; new=u-v@newer.inverse@v.T
    gain=new-old
    return InformationResult(old,new,gain,_kernel(old),_kernel(new),_kernel(gain))


def _execution_state(value, seen=None):
    """Fingerprint live prediction state, including mutable captured arrays.

    This is a local reproducibility check, not a security boundary. A callable
    with opaque external state must expose that state through its bound object
    or use a separately source-bound provider adapter.
    """
    seen=set() if seen is None else seen
    if isinstance(value,np.ndarray):return {"array_dtype":str(value.dtype),"shape":value.shape,"bytes":hashlib.sha256(value.tobytes()).hexdigest()}
    if isinstance(value,np.generic):return _execution_state(value.item(),seen)
    if isinstance(value,float) and not math.isfinite(value):return {"floating_state":repr(value)}
    if value is None or isinstance(value,(str,int,float,bool)):return value
    if type(value).__module__.startswith("scipy.stats."):
        return {"distribution":type(value).__module__+"."+type(value).__qualname__,"name":getattr(value,"name",None),
            "args":_execution_state(getattr(value,"args",()),seen),"kwds":_execution_state(getattr(value,"kwds",{}),seen)}
    if id(value) in seen:return {"cycle":type(value).__qualname__}
    seen=seen|{id(value)}
    if isinstance(value,(list,tuple)):return [_execution_state(v,seen) for v in value]
    if isinstance(value,dict):return {str(k):_execution_state(v,seen) for k,v in value.items()}
    if isinstance(value,types.ModuleType):return {"module":value.__name__,"version":getattr(value,"__version__",None)}
    if isinstance(value,types.MethodType):return {"method":_execution_state(value.__func__,seen),"self":_execution_state(value.__self__,seen)}
    if isinstance(value,types.FunctionType):
        module=value.__module__ or ""
        if module.startswith(("numpy.","scipy.")):
            return {"library_function":module+"."+value.__qualname__}
        captured={name:_execution_state(value.__globals__[name],seen) for name in value.__code__.co_names
                  if name in value.__globals__ and not name.startswith("__")}
        return {"function":module+"."+value.__qualname__,"code":hashlib.sha256(marshal.dumps(value.__code__)).hexdigest(),
                "defaults":_execution_state(value.__defaults__,seen),"keywords":_execution_state(value.__kwdefaults__,seen),
                "closure":[_execution_state(c.cell_contents,seen) for c in (value.__closure__ or ())],"globals":captured}
    if isinstance(value,type):return {"class":value.__module__+"."+value.__qualname__}
    if hasattr(value,"__dict__"):
        return {"type":type(value).__module__+"."+type(value).__qualname__,
                "state":{k:_execution_state(v,seen) for k,v in vars(value).items() if k not in {"_execution_seal","_binding_token"}},
                "call_implementation":_execution_state(getattr(type(value),"__call__",None),seen) if callable(value) else None}
    return {"opaque_type":type(value).__module__+"."+type(value).__qualname__,"identity":repr(value)}


@dataclass(frozen=True)
class JointObservationLaw:
    scope: ScopeKey
    observed: np.ndarray
    measurement_ids: tuple[str,...]
    parameter_names: tuple[str,...]
    parameter_units: tuple[str,...]
    mean: Callable
    covariance: np.ndarray | Callable | None
    specification: dict
    domain_id: str
    domain_contains: Callable
    jacobian_theta: Callable | None = None
    jacobian_eta: Callable | None = None
    shared_latent_ids: tuple[str,...] = ()
    conditioning_target: str = "UNCONDITIONAL_KNOWN_GAUSSIAN"
    support_tol: float = 0.
    approximation: str = "EXACT_WITHIN_DECLARED_GAUSSIAN_MODEL"
    transfer_source: str = "OBSERVATION_SPACE"
    log_density: Callable | None = None

    def __post_init__(self):
        y=finite_array(self.observed,ndim=1,name="observed")
        object.__setattr__(self,"observed",y)
        if len(self.measurement_ids)!=len(y) or len(set(self.measurement_ids))!=len(y):
            raise ValueError("unique ordered measurement identities required")
        if len(self.parameter_names)!=len(self.parameter_units) or len(set(self.parameter_names))!=len(self.parameter_names):
            raise ValueError("ordered unique parameter names/units required")
        for key in ("source_ids","selection_law","covariance_source","mean_definition"):
            if not self.specification.get(key): raise ValueError(f"law specification needs {key}")
        if self.log_density is not None and not self.specification.get("normalized_density_definition"):
            raise ValueError("non-Gaussian law requires its normalization definition")
        if self.covariance is None and self.log_density is None: raise ValueError("covariance or normalized density required")
        if self.covariance is not None and not callable(self.covariance):
            c=decompose_covariance(self.covariance)
            if c.covariance.shape!=(len(y),len(y)): raise ValueError("covariance dimension mismatch")
            object.__setattr__(self,"covariance",finite_array(self.covariance,ndim=2))
        object.__setattr__(self,"_spec_id",content_id(self.specification))
        # A calibration is also bound to the exact live implementation objects.
        # Reconstructed laws must reconstruct their calibration; copying text
        # identities cannot silently replace a prediction or domain callable.
        object.__setattr__(self,"_binding_token",object())
        object.__setattr__(self,"_execution_seal",self.execution_identity)

    @property
    def execution_identity(self):
        return content_id(_execution_state((self.mean,self.covariance,self.domain_contains,self.log_density,self.jacobian_theta,self.jacobian_eta,self.observed,self.measurement_ids,self.parameter_names,self.parameter_units)))

    @property
    def specification_id(self):
        if content_id(self.specification)!=self._spec_id: raise ValueError("bound law specification mutated")
        if self.execution_identity!=self._execution_seal:raise ValueError("bound law callable state mutated")
        return self._spec_id

    def covariance_at(self,theta,eta=None):
        return self.covariance(theta,eta) if callable(self.covariance) else self.covariance

    def loglik(self,theta,eta=None):
        self.specification_id
        if not self.domain_contains(theta,eta): return -math.inf
        if self.log_density is not None:
            value=float(self.log_density(theta,eta))
            if math.isnan(value) or value==math.inf: raise NumericalUnresolved("invalid normalized log density")
            return value
        return gaussian_loglik(self.observed-self.mean(theta,eta),
                                self.covariance_at(theta,eta),self.support_tol)


@dataclass(frozen=True)
class ObservationLawFactory:
    factory_id: str
    measurement_ids: tuple[str,...]
    unfilled_prediction_slots: tuple[str,...]
    specification: dict
    builder: Callable

    def __post_init__(self):
        if not self.unfilled_prediction_slots: raise ValueError("factory must identify missing prediction slots")
        object.__setattr__(self,"_seal",content_id(self.specification))

    @property
    def empirical_eligible(self): return False

    def bind(self,provider):
        if content_id(self.specification)!=self._seal: raise ValueError("factory specification changed")
        available=provider.capabilities()
        missing=set(self.unfilled_prediction_slots)-set(available)
        if missing: raise ValueError(f"unsupported prediction slots: {sorted(missing)}")
        law=self.builder(provider)
        if not isinstance(law,JointObservationLaw): raise TypeError("binding must return a normalized observation law")
        return law


def require_fixed_known_gaussian(law):
    if not isinstance(law,JointObservationLaw) or law.log_density is not None:
        raise TypeError("fixed Gaussian acceptance requires a bound Gaussian law")
    if callable(law.covariance):raise ValueError("variable covariance requires separate uniform numerical obligations")
    if any(word in law.approximation.upper() for word in ('EMPIRICAL','APPROXIMATION','ESTIMATED','QUADRATURE')):
        raise ValueError("an approximate/estimated law cannot use fixed known-Gaussian confidence")
    law.specification_id
