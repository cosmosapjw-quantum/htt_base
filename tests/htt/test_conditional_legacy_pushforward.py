import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest
from htt.infer.conditional_legacy_pushforward import (ConditionalDraw, PosteriorDrawSource,
    conditional_legacy_image, posterior_legacy_image)
from common.typefree_functionals import FunctionalSpec, FunctionalRecord
from common.depth_path import DepthRepresentation

SOURCES = Path(__file__).resolve().parents[2] / 'docs/observational_upgrade_r2/R2-04/sources'
spec = importlib.util.spec_from_file_location('r204_legacy_adapter', SOURCES/'code/legacy_adapter.py')
legacy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = legacy
spec.loader.exec_module(legacy)


def adapter():
    return legacy.LegacyAdapter(SOURCES/'sources/HTT/HTT', legacy.AnalysisContract(
        'finite-fixture-v1', 'fixture-flow', 'fixed-flat', 'conditional-shear', 'synthetic-sampling'))


def run(draws, weights=None, **kwargs):
    return conditional_legacy_image(draws, adapter(), source_id='deterministic-fixture-v1',
        joint_id='paired-fixture-v1', weights=[1]*len(draws) if weights is None else weights,
        law_kind='SAMPLING', **kwargs)


def test_signed_unknown_boundary_and_oracle():
    draws = [ConditionalDraw('a', .1,.5,0,0,1), ConditionalDraw('b',.2,0,0,0,1),
             ConditionalDraw('c',None,0,0,0,1)]
    a = run(draws,[2,3,5],q_thresholds=[0,.2])
    assert a['x'].atoms[0].value < 0
    assert a['x'].undefined_mass == .5
    assert a['Pi_intervals'][1]['known_boundary_mass'] == .3
    assert a['Pi_intervals'][0]['lower'] == .3
    assert a['Pi_intervals'][0]['upper'] == .8
    b = run(draws,[2e307,3e307,5e307],q_thresholds=[0,.2])
    assert a['Pi_intervals'] == b['Pi_intervals']
    assert a['draw_ids'] == ('a','b','c')
    for d, atom in zip(draws[:2],a['x'].atoms[:2]):
        assert float(atom.value) == adapter().bounds.x_defect(d.Sigma2,
            Omega_tilt=d.Omega_tilt,Omega_k_aniso=d.curvature_delta,W2=d.W2)


def test_invalid_denominators_preserve_x_and_mass():
    a = run([ConditionalDraw('a',1,0,0,0,0),ConditionalDraw('b',2,0,0,0,-1)])
    assert a['x'].undefined_mass == 0
    assert a['Q'].undefined_mass == 1
    assert a['Pi_intervals'][0]['upper'] == 1


def test_same_draw_correlation_is_not_permutation_invariant():
    a = run([ConditionalDraw('a',1,0,0,0,1),ConditionalDraw('b',4,0,0,0,4)],q_thresholds=[1])
    b = run([ConditionalDraw('a',1,0,0,0,4),ConditionalDraw('b',4,0,0,0,1)],q_thresholds=[1])
    assert a['Pi_intervals'][0]['lower'] == 0
    assert b['Pi_intervals'][0]['lower'] == .5


def depth_record(latent, label, value):
    spec = FunctionalSpec('depth-fixture', (label,), (1,),0,'SIGNED','scalar',
        'dimensionless','fixture-flow','fixture',label,'VA-02','fixture','signed')
    return FunctionalRecord(latent,spec,np.array([value]),np.array([0]))


def test_depth_shared_latent_and_missing_cross_blocks():
    rep = DepthRepresentation((1,1),(np.eye(1),),('near','far'),'fixture-fixed')
    rows = (depth_record('a','near',1),depth_record('a','far',3))
    d = ConditionalDraw('a',1,0,0,0,1,depth_records=rows)
    a = run([d],depth_representation=rep,covariance_blocks={(0,0):[[1]],(1,1):[[1]]})
    np.testing.assert_equal(a['depth'][0].contrasts,[2])
    assert a['depth'][0].covariance_status == 'COVARIANCE_UNAVAILABLE'
    b = run([d],depth_representation=rep,covariance=[[1,.5],[.5,1]])
    np.testing.assert_allclose(b['depth'][0].contrast_covariance,[[1]])
    bad = ConditionalDraw('a',1,0,0,0,1,depth_records=(rows[0],depth_record('b','far',3)))
    with pytest.raises(ValueError,match='draw ID'):
        run([bad],depth_representation=rep)


def test_set_and_missing_sector_semantics():
    d = ConditionalDraw('a',1,None,0,0,1)
    a = conditional_legacy_image([d],adapter(),source_id='finite-set-v1',joint_id='set-v1',
        weights=None,law_kind='FINITE_SET')
    assert a['Pi_intervals'] is None and a['Q'].undefined_mass is None
    assert a['Q'].atoms[0].value is None
    assert a['F4'] is None and a['filling_fraction'] is None
    with pytest.raises(ValueError):
        conditional_legacy_image([d],adapter(),source_id='fixture',joint_id='fixture',
            weights=[1],law_kind='POSTERIOR')


