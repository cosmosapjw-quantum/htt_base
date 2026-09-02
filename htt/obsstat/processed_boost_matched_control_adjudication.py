"""Fail-closed adjudication for PMG-WU-011 Task-7C matched controls.

The matched full-sky receipt is an engineering calibration artifact.  This
module converts its rank-decision rows into a typed, non-scientific status:

* ambiguity or control-factor instability -> rank unresolved;
* stable resolved non-containment -> survivor present;
* stable resolved containment in every registered row -> containment candidate.

The last state is still only a candidate.  It does not authorize an empirical
velocity fit, a global-tilt interpretation, Bianchi attribution, or claim
promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Iterable, Mapping


_ADJUDICATION_SCHEMA = "HTT_WU011_TASK7C_MATCHED_CONTROL_ADJUDICATION_V1"
_REQUIRED_FIELDS = (
    "direction_id",
    "source_cutoff",
    "control_safety_factor",
    "rank_status",
    "high_rank",
    "surviving_rank",
    "augmented_rank_increment",
    "rank_identity_holds",
    "containment_witness",
)


class MatchedControlAdjudicationError(ValueError):
    """Raised when matched-control decision rows are malformed or incomplete."""


class MatchedControlAdjudicationTerminal(str, Enum):
    """Typed non-scientific outcomes of the matched-control rank audit."""

    RANK_UNRESOLVED = "PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED"
    SURVIVOR_PRESENT = "PASS_TASK7C_MATCHED_CONTROL_SURVIVOR_PRESENT"
    CONTAINMENT_CANDIDATE = "PASS_TASK7C_MATCHED_CONTROL_CONTAINMENT_CANDIDATE"


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _parse_int(value: object, *, label: str, allow_empty: bool = False) -> int | None:
    if allow_empty and (value is None or value == ""):
        return None
    if isinstance(value, bool):
        raise MatchedControlAdjudicationError(f"{label} is not an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise MatchedControlAdjudicationError(f"{label} is not an integer") from exc
    if isinstance(value, float) and not value.is_integer():
        raise MatchedControlAdjudicationError(f"{label} is not an integer")
    return parsed


def _parse_float(value: object, *, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise MatchedControlAdjudicationError(f"{label} is not finite") from exc
    if not math.isfinite(parsed):
        raise MatchedControlAdjudicationError(f"{label} is not finite")
    return parsed


def _parse_bool(value: object, *, label: str, allow_empty: bool = False) -> bool | None:
    if allow_empty and (value is None or value == ""):
        return None
    if type(value) is bool:
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise MatchedControlAdjudicationError(f"{label} is not a boolean")


@dataclass(frozen=True)
class _NormalizedRankRecord:
    direction_id: str
    source_cutoff: int
    control_safety_factor: float
    rank_status: str
    high_rank: int
    surviving_rank: int | None
    augmented_rank_increment: int | None
    rank_identity_holds: bool | None
    containment_witness: bool | None

    def __post_init__(self) -> None:
        if not self.direction_id:
            raise MatchedControlAdjudicationError("direction ID is absent")
        if self.source_cutoff < 7:
            raise MatchedControlAdjudicationError("source cutoff is outside its domain")
        if self.control_safety_factor <= 1.0:
            raise MatchedControlAdjudicationError(
                "control safety factor must exceed one"
            )
        if self.rank_status not in ("RESOLVED", "AMBIGUOUS"):
            raise MatchedControlAdjudicationError("rank status is outside the registry")
        if self.high_rank < 0:
            raise MatchedControlAdjudicationError("high rank is negative")
        if self.rank_status == "AMBIGUOUS":
            if any(
                value is not None
                for value in (
                    self.surviving_rank,
                    self.augmented_rank_increment,
                    self.rank_identity_holds,
                    self.containment_witness,
                )
            ):
                raise MatchedControlAdjudicationError(
                    "ambiguous rank row carries a resolved decision"
                )
        else:
            if (
                self.surviving_rank is None
                or self.augmented_rank_increment is None
                or self.rank_identity_holds is None
                or self.containment_witness is None
            ):
                raise MatchedControlAdjudicationError(
                    "resolved rank row is incomplete"
                )
            if self.surviving_rank < 0 or self.augmented_rank_increment < 0:
                raise MatchedControlAdjudicationError("resolved rank is negative")
            if not self.rank_identity_holds:
                raise MatchedControlAdjudicationError(
                    "resolved row violates the augmented-rank identity"
                )
            expected_containment = (
                self.surviving_rank == 0
                and self.augmented_rank_increment == 0
            )
            if self.containment_witness != expected_containment:
                raise MatchedControlAdjudicationError(
                    "containment flag contradicts the resolved ranks"
                )

    @property
    def coordinate(self) -> tuple[str, int]:
        return self.direction_id, self.source_cutoff

    @property
    def decision_signature(self) -> tuple[object, ...]:
        return (
            self.rank_status,
            self.high_rank,
            self.surviving_rank,
            self.augmented_rank_increment,
            self.rank_identity_holds,
            self.containment_witness,
        )


def _normalize_record(record: Mapping[str, object]) -> _NormalizedRankRecord:
    missing = [field for field in _REQUIRED_FIELDS if field not in record]
    if missing:
        raise MatchedControlAdjudicationError(
            "matched-control row misses fields: " + ",".join(missing)
        )
    status = str(record["rank_status"])
    ambiguous = status == "AMBIGUOUS"
    return _NormalizedRankRecord(
        direction_id=str(record["direction_id"]),
        source_cutoff=_parse_int(record["source_cutoff"], label="source cutoff") or 0,
        control_safety_factor=_parse_float(
            record["control_safety_factor"],
            label="control safety factor",
        ),
        rank_status=status,
        high_rank=_parse_int(record["high_rank"], label="high rank") or 0,
        surviving_rank=_parse_int(
            record["surviving_rank"],
            label="surviving rank",
            allow_empty=ambiguous,
        ),
        augmented_rank_increment=_parse_int(
            record["augmented_rank_increment"],
            label="augmented-rank increment",
            allow_empty=ambiguous,
        ),
        rank_identity_holds=_parse_bool(
            record["rank_identity_holds"],
            label="rank-identity flag",
            allow_empty=ambiguous,
        ),
        containment_witness=_parse_bool(
            record["containment_witness"],
            label="containment flag",
            allow_empty=ambiguous,
        ),
    )


@dataclass(frozen=True)
class MatchedControlAdjudication:
    """Immutable aggregate decision for one matched-control receipt."""

    terminal: MatchedControlAdjudicationTerminal
    nominal_control_factor: float
    row_count: int
    coordinate_count: int
    nominal_row_count: int
    nominal_ambiguous_count: int
    nominal_resolved_count: int
    nominal_survivor_count: int
    nominal_containment_count: int
    sensitivity_stable: bool
    unstable_coordinates: tuple[tuple[str, int], ...]
    factor_registry: tuple[float, ...]
    scientific_terminal_authorized: bool
    claim_promotion: bool
    content_id: str

    def __post_init__(self) -> None:
        if self.scientific_terminal_authorized or self.claim_promotion:
            raise MatchedControlAdjudicationError(
                "matched-control adjudication cannot promote a scientific claim"
            )
        if not self.content_id.startswith("sha256:"):
            raise MatchedControlAdjudicationError("adjudication identity is invalid")

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": _ADJUDICATION_SCHEMA,
                "terminal": self.terminal.value,
                "nominal_control_factor": self.nominal_control_factor,
                "row_count": self.row_count,
                "coordinate_count": self.coordinate_count,
                "nominal_row_count": self.nominal_row_count,
                "nominal_ambiguous_count": self.nominal_ambiguous_count,
                "nominal_resolved_count": self.nominal_resolved_count,
                "nominal_survivor_count": self.nominal_survivor_count,
                "nominal_containment_count": self.nominal_containment_count,
                "sensitivity_stable": self.sensitivity_stable,
                "unstable_coordinates": [
                    {"direction_id": direction, "source_cutoff": cutoff}
                    for direction, cutoff in self.unstable_coordinates
                ],
                "factor_registry": list(self.factor_registry),
                "scientific_terminal_authorized": False,
                "claim_promotion": False,
                "content_id": self.content_id,
            }
        )


def adjudicate_rank_records(
    records: Iterable[Mapping[str, object]],
    *,
    nominal_control_factor: float = 5.0,
) -> MatchedControlAdjudication:
    """Aggregate matched-control rows without converting ambiguity to rank."""

    nominal = _parse_float(
        nominal_control_factor,
        label="nominal control safety factor",
    )
    normalized = tuple(_normalize_record(record) for record in records)
    if not normalized:
        raise MatchedControlAdjudicationError("matched-control row registry is empty")

    keys = [
        (record.direction_id, record.source_cutoff, record.control_safety_factor)
        for record in normalized
    ]
    if len(set(keys)) != len(keys):
        raise MatchedControlAdjudicationError("matched-control row registry is duplicated")

    factor_registry = tuple(sorted({record.control_safety_factor for record in normalized}))
    if nominal not in factor_registry:
        raise MatchedControlAdjudicationError(
            "nominal control safety factor is absent from the registry"
        )
    coordinates = tuple(sorted({record.coordinate for record in normalized}))
    expected_factors = set(factor_registry)
    grouped: dict[tuple[str, int], list[_NormalizedRankRecord]] = {
        coordinate: [] for coordinate in coordinates
    }
    for record in normalized:
        grouped[record.coordinate].append(record)
    for coordinate, group in grouped.items():
        if {record.control_safety_factor for record in group} != expected_factors:
            raise MatchedControlAdjudicationError(
                f"control-factor registry is incomplete at {coordinate}"
            )

    nominal_rows = tuple(
        record for record in normalized if record.control_safety_factor == nominal
    )
    if len(nominal_rows) != len(coordinates):
        raise MatchedControlAdjudicationError("nominal matched-control slice is incomplete")

    unstable: list[tuple[str, int]] = []
    for coordinate, group in grouped.items():
        signatures = {record.decision_signature for record in group}
        if (
            len(signatures) != 1
            or any(record.rank_status != "RESOLVED" for record in group)
        ):
            unstable.append(coordinate)
    sensitivity_stable = not unstable

    ambiguous_count = sum(record.rank_status == "AMBIGUOUS" for record in nominal_rows)
    resolved_rows = tuple(record for record in nominal_rows if record.rank_status == "RESOLVED")
    survivor_count = sum(record.containment_witness is False for record in resolved_rows)
    containment_count = sum(record.containment_witness is True for record in resolved_rows)

    if ambiguous_count or not sensitivity_stable:
        terminal = MatchedControlAdjudicationTerminal.RANK_UNRESOLVED
    elif containment_count == len(nominal_rows):
        terminal = MatchedControlAdjudicationTerminal.CONTAINMENT_CANDIDATE
    else:
        terminal = MatchedControlAdjudicationTerminal.SURVIVOR_PRESENT

    payload = {
        "terminal": terminal.value,
        "nominal_control_factor_hex": nominal.hex(),
        "row_count": len(normalized),
        "coordinate_count": len(coordinates),
        "nominal_row_count": len(nominal_rows),
        "nominal_ambiguous_count": ambiguous_count,
        "nominal_resolved_count": len(resolved_rows),
        "nominal_survivor_count": survivor_count,
        "nominal_containment_count": containment_count,
        "sensitivity_stable": sensitivity_stable,
        "unstable_coordinates": [list(item) for item in unstable],
        "factor_registry_hex": [factor.hex() for factor in factor_registry],
        "scientific_terminal_authorized": False,
        "claim_promotion": False,
    }
    content_id = "sha256:" + hashlib.sha256(
        _ADJUDICATION_SCHEMA.encode("ascii") + b"\0" + _canonical_json(payload)
    ).hexdigest()
    return MatchedControlAdjudication(
        terminal=terminal,
        nominal_control_factor=nominal,
        row_count=len(normalized),
        coordinate_count=len(coordinates),
        nominal_row_count=len(nominal_rows),
        nominal_ambiguous_count=ambiguous_count,
        nominal_resolved_count=len(resolved_rows),
        nominal_survivor_count=survivor_count,
        nominal_containment_count=containment_count,
        sensitivity_stable=sensitivity_stable,
        unstable_coordinates=tuple(unstable),
        factor_registry=factor_registry,
        scientific_terminal_authorized=False,
        claim_promotion=False,
        content_id=content_id,
    )


__all__ = [
    "MatchedControlAdjudication",
    "MatchedControlAdjudicationError",
    "MatchedControlAdjudicationTerminal",
    "adjudicate_rank_records",
]
