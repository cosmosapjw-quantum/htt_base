"""Exact 60-node R78 preparation overlay and fail-closed science entry.

This is an execution preparation adapter, not a rewritten publication DAG.
Seven reusable calculation packages are mapped to all canonical node IDs.
A package result never satisfies a different node's scientific acceptance.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
DAG=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
OUT=BASE/"R98_FOURTH_RESEARCH_CYCLE_20261123"
PIN="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
BASELINE="52fee3f277d715cdb982dfbe751fefac10513060"
PY=".venv/bin/python"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# IDs refer to distinct scientific obligations; a node may inherit several.
BLOCKERS={
"D01":("DATA","CF4 upstream calibration","Pre-intercalibration joint zero-point law, anchor training membership and DirectCal cross-covariance are absent.","MISSING_INPUT_CONTRACTS.json#CF4_UPSTREAM_CALIBRATION","Obtain source-signed upstream law; preserve 7-method order and gauge. Do not estimate it again from globally registered moduli."),
"D02":("DATA","CF4 selection","Targeting, rejected-source denominators and method-specific inclusion law are absent.","MISSING_INPUT_CONTRACTS.json#CF4_PV_SELECTION","Acquire source selection metadata, join all 38053 groups and 55877 galaxy rows; fit a selection likelihood including rejected sources."),
"M01":("MODEL","CF4 physical correlated PV","R36 low-k selected covariance and R98 log-noise dispersion are working alternatives, not the full source-space PV law.","CF4_P1_RESULTS.json","Build a cosmology-conditioned velocity covariance operator and source distance likelihood; compare physical PV alternatives on all eligible rows."),
"M02":("MODEL","finite-redshift optical/frame transfer","Apparent log expansion, radial velocity, proper-motion and normal-frame kinematics need a shared finite-z response.","BIANCHI_HISTORY_RESULTS.json","Extend R49 geodesic/Sachs transport along the same background, include observer/emitter tilt and source distances; verify Jacobi/optical limits."),
"M03":("MODEL","P1 physical anchor and finite law","The 2048 weights define a coupled working finite measure, without the physical body/anchor or calibrated joint law.","CF4_P1_RESULTS.json#P1","Map the admitted source law through a signed physical carrier; retain unknown mass and common nuisance, with no per-draw nuisance maximization."),
"D03":("DATA","CMB matched simulation genealogy","Observed splits and full bank exist. A qualified common split/noise/systematics/foreground law, including Commander noise, is still absent.","CMB_OBSERVED_SPLITS.json","Use official PR3 product index and existing files; acquire missing component-specific simulations with exact IDs/beam/masks and prove the joint law."),
"M04":("MODEL","CMB foreground/selected-weight null","Repeated noise groups, foreground residuals and selected nuisance fits need a matched null for each statistic.","CMB_GROUPED_FULL_CACHE.json","Keep group-wise cross-fitting, add paired residual/foreground and weight-selection generative model; calibrate on held-out noise groups."),
"D04":("DATA","Gaia angular astrometric/AGN covariance","Per-source pm covariance and 48-patch diagnostics exist; AGIS/spatial correlated error and independent AGN-source null are not qualified.","GAIA_FULL_SHARED_PATCH.json","Use all source_id joins and official angular-systematics references; acquire release-specific correlated error evidence where available."),
"M05":("MODEL","Gaia source/normal-frame relation","E2/B2 apparent tangent fields combine scan, source centroids, frame spin and cosmological transport.","GAIA_FULL_SHARED_PATCH.json","Fit spatial low-rank scan+AGN nuisance and finite-z optical response jointly; reference-frame spin/vorticity degeneracy stays explicit."),
"D05":("DATA","radio footprint/completeness/SED","Five full catalogues exist; all-sky tile/RMS/zero-source coverage, resolved components and spectral-index response are incomplete.","ACQUISITION_PREFLIGHT.json","Use recorded official RMS/mask links with size/checksum preflight; join catalog components and multi-frequency source matches before response calibration."),
"M06":("MODEL","radio LSS and selection response","NB1 conditional cell law improves overdispersion treatment but is not a shared-source LSS/selection simulation law.","RADIO_FULL_MODELS.json","Develop Cox/LSS mocks with flux-size completeness and spectral-index distribution; jointly propagate shared-object and shared-sky covariance."),
"M07":("MODEL","local/global velocity transfer","Finite observer boost and source-history global tilt require common-frame, distinct calibrated response columns.","BIANCHI_HISTORY_RESULTS.json","Compute common-operator Jacobians for both mechanisms, test singular values under observational covariance rather than arbitrary column normalization."),
"D06":("DATA","independent normal-frame matter/photon flux","Independent rho,j,pi in a common normal frame are absent; Codazzi inversion alone cannot supply a new observation.","CROSS_PHY_RESULTS.json","Prepare source/units/frame contracts; seek independent matter or photon observables. No generic catalogue download supplies all these moments."),
"M08":("MODEL","Einstein–Boltzmann feedback/IC atlas","R98 evolves Einstein–Euler backgrounds and passive prescribed-xe all-m radiation; photon backreaction and primordial mode family are open.","BIANCHI_HISTORY_RESULTS.json","Couple radiation moments to background Euler/Einstein equations; define regular/irregular IC families and compare scope-matched external solvers."),
"M09":("MODEL","anisotropic recombination/reionization closure","Main sky uses prescribed HyRec2+tanh. A finite Peebles window response exists, not a self-consistent anisotropic radiative closure.","BIANCHI_THEORY_CODE_KO.md","Extend retained rec/rei source operators along actual H/clock with photons and density; verify conserved energy, opacity and chemical closure."),
"A01":("ADDITIONAL_ANALYSIS","source-law coverage and independent validation","Current full-data processing is complete within its stated working models; physical-law coverage tests still depend on new law inputs.","CF4_P1_RESULTS.json","After D01/D02/M01, execute complete-source posterior predictive and truly independent holdout/selection injections, with old diagnostic retained."),
"A02":("ADDITIONAL_ANALYSIS","CMB statistic-specific calibration","999 signal/paired and 300 noise grouped diagnostics plus 10 observed maps are complete; physical null coverage remains open.","CMB_GROUPED_FULL_CACHE.json","Once D03/M04 are qualified, rerun all groups and all candidate statistics with a prospective multiplicity protocol; retain noise genealogy."),
"A03":("ADDITIONAL_ANALYSIS","Bianchi atlas and convergence","Five declared histories and L12 all-m have run; complete I–IX/exceptional mode families and stronger source/collision convergence are pending.","BIANCHI_HISTORY_RESULTS.json","Expand admissible parameter/IC atlas with constraint monitoring; test scalar/vector/tensor limits, radiation feedback and external near-FLRW agreement."),
"A04":("ADDITIONAL_ANALYSIS","cross-probe calibrated covariance","Joint spatial patch diagnostics are computed; a common physically calibrated source/selection/transport null remains absent.","GAIA_FULL_SHARED_PATCH.json","Use all catalog overlap IDs and common mock sky/light cone, not product of per-survey likelihoods; compare alternative source and transfer models."),
"A05":("ADDITIONAL_ANALYSIS","selection robustness/injection and all-source comparison","Full radio/Gaia working-law fits and paired model contrasts are available; source-model injection/coverage is not.","RADIO_FULL_MODELS.json","Repeat all flux/redshift/model combinations on qualified matched mocks, including missing/zero-source regions and systematic model alternatives."),
"A06":("ADDITIONAL_ANALYSIS","publication and novelty adjudication","Publication gates require completed upstream claims and a matched primary-literature comparison.","REPORT_KO.md","Use source-qualified results to decide informative null/partial identification/model discrimination, then draft; keep retrospective statistics retrospective.")
}
PACKAGES={
"CF4":{"command":[PY,"-m","scripts.r98.cf4_p1"],"outputs":["CF4_P1_RESULTS.json"],"purpose":"all CF4 rows, log tomography, common-nuisance P1"},
"CMB_CACHE":{"command":[PY,"-m","scripts.r98.cmb_full","cache"],"outputs":["CMB_GROUPED_FULL_CACHE.json"],"purpose":"all999+300 grouped null diagnostics"},
"CMB_SPLITS":{"command":[PY,"-m","scripts.r98.cmb_full","splits"],"outputs":["CMB_OBSERVED_SPLITS.json"],"purpose":"10 complete NSIDE2048 observed maps, existing inputs"},
"BIANCHI":{"command":[PY,"-m","scripts.r98.bianchi_history","--output",str(OUT/"BIANCHI_HISTORY_RESULTS.json")],"outputs":["BIANCHI_HISTORY_RESULTS.json"],"purpose":"five full histories/passive all-m radiation and chemistry"},
"GAIA":{"command":[PY,"-m","scripts.r98.cross_survey","--task","gaia"],"outputs":["GAIA_FULL_SHARED_PATCH.json"],"purpose":"all1.614M CRF3+all692154 Quaia join, shared48patch"},
"RADIO":{"command":[PY,"-m","scripts.r98.cross_survey","--task","radio"],"outputs":["RADIO_FULL_MODELS.json"],"purpose":"five full radio catalogues,19thresholds,NB1/Poisson/sharedpatch"},
"CROSS":{"command":[PY,"-m","scripts.r98.cross_phy","--output",str(OUT/"CROSS_PHY_RESULTS.json")],"outputs":["CROSS_PHY_RESULTS.json"],"purpose":"seven coupled theoretical/source-dependent preparation cases"}
}
DIRECT={
"S02":["D01","D02","M01","M02","M03"],"S03":["A05"],"S04":["M03","A01"],"S05":["A06"],"S06":["A06"],
"L03":["D03","M04"],"L04":["A02"],"L05":["A06"],"L06":["A06"],
"H02":["D01","D02","M01"],"H04":["A01","M02"],"H05":["A06"],"H06":["A06"],
"V04":["M07","A04"],"V05":["A04","A05"],"V06":["A06"],
"B02":["M08","M09","A03"],"B03":["A02","A03"],"B04":["A03","A04"],"B05":["A06"],
"K03":["D04","M02","M05"],"K04":["M02","A01"],"K05":["M05","M07","A04"],"K06":["A06"],
"SQ-CF4":["D01","D02","M01","A01"],"SQ-GAIA":["D04","M05","A05"],"SQ-RADIO":["D05","M06","A05"],
"SQ-FRAME":["M02","M07"],"SQ-P1-ANCHOR":["M03"],"SQ-CMB-NULL":["D03","M04","A02"],
"SQ-PHOTON-FLUX":["D06","M08"],"SQ-LIE-FLUX":["D06","M08"],"SQ-OPTICAL":["M02"],
"SQ-CROSS-COV":["A04"],"SQ-NATIVE":["M08","M09","A03"],
"PHY-01":["M02","A04"],"PHY-02":["D06","M08"],"PHY-03":["M06","M07","A04"],"PHY-04":["M02","M05","A04"],
"PHY-05":["D06","A04"],"PHY-06":["M08","M09"],"PHY-07":["M01","M02","M06","A04"]
}
def node_packages(node):
 id=node["id"];paper=node["paper"]
 if paper=="P1" or paper=="P3":return ["CF4"]
 if paper=="P2":return ["CMB_CACHE","CMB_SPLITS"]
 if paper=="P4":return ["RADIO","BIANCHI"]
 if paper=="P5":return ["BIANCHI"]
 if paper=="P6":return ["GAIA","CF4","BIANCHI"]
 if paper=="CROSS":return ["CROSS"]
 return {"E0":["CROSS"],"E1":["CF4"],"E2":["CMB_CACHE"],"E3":["CF4"],"X01":["CROSS"],"X02":["CROSS"],"X03":["CROSS"],
         "SQ-FRAME":["BIANCHI","GAIA","RADIO"],"SQ-OPTICAL":["BIANCHI"],"SQ-CROSS-COV":["CF4","CMB_CACHE","RADIO","GAIA","CROSS"]}[id]
def build():
 if sha(DAG)!=PIN:raise RuntimeError("R78 authority changed; reconcile explicitly")
 d=json.loads(DAG.read_text());nodes={n["id"]:n for n in d["nodes"]}
 if len(nodes)!=60:raise RuntimeError("expected exact60 canonical IDs")
 parents={key:set(n["depends_on"]) for key,n in nodes.items()}
 for edge in d["edges"]:
  if edge.get("hard",True):parents[edge["to"]].add(edge["from"])
 memo={};active=set()
 def inherited(id):
  if id in memo:return memo[id]
  if id in active:raise RuntimeError("canonical hard dependency cycle")
  active.add(id);b=set(DIRECT.get(id,[]))
  for parent in parents[id]:b.update(inherited(parent))
  active.remove(id);memo[id]=sorted(b);return memo[id]
 rows=[]
 for n in d["nodes"]:
  id=n["id"];bs=inherited(id);pk=node_packages(n)
  state="INHERITED_COMPLETED_SCOPED" if n["state"]=="completed_scoped" else "SCIENCE_BLOCKED"
  # A ready_scoped qualifier is an executable diagnostic, not admitted science.
  rows.append({"id":id,"paper":n["paper"],"original_state":n["state"],"original_objective":n["objective"],
       "original_acceptance":n["acceptance"],"original_dependencies":n["depends_on"],"effective_hard_dependencies":sorted(parents[id]),
       "science_status":state,"direct_blockers":DIRECT.get(id,[]),"all_blockers_including_dependencies":bs,
       "blocker_categories":sorted({BLOCKERS[x][0] for x in bs}),
       "preparation_packages":pk,"available_results":[x for p in pk for x in PACKAGES[p]["outputs"] if (OUT/x).exists()],
       "next_action":[BLOCKERS[x][4] for x in DIRECT.get(id,[])] or ["Reuse exact inherited scoped evidence; check its source identity before downstream scientific promotion."],
       "new_acceptance_claimed":False})
 blockers={k:{"category":v[0],"label":v[1],"current_defect":v[2],"R98_evidence":v[3],"prepared_action":v[4],
               "status":"OPEN_OR_PARTIALLY_RESOLVED","affected_nodes":[r["id"] for r in rows if k in r["all_blockers_including_dependencies"]]} for k,v in BLOCKERS.items()}
 out={"schema":"htt.r98.exact60_preparation_overlay/1","baseline":BASELINE,"science_authority":{"path":str(DAG.relative_to(ROOT)),"sha256":PIN,"next_id":d["next_action_id"],"modified":False},
      "canonical_edges":d["edges"],"source_qualification_overlay":d["source_qualification_overlay"],
      "counts":{"nodes":len(rows),"edges":len(d["edges"]),"node_payload_dependencies":sum(len(n["depends_on"]) for n in nodes.values()),"major_topics":6,"cross_topics":7,"original_scoped_completed":sum(r["science_status"]=="INHERITED_COMPLETED_SCOPED" for r in rows),"new_science_nodes_promoted":0,
               "distinct_open_obligations":dict(collections.Counter(b["category"] for b in blockers.values()))},
      "node_count_by_paper":dict(collections.Counter(r["paper"] for r in rows)),
      "packages":{k:{**v,"output_sha256":{x:sha(OUT/x) for x in v["outputs"] if (OUT/x).exists()}} for k,v in PACKAGES.items()},
      "blockers":blockers,"nodes":rows,
      "authorized_scope_update":"Current owner's explicit fourth-cycle execution and internal-model construction supersede obsolete blanket R86 worker/native-code STOP for scoped preparation. Scientific R78 acceptance is unchanged.",
      "interpretation":"Seven reusable preparation packages are not 60 independent science executions. Each node retains its own exact acceptance and inherited blockers."}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"NODE60_EXECUTION_PREPARATION.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 lines=["# R98: exact 60-node execution preparation","","R78 authority is unchanged. DATA / MODEL / ADDITIONAL_ANALYSIS apply to each obligation, not mutually exclusive node labels.","","| ID | Topic | Original state | Direct blockers | Inherited blockers | Preparation |","|---|---|---|---|---|---|"]
 for r in rows:lines.append("| "+" | ".join([r["id"],r["paper"],r["original_state"],", ".join(r["direct_blockers"]) or "—",", ".join(r["all_blockers_including_dependencies"]) or "—",", ".join(r["preparation_packages"])])+" |")
 lines+=["","## Blocker actions",""]
 for k,b in blockers.items():lines +=[f"### {k} — {b['category']}: {b['label']}","",b["current_defect"],"",b["prepared_action"],"",f"R98 evidence: `{b['R98_evidence']}`",""]
 (OUT/"NODE60_BLOCKERS_AND_ACTIONS.md").write_text("\n".join(lines).rstrip()+"\n")
 return out
def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument("--build",action="store_true");ap.add_argument("--node");ap.add_argument("--mode",choices=["preparation","science"],default="preparation");ap.add_argument("--execute",action="store_true");ap.add_argument("--include-observed-splits",action="store_true");args=ap.parse_args(argv)
 d=build()
 if not args.node:print(json.dumps(d["counts"]));return 0
 found=[x for x in d["nodes"] if x["id"]==args.node]
 if not found:ap.error("unknown canonical node ID")
 row=found[0]
 if args.mode=="science":
  print(json.dumps({"node":args.node,"status":row["science_status"],"blockers":row["all_blockers_including_dependencies"],"science_command_executed":False,"acceptance":row["original_acceptance"]},ensure_ascii=False))
  return 3 if row["science_status"]=="SCIENCE_BLOCKED" else 0
 keys=row["preparation_packages"]
 if args.execute:
  env={**os.environ,"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","PYTHONDONTWRITEBYTECODE":"1","HTT_ANALYSIS_BACKEND":"auto"}
  for key in keys:
   if key=="CMB_SPLITS" and not args.include_observed_splits:
    if not all((OUT/x).exists() for x in PACKAGES[key]["outputs"]):raise FileNotFoundError("observed split result missing; use --include-observed-splits")
    old=json.loads((OUT/"CMB_OBSERVED_SPLITS.json").read_text())
    if old["environment"]["script_sha256"]!=sha(ROOT/"scripts/r98/cmb_full.py"):raise RuntimeError("split producer changed; rerun --include-observed-splits")
    continue
   result=subprocess.run(PACKAGES[key]["command"],cwd=ROOT,env=env)
   if result.returncode:return result.returncode
  d=build()
 print(json.dumps({"node":args.node,"mode":"preparation","packages":keys,"science_status":row["science_status"],"science_acceptance_promoted":False,"commands":[PACKAGES[k]["command"] for k in keys]},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
