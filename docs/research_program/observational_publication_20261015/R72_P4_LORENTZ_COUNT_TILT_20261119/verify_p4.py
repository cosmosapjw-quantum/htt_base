"""R72/P4 bounded theory validation: Lorentz count curvature, STF quadrupole,
actual existing R65 NVSS mask and paired source-dependent covariance.

Inputs read-only: original R65/R63 retained results, no source refit/download.
Outputs mathematical/survey-geometry diagnostics ONLY; not a physical dipole
detection, velocity bound, LSS-calibrated p-value or Bianchi identification.
Run from htt_base root with PYTHONPATH=. .venv/bin/python -B <this_file>.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import sympy as sp
from astropy.coordinates import SkyCoord
from astropy import units as u
from numpy.polynomial.legendre import leggauss, legval
from scripts.r68.fiveview_geometry import stf_shape

R=Path("docs/research_program/observational_publication_20261015")
R65=R/"R65_DIPOLE_ANOMALY_20261117"/"RESULTS"
R63=R/"R63_LOCAL_BOOST_GLOBAL_TILT_20261117"/"RESULTS"
C_KM_S=299792.458

def symbolic_boost_expansion():
    beta,mu,k,kap=sp.symbols("beta mu k kap", real=True)
    t=sp.log(1-beta**2)/2-sp.log(1-beta*mu)
    actual=sp.series(sp.exp(k*t+kap*t**2/2),beta,0,3).removeO()
    expected=1+k*beta*mu+beta**2*((k*k+k+kap)*mu**2/2-k/2)
    assert sp.simplify(actual-expected)==0
    logactual=sp.series(k*t+kap*t**2/2,beta,0,3).removeO()
    logexpected=k*beta*mu+beta**2*((k+kap)*mu**2/2-k/2)
    assert sp.simplify(logactual-logexpected)==0
    pure=sp.series((1-beta**2)**(k/2)*(1-beta*mu)**(-k),beta,0,3).removeO()
    assert sp.simplify(pure-expected.subs(kap,0))==0
    return {"count_density_coeff_difference":"exact symbolic zero through order beta^2",
            "log_count_coeff_difference":"exact symbolic zero through order beta^2",
            "power_law_specialization":"exact symbolic zero","independent_tool":"SymPy"}

def finite_bin_and_mixture():
    alpha=.75;s=1+alpha;L=20.;U=80.
    x1=1/s;x2=3/s;xp=2/s
    # Define positive parent counts g_i(S)=C_i S^(-1-x_i).
    # C_i chosen so each component integrates to one source-count unit.
    def coeff(x):return x/(L**(-x)-U**(-x))
    c1,c2=coeff(x1),coeff(x2)
    def integral(x,c,t):
        low=L*np.exp(-s*t);up=U*np.exp(-s*t)
        return c*(low**(-x)-up**(-x))/x
    def mixed(t):
        return np.exp(2*t)*(integral(x1,c1,t)+integral(x2,c2,t))/2
    def pure(t):
        return np.exp(2*t)*integral(xp,coeff(xp),t)
    eps=1.e-5
    k_mix=(np.log(mixed(eps))-np.log(mixed(-eps)))/(2*eps)
    kap_mix=(np.log(mixed(eps))-2*np.log(mixed(0))+np.log(mixed(-eps)))/(eps**2)
    assert abs(k_mix-4)<1e-8
    assert abs(kap_mix-1)<3e-5
    assert abs(pure(.03)-np.exp(4*.03))<1e-13
    # exact δ-to-second-order count: dipole k beta, Q_count coefficient 1/2(k²+k+κ)
    beta=369.82/C_KM_S
    for fn, kap in [(pure,0.),(mixed,1.)]:
        mu=np.array([-1.,-.3,.1,.7,1.])
        delta=1/((1-beta*beta)**(-.5)*(1-beta*mu))
        vals=np.array([fn(np.log(di)) for di in delta])
        approx=1+4*beta*mu+beta**2*((16+4+kap)*mu**2/2-4/2)
        assert np.max(abs(vals-approx))<5e-8
    x,w=leggauss(80)
    def l2_coeff(f):
        delta=1/((1-beta*beta)**(-.5)*(1-beta*x))
        sig=np.array([f(np.log(di)) for di in delta])
        sig/=np.dot(w,sig)/2
        return 5*np.dot(w,sig*legval(x,[0,0,1]))/2
    a2pure=l2_coeff(pure);a2mixed=l2_coeff(mixed)
    predpure=20*beta**2/3;predmixed=21*beta**2/3
    assert abs(a2pure-predpure)<5e-10
    assert abs(a2mixed-predmixed)<5e-10
    return {"lower_flux":L,"upper_flux":U,"alpha":alpha,"beta_CMB_reference":beta,
        "population_A":{"k":4.,"kappa":0.,"a2_exact":a2pure,"a2_quadratic":predpure,
                        "Q_STF_amplitude_over_beta2":10.},
        "population_B":{"k":k_mix,"kappa":kap_mix,"a2_exact":a2mixed,
                        "a2_quadratic":predmixed,"Q_STF_amplitude_over_beta2":10.5},
        "same_first_order_dipole_both":4*beta,
        "second_order_difference_is_physical_selection_curvature":True}

def r65_mask_geometry():
    d=json.loads((R65/"INTERPRETATION_SUMMARY.json").read_text())
    with np.load(R65/"NVSS_CONDITIONAL_CARRIERS.npz",allow_pickle=False) as raw:
        n=np.array(raw["base64_pixel_vectors"])
        counts=np.array(raw["base64_counts"])
    assert n.shape==(33000,3) and counts.shape==(3,33000)
    np.testing.assert_allclose(np.linalg.norm(n,axis=1),1,atol=1e-14)
    cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
    p=np.array([np.cos(cmb.ra.radian)*np.cos(cmb.dec.radian),
                np.sin(cmb.ra.radian)*np.cos(cmb.dec.radian),np.sin(cmb.dec.radian)])
    h=(n@p)>0
    mean=(n@p)**2-1/3
    Mplus=n[h].T@n[h]/np.sum(h); Mminus=n[~h].T@n[~h]/np.sum(~h)
    STF=np.outer(p,p)-np.eye(3)/3
    value=float(np.einsum("ij,ij",STF,Mplus-Mminus))
    assert abs(value-(np.mean(mean[h])-np.mean(mean[~h])))<1e-14
    assert abs(value+0.020109432631770497)<1e-12
    beta=369.82/C_KM_S
    k=2+1.0431020647103473*(1+.75) # R65 earlier x slope over broad proxy range; illustrative
    A=k*(k+1)*beta*beta/2
    Qinjection=A*STF
    shape=stf_shape(Qinjection)
    assert abs(float(shape["signed_chi"])-1)<2e-14
    leak=float(np.einsum("ij,ij",Qinjection,Mplus-Mminus))
    assert abs(leak-A*value)<2e-17
    sourcebins=[]
    for b,row in enumerate(counts):
        plus=int(row[h].sum());minus=int(row[~h].sum())
        sourcebins.append({"bin":b,"observed_total_masked":plus+minus,
             "observed_CMB_hemispheres":[plus,minus],"observed_hemisphere_fraction":plus/(plus+minus),
             "uniform_mask_sky_pixel_fraction":np.mean(h),
             "meaning":"raw selected component count fraction, NOT corrected cosmic occupancy or posterior"})
    assert [x["observed_total_masked"] for x in sourcebins]==[115906,65260,55581]
    return {"source_mask_sha256":d["source_geometries"]["base64"]["mask_sha256"],
         "source_mask_pixels":len(n),"source_exposure_model":"uniform equal-area retained pixels, not ring-conditioned likelihood",
         "CMB_ICRS_RA_DEC_deg":[float(cmb.ra.deg),float(cmb.dec.deg)],
         "plus_minus_pixels":[int(np.sum(h)),int(np.sum(~h))],
         "STF_hemisphere_window_operator_Frobenius":float(np.linalg.norm(Mplus-Mminus)),
         "unit_rank1_quadrupole_leakage":value,
         "illustrative_k":k,"illustrative_beta_CMB":beta,
         "pure_boost_count_STF_coefficient":A,
         "pure_boost_chi":float(shape["signed_chi"]),
         "pure_boost_intrinsic_FOmega":float(1-1/np.sqrt(3)),
         "pure_boost_masked_hemisphere_mean_leakage":leak,
         "observed_counts_not_a_boost_measurement":sourcebins}

def paired_and_fisher():
    d=json.loads((R65/"INTERPRETATION_SUMMARY.json").read_text())
    arr=d["source_definition_covariance_ablation"]
    x=np.asarray(arr["actual_delta"],float)
    C=np.asarray(arr["actual_covariance"],float)
    wald=float(x@np.linalg.solve(C,x))
    p=d["source_definition_paired_results"]["dipole_stf"]
    cov=p["covariance"]
    CL=np.asarray(cov["covariance_left"]); CR=np.asarray(cov["covariance_right"])
    Ccross=np.asarray(cov["covariance_cross"])
    np.testing.assert_allclose(C,CL+CR-Ccross-Ccross.T,rtol=1e-13,atol=1e-16)
    wrong=float(x@np.linalg.solve(CL+CR,x))
    assert abs(wald-arr["actual_wald"])<1e-8
    assert abs(wrong-arr["wrong_independent_wald"])<1e-8
    response=d["nvss_tables"][1]["peak_response_diagnostics"]["0.75"]["response"]
    K=np.array(response)
    B=len(K); H=np.kron(np.ones((B,1)),np.eye(2))
    D=np.kron(K[:,None],np.eye(2))
    assert np.linalg.matrix_rank(np.column_stack([D,H]))==4
    # exact Gaussian nuisance Schur via synthetic positive definite covariance;
    # direct projection and full Schur identical (no reuse of stored R65 full 6x6 C).
    rng=np.random.default_rng(612)
    P=rng.normal(size=(6,6));C6=P@P.T+np.eye(6)*.5;W=np.linalg.inv(C6)
    f=(D.T@W@D)-(D.T@W@H)@np.linalg.solve(H.T@W@H,H.T@W@D)
    Pproj=W-W@H@np.linalg.solve(H.T@W@H,H.T@W)
    np.testing.assert_allclose(f,D.T@Pproj@D,atol=3e-14)
    ff=np.linalg.eigvalsh(f); assert ff[0]>0
    single=np.full(B,3.8)
    Dj=np.kron(single[:,None],np.eye(2))
    ff0=np.linalg.eigvalsh(Dj.T@Pproj@Dj)
    assert max(abs(ff0))<1e-11
    q=d["beta_residual_precision"]; V=np.asarray(q["full_covariance"],float)
    assert q["rank"]==4
    Vb=V[:2,:2]
    target_beta=369.82/C_KM_S
    cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
    beta_cmb=target_beta*np.array([np.cos(cmb.dec.rad)*np.cos(cmb.ra.rad),np.cos(cmb.dec.rad)*np.sin(cmb.ra.rad)])
    estimate=np.asarray(q["estimate"][:2])
    delta=estimate-beta_cmb
    condwald=float(delta@np.linalg.solve(Vb,delta))
    return {"R65_source_sha256":hashlib.sha256((R65/"INTERPRETATION_SUMMARY.json").read_bytes()).hexdigest(),
      "paired_integrated_minus_peak_delta":x.tolist(),
      "paired_cross_source_covariance_verified":True,
      "paired_working_wald":wald,
      "wrong_independent_working_wald":wrong,
      "paired_same_source_n":p["covariance"]["n_shared"],
      "paired_left_right_n":[p["covariance"]["n_left"],p["covariance"]["n_right"]],
      "flux_bin_k_assumed_alpha_0p75":response,
      "synthetic_source_response_Fisher_rank":2,
      "equal_k_projected_rank":0,
      "synthetic_Schur_fisher_eigenvalues":ff.tolist(),
      "R65_actual_beta_plus_residual_rank":q["rank"],
      "R65_beta_perp_hat":estimate.tolist(),
      "R65_beta_perp_working_sd":q["sd"][:2],
      "CMB_beta_xy_ICRS":beta_cmb.tolist(),
      "conditional_beta_minus_CMB_Wald2":condwald,
      "meaning":"working R65 same-source conditional Poisson/Gaussian; LSS and physical 3D velocity not qualified"}

def r63_history():
    x=json.loads((R63/"INTERPRETATION_SUMMARY.json").read_text())
    assert x["n_sources"]==35970 and x["publication_status"]=="NOT_READY_TO_SUBMIT"
    assert x["max_power_body"]<.100001
    return {"R63_source_sha256":hashlib.sha256((R63/"INTERPRETATION_SUMMARY.json").read_bytes()).hexdigest(),
            "actual_CF4_selected_groups":x["n_sources"],
            "restricted_history_working_power_alpha":x["power_alpha"],
            "restricted_history_power_upper_bound":x["max_power_body"],
            "meaning":"compensated dust/radiation history vs constant bulk only, NOT a global-tilt exclusion"}

def main():
    return {"schema":"htt.r72.p4_lorentz_count_tilt_physics/1",
      "symbolic":symbolic_boost_expansion(),
      "finite_flux_mixture":finite_bin_and_mixture(),
      "R65_actual_mask_geometry":r65_mask_geometry(),
      "R65_actual_paired_source_and_fisher":paired_and_fisher(),
      "R63_actual_CF4_compensated_history":r63_history(),
      "scope":"source and geometry checks, no re-estimated radio cosmic dipole, source velocity or Bianchi tilt posterior"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2))
