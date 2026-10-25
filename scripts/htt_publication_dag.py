#!/usr/bin/env python3
"""Validate and select HTT six-paper observational publication tasks.

This command never changes tasks, runs physics, submits manuscripts, creates PRs
or merges branches. The explicit --export option writes a derived ready queue.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

DAG = Path(__file__).resolve().parents[1] / "docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json"
SCHEMA = "htt.observational_six_paper_dag/1"
PAPERS = ("P1","P2","P3","P4","P5","P6")
STATES = frozenset(("completed_scoped","pending","blocked_input"))


class PublicationDAGError(ValueError):
    pass


def validate(doc):
    if not isinstance(doc,dict) or doc.get("schema")!=SCHEMA:
        raise PublicationDAGError("invalid publication DAG schema")
    papers=doc.get("papers")
    nodes=doc.get("nodes")
    if not isinstance(papers,list) or not isinstance(nodes,list):
        raise PublicationDAGError("paper and node lists required")
    pids=[p.get("id") for p in papers]
    if len(pids)!=6 or len(set(pids))!=6 or set(pids)!=set(PAPERS):
        raise PublicationDAGError("exactly six unique publication tracks required")
    if sorted(p.get("priority") for p in papers)!=list(range(1,7)):
        raise PublicationDAGError("unique paper priority 1..6 required")
    for p in papers:
        if p.get("publication_status")!="NOT_READY_TO_SUBMIT":
            raise PublicationDAGError("planning cannot certify submission readiness")
        for k in ("title","question","estimands","minimum_publishable_result","principal_blocker","submission_gate"):
            if not isinstance(p.get(k),str) or not p[k].strip():
                raise PublicationDAGError(f"missing paper field {p['id']}.{k}")
    ids=[n.get("id") for n in nodes]
    if len(ids)!=len(set(ids)) or any(not isinstance(i,str) or not i for i in ids):
        raise PublicationDAGError("duplicate or blank task IDs")
    byid={n["id"]:n for n in nodes}
    for n in nodes:
        key=n["id"]
        if n.get("paper") not in (*PAPERS,"COMMON"):
            raise PublicationDAGError(f"unknown track in {key}")
        if n.get("state") not in STATES:
            raise PublicationDAGError(f"unknown status in {key}")
        deps=n.get("depends_on")
        if not isinstance(deps,list) or len(deps)!=len(set(deps)):
            raise PublicationDAGError(f"duplicate dependencies in {key}")
        if key in deps or any(x not in byid for x in deps):
            raise PublicationDAGError(f"self or unknown dependency in {key}")
        if not isinstance(n.get("external_missing"),list):
            raise PublicationDAGError(f"invalid missing input in {key}")
        for k in ("objective","output","acceptance","next_action"):
            if not isinstance(n.get(k),str) or not n[k].strip():
                raise PublicationDAGError(f"missing task field {key}.{k}")
        if n["state"]=="completed_scoped" and (not n.get("existing_evidence") or n["external_missing"]):
            raise PublicationDAGError(f"unverified completion in {key}")
        if n["state"]=="completed_scoped":
            if any(byid[d]["state"]!="completed_scoped" for d in deps):
                raise PublicationDAGError(f"unfinished prerequisite for {key}")
            if n.get("submission_terminal"):
                decision=n.get("publication_decision")
                if (not isinstance(decision,dict)
                    or decision.get("outcome") not in ("HOLD","READY_FOR_OWNER_REVIEW")
                    or decision.get("submitted") is not False
                    or not isinstance(decision.get("evidence"),list)
                    or not decision["evidence"]
                    or any(not isinstance(e,str) or not e.strip() for e in decision["evidence"])):
                    raise PublicationDAGError("terminal completion requires an evidenced decision without submission")
    active,done=set(),set()
    def visit(key):
        if key in done:return
        if key in active:raise PublicationDAGError(f"cycle at {key}")
        active.add(key)
        for before in byid[key]["depends_on"]:visit(before)
        active.remove(key)
        done.add(key)
    for key in byid:visit(key)
    for paper in PAPERS:
        terminals=[x for x in nodes if x["paper"]==paper and x.get("submission_terminal")]
        if len(terminals)!=1 or not terminals[0]["depends_on"]:
            raise PublicationDAGError(f"exactly one dependent publication gate for {paper}")
    return {"schema":SCHEMA,"paper_count":len(papers),"node_count":len(nodes),
            "reused_evidence_anchors":sum(x["state"]=="completed_scoped" for x in nodes),
            "new_tasks":sum(x["state"]!="completed_scoped" for x in nodes),
            "external_missing_nodes":sum(bool(x["external_missing"]) for x in nodes),
            "submission_gates":sum(bool(x.get("submission_terminal")) for x in nodes)}


def load(path=DAG):
    obj=json.loads(Path(path).read_text())
    validate(obj)
    return obj


def resolved_status(node,byid):
    if node["state"]=="completed_scoped":return "completed_scoped"
    if node["state"]=="blocked_input" or node["external_missing"]:return "blocked_external"
    if all(byid[d]["state"]=="completed_scoped" for d in node["depends_on"]):return "ready"
    return "waiting_dependencies"


def ready(doc,paper=None):
    validate(doc)
    lookup={z["id"]:z for z in doc["nodes"]}
    order={p["id"]:p["priority"] for p in doc["papers"]}
    result=[{"id":z["id"],"paper":z["paper"],"objective":z["objective"],"output":z["output"]}
        for z in doc["nodes"] if (paper is None or z["paper"]==paper)
        and resolved_status(z,lookup)=="ready"]
    return sorted(result,key=lambda x:(order.get(x["paper"],0),x["id"]))


def blocked(doc):
    validate(doc)
    lookup={z["id"]:z for z in doc["nodes"]}
    return [{"id":z["id"],"paper":z["paper"],"missing":z["external_missing"]}
            for z in doc["nodes"] if resolved_status(z,lookup)=="blocked_external"]


def task_packet(doc,key):
    validate(doc)
    lookup={z["id"]:z for z in doc["nodes"]}
    if key not in lookup:raise PublicationDAGError(f"unknown task {key}")
    node=lookup[key]
    paper=next((p for p in doc["papers"] if p["id"]==node["paper"]),None)
    return {"schema":"htt.publication_task_packet/1","task":node,
            "status":resolved_status(node,lookup),"paper":paper,
            "direct_prerequisites":[{"id":dep,"status":lookup[dep]["state"],
                                     "evidence":lookup[dep]["existing_evidence"]}
                                    for dep in node["depends_on"]],
            "scientific_limits":doc["policy"],"mutation":"No original dirty checkout changes"}


def derived_queue(doc):
    validate(doc)
    content=json.dumps(doc,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return {"schema":"htt.observational_ready_queue/1",
            "input_content_sha256":hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "ready":ready(doc),"external_blockers":blocked(doc),
            "scientific_claim":"NOT_READY_TO_SUBMIT","background_scheduler":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag",type=Path,default=DAG)
    opts=parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--validate",action="store_true")
    opts.add_argument("--ready",action="store_true")
    opts.add_argument("--blocked",action="store_true")
    opts.add_argument("--paper",choices=PAPERS)
    opts.add_argument("--task")
    opts.add_argument("--export",action="store_true")
    args=parser.parse_args()
    doc=load(args.dag)
    if args.validate:
        payload=validate(doc);payload["ready_now"]=len(ready(doc))
    elif args.ready:
        payload={"ready":ready(doc)}
        if doc.get("publication_output_route_20261025"):
            payload["additional_publication_route"]=doc["publication_output_route_20261025"]
            payload["route_note"]="Read-only pointer; append with the existing controller after preflight. Original ready list is unchanged."
    elif args.blocked:payload={"blocked":blocked(doc)}
    elif args.paper:
        paper=next(p for p in doc["papers"] if p["id"]==args.paper)
        lookup={z["id"]:z for z in doc["nodes"]}
        payload={"paper":paper,"nodes":[{"id":z["id"],"status":resolved_status(z,lookup),
                                        "depends_on":z["depends_on"],"missing":z["external_missing"]}
            for z in doc["nodes"] if z["paper"]==args.paper]}
    elif args.task:payload=task_packet(doc,args.task)
    else:
        payload=derived_queue(doc)
        out=args.dag.parent/"READY_QUEUE.json"
        out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
        payload={"ready_count":len(payload["ready"]),
                 "external_blocker_count":len(payload["external_blockers"]),
                 "export":str(out)}
    print(json.dumps(payload,indent=2,ensure_ascii=False))


if __name__=="__main__":
    try:main()
    except (PublicationDAGError,OSError,ValueError) as exc:
        raise SystemExit(f"PUBLICATION_DAG_ERROR: {exc}")

