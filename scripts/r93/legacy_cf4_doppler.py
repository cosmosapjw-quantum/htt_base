"""R93 reuse actual Mayukh-ver3 HTT.zip legacy SN-like tilt redshift model.

Adversarially compare claimed 'exact relativistic' legacy inverse
  zc = (1+zobs)/(1+beta cosθ)-1
with normalized SR Doppler inverse
  zc = (1+zobs)/[gamma(1+beta cosθ)]-1,
under the SAME explicitly chosen signed convention. The correction is O(beta²)
and is an independent algebraic check, not source-matched CF4 PV calibration.
Execute across all actual 35,970 CF4 source directions/redshifts and fixed
Planck solar-apex direction, with declared physical unit c.
No modifications to the historical ZIP or R78 science authority.
"""
from __future__ import annotations
import hashlib,json,math,zipfile
from pathlib import Path
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ZIP=Path("/home/cosmosapjw/Dropbox/Mayukh_cowork/ver3/HTT.zip")
MEMBER="HTT/htt/catalog_likelihood.py"
CF4=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
OUT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/CF4_LEGACY_TILT_DOPPLER_COMPARISON.json"
C=299792.458

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(2**20),b""):h.update(b)
 return h.hexdigest()

def compare():
 with zipfile.ZipFile(ZIP) as f:
  src=f.read(MEMBER)
  legacy_source=src.decode()
 if "z_c = (1+z_obs)/(1+β cosθ) − 1" not in legacy_source and "(1+z_obs)/(1+β cosθ)" not in legacy_source:
  raise RuntimeError("Mayukh legacy inverse-redshift formula drift")
 with np.load(CF4,allow_pickle=False) as f:
  n=np.asarray(f["n_J2000"],float)
  z=np.asarray(f["z_CMB"],float)
 if len(z)!=35970 or n.shape!=(35970,3) or np.any(z<=0):
  raise RuntimeError("CF4 selected actual group geometry changed")
 # Astropy ICRS unit direction of Planck solar-system CMB dipole apex.
 sky=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
 direction=np.asarray(sky.cartesian.xyz.value,float)
 direction/=np.linalg.norm(direction)
 cosine=n@direction
 expected=np.linalg.norm(n,axis=1)
 if np.max(abs(expected-1))>1e-8:
  raise RuntimeError("CF4 unit direction drift")
 metrics={}
 for beta in (0.,0.001,0.003,0.01):
  gamma=1./np.sqrt(1.-beta**2)
  legacy=(1+z)/(1+beta*cosine)-1
  exact=(1+z)/(gamma*(1+beta*cosine))-1
  d=legacy-exact
  v=np.isfinite(exact)&np.isfinite(legacy)&(exact>0)&(legacy>0)&(z>0.01)
  # conditional low-z distance modulus difference using d_L∝z, not an
  # exact finite-z cosmology, and not source calibration likelihood.
  dmu=(5./np.log(10.))*np.log(legacy[v]/exact[v])
  metrics[str(beta)]={
   "beta":beta,"speed_km_s":beta*C,"gamma":gamma,
   "all_selected_35970_delta_z_p50_abs":float(np.median(abs(d))),
   "all_selected_delta_z_p95_abs":float(np.quantile(abs(d),.95)),
   "positive_distance_zobs_gt0p01_count":int(v.sum()),
   "lowz_dmu_median_abs_mag":float(np.median(abs(dmu))) if v.any() else 0.,
   "lowz_dmu_p95_abs_mag":float(np.quantile(abs(dmu),.95)) if v.any() else 0.,
   "old_minus_gamma_corrected_minmax_delta_z":[float(np.min(d)),float(np.max(d))]
  }
 if metrics["0.0"]["all_selected_35970_delta_z_p50_abs"]!=0:
  raise RuntimeError("zero boost exact limit failed")
 return {
  "schema":"htt.r93.legacy_mayukh_exact_doppler_source_check/1",
  "source_zip":str(ZIP),"source_zip_sha256":sha(ZIP),
  "source_member":MEMBER,"source_member_sha256":hashlib.sha256(src).hexdigest(),
  "cf4_group_sha256":sha(CF4),"cf4_all_selected_groups":len(z),
  "fixed_solar_apex": {"galactic_l_deg":264.021,"galactic_b_deg":48.253,"ICRS_vector":direction.tolist()},
  "metric_signature":"(-,+,+,+)",
  "convention":"legacy zobs=(1+zc)*D-1 with D=gamma(1+beta*mu), chosen solely to match quoted legacy orientation",
  "legacy_formula":"zc_old=(1+zobs)/(1+beta*mu)-1 (gamma factor omitted)",
  "SR_corrected_formula":"zc_SR=(1+zobs)/(gamma*(1+beta*mu))-1",
  "amplitude_grid":metrics,
  "physics_boundary":"source-conditioned forward redshift conversion, not upstream calibration or physical peculiar velocity covariance",
  "legacy_code_not_executed":True,
  "physical_SQ_CF4_acceptance":"BLOCKED_INPUT",
 }
if __name__=="__main__":
 if OUT.exists():raise RuntimeError("create-only output")
 x=compare()
 OUT.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"groups":x["cf4_all_selected_groups"],
                   "beta_grid":{k:{"dmu_p95":v["lowz_dmu_p95_abs_mag"],
                                   "delta_z_p95":v["all_selected_delta_z_p95_abs"]}
                                  for k,v in x["amplitude_grid"].items()}}))
