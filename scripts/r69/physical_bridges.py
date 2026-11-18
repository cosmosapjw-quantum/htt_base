"""R69 GR/kinetic/geometry-to-observable bridges.

All local physical formulae state restrictive assumptions; actual catalogue
outputs are separate from conditional physical interpretations.
No physical Bianchi detection, no end-to-end Gaia systematic likelihood.
Signature (-,+,+,+), c retained; n observer->source.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
from scipy.constants import c as C_SI, Julian_year, parsec
from scripts.r68.fiveview_geometry import E, stf_matrix, stf_coordinates, stf_shape


def angular_tensor_moments(S):
    """Exact full-sky moments of f(n)=n^T S n, STF(3)."""
    S = np.asarray(S,float)
    stf_coordinates(S)
    I2 = float(np.trace(S @ S))
    I3 = float(np.trace(S @ S @ S))
    m2=2*I2/15
    m3=8*I3/105
    return {"m2":m2, "m3":m3,
            "signed_skewness":m3/m2**1.5 if m2>0 else None}


def hemisphere_leakage(n,p):
    """Unweighted catalogue hemisphere window; f=H+d.n+n.S.n."""
    n=np.asarray(n,float)
    p=np.asarray(p,float);p/=np.linalg.norm(p)
    plus=n@p>=0
    if not np.any(plus) or not np.any(~plus):
        raise ValueError("Both hemispheres required")
    mplus=n[plus].mean(axis=0);mminus=n[~plus].mean(axis=0)
    Gplus=np.einsum("ni,nj->ij",n[plus],n[plus])/int(plus.sum())
    Gminus=np.einsum("ni,nj->ij",n[~plus],n[~plus])/int((~plus).sum())
    D=Gplus-Gminus
    Dstf=D-np.eye(3)*np.trace(D)/3
    return {"N_plus":int(plus.sum()),"N_minus":int((~plus).sum()),
            "dipole_window_response":(mplus-mminus).tolist(),
            "dipole_ideal_p":p.tolist(),
            "dipole_response_error":float(np.linalg.norm(mplus-mminus-p)),
            "STF_window_leakage_matrix":Dstf.tolist(),
            "STF_window_leakage_norm":float(np.linalg.norm(Dstf)),
            "max_quadrupole_leakage_vs_fullsky_quadrupole_RMS":
                float(np.linalg.norm(Dstf)/np.sqrt(2/15)),
            "mean_sky":n.mean(axis=0).tolist()}


def cf4_hemisphere_windows(path,groups=(0,40,80,140,220,400,float("inf"))):
    """Original group table4, Galactic sky and catalogue-measured group Dist[Mpc].

    The survey window alone, not physical shear. A pure angular STF field can
    generate apparent hemisphere differences through this nonuniform window.
    """
    p=Path(path)
    groups_data=[]
    for line in p.open():
        try:
            ident=int(line[:7]);dist=float(line[21:26])
            l=np.deg2rad(float(line[101:109]))
            b=np.deg2rad(float(line[110:118]))
            if not (0<=dist and np.isfinite(l+b)):
                continue
            n=[np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)]
            groups_data.append((ident,dist,*n))
        except ValueError:
            continue
    a=np.asarray(groups_data,float)
    n=a[:,2:5];dist=a[:,1]
    p_gal_N=np.array([0,0,1.])
    l,b=np.deg2rad([264.021,48.253])
    p_cmb=np.array([np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)])
    result={"source":str(path),"source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "valid_rows":len(a),"distance_bins_Mpc":[v if np.isfinite(v) else None for v in groups],
            "interpretation":"geometric mask leakages, not CF4 signal or covariance estimates",
            "bins":[]}
    for lo,hi in zip(groups[:-1],groups[1:]):
        m=(dist>=lo)&(dist<hi)
        if np.count_nonzero(m)<10:continue
        result["bins"].append({
            "distance_range_Mpc":[lo,hi if np.isfinite(hi) else None],
            "n":int(np.count_nonzero(m)),
            "Galactic_north":hemisphere_leakage(n[m],p_gal_N),
            "CMB_dipole_direction":hemisphere_leakage(n[m],p_cmb)})
    return result


def boosted_radiation_stress(beta,nhat):
    """Exact normalized rest-isotropic photon gas stress in moving lab frame.

    T^(mu nu)=(epsilon+p)U^mu U^nu/c² + p g^mu nu,
    q/(rho c)=4 beta/(3+beta²), S=pi/rho =
    [4 beta²/(3+beta²)] STF(n n). Here c is restored only in q/rho c.
    """
    nhat=np.asarray(nhat,float);nhat=nhat/np.linalg.norm(nhat)
    if not 0<=beta<1:raise ValueError("Subluminal beta")
    factor=4*beta**2/(3+beta**2)
    S=factor*(np.outer(nhat,nhat)-np.eye(3)/3)
    return {"stress_STF":S, "flux_to_energy_c":4*beta/(3+beta**2),
            "stress_amplitude_factor":factor, "chi":float(stf_shape(S)["signed_chi"]) if beta>0 else None}


def retained_r66_boost_check(path):
    """Source file must match the verified R68 R66 byte identity."""
    from scripts.r68.fiveview_geometry import r66_reused_stress
    r=r66_reused_stress(path)
    # R66 restored solar-system dipole: Galactic 264.021°, +48.253°,
    # temperature dipole amplitude=3362.08 microK; T0=2.72548 K.
    b=3362.08/(r["T0_K"]*1e6)
    l,lat=np.deg2rad([264.021,48.253])
    n=np.array([np.cos(lat)*np.cos(l),np.cos(lat)*np.sin(l),np.sin(lat)])
    kin=boosted_radiation_stress(b,n)
    vkin=stf_coordinates(kin["stress_STF"])
    out={"R66_file_sha256":r["R66_source_file_sha256"],
         "dipole_definition":"beta=D_thermal/T0 + O(beta^3), direction Galactic (264.021,48.253) deg",
         "beta_first_order":b,"boost_only_reference_STF5":vkin.tolist(),
         "boost_only_signed_shape":kin["chi"],
          "approximation":"Boost-only analytic tensor is a comparator; subtracting normalized stresses is NOT a Lorentz deboost, R66 finite-band contains other effects",
         "results":{}}
    for k,v in r["results"].items():
        obs=np.asarray(v["pi5_over_rho"])
        resid=obs-vkin
        S=stf_matrix(resid)
        out["results"][k]={
            "observed_STF5":obs.tolist(),"boost_template_difference_STF5":resid.tolist(),
            "norm_observed":float(np.linalg.norm(obs)),
            "norm_boost_only":float(np.linalg.norm(vkin)),
            "norm_residual":float(np.linalg.norm(resid)),
            "signed_chi_observed":v["signed_chi"],
             "signed_chi_boost_template_difference":float(stf_shape(S)["signed_chi"]),
            "angle_cosine_obs_boost":float(obs@vkin/(np.linalg.norm(obs)*np.linalg.norm(vkin))),
            "boost_only_algebraically_sufficient":bool(np.allclose(resid,0,rtol=0,atol=1e-14))}
    return out


def formal_shear_template_inversion(kin, z_star=1100., Om=.3153, Or=.0001):
    """Illustrative INADMISSIBLE-as-measurement Bianchi I closure/proxy.

    sigma(t)=sigma0*(a0/a)^3 assumes geodesic Bianchi I with vanishing
    *total* normal anisotropic stress. Photons treated as test radiation,
    isotropic at emission, collisionless afterwards. This is neither a
    self-consistent early-universe photon Boltzmann solution nor a measured
    present-day shear. Simple normalized stress subtraction is NOT a true
    Lorentz deboost of full T^ab and its flux/normalization; it is an algebraic
    template difference only. Background E(z) is a chosen numeric benchmark.
    """
    from scipy.integrate import quad
    Ol=1.-Om-Or
    def Ez(z):
        return np.sqrt(Or*(1+z)**4+Om*(1+z)**3+Ol)
    # H0 * integral sigma(z)/sigma0 dt = ∫ (1+z)^2/E(z) dz.
    factor=quad(lambda z:(1+z)**2/Ez(z),0,z_star,epsrel=1e-11)[0]
    terms={}
    for name,r in kin["results"].items():
        observed=np.asarray(r["boost_template_difference_STF5"])
        # T anisotropy Q/T0 = -integral sigma dt;
        # pi/rho=(8/15) Q/T0 to linear order.
        integral = -(15/8)*observed
        instantaneous=integral/factor
        terms[name]={"formal_integrated_sigma_template_STF5":integral.tolist(),
                     "formal_norm_integrated_sigma_template":float(np.linalg.norm(integral)),
                     "formal_sigma0_template_over_H0_STF5":instantaneous.tolist(),
                     "formal_norm_sigma0_template_over_H0":float(np.linalg.norm(instantaneous))}
    return {"model":"Bianchi I diagonal, zero total anisotropic stress closure, test-photon collisionless, isotropic emission at z_star; R66 finite-band source",
            "z_star":z_star,"Omega_m":Om,"Omega_r":Or,"Omega_lambda":Ol,
            "dimensionless_H0_integral":factor,"physical_status":"FORMAL_TEMPLATE_NOT_PHYSICAL_DEBOOST_OR_OBSERVATIONAL_BOUND",
            "missing_physics":"full radiation T_ab energy and flux with explicit observer Lorentz transformation, intrinsic emission and source transfer",
            "nonclaims":["Initial intrinsic quadrupole, radiation anisotropic stress backreaction and source transfer unknown",
                         "R66 PR3/PR4 have no end-to-end Commander T null; sigma0/H0 is not a cosmological constraint"],
            "results":terms}


def frame_aware_fossil_consistency(kin, gaia_result):
    """Counterfactual test of restricted Bianchi I same-frame tensors.

    Physical diagonal Bianchi I with fixed shear axes and total pi_N=0,
    isotropic collisionless test photons gives Q_CMB/T0=-I*sigma_o+O(epsilon²)
    to FIRST ORDER only; exact common axes need not imply exact proportionality.
    Here the inputs do NOT satisfy the necessary physical source contract:
    Gaia E2 is an apparent proper-motion angular template, not a validated
    local homogeneous shear, and R66 is a finite-band released-map moment.
    This is a deterministic *anti-overinterpretation* diagnostic only.
    """
    from astropy.coordinates import SkyCoord
    a=json.loads(Path(gaia_result).read_text())
    v=np.asarray(a["results"]["quality"]["coefs_microasyr"][6:11],float)
    sigma_like=stf_matrix(v) # ICRS, units microarcseconds/year
    R=np.column_stack([
        SkyCoord(x=x,y=y,z=z,representation_type="cartesian",frame="icrs").galactic.cartesian.xyz.value
        for x,y,z in np.eye(3)])
    if np.linalg.det(R)<0 or not np.allclose(R.T@R,np.eye(3),atol=1e-12):
        raise ValueError("Invalid ICRS -> Galactic SO(3) frame")
    out={"Gaia_source_file_sha256":hashlib.sha256(Path(gaia_result).read_bytes()).hexdigest(),
         "ICRS_to_Galactic_SO3":R.tolist(),
         "hypothesis":"diagonal Bianchi I yields exact common eigenaxes for isotropic-emission photons; first-order Q=-I*sigma+O(epsilon²), opposite normalized chi=-chi(sigma)+O(epsilon), not exact finite-shear proportionality",
         "actual_status":"NOT_PHYSICAL_TEST_UNQUALIFIED_TRANSFER_AND_CORRELATED_ERRORS",
         "comparisons":{}}
    for rel,r in kin["results"].items():
        for key in ("observed_STF5","boost_template_difference_STF5"):
            Q_gal=stf_matrix(r[key])
            Q_icrs=R.T@Q_gal@R
            ns=np.linalg.norm(sigma_like);nq=np.linalg.norm(Q_icrs)
            out["comparisons"][rel+"__"+key]={
                "expected_negative_proportional_cosine":1.0,
                 "counterfactual_negative_cosine_WEAK_ANISOTROPY_ONLY":float(-np.sum(Q_icrs*sigma_like)/(ns*nq)),
                "counterfactual_normalized_commutator":float(np.linalg.norm(Q_icrs@sigma_like-sigma_like@Q_icrs)/(ns*nq)),
                 "chi_CMB_template":float(stf_shape(Q_icrs)["signed_chi"]),
                "chi_Gaia_E2_template":float(stf_shape(sigma_like)["signed_chi"])}
    return out


def validate_tracefree_beta(beta):
    beta=np.asarray(beta,float)
    if beta.shape!=(3,) or not np.all(np.isfinite(beta)):
        raise ValueError("Bianchi I diagonal beta_i must be a finite length-3 vector")
    norm=np.max(np.abs(beta))
    if abs(np.sum(beta))>1e-12*norm:
        raise ValueError("Bianchi I beta_i must be tracefree")
    return beta


def bianchi_I_directional_redshift(a_o,a_e,beta_o,beta_e,dirs):
    """Exact photon energy ratio E_e/E_o for diagonal Bianchi I.

    ds²=-c²dt²+a² sum_i exp(2 beta_i(t)) (dx^i)².
    Directions are measured in *observer's* orthonormal spatial triad.
    Photon coordinate momenta p_i conserved by spatial Killing fields.
    """
    bo,be=validate_tracefree_beta(beta_o),validate_tracefree_beta(beta_e)
    n=np.asarray(dirs,float)
    if a_o<=0 or a_e<=0 or not np.allclose(np.linalg.norm(n,axis=-1),1,atol=1e-10):
        raise ValueError("positive scale factors, unit sourceward directions")
    return (a_o/a_e)*np.sqrt(np.sum(n*n*np.exp(2*(bo-be)),axis=-1))


def bianchi_I_temperature(a_o,a_e,bo,be,dirs,T_e):
    """If isotropic blackbody at emission, free streaming until observation."""
    return T_e/bianchi_I_directional_redshift(a_o,a_e,bo,be,dirs)


def bianchi_I_radiation_moment(bo,be, quadrature_mu=64, quadrature_phi=128):
    """Exact angular T^4 pressure moment of collisionless homogeneous photons.

    Input bo/be are tracefree log scale anisotropies in comoving fixed axes.
    Emission f_e was isotropic Planck and collisionless Liouville propagated.
    The normalization cancels a_o/a_e and T_e. Gauss-Legendre/azimuth for
    numerical quadrature, not claim of an exact symbolic all-orders solution.
    """
    from numpy.polynomial.legendre import leggauss
    bo,be=validate_tracefree_beta(bo),validate_tracefree_beta(be)
    if np.array_equal(bo,be):
        # Exact isotropic-redshift solution; do not mistake quadrature roundoff
        # for a physically nonzero ~1e-16 STF tensor.
        zero=np.zeros((3,3))
        return {"STF_pressure":zero,"STF5":np.zeros(5),
                "raw_trace_error":0.,"trace_error":0.,"n_directions":quadrature_mu*quadrature_phi,
                "exact_isotropic_case":True}
    mu,w=leggauss(quadrature_mu)
    phi=2*np.pi*np.arange(quadrature_phi)/quadrature_phi
    MU,PHI=np.meshgrid(mu,phi,indexing="ij")
    sin=np.sqrt(1-MU**2)
    n=np.column_stack([sin.ravel()*np.cos(PHI).ravel(),
                       sin.ravel()*np.sin(PHI).ravel(),
                       MU.ravel()])
    weights=np.repeat(w,quadrature_phi)*2*np.pi/quadrature_phi
    T=bianchi_I_temperature(1.,.5,bo,be,n,T_e=2.)
    bright=weights*T**4
    pressure=np.einsum("n,ni,nj->ij",bright,n,n)/np.sum(bright)
    Sraw=pressure-np.eye(3)/3
    tr=float(np.trace(Sraw))
    # The exact radiation pressure has trace 1. Subtract only numerical
    # quadrature/accumulation trace leakage before STF coordinate validation.
    S=(Sraw+Sraw.T)/2-np.eye(3)*tr/3
    if np.linalg.norm(S)<1e-13:
        raise ValueError("Anisotropic radiation moment below numerical quadrature resolution")
    return {"STF_pressure":S,"STF5":stf_coordinates(S),
            "raw_trace_error":tr,"trace_error":float(np.trace(S)),
            "n_directions":len(weights)}


def sky_random(n=300000,seed=69):
    rng=np.random.default_rng(seed)
    z=rng.uniform(-1,1,n);phi=rng.uniform(0,2*np.pi,n)
    s=np.sqrt(1-z*z)
    return np.column_stack((s*np.cos(phi),s*np.sin(phi),z))


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    root=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
    cf4=cf4_hemisphere_windows(root)
    r66=Path(__file__).resolve().parents[2]/"docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"
    kin=retained_r66_boost_check(r66)
    bridge=formal_shear_template_inversion(kin)
    gaiapath=out/"GAIA_E1B1E2B2.json"
    alignment=frame_aware_fossil_consistency(kin,gaiapath) if gaiapath.exists() else None
    rng=np.random.default_rng(72)
    n=sky_random(350000,seed=79)
    Q=stf_matrix(np.array([.01,-.025,.035,.02,-.012]))
    f=np.einsum("ni,ij,nj->n",n,Q,n)
    analytic=angular_tensor_moments(Q)
    mc={"m2":float(np.mean(f*f)),"m3":float(np.mean(f**3)),
        "relative_error_m2":float(np.mean(f*f)/analytic["m2"]-1),
        "relative_error_m3":float(np.mean(f**3)/analytic["m3"]-1)}
    # Unit test of exact Bianchi I free-streaming temperature.
    initial=np.array([-.01,.006,.004]);final=np.zeros(3)
    eps=np.array([1e-2,3e-3,1e-3])
    errors=[]
    for e in eps:
        E=bianchi_I_directional_redshift(1.,.5,final,e*initial,n[:80000])
        T=2./E  # T_e=2; background T=1
        anis=T/T.mean()-1.
        # Bianchi I tensor redshift is quadratic in n_i, NOT a dipole.
        lin=-np.sum(n[:80000]**2*(final-e*initial),axis=1)
        lin-=lin.mean()
        errors.append({"epsilon":e,"rms_residual":float(np.sqrt(np.mean((anis-lin)**2))),
                       "rms_signal":float(np.sqrt(np.mean(lin**2)))})
    # Independent deterministic angular quadrature, validating collisionless
    # Boltzmann blackbody moment: S=-(8/15)*DeltaBeta+O(DeltaBeta²).
    kinetic_errors=[]
    direction=np.array([.5,-.3,-.2])
    for e in (1e-2,3e-3,1e-3):
        delta=e*direction
        Snum=bianchi_I_radiation_moment(np.zeros(3),-delta)["STF_pressure"]
        # delta = bo-be; Q/T0=-delta; stress=-(8/15)delta.
        Slin=-(8/15)*np.diag(delta)
        kinetic_errors.append({"epsilon":e,"error_Frobenius":float(np.linalg.norm(Snum-Slin)),
                               "linear_norm":float(np.linalg.norm(Slin))})
    result={
        "schema":"htt.r69.GR_kinetic_hemispherical_physics/1",
        "cf4_hemispheres":cf4,
        "R66_kinetic_boost_only_diagnostic":kin,
        "R66_to_BianchiI_FORMAL_template_only":bridge,
        "Gaia_CMB_counterfactual_frame_alignment":alignment,
        "STF_moments_exact_vs_sky_MC":{"analytic":analytic,"sky_mc":mc,"N":len(n)},
        "BianchiI_Liouville_temperature4_to_radiation_STF":{"source":"isotropic Planck at emission, collisionless Liouville, fixed diagonal metric and Gauss-Legendre angular moment","errors":kinetic_errors},
        "BianchiI_exact_redshift_vs_integrated_shear_first_order":{"source":"diagonal homogeneous Bianchi I, photon geodesic, isotropic blackbody emitter, a_e=.5,a_o=1",
            "beta_epoch_seed":initial.tolist(),"n_draws":80000,"errors":errors},
        "scope":"Actual CF4 mask and R66 already-computed radiation stress combined with exact conditional geometric identities; no physical anisotropy detection"
    }
    (out/"GR_KINETIC_HEMISPHERES.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"CF4_rows":cf4["valid_rows"],
                      "mask":[{"range":r["distance_range_Mpc"],"n":r["n"],"leak":r["Galactic_north"]["STF_window_leakage_norm"]} for r in cf4["bins"]],
                      "r66_boost":{k:{"cos":v["angle_cosine_obs_boost"],"relative_resid":v["norm_residual"]/v["norm_observed"]} for k,v in kin["results"].items()},
                       "formal_sigma0_template_over_H0_NO_PHYSICAL_INFERENCE":{k:v["formal_norm_sigma0_template_over_H0"] for k,v in bridge["results"].items()},
                      "sky_moments":mc,"redshift_errors":errors,"kinetic_errors":kinetic_errors},indent=2))


if __name__=="__main__":
    out=Path(__file__).resolve().parents[2]/"docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS"
    run(out)
