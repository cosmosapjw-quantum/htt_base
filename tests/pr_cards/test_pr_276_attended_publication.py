from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / ".agent-harness" / "scripts"
sys.path.insert(0, str(HARNESS))

import attended_pr_publisher as attended  # noqa: E402
from publication_integrity import (  # noqa: E402
    ATTENDED_PUBLISHER_AUTHORIZATION_MODE,
    ATTENDED_PUBLICATION_TRANSACTION,
    PublicationIntegrityError,
    authorization_hmac,
    classify_publication_command,
    load_publication_policy,
    validate_authorization_payload,
)


POLICY_REL = "docs/research_program/post_pr275/pr276_publication_policy.json"
CANDIDATE_SHA = "a" * 40
BRANCH = "changeset/pr276-policy-repair"
BASE = "research/pr04-multicomponent"
REPO_SLUG = "owner/repository"


def _request() -> dict[str, object]:
    return {
        "authorization_mode": ATTENDED_PUBLISHER_AUTHORIZATION_MODE,
        "publication_repository_slug": REPO_SLUG,
        "remote_push_url": "https://github.com/owner/repository.git",
        "head_refspec": f"{CANDIDATE_SHA}:refs/heads/{BRANCH}",
        "pr_title": "PR-276: repair attended publication",
        "pr_body": (
            "Change-Set-ID: CS-PR276-POST275-RECONCILIATION\n"
            "Publication-Group-ID: PG-PR276-POST275-RECONCILIATION\n"
        ),
        "pr_base_branch": BASE,
        "pr_head_branch": BRANCH,
        "pr_draft": False,
    }


def _verified_pr() -> dict[str, object]:
    request = _request()
    return {
        "number": 376,
        "url": "https://github.com/owner/repository/pull/376",
        "headRefOid": CANDIDATE_SHA,
        "headRefName": BRANCH,
        "baseRefName": BASE,
        "title": request["pr_title"],
        "body": request["pr_body"],
        "isDraft": False,
    }


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        seal="seal.json",
        review_result="review.json",
        integration="integration.json",
        inventory=str(tmp_path / "inventory.json"),
        authorization=str(tmp_path / "authorization.json"),
        publisher_key=str(tmp_path / "publisher.key"),
        nonce_ledger=str(tmp_path / "nonce-ledger"),
        receipt_output=str(tmp_path / "receipt.json"),
    )


def test_pr276_policy_registers_only_the_narrow_attended_transaction() -> None:
    _, policy = load_publication_policy(ROOT, POLICY_REL)
    lane = policy["attended_publication"]
    assert lane == {
        "enabled": True,
        "authorization_mode": ATTENDED_PUBLISHER_AUTHORIZATION_MODE,
        "transaction": ATTENDED_PUBLICATION_TRANSACTION,
        "max_transactions": 1,
        "requires_current_turn_authorization": True,
        "direct_mutation_commands_forbidden": True,
        "publisher_entrypoint": ".agent-harness/scripts/attended_pr_publisher.py",
        "forbidden_actions": [
            "force_push",
            "approve",
            "merge",
            "ruleset_mutation",
        ],
    }
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["default_publication_mode"] == (
        "unattended_external_publisher_only"
    )
    assert policy["unattended_publication_requires_external_publisher"] is True

    assert classify_publication_command("git push origin HEAD")[0] is True
    assert classify_publication_command("gh pr create --fill")[0] is True
    wrapper = (
        "python .agent-harness/scripts/attended_pr_publisher.py "
        "--seal seal.json"
    )
    assert classify_publication_command(wrapper) == (False, "")


def test_attended_policy_schema_fails_closed_on_relaxation(tmp_path: Path) -> None:
    policy = json.loads((ROOT / POLICY_REL).read_text(encoding="utf-8"))
    entrypoint = tmp_path / ".agent-harness/scripts/attended_pr_publisher.py"
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text("# test entrypoint\n", encoding="utf-8")
    policy_path = tmp_path / "policy.json"

    relaxed = copy.deepcopy(policy)
    relaxed["attended_publication"]["max_transactions"] = 2
    policy_path.write_text(json.dumps(relaxed), encoding="utf-8")
    with pytest.raises(PublicationIntegrityError, match="max_transactions"):
        load_publication_policy(tmp_path, "policy.json")

    relaxed = copy.deepcopy(policy)
    relaxed["attended_publication"]["direct_mutation_commands_forbidden"] = False
    policy_path.write_text(json.dumps(relaxed), encoding="utf-8")
    with pytest.raises(PublicationIntegrityError, match="direct mutation"):
        load_publication_policy(tmp_path, "policy.json")

    relaxed = copy.deepcopy(policy)
    relaxed["attended_publication"]["forbidden_actions"].remove("merge")
    policy_path.write_text(json.dumps(relaxed), encoding="utf-8")
    with pytest.raises(PublicationIntegrityError, match="forbidden action"):
        load_publication_policy(tmp_path, "policy.json")


