"""R7 finite acceptance tests. MES_R7_SOURCE points to the unchanged input bundle."""
import importlib.util
import json
import os
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest

from common.conditional_source_image import BoxSourceImage, SourceImageError, phi
from obsstat.mes_r7_source_image import load_frozen, conditional_report, write_report, LABELS


@pytest.fixture(scope='module')
def source():
    return Path(os.environ['MES_R7_SOURCE'])


@pytest.fixture(scope='module')
def loaded(source):
    return load_frozen(source)


@pytest.fixture(scope='module')
def consumer(source,tmp_path_factory):
    # Actual consumer, root-cover depth tests the same enclosure without repeating
    # the separately recorded 64-node production replay.
    out=tmp_path_factory.mktemp('consumer')/'new_result'
    report=write_report(source,out,cover_depth=0)
    on_disk=json.loads((out/'result.json').read_text())
    assert on_disk['status']==report['status']=='CONDITIONAL_SCENARIO'
    return on_disk


def test_origin_units_and_shared_state(loaded):
    image,intake,embedding,fixture,contract=loaded
    assert np.array_equal(image.velocity(np.zeros(4)),image.v0)
    assert image.realization(np.zeros(4)).feature_vector==(0.,)*5
    assert len(intake.row_ids)==525 and len(set(intake.source_ids))==418
    assert intake.law_kind=='SCENARIO_ONLY' and intake.covariance_source is None
    x=np.array([.1,-.2,.3,-.4]);state=image.realization(x)
    assert np.allclose(state.feature_vector,-image.L@np.log1p(-image.A@x),rtol=0,atol=1e-15)
    assert np.array_equal(embedding.split(state.delta_theta)[0],state.delta_theta)


@pytest.mark.parametrize('name,value,code',[
    ('L',np.zeros((4,525)),'UNSUPPORTED_SHAPE'),
    ('G',np.zeros((525,3)),'UNSUPPORTED_SHAPE'),
    ('z',np.ones(524),'UNSUPPORTED_SHAPE'),
    ('v0',np.full(525,np.nan),'NONFINITE_INPUT'),
    ('halfwidth',np.full(4,np.inf),'NONFINITE_INPUT'),
    ('parameter_units',('km/s',)*4,'UNIT_MISMATCH'),
    ('velocity_frame','ICRS','FRAME_MISMATCH'),
    ('feature_frame','GALACTIC','FRAME_MISMATCH'),
    ('domain','ELLIPSOID','UNSUPPORTED_DOMAIN'),
    ('halfwidth',-np.ones(4),'INVALID_DOMAIN')])
def test_rejected_contracts(loaded,name,value,code):
    with pytest.raises(SourceImageError,match=code):replace(loaded[0],**{name:value})


def test_rows_and_nonfinite_xi(loaded):
    image=loaded[0]
    with pytest.raises(SourceImageError,match='ROW_ORDER_MISMATCH'):
        replace(image,row_ids=image.row_ids[::-1])
    for x in [np.ones((14,4)),np.ones(5),[np.nan,0,0,0],[1.00001,0,0,0]]:
        with pytest.raises(SourceImageError):image.realization(x)
    with pytest.raises(ValueError):image.L[0,0]=1


def test_zero_width_and_small_log1p(loaded):
    image=replace(loaded[0],halfwidth=np.zeros(4))
    assert image.realization([1,-1,.5,.3]).feature_vector==(0.,)*5
    rows,_=image.support(np.eye(5)[:1],['zero'],cover_depth=0)
    assert rows[0]['coherent_nonlinear_feasible_lower']==0
    assert 0<=rows[0]['coherent_nonlinear_certified_upper']<1e-300
    t=1e-18
    assert phi(np.ones((1,1)),np.ones((1,1)),np.array([t]))[0]>0
    assert phi(np.ones((1,1)),np.ones((1,1)),np.array([t]))[0]==pytest.approx(t,rel=1e-15,abs=0)


def test_whole_box_log_and_redshift_boundaries(loaded):
    im=loaded[0];z=np.ones(525);v=np.zeros(525);g=np.zeros((525,4));g[0,0]=299792.458
    for multiplier in [1,1.01]:
        with pytest.raises(SourceImageError,match='LOG_DOMAIN_ERROR'):
            replace(im,z=z,v0=v,G=g*multiplier,halfwidth=np.ones(4))
    with pytest.raises(SourceImageError,match='LOG_DOMAIN_ERROR'):
        replace(im,z=np.zeros(525),v0=v)
    # Positive log denominator does not license a nonpositive redshift factor.
    with pytest.raises(SourceImageError,match='REDSHIFT_DOMAIN_ERROR'):
        replace(im,z=z,v0=np.full(525,-299792.458),G=np.zeros((525,4)))


