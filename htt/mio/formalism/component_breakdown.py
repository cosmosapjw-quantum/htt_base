"""Component-level MIO departure-coordinate bookkeeping."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math


CANONICAL_COMPONENT_SIGNS: dict[str, float] = {
    "Sigma2_std": 1.0,
    "W2_std": -1.0,
    "Omega_tilt": 1.0,
    "Omega_k_aniso": 1.0,
}
CANONICAL_COMPONENT_ORDER: tuple[str, ...] = tuple(CANONICAL_COMPONENT_SIGNS)


def _require_non_empty(value: str, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _finite_float(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _validate_component_names(values: Mapping[str, object]) -> None:
    names = set(values)
    required = set(CANONICAL_COMPONENT_ORDER)
    if names != required:
        missing = tuple(sorted(required - names))
        extra = tuple(sorted(names - required))
        raise ValueError(
            "Departure breakdown requires exactly the canonical components "
            f"{CANONICAL_COMPONENT_ORDER}; missing={missing}, extra={extra}"
        )


def signed_component_projection(values: Mapping[str, float]) -> float:
    """Return the signed comparator projection for canonical components."""

    _validate_component_names(values)
    return float(
        sum(
            CANONICAL_COMPONENT_SIGNS[name] * _finite_float(values[name], name)
            for name in CANONICAL_COMPONENT_ORDER
        )
    )


@dataclass(frozen=True)
class DepartureComponent:
    """One canonical ingredient of the signed ``x_C`` projection."""

    name: str
    value: float
    comparator: str
    frame: str
    units: str

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "component name")
        if self.name not in CANONICAL_COMPONENT_SIGNS:
            raise ValueError(f"unknown departure component {self.name!r}")
        object.__setattr__(self, "value", _finite_float(self.value, self.name))
        object.__setattr__(
            self,
            "comparator",
            _require_non_empty(self.comparator, "comparator"),
        )
        object.__setattr__(self, "frame", _require_non_empty(self.frame, "frame"))
        object.__setattr__(self, "units", _require_non_empty(self.units, "units"))

    @property
    def sign(self) -> float:
        return CANONICAL_COMPONENT_SIGNS[self.name]

    @property
    def signed_contribution(self) -> float:
        return float(self.sign * self.value)

    def as_payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "sign": self.sign,
            "signed_contribution": self.signed_contribution,
            "comparator": self.comparator,
            "frame": self.frame,
            "units": self.units,
        }


@dataclass(frozen=True)
class ComponentBreakdown:
    """Canonical components and cancellation metadata for one comparator."""

    components: tuple[DepartureComponent, ...]
    comparator: str
    frame: str
    units: str

    def __post_init__(self) -> None:
        comparator = _require_non_empty(self.comparator, "comparator")
        frame = _require_non_empty(self.frame, "frame")
        units = _require_non_empty(self.units, "units")
        object.__setattr__(self, "comparator", comparator)
        object.__setattr__(self, "frame", frame)
        object.__setattr__(self, "units", units)

        components = tuple(self.components)
        by_name = {component.name: component for component in components}
        _validate_component_names(by_name)
        ordered = tuple(by_name[name] for name in CANONICAL_COMPONENT_ORDER)
        for component in ordered:
            if component.comparator != comparator:
                raise ValueError(
                    "all departure components must use the same comparator"
                )
            if component.frame != frame:
                raise ValueError("all departure components must use the same frame")
            if component.units != units:
                raise ValueError("all departure components must use the same units")
        object.__setattr__(self, "components", ordered)

    @property
    def component_values(self) -> dict[str, float]:
        return {component.name: component.value for component in self.components}

    @property
    def signed_contributions(self) -> dict[str, float]:
        return {
            component.name: component.signed_contribution
            for component in self.components
        }

    @property
    def x_C(self) -> float:
        return float(sum(self.signed_contributions.values()))

    @property
    def absolute_component_total(self) -> float:
        return float(sum(abs(component.value) for component in self.components))

    @property
    def cancellation_index(self) -> float:
        total = self.absolute_component_total
        if total == 0.0:
            return 0.0
        return float(1.0 - min(abs(self.x_C) / total, 1.0))

    def as_payload(self) -> dict[str, object]:
        return {
            "comparator": self.comparator,
            "frame": self.frame,
            "units": self.units,
            "component_order": list(CANONICAL_COMPONENT_ORDER),
            "component_signs": dict(CANONICAL_COMPONENT_SIGNS),
            "components": [component.as_payload() for component in self.components],
            "component_values": self.component_values,
            "signed_contributions": self.signed_contributions,
            "x_C": self.x_C,
            "absolute_component_total": self.absolute_component_total,
            "cancellation_index": self.cancellation_index,
        }


def build_component_breakdown(
    components: Mapping[str, float],
    *,
    comparator: str,
    frame: str,
    units: str,
) -> ComponentBreakdown:
    """Construct a validated canonical component breakdown."""

    _validate_component_names(components)
    return ComponentBreakdown(
        components=tuple(
            DepartureComponent(
                name=name,
                value=float(components[name]),
                comparator=comparator,
                frame=frame,
                units=units,
            )
            for name in CANONICAL_COMPONENT_ORDER
        ),
        comparator=comparator,
        frame=frame,
        units=units,
    )


__all__ = [
    "CANONICAL_COMPONENT_ORDER",
    "CANONICAL_COMPONENT_SIGNS",
    "ComponentBreakdown",
    "DepartureComponent",
    "build_component_breakdown",
    "signed_component_projection",
]
