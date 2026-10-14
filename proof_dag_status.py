#!/usr/bin/env python3
"""Read-only status scanner for the htt_base sequential proof DAG.

Reads PROOF_DAG.json plus every ADJUDICATION.json / RETURN.json under
local_cas, classifies each node from the most recent recorded evidence, applies
the DAG dependencies and serial_policy.priority_order, and prints the next
eligible node. Never executes a proof engine and never edits any file.

Usage:  python3 -I proof_dag_status.py [REPO_ROOT] [--json]

State meanings (finite CAS evidence only; scientific admission is always HOLD):
  PASS_FINITE      latest observed aggregate is CAS_4AXIS_PASS
  BLOCKED          latest aggregate is CAS_BLOCKED, or status text says blocked/hold
  NEEDS_SUCCESSOR  latest aggregate is CAS_CONFLICT / CAS_FAIL / incomplete
                   (needs a corrected successor contract, not a replay)
  NOT_RUN          no adjudication found for this node
  HOLD_NO_CONTRACT DAG says no executable contract exists
"""
import glob
import json
import os
import re
import subprocess
import sys

PKG = "docs/research_program/gr_statistics_loops_20260930"
DAG = PKG + "/local_sequential_verification_20261001/PROOF_DAG.json"


def git_ts(root, path):
    try:
        out = subprocess.run(
            ["git", "-C", root, "log", "-1", "--format=%ct", "--", path],
            capture_output=True, text=True, timeout=60).stdout.strip()
        return int(out) if out else 0
    except Exception:
        return 0


def node_of(path):
    """Map an evidence path to a GR-CAS node number (or None)."""
    for pat in (r"/CAS-(\d{2})/", r"GRSTAT-CAS(\d{2})-C\d{2}", r"/CAS(\d{2})-C\d{2}/"):
        m = re.search(pat, path)
        if m:
            return int(m.group(1))
    return None


def aggregate_of(j):
    agg = j.get("aggregate_status") or j.get("aggregate")
    if not agg and isinstance(j.get("result"), dict):
        agg = j["result"].get("aggregate_status")
    if not agg and isinstance(j.get("observed_aggregate"), dict):
        agg = j["observed_aggregate"].get("status")
    if isinstance(agg, dict):
        agg = agg.get("status")
    return agg if isinstance(agg, str) else None


def classify(agg, status_text):
    s = (agg or "").upper()
    t = (status_text or "").upper()
    if s == "CAS_4AXIS_PASS":
        return "PASS_FINITE"
    if s == "CAS_BLOCKED" or "BLOCKED" in t or "HOLD" in t:
        return "BLOCKED"
    if s in ("CAS_CONFLICT", "CAS_FAIL", "CAS_INCOMPLETE") or "INCOMPLETE" in t:
        return "NEEDS_SUCCESSOR"
    return "NOT_RUN"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = os.path.abspath(args[0]) if args else os.getcwd()
    want_json = "--json" in sys.argv
    dag = json.load(open(os.path.join(root, DAG)))
    prio = dag["serial_policy"]["priority_order"]

    ev = {}
    for pat in ("ADJUDICATION.json", "RETURN.json"):
        for p in glob.glob(os.path.join(root, PKG, "**", pat), recursive=True):
            rel = os.path.relpath(p, root)
            n = node_of("/" + rel)
            if n is None:
                continue
            try:
                j = json.load(open(p))
            except Exception:
                continue
            st = j.get("status") if isinstance(j.get("status"), str) else ""
            ev.setdefault(n, []).append({
                "path": rel, "ts": git_ts(root, rel), "agg": aggregate_of(j),
                "status": st, "vstate": j.get("verification_state")})

    state = {}
    for g in dag["gr_nodes"]:
        nid = g["id"]
        n = int(nid.split("-")[-1])
        items = sorted(ev.get(n, []), key=lambda e: (e["ts"], e["path"]))
        if "HOLD_INPUT_NO_EXECUTABLE_CONTRACT" in str(g.get("status")):
            st, last = "HOLD_NO_CONTRACT", None
        elif not items:
            st, last = "NOT_RUN", None
        else:
            last = items[-1]
            st = classify(last["agg"], last["status"])
        state[nid] = {"state": st, "last": last, "deps": g.get("depends_on", []),
                      "title": g["title"], "n_evidence": len(items)}
    for key in ("port_nodes", "loop2_bridges"):
        for g in dag[key]:
            state[g["id"]] = {"state": "NOT_RUN", "last": None,
                              "deps": g.get("depends_on", []),
                              "title": g.get("title", g["id"]), "n_evidence": 0}

    done = {k for k, v in state.items() if v["state"] == "PASS_FINITE"}
    nxt = None
    rows = []
    for nid in prio:
        v = state.get(nid)
        if not v:
            continue
        v["unmet_deps"] = [d for d in v["deps"] if d not in done]
        v["eligible"] = v["state"] in ("NOT_RUN", "NEEDS_SUCCESSOR") and not v["unmet_deps"]
        if v["eligible"] and nxt is None:
            nxt = nid
        rows.append(nid)

    if want_json:
        print(json.dumps({"next": nxt, "nodes": state}, ensure_ascii=False,
                         indent=1, default=str))
        return
    print("%-12s %-16s %-14s %s" % ("node", "state", "deps-unmet", "title"))
    for nid in rows:
        v = state[nid]
        print("%-12s %-16s %-14s %s" % (
            nid, v["state"], ",".join(v["unmet_deps"]) or "-", v["title"][:58]))
    print("\nnext eligible by priority_order:", nxt)
    print("note: PASS_FINITE = finite CAS component only; analytic obligations,"
          " independent review and scientific admission are tracked separately.")


if __name__ == "__main__":
    main()
