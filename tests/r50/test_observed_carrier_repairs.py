"""Scientific regressions for R50, using no external catalogue paths."""
import numpy as np
import pytest
from scipy.linalg import null_space

from htt.htt.infer.gaussian_carrier_benchmark import (
    linear_compression_information, log_likelihood_ratio, profile_normal_carrier,
)
from htt.htt.infer.r49_general_bianchi_likelihood import (
    compute_r49_htt_five_views_from_posterior, compute_scalar_xc_ablation_comparison,
)
from bass.transport.general_bianchi_transfer import (
    TiltedTransferParameters, compute_general_bianchi_transfer,
)


def test_profile_matches_direct_weighted_residual_with_correlated_noise():
    rng = np.random.default_rng(501)
    X, y = rng.normal(size=(19, 6)), rng.normal(size=19)
    Z = rng.normal(size=(19, 19)); C = Z@Z.T+np.eye(19)
    L = np.linalg.cholesky(C); Xw=np.linalg.solve(L,X); yw=np.linalg.solve(L,y)
    G, b = Xw.T@Xw, Xw.T@yw
    J,N = np.eye(6)[:,:3],np.eye(6)[:,3:]
    F,t,mean,cov=profile_normal_carrier(G,b,J,N)
    def residual(theta):
        r=yw-Xw@J@theta
        eta=np.linalg.lstsq(Xw@N,r,rcond=None)[0]
        return np.linalg.norm(r-Xw@N@eta)**2
    for theta in rng.normal(size=(8,3)):
        assert log_likelihood_ratio(F,t,theta,np.zeros(3)) == pytest.approx(-.5*(residual(theta)-residual(np.zeros(3))),abs=2e-12)
    np.testing.assert_allclose(F@cov,np.eye(3),atol=2e-12)
    np.testing.assert_allclose(F@mean,t,atol=2e-12)


def test_invertible_tensor_chart_ties_full_score_but_scalar_has_blind_directions():
    F=np.array([[4.,1.,.2],[1.,2.,.3],[.2,.3,1.]])
    B=np.array([[1.,2.,0.],[0.,1.,1.],[1.,0.,1.]])
    np.testing.assert_allclose(linear_compression_information(F,B),F,atol=2e-12)
    scalar=np.array([[1.,0.,0.]])
    FI=linear_compression_information(F,scalar)
    v=null_space(scalar)[:,0]
    assert v@FI@v == pytest.approx(0,abs=1e-14)
    assert v@F@v > 0


@pytest.mark.parametrize("bad", [np.diag([1.,0.]),np.array([[1.,2.],[2.,1.]])])
def test_singular_or_indefinite_law_rejected_without_jitter(bad):
    with pytest.raises((ValueError,np.linalg.LinAlgError)):
        profile_normal_carrier(bad,np.zeros(2),np.eye(2),np.zeros((2,0)))


def test_unqualified_quadrupole_velocity_null_rejected():
    with pytest.raises(ValueError,match="Unqualified beta null"):
        compute_r49_htt_five_views_from_posterior(np.zeros((20,24)),matched_null_samples_beta=np.zeros((300,3)))


def test_missing_null_never_generates_random_matched_samples(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("random null fallback was invoked")
    monkeypatch.setattr(np.random,"RandomState",forbidden)
    result=compute_r49_htt_five_views_from_posterior(np.zeros((20,24)),
        shell_redshift_bins=[(.01,.02),(.02,.03)],
        shell_data_vectors=[np.zeros(3),np.zeros(3)],cross_shell_data_cov=np.eye(6))
    assert set(result["Pi_exceedance"]) == {"BETA_MO_NORM"}
    assert result["velocity_null_status"].startswith("UNAVAILABLE")
    shear=result["five_variable_state"].support_profiles_F["SHEAR_SIGMA"]
    assert shear.anchor_support_values is None and shear.occupancy_ratios is None


def test_dimension_count_not_information_loss_and_rank_not_jittered():
    draws=np.zeros((20,24));draws[:,17]=np.linspace(-.001,.001,20)
    out=compute_scalar_xc_ablation_comparison(draws)
    assert out["full_covariance_rank"] == 1
    assert out["information_loss_ratio_dof"] is None
    assert out["coordinate_reduction_fraction"] == pytest.approx(13/14)
    assert compute_scalar_xc_ablation_comparison(np.zeros((20,24)))["full_covariance_rank"] == 0


@pytest.mark.parametrize("family",["V","VII_0","VII_h","IX"])
def test_exact_abelian_boundary_has_no_family_label_morphology(family):
    kw=dict(sigma_N=np.diag([1e-5,-5e-6,-5e-6]),a_vec=np.zeros(3),
        n_mat=np.zeros((3,3)),omega_k=0.,ell_max=4,n_gl_theta=12)
    reference=compute_general_bianchi_transfer(TiltedTransferParameters(family="I",**kw))
    candidate=compute_general_bianchi_transfer(TiltedTransferParameters(family=family,**kw))
    for key in ["cosmo_T_map","cosmo_Q_map","cosmo_U_map"]:
        np.testing.assert_allclose(getattr(candidate,key),getattr(reference,key),rtol=1e-12,atol=1e-16)
