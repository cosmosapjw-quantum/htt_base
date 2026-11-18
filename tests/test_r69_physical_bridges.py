"""R69 exact/finite physical bridge checks. No cosmological anomaly p-values."""
import json
from pathlib import Path

import numpy as np
import pytest

from scripts.r68.fiveview_geometry import E,stf_matrix,stf_shape
from scripts.r69.physical_bridges import (
    angular_tensor_moments,hemisphere_leakage,cf4_hemisphere_windows,
    boosted_radiation_stress,retained_r66_boost_check,
    bianchi_I_directional_redshift,bianchi_I_temperature,
    sky_random
)
from scripts.r69.gaia_e2_b2 import templates,accumulate,fit_case


def test_stf_angular_moment_identity_monte_carlo():
    n=sky_random(700000,seed=17)
    S=stf_matrix([.01,-.02,.05,.007,-.015])
    f=np.einsum("ni,ij,nj->n",n,S,n)
    exact=angular_tensor_moments(S)
    assert abs(f.dot(f)/len(n)/exact["m2"]-1)<.006
    assert abs(np.mean(f**3)/exact["m3"]-1)<.045


def test_hemisphere_monopole_and_stf_cancellation_full_sky():
    n=sky_random(450000,seed=18)
    p=np.array([0.,0.,1.])
    t=hemisphere_leakage(n,p)
    assert t["dipole_response_error"]<.006
    assert t["STF_window_leakage_norm"]<.008


def test_hemisphere_leakage_reconstructs_arbitrary_stf():
    n=np.array([[1.,0.,0.],[-1.,0.,0.],[0.,1.,0.],[0.,-1.,0.],[0.,0.,1.],[0.,0.,-1.]])
    p=np.array([1,0,0.])
    # Avoid arbitrary equatorial membership by rotating away from boundary.
    n=sky_random(30000,seed=21)
    t=hemisphere_leakage(n,p)
    Q=stf_matrix([1.,.5,-.3,.4,.7])
    npos=n@npar(p)>=0
    f=np.einsum("ni,ij,nj->n",n,Q,n)
    observed=f[npos].mean()-f[~npos].mean()
    np.testing.assert_allclose(observed,np.einsum("ij,ij->",t["STF_window_leakage_matrix"],Q),atol=1e-12)


def npar(x):
    return np.asarray(x,float)/np.linalg.norm(x)


def test_bianchiI_exact_geodesic_redshift_flrw_limit():
    dirs=sky_random(1500,seed=42)
    Z=bianchi_I_directional_redshift(1.,.3,np.zeros(3),np.zeros(3),dirs)
    np.testing.assert_allclose(Z,np.full(1500,1/.3),atol=1e-13)


def test_bianchiI_exact_first_order_integrated_shear_quadrupole():
    n=sky_random(30000,seed=57)
    s=np.array([.5,-.3,-.2])
    error=[]
    for e in [1e-2,1e-3,1e-4]:
        t=bianchi_I_temperature(1.,.7,np.zeros(3),-e*s,n,T_e=1./.7)
        lin=-np.sum(n*n*(e*s),axis=1)
        obs=t/t.mean()-1.
        lin-=lin.mean()
        error.append(float(np.linalg.norm(obs-lin)/np.sqrt(len(n))))
    assert error[1]/error[0]<.02
    assert error[2]/error[1]<.02


def test_kinetic_isotropic_radiation_boost_exact_tensor():
    beta=.2
    n=np.array([.36,.48,.8]);n=n/np.linalg.norm(n)
    r=boosted_radiation_stress(beta,n)
    gamma2=1/(1-beta**2)
    # epsilon_rest=1, p=1/3, c=1 for tensor component test.
    U=np.r_[np.sqrt(gamma2),np.sqrt(gamma2)*beta*n]
    metric=np.diag([-1.,1.,1.,1.])
    T=(4./3)*np.outer(U,U)+(1./3)*metric
    rho=T[0,0];P=T[1:,1:];pi=P-np.trace(P)*np.eye(3)/3
    np.testing.assert_allclose(pi/rho,r["stress_STF"],atol=1e-14)
    q=T[0,1:]
    np.testing.assert_allclose(np.linalg.norm(q)/rho,r["flux_to_energy_c"],atol=1e-14)
    assert np.isclose(r["chi"],1)


