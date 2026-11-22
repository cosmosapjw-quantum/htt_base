"""R96 source-typed local-agent dispatch for exact original 60-node R78 DAG.

Read-only to all original R78/R95/R94 state. Creates new R96 preflight output
with every original node's latest scoped result and its specific real code and
data/model/native dependency; does not promote science approval.
"""
from pathlib import Path
from hashlib import sha256
import json
from collections import Counter
ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE=ROOT/"docs/research_program/observational_publication_20261015"
OUT=BASE/"R96_THREE_THEORY_LOOPS_20261122/R96_LOCAL_AGENT_60_NODE_DISPATCH.json"
R78=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R95=BASE/"R95_LOCAL_EXECUTION_20261122/R95_60_NODE_EVIDENCE.json"
SHA_R78="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
EXTERNAL={"SQ-NATIVE","B02","B03","B04","B05"}
TASKS={
 "P3":{"id":"R96-A","scripts":["scripts/r96/cf4_covariance_bridge.py"],
       "evidence":["CF4_COVARIANCE_RECONCILIATION.json","THEORY_A_CF4_R1_R10_KO.md"],
       "priority":"SQ-CF4 FIRST",
       "next":"compare R36 four-method vs R95 seven-channel source models; seek raw upstream preintercalibration zero-point posterior, heldout and selection covariance"},
 "P2":{"id":"R96-B","scripts":["scripts/r96/legacy_biposh_recovered.py","scripts/r96/cmb_crossfit_null.py"],
       "evidence":["CMB_MASK_BIPO_CROSSVALIDATED_NULL.json","THEORY_B_CMB_R1_R10_KO.md"],
       "priority":"masked-source-matched MC",
       "next":"mask+beam anisotropic injection recovery with source matched MC, separate Commander release null and 300/999 noise interpretation"},
 "P5":{"id":"R96-C","scripts":["scripts/r96/spin2_mblock_extension.py"],
       "evidence":["SPIN2_MBLOCK_HIERARCHY.json","THEORY_C_BIANCHI_R1_R10_KO.md"],
       "priority":"physical all-m photon hierarchy",
       "next":"derive source-locked Bianchi curved m-mixing from R49 connection, independent spin/Thomson boundary, full all-m T/E/B and posterior"},
 "P1":{"id":"R95-P1","scripts":["scripts/r95/p1_five_view_analysis.py"],"evidence":[],
       "priority":"partial-ID source","next":"source-matched Pi and GF physical null under actual measure; preserve None otherwise"},
 "P4":{"id":"R95-P4","scripts":["scripts/r95/radio_p4_analysis.py"],"evidence":[],
       "priority":"survey cov","next":"selection and LSS cross-catalog covariance on all 5 radio surveys"},
 "P6":{"id":"R95-P6","scripts":["scripts/r95/gaia_p6_analysis.py"],"evidence":[],
       "priority":"systematic null","next":"source-matched Gaia AGN and scanning-law null with normal-frame source transport"},
 "COMMON":{"id":"R95-COMMON","scripts":["scripts/r95/build_r95_master_ledger.py"],"evidence":[],
       "priority":"source provenance","next":"original R78 source authority and all source ownership strict"},
 "CROSS":{"id":"R95-PHY","scripts":["scripts/r95/cross_phy_synthesis.py"],"evidence":[],
       "priority":"seven cross-physics","next":"source-qualified finite-z optical/matched covariances across probes, Pi/GF unresolved"},
}
def sha(p):return sha256(p.read_bytes()).hexdigest()
def build():
 if sha(R78)!=SHA_R78:raise RuntimeError("original science DAG changed")
 dag=json.loads(R78.read_text())
 old=json.loads(R95.read_text())
 if len(dag["nodes"])!=60 or len(dag["edges"])!=129 or dag["next_action_id"]!="SQ-CF4":
  raise RuntimeError("invalid R78")
 old_map={x["id"]:x for x in old["nodes"]}
 if set(old_map)!={n["id"] for n in dag["nodes"]}:raise RuntimeError("node identity drift")
 status=Counter()
 routes=[]
 basedir=OUT.parent
 for n in dag["nodes"]:
  r=old_map[n["id"]];p=n["paper"]
  own=TASKS.get(p,TASKS["COMMON"])
  for rel in own["scripts"]:
   if not (ROOT/rel).exists():raise RuntimeError("missing real executable code "+rel)
  b=[x for x in own["evidence"] if (basedir/x).exists()]
  is_ext=n["id"] in EXTERNAL
  routes.append({
   "id":n["id"],"paper":p,
   "R78_science_state_original":n["state"],
   "R95_execution_status_original":r["r95_execution_status"],
   "R95_original_pub_accepted":r["publication_science_accepted"],
   "r96_workstream":own["id"],"r96_script":own["scripts"],
   "r96_new_result_files":b,
   "classification":("EXTERNAL_FULL_M_BIANCHI_PENDING" if is_ext else r["blocker_bucket"]),
   "actual_next_work":own["next"],
   "original_science_state_promoted":False,
   "new_physical_publication_claim":False
  })
  status[r["r95_execution_status"]]+=1
 return {"schema":"htt.r96.three_theory_60node_execution_preflight/1",
  "base_R78_SHA256":SHA_R78,"base_R95_SHA256":sha(R95),
  "base_R95_HEAD":"a87df07da328ba6d704e7cf0d554081f52d39213",
  "n_original_nodes":60,"n_original_edges":129,"next_science_id":"SQ-CF4",
  "original_R95_status_counts":dict(status),
  "three_R96_theory_loops_complete":True,
  "new_science_A":["CF4 35970 groups, 3x5 covariance grid, R36 vs R95 model inequivalence"],
  "new_science_B":["fullcov 60D signed BiPoSH 300 MC, 150/150 heldout, legacy fsky correction"],
  "new_science_C":["spin2 recurrence and m=-2..2 sparse T/E/B to L60; NOT general curved full-all-m"],
  "PHY_nodes":[f"PHY-{i:02d}" for i in range(1,8)],
  "native_external_boltzmann_gate_ids":sorted(EXTERNAL),
  "all_original_science_60_pass":False,
  "source_data_missing_calibration_and_commander_null":True,
  "private_legacy_corpus_preserved":True,
  "routes":routes}
def main():
 if OUT.exists():raise FileExistsError("create-only")
 j=build()
 OUT.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"n":len(j["routes"]),"status":j["original_R95_status_counts"],"new_workstreams":3}))
if __name__=="__main__":main()
