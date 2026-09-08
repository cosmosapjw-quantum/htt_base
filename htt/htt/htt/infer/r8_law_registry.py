"""Product-keyed execution of live, source-bound fixed Gaussian experiments.

No product-name or node-ID dispatch. An unfilled factory and missing law remain
refusals. Registration preserves a law's conditional/approximate status; it
cannot establish its scientific premises from a sidecar label.
"""
from dataclasses import dataclass, field
from fractions import Fraction
import numpy as np
from scipy.stats import chi2
from common.r8_contracts import RegionMembership as R, exact_alpha
from common.r7_contracts import content_id
from .r7_gaussian_law import JointObservationLaw, require_fixed_known_gaussian
from .r8_partial_law import chi_critical_bounds, QuantileUnresolved
from .r8_support import factor_support, exact_matrix, contains_residual, reduced_quadratic

@dataclass(frozen=True)
class ScopedRefusal:
    product_id: str
    reasons: tuple
    status: str='INPUT_UNAVAILABLE'

@dataclass(frozen=True)
class AdmittedLaw:
    product_id: str
    law: JointObservationLaw
    support: object
    frame: str
    identity: str
    scope: dict
    _binding_token: object=field(default_factory=object,init=False,repr=False)

    @property
    def current_identity(self):
        return content_id({'law':_identity(self.law),'scope':self.scope,'frame':self.frame,
            'B':str(self.support.B),'V':str(self.support.V),'support_semantics':self.support.semantics})

@dataclass(frozen=True)
class BoundMethod:
    live_binding: object
    law_identity: str
    alpha: Fraction
    config_id: str
    method_id: str='R8_FIXED_STRUCTURAL_GAUSSIAN_ACCEPTANCE_V1'

@dataclass(frozen=True)
class ScopeResult:
    scope: dict
    membership: R
    quadratic: float | None
    threshold: float | None
    rank: int
    outcome: str
    numerical_status: str


def _identity(law):
    return content_id({'specification':law.specification_id,'execution':law.execution_identity,
                       'scope':law.scope,'domain':law.domain_id,'conditioning':law.conditioning_target,
                       'approximation':law.approximation})


def admit_product(product,sidecar):
    pid=str(product['product_id']); law=sidecar.get('law')
    if isinstance(law,PartialObservationLaw):return _admit_partial(product,sidecar)
    def refuse(reason):return ScopedRefusal(pid,(reason,))
    if not isinstance(law,JointObservationLaw):return refuse('No bound live observation law; factories have no empirical eligibility')
    require_fixed_known_gaussian(law)
    if (tuple(product.get('measurement_ids',()))!=tuple(law.measurement_ids)
        or tuple(product.get('source_ids',()))!=tuple(law.specification['source_ids'])
        or not np.array_equal(product.get('observed'),law.observed)):
        return refuse('Product order/source/value differs from the law sampling variable')
    if not sidecar.get('frame') or sidecar.get('conditioning_id')!=law.conditioning_target:
        return refuse('Missing frame or different conditioning target')
    C=exact_matrix(law.covariance)
    if 'support' in sidecar:
        support=sidecar['support']
        if support.B*support.V*support.B.T!=C:return refuse('Structural covariance does not equal the live covariance')
    else:
        # Full rank is certified using exact dyadic principal minors. Singular
        # covariance requires its actual structural factor, not an eigentolerance.
        try:support=factor_support(np.eye(len(law.observed),dtype=int),law.covariance,
            {'source':law.specification['covariance_source'],'semantics':'EXACT_STRUCTURAL'})
        except ValueError:return refuse('Singular/uncertain covariance requires a structural factor and rounding semantics')
    scope={'product_id':pid,'experiment_id':law.scope.experiment_id,'law_id':law.scope.law_id,
           'model_id':law.scope.model_id,'dataset_ids':law.scope.dataset_ids,'convention_id':law.scope.conventions,
           'domain_id':law.domain_id,'conditioning_id':law.conditioning_target,
           'ordered_measurement_ids':law.measurement_ids,'parameter_names':law.parameter_names,
           'parameter_units':law.parameter_units,'frame':sidecar['frame'],'approximation':law.approximation}
    return AdmittedLaw(pid,law,support,sidecar['frame'],_identity(law),scope)


