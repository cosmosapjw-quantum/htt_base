#!/usr/bin/env python3
"""Compute evidence-backed six-paper DAG completion from source statuses.

A completed_scoped node is a bounded result, not a physical detection or
manuscript acceptance. Never edits any scientific DAG or program state.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from htt_publication_dag import DAG,load,resolved_status

ORDER=("COMMON","P1","P2","P3","P4","P5","P6")
STATES=("completed_scoped","ready","blocked_external","waiting_dependencies")


def report(doc):
    nodes=doc["nodes"]
    lookup={z["id"]:z for z in nodes}
    totals={name:{s:0 for s in STATES} for name in ORDER}
    for item in nodes:
        totals[item["paper"]][resolved_status(item,lookup)]+=1
    per={}
    for name in ORDER:
        row=totals[name]
        total=sum(row.values())
        if not total:
            raise ValueError(f"empty task group {name}")
        per[name]={
          "total":total,
          "completed_scoped":row["completed_scoped"],
          "ready":row["ready"],
          "external_missing":row["blocked_external"],
          "waiting_dependencies":row["waiting_dependencies"],
          "completion_fraction":row["completed_scoped"]/total
        }
    count={
      "completed_scoped":sum(per[z]["completed_scoped"] for z in ORDER),
      "ready":sum(per[z]["ready"] for z in ORDER),
      "external_missing":sum(per[z]["external_missing"] for z in ORDER),
      "waiting_dependencies":sum(per[z]["waiting_dependencies"] for z in ORDER)
    }
    if sum(count.values())!=len(nodes):
        raise ValueError("publication task states fail to partition the DAG")
    if {p["id"] for p in doc["papers"]}!=set(ORDER[1:]):
        raise ValueError("six scientific paper programs required")
    gates=[z for z in nodes if z.get("submission_terminal")]
    passed=sum(z["state"]=="completed_scoped" for z in gates)
    if len(gates)!=6 or any(p["publication_status"]!="NOT_READY_TO_SUBMIT"
                             for p in doc["papers"]):
        raise ValueError("manuscript readiness cannot be inherited from plans")
    return {
      "schema":"htt.publication_DAG_evidence_progress/1",
      "research_date":"2026-10-15",
      "all_task_nodes":len(nodes),
      "completed_scoped_nodes":count["completed_scoped"],
      "completed_scoped_fraction":count["completed_scoped"]/len(nodes),
      "completed_scoped_percent":100*count["completed_scoped"]/len(nodes),
      "ready_nodes":count["ready"],
      "blocked_external_nodes":count["external_missing"],
      "waiting_dependency_nodes":count["waiting_dependencies"],
      "scoped_progress_by_track":per,
      "manuscript_submission_gates_passed":passed,
      "manuscript_submission_gates_total":6,
      "manuscript_status":"0/6: NOT_READY_TO_SUBMIT",
      "pending_scientific_claims_are_not_node_completion":True,
      "note":"Partial numerical work on pending paper tasks does not increase percent",
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dag",type=Path,default=DAG)
    ap.add_argument("--write",type=Path,default=None)
    args=ap.parse_args()
    value=report(load(args.dag))
    result=json.dumps(value,indent=2,ensure_ascii=False)+"\n"
    if args.write is not None:
        if args.write.exists():
            raise FileExistsError("progress output create-only; preserve old snapshots")
        args.write.parent.mkdir(parents=True,exist_ok=True)
        args.write.write_text(result,encoding="utf-8")
    print(result,end="")


if __name__=="__main__":
    main()
