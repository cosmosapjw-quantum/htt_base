"""PR-278 exact-source inventory for Tier-A non-author lane adjudication.

The inventory is deliberately conservative.  The historical family ledger
names 20 author-side candidates, but one of them still names a non-terminal
PR card.  The 62 dual-axis rows have no exact terminal-receipt crosswalk in the
repository.  Neither condition may be repaired by matching similar prose.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

import yaml

from common.remediation_state import RemediationContractError


REPO = Path(__file__).resolve().parents[3]
BASE_MERGE_SHA = "a7800430660c5a4bd532d8655fc63df03b21496e"
FAMILY_LEDGER = "docs/generated/claim_adjudication/adjudication_ledger.json"
LITERATURE_VERDICTS = (
    "docs/generated/claim_adjudication/literature_verdicts.json"
)
DUAL_AXIS_LEDGER = "docs/generated/dual_axis_claim_ledger.json"
V10_TIER_SOURCE = "docs/audits/v10_web_crag_20260721/tier_evidence.json"
STATUS = "docs/codex_handoff/pr_status.yaml"
BACKLOG = "docs/codex_handoff/pr_backlog.yaml"
MAPPER_RESULT = (
    ".agent-harness/runs/pr278-evidence-map-r2-20260804/results/"
    "A-PR278-EVIDENCE-MAP.json"
)
MAPPER_RESULT_SHA256 = (
    "515ab62fc7718e0c926da1fa8a378f5412bcb29be91a5eaad693c2168ba6d616"
)
MAPPER_RECEIPT = (
    "docs/research_program/post_pr275/tier_a_adjudication/"
    "exact_crosswalk_mapper_receipt.json"
)

FROZEN_SHA256: Mapping[str, str] = {
    FAMILY_LEDGER: "9cce5fd765ad7686ccbf84667829618053eb1c40c3f74a46c3e3957c90997b6f",
    LITERATURE_VERDICTS: "d8412195085042bb437f8419362ea6b5020c0456764fa1376936d7d5121f9593",
    DUAL_AXIS_LEDGER: "acc4cd8f755e3205cba50f12c4cabf1dcca69be082a15529ea792d9ffdec5c55",
    V10_TIER_SOURCE: "0aa5150b4660c55c724dc7342072b07bb1d5766d8a0845bd857c7467fafbc216",
    STATUS: "fa8dee2949e786cb3e1dfac4d09ed74a4a75acd14300e5ed4293cc9710c5b18c",
    BACKLOG: "9d017d3e10c553d3ba112b490385f4a85b63c20267abe5190b68ab5d955c2709",
    MAPPER_RECEIPT: "5155716fededb66e349bbe8932d9b9c4c4ad397f3a515d979528f72bf2d610ec",
}

BASE_SNAPSHOT_SOURCES = frozenset({STATUS, BACKLOG})

ELIGIBLE_SOURCE_STATUS = "PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION"
EVENT_GATED: Mapping[str, str] = {
    "D-DESI": "data_acquisition_pr151",
    "D-TEFF": "native_solver",
    "II-NATIVE": "native_solver",
    "T-SHARP": "native_solver",
    "M-ESTCOV": "genuinely_incomplete",
    "M-PARTIALID": "genuinely_incomplete",
    "T-KE": "genuinely_incomplete",
    "M-DUALAXIS": "process_only_no_literature_axis",
}
EXPECTED_FAMILY_COUNT = 28
EXPECTED_SOURCE_ELIGIBLE_COUNT = 20
EXPECTED_EVENT_GATED_COUNT = 8
EXPECTED_DUAL_AXIS_COUNT = 62


class TierASourceError(RemediationContractError):
    """Raised when a frozen PR-278 source or partition drifts."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _regular_file(repo: Path, relative: str) -> Path:
    path = repo / relative
    if not path.is_file() or path.is_symlink():
        raise TierASourceError(f"required regular file is missing: {relative}")
    return path


def _frozen_bytes(repo: Path, relative: str) -> bytes:
    if relative in BASE_SNAPSHOT_SOURCES:
        try:
            completed = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "show",
                    f"{BASE_MERGE_SHA}:{relative}",
                ],
                check=False,
                capture_output=True,
            )
        except OSError as exc:
            raise TierASourceError(
                f"cannot read frozen Git snapshot source: {relative}"
            ) from exc
        if completed.returncode != 0:
            raise TierASourceError(
                f"frozen Git snapshot source is unavailable: {relative}"
            )
        payload = completed.stdout
        expected = FROZEN_SHA256[relative]
        if _sha256_bytes(payload) != expected:
            raise TierASourceError(
                f"frozen Git snapshot identity drifted: {relative}"
            )
        return payload
    path = _regular_file(repo, relative)
    payload = path.read_bytes()
    expected = FROZEN_SHA256.get(relative)
    if expected is not None and _sha256_bytes(payload) != expected:
        raise TierASourceError(f"frozen source identity drifted: {relative}")
    return payload


