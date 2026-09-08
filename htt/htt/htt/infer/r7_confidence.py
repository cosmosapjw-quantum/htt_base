"""Neyman inversion of a fixed sampling law, including exact support.

For each true parameter in the maintained domain the standardized residual has
rank(C) independent standard normal coordinates and zero null coordinates.
Its squared length is chi-square(rank(C)); at rank zero it is identically zero.
The event that this test accepts the true parameter implies membership of every
image of this region. Fitting parameters does not change these degrees of
freedom. Numerical refusal is not statistical rejection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import math
import numpy as np

from common.r7_contracts import AcceptanceResult, NumericalUnresolved, finite_array
from .r7_gaussian_law import JointObservationLaw, gaussian_acceptance,require_fixed_known_gaussian


@dataclass(frozen=True)
class PhysicalDomain:
    domain_id: str
    parameter_names: tuple[str, ...]
    contains: Callable
    bounds: tuple[tuple[float, float], ...] | None = None
    witnesses: tuple = ()
    assumptions: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.domain_id or not self.parameter_names: raise ValueError("named domain and parameters required")
        if self.bounds is not None:
            if len(self.bounds) != len(self.parameter_names): raise ValueError("domain bounds dimension")
            if any(math.isnan(a) or math.isnan(b) or a > b for a,b in self.bounds):
                raise ValueError("invalid domain bounds")

    def includes(self,theta,eta=None):
        x=finite_array(theta,shape=(len(self.parameter_names),),name="theta")
        if self.bounds is not None and any(v<a or v>b for v,(a,b) in zip(x,self.bounds)):
            return False
        return bool(self.contains(x,eta))


@dataclass(frozen=True)
class GaussianAcceptanceRule:
    alpha: float = .05
    support_tol: float = 0.
    nuisance_gamma: float = 0.

    def __post_init__(self):
        if not 0 < self.alpha < 1 or not 0 <= self.nuisance_gamma < 1-self.alpha:
            raise ValueError("invalid simultaneous coverage allocation")
        if not math.isfinite(self.support_tol) or self.support_tol < 0: raise ValueError("support tolerance")

    def __call__(self,residual,covariance):
        return gaussian_acceptance(residual,covariance,self.alpha,self.support_tol)


@dataclass(frozen=True)
class PhysicalRegion:
    law: JointObservationLaw | None
    domain: PhysicalDomain
    acceptance_rule: GaussianAcceptanceRule | None
    membership: Callable
    coverage_lower: float
    construction: str
    scope_ids: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    components: tuple = ()
    numeric_status: str = "SET_DEFINED_NO_OUTER_OPTIMIZATION"

    def evaluate(self,theta,eta=None):
        try:
            if not self.domain.includes(theta,eta):
                return AcceptanceResult(False,None,None,None,False,"OUTSIDE_PHYSICAL_DOMAIN")
            return self.membership(theta,eta)
        except NumericalUnresolved:
            return AcceptanceResult(False,None,None,None,False,"NUMERICALLY_UNRESOLVED")

    def contains(self,theta,eta=None):
        result=self.evaluate(theta,eta)
        if result.numeric_status == "NUMERICALLY_UNRESOLVED":
            raise NumericalUnresolved("region membership numerically unresolved")
        return result.accepted


def invert_acceptance(law, physical_domain, acceptance_rule) -> PhysicalRegion:
    require_fixed_known_gaussian(law)
    if not isinstance(law,JointObservationLaw): raise TypeError("a bound observation law is required")
    if law.log_density is not None: raise TypeError("non-Gaussian law needs a separately calibrated acceptance adapter")
    if not isinstance(physical_domain,PhysicalDomain): raise TypeError("typed physical domain required")
    if physical_domain.parameter_names != law.parameter_names: raise ValueError("ordered parameter mismatch")
    if not isinstance(acceptance_rule,GaussianAcceptanceRule): raise TypeError("unsupported nonlinear acceptance adapter")
    if acceptance_rule.support_tol != law.support_tol: raise ValueError("support tolerance must be bound by the law")
    law.specification_id

    def membership(theta,eta):
        law.specification_id
        if not law.domain_contains(theta,eta):
            return AcceptanceResult(False,None,None,None,False,"OUTSIDE_LAW_DOMAIN")
        return acceptance_rule(law.observed-law.mean(theta,eta),law.covariance_at(theta,eta))

    return PhysicalRegion(law,physical_domain,acceptance_rule,membership,
        1-acceptance_rule.alpha-acceptance_rule.nuisance_gamma,
        "FIXED_GAUSSIAN_ACCEPTANCE_INVERSE_IMAGE",(law.scope.identity,),
        physical_domain.assumptions+(law.approximation,law.conditioning_target))


def combine_regions(regions, domain, *, mode, fixed_alphas=None):
    """Unknown dependence intersects marginal regions; alternative laws union.

    A missing fixed marginal is the full maintained domain, retaining its alpha
    allocation. An unresolved membership is never coerced to exclusion.
    """
    regions=tuple(regions)
    if mode not in {"MARGINAL_UNION_BOUND","ALTERNATIVE_MODEL_UNION"}: raise ValueError("unknown set construction")
    if not regions: raise ValueError("a fixed list of scopes is required")
    if any(r is not None and r.domain.parameter_names!=domain.parameter_names for r in regions):
        raise ValueError("regions do not share an estimand")
    if mode=="MARGINAL_UNION_BOUND":
        if fixed_alphas is None or len(fixed_alphas)!=len(regions): raise ValueError("fixed allocation required")
        if any(not 0<a<1 for a in fixed_alphas) or sum(fixed_alphas)>=1: raise ValueError("invalid allocation")
        for r,a in zip(regions,fixed_alphas):
            if r is not None and r.coverage_lower < 1-a-1e-14: raise ValueError("marginal coverage below allocation")
        coverage=1-sum(fixed_alphas)
    else:
        if any(r is None for r in regions): coverage=1.
        else: coverage=min(r.coverage_lower for r in regions)

    def membership(theta,eta):
        values=[r.evaluate(theta,eta) if r else AcceptanceResult(True,0.,0,0.,True,"FULL_DOMAIN") for r in regions]
        unknown=any(v.numeric_status=="NUMERICALLY_UNRESOLVED" for v in values)
        if mode=="MARGINAL_UNION_BOUND":
            decided=any(not v.accepted and v.numeric_status!="NUMERICALLY_UNRESOLVED" for v in values)
            accepted=not decided and not unknown
        else:
            decided=any(v.accepted for v in values)
            accepted=decided
        status="NUMERICALLY_UNRESOLVED" if unknown and not decided else "RESOLVED"
        return AcceptanceResult(True,None,None,None,accepted,status)

    return PhysicalRegion(None,domain,None,membership,coverage,mode,
        tuple(s for r in regions if r for s in r.scope_ids),components=regions)


@dataclass(frozen=True)
class ProjectionResult:
    functional_id: str
    outer_bounds: tuple[float,float] | None
    inner_values: tuple[float,...]
    inner_witnesses: tuple
    status: str
    numerical_error: float | None
    bound_provenance: str | None
    undefined_witnesses: tuple = ()
    assumptions: tuple[str,...] = ()


@dataclass(frozen=True)
class BoundCertificate:
    """Output of an actual interval/analytic bound provider, never an optimizer."""
    bounds: tuple[float,float] | None
    status: str
    error: float | None
    procedure: str
    scope_ids: tuple[str,...]
    functional_id: str
    domain_id: str
    assumptions: tuple[str,...] = ()


def project_joint_region(region, functional, certified_bound_provider) -> ProjectionResult:
    if not getattr(functional,"functional_id",None): raise ValueError("registered functional identity required")
    witnesses=[];values=[];undefined=[]
    for theta in region.domain.witnesses:
        try:
            if not region.contains(theta): continue
            v=float(functional(theta))
            if not math.isfinite(v): undefined.append(theta)
            else: witnesses.append(theta);values.append(v)
        except NumericalUnresolved:
            continue
        except ZeroDivisionError:
            undefined.append(theta)
    certificate=certified_bound_provider(region,functional) if certified_bound_provider else None
    if certificate is None:
        return ProjectionResult(functional.functional_id,None,tuple(values),tuple(witnesses),
            "OUTER_RANGE_UNRESOLVED",None,None,tuple(undefined))
    if not isinstance(certificate,BoundCertificate): raise TypeError("bound provider must return a certificate")
    if (certificate.scope_ids!=region.scope_ids or certificate.functional_id!=functional.functional_id
            or certificate.domain_id!=region.domain.domain_id): raise ValueError("bound certificate scope mismatch")
    if certificate.bounds is not None:
        a,b=certificate.bounds
        if math.isnan(a) or math.isnan(b) or a>b: raise ValueError("invalid outer bounds")
        if certificate.error is None or certificate.error<0 or not math.isfinite(certificate.error): raise ValueError("bound numerical error required")
        if any(v<a-certificate.error or v>b+certificate.error for v in values): raise ValueError("outer bound excludes feasible witness")
    return ProjectionResult(functional.functional_id,certificate.bounds,tuple(values),tuple(witnesses),
        certificate.status,certificate.error,certificate.procedure,tuple(undefined),certificate.assumptions)
