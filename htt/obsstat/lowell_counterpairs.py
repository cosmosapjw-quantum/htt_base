"""Matched low-ell morphology feature packets for PR-257.

OBSSTAT owns only the observable feature extraction and pair-matching
metadata.  It does not classify a source, build an HTT likelihood, interpret
anchor stress as evidence, or identify a Bianchi family.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
import math
import re

import numpy as np

from .lowell_poles import (
    IMPLEMENTED_HARMONIC_CONVENTION,
    angular_momentum_power_tensor,
)
from .scalar_lowell import compute_cl_from_alm


class LowEllCounterpairError(ValueError):
    """Raised when a feature packet or matched-pair contract is invalid."""


class CounterpairFactor(str, Enum):
    PHASE = "PHASE"
    ORIENTATION = "ORIENTATION"
    PARITY = "PARITY"


class ParityRealization(str, Enum):
    REFERENCE = "REFERENCE"
    O3_REFLECTION = "O3_REFLECTION"


class InterventionOperator(str, Enum):
    NONLINEAR_M_PHASE_V1 = "NONLINEAR_M_PHASE_V1"
    COMMON_PROPER_Z_ROTATION_V1 = "COMMON_PROPER_Z_ROTATION_V1"
    SCALAR_PARITY_V1 = "SCALAR_PARITY_V1"


class MorphologyFeatureKind(str, Enum):
    MULTIPOLE_POWER_TENSOR = "MULTIPOLE_POWER_TENSOR"
    BIPOSH = "BIPOSH"
    DIRECTIONAL_WAVELET = "DIRECTIONAL_WAVELET"
    TEB_CROSS_MORPHOLOGY = "TEB_CROSS_MORPHOLOGY"


class FeatureAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING_FEATURE_PROVIDER = "MISSING_FEATURE_PROVIDER"


_PACKET_TOKEN = object()
_PAIR_TOKEN = object()
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ALLOWED_USE = (
    "synthetic low-ell feature extraction",
    "matched-counterpair diagnostic",
    "null-feature and mask-sensitivity bookkeeping",
)
_FORBIDDEN_USE = (
    "source attribution",
    "posterior or evidence term",
    "cosmological anomaly detection",
    "Bianchi family identification",
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise LowEllCounterpairError(f"{name} must be non-empty trimmed text")
    return value


def _receipt(value: object, name: str) -> str:
    text = _text(value, name)
    if not _SHA256_RE.fullmatch(text):
        raise LowEllCounterpairError(
            f"{name} must be a lowercase sha256 content identity"
        )
    return text


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise LowEllCounterpairError(f"{name} must not be boolean")
    if isinstance(value, (str, bytes)):
        raise LowEllCounterpairError(f"{name} must not be text")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise LowEllCounterpairError(f"{name} must be a finite real") from exc
    if not math.isfinite(out):
        raise LowEllCounterpairError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _finite_real(value, name)
    if out < 0.0:
        raise LowEllCounterpairError(f"{name} must be non-negative")
    return out


def _positive_tolerance(value: object, name: str) -> float:
    out = _finite_real(value, name)
    if out <= 0.0 or out > 1.0e-6:
        raise LowEllCounterpairError(
            f"{name} must be in the interval (0, 1e-6]"
        )
    return out


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class LowEllInterventionSpec:
    """Exact one-factor action used to construct the second packet."""

    factor: CounterpairFactor
    operator: InterventionOperator
    angle_radians: float | None = None
    intervention_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.factor, CounterpairFactor):
            raise LowEllCounterpairError(
                "factor must be a CounterpairFactor"
            )
        if not isinstance(self.operator, InterventionOperator):
            raise LowEllCounterpairError(
                "operator must be an InterventionOperator"
            )
        expected = {
            CounterpairFactor.PHASE: InterventionOperator.NONLINEAR_M_PHASE_V1,
            CounterpairFactor.ORIENTATION: (
                InterventionOperator.COMMON_PROPER_Z_ROTATION_V1
            ),
            CounterpairFactor.PARITY: InterventionOperator.SCALAR_PARITY_V1,
        }[self.factor]
        if self.operator is not expected:
            raise LowEllCounterpairError(
                "intervention operator does not match the declared factor"
            )
        if self.factor is CounterpairFactor.PARITY:
            if self.angle_radians is not None:
                raise LowEllCounterpairError(
                    "scalar parity does not accept an angle or free rotation"
                )
            angle = None
        else:
            angle = _finite_real(self.angle_radians, "angle_radians")
            if abs(math.sin(angle / 2.0)) <= 1.0e-8:
                raise LowEllCounterpairError(
                    "intervention angle must not be the identity modulo 2pi"
                )
            if (
                self.factor is CounterpairFactor.PHASE
                and abs(math.sin(angle)) <= 1.0e-8
            ):
                raise LowEllCounterpairError(
                    "nonlinear phase action overlaps a common proper rotation"
                )
            object.__setattr__(self, "angle_radians", angle)
        object.__setattr__(
            self,
            "intervention_id",
            _sha256_payload(
                {
                    "angle_radians_hex": (
                        None if angle is None else angle.hex()
                    ),
                    "factor": self.factor.value,
                    "operator": self.operator.value,
                    "schema": "PR257_LOWELL_INTERVENTION_ID_V1",
                }
            ),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "angle_radians": self.angle_radians,
            "factor": self.factor.value,
            "intervention_id": self.intervention_id,
            "operator": self.operator.value,
            "schema": "PR257_LOWELL_INTERVENTION_V1",
        }


def _array_content_id(array: np.ndarray, *, role: str) -> str:
    canonical = np.ascontiguousarray(np.asarray(array, dtype=np.float64))
    digest = hashlib.sha256()
    digest.update(role.encode("ascii"))
    digest.update(b"\0")
    digest.update(str(canonical.shape).encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _validate_feature_values(
    values: Sequence[object],
    *,
    name: str,
) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise LowEllCounterpairError(f"{name} must be a numeric sequence")
    out = tuple(_finite_real(value, f"{name}[{index}]") for index, value in enumerate(values))
    if not out:
        raise LowEllCounterpairError(f"{name} must be non-empty")
    return out


@dataclass(frozen=True)
class RegisteredMorphologyFeature:
    """One explicitly available or unavailable observable feature block."""

    kind: MorphologyFeatureKind
    availability: FeatureAvailability
    provider_id: str
    units: str
    source_alm_id: str | None = None
    values: tuple[float, ...] | None = None
    missing_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MorphologyFeatureKind):
            raise LowEllCounterpairError(
                "kind must be a MorphologyFeatureKind"
            )
        if not isinstance(self.availability, FeatureAvailability):
            raise LowEllCounterpairError(
                "availability must be a FeatureAvailability"
            )
        _receipt(self.provider_id, "provider_id")
        _text(self.units, "units")
        if self.availability is FeatureAvailability.AVAILABLE:
            _receipt(self.source_alm_id, "source_alm_id")
            if self.values is None:
                raise LowEllCounterpairError(
                    "available feature requires explicit values"
                )
            object.__setattr__(
                self,
                "values",
                _validate_feature_values(
                    self.values,
                    name=f"{self.kind.value}.values",
                ),
            )
            if self.missing_reason is not None:
                raise LowEllCounterpairError(
                    "available feature must not carry missing_reason"
                )
        else:
            if self.source_alm_id is not None:
                raise LowEllCounterpairError(
                    "missing feature must not carry source_alm_id"
                )
            if self.values is not None:
                raise LowEllCounterpairError(
                    "missing feature must not carry values, including zeros"
                )
            _text(self.missing_reason, "missing_reason")

    @property
    def content_id(self) -> str | None:
        if self.values is None:
            return None
        return _array_content_id(
            np.asarray(self.values),
            role=f"pr257_feature:{self.kind.value}",
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "availability": self.availability.value,
            "content_id": self.content_id,
            "kind": self.kind.value,
            "missing_reason": self.missing_reason,
            "provider_id": self.provider_id,
            "source_alm_id": self.source_alm_id,
            "units": self.units,
            "values": None if self.values is None else list(self.values),
        }


def register_morphology_feature(
    *,
    kind: MorphologyFeatureKind,
    availability: FeatureAvailability,
    provider_id: str,
    units: str,
    source_alm_id: str | None = None,
    values: Sequence[object] | None = None,
    missing_reason: str | None = None,
) -> RegisteredMorphologyFeature:
    """Register one feature without translating absence into a zero vector."""

    return RegisteredMorphologyFeature(
        kind=kind,
        availability=availability,
        provider_id=provider_id,
        units=units,
        source_alm_id=source_alm_id,
        values=None if values is None else tuple(values),
        missing_reason=missing_reason,
    )


def _validate_ell_values(values: Sequence[object]) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise LowEllCounterpairError("ell_values must be an integer sequence")
    out: list[int] = []
    for index, value in enumerate(values):
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ):
            raise LowEllCounterpairError(
                f"ell_values[{index}] must be an integer"
            )
        integer = int(value)
        if integer < 2:
            raise LowEllCounterpairError("ell_values must be at least 2")
        out.append(integer)
    result = tuple(out)
    if not result or tuple(sorted(set(result))) != result:
        raise LowEllCounterpairError(
            "ell_values must be non-empty, distinct, and increasing"
        )
    return result


def _canonical_dense_alm(
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    *,
    ell_values: tuple[int, ...],
) -> tuple[tuple[int, int, float, float], ...]:
    if not isinstance(alm_by_lm, Mapping):
        raise LowEllCounterpairError("alm_by_lm must be a mapping")
    entries: list[tuple[int, int, float, float]] = []
    expected = {
        (ell, m)
        for ell in ell_values
        for m in range(-ell, ell + 1)
    }
    actual = set(alm_by_lm)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise LowEllCounterpairError(
            f"alm_by_lm keys mismatch; missing={missing}, extra={extra}"
        )
    for ell in ell_values:
        for m in range(-ell, ell + 1):
            raw = alm_by_lm[(ell, m)]
            if isinstance(raw, (bool, np.bool_)) or isinstance(raw, (str, bytes)):
                raise LowEllCounterpairError(
                    "alm coefficients must be finite numeric values"
                )
            try:
                value = complex(raw)
            except (TypeError, ValueError, OverflowError) as exc:
                raise LowEllCounterpairError(
                    "alm coefficients must be finite numeric values"
                ) from exc
            if not math.isfinite(value.real) or not math.isfinite(value.imag):
                raise LowEllCounterpairError("alm coefficients must be finite")
            expected_negative = ((-1) ** m) * value.conjugate()
            if m > 0 and not np.isclose(
                alm_by_lm[(ell, -m)],
                expected_negative,
                rtol=1.0e-12,
                atol=1.0e-14,
            ):
                raise LowEllCounterpairError(
                    "alm coefficients violate the real-field reality condition"
                )
            if m == 0 and not math.isclose(
                value.imag, 0.0, abs_tol=1.0e-14, rel_tol=0.0
            ):
                raise LowEllCounterpairError(
                    "m=0 scalar alm coefficients must be real"
                )
            entries.append((ell, m, float(value.real), float(value.imag)))
    return tuple(entries)


def _alm_mapping(
    entries: Sequence[tuple[int, int, float, float]],
) -> dict[tuple[int, int], complex]:
    return {
        (ell, m): complex(real, imag)
        for ell, m, real, imag in entries
    }


def _alm_id(
    entries: tuple[tuple[int, int, float, float], ...],
) -> str:
    return _sha256_payload(
        {
            "entries": [
                [ell, m, real.hex(), imag.hex()]
                for ell, m, real, imag in entries
            ],
            "schema": "PR257_DENSE_REAL_ALM_V1",
        }
    )


def _registered_scalar_biposh_feature(
    entries: tuple[tuple[int, int, float, float], ...],
    *,
    ell_values: tuple[int, ...],
    harmonic_convention: str,
) -> RegisteredMorphologyFeature:
    """Derive a fixed signed scalar-BiPoSH vector from the bound alms.

    The deterministic vector retains real and imaginary parts of every
    registered coefficient in ``(ell1, ell2, L, M)`` order. It is a
    single-sky observable feature, not a covariance or source classifier.
    """

    if ell_values != (2, 3):
        raise LowEllCounterpairError(
            "PR-257 low-ell packets require ell_values=(2, 3)"
        )
    from .biposh_smica import compute_biposh_from_alm

    lmax = ell_values[-1]
    packed = np.zeros((lmax + 1) * (lmax + 2) // 2, dtype=np.complex128)
    for ell, m, real, imag in entries:
        if m < 0:
            continue
        packed[m * (2 * lmax + 1 - m) // 2 + ell] = complex(real, imag)
    measurement = compute_biposh_from_alm(
        packed,
        lmax,
        L_values=(1, 2),
        ell_min=ell_values[0],
        channel="T",
        threshold=-1.0,
    )
    values = tuple(
        component
        for coefficient in measurement.coefficients
        for component in (
            float(complex(coefficient.value).real),
            float(complex(coefficient.value).imag),
        )
    )
    return register_morphology_feature(
        kind=MorphologyFeatureKind.BIPOSH,
        availability=FeatureAvailability.AVAILABLE,
        provider_id=_sha256_payload(
            {
                "algorithm": "obsstat.biposh_smica.compute_biposh_from_alm",
                "channel": "T",
                "ell_values": list(ell_values),
                "harmonic_convention": harmonic_convention,
                "L_values": [1, 2],
                "schema": "PR257_SIGNED_SCALAR_BIPOSH_PROVIDER_V1",
                "value_order": "ell1_ell2_L_M_real_imag",
            }
        ),
        units="dimensionless_alm_product_complex_pairs",
        source_alm_id=_alm_id(entries),
        values=values,
    )


def _apply_intervention_to_alm(
    entries: tuple[tuple[int, int, float, float], ...],
    intervention: LowEllInterventionSpec,
) -> dict[tuple[int, int], complex]:
    out: dict[tuple[int, int], complex] = {}
    for ell, m, real, imag in entries:
        value = complex(real, imag)
        if intervention.factor is CounterpairFactor.PARITY:
            transformed = ((-1) ** ell) * value
        elif intervention.factor is CounterpairFactor.ORIENTATION:
            transformed = np.exp(
                -1j * m * float(intervention.angle_radians)
            ) * value
        else:
            signed_phase = (
                0.0
                if m == 0
                else math.copysign(1.0, m)
                * float(m * m)
                * float(intervention.angle_radians)
            )
            transformed = np.exp(1j * signed_phase) * value
        out[(ell, m)] = complex(transformed)
    return out


def _phase_id(
    entries: tuple[tuple[int, int, float, float], ...],
    ell_values: tuple[int, ...],
) -> str:
    alm = _alm_mapping(entries)
    normalized: list[tuple[int, int, str, str]] = []
    for ell in ell_values:
        vector = np.array(
            [alm[(ell, m)] for m in range(-ell, ell + 1)],
            dtype=np.complex128,
        )
        norm = float(np.linalg.norm(vector))
        if not math.isfinite(norm) or norm == 0.0:
            raise LowEllCounterpairError(
                "each selected multipole must have non-zero finite power"
            )
        for m, value in zip(range(-ell, ell + 1), vector / norm, strict=True):
            normalized.append(
                (ell, m, float(value.real).hex(), float(value.imag).hex())
            )
    return _sha256_payload(
        {"schema": "PR257_PHASE_SIGNATURE_V1", "values": normalized}
    )


def _stress_interval(
    value: Sequence[object],
) -> tuple[float, float]:
    if isinstance(value, (str, bytes)) or len(value) != 2:
        raise LowEllCounterpairError(
            "anchor_stress_interval must contain exactly two values"
        )
    lower = _nonnegative(value[0], "anchor_stress_interval[0]")
    upper = _nonnegative(value[1], "anchor_stress_interval[1]")
    if lower > upper:
        raise LowEllCounterpairError(
            "anchor_stress_interval lower bound exceeds upper bound"
        )
    return (lower, upper)


@dataclass(frozen=True)
class LowEllMorphologyFeaturePacket:
    """Factory-derived observable packet with exact power and provider binding."""

    sample_id: str
    ell_values: tuple[int, ...]
    alm_entries: tuple[tuple[int, int, float, float], ...]
    cl_by_ell: tuple[tuple[int, float], ...]
    power_tensors: tuple[tuple[int, tuple[tuple[float, ...], ...]], ...]
    features: tuple[RegisteredMorphologyFeature, ...]
    coordinate_frame: str
    harmonic_convention: str
    anchor_id: str
    anchor_stress_interval: tuple[float, float]
    mask_id: str
    beam_id: str
    foreground_model_id: str
    parity_realization: ParityRealization
    parent_packet_id: str | None
    intervention: LowEllInterventionSpec | None
    phase_id: str
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PACKET_TOKEN:
            raise LowEllCounterpairError(
                "LowEllMorphologyFeaturePacket must be factory-derived"
            )
        _text(self.sample_id, "sample_id")
        ells = _validate_ell_values(self.ell_values)
        if self.harmonic_convention != IMPLEMENTED_HARMONIC_CONVENTION:
            raise LowEllCounterpairError(
                "harmonic_convention is not implemented by this kernel"
            )
        for name in (
            "anchor_id",
            "mask_id",
            "beam_id",
            "foreground_model_id",
            "phase_id",
        ):
            _receipt(getattr(self, name), name)
        _text(self.coordinate_frame, "coordinate_frame")
        interval = _stress_interval(self.anchor_stress_interval)
        if not isinstance(self.parity_realization, ParityRealization):
            raise LowEllCounterpairError(
                "parity_realization must be a ParityRealization"
            )
        if self.intervention is None:
            if self.parent_packet_id is not None:
                raise LowEllCounterpairError(
                    "reference packet must not carry parent_packet_id"
                )
            if self.parity_realization is not ParityRealization.REFERENCE:
                raise LowEllCounterpairError(
                    "reference packet must use REFERENCE parity realization"
                )
        else:
            if not isinstance(self.intervention, LowEllInterventionSpec):
                raise LowEllCounterpairError(
                    "intervention must be a LowEllInterventionSpec"
                )
            _receipt(self.parent_packet_id, "parent_packet_id")
            expected_parity = (
                ParityRealization.O3_REFLECTION
                if self.intervention.factor is CounterpairFactor.PARITY
                else ParityRealization.REFERENCE
            )
            if self.parity_realization is not expected_parity:
                raise LowEllCounterpairError(
                    "parity_realization does not match the intervention"
                )
        if (
            self.parity_realization is ParityRealization.O3_REFLECTION
            and (
                self.intervention is None
                or self.intervention.factor is not CounterpairFactor.PARITY
            )
        ):
            raise LowEllCounterpairError(
                "O3_REFLECTION requires the exact scalar parity intervention"
            )
        features = tuple(self.features)
        if not features or not all(
            isinstance(item, RegisteredMorphologyFeature) for item in features
        ):
            raise LowEllCounterpairError(
                "features must contain registered feature blocks"
            )
        kinds = tuple(item.kind for item in features)
        if len(set(kinds)) != len(kinds):
            raise LowEllCounterpairError("feature kinds must be unique")
        if set(kinds) != set(MorphologyFeatureKind):
            raise LowEllCounterpairError(
                "feature packet must register every PR-257 feature kind"
            )
        power = next(
            item
            for item in features
            if item.kind is MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR
        )
        expected_power = tuple(
            value
            for _, tensor in self.power_tensors
            for row in tensor
            for value in row
        )
        if power.values != expected_power:
            raise LowEllCounterpairError(
                "power-tensor feature does not match bound power tensors"
            )
        source_alm_id = _alm_id(self.alm_entries)
        for feature in features:
            if (
                feature.availability is FeatureAvailability.AVAILABLE
                and feature.source_alm_id != source_alm_id
            ):
                raise LowEllCounterpairError(
                    f"{feature.kind.value} feature is not bound to packet alm bytes"
                )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise LowEllCounterpairError(
                "feature packet must retain the OBSSTAT claim boundary"
            )
        object.__setattr__(self, "ell_values", ells)
        object.__setattr__(self, "anchor_stress_interval", interval)
        object.__setattr__(self, "features", features)

    @property
    def packet_id(self) -> str:
        return _sha256_payload(self.as_payload())

    def feature(self, kind: MorphologyFeatureKind) -> RegisteredMorphologyFeature:
        for item in self.features:
            if item.kind is kind:
                return item
        raise KeyError(kind)

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "alm_id": _alm_id(self.alm_entries),
            "anchor_id": self.anchor_id,
            "anchor_stress_interval": list(self.anchor_stress_interval),
            "beam_id": self.beam_id,
            "cl_by_ell": [[ell, value] for ell, value in self.cl_by_ell],
            "coordinate_frame": self.coordinate_frame,
            "ell_values": list(self.ell_values),
            "features": [item.as_payload() for item in self.features],
            "forbidden_use": list(self.forbidden_use),
            "foreground_model_id": self.foreground_model_id,
            "harmonic_convention": self.harmonic_convention,
            "mask_id": self.mask_id,
            "intervention": (
                None if self.intervention is None else self.intervention.as_payload()
            ),
            "parity_realization": self.parity_realization.value,
            "parent_packet_id": self.parent_packet_id,
            "phase_id": self.phase_id,
            "power_tensors": [
                [ell, [list(row) for row in tensor]]
                for ell, tensor in self.power_tensors
            ],
            "sample_id": self.sample_id,
            "schema": "PR257_LOWELL_FEATURE_PACKET_V1",
        }


def _build_lowell_morphology_feature_packet(
    *,
    sample_id: str,
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    ell_values: Sequence[object],
    additional_features: Sequence[RegisteredMorphologyFeature],
    coordinate_frame: str,
    harmonic_convention: str,
    anchor_id: str,
    anchor_stress_interval: Sequence[object],
    mask_id: str,
    beam_id: str,
    foreground_model_id: str,
    parity_realization: ParityRealization,
    parent_packet_id: str | None,
    intervention: LowEllInterventionSpec | None,
    registered_cl_by_ell: tuple[tuple[int, float], ...] | None = None,
) -> LowEllMorphologyFeaturePacket:
    """Extract exact power tensors and bind the remaining provider blocks."""

    ells = _validate_ell_values(ell_values)
    if ells != (2, 3):
        raise LowEllCounterpairError(
            "PR-257 low-ell packets require ell_values=(2, 3)"
        )
    entries = _canonical_dense_alm(alm_by_lm, ell_values=ells)
    alm = _alm_mapping(entries)
    source_alm_id = _alm_id(entries)
    cl = compute_cl_from_alm(alm)
    computed_cl_items = tuple((ell, float(cl[ell])) for ell in ells)
    if registered_cl_by_ell is None:
        cl_items = computed_cl_items
    else:
        cl_items = tuple(
            (
                int(ell),
                _nonnegative(value, f"registered_cl_by_ell[{index}][1]"),
            )
            for index, (ell, value) in enumerate(registered_cl_by_ell)
        )
        if tuple(ell for ell, _ in cl_items) != ells:
            raise LowEllCounterpairError(
                "registered C_ell vector must cover the exact selected ell set"
            )
        if any(
            not math.isclose(
                computed,
                registered,
                rel_tol=1.0e-12,
                abs_tol=0.0,
            )
            for (_, computed), (_, registered) in zip(
                computed_cl_items,
                cl_items,
                strict=True,
            )
        ):
            raise LowEllCounterpairError(
                "intervention does not numerically preserve the registered C_ell"
            )
    tensors = tuple(
        (
            ell,
            tuple(
                tuple(float(value) for value in row)
                for row in angular_momentum_power_tensor(
                    alm_by_lm=alm,
                    ell=ell,
                )
            ),
        )
        for ell in ells
    )
    power_values = tuple(
        value
        for _, tensor in tensors
        for row in tensor
        for value in row
    )
    power_feature = register_morphology_feature(
        kind=MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR,
        availability=FeatureAvailability.AVAILABLE,
        provider_id=_sha256_payload(
            {
                "harmonic_convention": harmonic_convention,
                "kind": "MULTIPOLE_POWER_TENSOR",
                "schema": "PR257_BUILTIN_PROVIDER_V1",
            }
        ),
        units="trace_one_dimensionless_tensor",
        source_alm_id=source_alm_id,
        values=power_values,
    )
    biposh_feature = _registered_scalar_biposh_feature(
        entries,
        ell_values=ells,
        harmonic_convention=harmonic_convention,
    )
    extras = tuple(additional_features)
    if any(
        item.kind
        in {
            MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR,
            MorphologyFeatureKind.BIPOSH,
        }
        for item in extras
    ):
        raise LowEllCounterpairError(
            "power tensor and scalar BiPoSH are factory-derived and must not be supplied"
        )
    forbidden_available = tuple(
        item.kind
        for item in extras
        if item.kind
        in {
            MorphologyFeatureKind.DIRECTIONAL_WAVELET,
            MorphologyFeatureKind.TEB_CROSS_MORPHOLOGY,
        }
        and item.availability is FeatureAvailability.AVAILABLE
    )
    if forbidden_available:
        raise LowEllCounterpairError(
            "directional-wavelet and T/E/B providers are not registered; "
            "they must remain MISSING_FEATURE_PROVIDER"
        )
    return LowEllMorphologyFeaturePacket(
        sample_id=sample_id,
        ell_values=ells,
        alm_entries=entries,
        cl_by_ell=cl_items,
        power_tensors=tensors,
        features=(power_feature, biposh_feature, *extras),
        coordinate_frame=coordinate_frame,
        harmonic_convention=harmonic_convention,
        anchor_id=anchor_id,
        anchor_stress_interval=_stress_interval(anchor_stress_interval),
        mask_id=mask_id,
        beam_id=beam_id,
        foreground_model_id=foreground_model_id,
        parity_realization=parity_realization,
        parent_packet_id=parent_packet_id,
        intervention=intervention,
        phase_id=_phase_id(entries, ells),
        _construction_token=_PACKET_TOKEN,
    )


def build_lowell_morphology_feature_packet(
    *,
    sample_id: str,
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    ell_values: Sequence[object],
    additional_features: Sequence[RegisteredMorphologyFeature],
    coordinate_frame: str,
    harmonic_convention: str,
    anchor_id: str,
    anchor_stress_interval: Sequence[object],
    mask_id: str,
    beam_id: str,
    foreground_model_id: str,
) -> LowEllMorphologyFeaturePacket:
    """Build a reference packet before any one-factor intervention."""

    return _build_lowell_morphology_feature_packet(
        sample_id=sample_id,
        alm_by_lm=alm_by_lm,
        ell_values=ell_values,
        additional_features=additional_features,
        coordinate_frame=coordinate_frame,
        harmonic_convention=harmonic_convention,
        anchor_id=anchor_id,
        anchor_stress_interval=anchor_stress_interval,
        mask_id=mask_id,
        beam_id=beam_id,
        foreground_model_id=foreground_model_id,
        parity_realization=ParityRealization.REFERENCE,
        parent_packet_id=None,
        intervention=None,
        registered_cl_by_ell=None,
    )


def apply_lowell_counterpair_intervention(
    *,
    reference: LowEllMorphologyFeaturePacket,
    intervention: LowEllInterventionSpec,
    sample_id: str,
    additional_features: Sequence[RegisteredMorphologyFeature],
) -> LowEllMorphologyFeaturePacket:
    """Construct the second packet from one exact registered intervention."""

    if not isinstance(reference, LowEllMorphologyFeaturePacket):
        raise TypeError("reference must be a LowEllMorphologyFeaturePacket")
    _revalidate_feature_packet(reference)
    if reference.intervention is not None:
        raise LowEllCounterpairError(
            "interventions must be applied directly to a reference packet"
        )
    if not isinstance(intervention, LowEllInterventionSpec):
        raise TypeError("intervention must be a LowEllInterventionSpec")
    validated_intervention = LowEllInterventionSpec(
        factor=intervention.factor,
        operator=intervention.operator,
        angle_radians=intervention.angle_radians,
    )
    if validated_intervention != intervention:
        raise LowEllCounterpairError(
            "intervention contract is not canonical"
        )
    transformed = _apply_intervention_to_alm(
        reference.alm_entries,
        validated_intervention,
    )
    return _build_lowell_morphology_feature_packet(
        sample_id=sample_id,
        alm_by_lm=transformed,
        ell_values=reference.ell_values,
        additional_features=additional_features,
        coordinate_frame=reference.coordinate_frame,
        harmonic_convention=reference.harmonic_convention,
        anchor_id=reference.anchor_id,
        anchor_stress_interval=reference.anchor_stress_interval,
        mask_id=reference.mask_id,
        beam_id=reference.beam_id,
        foreground_model_id=reference.foreground_model_id,
        parity_realization=(
            ParityRealization.O3_REFLECTION
            if validated_intervention.factor is CounterpairFactor.PARITY
            else ParityRealization.REFERENCE
        ),
        parent_packet_id=reference.packet_id,
        intervention=validated_intervention,
        registered_cl_by_ell=reference.cl_by_ell,
    )


def _revalidate_feature_packet(
    packet: LowEllMorphologyFeaturePacket,
) -> None:
    """Recompute factory-owned bindings before a packet enters a pair report."""

    canonical_entries = _canonical_dense_alm(
        _alm_mapping(packet.alm_entries),
        ell_values=packet.ell_values,
    )
    if canonical_entries != packet.alm_entries:
        raise LowEllCounterpairError(
            "feature packet alm entries are not in canonical form"
        )
    validated_features = tuple(
        RegisteredMorphologyFeature(
            kind=feature.kind,
            availability=feature.availability,
            provider_id=feature.provider_id,
            units=feature.units,
            source_alm_id=feature.source_alm_id,
            values=feature.values,
            missing_reason=feature.missing_reason,
        )
        for feature in packet.features
    )
    validated_intervention = (
        None
        if packet.intervention is None
        else LowEllInterventionSpec(
            factor=packet.intervention.factor,
            operator=packet.intervention.operator,
            angle_radians=packet.intervention.angle_radians,
        )
    )
    validated_cl = tuple(
        (
            int(ell),
            _nonnegative(value, f"cl_by_ell[{index}][1]"),
        )
        for index, (ell, value) in enumerate(packet.cl_by_ell)
    )
    if (
        tuple(ell for ell, _ in validated_cl) != packet.ell_values
        or validated_cl != packet.cl_by_ell
    ):
        raise LowEllCounterpairError(
            "feature packet C_ell vector is not canonical"
        )
    validated_packet = LowEllMorphologyFeaturePacket(
        sample_id=packet.sample_id,
        ell_values=packet.ell_values,
        alm_entries=packet.alm_entries,
        cl_by_ell=validated_cl,
        power_tensors=packet.power_tensors,
        features=validated_features,
        coordinate_frame=packet.coordinate_frame,
        harmonic_convention=packet.harmonic_convention,
        anchor_id=packet.anchor_id,
        anchor_stress_interval=packet.anchor_stress_interval,
        mask_id=packet.mask_id,
        beam_id=packet.beam_id,
        foreground_model_id=packet.foreground_model_id,
        parity_realization=packet.parity_realization,
        parent_packet_id=packet.parent_packet_id,
        intervention=validated_intervention,
        phase_id=packet.phase_id,
        allowed_use=packet.allowed_use,
        forbidden_use=packet.forbidden_use,
        _construction_token=_PACKET_TOKEN,
    )
    if validated_packet != packet:
        raise LowEllCounterpairError(
            "feature packet or nested contract is not canonical"
        )
    if packet.phase_id != _phase_id(canonical_entries, packet.ell_values):
        raise LowEllCounterpairError(
            "feature packet phase signature does not replay from bound alm bytes"
        )
    alm = _alm_mapping(canonical_entries)
    expected_tensors = tuple(
        (
            ell,
            tuple(
                tuple(float(value) for value in row)
                for row in angular_momentum_power_tensor(
                    alm_by_lm=alm,
                    ell=ell,
                )
            ),
        )
        for ell in packet.ell_values
    )
    if packet.power_tensors != expected_tensors:
        raise LowEllCounterpairError(
            "feature packet power tensors do not replay from bound alm bytes"
        )
    expected_power = register_morphology_feature(
        kind=MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR,
        availability=FeatureAvailability.AVAILABLE,
        provider_id=_sha256_payload(
            {
                "harmonic_convention": packet.harmonic_convention,
                "kind": "MULTIPOLE_POWER_TENSOR",
                "schema": "PR257_BUILTIN_PROVIDER_V1",
            }
        ),
        units="trace_one_dimensionless_tensor",
        source_alm_id=_alm_id(canonical_entries),
        values=tuple(
            value
            for _, tensor in expected_tensors
            for row in tensor
            for value in row
        ),
    )
    if packet.feature(MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR) != expected_power:
        raise LowEllCounterpairError(
            "power-tensor feature does not replay from bound alm bytes"
        )
    expected_biposh = _registered_scalar_biposh_feature(
        canonical_entries,
        ell_values=packet.ell_values,
        harmonic_convention=packet.harmonic_convention,
    )
    if packet.feature(MorphologyFeatureKind.BIPOSH) != expected_biposh:
        raise LowEllCounterpairError(
            "BiPoSH feature does not replay from bound alm bytes"
        )


@dataclass(frozen=True)
class MatchedCounterpairReport:
    pair_id: str
    factor: CounterpairFactor
    left: LowEllMorphologyFeaturePacket
    right: LowEllMorphologyFeaturePacket
    feature_distances: tuple[tuple[MorphologyFeatureKind, float | None], ...]
    separated_feature_kinds: tuple[MorphologyFeatureKind, ...]
    missing_feature_kinds: tuple[MorphologyFeatureKind, ...]
    power_relative_tolerance: float
    feature_separation_tolerance: float
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PAIR_TOKEN:
            raise LowEllCounterpairError(
                "MatchedCounterpairReport must be factory-derived"
            )
        _text(self.pair_id, "pair_id")
        if not isinstance(self.factor, CounterpairFactor):
            raise LowEllCounterpairError(
                "factor must be a CounterpairFactor"
            )
        if not isinstance(self.left, LowEllMorphologyFeaturePacket) or not isinstance(
            self.right, LowEllMorphologyFeaturePacket
        ):
            raise LowEllCounterpairError(
                "counterpair members must be feature packets"
            )
        if self.left.packet_id == self.right.packet_id:
            raise LowEllCounterpairError(
                "counterpair members must be distinct packets"
            )
        tolerance = _positive_tolerance(
            self.power_relative_tolerance,
            "power_relative_tolerance",
        )
        separation_tolerance = _positive_tolerance(
            self.feature_separation_tolerance,
            "feature_separation_tolerance",
        )
        kinds = tuple(kind for kind, _ in self.feature_distances)
        if kinds != tuple(MorphologyFeatureKind):
            raise LowEllCounterpairError(
                "feature distances must cover the frozen feature order"
            )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise LowEllCounterpairError(
                "counterpair report must retain the OBSSTAT claim boundary"
            )
        object.__setattr__(self, "power_relative_tolerance", tolerance)
        object.__setattr__(
            self,
            "feature_separation_tolerance",
            separation_tolerance,
        )

    @property
    def report_id(self) -> str:
        return _sha256_payload(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "factor": self.factor.value,
            "feature_distances": [
                [kind.value, value] for kind, value in self.feature_distances
            ],
            "feature_separation_tolerance": (
                self.feature_separation_tolerance
            ),
            "forbidden_use": list(self.forbidden_use),
            "left_packet_id": self.left.packet_id,
            "missing_feature_kinds": [
                kind.value for kind in self.missing_feature_kinds
            ],
            "pair_id": self.pair_id,
            "power_relative_tolerance": self.power_relative_tolerance,
            "right_packet_id": self.right.packet_id,
            "schema": "PR257_MATCHED_COUNTERPAIR_REPORT_V1",
            "separated_feature_kinds": [
                kind.value for kind in self.separated_feature_kinds
            ],
        }


def build_matched_counterpair(
    *,
    pair_id: str,
    factor: CounterpairFactor,
    left: LowEllMorphologyFeaturePacket,
    right: LowEllMorphologyFeaturePacket,
    power_relative_tolerance: float = 1.0e-12,
    feature_separation_tolerance: float = 1.0e-12,
) -> MatchedCounterpairReport:
    """Match power/anchor contracts and report which features actually differ."""

    if not isinstance(left, LowEllMorphologyFeaturePacket) or not isinstance(
        right, LowEllMorphologyFeaturePacket
    ):
        raise TypeError("left and right must be feature packets")
    if not isinstance(factor, CounterpairFactor):
        raise TypeError("factor must be a CounterpairFactor")
    _revalidate_feature_packet(left)
    _revalidate_feature_packet(right)
    power_tolerance = _positive_tolerance(
        power_relative_tolerance,
        "power_relative_tolerance",
    )
    separation_tolerance = _positive_tolerance(
        feature_separation_tolerance,
        "feature_separation_tolerance",
    )
    for name in (
        "ell_values",
        "coordinate_frame",
        "harmonic_convention",
        "anchor_id",
        "anchor_stress_interval",
        "mask_id",
        "beam_id",
        "foreground_model_id",
    ):
        if getattr(left, name) != getattr(right, name):
            raise LowEllCounterpairError(
                f"matched counterpair requires identical {name}"
            )
    if left.cl_by_ell != right.cl_by_ell:
        raise LowEllCounterpairError(
            "matched counterpair requires an identical exact C_ell vector"
        )
    registered_cl = dict(left.cl_by_ell)
    for side, packet in (("left", left), ("right", right)):
        replayed_cl = compute_cl_from_alm(_alm_mapping(packet.alm_entries))
        if any(
            not math.isclose(
                float(replayed_cl[ell]),
                registered_cl[ell],
                rel_tol=power_tolerance,
                abs_tol=0.0,
            )
            for ell in registered_cl
        ):
            raise LowEllCounterpairError(
                f"{side} packet alms do not replay the registered C_ell vector"
            )
    if left.intervention is not None or left.parent_packet_id is not None:
        raise LowEllCounterpairError(
            "left counterpair member must be the registered reference packet"
        )
    if (
        right.intervention is None
        or right.intervention.factor is not factor
        or right.parent_packet_id != left.packet_id
    ):
        raise LowEllCounterpairError(
            "right packet must bind the declared intervention and reference"
        )
    expected_entries = _canonical_dense_alm(
        _apply_intervention_to_alm(left.alm_entries, right.intervention),
        ell_values=left.ell_values,
    )
    if expected_entries != right.alm_entries:
        raise LowEllCounterpairError(
            "right alm bytes do not match the registered intervention"
        )
    if factor is CounterpairFactor.PHASE:
        if left.phase_id == right.phase_id:
            raise LowEllCounterpairError(
                "phase counterpair must have different normalized alm phases"
            )
        if (
            right.intervention.operator
            is not InterventionOperator.NONLINEAR_M_PHASE_V1
            or left.parity_realization is not right.parity_realization
        ):
            raise LowEllCounterpairError(
                "phase counterpair must use the disjoint nonlinear-m phase action"
            )
    elif factor is CounterpairFactor.ORIENTATION:
        left_power = left.feature(
            MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR
        )
        right_power = right.feature(
            MorphologyFeatureKind.MULTIPOLE_POWER_TENSOR
        )
        if left_power.content_id == right_power.content_id:
            raise LowEllCounterpairError(
                "orientation counterpair must change the power tensor"
            )
        if (
            right.intervention.operator
            is not InterventionOperator.COMMON_PROPER_Z_ROTATION_V1
            or left.parity_realization is not right.parity_realization
        ):
            raise LowEllCounterpairError(
                "orientation counterpair must use one common proper rotation"
            )
    else:
        if {
            left.parity_realization,
            right.parity_realization,
        } != {
            ParityRealization.REFERENCE,
            ParityRealization.O3_REFLECTION,
        }:
            raise LowEllCounterpairError(
                "parity counterpair requires one reference and one reflection"
            )
        if (
            right.intervention.operator
            is not InterventionOperator.SCALAR_PARITY_V1
        ):
            raise LowEllCounterpairError(
                "parity counterpair must use scalar parity without a rotation"
            )

    distances: list[tuple[MorphologyFeatureKind, float | None]] = []
    separated: list[MorphologyFeatureKind] = []
    missing: list[MorphologyFeatureKind] = []
    for kind in MorphologyFeatureKind:
        left_feature = left.feature(kind)
        right_feature = right.feature(kind)
        if left_feature.availability is not right_feature.availability:
            raise LowEllCounterpairError(
                f"{kind.value} feature availability must match"
            )
        if left_feature.provider_id != right_feature.provider_id:
            raise LowEllCounterpairError(
                f"{kind.value} feature provider identity must match"
            )
        if left_feature.units != right_feature.units:
            raise LowEllCounterpairError(
                f"{kind.value} feature units must match"
            )
        if (
            left_feature.availability is FeatureAvailability.MISSING_FEATURE_PROVIDER
        ):
            if left_feature.missing_reason != right_feature.missing_reason:
                raise LowEllCounterpairError(
                    f"{kind.value} missing-provider reason must match"
                )
            distances.append((kind, None))
            missing.append(kind)
            continue
        left_values = np.asarray(left_feature.values)
        right_values = np.asarray(right_feature.values)
        if left_values.shape != right_values.shape:
            raise LowEllCounterpairError(
                f"{kind.value} feature shapes must match"
            )
        distance = float(np.linalg.norm(left_values - right_values))
        distances.append((kind, distance))
        if distance > separation_tolerance:
            separated.append(kind)

    if not separated:
        raise LowEllCounterpairError(
            "registered features do not separate the declared counterpair"
        )

    return MatchedCounterpairReport(
        pair_id=pair_id,
        factor=factor,
        left=left,
        right=right,
        feature_distances=tuple(distances),
        separated_feature_kinds=tuple(separated),
        missing_feature_kinds=tuple(missing),
        power_relative_tolerance=power_tolerance,
        feature_separation_tolerance=separation_tolerance,
        _construction_token=_PAIR_TOKEN,
    )


def revalidate_matched_counterpair(
    report: MatchedCounterpairReport,
) -> MatchedCounterpairReport:
    if type(report) is not MatchedCounterpairReport:
        raise LowEllCounterpairError(
            "report must be an exact MatchedCounterpairReport"
        )
    rebuilt = build_matched_counterpair(
        pair_id=report.pair_id,
        factor=report.factor,
        left=report.left,
        right=report.right,
        power_relative_tolerance=report.power_relative_tolerance,
        feature_separation_tolerance=report.feature_separation_tolerance,
    )
    if rebuilt.as_payload() != report.as_payload():
        raise LowEllCounterpairError(
            "counterpair report fields do not match bound feature packets"
        )
    return rebuilt


__all__ = [
    "CounterpairFactor",
    "FeatureAvailability",
    "InterventionOperator",
    "LowEllCounterpairError",
    "LowEllInterventionSpec",
    "LowEllMorphologyFeaturePacket",
    "MatchedCounterpairReport",
    "MorphologyFeatureKind",
    "ParityRealization",
    "RegisteredMorphologyFeature",
    "apply_lowell_counterpair_intervention",
    "build_lowell_morphology_feature_packet",
    "build_matched_counterpair",
    "register_morphology_feature",
    "revalidate_matched_counterpair",
]
