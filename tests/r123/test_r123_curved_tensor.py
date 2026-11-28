import numpy as np
import pytest
from common.curved_tensor_response import angular_matrices,integrate_tensor,tensor_sky,F2
from common.finite_start_bianchi_i import integrate_response

def anchors():
    return {"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13}

def test_projection_identities():
    for h in (0,2,-2):
        G,A,M=angular_matrices(12,h)
        np.testing.assert_allclose(G,np.eye(11),atol=2e-12)
        np.testing.assert_allclose(M,M.T,atol=2e-12)
        np.testing.assert_allclose(A+A.T,2*M,atol=2e-12)
        np.testing.assert_allclose(M[0,0],-h/3,atol=2e-12)

def test_flat_i_limit_and_signed_reality():
    tab=np.array([[0.,1.],[.2,.5],[.5,.1]])
    t=integrate_tensor(anchors(),.4,tab,2e-20,0.,0.,6,rtol=1e-10)
    i=integrate_response(anchors(),.4,tab,2e-20,rtol=1e-10)
    s,a,b,v=i["endpoint"];x=t["endpoint"];n=5
    np.testing.assert_allclose([x[0],x[2]/F2,x[2+n]/(np.sqrt(6)*F2),x[2+3*n]/F2],[s,a,b,v],rtol=1e-7,atol=1e-9)
    y=tensor_sky(x,6,6)
    assert y.shape==(45,3)
    np.testing.assert_allclose(y[4],y[0].conjugate(),atol=1e-13)
    assert np.linalg.norm(y[:,2])<1e-12
    assert np.linalg.norm(y[5:])<1e-12

def test_twist_transports_and_mixes():
    tab=np.array([[0.,1.],[.5,1.]])
    t=integrate_tensor(anchors(),.4,tab,2e-20,.1,.05,6)
    x=tensor_sky(t["endpoint"],6,6)
    assert np.linalg.norm(x[:,2])>1e-6
    assert np.linalg.norm(x[5:])>1e-6
    for l in range(2,7):
        a=x[l*l-4:(l+1)**2-4]
        np.testing.assert_allclose(a[l+2],a[l-2].conjugate(),atol=1e-13)
        assert np.linalg.norm(np.delete(a,[l-2,l+2],axis=0))==0

def test_invalid_inputs():
    tab=np.array([[0.,1.],[.5,1.]])
    with pytest.raises(ValueError):integrate_tensor(anchors(),.4,tab,2e-20,0.,1.,4)
    with pytest.raises(ValueError):angular_matrices(4,1)
