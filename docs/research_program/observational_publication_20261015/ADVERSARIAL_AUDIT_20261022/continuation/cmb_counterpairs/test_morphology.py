import copy
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.spatial.transform import Rotation

s=importlib.util.spec_from_file_location('morphology',Path(__file__).with_name('morphology.py'))
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)


def fixture(seed=1):
    rng=np.random.default_rng(seed);a={}
    for l in (2,3,4):
        a[l,0]=complex(rng.normal())
        for k in range(1,l+1):
            z=complex(*rng.normal(size=2));a[l,k]=z;a[l,-k]=(-1)**k*z.conjugate()
    return a


def rotate(a,axis,angle):
    out={}
    for l in (2,3,4):
        ms=np.arange(-l,l+1);plus=np.zeros((2*l+1,2*l+1),complex)
        for k in range(2*l):plus[k+1,k]=np.sqrt(l*(l+1)-ms[k]*(ms[k]+1))
        lx=(plus+plus.T)/2;ly=(plus-plus.T)/(2j);lz=np.diag(ms)
        v=expm(-1j*angle*(axis[0]*lx+axis[1]*ly+axis[2]*lz))@np.array([a[l,k] for k in ms])
        out.update({(l,int(k)):z for k,z in zip(ms,v)})
    return out


def tensor(x):
    xx,xy,xz,yy,yz,zz=x
    return np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])


def test_donor_and_full_power_reality_controls():
    a=fixture()
    for factor,angle in ((m.Factor.PARITY,0),(m.Factor.PHASE,.37),(m.Factor.ORIENTATION,.41)):
        b=m.intervention(a,factor,angle);oracle=m.donor_intervention(a,factor,angle)
        assert b==oracle
        f,g=m.features(a),m.features(b)
        for l in (2,3,4):assert abs(f['C_ell_K_CMB2'][str(l)]/g['C_ell_K_CMB2'][str(l)]-1)<1e-12
    bad=dict(a);bad[2,-1]+=1e-3
    with pytest.raises(ValueError):m.features(bad)


def test_exact_nonzero_and_phase_witness():
    a={(l,k):0j for l in (2,3,4) for k in range(-l,l+1)}
    a[2,0]=1;a[3,1]=1;a[3,-1]=-1;a[4,1]=1j;a[4,-1]=1j
    assert abs(m.features(a)['J234']+np.sqrt(21)/42)<1e-14
    a={(l,k):0j for l in (2,3,4) for k in range(-l,l+1)}
    a[2,1]=1;a[2,-1]=-1;a[3,1]=1;a[3,-1]=-1;a[4,2]=1j;a[4,-2]=-1j
    assert abs(m.features(a)['J234']-np.sqrt(14)/84)<1e-14
    assert abs(m.features(m.intervention(a,'phase',.37))['J234']-np.sqrt(14)/84*np.cos(.74))<1e-14


def test_SO3_parity_tensor_and_abstention():
    axis=np.array([1,2,3])/np.sqrt(14);theta=.63;r=Rotation.from_rotvec(axis*theta).as_matrix()
    for seed in range(5):
        a=fixture(seed);f=m.features(a);g=m.features(rotate(a,axis,theta));p=m.features(m.intervention(a,'parity'))
        assert abs(f['J234']-g['J234'])<1e-12
        assert abs(f['alignment23_squared']-g['alignment23_squared'])<1e-12
        assert abs(f['J234']+p['J234'])<1e-12
        for key in ('tensor2','tensor3'):np.testing.assert_allclose(tensor(g[key]),r@tensor(f[key])@r.T,atol=1e-12,rtol=0)
    a=fixture();a.update({(2,k):complex(k==0) for k in range(-2,3)})
    f=m.features(a);assert f['alignment23_squared'] is None
    assert m.joint_score([f,m.features(fixture())]) is None


def test_whole_sky_identity_negative_and_schema():
    import json
    ex=json.loads((m.HERE/'EXPERIMENT.json').read_text());rows=[e for e in ex['products'] if e['lmax']==32]
    m.validate_link(rows)
    bad=copy.deepcopy(rows);bad[0]['underlying_sky_id']='another-sky-with-same-spectra'
    with pytest.raises(ValueError):m.validate_link(bad)
    bad=copy.deepcopy(rows);bad[0]['contract']['native_window_sha256']='other-window'
    with pytest.raises(ValueError):m.validate_link(bad)
    with pytest.raises(ValueError):m.validate_link(rows[:-1])
