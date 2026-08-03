from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timedelta, timezone
import json
import os
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
    consume_attended_authorization_nonce,
    create_attended_nonce_ledger,
    load_publication_policy,
    validate_authorization_payload,
)


POLICY_REL = "docs/research_program/post_pr275/pr276_publication_policy.json"
CANDIDATE_SHA = "a" * 40
BRANCH = "changeset/pr276-policy-repair"
BASE = "research/pr04-multicomponent"
REPO_SLUG = "owner/repository"


def _ledger_identity(
    path: str = "/tmp/htt-pr276-attended-test-nonce-ledger",
) -> dict[str, object]:
    return {
        "path": path,
        "device": 1,
        "inode": 2,
        "initial_ctime_ns": 3,
        "initial_size": 0,
    }


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
        "nonce_ledger": _ledger_identity(),
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
        "nonce_ledger_binding": "authorization_hmac_frozen_external_inode_v1",
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

    relaxed = copy.deepcopy(policy)
    relaxed["attended_publication"]["nonce_ledger_binding"] = "caller_selected"
    policy_path.write_text(json.dumps(relaxed), encoding="utf-8")
    with pytest.raises(PublicationIntegrityError, match="nonce ledger"):
        load_publication_policy(tmp_path, "policy.json")


def test_attended_authorization_requires_an_opted_in_policy(
    tmp_path: Path,
) -> None:
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
        "nonce_ledger": create_attended_nonce_ledger(
            tmp_path / "nonce-ledger", repo=ROOT
        ),
    }
    authorization["hmac_sha256"] = authorization_hmac(authorization, key=key)
    assert validate_authorization_payload(
        authorization,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=artifact_hashes,
        repo=ROOT,
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
        repo=ROOT,
        now=now,
    )
    assert errors == ["policy does not authorize attended publication"]

    rebound = copy.deepcopy(authorization)
    rebound["nonce_ledger"]["path"] = str(tmp_path / "second-ledger")
    assert validate_authorization_payload(
        rebound,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=artifact_hashes,
        repo=ROOT,
        now=now,
    ) == ["publish authorization HMAC is invalid"]

    inside = copy.deepcopy(authorization)
    inside["nonce_ledger"]["path"] = str(ROOT / ".prguard" / "nonce-ledger")
    inside["hmac_sha256"] = authorization_hmac(inside, key=key)
    assert validate_authorization_payload(
        inside,
        key=key,
        seal=seal,
        policy=policy,
        artifact_hashes=artifact_hashes,
        repo=ROOT,
        now=now,
    ) == ["nonce ledger must be outside the repository"]


def test_attended_publisher_has_no_caller_selected_nonce_ledger_option() -> None:
    completed = subprocess.run(
        [sys.executable, str(Path(attended.__file__)), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "--nonce-ledger" not in completed.stdout


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
                "authorization_file_sha256": "1" * 64,
                "publication_request": request,
            },
            "b" * 48,
        ),
    )
    consumed = False

    def _consume(*args: object, **kwargs: object) -> None:
        nonlocal consumed
        consumed = True

    monkeypatch.setattr(attended, "consume_attended_authorization_nonce", _consume)
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
                "authorization_file_sha256": "2" * 64,
                "publication_request": request,
            },
            "c" * 48,
        ),
    )
    consumed: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        attended,
        "consume_attended_authorization_nonce",
        lambda nonce, **kwargs: consumed.append(
            (nonce, dict(kwargs["ledger_identity"]))
        ),
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
    assert consumed == [("c" * 48, dict(request["nonce_ledger"]))]
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
    assert receipt["authorization_file_sha256"] == "2" * 64
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
                "authorization_file_sha256": "3" * 64,
                "publication_request": request,
            },
            "d" * 48,
        ),
    )
    monkeypatch.setattr(
        attended, "consume_attended_authorization_nonce", lambda *a, **k: None
    )
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


def test_attended_publisher_replay_uses_one_authorization_bound_ledger(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request()
    request["nonce_ledger"] = create_attended_nonce_ledger(
        tmp_path / "bound-nonce-ledger", repo=ROOT
    )
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
                "authorization_file_sha256": "4" * 64,
                "publication_request": request,
            },
            "e" * 48,
        ),
    )
    remote_checks: list[str] = []

    def _remote(*args: object, **kwargs: object) -> str:
        remote_checks.append("checked")
        return CANDIDATE_SHA

    monkeypatch.setattr(attended, "_remote_head", _remote)
    monkeypatch.setattr(attended, "_open_prs", lambda *a, **k: [_verified_pr()])
    receipts: list[dict[str, object]] = []
    monkeypatch.setattr(
        attended,
        "_write_receipt",
        lambda repo, output, receipt: receipts.append(dict(receipt)),
    )

    first = _args(tmp_path)
    first.receipt_output = str(tmp_path / "first-receipt.json")
    assert attended._publish(first, ROOT)["status"] == "PASS"

    second = _args(tmp_path)
    second.receipt_output = str(tmp_path / "second-receipt.json")
    with pytest.raises(PublicationIntegrityError, match="already used"):
        attended._publish(second, ROOT)

    assert remote_checks == ["checked", "checked"]
    assert [row["status"] for row in receipts] == ["PASS", "FAIL"]

    ledger_path = Path(str(request["nonce_ledger"]["path"]))
    ledger_path.unlink()
    fd = os.open(ledger_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    third = _args(tmp_path)
    third.receipt_output = str(tmp_path / "third-receipt.json")
    with pytest.raises(
        PublicationIntegrityError,
        match="inode differs|reset after authorization",
    ):
        attended._publish(third, ROOT)
    assert remote_checks == ["checked", "checked"]
    assert [row["status"] for row in receipts] == ["PASS", "FAIL", "FAIL"]


def test_attended_nonce_ledger_rejects_reset_and_serializes_concurrency(
    tmp_path: Path,
) -> None:
    concurrent_identity = create_attended_nonce_ledger(
        tmp_path / "concurrent-ledger", repo=ROOT
    )

    def _consume() -> str:
        try:
            consume_attended_authorization_nonce(
                "f" * 48,
                ledger_identity=concurrent_identity,
                repo=ROOT,
            )
        except PublicationIntegrityError as exc:
            return str(exc)
        return "PASS"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: _consume(), range(2)))
    assert sorted(outcomes) == ["PASS", "publish authorization nonce was already used"]

    reset_identity = create_attended_nonce_ledger(
        tmp_path / "reset-ledger", repo=ROOT
    )
    reset_path = Path(str(reset_identity["path"]))
    reset_path.write_text("transient\n", encoding="ascii")
    reset_path.write_text("", encoding="ascii")
    with pytest.raises(PublicationIntegrityError, match="reset after authorization"):
        consume_attended_authorization_nonce(
            "1" * 48,
            ledger_identity=reset_identity,
            repo=ROOT,
        )
