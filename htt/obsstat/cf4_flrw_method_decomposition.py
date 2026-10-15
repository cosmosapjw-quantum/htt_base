"""Source-conditioned Cosmicflows-4 FLRW-reference and method-mix decomposition.

Observed h_i=log(c z_i / D_i), D_i =10**((mu_i-25)/5) Mpc, is NOT H(z).
Flat-LCDM reference h_ref(z)=log(c z/d_L^FLRW(z)) has nontrivial z
dependence even when underlying H(z) is statistically isotropic.

For each fixed disjoint redshift window j and method m, with declared
diagonal sigma and weights w_i=1/sigma_i^2, let
   f_jm= W_jm/W_j, u_jm= sum_{i in jm}w_i h_i/W_jm.
The exact symmetric decomposition is
   Delta sum_m(f_m u_m) =
     sum_m Delta f_m * average(u_m)
     + sum_m average(f_m) * Delta u_m.
It is accounting, not causal identification. Fixed method-standardization
with one common pi across windows cancels *constant* method zero-point
shifts, but not method-depth or selection effects.
"""
from __future__ import annotations
from collections.abc import Sequence
import numpy as np
from .htt_hubble_depth_window import C_KM_S, K_LOG, source_log_hubble
from .cf4_apparent_kinematic_distribution import luminosity_distance_flat_lcdm


class DepthMethodDomainError(ValueError):
    pass


def flrw_log_cz_over_luminosity(z, *, H0=74.6, omega_m=0.3153):
    """Flat-LCDM reference of apparent H_eff [km s^-1 Mpc^-1] (log numeric)."""
    arr=np.asarray(z)
    if np.iscomplexobj(arr) or arr.ndim!=1:
        raise DepthMethodDomainError("one-dimensional real redshift sample")
    z=np.asarray(arr,float)
    d_l,*_=luminosity_distance_flat_lcdm(z,H0=H0,omega_m=omega_m)
    return np.log(C_KM_S*z/d_l)


def exact_symmetric_decomposition(f_near,f_far,u_near,u_far):
    """Return exact arithmetic partition of weighted far-minus-near mean."""
    xs=[np.asarray(x) for x in (f_near,f_far,u_near,u_far)]
    if any(np.iscomplexobj(x) or x.ndim!=1 or not np.isfinite(x).all() for x in xs):
        raise DepthMethodDomainError("finite real fractions/means required")
    a,b,yn,yf=[np.asarray(x,float) for x in xs]
    if not a.shape==b.shape==yn.shape==yf.shape or a.size<1:
        raise DepthMethodDomainError("matching finite method mixture")
    if (np.any(a<0) or np.any(b<0)
        or not np.isclose(a.sum(),1,atol=1e-12,rtol=0)
        or not np.isclose(b.sum(),1,atol=1e-12,rtol=0)):
        raise DepthMethodDomainError("proper normalized nonnegative method fractions")
    center=float(np.mean(np.r_[yn,yf]))
    mixing=float(np.dot(b-a,(yf+yn)/2-center))
    within=float(np.dot((a+b)/2,yf-yn))
    whole=float(np.dot(b,yf-center)-np.dot(a,yn-center))
    if abs(mixing+within-whole)>2e-12*max(abs(whole),1):
        raise DepthMethodDomainError("method-mix accounting identity lost")
    return {"total":whole,"composition":mixing,"within_method":within,
            "closure_residual":mixing+within-whole}


def _prepare_bins(bins):
    if not isinstance(bins,(list,tuple)) or len(bins)<2:
        raise DepthMethodDomainError("at least two fixed nonempty bins")
    pairs=[]
    for item in bins:
        if isinstance(item,dict):
            lo=float(item["min_z"]);hi=float(item["max_z"])
        elif len(item)==2:
            lo,hi=map(float,item)
        else:
            raise DepthMethodDomainError("bin expects lower and upper")
        if not np.isfinite([lo,hi]).all() or not 0<lo<hi<=.5:
            raise DepthMethodDomainError("finite increasing physical z support")
        if pairs and lo<pairs[-1][1]-1e-14:
            raise DepthMethodDomainError("method bins must be disjoint and ordered")
        pairs.append((lo,hi))
    return pairs


