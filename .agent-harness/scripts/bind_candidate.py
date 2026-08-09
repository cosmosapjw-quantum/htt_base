#!/usr/bin/env python3
"""Bind a schema-v2 run to one immutable candidate seal exactly once."""
from __future__ import annotations

import argparse

from _harness import (
    cli_active_run_id,
    declared_result_path,
    dump_json,
    load_json,
    root,
    validate_run_plan_payload,
)
from publication_integrity import (
    PublicationIntegrityError,
    bytes_sha256,
    candidate_binding_from_payload,
    read_repo_json,
    validate_candidate_seal_payload,
)
from strict_result_validation import load_and_validate_registered_result_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seal",
        required=True,
        help="repository-relative immutable CANDIDATE_SEAL.json",
    )
    args = parser.parse_args()

    repo = root()
    run_id = cli_active_run_id(repo)
    assert run_id is not None
    plan_path = repo / ".agent-harness" / "runs" / run_id / "RUN_PLAN.json"
    plan = load_json(plan_path)
    if plan.get("schema_version") != 2:
        raise SystemExit("candidate binding requires a schema-v2 RUN_PLAN")
    binding = plan.get("candidate_binding")
    if not isinstance(binding, dict) or binding.get("state") != "mutable":
        raise SystemExit(
            "candidate is already frozen; repair requires a new candidate and run"
        )
    try:
        index = load_json(
            repo / ".agent-harness/context/CONTEXT_INDEX.json"
        )
        context_version = str(index.get("context_version") or "")
        plan_errors = validate_run_plan_payload(
            plan,
            repo=repo,
            run_id=run_id,
            context_version=context_version,
        )
        if plan_errors:
            raise PublicationIntegrityError(
                "invalid RUN_PLAN: " + "; ".join(plan_errors)
            )
        assignments = sorted((plan_path.parent / "assignments").glob("*.json"))
        result_files = sorted((plan_path.parent / "results").glob("*.json"))
        expected_results = {
            repo / declared_result_path(run_id, assignment.stem)
            for assignment in assignments
        }
        if set(result_files) != expected_results:
            raise PublicationIntegrityError(
                "candidate freeze requires exactly one result for every "
                "registered implementer assignment"
            )
        for result_path in result_files:
            validation = load_and_validate_registered_result_file(
                repo,
                result_path,
                run_id=run_id,
                context_version=context_version,
            )
            if validation.errors:
                raise PublicationIntegrityError(
                    f"{result_path.name} is invalid: "
                    + "; ".join(validation.errors)
                )
            assignment = validation.assignment
            result = validation.result
            if (
                not isinstance(assignment, dict)
                or assignment.get("workflow_role") != "implementer"
                or not isinstance(result, dict)
                or result.get("status") != "pass"
            ):
                raise PublicationIntegrityError(
                    "candidate freeze requires passing implementer results only"
                )
        _, data, seal = read_repo_json(repo, args.seal, field="candidate seal")
        errors = validate_candidate_seal_payload(seal, repo=repo)
        if errors:
            raise PublicationIntegrityError("; ".join(errors))
        expected = {
            "change_set_id": plan.get("change_set_id"),
            "publication_group_id": plan.get("publication_group_id"),
            "target_remote": plan.get("target_remote"),
            "target_branch": plan.get("target_branch"),
            "target_ref": plan.get("target_ref"),
            "base_sha": plan.get("base_sha"),
        }
        for field, value in expected.items():
            if seal.get(field) != value:
                raise PublicationIntegrityError(
                    f"candidate seal does not match RUN_PLAN {field}"
                )
        policy_ref = plan.get("integration_policy")
        if not isinstance(policy_ref, dict) or seal.get("integration_policy") != policy_ref:
            raise PublicationIntegrityError(
                "candidate seal does not match RUN_PLAN integration policy"
            )
        plan["candidate_binding"] = candidate_binding_from_payload(
            seal,
            seal_path=args.seal,
            seal_file_sha256=bytes_sha256(data),
        )
        plan["production_hash"] = seal.get("production_hash")
        plan["evidence_key"] = {
            "production_hash": seal.get("production_hash"),
            "dependency_hashes": dict(plan.get("dependency_hashes") or {}),
        }
        plan["status"] = "candidate_frozen"
    except PublicationIntegrityError as exc:
        raise SystemExit(f"candidate binding refused: {exc}") from None
    dump_json(plan_path, plan)
    print(args.seal)
    print(plan["candidate_binding"]["seal_sha256"])


if __name__ == "__main__":
    main()
