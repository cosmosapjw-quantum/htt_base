"""Observed-source conditional CF4 H_eff(z, n) survey-window diagnostics.

The primary estimator is the weighted geometrical mean of cz_i / D_i where
D_i = 10**[(DM_i-25)/5] Mpc. It is NOT local geometry Theta/3, and
log(cz/D) is not the native distance-modulus likelihood.
Errors here are a declared independent working law; shared CF4 method
calibration, peculiar-velocity correlations and selection are NOT included.
"""
from __future__ import annotations
import numpy as np

C_KM_S = 299792.458
K_LOG = np.log(10.)/5


class HubbleWindowError(ValueError):
    pass


def source_log_hubble(z, distance_modulus, sigma_modulus, *,
                      velocity_dispersion_kms=250.):
    """Log of the numerical value of (cz/D) / [1 km s^-1 Mpc^-1]."""
    z=np.asarray(z)
    mu=np.asarray(distance_modulus)
    s=np.asarray(sigma_modulus)
    if any(np.iscomplexobj(a) for a in (z,mu,s)):
        raise HubbleWindowError("real source fields required")
    z,mu,s=map(lambda a:np.asarray(a,float),(z,mu,s))
    if (z.ndim!=1 or z.shape!=mu.shape or z.shape!=s.shape
        or not np.isfinite(z).all() or not np.isfinite(mu).all()
        or not np.isfinite(s).all() or np.any(z<=0) or np.any(z>.5)
        or np.any(s<=0) or not np.isfinite(velocity_dispersion_kms)
        or velocity_dispersion_kms<0):
        raise HubbleWindowError("positive redshifts and distance-modulus errors needed")
    y=np.log(C_KM_S*z)-K_LOG*(mu-25.)
    # Linearized log-redshift velocity-response variance, independent by assumption.
    sigma2=(K_LOG*s)**2+(velocity_dispersion_kms/(C_KM_S*z))**2
    return y, np.sqrt(sigma2)


def _validate(z,n,y,sigma,method,group_id):
    x=list(map(np.asarray,(z,n,y,sigma,method,group_id)))
    zz,nn,yy,ss,ff,ids=x
    if (zz.ndim!=1 or nn.shape!=(len(zz),3) or
        any(a.shape!=(len(zz),) for a in (yy,ss,ff,ids))
        or len(np.unique(ids))!=len(ids) or np.iscomplexobj(nn)
        or np.iscomplexobj(zz) or np.iscomplexobj(yy)
        or np.any(zz<=0) or np.any(zz>.5) or np.any(ss<=0)
        or not all(np.isfinite(a).all() for a in (zz,nn,yy,ss))
        or not np.allclose(np.sum(nn.astype(float)**2,axis=1),1,atol=1e-11)):
        raise HubbleWindowError("finite group-unique redshift, direction and working law expected")
    return np.asarray(zz,float),np.asarray(nn,float),np.asarray(yy,float),np.asarray(ss,float),np.asarray(ff).astype('U40')


