"""Typed observer/data-space irreducible representation state.

This module records measured or simulated harmonic/STF content.  It does not
construct or represent physical shear, vorticity, acceleration, geometry,
local/global motion, a transfer response, or a Bianchi family.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from numbers import Real
from typing import ClassVar, Mapping, Sequence

from common.enum_compat import StrEnum


class ObservableIrrepStateError(ValueError):
    """Raised when observer-space irrep metadata or identity is invalid."""


class ObservableIrrepParity(StrEnum):
    """O(3) inversion parity of a registered scalar-harmonic irrep."""

    EVEN = "EVEN"
    ODD = "ODD"


class ObservableIrrepRepresentation(StrEnum):
    """Registered retained harmonic and Cartesian STF representations."""

    REAL_SPHERICAL_HARMONIC_5 = "REAL_SPHERICAL_HARMONIC_5"
    CARTESIAN_STF2_5 = "CARTESIAN_STF2_5"
    REAL_SPHERICAL_HARMONIC_7 = "REAL_SPHERICAL_HARMONIC_7"
    CARTESIAN_STF3_7 = "CARTESIAN_STF3_7"
    REAL_SPHERICAL_HARMONIC_9 = "REAL_SPHERICAL_HARMONIC_9"
    REAL_SPHERICAL_HARMONIC_11 = "REAL_SPHERICAL_HARMONIC_11"


class ObservableIrrepAvailability(StrEnum):
    """Whether a block has numerical components or typed absence."""

    AVAILABLE = "AVAILABLE"
    ABSENT = "ABSENT"


OBSERVABLE_IRREP_SEMANTIC_LAYER = "OBSERVER_DATA_SPACE"
OBSERVABLE_IRREP_CLAIM_CEILING = "diagnostic_only_observer_space"
OBSERVABLE_IRREP_ALLOWED_USE = (
    "observer-space harmonic transport",
    "observer-space STF projection",
    "diagnostic orbit morphology after a registered projection",
)
OBSERVABLE_IRREP_FORBIDDEN_USE = (
    "physical shear or vorticity inference",
    "physical acceleration or geometry inference",
    "local boost or global tilt identification",
    "Bianchi family identification",
    "implicit response inversion",
)


_REPRESENTATION_CONTRACT: Mapping[
    ObservableIrrepRepresentation,
    tuple[int, int, ObservableIrrepParity, int],
] = {
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_5: (
        2,
        0,
        ObservableIrrepParity.EVEN,
        5,
    ),
    ObservableIrrepRepresentation.CARTESIAN_STF2_5: (
        2,
        0,
        ObservableIrrepParity.EVEN,
        5,
    ),
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_7: (
        3,
        0,
        ObservableIrrepParity.ODD,
        7,
    ),
    ObservableIrrepRepresentation.CARTESIAN_STF3_7: (
        3,
        0,
        ObservableIrrepParity.ODD,
        7,
    ),
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_9: (
        4,
        0,
        ObservableIrrepParity.EVEN,
        9,
    ),
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_11: (
        5,
        0,
        ObservableIrrepParity.ODD,
        11,
    ),
}


def _content_id(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ObservableIrrepStateError(f"{name} must be a non-empty string")
    return value.strip()


def _exact_keys(
    payload: Mapping[object, object],
    expected: set[str],
    *,
    name: str,
) -> None:
    observed = set(payload)
    if observed != expected:
        missing = sorted(expected - observed)  # type: ignore[operator]
        extra = sorted(observed - expected)  # type: ignore[operator]
        raise ObservableIrrepStateError(
            f"{name} keys mismatch: missing={missing}, extra={extra}"
        )


def _enum(value: object, enum_type: type[StrEnum], name: str) -> StrEnum:
    if type(value) is enum_type:
        return value  # type: ignore[return-value]
    if not isinstance(value, str):
        raise ObservableIrrepStateError(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        )
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ObservableIrrepStateError(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        ) from exc


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ObservableIrrepStateError(f"{name} must be an integer")
    if value < 0:
        raise ObservableIrrepStateError(f"{name} must be nonnegative")
    return value


def _components(value: object, *, dimension: int) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ObservableIrrepStateError(
            "components must be a numeric sequence or ObservableIrrepAbsence"
        )
    if len(value) != dimension:
        raise ObservableIrrepStateError(
            f"component dimension must be exactly {dimension}"
        )
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real):
            raise ObservableIrrepStateError("components must be finite real values")
        normalized = float(item)
        if not math.isfinite(normalized):
            raise ObservableIrrepStateError("components must be finite real values")
        out.append(normalized)
    return tuple(out)


@dataclass(frozen=True)
class ObservableIrrepAbsence:
    """Typed absence for an undefined representation on a declared stratum."""

    reason: str
    stratum: str

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_ABSENCE_V1"
    status: ClassVar[ObservableIrrepAvailability] = (
        ObservableIrrepAvailability.ABSENT
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "stratum", _text(self.stratum, "stratum"))

    def to_payload(self) -> dict[str, object]:
        return {
            "reason": self.reason,
            "schema": self.schema,
            "status": self.status.value,
            "stratum": self.stratum,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "ObservableIrrepAbsence":
        if not isinstance(payload, Mapping):
            raise ObservableIrrepStateError("absence payload must be a mapping")
        _exact_keys(
            payload,
            {"reason", "schema", "status", "stratum"},
            name="absence payload",
        )
        if payload["schema"] != cls.schema:
            raise ObservableIrrepStateError("unknown absence schema")
        if payload["status"] != ObservableIrrepAvailability.ABSENT.value:
            raise ObservableIrrepStateError("absence status must remain ABSENT")
        return cls(
            reason=payload["reason"],  # type: ignore[arg-type]
            stratum=payload["stratum"],  # type: ignore[arg-type]
        )


IrrepComponents = tuple[float, ...] | ObservableIrrepAbsence


@dataclass(frozen=True)
class ObservableIrrepBlock:
    """One registered observer-space O(3) irrep block."""

    ell: int
    spin: int
    representation: ObservableIrrepRepresentation | str
    parity: ObservableIrrepParity | str
    components: IrrepComponents
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_BLOCK_V1"

    def __post_init__(self) -> None:
        ell = _integer(self.ell, "ell")
        spin = _integer(self.spin, "spin")
        representation = _enum(
            self.representation,
            ObservableIrrepRepresentation,
            "representation",
        )
        parity = _enum(self.parity, ObservableIrrepParity, "parity")
        expected_ell, expected_spin, expected_parity, dimension = (
            _REPRESENTATION_CONTRACT[representation]  # type: ignore[index]
        )
        if ell != expected_ell:
            raise ObservableIrrepStateError(
                "ell does not match the registered representation"
            )
        if spin != expected_spin:
            raise ObservableIrrepStateError(
                "spin does not match the registered representation"
            )
        if parity is not expected_parity:
            raise ObservableIrrepStateError(
                "parity does not match the registered representation"
            )
        if type(self.components) is ObservableIrrepAbsence:
            components: IrrepComponents = self.components
        else:
            components = _components(self.components, dimension=dimension)
        object.__setattr__(self, "ell", ell)
        object.__setattr__(self, "spin", spin)
        object.__setattr__(self, "representation", representation)
        object.__setattr__(self, "parity", parity)
        object.__setattr__(self, "components", components)
        object.__setattr__(
            self,
            "_identity_seal",
            _content_id(self._payload_unchecked()),
        )

    @property
    def availability(self) -> ObservableIrrepAvailability:
        if type(self.components) is ObservableIrrepAbsence:
            return ObservableIrrepAvailability.ABSENT
        return ObservableIrrepAvailability.AVAILABLE

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        absent = type(self.components) is ObservableIrrepAbsence
        return {
            "absence": self.components.to_payload() if absent else None,
            "availability": self.availability.value,
            "components": None if absent else list(self.components),
            "ell": self.ell,
            "parity": self.parity.value,
            "representation": self.representation.value,
            "schema": self.schema,
            "spin": self.spin,
        }

    def _assert_identity_sealed(self) -> None:
        if _content_id(self._payload_unchecked()) != self._identity_seal:
            raise ObservableIrrepStateError(
                "observable irrep block identity drifted after construction"
            )

    def to_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}

    @classmethod
    def from_payload(cls, payload: object) -> "ObservableIrrepBlock":
        if not isinstance(payload, Mapping):
            raise ObservableIrrepStateError("block payload must be a mapping")
        _exact_keys(
            payload,
            {
                "absence",
                "availability",
                "components",
                "content_id",
                "ell",
                "parity",
                "representation",
                "schema",
                "spin",
            },
            name="block payload",
        )
        if payload["schema"] != cls.schema:
            raise ObservableIrrepStateError("unknown observable irrep block schema")
        availability = _enum(
            payload["availability"],
            ObservableIrrepAvailability,
            "availability",
        )
        if availability is ObservableIrrepAvailability.ABSENT:
            if payload["components"] is not None or payload["absence"] is None:
                raise ObservableIrrepStateError(
                    "absent block requires typed absence and no components"
                )
            components: object = ObservableIrrepAbsence.from_payload(
                payload["absence"]
            )
        else:
            if payload["absence"] is not None or payload["components"] is None:
                raise ObservableIrrepStateError(
                    "available block requires components and no absence"
                )
            components = payload["components"]
        block = cls(
            ell=payload["ell"],  # type: ignore[arg-type]
            spin=payload["spin"],  # type: ignore[arg-type]
            representation=payload["representation"],  # type: ignore[arg-type]
            parity=payload["parity"],  # type: ignore[arg-type]
            components=components,  # type: ignore[arg-type]
        )
        if payload["content_id"] != block.content_id:
            raise ObservableIrrepStateError(
                "observable irrep block content identity mismatch"
            )
        return block


@dataclass(frozen=True)
class ObservableIrrepState:
    """Metadata-bound observer/data-space irrep content for one row."""

    blocks: tuple[ObservableIrrepBlock, ...]
    frame: str
    basis: str
    units: str
    source_identity: str
    operator_identity: str
    row_identity: str
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_STATE_V1"
    semantic_layer: ClassVar[str] = OBSERVABLE_IRREP_SEMANTIC_LAYER
    claim_ceiling: ClassVar[str] = OBSERVABLE_IRREP_CLAIM_CEILING
    allowed_use: ClassVar[tuple[str, ...]] = OBSERVABLE_IRREP_ALLOWED_USE
    forbidden_use: ClassVar[tuple[str, ...]] = OBSERVABLE_IRREP_FORBIDDEN_USE

    def __post_init__(self) -> None:
        if isinstance(self.blocks, (str, bytes)) or not isinstance(
            self.blocks,
            Sequence,
        ):
            raise ObservableIrrepStateError(
                "blocks must be a non-empty sequence of ObservableIrrepBlock"
            )
        blocks = tuple(self.blocks)
        if not blocks:
            raise ObservableIrrepStateError("blocks must be non-empty")
        if any(type(block) is not ObservableIrrepBlock for block in blocks):
            raise ObservableIrrepStateError(
                "blocks must contain exact ObservableIrrepBlock values"
            )
        keys = tuple((block.ell, block.representation.value) for block in blocks)
        if len(set(keys)) != len(keys):
            raise ObservableIrrepStateError(
                "blocks must have unique ell and representation identities"
            )
        object.__setattr__(self, "blocks", blocks)
        for name in (
            "frame",
            "basis",
            "units",
            "source_identity",
            "operator_identity",
            "row_identity",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self,
            "_identity_seal",
            _content_id(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "basis": self.basis,
            "blocks": [block.to_payload() for block in self.blocks],
            "claim_ceiling": self.claim_ceiling,
            "forbidden_use": list(self.forbidden_use),
            "frame": self.frame,
            "operator_identity": self.operator_identity,
            "row_identity": self.row_identity,
            "schema": self.schema,
            "semantic_layer": self.semantic_layer,
            "source_identity": self.source_identity,
            "units": self.units,
        }

    def _assert_identity_sealed(self) -> None:
        if _content_id(self._payload_unchecked()) != self._identity_seal:
            raise ObservableIrrepStateError(
                "observable irrep state identity drifted after construction"
            )

    def to_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}

    @classmethod
    def from_payload(cls, payload: object) -> "ObservableIrrepState":
        return observable_irrep_state_from_payload(payload)


def observable_irrep_state_from_payload(payload: object) -> ObservableIrrepState:
    """Replay one exact observer-space state without semantic promotion."""

    if not isinstance(payload, Mapping):
        raise ObservableIrrepStateError(
            "ObservableIrrepState payload must be a mapping"
        )
    _exact_keys(
        payload,
        {
            "allowed_use",
            "basis",
            "blocks",
            "claim_ceiling",
            "content_id",
            "forbidden_use",
            "frame",
            "operator_identity",
            "row_identity",
            "schema",
            "semantic_layer",
            "source_identity",
            "units",
        },
        name="ObservableIrrepState payload",
    )
    if payload["schema"] != ObservableIrrepState.schema:
        raise ObservableIrrepStateError("unknown ObservableIrrepState schema")
    if payload["semantic_layer"] != OBSERVABLE_IRREP_SEMANTIC_LAYER:
        raise ObservableIrrepStateError("observable semantic layer drifted")
    if payload["claim_ceiling"] != OBSERVABLE_IRREP_CLAIM_CEILING:
        raise ObservableIrrepStateError("observable claim ceiling drifted")
    if tuple(payload["allowed_use"]) != OBSERVABLE_IRREP_ALLOWED_USE:  # type: ignore[arg-type]
        raise ObservableIrrepStateError("observable allowed-use contract drifted")
    if tuple(payload["forbidden_use"]) != OBSERVABLE_IRREP_FORBIDDEN_USE:  # type: ignore[arg-type]
        raise ObservableIrrepStateError("observable forbidden-use contract drifted")
    block_payloads = payload["blocks"]
    if isinstance(block_payloads, (str, bytes)) or not isinstance(
        block_payloads,
        Sequence,
    ):
        raise ObservableIrrepStateError("blocks payload must be a sequence")
    state = ObservableIrrepState(
        blocks=tuple(
            ObservableIrrepBlock.from_payload(item) for item in block_payloads
        ),
        frame=payload["frame"],  # type: ignore[arg-type]
        basis=payload["basis"],  # type: ignore[arg-type]
        units=payload["units"],  # type: ignore[arg-type]
        source_identity=payload["source_identity"],  # type: ignore[arg-type]
        operator_identity=payload["operator_identity"],  # type: ignore[arg-type]
        row_identity=payload["row_identity"],  # type: ignore[arg-type]
    )
    if payload["content_id"] != state.content_id:
        raise ObservableIrrepStateError(
            "ObservableIrrepState content identity mismatch"
        )
    return state


__all__ = [
    "OBSERVABLE_IRREP_ALLOWED_USE",
    "OBSERVABLE_IRREP_CLAIM_CEILING",
    "OBSERVABLE_IRREP_FORBIDDEN_USE",
    "OBSERVABLE_IRREP_SEMANTIC_LAYER",
    "ObservableIrrepAbsence",
    "ObservableIrrepAvailability",
    "ObservableIrrepBlock",
    "ObservableIrrepParity",
    "ObservableIrrepRepresentation",
    "ObservableIrrepState",
    "ObservableIrrepStateError",
    "observable_irrep_state_from_payload",
]
