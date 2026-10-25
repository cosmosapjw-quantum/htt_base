#!/usr/bin/env python3
"""Durable host-driven research state machine; never launches native workers itself."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any
from urllib.parse import urlsplit

from native_routing import load_policy, resolve_route


class ControllerError(ValueError):
    """An unverified transition must not advance the campaign."""


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ControllerError(message)


def initialize(campaign: dict, authorization: str) -> dict:
    """Freeze a reviewed campaign, including explicit current owner authorization."""
    require(authorization.strip(), "current user authorization required")
    require(campaign.get("campaign_id"), "campaign_id required")
    rows = campaign.get("tasks", [])
    require(rows, "nonempty task DAG required")
    ids = [t["id"] for t in rows]
    require(len(ids) == len(set(ids)), "duplicate task ID")
    for t in rows:
        require(t.get("goal") and t.get("acceptance") and t.get("input_identity"),
                "goal, frozen acceptance and input_identity required")
        require(t.get("kind", "code") in {"theory", "numeric", "code", "input"}, "invalid task kind")
        require(t.get("implementation_route", "subagent_specialist") in {
            "subagent_specialist", "subagent_routine", "general_code", "routine_mechanical"},
            "implementation route cannot bypass research/escalation/review state gates")
        require(set(t.get("depends_on", [])) <= set(ids), "unknown dependency")
        require(not t.get("prohibited_operation"), "prohibited operation in campaign")
        require(t.get("initial_state", "ready") in {"ready", "completed"}, "invalid initial state")
        contributors = t.get("contributors", [])
        require(isinstance(contributors, list) and all(isinstance(agent, str) and agent.strip() for agent in contributors),
                "declared contributors must be a list of actual nonempty agent IDs")
        if t.get("initial_state") == "completed":
            require(t.get("reuse_evidence"), "completed reuse needs evidence; counts are not evidence")
    visiting, visited = set(), set()
    by_id = {t["id"]: t for t in rows}
    def visit(key):
        require(key not in visiting, "dependency cycle")
        if key in visited:
            return
        visiting.add(key)
        for dep in by_id[key].get("depends_on", []):
            visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in ids:
        visit(key)
    tasks = {}
    for t in rows:
        phase = "acquisition" if t.get("kind") == "input" else "execute"
        tasks[t["id"]] = {"spec": copy.deepcopy(t), "state": t.get("initial_state", "ready"),
                          "phase": phase, "attempt": 0, "history": [], "failures": [],
                          "ultra_used": [], "authors": [],
                          "contributors": list(dict.fromkeys(t.get("contributors", []))), "last_turn": -1}
    return {"schema": "htt.continuous_research_controller/1", "campaign_id": campaign["campaign_id"],
            "campaign_identity": digest(campaign), "campaign": copy.deepcopy(campaign),
            "authorization": authorization, "tasks": tasks, "turn": 0, "events": [], "packets": {},
            "ultra_repairs": {}, "ultra_pending": {}}


def bind_original_contracts(campaign: dict, dag: dict, plan: dict) -> dict:
    """Bind unchanged source science; controller task completion cannot rewrite it."""
    nodes = {n["id"]: n for n in dag["nodes"]}
    originals = {n["id"]: n for n in plan["all_original_nodes"]}
    require(len(nodes) == len(dag["nodes"]) and len(originals) == len(plan["all_original_nodes"]),
            "duplicate original science node")
    require(nodes.keys() == originals.keys(), "scientific inventory changed")
    visiting, visited = set(), set()
    def visit(key):
        require(key in nodes, "unknown original scientific dependency")
        require(key not in visiting, "original scientific dependency cycle")
        if key in visited:
            return
        visiting.add(key)
        for dep in nodes[key]["depends_on"]:
            visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in nodes:
        visit(key)
    for key, node in nodes.items():
        require(node["acceptance"] == originals[key]["acceptance"] and
                node["depends_on"] == originals[key]["depends_on"],
                "original science acceptance/dependencies changed: " + key)
    bound = copy.deepcopy(campaign)
    bound["original_science_contract"] = copy.deepcopy(dag)
    bound["continuation_plan_identity"] = digest(plan)
    return bound


def _semantic_delta(delta: dict) -> None:
    """Require a discriminating change, rather than an assignment seal change."""
    require(isinstance(delta, dict) and delta.get("kind") in {
        "input", "method", "assumption", "validation_counterexample", "prelaunch_transport"},
        "typed semantic evidence required")
    require(isinstance(delta.get("before"), dict) and isinstance(delta.get("after"), dict)
            and delta.get("discriminator") and delta.get("scope"),
            "semantic before/after objects, discriminator and scope required")
    require(_semantic_meaning(delta["before"]) != _semantic_meaning(delta["after"]),
            "label/hash/identity change alone is not new scientific information")


def _semantic_meaning(value):
    """Discard seals and descriptive metadata when comparing scientific meaning."""
    if isinstance(value, dict):
        administrative = {"identity", "input_identity", "source_identity", "candidate_identity",
                          "semantic_identity", "hash", "sha256", "label", "labels", "metadata",
                          "note", "notes", "name", "names", "timestamp", "timestamps",
                          "created_at", "updated_at", "comment", "comments", "display_name"}
        return {k: _semantic_meaning(v) for k, v in value.items() if k.lower() not in administrative}
    if isinstance(value, list):
        return [_semantic_meaning(v) for v in value]
    return value


def _semantic_projection(delta: dict) -> dict:
    """Only typed meaning controls replay eligibility; retain raw evidence separately."""
    projected = {key: _semantic_meaning(delta[key]) for key in
                 ("kind", "before", "after", "discriminator", "scope")}
    if delta["kind"] == "prelaunch_transport":
        projected["packet_id"] = delta.get("packet_id")
    return projected


def _obligation_refs(expr: dict) -> set[str]:
    require(isinstance(expr, dict), "obligation must be an object")
    if set(expr) in ({"all"}, {"any"}):
        op = next(iter(expr))
        children = expr[op]
        require(isinstance(children, list) and (op == "all" or children), "invalid all/any obligation")
        refs = set()
        for child in children:
            refs |= _obligation_refs(child)
        return refs
    require(set(expr) <= {"task_id", "evidence", "product"} and expr.get("task_id")
            and expr.get("evidence") in {"completed", "qualified"}, "invalid typed obligation leaf")
    require(expr["evidence"] != "qualified" or isinstance(expr.get("product"), str)
            and expr["product"].strip(), "qualified obligation needs exact product")
    return {expr["task_id"]}


def _obligation_met(expr: dict, tasks: dict) -> bool:
    if "all" in expr:
        return all(_obligation_met(child, tasks) for child in expr["all"])
    if "any" in expr:
        return any(_obligation_met(child, tasks) for child in expr["any"])
    task = tasks[expr["task_id"]]
    if task["state"] != "completed":
        return False
    if expr["evidence"] == "completed":
        return True
    return expr["product"] in task.get("qualified_products", [])


def _action_signature(spec: dict) -> str:
    # Locators, wrapper bytes and administrative metadata do not prove a new
    # scientific action. A real source/cohort change must be explicit in the
    # typed before/after meaning, assessed by the scientific research/reviewer.
    return digest({"semantic_delta": _semantic_projection(spec["semantic_delta"]),
                   "kind": spec.get("kind", "code")})


def _repair_approved(state: dict, repair_id: str | None) -> bool:
    return bool(repair_id and (repair_id in state["campaign"].get("approved_scientific_repairs", [])
                              or repair_id in state.get("repair_authorizations", {})))


def _validate_repair_binding(state: dict, repair_id: str | None, task_id: str,
                             spec: dict | None = None, issue: dict | None = None,
                             delta: dict | None = None, prospective: bool = False) -> None:
    """A registered allowance funds only its reviewed issue/target and explicit successors."""
    row = state.get("repair_authorizations", {}).get(repair_id)
    if row is None:
        return  # Historical frozen allowances retain their original semantics.
    task = state["tasks"].get(task_id, {})
    spec = spec if spec is not None else task.get("spec", {})
    issue = issue if issue is not None else task.get("issue")
    expected_delta = row["semantic_delta_identity"]
    if task_id == row["origin_task_id"]:
        require(spec.get("acceptance") == row["claim_target"], "registered repair claim target changed")
    else:
        binding = next((value for value in row.get("successor_bindings", [])
                        if value["task_id"] == task_id), None)
        require(binding is not None, "registered repair is not authorized for this origin/successor task")
        require(binding["task_spec_identity"] == digest(spec)
                and binding["claim_target"] == spec.get("acceptance")
                and binding["issue_identity"] == row["issue_identity"]
                and spec.get("semantic_delta")
                and binding["semantic_delta_identity"] == digest(_semantic_projection(spec["semantic_delta"])),
                "registered successor spec, issue, target or semantic delta changed")
        expected_delta = binding["semantic_delta_identity"]
    if not prospective:
        require(issue and _operative_issue_identity(issue) == _operative_issue_identity(row["issue"]),
                "registered repair operative issue changed")
    if delta is not None:
        require(digest(_semantic_projection(delta)) == expected_delta,
                "registered repair semantic delta changed")


def _task_repair_id(state: dict, task_id: str) -> str | None:
    task = state["tasks"][task_id]
    for key, row in reversed(list(state.get("repair_authorizations", {}).items())):
        if row["origin_task_id"] == task_id and task.get("issue") and (
                _operative_issue_identity(row["issue"]) == _operative_issue_identity(task["issue"])):
            _validate_repair_binding(state, key, task_id)
            return key
    key = task.get("active_repair_id") or task["spec"].get("approved_repair_id")
    row = state.get("repair_authorizations", {}).get(key)
    if row is not None and task.get("issue") and (
            _operative_issue_identity(task["issue"]) != _operative_issue_identity(row["issue"])):
        # Preserve an actual newly observed defect, but do not fund it with this
        # issue's allowance. Foreign task/claim/spec bindings still fail closed.
        _validate_repair_binding(state, key, task_id, prospective=True)
        return None
    _validate_repair_binding(state, key, task_id,
                            prospective=not task.get("issue") and task["phase"] in {"execute", "acquisition"})
    return key


def _operative_issue_identity(issue: dict) -> str:
    # Risk labels and administrative changes cannot replenish the same operative defect.
    return digest({key: _semantic_meaning(issue.get(key)) for key in
                   ("class", "question", "exact_missing_or_defect", "input_sources", "counterexample")})


def _bound_repair_issues(state: dict) -> set[str]:
    """Read issue-level allowance bindings without attributing later task defects."""
    bound = {_operative_issue_identity(row["issue"])
             for row in state.get("repair_authorizations", {}).values()}
    for allowance in [*state["ultra_pending"].values(), *state["ultra_repairs"].values()]:
        if allowance.get("operative_issue_identity"):
            bound.add(allowance["operative_issue_identity"])
            continue
        task = state["tasks"].get(allowance.get("task_id"), {})
        history = task.get("history", [])
        trigger = allowance.get("trigger_packet")
        if trigger:
            issue = next((event.get("result", {}).get("issue") for event in history
                          if event["packet_id"] == trigger), None)
            if issue:
                bound.add(_operative_issue_identity(issue))
                continue
        packet_id = allowance.get("packet_id") or trigger
        packet = state["packets"].get(packet_id, {})
        # Historical escalation packets already delivered the operative issue in
        # their identity-bound JSON assignment. Do not rewrite those packets.
        message = packet.get("spawn_args", {}).get("message", "")
        if packet.get("phase") == "escalation" and "Assignment:\n" in message:
            try:
                assignment = json.loads(message.rsplit("Assignment:\n", 1)[1])
                if (assignment.get("packet_id") == packet_id
                        and assignment.get("task_id") == allowance.get("task_id")
                        and assignment.get("issue")):
                    bound.add(_operative_issue_identity(assignment["issue"]))
                    continue
            except (ValueError, TypeError):
                pass
        # Fallback for old receipts: inspect only history preceding the actual
        # escalation outcome, or the still-current acknowledged packet.
        cutoff = next((index for index, event in enumerate(history)
                       if event["packet_id"] == packet_id), None)
        if cutoff is None and task.get("packet_id") == packet_id:
            cutoff = len(history)
        if cutoff is not None:
            issue = next((event.get("result", {}).get("issue") for event in reversed(history[:cutoff])
                          if event.get("result", {}).get("issue", {}).get("class")
                          in {"theory", "numeric", "code"}), None)
            if issue:
                bound.add(_operative_issue_identity(issue))
    return bound


def authorize_repair(state: dict, authorization: dict, user_authorization: str) -> None:
    """Append a distinct issue allowance; never replenish a historical repair alias."""
    require(user_authorization.strip(), "current scoped user authorization required")
    require(state["campaign_identity"] == digest(state["campaign"]), "campaign identity changed")
    key = authorization.get("repair_id")
    require(isinstance(key, str) and key.strip() and not _repair_approved(state, key)
            and key not in state["ultra_repairs"] and key not in state["ultra_pending"],
            "repair ID already approved, consumed or reserved")
    require(authorization.get("cumulative_budget_link") == state["campaign_identity"],
            "repair must link the existing cumulative campaign budget")
    issue = authorization.get("issue")
    require(isinstance(issue, dict) and issue.get("class") in {"theory", "numeric", "code"}
            and issue.get("question") and issue.get("exact_missing_or_defect")
            and authorization.get("scope") and authorization.get("operative_question") == issue["question"],
            "distinct operative scientific issue and scope required")
    signature = digest(_semantic_meaning(issue))
    require(authorization.get("issue_identity") == signature, "issue identity must bind scientific meaning")
    origin_id = authorization.get("origin_task_id")
    require(origin_id in state["tasks"], "exact predecessor task required")
    origin = state["tasks"][origin_id]
    origin_issues = [event.get("result", {}).get("issue") for event in origin.get("history", [])]
    origin_issues.append(origin.get("issue"))
    origin_issues = [value for value in origin_issues if value]
    require(any(digest(_semantic_meaning(value)) == authorization.get("origin_issue_identity")
                for value in origin_issues), "stale predecessor issue binding")
    require(authorization.get("claim_target") == origin["spec"]["acceptance"],
            "repair must bind the predecessor's unchanged claim target")
    delta = authorization.get("semantic_delta")
    _semantic_delta(delta)
    require(delta["kind"] != "prelaunch_transport" and delta["scope"] == authorization["scope"],
            "bounded scientific repair delta and matching scope required")
    # Wording a question differently is not itself an operative change.
    def operative(value):
        if isinstance(value, dict):
            return {key: operative(item) for key, item in _semantic_meaning(value).items()
                    if key not in {"question", "operative_question", "exact_missing_or_defect", "description", "risk"}}
        if isinstance(value, list):
            return [operative(item) for item in value]
        return value
    require(operative(delta["before"]) != operative(delta["after"]),
            "question/defect wording alone cannot authorize a new repair")
    delta_identity = digest(_semantic_projection(delta))
    previous = list(state.get("repair_authorizations", {}).values())
    require(not any(row.get("semantic_delta_identity") == delta_identity for row in previous),
            "repair semantic evidence already authorized")
    issue_key = _operative_issue_identity(issue)
    require(not any(_operative_issue_identity(row["issue"]) == issue_key for row in previous),
            "existing authorized issue cannot replenish a repair under a new alias")
    require(issue_key not in _bound_repair_issues(state),
            "approved or consumed operative issue cannot replenish an alias")
    _source_refs(authorization.get("evidence_refs"))
    receipts = [_receipt(ref) for ref in authorization["evidence_refs"] if Path(ref).is_file()]
    require(receipts, "distinct issue requires at least one actual local evidence receipt")
    review_receipt = _receipt(authorization.get("research_decision_receipt", ""))
    review = json.loads(Path(review_receipt["path"]).read_text())
    require(isinstance(review, dict) and review.get("decision") == "distinct_scoped_issue"
            and isinstance(review.get("agent_id"), str) and review["agent_id"].strip()
            and review["agent_id"] not in origin["authors"], "read-only scoped Astra research decision required")
    packets = {**state["packets"], **state.get("adaptive", {}).get("packets", {})}
    decision_packet = packets.get(review.get("packet_id"), {})
    require(decision_packet.get("launch_performed") is True
            and decision_packet.get("agent_id") == review["agent_id"]
            and decision_packet.get("phase") in {"research", "discovery", "escalation"}
            and decision_packet.get("route", {}).get("requested", {}).get("model") == "gpt-6-astra",
            "decision must come from an actually acknowledged Astra research/discovery packet")
    recorded = [event for task in state["tasks"].values() for event in task.get("history", [])]
    recorded += state.get("adaptive", {}).get("checkpoints", [])
    require(any(event.get("receipt") == review_receipt
                and event.get("result", {}).get("packet_id") == decision_packet["packet_id"]
                for event in recorded), "actual Astra decision outcome must be recorded before authorization")
    bindings = {"origin_task_id": origin_id, "origin_issue_identity": authorization["origin_issue_identity"],
                "issue_identity": signature, "semantic_delta_identity": delta_identity,
                "claim_target": authorization["claim_target"], "cumulative_budget_link": state["campaign_identity"]}
    successors = authorization.get("successor_bindings", [])
    require(isinstance(successors, list), "successor bindings must be a list")
    successor_ids = []
    for successor in successors:
        require(isinstance(successor, dict) and set(successor) == {
                    "task_id", "task_spec_identity", "claim_target", "issue_identity", "semantic_delta_identity"}
                and all(isinstance(value, str) and value.strip() for value in successor.values())
                and successor["task_id"] != origin_id
                and successor["issue_identity"] == signature, "exact successor issue/spec/target/delta binding required")
        successor_ids.append(successor["task_id"])
    require(len(successor_ids) == len(set(successor_ids)), "duplicate successor binding")
    if successors:
        require(review.get("successor_bindings") == successors, "actual Astra decision must bind successors explicitly")
    require(all(review.get(field) == value for field, value in bindings.items()),
            "novelty review must bind exact predecessor, delta, issue, claim and cumulative budget")
    state.setdefault("repair_authorizations", {})[key] = {**copy.deepcopy(authorization),
            "semantic_delta_identity": delta_identity, "research_decision": review_receipt,
            "requested_research_runtime": decision_packet["route"]["requested"],
            "observed_research_runtime": decision_packet.get("observed_runtime", "UNKNOWN"),
            "user_authorization": user_authorization, "receipts": receipts}


def append_frontier(state: dict, frontier: dict, authorization: str) -> None:
    """Append conditional questions without rewriting any frozen campaign object."""
    require(authorization.strip(), "current frontier authorization required")
    require(state["campaign_identity"] == digest(state["campaign"]), "campaign identity changed")
    require(frontier.get("frontier_id") and frontier.get("tasks"), "frontier_id and tasks required")
    require(not any(f["frontier"]["frontier_id"] == frontier["frontier_id"]
                    for f in state.get("frontiers", [])), "frontier already appended")
    rows = frontier["tasks"]
    ids = [t["id"] for t in rows]
    require(len(set(ids)) == len(ids) and not set(ids) & state["tasks"].keys(), "duplicate task ID")
    old_signatures = {_action_signature(task["spec"]) for task in state["tasks"].values()
                      if task["spec"].get("semantic_delta") and task["spec"].get("input_sources")}
    for t in rows:
        require(t.get("contract_origin") == "new_conditional_research"
                and t.get("promotes_original_acceptance") is False,
                "frontier tasks must preserve original scientific acceptance")
        require(t.get("owned_paths") and t.get("input_sources") and t.get("requires") is not None,
                "lowered owned_paths, input_sources and typed requires needed")
        require(not t.get("enables_nodes") and not t.get("depends_on"),
                "new tasks use typed requires; original enabling edges cannot change")
        require(t.get("initial_state", "ready") == "ready", "new tasks require actual execution and review")
        repair = t.get("approved_repair_id")
        require(not repair or _repair_approved(state, repair),
                "append cannot authorize a new ultra repair budget")
        _semantic_delta(t.get("semantic_delta"))
        require(t["semantic_delta"]["kind"] != "prelaunch_transport", "transport is resume evidence, not a new question")
        signature = _action_signature(t)
        require(signature not in old_signatures,
                "logical research action already exists; new IDs/owned paths cannot reset attempts")
        old_signatures.add(signature)
        _validate_repair_binding(state, repair, t["id"], spec=t, prospective=True)
    # Reuse the existing spec validator; graph validation below includes typed edges.
    new = initialize({"campaign_id": state["campaign_id"], "tasks": rows}, authorization)
    combined = {**state["tasks"], **new["tasks"]}
    edges = {}
    for key, task in combined.items():
        edges[key] = set(task["spec"].get("depends_on", []))
        if "requires" in task["spec"]:
            edges[key] |= _obligation_refs(task["spec"]["requires"])
        require(edges[key] <= combined.keys(), "unknown obligation/dependency reference")
    visiting, visited = set(), set()
    def visit(key):
        require(key not in visiting, "obligation dependency cycle")
        if key in visited:
            return
        visiting.add(key)
        for dep in edges[key]:
            visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in combined:
        visit(key)
    # No mutation occurs before all validation completes.
    state["tasks"].update(new["tasks"])
    entry = {"frontier": copy.deepcopy(frontier), "identity": digest(frontier), "authorization": authorization}
    state.setdefault("frontiers", []).append(entry)
    state["events"].append({"type": "frontier_appended", "identity": entry["identity"], "task_ids": ids})


def enable_adaptive(state: dict, authorization: str, state_source: str | None = None) -> None:
    """Opt in outside the frozen campaign; never reset an existing witness."""
    require(isinstance(authorization, str) and authorization.strip(), "current adaptive authorization required")
    require(state["campaign_identity"] == digest(state["campaign"]), "campaign identity changed")
    require(state_source is None or Path(state_source).is_file(), "adaptive state source file required")
    if "adaptive" not in state:
        state["adaptive"] = {"authorization": authorization, "packets": {}, "checkpoints": [],
                             "evidence_deltas": [], "state_source": str(Path(state_source).resolve()) if state_source else None}


def adaptive_evidence(state: dict, evidence: str) -> None:
    """Register a real source/method change, not a discovery/event counter."""
    require("adaptive" in state, "adaptive continuation is not enabled")
    receipt = _receipt(evidence)
    delta = json.loads(Path(evidence).read_text())
    _semantic_delta(delta)
    require(delta["kind"] != "prelaunch_transport", "adaptive evidence must change research meaning")
    _source_refs(delta.get("source_refs"))
    identity = digest(_semantic_projection(delta))
    require(not any(row["identity"] == identity for row in state["adaptive"]["evidence_deltas"]),
            "adaptive semantic evidence already registered")
    state["adaptive"]["evidence_deltas"].append({"identity": identity, "delta": delta, "receipt": receipt})


def restore_discovery(state: dict, packet_id: str, evidence: str) -> None:
    """Restore only an actually refused, unacknowledged, non-exhausted discovery launch."""
    adaptive = state.get("adaptive", {})
    packet = adaptive.get("packets", {}).get(packet_id)
    require(packet and packet["state"] == "held" and not packet.get("launch_performed")
            and not packet.get("agent_id"), "only refused unacknowledged discovery may restore")
    require(not packet["hold"].get("retry_prohibited"), "exhausted/prohibited discovery transport cannot retry")
    require(packet["fingerprint"] == adaptive_fingerprint(state), "discovery science fingerprint changed")
    require(not any(value["state"] in {"planned", "running"} for value in adaptive["packets"].values())
            and not any(task["state"] in {"planned", "running"} for task in state["tasks"].values()),
            "outstanding native opportunity cannot replay")
    receipt = _receipt(evidence)
    delta = json.loads(Path(evidence).read_text())
    _semantic_delta(delta)
    require(delta["kind"] == "prelaunch_transport" and delta.get("packet_id") == packet_id
            and delta.get("fingerprint") == packet["fingerprint"], "exact discovery transport delta required")
    restoration_receipt = _receipt(delta.get("restoration_receipt", ""))
    restored = json.loads(Path(restoration_receipt["path"]).read_text())
    require(isinstance(restored, dict) and restored.get("transport_available") is True
            and restored.get("retry_permitted") is True
            and restored.get("packet_id") == packet_id and restored.get("fingerprint") == packet["fingerprint"]
            and restored.get("native_tool") == packet["native_tool"], "actual identity-bound transport restoration required")
    record = {"packet_id": packet_id, "fingerprint": packet["fingerprint"],
              "semantic_delta": delta, "receipt": receipt, "restoration_receipt": restoration_receipt}
    packet["state"] = "restored"
    adaptive.setdefault("transport_restorations", []).append(record)


def _source_refs(refs: Any) -> None:
    from urllib.parse import urlparse
    require(isinstance(refs, list) and refs, "nonempty resolvable source_refs required")
    for ref in refs:
        require(isinstance(ref, str) and ref.strip(), "source reference must be a string")
        url = urlparse(ref)
        require((url.scheme in {"https", "http"} and bool(url.netloc)) or Path(ref).is_file(),
                "source reference must be an existing file or explicit http(s) source")


def adaptive_fingerprint(state: dict) -> str:
    """Stable nonplanning evidence; discovery cannot make its own next opportunity."""
    evidence = {}
    for key, task in sorted(state["tasks"].items()):
        history = task.get("history", [])
        evidence[key] = {"spec": task["spec"],
                         "latest_actual_result": history[-1] if history else None,
                         "candidate_identity": task.get("candidate_identity"),
                         "candidate_products": task.get("candidate_products", []),
                         "qualified_products": task.get("qualified_products", []),
                         "hold": task.get("hold"),
                         "scientific_resume": task.get("scientific_resume")}
    return digest({"tasks": evidence,
                   "evidence_deltas": [row["identity"] for row in state.get("adaptive", {}).get("evidence_deltas", [])]})


def _adaptive_next(state: dict, policy: dict, profiles: set[tuple[str, str]]) -> dict | None:
    adaptive = state.get("adaptive")
    if adaptive is None:
        return None
    for packet in adaptive["packets"].values():
        if packet["state"] == "planned":
            return copy.deepcopy(packet)
        if packet["state"] == "running":
            return summary(state)
    exhausted = [packet for packet in adaptive["packets"].values()
                 if packet["state"] == "held" and packet.get("hold", {}).get("retry_prohibited")]
    if exhausted:
        return {**summary(state), "status": "HOLD_TRANSPORT_UNAVAILABLE", "discovery_hold": exhausted[-1]["hold"]}
    fingerprint = adaptive_fingerprint(state)
    if any(row["fingerprint"] == fingerprint for row in adaptive["checkpoints"]):
        return None
    refused = [p for p in adaptive["packets"].values()
               if p["fingerprint"] == fingerprint and p["state"] == "held"]
    if refused:
        return {**summary(state), "status": "HOLD_TRANSPORT_UNAVAILABLE", "discovery_hold": refused[-1]["hold"]}
    route = resolve_route(policy, "review_or_research", profiles)
    if route["transport_selected"] is None:
        return {**summary(state), "status": "HOLD_TRANSPORT_UNAVAILABLE", "discovery_route": route}
    eligible = sorted(key for key, task in state["tasks"].items()
                      if task["state"] not in {"completed", "checkpointed", "resume_pending"})
    if not eligible:
        return None
    selected = route["transport_selected"]
    identity = {"campaign": state["campaign_identity"], "adaptive_discovery": fingerprint}
    restorations = [row for row in adaptive.get("transport_restorations", []) if row["fingerprint"] == fingerprint]
    restoration = restorations[-1] if restorations else None
    if restoration:
        identity["transport_restoration_identity"] = digest(restoration)
    packet_id = digest(identity)
    assignment = {"fingerprint": fingerprint, "campaign_identity": state["campaign_identity"],
                  "state_source": adaptive.get("state_source"), "eligible_branches": eligible,
                  "transport_restoration": restoration,
                  "branch_inventory": {key: {"state": task["state"], "phase": task["phase"]}
                      for key, task in state["tasks"].items()},
                  "evidence_delta_receipts": [row["receipt"] for row in adaptive["evidence_deltas"]]}
    prompt = ("Read-only bounded adaptive research discovery. Do not spawn children, implement, run a native "
              "solver/ODE, manufacture inputs, reopen exhausted attempts or alter original acceptances/budgets. "
              "Read state_source and its source/receipt references before making claims; absent source access is an exact residual. "
              "Examine held branches for genuine new methods, assumptions, observables, sources or counterexamples. "
              "Return packet_id, task_id, input_identity, agent_id and raw_receipt. outcome must be proposal or "
              "no_action. A no_action result must examine every exact assigned eligible_branches entry. "
              "Always provide examined_branches, methods, source_refs and exact_residuals. A proposal "
              "also needs frontier: executable new_conditional_research tasks with existing local or explicit "
              "http(s) input_sources, typed requires, bounded owned_paths, semantic_delta and unchanged original "
              "acceptance. Discovery has no qualified products or scientific success. Assignment: " +
              json.dumps({"packet_id": packet_id, "task_id": "adaptive-discovery", "input_identity": fingerprint,
                          **assignment}, ensure_ascii=False))
    packet = {"packet_id": packet_id, "task_id": "adaptive-discovery", "input_identity": fingerprint,
              "fingerprint": fingerprint, "eligible_branches": eligible,
              "transport_restoration": restoration, "phase": "discovery", "state": "planned", "route": route,
              "launch_performed": False, "observed_runtime": "UNKNOWN",
              "native_tool": "collaboration.spawn_agent",
              "spawn_args": {"task_name": "discovery_" + packet_id[:16], "fork_turns": "none",
                             "model": selected["model"], "reasoning_effort": selected["effort"], "message": prompt}}
    adaptive["packets"][packet_id] = packet
    return copy.deepcopy(packet)


def _adaptive_record(state: dict, result: dict) -> None:
    adaptive = state["adaptive"]
    packet = adaptive["packets"][result["packet_id"]]
    require(packet["state"] == "running", "stale or unlaunched discovery result")
    require(result.get("agent_id") == packet["agent_id"] and result.get("task_id") == packet["task_id"]
            and result.get("input_identity") == packet["input_identity"], "stale discovery identity")
    receipt = _receipt(result.get("raw_receipt", ""))
    require(not result.get("qualified_products") and not result.get("acceptance_met"),
            "discovery cannot qualify products or accept science")
    for field in ("examined_branches", "methods", "exact_residuals"):
        require(isinstance(result.get(field), list) and result[field]
                and all(isinstance(v, str) and v.strip() for v in result[field]),
                "discovery needs nonempty " + field)
    require(set(result["examined_branches"]) <= state["tasks"].keys(), "unknown examined branch")
    _source_refs(result.get("source_refs"))
    outcome = result.get("outcome")
    require(outcome in {"proposal", "no_action"}, "discovery needs proposal or scoped no_action")
    if outcome == "proposal":
        frontier = result.get("frontier")
        require(isinstance(frontier, dict), "executable frontier required")
        for task in frontier.get("tasks", []):
            _source_refs(task.get("input_sources"))
        append_frontier(state, frontier, adaptive["authorization"])
        for spec in frontier["tasks"]:
            contributors = state["tasks"][spec["id"]]["contributors"]
            if packet["agent_id"] not in contributors:
                contributors.append(packet["agent_id"])
    else:
        require(set(result["examined_branches"]) == set(packet["eligible_branches"]),
                "no_action must cover every exact assigned eligible branch")
        require(not result.get("frontier"), "no_action cannot append work")
    adaptive["checkpoints"].append({"fingerprint": packet["fingerprint"], "outcome": outcome,
                                    "receipt": receipt, "result": copy.deepcopy(result)})
    packet["state"] = "recorded"


def _file_seal(value: dict) -> dict:
    """Verify real bytes with bounded memory, including large retained products."""
    require(isinstance(value, dict), "file seal required")
    require(isinstance(value.get("path"), str) and value["path"], "sealed file path required")
    path = Path(value["path"])
    require(path.is_file() and isinstance(value.get("size_bytes"), int), "sealed file/size required")
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            hasher.update(chunk)
    require(size == value["size_bytes"] and hasher.hexdigest() == value.get("sha256"),
            "sealed file bytes changed: " + str(path))
    return {"path": str(path.resolve()), "sha256": hasher.hexdigest(), "size_bytes": size}


def _checkpoint_document(path: str) -> tuple[dict, dict]:
    receipt = _receipt(path)
    require(Path(receipt["path"]).stat().st_size <= 8 * 1024 * 1024, "checkpoint metadata bound exceeded")
    data = json.loads(Path(receipt["path"]).read_text())
    require(isinstance(data, dict), "checkpoint document required")
    require(_receipt(path) == receipt, "checkpoint receipt changed during inspection")
    return data, receipt


def acquisition_binding(state: dict, task_id: str, sequence: int) -> dict:
    """Identity supplied to the actual worker; this does not request or observe a handoff."""
    require(task_id in state["tasks"], "unknown acquisition")
    task = state["tasks"][task_id]
    packet = state["packets"].get(task.get("packet_id"), {})
    require(task["phase"] == packet.get("phase") == "acquisition"
            and packet.get("task_id") == task_id
            and packet.get("input_identity") == task["spec"]["input_identity"]
            and packet.get("launch_performed") and packet.get("agent_id"), "acknowledged acquisition required")
    require(isinstance(sequence, int) and not isinstance(sequence, bool) and sequence > 0,
            "positive checkpoint sequence required")
    return {"campaign_identity": state["campaign_identity"], "task_id": task_id,
            "packet_id": task["packet_id"], "input_identity": task["spec"]["input_identity"],
            "task_spec_identity": digest(task["spec"]),
            "task_identity": digest({k: v for k, v in task.items() if k != "state"}),
            "packet_identity": digest(packet), "agent_id": packet["agent_id"], "sequence": sequence}


def _checkpoint_snapshot(snapshot: dict) -> None:
    required = {"sources", "processes", "queued_writers", "future_launchers", "attempt_receipts",
                "completed_products", "partial_products", "accounting"}
    require(isinstance(snapshot, dict) and required <= snapshot.keys(), "complete checkpoint snapshot required")
    require(snapshot["queued_writers"] == [] and snapshot["future_launchers"] == [],
            "queued writer or future launcher remains")
    for key in ("sources", "processes", "attempt_receipts", "completed_products", "partial_products"):
        require(isinstance(snapshot[key], list), "checkpoint inventory must be a list")
    require(snapshot["sources"] and snapshot["processes"] and snapshot["attempt_receipts"],
            "executed source/process/attempt inventory required")
    sources = set()
    for value in snapshot["sources"]:
        seal = _file_seal(value)
        require(seal["path"] not in sources, "duplicate executing source")
        sources.add(seal["path"])
    processes = set()
    for process in snapshot["processes"]:
        require(isinstance(process, dict) and isinstance(process.get("pid"), int) and process["pid"] > 0
                and isinstance(process.get("parent_pid"), int) and process["parent_pid"] >= 0
                and isinstance(process.get("start_identity"), str) and process["start_identity"].strip()
                and isinstance(process.get("session_id"), str) and process["session_id"].strip()
                and isinstance(process.get("command"), list) and process["command"]
                and all(isinstance(v, str) and v for v in process["command"])
                and isinstance(process.get("cwd"), str) and Path(process["cwd"]).is_absolute()
                and process.get("role") in {"controller", "launcher", "transfer", "child", "continuation"},
                "complete PID/start/command/cwd/parent/session identity required")
        require(process.get("state") == "exited" and isinstance(process.get("exit_code"), int),
                "active or dormant process retains writer ownership")
        identity = (process["pid"], process["start_identity"])
        require(identity not in processes, "duplicate process identity")
        processes.add(identity)
        require(isinstance(process.get("source_refs"), list) and process["source_refs"]
                and {str(Path(ref).resolve()) for ref in process["source_refs"]} <= sources,
                "process executing source binding missing")
    for value in snapshot["attempt_receipts"]:
        _file_seal(value)
    products = set()
    for key in ("completed_products", "partial_products"):
        for value in snapshot[key]:
            _file_seal(value)
            require(isinstance(value.get("product_id"), str) and value["product_id"].strip()
                    and isinstance(value.get("source_release"), str) and value["source_release"].strip()
                    and isinstance(value.get("source_refs"), list) and value["source_refs"]
                    and {str(Path(ref).resolve()) for ref in value["source_refs"]} <= sources,
                    "product source/release binding required")
            require(value["product_id"] not in products, "duplicate completed/partial product")
            products.add(value["product_id"])
            if key == "partial_products":
                require(value.get("offset") == value["size_bytes"], "partial offset differs from sealed retained bytes")
    accounting = snapshot["accounting"]
    require(isinstance(accounting, dict) and accounting and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0
        and v < float("inf") for v in accounting.values()), "finite nonnegative cumulative accounting required")


def _validate_checkpoint(state: dict, task_id: str, worker_path: str, host_path: str) -> dict:
    started = time.monotonic()
    worker, worker_receipt = _checkpoint_document(worker_path)
    host, host_receipt = _checkpoint_document(host_path)
    require(worker_receipt["path"] != host_receipt["path"], "independent host corroboration required")
    binding = worker.get("binding", {})
    require(isinstance(binding, dict), "checkpoint binding object required")
    require(binding == acquisition_binding(state, task_id, binding.get("sequence")),
            "checkpoint task/packet/input/agent/science identity changed")
    require(worker.get("handoff_complete") is True and worker.get("inventory_complete") is True,
            "actual complete worker handoff required")
    snapshot = worker.get("snapshot")
    _checkpoint_snapshot(snapshot)
    require(host.get("binding") == binding and host.get("worker_receipt") == worker_receipt
            and host.get("snapshot_identity") == digest(snapshot)
            and host.get("inventory_complete") is True and host.get("quiescence_observed") is True
            and host.get("observer") and host["observer"] != binding["agent_id"],
            "independent complete host corroboration missing or stale")
    require(isinstance(worker.get("raw_evidence"), list) and worker["raw_evidence"], "actual worker raw evidence required")
    for value in worker["raw_evidence"]:
        _file_seal(value)
    observation = _file_seal(host.get("process_observation", {}))
    observed, _ = _checkpoint_document(observation["path"])
    require(observed.get("binding") == binding and observed.get("observer") == host["observer"]
            and observed.get("inventory_complete") is True
            and observed.get("processes") == snapshot["processes"]
            and observed.get("queued_writers") == [] and observed.get("future_launchers") == [],
            "raw host process/start/launcher/queue observations do not corroborate handoff")
    require(isinstance(host.get("raw_evidence"), list) and host["raw_evidence"], "raw host source/artifact corroboration required")
    for value in host["raw_evidence"]:
        _file_seal(value)
    require(_receipt(worker_path) == worker_receipt and _receipt(host_path) == host_receipt,
            "checkpoint receipts changed during validation")
    return {"binding": binding, "snapshot": snapshot, "worker_receipt": worker_receipt,
            "host_receipt": host_receipt, "checkpoint_identity": digest({"worker": worker_receipt, "host": host_receipt}),
            "validation_wall_seconds": time.monotonic() - started}


def _validate_stored_checkpoint(state: dict, task_id: str, row: dict) -> None:
    current = _validate_checkpoint(state, task_id, row["worker_receipt"]["path"], row["host_receipt"]["path"])
    require(all(current[key] == row[key] for key in
                ("binding", "snapshot", "worker_receipt", "host_receipt", "checkpoint_identity")),
            "stored checkpoint receipts/snapshot replaced")


def _validate_released_acquisitions(state: dict) -> None:
    for task_id, rows in state.get("acquisition_lifecycle", {}).items():
        if state["tasks"][task_id]["state"] == "checkpointed":
            _validate_stored_checkpoint(state, task_id, rows[-1])


def _retained_prefix(previous: dict, current: dict) -> bool:
    if (current["size_bytes"] < previous["size_bytes"]
            or current["source_release"] != previous["source_release"]
            or not {str(Path(ref).resolve()) for ref in previous["source_refs"]}
            <= {str(Path(ref).resolve()) for ref in current["source_refs"]}):
        return False
    remaining = previous["size_bytes"]
    hasher = hashlib.sha256()
    with Path(current["path"]).open("rb") as stream:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                return False
            hasher.update(chunk)
            remaining -= len(chunk)
    return hasher.hexdigest() == previous["sha256"]


def checkpoint_acquisition(state: dict, task_id: str, worker_receipt: str, host_evidence: str) -> dict:
    """Release only an actually handed-off acquisition; never observe or stop processes."""
    task = state["tasks"].get(task_id)
    require(task, "unknown acquisition")
    previous = state.get("acquisition_lifecycle", {}).get(task_id, [])
    worker_seal, host_seal = _receipt(worker_receipt), _receipt(host_evidence)
    for row in previous:
        if row["worker_receipt"] == worker_seal and row["host_receipt"] == host_seal:
            return copy.deepcopy(row)  # Historical duplicate cannot checkpoint a resumed writer again.
    require(task["state"] == "running", "only a running acknowledged acquisition can checkpoint")
    row = _validate_checkpoint(state, task_id, worker_receipt, host_evidence)
    require(row["binding"]["sequence"] == len(previous) + 1, "nonmonotonic checkpoint sequence")
    if previous:
        old, new = previous[-1]["snapshot"], row["snapshot"]
        require(new["attempt_receipts"][:len(old["attempt_receipts"])] == old["attempt_receipts"],
                "attempt receipt history was reset")
        require(all(k in new["accounting"] and new["accounting"][k] >= v for k, v in old["accounting"].items()),
                "cumulative accounting decreased")
        require(all(v in new["completed_products"] for v in old["completed_products"]),
                "completed immutable products changed or disappeared")
        products = {v["product_id"]: v for key in ("completed_products", "partial_products") for v in new[key]}
        require(all(v["product_id"] in products and _retained_prefix(v, products[v["product_id"]])
                    for v in old["partial_products"]), "retained partial prefix/source continuity changed")
    state.setdefault("acquisition_lifecycle", {}).setdefault(task_id, []).append(row)
    task["state"] = "checkpointed"
    return copy.deepcopy(row)


def _writer_reserved(state: dict) -> bool:
    return any(task["state"] == "resume_pending" for task in state["tasks"].values())


def _validate_resume_plan(row: dict, plan_path: str) -> dict:
    plan, receipt = _checkpoint_document(plan_path)
    require(plan.get("checkpoint_identity") == row["checkpoint_identity"]
            and plan.get("binding") == row["binding"], "resume plan checkpoint binding changed")
    require(isinstance(plan.get("sources"), list) and plan["sources"], "reviewed cooperative source list required")
    seals = [_file_seal(value) for value in plan["sources"]]
    review_seal = _file_seal(plan.get("review_receipt", {}))
    review, _ = _checkpoint_document(review_seal["path"])
    require(review.get("verdict") == "SCOPED_PASS" and review.get("reviewer")
            and review["reviewer"] != row["binding"]["agent_id"]
            and review.get("task_id") == row["binding"]["task_id"]
            and review.get("packet_id") == row["binding"]["packet_id"]
            and review.get("input_identity") == row["binding"]["input_identity"]
            and review.get("source_hashes") == {value["path"]: value["sha256"] for value in seals},
            "actual independent source review must bind exact resumed helper bytes/task/input")
    require(_receipt(plan_path) == receipt, "resume plan changed during inspection")
    return {"plan_receipt": receipt, "sources": seals, "review_receipt": review_seal}


def prepare_acquisition_resume(state: dict, task_id: str, checkpoint_identity: str, resume_plan: str) -> dict:
    """Durably reserve before a same-agent followup; ambiguity retains writer ownership."""
    task = state["tasks"].get(task_id)
    require(task, "unknown acquisition")
    rows = state.get("acquisition_lifecycle", {}).get(task_id, [])
    require(rows and rows[-1]["checkpoint_identity"] == checkpoint_identity, "exact current checkpoint required")
    row = rows[-1]
    if "resume" in row:
        require(row["resume"]["plan"]["plan_receipt"] == _receipt(resume_plan), "different resume plan already reserved")
        return copy.deepcopy(row["resume"])
    require(task["state"] == "checkpointed", "acquisition is not checkpointed")
    require(not any(t["state"] in {"planned", "running", "resume_pending"} for t in state["tasks"].values())
            and not any(p["state"] in {"planned", "running"} for p in state.get("adaptive", {}).get("packets", {}).values()),
            "another native packet owns the writer slot")
    _validate_stored_checkpoint(state, task_id, row)
    plan = _validate_resume_plan(row, resume_plan)
    packet = state["packets"][row["binding"]["packet_id"]]
    reservation = {"checkpoint_identity": checkpoint_identity, "binding": copy.deepcopy(row["binding"]),
                   "plan": plan, "route": copy.deepcopy(packet["route"]), "state": "pending",
                   "native_tool": "collaboration.followup_task", "agent_id": packet["agent_id"]}
    reservation["reservation_identity"] = digest(reservation)
    row["resume"] = reservation
    task["state"] = "resume_pending"
    return copy.deepcopy(reservation)


def acknowledge_acquisition_resume(state: dict, task_id: str, reservation_identity: str,
                                   dispatch_evidence: str, observed: str = "UNKNOWN") -> None:
    task = state["tasks"].get(task_id)
    require(task, "unknown acquisition")
    rows = state.get("acquisition_lifecycle", {}).get(task_id, [])
    require(rows and rows[-1].get("resume"), "no durable resume reservation")
    row, reservation = rows[-1], rows[-1]["resume"]
    require(reservation["reservation_identity"] == reservation_identity, "stale resume reservation")
    data, receipt = _checkpoint_document(dispatch_evidence)
    if reservation["state"] == "acknowledged":
        require(reservation["dispatch_receipt"] == receipt, "different followup already acknowledged")
        _file_seal(reservation["tool_receipt"])
        return
    require(task["state"] == "resume_pending", "resume not pending")
    require(not any(key != task_id and t["state"] in {"planned", "running", "resume_pending"}
                    for key, t in state["tasks"].items())
            and not any(p["state"] in {"planned", "running"} for p in state.get("adaptive", {}).get("packets", {}).values()),
            "competing native owner appeared before resume ACK")
    _validate_stored_checkpoint(state, task_id, row)
    plan = _validate_resume_plan(row, reservation["plan"]["plan_receipt"]["path"])
    require(plan == reservation["plan"], "durably reserved resume plan/source/review replaced")
    expected = {"binding": row["binding"], "checkpoint_identity": row["checkpoint_identity"],
                "reservation_identity": reservation_identity, "agent_id": reservation["agent_id"],
                "native_tool": "collaboration.followup_task", "accepted": True,
                "requested": reservation["route"]["requested"],
                "transport_selected": reservation["route"]["transport_selected"]}
    require(all(data.get(k) == v for k, v in expected.items()), "actual same-agent followup acceptance binding required")
    tool_seal = _file_seal(data.get("tool_receipt", {}))
    tool, _ = _checkpoint_document(tool_seal["path"])
    require(all(tool.get(k) == v for k, v in expected.items()), "raw native accepted-call receipt mismatch")
    reservation.update(state="acknowledged", dispatch_receipt=receipt, tool_receipt=tool_seal,
                       observed_runtime=observed)
    task["state"] = "running"


def route_for(task: dict) -> str:
    if task["phase"] == "escalation":
        return "blocker_escalation"
    if task["phase"] in {"research", "review"} or (
            task["phase"] == "execute" and task["spec"].get("kind") == "theory"):
        return "review_or_research"
    return task["spec"].get("implementation_route", "subagent_specialist")


def summary(state: dict) -> dict:
    tasks = state["tasks"]
    states = {key: t["state"] for key, t in tasks.items()}
    done = {key for key, t in tasks.items() if t["state"] == "completed"}
    ready = [key for key, t in tasks.items() if t["state"] == "ready"
             and set(t["spec"].get("depends_on", [])) <= done
             and _obligation_met(t["spec"].get("requires", {"all": []}), tasks)]
    if len(done) == len(tasks):
        status = "CAMPAIGN_ACCEPTANCES_REVIEWED"
    elif any(t["state"] in {"planned", "running", "resume_pending"} for t in tasks.values()):
        status = "AWAITING_NATIVE_OUTCOME"
    elif ready:
        status = "CONTINUE"
    else:
        status = "HOLD_UNRESOLVED_BRANCHES"
    originals = state["campaign"].get("original_science_contract", {}).get("nodes", [])
    adaptive = state.get("adaptive", {})
    planning = list(adaptive.get("packets", {}).values())
    if any(p["state"] in {"planned", "running"} for p in planning):
        status = "AWAITING_NATIVE_OUTCOME"
    return {"acquisition_lifecycle": {key: {"state": tasks[key]["state"], "checkpoints": len(rows)}
                                      for key, rows in state.get("acquisition_lifecycle", {}).items()},
            "planning": {"enabled": bool(adaptive), "packets": len(planning),
                          "checkpoints": len(adaptive.get("checkpoints", [])),
                          "outstanding": sum(p["state"] in {"planned", "running"} for p in planning)},
            "campaign_id": state["campaign_id"], "status": status, "states": states,
            "ready": ready, "completed": len(done), "total": len(tasks),
            "original_science": {"total": len(originals),
                                 "source_completed_scoped": sum(n.get("state") == "completed_scoped" for n in originals),
                                 "admission": "UNCHANGED_NOT_GRANTED_BY_CONTROLLER"},
            "held": {key: t.get("hold") for key, t in tasks.items() if t["state"] == "held"},
            "note": "Scoped task acceptance never automatically promotes original scientific nodes."}


def _review_context(state: dict, task_id: str, *, allow_running: bool = False,
                    repository_root: Path | None = None) -> dict | None:
    """Prove the narrow read-only slot from declared, resolved local scopes."""
    task = state["tasks"][task_id]
    if (task["phase"] != "review" or task["state"] not in ({"ready", "planned", "running"} if allow_running else {"ready", "planned"})
            or not task.get("candidate_identity")):
        return None
    done = {key for key, row in state["tasks"].items() if row["state"] == "completed"}
    if not (set(task["spec"].get("depends_on", [])) <= done
            and _obligation_met(task["spec"].get("requires", {"all": []}), state["tasks"])):
        return None
    if any(packet["state"] in {"planned", "running"}
           for packet in state.get("adaptive", {}).get("packets", {}).values()):
        return None
    others = [(key, row) for key, row in state["tasks"].items()
              if key != task_id and row["state"] in {"planned", "running"}]
    if len(others) > 1 or any(row["state"] != "running" or row["phase"] != "acquisition"
                              for _, row in others):
        return None
    root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[2]
    def local(value, exists=False, relative_to=None):
        if (not isinstance(value, str) or not value.strip() or "://" in value
                or any(char in value for char in "*?[")):
            raise ValueError("unknown local scope")
        value = Path(value)
        choices = {(value if value.is_absolute() else root / value).resolve()}
        if relative_to is not None and not value.is_absolute():
            choices.add((relative_to / value).resolve())
        if exists:
            choices = {path for path in choices if path.exists()}
        if len(choices) != 1:
            raise ValueError("missing or ambiguous local scope")
        return str(choices.pop())
    def metadata(path):
        # Bounded reads even if a file grows between stat and read.
        with path.open("rb") as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("metadata traversal bound")
        document = json.loads(raw)
        if not isinstance(document, dict):
            raise ValueError("unknown contract declarations")
        return raw, document
    try:
        spec = task["spec"]
        if (not spec.get("owned_paths") or not spec.get("input_sources")
                or len(spec["owned_paths"]) > 256 or len(spec["input_sources"]) > 256
                or not isinstance(task["candidate_identity"], str)):
            return None
        # Establish write ownership before reading any newly declared source.
        acquisition = None
        writes = []
        if others:
            owner_id, owner = others[0]
            packet = state["packets"].get(owner.get("packet_id"), {})
            if (not packet.get("launch_performed") or not packet.get("agent_id")
                    or packet.get("task_id") != owner_id or packet.get("phase") != "acquisition"
                    or packet.get("input_identity") != owner["spec"].get("input_identity")
                    or not owner["spec"].get("owned_paths")):
                return None
            writes = sorted({local(value) for value in owner["spec"]["owned_paths"]})
            acquisition = {"task_id": owner_id, "packet_id": owner["packet_id"],
                           "input_identity": packet["input_identity"], "owned_paths": writes}
        def disjoint(value):
            p = Path(value)
            if any(p == Path(w) or p.is_relative_to(w) or Path(w).is_relative_to(p) for w in writes):
                raise ValueError("acquisition/review source overlap")

        owned_scopes = {local(value, True) for value in spec["owned_paths"]}
        for value in owned_scopes:
            disjoint(value)
        reads, contracts, source_seals, aliases = set(owned_scopes), {}, {}, {}
        inventory_alias_pairs = []
        source_bytes = metadata_bytes = 0
        queue = [(entry, root, 0, None) for entry in spec["input_sources"]]
        typed_leaves = {}
        frozen_root = "/mnt/extdrive/workdir/htt_open_data/r25_gaia_tag_association_proposal/INPUT.json"
        frozen_sha = "00209480018bcb19f29c3c22a2d847c26560bcf950045978f10579967314e39f"
        large_leaf = "/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_properties_20261023/products/property_table.json"
        large_sha = "76d523bb28a1176fa3e81139b6581f3fa176ae4745129f8ec5c9dd995d207c4e"
        frozen_role = large_role_record = False
        while queue:
            entry, parent, depth, role = queue.pop(0)
            def remote_url(value):
                parsed = urlsplit(value) if isinstance(value, str) else None
                return bool(parsed and parsed.scheme in {"http", "https"} and parsed.hostname)
            if isinstance(entry, dict) and "url" in entry:
                keys = set(entry)
                if (keys not in ({"url"}, {"url", "scope"}, {"url", "role"}, {"url", "scope", "role"})
                        or not isinstance(entry["url"], str)
                        or ("role" in entry and entry["role"] != "reference")):
                    raise ValueError("mixed remote/local declaration")
                if not remote_url(entry["url"]) or ("scope" in entry and not isinstance(entry["scope"], str)):
                    raise ValueError("invalid remote reference")
                continue
            if isinstance(entry, str) and entry.startswith(("https://", "http://")):
                if not remote_url(entry):
                    raise ValueError("invalid remote reference")
                continue
            record = entry if isinstance(entry, dict) else {}
            role = record.get("role", role)
            record_keys = {"path", "resolved_path", "sha256", "bytes", "size_bytes", "role",
                           "allowed_array", "forbidden_array_access", "count", "identity",
                           "canonical_ID_bytes", "canonical_ID_sha256", "join"}
            if record and ("path" not in record or set(record) - record_keys):
                raise ValueError("unsupported source record")
            if "role" in record and record["role"] not in {"data", "code", "contract", "manifest"}:
                raise ValueError("unsupported local source role")
            name = record.get("path") if record else entry
            path = Path(local(name, True, parent))
            disjoint(path)
            if depth > 16 or len(reads) >= 256 and str(path) not in reads:
                raise ValueError("source scope bound")
            lexical = Path(name)
            if not lexical.is_absolute():
                relative_alias = parent / lexical
                lexical = relative_alias if relative_alias.is_file() else root / lexical
            lexical = str(lexical.absolute())
            if lexical in aliases and aliases[lexical] != str(path):
                raise ValueError("source alias redirected")
            aliases[lexical] = str(path)
            if "resolved_path" in record and record["resolved_path"] != str(path):
                raise ValueError("declared source alias redirected")
            reads.add(str(path))
            if str(path) not in source_seals:
                h, size = hashlib.sha256(), 0
                before_read = path.stat()
                with path.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        size += len(chunk)
                        source_bytes += len(chunk)
                        if source_bytes > 64 * 1024 * 1024:
                            raise ValueError("source binding byte bound")
                        h.update(chunk)
                after_read = path.stat()
                if ((before_read.st_ino, before_read.st_size, before_read.st_mtime_ns)
                        != (after_read.st_ino, after_read.st_size, after_read.st_mtime_ns)
                        or size != after_read.st_size):
                    raise ValueError("source changed during sealing")
                source_seals[str(path)] = {"sha256": h.hexdigest(), "size_bytes": size}
            seal = source_seals[str(path)]
            if "sha256" in record and record["sha256"] != seal["sha256"]:
                raise ValueError("declared source SHA changed")
            for size_key in ("bytes", "size_bytes"):
                if size_key in record and (type(record[size_key]) is not int or record[size_key] != seal["size_bytes"]):
                    raise ValueError("declared source size changed")
            if str(path) == frozen_root and seal["sha256"] == frozen_sha and depth == 0:
                frozen_role = True
            if str(path) == large_leaf and frozen_role:
                if (seal != {"sha256": large_sha, "size_bytes": 4643777}
                        or not large_role_record):
                    raise ValueError("frozen data leaf role changed")
                continue
            if path.suffix.lower() == ".json" and role == "data" and typed_leaves.get(str(path)) == seal:
                # An identity-bound data role cannot conceal a dependency contract.
                with path.open("rb") as stream:
                    raw_data = stream.read(seal["size_bytes"] + 1)
                if len(raw_data) != seal["size_bytes"] or hashlib.sha256(raw_data).hexdigest() != seal["sha256"]:
                    raise ValueError("typed data leaf changed during inspection")
                data_document = json.loads(raw_data)
                source_keys = {"input_sources", "sources", "inputs", "input_identity_binding",
                               "method_source", "source_id_input", "original_task_identity",
                               "files", "file_hashes", "source_hashes", "external_raw_carrier"}
                def contains_declarations(value):
                    if isinstance(value, dict):
                        return bool(source_keys & value.keys()) or any(contains_declarations(v) for v in value.values())
                    return isinstance(value, list) and any(contains_declarations(v) for v in value)
                if contains_declarations(data_document):
                    raise ValueError("typed data leaf declares local sources")
                continue
            if role in {"data", "code"} and path.suffix.lower() != ".json":
                continue
            if (path.suffix.lower() != ".json" and role not in {"contract", "manifest"}) or str(path) in contracts:
                continue
            if len(contracts) >= 64:
                raise ValueError("metadata document bound")
            raw, document = metadata(path)
            metadata_bytes += len(raw)
            if metadata_bytes > 4 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != seal["sha256"]:
                raise ValueError("metadata bound or identity changed")
            contracts[str(path)] = seal["sha256"]
            if depth == 0 and spec.get("input_identity") == "sha256:" + seal["sha256"]:
                for value in document.get("input_sources", []):
                    if not isinstance(value, dict) or value.get("role") != "data":
                        continue
                    if not (isinstance(value.get("sha256"), str)
                            and (type(value.get("bytes")) is int or type(value.get("size_bytes")) is int)):
                        raise ValueError("typed data leaf needs exact SHA and size")
                    target = local(value.get("path"), True, path.parent)
                    disjoint(target)
                    size = value.get("bytes", value.get("size_bytes"))
                    typed_leaves[target] = {"sha256": value["sha256"], "size_bytes": size}
            if str(path) == frozen_root and frozen_role:
                large_role_record = any(isinstance(v, dict) and v.get("path") == large_leaf
                                        and v.get("sha256") == large_sha and v.get("bytes") == 4643777
                                        for v in document.get("input_sources", []))
            def declared(value, parent_key=None, identity=False):
                if isinstance(value, str):
                    if parent_key in {"task_id", "implementation_packet_id", "input_identity",
                                      "candidate_semantic_identity", "return_manifest_sha256_field",
                                      "identity_roles", "relocation_interpretation", "sha256"}:
                        return
                    if identity:
                        raise ValueError("unsupported identity declaration")
                    queue.append((value, path.parent, depth + 1, None))
                elif isinstance(value, list):
                    for child in value:
                        declared(child, parent_key, identity)
                elif isinstance(value, dict):
                    if "path" in value or "url" in value:
                        queue.append((value, path.parent, depth + 1, value.get("role")))
                    else:
                        for key, child in value.items():
                            if key == "array_member_headers":
                                continue
                            declared(child, key, identity)
                else:
                    raise ValueError("unsupported source declaration")
            for group in ("input_sources", "sources", "inputs", "input_identity_binding",
                          "method_source", "source_id_input"):
                if group in document:
                    declared(document[group])
            if "original_task_identity" in document:
                value = document["original_task_identity"]
                if not isinstance(value, dict):
                    raise ValueError("unsupported original task identity")
                if "candidate_manifest_bytes" in value:
                    declared(value["candidate_manifest_bytes"])
            for group in ("files", "file_hashes", "source_hashes"):
                if group not in document:
                    continue
                inventory = document[group]
                if isinstance(inventory, dict):
                    rows = inventory.items()
                elif group == "files" and isinstance(inventory, list):
                    if not all(isinstance(v, dict) and "path" in v for v in inventory):
                        raise ValueError("unsupported source manifest inventory")
                    rows = [(v["path"], v) for v in inventory]
                else:
                    raise ValueError("unsupported source manifest inventory")
                for name, value in rows:
                    if isinstance(value, dict):
                        if "path" in value:
                            embedded_target = local(value["path"], True, path.parent)
                            if embedded_target != local(name, True, path.parent):
                                raise ValueError("conflicting source inventory path")
                            inventory_alias_pairs.append((name, value["path"], path.parent,
                                                          embedded_target))
                            # Both lexical declarations must survive an alias race.
                            queue.append(({"path": name, **{k: v for k, v in value.items() if k != "path"}},
                                          path.parent, depth + 1, None))
                            queue.append((value, path.parent, depth + 1, None))
                        else:
                            queue.append(({"path": name, **value}, path.parent, depth + 1, None))
                    else:
                        queue.append(({"path": name, "sha256": value}, path.parent, depth + 1, None))
            if "external_raw_carrier" in document or "external_raw_carrier_sha256" in document:
                if not isinstance(document.get("external_raw_carrier"), str) or not isinstance(document.get("external_raw_carrier_sha256"), str):
                    raise ValueError("incomplete external source carrier")
                queue.append(({"path": document["external_raw_carrier"],
                               "sha256": document["external_raw_carrier_sha256"]}, path.parent, depth + 1, None))
        for value in spec["owned_paths"]:
            resolved = local(value, True)
            disjoint(resolved)
            reads.add(resolved)
        if len(reads) > 256:
            raise ValueError("source and owned scope bound")
        owned = [Path(local(value, True)) for value in spec["owned_paths"]]
        def candidate_path(value):
            if not isinstance(value, str) or not value.strip() or "://" in value:
                raise ValueError("unknown candidate product")
            path = Path(value)
            choices = {path.resolve()} if path.is_absolute() else {
                (root / path).resolve(), *(directory / path for directory in owned if directory.is_dir())}
            choices = {path.resolve() for path in choices if path.is_file()}
            if len(choices) != 1:
                raise ValueError("missing or ambiguous candidate product")
            return choices.pop()
        if len(task.get("candidate_products", [])) > 256:
            return None
        products = {candidate_path(value) for value in task.get("candidate_products", [])}
        candidates = set(products)
        for path in owned:
            if path.is_file():
                candidates.add(path)
            else:
                for name in ("MANIFEST.json", "ARTIFACT_MANIFEST.json"):
                    if (path / name).is_file():
                        candidates.add((path / name).resolve())
        expected = task["candidate_identity"].removeprefix("sha256:").lower()
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            return None
        candidate_seals, candidate_bytes = {}, 0
        def content_seal(path):
            nonlocal candidate_bytes
            disjoint(path)
            if str(path) not in candidate_seals:
                digestor = hashlib.sha256()
                with path.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        candidate_bytes += len(chunk)
                        if candidate_bytes > 64 * 1024 * 1024:
                            raise ValueError("candidate binding byte bound")
                        digestor.update(chunk)
                candidate_seals[str(path)] = digestor.hexdigest()
            return candidate_seals[str(path)]
        binding = next((path for path in sorted(candidates) if content_seal(path) == expected), None)
        if binding is None:
            return None
        if binding.suffix.lower() == ".json":
            manifest_raw, manifest = metadata(binding)
            if hashlib.sha256(manifest_raw).hexdigest() != expected:
                return None
            declarations = {}
            for inventory in ("files", "products_sha256", "products", "inventory"):
                if inventory not in manifest:
                    continue
                entries = manifest[inventory]
                if isinstance(entries, dict):
                    entries = list(entries.items())
                elif isinstance(entries, list) and inventory in {"files", "products", "inventory"}:
                    if not all(isinstance(row, dict) and "path" in row for row in entries):
                        return None
                    entries = [(row["path"], row) for row in entries]
                else:
                    return None
                if entries and (manifest.get("task_id", task_id) != task_id
                                or manifest.get("input_identity", spec["input_identity"]) != spec["input_identity"]):
                    return None
                for name, record in entries:
                    if inventory == "inventory" and (not isinstance(record, dict)
                            or set(record) - {"path", "sha256", "size_bytes", "bytes", "resolved_path"}
                            or not any(k in record for k in ("size_bytes", "bytes"))):
                        return None
                    path = Path(local(name, True, binding.parent))
                    declared_hash = record.get("sha256") if isinstance(record, dict) else record
                    if not isinstance(declared_hash, str) or len(declared_hash) != 64:
                        return None
                    if str(path) in declarations and declarations[str(path)] != declared_hash:
                        return None
                    declarations[str(path)] = declared_hash
                    if isinstance(record, dict):
                        if "path" in record and Path(local(record["path"], True, binding.parent)) != path:
                            return None
                        if "resolved_path" in record and record["resolved_path"] != str(path):
                            return None
                        for size_key in ("size_bytes", "bytes"):
                            if size_key in record and (type(record[size_key]) is not int
                                                       or record[size_key] != path.stat().st_size):
                                return None
                    if content_seal(path) != declared_hash:
                        return None
                    products.add(path)
        for path in products:
            content_seal(path)
        reads.update(candidate_seals)
        for value in reads:
            disjoint(value)
        if any(not Path(alias).is_file() or str(Path(alias).resolve()) != resolved
               for alias, resolved in aliases.items()):
            raise ValueError("source alias redirected during review planning")
        if any(local(key, True, parent) != target
               or local(embedded, True, parent) != target
               for key, embedded, parent, target in inventory_alias_pairs):
            raise ValueError("source inventory aliases diverged during review planning")
        return {"scope": {"candidate_identity": task["candidate_identity"],
                           "input_identity": spec["input_identity"], "spec_identity": digest(spec),
                           "read_paths": sorted(reads), "source_contracts": contracts,
                           "source_seals": source_seals, "source_aliases": aliases,
                           "candidate_binding": str(binding), "candidate_seals": candidate_seals},
                "acquisition": acquisition}
    except (OSError, ValueError, TypeError, KeyError):
        return None


def _review_context_matches(state: dict, packet: dict, *, allow_running: bool = False) -> bool:
    context = _review_context(state, packet["task_id"], allow_running=allow_running)
    expected = packet.get("review_context", {})
    return bool(context and context["scope"] == expected.get("scope")
                and (context["acquisition"] is None or context["acquisition"] == expected.get("acquisition"))
                and packet.get("candidate_identity") == context["scope"]["candidate_identity"]
                and packet.get("input_identity") == context["scope"]["input_identity"])


def next_packet(state: dict, policy: dict, profiles: set[tuple[str, str]], *, review_only: bool = False) -> dict:
    """Reserve one fair, dependency-ready opportunity; transport availability is live."""
    if _writer_reserved(state):
        return summary(state)
    _validate_released_acquisitions(state)
    for packet in state.get("adaptive", {}).get("packets", {}).values():
        if packet["state"] == "planned":
            return summary(state) if review_only else copy.deepcopy(packet)
        if packet["state"] == "running":
            return summary(state)
    # One outstanding packet prevents competing writers and makes interruption replay exact.
    for p in state["packets"].values():
        task = state["tasks"][p["task_id"]]
        if task["state"] == "planned" and task.get("packet_id") == p["packet_id"]:
            if review_only and (p["phase"] != "review" or not p.get("review_only")):
                return summary(state)
            if p.get("review_only") and not _review_context_matches(state, p):
                return summary(state)
            if p["phase"] == "escalation":
                repair_id = _task_repair_id(state, p["task_id"])
                require(_repair_approved(state, repair_id), "escalation requires its exact authorized operative issue")
                _validate_repair_binding(state, repair_id, p["task_id"])
                if repair_id in state.get("repair_authorizations", {}):
                    require(p.get("approved_repair_id") == repair_id
                            and p.get("repair_authorization_identity") == digest(state["repair_authorizations"][repair_id]),
                            "stale registered escalation packet binding")
            return copy.deepcopy(p)
    if not review_only and any(t["state"] == "running" for t in state["tasks"].values()):
        return summary(state)
    ready = summary(state)["ready"]
    if review_only:
        ready = [key for key in ready if _review_context(state, key) is not None]
    unavailable = []
    for key in sorted(ready, key=lambda k: (state["tasks"][k]["last_turn"], k)):
        t = state["tasks"][key]
        route = resolve_route(policy, route_for(t), profiles)
        if route["transport_selected"] is None:
            unavailable.append({"task_id": key, "route": route})
            continue
        spec = t["spec"]
        attempt = t["attempt"] + 1
        identity = {"campaign": state["campaign_identity"], "task_id": key,
                    "attempt": attempt, "phase": t["phase"], "input_identity": spec["input_identity"],
                    "candidate_identity": t.get("candidate_identity")}
        # Bind future appended assignments without changing historical packet identities.
        frontier = next((f for f in state.get("frontiers", [])
                         if any(row["id"] == key for row in f["frontier"]["tasks"])), None)
        if frontier is not None:
            identity.update(frontier_identity=frontier["identity"], task_spec_identity=digest(spec))
        effective_repair = _task_repair_id(state, key)
        if t["phase"] == "escalation":
            require(_repair_approved(state, effective_repair), "escalation requires its exact authorized operative issue")
        if effective_repair in state.get("repair_authorizations", {}):
            identity.update(approved_repair_id=effective_repair,
                            repair_authorization_identity=digest(state["repair_authorizations"][effective_repair]))
        review_context = _review_context(state, key) if review_only else None
        if review_only:
            require(route["route"] == "review_or_research", "review-only route must be read-only")
            identity.update(review_only=True, review_context_identity=digest(review_context))
        packet_id = digest(identity)
        selected = route["transport_selected"]
        # Prompts carry resumable receipt references; durable state retains every raw outcome.
        history_refs = [{"phase": event["phase"], "packet_id": event["packet_id"],
                         "receipt": event["receipt"], "outcome": event["result"].get("outcome"),
                         "candidate_identity": event["result"].get("candidate_identity")}
                        for event in t["history"][-2:]]
        prompt = (("Review-only slot: do not modify candidate, inputs, acquisition outputs or controller state. "
                   "The host alone stores the review receipt outside those paths and serializes state mutations. "
                   if review_only else "") + "Execute this bounded HTT campaign assignment. Do not spawn children. "
                  "No native low-ell solver or ODE evolution; preserve HTT/MIO and transfer provenance. "
                  "Do not weaken acceptance or promote scoped diagnostics. Research/escalation/review "
                  "are read-only. Review must be independent of all recorded authors. "
                  "Return a result JSON bound to packet_id, task_id, input_identity, plus a local "
                  "raw_receipt path. Never claim dispatch from this packet. Assignment:\n" +
                  json.dumps({**identity, "packet_id": packet_id, "spec": spec,
                              "issue": t.get("issue"), "repair_plan": t.get("repair_plan"),
                              "repair_authorization": state.get("repair_authorizations", {}).get(effective_repair),
                              **({"review_context": review_context} if review_only else {}),
                              "resume_evidence": t.get("resume_evidence"),
                              "scientific_resume": t.get("scientific_resume"),
                              "transport_resume": t.get("transport_resume"),
                              "repair_input_transition": t.get("repair_input_transition"),
                              "authors": t["authors"], "contributors": t["contributors"],
                              "history_refs": history_refs, "history_total": len(t["history"])}, ensure_ascii=False))
        p = {**identity, "packet_id": packet_id, "route": route,
             "resume_evidence": copy.deepcopy(t.get("resume_evidence")),
             "scientific_resume": copy.deepcopy(t.get("scientific_resume")),
             "transport_resume": copy.deepcopy(t.get("transport_resume")),
             **({"repair_input_transition": copy.deepcopy(t["repair_input_transition"])}
                if t.get("repair_input_transition") else {}),
             "launch_performed": False, "observed_runtime": "UNKNOWN",
             "native_tool": "collaboration.spawn_agent",
             **({"review_only": True, "review_context": review_context} if review_only else {}),
             "spawn_args": {"task_name": "rc_" + packet_id[:16], "fork_turns": "none",
                            "model": selected["model"], "reasoning_effort": selected["effort"],
                            "message": prompt}}
        t.update(state="planned", attempt=attempt, packet_id=packet_id, last_turn=state["turn"])
        state["turn"] += 1
        state["packets"][packet_id] = p
        state["events"].append({"type": "planned", "packet_id": packet_id})
        return copy.deepcopy(p)
    if not ready and not review_only:
        discovery = _adaptive_next(state, policy, profiles)
        if discovery is not None:
            return discovery
    return {**summary(state), "unavailable": unavailable,
            "status": "HOLD_TRANSPORT_UNAVAILABLE" if ready else summary(state)["status"]}


def _concrete_repair_plan(plan: object) -> bool:
    """Preserve the recorded representation and identity of string/object plans."""
    return (isinstance(plan, str) and bool(plan.strip())) or (isinstance(plan, dict) and bool(plan))


def _repair_followup(state: dict, p: dict, t: dict, agent_id: str, evidence: str) -> dict:
    """Validate explicit host followup evidence; never relabel a reused thread as fresh."""
    require(t["phase"] == p["phase"] == "repair", "followup allowed only for planned repair")
    plan = t.get("repair_plan")
    require(_concrete_repair_plan(plan), "followup needs concrete recorded repair plan")
    seal = _receipt(evidence)
    data = json.loads(Path(seal["path"]).read_text())
    require(isinstance(data, dict), "followup evidence must be an object")
    fields = ("native_tool", "task_id", "agent_id", "phase", "packet_id", "input_identity",
              "repair_plan_identity", "base_packet_id")
    dispatched = data.get("status") == "dispatched"
    if not dispatched:
        fields += ("candidate_identity", "raw_receipt", "raw_receipt_sha256")
    require(all(isinstance(data.get(k), str) and data[k].strip() for k in fields),
            "followup evidence requires nonempty string identities and receipt path/hash")
    require(data.get("native_tool") == "collaboration.followup_task"
            and data.get("task_id") == p["task_id"] and data.get("agent_id") == agent_id
            and data.get("phase") == "repair" and data.get("packet_id") == p["packet_id"]
            and data.get("input_identity") == p["input_identity"] == t["spec"]["input_identity"]
            and data.get("repair_plan_identity") == digest(plan), "stale followup assignment/plan")
    prior = [q for q in state["packets"].values() if q.get("agent_id") == agent_id]
    history = {e["packet_id"]: e for e in t["history"]}
    require(prior and agent_id in t["authors"] and all(
        q["task_id"] == p["task_id"] and q["phase"] in {"execute", "repair"}
        and q["packet_id"] in history for q in prior),
        "followup requires prior same-task implementation author with recorded outcomes")
    # A followup resumes the original native thread; its role/profile cannot be
    # retargeted by a newly selected repair packet (notably Astra theory execute).
    implementation_routes = {"subagent_specialist", "general_code", "routine_mechanical"}
    route = p["route"]
    require(route.get("route") in implementation_routes and route.get("transport_selected")
            and all(q["route"].get("route") in implementation_routes
                    and q["route"].get("requested") == route["requested"]
                    and q["route"].get("transport_selected") == route["transport_selected"]
                    for q in prior), "followup requires unchanged implementation route/profile")
    source = history.get(data.get("base_packet_id"), {})
    source_result = source.get("result", {})
    initial_failure = source_result.get("outcome") == "blocker"
    if initial_failure:
        base = state["packets"].get(data.get("base_packet_id"), {})
        issue = source_result.get("issue", {})
        implementation_history = [h for h in t["history"]
                                  if h.get("phase") in {"execute", "repair"}
                                  and h.get("result", {}).get("agent_id") == agent_id]
        require(dispatched and implementation_history and source == implementation_history[-1]
                and all(history[q["packet_id"]].get("result", {}).get("outcome") in {"success", "blocker"}
                        for q in prior)
                and base.get("launch_performed") is True and base.get("agent_id") == agent_id
                and base.get("task_id") == p["task_id"] and base.get("phase") == source.get("phase")
                and source.get("phase") in {"execute", "repair"}
                and source_result.get("packet_id") == base.get("packet_id") == data.get("base_packet_id")
                and source_result.get("task_id") == p["task_id"]
                and source_result.get("agent_id") == agent_id
                and source_result.get("input_identity") == base.get("input_identity") == p["input_identity"]
                and issue.get("class") in {"code", "numeric"} and issue.get("substantive") is True
                and issue.get("input_identity") == p["input_identity"]
                and all(value is None for value in (source_result.get("candidate_identity"),
                    base.get("candidate_identity"), t.get("candidate_identity"), p.get("candidate_identity"),
                    data.get("base_candidate_identity")))
                and not any(h.get("result", {}).get("outcome") == "success"
                            and h.get("result", {}).get("candidate_identity") for h in t["history"]),
                "followup needs latest acknowledged substantive initial implementation failure without candidate")
        base_receipt = source.get("receipt")
        require(isinstance(base_receipt, dict) and data.get("base_raw_receipt") == base_receipt
                and _receipt(source_result.get("raw_receipt", "")) == base_receipt,
                "initial failure followup needs exact stored raw receipt seal")
    else:
        require(isinstance(data.get("base_candidate_identity"), str) and data["base_candidate_identity"].strip(),
                "followup needs nonempty base candidate identity")
        require(source.get("phase") in {"execute", "repair"}
            and source_result.get("agent_id") == agent_id and source_result.get("outcome") == "success"
            and source_result.get("input_identity") == p["input_identity"]
            and source_result.get("candidate_identity") == data.get("base_candidate_identity")
            == t.get("candidate_identity") == p.get("candidate_identity")
            and bool(t.get("candidate_identity")), "stale followup source candidate/author")
    if dispatched:
        require(data.get("requested") == route["requested"]
                and data.get("transport_selected") == route["transport_selected"],
                "followup dispatch must bind unchanged route/profile")
        raw = _receipt(data.get("host_call_receipt", ""))
        require(raw["sha256"] == data.get("host_call_receipt_sha256"), "host dispatch receipt hash mismatch")
        host = json.loads(Path(raw["path"]).read_text())
        require(isinstance(host, dict) and host.get("dispatch_accepted") is True
                and all(host.get(k) == data.get(k) for k in
                        ("native_tool", "agent_id", "packet_id", "task_id", "input_identity")),
                "host followup receipt must bind actual accepted dispatch")
        return {"mode": "dispatched", "evidence": seal, "host_call_receipt": raw,
                "native_tool": data["native_tool"], "base_packet_id": data["base_packet_id"],
                "base_candidate_identity": data.get("base_candidate_identity"),
                "repair_plan_identity": data["repair_plan_identity"],
                **({"base_raw_receipt": base_receipt} if initial_failure else {})}
    candidate = data.get("candidate_identity")
    require(isinstance(candidate, str) and candidate.strip()
            and candidate != t["candidate_identity"], "followup needs new candidate identity")
    raw = _receipt(data.get("raw_receipt", ""))
    require(raw["sha256"] == data.get("raw_receipt_sha256")
            and raw["sha256"] not in {e["receipt"]["sha256"] for e in t["history"]},
            "followup needs new matching raw receipt")
    receipt_data = json.loads(Path(raw["path"]).read_text())
    require(isinstance(receipt_data, dict) and all(receipt_data.get(k) == data.get(k) for k in
            ("task_id", "agent_id", "input_identity", "base_packet_id", "base_candidate_identity",
             "candidate_identity")), "followup raw receipt identity mismatch")
    return {"evidence": seal, "native_tool": data["native_tool"], "base_packet_id": data["base_packet_id"],
            "base_candidate_identity": data["base_candidate_identity"], "candidate_identity": candidate,
            "repair_plan_identity": data["repair_plan_identity"], "raw_receipt": raw}


def acknowledge(state: dict, packet_id: str, agent_id: str, observed: str = "UNKNOWN",
                followup_evidence: str | None = None) -> None:
    require(not _writer_reserved(state), "acquisition resume owns the native writer slot")
    _validate_released_acquisitions(state)
    adaptive_packets = state.get("adaptive", {}).get("packets", {})
    if packet_id in adaptive_packets:
        p = adaptive_packets[packet_id]
        require(p["state"] == "planned", "discovery packet not awaiting launch")
        require(isinstance(agent_id, str) and agent_id.strip(), "actual native agent ID required")
        require(not followup_evidence, "discovery requires a fresh native context")
        require(not any(q.get("agent_id") == agent_id for q in
                        [*state["packets"].values(), *adaptive_packets.values()]), "fresh native discovery launch required")
        p.update(state="running", agent_id=agent_id, launch_performed=True, observed_runtime=observed)
        return
    require(packet_id in state["packets"], "unknown packet")
    p = state["packets"][packet_id]
    t = state["tasks"][p["task_id"]]
    require(t.get("packet_id") == packet_id and t["state"] == "planned", "packet not awaiting launch")
    if p.get("review_only"):
        require(p["phase"] == t["phase"] == "review" and _review_context_matches(state, p),
                "review-only candidate, input, dependency or acquisition scope changed")
        selected = p["route"].get("transport_selected")
        require(p["route"].get("route") == "review_or_research" and selected
                and p["spawn_args"].get("model") == selected["model"]
                and p["spawn_args"].get("reasoning_effort") == selected["effort"],
                "review-only route must remain supported and read-only")
    require(agent_id.strip(), "actual native agent ID required")
    require(agent_id not in t["contributors"] if t["phase"] == "review" else True,
            "reviewer must be independent of all implementation/research/escalation contributors")
    reused = any(q.get("agent_id") == agent_id for q in
                 [*state["packets"].values(), *adaptive_packets.values()])
    require(not reused or followup_evidence, "fresh native launch required; agent ID already used")
    continuation = None
    if followup_evidence is not None:
        require(reused, "followup evidence requires an actual prior author thread")
        continuation = _repair_followup(state, p, t, agent_id, followup_evidence)
    if t["phase"] == "escalation":
        repair_id = _task_repair_id(state, p["task_id"])
        require(_repair_approved(state, repair_id), "escalation requires its exact authorized operative issue")
        _validate_repair_binding(state, repair_id, p["task_id"])
        if repair_id in state.get("repair_authorizations", {}):
            require(p.get("approved_repair_id") == repair_id
                    and p.get("repair_authorization_identity") == digest(state["repair_authorizations"][repair_id]),
                    "stale registered escalation packet binding")
        require(repair_id not in state["ultra_repairs"], "actual ultra launch allowance already consumed")
        state["ultra_repairs"][repair_id] = {"task_id": p["task_id"], "packet_id": packet_id,
                                             "agent_id": agent_id,
                                             "operative_issue_identity": _operative_issue_identity(t["issue"])}
        state["ultra_pending"].pop(repair_id, None)
        t["ultra_used"].append(repair_id)
    p.update(agent_id=agent_id, launch_performed=True, observed_runtime=observed)
    t["state"] = "running"
    if continuation:
        p.update(native_tool="collaboration.followup_task", continuation=continuation)
    if agent_id not in t["contributors"]:
        t["contributors"].append(agent_id)
    if t["phase"] not in {"research", "escalation", "review"} and agent_id not in t["authors"]:
        t["authors"].append(agent_id)
    state["events"].append({**({"continuation": continuation} if continuation else {}),
                            "type": "followup_acknowledged" if continuation else "launched",
                            "packet_id": packet_id, "agent_id": agent_id,
                            "requested": p["route"]["requested"], "observed_runtime": observed})


def _receipt(path: str) -> dict:
    p = Path(path)
    require(p.is_file(), "raw receipt file required")
    return {"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def launch_failed(state: dict, packet_id: str, evidence: str, classification: str, reason: str,
                  retry_prohibited: bool = False) -> None:
    """Preserve a real pre-launch transport/quota refusal without inventing an agent."""
    require(not _writer_reserved(state), "acquisition resume owns the native writer slot")
    _validate_released_acquisitions(state)
    adaptive_packets = state.get("adaptive", {}).get("packets", {})
    if packet_id in adaptive_packets:
        p = adaptive_packets[packet_id]
        require(p["state"] == "planned", "not an unacknowledged discovery launch")
        require(classification in {"environment", "permission", "transport"} and reason.strip(),
                "exact launch refusal classification/reason required")
        receipt = _receipt(evidence)
        p.update(state="held", hold={"class": classification,
                 "exact_missing_or_defect": reason, "receipt": receipt,
                 "retry_prohibited": bool(retry_prohibited or "exhaust" in reason.lower()
                                          or "monthly quota" in reason.lower())})
        return
    require(packet_id in state["packets"], "unknown packet")
    p = state["packets"][packet_id]
    t = state["tasks"][p["task_id"]]
    require(t["state"] == "planned" and t.get("packet_id") == packet_id, "not an unacknowledged launch")
    require(classification in {"environment", "permission", "transport"} and reason.strip(),
            "exact launch refusal classification/reason required")
    receipt = _receipt(evidence)
    hold = {"class": classification, "exact_missing_or_defect": reason, "receipt": receipt,
            "retry_prohibited": bool(retry_prohibited or "exhaust" in reason.lower()
                                     or "monthly quota" in reason.lower())}
    t.update(state="held", hold=hold)
    repair_id = _task_repair_id(state, p["task_id"])
    pending = state["ultra_pending"].get(repair_id)
    if pending and pending["task_id"] == p["task_id"]:
        state["ultra_pending"].pop(repair_id)
    state["events"].append({"type": "launch_refused", "packet_id": packet_id, "hold": hold,
                            "launch_performed": False, "observed_runtime": "UNKNOWN"})


def resume(state: dict, task_id: str, evidence: str, input_identity: str,
           approved_repair_id: str | None = None) -> None:
    """Reopen only on a typed semantic delta or exact prelaunch restoration."""
    require(task_id in state["tasks"], "unknown task")
    t = state["tasks"][task_id]
    require(t["state"] == "held", "only held branches may resume")
    receipt = _receipt(evidence)
    try:
        delta = json.loads(Path(evidence).read_text())
    except (ValueError, TypeError) as exc:
        raise ControllerError("typed semantic JSON evidence required") from exc
    _semantic_delta(delta)
    require(not any(e.get("type") == "resume" and e.get("task_id") == task_id
                    and e.get("semantic_delta") is not None
                    and _semantic_projection(e["semantic_delta"]) == _semantic_projection(delta)
                    for e in state["events"]),
            "semantic evidence already used; do not rename exhausted attempts")
    require(input_identity.strip(), "input_identity required")
    if approved_repair_id:
        require(_repair_approved(state, approved_repair_id),
                "repair was not covered by campaign authorization")
    bound_repair = approved_repair_id or _task_repair_id(state, task_id)
    prospective_spec = t["spec"] if delta["kind"] == "prelaunch_transport" else {**t["spec"], "input_identity": input_identity}
    _validate_repair_binding(state, bound_repair, task_id, spec=prospective_spec,
                            delta=None if delta["kind"] == "prelaunch_transport" else delta)
    if delta["kind"] == "prelaunch_transport":
        require(not t.get("hold", {}).get("retry_prohibited")
                and not any(word in t.get("hold", {}).get("exact_missing_or_defect", "").lower()
                            for word in ("exhaust", "monthly quota")),
                "exhausted/prohibited ordinary transport cannot retry")
        packet_id = t.get("packet_id")
        p = state["packets"].get(packet_id, {})
        require(delta.get("packet_id") == packet_id and p and not p.get("launch_performed")
                and not p.get("agent_id"), "only current refused unacknowledged packet may restore")
        require(any(e.get("type") == "launch_refused" and e.get("packet_id") == packet_id
                    for e in state["events"]), "confirmed prelaunch refusal required")
        require(input_identity == p["input_identity"] == t["spec"]["input_identity"]
                and approved_repair_id in {None, _task_repair_id(state, task_id)},
                "transport restore must preserve scientific input and repair")
        if t["phase"] == "escalation":
            repair_id = _task_repair_id(state, task_id)
            require(_repair_approved(state, repair_id), "escalation requires its exact authorized operative issue")
            require(repair_id not in state["ultra_repairs"] and
                    repair_id not in state["ultra_pending"], "ultra repair already used or reserved")
            state["ultra_pending"][repair_id] = {"task_id": task_id, "trigger_packet": packet_id,
                                                "operative_issue_identity": _operative_issue_identity(t["issue"])}
        t["state"] = "ready"
    else:
        require(not any(p.get("launch_performed") and p["packet_id"] == t.get("packet_id")
                        and not any(h["packet_id"] == p["packet_id"] for h in t["history"])
                        for p in state["packets"].values()), "acknowledged unknown outcome cannot replay")
        if approved_repair_id:
            require(approved_repair_id != (t.get("active_repair_id") or t["spec"].get("approved_repair_id"))
                    and approved_repair_id not in state["ultra_repairs"]
                    and approved_repair_id not in state["ultra_pending"],
                    "different unused approved repair required")
            t["active_repair_id"] = approved_repair_id
        t["spec"]["input_identity"] = input_identity
        t["failures"] = []
        t.update(state="ready", phase="research")
    # A transport repair must not erase the scientific change the worker must execute.
    previous = t.get("resume_evidence")
    if (delta["kind"] == "prelaunch_transport" and previous
            and previous["semantic_delta"]["kind"] != "prelaunch_transport"):
        t.setdefault("scientific_resume", copy.deepcopy(previous))
    t["resume_evidence"] = {"semantic_delta": copy.deepcopy(delta), "receipt": receipt,
                            "semantic_identity": digest(_semantic_projection(delta))}
    slot = "transport_resume" if delta["kind"] == "prelaunch_transport" else "scientific_resume"
    t[slot] = copy.deepcopy(t["resume_evidence"])
    if slot == "scientific_resume":
        t.pop("transport_resume", None)
    state["events"].append({"type": "resume", "task_id": task_id, "receipt": receipt,
                            "semantic_delta": delta, "input_identity": input_identity,
                            "approved_repair_id": approved_repair_id})


def _repair_seal(value: dict) -> dict:
    """The transition schema uses path/hash pairs, never predicted identities."""
    require(isinstance(value, dict) and set(value) == {"path", "sha256"}, "exact repair seal required")
    require(isinstance(value["sha256"], str) and len(value["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in value["sha256"]), "full SHA256 required")
    actual = _receipt(value["path"])
    require(actual == value, "stale repair seal: " + str(value.get("path")))
    return actual


def _repair_document(value: dict) -> dict:
    seal = _repair_seal(value)
    require(Path(seal["path"]).stat().st_size <= 8 * 1024 * 1024, "repair metadata too large")
    document = json.loads(Path(seal["path"]).read_text())
    require(isinstance(document, dict), "repair document must be an object")
    return document


def _validate_repair_input_transition(state: dict, result: dict, path: str) -> dict:
    """Validate one explicitly typed source repair without scheduling or ledger mutation."""
    seal = _receipt(path)
    tr = _repair_document(seal)
    fields = {"schema", "kind", "campaign", "task_id", "research_packet_id", "research_result",
              "repair_contract", "before_input", "after_input", "raw_before", "source_review",
              "preparation_contributors"}
    require(set(tr) == fields and tr["schema"] == "htt.repair_input_transition/1"
            and tr["kind"] in {"full7_memory_lifetime_same_science",
                               "saved_law_singleton_test_same_science",
                               "cf4_final_group_fixture_same_science",
                               "cf4_source_layout_same_science"}, "unsupported repair transition")
    if tr["kind"] == "cf4_source_layout_same_science":
        return _validate_cf4_source_layout(state, result, seal, tr)
    if tr["kind"] == "cf4_final_group_fixture_same_science":
        return _validate_cf4_fixture_testfix(state, result, seal, tr)
    if tr["kind"] == "saved_law_singleton_test_same_science":
        return _validate_saved_law_testfix(state, result, seal, tr)
    require(tr["campaign"] == state["campaign_identity"] and tr["task_id"] == result.get("task_id")
            == "R25-PR3-FREQUENCY-TENSOR-CROSSPREDICTION", "repair campaign/task mismatch")
    p = state["packets"].get(result.get("packet_id"), {})
    t = state["tasks"][tr["task_id"]]
    require(tr["research_packet_id"] == p.get("packet_id") and t.get("packet_id") == p.get("packet_id")
            and p.get("launch_performed") is True and p.get("agent_id") == result.get("agent_id")
            and t["state"] == "running" and t["phase"] == p.get("phase")
            and p.get("phase") in {"research", "escalation"} and result.get("outcome") == "success"
            and isinstance(result.get("repair_plan"), str) and result["repair_plan"].strip(),
            "repair requires current acknowledged successful research")
    require(not t.get("repair_input_transition") and not any(
        q.get("task_id") == tr["task_id"] and q.get("packet_id") != p["packet_id"]
        and q.get("launch_performed") and not any(h.get("packet_id") == q.get("packet_id")
        for h in t["history"]) for q in state["packets"].values()), "concurrent or repeated repair transition")
    require(_repair_document(tr["research_result"]) == result, "research result bytes mismatch")
    _repair_seal(tr["repair_contract"])
    before, after = _repair_document(tr["before_input"]), _repair_document(tr["after_input"])
    require(t["spec"]["input_identity"] == result["input_identity"] == p["input_identity"]
            == "sha256:" + tr["before_input"]["sha256"], "old input identity mismatch")
    require(before.get("schema") == "htt.full7_native_input/1"
            and after.get("schema") == "htt.full7_native_input/2", "repair input schema mismatch")
    allowed = {"schema", "source_sha256", "input_sources", "ack_path", "source_contributors", "repair_lineage"}
    require({k:v for k,v in before.items() if k not in allowed}
            == {k:v for k,v in after.items() if k not in allowed}, "scientific input fields changed")
    require(set(after) == set(before) | {"repair_lineage"}, "repair input fields changed")
    require(after["ack_path"] != before["ack_path"] and not Path(after["ack_path"]).exists(),
            "repair requires a future fresh ACK path")
    names = {"full7_consumer.py", "full7_math.py", "test_full7_synthetic.py"}
    require(set(before["source_sha256"]) == set(after["source_sha256"]) == names
            and before["source_sha256"]["full7_math.py"] == after["source_sha256"]["full7_math.py"],
            "repair source set/math changed")
    old_sources, new_sources = before["input_sources"], after["input_sources"]
    require(len(old_sources) == len(new_sources), "repair source inventory changed")
    for old, new in zip(old_sources, new_sources):
        name = Path(old["path"]).name
        if old.get("role") == "code" and name in names:
            require(set(old) == set(new) and {k:v for k,v in old.items() if k not in {"sha256", "bytes"}}
                    == {k:v for k,v in new.items() if k not in {"sha256", "bytes"}}, "code source path changed")
            require(new["sha256"] == after["source_sha256"][name], "new source seal mismatch")
            _repair_seal({"path":new["path"], "sha256":new["sha256"]})
            require(new.get("bytes") == Path(new["path"]).stat().st_size, "source size mismatch")
        else:
            require(old == new, "nonrepair source changed")
    lineage = after["repair_lineage"]
    require(set(lineage) == {"schema", "repair_id", "repair_contract", "research_result", "parent_input",
            "parent_ack", "parent_packet", "parent_raw_receipt", "source_preimages", "checkpoint_seals",
            "historical_controls", "affected_controls", "output_directory", "ledger_path",
            "max_resumed_numerical_attempts"}, "repair lineage fields changed")
    require(lineage["schema"] == "htt.full7_memory_repair_lineage/1"
            and lineage["repair_id"] == "R26-FULL7-MEMORY-LIFETIME-01"
            and lineage["max_resumed_numerical_attempts"] == 1, "repair scope changed")
    for key, target in (("repair_contract", "repair_contract"), ("research_result", "research_result"),
                        ("parent_input", "before_input"), ("parent_raw_receipt", "raw_before")):
        require(lineage[key] == tr[target], "repair lineage seal mismatch: " + key)
    raw = _repair_document(tr["raw_before"])
    ack, parent = _repair_document(lineage["parent_ack"]), _repair_document(lineage["parent_packet"])
    require(ack.get("status") == "CONTROLLER_ACTUAL_DISPATCH_ACKNOWLEDGED"
            and ack.get("native_call_accepted") is True and ack.get("worker_wait_confirmed") is True
            and ack.get("campaign_identity") == state["campaign_identity"]
            and ack.get("task_id") == tr["task_id"] and ack.get("input_sha256") == tr["before_input"]["sha256"]
            and ack.get("controller_packet_receipt") == lineage["parent_packet"]
            and parent.get("packet_id") == ack.get("packet_id")
            and parent.get("launch_performed") is True and parent.get("agent_id") == ack.get("executor_id")
            and state["packets"].get(parent["packet_id"]) == parent, "old actual ACK/packet chain mismatch")
    require(raw.get("input_sha256") == tr["before_input"]["sha256"]
            and raw.get("ack_sha256") == lineage["parent_ack"]["sha256"]
            and raw.get("controller_packet_id") == parent["packet_id"]
            and raw.get("stage_status") == "HOLD_FIRST_FAILURE" and raw.get("first_failures"),
            "unknown or unbound original outcome")
    require(lineage["output_directory"] == "/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run"
            and lineage["ledger_path"] == lineage["output_directory"] + "/RAW_RECEIPT.json", "repair output paths expanded")
    require(Path(lineage["ledger_path"]).read_bytes() == Path(tr["raw_before"]["path"]).read_bytes(),
            "live old ledger changed")
    for row in raw["products"].values():
        require(isinstance(row.get("charged_seconds"), (int,float)) and 0 <= row["charged_seconds"] < 900,
                "product budget exhausted")
        for attempt in row["attempts"]:
            require(attempt.get("child_reaped") is True and attempt.get("status") in {"FINISHED", "FAILED"}
                    and isinstance(attempt.get("exit_code"), int), "old child unresolved")
            proc = Path('/proc') / str(attempt["child_pid"]) / 'stat'
            require(not proc.exists() or proc.read_text().split()[21] != str(attempt["child_start_ticks"]),
                    "old child still running")
    require(set(lineage["source_preimages"]) == names, "source preimages incomplete")
    for name, ref in lineage["source_preimages"].items():
        _repair_seal(ref)
        require(ref["sha256"] == before["source_sha256"][name], "source preimage mismatch")
    expected = {"VALID_" + key + ".npz" for key in raw["products"]} | {"COMMON_SUPPORT_S7.npz"}
    require(set(lineage["checkpoint_seals"]) == expected, "checkpoint inventory changed")
    for name, ref in lineage["checkpoint_seals"].items():
        require(ref["path"] == lineage["output_directory"] + '/' + name, "checkpoint path changed")
        _repair_seal(ref)
    _repair_seal(lineage["historical_controls"])
    require(isinstance(lineage["affected_controls"], list) and lineage["affected_controls"], "affected controls missing")
    require(len({ref["sha256"] for ref in lineage["affected_controls"]}) == len(lineage["affected_controls"]),
            "duplicate affected controls")
    controls_elapsed = 0.0
    for ref in lineage["affected_controls"]:
        control = _repair_document(ref)
        require(control.get("status") == "FINISHED" and control.get("exit_code") == 0
                and control.get("child_reaped") is True and 0 < control.get("elapsed_seconds", 0) <= 30
                and 0 < control.get("ru_maxrss_bytes", 0) <= 2 * 1024**3, "affected control failed/unobserved")
        controls_elapsed += control["elapsed_seconds"]
    require(controls_elapsed <= 30, "shared affected control time exhausted")
    contributors = tr["preparation_contributors"]
    require(isinstance(contributors, list) and {v.get("role") for v in contributors}
            == {"controller_patch", "numerical_source"}, "preparation contributor roles missing")
    for contributor in contributors:
        require(set(contributor) == {"agent_id", "role", "requested_runtime", "observed_runtime", "raw_receipt"}
                and all(contributor.get(k) for k in ("agent_id", "requested_runtime", "observed_runtime")),
                "contributor identity missing")
        _repair_seal(contributor["raw_receipt"])
    require(after["source_contributors"] == before["source_contributors"] + contributors,
            "source contributor history changed")
    review = _repair_document(tr["source_review"])
    require(review.get("decision") == "APPROVE_ONE_BOUNDED_SAME_TASK_MEMORY_REPAIR"
            and review.get("scientific_admission") == "HOLD" and review.get("preserved_scientific_fields") is True
            and review.get("preserved_caps") is True and review.get("unresolved_blocking_findings") == [],
            "source review does not approve bounded repair")
    for key in ("before_input", "after_input", "repair_contract", "raw_before"):
        require(review.get(key) == tr[key], "review binding mismatch: " + key)
    require(review.get("source_sha256") == after["source_sha256"]
            and review.get("affected_controls") == lineage["affected_controls"], "review source/control mismatch")
    agents = set(t["authors"] + t["contributors"] + [v["agent_id"] for v in contributors])
    require(review.get("reviewer_id") and review["reviewer_id"] not in agents
            and agents <= set(review.get("independent_of", [])) and review.get("requested_runtime")
            and review.get("observed_runtime"), "source reviewer not independent")
    require(set(review.get("diffs", {})) == {"controller_patch", "numerical_source"}, "both reviewed diffs required")
    for ref in review["diffs"].values():
        _repair_seal(ref)
    require(review.get("controller_patch") == review["diffs"]["controller_patch"], "controller patch binding mismatch")
    controller_ref = review.get("controller_source")
    _repair_seal(controller_ref)
    require(controller_ref["path"] == str(Path(__file__).resolve()), "review must bind actual controller source")
    test_ref = review.get("controller_tests")
    _repair_seal(test_ref)
    require(test_ref["path"] == str(Path(__file__).resolve().with_name("test_research_controller_frontier.py")),
            "review must bind actual controller tests")
    return {"seal":seal, "document":tr, "after":after,
            "resolved_input_sources": copy.deepcopy(after["input_sources"]) + [
                {**tr["after_input"], "role":"contract",
                 "bytes":Path(tr["after_input"]["path"]).stat().st_size}],
            "parent_ack":lineage["parent_ack"]}


_SAVED_LAW_DIRECTORY = "/mnt/extdrive/workdir/htt_open_data/r26_s04_selected_law_consumer"
_SAVED_LAW_PARENT_SHA256 = {
    "parent_input":"b2a0714920f3161832972bddc0251899f8edbc44473224567839f08e8b8884c0",
    "parent_ack":"8dd199d5709161113437ba09ee8b88d1a0af034599c93e209abe5a4612ec2d17",
    "parent_packet":"1911f54155be18fa2143a048348d9d04a6b4fe06b67edb4aa65e17591a3da8da",
    "parent_raw_receipt":"05d6b2db036bf27d898726145903393c4b54135bde539c8d988b332734b9dbe2",
    "parent_outcome":"5f7fe0e17d977ccfa545cdf39c2e40da422dfde286e33ef7b80fb16a8f7bf1e6",
    "failure_log":"4bfc29039260e1a75f02ca2e90a43aeb4d260ba11577db6ea74d3f3e30fbaeed",
    "repair_contract":"0d94b281cd348e6b7dba567ff71dd295504f222f9ab14e8c859d176fd6e8bd5f",
}


def _validate_saved_law_testfix(state: dict, result: dict, seal: dict, tr: dict) -> dict:
    """One test-only scalar extraction change; no new scientific execution authority."""
    key = "R26-SAVED-SELECTED-LAW-CONSUMPTION"
    require(tr["campaign"] == state["campaign_identity"] and tr["task_id"] == result.get("task_id") == key,
            "repair campaign/task mismatch")
    t = state["tasks"][key]
    p = state["packets"].get(result.get("packet_id"), {})
    require(tr["research_packet_id"] == p.get("packet_id") == t.get("packet_id")
            and p.get("launch_performed") is True and p.get("agent_id") == result.get("agent_id")
            and t["state"] == "running" and t["phase"] == p.get("phase") == "research"
            and result.get("outcome") == "success" and isinstance(result.get("repair_plan"), str)
            and result["repair_plan"].strip(), "repair requires current acknowledged successful research")
    require(not t.get("repair_input_transition") and not any(
        q.get("task_id") == key and q.get("packet_id") != p["packet_id"] and q.get("launch_performed")
        and not any(h.get("packet_id") == q.get("packet_id") for h in t["history"])
        for q in state["packets"].values()), "concurrent or repeated repair transition")
    require(_repair_document(tr["research_result"]) == result, "research result bytes mismatch")
    _repair_seal(tr["repair_contract"])
    before, after = _repair_document(tr["before_input"]), _repair_document(tr["after_input"])
    require(t["spec"]["input_identity"] == result["input_identity"] == p["input_identity"]
            == "sha256:" + tr["before_input"]["sha256"], "old input identity mismatch")
    require(before.get("schema") == "htt.saved_selected_law_frozen_input/1"
            and after.get("schema") == "htt.saved_selected_law_frozen_input/2"
            and before.get("task_id") == key, "repair input schema mismatch")
    allowed = {"schema", "source_code", "repair_lineage"}
    require(set(after) == set(before) | {"repair_lineage"}
            and {k:v for k,v in before.items() if k not in allowed}
            == {k:v for k,v in after.items() if k not in allowed}
            and len(before["source_inputs"]) == 15, "scientific input fields changed")
    names = {"consume.py", "test_consume.py", "plot.py", "run_capped.py"}
    require(set(before["source_code"]) == names
            and set(after["source_code"]) == names | {"run_continuation.py"}, "repair source set changed")
    root = Path(_SAVED_LAW_DIRECTORY)
    require(Path(tr["after_input"]["path"]).parent == root,
            "new frozen input path changed")
    lineage = after["repair_lineage"]
    require(set(lineage) == {"schema", "repair_id", "repair_contract", "research_result", "parent_input",
        "parent_ack", "parent_packet", "parent_raw_receipt", "parent_outcome", "failure_log",
        "source_preimages", "ack_path", "output_directory", "ledger_path", "inherited_seconds_cap",
        "prior_charged_seconds", "inherited_rss_bytes_max", "max_resumed_numerical_attempts"},
        "repair lineage fields changed")
    require(lineage["schema"] == "htt.saved_law_testfix_lineage/1"
            and lineage["repair_id"] == "R26-SAVED-LAW-SINGLETON-01"
            and lineage["inherited_seconds_cap"] == 90
            and lineage["prior_charged_seconds"] == 2.9794867201708257
            and lineage["inherited_rss_bytes_max"] == 2147483648
            and lineage["max_resumed_numerical_attempts"] == 1, "repair caps/scope changed")
    require(lineage["output_directory"] == str(root)
            and lineage["ledger_path"] == str(root / "RUN_ACCOUNTING_TESTFIX.json")
            and Path(lineage["ack_path"]).resolve().is_relative_to(root.resolve())
            and lineage["ack_path"] != str(root / "CONTROLLER_ACK.json")
            and not Path(lineage["ack_path"]).exists()
            and not Path(lineage["ledger_path"]).exists(), "repair requires future fresh ACK/ledger")
    for k, target in (("repair_contract", "repair_contract"), ("research_result", "research_result"),
                      ("parent_input", "before_input"), ("parent_raw_receipt", "raw_before")):
        require(lineage[k] == tr[target], "repair lineage seal mismatch: " + k)
    for k, name in (("parent_input", "FROZEN_INPUT.json"), ("parent_ack", "CONTROLLER_ACK.json"),
                    ("parent_packet", "ACKNOWLEDGED_EXECUTION_PACKET.json"),
                    ("parent_raw_receipt", "RUN_ACCOUNTING.json"),
                    ("parent_outcome", "CONTROLLER_OUTCOME.json"), ("failure_log", "focused_tests.stderr.log")):
        require(lineage[k]["path"] == str(root / name), "parent path changed: " + k)
        _repair_seal(lineage[k])
    require(all(lineage[k]["sha256"] == expected for k, expected in _SAVED_LAW_PARENT_SHA256.items()),
            "frozen saved-law parent identity mismatch")
    require(any(h.get("packet_id") == _repair_document(lineage["parent_packet"]).get("packet_id")
                and h.get("receipt") == tr["raw_before"] for h in t["history"]),
            "parent raw receipt not recorded in task history")
    require(set(lineage["source_preimages"]) == names, "source preimages incomplete")
    for name in names:
        old, new = before["source_code"][name], after["source_code"][name]
        _repair_seal(lineage["source_preimages"][name])
        require(lineage["source_preimages"][name]["sha256"] == old["sha256"], "source preimage mismatch")
        require(old["path"] == new["path"] == str(root / name), "code source path changed")
        if name == "test_consume.py":
            require({k:v for k,v in old.items() if k not in {"bytes", "sha256"}}
                    == {k:v for k,v in new.items() if k not in {"bytes", "sha256"}}, "test metadata changed")
        else:
            require(old == new, "nonrepair source changed")
    for name, row in after["source_code"].items():
        require(row["path"] == str(root / name), "new source path changed")
        _repair_seal({"path":row["path"], "sha256":row["sha256"]})
        require(row["bytes"] == Path(row["path"]).stat().st_size, "source size mismatch")
    preimage = Path(lineage["source_preimages"]["test_consume.py"]["path"]).read_bytes()
    current = Path(after["source_code"]["test_consume.py"]["path"]).read_bytes()
    old_expr, new_expr = b"float(Z@Ginv@Z.T)", b"(Z@Ginv@Z.T).item()"
    require(preimage.count(old_expr) == 1 and current == preimage.replace(old_expr, new_expr, 1),
            "test repair must preserve all other bytes")
    try:
        old_ast, new_ast = ast.parse(preimage), ast.parse(current)
    except SyntaxError as exc:
        raise ControllerError("test source AST invalid") from exc
    methods = [m for c in old_ast.body if isinstance(c, ast.ClassDef) and c.name == "AnalyticContractTests"
               for m in c.body if isinstance(m, ast.FunctionDef)
               and m.name == "test_correlated_prediction_includes_training_uncertainty"]
    nodes = [n for m in methods for n in ast.walk(m) if isinstance(n, ast.Call)
             and ast.dump(n, include_attributes=False) == ast.dump(ast.parse(old_expr.decode(), mode="eval").body,
                                                                   include_attributes=False)]
    require(len(nodes) == 1, "repair expression not unique in affected method")
    class Restore(ast.NodeTransformer):
        count = 0
        def visit_Call(self, node):
            if ast.dump(node, include_attributes=False) == ast.dump(ast.parse(new_expr.decode(), mode="eval").body,
                                                                  include_attributes=False):
                self.count += 1
                return copy.deepcopy(nodes[0])
            return self.generic_visit(node)
    restore = Restore()
    restored = restore.visit(new_ast)
    require(restore.count == 1 and ast.dump(restored, include_attributes=False)
            == ast.dump(old_ast, include_attributes=False), "extra test AST edit")
    ack = _repair_document(lineage["parent_ack"])
    parent = _repair_document(lineage["parent_packet"])
    raw = _repair_document(tr["raw_before"])
    outcome = _repair_document(lineage["parent_outcome"])
    require(ack.get("schema") == "htt.saved_law_actual_controller_ack/1"
            and ack.get("controller_ack") is True and ack.get("native_call_returned_without_error") is True
            and ack.get("worker_wait_confirmed") is True and ack.get("task_id") == key
            and ack.get("input_identity") == parent.get("input_identity") == t["spec"]["input_identity"]
            and ack.get("acknowledged_packet") == lineage["parent_packet"]
            and parent.get("task_id") == key and parent.get("campaign") == state["campaign_identity"]
            and parent.get("packet_id") == ack.get("packet_id") and parent.get("launch_performed") is True
            and parent.get("agent_id") == ack.get("agent_id")
            and state["packets"].get(parent["packet_id"]) == parent, "old actual ACK/packet chain mismatch")
    debit = lineage["prior_charged_seconds"]
    require(raw.get("schema") == "htt.r26.saved_law_cumulative_execution/1" and raw.get("task_id") == key
            and raw.get("controller_ack_file") == lineage["parent_ack"]["path"]
            and raw.get("controller_ack_sha256") == lineage["parent_ack"]["sha256"]
            and raw.get("source_contract_sha256") == ack.get("contract_sha256") == before["owner_contract"]["sha256"]
            and raw.get("seconds_cap") == 90 and raw.get("rss_cap_bytes") == 2147483648
            and raw.get("state") == "FIRST_FAILURE" and raw.get("cumulative_elapsed_seconds") == debit
            and len(raw.get("started_commands", [])) == 1, "original raw accounting mismatch")
    command = raw["started_commands"][0]
    require(command.get("label") == "focused_tests" and command.get("state") == "FIRST_FAILURE"
            and command.get("exit_code") == 1 and command.get("elapsed_seconds") == debit
            and command.get("stop_reason") == "NONZERO_EXIT"
            and command.get("stderr") == lineage["failure_log"]["path"]
            and command.get("stderr_sha256") == lineage["failure_log"]["sha256"], "old child outcome unresolved")
    require(outcome.get("schema") == "htt.r26.controller_execute_outcome/1"
            and all(outcome.get(k) == ack.get(k) for k in ("task_id", "packet_id", "agent_id", "input_identity"))
            and outcome.get("raw_receipt") == tr["raw_before"]["path"]
            and outcome.get("raw_receipt_sha256") == tr["raw_before"]["sha256"]
            and outcome.get("first_failure_log") == lineage["failure_log"]["path"]
            and outcome.get("first_failure_log_sha256") == lineage["failure_log"]["sha256"]
            and outcome.get("validation_evidence", {}).get("consumer") == "NOT_STARTED"
            and outcome.get("validation_evidence", {}).get("plot") == "NOT_STARTED", "parent outcome mismatch")
    contributors = tr["preparation_contributors"]
    require(isinstance(contributors, list) and len(contributors) == 2
            and {v.get("role") for v in contributors} == {"controller_patch", "numerical_source"},
            "preparation contributor roles missing")
    for row in contributors:
        require(set(row) == {"agent_id", "role", "requested_runtime", "observed_runtime", "raw_receipt"}
                and all(row.get(k) for k in ("agent_id", "requested_runtime", "observed_runtime")),
                "contributor identity missing")
        _repair_seal(row["raw_receipt"])
    review = _repair_document(tr["source_review"])
    require(review.get("decision") == "APPROVE_ONE_BOUNDED_SAME_TASK_TEST_REPAIR"
            and review.get("scientific_admission") == "HOLD" and review.get("preserved_scientific_fields") is True
            and review.get("preserved_caps") is True and review.get("unresolved_blocking_findings") == [],
            "source review does not approve bounded repair")
    for k in ("before_input", "after_input", "repair_contract", "raw_before"):
        require(review.get(k) == tr[k], "review binding mismatch: " + k)
    require(review.get("source_code") == after["source_code"], "review source mismatch")
    agents = set(t["authors"] + t["contributors"] + [r["agent_id"] for r in contributors])
    require(review.get("contract_author_id") and review.get("reviewer_id")
            and review["reviewer_id"] not in agents | {review["contract_author_id"]}
            and agents | {review["contract_author_id"]} <= set(review.get("independent_of", []))
            and review.get("requested_runtime") and review.get("observed_runtime"), "source reviewer not independent")
    require(set(review.get("diffs", {})) == {"controller_patch", "numerical_source"}, "both reviewed diffs required")
    for ref in review["diffs"].values():
        _repair_seal(ref)
    require(review.get("controller_patch") == review["diffs"]["controller_patch"], "controller patch binding mismatch")
    for k, name in (("controller_source", "research_controller.py"),
                    ("controller_tests", "test_research_controller_frontier.py")):
        _repair_seal(review.get(k))
        require(review[k]["path"] == str(Path(__file__).resolve().with_name(name)), "review source path mismatch")
    resolved = copy.deepcopy(t["spec"]["input_sources"])
    replacements = {before["source_code"]["test_consume.py"]["path"]:
                    {k:v for k,v in after["source_code"]["test_consume.py"].items() if k != "ast"},
                    tr["before_input"]["path"]: {**tr["after_input"],
                    "bytes":Path(tr["after_input"]["path"]).stat().st_size}}
    require(all(sum(row.get("path") == path for row in resolved) == 1 for path in replacements),
            "old task inventory missing repair sources")
    for row in resolved:
        if row.get("path") in replacements:
            row.update(replacements[row["path"]])
    resolved.append({**{k:v for k,v in after["source_code"]["run_continuation.py"].items() if k != "ast"}, "role":"code"})
    return {"seal":seal, "document":tr, "after":after,
            "resolved_input_sources":resolved, "parent_ack":lineage["parent_ack"]}


_CF4_DIRECTORY = '/mnt/extdrive/workdir/htt_open_data/r26_cf4_final_group_operator_consumer'
_CF4_OLD_SHA256 = {'FROZEN_INPUT.json': '80b8e8104acdc1a19e330179e421ca62b81d106a2327b2e8c0c77045825be8c8',
 'ACTUAL_ACK_EXECUTE.json': 'f2aeab07125cf95e9cd1b5d173c4c6593e5646657dae7f289f43fb44c224158e',
 'ACTUAL_CONTROLLER_APPEND.json': '0913b3be492fcbb44d40f269639c31ea6146e4acd43e429e234584ffe5d3825e',
 'RUN_RECEIPT.json': '804686d2c0f4bbd97ead7719336cdf75d0e38ecb73e2423893c2f6c6b5f7367e',
 'EXECUTOR_RESULT.json': '01d45f80ac6f84590523862824873f4ec7161fbd363171b7df3457785898fe80',
 'EXECUTION.jsonl': 'dfe62a827771cbf83860d2f7551733bdcc8443e6686ad77b13847f53b96b5079',
 'tests.stderr': 'd650844c7654fd873812d8cc61058b6d34397b73785649dcd5098bc4d7698aab',
 'PREPARATION.json': 'aa75537f7695b1a7db330c6c79f2a3675d104debf52fd08c51dc139f2a3db75e',
 'consume.py': 'bc589b660472bba6f9855971a85d5cc48063b9621f06e00a2b94e612182e4cd3',
 'test_consume.py': '938c221f372b473aa895541298ce8b2f8d3226cf27a8f10c9241198f90018e6b',
 'plot.py': '782008788495dca960a785f14fab48716070738acf8225101cf85ba282978513',
 'driver.py': 'd9a30cd370737c5f52f85638a79a08cd8794bae874d8a0696425ac5590662b65'}
_CF4_SOURCE_REVIEW_PATH = '/mnt/extdrive/workdir/htt_open_data/r26_cf4_fixture_source_review/REVIEW.json'
_CF4_TASK = 'R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE'
_CF4_RESEARCH_PACKET = '8bf9a4d1c387fae46a29aa5120f348e5f4cb8c267d0124c6c52a45374de76475'
_CF4_CONTRACT_SHA256 = '162a2abdef2348437da20ce39c195d9362b8bac9be0078039a5ee0b3398fa0ef'
_CF4_ALLOWED_METHODS = {'test_singleton_known_offset_and_zero_point',
                        'test_joint_mean_error_excludes_separately_possible_mean'}


def _cf4_test_ast(old: bytes, new: bytes) -> None:
    """Only the two diagnosed fixture bodies may differ; never import science."""
    try:
        left, right = ast.parse(old), ast.parse(new)
    except SyntaxError as exc:
        raise ControllerError('CF4 test AST invalid') from exc
    for tree in (left, right):
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
                   and n.name == 'FinalGroupOperatorTest']
        require(len(classes) == 1, 'CF4 test class missing')
        methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef)
                   and n.name.startswith('test_')]
        require(len(methods) == 8 and len({m.name for m in methods}) == 8
                and _CF4_ALLOWED_METHODS <= {m.name for m in methods}, 'CF4 test inventory changed')
        for method in methods:
            if method.name in _CF4_ALLOWED_METHODS:
                # Preserve method signatures/decorators as well as all other module AST.
                method.body = [ast.Pass()]
    require(ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False),
            'extra CF4 test AST edit')


def _validate_cf4_fixture_testfix(state: dict, result: dict, seal: dict, tr: dict) -> dict:
    require(tr['campaign'] == state['campaign_identity']
            and tr['task_id'] == result.get('task_id') == _CF4_TASK, 'repair campaign/task mismatch')
    t = state['tasks'][_CF4_TASK]
    p = state['packets'].get(result.get('packet_id'), {})
    require(tr['research_packet_id'] == p.get('packet_id') == t.get('packet_id') == _CF4_RESEARCH_PACKET
            and p.get('launch_performed') is True and p.get('agent_id') == result.get('agent_id')
            and t['state'] == 'running' and t['phase'] == p.get('phase') == 'research'
            and result.get('outcome') == 'success' and isinstance(result.get('repair_plan'), str)
            and result['repair_plan'].strip(), 'repair requires current acknowledged successful research')
    require(not t.get('repair_input_transition') and not any(
        q.get('task_id') == _CF4_TASK and q.get('packet_id') != p['packet_id'] and q.get('launch_performed')
        and not any(h.get('packet_id') == q.get('packet_id') for h in t['history'])
        for q in state['packets'].values()), 'concurrent or repeated repair transition')
    require(_repair_document(tr['research_result']) == result, 'research result bytes mismatch')
    require(_repair_seal(tr['repair_contract'])['sha256'] == _CF4_CONTRACT_SHA256,
            'CF4 research contract changed')
    before, after = _repair_document(tr['before_input']), _repair_document(tr['after_input'])
    require(t['spec']['input_identity'] == result['input_identity'] == p['input_identity']
            == 'sha256:' + tr['before_input']['sha256'], 'old input identity mismatch')
    require(before.get('schema') == 'htt.r26.cf4_final_group_frozen_input/1'
            and after.get('schema') == 'htt.r26.cf4_final_group_frozen_input/2'
            and set(after) == set(before) | {'source_code', 'repair_lineage'}
            and {k:v for k,v in before.items() if k != 'schema'}
            == {k:v for k,v in after.items() if k not in {'schema','source_code','repair_lineage'}},
            'scientific input fields changed')
    require(before['limits']['cap_seconds'] == 600
            and before['limits']['single_invocation_subcap_seconds'] == 120
            and before['limits']['RSS_GiB'] == 2 and before['limits']['BLAS_threads'] == 1,
            'CF4 inherited limits changed')
    root = Path(_CF4_DIRECTORY)
    require(tr['before_input']['path'] == str(root/'FROZEN_INPUT.json')
            and tr['after_input']['path'] == str(root/'FROZEN_INPUT_REPAIR.json'), 'CF4 frozen paths changed')
    for row in [before['frozen_contract'], *before['source_inputs']]:
        _repair_seal(row)
    names = {'consume.py','plot.py','driver.py','test_consume.py',
             'test_consume_repair.py','run_continuation.py'}
    rows = after['source_code']
    require(isinstance(rows, list) and len(rows) == 6
            and {Path(r.get('path','')).name for r in rows} == names, 'CF4 source inventory changed')
    source = {Path(r['path']).name:r for r in rows}
    for name,row in source.items():
        require(set(row) == {'path','sha256','size_bytes'} and row['path'] == str(root/name),
                'CF4 code path/metadata changed')
        _repair_seal({k:row[k] for k in ('path','sha256')})
        require(row['size_bytes'] == Path(row['path']).stat().st_size, 'CF4 source size mismatch')
    _cf4_test_ast((root/'test_consume.py').read_bytes(), (root/'test_consume_repair.py').read_bytes())
    lineage = after['repair_lineage']
    require(set(lineage) == {'task_id','transition_kind','old_input','research_contract','research_result',
        'old_evidence','inherited_accounting','original_code','allowed_repaired_test_methods',
        'future_ack_path','future_source_review_path','future_execution_ledger_path','future_run_receipt_path'}
        and lineage['task_id'] == _CF4_TASK and lineage['transition_kind'] == tr['kind'],
        'CF4 repair lineage scope changed')
    for key,target in (('old_input','before_input'),('research_contract','repair_contract'),
                       ('research_result','research_result')):
        require(lineage[key] == tr[target], 'CF4 lineage seal mismatch: '+key)
    require(tr['before_input']['sha256'] == _CF4_OLD_SHA256['FROZEN_INPUT.json'], 'CF4 old input changed')
    old_names = {'consume.py','plot.py','driver.py','test_consume.py'}
    require(set(lineage['original_code']) == old_names, 'CF4 original code set changed')
    for name,row in lineage['original_code'].items():
        require(row == {'path':str(root/name),'sha256':_CF4_OLD_SHA256[name]}
                and source[name]['sha256'] == row['sha256'], 'CF4 original code changed')
        _repair_seal(row)
    require(len(lineage['allowed_repaired_test_methods']) == 2
            and set(lineage['allowed_repaired_test_methods']) == _CF4_ALLOWED_METHODS,
            'CF4 allowed test methods changed')
    evidence = lineage['old_evidence']
    require(set(evidence) == {'ACTUAL_ACK_EXECUTE.json','ACTUAL_CONTROLLER_APPEND.json',
            'EXECUTION.jsonl','RUN_RECEIPT.json','EXECUTOR_RESULT.json','tests.stderr'},
            'CF4 old failure evidence incomplete')
    for name,row in evidence.items():
        require(row == {'path':str(root/name),'sha256':_CF4_OLD_SHA256[name]}, 'CF4 parent seal changed')
        _repair_seal(row)
    ack = _repair_document(evidence['ACTUAL_ACK_EXECUTE.json'])
    append = _repair_document(evidence['ACTUAL_CONTROLLER_APPEND.json'])
    raw = _repair_document(tr['raw_before'])
    outcome = _repair_document(evidence['EXECUTOR_RESULT.json'])
    parent = state['packets'].get(ack.get('packet_id'), {})
    require(tr['raw_before'] == evidence['RUN_RECEIPT.json'] and ack.get('decision') == 'GO'
            and all(ack.get(k) is True for k in ('controller_ack','native_call_returned_without_error',
                                               'worker_wait_confirmed'))
            and ack.get('task_id') == append.get('task_id') == parent.get('task_id') == _CF4_TASK
            and ack.get('input_identity') == append.get('input_identity') == parent.get('input_identity')
                == result['input_identity']
            and parent.get('launch_performed') is True and parent.get('agent_id') == ack.get('agent_id')
            and ack.get('controller_append_sha256') == evidence['ACTUAL_CONTROLLER_APPEND.json']['sha256']
            and any(h.get('packet_id') == parent.get('packet_id') and h.get('receipt') == tr['raw_before']
                    for h in t['history']), 'CF4 parent ACK/history chain mismatch')
    require(raw.get('status') == 'INTERRUPTED' and raw.get('threads') == 1 and raw.get('cap_seconds') == 600
            and raw.get('cumulative_seconds') == 64.38265966903418
            and raw.get('ack_sha256') == evidence['ACTUAL_ACK_EXECUTE.json']['sha256']
            and raw.get('controller_append_sha256') == evidence['ACTUAL_CONTROLLER_APPEND.json']['sha256']
            and all(outcome.get(k) == ack.get(k) for k in ('task_id','packet_id','agent_id','input_identity'))
            and outcome.get('outcome') == 'blocker' and outcome.get('original_H02') == 'HOLD_UNCHANGED'
            and outcome.get('raw_receipt') == tr['raw_before']['path']
            and outcome.get('products') == dict.fromkeys(('operator','plot','report','result'),'NOT_RUN')
            and outcome.get('test_summary') == {'errors':0,'failures':2,'run':8,
                'stderr':evidence['tests.stderr']['path'],'stderr_sha256':evidence['tests.stderr']['sha256']},
            'unknown or unbound CF4 first outcome')
    events = [json.loads(line) for line in Path(evidence['EXECUTION.jsonl']['path']).read_text().splitlines()]
    starts = [e for e in events if e.get('event') == 'START']
    terminals = [e for e in events if e.get('event') == 'TERMINAL']
    require(len(starts) == len(terminals) == 1 and starts[0].get('stage') == terminals[0].get('stage') == 'tests'
            and terminals[0].get('exitcode') == 1 and terminals[0].get('outcome') == 'FAILED'
            and terminals[0].get('peak_rss_bytes') == 39976960, 'CF4 old child outcome unresolved')
    budget = lineage['inherited_accounting']
    require(set(budget) == {'cap_seconds','cumulative_seconds','future_invocation_seconds_cap',
            'future_scientific_invocations_max','rss_cap_bytes','threads'}
            and budget['cap_seconds'] == 600 and budget['future_invocation_seconds_cap'] == 120
            and budget['future_scientific_invocations_max'] == 1 and budget['rss_cap_bytes'] == 2147483648
            and budget['threads'] == 1 and isinstance(budget['cumulative_seconds'], (int,float))
            and max(64.38265966903418, t.get('accounting', {}).get('seconds', 0))
                <= budget['cumulative_seconds'] < 600,
            'CF4 repair caps/debit changed')
    for key,name in (('future_ack_path','ACTUAL_ACKNOWLEDGED_REPAIR_PACKET.json'),
                     ('future_execution_ledger_path','EXECUTION.jsonl'),('future_run_receipt_path','RUN_RECEIPT.json')):
        require(lineage[key] == str(root/'repair_run'/name) and not Path(lineage[key]).exists(),
                'CF4 repair requires future fresh ACK/ledger/receipt')

    require(lineage['future_source_review_path'] == tr['source_review']['path']
            == _CF4_SOURCE_REVIEW_PATH,
            'CF4 future source review path mismatch')
    contributors = tr["preparation_contributors"]
    require(isinstance(contributors, list) and len(contributors) == 2
            and {v.get("role") for v in contributors} == {"controller_patch", "numerical_source"},
            "preparation contributor roles missing")
    for row in contributors:
        require(set(row) == {"agent_id", "role", "requested_runtime", "observed_runtime", "raw_receipt"}
                and all(row.get(k) for k in ("agent_id", "requested_runtime", "observed_runtime")),
                "contributor identity missing")
        _repair_seal(row["raw_receipt"])
    review = _repair_document(tr["source_review"])
    require(review.get("decision") == "APPROVE_ONE_BOUNDED_SAME_TASK_FIXTURE_REPAIR"
            and review.get("scientific_admission") == "HOLD" and review.get("preserved_scientific_fields") is True
            and review.get("preserved_caps") is True and review.get("unresolved_blocking_findings") == [],
            "source review does not approve bounded repair")
    for k in ("before_input", "after_input", "repair_contract", "raw_before"):
        require(review.get(k) == tr[k], "review binding mismatch: " + k)
    require(review.get("source_code") == after["source_code"], "review source mismatch")
    agents = set(t["authors"] + t["contributors"] + [r["agent_id"] for r in contributors])
    require(review.get("contract_author_id") == p["agent_id"] and review.get("reviewer_id")
            and review["reviewer_id"] not in agents | {review["contract_author_id"]}
            and agents | {review["contract_author_id"]} <= set(review.get("independent_of", []))
            and review.get("requested_runtime") and review.get("observed_runtime"), "source reviewer not independent")
    require(set(review.get("diffs", {})) == {"controller_patch", "numerical_source"}, "both reviewed diffs required")
    for ref in review["diffs"].values():
        _repair_seal(ref)
    require(review.get("controller_patch") == review["diffs"]["controller_patch"], "controller patch binding mismatch")
    for k, name in (("controller_source", "research_controller.py"),
                    ("controller_tests", "test_research_controller_frontier.py")):
        _repair_seal(review.get(k))
        require(review[k]["path"] == str(Path(__file__).resolve().with_name(name)), "review source path mismatch")
    resolved = copy.deepcopy(t['spec']['input_sources'])
    require(sum(row.get('path') == tr['before_input']['path'] for row in resolved) == 1,
            'CF4 contract inventory missing or duplicated')
    for name in old_names:
        require(sum(row.get('path') == str(root/name) and row.get('sha256') == _CF4_OLD_SHA256[name]
                    for row in resolved) == 1, 'CF4 consumed code inventory changed')
    for row in resolved:
        if row.get('path') == tr['before_input']['path']:
            row.update(tr['after_input'], bytes=Path(tr['after_input']['path']).stat().st_size)
    for name in ('test_consume_repair.py','run_continuation.py'):
        require(not any(row.get('path') == source[name]['path'] for row in resolved),
                'CF4 additive code already consumed')
        resolved.append({'path':source[name]['path'],'sha256':source[name]['sha256'],
                         'bytes':source[name]['size_bytes'],'role':'code'})
    return {'seal':seal, 'document':tr, 'after':after,
            'resolved_input_sources':resolved, 'parent_ack':evidence['ACTUAL_ACK_EXECUTE.json']}


_CF4_LAYOUT_CONTRACT_SHA256 = '820723b444ffb5177d7080988fdc563c86a89a5eba13c6cc9d2dbe94da8294ab'
_CF4_LAYOUT_PREFLIGHT_SHA256 = '7799b3df8bd363bed2f8de0d945d6d5b5704a2879231030d92a05f63e52a20de'
_CF4_LAYOUT_REVIEW_PATH = '/mnt/extdrive/workdir/htt_open_data/r26_cf4_source_layout_source_review/REVIEW.json'
_CF4_LAYOUT_PREIMAGES = {'ACTUAL_FIXTURE_INPUT_TRANSITION.json': 'c0414bd6733ed744a233bdc15bd9d932b9ae7f8b9bac81e08262a402ae199184',
 'FROZEN_INPUT_REPAIR.json': '26a4669b02f93d44153c235728ec0813e155fc1acee47d40d8d4ebd783688e59',
 'consume.py': 'bc589b660472bba6f9855971a85d5cc48063b9621f06e00a2b94e612182e4cd3',
 'driver.py': 'd9a30cd370737c5f52f85638a79a08cd8794bae874d8a0696425ac5590662b65',
 'plot.py': '782008788495dca960a785f14fab48716070738acf8225101cf85ba282978513',
 'repair_run/ACTUAL_ACKNOWLEDGED_REPAIR_PACKET.json': '573c93c92f9d73ef8069e92228138671d10508437f17317c4cfb61729c2bedcd',
 'repair_run/ACTUAL_CONTROLLER_REPAIR_PACKET.json': '512293ed8969eeec58f89bdb72ab719493e6bcc88bdbce8d49dcd4bba86c4867',
 'repair_run/EXECUTION.jsonl': 'd89769ea787764049bee4550b0f2ad17853e29415d433e9e58dab3d673a89290',
 'repair_run/EXECUTOR_REPAIR_RESULT.json': '60681fcc1f5800310b50a81cd771140a47c92ffb720c5fb13687e4e90698b6b5',
 'repair_run/RUN_RECEIPT.json': 'f4984863b451e9058d901b9869009f10bf92bd9c4228f982c3bfabe6e906f483',
 'repair_run/consumer.stderr': '456167b6cbb60162bd9bc00bceffe5315e7960c0f0c83249a02d864f04e44f21',
 'repair_run/tests.stderr': '7c0225b3c74e137da14f999b48621707cdaaec50fb77333695af6afb8d0d80d9',
 'run_continuation.py': '32cf77692d0c8c0329a995c374a8bcca3d8d58272aca90469c2c56cf7c891089',
 'test_consume.py': '938c221f372b473aa895541298ce8b2f8d3226cf27a8f10c9241198f90018e6b',
 'test_consume_repair.py': '06f87d40defc07f1364d4ba7fc46fcd5b1fa36b453f9da32526ee1d54e5b3f93'}


def _cf4_parser_ast(old: bytes, new: bytes) -> None:
    """A source-format repair may replace only one parser function body."""
    try:
        trees = [ast.parse(old), ast.parse(new)]
    except SyntaxError as exc:
        raise ControllerError('CF4 parser AST invalid') from exc
    for tree in trees:
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'parse_table3']
        require(len(functions) == 1, 'CF4 parser definition missing or duplicated')
        functions[0].body = [ast.Pass()]
    require(ast.dump(trees[0], include_attributes=False) == ast.dump(trees[1], include_attributes=False),
            'CF4 change outside parser body')


def _validate_cf4_source_layout(state: dict, result: dict, seal: dict, tr: dict) -> dict:
    """Sequential, same-task source ingestion repair; no scheduling or science execution."""
    require(tr['campaign'] == state['campaign_identity']
            and tr['task_id'] == result.get('task_id') == _CF4_TASK, 'CF4 layout task/campaign mismatch')
    t = state['tasks'][_CF4_TASK]; p = state['packets'].get(result.get('packet_id'), {})
    require(tr['research_packet_id'] == p.get('packet_id') == t.get('packet_id')
            and t['state'] == 'running' and t['phase'] == p.get('phase') == 'research'
            and p.get('launch_performed') is True and p.get('agent_id') == result.get('agent_id')
            and result.get('outcome') == 'success' and result.get('repair_plan'),
            'CF4 layout requires actual current successful research')
    require(not any(q.get('task_id') == _CF4_TASK and q.get('packet_id') != p['packet_id']
            and q.get('launch_performed') and not any(h.get('packet_id') == q.get('packet_id')
            for h in t['history']) for q in state['packets'].values()), 'CF4 layout unresolved concurrent packet')
    require(_repair_document(tr['research_result']) == result, 'CF4 layout research result mismatch')
    root = Path(_CF4_DIRECTORY)
    before, after = _repair_document(tr['before_input']), _repair_document(tr['after_input'])
    require(tr['before_input']['path'] == str(root/'FROZEN_INPUT_REPAIR.json')
            and tr['before_input']['sha256'] == _CF4_LAYOUT_PREIMAGES['FROZEN_INPUT_REPAIR.json']
            and t['spec']['input_identity'] == p['input_identity'] == result['input_identity']
                == 'sha256:'+tr['before_input']['sha256']
            and tr['after_input']['path'] == str(root/'FROZEN_INPUT_SOURCE_LAYOUT.json'), 'CF4 layout input identity mismatch')
    require(before['schema'] == 'htt.r26.cf4_final_group_frozen_input/2'
            and after['schema'] == 'htt.r26.cf4_final_group_frozen_input/3'
            and set(after) == set(before) | {'source_layout_code','source_layout_lineage'}
            and {k:v for k,v in before.items() if k != 'schema'}
                == {k:v for k,v in after.items() if k not in {'schema','source_layout_code','source_layout_lineage'}},
            'CF4 layout changed prior scientific input/lineage')
    lineage = after['source_layout_lineage']
    require(set(lineage) == {'task_id','transition_kind','before_input','source_layout_contract',
        'source_layout_preflight','predecessor_transition','failed_parent_evidence','allowed_parser_ast_delta',
        'inherited_accounting','future_ack_path','future_execution_ledger_path','future_run_receipt_path',
        'future_source_review_path','research_result_future_path','research_packet_status'}
        and lineage['task_id'] == _CF4_TASK and lineage['transition_kind'] == tr['kind']
        and lineage['before_input'] == tr['before_input'] and lineage['source_layout_contract'] == tr['repair_contract']
        and lineage['allowed_parser_ast_delta'] == 'parse_table3_body_only'
        and lineage['research_packet_status'] == 'PENDING_GENUINE_CONTROLLER_ACK'
        and lineage['research_result_future_path'] == tr['research_result']['path'], 'CF4 layout lineage mismatch')
    require(_repair_seal(tr['repair_contract'])['sha256'] == _CF4_LAYOUT_CONTRACT_SHA256
            and _repair_seal(lineage['source_layout_preflight'])['sha256'] == _CF4_LAYOUT_PREFLIGHT_SHA256,
            'CF4 layout contract/preflight changed')
    predecessor = _repair_seal(lineage['predecessor_transition'])
    prior = t.get('repair_input_transition', {})
    require(predecessor == {k:prior.get(k) for k in ('path','sha256')}
            and predecessor['path'] == str(root/'ACTUAL_FIXTURE_INPUT_TRANSITION.json')
            and predecessor['sha256'] == _CF4_LAYOUT_PREIMAGES['ACTUAL_FIXTURE_INPUT_TRANSITION.json']
            and not t.get('repair_input_transition_history'), 'CF4 layout stale/repeated predecessor')
    for name, expected in _CF4_LAYOUT_PREIMAGES.items():
        _repair_seal({'path':str(root/name),'sha256':expected})
    for row in [before['frozen_contract'], *before['source_inputs']]:
        _repair_seal(row)
    evidence = lineage['failed_parent_evidence']
    expected_evidence = {n for n in _CF4_LAYOUT_PREIMAGES if n.startswith('repair_run/')}
    require(set(evidence) == expected_evidence and all(evidence[n] == {'path':str(root/n),
            'sha256':_CF4_LAYOUT_PREIMAGES[n]} for n in expected_evidence), 'CF4 layout parent evidence mismatch')
    ack_ref = evidence['repair_run/ACTUAL_ACKNOWLEDGED_REPAIR_PACKET.json']
    ack = _repair_document(ack_ref)
    packet = _repair_document(evidence['repair_run/ACTUAL_CONTROLLER_REPAIR_PACKET.json'])
    raw = _repair_document(tr['raw_before'])
    require(tr['raw_before'] == evidence['repair_run/RUN_RECEIPT.json']
            and ack['actual_acknowledged_packet'] == evidence['repair_run/ACTUAL_CONTROLLER_REPAIR_PACKET.json']
            and all(ack.get(k) == packet.get(k) for k in ('packet_id','task_id','agent_id','input_identity','phase','launch_performed'))
            and ack['phase'] == 'repair' and ack['launch_performed'] is True
            and ack['decision'] == 'GO' and ack['input_identity'] == result['input_identity']
            and state['packets'].get(packet['packet_id']) == packet
            and any(h.get('packet_id') == packet['packet_id'] and h.get('receipt') == tr['raw_before'] for h in t['history'])
            and raw['cumulative_seconds'] == 75.37988796900027 and raw['status'] == 'INTERRUPTED'
            and raw['ack_sha256'] == ack_ref['sha256'] and raw['products_path'] is None,
            'CF4 layout unbound recorded failure')
    budget = lineage['inherited_accounting']
    require(set(budget) == {'cap_seconds','cumulative_seconds','future_invocation_seconds_cap','rss_cap_bytes','threads'}
            and {k:v for k,v in budget.items() if k != 'cumulative_seconds'} == {'cap_seconds':600,
                'future_invocation_seconds_cap':120,'rss_cap_bytes':2147483648,'threads':1}
            and isinstance(budget['cumulative_seconds'],(int,float))
            and max(75.37988796900027,t.get('accounting',{}).get('seconds',0)) <= budget['cumulative_seconds'] < 600,
            'CF4 layout caps/debit changed')
    for key,name in (('future_ack_path','ACTUAL_ACKNOWLEDGED_SOURCE_LAYOUT_PACKET.json'),
                     ('future_execution_ledger_path','EXECUTION.jsonl'),('future_run_receipt_path','RUN_RECEIPT.json')):
        require(lineage[key] == str(root/'source_layout_run'/name) and not Path(lineage[key]).exists(),
                'CF4 layout requires unique future execution paths')
    paths = ('source_layout/consume.py','source_layout/test_consume_repair.py',
             'source_layout/test_source_layout.py','run_source_layout_continuation.py')
    rows = after['source_layout_code']
    require(isinstance(rows,list) and len(rows) == 4 and {r.get('path') for r in rows} == {str(root/n) for n in paths},
            'CF4 layout additive source paths changed')
    for row in rows:
        require(set(row) == {'path','sha256','size_bytes'}, 'CF4 layout source metadata changed')
        _repair_seal({k:row[k] for k in ('path','sha256')})
        require(row['size_bytes'] == Path(row['path']).stat().st_size, 'CF4 layout source size mismatch')
    require((root/'source_layout/test_consume_repair.py').read_bytes() == (root/'test_consume_repair.py').read_bytes(),
            'CF4 layout eight mathematical tests changed')
    _cf4_parser_ast((root/'consume.py').read_bytes(), (root/'source_layout/consume.py').read_bytes())
    contributors = tr['preparation_contributors']
    require(isinstance(contributors,list) and len(contributors) == 2
            and {r.get('role') for r in contributors} == {'controller_patch','numerical_source'}, 'CF4 layout contributors missing')
    for row in contributors:
        require(set(row) == {'agent_id','role','requested_runtime','observed_runtime','raw_receipt'}
                and all(row.get(k) for k in ('agent_id','requested_runtime','observed_runtime')), 'CF4 layout contributor identity missing')
        _repair_seal(row['raw_receipt'])
    review = _repair_document(tr['source_review'])
    require(lineage['future_source_review_path'] == tr['source_review']['path'] == _CF4_LAYOUT_REVIEW_PATH
            and review.get('decision') == 'APPROVE_ONE_BOUNDED_SAME_TASK_SOURCE_LAYOUT_REPAIR'
            and review.get('scientific_admission') == 'HOLD' and review.get('preserved_scientific_fields') is True
            and review.get('preserved_caps') is True and review.get('unresolved_blocking_findings') == []
            and review.get('source_layout_code') == rows
            and all(review.get(k) == tr[k] for k in ('before_input','after_input','repair_contract','raw_before')),
            'CF4 layout source review mismatch')
    agents = set(t['authors']+t['contributors']+[r['agent_id'] for r in contributors]+[p['agent_id']])
    require(review.get('contract_author_id') == p['agent_id'] and review.get('reviewer_id')
            and review['reviewer_id'] not in agents and agents <= set(review.get('independent_of',[]))
            and review.get('requested_runtime') and review.get('observed_runtime'), 'CF4 layout reviewer not independent')
    require(set(review.get('diffs',{})) == {'controller_patch','numerical_source'}, 'CF4 layout reviewed diffs missing')
    for ref in review['diffs'].values():
        _repair_seal(ref)
    for key,name in (('controller_source','research_controller.py'),('controller_tests','test_research_controller_frontier.py')):
        ref = _repair_seal(review.get(key))
        require(ref['path'] == str(Path(__file__).resolve().with_name(name)), 'CF4 layout reviewed controller path mismatch')
    resolved = copy.deepcopy(t['spec']['input_sources'])
    require(sum(r.get('path') == tr['before_input']['path'] for r in resolved) == 1, 'CF4 layout contract row missing')
    for old in before['source_code']:
        require(sum(r.get('path') == old['path'] and r.get('sha256') == old['sha256'] for r in resolved) == 1,
                'CF4 layout historical source row changed')
    for row in resolved:
        if row.get('path') == tr['before_input']['path']:
            row.update(tr['after_input'],bytes=Path(tr['after_input']['path']).stat().st_size)
    for row in rows:
        require(not any(r.get('path') == row['path'] for r in resolved), 'CF4 layout additive source already consumed')
        resolved.append({'path':row['path'],'sha256':row['sha256'],'bytes':row['size_bytes'],'role':'code'})
    return {'seal':seal,'document':tr,'after':after,'resolved_input_sources':resolved,'parent_ack':ack_ref,
            'predecessor_transition':copy.deepcopy(prior)}


def _bind_repair_input(state: dict, binding: dict) -> None:
    tr, after = binding["document"], binding["after"]
    t = state["tasks"][tr["task_id"]]
    t.setdefault("spec_history", []).append(copy.deepcopy(t["spec"]))
    t["spec"]["input_identity"] = "sha256:" + tr["after_input"]["sha256"]
    t["spec"]["input_sources"] = copy.deepcopy(binding["resolved_input_sources"])
    for row in tr["preparation_contributors"]:
        if row["agent_id"] not in t["contributors"]:
            t["contributors"].append(row["agent_id"])
    if "predecessor_transition" in binding:
        t.setdefault("repair_input_transition_history", []).append(copy.deepcopy(binding["predecessor_transition"]))
    t["repair_input_transition"] = {**binding["seal"], "parent_input":tr["before_input"],
                                     "parent_ack":binding["parent_ack"]}
    state["events"].append({"type":"repair_input_bound", "task_id":tr["task_id"],
                            "transition":copy.deepcopy(t["repair_input_transition"])})


def record(state: dict, result: dict, policy: dict, repair_input_transition: str | None = None) -> None:
    """Apply the transition atomically in memory as well as at checkpoint time."""
    candidate = copy.deepcopy(state)
    binding = (_validate_repair_input_transition(candidate, result, repair_input_transition)
               if repair_input_transition is not None else None)
    _record(candidate, result, policy)
    if binding is not None:
        _bind_repair_input(candidate, binding)
    state.clear()
    state.update(candidate)


def _record(state: dict, result: dict, policy: dict) -> None:
    """Apply one identity-bound native outcome. Caller checkpoints before next action."""
    packet_id = result.get("packet_id")
    if packet_id in state.get("adaptive", {}).get("packets", {}):
        _adaptive_record(state, result)
        return
    require(packet_id in state["packets"], "unknown result packet")
    p = state["packets"][packet_id]
    t = state["tasks"][p["task_id"]]
    require(t["state"] == "running" and t.get("packet_id") == packet_id, "stale or unlaunched result")
    require(result.get("task_id") == p["task_id"] and result.get("input_identity") == p["input_identity"],
            "stale task/input identity")
    require(result.get("agent_id") == p["agent_id"], "result agent identity mismatch")
    if p.get("review_only"):
        require(p["phase"] == t["phase"] == "review"
                and _review_context_matches(state, p, allow_running=True),
                "review-only candidate/input context changed before outcome")
    receipt = _receipt(result.get("raw_receipt", ""))
    if p.get("continuation"):
        continuation = p["continuation"]
        if continuation.get("mode") == "dispatched":
            require(result.get("base_packet_id") == continuation["base_packet_id"]
                    and result.get("base_candidate_identity") == continuation["base_candidate_identity"],
                    "followup result must bind acknowledged base candidate")
            if "base_raw_receipt" in continuation:
                require(result.get("base_raw_receipt") == continuation["base_raw_receipt"],
                        "followup result must bind acknowledged initial failure receipt")
            require(receipt["sha256"] not in {event["receipt"]["sha256"] for event in t["history"]},
                    "followup result needs a new actual raw receipt")
            raw_data = json.loads(Path(receipt["path"]).read_text())
            require(isinstance(raw_data, dict) and all(raw_data.get(k) == result.get(k) for k in
                    ("packet_id", "task_id", "agent_id", "input_identity", "base_packet_id",
                     "base_candidate_identity", "outcome", "candidate_identity")),
                    "followup raw outcome identity mismatch")
            if "base_raw_receipt" in continuation:
                require(raw_data.get("base_raw_receipt") == continuation["base_raw_receipt"],
                        "followup raw outcome must bind initial failure receipt")
            if result.get("outcome") == "success":
                require(result.get("candidate_identity")
                        and result["candidate_identity"] != continuation["base_candidate_identity"],
                        "followup must produce a new candidate")
        else:
            require(receipt == continuation["raw_receipt"]
                    and result.get("candidate_identity") == continuation["candidate_identity"],
                    "followup result must match acknowledged raw receipt/candidate")
    phase = t["phase"]
    outcome = result.get("outcome")
    require(outcome in {"success", "blocker"}, "outcome must be success or blocker")
    if phase == "review":
        require(result.get("candidate_identity") == t.get("candidate_identity"), "stale reviewed candidate")
    event = {"type": "outcome", "phase": phase, "packet_id": packet_id,
             "receipt": receipt, "result": copy.deepcopy(result)}
    if outcome == "success":
        if phase in {"research", "escalation"}:
            require(_concrete_repair_plan(result.get("repair_plan")), "research must return concrete bounded repair plan")
            t.update(phase="repair", state="ready", repair_plan=result["repair_plan"])
        elif phase == "review":
            require(result.get("candidate_identity") == t.get("candidate_identity"), "stale reviewed candidate")
            require(result.get("acceptance_met") is True and result.get("validation_evidence"),
                    "review requires unchanged acceptance and validation evidence")
            products = result.get("qualified_products", [])
            require(isinstance(products, list) and all(isinstance(v, str) and v.strip() for v in products),
                    "qualified products must be exact product names")
            proposed = t.get("candidate_products", [])
            require(set(products) <= set(proposed), "review cannot invent candidate scientific products")
            t.update(state="completed", qualified_products=products)
        else:
            require(result.get("candidate_identity") and result.get("validation_evidence"),
                    "implementation/acquisition needs candidate identity and meaningful validation")
            targeted = t.get("targeted_repairs", [])
            if phase == "repair" and targeted:
                require(result["candidate_identity"] != targeted[-1]["candidate_identity"],
                        "targeted repair must produce a new candidate identity")
            products = result.get("qualified_products", [])
            require(isinstance(products, list) and all(isinstance(v, str) and v.strip() for v in products),
                    "qualified products must be exact product names")
            t.update(phase="review", state="ready", candidate_identity=result["candidate_identity"],
                     candidate_products=products)
    else:
        issue = result.get("issue", {})
        require(issue.get("class") in {"theory", "numeric", "code", "input", "environment", "permission"},
                "classify blocker: theory/numeric/code/input/environment/permission")
        require(issue.get("question") and issue.get("exact_missing_or_defect"), "precise blocker issue required")
        require(issue.get("input_identity") == p["input_identity"], "blocker input identity changed")
        t["issue"] = copy.deepcopy(issue)
        t["failures"].append({"class": issue["class"], "substantive": issue.get("substantive") is True,
                              "receipt": receipt, "packet_id": packet_id})
        if issue.get("true_external") is True:
            require(issue["class"] == "input", "external payload hold must be an input issue, not a scientific failure")
            payload = issue.get("external_payload", {})
            require(payload.get("required") and payload.get("source_or_owner") and payload.get("exhaustion_receipt"),
                    "external hold needs exact required payload, source/owner and exhausted-route receipt")
            _receipt(payload["exhaustion_receipt"])
        if issue.get("prohibited") is True:
            require(issue["class"] == "permission" and issue.get("prohibition_basis") in {
                "no_native_solver_or_ode", "owner_explicit_prohibition", "auth_wall_no_bypass"},
                "prohibition hold needs explicit applicable permission basis")
        external = issue.get("true_external") is True or issue.get("prohibited") is True
        if external or issue["class"] in {"environment", "permission"}:
            t.update(state="held", hold=issue)
        else:
            repair_id = _task_repair_id(state, p["task_id"])
            approved = _repair_approved(state, repair_id)
            failures = [f for f in t["failures"] if f["class"] == issue["class"] and f["substantive"]]
            two = len({f["receipt"]["sha256"] for f in failures}) >= 2
            high = issue.get("high_consequence") is True and bool(issue.get("risk"))
            # Missing input alone, timeout and unknown runtime never trigger ultra.
            eligible = issue["class"] in {"theory", "numeric", "code"} and (two or high)
            require(policy["escalation"]["max_astra_ultra_repairs_per_approved_scientific_repair"] == 1,
                    "unsupported escalation budget policy")
            if approved and eligible and repair_id not in state["ultra_repairs"] and repair_id not in state["ultra_pending"]:
                _validate_repair_binding(state, repair_id, p["task_id"])
                if repair_id in state.get("repair_authorizations", {}):
                    require(p.get("approved_repair_id") == repair_id
                            and p.get("repair_authorization_identity") == digest(state["repair_authorizations"][repair_id]),
                            "reservation requires the exact registered repair assignment")
                state["ultra_pending"][repair_id] = {"task_id": p["task_id"], "trigger_packet": packet_id,
                                                    "operative_issue_identity": _operative_issue_identity(issue)}
                t.update(phase="escalation", state="ready")
            elif (phase == "review" and issue["class"] in {"code", "numeric"}
                  and isinstance(result.get("repair_plan"), str) and result["repair_plan"].strip()
                  and (not t.get("targeted_repairs") or (
                      isinstance(result.get("counterexample"), dict)
                      and bool(_semantic_meaning(result["counterexample"]))
                      and digest(_semantic_meaning(result["counterexample"])) not in
                          {row.get("counterexample_identity") for row in t["targeted_repairs"]}
                      and digest({"counterexample": _semantic_meaning(result["counterexample"]),
                                  "repair_plan": result["repair_plan"]}) not in
                          {row.get("repair_signature") for row in t["targeted_repairs"]}))):
                # Each fresh concrete reviewer counterexample may have its deterministic closeout.
                # It never resets history or buys another ultra launch.
                t.setdefault("targeted_repairs", []).append({"candidate_identity": t["candidate_identity"],
                    "issue_identity": digest(issue), "packet_id": packet_id,
                    "repair_plan": result["repair_plan"],
                    "counterexample_identity": digest(_semantic_meaning(result.get("counterexample"))),
                    "repair_signature": digest({"counterexample": _semantic_meaning(result.get("counterexample")),
                                                "repair_plan": result["repair_plan"]})})
                t.update(phase="repair", state="ready", repair_plan=result["repair_plan"])
            elif repair_id in state["ultra_repairs"] and phase in {"repair", "review", "escalation"}:
                t.update(state="held", hold={**issue, "reason": "approved repair escalation consumed; new evidence/repair authorization required"})
            elif phase == "research":
                t.update(state="held", hold={**issue, "reason": "research returned no bounded repair; exact residual issue retained"})
            else:
                t.update(phase="research", state="ready")
    t["history"].append(event)
    state["events"].append(event)


def save(path: Path, value: dict) -> None:
    """Atomic checkpoint; completed outcomes retained inside state even if interrupted."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".controller-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("--campaign", type=Path, required=True)
    init.add_argument("--authorization", required=True)
    init.add_argument("--dag", type=Path)
    init.add_argument("--plan", type=Path)
    nxt = sub.add_parser("next")
    nxt.add_argument("--available-profile", action="append", default=[])
    nxt.add_argument("--review-only", action="store_true", help="One disjoint read-only review beside one running acquisition")
    ack = sub.add_parser("ack")
    ack.add_argument("--packet-id", required=True)
    ack.add_argument("--agent-id", required=True)
    ack.add_argument("--observed-runtime", default="UNKNOWN")
    ack.add_argument("--followup-evidence", help="Local identity-bound same-task repair followup JSON")
    rec = sub.add_parser("record")
    rec.add_argument("--result", type=Path, required=True)
    rec.add_argument("--repair-input-transition", type=str)
    refused = sub.add_parser("launch-failed")
    refused.add_argument("--packet-id", required=True)
    refused.add_argument("--evidence", required=True)
    refused.add_argument("--class", dest="classification", required=True,
                         choices=["environment", "permission", "transport"])
    refused.add_argument("--reason", required=True)
    refused.add_argument("--retry-prohibited", action="store_true")
    restore = sub.add_parser("restore-discovery")
    restore.add_argument("--packet-id", required=True)
    restore.add_argument("--evidence", required=True)
    reopen = sub.add_parser("resume")
    reopen.add_argument("--task-id", required=True)
    reopen.add_argument("--evidence", required=True)
    reopen.add_argument("--input-identity", required=True)
    reopen.add_argument("--approved-repair-id")
    append = sub.add_parser("append-frontier")
    append.add_argument("--frontier", type=Path, required=True)
    append.add_argument("--authorization", required=True)
    repair_auth = sub.add_parser("authorize-repair")
    repair_auth.add_argument("--issue", type=Path, required=True)
    repair_auth.add_argument("--authorization", required=True)
    adaptive = sub.add_parser("enable-adaptive")
    adaptive.add_argument("--authorization", required=True)
    delta = sub.add_parser("adaptive-evidence")
    delta.add_argument("--evidence", required=True)
    checkpoint = sub.add_parser("checkpoint-acquisition", help="Validate actual worker handoff and independent host corroboration; never stop processes")
    checkpoint.add_argument("--task-id", required=True)
    checkpoint.add_argument("--worker-receipt", required=True)
    checkpoint.add_argument("--host-evidence", required=True)
    prep = sub.add_parser("prepare-acquisition-resume", help="Reserve writer durably before actual same-agent followup")
    prep.add_argument("--task-id", required=True)
    prep.add_argument("--checkpoint-identity", required=True)
    prep.add_argument("--resume-plan", required=True)
    resume_ack = sub.add_parser("ack-acquisition-resume", help="Record actual accepted same-agent call; unknown calls retain reservation")
    resume_ack.add_argument("--task-id", required=True)
    resume_ack.add_argument("--reservation-identity", required=True)
    resume_ack.add_argument("--dispatch-evidence", required=True)
    resume_ack.add_argument("--observed-runtime", default="UNKNOWN")
    sub.add_parser("summary")
    args = parser.parse_args()
    try:
        # Pin the durable checkpoint once, before either reading or placing sidecars.
        args.state = args.state.resolve()
        policy = load_policy(args.policy) if args.policy else load_policy()
        if args.action == "init":
            require(not args.state.exists(), "refusing to overwrite existing campaign")
            campaign = json.loads(args.campaign.read_text())
            require(bool(args.dag) == bool(args.plan), "supply both --dag and --plan")
            if args.dag:
                campaign = bind_original_contracts(campaign, json.loads(args.dag.read_text()),
                                                   json.loads(args.plan.read_text()))
            state = initialize(campaign, args.authorization)
            output = summary(state)
        else:
            state = json.loads(args.state.read_text())
            require(state["campaign_identity"] == digest(state["campaign"]), "campaign identity changed")
            if args.action == "next":
                profiles = set()
                for profile in args.available_profile:
                    model, sep, effort = profile.rpartition("/")
                    require(sep and model and effort, "expected MODEL/EFFORT")
                    profiles.add((model, effort))
                output = next_packet(state, policy, profiles, review_only=args.review_only)
            elif args.action == "ack":
                acknowledge(state, args.packet_id, args.agent_id, args.observed_runtime, args.followup_evidence)
                output = summary(state)
            elif args.action == "checkpoint-acquisition":
                output = checkpoint_acquisition(state, args.task_id, args.worker_receipt, args.host_evidence)
            elif args.action == "prepare-acquisition-resume":
                output = prepare_acquisition_resume(state, args.task_id, args.checkpoint_identity, args.resume_plan)
            elif args.action == "ack-acquisition-resume":
                acknowledge_acquisition_resume(state, args.task_id, args.reservation_identity, args.dispatch_evidence, args.observed_runtime)
                output = summary(state)
            elif args.action == "record":
                result = json.loads(args.result.read_text())
                record(state, result, policy, args.repair_input_transition)
                # Immutable content-addressed copy; state also includes the full result.
                save(args.state.parent / (args.state.name + ".results") / (digest(result) + ".json"), result)
                output = summary(state)
            elif args.action == "authorize-repair":
                authorize_repair(state, json.loads(args.issue.read_text()), args.authorization)
                output = summary(state)
            elif args.action == "enable-adaptive":
                enable_adaptive(state, args.authorization, str(args.state))
                output = summary(state)
            elif args.action == "adaptive-evidence":
                adaptive_evidence(state, args.evidence)
                output = summary(state)
            elif args.action == "append-frontier":
                append_frontier(state, json.loads(args.frontier.read_text()), args.authorization)
                output = summary(state)
            elif args.action == "resume":
                resume(state, args.task_id, args.evidence, args.input_identity, args.approved_repair_id)
                output = summary(state)
            elif args.action == "restore-discovery":
                restore_discovery(state, args.packet_id, args.evidence)
                output = summary(state)
            elif args.action == "launch-failed":
                launch_failed(state, args.packet_id, args.evidence, args.classification, args.reason,
                              args.retry_prohibited)
                output = summary(state)
            else:
                output = summary(state)
        if args.action != "summary":
            save(args.state, state)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ControllerError, ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
