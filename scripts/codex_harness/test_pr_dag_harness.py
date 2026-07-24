from __future__ import annotations

import hashlib
import hmac
import json
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "codex_harness" / "validate_pr_dag.py"
PROGRESS = REPO_ROOT / "scripts" / "codex_harness" / "progress_report.py"
HARNESS_ROOT = PROGRESS.parent
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

import progress_report as progress_module  # noqa: E402
from common.remediation_state import (  # noqa: E402
    AdjudicatedClaim,
    AdjudicationReceipt,
    AuthorityRegistry,
    ExternalDeliveryReceipt,
    PrincipalRecord,
)


AT = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
_VERIFIER_KEYS = {
    "principal:adjudicator": b"progress-test-adjudicator-key",
    "principal:external-provider": b"progress-test-provider-key",
}


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _backlog_with_policy(order: list[str]) -> dict:
    return {
        "policy": {"topological_order": order},
        "prs": [
            {
                "id": "PR-000",
                "wave": 0,
                "title": "Root",
                "owner": "COMMON",
                "depends": [],
            },
            {
                "id": "PR-001",
                "wave": 0,
                "title": "Packaging",
                "owner": "COMMON",
                "depends": ["PR-000"],
            },
            {
                "id": "PR-002",
                "wave": 0,
                "title": "Taxonomy",
                "owner": "COMMON",
                "depends": ["PR-001"],
            },
            {
                "id": "PR-003",
                "wave": 0,
                "title": "DAG harness",
                "owner": "COMMON",
                "depends": ["PR-000"],
            },
        ],
    }


