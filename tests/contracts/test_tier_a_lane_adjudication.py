from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from common.remediation_state import (
    AuthorityError,
    LaneAdjudicationUnitKind,
    LaneAdjudicationVerdict,
    RemediationContractError,
    TIER_A_LANE_CAPABILITY_EFFECT,
    TierALaneAdjudication,
)
from common.tier_a_lane_adjudication import (
    EVENT_GATED,
    FAMILY_LEDGER,
    FROZEN_SHA256,
    MAPPER_RECEIPT,
    MAPPER_RESULT,
    MAPPER_RESULT_SHA256,
    STATUS,
    TierASourceError,
    _frozen_bytes,
    build_source_manifest,
)
from common.tier_a_adjudication_ledger import (
    PANEL_RECEIPT_FILE_SHA256,
    PANEL_RESULT_RUN_ID,
    PANEL_RESULT_SHA256,
    SOURCE_MANIFEST_FILE_SHA256,
    SUPERSEDED_PANEL_RESULT,
    TierALedgerError,
    _validate_panel_lane,
    build_adjudication_ledger,
)


ROOT = Path(__file__).resolve().parents[2]
GENERATED = (
    ROOT
    / "docs/research_program/post_pr275/tier_a_adjudication/source_manifest.json"
)
PANEL = (
    ROOT
    / "docs/research_program/post_pr275/tier_a_adjudication/panel_receipt.json"
)
LEDGER = (
    ROOT
    / "docs/research_program/post_pr275/tier_a_adjudication/adjudication_ledger.json"
)
V10_SOURCE = ROOT / "docs/audits/v10_web_crag_20260721/tier_evidence.json"
DELIVERY_SPEC = (
    ROOT
    / "docs/research_program/post_pr275/tier_a_adjudication/pr278_delivery_spec_v2.yaml"
)
PANEL_SPEC = (
    ROOT / "docs/research_program/post_pr275/tier_a_adjudication/pr278_spec.yaml"
)
POLICY_V2 = (
    ROOT
    / "docs/research_program/post_pr275/tier_a_adjudication/pr278_publication_policy_v2.json"
)
MAPPER_RECEIPT_PATH = ROOT / MAPPER_RECEIPT


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _tracked_source_manifest() -> dict[str, object]:
    payload = GENERATED.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == SOURCE_MANIFEST_FILE_SHA256
    value = json.loads(payload)
    assert isinstance(value, dict)
    return value


def _record(**updates: object) -> TierALaneAdjudication:
    source_ledger_sha = _digest("family-ledger")
    receipt = "docs/PR_DELTAS/pr-101.md"
    values: dict[str, object] = {
        "unit_id": "T-EXAMPLE",
        "unit_kind": LaneAdjudicationUnitKind.FAMILY,
        "verdict": LaneAdjudicationVerdict.GRANT,
        "source_ledger_sha256": source_ledger_sha,
        "source_row_sha256": _digest("family-row"),
        "evidence_bindings": {
            FAMILY_LEDGER: source_ledger_sha,
            receipt: _digest("receipt"),
        },
        "terminal_receipt_refs": (receipt,),
        "reviewer_assignment_id": "A-PR278-PANEL-A",
        "reviewer_principal": "reviewer:A-PR278-PANEL-A",
        "author_principals": ("owner:COMMON", "program:BASS_HTT_program"),
        "dissent": "",
    }
    values.update(updates)
    return TierALaneAdjudication(**values)


def test_exact_source_partition_and_negative_crosswalk_result() -> None:
    manifest = _tracked_source_manifest()

    assert manifest["summary"] == {
        "family_rows": 28,
        "source_candidates": 20,
        "reviewable_families": 19,
        "source_candidate_holds": 1,
        "event_gated_families": 8,
        "dual_axis_rows": 62,
        "dual_axis_exact_crosswalks": 0,
        "dual_axis_inconclusive": 62,
        "cf4_p0_rescue_count": 0,
    }
    assert manifest["event_gated"] == dict(sorted(EVENT_GATED.items()))
    assert manifest["final_aggregator"] == "PR-157"
    assert manifest["capability_effect"] == TIER_A_LANE_CAPABILITY_EFFECT
    assert manifest["public_use"] is False
    assert manifest["claim_ceiling"] == "diagnostic_only"


