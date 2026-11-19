"""R76 P6: physical scalar/vector identity, source sky/Fisher geometry,
and fully global conservative Gaussian+calibration domain certificate.

Inputs are pinned R61 and R69 JSON and original R58 carrier (read only).
No full Einstein--Boltzmann, physical Gaia/CF4 common-frame claim or cosmic null.
Execute from htt_base repo root with PYTHONPATH=. OPENBLAS_NUM_THREADS=1.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
from scipy.linalg import eigh
from scipy.stats import chi2
from scipy.special import roots_legendre
from scripts.r68.fiveview_geometry import E,stf_matrix,stf_shape
from scripts.r69.fiveview_response import min_spherical_quadratic

R=Path("docs/research_program/observational_publication_20261015")
CF4=R/"R61_KINEMATIC_MEASUREMENT_20261117"/"RESULTS"/"IMAGES"/"KINEMATIC_IMAGES.json"
CF4_DEPTH=R/"R61_KINEMATIC_MEASUREMENT_20261117"/"RESULTS"/"DEPTH_CORRECTED"/"KINEMATIC_DEPTH.json"
R58=R/"R58_MIXED_TENSOR_CONVERGENCE_20261117"/"RESULTS"/"OWNED_TENSOR_CARRIERS.npz"
GAIA=R/"R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118"/"RESULTS"/"GAIA_E1B1E2B2.json"
R69_PROVENANCE=R/"R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118"/"PROVENANCE.json"
MMAG_TO_RHO=np.log(10)/5*0.001

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def sphere(nmu=100,nphi=160):
    mu, w=roots_legendre(nmu)
    phi=np.arange(nphi)*2*np.pi/nphi
    mm,pp=np.meshgrid(mu,phi,indexing="ij")
    sn=np.sqrt(1-mm**2)
    n=np.column_stack([np.ravel(sn*np.cos(pp)),
                       np.ravel(sn*np.sin(pp)),np.ravel(mm)])
    wt=np.repeat(w/(2*nphi),nphi)
    assert abs(np.sum(wt)-1)<1e-14
    return n,wt

def w_map(n):
    n=np.asarray(n,float)
    if n.ndim==1:n=n[None,:]
    q=np.einsum("ni,aij,nj->na",n,E,n)
    out=np.concatenate([np.zeros((len(n),3)),n,q],axis=1)
    return out

def actual_fullsky_F_S(S,n,wt):
    g=np.einsum("ni,ij,nj->n",n,S,n)
    return float(np.dot(wt,g>0))

def core_algebra():
    rng=np.random.default_rng(1476)
    n,wt=sphere(112,180)
    results=[]
    for i in range(4):
        S=stf_matrix(rng.normal(size=5))*.025
        omega=rng.normal(size=3)*.03
        g=np.einsum("ni,ij,nj->n",n,S,n)
        v=n@S.T-g[:,None]*n
        # equivalent direct tangent projection
        assert np.max(abs(np.einsum("ni,ni->n",n,v)))<3e-14
        vv=np.sum(v*v,axis=1)
        vr=np.cross(omega[None,:],n)
        qn=float(np.dot(wt,g*g))
        vn=float(np.dot(wt,vv))
        rn=float(np.dot(wt,np.sum(vr*vr,axis=1)))
        t=float(np.trace(S@S))
        assert abs(qn-(2/15)*t)<2e-12
        assert abs(vn-t/5)<2e-12
        assert abs(rn-(2/3)*float(omega@omega))<2e-12
        assert abs(vn/qn-1.5)<1e-10
        # sphere sampling gradient of g via directional short arcs
        for nn in n[[31,1234,6878]]:
            vv0=S@nn-(nn@S@nn)*nn
            tangent=rng.normal(size=3);tangent-=nn*(nn@tangent);tangent/=np.linalg.norm(tangent)
            h=2e-6
            xplus=np.cos(h)*nn+np.sin(h)*tangent
            xminus=np.cos(h)*nn-np.sin(h)*tangent
            derivative=(xplus@S@xplus-xminus@S@xminus)/(2*h)
            assert abs(derivative-2*tangent@vv0)<2e-10
        results.append({"toy":i,"scalar_rms2":qn,
          "E2_over_H_rms2":vn,"E2_vs_scalar_power_ratio":vn/qn,
          "B1_rotational_rms2":rn,"physical_normalization":"V_E2=H times normalized tangent; S=sigma/H"})
    # completeness of STF basis yielding uniform robust Gaussian bound
    moments=np.einsum("ni,aij,nj->na",n,E,n)
    norms=np.sum(moments**2,axis=1)
    np.testing.assert_allclose(norms,np.full(len(n),2/3),rtol=1e-13,atol=2e-13)
    w=w_map(n)
    np.testing.assert_allclose(np.sum(w**2,axis=1),np.full(len(n),5/3),rtol=1e-13,atol=2e-13)
    return {"model":"Euclidean local-affine tangent versus local vertex; not general finite-z Gaia",
       "cases":results,"quadrupole_basis_pointwise_sum":float(np.mean(norms)),
       "CF4_11D_affine_row_norm2":float(np.mean(np.sum(w*w,axis=1))),
       "identity":"pointwise sum_A(n E_A n)^2=2/3; 8D row norm2=5/3"}

def cf4_by_model():
    a=json.loads(CF4.read_text())
    assert a["source"]["sha256"]==sha(R58)
    assert a["source"]["n_groups"]==35970
    n,wt=sphere()
    W=w_map(n)
    cutoff=float(a["contract"]["cutoffs"]["simultaneous11"])
    assert abs(cutoff-chi2.ppf(.95,11))<2e-12
    results={}
    for name,models in a["variants"].items():
        sub=models["1.0"]
        theta=np.asarray(sub["estimate11"],float)
        C=np.asarray(sub["covariance11"],float)
        assert theta.shape==(11,) and C.shape==(11,11)
        assert np.linalg.eigvalsh(C)[0]>0
        d=theta[3:6]
        S=stf_matrix(theta[6:11])
        trust=min_spherical_quadratic(S,d)
        minpoint=1+trust["min_angular_perturbation"]
        Q=max(0.,-trust["min_angular_perturbation"])
        skyfield=1+W@theta
        skyF=float(np.dot(wt,skyfield>0))
        shearF=actual_fullsky_F_S(S,n,wt)
        # 11D joint confidence ellipsoid maps into fixed direction.
        mu=skyfield
        var=np.einsum("ni,ij,nj->n",W,C,W)
        assert np.min(var)>0
        low=mu-np.sqrt(cutoff*var)
        imin=int(np.argmin(low))
        row=W[imin]
        candidate=theta-np.sqrt(cutoff)*(C@row)/np.sqrt(row@C@row)
        witness_h=1+row@candidate
        witness_q=(candidate-theta)@np.linalg.solve(C,candidate-theta)
        assert abs(witness_h-low[imin])<3e-12
        assert abs(witness_q-cutoff)<1e-6
        # Exact uniform direction norm establishes a GLOBAL conservative
        # lower confidence bound, without relying on sky pixel sampling.
        # q-calibration RMS metric is |d_cal|²/3+2||q_cal||_F²/15;
        # pointwise dual norm exactly sqrt(8)*rho.
        c8=C[3:11,3:11]
        lam=float(np.linalg.eigvalsh(c8)[-1])
        mean_global_LB=1-np.linalg.norm(d)-np.linalg.norm(S,2)
        err_global_UB=np.sqrt(cutoff*(5/3)*lam)
        global_bound0=float(mean_global_LB-err_global_UB)
        exact_shape=stf_shape(S)
        cal={}
        for mag in (0,1,5,10):
            rho=MMAG_TO_RHO*mag
            margin=global_bound0-np.sqrt(8)*rho
            cal[f"{mag}mmag"]={"global_uniform_lower_bound":float(margin),
                "strict_positive_certified":bool(margin>0),
                "max_point_calibration_bias":float(np.sqrt(8)*rho)}
        results[name]={
          "source":"R61 saved same CF4 group model "+name+" covariance x11, zero-calibration local interpretation",
          "n_groups":a["source"]["n_groups"],
          "point_directional_min_allsky_trust_region":float(minpoint),
          "point_Q_H_apparent":float(Q),
          "point_fullsky_positive_H_area_fraction":skyF,
          "shear_signed_chi":float(exact_shape["signed_chi"]),
          "shear_fullsky_signed_positive_area":shearF,
          "CF4_directional_calibration_nuisance":"zero baseline plus 0/1/5/10 mmag deterministic allowance",
          "sufficient_global_min_at_0mmag":global_bound0,
          "uniform_gaussian_ellipsoid_angular_error_upper":float(err_global_UB),
          "source_covariance_max_eig_d_S_8D":lam,
          "global_strict_positive_sufficient_certificate":cal,
          "finite_sphere_min_directional_joint_lower":float(low[imin]),
          "finite_sphere_min_direction_index":imin,
          "finite_sphere_extremal_ellipsoid_witness_h":float(witness_h),
          "finite_sphere_extremal_ellipsoid_distance_squared":float(witness_q),
          "finite_sphere_number_directions":len(n),
          "source_adequacy_p_working":float(sub["adequacy_p"]),
          "source_model_scope":"NOT_GR_normal_shear_or_vorticity; no H monopole; no global cosmic p"}
    return {"source_sha256":sha(CF4),
       "source_R58_carrier_sha256":sha(R58),
       "common_simultaneous11_95pct_cutoff":cutoff,
       "proof_global_lower":"h>=1-|d|-||S||op-sqrt((5/3)*cutoff*lambda_max(C8))-sqrt(8)*rho",
       "models":results}

def canonical_corr(EE,EB,BB):
    def isqrt(X):
        eig,U=eigh(X)
        if eig[0]<=0:raise ValueError("non-positive Fisher block")
        return (U/eig**.5)@U.T
    M=isqrt(EE)@EB@isqrt(BB)
    return np.linalg.svd(M,compute_uv=False).tolist()

def gaia_cross_geometry():
    d=json.loads(GAIA.read_text())
    assert d["template_convention"].startswith("E1=P_n")
    results={}
    for name,row in d["results"].items():
        theta=np.asarray(row["coefs_microasyr"],float)
        Cformal=np.asarray(row["formal_cov_microasyr2"],float)
        assert theta.shape==(16,) and Cformal.shape==(16,16)
        evals=np.linalg.eigvalsh(Cformal)
        assert evals[0]>0
        Fisher=np.linalg.inv(Cformal)
        # First 6 = E1/B1 nuisance, last 10 = E2/B2.
        fn=Fisher[:6,:6]
        cross=Fisher[6:,:6]
        prof=Fisher[6:,6:]-cross@np.linalg.solve(fn,cross.T)
        np.testing.assert_allclose(prof,np.linalg.inv(Cformal[6:,6:]),
                    rtol=1e-11,atol=1e-10)
        mix=canonical_corr(prof[:5,:5],prof[:5,5:],prof[5:,5:])
        # All-sky uniform E2/B2 correlation is EXACTLY 0; any observed
        # nonzero coupling is due to weighted sky design selection.
        e=theta[6:11]
        b=theta[11:16]
        E2=stf_matrix(e)
        n,wt=sphere()
        scal=n@E2
        scalar=np.einsum("ni,ni->n",n,scal)
        v=scal-scalar[:,None]*n
        scalar_sq=float(np.dot(wt,scalar**2))
        E2_sq=float(np.dot(wt,np.sum(v*v,axis=1)))
        np.testing.assert_allclose(E2_sq/scalar_sq,1.5,rtol=1e-10)
        shape=stf_shape(E2)
        FE2=actual_fullsky_F_S(E2,n,wt)
        # Two empirical Gaussian covariance laws. Patch is only sensitivity
        # covariance, never source-design inverse/Fisher.
        t_E_formal=float(e@np.linalg.solve(Cformal[6:11,6:11],e))
        t_B_formal=float(b@np.linalg.solve(Cformal[11:16,11:16],b))
        one={
          "source_quality_case":name,"n_gaia_sources":row["n_sources"],
          "actual_rank":row["rank"],"source_condition":row["F_condition"],
          "E2_signed_coefficients_microasyr":e.tolist(),
          "B2_signed_coefficients_microasyr":b.tolist(),
          "E2_chi_from_cartesian_STF":float(shape["signed_chi"]),
          "E2_intrinsic_quadrupole_potential_FOmega":FE2,
          "E2_local_affine_vector_to_scalar_rms2":E2_sq/scalar_sq,
          "E2_B2_profiled_design_canonical_corr":mix,
          "E2_B2_profiled_design_maxcanonical":float(mix[0]),
          "E2_B2_design_cross_block_frobenius":float(np.linalg.norm(prof[:5,5:])),
          "E2_working_formal_chi2_5":t_E_formal,
          "B2_working_formal_chi2_5":t_B_formal,
          "E2_formal_p_naive":float(chi2.sf(t_E_formal,5)),
          "B2_formal_p_naive":float(chi2.sf(t_B_formal,5)),
          "gaia_B1_is_not_cosmological_fluid_vorticity":True,
          "gaia_E2_not_a_measured_sigma_over_H":True}
        if name=="quality":
            cpatch=np.asarray(row["spatial_patch_192_cov_microasyr2"],float)
            assert np.linalg.eigvalsh(cpatch)[0]>0
            tE=float(e@np.linalg.solve(cpatch[6:11,6:11],e))
            tB=float(b@np.linalg.solve(cpatch[11:16,11:16],b))
            one["exploratory_patch_E2_chi2_5"]=tE
            one["exploratory_patch_B2_chi2_5"]=tB
            one["exploratory_patch_E2_nominal_p_not_cosmic"]=float(chi2.sf(tE,5))
            one["exploratory_patch_B2_nominal_p_not_cosmic"]=float(chi2.sf(tB,5))
            # Coefficient uncertainty canonical corr is not design mixing.
            one["exploratory_patch_coefficient_error_correlation_max"]=float(
              canonical_corr(cpatch[6:11,6:11],cpatch[6:11,11:16],cpatch[11:16,11:16])[0])
        results[name]=one
    return {"source_sha256":sha(GAIA),
       "original_gaia_input_sha256_recorded_in_R69":json.loads(R69_PROVENANCE.read_text())["source_bytes_and_sha256"]["Gaia_CRF3_original"]["sha256"],
       "results":results,
       "interpretation":"real source-weight/Fisher mixing and source-model template shape; no direct cosmic shear or vorticity identification"}

def GF_toy():
    a0=1.5
    adot=.2
    t0=0.
    def F(t):
        a=a0+adot*t
        return 1. if a<=1 else .5*(1+1/a)
    dt=1.e-5
    derivative=(F(dt)-F(-dt))/(2*dt)
    exact=-adot/(2*a0*a0)
    assert abs(derivative-exact)<2e-11
    # critical a=1: F continuous but one-sided derivative differs.
    return {"explicit_toy":"observer Fermi sky sign event h=1+a(t) cos theta; no full Einstein model",
       "a0":a0,"adot_per_time":adot,
       "F_Hplus":F(t0),"exact_GF_time_derivative":exact,
       "finite_difference_derivative":derivative,
       "critical_nonregular_a_equals_one":"F continuous but derivative changes, coarea regularity fails at point zero",
       "actual_cosmic_time_GF":"UNAVAILABLE_FROM_R61_REDSHIFT_SLOPE"}

def main():
    algebra=core_algebra()
    cf=cf4_by_model()
    gaia=gaia_cross_geometry()
    toy=GF_toy()
    return {"schema":"htt.r76.p6_physical_fiveview_scalar_tangent/1",
       "evidence_status":"DERIVED_AND_SAVED_SOURCE_CONDITIONAL_NUMERICALLY_CHECKED",
       "input_files_sha256":{"R61_images":sha(CF4),
           "R61_depth":sha(CF4_DEPTH),
           "R58_selected_CF4_carrier":sha(R58),
           "R69_Gaia_VSH":sha(GAIA),
           "R69_original_provenance":sha(R69_PROVENANCE)},
       "exact_synthetic_geometry":algebra,
       "R61_CF4_11D_simultaneous_source_models":cf,
       "R69_Gaia_VSH_actual_source":gaia,
       "physical_GF_transport_toy_only":toy,
       "nonclaims":"No full normalized GR shear/acceleration/omega identification, no calibrated cross CF4/Gaia joint null, no actual physical GF, no family posterior"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False,allow_nan=False))
