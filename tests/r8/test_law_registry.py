from fractions import Fraction as F
import numpy as np
import pytest
from htt.infer.r7_desi_law import build_compressed_bao_law
from htt.infer.r8_law_registry import admit_product, bind_method, run_scope, ScopedRefusal

def example(value=.98):
    law=build_compressed_bao_law(dict(likelihood_name='gaussian_likelihood',parameter='qiso',observed=[value],covariance=[[.0004]],window=[[1]],DV_over_rd_fid=8.,zeff=.2,source_id='test-fixture-release'))
    product=dict(product_id='ANY_PRODUCT_KEY',observed=law.observed,measurement_ids=law.measurement_ids,source_ids=law.specification['source_ids'])
    return product,dict(law=law,frame='NONANGULAR',conditioning_id=law.conditioning_target)

def test_generic_dispatch_uses_live_law_not_node_or_label():
    p,s=example(); a=admit_product(p,s); method=bind_method(a,F(1,20))
    out=run_scope(a,method,[1.])
    assert out.membership=='ACCEPT' and out.quadratic==pytest.approx(1.)
    assert out.scope['product_id']=='ANY_PRODUCT_KEY'
    assert run_scope(a,method,[-1.]).membership=='REJECT'
    p2,s2=example(); other=admit_product(p2,s2)
    with pytest.raises(ValueError):run_scope(other,method,[1.])
    s['law'].specification['mean_definition']='changed'
    with pytest.raises(ValueError):run_scope(a,method,[1.])

def test_factory_missing_and_mutated_inputs_cannot_be_admitted():
    p,s=example()
    assert isinstance(admit_product(p,{}),ScopedRefusal)
    assert isinstance(admit_product({**p,'measurement_ids':['wrong']},s),ScopedRefusal)
    assert isinstance(admit_product({**p,'observed':[99.]},s),ScopedRefusal)
    s['conditioning_id']='another conditional experiment'
    assert isinstance(admit_product(p,s),ScopedRefusal)

def test_actual_partial_sampling_variable_routes_without_joint_gaussian():
    from htt.infer.r8_law_registry import PartialObservationLaw
    for premise in ('KNOWN_GAUSSIAN_MARGINALS','KNOWN_VARIANCE_UPPER_BOUNDS'):
        mean_state=np.array([0.,0.])
        law=PartialObservationLaw([.1,.2],('a','b'),('marginal-fixture',),[1.,1.],
            lambda x:x+mean_state,lambda x:x.shape==(2,),'R2','FIXED_ORIGINAL_VARIABLE','TEST_FRAME',
            ('K','K'),premise,'INDEPENDENT_PREMISE_FIXTURE',('x','y'))
        product=dict(product_id='CF4_CONDITIONAL_FIXTURE',observed=law.observed,measurement_ids=law.measurement_ids,source_ids=law.source_ids)
        a=admit_product(product,dict(law=law,frame=law.frame,conditioning_id=law.conditioning_id));m=bind_method(a,F(1,80))
        assert run_scope(a,m,[0.,0.]).membership=='ACCEPT'
        assert run_scope(a,m,[100.,100.]).membership=='REJECT'
        mean_state[0]=1
        with pytest.raises(ValueError):run_scope(a,m,[0.,0.])
