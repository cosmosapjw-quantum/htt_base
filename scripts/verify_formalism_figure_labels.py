#!/usr/bin/env python3
"""Lint canonical x/Q/Pi/F/G_F labels in manuscript figure payloads."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SEMANTIC_SPLIT_POINTER = "/semantic_and_vectors/semantic_split"
DEPARTURE_DISPLAY_CONTRACT_POINTER = (
    "/semantic_and_vectors/departure_display_contract"
)
CANCELLATION_COUNTEREXAMPLE_POINTER = (
    "/semantic_and_vectors/cancellation_counterexample"
)
Q_MULTIVERSE_POINTER = "/transfer_sensitivity/q_comparator_multiverse"
PI_POLICY_POINTER = "/transfer_sensitivity/pi_policy_summary"
PI_DISPLAY_CONTRACT_POINTER = "/semantic_and_vectors/pi_display_contract"
REQUIRED_PI_BLOCKED_USE_CODES = frozenset(
    {
        "p_value_claim",
        "truth_probability",
        "htt_inference_consumption",
        "model_selection",
        "solver_validation",
        "scalar_classification",
    }
)


@dataclass(frozen=True)
class CanonicalSymbol:
    symbol: str
    owner: str
    required_definition_terms: tuple[tuple[str, ...], ...]
    definition_summary: str


@dataclass(frozen=True)
class LabelIssue:
    row_index: int
    symbol: str
    issue_type: str
    expected: str
    actual: str
    pointer: str = SEMANTIC_SPLIT_POINTER

    def render(self) -> str:
        location = (
            f"{self.pointer}/{self.row_index}"
            if self.row_index >= 0
            else self.pointer
        )
        return (
            f"{location}: "
            f"{self.symbol} {self.issue_type}: expected {self.expected}; "
            f"actual {self.actual}"
        )


CANONICAL_SYMBOLS: dict[str, CanonicalSymbol] = {
    "x": CanonicalSymbol(
        symbol="x",
        owner="MIO",
        required_definition_terms=(("departure",), ("scalar",)),
        definition_summary="raw diagnostic departure scalar",
    ),
    "Q": CanonicalSymbol(
        symbol="Q",
        owner="MIO",
        required_definition_terms=(("denominator",), ("policy",)),
        definition_summary="x divided by an explicit denominator policy",
    ),
    "Pi": CanonicalSymbol(
        symbol="Pi",
        owner="MIO",
        required_definition_terms=(("exceedance",), ("threshold",)),
        definition_summary="exceedance curve over an explicit threshold grid",
    ),
    "F": CanonicalSymbol(
        symbol="F",
        owner="MIO",
        required_definition_terms=(
            ("certified",),
            ("filling fraction", "fraction"),
            ("admissible", "ceiling", "sign-clean"),
        ),
        definition_summary="certified filling fraction under admissible ceilings",
    ),
    "G_F": CanonicalSymbol(
        symbol="G_F",
        owner="MIO",
        required_definition_terms=(
            ("depth-gap", "depth gap"),
            ("depth-bin", "depth bin"),
            ("null",),
        ),
        definition_summary="depth-gap diagnostic with depth-bin metadata and null calibration",
    ),
}
DISPLAY_METADATA_SYMBOLS = frozenset({"x", "F"})
COMPARATOR_DISPLAY_SYMBOLS = frozenset({"x", "Q"})


def _issue(
    *,
    row_index: int,
    symbol: str,
    issue_type: str,
    expected: str,
    actual: object,
    pointer: str = SEMANTIC_SPLIT_POINTER,
) -> LabelIssue:
    return LabelIssue(
        row_index=row_index,
        symbol=symbol,
        issue_type=issue_type,
        expected=expected,
        actual=str(actual) if actual not in (None, "") else "<missing>",
        pointer=pointer,
    )


def _normalize(text: object) -> str:
    return str(text).strip().casefold().replace("_", "-")


def _definition_matches(definition: object, required_terms: Sequence[Sequence[str]]) -> bool:
    normalized = _normalize(definition)
    return all(any(term.casefold() in normalized for term in group) for group in required_terms)


def _semantic_split_rows(payload: Mapping[str, Any]) -> list[Any]:
    semantic_and_vectors = payload.get("semantic_and_vectors")
    if not isinstance(semantic_and_vectors, Mapping):
        raise ValueError("missing object at /semantic_and_vectors")
    rows = semantic_and_vectors.get("semantic_split")
    if not isinstance(rows, list):
        raise ValueError(f"missing list at {SEMANTIC_SPLIT_POINTER}")
    return rows


def _display_metadata_issues(
    row: Mapping[str, Any],
    *,
    row_index: int,
    symbol: str,
) -> list[LabelIssue]:
    metadata = row.get("display_metadata")
    if not isinstance(metadata, Mapping):
        return [
            _issue(
                row_index=row_index,
                symbol=symbol,
                issue_type="missing_cancellation_display_metadata",
                expected="display_metadata object with sector/cancellation/M gates",
                actual=type(metadata).__name__,
            )
        ]

    issues: list[LabelIssue] = []
    requirements = (
        ("requires_sector_profile", "missing_cancellation_display_metadata"),
        ("requires_absolute_component_total", "missing_absolute_total_metadata"),
        ("requires_cancellation_index", "missing_cancellation_index_metadata"),
        ("requires_magnitude_companion_M", "missing_magnitude_companion_metadata"),
    )
    for field, issue_type in requirements:
        if metadata.get(field) is not True:
            issues.append(
                _issue(
                    row_index=row_index,
                    symbol=symbol,
                    issue_type=issue_type,
                    expected=f"{field}=true",
                    actual=metadata.get(field),
                )
            )

    interpretation = _normalize(metadata.get("interpretation", ""))
    if "cancellation" not in interpretation or "not isotropy" not in interpretation:
        issues.append(
            _issue(
                row_index=row_index,
                symbol=symbol,
                issue_type="unsafe_cancellation_interpretation",
                expected="interpretation mentions cancellation and not isotropy",
                actual=metadata.get("interpretation", ""),
            )
        )
    return issues


def _has_non_empty_text(metadata: Mapping[str, Any], field: str) -> bool:
    return bool(str(metadata.get(field, "")).strip())


def _has_non_empty_list(metadata: Mapping[str, Any], field: str) -> bool:
    value = metadata.get(field)
    return isinstance(value, list) and bool(value)


def _positive_int(value: object) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = int(value)
    except (TypeError, ValueError):
        return False
    return number >= 1 and number == value


def _comparator_display_issues(
    row: Mapping[str, Any],
    *,
    row_index: int,
    symbol: str,
) -> list[LabelIssue]:
    metadata = row.get("display_metadata")
    if not isinstance(metadata, Mapping):
        return [
            _issue(
                row_index=row_index,
                symbol=symbol,
                issue_type="missing_comparator_display_metadata",
                expected="display_metadata object with comparator/frame/units",
                actual=type(metadata).__name__,
            )
        ]

    issues: list[LabelIssue] = []
    if metadata.get("requires_comparator_label") is not True:
        issues.append(
            _issue(
                row_index=row_index,
                symbol=symbol,
                issue_type="missing_comparator_display_metadata",
                expected="requires_comparator_label=true",
                actual=metadata.get("requires_comparator_label"),
            )
        )
    for field in ("comparator", "frame", "units"):
        if not _has_non_empty_text(metadata, field):
            issues.append(
                _issue(
                    row_index=row_index,
                    symbol=symbol,
                    issue_type=f"missing_{field}_metadata",
                    expected=f"non-empty display_metadata.{field}",
                    actual=metadata.get(field),
                )
            )

    if symbol == "Q":
        for field in ("numerator_policy", "denominator_policy", "denominator_use"):
            if not _has_non_empty_text(metadata, field):
                issues.append(
                    _issue(
                        row_index=row_index,
                        symbol=symbol,
                        issue_type=f"missing_{field}_metadata",
                        expected=f"non-empty display_metadata.{field}",
                        actual=metadata.get(field),
                    )
                )
        has_multiverse_ref = _has_non_empty_text(metadata, "comparator_multiverse_ref")
        has_comparator_labels = _has_non_empty_list(metadata, "comparator_labels")
        has_spread_role = (
            metadata.get("spread_role") == "specification_curve_sensitivity_only"
        )
        has_axis_status = _has_non_empty_text(metadata, "comparator_axis_status")
        has_admissible_status = _has_non_empty_text(metadata, "admissible_set_status")
        has_rank_status = _has_non_empty_text(metadata, "rank_equivalence_status")
        try:
            spread = float(metadata.get("q_spread_absolute"))
            has_spread = spread >= 0.0
        except (TypeError, ValueError):
            has_spread = False
        if not (
            has_multiverse_ref
            and has_comparator_labels
            and has_spread_role
            and has_spread
            and has_axis_status
            and has_admissible_status
            and has_rank_status
        ):
            issues.append(
                _issue(
                    row_index=row_index,
                    symbol=symbol,
                    issue_type="missing_comparator_multiverse_metadata",
                    expected=(
                        "comparator_multiverse_ref, comparator_labels, "
                        "q_spread_absolute, specification-curve spread_role, "
                        "and comparator-axis status metadata"
                    ),
                    actual=metadata,
                )
            )
    return issues


def _q_spread_issues(
    row: Mapping[str, Any],
    *,
    row_index: int,
) -> list[LabelIssue]:
    metadata = row.get("display_metadata")
    if not isinstance(metadata, Mapping):
        return [
            _issue(
                row_index=row_index,
                symbol="Q-spread",
                issue_type="missing_q_spread_contract",
                expected="display_metadata object with Q spread contract",
                actual=type(metadata).__name__,
            )
        ]
    try:
        spread = float(metadata.get("q_spread_absolute"))
        has_spread = spread >= 0.0
    except (TypeError, ValueError):
        has_spread = False
    definition = _normalize(row.get("definition", ""))
    ok = (
        row.get("owner") == "MIO"
        and "specification-curve" in definition
        and "comparator" in definition
        and metadata.get("spread_role") == "specification_curve_sensitivity_only"
        and _has_non_empty_list(metadata, "comparator_labels")
        and has_spread
    )
    if ok:
        return []
    return [
        _issue(
            row_index=row_index,
            symbol="Q-spread",
            issue_type="missing_q_spread_contract",
            expected=(
                "MIO row with comparator specification-curve definition, "
                "comparator_labels, q_spread_absolute, and spread_role"
            ),
            actual=row,
        )
    ]


def _pi_display_issues(
    row: Mapping[str, Any],
    *,
    row_index: int,
) -> list[LabelIssue]:
    metadata = row.get("display_metadata")
    if not isinstance(metadata, Mapping):
        return [
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="missing_pi_display_metadata",
                expected="display_metadata object with measure/threshold policy",
                actual=type(metadata).__name__,
            )
        ]

    issues: list[LabelIssue] = []
    if metadata.get("requires_measure_kind") is not True:
        issues.append(
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="missing_measure_kind_display_metadata",
                expected="requires_measure_kind=true",
                actual=metadata.get("requires_measure_kind"),
            )
        )
    for field, issue_type in (
        ("source_score_label", "missing_source_score_label"),
        ("source_kind", "missing_source_kind"),
        ("measure_kind", "missing_measure_kind"),
        ("threshold_policy", "missing_threshold_policy"),
        ("threshold_registration_status", "missing_threshold_registration_status"),
        ("exceedance_rule", "missing_exceedance_rule"),
        ("calibration_status", "missing_calibration_status"),
        ("covariance_status", "missing_covariance_status"),
        ("null_mock_status", "missing_null_mock_status"),
    ):
        if not _has_non_empty_text(metadata, field):
            issues.append(
                _issue(
                    row_index=row_index,
                    symbol="Pi",
                    issue_type=issue_type,
                    expected=f"non-empty display_metadata.{field}",
                    actual=metadata.get(field),
                )
            )
    if not _has_non_empty_list(metadata, "threshold_grid"):
        issues.append(
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="missing_threshold_grid",
                expected="non-empty display_metadata.threshold_grid",
                actual=metadata.get("threshold_grid"),
            )
        )
    if not _positive_int(metadata.get("look_elsewhere_trials")):
        issues.append(
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="missing_look_elsewhere_trials",
                expected="positive integer display_metadata.look_elsewhere_trials",
                actual=metadata.get("look_elsewhere_trials"),
            )
        )
    if metadata.get("p_value_interpretation_status") != "blocked_exceedance_not_p_value":
        issues.append(
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="missing_p_value_block_status",
                expected="blocked_exceedance_not_p_value",
                actual=metadata.get("p_value_interpretation_status"),
            )
        )
    if metadata.get("calibration_status") != "raw_exceedance_only_uncalibrated_no_p_value":
        issues.append(
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="bad_pi_calibration_status",
                expected="raw_exceedance_only_uncalibrated_no_p_value",
                actual=metadata.get("calibration_status"),
            )
        )
    blocked = metadata.get("blocked_use_codes")
    blocked_set = {str(item) for item in blocked} if isinstance(blocked, list) else set()
    if not REQUIRED_PI_BLOCKED_USE_CODES <= blocked_set:
        issues.append(
            _issue(
                row_index=row_index,
                symbol="Pi",
                issue_type="missing_pi_blocked_use_codes",
                expected="blocked_use_codes includes all forbidden Pi interpretations",
                actual=blocked,
            )
        )
    return issues


def validate_rows(rows: Iterable[Any]) -> list[LabelIssue]:
    issues: list[LabelIssue] = []
    for row_index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        symbol = str(row.get("symbol", ""))
        if symbol == "Q-spread":
            issues.extend(_q_spread_issues(row, row_index=row_index))
            continue
        canonical = CANONICAL_SYMBOLS.get(symbol)
        if canonical is None:
            continue

        owner = str(row.get("owner", ""))
        if owner != canonical.owner:
            issues.append(
                LabelIssue(
                    row_index=row_index,
                    symbol=symbol,
                    issue_type="owner_mismatch",
                    expected=canonical.owner,
                    actual=owner or "<missing>",
                )
            )

        definition = str(row.get("definition", ""))
        if not _definition_matches(definition, canonical.required_definition_terms):
            issues.append(
                LabelIssue(
                    row_index=row_index,
                    symbol=symbol,
                    issue_type="definition_mismatch",
                    expected=canonical.definition_summary,
                    actual=definition or "<missing>",
                )
            )
        if symbol in DISPLAY_METADATA_SYMBOLS:
            issues.extend(
                _display_metadata_issues(
                    row,
                    row_index=row_index,
                    symbol=symbol,
                )
            )
        if symbol in COMPARATOR_DISPLAY_SYMBOLS:
            issues.extend(
                _comparator_display_issues(
                    row,
                    row_index=row_index,
                    symbol=symbol,
                )
            )
        if symbol == "Pi":
            issues.extend(_pi_display_issues(row, row_index=row_index))
    return issues


def _validate_departure_display_contract(
    semantic_and_vectors: Mapping[str, Any],
) -> list[LabelIssue]:
    contract = semantic_and_vectors.get("departure_display_contract")
    if not isinstance(contract, Mapping):
        return [
            _issue(
                row_index=-1,
                symbol="x/F",
                issue_type="missing_departure_display_contract",
                expected="departure_display_contract object",
                actual=type(contract).__name__,
                pointer=DEPARTURE_DISPLAY_CONTRACT_POINTER,
            )
        ]

    issues: list[LabelIssue] = []
    expected_symbols = ["x", "F"]
    if contract.get("required_for_symbols") != expected_symbols:
        issues.append(
            _issue(
                row_index=-1,
                symbol="x/F",
                issue_type="bad_departure_display_symbols",
                expected=str(expected_symbols),
                actual=contract.get("required_for_symbols"),
                pointer=DEPARTURE_DISPLAY_CONTRACT_POINTER,
            )
        )
    for field in (
        "requires_sector_profile",
        "requires_absolute_component_total",
        "requires_cancellation_index",
        "requires_magnitude_companion_M",
    ):
        if contract.get(field) is not True:
            issues.append(
                _issue(
                    row_index=-1,
                    symbol="x/F",
                    issue_type=f"missing_contract_{field}",
                    expected=f"{field}=true",
                    actual=contract.get(field),
                    pointer=DEPARTURE_DISPLAY_CONTRACT_POINTER,
                )
            )
    return issues


def _validate_cancellation_counterexample(
    semantic_and_vectors: Mapping[str, Any],
) -> list[LabelIssue]:
    counterexample = semantic_and_vectors.get("cancellation_counterexample")
    if not isinstance(counterexample, Mapping):
        return [
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="missing_cancellation_counterexample",
                expected="cancellation_counterexample object",
                actual=type(counterexample).__name__,
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        ]

    issues: list[LabelIssue] = []
    try:
        x_c = float(counterexample.get("x_C"))
        absolute_total = float(counterexample.get("absolute_component_total"))
        cancellation_index = float(counterexample.get("cancellation_index"))
        magnitude = float(counterexample.get("M_sector_magnitude"))
    except (TypeError, ValueError):
        return [
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="invalid_cancellation_counterexample_numbers",
                expected="numeric x_C, absolute total, cancellation index, and M",
                actual=counterexample,
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        ]

    if abs(x_c) > 1.0e-12:
        issues.append(
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="bad_counterexample_x_C",
                expected="x_C approximately 0",
                actual=x_c,
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        )
    if absolute_total <= 0.0:
        issues.append(
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="bad_counterexample_absolute_total",
                expected="absolute_component_total > 0",
                actual=absolute_total,
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        )
    if abs(cancellation_index - 1.0) > 1.0e-12:
        issues.append(
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="bad_counterexample_cancellation_index",
                expected="cancellation_index approximately 1",
                actual=cancellation_index,
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        )
    if magnitude <= 0.0:
        issues.append(
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="bad_counterexample_magnitude",
                expected="M_sector_magnitude > 0",
                actual=magnitude,
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        )
    interpretation = _normalize(counterexample.get("interpretation", ""))
    if "cancellation" not in interpretation or "not isotropy" not in interpretation:
        issues.append(
            _issue(
                row_index=-1,
                symbol="x",
                issue_type="unsafe_counterexample_interpretation",
                expected="counterexample states cancellation and not isotropy",
                actual=counterexample.get("interpretation", ""),
                pointer=CANCELLATION_COUNTEREXAMPLE_POINTER,
            )
        )
    return issues


def _float_equal(left: object, right: object, *, tolerance: float = 1.0e-12) -> bool:
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return False


def _row_by_symbol(rows: Iterable[Any], symbol: str) -> Mapping[str, Any] | None:
    for row in rows:
        if isinstance(row, Mapping) and row.get("symbol") == symbol:
            return row
    return None


def _validate_q_summary(
    payload: Mapping[str, Any],
    rows: list[Any],
) -> list[LabelIssue]:
    transfer = payload.get("transfer_sensitivity")
    if not isinstance(transfer, Mapping):
        return [
            _issue(
                row_index=-1,
                symbol="Q",
                issue_type="missing_q_comparator_multiverse_summary",
                expected="transfer_sensitivity object with q_comparator_multiverse",
                actual=type(transfer).__name__,
                pointer=Q_MULTIVERSE_POINTER,
            )
        ]
    summary = transfer.get("q_comparator_multiverse")
    if not isinstance(summary, Mapping):
        return [
            _issue(
                row_index=-1,
                symbol="Q",
                issue_type="missing_q_comparator_multiverse_summary",
                expected="q_comparator_multiverse object",
                actual=type(summary).__name__,
                pointer=Q_MULTIVERSE_POINTER,
            )
        ]

    issues: list[LabelIssue] = []
    required_fields = (
        "summary_label",
        "summary_kind",
        "baseline_comparator",
        "baseline_q",
        "comparator_labels",
        "q_spread_absolute",
        "q_spread_relative_to_baseline",
        "config_hash",
        "comparator_axis_status",
        "admissible_set_status",
        "rank_equivalence_status",
    )
    for field in required_fields:
        if field not in summary or summary.get(field) in (None, "", []):
            issues.append(
                _issue(
                    row_index=-1,
                    symbol="Q",
                    issue_type="bad_q_comparator_summary",
                    expected=f"non-empty q_comparator_multiverse.{field}",
                    actual=summary.get(field),
                    pointer=Q_MULTIVERSE_POINTER,
                )
            )
    if summary.get("summary_label") != "Q_comparator_multiverse":
        issues.append(
            _issue(
                row_index=-1,
                symbol="Q",
                issue_type="bad_q_comparator_summary",
                expected="summary_label=Q_comparator_multiverse",
                actual=summary.get("summary_label"),
                pointer=Q_MULTIVERSE_POINTER,
            )
        )
    display = summary.get("display_metadata")
    if not isinstance(display, Mapping):
        issues.append(
            _issue(
                row_index=-1,
                symbol="Q",
                issue_type="bad_q_comparator_summary",
                expected="summary display_metadata object",
                actual=type(display).__name__,
                pointer=Q_MULTIVERSE_POINTER,
            )
        )

    q_row = _row_by_symbol(rows, "Q")
    if q_row is None:
        return issues
    row_display = q_row.get("display_metadata")
    if not isinstance(row_display, Mapping):
        return issues

    expected_pairs = (
        ("comparator", "baseline_comparator"),
        ("baseline_comparator", "baseline_comparator"),
        ("config_hash", "config_hash"),
        ("comparator_axis_status", "comparator_axis_status"),
        ("admissible_set_status", "admissible_set_status"),
        ("rank_equivalence_status", "rank_equivalence_status"),
    )
    mismatch = False
    for row_field, summary_field in expected_pairs:
        if row_display.get(row_field) != summary.get(summary_field):
            mismatch = True
    for field in ("comparator_labels",):
        if row_display.get(field) != summary.get(field):
            mismatch = True
    for field in ("q_spread_absolute", "q_spread_relative_to_baseline"):
        if not _float_equal(row_display.get(field), summary.get(field)):
            mismatch = True
    if not _float_equal(q_row.get("display_value"), summary.get("baseline_q")):
        mismatch = True
    if mismatch:
        issues.append(
            _issue(
                row_index=rows.index(q_row),
                symbol="Q",
                issue_type="q_comparator_summary_mismatch",
                expected="Q row display metadata matches q_comparator_multiverse",
                actual=row_display,
            )
        )

    q_spread_row = _row_by_symbol(rows, "Q-spread")
    if q_spread_row is not None:
        q_spread_display = q_spread_row.get("display_metadata")
        if not isinstance(q_spread_display, Mapping) or not _float_equal(
            q_spread_row.get("display_value"),
            summary.get("q_spread_absolute"),
        ):
            issues.append(
                _issue(
                    row_index=rows.index(q_spread_row),
                    symbol="Q-spread",
                    issue_type="q_spread_summary_mismatch",
                    expected="Q-spread display matches q_comparator_multiverse",
                    actual=q_spread_row,
                )
            )
    return issues


def _validate_pi_policy_summary(
    payload: Mapping[str, Any],
    semantic_and_vectors: Mapping[str, Any],
) -> list[LabelIssue]:
    transfer = payload.get("transfer_sensitivity")
    if not isinstance(transfer, Mapping):
        return [
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="missing_pi_policy_summary",
                expected="transfer_sensitivity object with pi_policy_summary",
                actual=type(transfer).__name__,
                pointer=PI_POLICY_POINTER,
            )
        ]
    summary = transfer.get("pi_policy_summary")
    if not isinstance(summary, Mapping):
        return [
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="missing_pi_policy_summary",
                expected="pi_policy_summary object",
                actual=type(summary).__name__,
                pointer=PI_POLICY_POINTER,
            )
        ]

    issues: list[LabelIssue] = []
    if summary.get("summary_label") != "Pi_policy_display_contract":
        issues.append(
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="bad_pi_policy_summary",
                expected="summary_label=Pi_policy_display_contract",
                actual=summary.get("summary_label"),
                pointer=PI_POLICY_POINTER,
            )
        )
    if summary.get("summary_kind") != "noncanonical_pi_policy_metadata_summary":
        issues.append(
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="bad_pi_policy_summary",
                expected="summary_kind=noncanonical_pi_policy_metadata_summary",
                actual=summary.get("summary_kind"),
                pointer=PI_POLICY_POINTER,
            )
        )
    if "pi_grid" in summary or "exceedance_fractions" in summary:
        issues.append(
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="canonical_pi_curve_exported_as_policy_summary",
                expected="policy summary without pi_grid/exceedance_fractions",
                actual=summary.keys(),
                pointer=PI_POLICY_POINTER,
            )
        )
    display = summary.get("display_metadata")
    if not isinstance(display, Mapping):
        issues.append(
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="missing_pi_policy_summary",
                expected="pi_policy_summary.display_metadata object",
                actual=type(display).__name__,
                pointer=PI_POLICY_POINTER,
            )
        )
    else:
        issues.extend(
            LabelIssue(
                row_index=-1,
                symbol=issue.symbol,
                issue_type=issue.issue_type,
                expected=issue.expected,
                actual=issue.actual,
                pointer=PI_POLICY_POINTER,
            )
            for issue in _pi_display_issues(
                {"display_metadata": display},
                row_index=-1,
            )
        )

    contract = semantic_and_vectors.get("pi_display_contract")
    if not isinstance(contract, Mapping):
        issues.append(
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="missing_pi_display_contract",
                expected="semantic_and_vectors.pi_display_contract object",
                actual=type(contract).__name__,
                pointer=PI_DISPLAY_CONTRACT_POINTER,
            )
        )
    elif isinstance(display, Mapping) and contract != display:
        issues.append(
            _issue(
                row_index=-1,
                symbol="Pi",
                issue_type="pi_display_contract_mismatch",
                expected="pi_display_contract equals pi_policy_summary.display_metadata",
                actual=contract,
                pointer=PI_DISPLAY_CONTRACT_POINTER,
            )
        )
    return issues


def validate_payload(payload: Mapping[str, Any]) -> list[LabelIssue]:
    semantic_and_vectors = payload.get("semantic_and_vectors")
    if not isinstance(semantic_and_vectors, Mapping):
        raise ValueError("missing object at /semantic_and_vectors")
    rows = _semantic_split_rows(payload)
    issues = validate_rows(rows)
    present = {
        str(row.get("symbol", ""))
        for row in rows
        if isinstance(row, Mapping)
    }
    if present & DISPLAY_METADATA_SYMBOLS:
        issues.extend(_validate_departure_display_contract(semantic_and_vectors))
        issues.extend(_validate_cancellation_counterexample(semantic_and_vectors))
    issues.extend(_validate_q_summary(payload, rows))
    issues.extend(_validate_pi_policy_summary(payload, semantic_and_vectors))
    return issues


def _load_payload(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("payload root must be a JSON object")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate canonical x/Q/Pi/F/G_F labels in current science figure payloads."
    )
    parser.add_argument("payload", type=Path, help="Path to current_science_plot_payload.json")
    args = parser.parse_args(argv)

    try:
        issues = validate_payload(_load_payload(args.payload))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if issues:
        for issue in issues:
            print(issue.render(), file=sys.stderr)
        return 1

    print(f"OK: canonical formalism labels valid in {args.payload}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
