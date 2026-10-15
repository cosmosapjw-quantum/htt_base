"""Finite-resolution source-masked T harmonic response and high-ell aliasing.

A finite masked l<=lmax OLS cannot be equated with a beam- and
foreground-deconvolved physical CMB tensor likelihood. Components are on the
same RING HEALPix pixel basis and orthonormal real Y_lm chart.
"""
from __future__ import annotations
import numpy as np
from scipy.linalg import cho_factor,cho_solve


class LowellResponseError(ValueError):
    pass


def source_fit_matrix(design, selected, *, max_cond=1e8):
    """Small well-conditioned full-column OLS only; no n*n projector."""
    x=np.asarray(design)
    m=np.asarray(selected)
    if (x.ndim!=2 or x.dtype.kind not in "fi" or m.dtype.kind!="b"
        or m.shape!=(x.shape[0],) or np.count_nonzero(m)<=x.shape[1]
        or not np.isfinite(x).all()):
        raise LowellResponseError("matching selected finite harmonic pixels required")
    A=x[m].astype(float,copy=False)
    G=A.T@A
    eig=np.linalg.eigvalsh(G)
    if eig[0]<=0 or np.sqrt(eig[-1]/eig[0])>max_cond:
        raise LowellResponseError("masked harmonic normal equations not identifiable")
    factor=cho_factor(G,lower=True,check_finite=False)
    op=cho_solve(factor,A.T,check_finite=False)
    identity=np.max(np.abs(op@A-np.eye(A.shape[1])))
    if identity>3e-9:
        raise LowellResponseError(f"source harmonic operator identity residual {identity:g}")
    return op,{
        "sampled_pixels":int(m.sum()),
        "columns":int(x.shape[1]),
        "design_condition":float(np.sqrt(eig[-1]/eig[0])),
        "identity_residual":float(identity),
        "units":"orthonormal real harmonic basis",
    }


def leakage_matrix(low, high, selected, *, band=slice(4,16)):
    """(X_low' X_low)^(-1) X_low' X_high projected onto l=2,3 modes."""
    X=np.asarray(low,float)
    Y=np.asarray(high,float)
    if (X.ndim!=2 or Y.ndim!=2 or X.shape[0]!=Y.shape[0]
        or X.shape[1]<16 or not np.isfinite(Y).all() or
        not isinstance(band,slice) or band.start is None or band.stop is None
        or band.start<0 or band.stop>X.shape[1]):
        raise LowellResponseError("finite low/high orthonormal real harmonic source")
    R,meta=source_fit_matrix(X,selected)
    response=R[band,:]@Y[np.asarray(selected,bool)]
    sv=np.linalg.svd(response,compute_uv=False)
    return response,{
        "shape":list(response.shape),
        "spectral_norm":float(sv[0]) if len(sv) else 0.,
        "frobenius_norm":float(np.linalg.norm(response)),
        "finite_high_mode_scope":"only the supplied high basis, not unbounded true sky",
        "operator_identity_residual":meta["identity_residual"],
    }


def source_map_fit(map_values, design, selected):
    """One or batch maps, fit same source mask/operator across processing choices."""
    op,info=source_fit_matrix(design,selected)
    dat=np.asarray(map_values)
    if np.iscomplexobj(dat) or dat.ndim not in (1,2) or dat.shape[-1]!=len(selected) or not np.isfinite(dat).all():
        raise LowellResponseError("one/batch full NPIX finite real maps expected")
    arr=dat if dat.ndim==2 else dat[None,:]
    co=arr[:,selected]@op.T
    res=arr[:,selected] - co@design[selected].T
    rms=np.sqrt(np.mean(res**2,axis=1))
    info["residual_rms_microK"]=rms.tolist()
    return co if dat.ndim==2 else co[0],info


def band_rms(full_harmonic, *, ell=2):
    """Norm of fixed real ell band divided by sqrt(2ell+1), in native map units."""
    coeff=np.asarray(full_harmonic,float)
    if coeff.ndim not in (1,2) or not np.isfinite(coeff).all() or coeff.shape[-1]<(ell+1)**2:
        raise LowellResponseError("full real harmonic coefficients through desired ell required")
    a=coeff[...,ell*ell:(ell+1)**2]
    return np.sqrt(np.sum(a*a,axis=-1)/(2*ell+1))
