"""MIO departure bundle with explicit comparator and frame metadata."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from common.transfer_registry import (
    TransferSource,
    validate_transfer_dependent_result,
)

from .component_breakdown import ComponentBreakdown, build_component_breakdown


DEFAULT_CAVEAT = (
    "x_C is a signed comparator projection and not an anisotropy norm, "
    "HTT inference quantity, model ranking, or scalar classifier; x_C near zero can "
    "reflect inter-sector cancellation rather than isotropy."
)


def _non_empty(value: object, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _tuple_of_str(values: Sequence[object], name: str) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in values)
    if any(not value for value in result):
        raise ValueError(f"{name} must contain only non-empty strings")
    return result


@dataclass(frozen=True)
class DepartureBundle:
    """Diagnostic ``x_C`` bundle for MIO-owned pre-solver reports."""

    component_breakdown: ComponentBreakdown
    comparator: str
    frame: str
    units: str
    config_hash: str
    input_hashes: tuple[str, ...]
    transfer_source: str = "none"
    transfer_spec_id: str | None = None
    transfer_metadata: Mapping[str, object] | None = None
    claim_tier: str = "diagnostic_only"
    owner: str = "MIO"
    implementation_scope: str = "mio"
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_CAVEAT,))

    def __post_init__(self) -> None:
        comparator = _non_empty(self.comparator, "comparator")
        frame = _non_empty(self.frame, "frame")
        units = _non_empty(self.units, "units")
        config_hash = _non_empty(self.config_hash, "config_hash")
        transfer_source = _non_empty(self.transfer_source, "transfer_source")
        transfer_spec_id = (
            None
            if self.transfer_spec_id is None
            else _non_empty(self.transfer_spec_id, "transfer_spec_id")
        )
        input_hashes = _tuple_of_str(self.input_hashes, "input_hashes")
        if not input_hashes:
            raise ValueError("input_hashes must contain at least one hash")
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_CAVEAT not in caveats:
            caveats = (DEFAULT_CAVEAT, *caveats)
        transfer_metadata = (
            None if self.transfer_metadata is None else dict(self.transfer_metadata)
        )
        canonical_transfer_source = TransferSource(transfer_source)
        if (
            canonical_transfer_source is not TransferSource.NONE
            and transfer_metadata is None
        ):
            raise ValueError(
                "transfer-derived DepartureBundle requires transfer_metadata"
            )
        if transfer_metadata is not None:
            validate_transfer_dependent_result(transfer_metadata)
            metadata_source = str(transfer_metadata["transfer_source"])
            if metadata_source != canonical_transfer_source.value:
                raise ValueError(
                    "DepartureBundle transfer_source must match transfer_metadata"
                )

        if self.component_breakdown.comparator != comparator:
            raise ValueError("DepartureBundle comparator must match component breakdown")
        if self.component_breakdown.frame != frame:
            raise ValueError("DepartureBundle frame must match component breakdown")
        if self.component_breakdown.units != units:
            raise ValueError("DepartureBundle units must match component breakdown")
        if self.owner != "MIO":
            raise ValueError("DepartureBundle owner must be 'MIO'")
        if self.claim_tier != "diagnostic_only":
            raise ValueError("DepartureBundle claim_tier must be 'diagnostic_only'")
        if self.implementation_scope != "mio":
            raise ValueError("DepartureBundle implementation_scope must be 'mio'")
        if transfer_source == "BASS_native_validated" and transfer_spec_id is None:
            raise ValueError(
                "native transfer provenance requires an explicit transfer_spec_id"
            )

        object.__setattr__(self, "comparator", comparator)
        object.__setattr__(self, "frame", frame)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "transfer_source", transfer_source)
        object.__setattr__(self, "transfer_spec_id", transfer_spec_id)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "caveats", caveats)

    @property
    def x_C(self) -> float:
        return self.component_breakdown.x_C

    @property
    def cancellation_index(self) -> float:
        return self.component_breakdown.cancellation_index

    @property
    def absolute_component_total(self) -> float:
        return self.component_breakdown.absolute_component_total

    @property
    def sector_magnitude_companion(self) -> float:
        return self.component_breakdown.sector_magnitude_companion

    @property
    def total_anisotropy_magnitude(self) -> float:
        return self.sector_magnitude_companion

    @property
    def sector_profile(self) -> dict[str, object]:
        return self.component_breakdown.sector_profile

    @property
    def display_metadata(self) -> dict[str, object]:
        return {
            "requires_sector_profile": True,
            "requires_absolute_component_total": True,
            "requires_cancellation_index": True,
            "requires_magnitude_companion_M": True,
            "requires_comparator": True,
            "M_key": "sector_magnitude_companion",
            "x_C_interpretation": (
                "signed comparator projection; near-zero x_C is not isotropy "
                "without the sector profile"
            ),
            "blocked_use_codes": [
                "isotropy_certificate",
                "scalar_classification",
                "htt_inference_consumption",
                "solver_validation",
            ],
        }

    def as_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "comparator": self.comparator,
            "frame": self.frame,
            "units": self.units,
            "x_C": self.x_C,
            "cancellation_index": self.cancellation_index,
            "absolute_component_total": self.absolute_component_total,
            "sector_magnitude_companion": self.sector_magnitude_companion,
            "sector_profile": self.sector_profile,
            "display_metadata": self.display_metadata,
            "component_breakdown": self.component_breakdown.as_payload(),
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": self.transfer_metadata,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "caveats": list(self.caveats),
        }


def build_departure_bundle(
    components: Mapping[str, float],
    *,
    comparator: str,
    frame: str,
    units: str,
    config_hash: str,
    input_hashes: Sequence[object],
    transfer_source: str = "none",
    transfer_spec_id: str | None = None,
    transfer_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] = (),
) -> DepartureBundle:
    """Build a validated MIO diagnostic departure bundle."""

    breakdown = build_component_breakdown(
        components,
        comparator=comparator,
        frame=frame,
        units=units,
    )
    return DepartureBundle(
        component_breakdown=breakdown,
        comparator=comparator,
        frame=frame,
        units=units,
        config_hash=config_hash,
        input_hashes=tuple(input_hashes),
        transfer_source=transfer_source,
        transfer_spec_id=transfer_spec_id,
        transfer_metadata=transfer_metadata,
        caveats=tuple(caveats) or (DEFAULT_CAVEAT,),
    )


__all__ = [
    "DEFAULT_CAVEAT",
    "DepartureBundle",
    "build_departure_bundle",
]
