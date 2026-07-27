#!/usr/bin/env python3
"""Manage short-lived external-publisher authorization material.

The key and authorization file must remain outside the repository.  This tool
does not publish and does not grant ordinary agents a publisher role.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _harness import root
from publication_integrity import (
    PublicationIntegrityError,
    _walk_without_symlinks,
    authorization_hmac,
    bytes_sha256,
    load_publication_policy,
    load_publisher_key,
    read_external_bytes,
    read_external_json,
    read_repo_json,
    validate_candidate_seal_payload,
    validate_authorization_payload,
    write_json_exclusive,
)


def _init_key(repo: Path, key_path: str) -> None:
    path = Path(key_path).expanduser().absolute()
    try:
        path.resolve().relative_to(repo)
    except ValueError:
        pass
    else:
        raise PublicationIntegrityError("publisher key must be outside the repository")
    path.parent.mkdir(parents=True, exist_ok=True)
    _walk_without_symlinks(path.parent)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PublicationIntegrityError(f"cannot create publisher key: {exc}") from exc
    try:
        data = secrets.token_bytes(32).hex().encode("ascii") + b"\n"
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def _issue(args: argparse.Namespace, repo: Path) -> dict:
    _, seal_bytes, seal = read_repo_json(repo, args.seal, field="candidate seal")
    seal_errors = validate_candidate_seal_payload(seal, repo=repo)
    if seal_errors:
        raise PublicationIntegrityError("; ".join(seal_errors))
    policy_ref = seal.get("integration_policy")
    if not isinstance(policy_ref, dict):
        raise PublicationIntegrityError("candidate seal lacks integration_policy")
    _, policy = load_publication_policy(
        repo,
        policy_ref.get("path"),
        expected_sha256=str(policy_ref.get("sha256") or ""),
    )
    _, review_bytes, _ = read_repo_json(
        repo, args.review_result, field="review result"
    )
    _, integration_bytes, _ = read_repo_json(
        repo, args.integration, field="integration receipt"
    )
    _, inventory_bytes, _ = read_external_json(
        repo, args.inventory, field="PR inventory"
    )
    key = load_publisher_key(args.key, repo=repo)
    ttl = int(args.ttl_seconds)
    maximum = int(policy["max_authorization_ttl_seconds"])
    if type(args.ttl_seconds) is bool or not 1 <= ttl <= maximum:
        raise PublicationIntegrityError(
            f"authorization TTL must be between 1 and {maximum} seconds"
        )
    push_url = args.remote_push_url
    if push_url not in seal.get("remote_push_urls", []):
        raise PublicationIntegrityError("remote push URL is not bound by the seal")
    _, body_bytes = read_external_bytes(
        repo, args.pr_body_file, field="PR body"
    )
    try:
        pr_body = body_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PublicationIntegrityError("PR body must be UTF-8") from exc
    now = datetime.now(timezone.utc).replace(microsecond=0)
    authorization = {
        "schema_version": 1,
        "change_set_id": seal.get("change_set_id"),
        "publication_group_id": seal.get("publication_group_id"),
        "target_remote": seal.get("target_remote"),
        "target_branch": seal.get("target_branch"),
        "publication_repository_host": seal.get(
            "publication_repository_host"
        ),
        "publication_repository_slug": seal.get(
            "publication_repository_slug"
        ),
        "remote_push_url": push_url,
        "candidate_branch": seal.get("candidate_branch"),
        "candidate_sha": seal.get("candidate_sha"),
        "candidate_seal_sha256": seal.get("seal_sha256"),
        "head_refspec": (
            f"{seal.get('candidate_sha')}:"
            f"refs/heads/{seal.get('candidate_branch')}"
        ),
        "pr_title": args.pr_title,
        "pr_body": pr_body,
        "pr_base_branch": seal.get("target_branch"),
        "pr_head_branch": seal.get("candidate_branch"),
        "pr_draft": not args.ready,
        "artifact_hashes": {
            "candidate_seal_file_sha256": bytes_sha256(seal_bytes),
            "review_result_file_sha256": bytes_sha256(review_bytes),
            "integration_receipt_file_sha256": bytes_sha256(integration_bytes),
            "pr_inventory_file_sha256": bytes_sha256(inventory_bytes),
        },
        "approved_by": args.approved_by,
        "issued_at": now.isoformat(timespec="seconds"),
        "expires_at": (now + timedelta(seconds=ttl)).isoformat(timespec="seconds"),
        "nonce": secrets.token_hex(24),
    }
    if not str(args.approved_by).strip():
        raise PublicationIntegrityError("approved_by must be non-empty")
    authorization["hmac_sha256"] = authorization_hmac(
        authorization, key=key
    )
    errors = validate_authorization_payload(
        authorization,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=authorization["artifact_hashes"],
        now=now,
    )
    if errors:
        raise PublicationIntegrityError("; ".join(errors))
    output = Path(args.output).expanduser().absolute()
    try:
        output.resolve().relative_to(repo)
    except ValueError:
        pass
    else:
        raise PublicationIntegrityError(
            "publish authorization must be written outside the repository"
        )
    write_json_exclusive(output, authorization)
    return authorization


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_key = subparsers.add_parser("init-key")
    init_key.add_argument("--key", required=True)
    issue = subparsers.add_parser("issue")
    issue.add_argument("--key", required=True)
    issue.add_argument("--seal", required=True)
    issue.add_argument("--review-result", required=True)
    issue.add_argument("--integration", required=True)
    issue.add_argument("--inventory", required=True)
    issue.add_argument("--remote-push-url", required=True)
    issue.add_argument("--pr-title", required=True)
    issue.add_argument("--pr-body-file", required=True)
    issue.add_argument(
        "--ready",
        action="store_true",
        help="authorize a ready PR; the safer default authorizes a draft",
    )
    issue.add_argument("--approved-by", required=True)
    issue.add_argument("--ttl-seconds", type=int, default=1800)
    issue.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = root()
    try:
        if args.command == "init-key":
            _init_key(repo, args.key)
            print(json.dumps({"ok": True, "key": str(Path(args.key).absolute())}))
            return
        authorization = _issue(args, repo)
        print(json.dumps({"ok": True, **authorization}, indent=2))
    except PublicationIntegrityError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
