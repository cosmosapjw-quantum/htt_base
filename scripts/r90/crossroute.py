"""R90 bounded solver-free numerical evaluations of seven inherited R77 PHY routes.

All numerical experiments explicitly label empirical source vs constructed
physics. No physical covariance/null/transfer is substituted or promoted.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.linalg import null_space
from scripts.r90.sf_attribution import ROOT, BASE, STF, codazzi_stf

R89 = BASE/"R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs"
CF4 = ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def evaluate():
    with np.load(CF4,allow_pickle=False) as f:
        n=np.asarray(f["n_J2000"],float)
        z=np.asarray(f["z_CMB"],float)
        w=1/np.asarray(f["e_dmzp"],float)**2
    M=np.einsum("ni,aij,nj->na",n,STF,n,optimize=True)
    # PHY01: real nonuniform CF4 window, exactly constructed quadrupole.
    # Project onto a monopole+dipole alone; this describes apparent leakage,
    # NOT a cosmological shear measurement.
    X=np.column_stack([np.ones(len(n)),n])
    qtest=M[:,0]
    alpha=np.linalg.solve((X.T*w)@X,(X.T*w)@qtest)
    # For a uniform full sky, <n_i n_j n_k> = 0 and this dipole is zero.
    r01={"carrier":"actual CF4 sky directions/weights; injected STF basis amplitude 1",
         "masked_monopole":float(alpha[0]),"masked_leakage_dipole_norm":float(np.linalg.norm(alpha[1:])),
         "uniform_sphere_dipole_exact":0.0,"science_status":"DIAGNOSTIC_CONDITIONAL"}
    # PHY02: exact Gram-based positivity of nonnegative weighted photon directions.
    cov=(n.T*w)@n/float(w.sum())
    e=np.linalg.eigvalsh(cov)
    r02={"moment_matrix_min_eigen":float(e[0]),"sum_eig":float(np.sum(e)),
         "w_nonnegative":bool(np.all(w>=0)), "identity":"v^T <n n^T> v = <(v.n)^2> >=0",
         "photon_hierarchy":"NOT_MEASURED","science_status":"GEOMETRIC_EXAMPLE_ONLY"}
    # PHY03: actual R89 radio observed vs Ellis-Baldwin expected dipole.
    radio=json.loads((R89/"G04_RADIO_FRAME/SOLVER_FREE_RESEARCH_RESULT.json").read_text())
    r03={}
    for survey,d in radio["part_a_ellis_baldwin_and_ladders"].items():
        first=d["ellis_baldwin_segments"][0]
        r03[survey]={"d_obs":first["d_obs_at_c2"],"dkin_assumed_alpha075":first["d_kin_alpha0p75"],
                     "ratio":first["excess_ratio_d_obs_over_d_kin"],"source_null":"UNQUALIFIED"}
    # PHY04: selected Gaia VSH E2/B2; no optical distance/normal-frame calibration.
    gaia=json.loads((R89/"G03_GAIA/SOLVER_FREE_RESEARCH_RESULT.json").read_text())
    rob=gaia["part_c_robust_covariance_and_vlba"]["nside2_48patch_sandwich_jackknife"]
    r04={"E2_jackknife_chisq_nominal":rob["jackknife_robust_wald_subspaces"]["E2_5D"]["wald_chi2"],
         "B2_jackknife_chisq_nominal":rob["jackknife_robust_wald_subspaces"]["B2_5D"]["wald_chi2"],
         "pure_homogeneous_scalar_shear_B2_theory":0.0,
         "cosmological_B2_rejection":"NOT_AVAILABLE_WITHOUT_SOURCE_SPECIFIC_NULL"}
    # PHY05: exceptional VI_-1/9 momentum map rank discontinuity.
    mex=codazzi_stf((0,1,-4),2/3)
    mgeneric=codazzi_stf((0,1,-4),.6)
    r05={"VI_exception_rank":int(np.linalg.matrix_rank(mex,tol=1e-10)),
         "VI_generic_rank":int(np.linalg.matrix_rank(mgeneric,tol=1e-10)),
         "VI_exception_right_nullity":int(null_space(mex).shape[1]),
         "background_convention":"orthonormal Class B N.a=0, a^2=|n2*n3|/9"}
    # PHY06: noncommuting shear and generator rotates shape eigenframe at fixed chi.
    S=np.diag([.13,-.08,-.05])
    D=np.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,0.]])
    comm=D@S-S@D
    skew=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,0.]])
    th=.2
    from scipy.linalg import expm
    R=expm(th*skew)
    Sr=R@S@R.T
    chi=lambda A: float(np.sqrt(6)*np.trace(A@A@A)/(np.trace(A@A)**1.5))
    r06={"commutator_norm":float(np.linalg.norm(comm)),
         "rotation_preserves_chi_abs_error":abs(chi(S)-chi(Sr)),
         "rotated_tensor_change_frob":float(np.linalg.norm(S-Sr)),
         "interpretation":"eigenframe rotates despite unchanged conjugacy-invariant shape; no physical derivative inferred"}
    # PHY07: radial 12D exact source-design rank split using 35970 real group directions and z.
    c=299792.458; h0=70.
    rz=c*z/h0
    if np.min(rz)<=0: raise ValueError("CF4 selected z must be positive")
    X9=np.column_stack([np.ones(len(n)),n,M])
    X12=np.column_stack([X9,(100/rz)[:,None]*n])
    # Weighted Fisher not a physical covariance. Normalize columns for rank/condition.
    def svals(A):
        W=np.sqrt(w)[:,None]*A
        W=W/np.linalg.norm(W,axis=0)
        return np.linalg.svd(W.T@W,compute_uv=False)
    s9,s12=svals(X9),svals(X12)
    r07={"n_real_selected_groups":len(n),"z_range":list(map(float,(np.min(z),np.max(z)))),
         "rank9":int(np.sum(s9>1e-10)), "rank12":int(np.sum(s12>1e-10)),
         "min_eigen9":float(s9[-1]),"min_eigen12":float(s12[-1]),
         "F12_condition":float(s12[0]/s12[-1]),
         "fixed_r_limit_rank9":9,"radial_transport_assumption":"observer-frame 100 Mpc/r response, model-dependent"}
    return {"schema":"htt.r90.seven_solverfree_phy_cases/1",
       "sources":{"CF4_selected_sha256":sha(CF4),
                  "G04_radio_sha256":sha(R89/"G04_RADIO_FRAME/SOLVER_FREE_RESEARCH_RESULT.json"),
                  "G03_gaia_sha256":sha(R89/"G03_GAIA/SOLVER_FREE_RESEARCH_RESULT.json")},
       "physics_status":"SOURCE_CONDITIONAL_AND_CONSTRUCTED_NOT_JOINT_PHYSICAL",
       "physical_Pi":None,"physical_GF":None,
       "PHY-01":r01,"PHY-02":r02,"PHY-03":r03,"PHY-04":r04,
       "PHY-05":r05,"PHY-06":r06,"PHY-07":r07}
