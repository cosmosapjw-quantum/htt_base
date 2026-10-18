"""Joint Planck half-mission split law with correlation-safe covariance.

Exact identities apply to ANY correlated Gaussian model of observed split
retained vectors. One observed split pair does not estimate this covariance;
HM-difference alone is blind to perfectly shared systematics.
"""
from __future__ import annotations

import numpy as np


class PlanckSplitLawError(ValueError):
    pass


def half_sum_difference(first,second):
    if np.iscomplexobj(first) or np.iscomplexobj(second):
        raise PlanckSplitLawError('real thermodynamic sky coefficient fields required')
    a=np.asarray(first,float);b=np.asarray(second,float)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise PlanckSplitLawError('equal finite split vectors required')
    return (a+b)*.5,(a-b)*.5


def split_covariance(c11,c22,c12):
    """Exact covariance of m=(y1+y2)/2 and d=(y1-y2)/2.

    Each C_ij is for the SAME observable coordinate/supported mask, and
    C21=C12.T. Neither split noises nor foreground components are assumed
    independent. The original 2D block covariance must be positive definite.
    """
    if any(np.iscomplexobj(x) for x in (c11,c22,c12)):
        raise PlanckSplitLawError('real covariance blocks needed')
    a,b,c=map(lambda x:np.asarray(x,dtype=float),(c11,c22,c12))
    if (a.ndim!=2 or a.shape[0]!=a.shape[1] or b.shape!=a.shape or c.shape!=a.shape
        or not np.isfinite(a).all() or not np.isfinite(b).all() or not np.isfinite(c).all()
        or not np.allclose(a,a.T,atol=1e-11,rtol=1e-10)
        or not np.allclose(b,b.T,atol=1e-11,rtol=1e-10)):
        raise PlanckSplitLawError('valid symmetric same-dimensional covariance blocks required')
    full=np.block([[a,c],[c.T,b]])
    eig=np.linalg.eigvalsh(full)
    if eig[0]<=0:
        raise PlanckSplitLawError('invalid joint split PSD/positive support')
    mm=(a+b+c+c.T)*.25
    dd=(a+b-c-c.T)*.25
    md=(a-b-c+c.T)*.25
    return (mm+mm.T)*.5,(dd+dd.T)*.5,md


def conditional_split_covariance(c11,c22,c12):
    """Schur covariance of half sum conditional on half difference, Gaussian."""
    cm,cd,cross=split_covariance(c11,c22,c12)
    if np.linalg.eigvalsh(cd)[0]<=0:
        raise PlanckSplitLawError('difference covariance singular')
    cond=cm-cross@np.linalg.solve(cd,cross.T)
    if np.linalg.eigvalsh((cond+cond.T)*.5)[0]<=0:
        raise PlanckSplitLawError('conditional covariance nonpositive')
    return (cond+cond.T)*.5


def nested_coarse_masked_mean(values,valid,nside_in=2048,nside_out=64,chunk_lowpix=1024):
    """Native NESTED HEALPix map -> RING coarse weighted valid-pixel average.

    This read-only reduction uses contiguous NESTED child groups, never
    substitutes missing pixels with zero, and separately returns retained
    fine-pixel coverage fraction. Neither this nor ud_grade propagates
    anisotropic beams/noise covariance.
    """
    import healpy as hp
    if np.iscomplexobj(values) or np.iscomplexobj(valid):
        raise PlanckSplitLawError('real HEALPix array required')
    v=np.asarray(values)
    flag=np.asarray(valid,dtype=bool)
    if (v.ndim!=1 or not np.issubdtype(v.dtype,np.number) or
        not hp.isnsideok(nside_in) or not hp.isnsideok(nside_out) or
        nside_out>nside_in or nside_in%nside_out or
        v.shape!=(hp.nside2npix(nside_in),) or flag.shape!=v.shape or
        chunk_lowpix<1):
        raise PlanckSplitLawError('NESTED fine map, matching mask and valid resolution needed')
    children=(nside_in//nside_out)**2
    nout=hp.nside2npix(nside_out)
    values_nest=np.empty(nout,float)
    coverage_nest=np.empty(nout,float)
    for start in range(0,nout,int(chunk_lowpix)):
        stop=min(nout,start+int(chunk_lowpix))
        block=np.asarray(v[start*children:stop*children],dtype=float).reshape(stop-start,children)
        mask=flag[start*children:stop*children].reshape(stop-start,children)
        # Reject invalid sentinel exactly as a missing pixel; no extrapolation.
        mask=mask&np.isfinite(block)&(block>-1e20)
        cnt=mask.sum(axis=1)
        coverage_nest[start:stop]=cnt/children
        num=np.sum(np.where(mask,block,0.),axis=1,dtype=float)
        values_nest[start:stop]=np.divide(num,cnt,out=np.full(stop-start,np.nan),where=cnt>0)
    return hp.reorder(values_nest,n2r=True),hp.reorder(coverage_nest,n2r=True)
