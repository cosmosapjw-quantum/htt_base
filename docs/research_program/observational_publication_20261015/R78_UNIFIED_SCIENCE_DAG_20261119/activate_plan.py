#!/usr/bin/env python3
"""One-way, guarded R78 science SSOT activation, preserving original 42 nodes.

Historical GitHub PR status and 291-entry software PR backlog are NOT modified.
Activation is not a research claim promotion or main-branch merge.
"""
from pathlib import Path
import hashlib,json
import yaml

PUB=Path("docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json")
OUT=Path("docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119")
DAG=OUT/"INTEGRATED_DAG.json"
AG=Path("AGENTS.md")
EXPECTED="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"

def sha_nodes(nodes):
    return hashlib.sha256(json.dumps(nodes,sort_keys=True).encode()).hexdigest()

def main():
    pub=json.loads(PUB.read_text())
    plan=json.loads(DAG.read_text())
    assert plan["revision"] in (2,3) and plan["count_total_graph_nodes"]==60
    assert len(pub["nodes"])==42 and sha_nodes(pub["nodes"])==EXPECTED==plan["original_42_payload_sha256"]
    assert len(yaml.safe_load(Path("docs/codex_handoff/pr_backlog.yaml").read_text())["prs"])==291
    before_nodes=json.dumps(pub["nodes"],sort_keys=True)
    before_papers=json.dumps(pub["papers"],sort_keys=True)
    previous=pub["current_scientific_route"]
    if previous.get("research_dag")==str(DAG):
        assert pub["current_integrated_science_dag"]["path"]==str(DAG)
        desired_sha=hashlib.sha256(DAG.read_bytes()).hexdigest()
        if pub["current_integrated_science_dag"]["sha256"]!=desired_sha:
            pub["current_integrated_science_dag"]["sha256"]=desired_sha
            pub["current_integrated_science_dag"]["revision"]=plan["revision"]
            pub["current_integrated_science_dag"]["inherited_regression_receipt"]=str(OUT/"REGRESSION_RECEIPT.json")
            pub["current_scientific_route"]["inherited_regression_receipt"]=str(OUT/"REGRESSION_RECEIPT.json")
            PUB.write_text(json.dumps(pub,ensure_ascii=False,indent=2)+"\n")
            print("R78_SCIENCE_AUTHORITY_REVISION_SHA_REFRESHED",plan["revision"])
        else:
            print("R78_SCIENCE_AUTHORITY_ALREADY_ACTIVATED")
        return
    assert previous.get("canonical_pr")=="PR-R66-LOWELL-PHYSICAL-OBSERVABLES",previous
    prior=pub.get("previous_scientific_routes",[])
    assert not any(x.get("canonical_pr")==previous["canonical_pr"] for x in prior)
    prior.append(previous)
    pub["previous_scientific_routes"]=prior
    pub["historical_next_action_before_R78"]=pub["next_action"]
    pub["next_action"]="R78 Unified science DAG: NEXT_ID=SQ-CF4; source-match 35,970 selected CF4 groups, indicator/PV/selection calibration, with heldout source-conditioned validation; do not auto-promote H04 or physical anisotropy."
    pub["current_scientific_route"]={
        "date":"2026-11-19",
        "source_base_sha":"dd857ff8decbcfe90fd566a9dd87dcf5be60f609",
        "canonical_pr":None,
        "science_task_id":"R78-UNIFIED-DAG",
        "selected_paper":"P1-P6_AND_PHY01-07",
        "scope":"Single active unified science research DAG from R60-R77; 42 immutable scientific goals plus 11 qualification work packages and 7 conditional PHY physical routes.",
        "status":"UNIFIED_PLAN_VALIDATED_SOURCE_GATES_PENDING",
        "report":str(OUT/"RESEARCH_PLAN_KO.md"),
        "plan":str(OUT/"RESEARCH_PLAN_KO.md"),
        "research_dag":str(DAG),
        "active_result":str(OUT/"VALIDATION.json"),
        "review":str(OUT/"ADVERSARIAL_REVIEW.md"),
        "next_id":"SQ-CF4",
        "original_six_tracks_and_42_gates_preserved":True,
        "publication_claim_gate":"NOT_READY_TO_SUBMIT",
        "submission_status":"NOT_READY_TO_SUBMIT",
        "github_pr_created":False,
        "automatic_successor":False,
        "local_agent_prompt_created":False
    }
    pub["current_integrated_science_dag"]={
        "schema":"htt.r78.active_science_authority/1",
        "path":str(DAG),
        "plan":str(OUT/"RESEARCH_PLAN_KO.md"),
        "diagram_overview":str(OUT/"PLAN_OVERVIEW.svg"),
        "diagram_full":str(OUT/"PLAN_FULL.svg"),
        "source_census":str(OUT/"SOURCE_CENSUS.json"),
        "review":str(OUT/"ADVERSARIAL_REVIEW.md"),
        "validation":str(OUT/"VALIDATION.json"),
        "sha256":hashlib.sha256(DAG.read_bytes()).hexdigest(),
        "original_42_node_payload_sha256":EXPECTED,
        "science_node_count":42,
        "source_qualifier_count":11,
        "physical_cross_route_count":7,
        "graph_node_count":60,
        "graph_edge_count":129,
        "next_id":"SQ-CF4",
        "software_PR_authority":"docs/codex_handoff/pr_backlog.yaml",
        "software_PR_current_entries":291,
        "software_PR_baseline_historical_entries":245,
        "original_status_unchanged":True,
        "no_auto_native_solver_or_claim_promotion":True
    }
    assert json.dumps(pub["nodes"],sort_keys=True)==before_nodes
    assert json.dumps(pub["papers"],sort_keys=True)==before_papers
    PUB.write_text(json.dumps(pub,ensure_ascii=False,indent=2)+"\n")
    agents=AG.read_text()
    marker="## Existing-checkout policy (owner reaffirmed 2026-10-14)"
    assert marker in agents
    assert "## Active unified science-program DAG (owner, 2026-11-19)" not in agents
    note="""## Active unified science-program DAG (owner, 2026-11-19)

- **For P1–P6 scientific research sequencing**, the one current science SSOT is docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json, with RESEARCH_PLAN_KO.md, SOURCE_CENSUS.json, ADVERSARIAL_REVIEW.md and VALIDATION.json in the same folder. Read its NEXT_ID and exact HEAD first. This authority supersedes older R60–R77 narrative next-action pointers, not their evidence.
- The **original 42 scientific publication gates/acceptance texts and states** in PUBLICATION_DAG.json remain immutable, canonical sorted-json node SHA256 e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d. R78 adds 11 qualified source/physics work packages and 7 conditional cross-paper PHY research routes, not 18 accepted new papers or independent likelihoods.
- The separate **software PR SSOT** remains docs/codex_handoff/pr_backlog.yaml and machine_readable/pr_backlog.yaml mirror, 291 entries as of this plan; the PUBLICATION_DAG historical 245 baseline is not current. Do not merge the two DAG populations, change existing PR statuses, or infer GitHub PR merge from source-branch ancestry.
- Default next bounded science work is **SQ-CF4**, exact selected 35,970-group CF4 indicator/PV/selection covariance with provenance and heldout check. If missing, record precise blocked source and choose SQ-GAIA. No forced physical expansion/tilt detection, no new native low-ell Bianchi solver, no automatic next-loop or main merge.

"""
    agents=agents.replace(marker,note+marker,1)
    AG.write_text(agents)
    print("R78_SCIENCE_AUTHORITY_ACTIVATED","prior",previous["canonical_pr"],
          "42_payload_sha",sha_nodes(pub["nodes"]),"PR_backlog_untouched_291",True)

if __name__=="__main__": main()
