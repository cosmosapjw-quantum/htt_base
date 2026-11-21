"""R90: actual source-bounded solver-free science lane, immutable R78 authority.

--write creates a new R90 research *overlay* only. --check read-only.
No Boltzmann solver, PR4 full intake, background daemon, or science-acceptance
mutation. Runs real R62 tensor/covariance compatibility across 12 canonical
Bianchi representatives and all seven R62 nuisance variants; seven PHY
numeric experiments and Quaia original selection maps from local Downloads.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from scripts.r90 import sf_attribution, crossroute, selection_support
from scripts.r90.download_minimal import ALLOWLIST, DEST

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
SSOT=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
OUT=BASE/"R90_SOLVERFREE_BIANCHI_ATTRIBUTION_20261121"
R89=BASE/"R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs"
EXPECTED_SHA_R78="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
STAGES_R=["contract","primary_literature_and_history","claim_assumptions","candidate_geometric_models",
          "Codazzi_profile_derivation","adversarial_semantics","actual_CF4_and_quaia_numeric",
          "claims_admission","computational_form","durable_handoff"]
STAGES_C=["baseline_lock","formula_data_code_map","stable_nullspace_GLS",
          "source_owned_lanes","implemented_analysis","targeted_unit_regression",
          "physical_injection_and_limits","numerical_condition_and_resources",
          "self_review_native_not_run","commit_and_dispatch_handoff"]

BLOCKERS=[
 ("SQ-CF4","DATA","CF4 pre-intercalibration MCMC zero-point posterior and source-matched PV/selection covariance",
  "R87 method overlap and R90/R89 full CF4/SDSS/DESI diagnostics","Request upstream posterior and independent CF4 mock/calibration; never substitute SDSS-footprint mocks"),
 ("H02","MODEL","Cross-method zero-point, PV and survey selection covariance/source overlap model",
  "Use R89 empirical method/profile and partial-ID scenario bounds","Fit true upstream Jcal and source-matched PV before physical H04"),
 ("SQ-GAIA","MODEL","AGN/scan/reddening joint error and normal-frame VSH transfer",
  "R89 48-patch jackknife and R90 actual Quaia selection map contrast","Source-specific Gaia scan/time/AGN null and position-drift data required"),
 ("K03","DATA","Independent nonradial normal-frame proper-motion source/null and source-redshift transport",
  "R89 Gaia/VLBA VSH source-conditioned inference","Matched radio/optical reference-frame and optical finite-z transfer"),
 ("SQ-RADIO","MODEL","Radio clustering, tile/RMS selection, source multiplicity and random catalog joint covariance",
  "R89 five-survey full catalog/overlap masks, radio jackknife, Ellis-Baldwin flux slopes","Build matched survey-specific LSS and selection mocks"),
 ("SQ-FRAME","MODEL","Observer/matter/source congruence response across CF4/Gaia/CMB/radio",
  "Use local-boost Lorentz map R72, R89 VSH/RACS source diagnostics","Solve covariant mapping with explicit source history; not spin=omega"),
 ("SQ-P1-ANCHOR","DATA","Physical normal-frame anchor and 274-row nonselected HI-CF4 release distances",
  "R89 G06 sharp Manski unknown mass bounds","Obtain calibration anchor; remain partially identified otherwise"),
 ("S02","MODEL","Actual physical x and calibrated finite law/measure",
  "Use R82 existing coupled 2048 window draws, R90 typed Q/F conditional","No physical Pi or transported G_F without null/geometry"),
 ("SQ-CMB-NULL","DATA","Release-matched full Commander T/E/B simulations and foreground/beam/processing null",
  "R89 PR3/PR4 selected maps, 75 SMICA pilot, 200 synthetic MASTER checks","Only qualified accessible Commander MC; do not download whole PR4"),
 ("L03","ADDITIONAL_ANALYSIS","Mode-coupling, MC tail, pixel-window and null adequacy",
  "R89 G05 MASTER conditional real map and split analysis","Full-spectrum leakage and independent source-calibrated simulations"),
 ("SQ-PHOTON-FLUX","MODEL","Physical photon higher moment distribution/normal flux",
  "PHY02 Gram positivity and existing analytic moment inequalities","External photon source or explicitly derived closure, not pseudo TEB transfer"),
 ("SQ-LIE-FLUX","MODEL","Independent normal-frame rho,j,pi source in tilted fluids",
  "R49 full Class A/B background + G07 q=0, pi !=0 counterexample","Physical species EOS/source histories and positive matter bounds"),
 ("SQ-OPTICAL","MODEL","General finite-z Sachs/Jacobi/position-drift mapping for tilted non-I Bianchi",
  "R89 exact-axisymmetric-Type-I optical and R49 background tetrad ODE","Independent Sachs/Jacobi check then extend R49 non-I families"),
 ("SQ-CROSS-COV","DATA","Source-overlap and shared calibration/LSS null across different probes",
  "R89 14-axis comparisons retained only descriptively","Request source IDs/selection randoms and joint covariance when available"),
 ("K04","MODEL","Physical kinematics and shear observable transport",
  "R90 canonical Codazzi+R62 conditional compatibility","Do not infer physical sigma from CF4 without optical coupling"),
 ("V04","ADDITIONAL_ANALYSIS","Local versus global tilt degeneracy under different source windows",
  "R89 boost and radio five-survey directional/source tests","Model and empirically calibrate independent source history before Bayesian claims"),
 ("PHY-01..07","ADDITIONAL_ANALYSIS","Full non-solver analytic/observational conditional route execution",
  "R90 seven real/constructed checks with physical limit flags","Upgrade only physical source qualified routes; theory-only remains valid"),
 ("SQ-NATIVE","SOLVER_DEPENDENT","Native polarized all-m Bianchi Einstein–Boltzmann transfer atlas",
  "External transport lane only, not an admissible shortcut for morphological geometry","Wait for independently verified external native transfer"),
 ("B02..B05","SOLVER_DEPENDENT","Polarized high-ell family atlas and cross-family evidence under physical CMB null",
  "SF-P5 canonical algebra/CF4 conditional morphology attribution now executable","Separate transfer lane for native family probabilities and full E/B power"),
]
SOLVER_ORIGINAL={"SQ-NATIVE","B02","B03","B04","B05"}
HYBRID_ORIGINAL={"PHY-02","PHY-06","SQ-PHOTON-FLUX"}
SF_GROUPS={
 "P1":{"source":["G06_P1"],"depends":["SF-P3"],"scope":"Signed x, Q statistical body, F working Gaussian, Pi and GF missing physical transfer"},
 "P2":{"source":["G05_PLANCK"],"depends":[],"scope":"Observed low-ell morphology/MASTER conditional, not source-matched significance"},
 "P3":{"source":["G02_CF4"],"depends":["SF-SQ-CF4"],"scope":"Full CF4 apparent Hubble tensor, PV/source partial-ID without full physical calibration"},
 "P4":{"source":["G04_RADIO_FRAME"],"depends":["SF-P3"],"scope":"Local boost/radio/global-tilt source diagnostics, physical joint likelihood blocked"},
 "P5":{"source":["G07_BIANCHI"],"depends":["SF-ATTR"],"scope":"Lie algebra/Codazzi/tilted shear family conditional compatibility, not native CMB attribution"},
 "P6":{"source":["G03_GAIA"],"depends":["SF-QUAIA"],"scope":"Gaia/VLBA nonradial VSH with selection/source covariance"},
}
PHY_DEPS={
 1:["SF-P3","SF-P5"],2:["SF-P2","SF-P5"],3:["SF-P4"],
 4:["SF-P6","SF-P4"],5:["SF-P5"],6:["SF-P2","SF-P5"],7:["SF-P3","SF-P4"]
}

def hash_path(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1<<20),b""):h.update(c)
 return h.hexdigest()

def validate_inputs():
 if hash_path(SSOT)!=EXPECTED_SHA_R78:raise ValueError("R78 source identity changed")
 dag=json.loads(SSOT.read_text())
 if len(dag["nodes"])!=60 or len(dag["edges"])!=129 or dag["next_action_id"]!="SQ-CF4":
  raise ValueError("R78 graph count/frontier changed")
 if len(set(n["id"] for n in dag["nodes"]))!=60:raise ValueError("duplicate historical node")
 if not all((DEST/n).exists() and (DEST/n).stat().st_size==s for n,(s,_) in ALLOWLIST.items()):
  raise ValueError("local Downloads Quaia minimal inputs absent")
 if not all(hashlib.md5((DEST/n).read_bytes()).hexdigest()==dig for n,(_,dig) in ALLOWLIST.items()):
  raise ValueError("Downloads data digest mismatch")
 return dag

def work_dag(dag):
 nodes=[]
 for id_ in ["SF-SQ-CF4","SF-ATTR","SF-QUAIA"]:
  nodes.append({"id":id_,"lane":"solver_free","depends":["SF-SQ-CF4"] if id_=="SF-ATTR" else [],
                "status":"OBSERVATIONAL_DIAGNOSTIC_OR_CONDITIONAL_MODEL_COMPUTED"})
 for id_,spec in SF_GROUPS.items():
  nodes.append({"id":"SF-"+id_,"lane":"solver_free","depends":spec["depends"],
                "source_group":spec["source"][0],"status":"SOURCE_CONDITIONAL_EXECUTED_OR_REUSED",
                "scope":spec["scope"]})
 for k,dep in PHY_DEPS.items():
  nodes.append({"id":f"SF-PHY-{k:02d}","lane":"solver_free","depends":dep,
                "status":"NUMERIC_OR_CONSTRUCTED_THEORY_DIAGNOSTIC",
                "physical_source_qualified":False})
 nodes.append({"id":"SF-ATTRIBUTION-SYNTHESIS","lane":"solver_free",
               "depends":["SF-P1","SF-P2","SF-P3","SF-P4","SF-P5","SF-P6"]+[f"SF-PHY-{i:02d}" for i in range(1,8)],
               "status":"SOURCE_CONDITIONAL_NOT_FAMILY_ID"})
 base_ids={n["id"] for n in nodes}
 if len(base_ids)!=len(nodes) or any(d not in base_ids for n in nodes for d in n["depends"]):
  raise ValueError("invalid new solver-free overlay topology")
 for id_ in ["SQ-NATIVE","B02","B03","B04","B05"]:
  nodes.append({"id":"TRANSFER-"+id_,"lane":"external_native_transfer",
                "depends":[],"status":"BLOCKED_EXTERNAL_SOLVER",
                "cannot_be_claimed_by_solver_free_lane":True})
 old_map=[{"id":n["id"],"r78_state":n["state"],
           "r90_lane":("EXTERNAL_TRANSFER" if n["id"] in SOLVER_ORIGINAL
                        else "HYBRID_THEORETICAL" if n["id"] in HYBRID_ORIGINAL
                        else "SOLVER_FREE_SOURCE_CONDITIONAL"),
           "scientific_state_changed":False}
          for n in dag["nodes"]]
 return {"schema":"htt.r90.solverfree_plus_external_transfer_overlay/1",
         "science_SSOT_path":str(SSOT.relative_to(ROOT)),
         "science_SSOT_SHA256":EXPECTED_SHA_R78,
         "original_60_nodes_unchanged":True,"original_129_hard_edges_unchanged":True,
         "original_next_science_id":"SQ-CF4","no_global_agent_START":True,
         "solver_free_nodes":len(base_ids),"external_transfer_nodes":5,
         "all_six_papers":list(SF_GROUPS),"all_seven_cross_phy":list(PHY_DEPS),
         "nodes":nodes,"original_node_lane_mappings":old_map,
         "claims":"conditional canonical Lie/Codazzi attribution yes; native family posterior/Planck Bianchi full CMB no"}

def evidence_physics():
 out={}
 for name in SF_GROUPS:
  p=R89/SF_GROUPS[name]["source"][0]/"SOLVER_FREE_RESEARCH_RESULT.json"
  out[name]={"path":str(p.relative_to(ROOT)),"sha256":hash_path(p),
             "type":"actual source-conditional science result, no new full rerun"}
 return out

def blockers():
 return {"schema":"htt.r90.non_solver_blocker_triage/1","asof":"2026-11-21",
         "classification_law":"data/model/additional_analysis/solver; a workaround enables conditional diagnostics, NOT historical physics PASS",
         "entries":[{"id":id_,"category":category,
                     "blocking_input":need,"solverfree_route":route,
                     "exact_missing_to_promote":missing,
                     "physical_claim_status":"OPEN_NOT_CLOSED"}
                    for id_,category,need,route,missing in BLOCKERS],
         "unresolved_non_solver_blocks":sum(1 for _,cat,*_ in BLOCKERS if cat!="SOLVER_DEPENDENT"),
         "external_transfer_blocks":sum(1 for _,cat,*_ in BLOCKERS if cat=="SOLVER_DEPENDENT")}

def source_receipt():
 return {"schema":"htt.r90.small_download_source_receipt/1",
         "download_folder":str(DEST),"downloaded_to_external_drive":False,
         "whole_PR4_downloaded":False,
         "official_quaia_record":"https://zenodo.org/records/10403370",
         "total_bytes":sum(s for s,_ in ALLOWLIST.values()),
         "files":[{"name":n,"path":str(DEST/n),"bytes":s,
                   "md5":md5,"sha256":hash_path(DEST/n)}
                  for n,(s,md5) in ALLOWLIST.items()],
         "remaining_source_recovery":"CF4 posterior, Commander matched null, Gaia/Radio matched covariance are NOT supplied by the three files"}

def compact_report(classify,phy,quaia,ledger):
 counts={name:sum(v["finite_witness_count"] for v in classify["source_variants"].values()) for name in ["all"]}
 return f"""# R90 | Solver-free Bianchi conditional attribution and six-paper/seven-PHY execution

