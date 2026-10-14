"""Bind known joint laws; preserve unresolved cross-probe dependence."""
from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np
from typing import Callable
from scipy.special import logsumexp
from scipy.linalg import block_diag,null_space
from common.r7_contracts import ScopeKey,finite_array,content_id,NumericalUnresolved
from .r7_gaussian_law import JointObservationLaw,ObservationLawFactory,decompose_covariance,gaussian_acceptance,gaussian_loglik


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


@dataclass(frozen=True)
class ProperSharedLatentRule:
    """One supplied probability measure, integrated once across all products.

    DISCRETE_EXACT is a finite proper prior. CONTINUOUS_QUADRATURE is only
    its supplied finite approximation, never certified continuous evidence.
    Positive weights must already sum to one; no prior is repaired/renormalized.
    """
    latent_ids: tuple[str, ...]
    nodes: np.ndarray
    weights: np.ndarray
    source_id: str
    measure_kind: str = "DISCRETE_EXACT"

    def __post_init__(self):
        nodes = finite_array(self.nodes, ndim=2).copy()
        weights = finite_array(self.weights, shape=(len(nodes),)).copy()
        if (not self.source_id or not self.latent_ids or len(set(self.latent_ids)) != len(self.latent_ids)
                or not all(self.latent_ids) or nodes.shape[1] != len(self.latent_ids) or not len(nodes)):
            raise ValueError("source-bound ordered shared latent identities/nodes required")
        if self.measure_kind not in {"DISCRETE_EXACT", "CONTINUOUS_QUADRATURE"}:
            raise ValueError("explicit proper latent measure kind required")
        if np.any(weights <= 0) or abs(float(weights.sum())-1.) > 64*np.finfo(float).eps:
            raise ValueError("proper positive latent weights summing to one required")
        nodes.setflags(write=False); weights.setflags(write=False)
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "weights", weights)


@dataclass(frozen=True)
class SelectedConditionalBlock:
    """Source-bound selected density w.r.t. ordered original measurement dY.

    The callable takes (Y, theta, shared_latent). Normalization is a supplied
    model obligation, including selection at every theta/latent; a profile or
    unnormalized objective cannot be declared here. Counts are conditioned on.
    """
    law_specification_id: str
    law_scope_id: str
    measurement_ids: tuple[str, ...]
    object_ids: tuple[str, ...]
    source_id: str
    selection_id: str
    normalization_definition: str
    log_density: Callable
    density_kind: str = "NORMALIZED_SELECTED_CONDITIONAL_LEBESGUE"
    count_conditioning: str = "FIXED_OBSERVED_COUNT"

    def __post_init__(self):
        if (not all((self.law_specification_id, self.law_scope_id, self.source_id,
                     self.selection_id, self.normalization_definition))
                or len(self.object_ids) != len(self.measurement_ids) or not all(self.object_ids)
                or len(set(self.measurement_ids)) != len(self.measurement_ids)
                or not self.measurement_ids or not all(self.measurement_ids)):
            raise ValueError("source/law/ordered measurement/object/selection identities required")
        if self.density_kind != "NORMALIZED_SELECTED_CONDITIONAL_LEBESGUE":
            raise ValueError("profile/objective is not a normalized evidence density")
        if self.count_conditioning != "FIXED_OBSERVED_COUNT" or not callable(self.log_density):
            raise ValueError("fixed-count normalized conditional density required")


