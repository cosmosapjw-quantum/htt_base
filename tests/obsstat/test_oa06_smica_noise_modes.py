"""The observation and noise samples use the same selected-sky operator."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from obsstat.r7_cmb_product_response import pixel_fit_geometry


SCRIPT=Path(__file__).resolve().parents[2]/'scripts/fit_cmb_smica_noise_modes.py'
spec=importlib.util.spec_from_file_location('oa06_noise',SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_masked_operator_injection_and_full_covariance():
    _,y=pixel_fit_geometry()
    rng=np.random.default_rng(606)
    coefficients=rng.normal(size=(80,36))
    noise=coefficients@y.T
    truth=np.zeros(36);truth[[4,13,35]]=[3.,-2.,1.]
    observed=y@truth
    mask=np.ones(49152)
    mask[::5]=0
    result=module.project(observed,noise,mask,y)
    np.testing.assert_allclose(result['observed_microK'],truth[4:],atol=1e-11)
    np.testing.assert_allclose(result['simulation_scatter_cov_microK2'],
                               np.cov(coefficients[:,4:].T),atol=1e-12)
    assert result['selected_pixels']==39321
    assert result['fit_rank']==36
    assert result['noise_eigen_min_microK2']>0


def test_incomplete_or_nonfinite_map_refused():
    _,y=pixel_fit_geometry()
    with pytest.raises(ValueError,match='NSIDE64'):
        module.project(np.zeros(49152),np.zeros((63,49152)),np.ones(49152),y)
    observation=np.zeros(49152);observation[0]=np.nan
    with pytest.raises(ValueError,match='finite common'):
        module.project(observation,np.zeros((64,49152)),np.ones(49152),y)


def test_selected_cache_must_match_source_gate(tmp_path):
    cache=tmp_path/'cache.npz'
    cache.write_bytes(b'fixture cache bytes')
    import hashlib
    gate={'cache_reproducibility_green':True,
          'cache_hash':'sha256:'+hashlib.sha256(cache.read_bytes()).hexdigest()}
    assert module.require_gated_cache(cache,gate)==gate['cache_hash']
    cache.write_bytes(b'changed cache bytes')
    with pytest.raises(ValueError,match='hash differs'):
        module.require_gated_cache(cache,gate)
