#!/usr/bin/env python3
"""Bind the whole original science DAG and authored new frontier to the controller."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from native_routing import load_policy
from research_controller import (ControllerError, bind_original_contracts, digest,
                                 initialize, next_packet, require, save, summary)


def build_campaign(dag: dict, plan: dict, frontier: dict, source_identity: dict | None = None) -> dict:
    """Preserve original acceptance and add explicit action-enabling edges only."""
    require(frontier.get("campaign_id"), "authored frontier campaign_id required")
    nodes = {n["id"]: n for n in dag["nodes"]}
    originals = {n["id"]: n for n in plan["all_original_nodes"]}
    actions = copy.deepcopy(frontier.get("actions", []))
    require(actions, "new authored frontier actions required; do not replay frozen campaigns")
    action_ids = [a["id"] for a in actions]
    require(len(action_ids) == len(set(action_ids)), "duplicate frontier action")
    prior_routes = {t["id"]: t for t in plan.get("tasks", []) + plan.get("frontier_actions", [])}
    prior_ids = set(prior_routes)
    require(not (set(action_ids) & (set(nodes) | prior_ids)), "frontier reopens an original/frozen campaign ID")
    source_identity = source_identity or {"dag_json_sha256": digest(dag), "plan_json_sha256": digest(plan)}
    repairs = frontier.get("original_node_repairs", {})
    approved = frontier.get("approved_scientific_repairs", [])
    require(set(repairs) <= set(nodes) and all(repair in approved for repair in repairs.values()),
            "original scientific repair IDs must name original nodes and approved campaign repairs")
    enables = {key: [] for key in nodes}
    for action in actions:
        require(action.get("kind") in {"theory", "numeric", "code", "input"}, "explicit frontier kind required")
        require(action.get("initial_state", "ready") == "ready" and action.get("status", "ready") == "ready",
                "authored frontier must contain new ready actions, not replayed completed campaigns")
        for key in action.get("enables_nodes", []):
            require(key in nodes, "frontier enables unknown original node")
            require(nodes[key]["state"] != "completed_scoped", "frontier cannot reopen completed original science")
            enables[key].append(action["id"])
        action["contract_origin"] = "authored_new_frontier"
        action["source_frontier_identity"] = digest(frontier)
    tasks = []
    for key, node in nodes.items():
        require(key in originals, "original science absent from continuation plan")
        original = originals[key]
        complete = node["state"] == "completed_scoped"
        evidence = node.get("existing_evidence", [])
        if complete:
            require(original.get("intake_state") == "completed_scoped" and evidence
                    and all(isinstance(ref, str) and ref.strip() for ref in evidence),
                    "completed original lacks source-bound node/plan evidence: " + key)
        external = copy.deepcopy(node.get("external_missing", []))
        require(set(original.get("input_routes", [])) <= prior_ids, "unknown original input route: " + key)
        kind = "input" if external else "theory"
        dependencies = list(node["depends_on"]) + enables[key]
        task = {"id": key, "goal": node.get("objective", original.get("goal", key)),
                "acceptance": node["acceptance"], "depends_on": dependencies,
                "original_depends_on": copy.deepcopy(node["depends_on"]),
                "input_identity": "sha256:" + digest({"source": source_identity, "node": node, "plan_node": original}),
                "kind": kind, "owned_paths": copy.deepcopy(node.get("planned_code", [])),
                "external_missing": external, "external_inputs": copy.deepcopy(original.get("external_inputs", [])),
                "input_routes": copy.deepcopy(original.get("input_routes", [])),
                "input_route_contracts": [copy.deepcopy(prior_routes[route]) for route in original.get("input_routes", [])],
                "source_node": copy.deepcopy(node), "source_plan_node": copy.deepcopy(original),
                "contract_origin": "original_science", "initial_state": "completed" if complete else "ready",
                "next_action": node.get("next_action"), "claim_tier": node.get("claim_tier"),
                "execution_instruction": (
                    "Reuse source-bound accepted scope; do not replay completed campaigns." if complete else
                    "Resolve the exact remaining scientific/input obligation using the source node, mapped input routes, "
                    "and reviewed enabling actions. Acquire/research public inputs before declaring a true external hold. "
                    "Preserve original acceptance, conditional boundaries, no-native/no-ODE and no-submission policy. "
                    "A scoped diagnostic or reviewed enabling action is not this original node's acceptance.")}
        if key in repairs:
            task["approved_repair_id"] = repairs[key]
        if complete:
            task["reuse_evidence"] = {"source_identity": copy.deepcopy(source_identity),
                                      "node_identity": digest(node), "plan_node_identity": digest(original),
                                      "existing_evidence": copy.deepcopy(evidence),
                                      "scope": "source-recorded completed_scoped; not newly revalidated"}
        tasks.append(task)
    campaign = {"campaign_id": frontier["campaign_id"], "tasks": tasks + actions,
                "approved_scientific_repairs": copy.deepcopy(frontier.get("approved_scientific_repairs", [])),
                "source_identity": copy.deepcopy(source_identity), "authored_frontier": copy.deepcopy(frontier),
                "frontier_action_ids": action_ids, "whole_original_dag": True,
                "execution_policy": copy.deepcopy(plan.get("policy", {})),
                "initial_priority_rule": "builder initializes frontier last_turn=-len(actions)-1+index in authored order; original nodes=-1"}
    campaign = bind_original_contracts(campaign, dag, plan)
    # Validate augmented dependencies/cycles without claiming authorization or persisting a state.
    initialize(campaign, "builder validation only; not execution authorization")
    return campaign


def initialize_whole_campaign(campaign: dict, authorization: str) -> dict:
    state = initialize(campaign, authorization)
    actions = campaign["frontier_action_ids"]
    for index, key in enumerate(actions):
        state["tasks"][key]["last_turn"] = -len(actions) - 1 + index
    state["events"].append({"type": "whole_dag_bound", "source_identity": campaign["source_identity"],
                            "frontier_identity": digest(campaign["authored_frontier"]),
                            "original_task_count": len(campaign["original_science_contract"]["nodes"])})
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dag", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--frontier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--authorization", default="")
    parser.add_argument("--next", action="store_true", dest="emit_next")
    parser.add_argument("--available-profile", action="append", default=[])
    parser.add_argument("--policy", type=Path)
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "refusing to overwrite a frozen campaign output")
        require(not args.state or not args.state.exists(), "refusing to overwrite existing controller state")
        require(not args.emit_next or args.state, "--next requires --state")
        docs = {key: path.read_bytes() for key, path in {"dag": args.dag, "plan": args.plan, "frontier": args.frontier}.items()}
        campaign = build_campaign(json.loads(docs["dag"]), json.loads(docs["plan"]), json.loads(docs["frontier"]),
                                  {key + "_file_sha256": hashlib.sha256(value).hexdigest() for key, value in docs.items()})
        state = initialize_whole_campaign(campaign, args.authorization) if args.state else None
        output = {"campaign_id": campaign["campaign_id"], "tasks": len(campaign["tasks"]),
                  "original_nodes": len(campaign["original_science_contract"]["nodes"]),
                  "frontier_actions": campaign["frontier_action_ids"], "campaign_identity": digest(campaign)}
        if state is not None:
            if args.emit_next:
                profiles = set()
                for raw in args.available_profile:
                    model, sep, effort = raw.rpartition("/")
                    require(sep and model and effort, "expected MODEL/EFFORT")
                    profiles.add((model, effort))
                output = next_packet(state, load_policy(args.policy) if args.policy else load_policy(), profiles)
            else:
                output = summary(state)
        save(args.output, campaign)
        if state is not None:
            save(args.state, state)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ControllerError, ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
