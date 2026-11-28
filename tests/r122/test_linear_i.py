import numpy as np
import pytest
from common.finite_start_bianchi_i import system_matrix, integrate_response, axial_sky

def anchors():
    return {"duration":1.,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13}
def test_collision_eigenvalues_and_source():
    a=system_matrix(0.,0.,0.,0.,1.)
    np.testing.assert_allclose(np.sort(np.linalg.eigvals(a[1:3,1:3]).real),[-1.,-.3])
    assert a[1,0]==-4 and a[3,0]==-4
    assert a[0,1]==a[0,3]==0
def test_collisionless_and_solver_crosscheck():
    tab=np.array([[0.,0.],[.5,0.],[1.,0.]])
    x=integrate_response(anchors(),.4,tab,2e-20,method="DOP853")
    y=integrate_response(anchors(),.4,tab,2e-20,method="Radau")
    np.testing.assert_allclose(x["endpoint"],y["endpoint"],rtol=1e-8,atol=1e-11)
    assert x["endpoint"][2]==0
    np.testing.assert_allclose(x["endpoint"][1],x["endpoint"][3])
    assert x["tau"]==0
def test_sky_normalization():
    x=axial_sky([1.,2.,3.,4.],.01)
    assert x.shape==(77,3)
    assert np.count_nonzero(x)==2
    np.testing.assert_allclose(x[2,:],.01*np.sqrt(4*np.pi/5)/4*np.array([2.,-3*np.sqrt(6),0.]))
def test_invalid_history():
    with pytest.raises(ValueError):integrate_response(anchors(),.4,np.array([[0.,1.],[.5,1.]]),2e-20)
