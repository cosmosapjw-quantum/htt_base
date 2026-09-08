"""One-way, same-channel MES premise normalization.

The normalizer scales numerical coordinates that already have declared support.
It cannot create direction, STF shape, a response, independent information, or
a physical state.  Registered MES coefficients remain owned by
``common.statistical_foundations``.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
import hashlib
import json
import math
from numbers import Real
from typing import ClassVar, Mapping, Sequence

from common.statistical_foundations import MESAnchorSpec


class MesPremiseNormalizationError(ValueError):
    """Raised when a premise normalization crosses a typed channel boundary."""


_REPORT_TOKEN = object()


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
        raise MesPremiseNormalizationError(f"{name} must be a non-empty string")
    return value.strip()


def _sha256_identity(value: object, name: str) -> str:
    normalized = _text(value, name)
    if not normalized.startswith("sha256:"):
        raise MesPremiseNormalizationError(
            f"{name} must be a sha256 content identity"
        )
    digest = normalized.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise MesPremiseNormalizationError(
            f"{name} must be a sha256 content identity"
        )
    return normalized


def _channel_key(value: object, name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise MesPremiseNormalizationError(f"{name} must be a channel sequence")
    normalized = tuple(_text(item, name) for item in value)
    if not normalized:
        raise MesPremiseNormalizationError(f"{name} must not be empty")
    return normalized


def _values(value: object, name: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise MesPremiseNormalizationError(
            f"{name} must be a supported numerical coordinate sequence"
        )
    normalized: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, Real):
            raise MesPremiseNormalizationError(f"{name} must contain finite reals")
        number = float(item)
        if not math.isfinite(number):
            raise MesPremiseNormalizationError(f"{name} must contain finite reals")
        normalized.append(number)
    if not normalized:
        raise MesPremiseNormalizationError(f"{name} must not be empty")
    return tuple(normalized)


@dataclass(frozen=True)
class MesPremiseNormalizer:
    """Factory-built report for one dimension-preserving MES scaling operation."""

    numerator_values: tuple[float, ...]
    normalized_values: tuple[float, ...]
    numerator_identity: str
    anchor_identity: str
    anchor_id: str
    anchor_value: float
    channel_key: tuple[str, ...]
    conditioning: str
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_MES_PREMISE_NORMALIZER_V1"
    creates_direction: ClassVar[bool] = False
    creates_shape: ClassVar[bool] = False
    creates_information: ClassVar[bool] = False
    creates_response: ClassVar[bool] = False
    physical_state_constructed: ClassVar[bool] = False
    claim_ceiling: ClassVar[str] = "diagnostic_only_same_channel_normalization"

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise MesPremiseNormalizationError(
                "MesPremiseNormalizer must be factory-built"
            )
        numerator = _values(self.numerator_values, "numerator_values")
        normalized = _values(self.normalized_values, "normalized_values")
        if len(numerator) != len(normalized):
            raise MesPremiseNormalizationError(
                "normalization must preserve coordinate dimension"
            )
        anchor_value = float(self.anchor_value)
        if not math.isfinite(anchor_value) or anchor_value <= 0.0:
            raise MesPremiseNormalizationError("anchor_value must be finite and positive")
        expected = tuple(value / anchor_value for value in numerator)
        if normalized != expected:
            raise MesPremiseNormalizationError(
                "normalized values must be the exact one-way anchor scaling"
            )
        object.__setattr__(self, "numerator_values", numerator)
        object.__setattr__(self, "normalized_values", normalized)
        object.__setattr__(
            self,
            "numerator_identity",
            _sha256_identity(self.numerator_identity, "numerator_identity"),
        )
        object.__setattr__(
            self,
            "anchor_identity",
            _sha256_identity(self.anchor_identity, "anchor_identity"),
        )
        object.__setattr__(self, "anchor_id", _text(self.anchor_id, "anchor_id"))
        object.__setattr__(self, "anchor_value", anchor_value)
        object.__setattr__(
            self,
            "channel_key",
            _channel_key(self.channel_key, "channel_key"),
        )
        object.__setattr__(
            self,
            "conditioning",
            _text(self.conditioning, "conditioning"),
        )
        object.__setattr__(self, "_identity_seal", _content_id(self._payload_unchecked()))

    @property
    def content_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "anchor_identity": self.anchor_identity,
            "anchor_value_hex": self.anchor_value.hex(),
            "channel_key": list(self.channel_key),
            "claim_ceiling": self.claim_ceiling,
            "conditioning": self.conditioning,
            "creates_direction": self.creates_direction,
            "creates_information": self.creates_information,
            "creates_response": self.creates_response,
            "creates_shape": self.creates_shape,
            "normalized_values_hex": [value.hex() for value in self.normalized_values],
            "numerator_identity": self.numerator_identity,
            "numerator_values_hex": [value.hex() for value in self.numerator_values],
            "physical_state_constructed": self.physical_state_constructed,
            "schema": self.schema,
        }

    def _assert_sealed(self) -> None:
        if _content_id(self._payload_unchecked()) != self._identity_seal:
            raise MesPremiseNormalizationError(
                "MES premise normalization identity drifted after construction"
            )

    def to_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}

    @classmethod
    def from_payload(cls, payload: object) -> "MesPremiseNormalizer":
        if not isinstance(payload, Mapping):
            raise MesPremiseNormalizationError("normalizer payload must be a mapping")
        expected = {
            "anchor_id",
            "anchor_identity",
            "anchor_value_hex",
            "channel_key",
            "claim_ceiling",
            "conditioning",
            "content_id",
            "creates_direction",
            "creates_information",
            "creates_response",
            "creates_shape",
            "normalized_values_hex",
            "numerator_identity",
            "numerator_values_hex",
            "physical_state_constructed",
            "schema",
        }
        if set(payload) != expected:
            raise MesPremiseNormalizationError("normalizer payload keys mismatch")
        fixed = {
            "schema": cls.schema,
            "claim_ceiling": cls.claim_ceiling,
            "creates_direction": False,
            "creates_shape": False,
            "creates_information": False,
            "creates_response": False,
            "physical_state_constructed": False,
        }
        for key, value in fixed.items():
            if payload[key] != value:
                raise MesPremiseNormalizationError(
                    f"normalizer claim boundary drifted: {key}"
                )
        try:
            report = cls(
                numerator_values=tuple(
                    float.fromhex(str(value)) for value in payload["numerator_values_hex"]
                ),
                normalized_values=tuple(
                    float.fromhex(str(value)) for value in payload["normalized_values_hex"]
                ),
                numerator_identity=payload["numerator_identity"],  # type: ignore[arg-type]
                anchor_identity=payload["anchor_identity"],  # type: ignore[arg-type]
                anchor_id=payload["anchor_id"],  # type: ignore[arg-type]
                anchor_value=float.fromhex(str(payload["anchor_value_hex"])),
                channel_key=tuple(payload["channel_key"]),  # type: ignore[arg-type]
                conditioning=payload["conditioning"],  # type: ignore[arg-type]
                _construction_token=_REPORT_TOKEN,
            )
        except (TypeError, ValueError) as exc:
            raise MesPremiseNormalizationError(
                "normalizer payload contains invalid numerical encoding"
            ) from exc
        if payload["content_id"] != report.content_id:
            raise MesPremiseNormalizationError(
                "normalizer payload content identity mismatch"
            )
        return report


def normalize_mes_premise(
    *,
    numerator: Sequence[Real],
    numerator_channel_key: Sequence[str],
    numerator_identity: str,
    anchor: MESAnchorSpec,
) -> MesPremiseNormalizer:
    """Scale one supplied coordinate sequence by one exact compatible anchor."""

    if type(anchor) is not MESAnchorSpec or not anchor.normalization_allowed:
        raise MesPremiseNormalizationError(
            "an exact verified normalization-eligible MESAnchorSpec is required"
        )
    channel_key = _channel_key(numerator_channel_key, "numerator_channel_key")
    if channel_key != anchor.channel_key:
        raise MesPremiseNormalizationError(
            "numerator and anchor channel identities must match exactly"
        )
    values = _values(numerator, "numerator")
    identity = _sha256_identity(numerator_identity, "numerator_identity")
    anchor_payload = {
        "anchor_id": anchor.anchor_id,
        "anchor_value_hex": anchor.value.hex(),
        "authority_kind": anchor.authority_kind.value,
        "channel_key": list(anchor.channel_key),
        "conditioning": anchor.conditioning.value,
        "status": anchor.status.value,
    }
    return MesPremiseNormalizer(
        numerator_values=values,
        normalized_values=tuple(value / anchor.value for value in values),
        numerator_identity=identity,
        anchor_identity=_content_id(anchor_payload),
        anchor_id=anchor.anchor_id,
        anchor_value=anchor.value,
        channel_key=channel_key,
        conditioning=anchor.conditioning.value,
        _construction_token=_REPORT_TOKEN,
    )


__all__ = [
    "MesPremiseNormalizationError",
    "MesPremiseNormalizer",
    "normalize_mes_premise",
]
