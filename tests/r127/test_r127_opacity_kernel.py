import numpy as np
import pytest
from common.physical_memory_budget import build_context,observation
from common.opacity_memory_kernel import NodalWindows,integrate_windows,goal_kernel,solve_state

def params(m=0,a0=0.):
    return dict(anchors={"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13},f_nu=.4,f_b=.157,table=np.array([[0.,1.],[.2,.6],[.5,.3]]),c_sigma=2e-20,k0=.1,a0=a0,m=m,L=8)

def test_exact_relative_interpolation():
    p=params();win=NodalWindows(p["table"],[0,1,2]);a=np.array([.1,-.2,.03,0.,0.]);t=np.linspace(0,.5,77)
    np.testing.assert_allclose(win.ratios(t).sum(axis=1),1,atol=1e-15)
    actual=np.interp(t,win.table[:,0],win.perturb(a)[:,1])
    expected=np.interp(t,win.table[:,0],win.table[:,1])*(1+win.ratios(t)@a)
    np.testing.assert_allclose(actual,expected,atol=1e-15)
    with pytest.raises(ValueError):win.perturb([-2,0,0,0,0])

def test_exact_B_and_zero_opacity():
    p=params();c=build_context(**p);w=NodalWindows(p["table"],[0,1,2])
    s=c["system"];j=s["labels"].index("B");r=integrate_windows(c,w,s["basis"][:,[j]],rtol=1e-10)
    np.testing.assert_allclose(r["tangent"][:,:,0],-r["end"][:,0][None,:]*r["tau"][:,None],atol=1e-11,rtol=1e-8)
    p["table"][:,1]=0;c=build_context(**p);w=NodalWindows(p["table"],[0,1,2])
    r=integrate_windows(c,w,c["system"]["basis"][:,[0]],rtol=1e-10)
    assert np.max(abs(r["tangent"]))==0

@pytest.mark.parametrize("m",[0,1,2])
def test_adjoint_and_fd(m):
    p=params(m,.05);c=build_context(**p);w=NodalWindows(p["table"],[0,1,2])
    s=c["system"];v=np.linspace(-.2,.3,len(s["labels"]));y=s["basis"]@v
    r=integrate_windows(c,w,y[:,None],rtol=1e-10);k=goal_kernel(c,w,y,rtol=1e-10)
    z=observation(c)@r["end"][:,0];dz=observation(c)@r["tangent"][:,:,0].T
    g=np.stack([np.real(z[i::3].conj()@dz[i::3]) for i in range(3)])
    np.testing.assert_allclose(k["group_gradient"],g,atol=1e-9,rtol=2e-6)
    np.testing.assert_allclose(k["knot_gradient"].sum(axis=1),g.sum(axis=1),atol=1e-9)
    e=np.zeros(5);e[1]=1e-3;ends=[]
    for sign in (-1,1):
        cp=build_context(**dict(p,table=w.perturb(sign*e)))
        ends.append(solve_state(cp,y,rtol=1e-11)["end"])
    np.testing.assert_allclose((ends[1]-ends[0])/(2e-3),r["tangent"][1,:,0],rtol=1e-4,atol=1e-8)
