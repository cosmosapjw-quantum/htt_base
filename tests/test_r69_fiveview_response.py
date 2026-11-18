"""Finite mathematical/real-input checks of typed five-view physics. No astronomy p calibration."""
import numpy as np
from scipy.stats import chi2
from pathlib import Path
import pytest
from scripts.r68.fiveview_geometry import stf_matrix,radiation_stress_gauge
from scripts.r69.fiveview_response import (
    gaussian_null, interval_occupancy, kinetic_flux_stress_gauge,
    directional_hubble_gauge, min_spherical_quadratic,
    shear_shape_evolution, atlas_from_previous_data
)
from scripts.r69.physical_bridges import boosted_radiation_stress, sky_random


def test_first_second_radiation_moments_are_physical_PSD():
    n=sky_random(6000,seed=12)
    w=np.exp(n[:,2]*2+.4*n[:,1]);w/=w.sum()
    f=np.sum(n*w[:,None],axis=0)
    P=np.einsum('n,ni,nj->ij',w,n,n)
    S=P-np.eye(3)/3
    k=kinetic_flux_stress_gauge(f,S)
    assert k["Q_kinetic_moment_body"]<1
    assert k["physically_admissible_first_second_moments"]
    assert k["P_minus_ffT_min_eigenvalue"]>0
    assert k["Q_kinetic_moment_body"]>=k["Q_stress_only"]-1e-13


def test_nontrivial_flux_constraint_stronger_than_stress():
    f=np.array([.7,0,0])
    S=np.zeros((3,3))
    k=kinetic_flux_stress_gauge(f,S)
    assert np.isclose(k["Q_kinetic_moment_body"],np.sqrt(3)*.7)
    assert np.isclose(k["Q_stress_only"],0.)
    assert not k["physically_admissible_first_second_moments"]


def test_pure_lorentz_boost_satisfies_photon_moment_body():
    n=np.array([.3,-.8,.52]);n/=np.linalg.norm(n)
    for b in (.0001,.3,.9):
        r=boosted_radiation_stress(b,n)
        k=kinetic_flux_stress_gauge(r["flux_to_energy_c"]*n,r["stress_STF"])
        assert 0<k["Q_kinetic_moment_body"]<1
        assert k["physically_admissible_first_second_moments"]


def test_pure_STF_Hubble_gauge_eigenvalue_rule():
    S=np.diag([.3,-.1,-.2])
    q=directional_hubble_gauge(1.,np.zeros(3),S)
    np.testing.assert_allclose(q["Q_H_positive_directional_expansion"],.2)
    assert q["all_directional_leading_expansion_positive"]


def test_pure_dipole_Hubble_gauge_causality_analogue():
    S=np.zeros((3,3));d=np.array([.5,-.3,.2])
    q=directional_hubble_gauge(1.,d,S)
    np.testing.assert_allclose(q["Q_H_positive_directional_expansion"],np.linalg.norm(d),atol=1e-11)
    q2=directional_hubble_gauge(.1,d,S)
    assert q2["Q_H_positive_directional_expansion"]>1
    assert not q2["all_directional_leading_expansion_positive"]


def test_aligned_axial_shear_acceleration_coupling_exact():
    s=.2;d=.15
    S=s*np.diag([-1/3,-1/3,2/3])
    q=directional_hubble_gauge(1.,np.array([0,0,d]),S)
    pred=s/3+d*d/(4*s)
    np.testing.assert_allclose(q["Q_H_positive_directional_expansion"],pred,rtol=1e-11)


def test_general_angular_hubble_global_solver_against_grid_and_rotation():
    rng=np.random.default_rng(67)
    n=sky_random(120000,seed=10)
    for _ in range(5):
        v=rng.normal(size=5)*.1
        S=stf_matrix(v)
        d=rng.normal(size=3)*.08
        q=directional_hubble_gauge(1.,d,S)
        m=q["minimum_H_over_H"]-1
        brute=np.min(np.einsum("ni,ij,nj->n",n,S,n)+n@d)
        assert m<=brute+1e-10
        assert brute-m<.01
        qbasis,_=np.linalg.qr(rng.normal(size=(3,3)))
        S2=qbasis@S@qbasis.T; d2=qbasis@d
        q2=directional_hubble_gauge(1.,d2,S2)
        np.testing.assert_allclose(q2["Q_H_positive_directional_expansion"],q["Q_H_positive_directional_expansion"],atol=1e-11)


