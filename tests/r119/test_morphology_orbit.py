import json
from pathlib import Path
import numpy as np
import pytest
from common.morphology_orbit import rotation_factory, profile_bounds

def real_sky():
    rng=np.random.default_rng(72);a=np.zeros((77,3),complex)
    for l in range(2,9):
        a[l*l-4+l]=rng.normal(size=3)
        for m in range(1,l+1):
            z=rng.normal(size=3)+1j*rng.normal(size=3)
            a[l*l-4+l+m]=z
            a[l*l-4+l-m]=(-1)**m*z.conj()
    return a

def test_rotation_identity_z_axis_and_inverse():
    a=real_sky();rot=rotation_factory(2,8)
    np.testing.assert_allclose(rot(a,(0,0,0)),a,atol=1e-13)
    alpha=.41;m=np.concatenate([np.arange(-l,l+1) for l in range(2,9)])
    np.testing.assert_allclose(rot(a,(alpha,0,0)),np.exp(-1j*alpha*m[:,None])*a,atol=1e-13)
    x=rot(a,(.2,1.4,-.6));y=rot(x,(.6,-1.4,-.2))
    np.testing.assert_allclose(y,a,atol=1e-13)
    for l in range(2,9):
        v=x[l*l-4:(l+1)**2-4];u=a[l*l-4:(l+1)**2-4]
        np.testing.assert_allclose(v[::-1],((-1.)**np.arange(-l,l+1))[:,None]*v.conj(),atol=1e-13)
        np.testing.assert_allclose(v.conj().T@v,u.conj().T@u,rtol=1e-13,atol=1e-12)

def test_sampled_bounds_scale_symmetry_nested():
    a=real_sky();b=rotation_factory(2,8)(a,(.1,.3,.5))
    data=np.array([a,3*a,b,-a])
    lo,identity,upper=profile_bounds(data,2,8,samples=(16,64))
    assert np.allclose(identity,identity.T) and np.allclose(lo,lo.T)
    assert np.all(upper[64]<=upper[16]+1e-12)
    assert np.all(upper[16]<=identity+1e-12) and np.all(lo<=upper[64]+2e-7)
    assert identity[0,1]<1e-7
    assert identity[0,3]==1
    assert lo[0,2]<1e-7
    _,_,upper2=profile_bounds(data*np.array([2,.5,3,7])[:,None,None],2,8,samples=(16,64))
    np.testing.assert_allclose(upper[64],upper2[64],atol=1e-7)

def test_zero_and_bad_inputs_rejected():
    with pytest.raises(ValueError,match="zero"):
        profile_bounds(np.zeros((1,77,3)),2,8)
    with pytest.raises(ValueError):
        profile_bounds(np.ones((1,77,2)),2,8)
    with pytest.raises(ValueError):
        profile_bounds(np.ones((1,77,3)),2,8,samples=(64,16))

def test_native_evidence_brackets():
    root=Path(__file__).resolve().parents[2]
    path=root/"docs/research_program/observational_publication_20261015/R119_NATIVE_CLASSIFICATION_INTAKE_20261128/C8.json"
    d=json.loads(path.read_text());assert len(d["pairs"])==66
    assert len({tuple(p["pair"]) for p in d["pairs"]})==66
    for p in d["pairs"]:
        assert 0<=p["lower"]<=p["upper_256"]+2e-7
        assert p["upper_256"]<=p["upper_64"]+1e-12<=p["identity_upper"]+2e-12
    assert d["max_pair_upper_h24_h32_change"]<1e-8
