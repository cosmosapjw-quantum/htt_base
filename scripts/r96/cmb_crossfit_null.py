"""R96 source-conditioned full-covariance BiPoSH 60D null on real R95 fullres MC.

Legacy source's f_sky-only covariance is replaced by (1) exact Gaunt signed
ell->ell+2 coefficients, (2) 300 actual unique-noise-ID simulation mean
(mask-induced bias), (3) positive shrinkage of 60x60 covariance in
unit-variance coordinates, (4) leave-one-out full-covariance empirical MC
rank, (5) disjoint train/test comparison, (6) signal vs noise bias source
decomposition. All model choices are fixed in source before evaluating obs.
This is a new conditional SMICA FFP10 *diagnostic*, not full independent
Commander null nor a physical Bianchi high-ell posterior.
"""
from pathlib import Path
from hashlib import sha256
from time import perf_counter
import json
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from scripts.r94.gaunt_fast import build_terms,project
from scripts.r93.smica_ffp999_biposh import iso_theory_cl
from scripts.r95.planck_fullres_teb_analysis import _all_six_spectra
from scripts.r96.legacy_biposh_recovered import provenance

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122/CMB_MASK_BIPO_CROSSVALIDATED_NULL.json"
STREAM=Path.home()/"Downloads/htt_r94_fullres_stream"
R95=ROOT/"docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G05_PLANCK_FULLRES_TEB_RESULT.json"
MANIFEST=STREAM/"full_stream_manifest_r95.json"
LAMBDAS=(0.05,0.20,0.40)
L_MAX=48
def sha(p):
 h=sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(2**20),b""):h.update(x)
 return h.hexdigest()

def metric(X,y,shrinkage=0.20):
 X=np.asarray(X,float);y=np.asarray(y,float)
 n,d=X.shape
 assert y.shape==(d,) and n>d+10
 mean=X.mean(axis=0)
 Z=X-mean
 S=Z.T@Z
 C=S/(n-1)
 std=np.sqrt(np.diag(C))
 if std.min()<=0:raise RuntimeError("negative empirical variance")
 def solve_for(C,u):
  sd=np.sqrt(np.diag(C))
  corr=C/sd[:,None]/sd[None,:]
  corr=(1-shrinkage)*corr+shrinkage*np.eye(d)
  chi=cho_factor(corr,lower=True,check_finite=False)
  r=u/sd
  return float(r@cho_solve(chi,r,check_finite=False))
 qobs=solve_for(C,y-mean)
 qmc=np.empty(n)
 for i in range(n):
  d_i=Z[i]
  mu_i=mean-d_i/(n-1)
  S_i=S-(n/(n-1))*np.outer(d_i,d_i)
  Ci=(S_i+S_i.T)/(2*(n-2))
  qmc[i]=solve_for(Ci,X[i]-mu_i)
 tail=int(np.count_nonzero(qmc>=qobs))
 return {"N":n,"d":d,"lambda":shrinkage,
   "obs_score":qobs,"mc_quantiles_50_95_99":np.quantile(qmc,[.5,.95,.99]).tolist(),
   "tail_count":tail,"rank":(tail+1)/(n+1),
   "empirical_cov_corr_min_eigen":float(np.linalg.eigvalsh(C/std[:,None]/std[None,:]).min()),
   "shrunken_corr_min_eigen":float(np.linalg.eigvalsh((1-shrinkage)*C/std[:,None]/std[None,:]+shrinkage*np.eye(d)).min()),
   "max_feature_bias_over_sd":float(np.max(abs(mean)/std)),
   "mean_bias_euclidean":float(np.linalg.norm(mean))}

def load():
 man=json.loads(MANIFEST.read_text())
 if man["cmb_count"]!=999 or man["noise_count"]!=300:
  raise RuntimeError("R95 fullres source not complete")
 paired=[];single=[];id_all=[]
 for c in man["cmb_chunks"]:
  p=STREAM/c["chunk"]
  if sha(p)!=c["sha256"]:raise RuntimeError("manifest chunk sha drift "+p.name)
  with np.load(p,allow_pickle=False) as f:
   paired.append(np.asarray(f["TEB_alm"],np.complex128))
   single.append(np.asarray(f["cmb_only_TEB_alm"],np.complex128))
   id_all.extend(f["cmb_ids"].tolist())
 order=np.argsort(id_all)
 paired=np.concatenate(paired)[order]
 single=np.concatenate(single)[order]
 ids=np.array(id_all,int)[order]
 with np.load(STREAM/"noise_300_TEB_alm.npz",allow_pickle=False) as f:
  noise=f["TEB_alm"].astype(np.complex128)
  if f["noise_ids"].tolist()!=list(range(300)):raise RuntimeError("noise IDs mismatch")
 with np.load(STREAM/"observed_smica_commander_TEB_alm.npz",allow_pickle=False) as f:
  observed=f["smica_TEB_n2048sub"].astype(np.complex128)
 if (len(ids)!=999 or len(set(ids))!=999 or set(ids)!=set(range(1000))-{970}):
  raise RuntimeError("SMICA sample provenance invalid")
 return ids,paired,single,noise,observed,man

