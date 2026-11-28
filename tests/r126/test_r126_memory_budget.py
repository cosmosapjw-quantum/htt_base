import numpy as np
import pytest
from common.initial_data_response import observe_columns,response_matrix
from common.physical_memory_budget import build_context,metric_weights,collision_action,observation,integrate_budget,whiten,adjoint_objective

def params():
    return dict(anchors={"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13},f_nu=.4,f_b=.157,table=np.array([[0.,1.],[.25,.6],[.5,.3]]),c_sigma=2e-20,k0=.1,a0=.05)

@pytest.mark.parametrize("m",[0,1,2])
def test_collision_and_observation(m):
    c=build_context(**params(),m=m,L=8);s=c["system"];n=len(s["basis"])
    for t in (0.,.2,.5):
        eye=np.eye(n,dtype=complex);C=collision_action(c,t,eye)
        np.testing.assert_allclose(C,s["rhs"](t,eye)-c["zero"]["rhs"](t,eye),atol=2e-12,rtol=1e-12)
        w,dw=metric_weights(c,t);D=-(w[:,None]*C+C.conj().T*w[None,:])
        assert np.min(np.linalg.eigvalsh(D))>-1e-12
        if t==.2:
            np.testing.assert_allclose(dw,(metric_weights(c,t+1e-5)[0]-metric_weights(c,t-1e-5)[0])/2e-5,rtol=1e-7,atol=1e-9)
    y=s["basis"]
    for f in ("host","normal","radiation","spectator"):
        got=observation(c,f)@y;sky=observe_columns(y,s,f)
        # m=0 response_matrix retains zero rows for all m and appends imaginary rows.
        # Select the actual m=0 rows rather than slicing that flattened array.
        want=np.asarray([sky[l*l-1+l] for l in range(1,9)]).reshape(-1,y.shape[1]) if m==0 else response_matrix(sky,m)
        np.testing.assert_allclose(got,want,atol=1e-13,rtol=1e-13)
    wi,_=metric_weights(c,0.);M=y.conj().T@(wi[:,None]*y);H=whiten(M)
    np.testing.assert_allclose(H.conj().T@M@H,np.eye(H.shape[0]),atol=1e-12)

@pytest.mark.parametrize("m",[0,1,2])
def test_integrated_budget(m):
    c=build_context(**params(),m=m,L=8)
    for lam in (0.,1.):
        r=integrate_budget(c,lam,rtol=1e-10,max_step=.01)
        assert r["closure_relative"]<1e-8
        assert r["min_D_eigenvalue"]>-1e-10
        if lam==0:assert np.max(abs(r["D"]))==0

def test_scalar_B_exact_and_adjoint():
    p=params();p["a0"]=0.
    c=build_context(**p,m=0,L=8);r=integrate_budget(c,1.,rtol=1e-10)
    j=c["system"]["labels"].index("B")
    O=observation(c,"host")
    got=np.linalg.norm(O@r["endpoint"][:,j]);want=np.linalg.norm(O@r["initial"][:,j])*np.exp(-r["tau"])
    np.testing.assert_allclose(got,want,rtol=1e-7,atol=1e-12)
    w=np.linspace(-.2,.3,len(c["system"]["labels"]))
    a=adjoint_objective(c,1.,w,rtol=1e-10,widths=(.01,.003))
    assert a["duality_relative"]<1e-7
    assert a["fd"][1]["absolute_error"]<1e-5
