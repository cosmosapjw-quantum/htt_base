"""Exact finite selected-pixel RING-2048 -> RING-64 Planck polarization reduction.

Source PR3 CMB SMICA FFP10 packaged maps are HEALPix RING native NSIDE=2048
but the released Planck *observed* full SMICA map is NESTED.  Do not group
consecutive RING pixels into coarse parents.  The mapping here uses
HEALPix's NESTED hierarchy to locate exact parents, then reads each
simulation's native RING samples via verified native pixel positions.

Polarization convention POLCCONV/COORDSYS is absent from these FFP10 FITS
headers. U+ and U- chart hypotheses must remain separately named.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
import numpy as np


class PlanckFFPPolarError(ValueError):
    pass


@dataclass(frozen=True)
class ParentLookup:
    """One nside pair + read-only selected/source masks."""
    nside_in: int
    nside_out: int
    selected_ring: np.ndarray
    fine_ring_idx: np.ndarray
    fine_mask: np.ndarray
    valid_counts: np.ndarray
    nested_children: int
    idx_sha256: str

    @property
    def n_selected(self):
        return int(len(self.selected_ring))


def build_parent_lookup(nside_in, nside_out, chosen_ring,
                        source_fine_nested):
    import healpy as hp
    if (not isinstance(nside_in,int) or not isinstance(nside_out,int)
        or not hp.isnsideok(nside_in) or not hp.isnsideok(nside_out)
        or nside_out>nside_in or nside_in % nside_out != 0):
        raise PlanckFFPPolarError("valid native-to-target HEALPix nsides required")
    chosen=np.asarray(chosen_ring)
    fine=np.asarray(source_fine_nested)
    if (chosen.dtype != np.dtype(bool) or fine.dtype != np.dtype(bool)
        or chosen.shape!=(hp.nside2npix(nside_out),)
        or fine.shape!=(hp.nside2npix(nside_in),)
        or not np.any(chosen)):
        raise PlanckFFPPolarError("actual coarse RING boolean and fine NESTED boolean source masks")
    selected=np.flatnonzero(chosen)
    k=(nside_in//nside_out)**2
    parents=hp.ring2nest(nside_out,selected)
    # Allocated once, not per simulation.  For nside2048->64 about 30M
    # int32 indices, so ~120 MiB retained, rather than full sky dense ops.
    native_nested=(parents[:,None].astype(np.int64)*k
                   +np.arange(k,dtype=np.int64)[None,:])
    native_mask=np.asarray(fine[native_nested],bool)
    counts=native_mask.sum(axis=1)
    if np.any(counts==0):
        raise PlanckFFPPolarError("source mask has no fine pixels under one selected coarse parent")
    ring=hp.nest2ring(nside_in,native_nested.reshape(-1))
    if np.max(ring)>=hp.nside2npix(nside_in):
        raise PlanckFFPPolarError("native HEALPix RING index out of bounds")
    # nest2ring is a HEALPix permutation, and selected parents are unique.
    # A 30-million-entry np.unique on actual NSIDE2048 would be a needless
    # multigigabyte sort; assert it directly only for small synthetic grids.
    if (ring.size!=selected.size*k or
        (nside_in<=16 and len(np.unique(ring))!=len(ring))):
        raise PlanckFFPPolarError("one-to-one selected native lookup expected")
    ring=np.asarray(ring,dtype=np.int32).reshape(len(selected),k)
    native_mask.setflags(write=False);ring.setflags(write=False)
    counts=np.asarray(counts,dtype=np.int32)
    counts.setflags(write=False);selected.setflags(write=False)
    ident=hashlib.sha256(ring.tobytes()).hexdigest()
    return ParentLookup(nside_in,nside_out,selected,ring,native_mask,
                        counts,k,ident)


def coarse_selected_mean_rings(native_ring_vector,lookup:ParentLookup,
                               *,use_source_mask=True):
    """Average Q/U/I native RING over fine children of each selected parent."""
    arr=np.asarray(native_ring_vector)
    if (np.iscomplexobj(arr) or arr.ndim!=1
        or len(arr)!=12*lookup.nside_in**2):
        raise PlanckFFPPolarError("native full-sky real HEALPix RING column required")
    # np.take materializes at most Nselected*Nchild dtype memory. File data
    # views are strided packed FITS float32; no full unmasked map copy needed.
    value=np.take(arr,lookup.fine_ring_idx)
    if not np.isfinite(value).all():
        raise PlanckFFPPolarError("source simulation has NaN or infinity")
    if np.any(value < -1e20):
        raise PlanckFFPPolarError("unexpected unseen source simulation pixel")
    if use_source_mask:
        value=np.where(lookup.fine_mask,value,0.)
        norm=lookup.valid_counts
    else:
        norm=lookup.nested_children
    return np.asarray(value.sum(axis=1,dtype=np.float64)/norm,float)


def ffp_source_header(path,nside=2048):
    from astropy.io import fits
    path=Path(path)
    if not path.is_file():
        raise PlanckFFPPolarError("FFP10 missing source file")
    with fits.open(path,memmap=True) as ff:
        h=ff[1]
        keys=["PIXTYPE","ORDERING","NSIDE","COORDSYS","POLCCONV",
              "INDXSCHM","NAXIS1","NAXIS2"]
        meta={k:h.header.get(k) for k in keys}
        col=h.columns.names
        unit=[h.header.get("TUNIT"+str(i)) for i in (1,2,3)]
        if (meta["PIXTYPE"]!="HEALPIX"
            or meta["ORDERING"]!="RING" or meta["NSIDE"]!=nside
            or meta["COORDSYS"] is not None or meta["POLCCONV"] is not None
            or meta["INDXSCHM"]!="IMPLICIT"
            or col!=["INTENSITY","Q-POLARISATION","U-POLARISATION"]
            or unit!=["K_CMB"]*3
            or len(h.data)*1024 != 12*nside*nside):
            raise PlanckFFPPolarError("unexpected FFP10 HEALPix source frame/header")
    return {"path":str(path),"size_bytes":path.stat().st_size,
            "header":meta,"columns":col,"units":unit,
            "frame_status":"COORDSYS_AND_POLCCONV_UNSPECIFIED"}


def load_ffp10_pol_projected(path,lookup:ParentLookup,operator,
                            *,u_sign=1,check_header=True,
                            include_intensity=False):
    """Return nmode real E/B coefficients, projected within same source support.

    U-sign chart selection is an explicit hypothesis (U+ or U-).
    Does not attach any observed-sky p-value.
    """
    from astropy.io import fits
    if u_sign not in (-1,1):
        raise PlanckFFPPolarError("formal U sign chart must be +1/-1")
    op=np.asarray(operator)
    n=lookup.n_selected
    if (op.ndim!=2 or op.shape[1]!=2*n or
        not np.isfinite(op).all()):
        raise PlanckFFPPolarError("Q/U source projector mismatches selected-pixel geometry")
    if check_header:meta=ffp_source_header(path,lookup.nside_in)
    else:meta={"path":str(path)}
    with fits.open(path,memmap=True) as ff:
        table=ff[1].data
        q=coarse_selected_mean_rings(
            table["Q-POLARISATION"].reshape(-1),lookup)
        u=coarse_selected_mean_rings(
            table["U-POLARISATION"].reshape(-1),lookup)*u_sign
        intensity=None
        if include_intensity:
            intensity=coarse_selected_mean_rings(
                table["INTENSITY"].reshape(-1),lookup)
    coeff=op@np.r_[q,u]*1e6
    return {"coefficients_microK":coeff,"source":meta,
            "u_sign_chart":int(u_sign),
            "selected_Q_U_microK_rms":float(
                np.sqrt(np.mean(np.r_[q,u]**2))*1e6),
            "selected_intensity_K":intensity}


def split_source_contrasts(coeffs,names):
    """Paired same-physical-sky low-ell HM/OE contrasts, no covariance claim."""
    x=np.asarray(coeffs)
    names=list(names)
    if (x.ndim!=2 or np.iscomplexobj(x) or not np.isfinite(x).all()
        or len(names)!=len(x) or len(names)!=len(set(names))):
        raise PlanckFFPPolarError("source same-sky real E/B coefficient table")
    lookup={name:x[i] for i,name in enumerate(names)}
    pairs=("SMICA_HM1","SMICA_HM2","SMICA_OE1","SMICA_OE2")
    if any(z not in lookup for z in pairs):
        raise PlanckFFPPolarError("at least HM/OE source split mapping required")
    h1,h2,o1,o2=(lookup[z] for z in pairs)
    return {
        "HM_half_difference":(h1-h2)/2,
        "OE_half_difference":(o1-o2)/2,
        "HM_half_sum":(h1+h2)/2,
        "OE_half_sum":(o1+o2)/2,
        "HM_minus_OE_coadd":(h1+h2-o1-o2)/2,
    }


def projected_covariance_and_rank(samples):
    """Sample covariance WITHOUT pretending rank >= N-1 or physical null fit."""
    z=np.asarray(samples,float)
    if z.ndim!=2 or z.shape[0]<2 or not np.isfinite(z).all():
        raise PlanckFFPPolarError("at least 2 finite unique cohort source rows")
    centred=z-z.mean(axis=0)
    C=centred.T@centred/(len(z)-1)
    sig=np.linalg.svd(centred,compute_uv=False)
    tol=max(z.shape)*np.finfo(float).eps*sig[0] if sig[0] else 0.
    return {"sample_covariance":C,
            "empirical_rank":int(np.count_nonzero(sig>tol)),
            "max_empirical_rank":min(z.shape[0]-1,z.shape[1]),
            "number_distinct_input_rows":int(len(z)),
            "statistical_independence":"MUST_BE_CERTIFIED_BY_SOURCE_BANK_NOT_BY_THIS_MATRIX",
            "one_sky_variants_are_not_MC_samples":True}


def split_covariance_transport(C11,C22,C12):
    """Exact same-sky split-noise coadd / halfdifference covariance.

    n1,n2 have joint covariance [[C11,C12],[C12.T,C22]].
    Coadd noise = (n1+n2)/2, split noise = (n1-n2)/2.
    The coadd-minus-split covariance is the symmetric cross-covariance,
    not automatically zero for HM/OE. This does NOT estimate actual Planck C12.
    """
    A=np.asarray(C11)
    B=np.asarray(C22)
    D=np.asarray(C12)
    if (A.ndim!=2 or A.shape[0]!=A.shape[1]
        or any(v.shape!=A.shape for v in (B,D))
        or any(np.iscomplexobj(v) or not np.isfinite(v).all() for v in (A,B,D))
        or not np.allclose(A,A.T,rtol=1e-12,atol=1e-13)
        or not np.allclose(B,B.T,rtol=1e-12,atol=1e-13)):
        raise PlanckFFPPolarError("real symmetric autos and arbitrary cross covariance required")
    joint=np.block([[A,D],[D.T,B]])
    eig=np.linalg.eigvalsh(joint)
    if eig[0]<-1e-11*max(np.max(abs(eig)),1e-30):
        raise PlanckFFPPolarError("full two-split noise covariance not PSD")
    sym_cross=D+D.T
    C_coadd=(A+B+sym_cross)/4
    C_halfdiff=(A+B-sym_cross)/4
    return {
      "coadd_noise_covariance":(C_coadd+C_coadd.T)/2,
      "half_difference_covariance":(C_halfdiff+C_halfdiff.T)/2,
      "coadd_minus_halfdiff_covariance":sym_cross/2,
      "measurement_status":"MATHEMATICAL_CONDITIONAL_ONLY_NO_REAL_C12_ESTIMATE"
    }
