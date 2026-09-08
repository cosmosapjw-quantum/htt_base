from dataclasses import replace
import numpy as np
import pytest
from common.r7_contracts import ScopeKey
from htt.infer.r7_gaussian_law import JointObservationLaw,ObservationLawFactory
from htt.infer.r7_calibration import (GaussianMethod,calibrate_method,run_observed_scope,robust_union_pvalue,
    rank_pool_pvalue,within_law_max_statistic,clopper_pearson)


def fixture():
    law=JointObservationLaw(ScopeKey('e','law','model',('data',),method_config_id='initial'),np.array([1.]),('row',),
        ('theta',),('K',),lambda t,e:np.array(t),np.eye(1),dict(source_ids=['known fixture'],selection_law='fixed',
        covariance_source='known',mean_definition='theta'),'D',lambda t,e:abs(t[0])<=10)
    method=GaussianMethod(dict(statistic='FULL_RESIDUAL_CHISQUARE_WITH_SUPPORT',alpha=.05,nuisance_policy='FIXED',
        fitting_procedure='NONE',selection_procedure='FIXED_ROWS',null_parameter=[0.],hypothesis_id='theta=0'))
    calibration=calibrate_method(method,law,dict(mechanism='EXACT_ACCEPTANCE_PROOF',proof_source='r7_confidence.py coverage argument'),())
    return law,method,calibration


def test_exact_proof_matches_full_scope_method_and_conditioning():
    law,method,cal=fixture()
    assert run_observed_scope(method,law,cal).scientific_outcome=='COMPATIBLE'
    for field,value in [('experiment_id','wrong'),('law_id','wrong'),('model_id','wrong'),('dataset_ids',('wrong',)),
                        ('conventions','wrong'),('version','wrong')]:
        with pytest.raises(ValueError,match='scope'):run_observed_scope(method,replace(law,scope=replace(law.scope,**{field:value})),cal)
    wrong=GaussianMethod(dict(method.configuration,alpha=.04))
    with pytest.raises(ValueError,match='scope'):run_observed_scope(wrong,law,cal)
    with pytest.raises(ValueError,match='conditioning'):run_observed_scope(method,replace(law,conditioning_target='wrong'),cal)
    with pytest.raises(ValueError,match='scope'):run_observed_scope(method,law,replace(cal,method_implementation_id='wrong'))


def test_factories_estimated_covariance_and_outside_domain_refused():
    law,method,cal=fixture()
    factory=ObservationLawFactory('f',('row',),('distance',),{},lambda p:law)
    with pytest.raises(TypeError):run_observed_scope(method,factory,cal)
    with pytest.raises(ValueError,match='approximate'):
        calibrate_method(method,replace(law,approximation='EMPIRICAL_COVARIANCE'),dict(mechanism='EXACT_ACCEPTANCE_PROOF',proof_source='proof'),())
    with pytest.raises(ValueError,match='outside'):
        run_observed_scope(method,law,replace(cal,supported_domain=lambda t,e:False))


def test_complete_pool_ties_permutation_nans_and_distinct_max_operations():
    scores=np.array([1.,3.,3.,0.])
    assert rank_pool_pvalue(scores,1)==.5
    permutation=np.array([2,0,3,1])
    assert rank_pool_pvalue(scores[permutation],3)==.5
    assert rank_pool_pvalue(np.ones(5))==1.
    with pytest.raises(ValueError,match='finite'):rank_pool_pvalue([1.,np.nan])
    with pytest.raises(ValueError):robust_union_pvalue([])
    assert robust_union_pvalue([.01,.40])==.40
    np.testing.assert_equal(within_law_max_statistic([[1.,3.],[4.,2.]]),[3.,4.])
    assert clopper_pearson(9500,10000)[0]>=.94
    assert clopper_pearson(500,10000)[1]<=.06


def test_copying_law_names_cannot_replace_bound_mean():
    law,method,cal=fixture()
    with pytest.raises(ValueError,match='bound prediction'):
        run_observed_scope(method,replace(law,mean=lambda t,e:np.array([99.])),cal)


def test_mutating_captured_prediction_state_invalidates_calibration():
    law,method,_=fixture();offset=np.array([0.])
    law=replace(law,mean=lambda t,e:np.asarray(t)+offset)
    cal=calibrate_method(method,law,dict(mechanism='EXACT_ACCEPTANCE_PROOF',proof_source='proof'),())
    assert run_observed_scope(method,law,cal).scientific_outcome=='COMPATIBLE'
    offset[0]=100.
    with pytest.raises(ValueError,match='callable state mutated'):run_observed_scope(method,law,cal)


def test_approximate_covariance_cannot_bypass_calibration_via_inversion():
    from htt.infer.r7_confidence import invert_acceptance,PhysicalDomain,GaussianAcceptanceRule
    law,_,_=fixture();law=replace(law,approximation='EMPIRICAL_COVARIANCE')
    with pytest.raises(ValueError,match='approximate'):
        invert_acceptance(law,PhysicalDomain('R',('theta',),lambda t,e:True),GaussianAcceptanceRule())


def test_mutating_callable_object_prediction_invalidates_calibration():
    law,method,_=fixture()
    class Mean:
        def __init__(self):self.offset=0.
        def __call__(self,t,e):return np.asarray(t)+self.offset
    mean=Mean();law=replace(law,mean=mean)
    cal=calibrate_method(method,law,dict(mechanism='EXACT_ACCEPTANCE_PROOF',proof_source='proof'),())
    mean.offset=10.
    with pytest.raises(ValueError,match='callable state mutated'):run_observed_scope(method,law,cal)