def test_family_queue_preserves_receipts_and_all_existing_gates() -> None:
    rows = {
        row["unit_id"]: row for row in _tracked_source_manifest()["family_units"]
    }
    reviewable = {identity for identity, row in rows.items() if row["reviewable_now"]}
    source_candidate_holds = {
        identity
        for identity, row in rows.items()
        if row["source_candidate"] and not row["reviewable_now"]
    }

    assert len(rows) == 28
    assert len(reviewable) == 19
    assert source_candidate_holds == {"T-OMK"}
    assert rows["T-OMK"]["missing_terminal_cards"] == ["PR-192"]
    assert set(rows) - reviewable - source_candidate_holds == set(EVENT_GATED)
    for identity in reviewable:
        row = rows[identity]
        assert row["pre_adjudication_disposition"] == "PENDING_NON_AUTHOR"
        assert row["terminal_receipt_refs"]
        assert not row["missing_terminal_cards"]
        for receipt in row["terminal_receipt_refs"]:
            assert receipt in row["evidence_bindings"]
            assert (ROOT / receipt).is_file()
    for identity, gate in EVENT_GATED.items():
        assert rows[identity]["event_gate"] == gate
        assert rows[identity]["pre_adjudication_disposition"] == "HOLD"


def test_all_dual_axis_rows_remain_individually_inconclusive() -> None:
    manifest = _tracked_source_manifest()
    rows = manifest["dual_axis_units"]
    v10_ids = {
        row["id"] for row in json.loads(V10_SOURCE.read_text())["entries"]
    }

    assert len(rows) == 62
    assert len({row["unit_id"] for row in rows}) == 62
    assert {row["unit_id"] for row in rows} == v10_ids
    for row in rows:
        assert row["pre_adjudication_disposition"] == "INCONCLUSIVE"
        assert row["exact_terminal_receipt_crosswalk"] is None
        assert row["terminal_receipt_refs"] == []
        assert row["capability_effect"] == TIER_A_LANE_CAPABILITY_EFFECT
        assert row["public_use"] is False
        assert "semantic similarity" in row["pre_adjudication_rationale"]


