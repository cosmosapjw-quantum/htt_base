"""R93 full 999 SMICA FFP10 CMB + reused 300 noise: a_lm and masked L=2 BipoSH.

Authoritative existing K1 PR150 compact NSIDE64 replay maps are reused for
all 999 CMB realization IDs (0..999 except 970); exactly 300 noise IDs
paired by ID % 300, matching frozen K1 contract. No 1 TB raw copied.
The cache already passed original exact raw-to-cache readback. This analysis
uses the NSIDE64 downsampled T-only maps; does NOT constitute a true
full-resolution Planck high-l E/B likelihood or independent 999-noise null.
No original R78 node acceptance is changed.

All statistics and bands are fixed *before* seeing the new result:
  L=2 Gaunt cross l->l+2, l=2..8,9..16,17..32,33..46, lmax=48
  300 unique-noise-paired MCs primary, all 999 modulo-reused secondary.
  Full observed/MC same weighted common PR3 SMICA mask, weighted mono/dipole fit.
  Empirical MC rank using leave-one-out 20D diagonal-standardized scores.
  Gaussian source C_l from published Planck TT best-fit, fixed positive weights.
Report values as conditional exploratory, not evidence for Bianchi family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path

import healpy as hp
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from sympy.physics.wigner import wigner_3j

ROOT=Path(__file__).resolve().parents[2]
CACHE=Path("/mnt/extdrive/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
PR150=ROOT/"docs/generated/pr150_e2e_input_manifest.json"
GATE=ROOT/"docs/generated/k1_e2e_cache_gate_ffp10_smica.json"
THEORY=Path("/mnt/extdrive/workdir/raw/planck_data/COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt")
OUT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121"
PRIVATE=Path.home()/"Downloads/htt_r93_ffp999_alm_biposh"
BANDS=((2,8),(9,16),(17,32),(33,46))
LMAX=48
NSIDE=64
L=2
M_LIST=(0,1,2)

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):
   h.update(b)
 return h.hexdigest()

def read_inputs():
 if not CACHE.is_file() or not PR150.is_file() or not GATE.is_file():
  raise RuntimeError("K1 reused exact reduction not present")
 src=json.loads(PR150.read_text())
 gate=json.loads(GATE.read_text())
 if not (src["usable_cmb_count"]==999 and src["noise_mc_count"]==300
         and src["excluded_ids"]==["00970"]
         and gate["cache_reproducibility_green"]
         and gate["raw_hash_ok"] and gate["full_map_replay"] is True):
  raise RuntimeError("K1 source and exact cache reproduction gate not recognized")
 digest=sha(CACHE)
 if digest!="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb":
  raise RuntimeError(f"cache SHA mismatch: {digest}")
 with np.load(CACHE,allow_pickle=False) as c:
  cmb_ids=np.asarray(c["cmb_ids"],int)
  noise_ids=np.asarray(c["noise_ids"],int)
  if not (len(cmb_ids)==999 and set(cmb_ids)==set(range(1000))-{970} and
          np.array_equal(noise_ids,np.arange(300))):
   raise RuntimeError("K1 ID set drift")
  cmb=np.asarray(c["cmb_maps"],float)
  noi=np.asarray(c["noise_maps"],float)
  obs=np.asarray(c["observed_map"],float)
  mask=np.asarray(c["common_mask"],float)
  stored_low=np.asarray(c["cmb_alm"],complex)
 if (cmb.shape!=(999,hp.nside2npix(NSIDE)) or noi.shape!=(300,cmb.shape[1]) or
         obs.shape!=(cmb.shape[1],) or mask.shape!=(cmb.shape[1],)):
  raise RuntimeError("K1 NSIDE64 source data shape drift")
 low_calc=hp.map2alm(cmb[0],lmax=8,iter=0)
 low_err=float(np.max(abs(low_calc-stored_low[0])))
 if low_err>2e-6:raise RuntimeError("K1 stored alm not consistent with source maps")
 if not np.all((mask>=0)&(mask<=1)):raise RuntimeError("invalid common mask")
 return cmb_ids,cmb,noi,obs,mask,digest,low_err

def iso_theory_cl():
 a=np.loadtxt(THEORY)
 if a.shape[0]!=2507 or a[0,0]!=2:
  raise RuntimeError("published Planck TT theory shape drift")
 C=np.zeros(LMAX+1,float)
 ell=np.arange(2,LMAX+1)
 C[2:]=a[:LMAX-1,1]*(2*math.pi)/(ell*(ell+1))
 if not np.all(np.isfinite(C[2:])) or not np.all(C[2:]>0):
  raise RuntimeError("theory TT C_l not positive")
 return C

def weighted_masked_alm(maps, mask, *,nside=NSIDE,lmax=LMAX):
    """Exact same weighted monopole/dipole fit and mask for all sky maps.

    Fractional NSIDE64 mask is retained, already present in K1. Each
    realization is processed independently, no estimand changes by noise id.
    """
    pix=np.arange(hp.nside2npix(nside))
    vec=np.stack(hp.pix2vec(nside,pix),axis=1)
    X=np.column_stack([np.ones(len(pix)),vec])
    w=mask
    gram=X.T@(w[:,None]*X)
    inv=np.linalg.inv(gram)
    D=inv@(X.T*w)
    data=np.asarray(maps,float)
    one=data.ndim==1
    rows=data[None,:] if one else data
    out=np.empty((rows.shape[0],hp.Alm.getsize(lmax)),np.complex128)
    for i,y in enumerate(rows):
      coef=D@y
      residual=(y-X@coef)*w
      out[i]=hp.map2alm(residual,lmax=lmax,iter=0,pol=False)
    return out[0] if one else out

def index_complex(alm,l,m,*,lmax=LMAX):
 idx=hp.Alm.getidx(lmax,l,abs(m))
 a=alm[...,idx]
 return a if m>=0 else (-1)**(-m)*np.conj(a)

def gaunt_terms(c_l):
    """Precompute actual exact Wigner 3j Gaunt factors and (C_l+C_l') normalization."""
    terms={}
    for ib,(lmin,lmax) in enumerate(BANDS):
      for M in M_LIST:
        this=[]
        gnorm=0.
        for ell in range(lmin,lmax+1):
          lp=ell+2
          pref=math.sqrt(5*(2*ell+1)*(2*lp+1)/(4*math.pi))
          w0=float(wigner_3j(ell,2,lp,0,0,0))
          for m in range(-ell,ell+1):
            mp=m-M
            if abs(mp)>lp:continue
            w1=float(wigner_3j(ell,2,lp,-m,M,mp))
            G=(-1)**m*pref*w0*w1
            if abs(G)<1e-14:continue
            den=c_l[ell]+c_l[lp]
            this.append((ell,m,lp,mp,G/den))
            gnorm+=G*G
        if gnorm<=0:raise RuntimeError("zero Gaunt norm")
        terms[ib,M]={"terms":this,"G_squared_norm":float(gnorm)}
    return terms

def project_biposh(alms, terms, *,lmax=LMAX):
    a=np.asarray(alms,dtype=complex)
    if a.ndim==1:a=a[None,:]
    N=a.shape[0]
    res=np.zeros((N,len(BANDS),5),float)
    for ib in range(len(BANDS)):
      values={}
      for M in M_LIST:
        acc=np.zeros(N,dtype=np.complex128)
        item=terms[ib,M]
        for l,m,lp,mp,coef in item["terms"]:
          aa=index_complex(a,l,m,lmax=lmax)
          bb=index_complex(a,lp,mp,lmax=lmax)
          acc += coef*aa*np.conj(bb)
        values[M]=acc/item["G_squared_norm"]
      # Components as a real orthonormal encoding of M=0,1,2.
      # For real maps and an L=2 physical sky: A_2,-M=(-1)^M conj A_2,M.
      res[:,ib,0]=values[0].real
      res[:,ib,1]=np.sqrt(2)*values[1].real
      res[:,ib,2]=np.sqrt(2)*values[1].imag
      res[:,ib,3]=np.sqrt(2)*values[2].real
      res[:,ib,4]=np.sqrt(2)*values[2].imag
      if max(abs(values[0].imag))>1e-6*max(1.,max(abs(values[0].real))):
       raise RuntimeError("BipoSH reality fail M=0")
    return res

def loo_diag_q(x, target):
    """Deterministic diagonal 20D test, empirically calibrated across MC.

    Does not assume independent bands for the null distribution, because
    the *full score* is calibrated against same MC realizations. Leave-one-
    out means/variances avoid overly optimistic in-sample ranks.
    """
    x=np.asarray(x,float)
    z=np.asarray(target,float)
    if x.ndim!=2 or z.shape!=(x.shape[1],) or x.shape[0]<50:
      raise ValueError("bad MC test dimensions")
    n=len(x)
    mean=x.mean(axis=0)
    var=x.var(axis=0,ddof=1)
    if np.any(var<=1e-18):raise ValueError("zero empirical stat variance")
    obs=float(np.sum((z-mean)**2/var))
    loo=np.empty(n)
    for i in range(n):
      e=np.delete(x,i,axis=0)
      me=e.mean(axis=0)
      va=e.var(axis=0,ddof=1)
      loo[i]=float(np.sum((x[i]-me)**2/va))
    tail=int(np.count_nonzero(loo>=obs))
    return {"observed_score":obs,"MC_N":n,"null_tail_count":tail,
            "rank_p":(tail+1)/(n+1),"MC_median_score":float(np.median(loo)),
            "MC_p95_score":float(np.quantile(loo,.95)),
            "mean_all":mean.tolist(),"std_all":np.sqrt(var).tolist(),
            "test":"20D diagonally standardized score, LOO calibrated jointly through MC, 4 fixed bands x 5 real M components"}

def run():
 t0=time.monotonic()
 ids,cmb,noise,obs,mask,cachehash,lowdiff=read_inputs()
 theory=iso_theory_cl()
 terms=gaunt_terms(theory)
 noise_by_id=ids%300
 # Physical raw original CMB+noise SIMS as defined in K1; source cache is
 # exact downgraded representation. Noise is reused three times on 999.
 alm_mc=np.empty((999,hp.Alm.getsize(LMAX)),np.complex128)
 for i,idx in enumerate(ids):
  alm_mc[i]=weighted_masked_alm(cmb[i]+noise[int(idx)%300],mask)
 alm_obs=weighted_masked_alm(obs,mask)
 x_mc=project_biposh(alm_mc,terms).reshape(999,20)
 x_obs=project_biposh(alm_obs,terms)[0].reshape(20)
 # Noise-independent first-cycle 300 set (0...299).
 distinct=np.isin(ids,np.arange(300))
 primary=loo_diag_q(x_mc[distinct],x_obs)
 secondary=loo_diag_q(x_mc,x_obs)
 subset_cycle={}
 for j in range(3):
   selected=(ids//300)==j
   if np.count_nonzero(selected)>50:
    subset_cycle[str(j)]=loo_diag_q(x_mc[selected],x_obs)
 # Single-band LOO scores. Each is a pre-fixed directional amplitude
 # estimator, unlike legacy fsky-only variance.
 bands={}
 for ib,(low,hi) in enumerate(BANDS):
  band=x_mc[:,ib*5:(ib+1)*5]
  bandobs=x_obs[ib*5:(ib+1)*5]
  bands[f"{low}-{hi}"]={
    "observed_signed_biposh_real5":bandobs.tolist(),
    "unique_noise_300":loo_diag_q(band[distinct],bandobs),
    "recycled_noise_999":loo_diag_q(band,bandobs),
  }
 # Paired injection: use CMB sample independent of noise for all 20
 # samples, fixed modulation 0.1*Y20(n); compare signed A20 after same mask.
 pix=np.arange(hp.nside2npix(NSIDE))
 costh=np.asarray(hp.pix2vec(NSIDE,pix))[2]
 y20=np.sqrt(5/(16*math.pi))*(3*costh**2-1)
 inp=weighted_masked_alm((cmb[:20]+noise[:20])*(1+.1*y20[None,:]),mask)
 inj=project_biposh(inp,terms)
 ref=x_mc[:20].reshape(20,4,5)
 gains=(inj[:,:,0]-ref[:,:,0]).mean(axis=0)
 # Note sign alone is an injection/orientation check, not robust
 # cosmological calibration of all 5 biaxial modes.
 source_count={"cmb_ids":int(len(ids)),"missing_cmb_id":970,
               "noise_ids":300,"noise_pairing":"noise_id = cmb_id % 300",
               "cmb_total_raw_bytes":603383850942,
               "source_cache_nside":NSIDE,"mask_mean":float(mask.mean()),
               "masked_pixels_weighted":float(mask.sum()),"units":"microK"}
 return ({
  "schema":"htt.r93.smica_ffp999_T_alm_masked_l2_biposh/1",
  "output":"NSIDE64 proxy of original full-resolution data; T-only, 4 fixed bands to l=46",
  "fft_lmax":LMAX,"nside":NSIDE,"source_counts":source_count,
  "known_00818_truncated_trailing_padding_source":"documented in official pre-existing PR150 E2E manifest; full data HDU usable",
  "source_cache_sha256":cachehash,"source_pr150_manifest_sha256":sha(PR150),
  "source_k1_gate_sha256":sha(GATE),"source_plik_theory_sha256":sha(THEORY),
  "cache_original_lmax8_alm_max_abs_rounding":lowdiff,
  "observed_alm_coefficients":int(len(alm_obs)),
  "observed_masked_cl_TT_ell_2_to_48":hp.alm2cl(alm_obs)[2:].tolist(),
  "bands":bands,"global_unique_noise_300":primary,
  "global_noise_reused_999":secondary,
  "global_reused_noise_cycle_sensitivity":subset_cycle,
  "injection_gY20":0.1,"injection_average_shift_A20_by_band":gains.tolist(),
  "seconds":float(time.monotonic()-t0),
  "claim":"FULL_999_SIGNAL_REPLAY + 300_REUSED_NOISE CONDITIONAL; NOT RELEASE_MATCHED_COMMANDER_NULL",
  "physical_significance":"conditional SMICA FFP10 E2E with frozen cache, no external heldout or new global registration",
  "high_ell_caveat":"NSIDE64 cache is exact downgraded map but not pre-harmonic low-pass; finite-pixel averaging/aliasing and foreground/beam require independent full-resolution validation before high-l claims",
  "polarization":"NOT_ANALYZED_R93_T_CACHE_ONLY; raw 999 have Q/U available for separate E/B lane",
  "Bianchi_family_attribution":None,"native_boltzmann_used":False,
 },{"cmb_ids":ids,"noise_id_for_each_cmb":noise_by_id,
    "paired_masked_alm_lmax48":alm_mc.astype(np.complex64),
    "observed_masked_alm_lmax48":alm_obs.astype(np.complex64),
    "biposh_real5_by_band":x_mc.reshape(999,4,5).astype(np.float32)})

def main():
 parser=argparse.ArgumentParser()
 g=parser.add_mutually_exclusive_group(required=True)
 g.add_argument("--write",action="store_true")
 g.add_argument("--check",action="store_true")
 args=parser.parse_args()
 summary,arrays=run()
 out=OUT/"SMICA_999_NSIDE64_BIPOSH_RESULT.json"
 npz=PRIVATE/"SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
 if args.write:
  if out.exists() or npz.exists():raise RuntimeError("create-only output already exists")
  PRIVATE.mkdir(parents=True,exist_ok=True)
  np.savez(npz,**arrays)
  summary["private_full_alm_path"]=str(npz)
  summary["private_full_alm_sha256"]=sha(npz)
  out.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
 else:
  existing=json.loads(out.read_text())
  sh=existing["private_full_alm_sha256"]
  if not npz.is_file() or sha(npz)!=sh:raise RuntimeError("private output SHA drift")
  del existing["private_full_alm_path"]
  del existing["private_full_alm_sha256"]
  # Timings are not deterministic.
  del existing["seconds"]
  del summary["seconds"]
  if json.dumps(existing,sort_keys=True)!=json.dumps(summary,sort_keys=True):
   raise RuntimeError("recomputed R93 highell statistical output differs")
 print(json.dumps({"mode":"write" if args.write else "check",
                  "n_cmb":summary["source_counts"]["cmb_ids"],
                  "n_noise_unique":summary["source_counts"]["noise_ids"],
                  "bands":list(BANDS),
                  "global_p_unique300":summary["global_unique_noise_300"]["rank_p"],
                  "global_p_reuse999":summary["global_noise_reused_999"]["rank_p"],
                  "injection_signs":np.sign(summary["injection_average_shift_A20_by_band"]).tolist(),
                  "runtime":summary.get("seconds","RECOMPUTED_VERIFIED")},ensure_ascii=False))
if __name__=="__main__":
 main()
