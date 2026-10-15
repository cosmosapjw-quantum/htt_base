"""Three-source HTT legacy -> modern STF -> actual Planck tensor bridge tests."""
import hashlib
import importlib.util
from pathlib import Path
import numpy as np
import pytest

from obsstat.legacy_teff_tensor_observation_bridge import (
    TeffTensorBridgeError,
    legacy_f4_exact_increment,bolometric_proxy_shift_microK,
    masked_planck_quadrupole_to_temperature_stf,
    real_l1_microK_to_temperature_dipole,
    quadrupole_morphology_stf,
    old_axis_A_W_Q_V_to_tensors,
    real_harmonic_quadrupole_source_consistency
)
from obsstat.r7_cmb_product_response import real_design
from obsstat.mes_eps_measurement_bridge import T0_MICROK

HERE=Path(__file__).resolve().parents[2]
LEGACY=HERE/"docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015/inputs/original_legacy_teff_extended.py"
LEGACY_SHA="39593691b86d5af1fb1ea2e7e02a9798a589b968d23d088288ed6d3b83aebf53"


def old_map():
    assert hashlib.sha256(LEGACY.read_bytes()).hexdigest()==LEGACY_SHA
    spec=importlib.util.spec_from_file_location("original_legacy_archive_teff_immutable",LEGACY)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TeffMomentMap(N_theta=24,N_phi=32)


def test_actually_archived_legacy_awqv_quadrature_matches_exact_invariants():
    old=old_map()
    for A,W,Q,V in (
        (.1,.03,.04,.02),(.15,-.13,.11,-.09),
        (.02,.01,-.05,.06),(0.,0.,.1,0.)):
        d,s=old_axis_A_W_Q_V_to_tensors(A,W,Q,V)
        out=legacy_f4_exact_increment(d,s,require_positive=True)
        q=old.moment(A,W,Q,V,alpha=4)
        assert float(out["F4"])==pytest.approx(q,rel=0,abs=2.5e-14)
        # Original legacy quadrature's sigma2_analytic matches our m2.
        assert float(out["mean_t2"])==pytest.approx(
            old.sigma2_analytic(A,W,Q,V),rel=0,abs=2e-14)


def test_wolfram_exact_axisymmetric_A_Q_formula_and_no_cancellation():
    a=.1;q=1/7
    d,s=old_axis_A_W_Q_V_to_tensors(a,0.,q,0.)
    x=legacy_f4_exact_increment(d,s)
    rational=(2*a*a+6*q*q/5+8*a*a*q/5+8*q**3/35+
              a**4/5+22*a*a*q*q/35+3*q**4/35)
    assert x["delta_F4"]==pytest.approx(rational,rel=1e-14)
    assert x["F4"]==pytest.approx(1+rational,rel=2e-15)
    xsmall=legacy_f4_exact_increment(np.zeros(3),np.diag([1e-7,-1e-7,0.]))
    delta=xsmall["delta_F4"]
    assert delta>0
    assert bolometric_proxy_shift_microK(delta)>0
    assert (1+delta)-1!=0  # at 1e-7 example not below machine resolution


def test_f4_invariant_under_simultaneous_SO3_rotation_of_d_and_S():
    rng=np.random.default_rng(3)
    a=rng.normal(size=(3,3))
    R,_=np.linalg.qr(a)
    if np.linalg.det(R)<0:R[:,0]*=-1
    d=rng.normal(size=3)*.07
    s=rng.normal(size=(3,3));s=(s+s.T)/2
    s-=np.eye(3)*np.trace(s)/3
    s*=.035
    first=legacy_f4_exact_increment(d,s,require_positive=True)
    second=legacy_f4_exact_increment(R@d,R@s@R.T,require_positive=True)
    for k in ("delta_F4","mean_t2","mean_t3","mean_t4","J2","J3","K1","K2"):
        assert first[k]==pytest.approx(second[k],rel=1e-12,abs=1e-14)


def test_batched_three_contributions_and_zero_case():
    rng=np.random.default_rng(19)
    d=rng.normal(size=(13,3))*.1
    s=rng.normal(size=(13,3,3));s=(s+np.transpose(s,(0,2,1)))/2
    s-=np.trace(s,axis1=1,axis2=2)[:,None,None]/3*np.eye(3)
    s*=.03
    batch=legacy_f4_exact_increment(d,s,require_positive=True)
    assert batch["delta_F4"].shape==(13,)
    for i in range(13):
        one=legacy_f4_exact_increment(d[i],s[i],require_positive=True)
        for k in ("delta_F4","J3","K2"):
            assert batch[k][i]==pytest.approx(one[k],abs=3e-15)
    zero=legacy_f4_exact_increment(np.zeros(3),np.zeros((3,3)))
    assert zero["delta_F4"]==0
    assert bolometric_proxy_shift_microK(zero["delta_F4"])==0


def test_planck_real_harmonic_l2_to_modern_stf_and_variance_identity():
    rng=np.random.default_rng(61)
    a=rng.normal(size=5)*19.
    s=masked_planck_quadrupole_to_temperature_stf(a)
    assert real_harmonic_quadrupole_source_consistency(a)<5e-20
    out=legacy_f4_exact_increment(np.zeros(3),s)
    # Orthonormal real Y_lm full-sky integral:
    expected=np.dot(a,a)/(4*np.pi*T0_MICROK**2)
    assert out["mean_t2"]==pytest.approx(expected,rel=1e-14)
    assert np.trace(s)==pytest.approx(0,abs=1e-18)
    assert -1.000000000001<=quadrupole_morphology_stf(s)<=1.000000000001


def test_intrinsic_l1_vector_adapter_is_separate_not_inferred_from_map():
    coeff=np.asarray([9.,-3.,5.])
    d=real_l1_microK_to_temperature_dipole(coeff)
    rng=np.random.default_rng(8)
    n=rng.normal(size=(100,3));n/=np.linalg.norm(n,axis=1)[:,None]
    mapped=n@d
    designed=(real_design(n,ell_max=1)[:,1:4]@coeff)/T0_MICROK
    np.testing.assert_allclose(mapped,designed,atol=5e-21)


def test_positive_temperature_domain_and_trace_guard():
    s=np.diag([1.,-1.,0.])
    with pytest.raises(TeffTensorBridgeError,match="positivity"):
        legacy_f4_exact_increment(np.zeros(3),s,require_positive=True)
    with pytest.raises(TeffTensorBridgeError,match="trace"):
        legacy_f4_exact_increment(np.zeros(3),np.eye(3))
    with pytest.raises(TeffTensorBridgeError):
        legacy_f4_exact_increment(np.zeros(4),np.zeros((3,3)))
    with pytest.raises(TeffTensorBridgeError):
        masked_planck_quadrupole_to_temperature_stf(np.ones(7))
    with pytest.raises(TeffTensorBridgeError):
        bolometric_proxy_shift_microK(-1.)