def test_attended_authorization_requires_an_opted_in_policy() -> None:
    _, policy = load_publication_policy(ROOT, POLICY_REL)
    key = bytes.fromhex("84" * 32)
    seal = {
        "change_set_id": "CS-PR276-POST275-RECONCILIATION",
        "publication_group_id": "PG-PR276-POST275-RECONCILIATION",
        "target_remote": "origin",
        "target_branch": BASE,
        "publication_repository_host": "github.com",
        "publication_repository_slug": REPO_SLUG,
        "candidate_branch": BRANCH,
        "candidate_sha": CANDIDATE_SHA,
        "seal_sha256": "f" * 64,
        "remote_push_urls": ["https://github.com/owner/repository.git"],
    }
    artifact_hashes = {
        "candidate_seal_file_sha256": "1" * 64,
        "review_result_file_sha256": "2" * 64,
        "integration_receipt_file_sha256": "3" * 64,
        "pr_inventory_file_sha256": "4" * 64,
    }
    now = datetime.now(timezone.utc).replace(microsecond=0)
    authorization = {
        "schema_version": 1,
        "authorization_mode": ATTENDED_PUBLISHER_AUTHORIZATION_MODE,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "target_remote": seal["target_remote"],
        "target_branch": seal["target_branch"],
        "publication_repository_host": seal["publication_repository_host"],
        "publication_repository_slug": seal["publication_repository_slug"],
        "remote_push_url": seal["remote_push_urls"][0],
        "candidate_branch": BRANCH,
        "candidate_sha": CANDIDATE_SHA,
        "candidate_seal_sha256": seal["seal_sha256"],
        "head_refspec": f"{CANDIDATE_SHA}:refs/heads/{BRANCH}",
        "pr_title": "PR-276: repair attended publication",
        "pr_body": (
            "Change-Set-ID: CS-PR276-POST275-RECONCILIATION\n"
            "Publication-Group-ID: PG-PR276-POST275-RECONCILIATION\n"
        ),
        "pr_base_branch": BASE,
        "pr_head_branch": BRANCH,
        "pr_draft": False,
        "artifact_hashes": artifact_hashes,
        "approved_by": "user-current-turn-2026-08-03",
        "issued_at": now.isoformat(timespec="seconds"),
        "expires_at": (now + timedelta(minutes=5)).isoformat(timespec="seconds"),
        "nonce": "5" * 48,
    }
    authorization["hmac_sha256"] = authorization_hmac(authorization, key=key)
    assert validate_authorization_payload(
        authorization,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=artifact_hashes,
        now=now,
    ) == []

    no_attended_lane = dict(policy)
    no_attended_lane.pop("attended_publication")
    errors = validate_authorization_payload(
        authorization,
        key=key,
        seal=seal,
        policy=no_attended_lane,
        artifact_hashes=artifact_hashes,
        now=now,
    )
    assert errors == ["policy does not authorize attended publication"]


def test_attended_publisher_rejects_external_authorization_before_nonce_use(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        attended,
        "_policy_for_seal",
        lambda repo, seal: {
            "attended_publication": {
                "enabled": True,
                "transaction": ATTENDED_PUBLICATION_TRANSACTION,
            }
        },
    )
    request = _request()
    request["authorization_mode"] = "external_publisher"
    monkeypatch.setattr(
        attended,
        "evaluate_gate",
        lambda args, repo: (
            {
                "ok": True,
                "candidate_sha": CANDIDATE_SHA,
                "publication_request": request,
            },
            "b" * 48,
        ),
    )
    consumed = False

    def _consume(*args: object, **kwargs: object) -> None:
        nonlocal consumed
        consumed = True

    monkeypatch.setattr(attended, "consume_authorization_nonce", _consume)
    with pytest.raises(PublicationIntegrityError, match="attended_explicit_user"):
        attended._publish(_args(tmp_path), ROOT)
    assert consumed is False


