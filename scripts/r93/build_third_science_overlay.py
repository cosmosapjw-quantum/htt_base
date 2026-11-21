"""R93 third bounded theory+coding science cycle: source-grounded overlay.

R93 runs *actual* (i) 999 SMICA signal/300 noise conditional T a_lm+BipoSH,
(ii) CF4 35970 source boost-kinematics redshift identity against legacy code,
(iii) BASS/HTT 12-strata/60-state Codazzi algebra bridge in BASS owner env,
(iv) full-resolution one-pair T/E/B and NSIDE64 resolution probes,
(v) refreshed complete legacy archive/source dedup indexing.

This aggregator records all 60 original node outcomes and six papers, seven
cross PHY but NEVER changes R78 authority or asserts 60 science PASS.
"""
import hashlib,json
from pathlib import Path
from collections import Counter
ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE=ROOT/"docs/research_program/observational_publication_20261015"
OUT=BASE/"R93_THIRD_SCIENCE_LOOP_20261121"
R78=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R91=BASE/"R91_SOLVERFREE_SECOND_CYCLE_20261121/WORK_DAG_OVERLAY.json"
R92=BASE/"R92_BASS_HIGH_ELL_THIRD_PREP_20261121/HIGH_ELL_L2_GAUNT_CONSTRUCTION.json"
R90=BASE/"R90_SOLVERFREE_BIANCHI_ATTRIBUTION_20261121/CROSS_PHY_RESULT.json"
NEW=[
"SMICA_999_NSIDE64_BIPOSH_RESULT.json",
"NSIDE2048_VS_N64_ALM_TRANSFER_QA.json",
"SMICA_FULLRES_EB_FIRSTPAIR_PILOT.json",
"LEGACY_BIPOSH_INVALID_ESTIMAND.json",
"CF4_LEGACY_TILT_DOPPLER_COMPARISON.json",
"BASS_HTT_CODAZZI_SAME_STATE_RESULT.json",
"LEGACY_SECOND_DEEP_SCAN.json",
]
SHA_R78="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
SHA_R92_GAUNT=hashlib.sha256(R92.read_bytes()).hexdigest()
GROUPS={
 "P1":{"reuse":"R91/P1 five-view partial identification and 2048 coupled draws",
       "new":[],"science_status":"REUSED_NOT_PROMOTED"},
 "P2":{"reuse":"R89/91 Planck PR3 maps / Plik-lite",
       "new":NEW[:4],"science_status":"NEW_SOURCE_CONDITIONAL_FFP10_T_ALM_BIPOSH_AND_1PAIRED_FULLRES_EB"},
 "P3":{"reuse":"R91 source-conditioned R36 CF4 PV/R27 calibration quotient",
       "new":[NEW[4]],"science_status":"NEW_FULL_35970_CF4_LEGACY_SR_DOPPLER_RELATIVE_SOURCE_TEST"},
 "P4":{"reuse":"R89/91 NVSS/RACS/SPICE/SUMSS/LoTSS source-conditioned radio",
       "new":[],"science_status":"REUSED_NOT_PROMOTED"},
 "P5":{"reuse":"R49/R90 general tilted Lie algebra 84 canonical witness",
       "new":[NEW[5]],"science_status":"NEW_BASS_HTT_12_STRATA_60_CASE_GEOMETRIC_SOURCE_CONVENTION_EQUIVALENCE"},
 "P6":{"reuse":"R91 all 634233 Gaia-Quaia clean source fits and 48-patch covariance",
       "new":[],"science_status":"REUSED_NOT_PROMOTED"},
}
PHY={f"PHY-{i:02d}" for i in range(1,8)}
TRANSFER={"SQ-NATIVE","B02","B03","B04","B05"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(2**18),b""):h.update(b)
 return h.hexdigest()
