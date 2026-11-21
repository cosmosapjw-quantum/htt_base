"""R93 independent one-pair full-NSIDE2048 vs approved K1 NSIDE64 masked T a_lm.

Read original FFP10 SMICA cmb MC 00000 + noise MC 00000 and original
PR3 common mask (NESTED), compare to old exact replay cache after the same
weighted NSIDE64-fit monopole/dipole subtraction. This is a finite
resolution/aliasing test; not a validation for all 999 maps or high-l physics.
"""
from pathlib import Path
from astropy.io import fits
import hashlib,json
import healpy as hp
import numpy as np

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
RAW=Path("/mnt/extdrive/workdir/raw/planck_ffp10")
CMB=RAW/"smica/cmb_mc/dx12_v3_smica_cmb_mc_00000_raw.fits"
NOI=RAW/"smica/noise_mc/dx12_v3_smica_noise_mc_00000_raw.fits"
MASK=Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
CACHE=Path("/mnt/extdrive/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
R93=Path.home()/"Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
OUTPUT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/NSIDE2048_VS_N64_ALM_TRANSFER_QA.json"
BANDS=((2,8),(9,16),(17,32),(33,46))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for part in iter(lambda:f.read(8<<20),b""):h.update(part)
 return h.hexdigest()

def calc():
 with np.load(CACHE,allow_pickle=False) as c:
  lo=c["cmb_maps"][0]+c["noise_maps"][0]
  masklo=c["common_mask"]
 with np.load(R93,allow_pickle=False) as c:
  almlo=np.asarray(c["paired_masked_alm_lmax48"][0],np.complex128)
 pix64=np.arange(lo.size)
 vec64=np.asarray(hp.pix2vec(64,pix64)).T
 X=np.column_stack([np.ones(len(pix64)),vec64])
 beta=np.linalg.solve(X.T@(masklo[:,None]*X),X.T@(masklo*lo))
 with fits.open(MASK,memmap=True) as h:
  maskhi=hp.reorder(np.asarray(h[1].data["TMASK"],np.float32).reshape(-1),n2r=True)
 if abs(maskhi.mean()-masklo.mean())>1e-5:
  raise RuntimeError("inconsistent mask sky fraction across resolutions")
 with fits.open(CMB,memmap=True) as f, fits.open(NOI,memmap=True) as g:
  sky=np.asarray(f[1].data["INTENSITY"],dtype=np.float64).reshape(-1).copy()
  sky+=np.asarray(g[1].data["INTENSITY"],dtype=np.float64).reshape(-1)
 sky*=1e6
 sky-=beta[0]
 pix=np.arange(sky.size)
 xp,yp,zp=hp.pix2vec(2048,pix)
 del pix
 sky-=beta[1]*xp
 sky-=beta[2]*yp
 sky-=beta[3]*zp
 del xp,yp,zp
 sky*=maskhi
 del maskhi
 almhi=hp.map2alm(sky,lmax=48,iter=0,pol=False)
 band={}
 for ll,hh in BANDS:
  inds=[hp.Alm.getidx(48,l,m) for m in range(hh+1) for l in range(max(ll,m),hh+1)]
  x=np.asarray(almhi[inds]);y=np.asarray(almlo[inds])
  band[f"{ll}-{hh}"]={
    "relative_alm_L2_difference":float(np.linalg.norm(x-y)/np.linalg.norm(x)),
    "complex_alm_direction_correlation":float(np.real(np.vdot(x,y)/np.sqrt(np.vdot(x,x)*np.vdot(y,y)))),
    "nside64_over_nside2048_rms":float(np.sqrt(np.vdot(y,y).real/np.vdot(x,x).real)),
    "n_alm":len(inds)}
 return {
  "schema":"htt.r93.smica_one_pair_full_resolution_mask_alm_comparison/1",
  "source_map":"SMICA_FFP10_00000_CMB_PLUS_NOISE_BOTH_N2048",
  "raw_cmb_sha256":sha(CMB),"raw_noise_sha256":sha(NOI),"common_mask_sha256":sha(MASK),
  "cache_sha256":sha(CACHE),"R93_masked_alm_npz_sha256":sha(R93),
  "lmax":48,"nside_raw":2048,"nside_cache":64,
  "weighted_original_NSIDE64_fit_beta_uK":beta.tolist(),
  "bands":band,
  "no_high_l_detection":True,
  "scope":"single CMB+noise raw pair, fixed common mask, same cache-regr fit; resolution/aliasing and mask response quantified, not all 999 full-resolution pass"
 }
if __name__=="__main__":
 if OUTPUT.exists():raise RuntimeError("create-only output")
 q=calc()
 OUTPUT.write_text(json.dumps(q,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"bands":q["bands"]},ensure_ascii=False))
