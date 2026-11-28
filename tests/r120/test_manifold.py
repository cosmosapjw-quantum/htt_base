import json
from pathlib import Path
import numpy as np
import pytest
from common.morphology_manifold import initial_geometry, lie_text, generators, quotient_metric, central_derivative, realify
from common.morphology_orbit import rotation_factory
from scripts.r120.plan_grid import make
from scripts.r120.ricci_probe import direct
from scripts.r120.native_scan import DOC, sources

POINTS={p["name"]:p for p in make()["points"]}

def sky():
    rng=np.random.default_rng(120);a=np.zeros((77,3),complex)
    for l in range(2,9):
        start=l*l-4+l;a[start]=rng.normal(size=3)
        for m in range(1,l+1):
            z=rng.normal(size=3)+1j*rng.normal(size=3)
            a[start+m]=z;a[start-m]=(-1)**m*z.conj()
    return a

def test_plan_and_gauss_surface():
    x=make();assert x==json.loads((DOC/"SCAN_PLAN.json").read_text())
    assert len(POINTS)==63 and len(x["fine_time"])==24 and len(x["fine_angular"])==4
    for name,p in POINTS.items():
        g=initial_geometry(p,0)
        assert g["omega_E"]>0 and g["jacobi_norm"]==0 and np.linalg.norm(g["required_flux_over_E"])<1
        assert len(lie_text(p,0).splitlines())==3
        n=p["N6"];a=p["A3"][0]
        if n[0]==0 and n[3:]==[0,0,0]:
            np.testing.assert_allclose(g["K"],-np.trace(direct(n[1],n[2],a))/6,atol=1e-15)
    assert initial_geometry(POINTS["VIh"],0)["K"]>initial_geometry(POINTS["VIIh"],0)["K"]
    assert POINTS["VIstar_k001"]["params"]["h"]==pytest.approx(-1/9)

@pytest.mark.parametrize("key,value",[("N6",[1,.01,-.01,0,0,0]),("shear6",[1,1,1,0,0,0]),("A3",[float("nan"),0,0]),("A3",[2,0,0])])
def test_reject_invalid_point(key,value):
    p=dict(POINTS["VIh"]);p[key]=value
    with pytest.raises(ValueError):initial_geometry(p,0)

def test_generators_and_realification():
    a=sky();g=generators(a,2,8);rot=rotation_factory(2,8);h=1e-6
    for i in (1,2):
        plus=(0,h,0) if i==1 else (h,0,0)
        minus=(0,-h,0) if i==1 else (-h,0,0)
        np.testing.assert_allclose(g[i],central_derivative(rot(a,minus),rot(a,plus),h),atol=2e-8,rtol=2e-8)
    # Rotation and amplitude tangent are distinct real directions.
    for z in g:assert abs(np.dot(realify(a),realify(z)))<1e-11

def test_quotient_annihilates_nuisance_and_covariance():
    a=sky();g=generators(a,2,8)
    result=quotient_metric(a,np.array([a,*g]),2,8)
    assert result["nuisance_rank"]==4 and np.max(result["singular_values"])<2e-14
    rng=np.random.default_rng(1)
    d=np.array([a+2*g[1]+rng.normal(size=a.shape),g[2]+1j*rng.normal(size=a.shape)])
    q=quotient_metric(a,d,2,8)
    rot=rotation_factory(2,8)
    qr=quotient_metric(rot(a,(.3,.7,-.1)),rot(d,(.3,.7,-.1)),2,8)
    np.testing.assert_allclose(q["gram"],qr["gram"],rtol=1e-12,atol=1e-12)
    assert q["nuisance_residual"]<1e-13
    assert np.linalg.eigvalsh(q["gram"]).min()>0

def test_stabilizer_rank():
    a=np.zeros((77,3),complex);a[2,0]=1
    q=quotient_metric(a,np.array([a]),2,8)
    assert q["nuisance_rank"]==3

def test_fd_and_zero_input():
    for h in (.04,.02):
        np.testing.assert_allclose(central_derivative(np.array([(1-h)**3]),np.array([(1+h)**3]),h),[3+h*h])
    with pytest.raises(ValueError,match="zero"):quotient_metric(np.zeros((77,3)),np.zeros((1,77,3)),2,8)
    with pytest.raises(ValueError):central_derivative([0],[1],0)

def test_bad_source_missing(tmp_path):
    with pytest.raises(FileNotFoundError):sources(tmp_path)