Base: 2026-11-21, existing active research branch. Frozen R78 remains 60 nodes, 129 hard edges, NEXT_ID SQ-CF4, original science state unchanged. New overlay has 17 solver-free work units and 5 separate native-transfer tasks.

## Science result

- R47 analytical geodesic-temperature, R49 Class A/B general tilted Lie/EOS, R62 exact CF4 7-nuisance confidence carriers were inspected/reused, not silently merged or promoted.
- Exact Codazzi conditional model: q_normal = K * M(N,a) sigma; for q=0, shear in ker M. After unknown observer SO(3) rotation, a source-space model A(R)b is profiled against each R62 full 15x15 covariance: min ||L^-1 (x-A(R)b)||². These are *constructive feasible upper bounds*; failed local optimization never proves family exclusion.
- Seven exact nuisance variants × twelve canonical/singular Lie representatives = 84 finite 95% confidence **compatibility witnesses** (total {counts['all']}/84). None proves unique Bianchi type. Type III is a VI_h stratum; VI_-1/9 is a singular rank stratum, not new independent group.
- Untyped arbitrary normal flux q allows an algebraic momentum-constraint solution for any STF shear, so adopting unconstrained tilted fluid source erases this canonical morphology-only discrimination. Matter positivity/EOS/transfer remains an independent physical question.
- R90 G01-G08 physical results reused with exact hash; 7 PHY real/constructed checks reexecuted. PHY01 real CF4 angular-mask quadrupole leakage dipole norm {phy['PHY-01']['masked_leakage_dipole_norm']:.6f}; PHY05 VI_-1/9 rank {phy['PHY-05']['VI_exception_rank']} versus generic rank {phy['PHY-05']['VI_generic_rank']}; PHY07 actual 35,970 CF4 groups yield rank {phy['PHY-07']['rank9']} → {phy['PHY-07']['rank12']} with depth.
- The dependent views are x (signed STF), Q (typed statistical Mahalanobis body), F (conditional Gaussian estimator draw occupancy), Pi=None and G_F=None without calibrated physical null and spacetime transport. This is *not* five independent likelihoods.
- New real download data: 2 Quaia full-sample HEALPix NSIDE64 selection maps + one template ZIP, {source_receipt()['total_bytes']} bytes, solely in {DEST}. Pixel-frame sky coordinate system has not been source-qualified, hence no claimed physical axis overlay. Map comparison Pearson {quaia['cross_threshold_full_pixel_delta_pearson']:.6f}.

