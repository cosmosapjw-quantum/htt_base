"""Fail-closed contracts for the PR-123 independent mutation laboratory.

This module owns mechanics receipts only.  It neither imports mapped OBSSTAT or
HTT producers nor promotes a synthetic mutation kill to scientific validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping

import numpy as np


FROZEN_MUTATION_IDS = (
    "shell_monopole_leak",
    "nonhermitian_rfft_plane",
    "fixed_alpha_mock",
    "low_order_curl_stencil",
    "ignored_host_error",
    "asymmetric_global_rank",
    "fitted_score_pseudo_bayes_factor",
    "plugin_pseudo_ppc",
    "stale_transfer_range",
)


class OracleLabError(ValueError):
    """Raised when a mutation receipt could otherwise become false-green."""


@dataclass(frozen=True)
class PropertyResult:
    property_id: str
    passed: bool
    metric: float | int | str | None
    threshold: float | int | str | None
    detail: str


@dataclass(frozen=True)
class MutationOutcome:
    mutation_id: str
    lane_id: str
    reference_symbol: str
    mutant_symbol: str
    fixture_hash: str
    reference_execution_count: int
    mutant_execution_count: int
    mutant_failed_properties: tuple[str, ...]
    execution_receipt_hash: str
    clean_passed: bool
    mutant_killed: bool
    status: str
    properties: tuple[PropertyResult, ...]
    metrics: Mapping[str, Any]

    @property
    def executed(self) -> bool:
        return self.reference_execution_count > 0 and self.mutant_execution_count > 0

    def as_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["executed"] = self.executed
        return _plain(record)


@dataclass(frozen=True)
class OracleLineage:
    mutation_id: str
    lane_id: str
    production_paths_and_sha256: tuple[Mapping[str, Any], ...]
    production_symbols: tuple[str, ...]
    reference_path_and_sha256: Mapping[str, str]
    reference_symbol: str
    reference_kernel_symbols: tuple[str, ...]
    mutant_symbol: str
    evaluator_symbol: str
    algorithm_id: str
    equation_or_source_ids: tuple[str, ...]
    fixture_ids_and_hashes: tuple[Mapping[str, str], ...]
    design_author_ids: tuple[str, ...]
    transcriber_id: str
    reviewer_id: str
    random_stream_namespace: str
    shared_lineage_disclosures: tuple[str, ...]
    later_production_owner: str
    later_adjudication_owner: str
    reference_metrics: Mapping[str, int]
    mutant_metrics: Mapping[str, int]
    evaluator_metrics: Mapping[str, int]
    complexity_budget: Mapping[str, int]
    automated_scan_checks: Mapping[str, bool]
    manual_algorithm_adjudication: Mapping[str, str]
    independence_class: str

    def as_record(self) -> dict[str, Any]:
        return _plain(asdict(self))


def _plain(value: Any) -> Any:
    """Convert scalar-array library values without accepting opaque objects."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    item = getattr(value, "item", None)
    if callable(item):
        return _plain(item())
    raise TypeError(f"value is not canonical-JSON compatible: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the one canonical JSON encoding used by PR-123 artifacts."""
    return json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def _execution_receipt_payload(
    *,
    mutation_id: str,
    lane_id: str,
    reference_symbol: str,
    mutant_symbol: str,
    fixture_hash: str,
    reference_execution_count: int,
    mutant_execution_count: int,
    mutant_failed_properties: Iterable[str],
    properties: Iterable[PropertyResult],
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "mutation_id": mutation_id,
        "lane_id": lane_id,
        "reference_symbol": reference_symbol,
        "mutant_symbol": mutant_symbol,
        "fixture_hash": fixture_hash,
        "reference_execution_count": reference_execution_count,
        "mutant_execution_count": mutant_execution_count,
        "mutant_failed_properties": tuple(mutant_failed_properties),
        "properties": [asdict(item) for item in properties],
        "metrics": metrics,
    }


def make_outcome(
    mutation_id: str,
    lane_id: str,
    properties: Iterable[PropertyResult],
    *,
    reference_symbol: str,
    mutant_symbol: str,
    fixture_hash: str,
    reference_execution_count: int,
    mutant_execution_count: int,
    mutant_failed_properties: Iterable[str],
    metrics: Mapping[str, Any],
) -> MutationOutcome:
    checked = tuple(properties)
    failed_properties = tuple(mutant_failed_properties)
    executed = reference_execution_count > 0 and mutant_execution_count > 0
    clean_passed = bool(checked) and all(item.passed for item in checked)
    mutant_killed = bool(failed_properties)
    if not executed:
        status = "BLOCKED_MUTATION_NOT_EXECUTED"
    elif not clean_passed:
        status = "BLOCKED_PROPERTY_FAILURE"
    elif not mutant_killed:
        status = "BLOCKED_MUTATION_SURVIVED"
    else:
        status = "PASS_MECHANICS_C2"
    receipt_payload = _execution_receipt_payload(
        mutation_id=mutation_id,
        lane_id=lane_id,
        reference_symbol=reference_symbol,
        mutant_symbol=mutant_symbol,
        fixture_hash=fixture_hash,
        reference_execution_count=reference_execution_count,
        mutant_execution_count=mutant_execution_count,
        mutant_failed_properties=failed_properties,
        properties=checked,
        metrics=metrics,
    )
    return MutationOutcome(
        mutation_id=mutation_id,
        lane_id=lane_id,
        reference_symbol=reference_symbol,
        mutant_symbol=mutant_symbol,
        fixture_hash=fixture_hash,
        reference_execution_count=reference_execution_count,
        mutant_execution_count=mutant_execution_count,
        mutant_failed_properties=failed_properties,
        execution_receipt_hash=content_sha256(receipt_payload),
        clean_passed=clean_passed,
        mutant_killed=mutant_killed,
        status=status,
        properties=checked,
        metrics=dict(metrics),
    )


def validate_outcomes(
    outcomes: Iterable[MutationOutcome],
    expected_registry: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate exact registry coverage and recompute every derived lane state."""
    rows = tuple(outcomes)
    ids = tuple(row.mutation_id for row in rows)
    if len(ids) != len(set(ids)):
        raise OracleLabError("duplicate mutation outcome")
    if set(ids) != set(FROZEN_MUTATION_IDS):
        missing = sorted(set(FROZEN_MUTATION_IDS) - set(ids))
        extra = sorted(set(ids) - set(FROZEN_MUTATION_IDS))
        raise OracleLabError(f"mutation registry mismatch: missing={missing}, extra={extra}")
    by_id = {row.mutation_id: row for row in rows}
    ordered = tuple(by_id[mid] for mid in FROZEN_MUTATION_IDS)
    derived_states: dict[str, tuple[bool, bool, bool, str]] = {}
    if set(expected_registry) != set(FROZEN_MUTATION_IDS):
        raise OracleLabError("expected registry does not cover frozen mutations")
    for row in ordered:
        expected = expected_registry[row.mutation_id]
        observed_properties = tuple(item.property_id for item in row.properties)
        expected_properties = tuple(expected["property_ids"])
        mismatches = []
        if row.lane_id != expected["lane_id"]:
            mismatches.append("lane_id")
        if row.reference_symbol != expected["reference_symbol"]:
            mismatches.append("reference_symbol")
        if row.mutant_symbol != expected["mutant_symbol"]:
            mismatches.append("mutant_symbol")
        if observed_properties != expected_properties:
            mismatches.append("property_ids")
        if row.fixture_hash != expected["fixture_hash"] or not _is_sha256(row.fixture_hash):
            mismatches.append("fixture_hash")
        if type(row.reference_execution_count) is not int or row.reference_execution_count != expected["reference_execution_count"]:
            mismatches.append("reference_execution_count")
        if type(row.mutant_execution_count) is not int or row.mutant_execution_count != expected["mutant_execution_count"]:
            mismatches.append("mutant_execution_count")
        if set(row.metrics) != set(expected["metric_keys"]):
            mismatches.append("metric_keys")
        if not set(row.mutant_failed_properties) <= set(expected_properties):
            mismatches.append("mutant_failed_properties")
        if any(not isinstance(item.passed, (bool, np.bool_)) or not item.detail for item in row.properties):
            mismatches.append("property_records")
        derived_executed = (
            row.reference_execution_count > 0 and row.mutant_execution_count > 0
        )
        derived_clean_passed = bool(row.properties) and all(
            bool(item.passed) for item in row.properties
        )
        derived_mutant_killed = bool(row.mutant_failed_properties)
        if not derived_executed:
            derived_status = "BLOCKED_MUTATION_NOT_EXECUTED"
        elif not derived_clean_passed:
            derived_status = "BLOCKED_PROPERTY_FAILURE"
        elif not derived_mutant_killed:
            derived_status = "BLOCKED_MUTATION_SURVIVED"
        else:
            derived_status = "PASS_MECHANICS_C2"
        if row.executed is not derived_executed:
            mismatches.append("executed")
        if type(row.clean_passed) is not bool or row.clean_passed is not derived_clean_passed:
            mismatches.append("clean_passed")
        if type(row.mutant_killed) is not bool or row.mutant_killed is not derived_mutant_killed:
            mismatches.append("mutant_killed")
        if type(row.status) is not str or row.status != derived_status:
            mismatches.append("status")
        expected_receipt_hash = content_sha256(_execution_receipt_payload(
            mutation_id=row.mutation_id,
            lane_id=row.lane_id,
            reference_symbol=row.reference_symbol,
            mutant_symbol=row.mutant_symbol,
            fixture_hash=row.fixture_hash,
            reference_execution_count=row.reference_execution_count,
            mutant_execution_count=row.mutant_execution_count,
            mutant_failed_properties=row.mutant_failed_properties,
            properties=row.properties,
            metrics=row.metrics,
        ))
        if row.execution_receipt_hash != expected_receipt_hash or not _is_sha256(row.execution_receipt_hash):
            mismatches.append("execution_receipt_hash")
        if mismatches:
            raise OracleLabError(
                f"outcome binding mismatch for {row.mutation_id}: {mismatches}"
            )
        derived_states[row.mutation_id] = (
            derived_executed,
            derived_clean_passed,
            derived_mutant_killed,
            derived_status,
        )
    survivors = [
        row.mutation_id
        for row in ordered
        if not all(derived_states[row.mutation_id][:3])
    ]
    return {
        "registered_count": len(FROZEN_MUTATION_IDS),
        "executed_count": sum(derived_states[row.mutation_id][0] for row in ordered),
        "clean_pass_count": sum(derived_states[row.mutation_id][1] for row in ordered),
        "killed_count": sum(derived_states[row.mutation_id][2] for row in ordered),
        "survivor_count": len(survivors),
        "survivors": survivors,
        "aggregate_status": (
            "PASS_MECHANICS_C2" if not survivors else "BLOCKED_MUTATION_LAB"
        ),
        "scientific_status": "OPEN",
        "claim_promotion_allowed": False,
        "outcomes": [row.as_record() for row in ordered],
    }


def validate_seed_ledger(
    rows: Iterable[Mapping[str, Any]],
    *,
    root_seed: int,
    bit_generator: str,
    expected_slots: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Replay every registered SeedSequence child and reject ledger laundering."""
    if type(root_seed) is not int or type(bit_generator) is not str:
        raise OracleLabError("seed ledger root or bit-generator type mismatch")
    checked = [dict(row) for row in rows]
    slots = [dict(slot) for slot in expected_slots]
    if len(checked) != len(slots):
        raise OracleLabError("seed ledger length mismatch")
    required_keys = {
        "lane_id", "replicate", "role", "root_entropy", "spawn_key",
        "bit_generator", "stream_hash",
    }
    seen_spawn_keys: set[tuple[int, ...]] = set()
    for index, (row, slot) in enumerate(zip(checked, slots, strict=True)):
        if set(row) != required_keys:
            raise OracleLabError(f"seed ledger field mismatch at slot {index}")
        if set(slot) != {"lane_id", "replicate", "role", "spawn_key"}:
            raise OracleLabError(f"seed schedule field mismatch at slot {index}")
        row_types_valid = (
            type(row["lane_id"]) is str
            and type(row["role"]) is str
            and type(row["replicate"]) is int
            and type(row["root_entropy"]) is int
            and type(row["spawn_key"]) is list
            and all(type(value) is int for value in row["spawn_key"])
            and type(row["bit_generator"]) is str
            and type(row["stream_hash"]) is str
        )
        slot_types_valid = (
            type(slot["lane_id"]) is str
            and type(slot["role"]) is str
            and type(slot["replicate"]) is int
            and type(slot["spawn_key"]) is list
            and all(type(value) is int for value in slot["spawn_key"])
        )
        if not row_types_valid or not slot_types_valid:
            raise OracleLabError(f"seed ledger exact-type mismatch at slot {index}")
        expected_spawn_key = tuple(slot["spawn_key"])
        observed_spawn_key = tuple(row["spawn_key"])
        if observed_spawn_key in seen_spawn_keys:
            raise OracleLabError("duplicate seed spawn key")
        seen_spawn_keys.add(observed_spawn_key)
        if (
            row["lane_id"] != slot["lane_id"]
            or row["role"] != slot["role"]
            or row["replicate"] != slot["replicate"]
            or row["root_entropy"] != root_seed
            or observed_spawn_key != expected_spawn_key
            or row["bit_generator"] != bit_generator
        ):
            raise OracleLabError(f"seed ledger schedule mismatch at slot {index}")
        child = np.random.SeedSequence(root_seed, spawn_key=expected_spawn_key)
        expected_hash = hashlib.sha256(child.generate_state(4).tobytes()).hexdigest()
        if row["stream_hash"] != expected_hash or not _is_sha256(row["stream_hash"]):
            raise OracleLabError(f"seed ledger replay mismatch at slot {index}")
    return checked


def validate_lineage_rows(rows: Iterable[OracleLineage]) -> list[dict[str, Any]]:
    """Reject missing, correlated-but-undisclosed, or over-budget references."""
    checked = tuple(rows)
    ids = tuple(row.mutation_id for row in checked)
    if set(ids) != set(FROZEN_MUTATION_IDS) or len(ids) != len(set(ids)):
        raise OracleLabError("lineage rows do not cover the frozen mutation registry")
    records: list[dict[str, Any]] = []
    for row in checked:
        required_sequences = (
            row.production_paths_and_sha256,
            row.production_symbols,
            row.reference_kernel_symbols,
            row.equation_or_source_ids,
            row.fixture_ids_and_hashes,
            row.design_author_ids,
            row.shared_lineage_disclosures,
        )
        required_scalars = (
            row.mutation_id,
            row.lane_id,
            row.reference_symbol,
            row.mutant_symbol,
            row.evaluator_symbol,
            row.algorithm_id,
            row.transcriber_id,
            row.reviewer_id,
            row.random_stream_namespace,
            row.later_production_owner,
            row.later_adjudication_owner,
            row.independence_class,
        )
        if not all(required_sequences) or not all(required_scalars):
            raise OracleLabError(f"incomplete lineage for {row.mutation_id}")
        if not row.automated_scan_checks or not all(row.automated_scan_checks.values()):
            raise OracleLabError(f"automated lineage scan failed for {row.mutation_id}")
        if row.manual_algorithm_adjudication.get("decision") != "distinct_with_disclosed_correlation":
            raise OracleLabError(f"manual lineage adjudication failed for {row.mutation_id}")
        sloc = int(row.reference_metrics.get("sloc", -1))
        branches = int(row.reference_metrics.get("branches", -1))
        if sloc < 1 or sloc > int(row.complexity_budget.get("max_sloc", -1)):
            raise OracleLabError(f"reference SLOC budget failed for {row.mutation_id}")
        if branches < 0 or branches > int(row.complexity_budget.get("max_branches", -1)):
            raise OracleLabError(f"reference branch budget failed for {row.mutation_id}")
        evaluator_sloc = int(row.evaluator_metrics.get("sloc", -1))
        evaluator_branches = int(row.evaluator_metrics.get("branches", -1))
        if evaluator_sloc < 1 or evaluator_sloc > int(row.complexity_budget.get("max_evaluator_sloc", -1)):
            raise OracleLabError(f"evaluator SLOC budget failed for {row.mutation_id}")
        if evaluator_branches < 0 or evaluator_branches > int(row.complexity_budget.get("max_evaluator_branches", -1)):
            raise OracleLabError(f"evaluator branch budget failed for {row.mutation_id}")
        mutant_sloc = int(row.mutant_metrics.get("sloc", -1))
        mutant_branches = int(row.mutant_metrics.get("branches", -1))
        if mutant_sloc < 1 or mutant_sloc > int(row.complexity_budget.get("max_mutant_sloc", -1)):
            raise OracleLabError(f"mutant SLOC budget failed for {row.mutation_id}")
        if mutant_branches < 0 or mutant_branches > int(row.complexity_budget.get("max_mutant_branches", -1)):
            raise OracleLabError(f"mutant branch budget failed for {row.mutation_id}")
        production_sloc = int(row.complexity_budget.get("mapped_production_call_closure_sloc", -1))
        if production_sloc < 1 or sloc >= production_sloc:
            raise OracleLabError(f"reference is not smaller than production for {row.mutation_id}")
        records.append(row.as_record())
    return records
