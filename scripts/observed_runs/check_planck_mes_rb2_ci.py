#!/usr/bin/env python3
"""Read-only exact-head CI check. Never reruns jobs or changes billing/settings.

The pure classifier is testable with synthetic records. Operational admission
always obtains fresh records using the authenticated GitHub CLI; there is no
snapshot or override option that can turn a saved PASS into live authorization.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from typing import Mapping, Sequence

REPOSITORY = "cosmosapjw-quantum/htt_base"
RB2_HEAD = "0ae0e70791273c13c7b80ac835232c3c63555c5b"
WORKFLOWS = {
    317997656: ("Repository integrity", ("Python package smoke", "Repository contracts", "Rust compile")),
    318213662: ("PR04 theory and integration gates", ("Python 3.10", "Python 3.11", "Python 3.12", "Python 3.13")),
    318213674: ("PR07 audit-repair gates", ("Portable numerical + claim gates",)),
}
_OID = re.compile(r"^[0-9a-f]{40}$")


class CIError(RuntimeError):
    """Live evidence could not be obtained or did not authorize transition."""


def classify_ci(head: str, runs: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Classify complete, latest-attempt records without trusting badge color."""
    report: dict[str, object] = {
        "schema": "htt.planck_mes.exact_head_ci.v1", "head": head,
        "state": "INVALID_CI_EVIDENCE", "transition_open": False,
        "job_count": 0, "executed_jobs": 0, "runs": [],
    }
    if not isinstance(head, str) or _OID.fullmatch(head) is None:
        return {**report, "reason": "exact 40-hex head is required"}
    if not isinstance(runs, (list, tuple)) or len(runs) != len(WORKFLOWS):
        return {**report, "reason": "required workflow inventory is incomplete"}
    if any(not isinstance(run, Mapping) for run in runs):
        return {**report, "reason": "malformed workflow record"}
    if Counter(run.get("workflow_id") for run in runs) != Counter(WORKFLOWS.keys()):
        return {**report, "reason": "workflow identity set differs"}
    pending = failed = incomplete = unstarted = billing = False
    job_ids: set[int] = set()
    for run in runs:
        name, required_names = WORKFLOWS[run["workflow_id"]]
        rid, attempt = run.get("id"), run.get("run_attempt")
        if (type(rid) is not int or rid <= 0 or type(attempt) is not int or attempt < 1
                or run.get("head_sha") != head or run.get("name") != name
                or run.get("event") not in {"push", "pull_request", "workflow_dispatch"}):
            return {**report, "reason": "workflow head, identity, or attempt differs"}
        jobs = run.get("jobs")
        if not isinstance(jobs, list) or any(not isinstance(job, Mapping) for job in jobs):
            return {**report, "reason": "malformed job inventory"}
        if Counter(job.get("name") for job in jobs) != Counter(required_names):
            return {**report, "reason": "required job inventory differs"}
        annotations = run.get("annotations", {})
        report["runs"].append({"id": rid, "workflow_id": run["workflow_id"], "attempt": attempt})
        if run.get("status") != "completed":
            pending = True
        elif run.get("conclusion") != "success":
            incomplete = True
        for job in jobs:
            jid = job.get("id")
            if (type(jid) is not int or jid <= 0 or jid in job_ids
                    or job.get("head_sha") != head or job.get("run_id") != rid
                    or job.get("run_attempt") != attempt or job.get("workflow_name") != name):
                return {**report, "reason": "job head, identity, or latest attempt differs"}
            job_ids.add(jid)
            report["job_count"] += 1
            steps, runner = job.get("steps"), job.get("runner_id")
            if (not isinstance(steps, list) or any(not isinstance(step, Mapping) for step in steps)
                    or type(runner) is not int or runner < 0):
                return {**report, "reason": "job execution evidence is malformed"}
            executed = runner > 0 and bool(steps)
            report["executed_jobs"] += int(executed)
            if job.get("status") != "completed":
                pending = True
                continue
            conclusion = job.get("conclusion")
            if not executed:
                if runner == 0 and not steps and conclusion == "failure":
                    unstarted = True
                    messages = annotations.get(str(jid), []) if isinstance(annotations, Mapping) else []
                    for item in messages if isinstance(messages, list) else []:
                        text = str(item.get("message", "")).lower() if isinstance(item, Mapping) else ""
                        billing |= "job was not started" in text and (
                            "payments have failed" in text or "spending limit" in text or "billing" in text
                        )
                else:
                    incomplete = True
                continue
            if conclusion == "failure" or any(s.get("conclusion") == "failure" for s in steps):
                failed = True
            elif conclusion != "success":
                incomplete = True
            if (not any(s.get("status") == "completed" and s.get("conclusion") == "success" for s in steps)
                    or any(s.get("status") != "completed" or s.get("conclusion") not in {"success", "skipped"} for s in steps)):
                incomplete = True
    if failed:
        state = "FAILED_EXECUTED_WORKFLOW"
    elif pending:
        state = "CI_PENDING"
    elif unstarted:
        state = "NOT_STARTED_EXTERNAL_GITHUB_BILLING" if billing else "NOT_STARTED_EXTERNAL_GITHUB_ACTIONS"
    elif incomplete or report["executed_jobs"] != 8:
        state = "INCOMPLETE_CI"
    else:
        state = "PASS"
    report.update(state=state, transition_open=state == "PASS")
    return report


