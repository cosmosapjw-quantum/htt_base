import numpy as np
import pytest
from scipy.integrate import quad
from htt_gate_precursors.selected_sources import (LatentNormal,SelectedMixture,
 normal_log_selection,wrong_fixed_parent_weight_density,gaussian_nuisance_projector)


def model():
    return SelectedMixture((LatentNormal(.6,-1.,.5),LatentNormal(.4,1.5,.5)),
                           'synthetic-parent-2types','synthetic-y>0-cut')


def test_selection_weighted_parent_law_and_integral():
    m=model(); p=m.selected_type_probabilities()
    assert 0<p[0]<.04 and .96<p[1]<1
    assert p.sum()==pytest.approx(1.,abs=1e-14)
    val=quad(m.density,0,9,epsabs=2e-11)[0]
    assert val==pytest.approx(1,abs=5e-12)


def test_wrong_mixture_is_other_law_not_unnormalized_likelihood():
    m=model();correct=m.density(.2)
    wrong=wrong_fixed_parent_weight_density(m,.2)
    assert abs(correct-wrong)>.01
    # Important subtlety: naive fixed-parent mixture of selected components ALSO
    # integrates to 1; normalization of entire density alone cannot detect it.
    assert quad(lambda y:wrong_fixed_parent_weight_density(m,y),0,9)[0]==pytest.approx(1,abs=1e-11)


def test_selected_posterior_type_is_parent_prob_times_admission_mass():
    m=model();c=m.components
    term=np.array([x.probability*np.exp(normal_log_selection(x.mean,x.sigma,m.low,m.high)) for x in c]);term/=term.sum()
    assert np.allclose(term,m.selected_type_probabilities(),atol=1e-14)


def test_tail_selection_logmass_remains_finite():
    v=normal_log_selection(0,1,8,9)
    assert np.isfinite(v) and v<-30
    assert v==pytest.approx(np.log(0.5*__import__('scipy').special.erfc(8/np.sqrt(2))
                                 -0.5*__import__('scipy').special.erfc(9/np.sqrt(2))),rel=1e-9)

@pytest.mark.parametrize('kwargs',[dict(sigma=-1),dict(low=1,high=1),dict(low=float('nan'))])
def test_reject_bad_selection(kwargs):
    with pytest.raises(ValueError):normal_log_selection(0,**({'sigma':1} | kwargs))


def test_invalid_source_id_fails_closed():
    with pytest.raises(ValueError):SelectedMixture((LatentNormal(1,0,1),),'','sel')


def test_unconstrained_method_zero_point_makes_common_monopole_unidentified():
    rng=np.random.default_rng(8);n=120;group=rng.integers(0,4,size=n)
    Z=np.eye(4)[group];F=np.column_stack([np.ones(n),rng.normal(size=n)])
    A,s,r=gaussian_nuisance_projector(F,Z,np.eye(n))
    assert r==4
    assert np.linalg.norm(A[:,0])<1e-12
    assert np.linalg.norm(A[:,1])>1


def test_proper_calibration_prior_restores_positive_conditioned_information():
    # A source-specified proper covariance prior Lambda creates finite precision,
    # but does not constitute observational identification without that prior.
    rng=np.random.default_rng(55);n=70;Z=np.eye(4)[rng.integers(0,4,size=n)]
    q=np.ones(n);C=np.eye(n)*.5
    x=q@np.linalg.solve(C+Z@np.diag(np.full(4,.3))@Z.T,q)
    assert x>0
    A,_,_=gaussian_nuisance_projector(q[:,None],Z,C)
    assert np.linalg.norm(A)<1e-12


def test_joint_selected_common_latent_reweights_prior_by_product_Z():
    from htt_gate_precursors.selected_sources import SharedSelectedLatent
    shared=SharedSelectedLatent(model())
    q=shared.posterior_common_latent_after_N_admissions(2)
    assert q[0]<.001 and q[1]>.999
    assert q.sum()==pytest.approx(1)
    ys=np.array([.2,.3])
    correct=np.exp(shared.joint_log_density(ys))
    wrong=shared.wrong_held_parent_joint_density(ys)
    assert correct>0 and wrong>0 and abs(correct-wrong)>.1


def test_source_joint_selected_likelihood_is_normalized_over_Rplus2():
    from htt_gate_precursors.selected_sources import SharedSelectedLatent
    shared=SharedSelectedLatent(model())
    # 2D integral normalized to 1; use scipy quad nesting on bounded (0,9)^2
    from scipy.integrate import dblquad
    z=dblquad(lambda yy,xx:np.exp(shared.joint_log_density([xx,yy])),0,8,lambda x:0,lambda x:8,epsabs=1e-9)[0]
    assert z==pytest.approx(1,abs=1e-8)


def test_selection_normalization_changes_mu_score_sign():
    # mu=0,sigma=1,y=0.3, y>0. dlogP/dmu=.3-phi(0)/Phi(0).
    m=SelectedMixture((LatentNormal(1,0,1),),'parent','detector')
    h=1e-5;y=.3
    def logp(mu):
        return SelectedMixture((LatentNormal(1,mu,1),),'parent','detector').log_density(y)
    derivative=(logp(h)-logp(-h))/(2*h)
    assert derivative==pytest.approx(y-np.sqrt(2/np.pi),abs=1e-9)
    assert derivative<0<y
