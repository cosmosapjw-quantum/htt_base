"""Independent finite-mixture, selected-density and Gaussian-limit falsifiers."""
from dataclasses import replace
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import logsumexp
from scipy.stats import norm, laplace
from numpy.polynomial.hermite import hermgauss
from common.r7_contracts import ScopeKey
from common.depth_path import DepthRepresentation
from htt.infer.r7_gaussian_law import JointObservationLaw, gaussian_loglik
from htt.infer.r7_joint_experiment import (ProperSharedLatentRule, SelectedConditionalBlock,
    SelectedJointDensityProvider, JointGaussianProvider, compose_joint_law)
from htt.infer.r9_depth_law import selected_depth_law


def fixture(name, y, selected=False, family='normal'):
    spec=dict(source_ids=['fixture'], selection_law='positive' if selected else 'all',
              covariance_source='supplied fixture', mean_definition='theta+shared_eta')
    law=JointObservationLaw(ScopeKey(name,name,'common',(name,),method_config_id='fixed'),
        np.array([y]), (name,), ('theta',), ('1',), lambda t,e:np.array([t[0]+e[0]]),
        np.eye(1), spec, 'real', lambda t,e:True, shared_latent_ids=('calibration',),
        conditioning_target='FIXED_OBSERVED_COUNT')
    def density(y,t,e):
        loc=t[0]+e[0]
        dist=norm if family == 'normal' else laplace
        if selected and y[0] <= 0:return -np.inf
        return float(dist.logpdf(y[0], loc=loc)-(dist.logsf(0,loc=loc) if selected else 0.))
    block=SelectedConditionalBlock(law.specification_id,law.scope.identity,law.measurement_ids,
        (name+'-object',),'fixture',spec['selection_law'],
        'normalized location density divided by positive-selection survival' if selected else 'normalized location density',density)
    return law,block


def composed(pairs, rule, **kwargs):
    laws,blocks=zip(*pairs)
    ids=tuple(dict.fromkeys(i for l in laws for i in l.measurement_ids))
    provider=SelectedJointDensityProvider(blocks,ids,rule,'manufactured joint model',
                                         conditional_independence_source='manufactured independent errors given eta',**kwargs)
    return compose_joint_law(laws,[],provider).admitted_laws[0]


def test_shared_latent_product_integrated_once_and_not_independent_marginals():
    rule=ProperSharedLatentRule(('calibration',),np.array([[-1.],[1.]]),np.array([.3,.7]),'discrete fixture')
    pairs=[fixture('a',.4,family='laplace'),fixture('b',1.4,family='laplace')]
    joint=composed(pairs,rule)
    reference=sum(w*laplace.pdf(.4,loc=.2+e[0])*laplace.pdf(1.4,loc=.2+e[0])
                  for e,w in zip(rule.nodes,rule.weights))
    assert joint.loglik([.2]) == pytest.approx(np.log(reference),abs=1e-13)
    independent=sum(w*laplace.pdf(.4,loc=.2+e[0]) for e,w in zip(rule.nodes,rule.weights))*sum(
        w*laplace.pdf(1.4,loc=.2+e[0]) for e,w in zip(rule.nodes,rule.weights))
    assert abs(np.log(independent)-joint.loglik([.2])) > .05
    assert joint.specification['count_factor'] == 'NONE'
    with pytest.raises(ValueError,match='integrated'):joint.loglik([.2],[0.])


def test_selected_nongaussian_normalization_and_independent_continuous_reference():
    nodes,weights=hermgauss(48)
    rule=ProperSharedLatentRule(('calibration',),(nodes*.3*np.sqrt(2))[:,None],weights/np.sqrt(np.pi),
                              'Gaussian prior quadrature','CONTINUOUS_QUADRATURE')
    pairs=[fixture('a',.4,True),fixture('b',1.4,True)]
    joint=composed(pairs,rule)
    reference=quad(lambda e:norm.pdf(e,scale=.3)*norm.pdf(.4,loc=.2+e)*norm.pdf(1.4,loc=.2+e)
                   /norm.sf(0,loc=.2+e)**2,-3,3,epsabs=1e-11)[0]
    assert joint.loglik([.2]) == pytest.approx(np.log(reference),abs=2e-10)
    # Independently integrate each conditional factor on its actual selection.
    for e in [-1.,0.,1.]:
        mass=quad(lambda y:np.exp(pairs[0][1].log_density(np.array([y]),[.2],[e])),0,np.inf)[0]
        assert mass == pytest.approx(1.,abs=1e-9)
    assert 'NOT_CERTIFIED_EVIDENCE' in joint.approximation


