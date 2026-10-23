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
        return {k: _semantic_meaning(v) for k, v in value.items()
                if not any(word in k.lower() for word in
                           ("identity", "hash", "sha256", "label", "metadata"))}
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
        require(not repair or repair in state["campaign"].get("approved_scientific_repairs", []),
                "append cannot authorize a new ultra repair budget")
        _semantic_delta(t.get("semantic_delta"))
        require(t["semantic_delta"]["kind"] != "prelaunch_transport", "transport is resume evidence, not a new question")
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
    elif any(t["state"] in {"planned", "running"} for t in tasks.values()):
        status = "AWAITING_NATIVE_OUTCOME"
    elif ready:
        status = "CONTINUE"
    else:
        status = "HOLD_UNRESOLVED_BRANCHES"
    originals = state["campaign"].get("original_science_contract", {}).get("nodes", [])
    return {"campaign_id": state["campaign_id"], "status": status, "states": states,
            "ready": ready, "completed": len(done), "total": len(tasks),
            "original_science": {"total": len(originals),
                                 "source_completed_scoped": sum(n.get("state") == "completed_scoped" for n in originals),
                                 "admission": "UNCHANGED_NOT_GRANTED_BY_CONTROLLER"},
            "held": {key: t.get("hold") for key, t in tasks.items() if t["state"] == "held"},
            "note": "Scoped task acceptance never automatically promotes original scientific nodes."}


