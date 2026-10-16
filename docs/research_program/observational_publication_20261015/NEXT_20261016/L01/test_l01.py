import numpy as np, pytest
from pathlib import Path
import l01_finite_response as r
ROOT=Path(__file__).resolve().parent.parent/'source/l01/source'
P=(ROOT/'baseline_response_matrices.npz',ROOT/'ell17_32_mask_response.npz',ROOT/'retained_common_support_coefficients.npz')

def test_locked_sources():
 a=r.diagnostics(P)
 assert a['shape']==[32,1053] and a['rank']==32 and a['nullity']==1021
 assert abs(a['spectral_norm']-2.4328695605629203)<2e-12

def test_fail_closed():
 with pytest.raises(ValueError,match='source'):r.response(P[2],P[1],P[0])

def test_power_bound_and_null():
 k,*_=r.response(*P)
 from scipy.linalg import svdvals
 s=svdvals(k)[0]
 rng=np.random.default_rng(21)
 for _ in range(25):
  h=rng.normal(size=1053); assert np.linalg.norm(k@h)<=s*np.linalg.norm(h)*(1+3e-13)

def test_source_processing_not_independent():
 k,t,n,eb,en=r.response(*P);assert t.shape[0]==9 and eb.shape[0]==8 and len(en)==8
 assert 'SMICA_noSZ_FULL' in n and 'SMICA_noSZ_FULL' not in en
