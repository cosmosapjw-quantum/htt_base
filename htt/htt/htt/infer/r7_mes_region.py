"""Same-state MES and registered GF images of accepted observation laws."""
from __future__ import annotations
from dataclasses import dataclass, replace
from fractions import Fraction
import numpy as np
from common.r7_contracts import NumericalUnresolved
from common.r7_radiation_jet import kinematics_from_radiation_jet
from .r7_confidence import (PhysicalDomain, GaussianAcceptanceRule, PhysicalRegion,
    BoundCertificate, ProjectionResult, invert_acceptance, project_joint_region)


@dataclass(frozen=True)
class JetDomain:
    domain_id: str
    jet_at: object
    contains: object
    assumptions: tuple[str,...]


def build_mes_region(experiment,jet_domain,model_domain,alpha_budget) -> PhysicalRegion:
    gamma=float(alpha_budget.get("gamma",0.));alpha=float(alpha_budget.get("observational_alpha",.05))
    if abs(alpha+gamma-.05)>1e-14: raise ValueError("R7 confidence budget must total .05")
    if gamma and (gamma!=.01 or alpha!=.04): raise ValueError("separate nuisance coverage requires gamma=.01 and alpha=.04")
    if gamma and not alpha_budget.get("nuisance_coverage_evidence"):
        raise ValueError("a nuisance confidence region requires its coverage evidence")
    if jet_domain is None:
        base=invert_acceptance(experiment,model_domain,GaussianAcceptanceRule(alpha,experiment.support_tol,gamma))
        return replace(base,numeric_status="MISSING_RADIATION_JET",
            assumptions=base.assumptions+("observable inverse image only; physical MES projection unavailable",))
    if not isinstance(jet_domain,JetDomain): raise TypeError("typed joint derivative domain required")
    def contains(theta,eta):
        if not model_domain.includes(theta,eta) or not jet_domain.contains(theta,eta): return False
        jet=jet_domain.jet_at(theta,eta)
        if jet.domain_id!=jet_domain.domain_id: raise ValueError("jet domain binding mismatch")
        state=kinematics_from_radiation_jet(jet)
        if state.status in {"MISSING_RADIATION_JET","UNSUPPORTED_PHYSICAL_PREMISES"}:
            raise NumericalUnresolved(state.status)
        return True
    domain=PhysicalDomain(model_domain.domain_id,model_domain.parameter_names,contains,
        model_domain.bounds,model_domain.witnesses,model_domain.assumptions+jet_domain.assumptions)
    return invert_acceptance(experiment,domain,GaussianAcceptanceRule(alpha,experiment.support_tol,gamma))


@dataclass(frozen=True)
class AffineRatioFunctional:
    functional_id: str
    numerator_constant: Fraction
    denominator_constant: Fraction
    numerator_coefficients: tuple[Fraction,...]
    denominator_coefficients: tuple[Fraction,...]

    def __call__(self,theta):
        if len(theta)!=len(self.numerator_coefficients) or len(theta)!=len(self.denominator_coefficients):
            raise ValueError("functional parameter order dimension")
        n=float(self.numerator_constant)+np.dot(np.array(self.numerator_coefficients,dtype=float),theta)
        d=float(self.denominator_constant)+np.dot(np.array(self.denominator_coefficients,dtype=float),theta)
        if d<=0: raise ZeroDivisionError("registered GF denominator is not positive")
        return n/d


def affine_box_gf_bound(region,functional):
    """Exact v8 signed affine quotient over a box OUTER relaxation of region.

    The accepted states may fill a strict subset of this box. These extrema are
    valid outer limits, with feasible inner witnesses reported independently.
    """
    from obsstat.egs3_gf_interval_v8 import exact_joint_interval_v8
    if not isinstance(functional,AffineRatioFunctional) or region.domain.bounds is None:
        return None
    try: bounds=tuple((Fraction(a),Fraction(b)) for a,b in region.domain.bounds)
    except (ValueError,OverflowError): return None
    n=Fraction(functional.numerator_constant);d=Fraction(functional.denominator_constant)
    values=exact_joint_interval_v8((n,n),(d,d),bounds,
        tuple(map(Fraction,functional.numerator_coefficients)),tuple(map(Fraction,functional.denominator_coefficients)))
    if values is None:
        return BoundCertificate(None,"DENOMINATOR_UNRESOLVED",None,"v8 exact rational box denominator check",
            region.scope_ids,functional.functional_id,region.domain.domain_id)
    lower=np.nextafter(float(values[0]),-np.inf);upper=np.nextafter(float(values[1]),np.inf)
    return BoundCertificate((lower,upper),"CERTIFIED_OUTER_BOUND",0.,"v8 exact Fraction shared-box vertices and outward float conversion",
        region.scope_ids,functional.functional_id,region.domain.domain_id,("box relaxation may include unaccepted states",))
