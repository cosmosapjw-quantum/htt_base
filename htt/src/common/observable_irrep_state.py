"""Typed observer/data-space irreducible representation state.

This module records measured or simulated harmonic/STF content. It does not
construct or represent physical shear, vorticity, acceleration, geometry,
local/global motion, a transfer response, or a Bianchi family.

A scalar or short feature vector cannot construct an irrep block directly.
Real-harmonic blocks are sliced from one complete, metadata-bound ell=2..5
carrier. Cartesian STF blocks are factory-built from an exact retained
harmonic parent and an explicit projection identity. The support receipt is
part of every content identity and is checked again at state assembly.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
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


class ObservableIrrepSupportKind(StrEnum):
    """Registered non-scalar support used to construct one irrep block."""

    REAL_HARMONIC_CARRIER = "REAL_HARMONIC_CARRIER"
    REGISTERED_STF_PROJECTION = "REGISTERED_STF_PROJECTION"


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

_REPRESENTATION_SUPPORT: Mapping[
    ObservableIrrepRepresentation,
    ObservableIrrepSupportKind,
] = {
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_5: (
        ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER
    ),
    ObservableIrrepRepresentation.CARTESIAN_STF2_5: (
        ObservableIrrepSupportKind.REGISTERED_STF_PROJECTION
    ),
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_7: (
        ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER
    ),
    ObservableIrrepRepresentation.CARTESIAN_STF3_7: (
        ObservableIrrepSupportKind.REGISTERED_STF_PROJECTION
    ),
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_9: (
        ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER
    ),
    ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_11: (
        ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER
    ),
}

_REAL_REPRESENTATION_BY_ELL: Mapping[int, ObservableIrrepRepresentation] = {
    2: ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_5,
    3: ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_7,
    4: ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_9,
    5: ObservableIrrepRepresentation.REAL_SPHERICAL_HARMONIC_11,
}

_STF_REPRESENTATION_BY_ELL: Mapping[int, ObservableIrrepRepresentation] = {
    2: ObservableIrrepRepresentation.CARTESIAN_STF2_5,
    3: ObservableIrrepRepresentation.CARTESIAN_STF3_7,
}

_SUPPORT_RECEIPT_TOKEN = object()
_BLOCK_TOKEN = object()


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


def _sha256_identity(value: object, name: str) -> str:
    normalized = _text(value, name)
    prefix = "sha256:"
    if not normalized.startswith(prefix):
        raise ObservableIrrepStateError(f"{name} must be a sha256 content identity")
    digest = normalized[len(prefix) :]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ObservableIrrepStateError(f"{name} must be a sha256 content identity")
    return normalized


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


def observable_real_harmonic_layout() -> tuple[tuple[int, int, str], ...]:
    """Canonical real-harmonic l=2..5 layout shared with the Planck operator."""

    rows: list[tuple[int, int, str]] = []
    for ell in range(2, 6):
        rows.append((ell, 0, "real"))
        for m in range(1, ell + 1):
            rows.extend(((ell, m, "real"), (ell, m, "imag")))
    return tuple(rows)


def _normalize_layout(value: object) -> tuple[tuple[int, int, str], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ObservableIrrepStateError("carrier layout must be a sequence")
    rows: list[tuple[int, int, str]] = []
    for index, row in enumerate(value):
        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence) or len(row) != 3:
            raise ObservableIrrepStateError(
                f"carrier layout row {index} must contain ell, m, and component kind"
            )
        ell = _integer(row[0], f"carrier layout row {index} ell")
        m = _integer(row[1], f"carrier layout row {index} m")
        kind = _text(row[2], f"carrier layout row {index} kind")
        rows.append((ell, m, kind))
    normalized = tuple(rows)
    if normalized != observable_real_harmonic_layout():
        raise ObservableIrrepStateError(
            "carrier layout must equal the canonical real-harmonic ell=2..5 layout"
        )
    return normalized


@dataclass(frozen=True)
class ObservableIrrepAbsence:
    """Typed absence for an undefined representation on a declared stratum."""

    reason: str
    stratum: str

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_ABSENCE_V1"
    status: ClassVar[ObservableIrrepAvailability] = ObservableIrrepAvailability.ABSENT

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


def _component_content_id(
    representation: ObservableIrrepRepresentation,
    components: IrrepComponents,
) -> str:
    return _content_id(
        {
            "components": (
                components.to_payload()
                if type(components) is ObservableIrrepAbsence
                else list(components)
            ),
            "representation": representation.value,
        }
    )


@dataclass(frozen=True)
class ObservableIrrepCarrier:
    """One complete, metadata-bound real harmonic carrier for l=2..5."""

    components: Sequence[Real]
    frame: str
    basis: str
    units: str
    source_identity: str
    operator_identity: str
    row_identity: str
    layout: Sequence[Sequence[object]] = field(
        default_factory=observable_real_harmonic_layout
    )
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_CARRIER_V1"

    def __post_init__(self) -> None:
        components = _components(self.components, dimension=32)
        layout = _normalize_layout(self.layout)
        object.__setattr__(self, "components", components)
        object.__setattr__(self, "layout", layout)
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
            "basis": self.basis,
            "components": list(self.components),
            "frame": self.frame,
            "layout": [list(row) for row in self.layout],
            "operator_identity": self.operator_identity,
            "row_identity": self.row_identity,
            "schema": self.schema,
            "source_identity": self.source_identity,
            "units": self.units,
        }

    def _assert_identity_sealed(self) -> None:
        if _content_id(self._payload_unchecked()) != self._identity_seal:
            raise ObservableIrrepStateError(
                "observable irrep carrier identity drifted after construction"
            )

    def to_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}

    @classmethod
    def from_payload(cls, payload: object) -> "ObservableIrrepCarrier":
        if not isinstance(payload, Mapping):
            raise ObservableIrrepStateError("carrier payload must be a mapping")
        _exact_keys(
            payload,
            {
                "basis",
                "components",
                "content_id",
                "frame",
                "layout",
                "operator_identity",
                "row_identity",
                "schema",
                "source_identity",
                "units",
            },
            name="carrier payload",
        )
        if payload["schema"] != cls.schema:
            raise ObservableIrrepStateError("unknown observable irrep carrier schema")
        carrier = cls(
            components=payload["components"],  # type: ignore[arg-type]
            frame=payload["frame"],  # type: ignore[arg-type]
            basis=payload["basis"],  # type: ignore[arg-type]
            units=payload["units"],  # type: ignore[arg-type]
            source_identity=payload["source_identity"],  # type: ignore[arg-type]
            operator_identity=payload["operator_identity"],  # type: ignore[arg-type]
            row_identity=payload["row_identity"],  # type: ignore[arg-type]
            layout=payload["layout"],  # type: ignore[arg-type]
        )
        if payload["content_id"] != carrier.content_id:
            raise ObservableIrrepStateError(
                "observable irrep carrier content identity mismatch"
            )
        return carrier


@dataclass(frozen=True)
class ObservableIrrepSupportReceipt:
    """Factory-built, content-bound support provenance for one irrep block."""

    kind: ObservableIrrepSupportKind | str
    representation: ObservableIrrepRepresentation | str
    ell: int
    spin: int
    parity: ObservableIrrepParity | str
    component_content_id: str
    support_identity: str
    frame: str
    basis: str
    units: str
    source_identity: str
    operator_identity: str
    row_identity: str
    parent_irrep_content_id: str | None = None
    projection_identity: str | None = None
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_SUPPORT_V1"

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SUPPORT_RECEIPT_TOKEN:
            raise ObservableIrrepStateError(
                "ObservableIrrepSupportReceipt must be factory-built"
            )
        kind = _enum(self.kind, ObservableIrrepSupportKind, "support kind")
        representation = _enum(
            self.representation,
            ObservableIrrepRepresentation,
            "support representation",
        )
        parity = _enum(self.parity, ObservableIrrepParity, "support parity")
        ell = _integer(self.ell, "support ell")
        spin = _integer(self.spin, "support spin")
        expected_ell, expected_spin, expected_parity, _ = _REPRESENTATION_CONTRACT[
            representation  # type: ignore[index]
        ]
        if (ell, spin, parity) != (expected_ell, expected_spin, expected_parity):
            raise ObservableIrrepStateError(
                "support ell, spin, or parity does not match its representation"
            )
        if kind is not _REPRESENTATION_SUPPORT[representation]:  # type: ignore[index]
            raise ObservableIrrepStateError(
                "support kind does not match its representation"
            )
        component_identity = _sha256_identity(
            self.component_content_id,
            "component_content_id",
        )
        support_identity = _sha256_identity(
            self.support_identity,
            "support_identity",
        )
        parent_identity: str | None
        normalized_projection_identity: str | None
        if kind is ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER:
            if self.parent_irrep_content_id is not None or self.projection_identity is not None:
                raise ObservableIrrepStateError(
                    "harmonic carrier support cannot contain parent/projection identities"
                )
            parent_identity = None
            normalized_projection_identity = None
        else:
            parent_identity = _sha256_identity(
                self.parent_irrep_content_id,
                "parent_irrep_content_id",
            )
            normalized_projection_identity = _sha256_identity(
                self.projection_identity,
                "projection_identity",
            )
            expected_support_identity = _content_id(
                {
                    "component_content_id": component_identity,
                    "parent_irrep_content_id": parent_identity,
                    "projection_identity": normalized_projection_identity,
                    "representation": representation.value,
                }
            )
            if support_identity != expected_support_identity:
                raise ObservableIrrepStateError(
                    "STF support identity is not content-bound to its parent and projection"
                )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "representation", representation)
        object.__setattr__(self, "ell", ell)
        object.__setattr__(self, "spin", spin)
        object.__setattr__(self, "parity", parity)
        object.__setattr__(self, "component_content_id", component_identity)
        object.__setattr__(self, "support_identity", support_identity)
        object.__setattr__(self, "parent_irrep_content_id", parent_identity)
        object.__setattr__(self, "projection_identity", normalized_projection_identity)
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

    def metadata_tuple(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.frame,
            self.basis,
            self.units,
            self.source_identity,
            self.operator_identity,
            self.row_identity,
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "basis": self.basis,
            "component_content_id": self.component_content_id,
            "ell": self.ell,
            "frame": self.frame,
            "kind": self.kind.value,
            "operator_identity": self.operator_identity,
            "parent_irrep_content_id": self.parent_irrep_content_id,
            "parity": self.parity.value,
            "projection_identity": self.projection_identity,
            "representation": self.representation.value,
            "row_identity": self.row_identity,
            "schema": self.schema,
            "source_identity": self.source_identity,
            "spin": self.spin,
            "support_identity": self.support_identity,
            "units": self.units,
        }

    def _assert_identity_sealed(self) -> None:
        if _content_id(self._payload_unchecked()) != self._identity_seal:
            raise ObservableIrrepStateError(
                "observable irrep support identity drifted after construction"
            )

    def to_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}

    @classmethod
    def from_payload(cls, payload: object) -> "ObservableIrrepSupportReceipt":
        if not isinstance(payload, Mapping):
            raise ObservableIrrepStateError("support payload must be a mapping")
        _exact_keys(
            payload,
            {
                "basis",
                "component_content_id",
                "content_id",
                "ell",
                "frame",
                "kind",
                "operator_identity",
                "parent_irrep_content_id",
                "parity",
                "projection_identity",
                "representation",
                "row_identity",
                "schema",
                "source_identity",
                "spin",
                "support_identity",
                "units",
            },
            name="support payload",
        )
        if payload["schema"] != cls.schema:
            raise ObservableIrrepStateError("unknown observable irrep support schema")
        receipt = cls(
            kind=payload["kind"],  # type: ignore[arg-type]
            representation=payload["representation"],  # type: ignore[arg-type]
            ell=payload["ell"],  # type: ignore[arg-type]
            spin=payload["spin"],  # type: ignore[arg-type]
            parity=payload["parity"],  # type: ignore[arg-type]
            component_content_id=payload["component_content_id"],  # type: ignore[arg-type]
            support_identity=payload["support_identity"],  # type: ignore[arg-type]
            frame=payload["frame"],  # type: ignore[arg-type]
            basis=payload["basis"],  # type: ignore[arg-type]
            units=payload["units"],  # type: ignore[arg-type]
            source_identity=payload["source_identity"],  # type: ignore[arg-type]
            operator_identity=payload["operator_identity"],  # type: ignore[arg-type]
            row_identity=payload["row_identity"],  # type: ignore[arg-type]
            parent_irrep_content_id=payload["parent_irrep_content_id"],  # type: ignore[arg-type]
            projection_identity=payload["projection_identity"],  # type: ignore[arg-type]
            _construction_token=_SUPPORT_RECEIPT_TOKEN,
        )
        if payload["content_id"] != receipt.content_id:
            raise ObservableIrrepStateError(
                "observable irrep support content identity mismatch"
            )
        return receipt


@dataclass(frozen=True)
class ObservableIrrepBlock:
    """One factory-built observer-space O(3) irrep block."""

    ell: int
    spin: int
    representation: ObservableIrrepRepresentation | str
    parity: ObservableIrrepParity | str
    components: IrrepComponents
    support: ObservableIrrepSupportReceipt
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_OBSERVABLE_IRREP_BLOCK_V1"

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _BLOCK_TOKEN:
            raise ObservableIrrepStateError(
                "ObservableIrrepBlock must be factory-built from retained support"
            )
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
        if type(self.support) is not ObservableIrrepSupportReceipt:
            raise ObservableIrrepStateError(
                "support must be an exact ObservableIrrepSupportReceipt"
            )
        support = self.support
        support._assert_identity_sealed()
        if (
            support.ell,
            support.spin,
            support.representation,
            support.parity,
        ) != (ell, spin, representation, parity):
            raise ObservableIrrepStateError(
                "support metadata does not match the irrep block"
            )
        if support.component_content_id != _component_content_id(
            representation,  # type: ignore[arg-type]
            components,
        ):
            raise ObservableIrrepStateError(
                "support component identity does not match the irrep components"
            )
        object.__setattr__(self, "ell", ell)
        object.__setattr__(self, "spin", spin)
        object.__setattr__(self, "representation", representation)
        object.__setattr__(self, "parity", parity)
        object.__setattr__(self, "components", components)
        object.__setattr__(self, "_identity_seal", _content_id(self._payload_unchecked()))

    @property
    def availability(self) -> ObservableIrrepAvailability:
        if type(self.components) is ObservableIrrepAbsence:
            return ObservableIrrepAvailability.ABSENT
        return ObservableIrrepAvailability.AVAILABLE

    @property
    def support_kind(self) -> ObservableIrrepSupportKind:
        return self.support.kind

    @property
    def support_identity(self) -> str:
        return self.support.support_identity

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
            "support": self.support.to_payload(),
        }

    def _assert_identity_sealed(self) -> None:
        self.support._assert_identity_sealed()
        if _component_content_id(
            self.representation,  # type: ignore[arg-type]
            self.components,
        ) != self.support.component_content_id:
            raise ObservableIrrepStateError(
                "observable irrep block component identity drifted after construction"
            )
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
                "support",
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
            components: object = ObservableIrrepAbsence.from_payload(payload["absence"])
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
            support=ObservableIrrepSupportReceipt.from_payload(payload["support"]),
            _construction_token=_BLOCK_TOKEN,
        )
        if payload["content_id"] != block.content_id:
            raise ObservableIrrepStateError(
                "observable irrep block content identity mismatch"
            )
        return block


def build_real_harmonic_irrep_block(
    *,
    carrier: ObservableIrrepCarrier,
    ell: int,
) -> ObservableIrrepBlock:
    """Slice one exact l block from a complete retained real-harmonic carrier."""

    if type(carrier) is not ObservableIrrepCarrier:
        raise ObservableIrrepStateError(
            "carrier must be an exact complete ObservableIrrepCarrier"
        )
    carrier._assert_identity_sealed()
    normalized_ell = _integer(ell, "ell")
    if normalized_ell not in _REAL_REPRESENTATION_BY_ELL:
        raise ObservableIrrepStateError("ell must be in the retained carrier band 2..5")
    representation = _REAL_REPRESENTATION_BY_ELL[normalized_ell]
    _, spin, parity, dimension = _REPRESENTATION_CONTRACT[representation]
    indices = [
        index
        for index, row in enumerate(carrier.layout)
        if row[0] == normalized_ell
    ]
    if len(indices) != dimension:
        raise ObservableIrrepStateError("carrier layout dimension drifted for selected ell")
    components = tuple(carrier.components[index] for index in indices)
    component_identity = _component_content_id(representation, components)
    support = ObservableIrrepSupportReceipt(
        kind=ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER,
        representation=representation,
        ell=normalized_ell,
        spin=spin,
        parity=parity,
        component_content_id=component_identity,
        support_identity=carrier.content_id,
        frame=carrier.frame,
        basis=carrier.basis,
        units=carrier.units,
        source_identity=carrier.source_identity,
        operator_identity=carrier.operator_identity,
        row_identity=carrier.row_identity,
        _construction_token=_SUPPORT_RECEIPT_TOKEN,
    )
    return ObservableIrrepBlock(
        ell=normalized_ell,
        spin=spin,
        representation=representation,
        parity=parity,
        components=components,
        support=support,
        _construction_token=_BLOCK_TOKEN,
    )


def build_cartesian_stf_irrep_block(
    *,
    parent: ObservableIrrepBlock,
    components: IrrepComponents,
    basis: str,
    projection_identity: str,
) -> ObservableIrrepBlock:
    """Build one l=2/3 STF block from an exact retained harmonic parent."""

    if type(parent) is not ObservableIrrepBlock:
        raise ObservableIrrepStateError(
            "parent must be an exact retained real-harmonic ObservableIrrepBlock"
        )
    parent._assert_identity_sealed()
    if parent.support.kind is not ObservableIrrepSupportKind.REAL_HARMONIC_CARRIER:
        raise ObservableIrrepStateError(
            "parent must use retained real-harmonic carrier support"
        )
    if parent.ell not in _STF_REPRESENTATION_BY_ELL:
        raise ObservableIrrepStateError("STF projection is registered only for ell=2 or ell=3")
    if parent.availability is not ObservableIrrepAvailability.AVAILABLE:
        raise ObservableIrrepStateError("harmonic parent must be numerically available")
    representation = _STF_REPRESENTATION_BY_ELL[parent.ell]
    ell, spin, parity, dimension = _REPRESENTATION_CONTRACT[representation]
    if type(components) is ObservableIrrepAbsence:
        normalized_components: IrrepComponents = components
    else:
        normalized_components = _components(components, dimension=dimension)
    normalized_basis = _text(basis, "basis")
    normalized_projection = _sha256_identity(
        projection_identity,
        "projection_identity",
    )
    component_identity = _component_content_id(
        representation,
        normalized_components,
    )
    support_identity = _content_id(
        {
            "component_content_id": component_identity,
            "parent_irrep_content_id": parent.content_id,
            "projection_identity": normalized_projection,
            "representation": representation.value,
        }
    )
    support = ObservableIrrepSupportReceipt(
        kind=ObservableIrrepSupportKind.REGISTERED_STF_PROJECTION,
        representation=representation,
        ell=ell,
        spin=spin,
        parity=parity,
        component_content_id=component_identity,
        support_identity=support_identity,
        frame=parent.support.frame,
        basis=normalized_basis,
        units=parent.support.units,
        source_identity=parent.support.source_identity,
        operator_identity=parent.support.operator_identity,
        row_identity=parent.support.row_identity,
        parent_irrep_content_id=parent.content_id,
        projection_identity=normalized_projection,
        _construction_token=_SUPPORT_RECEIPT_TOKEN,
    )
    return ObservableIrrepBlock(
        ell=ell,
        spin=spin,
        representation=representation,
        parity=parity,
        components=normalized_components,
        support=support,
        _construction_token=_BLOCK_TOKEN,
    )


@dataclass(frozen=True)
class ObservableIrrepState:
    """Metadata-bound observer/data-space irrep content for one row and basis."""

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
        expected_metadata = (
            self.frame,
            self.basis,
            self.units,
            self.source_identity,
            self.operator_identity,
            self.row_identity,
        )
        for block in blocks:
            block._assert_identity_sealed()
            if block.support.metadata_tuple() != expected_metadata:
                raise ObservableIrrepStateError(
                    "block support metadata does not match the enclosing state"
                )
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
        for block in self.blocks:
            block._assert_identity_sealed()
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
    "ObservableIrrepCarrier",
    "ObservableIrrepParity",
    "ObservableIrrepRepresentation",
    "ObservableIrrepSupportKind",
    "ObservableIrrepSupportReceipt",
    "ObservableIrrepState",
    "ObservableIrrepStateError",
    "build_cartesian_stf_irrep_block",
    "build_real_harmonic_irrep_block",
    "observable_irrep_state_from_payload",
    "observable_real_harmonic_layout",
]
