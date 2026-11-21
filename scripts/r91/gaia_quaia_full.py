"""R91: actual full 692154-row Quaia/Gaia join VSH source-weighting stress test.

Reuses the R89 634233 qualified astrometric subset, R90 exact official
Quaia G<20 selection pixel qualification and R69 16D E1/B1/E2/B2
tangent templates. Contrasts:
  unweighted inverse-noise fit;
  historical R89 selection-multiplied fit (w=s; NOT inverse propensity);
  inverse-relative-selection WLS with floors 0.20 and 0.35.
For each, 48 HEALPix nside2 leave-one-region-out jackknife, preserving
within-source pmra/pmdec correlation. No physically independent quasar/scan
null, cosmological shear or vorticity claim.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import healpy as hp
import numpy as np
from scripts.r69.gaia_e2_b2 import templates
from htt.obsstat import pre_dag_fast

ROOT=Path(__file__).resolve().parents[2]
JOIN=Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz")
QUAL=ROOT/"docs/research_program/observational_publication_20261015/R90_SOLVERFREE_BIANCHI_ATTRIBUTION_20261121/QUAIA_COORDINATE_QUALIFICATION.json"
R89=ROOT/"docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G03_GAIA/SOLVER_FREE_RESEARCH_RESULT.json"
MODES=("inverse_noise","multiply_selection_s","ipw_floor_0p20","ipw_floor_0p35")
SLICES={"E1":slice(0,3),"B1":slice(3,6),"E2":slice(6,11),"B2":slice(11,16)}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for blk in iter(lambda:f.read(1<<20),b""):h.update(blk)
 return h.hexdigest()

def fit_numpy(F,s,patchF,patchS,counts):
 beta=np.linalg.solve(F,s)
 cov=np.linalg.inv(F)
 active=np.flatnonzero(counts>100)
 leave=[]
 for k in active:
  leave.append(np.linalg.solve(F-patchF[k],s-patchS[k]))
 leave=np.asarray(leave)
 loocent=leave.mean(axis=0)
 Cjk=(len(active)-1)/len(active) * np.einsum("na,nb->ab",leave-loocent,leave-loocent)
 return {"n_sky_patches":int(len(active)),
         "coefs_microasyr":(beta*1000).tolist(),
         "formal_std_microasyr":(np.sqrt(np.diag(cov))*1000).tolist(),
         "jackknife_std_microasyr":(np.sqrt(np.maximum(0,np.diag(Cjk)))*1000).tolist(),
         "mode_amplitudes_microasyr":{k:float(1000*np.linalg.norm(beta[v])) for k,v in SLICES.items()},
         "jackknife_E2_B2_cov":(Cjk[6:16,6:16]*1e6).tolist(),
         "F_condition":float(np.linalg.cond(F)),
         "sampling_unit":"48 large nside2 sky patches; quasar AGN correlated source null NOT calibrated"}

def compute(chunk=60000):
 prior=json.loads(QUAL.read_text())
 if prior["matching_ra_dec_to_preexisting_pixel_fraction"]!=1 or prior["G20.0_join_selection_max_abs_error"]>1e-10:
  raise RuntimeError("R90 G20 source-coordinate contract not qualified")
 prior_r89=json.loads(R89.read_text())["part_b_population_and_quaia_tomography"]["quaia_4bin_z_tomography"]
 with np.load(JOIN,allow_pickle=False) as z:
  data={name:np.asarray(z[name]).copy() for name in (
    "ra","dec","redshift_quaia","gaia_pmra","gaia_pmdec",
    "gaia_pmra_error","gaia_pmdec_error","gaia_pmra_pmdec_corr",
    "gaia_ruwe","gaia_astrometric_params_solved","selection_relative")}
 ra=data["ra"];dec=data["dec"];zq=data["redshift_quaia"]
 yy=np.column_stack([data["gaia_pmra"],data["gaia_pmdec"]])
 e1=data["gaia_pmra_error"];e2=data["gaia_pmdec_error"];rho=data["gaia_pmra_pmdec_corr"]
 srel=data["selection_relative"]
 valid=(np.isfinite(ra)&np.isfinite(dec)&np.isfinite(zq)
       &np.isfinite(yy).all(axis=1)&np.isfinite(e1)&np.isfinite(e2)&np.isfinite(rho)
       &(e1>0)&(e2>0)&(abs(rho)<.999)&
       (data["gaia_ruwe"]<1.4)&(data["gaia_astrometric_params_solved"]==31)&
       (abs(yy[:,0])<100)&(abs(yy[:,1])<100)&
       (srel>0))
 idx=np.flatnonzero(valid)
 assert len(idx)==prior_r89["n_clean"]==634233,(len(idx),prior_r89["n_clean"])
 sets={m:{"F":np.zeros((16,16)),"score":np.zeros(16),
          "patchF":np.zeros((48,16,16)),"patchS":np.zeros((48,16))} for m in MODES}
 n_patch=np.zeros(48,dtype=int)
 for begin in range(0,len(idx),chunk):
  ii=idx[begin:begin+chunk]
  rr=np.deg2rad(ra[ii]);dd=np.deg2rad(dec[ii])
  _,B=templates(rr,dd)
  yz=yy[ii];se=srel[ii]
  patch=hp.ang2pix(2,np.pi/2-dd,rr)
  vals={"inverse_noise":np.ones(len(ii)),
        "multiply_selection_s":se,
        "ipw_floor_0p20":1/np.maximum(se,.20),
        "ipw_floor_0p35":1/np.maximum(se,.35)}
  for p in np.unique(patch):
   m=(patch==p)
   n_patch[p]+=int(np.sum(m))
   bp,yp=B[m],yz[m]
   for mode in MODES:
    ww=vals[mode][m]
    dsd=1/np.sqrt(ww)
    F,score,_=pre_dag_fast.accumulate_gaia(bp,yp,e1[ii][m]*dsd,e2[ii][m]*dsd,rho[ii][m],threads=1)
    obj=sets[mode]
    obj["F"]+=F;obj["score"]+=score
    obj["patchF"][p]+=F;obj["patchS"][p]+=score
 summary={}
 for name,item in sets.items():
  summary[name]=fit_numpy(item["F"],item["score"],item["patchF"],item["patchS"],n_patch)
 ref=np.asarray(summary["inverse_noise"]["coefs_microasyr"])
 for mode in MODES:
  arr=np.asarray(summary[mode]["coefs_microasyr"])
  summary[mode]["delta_vs_inverse_noise_mode_norm_microasyr"]={
      k:float(np.linalg.norm(arr[sl]-ref[sl])) for k,sl in SLICES.items()}
 return {"schema":"htt.r91.gaia_quaia_full_source_selection_weight_sensitivity/1",
         "origin_source_join_sha256":sha(JOIN),
         "origin_qualified_G20_selection_sha256":prior["official_file_shas"]["20.0"],
         "historical_R89_sha256":sha(R89),
         "source_total":int(len(ra)),"n_clean_full_source":len(idx),
         "same_quaia_G20_source_selection_exact":True,
         "n_active_jackknife_patches":int(np.count_nonzero(n_patch>100)),
         "nside_patch":2,"patch_counts_min_max":[int(np.min(n_patch[n_patch>0])),int(np.max(n_patch))],
         "source_weighting_models":{
             "inverse_noise":"usual Gaussian astrometric covariance inverse",
             "multiply_selection_s":"R89 historical selection_weighted: weight ~s, NOT inverse propensity",
             "ipw_floor_0p20":"estimated s relative from official Quaia, weight 1/max(s,0.20), not official null",
             "ipw_floor_0p35":"stability against selection-floor clipping"},
         "fits":summary,
         "strong_claims":{"physical_pi":None,"physical_gf":None,"source_corrected_cosmic_shear":False,
                          "publication_significance":False,
                          "full_catalog_used_not_partial":True}}
