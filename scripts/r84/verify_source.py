"""R84 C7 actual source R65/R74 + B01 Lie + H03 working source replay.

Physical same-frame observer/global transfer and qualified null remain unavailable.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

from scripts.r84.bench_baseline import source,axes,CARRIER,R74
from htt.obsstat import p4_bianchi_fast as fast

ROOT=Path("docs/research_program/observational_publication_20261015")
P=ROOT/"R84_PRE_DAG_NODES41_50_20261120"
B01=ROOT/"READY_20261016/B01_BIANCHI_ATLAS_REGISTRY.json"
R75=ROOT/"R75_P5_LIE_TILT_FIVEVIEW_20261119/RESULTS.json"
H03=ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json"
R83=ROOT/"R83_PRE_DAG_NODES31_40_20261120/C7_REAL_SOURCE.json"


def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()


def main():
 n,counts,groups,k,v,original=source()
 assert sha(CARRIER)==original["source_hashes"]["R65_original_pixel_carrier"]
 old=fast.prepare_ring_source(n,groups,counts,v,k)
 cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
 a=np.array([np.cos(cmb.dec.rad)*np.cos(cmb.ra.rad),
             np.cos(cmb.dec.rad)*np.sin(cmb.ra.rad),
             np.sin(cmb.dec.rad)])
 ax=np.vstack([a,axes(96)])
 fast_source=fast.batch_ring_occ(n,ax,old)
 native=fast.last_p4_receipt()
 baseline=fast.batch_ring_occ(n,ax,old,native_lib=None)
 errF=float(np.max(abs(fast_source["F"]-baseline["F"])))
 errgrad=float(np.max(abs(fast_source["gradient"]-baseline["gradient"])))
 assert errF<2e-12 and errgrad<2e-11
 exact=[]
 for b in range(3):
  ref=original["actual_R65_masked_F_response"]["source_geometry_and_exact_ring_z_null"][f"bin_{b+1}"]
  obj={"flux_bin":b+1,"source_selected_N":ref["source_selected_total"],
       "source_F_R74":ref["F_ring_predicted_at_beta0"],
       "replayed_CMB_axis_F":float(fast_source["F"][0,b]),
       "replayed_CMB_axis_dF_dbeta":fast_source["gradient"][0,b].tolist(),
       "R74_original_gradient":ref["F_ring_kinematic_score_gradient"]}
  assert abs(obj["replayed_CMB_axis_F"]-obj["source_F_R74"])<2e-13
  np.testing.assert_allclose(obj["replayed_CMB_axis_dF_dbeta"],obj["R74_original_gradient"],
                             atol=2e-12,rtol=0)
  exact.append(obj)
 # Original full unqualified source flux means all-axis gradient sums to zero.
 np.testing.assert_allclose(old["weight"].sum(axis=0),np.ones(3),atol=2e-13,rtol=0)
 np.testing.assert_allclose(old["score"].sum(axis=0),np.zeros((3,3)),atol=3e-13,rtol=0)
 atlas=fast.validate_bianchi_registry()
 assert atlas["canonical_count"]==11
 assert atlas["exceptional_VI_minus_1_over_9"]["source_specific_rank"]==2
 assert not atlas["exceptional_VI_minus_1_over_9"]["distinct_twelfth_type"]
 historical=fast.historical_41_50_status()
 assert historical["next_actual_science_ID"]=="SQ-CF4"
 for name in ("H04","H05","H06","V04","V05","V06"):
  assert historical["science_nodes"][name]=="pending"
 for name in ("V01","V02","V03","B01"):
  assert historical["science_nodes"][name]=="completed_scoped"
 h03=json.loads(H03.read_text())
 cov=np.array(h03["joint_covariance_36x36"],float)
 assert cov.shape==(36,36)
 source_eig=np.linalg.eigvalsh(cov)
 assert source_eig[0]>0
 assert np.linalg.norm(cov[:9,9:18])>.1
 if R83.is_file():
  p3=json.loads(R83.read_text())
  assert p3["H03_original_selected_count"]==35970
  assert p3["H03_original_36x36_cov_max_abs_difference_cpp"]<1e-9
 # Normalization of a null local/global column must not create rank.
 local=np.eye(6)[:,:2];global_cols=np.column_stack([local[:,0],np.eye(6)[:,4]])
 test=fast.source_conditional_local_global_rank(local,global_cols,np.eye(6))
 assert test["rank_local"]==2 and test["rank_increment_global"]==1
 assert test["physical_Pi"] is None
 out={
  "schema":"htt.r84.c7_original_NVSS_threeband_and_Bianchi_source/1",
  "input_sha256":{str(p):sha(p) for p in (CARRIER,R74,B01,R75,H03)},
  "source_NVSS_pixels":len(n),"source_NVSS_rings":old["ring_count"],
  "source_NVSS_flux_bin_totals":[int(t.sum()) for t in counts],
  "source_stable_weight_threeband_mass":old["weight"].sum(axis=0).tolist(),
  "source_fullsky_conditional_score_sums":old["score"].sum(axis=0).tolist(),
  "physical_p_value":None,
  "CMB_axis_replayed_R74_three_flux_bins":exact,
  "multi_axes":len(ax),
  "source_weighted_F_ranges":[float(np.min(fast_source["F"])),float(np.max(fast_source["F"]))],
  "source_score_gradient_maxabs":float(np.max(abs(fast_source["gradient"]))),
  "native_reference_F_maxabs":errF,
  "native_reference_score_maxabs":errgrad,
  "backend_receipt":native,
  "B01_canonical_Lie_types":atlas,
  "source_H03_C36_working_min_eigen":float(source_eig[0]),
  "source_H03_working_offdiagonal_Frob":float(np.linalg.norm(cov[:9,9:18])),
  "H04_complete_correlated_PV_method_selection_C":None,
  "V04_rank_example_explicitly_synthetic":test,
  "source_physics_H04_V01_06_B01_statuses":historical,
  "science_claim":"R84 implementation/source-conditional math only; NOT actual local/global physical tilt, global-matter source response, independent null, or Bianchi family inference"}
 P.mkdir(parents=True,exist_ok=True)
 (P/"C7_REAL_SOURCE.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"pixels":len(n),"rings":old["ring_count"],
    "native":native["used"],"F_error":errF,"score_error":errgrad,
    "11_Bianchi":atlas["canonical_count"],
    "Bianchi_VI_m1_9_rank":atlas["exceptional_VI_minus_1_over_9"]["source_specific_rank"],
    "H03_C_min_eig":float(source_eig[0])},ensure_ascii=False))
if __name__=="__main__":main()