def method_depth_source_moments(z,mu,sigma_mu,method,group_id,windows,
                                *, velocity_dispersion_kms=250.):
    """Report n_bins x n_methods source means, covariance and method mix.

    This does NOT estimate a physical CF4 likelihood: no shared calibration
    / peculiar velocities / selection normalisation is in diagonal sigma.
    """
    zz=np.asarray(z);ff=np.asarray(method);ids=np.asarray(group_id)
    if (zz.ndim!=1 or ff.shape!=zz.shape or ids.shape!=zz.shape
        or len(np.unique(ids))!=len(zz) or np.iscomplexobj(zz)
        or len(zz)<4):
        raise DepthMethodDomainError("aligned unique CF4 grouped sources")
    bins=_prepare_bins(windows)
    y,sig=source_log_hubble(z,mu,sigma_mu,
                           velocity_dispersion_kms=velocity_dispersion_kms)
    names=sorted(set(str(x) for x in ff))
    if any(not x for x in names):
        raise DepthMethodDomainError("method family nonempty")
    nbin=len(bins);nm=len(names)
    counts=np.zeros((nbin,nm),int)
    total_weight=np.zeros((nbin,nm))
    means=np.zeros((nbin,nm))
    variance=np.zeros((nbin,nm))
    sel=np.zeros(len(zz),bool)
    sum_wsq=np.zeros((nbin,nm))
    source_weights=np.zeros((nbin,nm,len(zz)))
    for k,(lo,hi) in enumerate(bins):
        zpick=(zz>=lo)&(zz<hi)
        if not np.any(zpick):
            raise DepthMethodDomainError("empty radial shell")
        if np.any(sel & zpick):
            raise DepthMethodDomainError("sources assigned to multiple disjoint bins")
        sel|=zpick
        for i,name in enumerate(names):
            pick=zpick & (ff==name)
            if not np.any(pick):
                raise DepthMethodDomainError(
                    f"method {name} absent in [{lo},{hi}); cannot fully standardize")
            w=1/(sig[pick]**2)
            wt=float(w.sum())
            counts[k,i]=int(pick.sum())
            total_weight[k,i]=wt
            means[k,i]=np.dot(w,y[pick])/wt
            variance[k,i]=1/wt
            sum_wsq[k,i]=float(w@w)
            source_weights[k,i,pick]=w/wt
    if not np.allclose(source_weights.sum(axis=-1),1,atol=1e-12):
        raise DepthMethodDomainError("source-group weights do not partition each method cell")
    fractions=total_weight/total_weight.sum(axis=1,keepdims=True)
    # Method-free estimator reproduces previous H01 result algebraically.
    raw=(fractions*means).sum(axis=1)
    cov=np.diag((fractions**2*variance).sum(axis=1))
    return {
        "bins":bins,"method_names":names,
        "counts":counts,"source_sigma":sig,"source_logh":y,
        "source_id":np.asarray(ids),
        "source_method":np.asarray(ff).astype("U40"),
        "method_weight_sum":total_weight,
        "method_weight_fraction":fractions,
        "method_logh_means":means,
        "method_logh_variance_diagonal":variance,
        "effective_n_by_method_cell":total_weight**2/sum_wsq,
        "method_cell_source_weights":source_weights,
        "raw_shell_logh":raw,
        "raw_shell_diagonal_covariance":cov,
        "scope":"PREDECLARED_BINS_SOURCE_DIAGONAL_WORKING_LAW",
    }


def reference_residual_moments(source,z,*,H0=74.6,omega_m=.3153):
    """Exact same-source and same-method-window reference removal."""
    ref=flrw_log_cz_over_luminosity(z,H0=H0,omega_m=omega_m)
    m=source["method_cell_source_weights"]
    # Source model distances are evaluated for EVERY original group BEFORE
    # aggregation (do not use a mean z as a substitute for mean log dL).
    x=np.einsum("jmi,i->jm",m,ref,optimize=True)
    resid=source["method_logh_means"]-x
    f=source["method_weight_fraction"]
    return {
      "reference_method_logh_mean":x,
      "residual_method_logh_mean":resid,
      "reference_shell_logh":np.sum(f*x,axis=1),
      "residual_shell_logh":np.sum(f*resid,axis=1),
      "source_ref_logh":ref,
      "flat_LCDM_H0_km_s_Mpc":H0,
      "flat_LCDM_Omega_m":omega_m,
      "physical_interpretation":"MODEL_DEPENDENT_FLRW_DISTANCE_LAW_REMOVAL_NOT_SOURCE_SELECTION_CORRECTION",
    }


def constant_method_standardization(source,matrix,*,policy="min_share",
                                    declared_weights=None):
    """Same method mixture pi in ALL shells; conditional source moment only.

    The declared reference mixture is not matched sky/redshift/host selection
    within a method. Very small cell counts can invalidate substantive
    interpretation even though a mathematical output exists.
    """
    f=np.asarray(source["method_weight_fraction"],float)
    y=np.asarray(matrix,float)
    v=np.asarray(source["method_logh_variance_diagonal"],float)
    if y.shape!=f.shape or not np.isfinite(y).all():
        raise DepthMethodDomainError("matching method-specific source means")
    if policy=="min_share" and declared_weights is None:
        p=f.min(axis=0)
        p=p/p.sum()
    elif policy=="declared" and declared_weights is not None:
        p=np.asarray(declared_weights,float)
        if (p.shape!=(f.shape[1],) or not np.isfinite(p).all()
            or np.any(p<0) or not np.isclose(p.sum(),1,atol=1e-12)):
            raise DepthMethodDomainError("declared nonnegative fixed normalized mixture")
    else:
        raise DepthMethodDomainError("explicit valid standardisation mixture policy")
    h=y@p
    source_weight=np.einsum("m,jmi->ji",p,source["method_cell_source_weights"])
    variance=np.einsum("m,jm->j",p*p,v)
    if not np.allclose(source_weight.sum(axis=1),1,atol=1e-12):
        raise DepthMethodDomainError("standardized weights not normalized per shell")
    kish=1/np.sum(source_weight**2,axis=1)
    return {
       "method_mix_pi":p,
       "logh":h,
       "variance_diagonal":variance,
       "conditional_1sigma_logh":np.sqrt(variance),
       "source_kish_effective_n":kish,
       "max_observation_reweight_relative_to_original_shell_method_fraction":np.max(
           np.divide(p[None,:],f,out=np.full_like(f,np.nan),where=f>0),axis=1),
       "invariance_to_fixed_method_zero_points_in_depth_contrast":"EXACT_IF_WEIGHTS_AND_MIX_HELD_FIXED",
       "physical_source_selection_corrected":False,
    }
