"""Focused falsifiers for the R36-07 actual consumer and claim boundary."""
import importlib.util
import math
from pathlib import Path
import numpy as np

SOURCE=Path(__file__).with_name('compute.py')
spec=importlib.util.spec_from_file_location('foreground_budget_compute',SOURCE)
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


def test_spin_weights_match_complex_pixel_sum():
    import healpy as hp
    m=c.load_spin_math()
    nside=8
    ring=np.asarray([9,37,210,502])
    q=np.asarray([.4,-.7,.3,.9])*1e-6
    u=np.asarray([-.2,.8,.1,-.5])*1e-6
    wq,wu=c.coordinate_weights(ring,nside,hp,m)
    direct=wq@q+wu@u
    qmap=np.zeros(12*nside*nside);umap=np.zeros_like(qmap)
    qmap[ring]=q;umap[ring]=u
    e,b,*_=m.independent_low_sum(qmap,umap,nside,hp,chunk=29)
    expected=m.canonical_grid(e,b)
    np.testing.assert_allclose(direct,expected,rtol=1e-12,atol=1e-20)


def test_cauchy_schwarz_scalar_completion_is_sharp():
    # Two native blocks with correlated scalar latent noise attain the sum.
    covs=[np.asarray([[2.,.3],[.3,1.]]),np.asarray([[.8,-.2],[-.2,3.]])]
    weights=[np.asarray([.4,-.6]),np.asarray([-.2,.7])]
    sig=[math.sqrt(float(w@v@w)) for w,v in zip(weights,covs)]
    common=np.asarray([[sig[0]**2,sig[0]*sig[1]],
                       [sig[0]*sig[1],sig[1]**2]])
    assert np.linalg.eigvalsh(common).min()>-1e-14
    assert abs(np.ones(2)@common@np.ones(2)-sum(sig)**2)<1e-14


def test_complex_cancellation_does_not_bound_total_variation():
    intensity=np.asarray([1.,1.])
    polarization=np.asarray([1.+0j,-1.+0j])
    assert np.all(np.abs(polarization)<=intensity)
    assert abs(np.sum(polarization))==0
    assert np.sum(np.abs(polarization))==2
    # Opposite phases need not cancel after distinct spectral responses.
    assert abs(np.dot(np.asarray([1.,1.2]),polarization))>.1


def test_total_variation_taylor_remainder_and_uncovered_positive_atom():
    # Exact two-emitter complex/signed mixture. A zero reference polarization
    # does not make a third-order remainder vanish.
    weights=np.asarray([1.+0j,-1.+0j])
    delta=np.asarray([.2,-.2])
    exact=np.dot(weights,np.exp(delta))
    second=np.dot(weights,1+delta+delta**2/2)
    bound=np.sum(np.abs(weights))*math.exp(.2)*(.2**3)/6
    assert 0<abs(exact-second)<bound
    # A positive source atom invisible to every supplied response but seen by
    # the target has no finite positive-dual domination certificate.
    source_response=np.asarray([[1.,0.]])
    target_response=np.asarray([1.,1.])
    assert source_response[0,1]==0<target_response[1]


def test_actual_compensators_and_radius_monotonicity():
    import json
    g=json.loads((c.OUT/'GEOMETRY.json').read_text())
    residual=[x['reconstruction_Frobenius_K_CMB'] for x in g['compensators']]
    assert max(residual)<2e-14
    assert g['compensators'][-1]['budget_K_CMB']>g['compensators'][0]['budget_K_CMB']
    radii=[x['s_ball_radius_K_CMB'] for x in g['conditional_curves']]
    assert np.all(np.diff(radii)>=0)
    assert all(x['scope'].startswith('CONDITIONAL_') for x in g['conditional_curves'])