def test_real_consumer_bracket_witness_and_original_checks(source,loaded,consumer):
    im,_,_,fx,_=loaded
    assert consumer['unresolved_inputs']['empirical_MES_D']=='HOLD_NOT_COMPUTED'
    assert consumer['ellipsoid']=='UNSUPPORTED_DOMAIN'
    assert len(consumer['support_results'])==14
    for r in consumer['support_results']:
        state=im.realization(r['feasible_witness_xi'])
        np.testing.assert_allclose(state.feature_vector,r['feasible_feature_vector'],atol=1e-15,rtol=0)
        val=np.dot(r['direction_coefficients'],state.feature_vector)
        assert r['coherent_nonlinear_feasible_lower']<=val+1e-15
        assert val<=r['coherent_nonlinear_certified_upper']+1e-15
        assert r['certificate_gap']>=0
    spec=importlib.util.spec_from_file_location('r7_original',source/'verification/coherent_calibration.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    original.phi=phi  # Original assertions unchanged, now exercising the new kernel.
    result=original.checks(im.L,im.A,fx['directions'],consumer['support_results'],fx['basis'],im.G,im.z,im.v0,fx['ngal'])
    assert result['status']=='PASS'
    for r in consumer['support_results'][-2:]:
        assert r['coherent_nonlinear_feasible_lower']>0
    assert np.linalg.norm(fx['B'].T@fx['left_null'])<1e-16


def test_row_box_and_coherent_nonconvex_counterexample():
    a=.3;L=np.eye(2);A=np.array([[1.],[-1.]])
    ends=[phi(L,A,np.array([x])) for x in [-a,a]]
    midpoint=sum(ends)/2
    assert np.all(midpoint>0)
    assert np.array_equal(phi(L,A,np.array([0.])),[0,0])
    # Independent row intervals give an exact translated rectangle (zonotope).
    center=-.5*np.log1p(-a*a)*np.ones(2);width=np.arctanh(a)
    assert np.all(midpoint>=center-width) and np.all(midpoint<=center+width)
    # Equality of the two coherent coordinates forces xi=0, so midpoint is not an image point.
    assert np.allclose(midpoint,center)


def test_complete_rotation_and_residual_composition(loaded):
    im,_,_,fx,_=loaded;rng=np.random.default_rng(11)
    Q,_=np.linalg.qr(rng.normal(size=(3,3)))
    if np.linalg.det(Q)<0:Q[:,0]*=-1
    basis=fx['basis'];O=np.einsum('aij,ik,bkl,jl->ab',basis,Q,basis,Q)
    xi=np.array([.2,-.3,.1,.4]);q=phi(im.L,im.A,xi);u=fx['directions'][0]
    rotated=phi(O@im.L,im.A,xi)
    np.testing.assert_allclose(rotated,O@q,rtol=0,atol=1e-15)
    assert np.dot(O@u,rotated)==pytest.approx(np.dot(u,q),abs=1e-15)
    assert np.linalg.norm(rotated)==pytest.approx(np.linalg.norm(q),abs=1e-15)
    # Rotate n and the physical bulk/domain axes together: row response is invariant.
    nrot=fx['ngal']@Q.T
    np.testing.assert_allclose(nrot@Q,fx['ngal'],atol=1e-15,rtol=0)
    deltav=im.G@(im.halfwidth*xi);res=np.full(525,2.)
    total=-im.L@np.log1p(-(deltav+res)/im.d)
    sequential=phi(im.L,im.A,xi)-im.L@np.log1p(-res/(im.d-deltav))
    np.testing.assert_allclose(total,sequential,atol=1e-15,rtol=0)
    wrong=phi(im.L,im.A,xi)-im.L@np.log1p(-res/im.d)
    assert np.linalg.norm(total-wrong)>1e-10


@pytest.mark.parametrize('quantity',['empirical_MES_D','physical_shear','joint_confidence','native_solver','MES_anchor'])
def test_physical_request_refusal(source,quantity):
    r=conditional_report(source,request=quantity)
    assert r['status']=='INSUFFICIENT_PHYSICAL_INPUTS'
    assert 'support_results' not in r
    assert r['unresolved_inputs']['empirical_MES_D']=='HOLD_NOT_COMPUTED'


def test_output_collision_and_changed_input(source,tmp_path):
    existing=tmp_path/'existing';existing.mkdir();marker=existing/'keep';marker.write_text('unchanged')
    for out in [existing,tmp_path/'dangling']:
        if out!=existing:out.symlink_to(tmp_path/'absent')
        with pytest.raises(SourceImageError,match='OUTPUT_EXISTS'):
            write_report(source,out)
    assert marker.read_text()=='unchanged'
    fake=tmp_path/'source';(fake/'inputs').mkdir(parents=True)
    (fake/'inputs/FROZEN_CALIBRATION_INPUT.npz').write_bytes(b'changed')
    with pytest.raises(SourceImageError,match='SOURCE_IDENTITY_MISMATCH'):load_frozen(fake)
