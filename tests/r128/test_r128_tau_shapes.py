import numpy as np
import pytest
from common.physical_memory_budget import build_context
from common.opacity_memory_kernel import NodalWindows,solve_state
from common.fixed_tau_shapes import source_metrics,constrained_basis,balanced_pair,visibility,integrate_direction

def setup(m=0):
    inp=dict(anchors={"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13},f_nu=.4,f_b=.157,table=np.array([[0.,1.],[.1,.8],[.2,.6],[.3,.4],[.4,.2],[.5,.1]]),c_sigma=2e-20,k0=.1,a0=0.,m=m,L=8)
    c=build_context(**inp);w=NodalWindows(inp["table"],[0,1,2,3,4,4])
    return inp,c,w
def test_depth_metric_and_null():
    inp,c,w=setup();q=source_metrics(c,w)
    np.testing.assert_allclose(q["M_tau"]@np.ones(5),q["t"]/q["tau"],atol=1e-14)
    np.testing.assert_allclose(q["nodal"].sum(),q["tau"],atol=1e-14)
    for active in ([0,1,2,3,4],[0,1,2,3],[2,3]):
        B=constrained_basis(q["M_tau"],q["t"],active)
        np.testing.assert_allclose(B.T@q["M_tau"]@B,np.eye(len(active)-1),atol=1e-12)
        np.testing.assert_allclose(q["t"]@B,0,atol=1e-12)
        assert np.all(B[np.setdiff1d(np.arange(5),active)]==0)
    v=balanced_pair(q["t"],1,0)
    np.testing.assert_allclose(q["t"]@v,0,atol=1e-14)
def test_visibility_and_fixed_tau_B():
    inp,c,w=setup();q=source_metrics(c,w);v=balanced_pair(q["t"],1,0)
    a=visibility(c,w);tab=w.perturb(.1*v);c2=build_context(**dict(inp,table=tab));w2=NodalWindows(tab,w.groups);b=visibility(c2,w2)
    np.testing.assert_allclose(a["tau"],b["tau"],rtol=1e-13)
    np.testing.assert_allclose(a["mass"],-np.expm1(-a["tau"]),rtol=1e-12)
    np.testing.assert_allclose(b["mass"],a["mass"],rtol=1e-12)
    assert abs(b["mean_eta"]-a["mean_eta"])>1e-6
    s=c["system"];y=s["basis"][:,s["labels"].index("B")]
    r=integrate_direction(c,w,v[w.groups],y,rtol=1e-10)
    assert np.linalg.norm(r["tangent"])<1e-9
    y2=solve_state(c2,y,rtol=1e-10)["end"]
    np.testing.assert_allclose(y2,r["end"],atol=1e-10,rtol=1e-8)
def test_arbitrary_nodal_direction():
    inp,c,w=setup(1);q=source_metrics(c,w);v=np.linspace(-.5,.7,len(w.table));v-=q["nodal"]@v/q["tau"]
    y=c["system"]["basis"][:,0];r=integrate_direction(c,w,v,y,rtol=1e-10);ends=[]
    for sign in (-1,1):
        tab=w.table.copy();tab[:,1]*=1+sign*.001*v
        cp=build_context(**dict(inp,table=tab));ends.append(solve_state(cp,y,rtol=1e-11)["end"])
    np.testing.assert_allclose((ends[1]-ends[0])/.002,r["tangent"],rtol=1e-4,atol=1e-8)