def compute():
 t0=perf_counter()
 ids,paired,signal,noise,obs,man=load()
 nfirst=ids<300
 C=np.zeros((3,L_MAX+1),float)
 C[0]=iso_theory_cl()
 raw=_all_six_spectra(paired[nfirst],L_MAX)
 C[1,2:]=np.maximum(raw["EE"][:,2:].mean(axis=0),1e-12)
 C[2,2:]=np.maximum(raw["BB"][:,2:].mean(axis=0),1e-12)
 terms=[build_terms(C[i],L_MAX) for i in range(3)]
 def all_bip(arr):
  return np.column_stack([project(arr[:,i,:],terms[i],backend="native").reshape(len(arr),20) for i in range(3)])
 X=all_bip(paired[nfirst])
 Xsig=all_bip(signal[nfirst])
 Xnoise=all_bip(noise)
 y=all_bip(obs[None,:,:])[0]
 old=json.loads(R95.read_text())["biposh_joint_60D_TEB"]["smica_n2048_unique_noise_300"]
 if old["MC_N"]!=300 or abs(old["rank_p"]-78/301)>1e-14:
  raise RuntimeError("original 60D rank source drift")
 report={str(k):metric(X,y,k) for k in LAMBDAS}
 # A disjoint 150/150 source holdout: fit mean/cov on train, rank obs
 # relative to holdout Q scores (only 150, no LOO and no post-hoc matching).
 i0=np.arange(300)%2==0
 train=X[i0];held=X[~i0]
 train_mu=train.mean(axis=0)
 train_C=np.cov(train,rowvar=False,ddof=1)
 diag=np.sqrt(np.diag(train_C))
 corr=train_C/diag[:,None]/diag[None,:]
 corr=.8*corr+.2*np.eye(60)
 chi=cho_factor(corr,lower=True,check_finite=False)
 def q(v):
  r=(v-train_mu)/diag
  return float(r@cho_solve(chi,r,check_finite=False))
 q_obs=q(y)
 held_score=np.asarray([q(v) for v in held])
 p_hold=(np.count_nonzero(held_score>=q_obs)+1)/(len(held)+1)
 # True noise+signal cross term in quadratic estimator (finite sample).
 err=X-Xsig-Xnoise
 denom=np.linalg.norm(X.mean(axis=0))
 bias={
  "MC_mean_masked_pair":np.linalg.norm(X.mean(axis=0)),
  "MC_mean_signal_only":np.linalg.norm(Xsig.mean(axis=0)),
  "MC_mean_noise_only":np.linalg.norm(Xnoise.mean(axis=0)),
  "MC_cross_terms_residual_mean":np.linalg.norm(err.mean(axis=0)),
  "cross_residual_over_pair_bias":np.linalg.norm(err.mean(axis=0))/max(denom,1e-30),
  "paired_minus_sum_is_not_expected_exact_per_realization":True,
 }
 return {"schema":"htt.r96.ffp10_masked_biposh_sim_matched_conditional_null/1",
         "source_shas":{"R95_G05":sha(R95),"R95_fullres_manifest":sha(MANIFEST),
           "R95_SMICA_observed":sha(STREAM/"observed_smica_commander_TEB_alm.npz"),
           "R94_gaunt_core":sha(ROOT/"scripts/r94/gaunt_fast.py")},
         "N_MC_unique_noise":300,"N_signal_MC_full":999,"nside_source":2048,
         "lmax":48,"features":"T/E/B, each 4 ell bands x 5 real signed L2 Gaunt coefficients; total d=60",
         "legacy_provenance":provenance(),
         "shrinkage_grid_predeclared":report,
         "disjoint_150train_150test":{"N_train":150,"N_test":150,
           "fitted_on":"even MC ID train only","N_exceed":int(np.count_nonzero(held_score>=q_obs)),
           "p_empirical_heldout":float(p_hold),
           "observed_score":float(q_obs),"heldout_score_median":float(np.median(held_score)),
           "proper_extrapolation_limit":"same FFP10 signal+noise pipeline but not independent CMB releases"},
         "noise_signal_mask_bias":bias,
         "R95_original_diagonal_60D_rank":float(old["rank_p"]),
         "zero_mean_is_NOT_assumed_on_masked_sky":True,
         "all_999_raw_SHA_independently_checked":False,
         "gaussian_theory_of_masked_statistic_assumed":False,
         "source_conditional_significance_only":True,
         "full_Wigner9j_mask_coupling_inverted":False,
         "Bianchi_family_attribution":None,
         "physical_Pi":None,"physical_GF":None,
         "elapsed_s":perf_counter()-t0}
def main():
 if OUT.exists():raise RuntimeError("create-only")
 j=compute()
 OUT.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"L2_full_cov_rank_lambda02":j["shrinkage_grid_predeclared"]["0.2"]["rank"],
    "split_holdout":j["disjoint_150train_150test"],
    "R95_original":j["R95_original_diagonal_60D_rank"],
    "bias":j["noise_signal_mask_bias"],"time_s":j["elapsed_s"]}))
if __name__=="__main__":main()
