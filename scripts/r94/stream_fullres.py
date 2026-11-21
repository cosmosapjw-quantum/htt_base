"""R94 full-resolution (NSIDE=2048) FFP10 SMICA streaming T/E/B preprocessor.

--pilot processes only real MC ids 0, 818, 999, each paired with its
registered noise_mc[id % 300], with the exact K1 PR150 *source-contracted*
common temperature and polarization masks. Reads raw 603MB source files in
place and never rewrites/moves them. Stores only harmonic coefficients in
local Downloads and a small public receipt in R94.

--full writes finite chunks to Downloads (create-only/checkpoint); may require
significant I/O and is intended for the local coding agent. No full production
run or statistical detection is claimed until every chunk and source null is
validated. Beam/full high-ell CMB model are not supplied by this converter.

NB: This input pair's released Q/U are RING, observed SMICA/masks are NESTED.
NSIDE64 R93 registered T mono/dipole working fit is carried into full-res
to allow a same-model resolution comparison rather than quietly changing the
estimand. Do not claim NSIDE64 cache is bandlimited or CMB E/B unmasked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
import warnings

import healpy as hp
import numpy as np
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning

ROOT=Path(__file__).resolve().parents[2]
R94=ROOT/"docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122"
CACHE=Path("/mnt/extdrive/workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz")
R93=Path.home()/"Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
INPUT=Path("/mnt/extdrive/workdir/raw/planck_ffp10/smica")
MASKROOT=Path("/mnt/extdrive/workdir/raw/planck_data")
HASHLOG=INPUT/"logs/SHA256SUMS.raw_fits.available1299.txt"
DEST=Path.home()/"Downloads/htt_r94_fullres_stream"
L_MAX=48
PILOT_IDS=(0,818,999)
ID_MISSING=970
NPIX=hp.nside2npix(2048)

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()

def registry():
 res={}
 for line in HASHLOG.read_text().splitlines():
  fields=line.split()
  if len(fields)!=2:continue
  res[Path(fields[1]).name]=fields[0]
 return res

def load_mask(name:str):
 fn=MASKROOT/name
 with fits.open(fn,memmap=True) as f:
  if f[1].header.get("NSIDE")!=2048 or f[1].header.get("ORDERING")!="NESTED":
   raise ValueError("official mask is no longer NSIDE2048 NESTED")
  column="TMASK" if "Int_" in name else "PMASK"
  map_=hp.reorder(np.asarray(f[1].data[column],np.float32).reshape(-1),n2r=True)
 if np.any(~np.isfinite(map_)) or map_.min()<0 or map_.max()>1:
  raise ValueError("invalid observed mask")
 return map_

def prep_low_beta(cmb_ids, noise_by_id, cmb, noise, mask64):
 nside=64; npix=hp.nside2npix(nside)
 if len(mask64)!=npix:raise RuntimeError("registered NSIDE64 mask missing")
 xyz=np.stack(hp.pix2vec(64,np.arange(npix)),axis=1)
 X=np.column_stack([np.ones(npix),xyz])
 u=np.asarray(mask64,float)
 pre=np.linalg.solve(X.T@(u[:,None]*X),X.T*u)
 # For 999 samples this is tiny; preserves exact R93 mono/dipole fit.
 return {int(i):pre@(cmb[k]+noise[int(i)%300])
         for k,i in enumerate(cmb_ids) if int(i) in noise_by_id}

def read_pair_file(id_,kind="cmb"):
 if kind not in ("cmb","noise"):raise ValueError("invalid FFP10 MC source kind")
 p=INPUT/("cmb_mc" if kind=="cmb" else "noise_mc")
 name=f"dx12_v3_smica_{kind}_mc_{id_:05d}_raw.fits"
 path=p/name
 if not path.is_file():raise FileNotFoundError(path)
 if path.stat().st_size<603_980_000 or path.stat().st_size>604_000_000:
  raise RuntimeError("source FITS size outside verified FFP10 envelope")
 return path

def _read_col(hdu,col):
 return np.asarray(hdu.data[col],np.float64).reshape(-1).copy()

def process_one(id_, beta64, maskI, maskP, *,registered_hashes, verify_sha=False):
 c=read_pair_file(id_,"cmb")
 n=read_pair_file(id_%300,"noise")
 for path in (c,n):
  if path.name not in registered_hashes:
   raise RuntimeError("no K1 raw hash registration for "+path.name)
  if verify_sha and sha(path)!=registered_hashes[path.name]:
   raise RuntimeError("SHA mismatch for "+path.name)
 # Exception is exactly 00818 trailing FITS padding. All other warnings
 # are preserved in this scientific scope instead of unconditionally ignored.
 with warnings.catch_warnings(record=True) as captured:
  warnings.simplefilter("always",AstropyWarning)
  with fits.open(c,memmap=True) as f, fits.open(n,memmap=True) as g:
   for h in (f[1],g[1]):
    if h.header.get("NSIDE")!=2048 or h.header.get("ORDERING")!="RING":
     raise RuntimeError("FFP10 file sky pixelization unexpected")
   t=(_read_col(f[1],"INTENSITY")+_read_col(g[1],"INTENSITY"))*1e6
   # Reuse R93 pre-fit beta from same exact K1 NSIDE64 partial sky.
   t-=beta64[0]
   ringxyz=np.stack(hp.pix2vec(2048,np.arange(NPIX)),axis=0)
   # Avoid allocating Nx4 Cartesian design; 3 vector operations.
   for k in range(3):
    t-=beta64[k+1]*ringxyz[k]
   del ringxyz
   t*=maskI
   aT=hp.map2alm(t,lmax=L_MAX,iter=0,pol=False)
   del t
   q=(_read_col(f[1],"Q-POLARISATION")+_read_col(g[1],"Q-POLARISATION"))*1e6
   u=(_read_col(f[1],"U-POLARISATION")+_read_col(g[1],"U-POLARISATION"))*1e6
   q*=maskP;u*=maskP
   aE,aB=hp.map2alm_spin([q,u],spin=2,lmax=L_MAX)
   del q,u
 warn=[str(z.message)[:200] for z in captured]
 if warn and id_!=818:
  raise RuntimeError("unexpected FITS warning for "+str(id_)+":"+repr(warn[:3]))
 return np.asarray([aT,aE,aB],dtype=np.complex64),{
  "id":id_,"noise_id":id_%300,"raw_cmb":c.name,"raw_noise":n.name,
  "registered_raw_hashes":{"cmb":registered_hashes[c.name],"noise":registered_hashes[n.name]},
  "actual_hashed":verify_sha,
  "observed_reader_warnings":warn,"lowres_mono_dipole_beta_uK":beta64.tolist()}

def input_identity():
 if sha(CACHE)!="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb":
  raise RuntimeError("K1 source cache drift")
 with np.load(CACHE,allow_pickle=False) as d:
  ids=np.asarray(d["cmb_ids"],int)
  cmb=d["cmb_maps"].copy()
  noise=d["noise_maps"].copy()
  mask64=d["common_mask"].copy()
 if len(ids)!=999 or set(ids)!=set(range(1000))-{ID_MISSING}:
  raise RuntimeError("CMB MC inventory changed")
 return ids,cmb,noise,mask64

def run(pilot=True,verify_sha=False):
 begin=time.perf_counter()
 ids,cmb,noise,mask64=input_identity()
 want=PILOT_IDS if pilot else tuple(int(i) for i in ids)
 inputids=set(want)
 beta=prep_low_beta(ids,inputids,cmb,noise,mask64)
 reg=registry()
 maskI=load_mask("COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
 maskP=load_mask("COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits")
 if pilot:
  target=DEST/"pilot_00000_00818_00999.npz"
  receipt=R94/"FFP10_FULLRES_STREAM_PILOT.json"
  if target.exists() or receipt.exists():
   raise RuntimeError("create-only R94 pilot already exists")
  DEST.mkdir(parents=True,exist_ok=True)
  transformed=[];cases=[]
  for i in want:
   a,info=process_one(i,beta[i],maskI,maskP,
     registered_hashes=reg,verify_sha=verify_sha)
   transformed.append(a);cases.append(info)
  np.savez(target,cmb_ids=np.asarray(want,dtype=np.int32),
    noise_ids=np.asarray(want,dtype=np.int32)%300,
    TEB_alm=np.stack(transformed))
  obj={"schema":"htt.r94.ffp10_smica_fullres_pilot/1",
   "nside":2048,"lmax":L_MAX,"methods":"FFP10 exact raw T/Q/U RING, masked T/I & Q/U separately, spin2 map2alm_spin",
   "source_case_count":len(cases),"selected_cmb_ids":list(want),
   "matched_noise_id_rule":"id mod 300","cases":cases,
   "cache_identity":sha(CACHE),"maskI_source_sha256":sha(MASKROOT/"COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"),
   "maskP_source_sha256":sha(MASKROOT/"COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"),
   "private_harmonic_path":str(target),"private_harmonic_sha256":sha(target),
   "raw_file_sha_actual":verify_sha,"source_original_data_changed":False,
   "elapsed_wall_seconds":time.perf_counter()-begin,
   "physical_significance":"STREAMED_RAW_SOURCE_PILOT_NOT_FULL_999",
   "high_l_model_source":"NONE",
   "full_resolution_entire_999_done":False,"full_EB_null_calibrated":False}
  receipt.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n")
  return obj
 # Full loop: chunks of 25; outputs kept private only, allow bounded resume
 # of previously verified chunk files without silently overwriting them.
 DEST.mkdir(parents=True,exist_ok=True)
 chunkrecords=[]
 chunk=25
 for start in range(0,len(want),chunk):
  section=want[start:start+chunk]
  target=DEST/f"full_TEB_{section[0]:05d}_{section[-1]:05d}.npz"
  if target.exists():
   with np.load(target,allow_pickle=False) as d:
    if d["cmb_ids"].tolist()!=list(section):raise RuntimeError("existing chunk contents conflict")
   chunkrecords.append({"chunk":target.name,"ids":list(section),"sha256":sha(target),"status":"ALREADY_VERIFIED"})
   continue
  data=[];cases=[]
  for i in section:
   a,info=process_one(i,beta[i],maskI,maskP,registered_hashes=reg,
                      verify_sha=verify_sha)
   data.append(a);cases.append(info)
  tmp=target.with_suffix(".partial")
  if tmp.exists():raise RuntimeError("stale partial chunk")
  with tmp.open("xb") as f:
   np.savez(f,cmb_ids=np.asarray(section,dtype=np.int32),
            noise_ids=np.asarray(section,dtype=np.int32)%300,
            TEB_alm=np.stack(data))
  os.replace(tmp,target)
  chunkrecords.append({"chunk":target.name,"ids":list(section),"sha256":sha(target),"status":"COMPUTED"})
  print("FULL_CHUNK",start,len(section),target.name,"elapsed",time.perf_counter()-begin,flush=True)
 private=DEST/"full_stream_manifest.json"
 if private.exists():raise RuntimeError("full result already exists")
 private.write_text(json.dumps({
  "schema":"htt.r94.full_999_harmonic_stream/1",
  "count":len(want),"chunks":chunkrecords,
  "input_cache_sha256":sha(CACHE),
  "total_seconds":time.perf_counter()-begin,
  "science_status":"STREAMED_HARMONIC_COMPONENTS_ONLY_NOT_BIANCHI_LIKELIHOOD"},indent=2)+"\n")
 return {"private_manifest":str(private),"count":len(want),"chunks":len(chunkrecords)}

def main():
 p=argparse.ArgumentParser()
 z=p.add_mutually_exclusive_group(required=True)
 z.add_argument("--pilot",action="store_true")
 z.add_argument("--full",action="store_true")
 z.add_argument("--check-pilot",action="store_true")
 p.add_argument("--sha",action="store_true",help="SHA all piloted source files on read (costs I/O)")
 opts=p.parse_args()
 if opts.check_pilot:
  j=json.loads((R94/"FFP10_FULLRES_STREAM_PILOT.json").read_text())
  if sha(Path(j["private_harmonic_path"]))!=j["private_harmonic_sha256"]:
   raise RuntimeError("pilot source identity drift")
  print(json.dumps({"pilot":True,"qualified_contents":True,"n":j["source_case_count"]}))
 else:
  x=run(pilot=opts.pilot,verify_sha=opts.sha)
  print(json.dumps({"status":"PILOT" if opts.pilot else "FULL",
                    "n":x.get("source_case_count",x.get("count")),"runtime_s":x.get("elapsed_wall_seconds"),
                    "all_999":bool(opts.full)},ensure_ascii=False))
if __name__=="__main__":main()