def test_gaussian_limit_matches_existing_provider_order_and_density():
    nodes,weights=hermgauss(48)
    rule=ProperSharedLatentRule(('calibration',),(nodes*.4*np.sqrt(2))[:,None],weights/np.sqrt(np.pi),
                              'Gaussian quadrature','CONTINUOUS_QUADRATURE')
    pairs=[fixture('a',.4),fixture('b',1.4)]
    joint=composed(pairs,rule)
    covariance=np.eye(2)+.16*np.ones((2,2))
    assert joint.loglik([.2]) == pytest.approx(gaussian_loglik(np.array([.2,1.2]),covariance),abs=1e-11)
    # Existing provider on matching marginals of the same known joint Gaussian.
    laws=[replace(p[0],covariance=np.array([[1.16]]),shared_latent_ids=()) for p in pairs]
    gaussian=compose_joint_law(laws,[],JointGaussianProvider(covariance,('a','b'),'analytic joint',(),
                                                          'FIXED_OBSERVED_COUNT')).admitted_laws[0]
    assert gaussian.loglik([.2],[0.]) == pytest.approx(joint.loglik([.2]),abs=1e-11)


def test_duplicate_adds_no_evidence_and_conflicts_refused():
    rule=ProperSharedLatentRule(('calibration',),np.array([[-1.],[1.]]),np.array([.5,.5]),'prior')
    a,b=fixture('a',.4)
    provider=SelectedJointDensityProvider((b,),('a',),rule,'joint','independence')
    single=compose_joint_law([a],[],provider).admitted_laws[0]
    duplicate=compose_joint_law([a,a],[],provider)
    assert duplicate.admitted_laws[0].loglik([.2]) == single.loglik([.2])
    assert duplicate.duplicate_measurements == ('a',)
    with pytest.raises(ValueError,match='conflicting'):
        compose_joint_law([a,replace(a,observed=np.array([.8]))],[],provider)
    c,d=fixture('b',.4)
    c=replace(c,measurement_ids=('a',))
    d=replace(d,measurement_ids=('a',),law_specification_id=c.specification_id,law_scope_id=c.scope.identity)
    with pytest.raises(ValueError,match='inconsistent'):
        composed([(a,b),(c,d)],rule)
    with pytest.raises(ValueError,match='conditioning'):
        composed([(a,b),(replace(c,conditioning_target='OTHER'),d)],rule)


def test_explicit_joint_provider_is_used_on_canonical_Y():
    rule=ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([1.]),'prior')
    pairs=[fixture('a',.4),fixture('b',1.4)]
    def conditional(y,t,e):
        assert y.shape == (2,)
        return gaussian_loglik(y-t[0]-e[0],np.array([[1.,.6],[.6,1.]]))
    joint=composed(pairs,rule,joint_log_density=conditional,joint_normalization_definition='normalized SPD Gaussian')
    assert joint.loglik([.2]) == pytest.approx(conditional(np.array([.4,1.4]),[.2],[0.]))


def test_profiles_improper_weights_and_unbound_sources_refused():
    a,b=fixture('a',.4)
    with pytest.raises(ValueError,match='profile'):
        replace(b,density_kind='PROFILE_LIKELIHOOD')
    with pytest.raises(ValueError,match='proper'):
        ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([.7]),'bad')
    rule=ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([1.]),'proper')
    with pytest.raises(ValueError,match='binding'):
        composed([(a,replace(b,source_id='unbound'))],rule)
    provider=SelectedJointDensityProvider((b,),('a',),rule,'joint')
    with pytest.raises(ValueError,match='independence'):
        compose_joint_law([a],[],provider)


def test_depth_same_Y_bijection_preserves_density_ratios_and_refuses_contrast():
    rule=ProperSharedLatentRule(('calibration',),np.array([[-1.],[1.]]),np.array([.5,.5]),'prior')
    joint=composed([fixture('a',.4,True),fixture('b',1.4,True)],rule)
    rep=DepthRepresentation((1,1),(np.array([[2.]]),),('a','b'),'fixed transport')
    depth=selected_depth_law(joint,rep)
    np.testing.assert_allclose(rep.restore(depth.observed),joint.observed)
    assert depth.loglik([.2])-depth.loglik([.8]) == pytest.approx(joint.loglik([.2])-joint.loglik([.8]))
    assert depth.loglik([.2]) == joint.loglik([.2]) # T has determinant one.
    assert depth.specification['not_an_independent_measurement']
    with pytest.raises(ValueError,match='contrasts'):
        selected_depth_law(joint,rep,view='CONTRASTS')