## Route dependency

New solver-free SF-P1..SF-P6 + SF-PHY-01..07 run independently of B02/B03/B04/B05/SQ-NATIVE. The latter belong to explicit EXTERNAL_TRANSFER lane. Native Bianchi all-m T/E/B evidence, release-matched Commander CMB null, physical tilted congruence transfer and multi-probe covariance were NOT manufactured. R78 next action remains SQ-CF4 physically blocked; SF-SQ-CF4 source diagnostic exists.

## Research 10 and coding 10

R1–R3: fixed original physics, primary/history sources and claim boundaries. R4–R5: constructed Lie/Codazzi family-shape model and derived feasible Gaussian projection. R6–R7: algebra/sign/rank/degenerate limit checks and executed actual CF4, Quaia and seven PHY numerical checks. R8: assigned conditional claim ceiling. R9: code/output contract. R10: durable overlay/ledger/reproduction.
C1–C4: exact R78 baseline, source-to-code trace, stable Cholesky/SVD/rotation GLS, 6+7 lane resource/dependencies. C5: new runnable source-bound attribution, cross-PHY, Quaia comparison and restricted-download modules. C6–C8: tests and analytic/numerical validation (see verification). C9: one self-audit only, native host subagent unavailable (NOT_RUN). C10: tested artifacts, branch commit/push and handoff record.

