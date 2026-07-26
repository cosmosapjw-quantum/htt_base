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
    args = parser.parse_args()
    if not is_safe_identifier(args.work_unit):
        raise SystemExit("work-unit must be a safe 1-128 character identifier")
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