def test_frozen_source_manifest_is_exact_and_self_addressed() -> None:
    generated = _tracked_source_manifest()
    content_hash = generated.pop("manifest_content_sha256")
    canonical = json.dumps(
        generated, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert content_hash == hashlib.sha256(canonical).hexdigest()


def test_live_dag_drift_does_not_rewrite_base_snapshot_evidence() -> None:
    manifest = _tracked_source_manifest()
    base = manifest["base_merge_sha"]
    frozen_sources = manifest["frozen_sources"]

    for relative in (
        "docs/codex_handoff/pr_backlog.yaml",
        "docs/codex_handoff/pr_status.yaml",
    ):
        completed = subprocess.run(
            ["git", "show", f"{base}:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        assert hashlib.sha256(completed.stdout).hexdigest() == frozen_sources[relative]


def test_source_manifest_regenerates_from_declared_base_snapshot() -> None:
    live_status = (ROOT / STATUS).read_bytes()
    assert hashlib.sha256(live_status).hexdigest() != FROZEN_SHA256[STATUS]
    assert build_source_manifest(ROOT) == _tracked_source_manifest()


def test_mapper_receipt_promotes_exact_operational_result_identity() -> None:
    raw = MAPPER_RECEIPT_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FROZEN_SHA256[MAPPER_RECEIPT]
    receipt = json.loads(raw)
    recorded = receipt.pop("receipt_content_sha256")
    canonical = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")

    assert recorded == hashlib.sha256(canonical).hexdigest()
    assert receipt["result_path"] == MAPPER_RESULT
    assert receipt["result_sha256"] == MAPPER_RESULT_SHA256
    assert receipt["result_status"] == "inconclusive"
    assert receipt["dual_axis_rows"] == 62
    assert receipt["exact_terminal_receipt_crosswalks"] == 0


def test_delivery_authority_supersedes_without_rewriting_closed_panel_input() -> None:
    delivery = yaml.safe_load(DELIVERY_SPEC.read_text())
    predecessor = delivery["authority_transition"]["predecessor"]
    policy = delivery["publication_policy"]

    assert delivery["status"] == "ACTIVE_DELIVERY_SPEC"
    assert policy["path"] == str(POLICY_V2.relative_to(ROOT))
    assert policy["sha256"] == hashlib.sha256(POLICY_V2.read_bytes()).hexdigest()
    assert predecessor["path"] == str(PANEL_SPEC.relative_to(ROOT))
    assert predecessor["sha256"] == hashlib.sha256(PANEL_SPEC.read_bytes()).hexdigest()
    assert predecessor["retained_role"] == "CLOSED_PANEL_INPUT_ONLY"
    assert delivery["authority_transition"]["v1_policy_role"] == "CLOSED_PANEL_INPUT_ONLY"
    assert "sole active delivery authority" in delivery["authority_transition"][
        "successor_rule"
    ]
    publication_policy = json.loads(POLICY_V2.read_text())
    command_ids = {
        command["id"] for command in publication_policy["required_commands"]
    }
    assert "pr278-source-regeneration" in command_ids
    assert publication_policy["attended_publication"]["transaction"] == (
        "sealed_sha_push_then_single_pr_create"
    )
    assert publication_policy["attended_publication"]["forbidden_actions"] == [
        "force_push",
        "approve",
        "merge",
        "ruleset_mutation",
    ]


def _valid_panel_lane() -> tuple[dict[str, object], dict[str, object]]:
    source_row = next(
        row
        for row in _tracked_source_manifest()["family_units"]
        if row["unit_id"] == "D-ACT"
    )
    assignment_id = "A-PR278-PANEL-TEST"
    lane: dict[str, object] = {
        "unit_id": source_row["unit_id"],
        "unit_kind": "FAMILY",
        "verdict": "INCONCLUSIVE",
        "evidence_fingerprint": source_row["evidence_fingerprint"],
        "source_ledger_sha256": FROZEN_SHA256[FAMILY_LEDGER],
        "source_row_sha256": source_row["source_row_sha256"],
        "terminal_receipt_refs": source_row["terminal_receipt_refs"],
        "reviewer_assignment_id": assignment_id,
        "reviewer_principal": f"reviewer:{assignment_id}",
        "author_principals": source_row["author_principals"],
        "claim_ceiling": "diagnostic_only",
        "capability_effect": TIER_A_LANE_CAPABILITY_EFFECT,
        "public_use": False,
        "rationale": "The exact composite proposition lacks one terminal receipt.",
        "dissent": "The evidence is insufficient for the exact row.",
        "evidence_refs": source_row["terminal_receipt_refs"],
    }
    return lane, source_row


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_reviewer", "lacks an assignment-bound reviewer principal"),
        ("wrong_reviewer", "lacks an assignment-bound reviewer principal"),
        ("missing_authors", "does not match source field author_principals"),
        ("wrong_authors", "does not match source field author_principals"),
    ],
)
def test_panel_ingestion_rejects_unbound_reviewer_or_author_identity(
    mutation: str, message: str
) -> None:
    lane, source_row = _valid_panel_lane()
    assignment_id = str(lane["reviewer_assignment_id"])
    if mutation == "missing_reviewer":
        lane.pop("reviewer_principal")
    elif mutation == "wrong_reviewer":
        lane["reviewer_principal"] = "reviewer:A-PR278-PANEL-OTHER"
    elif mutation == "missing_authors":
        lane.pop("author_principals")
    else:
        lane["author_principals"] = ["owner:OTHER"]

    with pytest.raises(TierALedgerError, match=message):
        _validate_panel_lane(
            lane,
            assignment_id=assignment_id,
            source_row=source_row,
        )


def test_panel_receipt_promotes_only_exact_registered_result_rows() -> None:
    panel = json.loads(PANEL.read_text())
    counts = panel["summary"]

    assert counts == {
        "reviewed_families": 19,
        "GRANT": 14,
        "HOLD": 3,
        "DOWNGRADE": 1,
        "INCONCLUSIVE": 1,
        "conflicts": 0,
        "cf4_p0_rescue_count": 0,
    }
    assert {
        row["assignment_id"]: row["sha256"] for row in panel["result_receipts"]
    } == dict(PANEL_RESULT_SHA256)
    assert {
        row["assignment_id"]: row["run_id"] for row in panel["result_receipts"]
    } == dict(PANEL_RESULT_RUN_ID)
    assert hashlib.sha256(PANEL.read_bytes()).hexdigest() == PANEL_RECEIPT_FILE_SHA256
    assert len(panel["lane_dispositions"]) == 19
    assert len({row["unit_id"] for row in panel["lane_dispositions"]}) == 19
    source_rows = {
        row["unit_id"]: row for row in _tracked_source_manifest()["family_units"]
    }
    for row in panel["lane_dispositions"]:
        assert row["reviewer_principal"] in {
            f"reviewer:{row['reviewer_assignment_id']}",
            f"agent:{row['reviewer_assignment_id']}",
        }
        assert row["author_principals"] == source_rows[row["unit_id"]][
            "author_principals"
        ]
    assert panel["superseded_result_receipts"] == [
        {
            "assignment_id": SUPERSEDED_PANEL_RESULT["assignment_id"],
            "run_id": SUPERSEDED_PANEL_RESULT["run_id"],
            "path": (
                f".agent-harness/runs/{SUPERSEDED_PANEL_RESULT['run_id']}"
                f"/results/{SUPERSEDED_PANEL_RESULT['assignment_id']}.json"
            ),
            "sha256": SUPERSEDED_PANEL_RESULT["sha256"],
            "reason": SUPERSEDED_PANEL_RESULT["reason"],
            "authoritative": False,
        }
    ]
    assert panel["capability_effect"] == "NONE_PENDING_PR157"
    assert panel["final_aggregator"] == "PR-157"
    assert panel["public_use"] is False


def test_final_ledger_preserves_all_family_and_dual_axis_dispositions() -> None:
    ledger = build_adjudication_ledger(ROOT)
    tracked = json.loads(LEDGER.read_text())
    families = {row["unit_id"]: row for row in ledger["family_dispositions"]}
    dual = {row["unit_id"]: row for row in ledger["dual_axis_dispositions"]}

    assert tracked == ledger
    assert ledger["summary"] == {
        "family_rows": 28,
        "family_GRANT": 14,
        "family_HOLD": 12,
        "family_DOWNGRADE": 1,
        "family_INCONCLUSIVE": 1,
        "event_gated_HOLD": 8,
        "nonterminal_candidate_HOLD": 1,
        "panel_HOLD": 3,
        "dual_axis_rows": 62,
        "dual_axis_INCONCLUSIVE": 62,
        "exact_dual_axis_terminal_receipt_crosswalks": 0,
        "cf4_p0_rescue_count": 0,
    }
    assert len(families) == 28
    assert len(dual) == 62
    assert {identity for identity, row in families.items() if row["verdict"] == "GRANT"} == {
        "D-CF4",
        "M-CLUSTER",
        "M-DISCRIM",
        "M-EVALUE",
        "M-EVIDENCE",
        "P-LEGACY",
        "T-EGS",
        "T-FRAME",
        "T-MES",
        "T-MULTIFLUID",
        "T-PARITY",
        "T-RANK2",
        "T-W2",
        "T-XC",
    }
    assert {
        identity for identity, row in families.items() if row["verdict"] == "DOWNGRADE"
    } == {"D-ACT"}
    assert {
        identity
        for identity, row in families.items()
        if row["verdict"] == "INCONCLUSIVE"
    } == {"D-K1"}
    assert {identity for identity, row in families.items() if row["verdict"] == "HOLD"} == {
        *EVENT_GATED,
        "T-OMK",
        "T-BIANCHI",
        "T-BRIDGE",
        "T-JOINT",
    }
    assert all(row["verdict"] == "INCONCLUSIVE" for row in dual.values())
    assert all(row["exact_terminal_receipt_crosswalk"] is None for row in dual.values())


def test_final_ledger_never_issues_capability_status_or_public_use() -> None:
    ledger = build_adjudication_ledger(ROOT)
    rows = [*ledger["family_dispositions"], *ledger["dual_axis_dispositions"]]

    assert ledger["claim_capability_decisions"] == []
    assert ledger["scientific_status_changes"] == []
    assert ledger["capability_effect"] == "NONE_PENDING_PR157"
    assert ledger["public_use"] is False
    assert ledger["final_aggregator"] == "PR-157"
    assert ledger["panel_receipt"]["sha256"] == PANEL_RECEIPT_FILE_SHA256
    for row in rows:
        assert row["claim_ceiling"] == "diagnostic_only"
        assert row["capability_effect"] == "NONE_PENDING_PR157"
        assert row["public_use"] is False
        assert "granted" not in row
        assert row["reviewer_principal"] not in row["author_principals"]
        assert len(row["evidence_fingerprint"]) == 64
        assert len(row["source_manifest_evidence_fingerprint"]) == 64
        if row["verdict"] != "GRANT":
            assert row["dissent"]
        if row["verdict"] == "GRANT":
            assert row["terminal_receipt_refs"]


def test_source_drift_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / FAMILY_LEDGER
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")

    with pytest.raises(TierASourceError, match="identity drifted"):
        _frozen_bytes(tmp_path, FAMILY_LEDGER)


def test_lane_record_is_frozen_deterministic_and_not_a_capability() -> None:
    record = _record()
    equivalent = _record(
        evidence_bindings=dict(reversed(list(record.evidence_bindings.items())))
    )
    payload = record.to_dict()

    assert record.evidence_fingerprint == equivalent.evidence_fingerprint
    assert payload["verdict"] == "GRANT"
    assert payload["capability_effect"] == TIER_A_LANE_CAPABILITY_EFFECT
    assert payload["public_use"] is False
    assert "granted" not in payload
    assert "capability" not in payload
    with pytest.raises(FrozenInstanceError):
        record.dissent = "mutated"  # type: ignore[misc]


def test_evidence_fingerprint_excludes_verdict_prose_but_binds_evidence() -> None:
    granted = _record()
    held = replace(granted, verdict="HOLD", dissent="named gate remains open")
    changed = _record(source_row_sha256=_digest("changed-family-row"))

    assert granted.evidence_fingerprint == held.evidence_fingerprint
    assert granted.evidence_fingerprint != changed.evidence_fingerprint


@pytest.mark.parametrize(
    ("updates", "error", "message"),
    [
        (
            {"reviewer_principal": "owner:COMMON"},
            AuthorityError,
            "must bind the registered reviewer_assignment_id",
        ),
        (
            {"reviewer_principal": "reviewer:A-PR278-PANEL-B"},
            AuthorityError,
            "must bind the registered reviewer_assignment_id",
        ),
        (
            {
                "author_principals": (
                    "owner:COMMON",
                    "reviewer:A-PR278-PANEL-A",
                )
            },
            AuthorityError,
            "must not be an author",
        ),
        (
            {"terminal_receipt_refs": (), "verdict": "GRANT"},
            RemediationContractError,
            "GRANT requires at least one terminal receipt",
        ),
        (
            {"terminal_receipt_refs": ("docs/missing.md",)},
            RemediationContractError,
            "must be present in evidence_bindings",
        ),
        (
            {"evidence_bindings": {"/absolute/evidence.json": _digest("x")}},
            RemediationContractError,
            "repository-relative",
        ),
        (
            {"evidence_bindings": {"docs/../escape.json": _digest("x")}},
            RemediationContractError,
            "repository-relative",
        ),
        (
            {"evidence_bindings": {r"C:\\evidence.json": _digest("x")}},
            RemediationContractError,
            "repository-relative",
        ),
        (
            {"source_ledger_sha256": _digest("unbound-ledger")},
            RemediationContractError,
            "must match an exact evidence binding",
        ),
        (
            {"source_row_sha256": "NOT-A-DIGEST"},
            RemediationContractError,
            "lowercase SHA-256",
        ),
        (
            {"verdict": "HOLD", "dissent": ""},
            RemediationContractError,
            "requires an explicit dissent",
        ),
        (
            {"claim_ceiling": "validated"},
            RemediationContractError,
            "must remain diagnostic_only",
        ),
        (
            {"capability_effect": "GRANT"},
            RemediationContractError,
            "cannot issue a capability",
        ),
        (
            {"public_use": True},
            RemediationContractError,
            "cannot enable public use",
        ),
    ],
)
def test_lane_record_rejects_authority_evidence_and_promotion_mutations(
    updates: dict[str, object], error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=message):
        _record(**updates)


def test_dual_axis_inconclusive_requires_explicit_negative_rationale() -> None:
    source_ledger_sha = _digest("dual-axis-ledger")
    record = _record(
        unit_id="D-CF4-CURL",
        unit_kind="DUAL_AXIS_ROW",
        verdict="INCONCLUSIVE",
        source_ledger_sha256=source_ledger_sha,
        evidence_bindings={
            "docs/generated/dual_axis_claim_ledger.json": source_ledger_sha,
            "docs/audits/v10_web_crag_20260721/tier_evidence.json": _digest(
                "v10-source"
            ),
        },
        terminal_receipt_refs=(),
        dissent="No exact registered terminal-receipt crosswalk exists.",
    )

    assert record.verdict is LaneAdjudicationVerdict.INCONCLUSIVE
    assert record.terminal_receipt_refs == ()
    assert record.to_dict()["capability_effect"] == "NONE_PENDING_PR157"


@pytest.mark.parametrize(
    "mode",
    [
        "check-source",
        "verify-frozen-source",
        "verify-panel",
        "verify-ledger",
    ],
)
def test_portable_runner_checks_frozen_generated_sources(mode: str) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr278_tier_a_adjudication.py",
            mode,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["ok"] is True
