"""Source-bound same-sky CMB split contrasts and finite spin-2 harmonic images.

All products are processed once with exactly the SAME common selected
temperature/polarization mask and ORTHONORMAL real harmonic conventions.
No split realization is treated as an independent cosmological sky,
nor does a raw residual give a calibrated covariance or Planck PTE.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve


class SourceMultiSplitError(ValueError):
    pass


def finite_real_input(value, *, name, shape=None):
    if np.iscomplexobj(value):
        raise SourceMultiSplitError(f'{name}: real harmonic source required')
    x=np.asarray(value,dtype=float)
    if (not np.isfinite(x).all() or (shape is not None and x.shape!=shape)):
        raise SourceMultiSplitError(f'{name}: finite shape/input contract violated')
    return x


def multisplit_contrasts(four_splits):
    """HM1, HM2, OE1, OE2 of SAME sky / SAME mask / SAME harmonic fit.

    The full-rank transform isolates a shared fourway mean and three
    common-offset-annihilating contrasts, in the coefficient basis.
    No probability law or noise independence follows from this identity.
    """
    x=finite_real_input(four_splits,name='four split harmonic arrays')
    if x.ndim!=2 or x.shape[0]!=4 or x.shape[1]<1:
        raise SourceMultiSplitError('four correlated same-sky coefficient rows required')
    hm=(x[0]+x[1])*.5
    oe=(x[2]+x[3])*.5
    return dict(
        fourway_mean=(hm+oe)*.5,
        hm_mean=hm,
        oe_mean=oe,
        hm_difference=(x[0]-x[1])*.5,
        oe_difference=(x[2]-x[3])*.5,
        partition_mean_difference=hm-oe,
    )


def split_power_identity(a,b):
    """Same-basis dot/ell-band power; cross = mean_auto - diff_auto."""
    a=finite_real_input(a,name='first split')
    b=finite_real_input(b,name='second split',shape=a.shape)
    if a.ndim!=1 or len(a)<1:
        raise SourceMultiSplitError('one band real coefficient vectors required')
    m=(a+b)*.5
    d=(a-b)*.5
    l=len(a)
    return {
        'first_auto':float(a@a/l),
        'second_auto':float(b@b/l),
        'cross':float(a@b/l),
        'mean_auto':float(m@m/l),
        'difference_auto':float(d@d/l),
        'cross_identity_residual':float((m@m-d@d-a@b)/l)
    }


def spin2_design_real(*,nside=64,lmax=5):
    """Pixel-real design of Q/U for physical spin-2 E and B coefficients.

    Reuse the same real harmonic layout as intensity:
       (ell,m0); m>0 (sqrt(2) Re, sqrt(2) Im).
    The corresponding physical complex a_ellm is
       a(m>0)=(a_cos-i*a_sin)/sqrt(2).
    Healpy's alm2map_spin defines the Stokes convention; both real
    channels use precisely that one convention. No mask or physics transfer
    is applied yet: design is an intrinsic spin-harmonic pixel operator.
    """
    import healpy as hp
    if not isinstance(nside,int) or not hp.isnsideok(nside) or nside<8:
        raise SourceMultiSplitError('healpix nside>=8 expected')
    if not isinstance(lmax,int) or lmax<2 or lmax>3*nside-1:
        raise SourceMultiSplitError('spin2 lmax in [2,3*nside-1]')
    n=hp.nside2npix(nside)
    nalm=hp.Alm.getsize(lmax)
    columns=[]
    meta=[]
    for ell in range(2,lmax+1):
        modes=[(0,'m0')]
        for m in range(1,ell+1):
            modes.extend(((m,'cos'),(m,'sin')))
        for spin in ('E','B'):
            for m,phase in modes:
                E=np.zeros(nalm,complex)
                B=np.zeros(nalm,complex)
                dest=E if spin=='E' else B
                dest[hp.Alm.getidx(lmax,ell,m)]=(1. if m==0 else
                  (1./np.sqrt(2.) if phase=='cos' else -1j/np.sqrt(2.)))
                q,u=hp.alm2map_spin([E,B],nside=nside,spin=2,lmax=lmax)
                columns.append(np.r_[q,u])
                meta.append({'ell':ell,'m':m,'phase':phase,'E_or_B':spin})
    X=np.column_stack(columns)
    return X,meta


def fit_spin2_coefficients(stokes_QU,selected_mask,design,*,max_condition=1e12):
    """One same-mask joint finite-pixel fit for E/B, not naive separate Q/U Ylm.

    Implicitly assumes the coordinates/basis frames of stokes and the design
    are identical (native Galactic HEALPix frame). A cut sky causes E/B
    mixing in naive pseudo-alms; joint LS removes this mixing WITHIN the
    FINITE DECLARED ell2..lmax response span, not unmodelled higher ell.
    """
    v=finite_real_input(stokes_QU,name='Q/U',shape=None)
    X=finite_real_input(design,name='spin2 design',shape=None)
    m=np.asarray(selected_mask,dtype=bool)
    if (v.ndim!=2 or v.shape[0]!=2 or
        m.shape!=(v.shape[1],) or X.shape[0]!=2*len(m)
        or X.ndim!=2 or X.shape[1]<1):
        raise SourceMultiSplitError('paired Q/U, matching common spin design/mask required')
    good=np.r_[m,m]
    XX=X[good]
    yy=v.reshape(-1)[good]
    if not np.isfinite(yy).all() or len(yy)<X.shape[1]:
        raise SourceMultiSplitError('invalid source QU on selected pixels')
    gram=XX.T@XX
    evals=np.linalg.eigvalsh(gram)
    if evals[0]<=0 or evals[-1]/evals[0]>max_condition:
        raise SourceMultiSplitError('spin-2 joint finite pixel design not identifiable')
    chol=cho_factor(gram,lower=True,check_finite=False)
    op=cho_solve(chol,XX.T,check_finite=False)
    arr=op@yy
    identity=float(np.max(np.abs(op@XX-np.eye(X.shape[1]))))
    if identity>1e-9:
        raise SourceMultiSplitError('joint spin projector not an identity on its design')
    return {'coefficients':arr,'rank':len(arr),
            'design_condition':float(np.sqrt(evals[-1]/evals[0])),
            'design_identity_residual':identity,
            'residual_rms_microK':float(np.linalg.norm(yy-XX@arr)/np.sqrt(len(yy))),
            'selected_n_pixels':int(m.sum())}
