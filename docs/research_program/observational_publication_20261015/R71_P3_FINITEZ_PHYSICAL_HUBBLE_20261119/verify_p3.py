"""R71 P3 finite-z Hubble: model-conditional R64 CF4 68D source readout, no cosmological inference.

Run from htt_base root:
  PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R71_P3_FINITEZ_PHYSICAL_HUBBLE_20261119/verify_p3.py
Original R64 files remain read-only. No native Einstein-Boltzmann solver, physical Hcal or full sky null.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.integrate import quad
from scipy.special import sph_harm_y
from numpy.polynomial.legendre import leggauss,legval
from scripts.r68.fiveview_geometry import E, stf_matrix, stf_shape
from scripts.r69.fiveview_response import min_spherical_quadratic

R64=Path("docs/research_program/observational_publication_20261015/R64_DIRECTIONAL_HUBBLE_20261117/RESULTS")
PATH=R64/"AUGMENTED"/"AUGMENTED_RESULT.json"
BASE=R64/"OBSERVED"/"DIRECTIONAL_HUBBLE_RESULT.json"
C_KM_S=299792.458

def flrw(z,H0,om):
    ee=np.sqrt(om*(1+z)**3+(1-om))
    h=H0*ee
    hp=h*(3*om*(1+z)**2)/(2*ee**2)
    chi=quad(lambda x:C_KM_S/(H0*np.sqrt(om*(1+x)**3+1-om)),0,z,epsabs=1e-11)[0]
    B=h*chi/C_KM_S
    Bprime=1+(hp/h)*B
    qref=-1+(1+z)*hp/h
    return h,hp,chi,B,Bprime,qref

def basis(n):
    return np.column_stack([np.ones(len(n)),n,np.einsum("ni,aij,nj->na",n,E,n)])

def fit9(n,f):
    X=basis(n)
    coef=np.linalg.lstsq(X,f,rcond=None)[0]
    residual=np.max(np.abs(X@coef-f))
    return coef,float(residual)

def sphere_grid(nmu=112,nphi=192):
    u,w=leggauss(nmu)
    ph=2*np.pi*np.arange(nphi)/nphi
    mu,az=np.meshgrid(u,ph,indexing="ij")
    sz=np.sqrt(1-mu**2)
    n=np.column_stack([sz.ravel()*np.cos(az).ravel(),sz.ravel()*np.sin(az).ravel(),mu.ravel()])
    p=(w[:,None]*np.ones((1,nphi))/(2*nphi)).ravel() # average-sphere weights sum 1
    th=np.arccos(np.clip(mu.ravel(),-1,1))
    return n,p,th,az.ravel()

def lm_rms(f,l,th,phi,w):
    # coefficient a_lm=∫dΩ fY*, normalized sky RMS=sum_m |a_lm|²/(4π)
    sq=0.0
    for m in range(-l,l+1):
        Y=sph_harm_y(l,m,th,phi)
        a=4*np.pi*np.dot(w,f*np.conj(Y))
        sq+=abs(a)**2/(4*np.pi)
    return float(np.sqrt(sq))

def p3(n,d,S):
    dn=n@d
    q=np.einsum("ni,ij,nj->n",n,S,n)
    return dn*q-(2/5)*n@(S@d)

def p4(n,S):
    q=np.einsum("ni,ij,nj->n",n,S,n)
    S2=S@S
    S2stf=S2-np.eye(3)*np.trace(S2)/3
    return q**2-(4/7)*np.einsum("ni,ij,nj->n",n,S2stf,n)-(2/15)*np.trace(S2)

def optical_toy():
    # length units c=1, Hcal=0.1, constant positive optical tidal strength F=2.5².
    kappa=2.5;h=0.1;lam=1.
    da=np.sin(kappa*lam)/kappa
    dal=np.cos(kappa*lam)
    zz=1/(1-h*lam)-1
    HD=(1+zz)*h/(dal+(1+zz)*h*da)
    assert da>0 and h>0 and HD<0 and lam<np.pi/kappa
    # M(z)=cos(kappa lambda(z)); dM/dz=-k² DA/(dz/dlambda) per Sachs.
    dMdz=-(kappa*kappa)*da/(((1+zz)**2)*h)
    return {"label":"OPTICAL_REDSHIFT_TOY_NOT_GLOBAL_GR","kappa":kappa,"Hcal_over_c":h,
            "lambda":lam,"z":zz,"D_A":da,"M=D_A_affine_prime":dal,
            "dM_dz":dMdz,"H_D_over_c":HD,"before_first_caustic":True,
            "physical_interpretation":"NEC/focusing can coexist with Hcal>0 and H_D<0; prescribed optical+redshift ODE not a verified full Einstein cosmology"}

def axial_harmonic():
    zz, ww=leggauss(240)
    p2=legval(zz,[0,0,1])
    out=[]
    for beta in [.01,.03,.1]:
        ff=-np.log1p(-beta*p2)
        coeff=(9/2)*float(np.dot(ww*ff,legval(zz,[0,0,0,0,1])))
        pred=9*beta*beta/35
        out.append({"beta=B_times_eta_P2_z":beta,"exact_l4":coeff,
                    "quadratic_tied_l4":pred,"relative_error":(coeff-pred)/pred})
    assert out[0]["relative_error"]<.02
    return out

def source_summary():
    obj=json.loads(PATH.read_text())
    base=json.loads(BASE.read_text())
    n=np.asarray(base["directions"],float)
    H0=float(base["H0_reference_km_s_Mpc"]);om=float(base["Omega_m_reference"])
    zs=list(map(float,base["z_evaluation"]))
    assert n.shape==(54,3) and len(zs)==4
    norms=np.linalg.norm(n,axis=1)
    np.testing.assert_allclose(norms,1.,atol=1e-12)
    ns,ws,th,ph=sphere_grid()
    modelnames=["mono_method__J1__method_angular_nuisance",
                "mono_method__J2__method_angular_nuisance",
                "mono_method__J3__method_angular_nuisance"]
    output={}
    for name in modelnames:
        mod=obj["models"][name]
        index={(int(row["z_index"]),int(row["direction_index"])):row for row in mod["maps"]}
        assert len(index)==216
        rows=[]
        for j,z in enumerate(zs):
            data=[index[j,k] for k in range(54)]
            dz=np.asarray([v["point"]["eta_z"] for v in data],float)
            dzz=np.asarray([v["point"]["eta_zz"] for v in data],float)
            eta=np.asarray([v["point"]["eta_relative"] for v in data],float)
            den=np.asarray([v["point"]["denominator"] for v in data],float)
            Hout=np.asarray([v["point"]["H_D_over_H_ref"] for v in data],float)
            qout=np.asarray([v["point"]["q_D"] for v in data],float)
            H,Hp,chi,B,Bp,qref=flrw(z,H0,om)
            calcden=1-B*dz
            calcH=np.exp(eta)/calcden
            calcq=qref+(1+z)*(dz+(Bp*dz+B*dzz)/calcden)
            assert np.isfinite(calcden).all()
            denomerr=float(np.max(np.abs(calcden-den)))
            Herr=float(np.max(np.abs(calcH-Hout)))
            qerr=float(np.max(np.abs(calcq-qout)))
            assert denomerr<2e-9,(name,z,denomerr)
            assert Herr<2e-8,(name,z,Herr)
            assert qerr<3e-7,(name,z,qerr)
            c0,fiterr=fit9(n,dz)
            c_eta,etaerr=fit9(n,eta)
            assert fiterr<1e-8,(name,z,fiterr)
            assert etaerr<1e-8,(name,z,etaerr)
            scalar,dvec,stfcoeff=c0[0],c0[1:4],c0[4:9]
            S=stf_matrix(stfcoeff)
            m=min_spherical_quadratic(-S,-dvec)
            sup=float(scalar-m["min_angular_perturbation"])
            Dglobmin=float(1-B*sup)
            skyderiv=basis(ns)@c0
            skyeta=basis(ns)@c_eta
            skyden=1-B*skyderiv
            max_abs_taylor_argument=float(np.max(np.abs(B*skyderiv)))
            sample_positive=sum(row["point"]["denominator"]>0 for row in data)
            gridpos=float(np.dot(ws,skyden>0))
            # Necessary full-sky condition for log-H_D, may fail for high-J.
            extra={"source_grid_positive_count":int(sample_positive),"source_grid_size":54,
              "global_min_D_fit":Dglobmin,"full_sky_area_D_positive_toy_fit":gridpos,
              "fullsky_optical_shape_chi_eta_z":None if np.linalg.norm(S)<1e-16 else float(stf_shape(S)["signed_chi"]),
              "Q_D_positive_derivative_domain_point_model":max(0,B*sup),
              "max_abs_B_eta_z_fullsky_point_model":max_abs_taylor_argument,
              "Taylor_log_denominator_series_uniform_convergence":bool(max_abs_taylor_argument<1),
              "H0_reference":H0,"z":z,"B":B,
              "max_R64_denominator_residual":denomerr,"max_R64_H_D_ratio_residual":Herr,
              "max_R64_qD_residual":qerr,
              "eta_z_9component_reconstruction_residual":fiterr}
            # NEC comparator only if conditionally assuming physical Hcal=Href:
            # f_ratio/f_ref = 1 + ((1+z)/(H Hp)) [H²(eta''-eta'²)+(2H²chi'/chi+H Hp)eta']
            rat=1+(1+z)/(H*Hp)*(H*H*(dzz-dz*dz)+
                       (2*H*H*(C_KM_S/H)/chi +H*Hp)*dz)
            # Independent distance-R second-derivative reconstruction of the
            # same physical conditional comparator: no use of compact eta formula.
            chp=C_KM_S/H
            chpp=-chp*Hp/H
            R=chi*np.exp(-eta)
            Rp=np.exp(-eta)*(chp-chi*dz)
            Rpp=np.exp(-eta)*(chpp-2*chp*dz+chi*(dz**2-dzz))
            focus=-((1+z)**4)/(C_KM_S**2*R)*(H**2*Rpp+H*Hp*(Rp-R/(1+z)))
            focus0=(1+z)**3*H*Hp/C_KM_S**2
            focus_comparison_resid=float(np.max(np.abs(focus/focus0-rat)))
            assert focus_comparison_resid<2e-9,(name,z,focus_comparison_resid)
            extra["reference_focus_derived_two_ways_residual"]=focus_comparison_resid
            extra["reference_Hcal_optical_focusing_ratio_min"]=float(np.min(rat))
            extra["reference_Hcal_optical_focusing_ratio_max"]=float(np.max(rat))
            extra["reference_Hcal_optical_focusing_negative_count_54"]=int(np.sum(rat<0))
            extra["reference_Hcal_assumption"]="Hcal(z,n)=Href(z) for all rays: CONDITIONAL NOT OBSERVED"
            extra["R64_support_D_positive_certified_count_54"]=sum(
                row["ratio"]["denominator"].get("lower",-1)>0 for row in data)
            # High-ell logH_D from exact nonlinear derivative, *only if D>0 globally*
            p3pred=B**2*p3(ns,dvec,S)
            p4pred=.5*B**2*p4(ns,S)
            extra["second_order_l3_l4_predicted_RMS_logH"]=[lm_rms(p3pred,3,th,ph,ws),
                                              lm_rms(p4pred,4,th,ph,ws)]
            if Dglobmin>1e-8:
                f=skyeta-np.log(skyden)
                exact=[lm_rms(f,L,th,ph,ws) for L in (3,4)]
                extra["fullsky_exact_nonlin_l3_l4_RMS_logH"]=exact
                extra["fullsky_logH_domain"]="ALL_SKY_POINT_MODEL_POSITIVE"
            else:
                extra["fullsky_exact_nonlin_l3_l4_RMS_logH"]=None
                extra["fullsky_logH_domain"]="POINT_MODEL_NEGATIVE_DOMAIN_SOMEWHERE"
            rows.append(extra)
        output[name]={"rank_field":mod["rank"],"model_adequacy_p_working":mod["adequacy_p"],
                      "nonlinear_source_scope":mod["mean_family_scope"],"by_z":rows}
    return {"models":output,"source_result_sha256":hashlib.sha256(PATH.read_bytes()).hexdigest(),
       "source_original_result_sha256":hashlib.sha256(BASE.read_bytes()).hexdigest(),
       "source_selected_groups":obj["source_rows"],
       "z_evaluation":zs,"source_directions_n":len(n),
       "reference_flat_LCDM":{"H0_km_s_Mpc":H0,"Omega_m":om},
       "interpretation":"R64 point fits are SAME existing CF4 68D Gaussian source, not independent sky measurements; R64 nuisance means optical eta not physical Hcal; negative comparator is NOT observed NEC violation"}

def main():
    return {"schema":"htt.r71.p3_finitez_optical_physics/1",
       "exact_source_tests":source_summary(),
       "optical_positive_focusing_negative_HD_counterexample":optical_toy(),
       "axisymmetric_tied_ell4_check":axial_harmonic(),
       "scope":"derived Sachs and conditional R64 finite-source diagnostics, no new physical anisotropy significance or native solver"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False))
