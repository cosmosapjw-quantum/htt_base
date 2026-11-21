"""R91 second theoretical/coding loop: data census, real reusable inference and lanes.

Creates ONLY R91 new research artifacts, --write is create-only, --check
recomputes all R91 outputs and verifies content. No native Bianchi Boltzmann
solver, no PR4 bulk download, no auto-start of R78 60-node production DAG,
no alteration of R78/R89/R90 or external data. Private full file census stays
in local ~/Downloads and is never copied to public Git.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,os,sys
from pathlib import Path
from scripts.r91 import cf4_legacy_pv_requalification as cf4, pliklite_baseline as plik, planck_cl_morphology as cl, gaia_quaia_full as gaia

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
R91=BASE/"R91_SOLVERFREE_SECOND_CYCLE_20261121"
R78=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R90=BASE/"R90_SOLVERFREE_BIANCHI_ATTRIBUTION_20261121"
R89=BASE/"R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs"
CENSUS=Path.home()/"Downloads/htt_r91_local_inventory/DEEP_SCAN_20261121.summary.json"
EXPECTED_R78="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
TRANSFER={"SQ-NATIVE","B02","B03","B04","B05"}
PHY={f"PHY-{i:02d}" for i in range(1,8)}
PAPERS=("P1","P2","P3","P4","P5","P6")
GROUPS=("G01_COMMON","G02_CF4","G03_GAIA","G04_RADIO_FRAME","G05_PLANCK","G06_P1","G07_BIANCHI","G08_OPTICAL_PHY")
R91_SOURCES={
  "P2":["PLANCK_C2_MORPHOLOGY.json","PLIKLITE_BASELINE.json"],
  "P3":["CF4_EXISTING_PV_REQUALIFIED.json"],
  "P6":["GAIA_QUAIA_FULL_SELECTION.json"],
  "P5":["R90_REFERENCE_ATTRIBUTION.json"],
  "P4":["R89_REFERENCE_RADIO.json"],
  "P1":["R89_REFERENCE_P1.json"],
}
R1_TO_R10=[
 ("R1","Fixed target and R78 60-node/129-edge science authority; SQ-CF4 source-first re-entry","R78 immutable SHA"),
 ("R2","Reused exact R47/R49/R62/R89/R90 and primary Plik-lite/Cosmicflows/Bianchi bibliography","SOURCE_REUSE, manuscript"),
 ("R3","Separated actual data from conditional geometric/kinematic/Planck high-l spectral calibration","CLAIM_SCOPE"),
 ("R4","Three competing routes: local EH98 partial PV, published Plik scalar power, Gaia selection reweight","CF4+PLIK+GAIA"),
 ("R5","Derived quadratic C2 shape-equivalence counterexample and source-conditioned Gaussian calibration GLS","PLANCK_C2, PLIK"),
 ("R6","Checked PV Fourier Gram, G07 conditional constraints, χ shape invariant and selection source chart","CF4+Planck+Gaia"),
 ("R7","Executed same-source R36 PV 36D, full 613-bin Plik-lite, real 634233 Gaia clean QSO and 48 patches","OUTPUTS"),
 ("R8","Admitted conditional likelihood/variance/selection sensitivity; withheld physical Bianchi family identification","CLAIM_SCOPE"),
 ("R9","Mapped P1-P6 + PHY01-07 to executable code and unresolved native-transfer and model/source blockers","WORK_OVERLAY"),
 ("R10","Stored reproducible source IDs, private census and new result/continuation","HANDOFF"),
]
C1_TO_C10=[
 ("C1","Locked git branch/HEAD and historical R78 SHA","BASELINE"),
 ("C2","Mapped R36/R27 original covariance, Cobaya PlanckPlikLite, R69/R89 Quaia VSH code","SOURCE_MODULES"),
 ("C3","Designed whitened GLS/Fortran covariance, profile amplitude, C_l morphology controls and 48-patch JK","FORMULAS"),
 ("C4","Batched 613 bins/634k rows; read-only existing raw source; 60-node overlay separates transfer","TOPOLOGY"),
 ("C5","Implemented deep metadata census, CF4/Plik/Planck/Gaia real numerical features","IMPLEMENTED"),
 ("C6","Ran scoped new unit/integration regressions and historical R49/R78/R89/R90","TEST_RECEIPT"),
 ("C7","Checked source-conditional vs physical covariance, Boltzmann absent, astrophysical null missing","PHYSICS"),
 ("C8","Ran exact identities, numerical rank/conditioning and full dataset/patch coverage","NUMERIC"),
 ("C9","One bounded self-audit; native subagent invocation unavailable in current Chat host","SELF_REVIEW_NOT_INDEPENDENT"),
 ("C10","Write closed-scope artifacts and validated selective research branch publication","HANDOFF_AND_GIT"),
]

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def baseline():
 if sha(R78)!=EXPECTED_R78:raise RuntimeError("R78 immutable source mismatch")
 dag=json.loads(R78.read_text())
 if len(dag["nodes"])!=60 or len(dag["edges"])!=129 or dag["next_action_id"]!="SQ-CF4":
  raise RuntimeError("R78 source graph/next ID mismatch")
 prior={}
 for group in GROUPS:
  r=json.loads((R89/group/"RESULT.json").read_text())
  for id,state in r["node_verdicts"].items():
   if id in prior:raise RuntimeError("R89 duplicate node "+id)
   prior[id]=state
 if set(prior)!={n["id"] for n in dag["nodes"]}:
  raise RuntimeError("R89 source base not exactly original 60")
 return dag,prior

def census():
 j=json.loads(CENSUS.read_text())
 if not j["complete"] or j["metadata_errors"]!=0 or j["file_records"]<=0:
  raise RuntimeError("private metadata scan incomplete")
 roots={}
 for name,obj in j["roots"].items():
  roots[name]={"files":obj["files"],"directories":obj["directories"],"size_bytes_sum":obj["total_bytes"],
               "top_extensions":obj["top_extensions"][:10],
               "candidate_tag_counts":obj["science_metadata_hits"]}
 # Note: do NOT publish user private filenames, full metadata ledger, or all
 # individual source path/mtime from Downloads.
 return {"schema":"htt.r91.sanitized_private_two_root_census/1","census_private":str(CENSUS),
         "scope":"metadata all files in /home/cosmosapjw/Downloads and /mnt/extdrive/workdir, no symlinks followed",
         "files_scanned":j["file_records"],"files_tagged_candidate":j["candidate_count"],
         "metadata_errors":0,"roots":roots,
         "privacy_note":"full path index and private candidate registry retained only in user-local Downloads, not Git"}

def discover():
 data={
  "legacy_CF4_R36_partial_PV":{
    "p":cf4.SOURCE/"PV_FACTORS.npz","function":"scoped published R36 CF4 EH98 Gaussian low-k conditional covariance"},
  "legacy_CF4_R27_support_quotient":{
    "p":cf4.R27/"FACTOR.npz","function":"serialized finite seven-channel difference factor only, not upstream posterior"},
  "Planck_2018_pliklite_data":{
    "p":plik.DATA/"plik_lite_v22.dataset","function":"published nuisance-marginalized Plik-lite 215+199+199 Gaussian likelihood"},
  "Planck_2018_lowE_native":{
    "p":Path("/mnt/extdrive/workdir/cobaya_packages/data/planck_2018_lowE_native/prob_table.txt"),
    "function":"candidate lowE TT/EE scalar release; NOT executed and NOT morphology atlas"},
  "Planck_PR3_published_bestfit":{
    "p":plik.THEORY,"function":"published theory vector l2..l2508; no CAMB run this stage"},
  "R49_tilted_ClassA_B_evolution":{
    "p":ROOT/"htt/bass/background/general_tilted_evolution.py",
    "function":"existing non-native general tilted Bianchi background Einstein constraints/ODE"},
  "R62_source_STF_carrier":{
    "p":BASE/"R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION/log__J2_coefficients.json",
    "function":"real 15D signed tensor estimate, fixed Gaussian covariance, seven nuisance evidence"},
  "PR4_NPIPE_masks_preexisting":{
    "p":Path("/mnt/extdrive/workdir/raw/planck_npipe_pr4/misc/mask_PR4_Lollipop_ns16.fits"),
    "function":"existing smaller PR4 ancillary mask; NO full PR4 data download"},
  "CLASS40GHz_instrument_response_not_Bianchi_solver":{
    "p":Path("/mnt/extdrive/workdir/raw/class_dr1/class_dr1_40GHz_VEB_transfer_matrix_lmax383_hits.hdf5"),
    "function":"CLASS telescope VEB instrument transfer, NOT AniCLASS/Bianchi Einstein-Boltzmann hierarchy"},
  "CAMB_external_env_binary_discovered":{
    "p":Path("/mnt/extdrive/workdir/external_fusion_round3_20260722_envs/firecrown/lib/python3.11/site-packages/camb/camblib.so"),
    "function":"installed isotropic CAMB library candidate; import/runtime NOT verified"},
  "Cobaya_Plik_native_reference_code":{
    "p":Path("/mnt/extdrive/workdir/external_fusion_round3_20260722_envs/inference/lib/python3.12/site-packages/cobaya/likelihoods/base_classes/planck_pliklite.py"),
    "function":"published Cobaya PlanckPlikLite source equations used in R91 independent local parser"},
 }
 rows=[]
 for name,item in data.items():
  p=item["p"]
  if not p.exists():
   rows.append({"name":name,"status":"MISSING_AT_SCAN","role":item["function"]});continue
  size=p.stat().st_size
  # Inputs actually used in computations provide SHA and full source binding.
  hashit=size<60_000_000
  rows.append({"name":name,"status":"EXISTS_CONTENT_VERIFIED" if hashit else "EXISTS_METADATA_ONLY",
               "path":str(p),"bytes":size,
               "sha256":sha(p) if hashit else None,
               "role":item["function"]})
 return {"schema":"htt.r91.new_prior_observational_data_discovery/1",
         "rows":rows,"downloaded_bytes_this_run":0,
         "no_full_PR4_requested":True,"no_extdrive_writes":True,
         "notes":"Existing Planck Plik-lite is a high-l C_l-only likelihood; CLASS-DR1 instrumental VEB response is not a Bianchi family transfer"}

def r90_refs():
 r={
  "P1":R89/"G06_P1/SOLVER_FREE_RESEARCH_RESULT.json",
  "P4":R89/"G04_RADIO_FRAME/SOLVER_FREE_RESEARCH_RESULT.json",
  "P5":R90/"ATTRIBUTION_RESULT.json",
  "PHY":R90/"CROSS_PHY_RESULT.json"
 }
 return {k:{"path":str(v),"sha256":sha(v)} for k,v in r.items()}

def overlay(dag, prior):
 bypaper=collections.defaultdict(list)
 for n in dag["nodes"]:bypaper[n["paper"]].append(n["id"])
 overlay=[]
 for n in dag["nodes"]:
  id=n["id"]
  cat="EXTERNAL_NATIVE_BIANCHI_TRANSFER" if id in TRANSFER else (
      "SEVEN_PHY_SOURCE_CONDITIONAL" if id in PHY else "SOLVER_FREE_OR_MODEL_SOURCE_DEPENDENT")
  phase2=[]
  if id in ("SQ-CF4","H02","H03","H04"):phase2.append("CF4_EXISTING_PV_REQUALIFIED.json")
  if id in ("L01","L02","L03","L04"):phase2.extend(("PLIKLITE_BASELINE.json","PLANCK_C2_MORPHOLOGY.json"))
  if id in ("K02","K03","K04","SQ-GAIA"):phase2.append("GAIA_QUAIA_FULL_SELECTION.json")
  if n["paper"]=="P1":phase2.append("R90_REUSED_PROVENANCE.json#P1")
  if n["paper"]=="P4":phase2.append("R90_REUSED_PROVENANCE.json#P4")
  if id in ("B01","B02","B03","B04","B05"):phase2.append("R90_REUSED_PROVENANCE.json#P5")
  if id in PHY:phase2.append("R90_REUSED_PROVENANCE.json#PHY")
  overlay.append({
     "id":id,"paper":n["paper"],"original_R78_state":n["state"],
     "original_R89_execution_verdict":prior[id],
     "r91_scope_lane":cat,"r91_new_evidence_refs":phase2,
     "original_R78_science_state_mutated":False,
     "publication_acceptance_promoted":False,
  })
 if len(set(x["id"] for x in overlay))!=60:raise RuntimeError("overlay node count drift")
 return {"schema":"htt.r91.second_cycle_60_node_solverfree_analysis_overlay/1",
         "science_SSOT":"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json",
         "science_SSOT_SHA256":EXPECTED_R78,
         "science_Next_ID":"SQ-CF4",
         "historical_60_nodes_129_hard_edges_frozen":True,
         "historical_60_science_complete":False,
         "original_R89_status_totals":dict(collections.Counter(prior.values())),
         "papers":{k:v for k,v in bypaper.items() if k in PAPERS},
         "cross_seven_PHY":sorted(PHY),
         "solver_dependent_original_ids":sorted(TRANSFER),
         "source_or_model_unqualified_still_open":True,
         "source_runner_actual":"scripts/r91/run_second_cycle.py --check",
         "items":overlay}

def blocker_receipt():
 old=json.loads((R90/"BLOCKER_LEDGER.json").read_text())
 return {
  "schema":"htt.r91.blocker_reconciliation_not_false_pass/1",
  "inherited_R90_open":old["unresolved_non_solver_blocks"],
  "remaining_native_transfer_bundles":old["external_transfer_blocks"],
  "SQ_CF4":{
    "progress":"R36 108x108 finite EH98 low-k source-correlated model recovered; exact R89 36D replay; R27 seven-channel finite support model recovered",
    "still_missing":["outside k=0.005..0.05 h/Mpc and non-linear PV sources","pre-intercalibration zero point MCMC posterior","measured/validated selection covariance","source-matched independent heldout"],
    "original_science_gate":"BLOCKED_INPUT"},
  "P2":{
    "progress":"source-native Planck 2018 Plik-lite 613-bin likelihood computed with fixed published theory and one analytic nuisance-profile; exact same-C2 non-SO3 shape counterexample",
    "still_missing":["release-matched Commander low-l T/E/B null", "all-m native Bianchi transfer for family posterior"],
    "original_L03_gate":"BLOCKED_INPUT"},
  "P6":{
    "progress":"complete matched Quaia 692154 and clean 634233 source VSH comparison with 48-patch JK and inverse relative selection sensitivity",
    "still_missing":["source-specific AGN/scan correlated physical null","normal-frame/source transfer"],
    "original_K03_gate":"BLOCKED_INPUT_OR_DEPENDENCY"},
  "P1_P4_P5_PHY":{
    "progress":"R89/R90 full-scope source-conditional results reused with hashes, not blindly rerun",
    "still_missing":["physical law/null and independent cross-probe source covariance",
                     "native transfer in separate lane for B02-B05"],
    "claim":"model-equivalence class, not particular family detection"},
  "permission":"additional public source downloads only to local Downloads; none required this cycle",
 }

def stage_evidence():
 return {
    "schema":"htt.r91.twenty_stages_second_cycle_actual_work/1",
    "theory":[{"id":id,"task":task,"evidence":source,
               "status":"SCOPED_EXECUTED_OR_REUSED"} for id,task,source in R1_TO_R10],
    "coding":[{"id":id,"task":task,"evidence":source,
               "status":"SELF_REVIEW_ONLY" if id=="C9" else "SCOPED_IMPLEMENTED_OR_VERIFIED"}
              for id,task,source in C1_TO_C10],
    "native_subagent":"NOT_RUN_HOST_DELEGATION_UNAVAILABLE",
    "independent_external_math_review":"PARTIAL_WOLFRAM_EXACT_Q2_EIGENSPECTRA_ONLY",
    "six_paper_original_42_science_acceptance":"UNCHANGED",
    "full_60_science_completed":False,
 }

def build():
 dag, prior=baseline()
 r_cf4=cf4.analyze(full_factor=True)
 r_plik=plik.compute(A_planck=1.0)
 r_cl=cl.analyze(64)
 r_gaia=gaia.compute(chunk=60000)
 cs=census()
 ds=discover()
 ov=overlay(dag,prior)
 blockers=blocker_receipt()
 stages=stage_evidence()
 refs=r90_refs()
 results={
  "FILE_SCAN_SUMMARY.json":cs,
  "SOURCE_DISCOVERY.json":ds,
  "CF4_EXISTING_PV_REQUALIFIED.json":r_cf4,
  "PLIKLITE_BASELINE.json":r_plik,
  "PLANCK_C2_MORPHOLOGY.json":r_cl,
  "GAIA_QUAIA_FULL_SELECTION.json":r_gaia,
  "R90_REUSED_PROVENANCE.json":refs,
  "WORK_DAG_OVERLAY.json":ov,
  "BLOCKER_RECONCILIATION.json":blockers,
  "R1_C1_TO_R10_C10_EVIDENCE.json":stages,
 }
 return {k:json.dumps(v,indent=2,ensure_ascii=False)+"\n" for k,v in results.items()}

def main():
 ap=argparse.ArgumentParser()
 g=ap.add_mutually_exclusive_group(required=True)
 g.add_argument("--write",action="store_true")
 g.add_argument("--check",action="store_true")
 args=ap.parse_args()
 try:
  files=build()
  if args.write:
   if any(R91.iterdir()):raise RuntimeError("R91 create-only artifact directory must be empty")
   for name,txt in files.items():
    with (R91/name).open("x",encoding="utf-8") as f:f.write(txt)
  else:
   for name,txt in files.items():
    if (R91/name).read_bytes()!=txt.encode("utf-8"):
     raise RuntimeError("R91 file missing or content mismatch: "+name)
  print(json.dumps({"schema":"htt.r91.second_cycle_runner_result/1",
                    "mode":"write" if args.write else "check",
                    "outputs":len(files),"file_census":json.loads(files["FILE_SCAN_SUMMARY.json"])["files_scanned"],
                    "science_original_nodes":60,"science_original_edges":129,
                    "physically_accepted_60_of_60":False,
                    "new_source_analyses":["CF4_R36_PV","PlikLite613","Planck_quadrupole_shape","Gaia_634233"]},ensure_ascii=False))
  return 0
 except (KeyError,FileNotFoundError,ValueError,RuntimeError,OSError) as e:
  print("R91_FAIL_CLOSED:"+repr(e),file=sys.stderr);return 2
if __name__=="__main__":
 raise SystemExit(main())
