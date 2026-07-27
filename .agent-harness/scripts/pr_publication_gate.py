#!/usr/bin/env python3
"""Validate all frozen evidence for a credential-isolated publisher.

This command never runs ``git push`` or creates a PR.  ``consume`` is intended
to be called by a serialized external publisher immediately before it executes
fixed, seal-derived publication argv with credentials unavailable to agents.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from _harness import assignment_sha256, load_json, root
from publication_integrity import (
    PublicationIntegrityError,
    bytes_sha256,
    candidate_binding_from_payload,
    consume_authorization_nonce,
    load_publication_policy,
    load_publisher_key,
    read_external_json,
    read_repo_json,
    remote_target_sha,
    validate_authorization_payload,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
    validate_pr_inventory_payload,
    validate_review_coverage_payload,
)
from strict_result_validation import load_and_validate_registered_result_file


def _validate_review_result(
    repo: Path,
    *,
    review_path: str,
    review_bytes: bytes,
    review: Mapping[str, Any],
    seal_path: str,
    seal_bytes: bytes,
    seal: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    run_id = review.get("run_id")
    assignment_id = review.get("assignment_id")
    context_version = review.get("context_version")
    if not all(isinstance(value, str) and value for value in (
        run_id,
        assignment_id,
        context_version,
    )):
        return ["review result lacks run/assignment/context identity"]
    validation = load_and_validate_registered_result_file(
        repo,
        repo / review_path,
        run_id=str(run_id),
        context_version=str(context_version),
    )
    errors.extend(validation.errors)
    if validation.result is not None and dict(validation.result) != dict(review):
        errors.append("review result changed during registered validation")
    assignment = validation.assignment
    if not isinstance(assignment, Mapping):
        return errors + ["review assignment is unavailable"]
    if review.get("schema_version") != 3:
        errors.append("publication review result must use schema version 3")
    if review.get("status") != "pass":
        errors.append("publication review result status must be pass")
    if review.get("workflow_role") != "reviewer":
        errors.append("publication review must come from workflow_role=reviewer")
    expected_binding = candidate_binding_from_payload(
        seal,
        seal_path=seal_path,
        seal_file_sha256=bytes_sha256(seal_bytes),
    )
    if review.get("candidate_binding") != expected_binding:
        errors.append("review result is bound to a different candidate")
    if assignment.get("candidate_binding") != expected_binding:
        errors.append("review assignment is bound to a different candidate")
    if assignment.get("assignment_sha256") != assignment_sha256(assignment):
        errors.append("review assignment checksum drifted")
    for field in ("change_set_id", "publication_group_id"):
        if review.get(field) != seal.get(field):
            errors.append(f"review result targets a different {field}")
    coverage_path = review.get("review_coverage_path")
    coverage_sha = review.get("review_coverage_sha256")
    if isinstance(coverage_path, str) and coverage_path:
        try:
            _, coverage_bytes, coverage = read_repo_json(
                repo, coverage_path, field="review coverage"
            )
            if bytes_sha256(coverage_bytes) != coverage_sha:
                raise PublicationIntegrityError("review coverage file hash drifted")
            errors.extend(
                validate_review_coverage_payload(
                    coverage,
                    seal=seal,
                    policy=policy,
                    run_id=str(run_id),
                    assignment_id=str(assignment_id),
                    risk_tier=str(assignment.get("risk_tier") or ""),
                    require_ready=True,
                    repo=repo,
                )
            )
        except PublicationIntegrityError as exc:
            errors.append(str(exc))
    else:
        errors.append("review result lacks review coverage")
    if review.get("result_path") != review_path:
        errors.append("review result_path does not match the supplied path")
    # The HMAC binds these exact bytes; keep the argument live and explicit.
    if not review_bytes:
        errors.append("review result file is empty")
    return errors


def _gate(args: argparse.Namespace, repo: Path) -> tuple[dict[str, Any], str | None]:
    errors: list[str] = []
    try:
        _, seal_bytes, seal = read_repo_json(
            repo, args.seal, field="candidate seal"
        )
        _, review_bytes, review = read_repo_json(
            repo, args.review_result, field="review result"
        )
        integration_path, integration_bytes, integration = read_repo_json(
            repo, args.integration, field="integration receipt"
        )
        _, inventory_bytes, inventory = read_external_json(
            repo, args.inventory, field="PR inventory"
        )
        _, authorization_bytes, authorization = read_external_json(
            repo, args.authorization, field="publish authorization"
        )
        policy_ref = seal.get("integration_policy")
        if not isinstance(policy_ref, Mapping):
            raise PublicationIntegrityError("candidate seal lacks integration_policy")
        _, policy = load_publication_policy(
            repo,
            policy_ref.get("path"),
            expected_sha256=str(policy_ref.get("sha256") or ""),
        )
        errors.extend(validate_candidate_seal_payload(seal, repo=repo))
        errors.extend(
            _validate_review_result(
                repo,
                review_path=args.review_result,
                review_bytes=review_bytes,
                review=review,
                seal_path=args.seal,
                seal_bytes=seal_bytes,
                seal=seal,
                policy=policy,
            )
        )
        errors.extend(
            validate_integration_receipt_payload(
                integration,
                seal=seal,
                policy=policy,
                now=datetime.now(timezone.utc),
                repo=repo,
                log_dir=integration_path.parent
                / (integration_path.stem + ".logs"),
            )
        )
        errors.extend(
            validate_pr_inventory_payload(
                inventory,
                seal=seal,
                policy=policy,
                now=datetime.now(timezone.utc),
            )
        )
        live_target = remote_target_sha(
            repo,
            str(seal.get("target_remote") or ""),
            str(seal.get("target_branch") or ""),
        )
        if live_target != seal.get("base_sha"):
            errors.append(
                "remote target moved after candidate freeze; rebase, reseal, and re-review"
            )
        if live_target != integration.get("latest_target_sha"):
            errors.append("integration receipt is not against the live remote target")
        key = load_publisher_key(args.publisher_key, repo=repo)
        artifact_hashes = {
            "candidate_seal_file_sha256": bytes_sha256(seal_bytes),
            "review_result_file_sha256": bytes_sha256(review_bytes),
            "integration_receipt_file_sha256": bytes_sha256(integration_bytes),
            "pr_inventory_file_sha256": bytes_sha256(inventory_bytes),
        }
        errors.extend(
            validate_authorization_payload(
                authorization,
                key=key,
                seal=seal,
                policy=policy,
                artifact_hashes=artifact_hashes,
                now=datetime.now(timezone.utc),
            )
        )
        if not authorization_bytes:
            errors.append("publish authorization file is empty")
        nonce = authorization.get("nonce")
    except (OSError, PublicationIntegrityError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        nonce = None

    payload = {
        "ok": not errors,
        "gate_state": (
            "READY_FOR_EXTERNAL_PUBLISHER" if not errors else "BLOCKED"
        ),
        "publication_executed": False,
        "change_set_id": locals().get("seal", {}).get("change_set_id"),
        "candidate_sha": locals().get("seal", {}).get("candidate_sha"),
        "errors": errors,
    }
    if not errors:
        payload["publication_request"] = {
            "publication_repository_host": authorization.get(
                "publication_repository_host"
            ),
            "publication_repository_slug": authorization.get(
                "publication_repository_slug"
            ),
            "remote_push_url": authorization.get("remote_push_url"),
            "head_refspec": authorization.get("head_refspec"),
            "pr_title": authorization.get("pr_title"),
            "pr_body": authorization.get("pr_body"),
            "pr_base_branch": authorization.get("pr_base_branch"),
            "pr_head_branch": authorization.get("pr_head_branch"),
            "pr_draft": authorization.get("pr_draft"),
        }
    return payload, str(nonce) if isinstance(nonce, str) else None


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "consume"):
        command = subparsers.add_parser(name)
        command.add_argument("--seal", required=True)
        command.add_argument("--review-result", required=True)
        command.add_argument("--integration", required=True)
        command.add_argument("--inventory", required=True)
        command.add_argument("--authorization", required=True)
        command.add_argument("--publisher-key", required=True)
        if name == "consume":
            command.add_argument("--nonce-ledger", required=True)
    args = parser.parse_args()
    repo = root()
    payload, nonce = _gate(args, repo)
    if payload["ok"] and args.command == "consume":
        assert nonce is not None
        try:
            consume_authorization_nonce(
                nonce,
                ledger_path=args.nonce_ledger,
                repo=repo,
            )
        except PublicationIntegrityError as exc:
            payload["ok"] = False
            payload["gate_state"] = "BLOCKED"
            payload["errors"].append(str(exc))
        else:
            payload["authorization_consumed"] = True
            payload["gate_state"] = "AUTHORIZED_FOR_IMMEDIATE_EXTERNAL_PUBLISHER_USE"
    else:
        payload["authorization_consumed"] = False
    print(json.dumps(payload, indent=2))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