@dataclass(frozen=True)
class PublishedGaussianSummaryBlock:
    """One fixed-covariance released summary density on its original dY.

    Its summary conditioning is kept verbatim. The mean and covariance must be
    the bound source law's own objects; a block cannot substitute a new response
    while retaining the old source identity. Shared latent nodes do not enter
    this summary block unless a future source-bound response explicitly does so.
    """
    law_specification_id: str
    law_scope_id: str
    law_execution_identity: str
    measurement_ids: tuple[str, ...]
    object_ids: tuple[str, ...]
    source_id: str
    selection_id: str
    normalization_definition: str
    mean: Callable
    covariance: np.ndarray
    density_kind: str = "NORMALIZED_PUBLISHED_GAUSSIAN_SUMMARY_LEBESGUE"
    count_conditioning: str = "PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE"

    def __post_init__(self):
        if (not all((self.law_specification_id,self.law_scope_id,self.law_execution_identity,
                     self.source_id,self.selection_id,self.normalization_definition))
                or not self.measurement_ids or len(self.object_ids)!=len(self.measurement_ids)
                or not all(self.object_ids) or len(set(self.measurement_ids))!=len(self.measurement_ids)
                or not callable(self.mean)):
            raise ValueError("source-bound released summary and ordered object identities required")
        if (self.density_kind!="NORMALIZED_PUBLISHED_GAUSSIAN_SUMMARY_LEBESGUE"
                or self.count_conditioning!="PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE"):
            raise ValueError("original released Gaussian summary conditioning required")
        c=decompose_covariance(self.covariance)
        if not c.resolved or c.rank!=len(self.measurement_ids) or c.covariance.shape!=(len(self.measurement_ids),)*2:
            raise ValueError("positive-definite fixed released summary covariance required")
        object.__setattr__(self,"covariance",c.covariance)

    def log_density(self,y,theta,latent):
        observed=finite_array(y,shape=(len(self.measurement_ids),))
        predicted=finite_array(self.mean(theta,None),shape=observed.shape)
        return gaussian_loglik(observed-predicted,self.covariance)

    def provenance(self):
        return {key:getattr(self,key) for key in ("law_specification_id","law_scope_id",
            "law_execution_identity","measurement_ids","object_ids","source_id",
            "selection_id","normalization_definition","density_kind","count_conditioning")}


