#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[1]
PKG_REL = Path("docs/codex_handoff/planck_mes_extended_data_execution")
PKG = ROOT / PKG_REL
BASE_SHA = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"
BASE_TREE = "47bdbb72aae62ca4280a96897f80028b1b910c20"
BASE_BRANCH = "changeset/pr324-mes-methodology-stack-20260826"
EXPECTED_WUS = [f"PED-WU-{index:03d}" for index in range(1, 5)]
EXPECTED_BUNDLES = {
    "planck_ffp10",
    "desi_dr1_mocks",
    "act_dr6_lensing",
    "hsc_kids",
    "planck_data",
    "desi",
    "act_data",
    "cf4",
    "jwst_sn",
    "jwst_anchors",
    "cf4_full",
    "desi_dr1_fullshape_bgs_bright_v1.2",
    "pr171_primary_sources",
    "planck_npipe_pr4",
}
EXPECTED_ROUTES = {
    "planck_primary_paired_300",
    "planck_smica_cmbonly_999",
    "planck_commander_observation",
    "planck_commander_finite_null",
    "planck_npipe_pr4",
    "submission_provenance_rebind",
    "act_dr6_lensing_control",
    "cf4_directional_lowz_paper_b",
    "desi_mock_calibrated_control",
    "kids_spin2_candidate",
    "jwst_2mrs_local_velocity_candidate",
    "spt_actdr4_bk_crosscmb_controls",
    "pr171_theory_sources",
}
PLAN_ONLY_ALLOWED = {
    str(PKG_REL / name)
    for name in (
        "PACKAGE_INDEX.yaml",
        "AUTHORITY_AND_SCOPE.yaml",
        "DATA_AVAILABILITY_SNAPSHOT.yaml",
        "DATA_ROUTE_MATRIX.yaml",
        "P0_P1_THREAT_CATALOG.json",
        "INVARIANT_TEST_MATRIX.yaml",
        "AUDIT_COMPILED_EXEC_PLAN.yaml",
        "FRESH_CONTEXT_REVIEW_CONTRACT.yaml",
        "FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml",
        "PROCESS_COST_ASSESSMENT.yaml",
        "AUDIT_COMPILED_PLAN.md",
        "CODEX_HANDOFF.md",
    )
} | {
    "scripts/validate_planck_mes_extended_data_plan.py",
    "tests/contracts/test_planck_mes_extended_data_plan.py",
}


class PlanValidationError(RuntimeError):
    """Raised when the audit-compiled package is incomplete or self-contradictory."""


def fail(message: str) -> None:
    raise PlanValidationError(message)


def load_yaml(package: Path, name: str) -> Any:
    path = package / name
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        fail(f"invalid YAML {name}: {exc}")


def load_json(package: Path, name: str) -> Any:
    path = package / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {name}: {exc}")


def run_git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_work_unit(row: Mapping[str, Any]) -> None:
    required = {
        "schema",
        "id",
        "title",
        "authority",
        "objective",
        "risk",
        "scope",
        "preconditions",
        "invariants",
        "failure_modes",
        "implementation",
        "verification",
        "completion_evidence",
        "agent_policy",
        "review_gate",
        "transition",
    }
    if set(row) != required:
        fail(f"work-unit keys drifted for {row.get('id')}")
    if row["schema"] != "audit-compiled-work-unit/v1":
        fail(f"work-unit schema drifted for {row['id']}")
    transition = row["transition"]
    if not isinstance(transition, Mapping):
        fail(f"work-unit transition missing for {row['id']}")
    for key in ("pass_next_executable_action", "fail_next_action"):
        if not _nonempty_string(transition.get(key)):
            fail(f"work-unit lacks {key}: {row['id']}")
    if not row.get("implementation", {}).get("ordered_steps"):
        fail(f"work-unit has no implementation steps: {row['id']}")
    if not row.get("completion_evidence", {}).get("required"):
        fail(f"work-unit has no completion evidence: {row['id']}")
    review = row.get("review_gate", {})
    if review.get("pass_condition") != {"P0": 0, "P1": 0}:
        fail(f"work-unit review gate drifted: {row['id']}")
    if review.get("read_only_first_pass") is not True:
        fail(f"work-unit review is not read-only first: {row['id']}")