def test_shear_shape_driver_cancels_isotropic_dilution():
    S=stf_matrix([1.,.2,.3,-.25,.1])
    q=shear_shape_evolution(S, .4*S)
    assert abs(q["chi_dot_s_inv"])<1e-13
    # Nonparallel physical driver changes signed shape generically:
    D=stf_matrix([.12,-.21,.1,.3,.15])
    result=shear_shape_evolution(S,D)
    from scripts.r68.fiveview_geometry import stf_shape
    dt=1e-5
    for h in [.05,.3]:
        Splus=S+dt*(-3*h*S+D)
        numerical=(float(stf_shape(Splus)["signed_chi"])-float(stf_shape(S)["signed_chi"]))/dt
        np.testing.assert_allclose(numerical,result["chi_dot_s_inv"],atol=.0002,rtol=1e-3)


def test_exact_occupancy_x_response_and_interior_flatness():
    a=interval_occupancy(.2,.1,-.5,1.)
    b=interval_occupancy(.4,.1,-.5,1.)
    assert np.isclose(a["F_uniform_1d"],b["F_uniform_1d"])
    c=interval_occupancy(.99,.1,-.5,1.)
    assert c["F_uniform_1d"]<a["F_uniform_1d"]
    # x+dx may evolve without G_F changing if the confidence event stays interior.
    assert np.isclose(b["F_uniform_1d"]-a["F_uniform_1d"],0)


def test_gaussian_tail_named_law_only():
    x=np.array([1.,2.]); C=np.diag([4.,1.])
    a=gaussian_null(x,np.zeros(2),C)
    assert np.isclose(a["wald"],4.25)
    assert np.isclose(a["Pi_upper_tail"],chi2.sf(4.25,2))
    with pytest.raises(ValueError):
        gaussian_null(x,np.zeros(2),np.ones((2,2)))


def test_real_inputs_roundtrip_and_evidence_labels():
    root=Path(".")
    r=atlas_from_previous_data(root)
    v=r["studies"]
    assert len(v)==7
    assert v["P2_lowell_radiation"]["results"]["PR4"]["Q_joint_flux_stress"]=="UNAVAILABLE_WITHOUT_ACTUAL_F"
    assert 0<v["P2_lowell_radiation"]["results"]["PR4"]["Q_stress_physical"]<.0001
    assert v["radio_dipole"]["Pi_working_Gaussian"]<1e-6
    assert v["P6_kinematics"]["G_F"].startswith("requires ")
    assert v["P5_bianchi_all_types"]["Q_status"].startswith("R62 K0")
    assert r["physical_claim"].startswith("No new cosmological")


def test_R61_small_speed_occupancy_is_not_p_value():
    r=atlas_from_previous_data(Path("."))["studies"]["P1_tensorized"]
    assert 0<r["F_uniform_causal_beta_ball_outer_bound"]<1e-6
    assert r["Pi"]>1e-5
    assert not np.isclose(r["F_uniform_causal_beta_ball_outer_bound"],r["Pi"])
    assert "NOT posterior" in r["F_scope"]


def test_photon_cap_F_not_determined_by_first_two_moments():
    from scripts.r69.fiveview_response import radiation_cap_nonuniqueness
    r=radiation_cap_nonuniqueness(.9)
    np.testing.assert_allclose(r["same_x_flux"],0)
    np.testing.assert_allclose(r["same_x_STF5"],0)
    assert np.isclose(r["uniform_sky_cap_F"],.1)
    assert np.isclose(r["six_beam_cap_F"],1/3)
    assert r["uniform_sky_cap_F"]!=r["six_beam_cap_F"]


def test_photon_iid_CLT_covariance_and_conditional_Pi_only():
    from scripts.r69.fiveview_response import independent_photon_direction_null
    out=independent_photon_direction_null(np.zeros(3),np.zeros((3,3)),N=100)
    assert np.isclose(out["T"],0) and np.isclose(out["Pi_asymptotic_chi2_8"],1)
    n=sky_random(1000000,seed=10)
    Q=np.einsum("ni,nj->nij",n,n)-np.eye(3)[None,:,:]/3
    f=n.mean(axis=0)
    S=Q.mean(axis=0)
    covf=(n.T@n/len(n)-np.outer(f,f))
    np.testing.assert_allclose(covf,np.eye(3)/3,atol=.003)
    from scripts.r68.fiveview_geometry import stf_coordinates
    qs=stf_coordinates(Q)
    covq=np.cov(qs,rowvar=False,bias=True)
    np.testing.assert_allclose(covq,np.eye(5)*2/15,atol=.0025)
    assert 0<=independent_photon_direction_null(f,S,len(n))["Pi_asymptotic_chi2_8"]<=1