def test_joint_selected_discrete_density_integrates_to_one():
    rule=ProperSharedLatentRule(('calibration',),np.array([[-.4],[.5]]),np.array([.3,.7]),'prior')
    # Independent nested quadrature integrates the actual selected joint dY law,
    # including both per-latent selection denominators, at a nonzero theta.
    _,a=fixture('a',.4,True)
    _,b=fixture('b',1.4,True)
    mass=quad(lambda x:quad(lambda y:sum(w*np.exp(a.log_density(np.array([x]),[.2],e)
            +b.log_density(np.array([y]),[.2],e)) for e,w in zip(rule.nodes,rule.weights)),
            0,8,epsabs=1e-9)[0],0,8,epsabs=1e-9)[0]
    assert mass == pytest.approx(1.,abs=1e-9)


def test_shared_latent_injection_mean_and_cross_covariance():
    # Manufactured repeated joint draws with one shared calibration per draw.
    # This is an injection check of the supplied model, not actual-data coverage.
    rng=np.random.default_rng(2505); n=20000
    eta=rng.choice([-1.,1.],size=n,p=[.3,.7]); theta=.6
    y=theta+eta[:,None]+rng.laplace(size=(n,2))
    estimate=y.mean()-.4
    assert abs(estimate-theta) < .04
    assert abs(np.cov(y.T)[0,1]-.84) < .06
    assert abs(np.var(y[:,0])-2.84) < .10


def test_duplicate_conditioning_and_prediction_conflict_before_integration():
    a,b=fixture('a',.4)
    rule=ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([1.]),'proper')
    provider=SelectedJointDensityProvider((b,),('a',),rule,'joint','independence')
    with pytest.raises(ValueError,match='conditioning'):
        compose_joint_law([a,replace(a,conditioning_target='PROFILE')],[],provider)
    with pytest.raises(ValueError,match='prediction'):
        compose_joint_law([a,replace(a,mean=lambda t,e:np.array([100.]))],[],provider)
    with pytest.raises(ValueError,match='normalized joint'):
        composed([fixture('a',.4),fixture('b',1.4)],rule,
                 joint_log_density=lambda y,t,e:0.,joint_normalization_definition='profile',
                 joint_density_kind='PROFILE')


def test_reviewer_component_transfer_and_quadrature_status_are_not_erased():
    a,b=fixture('a',.4)
    a=replace(a,transfer_source='AniCLASS_external_fixture',
              approximation='NUMERICALLY_NORMALIZED_LATENT_LAW_WITH_QUADRATURE_ERROR',
              conditioning_target='SELECTED_JOINT_BLOCK_GIVEN_LATENT_FIELD_AND_COUNT')
    rule=ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([1.]),'proper discrete')
    joint=composed([(a,b)],rule)
    assert joint.transfer_source == a.transfer_source
    assert 'QUADRATURE_ERROR' in joint.approximation
    assert 'EXACT_WITHIN_SUPPLIED_DISCRETE_PRIOR' != joint.approximation
    component=joint.specification['input_law_provenance'][0]
    assert component['transfer_source'] == a.transfer_source
    assert component['approximation'] == a.approximation
    assert component['conditioning_target'] == a.conditioning_target


@pytest.mark.parametrize('target',['POISSON_RANDOM_COUNT','PROFILE_LIKELIHOOD','UNKNOWN','UNCONDITIONAL_KNOWN_GAUSSIAN'])
def test_reviewer_random_count_profile_and_unknown_source_conditioning_refused(target):
    a,b=fixture('a',.4)
    rule=ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([1.]),'proper discrete')
    with pytest.raises(ValueError,match='fixed-observed-count'):
        composed([(replace(a,conditioning_target=target),b)],rule)


def test_component_provenance_aggregate_mixed_transfers_and_unknown_approximation():
    a,b=fixture('a',.4); c,d=fixture('b',1.4)
    a=replace(a,transfer_source='external-A',approximation='UNKNOWN_COMPONENT_ACCURACY')
    c=replace(c,transfer_source='external-B')
    rule=ProperSharedLatentRule(('calibration',),np.array([[0.]]),np.array([1.]),'discrete')
    joint=composed([(a,b),(c,d)],rule)
    assert joint.transfer_source.startswith('JOINT_SOURCE_BOUND_TRANSFER:')
    assert joint.specification['input_transfer_sources'] == ('external-A','external-B')
    assert 'UNKNOWN_COMPONENT_ACCURACY' in joint.approximation
    assert joint.specification['aggregate_transfer_source'] == joint.transfer_source
    rep=DepthRepresentation((1,1),(np.array([[1.]]),),('a','b'),'fixed')
    depth=selected_depth_law(joint,rep)
    assert depth.transfer_source == joint.transfer_source
    assert depth.approximation == joint.approximation
    assert depth.specification['input_law_provenance'] == joint.specification['input_law_provenance']
    with pytest.raises(ValueError,match='conflicting'):
        compose_joint_law([a,replace(a,approximation='NUMERICAL_APPROXIMATION')],[],None)
