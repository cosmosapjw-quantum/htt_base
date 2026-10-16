import sys, importlib.util,hashlib
from pathlib import Path
import numpy as np
import pytest
src=Path(__file__).resolve().parents[1]/'src/planck_mask_gate.py'
s=importlib.util.spec_from_file_location('planck_mask_gate',src)
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)

def test_six_masks_exact_lock_count():
    assert len(m.LOCKED)==6
    assert {k.split('_')[-1] for k in m.LOCKED}=={'Int','Pol'}
    assert len(set(x[1] for x in m.LOCKED.values()))==6


def test_checksum_byte_lock(tmp_path):
    f=b'SIMPLE  ='+b' '*72+b'actual source bytes'
    name='test_mask.fits';q=tmp_path/'planck/PR3/masks'/name
    q.parent.mkdir(parents=True);q.write_bytes(f)
    lock={'common_Int':(name,hashlib.sha256(f).hexdigest())}
    out=m.verify_masks(tmp_path,locked=lock,expected_bytes=len(f))
    assert out['common_Int']['status']=='BYTES_REHASHED'
    q.write_bytes(f+b'changed')
    with pytest.raises(ValueError,match='length mismatch'):
        m.verify_masks(tmp_path,locked=lock,expected_bytes=len(f))


def test_six_finite_support_masks():
    k=list(m.LOCKED)
    arr={n:np.array([1.,1.,0.,0.,1.,1.,0.,1.]) for n in k}
    arr['HM_Int'][0]=0;arr['common_Pol'][1]=0;arr['OE_Pol'][7]=0
    r=m.support_masks(arr)
    assert r['fraction_by_map']['HM_Int']==.5
    assert r['joint']['all_six_intersection_fraction']==.25
    assert r['one_latent_sky'] is True


def test_invalid_masks_fail_closed():
    a={k:np.ones(12) for k in m.LOCKED}
    a['common_Pol'][0]=np.nan
    with pytest.raises(ValueError,match='finite'):m.support_masks(a)
    a['common_Pol'][0]=1.2
    with pytest.raises(ValueError,match='finite'):m.support_masks(a)
    a.pop('common_Pol')
    with pytest.raises(ValueError,match='six map'):m.support_masks(a)
