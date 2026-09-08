"""R7 thermal response and measured full harmonic carriers; no inference."""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from scipy.special import sph_harm_y

from common.r7_contracts import TensorRecord, finite_array, content_id
from .lorentz_sky_pullback import pullback_thermodynamic_temperature_field
from .planck_lowell_irrep_projection import real_harmonic_l2_to_stf, real_harmonic_l3_to_stf


def layout_scale(ell):
    """a_m=Re+i Im -> coefficients of (Y_l0,sqrt2 ReY,sqrt2 ImY)."""
    if not isinstance(ell,int) or ell<0: raise ValueError("nonnegative integer ell")
    return np.array([1.]+[v for _ in range(ell) for v in (np.sqrt(2.),-np.sqrt(2.))])


def stored_to_real(coefficients, ell, covariance=None):
    a=finite_array(coefficients,shape=(2*ell+1,));s=layout_scale(ell)
    c=None if covariance is None else finite_array(covariance,shape=(len(s),len(s)))*s[:,None]*s[None,:]
    return a*s,c


def real_to_stored(coefficients,ell):
    return finite_array(coefficients,shape=(2*ell+1,))/layout_scale(ell)


def real_design(directions, ell_max=5):
    n=finite_array(directions,ndim=2,name="directions")
    if n.shape[1]!=3 or not np.allclose(np.linalg.norm(n,axis=1),1.,atol=5e-13,rtol=0): raise ValueError("unit directions required")
    theta=np.arccos(np.clip(n[:,2],-1,1));phi=np.arctan2(n[:,1],n[:,0])
    columns=[]
    for ell in range(ell_max+1):
        columns.append(sph_harm_y(ell,0,theta,phi).real)
        for m in range(1,ell+1):
            y=sph_harm_y(ell,m,theta,phi)
            columns.extend((np.sqrt(2)*y.real,np.sqrt(2)*y.imag))
    return np.column_stack(columns)


@lru_cache(maxsize=2)
def pixel_fit_geometry(nside=64):
    import healpy as hp
    if nside!=64: raise ValueError("registered thermal fit uses NSIDE64")
    n=np.column_stack(hp.pix2vec(nside,np.arange(hp.nside2npix(nside))))
    n.setflags(write=False);y=real_design(n);y.setflags(write=False)
    return n,y


@dataclass(frozen=True)
class ProductResponse:
    product_id: str
    source_id: str
    beta: np.ndarray
    full_coefficients: np.ndarray
    retained: np.ndarray
    processing_id: str
    frame: str
    response_kind: str
    fit_rank: int
    fit_residual_rms_K: float
    assumptions: tuple[str,...]
    units: str = "K"
    numerical_status: str = "PIXEL_NUMERICAL_NO_CONTINUUM_ERROR_CERTIFICATE"


def build_product_response(product_spec, source_spec, beta, processing_policy) -> ProductResponse:
    for key in ("product_id","release","frame","units","correction","channel_convention","beam"):
        if not product_spec.get(key): raise ValueError(f"product response needs {key}")
    if product_spec["units"]!="K": raise ValueError("convert product to absolute temperature K explicitly")
    if source_spec.get("units")!="K" or not source_spec.get("source_id"):
        raise ValueError("absolute source temperature and identity required")
    n,y=pixel_fit_geometry()
    b=finite_array(beta,shape=(3,),name="beta")
    sky=pullback_thermodynamic_temperature_field(n,b,source_spec["temperature"])
    pixel_processor=processing_policy.get("pixel_processor")
    if product_spec["beam"]!="IDENTITY" and pixel_processor is None:
        raise ValueError("a named beam requires its actual pixel processing implementation")
    if pixel_processor is not None:
        if not processing_policy.get("processor_source_id"): raise ValueError("processor source identity required")
        sky=finite_array(pixel_processor(sky),shape=(len(n),),name="processed sky")
    weights=finite_array(processing_policy.get("mask_weights",np.ones(len(n))),shape=(len(n),))
    if np.any(weights<0) or np.any(weights>1) or not np.any(weights): raise ValueError("mask weights in [0,1] with nonempty support")
    weighted=y*np.sqrt(weights[:,None]);target=sky*np.sqrt(weights)
    coefficients,_,rank,_=np.linalg.lstsq(weighted,target,rcond=None)
    if rank!=36: raise ValueError("ell=0..5 simultaneous fit is rank deficient")
    residual=sky-y@coefficients
    policy_id=content_id({"product":product_spec,"mask":weights,
        "pixel_processor":processing_policy.get("processor_source_id"),"nside":64,"fit_ells":[0,5],"retained_ells":[2,5]})
    return ProductResponse(product_spec["product_id"],source_spec["source_id"],b,
        coefficients,coefficients[4:],policy_id,product_spec["frame"],"THERMAL_RESPONSE",int(rank),
        float(np.sqrt(np.average(residual**2,weights=weights))),
        ("positive blackbody thermodynamic temperature; Doppler weight one",
         "simultaneous NSIDE64 pixel fit ell=0..5 before retaining ell=2..5",
         "released-product experiment and its covariance/selection are not supplied by this thermal calculation"))


def build_tensor_record(retained_row, measurement_meta, covariance_provider) -> TensorRecord:
    row=finite_array(retained_row,shape=(32,),name="retained row")
    units=measurement_meta["units"]
    if units not in {"K","microK"}: raise ValueError("unsupported temperature units")
    factor=1. if units=="K" else 1e-6
    row=row*factor
    layout=measurement_meta["harmonic_layout"]
    scale=np.ones(32)
    if layout=="STORED_RE_IM": scale=np.concatenate([layout_scale(l) for l in range(2,6)]);row=row*scale
    elif layout!="ORTHONORMAL_REAL_M0_COS_SIN": raise ValueError("unknown harmonic layout")
    covariance=None;covariance_id=None
    if covariance_provider is not None:
        provided=covariance_provider(measurement_meta)
        covariance=finite_array(provided["covariance"],ndim=2)
        if provided["sample_id"]!=measurement_meta["sample_id"]: raise ValueError("covariance sample mismatch")
        if provided["units"]!=units or provided["harmonic_layout"]!=layout: raise ValueError("covariance convention mismatch")
        dim=len(covariance)
        if covariance.shape not in {(12,12),(32,32)}: raise ValueError("full low- or high-mode cross-covariance required")
        covariance=covariance*factor**2*scale[:dim,None]*scale[None,:dim]
        error=32*dim*np.finfo(float).eps*np.linalg.norm(covariance,2)
        if np.max(abs(covariance-covariance.T))>error or np.linalg.eigvalsh((covariance+covariance.T)/2).min() < -error:
            raise ValueError("invalid covariance")
        covariance_id=provided["covariance_id"]
    q=real_harmonic_l2_to_stf(real_to_stored(row[:5],2))
    o=real_harmonic_l3_to_stf(real_to_stored(row[5:12],3))
    return TensorRecord(measurement_meta["sample_id"],row,q,o,measurement_meta["frame"],
        measurement_meta["product_id"],measurement_meta["release"],measurement_meta["processing_id"],
        covariance,measurement_meta.get("source_realization_id"),measurement_meta.get("noise_realization_id"),
        mask_id=measurement_meta["mask_id"],covariance_id=covariance_id,
        covariance_role=measurement_meta.get("covariance_role","MEASUREMENT_COVARIANCE"))
