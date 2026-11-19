"""R73 P1-P4 physical typed five-view evidence calculation.

Read-only pinned R62/R64/R65/R66 and previous R69-P1 products. This uses
only source-conditional Gaussian, finite-band Commander and selected radio
catalogue readout; no independent cosmological null, global tilt or photon flux.

To run at htt_base root:
  PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R73_P1_P4_TYPED_PHYSICAL_FIVEVIEW_20261119/verify_fiveview.py
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.integrate import quad
from scipy.special import betainc
from scipy.stats import chi2
from htt.htt.infer import r64_directional_hubble as rd
from scripts.r68.fiveview_geometry import (
    stf_matrix, stf_shape, radiation_stress_gauge
)

ROOT = Path("docs/research_program/observational_publication_20261015")
R62 = ROOT/"R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION/log__J2_coefficients.json"
R66 = ROOT/"R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"
R64 = ROOT/"R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/AUGMENTED/AUGMENTED_CARRIERS.npz"
R64RESULT = ROOT/"R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/AUGMENTED/AUGMENTED_RESULT.json"
R64BASE = ROOT/"R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/OBSERVED/DIRECTIONAL_HUBBLE_RESULT.json"
R65 = ROOT/"R65_DIPOLE_ANOMALY_20261117/RESULTS/INTERPRETATION_SUMMARY.json"
R69P1 = ROOT/"R69_P1_FIVEVIEW_PHYSICS_LOOP2_20261119/RESULT.json"

def hash_bytes(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def exact_area_stf(S):
    """Intrinsic unweighted sphere fraction n S n > 0, not source photon F."""
    l1, l2, l3 = np.linalg.eigvalsh(S)
    if not (l1 < 0 < l3):
        raise ValueError("nonzero STF needed")
    ta = np.sqrt(-l1/(l3-l1))
    if abs(l2-l1) < 1e-12 * max(abs(l1),abs(l3)):
        return float(1-ta)
    tb = np.sqrt(-l2/(l3-l2)) if l2<0 else 0.
    def integrand(t):
        den=(l2-l1)*(1-t*t)
        num=l2*(1-t*t)+l3*t*t
        x=np.clip(num/den,0,1)
        return 2/np.pi*np.arcsin(np.sqrt(x))
    return float(1-ta+quad(integrand,tb,ta,epsabs=1e-12,epsrel=1e-12,limit=300)[0])

def halfspace_ellipsoid_F(dim, signed_normalized_margin):
    """Fraction of *uniform r-ball* satisfying a halfspace, not posterior."""
    t=float(signed_normalized_margin)
    if t<=-1:return 0.
    if t>=1:return 1.
    return float(.5 + .5*np.sign(t)*betainc(.5,(dim+1)/2,t*t))

def p1_r62_working():
    obj=json.loads(R62.read_text())
    a=np.array(obj["mean"][:5],float)
    C=np.array(obj["covariance"],float)[:5,:5]
    S=stf_matrix(a)
    Qh=-float(np.linalg.eigvalsh(S)[0])
    T=float(a@np.linalg.solve(C,a))
    p=float(chi2.sf(T,5))
    shape=stf_shape(S)
    f=exact_area_stf(S)
    old=json.loads(R69P1.read_text())
    assert abs(f-old["K0_fullsky_intrinsic_positive_area"])<3e-11
    assert obj["experiment"]=="J2_coefficients"
    assert abs(float(shape["signed_chi"])-old["K0_chi"])<1e-10
    return {
      "source":"R62 same CF4 15D apparent signed tensor, not P1 original selected 274-row law",
      "actual_R62_STF5":a.tolist(), "full_covariance_rank5":int(np.linalg.matrix_rank(C)),
      "actual_R62_STF_shape_chi":float(shape["signed_chi"]),
      "actual_R62_STF_intrinsic_fullsky_FOmega":f,
      "actual_R62_working_Gaussian_zero5_T":T,
      "actual_R62_working_Gaussian_zero5_tail":p,
      "hypothetical_GR_Q_H_if_H_eq1_d_eq0_S_eqK0":Qh,
      "hypothetical_GR_min_Hfrac_if_used_as_local_sigma_over_H":1-Qh,
      "actual_CF4_sample_FOmega_40_400_Mpc_from_existing_result":
          old["K0_CF4_unweighted_geometry_occupancy"][-1]["F_sample"],
      "nonclaims":["not P1 274-row confidence law","R62 apparent S != GR shear",
                   "fullsky F != masked sample fraction", "Gaussian tail != cosmic anisotropy PTE"]
    }

def p2_r66_radiation():
    src=json.loads(R66.read_text())
    assert src["qualified_actual_Commander_temperature_MC_count"]==0
    by={}
    t=.9
    for release in ("PR3","PR4"):
        v=np.array(src["nonlinear"][release]["radiation_moment_bundle"]["pi5_over_rho"],float)
        S=stf_matrix(v)
        P=np.eye(3)/3+S
        e=np.linalg.eigvalsh(P)
        assert e[0]>0 and abs(np.trace(P)-1)<2e-14
        q=float(radiation_stress_gauge(S))
        area=exact_area_stf(S)
        pzz=float(P[2,2])
        lower=max(0.,(pzz-t*t)/(1-t*t))
        upper=min(1.,pzz/(t*t))
        assert 0 <= lower<=upper <=1
        # Ellipsoid of allowed photon flux: f'P^-1 f<=1,
        # verified by a random admissible interior direction.
        rng=np.random.default_rng(123)
        test=rng.normal(size=3);test/=np.linalg.norm(test)
        evals,U=np.linalg.eigh(P)
        f=U@(np.sqrt(evals)*test*.8)
        assert float(f@np.linalg.solve(P,f))<1
        assert np.linalg.eigvalsh(P-np.outer(f,f))[0]>0
        assert np.linalg.eigvalsh(P-np.outer(f/.8*1.01,f/.8*1.01))[0]<0
        by[release]={
            "actual_retained_pi_over_rho_STF5":v.tolist(),
            "Q_stress_physical_moment_positive_gauge":q,
            "physical_stress_body_Q_le1":bool(q<=1),
            "signed_shape_chi":float(stf_shape(S)["signed_chi"]),
            "intrinsic_fullsky_positive_quadrupole_area":area,
            "P_eigenvalues":e.tolist(),
            "allowed_flux_ellipsoid_principal_semiaxes":np.sqrt(e).tolist(),
            "cap_abs_mu_gt_0p9_Pzz":pzz,
            "cap_energy_fraction_valid_lower_bound":lower,
            "cap_energy_fraction_valid_upper_bound":upper,
            "actual_flux_measured":False, "joint_Q_gamma_unavailable":True,
            "physical_cap_F_unidentified_from_STF5":True}
    return {
        "source":"R66 actual PR3/PR4 finite-band retained T^4 moment bundle, not full cosmological photon solution",
        "Commander_matched_T_MC_count":0,
        "release_results":by,
        "nonclosure_counterexample_from_R70":
         "smooth p_epsilon=(1+epsilon P4(cos theta))/(4pi), same first two moments, different photon cap F and Sdot",
        "physical_Pi":None,"physical_G_F":None}

def p3_r64_gaussian():
    original=json.loads(R64RESULT.read_text())
    base=json.loads(R64BASE.read_text())
    dirs=np.array(base["directions"],float)
    z=.08
    bg=rd.background_factors(z,base["Omega_m_reference"],base["H0_reference_km_s_Mpc"])
    B=float(bg["B"])
    assert dirs.shape==(54,3)
    rng=np.random.default_rng(20261119)
    model={}
    with np.load(R64,allow_pickle=False) as npz:
        for J in (1,2,3):
            key=f"mono_method__J{J}__method_angular_nuisance"
            theta=np.array(npz[key+"__estimate"],float)
            C=np.array(npz[key+"__covariance"],float)
            npar=len(theta)
            assert npar==3+9*(J+1)
            assert np.linalg.eigvalsh(C)[0]>0
            radius2=float(chi2.ppf(.95,npar))
            a=np.stack([-B*rd.field_rows(z,n,J)[1] for n in dirs])
            D=1+a@theta
            sd=np.sqrt(np.einsum("ni,ij,nj->n",a,C,a))
            lower=D-np.sqrt(radius2)*sd
            tf=D/(np.sqrt(radius2)*sd)
            pcap=np.array([halfspace_ellipsoid_F(npar,t) for t in tf])
            index=int(np.argmin(lower))
            aa=a[index]; s=sd[index]
            witness=theta-np.sqrt(radius2)*(C@aa)/s
            wD=float(1+aa@witness)
            wr2=float((witness-theta)@np.linalg.solve(C,witness-theta))
            assert abs(wD-lower[index])<5e-12
            assert abs(wr2-radius2)<1e-6
            # Check every saved source lower bound before using it.
            rows=original["models"][key]["maps"]
            for k,n in enumerate(dirs):
                row=next(v for v in rows if v["z_index"]==3 and v["direction_index"]==k)
                raw=row["ratio"]["denominator"]
                assert abs(float(raw["estimate"])-D[k])<3e-9
                assert abs(float(raw["sd"])-sd[k])<3e-9
                assert abs(float(raw["lower"])-lower[k])<3e-8
            # Uniform reference *volume* on the single joint 95% ellipsoid.
            # Do NOT conflate with a Bayesian posterior or sky area.
            chol=np.linalg.cholesky(C)
            runs=16384
            u=rng.normal(size=(runs,npar))
            u/=np.linalg.norm(u,axis=1)[:,None]
            u*=rng.random(runs)[:,None]**(1/npar)
            trials=theta[None,:]+np.sqrt(radius2)*(u@chol.T)
            Dr=1+trials@a.T
            accepted=np.all(Dr>0,axis=1)
            F54=float(np.mean(accepted))
            stderr=float(np.sqrt(F54*(1-F54)/runs))
            # Strict conditions: F54 is a grid occupancy (upper bound on
            # the *all-sky* ellipsoid feasible occupancy), not physical G_F.
            source_positive=int(np.sum(lower>0))
            assert source_positive==(54 if J<3 else 0)
            model[f"J{J}"]={
                "parent_model_key":key,"parameter_dimension":npar,
                "gaussian_common_95pct_cutoff_chisquare":radius2,
                "z":z,"reference_B":B,
                "point_D_min_over_54":float(np.min(D)),
                "positive_support_lower_count_54":source_positive,
                "min_joint_ellipsoid_D_lower":float(np.min(lower)),
                "explicit_counter_witness_direction_index":index,
                "explicit_counter_witness_D":wD,
                "explicit_counter_witness_ellipsoid_distance_squared":wr2,
                "uniform_ellipsoid_one_direction_Fmin_exact":float(np.min(pcap)),
                "uniform_ellipsoid_one_direction_Fmean_exact":float(np.mean(pcap)),
                "uniform_ellipsoid_54direction_joint_positive_fraction_MC":F54,
                "uniform_ellipsoid_54direction_MC_stderr":stderr,
                "uniform_ellipsoid_MC_sample_size":runs,
                "F54_semantics":"fraction of original 95% identified-parameter ellipsoid satisfying D>0 at all 54 fixed evaluation directions; NOT fullsky area or Bayesian posterior or cosmological probability",
                "allsky_F_upper_bound_by_F54":"F_allsky_ellipsoid <= F54; R73 does not calculate exact uncountable sky intersection"}
    return {"source":"R64 actual same CF4 68D mono_method+24 Gaussian, no independent Hcal, same source-selected sample",
            "actual_CF4_selected_groups":original["source_rows"],
            "reference":"flat smooth Planck18 H0 and Omega_m from R64, no physical GR source qualification",
            "models":model,"actual_physical_null":None,
            "actual_physical_G_F":None}

def p4_r65_count():
    obj=json.loads(R65.read_text())
    c=obj["source_definition_covariance_ablation"]
    delta=np.asarray(c["actual_delta"],float)
    cov=np.asarray(c["actual_covariance"],float)
    T=float(delta@np.linalg.solve(cov,delta))
    Q=np.sqrt(T)
    p=float(chi2.sf(T,2))
    assert abs(T-c["actual_wald"])<1e-10
    assert abs(p-c["actual_conditional_tail"])<1e-12
    assert abs(p-np.exp(-Q*Q/2))<1e-14
    g=obj["source_geometries"]["base64"]
    p4old=ROOT/"R72_P4_LORENTZ_COUNT_TILT_20261119/RESULTS.json"
    tmp=json.loads(p4old.read_text())
    hemi=tmp["R65_actual_mask_geometry"]["observed_counts_not_a_boost_measurement"]
    # Exact catalogue-defined F, with uncorrected selection/exposure.
    return {
       "source":"R65 same-provider peak/integrated ICRS transverse log-count source definition contrast, full cross covariance",
       "actual_paired_integrated_minus_peak_signed":delta.tolist(),
       "conditional_working_Q_stat":float(Q),
       "conditional_working_chisquare2_T":T,
       "conditional_working_Pi_tail":p,
       "exact_fixed_gaussian_Pi_from_Q2":float(np.exp(-Q*Q/2)),
       "wrong_independent_paired_Wald":c["wrong_independent_wald"],
       "registered_shared_components":obj["source_definition_paired_results"]["dipole_stf"]["covariance"]["n_shared"],
       "R65_flux_bins_source_selected_actual_counts":[b["observed_total_masked"] for b in hemi],
       "R65_raw_hemisphere_F":[b["observed_hemisphere_fraction"] for b in hemi],
       "R65_equal_pixel_mask_hemisphere_reference_F":hemi[0]["uniform_mask_sky_pixel_fraction"],
       "R65_loglink_count_positive":True,
       "physical_Q_beta":None,
       "physical_Pi_LSS":None,
       "physical_G_F":None,
       "nonclaim":"peak/integrated selection difference is not cosmic evolution, beta posterior, or fullsky source fraction"}

def p2_physical_GF_kinetic_toy():
    """A genuine conditional time-derivative of a normalized photon cap F.

    Fixed cap A={abs(mu)>.9}, homogeneous collisionless Bianchi I,
    axial normal sigma=s*diag(-1/3,-1/3,2/3), H=0 at the instant.
    This is synthetic physical kinetic evolution, not a CMB epoch fit.
    """
    s=.07
    t=.9
    P4=lambda mu:(35*mu**4-30*mu*mu+3)/8
    P4prime=lambda mu:(140*mu**3-60*mu)/8
    v=lambda mu:-s*mu*(1-mu*mu)
    h=lambda mu:mu*mu-1/3
    cases=[]
    for eps in (0.,1.):
        p=lambda mu:(1+eps*P4(mu))/2
        pprime=lambda mu:eps*P4prime(mu)/2
        # The two symmetric cap boundaries supply the geometric flux term.
        boundary=-s*t*(1-t*t)*(1+eps*P4(t))
        covariance=-s*2*quad(lambda mu:h(mu)*p(mu),t,1)[0]
        source_integral=2*quad(lambda mu:-v(mu)*pprime(mu)-4*s*h(mu)*p(mu),t,1)[0]
        assert abs(boundary+covariance-source_integral)<3e-14
        Fcap=2*quad(lambda mu:p(mu),t,1)[0]
        assert abs(Fcap-(.1+.05707125*eps))<2e-13
        cases.append({"epsilon":eps,"same_initial_flux_and_STF5_zero":True,
            "physical_cap_F_at_initial_event":Fcap,
            "angular_boundary_flux_term":boundary,
            "kinetic_covariance_source_term":covariance,
            "GF_time_derivative_exact":boundary+covariance,
            "direct_intensity_transport_integral":source_integral,
            "check_error":float(abs(boundary+covariance-source_integral))})
    assert abs(cases[0]["GF_time_derivative_exact"]-(-.01596))<1e-13
    assert abs(cases[1]["GF_time_derivative_exact"]-(-.020813835))<1e-13
    return {"theorem":"dF/dt=-int_boundary p V.nu -Cov_p(1_A,sigma_nn-2c a.n), for specified fixed event and collisionless homogeneous normal",
            "real_CMB_epoch_transfer_available":False,
            "time_unit":"illustrative, s=.07 per source-defined unit",
            "physical_toy_verified":cases}


def main():
    assert abs(halfspace_ellipsoid_F(1,.4)-.7)<2e-15
    assert abs(halfspace_ellipsoid_F(5,.4)-.83692)<2e-14
    s=np.diag([-1.,-1.,2.])
    assert abs(exact_area_stf(s)-(1-1/np.sqrt(3)))<2e-12
    p1=p1_r62_working()
    p2=p2_r66_radiation()
    p3=p3_r64_gaussian()
    p4=p4_r65_count()
    data={
      "schema":"htt.r73.p1_p4_typed_physical_fiveview/1",
      "source_input_sha256":{
        "R62_J2_15D":hash_bytes(R62),
        "R66_PR3PR4":hash_bytes(R66),
        "R64_augmented_carrier":hash_bytes(R64),
        "R64_augmented_result":hash_bytes(R64RESULT),
        "R65_interpretation":hash_bytes(R65),
        "R69_P1_geometry":hash_bytes(R69P1)},
      "source_scientific_scope":"one observed source per paper, no independent physical source-posterior or new CMB/radio anomaly",
      "P1":p1,"P2":p2,"P3":p3,"P4":p4,
      "P2_physical_GF_toy":p2_physical_GF_kinetic_toy(),
      "tested_analytic_halfspace_ball_cap":"dimension 1 and dimension 5 exact reference values",
      "native_independent_reviewer":"NOT_RUN",
      "physical_discovery":"NOT_CLAIMED"
    }
    return data
if __name__=="__main__":
    print(json.dumps(main(),ensure_ascii=False,indent=2))