def test_validate_rejects_policy_order_that_violates_dependency(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-003", "PR-001", "PR-000", "PR-002"]))

    completed = _run(str(VALIDATOR), str(backlog))

    assert completed.returncode != 0
    assert "policy.topological_order" in completed.stderr


def test_validate_rejects_non_mapping_policy(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    payload = _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"])
    payload["policy"] = []
    _write_yaml(backlog, payload)

    completed = _run(str(VALIDATOR), str(backlog))

    assert completed.returncode != 0
    assert "policy must be a mapping" in completed.stderr


def test_validate_can_write_mermaid_graph_from_backlog(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    graph = tmp_path / "pr_dag.mmd"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))

    completed = _run(str(VALIDATOR), str(backlog), "--write-mermaid", str(graph))

    assert completed.returncode == 0, completed.stderr
    rendered = graph.read_text(encoding="utf-8")
    assert rendered.startswith("flowchart TD\n")
    assert 'PR_000["PR-000<br/>Root"]' in rendered
    assert "PR_000 --> PR_003" in rendered


def test_progress_report_orders_unblocked_by_policy_and_reports_weighted_metrics(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-000", "PR-001"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["unblocked_next"] == ["PR-003", "PR-002"]
    assert payload["critical_path_percent_complete"] == 66.67
    assert "dependency_weighted_percent_complete" in payload
    assert payload["critical_path"] == ["PR-000", "PR-001", "PR-002"]


def test_progress_report_rejects_unknown_status_ids(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-999"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert "unknown completed PR ids" in completed.stderr


def test_progress_report_rejects_completed_skipped_overlap(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-000"], "skipped": ["PR-000"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert "both completed and skipped" in completed.stderr


def test_progress_report_tracks_skipped_without_counting_completion(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-000"], "skipped": ["PR-001"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["completed"] == 1
    assert payload["skipped"] == ["PR-001"]
    assert payload["skipped_count"] == 1
    assert "PR-001" not in payload["unblocked_next"]
    assert "PR-002" not in payload["unblocked_next"]


def test_progress_report_handles_empty_backlog(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, {"prs": []})
    _write_yaml(status, {"completed": [], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["total"] == 0
    assert payload["percent_complete"] == 0.0
    assert payload["critical_path"] == []
    assert payload["critical_path_percent_complete"] == 0.0


def test_progress_report_writes_scoreboard_when_checkpoint_not_due(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    scoreboard = tmp_path / "progress_scoreboard.md"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(
        status,
        {
            "completed": [f"PR-{index:03d}" for index in range(4)],
            "skipped": ["PR-004"],
            "blocked": [],
        },
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-scoreboard",
        str(scoreboard),
    )

    assert completed.returncode == 0, completed.stderr
    rendered = scoreboard.read_text(encoding="utf-8")
    assert "Completed PRs: 4/5 = 80.0%" in rendered
    assert "Skipped PRs: PR-004" in rendered
    assert "Checkpoint due: no" in rendered
    assert "not scientific readiness evidence" in rendered
    for field in (
        "Owner:",
        "Implementation scope:",
        "Claim tier:",
        "Transfer source:",
        "Config hash:",
        "Input hashes:",
        "Sky support / mask status:",
        "Covariance / null mock status:",
        "Caveats:",
        "Generating command:",
        "Git commit / worktree state:",
    ):
        assert field in rendered


def _linear_backlog(count: int) -> dict:
    ids = [f"PR-{index:03d}" for index in range(count)]
    return {
        "policy": {"topological_order": ids},
        "prs": [
            {
                "id": pr_id,
                "wave": 0,
                "title": f"Step {index}",
                "owner": "COMMON",
                "depends": [] if index == 0 else [ids[index - 1]],
            }
            for index, pr_id in enumerate(ids)
        ],
    }


def _typed_backlog(*cards: dict) -> dict:
    return {
        "policy": {"topological_order": [card["id"] for card in cards]},
        "prs": list(cards),
    }


def _typed_card(
    pr_id: str,
    *,
    depends: list[str] | None = None,
    mode: str = "requires_success",
    external_event: str | None = None,
) -> dict:
    dependencies = depends or []
    card = {
        "id": pr_id,
        "wave": 13,
        "title": f"Typed {pr_id}",
        "owner": "COMMON",
        "depends": dependencies,
        "dependency_contracts": [
            {"upstream_id": dependency, "mode": mode}
            for dependency in dependencies
        ],
    }
    if external_event is not None:
        card["external_dependency_contracts"] = [
            {
                "upstream_id": external_event,
                "mode": "requires_authenticated_external_receipt",
                "scope": "native_low_ell_delivery",
            }
        ]
    return card


def _resolution(resolution: str, **extra: object) -> dict:
    return {
        "resolution": resolution,
        "receipt": "docs/PR_DELTAS/test-receipt.md",
        **extra,
    }


def _test_verifier(
    principal: PrincipalRecord,
    payload: bytes,
    attestation: str,
) -> bool:
    key = _VERIFIER_KEYS.get(principal.principal_id)
    if key is None:
        return False
    expected = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, attestation)


def _verifiers() -> dict[
    str, Callable[[PrincipalRecord, bytes, str], bool]
]:
    return {"test_hmac_sha256": _test_verifier}


def _principal(
    principal_id: str,
    fingerprint_character: str,
    *,
    roles: tuple[str, ...],
    scopes: tuple[str, ...],
    independence_class: str,
    valid_from: str = "2026-01-01T00:00:00+00:00",
    valid_until: str = "2027-01-01T00:00:00+00:00",
    revoked: bool = False,
) -> PrincipalRecord:
    return PrincipalRecord(
        principal_id=principal_id,
        identity_fingerprint=fingerprint_character * 64,
        aliases=(),
        allowed_roles=roles,
        allowed_scopes=scopes,
        independence_class=independence_class,
        valid_from=valid_from,
        valid_until=valid_until,
        revoked=revoked,
        verifier="test_hmac_sha256",
    )


def _trusted_registry(
    *,
    adjudication_scope: str = "PR-157",
    provider_scope: str = "native_low_ell_delivery",
    provider_independence: str = "independent_external",
    provider_valid_until: str = "2027-01-01T00:00:00+00:00",
    provider_revoked: bool = False,
) -> AuthorityRegistry:
    return AuthorityRegistry(
        (
            _principal(
                "principal:author",
                "a",
                roles=("author",),
                scopes=(adjudication_scope,),
                independence_class="correlated_internal_author",
            ),
            _principal(
                "principal:adjudicator",
                "b",
                roles=("adjudicator", "scientific_status_promoter"),
                scopes=(adjudication_scope,),
                independence_class="independent_external",
            ),
            _principal(
                "principal:external-provider",
                "c",
                roles=("external_receipt_provider",),
                scopes=(provider_scope,),
                independence_class=provider_independence,
                valid_until=provider_valid_until,
                revoked=provider_revoked,
            ),
        ),
        verifiers=_verifiers(),
    )


def _signed_adjudication_record(
    *, scope: str, empty_claim_set: bool = False
) -> dict[str, object]:
    claims = () if empty_claim_set else (
        AdjudicatedClaim(
            claim_id="finding:test",
            identity_fingerprint="e" * 64,
            scientific_status="BLOCKED",
        ),
    )
    draft = AdjudicationReceipt(
        receipt_id=f"adjudication:{scope}",
        author="principal:author",
        author_identity_fingerprint="a" * 64,
        adjudicator="principal:adjudicator",
        adjudicator_identity_fingerprint="b" * 64,
        scope=scope,
        accepted_claims=claims,
        issued_at=AT,
        attestation="unsigned",
    )
    signature = hmac.new(
        _VERIFIER_KEYS["principal:adjudicator"],
        draft.canonical_attestation_payload(),
        hashlib.sha256,
    ).hexdigest()
    receipt = replace(draft, attestation=signature)
    return {
        "receipt_id": receipt.receipt_id,
        "author": receipt.author,
        "author_identity_fingerprint": receipt.author_identity_fingerprint,
        "adjudicator": receipt.adjudicator,
        "adjudicator_identity_fingerprint": (
            receipt.adjudicator_identity_fingerprint
        ),
        "scope": receipt.scope,
        "accepted_claims": [
            {
                "claim_id": claim.claim_id,
                "identity_fingerprint": claim.identity_fingerprint,
                "scientific_status": claim.scientific_status.value,
            }
            for claim in receipt.accepted_claims
        ],
        "issued_at": receipt.issued_at.isoformat(),
        "attestation": receipt.attestation,
    }


def _signed_external_record(
    *,
    scope: str = "native_low_ell_delivery",
    provider: str = "principal:external-provider",
    forged: bool = False,
) -> dict[str, object]:
    draft = ExternalDeliveryReceipt(
        receipt_id="external:native-lowell:delivery-001",
        provider=provider,
        provider_identity_fingerprint="c" * 64,
        scope=scope,
        artifact_fingerprint="d" * 64,
        issued_at=AT,
        attestation="unsigned",
    )
    signature = hmac.new(
        _VERIFIER_KEYS["principal:external-provider"],
        draft.canonical_attestation_payload(),
        hashlib.sha256,
    ).hexdigest()
    receipt = replace(
        draft,
        attestation="0" * 64 if forged else signature,
    )
    return {
        "receipt_id": receipt.receipt_id,
        "provider": receipt.provider,
        "provider_identity_fingerprint": receipt.provider_identity_fingerprint,
        "scope": receipt.scope,
        "artifact_fingerprint": receipt.artifact_fingerprint,
        "issued_at": receipt.issued_at.isoformat(),
        "attestation": receipt.attestation,
    }


def _write_json_receipt(
    root: Path,
    name: str,
    payload: dict[str, object],
) -> dict[str, str]:
    path = root / name
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    path.write_text(rendered, encoding="utf-8")
    return {
        "path": name,
        "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
    }


def _direct_unblocked(
    backlog: dict,
    status: dict,
    context: progress_module.ReceiptVerificationContext,
) -> list[str]:
    info = progress_module.validate_backlog(backlog)
    completed, blocked, skipped = progress_module.validate_status(
        status,
        info,
        verification_context=context,
    )
    report = progress_module.build_report(
        info,
        completed,
        blocked,
        skipped,
        5,
        status=status,
        verification_context=context,
    )
    return report["unblocked_next"]


def test_progress_report_requires_full_disjoint_pr119_plus_status_coverage(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(
        backlog,
        _typed_backlog(
            _typed_card("PR-118"),
            _typed_card("PR-119", depends=["PR-118"]),
            _typed_card("PR-120", depends=["PR-119"]),
        ),
    )
    _write_yaml(
        status,
        {
            "completed": ["PR-118", "PR-119"],
            "blocked": [],
            "pending": [],
            "dormant_external": [],
            "execution_resolutions": {
                "PR-119": _resolution("COMPLETED_SUCCESS")
            },
            "external_events": {},
        },
    )

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert "coverage missing PR-119+ ids" in completed.stderr
    assert "PR-120" in completed.stderr


def test_progress_report_uses_success_receipt_for_typed_unblocking(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(
        backlog,
        _typed_backlog(
            _typed_card("PR-118"),
            _typed_card("PR-119", depends=["PR-118"]),
            _typed_card("PR-120", depends=["PR-119"]),
        ),
    )
    base_status = {
        "completed": ["PR-118", "PR-119"],
        "blocked": [],
        "pending": ["PR-120"],
        "dormant_external": [],
        "execution_resolutions": {
            "PR-119": _resolution("COMPLETED_SUCCESS")
        },
        "external_events": {},
    }
    _write_yaml(status, base_status)

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["unblocked_next"] == ["PR-120"]
    assert payload["execution_resolved_count"] == 1
    assert payload["dormant_external_count"] == 0

    base_status["execution_resolutions"]["PR-119"] = _resolution(
        "COMPLETED_FAILED_WITH_RECEIPT"
    )
    _write_yaml(status, base_status)
    failed = _run(str(PROGRESS), str(backlog), str(status), "--json")
    assert failed.returncode != 0
    assert "must have COMPLETED_SUCCESS" in failed.stderr


def test_progress_report_rejects_truthy_flag_as_terminal_receipt(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _typed_backlog(_typed_card("PR-119")))
    _write_yaml(
        status,
        {
            "completed": ["PR-119"],
            "blocked": [],
            "pending": [],
            "dormant_external": [],
            "execution_resolutions": {
                "PR-119": {"resolution": "COMPLETED_SUCCESS", "receipt": True}
            },
            "external_events": {},
        },
    )

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert "lacks a valid receipt" in completed.stderr


def test_progress_and_strict_validator_reject_the_same_structured_process_receipt(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    canonical_backlog = yaml.safe_load(
        (REPO_ROOT / "docs/codex_handoff/pr_backlog.yaml").read_text(
            encoding="utf-8"
        )
    )
    canonical_status = yaml.safe_load(
        (REPO_ROOT / "docs/codex_handoff/pr_status.yaml").read_text(
            encoding="utf-8"
        )
    )
    canonical_status["execution_resolutions"]["PR-119"]["receipt"] = {
        "path": "docs/PR_DELTAS/pr-119.md",
        "sha256": "a" * 64,
    }
    _write_yaml(backlog, canonical_backlog)
    _write_yaml(status, canonical_status)

    progress = _run(str(PROGRESS), str(backlog), str(status), "--json")
    strict = _run(
        str(VALIDATOR),
        str(backlog),
        "--status",
        str(status),
        "--strict-rescue-slice",
    )

    assert progress.returncode != 0
    assert "lacks a valid receipt" in progress.stderr
    assert strict.returncode != 0
    assert "receipt pointer must be nonempty" in strict.stderr


@pytest.mark.parametrize(
    ("terminal_state", "expected_error"),
    [
        ("blocked", "must have a documented negative resolution"),
        ("skipped", "must have ABANDONED_WITH_RECEIPT resolution"),
    ],
)
def test_noncompleted_terminal_state_rejects_success_resolution(
    tmp_path: Path,
    terminal_state: str,
    expected_error: str,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _typed_backlog(_typed_card("PR-119")))
    payload = {
        "completed": [],
        "blocked": [],
        "skipped": [],
        "pending": [],
        "dormant_external": [],
        "execution_resolutions": {
            "PR-119": _resolution("COMPLETED_SUCCESS")
        },
        "external_events": {},
    }
    payload[terminal_state] = ["PR-119"]
    _write_yaml(status, payload)

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert expected_error in completed.stderr


@pytest.mark.parametrize(
    ("terminal_state", "resolution", "expected_error"),
    [
        ("blocked", "ABANDONED_WITH_RECEIPT", "documented negative"),
        ("skipped", "BLOCKED_WITH_RECEIPT", "ABANDONED_WITH_RECEIPT"),
    ],
)
def test_terminal_bucket_rejects_a_different_negative_resolution(
    tmp_path: Path,
    terminal_state: str,
    resolution: str,
    expected_error: str,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _typed_backlog(_typed_card("PR-119")))
    payload = {
        "completed": [],
        "blocked": [],
        "skipped": [],
        "pending": [],
        "dormant_external": [],
        "execution_resolutions": {"PR-119": _resolution(resolution)},
        "external_events": {},
    }
    payload[terminal_state] = ["PR-119"]
    _write_yaml(status, payload)

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert expected_error in completed.stderr


def test_terminal_receipt_closes_only_explicit_terminal_edge(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(
        backlog,
        _typed_backlog(
            _typed_card("PR-143"),
            _typed_card(
                "PR-157",
                depends=["PR-143"],
                mode="requires_terminal_receipt",
            ),
        ),
    )
    _write_yaml(
        status,
        {
            "completed": [],
            "blocked": ["PR-143"],
            "pending": ["PR-157"],
            "dormant_external": [],
            "execution_resolutions": {
                "PR-143": _resolution("BLOCKED_WITH_RECEIPT")
            },
            "external_events": {},
        },
    )

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["unblocked_next"] == ["PR-157"]
    assert payload["completed"] == 0


def test_cli_adjudicated_edge_never_unlocks_from_shape_only_record(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(
        backlog,
        _typed_backlog(
            _typed_card("PR-157"),
            _typed_card(
                "PR-158",
                depends=["PR-157"],
                mode="requires_adjudicated_claim_set",
            ),
        ),
    )
    status_payload = {
        "completed": ["PR-157"],
        "blocked": [],
        "pending": ["PR-158"],
        "dormant_external": [],
        "execution_resolutions": {
            "PR-157": _resolution(
                "COMPLETED_SUCCESS", adjudication={"authorized": True}
            )
        },
        "external_events": {},
    }
    _write_yaml(status, status_payload)

    unverified = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert unverified.returncode == 0, unverified.stderr
    assert json.loads(unverified.stdout)["unblocked_next"] == []

    status_payload["execution_resolutions"]["PR-157"] = _resolution(
        "COMPLETED_SUCCESS",
        adjudication={
            "receipt": {
                "path": "docs/adjudications/test.json",
                "sha256": "d" * 64,
            }
        },
    )
    _write_yaml(status, status_payload)
    still_unverified = _run(str(PROGRESS), str(backlog), str(status), "--json")
    assert still_unverified.returncode == 0, still_unverified.stderr
    assert json.loads(still_unverified.stdout)["unblocked_next"] == []


@pytest.mark.parametrize(
    ("upstream_id", "downstream_id"),
    [("PR-157", "PR-158"), ("PR-165", "PR-166")],
)
def test_typed_adjudication_api_unlocks_only_hash_bound_attested_receipt(
    tmp_path: Path,
    upstream_id: str,
    downstream_id: str,
) -> None:
    pointer = _write_json_receipt(
        tmp_path,
        "adjudication.json",
        _signed_adjudication_record(scope=upstream_id),
    )
    backlog = _typed_backlog(
        _typed_card(upstream_id),
        _typed_card(
            downstream_id,
            depends=[upstream_id],
            mode="requires_adjudicated_claim_set",
        ),
    )
    status = {
        "completed": [upstream_id],
        "blocked": [],
        "pending": [downstream_id],
        "dormant_external": [],
        "execution_resolutions": {
            upstream_id: _resolution(
                "COMPLETED_SUCCESS",
                adjudication={"receipt": pointer},
            )
        },
        "external_events": {},
    }
    context = progress_module.ReceiptVerificationContext(
        registry=_trusted_registry(adjudication_scope=upstream_id),
        receipt_root=tmp_path,
        at=AT,
    )

    assert _direct_unblocked(backlog, status, context) == [downstream_id]

    status["execution_resolutions"][upstream_id]["adjudication"] = {
        "receipt": {**pointer, "sha256": "0" * 64}
    }
    assert _direct_unblocked(backlog, status, context) == []


def test_typed_adjudication_api_rejects_an_attested_empty_claim_set(
    tmp_path: Path,
) -> None:
    pointer = _write_json_receipt(
        tmp_path,
        "empty-adjudication.json",
        _signed_adjudication_record(scope="PR-157", empty_claim_set=True),
    )
    backlog = _typed_backlog(
        _typed_card("PR-157"),
        _typed_card(
            "PR-158",
            depends=["PR-157"],
            mode="requires_adjudicated_claim_set",
        ),
    )
    status = {
        "completed": ["PR-157"],
        "blocked": [],
        "pending": ["PR-158"],
        "dormant_external": [],
        "execution_resolutions": {
            "PR-157": _resolution(
                "COMPLETED_SUCCESS",
                adjudication={"receipt": pointer},
            )
        },
        "external_events": {},
    }
    context = progress_module.ReceiptVerificationContext(
        registry=_trusted_registry(adjudication_scope="PR-157"),
        receipt_root=tmp_path,
        at=AT,
    )

    assert _direct_unblocked(backlog, status, context) == []


def test_cli_external_card_stays_unavailable_without_trusted_verifier(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    event_id = "AUTHENTICATED_NATIVE_DELIVERY"
    external_card = _typed_card("PR-159", external_event=event_id)
    external_card["activation_state"] = "DORMANT_EXTERNAL"
    _write_yaml(backlog, _typed_backlog(external_card))
    status_payload = {
        "completed": [],
        "blocked": [],
        "pending": [],
        "dormant_external": ["PR-159"],
        "execution_resolutions": {},
        "external_events": {},
    }
    _write_yaml(status, status_payload)

    dormant = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert dormant.returncode == 0, dormant.stderr
    assert json.loads(dormant.stdout)["unblocked_next"] == []

    status_payload["dormant_external"] = []
    status_payload["pending"] = ["PR-159"]
    external_card["activation_state"] = "PENDING"
    _write_yaml(backlog, _typed_backlog(external_card))
    status_payload["external_events"] = {event_id: {"verified": True}}
    _write_yaml(status, status_payload)
    unauthenticated = _run(str(PROGRESS), str(backlog), str(status), "--json")
    assert unauthenticated.returncode == 0, unauthenticated.stderr
    assert json.loads(unauthenticated.stdout)["unblocked_next"] == []

    status_payload["external_events"] = {
        event_id: {
            "receipt": {
                "path": "docs/native_delivery/receipt.json",
                "sha256": "d" * 64,
            }
        }
    }
    _write_yaml(status, status_payload)
    no_trust_root = _run(str(PROGRESS), str(backlog), str(status), "--json")
    assert no_trust_root.returncode == 0, no_trust_root.stderr
    assert json.loads(no_trust_root.stdout)["unblocked_next"] == []


def _external_status(pointer: dict[str, str]) -> tuple[dict, dict]:
    event_id = "AUTHENTICATED_NATIVE_DELIVERY"
    backlog = _typed_backlog(_typed_card("PR-159", external_event=event_id))
    status = {
        "completed": [],
        "blocked": [],
        "pending": ["PR-159"],
        "dormant_external": [],
        "execution_resolutions": {},
        "external_events": {event_id: {"receipt": pointer}},
    }
    return backlog, status


def test_typed_external_api_accepts_verified_independent_delivery(
    tmp_path: Path,
) -> None:
    pointer = _write_json_receipt(
        tmp_path,
        "external.json",
        _signed_external_record(),
    )
    backlog, status = _external_status(pointer)
    context = progress_module.ReceiptVerificationContext(
        registry=_trusted_registry(),
        receipt_root=tmp_path,
        at=AT,
    )

    assert _direct_unblocked(backlog, status, context) == ["PR-159"]


@pytest.mark.parametrize(
    "failure_mode",
    [
        "nonexistent",
        "hash_mismatch",
        "forged",
        "wrong_scope",
        "unknown_provider",
        "expired_provider",
        "revoked_provider",
        "internal_provider",
    ],
)
def test_typed_external_api_rejects_untrusted_delivery_modes(
    tmp_path: Path,
    failure_mode: str,
) -> None:
    scope = (
        "unrelated_external_scope"
        if failure_mode == "wrong_scope"
        else "native_low_ell_delivery"
    )
    provider = (
        "principal:unknown"
        if failure_mode == "unknown_provider"
        else "principal:external-provider"
    )
    payload = _signed_external_record(
        scope=scope,
        provider=provider,
        forged=failure_mode == "forged",
    )
    pointer = _write_json_receipt(tmp_path, "external.json", payload)
    if failure_mode == "nonexistent":
        pointer["path"] = "missing.json"
    elif failure_mode == "hash_mismatch":
        pointer["sha256"] = "0" * 64
    backlog, status = _external_status(pointer)
    context = progress_module.ReceiptVerificationContext(
        registry=_trusted_registry(
            provider_independence=(
                "correlated_internal_provider"
                if failure_mode == "internal_provider"
                else "independent_external"
            ),
            provider_valid_until=(
                "2026-07-14T00:00:00+00:00"
                if failure_mode == "expired_provider"
                else "2027-01-01T00:00:00+00:00"
            ),
            provider_revoked=failure_mode == "revoked_provider",
        ),
        receipt_root=tmp_path,
        at=AT,
    )

    assert _direct_unblocked(backlog, status, context) == []


def test_progress_report_writes_checkpoint_artifact_when_due(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(
        status,
        {
            "completed": [f"PR-{index:03d}" for index in range(5)],
            "blocked": [],
        },
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode == 0, completed.stderr
    checkpoint = checkpoint_dir / "checkpoint_005.md"
    assert checkpoint.exists()
    rendered = checkpoint.read_text(encoding="utf-8")
    assert "Completed PRs: 5/5 = 100.0%" in rendered
    assert "Replan required: no" in rendered
    assert "not scientific readiness evidence" in rendered
    assert "## Artifact metadata" in rendered
    assert "Config hash:" in rendered
    assert "Input hashes:" in rendered


def test_progress_report_scoreboard_records_satisfied_checkpoint(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    scoreboard = tmp_path / "progress_scoreboard.md"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
        "--write-scoreboard",
        str(scoreboard),
    )

    assert completed.returncode == 0, completed.stderr
    rendered = scoreboard.read_text(encoding="utf-8")
    assert "Checkpoint due: yes; satisfied by " in rendered
    assert "checkpoint_005.md" in rendered


def test_progress_report_checkpoint_detects_no_progress_when_due_count_repeats(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(
        status,
        {
            "completed": [f"PR-{index:03d}" for index in range(5)],
            "blocked": [],
        },
    )

    first = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
        "--json",
    )
    assert first.returncode == 0, first.stderr
    checkpoint = checkpoint_dir / "checkpoint_005.md"
    original = checkpoint.read_text(encoding="utf-8")

    repeated = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
        "--json",
    )

    assert repeated.returncode == 0, repeated.stderr
    payload = json.loads(repeated.stdout)
    assert payload["previous_checkpoint_completed"] == 5
    assert payload["progress_delta_completed"] == 0
    assert payload["replan_required"] is True
    assert "progress did not advance" in payload["replan_reason"]
    assert checkpoint.read_text(encoding="utf-8") == original


def test_progress_report_rejects_checkpoint_completed_identity_mismatch(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    _write_yaml(backlog, _linear_backlog(10))
    _write_yaml(
        status,
        {
            "completed": [f"PR-{index:03d}" for index in range(10)],
            "blocked": [],
        },
    )
    (checkpoint_dir / "checkpoint_005.md").write_text(
        '<!-- checkpoint_meta {"completed": 10, "percent_complete": 100.0} -->\n',
        encoding="utf-8",
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode != 0
    assert "completed count does not match filename" in completed.stderr


def test_progress_report_does_not_write_checkpoint_when_not_due(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(4)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode == 0, completed.stderr
    assert "Checkpoint due: False" in completed.stdout
    assert not checkpoint_dir.exists()


def test_progress_report_json_stays_valid_when_writing_checkpoint(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
        "--json",
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["checkpoint_due"] is True
    assert payload["checkpoint_artifact"].endswith("checkpoint_005.md")
    assert payload["replan_required"] is False


def test_progress_report_json_marks_due_checkpoint_without_write_dir(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--json",
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["checkpoint_due"] is True
    assert payload["checkpoint_artifact"] is None
    assert "rerun with --write-checkpoint-dir" in payload["replan_reason"]


def test_progress_report_rejects_malformed_previous_checkpoint_metadata(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})
    (checkpoint_dir / "checkpoint_004.md").write_text(
        "<!-- checkpoint_meta not-json -->\n",
        encoding="utf-8",
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode != 0
    assert "malformed checkpoint metadata" in completed.stderr


def test_progress_checkpoint_is_immutable_but_identical_reuse_is_allowed(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(
        status,
        {
            "completed": [f"PR-{index:03d}" for index in range(5)],
            "blocked": [],
        },
    )
    command = (
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    first = _run(*command)
    assert first.returncode == 0, first.stderr
    checkpoint = checkpoint_dir / "checkpoint_005.md"
    original = checkpoint.read_text(encoding="utf-8")

    identical = _run(*command)
    assert identical.returncode == 0, identical.stderr
    assert checkpoint.read_text(encoding="utf-8") == original

    checkpoint.write_text(
        original.replace("Replan required: no", "Replan required: yes"),
        encoding="utf-8",
    )
    differing = _run(*command)
    assert differing.returncode != 0
    assert "refusing to overwrite differing immutable checkpoint" in differing.stderr
    assert checkpoint.read_text(encoding="utf-8") != original
