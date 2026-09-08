from dataclasses import replace
import numpy as np
import pytest
from htt.infer.jwst_host_hierarchy import HostPair


def cf4_fixture():
    from obsstat.cf4_current_stack import Cf4OperatorInputs
    ids=np.array(['b','a','c']);c=np.eye(3)+.1*np.ones((3,3))
    inputs=Cf4OperatorInputs(ids,np.array([0.,90.,180.]),np.array([0.,0.,30.]),np.array([20.,30.,40.]),
        np.array([1400.,2100.,2800.]),c,ids.copy(),np.array(['c','b']))
    product=dict(product_id='cf4',source_id='fixture',operator_inputs=inputs)
    selection=dict(selection_id='fixed',ordered_group_ids=['c','b'])
    calibration=dict(source_id='known fixture',sampling_law='KNOWN_GAUSSIAN_CONDITIONAL',covariance_source='known full matrix')
    return product,selection,calibration


def test_cf4_conditional_order_full_covariance_and_radial_curl_null():
    from obsstat.cf4_current_stack import galactic_unit_vectors
    from htt.infer.r7_cf4_law import build_cf4_law
    p,s,c=cf4_fixture();law=build_cf4_law(p,s,c)
    assert law.scope.model_id=='CF4_CONDITIONAL_AFFINE'
    assert law.measurement_ids==('cf4:group:c','cf4:group:b')
    np.testing.assert_allclose(law.mean([70.,0,0,0,0,0,0,0,0],None),[2800.,1400.])
    assert law.covariance[0,1]==.1
    n=galactic_unit_vectors(p['operator_inputs'].galactic_longitude_deg,p['operator_inputs'].galactic_latitude_deg)
    anti=np.array([[0.,1.,-2.],[-1.,0.,3.],[2.,-3.,0.]])
    np.testing.assert_allclose(np.einsum('ni,ij,nj->n',n,anti,n),0,atol=1e-15)
    bad=replace(p['operator_inputs'],covariance_group_ids=np.array(['a','b','c']))
    with pytest.raises(ValueError,match='order'):build_cf4_law(dict(p,operator_inputs=bad),s,c)


def test_selected_latent_density_is_normalized_and_factory_unbound():
    from htt.infer.r7_cf4_law import SelectedLatentBlock,build_cf4_law
    # xi~uniform(0,1), y|xi uniform(0,2); selection y/2 -> selected density y/2.
    block=SelectedLatentBlock(((0.,1.),),((0.,2.),),lambda x,t,e,p:1.,lambda y,x,t,e,p:.5,lambda y:y[0]/2,'fixture')
    assert abs(block.loglik(np.array([1.]),None,None,None)-np.log(.5))<1e-10
    assert abs(block.loglik(np.array([2.]),None,None,None))<1e-10
    product=dict(product_id='raw',observed=np.array([1.]),measurement_ids=['r'],parameter_names=['theta'],parameter_units=['1'],
        mean=lambda t,e,p:np.array([4/3]),domain_id='positive',domain_contains=lambda t,e:t[0]>0,source_id='s')
    factory=build_cf4_law(product,dict(latent_block=block,selection_id='s'),dict(source_id='known'))
    assert not factory.empirical_eligible and factory.unfilled_prediction_slots==('distance',)


def jwst_fixture():
    pair=HostPair('family','host','A',30.1,.2,'B',30.,.2)
    p=dict(product_id='jwst',source_id='table',selection_id='fixed-host',pairs=[pair])
    ids=('family:host:A','family:host:B')
    c=dict(matrix=np.array([[.04,.02],[.02,.04]]),source_id='shared measurement fixture',measurement_ids=ids)
    cal=dict(source_id='calibration fixture',host_population_covariance=np.array([[.25]]),design=np.array([[1.,.5],[1.,-.5]]),
        parameter_names=('geometry','calibration'),parameter_units=('mag','mag'),measurement_df=5.)
    return p,c,cal


def test_jwst_host_geometry_cancels_and_shared_covariance_once():
    from htt.infer.r7_jwst_law import build_jwst_law
    p,c,cal=jwst_fixture();law=build_jwst_law(p,c,cal,'GAUSSIAN')
    np.testing.assert_allclose(law.jacobian_theta(None,None),[[0.,1.]])
    np.testing.assert_allclose(law.covariance,[[.04]])
    assert law.loglik([30.,.1])==law.loglik([100.,.1])
    student=build_jwst_law(p,c,cal,'STUDENT_T')
    assert student.specification['host_population']=='GAUSSIAN' and np.isfinite(student.loglik([30.,.1]))
    exact=dict(c,matrix=np.full((2,2),.04))
    singular=build_jwst_law(p,exact,cal,'GAUSSIAN')
    assert singular.loglik([30.,0.])==-np.inf
    assert singular.loglik([30.,singular.observed[0]])==0.
    with pytest.raises(ValueError,match='only once'):build_jwst_law(dict(p,pairs=p['pairs']*2),c,cal,'GAUSSIAN')


def test_desi_every_mock_is_refitted_and_covariance_is_not_known_law():
    from htt.infer.r7_desi_law import build_desi_law
    from scripts.observed_runs.run_desi_bgs_bright import _synthetic_selection,_synthetic_realization
    s=_synthetic_selection()
    observed=_synthetic_realization('OBSERVED',0)
    ez=[_synthetic_realization('EZMOCK',i) for i in range(1,1001)]
    ab=[_synthetic_realization('ABACUS',i) for i in range(25)]
    result=build_desi_law(dict(product_id='desi',source_ids=['fixture'],realization=observed),
        dict(source_id='random-fixture',window_ids=s.window_ids,frame=s.coordinate_frame_id),
        dict(ezmock=ez,abacus=ab,law_id='P_synthetic'),s)
    assert result.outcome=='SCENARIO_ONLY'
    assert result.controls['mock_support']['ezmock_count']==1000
    assert result.controls['mock_support']['abacus_count']==25
    assert len(result.controls['observed_features'])==18
    assert len(result.controls['normalization_hat'])==6


def test_student_measurement_gaussian_host_enlarges_singular_support():
    from htt.infer.r7_jwst_law import build_jwst_law
    from scipy.stats import norm,t
    pair=HostPair('family','host','A',.1,1.,'B',.123,0.)
    p=dict(product_id='jwst',source_id='table',selection_id='fixed',pairs=[pair],measurement_mode='ABSOLUTE')
    c=dict(matrix=np.diag([1.,0.]),source_id='known scale',measurement_ids=('family:host:A','family:host:B'))
    cal=dict(source_id='known host',host_population_covariance=[[.25]],design=np.ones((2,1)),parameter_names=('mu',),
        parameter_units=('mag',),measurement_df=5.,quadrature_order=128)
    law=build_jwst_law(p,c,cal,'STUDENT_T')
    expected=norm.logpdf(.123,scale=.5)+t.logpdf(.1-.123,df=5)
    assert abs(law.loglik([0.])-expected)<1e-6
    assert 'QUADRATURE_APPROXIMATION' in law.approximation
