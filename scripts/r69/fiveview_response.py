"""R69 physically specialized x -> (Q, Pi, F, G_F) calculations.

Each statistic is evaluated ONLY when its extra physical/statistical inputs
are present. NO universal x-only law exists. Physical response and the
working Gaussian law are deliberately separate. No new anisotropy inference.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2
from scripts.r68.fiveview_geometry import (
    stf_matrix, stf_coordinates, stf_shape, radiation_stress_gauge
)


def gaussian_null(x,mean,cov):
    """Tail of specified fixed-mean, full-rank Gaussian coefficient law."""
    x,mean,C=np.asarray(x,float),np.asarray(mean,float),np.asarray(cov,float)
    if x.shape!=mean.shape or C.shape!=(x.size,x.size):
        raise ValueError("Gaussian source dimensions mismatch")
    if not np.allclose(C,C.T,atol=1e-13) or np.linalg.eigvalsh(C).min()<=0:
        raise ValueError("A qualified positive definite covariance is required")
    delta=x-mean
    T=float(delta@np.linalg.solve(C,delta))
    return {"Q_stat_sqrt_chi2":float(np.sqrt(T)),"wald":T,
            "chi2_df":x.size,"Pi_upper_tail":float(chi2.sf(T,x.size)),
            "law":"fixed multivariate Gaussian N(mean,cov) as declared; not a universal astrophysical null"}


def interval_occupancy(x,radius,lo,hi):
    """Uniform-measure F on one finite physical interval, confidence interval E_x."""
    if radius<0 or not lo<hi:raise ValueError("Finite physical body and radius required")
    inter=max(0.,min(hi,x+radius)-max(lo,x-radius))
    return {"F_uniform_1d":inter/(hi-lo),"confidence_event":[x-radius,x+radius],
            "physical_body":[lo,hi],
            "measure":"Lebesgue uniform on explicitly declared physical 1D body"}


def contrast_covariance(Cii,Cjj,Cij,T):
    Cii,Cjj,Cij,T=map(lambda x:np.asarray(x,float),(Cii,Cjj,Cij,T))
    return Cjj+T@Cii@T.T-T@Cij-Cij.T@T.T


def kinetic_flux_stress_gauge(f,S):
    """Exact Minkowski gauge of normalized angular radiation first+second moments.

    x=(f,S), f=q/(rho c)=<n>, S=pi/rho=<nn>-I/3.
    The physical K is the PSD moment cone section
       M=[[1,f.T],[f,I/3+S]] >=0,
    trace S=0. Equiv I/3+S-ff.T >=0.
    Gauge Q(x)=min t>=0 s.t. [[t,f.T],[f,tI/3+S]]>=0,
    hence -lambda_min([[0,sqrt3 f.T],[sqrt3 f,3S]]).
    This is stronger than stress positivity alone and includes dipole flux.
    """
    f=np.asarray(f,float)
    if f.shape!=(3,) or not np.all(np.isfinite(f)):
        raise ValueError("Normalized radiation flux needs finite 3-vector")
    S=np.asarray(S,float)
    stf_coordinates(S)
    B=np.zeros((4,4))
    B[0,1:]=np.sqrt(3)*f
    B[1:,0]=np.sqrt(3)*f
    B[1:,1:]=3*S
    Q=max(0.,-float(np.linalg.eigvalsh(B)[0]))
    C=np.eye(3)/3+S-np.outer(f,f)
    return {"Q_kinetic_moment_body":Q,
            "Q_stress_only":float(radiation_stress_gauge(S)),
            "P_minus_ffT_min_eigenvalue":float(np.linalg.eigvalsh(C)[0]),
            "physically_admissible_first_second_moments":bool(np.linalg.eigvalsh(C)[0]>=-1e-12),
            "units":"f dimensionless flux/(rho c), S dimensionless stress/rho",
            "reference":"angular distribution I(n)>=0; first and second photon direction moments; frame fixed"}


def kinetic_Q_susceptibility(f,S,df,dS):
    """Physical gauge derivative when the minimal eigenvalue is simple.

    If Q_gamma>0, B(f,S) has a *simple* smallest eigenvalue, then
    dot Q_gamma = -w.T dot B w, w the normalized min eigenvector.
    df/dt and dS/dt must come from a source-qualified Boltzmann
    hierarchy. At zero gauge or eigenvalue collision: NOT_DIFFERENTIABLE
    or UNRESOLVED; a numerical value must not be promoted to a theorem.
    """
    f,df=np.asarray(f,float),np.asarray(df,float)
    S,dS=np.asarray(S,float),np.asarray(dS,float)
    if f.shape!=(3,) or df.shape!=(3,):
        raise ValueError("Three-vector flux and its physical derivative required")
    stf_coordinates(S); stf_coordinates(dS)
    B=np.zeros((4,4),float);Bt=np.zeros((4,4),float)
    B[0,1:]=np.sqrt(3)*f;B[1:,0]=np.sqrt(3)*f;B[1:,1:]=3*S
    Bt[0,1:]=np.sqrt(3)*df;Bt[1:,0]=np.sqrt(3)*df;Bt[1:,1:]=3*dS
    ev,U=np.linalg.eigh(B)
    scale=max(1.,np.max(np.abs(ev)),np.linalg.norm(Bt))
    if ev[0]>=0:
        return {"status":"ZERO_GAUGE_KINK_OR_INTERIOR","Q":max(0.,-float(ev[0])),"dQ":None}
    gap=ev[1]-ev[0]
    if gap<=1e-10*scale:
        return {"status":"NONDIFFERENTIABLE_DEGENERATE_EIGENVALUE","Q":-float(ev[0]),"dQ":None}
    w=U[:,0]
    return {"status":"SIMPLE_ACTIVE_EIGENVALUE_CONDITIONAL",
            "Q":-float(ev[0]),"dQ":-float(w@Bt@w),
            "spectral_gap":float(gap),
            "law":"requires physically sourced df/dt,dS/dt; not computable from one instantaneous x"}


def independent_photon_direction_null(f,S,N):
    """Large-N CLT for N independent photon directions from an isotropic sky.

    Not applicable to 1.6-million *correlated sky pixels*, cosmic variance,
    Planck/Commander CMB or frequency-dependent instrument measurements.
    If each direction n_k is sampled iid from uniform S², then
    sqrt(N) (f, S_A) has covariance diag(I3/3, (2/15)I5).
    The Wald statistic asymptotically has chi²8, not exact finite-N.
    """
    f=np.asarray(f,float)
    S=np.asarray(S,float)
    stf_coordinates(S)
    if f.shape!=(3,) or N<=0 or int(N)!=N:raise ValueError("N iid directions required")
    T=float(N*(3*np.dot(f,f)+(15/2)*np.sum(S*S)))
    return {"Q_CLT_sqrt_T":float(np.sqrt(T)),"T":T,"Pi_asymptotic_chi2_8":float(chi2.sf(T,8)),
            "law":"N iid uniformly sampled photon directions, asymptotic central limit; NOT real CMB sky law"}


def radiation_cap_nonuniqueness(threshold=.9):
    """Same x=(f=0,S=0), two different physical angular intensity measures.

    A uniform sphere and six symmetric beams along axes have identical
    normalized first and second moments, yet different cap occupancy.
    E={|n_z|>threshold}. This proves x alone cannot determine F.
    """
    if not 0<threshold<1:raise ValueError("cap parameter must be 0<t<1")
    axes=np.concatenate([np.eye(3),-np.eye(3)])
    f=axes.mean(axis=0)
    S=axes.T@axes/6-np.eye(3)/3
    assert np.allclose(f,0) and np.allclose(S,0)
    return {"same_x_flux":[0.,0.,0.],"same_x_STF5":[0.]*5,
            "uniform_sky_cap_F":float(1-threshold),
            "six_beam_cap_F":float(1/3),
            "cap_event":"abs(n_z)>threshold, 0<threshold<1",
            "condition":"Both measures nonnegative, normalized, with exactly equal first two moments",
            "theorem":"F of an angular cap is not identified from x=(f,S) without angular distribution or a closure"}


def maximum_entropy_axisymmetric_photon_closure(beta=.3, cap=.9):
    """Conditional maximum-entropy angular intensity for exact boosted-photon moments.

    Given only f=<mu> and s=<mu^2-1/3>, choose one angular distribution
    p_ME(mu) proportional exp(lambda*mu+nu*(mu^2-1/3)).
    This is an ENTROPY CLOSURE, not the unique radiation distribution
    and not a Boltzmann solution. Compare to exact boost intensity
    p_exact(mu) proportional (1-beta*mu)^(-4). Its higher angular moments
    and F(cap) need not agree despite exact matching of f,s.
    """
    from scipy.optimize import root
    from numpy.polynomial.legendre import leggauss
    if not 0<=beta<1 or not 0<cap<1:
        raise ValueError("Subluminal beta and angular cap required")
    mu,w=leggauss(256)
    tw=np.column_stack((mu,mu**2-1/3))
    want=np.array([4*beta/(3+beta**2),
                   (2/3)*(4*beta**2/(3+beta**2))])
    def moments(par,extra=False):
        v=tw@par
        w2=w*np.exp(v-np.max(v))
        p=w2/np.sum(w2)
        mean=p@tw
        cov=(tw-mean).T@(p[:,None]*(tw-mean))
        return (mean,cov,p)
    def fun(par):
        mean,cov,p=moments(par)
        return mean-want
    sol=root(fun,np.zeros(2),tol=1e-12)
    if not np.linalg.norm(fun(sol.x))<1e-11:
        raise ArithmeticError("Maximum-entropy moment fit not certified")
    _,_,pme=moments(sol.x)
    exact=w*(1-beta*mu)**(-4)
    exact/=exact.sum()
    # The angular cap has two DISCONTINUOUS indicator edges. Whole-domain
    # Gaussian nodes with mask(cap) are biased; integrate each cap separately.
    from scipy.integrate import quad
    a,b=sol.x
    def exp_me(z):
        return np.exp(a*z+b*(z*z-1/3))
    def exp_exact(z):
        return (1-beta*z)**(-4)
    def cap_integral(fun):
        return quad(fun,-1.,-cap,epsabs=2e-13,epsrel=2e-13)[0]+quad(fun,cap,1.,epsabs=2e-13,epsrel=2e-13)[0]
    F_exact=float(cap_integral(exp_exact)/quad(exp_exact,-1.,1.,epsabs=2e-13,epsrel=2e-13)[0])
    F_me=float(cap_integral(exp_me)/quad(exp_me,-1.,1.,epsabs=2e-13,epsrel=2e-13)[0])
    third_exact=float(exact@(mu**3))
    third_me=float(pme@(mu**3))
    return {"beta_boost_exact":beta,"cap_abs_mu_greater":cap,
            "x_flux_axial":want[0],"x_STF_zz":want[1],
            "max_entropy_lambda_nu":sol.x.tolist(),
            "moment_residual_max_abs":float(np.max(np.abs(fun(sol.x)))),
            "F_cap_exact_boost":F_exact,"F_cap_max_entropy_closure":F_me,
            "F_cap_closure_error":F_me-F_exact,
            "third_moment_exact_boost":third_exact,
            "third_moment_max_entropy":third_me,
            "third_moment_closure_error":third_me-third_exact,
            "status":"EXPLICIT_MAXENT_CLOSURE_BENCHMARK_NOT_OBSERVED_CMB"}


def sky_solid_angle_F(S,d=None,nside=128,threshold=0.):
    """Physical/geometric angular occupancy of a named signed direction field.

    x=(d,S) sets u(n)=d.n+n.S.n. The chosen event is u(n)>threshold.
    F_sky=area{n:u(n)>threshold}/4pi uses canonical round-sphere area,
    NOT radiation-energy weighting, parameter-prior occupancy, or a p-value.
    The output is HEALPix equal-area *pixel-center approximation* and
    nside doubling should be checked for discontinuity/boundary error.
    """
    import healpy as hp
    S=np.asarray(S,float)
    stf_coordinates(S)
    d=np.zeros(3) if d is None else np.asarray(d,float)
    if d.shape!=(3,) or not np.all(np.isfinite(d)):
        raise ValueError("Finite signed angular dipole needed")
    if nside<4 or (int(nside)&(int(nside)-1))!=0:
        raise ValueError("HEALPix power-of-two nside >=4")
    ns=hp.nside2npix(nside)
    n=np.array(hp.pix2vec(nside,np.arange(ns))).T
    u=n@d+np.einsum("ni,ij,nj->n",n,S,n)
    if np.linalg.norm(S)+np.linalg.norm(d)==0:
        return {"F_sky_solid_angle":None,"status":"DEGENERATE_ZERO_FIELD_EVENT_NOT_INFORMATIVE",
                "event":"u(n)>threshold"}
    return {"F_sky_solid_angle":float(np.mean(u>threshold)),
            "status":"FINITE_EQUAL_AREA_PIXEL_CENTRE_ESTIMATOR",
            "event":"d.n+n.S.n > threshold, round-sphere area fraction",
            "threshold":float(threshold),"nside":int(nside),"n_pixels":int(ns),
            "minimum_signed_response":float(u.min()),
            "maximum_signed_response":float(u.max())}


def min_spherical_quadratic(S,d):
    """Global sphere quadratic min via scale-independent secular solution.

    Min n.S.n+d.n on |n|=1, symmetric STF S. Rescale by common
    max component magnitude before eigenspace detection and root solving.
    Exposes physical units ONLY at the output, not in rank tolerances.
    """
    S=np.asarray(S,float);d=np.asarray(d,float)
    stf_coordinates(S)
    if d.shape!=(3,) or not np.all(np.isfinite(d)):
        raise ValueError("finite dipole 3-vector required")
    scale=max(float(np.max(np.abs(S))),float(np.max(np.abs(d))))
    if scale==0:
        return {"min_angular_perturbation":0.,
                "min_direction":[1.,0.,0.],"secular_mu":0.,
                "stationarity_residual":0.,"case":"identically_zero"}
    A=S/scale;v=d/scale
    lam,U=np.linalg.eigh(A)
    coeff=U.T@v
    low=lam[0]
    if np.all(v==0):
        n=U[:,0]
        return {"min_angular_perturbation":float(scale*low),
                "min_direction":n.tolist(),"secular_mu":float(scale*low),
                "stationarity_residual":0.,"case":"pure_STF"}
    # Tolerance now depends only on scaled magnitude ~O(1).
    tol=64*np.finfo(float).eps
    minspace=np.abs(lam-low)<=tol
    comp=np.zeros(3);free=~minspace
    comp[free]=-coeff[free]/(2*(lam[free]-low))
    if np.linalg.norm(coeff[minspace])<=tol and np.linalg.norm(comp)<=1+tol:
        compnorm=np.linalg.norm(comp)
        if compnorm>1:
            comp/=compnorm
        else:
            comp[np.flatnonzero(minspace)[0]]=np.sqrt(max(0.,1-comp@comp))
        n=U@comp
        n/=np.linalg.norm(n)
        mu=low
        label="hard_stationary"
    else:
        def f(mu):
            with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
                return np.sum((coeff/(2*(lam-mu)))**2)-1
        width=max(1.,2*np.linalg.norm(v),2*np.linalg.norm(A))
        left=low-width
        while f(left)>0:
            width*=2
            left=low-width
        right=np.nextafter(low,-np.inf)
        if f(right)<=0:
            raise ArithmeticError("Severe near-degenerate secular root: no false certificate")
        mu=brentq(f,left,right,xtol=1e-14,rtol=1e-14)
        comp=-coeff/(2*(lam-mu))
        n=U@comp
        n/=np.linalg.norm(n)
        label="regular_secular"
    objective=scale*(n@A@n+v@n)
    # Physical first-order KKT condition in scaled units. A near-degenerate
    # hard case can be admitted only within its explicitly computed residual.
    stat=np.linalg.norm(2*A@n+v-2*mu*n)
    if stat>1e-9:
        raise ArithmeticError(f"Uncertified spherical stationarity residual={stat:g}")
    return {"min_angular_perturbation":float(objective),
            "min_direction":n.tolist(),"secular_mu":float(scale*mu),
            "stationarity_residual":float(stat),"case":label}



def directional_hubble_gauge(H,d,S):
    """Physics-derived one-sided gauge of positive directional vertex H(n).

    H>0, H(n)=H+d.n+n.S.n, where d=-A/c.
    Q=max_n[-(d.n+n.S.n)]/H, exactly.
    Q<=1 iff all leading directional H(n)>=0; strict positivity needs Q<1.
    For finite redshift, different optical transfer is needed.
    """
    if H<=0:raise ValueError("Positive monopole expansion H required")
    m=min_spherical_quadratic(S,d)
    Q=max(0.,-m["min_angular_perturbation"]/H)
    return {"Q_H_positive_directional_expansion":float(Q),
            "minimum_H_over_H":float(1+m["min_angular_perturbation"]/H),
            "all_directional_leading_expansion_positive":bool(Q<1),
            "minimum_direction":m["min_direction"],
            "solver_case":m["case"],"physical_source":"Heinesen local direction-dependent Hubble vertex, not finite-depth H_D"}


def shear_shape_evolution(S,driver):
    """Exact Fermi-frame derivative of chi(S) from shear evolution

      D_t S = -3 H S + D,  D=8piG*pi_N/c²-c²(3R)_STF
    only for homogeneous geodesic normal Einstein closure used in R62.
    Dimension: S s^-1, driver s^-2, chi_dot s^-1.
    """
    S,driver=np.asarray(S,float),np.asarray(driver,float)
    stf_coordinates(S);stf_coordinates(driver)
    I2=float(np.trace(S@S))
    if I2<=0:
        return {"chi":None,"chi_dot":None,"status":"UNDEFINED_AT_ZERO_SHEAR"}
    I3=float(np.trace(S@S@S))
    shape=stf_shape(S)
    chirate=(3*np.sqrt(6)/I2**1.5) * (np.trace(S@S@driver)-(I3/I2)*np.trace(S@driver))
    comm=np.linalg.norm(S@driver-driver@S)
    return {"chi":float(shape["signed_chi"]),
            "chi_dot_s_inv":float(chirate),
            "commutator_norm_units_s_inv3":float(comm),
            "physical_source":"geodesic homogeneous normal shear+Einstein tracefree; source driver D=(8piG/c²)pi_N-c²(3R)_STF"}


def read_r68_r66(root):
    from scripts.r68.fiveview_geometry import r66_reused_stress
    return r66_reused_stress(root/"R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json")


def atlas_from_previous_data(repo):
    repo=Path(repo)
    root=repo/"docs/research_program/observational_publication_20261015"
    def rd(path):return json.loads((root/path).read_text())
    r66=read_r68_r66(root)
    r65=rd("R65_DIPOLE_ANOMALY_20261117/RESULTS/INTERPRETATION_SUMMARY.json")
    r61=rd("R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/NUMERICAL_SUMMARY.json")
    r62=rd("R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION/log__J2_coefficients.json")
    r64=rd("R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/INTERPRETATION_SUMMARY.json")
    r63=rd("R63_LOCAL_BOOST_GLOBAL_TILT_20261117/RESULTS/INTERPRETATION_SUMMARY.json")
    r69=rd("R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GR_KINETIC_HEMISPHERES.json")
    g69=rd("R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json")
    radiation={}
    for k,v in r66["results"].items():
        S=stf_matrix(v["pi5_over_rho"])
        # The actual q/(rho c) is NOT in the R66 retained-moment bundle;
        # f=0 is an illustration of an unobserved rest-frame condition.
        radiation[k]={"x_actual_pi_over_rho_STF5":v["pi5_over_rho"],
            "x_flux_available":False,
            "Q_stress_physical":float(radiation_stress_gauge(S)),
            "Q_joint_flux_stress":"UNAVAILABLE_WITHOUT_ACTUAL_F",
            "Pi":"UNAVAILABLE_NO_QUALIFIED_COMMANDER_FULL_T_NULL",
            "F":"UNAVAILABLE_NO_CONFIDENCE_EVENT_AND_MEASURE",
            "G_F":"NOT_APPLICABLE_SINGLE_SKY",
            "signed_chi":float(stf_shape(S)["signed_chi"]),
            "F_geometric_sky_stress_positive":sky_solid_angle_F(S,nside=128)["F_sky_solid_angle"],
            "F_geometric_note":"canonical solid-angle fraction where n.S.n>0; NOT radiative energy-weighted occupancy"}
    # Conditional idealized boost makes f available only as comparator
    kin=r69["R66_kinetic_boost_only_diagnostic"]
    b=kin["beta_first_order"]
    n_gal=np.deg2rad([264.021,48.253])
    n=np.array([np.cos(n_gal[1])*np.cos(n_gal[0]),
                np.cos(n_gal[1])*np.sin(n_gal[0]),np.sin(n_gal[1])])
    boost_f=4*b/(3+b*b)*n
    boost_S=stf_matrix(kin["boost_only_reference_STF5"])
    purekin=kinetic_flux_stress_gauge(boost_f,boost_S)
    for k,v in radiation.items():
        S=stf_matrix(v["x_actual_pi_over_rho_STF5"])
        v["Q_joint_assuming_boost_only_flux_not_measured"]=kinetic_flux_stress_gauge(boost_f,S)["Q_kinetic_moment_body"]
    sample_r62=np.asarray(r62["mean"][:5],float)
    S0=stf_matrix(sample_r62)
    pheno_q=directional_hubble_gauge(1.,np.zeros(3),S0)
    # Physical formula is correct ONLY if a physical GR vertex shear was
    # provided. R62 K0 was a finite-depth apparent log-distance coefficient.
    pheno_q["actual_input_scope"]="R62 PHENOMENOLOGICAL RESPONSE, NOT OBSERVED SIGMA/H; Q_H is hypothetical"
    pheno_q["physical_source"]="FORMULA_ONLY_IF_INPUT_IS_LOCAL_GR_VERTEX: Heinesen H(n), not this R62 K0"
    pheno_sky=sky_solid_angle_F(S0,nside=128)
    # Actual R62 J2 Legendre K_j(z) is phenomenological; the F(z) curve is
    # a deterministic angular fraction of the apparent coefficient, NOT a
    # physical G_F with calibrated cross-z uncertainty/transport.
    kseries=np.asarray(r62["mean"],float).reshape(3,5)
    depth_sky=[]
    for z in (.025,.04,.06,.08):
        t=(z-.055)/.045
        kp=(np.polynomial.legendre.legvander(t,2)@kseries).ravel()
        depth_sky.append({"z_cmb":z,"F_sky_apparent":sky_solid_angle_F(stf_matrix(kp),nside=128)["F_sky_solid_angle"]})
    pheno_Q2=gaussian_null(sample_r62,np.zeros(5),np.asarray(r62["covariance"])[:5,:5])
    # A *single-point* R64 exemplar, not a physical all-sky x(z,n)
    ex=r64["exemplars"]["log_mono__J2"][0]
    rp=ex["point"]
    local_q=max(0.,1-rp["denominator"])
    # R65 has a signed 2D difference and its full paired covariance
    src=r65["source_definition_covariance_ablation"]
    radio=gaussian_null(src["actual_delta"],np.zeros(2),np.asarray(src["actual_covariance"]))
    # R69 16-mode Gaia actual sourcewise working covariance
    Gaia=g69["results"]["quality"]
    Gaia16=np.asarray(Gaia["coefs_microasyr"],float)
    GaiaCov=np.asarray(Gaia["formal_cov_microasyr2"],float)
    B2=Gaia16[11:]
    gaia_pi=gaussian_null(B2,np.zeros(5),GaiaCov[11:,11:])
    # R61 11D conditional upper bound for speed, not a speed detection
    v_bound=r61["speed_upper_km_s"]
    speed_radius=v_bound/299792.458
    f_upper=min(1.,speed_radius**3) # Uniform Lebesgue on causal beta ball.
    # Source-less kinematical example with physical gamma+normal stress driver
    # Generic non-axisymmetric toy (axisymmetric chi=±1 is stationary
    # at first order even when the Einstein driver is nonproportional).
    S=stf_matrix(np.array([.002,.001,-.0006,.0002,.0003]))
    D=stf_matrix(np.array([.25,-.17,.06,.12,.04])*1e-5)
    dyn=shear_shape_evolution(S,D)
    # R63 free history estimator power is a comparison, not actual tilt probability
    atlas={
     "schema":"htt.r69.typed_x_to_fiveview_physics/1",
     "experiment_law":"All readouts named by their original actual working source and physical qualifiedness",
     "universal_x_only_map":"IMPOSSIBLE_WITHOUT_K_L_MEASURE_TRANSPORT",
     "studies":{
      "P1_tensorized": {
       "x":"R61 actual CF4 11D apparent vector/tensor response; desired physical state (beta,sigma/H,omega/H,A/cH) NOT directly observed",
       "x_physical_qualification":"OBSERVATIONAL RESPONSE ONLY; omega has no identifiable column, beta and sigma/A require source/frame transfer",
       "Q":"for causal beta, Q_beta=|beta|; only an OUTER speed upper exists",
       "Q_beta_upper_conditional":speed_radius,
       "Pi":r61["maximum_p11_zero_response"],
       "Pi_scope":"largest nominal p of zero *apparent response* among correlated CF4 nuisance variants, not physical FLRW probability",
       "F_uniform_causal_beta_ball_outer_bound":f_upper,
       "F_scope":"Lebesgue reference on |beta|<=1; outer radius at zero from R61 11D ellipsoids; NOT posterior mass and strongly prior dependent",
       "G_F":"UNAVAILABLE_WITHOUT_ACTUAL_PREDICTIVE_F_DEPTH"
      },
      "P2_lowell_radiation": {"results":radiation,
        "pure_boost_companion":purekin,
        "first_second_moment_F_nonidentifiability_counterexample":radiation_cap_nonuniqueness(.9),
        "max_entropy_axisymmetric_photon_closure_benchmark":maximum_entropy_axisymmetric_photon_closure(beta=.3,cap=.9),
        "Q_joint_status":"real radiation flux missing; pure boost q is a model assumption"},
      "radio_dipole": {
       "x_actual_delta_log_count_xy":src["actual_delta"],
       "Q_statistical_signed_source_difference":radio["Q_stat_sqrt_chi2"],
       "Pi_working_Gaussian":radio["Pi_upper_tail"],
       "Q_physical":"UNAVAILABLE_REAL_X_IS_LOG_INTENSITY_NOT_LINEAR_COUNT_OR_VALIDATED_VELOCITY",
       "F":"UNAVAILABLE_NO_ACTUAL_COUNT_SELECTION_BODY_AND_REFERENCE_MEASURE",
       "G_F":"NOT_APPLICABLE_FLUX_CUT_IS_NOT_COSMIC_TIME",
       "law":"same-source Poisson influence fixed Gaussian, not LSS-calibrated"
      },
      "P6_kinematics": {
       "x":"R61 actual CF4 conditional apparent response (not direct local sigma,omega,A,beta); target GR state sigma,omega,A,beta unmeasured as a complete tuple",
       "x_physical_qualification":"R61 linearized 11D phenomenological source/carrier, omega unobserved; no direct physical 4-kinematic-component measurement",
       "Q_beta_upper":speed_radius,
       "Q_general_GR":"UNAVAILABLE_WITHOUT_FIELD_CONSTRAINT_INITIAL_DATA",
       "Pi":"conditional R61 likelihood only, no vorticity-column",
       "F":"requires a physical finite body+measure; no canonical uniform full GR data",
       "G_F":"requires actual kinetic/Einstein transport and common survey covariance",
       "example_chi_driver":dyn
      },
      "P5_bianchi_all_types": {
       "x_R62_log_J2_first_K5":sample_r62.tolist(),
       "signed_shape_chi":float(stf_shape(S0)["signed_chi"]),
       "F_sky_apparent_STF_positive":pheno_sky["F_sky_solid_angle"],
       "F_sky_apparent_depth_curve_not_physical_G_F":depth_sky,
       "Q_apparent_unit_H_if_K0_interpreted_as_sigma_over_H":pheno_q["Q_H_positive_directional_expansion"],
       "Q_status":"R62 K0 is phenomenological log-distance response not physical normal shear; cannot impose Bianchi constraint",
       "Pi_zero5_working_Gaussian":pheno_Q2["Pi_upper_tail"],
       "F":"UNAVAILABLE_NONCOMPACT_FAMILY_NO_GAUGE_FIXED_MEASURE",
       "G_F":"UNAVAILABLE_NOT_A_PHYSICAL_SHEAR_HISTORY",
       "physical_rule":"given actual a_i,n_ij,sigma,pi_N,q_N,H,energy, use Einstein/Jacobi/Codazzi and shear driver D"
      },
      "P3_directional_H": {
       "x_R64_example":{"eta_z":rp["eta_z"],"eta_zz":rp["eta_zz"],"denominator":rp["denominator"],"H_D":rp["H_D"]},
       "Q_one_point_H_D_derivative_pos_part":local_q,
       "Q_scope":"one reported direction/redshift model exemplar; not global direction/depth gate or physical Theta/3",
       "Q_vertex_from_R62_phenomenological_STF":pheno_q,
       "Pi":"R64 working fixed-Gaussian nested angular-depth test, not physics direct",
       "F":"UNAVAILABLE_NO_PHYSICAL_REFERENCE_MEASURE",
       "G_F":"UNAVAILABLE_NO_F_DEPTH_PATH; raw H_D ratio is different observable"
      },
      "P4_boost_vs_tilt": {
       "x":"relative beta_{O|R},beta_{M|R},beta_{M|N}; Gaia E1 proper motion is observer acceleration, NOT beta",
       "Q":"velocity causality Q=|beta| if actual relative velocity known",
       "Q_comparison_pure_boost_beta":b,
       "Pi":"R63 compensated-history discrimination has near-size power; no joint physical source likelihood",
       "F":"UNAVAILABLE_NO_NORMALIZED_COMMON_FRAME_MEASURE_AND_FAMILY_ELLIPSOID",
       "G_F":"UNAVAILABLE_NO_ACTUAL_PHYSICAL_BETA_HISTORY_IN_OBSERVED_DATA",
       "frame_invariant":"gamma_MR=-g(u_M,u_R)/c²; frames must be labelled, no global tilt from E1/B1 alone"
      }
     },
     "uncertainty":"Conditional diagnostics and source provenance as named; never multiply dependent Pi values",
     "physical_claim":"No new cosmological anisotropy, shear, vorticity, Bianchi or tilt measurement is asserted"
    }
    return atlas


def main():
    repo=Path(__file__).resolve().parents[2]
    output=repo/"docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS"
    out=atlas_from_previous_data(repo)
    (output/"FIVEVIEW_X_RESPONSE_ATLAS.json").write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    for k,v in out["studies"].items():
        print(k,str({a:b for a,b in v.items() if a in ("Q_beta_upper_conditional","Pi","F_uniform_causal_beta_ball_outer_bound","Q_statistical_signed_source_difference","Pi_working_Gaussian","Q_apparent_unit_H_if_K0_interpreted_as_sigma_over_H","Pi_zero5_working_Gaussian","Q_one_point_H_D_derivative_pos_part")})[:550])


if __name__=="__main__":main()
