"""Source-gated and observed-result scoped tests. Real CF4 source, not mock publication likelihood."""
from pathlib import Path
import sys
import json
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import h03_tomography as H
from run_h03 import compute,discover_source

@pytest.fixture(scope='module')
def source_result():
 p=discover_source(); assert H.digest(p)==H.SOURCE_SHA256
 result,arrays=compute(p)
 return result,arrays

def test_source_identity_35970():
 s=H.source(discover_source())
 assert len(s.ids)==35970 and len(set(s.ids))==35970
 assert len(np.unique(s.method))==4

def test_actual_monopole_and_9d_tomography_source(source_result):
 data,_=source_result
 assert data['source_groups']==35970
 H01=[74.62934813010348,74.343818424135,72.5163329032,70.8102232782]
 for j,rec in enumerate(data['monopole_dipole_STF2_windows']):
  assert abs(rec['H01_monopole_only_formula']-H01[j])<5e-6
  assert np.isfinite(rec['theta9']).all()
  assert len(rec['theta9'])==9
  assert 0<rec['working_design_condition']<15
  assert abs(np.trace(rec['STF2_matrix_km_s_Mpc']))<1e-12

def test_actual_joint_window_covariance_is_not_independent(source_result):
 d,arrays=source_result
 C=arrays['joint_cov36x36'];R=arrays['joint_corr36x36']
 assert C.shape==(36,36) and R.shape==(36,36)
 assert np.linalg.eigvalsh(C).min()>0
 assert abs(R[0,9])>.6
 assert abs(R[9,18])>.45
 assert abs(R[18,27])>.3
 np.testing.assert_allclose(C,C.T,rtol=0,atol=2e-15)

def test_actual_group_family_and_12_patch_stresses(source_result):
 d,_=source_result
 s=d['source_method_family_delete_sensitivity'];p=d['fixed_ICRS_12_patch_delete_sensitivity']
 assert {x['family_excluded'] for x in s}==set(H.METHODS)
 assert len(p)==12 and sorted(x['ICRS_patch_id'] for x in p)==list(range(12))
 assert sum(x['excluded_groups'] for x in s)==35970
 assert sum(x['removed_groups'] for x in p)==35970
 assert all(len(x['windows'])==4 for x in s+p)

def test_source_digest_failclosed(tmp_path):
 p=discover_source();raw=p.read_bytes();t=tmp_path/'tampered.npz'
 t.write_bytes(raw+b'forged')
 with pytest.raises(ValueError,match='SHA256'):H.source(t)

def test_fixed_source_outputs_agree_with_committed_reference(source_result):
 from pathlib import Path
 import json
 actual=Path(__file__).resolve().parents[1]/'results'/'source_h03_v1'/'H03_SOURCE_TOMOGRAPHY.json'
 if not actual.is_file():
  actual=Path(__file__).resolve().parents[1]/'results'/'H03_SOURCE_TOMOGRAPHY.json'
 if not actual.is_file(): pytest.skip('published numerical reference absent, run source script first')
 committed=json.loads(actual.read_text())
 np.testing.assert_allclose([x['H0_working_km_s_Mpc'] for x in source_result[0]['monopole_dipole_STF2_windows']],
                            [x['H0_working_km_s_Mpc'] for x in committed['monopole_dipole_STF2_windows']],rtol=0,atol=1e-10)
 assert committed['source_SHA256']==H.SOURCE_SHA256