def validate_package(
    root: Path = ROOT,
    *,
    package: Path | None = None,
    check_git: bool = True,
) -> dict[str, object]:
    root = Path(root)
    package = Path(package) if package is not None else root / PKG_REL

    index = load_yaml(package, "PACKAGE_INDEX.yaml")
    required_files = index.get("files")
    if not isinstance(required_files, list) or set(required_files) != {
        path.name for path in package.iterdir() if path.is_file()
    }:
        fail("package index and package file set differ")
    missing = sorted(name for name in required_files if not (package / name).is_file())
    if missing:
        fail(f"missing package files: {missing}")

    authority = load_yaml(package, "AUTHORITY_AND_SCOPE.yaml")
    base = authority.get("canonical_base", {})
    if base != {
        "repository": "cosmosapjw-quantum/htt_base",
        "branch": BASE_BRANCH,
        "sha": BASE_SHA,
        "tree": BASE_TREE,
        "moved_authority_policy": "STOP_BLOCKED_BY_MOVED_AUTHORITY",
    }:
        fail("canonical authority drifted")

    snapshot = load_yaml(package, "DATA_AVAILABILITY_SNAPSHOT.yaml")
    total = snapshot.get("raw_total", {})
    if total.get("file_count") != 12239 or total.get("byte_count") != 976_978_065_267:
        fail("raw total drifted")
    bundles = snapshot.get("bundles")
    if not isinstance(bundles, list):
        fail("bundle inventory missing")
    bundle_ids = {row.get("id") for row in bundles if isinstance(row, Mapping)}
    if bundle_ids != EXPECTED_BUNDLES:
        fail(f"bundle coverage drifted: {sorted(bundle_ids)}")
    if sum(row["file_count"] for row in bundles) != 12239:
        fail("bundle file counts do not sum to raw total")

    planck = snapshot.get("planck_detail", {})
    cmb = planck.get("smica_cmb_mc", {})
    noise = planck.get("smica_noise_mc", {})
    commander = planck.get("commander_cmb_mc", {})
    npipe = planck.get("npipe_pr4", {})
    if (
        cmb.get("official_missing_indices") != [970]
        or cmb.get("expected_complete_count") != 999
        or cmb.get("size_anomaly", {}).get("index") != 818
        or noise.get("expected_complete_count") != 300
        or commander.get("complete_indices") != [0, 1, 2]
        or commander.get("partial_indices") != [3, 4, 5, 6]
        or commander.get("finite_null_eligible") is not False
        or npipe.get("file_count") != 0
        or npipe.get("status") != "UNAVAILABLE"
    ):
        fail("Planck inventory contract drifted")
    if snapshot.get("other_data_detail", {}).get("hsc_status") != (
        "NO_ACTUAL_HSC_OR_SACC_NAMED_PAYLOAD_IN_REPORTED_HSC_KIDS_ROOT"
    ):
        fail("HSC/KiDS classification drifted")

    routes = load_yaml(package, "DATA_ROUTE_MATRIX.yaml").get("routes")
    if not isinstance(routes, list):
        fail("route matrix missing")
    route_by_id = {row.get("id"): row for row in routes if isinstance(row, Mapping)}
    if set(route_by_id) != EXPECTED_ROUTES:
        fail("route coverage drifted")
    required_route_states = {
        "planck_smica_cmbonly_999": "EXECUTE_NOW_AFTER_INTAKE",
        "planck_commander_observation": "EXECUTE_DESCRIPTIVE_ONLY",
        "planck_commander_finite_null": "BLOCKED_INSUFFICIENT_COMPLETE_NULLS",
        "planck_npipe_pr4": "BLOCKED_MISSING_DATA",
        "kids_spin2_candidate": "DEFER_RELEASE_AND_CALIBRATION_ADMISSION",
    }
    for route_id, status in required_route_states.items():
        if route_by_id[route_id].get("status") != status:
            fail(f"route status drifted: {route_id}")

    threats = load_json(package, "P0_P1_THREAT_CATALOG.json").get("failure_modes")
    if not isinstance(threats, list) or not threats:
        fail("threat catalogue missing")
    threat_ids: set[str] = set()
    for row in threats:
        if not isinstance(row, Mapping):
            fail("threat row is not a mapping")
        identifier = row.get("id")
        if not _nonempty_string(identifier) or identifier in threat_ids:
            fail(f"duplicate or malformed threat id: {identifier}")
        threat_ids.add(identifier)
        if row.get("severity") not in {"P0", "P1"}:
            fail(f"non-P0/P1 row in threat catalogue: {identifier}")
        detection = row.get("detection", {})
        if not _nonempty_string(detection.get("executable")):
            fail(f"threat lacks executable detector: {identifier}")
        if type(row.get("current_task_blocking")) is not bool:
            fail(f"threat lacks blocking relevance: {identifier}")

    matrix = load_yaml(package, "INVARIANT_TEST_MATRIX.yaml").get("rows")
    if not isinstance(matrix, list):
        fail("invariant matrix missing")
    mapped = {row.get("failure_mode") for row in matrix if isinstance(row, Mapping)}
    if mapped != threat_ids:
        fail(
            "matrix coverage drift: "
            f"missing={sorted(threat_ids-mapped)} extra={sorted(mapped-threat_ids)}"
        )
    for row in matrix:
        if not _nonempty_string(row.get("pass_transition")):
            fail(f"matrix row lacks pass transition: {row.get('failure_mode')}")

    plan = load_yaml(package, "AUDIT_COMPILED_EXEC_PLAN.yaml")
    if plan.get("ordered_work_units") != EXPECTED_WUS:
        fail("work-unit order drifted")
    work_units = plan.get("work_units")
    if not isinstance(work_units, list) or [row.get("id") for row in work_units] != EXPECTED_WUS:
        fail("work-unit records drifted")
    for row in work_units:
        _validate_work_unit(row)

    policy = plan.get("global_transition_policy", {})
    if (
        policy.get("execution_permission_separate_from_claim_admission") is not True
        or policy.get("process_starvation_trigger")
        != "two substantial process-only cycles"
        or not policy.get("trusted_verification_boundary")
    ):
        fail("execution-transition policy drifted")

    fresh = load_yaml(package, "FRESH_CONTEXT_REVIEW_CONTRACT.yaml")
    if (
        fresh.get("mode") != "READ_ONLY_FIRST_PASS"
        or fresh.get("pass_condition") != {"P0": 0, "P1": 0}
        or not _nonempty_string(fresh.get("pass_transition"))
        or "No further review" not in fresh.get("stopping_rule", "")
    ):
        fail("fresh-context review contract drifted")

    final = load_yaml(package, "FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml")
    if (
        final.get("pass_condition") != {"P0": 0, "P1": 0}
        or not final.get("must_not_reconsider")
        or not _nonempty_string(final.get("pass_transition"))
    ):
        fail("final differential audit contract drifted")

    cost = load_yaml(package, "PROCESS_COST_ASSESSMENT.yaml")
    assurance = cost.get("minimum_required_assurance", {})
    if (
        assurance.get("full_suite_required") is not False
        or assurance.get("fresh_reviews_per_work_unit") != 1
        or "preflight hashing of every unrelated 910-GiB raw file"
        not in cost.get("remove_or_do_not_add", [])
    ):
        fail("process-cost contract drifted")

    for markdown_name in ("AUDIT_COMPILED_PLAN.md", "CODEX_HANDOFF.md"):
        text = (package / markdown_name).read_text(encoding="utf-8")
        for forbidden in ("TBD", "TODO", "<REPO_URL_OR_PATH>", "<USER_OBJECTIVE>"):
            if forbidden in text:
                fail(f"placeholder remains in {markdown_name}: {forbidden}")

    if check_git:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_SHA, "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if ancestor.returncode != 0:
            fail("canonical base is not an ancestor of HEAD")
        base_tree = run_git(root, "rev-parse", f"{BASE_SHA}^{{tree}}")
        if base_tree != BASE_TREE:
            fail("canonical base tree drifted")
        changed = set(
            line
            for line in run_git(root, "diff", "--name-only", BASE_SHA, "HEAD").splitlines()
            if line
        )
        if not changed:
            fail("planning package produced no changed files")
        unexpected = sorted(changed - PLAN_ONLY_ALLOWED)
        if unexpected:
            fail(f"planning package changed forbidden paths: {unexpected}")

    return {
        "schema": "htt.planck_mes_extended_data.plan_validation.v1",
        "status": "PASS",
        "work_units": EXPECTED_WUS,
        "failure_modes": len(threat_ids),
        "P0": sum(row["severity"] == "P0" for row in threats),
        "P1": sum(row["severity"] == "P1" for row in threats),
        "bundle_count": len(EXPECTED_BUNDLES),
        "route_count": len(EXPECTED_ROUTES),
        "first_objective_transition": index["first_objective_transition"],
        "first_scientific_transition": index["first_scientific_transition"],
        "canonical_DAG_changed": False,
        "science_code_changed": False,
        "raw_data_committed": False,
    }


