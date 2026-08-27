#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "docs/codex_handoff/mes_stack_integration"
PR412 = "4733a4c6dbc638372dee7f99ac38f39dba56d933"
PR411 = "5a3825f903546891fd90e3d708481707d59babf4"
MERGE = "1ace5692bb6778ee8d5b99c112fc84dc2ec8cb72"
PLAN_HEAD = "8b6028abcde18c87591789f6ba53e81157fa4eba"
EXPECTED_WUS = [f"MSI-WU-{i:03d}" for i in range(9)]

def fail(message: str) -> None:
    raise SystemExit(message)

def run(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, check=True, text=True,
                          capture_output=True).stdout.strip()

def load_yaml(name: str):
    return yaml.safe_load((PKG / name).read_text(encoding="utf-8"))

def main() -> int:
    required = set(load_yaml("PACKAGE_INDEX.yaml")["files"])
    missing = sorted(name for name in required if not (PKG / name).is_file())
    if missing:
        fail(f"missing package files: {missing}")

    if subprocess.run(["git", "merge-base", "--is-ancestor", PR412, "HEAD"],
                      cwd=ROOT).returncode != 0:
        fail("PR412 is not an ancestor")
    if subprocess.run(["git", "merge-base", "--is-ancestor", PR411, "HEAD"],
                      cwd=ROOT).returncode != 0:
        fail("PR411 is not an ancestor")
    if subprocess.run(["git", "merge-base", "--is-ancestor", PLAN_HEAD, "HEAD"],
                      cwd=ROOT).returncode != 0:
        fail("frozen planning snapshot is not an ancestor")
    parents = run("git", "show", "-s", "--format=%P", MERGE).split()
    if parents != [PR412, PR411]:
        fail(f"integration merge parents drifted: {parents}")

    manifest = load_yaml("SOURCE_IMPORT_MANIFEST.yaml")
    for row in manifest["imports"]:
        actual = run("git", "hash-object", row["path"])
        if actual != row["git_blob_sha"]:
            fail(f"source import drift: {row['path']}")

    plan = load_yaml("AUDIT_COMPILED_EXEC_PLAN.yaml")
    if plan["ordered_work_units"] != EXPECTED_WUS:
        fail("work-unit order drifted")
    if [row["id"] for row in plan["work_units"]] != EXPECTED_WUS:
        fail("work-unit records drifted")

    threats = json.loads((PKG / "P0_P1_THREAT_CATALOG.json").read_text())
    ids = {row["id"] for row in threats["failure_modes"]}
    for row in threats["failure_modes"]:
        if row["severity"] in {"P0", "P1"} and not row.get("detection", {}).get("executable"):
            fail(f"failure lacks detector: {row['id']}")
    matrix = load_yaml("INVARIANT_TEST_MATRIX.yaml")
    mapped = {row["failure_mode"] for row in matrix["rows"]}
    if mapped != ids:
        fail(f"matrix coverage drift: missing={sorted(ids-mapped)} extra={sorted(mapped-ids)}")

    dispositions = load_yaml("PR_DISPOSITION_LEDGER.yaml")["dispositions"]
    required_prs = {385,386,387,388,403,404,405,406,407,408,409,410,411,412,413}
    if {row["github_pr"] for row in dispositions} != required_prs:
        fail("PR disposition coverage drifted")

    # Seal the planning snapshot itself. Later implementation/science descendants
    # may legitimately modify paths that were forbidden only in the planning PR.
    changed = set(run("git", "diff", "--name-only", PR412, PLAN_HEAD).splitlines())
    forbidden_prefixes = (
        "htt/", "machine_readable/", "docs/codex_handoff/pr_backlog",
        "docs/codex_handoff/pr_status", "docs/generated/status_",
        "docs/generated/claim_ledger",
    )
    for path in changed:
        if path.startswith(forbidden_prefixes):
            fail(f"planning integration changed forbidden path: {path}")

    workflow = (ROOT / ".github/workflows/repository-integrity.yml").read_text()
    for required_text in (
        "Run PR-310/321 HSC-KiDS closure contracts",
        "Run MES recovery and stack-integration planning contracts",
        "validate_mes_methodology_recovery_contract.py",
        "validate_mes_stack_integration_plan.py",
    ):
        if required_text not in workflow:
            fail(f"workflow missing: {required_text}")

    payload = {
        "schema": "htt.mes_stack_integration.plan_validation.v1",
        "status": "PASS",
        "merge_parents": parents,
        "planning_snapshot": PLAN_HEAD,
        "work_units": EXPECTED_WUS,
        "source_imports": len(manifest["imports"]),
        "failure_modes": len(ids),
        "canonical_DAG_changed": False,
        "science_code_changed": False,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