@dataclass(frozen=True)
class SelectedJointDensityProvider:
    """Compose supplied selected blocks under one proper shared latent rule.

    Factorization requires an explicit source-bound conditional independence
    assertion. Otherwise joint_log_density supplies the full normalized joint
    conditional law on canonical unique Y. Partial duplicate factorizations
    cannot be repaired by multiplying marginal block densities.
    """
    blocks: tuple[SelectedConditionalBlock, ...]
    ordered_measurement_ids: tuple[str, ...]
    latent_rule: ProperSharedLatentRule
    source_id: str
    conditional_independence_source: str | None = None
    joint_log_density: Callable | None = None
    joint_normalization_definition: str | None = None
    joint_density_kind: str = "NORMALIZED_SELECTED_CONDITIONAL_LEBESGUE"

    def build(self, laws):
        laws = tuple(laws)
        if not laws or not self.source_id or not isinstance(self.latent_rule, ProperSharedLatentRule):
            raise ValueError("bound laws and source-bound proper latent rule required")
        if len(self.blocks) != len(laws) or any(not isinstance(b, (SelectedConditionalBlock,PublishedGaussianSummaryBlock)) for b in self.blocks):
            raise ValueError("one typed selected or published-summary conditional block per deduplicated law required")
        if self.joint_log_density is None:
            if not self.conditional_independence_source:
                raise ValueError("conditional independence source or explicit joint conditional provider required")
        elif (not callable(self.joint_log_density) or not self.joint_normalization_definition
              or self.joint_density_kind != "NORMALIZED_SELECTED_CONDITIONAL_LEBESGUE"):
            raise ValueError("normalized joint conditional density definition required")
        first = laws[0]
        ids=[]; values=[]; owners=[]; duplicates=[]; block_indices=[]
        for law, block in zip(laws, self.blocks):
            summary=isinstance(block,PublishedGaussianSummaryBlock)
            if summary:
                if (law.conditioning_target!=block.count_conditioning or law.log_density is not None
                        or callable(law.covariance) or law.shared_latent_ids
                        or block.mean is not law.mean or block.law_execution_identity!=law.execution_identity
                        or not np.array_equal(block.covariance,law.covariance)):
                    raise ValueError("released summary conditioning/covariance/prediction binding mismatch")
            elif law.conditioning_target not in {
                    "FIXED_OBSERVED_COUNT", "SELECTED_JOINT_BLOCK_GIVEN_LATENT_FIELD_AND_COUNT"}:
                raise ValueError("supported fixed-observed-count source conditioning required")
            if not law.transfer_source or not law.approximation:
                raise ValueError("input transfer source and approximation status required")
            if (law.specification_id != block.law_specification_id or law.scope.identity != block.law_scope_id
                    or law.measurement_ids != block.measurement_ids
                    or law.specification['selection_law'] != block.selection_id
                    or block.source_id not in law.specification['source_ids']):
                raise ValueError("conditional block source/law/order/selection binding mismatch")
            if (law.parameter_names != first.parameter_names or law.parameter_units != first.parameter_units
                    or law.scope.model_id != first.scope.model_id or law.scope.conventions != first.scope.conventions
                    or law.scope.version != first.scope.version
                    or (law.shared_latent_ids != (() if summary else self.latent_rule.latent_ids))):
                raise ValueError("shared parameter/model/convention/conditioning/latent scope mismatch")
            indices=[]
            for name, obj, value in zip(law.measurement_ids, block.object_ids, law.observed):
                if name in ids:
                    j=ids.index(name); oldlaw, oldblock, oldobj=owners[j]
                    if (value != values[j] or obj != oldobj or block.source_id != oldblock.source_id
                            or block.selection_id != oldblock.selection_id
                            or law.scope.identity != oldlaw.scope.identity
                            or law.specification_id != oldlaw.specification_id):
                        raise ValueError("duplicate measurement has inconsistent value/source/object/scope")
                    duplicates.append(name)
                else:
                    j=len(ids); ids.append(name); values.append(value); owners.append((law,block,obj))
                indices.append(j)
            block_indices.append(np.asarray(indices, dtype=int))
        if tuple(ids) != self.ordered_measurement_ids:
            raise ValueError("joint provider canonical ordered measurement identity mismatch")
        if duplicates and self.joint_log_density is None:
            raise ValueError("overlapping blocks require an explicit joint conditional density on unique Y")
        observed=np.asarray(values, dtype=float); observed.setflags(write=False)
        rule=self.latent_rule
        input_provenance=[{"law_specification_id":l.specification_id, "scope_id":l.scope.identity,
                           "transfer_source":l.transfer_source, "approximation":l.approximation,
                           "conditioning_target":l.conditioning_target} for l in laws]
        transfers=tuple(dict.fromkeys(l.transfer_source for l in laws))
        transfer_source=(transfers[0] if len(transfers) == 1
                         else "JOINT_SOURCE_BOUND_TRANSFER:"+content_id(transfers))
        prior_status=("EXACT_WITHIN_SUPPLIED_DISCRETE_PRIOR" if rule.measure_kind == "DISCRETE_EXACT"
                      else "SUPPLIED_CONTINUOUS_PRIOR_QUADRATURE_APPROXIMATION_NOT_CERTIFIED_EVIDENCE")
        # Exact integration over a finite prior cannot upgrade component densities.
        # Unknown/custom approximation descriptions are conservatively retained.
        exact_components={"EXACT_WITHIN_DECLARED_GAUSSIAN_MODEL",
                          "KNOWN_GAUSSIAN_CONDITIONAL_AFFINE_MODEL", "EXACT_WITHIN_SUPPLIED_DISCRETE_PRIOR"}
        component_status=tuple(dict.fromkeys(l.approximation for l in laws))
        approximation=(prior_status if all(a in exact_components for a in component_status)
                       else "COMPONENT_LIMITED_DENSITY:"+"|".join(component_status)+";SHARED_PRIOR:"+prior_status)
        def valid(theta, eta):
            if eta is not None and np.asarray(eta).size:
                raise ValueError("shared latent already integrated; cannot condition/profile it again")
            return all(l.domain_contains(theta, None if isinstance(b,PublishedGaussianSummaryBlock) else node)
                       for l,b in zip(laws,self.blocks) for node in rule.nodes)
        def density_at(y, theta, eta=None):
            if not valid(theta, eta): return -np.inf
            y=finite_array(y, shape=observed.shape)
            terms=[]
            for node, weight in zip(rule.nodes, rule.weights):
                if self.joint_log_density is not None:
                    term=float(self.joint_log_density(y, theta, node))
                else:
                    term=sum(float(b.log_density(y[index], theta, node))
                             for b,index in zip(self.blocks, block_indices))
                if np.isnan(term) or term == np.inf:
                    raise NumericalUnresolved("invalid normalized conditional density")
                terms.append(np.log(weight)+term)
            return float(logsumexp(terms))
        def unavailable_mean(theta, eta):
            raise ValueError("joint marginal mean not supplied; normalized density is available")
        spec={"source_ids":list(dict.fromkeys(s for l in laws for s in l.specification['source_ids']))+[self.source_id, rule.source_id],
              "selection_law":"SOURCE_BOUND_SELECTED_JOINT_FIXED_COUNT", "covariance_source":"DENSITY_NOT_COVARIANCE",
              "mean_definition":"UNAVAILABLE_USE_NORMALIZED_DENSITY",
              "normalized_density_definition":"one proper shared latent integral of normalized selected conditional dY densities",
              "input_law_provenance":input_provenance,
              "input_transfer_sources":transfers, "aggregate_transfer_source":transfer_source,
              "shared_prior_integration_status":prior_status, "aggregate_approximation":approximation,
              "block_laws":[l.specification_id for l in laws], "block_scopes":[l.scope.identity for l in laws],
              "blocks":[(b.provenance() if isinstance(b,PublishedGaussianSummaryBlock)
                          else {k:v for k,v in vars(b).items() if k != "log_density"}) for b in self.blocks],
              "measurement_ids":ids, "object_ids":[o[2] for o in owners],
              "conditional_independence_source":self.conditional_independence_source,
              "joint_normalization_definition":self.joint_normalization_definition,
              "joint_density_kind":self.joint_density_kind,
              "latent_measure_kind":rule.measure_kind, "latent_nodes":rule.nodes, "latent_weights":rule.weights,
              "latent_source":rule.source_id, "integrated_latent_ids":rule.latent_ids,
              "count_conditioning":("MIXED_ORIGINAL_SOURCE_CONDITIONINGS" if any(
                  isinstance(b,PublishedGaussianSummaryBlock) for b in self.blocks) else "FIXED_OBSERVED_COUNT"),
              "count_factor":"NONE",
              "density_measure":"LEBESGUE_DY", "continuous_evidence_status":"NOT_CERTIFIED"}
        scope=replace(first.scope, experiment_id="joint:"+content_id([l.scope.identity for l in laws]),
                      law_id=content_id(spec), dataset_ids=tuple(dict.fromkeys(i for l in laws for i in l.scope.dataset_ids)))
        joint=JointObservationLaw(scope, observed, tuple(ids), first.parameter_names, first.parameter_units,
            unavailable_mean, None, spec, "intersection:"+content_id([l.domain_id for l in laws]), valid,
            shared_latent_ids=(), conditioning_target=(
                "MIXED_SELECTED_AND_PUBLISHED_SUMMARY_SHARED_LATENT_MARGINAL" if any(
                    isinstance(b,PublishedGaussianSummaryBlock) for b in self.blocks)
                else "FIXED_OBSERVED_COUNT_SHARED_LATENT_MARGINAL"),
            approximation=approximation, transfer_source=transfer_source,
            log_density=lambda theta,eta:density_at(observed,theta,eta))
        return joint, tuple(duplicates)


