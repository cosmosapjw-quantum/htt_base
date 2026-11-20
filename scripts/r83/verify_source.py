"""R83 C7 exact original H03 4x9 and full cross source covariance; L02/L03 pilot.

No calibration of CMB null, true cosmographic H(z,n), or cross-source PV.
"""
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from htt.obsstat import p2p3_fast as fast

ROOT=Path("docs/research_program/observational_publication_20261015")
H03=ROOT/"H03_20261016/src"
P=ROOT/"R83_PRE_DAG_NODES31_40_20261120"
SOURCE=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
ORIG=ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json"
L02=ROOT/"CONTINUATION_20261018/L02_EXECUTION_20261018/results/L02_ACTUAL_STATISTICS.json"
L03=ROOT/"CONTINUATION_20261018/L03_EXECUTION_20261018/results/L02_ON_EIGHT_PAIR_PILOT.json"

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()

def maxdiff(a,b):
 x=np.asarray(a,float);y=np.asarray(b,float)
 return float(np.max(abs(x-y)))

def main():
 assert sha(SOURCE)=="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
 sys.path.insert(0,str(H03.resolve()))
 import h03_tomography as H
 src=H.source(SOURCE)
 dist=H.proxy_distance(src.mu)
 sig=H.working_sigma(dist,src.e_mu)
 X=H.velocity_design(dist,src.n)
 y=H.C_KM_S*src.z
 W=np.column_stack([H.window(src.z,sig,c) for c in H.CENTERS])
 benchmark=fast.four_window_working_gls(X,y,W,sig,native_lib=None)
 lib=fast._certified_native()
 native=fast.four_window_working_gls(X,y,W,sig,native_lib=lib,threads=4)
 stored=json.loads(ORIG.read_text())
 old=np.array([row["theta9"] for row in stored["monopole_dipole_STF2_windows"]])
 C=np.array(stored["joint_covariance_36x36"])
 assert maxdiff(benchmark["theta"],old)<1e-8
 assert maxdiff(benchmark["joint_cov"],C)<1e-9
 assert maxdiff(native["theta"],old)<1e-8
 assert maxdiff(native["joint_cov"],C)<1e-9
 np.testing.assert_allclose(benchmark["F"],native["F"],rtol=2e-12,atol=1e-7)
 assert np.linalg.eigvalsh(C)[0]>0
 offdiag=benchmark["joint_cov"][:9,9:18]
 assert np.linalg.norm(offdiag)>0
 h01=[]
 for j,item in enumerate(stored["monopole_dipole_STF2_windows"]):
  w=W[:,j]
  h=float(np.sum(w*dist*y)/np.sum(w*dist**2))
  assert abs(h-item["H01_monopole_only_formula"])<1e-9
  h01.append(h)
 # Source descriptors only. These products do NOT define one matched source
 # likelihood and cannot be used to compute Planck physical anomaly p-values.
 p2=fast.historical_planck_science_status()
 l02=json.loads(L02.read_text())
 l03=json.loads(L03.read_text())
 assert p2["L02_fields"]==25 and p2["L02_same_sky_pairs"]==24
 assert p2["L03_pilot_pair_ids"]==8
 grouped=defaultdict(dict)
 for row in l03["rows"]:
  grouped[str(row["simulation_id"])][row["variant"]]=row
 assert len(grouped)==8
 within_source=[]
 for key,variant in sorted(grouped.items(),key=lambda z:int(z[0])):
  sig_only=variant["signal_only"]["fields"]
  sum_one=variant["sum_noise_1.00"]["fields"]
  pair={"pilot_pair_ID":key}
  for field in ("T","E","B"):
   pair[field+"_C2_processing_difference_microK2"]=float(sum_one[field]["C2_microK2"]-sig_only[field]["C2_microK2"])
  within_source.append(pair)
 # For L02 signed T/E and axial B, check actual exception/source:
 B_even=[row for row in l02["field_rows"] if row["field"]=="B" and
         isinstance(row["SO3_signed"]["chirality"],(float,int)) and
         row["SO3_signed"]["chirality"]<0]
 assert len(B_even)>=2
 assert all(row["SO3_signed"]["chirality"]==row["O3_summaries"]["chirality"] for row in B_even)
 output={
  "schema":"htt.r83.c7_original_CF4_H03_and_Planck_L02_L03_source_replay/1",
  "actual_input_sha256":{str(p):sha(p) for p in (SOURCE,ORIG,L02,L03)},
  "H03_original_selected_count":len(src.ids),
  "H03_original_source_C_km_per_s":H.C_KM_S,
  "H03_original_4x9_theta_max_abs_difference_numpy":maxdiff(benchmark["theta"],old),
  "H03_original_4x9_theta_max_abs_difference_cpp":maxdiff(native["theta"],old),
  "H03_original_36x36_cov_max_abs_difference_numpy":maxdiff(benchmark["joint_cov"],C),
  "H03_original_36x36_cov_max_abs_difference_cpp":maxdiff(native["joint_cov"],C),
  "H03_full_36x36_working_C_min_eigen":float(np.linalg.eigvalsh(C)[0]),
  "H03_offdiagonal_window_covariance_norm":float(np.linalg.norm(offdiag)),
  "H01_source_window_monopole_replay_km_per_s_per_Mpc":h01,
  "H03_working_normal_condition_max":max(benchmark["condition_normal"]),
  "source_H02_method_PV_selection_C":"UNAVAILABLE",
  "Planck_L02_field_row_count":len(l02["field_rows"]),
  "Planck_L02_same_sky_pair_count":len(l02["same_product_cross_fields"]),
  "Planck_B_axial_O3_even_negative_chirality_source_rows":len(B_even),
  "Planck_L03_pilot_independent_pair_ID_count":len(grouped),
  "Planck_L03_pilot_variant_rows":len(l03["rows"]),
  "Planck_L03_within_pair_processing_control":within_source,
  "Planck_L03_full_qualified_matched_null":False,
  "Planck_L04_real_p_value":None,
  "S06_and_L06_manuscript_ready":False,
  "R78_science_next_ID":p2["R78_science_next_ID"],
  "scientific_limit":"verified source working statistics, not independent CMB skies, physical H(z,n), calibrated PV, nor p-value"}
 P.mkdir(parents=True,exist_ok=True)
 (P/"C7_REAL_SOURCE.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"n":len(src.ids),"theta_error":output["H03_original_4x9_theta_max_abs_difference_cpp"],
  "cov_error":output["H03_original_36x36_cov_max_abs_difference_cpp"],
  "offdiag_norm":output["H03_offdiagonal_window_covariance_norm"],
  "pilot_IDs":len(grouped),"signed_B_chirality":len(B_even)}))
if __name__=="__main__":main()
