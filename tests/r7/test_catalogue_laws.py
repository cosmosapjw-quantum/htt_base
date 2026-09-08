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