def test_attended_publisher_refuses_used_receipt_path_before_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args = _args(tmp_path)
    Path(args.receipt_output).write_text("occupied\n", encoding="utf-8")
    gate_called = False

    def _gate(*values: object, **kwargs: object) -> tuple[dict, str]:
        nonlocal gate_called
        gate_called = True
        return {}, ""

    monkeypatch.setattr(attended, "evaluate_gate", _gate)
    with pytest.raises(PublicationIntegrityError, match="path must be unused"):
        attended._publish(args, ROOT)
    assert gate_called is False


def test_attended_publisher_executes_exact_transaction_and_records_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request()
    monkeypatch.setattr(
        attended,
        "_policy_for_seal",
        lambda repo, seal: {
            "attended_publication": {
                "enabled": True,
                "transaction": ATTENDED_PUBLICATION_TRANSACTION,
            }
        },
    )
    monkeypatch.setattr(
        attended,
        "evaluate_gate",
        lambda args, repo: (
            {
                "ok": True,
                "candidate_sha": CANDIDATE_SHA,
                "publication_request": request,
            },
            "c" * 48,
        ),
    )
    monkeypatch.setattr(
        attended,
        "read_external_json",
        lambda repo, path, field: (
            Path(path),
            b"authorization-bytes",
            {"authorization_mode": ATTENDED_PUBLISHER_AUTHORIZATION_MODE},
        ),
    )
    consumed: list[str] = []
    monkeypatch.setattr(
        attended,
        "consume_authorization_nonce",
        lambda nonce, **kwargs: consumed.append(nonce),
    )

    remote_heads = iter((None, CANDIDATE_SHA))
    monkeypatch.setattr(
        attended,
        "_remote_head",
        lambda repo, **kwargs: next(remote_heads),
    )
    pr_rows = iter(([], [_verified_pr()]))
    monkeypatch.setattr(
        attended,
        "_open_prs",
        lambda repo, **kwargs: next(pr_rows),
    )
    commands: list[list[str]] = []

    def _run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(attended, "_run", _run)
    receipts: list[dict[str, object]] = []
    monkeypatch.setattr(
        attended,
        "_write_receipt",
        lambda repo, output, receipt: receipts.append(dict(receipt)),
    )

    receipt = attended._publish(_args(tmp_path), ROOT)
    assert consumed == ["c" * 48]
    assert commands[0] == [
        "git",
        "push",
        request["remote_push_url"],
        request["head_refspec"],
    ]
    assert commands[1][:4] == ["gh", "pr", "create", "--repo"]
    assert not ({"--force", "--approve", "--merge"} & set(commands[0] + commands[1]))
    assert receipt["status"] == "PASS"
    assert receipt["branch_pushed"] is True
    assert receipt["pr_created"] is True
    assert receipt["pr_number"] == 376
    assert receipts == [receipt]


def test_attended_publisher_blocks_mismatched_remote_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request()
    monkeypatch.setattr(
        attended,
        "_policy_for_seal",
        lambda repo, seal: {
            "attended_publication": {
                "enabled": True,
                "transaction": ATTENDED_PUBLICATION_TRANSACTION,
            }
        },
    )
    monkeypatch.setattr(
        attended,
        "evaluate_gate",
        lambda args, repo: (
            {
                "ok": True,
                "candidate_sha": CANDIDATE_SHA,
                "publication_request": request,
            },
            "d" * 48,
        ),
    )
    monkeypatch.setattr(
        attended,
        "read_external_json",
        lambda repo, path, field: (
            Path(path),
            b"authorization-bytes",
            {"authorization_mode": ATTENDED_PUBLISHER_AUTHORIZATION_MODE},
        ),
    )
    monkeypatch.setattr(attended, "consume_authorization_nonce", lambda *a, **k: None)
    monkeypatch.setattr(attended, "_remote_head", lambda repo, **kwargs: "e" * 40)
    commands: list[list[str]] = []
    monkeypatch.setattr(
        attended,
        "_run",
        lambda argv, **kwargs: commands.append(list(argv)),
    )
    receipts: list[dict[str, object]] = []
    monkeypatch.setattr(
        attended,
        "_write_receipt",
        lambda repo, output, receipt: receipts.append(dict(receipt)),
    )

    with pytest.raises(PublicationIntegrityError, match="different SHA"):
        attended._publish(_args(tmp_path), ROOT)
    assert commands == []
    assert receipts[0]["status"] == "FAIL"
