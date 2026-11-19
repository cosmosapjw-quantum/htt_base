#!/usr/bin/env python3
"""Adversarial structure/provenance validator of the R78 unified science plan.

Validates graph/SSOT/source identity and claim guardrails, NOT observational physics
or the missing external Bianchi transfer. --strict verifies the live R78 pointers.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

ROOT=Path("docs/research_program/observational_publication_20261015")
DIR=ROOT/"R78_UNIFIED_SCIENCE_DAG_20261119"
PUB=ROOT/"PUBLICATION_DAG.json"
FUS=ROOT/"R67_SEVEN_AXIS_FUSION_20261118/FUSION_DAG.json"
DAG=DIR/"INTEGRATED_DAG.json"
CENSUS=DIR/"SOURCE_CENSUS.json"
EXPECTED="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
    return json.loads(p.read_text())
def canonical(nodes):
    return hashlib.sha256(json.dumps(nodes,sort_keys=True).encode()).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--strict-authority",action="store_true")
    ap.add_argument("--save",action="store_true")
    args=ap.parse_args()
    checks={}
    issues=[]
    def check(name,truth,details=None):
        checks[name]={"pass":bool(truth),"details":details}
        if not truth:issues.append(name)
    d=load(DAG);c=load(CENSUS);old=load(PUB)
    orig=old["nodes"]
    archived=load(FUS)
    check("original_42_exact_payload",[n for n in d["nodes"] if n["id"] in {o["id"] for o in orig}]==orig)
    check("original_42_hash",canonical(orig)==EXPECTED==canonical([n for n in d["nodes"] if n["id"] in {o["id"] for o in orig}])==archived["original_science_node_sha256"])
    check("historic_status_no_auto_promotion",len(orig)==42 and
          collections.Counter(n["state"] for n in orig)==collections.Counter(n["state"] for n in d["nodes"] if n["id"] in {o["id"] for o in orig}))
    check("papers_6",len(old["papers"])==6 and len(d["papers"])==6)
    check("graph_node_count",len(d["nodes"])==d["count_total_graph_nodes"]==60)
    byid={n["id"]:n for n in d["nodes"]}
    check("no_duplicate_node_ids",len(byid)==60)
    check("qualifier_count",len([n for n in d["nodes"] if n.get("node_class")=="source_qualification"])==11)
    check("PHY_count",len([n for n in d["nodes"] if n.get("node_class")=="physical_cross_route"])==7 and
          {n["id"] for n in d["nodes"] if n.get("node_class")=="physical_cross_route"}=={f"PHY-{i:02d}" for i in range(1,8)})
    check("R67_seven_research_axes_distinct_from_PHY",len(d["seven_R67_research_axes"])==7 and
          len(d["seven_R77_PHY_combinations"])==7 and
          {x["id"] for x in d["seven_R67_research_axes"]}!={x["id"] for x in d["seven_R77_PHY_combinations"]})
    edges=d["edges"]
    check("edge_source_dest_valid",all(e["from"] in byid and e["to"] in byid and e["from"]!=e["to"] for e in edges))
    check("edge_unique",len({(e["from"],e["to"]) for e in edges})==len(edges))
    check("edge_count",len(edges)==129)
    order=d["topological_order"]
    idx={id:i for i,id in enumerate(order)}
    check("complete_acyclic_toposort",len(order)==len(set(order))==60 and
          all(x in idx for x in byid) and all(idx[e["from"]]<idx[e["to"]] for e in edges))
    check("original_edges_preserved",all(any(e["from"]==j and e["to"]==n["id"] and e["kind"]=="original_science"
                      for e in edges) for n in orig for j in n.get("depends_on",[])))
    check("source_overlay_not_mutating_science_payload",all(not e["changes_original_node_payload"] for e in edges
                      if e["kind"]=="new_qualification_overlay"))
    qual={n["id"]:n for n in d["nodes"] if n.get("node_class")=="source_qualification"}
    check("next_ready",d["next_action_id"]=="SQ-CF4" and
          [r["id"] for r in d["initial_executable_frontier"]]==["SQ-CF4","SQ-GAIA","SQ-RADIO","SQ-FRAME"] and
          all(qual[r["id"]]["state"]=="ready_scoped" for r in d["initial_executable_frontier"]))
    check("blocked_not_ready",all(qual[r["id"]]["state"]!="ready_scoped" for r in d["not_currently_executable_frontier"]))
    check("P1_anchor_distinguishes_missing_physics_from_existing_law",qual["SQ-P1-ANCHOR"]["state"]=="blocked_physical_anchor")
    check("native_solver_preserved_external",qual["SQ-NATIVE"]["state"]=="blocked_external" and d["no_native_boltzmann_solver_implementation"])
    check("original_B02_blocked_on_native_source",any(e["from"]=="SQ-NATIVE" and e["to"]=="B02" for e in edges))
    check("original_H02_linked_to_real_CF4_source",any(e["from"]=="SQ-CF4" and e["to"]=="H02" for e in edges))
    check("R60_R77_coverage",len(c["R60_R77_evidence"])==18 and
          [x["id"] for x in c["R60_R77_evidence"]]==[f"R{i}" for i in range(60,78)])
    aliases=[x for x in c["R60_R77_evidence"] if x["id"]=="R69"][0]["additional_same_number_routes"]
    check("R69_three_separate_source_artifacts",len(aliases)==2 and all(len(x["sha256"])==64 for x in aliases))
    sourceok=True
    for x in c["R60_R77_evidence"]:
        p=Path(x["evidence"])
        sourceok &= p.is_file() and sha(p)==x["evidence_sha256"] and x["last_matching_git_commit"] is not None
        for a in x.get("additional_same_number_routes",[]):
            p2=Path(a["path"])/a["anchor_name"]
            sourceok &= p2.is_file() and sha(p2)==a["sha256"]
    check("R60_R77_source_pins_current_bytes",sourceok)
    bl=Path("docs/codex_handoff/pr_backlog.yaml")
    mirror=Path("machine_readable/pr_backlog.yaml")
    canon=yaml.safe_load(bl.read_text());m=yaml.safe_load(mirror.read_text())
    check("291_current_software_PR_vs_245_historical",len(canon["prs"])==c["current_canonical_software_PR_entries"]==291 and
          c["software_PR_backlog_baseline_20261015"]==245 and old["canonical_backlog_baseline_entries"]==245)
    check("canonical_software_PR_mirror_byte",sha(bl)==sha(mirror)==c["current_canonical_software_PR_backlog_sha256"])
    check("publication_claim_guard",d["publication_status"]=="NOT_READY_TO_SUBMIT" and
          all(n.get("automatic_pub_claim") is False for n in qual.values()))
    check("no_independent_likelihood_from_views",all(n.get("scientific_claim_tier")=="conditional_theory_not_cosmological_detection"
          for n in d["nodes"] if n.get("node_class")=="physical_cross_route"))
    if args.strict_authority:
        p=old.get("current_integrated_science_dag",{})
        check("active_publication_pointer",p.get("path")==str(DAG) and
              old.get("current_scientific_route",{}).get("research_dag")==str(DAG))
        ag=Path("AGENTS.md").read_text()
        check("AGENTS_current_science_pointer","R78_UNIFIED_SCIENCE_DAG_20261119" in ag)
    out={"schema":"htt.r78.dag_verification/1","strict_authority":args.strict_authority,
         "pass":not issues,"checks":checks,"failed_checks":issues,
         "source_evidence_tier":"plan graph/source identity only, not GR model approval",
         "node_counts":{"historical_science":42,"qualification":11,"conditional_cross_phy":7,"total":60,"edges":len(edges)}}
    if args.save:
        (DIR/"VALIDATION.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"pass":out["pass"],"failed":issues,"counts":out["node_counts"],
                     "checks":len(checks),"strict":args.strict_authority},ensure_ascii=False))
    if issues:raise SystemExit(1)
if __name__=="__main__":main()
