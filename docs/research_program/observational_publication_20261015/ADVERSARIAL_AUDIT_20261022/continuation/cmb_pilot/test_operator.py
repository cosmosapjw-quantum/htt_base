import importlib.util
from pathlib import Path
import sys
import healpy as hp
import numpy as np

s=importlib.util.spec_from_file_location('a22_operator',Path(__file__).with_name('operator.py'))
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)


def test_repacking_masks_linearity_and_physical_parity():
    w=m.windows();e=np.zeros(hp.Alm.getsize(8),complex);b=e.copy()
    e[hp.Alm.getidx(8,2,0)]=1;e[hp.Alm.getidx(8,6,1)]=.4+.2j
    b[hp.Alm.getidx(8,3,1)]=-.3+.1j;b[hp.Alm.getidx(8,8,2)]=.2-.3j
    ep=m.repack(e,8,12);bp=m.repack(b,8,12)
    for ww in w.values():
        a=m.transform(e,b,8,ww);extended=m.transform(ep,bp,12,ww)
        np.testing.assert_allclose(a,extended,rtol=0,atol=1e-12)
        eo=m.transform(e,b*0,8,ww);bo=m.transform(e*0,b,8,ww)
        assert m.normalized_residual(a-eo-bo,a,e,b)<1e-10
        p=m.transform(m.parity(e,8),m.parity(b,8,True),8,ww)
        expected=np.array([m.parity(a[0],4),m.parity(a[1],4,True)])
        assert m.normalized_residual(p-expected,a,e,b)<1e-10
    high=np.zeros_like(e);high[hp.Alm.getidx(8,6,1)]=1
    cut=m.transform(high,high*0,8,w[20]);unwindowed=m.transform(high,high*0,8,w[0])
    assert np.linalg.norm(cut-unwindowed)>1e-3


def test_B_parity_must_differ_and_bad_schema_fails():
    import pytest
    e=np.zeros(hp.Alm.getsize(8),complex);b=e.copy();b[hp.Alm.getidx(8,3,1)]=1+2j
    w=m.windows()[20];base=m.transform(e,b,8,w)
    wrong=m.transform(m.parity(e,8),m.parity(b,8),8,w)
    expected=np.array([m.parity(base[0],4),m.parity(base[1],4,True)])
    assert np.linalg.norm(wrong-expected)>1e-3
    with pytest.raises(ValueError):m.transform(e,b[:-1],8,w)
    b[0]=1
    with pytest.raises(ValueError):m.transform(e,b,8,w)
