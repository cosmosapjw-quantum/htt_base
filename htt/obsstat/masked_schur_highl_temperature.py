"""Finite Planck T high-mode Schur/mask forward-response, source-conditional.

At fixed selected pixels and harmonic chart X=[XL,XH], the exact identity
restricted_aL - joint_aL = (XL'XL)^-1 XL'XH joint_aH
holds without a cosmological likelihood, even for arbitrary foregrounds.

Schur S=GLL-GLH GHH^-1 GHL profiles unknown ell6..12 finite nuisance
modes. The beam/pixel response is a declared nominal scenario, NOT an
inversion of the actual Planck component-separation release transfer.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.linalg import cho_factor,cho_solve,eigh


class MaskSchurError(ValueError):
    pass


@dataclass
class MaskSchurGeometry:
    x: np.ndarray
    selected: np.ndarray
    low: tuple
    high: tuple
    full: tuple
    profiled: tuple
    cross: np.ndarray
    K: np.ndarray
    low_count: int
    diagnostics: dict


def make_geometry(design,mask,*,low_count=36,max_condition=2e7):
    v=np.asarray(design)
    m=np.asarray(mask)
    if (v.ndim!=2 or v.dtype.kind not in 'fi' or m.dtype.kind!='b'
        or len(v)!=len(m) or not np.isfinite(v).all()
        or not isinstance(low_count,int) or low_count<16
        or not low_count<v.shape[1] or m.sum()<=v.shape[1]):
        raise MaskSchurError("matching selected real harmonic geometry needed")
    x=np.asarray(v[m],float)
    gram=x.T@x
    gram=(gram+gram.T)*.5
    spectrum=np.linalg.eigvalsh(gram)
    if spectrum[0]<=0 or np.sqrt(spectrum[-1]/spectrum[0])>max_condition:
        raise MaskSchurError("mask geometry not numerically identifiable")
    GL=gram[:low_count,:low_count]
    GH=gram[low_count:,low_count:]
    C=gram[:low_count,low_count:]
    fL=cho_factor(GL,lower=True,check_finite=False)
    fH=cho_factor(GH,lower=True,check_finite=False)
    fF=cho_factor(gram,lower=True,check_finite=False)
    K=cho_solve(fL,C,check_finite=False)
    S=GL-C@cho_solve(fH,C.T,check_finite=False)
    S=(S+S.T)*.5
    fs=cho_factor(S,lower=True,check_finite=False)
    eigen=eigh(S,GL,eigvals_only=True,check_finite=False)
    if eigen[0]<=0 or eigen[-1]>1+1e-10:
        raise MaskSchurError("nuisance-profiled source Gram outside positive information range")
    return MaskSchurGeometry(
        x,m.copy(),fL,fH,fF,fs,C,K,low_count,
        {"selected_pixels":int(m.sum()),
         "restricted_columns":low_count,"high_columns":v.shape[1]-low_count,
         "full_design_condition":float(np.sqrt(spectrum[-1]/spectrum[0])),
         "profile_information_min":float(eigen[0]),
         "profile_information_median":float(np.median(eigen)),
         "profile_information_max":float(eigen[-1]),
         "low_ell2to3_high_nuisance_norm":float(np.linalg.norm(K[4:16],2)),
         "l_gt_max":"UNKNOWN_NOT_IN_FINITE_MODEL",
         "interpretation":"source mask/profile algebra, not calibrated Planck likelihood"})


def fit_source_batches(maps,geo:MaskSchurGeometry,*,chunk=48):
    z=np.asarray(maps)
    if z.ndim==1:z=z[None,:]
    if (z.ndim!=2 or z.dtype.kind not in 'fi'
        or z.shape[1]!=len(geo.selected) or not np.isfinite(z).all()
        or not isinstance(chunk,int) or chunk<1 or chunk>512):
        raise MaskSchurError("finite full source map rows and bounded batch size")
    small=[];full=[];rel=[]
    for i in range(0,len(z),chunk):
        data=np.asarray(z[i:i+chunk][:,geo.selected],float)
        rhs=geo.x.T@data.T
        a=cho_solve(geo.low,rhs[:geo.low_count],check_finite=False).T
        b=cho_solve(geo.full,rhs,check_finite=False).T
        delta=a-b[:,:geo.low_count]-b[:,geo.low_count:]@geo.K.T
        relative=np.max(abs(delta),axis=1)/np.maximum(np.max(abs(a),axis=1),1)
        if np.max(relative)>3e-11:
            raise MaskSchurError("restricted vs joint high-l identity fails")
        rhs_prof=rhs[:geo.low_count]-geo.cross@cho_solve(
            geo.high,rhs[geo.low_count:],check_finite=False)
        independent=cho_solve(geo.profiled,rhs_prof,check_finite=False).T
        if np.max(abs(independent-b[:,:geo.low_count]))>3e-10*max(np.max(abs(b)),1):
            raise MaskSchurError("profiled Schur estimator differs from full joint OLS")
        small.append(a)
        full.append(b)
        rel.extend(relative)
    return {"restricted":np.vstack(small),
            "joint":np.vstack(full),
            "max_relative_schur_identity":float(np.max(rel)),
            "rows":len(z)}


def nominal_beam_window(geo:MaskSchurGeometry,*,fwhm_arcmin=5.,
                        native_nside=2048,proc_nside=64):
    import healpy as hp
    if (not np.isfinite(fwhm_arcmin) or not 0<fwhm_arcmin<=60
        or not hp.isnsideok(native_nside) or not hp.isnsideok(proc_nside)
        or native_nside<proc_nside
        or geo.low_count!=36 or geo.K.shape!=(36,133)):
        raise MaskSchurError("fixed original l0..12 chart and nominal beam needed")
    win=hp.gauss_beam(fwhm=np.deg2rad(fwhm_arcmin/60),lmax=12)
    native=hp.pixwin(native_nside,lmax=12)
    coarse=hp.pixwin(proc_nside,lmax=12)
    ell=np.repeat(np.arange(13),2*np.arange(13)+1)
    if len(ell)!=169:raise MaskSchurError("invalid angular-harmonic chart")
    Beff=win*coarse
    transfer=Beff[ell]
    nom=geo.K[4:16]
    intrinsic=nom*transfer[36:][None,:]/transfer[4:16,None]
    return {
      "scope":"DECLARED_NOMINAL_NOT_ACTUAL_RELEASE_TRANSFER",
      "Gaussian_FWHM_arcmin":fwhm_arcmin,
      "native_pixel_window":{str(l):float(native[l]) for l in (2,3,8,12)},
      "analysis_pixel_window":{str(l):float(coarse[l]) for l in (2,3,8,12)},
      "gaussian_beam_window":{str(l):float(win[l]) for l in (2,3,8,12)},
      "nominal_Bell_product":{str(l):float(Beff[l]) for l in (2,3,8,12)},
      "observed_high_to_low_ell2to3_spectral_norm":float(np.linalg.norm(nom,2)),
      "nominal_intrinsic_high_to_low_ell2to3_spectral_norm":float(np.linalg.norm(intrinsic,2)),
      "relative_norm_change":float(np.linalg.norm(intrinsic,2)/np.linalg.norm(nom,2)-1),
      "physical_limits":"actual component separation beam/filter, nested averaging, polarization, foreground noise and ell>=13 unresolved",
    }



def nested_lmax_source_coefficients(maps,geo:MaskSchurGeometry, *,
                                    lmax_set=(5,8,10,12),chunk=48):
    """Reuse one X_ell0..12 masked RHS across all nested harmonic fits.

    Exact OLS with G[:p,:p] and b[:p] for p=(ellmax+1)^2.
    Benchmarks are at matched output/source precision; FFP signal/noise
    rows remain independent source realizations, not independent skies
    when summed into paired CMB+noise realizations.
    """
    data=np.asarray(maps)
    if data.ndim==1:data=data[None,:]
    if (data.ndim!=2 or data.shape[1]!=len(geo.selected)
        or data.dtype.kind not in 'fi' or not np.isfinite(data).all()
        or not isinstance(chunk,int) or not 1<=chunk<=256):
        raise MaskSchurError("finite complete selected HEALPix pixel rows needed")
    if not isinstance(lmax_set,(tuple,list)) or set(lmax_set)!={5,8,10,12}:
        raise MaskSchurError("fixed scientific lmax=(5,8,10,12) nested chart required")
    shapes={ell:(ell+1)**2 for ell in lmax_set}
    if geo.x.shape[1]!=169 or geo.low_count!=36:
        raise MaskSchurError("original full real ell0..12 chart required")
    gram=geo.x.T@geo.x
    fac={ell:cho_factor((gram[:k,:k]+gram[:k,:k].T)/2,lower=True,
                       check_finite=False)
         for ell,k in shapes.items()}
    out={ell:[] for ell in lmax_set}
    residual=[]
    for start in range(0,len(data),chunk):
        x=np.asarray(data[start:start+chunk][:,geo.selected],float)
        rhs=geo.x.T@x.T
        for ell,k in shapes.items():
            a=cho_solve(fac[ell],rhs[:k],check_finite=False).T
            out[ell].append(a[:,:36].copy())
        restricted=out[5][-1]
        full=cho_solve(geo.full,rhs,check_finite=False).T
        d=restricted-full[:,:36]-full[:,36:]@geo.K.T
        rel=np.max(abs(d),axis=1)/np.maximum(np.max(abs(restricted),axis=1),1)
        if np.max(rel)>2e-10:
            raise MaskSchurError("nested source coefficients violate high-l elimination identity")
        residual.extend(rel.tolist())
        np.testing.assert_allclose(out[12][-1],full[:,:36],rtol=5e-10,atol=5e-10)
    return {
        "lowl_by_lmax":{str(ell):np.vstack(rows) for ell,rows in out.items()},
        "Schur_identity_relative_max":float(max(residual)),
        "rows":len(data),
    }