def _json(repo: Path, relative: str) -> Any:
    try:
        return json.loads(_frozen_bytes(repo, relative))
    except json.JSONDecodeError as exc:
        raise TierASourceError(f"invalid JSON source: {relative}") from exc


def _yaml(repo: Path, relative: str) -> Any:
    try:
        return yaml.safe_load(_frozen_bytes(repo, relative))
    except yaml.YAMLError as exc:
        raise TierASourceError(f"invalid YAML source: {relative}") from exc


def _unique_index(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identity = row.get(key)
        if not isinstance(identity, str) or not identity:
            raise TierASourceError(f"{label} has a missing {key}")
        if identity in result:
            raise TierASourceError(f"{label} has duplicate {key}: {identity}")
        result[identity] = row
    return result


def _pr_delta_ref(pr_id: str) -> str:
    try:
        number = int(pr_id.split("-", 1)[1])
    except (IndexError, ValueError) as exc:
        raise TierASourceError(f"invalid PR id: {pr_id!r}") from exc
    return f"docs/PR_DELTAS/pr-{number:03d}.md"


def _binding(repo: Path, relative: str) -> tuple[str, str]:
    return relative, _sha256_bytes(_regular_file(repo, relative).read_bytes())


def _source_evidence_fingerprint(
    *,
    unit_id: str,
    unit_kind: str,
    source_row_sha256: str,
    evidence_bindings: Mapping[str, str],
    terminal_receipt_refs: list[str],
) -> str:
    return _canonical_sha256(
        {
            "schema": "htt.tier_a_source_evidence.v1",
            "unit_id": unit_id,
            "unit_kind": unit_kind,
            "source_row_sha256": source_row_sha256,
            "evidence_bindings": dict(sorted(evidence_bindings.items())),
            "terminal_receipt_refs": sorted(terminal_receipt_refs),
        }
    )


def build_source_manifest(repo: Path = REPO) -> dict[str, Any]:
    """Build the deterministic review inventory from the exact frozen inputs."""

    repo = repo.resolve()
    family_ledger = _json(repo, FAMILY_LEDGER)
    literature = _json(repo, LITERATURE_VERDICTS)
    dual_axis = _json(repo, DUAL_AXIS_LEDGER)
    v10 = _json(repo, V10_TIER_SOURCE)
    status = _yaml(repo, STATUS)
    backlog = _yaml(repo, BACKLOG)
    mapper = _json(repo, MAPPER_RECEIPT)
    if not all(
        isinstance(value, dict)
        for value in (
            family_ledger,
            literature,
            dual_axis,
            v10,
            status,
            backlog,
            mapper,
        )
    ):
        raise TierASourceError("every frozen PR-278 source must contain a mapping")

    family_rows = family_ledger.get("rows")
    dual_rows = dual_axis.get("claims")
    v10_rows = v10.get("entries")
    cards = backlog.get("prs")
    if not isinstance(cards, list):
        cards = backlog.get("cards")
    if not all(isinstance(value, list) for value in (family_rows, dual_rows, v10_rows, cards)):
        raise TierASourceError("family, dual-axis, v10, and backlog rows must be lists")
    if len(family_rows) != EXPECTED_FAMILY_COUNT:
        raise TierASourceError("family source must contain exactly 28 rows")
    if len(dual_rows) != EXPECTED_DUAL_AXIS_COUNT or len(v10_rows) != EXPECTED_DUAL_AXIS_COUNT:
        raise TierASourceError("dual-axis and v10 sources must contain exactly 62 rows")

    family_by_id = _unique_index(family_rows, "family", "family ledger")
    dual_by_id = _unique_index(dual_rows, "id", "dual-axis ledger")
    v10_by_id = _unique_index(v10_rows, "id", "v10 tier source")
    card_by_id = _unique_index(cards, "id", "canonical backlog")
    if set(literature) != set(family_by_id):
        raise TierASourceError(
            "literature verdicts and family ledger must have the same 28 IDs"
        )
    if set(dual_by_id) != set(v10_by_id):
        raise TierASourceError("dual-axis and v10 claim ID sets differ")
    if (
        dual_axis.get("source_ledger") != V10_TIER_SOURCE
        or dual_axis.get("source_sha256") != FROZEN_SHA256[V10_TIER_SOURCE]
    ):
        raise TierASourceError("dual-axis ledger does not bind the exact v10 source")

    eligible = {
        family_id
        for family_id, row in family_by_id.items()
        if row.get("unlock_status") == ELIGIBLE_SOURCE_STATUS
    }
    if len(eligible) != EXPECTED_SOURCE_ELIGIBLE_COUNT:
        raise TierASourceError("author-side family source must name exactly 20 candidates")
    if len(EVENT_GATED) != EXPECTED_EVENT_GATED_COUNT or set(EVENT_GATED) != (
        set(family_by_id) - eligible
    ):
        raise TierASourceError("the exact eight-family event-gated partition drifted")
    mapper_content_sha256 = mapper.pop("receipt_content_sha256", None)
    if (
        mapper.get("schema") != "htt.tier_a_exact_crosswalk_mapper_receipt.v1"
        or mapper.get("run_id") != "pr278-evidence-map-r2-20260804"
        or mapper.get("assignment_id") != "A-PR278-EVIDENCE-MAP"
        or mapper.get("result_path") != MAPPER_RESULT
        or mapper.get("result_sha256") != MAPPER_RESULT_SHA256
        or mapper.get("result_status") != "inconclusive"
        or mapper.get("claim_id") != "C-PR278-TIER-A-ADJUDICATION"
        or mapper.get("finding_id") != "F-PR278-EXACT-CROSSWALK-ABSENT"
        or mapper.get("evidence_fingerprint")
        != "dual-axis-terminal-receipt-crosswalk-62-absent"
        or mapper.get("dual_axis_rows") != EXPECTED_DUAL_AXIS_COUNT
        or mapper.get("exact_terminal_receipt_crosswalks") != 0
        or mapper_content_sha256 != _canonical_sha256(mapper)
    ):
        raise TierASourceError(
            "the promoted exact-crosswalk mapper receipt drifted"
        )

    terminal_cards = set(status.get("completed", ())) | set(status.get("blocked", ()))
    family_units: list[dict[str, Any]] = []
    reviewable_count = 0
    for family_id in sorted(family_by_id):
        row = family_by_id[family_id]
        pr_cards = row.get("pr_cards")
        if not isinstance(pr_cards, list) or not pr_cards:
            raise TierASourceError(f"family {family_id} has no PR cards")
        owners: set[str] = {"program:BASS_HTT_program"}
        terminal_receipts: list[str] = []
        missing_terminal_cards: list[str] = []
        evidence_bindings = {
            FAMILY_LEDGER: FROZEN_SHA256[FAMILY_LEDGER],
            LITERATURE_VERDICTS: FROZEN_SHA256[LITERATURE_VERDICTS],
            STATUS: FROZEN_SHA256[STATUS],
            BACKLOG: FROZEN_SHA256[BACKLOG],
        }
        for pr_id in pr_cards:
            card = card_by_id.get(pr_id)
            if card is None:
                raise TierASourceError(f"family {family_id} names unknown card {pr_id}")
            owner = card.get("owner")
            if not isinstance(owner, str) or not owner:
                raise TierASourceError(f"card {pr_id} has no owner")
            owners.add(f"owner:{owner}")
            receipt_ref = _pr_delta_ref(pr_id)
            if pr_id not in terminal_cards:
                missing_terminal_cards.append(pr_id)
                continue
            receipt_path, receipt_sha = _binding(repo, receipt_ref)
            terminal_receipts.append(receipt_path)
            evidence_bindings[receipt_path] = receipt_sha

        source_row_sha = _canonical_sha256(row)
        is_source_candidate = family_id in eligible
        reviewable = is_source_candidate and not missing_terminal_cards
        if reviewable:
            reviewable_count += 1
            disposition = "PENDING_NON_AUTHOR"
            rationale = "exact family row and every named terminal PR delta are present"
        elif is_source_candidate:
            disposition = "HOLD"
            rationale = "named family PR cards are not terminal: " + ", ".join(
                missing_terminal_cards
            )
        else:
            disposition = "HOLD"
            rationale = f"named event gate remains unresolved: {EVENT_GATED[family_id]}"
        family_units.append(
            {
                "unit_id": family_id,
                "unit_kind": "FAMILY",
                "title": row.get("title"),
                "lane": row.get("lane"),
                "pr_cards": list(pr_cards),
                "source_unlock_status": row.get("unlock_status"),
                "source_candidate": is_source_candidate,
                "reviewable_now": reviewable,
                "event_gate": EVENT_GATED.get(family_id),
                "missing_terminal_cards": missing_terminal_cards,
                "terminal_receipt_refs": sorted(terminal_receipts),
                "author_principals": sorted(owners),
                "source_row_sha256": source_row_sha,
                "evidence_bindings": dict(sorted(evidence_bindings.items())),
                "evidence_fingerprint": _source_evidence_fingerprint(
                    unit_id=family_id,
                    unit_kind="FAMILY",
                    source_row_sha256=source_row_sha,
                    evidence_bindings=evidence_bindings,
                    terminal_receipt_refs=terminal_receipts,
                ),
                "pre_adjudication_disposition": disposition,
                "pre_adjudication_rationale": rationale,
                "claim_ceiling": "diagnostic_only",
                "capability_effect": "NONE_PENDING_PR157",
                "public_use": False,
            }
        )

    if reviewable_count != 19:
        raise TierASourceError(
            "exact terminal receipts must leave 19 reviewable families and "
            "one source-candidate HOLD"
        )
    held_source_candidates = [
        row["unit_id"]
        for row in family_units
        if row["source_candidate"] and not row["reviewable_now"]
    ]
    if held_source_candidates != ["T-OMK"]:
        raise TierASourceError("T-OMK must remain the sole non-terminal source candidate")

    dual_units: list[dict[str, Any]] = []
    for claim_id in sorted(dual_by_id):
        dual_row = dual_by_id[claim_id]
        v10_row = v10_by_id[claim_id]
        combined_row = {"dual_axis": dual_row, "v10_source": v10_row}
        source_row_sha = _canonical_sha256(combined_row)
        evidence_bindings = {
            DUAL_AXIS_LEDGER: FROZEN_SHA256[DUAL_AXIS_LEDGER],
            V10_TIER_SOURCE: FROZEN_SHA256[V10_TIER_SOURCE],
            MAPPER_RECEIPT: FROZEN_SHA256[MAPPER_RECEIPT],
        }
        dual_units.append(
            {
                "unit_id": claim_id,
                "unit_kind": "DUAL_AXIS_ROW",
                "subject": v10_row.get("subject"),
                "novelty_tier_external": dual_row.get("novelty_tier_external"),
                "readiness_state": dual_row.get("readiness_state"),
                "independence_gate": (dual_row.get("gates") or {}).get("independence"),
                "terminal_receipt_refs": [],
                "exact_terminal_receipt_crosswalk": None,
                "source_row_sha256": source_row_sha,
                "evidence_bindings": dict(sorted(evidence_bindings.items())),
                "evidence_fingerprint": _source_evidence_fingerprint(
                    unit_id=claim_id,
                    unit_kind="DUAL_AXIS_ROW",
                    source_row_sha256=source_row_sha,
                    evidence_bindings=evidence_bindings,
                    terminal_receipt_refs=[],
                ),
                "pre_adjudication_disposition": "INCONCLUSIVE",
                "pre_adjudication_rationale": (
                    "no exact terminal-receipt crosswalk is registered; semantic "
                    "similarity cannot supply one"
                ),
                "claim_ceiling": "diagnostic_only",
                "capability_effect": "NONE_PENDING_PR157",
                "public_use": False,
            }
        )

    payload: dict[str, Any] = {
        "schema": "htt.tier_a_adjudication.source_manifest.v1",
        "pr_id": "PR-278",
        "base_merge_sha": BASE_MERGE_SHA,
        "frozen_sources": dict(sorted(FROZEN_SHA256.items())),
        "summary": {
            "family_rows": EXPECTED_FAMILY_COUNT,
            "source_candidates": EXPECTED_SOURCE_ELIGIBLE_COUNT,
            "reviewable_families": reviewable_count,
            "source_candidate_holds": 1,
            "event_gated_families": EXPECTED_EVENT_GATED_COUNT,
            "dual_axis_rows": EXPECTED_DUAL_AXIS_COUNT,
            "dual_axis_exact_crosswalks": 0,
            "dual_axis_inconclusive": EXPECTED_DUAL_AXIS_COUNT,
            "cf4_p0_rescue_count": 0,
        },
        "event_gated": dict(sorted(EVENT_GATED.items())),
        "family_units": family_units,
        "dual_axis_units": dual_units,
        "final_aggregator": "PR-157",
        "capability_effect": "NONE_PENDING_PR157",
        "public_use": False,
        "claim_ceiling": "diagnostic_only",
    }
    payload["manifest_content_sha256"] = _canonical_sha256(payload)
    return payload


__all__ = [
    "BASE_MERGE_SHA",
    "EVENT_GATED",
    "EXPECTED_DUAL_AXIS_COUNT",
    "EXPECTED_EVENT_GATED_COUNT",
    "EXPECTED_FAMILY_COUNT",
    "EXPECTED_SOURCE_ELIGIBLE_COUNT",
    "FROZEN_SHA256",
    "MAPPER_RECEIPT",
    "MAPPER_RESULT",
    "MAPPER_RESULT_SHA256",
    "TierASourceError",
    "build_source_manifest",
]
