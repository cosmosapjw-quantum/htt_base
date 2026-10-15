"""CF4 apparent STF source transfer ambiguity and conditional identified subspaces.

Input observational law is real grouped CF4 (DMzp - flat-LCDM mu_ref),
not the proper-time photon energy drift. A placeholder transfer shape g(z)
maps an angular STF tensor coefficient gamma (dimensionless) to distance
modulus shifts B_gamma = -(5/ln10) g(z) [n_i T^a_ij n_j].

The exact covariant K01 photon law at a single event only supplies
an angular tensor contraction; it does NOT specify the integrated
luminosity-distance/geodesic/peculiar-velocity/selection g(z). All g(z)
below are expressly counterfactual templates, NOT native GR solutions.

Within each g(z), method intercept, method depth slope, bulk and angular
dipole nuisance are profiled under the existing *fixed diagonal Gaussian
working law* (reported eDMzp, +0.15 mag, 250 km/s).
Three indispensable checks:
  - source previous g(z)=1 result reproduces prior CF4 5D apparent STF.
  - unknown overall gain lambda>0 gives exactly gamma/lambda and
    covariance/lambda^2, hence no finite physical shear amplitude bound.
  - unrestricted method-specific 5D quadrupole calibration nuisance,
    B_m=1_{method=m} B, spans B=sum B_m exactly: 5D physical parameter
    is unidentifiable even though the restricted 5D source fit has rank5.

No physical cosmological 1+3 shear posterior, measured acceleration,
vorticity, tilt, CF4 selection-corrected odds or observational p-values.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_triangular

from .cf4_apparent_kinematic_distribution import model_matrix,stf2_orthonormal
from .cf4_schur_information import profile_stf_information


class CF4PhysicalBridgeError(ValueError):
    pass


KAPPA=5/np.log(10)
KERNELS=("unit_angular_endpoint","linear_z_over_0p05",
         "reciprocal_0p05_over_z","early_late_1plusz")


def checked_z(z):
    z=np.asarray(z)
    if (np.iscomplexobj(z) or z.ndim!=1 or len(z)<1
        or not np.isfinite(z).all()
        or np.any(z<.01-1e-12) or np.any(z>.1+1e-12)):
        raise CF4PhysicalBridgeError("real registered source CMB redshift 0.01..0.1")
    return np.asarray(z,float)


def declared_response_kernel(z,name):
    """Radial model stress tests, NONE a physical verified light-cone kernel."""
    t=checked_z(z)
    if name not in KERNELS:
        raise CF4PhysicalBridgeError("one of fixed four source response alternatives expected")
    if name=="unit_angular_endpoint":
        g=np.ones(len(t))
    elif name=="linear_z_over_0p05":
        g=t/.05
    elif name=="reciprocal_0p05_over_z":
        g=.05/t
    else:
        # Smooth positive mild source evolution, normalized at z=.05.
        g=(1+t)/(1+.05)
    assert np.isfinite(g).all() and np.min(g)>0
    return g


def cf4_working_model(z,n,methods,dm,err,*,kernel_name):
    """Construct actual-source matrix and declared fixed-error law."""
    zz=checked_z(z)
    look=np.asarray(n,float)
    cat=np.asarray(methods)
    mags=np.asarray(dm)
    errs=np.asarray(err)
    if (look.shape!=(len(zz),3) or cat.shape!=(len(zz),)
        or mags.shape!=(len(zz),) or errs.shape!=(len(zz),)
        or np.iscomplexobj(mags) or np.iscomplexobj(errs)
        or not np.isfinite(mags).all() or not np.isfinite(errs).all()
        or np.any(errs<=0)):
        raise CF4PhysicalBridgeError("source-coupled DMzp eDMzp directions/methods")
    source=model_matrix(zz,look,cat,
        include_method_slope=True,include_bulk=True,
        include_angular_dipole=True,omega_m=.3153,H0=74.6)
    s=source["slices"]["shear"]
    if s.stop-s.start!=5:
        raise CF4PhysicalBridgeError("five Frobenius-orthonormal angular STF coefficients needed")
    response=declared_response_kernel(zz,kernel_name)
    X=np.asarray(source["design"],float).copy()
    X[:,s]*=response[:,None]
    width=source["redshift_velocity_width_basis_mag_per_kms"]
    std=np.sqrt(errs**2+.15**2+(250*width)**2)
    y=mags-source["reference_mu_mag"]
    return {"design":X,"error":std,"residual":y,"STF_slice":s,
            "g":response,"method_order":source["methods"],
            "working_model":"CF4 source flat-LCDM H0=74.6 omega_m=.3153 method slopes+bulk+dipole with diagonal 0.15mag+250kms noise",
            "source_sky_frame":"ICRS J2000 look; redshift Vcmb/c PROXY",
            "physical_cosmological_transfer":"UNKNOWN"}


def profile_declared_family(model):
    p=profile_stf_information(model["design"],model["residual"],
                              model["error"],model["STF_slice"])
    gamma=np.asarray(p["beta_signal"],float)
    info=np.asarray(p["relative_information_eigenvalues"],float)
    cov=np.asarray(p["signal_cov"],float)
    return {"gamma":gamma,"cov":cov,"relative_eigenvalues":info,
            "rank":p["signal_rank"],"nuisance_rank":p["nuisance_rank"],
            "chi2":p["chi2_profiled"],"dof":p["dof"],
            "schur_residual":p["normal_equation_residual"],
            "conditional_apparent_frobenius_norm":float(np.linalg.norm(gamma)),
            "source_fisher_profiled":p["fisher_profiled"],
            "source_condition_number":p["projected_signal_condition"]}


def physical_gain_degeneracy(gamma,cov,*,gain):
    """One fixed radial *shape* with unknown positive scalar normalization."""
    g=np.asarray(gamma)
    c=np.asarray(cov)
    if (g.shape!=(5,) or c.shape!=(5,5) or
        np.iscomplexobj(g) or np.iscomplexobj(c)
        or not np.isfinite(g).all() or not np.isfinite(c).all()
        or not np.isfinite(gain) or gain<=0):
        raise CF4PhysicalBridgeError("real apparent STF5/cov and positive hypothetical gain")
    return {"conditional_gamma_for_gain":g/gain,
            "conditional_cov_for_gain":c/gain**2,
            "gain":float(gain),
            "scope":"UNVERIFIED_PHYSICAL_TRANSFER_GAIN_NOT_A_POSTERIOR"}


def method_quadrupole_span_certificate(z,n,methods,source_response):
    """One algebraically admissible nuisance extension wipes out STF rank.

    If each of four CF4 method families is allowed a completely free
    direction-dependent 5D calibration term with the SAME source kernel,
      B = sum_m diag(1_method=m) B,
    so global angular STF cannot be separated. This is an explicit
    counterexample, not evidence that such a systematic actually occurs.
    It never claims that the true CF4 covariance contains these terms.
    """
    zz=checked_z(z)
    x=np.asarray(n,float)
    m=np.asarray(methods)
    g=np.asarray(source_response)
    if (x.shape!=(len(zz),3) or m.shape!=(len(zz),)
        or g.shape!=(len(zz),) or not np.isfinite(x).all()
        or not np.isfinite(g).all() or np.any(g<=0)):
        raise CF4PhysicalBridgeError("same CF4 source rows for method STF overlap")
    names=sorted(set(m.tolist()))
    if len(names)!=4:
        raise CF4PhysicalBridgeError("four registered CF4 method families required")
    T=stf2_orthonormal()
    q=-KAPPA*g[:,None]*np.einsum("ni,aij,nj->na",x,T,x,optimize=True)
    per=np.column_stack([q*(m==name)[:,None] for name in names])
    identity=float(np.max(abs(q-np.sum(
       per.reshape(len(zz),len(names),5),axis=1))))
    # No 35970x35970 projection. Column-scaled least squares checks the
    # exact span using just the 20-column nuisance basis.
    norms=np.linalg.norm(per,axis=0)
    if not np.all(norms>0):
        raise CF4PhysicalBridgeError("unsupported sparse source family quadrupole")
    U=per/norms
    Q,R=np.linalg.qr(U,mode="reduced")
    singular=np.linalg.svd(R,compute_uv=False)
    nuisance_rank=int(np.sum(singular>singular[0]*1e-10))
    residual=q-Q@(Q.T@q)
    residual_norm=float(np.linalg.norm(residual)/np.linalg.norm(q))
    if residual_norm>5e-12 or identity>5e-13:
        raise CF4PhysicalBridgeError("global quadrupole not contained in unrestricted method quadrupoles")
    return {
        "source_method_order":names,
        "source_method_nuisance_columns":len(names)*5,
        "source_method_nuisance_rank":nuisance_rank,
        "source_exact_B_minus_sum_Bm_maxabs":identity,
        "relative_projected_global_STF_norm":residual_norm,
        "global_STF_identified_rank_if_unrestricted_method_STF_allowed":0,
        "number_unidentified_global_STF_columns":5,
        "scope":"CONDITIONAL_COUNTEREXAMPLE_NOT_MEASURED_CALIBRATION_STF",
    }


def angular_axis_cosine(gamma_a,gamma_b):
    """STF Frobenius 5D orientations, not an observed cosmological axis odds."""
    a=np.asarray(gamma_a,float)
    b=np.asarray(gamma_b,float)
    if a.shape!=(5,) or b.shape!=(5,) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise CF4PhysicalBridgeError("two finite five-dimensional Frobenius STF vectors required")
    aa=np.linalg.norm(a);bb=np.linalg.norm(b)
    if aa<=0 or bb<=0:
        raise CF4PhysicalBridgeError("nontrivial STF orientation required")
    return float(np.clip(a@b/(aa*bb),-1.,1.))



def method_angular_calibration_alias_matrix(model,sky_look,methods):
    """Conditional d gamma_app / d angular method-calibration amplitude.

    Assume angular modulus contamination δmu_i=Σ_m 1_{m(i)=m}
         Q_a(n_i) alpha_{ma}, with alpha in mag (20 parameters).
    Holding the registered 14 method/bulk/dipole nuisance model fixed,
      δ gamma_app = (B^T P_N B)^-1 B^T P_N U alpha.
    This does NOT assign uncertainty or occurrence to actual angular
    method calibration. It quantifies SOURCE-WINDOW susceptibility.
    """
    X=np.asarray(model["design"],float)
    std=np.asarray(model["error"],float)
    y=np.asarray(model["residual"],float)
    s=model["STF_slice"]
    n=np.asarray(sky_look,float)
    fam=np.asarray(methods)
    if (X.ndim!=2 or s.stop-s.start!=5 or n.shape!=(len(X),3)
        or fam.shape!=(len(X),) or std.shape!=(len(X),)
        or y.shape!=(len(X),)
        or np.any(std<=0) or not np.isfinite(X).all()):
        raise CF4PhysicalBridgeError("registered observed and calibration STF source columns")
    names=sorted(set(fam.tolist()))
    if len(names)!=4:raise CF4PhysicalBridgeError("expected 4 registered method families")
    ix=np.r_[np.arange(s.start),np.arange(s.stop,X.shape[1])]
    B=X[:,s]/std[:,None]
    Z=X[:,ix]/std[:,None]
    Z/=np.linalg.norm(Z,axis=0)
    Q,_=np.linalg.qr(Z,mode="reduced")
    projected_B=B-Q@(Q.T@B)
    qsky=np.einsum("ni,aij,nj->na",n,stf2_orthonormal(),n,optimize=True)
    U=np.column_stack([qsky*(fam==name)[:,None] for name in names])
    projected_U=U/std[:,None]
    projected_U-=Q@(Q.T@projected_U)
    F=projected_B.T@projected_B
    alias=np.linalg.solve(F,projected_B.T@projected_U)
    if alias.shape!=(5,20) or not np.isfinite(alias).all():
        raise CF4PhysicalBridgeError("angular calibration alias matrix not finite")
    return {
      "alias_gamma_per_method_quadrupole_mag":alias,
      "method_names":names,
      "units":"apparent STF gamma / angular method coefficient in mag",
      "nuisance_scope":"METHOD_ANGULAR_CALIBRATION_UNMEASURED_SENSITIVITY_ONLY",
    }