def test_BianchiV_codazzi_required_zero_shear_eigenvalue():
    S=stf_matrix([.5,0,0,0,0])
    assert np.isclose(np.linalg.det(S),0)
    assert np.isclose(stf_shape(S)["signed_chi"],0)
    a=np.array([0.,0.,1.])
    np.testing.assert_allclose(S@a,0.,atol=1e-15)
    axial=stf_matrix([0.,1.,0,0,0])
    assert np.abs(np.linalg.det(axial))>0
    assert np.isclose(np.abs(stf_shape(axial)["signed_chi"]),1)


def test_gaia_E2_screen_gradient_and_B2_orthogonality():
    ra=np.array([.3,1.1,2.9])
    dec=np.array([.1,-.2,.4])
    n,B=templates(ra,dec)
    coeff=np.array([.2,-.3,.5,.1,-.7])
    S=stf_matrix(coeff)
    field=B[:,:,6:11]@coeff
    f=np.einsum("ni,ij,nj->n",n,S,n)
    eps=1e-6
    np_,_=templates(ra+eps,dec)
    nm_,_=templates(ra-eps,dec)
    f_=[np.einsum("ni,ij,nj->n",ni,S,ni) for ni in (np_,nm_)]
    grad_ra=(f_[0]-f_[1])/(2*eps*np.cos(dec))
    ndp,_=templates(ra,dec+eps)
    ndm,_=templates(ra,dec-eps)
    grad_dec=(np.einsum("ni,ij,nj->n",ndp,S,ndp)-
              np.einsum("ni,ij,nj->n",ndm,S,ndm))/(2*eps)
    np.testing.assert_allclose(field[:,0],grad_ra/2,rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(field[:,1],grad_dec/2,rtol=1e-8,atol=1e-8)
    bfield=B[:,:,11:16]@coeff
    np.testing.assert_allclose(np.sum(field*bfield,axis=1),0.,atol=1e-14)


def test_gaia_simulated_sixteen_mode_recovery():
    rng=np.random.default_rng(80)
    ra=rng.uniform(0,2*np.pi,1500);dec=np.arcsin(rng.uniform(-1,1,1500))
    _,B=templates(ra,dec)
    beta=rng.normal(size=16)*.008
    mu=B@beta
    F,s,c=accumulate(B,mu,np.full(len(ra),.4),np.full(len(ra),.3),np.full(len(ra),.15))
    res=fit_case({"F":F,"score":s,"chisq":c,"N":len(mu)})
    assert res["rank"]==16
    np.testing.assert_allclose(res["coefs_microasyr"],1000*beta,atol=1e-10)


def test_real_catalogue_geometry_and_source_identity_optional():
    root=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
    if root.exists():
        r=cf4_hemisphere_windows(root)
        assert r["valid_rows"]==38053
        assert len(r["bins"])==6
        assert r["bins"][-1]["Galactic_north"]["STF_window_leakage_norm"]>.3
    r66=Path("docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json")
    if r66.exists():
        r=retained_r66_boost_check(r66)
        assert all(x["angle_cosine_obs_boost"]<.2 for x in r["results"].values())
        assert all(not x["boost_only_algebraically_sufficient"] for x in r["results"].values())


def test_saved_gaia_real_data_exists_if_available():
    p=Path("docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json")
    if not p.exists():pytest.skip("Actual 1.6million source Gaia fit not yet run")
    r=json.loads(p.read_text())
    x=r["results"]["quality"]
    assert x["n_sources"]==1580645 and x["rank"]==16
    assert 5<x["groups_amplitude_microasyr"]["E2"]<7
    assert 3<x["groups_amplitude_microasyr"]["B2"]<5
    assert x["spatial_patch_192_std_microasyr"][6]>x["formal_errors_microasyr"][6]


def test_exact_signed_shape_and_fossil_axis_under_restricted_bianchi_I():
    # Under the *restricted* isotropic-source/zero-total-pi Bianchi-I closure:
    # CMB Q proportional to -sigma0, axes same and signed chi opposite.
    S=stf_matrix([1.3,-.7,.4,.9,-.2])
    Q=-.00002*S
    np.testing.assert_allclose(np.linalg.norm(Q@S-S@Q),0,atol=1e-18)
    np.testing.assert_allclose(np.sum(-Q*S)/(np.linalg.norm(Q)*np.linalg.norm(S)),1)
    np.testing.assert_allclose(stf_shape(Q)["signed_chi"],
                               -stf_shape(S)["signed_chi"])


def test_actual_frame_aware_gaia_cmb_counterfactual_optional():
    p=Path("docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GR_KINETIC_HEMISPHERES.json")
    if not p.exists():pytest.skip("Actual cross-probe diagnostic unavailable")
    r=json.loads(p.read_text())
    x=r["Gaia_CMB_counterfactual_frame_alignment"]
    assert x["actual_status"].startswith("NOT_PHYSICAL_TEST")
    R=np.asarray(x["ICRS_to_Galactic_SO3"])
    np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-13)
    np.testing.assert_allclose(np.linalg.det(R),1.,atol=1e-13)
    q=x["comparisons"]["PR4__observed_STF5"]
    assert abs(q["chi_CMB_template"]+q["chi_Gaia_E2_template"])<.03
    assert abs(q["counterfactual_negative_cosine_WEAK_ANISOTROPY_ONLY"])<.15
    assert q["counterfactual_normalized_commutator"]>.5


