import numpy as np
import pytest
from common.morphology_conditioning import signed_split,amplitude_shape,scaled_diagnostic,spin2_support
from common.morphology_manifold import generators,quotient_metric
from common.morphology_orbit import rotation_factory
from scripts.r121.plan import make

def real_sky():
    r=np.random.default_rng(121);a=np.zeros((77,3),complex)
    for l in range(2,9):
        c=l*l-4+l;a[c]=r.normal(size=3)
        for m in range(1,l+1):
            z=r.normal(size=3)+1j*r.normal(size=3);a[c+m]=z;a[c-m]=(-1)**m*z.conj()
    return a

def test_signed_split_exact():
    a=real_sky();b=.02*a;c=.001*a
    z,o,e=signed_split(a+b+c,a,a-b+c)
    np.testing.assert_allclose(o,b,atol=1e-15)
    np.testing.assert_allclose(e,c,atol=1e-15)
    np.testing.assert_allclose(z+o+e,a+b+c)

def test_absolute_shape_identity_and_rotation():
    a=real_sky();g=generators(a,2,8);rng=np.random.default_rng(121)
    d=np.array([a,g[0],rng.normal(size=a.shape),rng.normal(size=a.shape)*1j])
    q=amplitude_shape(a,d);old=quotient_metric(a,d,2,8)
    np.testing.assert_allclose(q["shape_gram"],old["gram"],atol=1e-13)
    assert np.linalg.norm(q["shape_projected"][:,:2])<1e-13
    assert np.isclose(q["grad_log_amplitude"][0],1)
    np.testing.assert_allclose(q["absolute_gram"],q["amplitude"]**2*(q["shape_gram"]+np.outer(q["grad_log_amplitude"],q["grad_log_amplitude"])),atol=1e-10)
    rot=rotation_factory(2,8);q2=amplitude_shape(rot(a,(.2,.8,-.5)),rot(d,(.2,.8,-.5)))
    np.testing.assert_allclose(q2["absolute_gram"],q["absolute_gram"],atol=1e-10)
    np.testing.assert_allclose(q2["shape_gram"],q["shape_gram"],atol=1e-13)

def test_floor_and_stabilizer():
    a=np.zeros((77,3),complex);a[2,0]=1
    q=amplitude_shape(a,np.array([a]))
    assert q["rotation_rank"]==2
    with pytest.raises(ValueError,match="floor"):amplitude_shape(a*1e-15,np.array([a]),floor=1e-12)

def test_scaled_column_bound():
    a=np.diag([1.,1000.,.01]);b=a+np.diag([.001,1.,.0001])
    q=scaled_diagnostic(a,{"time":b},[1,.001,1])
    np.testing.assert_allclose(q["singular_values"],[1,1,.01])
    assert q["count_above_observed_scale"]==3
    assert q["errors"]["time"]["scaled_operator"]<=q["errors"]["time"]["scaled_frobenius"]
    with pytest.raises(ValueError):scaled_diagnostic(a,{},[1,0,1])

def test_spin2_support_axis():
    a=np.zeros((77,3),complex);a[0,0]=1+2j;a[4,0]=a[0,0].conjugate()
    rot=rotation_factory(2,8);b=rot(a,(0,np.pi/2,0))
    assert spin2_support(b)["relative_off_m2"]<1e-14

def test_plan():
    x=make();assert len(x["base"])==26 and len(x["fine"])==20
    assert len({p["name"] for p in x["points"]})==len(x["points"])
