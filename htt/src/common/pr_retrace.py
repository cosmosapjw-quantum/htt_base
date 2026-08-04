"""Fail-closed reverse-trace and recomputation routing for PR-279.

The records produced here are governance diagnostics.  Artifact invalidation
is represented by a real :class:`common.evidence_graph.EvidenceGraph`, while
work-unit scheduling remains a separate routing projection.  Neither surface
can issue a ``ClaimCapabilityDecision``.  Historical source rows remain
reconstructible byte-for-byte while live orchestration state is overlaid from
the canonical status SSoT.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import yaml


class RetraceContractError(ValueError):
    """Raised when a reverse-trace input or derived route is not total."""


class RetraceDisposition(str, Enum):
    STABLE_REPLAY = "STABLE_REPLAY"
    MIGRATION_ONLY = "MIGRATION_ONLY"
    REPROVE = "REPROVE"
    RECALIBRATE_SYNTHETIC = "RECALIBRATE_SYNTHETIC"
    RERUN_FROM_RAW_DATA = "RERUN_FROM_RAW_DATA"
    RERUN_FROM_ADMITTED_SUMMARY = "RERUN_FROM_ADMITTED_SUMMARY"
    CORRECTED_SUPERSEDED = "CORRECTED_SUPERSEDED"
    FALSIFIED_HISTORICAL = "FALSIFIED_HISTORICAL"
    LEGACY_REPRODUCTION_ONLY = "LEGACY_REPRODUCTION_ONLY"
    EXTERNAL_BLOCKED = "EXTERNAL_BLOCKED"
    NATIVE_BLOCKED = "NATIVE_BLOCKED"


class DataArtifactDisposition(str, Enum):
    REDO_REQUIRED = "REDO_REQUIRED"
    REDO_UPGRADE = "REDO_UPGRADE"
    PRESERVE = "PRESERVE"
    BLOCKED = "BLOCKED"


PR280_ACTIVE_CORE_SUCCESSORS = (
    (
        "htt.bass.validation.test_external_code_policy::"
        "test_no_external_code_imports_in_production",
        "PR-295",
    ),
    (
        "htt.bass.spectrum.test_d2_pstf_progressive_closure::"
        "test_python_pstf_closure_does_not_regress",
        "PR-296",
    ),
    (
        "scripts.codex_harness.test_codex_assets::"
        "test_installer_copies_repo_scoped_assets_with_project_harness_config",
        "PR-297",
    ),
)


INTERNAL_CSV_FIELDS = (
    "pr_id",
    "wave",
    "owner",
    "level",
    "risk",
    "current_status",
    "title",
    "depends",
    "disposition",
    "phase",
    "start_condition",
    "maximum_post_replay_claim",
    "rationale",
)

GITHUB_CSV_FIELDS = (
    "github_pr",
    "merged",
    "state",
    "draft",
    "base",
    "head",
    "head_sha",
    "commits",
    "title",
    "url",
    "lineage_role",
)

LIFECYCLE_EDGE_KINDS = frozenset(
    {
        "SUPERSEDED_BY",
        "INVALIDATES_THEOREM",
        "INVALIDATES_DATA",
        "INVALIDATES_MASK",
        "INVALIDATES_COVARIANCE",
        "INVALIDATES_TRANSFER",
        "INVALIDATES_ESTIMAND",
        "REQUIRES_RECALIBRATION",
        "REQUIRES_REEXECUTION",
    }
)

_INTERNAL_ID_RE = re.compile(r"PR-(\d{3})\Z")
_GITHUB_ID_RE = re.compile(r"GITHUB-PR-(\d{4})\Z")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
_ATOMIC_ACTIONS = (
    "PROOF_READJUDICATION",
    "FRESH_SYNTHETIC",
    "LEGACY_PUSHFORWARD",
    "FULL_REFIT",
    "REGENERATE",
    "FROM_RAW",
)

_ACTIVE_SCIENTIFIC_OWNERS = frozenset({"COMMON", "OBSSTAT", "HTT", "MIO"})
_LEGACY_SCIENTIFIC_OWNER = "TSC_LEGACY"

_SUPERSESSION_RELATION_IDS = frozenset(
    {
        "SUP-PR172-PR184",
        "SUP-PR168-PR248",
        "SUP-PR130-TAIL-GATE",
        "SUP-PR169-ALGEBRAIC-ONLY",
        "SUP-PR170-PROVENANCE-ONLY",
    }
)

_PRIMARY_PRECEDENCE = (
    RetraceDisposition.FALSIFIED_HISTORICAL,
    RetraceDisposition.NATIVE_BLOCKED,
    RetraceDisposition.EXTERNAL_BLOCKED,
    RetraceDisposition.CORRECTED_SUPERSEDED,
    RetraceDisposition.RERUN_FROM_RAW_DATA,
    RetraceDisposition.RERUN_FROM_ADMITTED_SUMMARY,
    RetraceDisposition.REPROVE,
    RetraceDisposition.RECALIBRATE_SYNTHETIC,
    RetraceDisposition.MIGRATION_ONLY,
    RetraceDisposition.LEGACY_REPRODUCTION_ONLY,
    RetraceDisposition.STABLE_REPLAY,
)

_REQUIRED_OUTPUT_METADATA = frozenset(
    {
        "owner",
        "scope",
        "allowed_use",
        "transfer_source",
        "source_identities",
        "assumptions",
        "caveats",
        "generating_procedure",
        "claim_tier_ceiling",
    }
)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return _digest(path.read_bytes())


def _require_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise RetraceContractError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _require_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RetraceContractError(f"{field} must be a mapping")
    return value


def _require_sequence(value: object, field: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RetraceContractError(f"{field} must be a sequence")
    return value


def validate_output_metadata(document: Mapping[str, object]) -> None:
    missing = _REQUIRED_OUTPUT_METADATA - set(document)
    if missing:
        raise RetraceContractError(
            f"derived output lacks global metadata: {sorted(missing)}"
        )
    for field in ("owner", "scope", "allowed_use", "transfer_source", "generating_procedure", "claim_tier_ceiling"):
        value = document.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RetraceContractError(f"derived output metadata {field} is empty")
    for field in ("source_identities", "assumptions", "caveats"):
        _require_sequence(document.get(field), f"output metadata {field}")


def load_yaml_mapping(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RetraceContractError(f"{path} must contain a mapping")
    return value


def dump_yaml_bytes(value: Mapping[str, object]) -> bytes:
    return yaml.safe_dump(
        dict(value),
        sort_keys=False,
        allow_unicode=True,
        width=100,
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    return _digest(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def _csv_rows(path: Path, expected_fields: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(expected_fields):
            raise RetraceContractError(
                f"{path.name} header mismatch: {reader.fieldnames!r}"
            )
        rows = [dict(row) for row in reader]
    if any(None in row for row in rows):
        raise RetraceContractError(f"{path.name} contains an over-wide CSV row")
    return rows


def reconstruct_csv_bytes(
    rows: Sequence[Mapping[str, object]],
    fields: Sequence[str],
    *,
    trailing_blank_lines: int = 0,
) -> bytes:
    if trailing_blank_lines < 0:
        raise RetraceContractError("trailing_blank_lines cannot be negative")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if set(row) != set(fields):
            raise RetraceContractError("source row fields do not match the registered CSV")
        writer.writerow({field: str(row[field]) for field in fields})
    return (output.getvalue() + "\n" * trailing_blank_lines).encode("utf-8")


def _parse_joined_actions(value: str) -> list[str]:
    actions: list[str] = []
    remaining = value
    while remaining:
        match = next(
            (action for action in _ATOMIC_ACTIONS if remaining.startswith(action)),
            None,
        )
        if match is None:
            raise RetraceContractError(
                f"unknown legacy disposition segment {remaining!r} in {value!r}"
            )
        actions.append(match)
        remaining = remaining[len(match) :]
        if remaining:
            if not remaining.startswith("_AND_"):
                raise RetraceContractError(
                    f"malformed legacy disposition separator in {value!r}"
                )
            remaining = remaining[len("_AND_") :]
    return actions


def parse_legacy_actions(value: str) -> tuple[str, ...]:
    """Parse the finite legacy grammar without lossy substring splitting."""

    if not isinstance(value, str) or not value:
        raise RetraceContractError("legacy disposition must be non-empty")
    exact = {
        "MIGRATE_REVALIDATE": ("MIGRATE_REVALIDATE",),
        "HOLD_NATIVE": ("HOLD_NATIVE",),
        "REPAIR_THEN_RERUN": ("REPAIR_THEN_RERUN",),
        "READMIT_COMPLETE_DATA_THEN_SEPARATELY_AUTHORIZE": (
            "READMIT_COMPLETE_DATA_THEN_SEPARATELY_AUTHORIZE",
        ),
    }
    if value in exact:
        return exact[value]
    for prefix in ("RESUME_COMPLETE_THEN_", "REBASE_THEN_"):
        if value.startswith(prefix):
            prefix_action = prefix[:-1]
            return (prefix_action, *_parse_joined_actions(value[len(prefix) :]))
    return tuple(_parse_joined_actions(value))


@dataclass(frozen=True)
class NormalizedLegacyDisposition:
    legacy_disposition: str
    legacy_actions: tuple[str, ...]
    normalized_dispositions: tuple[RetraceDisposition, ...]
    execution_steps: tuple[str, ...]
    primary_disposition: RetraceDisposition


def normalize_legacy_disposition(
    value: str,
    spec: Mapping[str, object],
    *,
    pr_id: str,
) -> NormalizedLegacyDisposition:
    normalization = _require_mapping(spec.get("legacy_normalization"), "legacy_normalization")
    rules = _require_mapping(normalization.get("atomic_rules"), "atomic_rules")
    actions = parse_legacy_actions(value)
    dispositions: list[RetraceDisposition] = []
    execution_steps: list[str] = []
    for action in actions:
        raw_rule = _require_mapping(rules.get(action), f"atomic_rules.{action}")
        for raw_disposition in _require_sequence(
            raw_rule.get("dispositions", ()), f"atomic_rules.{action}.dispositions"
        ):
            try:
                parsed = RetraceDisposition(str(raw_disposition))
            except ValueError as exc:
                raise RetraceContractError(
                    f"unknown normalized disposition {raw_disposition!r}"
                ) from exc
            if parsed not in dispositions:
                dispositions.append(parsed)
        for step in _require_sequence(
            raw_rule.get("execution_steps", ()), f"atomic_rules.{action}.execution_steps"
        ):
            text = str(step)
            if not text:
                raise RetraceContractError("execution step cannot be empty")
            if text not in execution_steps:
                execution_steps.append(text)

    overrides = _require_mapping(
        normalization.get("explicit_current_overrides", {}),
        "explicit_current_overrides",
    )
    if pr_id in overrides:
        override = _require_mapping(overrides[pr_id], f"override.{pr_id}")
        for raw_disposition in _require_sequence(
            override.get("add", ()), f"override.{pr_id}.add"
        ):
            try:
                parsed = RetraceDisposition(str(raw_disposition))
            except ValueError as exc:
                raise RetraceContractError(
                    f"unknown override disposition {raw_disposition!r}"
                ) from exc
            if parsed not in dispositions:
                dispositions.append(parsed)

    if not dispositions:
        raise RetraceContractError(f"{pr_id} normalized to no disposition")
    primary = next((item for item in _PRIMARY_PRECEDENCE if item in dispositions), None)
    if primary is None:  # pragma: no cover - enum totality guard
        raise RetraceContractError(f"{pr_id} lacks a primary disposition")
    return NormalizedLegacyDisposition(
        legacy_disposition=value,
        legacy_actions=actions,
        normalized_dispositions=tuple(dispositions),
        execution_steps=tuple(execution_steps),
        primary_disposition=primary,
    )


def _cards(backlog: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    cards: dict[str, Mapping[str, object]] = {}
    for raw_card in _require_sequence(backlog.get("prs"), "backlog.prs"):
        card = _require_mapping(raw_card, "backlog card")
        pr_id = str(card.get("id", ""))
        if not _INTERNAL_ID_RE.fullmatch(pr_id):
            raise RetraceContractError(f"invalid canonical PR id {pr_id!r}")
        if pr_id in cards:
            raise RetraceContractError(f"duplicate canonical PR id {pr_id}")
        cards[pr_id] = card
    return cards


def historical_and_prospective_ids(
    backlog: Mapping[str, object], spec: Mapping[str, object]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    cards = _cards(backlog)
    historical = tuple(
        sorted(
            (pr_id for pr_id in cards if int(pr_id[3:]) <= 275),
            key=lambda value: int(value[3:]),
        )
    )
    spaces = _require_mapping(spec.get("identity_spaces"), "identity_spaces")
    prospective_spec = _require_mapping(
        spaces.get("prospective_internal"), "identity_spaces.prospective_internal"
    )
    prospective = tuple(str(value) for value in prospective_spec.get("exact_ids", ()))
    if set(historical) & set(prospective):
        raise RetraceContractError("historical and prospective PR spaces overlap")
    later_root_cause = {successor for _node, successor in PR280_ACTIVE_CORE_SUCCESSORS}
    registered_later = set(cards) - set(historical) - set(prospective)
    if registered_later not in (set(), later_root_cause):
        missing = sorted(registered_later - later_root_cause)
        extra = sorted(set(prospective) - set(cards))
        raise RetraceContractError(
            f"canonical PR partition mismatch: missing={missing}, extra={extra}"
        )
    if set(prospective) - set(cards):
        raise RetraceContractError(
            "canonical PR partition is missing prospective work units: "
            f"{sorted(set(prospective) - set(cards))}"
        )
    return historical, prospective


def canonical_status_map(
    status: Mapping[str, object], expected_ids: Iterable[str]
) -> dict[str, dict[str, object]]:
    categories = (
        "completed",
        "blocked",
        "pending",
        "dormant_external",
        "in_progress",
        "background_in_progress",
    )
    by_pr: dict[str, str] = {}
    for category in categories:
        values = status.get(category) or ()
        for value in _require_sequence(values, f"status.{category}"):
            pr_id = str(value)
            if pr_id in by_pr:
                raise RetraceContractError(
                    f"{pr_id} occurs in multiple canonical status categories"
                )
            by_pr[pr_id] = category
    expected = set(expected_ids)
    if set(by_pr) != expected:
        raise RetraceContractError(
            "canonical status is not total over the DAG: "
            f"missing={sorted(expected - set(by_pr))}, extra={sorted(set(by_pr) - expected)}"
        )
    resolutions = _require_mapping(
        status.get("execution_resolutions", {}), "status.execution_resolutions"
    )
    lanes = _require_mapping(status.get("execution_lane", {}), "status.execution_lane")
    result: dict[str, dict[str, object]] = {}
    for pr_id in sorted(expected, key=lambda value: int(value[3:])):
        resolution = resolutions.get(pr_id)
        if resolution is not None:
            resolution = dict(_require_mapping(resolution, f"resolution.{pr_id}"))
        result[pr_id] = {
            "orchestration_status": by_pr[pr_id],
            "execution_lane": lanes.get(pr_id),
            "execution_resolution": resolution,
        }
    return result


def _source_definition(spec: Mapping[str, object], source_id: str) -> Mapping[str, object]:
    intake = _require_mapping(spec.get("source_intake"), "source_intake")
    sources = _require_sequence(intake.get("sources"), "source_intake.sources")
    matches = [
        _require_mapping(source, "source definition")
        for source in sources
        if isinstance(source, Mapping) and source.get("source_id") == source_id
    ]
    if len(matches) != 1:
        raise RetraceContractError(f"expected exactly one source definition {source_id}")
    return matches[0]


def build_internal_ledger(
    *,
    source_csv: Path,
    spec: Mapping[str, object],
    backlog: Mapping[str, object],
    status: Mapping[str, object],
) -> dict[str, object]:
    source = _source_definition(spec, "SRC-PR279-INTERNAL-222")
    expected_hash = _require_digest(source.get("sha256"), "internal source sha256")
    if file_sha256(source_csv) != expected_hash:
        raise RetraceContractError("internal source CSV hash mismatch")
    rows = _csv_rows(source_csv, INTERNAL_CSV_FIELDS)
    expected_count = int(source.get("expected_records", -1))
    if len(rows) != expected_count:
        raise RetraceContractError(
            f"internal source count mismatch: {len(rows)} != {expected_count}"
        )
    return _assemble_internal_ledger(
        rows=rows,
        source=source,
        spec=spec,
        backlog=backlog,
        status=status,
    )


def _assemble_internal_ledger(
    *,
    rows: Sequence[Mapping[str, str]],
    source: Mapping[str, object],
    spec: Mapping[str, object],
    backlog: Mapping[str, object],
    status: Mapping[str, object],
) -> dict[str, object]:
    historical, prospective = historical_and_prospective_ids(backlog, spec)
    cards = _cards(backlog)
    source_ids = [row["pr_id"] for row in rows]
    if len(set(source_ids)) != len(source_ids):
        raise RetraceContractError("internal source contains duplicate PR ids")
    if set(source_ids) != set(historical):
        raise RetraceContractError(
            "internal source is not the exact historical canonical set: "
            f"missing={sorted(set(historical) - set(source_ids))}, "
            f"extra={sorted(set(source_ids) - set(historical))}"
        )
    status_by_pr = canonical_status_map(status, cards)
    records: list[dict[str, object]] = []
    for row in rows:
        pr_id = row["pr_id"]
        normalized = normalize_legacy_disposition(row["disposition"], spec, pr_id=pr_id)
        card = cards[pr_id]
        canonical = status_by_pr[pr_id]
        records.append(
            {
                "internal_pr_id": pr_id,
                "source_fields": row,
                "source_row_sha256": canonical_json_sha256(row),
                "legacy_status_snapshot": row["current_status"],
                "legacy_disposition": normalized.legacy_disposition,
                "legacy_actions": list(normalized.legacy_actions),
                "normalized_dispositions": [
                    item.value for item in normalized.normalized_dispositions
                ],
                "primary_disposition": normalized.primary_disposition.value,
                "execution_steps": list(normalized.execution_steps),
                "canonical_card": {
                    "title": card.get("title"),
                    "owner": card.get("owner"),
                    "depends": list(card.get("depends") or ()),
                    "capability": card.get("capability"),
                    "claim_tier_ceiling": card.get("claim_tier_ceiling"),
                },
                "current_canonical": canonical,
                "status_drifted_from_source": row["current_status"]
                != canonical["orchestration_status"],
            }
        )
    prospective_records = []
    for pr_id in prospective:
        card = cards[pr_id]
        prospective_records.append(
            {
                "internal_pr_id": pr_id,
                "section": "prospective_post275",
                "canonical_card": {
                    "title": card.get("title"),
                    "owner": card.get("owner"),
                    "depends": list(card.get("depends") or ()),
                    "capability": card.get("capability"),
                    "claim_tier_ceiling": card.get("claim_tier_ceiling"),
                },
                "current_canonical": status_by_pr[pr_id],
            }
        )
    return {
        "schema": "htt.pr_retrace_ledger.v1",
        "document_id": "PR279-PR-RETRACE-LEDGER",
        "owner": "COMMON",
        "scope": "historical internal work-unit reverse trace plus prospective separation",
        "allowed_use": "diagnostic recomputation routing only",
        "transfer_source": "preserved per historical work unit",
        "source_identities": [
            {"source_id": source["source_id"], "sha256": source["sha256"]},
            {
                "source_id": "canonical_backlog",
                "semantic_sha256": canonical_json_sha256(backlog),
            },
            {
                "source_id": "canonical_status",
                "semantic_sha256": canonical_json_sha256(status),
            },
        ],
        "assumptions": [
            "Legacy CSV status is historical text; current orchestration status comes only from the canonical SSoT.",
            "Normalized dispositions route work and do not grant scientific capability.",
        ],
        "caveats": [
            "Historical and prospective internal work units are separate sections.",
            "Exact replay identity is not scientific validity or readiness.",
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "claim_effect": "none_diagnostic_recomputation_routing_only",
        "source": {
            "source_id": source["source_id"],
            "filename": source["filename"],
            "sha256": source["sha256"],
            "csv_fields": list(INTERNAL_CSV_FIELDS),
            "trailing_blank_lines": 0,
            "record_count": len(records),
        },
        "canonical_snapshot": {
            "backlog_semantic_sha256": canonical_json_sha256(backlog),
            "status_semantic_sha256": canonical_json_sha256(status),
        },
        "historical_internal_work_units": records,
        "prospective_post275_work_units": prospective_records,
        "summary": {
            "historical_count": len(records),
            "prospective_count": len(prospective_records),
            "status_drift_count": sum(
                bool(record["status_drifted_from_source"]) for record in records
            ),
            "unknown_disposition_count": 0,
            "orphan_work_unit_count": 0,
        },
    }


def build_source_snapshot(
    *,
    internal_csv: Path,
    github_csv: Path,
    redo_campaign_yaml: Path,
    data_group_proposal: Mapping[str, object],
    data_group_proposal_sha256: str,
    spec: Mapping[str, object],
) -> dict[str, object]:
    """Normalize the three read-only inputs into one portable tracked surface."""

    internal_source = _source_definition(spec, "SRC-PR279-INTERNAL-222")
    github_source = _source_definition(spec, "SRC-PR279-GITHUB-366")
    redo_source = _source_definition(spec, "SRC-PR279-REDO-CAMPAIGN")
    source_paths = (
        (internal_csv, internal_source),
        (github_csv, github_source),
        (redo_campaign_yaml, redo_source),
    )
    for path, source in source_paths:
        expected = _require_digest(source.get("sha256"), f"{source['source_id']} sha256")
        if file_sha256(path) != expected:
            raise RetraceContractError(f"{source['source_id']} source hash mismatch")
    internal_rows = _csv_rows(internal_csv, INTERNAL_CSV_FIELDS)
    github_rows = _csv_rows(github_csv, GITHUB_CSV_FIELDS)
    redo = load_yaml_mapping(redo_campaign_yaml)
    selected_redo = {
        "schema": redo.get("schema"),
        "document_id": redo.get("document_id"),
        "date": redo.get("date"),
        "audited_revision": redo.get("audited_revision"),
        "claim_posture": redo.get("claim_posture"),
        "part_IV_redo_campaign": redo.get("part_IV_redo_campaign"),
        "sequencing": redo.get("sequencing"),
    }
    proposal_groups = data_group_proposal.get("data_artifact_groups")
    if not isinstance(proposal_groups, Sequence) or isinstance(
        proposal_groups, (str, bytes)
    ):
        raise RetraceContractError("data-group proposal lacks data_artifact_groups")
    if len(proposal_groups) != 45:
        raise RetraceContractError("data-group proposal must contain exactly 45 groups")
    proposal_file_sha256 = _require_digest(
        data_group_proposal_sha256, "data-group proposal file sha256"
    )
    proposal_assignment_id = str(data_group_proposal.get("assignment_id", ""))
    proposal_context_version = str(data_group_proposal.get("context_version", ""))
    if not proposal_assignment_id or not proposal_context_version:
        raise RetraceContractError(
            "data-group proposal lacks assignment/context identity"
        )
    proposal_fingerprint = str(data_group_proposal.get("evidence_fingerprint", ""))
    return {
        "schema": "htt.pr279_source_snapshot.v1",
        "document_id": "PR279-PORTABLE-NORMALIZED-SOURCE-SNAPSHOT",
        "owner": "COMMON",
        "scope": "PR-279 diagnostic recomputation routing only",
        "allowed_use": "regenerate PR-279 routing outputs; no capability or public-use grant",
        "transfer_source": "mixed_source_identities_preserved_per_derived_row",
        "source_identities": [
            {
                "source_id": source["source_id"],
                "filename": source["filename"],
                "sha256": source["sha256"],
            }
            for source in (internal_source, github_source, redo_source)
        ]
        + [
            {
                "source_id": proposal_assignment_id,
                "context_version": proposal_context_version,
                "sha256": proposal_file_sha256,
            }
        ],
        "claim_tier_ceiling": "diagnostic_only",
        "assumptions": [
            "The two CSV inventories are immutable source snapshots dated 2026-08-02.",
            "Canonical status overlays come from live pr_status.yaml, never the legacy CSV field.",
            "The redo campaign supplies approximate group totals; exact 45 boundaries are a PR-279 normalization.",
        ],
        "caveats": [
            "The original read-only files remain untracked and are not moved, deleted, or unpacked.",
            "The normalized redo payload preserves decision-relevant semantics, not byte-identical YAML layout.",
            "Source identity and routing reproducibility do not establish scientific validity or readiness.",
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py intake",
        "sources": {
            "internal_inventory": {
                "source_id": internal_source["source_id"],
                "filename": internal_source["filename"],
                "sha256": internal_source["sha256"],
                "csv_fields": list(INTERNAL_CSV_FIELDS),
                "trailing_blank_lines": 0,
                "rows": internal_rows,
            },
            "github_inventory": {
                "source_id": github_source["source_id"],
                "filename": github_source["filename"],
                "sha256": github_source["sha256"],
                "csv_fields": list(GITHUB_CSV_FIELDS),
                "trailing_blank_lines": 1,
                "rows": github_rows,
            },
            "redo_campaign": {
                "source_id": redo_source["source_id"],
                "filename": redo_source["filename"],
                "sha256": redo_source["sha256"],
                "normalized_semantic_payload": selected_redo,
                "normalized_semantic_sha256": canonical_json_sha256(selected_redo),
            },
        },
        "data_group_normalization": {
            "status": "PR279_EXACTIZATION_OF_APPROXIMATE_SOURCE_GROUPS",
            "proposal_assignment_id": proposal_assignment_id,
            "proposal_context_version": proposal_context_version,
            "proposal_file_sha256": proposal_file_sha256,
            "proposal_semantic_sha256": canonical_json_sha256(data_group_proposal),
            "proposal_evidence_fingerprint": proposal_fingerprint,
            "groups": [dict(_require_mapping(row, "data proposal row")) for row in proposal_groups],
            "groups_semantic_sha256": canonical_json_sha256(
                [
                    dict(_require_mapping(row, "data proposal row"))
                    for row in proposal_groups
                ]
            ),
        },
    }


def validate_source_snapshot(
    snapshot: Mapping[str, object], *, spec: Mapping[str, object]
) -> None:
    validate_output_metadata(snapshot)
    if snapshot.get("schema") != "htt.pr279_source_snapshot.v1":
        raise RetraceContractError("unknown PR-279 source snapshot schema")
    exact_top_level_keys = {
        "schema",
        "document_id",
        "owner",
        "scope",
        "allowed_use",
        "transfer_source",
        "source_identities",
        "claim_tier_ceiling",
        "assumptions",
        "caveats",
        "generating_procedure",
        "sources",
        "data_group_normalization",
    }
    if set(snapshot) != exact_top_level_keys:
        raise RetraceContractError("portable source snapshot top-level contract drifted")
    exact_metadata = {
        "document_id": "PR279-PORTABLE-NORMALIZED-SOURCE-SNAPSHOT",
        "owner": "COMMON",
        "scope": "PR-279 diagnostic recomputation routing only",
        "allowed_use": "regenerate PR-279 routing outputs; no capability or public-use grant",
        "transfer_source": "mixed_source_identities_preserved_per_derived_row",
        "claim_tier_ceiling": "diagnostic_only",
        "assumptions": [
            "The two CSV inventories are immutable source snapshots dated 2026-08-02.",
            "Canonical status overlays come from live pr_status.yaml, never the legacy CSV field.",
            "The redo campaign supplies approximate group totals; exact 45 boundaries are a PR-279 normalization.",
        ],
        "caveats": [
            "The original read-only files remain untracked and are not moved, deleted, or unpacked.",
            "The normalized redo payload preserves decision-relevant semantics, not byte-identical YAML layout.",
            "Source identity and routing reproducibility do not establish scientific validity or readiness.",
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py intake",
    }
    if any(snapshot.get(field) != value for field, value in exact_metadata.items()):
        raise RetraceContractError("portable source snapshot metadata drifted")
    sources = _require_mapping(snapshot.get("sources"), "snapshot.sources")
    if set(sources) != {"internal_inventory", "github_inventory", "redo_campaign"}:
        raise RetraceContractError("portable source snapshot source set drifted")
    definitions = (
        (
            "internal_inventory",
            "SRC-PR279-INTERNAL-222",
            INTERNAL_CSV_FIELDS,
            0,
        ),
        (
            "github_inventory",
            "SRC-PR279-GITHUB-366",
            GITHUB_CSV_FIELDS,
            1,
        ),
    )
    for key, source_id, expected_fields, trailing_blank_lines in definitions:
        source = _require_mapping(sources.get(key), f"snapshot.sources.{key}")
        if set(source) != {
            "source_id",
            "filename",
            "sha256",
            "csv_fields",
            "trailing_blank_lines",
            "rows",
        }:
            raise RetraceContractError(f"{key} source contract drifted")
        definition = _source_definition(spec, source_id)
        if source.get("source_id") != source_id or source.get("sha256") != definition.get(
            "sha256"
        ):
            raise RetraceContractError(f"{key} source identity differs from spec")
        if source.get("filename") != definition.get("filename"):
            raise RetraceContractError(f"{key} source filename differs from spec")
        if source.get("trailing_blank_lines") != trailing_blank_lines:
            raise RetraceContractError(f"{key} source newline convention drifted")
        fields = tuple(str(value) for value in source.get("csv_fields", ()))
        if fields != tuple(expected_fields):
            raise RetraceContractError(f"{key} source fields differ from spec")
        rows = _require_sequence(source.get("rows"), f"{key}.rows")
        if len(rows) != int(definition.get("expected_records", -1)):
            raise RetraceContractError(f"{key} source record count differs from spec")
        reconstructed = reconstruct_csv_bytes(
            [_require_mapping(row, f"{key}.row") for row in rows],
            fields,
            trailing_blank_lines=int(source.get("trailing_blank_lines", 0)),
        )
        if _digest(reconstructed) != source.get("sha256"):
            raise RetraceContractError(f"{key} rows do not reconstruct source bytes")
    redo = _require_mapping(sources.get("redo_campaign"), "snapshot.sources.redo_campaign")
    definition = _source_definition(spec, "SRC-PR279-REDO-CAMPAIGN")
    if (
        set(redo)
        != {
            "source_id",
            "filename",
            "sha256",
            "normalized_semantic_payload",
            "normalized_semantic_sha256",
        }
        or redo.get("source_id") != definition.get("source_id")
        or redo.get("filename") != definition.get("filename")
        or redo.get("sha256") != definition.get("sha256")
    ):
        raise RetraceContractError("redo campaign source identity differs from spec")
    payload = _require_mapping(
        redo.get("normalized_semantic_payload"), "redo normalized semantic payload"
    )
    if (
        canonical_json_sha256(payload) != redo.get("normalized_semantic_sha256")
        or redo.get("normalized_semantic_sha256")
        != definition.get("normalized_semantic_sha256")
    ):
        raise RetraceContractError("redo normalized semantic payload fingerprint mismatch")
    grouping = _require_mapping(
        snapshot.get("data_group_normalization"), "data_group_normalization"
    )
    groups = _require_sequence(grouping.get("groups"), "data_group_normalization.groups")
    source_intake = _require_mapping(spec.get("source_intake"), "spec.source_intake")
    proposal_authority = _require_mapping(
        source_intake.get("data_group_proposal"),
        "spec.source_intake.data_group_proposal",
    )
    expected_source_identities = [
        {
            "source_id": source_definition["source_id"],
            "filename": source_definition["filename"],
            "sha256": source_definition["sha256"],
        }
        for source_definition in (
            _source_definition(spec, "SRC-PR279-INTERNAL-222"),
            _source_definition(spec, "SRC-PR279-GITHUB-366"),
            _source_definition(spec, "SRC-PR279-REDO-CAMPAIGN"),
        )
    ] + [
        {
            "source_id": proposal_authority["assignment_id"],
            "context_version": proposal_authority["context_version"],
            "sha256": proposal_authority["file_sha256"],
        }
    ]
    if snapshot.get("source_identities") != expected_source_identities:
        raise RetraceContractError("portable source snapshot source identities drifted")
    if (
        set(grouping)
        != {
            "status",
            "proposal_assignment_id",
            "proposal_context_version",
            "proposal_file_sha256",
            "proposal_semantic_sha256",
            "proposal_evidence_fingerprint",
            "groups",
            "groups_semantic_sha256",
        }
        or grouping.get("status")
        != "PR279_EXACTIZATION_OF_APPROXIMATE_SOURCE_GROUPS"
    ):
        raise RetraceContractError("data-group normalization contract drifted")
    expected_group_count = int(proposal_authority.get("expected_groups", -1))
    if len(groups) != expected_group_count:
        raise RetraceContractError(
            "portable source snapshot has the wrong normalized group count"
        )
    expected_proposal_file_sha256 = _require_digest(
        proposal_authority.get("file_sha256"),
        "spec data-group proposal file sha256",
    )
    expected_proposal_semantic_sha256 = _require_digest(
        proposal_authority.get("semantic_sha256"),
        "spec data-group proposal semantic sha256",
    )
    expected_groups_semantic_sha256 = _require_digest(
        proposal_authority.get("groups_semantic_sha256"),
        "spec data-group groups semantic sha256",
    )
    if grouping.get("proposal_file_sha256") != expected_proposal_file_sha256:
        raise RetraceContractError("data-group proposal file identity differs from spec")
    if (
        grouping.get("proposal_semantic_sha256")
        != expected_proposal_semantic_sha256
    ):
        raise RetraceContractError("data-group proposal semantic identity differs from spec")
    groups_semantic_sha256 = _require_digest(
        grouping.get("groups_semantic_sha256"),
        "data-group groups semantic sha256",
    )
    if groups_semantic_sha256 != expected_groups_semantic_sha256:
        raise RetraceContractError("data-group row identity differs from spec")
    if canonical_json_sha256(
        [dict(_require_mapping(row, "data group")) for row in groups]
    ) != groups_semantic_sha256:
        raise RetraceContractError("embedded data-group proposal rows drifted")
    expected_provenance = {
        "proposal_assignment_id": proposal_authority.get("assignment_id"),
        "proposal_context_version": proposal_authority.get("context_version"),
        "proposal_evidence_fingerprint": proposal_authority.get(
            "evidence_fingerprint"
        ),
    }
    for field, expected in expected_provenance.items():
        if not isinstance(expected, str) or not expected or grouping.get(field) != expected:
            raise RetraceContractError(
                f"data-group proposal provenance field {field} differs from spec"
            )


def build_internal_ledger_from_snapshot(
    *,
    snapshot: Mapping[str, object],
    spec: Mapping[str, object],
    backlog: Mapping[str, object],
    status: Mapping[str, object],
) -> dict[str, object]:
    validate_source_snapshot(snapshot, spec=spec)
    source = _require_mapping(
        _require_mapping(snapshot["sources"], "sources")["internal_inventory"],
        "internal_inventory",
    )
    rows = [
        {str(key): str(value) for key, value in _require_mapping(row, "internal row").items()}
        for row in _require_sequence(source["rows"], "internal rows")
    ]
    definition = _source_definition(spec, "SRC-PR279-INTERNAL-222")
    return _assemble_internal_ledger(
        rows=rows,
        source=definition,
        spec=spec,
        backlog=backlog,
        status=status,
    )


def build_github_index(
    *, source_csv: Path, spec: Mapping[str, object]
) -> dict[str, object]:
    source = _source_definition(spec, "SRC-PR279-GITHUB-366")
    expected_hash = _require_digest(source.get("sha256"), "GitHub source sha256")
    if file_sha256(source_csv) != expected_hash:
        raise RetraceContractError("GitHub source CSV hash mismatch")
    rows = _csv_rows(source_csv, GITHUB_CSV_FIELDS)
    expected_count = int(source.get("expected_records", -1))
    if len(rows) != expected_count:
        raise RetraceContractError(
            f"GitHub source count mismatch: {len(rows)} != {expected_count}"
        )
    records: list[dict[str, object]] = []
    numbers: list[int] = []
    for row in rows:
        try:
            number = int(row["github_pr"])
        except ValueError as exc:
            raise RetraceContractError("GitHub PR number must be integral") from exc
        numbers.append(number)
        records.append(
            {
                "github_record_id": f"GITHUB-PR-{number:04d}",
                "source_fields": row,
                "source_row_sha256": canonical_json_sha256(row),
            }
        )
    if numbers != list(range(2, 368)):
        raise RetraceContractError("GitHub source must contain the contiguous range 2..367")
    return {
        "schema": "htt.github_publication_review_index.v1",
        "document_id": "PR279-GITHUB-PUBLICATION-REVIEW-INDEX",
        "owner": "COMMON",
        "scope": "GitHub publication and review records separate from internal work units",
        "allowed_use": "lineage inventory and cross-reference only",
        "transfer_source": "not_applicable",
        "source_identities": [
            {"source_id": source["source_id"], "sha256": expected_hash}
        ],
        "assumptions": [
            "GitHub numeric identifiers are never internal work-unit identities."
        ],
        "caveats": [
            "This index records publication/review lineage and grants no capability or approval."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "identity_space": "github_publication_review_not_internal_work_unit",
        "cross_space_rule": "numeric_equality_never_implies_identity_equality",
        "source": {
            "source_id": source["source_id"],
            "filename": source["filename"],
            "sha256": expected_hash,
            "csv_fields": list(GITHUB_CSV_FIELDS),
            "trailing_blank_lines": 1,
            "record_count": len(records),
        },
        "records": records,
        "summary": {
            "record_count": len(records),
            "first_id": records[0]["github_record_id"],
            "last_id": records[-1]["github_record_id"],
            "internal_identity_conflation_count": 0,
        },
    }


def build_github_index_from_snapshot(
    *, snapshot: Mapping[str, object], spec: Mapping[str, object]
) -> dict[str, object]:
    validate_source_snapshot(snapshot, spec=spec)
    source = _require_mapping(
        _require_mapping(snapshot["sources"], "sources")["github_inventory"],
        "github_inventory",
    )
    rows = [
        {str(key): str(value) for key, value in _require_mapping(row, "GitHub row").items()}
        for row in _require_sequence(source["rows"], "GitHub rows")
    ]
    records: list[dict[str, object]] = []
    numbers: list[int] = []
    for row in rows:
        number = int(row["github_pr"])
        numbers.append(number)
        records.append(
            {
                "github_record_id": f"GITHUB-PR-{number:04d}",
                "source_fields": row,
                "source_row_sha256": canonical_json_sha256(row),
            }
        )
    if numbers != list(range(2, 368)):
        raise RetraceContractError("GitHub snapshot must contain contiguous range 2..367")
    definition = _source_definition(spec, "SRC-PR279-GITHUB-366")
    return {
        "schema": "htt.github_publication_review_index.v1",
        "document_id": "PR279-GITHUB-PUBLICATION-REVIEW-INDEX",
        "owner": "COMMON",
        "scope": "GitHub publication and review records separate from internal work units",
        "allowed_use": "lineage inventory and cross-reference only",
        "transfer_source": "not_applicable",
        "source_identities": [
            {"source_id": definition["source_id"], "sha256": definition["sha256"]}
        ],
        "assumptions": [
            "GitHub numeric identifiers are never internal work-unit identities."
        ],
        "caveats": [
            "This index records publication/review lineage and grants no capability or approval."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "identity_space": "github_publication_review_not_internal_work_unit",
        "cross_space_rule": "numeric_equality_never_implies_identity_equality",
        "source": {
            "source_id": definition["source_id"],
            "filename": definition["filename"],
            "sha256": definition["sha256"],
            "csv_fields": list(GITHUB_CSV_FIELDS),
            "trailing_blank_lines": 1,
            "record_count": len(records),
        },
        "records": records,
        "summary": {
            "record_count": len(records),
            "first_id": records[0]["github_record_id"],
            "last_id": records[-1]["github_record_id"],
            "internal_identity_conflation_count": 0,
        },
    }


def _validate_source_reconstruction(
    document: Mapping[str, object], *, expected_fields: Sequence[str], records_key: str
) -> None:
    source = _require_mapping(document.get("source"), "document.source")
    fields = tuple(str(value) for value in source.get("csv_fields", ()))
    if fields != tuple(expected_fields):
        raise RetraceContractError("tracked source header differs from the registered header")
    records = _require_sequence(document.get(records_key), records_key)
    source_rows: list[Mapping[str, object]] = []
    for raw_record in records:
        record = _require_mapping(raw_record, "source record")
        row = _require_mapping(record.get("source_fields"), "source_fields")
        if canonical_json_sha256(row) != record.get("source_row_sha256"):
            raise RetraceContractError("source row fingerprint mismatch")
        source_rows.append(row)
    reconstructed = reconstruct_csv_bytes(
        source_rows,
        fields,
        trailing_blank_lines=int(source.get("trailing_blank_lines", 0)),
    )
    if _digest(reconstructed) != _require_digest(source.get("sha256"), "source.sha256"):
        raise RetraceContractError("tracked normalized rows do not reconstruct source bytes")


def validate_internal_ledger(
    ledger: Mapping[str, object],
    *,
    snapshot: Mapping[str, object],
    spec: Mapping[str, object],
    backlog: Mapping[str, object],
    status: Mapping[str, object],
) -> None:
    validate_output_metadata(ledger)
    if ledger.get("schema") != "htt.pr_retrace_ledger.v1":
        raise RetraceContractError("unknown PR retrace ledger schema")
    _validate_source_reconstruction(
        ledger,
        expected_fields=INTERNAL_CSV_FIELDS,
        records_key="historical_internal_work_units",
    )
    historical, prospective = historical_and_prospective_ids(backlog, spec)
    records = _require_sequence(
        ledger.get("historical_internal_work_units"), "historical_internal_work_units"
    )
    record_ids = [
        str(_require_mapping(record, "historical record").get("internal_pr_id"))
        for record in records
    ]
    if tuple(record_ids) != historical:
        raise RetraceContractError("historical ledger order/set differs from canonical scope")
    prospective_records = _require_sequence(
        ledger.get("prospective_post275_work_units"), "prospective_post275_work_units"
    )
    prospective_ids = tuple(
        str(_require_mapping(record, "prospective record").get("internal_pr_id"))
        for record in prospective_records
    )
    if prospective_ids != prospective:
        raise RetraceContractError("prospective ledger differs from PR-276..294")
    status_by_pr = canonical_status_map(status, _cards(backlog))
    cards = _cards(backlog)
    for raw_record in records:
        record = _require_mapping(raw_record, "historical record")
        pr_id = str(record["internal_pr_id"])
        source_fields = _require_mapping(record["source_fields"], "source_fields")
        normalized = normalize_legacy_disposition(
            str(source_fields["disposition"]), spec, pr_id=pr_id
        )
        expected_dispositions = [item.value for item in normalized.normalized_dispositions]
        if record.get("legacy_actions") != list(normalized.legacy_actions):
            raise RetraceContractError(f"{pr_id} legacy action mapping drifted")
        if record.get("normalized_dispositions") != expected_dispositions:
            raise RetraceContractError(f"{pr_id} normalized disposition mapping drifted")
        if record.get("primary_disposition") != normalized.primary_disposition.value:
            raise RetraceContractError(f"{pr_id} primary disposition drifted")
        if record.get("execution_steps") != list(normalized.execution_steps):
            raise RetraceContractError(f"{pr_id} execution steps drifted")
        if record.get("current_canonical") != status_by_pr[pr_id]:
            raise RetraceContractError(f"{pr_id} canonical status overlay is stale")
        card = _require_mapping(record.get("canonical_card"), "canonical_card")
        if card.get("title") != cards[pr_id].get("title"):
            raise RetraceContractError(f"{pr_id} canonical title drifted")
    for raw_record in prospective_records:
        record = _require_mapping(raw_record, "prospective record")
        pr_id = str(record["internal_pr_id"])
        if record.get("current_canonical") != status_by_pr[pr_id]:
            raise RetraceContractError(f"{pr_id} prospective status overlay is stale")
    expected_ledger = build_internal_ledger_from_snapshot(
        snapshot=snapshot,
        spec=spec,
        backlog=backlog,
        status=status,
    )
    if ledger != expected_ledger:
        raise RetraceContractError(
            "internal ledger differs from its exact snapshot, DAG, and status projection"
        )


def validate_github_index(
    document: Mapping[str, object],
    *,
    snapshot: Mapping[str, object],
    spec: Mapping[str, object],
) -> None:
    validate_output_metadata(document)
    if document.get("schema") != "htt.github_publication_review_index.v1":
        raise RetraceContractError("unknown GitHub index schema")
    _validate_source_reconstruction(
        document, expected_fields=GITHUB_CSV_FIELDS, records_key="records"
    )
    records = _require_sequence(document.get("records"), "records")
    expected_ids = [f"GITHUB-PR-{number:04d}" for number in range(2, 368)]
    ids = [str(_require_mapping(record, "GitHub record").get("github_record_id")) for record in records]
    if ids != expected_ids:
        raise RetraceContractError("GitHub record ids are not the exact contiguous identity set")
    if any(not _GITHUB_ID_RE.fullmatch(value) for value in ids):
        raise RetraceContractError("GitHub record escaped its separate identity namespace")
    source = _source_definition(spec, "SRC-PR279-GITHUB-366")
    if _require_mapping(document.get("source"), "source").get("sha256") != source.get(
        "sha256"
    ):
        raise RetraceContractError("GitHub index source identity differs from spec")
    expected_document = build_github_index_from_snapshot(
        snapshot=snapshot, spec=spec
    )
    if document != expected_document:
        raise RetraceContractError(
            "GitHub index differs from its exact portable-snapshot projection"
        )


def route_id(disposition: str | RetraceDisposition) -> str:
    parsed = (
        disposition
        if isinstance(disposition, RetraceDisposition)
        else RetraceDisposition(disposition)
    )
    return f"ROUTE-{parsed.value}"


def validate_data_artifact_inventory(
    inventory: Mapping[str, object],
    *,
    repo_root: Path,
    spec: Mapping[str, object],
    snapshot: Mapping[str, object],
) -> None:
    validate_output_metadata(inventory)
    if inventory.get("schema") != "htt.data_artifact_disposition.v1":
        raise RetraceContractError("unknown data artifact inventory schema")
    rows = _require_sequence(inventory.get("artifacts"), "artifacts")
    scope = _require_mapping(spec.get("data_artifact_scope"), "data_artifact_scope")
    expected_totals = {
        str(key): int(value)
        for key, value in _require_mapping(
            scope.get("expected_totals"), "data_artifact_scope.expected_totals"
        ).items()
    }
    required_fields = {
        str(value)
        for value in _require_sequence(
            scope.get("required_fields"), "data_artifact_scope.required_fields"
        )
    }
    counts = {item.value: 0 for item in DataArtifactDisposition}
    ids: set[str] = set()
    all_roots = {
        str(_require_mapping(root, "root").get("root_id"))
        for root in _require_sequence(spec.get("invalidation_roots"), "invalidation_roots")
    }
    for raw_row in rows:
        row = _require_mapping(raw_row, "data artifact")
        artifact_id = str(row.get("artifact_id", ""))
        if not re.fullmatch(r"DATA-ART-[0-9]{3}", artifact_id):
            raise RetraceContractError(f"invalid data artifact id {artifact_id!r}")
        if artifact_id in ids:
            raise RetraceContractError(f"duplicate data artifact id {artifact_id}")
        ids.add(artifact_id)
        missing = required_fields - set(row)
        if missing:
            raise RetraceContractError(
                f"{artifact_id} lacks required fields: {sorted(missing)}"
            )
        if type(row.get("materialized")) is not bool:
            raise RetraceContractError(f"{artifact_id}.materialized must be boolean")
        if not isinstance(row.get("disposition_basis"), str) or not str(
            row.get("disposition_basis")
        ).strip():
            raise RetraceContractError(f"{artifact_id} lacks disposition basis")
        if not isinstance(row.get("recompute_route"), str) or not str(
            row.get("recompute_route")
        ).strip():
            raise RetraceContractError(f"{artifact_id} lacks a named recompute route")
        try:
            disposition = DataArtifactDisposition(str(row.get("disposition")))
        except ValueError as exc:
            raise RetraceContractError(
                f"{artifact_id} has unknown data artifact disposition"
            ) from exc
        counts[disposition.value] += 1
        internal_prs = _require_sequence(row.get("internal_prs"), f"{artifact_id}.internal_prs")
        if not internal_prs or any(not _INTERNAL_ID_RE.fullmatch(str(value)) for value in internal_prs):
            raise RetraceContractError(f"{artifact_id} lacks valid internal PR ownership")
        producers = _require_sequence(row.get("producer_or_source_paths"), f"{artifact_id}.producer_or_source_paths")
        if not producers:
            raise RetraceContractError(f"{artifact_id} lacks a producer or source path")
        for raw_path in producers:
            path = Path(str(raw_path))
            if path.is_absolute() or ".." in path.parts:
                raise RetraceContractError(f"{artifact_id} has an unsafe producer path")
            if not (repo_root / path).is_file():
                raise RetraceContractError(
                    f"{artifact_id} producer/source path does not resolve: {path}"
                )
        consumers = _require_sequence(row.get("consumers"), f"{artifact_id}.consumers")
        if not consumers:
            raise RetraceContractError(f"{artifact_id} has no downstream consumer")
        for raw_path in consumers:
            path = Path(str(raw_path))
            if (
                path.is_absolute()
                or ".." in path.parts
                or not (repo_root / path).is_file()
            ):
                raise RetraceContractError(
                    f"{artifact_id} consumer does not resolve: {path}"
                )
        source_identities = _require_sequence(
            row.get("source_identities"), f"{artifact_id}.source_identities"
        )
        expected_source_identities = {
            (str(path), file_sha256(repo_root / str(path))) for path in producers
        }
        actual_source_identities = {
            (
                str(_require_mapping(item, "source identity").get("path")),
                str(_require_mapping(item, "source identity").get("sha256")),
            )
            for item in source_identities
        }
        if actual_source_identities != expected_source_identities:
            raise RetraceContractError(f"{artifact_id} source identities drifted")
        scientific_owner = row.get("scientific_owner")
        if scientific_owner not in _ACTIVE_SCIENTIFIC_OWNERS | {
            _LEGACY_SCIENTIFIC_OWNER
        }:
            raise RetraceContractError(f"{artifact_id} has an unknown scientific owner")
        downstream = [str(value) for value in row.get("downstream_work_units", ())]
        if any(not _INTERNAL_ID_RE.fullmatch(value) for value in downstream):
            raise RetraceContractError(
                f"{artifact_id} has an invalid downstream work-unit identity"
            )
        roots = {str(value) for value in row.get("invalidation_roots", ())}
        if not roots <= all_roots:
            raise RetraceContractError(
                f"{artifact_id} references unknown roots: {sorted(roots - all_roots)}"
            )
        if disposition is DataArtifactDisposition.PRESERVE and roots:
            raise RetraceContractError(
                f"{artifact_id} cannot be both PRESERVE and actively invalidated"
            )
        normalized = _require_sequence(
            row.get("normalized_dispositions"), f"{artifact_id}.normalized_dispositions"
        )
        if not normalized:
            raise RetraceContractError(f"{artifact_id} lacks a recompute disposition")
        for value in normalized:
            try:
                RetraceDisposition(str(value))
            except ValueError as exc:
                raise RetraceContractError(
                    f"{artifact_id} references unknown recompute disposition {value!r}"
                ) from exc
        if scientific_owner == _LEGACY_SCIENTIFIC_OWNER and (
            disposition is not DataArtifactDisposition.PRESERVE
            or RetraceDisposition.LEGACY_REPRODUCTION_ONLY.value not in normalized
            or row.get("claim_ceiling") != "legacy_reproduction_only"
        ):
            raise RetraceContractError(
                f"{artifact_id} may use TSC_LEGACY only for a preserved "
                "legacy-reproduction route"
            )
        if disposition is DataArtifactDisposition.BLOCKED and not row.get("blocking_event"):
            raise RetraceContractError(f"{artifact_id} BLOCKED row lacks a named event")
        if disposition is not DataArtifactDisposition.BLOCKED and row.get("blocking_event"):
            raise RetraceContractError(
                f"{artifact_id} non-BLOCKED row must not carry a blocking event"
            )
    expected_inventory = build_data_artifact_inventory_from_snapshot(
        snapshot, repo_root=repo_root, spec=spec
    )
    if inventory != expected_inventory:
        raise RetraceContractError(
            "data artifact inventory differs from its exact source-snapshot projection"
        )
        if row.get("claim_ceiling") not in {
            "diagnostic_only",
            "data_transfer_conditional_diagnostic",
            "legacy_reproduction_only",
            "structural_no_go_only",
        }:
            raise RetraceContractError(f"{artifact_id} has an unknown claim ceiling")
    if counts != expected_totals:
        raise RetraceContractError(
            f"data artifact totals mismatch: {counts} != {expected_totals}"
        )


def _artifact_routes(group_id: str, disposition: DataArtifactDisposition) -> list[str]:
    if disposition is DataArtifactDisposition.REDO_REQUIRED:
        if group_id == "DA-R20":
            return [RetraceDisposition.RERUN_FROM_RAW_DATA.value]
        return [
            RetraceDisposition.RERUN_FROM_ADMITTED_SUMMARY.value,
            RetraceDisposition.LEGACY_REPRODUCTION_ONLY.value,
        ]
    if disposition is DataArtifactDisposition.REDO_UPGRADE:
        if group_id in {"DA-U12", "DA-U13", "DA-U14"}:
            return [
                RetraceDisposition.RECALIBRATE_SYNTHETIC.value,
                RetraceDisposition.LEGACY_REPRODUCTION_ONLY.value,
            ]
        return [RetraceDisposition.RERUN_FROM_RAW_DATA.value]
    if disposition is DataArtifactDisposition.PRESERVE:
        if group_id == "DA-P02":
            return [
                RetraceDisposition.STABLE_REPLAY.value,
                RetraceDisposition.LEGACY_REPRODUCTION_ONLY.value,
            ]
        return [RetraceDisposition.STABLE_REPLAY.value]
    return [
        RetraceDisposition.EXTERNAL_BLOCKED.value,
        RetraceDisposition.RERUN_FROM_RAW_DATA.value,
    ]


def _artifact_roots(group_id: str) -> list[str]:
    prefix = group_id[:4]
    index = int(group_id[4:])
    roots: list[str] = []
    if prefix in {"DA-U", "DA-R"}:
        roots.append("ROOT-SCALAR-TO-TYPED-STATE")
    if group_id in {"DA-U01", "DA-U02", "DA-U03", "DA-U04", "DA-U05", "DA-R20"}:
        roots.extend(
            [
                "ROOT-ORBIT-CATALOGUE-V3",
                "ROOT-CONDITIONAL-EXCEEDANCE",
                "ROOT-RESPONSE-GEOMETRY",
                "ROOT-OPEN-SET-CLASS",
                "ROOT-DATA-ADMISSION",
            ]
        )
    if group_id in {"DA-U06", "DA-U07", "DA-U08", "DA-U09", "DA-U10", "DA-U11"}:
        roots.extend(["ROOT-DATA-ADMISSION", "ROOT-CONDITIONAL-EXCEEDANCE"])
    if group_id in {"DA-U09", "DA-U10", "DA-U11"}:
        roots.extend(["ROOT-DEPTH-PATH", "ROOT-RESPONSE-GEOMETRY"])
    if group_id == "DA-U11":
        roots.append("ROOT-CF4-P0-QUARANTINE")
    if group_id in {"DA-U12", "DA-U13", "DA-U14"}:
        roots.extend(["ROOT-MES-REFREEZE", "ROOT-ANCHOR-GEOMETRY"])
    if group_id == "DA-U13":
        roots.extend(["ROOT-RESPONSE-GEOMETRY", "ROOT-OPEN-SET-CLASS"])
    if prefix == "DA-R" and index <= 19:
        roots.extend(
            [
                "ROOT-MES-REFREEZE",
                "ROOT-FRAME-SEPARATION",
                "ROOT-ANCHOR-GEOMETRY",
                "ROOT-CONDITIONAL-EXCEEDANCE",
                "ROOT-DATA-ADMISSION",
            ]
        )
    if group_id in {"DA-R17", "DA-R18", "DA-R19"}:
        roots.extend(
            ["ROOT-DEPTH-PATH", "ROOT-RESPONSE-GEOMETRY", "ROOT-OPEN-SET-CLASS"]
        )
    if group_id in {"DA-B01", "DA-B04", "DA-B06"}:
        roots.extend(
            [
                "ROOT-CF4-P0-QUARANTINE",
                "ROOT-DATA-ADMISSION",
                "ROOT-DEPTH-PATH",
                "ROOT-RESPONSE-GEOMETRY",
            ]
        )
    if group_id in {"DA-B02", "DA-B03"}:
        roots.append("ROOT-DATA-ADMISSION")
    if group_id == "DA-B05":
        roots.extend(
            ["ROOT-DATA-ADMISSION", "ROOT-RESPONSE-GEOMETRY", "ROOT-OPEN-SET-CLASS"]
        )
    return list(dict.fromkeys(roots))


def _normalized_claim_ceiling(
    group_id: str, disposition: DataArtifactDisposition
) -> str:
    if group_id == "DA-P01":
        return "structural_no_go_only"
    if group_id == "DA-P02" or group_id.startswith("DA-R"):
        return "legacy_reproduction_only"
    if disposition in {
        DataArtifactDisposition.REDO_UPGRADE,
        DataArtifactDisposition.BLOCKED,
    }:
        return "data_transfer_conditional_diagnostic"
    return "diagnostic_only"


def _transfer_source(group_id: str) -> str:
    if group_id.startswith("DA-R"):
        return "legacy_external_transfer_conditional_or_not_applicable_per_surface"
    if group_id in {"DA-U12", "DA-U13", "DA-U14"}:
        return "mixed_legacy_transfer_conditional_report_composition"
    if group_id in {"DA-P02"}:
        return "legacy_synthetic_no_native_status"
    if group_id in {"DA-P04"}:
        return "none_exact_algebra"
    return "not_applicable_observer_feature_or_catalogue"


def build_data_artifact_inventory_from_snapshot(
    snapshot: Mapping[str, object], *, repo_root: Path, spec: Mapping[str, object]
) -> dict[str, object]:
    validate_source_snapshot(snapshot, spec=spec)
    grouping = _require_mapping(snapshot["data_group_normalization"], "grouping")
    raw_groups = _require_sequence(grouping["groups"], "grouping.groups")
    artifacts: list[dict[str, object]] = []
    for position, raw_group in enumerate(raw_groups, start=1):
        group = _require_mapping(raw_group, "data group")
        group_id = str(group.get("group_id", ""))
        try:
            disposition = DataArtifactDisposition(str(group.get("disposition")))
        except ValueError as exc:
            raise RetraceContractError(f"{group_id} has unknown disposition") from exc
        source_paths = [str(value) for value in group.get("source_paths", ())]
        consumers: list[str] = []
        downstream_work_units: list[str] = []
        for raw_consumer in group.get("consumers", ()):
            consumer = str(raw_consumer)
            if _INTERNAL_ID_RE.fullmatch(consumer):
                downstream_work_units.append(consumer)
                consumer = "docs/codex_handoff/pr_backlog.yaml"
            if consumer not in consumers:
                consumers.append(consumer)
        internal_prs: list[str] = []
        for value in (
            group.get("internal_pr_owner"),
            *list(group.get("source_work_units", ())),
        ):
            text = str(value)
            if _INTERNAL_ID_RE.fullmatch(text) and text not in internal_prs:
                internal_prs.append(text)
        if not internal_prs:
            raise RetraceContractError(f"{group_id} lacks an internal PR owner")
        materialized = group_id != "DA-B02"
        if group_id in {"DA-U12", "DA-U13", "DA-U14"}:
            artifact_kind = "report_composition_surface"
        elif group_id.startswith("DA-R"):
            artifact_kind = "legacy_inference_or_rendering_surface"
        elif not materialized:
            artifact_kind = "nonmaterialized_execution_target"
        else:
            artifact_kind = "materialized_data_or_method_artifact"
        support = str(group.get("support", ""))
        if disposition is DataArtifactDisposition.BLOCKED:
            basis = "event_blocked"
        elif disposition is DataArtifactDisposition.PRESERVE:
            basis = "policy_preserve"
        elif disposition is DataArtifactDisposition.REDO_REQUIRED:
            basis = (
                "direct_registered_falsification"
                if group_id == "DA-R01"
                else "propagated_or_separate_defect_legacy_only"
            )
        else:
            basis = "typed_migration_target"
        claim_ceiling = _normalized_claim_ceiling(group_id, disposition)
        routes = _artifact_routes(group_id, disposition)
        artifact = {
            "artifact_id": f"DATA-ART-{position:03d}",
            "source_group_id": group_id,
            "name": group.get("name"),
            "artifact_kind": artifact_kind,
            "materialized": materialized,
            "disposition": disposition.value,
            "disposition_basis": basis,
            "owner": "COMMON",
            "scientific_owner": group.get("scientific_owner"),
            "internal_prs": internal_prs,
            "downstream_work_units": downstream_work_units,
            "producer_or_source_paths": source_paths,
            "consumers": consumers,
            "normalized_dispositions": routes,
            "recompute_route": group.get("recompute_route"),
            "blocking_event": group.get("blocking_event"),
            "invalidation_roots": _artifact_roots(group_id),
            "scope": "PR-279 reverse-trace data-artifact group",
            "allowed_use": "recomputation routing diagnostic only",
            "claim_ceiling": claim_ceiling,
            "source_claim_ceiling_label": group.get("claim_ceiling"),
            "transfer_source": _transfer_source(group_id),
            "sky_mask_covariance_null_status": (
                "event_blocked_not_admitted"
                if disposition is DataArtifactDisposition.BLOCKED
                else "must_be_revalidated_by_named_recompute_route"
                if disposition
                in {
                    DataArtifactDisposition.REDO_REQUIRED,
                    DataArtifactDisposition.REDO_UPGRADE,
                }
                else "preserved_under_original_declared_scope_only"
            ),
            "source_identities": [
                {
                    "path": path,
                    "sha256": file_sha256(repo_root / path),
                }
                for path in source_paths
            ],
            "assumptions": [
                "Disposition is orthogonal to readiness, admission, and scientific status.",
                "Every observed rerun requires the named admission and separate execution authorization.",
            ],
            "caveats": [
                support,
                "No PR-279 row grants capability, public use, native status, or family identification.",
            ],
            "generating_procedure": "normalized from SRC-PR279-REDO-CAMPAIGN plus A-PR279-DATA; no observed data executed",
        }
        artifacts.append(artifact)
    inventory = {
        "schema": "htt.data_artifact_disposition.v1",
        "document_id": "PR279-DATA-ARTIFACT-DISPOSITION",
        "owner": "COMMON",
        "scope": "exact 45-group normalization of an approximate source campaign",
        "allowed_use": "recomputation routing diagnostic only",
        "transfer_source": "preserved_per_artifact",
        "source_identities": [
            {
                "source_id": "SRC-PR279-REDO-CAMPAIGN",
                "sha256": _source_definition(spec, "SRC-PR279-REDO-CAMPAIGN")[
                    "sha256"
                ],
            },
            {
                "source_id": "A-PR279-DATA",
                "semantic_sha256": grouping.get("proposal_semantic_sha256"),
            },
        ],
        "assumptions": [
            "The source totals are approximate and do not define the exact group boundaries.",
            "PR-279 selects these 45 boundaries as a normalized routing scope, not historical fact.",
        ],
        "caveats": [
            "Only the shared-cause fitted score is directly falsified; other V1 evidence surfaces use propagated-inference disposition.",
            "REDO_UPGRADE does not imply admission, readiness, calibration, or stronger claims.",
            "DESI BGS_ANY and BGS_BRIGHT-21.5 remain different estimands.",
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "artifacts": artifacts,
        "summary": {
            "artifact_count": len(artifacts),
            "counts": {
                item.value: sum(row["disposition"] == item.value for row in artifacts)
                for item in DataArtifactDisposition
            },
            "unknown_disposition_count": 0,
            "orphan_consumer_count": 0,
        },
    }
    return inventory


def work_unit_roots(record: Mapping[str, object]) -> tuple[str, ...]:
    """Return non-authoritative routing hints from normalized dispositions.

    These hints are deliberately coarse and never instantiate lifecycle
    edges.  PR-277 lifecycle edges are reserved for the explicitly curated
    artifact groups in ``data_artifact_disposition.yaml``.
    """

    dispositions = {
        RetraceDisposition(str(value))
        for value in _require_sequence(
            record.get("normalized_dispositions"), "normalized_dispositions"
        )
    }
    roots: list[str] = []
    if dispositions & {
        RetraceDisposition.RECALIBRATE_SYNTHETIC,
        RetraceDisposition.LEGACY_REPRODUCTION_ONLY,
    }:
        roots.append("ROOT-SCALAR-TO-TYPED-STATE")
    if RetraceDisposition.REPROVE in dispositions:
        roots.append("ROOT-THEOREM-REGISTRY-V3")
    if dispositions & {
        RetraceDisposition.RERUN_FROM_RAW_DATA,
        RetraceDisposition.RERUN_FROM_ADMITTED_SUMMARY,
        RetraceDisposition.EXTERNAL_BLOCKED,
    }:
        roots.append("ROOT-DATA-ADMISSION")
    return tuple(roots)


def build_recompute_matrix(
    ledger: Mapping[str, object], inventory: Mapping[str, object]
) -> dict[str, object]:
    work_units = []
    for raw_record in _require_sequence(
        ledger.get("historical_internal_work_units"), "historical_internal_work_units"
    ):
        record = _require_mapping(raw_record, "historical record")
        primary = str(record["primary_disposition"])
        work_units.append(
            {
                "internal_pr_id": record["internal_pr_id"],
                "primary_disposition": primary,
                "normalized_dispositions": list(record["normalized_dispositions"]),
                "route_id": route_id(primary),
                "execution_steps": list(record["execution_steps"]),
                "start_condition": _require_mapping(
                    record["source_fields"], "source_fields"
                )["start_condition"],
                "routing_root_hints": list(work_unit_roots(record)),
                "routing_root_hints_are_authority": False,
                "current_orchestration_status": _require_mapping(
                    record["current_canonical"], "current_canonical"
                )["orchestration_status"],
            }
        )
    artifacts = []
    for raw_artifact in _require_sequence(inventory.get("artifacts"), "artifacts"):
        artifact = _require_mapping(raw_artifact, "artifact")
        dispositions = [str(value) for value in artifact["normalized_dispositions"]]
        primary = next(
            item.value
            for item in _PRIMARY_PRECEDENCE
            if item.value in dispositions
        )
        artifacts.append(
            {
                "artifact_id": artifact["artifact_id"],
                "disposition": artifact["disposition"],
                "primary_disposition": primary,
                "route_id": route_id(primary),
                "internal_prs": list(artifact["internal_prs"]),
                "blocking_event": artifact.get("blocking_event"),
            }
        )
    return {
        "schema": "htt.pr279_recompute_matrix.v1",
        "document_id": "PR279-RECOMPUTE-MATRIX",
        "owner": "COMMON",
        "scope": "total routing projection for historical work units and normalized data artifacts",
        "allowed_use": "scheduling diagnostic only",
        "transfer_source": "preserved per routed object",
        "source_identities": [
            {
                "ledger_semantic_sha256": canonical_json_sha256(ledger),
                "inventory_semantic_sha256": canonical_json_sha256(inventory),
            }
        ],
        "assumptions": [
            "A route is not execution authorization or capability evidence."
        ],
        "caveats": [
            "Work-unit root hints are coarse routing hints and never PR-277 lifecycle authority."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "claim_effect": "none_routing_only",
        "routes": [
            {
                "route_id": route_id(item),
                "disposition": item.value,
                "capability_effect": "none",
            }
            for item in RetraceDisposition
        ],
        "historical_work_units": work_units,
        "data_artifacts": artifacts,
        "summary": {
            "historical_work_unit_count": len(work_units),
            "data_artifact_count": len(artifacts),
            "unknown_route_count": 0,
            "orphan_route_count": 0,
        },
    }


def build_semantic_invalidation_graph(
    *,
    repo_root: Path,
    spec: Mapping[str, object],
    ledger: Mapping[str, object],
    inventory: Mapping[str, object],
) -> dict[str, object]:
    """Build a typed artifact lifecycle graph and an orthogonal route graph."""

    from common.evidence_graph import (
        EvidenceAxes,
        EvidenceEdge,
        EvidenceEdgeKind,
        EvidenceGraph,
        EvidenceNode,
        EvidenceNodeKind,
        EvidenceStatus,
        ProcessResult,
    )

    roots = [
        dict(_require_mapping(root, "invalidation root"))
        for root in _require_sequence(spec.get("invalidation_roots"), "invalidation_roots")
    ]
    root_by_id = {str(root["root_id"]): root for root in roots}
    if len(root_by_id) != len(roots):
        raise RetraceContractError("duplicate invalidation root")
    claim_node = EvidenceNode(
        kind=EvidenceNodeKind.CLAIM,
        label="C-PR279-REVERSE-TRACE",
        content_sha256=file_sha256(
            repo_root / "docs/research_program/post_pr275/pr279_spec.yaml"
        ),
        axes=EvidenceAxes(
            ProcessResult.PASS, EvidenceStatus.PRESENT, "OPEN"
        ),
        metadata={
            "claim_id": "C-PR279-REVERSE-TRACE",
            "scope": "diagnostic reverse trace and recomputation routing",
            "capability_issuance": "forbidden",
        },
    )
    lifecycle_nodes: list[object] = [claim_node]
    lifecycle_edges: list[object] = []
    authority_node_by_root: dict[str, object] = {}
    reason_ref_by_root: dict[str, str] = {}
    for root in roots:
        root_id = str(root["root_id"])
        authority_path = Path(str(root["authority_path"]))
        reason_ref = file_sha256(repo_root / authority_path)
        node = EvidenceNode(
            kind=EvidenceNodeKind.ARTIFACT,
            label=f"PR279 authority {root_id}",
            content_sha256=reason_ref,
            axes=EvidenceAxes(
                ProcessResult.PASS, EvidenceStatus.PRESENT, "OPEN"
            ),
            metadata={
                "root_id": root_id,
                "authority_path": authority_path.as_posix(),
                "authority_role": str(root["authority_role"]),
                "direct_authority_pr": str(root["direct_authority_pr"]),
            },
        )
        lifecycle_nodes.append(node)
        authority_node_by_root[root_id] = node
        reason_ref_by_root[root_id] = reason_ref

    target_node_by_id: dict[str, object] = {}
    for raw_artifact in _require_sequence(inventory.get("artifacts"), "artifacts"):
        artifact = _require_mapping(raw_artifact, "artifact")
        artifact_id = str(artifact["artifact_id"])
        evidence_status = (
            EvidenceStatus.BLOCKED
            if artifact["disposition"] == DataArtifactDisposition.BLOCKED.value
            else EvidenceStatus.STALE
        )
        identity_payload = {
            "schema": "htt.pr279_data_artifact_identity.v1",
            "artifact_id": artifact_id,
            "source_group_id": artifact["source_group_id"],
            "producer_or_source_paths": list(artifact["producer_or_source_paths"]),
            "internal_prs": list(artifact["internal_prs"]),
            "disposition": artifact["disposition"],
        }
        node = EvidenceNode(
            kind=EvidenceNodeKind.ARTIFACT,
            label=f"PR279 target {artifact_id}",
            content_sha256=canonical_json_sha256(identity_payload),
            axes=EvidenceAxes(ProcessResult.NOT_RUN, evidence_status, "OPEN"),
            metadata={
                "artifact_id": artifact_id,
                "source_group_id": str(artifact["source_group_id"]),
                "disposition": str(artifact["disposition"]),
                "identity_basis": "normalized PR-279 artifact row",
            },
        )
        lifecycle_nodes.append(node)
        target_node_by_id[artifact_id] = node
        for root_id_value in artifact.get("invalidation_roots", ()):
            root_id = str(root_id_value)
            root = root_by_id.get(root_id)
            if root is None:
                raise RetraceContractError(
                    f"{artifact_id} references unknown invalidation root {root_id}"
                )
            raw_kinds = [str(value) for value in root["edge_kinds"]]
            if len(raw_kinds) != 1:
                raise RetraceContractError(
                    f"{root_id} must select exactly one lifecycle edge kind"
                )
            kind = EvidenceEdgeKind(raw_kinds[0].lower())
            lifecycle_edges.append(
                EvidenceEdge(
                    kind=kind,
                    source_ref=authority_node_by_root[root_id].node_ref,
                    target_ref=node.node_ref,
                    metadata={
                        "affected_capabilities": list(
                            root["affected_capabilities"]
                        ),
                        "reason_ref": reason_ref_by_root[root_id],
                    },
                )
            )

    typed_graph = EvidenceGraph(nodes=lifecycle_nodes, edges=lifecycle_edges)

    route_nodes: list[dict[str, object]] = [
        {
            "node_id": route_id(disposition),
            "kind": "recompute_route",
            "disposition": disposition.value,
        }
        for disposition in RetraceDisposition
    ]
    route_edges: list[dict[str, object]] = []
    for raw_record in _require_sequence(
        ledger.get("historical_internal_work_units"), "historical_internal_work_units"
    ):
        record = _require_mapping(raw_record, "historical record")
        pr_id = str(record["internal_pr_id"])
        route_nodes.append({"node_id": pr_id, "kind": "internal_work_unit"})
        route_edges.append(
            {
                "edge_id": f"EDGE-{pr_id}-ROUTE",
                "kind": "ROUTED_TO",
                "source": pr_id,
                "target": route_id(str(record["primary_disposition"])),
            }
        )
    consumers: set[str] = set()
    for raw_artifact in _require_sequence(inventory.get("artifacts"), "artifacts"):
        artifact = _require_mapping(raw_artifact, "artifact")
        artifact_id = str(artifact["artifact_id"])
        route_nodes.append(
            {"node_id": artifact_id, "kind": "data_artifact_group"}
        )
        dispositions = [str(value) for value in artifact["normalized_dispositions"]]
        primary = next(item.value for item in _PRIMARY_PRECEDENCE if item.value in dispositions)
        route_edges.append(
            {
                "edge_id": f"EDGE-{artifact_id}-ROUTE",
                "kind": "ROUTED_TO",
                "source": artifact_id,
                "target": route_id(primary),
            }
        )
        for path in artifact["consumers"]:
            consumer_id = f"CONSUMER-{canonical_json_sha256(str(path))[:16]}"
            if consumer_id not in consumers:
                consumers.add(consumer_id)
                route_nodes.append(
                    {"node_id": consumer_id, "kind": "consumer", "path": str(path)}
                )
            route_edges.append(
                {
                    "edge_id": f"EDGE-{artifact_id}-{consumer_id}",
                    "kind": "CONSUMED_BY",
                    "source": artifact_id,
                    "target": consumer_id,
                }
            )
    root_index = []
    for root_id, root in root_by_id.items():
        authority_node = authority_node_by_root[root_id]
        root_edges = [
            edge
            for edge in typed_graph.edges
            if edge.source_ref == authority_node.node_ref
        ]
        root_index.append(
            {
                "root_id": root_id,
                "current_activation": root.get(
                    "current_activation", "ACTIVE_TARGETS_REQUIRED"
                ),
                "authority_node_ref": authority_node.node_ref,
                "target_node_refs": [edge.target_ref for edge in root_edges],
                "edge_refs": [edge.edge_ref for edge in root_edges],
                "affected_capabilities": list(root["affected_capabilities"]),
                "reason_ref": reason_ref_by_root[root_id],
            }
        )

    return {
        "schema": "htt.pr279_semantic_invalidation_graph.v1",
        "owner": "COMMON",
        "scope": "typed artifact invalidation plus non-authoritative scheduling projection",
        "allowed_use": "diagnostic recomputation routing only",
        "transfer_source": "preserved per target artifact; no native transfer status",
        "source_identities": [
            {
                "root_id": row["root_id"],
                "reason_ref": row["reason_ref"],
            }
            for row in root_index
        ],
        "assumptions": [
            "Only curated artifact rows instantiate PR-277 lifecycle edges.",
            "Internal work-unit routes do not enter capability closure.",
        ],
        "caveats": [
            "Graph closure is not scientific validity, readiness, or publication approval."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "authority_model": "pr277_typed_lifecycle_plus_separate_route_projection",
        "capability_issuance": "forbidden",
        "typed_lifecycle_graph": typed_graph.to_record(),
        "root_index": root_index,
        "routing_projection": {
            "authority": "none_routing_only",
            "nodes": route_nodes,
            "relations": route_edges,
        },
        "summary": {
            "lifecycle_node_count": len(typed_graph.nodes),
            "lifecycle_edge_count": len(typed_graph.edges),
            "routing_node_count": len(route_nodes),
            "routing_relation_count": len(route_edges),
            "invalidation_root_count": len(roots),
            "historical_work_unit_count": 222,
            "data_artifact_count": len(target_node_by_id),
            "recompute_route_count": len(RetraceDisposition),
            "consumer_count": len(consumers),
            "orphan_node_count": 0,
            "unknown_edge_kind_count": 0,
        },
    }


def validate_semantic_invalidation_graph(
    graph: Mapping[str, object],
    *,
    repo_root: Path,
    spec: Mapping[str, object],
    ledger: Mapping[str, object],
    inventory: Mapping[str, object],
) -> None:
    from common.evidence_graph import EvidenceEdgeKind, EvidenceGraph

    if graph.get("schema") != "htt.pr279_semantic_invalidation_graph.v1":
        raise RetraceContractError("unknown semantic invalidation graph schema")
    validate_output_metadata(graph)
    if graph.get("capability_issuance") != "forbidden":
        raise RetraceContractError("PR-279 graph cannot issue capability decisions")
    raw_typed = _require_mapping(
        graph.get("typed_lifecycle_graph"), "typed_lifecycle_graph"
    )
    try:
        typed = EvidenceGraph.from_record(raw_typed)
    except ValueError as exc:
        raise RetraceContractError("invalid PR-277 typed lifecycle graph") from exc
    root_index = _require_sequence(graph.get("root_index"), "root_index")
    roots = {
        str(_require_mapping(root, "root").get("root_id")): _require_mapping(
            root, "root"
        )
        for root in _require_sequence(spec.get("invalidation_roots"), "invalidation_roots")
    }
    if len(roots) != 12 or len(root_index) != len(roots):
        raise RetraceContractError("semantic graph requires the exact 12 roots")
    typed_node_refs = {node.node_ref for node in typed.nodes}
    typed_edge_refs = {edge.edge_ref for edge in typed.edges}
    seen_roots: set[str] = set()
    for raw_row in root_index:
        row = _require_mapping(raw_row, "root_index row")
        root_id = str(row.get("root_id"))
        if root_id not in roots or root_id in seen_roots:
            raise RetraceContractError(f"unknown or duplicate root index {root_id}")
        seen_roots.add(root_id)
        authority_ref = str(row.get("authority_node_ref"))
        target_refs = [str(value) for value in row.get("target_node_refs", ())]
        edge_refs = [str(value) for value in row.get("edge_refs", ())]
        expected_activation = str(
            roots[root_id].get("current_activation", "ACTIVE_TARGETS_REQUIRED")
        )
        if row.get("current_activation") != expected_activation:
            raise RetraceContractError(f"{root_id} activation status drifted")
        if authority_ref not in typed_node_refs:
            raise RetraceContractError(f"{root_id} lacks a typed authority node")
        if expected_activation == "ACTIVE_TARGETS_REQUIRED":
            if not target_refs or not edge_refs:
                raise RetraceContractError(f"{root_id} lacks typed lifecycle targets")
        elif expected_activation == "DORMANT_NO_CURRENT_TARGETS":
            if target_refs or edge_refs:
                raise RetraceContractError(
                    f"{root_id} dormant authority cannot carry active lifecycle edges"
                )
        else:
            raise RetraceContractError(f"{root_id} has unknown activation status")
        if not set(target_refs) <= typed_node_refs or not set(edge_refs) <= typed_edge_refs:
            raise RetraceContractError(f"{root_id} contains orphan typed references")
        expected_capabilities = sorted(
            str(value) for value in roots[root_id]["affected_capabilities"]
        )
        if sorted(str(value) for value in row.get("affected_capabilities", ())) != expected_capabilities:
            raise RetraceContractError(f"{root_id} capability scope drifted")
        if row.get("reason_ref") != file_sha256(
            repo_root / Path(str(roots[root_id]["authority_path"]))
        ):
            raise RetraceContractError(f"{root_id} authority reason_ref drifted")
        matched = [edge for edge in typed.edges if edge.edge_ref in edge_refs]
        outgoing = [edge for edge in typed.edges if edge.source_ref == authority_ref]
        if set(edge_refs) != {edge.edge_ref for edge in outgoing} or set(
            target_refs
        ) != {edge.target_ref for edge in outgoing}:
            raise RetraceContractError(f"{root_id} root index is not total")
        if any(
            edge.source_ref != authority_ref
            or edge.target_ref not in target_refs
            or edge.kind
            not in {
                EvidenceEdgeKind.REQUIRES_RECALIBRATION,
                EvidenceEdgeKind.REQUIRES_REEXECUTION,
            }
            or sorted(str(value) for value in edge.metadata["affected_capabilities"])
            != expected_capabilities
            or edge.metadata["reason_ref"] != row.get("reason_ref")
            for edge in matched
        ):
            raise RetraceContractError(f"{root_id} lifecycle edge projection drifted")
    if seen_roots != set(roots):
        raise RetraceContractError("semantic graph does not cover every root")

    routing = _require_mapping(graph.get("routing_projection"), "routing_projection")
    nodes = _require_sequence(routing.get("nodes"), "routing_projection.nodes")
    node_ids = [str(_require_mapping(node, "node").get("node_id")) for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise RetraceContractError("semantic invalidation graph has duplicate nodes")
    node_set = set(node_ids)
    node_kind = {
        str(_require_mapping(node, "node").get("node_id")): str(
            _require_mapping(node, "node").get("kind")
        )
        for node in nodes
    }
    edges = _require_sequence(routing.get("relations"), "routing_projection.relations")
    edge_ids: set[str] = set()
    for raw_edge in edges:
        edge = _require_mapping(raw_edge, "edge")
        edge_id = str(edge.get("edge_id"))
        if edge_id in edge_ids:
            raise RetraceContractError(f"duplicate semantic edge {edge_id}")
        edge_ids.add(edge_id)
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        if source not in node_set or target not in node_set:
            raise RetraceContractError(f"orphan semantic edge {edge_id}")
        kind = str(edge.get("kind"))
        if kind not in {"ROUTED_TO", "CONSUMED_BY"}:
            raise RetraceContractError(f"lifecycle semantics leaked into route graph: {kind}")
        if kind == "ROUTED_TO" and (
            node_kind[source] not in {"internal_work_unit", "data_artifact_group"}
            or node_kind[target] != "recompute_route"
        ):
            raise RetraceContractError(f"invalid ROUTED_TO endpoints in {edge_id}")
        if kind == "CONSUMED_BY" and (
            node_kind[source] != "data_artifact_group"
            or node_kind[target] != "consumer"
        ):
            raise RetraceContractError(f"invalid CONSUMED_BY endpoints in {edge_id}")
    consumer_nodes = {
        node_id
        for node_id, raw_node in zip(node_ids, nodes)
        if _require_mapping(raw_node, "node").get("kind") == "consumer"
    }
    consumed_targets = {
        str(_require_mapping(edge, "edge").get("target"))
        for edge in edges
        if _require_mapping(edge, "edge").get("kind") == "CONSUMED_BY"
    }
    if consumer_nodes != consumed_targets:
        raise RetraceContractError("orphan consumer in semantic invalidation graph")
    kinds = [str(_require_mapping(node, "node").get("kind")) for node in nodes]
    if kinds.count("internal_work_unit") != 222:
        raise RetraceContractError("routing projection must contain exactly 222 work units")
    if kinds.count("data_artifact_group") != 45:
        raise RetraceContractError("routing projection must contain exactly 45 artifacts")
    if kinds.count("recompute_route") != len(RetraceDisposition):
        raise RetraceContractError("routing projection must contain all 11 routes")
    routed_sources = [
        str(_require_mapping(edge, "edge").get("source"))
        for edge in edges
        if _require_mapping(edge, "edge").get("kind") == "ROUTED_TO"
    ]
    expected_routed_sources = {
        node_id
        for node_id, kind in node_kind.items()
        if kind in {"internal_work_unit", "data_artifact_group"}
    }
    if len(routed_sources) != len(set(routed_sources)) or set(
        routed_sources
    ) != expected_routed_sources:
        raise RetraceContractError("routing projection is not total and one-to-one")
    indexed_lifecycle_edge_refs = {
        str(value)
        for raw_row in root_index
        for value in _require_mapping(raw_row, "root_index row").get("edge_refs", ())
    }
    if indexed_lifecycle_edge_refs != typed_edge_refs:
        raise RetraceContractError(
            "typed lifecycle graph contains an edge outside the exact root index"
        )
    expected_graph = build_semantic_invalidation_graph(
        repo_root=repo_root,
        spec=spec,
        ledger=ledger,
        inventory=inventory,
    )
    if graph != expected_graph:
        raise RetraceContractError(
            "semantic invalidation graph differs from its exact registered projection"
        )


def build_supersession_map(*, repo_root: Path) -> dict[str, object]:
    """Build only evidence-backed supersessions; preserve unresolved chronology."""

    from common.evidence_graph import (
        EvidenceAxes,
        EvidenceEdge,
        EvidenceEdgeKind,
        EvidenceGraph,
        EvidenceNode,
        EvidenceNodeKind,
        EvidenceStatus,
        ProcessResult,
    )

    definitions = (
        {
            "relation_id": "SUP-PR172-PR184",
            "predecessor_id": "PR-172",
            "predecessor_path": "docs/generated/pr172_result_card.json",
            "successor_id": "PR-184",
            "successor_path": "docs/generated/pr184_result_card.json",
            "evidence_path": "docs/research_program/long_horizon_rescue/pr184_spec.yaml",
            "changed_dimensions": ["THEOREM"],
            "affected_capabilities": ["CONTRACT_VALIDATED", "PUBLIC_RELEASE"],
            "preservation": "PR-172 remains failed-with-receipt; PR-184 changes only the premise-complete callable reading.",
        },
        {
            "relation_id": "SUP-PR168-PR248",
            "predecessor_id": "PR-168",
            "predecessor_path": "docs/generated/pr168_code_integrity_receipt.json",
            "successor_id": "PR-248",
            "successor_path": "docs/research_program/stat_foundations/pr248_pr168_integrity_supersession.yaml",
            "evidence_path": "docs/research_program/stat_foundations/pr248_pr168_integrity_supersession.yaml",
            "changed_dimensions": ["THEOREM"],
            "affected_capabilities": ["CONTRACT_VALIDATED", "METHOD_CALIBRATED", "PUBLIC_RELEASE"],
            "preservation": "PR-168 receipt and inventory remain byte-preserved; PR-248 is a bounded live-registry overlay.",
        },
        {
            "relation_id": "SUP-PR130-TAIL-GATE",
            "predecessor_id": "PR-130-LEGACY",
            "predecessor_path": "htt/obsstat/egs2_fisher.py",
            "successor_id": "C-PR130-NT2-TAIL",
            "successor_path": "docs/generated/pr130_legacy_invalidation.json",
            "evidence_path": "docs/generated/pr130_legacy_invalidation.json",
            "changed_dimensions": ["THEOREM"],
            "affected_capabilities": ["THEOREM_PROVED_CONDITIONAL", "METHOD_CALIBRATED", "PUBLIC_RELEASE"],
            "preservation": "The legacy module remains byte-frozen; the tail theorem and sufficiency gate own the successor reading.",
        },
        {
            "relation_id": "SUP-PR169-ALGEBRAIC-ONLY",
            "predecessor_id": "PR-169-CANDIDATE",
            "predecessor_path": "docs/research_program/long_horizon_rescue/pr169_spec.yaml",
            "successor_id": "PR-169-ALGEBRAIC-ONLY",
            "successor_path": "docs/generated/pr169_candidate_branch_supersession.json",
            "evidence_path": "docs/generated/pr169_candidate_branch_supersession.json",
            "changed_dimensions": ["THEOREM"],
            "affected_capabilities": ["THEOREM_PROVED_CONDITIONAL", "MORPHOLOGY_COMPATIBILITY", "FAMILY_IDENTIFICATION", "PUBLIC_RELEASE"],
            "preservation": "The constructive candidate remains historical; only exact comparator algebra survives.",
        },
        {
            "relation_id": "SUP-PR170-PROVENANCE-ONLY",
            "predecessor_id": "PR-170-CANDIDATE",
            "predecessor_path": "docs/research_program/long_horizon_rescue/pr170_spec.yaml",
            "successor_id": "PR-170-PROVENANCE-ONLY",
            "successor_path": "docs/generated/pr170_candidate_branch_supersession.json",
            "evidence_path": "docs/generated/pr170_candidate_branch_supersession.json",
            "changed_dimensions": ["THEOREM"],
            "affected_capabilities": ["THEOREM_PROVED_CONDITIONAL", "MORPHOLOGY_COMPATIBILITY", "FAMILY_IDENTIFICATION", "PUBLIC_RELEASE"],
            "preservation": "The candidate branch remains historical and CAS-blocked; the successor is source-provenance audit only.",
        },
    )
    claim = EvidenceNode(
        kind=EvidenceNodeKind.CLAIM,
        label="C-PR279-SUPERSESSION-PROJECTION",
        content_sha256=file_sha256(
            repo_root / "docs/research_program/post_pr275/pr279_spec.yaml"
        ),
        axes=EvidenceAxes(ProcessResult.PASS, EvidenceStatus.PRESENT, "OPEN"),
        metadata={
            "scope": "diagnostic supersession projection",
            "capability_issuance": "forbidden",
        },
    )
    nodes: list[object] = [claim]
    edges: list[object] = []
    relations: list[dict[str, object]] = []
    for definition in definitions:
        predecessor_path = repo_root / str(definition["predecessor_path"])
        successor_path = repo_root / str(definition["successor_path"])
        evidence_path = repo_root / str(definition["evidence_path"])
        for path in (predecessor_path, successor_path, evidence_path):
            if path.is_symlink() or not path.is_file():
                raise RetraceContractError(
                    f"supersession evidence is missing or non-regular: {path}"
                )
        predecessor = EvidenceNode(
            kind=EvidenceNodeKind.ARTIFACT,
            label=f"PR279 predecessor {definition['relation_id']}",
            content_sha256=file_sha256(predecessor_path),
            axes=EvidenceAxes(ProcessResult.PASS, EvidenceStatus.PRESENT, "OPEN"),
            metadata={
                "historical_identity": str(definition["predecessor_id"]),
                "path": str(definition["predecessor_path"]),
                "preservation": str(definition["preservation"]),
            },
        )
        successor = EvidenceNode(
            kind=EvidenceNodeKind.ARTIFACT,
            label=f"PR279 successor {definition['relation_id']}",
            content_sha256=file_sha256(successor_path),
            axes=EvidenceAxes(ProcessResult.PASS, EvidenceStatus.PRESENT, "OPEN"),
            metadata={
                "successor_identity": str(definition["successor_id"]),
                "path": str(definition["successor_path"]),
                "scope": "registered successor reading only",
            },
        )
        edge = EvidenceEdge(
            kind=EvidenceEdgeKind.SUPERSEDED_BY,
            source_ref=predecessor.node_ref,
            target_ref=successor.node_ref,
            metadata={
                "affected_capabilities": list(definition["affected_capabilities"]),
                "reason_ref": file_sha256(evidence_path),
                "changed_dimensions": list(definition["changed_dimensions"]),
            },
        )
        nodes.extend((predecessor, successor))
        edges.append(edge)
        relations.append(
            {
                **definition,
                "predecessor_sha256": predecessor.content_sha256,
                "successor_sha256": successor.content_sha256,
                "reason_ref": file_sha256(evidence_path),
                "predecessor_node_ref": predecessor.node_ref,
                "successor_node_ref": successor.node_ref,
                "edge_ref": edge.edge_ref,
            }
        )
    graph = EvidenceGraph(nodes=nodes, edges=edges)

    extension_path = repo_root / "docs/research_program/stat_foundations/pr252_pr248_integrity_supersession.yaml"
    migration_path = repo_root / "docs/research_program/stat_foundations/pr252_mes_consumer_migration.yaml"
    extension = load_yaml_mapping(extension_path)
    pinned_migration = str(
        _require_mapping(
            extension.get("authorizing_receipt"), "PR-252 authorizing_receipt"
        ).get("sha256")
    )
    current_migration = file_sha256(migration_path)
    if pinned_migration == current_migration:
        raise RetraceContractError(
            "PR-248 -> PR-252 withheld-edge contradiction was resolved; register a new explicit supersession row"
        )
    result = {
        "schema": "htt.pr279_supersession_map.v1",
        "document_id": "PR279-SUPERSESSION-MAP",
        "owner": "COMMON",
        "scope": "narrow evidence-backed successor readings and preserved negative history",
        "allowed_use": "diagnostic invalidation and recomputation routing only",
        "transfer_source": "not_applicable_or_preserved_per_historical_surface",
        "source_identities": [
            {"relation_id": row["relation_id"], "reason_ref": row["reason_ref"]}
            for row in relations
        ],
        "assumptions": [
            "A successor changes only its registered identity dimensions.",
            "Historical failed receipts remain immutable and terminal under their original statement."
        ],
        "caveats": [
            "PR-248 to PR-252 is withheld because its tracked exact-hash authorities contradict each other.",
            "No direct PR-124 to PR-259 supersession edge is registered."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "capability_issuance": "forbidden",
        "typed_supersession_graph": graph.to_record(),
        "relations": relations,
        "related_invalidations": [
            {
                "invalidation_id": "INV-PR128-AUTHORITY-TABLE",
                "relation": "INVALIDATES_THEOREM",
                "historical_pr": "PR-128",
                "evidence_path": "docs/generated/pr128_invalidation_table.json",
                "reason_ref": file_sha256(
                    repo_root / "docs/generated/pr128_invalidation_table.json"
                ),
                "disposition": RetraceDisposition.CORRECTED_SUPERSEDED.value,
            }
        ],
        "preserved_falsified_history": [
            {
                "history_id": "FALSIFIED-PR190-FULL-ATTAINABILITY",
                "historical_pr": "PR-190",
                "statement_path": "docs/research_program/strengthening/pr190_spec.yaml",
                "result_path": "docs/generated/pr190_attainability/attainability_report.json",
                "result_sha256": file_sha256(
                    repo_root
                    / "docs/generated/pr190_attainability/attainability_report.json"
                ),
                "disposition": RetraceDisposition.FALSIFIED_HISTORICAL.value,
                "successor": None,
            }
        ],
        "withheld_relations": [
            {
                "relation_id": "WITHHELD-PR248-PR252-HASH-CONTRADICTION",
                "candidate_relation": "PR-248 -> PR-252",
                "extension_path": str(extension_path.relative_to(repo_root)),
                "extension_sha256": file_sha256(extension_path),
                "pinned_migration_sha256": pinned_migration,
                "current_migration_path": str(migration_path.relative_to(repo_root)),
                "current_migration_sha256": current_migration,
                "route_id": route_id(RetraceDisposition.CORRECTED_SUPERSEDED),
                "named_resolution_event": "OWNER_APPROVED_CHRONOLOGY_PRESERVING_SUCCESSOR_REGISTRATION",
            }
        ],
        "summary": {
            "typed_supersession_count": len(relations),
            "related_invalidation_count": 1,
            "preserved_falsified_count": 1,
            "withheld_relation_count": 1,
            "historical_predecessor_rewrite_count": 0,
        },
    }
    return result


def validate_supersession_map(
    document: Mapping[str, object], *, repo_root: Path
) -> None:
    from common.evidence_graph import EvidenceEdgeKind, EvidenceGraph

    if document.get("schema") != "htt.pr279_supersession_map.v1":
        raise RetraceContractError("unknown supersession-map schema")
    validate_output_metadata(document)
    if document.get("capability_issuance") != "forbidden":
        raise RetraceContractError("supersession map cannot issue capability decisions")
    graph = EvidenceGraph.from_record(
        _require_mapping(
            document.get("typed_supersession_graph"), "typed_supersession_graph"
        )
    )
    if len(graph.edges) != 5 or any(
        edge.kind is not EvidenceEdgeKind.SUPERSEDED_BY for edge in graph.edges
    ):
        raise RetraceContractError("supersession map requires the exact five typed edges")
    relations = _require_sequence(document.get("relations"), "relations")
    if len(relations) != 5:
        raise RetraceContractError("supersession relation count drifted")
    relation_ids = [
        str(_require_mapping(row, "supersession relation").get("relation_id"))
        for row in relations
    ]
    if (
        len(relation_ids) != len(set(relation_ids))
        or set(relation_ids) != _SUPERSESSION_RELATION_IDS
    ):
        raise RetraceContractError("supersession relation identities drifted")
    node_by_ref = {node.node_ref: node for node in graph.nodes}
    edge_by_ref = {edge.edge_ref: edge for edge in graph.edges}
    predecessors: set[str] = set()
    relation_edge_refs: set[str] = set()
    for raw_row in relations:
        row = _require_mapping(raw_row, "supersession relation")
        predecessor = str(row.get("predecessor_id"))
        if predecessor in predecessors:
            raise RetraceContractError(f"duplicate predecessor {predecessor}")
        predecessors.add(predecessor)
        for field, digest_field in (
            ("predecessor_path", "predecessor_sha256"),
            ("successor_path", "successor_sha256"),
            ("evidence_path", "reason_ref"),
        ):
            path = repo_root / str(row.get(field))
            if path.is_symlink() or not path.is_file() or file_sha256(path) != row.get(
                digest_field
            ):
                raise RetraceContractError(
                    f"supersession evidence drifted: {row.get(field)}"
                )
        predecessor_ref = str(row.get("predecessor_node_ref"))
        successor_ref = str(row.get("successor_node_ref"))
        edge_ref = str(row.get("edge_ref"))
        predecessor_node = node_by_ref.get(predecessor_ref)
        successor_node = node_by_ref.get(successor_ref)
        edge = edge_by_ref.get(edge_ref)
        if predecessor_node is None or successor_node is None or edge is None:
            raise RetraceContractError(
                f"supersession relation {row.get('relation_id')} has orphan graph references"
            )
        if edge_ref in relation_edge_refs:
            raise RetraceContractError(f"duplicate supersession edge reference {edge_ref}")
        relation_edge_refs.add(edge_ref)
        expected_capabilities = sorted(
            str(value) for value in row.get("affected_capabilities", ())
        )
        expected_dimensions = sorted(
            str(value) for value in row.get("changed_dimensions", ())
        )
        if (
            edge.source_ref != predecessor_ref
            or edge.target_ref != successor_ref
            or predecessor_node.content_sha256 != row.get("predecessor_sha256")
            or successor_node.content_sha256 != row.get("successor_sha256")
            or predecessor_node.metadata.get("historical_identity")
            != row.get("predecessor_id")
            or successor_node.metadata.get("successor_identity")
            != row.get("successor_id")
            or sorted(
                str(value) for value in edge.metadata.get("affected_capabilities", ())
            )
            != expected_capabilities
            or sorted(
                str(value) for value in edge.metadata.get("changed_dimensions", ())
            )
            != expected_dimensions
            or edge.metadata.get("reason_ref") != row.get("reason_ref")
        ):
            raise RetraceContractError(
                f"supersession relation {row.get('relation_id')} differs from typed edge"
            )
    if relation_edge_refs != set(edge_by_ref):
        raise RetraceContractError("supersession relation projection is not total")
    withheld = _require_sequence(
        document.get("withheld_relations"), "withheld_relations"
    )
    if len(withheld) != 1 or _require_mapping(
        withheld[0], "withheld relation"
    ).get("relation_id") != "WITHHELD-PR248-PR252-HASH-CONTRADICTION":
        raise RetraceContractError("PR-248 -> PR-252 contradiction must remain explicit")
    withheld_row = _require_mapping(withheld[0], "withheld relation")
    extension_path = repo_root / str(withheld_row.get("extension_path"))
    migration_path = repo_root / str(withheld_row.get("current_migration_path"))
    if any(path.is_symlink() or not path.is_file() for path in (extension_path, migration_path)):
        raise RetraceContractError("withheld chronology evidence is missing or non-regular")
    extension = load_yaml_mapping(extension_path)
    pinned = str(
        _require_mapping(
            extension.get("authorizing_receipt"), "withheld authorizing_receipt"
        ).get("sha256")
    )
    current = file_sha256(migration_path)
    if (
        file_sha256(extension_path) != withheld_row.get("extension_sha256")
        or pinned != withheld_row.get("pinned_migration_sha256")
        or current != withheld_row.get("current_migration_sha256")
        or pinned == current
        or withheld_row.get("route_id")
        != route_id(RetraceDisposition.CORRECTED_SUPERSEDED)
        or not withheld_row.get("named_resolution_event")
    ):
        raise RetraceContractError("withheld PR-248 -> PR-252 chronology evidence drifted")
    falsified = _require_sequence(
        document.get("preserved_falsified_history"), "preserved_falsified_history"
    )
    if len(falsified) != 1 or _require_mapping(
        falsified[0], "falsified history"
    ).get("successor") is not None:
        raise RetraceContractError("PR-190 must remain falsified without a fake successor")
    expected_document = build_supersession_map(repo_root=repo_root)
    if document != expected_document:
        raise RetraceContractError(
            "supersession map differs from its exact evidence-backed projection"
        )


def build_failure_debt(
    *,
    backlog: Mapping[str, object],
    inventory: Mapping[str, object],
    pr280_inventory_receipt_sha256: str | None = None,
    pr280_active_core_nodes: Sequence[str] | None = None,
) -> dict[str, object]:
    if pr280_inventory_receipt_sha256 is not None and re.fullmatch(
        r"[0-9a-f]{64}", pr280_inventory_receipt_sha256
    ) is None:
        raise RetraceContractError("PR-280 inventory receipt hash is malformed")
    if pr280_inventory_receipt_sha256 is None:
        if pr280_active_core_nodes is not None:
            raise RetraceContractError(
                "PR-280 active-core nodes require an inventory receipt"
            )
        active_core_nodes: tuple[str, ...] | None = None
    else:
        if not isinstance(pr280_active_core_nodes, Sequence) or isinstance(
            pr280_active_core_nodes, (str, bytes)
        ):
            raise RetraceContractError(
                "PR-280 receipt requires an exact active-core node sequence"
            )
        supplied_nodes = tuple(pr280_active_core_nodes)
        if any(not isinstance(node, str) or not node for node in supplied_nodes):
            raise RetraceContractError("PR-280 active-core node is malformed")
        if len(supplied_nodes) != len(set(supplied_nodes)):
            raise RetraceContractError("PR-280 active-core nodes contain duplicates")
        successor_by_node = dict(PR280_ACTIVE_CORE_SUCCESSORS)
        unknown_nodes = sorted(set(supplied_nodes) - set(successor_by_node))
        if unknown_nodes:
            raise RetraceContractError(
                "PR-280 active-core node lacks a registered root-cause successor: "
                f"{unknown_nodes}"
            )
        active_core_nodes = tuple(
            node
            for node, _successor in PR280_ACTIVE_CORE_SUCCESSORS
            if node in supplied_nodes
        )
    active_core_count = None if active_core_nodes is None else len(active_core_nodes)
    active_successors = [
        {"pr_id": successor, "failure_node": node}
        for node, successor in PR280_ACTIVE_CORE_SUCCESSORS
        if active_core_nodes is not None and node in active_core_nodes
    ]
    cards = _cards(backlog)
    native_cards = sorted(
        pr_id
        for pr_id, card in cards.items()
        if card.get("solver_gate_required") is True
    )
    rows = [
        {
            "debt_id": "DEBT-PR280-FRESH-INVENTORY",
            "status": (
                "OPEN"
                if pr280_inventory_receipt_sha256 is None
                else "RESOLVED_IN_PR280"
                if active_core_count == 0
                else "OPEN_ROOT_CAUSE_REQUIRED"
            ),
            "blocker_class": (
                "ACTIVE_CORE_REGRESSION"
                if active_core_count
                else "INFRASTRUCTURE_DEBT"
            ),
            "affected_prs": (
                [
                    "PR-280",
                    *(f"PR-{number}" for number in range(281, 295)),
                    *(row["pr_id"] for row in active_successors),
                ]
                if active_core_count
                else ["PR-280"]
            ),
            "route_id": route_id(RetraceDisposition.STABLE_REPLAY),
            "next_work_unit": (
                active_successors[0]["pr_id"] if active_core_count else "PR-280"
            ),
            "named_event": None,
            "resolution_receipt_sha256": pr280_inventory_receipt_sha256,
            "active_core_count": active_core_count,
            "active_core_nodes": (
                None if active_core_nodes is None else list(active_core_nodes)
            ),
            "root_cause_work_units": active_successors,
            "resolution_condition": (
                None
                if not active_core_count
                else "Every exact active-core node passes under a cache-free rerun "
                "receipt and each bound root-cause successor is COMPLETED_SUCCESS; "
                "rebucketing, waiver, skip, or baseline relaxation is not resolution."
            ),
            "effect": (
                "Fresh cache-free full inventory and failure classification have not run."
                if pr280_inventory_receipt_sha256 is None
                else "Fresh cache-free full inventory and exact failure classification are receipt-bound; no scientific capability is granted."
                if active_core_count == 0
                else "Fresh cache-free inventory is receipt-bound but contains three exact active-core failures; PR-295, PR-296, and PR-297 must resolve them before downstream science."
            ),
        },
        {
            "debt_id": "DEBT-PR276-STALE-RECONCILIATION-ASSERTIONS",
            "status": "RESOLVED_IN_PR279",
            "blocker_class": "INFRASTRUCTURE_DEBT",
            "affected_prs": ["PR-276", "PR-279"],
            "route_id": route_id(RetraceDisposition.MIGRATION_ONLY),
            "next_work_unit": "PR-279",
            "named_event": None,
            "effect": "Two fixed-list/generated-source assertions were stale after PR-278 completion.",
        },
        {
            "debt_id": "DEBT-NO-ADMITTED-DATA",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-274", "PR-289", "PR-290", "PR-291", "PR-292", "PR-293"],
            "route_id": route_id(RetraceDisposition.EXTERNAL_BLOCKED),
            "next_work_unit": "PR-289",
            "named_event": "LANE_SPECIFIC_DATA_ADMISSION",
            "effect": "PR-274 admitted zero products; observed execution remains forbidden.",
        },
        {
            "debt_id": "DEBT-NATIVE-SOLVER-ATLAS",
            "status": "BLOCKED_NAMED_EVENT",
            "blocker_class": "PHYSICAL_HARD",
            "affected_prs": native_cards,
            "route_id": route_id(RetraceDisposition.NATIVE_BLOCKED),
            "next_work_unit": None,
            "named_event": "EXTERNAL_NATIVE_LOW_ELL_SOLVER_AND_MORPHOLOGY_ATLAS_VALIDATED",
            "effect": "Native-dependent cards remain dormant; family identification stays blocked.",
        },
        {
            "debt_id": "DEBT-PR151-PARTIAL-DESI",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-151", "PR-203", "PR-178"],
            "route_id": route_id(RetraceDisposition.EXTERNAL_BLOCKED),
            "next_work_unit": "PR-151",
            "named_event": "AUTHENTICATED_COMPLETE_1000_EZMOCK_AND_25_ABACUS_ACQUISITION",
            "effect": "Partial/background DESI inputs cannot enter a statistic.",
        },
        {
            "debt_id": "DEBT-CF4-P0-QUARANTINE",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-120", "PR-209", "PR-291"],
            "route_id": route_id(RetraceDisposition.RERUN_FROM_RAW_DATA),
            "next_work_unit": "PR-291",
            "named_event": "H-CF4",
            "effect": "P0 rescue count remains zero; raw-catalogue/full-covariance replay is required.",
        },
        {
            "debt_id": "DEBT-THEOREM-151-ADJUDICATIONS",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-285", "PR-286"],
            "route_id": route_id(RetraceDisposition.REPROVE),
            "next_work_unit": "PR-285",
            "named_event": None,
            "effect": "The 123 source plus 28 VT obligations require receipt-bearing terminal adjudication.",
        },
        {
            "debt_id": "DEBT-BAYES-SEMANTICS",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-288"],
            "route_id": route_id(RetraceDisposition.RERUN_FROM_ADMITTED_SUMMARY),
            "next_work_unit": "PR-288",
            "named_event": None,
            "effect": "Legacy evidence, posterior, PPC, and LOOCV surfaces remain legacy-only until PR-288.",
        },
        {
            "debt_id": "DEBT-RESIDUAL-TYPED-GAPS",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-281", "PR-282", "PR-283", "PR-284"],
            "route_id": route_id(RetraceDisposition.RECALIBRATE_SYNTHETIC),
            "next_work_unit": "PR-281",
            "named_event": None,
            "effect": "Orbit acceptance, parity, weak-ID, and depth-path calibration remain pending.",
        },
        {
            "debt_id": "DEBT-DESI-BGS-ANY-ESTIMAND-ROUTE",
            "status": "OPEN_REPLAN_REQUIRED",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-203", "PR-289", "PR-294"],
            "route_id": route_id(RetraceDisposition.CORRECTED_SUPERSEDED),
            "next_work_unit": None,
            "named_event": "OWNER_APPROVED_VERSIONED_BGS_ANY_SUCCESSOR_CARD",
            "effect": "BGS_ANY and BGS_BRIGHT-21.5 are distinct estimands; no dedicated BGS_ANY successor is registered.",
        },
        {
            "debt_id": "DEBT-ACT-ADMISSION-AUTHORIZATION",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-204", "PR-289"],
            "route_id": route_id(RetraceDisposition.EXTERNAL_BLOCKED),
            "next_work_unit": "PR-204",
            "named_event": "H-ACT",
            "effect": "PR-204 consumes PR-289 through the canonical dependency overlay but still lacks admission and H-ACT execution receipts.",
        },
        {
            "debt_id": "DEBT-PR248-PR252-HASH-CONTRADICTION",
            "status": "OPEN_REPLAN_REQUIRED",
            "blocker_class": "LEGACY_SUPERSESSION",
            "affected_prs": ["PR-168", "PR-248", "PR-252", "PR-259"],
            "route_id": route_id(RetraceDisposition.CORRECTED_SUPERSEDED),
            "next_work_unit": None,
            "named_event": "OWNER_APPROVED_CHRONOLOGY_PRESERVING_SUCCESSOR_REGISTRATION",
            "effect": "Tracked PR-252 extension and migration receipt disagree on exact hashes; the edge is withheld.",
        },
        {
            "debt_id": "DEBT-FINAL-PUBLICATION",
            "status": "OPEN",
            "blocker_class": "EVIDENCE_CONDITIONAL",
            "affected_prs": ["PR-207", "PR-208"],
            "route_id": route_id(RetraceDisposition.STABLE_REPLAY),
            "next_work_unit": "PR-208",
            "named_event": None,
            "effect": "Publication may consume only capability-approved generated results after independent reproduction.",
        },
    ]
    result = {
        "schema": "htt.pr279_failure_debt.v1",
        "document_id": "PR279-FAILURE-DEBT",
        "owner": "COMMON",
        "scope": "named unresolved or explicitly resolved blockers discovered by reverse trace",
        "allowed_use": "dependency routing and stop decisions only",
        "transfer_source": "preserved per affected lane",
        "source_identities": [
            {"backlog_semantic_sha256": canonical_json_sha256(backlog)},
            {"inventory_semantic_sha256": canonical_json_sha256(inventory)},
        ],
        "assumptions": [
            "Blockers affect only named capabilities and downstream work units."
        ],
        "caveats": [
            "A named route does not authorize execution, admission, claim promotion, or publication."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "rows": rows,
        "summary": {
            "row_count": len(rows),
            "open_count": sum(str(row["status"]).startswith("OPEN") for row in rows),
            "named_event_blocked_count": sum(row["named_event"] is not None for row in rows),
            "unknown_route_count": 0,
        },
    }
    return result


def validate_failure_debt(
    document: Mapping[str, object],
    *,
    backlog: Mapping[str, object],
    inventory: Mapping[str, object],
    pr280_inventory_receipt_sha256: str | None = None,
    pr280_active_core_nodes: Sequence[str] | None = None,
) -> None:
    if document.get("schema") != "htt.pr279_failure_debt.v1":
        raise RetraceContractError("unknown failure-debt schema")
    validate_output_metadata(document)
    cards = _cards(backlog)
    rows = _require_sequence(document.get("rows"), "failure_debt.rows")
    ids: set[str] = set()
    allowed_classes = {
        "PHYSICAL_HARD",
        "EVIDENCE_CONDITIONAL",
        "LEGACY_SUPERSESSION",
        "INFRASTRUCTURE_DEBT",
        "ACTIVE_CORE_REGRESSION",
    }
    known_routes = {route_id(item) for item in RetraceDisposition}
    for raw_row in rows:
        row = _require_mapping(raw_row, "failure debt row")
        debt_id = str(row.get("debt_id"))
        if debt_id in ids or not debt_id.startswith("DEBT-"):
            raise RetraceContractError(f"duplicate or invalid failure debt id {debt_id}")
        ids.add(debt_id)
        if row.get("blocker_class") not in allowed_classes:
            raise RetraceContractError(f"{debt_id} has unknown blocker class")
        if row.get("route_id") not in known_routes:
            raise RetraceContractError(f"{debt_id} has unknown recompute route")
        affected = [str(value) for value in row.get("affected_prs", ())]
        if not affected or any(value not in cards for value in affected):
            raise RetraceContractError(f"{debt_id} has unknown affected work unit")
        next_work_unit = row.get("next_work_unit")
        if next_work_unit is not None and str(next_work_unit) not in cards:
            raise RetraceContractError(f"{debt_id} has unknown next work unit")
        if next_work_unit is None and not row.get("named_event"):
            raise RetraceContractError(
                f"{debt_id} lacks both a next work unit and a named event"
            )
    expected_document = build_failure_debt(
        backlog=backlog,
        inventory=inventory,
        pr280_inventory_receipt_sha256=pr280_inventory_receipt_sha256,
        pr280_active_core_nodes=pr280_active_core_nodes,
    )
    if document != expected_document:
        raise RetraceContractError(
            "failure debt differs from its exact backlog and inventory projection"
        )


_RUNBOOK_SEQUENCE = (
    "authenticated_release",
    "selection_mask_frame_units_transfer",
    "feature_extraction",
    "null_and_covariance",
    "JointAnisotropyState",
    "functional_orbit_depth",
    "MIO_diagnostic",
    "separate_HTT_inference",
    "legacy_scalar_projection",
    "blind_replay_and_adjudication",
)

_RUNBOOK_OWNERSHIP = {
    "OBSSTAT": "feature extraction only",
    "MIO": "diagnostic cross-check only; no likelihood, posterior, or evidence",
    "HTT": "model-dependent likelihood, posterior, evidence, and inference only",
    "COMMON": "contracts, provenance, and capability filtering",
}

_RUNBOOK_TRANSFER_PROVENANCE = (
    "preserve lane identity; external transfer never becomes native"
)

_RUNBOOK_FORBIDDEN = (
    "execution before both admission and lane-scoped human authorization",
    "MIO diagnostic used as HTT likelihood, posterior, or evidence",
    "weak-identification point estimate or nearest-family forcing",
    "native solver, native atlas, geometry detection, or family identification claim",
)

_RUNBOOK_DEFINITIONS = (
    ("RB-PLANCK", "PLANCK", "PR-290", "H-PLANCK", ("PR-194", "PR-198", "PR-199", "PR-202", "PR-281", "PR-282", "PR-287", "PR-288", "PR-289", "PR-290"), "OBSERVED_DESCRIPTIVE", "PR3 maps, masks, beams, harmonic conventions, and FFP10 processed through one observation/null pipeline"),
    ("RB-CF4", "CF4", "PR-291", "H-CF4", ("PR-195", "PR-201", "PR-283", "PR-284", "PR-287", "PR-289", "PR-291"), "MORPHOLOGY_COMPATIBILITY", "raw group catalogue, full covariance, depth and ZoA path, orbit invariants, and shared-nuisance identified set"),
    ("RB-HSC-KIDS", "HSC_KIDS", "PR-292", "H-HSC/KiDS", ("PR-287", "PR-289", "PR-292"), "MORPHOLOGY_COMPATIBILITY", "separate complete HSC and KiDS spin-2 products, masks, randoms, PSF, n(z), calibration, response, and covariance"),
    ("RB-ACT", "ACT", "PR-204", "H-ACT", ("PR-204", "PR-287", "PR-288", "PR-289"), "METHOD_CALIBRATED", "one frozen branch: validated 40<L<763 products or configuration-locked raw QE with exact response, mean field, noise, and simulations"),
    ("RB-DESI", "DESI", "PR-203", "H-DESI", ("PR-151", "PR-178", "PR-203", "PR-289"), "OBSERVED_INFERENTIAL", "complete BGS_BRIGHT-21.5 data/randoms, 1000 EZmock and separate 25 Abacus identities; BGS_ANY remains a distinct estimand"),
    ("RB-JWST-SN", "JWST_SN", "PR-293", "H-JWST", ("PR-287", "PR-288", "PR-289", "PR-293"), "OBSERVED_DESCRIPTIVE", "row-level source and host identity, individual errors, shared zero-point and peculiar-velocity covariance, and competitor models"),
    ("RB-CROSS-PROBE", "CROSS_PROBE", "PR-294", "SEPARATE_PR294_SCHEDULING_AFTER_ALL_INCLUDED_LANE_RECEIPTS", ("PR-155", "PR-156", "PR-157", "PR-158", "PR-178", "PR-181", "PR-205", "PR-206", "PR-207", "PR-208", "PR-294"), "SOURCE_SEPARATION_CANDIDATE", "capability-approved passed lanes only, joint covariance, principal angles, held-out injections, multiplicity, and mandatory abstention"),
)


def build_data_runbooks(*, backlog: Mapping[str, object]) -> dict[str, object]:
    cards = _cards(backlog)
    runbooks: list[dict[str, object]] = []
    for runbook_id, lane, owner_pr, gate, dependencies, ceiling, requirement in _RUNBOOK_DEFINITIONS:
        unknown = [pr_id for pr_id in dependencies if pr_id not in cards]
        if unknown:
            raise RetraceContractError(
                f"{runbook_id} references unknown work units: {unknown}"
            )
        runbooks.append(
            {
                "runbook_id": runbook_id,
                "lane": lane,
                "owner_pr": owner_pr,
                "dependencies": list(dependencies),
                "current_state": "BLOCKED_AT_ADMISSION_OR_AUTHORIZATION",
                "admission_work_unit": "PR-289",
                "execution_authorization_gate": gate,
                "admission_is_execution_authorization": False,
                "required_input_contract": requirement,
                "sequence": list(_RUNBOOK_SEQUENCE),
                "ownership": dict(_RUNBOOK_OWNERSHIP),
                "maximum_initial_capability": ceiling,
                "achieved_capability": None,
                "claim_ceiling": "data_transfer_conditional_diagnostic_or_stricter",
                "transfer_provenance": _RUNBOOK_TRANSFER_PROVENANCE,
                "no_claim_exit": f"{lane}_NOT_EXECUTED_OR_ABSTAIN_WITH_RECEIPT",
                "forbidden": list(_RUNBOOK_FORBIDDEN),
            }
        )
    result = {
        "schema": "htt.pr279_data_runbooks.v1",
        "document_id": "PR279-DATA-RUNBOOKS",
        "owner": "COMMON",
        "scope": "non-executing admission-to-adjudication routes for seven data lanes",
        "allowed_use": "preflight and future authorized execution routing only",
        "transfer_source": "lane_specific_and_never_native_by_inference",
        "source_identities": [
            {"backlog_semantic_sha256": canonical_json_sha256(backlog)},
            {
                "pr274_admission_result": "docs/research_program/vector_tensor/data_admission/PR274_ADMISSION_RESULT.json"
            },
        ],
        "assumptions": [
            "PR-274 admitted zero inputs and PR-289 is the only admission-successor work unit.",
            "Every observed lane requires a separate current human execution receipt."
        ],
        "caveats": [
            "Maximum initial capability is a ceiling, not an entitlement or achieved state.",
            "Cross-probe synthesis requires separate scheduling after every included lane is eligible."
        ],
        "generating_procedure": "scripts/codex_harness/run_pr279_reverse_trace.py build",
        "claim_tier_ceiling": "diagnostic_only",
        "observed_data_executed": False,
        "runbooks": runbooks,
        "summary": {
            "lane_count": len(runbooks),
            "admitted_lane_count": 0,
            "authorized_lane_count": 0,
            "executed_lane_count": 0,
            "family_identification_count": 0,
        },
    }
    return result


def validate_data_runbooks(
    document: Mapping[str, object], *, backlog: Mapping[str, object]
) -> None:
    from common.remediation_state import ClaimCapability

    if document.get("schema") != "htt.pr279_data_runbooks.v1":
        raise RetraceContractError("unknown data-runbook schema")
    validate_output_metadata(document)
    if document.get("observed_data_executed") is not False:
        raise RetraceContractError("PR-279 data runbooks must be non-executing")
    cards = _cards(backlog)
    runbooks = _require_sequence(document.get("runbooks"), "data_runbooks.runbooks")
    expected_lanes = {
        "PLANCK",
        "CF4",
        "HSC_KIDS",
        "ACT",
        "DESI",
        "JWST_SN",
        "CROSS_PROBE",
    }
    definition_by_lane = {
        lane: {
            "runbook_id": runbook_id,
            "owner_pr": owner_pr,
            "gate": gate,
            "dependencies": dependencies,
            "ceiling": ceiling,
            "requirement": requirement,
        }
        for (
            runbook_id,
            lane,
            owner_pr,
            gate,
            dependencies,
            ceiling,
            requirement,
        ) in _RUNBOOK_DEFINITIONS
    }
    lanes: set[str] = set()
    for raw_row in runbooks:
        row = _require_mapping(raw_row, "data runbook")
        lane = str(row.get("lane"))
        if lane in lanes:
            raise RetraceContractError(f"duplicate data runbook lane {lane}")
        lanes.add(lane)
        definition = definition_by_lane.get(lane)
        if definition is None:
            raise RetraceContractError(f"unknown data runbook lane {lane}")
        if row.get("admission_work_unit") != "PR-289" or row.get(
            "admission_is_execution_authorization"
        ) is not False:
            raise RetraceContractError(f"{lane} conflates admission and authorization")
        if row.get("execution_authorization_gate") != definition["gate"]:
            raise RetraceContractError(f"{lane} execution authorization gate drifted")
        if tuple(row.get("sequence", ())) != _RUNBOOK_SEQUENCE:
            raise RetraceContractError(f"{lane} execution sequence drifted")
        dependencies = [str(value) for value in row.get("dependencies", ())]
        owner_pr = str(row.get("owner_pr"))
        if (
            owner_pr != definition["owner_pr"]
            or row.get("runbook_id") != definition["runbook_id"]
            or tuple(dependencies) != definition["dependencies"]
            or row.get("required_input_contract") != definition["requirement"]
            or owner_pr not in cards
            or owner_pr not in dependencies
            or len(dependencies) != len(set(dependencies))
            or any(value not in cards for value in dependencies)
        ):
            raise RetraceContractError(f"{lane} has unknown dependency")
        try:
            maximum_capability = ClaimCapability(
                str(row.get("maximum_initial_capability"))
            )
        except ValueError as exc:
            raise RetraceContractError(
                f"{lane} has an unknown maximum initial capability"
            ) from exc
        if maximum_capability in {
            ClaimCapability.FAMILY_IDENTIFICATION,
            ClaimCapability.PUBLIC_RELEASE,
        }:
            raise RetraceContractError(
                f"{lane} exceeds the pre-native runbook capability ceiling"
            )
        if maximum_capability.value != definition["ceiling"]:
            raise RetraceContractError(f"{lane} capability ceiling drifted")
        if row.get("achieved_capability") is not None:
            raise RetraceContractError(f"{lane} cannot predeclare an achieved capability")
        ownership = _require_mapping(row.get("ownership"), f"{lane}.ownership")
        if dict(ownership) != _RUNBOOK_OWNERSHIP:
            raise RetraceContractError(f"{lane} ownership firewall drifted")
        if row.get("transfer_provenance") != _RUNBOOK_TRANSFER_PROVENANCE:
            raise RetraceContractError(f"{lane} transfer provenance drifted")
        if tuple(row.get("forbidden", ())) != _RUNBOOK_FORBIDDEN:
            raise RetraceContractError(f"{lane} non-relaxable claim firewall drifted")
    if lanes != expected_lanes:
        raise RetraceContractError(
            f"data runbooks differ from exact seven-lane scope: {sorted(lanes)}"
        )
    expected_document = build_data_runbooks(backlog=backlog)
    if document != expected_document:
        raise RetraceContractError(
            "data runbooks differ from their exact registered lane projection"
        )


def validate_recompute_matrix(
    document: Mapping[str, object],
    *,
    ledger: Mapping[str, object],
    inventory: Mapping[str, object],
) -> None:
    if document.get("schema") != "htt.pr279_recompute_matrix.v1":
        raise RetraceContractError("unknown recompute-matrix schema")
    validate_output_metadata(document)
    expected_document = build_recompute_matrix(ledger, inventory)
    if document != expected_document:
        raise RetraceContractError(
            "recompute matrix differs from its exact ledger and inventory projection"
        )
    routes = _require_sequence(document.get("routes"), "recompute_matrix.routes")
    expected = {route_id(item) for item in RetraceDisposition}
    route_rows = [_require_mapping(row, "route") for row in routes]
    route_ids = [str(row.get("route_id")) for row in route_rows]
    if len(route_ids) != len(set(route_ids)) or set(route_ids) != expected:
        raise RetraceContractError("recompute matrix does not contain exact 11 routes")
    if any(
        row.get("route_id") != route_id(str(row.get("disposition")))
        or row.get("capability_effect") != "none"
        for row in route_rows
    ):
        raise RetraceContractError("recompute route identity or capability effect drifted")
    work_units = _require_sequence(
        document.get("historical_work_units"), "historical_work_units"
    )
    artifacts = _require_sequence(document.get("data_artifacts"), "data_artifacts")
    if len(work_units) != 222 or len(artifacts) != 45:
        raise RetraceContractError("recompute matrix cardinality drifted")
    work_unit_ids = [
        str(_require_mapping(row, "historical work unit").get("internal_pr_id"))
        for row in work_units
    ]
    artifact_ids = [
        str(_require_mapping(row, "data artifact").get("artifact_id"))
        for row in artifacts
    ]
    if (
        len(work_unit_ids) != len(set(work_unit_ids))
        or any(not _INTERNAL_ID_RE.fullmatch(value) for value in work_unit_ids)
        or artifact_ids != [f"DATA-ART-{index:03d}" for index in range(1, 46)]
    ):
        raise RetraceContractError("recompute matrix object identities drifted")
    for raw_row in (*work_units, *artifacts):
        row = _require_mapping(raw_row, "recompute row")
        if row.get("route_id") not in expected:
            raise RetraceContractError("recompute matrix contains an unknown route")
        primary = str(row.get("primary_disposition"))
        try:
            RetraceDisposition(primary)
        except ValueError as exc:
            raise RetraceContractError(
                "recompute matrix contains an unknown primary disposition"
            ) from exc
        if row.get("route_id") != route_id(primary):
            raise RetraceContractError("recompute matrix route differs from disposition")
        if "normalized_dispositions" in row and primary not in row.get(
            "normalized_dispositions", ()
        ):
            raise RetraceContractError(
                "recompute matrix primary disposition is absent from its source row"
            )


__all__ = [
    "DataArtifactDisposition",
    "GITHUB_CSV_FIELDS",
    "INTERNAL_CSV_FIELDS",
    "LIFECYCLE_EDGE_KINDS",
    "NormalizedLegacyDisposition",
    "PR280_ACTIVE_CORE_SUCCESSORS",
    "RetraceContractError",
    "RetraceDisposition",
    "build_data_artifact_inventory_from_snapshot",
    "build_data_runbooks",
    "build_failure_debt",
    "build_github_index",
    "build_github_index_from_snapshot",
    "build_internal_ledger",
    "build_internal_ledger_from_snapshot",
    "build_recompute_matrix",
    "build_semantic_invalidation_graph",
    "build_source_snapshot",
    "build_supersession_map",
    "canonical_json_sha256",
    "canonical_status_map",
    "dump_yaml_bytes",
    "file_sha256",
    "historical_and_prospective_ids",
    "load_yaml_mapping",
    "normalize_legacy_disposition",
    "parse_legacy_actions",
    "reconstruct_csv_bytes",
    "route_id",
    "validate_data_artifact_inventory",
    "validate_data_runbooks",
    "validate_failure_debt",
    "validate_github_index",
    "validate_internal_ledger",
    "validate_output_metadata",
    "validate_recompute_matrix",
    "validate_semantic_invalidation_graph",
    "validate_source_snapshot",
    "validate_supersession_map",
    "work_unit_roots",
]
