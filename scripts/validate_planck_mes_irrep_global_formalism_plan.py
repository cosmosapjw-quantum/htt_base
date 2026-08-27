#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml


BASE_BRANCH = "changeset/pr324-mes-methodology-stack-20260826"
BASE_SHA = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"
BASE_TREE = "47bdbb72aae62ca4280a96897f80028b1b910c20"
PLANNING_BRANCH = "analysis/planck-mes-extended-data-execution-20260826"
PREDECESSOR_SHA = "2669a55ef230d1ca9e79c09d3344f7b15c50ac0e"
PREDECESSOR_TREE = "274d74507542cc99bb4ea355705791fa03d15697"
PACKAGE_ID = "PLANCK_MES_IRREP_GLOBAL_FORMALISM_EXECUTION_20260827"
PACKAGE_REL = Path("docs/codex_handoff/planck_mes_irrep_global_formalism_execution")
ACTIVE_POINTER_REL = Path("docs/codex_handoff/ACTIVE_PLANCK_MES_EXECUTION_PACKAGE.yaml")
WORKFLOW_REL = Path(".github/workflows/repository-integrity.yml")
EXPECTED_WUS = [f"PMG-WU-{index:03d}" for index in range(1, 10)]
FORBIDDEN_OLD_WUS = [f"PED-WU-{index:03d}" for index in range(1, 5)]