def test_kinetic_maxentropy_closure_moment_match_and_nonidentical_F():
    from scripts.r69.fiveview_response import maximum_entropy_axisymmetric_photon_closure
    r=maximum_entropy_axisymmetric_photon_closure(beta=.3,cap=.9)
    assert r["moment_residual_max_abs"]<1e-11
    assert abs(r["F_cap_closure_error"])>1e-8
    assert abs(r["third_moment_closure_error"])>1e-8
    z=maximum_entropy_axisymmetric_photon_closure(beta=0.,cap=.9)
    assert max(abs(q) for q in z["max_entropy_lambda_nu"])<1e-10
    assert abs(z["F_cap_exact_boost"]-z["F_cap_max_entropy_closure"])<1e-11


def test_canonical_sky_F_axial_positive_and_negative_same_norm():
    from scripts.r69.fiveview_response import sky_solid_angle_F
    S=np.diag([-.2/3,-.2/3,.4/3])
    pos=sky_solid_angle_F(S,nside=128)
    neg=sky_solid_angle_F(-S,nside=128)
    exact=1-1/np.sqrt(3)
    assert abs(pos["F_sky_solid_angle"]-exact)<.004
    assert abs(neg["F_sky_solid_angle"]-1/np.sqrt(3))<.004
    assert np.isclose(pos["F_sky_solid_angle"]+neg["F_sky_solid_angle"],1,atol=.003)
    assert pos["F_sky_solid_angle"]!=neg["F_sky_solid_angle"]


def test_R62_apparent_depth_sky_F_not_promoted_physical_GF():
    from scripts.r69.fiveview_response import atlas_from_previous_data
    r=atlas_from_previous_data(Path("."))
    a=r["studies"]["P5_bianchi_all_types"]
    f=a["F_sky_apparent_depth_curve_not_physical_G_F"]
    assert len(f)==4 and [r["z_cmb"] for r in f]==[.025,.04,.06,.08]
    assert all(0<=r["F_sky_apparent"]<=1 for r in f)
    assert a["G_F"].startswith("UNAVAILABLE")


def test_hubble_gauge_tiny_physical_units_no_false_positive():
    from scripts.r69.fiveview_response import directional_hubble_gauge
    H=1e-12
    S=np.diag([-H,0,H])
    d=np.array([H,0,0])
    out=directional_hubble_gauge(H,d,S)
    np.testing.assert_allclose(out["Q_H_positive_directional_expansion"],2.,atol=1e-11)
    assert not out["all_directional_leading_expansion_positive"]
    for unit_factor in [1e-8,1e-4,1,1e7]:
        nxt=directional_hubble_gauge(H*unit_factor,d*unit_factor,S*unit_factor)
        np.testing.assert_allclose(nxt["Q_H_positive_directional_expansion"],2.,atol=1e-11)
        assert nxt["stationarity_residual"]<1e-10 if "stationarity_residual" in nxt else True


def test_sphere_hard_case_outside_min_eigenspace():
    from scripts.r69.fiveview_response import min_spherical_quadratic
    S=np.diag([-2.,0.,2.])
    d=np.array([0.,.8,0.])
    out=min_spherical_quadratic(S,d)
    assert out["case"]=="hard_stationary"
    np.testing.assert_allclose(out["min_angular_perturbation"],-2.08,atol=1e-10)
    assert out["stationarity_residual"]<1e-10


def test_cap_integral_split_analytic_boost_and_isotropic():
    from scripts.r69.fiveview_response import maximum_entropy_axisymmetric_photon_closure
    c=.9;b=.3
    r=maximum_entropy_axisymmetric_photon_closure(beta=b,cap=c)
    # Exact analytic boost bolometric angular integral: int (1-b mu)^-4 dmu
    def antiderivative(z):
        return (1-b*z)**(-3)/(3*b)
    boost=(antiderivative(-c)-antiderivative(-1)+
           antiderivative(1)-antiderivative(c)) / (antiderivative(1)-antiderivative(-1))
    np.testing.assert_allclose(r["F_cap_exact_boost"],boost,rtol=1e-11)
    np.testing.assert_allclose(r["F_cap_exact_boost"],.1535975902,atol=1e-9)
    np.testing.assert_allclose(r["F_cap_max_entropy_closure"],.1529194181,atol=1e-9)
    isotropic=maximum_entropy_axisymmetric_photon_closure(beta=0.,cap=c)
    np.testing.assert_allclose(isotropic["F_cap_exact_boost"],1-c,atol=1e-13)
    np.testing.assert_allclose(isotropic["F_cap_max_entropy_closure"],1-c,atol=1e-13)


