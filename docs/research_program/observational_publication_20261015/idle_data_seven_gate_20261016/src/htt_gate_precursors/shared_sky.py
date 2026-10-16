"""L03 conditional matched-null units: independent skies, not map-products."""
from __future__ import annotations
import numpy as np


def simulate_same_sky(n_sky:int,n_method:int,noise_sigma:float,seed:int=2026):
    if n_sky<2 or n_method<1 or noise_sigma<0:
        raise ValueError('invalid simulation shape')
    rng=np.random.default_rng(seed)
    latent=rng.normal(size=(n_sky,1))
    product=latent+rng.normal(size=(n_sky,n_method),scale=noise_sigma)
    return product


def matched_scan(scores:np.ndarray,source_ids:tuple[str,...]|None=None):
    """Register one max-|score| per latent independent sky; same scan for all."""
    scores=np.asarray(scores,dtype=float)
    if scores.ndim!=2 or scores.shape[1]<1 or scores.shape[0]<2 or not np.all(np.isfinite(scores)):
        raise ValueError('one row per independent sky, columns = processing products')
    if source_ids is not None and (len(source_ids)!=len(scores) or len(set(source_ids))!=len(scores)):
        raise ValueError('latent sky ids must be unique')
    return np.max(np.abs(scores),axis=1)


def heldout_rank_p_values(statistic:np.ndarray):
    """Treat each sky once as observed, other N-1 as null.

    Under continuous iid exchangeability the exact ranks enumerate 1/N,...,1.
    """
    statistic=np.asarray(statistic,dtype=float)
    if statistic.ndim!=1 or len(statistic)<2 or not np.all(np.isfinite(statistic)):
        raise ValueError('bad statistic vector')
    N=len(statistic)
    return np.array([np.count_nonzero(statistic >= v)/N for v in statistic],dtype=float)


def observed_p(observed:np.ndarray,null_by_sky:np.ndarray):
    observed=np.asarray(observed,dtype=float)
    null_by_sky=np.asarray(null_by_sky,dtype=float)
    if observed.ndim!=1 or null_by_sky.ndim!=2 or len(observed)!=null_by_sky.shape[1]:
        raise ValueError('same statistic channels for observed and null')
    if not np.all(np.isfinite(observed)) or not np.all(np.isfinite(null_by_sky)):
        raise ValueError('nonfinite score')
    stat_obs=np.max(np.abs(observed))
    stats=np.max(np.abs(null_by_sky),axis=1)
    return float((1+np.count_nonzero(stats>=stat_obs))/(len(stats)+1))
