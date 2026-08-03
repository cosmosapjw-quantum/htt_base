"""Portable PR-278 panel receipt and fail-closed per-lane ledger.

The registered harness run is local operational evidence and is not committed
wholesale.  This module promotes only the exact result identities and the 19
bounded family dispositions into a compact receipt, then combines that receipt
with the frozen source manifest.  Static event gates, the non-terminal T-OMK
candidate, and the 62 negative dual-axis mappings are preserved rather than
voted away.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from common.remediation_state import (
    TIER_A_LANE_CAPABILITY_EFFECT,
    TierALaneAdjudication,
)
from common.tier_a_lane_adjudication import (
    DUAL_AXIS_LEDGER,
    FAMILY_LEDGER,
    FROZEN_SHA256,
    MAPPER_RECEIPT,
    TierASourceError,
)


REPO = Path(__file__).resolve().parents[3]
OUTPUT_DIR = "docs/research_program/post_pr275/tier_a_adjudication"
SOURCE_MANIFEST = f"{OUTPUT_DIR}/source_manifest.json"
PANEL_RECEIPT = f"{OUTPUT_DIR}/panel_receipt.json"
DELIVERY_SPEC = f"{OUTPUT_DIR}/pr278_delivery_spec_v2.yaml"
ACTIVE_PUBLICATION_POLICY = f"{OUTPUT_DIR}/pr278_publication_policy_v2.json"

PANEL_RUN_ID = "pr278-family-panel-r1-20260804"
PRINCIPAL_REMEDIATION_RUN_ID = "pr278-principal-remediation-r1-20260804"
PANEL_RESULT_RUN_ID: Mapping[str, str] = {
    "A-PR278-PANEL-DATA-METHOD-R2": PRINCIPAL_REMEDIATION_RUN_ID,
    "A-PR278-PANEL-EVIDENCE-LEGACY": PANEL_RUN_ID,
    "A-PR278-PANEL-THEORY": PANEL_RUN_ID,
}
PANEL_RESULT_SHA256: Mapping[str, str] = {
    "A-PR278-PANEL-DATA-METHOD-R2": (
        "13ef70783b74f4fe3520d604be234ca62e1ac05c2d02651015337a889c655a49"
    ),
    "A-PR278-PANEL-EVIDENCE-LEGACY": (
        "b78704ad042dfca6d2bac5bfa010eca7dcbe4770896310b77f98d352a59ced26"
    ),
    "A-PR278-PANEL-THEORY": (
        "d34e2dd6490097332085927252829da482d3d9dd772c1304f55bde3670729472"
    ),
}
PANEL_RESULT_STATUS: Mapping[str, str] = {
    "A-PR278-PANEL-DATA-METHOD-R2": "inconclusive",
    "A-PR278-PANEL-EVIDENCE-LEGACY": "inconclusive",
    "A-PR278-PANEL-THEORY": "fail",
}
PANEL_RUN_AGGREGATES: Mapping[str, Mapping[str, object]] = {
    PANEL_RUN_ID: {
        "merged_sha256": "98fad3229b2dff9885fd09abc5021d23717cc4e1ab6ca2e81508e6fab46c9b06",
        "summary_sha256": "47122e8942ab3a24c521a53dd71e03223b3d9bc93ef79ff3eff716ec582d8c27",
        "assignment_count": 3,
    },
    PRINCIPAL_REMEDIATION_RUN_ID: {
        "merged_sha256": "72e772fb9140c8db9c05eb6af1d3764ee57ab1fba9a727332186f5ca58928ca7",
        "summary_sha256": "6f197b9801a8375140b3ccb88af9be4a5f115e26ef0cf2f6c8e1b241b76c2e9d",
        "assignment_count": 1,
    },
}
SUPERSEDED_PANEL_RESULT: Mapping[str, str] = {
    "assignment_id": "A-PR278-PANEL-DATA-METHOD",
    "run_id": PANEL_RUN_ID,
    "sha256": "0f5bc92525f82ad171f681cd93c3f412484c9c6bf0ecb654a29c45e3e15ecfc6",
    "reason": "MISSING_REVIEWER_AND_AUTHOR_PRINCIPAL_BINDING",
}
SOURCE_MANIFEST_FILE_SHA256 = (
    "0b7eb908da0e92e282ae2470e50ae584cd5f8c00c82c5b1f52f1664145e68a13"
)
DELIVERY_SPEC_FILE_SHA256 = (
    "e5ad215aa01c9c585bad96a871496a4cd098c216296c3192d9b5a32db1530c79"
)
ACTIVE_PUBLICATION_POLICY_FILE_SHA256 = (
    "b3643e191a2e743b8b12165c99405f5dd9f46cd58b7af88593bc1e9070fe0193"
)
PANEL_RECEIPT_FILE_SHA256 = (
    "b7839be6ecf6b0fcdd81f9cbbcff03fc08058d20f2c62b94588602c8ae966f04"
)
EXPECTED_PANEL_FAMILIES: Mapping[str, frozenset[str]] = {
    "A-PR278-PANEL-DATA-METHOD-R2": frozenset(
        {"D-ACT", "D-CF4", "D-K1", "M-CLUSTER", "M-DISCRIM", "M-EVALUE"}
    ),
    "A-PR278-PANEL-EVIDENCE-LEGACY": frozenset(
        {"M-EVIDENCE", "P-LEGACY", "T-BIANCHI", "T-BRIDGE", "T-EGS", "T-FRAME"}
    ),
    "A-PR278-PANEL-THEORY": frozenset(
        {
            "T-JOINT",
            "T-MES",
            "T-MULTIFLUID",
            "T-PARITY",
            "T-RANK2",
            "T-W2",
            "T-XC",
        }
    ),
}
ALLOWED_PANEL_VERDICTS = frozenset({"GRANT", "HOLD", "DOWNGRADE", "INCONCLUSIVE"})


class TierALedgerError(TierASourceError):
    """Raised when the portable panel receipt or final ledger drifts."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )


