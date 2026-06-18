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

    def render(self) -> str:
        return (
            f"{SEMANTIC_SPLIT_POINTER}/{self.row_index}: "
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
    return issues


def validate_payload(payload: Mapping[str, Any]) -> list[LabelIssue]:
    return validate_rows(_semantic_split_rows(payload))


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
