"""R93 adversarial numerical check of legacy bianchi_departure BipoSH prototype.

Old legacy estimate_biposh_L2 accumulates |a_lm|**2 into A20 without
Wigner coupling or signed offdiagonal l->l+2. It is nonnegative by
construction and not a valid centered L=2 statistical-isotropy test.
Use all 999 new R93 masked alms to show nonzero positive old statistic
against signed proper-Gaunt response. The replacement still requires
mask/foreground matched MC and true Bianchi transfer for detection.
"""
import hashlib,json,zipfile,math
from pathlib import Path
import numpy as np
import healpy as hp
from scripts.r93.smica_ffp999_biposh import iso_theory_cl,LMAX

ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
ZIP=ROOT/"legacy/bianchi_departure_v091_github.zip"
SRC="htt/likelihood/biposh_masked.py"
INPUT=Path.home()/"Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
OUT=ROOT/"docs/research_program/observational_publication_20261015/R93_THIRD_SCIENCE_LOOP_20261121/LEGACY_BIPOSH_INVALID_ESTIMAND.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def evaluate():
 with zipfile.ZipFile(ZIP) as f:raw=f.read(SRC)
 s=raw.decode("utf-8")
 required=("biposh[2] += np.real(a_lm * np.conj(a_lm))","biposh = np.zeros(5)","biposh /= (norm * f_sky)")
 if not all(x in s for x in required):
  raise RuntimeError("old legacy BipoSH source content changed")
 with np.load(INPUT,allow_pickle=False) as d:
  a=np.asarray(d["paired_masked_alm_lmax48"],np.complex64)
  corrected=np.asarray(d["biposh_real5_by_band"],np.float64)
  ids=np.asarray(d["cmb_ids"])
 if a.shape!=(999,hp.Alm.getsize(LMAX)):raise RuntimeError("R93 source changed")
 cl=iso_theory_cl()
 denom=sum((2*l+1)*cl[l] for l in range(2,31))
 fsky=.7794118722279867
 if denom<=0:raise RuntimeError("invalid theoretical normalizer")
 # Directly follow the *sign structure* of legacy loop at ell=2..30,
 # including its redundant |m| as its code uses abs(m).
 power=np.zeros(len(a))
 for l in range(2,31):
  for m in range(-l,l+1):
   power+=abs(a[:,hp.Alm.getidx(LMAX,l,abs(m))])**2
 pseudo=power/(denom*fsky)
 signed_m0=corrected[:,:,0]
 centered=signed_m0-signed_m0.mean(axis=0)[None,:]
 return {"schema":"htt.r93.legacy_biposh_unsafe_estimator_999_source/1",
         "legacy_source_sha256":hashlib.sha256(raw).hexdigest(),
         "legacy_zip_sha256":sha(ZIP),
         "private_alm_sha256":sha(INPUT),"MC_N":999,
         "legacy_pseudo_A20_positive_fraction":float(np.mean(pseudo>0)),
         "legacy_pseudo_A20_mean":float(np.mean(pseudo)),
         "legacy_pseudo_A20_min":float(np.min(pseudo)),
         "proper_Gaunt_centered_A20_fraction_negative_by_band":np.mean(centered<0,axis=0).tolist(),
         "legacy_source_actual":"biposh[2]+=|a_lm|² for all l,m, with fsky normalization but no genuine Clebsch-Gordan weight",
         "conclusion":"LEGACY_ESTIMATOR_INVALID_FOR_L2_BIPOSH; salvage structural API/data loader, replace quadrupolar estimator and mask mixing with exact-Gaunt plus simulation-calibrated covariance",
         "old_code_executed":False,
         "new_gaunt_source":"R93 scripts/r93/smica_ffp999_biposh.py",
         "publication_significance":"NOT_QUALIFIED",
         "Bianchi_type_identification":False}
if __name__=="__main__":
 if OUT.exists():raise RuntimeError("create-only")
 j=evaluate()
 OUT.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({k:v for k,v in j.items() if k in ("legacy_pseudo_A20_positive_fraction","legacy_pseudo_A20_mean","proper_Gaunt_centered_A20_fraction_negative_by_band")}))