def bind_method(live_law,alpha):
    exact_alpha(alpha)
    if isinstance(live_law,AdmittedPartialLaw):
        config=content_id({'alpha':[alpha.numerator,alpha.denominator],'allocation':'FIXED_EQUAL_PER_ORIGINAL_ROW',
            'domain':live_law.law.domain_id,'premise':live_law.law.premise})
        return BoundMethod(live_law._binding_token,live_law.current_identity,alpha,config,'R8_PARTIAL_ACCEPTANCE_V1')
    if not isinstance(live_law,AdmittedLaw):raise TypeError('method needs an admitted live law')
    if _identity(live_law.law)!=live_law.identity:raise ValueError('live law changed')
    config=content_id({'alpha':[alpha.numerator,alpha.denominator],'support':'EXACT_FACTOR',
                       'domain':live_law.law.domain_id,'conditioning':live_law.law.conditioning_target})
    return BoundMethod(live_law._binding_token,live_law.current_identity,alpha,config)


def run_scope(live_law,method,x_or_domain):
    """One candidate-state acceptance; a grid of these is not a continuum image."""
    if isinstance(live_law,AdmittedPartialLaw) and isinstance(method,BoundMethod):return _run_partial(live_law,method,x_or_domain)
    if not isinstance(live_law,AdmittedLaw) or not isinstance(method,BoundMethod):raise TypeError('bound law and method required')
    law=live_law.law
    if method.live_binding is not live_law._binding_token or method.law_identity!=live_law.current_identity:
        raise ValueError('calibration/acceptance proof belongs to another or mutated live law')
    scope={**live_law.scope,'method_id':method.method_id,'method_config_id':method.config_id,
           'alpha':[method.alpha.numerator,method.alpha.denominator]}
    rank=live_law.support.rank
    def result(member,q=None,threshold=None,status='RESOLVED'):
        return ScopeResult(scope,member,q,threshold,rank,'CONDITIONAL_ON_DECLARED_LAW',status)
    x=np.asarray(x_or_domain,dtype=float)
    if not np.isfinite(x).all():raise ValueError('nonfinite candidate')
    if not law.domain_contains(x,None):return result(R.REJECT,status='OUTSIDE_PHYSICAL_DOMAIN')
    # Subtract exact dyadic coordinates, rather than introducing a spurious
    # off-support component through a rounded floating subtraction.
    y=exact_matrix(np.asarray(law.observed,object).reshape(-1,1))
    mu=exact_matrix(np.asarray(law.mean(x,None),object).reshape(-1,1))
    if y.shape!=mu.shape:raise ValueError('mean changed observation dimensions')
    residual=list(y-mu)
    support=contains_residual(live_law.support,residual)
    if support==R.REJECT:return result(R.REJECT,status='OFF_EXACT_SUPPORT')
    if support==R.UNRESOLVED:return result(R.UNRESOLVED,status='UNRESOLVED_SUPPORT')
    q_exact=reduced_quadratic(live_law.support,residual)
    q=float(q_exact)
    threshold=float(chi2.ppf(1-float(method.alpha),rank)) if rank else 0.
    try:lo,hi=chi_critical_bounds(method.alpha,rank)
    except QuantileUnresolved:return result(R.UNRESOLVED,q,threshold,'UNRESOLVED_QUANTILE_BOUNDARY')
    member=R.ACCEPT if q_exact<=lo else R.REJECT if q_exact>hi else R.UNRESOLVED
    return result(member,q,threshold,'CERTIFIED_QUANTILE_BRACKET' if member!=R.UNRESOLVED else 'UNRESOLVED_QUANTILE_BOUNDARY')

