import numpy as np
import pytest
from common.codazzi_linear_response import angular_matrices,integrate_sector,sector_sky,normalizations
from common.finite_start_bianchi_i import integrate_response

def anchors():
    return {"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13}
def test_general_spin_projection():
    for m in (0,1):
        for h in (0,2,-2):
            G,A,M=angular_matrices(12,m,h)
            np.testing.assert_allclose(G,np.eye(len(G)),atol=2e-12)
            np.testing.assert_allclose(A+A.T,2*M,atol=2e-12)
            np.testing.assert_allclose(M,M.T,atol=2e-12)
def test_flat_limit():
    tab=np.array([[0.,1.],[.2,.5],[.5,.1]])
    i=integrate_response(anchors(),.4,tab,2e-20,rtol=1e-10)
    for m in (0,1):
        r=integrate_sector(anchors(),.4,.157,tab,2e-20,0.,0.,m,6,rtol=1e-10)
        s,a,b,v=i["endpoint"];q=r["endpoint"];n=7-m;l=2-m;f2,_=normalizations(m)
        np.testing.assert_allclose([q[0],q[3+l]/f2,q[3+2*n]/(np.sqrt(6)*f2),q[3+n+l]/f2],[s,a,b,v],rtol=2e-8,atol=1e-10)
        assert np.linalg.norm(q[1:3])<1e-13
        sky=sector_sky(q,m,6,6,"normal")
        assert np.linalg.norm(sky[:,2])<1e-12
        assert np.linalg.norm(sky[8:])<1e-12
def test_codazzi_and_observer():
    tab=np.array([[0.,1.],[.25,.6],[.5,.3]])
    for m in (0,1):
        r=integrate_sector(anchors(),.4,.157,tab,2e-20,.1,.05,m,8,rtol=1e-10)
        q=r["endpoint"];y=sector_sky(q,m,8,8,"host");x=sector_sky(q,m,8,8,"normal")
        np.testing.assert_allclose(y[3:],x[3:],atol=0,rtol=0)
        _,g1=normalizations(m)
        np.testing.assert_allclose((y-x)[1+m,0],g1*q[1],rtol=1e-13,atol=1e-14)
        assert r["max_codazzi"]<1e-10
        if m==0:assert np.linalg.norm(x[:,2])<1e-12
        else:assert np.linalg.norm(x[:,2])>1e-7
def test_inputs():
    tab=np.array([[0.,1.],[.5,1.]])
    with pytest.raises(ValueError):integrate_sector(anchors(),.4,.157,tab,2e-20,.1,.05,2,8)
    with pytest.raises(ValueError):angular_matrices(5,0,1)
