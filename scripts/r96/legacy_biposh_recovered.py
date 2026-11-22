"""Maintained repair of legacy/bianchi_departure_v091/.../biposh_masked.py.

The legacy estimator accumulated |a_lm|² in 'A20' with fsky variance;
this is neither a centered L=2 BipoSH nor a mask-corrected likelihood.
This version preserves the intended public API names and accepts an
explicit source-matched Monte Carlo ensemble for bias and covariance.
NEVER silently applies 1/fsky correction or invents null Monte Carlo.

The immutable legacy snapshot remains untracked and untouched. This module
is its tracked, versioned, derived replacement, source-locked in R96.

L=2 quadrupolar Gaunt off-diagonal pairs ell -> ell+2 only, M=0,1,2,
five real coefficients. Mask bias correction is empirical from matched MC.
Full Wigner-9j anisotropic mask coupling / physical Bianchi likelihood not
provided; use 'masked source-conditioned statistical diagnostic' language.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,math
import numpy as np
import healpy as hp
from scripts.r94.gaunt_fast import build_terms,project,loo_diagonal_fast

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/"legacy/bianchi_departure_v091_github/htt/likelihood/biposh_masked.py"
__all__=["BiPoSHLikelihood","estimate_biposh_L2","biposh_variance",
         "estimate_biposh_from_alm","masked_alm","conditioned_full_covariance"]

def provenance():
 return {"legacy_source_path":str(ORIGINAL),
         "legacy_source_sha256":hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
         "original_retained_untouched":True,
         "new_source":"scripts/r96/legacy_biposh_recovered.py"}

def masked_alm(m,mask,lmax:int):
 m=np.asarray(m,dtype=np.float64)
 mask=np.asarray(mask,dtype=np.float64)
 if m.shape!=mask.shape or m.ndim!=1 or not np.all(np.isfinite(m)):
  raise ValueError("map or mask incompatible/nonfinite")
 nside=hp.npix2nside(len(m))
 if lmax<4 or lmax>3*nside-1:
  raise ValueError("lmax outside HEALPix bandwidth")
 if not np.all(np.isfinite(mask)) or mask.min()<0 or mask.max()>1:
  raise ValueError("mask outside [0,1]")
 xyz=np.stack(hp.pix2vec(nside,np.arange(len(m))),axis=1)
 X=np.column_stack([np.ones(len(m)),xyz])
 W=(X.T*mask)
 beta=np.linalg.solve(W@X,W@m)
 return hp.map2alm((m-X@beta)*mask,lmax=lmax,iter=0)

def conditioned_full_covariance(mc_values, shrinkage:float=0.20):
 mc=np.asarray(mc_values,float)
 if mc.ndim!=2 or mc.shape[0]<mc.shape[1]+5:
  raise ValueError("need matched MC ensemble (N >= d+5)")
 if not np.isfinite(mc).all() or not (0<=shrinkage<=1):
  raise ValueError("bad MC or shrinkage")
 cov=np.cov(mc,rowvar=False,ddof=1)
 scale=np.trace(cov)/mc.shape[1]
 return (1-shrinkage)*cov+shrinkage*scale*np.eye(mc.shape[1])

def estimate_biposh_from_alm(obs_alm,mc_alms,cl_iso,ell_range,
                              *,lmax,shrinkage=0.20,backend="numpy"):
 if mc_alms is None:raise ValueError("source-matched MC required; no f_sky-only variance allowed")
 mc=np.asarray(mc_alms,dtype=np.complex128)
 obs=np.asarray(obs_alm,dtype=np.complex128)
 if mc.ndim!=2 or len(obs)!=mc.shape[1] or len(mc)<25:raise ValueError("bad alms")
 low,hi=ell_range
 if low<2 or hi+2>lmax:raise ValueError("ell range invalid")
 cl=np.asarray(cl_iso,float)
 if len(cl)<lmax+1 or not np.all(cl[low:hi+3]>0):raise ValueError("C_ell invalid")
 terms=build_terms(cl,lmax,bands=(ell_range,),ms=(0,1,2))
 y_obs=project(obs,terms,backend=backend).reshape(5)
 y_mc=project(mc,terms,backend=backend).reshape(len(mc),5)
 bias=y_mc.mean(axis=0)
 centered=y_obs-bias
 cov=conditioned_full_covariance(y_mc,shrinkage=shrinkage)
 rank=loo_diagonal_fast(y_mc,y_obs) # explicit diagonal-Loo reference, not covariance Loo
 return {"obs_raw":y_obs,"obs_bias_corrected":centered,
         "mc_raw":y_mc,"mc_bias":bias,"covariance":cov,
         "estimated_variance":np.diag(cov),"rank_diagonal_LOO":rank["rank_p"],
         "statistic":"mask and noise Monte Carlo calibrated L=2 ell->ell+2 Gaunt diagnostic",
         "beam_transfer_or_gaussian_likelihood_source_qualified":False}

def estimate_biposh_L2(sky_map,mask,cl_iso,lmax=30,nside=None,
                        *,mc_sky_maps=None,shrinkage=0.20,backend="numpy"):
 """Compat repaired legacy function: returns 5 centered values and full 5x5 covariance.

 New required mc_sky_maps keyword. Using old four args without MC raises
 rather than fabricating publication-quality significance from 1/fsky.
 """
 if mc_sky_maps is None:
  raise ValueError("legacy fsky-only L=2 variance is invalid; pass source-matched mc_sky_maps")
 if nside is None:nside=hp.npix2nside(len(sky_map))
 if hp.nside2npix(nside)!=len(sky_map):raise ValueError("nside mismatch")
 obs=masked_alm(sky_map,mask,lmax)
 mc=[masked_alm(x,mask,lmax) for x in np.asarray(mc_sky_maps)]
 rec=estimate_biposh_from_alm(obs,mc,cl_iso,(2,lmax-2),
   lmax=lmax,shrinkage=shrinkage,backend=backend)
 return rec["obs_bias_corrected"],rec["covariance"]

def biposh_variance(cl_iso,f_sky,ell_min=2,ell_max=30,*,mc_biposh=None):
 """No generic 1/fsky shortcut. Returns MC covariance if source-qualified."""
 if mc_biposh is None:
  raise ValueError("masked BipoSH covariance requires matched MC, not just f_sky")
 return conditioned_full_covariance(mc_biposh,shrinkage=0.20)

class BiPoSHLikelihood:
 def __init__(self,biposh_obs,biposh_var,mask,ell_range=(2,30)):
  self.biposh_obs=np.asarray(biposh_obs,float)
  self.covariance=np.asarray(biposh_var,float)
  if self.biposh_obs.shape!=(5,) or self.covariance.shape!=(5,5):
   raise ValueError("five signed L=2 components and source-matched 5x5 covariance required")
  self.mask=np.asarray(mask,float)
  self.ell_range=ell_range
  # Source-matched MC covariance must already include mask bias.
  if np.linalg.eigvalsh(self.covariance).min()<=0:raise ValueError("covariance not SPD")
  self.chol=np.linalg.cholesky(self.covariance)
 def log_likelihood(self,biposh_model):
  model=np.asarray(biposh_model,float)
  if model.shape!=(5,):raise ValueError("shape mismatch")
  r=np.linalg.solve(self.chol,self.biposh_obs-model)
  return float(-0.5*r@r)