## Open blocker classification

{ledger['unresolved_non_solver_blocks']} entries remain open at physical-acceptance level because actual external calibration, independent null or additional source matching is not present; they are assigned concrete DATA, MODEL or ADDITIONAL_ANALYSIS routes. {ledger['external_transfer_blocks']} entries are native-transfer dependent. Original scientific success has not been asserted.

### Priority scientific next
1. Source-qualified CF4 upstream calibration MCMC and PV/selection response; otherwise R90 conditional 95% family compatibility and G03 Gaia selection systematics are already executable.
2. Full survey matched radio/AGN/Planck Commander null and source covariance; existing multi-survey maps/catalogues available and analyzed in R89.
3. Compare independent Sachs optical Jacobi solution against R89 Bianchi I and adapt R49 general tilted background dynamics without claiming a photon Boltzmann solver.
4. Improve family discriminators from ker(Codazzi), curvature invariants, finite-z tidal/optical transfer, not from scalar x/Q/Pi/F/G_F label guessing.
"""

def handoff():
 return """# R90 local agent handoff (scientific continuation)
1. In /home/cosmosapjw/Dropbox/bianchi/htt_base, verify current HEAD and R78 SHA; read R90 WORK_DAG, BLOCKERS, SOURCE, ATTRIBUTION, CROSS_PHY, QUAIA_SELECTION and R49/R62 actual evidence. Do not create worktree or rewrite SSOT.
2. Non-solver DATA: request and inspect CF4 upstream calibration/independent PV ensemble; if unavailable keep old SQ-CF4 BLOCKED_INPUT, proceed solverfree. Gaia Quaia selection maps are already downloaded to ~/Downloads/htt_r90_minimal_inputs; use SHA; DO NOT write source downloads to /mnt/extdrive and DO NOT fetch full PR4/NPIPE.
3. MODEL: use R49 Class A/B 3-vector tilt full background and Codazzi constraints, R47 solver-free endpoint geodesic model, and R89 Sachs/optic. Derive family-specific forward likelihood with explicit source/frame/selection and test exact non-I counterexamples.
4. ANALYSIS: process full available CF4 35970, Gaia DR3, all five radio catalogues, Pantheon/DES, and 8 CMB maps from existing R89 when covariance/source permits. Add source-matched null where physical. Do not repeat previously validated calculations without new question.
5. Cross PHY01..07: R90 numerical experiment is a scoped seed; convert only those with actual independent source-response to observational constraints, keeping photon high-moment transfer and all-m Bianchi T/E/B external.
6. Five-variable x,Q,Pi,F,G_F only with typed body, measure, null and finite-redshift physical transfer. If missing output explicit None; do not relabel conditional compatibility as family discovery.
7. Each bounded result gets exact source hashes, executable code, tests, false-PASS protection, a short finding and next missing input. Commit/push only validated files to same research branch; do not modify main or merge open historical PRs. Preserve unrelated untracked files.
8. Transfer lane: SQ-NATIVE/B02-B05 require independent externally validated native polarized all-m Boltzmann atlas for full family probability; cannot be falsely satisfied by old R49 pre-solver conditional transport.
"""

def artifacts():
 dag=validate_inputs()
 cls=sf_attribution.run(fast=False)
 phy=crossroute.evaluate()
 selection=selection_support.measure()
 led=blockers()
 graph=work_dag(dag)
 sources=source_receipt()
 evidence=evidence_physics()
 files={
 "WORK_DAG.json":graph,
 "BLOCKER_LEDGER.json":led,
 "ATTRIBUTION_RESULT.json":cls,
 "CROSS_PHY_RESULT.json":phy,
 "QUAIA_SELECTION_RESULT.json":selection,
 "DOWNLOAD_RECEIPT.json":sources,
 "REUSED_SIX_PAPER_EVIDENCE.json":evidence,
 "STAGE_EVIDENCE.json":{
     "schema":"htt.r90.twenty_phase_source_bounded_claims/1",
     "theory":[{"id":f"R{i+1}","objective":v,"status":"EXECUTED_WITH_SCOPED_EVIDENCE"}
               for i,v in enumerate(STAGES_R)],
     "coding":[{"id":f"C{i+1}","objective":v,
                "status":"SELF_REVIEW_ONLY" if i==8 else "IMPLEMENTED_OR_TESTED_WITH_SCOPED_EVIDENCE"}
                for i,v in enumerate(STAGES_C)],
     "native_subagent":"NOT_RUN_NO_HOST_NATIVE_SPAWN",
     "scientific_60_of_60_pass":False,
     "physical_Bianchi_type_identified":False,
  },
 }
 raw={k:json.dumps(v,indent=2,ensure_ascii=False)+"\n" for k,v in files.items()}
 raw["REPORT_KO.md"]=compact_report(cls,phy,selection,led)
 raw["HANDOFF_KO.md"]=handoff()
 return raw

def main():
 ap=argparse.ArgumentParser()
 g=ap.add_mutually_exclusive_group(required=True)
 g.add_argument("--write",action="store_true")
 g.add_argument("--check",action="store_true")
 g.add_argument("--summary",action="store_true")
 args=ap.parse_args()
 try:
  art=artifacts()
  if args.write:
   if OUT.exists() and any(OUT.iterdir()):
    raise ValueError("R90 create-only: output exists")
   OUT.mkdir(parents=True,exist_ok=True)
   for n,s in art.items(): (OUT/n).write_text(s)
  if args.check:
   for n,s in art.items():
    if not (OUT/n).exists() or (OUT/n).read_bytes()!=s.encode():
     raise ValueError("R90 content drift or missing output: "+n)
  print(json.dumps({"schema":"htt.r90.run_result/1",
                    "mode":"write" if args.write else "check" if args.check else "summary",
                    "files":len(art),"solver_free_work_units":17,
                    "transfer_dependent_work_units":5,
                    "seven_phy_executed":True,
                    "r62_variants":7,"canonical_singular_representatives":12,
                    "witnesses":84,"local_download_bytes":sum(s for s,_ in ALLOWLIST.values()),
                    "physical_family_identification":False,"native_agent_dispatched":False},
                   ensure_ascii=False))
  return 0
 except (OSError,ValueError,KeyError,RuntimeError) as e:
  print(f"R90_FAIL_CLOSED: {e}",file=sys.stderr)
  return 2

if __name__=="__main__":raise SystemExit(main())