def test_actual_conditional_shear_history_only_benchmark():
    p=Path("docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GR_KINETIC_HEMISPHERES.json")
    if not p.exists():pytest.skip("Actual conditional bridge unavailable")
    b=json.loads(p.read_text())["R66_to_BianchiI_FORMAL_template_only"]
    assert b["physical_status"]=="FORMAL_TEMPLATE_NOT_PHYSICAL_DEBOOST_OR_OBSERVATIONAL_BOUND"
    assert 39000<b["dimensionless_H0_integral"]<41000
    for k in ["PR3","PR4"]:
        val=b["results"][k]
        np.testing.assert_allclose(val["formal_norm_integrated_sigma_template"]/
                                   val["formal_norm_sigma0_template_over_H0"],
                                   b["dimensionless_H0_integral"],rtol=1e-12)


def test_collisionless_bianchiI_radiation_moment_kinetic_angular_quadrature():
    from scripts.r69.physical_bridges import bianchi_I_radiation_moment
    zeros=np.zeros(3)
    a=bianchi_I_radiation_moment(zeros,zeros)
    np.testing.assert_allclose(a["STF_pressure"],zeros[:,None]*zeros[None,:],atol=3e-14)
    assert abs(a["raw_trace_error"])<2e-13
    direction=np.array([.5,-.3,-.2])
    errs=[]
    for e in [1e-2,1e-3,1e-4]:
        v=bianchi_I_radiation_moment(zeros,-e*direction)
        expected=-(8/15)*np.diag(e*direction)
        errs.append(np.linalg.norm(v["STF_pressure"]-expected))
    # First-order Boltzmann stress map, quadratic analytic remainder.
    assert errs[1]/errs[0]<.02
    assert errs[2]/errs[1]<.02
    assert errs[0]<1e-5


def test_real_cf4_CMB_axis_hemisphere_is_extremely_imbalanced():
    p=Path("docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GR_KINETIC_HEMISPHERES.json")
    if not p.exists():pytest.skip("Actual full CF4 mask not processed yet")
    d=json.loads(p.read_text())["cf4_hemispheres"]["bins"][-1]
    assert d["distance_range_Mpc"]==[400,None] and d["n"]==4277
    p=d["CMB_dipole_direction"]
    assert p["N_plus"]==4187 and p["N_minus"]==90
    assert p["STF_window_leakage_norm"]>.7


def test_finite_integrated_shear_only_leading_tensor_proportionality():
    # Independent scientific review finite-shear counterexample: diagonal
    # Bianchi-I exact photon moment is coaxial but not proportional to Δβ.
    from scripts.r69.physical_bridges import bianchi_I_radiation_moment
    from scripts.r68.fiveview_geometry import stf_shape
    d=np.array([.4,-.1,-.3])
    S=bianchi_I_radiation_moment(d,np.zeros(3))["STF_pressure"]
    np.testing.assert_allclose(S-np.diag(np.diag(S)),0.,atol=1e-13)
    np.testing.assert_allclose(np.linalg.norm(S@np.diag(d)-np.diag(d)@S),0.,atol=1e-13)
    actual=float(stf_shape(S)["signed_chi"])
    linear=-float(stf_shape(np.diag(d))["signed_chi"])
    assert abs(actual-linear)>.2
    assert abs(actual+.3581)<.005