def test_hubble_gauge_fails_closed_at_nontrivial_hard_case_in_units():
    H=1e-11; S=np.diag([-2.,0,2.])*H
    d=np.array([0,.8,0])*H
    from scripts.r69.fiveview_response import directional_hubble_gauge
    out=directional_hubble_gauge(H,d,S)
    np.testing.assert_allclose(out["Q_H_positive_directional_expansion"],2.08,atol=1e-11)
    assert not out["all_directional_leading_expansion_positive"]
    for factor in (1e-9,1.,1e9):
        other=directional_hubble_gauge(H*factor,d*factor,S*factor)
        np.testing.assert_allclose(other["Q_H_positive_directional_expansion"],2.08,atol=1e-10)


def test_boost_flux_stress_gauge_subluminal_limit():
    from scripts.r69.fiveview_response import kinetic_flux_stress_gauge
    n=np.array([0.,0.,1.])
    from scripts.r69.physical_bridges import boosted_radiation_stress
    values=[]
    for beta in (.001,.5,.95):
        v=boosted_radiation_stress(beta,n)
        g=kinetic_flux_stress_gauge(v["flux_to_energy_c"]*n,v["stress_STF"])
        values.append(g["Q_kinetic_moment_body"])
        assert g["physically_admissible_first_second_moments"]
    assert values[0]<values[1]<values[2]<1.


def test_kinetic_physical_gauge_susceptibility_vs_direct_finite_difference():
    from scripts.r69.fiveview_response import kinetic_Q_susceptibility
    f=np.array([.23,.07,-.13])
    S=stf_matrix([.025,.014,-.032,.028,.019])
    df=np.array([.05,-.04,.07])
    dS=stf_matrix([-.015,.018,.005,-.025,.02])
    ans=kinetic_Q_susceptibility(f,S,df,dS)
    assert ans["status"]=="SIMPLE_ACTIVE_EIGENVALUE_CONDITIONAL"
    h=1e-6
    a=kinetic_flux_stress_gauge(f+h*df,S+h*dS)["Q_kinetic_moment_body"]
    b=kinetic_flux_stress_gauge(f-h*df,S-h*dS)["Q_kinetic_moment_body"]
    np.testing.assert_allclose(ans["dQ"],(a-b)/(2*h),atol=1e-9,rtol=1e-8)
    out=kinetic_Q_susceptibility(np.zeros(3),np.zeros((3,3)),
                                np.ones(3),np.zeros((3,3)))
    assert out["dQ"] is None


def test_geometry_F_does_not_recover_physical_amplitude_history():
    from scripts.r69.fiveview_response import sky_solid_angle_F
    S=stf_matrix([.2,.1,-.3,.08,.05])
    v=[sky_solid_angle_F(a*S,nside=64)["F_sky_solid_angle"] for a in (.1,1.,10.)]
    assert v[0]==v[1]==v[2]  # identical sign events, distinct physical shear amplitudes


def test_real_atlas_physical_referent_not_promoted():
    from scripts.r69.fiveview_response import atlas_from_previous_data
    r=atlas_from_previous_data(Path("."))["studies"]
    assert "NOT directly observed" in r["P1_tensorized"]["x"]
    assert "not direct local" in r["P6_kinematics"]["x"]
    q=r["P3_directional_H"]["Q_vertex_from_R62_phenomenological_STF"]
    assert "FORMULA_ONLY_IF_INPUT_IS_LOCAL_GR_VERTEX" in q["physical_source"]
    assert q["actual_input_scope"].startswith("R62 PHENOMENOLOGICAL")
    assert r["P2_lowell_radiation"]["results"]["PR4"]["Q_joint_flux_stress"]=="UNAVAILABLE_WITHOUT_ACTUAL_F"


def test_report_primary_cap_values_equal_reproduced_atlas():
    import json
    p=Path("docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118")
    s=(p/"X_TO_FIVEVIEW_PHYSICAL_RESPONSE_KO.md").read_text()
    primary=s.split("## 심사 후",1)[0]
    assert "F boost exact .1535975902, F ME .1529194181" in primary
    assert ".1568503863" not in primary
    a=json.loads((p/"RESULTS/FIVEVIEW_X_RESPONSE_ATLAS.json").read_text())
    cl=a["studies"]["P2_lowell_radiation"]["max_entropy_axisymmetric_photon_closure_benchmark"]
    assert abs(cl["F_cap_exact_boost"]-.15359759018323188)<1e-13
    assert abs(cl["F_cap_max_entropy_closure"]-.1529194181103092)<1e-13
