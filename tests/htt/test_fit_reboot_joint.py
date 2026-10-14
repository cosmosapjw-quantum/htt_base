from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

REPO = Path(os.environ.get('HTT_REBOOT_SOURCE_ROOT', Path(__file__).resolve().parents[2]))
CANDIDATE = Path(os.environ.get('HTT_REBOOT_CODE_ROOT', REPO))
os.environ['HTT_REBOOT_SOURCE_ROOT'] = str(REPO)
os.environ['HTT_REBOOT_CODE_ROOT'] = str(CANDIDATE)
import sys
sys.path.insert(0, str(REPO/'htt'))
sys.path.insert(0, str(REPO/'htt/src'))
import htt.infer
if CANDIDATE != REPO:
    adapter_spec = importlib.util.spec_from_file_location(
        'htt.infer.conditional_legacy_pushforward',
        CANDIDATE/'htt/htt/htt/infer/conditional_legacy_pushforward.py')
    adapter_mod = importlib.util.module_from_spec(adapter_spec)
    sys.modules[adapter_spec.name] = adapter_mod
    adapter_spec.loader.exec_module(adapter_mod)
spec = importlib.util.spec_from_file_location('fit_reboot_joint', CANDIDATE/'scripts/fit_reboot_joint.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
from htt.infer.conditional_legacy_pushforward import PosteriorDrawSource, posterior_distance_image


def test_source_binding_and_duplicate_q_refusal(tmp_path):
    data = mod.load_inputs()
    assert len(data['z']) == 22
    assert data['desi_source_id'] == mod.EXPECTED_DESI_SOURCE
    payload = json.loads(mod.DESI.read_text())
    payload['observed'].append(payload['observed'][0])
    bad = tmp_path/'bad.json'
    bad.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='conditioning'):
        mod.load_inputs(desi=bad)


def test_joint_marginals_spd_and_rho_factorization():
    d = mod.load_inputs()
    for rho in mod.RHO:
        c, w = mod.covariance(d, rho)
        np.testing.assert_allclose(c[:-1, :-1], np.linalg.inv(d['precision']))
        assert c[-1, -1] == d['variance']
        assert np.min(np.linalg.eigvalsh(c)) > 0
        assert abs(w @ d['precision'] @ w - 1) < 1e-11
    t = mod.table(16, d)
    f0 = mod.fit_grid(d, t, 0.)
    f5 = mod.fit_grid(d, t, .5)
    assert not np.allclose(f0['ll'], f5['ll'])
    ru = d['mu'] - t['s'][3] - 43
    rq = d['q'] - t['qshape'][3]/t['ar'][8]
    cmu = np.linalg.inv(d['precision']) + 25*np.ones((22,22))
    separate = (-0.5*(ru @ np.linalg.solve(cmu, ru) +
                      np.linalg.slogdet(cmu)[1] + 22*np.log(2*np.pi))
                + norm.logpdf(rq, scale=np.sqrt(d['variance'])))
    assert f0['ll'][3,8] == pytest.approx(separate, abs=2e-10)
    assert f0['weights'].sum() == pytest.approx(1., abs=2e-12)


def test_analytic_M_integral_matches_numeric():
    d = mod.load_inputs()
    t = mod.table(16, d)
    f = mod.fit_grid(d, t, .25)
    i, j = 5, 7
    y = np.r_[d['mu'], d['q']]
    base = np.r_[t['s'][i], t['qshape'][i]/t['ar'][j]]
    ci = np.linalg.inv(f['c'])
    logdet = np.linalg.slogdet(f['c'])[1]
    def density(m):
        r = y-base-np.r_[np.ones(22),0]*m
        return np.exp(-.5*(r @ ci @ r + logdet + 23*np.log(2*np.pi)) + norm.logpdf(m,43,5))
    scale = f['ll'][i,j]
    val = quad(lambda m: density(m)*np.exp(-scale), 25, 60, epsrel=1e-10)[0]
    assert val == pytest.approx(1., rel=2e-8)


def test_distance_image_same_measure_and_unknown_physical_mass():
    source = PosteriorDrawSource('p','u|d','law','prior',('a','b'),(.3,.7),
                                 'FLAT_LCDM_DISTANCE','DISTANCE_ONLY')
    om=np.array([.25,.35]); ar=np.array([9000.,12000.]); z=np.array([.2,.8])
    source=replace(source,distance_state_sha256=mod.distance_state_digest(source,om,ar,z,mod.radial(om,z)))
    image=posterior_distance_image(source,om,ar,redshift=z,radial_integral=mod.radial(om,z))
    assert image['draw_ids'] == source.draw_ids and image['weights'] == source.weights
    np.testing.assert_allclose(image['H0_DL_over_c'],(1+z)**2*image['H0_DA_over_c'])
    assert image['physical_sector']['Sigma2']['unknown_mass'] == 1
    assert image['physical_sector']['Q']['status'] == 'UNAVAILABLE'
    with pytest.raises(ValueError, match='binding|aligned'):
        posterior_distance_image(source,om[::-1],ar,redshift=z,radial_integral=np.zeros((2,2)))


def test_vectorized_radial_matches_existing_response():
    from htt.infer.r7_desi_law import flat_lcdm_qiso
    d = mod.load_inputs()
    for om, ar in ((.1,8000.),(.3,12000.),(.8,18000.)):
        i = mod.radial([om],[d['zeff']])[0,0]
        e=np.sqrt(om*(1+d['zeff'])**3+1-om)
        q=mod.C_LIGHT/ar/d['fid']*np.cbrt(d['zeff']*i*i/e)
        assert q == pytest.approx(flat_lcdm_qiso(om,ar,zeff=d['zeff'],dv_over_rd_fid=d['fid']),rel=1e-12)


def test_distance_binding_model_pairing_and_finite_output_guards():
    base=PosteriorDrawSource('p','u|d','law','prior',('a','b'),(.3,.7),'FLAT_LCDM_DISTANCE','DISTANCE_ONLY')
    om=np.array([.25,.35]);ar=np.array([9000.,12000.]);z=np.array([.2,.8]);integ=mod.radial(om,z)
    source=replace(base,distance_state_sha256=mod.distance_state_digest(base,om,ar,z,integ))
    with pytest.raises(ValueError,match='binding'):
        posterior_distance_image(source,om[::-1],ar,redshift=z,radial_integral=integ)
    wrong=replace(base,distance_state_sha256=mod.distance_state_digest(base,om[::-1],ar,z,integ))
    with pytest.raises(ValueError,match='pairing'):
        posterior_distance_image(wrong,om[::-1],ar,redshift=z,radial_integral=integ)
    tiny=np.array([1e-320,12000.]);bound=replace(base,distance_state_sha256=mod.distance_state_digest(base,om,tiny,z,integ))
    with pytest.raises(ValueError,match='nonfinite'):
        posterior_distance_image(bound,om,tiny,redshift=z,radial_integral=integ)
    with pytest.raises(ValueError,match='real'):
        posterior_distance_image(source,om+1j,ar,redshift=z,radial_integral=integ)
