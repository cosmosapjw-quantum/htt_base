"""Same-frame SO(3) tensor orientation diagnostics for observational *proxies*.

The CF4 apparent Hubble quadrupole is in ICRS J2000; the Planck STF Q
is in Galactic coordinates. A numerical angular relation does not
identify a common physical Bianchi shear; no cosmological null follows.
"""
from __future__ import annotations
import functools
import numpy as np


@functools.lru_cache(maxsize=1)
def icrs_to_galactic_rotation():
    """Astropy/IAU ICRS -> Galactic active orthogonal transform on XYZ."""
    from astropy.coordinates import SkyCoord
    cardinal=np.eye(3)
    sky=SkyCoord(x=cardinal[:,0],y=cardinal[:,1],z=cardinal[:,2],
                 representation_type='cartesian',frame='icrs')
    R=np.asarray(sky.galactic.cartesian.xyz.value,dtype=float)
    if np.max(abs(R.T@R-np.eye(3)))>1e-12 or abs(np.linalg.det(R)-1)>1e-12:
        raise ValueError('ICRS to Galactic sky rotation not orthogonal')
    R.setflags(write=False)
    return R


def _check(tensor):
    if np.iscomplexobj(tensor):raise ValueError('real tensor required')
    t=np.asarray(tensor,float)
    if (t.shape!=(3,3) or not np.isfinite(t).all() or
        np.linalg.norm(t)<=0 or np.max(abs(t-t.T))>1e-11*np.linalg.norm(t) or
        abs(np.trace(t))>1e-11*np.linalg.norm(t)):
        raise ValueError('real finite nonzero STF2 with correct frame needed')
    return t


def stf_tensor_cosine(a,b):
    A=_check(a);B=_check(b)
    return float(np.sum(A*B)/(np.linalg.norm(A)*np.linalg.norm(B)))


def stf_principal_axis_separation(a,b):
    A=_check(a);B=_check(b)
    v=np.linalg.eigh(A)[1][:,-1]
    u=np.linalg.eigh(B)[1][:,-1]
    return float(np.rad2deg(np.arccos(np.clip(abs(u@v),0,1))))
