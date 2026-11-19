"""R74/P4: source-conditional radio dipole rank/occupancy response checks.

Read-only original R65 NVSS 33k-pixel carrier, three-bin independent conditional
fits and R63 summary. NOT a physical Lorentz-reselection, LSS-calibrated null,
global tilt detection, or physical time evolution.

To reproduce at htt_base root:
  PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R74_P4_SOURCE_SCORE_FIVEVIEW_20261119/verify_p4.py
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import chi2
from astropy.coordinates import SkyCoord
from astropy import units as u

R = Path("docs/research_program/observational_publication_20261015")
SOURCE=R/"R65_DIPOLE_ANOMALY_20261117"/"RESULTS"
SOURCE_NVSS=SOURCE/"NVSS_OBSERVED_RESULT.json"
SOURCE_SUMMARY=SOURCE/"INTERPRETATION_SUMMARY.json"
SOURCE_CARRIER=SOURCE/"NVSS_CONDITIONAL_CARRIERS.npz"
SOURCE_R63=R/"R63_LOCAL_BOOST_GLOBAL_TILT_20261117"/"RESULTS/INTERPRETATION_SUMMARY.json"
C_KM_S=299792.458
SEED=20261119

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stack_saved_fits(model):
    """Return R65 saved independent fit 6D x and its disjoint-bin working C."""
    f=model["independent_fits"]
    assert len(f)==3
    v=np.array([part["estimate"][:2] for part in f],float)
    C=np.zeros((6,6))
    for b,part in enumerate(f):
        cc=np.array(part["covariance"],float)[:2,:2]
        C[2*b:2*b+2,2*b:2*b+2]=cc
    assert np.linalg.eigvalsh(C)[0]>0
    return v,C

def response_geometry(v,C,k,reference_T=None):
    """Fixed-k 3-bin shared a and beta, source-conditional Gaussian."""
    k=np.asarray(k,float)
    X=np.column_stack([np.kron(k[:,None],np.eye(2)),
                       np.kron(np.ones((3,1)),np.eye(2))])
    assert X.shape==(6,4) and np.linalg.matrix_rank(X)==4
    y=v.reshape(-1)
    W=np.linalg.inv(C)
    info=X.T@W@X
    covtheta=np.linalg.inv(info)
    theta=np.linalg.solve(info,X.T@W@y)
    resid=y-X@theta
    T=float(resid@W@resid)
    if reference_T is not None:
        assert abs(T-reference_T)<1e-9,(T,reference_T)
    d21=v[1]-v[0];d31=v[2]-v[0]
    det=float(d21[0]*d31[1]-d21[1]*d31[0])
    grad=np.array([-d31[1]+d21[1],d31[0]-d21[0],
                   d31[1],-d31[0],-d21[1],d21[0]])
    sigma_det=float(np.sqrt(grad@C@grad))
    ratio=(k[2]-k[0])/(k[1]-k[0])
    fixed_ratio_residual=(d31-ratio*d21)
    # fixed-k conditional plug-in parametric Gaussian reference for det ONLY
    # Reuses one source and conditions on estimated nuisance/response.
    rng=np.random.default_rng(SEED)
    n_draws=50000
    sample=rng.multivariate_normal(X@theta,C,n_draws).reshape(n_draws,3,2)
    aa=sample[:,1]-sample[:,0];bb=sample[:,2]-sample[:,0]
    det_null=aa[:,0]*bb[:,1]-aa[:,1]*bb[:,0]
    # This is NOT calibration under unknown freely fitted k.
    p_det=(1+int(np.sum(np.abs(det_null)>=abs(det))))/(n_draws+1)
    # independent conditional test of Gaussian residual distribution
    testdraws=rng.multivariate_normal(X@theta,C,10000)
    fitted=testdraws@W@X@covtheta
    re=testdraws-fitted@X.T
    Tsim=np.einsum("ni,ij,nj->n",re,W,re)
    assert abs(float(np.mean(Tsim))-2)<.1
    assert abs(float(np.mean(Tsim>chi2.ppf(.95,2)))-.05)<.01
    return {
      "conditional_response_k":k.tolist(),
      "selected_carrier_6D":y.tolist(),
      "fixed_k_fitted_parameters_beta_xy_a_xy":theta.tolist(),
      "fixed_k_fitted_parameters_conditional_sd":np.sqrt(np.diag(covtheta)).tolist(),
      "full_C6_working_covariance_eigen_range":[float(np.linalg.eigvalsh(C)[0]),
                                               float(np.linalg.eigvalsh(C)[-1])],
      "fixed_k_chi2_residual_T2":T,
      "fixed_k_score_Qstat":float(np.sqrt(T)),
      "fixed_k_Pi_conditional_chisquare2":float(np.exp(-T/2)),
      "full_C_gaussian_residual_null_mc_chisquare2_mean":float(np.mean(Tsim)),
      "full_C_gaussian_residual_null_mc_95tail":float(np.mean(Tsim>chi2.ppf(.95,2))),
      "rank_one_geometric_determinant":det,
      "rank_one_geometric_determinant_delta_sd":sigma_det,
      "rank_one_det_standardized_delta_warning":None if sigma_det==0 else det/sigma_det,
      "rank_one_det_conditional_parametric_bootstrap_two_sided_p":p_det,
      "rank_one_det_bootstrap_n":n_draws,
      "rank_one_det_bootstrap_null":"FIXED K, fitted common-a and beta nuisance; NOT free-k collinearity null, NOT cosmic LSS",
      "k_order_fixed_ratio":float(ratio),
      "k_order_point_norms_delta21_delta31":[float(np.linalg.norm(d21)),float(np.linalg.norm(d31))],
      "k_order_point_outside_segment":bool(np.linalg.norm(d21)>np.linalg.norm(d31)),
      "signed_contrast21":d21.tolist(),"signed_contrast31":d31.tolist(),
      "fixed_k_raw_unscaled_contrast_error":fixed_ratio_residual.tolist(),
      "claim_scope":"Source-conditional linear Gaussian, not observed three-dimensional observer speed or cosmic p-value"
    }

def ring_occ_one_bin(n,inv,counts,beta,k,v,axis):
    """Original R65 pixel-centre ring-conditioned *fitted model* occupancy.
    Original observed ring totals fixed, equal area pixel exposure.
    """
    beta=np.asarray(beta,float)
    event=(n@axis)>0
    nring=int(np.max(inv)+1)
    N_ring=np.bincount(inv,weights=counts,minlength=nring)
    Ntot=float(np.sum(counts))
    if Ntot<=0:raise ValueError("No selected sources")
    logw=n[:,:2]@v + k*(n@beta)
    # Small magnitude only in this bounded study, safe exponential.
    weights=np.exp(logw)
    Z=np.bincount(inv,weights=weights,minlength=nring)
    assert np.min(Z)>0
    p=weights/Z[inv]
    norm=np.bincount(inv,weights=p,minlength=nring)
    np.testing.assert_allclose(norm,np.ones_like(norm),rtol=1e-12,atol=1e-12)
    expected=N_ring[inv]*p
    F=float(np.sum(expected*event)/Ntot)
    Abar=np.bincount(inv,weights=p*event,minlength=nring)
    muN=np.stack([np.bincount(inv,weights=p*n[:,j],minlength=nring)
                  for j in range(3)],axis=1)
    muAN=np.stack([np.bincount(inv,weights=p*event*n[:,j],minlength=nring)
                   for j in range(3)],axis=1)
    grad=k*np.sum((N_ring/Ntot)[:,None]*(muAN-Abar[:,None]*muN),axis=0)
    # Full-mask global (not ring-profiled) variant, using the same fitted baseline.
    probability=expected/Ntot
    fullgrad=k*(np.sum(probability[:,None]*event[:,None]*n,axis=0)
                -F*np.sum(probability[:,None]*n,axis=0))
    return {"F_ring_conditional":F,
       "score_gradient_ring_profiled":grad.tolist(),
       "score_gradient_unprofiled_global":fullgrad.tolist(),
       "max_abs_ring_nz_spread":max(float(np.ptp(n[inv==j,2]))
                         for j in range(nring)),
       "N_selected":int(Ntot)}

def score_sensitivity(original,model,summary):
    with np.load(SOURCE_CARRIER,allow_pickle=False) as q:
        n=np.array(q["base64_pixel_vectors"],float)
        groups=np.array(q["base64_groups"],int)
        counts=np.array(q["base64_counts"],float)
        feature=np.array(q["base64_features"],float)
    assert n.shape==(33000,3) and counts.shape==(3,33000)
    np.testing.assert_allclose(feature[:,:2],n[:,:2],atol=1e-14)
    u_groups,inv=np.unique(groups,return_inverse=True)
    assert len(u_groups)==185
    cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
    p=np.array([np.cos(cmb.ra.rad)*np.cos(cmb.dec.rad),
                np.sin(cmb.ra.rad)*np.cos(cmb.dec.rad),np.sin(cmb.dec.rad)])
    k=np.asarray(summary["nvss_tables"][0]["peak_response_diagnostics"]["0.75"]["response"])
    V=np.array([x["estimate"][:2] for x in model["independent_fits"]])
    out={}
    for b in range(3):
        raw_counts=counts[b]
        base=ring_occ_one_bin(n,inv,raw_counts,np.zeros(3),k[b],V[b],p)
        step=1.e-5
        finite=np.zeros(3)
        for j in range(3):
            basis=np.zeros(3);basis[j]=step
            plus=ring_occ_one_bin(n,inv,raw_counts,basis,k[b],V[b],p)
            minus=ring_occ_one_bin(n,inv,raw_counts,-basis,k[b],V[b],p)
            finite[j]=(plus["F_ring_conditional"]-minus["F_ring_conditional"])/(2*step)
        grad=np.asarray(base["score_gradient_ring_profiled"])
        assert np.max(np.abs(finite-grad))<3e-8,(b,finite,grad)
        assert abs(grad[2])<2e-13,(b,grad)
        cmb_beta=369.82/C_KM_S*p
        injected=ring_occ_one_bin(n,inv,raw_counts,cmb_beta,k[b],V[b],p)
        delta=injected["F_ring_conditional"]-base["F_ring_conditional"]
        lin=float(grad@cmb_beta)
        assert abs(delta-lin)<5e-6
        rawF=float(np.sum(raw_counts[(n@p)>0])/np.sum(raw_counts))
        out[f"bin_{b+1}"]={
          "fixed_qualifying_selection":"original R65 base64, conditional pixel-centre log-count multinomial, ring totals fixed",
          "flux_interval_mJy_beam":([20,40],[40,80],[80,None])[b],
          "k_alpha_0p75_held_fixed":float(k[b]),
          "source_selected_total":int(np.sum(raw_counts)),
          "F_raw_empirical_selected_CMB_hemisphere":rawF,
          "F_ring_predicted_at_beta0":base["F_ring_conditional"],
          "F_ring_kinematic_score_gradient":base["score_gradient_ring_profiled"],
          "F_unprofiled_kinematic_score_gradient":base["score_gradient_unprofiled_global"],
          "F_ring_gradient_finite_difference":finite.tolist(),
          "F_ring_score_vs_finite_diff_maxabs_error":float(np.max(np.abs(grad-finite))),
          "ring_nz_range_max":base["max_abs_ring_nz_spread"],
          "F_ring_injected_betaCMB_toy":injected["F_ring_conditional"],
          "F_ring_betaCMB_increment_toy":float(delta),
          "F_ring_betaCMB_linear_prediction_toy":lin,
          "meaning":"NOT physically boosted NVSS sky or time GF; only conditional exponential score response"
        }
    assert any(abs(x["F_unprofiled_kinematic_score_gradient"][2])>1e-3 for x in out.values())
    return {"CMB_axis_ICRS_deg":[float(cmb.ra.deg),float(cmb.dec.deg)],
            "pixel_and_ring_counts":[len(n),len(u_groups)],
            "source_geometry_and_exact_ring_z_null":out,
            "rank_and_score_scope":"group total profiled, exponential count score, no true Lorentz aberration, source rest intrinsic unknown"}

def transport_toy():
    # Normalized angular probability obeying dot rho+div(rho V)=s,
    # choose no advection V=0 and s=rho*h for an analytic two-hemisphere source.
    # F(t)=exp(t)/(exp(t)+exp(-t)) under two regions of equal area,
    # source rate h=+1 on A and -1 on complement.
    tau=.3
    F=np.exp(tau)/(np.exp(tau)+np.exp(-tau))
    analytic=2*F*(1-F)
    dt=1e-5
    fp=np.exp(tau+dt)/(np.exp(tau+dt)+np.exp(-tau-dt))
    fm=np.exp(tau-dt)/(np.exp(tau-dt)+np.exp(-tau+dt))
    numeric=(fp-fm)/(2*dt)
    assert abs(analytic-numeric)<2e-10
    return {"model":"two equal-area hemispheres; V=0 and physical source term s=±rho per unit time (toy only)",
            "tau":tau,"F":float(F),"G_F_dot_exact":float(analytic),
            "G_F_dot_finite_difference":float(numeric),
            "actual_R65_physical_time_source_missing":True}

def main():
    obj=json.load(open(SOURCE_NVSS))
    summary=json.load(open(SOURCE_SUMMARY))
    original=json.load(open(SOURCE_R63))
    k=summary["nvss_tables"][0]["peak_response_diagnostics"]["0.75"]["response"]
    results={}
    for name in ("base64_dipole","base64_dipole_stf"):
        mod=obj["models"][name]
        v,C=stack_saved_fits(mod)
        oldT=(None if name=="base64_dipole" else summary["beta_residual_precision"]["residual_chi2"])
        results[name]=response_geometry(v,C,k,oldT)
    assert abs(results["base64_dipole"]["fixed_k_chi2_residual_T2"]-1.7879595655429783)<1e-9
    assert abs(results["base64_dipole_stf"]["fixed_k_chi2_residual_T2"]-1.6688570127294107)<1e-9
    sens=score_sensitivity(obj,obj["models"]["base64_dipole"],summary)
    assert original["publication_status"]=="NOT_READY_TO_SUBMIT"
    return {
      "schema":"htt.r74.p4_physical_fiveview_source_score/1",
      "source_hashes":{"R65_original_observed":sha(SOURCE_NVSS),
                       "R65_original_interpretation":sha(SOURCE_SUMMARY),
                       "R65_original_pixel_carrier":sha(SOURCE_CARRIER),
                       "R63_original_interpretation":sha(SOURCE_R63)},
      "units":"Dimensionless log-source-count dipoles and beta=v/c, R65 ICRS sourceward; 1st-order count-score only",
      "signed_three_bin_fits":{"original_pure_dipole_vs_dipole_plus_free_STF":results,
         "do_not_merge_different_baselines":True},
      "actual_R65_masked_F_response":sens,
      "physical_angular_number_balance_law_synthetic_validation":transport_toy(),
      "physical_Q_beta_status":"UNAVAILABLE_FULL_3D_SOURCE_FRAME_VELOCITY",
      "cosmological_Pi_status":"UNAVAILABLE_LSS_AND_POPULATION_NULL",
      "physical_G_F_status":"UNAVAILABLE_ONE_EPOCH_AND_NO_CONGRUENCE_TRANSPORT",
      "novelty_status":"PROJECT_APPLICATION_OF_KNOWN_GAUSSIAN_AND_COUNT_SCORE_GEOMETRY_NOT_NEW_GENERAL_STATISTICAL_THEOREM",
      "evidence":"stored conditional source responses and mask, analytic derivatives, numerical finite differences, fixed-Gaussian parametric null only"}

if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False))
