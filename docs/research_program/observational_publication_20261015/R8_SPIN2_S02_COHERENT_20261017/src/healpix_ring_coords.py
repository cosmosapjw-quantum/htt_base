"""Pure NumPy HEALPix RING pixel centers for bounded finite spin-2 audits.

This is a reference independent of healpy for input maps ALREADY known to be
RING. It NEVER reorders a native NSIDE2048 NESTED FITS array. For native FITS
perform healpy.read_map(...,nest=False), record the source hash, then ud_grade
RING->RING before this adapter. Author's HEALPix equal-area pixel centers.
"""
import numpy as np


def pix2ang_ring(nside, ipix=None):
    if not isinstance(nside, (int,np.integer)) or nside<1 or nside&(nside-1):
        raise ValueError('nside must be a power of two')
    npix=12*nside*nside
    p=np.arange(npix,dtype=np.int64) if ipix is None else np.asarray(ipix,dtype=np.int64)
    if p.ndim!=1 or len(p)==0 or np.any((p<0)|(p>=npix)):
        raise ValueError('HEALPix RING index outside source range')
    ncap=2*nside*(nside-1)
    z=np.empty(len(p),dtype=np.float64)
    phi=np.empty(len(p),dtype=np.float64)
    north=p<ncap
    south=p>=npix-ncap
    equ=~(north|south)
    if north.any():
        ip=p[north]+1
        ir=np.floor(.5*(1+np.sqrt(2.0*ip-1))).astype(np.int64)
        ph=ip-2*ir*(ir-1)
        z[north]=1.-ir**2/(3.*nside*nside)
        phi[north]=(ph-.5)*np.pi/(2.*ir)
    if south.any():
        ip=npix-p[south]
        ir=np.floor(.5*(1+np.sqrt(2.0*ip-1))).astype(np.int64)
        ph=4*ir+1-(ip-2*ir*(ir-1))
        z[south]=-1.+ir**2/(3.*nside*nside)
        phi[south]=(ph-.5)*np.pi/(2.*ir)
    if equ.any():
        ip=p[equ]-ncap
        ir=ip//(4*nside)+nside
        ph=ip%(4*nside)+1
        fodd=.5*(1.+((ir+nside)&1))
        z[equ]=(2*nside-ir)*(2./(3*nside))
        phi[equ]=(ph-fodd)*np.pi/(2.*nside)
    return np.arccos(np.clip(z,-1,1)), np.mod(phi,2*np.pi)


def healpy_crosscheck(nside,ipix):
    """Optional external independent convention check, requires explicit healpy."""
    import healpy as hp
    th,ph=pix2ang_ring(nside,ipix)
    a,b=hp.pix2ang(nside,ipix,nest=False)
    return float(max(np.max(abs(th-a)),np.max(abs(np.angle(np.exp(1j*(ph-b)))))))