def validate_implementation_diff(paths: Sequence[str]) -> dict[str, object]:
    cleaned = [path.strip() for path in paths if path.strip()]
    if not cleaned:
        fail("implementation diff is empty")
    planning_prefix = str(PKG_REL) + "/"
    if any(
        path.startswith(planning_prefix)
        or (
            path.startswith("docs/codex_handoff/")
            and "planck_mes_extended_data" in path
        )
        for path in cleaned
    ):
        fail("implementation diff creates or modifies the planning package")
    objective_prefixes = (
        "scripts/observed_runs/",
        "scripts/paper/",
        "tests/integration/",
        "tests/paper/",
        "tests/contracts/",
        "docs/generated/planck_mes_",
        "papers/planck_mes_first_observation/",
    )
    if not any(path.startswith(objective_prefixes) for path in cleaned):
        fail("implementation diff has no objective or enabling implementation path")
    return {
        "status": "PASS_IMPLEMENTATION_DIFF",
        "path_count": len(cleaned),
        "planning_package_untouched": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="validate package content without repository ancestry/diff checks",
    )
    parser.add_argument(
        "--implementation-diff",
        metavar="PATH_OR_DASH",
        help="validate a newline-delimited changed-path list; use - for stdin",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.implementation_diff:
            if args.implementation_diff == "-":
                paths = sys.stdin.read().splitlines()
            else:
                paths = Path(args.implementation_diff).read_text(
                    encoding="utf-8"
                ).splitlines()
            payload = validate_implementation_diff(paths)
        else:
            payload = validate_package(check_git=not args.skip_git)
    except PlanValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
