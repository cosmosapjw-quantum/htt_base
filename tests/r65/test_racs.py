"""Falsifying checks for posterior weights, units, frame and projection semantics."""
import io
import json
import zipfile
import numpy as np
import pytest
import yaml

try:
    from htt.htt.infer import r65_racs as r
except ImportError:
    import r65_racs as r


def tiny_csv(weights=(1,3,0)):
    return (',,observer_speed,dipole_longitude,dipole_latitude,temp_beta,lambda_clus,logL\n'
            'labels,,D,phi,theta,beta,lclus,logL\n'
            ',weights,,,,,,\n'+
            '\n'.join(f'{i},{w},{s},0,0,{t},1,-999999' for i,(w,s,t) in enumerate(zip(weights,[1,3,100],[0,.04,.02])))+'\n').encode()


def test_known_nonuniform_measure_and_zero_mass_extreme():
    cols,w,meta=r.read_posterior_csv(tiny_csv())
    mean,cov=r.weighted_moments(cols['observer_speed'],w)
    assert mean[0] == 2.5
    assert cov[0,0] == .75
    assert meta['n_zero_weights']==1
    assert r.weighted_quantile(cols['observer_speed'],w,[.025,.5,.975]).tolist()==[1,3,3]
    out=r.summarize_posterior(cols,w)
    # The equal-weight answer would be104/3 and is intentionally very different.
    assert out['scalar_summaries']['speed_ratio']['mean']==2.5
    assert np.isclose(out['weight_concentration_ess'],1.6)
    assert np.isclose(np.trace(out['covariance_velocity_icrs_km2_s2']),.75*r.SPEED_KM_S**2)


@pytest.mark.parametrize('weights', [(-1,2,0),(0,0,0),(1,float('nan'),0),(1,float('inf'),0)])
def test_invalid_original_weights_rejected(weights):
    with pytest.raises(ValueError): r.read_posterior_csv(tiny_csv(weights))


def test_latitude_domain_and_header_rejected():
    with pytest.raises(ValueError):r.read_posterior_csv(tiny_csv().replace(b',weights',b',logweights'))
    with pytest.raises(ValueError):r.read_posterior_csv(tiny_csv().replace(b'1,3,3,0,0,',b'1,3,3,0,91,'))


def test_galactic_north_pole_independent_oracle():
    # IAU Galactic N pole in ICRS (J2000), independent angular reference.
    v=r.galactic_to_icrs_vectors([0,250],[90,90],[1,1])
    ra,dec=np.deg2rad([192.85948,27.12825])
    expected=np.array([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)])
    np.testing.assert_allclose(v,[expected,expected],atol=2e-7)


def test_cmb_projected_ratio_normalization_and_rotation():
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    sky=SkyCoord(ra=167.942*u.deg,dec=-6.944*u.deg,frame='icrs').galactic
    cols={'observer_speed':np.array([1.,2.]),'dipole_longitude':np.repeat(sky.l.deg,2),'dipole_latitude':np.repeat(sky.b.deg,2)}
    out=r.summarize_posterior(cols,[.25,.75])
    np.testing.assert_allclose(out['scalar_summaries']['transverse_parallel_ratio_to_cmb']['mean'],1.75,atol=1e-12)
    np.testing.assert_allclose(out['scalar_summaries']['transverse_perpendicular_km_s']['mean'],0,atol=1e-10)
    with pytest.raises(ValueError):r.summarize_posterior(cols,[1,1],cmb_dec_deg=90)


def child_fixture(*, corrupt_csv=False):
    exp='test_experiment'
    config={'experiment_id':exp,'args':{'observer_speed_min':0.,'observer_speed_max':12.}}
    data={'posterior/final-posterior.csv':tiny_csv(),'provenance/model_config.json':b'{}','configs/experiment.yaml':yaml.safe_dump(config).encode()}
    manifest={'format_version':3,'experiment_id':exp,'source':{'repository':r.SOURCE_REPOSITORY,'commit':r.SOURCE_COMMIT,'dirty':False,'reproducible':True},
              'files':[{'archive_path':n,'size':len(v),'sha256':r.sha256(v)} for n,v in data.items()]}
    if corrupt_csv:data['posterior/final-posterior.csv']=data['posterior/final-posterior.csv'].replace(b'-999999',b'-888888')
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for n,v in data.items():z.writestr(n,v)
        z.writestr('artifact-manifest.yaml',yaml.safe_dump(manifest))
    raw=b.getvalue();h=r.sha256(raw)
    return raw,f'{exp}.{h}.analysis.zip',h,exp


def test_nested_artifact_member_mutation_is_detected():
    raw,name,h,exp=child_fixture()
    cols,w,meta=r.read_child_archive(raw,name,expected_hash=h,experiment_id=exp)
    assert w.tolist()==[.25,.75,0]
    assert meta['artifact_manifest']['source']['dirty'] is False
    raw,name,h,exp=child_fixture(corrupt_csv=True)
    with pytest.raises(ValueError,match='member identity mismatch'):
        r.read_child_archive(raw,name,expected_hash=h,experiment_id=exp)
    with pytest.raises(ValueError,match='SHA256'):
        r.read_child_archive(raw,name,expected_hash='0'*64,experiment_id=exp)
