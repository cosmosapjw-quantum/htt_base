"""Physical spin-2 E/B source mask and finite masked harmonic response.

HEALPix polarization uses Q/U on one Galactic spin-2 frame, as in the
previous source-matched Planck 2018 PR3 pipeline. A finite l<=lmax
masked joint E/B inverse is exact only on that declared subspace;
high-l contamination, foreground residuals, and physical CMB nulls
are NOT calibrated by this module.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor,cho_solve


class Spin2ResponseError(ValueError):
    pass


def real_spin2_design(*,nside:int,lmax:int):
    """Q/U design; for each ell, E modes then B modes (m0,cos,sin...)."""
    import healpy as hp
    if (not isinstance(nside,int) or nside<8 or not hp.isnsideok(nside)
        or not isinstance(lmax,int) or lmax<2 or lmax>3*nside-1):
        raise Spin2ResponseError("HEALPix nside>=8, 2<=lmax<=3*nside-1")
    nalm=hp.Alm.getsize(lmax)
    X=[]
    meta=[]
    for ell in range(2,lmax+1):
        combos=[(0,"m0")]
        for m in range(1,ell+1):
            combos.extend(((m,"cos"),(m,"sin")))
        for spin in ("E","B"):
            for m,phase in combos:
                E=np.zeros(nalm,complex)
                B=np.zeros(nalm,complex)
                arr=E if spin=="E" else B
                val=1. if m==0 else (1/np.sqrt(2.) if phase=="cos" else -1j/np.sqrt(2.))
                arr[hp.Alm.getidx(lmax,ell,m)]=val
                q,u=hp.alm2map_spin([E,B],nside=nside,spin=2,lmax=lmax)
                X.append(np.concatenate((q,u)))
                meta.append({"ell":ell,"spin":spin,"m":m,"phase":phase})
    return np.column_stack(X),meta


def fit_spin2_operator(X,selected):
    """Source-selected same-P-mask joint LS, Q and U share identical rows."""
    design=np.asarray(X)
    m=np.asarray(selected)
    if (design.ndim!=2 or design.dtype.kind!="f" or
        m.dtype.kind!="b" or design.shape[0]!=2*len(m) or
        not np.isfinite(design).all() or int(m.sum())<design.shape[1]+1):
        raise Spin2ResponseError("finite physical spin-2 Q/U design and shared mask required")
    choose=np.r_[m,m]
    A=design[choose]
    G=A.T@A
    eig=np.linalg.eigvalsh(G)
    if eig[0]<=0 or np.sqrt(eig[-1]/eig[0])>1e8:
        raise Spin2ResponseError("joint spin-2 masked design rank/conditioning failed")
    op=cho_solve(cho_factor(G,lower=True,check_finite=False),A.T,check_finite=False)
    identity=float(np.max(abs(op@A-np.eye(design.shape[1]))))
    if identity>2e-9:
        raise Spin2ResponseError("masked spin2 low-harmonic reproduction failed")
    return op,{"pixels":int(m.sum()),"rank":int(A.shape[1]),
               "design_condition":float(np.sqrt(eig[-1]/eig[0])),
               "identity_maxabs":identity}


def finite_spin2_leakage(low,high,low_meta,high_meta,selected):
    """Emit observable low E/B from non-modeled higher E and B excitations."""
    op,info=fit_spin2_operator(low,selected)
    m=np.r_[selected,selected]
    if (high.ndim!=2 or high.shape[0]!=low.shape[0] or
        len(high_meta)!=high.shape[1] or len(low_meta)!=low.shape[1]
        or not np.isfinite(high).all()):
        raise Spin2ResponseError("low/high bases must share spin conventions and pixels")
    block=op@high[m]
    result={"all_high_to_low_spectral_norm":float(np.linalg.norm(block,2)),
            "all_high_to_low_frobenius_norm":float(np.linalg.norm(block,"fro")),
            "source_mask_fit":info}
    for spin_low in ("E","B"):
        lo=[i for i,m in enumerate(low_meta) if m["spin"]==spin_low]
        for spin_hi in ("E","B"):
            hi=[i for i,m in enumerate(high_meta) if m["spin"]==spin_hi]
            part=block[np.ix_(lo,hi)]
            result[f"{spin_low}_from_{spin_hi}_spectral_norm"]=float(np.linalg.norm(part,2))
            result[f"{spin_low}_from_{spin_hi}_frobenius_norm"]=float(np.linalg.norm(part,"fro"))
    return block,result


def source_EB_band_powers(coeff,meta):
    """Source projected *finite-basis* E/B harmonics in microK^2."""
    x=np.asarray(coeff)
    if (x.ndim!=2 or np.iscomplexobj(x) or not np.isfinite(x).all()
        or len(meta)!=x.shape[1]):
        raise Spin2ResponseError("source processing E/B coefficients and matched mode chart required")
    results={}
    for ell in sorted(set(int(z["ell"]) for z in meta)):
        results[str(ell)]={}
        for spin in ("E","B"):
            k=[i for i,q in enumerate(meta) if q["spin"]==spin and int(q["ell"])==ell]
            if len(k)!=2*ell+1:
                raise Spin2ResponseError("invalid real physical E/B spin band cardinality")
            results[str(ell)][spin]=np.sum(x[:,k]**2,axis=1)/(2*ell+1)
    return results


def source_polar_mask(mask_paths,*,nside_in=2048,nside_out=64,coverage_floor=.995,return_fine=False):
    """Actual Planck NSIDE2048 NESTED polarization PMASK intersection -> RING."""
    from pathlib import Path
    from astropy.io import fits
    import healpy as hp
    from .mes_eps_measurement_bridge import nested_children_coverage_to_ring
    if nside_in<nside_out or nside_in%nside_out or not 0<coverage_floor<=1:
        raise Spin2ResponseError("valid mask downgrade and confidence threshold required")
    if not isinstance(mask_paths,(list,tuple)) or not mask_paths:
        raise Spin2ResponseError("actual source mask file list required")
    combined=None
    for file in mask_paths:
        p=Path(file)
        if not p.is_file():
            raise Spin2ResponseError(f"source native polarization mask not found: {p}")
        with fits.open(p,memmap=True) as f:
            h=f[1]
            if (h.header.get("NSIDE")!=nside_in or
                h.header.get("ORDERING")!="NESTED" or
                "PMASK" not in h.columns.names):
                raise Spin2ResponseError(f"native Planck polarization mask mismatch: {p}")
            valid=np.asarray(h.data["PMASK"])>.5
            if combined is None:
                combined=valid.copy()
            else:
                combined&=valid
    coarse=nested_children_coverage_to_ring(combined,nside_in=nside_in,nside_out=nside_out)
    chosen=coarse>=coverage_floor
    meta={"selected_nside_out_pix":int(np.sum(chosen)),
          "ordering":"RING","nside_in":nside_in,"nside_out":nside_out,
          "coverage_floor":float(coverage_floor),"files":list(map(str,mask_paths))}
    return (chosen,meta,combined) if return_fine else (chosen,meta)
