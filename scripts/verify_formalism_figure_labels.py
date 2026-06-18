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


def validate_rows(rows: Iterable[Any]) -> list[LabelIssue]:
    issues: list[LabelIssue] = []
    for row_index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        symbol = str(row.get("symbol", ""))
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