@dataclass(frozen=True)
class PartialObservationLaw:
    """Actual marginal or moment premises for the original sampling vector.

    Variances are marginal variances or proved upper bounds. This type has no
    joint covariance, density or posterior interface.
    """
    observed: object
    measurement_ids: tuple
    source_ids: tuple
    variances: object
    mean: object
    domain_contains: object
    domain_id: str
    conditioning_id: str
    frame: str
    units: tuple
    premise: str
    law_source: str
    parameter_names: tuple
    _binding_token: object=field(default_factory=object,init=False,repr=False)
    def __post_init__(self):
        from common.r7_contracts import finite_array
        y=finite_array(self.observed,ndim=1);v=finite_array(self.variances,shape=y.shape)
        if (self.premise not in {'KNOWN_GAUSSIAN_MARGINALS','KNOWN_VARIANCE_UPPER_BOUNDS'}
            or not callable(self.mean) or not callable(self.domain_contains)
            or not all((self.law_source,self.domain_id,self.conditioning_id,self.frame,self.source_ids,self.parameter_names))
            or len(y)!=len(self.measurement_ids) or len(set(self.measurement_ids))!=len(y)
            or len(self.units)!=len(y) or np.any(v<0)):
            raise ValueError('actual ordered sampling variable and independent partial-law premises required')
        if self.premise=='KNOWN_GAUSSIAN_MARGINALS' and np.any(v<=0):raise ValueError('use exact moment equality for zero-variance coordinates')
        object.__setattr__(self,'observed',y);object.__setattr__(self,'variances',v)
        object.__setattr__(self,'_seal',self.execution_identity)
    @property
    def execution_identity(self):
        from .r7_gaussian_law import _execution_state
        return content_id(_execution_state((self.observed,self.variances,self.mean,self.domain_contains,
            self.measurement_ids,self.source_ids,self.domain_id,self.conditioning_id,self.frame,self.units,
            self.premise,self.law_source,self.parameter_names)))
    @property
    def specification_id(self):
        if self.execution_identity!=self._seal:raise ValueError('partial sampling law mutated')
        return self._seal

@dataclass(frozen=True)
class AdmittedPartialLaw:
    product_id: str
    law: PartialObservationLaw
    identity: str
    scope: dict
    _binding_token: object=field(default_factory=object,init=False,repr=False)
    @property
    def current_identity(self):return content_id((self.law.specification_id,self.scope))


def _admit_partial(product,sidecar):
    law=sidecar['law'];pid=str(product['product_id'])
    if (tuple(product.get('measurement_ids',()))!=law.measurement_ids or tuple(product.get('source_ids',()))!=law.source_ids
        or not np.array_equal(product.get('observed'),law.observed) or sidecar.get('frame')!=law.frame
        or sidecar.get('conditioning_id')!=law.conditioning_id):
        return ScopedRefusal(pid,('Partial law does not match the original product variable/order/frame/conditioning',))
    scope={'product_id':pid,'experiment_id':pid,'law_id':law.specification_id,'model_id':law.premise,
        'dataset_ids':law.source_ids,'ordered_measurement_ids':law.measurement_ids,'units':law.units,
        'parameter_names':law.parameter_names,'convention_id':law.frame,'domain_id':law.domain_id,
        'conditioning_id':law.conditioning_id,'law_source':law.law_source}
    return AdmittedPartialLaw(pid,law,law.specification_id,scope)


def _run_partial(live_law,method,x):
    from .r8_partial_law import gaussian_marginal,marginal_acceptance,moment_acceptance
    law=live_law.law
    if method.live_binding is not live_law._binding_token or method.law_identity!=live_law.current_identity:
        raise ValueError('partial method belongs to another or mutated live law')
    x=np.asarray(x,dtype=float)
    if not np.isfinite(x).all():raise ValueError('nonfinite candidate')
    if not law.domain_contains(x):member=R.REJECT
    else:
        mu=np.asarray(law.mean(x),dtype=float)
        if mu.shape!=law.observed.shape or not np.isfinite(mu).all():raise ValueError('partial mean outside ordered finite contract')
        if law.premise=='KNOWN_VARIANCE_UPPER_BOUNDS':member=moment_acceptance(law.observed,mu,law.variances,method.alpha)
        else:
            blocks={name:gaussian_marginal(y,lambda ignored,mu=m:mu,v,law.law_source)
                    for name,y,m,v in zip(law.measurement_ids,law.observed,mu,law.variances)}
            allocation={name:method.alpha/len(blocks) for name in blocks}
            member=marginal_acceptance(blocks,x,allocation)
    scope={**live_law.scope,'method_id':method.method_id,'method_config_id':method.config_id,
           'alpha':[method.alpha.numerator,method.alpha.denominator]}
    return ScopeResult(scope,member,None,None,0,'CONDITIONAL_ON_DECLARED_PARTIAL_LAW',
        'PARTIAL_LAW_NO_JOINT_RANK_OR_COVARIANCE')
