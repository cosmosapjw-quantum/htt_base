#!/usr/bin/env python3
"""Execute one sealed, explicitly owner-authorized attended PR transaction.

Direct ``git push`` and ``gh pr create`` remain forbidden to ordinary agent
commands.  This entrypoint first replays the existing candidate/review/
integration/inventory gate, consumes its one-use nonce, and then performs only
the exact SHA-sourced branch push and single review-PR creation bound by that
authorization.  It never approves, merges, force-pushes, or changes rulesets.

This attended lane uses the current authenticated GitHub identity.  It is a
procedural, user-authorized exception, not the credential-isolated hard
boundary provided by an external publisher.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping, Sequence

from _harness import root, utc_now
from pr_publication_gate import evaluate_gate
from publication_integrity import (
    ATTENDED_PUBLISHER_AUTHORIZATION_MODE,
    ATTENDED_PUBLICATION_TRANSACTION,
    PublicationIntegrityError,
    _walk_without_symlinks,
    consume_attended_authorization_nonce,
    load_publication_policy,
    read_repo_json,
    write_json_exclusive,
)


PR_FIELDS = (
    "number",
    "url",
    "headRefOid",
    "headRefName",
    "baseRefName",
    "title",
    "body",
    "isDraft",
)


def _run(
    argv: Sequence[str],
    *,
    repo: Path,
    timeout_seconds: int = 120,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GH_PROMPT_DISABLED": "1",
        }
    )
    try:
        completed = subprocess.run(
            list(argv),
            cwd=repo,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise PublicationIntegrityError(
            f"publisher executable is missing: {argv[0]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise PublicationIntegrityError(
            f"publisher command timed out: {Path(argv[0]).name}"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise PublicationIntegrityError(
            f"publisher command failed ({Path(argv[0]).name}, "
            f"exit {completed.returncode}): {detail[:2000]}"
        )
    return completed


def _remote_head(
    repo: Path,
    *,
    push_url: str,
    branch: str,
) -> str | None:
    completed = _run(
        ["git", "ls-remote", "--heads", push_url, f"refs/heads/{branch}"],
        repo=repo,
        timeout_seconds=30,
    )
    rows = [line.split() for line in completed.stdout.splitlines() if line.strip()]
    if not rows:
        return None
    if (
        len(rows) != 1
        or len(rows[0]) != 2
        or rows[0][1] != f"refs/heads/{branch}"
    ):
        raise PublicationIntegrityError(
            "candidate remote head did not resolve to zero or one exact branch"
        )
    return rows[0][0]


def _open_prs(repo: Path, *, repo_slug: str, branch: str) -> list[dict[str, Any]]:
    completed = _run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo_slug,
            "--state",
            "open",
            "--head",
            branch,
            "--limit",
            "100",
            "--json",
            ",".join(PR_FIELDS),
        ],
        repo=repo,
        timeout_seconds=60,
    )
    try:
        rows = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PublicationIntegrityError("gh returned malformed PR JSON") from exc
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise PublicationIntegrityError("gh PR inventory is not a JSON list of objects")
    return rows


def _normalized_body(value: object) -> str:
    if not isinstance(value, str):
        raise PublicationIntegrityError("GitHub PR body is missing")
    return value.replace("\r\n", "\n").rstrip("\n")


def _verify_single_pr(
    rows: list[dict[str, Any]],
    *,
    request: Mapping[str, Any],
    candidate_sha: str,
) -> dict[str, Any]:
    if len(rows) != 1:
        raise PublicationIntegrityError(
            f"expected exactly one open PR for the candidate head, found {len(rows)}"
        )
    row = rows[0]
    expected = {
        "headRefOid": candidate_sha,
        "headRefName": request.get("pr_head_branch"),
        "baseRefName": request.get("pr_base_branch"),
        "title": request.get("pr_title"),
        "isDraft": request.get("pr_draft"),
    }
    for field, value in expected.items():
        if row.get(field) != value:
            raise PublicationIntegrityError(
                f"published PR {field} differs from the sealed authorization"
            )
    if _normalized_body(row.get("body")) != _normalized_body(request.get("pr_body")):
        raise PublicationIntegrityError(
            "published PR body differs from the sealed authorization"
        )
    number = row.get("number")
    url = row.get("url")
    if type(number) is not int or not isinstance(url, str) or not url:
        raise PublicationIntegrityError("published PR lacks a stable number or URL")
    return row


def _write_receipt(repo: Path, output_value: str, receipt: Mapping[str, Any]) -> None:
    output = _receipt_output_path(repo, output_value)
    write_json_exclusive(output, receipt)


def _receipt_output_path(repo: Path, output_value: str) -> Path:
    output = Path(output_value).expanduser().absolute()
    try:
        output.resolve().relative_to(repo.resolve())
    except ValueError:
        pass
    else:
        raise PublicationIntegrityError(
            "attended publication receipt must be outside the repository"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    _walk_without_symlinks(output.parent)
    if output.exists() or output.is_symlink():
        raise PublicationIntegrityError(
            "attended publication receipt path must be unused"
        )
    if not output.parent.is_dir() or not os.access(output.parent, os.W_OK):
        raise PublicationIntegrityError(
            "attended publication receipt parent is not writable"
        )
    return output


def _policy_for_seal(repo: Path, seal_path: str) -> Mapping[str, Any]:
    _, _, seal = read_repo_json(repo, seal_path, field="candidate seal")
    policy_ref = seal.get("integration_policy")
    if not isinstance(policy_ref, Mapping):
        raise PublicationIntegrityError("candidate seal lacks integration policy")
    _, policy = load_publication_policy(
        repo,
        policy_ref.get("path"),
        expected_sha256=str(policy_ref.get("sha256") or ""),
    )
    attended = policy.get("attended_publication")
    if not isinstance(attended, Mapping) or attended.get("enabled") is not True:
        raise PublicationIntegrityError("policy does not enable attended publication")
    expected_entrypoint = (repo / str(attended.get("publisher_entrypoint"))).resolve()
    if Path(__file__).resolve() != expected_entrypoint:
        raise PublicationIntegrityError(
            "attended publisher entrypoint differs from the policy binding"
        )
    return policy


def _publish(args: argparse.Namespace, repo: Path) -> dict[str, Any]:
    _receipt_output_path(repo, args.receipt_output)
    policy = _policy_for_seal(repo, args.seal)
    attended = policy["attended_publication"]
    if attended.get("transaction") != ATTENDED_PUBLICATION_TRANSACTION:
        raise PublicationIntegrityError("attended publication transaction drifted")

    gate_payload, nonce = evaluate_gate(args, repo)
    if not gate_payload.get("ok") or nonce is None:
        errors = gate_payload.get("errors") or ["publication gate refused"]
        raise PublicationIntegrityError("; ".join(str(item) for item in errors))
    request = gate_payload.get("publication_request")
    if not isinstance(request, Mapping):
        raise PublicationIntegrityError("publication gate returned no request")
    if request.get("authorization_mode") != ATTENDED_PUBLISHER_AUTHORIZATION_MODE:
        raise PublicationIntegrityError(
            "attended publisher requires attended_explicit_user authorization"
        )

    authorization_file_sha256 = gate_payload.get("authorization_file_sha256")
    if not isinstance(authorization_file_sha256, str):
        raise PublicationIntegrityError(
            "publication gate returned no validated authorization identity"
        )
    nonce_ledger = request.get("nonce_ledger")
    if not isinstance(nonce_ledger, Mapping):
        raise PublicationIntegrityError(
            "publication gate returned no authorization-bound nonce ledger"
        )

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "transaction": ATTENDED_PUBLICATION_TRANSACTION,
        "authorization_mode": ATTENDED_PUBLISHER_AUTHORIZATION_MODE,
        "started_at": utc_now(),
        "candidate_sha": gate_payload.get("candidate_sha"),
        "candidate_branch": request.get("pr_head_branch"),
        "base_branch": request.get("pr_base_branch"),
        "publication_repository_slug": request.get("publication_repository_slug"),
        "authorization_file_sha256": authorization_file_sha256,
        "authorization_nonce_sha256": hashlib.sha256(nonce.encode("ascii")).hexdigest(),
        "ordinary_direct_mutation_bypass": False,
        "force_push": False,
        "approved": False,
        "merged": False,
        "ruleset_mutated": False,
        "branch_pushed": False,
        "pr_created": False,
    }

    try:
        consume_attended_authorization_nonce(
            nonce,
            ledger_identity=nonce_ledger,
            repo=repo,
        )
        receipt["authorization_consumed"] = True

        candidate_sha = str(gate_payload.get("candidate_sha") or "")
        branch = str(request.get("pr_head_branch") or "")
        push_url = str(request.get("remote_push_url") or "")
        remote_before = _remote_head(
            repo, push_url=push_url, branch=branch
        )
        if remote_before is None:
            _run(
                ["git", "push", push_url, str(request.get("head_refspec"))],
                repo=repo,
                timeout_seconds=180,
            )
            receipt["branch_pushed"] = True
        elif remote_before != candidate_sha:
            raise PublicationIntegrityError(
                "candidate remote branch exists at a different SHA"
            )
        receipt["remote_head_before"] = remote_before

        remote_after = _remote_head(repo, push_url=push_url, branch=branch)
        if remote_after != candidate_sha:
            raise PublicationIntegrityError(
                "remote candidate branch does not equal the sealed SHA after push"
            )
        receipt["remote_head_after"] = remote_after

        repo_slug = str(request.get("publication_repository_slug") or "")
        rows = _open_prs(repo, repo_slug=repo_slug, branch=branch)
        if not rows:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                prefix="htt-pr-body-",
                suffix=".md",
                delete=True,
            ) as body_file:
                body_file.write(str(request.get("pr_body") or ""))
                body_file.flush()
                argv = [
                    "gh",
                    "pr",
                    "create",
                    "--repo",
                    repo_slug,
                    "--base",
                    str(request.get("pr_base_branch") or ""),
                    "--head",
                    branch,
                    "--title",
                    str(request.get("pr_title") or ""),
                    "--body-file",
                    body_file.name,
                ]
                if request.get("pr_draft") is True:
                    argv.append("--draft")
                _run(argv, repo=repo, timeout_seconds=120)
            receipt["pr_created"] = True

        verified = _verify_single_pr(
            _open_prs(repo, repo_slug=repo_slug, branch=branch),
            request=request,
            candidate_sha=candidate_sha,
        )
        receipt.update(
            {
                "status": "PASS",
                "completed_at": utc_now(),
                "pr_number": verified["number"],
                "pr_url": verified["url"],
            }
        )
    except (OSError, PublicationIntegrityError) as exc:
        receipt.update(
            {
                "status": "FAIL",
                "completed_at": utc_now(),
                "error": str(exc),
            }
        )
        _write_receipt(repo, args.receipt_output, receipt)
        raise

    _write_receipt(repo, args.receipt_output, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", required=True)
    parser.add_argument("--review-result", required=True)
    parser.add_argument("--integration", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--publisher-key", required=True)
    parser.add_argument("--receipt-output", required=True)
    args = parser.parse_args()
    repo = root()
    try:
        receipt = _publish(args, repo)
    except PublicationIntegrityError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        raise SystemExit(1) from None
    print(json.dumps({"ok": True, **receipt}, indent=2))


if __name__ == "__main__":
    main()