def run():
 if sha(R78)!=SHA_R78:raise RuntimeError("R78 changed")
 dag=json.loads(R78.read_text())
 old=json.loads(R91.read_text())
 if len(dag["nodes"])!=60 or len(dag["edges"])!=129 or dag["next_action_id"]!="SQ-CF4":
  raise RuntimeError("R78 original DAG semantics changed")
 old_map={r["id"]:r for r in old["items"]}
 if set(old_map)!={n["id"] for n in dag["nodes"]}:
  raise RuntimeError("R91 original node identity changed")
 report={}
 for file in NEW:
  f=OUT/file
  if not f.is_file():raise FileNotFoundError(f)
  report[file]={"sha256":sha(f),"size_bytes":f.stat().st_size}
 bim=json.loads((OUT/NEW[0]).read_text())
 lres=json.loads((OUT/NEW[6]).read_text())
 b=json.loads((OUT/NEW[5]).read_text())
 cf=json.loads((OUT/NEW[4]).read_text())
 eb=json.loads((OUT/NEW[2]).read_text())
 if bim["source_counts"]["cmb_ids"]!=999 or bim["source_counts"]["noise_ids"]!=300:
  raise RuntimeError("conditional MC not full verified 999")
 if cf["cf4_all_selected_groups"]!=35970 or b["test_count"]!=60:
  raise RuntimeError("R93 actual scientific scope incomplete")
 if eb["full_999_EB_done"]:
  raise RuntimeError("E/B pilot falsely promoted")
 if lres["physical_file_count"]<2913 or lres["zip_count"]!=24:
  raise RuntimeError("actual legacy repeat scan incomplete")
 entries=[]
 for n in dag["nodes"]:
  nid=n["id"]
  paper=n["paper"]
  previous=old_map[nid]
  newe=[]
  if paper in GROUPS:
   newe=list(GROUPS[paper]["new"])
  if nid=="SQ-CF4" and NEW[4] not in newe:
   newe.append(NEW[4])
  tag="EXTERNAL_NATIVE_BIANCHI_TRANSFER" if nid in TRANSFER else (
    "CONDITIONAL_CROSS_PHY_REUSED" if nid in PHY else
    "SOURCE_CONDITIONAL_SCIENCE_PARTIAL_OR_REUSED")
  entries.append({
    "id":nid,"paper":paper,"r78_scientific_state":n["state"],
    "r89_original_verdict":previous["original_R89_execution_verdict"],
    "r91_old_evidence":previous["r91_new_evidence_refs"],
    "r93_new_result_files":newe,
    "current_lane":tag,
    "physics_publication_pass_promoted":False,
    "original_R78_science_state_changed":False
  })
 return {
  "schema":"htt.r93.full_60_node_third_science_overlay/1",
  "r78_source_SHA256":SHA_R78,
  "r91_source_SHA256":sha(R91),
  "r92_prior_gaunt_SHA256":SHA_R92_GAUNT,
  "frozen_original_nodes":60,"frozen_original_edges":129,
  "original_next_action_id":"SQ-CF4",
  "no_unconditional_science_60_pass":True,
  "new_actual_science_sources":report,
  "new_papers_scoped":GROUPS,"old_seven_PHY":sorted(PHY),
  "external_native_boltzmann_lane":sorted(TRANSFER),
  "r89_verdict_totals":dict(Counter(v["r89_original_verdict"] for v in entries)),
  "r93_science_coverage":{"actual_new_P2_T_NSID64_999":999,
   "actual_new_P3_CF4_redshift_source_groups":35970,
   "actual_new_P5_BASS_HTT_strata":12,
   "actual_new_P5_Codazzi_cases":60,
   "actual_new_EB_fullres_pilot_MC_pairs":1,
   "original_60_scientific_nodes_all_executed":False,
   "seven_cross_PHY_reused_with_original_status":True},
  "items":entries
 }
if __name__=="__main__":
 path=OUT/"WORK_DAG_60_EVIDENCE.json"
 if path.exists():raise RuntimeError("create-only")
 x=run()
 path.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"nodes":len(x["items"]),"old_verdicts":x["r89_verdict_totals"],
                   "new_paper_scope":{p:t["science_status"] for p,t in x["new_papers_scoped"].items()}}))
