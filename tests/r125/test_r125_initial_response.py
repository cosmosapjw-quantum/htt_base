import numpy as np
import pytest
from common.initial_data_response import build_system,integrate_columns,observe_columns,response_matrix
from common.codazzi_linear_response import integrate_sector,sector_sky
from common.curved_tensor_response import integrate_tensor,tensor_sky

def inputs():
    return dict(anchors={"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13},f_nu=.4,f_b=.157,table=np.array([[0.,1.],[.25,.6],[.5,.3]]),c_sigma=2e-20,k0=.1,a0=.05)

@pytest.mark.parametrize("m",[0,1,2])
def test_basis_and_prior_shear(m):
    p=inputs();sys=build_system(**p,m=m,L=8)
    y0=sys["basis"]
    assert y0.shape[1]==(6 if m==2 else 8)
    assert np.linalg.matrix_rank(y0)==y0.shape[1]
    assert np.max(abs(sys["constraint"](0.,y0)))<1e-14
    r=integrate_columns(sys,rtol=1e-10)
    x=observe_columns(r["endpoint"],sys,"host")
    if m<2:
        old=integrate_sector(**p,m=m,L=8,rtol=1e-10)
        ref=sector_sky(old["endpoint"],m,8,8,"host")
    else:
        p.pop("f_b");old=integrate_tensor(**p,L=8,rtol=1e-10)
        ref=np.vstack((np.zeros((3,3),complex),tensor_sky(old["endpoint"],8,8)))
    np.testing.assert_allclose(x[:, :,0],ref,rtol=2e-8,atol=1e-10)
    assert r["max_constraint"]<1e-10
    if m<2:assert np.linalg.norm(observe_columns(r["endpoint"],sys,"radiation")[:3])<1e-13
    M=response_matrix(x,m)
    np.testing.assert_allclose(np.linalg.norm(M,axis=0),np.linalg.norm(x,axis=(0,1)),atol=1e-12)

def test_scalar_pure_B_and_mixture():
    p=inputs();p["a0"]=0
    s=build_system(**p,m=0,L=8)
    r=integrate_columns(s,rtol=1e-10)
    x=observe_columns(r["endpoint"],s,"host")
    j=s["labels"].index("B")
    np.testing.assert_allclose(x[:,:,j][:,:2],0,atol=1e-13)
    assert np.linalg.norm(x[:,:,j])>0
    c=np.linspace(-.3,.4,len(s["labels"]))
    q=integrate_columns(s,(s["basis"]@c)[:,None],rtol=1e-10)
    np.testing.assert_allclose(q["endpoint"][:,0],r["endpoint"]@c,rtol=1e-7,atol=1e-10)
    with pytest.raises(ValueError):
        z=s["basis"][:,[0]].copy();z[1,0]+=1
        integrate_columns(s,z)

def test_metric_flat_contraction():
    p=inputs();p["k0"]=p["a0"]=0.
    s=build_system(**p,m=2,L=8)
    r=integrate_columns(s,rtol=1e-10)
    x=observe_columns(r["endpoint"],s,"host")
    assert np.linalg.norm(x[:,:,s["labels"].index("metric")])==0
