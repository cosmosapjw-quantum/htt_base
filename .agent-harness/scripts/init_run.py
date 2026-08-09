#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from _harness import (
    ActiveRunError,
    cli_active_run_id,
    confined_repo_file,
    dump_json,
    is_safe_identifier,
    load_json,
    root,
    utc_now,
    validate_run_plan_payload,
    write_active_run_id,
)
from publication_integrity import (
    PublicationIntegrityError,
    bytes_sha256,
    canonical_target_ref,
    git,
    load_publication_policy,
    mutable_candidate_binding,
    remote_target_sha,
    require_change_set_id,
    require_publication_group_id,
    validate_declared_policy_identity,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--spec-ref", default="SPEC.md")
    parser.add_argument(
        "--target-ref",
        default=None,
        help=(
            "remote-tracking target such as origin/research/pr04-multicomponent; "
            "when omitted, an existing origin/HEAD is resolved and no branch is guessed"
        ),
    )
    parser.add_argument("--candidate-ref", default="HEAD")
    parser.add_argument("--change-set", required=True)
    parser.add_argument("--publication-group", required=True)
    parser.add_argument(
        "--integration-policy",
        required=True,
        help="repository-relative publication/integration policy JSON",
    )
    parser.add_argument(
        "--work-unit",
        required=True,
        help=(
            "Work-unit identifier (normally the PR id, e.g. PR-124). The spawn "
            "budget is cumulative across every run sharing this work unit "
            "(audit H7: run-local budgets reset by creating a new run)."
        ),
    )
    parser.add_argument(
        "--review-rereview-exception-assignment",
        action="append",
        default=[],
        help=(
            "owner-authorized reviewer assignment ID for one dedicated "
            "post-budget rereview run; may be supplied at most twice"
        ),
    )
    parser.add_argument(
        "--review-rereview-exception-id",
        default=None,
        help="safe identifier for the explicit one-time owner authorization",
    )
    parser.add_argument(
        "--review-rereview-authorized-by",
        default=None,
        help="bounded identity of the human authorization source",
    )
    parser.add_argument(
        "--review-rereview-reason",
        default=None,
        help="bounded reason for consuming the narrow reviewer exception",
    )
    parser.add_argument(
        "--review-rereview-reauthorization-start",
        type=int,
        default=None,
        help=(
            "exact cumulative assignment count for the single owner-authorized "
            "second review wave; only the registered value 18 is accepted"
        ),
    )
    args = parser.parse_args()
    if not is_safe_identifier(args.work_unit):
        raise SystemExit("work-unit must be a safe 1-128 character identifier")
    exception_assignment_ids = args.review_rereview_exception_assignment
    exception_fields = (
        args.review_rereview_exception_id,
        args.review_rereview_authorized_by,
        args.review_rereview_reason,
    )
    if exception_assignment_ids:
        if (
            not 1 <= len(exception_assignment_ids) <= 2
            or len(set(exception_assignment_ids))
            != len(exception_assignment_ids)
            or any(
                not is_safe_identifier(item)
                for item in exception_assignment_ids
            )
            or not all(
                isinstance(item, str) and item.strip()
                for item in exception_fields
            )
            or not is_safe_identifier(args.review_rereview_exception_id)
        ):
            raise SystemExit(
                "review rereview exception requires one or two unique safe "
                "assignment IDs, a safe exception ID, authorizer, and reason"
            )
    elif any(item is not None for item in exception_fields):
        raise SystemExit(
            "review rereview exception metadata requires at least one "
            "--review-rereview-exception-assignment"
        )
    elif args.review_rereview_reauthorization_start is not None:
        raise SystemExit(
            "review rereview reauthorization requires at least one "
            "--review-rereview-exception-assignment"
        )
    try:
        change_set_id = require_change_set_id(args.change_set)
        publication_group_id = require_publication_group_id(
            args.publication_group
        )
    except PublicationIntegrityError as exc:
        raise SystemExit(str(exc)) from None

    repo = root()
    harness = repo / ".agent-harness"
    active = cli_active_run_id(repo, required=False)
    if active is not None:
        raise SystemExit(
            f"Active run already exists: {active}. Close it with close_run.py first."
        )
    run_id = args.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    if not is_safe_identifier(run_id):
        raise SystemExit("run-id must be a safe 1-128 character identifier")
    run_dir = harness / "runs" / run_id
    if run_dir.exists():
        raise SystemExit(f"Run already exists: {run_id}")

    index = load_json(harness / "context" / "CONTEXT_INDEX.json")
    version = str(index.get("context_version", "UNBUILT"))
    if version == "UNBUILT":
        raise SystemExit("Build the context pack before initializing a run.")

    try:
        confined_repo_file(repo, args.spec_ref, label="RUN_PLAN spec_ref")
        target_remote, target_branch, target_ref = canonical_target_ref(
            repo, args.target_ref
        )
        base_sha = str(
            git(repo, "rev-parse", "--verify", f"{target_ref}^{{commit}}")
        ).strip()
        if remote_target_sha(repo, target_remote, target_branch) != base_sha:
            raise PublicationIntegrityError(
                "remote target differs from the local tracking ref; fetch "
                "before initializing the run"
            )
        policy_bytes, policy = load_publication_policy(
            repo, args.integration_policy
        )
        validate_declared_policy_identity(
            policy,
            change_set_id=change_set_id,
            publication_group_id=publication_group_id,
            target_ref=f"{target_remote}/{target_branch}",
            target_sha=base_sha,
        )
    except (
        OSError,
        PublicationIntegrityError,
        ValueError,
    ) as exc:
        raise SystemExit(f"run initialization refused: {exc}") from None

    template = load_json(harness / "templates" / "RUN_PLAN.json")
    template.update(
        {
            "schema_version": 2,
            "run_id": run_id,
            "work_unit_id": args.work_unit,
            "change_set_id": change_set_id,
            "publication_group_id": publication_group_id,
            "created_at": utc_now(),
            "spec_ref": args.spec_ref,
            "target_remote": target_remote,
            "target_branch": target_branch,
            "target_ref": target_ref,
            "base_sha": base_sha,
            "candidate_ref": args.candidate_ref,
            "integration_policy": {
                "path": args.integration_policy,
                "sha256": bytes_sha256(policy_bytes),
                "policy_id": policy["policy_id"],
            },
            "candidate_binding": mutable_candidate_binding(),
            "publication_budget": {
                field: policy[field]
                for field in (
                    "max_open_prs",
                    "max_direct_to_target_prs",
                    "max_prs_per_change_set",
                    "max_stack_depth",
                    "max_file_overlap_prs",
                )
            },
            "context_version": version,
        }
    )
    if exception_assignment_ids:
        reauthorization_start = (
            args.review_rereview_reauthorization_start
        )
        template["budget_exception"] = {
            "exception_id": args.review_rereview_exception_id,
            "kind": (
                "single_run_reviewer_rereview_reauthorization"
                if reauthorization_start is not None
                else "single_run_reviewer_rereview"
            ),
            "run_id": run_id,
            "work_unit_id": args.work_unit,
            "authorized_by": args.review_rereview_authorized_by,
            "reason": args.review_rereview_reason,
            "baseline_limit": 16,
            "additional_assignments": len(exception_assignment_ids),
            "allowed_workflow_role": "reviewer",
            "allowed_assignment_ids": exception_assignment_ids,
            "single_use": True,
        }
        if reauthorization_start is not None:
            template["budget_exception"]["cumulative_start"] = (
                reauthorization_start
            )
    plan_errors = validate_run_plan_payload(
        template,
        repo=repo,
        run_id=run_id,
        context_version=version,
    )
    if plan_errors:
        raise SystemExit(
            "run initialization refused (invalid RUN_PLAN):\n- "
            + "\n- ".join(plan_errors)
        )
    for name in ["assignments", "results", "launches", "raw_logs", "artifacts"]:
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    dump_json(run_dir / "RUN_PLAN.json", template)
    try:
        write_active_run_id(repo, run_id)
    except ActiveRunError as exc:
        raise SystemExit(str(exc)) from None
    print(run_id)


if __name__ == "__main__":
    main()
