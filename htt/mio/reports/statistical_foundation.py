"""Typed MIO result card for the rebuilt statistical foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from common.mes_successor_registry import current_mes_successor_registry
from common.orbit_nonlinearity import NonlinearityReport
from common.statistical_foundations import (
    AnchorStressReport,
    DepartureState,
    IdentifiedDepartureSet,
    LegacyProjectionReport,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id


@dataclass(frozen=True)
class StatisticalFoundationResultCard:
    """Keep state, identification, anchor stress and nonlinearity disjoint.

    This diagnostic card is deliberately not a posterior, evidence bundle,
    morphology/family classifier, or automatic bridge between output spaces.
    """

    card_id: str
    departure_state: DepartureState | None = None
    identified_set: IdentifiedDepartureSet | None = None
    anchor_stress: AnchorStressReport | None = None
    legacy_projection: LegacyProjectionReport | None = None
    nonlinearity: NonlinearityReport | None = None
    morphology_reference: Mapping[str, str] | None = None
    owner: str = "MIO"
    status: str = "diagnostic_only"
    allowed_use: tuple[str, ...] = (
        "typed diagnostic reporting",
        "separate output-space comparison",
    )
    forbidden_use: tuple[str, ...] = (
        "MIO posterior",
        "evidence",
        "FLRW converse",
        "geometry detection",
        "Bianchi family identification",
        "automatic cross-space conversion",
    )

    def __post_init__(self) -> None:
        if not isinstance(self.card_id, str) or not self.card_id.strip():
            raise ValueError("card_id must be non-empty")
        if self.owner != "MIO" or self.status != "diagnostic_only":
            raise ValueError("foundation result cards are MIO diagnostic-only")
        if all(
            value is None
            for value in (
                self.departure_state,
                self.identified_set,
                self.anchor_stress,
                self.legacy_projection,
                self.nonlinearity,
                self.morphology_reference,
            )
        ):
            raise ValueError("foundation result card requires at least one section")
        expected_types = (
            ("departure_state", self.departure_state, DepartureState),
            ("identified_set", self.identified_set, IdentifiedDepartureSet),
            ("anchor_stress", self.anchor_stress, AnchorStressReport),
            ("legacy_projection", self.legacy_projection, LegacyProjectionReport),
            ("nonlinearity", self.nonlinearity, NonlinearityReport),
        )
        for name, value, expected_type in expected_types:
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(f"{name} must be {expected_type.__name__} or None")
        if self.morphology_reference is not None:
            reference = dict(self.morphology_reference)
            required = {"artifact_id", "owner", "status"}
            if set(reference) != required:
                raise ValueError(
                    "morphology_reference requires artifact_id/owner/status"
                )
            if reference["owner"] != "OBSSTAT":
                raise ValueError("morphology_reference must remain OBSSTAT-owned")
            object.__setattr__(self, "morphology_reference", reference)

    def as_payload(self) -> dict[str, object]:
        def payload(value):
            return None if value is None else asdict(value)

        return {
            "schema": "mio.statistical_foundation_result_card.v1",
            "card_id": self.card_id,
            "owner": self.owner,
            "status": self.status,
            "output_spaces": {
                "departure_state": payload(self.departure_state),
                "identified_set": payload(self.identified_set),
                "anchor_stress": payload(self.anchor_stress),
                "legacy_projection": payload(self.legacy_projection),
                "nonlinearity": payload(self.nonlinearity),
                "morphology_reference": (
                    None
                    if self.morphology_reference is None
                    else dict(self.morphology_reference)
                ),
            },
            "automatic_conversion": False,
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


__all__ = ["StatisticalFoundationResultCard"]
