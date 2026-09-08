import numpy as np
from scipy.linalg import null_space
from scipy.stats import beta
from obsstat.boost_response import quadrupole_boost_octupole,boost_response_metric
from scripts.observed_runs.rebuild_mes_tensor_carriers import harmonic_stf_matrices


def test_boost_adjoint_rank_fibre_and_ideal_scalar_law():
    q=np.diag([-2.,.5,1.5]);q/=np.linalg.norm(q)
    b=np.column_stack([quadrupole_boost_octupole(q,e).ravel() for e in np.eye(3)])
    np.testing.assert_allclose(b.T@b,3*boost_response_metric(q),rtol=1e-13,atol=1e-14)
    _,ob=harmonic_stf_matrices();ob=ob/np.sqrt(35/(8*np.pi))
    L=np.einsum('kabc,bc->ak',ob,q)
    np.testing.assert_allclose(L@L.T,boost_response_metric(q)/3,atol=2e-15)
    kernel=null_space(L);assert kernel.shape==(7,4)
    v=np.array([.02,.03,.01]);right=L.T@np.linalg.solve(L@L.T,v)
    for col in kernel.T:
        o=right+np.sqrt(1-right@right)*col
        np.testing.assert_allclose(L@o,v,atol=2e-15);assert abs(o@o-1)<1e-14
    x=np.linspace(0,1,31)
    np.testing.assert_allclose(beta.cdf(x,1.5,2),2.5*x**1.5-1.5*x**2.5,atol=2e-15)
    assert beta.mean(1.5,2)==3/7


def test_fixed_band_soft_mask_matrix_identity_and_norm_bound():
    # An exact finite-dimensional instance of the T5 Gram/inverse argument.
    # These rational E,A,C inputs are an operator oracle, not a pixel certificate.
    E=np.diag([.25,.5]);A=np.array([[1.,-2.],[.5,.25]]);C=np.array([[0.,1.]])
    def K(t):return -t*C@np.linalg.solve(np.eye(2)-t*E,A)
    np.testing.assert_array_equal(K(0),[[0.,0.]])
    h=2.**-20
    np.testing.assert_allclose((K(h)-K(-h))/(2*h),-C@A,atol=1e-12)
    for t in (1e-5,.001,.01):
        f=t/36;cL=36*np.linalg.norm(C,2)*np.linalg.norm(A,2)
        bound=cL*f/(1-36*f)
        assert np.linalg.norm(K(t),2)<=bound
        d=np.array([.1]);cost=np.linalg.norm(np.linalg.pinv(K(t))@d)**2
        assert cost>=np.linalg.norm(d)**2/bound**2
