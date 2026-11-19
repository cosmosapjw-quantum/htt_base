"""R77 seven physical PHY cross-view route checks: source-qualified and read-only.

Run from htt_base root:
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R77_SEVEN_PHY_CROSSVIEW_20261119/verify_seven.py > docs/research_program/observational_publication_20261015/R77_SEVEN_PHY_CROSSVIEW_20261119/RESULTS.json

No new common physical multi-instrument likelihood, cosmic posterior or discovery.
Original CF4 table4 is 38053 groups, NOT identical to R61's selected 35970.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.integrate import quad
from scipy.special import roots_legendre
from scipy.stats import chi2
from scripts.r68.fiveview_geometry import E,stf_matrix,stf_shape

ROOT=Path("docs/research_program/observational_publication_20261015")
CF4_RAW=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
R61=ROOT/"R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/IMAGES/KINEMATIC_IMAGES.json"
R65=ROOT/"R65_DIPOLE_ANOMALY_20261117/RESULTS/INTERPRETATION_SUMMARY.json"
R65N=ROOT/"R65_DIPOLE_ANOMALY_20261117/RESULTS/NVSS_CONDITIONAL_CARRIERS.npz"
R66=ROOT/"R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"
R73=ROOT/"R73_P1_P4_TYPED_PHYSICAL_FIVEVIEW_20261119/RESULTS.json"
R74=ROOT/"R74_P4_SOURCE_SCORE_FIVEVIEW_20261119/RESULTS.json"
R75=ROOT/"R75_P5_LIE_TILT_FIVEVIEW_20261119/RESULTS.json"
R76=ROOT/"R76_P6_COVARIANT_DRIFT_FIVEVIEW_20261119/RESULTS.json"
REQUIRED=(CF4_RAW,R61,R65,R65N,R66,R73,R74,R75,R76)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def cf4():
    a=[]
    for line in CF4_RAW.open():
        try:
            r=float(line[21:26]);l=np.deg2rad(float(line[101:109]));b=np.deg2rad(float(line[110:118]))
            if r>0 and np.isfinite(r+l+b):
                a.append([r,np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)])
        except (ValueError,IndexError):
            pass
    a=np.asarray(a,float)
    assert a.shape==(38053,4)
    n=a[:,1:]
    np.testing.assert_allclose(np.linalg.norm(n,axis=1),1,rtol=0,atol=1e-13)
    return a

def angular(n):
    q=np.einsum("ni,aij,nj->na",n,E,n)
    return np.column_stack([np.ones(len(n)),n,q])

def sigma(x):
    return stf_matrix(np.asarray(x,float))

def ph01(a):
    # Exact full-group selected geometry, CMB axis given in the SAME galactic frame as table4.
    a=a[(a[:,0]>=40)&(a[:,0]<400)]
    n=a[:,1:]
    l,b=np.deg2rad([264.021,48.253])
    p=np.array([np.cos(l)*np.cos(b),np.sin(l)*np.cos(b),np.sin(b)])
    h=(n@p)>0
    assert min(np.sum(h),np.sum(~h))>1000
    mp=np.mean(n[h],axis=0);mm=np.mean(n[~h],axis=0)
    Mp=n[h].T@n[h]/np.sum(h);Mm=n[~h].T@n[~h]/np.sum(~h)
    delta=Mp-Mm
    assert abs(np.trace(delta))<2e-13
    vals,U=np.linalg.eigh(delta)
    shear_amp=.03
    # max S:delta for Type V zero-normal-flux sigma eigenvalues [-s,0,+s].
    S=U@np.diag([-shear_amp,0.,shear_amp])@U.T
    S-=np.eye(3)*np.trace(S)/3
    a_direction=U[:,1] # zero eigenvector, Type V structure a aligned here
    assert np.linalg.norm(S@a_direction)<1e-13
    chi=float(stf_shape(S)["signed_chi"])
    assert abs(chi)<1e-13
    leak=float(np.einsum("ij,ij",S,delta))
    sharp=float(shear_amp*(vals[-1]-vals[0]))
    np.testing.assert_allclose(leak,sharp,rtol=1e-13,atol=1e-15)
    v=np.einsum("ni,ij,nj->n",n,S,n)
    direct=float(np.mean(v[h])-np.mean(v[~h]))
    assert abs(leak-direct)<4e-14
    # Random 500 SO3 orientations cannot exceed exact von Neumann bound.
    rng=np.random.default_rng(777)
    max_orient=-1e50
    for _ in range(500):
        R,_=np.linalg.qr(rng.normal(size=(3,3)))
        Srot=R@np.diag([-shear_amp,0,shear_amp])@R.T
        max_orient=max(max_orient,np.sum(Srot*delta))
    assert max_orient<=sharp+1e-13
    full_sky_zero_flux_F=0.5
    return {"source":"original CF4 table4 38053 full groups, conditional subset 40-400 Mpc; NOT identical to R61 35970 selected",
      "selected_n":len(n),"hemisphere_pixel_counts":[int(h.sum()),int((~h).sum())],
      "CMB_axis_galactic_deg":[264.021,48.253],
      "mask_direction_mean_difference":(mp-mm).tolist(),
      "mask_quadrupole_window_difference_eigenvalues":vals.tolist(),
      "TypeV_zero_total_flux_signed_chi":chi,
      "TypeV_zero_flux_FOmega":full_sky_zero_flux_F,
      "TypeV_shear_eigen_amplitude":shear_amp,
      "sharp_max_even_to_odd_mask_leakage":sharp,
      "explicit_zero_flux_shear_leakage":leak,
      "explicit_mask_mean_direct_check":direct,
      "random_SO3_500_max_leakage":max_orient,
      "physical_scope":"Type V j_total=0 conditional shear shape and actual CF4 geometric window; no source normal-shear measurement"}

def ph02():
    d=json.loads(R66.read_text())
    old=json.loads(R75.read_text())
    out={}
    for release in ("PR3","PR4"):
        x=d["nonlinear"][release]["radiation_moment_bundle"]["pi5_over_rho"]
        S=sigma(x);P=np.eye(3)/3+S
        vals,U=np.linalg.eigh(P)
        assert np.min(vals)>0
        eta=.2;OmegaN=.3
        f=.8*np.sqrt(vals[-1])*U[:,-1]
        u=eta*f
        E=float(u@np.linalg.solve(P,u)/eta**2)
        assert abs(E-.64)<3e-13
        L=-3*OmegaN*u
        combined=float(L@np.linalg.solve(P,L)/(9*OmegaN**2*eta**2))
        assert abs(combined-.64)<4e-13
        out[release]={
          "actual_R66_normalized_STF5":list(map(float,x)),
          "P_eigenvalues":vals.tolist(),"P_positive":True,
          "max_normal_photon_only_flux_ratio_to_rho_total_for_eta_0p2":float(eta*np.sqrt(vals[-1])),
          "synthetic_eta_rho_gamma_over_total":eta,
          "synthetic_normal_photon_flux":u.tolist(),
          "synthetic_OmegaN":OmegaN,
          "P_positive_schur_ratio":E,
          "Einstein_Codazzi_photon_only_joint_ellipsoid_ratio":combined,
          "same_frame_flux_observed":False}
    # Exceptional VI_-1/9 additional left-null eliminates one flux direction.
    left=np.array([0.,3.,3.]); allowed=np.array([0.,1.,-1.])/np.sqrt(2)
    excluded=np.array([0.,1.,1.])/np.sqrt(2)
    assert abs(left@allowed)<1e-15 and abs(left@excluded)>1
    return {"R66_same_sky_finiteband_photon_pressure":out,
      "VI_exceptional_flux_left_null_constraint":left.tolist(),
      "normal_flux_allowed_unit_example":allowed.tolist(),
      "normal_flux_excluded_unit_example":excluded.tolist(),
      "multi_fluid_counterexample":"opposing matter flux invalidates photon-only total momentum substitution",
      "original_R75_Codazzi_exceptional_rank":old["source_all_Bianchi_atlas"]["VI_minus_1_over_9"]["Codazzi_signed_STF5_to_normal_flux_rank"]}

def ph03():
    r66=json.loads(R66.read_text())
    r65=json.loads(R65.read_text())
    beta=369.82/299792.458
    vec=np.array([beta,0.,0.])
    k=3.8254286125;kap=0.
    A=(k*k+k+kap)/2
    B=np.outer(vec,vec)-np.eye(3)*(vec@vec)/3
    Sg=4*B/(3+beta**2)
    Q=A*B
    np.testing.assert_allclose(Q,A*(3+beta**2)/4*Sg,rtol=1e-14,atol=1e-21)
    m=4*beta/(3+beta**2)
    inv=3*m/(2+np.sqrt(4-3*m*m))
    assert abs(inv-beta)<2e-17
    sign=float(stf_shape(Sg)["signed_chi"])
    assert abs(sign-1)<1e-14
    observed={}
    for release in ("PR3","PR4"):
        S=sigma(r66["nonlinear"][release]["radiation_moment_bundle"]["pi5_over_rho"])
        ch=float(stf_shape(S)["signed_chi"])
        assert ch<0
        observed[release]={"R66_signed_chi_finiteband":ch,
            "can_be_exact_pure_boost_stress_if_source_matching_yes":False,
            "physical_boost_significance_calibrated":False}
    return {"same_frame_CMB_speed_synthetic_beta":beta,"radio_first_order_k":k,
      "count_selection_A_coefficient":A,"photon_flux_m_norm":m,
      "m_to_beta_inverse":inv,
      "pure_boost_signed_STF_chi":sign,
      "pure_boost_Q_count_Frobenius":float(np.linalg.norm(Q)),
      "exact_radio_to_photon_STF_error":float(np.linalg.norm(Q-A*(3+beta**2)/4*Sg)),
      "R65_saved_theoretical_peak_bin_k_alpha_0p75":r65["nvss_tables"][0]["peak_response_diagnostics"]["0.75"]["response"],
      "actual_R66_finiteband_stress":observed,
      "common_physical_3D_beta_observed":False}

def sphere():
    mu,wm=roots_legendre(96)
    phi=np.arange(192)*2*np.pi/192
    mm,pp=np.meshgrid(mu,phi,indexing="ij")
    n=np.column_stack([np.sqrt(1-mm.ravel()**2)*np.cos(pp.ravel()),
                       np.sqrt(1-mm.ravel()**2)*np.sin(pp.ravel()),mm.ravel()])
    wt=np.repeat(wm/(2*192),192)
    return n,wt

def ph04():
    n,wt=sphere()
    # Canonical class A symmetric spatial Lie N, dimensionless \bar N = cN/H0.
    Nbar=np.diag([.013,-.017,.004])
    Nbar=Nbar-np.eye(3)*np.trace(Nbar)/3
    S=np.diag([-.02,0.,.02])
    Vb=-np.cross(n,n@Nbar.T)
    Es=n@S.T-n*(np.einsum("ni,ij,nj->n",n,S,n))[:,None]
    normb=float(np.dot(wt,np.sum(Vb*Vb,axis=1)))
    analytic=float(np.trace(Nbar@Nbar)/5)
    assert abs(normb-analytic)<1e-14
    cross=float(np.dot(wt,np.einsum("ni,ni->n",Vb,Es)))
    assert abs(cross)<2e-15
    # Local Type V N=0 and I N=0 have no direct B2, unlike generic Class A.
    g=json.loads(R76.read_text())["R69_Gaia_VSH_actual_source"]["results"]
    assert g["quality"]["E2_B2_profiled_design_maxcanonical"]<.1
    assert g["quality_north"]["E2_B2_profiled_design_maxcanonical"]>.8
    return {"toy_dimensionless_Nbar_stf":Nbar.tolist(),
       "normal_Lie_B2_dimensionless_rate_squared_skymean":normb,
       "exact_STF_prediction":analytic,
       "skymean_B2_dot_local_E2":cross,
       "TypeI_TypeV_Nzero_direct_B2":True,
       "R69_actual_Gaia_quality_EB2_maxFisherCanonical":g["quality"]["E2_B2_profiled_design_maxcanonical"],
       "R69_actual_Gaia_north_EB2_maxFisherCanonical":g["quality_north"]["E2_B2_profiled_design_maxcanonical"],
       "R69_actual_Gaia_south_EB2_maxFisherCanonical":g["quality_south"]["E2_B2_profiled_design_maxcanonical"],
       "Gaia_B2_formal_chi2_p":g["quality"]["B2_formal_p_naive"],
       "Gaia_B2_patch_nominal_p":g["quality"]["exploratory_patch_B2_nominal_p_not_cosmic"],
       "normal_to_Gaia_physical_optical_transfer":False}

def ph05():
    d=json.loads(R75.read_text())
    M=np.array([[-3,0,0,0,-6],[0,0,-3,3,0],[0,0,3,-3,0]],float)
    assert np.linalg.matrix_rank(M)==2
    left=np.array([0.,3.,3.])
    np.testing.assert_allclose(left@M,np.zeros(5),atol=1e-14)
    Sigma=np.array([-2.,0.,0.,0.,1.])
    np.testing.assert_allclose(M@Sigma,np.zeros(3),atol=1e-14)
    Omega=.4
    D=np.column_stack([M/(3*Omega),np.eye(3)])
    C=np.diag([.04**2]*5+[.03**2]*3)
    Cr=D@C@D.T
    assert np.linalg.matrix_rank(Cr)==3
    # Independent synthetic source measurements: residual covariance full rank
    # even though Lie shear->normal flux map has rank2.
    rng=np.random.default_rng(77)
    samples=rng.multivariate_normal(np.zeros(8),C,9000)
    residual=samples@D.T
    T=np.einsum("ni,ij,nj->n",residual,np.linalg.inv(Cr),residual)
    assert abs(float(np.mean(T))-3)<.09
    assert abs(float(np.mean(T>chi2.ppf(.95,3)))-.05)<.013
    dposter=d["actual_R49_source_posterior_geometry"]
    return {"exceptional_VI_m1_9_signed_shear_to_flux_rank":2,
      "exceptional_M_signed_STF5_to_u":M.tolist(),
      "exceptional_left_normal_flux_constraint":left.tolist(),
      "zero_flux_signed_sigma_nonzero_example":Sigma.tolist(),
      "source_R49_posterior_chi_median":dposter["posterior_shear_signed_chi_quantiles_05_16_50_84_95"][2],
      "source_R49_posterior_FOmega_median":dposter["posterior_shear_intrinsic_fullsky_FOmega_quantiles_05_16_50_84_95"][2],
      "synthetic_independent_joint_noise_residual_covariance_rank":int(np.linalg.matrix_rank(Cr)),
      "synthetic_gaussian_Tmean":float(np.mean(T)),
      "synthetic_gaussian_T95tail":float(np.mean(T>chi2.ppf(.95,3))),
      "actual_independent_normal_j_source":False}

def ph06():
    H=.1
    S=np.diag([-.03,-.01,.04])
    D=np.zeros((3,3))
    D[0,1]=D[1,0]=.01
    driver=-3*H*S+D
    comm=float(np.linalg.norm(S@D-D@S))
    assert comm>1e-5
    def chi(A):return float(stf_shape(A)["signed_chi"])
    I2=float(np.trace(S@S));I3=float(np.trace(S@S@S))
    chidot=3*np.sqrt(6)/I2**1.5*(np.trace(S@S@D)-(I3/I2)*np.trace(S@D))
    assert abs(chidot)<2e-13
    h=1.e-4
    deriv=(chi(S+h*driver)-chi(S-h*driver))/(2*h)
    assert abs(deriv)<1e-7,(deriv,chidot)
    eig0,U0=np.linalg.eigh(S)
    eig1,U1=np.linalg.eigh(S+h*driver)
    # Pairwise projector drift, not eigenvector sign.
    dproj=float(np.linalg.norm(np.outer(U1[:,0],U1[:,0])-np.outer(U0[:,0],U0[:,0])))
    assert dproj>1e-5
    # Two smooth positive radiation skies same low moments and different future response
    s=.07
    results={}
    P4=lambda mu:(35*mu**4-30*mu**2+3)/8
    for eps in (0.,1.):
        p=lambda mu:(1+eps*P4(mu))/2
        mean2=quad(lambda mu:mu**2*p(mu),-1,1,epsabs=1e-13)[0]
        assert abs(mean2-1/3)<2e-14
        mean4=quad(lambda mu:mu**4*p(mu),-1,1,epsabs=1e-13)[0]
        dotS=-s*(5/9-mean4)
        theory=-16*s/45+8*eps*s/315
        assert abs(dotS-theory)<5e-14
        frac=2*quad(p,.9,1,epsabs=1e-13)[0]
        F_theory=.1+.05707125*eps
        assert abs(frac-F_theory)<3e-13
        results[str(eps)]={"same_initial_f_and_STF5_zero":True,
            "actual_kinetic_synthetic_cap_F":frac,
            "instantaneous_dS_gamma_zz":dotS}
    return {"Einstein_shear_initial_chi":chi(S),
      "Einstein_driver_noncommutator_norm":comm,
      "chi_time_derivative_exact":chidot,
      "chi_time_derivative_finite_difference":deriv,
      "signed_eigenframe_projector_change_at_dt":dproj,
      "photon_nonclosed_smooth_positive_sky_cases":results,
      "physical_Boltzmann_time_solution_fully_integrated":False}

def ph07(a):
    r=a[:,0];n=a[:,1:]
    results={}
    for low,high in ((40,400),(80,220),(140,220)):
        select=(r>=low)&(r<high)
        rr=r[select];nn=n[select]
        B=angular(nn)
        X=np.column_stack([B,(100/rr)[:,None]*nn])
        norm=np.linalg.norm(X,axis=0)
        M=X/norm
        singular=np.linalg.svd(M,full_matrices=False,compute_uv=False)
        rank=int(np.sum(singular>1e-10*singular[0]))
        condition=float(singular[0]/singular[-1])
        assert rank==12
        # Same actual direction sky, artificially constant radius -> rank9.
        X_const=np.column_stack([B, (100/150)*nn])
        Sc=np.linalg.svd(X_const,full_matrices=False,compute_uv=False)
        rc=int(np.sum(Sc>1e-10*Sc[0]))
        assert rc==9
        results[f"{low}-{high}"]={"actual_unweighted_CF4_table4_n":len(nn),
           "actual_geometric_rank12":rank,"column_normalized_condition":condition,
           "synthetic_single_radius_rank":rc,
           "physical_source_covariance_provided":False}
    rad=json.loads(R65.read_text())
    radio_k=rad["nvss_tables"][0]["peak_response_diagnostics"]["0.75"]["response"]
    assert len(radio_k)==3 and min(np.diff(radio_k))>0
    rad_n=json.loads(R74.read_text())["signed_three_bin_fits"]["original_pure_dipole_vs_dipole_plus_free_STF"]["base64_dipole"]
    return {"CF4_full_group_geometric_radial_leverage":results,
      "source_CF4_R61_selected_sample_n":35970,
      "source_CF4_full_table4_n":len(a),
      "radio_source_k_assumed_alpha_0p75":radio_k,
      "radio_working_fixed_k_common_residual_p":rad_n["fixed_k_Pi_conditional_chisquare2"],
      "common_physical_beta_and_CF4_radio_cross_covariance_available":False}

def main():
    for f in REQUIRED:
        assert f.is_file(),f
    a=cf4()
    results={
      "PHY-01":ph01(a),
      "PHY-02":ph02(),
      "PHY-03":ph03(),
      "PHY-04":ph04(),
      "PHY-05":ph05(),
      "PHY-06":ph06(),
      "PHY-07":ph07(a)}
    return {"schema":"htt.r77.seven_cross_phy_theorems/1",
      "source_sha256":{str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f):sha(f) for f in REQUIRED},
      "source_frame":"original CF4 Galactocentric galactic l,b and distance; R65/Gaia ICRS separate; physical joint frame transfer not applied",
      "scientific_evidence":"7 conditional derivations, 7 finite original-data/synthetic route checks; NOT cross-probe physical cosmological likelihood",
      "results":results,
      "original_six_paper_42_science_DAG_unchanged":True}
if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False))
