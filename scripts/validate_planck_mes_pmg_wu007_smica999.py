#!/usr/bin/env python3
"""Validate the PMG-WU-007 SMICA CMB-only local execution binding."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG_REL = Path("docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution")
PKG = ROOT / PKG_REL
PACKAGE_ID = "PLANCK_MES_PMG_WU007_SMICA999_LOCAL_EXECUTION_20260829"
BASE_SHA = "242eb4b9904a0c5d8514f3b50c7341d4837d71f5"
BASE_TREE = "86c580bbdd9d465992b2db6532d1086e1ec1ce9a"
BASE_BRANCH = "changeset/planck-mes-wu006-admission-staging-20260829"
PACKAGE_BRANCH = "changeset/planck-mes-wu007-smica999-preflight-20260829"
EXPECTED_PACKAGE_FILES = {
    "PACKAGE_INDEX.yaml", "AUTHORITY_BINDING.yaml", "DATA_AVAILABILITY_BINDING.yaml",
    "WU007_EXECUTION_CONTRACT.yaml", "EVIDENCE_ADAPTIVE_CLAIM_ENVELOPE.yaml",
    "REFEREE_FINDINGS_ROUTE.yaml", "P0_P1_THREAT_CATALOG.json", "INVARIANT_TEST_MATRIX.yaml",
    "CODEX_HANDOFF.md", "CODEX_HANDOFF_PROMPT.md",
}
EXPECTED_VALIDATION_FILES = {
    "scripts/validate_planck_mes_pmg_wu007_smica999.py",
    "tests/contracts/test_planck_mes_pmg_wu007_smica999.py",
    "scripts/observed_runs/preflight_planck_mes_smica999.py",
    "tests/integration/test_planck_mes_smica999_preflight.py",
}
FORBIDDEN_ACTIONS_PATTERNS = (
    "gh run", "actions/runs", "workflow_run", "fetch_commit_workflow_runs", "rerun-failed-jobs",
)


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_yaml(name: str, package: Path = PKG) -> Any:
    try:
        return yaml.safe_load((package / name).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid YAML {name}: {exc}")


def load_json(name: str, package: Path = PKG) -> Any:
    try:
        return json.loads((package / name).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {name}: {exc}")


def mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(f"{label} must be a mapping")
    return value


def sequence(value: object, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        fail(f"{label} must be a sequence")
    return value


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_package(package: Path = PKG, check_git: bool = False) -> dict[str, Any]:
    actual = {p.name for p in package.iterdir() if p.is_file()}
    if actual != EXPECTED_PACKAGE_FILES:
        fail(f"package file set drifted: missing={sorted(EXPECTED_PACKAGE_FILES-actual)} extra={sorted(actual-EXPECTED_PACKAGE_FILES)}")

    index = mapping(load_yaml("PACKAGE_INDEX.yaml", package), "package index")
    if index.get("schema") != "htt.planck_mes.pmg_wu007.package_index.v1":
        fail("package schema drifted")
    if index.get("package_id") != PACKAGE_ID:
        fail("package ID drifted")
    if set(index.get("files", [])) != EXPECTED_PACKAGE_FILES:
        fail("package index file coverage drifted")
    if set(index.get("validation_files", [])) != EXPECTED_VALIDATION_FILES:
        fail("validation-file coverage drifted")
    if index.get("remote_download_required") is not False:
        fail("WU-007 must not require a download")
    if index.get("github_actions_required") is not False:
        fail("GitHub Actions cannot be a WU-007 gate")
    if index.get("science_execution_performed_by_this_package") is not False:
        fail("preflight package falsely claims science execution")

    authority = mapping(load_yaml("AUTHORITY_BINDING.yaml", package), "authority")
    predecessor = mapping(authority.get("accepted_predecessor"), "predecessor")
    if predecessor.get("branch") != BASE_BRANCH or predecessor.get("sha") != BASE_SHA or predecessor.get("tree") != BASE_TREE:
        fail("accepted WU-006 authority drifted")
    if authority.get("implementation_binding_branch") != PACKAGE_BRANCH:
        fail("package branch drifted")
    if authority.get("remote_ci_policy") != "LOCAL_ALTERNATIVE_ONLY_NO_ACTIONS_QUERY_RERUN_OR_STATUS_CHECK":
        fail("local verification policy drifted")

    data = mapping(load_yaml("DATA_AVAILABILITY_BINDING.yaml", package), "data binding")
    if data.get("remote_downloads_remaining") != 0 or data.get("active_downloads") != 0:
        fail("download-complete state drifted")
    planck = mapping(data.get("planck"), "Planck inventory")
    if planck.get("smica_cmb_complete") != 999 or planck.get("smica_noise_complete") != 300:
        fail("Planck inventory counts drifted")
    if planck.get("known_missing") != ["00970"] or planck.get("required_included_special_row") != "00818":
        fail("Planck special-row contract drifted")

    contract = mapping(load_yaml("WU007_EXECUTION_CONTRACT.yaml", package), "work unit")
    if contract.get("schema") != "audit-compiled-work-unit/v1" or contract.get("id") != "PMG-WU-007":
        fail("work-unit identity drifted")
    scope = mapping(contract.get("scope"), "scope")
    forbidden = "\n".join(str(x) for x in scope.get("forbidden_changes", []))
    for required in ("GitHub Actions", "paired-300", "rank"):
        if required not in forbidden:
            fail(f"forbidden-change boundary missing: {required}")
    implementation = mapping(contract.get("implementation"), "implementation")
    outputs = set(implementation.get("required_outputs", []))
    required_outputs = {
        "docs/generated/planck_mes_smica_cmbonly_999_irrep/observable_irreps.npz",
        "docs/generated/planck_mes_smica_cmbonly_999_irrep/result.json",
        "docs/generated/planck_mes_smica_cmbonly_999_irrep/replay.json",
        "docs/generated/planck_mes_smica_cmbonly_999_irrep/terminal.json",
    }
    if not required_outputs.issubset(outputs):
        fail("required scientific-output coverage drifted")
    transition = mapping(contract.get("transition"), "transition")
    if transition.get("pass_next_executable_action") != "START_PMG-WU-008_INJECTION_POWER_STUDY":
        fail("PASS transition drifted")
    policy = mapping(contract.get("agent_policy"), "agent policy")
    for key in ("github_actions_query_rerun_or_gate", "additional_downloads", "creating_successor_planning_package"):
        if policy.get(key) != "forbidden":
            fail(f"agent policy drifted: {key}")

    envelope = mapping(load_yaml("EVIDENCE_ADAPTIVE_CLAIM_ENVELOPE.yaml", package), "claim envelope")
    if envelope.get("rank_based_promotion_forbidden") is not True:
        fail("rank-based claim promotion is not forbidden")
    axes = {row.get("id"): row for row in envelope.get("axes", []) if isinstance(row, Mapping)}
    expected_axes = {
        "representation_validity", "conditional_finite_pool_statistics", "orbit_family_completeness",
        "detection_power", "null_and_systematics_fidelity", "cross_map_release_robustness",
        "physical_source_identifiability",
    }
    if set(axes) != expected_axes:
        fail("claim-envelope axis coverage drifted")
    if axes["orbit_family_completeness"].get("current_level") != "PROVABLY_NONSEPARATING_PARTIAL_FAMILY":
        fail("orbit-completeness claim was silently strengthened")
    if axes["detection_power"].get("current_level") != "UNVALIDATED":
        fail("power claim was silently promoted")
    if axes["physical_source_identifiability"].get("current_level") != "ABSENT":
        fail("physical claim was silently promoted")

    routes = mapping(load_yaml("REFEREE_FINDINGS_ROUTE.yaml", package), "referee routes")
    route_rows = sequence(routes.get("routes"), "referee routes")
    if len(route_rows) != 10:
        fail("referee finding coverage drifted")
    if not any(row.get("finding", "").startswith("R1 ") and row.get("disposition") == "PMG-WU-008" for row in route_rows):
        fail("power-study route drifted")

    threats = mapping(load_json("P0_P1_THREAT_CATALOG.json", package), "threat catalog")
    failure_modes = sequence(threats.get("failure_modes"), "failure modes")
    ids = [row.get("id") for row in failure_modes if isinstance(row, Mapping)]
    if len(ids) != 14 or len(set(ids)) != 14:
        fail("P0/P1 failure-mode coverage drifted")
    for row in failure_modes:
        if row.get("severity") not in {"P0", "P1"}:
            fail(f"invalid threat severity: {row.get('id')}")
        detector = mapping(row.get("detection"), f"detector {row.get('id')}")
        if not detector.get("executable"):
            fail(f"missing detector: {row.get('id')}")

    matrix_doc = mapping(load_yaml("INVARIANT_TEST_MATRIX.yaml", package), "matrix")
    rows = sequence(matrix_doc.get("rows"), "matrix rows")
    mapped_ids = {row.get("failure_mode") for row in rows if isinstance(row, Mapping)}
    if mapped_ids != set(ids):
        fail("threat/matrix coverage drifted")

    for name in ("CODEX_HANDOFF.md", "CODEX_HANDOFF_PROMPT.md"):
        text = (package / name).read_text(encoding="utf-8")
        lowered = text.lower()
        for pattern in FORBIDDEN_ACTIONS_PATTERNS:
            if pattern in lowered:
                fail(f"forbidden GitHub Actions command/reference in {name}: {pattern}")
        if "do not query, rerun, or inspect github actions" not in lowered:
            fail(f"explicit local-only policy missing in {name}")

    if check_git:
        git("cat-file", "-e", f"{BASE_SHA}^{{commit}}")
        if git("rev-parse", f"{BASE_SHA}^{{tree}}") != BASE_TREE:
            fail("base tree mismatch")
        if subprocess.run(["git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"], cwd=ROOT).returncode != 0:
            fail("HEAD is not descended from accepted WU-006")
    return {
        "schema": "htt.planck_mes.pmg_wu007.package_validation.v1",
        "status": "PASS",
        "package_id": PACKAGE_ID,
        "base_sha": BASE_SHA,
        "work_unit": "PMG-WU-007",
        "failure_modes": len(ids),
        "P0": sum(row["severity"] == "P0" for row in failure_modes),
        "P1": sum(row["severity"] == "P1" for row in failure_modes),
        "first_executable_action": "RUN_LOCAL_SMICA999_PREFLIGHT",
        "science_executed": False,
        "github_actions_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-git", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_package(check_git=args.check_git)
    except ValidationError as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"PASS: {PACKAGE_ID} ({result['failure_modes']} failure modes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
