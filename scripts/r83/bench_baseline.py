"""R83 C1: original H03 CF4 4-window QR and L02/L03 source baseline.

Accurately records source-conditioned algorithm time; does not qualify L03/L04
Planck physical null or promote S06/H02 to science completion.
"""
import hashlib,json,platform,resource,sys,time
from pathlib import Path
import numpy as np

ROOT=Path("docs/research_program/observational_publication_20261015")
SRC=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
H03=ROOT/"H03_20261016/src"
L02=ROOT/"CONTINUATION_20261018/L02_EXECUTION_20261018/results/L02_ACTUAL_STATISTICS.json"
L03=ROOT/"CONTINUATION_20261018/L03_EXECUTION_20261018/results/L02_ON_EIGHT_PAIR_PILOT.json"
R78=ROOT/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
OUT=ROOT/"R83_PRE_DAG_NODES31_40_20261120/C1_BASELINE.json"
SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()

def bench(fn,reps=3):
 fn()
 runs=[]
 for _ in range(reps):
  t=time.perf_counter()
  fn()
  runs.append(time.perf_counter()-t)
 return {"median_s":float(np.median(runs)),"min_s":float(min(runs)),"series_s":runs}

def main():
 assert sha(SRC)==SHA
 sys.path.insert(0,str(H03.resolve()))
 import h03_tomography as H
 source=H.source(SRC)
 dist=H.proxy_distance(source.mu)
 sigma=H.working_sigma(dist,source.e_mu)
 X=H.velocity_design(dist,source.n)
 y=H.C_KM_S*source.z
 W=np.column_stack([H.window(source.z,sigma,c) for c in H.CENTERS])
 def old_four_fit():
  return [H.fit(X,y,W[:,j],influence=False) for j in range(4)]
 def old_joint():
  vals=[H.fit(X,y,W[:,j],influence=True) for j in range(4)]
  A=np.vstack([x["A"] for x in vals])
  return H.joint_covariance(A,sigma)
 old=bench(old_four_fit)
 full=bench(old_joint,2)
 vals=old_four_fit()
 c0=old_joint()[0]
 archived=json.loads((ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json").read_text())
 for j,item in enumerate(archived["monopole_dipole_STF2_windows"]):
  np.testing.assert_allclose(vals[j]["theta"],item["theta9"],atol=2e-9,rtol=2e-11)
 np.testing.assert_allclose(c0,archived["joint_covariance_36x36"],atol=1e-9,rtol=5e-11)
 l02=json.loads(L02.read_text())
 l03=json.loads(L03.read_text())
 assert len(l02["field_rows"])==25 and len(l02["same_product_cross_fields"])==24
 assert len(l03["independent_pair_ids"])==8 and len(l03["rows"])==40
 assert len({(x["simulation_id"],x["variant"]) for x in l03["rows"]})==40
 ids=sorted({x["simulation_id"] for x in l03["rows"]})
 assert ids==list(l03["independent_pair_ids"])
 assert all(x["sky_id"]=="ONE_PHYSICAL_PLANCK_SKY" for x in l02["field_rows"])
 d=json.loads(R78.read_text())
 assert d["next_action_id"]=="SQ-CF4"
 target=['S06',*(f"L{i:02d}" for i in range(1,7)),*(f"H{i:02d}" for i in range(1,4))]
 assert all(k in {x["id"] for x in d["nodes"]} for k in target)
 report={
  "schema":"htt.r83.c1_actual_cf4_H03_and_planck_L02_L03_baseline/1",
  "source_sha256":{str(p):sha(p) for p in (SRC,L02,L03,R78)},
  "start_repo_head":"36b049dd7c4bd8b540b9337d2b11a0ed22e2611c",
  "target_ordinal_ids":{str(i):x for i,x in enumerate(target,31)},
  "CF4_selected_group_count":len(source.z),
  "CF4_source_4x9_model":"cz = d(H + D.n + n.Q.n), four Gaussian z windows center .025/.04/.06/.08 width .012; diagonal working sigma, not physical H(z,n)",
  "H03_QR_four_fit_no_influence":old,
  "H03_QR_four_fit_and_joint_36cov":full,
  "H03_9D_cond_max":max(x["cond"] for x in vals),
  "H03_archive_4x9_and_joint_cov_replayed":True,
  "L02_field_rows":len(l02["field_rows"]),"L02_cross_product_pair_rows":len(l02["same_product_cross_fields"]),
  "L02_one_physical_sky":True,
  "L03_pilot_unique_pair_ID_count":len(ids),
  "L03_pilot_variants_per_pair":len(l03["rows"])//len(ids),
  "L03_pilot_physical_null_qualified":False,
  "memory_maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  "numpy":np.__version__,"python":platform.python_version(),
  "scientific_source_ceiling":"SOURCE_CONDITIONAL_NUMERICAL_BASELINE; L03_MATCHED_NULL_HOLD, H02_CORRELATED_PV_UNKNOWN"}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"n":len(source.z),"QR_4fit_median_s":old["median_s"],
  "QR_4fit_jointcov_median_s":full["median_s"],"condition":report["H03_9D_cond_max"],
  "Planck_field_rows":25,"L03_pilot_pairs":8,"rssMiB":report["memory_maxrss_kib"]/1024}))
if __name__=="__main__":main()
