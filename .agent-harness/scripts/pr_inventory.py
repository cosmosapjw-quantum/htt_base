#!/usr/bin/env python3
"""Collect a live, read-only GitHub PR inventory for the external publisher."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from _harness import root
from publication_integrity import (
    PublicationIntegrityError,
    CHANGE_SET_METADATA_LINE_RE,
    PUBLICATION_GROUP_METADATA_LINE_RE,
    canonical_sha256,
    load_publication_policy,
    publication_repository_identity,
    read_repo_json,
    single_pr_metadata,
    validate_candidate_seal_payload,
    validate_pr_inventory_payload,
    write_json_exclusive,
)


def parse_gh_json(text: str) -> object:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate object key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite number: {value}")

    try:
        return json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise PublicationIntegrityError(
            f"gh PR inventory returned invalid JSON: {exc}"
        ) from exc


def _optional_metadata(pattern: re.Pattern[str], body: object, field: str) -> str | None:
    try:
        return single_pr_metadata(pattern, body, field=field)
    except PublicationIntegrityError:
        return None


def _stack_depths(rows: list[Mapping[str, Any]]) -> dict[int, int]:
    by_head: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        head = row.get("headRefName")
        if not isinstance(head, str) or not head or head in by_head:
            raise PublicationIntegrityError(
                "live PR inventory has a missing or duplicate head branch"
            )
        by_head[head] = row

    cache: dict[int, int] = {}

    def visit(row: Mapping[str, Any], trail: set[str]) -> int:
        number = row.get("number")
        if type(number) is not int or number < 1:
            raise PublicationIntegrityError(
                "live PR inventory contains an invalid PR number"
            )
        if number in cache:
            return cache[number]
        head = str(row.get("headRefName") or "")
        if head in trail:
            raise PublicationIntegrityError("live PR inventory contains a stack cycle")
        base = row.get("baseRefName")
        if not isinstance(base, str) or not base:
            raise PublicationIntegrityError(
                f"live PR #{number} lacks a base branch"
            )
        parent = by_head.get(base)
        depth = 1 if parent is None else 1 + visit(parent, trail | {head})
        cache[number] = depth
        return depth

    for row in rows:
        visit(row, set())
    return cache


def inventory_from_gh_rows(
    rows: object,
    *,
    seal: Mapping[str, Any],
    observed_at: str,
) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise PublicationIntegrityError("gh pr list did not return a JSON list")
    mappings: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise PublicationIntegrityError(f"gh PR row {index} is not an object")
        mappings.append(row)
    depths = _stack_depths(mappings)
    normalized: list[dict[str, Any]] = []
    for row in mappings:
        number = row.get("number")
        assert type(number) is int
        files = row.get("files")
        if not isinstance(files, list):
            raise PublicationIntegrityError(f"live PR #{number} lacks its file list")
        changed_files = row.get("changedFiles")
        if (
            type(changed_files) is not int
            or changed_files < 1
            or changed_files != len(files)
        ):
            raise PublicationIntegrityError(
                f"live PR #{number} file inventory is incomplete"
            )
        paths: list[str] = []
        for file_index, file_row in enumerate(files):
            if not isinstance(file_row, Mapping):
                raise PublicationIntegrityError(
                    f"live PR #{number} file {file_index} is not an object"
                )
            path = file_row.get("path")
            if not isinstance(path, str) or not path:
                raise PublicationIntegrityError(
                    f"live PR #{number} file {file_index} lacks a path"
                )
            paths.append(path)
        normalized.append(
            {
                "number": number,
                "head_branch": row.get("headRefName"),
                "base_branch": row.get("baseRefName"),
                "head_sha": row.get("headRefOid"),
                "change_set_id": _optional_metadata(
                    CHANGE_SET_METADATA_LINE_RE,
                    row.get("body"),
                    "Change-Set-ID",
                ),
                "publication_group_id": _optional_metadata(
                    PUBLICATION_GROUP_METADATA_LINE_RE,
                    row.get("body"),
                    "Publication-Group-ID",
                ),
                "changed_files": sorted(paths),
                "stack_depth": depths[number],
                "is_draft": row.get("isDraft"),
            }
        )
    normalized.sort(key=lambda row: row["number"])
    fetch_urls = seal.get("remote_fetch_urls")
    if not isinstance(fetch_urls, list) or not fetch_urls:
        raise PublicationIntegrityError("candidate seal lacks a fetch URL")
    inventory: dict[str, Any] = {
        "schema_version": 1,
        "repository_fetch_url": fetch_urls[0],
        "repository_host": seal.get("publication_repository_host"),
        "repository_slug": seal.get("publication_repository_slug"),
        "target_remote": seal.get("target_remote"),
        "target_branch": seal.get("target_branch"),
        "observed_at": observed_at,
        "open_prs": normalized,
    }
    inventory["inventory_sha256"] = canonical_sha256(
        inventory, omit={"inventory_sha256"}
    )
    return inventory


def collect(repo: Path, *, seal_path: str, repo_slug: str) -> dict[str, Any]:
    _, _, seal = read_repo_json(repo, seal_path, field="candidate seal")
    seal_errors = validate_candidate_seal_payload(seal, repo=repo)
    if seal_errors:
        raise PublicationIntegrityError("; ".join(seal_errors))
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo_slug):
        raise PublicationIntegrityError("--repo-slug must use OWNER/REPO form")
    publication_host, publication_slug = publication_repository_identity(
        [
            *seal.get("remote_fetch_urls", []),
            *seal.get("remote_push_urls", []),
        ]
    )
    if publication_host != seal.get("publication_repository_host"):
        raise PublicationIntegrityError(
            "candidate seal publication repository host is inconsistent"
        )
    if publication_slug != seal.get("publication_repository_slug"):
        raise PublicationIntegrityError(
            "candidate seal publication repository slug is inconsistent"
        )
    if repo_slug.lower() != publication_slug:
        raise PublicationIntegrityError(
            "--repo-slug does not match the sealed publication repository"
        )
    environment = dict(os.environ)
    environment["GH_PAGER"] = "cat"
    environment["GH_PROMPT_DISABLED"] = "1"
    environment["GH_HOST"] = publication_host
    environment.pop("GH_REPO", None)
    argv = [
        "gh",
        "pr",
        "list",
        "--repo",
        repo_slug,
        "--state",
        "open",
        "--limit",
        "1000",
        "--json",
        # changedFiles lets us fail closed if the nested file list is truncated.
        "number,headRefName,baseRefName,headRefOid,isDraft,body,changedFiles,files",
    ]
    try:
        completed = subprocess.run(
            argv,
            cwd=repo,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise PublicationIntegrityError("gh CLI is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise PublicationIntegrityError("gh PR inventory timed out") from exc
    if completed.returncode != 0:
        raise PublicationIntegrityError(
            f"gh PR inventory failed ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    rows = parse_gh_json(completed.stdout)
    return inventory_from_gh_rows(
        rows,
        seal=seal,
        observed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", required=True)
    parser.add_argument("--repo-slug", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = root()
    try:
        inventory = collect(
            repo,
            seal_path=args.seal,
            repo_slug=args.repo_slug,
        )
        output = Path(args.output).expanduser().absolute()
        try:
            output.resolve().relative_to(repo.resolve())
        except ValueError:
            pass
        else:
            raise PublicationIntegrityError(
                "PR inventory must be written outside the repository"
            )
        write_json_exclusive(output, inventory)
        _, _, seal = read_repo_json(repo, args.seal, field="candidate seal")
        policy_ref = seal.get("integration_policy")
        if not isinstance(policy_ref, Mapping):
            raise PublicationIntegrityError("candidate seal lacks integration_policy")
        _, policy = load_publication_policy(
            repo,
            policy_ref.get("path"),
            expected_sha256=str(policy_ref.get("sha256") or ""),
        )
        errors = validate_pr_inventory_payload(
            inventory,
            seal=seal,
            policy=policy,
        )
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "inventory_written": str(output),
                    "errors": errors,
                },
                indent=2,
            )
        )
        if errors:
            raise SystemExit(1)
    except PublicationIntegrityError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
