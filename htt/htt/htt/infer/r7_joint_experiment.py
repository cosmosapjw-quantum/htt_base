"""Bind known joint laws; preserve unresolved cross-probe dependence."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.linalg import block_diag,null_space
from common.r7_contracts import ScopeKey,finite_array,content_id,NumericalUnresolved
from .r7_gaussian_law import JointObservationLaw,ObservationLawFactory,decompose_covariance,gaussian_acceptance


@dataclass(frozen=True)
class ExperimentPartition:
    admitted_laws: tuple
    subset_laws: tuple
    factories: tuple
    unresolved_cross_links: tuple
    duplicate_measurements: tuple[str,...]


@dataclass(frozen=True)
class JointGaussianProvider:
    """A supplied full joint covariance on ordered original measurements."""
    covariance: np.ndarray
    ordered_measurement_ids: tuple[str,...]
    source_id: str
    shared_latent_ids: tuple[str,...]
    conditioning_target: str

    def build(self,laws):
        if any(l.log_density is not None or callable(l.covariance) for l in laws):
            raise ValueError("constant joint Gaussian provider cannot bind nonlinear density/covariance")
        ids=tuple(i for law in laws for i in law.measurement_ids)
        if ids!=self.ordered_measurement_ids: raise ValueError("joint provider ordered measurement identity mismatch")
        covariance=decompose_covariance(self.covariance).covariance
        if covariance.shape!=(len(ids),len(ids)): raise ValueError("joint covariance dimensions")
        offset=0
        for law in laws:
            size=len(law.observed)
            if not np.array_equal(covariance[offset:offset+size,offset:offset+size],law.covariance):
                raise ValueError("joint covariance does not preserve a supplied marginal law")
            offset+=size
        names=laws[0].parameter_names;units=laws[0].parameter_units
        if any(l.parameter_names!=names or l.parameter_units!=units for l in laws): raise ValueError("joint parameter identities/units differ")
        # Repeated source IDs are kept once; covariance of a repeated measurement
        # must be identical to its original row/column, not independent noise.
        unique=[];index=[];duplicates=[]
        observed=np.concatenate([l.observed for l in laws])
        for i,name in enumerate(ids):
            if name in unique:
                old=index[unique.index(name)];duplicates.append(name)
                if observed[i]!=observed[old] or not np.array_equal(covariance[i],covariance[old]):
                    raise ValueError("duplicate identity has inconsistent value or joint noise law")
            else:unique.append(name);index.append(i)
        index=np.array(index,dtype=int);covariance=covariance[np.ix_(index,index)]
        spec={"source_ids":[l.specification_id for l in laws]+[self.source_id],"selection_law":"SUPPLIED_JOINT_LAW_MARGINALS",
            "covariance_source":self.source_id,"mean_definition":"concatenated aligned mean with repeated measurements retained once",
            "joint_covariance":covariance,"measurement_ids":unique,"conditioning":self.conditioning_target,
            "shared_latent_ids":self.shared_latent_ids}
        scope=ScopeKey("joint:"+content_id([l.scope.experiment_id for l in laws]),content_id(spec),laws[0].scope.model_id,
            tuple(dict.fromkeys(i for l in laws for i in l.scope.dataset_ids)),laws[0].scope.conventions,laws[0].scope.version,
            "gaussian_acceptance",content_id([l.scope.method_config_id for l in laws]))
        if any(l.scope.conventions!=scope.conventions or l.scope.version!=scope.version for l in laws): raise ValueError("joint convention/version mismatch")
        def mean(t,e):
            full=np.concatenate([l.mean(t,e) for l in laws])
            for name in duplicates:
                pos=[i for i,x in enumerate(ids) if x==name]
                if any(full[p]!=full[pos[0]] for p in pos): raise ValueError("duplicate source predictions disagree")
            return full[index]
        def jac(which,t,e):
            return np.vstack([getattr(l,which)(t,e) for l in laws])[index]
        joint=JointObservationLaw(scope,observed[index],tuple(unique),names,units,mean,covariance,spec,
            "intersection:"+content_id([l.domain_id for l in laws]),lambda t,e:all(l.domain_contains(t,e) for l in laws),
            jacobian_theta=(lambda t,e:jac("jacobian_theta",t,e)) if all(l.jacobian_theta for l in laws) else None,
            jacobian_eta=(lambda t,e:jac("jacobian_eta",t,e)) if all(l.jacobian_eta for l in laws) else None,
            shared_latent_ids=self.shared_latent_ids,conditioning_target=self.conditioning_target,
            support_tol=max(l.support_tol for l in laws),approximation="SUPPLIED_JOINT_GAUSSIAN_MODEL")
        return joint,tuple(duplicates)


def compose_joint_law(laws,overlap_table,shared_latent_provider) -> ExperimentPartition:
    laws=tuple(laws);bound=tuple(l for l in laws if isinstance(l,JointObservationLaw))
    factories=tuple(l for l in laws if isinstance(l,ObservationLawFactory))
    if len(bound)+len(factories)!=len(laws): raise TypeError("only bound laws and sealed factories can be composed")
    # Exact copies of one law are one experiment, even without an extra provider.
    unique=[];duplicates=[]
    for law in bound:
        match=next((l for l in unique if l.scope.identity==law.scope.identity and l.specification_id==law.specification_id),None)
        if match:
            if not np.array_equal(law.observed,match.observed): raise ValueError("same law identity has conflicting observations")
            duplicates.extend(law.measurement_ids)
        else:unique.append(law)
    bound=tuple(unique)
    if len(bound)<2:return ExperimentPartition(bound,bound,factories,(),tuple(duplicates))
    # Object matching is evidence-backed identity, never angular proximity.
    for row in overlap_table:
        if row.get("basis") in {"POSITION_ONLY","ANGULAR_NEAREST"} or not row.get("evidence"):
            raise ValueError("cross-probe overlap requires object/product evidence")
    if shared_latent_provider is not None:
        if not isinstance(shared_latent_provider,JointGaussianProvider): raise TypeError("supported joint sampling-law provider required")
        joint,more=shared_latent_provider.build(bound)
        return ExperimentPartition((joint,),bound,factories,(),tuple(duplicates)+more)
    links=tuple({"left":a.scope.experiment_id,"right":b.scope.experiment_id,
        "status":"CROSS_DEPENDENCE_UNAVAILABLE","next_input":"joint measurement/shared calibration law"}
        for i,a in enumerate(bound) for b in bound[:i])
    return ExperimentPartition(bound,bound,factories,links,tuple(duplicates))


@dataclass(frozen=True)
class IdentificationResult:
    parameter_names: tuple[str,...]
    parameter_units: tuple[str,...]
    singular_spectrum: np.ndarray
    kernel: np.ndarray
    efficient_information: np.ndarray
    exact_support_constraints: np.ndarray
    feasible_region: dict
    rank: int
    numeric_status: str


def analyze_identifiable_combinations(law,theta,eta,error_budget) -> IdentificationResult:
    if not isinstance(law,JointObservationLaw) or law.log_density is not None: raise TypeError("Gaussian bound law required")
    if law.jacobian_theta is None: raise ValueError("physical/observational response derivative unavailable")
    if callable(law.covariance): raise NumericalUnresolved("parameter-dependent covariance needs its full Fisher derivative adapter")
    if not law.domain_contains(theta,eta): raise ValueError("parameter outside law domain")
    c=decompose_covariance(law.covariance)
    if not c.resolved: raise NumericalUnresolved("covariance support rank unresolved")
    j=finite_array(law.jacobian_theta(theta,eta),shape=(len(law.observed),len(law.parameter_names)))
    v=finite_array(law.jacobian_eta(theta,eta),ndim=2) if law.jacobian_eta else np.empty((len(j),0))
    if len(v)!=len(j): raise ValueError("nuisance derivative dimensions")
    w=(c.eigenvectors[:,c.positive]/np.sqrt(c.eigenvalues[c.positive])).T
    dj=c.null.T@j;dv=c.null.T@v
    if v.shape[1]:
        pinv=np.linalg.pinv(dv) if dv.size else np.zeros((v.shape[1],dj.shape[0]))
        exact=dj-dv@pinv@dj
        nuisance_kernel=null_space(dv) if dv.shape[0] else np.eye(v.shape[1])
        effective=w@(j-v@pinv@dj);remaining=w@v@nuisance_kernel
        response=effective-remaining@np.linalg.pinv(remaining)@effective if remaining.size else effective
    else:exact=dj;response=w@j
    total=np.vstack((exact,response));sv=np.linalg.svd(total,compute_uv=False)
    tolerance=float(error_budget.get("absolute",0.))+float(error_budget.get("relative",1e-12))*(sv[0] if len(sv) else 0.)
    if not np.isfinite(tolerance) or tolerance<0: raise ValueError("valid response error budget required")
    rank=int(np.sum(sv>tolerance));kernel=null_space(total,rcond=(tolerance/sv[0] if len(sv) and sv[0] else None))
    return IdentificationResult(law.parameter_names,law.parameter_units,sv,kernel,response.T@response,exact,
        {"domain_id":law.domain_id,"local_tangent_only":True,"exact_constraints":"E dtheta=0"},rank,
        "LOCAL_NUMERICAL_RANK_WITH_DECLARED_ERROR_BUDGET")


def compare_p0_p1(law,baseline,design,design_id,parameter_labels):
    """Pre-provider fixed-column observation-space comparison under one law."""
    if not isinstance(law,JointObservationLaw) or law.log_density is not None or callable(law.covariance):
        raise TypeError("already bound fixed Gaussian experiment required")
    if not design_id: raise ValueError("predeclared column identity required")
    baseline=finite_array(baseline,shape=law.observed.shape);a=finite_array(design,ndim=2)
    if a.shape!=(len(baseline),len(parameter_labels)): raise ValueError("fixed design dimension")
    c=decompose_covariance(law.covariance)
    if not c.resolved: raise NumericalUnresolved("comparison covariance support rank unresolved")
    residual=law.observed-baseline
    exact=c.null.T@a;rhs=c.null.T@residual
    origin=np.linalg.lstsq(exact,rhs,rcond=None)[0] if exact.shape[0] else np.zeros(a.shape[1])
    if np.linalg.norm(exact@origin-rhs)>law.support_tol:
        return {"scope":law.scope.identity,"status":"P1_OUTSIDE_EXACT_SUPPORT","design_id":design_id}
    z=null_space(exact) if exact.shape[0] else np.eye(a.shape[1])
    w=(c.eigenvectors[:,c.positive]/np.sqrt(c.eigenvalues[c.positive])).T
    b=w@a@z;target=w@(residual-a@origin)
    fit=origin+z@np.linalg.lstsq(b,target,rcond=None)[0]
    p0=gaussian_acceptance(residual,law.covariance,.05,law.support_tol)
    p1=gaussian_acceptance(residual-a@fit,law.covariance,.05,law.support_tol)
    return {"scope":law.scope.identity,"status":"OBSERVATION_SPACE_COMPARISON","design_id":design_id,
        "parameter_labels":tuple(parameter_labels),"coefficients":fit,"p0":p0,"p1":p1,
        "p1_nonidentified_directions":null_space(np.vstack((exact,w@a))),
        "uncertainty":"full residual acceptance rank; no Wilks subtraction",
        "physical_interpretation":"fixed observational columns; no Bianchi family attribution"}