def compose_joint_law(laws,overlap_table,shared_latent_provider) -> ExperimentPartition:
    laws=tuple(laws);bound=tuple(l for l in laws if isinstance(l,JointObservationLaw))
    factories=tuple(l for l in laws if isinstance(l,ObservationLawFactory))
    if len(bound)+len(factories)!=len(laws): raise TypeError("only bound laws and sealed factories can be composed")
    # Exact copies of one law are one experiment, even without an extra provider.
    unique=[];duplicates=[]
    for law in bound:
        match=next((l for l in unique if l.scope.identity==law.scope.identity and l.specification_id==law.specification_id),None)
        if match:
            if (law.measurement_ids != match.measurement_ids or not np.array_equal(law.observed,match.observed)
                    or law.execution_identity != match.execution_identity
                    or law.shared_latent_ids != match.shared_latent_ids
                    or law.conditioning_target != match.conditioning_target
                    or law.transfer_source != match.transfer_source
                    or law.approximation != match.approximation):
                raise ValueError("same law identity has conflicting observations/order/prediction/conditioning")
            duplicates.extend(law.measurement_ids)
        else:unique.append(law)
    bound=tuple(unique)
    if len(bound)<2 and not isinstance(shared_latent_provider,SelectedJointDensityProvider):
        return ExperimentPartition(bound,bound,factories,(),tuple(duplicates))
    # Object matching is evidence-backed identity, never angular proximity.
    for row in overlap_table:
        if row.get("basis") in {"POSITION_ONLY","ANGULAR_NEAREST"} or not row.get("evidence"):
            raise ValueError("cross-probe overlap requires object/product evidence")
    if shared_latent_provider is not None:
        if not isinstance(shared_latent_provider,(JointGaussianProvider,SelectedJointDensityProvider)): raise TypeError("supported joint sampling-law provider required")
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
