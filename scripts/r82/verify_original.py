"""R82 C7 real 2048 coupled original source numerical and E2-X03 evidence.

Four overlapping redshift windows share one draw ID; no physics sector
completion, no independent 9-Planck-map likelihood, no P1 publication claim.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from htt.obsstat import p1_fast

ROOT=Path("docs/research_program/observational_publication_20261015")
P1=ROOT/"CONTINUATION_20261018/P1/results"
DATA=P1/"paired_functional_arrays.npz"
SUMMARY=P1/"FUNCTIONAL_SENSITIVITY_RESULT.json"
OUT=ROOT/"R82_PRE_DAG_NODES21_30_20261120/C7_SOURCE_REPLAY.json"
PIN="cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27"

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for z in iter(lambda:f.read(1<<20),b""):h.update(z)
 return h.hexdigest()

def rel(x,y):
 a=np.asarray(x,float);b=np.asarray(y,float)
 return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),1e-200))

def main():
 if sha(DATA)!=PIN:raise ValueError("original P1 joint source file bytes changed")
 with np.load(DATA,allow_pickle=False) as z:
  q=z["q_app"].copy()
  w=z["weights"].copy()
  ids=z["sample_id"].copy()
  raws=z["draws"].copy()
  anchors=z["anchors"].copy()
  floors=z["floors"].copy()
  q_phys=z["physical_Q"].copy()
  f_phys=z["physical_F"].copy()
  gf_phys=z["physical_G_F"].copy()
  reason_Q=z["physical_Q_reason"].copy()
  reason_FGF=z["physical_F_G_reason"].copy()
 assert raws.shape==(2048,4,9) and q.shape==(2048,4)
 assert len(set(ids))==2048 and abs(w.sum()-1)<1e-14
 assert np.isnan(q_phys).all() and np.isnan(f_phys).all() and np.isnan(gf_phys).all()
 assert set(reason_Q)=={"unmeasured_defined"} and set(reason_FGF)=={"domain_uncertified"}
 old=json.loads(SUMMARY.read_text())
 assert old["sample_count"]==2048
 ts=np.asarray([x["threshold"] for x in old["strict_exceedance"]])
 lib_cpp=p1_fast._certified_native("tails")
 lib_fortran=p1_fast._certified_native("floor")
 base=p1_fast.joint_tail_bounds(q,w,ts,sample_ids=ids,native_lib=None)
 got=p1_fast.joint_tail_bounds(q,w,ts,sample_ids=ids,native_lib=lib_cpp,threads=8)
 assert rel(got["lower"],base["lower"])<2e-14
 assert rel(got["upper"],base["upper"])<2e-14
 assert np.allclose(got["lower"],got["upper"],atol=2e-14,rtol=0)
 for i,line in enumerate(old["strict_exceedance"]):
  np.testing.assert_allclose(got["lower"][i,:4],line["per_window"],atol=2e-14,rtol=0)
  assert abs(got["lower"][i,4]-line["any_window"])<2e-14
  assert abs(got["lower"][i,5]-line["all_windows"])<2e-14
 sampled_t=float(ts[np.flatnonzero(np.isclose(ts,.05))[0]])
 t005=got["lower"][np.flatnonzero(np.isclose(ts,.05))[0]].tolist()
 assert abs(t005[4]-1235/2048)<1e-15 and t005[5]==0
 # original archived sensitivity anchor grid / 1 exceedance
 an=np.asarray(old["anchor_sensitivity"]["anchors"])
 asens=p1_fast.joint_tail_bounds(q,w,an,sample_ids=ids,native_lib=lib_cpp,threads=8)
 np.testing.assert_allclose(asens["lower"][:,:4],
  np.asarray(old["anchor_sensitivity"]["strict_mass_score_gt_1"]),atol=2e-14,rtol=0)
 # Original S03 apparent floor ratio source and ties.
 floor_list=[x["floor"] for x in old["floor_depth_sensitivity"]]
 orig_floor=p1_fast.floor_depth_grid(q,w,[.05],floor_list,native_lib=None)
 fast_floor=p1_fast.floor_depth_grid(q,w,[.05],floor_list,native_lib=lib_fortran,threads=8)
 for key in ("strict_above_one","tie_one","mean_ratio"):
  np.testing.assert_allclose(fast_floor[key],orig_floor[key],atol=2e-11,rtol=2e-11)
 for j,archived in enumerate(old["floor_depth_sensitivity"]):
  np.testing.assert_allclose(fast_floor["strict_above_one"][0,j],archived["strict_mass_above_1"],atol=2e-14,rtol=0)
  np.testing.assert_allclose(fast_floor["tie_one"][0,j],archived["tie_mass_at_1"],atol=2e-14,rtol=0)
 # Explicit complete missing physical source, no reweighting.
 phys=np.column_stack([q_phys,q_phys,q_phys,q_phys])
 rQ=np.ones((2048,4),np.int8)
 rF=np.full((2048,4),2,np.int8)
 blocked_Q=p1_fast.joint_tail_bounds(phys,w,ts,missing_codes=rQ,sample_ids=ids,native_lib=lib_cpp,threads=8)
 blocked_F=p1_fast.joint_tail_bounds(phys,w,ts,missing_codes=rF,sample_ids=ids,native_lib=None)
 for b in (blocked_Q,blocked_F):
  np.testing.assert_allclose(b["lower"],0,atol=1e-14,rtol=0)
  np.testing.assert_allclose(b["upper"],1,atol=1e-14,rtol=0)
  assert b["physical_Pi"] is None
  np.testing.assert_allclose(b["unknown_mass_per_window"],1,atol=1e-14,rtol=0)
 assert blocked_Q["missing_unmeasured_mass_per_window"]==[1,1,1,1]
 assert blocked_F["missing_uncertified_mass_per_window"]==[1,1,1,1]
 evidence=p1_fast.historical_evidence_21_30()
 assert evidence["E2_planck_same_sky_maps"]==9
 assert evidence["X03_new_observational_null"]=="NOT_REGISTERED_FOR_NEW_OBSERVATIONAL_NULL"
 # Frozen record hash and direct source changes are not introduced.
 out={
  "schema":"htt.r82.c7_source_2048_P1_and_planck_E2_novelties/1",
  "source_sha256":{str(DATA):sha(DATA),str(SUMMARY):sha(SUMMARY)},
  "historical_sha_by_node_id":evidence["source_sha256"],
  "original_joint_draw_shape":list(raws.shape),
  "coherent_joint_weight_total":float(w.sum()),
  "sample_ID_SHA256":hashlib.sha256("\n".join(map(str,ids)).encode()).hexdigest(),
  "native_CPP_strict_tail_rel_error":rel(got["lower"],base["lower"]),
  "native_Fortran_floor_mean_rel_error":rel(fast_floor["mean_ratio"],orig_floor["mean_ratio"]),
  "original_strict_event_at_0p05_4window_any_all":t005,
  "original_archived_anchor_grid_replayed":True,
  "original_archived_floor_grid_tie_count_replayed":True,
  "real_physical_Q_lower_upper":[0,1],"real_physical_F_lower_upper":[0,1],
  "real_physical_GF_lower_upper":[0,1],
  "physical_unknown_mass":1.0,
  "E2_and_X01_X02_X03_evidence":evidence,
  "scientific_source_status":"2048 JOINT WORKING CONDITIONAL SOURCE; true same-congruence physical posterior and source C are NOT IDENTIFIED",
  "preserved_science_R78_status":True,
  "physical_joint_likelihood_null_calibrated":False
 }
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"n":len(q),"tail_native_error":out["native_CPP_strict_tail_rel_error"],
  "floor_native_error":out["native_Fortran_floor_mean_rel_error"],
  "strict_t_0p05":t005,"physical_unknown_mass":out["physical_unknown_mass"],
  "planck_same_sky_maps":evidence["E2_planck_same_sky_maps"]}))
if __name__=="__main__":main()
