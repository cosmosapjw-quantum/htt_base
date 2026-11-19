#!/usr/bin/env python3
"""R78 unified *science* DAG generator. Original 42 node payload immutable.

Inputs R60-R77 canonical evidence files, R67 seven-axis DAG, R77 seven PHY
contracts, canonical software PR backlog (read-only), Git refs.
Output a versioned, auditable integrated research DAG and exact-source census.
This is PLAN generation, not publication-grade science or native Boltzmann code.

Run at htt_base root:
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/build_unified.py
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

BASE=Path("docs/research_program/observational_publication_20261015")
OUT=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119"
PUB=BASE/"PUBLICATION_DAG.json"
FUS=BASE/"R67_SEVEN_AXIS_FUSION_20261118/FUSION_DAG.json"
PHY=BASE/"R77_SEVEN_PHY_CROSSVIEW_20261119/APPLICATIONS.json"
BL=Path("docs/codex_handoff/pr_backlog.yaml")
MIRROR=Path("machine_readable/pr_backlog.yaml")
PR_STATUS=Path("docs/codex_handoff/pr_status.yaml")
EXPECTED_42_SHA="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
PRIOR_HEAD="dd857ff8decbcfe90fd566a9dd87dcf5be60f609"

def sha_bytes(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def node_sha(nodes):
    """The actual R67 original identity: json.dumps(sort_keys=True) default separators."""
    return hashlib.sha256(json.dumps(nodes, sort_keys=True).encode()).hexdigest()

def git(*parts):
    return subprocess.check_output(["git",*parts],text=True).strip()

def source_census():
    p=json.loads(PUB.read_text())
    f=json.loads(FUS.read_text())
    assert len(p["nodes"])==42 and len(p["papers"])==6
    assert node_sha(p["nodes"])==EXPECTED_42_SHA==f["original_science_node_sha256"]
    assert git("merge-base","--is-ancestor",PRIOR_HEAD,"HEAD")==""  # raises if not ancestor
    backlog=yaml.safe_load(BL.read_text())
    mirror=yaml.safe_load(MIRROR.read_text())
    assert backlog==mirror and sha_bytes(BL)==sha_bytes(MIRROR)
    pr_status=yaml.safe_load(PR_STATUS.read_text())
    census=[]
    for k in range(60,78):
        dirs=list(BASE.glob(f"R{k}_*"))
        if k==69:
            # Three genuine R69 folders exist. The original R69 physics
            # bridge is the main route; both P1 follow-on routes are
            # separate records and must not be silently discarded.
            folder=BASE/"R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118"
            assert folder in dirs and len(dirs)==3,(k,dirs)
            aliases=[{"path":str(x),"anchor_name":next((a for a in ("THEOREMS_KO.md","REPORT_KO.md","THEORY.md","RESULT.json","RESULTS.json") if (x/a).is_file()),None)} for x in dirs if x!=folder]
            for a in aliases:
                assert a["anchor_name"],a
                a["sha256"]=sha_bytes(Path(a["path"])/a["anchor_name"])
        else:
            assert len(dirs)==1,(k,dirs)
            folder=dirs[0]
            aliases=[]
        files={x.name:x for x in folder.iterdir() if x.is_file()}
        anchor=next((x for x in ("RESEARCH_DAG.json","FUSION_DAG.json","PROVENANCE.json","RESULTS.json","THEORY_AND_PROOFS_KO.md","REPORT_KO.md")
                     if x in files),None)
        assert anchor
        recorded="SCOPED_COMPLETED" if k<=67 else "DERIVED_CONDITIONAL"
        reported=None
        if "RESEARCH_DAG.json" in files:
            reported=json.loads(files["RESEARCH_DAG.json"].read_text()).get("status")
        if k<=69:
            branch=next(b for b in subprocess.check_output(["git","branch","-r"],text=True).splitlines()
                        if f"/r{k}-" in b).strip()
            commit=git("rev-parse",branch)
        else:
            logs=subprocess.check_output(["git","log","--all","--format=%H %s",
                 "--extended-regexp","--grep",f"^R{k}([^0-9]|$)","-n","1"],text=True).strip().splitlines()
            commit=logs[0].split(" ",1)[0] if logs else None
        assert commit,(k,"no trusted historical stage commit")
        census.append(dict(id=f"R{k}", source_folder=str(folder), evidence=str(files[anchor]),
                           evidence_sha256=sha_bytes(files[anchor]), reported_scope_status=reported or recorded,
                           full_source_result_is_physical_publication=False,
                           last_matching_git_commit=commit,
                           additional_same_number_routes=aliases,
                           audited_in_current_ancestry=True))
    heads=[]
    for k in range(60,70):
        refs=subprocess.check_output(["git","branch","-r"],text=True).splitlines()
        match=[s.strip() for s in refs if f"/r{k}-" in s]
        assert len(match)==1,(k,match)
        sha=git("rev-parse",match[0])
        ancestry_check=subprocess.run(["git","merge-base","--is-ancestor",sha,"HEAD"])
        heads.append({"research_branch":match[0],"head_sha":sha,"in_active_history":ancestry_check.returncode==0,
                      "historical_PR_not_implicitly_merged":True})
    assert all(x["in_active_history"] for x in heads)
    return {
      "schema":"htt.r78.source_census/1",
      "current_checkout_head":git("rev-parse","HEAD"),
      "historic_42_science_nodes_sha256":EXPECTED_42_SHA,
      "historic_42_science_nodes_count":42,
      "historic_42_science_node_state_counts":dict(collections.Counter(n["state"] for n in p["nodes"])),
      "pinned_prior_HEAD_publication_container_sha256":hashlib.sha256(
        subprocess.check_output(["git","show",f"{PRIOR_HEAD}:{PUB}"])).hexdigest(),
      "original_science_node_identity_verification":"42 nodes via canonical json.dumps(sort_keys=True); independent of mutable publication pointer",
      "original_R67_fusion_dag_sha256":sha_bytes(FUS),
      "original_R77_PHY_application_sha256":sha_bytes(PHY),
      "software_PR_backlog_baseline_20261015":p["canonical_backlog_baseline_entries"],
      "current_canonical_software_PR_entries":len(backlog["prs"]),
      "current_canonical_software_PR_backlog_sha256":sha_bytes(BL),
      "current_compatibility_mirror_sha256":sha_bytes(MIRROR),
      "current_pr_status_sha256":sha_bytes(PR_STATUS),
      "software_PR_workflow_unchanged":True,
      "software_PR_status_record_lists":{k:len(pr_status.get(k) or []) for k in
          ("completed","blocked","pending","dormant_external","in_progress","background_in_progress")},
      "R60_R77_evidence":census,
      "R60_R69_branch_history":heads,
      "earlier_PR_stack_snapshot":[
        {"number":575,"head":"research/r49-general-tilted-bianchi-20261112","state":"OPEN"},
        {"number":576,"head":"research/r50-observed-convergence-20261115","state":"OPEN"},
        {"number":577,"head":"research/r54-tensor-frame-tomography-20261116","state":"OPEN"}],
      "previous_R60_R77_PR_lookup":"No matching R60-R77 numbered GitHub PRs in gh pr list --state all --limit 250; direct branch ancestry and commits are separate from GitHub PR merge status",
      "outside_branch_historical_R49_authority":"R49 frozen separate worktree source, transfer conditional; do not auto-merge old open stack"
    }

def qualified(id,paper,title,status,deps,goal,source,accept,stop,priority,evidence):
    return {"id":id,"paper":paper,"node_class":"source_qualification","state":status,"depends_on":deps,
            "objective":title,"physics_goal":goal,"source_identity":source,"acceptance":accept,
            "stop_condition":stop,"priority":priority,"evidence":evidence,
            "scientific_claim_tier":"conditional_source_contract_not_detection",
            "automatic_pub_claim":False}

def qualifiers():
    return [
      qualified("SQ-CF4","P3","CF4 selected-group method/PV calibration",
        "ready_scoped",["E1","X01","H01"],
        "Qualify the source-selected 35,970-group full indicator/selection response; independent covariance/heldout, not full 38,053 table4 geometry.",
        "R60,R61,R64,R67 and original CF4 table3/4 group IDs",
        "Match exact group/method IDs, form source-level C=N+S_PV+Jcal Sigma_cal Jcal^T+Csel, compare heldout contrast/coverage with an explicit missing-source remainder.",
        "No physical H(z,n) claim if calibrated source law cannot be built; report identified subspace and limitations.",
        1,["R60","R64","R67","R73","R77"]),
      qualified("SQ-GAIA","P6","Gaia quasar redshift/scan/AGN source calibration",
        "ready_scoped",["X01","K01"],
        "Separate astrometric E1/B1 reference spin, E2/B2 source sky aliases, redshift and AGN morphology; properly calibrate heldout patch null.",
        "R61,R69,R76; R69 Gaia-CRF3 1,580,645 quality source",
        "Reproduce 16D fit on registered subset with stable cross-hemisphere/patch forecast and a source-specific null; keep local cosmic shear unqualified.",
        "If redshift/scanning-law source unavailable, publish source-conditional alias diagnostics without physical omega.",
        2,["R61","R69","R76","R77"]),
      qualified("SQ-RADIO","P4","Radio same-source selection response k,kappa and LSS null",
        "ready_scoped",["V01","X01"],
        "Use registered overlapping peak/integrated source IDs, flux, SED, beam, size and population source response.",
        "R65,R72,R74 NVSS 33k masked pixels and selected components",
        "Estimate one physically selected k,kappa and paired covariance; source-preserving Lorentz aberration/reselection/heldout validation; distinguish log-count vs count-density.",
        "Stop if morphology/SED source cannot support physical boost inference; keep conditional 6D count score.",
        3,["R63","R65","R72","R74","R77"]),
      qualified("SQ-FRAME","COMMON","Observer/emitter normal and source frame matching",
        "ready_scoped",["X01","V01","K01"],
        "Build observer-to-source and normal-to-observer velocity/acceleration/tilt frame map with exact sign and units.",
        "R63,R69,R72,R75,R76",
        "Produce a unit-tested local proper Lorentz/Fermi frame dictionary, source frame identity and redshift-dependent applicability; no unmeasured beta.",
        "If global observer/source 3D beta absent, keep a model/source-indexed conditional map only.",
        4,["R63","R69","R75","R76"]),
      qualified("SQ-P1-ANCHOR","P1","P1 selected 274-row source physical anchor and null",
        "blocked_physical_anchor",["S01","X01"],
        "Qualify P1 original 274-row 15D signed estimand, physical anchor and unknown-scale common selected law.",
        "R60,R68,R69,R73; original P1 selected 274-row (not CF4 selected 35,970)",
        "One identified physical x with actual source covariance and partial identified interval; original P1 F/common-scale null.",
        "Stop at valid conditional partial identification when positive scale/reference unavailable.",
        5,["R60","R68","R69","R73"]),
      qualified("SQ-CMB-NULL","P2","Qualified release-matched CMB T/E/B Monte Carlo/null",
        "blocked_source",["E2","L01"],
        "Audit Commander/MES/beam/mask/foreground temperature+polarization source exchangeability and source-calibrated null.",
        "R66 actual PR3/PR4 finite-band plus Commander public MC source status",
        "Same-release source-qualified T/E/B null and actual matched cosmic/instrument simulation coverage, no invented PTE.",
        "Unavailable matched MC remains blocked; PR4 vs PR3 not independent sky detections.",
        6,["R66","R67","R70","R77"]),
      qualified("SQ-PHOTON-FLUX","P2","Photon flux/kinetic higher moments and common normal source",
        "blocked_source",["L01","B01"],
        "Source physically same electron-normal f_gamma, rho_gamma/rho_N, j_other, high-L/Thomson closure.",
        "R66,R70,R73,R77 photon stress without actual f",
        "Check P-ff^T PSD and Einstein-Codazzi joint photon-only vs multifluid constraints with independently defined frame.",
        "Do not set photon-only total momentum if other species carry normal flux or f unobserved.",
        7,["R66","R70","R73","R77"]),
      qualified("SQ-LIE-FLUX","P5","Independent normal-frame rho,j,pi and Bianchi family source",
        "blocked_source",["B01","K01"],
        "Independent stress/flux in one normal Bianchi tetrad, including Class A/B exceptional rank and multiple tilted fluids.",
        "R49 historical transfer-conditional posterior and R62,R75",
        "Rank-aware normal Codazzi residual using independently sourced shear+u with covariance and Hamiltonian consistency.",
        "A flux computed from the same shear via Codazzi yields a tautology, not astrophysical validation.",
        8,["R62","R75","R77"]),
      qualified("SQ-OPTICAL","COMMON","Finite-redshift Sachs/Jacobi + position-drift transfer",
        "pending_conditional",["H01","K01","B01","SQ-FRAME"],
        "For one named family/observer/source, construct local-to-finite-z optical and Gaia position-drift Jacobians with boundaries.",
        "R69,R71,R75,R76, and original source time/redshift distributions",
        "Validate z->0 local H and same-tensor scalar/E2 consistency; compute T_C(z), T_G(z), and precise finite-z optical remainder with heldout prediction.",
        "No arbitrary extrapolation of low-z STF identity to full Gaia redshift; no native all-family solver here.",
        9,["R69","R71","R75","R76","R77"]),
      qualified("SQ-CROSS-COV","COMMON","Actual cross-probe source covariance and null/heldout",
        "pending_dependency",["SQ-CF4","SQ-GAIA","SQ-RADIO","SQ-FRAME","SQ-OPTICAL"],
        "Build a measured common observer/source covariance, not pseudo-independent CMB/Gaia/CF4/radio score multiplication.",
        "R67,R73,R77 and original source IDs/systematics",
        "Independent source-level cross-covariance and calibrated heldout predictive test; report identifiable target rank and nuisance profile.",
        "If no justified physical cross-covariance, do not compute cross-instrument astrophysical Pi/Bayes factor.",
        10,["R67","R73","R76","R77"]),
      qualified("SQ-NATIVE","P5","External native polarized Bianchi transfer/atlas qualification",
        "blocked_external",["B01","L01"],
        "Intake external native E/B all-m solver outputs and independent transfer validation only when real external source exists.",
        "R49 historical transfer conditional, R67 source rules, AGENTS nonnegotiable no native implementation",
        "Qualify actual external solver provenance, CMB/Planck response family confusion and injection with heldout calibrated null.",
        "Never implement or simulate future native low-ell solver in htt_base; stop pending real external data.",
        11,["R49","R66","R67","R75"])
    ]

SUPPLEMENTAL={
  "S02":["SQ-P1-ANCHOR"],
  "H02":["SQ-CF4"],
  "L03":["SQ-CMB-NULL"],
  "V04":["SQ-FRAME","SQ-RADIO"],
  "B02":["SQ-NATIVE"],
  "B03":["SQ-CMB-NULL","SQ-OPTICAL"],
  "K03":["SQ-GAIA"],
  "K04":["SQ-OPTICAL"],
  "K05":["SQ-CROSS-COV"],
}
PHY_NEEDS={
 "PHY-01":["SQ-CF4","SQ-OPTICAL","SQ-LIE-FLUX"],
 "PHY-02":["SQ-CMB-NULL","SQ-PHOTON-FLUX","SQ-LIE-FLUX"],
 "PHY-03":["SQ-RADIO","SQ-PHOTON-FLUX","SQ-FRAME"],
 "PHY-04":["SQ-GAIA","SQ-RADIO","SQ-OPTICAL","SQ-FRAME"],
 "PHY-05":["SQ-LIE-FLUX","SQ-OPTICAL"],
 "PHY-06":["SQ-CMB-NULL","SQ-PHOTON-FLUX","SQ-LIE-FLUX","SQ-OPTICAL"],
 "PHY-07":["SQ-CF4","SQ-RADIO","SQ-OPTICAL","SQ-FRAME"]
}

def build(revision=0):
    census=source_census()
    pub=json.loads(PUB.read_text())
    original=pub["nodes"]
    paper_ids={p["id"] for p in pub["papers"]}
    routes=json.loads(PHY.read_text())["combinations"]
    assert len(routes)==7 and {r["id"] for r in routes}==set(PHY_NEEDS)
    qs=qualifiers()
    phy_nodes=[]
    for r in routes:
        id=r["id"]
        phy_nodes.append(dict(
            id=id,paper="CROSS",node_class="physical_cross_route",
            state="theory_verified_physical_data_pending",depends_on=PHY_NEEDS[id],
            objective=r["R77_specific_theorem"],axes=r["axes"],
            x=r["x"],Q=r["Q"],Pi=r["Pi"],F=r["F"],G_F=r["G_F"],
            observable_evidence=r["actual_source_or_synthetic_check"],
            acceptance="Physically matched source/null/frames and heldout independent predictive discriminator; preserve signed source data and joint covariance.",
            next_bounded_empirical_test=r["next_bounded_empirical_test"],
            stop_condition=r["physical_blocker"],
            evidence=["R67","R68","R69","R70","R71","R72","R73","R74","R75","R76","R77"],
            scientific_claim_tier="conditional_theory_not_cosmological_detection"))
    nodes=[*original,*qs,*phy_nodes]
    allids=[x["id"] for x in nodes]
    assert len(allids)==len(set(allids))==60
    edges=[]
    for n in nodes:
        for p in n.get("depends_on",[]):
            edges.append({"from":p,"to":n["id"],"kind":"original_science" if n["id"] in {x["id"] for x in original} else "new_source_or_physical_route","hard":True})
    for to,fromlist in SUPPLEMENTAL.items():
        for fr in fromlist:
            edges.append({"from":fr,"to":to,"kind":"new_qualification_overlay","hard":True,"changes_original_node_payload":False})
    ind={id:0 for id in allids}
    adj={id:[] for id in allids}
    for e in edges:
        assert e["from"] in ind and e["to"] in ind,e
        ind[e["to"]]+=1;adj[e["from"]].append(e["to"])
    ready=sorted(x for x in ind if not ind[x])
    top=[]
    while ready:
        x=ready.pop(0);top.append(x)
        for nxt in adj[x]:
            ind[nxt]-=1
            if not ind[nxt]:ready.append(nxt)
        ready.sort()
    assert len(top)==len(allids),("CYCLE",len(top),len(allids))
    old_states={n["id"]:n["state"] for n in original}
    done={id for id,s in old_states.items() if s=="completed_scoped"}
    # Newly qualified nodes are NEVER assumed completed, even if local source exists.
    pending=[]
    for n in qs:
        if all(dep in done for dep in n["depends_on"]):
            pending.append({"id":n["id"],"state":n["state"],"priority":n["priority"],"action":n["objective"]})
    order=sorted(pending,key=lambda x:x["priority"])
    assert order[0]["id"]=="SQ-CF4"
    out={
     "schema":"htt.r78.unified_science_dag/1",
     "date":"2026-11-19 KST",
     "revision":revision,
     "science_SSOT":"docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json",
     "historical_42_node_source":"docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json",
     "original_42_payload_sha256":node_sha(original),
     "software_PR_backlog_authority":"docs/codex_handoff/pr_backlog.yaml",
     "current_software_PR_entries":census["current_canonical_software_PR_entries"],
     "software_PR_baseline_historical":census["software_PR_backlog_baseline_20261015"],
     "publication_status":"NOT_READY_TO_SUBMIT",
     "no_auto_merge_or_main_push":True,
     "provenance_claim_rule":"R60-66 COMPLETE_SCOPED_C0, R67-77 conditional evidence; no original 42 science gate auto-promoted",
     "count_original_science":len(original),"count_new_source_qualifiers":len(qs),
     "count_cross_phy_theory_routes":len(phy_nodes),
     "count_total_graph_nodes":len(nodes),"papers":[p["id"] for p in pub["papers"]],
     "seven_R67_research_axes":json.loads(FUS.read_text())["research_axes"],
     "seven_R77_PHY_combinations":[{"id":x["id"],"axes":x["axes"]} for x in routes],
     "nodes":nodes,"edges":edges,
     "topological_order":top,
     "source_qualification_overlay":SUPPLEMENTAL,
     "initial_executable_frontier":[x for x in order if x["state"]=="ready_scoped"],
     "not_currently_executable_frontier":[x for x in order if x["state"]!="ready_scoped"],
     "next_action_id":"SQ-CF4",
     "next_action_contract":{
         "node_id":"SQ-CF4",
         "scope":"one bounded CF4 selected-method source covariance/identity slice; no new 10-stage meta loop",
         "input":"R58/R61 original 35970 selected group IDs and method32, original table3/4 and R64 full group genealogy; original source covariance",
         "physical_estimand":"method-conditioned angular/radial response and partially identifiable PV-Hubble dipole, NOT local GR shear yet",
         "action":"audit exact selected source IDs, fit one same-source calibration nuisance or measure missing cross-indicator terms, compare heldout coverage/contrast",
         "pass":"actual source-conditional calibrated covariance/coverage or reproducible partially identified limitation with source IDs and heldout",
         "stop":"no matched global selection/calibration source => record blocker and choose SQ-GAIA, never promote H04",
         "commit_policy":"scoped validated source/result changes only on active research branch"},
     "evidence_R60_R77":[{k:v for k,v in x.items() if k in ("id","evidence","evidence_sha256","reported_scope_status","last_matching_git_commit")} for x in census["R60_R77_evidence"]],
     "review_status":"CANDIDATE_UNREVIEWED" if revision==0 else "REVISED_UNDER_LIMITED_ADVERSARIAL_AUDIT",
     "no_native_boltzmann_solver_implementation":True
    }
    return out,census

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--revision",type=int,default=0)
    args=ap.parse_args()
    assert args.revision in (0,1,2,3)
    OUT.mkdir(parents=True,exist_ok=True)
    plan,census=build(args.revision)
    (OUT/"INTEGRATED_DAG.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n")
    (OUT/"SOURCE_CENSUS.json").write_text(json.dumps(census,ensure_ascii=False,indent=2)+"\n")
    print("R78_DAG_GENERATED",plan["count_total_graph_nodes"],"NODE",len(plan["edges"]),"EDGES",len(plan["topological_order"]),"ACYCLIC",plan["revision"],"rev")
    print("R78_FRONTIER",plan["initial_executable_frontier"])
    print("R78_SCIENCE_HASH",plan["original_42_payload_sha256"])
    print("R78_SOFTWARE_PR",census["current_canonical_software_PR_entries"],"baseline",census["software_PR_backlog_baseline_20261015"])

if __name__=="__main__":
    main()
