"""Actual CF4 physical-response-gain unidentifiability, nuisance Schur tests."""
import numpy as np
import pytest

from obsstat.cf4_physical_transfer_identification import (
 CF4PhysicalBridgeError,KERNELS,declared_response_kernel,
 cf4_working_model,profile_declared_family,physical_gain_degeneracy,
 method_quadrupole_span_certificate,angular_axis_cosine
)
from obsstat.cf4_apparent_kinematic_distribution import (
 luminosity_distance_flat_lcdm
)


def mock(n=640,seed=60):
    rng=np.random.default_rng(seed)
    z=rng.uniform(.012,.095,n)
    v=rng.normal(size=(n,3))
    v/=np.linalg.norm(v,axis=1)[:,None]
    names=np.array(["FP","OTHER","SN","TF"])[np.arange(n)%4]
    rng.shuffle(names)
    dL,_,_=luminosity_distance_flat_lcdm(z)
    mu=25+5*np.log10(dL)
    err=np.full(n,.30)
    return z,v,names,mu,err


def test_radial_transfer_shapes_are_fixed_positive_and_not_physical():
    z=np.asarray([.02,.05,.08])
    a=declared_response_kernel(z,"unit_angular_endpoint")
    b=declared_response_kernel(z,"linear_z_over_0p05")
    c=declared_response_kernel(z,"reciprocal_0p05_over_z")
    d=declared_response_kernel(z,"early_late_1plusz")
    np.testing.assert_array_equal(a,[1,1,1])
    np.testing.assert_allclose(b,[.4,1,1.6])
    np.testing.assert_allclose(c,[2.5,1,.625])
    np.testing.assert_allclose(d,(1+z)/1.05)
    with pytest.raises(CF4PhysicalBridgeError):
        declared_response_kernel(z,"unknown_geometry")
    with pytest.raises(CF4PhysicalBridgeError):
        declared_response_kernel([0,.03],"unit_angular_endpoint")
    assert len(KERNELS)==4


def test_same_synthetic_source_injection_profiles_five_STF_modes_exactly():
    z,n,m,mu,e=mock()
    model=cf4_working_model(z,n,m,mu,e,kernel_name="linear_z_over_0p05")
    X=model["design"];s=model["STF_slice"]
    coeff=np.zeros(X.shape[1])
    coeff[s]=np.array([.012,-.02,.03,.005,-.015])
    coeff[0]=.06;coeff[1]=-.07
    model["residual"]=X@coeff
    p=profile_declared_family(model)
    np.testing.assert_allclose(p["gamma"],coeff[s],atol=7e-12)
    assert p["rank"]==5
    assert p["nuisance_rank"]==X.shape[1]-5
    assert np.linalg.eigvalsh(p["cov"]).min()>0
    assert np.all((p["relative_eigenvalues"]>0)&(p["relative_eigenvalues"]<=1+1e-10))


def test_scale_lambda_one_event_physical_response_degeneracy_exact():
    z,n,m,mu,e=mock()
    x=cf4_working_model(z,n,m,mu,e,kernel_name="unit_angular_endpoint")
    rng=np.random.default_rng(20)
    x["residual"]=rng.normal(size=len(z))*.3
    p=profile_declared_family(x)
    for gain in (.04,.37,3.,100.):
        amplified=cf4_working_model(z,n,m,mu,e,kernel_name="unit_angular_endpoint")
        amplified["design"][:,amplified["STF_slice"]]*=gain
        amplified["residual"]=x["residual"]
        fit=profile_declared_family(amplified)
        witness=physical_gain_degeneracy(p["gamma"],p["cov"],gain=gain)
        np.testing.assert_allclose(fit["gamma"],witness["conditional_gamma_for_gain"],
                                   atol=1e-11,rtol=1e-10)
        np.testing.assert_allclose(fit["cov"],witness["conditional_cov_for_gain"],
                                   atol=3e-10,rtol=1e-10)
        np.testing.assert_allclose(fit["relative_eigenvalues"],p["relative_eigenvalues"],
                                   rtol=2e-10,atol=1e-10)
    with pytest.raises(CF4PhysicalBridgeError):
        physical_gain_degeneracy(p["gamma"],p["cov"],gain=0)


def test_unrestricted_method_specific_quadrupole_exact_full_source_rank_zero():
    z,n,m,mu,e=mock(n=1200)
    f=declared_response_kernel(z,"linear_z_over_0p05")
    z=method_quadrupole_span_certificate(z,n,m,f)
    assert z["source_method_nuisance_rank"]==20
    assert z["global_STF_identified_rank_if_unrestricted_method_STF_allowed"]==0
    assert z["number_unidentified_global_STF_columns"]==5
    assert z["source_exact_B_minus_sum_Bm_maxabs"]<1e-15
    assert z["relative_projected_global_STF_norm"]<3e-14
    assert z["scope"].startswith("CONDITIONAL_COUNTEREXAMPLE")


def test_scalar_gain_preserves_conditional_STF_orientation_but_kernels_need_not():
    rng=np.random.default_rng(43)
    v=rng.normal(size=5)
    assert angular_axis_cosine(v,.003*v)==pytest.approx(1.,abs=1e-15)
    assert angular_axis_cosine(v,-v)==pytest.approx(-1.,abs=1e-15)
    with pytest.raises(CF4PhysicalBridgeError):
        angular_axis_cosine(np.zeros(5),v)
    with pytest.raises(CF4PhysicalBridgeError):
        angular_axis_cosine(np.zeros(6),v)



def test_method_angular_STF_alias_is_exact_common_method_direction_witness():
    from obsstat.cf4_physical_transfer_identification import (
        method_angular_calibration_alias_matrix,KAPPA)
    z,n,fam,mu,e=mock(n=1200,seed=74)
    m=cf4_working_model(z,n,fam,mu,e,kernel_name="unit_angular_endpoint")
    alias=method_angular_calibration_alias_matrix(m,n,fam)
    L=alias["alias_gamma_per_method_quadrupole_mag"]
    assert L.shape==(5,20)
    # If every method has the same sky-quadrupole magnitude calibration,
    # that exactly mimics the global STF but with factor -1/kappa.
    alpha=np.array([.02,-.01,.03,.04,.008])
    common=np.tile(alpha,4)
    np.testing.assert_allclose(L@common,-alpha/KAPPA,atol=2e-13,rtol=1e-12)
    # A finite injected source distortion must shift real fitted STF
    # coefficients exactly as source nuisance-projected Jacobian says.
    source=np.einsum("ni,aij,nj->na",n,
      __import__('obsstat.cf4_apparent_kinematic_distribution',fromlist=['stf2_orthonormal']).stf2_orthonormal(),
      n,optimize=True)
    delta=np.sum(source*alpha[None,:],axis=1)
    original=profile_declared_family(m)
    injected={**m,"residual":m["residual"]+delta}
    updated=profile_declared_family(injected)
    np.testing.assert_allclose(updated["gamma"]-original["gamma"],L@common,
                               atol=1e-12,rtol=1e-10)