PACKAGE_FILES = {
    "PACKAGE_INDEX.yaml",
    "AUTHORITY_AND_SCOPE.yaml",
    "PRIOR_PLAN_SUPERSESSION.yaml",
    "FORMALISM_CONTRACT.yaml",
    "FORMALISM_MIGRATION_MATRIX.yaml",
    "DATA_ROUTE_MATRIX.yaml",
    "P0_P1_THREAT_CATALOG.json",
    "INVARIANT_TEST_MATRIX.yaml",
    "AUDIT_COMPILED_EXEC_PLAN.yaml",
    "FRESH_CONTEXT_REVIEW_CONTRACT.yaml",
    "FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml",
    "PROCESS_COST_ASSESSMENT.yaml",
    "AUDIT_COMPILED_PLAN.md",
    "CODEX_HANDOFF.md",
    "CODEX_HANDOFF_PROMPT.md",
    "PR417_UPDATE_BODY.md",
}
VALIDATION_FILES = {
    "scripts/validate_planck_mes_irrep_global_formalism_plan.py",
    "tests/contracts/test_planck_mes_irrep_global_formalism_plan.py",
}
PLAN_ONLY_ALLOWED = {
    *(str(PACKAGE_REL / name) for name in PACKAGE_FILES),
    str(ACTIVE_POINTER_REL),
    *VALIDATION_FILES,
    str(WORKFLOW_REL),
}
WORKFLOW_REQUIRED = (
    "Run Planck MES irrep/global-formalism planning contracts",
    "python scripts/validate_planck_mes_irrep_global_formalism_plan.py",
    "python -m pytest -q tests/contracts/test_planck_mes_irrep_global_formalism_plan.py",
)
WORK_UNIT_KEYS = {
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
REQUIRED_MIGRATION_PATHS = {
    "htt/src/common/observable_irrep_state.py",
    "htt/src/common/mes_premise_normalization.py",
    "htt/src/common/response_bound_observable_state.py",
    "htt/src/common/joint_anisotropy_state.py",
    "htt/src/common/orbit_catalogue_v3.py",
    "htt/src/common/mes_directional_state.py",
    "htt/obsstat/mes_directional_moments.py",
    "htt/obsstat/finite_null_reducers.py",
    "htt/obsstat/mes_coordinate_mechanism.py",
    "htt/obsstat/planck_post275_lane.py",
    "scripts/observed_runs/run_planck_mes_morphology.py",
    "scripts/observed_runs/run_planck_mes_coordinate_audit.py",
    "htt/obsstat/planck_pr3_operator.py",
    "htt/obsstat/planck_irrep_carrier.py",
    "scripts/observed_runs/run_planck_pr3.py",
    "htt/obsstat/observable_irrep_orbit.py",
    "scripts/observed_runs/run_planck_mes_irrep_analysis.py",
    "scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py",
    "scripts/observed_runs/run_planck_mes_commander_observation.py",
    "scripts/observed_runs/run_planck_mes_irrep_injections.py",
    "scripts/paper/build_planck_mes_first_paper.py",
    "tests/architecture/test_import_boundaries.py",
}
REQUIRED_ROUTE_STATES = {
    "legacy_scalar_primary_paired300": "FROZEN_LEGACY_BASELINE",
    "map_free_coordinate_mechanism_audit": "EXECUTE_NOW_AFTER_FORMALISM_PREWORK",
    "local_planck_inventory": "VERIFY_READ_ONLY",
    "paired300_irrep_carrier": "EXECUTE_AFTER_INTAKE",
    "paired300_observable_irrep_analysis": "EXECUTE_AFTER_CARRIER_REPLAY_MATCH",
    "smica_cmbonly999_irrep_robustness": "EXECUTE_ONCE_WITH_CARRIER_EXPORT",
    "commander_observation_irrep_comparison": "EXECUTE_DESCRIPTIVE_ONLY_WITH_CARRIER_EXPORT",
    "algebraic_harmonic_injections": "EXECUTE_AFTER_PMG-WU-006",
    "physical_bianchi_template_injections": "CONDITIONAL_EXECUTION",
    "methods_first_paper_revision": "EXECUTE_LAST",
}


class PlanValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise PlanValidationError(message)


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        fail(f"invalid YAML {path}: {exc}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path}: {exc}")


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def is_ancestor(root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def exact_mapping(value: object, expected: set[str], name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(f"{name} must be a mapping")
    if set(value) != expected:
        fail(
            f"{name} keys drifted; missing={sorted(expected-set(value))} "
            f"extra={sorted(set(value)-expected)}"
        )
    return value


def sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        fail(f"{name} must be a sequence")
    return value


def validate_work_unit(
    row: Mapping[str, Any],
    *,
    threat_ids: set[str],
    expected_id: str,
) -> None:
    exact_mapping(row, WORK_UNIT_KEYS, f"work unit {expected_id}")
    if row.get("schema") != "audit-compiled-work-unit/v1":
        fail(f"work-unit schema drifted: {expected_id}")
    if row.get("id") != expected_id:
        fail(f"work-unit id drifted: expected {expected_id}")
    authority = row.get("authority", {})
    if authority.get("canonical_science_base_sha") != BASE_SHA:
        fail(f"canonical science base drifted in {expected_id}")
    if authority.get("planning_predecessor_sha") != PREDECESSOR_SHA:
        fail(f"planning predecessor drifted in {expected_id}")
    if authority.get("planning_branch") != PLANNING_BRANCH:
        fail(f"planning branch drifted in {expected_id}")

    objective = row.get("objective", {})
    for key in ("statement", "observable_success"):
        if not nonempty(objective.get(key)):
            fail(f"{expected_id} lacks objective.{key}")

    risk = row.get("risk", {})
    refs = set(risk.get("P0_failure_modes", [])) | set(risk.get("P1_failure_modes", []))
    if not refs or not refs <= threat_ids:
        fail(f"{expected_id} risk references are empty or unknown: {sorted(refs-threat_ids)}")

    failure_rows = sequence(row.get("failure_modes"), f"{expected_id}.failure_modes")
    failure_refs = {item.get("id") for item in failure_rows if isinstance(item, Mapping)}
    if not refs <= failure_refs:
        fail(f"{expected_id} lacks local failure rows: {sorted(refs-failure_refs)}")

    steps = row.get("implementation", {}).get("ordered_steps")
    if not isinstance(steps, list) or not steps:
        fail(f"{expected_id} has no implementation steps")
    if len({item.get("id") for item in steps if isinstance(item, Mapping)}) != len(steps):
        fail(f"{expected_id} has duplicate/malformed implementation step ids")

    invariants = row.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        fail(f"{expected_id} has no invariants")
    for item in invariants:
        if not isinstance(item, Mapping):
            fail(f"{expected_id} invariant must be a mapping")
        check = item.get("mechanical_check", {})
        if not nonempty(check.get("command")) or not nonempty(check.get("expect")):
            fail(f"{expected_id} invariant lacks mechanical check: {item.get('id')}")

    evidence = row.get("completion_evidence", {}).get("required")
    if not isinstance(evidence, list) or "objective_output_paths" not in evidence:
        fail(f"{expected_id} completion evidence is incomplete")
    if "replay_status" not in evidence:
        fail(f"{expected_id} does not require replay status")

    policy = row.get("agent_policy", {})
    required_policy = {
        "ask_user_questions": False,
        "guessing_across_spec_boundary": "forbidden",
        "changing_tests_to_fit_implementation": "forbidden",
        "claiming_unexecuted_work": "forbidden",
        "creating_successor_planning_package": "forbidden",
        "raw_data_mutation": "forbidden",
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            fail(f"{expected_id} agent policy drifted: {key}")

    review = row.get("review_gate", {})
    if review.get("read_only_first_pass") is not True:
        fail(f"{expected_id} review is not read-only first")
    if review.get("pass_condition") != {"P0": 0, "P1": 0}:
        fail(f"{expected_id} review pass condition drifted")
    if "at most one targeted repair" not in str(review.get("stopping_rule", "")):
        fail(f"{expected_id} review stopping rule drifted")

    transition = row.get("transition", {})
    for key in ("pass_next_executable_action", "fail_next_action"):
        if not nonempty(transition.get(key)):
            fail(f"{expected_id} lacks transition.{key}")


def validate_package(root: Path, *, check_git: bool = True) -> dict[str, object]:
    root = Path(root)
    package = root / PACKAGE_REL
    if not package.is_dir():
        fail(f"package directory missing: {package}")

    index = load_yaml(package / "PACKAGE_INDEX.yaml")
    if index.get("package_id") != PACKAGE_ID:
        fail("package id drifted")
    actual_files = {path.name for path in package.iterdir() if path.is_file()}
    listed_files = set(index.get("files", []))
    if actual_files != PACKAGE_FILES or listed_files != PACKAGE_FILES:
        fail(
            f"package file set drifted; actual={sorted(actual_files)} "
            f"listed={sorted(listed_files)}"
        )
    if set(index.get("validation_files", [])) != VALIDATION_FILES:
        fail("validation file list drifted")
    base = index.get("base_authority", {})
    expected_base = {
        "repository": "cosmosapjw-quantum/htt_base",
        "canonical_science_branch": BASE_BRANCH,
        "canonical_science_sha": BASE_SHA,
        "canonical_science_tree": BASE_TREE,
        "planning_branch": PLANNING_BRANCH,
        "planning_predecessor_sha": PREDECESSOR_SHA,
        "planning_predecessor_tree": PREDECESSOR_TREE,
        "open_draft_pr": 417,
    }
    if base != expected_base:
        fail("package base authority drifted")

    pointer = load_yaml(root / ACTIVE_POINTER_REL)
    if pointer.get("package_id") != PACKAGE_ID:
        fail("active pointer package id drifted")
    if pointer.get("active_package") != str(PACKAGE_REL):
        fail("active pointer path drifted")
    if pointer.get("active_work_units") != EXPECTED_WUS:
        fail("active pointer work-unit order drifted")
    if pointer.get("forbidden_superseded_work_units") != FORBIDDEN_OLD_WUS:
        fail("active pointer predecessor lock drifted")
    if pointer.get("first_objective_execution") != "PMG-WU-003":
        fail("active pointer objective transition drifted")

    authority = load_yaml(package / "AUTHORITY_AND_SCOPE.yaml")
    canonical = authority.get("canonical_science_base", {})
    if canonical != {
        "repository": "cosmosapjw-quantum/htt_base",
        "branch": BASE_BRANCH,
        "sha": BASE_SHA,
        "tree": BASE_TREE,
        "moved_authority_policy": "STOP_BLOCKED_BY_MOVED_AUTHORITY",
    }:
        fail("canonical authority file drifted")
    predecessor = authority.get("planning_predecessor", {})
    if predecessor.get("branch") != PLANNING_BRANCH:
        fail("planning predecessor branch drifted")
    if predecessor.get("sha") != PREDECESSOR_SHA or predecessor.get("tree") != PREDECESSOR_TREE:
        fail("planning predecessor identity drifted")
    if authority.get("execution_permission") != "ALLOWED_AT_EXPLORATORY_OR_DIAGNOSTIC_LEVEL_AFTER_EACH_LOCAL_GATE":
        fail("execution permission drifted")
    if authority.get("claim_admission") != "FAIL_CLOSED_UNTIL_RESPONSE_AND_VALIDATION_GATES_PASS":
        fail("claim admission policy drifted")

    supersession = load_yaml(package / "PRIOR_PLAN_SUPERSESSION.yaml")
    if supersession.get("historical_head") != PREDECESSOR_SHA:
        fail("historical package head drifted")
    lock = supersession.get("execution_lock", {})
    if lock.get("forbidden_active_ids") != FORBIDDEN_OLD_WUS:
        fail("superseded work-unit lock drifted")
    if lock.get("ordered_active_ids") != EXPECTED_WUS:
        fail("active work-unit lock drifted")
    dispositions = supersession.get("prior_work_unit_disposition", [])
    if [item.get("prior_id") for item in dispositions] != FORBIDDEN_OLD_WUS:
        fail("prior work-unit disposition coverage drifted")

    formalism = load_yaml(package / "FORMALISM_CONTRACT.yaml")
    if [row.get("type") for row in formalism.get("typed_layers", [])] != [
        "ObservableIrrepState",
        "JointAnisotropyState",
        "MesPremiseNormalizer",
        "ResponseBoundObservableState",
    ]:
        fail("typed-layer order or coverage drifted")
    identities = formalism.get("mes_coordinate_identities", {})
    required_identities = {
        "W2_max = C_2/(30*pi*T0^2)",
        "Sigma2_max = (27/98)*(7*epsilon_2 + epsilon_3)^2",
    }
    if set(identities.get("exact_identities", [])) != required_identities:
        fail("exact MES coordinate identities drifted")
    if identities.get("independent_information_gain") is not False:
        fail("MES information-gain firewall drifted")
    if identities.get("information_statement") != (
        "sigma(Sigma2_max,W2_max,M) = sigma(C_2,C_3,M) "
        "on the registered nonnegative domain"
    ):
        fail("MES sigma-algebra statement drifted")
    eps_scan = formalism.get("epsilon1_sensitivity", {}).get("required_scan", {})
    if eps_scan != {"minimum": 0.0, "maximum": 1e-05, "points": 101, "spacing": "linear"}:
        fail("epsilon1 sensitivity grid drifted")
    tails = formalism.get("tail_registries", [])
    if [row.get("id") for row in tails] != [
        "LEGACY_ALL_TWO_SIDED_V1",
        "REGISTERED_PHYSICS_ORIENTED_SCALAR_V1",
        "OBSERVABLE_IRREP_ORBIT_V1",
    ]:
        fail("tail registry order or coverage drifted")
    scalar_tails = tails[1].get("coordinates", {})
    expected_scalar_tails = {
        "Sigma2_max": "upper",
        "W2_max": "upper",
        "parity_even_over_odd_l2_l5": "two-sided",
        "power_tensor_gap_l2": "upper",
        "power_tensor_gap_l3": "upper",
        "multipole_l2_absdot": "two-sided",
        "multipole_l3_absdot_0": "two-sided",
        "multipole_l3_absdot_1": "two-sided",
        "multipole_l3_absdot_2": "two-sided",
        "multipole_plane_alignment_max_l2_l3": "upper",
    }
    if scalar_tails != expected_scalar_tails:
        fail("physics-oriented scalar tail registry drifted")

    cells = formalism.get("factorial_coordinate_mechanism", {}).get("cells", [])
    if [row.get("id") for row in cells] != [
        "EPS_LINEAR",
        "SQUARE_ONLY",
        "CARRIER_ONLY",
        "MES_SQUARED",
    ]:
        fail("factorial mechanism cells drifted")
    carrier = formalism.get("carrier_package", {})
    if carrier.get("schema") != "PLANCK_PR3_LOWELL_IRREP_CARRIER_V1":
        fail("carrier schema drifted")
    if carrier.get("arrays", {}).get("observed_real_alm") != [32]:
        fail("observed carrier dimension drifted")
    if carrier.get("arrays", {}).get("null_real_alm_paired300") != [300, 32]:
        fail("paired carrier dimension drifted")

    migration = load_yaml(package / "FORMALISM_MIGRATION_MATRIX.yaml")
    paths = {row.get("path") for row in migration.get("rows", []) if isinstance(row, Mapping)}
    if paths != REQUIRED_MIGRATION_PATHS:
        fail(
            f"migration path coverage drifted; missing={sorted(REQUIRED_MIGRATION_PATHS-paths)} "
            f"extra={sorted(paths-REQUIRED_MIGRATION_PATHS)}"
        )
    if set(migration.get("required_path_set", [])) != REQUIRED_MIGRATION_PATHS:
        fail("migration required_path_set drifted")

    route_payload = load_yaml(package / "DATA_ROUTE_MATRIX.yaml")
    route_rows = route_payload.get("routes", [])
    route_by_id = {
        row.get("id"): row for row in route_rows if isinstance(row, Mapping)
    }
    for route_id, status in REQUIRED_ROUTE_STATES.items():
        if route_by_id.get(route_id, {}).get("status") != status:
            fail(f"route status drifted: {route_id}")
    if route_payload.get("expensive_read_policy") != (
        "NO_NEW_PLANCK_MAP_PASS_MAY_DISCARD_RETAINED_REAL_HARMONIC_COEFFICIENTS"
    ):
        fail("expensive map-read policy drifted")

    threats_payload = load_json(package / "P0_P1_THREAT_CATALOG.json")
    threats = threats_payload.get("failure_modes")
    if not isinstance(threats, list) or not threats:
        fail("threat catalogue missing")
    threat_ids: set[str] = set()
    for row in threats:
        if not isinstance(row, Mapping):
            fail("threat row is not a mapping")
        identifier = row.get("id")
        if not nonempty(identifier) or identifier in threat_ids:
            fail(f"duplicate or malformed threat id: {identifier}")
        threat_ids.add(identifier)
        if row.get("severity") not in {"P0", "P1"}:
            fail(f"invalid threat severity: {identifier}")
        if type(row.get("current_task_blocking")) is not bool:
            fail(f"threat lacks blocking relevance: {identifier}")
        detection = row.get("detection", {})
        if not nonempty(detection.get("executable")):
            fail(f"threat lacks executable detector: {identifier}")
        units = set(row.get("work_units", []))
        if not units or not units <= set(EXPECTED_WUS):
            fail(f"threat has invalid work-unit coverage: {identifier}")
    if len(threat_ids) != 25:
        fail(f"threat count drifted: {len(threat_ids)}")
    summary = threats_payload.get("summary", {})
    if summary.get("P0") != 11 or summary.get("P1") != 14:
        fail("threat severity summary drifted")

    matrix = load_yaml(package / "INVARIANT_TEST_MATRIX.yaml")
    matrix_rows = matrix.get("rows")
    if not isinstance(matrix_rows, list):
        fail("invariant matrix missing")
    mapped = [row.get("failure_mode") for row in matrix_rows if isinstance(row, Mapping)]
    if set(mapped) != threat_ids or len(mapped) != len(threat_ids):
        fail("invariant matrix does not cover each threat exactly once")
    invariant_ids = [row.get("invariant") for row in matrix_rows]
    if len(set(invariant_ids)) != len(invariant_ids):
        fail("invariant ids are not unique")
    for row in matrix_rows:
        if not nonempty(row.get("mechanical_detector")):
            fail(f"invariant lacks detector: {row.get('invariant')}")
        if not nonempty(row.get("pass_transition")):
            fail(f"invariant lacks pass transition: {row.get('invariant')}")

    plan = load_yaml(package / "AUDIT_COMPILED_EXEC_PLAN.yaml")
    if plan.get("ordered_work_units") != EXPECTED_WUS:
        fail("execution work-unit order drifted")
    units = plan.get("work_units")
    if not isinstance(units, list) or len(units) != len(EXPECTED_WUS):
        fail("work-unit records missing")
    for expected_id, row in zip(EXPECTED_WUS, units):
        if not isinstance(row, Mapping):
            fail(f"work unit is not a mapping: {expected_id}")
        validate_work_unit(row, threat_ids=threat_ids, expected_id=expected_id)

    policy = plan.get("global_transition_policy", {})
    if policy.get("execution_permission_separate_from_claim_admission") is not True:
        fail("execution/claim separation drifted")
    if policy.get("first_mandatory_objective_execution") != "PMG-WU-003":
        fail("first objective execution drifted")
    if policy.get("process_starvation_trigger") != "two substantial process-only cycles":
        fail("process starvation trigger drifted")
    if policy.get("successor_planning_package_before_PMG_WU_003") != "forbidden":
        fail("successor package firewall drifted")
    if not policy.get("trusted_verification_boundary"):
        fail("trusted verification boundary missing")
    if policy.get("full_suite_default") is not False:
        fail("full-suite default drifted")

    fresh = load_yaml(package / "FRESH_CONTEXT_REVIEW_CONTRACT.yaml")
    if fresh.get("mode") != "READ_ONLY_FIRST_PASS":
        fail("fresh review mode drifted")
    if fresh.get("pass_condition") != {"P0": 0, "P1": 0}:
        fail("fresh review pass condition drifted")
    if "No further review after PASS" not in str(fresh.get("stopping_rule", "")):
        fail("fresh review stopping rule drifted")

    final = load_yaml(package / "FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml")
    if final.get("pass_condition") != {"P0": 0, "P1": 0}:
        fail("final audit pass condition drifted")
    if not final.get("must_not_reconsider"):
        fail("final audit differential boundary missing")
    if not nonempty(final.get("pass_transition")):
        fail("final audit pass transition missing")

    cost = load_yaml(package / "PROCESS_COST_ASSESSMENT.yaml")
    assurance = cost.get("minimum_required_assurance", {})
    if assurance.get("full_suite_required") is not False:
        fail("process cost full-suite policy drifted")
    if assurance.get("fresh_reviews_per_work_unit") != 1:
        fail("process cost reviewer count drifted")
    if "another successor planning package" not in cost.get("remove_or_do_not_add", []):
        fail("anti-bureaucracy package firewall missing")
    if cost.get("process_starvation_brake", {}).get("trigger") != (
        "two substantial consecutive cycles with only process outputs"
    ):
        fail("process starvation brake drifted")

    for markdown_name in (
        "AUDIT_COMPILED_PLAN.md",
        "CODEX_HANDOFF.md",
        "CODEX_HANDOFF_PROMPT.md",
        "PR417_UPDATE_BODY.md",
    ):
        text = (package / markdown_name).read_text(encoding="utf-8")
        for placeholder in ("TBD", "TODO", "<REPO", "<USER", "<<<", ">>>"):
            if placeholder in text:
                fail(f"placeholder remains in {markdown_name}: {placeholder}")
    handoff = (package / "CODEX_HANDOFF.md").read_text(encoding="utf-8")
    for required in (
        "PMG-WU-001",
        "PMG-WU-003",
        "ObservableIrrepState",
        "independent_information_gain = false",
        "PROCESS_STARVATION",
    ):
        if required not in handoff:
            fail(f"Codex handoff lacks required boundary: {required}")

    workflow = (root / WORKFLOW_REL).read_text(encoding="utf-8")
    for required in WORKFLOW_REQUIRED:
        if required not in workflow:
            fail(f"workflow missing planning contract command: {required}")

    for rel in VALIDATION_FILES:
        if not (root / rel).is_file():
            fail(f"validation file missing: {rel}")

    if check_git:
        if run_git(root, "rev-parse", f"origin/{BASE_BRANCH}") != BASE_SHA:
            fail("remote canonical base moved")
        if run_git(root, "rev-parse", f"{BASE_SHA}^{{tree}}") != BASE_TREE:
            fail("canonical science tree drifted")
        if run_git(root, "rev-parse", f"{PREDECESSOR_SHA}^{{tree}}") != PREDECESSOR_TREE:
            fail("planning predecessor tree drifted")
        if not is_ancestor(root, PREDECESSOR_SHA):
            fail("planning predecessor is not an ancestor of HEAD")
        changed = {
            line
            for line in run_git(root, "diff", "--name-only", PREDECESSOR_SHA, "HEAD").splitlines()
            if line
        }
        if not changed:
            fail("active package produced no repository delta")
        unexpected = sorted(changed - PLAN_ONLY_ALLOWED)
        if unexpected:
            fail(f"planning package changed forbidden paths: {unexpected}")

    return {
        "schema": "htt.planck_mes_irrep_global_formalism.plan_validation.v1",
        "status": "PASS",
        "package_id": PACKAGE_ID,
        "canonical_science_base": BASE_SHA,
        "planning_predecessor": PREDECESSOR_SHA,
        "active_work_units": EXPECTED_WUS,
        "first_objective_execution": "PMG-WU-003",
        "threat_count": len(threat_ids),
        "P0": sum(row["severity"] == "P0" for row in threats),
        "P1": sum(row["severity"] == "P1" for row in threats),
        "migration_paths": len(paths),
        "package_files": len(actual_files),
        "process_starvation_brake": "ENABLED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--no-git", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_package(args.root, check_git=not args.no_git)
    except PlanValidationError as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(yaml.safe_dump(result, sort_keys=False).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
