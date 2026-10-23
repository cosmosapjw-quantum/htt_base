#!/usr/bin/env python3
"""Durable host-driven research state machine; never launches native workers itself."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any

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


def _review_context(state: dict, task_id: str, *, allow_running: bool = False) -> dict | None:
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
    root = Path(__file__).resolve().parents[2]
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
        reads = {local(value, True) for value in spec["owned_paths"]}
        contracts, queue = {}, []
        for source in spec["input_sources"]:
            source = source.get("path") if isinstance(source, dict) else source
            queue.append((Path(local(source, True)), 0))
        metadata_bytes = 0
        while queue:
            path, depth = queue.pop()
            reads.add(str(path))
            if len(reads) > 256:
                return None
            if path.suffix.lower() != ".json" or str(path) in contracts:
                continue
            if depth > 16 or len(contracts) >= 64:
                return None
            raw, document = metadata(path)
            metadata_bytes += len(raw)
            if metadata_bytes > 4 * 1024 * 1024:
                return None
            contracts[str(path)] = hashlib.sha256(raw).hexdigest()
            # Traverse only declared source fields, including nested contracts.
            for group in ("input_sources", "sources", "inputs"):
                entries = document.get(group, [])
                if not isinstance(entries, list):
                    return None
                for entry in entries:
                    if isinstance(entry, dict) and "url" in entry and "path" not in entry:
                        continue
                    if len(queue) + len(reads) >= 256:
                        return None
                    value = entry.get("path") if isinstance(entry, dict) else entry
                    queue.append((Path(local(value, True, path.parent)), depth + 1))
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
            for inventory in ("files", "products_sha256", "products"):
                if inventory not in manifest:
                    continue
                entries = manifest[inventory]
                if isinstance(entries, dict):
                    entries = list(entries.items())
                elif isinstance(entries, list) and inventory != "products_sha256":
                    if not all(isinstance(row, dict) and "path" in row for row in entries):
                        return None
                    entries = [(row["path"], row) for row in entries]
                else:
                    return None
                if entries and (manifest.get("task_id", task_id) != task_id
                                or manifest.get("input_identity", spec["input_identity"]) != spec["input_identity"]):
                    return None
                for name, record in entries:
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
        acquisition = None
        if others:
            owner_id, owner = others[0]
            packet = state["packets"].get(owner.get("packet_id"), {})
            if (not packet.get("launch_performed") or not packet.get("agent_id")
                    or packet.get("task_id") != owner_id or packet.get("phase") != "acquisition"
                    or packet.get("input_identity") != owner["spec"].get("input_identity")
                    or not owner["spec"].get("owned_paths")):
                return None
            writes = sorted({local(value) for value in owner["spec"]["owned_paths"]})
            for read in reads:
                for write in writes:
                    a, b = Path(read), Path(write)
                    if a == b or a.is_relative_to(b) or b.is_relative_to(a):
                        return None
            acquisition = {"task_id": owner_id, "packet_id": owner["packet_id"],
                           "input_identity": packet["input_identity"], "owned_paths": writes}
        return {"scope": {"candidate_identity": task["candidate_identity"],
                           "input_identity": spec["input_identity"], "spec_identity": digest(spec),
                           "read_paths": sorted(reads), "source_contracts": contracts,
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
                              "authors": t["authors"], "contributors": t["contributors"],
                              "history_refs": history_refs, "history_total": len(t["history"])}, ensure_ascii=False))
        p = {**identity, "packet_id": packet_id, "route": route,
             "resume_evidence": copy.deepcopy(t.get("resume_evidence")),
             "scientific_resume": copy.deepcopy(t.get("scientific_resume")),
             "transport_resume": copy.deepcopy(t.get("transport_resume")),
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


def _repair_followup(state: dict, p: dict, t: dict, agent_id: str, evidence: str) -> dict:
    """Validate explicit host followup evidence; never relabel a reused thread as fresh."""
    require(t["phase"] == p["phase"] == "repair", "followup allowed only for planned repair")
    plan = t.get("repair_plan")
    require(isinstance(plan, str) and plan.strip(), "followup needs concrete recorded repair plan")
    seal = _receipt(evidence)
    data = json.loads(Path(seal["path"]).read_text())
    require(isinstance(data, dict), "followup evidence must be an object")
    fields = ("native_tool", "task_id", "agent_id", "phase", "packet_id", "input_identity",
              "repair_plan_identity", "base_packet_id", "base_candidate_identity")
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
                "base_candidate_identity": data["base_candidate_identity"],
                "repair_plan_identity": data["repair_plan_identity"]}
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
    hold = {"class": classification, "exact_missing_or_defect": reason, "receipt": receipt}
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


def record(state: dict, result: dict, policy: dict) -> None:
    """Apply the transition atomically in memory as well as at checkpoint time."""
    candidate = copy.deepcopy(state)
    _record(candidate, result, policy)
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
            require(receipt["sha256"] not in {event["receipt"]["sha256"] for event in t["history"]},
                    "followup result needs a new actual raw receipt")
            raw_data = json.loads(Path(receipt["path"]).read_text())
            require(isinstance(raw_data, dict) and all(raw_data.get(k) == result.get(k) for k in
                    ("packet_id", "task_id", "agent_id", "input_identity", "base_packet_id",
                     "base_candidate_identity", "outcome", "candidate_identity")),
                    "followup raw outcome identity mismatch")
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
            require(result.get("repair_plan"), "research must return concrete bounded repair plan")
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
                record(state, result, policy)
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
