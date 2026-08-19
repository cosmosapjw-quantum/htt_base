"""PR-247 change-set/publication-integrity attack regressions."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_SCRIPTS = REPO_ROOT / ".agent-harness" / "scripts"
sys.path.insert(0, str(HARNESS_SCRIPTS))

from publication_integrity import (  # noqa: E402
    PYTHON_EXECUTABLE_TOKEN,
    PublicationIntegrityError,
    authorization_hmac,
    build_candidate_seal,
    bytes_sha256,
    candidate_binding_from_payload,
    canonical_sha256,
    classify_provider_payload,
    classify_publication_command,
    consume_authorization_nonce,
    load_publication_policy,
    load_publisher_key,
    mutable_candidate_binding,
    runtime_output_path,
    validate_authorization_payload,
    validate_candidate_seal_payload,
    validate_integration_receipt_payload,
    validate_pr_inventory_payload,
    validate_review_coverage_payload,
    write_json_exclusive,
)
from _harness import (  # noqa: E402
    enforce_work_unit_assignment_budget,
    validate_assignment_payload,
    validate_review_rereview_budget_exception,
)
from new_assignment import _work_unit_assignment_count  # noqa: E402
from integration_rehearsal import create_receipt  # noqa: E402
from pr_inventory import collect as collect_pr_inventory  # noqa: E402
from pr_inventory import inventory_from_gh_rows, parse_gh_json  # noqa: E402


POLICY_REL = "docs/publication-policy.json"
TARGET_BRANCH = "research/pr04-multicomponent"
CHANGE_SET = "CS-TEST-PUBLICATION-P0"
PUBLICATION_GROUP = "PG-TEST-PUBLICATION-P0"
CONTEXT_VERSION = "c" * 64


def _run(
    argv: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _git(repo: Path, *args: str) -> str:
    completed = _run(["git", *args], cwd=repo)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout.strip()


def _policy() -> dict:
    return {
        "schema_version": 1,
        "policy_id": "TEST-PUBLICATION-POLICY",
        "max_open_prs": 10,
        "max_direct_to_target_prs": 10,
        "max_prs_per_change_set": 1,
        "max_stack_depth": 10,
        "max_file_overlap_prs": 0,
        "max_inventory_age_seconds": 300,
        "max_receipt_age_seconds": 1800,
        "max_authorization_ttl_seconds": 1800,
        "required_review_cells": [
            "candidate_identity",
            "changed_public_apis",
            "changed_call_sites",
            "bool_as_int",
            "nan_inf",
            "empty_zero_negative",
            "shape_dtype",
            "duplicate_alias_reuse",
            "mutation_control",
            "property_metamorphic",
            "compatibility",
            "concurrency_replay_state",
            "latest_target_integration",
        ],
        "required_commands": [
            {
                "id": "deterministic-oracle",
                "argv": [
                    PYTHON_EXECUTABLE_TOKEN,
                    "-c",
                    "from pathlib import Path; "
                    "assert Path('feature.txt').read_text() == 'candidate\\n'",
                ],
                "timeout_seconds": 30,
            }
        ],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _install_test_harness_files(repo: Path) -> None:
    templates = repo / ".agent-harness" / "templates"
    templates.mkdir(parents=True)
    for source in (REPO_ROOT / ".agent-harness" / "templates").glob("*.json"):
        (templates / source.name).write_bytes(source.read_bytes())
    context = repo / ".agent-harness" / "context"
    context.mkdir(parents=True)
    _write_json(
        context / "CONTEXT_INDEX.json",
        {
            "schema_version": 1,
            "context_version": CONTEXT_VERSION,
            "max_injected_chars": 12000,
            "shared_files": ["shared.md"],
            "pack_files": ["shared.md"],
            "file_hashes": {},
            "live_sources": {
                "dag": "docs/codex_handoff/pr_backlog.yaml",
                "status": "docs/codex_handoff/pr_status.yaml",
            },
            "role_files": {},
        },
    )
    (context / "CLAIM_REGISTRY.jsonl").write_text(
        json.dumps({"claim_id": "C-001", "statement": "Test claim."}) + "\n",
        encoding="utf-8",
    )
    agents = repo / ".codex" / "agents"
    agents.mkdir(parents=True)
    (agents / "harness-engineer.toml").write_text(
        'name = "harness_engineer"\n'
        'description = "read-only test reviewer"\n'
        'sandbox_mode = "read-only"\n'
        'model_reasoning_effort = "high"\n'
        'developer_instructions = "test"\n',
        encoding="utf-8",
    )
    (repo / "shared.md").write_text("shared\n", encoding="utf-8")
    (repo / "input.txt").write_text("input\n", encoding="utf-8")
    handoff = repo / "docs" / "codex_handoff"
    handoff.mkdir(parents=True)
    (handoff / "pr_backlog.yaml").write_text(
        "generated_on: '2026-07-26'\nscope: test\nprs: []\n",
        encoding="utf-8",
    )
    (handoff / "pr_status.yaml").write_text(
        "generated_on: '2026-07-26'\ncompleted: []\nblocked: []\n"
        "pending: []\nin_progress: null\n",
        encoding="utf-8",
    )


def _make_candidate_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    remote.mkdir()
    assert _run(["git", "init", "--bare", "-q"], cwd=remote).returncode == 0
    seed = tmp_path / "seed"
    seed.mkdir()
    assert _run(["git", "init", "-q", "-b", TARGET_BRANCH], cwd=seed).returncode == 0
    _git(seed, "config", "user.name", "Harness Test")
    _git(seed, "config", "user.email", "harness@example.invalid")
    (seed / ".gitignore").write_text(
        ".agent-harness/runs/\n.agent-harness/runtime/\n.prguard/runtime/\n",
        encoding="utf-8",
    )
    (seed / ".prguard").mkdir()
    (seed / ".prguard" / ".gitignore").write_text("runtime/\n", encoding="utf-8")
    (seed / "docs").mkdir()
    _write_json(seed / POLICY_REL, _policy())
    (seed / "SPEC.md").write_text("# Test spec\n", encoding="utf-8")
    _install_test_harness_files(seed)
    _git(seed, "add", ".")
    _git(seed, "commit", "-qm", "baseline")
    _git(seed, "remote", "add", "origin", str(remote))
    _git(seed, "push", "-q", "-u", "origin", TARGET_BRANCH)
    _git(remote, "symbolic-ref", "HEAD", f"refs/heads/{TARGET_BRANCH}")

    repo = tmp_path / "repo"
    cloned = _run(["git", "clone", "-q", str(remote), str(repo)], cwd=tmp_path)
    assert cloned.returncode == 0, cloned.stdout + cloned.stderr
    _git(repo, "config", "user.name", "Harness Test")
    _git(repo, "config", "user.email", "harness@example.invalid")
    _git(
        repo,
        "remote",
        "set-url",
        "--push",
        "origin",
        "https://github.com/example/test-publication.git",
    )
    _git(repo, "switch", "-q", "-c", "changeset/test-publication-p0")
    (repo / "feature.txt").write_text("candidate\n", encoding="utf-8")
    _git(repo, "add", "feature.txt")
    _git(repo, "commit", "-qm", "candidate")
    return repo, remote


def _seal(repo: Path) -> dict:
    return build_candidate_seal(
        repo,
        change_set_id=CHANGE_SET,
        publication_group_id=PUBLICATION_GROUP,
        target_ref=f"origin/{TARGET_BRANCH}",
        candidate_ref="HEAD",
        integration_policy_path=POLICY_REL,
    )


def _test_stable_patch_id(repo: Path, commit: str) -> str:
    shown = subprocess.run(
        ["git", "show", "--pretty=format:", "--binary", "--full-index", commit],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    computed = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=repo,
        input=shown.stdout,
        check=True,
        capture_output=True,
        text=False,
    ).stdout.decode("ascii").strip()
    assert computed
    return computed.split()[0]


def _install_test_logical_patch_lineage(
    repo: Path, *, corruption: str | None = None
) -> dict:
    candidate_branch = _git(repo, "branch", "--show-current")
    included_commit = _git(repo, "rev-parse", "HEAD")
    included_parent = _git(repo, "rev-parse", "HEAD^")
    included_tree = _git(repo, "rev-parse", "HEAD^{tree}")
    included_alias = _git(
        repo,
        "commit-tree",
        included_tree,
        "-p",
        included_parent,
        "-m",
        "duplicate source alias",
    )

    _git(repo, "switch", "-q", "-c", "source/excluded", f"origin/{TARGET_BRANCH}")
    (repo / "excluded.txt").write_text("obsolete\n", encoding="utf-8")
    _git(repo, "add", "excluded.txt")
    _git(repo, "commit", "-qm", "obsolete source patch")
    excluded_commit = _git(repo, "rev-parse", "HEAD")
    _git(repo, "switch", "-q", candidate_branch)

    included_patch_id = _test_stable_patch_id(repo, included_commit)
    excluded_patch_id = _test_stable_patch_id(repo, excluded_commit)
    authority_sha = hashlib.sha256((repo / "SPEC.md").read_bytes()).hexdigest()
    lineage = {
        "schema_version": 1,
        "authority": {
            "document_id": "SPEC.md",
            "sha256": authority_sha,
        },
        "groups": [
            {
                "group_id": "G20",
                "disposition": "INCLUDE",
                "representative_commit": included_commit,
                "duplicate_alias_commits": [included_alias],
                "stable_patch_id": included_patch_id,
                "candidate_commit": included_commit,
            },
            {
                "group_id": "G22",
                "disposition": "EXCLUDE_OBSOLETE",
                "representative_commit": excluded_commit,
                "duplicate_alias_commits": [],
                "stable_patch_id": excluded_patch_id,
                "candidate_commit": None,
            },
        ],
    }
    if corruption == "wrong_representative":
        lineage["groups"][0]["representative_commit"] = excluded_commit
    elif corruption == "wrong_alias":
        lineage["groups"][0]["duplicate_alias_commits"] = [excluded_commit]
    elif corruption == "missing_candidate":
        lineage["groups"][0]["candidate_commit"] = excluded_commit
    elif corruption == "duplicate_group":
        lineage["groups"].append(copy.deepcopy(lineage["groups"][0]))
    elif corruption is not None:
        raise AssertionError(f"unknown corruption: {corruption}")

    policy = json.loads((repo / POLICY_REL).read_text(encoding="utf-8"))
    policy["logical_patch_lineage"] = lineage
    _write_json(repo / POLICY_REL, policy)
    _git(repo, "add", POLICY_REL)
    _git(repo, "commit", "-qm", "bind logical patch lineage")
    return lineage


@pytest.mark.parametrize(
    "command",
    [
        "git push origin HEAD",
        "/usr/bin/git push origin HEAD",
        "git -C . push origin HEAD",
        "git -c alias.p=push p origin HEAD",
        "git config alias.publish push; git publish origin HEAD",
        "git submodule foreach 'git push origin HEAD'",
        "git bisect run git push origin HEAD",
        "git send-pack origin HEAD",
        "git-http-push origin HEAD",
        "git-remote-https origin https://github.com/o/r.git",
        "/usr/lib/git-core/git-push origin HEAD",
        "true;git push origin HEAD",
        "gh --repo owner/repo pr create",
        "gh pr ready 42",
        "gh api --method=POST repos/o/r/pulls",
        "gh api -XPOST repos/o/r/pulls",
        "gh api -Ftitle=test repos/o/r/pulls",
        "curl -X POST https://api.github.com/repos/o/r/pulls",
        "bash -c 'git push origin HEAD'",
        "/bin/bash -lc 'git push origin HEAD'",
        "bash -cl 'git push origin HEAD'",
        "sh -xec 'git push origin HEAD'",
        "python -Bc 'git push origin HEAD'",
        "node --eval 'gh pr create'",
        "ssh git@github.com git-receive-pack owner/repo.git",
    ],
)
def test_publication_command_equivalents_are_denied(command: str) -> None:
    denied, reason = classify_publication_command(command)
    assert denied is True
    assert reason


@pytest.mark.parametrize(
    "command",
    [
        "git status --short",
        "git diff --stat",
        "gh pr view 42",
        "gh --repo owner/repo pr list",
        "gh api --method GET repos/o/r/pulls",
        "bash -lc 'git status --short'",
    ],
)
def test_read_only_git_and_gh_commands_remain_available(command: str) -> None:
    assert classify_publication_command(command) == (False, "")


def test_integration_policy_rejects_publication_capable_argv(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    policy = _policy()
    policy["required_commands"][0]["argv"] = [
        "git",
        "-C",
        ".",
        "push",
        "origin",
        "HEAD",
    ]
    _write_json(repo / POLICY_REL, policy)
    with pytest.raises(PublicationIntegrityError, match="publication-capable"):
        load_publication_policy(repo, POLICY_REL)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("claim_ceiling", "unbounded", "claim_ceiling"),
        ("family_identification_gate", "PASS", "family_identification_gate"),
        ("ordinary_agent_push_forbidden", False, "ordinary_agent_push_forbidden"),
        (
            "ordinary_agent_pr_mutation_forbidden",
            False,
            "ordinary_agent_pr_mutation_forbidden",
        ),
        ("invalidates_review", [], "invalidates_review"),
    ],
)
def test_policy_nonrelaxable_metadata_fails_closed(
    tmp_path: Path,
    field: str,
    replacement: object,
    message: str,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    policy = _policy()
    policy.update(
        {
            "claim_ceiling": "diagnostic_only",
            "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
            "ordinary_agent_push_forbidden": True,
            "ordinary_agent_pr_mutation_forbidden": True,
            "invalidates_review": ["candidate_sha_changed"],
        }
    )
    policy[field] = replacement
    _write_json(repo / POLICY_REL, policy)

    with pytest.raises(PublicationIntegrityError, match=message):
        load_publication_policy(repo, POLICY_REL)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("change_set_id", "CS-WRONG"),
        ("publication_group_id", "PG-WRONG"),
        ("target_ref", "origin/not-the-target"),
        ("target_sha", "0" * 40),
    ],
)
def test_candidate_seal_cross_binds_declared_policy_identity(
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    policy = _policy()
    policy.update(
        {
            "change_set_id": CHANGE_SET,
            "publication_group_id": PUBLICATION_GROUP,
            "target_ref": f"origin/{TARGET_BRANCH}",
            "target_sha": _git(repo, "rev-parse", f"origin/{TARGET_BRANCH}"),
        }
    )
    policy[field] = replacement
    _write_json(repo / POLICY_REL, policy)
    _git(repo, "add", POLICY_REL)
    _git(repo, "commit", "-qm", f"mutate policy {field}")

    with pytest.raises(PublicationIntegrityError, match=field):
        _seal(repo)


def test_pr247_policy_uses_portable_receipted_python() -> None:
    relative = (
        "docs/research_program/long_horizon_rescue/"
        "pr247_publication_policy.json"
    )
    _, policy = load_publication_policy(REPO_ROOT, relative)
    assert policy["required_commands"]
    assert all(
        row["argv"][0] == PYTHON_EXECUTABLE_TOKEN
        for row in policy["required_commands"]
    )


def test_publication_artifacts_reject_nan_and_duplicate_json_keys() -> None:
    with pytest.raises(PublicationIntegrityError, match="NaN"):
        canonical_sha256({"unsafe": float("nan")})
    from publication_integrity import read_json_bytes

    with pytest.raises(PublicationIntegrityError, match="duplicate"):
        read_json_bytes(b'{"schema_version":1,"schema_version":1}', field="test")
    with pytest.raises(PublicationIntegrityError, match="non-finite"):
        read_json_bytes(b'{"unsafe":NaN}', field="test")


def test_provider_payloads_use_documented_command_fields() -> None:
    for provider, payload in (
        (
            "codex",
            {"tool_name": "Bash", "tool_input": {"command": "/usr/bin/git push"}},
        ),
        (
            "claude",
            {"tool_name": "Bash", "tool_input": {"command": "gh pr create"}},
        ),
        (
            "antigravity",
            {
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "git -C . push"},
                }
            },
        ),
        (
            "antigravity",
            {"tool_args": {"CommandLine": "git push origin HEAD"}},
        ),
    ):
        denied, reason = classify_provider_payload(payload, provider=provider)
        assert denied is True, (provider, payload)
        assert reason
    malformed = {"toolCall": {"name": "run_command", "args": {"command": "git push"}}}
    assert classify_provider_payload(malformed, provider="antigravity")[0] is True
    ambiguous = {
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "git status"},
        },
        "tool_args": {"CommandLine": "git push origin HEAD"},
    }
    assert classify_provider_payload(ambiguous, provider="antigravity")[0] is True
    assert classify_provider_payload({}, provider="antigravity")[0] is True
    assert (
        classify_provider_payload(
            {
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": "/tmp/read-only"},
                }
            },
            provider="antigravity",
        )[0]
        is True
    )
    assert (
        classify_provider_payload(
            {"tool_args": {"CommandLine": "git status"}},
            provider="antigravity",
        )
        == (False, "")
    )


def test_provider_hook_outputs_are_provider_native(tmp_path: Path) -> None:
    hook = HARNESS_SCRIPTS / "provider_publication_hook.py"
    codex = _run(
        [sys.executable, str(hook), "--provider", "codex"],
        cwd=REPO_ROOT,
        input_text=json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "git push"}}
        ),
    )
    assert codex.returncode == 0
    assert json.loads(codex.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

    claude = _run(
        [sys.executable, str(hook), "--provider", "claude"],
        cwd=REPO_ROOT,
        input_text=json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "gh pr create"}}
        ),
    )
    assert claude.returncode == 2
    assert "PUBLICATION_FIREWALL" in claude.stderr

    antigravity = _run(
        [sys.executable, str(hook), "--provider", "antigravity"],
        cwd=REPO_ROOT,
        input_text=json.dumps(
            {
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "git status"},
                }
            }
        ),
    )
    assert antigravity.returncode == 0
    assert json.loads(antigravity.stdout) == {"decision": "allow"}

    antigravity_legacy_publication = _run(
        [sys.executable, str(hook), "--provider", "antigravity"],
        cwd=REPO_ROOT,
        input_text=json.dumps(
            {"tool_args": {"CommandLine": "git push origin HEAD"}}
        ),
    )
    assert antigravity_legacy_publication.returncode == 2
    assert "PUBLICATION_FIREWALL" in antigravity_legacy_publication.stderr

    antigravity_legacy_read = _run(
        [sys.executable, str(hook), "--provider", "antigravity"],
        cwd=REPO_ROOT,
        input_text=json.dumps(
            {"tool_args": {"CommandLine": "git status"}}
        ),
    )
    assert antigravity_legacy_read.returncode == 0
    assert antigravity_legacy_read.stdout == ""

    antigravity_unknown = _run(
        [sys.executable, str(hook), "--provider", "antigravity"],
        cwd=REPO_ROOT,
        input_text=json.dumps({}),
    )
    assert antigravity_unknown.returncode == 0
    assert json.loads(antigravity_unknown.stdout)["decision"] == "deny"

    duplicate = _run(
        [sys.executable, str(hook), "--provider", "codex"],
        cwd=REPO_ROOT,
        input_text=(
            '{"tool_name":"Bash","tool_input":{"command":"git status"},'
            '"tool_input":{"command":"git push"}}'
        ),
    )
    assert duplicate.returncode == 0
    assert json.loads(duplicate.stdout)["hookSpecificOutput"][
        "permissionDecision"
    ] == "deny"


def test_candidate_seal_binds_diff_remote_policy_and_clean_state(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    assert validate_candidate_seal_payload(seal, repo=repo) == []
    assert seal["target_branch"] == TARGET_BRANCH
    assert seal["candidate_branch"].startswith("changeset/")
    assert seal["changed_files"] == [{"status": "A", "path": "feature.txt"}]
    assert len(seal["stable_patch_ids"]) == 1
    assert seal["stable_patch_ids"][0]["commit"] == seal["candidate_sha"]
    assert len(seal["stable_patch_ids"][0]["stable_patch_id"]) == 40
    assert len(seal["stable_patch_ids_sha256"]) == 64
    assert len(seal["production_hash"]) == 64
    assert seal["diff_stat"] == {
        "production": 1,
        "tests": 0,
        "runners": 0,
        "receipts": 0,
        "generated": 0,
    }
    binding = candidate_binding_from_payload(
        seal,
        seal_path=".prguard/runtime/CANDIDATE_SEAL.json",
        seal_file_sha256="0" * 64,
    )
    assert binding["production_hash"] == seal["production_hash"]

    _git(repo, "remote", "set-url", "--push", "origin", "ssh://example.invalid/x")
    errors = validate_candidate_seal_payload(seal, repo=repo)
    assert any(
        "publication remote" in error or "remote_push_urls" in error
        for error in errors
    )
    for escaped in (
        ".prguard/runtime/../escape.json",
        ".prguard/runtimeevil/escape.json",
        "../escape.json",
    ):
        with pytest.raises(PublicationIntegrityError):
            runtime_output_path(
                repo, escaped, field="test runtime output"
            )


def test_candidate_seal_binds_verified_logical_patch_lineage(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    lineage = _install_test_logical_patch_lineage(repo)

    seal = _seal(repo)

    assert seal["logical_patch_lineage"] == lineage
    assert seal["logical_patch_lineage_sha256"] == bytes_sha256(
        json.dumps(
            lineage,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )
    assert validate_candidate_seal_payload(seal, repo=repo) == []


@pytest.mark.parametrize(
    "corruption",
    ["wrong_representative", "wrong_alias", "missing_candidate", "duplicate_group"],
)
def test_candidate_seal_rejects_invalid_logical_patch_lineage(
    tmp_path: Path, corruption: str
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    _install_test_logical_patch_lineage(repo, corruption=corruption)

    with pytest.raises(PublicationIntegrityError, match="logical patch lineage"):
        _seal(repo)


def test_candidate_seal_rejects_embedded_remote_credentials(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    _git(
        repo,
        "remote",
        "set-url",
        "--push",
        "origin",
        "https://secret@github.com/example/test-publication.git",
    )
    with pytest.raises(PublicationIntegrityError, match="embed credentials"):
        _seal(repo)


def test_candidate_seal_requires_github_publication_push_destination(
    tmp_path: Path,
) -> None:
    repo, remote = _make_candidate_repo(tmp_path)
    _git(repo, "remote", "set-url", "--push", "origin", str(remote))
    with pytest.raises(
        PublicationIntegrityError,
        match="exactly one GitHub publication",
    ):
        _seal(repo)


def test_candidate_seal_rejects_dirty_candidate_and_target_movement(
    tmp_path: Path,
) -> None:
    repo, remote = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    assert validate_candidate_seal_payload(seal, repo=repo)
    (repo / "dirty.txt").unlink()

    other = tmp_path / "other"
    cloned = _run(["git", "clone", "-q", str(remote), str(other)], cwd=tmp_path)
    assert cloned.returncode == 0
    _git(other, "config", "user.name", "Harness Test")
    _git(other, "config", "user.email", "harness@example.invalid")
    (other / "target.txt").write_text("advanced\n", encoding="utf-8")
    _git(other, "add", "target.txt")
    _git(other, "commit", "-qm", "advance target")
    _git(other, "push", "-q", "origin", TARGET_BRANCH)
    seal_rel = ".prguard/runtime/CANDIDATE_SEAL.json"
    write_json_exclusive(repo / seal_rel, seal)
    with pytest.raises(PublicationIntegrityError, match="base_sha|target moved"):
        create_receipt(
            repo,
            seal_path=seal_rel,
            output_path=".prguard/runtime/INTEGRATION_RECEIPT.json",
        )
    errors = validate_candidate_seal_payload(seal, repo=repo)
    assert any("base_sha" in error or "target" in error for error in errors)


def _coverage(
    repo: Path,
    seal: dict,
    policy: dict,
    *,
    run_id: str = "run-review",
    assignment_id: str = "A-REVIEW",
) -> dict:
    artifact_path = (
        f".agent-harness/runs/{run_id}/artifacts/{assignment_id}/oracle.log"
    )
    artifact = repo / artifact_path
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("independent oracle passed\n", encoding="utf-8")
    artifact_data = artifact.read_bytes()
    oracle_argv = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-q",
        "scripts/codex_harness/test_publication_integrity.py",
    ]
    value = {
        "schema_version": 1,
        "run_id": run_id,
        "assignment_id": assignment_id,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "diff_sha256": seal["diff_sha256"],
        "changed_files_sha256": seal["changed_files_sha256"],
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "first_verdict_read_only": True,
        "correlated_review": False,
        "coverage_cells": [
            {
                "cell": cell,
                "status": "PASS",
                "evidence_refs": [f"test:{cell}"],
                "rationale": "",
            }
            for cell in policy["required_review_cells"]
        ],
        "independent_oracles": [
            {
                "oracle_id": "ORACLE-1",
                "kind": "property_test",
                "status": "PASS",
                "argv": oracle_argv,
                "command_fingerprint": canonical_sha256(
                    {"argv": oracle_argv}
                ),
                "started_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "completed_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "returncode": 0,
                "timed_out": False,
                "artifact_path": artifact_path,
                "artifact_sha256": bytes_sha256(artifact_data),
                "artifact_bytes": len(artifact_data),
                "evidence_refs": ["test:property"],
            }
        ],
    }
    value["coverage_sha256"] = canonical_sha256(
        value, omit={"coverage_sha256"}
    )
    return value


def test_review_coverage_is_executable_and_candidate_bound(tmp_path: Path) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(repo, POLICY_REL)
    coverage = _coverage(repo, seal, dict(policy))
    assert (
        validate_review_coverage_payload(
            coverage,
            seal=seal,
            policy=policy,
            run_id="run-review",
            assignment_id="A-REVIEW",
            risk_tier="R2",
            repo=repo,
        )
        == []
    )
    drifted = copy.deepcopy(coverage)
    drifted["candidate_sha"] = "0" * 40
    drifted["coverage_sha256"] = canonical_sha256(
        drifted, omit={"coverage_sha256"}
    )
    assert validate_review_coverage_payload(
        drifted,
        seal=seal,
        policy=policy,
        run_id="run-review",
        assignment_id="A-REVIEW",
        risk_tier="R2",
        repo=repo,
    )
    blocking = copy.deepcopy(coverage)
    blocking["coverage_cells"][0]["status"] = "FAIL"
    blocking["coverage_sha256"] = canonical_sha256(
        blocking, omit={"coverage_sha256"}
    )
    assert validate_review_coverage_payload(
        blocking,
        seal=seal,
        policy=policy,
        run_id="run-review",
        assignment_id="A-REVIEW",
        risk_tier="R2",
        require_ready=False,
        repo=repo,
    ) == []
    assert validate_review_coverage_payload(
        blocking,
        seal=seal,
        policy=policy,
        run_id="run-review",
        assignment_id="A-REVIEW",
        risk_tier="R2",
        require_ready=True,
        repo=repo,
    )


def test_integration_receipt_rejects_true_only_and_stale_receipts(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(repo, POLICY_REL)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    receipt = {
        "schema_version": 1,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "diff_sha256": seal["diff_sha256"],
        "changed_files_sha256": seal["changed_files_sha256"],
        "target_remote": seal["target_remote"],
        "target_branch": seal["target_branch"],
        "latest_target_sha": seal["base_sha"],
        "integration_policy_sha256": seal["integration_policy"]["sha256"],
        "merged_tree_sha": seal["candidate_tree_sha"],
        "started_at": now.isoformat(timespec="seconds"),
        "completed_at": now.isoformat(timespec="seconds"),
        "status": "PASS",
        "commands": [
            {
                "id": "true-only",
                "argv": ["true"],
                "timeout_seconds": 1,
                "started_at": now.isoformat(timespec="seconds"),
                "completed_at": now.isoformat(timespec="seconds"),
                "returncode": 0,
                "timed_out": False,
                "stdout_sha256": hashlib.sha256(b"").hexdigest(),
                "stdout_bytes": 0,
                "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                "stderr_bytes": 0,
            }
        ],
    }
    receipt["receipt_sha256"] = canonical_sha256(
        receipt, omit={"receipt_sha256"}
    )
    errors = validate_integration_receipt_payload(
        receipt, seal=seal, policy=policy, now=now
    )
    assert any("drifted from policy" in error for error in errors)

    valid = copy.deepcopy(receipt)
    valid["commands"][0].update(policy["required_commands"][0])
    stale = now - timedelta(seconds=int(policy["max_receipt_age_seconds"]) + 1)
    valid["started_at"] = stale.isoformat(timespec="seconds")
    valid["completed_at"] = stale.isoformat(timespec="seconds")
    valid["commands"][0]["started_at"] = stale.isoformat(timespec="seconds")
    valid["commands"][0]["completed_at"] = stale.isoformat(timespec="seconds")
    valid["receipt_sha256"] = canonical_sha256(
        valid, omit={"receipt_sha256"}
    )
    assert any(
        "stale" in error
        for error in validate_integration_receipt_payload(
            valid, seal=seal, policy=policy, now=now
        )
    )


def test_integration_rehearsal_binds_merged_tree_and_command_logs(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    seal_rel = ".prguard/runtime/CANDIDATE_SEAL.json"
    write_json_exclusive(repo / seal_rel, seal)
    receipt_rel = ".prguard/runtime/INTEGRATION_RECEIPT.json"
    receipt = create_receipt(
        repo,
        seal_path=seal_rel,
        output_path=receipt_rel,
    )
    _, policy = load_publication_policy(repo, POLICY_REL)
    log_dir = (
        repo / ".prguard/runtime/INTEGRATION_RECEIPT.logs"
    )
    assert validate_integration_receipt_payload(
        receipt,
        seal=seal,
        policy=policy,
        repo=repo,
        log_dir=log_dir,
    ) == []
    command = receipt["commands"][0]
    assert command["policy_argv"][0] == PYTHON_EXECUTABLE_TOKEN
    assert Path(command["argv"][0]).is_absolute()
    assert command["argv"][0] == command["executable_path"]
    assert command["executable_path"] == str(
        Path(os.path.abspath(sys.executable))
    )
    assert command["executable_realpath"] == str(
        Path(sys.executable).resolve(strict=True)
    )

    forged_executable = copy.deepcopy(receipt)
    forged_executable["commands"][0]["executable_sha256"] = "1" * 64
    forged_executable["receipt_sha256"] = canonical_sha256(
        forged_executable, omit={"receipt_sha256"}
    )
    assert any(
        "executable hash drifted" in error
        for error in validate_integration_receipt_payload(
            forged_executable,
            seal=seal,
            policy=policy,
            repo=repo,
            log_dir=log_dir,
        )
    )

    forged_realpath = copy.deepcopy(receipt)
    forged_realpath["commands"][0]["executable_realpath"] = str(
        Path(command["executable_realpath"]).parent
    )
    forged_realpath["receipt_sha256"] = canonical_sha256(
        forged_realpath, omit={"receipt_sha256"}
    )
    assert any(
        "executable realpath drifted" in error
        for error in validate_integration_receipt_payload(
            forged_realpath,
            seal=seal,
            policy=policy,
            repo=repo,
            log_dir=log_dir,
        )
    )

    forged_tree = copy.deepcopy(receipt)
    forged_tree["merged_tree_sha"] = "1" * 40
    forged_tree["receipt_sha256"] = canonical_sha256(
        forged_tree, omit={"receipt_sha256"}
    )
    assert any(
        "exact target/candidate merge" in error
        for error in validate_integration_receipt_payload(
            forged_tree,
            seal=seal,
            policy=policy,
            repo=repo,
            log_dir=log_dir,
        )
    )

    stdout_log = log_dir / "deterministic-oracle.stdout"
    stdout_log.write_text("tampered\n", encoding="utf-8")
    assert any(
        "log hash drifted" in error or "byte count drifted" in error
        for error in validate_integration_receipt_payload(
            receipt,
            seal=seal,
            policy=policy,
            repo=repo,
            log_dir=log_dir,
        )
    )


def test_integration_rehearsal_runs_commands_from_a_clean_merged_tree(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    policy = _policy()
    policy["required_commands"][0]["argv"] = [
        PYTHON_EXECUTABLE_TOKEN,
        "-c",
        "import subprocess; "
        "status = subprocess.run("
        "['git', 'status', '--porcelain'], "
        "check=True, capture_output=True, text=True); "
        "assert status.stdout == ''",
    ]
    _write_json(repo / POLICY_REL, policy)
    _git(repo, "add", POLICY_REL)
    _git(repo, "commit", "-qm", "require clean integration command root")
    seal = _seal(repo)
    seal_rel = ".prguard/runtime/CLEAN_CANDIDATE_SEAL.json"
    write_json_exclusive(repo / seal_rel, seal)

    receipt = create_receipt(
        repo,
        seal_path=seal_rel,
        output_path=".prguard/runtime/CLEAN_INTEGRATION_RECEIPT.json",
    )

    assert receipt["status"] == "PASS"
    assert receipt["commands"][0]["returncode"] == 0


def _inventory(seal: dict, *, rows: list[dict] | None = None) -> dict:
    value = {
        "schema_version": 1,
        "repository_fetch_url": seal["remote_fetch_urls"][0],
        "repository_host": seal["publication_repository_host"],
        "repository_slug": seal["publication_repository_slug"],
        "target_remote": seal["target_remote"],
        "target_branch": seal["target_branch"],
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "open_prs": rows or [],
    }
    value["inventory_sha256"] = canonical_sha256(
        value, omit={"inventory_sha256"}
    )
    return value


def _open_pr(seal: dict, *, change_set_id: str | None = None) -> dict:
    return {
        "number": 7,
        "head_branch": "changeset/other",
        "base_branch": "other-target",
        "head_sha": "1" * 40,
        "change_set_id": change_set_id or "CS-OTHER",
        "publication_group_id": "PG-OTHER",
        "changed_files": ["other.txt"],
        "stack_depth": 1,
        "is_draft": False,
    }


def test_pr284_policy_allows_one_open_predecessor_and_bounds_next_slots(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(
        REPO_ROOT,
        "docs/research_program/post_pr275/pr284_publication_policy.json",
    )
    assert {
        "max_open_prs": policy["max_open_prs"],
        "max_stack_depth": policy["max_stack_depth"],
        "max_file_overlap_prs": policy["max_file_overlap_prs"],
    } == {
        "max_open_prs": 2,
        "max_stack_depth": 2,
        "max_file_overlap_prs": 1,
    }

    predecessor = _open_pr(seal)
    predecessor.update(
        {
            "number": 380,
            "head_branch": seal["target_branch"],
            "head_sha": seal["base_sha"],
            "changed_files": ["feature.txt"],
            "stack_depth": 1,
        }
    )
    assert validate_pr_inventory_payload(
        _inventory(seal, rows=[predecessor]),
        seal=seal,
        policy=policy,
    ) == []

    second_open = _open_pr(seal)
    second_open.update(
        {
            "number": 381,
            "head_branch": "changeset/unrelated-open-pr",
            "head_sha": "2" * 40,
            "changed_files": ["unrelated.txt"],
        }
    )
    assert any(
        "open-PR budget" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[predecessor, second_open]),
            seal=seal,
            policy=policy,
        )
    )

    too_deep = copy.deepcopy(predecessor)
    too_deep["stack_depth"] = 2
    assert any(
        "stack-depth budget" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[too_deep]),
            seal=seal,
            policy=policy,
        )
    )

    second_overlap = copy.deepcopy(second_open)
    second_overlap["changed_files"] = ["feature.txt"]
    overlap_probe_policy = copy.deepcopy(policy)
    overlap_probe_policy["max_open_prs"] = 3
    overlap_probe_policy["max_stack_depth"] = 3
    assert any(
        "overlaps open PR" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[predecessor, second_overlap]),
            seal=seal,
            policy=overlap_probe_policy,
        )
    )


def test_pr285_policy_allows_two_open_predecessors_and_bounds_next_slots(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(
        REPO_ROOT,
        "docs/research_program/post_pr275/pr285_publication_policy.json",
    )
    assert {
        "max_open_prs": policy["max_open_prs"],
        "max_stack_depth": policy["max_stack_depth"],
        "max_file_overlap_prs": policy["max_file_overlap_prs"],
    } == {
        "max_open_prs": 3,
        "max_stack_depth": 3,
        "max_file_overlap_prs": 2,
    }

    first = _open_pr(seal)
    first.update(
        {
            "number": 380,
            "head_branch": "changeset/pr283-weak-identification-recovery-20260810",
            "head_sha": "1" * 40,
            "base_branch": "canonical/base",
            "changed_files": ["feature.txt"],
            "stack_depth": 1,
        }
    )
    second = _open_pr(seal)
    second.update(
        {
            "number": 381,
            "head_branch": seal["target_branch"],
            "head_sha": seal["base_sha"],
            "base_branch": first["head_branch"],
            "changed_files": ["feature.txt"],
            "stack_depth": 2,
        }
    )
    assert validate_pr_inventory_payload(
        _inventory(seal, rows=[first, second]),
        seal=seal,
        policy=policy,
    ) == []

    third_open = _open_pr(seal)
    third_open.update(
        {
            "number": 382,
            "head_branch": "changeset/unrelated-open-pr",
            "head_sha": "2" * 40,
            "changed_files": ["unrelated.txt"],
        }
    )
    assert any(
        "open-PR budget" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[first, second, third_open]),
            seal=seal,
            policy=policy,
        )
    )

    too_deep = copy.deepcopy(second)
    too_deep["stack_depth"] = 3
    assert any(
        "stack-depth budget" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[first, too_deep]),
            seal=seal,
            policy=policy,
        )
    )

    third_overlap = copy.deepcopy(third_open)
    third_overlap["changed_files"] = ["feature.txt"]
    overlap_probe_policy = copy.deepcopy(policy)
    overlap_probe_policy["max_open_prs"] = 4
    overlap_probe_policy["max_stack_depth"] = 4
    assert any(
        "overlaps open PR" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[first, second, third_overlap]),
            seal=seal,
            policy=overlap_probe_policy,
        )
    )


def test_pr286_policy_allows_three_open_predecessors_and_bounds_next_slots(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(
        REPO_ROOT,
        "docs/research_program/post_pr275/pr286_publication_policy.json",
    )
    assert {
        "max_open_prs": policy["max_open_prs"],
        "max_stack_depth": policy["max_stack_depth"],
        "max_file_overlap_prs": policy["max_file_overlap_prs"],
    } == {
        "max_open_prs": 4,
        "max_stack_depth": 4,
        "max_file_overlap_prs": 3,
    }

    first = _open_pr(seal)
    first.update(
        {
            "number": 380,
            "head_branch": "changeset/pr283-weak-identification-recovery-20260810",
            "head_sha": "1" * 40,
            "base_branch": "canonical/base",
            "changed_files": ["feature.txt"],
            "stack_depth": 1,
        }
    )
    second = _open_pr(seal)
    second.update(
        {
            "number": 381,
            "head_branch": "changeset/pr284-finite-depth-law-recovery-20260810",
            "head_sha": "2" * 40,
            "base_branch": first["head_branch"],
            "changed_files": ["feature.txt"],
            "stack_depth": 2,
        }
    )
    third = _open_pr(seal)
    third.update(
        {
            "number": 382,
            "head_branch": seal["target_branch"],
            "head_sha": seal["base_sha"],
            "base_branch": second["head_branch"],
            "changed_files": ["feature.txt"],
            "stack_depth": 3,
        }
    )
    assert validate_pr_inventory_payload(
        _inventory(seal, rows=[first, second, third]),
        seal=seal,
        policy=policy,
    ) == []

    fourth_open = _open_pr(seal)
    fourth_open.update(
        {
            "number": 383,
            "head_branch": "changeset/unrelated-open-pr",
            "head_sha": "3" * 40,
            "changed_files": ["unrelated.txt"],
        }
    )
    assert any(
        "open-PR budget" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[first, second, third, fourth_open]),
            seal=seal,
            policy=policy,
        )
    )

    too_deep = copy.deepcopy(third)
    too_deep["stack_depth"] = 4
    assert any(
        "stack-depth budget" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[first, second, too_deep]),
            seal=seal,
            policy=policy,
        )
    )

    fourth_overlap = copy.deepcopy(fourth_open)
    fourth_overlap["changed_files"] = ["feature.txt"]
    overlap_probe_policy = copy.deepcopy(policy)
    overlap_probe_policy["max_open_prs"] = 5
    overlap_probe_policy["max_stack_depth"] = 5
    assert any(
        "overlaps open PR" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[first, second, third, fourth_overlap]),
            seal=seal,
            policy=overlap_probe_policy,
        )
    )


def test_pr285_policy_binds_exact_g20_g21_include_and_g22_exclude_lineage() -> None:
    _, policy = load_publication_policy(
        REPO_ROOT,
        "docs/research_program/post_pr275/pr285_publication_policy.json",
    )
    lineage = policy["logical_patch_lineage"]
    groups = {item["group_id"]: item for item in lineage["groups"]}
    assert lineage["authority"] == {
        "document_id": "HTT_PROCESS_INFLATION_SALVAGE_AUDIT_20260810.md",
        "sha256": "c42b44641a7655edc36c11e23a747433275285a4f342a824fa69dda88bd6f436",
    }
    assert {key: value["disposition"] for key, value in groups.items()} == {
        "G20": "INCLUDE",
        "G21": "INCLUDE",
        "G22": "EXCLUDE_OBSOLETE",
    }

    candidate_commits = set(
        _git(
            REPO_ROOT,
            "rev-list",
            "--no-merges",
            f"{policy['target_sha']}..HEAD",
        ).splitlines()
    )
    candidate_patch_ids = {
        _test_stable_patch_id(REPO_ROOT, commit) for commit in candidate_commits
    }
    for group in groups.values():
        source_commits = [
            group["representative_commit"],
            *group["duplicate_alias_commits"],
        ]
        assert {
            _test_stable_patch_id(REPO_ROOT, commit) for commit in source_commits
        } == {group["stable_patch_id"]}
        if group["disposition"] == "INCLUDE":
            assert group["candidate_commit"] in candidate_commits
            assert (
                _test_stable_patch_id(REPO_ROOT, group["candidate_commit"])
                == group["stable_patch_id"]
            )
            assert group["stable_patch_id"] in candidate_patch_ids
        else:
            assert group["candidate_commit"] is None
            assert group["stable_patch_id"] not in candidate_patch_ids


def test_inventory_rejects_aliases_duplicates_overlap_and_bool_counts(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(repo, POLICY_REL)
    assert validate_pr_inventory_payload(
        _inventory(seal), seal=seal, policy=policy
    ) == []

    wrong_repository = _inventory(seal)
    wrong_repository["repository_slug"] = "example/empty-repository"
    wrong_repository["inventory_sha256"] = canonical_sha256(
        wrong_repository, omit={"inventory_sha256"}
    )
    assert any(
        "repository slug" in error
        for error in validate_pr_inventory_payload(
            wrong_repository, seal=seal, policy=policy
        )
    )

    duplicate = _inventory(
        seal, rows=[_open_pr(seal, change_set_id=seal["change_set_id"])]
    )
    assert validate_pr_inventory_payload(
        duplicate, seal=seal, policy=policy
    )
    alias = _inventory(
        seal, rows=[_open_pr(seal, change_set_id="changeset:247")]
    )
    assert any(
        "canonical" in error
        for error in validate_pr_inventory_payload(
            alias, seal=seal, policy=policy
        )
    )
    missing_identity_row = _open_pr(seal)
    missing_identity_row["change_set_id"] = None
    assert validate_pr_inventory_payload(
        _inventory(seal, rows=[missing_identity_row]),
        seal=seal,
        policy=policy,
    )
    duplicate_group_row = _open_pr(seal)
    duplicate_group_row["publication_group_id"] = seal[
        "publication_group_id"
    ]
    assert any(
        "publication group" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[duplicate_group_row]),
            seal=seal,
            policy=policy,
        )
    )
    duplicate_head_row = _open_pr(seal)
    duplicate_head_row["head_branch"] = seal["candidate_branch"]
    assert any(
        "candidate branch" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[duplicate_head_row]),
            seal=seal,
            policy=policy,
        )
    )
    overlap_row = _open_pr(seal)
    overlap_row["changed_files"] = ["feature.txt"]
    overlap = _inventory(seal, rows=[overlap_row])
    assert any(
        "overlaps" in error
        for error in validate_pr_inventory_payload(
            overlap, seal=seal, policy=policy
        )
    )
    alias_path_row = _open_pr(seal)
    alias_path_row["changed_files"] = ["./feature.txt"]
    assert any(
        "canonical repository-relative" in error
        for error in validate_pr_inventory_payload(
            _inventory(seal, rows=[alias_path_row]),
            seal=seal,
            policy=policy,
        )
    )
    boolean = _inventory(seal, rows=[_open_pr(seal)])
    boolean["open_prs"][0]["number"] = True
    boolean["inventory_sha256"] = canonical_sha256(
        boolean, omit={"inventory_sha256"}
    )
    assert any(
        "bool" in error
        for error in validate_pr_inventory_payload(
            boolean, seal=seal, policy=policy
        )
    )


def test_live_inventory_normalizes_metadata_and_stack_depth(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(repo, POLICY_REL)
    rows = [
        {
            "number": 11,
            "headRefName": "changeset/parent",
            "baseRefName": TARGET_BRANCH,
            "headRefOid": "1" * 40,
            "isDraft": False,
            "body": "Change-Set-ID: CS-PARENT\n"
            "Publication-Group-ID: PG-PARENT\n",
            "changedFiles": 1,
            "files": [{"path": "parent.txt"}],
        },
        {
            "number": 12,
            "headRefName": "changeset/child",
            "baseRefName": "changeset/parent",
            "headRefOid": "2" * 40,
            "isDraft": True,
            "body": "Change-Set-ID: CS-CHILD\n"
            "Publication-Group-ID: PG-CHILD\n",
            "changedFiles": 1,
            "files": [{"path": "child.txt"}],
        },
    ]
    inventory = inventory_from_gh_rows(
        rows,
        seal=seal,
        observed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    assert [row["stack_depth"] for row in inventory["open_prs"]] == [1, 2]
    assert validate_pr_inventory_payload(
        inventory, seal=seal, policy=policy
    ) == []

    missing_metadata = copy.deepcopy(rows)
    missing_metadata[0]["body"] = ""
    incomplete = inventory_from_gh_rows(
        missing_metadata,
        seal=seal,
        observed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    assert validate_pr_inventory_payload(
        incomplete, seal=seal, policy=policy
    )

    cycle = copy.deepcopy(rows)
    cycle[0]["baseRefName"] = "changeset/child"
    with pytest.raises(PublicationIntegrityError, match="cycle"):
        inventory_from_gh_rows(
            cycle,
            seal=seal,
            observed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
    truncated = copy.deepcopy(rows)
    truncated[0]["changedFiles"] = 2
    with pytest.raises(PublicationIntegrityError, match="incomplete"):
        inventory_from_gh_rows(
            truncated,
            seal=seal,
            observed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


def test_live_inventory_json_rejects_duplicate_keys_and_nonfinite_numbers() -> None:
    with pytest.raises(PublicationIntegrityError, match="duplicate object key"):
        parse_gh_json('[{"number":1,"number":2}]')
    with pytest.raises(PublicationIntegrityError, match="non-finite"):
        parse_gh_json('[{"number":NaN}]')


def test_live_inventory_query_is_bound_to_sealed_repository(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    seal_path = repo / ".prguard" / "runtime" / "candidate-seal.json"
    _write_json(seal_path, seal)
    with pytest.raises(PublicationIntegrityError, match="does not match"):
        collect_pr_inventory(
            repo,
            seal_path=".prguard/runtime/candidate-seal.json",
            repo_slug="example/empty-repository",
        )


def _authorization(
    seal: dict,
    policy: dict,
    key: bytes,
    artifact_hashes: dict[str, str],
    *,
    issued: datetime,
    expires: datetime,
) -> dict:
    value = {
        "schema_version": 1,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "target_remote": seal["target_remote"],
        "target_branch": seal["target_branch"],
        "publication_repository_host": seal["publication_repository_host"],
        "publication_repository_slug": seal["publication_repository_slug"],
        "remote_push_url": seal["remote_push_urls"][0],
        "candidate_branch": seal["candidate_branch"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "head_refspec": (
            f"{seal['candidate_sha']}:"
            f"refs/heads/{seal['candidate_branch']}"
        ),
        "pr_title": "PR-247: enforce publication integrity",
        "pr_body": (
            f"Change-Set-ID: {seal['change_set_id']}\n"
            f"Publication-Group-ID: {seal['publication_group_id']}\n"
        ),
        "pr_base_branch": seal["target_branch"],
        "pr_head_branch": seal["candidate_branch"],
        "pr_draft": True,
        "artifact_hashes": artifact_hashes,
        "approved_by": "human-reviewer",
        "issued_at": issued.isoformat(timespec="seconds"),
        "expires_at": expires.isoformat(timespec="seconds"),
        "nonce": "ab" * 24,
    }
    value["hmac_sha256"] = authorization_hmac(value, key=key)
    return value


def test_authorization_requires_external_key_bounded_ttl_and_one_use_nonce(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    _, policy = load_publication_policy(repo, POLICY_REL)
    key_path = tmp_path / "publisher.key"
    key_path.write_text(("42" * 32) + "\n", encoding="ascii")
    key_path.chmod(0o600)
    key = load_publisher_key(key_path, repo=repo)
    hashes = {
        "candidate_seal_file_sha256": "1" * 64,
        "review_result_file_sha256": "2" * 64,
        "integration_receipt_file_sha256": "3" * 64,
        "pr_inventory_file_sha256": "4" * 64,
    }
    now = datetime.now(timezone.utc).replace(microsecond=0)
    authorization = _authorization(
        seal,
        dict(policy),
        key,
        hashes,
        issued=now,
        expires=now + timedelta(seconds=60),
    )
    assert validate_authorization_payload(
        authorization,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=hashes,
        repo=repo,
        now=now,
    ) == []
    assert authorization["head_refspec"] == (
        f"{seal['candidate_sha']}:refs/heads/{seal['candidate_branch']}"
    )
    invalid_body = copy.deepcopy(authorization)
    invalid_body["pr_body"] = "missing canonical metadata\n"
    invalid_body["hmac_sha256"] = authorization_hmac(
        invalid_body, key=key
    )
    assert validate_authorization_payload(
        invalid_body,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=hashes,
        repo=repo,
        now=now,
    )

    overlong = _authorization(
        seal,
        dict(policy),
        key,
        hashes,
        issued=now,
        expires=now
        + timedelta(seconds=int(policy["max_authorization_ttl_seconds"]) + 1),
    )
    assert validate_authorization_payload(
        overlong,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=hashes,
        repo=repo,
        now=now,
    )
    inside = repo / "publisher.key"
    inside.write_text(("42" * 32) + "\n", encoding="ascii")
    inside.chmod(0o600)
    with pytest.raises(PublicationIntegrityError, match="outside"):
        load_publisher_key(inside, repo=repo)
    inside.unlink()
    linked = tmp_path / "publisher-linked.key"
    os.link(key_path, linked)
    with pytest.raises(PublicationIntegrityError, match="hard links"):
        load_publisher_key(key_path, repo=repo)
    linked.unlink()

    ledger = tmp_path / "nonce-ledger"
    consume_authorization_nonce(
        authorization["nonce"], ledger_path=ledger, repo=repo
    )
    with pytest.raises(PublicationIntegrityError, match="already used"):
        consume_authorization_nonce(
            authorization["nonce"], ledger_path=ledger, repo=repo
        )
    ledger_link = tmp_path / "nonce-ledger-link"
    os.link(ledger, ledger_link)
    with pytest.raises(PublicationIntegrityError, match="hard links"):
        consume_authorization_nonce(
            "cd" * 24, ledger_path=ledger, repo=repo
        )


def test_init_run_never_guesses_main_and_records_explicit_target(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    _git(repo, "symbolic-ref", "--delete", "refs/remotes/origin/HEAD")
    script = HARNESS_SCRIPTS / "init_run.py"
    common = [
        sys.executable,
        str(script),
        "--run-id",
        "run-explicit-target",
        "--work-unit",
        "PR-247",
        "--change-set",
        CHANGE_SET,
        "--publication-group",
        PUBLICATION_GROUP,
        "--integration-policy",
        POLICY_REL,
        "--spec-ref",
        "SPEC.md",
    ]
    refused = _run(common, cwd=repo)
    assert refused.returncode != 0
    assert "explicit remote target" in refused.stderr
    assert "main" not in refused.stderr

    initialized = _run(
        [*common, "--target-ref", f"origin/{TARGET_BRANCH}"],
        cwd=repo,
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    plan = json.loads(
        (
            repo
            / ".agent-harness/runs/run-explicit-target/RUN_PLAN.json"
        ).read_text(encoding="utf-8")
    )
    assert plan["schema_version"] == 2
    assert plan["target_ref"] == f"refs/remotes/origin/{TARGET_BRANCH}"
    assert plan["target_branch"] == TARGET_BRANCH
    assert plan["change_set_id"] == CHANGE_SET
    assert plan["candidate_binding"] == mutable_candidate_binding()


def test_reviewer_rereview_budget_exception_is_named_single_run_and_single_use(
) -> None:
    run_id = "run-pr254-rereview"
    allowed = ["A-PR254-FINAL-HARNESS", "A-PR254-FINAL-PHYSSTAT"]
    plan = {
        "run_id": run_id,
        "work_unit_id": "PR-254",
        "budget": {
            "max_total_per_work_unit": 16,
        },
        "budget_exception": {
            "exception_id": "PR254-OWNER-REREVIEW-20260729",
            "kind": "single_run_reviewer_rereview",
            "run_id": run_id,
            "work_unit_id": "PR-254",
            "authorized_by": "owner user explicit authorization 2026-07-29",
            "reason": "two executed benchmark evidence defects require rereview",
            "baseline_limit": 16,
            "additional_assignments": 2,
            "allowed_workflow_role": "reviewer",
            "allowed_assignment_ids": allowed,
            "single_use": True,
        },
    }
    assert (
        validate_review_rereview_budget_exception(plan, run_id=run_id)
        == plan["budget_exception"]
    )

    enforce_work_unit_assignment_budget(
        plan,
        run_id=run_id,
        assignment_id=allowed[0],
        workflow_role="reviewer",
        cumulative_count=16,
        current_run_assignment_ids=set(),
    )
    enforce_work_unit_assignment_budget(
        plan,
        run_id=run_id,
        assignment_id=allowed[1],
        workflow_role="reviewer",
        cumulative_count=17,
        current_run_assignment_ids={allowed[0]},
    )

    with pytest.raises(
        PublicationIntegrityError,
        match="named reviewer assignments",
    ):
        enforce_work_unit_assignment_budget(
            plan,
            run_id=run_id,
            assignment_id="A-PR254-UNLISTED",
            workflow_role="reviewer",
            cumulative_count=16,
            current_run_assignment_ids=set(),
        )
    with pytest.raises(
        PublicationIntegrityError,
        match="named reviewer assignments",
    ):
        enforce_work_unit_assignment_budget(
            plan,
            run_id=run_id,
            assignment_id=allowed[0],
            workflow_role="implementer",
            cumulative_count=16,
            current_run_assignment_ids=set(),
        )
    with pytest.raises(
        PublicationIntegrityError,
        match="named reviewer assignments",
    ):
        enforce_work_unit_assignment_budget(
            plan,
            run_id=run_id,
            assignment_id=allowed[0],
            workflow_role="adjudicator",
            cumulative_count=16,
            current_run_assignment_ids=set(),
        )
    with pytest.raises(
        PublicationIntegrityError,
        match="cannot be consumed before",
    ):
        enforce_work_unit_assignment_budget(
            plan,
            run_id=run_id,
            assignment_id=allowed[0],
            workflow_role="reviewer",
            cumulative_count=15,
            current_run_assignment_ids=set(),
        )
    with pytest.raises(PublicationIntegrityError, match="exhausted"):
        enforce_work_unit_assignment_budget(
            plan,
            run_id=run_id,
            assignment_id=allowed[1],
            workflow_role="reviewer",
            cumulative_count=18,
            current_run_assignment_ids=set(allowed),
        )
    wrong_run = copy.deepcopy(plan)
    wrong_run["budget_exception"]["run_id"] = "different-run"
    with pytest.raises(
        PublicationIntegrityError,
        match="different run",
    ):
        validate_review_rereview_budget_exception(
            wrong_run,
            run_id=run_id,
        )
    wrong_work_unit = copy.deepcopy(plan)
    wrong_work_unit["budget_exception"]["work_unit_id"] = "PR-OTHER"
    with pytest.raises(
        PublicationIntegrityError,
        match="different work unit",
    ):
        validate_review_rereview_budget_exception(
            wrong_work_unit,
            run_id=run_id,
        )


def test_init_run_records_the_exact_reviewer_rereview_exception(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    run_id = "run-pr254-rereview"
    initialized = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "init_run.py"),
            "--run-id",
            run_id,
            "--work-unit",
            "PR-254",
            "--change-set",
            CHANGE_SET,
            "--publication-group",
            PUBLICATION_GROUP,
            "--integration-policy",
            POLICY_REL,
            "--target-ref",
            f"origin/{TARGET_BRANCH}",
            "--spec-ref",
            "SPEC.md",
            "--review-rereview-exception-id",
            "PR254-OWNER-REREVIEW-20260729",
            "--review-rereview-authorized-by",
            "owner user explicit authorization 2026-07-29",
            "--review-rereview-reason",
            "two executed benchmark evidence defects require rereview",
            "--review-rereview-exception-assignment",
            "A-PR254-FINAL-HARNESS",
            "--review-rereview-exception-assignment",
            "A-PR254-FINAL-PHYSSTAT",
        ],
        cwd=repo,
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    plan = json.loads(
        (
            repo
            / f".agent-harness/runs/{run_id}/RUN_PLAN.json"
        ).read_text(encoding="utf-8")
    )
    assert plan["budget"]["max_total_per_work_unit"] == 16
    assert plan["budget_exception"]["run_id"] == run_id
    assert plan["budget_exception"]["work_unit_id"] == "PR-254"
    assert plan["budget_exception"]["allowed_workflow_role"] == "reviewer"
    assert plan["budget_exception"]["allowed_assignment_ids"] == [
        "A-PR254-FINAL-HARNESS",
        "A-PR254-FINAL-PHYSSTAT",
    ]
    assert plan["budget_exception"]["single_use"] is True


def test_reviewer_rereview_budget_exception_cannot_raise_the_ordinary_limit(
) -> None:
    plan = {
        "run_id": "run-pr254-rereview",
        "work_unit_id": "PR-254",
        "budget": {"max_total_per_work_unit": 18},
        "budget_exception": {
            "exception_id": "PR254-OWNER-REREVIEW-20260729",
            "kind": "single_run_reviewer_rereview",
            "run_id": "run-pr254-rereview",
            "work_unit_id": "PR-254",
            "authorized_by": "owner user explicit authorization 2026-07-29",
            "reason": "two executed benchmark evidence defects require rereview",
            "baseline_limit": 16,
            "additional_assignments": 2,
            "allowed_workflow_role": "reviewer",
            "allowed_assignment_ids": [
                "A-PR254-FINAL-HARNESS",
                "A-PR254-FINAL-PHYSSTAT",
            ],
            "single_use": True,
        },
    }
    with pytest.raises(
        PublicationIntegrityError,
        match="cannot alter the ordinary work-unit limit",
    ):
        validate_review_rereview_budget_exception(
            plan,
            run_id="run-pr254-rereview",
        )


def test_reviewer_rereview_reauthorization_is_rejected() -> None:
    run_id = "run-pr254-rereview-r2"
    allowed = ["A-PR254-R2-HARNESS", "A-PR254-R2-PHYSSTAT"]
    plan = {
        "run_id": run_id,
        "work_unit_id": "PR-254",
        "budget": {"max_total_per_work_unit": 16},
        "budget_exception": {
            "exception_id": "PR254-OWNER-REREVIEW-R2-20260729",
            "kind": "single_run_reviewer_rereview_reauthorization",
            "run_id": run_id,
            "work_unit_id": "PR-254",
            "authorized_by": "owner user explicit authorization 2026-07-29",
            "reason": "repair findings require one final candidate bound review",
            "baseline_limit": 16,
            "cumulative_start": 18,
            "additional_assignments": 2,
            "allowed_workflow_role": "reviewer",
            "allowed_assignment_ids": allowed,
            "single_use": True,
        },
    }
    with pytest.raises(PublicationIntegrityError, match="fields must exactly match"):
        validate_review_rereview_budget_exception(plan, run_id=run_id)


def test_init_run_rejects_retired_reauthorization_option(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    run_id = "run-pr254-rereview-r2"
    initialized = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "init_run.py"),
            "--run-id",
            run_id,
            "--work-unit",
            "PR-254",
            "--change-set",
            CHANGE_SET,
            "--publication-group",
            PUBLICATION_GROUP,
            "--integration-policy",
            POLICY_REL,
            "--target-ref",
            f"origin/{TARGET_BRANCH}",
            "--spec-ref",
            "SPEC.md",
            "--review-rereview-exception-id",
            "PR254-OWNER-REREVIEW-R2-20260729",
            "--review-rereview-authorized-by",
            "owner user explicit authorization 2026-07-29",
            "--review-rereview-reason",
            "repair findings require one final candidate bound review",
            "--review-rereview-reauthorization-start",
            "20",
            "--review-rereview-exception-assignment",
            "A-PR254-R2-HARNESS",
            "--review-rereview-exception-assignment",
            "A-PR254-R2-PHYSSTAT",
        ],
        cwd=repo,
    )
    assert initialized.returncode != 0
    assert "unrecognized arguments" in initialized.stderr


def test_cumulative_work_unit_budget_fails_closed_on_malformed_history(
    tmp_path: Path,
) -> None:
    harness = tmp_path / ".agent-harness"
    malformed_run = harness / "runs" / "malformed-history"
    (malformed_run / "assignments").mkdir(parents=True)
    (malformed_run / "assignments" / "A-PR254-HISTORICAL.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (malformed_run / "RUN_PLAN.json").write_text(
        "{not valid json\n",
        encoding="utf-8",
    )
    with pytest.raises(
        PublicationIntegrityError,
        match="cannot be verified.*malformed RUN_PLAN",
    ):
        _work_unit_assignment_count(harness, "PR-254")


def test_pr254_focused_runner_resolves_tests_outside_repository_cwd(
    tmp_path: Path,
) -> None:
    completed = _run(
        [
            sys.executable,
            "-B",
            str(
                REPO_ROOT
                / "scripts/codex_harness/run_pr254_integration.py"
            ),
            "focused",
        ],
        cwd=tmp_path,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "42 passed" in completed.stdout


def test_reviewer_registration_requires_frozen_candidate_and_no_publisher_role(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    seal = _seal(repo)
    seal_rel = ".prguard/runtime/CANDIDATE_SEAL.json"
    write_json_exclusive(repo / seal_rel, seal)
    seal_bytes = (repo / seal_rel).read_bytes()
    run_id = "run-review"
    run_dir = repo / ".agent-harness" / "runs" / run_id
    for name in ("assignments", "results", "launches", "artifacts"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    plan = json.loads(
        (repo / ".agent-harness/templates/RUN_PLAN.json").read_text(
            encoding="utf-8"
        )
    )
    policy_bytes = (repo / POLICY_REL).read_bytes()
    policy = json.loads(policy_bytes)
    plan.update(
        {
            "run_id": run_id,
            "work_unit_id": "PR-247",
            "change_set_id": CHANGE_SET,
            "publication_group_id": PUBLICATION_GROUP,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "spec_ref": "SPEC.md",
            "target_remote": seal["target_remote"],
            "target_branch": seal["target_branch"],
            "target_ref": seal["target_ref"],
            "base_sha": seal["base_sha"],
            "candidate_ref": "HEAD",
            "integration_policy": {
                "path": POLICY_REL,
                "sha256": bytes_sha256(policy_bytes),
                "policy_id": policy["policy_id"],
            },
            "candidate_binding": mutable_candidate_binding(),
            "context_version": CONTEXT_VERSION,
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
        }
    )
    _write_json(run_dir / "RUN_PLAN.json", plan)
    active = repo / ".agent-harness" / "runtime" / "ACTIVE_RUN"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(run_id + "\n", encoding="utf-8")
    assignment_cli = HARNESS_SCRIPTS / "new_assignment.py"
    implementer_args = [
        sys.executable,
        str(assignment_cli),
        "--assignment-id",
        "A-IMPLEMENT",
        "--agent-type",
        "harness_engineer",
        "--task",
        "bounded implementation",
        "--workflow-role",
        "implementer",
        "--risk-tier",
        "R2",
        "--claim-id",
        "C-001",
        "--required-input",
        "input.txt",
        "--allowed-tool",
        "read",
        "--required-output",
        "implementation result",
    ]
    implemented = _run(implementer_args, cwd=repo)
    assert implemented.returncode == 0, implemented.stdout + implemented.stderr
    refused_freeze = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "bind_candidate.py"),
            "--seal",
            seal_rel,
        ],
        cwd=repo,
    )
    assert refused_freeze.returncode != 0
    assert "exactly one result" in refused_freeze.stderr
    args = [
        sys.executable,
        str(assignment_cli),
        "--assignment-id",
        "A-REVIEW",
        "--agent-type",
        "harness_engineer",
        "--task",
        "read-only review",
        "--workflow-role",
        "reviewer",
        "--risk-tier",
        "R2",
        "--claim-id",
        "C-001",
        "--required-input",
        "input.txt",
        "--allowed-tool",
        "read",
        "--required-output",
        "review coverage",
    ]
    refused = _run(args, cwd=repo)
    assert refused.returncode != 0
    assert "frozen candidate" in refused.stderr

    plan["candidate_binding"] = candidate_binding_from_payload(
        seal,
        seal_path=seal_rel,
        seal_file_sha256=bytes_sha256(seal_bytes),
    )
    plan["status"] = "candidate_frozen"
    _write_json(run_dir / "RUN_PLAN.json", plan)
    implementer_assignment = json.loads(
        (run_dir / "assignments/A-IMPLEMENT.json").read_text(encoding="utf-8")
    )
    assert validate_assignment_payload(
        implementer_assignment,
        run_id=run_id,
        context_version=CONTEXT_VERSION,
        assignment_id="A-IMPLEMENT",
        repo=repo,
    ) == []
    accepted = _run(args, cwd=repo)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assignment = json.loads(
        (run_dir / "assignments/A-REVIEW.json").read_text(encoding="utf-8")
    )
    assert assignment["schema_version"] == 3
    assert assignment["workflow_role"] == "reviewer"
    assert assignment["candidate_binding"]["candidate_sha"] == seal["candidate_sha"]

    publisher = _run(
        [
            *args[: args.index("--workflow-role") + 1],
            "publisher",
            *args[args.index("--workflow-role") + 2 :],
        ],
        cwd=repo,
    )
    assert publisher.returncode != 0
    assert "invalid choice" in publisher.stderr


def test_publication_gate_validates_exact_evidence_and_consumes_once(
    tmp_path: Path,
) -> None:
    repo, _ = _make_candidate_repo(tmp_path)
    built = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "build_context_pack.py"),
        ],
        cwd=repo,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    _git(repo, "add", ".agent-harness/context/CONTEXT_INDEX.json")
    _git(repo, "add", ".agent-harness/generated/CONTEXT_PACK.md")
    _git(repo, "commit", "-qm", "build test context")
    run_id = "run-gate"
    initialized = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "init_run.py"),
            "--run-id",
            run_id,
            "--work-unit",
            "PR-247",
            "--change-set",
            CHANGE_SET,
            "--publication-group",
            PUBLICATION_GROUP,
            "--integration-policy",
            POLICY_REL,
            "--target-ref",
            f"origin/{TARGET_BRANCH}",
            "--spec-ref",
            "SPEC.md",
        ],
        cwd=repo,
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr

    seal = _seal(repo)
    seal_rel = ".prguard/runtime/CANDIDATE_SEAL.json"
    write_json_exclusive(repo / seal_rel, seal)
    frozen = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "bind_candidate.py"),
            "--seal",
            seal_rel,
        ],
        cwd=repo,
    )
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    frozen_plan = json.loads(
        (repo / f".agent-harness/runs/{run_id}/RUN_PLAN.json").read_text(
            encoding="utf-8"
        )
    )
    assert frozen_plan["production_hash"] == seal["production_hash"]
    assert frozen_plan["evidence_key"] == {
        "production_hash": seal["production_hash"],
        "dependency_hashes": {},
    }

    assignment_id = "A-REVIEW"
    registered = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "new_assignment.py"),
            "--assignment-id",
            assignment_id,
            "--agent-type",
            "harness_engineer",
            "--task",
            "read-only publication review",
            "--workflow-role",
            "reviewer",
            "--risk-tier",
            "R2",
            "--claim-id",
            "C-001",
            "--required-input",
            "input.txt",
            "--allowed-tool",
            "read",
            "--required-output",
            "review coverage",
        ],
        cwd=repo,
    )
    assert registered.returncode == 0, registered.stdout + registered.stderr
    run_dir = repo / ".agent-harness/runs" / run_id
    assignment = json.loads(
        (run_dir / f"assignments/{assignment_id}.json").read_text(
            encoding="utf-8"
        )
    )
    _, policy = load_publication_policy(repo, POLICY_REL)
    coverage = _coverage(
        repo,
        seal,
        dict(policy),
        run_id=run_id,
        assignment_id=assignment_id,
    )
    coverage_rel = (
        f".agent-harness/runs/{run_id}/artifacts/"
        f"{assignment_id}/REVIEW_COVERAGE.json"
    )
    _write_json(repo / coverage_rel, coverage)
    coverage_data = (repo / coverage_rel).read_bytes()
    oracle = coverage["independent_oracles"][0]
    oracle_data = (repo / oracle["artifact_path"]).read_bytes()
    result_rel = (
        f".agent-harness/runs/{run_id}/results/{assignment_id}.json"
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = {
        "schema_version": 3,
        "run_id": run_id,
        "assignment_id": assignment_id,
        "context_version": assignment["context_version"],
        "agent_type": "harness_engineer",
        "work_unit_id": "PR-247",
        "change_set_id": CHANGE_SET,
        "publication_group_id": PUBLICATION_GROUP,
        "workflow_role": "reviewer",
        "candidate_binding": assignment["candidate_binding"],
        "independence_mode": assignment["independence_mode"],
        "status": "pass",
        "result_path": result_rel,
        "assignment_sha256": assignment["assignment_sha256"],
        "launch_id": None,
        "launch_evidence": "unverified",
        "execution_evidence": "self_declared",
        "files_read": ["input.txt"],
        "files_read_evidence": "self_declared",
        "started_at": now,
        "completed_at": now,
        "tool_versions": {"python": sys.version.split()[0]},
        "commands": [oracle["argv"]],
        "artifacts": [
            {
                "path": coverage_rel,
                "sha256": bytes_sha256(coverage_data),
                "bytes": len(coverage_data),
                "producer": assignment_id,
            },
            {
                "path": oracle["artifact_path"],
                "sha256": bytes_sha256(oracle_data),
                "bytes": len(oracle_data),
                "producer": assignment_id,
                "command_fingerprint": oracle["command_fingerprint"],
            },
        ],
        "review_coverage_path": coverage_rel,
        "review_coverage_sha256": bytes_sha256(coverage_data),
        "findings": [],
        "claim_results": [
            {
                "claim_id": "C-001",
                "outcome": "examined_no_findings",
                "finding_ids": [],
                "summary": "No blocking finding in the disposable candidate.",
                "evidence_refs": [coverage_rel],
            }
        ],
        "errors": [],
    }
    _write_json(repo / result_rel, result)
    validated = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "validate_harness.py"),
        ],
        cwd=repo,
    )
    assert validated.returncode == 0, validated.stdout + validated.stderr

    integration_rel = ".prguard/runtime/INTEGRATION_RECEIPT.json"
    create_receipt(
        repo,
        seal_path=seal_rel,
        output_path=integration_rel,
    )
    inventory = _inventory(seal)
    inventory_path = tmp_path / "PR_INVENTORY.json"
    _write_json(inventory_path, inventory)
    key_path = tmp_path / "publisher.key"
    key_path.write_text(("84" * 32) + "\n", encoding="ascii")
    key_path.chmod(0o600)
    pr_body_path = tmp_path / "PR_BODY.md"
    pr_body_path.write_text(
        f"Change-Set-ID: {CHANGE_SET}\n"
        f"Publication-Group-ID: {PUBLICATION_GROUP}\n",
        encoding="utf-8",
    )
    authorization_path = tmp_path / "PUBLISH_AUTHORIZATION.json"
    issued = _run(
        [
            sys.executable,
            str(HARNESS_SCRIPTS / "publisher_authorization.py"),
            "issue",
            "--key",
            str(key_path),
            "--seal",
            seal_rel,
            "--review-result",
            result_rel,
            "--integration",
            integration_rel,
            "--inventory",
            str(inventory_path),
            "--remote-push-url",
            seal["remote_push_urls"][0],
            "--pr-title",
            "PR-247: enforce publication integrity",
            "--pr-body-file",
            str(pr_body_path),
            "--approved-by",
            "human-reviewer",
            "--ttl-seconds",
            "60",
            "--output",
            str(authorization_path),
        ],
        cwd=repo,
    )
    assert issued.returncode == 0, issued.stdout + issued.stderr

    gate = HARNESS_SCRIPTS / "pr_publication_gate.py"
    common_args = [
        "--seal",
        seal_rel,
        "--review-result",
        result_rel,
        "--integration",
        integration_rel,
        "--inventory",
        str(inventory_path),
        "--authorization",
        str(authorization_path),
        "--publisher-key",
        str(key_path),
    ]
    checked = _run(
        [sys.executable, str(gate), "check", *common_args],
        cwd=repo,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    checked_payload = json.loads(checked.stdout)
    assert checked_payload["gate_state"] == (
        "READY_FOR_EXTERNAL_PUBLISHER"
    )
    assert checked_payload["publication_request"]["head_refspec"].startswith(
        seal["candidate_sha"] + ":"
    )
    assert checked_payload["publication_request"][
        "publication_repository_host"
    ] == seal["publication_repository_host"]
    assert checked_payload["publication_request"][
        "publication_repository_slug"
    ] == seal["publication_repository_slug"]
    assert f"Change-Set-ID: {CHANGE_SET}" in checked_payload[
        "publication_request"
    ]["pr_body"]

    ledger = tmp_path / "nonce-ledger"
    consumed = _run(
        [
            sys.executable,
            str(gate),
            "consume",
            *common_args,
            "--nonce-ledger",
            str(ledger),
        ],
        cwd=repo,
    )
    assert consumed.returncode == 0, consumed.stdout + consumed.stderr
    assert json.loads(consumed.stdout)["gate_state"] == (
        "AUTHORIZED_FOR_IMMEDIATE_EXTERNAL_PUBLISHER_USE"
    )
    replay = _run(
        [
            sys.executable,
            str(gate),
            "consume",
            *common_args,
            "--nonce-ledger",
            str(ledger),
        ],
        cwd=repo,
    )
    assert replay.returncode == 1
    assert "already used" in replay.stdout