def _gh_get(endpoint: str, *, paginate: bool = False) -> object:
    command = ["gh", "api", "--method", "GET", endpoint]
    if paginate:
        command += ["--paginate", "--slurp"]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CIError("authenticated gh read is unavailable") from exc
    if result.returncode:
        # Do not echo credentials or arbitrary provider error bodies into evidence.
        raise CIError(f"GitHub GET failed for {endpoint.split('?')[0]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CIError("GitHub returned non-JSON CI evidence") from exc


def _items(pages: object, key: str) -> list[dict[str, object]]:
    if not isinstance(pages, list):
        raise CIError("paginated GitHub response is malformed")
    result: list[dict[str, object]] = []
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get(key), list):
            raise CIError("GitHub collection is malformed")
        result.extend(page[key])
    if any(not isinstance(item, dict) for item in result):
        raise CIError("GitHub collection item is malformed")
    return result


def check_live_ci(head: str = RB2_HEAD) -> dict[str, object]:
    """Read latest workflow/run attempts from GitHub, including all list pages."""
    if not isinstance(head, str) or _OID.fullmatch(head) is None:
        raise CIError("live CI requires an exact 40-hex head")
    prefix = f"repos/{REPOSITORY}"
    records = _items(_gh_get(f"{prefix}/actions/runs?head_sha={head}&per_page=100", paginate=True), "workflow_runs")
    selected: list[dict[str, object]] = []
    for wid in WORKFLOWS:
        candidates = [r for r in records if r.get("workflow_id") == wid and r.get("head_sha") == head]
        if not candidates:
            return {"schema": "htt.planck_mes.exact_head_ci.v1", "head": head,
                    "state": "CI_PENDING", "transition_open": False, "reason": f"workflow {wid} absent"}
        latest = max(candidates, key=lambda r: (int(r.get("run_number", 0)), int(r["id"])))
        run = _gh_get(f"{prefix}/actions/runs/{latest['id']}")
        if not isinstance(run, dict):
            raise CIError("workflow detail is malformed")
        attempt = run.get("run_attempt")
        if type(attempt) is not int or attempt < 1:
            raise CIError("workflow attempt is missing")
        jobs = _items(_gh_get(f"{prefix}/actions/runs/{run['id']}/attempts/{attempt}/jobs?per_page=100", paginate=True), "jobs")
        run["jobs"], run["annotations"] = jobs, {}
        for job in jobs:
            if job.get("runner_id") == 0 and job.get("steps") == [] and job.get("conclusion") == "failure":
                try:
                    pages = _gh_get(f"{prefix}/check-runs/{job['id']}/annotations?per_page=100", paginate=True)
                    if isinstance(pages, list) and all(isinstance(p, list) for p in pages):
                        run["annotations"][str(job["id"])] = [item for page in pages for item in page]
                except CIError:
                    pass  # Unknown external nonexecution, never an inferred billing claim.
        fresh = _gh_get(f"{prefix}/actions/runs/{run['id']}")
        if not isinstance(fresh, dict) or any(fresh.get(k) != run.get(k) for k in ("head_sha", "run_attempt", "status", "conclusion")):
            raise CIError("CI attempt changed while being read; collect again")
        selected.append(run)
    # Detect a newer run created during collection instead of admitting a stale PASS.
    final_records = _items(_gh_get(f"{prefix}/actions/runs?head_sha={head}&per_page=100", paginate=True), "workflow_runs")
    for run in selected:
        current = [r for r in final_records if r.get("workflow_id") == run["workflow_id"] and r.get("head_sha") == head]
        if not current:
            raise CIError("workflow disappeared during collection")
        latest = max(current, key=lambda r: (int(r.get("run_number", 0)), int(r["id"])))
        if latest.get("id") != run["id"] or latest.get("run_attempt") != run["run_attempt"]:
            raise CIError("a newer CI run/attempt exists; collect again")
    return {**classify_ci(head, selected), "evidence_origin": "LIVE_GITHUB_GET_ONLY"}


def require_live_ci(head: str = RB2_HEAD) -> dict[str, object]:
    report = check_live_ci(head)
    if report.get("transition_open") is not True:
        raise CIError(f"exact-head transition remains closed: {report.get('state')}")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head", default=RB2_HEAD)
    args = parser.parse_args(argv)
    try:
        report = check_live_ci(args.head)
    except (CIError, KeyError, TypeError, ValueError) as exc:
        report = {"head": args.head, "state": "CI_EVIDENCE_UNAVAILABLE", "transition_open": False, "error": str(exc)}
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0 if report.get("transition_open") is True else 3


if __name__ == "__main__":
    sys.exit(main())
