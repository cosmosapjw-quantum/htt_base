#!/usr/bin/env python3
"""Validate the frozen Planck MES observable-irrep execution package.

This validator checks the compiled plan itself and the smallest repository
boundaries needed to keep later implementation work inside the authorized
formalism. It does not execute science and does not validate raw observational
data.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml


ROOT = Path(__file__).resolve().parents[1]
PKG_REL = Path("docs/codex_handoff/planck_mes_observable_irrep_execution")
PKG = ROOT / PKG_REL
BASE_BRANCH = "changeset/pr324-mes-methodology-stack-20260826"
BASE_SHA = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"
BASE_TREE = "47bdbb72aae62ca4280a96897f80028b1b910c20"
PREDECESSOR_BRANCH = "analysis/planck-mes-extended-data-execution-20260826"
PREDECESSOR_SHA = "2669a55ef230d1ca9e79c09d3344f7b15c50ac0e"
PREDECESSOR_TREE = "274d74507542cc99bb4ea355705791fa03d15697"
PLANNING_BRANCH = "analysis/planck-mes-observable-irrep-execution-20260827"
PACKAGE_ID = "PLANCK_MES_OBSERVABLE_IRREP_EXECUTION_20260827"
EXPECTED_WUS = ['PMI-WU-001', 'PMI-WU-002', 'PMI-WU-003', 'PMI-WU-004', 'PMI-WU-005', 'PMI-WU-006', 'PMI-WU-007']
PACKAGE_FILES = {'FRESH_CONTEXT_REVIEW_CONTRACT.yaml', 'INVARIANT_TEST_MATRIX.yaml', 'MIGRATION_MAP.yaml', 'IMPLEMENTATION_PLAN.md', 'CODEX_HANDOFF.md', 'FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml', 'P0_P1_THREAT_CATALOG.json', 'AUTHORITY_AND_SCOPE.yaml', 'PACKAGE_INDEX.yaml', 'FORMALISM_CONTRACT.yaml', 'PROCESS_COST_ASSESSMENT.yaml', 'AUDIT_COMPILED_EXEC_PLAN.yaml'}
PACKAGE_HASHES = {'PACKAGE_INDEX.yaml': '6b6b5b5bd16b7ac00c786513a241679b8de3217155c13471d6468c4361dc15fe', 'AUTHORITY_AND_SCOPE.yaml': '68ae5426da275bafdefc2d7ab90b345ab34bbb0ea045d8e47718843f07d62930', 'FORMALISM_CONTRACT.yaml': '57e297f6d419a49dc67ec4cb4bf1a936a915c9739a3270a18c498e6a40406c53', 'MIGRATION_MAP.yaml': '75a2d52fc795d3ff16747f1f395f57dbd6245a1ef2039888f55171448dc3d7dc', 'P0_P1_THREAT_CATALOG.json': '80475e3f23dc1d0912e207f6e37a1e992829a4b772eb7017c158b3a713f2f6a1', 'INVARIANT_TEST_MATRIX.yaml': '1cd7a5cb8f3d34e42ba52e6105771703a406fe135463130c4b92f1aa6f880d82', 'AUDIT_COMPILED_EXEC_PLAN.yaml': '9db9f3aa7304f4ad506c9898e6bec63f6bfa9eb7e66a98197918b0993c2613de', 'FRESH_CONTEXT_REVIEW_CONTRACT.yaml': 'fb43b0ef3be9c02617e7f6c14f257224a5709c9f17389ee80c60bef6c754fd6e', 'FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml': '3c01a4085f26b8c6277940f9dde182e3eef2470f3c3cb53bcad78f1533363b32', 'PROCESS_COST_ASSESSMENT.yaml': 'f19a32791c448b6aec64ca3f023433834f24635ed321d2959536731aff9a26c5', 'IMPLEMENTATION_PLAN.md': '4e9e16ebae590c6a1874650dbaabe6ef086a6acd41e61b87745c4f0feea16346', 'CODEX_HANDOFF.md': 'a5f485cea399c87383b45a34f38620cdaa8aecfc862b5dc17ccbb46fbfbd02ae'}
VALIDATION_FILES = {
    "scripts/validate_planck_mes_irrep_execution_plan.py",
    "tests/contracts/test_planck_mes_irrep_execution_plan.py",
}
WORK_UNIT_REQUIRED_KEYS = {
    "schema", "id", "title", "authority", "objective", "risk", "scope",
    "preconditions", "invariants", "failure_modes", "implementation",
    "verification", "completion_evidence", "agent_policy", "review_gate",
    "transition",
}
FORBIDDEN_CHANGED_PATTERNS = (
    "htt/src/common/joint_anisotropy_state_v1.py",
    "htt/src/common/orbit_catalogue_v3.py",
    "docs/generated/planck_mes_morphology/planck_mes_morphology.npz",
    "docs/generated/pr315_planck_smica_feature_replay.npz",
    "machine_readable/pr_backlog.json",
    "machine_readable/pr_backlog.yaml",
    "machine_readable/pr_status.yaml",
)
RAW_SUFFIXES = (
    ".fits", ".fits.gz", ".h5", ".hdf5", ".parquet", ".tar", ".tar.gz",
    ".tgz", ".zip", ".7z",
)
PLACEHOLDERS = ("TBD", "TODO", "<REPO_URL_OR_PATH>", "<USER_OBJECTIVE>")


class PlanValidationError(RuntimeError):
    """Raised when the execution package is incomplete or contradictory."""


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_is_ancestor(root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    ).returncode == 0


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def path_matches(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def validate_work_unit(row: Mapping[str, Any]) -> None:
    if set(row) != WORK_UNIT_REQUIRED_KEYS:
        fail(f"work-unit keys drifted for {row.get('id')}")
    if row.get("schema") != "audit-compiled-work-unit/v1":
        fail(f"work-unit schema drifted for {row.get('id')}")
    identifier = row.get("id")
    if not nonempty(identifier):
        fail("work-unit identifier is malformed")
    transition = row.get("transition")
    if not isinstance(transition, Mapping):
        fail(f"work-unit transition missing for {identifier}")
    for key in ("pass_next_executable_action", "fail_next_action"):
        if not nonempty(transition.get(key)):
            fail(f"work-unit lacks {key}: {identifier}")
    if not row.get("implementation", {}).get("ordered_steps"):
        fail(f"work-unit has no ordered implementation: {identifier}")
    if not row.get("completion_evidence", {}).get("required"):
        fail(f"work-unit has no completion evidence: {identifier}")
    review = row.get("review_gate", {})
    if review.get("pass_condition") != {"P0": 0, "P1": 0}:
        fail(f"work-unit review pass condition drifted: {identifier}")
    if review.get("read_only_first_pass") is not True:
        fail(f"work-unit review is not read-only first: {identifier}")
    policy = row.get("agent_policy", {})
    required_forbidden = {
        "guessing_across_spec_boundary": "forbidden",
        "changing_tests_to_fit_implementation": "forbidden",
        "changing_reference_outputs_without_authority": "forbidden",
        "suppressing_failures": "forbidden",
        "claiming_unexecuted_work": "forbidden",
        "creating_successor_planning_package": "forbidden",
        "raw_data_mutation": "forbidden",
        "posthoc_statistic_or_template_selection": "forbidden",
    }
    for key, expected in required_forbidden.items():
        if policy.get(key) != expected:
            fail(f"work-unit policy drifted for {identifier}: {key}")


def allowed_implementation_patterns(plan: Mapping[str, Any]) -> tuple[str, ...]:
    patterns: list[str] = [
        str(PKG_REL / "*"),
        *VALIDATION_FILES,
    ]
    for row in plan["work_units"]:
        patterns.extend(row["scope"]["allowed_paths"])
    return tuple(dict.fromkeys(patterns))


def validate_implementation_diff(root: Path, diff_from: str, plan: Mapping[str, Any]) -> None:
    changed = [
        line for line in run_git(root, "diff", "--name-only", diff_from, "HEAD").splitlines()
        if line
    ]
    allowed = allowed_implementation_patterns(plan)
    unknown = sorted(path for path in changed if not path_matches(path, allowed))
    if unknown:
        fail(f"implementation diff contains unauthorized paths: {unknown}")
    forbidden = sorted(
        path for path in changed if path_matches(path, FORBIDDEN_CHANGED_PATTERNS)
    )
    if forbidden:
        fail(f"implementation diff changes frozen paths: {forbidden}")
    extra_packages = sorted(
        path for path in changed
        if path.startswith("docs/codex_handoff/")
        and not path.startswith(str(PKG_REL) + "/")
    )
    if extra_packages:
        fail(f"successor or unrelated planning package detected: {extra_packages}")
    raw_like = sorted(
        path for path in changed
        if any(path.lower().endswith(suffix) for suffix in RAW_SUFFIXES)
    )
    if raw_like:
        fail(f"raw/archive-like payload staged in implementation diff: {raw_like}")


def validate_package(
    root: Path = ROOT,
    *,
    package: Path | None = None,
    check_git: bool = True,
    implementation_diff_from: str | None = None,
) -> dict[str, object]:
    root = Path(root)
    package = Path(package) if package is not None else root / PKG_REL

    actual_files = {path.name for path in package.iterdir() if path.is_file()}
    if actual_files != PACKAGE_FILES:
        fail(
            "package file set drifted: "
            f"missing={sorted(PACKAGE_FILES-actual_files)} "
            f"extra={sorted(actual_files-PACKAGE_FILES)}"
        )
    for name, expected in PACKAGE_HASHES.items():
        observed = sha256_file(package / name)
        if observed != expected:
            fail(f"frozen package content drifted: {name}")

    index = load_yaml(package / "PACKAGE_INDEX.yaml")
    if index.get("package_id") != PACKAGE_ID:
        fail("package id drifted")
    if set(index.get("files", [])) != PACKAGE_FILES:
        fail("package index coverage drifted")
    if index.get("validation_files") != [
        "scripts/validate_planck_mes_irrep_execution_plan.py",
        "tests/contracts/test_planck_mes_irrep_execution_plan.py",
    ]:
        fail("validation-file registry drifted")
    if index.get("science_code_changed_by_this_package") is not False:
        fail("planning package falsely claims a science-code change")
    if index.get("planning_predecessor", {}).get("disposition") != (
        "SUPERSEDED_BEFORE_SCIENTIFIC_RUNTIME_BY_CARRIER_PRESERVING_PLAN"
    ):
        fail("predecessor disposition drifted")

    authority = load_yaml(package / "AUTHORITY_AND_SCOPE.yaml")
    if authority.get("canonical_base") != {
        "repository": "cosmosapjw-quantum/htt_base",
        "branch": BASE_BRANCH,
        "sha": BASE_SHA,
        "tree": BASE_TREE,
        "moved_authority_policy": "STOP_BLOCKED_BY_MOVED_AUTHORITY",
    }:
        fail("canonical authority drifted")
    predecessor = authority.get("planning_predecessor", {})
    if (
        predecessor.get("branch") != PREDECESSOR_BRANCH
        or predecessor.get("sha") != PREDECESSOR_SHA
        or predecessor.get("tree") != PREDECESSOR_TREE
    ):
        fail("planning predecessor drifted")
    locks = set(authority.get("user_locks", []))
    for required in (
        "Preserve the exact paired 300 FFP10 SMICA CMB+noise Paper-A pool and its 301-row order.",
        "Preserve GENERIC_12=133/301, RAW_REDUCED_10=110/301, EPS_REDUCED_10=109/301, MES_10=98/301, ANCHORS_ONLY_2=78/301, and MORPHOLOGY_ONLY_8=88/301 as immutable legacy scalar baselines.",
        "Do not identify ObservableIrrepState with JointAnisotropyState or any physical shear, vorticity, acceleration, tilt, curvature, or Bianchi family.",
        "A scalar MES anchor may scale a channel-matched existing object but may not manufacture a direction, axis, vector, or STF tensor.",
        "Do not create another planning package during execution.",
    ):
        if required not in locks:
            fail(f"required user lock missing: {required}")

    formalism = load_yaml(package / "FORMALISM_CONTRACT.yaml")
    if formalism.get("package_id") != PACKAGE_ID:
        fail("formalism package binding drifted")
    conventions = formalism.get("conventions", {})
    if conventions.get("metric_signature_for_physical_state") != "(-,+,+,+)":
        fail("metric signature drifted")
    observable = formalism.get("observable_irrep_contract", {})
    if observable.get("blocks") != [
        {"ell": 2, "dimension": 5, "inversion_parity": "even"},
        {"ell": 3, "dimension": 7, "inversion_parity": "odd"},
        {"ell": 4, "dimension": 9, "inversion_parity": "even"},
        {"ell": 5, "dimension": 11, "inversion_parity": "odd"},
    ]:
        fail("observable irrep block dimensions drifted")
    if observable.get("real_component_layout", {}).get(
        "total_dimension_ell2_to_ell5"
    ) != 32:
        fail("observable carrier dimension drifted")
    identities = formalism.get("mes_identities", {})
    if identities.get("eps1_zero_identities") != [
        "W_max^2=C2/(30*pi*T0^2)",
        "Sigma_max^2=(27/98)*(7*epsilon2+epsilon3)^2",
    ]:
        fail("eps1=0 analytic identities drifted")
    finite = formalism.get("finite_null_contract", {})
    if finite.get("legacy_exact_family_ranks") != {
        "GENERIC_12": "133/301",
        "RAW_REDUCED_10": "110/301",
        "EPS_REDUCED_10": "109/301",
        "MES_10": "98/301",
        "ANCHORS_ONLY_2": "78/301",
        "MORPHOLOGY_ONLY_8": "88/301",
    }:
        fail("historical scalar rank locks drifted")
    if finite.get("invariant_reducer", {}).get("u") != (
        "(count(X_kj<X_ij)+0.5*count(X_kj=X_ij))/(N-1), k!=i"
    ):
        fail("LOO ECDF midrank formula drifted")
    injection = formalism.get("template_and_injection_contract", {})
    if injection.get("mandatory_template") != (
        "ANALYTIC_AXISYMMETRIC_STF_L2_L3_V1"
    ):
        fail("mandatory analytic template drifted")
    if injection.get("orientation_score_grid", {}).get("rotation_count") != 384:
        fail("score rotation grid drifted")
    if injection.get("power_evaluation_orientation_grid", {}).get(
        "rotation_count"
    ) != 96:
        fail("power rotation grid drifted")
    if injection.get("amplitude_grid") != [
        0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0
    ]:
        fail("injection amplitude grid drifted")
    if injection.get("conditional_disposition_if_missing") != (
        "DEFERRED_MISSING_TEMPLATE_AUTHORITY, without blocking the analytic injection lane"
    ):
        fail("native-template conditional disposition drifted")

    migration = load_yaml(package / "MIGRATION_MAP.yaml")
    surfaces = migration.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        fail("migration surface map missing")
    surface_paths = [row.get("path") for row in surfaces if isinstance(row, Mapping)]
    if len(surface_paths) != len(set(surface_paths)):
        fail("migration surface paths are duplicated")
    if "htt/src/common/observable_irrep_state.py" not in surface_paths:
        fail("observable-irrep SSOT migration is missing")
    if "htt/obsstat/finite_null_family.py" not in surface_paths:
        fail("finite-null centralization migration is missing")

    threat_payload = load_json(package / "P0_P1_THREAT_CATALOG.json")
    threats = threat_payload.get("failure_modes")
    if not isinstance(threats, list) or len(threats) != 24:
        fail("threat catalogue cardinality drifted")
    threat_ids: set[str] = set()
    for row in threats:
        if not isinstance(row, Mapping):
            fail("threat row is not a mapping")
        identifier = row.get("id")
        if not nonempty(identifier) or identifier in threat_ids:
            fail(f"duplicate or malformed threat id: {identifier}")
        threat_ids.add(identifier)
        if row.get("severity") not in {"P0", "P1"}:
            fail(f"non-P0/P1 row in threat catalogue: {identifier}")
        if type(row.get("current_task_blocking")) is not bool:
            fail(f"threat lacks current-task blocking relevance: {identifier}")
        if not nonempty(row.get("detection", {}).get("executable")):
            fail(f"threat lacks executable detector: {identifier}")
        if not nonempty(row.get("prevention", {}).get("mechanism")):
            fail(f"threat lacks prevention mechanism: {identifier}")

    matrix_payload = load_yaml(package / "INVARIANT_TEST_MATRIX.yaml")
    rows = matrix_payload.get("rows")
    if not isinstance(rows, list):
        fail("invariant matrix missing")
    mapped = {row.get("failure_mode") for row in rows if isinstance(row, Mapping)}
    if mapped != threat_ids:
        fail(
            "invariant matrix coverage drifted: "
            f"missing={sorted(threat_ids-mapped)} extra={sorted(mapped-threat_ids)}"
        )
    for row in rows:
        if not nonempty(row.get("mechanical_detector")):
            fail(f"matrix detector missing: {row.get('failure_mode')}")
        if not nonempty(row.get("pass_transition")):
            fail(f"matrix pass transition missing: {row.get('failure_mode')}")

    plan = load_yaml(package / "AUDIT_COMPILED_EXEC_PLAN.yaml")
    if plan.get("ordered_work_units") != EXPECTED_WUS:
        fail("work-unit order drifted")
    work_units = plan.get("work_units")
    if not isinstance(work_units, list) or [
        row.get("id") for row in work_units
    ] != EXPECTED_WUS:
        fail("work-unit records drifted")
    for row in work_units:
        validate_work_unit(row)
    policy = plan.get("global_transition_policy", {})
    if (
        policy.get("execution_permission_separate_from_claim_admission") is not True
        or policy.get("first_objective_output_required_by") != "PMI-WU-002"
        or policy.get("large_data_execution_must_preserve_harmonic_carrier") is not True
        or policy.get("process_starvation_trigger")
        != "two substantial process-only cycles"
        or policy.get("full_repository_suite_default") is not False
    ):
        fail("global execution-transition policy drifted")

    fresh = load_yaml(package / "FRESH_CONTEXT_REVIEW_CONTRACT.yaml")
    if (
        fresh.get("mode") != "READ_ONLY_FIRST_PASS"
        or fresh.get("pass_condition") != {"P0": 0, "P1": 0}
        or not nonempty(fresh.get("pass_transition"))
        or "No further review" not in fresh.get("stopping_rule", "")
    ):
        fail("fresh-context review contract drifted")

    final = load_yaml(package / "FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml")
    if (
        final.get("pass_condition") != {"P0": 0, "P1": 0}
        or not final.get("must_not_reconsider")
        or not nonempty(final.get("pass_transition"))
    ):
        fail("final differential audit contract drifted")

    cost = load_yaml(package / "PROCESS_COST_ASSESSMENT.yaml")
    assurance = cost.get("minimum_required_assurance", {})
    if (
        assurance.get("full_suite_required") is not False
        or assurance.get("fresh_reviews_per_work_unit") != 1
        or assurance.get("targeted_repair_limit") != 1
        or assurance.get("full_raw_tree_hash_before_execution") is not False
    ):
        fail("process-cost contract drifted")
    for prohibited in (
        "a second successor planning package",
        "review-of-review or meta-review loops",
        "preflight hashing of every unrelated 910-GiB raw file",
        "the full repository suite by default",
    ):
        if prohibited not in cost.get("remove_or_do_not_add", []):
            fail(f"anti-bureaucracy control missing: {prohibited}")

    for name in ("IMPLEMENTATION_PLAN.md", "CODEX_HANDOFF.md"):
        text = (package / name).read_text(encoding="utf-8")
        for token in PLACEHOLDERS:
            if token in text:
                fail(f"placeholder remains in {name}: {token}")
    handoff = (package / "CODEX_HANDOFF.md").read_text(encoding="utf-8")
    for required in (
        "PMI-WU-001 — start here",
        "PMI-WU-002 — mandatory first objective result",
        "ANALYTIC_AXISYMMETRIC_STF_L2_L3_V1",
        "DEFERRED_MISSING_TEMPLATE_AUTHORITY",
        "Do **not** create another plan",
    ):
        if required not in handoff:
            fail(f"Codex handoff requirement missing: {required}")

    if check_git:
        if not git_is_ancestor(root, BASE_SHA):
            fail("canonical base is not an ancestor of HEAD")
        if not git_is_ancestor(root, PREDECESSOR_SHA):
            fail("planning predecessor is not an ancestor of HEAD")
        if run_git(root, "rev-parse", f"{BASE_SHA}^{{tree}}") != BASE_TREE:
            fail("canonical base tree drifted")
        if run_git(root, "rev-parse", f"{PREDECESSOR_SHA}^{{tree}}") != PREDECESSOR_TREE:
            fail("planning predecessor tree drifted")
        validate_implementation_diff(
            root,
            implementation_diff_from or PREDECESSOR_SHA,
            plan,
        )

    return {
        "schema": "htt.planck_mes_observable_irrep.plan_validation.v1",
        "status": "PASS",
        "package_id": PACKAGE_ID,
        "base_sha": BASE_SHA,
        "predecessor_sha": PREDECESSOR_SHA,
        "planning_branch": PLANNING_BRANCH,
        "work_units": EXPECTED_WUS,
        "failure_modes": len(threat_ids),
        "P0": sum(row["severity"] == "P0" for row in threats),
        "P1": sum(row["severity"] == "P1" for row in threats),
        "first_objective_work_unit": "PMI-WU-002",
        "large_data_carrier_gate": "REQUIRED",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="validate package content without repository ancestry/diff checks",
    )
    parser.add_argument(
        "--implementation-diff-from",
        metavar="SHA",
        help="validate HEAD changes from the supplied accepted predecessor",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_package(
            check_git=not args.no_git,
            implementation_diff_from=args.implementation_diff_from,
        )
    except PlanValidationError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "PASS "
            f"package={result['package_id']} "
            f"work_units={len(result['work_units'])} "
            f"P0={result['P0']} P1={result['P1']} "
            f"first_objective={result['first_objective_work_unit']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
