import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest

sp=importlib.util.spec_from_file_location('sn_refit',Path(__file__).with_name('refit.py'))
m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)


def test_source_identity_join_overrides_and_calibration_primary():
    rows,meta,summary,overrides=m.read_inputs();e=m.Experiment()
    assert len(rows)==59 and summary['CID']=='010010' and int(summary['IDSURVEY'])==15
    assert overrides['HOSTGAL_LOGMASS']==9.50285
    for band,b in e.bands.items():
        # The SALT-only .27 offset must NOT be applied to this calibration probe.
        assert abs(e.primary_probe(band)/10**(.4*(27.5-b['primary_mag']))-1)<1e-14
    assert m.CFG['MW']['raw_EBV']*m.CFG['MW']['scale']==.017544


def test_spectral_units_paired_transport_MW_and_extrapolation():
    e=m.Experiment();theta=np.array([.3,np.log(.0004),.8,.01]);t=np.array([-5.,0.,8.]);bands=np.array(['g','r','i']);z=.0984
    for delta in (.99,.999,1.001,1.01):
        tp=t/delta;zp=(1+z)/delta-1
        transformed=e.predict(theta,delta*tp,bands,z,mw_lambda=delta,spectral_lambda=delta,boost=delta**3)
        expected=theta.copy();expected[0]/=delta;expected[1]+=2*np.log(delta)
        covariant=e.predict(expected,tp,bands,zp,mw_lambda=delta)
        np.testing.assert_allclose(covariant,transformed,rtol=1e-11,atol=1e-11)
    cov=e.predict(expected,tp,bands,zp,mw_lambda=delta)
    frozen=e.predict(expected,tp,bands,zp,mw_lambda=1)
    assert np.max(abs(cov/frozen-1))>1e-5
    with pytest.raises(ValueError):e.predict(theta,np.array([100.]),np.array(['g']),z)
    with pytest.raises(ValueError):e.predict(theta,t,bands,z,spectral_lambda=4)


def test_relative_epoch_and_quadrature_refinement():
    e=m.Experiment(.5);f=m.Experiment(.25);theta=np.array([0.,np.log(.000394269),.9091,.010397])
    times=np.array([-10.,0,10]);bands=np.array(['g','r','i'])
    a=e.predict(theta,times,bands,.0984);b=f.predict(theta,times,bands,.0984)
    assert np.max(abs(a/b-1))<1e-6
    assert (m.CFG['T_ref_MJD']+(times/m.CFG['deltas'][-1])-m.CFG['T_ref_MJD']).max()<11
