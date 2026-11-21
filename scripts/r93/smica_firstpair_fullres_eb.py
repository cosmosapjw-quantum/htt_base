"""R93 observed SMICA and FFP10 MC 00000+noise 00000 full-resolution E/B pilot.

Reads original NSIDE2048 Q/U maps with correct NESTED->RING order for
observed SMICA and PR3 pol common mask, RING for FFP10 MC. Computes spin-2
HEALPix a_E/a_B at lmax48 without downgrading. No polarization Monte Carlo
null, no beam/foreground/reionization/Bianchi transfer correction.
"""
from pathlib import Path
from astropy.io import fits
import healpy as hp,numpy as np,json
from hashlib import sha256

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE=Path("/mnt/extdrive/workdir/raw")
OBS=BASE/"planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits"
MASK=BASE/"planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"
MC=BASE/"planck_ffp10/smica/cmb_mc/dx12_v3_smica_cmb_mc_00000_raw.fits"
NOI=BASE/"planck_ffp10/smica/noise_mc/dx12_v3_smica_noise_mc_00000_raw.fits"
OUT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/SMICA_FULLRES_EB_FIRSTPAIR_PILOT.json"
BANDS=((2,8),(9,16),(17,32),(33,46))

def read_observed():
 with fits.open(OBS,memmap=True) as f:
  q=hp.reorder(np.asarray(f[1].data["Q_STOKES"],np.float32).reshape(-1),n2r=True).astype(np.float64)
  u=hp.reorder(np.asarray(f[1].data["U_STOKES"],np.float32).reshape(-1),n2r=True).astype(np.float64)
 return q*1e6,u*1e6

def read_mc_pair():
 with fits.open(MC,memmap=True) as f, fits.open(NOI,memmap=True) as g:
  q=np.asarray(f[1].data["Q-POLARISATION"],np.float64).reshape(-1)
  q=q+np.asarray(g[1].data["Q-POLARISATION"],np.float64).reshape(-1)
  u=np.asarray(f[1].data["U-POLARISATION"],np.float64).reshape(-1)
  u=u+np.asarray(g[1].data["U-POLARISATION"],np.float64).reshape(-1)
 return q*1e6,u*1e6

def transform(q,u,mask):
 if not (len(q)==len(u)==len(mask)==hp.nside2npix(2048)):
  raise RuntimeError("invalid full-resolution polarization geometry")
 q=np.nan_to_num(q*mask,posinf=0.,neginf=0.)
 u=np.nan_to_num(u*mask,posinf=0.,neginf=0.)
 e,b=hp.map2alm_spin([q,u],spin=2,lmax=48)
 cl_ee=hp.alm2cl(e)
 cl_bb=hp.alm2cl(b)
 cl_eb=hp.alm2cl(e,b)
 rows={}
 for l,h in BANDS:
  rows[f"{l}-{h}"]={
    "EE_mean_Cl_microK2":float(np.mean(cl_ee[l:h+1])),
    "BB_mean_Cl_microK2":float(np.mean(cl_bb[l:h+1])),
    "EB_mean_Cl_microK2":float(np.mean(cl_eb[l:h+1])),
    "mean_BB_over_EE":float(np.mean(cl_bb[l:h+1])/np.mean(cl_ee[l:h+1]))}
 return rows

def compute():
 with fits.open(MASK,memmap=True) as f:
  m=hp.reorder(np.asarray(f[1].data["PMASK"],np.float32).reshape(-1),n2r=True)
 if not (np.all(np.isfinite(m)) and np.all((m>=0)&(m<=1))):
  raise RuntimeError("invalid polarization mask")
 q,u=read_observed()
 o=transform(q,u,m)
 del q,u
 q,u=read_mc_pair()
 s=transform(q,u,m)
 return {
  "schema":"htt.r93.smica_one_realization_fullres_spin2_pilot/1",
  "nside":2048,"lmax":48,"observed_source":str(OBS),
  "ffp10_cmb_source":str(MC),"ffp10_noise_source":str(NOI),
  "same_pr3_common_polarization_mask":str(MASK),
  "mean_weighted_f_sky_polarization":float(m.mean()),
  "observed_EB_bandpowers":o,
  "one_MC_pair_EB_bandpowers":s,
  "harmonic_kind":"E/B spin-2 from Q/U on NSIDE2048; mask and polarization coordinate convention beyond HEALPix RING not independently source-qualified",
  "claim":"ONE_PAIR_IMPLEMENTATION_PILOT_ONLY; NO E/B NULL/CALIBRATED_DETECTION",
  "full_999_EB_done":False,
  "beam_transfer_matched":False,"Bianchi_family_detected":False}

if __name__=="__main__":
 if OUT.exists():raise RuntimeError("create-only artifact")
 d=compute()
 OUT.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"obs_BB_ratio":[x["mean_BB_over_EE"] for x in d["observed_EB_bandpowers"].values()],"MC_BB_ratio":[x["mean_BB_over_EE"] for x in d["one_MC_pair_EB_bandpowers"].values()],"fsky":d["mean_weighted_f_sky_polarization"]}))
