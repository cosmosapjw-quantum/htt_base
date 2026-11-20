"""R84 C1 original R65/R74 real NVSS source ring-softmax/gradient baseline.

No new kinematic source fitting or CMB/local frame identification.
Four 41-50 blocks H04..H06, V01..V06, B01 have original R78 states.
"""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

from htt.obsstat.pre_dag_fast import ring_softmax_occupancy

BASE=Path("docs/research_program/observational_publication_20261015")
SRC=BASE/"R65_DIPOLE_ANOMALY_20261117/RESULTS"
R74=BASE/"R74_P4_SOURCE_SCORE_FIVEVIEW_20261119/RESULTS.json"
ORIG=SRC/"NVSS_OBSERVED_RESULT.json"
SUMMARY=SRC/"INTERPRETATION_SUMMARY.json"
CARRIER=SRC/"NVSS_CONDITIONAL_CARRIERS.npz"
R78=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
OUT=BASE/"R84_PRE_DAG_NODES41_50_20261120/C1_BASELINE.json"

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def axes(m):
 i=np.arange(m,dtype=float)
 z=1-2*(i+.5)/m
 phi=(i*np.pi*(3-np.sqrt(5)))%(2*np.pi)
 return np.column_stack([np.sqrt(1-z*z)*np.cos(phi),
                         np.sqrt(1-z*z)*np.sin(phi),z])

def source():
 with np.load(CARRIER,allow_pickle=False) as z:
  n=z["base64_pixel_vectors"].copy()
  counts=z["base64_counts"].copy()
  _,groups=np.unique(z["base64_groups"],return_inverse=True)
 assert n.shape==(33000,3) and counts.shape==(3,33000)
 assert groups.max()+1==185
 old=json.loads(ORIG.read_text())
 summary=json.loads(SUMMARY.read_text())
 original=json.loads(R74.read_text())
 ks=np.asarray(summary["nvss_tables"][0]["peak_response_diagnostics"]["0.75"]["response"])
 v=np.array([q["estimate"][:2] for q in old["models"]["base64_dipole"]["independent_fits"]])
 return n,counts,groups,ks,v,original

def ring_reference(n,c,group,k,v,axis):
 totals=np.bincount(group,weights=c,minlength=185)
 return ring_softmax_occupancy(n[:,:2]@v,group,n@axis>0,totals,directions=n,k=float(k))

def test_original():
 n,c,g,ks,v,old=source()
 cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
 p=np.array([np.cos(cmb.dec.rad)*np.cos(cmb.ra.rad),
             np.cos(cmb.dec.rad)*np.sin(cmb.ra.rad),np.sin(cmb.dec.rad)])
 matches={}
 for b in range(3):
  obs=ring_reference(n,c[b],g,ks[b],v[b],p)
  ref=old["actual_R65_masked_F_response"]["source_geometry_and_exact_ring_z_null"][f"bin_{b+1}"]
  errF=abs(obs["F"]-ref["F_ring_predicted_at_beta0"])
  errgrad=float(np.max(abs(obs["dF_dbeta"]-ref["F_ring_kinematic_score_gradient"])))
  assert errF<2e-13 and errgrad<2e-12
  matches[f"bin_{b+1}"]={"source_selected_count":int(c[b].sum()),
    "CMB_axis_F":obs["F"],"source_ring_dF_dbeta":obs["dF_dbeta"].tolist(),
    "F_error":errF,"gradient_max_error":errgrad}
 ax=axes(32)
 start=time.perf_counter()
 for axis in ax:
  for b in range(3):
   ring_reference(n,c[b],g,ks[b],v[b],axis)
 slow=time.perf_counter()-start
 results={
  "schema":"htt.r84.c1_actual_R65_R74_NVSS_conditional_source_baseline/1",
  "source_sha256":{str(p):sha(p) for p in (CARRIER,ORIG,SUMMARY,R74,R78)},
  "original_33k_source_pixels":len(n),"source_conditional_rings":185,
  "flux_bin_count":3,"benchmark_direction_axes":len(ax),
  "reference_original_source_32axis_3bin_seconds":slow,
  "CMB_axis_matching_R74":matches,
  "ring_conditioned_source_count_k":ks.tolist(),
  "source_relative_to_frame":"R65 ICRS sourceward direction; CMB axis transformed from Galactic",
  "physical_Pi":"UNAVAILABLE",
  "real_physical_local_or_global_beta":"NOT_IDENTIFIED",
  "rank_claim":"R74 conditional source score only; no cosmic null",
  "backend_reference":"htt.obsstat.pre_dag_fast.ring_softmax_occupancy",
  "R78_science_DAG_next":json.loads(R78.read_text())["next_action_id"],
  "numpy_version":np.__version__}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"n":len(n),"rings":185,"base32axis_3bin_seconds":slow,
                   "R74_errors":matches},ensure_ascii=False))
if __name__=="__main__":test_original()