def directional_window_summary(z,n,log_h,sigma,method,group_id,windows,
                               *,min_sources=15):
    """O(n*k) source-window mean, leakage and diagonal-error cross-window covariance.

    For a *fixed* source log-H response:
       y_i = log H + n_i.B/(cz_i) + n_i.D + (n_i n_j-I/3)S_ij + ...
    window w_ki ∝ inv(sigma_i^2)*1_window. Thus
       log H_W = log H + kB_W.B + kD_W.D + kS_W:S + ...
    kB units (km/s)^-1, kD and kS dimensionless.
    All windows share any common source IDs; do NOT treat their means independent.
    """
    zz,nn,yy,ss,ff=_validate(z,n,log_h,sigma,method,group_id)
    if not isinstance(windows,(list,tuple)) or not windows:
        raise HubbleWindowError("nonempty predeclared window list expected")
    if not isinstance(min_sources,int) or min_sources<1:
        raise HubbleWindowError("minimum supported source count positive integer")
    rows=[]
    names=[]
    counts=[]
    groups={}
    for spec in windows:
        if not isinstance(spec,dict) or set(spec)!={"id","min_z","max_z"}:
            raise HubbleWindowError("window spec needs id,min_z,max_z")
        k=str(spec["id"])
        lo=float(spec["min_z"]);hi=float(spec["max_z"])
        if (not k or k in names or not np.isfinite(lo) or
            not np.isfinite(hi) or lo<=0 or lo>=hi or hi>.5):
            raise HubbleWindowError("distinct positive half-open windows required")
        pick=(zz>=lo)&(zz<hi)
        if pick.sum()<min_sources:
            raise HubbleWindowError(f"under-supported window {k}: {pick.sum()}")
        row=np.zeros(len(zz))
        row[pick]=ss[pick]**-2
        row/=np.sum(row)
        rows.append(row)
        names.append(k)
        counts.append(int(pick.sum()))
        values,nums=np.unique(ff[pick],return_counts=True)
        groups[k]={str(m):int(c) for m,c in zip(values,nums,strict=True)}
    weights=np.vstack(rows)
    cov=(weights*ss[None,:]**2)@weights.T
    cov=.5*(cov+cov.T)
    avg=weights@yy
    kbulk=weights@(nn/(C_KM_S*zz[:,None]))
    kdipole=weights@nn
    stf=np.einsum("ni,nj->nij",nn,nn)-np.eye(3)[None,:,:]/3
    kquadrupole=np.einsum("wn,nij->wij",weights,stf,optimize=True)
    eigen=np.linalg.eigvalsh(cov)
    scale=max(np.max(np.abs(eigen)),1e-300)
    if eigen[0]<-1e-10*scale:
        raise HubbleWindowError("working cross-window covariance is not PSD")
    diagon=np.sqrt(np.diag(cov))
    return {
        "window_ids":names,
        "source_count":counts,
        "by_method_counts":groups,
        "logH_window_mean":avg,
        "H_eff_km_s_Mpc":np.exp(avg),
        "H_eff_conditional_1sigma_km_s_Mpc":np.exp(avg)*diagon,
        "covariance_logH_working_diagonal_only":cov,
        "correlation_logH_working_diagonal_only":cov/np.outer(diagon,diagon),
        "bulk_response_per_km_s":kbulk,
        "bulk_response_per_300_km_s":300*kbulk,
        "angular_dipole_response":kdipole,
        "STF2_angular_quadrupole_response":kquadrupole,
        "weight_operator":weights,
        "declared_correlation_model":"independent source modulus errors and 250 km/s diagonal scatter only",
        "physical_identification":"NO: observed H_eff and window leakage, not GR expansion/shear/tilt",
    }


def injected_window_deviation(summary, *, bulk_velocity_kms=None,
                              angular_dipole=None, stf2=None):
    """Exact response for stated first-order *log-H* model, not nonlinear ray tracing."""
    k=np.asarray(summary["bulk_response_per_km_s"])
    out=np.zeros(k.shape[0],float)
    for name,value,resp in (("bulk",bulk_velocity_kms,k),
                            ("angular",angular_dipole,summary["angular_dipole_response"])):
        if value is not None:
            v=np.asarray(value,float)
            if v.shape!=(3,) or not np.isfinite(v).all():
                raise HubbleWindowError(f"invalid {name} coefficient vector")
            out=out+np.asarray(resp)@v
    if stf2 is not None:
        t=np.asarray(stf2,float)
        if (t.shape!=(3,3) or not np.isfinite(t).all()
            or not np.allclose(t,t.T,atol=1e-12)
            or abs(np.trace(t))>1e-12):
            raise HubbleWindowError("symmetric tracefree 3x3 angular response expected")
        out=out+np.einsum("wij,ij->w",summary["STF2_angular_quadrupole_response"],t)
    return out
