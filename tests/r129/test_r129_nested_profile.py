import numpy as np
import pytest
from common.physical_memory_budget import build_context,observation
from common.opacity_memory_kernel import NodalWindows
from common.fixed_tau_shapes import constrained_basis,source_metrics
from common.profiled_opacity_shapes import nested_groups,aggregation,NodalBasis,nodal_metric,integrate_nested,real_initial_map,real_shape_map,profile,unpack_ic

def setup(m=1):
    t=np.linspace(0,.5,25);tab=np.column_stack((t,1-t))
    g=np.repeat(np.arange(5),5)
    p=dict(anchors={"duration":.5,"dust_fraction":.7,"omega_lambda_emit":.1,"n_h_emit_m3":1e8,"h_emit_s":1e-13},f_nu=.4,f_b=.157,table=tab,c_sigma=2e-20,k0=.1,a0=.03,m=m,L=8)
    return build_context(**p),g,tab
def test_nested_metrics_and_aggregation():
    c,g,tab=setup();fine=nested_groups(g);w=NodalBasis(tab,fine);r=nodal_metric(c,w);old=source_metrics(c,NodalWindows(tab,g))
    E=aggregation(4)
    np.testing.assert_allclose(E.T@r["t"],old["t"][:4],atol=1e-13)
    np.testing.assert_allclose(E.T@r["M_tau"]@E,old["M_tau"][:4,:4],atol=1e-13)
    assert np.all(w.components[g==4]==0)
    B=constrained_basis(r["M_tau"],r["t"],list(range(16)))
    np.testing.assert_allclose(r["t"]@B,0,atol=1e-13)
    np.testing.assert_allclose(B.T@r["M_tau"]@B,np.eye(15),atol=1e-12)
def test_real_phase_and_profile():
    rng=np.random.default_rng(129);Z=rng.normal(size=(12,4))+1j*rng.normal(size=(12,4));v=rng.normal(size=4)+1j*rng.normal(size=4)
    R=real_initial_map(Z,1);np.testing.assert_allclose(R@np.r_[v.real,v.imag],real_shape_map((Z@v)[:,None])[:,0],atol=1e-13)
    np.testing.assert_array_equal(unpack_ic(np.r_[v.real,v.imag],1),v)
    S=rng.normal(size=(24,5));a=profile(R,S,1e-12)
    np.testing.assert_allclose(a["E"],S+R@a["C"],atol=1e-13)
    np.testing.assert_allclose(R.T@a["E"],0,atol=1e-12)
    np.testing.assert_allclose(a["P"]@a["P"],a["P"],atol=1e-13)
def test_new_tangent_reduces_to_old_windows():
    from common.opacity_memory_kernel import integrate_windows
    c,g,tab=setup(1);w=NodalBasis(tab,nested_groups(g));y=c["system"]["basis"][:,0]
    r=integrate_nested(c,w,y,rtol=1e-10);old=integrate_windows(c,NodalWindows(tab,g),y[:,None],rtol=1e-10)
    np.testing.assert_allclose(r["tangent"]@aggregation(4),old["tangent"][:4,:,0].T,rtol=1e-6,atol=1e-10)
    np.testing.assert_allclose(r["end"],old["end"][:,0],rtol=1e-8,atol=1e-10)