def test_missing_depth_retains_measure_mass():
    rep = DepthRepresentation((1,1),(np.eye(1),),('near','far'),'fixture-fixed')
    near = depth_record('a','near',1)
    far = depth_record('a','far',3)
    missing = FunctionalRecord('a',far.spec,None,None,status='MISSING_SECTOR')
    d = ConditionalDraw('a',1,0,0,0,1,depth_records=(near,missing))
    a = run([d],depth_representation=rep)
    assert a['depth_image'].undefined_mass == 1
    assert a['depth_image'].atoms[0].latent_id == a['Q'].atoms[0].latent_id
    assert a['depth_image'].atoms[0].value is None


@pytest.mark.parametrize('field,value', [
    ('units','km/s'), ('definition_id','other-depth-definition'),
    ('frame','other-flow'), ('branch','other-branch'),
    ('normalization','other-normalization'), ('epoch','other-epoch'),
    ('domain_id','other-domain'), ('output_shape',(1,1)),
])
def test_cross_draw_depth_specs_must_match(field,value):
    from dataclasses import replace
    rep = DepthRepresentation((1,1),(np.eye(1),),('near','far'),'fixture-fixed')
    first = tuple(depth_record('a',label,v) for label,v in [('near',1),('far',3)])
    second = tuple(depth_record('b',label,v) for label,v in [('near',2),('far',4)])
    # Both depth blocks change together: each path is valid in isolation.
    second = tuple(FunctionalRecord('b',replace(r.spec,**{field:value}),
        r.values.reshape((1,1)) if field == 'output_shape' else r.values,
        r.reference.reshape((1,1)) if field == 'output_shape' else r.reference) for r in second)
    draws = [ConditionalDraw('a',1,0,0,0,1,depth_records=first),
             ConditionalDraw('b',1,0,0,0,1,depth_records=second)]
    with pytest.raises(ValueError,match='cross-draw depth specs'):
        run(draws,depth_representation=rep)


def test_multidraw_depth_measure_and_missing_mass():
    rep = DepthRepresentation((1,1),(np.eye(1),),('near','far'),'fixture-fixed')
    first = tuple(depth_record('a',label,v) for label,v in [('near',1),('far',3)])
    second = tuple(depth_record('b',label,v) for label,v in [('near',2),('far',4)])
    second = (second[0],FunctionalRecord('b',second[1].spec,None,None,status='MISSING_SECTOR'))
    draws = [ConditionalDraw('a',1,0,0,0,1,depth_records=first),
             ConditionalDraw('b',1,0,0,0,1,depth_records=second)]
    result = run(draws,[2,3],depth_representation=rep)
    assert result['depth_image'].undefined_mass == pytest.approx(.6,abs=2e-16,rel=0)
    assert tuple(a.latent_id for a in result['depth_image'].atoms) == ('a','b')
    np.testing.assert_allclose([a.mass for a in result['depth_image'].atoms], [.4,.6],rtol=0,atol=2e-16)
    np.testing.assert_equal(result['depth_image'].atoms[0].value,[2])
    assert result['depth_image'].atoms[1].value is None


def test_typed_posterior_image_keeps_original_draws_weights_and_unknown_mass():
    draws=(ConditionalDraw('a',.1,.5,0,0,1),ConditionalDraw('b',.2,0,0,0,1),
           ConditionalDraw('c',None,0,0,0,1))
    source=PosteriorDrawSource('joint-posterior-v1','observed-products-v1','joint-law-v1',
        'proper-prior-v1',('a','b','c'),(.2,.3,.5),'fixture-flow','fixed-flat')
    result=posterior_legacy_image(draws,adapter(),source,q_thresholds=(0.,.2))
    assert result['law_kind']=='POSTERIOR'
    assert result['draw_ids']==source.draw_ids
    assert [a.mass for a in result['x'].atoms]==pytest.approx(source.weights)
    assert result['x'].undefined_mass==pytest.approx(.5)
    assert result['Pi_intervals'][1]['known_boundary_mass']==pytest.approx(.3)
    assert result['Q'].atoms[2].status!='DEFINED'
    assert result['posterior_source']==source
    assert result['F4'] is None and result['filling_fraction'] is None


def test_posterior_interface_refuses_relabel_and_inconsistent_contract():
    draw=(ConditionalDraw('a',1,0,0,0,1),)
    source=PosteriorDrawSource('posterior','data','likelihood','prior',('a',),(1.,),
                               'fixture-flow','fixed-flat')
    with pytest.raises(ValueError,match='SAMPLING or FINITE_SET'):
        conditional_legacy_image(draw,adapter(),source_id='data',joint_id='posterior',
                                 weights=(1.,),law_kind='POSTERIOR')
    with pytest.raises(ValueError,match='order/identity'):
        posterior_legacy_image((ConditionalDraw('b',1,0,0,0,1),),adapter(),source)
    with pytest.raises(ValueError,match='contract mismatch'):
        posterior_legacy_image(draw,adapter(),
            PosteriorDrawSource('posterior','data','likelihood','prior',('a',),(1.,),
                                'other-flow','fixed-flat'))
    with pytest.raises(ValueError,match='normalized'):
        PosteriorDrawSource('posterior','data','likelihood','prior',('a',),(.5,),
                            'fixture-flow','fixed-flat')
