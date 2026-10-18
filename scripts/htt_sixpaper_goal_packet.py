#!/usr/bin/env python3
"""Print bounded, source-linked research goals. Does not execute or admit results."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import htt_publication_dag as publication

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs/research_program/observational_publication_20261015/CONTINUATION_20261018/EXECUTION_GOALS.json"


def packets(doc, goals):
    publication.validate(doc)
    if goals.get("schema") != "htt.sixpaper_execution_goals/1":
        raise ValueError("unknown goal schema")
    nodes = {n["id"]: n for n in doc["nodes"]}
    rows = goals.get("nodes", [])
    if len(rows) != len(nodes) or {n["id"] for n in rows} != set(nodes):
        raise ValueError("goal file must cover each canonical node exactly once")
    out = []
    for row in rows:
        node = nodes[row["id"]]
        for key in ("acceptance", "depends_on"):
            if row[key] != node[key]:
                raise ValueError(f"stale goal contract: {node['id']}.{key}; refresh from current canonical DAG")
        item = dict(row)
        # Current state, blockers and evidence always come from the live DAG.
        item.update(status=publication.resolved_status(node, nodes),
                    external_missing=node["external_missing"],
                    canonical_evidence=node["existing_evidence"])
        item["unfinished_prerequisites"] = [d for d in node["depends_on"]
                                           if nodes[d]["state"] != "completed_scoped"]
        item["completion_is_automatic"] = False
        out.append(item)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag", type=Path, default=publication.DAG)
    parser.add_argument("--goals", type=Path, default=DEFAULT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task")
    group.add_argument("--ready", action="store_true")
    group.add_argument("--frontier", action="store_true")
    args = parser.parse_args()
    rows = packets(publication.load(args.dag), json.loads(args.goals.read_text()))
    if args.task:
        selected = [r for r in rows if r["id"] == args.task]
        if not selected:
            raise ValueError("unknown task ID")
    elif args.ready:
        selected = [r for r in rows if r["status"] == "ready"]
    else:
        selected = [{k:r[k] for k in ("id", "paper", "status", "goal", "external_missing",
                                    "unfinished_prerequisites", "preparation_or_reuse")}
                    for r in rows if r["status"] != "completed_scoped"]
    print(json.dumps({"automatic_execution":False, "tasks":selected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"GOAL_PACKET_ERROR: {exc}")
