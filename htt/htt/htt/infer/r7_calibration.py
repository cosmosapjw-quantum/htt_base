"""Method-specific exact proofs, finite operational stress, and observed joins."""
from __future__ import annotations
from dataclasses import dataclass,replace
from pathlib import Path
import hashlib
import math
import numpy as np
from scipy.stats import beta as beta_distribution,chi2
from common.r7_contracts import ScopeKey,BranchResult,content_id,finite_array,json_value
from .r7_gaussian_law import JointObservationLaw,decompose_covariance,gaussian_acceptance,require_fixed_known_gaussian


@dataclass(frozen=True)
class GaussianMethod:
    configuration: dict
    method_id: str = "R7_FIXED_GAUSSIAN_ACCEPTANCE"

    def __post_init__(self):
        required={"statistic","alpha","nuisance_policy","fitting_procedure","selection_procedure","null_parameter","hypothesis_id"}
        if not required<=self.configuration.keys():raise ValueError("full method configuration required")
        if self.configuration["statistic"]!="FULL_RESIDUAL_CHISQUARE_WITH_SUPPORT":raise ValueError("unsupported Gaussian statistic")
        if self.configuration["alpha"] not in {.05,.04}:raise ValueError("registered observational alpha is .05 or .04")
        object.__setattr__(self,"_seal",content_id(self.configuration))

    @property
    def config_id(self):
        if content_id(self.configuration)!=self._seal:raise ValueError("method configuration mutated")
        return self._seal

    @property
    def implementation_id(self):
        files=[Path(__file__),Path(__file__).with_name('r7_gaussian_law.py')]
        return content_id({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def scope_for(self,experiment):
        return replace(experiment.scope,method_id=self.method_id,method_config_id=self.config_id)

    def evaluate(self,experiment):
        theta=self.configuration['null_parameter'];eta=self.configuration.get('null_nuisance')
        if not experiment.domain_contains(theta,eta):raise ValueError("hypothesis outside supported law domain")
        return gaussian_acceptance(experiment.observed-experiment.mean(theta,eta),experiment.covariance_at(theta,eta),
            self.configuration['alpha'],experiment.support_tol)


@dataclass(frozen=True)
class CalibrationRecord:
    scope: ScopeKey
    law_specification_id: str
    method_implementation_id: str
    mechanism: str
    validity: str
    conditioning_target: str
    supported_domain_id: str
    supported_domain: object
    numerical_obligations: dict
    evidence: tuple[str,...]
    stress_results: tuple = ()
    live_law_binding: object = None


def clopper_pearson(successes,trials,confidence=.99):
    if type(successes) is not int or type(trials) is not int or not 0<=successes<=trials or trials<=0:raise ValueError("integer binomial count required")
    if not 0<confidence<1:raise ValueError("confidence in (0,1)")
    alpha=1-confidence
    return (0. if successes==0 else float(beta_distribution.ppf(alpha/2,successes,trials-successes+1)),
            1. if successes==trials else float(beta_distribution.ppf(1-alpha/2,successes+1,trials-successes)))


def gaussian_operational_stress(cells,*,seed=720260908,trials=10000):
    """Independent draws per preregistered cell; no transfer to product nulls.

    Confidence coverage tests the actual mean. Rejection/power tests the fixed
    zero-mean null, so mirror alternatives remain distinct named cells. Exact
    rank-zero laws overcover; their coverage is 1, not a failed 0.95 target.
    """
    if trials!=10000:raise ValueError("R7 operational stress fixes 10000 independent trials per cell")
    cells=tuple(cells)
    if len({c['cell_id'] for c in cells})!=len(cells):raise ValueError("unique declared cell IDs")
    children=np.random.SeedSequence(seed).spawn(len(cells));results=[]
    for cell,child in zip(cells,children):
        c=decompose_covariance(cell['covariance'])
        if not c.resolved:raise ValueError("stress law support unresolved")
        mean=finite_array(cell['mean'],shape=(len(c.covariance),))
        rng=np.random.default_rng(child);z=rng.normal(size=(trials,c.rank))
        root=c.eigenvectors[:,c.positive]*np.sqrt(c.eigenvalues[c.positive])
        draws=z@root.T+mean
        threshold=float(chi2.ppf(.95,c.rank)) if c.rank else 0.
        # Exercise the public acceptance implementation on every trial; the
        # latent chi-square identity alone would only test the simulator math.
        coverage_results=[gaussian_acceptance(draw-mean,c.covariance,.05,0.) for draw in draws]
        cover=np.array([r.accepted for r in coverage_results])
        null_support=not c.null.size or np.linalg.norm(c.null.T@mean)==0.
        coordinates=(draws@c.eigenvectors[:,c.positive])/np.sqrt(c.eigenvalues[c.positive])
        null_results=[gaussian_acceptance(draw,c.covariance,.05,0.) for draw in draws]
        refusals=np.array([a.numeric_status=='NUMERICALLY_UNRESOLVED' or b.numeric_status=='NUMERICALLY_UNRESOLVED'
            for a,b in zip(coverage_results,null_results)])
        reject=np.array([not r.accepted and r.numeric_status!='NUMERICALLY_UNRESOLVED' for r in null_results])
        coverage_count=int(cover.sum());rejection_count=int(reject.sum())
        cover_interval=clopper_pearson(coverage_count,trials);reject_interval=clopper_pearson(rejection_count,trials)
        is_null=bool(np.all(mean==0))
        passed=not refusals.any() and cover_interval[0]>=.94 and (not is_null or reject_interval[1]<=.06)
        results.append({'cell_id':cell['cell_id'],'law_id':cell['law_id'],'configuration_id':content_id(cell),
            'trials':trials,'independent_draws':True,'seed_entropy':child.entropy,'seed_spawn_key':child.spawn_key,
            'coverage':coverage_count/trials,'coverage_count':coverage_count,'coverage_CP99':cover_interval,
            'FPR' if is_null else 'power':rejection_count/trials,'rejection_count':rejection_count,'rejection_CP99':reject_interval,
            'refusal_rate':float(refusals.mean()),'rank':c.rank,'status':'PASS' if passed else 'FAILED_OPERATIONAL_CELL',
            'scope':'declared synthetic known Gaussian law only'})
    return tuple(results)


def registered_gaussian_cells():
    cells=[]
    for amplitude in (0.,.5,1.,2.):
        for sign,label in ((1.,'ordinary'),(-1.,'mirror')):
            cells.append({'cell_id':f'gaussian12_{label}_{amplitude}','law_id':'ISOTROPIC_ORTHONORMAL_12_GAUSSIAN',
                'mean':[sign*amplitude]+[0.]*11,'covariance':np.eye(12).tolist(),'amplitude':amplitude,'orientation':label})
    cells.extend(({'cell_id':'singular_rank1','law_id':'EXACT_SINGULAR_GAUSSIAN','mean':[0.,0.],'covariance':[[1.,0.],[0.,0.]]},
                  {'cell_id':'singular_off_null_support','law_id':'EXACT_SINGULAR_GAUSSIAN','mean':[0.,1.],'covariance':[[1.,0.],[0.,0.]]},
                  {'cell_id':'rank0','law_id':'DETERMINISTIC_POINT_MASS','mean':[0.],'covariance':[[0.]]}))
    return tuple(cells)


def calibrate_method(method,experiment,null_design,stress_design) -> CalibrationRecord:
    require_fixed_known_gaussian(experiment)
    if not isinstance(method,GaussianMethod) or not isinstance(experiment,JointObservationLaw) or experiment.log_density is not None:
        raise TypeError("this adapter supplies only the fixed Gaussian acceptance proof")
    if null_design.get('mechanism')!='EXACT_ACCEPTANCE_PROOF':
        raise ValueError("simulator calibration requires a separately supported method adapter")
    if not null_design.get('proof_source'):raise ValueError("coverage proof source required")
    theta=method.configuration['null_parameter'];eta=method.configuration.get('null_nuisance')
    if not experiment.domain_contains(theta,eta):raise ValueError("hypothesis outside law domain")
    if callable(experiment.covariance):raise ValueError("uniform variable-support numerical obligations are unprovided")
    covariance=decompose_covariance(experiment.covariance)
    if not covariance.resolved:raise ValueError("exact proof numerical support/rank obligations unresolved")
    # A true covariance is part of the declared Gaussian law. Estimated scatter
    # or a simulator approximation cannot acquire that law by copying an ID.
    if any(word in experiment.approximation.upper() for word in ('EMPIRICAL','APPROXIMATION','ESTIMATED','QUADRATURE')):
        raise ValueError("an approximate/estimated law cannot use exact known-Gaussian calibration")
    obligations={'finite_symmetric_PSD':True,'rank_resolved':True,'rank':covariance.rank,
        'exact_null_support_checked':True,'method_config_id':method.config_id,'law_domain_id':experiment.domain_id,
        'coverage_argument':'true-parameter residual whitened on fixed Gaussian support; chi-square rank, not fitted-parameter subtraction'}
    return CalibrationRecord(method.scope_for(experiment),experiment.specification_id,method.implementation_id,'EXACT_ACCEPTANCE_PROOF',
        'EXACT_WITHIN_DECLARED_KNOWN_GAUSSIAN_LAW',experiment.conditioning_target,experiment.domain_id,experiment.domain_contains,
        obligations,(null_design['proof_source'],),tuple(stress_design or ()),experiment._binding_token)


def run_observed_scope(method,experiment,calibration) -> BranchResult:
    if not isinstance(experiment,JointObservationLaw):raise TypeError("unbound factories have no empirical eligibility")
    if (calibration.scope!=method.scope_for(experiment) or calibration.law_specification_id!=experiment.specification_id
            or calibration.method_implementation_id!=method.implementation_id):raise ValueError("calibration exact scope/specification/implementation mismatch")
    if calibration.supported_domain_id!=experiment.domain_id or calibration.conditioning_target!=experiment.conditioning_target:
        raise ValueError("calibration domain or conditioning target mismatch")
    if calibration.live_law_binding is not experiment._binding_token:
        raise ValueError("calibration scope requires the same bound prediction/domain implementation; recalibrate a reconstructed law")
    theta=method.configuration['null_parameter'];eta=method.configuration.get('null_nuisance')
    if not calibration.supported_domain(theta,eta):raise ValueError("experiment outside calibrated parameter domain")
    result=method.evaluate(experiment)
    if result.numeric_status=='NUMERICALLY_UNRESOLVED':outcome='NUMERICALLY_UNRESOLVED'
    else:outcome='COMPATIBLE' if result.accepted else 'REJECTED_CONJUNCTION'
    return BranchResult('R7-19','COMPLETED_SUCCESS',outcome,(),json_value(calibration.scope),calibration.evidence,
        (experiment.approximation,experiment.conditioning_target),valid_estimands=(method.configuration['hypothesis_id'],),
        uncertainty_type='FIXED_KNOWN_GAUSSIAN_CONFIDENCE',product_results={'acceptance':json_value(result),
            'hypothesis_id':method.configuration['hypothesis_id'],'null_parameter':theta,
            'confidence_region':'all domain parameters accepted by the same full-residual test'})


def robust_union_pvalue(valid_model_pvalues) -> float:
    values=finite_array(valid_model_pvalues,ndim=1,name='valid model p-values')
    if not len(values) or np.any(values<0) or np.any(values>1):raise ValueError("nonempty valid p-values in [0,1] required")
    return float(values.max())


def rank_pool_pvalue(scores,observed_index=0):
    values=finite_array(scores,ndim=1,name='complete score pool')
    if len(values)<2 or not 0<=observed_index<len(values):raise ValueError("observed plus reference pool required")
    return float(np.count_nonzero(values>=values[observed_index])/len(values))


def within_law_max_statistic(scores):
    values=finite_array(scores,ndim=2,name='row-symmetric registered diagnostics')
    if not values.size:raise ValueError("nonempty diagnostics")
    return values.max(axis=1)