def _regular_bytes(repo: Path, relative: str) -> bytes:
    path = repo / relative
    if not path.is_file() or path.is_symlink():
        raise TierALedgerError(f"required regular file is missing: {relative}")
    return path.read_bytes()


def _bound_json(repo: Path, relative: str, expected_sha256: str) -> dict[str, Any]:
    payload = _regular_bytes(repo, relative)
    if _sha256(payload) != expected_sha256:
        raise TierALedgerError(f"bound JSON identity drifted: {relative}")
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise TierALedgerError(f"invalid JSON: {relative}") from exc
    if not isinstance(value, dict):
        raise TierALedgerError(f"bound JSON must contain an object: {relative}")
    return value


def _panel_result_path(assignment_id: str) -> str:
    return (
        f".agent-harness/runs/{PANEL_RESULT_RUN_ID[assignment_id]}"
        f"/results/{assignment_id}.json"
    )


def _source_units(source: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = source.get("family_units")
    if not isinstance(rows, list):
        raise TierALedgerError("source manifest family_units must be a list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("unit_id"), str):
            raise TierALedgerError("source manifest has an invalid family row")
        identity = row["unit_id"]
        if identity in result:
            raise TierALedgerError(f"duplicate source family: {identity}")
        result[identity] = row
    if len(result) != 28:
        raise TierALedgerError("source manifest must contain exactly 28 families")
    return result


def _validate_panel_lane(
    lane: Mapping[str, Any],
    *,
    assignment_id: str,
    source_row: Mapping[str, Any],
) -> dict[str, Any]:
    identity = source_row["unit_id"]
    if lane.get("unit_id") != identity or lane.get("unit_kind") != "FAMILY":
        raise TierALedgerError(f"panel lane identity/kind drifted: {identity}")
    verdict = lane.get("verdict")
    if verdict not in ALLOWED_PANEL_VERDICTS:
        raise TierALedgerError(f"panel lane has invalid verdict: {identity}")
    expected_fields = {
        "evidence_fingerprint": source_row["evidence_fingerprint"],
        "source_ledger_sha256": FROZEN_SHA256[FAMILY_LEDGER],
        "source_row_sha256": source_row["source_row_sha256"],
        "terminal_receipt_refs": source_row["terminal_receipt_refs"],
        "reviewer_assignment_id": assignment_id,
        "claim_ceiling": "diagnostic_only",
        "capability_effect": TIER_A_LANE_CAPABILITY_EFFECT,
        "public_use": False,
        "author_principals": source_row["author_principals"],
    }
    for field, expected in expected_fields.items():
        if lane.get(field) != expected:
            raise TierALedgerError(
                f"panel lane {identity} does not match source field {field}"
            )
    reviewer = lane.get("reviewer_principal")
    if reviewer not in {
        f"reviewer:{assignment_id}",
        f"agent:{assignment_id}",
    }:
        raise TierALedgerError(
            f"panel lane {identity} lacks an assignment-bound reviewer principal"
        )
    if reviewer in source_row["author_principals"]:
        raise TierALedgerError(f"panel lane {identity} is author self-approval")
    rationale = lane.get("rationale")
    dissent = lane.get("dissent")
    if not isinstance(rationale, str) or not rationale.strip():
        raise TierALedgerError(f"panel lane {identity} lacks a rationale")
    if not isinstance(dissent, str) or (verdict != "GRANT" and not dissent.strip()):
        raise TierALedgerError(f"panel lane {identity} lacks required dissent")
    refs = lane.get("evidence_refs")
    if not isinstance(refs, list):
        raise TierALedgerError(f"panel lane {identity} evidence_refs must be a list")
    if not set(source_row["terminal_receipt_refs"]).issubset(set(refs)):
        raise TierALedgerError(f"panel lane {identity} omitted a terminal receipt")
    return dict(lane)


def build_panel_receipt_from_run(repo: Path = REPO) -> dict[str, Any]:
    """Promote three exact authoritative results and preserve one superseded result."""

    repo = repo.resolve()
    if _sha256(_regular_bytes(repo, DELIVERY_SPEC)) != DELIVERY_SPEC_FILE_SHA256:
        raise TierALedgerError("active PR-278 delivery spec identity drifted")
    if (
        _sha256(_regular_bytes(repo, ACTIVE_PUBLICATION_POLICY))
        != ACTIVE_PUBLICATION_POLICY_FILE_SHA256
    ):
        raise TierALedgerError("active PR-278 publication policy identity drifted")
    source = _bound_json(repo, SOURCE_MANIFEST, SOURCE_MANIFEST_FILE_SHA256)
    source_rows = _source_units(source)
    result_receipts: list[dict[str, Any]] = []
    lanes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for assignment_id in sorted(PANEL_RESULT_SHA256):
        relative = _panel_result_path(assignment_id)
        run_id = PANEL_RESULT_RUN_ID[assignment_id]
        result = _bound_json(repo, relative, PANEL_RESULT_SHA256[assignment_id])
        if (
            result.get("run_id") != run_id
            or result.get("assignment_id") != assignment_id
            or result.get("agent_type") != "claim_gate_reviewer"
            or result.get("independence_mode") != "blind-results"
            or result.get("status") != PANEL_RESULT_STATUS[assignment_id]
            or result.get("errors") != []
        ):
            raise TierALedgerError(f"panel result envelope drifted: {assignment_id}")
        rows = result.get("lane_dispositions")
        if not isinstance(rows, list):
            raise TierALedgerError(f"panel result lacks lane_dispositions: {assignment_id}")
        identities = {
            row.get("unit_id") for row in rows if isinstance(row, Mapping)
        }
        if identities != EXPECTED_PANEL_FAMILIES[assignment_id] or len(rows) != len(identities):
            raise TierALedgerError(f"panel assignment family partition drifted: {assignment_id}")
        for raw_lane in rows:
            assert isinstance(raw_lane, Mapping)
            identity = str(raw_lane["unit_id"])
            if identity in seen:
                raise TierALedgerError(f"family received multiple panel verdicts: {identity}")
            seen.add(identity)
            lane = _validate_panel_lane(
                raw_lane,
                assignment_id=assignment_id,
                source_row=source_rows[identity],
            )
            lane["panel_result_path"] = relative
            lane["panel_result_sha256"] = PANEL_RESULT_SHA256[assignment_id]
            lanes.append(lane)
        result_receipts.append(
            {
                "assignment_id": assignment_id,
                "run_id": run_id,
                "path": relative,
                "sha256": PANEL_RESULT_SHA256[assignment_id],
                "status": PANEL_RESULT_STATUS[assignment_id],
                "lane_count": len(rows),
            }
        )
    expected = set().union(*EXPECTED_PANEL_FAMILIES.values())
    if seen != expected or len(seen) != 19:
        raise TierALedgerError("panel receipt must cover exactly 19 unique families")
    run_receipts = []
    for run_id, expected_run in sorted(PANEL_RUN_AGGREGATES.items()):
        merged_path = f".agent-harness/runs/{run_id}/MERGED_RESULTS.json"
        summary_path = f".agent-harness/runs/{run_id}/RUN_SUMMARY.json"
        merged_sha = str(expected_run["merged_sha256"])
        summary_sha = str(expected_run["summary_sha256"])
        assignment_count = int(expected_run["assignment_count"])
        merged = _bound_json(repo, merged_path, merged_sha)
        summary = _bound_json(repo, summary_path, summary_sha)
        if (
            merged.get("process_status") != "STRUCTURALLY_VALID"
            or merged.get("validated_result_count") != assignment_count
            or merged.get("errors") != []
            or merged.get("conflicts") != []
            or summary.get("assignment_count") != assignment_count
        ):
            raise TierALedgerError(
                f"panel aggregate or run summary is not structurally valid: {run_id}"
            )
        run_receipts.append(
            {
                "run_id": run_id,
                "merged_results": {"path": merged_path, "sha256": merged_sha},
                "run_summary": {"path": summary_path, "sha256": summary_sha},
                "assignment_count": assignment_count,
            }
        )
    superseded_id = SUPERSEDED_PANEL_RESULT["assignment_id"]
    superseded_run = SUPERSEDED_PANEL_RESULT["run_id"]
    superseded_path = (
        f".agent-harness/runs/{superseded_run}/results/{superseded_id}.json"
    )
    superseded = _bound_json(
        repo, superseded_path, SUPERSEDED_PANEL_RESULT["sha256"]
    )
    superseded_rows = superseded.get("lane_dispositions")
    if (
        superseded.get("assignment_id") != superseded_id
        or not isinstance(superseded_rows, list)
        or any(
            not isinstance(row, Mapping)
            or row.get("reviewer_principal") is not None
            or row.get("author_principals") is not None
            for row in superseded_rows
        )
    ):
        raise TierALedgerError("superseded panel result reason no longer matches")
    counts = Counter(str(row["verdict"]) for row in lanes)
    if counts != Counter(
        {"GRANT": 14, "HOLD": 3, "DOWNGRADE": 1, "INCONCLUSIVE": 1}
    ):
        raise TierALedgerError("panel verdict counts drifted")
    payload: dict[str, Any] = {
        "schema": "htt.tier_a_adjudication.panel_receipt.v2",
        "pr_id": "PR-278",
        "delivery_authority": {
            "path": DELIVERY_SPEC,
            "sha256": DELIVERY_SPEC_FILE_SHA256,
            "publication_policy": {
                "path": ACTIVE_PUBLICATION_POLICY,
                "sha256": ACTIVE_PUBLICATION_POLICY_FILE_SHA256,
            },
        },
        "source_manifest": {
            "path": SOURCE_MANIFEST,
            "sha256": SOURCE_MANIFEST_FILE_SHA256,
            "manifest_content_sha256": source["manifest_content_sha256"],
            "snapshot_commit": source["base_merge_sha"],
        },
        "result_receipts": result_receipts,
        "run_receipts": run_receipts,
        "superseded_result_receipts": [
            {
                "assignment_id": superseded_id,
                "run_id": superseded_run,
                "path": superseded_path,
                "sha256": SUPERSEDED_PANEL_RESULT["sha256"],
                "reason": SUPERSEDED_PANEL_RESULT["reason"],
                "authoritative": False,
            }
        ],
        "summary": {
            "reviewed_families": 19,
            "GRANT": 14,
            "HOLD": 3,
            "DOWNGRADE": 1,
            "INCONCLUSIVE": 1,
            "conflicts": 0,
            "cf4_p0_rescue_count": 0,
        },
        "lane_dispositions": sorted(lanes, key=lambda row: row["unit_id"]),
        "capability_effect": TIER_A_LANE_CAPABILITY_EFFECT,
        "final_aggregator": "PR-157",
        "public_use": False,
        "claim_ceiling": "diagnostic_only",
    }
    payload["receipt_content_sha256"] = _canonical_sha256(payload)
    return payload


def _normalized_panel_record(
    lane: Mapping[str, Any], source_row: Mapping[str, Any]
) -> dict[str, Any]:
    assignment_id = str(lane["reviewer_assignment_id"])
    record = TierALaneAdjudication(
        unit_id=str(lane["unit_id"]),
        unit_kind="FAMILY",
        verdict=str(lane["verdict"]),
        source_ledger_sha256=FROZEN_SHA256[FAMILY_LEDGER],
        source_row_sha256=str(source_row["source_row_sha256"]),
        evidence_bindings=source_row["evidence_bindings"],
        terminal_receipt_refs=source_row["terminal_receipt_refs"],
        reviewer_assignment_id=assignment_id,
        reviewer_principal=str(lane["reviewer_principal"]),
        author_principals=lane["author_principals"],
        dissent=str(lane["dissent"]),
    )
    payload = record.to_dict()
    payload.update(
        {
            "disposition_origin": "registered_non_author_panel",
            "source_manifest_evidence_fingerprint": source_row[
                "evidence_fingerprint"
            ],
            "panel_result_path": lane["panel_result_path"],
            "panel_result_sha256": lane["panel_result_sha256"],
            "rationale": lane["rationale"],
            "counterevidence": list(lane.get("counterevidence", [])),
        }
    )
    return payload


def _static_family_record(source_row: Mapping[str, Any]) -> dict[str, Any]:
    bindings = dict(source_row["evidence_bindings"])
    bindings[MAPPER_RECEIPT] = FROZEN_SHA256[MAPPER_RECEIPT]
    record = TierALaneAdjudication(
        unit_id=str(source_row["unit_id"]),
        unit_kind="FAMILY",
        verdict="HOLD",
        source_ledger_sha256=FROZEN_SHA256[FAMILY_LEDGER],
        source_row_sha256=str(source_row["source_row_sha256"]),
        evidence_bindings=bindings,
        terminal_receipt_refs=source_row["terminal_receipt_refs"],
        reviewer_assignment_id="A-PR278-EVIDENCE-MAP",
        reviewer_principal="reviewer:A-PR278-EVIDENCE-MAP",
        author_principals=source_row["author_principals"],
        dissent=str(source_row["pre_adjudication_rationale"]),
    )
    payload = record.to_dict()
    payload.update(
        {
            "disposition_origin": "registered_exact_source_map",
            "source_manifest_evidence_fingerprint": source_row[
                "evidence_fingerprint"
            ],
            "event_gate": source_row.get("event_gate"),
            "missing_terminal_cards": list(source_row["missing_terminal_cards"]),
            "rationale": source_row["pre_adjudication_rationale"],
            "counterevidence": [],
        }
    )
    return payload


def _dual_axis_record(source_row: Mapping[str, Any]) -> dict[str, Any]:
    record = TierALaneAdjudication(
        unit_id=str(source_row["unit_id"]),
        unit_kind="DUAL_AXIS_ROW",
        verdict="INCONCLUSIVE",
        source_ledger_sha256=FROZEN_SHA256[DUAL_AXIS_LEDGER],
        source_row_sha256=str(source_row["source_row_sha256"]),
        evidence_bindings=source_row["evidence_bindings"],
        terminal_receipt_refs=(),
        reviewer_assignment_id="A-PR278-EVIDENCE-MAP",
        reviewer_principal="reviewer:A-PR278-EVIDENCE-MAP",
        author_principals=("program:BASS_HTT_program",),
        dissent=str(source_row["pre_adjudication_rationale"]),
    )
    payload = record.to_dict()
    payload.update(
        {
            "disposition_origin": "registered_negative_exact_crosswalk_map",
            "source_manifest_evidence_fingerprint": source_row[
                "evidence_fingerprint"
            ],
            "exact_terminal_receipt_crosswalk": None,
            "rationale": source_row["pre_adjudication_rationale"],
            "counterevidence": [],
        }
    )
    return payload


def build_adjudication_ledger(repo: Path = REPO) -> dict[str, Any]:
    """Build all 28 family and 62 dual-axis receipt dispositions."""

    repo = repo.resolve()
    source = _bound_json(repo, SOURCE_MANIFEST, SOURCE_MANIFEST_FILE_SHA256)
    panel = _bound_json(repo, PANEL_RECEIPT, PANEL_RECEIPT_FILE_SHA256)
    recorded_panel_content = panel.get("receipt_content_sha256")
    panel_content = dict(panel)
    panel_content.pop("receipt_content_sha256", None)
    if recorded_panel_content != _canonical_sha256(panel_content):
        raise TierALedgerError("panel receipt self-addressed content hash drifted")
    if panel.get("source_manifest", {}).get("sha256") != SOURCE_MANIFEST_FILE_SHA256:
        raise TierALedgerError("panel receipt does not bind the frozen source manifest")
    source_rows = _source_units(source)
    panel_rows = panel.get("lane_dispositions")
    if not isinstance(panel_rows, list):
        raise TierALedgerError("panel receipt lane_dispositions must be a list")
    reviewed: dict[str, Mapping[str, Any]] = {}
    for lane in panel_rows:
        if not isinstance(lane, Mapping) or not isinstance(lane.get("unit_id"), str):
            raise TierALedgerError("panel receipt has an invalid lane row")
        identity = lane["unit_id"]
        if identity in reviewed:
            raise TierALedgerError(f"panel receipt duplicated family {identity}")
        reviewed[identity] = lane
    if set(reviewed) != set().union(*EXPECTED_PANEL_FAMILIES.values()):
        raise TierALedgerError("panel receipt family set drifted")
    family_records = []
    for identity, source_row in sorted(source_rows.items()):
        lane = reviewed.get(identity)
        family_records.append(
            _normalized_panel_record(lane, source_row)
            if lane is not None
            else _static_family_record(source_row)
        )
    dual_rows = source.get("dual_axis_units")
    if not isinstance(dual_rows, list) or len(dual_rows) != 62:
        raise TierALedgerError("source manifest must contain exactly 62 dual-axis rows")
    dual_records = [_dual_axis_record(row) for row in dual_rows]
    if len({row["unit_id"] for row in dual_records}) != 62:
        raise TierALedgerError("dual-axis final records are not unique")
    family_counts = Counter(row["verdict"] for row in family_records)
    dual_counts = Counter(row["verdict"] for row in dual_records)
    if family_counts != Counter(
        {"GRANT": 14, "HOLD": 12, "DOWNGRADE": 1, "INCONCLUSIVE": 1}
    ):
        raise TierALedgerError("final family verdict counts drifted")
    if dual_counts != Counter({"INCONCLUSIVE": 62}):
        raise TierALedgerError("final dual-axis verdict counts drifted")
    if any(row["public_use"] for row in (*family_records, *dual_records)):
        raise TierALedgerError("PR-278 final ledger cannot enable public use")
    payload: dict[str, Any] = {
        "schema": "htt.tier_a_adjudication.ledger.v1",
        "pr_id": "PR-278",
        "source_manifest": panel["source_manifest"],
        "panel_receipt": {
            "path": PANEL_RECEIPT,
            "sha256": PANEL_RECEIPT_FILE_SHA256,
            "receipt_content_sha256": panel["receipt_content_sha256"],
            "result_receipts": panel["result_receipts"],
        },
        "summary": {
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
        },
        "family_dispositions": family_records,
        "dual_axis_dispositions": dual_records,
        "final_aggregator": "PR-157",
        "capability_effect": TIER_A_LANE_CAPABILITY_EFFECT,
        "public_use": False,
        "claim_ceiling": "diagnostic_only",
        "scientific_status_changes": [],
        "claim_capability_decisions": [],
    }
    payload["ledger_content_sha256"] = _canonical_sha256(payload)
    return payload


__all__ = [
    "PANEL_RECEIPT",
    "PANEL_RECEIPT_FILE_SHA256",
    "PANEL_RESULT_RUN_ID",
    "PANEL_RESULT_SHA256",
    "PANEL_RUN_ID",
    "SOURCE_MANIFEST",
    "SOURCE_MANIFEST_FILE_SHA256",
    "SUPERSEDED_PANEL_RESULT",
    "TierALedgerError",
    "build_adjudication_ledger",
    "build_panel_receipt_from_run",
]