def next_packet(state: dict, policy: dict, profiles: set[tuple[str, str]]) -> dict:
    """Reserve one fair, dependency-ready opportunity; transport availability is live."""
    # One outstanding packet prevents competing writers and makes interruption replay exact.
    for p in state["packets"].values():
        task = state["tasks"][p["task_id"]]
        if task["state"] == "planned" and task.get("packet_id") == p["packet_id"]:
            return copy.deepcopy(p)
    if any(t["state"] == "running" for t in state["tasks"].values()):
        return summary(state)
    ready = summary(state)["ready"]
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
        packet_id = digest(identity)
        selected = route["transport_selected"]
        # Prompts carry resumable receipt references; durable state retains every raw outcome.
        history_refs = [{"phase": event["phase"], "packet_id": event["packet_id"],
                         "receipt": event["receipt"], "outcome": event["result"].get("outcome"),
                         "candidate_identity": event["result"].get("candidate_identity")}
                        for event in t["history"][-2:]]
        prompt = ("Execute this bounded HTT campaign assignment. Do not spawn children. "
                  "No native low-ell solver or ODE evolution; preserve HTT/MIO and transfer provenance. "
                  "Do not weaken acceptance or promote scoped diagnostics. Research/escalation/review "
                  "are read-only. Review must be independent of all recorded authors. "
                  "Return a result JSON bound to packet_id, task_id, input_identity, plus a local "
                  "raw_receipt path. Never claim dispatch from this packet. Assignment:\n" +
                  json.dumps({**identity, "packet_id": packet_id, "spec": spec,
                              "issue": t.get("issue"), "repair_plan": t.get("repair_plan"),
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
             "spawn_args": {"task_name": "rc_" + packet_id[:16], "fork_turns": "none",
                            "model": selected["model"], "reasoning_effort": selected["effort"],
                            "message": prompt}}
        t.update(state="planned", attempt=attempt, packet_id=packet_id, last_turn=state["turn"])
        state["turn"] += 1
        state["packets"][packet_id] = p
        state["events"].append({"type": "planned", "packet_id": packet_id})
        return copy.deepcopy(p)
    return {**summary(state), "unavailable": unavailable,
            "status": "HOLD_TRANSPORT_UNAVAILABLE" if ready else summary(state)["status"]}


def acknowledge(state: dict, packet_id: str, agent_id: str, observed: str = "UNKNOWN") -> None:
    require(packet_id in state["packets"], "unknown packet")
    p = state["packets"][packet_id]
    t = state["tasks"][p["task_id"]]
    require(t.get("packet_id") == packet_id and t["state"] == "planned", "packet not awaiting launch")
    require(agent_id.strip(), "actual native agent ID required")
    require(agent_id not in t["contributors"] if t["phase"] == "review" else True,
            "reviewer must be independent of all implementation/research/escalation contributors")
    require(not any(q.get("agent_id") == agent_id for q in state["packets"].values()),
            "fresh native launch required; agent ID already used")
    if t["phase"] == "escalation":
        repair_id = t["spec"]["approved_repair_id"]
        require(repair_id not in state["ultra_repairs"], "actual ultra launch allowance already consumed")
        state["ultra_repairs"][repair_id] = {"task_id": p["task_id"], "packet_id": packet_id,
                                             "agent_id": agent_id}
        state["ultra_pending"].pop(repair_id, None)
        t["ultra_used"].append(repair_id)
    p.update(agent_id=agent_id, launch_performed=True, observed_runtime=observed)
    t["state"] = "running"
    t["contributors"].append(agent_id)
    if t["phase"] not in {"research", "escalation", "review"}:
        t["authors"].append(agent_id)
    state["events"].append({"type": "launched", "packet_id": packet_id, "agent_id": agent_id,
                            "requested": p["route"]["requested"], "observed_runtime": observed})


def _receipt(path: str) -> dict:
    p = Path(path)
    require(p.is_file(), "raw receipt file required")
    return {"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def launch_failed(state: dict, packet_id: str, evidence: str, classification: str, reason: str) -> None:
    """Preserve a real pre-launch transport/quota refusal without inventing an agent."""
    require(packet_id in state["packets"], "unknown packet")
    p = state["packets"][packet_id]
    t = state["tasks"][p["task_id"]]
    require(t["state"] == "planned" and t.get("packet_id") == packet_id, "not an unacknowledged launch")
    require(classification in {"environment", "permission", "transport"} and reason.strip(),
            "exact launch refusal classification/reason required")
    receipt = _receipt(evidence)
    hold = {"class": classification, "exact_missing_or_defect": reason, "receipt": receipt}
    t.update(state="held", hold=hold)
    repair_id = t["spec"].get("approved_repair_id")
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
        require(approved_repair_id in state["campaign"].get("approved_scientific_repairs", []),
                "repair was not covered by campaign authorization")
    if delta["kind"] == "prelaunch_transport":
        packet_id = t.get("packet_id")
        p = state["packets"].get(packet_id, {})
        require(delta.get("packet_id") == packet_id and p and not p.get("launch_performed")
                and not p.get("agent_id"), "only current refused unacknowledged packet may restore")
        require(any(e.get("type") == "launch_refused" and e.get("packet_id") == packet_id
                    for e in state["events"]), "confirmed prelaunch refusal required")
        require(input_identity == p["input_identity"] == t["spec"]["input_identity"]
                and approved_repair_id in {None, t["spec"].get("approved_repair_id")},
                "transport restore must preserve scientific input and repair")
        if t["phase"] == "escalation":
            repair_id = t["spec"].get("approved_repair_id")
            require(repair_id not in state["ultra_repairs"] and
                    repair_id not in state["ultra_pending"], "ultra repair already used or reserved")
            state["ultra_pending"][repair_id] = {"task_id": task_id, "trigger_packet": packet_id}
        t["state"] = "ready"
    else:
        require(not any(p.get("launch_performed") and p["packet_id"] == t.get("packet_id")
                        and not any(h["packet_id"] == p["packet_id"] for h in t["history"])
                        for p in state["packets"].values()), "acknowledged unknown outcome cannot replay")
        if approved_repair_id:
            require(approved_repair_id != t["spec"].get("approved_repair_id")
                    and approved_repair_id not in state["ultra_repairs"]
                    and approved_repair_id not in state["ultra_pending"],
                    "different unused approved repair required")
            t["spec"]["approved_repair_id"] = approved_repair_id
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
    require(packet_id in state["packets"], "unknown result packet")
    p = state["packets"][packet_id]
    t = state["tasks"][p["task_id"]]
    require(t["state"] == "running" and t.get("packet_id") == packet_id, "stale or unlaunched result")
    require(result.get("task_id") == p["task_id"] and result.get("input_identity") == p["input_identity"],
            "stale task/input identity")
    require(result.get("agent_id") == p["agent_id"], "result agent identity mismatch")
    receipt = _receipt(result.get("raw_receipt", ""))
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
            repair_id = t["spec"].get("approved_repair_id")
            approved = repair_id and repair_id in state["campaign"].get("approved_scientific_repairs", [])
            failures = [f for f in t["failures"] if f["class"] == issue["class"] and f["substantive"]]
            two = len({f["receipt"]["sha256"] for f in failures}) >= 2
            high = issue.get("high_consequence") is True and bool(issue.get("risk"))
            # Missing input alone, timeout and unknown runtime never trigger ultra.
            eligible = issue["class"] in {"theory", "numeric", "code"} and (two or high)
            require(policy["escalation"]["max_astra_ultra_repairs_per_approved_scientific_repair"] == 1,
                    "unsupported escalation budget policy")
            if approved and eligible and repair_id not in state["ultra_repairs"] and repair_id not in state["ultra_pending"]:
                state["ultra_pending"][repair_id] = {"task_id": p["task_id"], "trigger_packet": packet_id}
                t.update(phase="escalation", state="ready")
            elif (phase == "review" and issue["class"] in {"code", "numeric"}
                  and isinstance(result.get("repair_plan"), str) and result["repair_plan"].strip()
                  and not t.get("targeted_repairs")):
                # One concrete reviewer-directed closeout; the plan is evidence, never admission.
                t["targeted_repairs"] = [{"candidate_identity": t["candidate_identity"],
                                          "issue_identity": digest(issue), "packet_id": packet_id,
                                          "repair_plan": result["repair_plan"]}]
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
    ack = sub.add_parser("ack")
    ack.add_argument("--packet-id", required=True)
    ack.add_argument("--agent-id", required=True)
    ack.add_argument("--observed-runtime", default="UNKNOWN")
    rec = sub.add_parser("record")
    rec.add_argument("--result", type=Path, required=True)
    refused = sub.add_parser("launch-failed")
    refused.add_argument("--packet-id", required=True)
    refused.add_argument("--evidence", required=True)
    refused.add_argument("--class", dest="classification", required=True,
                         choices=["environment", "permission", "transport"])
    refused.add_argument("--reason", required=True)
    reopen = sub.add_parser("resume")
    reopen.add_argument("--task-id", required=True)
    reopen.add_argument("--evidence", required=True)
    reopen.add_argument("--input-identity", required=True)
    reopen.add_argument("--approved-repair-id")
    append = sub.add_parser("append-frontier")
    append.add_argument("--frontier", type=Path, required=True)
    append.add_argument("--authorization", required=True)
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
                output = next_packet(state, policy, profiles)
            elif args.action == "ack":
                acknowledge(state, args.packet_id, args.agent_id, args.observed_runtime)
                output = summary(state)
            elif args.action == "record":
                result = json.loads(args.result.read_text())
                record(state, result, policy)
                # Immutable content-addressed copy; state also includes the full result.
                save(args.state.parent / (args.state.name + ".results") / (digest(result) + ".json"), result)
                output = summary(state)
            elif args.action == "append-frontier":
                append_frontier(state, json.loads(args.frontier.read_text()), args.authorization)
                output = summary(state)
            elif args.action == "resume":
                resume(state, args.task_id, args.evidence, args.input_identity, args.approved_repair_id)
                output = summary(state)
            elif args.action == "launch-failed":
                launch_failed(state, args.packet_id, args.evidence, args.classification, args.reason)
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
