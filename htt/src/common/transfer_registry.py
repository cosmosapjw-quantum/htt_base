"""Transfer-function provenance contracts for pre-solver HTT/MIO/BASS work.

PR-014 records where transfer-dependent numbers came from. It does not compute
transfer functions or synthesize future native solver outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable, Mapping, Sequence


class TransferSource(StrEnum):
    """Allowed transfer-source vocabulary."""

    NONE = "none"
    ANICLASS_EXTERNAL = "AniCLASS_external"
    EXTERNAL_TRANSFER = "external_transfer"
    EMPIRICAL_PROXY = "empirical_proxy"
    BASS_NATIVE_PROVISIONAL = "BASS_native_provisional"
    BASS_NATIVE_VALIDATED = "BASS_native_validated"


class ObservableKind(StrEnum):
    """Observable family produced by a transfer function."""

    TEMPERATURE = "temperature"
    POLARIZATION_E = "polarization_E"
    POLARIZATION_B = "polarization_B"
    BIPOSH = "biposh"
    TEMPLATE = "template"
    SCALAR_SUMMARY = "scalar_summary"


class CalibrationStatus(StrEnum):
    """Calibration/provenance state for a transfer function."""

    NONE = "none"
    UNCALIBRATED = "uncalibrated"
    EXTERNAL_CALIBRATED = "external_calibrated"
    EMPIRICAL_PROXY = "empirical_proxy"
    NATIVE_PROVISIONAL = "native_provisional"
    NATIVE_VALIDATED = "native_validated"


_EXTERNAL_SOURCES = {
    TransferSource.ANICLASS_EXTERNAL,
    TransferSource.EXTERNAL_TRANSFER,
    TransferSource.EMPIRICAL_PROXY,
}
_NATIVE_SOURCES = {
    TransferSource.BASS_NATIVE_PROVISIONAL,
    TransferSource.BASS_NATIVE_VALIDATED,
}
_NATIVE_VALIDATION_GATES = {"native_transfer_validated", "native_solver_validation"}
_REQUIRED_METADATA_FIELDS = {
    "transfer_source",
    "family",
    "valid_range",
    "observable_kind",
    "normalization",
    "calibration_status",
    "caveats",
}


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, StrEnum) else str(value)


def _validate_range_metadata(value: object) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("transfer metadata valid_range must be a mapping")
    required = {"k_min", "k_max", "ell_min", "ell_max"}
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"transfer metadata valid_range missing fields: {missing}")
    TransferValidRange(
        k_min=float(value["k_min"]),
        k_max=float(value["k_max"]),
        ell_min=int(value["ell_min"]),
        ell_max=int(value["ell_max"]),
    )


@dataclass(frozen=True)
class TransferValidRange:
    """Domain where a transfer specification may be used."""

    k_min: float
    k_max: float
    ell_min: int
    ell_max: int

    def __post_init__(self) -> None:
        if self.k_min <= 0.0:
            raise ValueError("TransferValidRange.k_min must be positive")
        if self.k_max <= self.k_min:
            raise ValueError("TransferValidRange.k_min must be < k_max")
        if self.ell_min < 0:
            raise ValueError("TransferValidRange.ell_min must be >= 0")
        if self.ell_max < self.ell_min:
            raise ValueError("TransferValidRange.ell_min must be <= ell_max")

    def to_metadata(self) -> dict[str, float | int]:
        return {
            "k_min": float(self.k_min),
            "k_max": float(self.k_max),
            "ell_min": int(self.ell_min),
            "ell_max": int(self.ell_max),
        }


@dataclass(frozen=True)
class TransferFunctionSpec:
    """Transfer provenance record required for transfer-dependent results."""

    transfer_id: str
    source: TransferSource | str
    family: str
    valid_range: TransferValidRange
    observable_kind: ObservableKind | str
    normalization: str
    calibration_status: CalibrationStatus | str
    caveats: Sequence[str]
    source_ref: str = ""
    version: str = "pr014"
    passed_validation_gates: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.transfer_id:
            raise ValueError("TransferFunctionSpec.transfer_id must be non-empty")
        if not self.family:
            raise ValueError("TransferFunctionSpec.family must be non-empty")
        if not isinstance(self.valid_range, TransferValidRange):
            raise TypeError(
                "TransferFunctionSpec.valid_range must be TransferValidRange"
            )
        if not self.normalization:
            raise ValueError("TransferFunctionSpec.normalization must be non-empty")
        if (
            isinstance(self.caveats, (str, bytes))
            or not isinstance(self.caveats, Sequence)
            or not self.caveats
        ):
            raise ValueError("TransferFunctionSpec.caveats must be non-empty")
        source = TransferSource(_enum_value(self.source))
        observable_kind = ObservableKind(_enum_value(self.observable_kind))
        calibration_status = CalibrationStatus(_enum_value(self.calibration_status))
        gates = tuple(str(gate) for gate in self.passed_validation_gates)
        if source in _EXTERNAL_SOURCES:
            if calibration_status in {
                CalibrationStatus.NATIVE_PROVISIONAL,
                CalibrationStatus.NATIVE_VALIDATED,
            } or _NATIVE_VALIDATION_GATES.intersection(gates):
                raise ValueError(
                    "external transfer sources cannot claim native validation"
                )
        if source is TransferSource.BASS_NATIVE_VALIDATED:
            if calibration_status is not CalibrationStatus.NATIVE_VALIDATED:
                raise ValueError(
                    "BASS_native_validated requires calibration_status native_validated"
                )
            if not _NATIVE_VALIDATION_GATES.intersection(gates):
                raise ValueError(
                    "BASS_native_validated requires native_transfer_validated "
                    "or native_solver_validation gate"
                )
        if source is TransferSource.BASS_NATIVE_PROVISIONAL:
            if calibration_status is CalibrationStatus.NATIVE_VALIDATED:
                raise ValueError(
                    "BASS_native_provisional cannot use native_validated calibration"
                )
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "observable_kind", observable_kind)
        object.__setattr__(self, "calibration_status", calibration_status)
        object.__setattr__(
            self,
            "caveats",
            tuple(str(caveat) for caveat in self.caveats),
        )
        object.__setattr__(self, "passed_validation_gates", gates)

    @property
    def is_native(self) -> bool:
        return self.source in _NATIVE_SOURCES

    @property
    def is_external(self) -> bool:
        return self.source in _EXTERNAL_SOURCES

    def to_metadata(self) -> dict[str, object]:
        """Return manifest-ready provenance metadata for dependent results."""

        return {
            "transfer_id": self.transfer_id,
            "transfer_source": self.source.value,
            "family": self.family,
            "valid_range": self.valid_range.to_metadata(),
            "observable_kind": self.observable_kind.value,
            "normalization": self.normalization,
            "calibration_status": self.calibration_status.value,
            "caveats": list(self.caveats),
            "source_ref": self.source_ref,
            "version": self.version,
            "passed_validation_gates": list(self.passed_validation_gates),
        }


class TransferRegistry:
    """Small deterministic registry for transfer provenance specs."""

    def __init__(self, specs: Iterable[TransferFunctionSpec] = ()) -> None:
        self._specs: dict[str, TransferFunctionSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: TransferFunctionSpec) -> TransferFunctionSpec:
        if not isinstance(spec, TransferFunctionSpec):
            raise TypeError("TransferRegistry.register requires TransferFunctionSpec")
        if spec.transfer_id in self._specs:
            raise ValueError(f"duplicate transfer_id {spec.transfer_id!r}")
        self._specs[spec.transfer_id] = spec
        return spec

    def get(self, transfer_id: str) -> TransferFunctionSpec:
        try:
            return self._specs[transfer_id]
        except KeyError as exc:
            raise KeyError(f"unknown transfer_id {transfer_id!r}") from exc

    def by_family(self, family: str) -> tuple[TransferFunctionSpec, ...]:
        return tuple(
            spec
            for spec in self._specs.values()
            if spec.family == family
        )

    def all(self) -> tuple[TransferFunctionSpec, ...]:
        return tuple(self._specs.values())


def validate_transfer_dependent_result(metadata: Mapping[str, object]) -> None:
    """Validate required PR-014 transfer metadata on a dependent result."""

    if metadata.get("schema_status") == "schema_only_no_solver_output":
        raise ValueError("schema-only transfer metadata is not a consumable result")
    if metadata.get("consumable_as_result") is False:
        raise ValueError("transfer metadata is marked non-consumable as a result")
    if metadata.get("returns_values") is False:
        raise ValueError("transfer metadata does not carry output values")
    missing = sorted(
        field for field in _REQUIRED_METADATA_FIELDS if field not in metadata
    )
    if missing:
        raise ValueError(f"transfer metadata missing required fields: {missing}")
    source = TransferSource(str(metadata["transfer_source"]))
    calibration_status = CalibrationStatus(str(metadata["calibration_status"]))
    _validate_range_metadata(metadata["valid_range"])
    caveats = metadata["caveats"]
    if (
        not isinstance(caveats, Sequence)
        or isinstance(caveats, (str, bytes))
        or not caveats
    ):
        raise ValueError("transfer metadata caveats must be a non-empty sequence")
    gates = tuple(str(gate) for gate in metadata.get("passed_validation_gates", ()))
    if source in _EXTERNAL_SOURCES:
        if calibration_status in {
            CalibrationStatus.NATIVE_PROVISIONAL,
            CalibrationStatus.NATIVE_VALIDATED,
        } or _NATIVE_VALIDATION_GATES.intersection(gates):
            raise ValueError("external transfer metadata cannot claim native validation")
    if (
        source is TransferSource.BASS_NATIVE_VALIDATED
        and not _NATIVE_VALIDATION_GATES.intersection(gates)
    ):
        raise ValueError("native transfer metadata requires native_transfer_validated gate")


__all__ = [
    "CalibrationStatus",
    "ObservableKind",
    "TransferFunctionSpec",
    "TransferRegistry",
    "TransferSource",
    "TransferValidRange",
    "validate_transfer_dependent_result",
]
