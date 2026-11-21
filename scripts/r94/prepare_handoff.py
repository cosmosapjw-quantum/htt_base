"""R94 original R78 60-node science-program preflight and CPU/native execution map.

Reads the original historical R78 science DAG, R93 source-conditional overlay,
R94 accelerated kernel, actual 3-file full-res pilot, real reused solver
bridge and all three deep-scanned source roots. Creates only a new R94
preparation receipt, never promotes R78 historical publication states.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
D=BASE/"R94_SIX_PAPER_ACCEL_HANDOFF_20261122"
R78=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R93=BASE/"R93_THIRD_SCIENCE_LOOP_20261121/WORK_DAG_60_EVIDENCE.json"
EXPECTED_SHA="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
OUT=D/"R94_PROGRAM_EXECUTION_MAP.json"
PAPER_ROUTES={
 "P1":{"owner":"G06_P1","code":["htt/obsstat/p1_fast.py","htt/obsstat/p1_lane.json"],"focus":"correct source-typed x,Q,Pi,F,GF, partial-ID and 2048 coupled draws"},
 "P2":{"owner":"G05_PLANCK","code":["scripts/r94/gaunt_fast.py","scripts/r94/gaunt_core.cpp","scripts/r94/stream_fullres.py","scripts/r94/solver_source_bridge.py"],
       "focus":"same estimator actual SMICA PR3 masked T/EB + 999/300 null; source-qualified physical Bianchi transfer separate"},
 "P3":{"owner":"G02_CF4","code":["htt/obsstat/cf4_p0b.py","htt/obsstat/phy_fast.py","scripts/r93/legacy_cf4_doppler.py"],
       "focus":"35,970 source selection, missing upstream MCMC, R36 finite low-k PV, independent heldout"},
 "P4":{"owner":"G04_RADIO_FRAME","code":["htt/obsstat/p4_bianchi_fast.py","scripts/r89/prepare_eight_groups.py"],
       "focus":"actual 5 radio surveys and selection/LSS matched null, local/global boost"},
 "P5":{"owner":"G07_BIANCHI","code":["htt/bass/background/general_tilted_evolution.py",
    "htt/bass/transport/general_bianchi_transfer.py","scripts/r94/solver_source_bridge.py"],
       "focus":"12 Bianchi Class A/B full EOS Einstein-Euler background and source-conditioned Sachs/Thomson, not native all-m"},
 "P6":{"owner":"G03_GAIA","code":["htt/obsstat/pre_dag_fast.py","scripts/r91/gaia_quaia_full.py"],
       "focus":"Gaia/Quaia/VLBA 634233 clean full QSO and 48-patch jackknife, frame/scan systematic null"},
}
OTHER_ROUTES={
 "COMMON":{"owner":"G01_COMMON","code":["scripts/r94/deep_reuse_index.py"],"focus":"provenance/source/node/conditional/transfer tags"},
 "QUALIFICATION":{"owner":"G08_OPTICAL_PHY","code":["scripts/r94/solver_source_bridge.py"],
  "focus":"7 cross PHY, Sachs/Jacobi/source matching, honest missing physics"}
}
NATIVE={"SQ-NATIVE","B02","B03","B04","B05"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(2**20),b""):h.update(b)
 return h.hexdigest()
def compose():
 if sha(R78)!=EXPECTED_SHA:raise RuntimeError("original R78 science authority changed")
 dag=json.loads(R78.read_text())
 old=json.loads(R93.read_text())
 if len(dag["nodes"])!=60 or len(dag["edges"])!=129 or dag["next_action_id"]!="SQ-CF4":
  raise RuntimeError("R78 structural drift")
 if len(old["items"])!=60:raise RuntimeError("R93 60-node source changed")
 before={x["id"]:x for x in old["items"]}
 if {n["id"] for n in dag["nodes"]}!=set(before):raise RuntimeError("node identities mismatch")
 for named in PAPER_ROUTES.values():
  for rel in named["code"]:
   if not (ROOT/rel).exists():raise RuntimeError("reusable code missing "+rel)
 for named in OTHER_ROUTES.values():
  for rel in named["code"]:
   if not (ROOT/rel).exists():raise RuntimeError("code missing "+rel)
 bench=json.loads((D/"GAUNT_CXX_SOURCE_BENCHMARK.json").read_text())
 sol=json.loads((D/"REUSED_SOLVER_CONDITIONAL_TRANSFER.json").read_text())
 pilot=json.loads((D/"FFP10_FULLRES_STREAM_PILOT.json").read_text())
 scan=json.loads((D/"SOURCE_REUSE_INDEX.json").read_text())
 rows=[]
 for n in dag["nodes"]:
  p=n["paper"]
  if p in PAPER_ROUTES:route=PAPER_ROUTES[p]
  elif n["id"].startswith("PHY-"):route=OTHER_ROUTES["QUALIFICATION"]
  else:route=OTHER_ROUTES["COMMON"]
  if n["id"] in NATIVE:
   scope="PHYSICAL_ALL_M_NATIVE_BIANCHI_TRANSFER_NOT_COMPLETED; CONDITIONAL_R49_EINSTEIN_EULER_REUSED"
  elif before[n["id"]]["r89_original_verdict"] in {"BLOCKED_INPUT","BLOCKED_DEPENDENCY"}:
   scope="SOURCE_CONDITIONAL_RUN_ALLOWED; OLD_PUBLICATION_BLOCKERS_REMAIN"
  else:
   scope="REUSED_SCOPED_OR_SOURCE_DIAGNOSTIC; NO_AUTO_PROMOTION"
  rows.append({
   "id":n["id"],"paper":p,
   "r78_science_state":n["state"],
   "r89_original_verdict":before[n["id"]]["r89_original_verdict"],
   "work_group":route["owner"],"code_paths":route["code"],
   "next_science_question":route["focus"],
   "r94_claim_scope":scope,
   "original_science_status_changed":False,
   "actual_r94_physical_science_acceptance":False
  })
 return {
  "schema":"htt.r94.local_agent_60_science_node_program_preflight/1",
  "R78_original_dag_SHA256":EXPECTED_SHA,"R93_previous_overlay_SHA256":sha(R93),
  "r78_nodes":60,"r78_hard_edges":129,"scientific_next_id":"SQ-CF4",
  "six_paper_routes":PAPER_ROUTES,"seven_PHY_nodes":[f"PHY-{x:02d}" for x in range(1,8)],
  "external_native_boltzmann_required_ids":sorted(NATIVE),
  "other_routes":OTHER_ROUTES,
  "r89_verdict_totals":dict(Counter(x["r89_original_verdict"] for x in rows)),
  "solver_progress":{
    "12_Bianchi_R49_Einstein_Euler_dynamic":sol["counts"]["dynamic_Einstein_Euler_families"],
    "12_Bianchi_geodesic_screen":sol["counts"]["exact_geodesic_family_count"],
    "6_near_FLRW_linearized":sol["counts"]["linearized_executed"],
    "BASS_exact_Thomson_energetic_error":sol["source"][0]["fractional_energy_error"],
    "REC_positive_clock":"RUN_WITH_CONSTRUCTED_ELECTRON_FRACTION",
    "REI_physical_CMB_source":"NOT_QUALIFIED_OWNER_ELECTRON_HISTORY",
    "native_all_m_EB_CMB_LSS":"NOT_IMPLEMENTATION_VERIFIED",
    "solver_source_bridge_sha256":sha(D/"REUSED_SOLVER_CONDITIONAL_TRANSFER.json")},
  "optimized_numeric_lane":{
    "Wigner_Gaunt_precompute_speedup_measured":bench["kernel_speedup_sympy_gaunt_generation"],
    "CXX_projection_speedup_measured":bench["kernel_speedup_R93_projection_Cxx17"],
    "LOO_speedup_measured":bench["kernel_speedup_R93_LOO_999"],
    "MC_999_300_rank_parity":bench["mc_rank_no_change"],
    "benchmark_receipt_sha256":sha(D/"GAUNT_CXX_SOURCE_BENCHMARK.json"),
    "backend_select":"g++ C++17/OpenMP only when source hashed and matching tests pass; otherwise NumPy"},
  "streaming_implementation":{
    "pilot_fullres_nside2048_pairs":pilot["source_case_count"],
    "pilot_cmb_ids":pilot["selected_cmb_ids"],
    "pilot_actual_raw_SHA_verified":pilot["raw_file_sha_actual"],
    "pilot_time_s":pilot["elapsed_wall_seconds"],
    "pilot_private_harmonics_SHA256":pilot["private_harmonic_sha256"],
    "requested_full_999_TEB":"DEFERRED_FOR_LOCAL_AGENT_FULL_LONG_RUN",
    "runtime_budget_from_pilot":"about 65s/3 ~22s per pair with actual SHA, 999 pairs order 6 hours if same sustained throughput",
    "RAM_source":"3-pair run peak RSS ~4.9 GB on 31 GiB RAM, 17 GiB currently available"},
  "reused_source_inventory":{
    "scan_physical_files":scan["all_physical_files"],
    "zip_members":scan["all_zip_member_records"],
    "curated_source_hashes":len(scan["curated_source_sha256"]),
    "private_fts":scan["private_local_index"]},
  "local_agent_native_subagent":"NOT_RUN_NATIVE_AGENT_CALL_TOOL_ABSENT",
  "R78_original_scientific_states_unchanged":True,
  "all_60_node_original_science_PASSED":False,
  "rows":rows,
 }
def main():
 if OUT.exists():raise RuntimeError("create-only R94 map")
 data=compose()
 OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"rows":len(data["rows"]),"groups":len(data["six_paper_routes"]),
   "solver_counts":data["solver_progress"],"r89_verdicts":data["r89_verdict_totals"]},ensure_ascii=False)[:1500])
if __name__=="__main__":main()
