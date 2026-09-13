"""Physical confidence images require one calibrated state-jet-anchor event.

Deterministic R8 jet images remain deterministic. Metadata describing a jet
covariance or matching frames cannot construct a joint confidence event.
"""
from dataclasses import dataclass
from fractions import Fraction
from common.r7_contracts import UnavailableLaw
from common.r9_product import SharedStateEmbedding
from .r7_confidence import PhysicalRegion, project_joint_region
from .r8_confidence_image import FIXED_INTEGRATED_ALLOCATION


@dataclass(frozen=True)
class StateFunctional:
    functional_id: str
    evaluator: object
    variable_names: tuple[str, ...]
    fixed_parameters: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.functional_id or not callable(self.evaluator) or not self.variable_names:
            raise ValueError('named functional, evaluator and complete dependencies required')
        object.__setattr__(self, 'variable_names', tuple(self.variable_names))
        object.__setattr__(self, 'fixed_parameters', tuple(self.fixed_parameters))

    def __call__(self, x):
        return self.evaluator(x)


@dataclass(frozen=True)
class JointCoverageEvent:
    region: PhysicalRegion
    embedding: SharedStateEmbedding
    region_identity: str
    covered_variables: tuple[str, ...]
    coverage_target: str
    coverage_procedure: str
    evidence_ref: str
    prospective_error_allocation: tuple[tuple[str, Fraction], ...]

    def __post_init__(self):
        if not isinstance(self.region, PhysicalRegion) or not isinstance(self.embedding, SharedStateEmbedding):
            raise TypeError("actual confidence region and common state embedding required")
        object.__setattr__(self, 'covered_variables', tuple(self.covered_variables))
        if (not self.region_identity or not self.coverage_procedure or not self.evidence_ref
                or self.covered_variables != self.embedding.state_names
                or self.region.domain.parameter_names != self.embedding.state_names):
            raise ValueError("one region, ordered state variables and actual coverage procedure required")
        allocations = tuple(self.prospective_error_allocation)
        names = [name for name, _ in allocations]
        if not allocations or len(names) != len(set(names)):
            raise ValueError("unique prospective product allocations required")
        for name, alpha in allocations:
            if (name not in FIXED_INTEGRATED_ALLOCATION or not isinstance(alpha, Fraction)
                    or not 0 < alpha <= FIXED_INTEGRATED_ALLOCATION[name]):
                raise ValueError("no post-hoc alpha redistribution or family expansion")
        if self.region.coverage_lower < float(1-sum(a for _, a in allocations)) - 1e-14:
            raise ValueError("region coverage does not meet its allocated error")
        if self.coverage_target not in {'TRUE_POINT', 'FULL_IDENTIFIED_SET'}:
            raise ValueError("explicit coverage target required")
        object.__setattr__(self, 'prospective_error_allocation', allocations)


def physical_confidence_image(region, functional, *, event=None, bound_provider=None):
    """Project the same region only; append no separately measured jet/anchor.

    Required variables include every physical/jet/uncertain-anchor dependency.
    A fixed-q formula is forbidden when q is a coordinate of the common region.
    Full identified-set coverage needs its own validated lifting construction;
    the point-coverage machinery here does not implement that construction.
    """
    def unavailable(reason):
        return UnavailableLaw('R9_PHYSICAL_IMAGE', 'INPUT_UNAVAILABLE', (reason,))
    if event is None:
        return unavailable('common state-jet-anchor coverage unavailable')
    if not isinstance(event, JointCoverageEvent) or event.region is not region:
        raise ValueError('coverage must bind this actual common region')
    if not isinstance(functional, StateFunctional):
        raise TypeError('functional with explicit state/jet/anchor dependencies required')
    if event.coverage_target != 'TRUE_POINT':
        return unavailable('full identified-set coverage construction not implemented')
    variables = set(functional.variable_names)
    covered = set(event.covered_variables)
    roles = dict(zip(event.embedding.state_names, event.embedding.state_roles))
    if not variables or not variables <= covered:
        return unavailable('functional dependencies absent from calibrated common event')
    if not any(roles[v] == 'JET' for v in variables):
        return unavailable('physical response requires covered radiation jet variables')
    if set(functional.fixed_parameters) & covered:
        return unavailable('uncertain q/anchor cannot be frozen in a plug-in fibre formula')
    result = project_joint_region(region, functional, bound_provider)
    return {'projection': result, 'region_identity': event.region_identity,
            'covered_variables': event.covered_variables, 'coverage_target': event.coverage_target,
            'coverage_lower': region.coverage_lower if result.outer_bounds is not None
                              and not result.undefined_witnesses else None,
            'event_coverage_lower': region.coverage_lower,
            'coverage_procedure': event.coverage_procedure, 'evidence_ref': event.evidence_ref,
            'scope': 'common-event outer image; not posterior, identification or a new test'}
