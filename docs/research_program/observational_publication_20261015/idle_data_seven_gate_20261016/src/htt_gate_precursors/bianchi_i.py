"""Collisionless exact Bianchi-I kinematic null-geodesic transport baseline.

Metric: ds^2 = -c^2dt^2 + sum a_i(t)^2 (dx^i)^2,
with a_i(t)=exp(H_i t) over a bounded interval, a_i(0)=1,
and H_i measured in inverse observer proper time. No Einstein closure.
"""
import numpy as np
from scipy.special import logsumexp


def log_frequency_ratio(H_i,lookback_time,direction):
    """log(E_em/E_obs)=1/2 log(sum n_i^2 exp(2 H_i tau))."""
    h=np.asarray(H_i,dtype=float);n=np.asarray(direction,dtype=float)
    if h.shape!=(3,) or not np.all(np.isfinite(h)) or not np.isfinite(lookback_time) or lookback_time<0:
        raise ValueError('invalid expansion or lookback')
    if n.shape[-1]!=3 or not np.all(np.isfinite(n)):
        raise ValueError('direction has shape (...,3)')
    norm2=np.sum(n*n,axis=-1)
    if np.any(np.abs(norm2-1)>1e-10):
        raise ValueError('unit direction required')
    return 0.5*logsumexp(2*lookback_time*h,b=n*n,axis=-1)


def log_redshift_taylor2(H_i,lookback_time,direction):
    """tau*<H>_w+tau^2*(<H^2>_w-<H>_w^2)+O(tau^3)."""
    h=np.asarray(H_i,dtype=float);n=np.asarray(direction,dtype=float)
    w=n*n
    mean=w@h;var=w@(h*h)-mean*mean
    return lookback_time*mean+lookback_time*lookback_time*var


def collisionless_temperature(T_em,H_i,lookback_time,direction):
    """Isotropic Planck f_em -> T_obs=T_em/(1+z), no new Q/U/V.

    Not a complete polarized Boltzmann solver or recombination calculation.
    """
    if T_em<=0 or not np.isfinite(T_em):
        raise ValueError('positive emitter temperature')
    return T_em*np.exp(-log_frequency_ratio(H_i,lookback_time,direction))


def stf_linear_temperature_anisotropy(sigma_i,lookback_time,direction):
    """Delta ln T = -tau sum sigma_i n_i^2 + O(tau^2 sigma^2).

    Requires sum sigma_i=0 and simultaneous isotropic emitter surface.
    """
    s=np.asarray(sigma_i,dtype=float)
    if s.shape!=(3,) or not np.all(np.isfinite(s)) or abs(np.sum(s))>1e-12:
        raise ValueError('traceless diagonal shear required')
    n=np.asarray(direction,dtype=float)
    if n.shape[-1]!=3 or np.any(abs(np.sum(n*n,axis=-1)-1)>1e-10):
        raise ValueError('unit direction')
    return -lookback_time*(n*n)@s
