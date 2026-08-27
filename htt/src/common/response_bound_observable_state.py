"""Content-bound observable/response compatibility without physical promotion.

This module records that an observer-space irrep state is compatible with a
separately certified response identity.  It does not implement or invert a
forward model and never constructs ``JointAnisotropyState``.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
import hashlib
import json
from typing import ClassVar, Mapping, Sequence

from common.enum_compat import StrEnum
from common.observable_irrep_state import (
    ObservableIrrepAvailability,
    ObservableIrrepState,
    observable_irrep_state_from_payload,
)


class ResponseBindingError(ValueError):
    """Raised when response metadata cannot bind one observable state exactly."""


class ResponseIdentificationStatus(StrEnum):
    """Algebraic identification status under the declared response rank."""

    POINT_IDENTIFIED = "POINT_IDENTIFIED"
    IDENTIFIED_SET = "IDENTIFIED_SET"


_BOUND_TOKEN = object()


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
        raise ResponseBindingError(f"{name} must be a non-empty string")
    return value.strip()


def _sha256_identity(value: object, name: str) -> str:
    normalized = _text(value, name)
    if not normalized.startswith("sha256:"):
        raise ResponseBindingError(f"{name} must be a sha256 content identity")
    digest = normalized.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ResponseBindingError(f"{name} must be a sha256 content identity")
    return normalized


def _channel_key(value: object, name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ResponseBindingError(f"{name} must be a channel sequence")
    normalized = tuple(_text(item, name) for item in value)
    if not normalized:
        raise ResponseBindingError(f"{name} must not be empty")
    return normalized


def _integer(value: object, name: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ResponseBindingError(f"{name} must be an integer >= {minimum}")
    return value


def _observable_dimension(state: ObservableIrrepState) -> int:
    return sum(
        len(block.components)
        for block in state.blocks
        if block.availability is ObservableIrrepAvailability.AVAILABLE
    )


@dataclass(frozen=True)
class ResponseBoundObservableState:
    """Factory-built binding of one exact observable state to response metadata."""

    observable_state: ObservableIrrepState
    observable_content_id: str
    observable_channel_key: tuple[str, ...]
    response_identity: str
    response_channel_key: tuple[str, ...]
    response_frame: str
    response_basis: str
    response_units: str
    response_rank: int
    physical_parameter_dimension: int
    observable_dimension: int
    identification_status: ResponseIdentificationStatus
    identified_set_semantics: str
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    schema: ClassVar[str] = "HTT_RESPONSE_BOUND_OBSERVABLE_STATE_V1"
    claim_ceiling: ClassVar[str] = "diagnostic_only_response_bound"
    physical_state_constructed: ClassVar[bool] = False
    response_model_executed: ClassVar[bool] = False

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _BOUND_TOKEN:
            raise ResponseBindingError(
                "ResponseBoundObservableState must be factory-built"
            )
        if type(self.observable_state) is not ObservableIrrepState:
            raise TypeError("observable_state must be an exact ObservableIrrepState")
        replayed = observable_irrep_state_from_payload(self.observable_state.to_payload())
        if replayed.content_id != self.observable_state.content_id:
            raise ResponseBindingError("observable state content identity drifted")
        observable_content_id = _sha256_identity(
            self.observable_content_id,
            "observable_content_id",
        )
        if observable_content_id != self.observable_state.content_id:
            raise ResponseBindingError("observable content identity mismatch")
        observable_channel = _channel_key(
            self.observable_channel_key,
            "observable_channel_key",
        )
        response_channel = _channel_key(
            self.response_channel_key,
            "response_channel_key",
        )
        if response_channel != observable_channel:
            raise ResponseBindingError("response channel does not match observable channel")
        response_identity = _sha256_identity(
            self.response_identity,
            "response_identity",
        )
        for name, observed, expected in (
            ("frame", self.response_frame, self.observable_state.frame),
            ("basis", self.response_basis, self.observable_state.basis),
            ("units", self.response_units, self.observable_state.units),
        ):
            normalized = _text(observed, f"response_{name}")
            if normalized != expected:
                raise ResponseBindingError(
                    f"response {name} does not match observable {name}"
                )
            object.__setattr__(self, f"response_{name}", normalized)
        response_rank = _integer(self.response_rank, "response_rank", minimum=0)
        physical_dimension = _integer(
            self.physical_parameter_dimension,
            "physical_parameter_dimension",
            minimum=1,
        )
        observable_dimension = _integer(
            self.observable_dimension,
            "observable_dimension",
            minimum=1,
        )
        actual_observable_dimension = _observable_dimension(self.observable_state)
        if observable_dimension != actual_observable_dimension:
            raise ResponseBindingError("observable dimension does not match irrep blocks")
        if response_rank > min(physical_dimension, observable_dimension):
            raise ResponseBindingError("response rank exceeds a declared space dimension")
        expected_status = (
            ResponseIdentificationStatus.POINT_IDENTIFIED
            if response_rank == physical_dimension
            else ResponseIdentificationStatus.IDENTIFIED_SET
        )
        if self.identification_status is not expected_status:
            raise ResponseBindingError("identification status does not match response rank")
        expected_semantics = (
            "FULL_COLUMN_RANK_POINT_IDENTIFICATION_CONDITIONAL_ON_BOUND_RESPONSE"
            if expected_status is ResponseIdentificationStatus.POINT_IDENTIFIED
            else "RANK_DEFICIENT_RESPONSE_IDENTIFIED_SET"
        )
        if self.identified_set_semantics != expected_semantics:
            raise ResponseBindingError("identified-set semantics do not match response rank")
        object.__setattr__(self, "observable_state", replayed)
        object.__setattr__(self, "observable_content_id", observable_content_id)
        object.__setattr__(self, "observable_channel_key", observable_channel)
        object.__setattr__(self, "response_identity", response_identity)
        object.__setattr__(self, "response_channel_key", response_channel)
        object.__setattr__(self, "response_rank", response_rank)
        object.__setattr__(self, "physical_parameter_dimension", physical_dimension)
        object.__setattr__(self, "observable_dimension", observable_dimension)
        object.__setattr__(self, "_identity_seal", _content_id(self._payload_unchecked()))

    @property
    def point_identification_supported(self) -> bool:
        return self.identification_status is ResponseIdentificationStatus.POINT_IDENTIFIED

    @property
    def content_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "claim_ceiling": self.claim_ceiling,
            "identification_status": self.identification_status.value,
            "identified_set_semantics": self.identified_set_semantics,
            "observable_channel_key": list(self.observable_channel_key),
            "observable_content_id": self.observable_content_id,
            "observable_dimension": self.observable_dimension,
            "observable_state": self.observable_state.to_payload(),
            "physical_parameter_dimension": self.physical_parameter_dimension,
            "physical_state_constructed": self.physical_state_constructed,
            "point_identification_supported": self.point_identification_supported,
            "response_basis": self.response_basis,
            "response_channel_key": list(self.response_channel_key),
            "response_frame": self.response_frame,
            "response_identity": self.response_identity,
            "response_model_executed": self.response_model_executed,
            "response_rank": self.response_rank,
            "response_units": self.response_units,
            "schema": self.schema,
        }

    def _assert_sealed(self) -> None:
        if _content_id(self._payload_unchecked()) != self._identity_seal:
            raise ResponseBindingError("response-bound state identity drifted")

    def to_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}

    @classmethod
    def from_payload(cls, payload: object) -> "ResponseBoundObservableState":
        if not isinstance(payload, Mapping):
            raise ResponseBindingError("response-bound payload must be a mapping")
        expected = {
            "claim_ceiling",
            "content_id",
            "identification_status",
            "identified_set_semantics",
            "observable_channel_key",
            "observable_content_id",
            "observable_dimension",
            "observable_state",
            "physical_parameter_dimension",
            "physical_state_constructed",
            "point_identification_supported",
            "response_basis",
            "response_channel_key",
            "response_frame",
            "response_identity",
            "response_model_executed",
            "response_rank",
            "response_units",
            "schema",
        }
        if set(payload) != expected:
            raise ResponseBindingError("response-bound payload keys mismatch")
        if (
            payload["schema"] != cls.schema
            or payload["claim_ceiling"] != cls.claim_ceiling
            or payload["physical_state_constructed"] is not False
            or payload["response_model_executed"] is not False
        ):
            raise ResponseBindingError("response-bound claim boundary drifted")
        try:
            status = ResponseIdentificationStatus(payload["identification_status"])
        except (TypeError, ValueError) as exc:
            raise ResponseBindingError("unknown response identification status") from exc
        bound = cls(
            observable_state=observable_irrep_state_from_payload(payload["observable_state"]),
            observable_content_id=payload["observable_content_id"],  # type: ignore[arg-type]
            observable_channel_key=tuple(payload["observable_channel_key"]),  # type: ignore[arg-type]
            response_identity=payload["response_identity"],  # type: ignore[arg-type]
            response_channel_key=tuple(payload["response_channel_key"]),  # type: ignore[arg-type]
            response_frame=payload["response_frame"],  # type: ignore[arg-type]
            response_basis=payload["response_basis"],  # type: ignore[arg-type]
            response_units=payload["response_units"],  # type: ignore[arg-type]
            response_rank=payload["response_rank"],  # type: ignore[arg-type]
            physical_parameter_dimension=payload["physical_parameter_dimension"],  # type: ignore[arg-type]
            observable_dimension=payload["observable_dimension"],  # type: ignore[arg-type]
            identification_status=status,
            identified_set_semantics=payload["identified_set_semantics"],  # type: ignore[arg-type]
            _construction_token=_BOUND_TOKEN,
        )
        if payload["point_identification_supported"] is not bound.point_identification_supported:
            raise ResponseBindingError("point-identification flag drifted")
        if payload["content_id"] != bound.content_id:
            raise ResponseBindingError("response-bound content identity mismatch")
        return bound


def bind_response_to_observable_state(
    *,
    observable_state: ObservableIrrepState,
    observable_channel_key: Sequence[str],
    response_identity: str,
    response_channel_key: Sequence[str],
    response_frame: str,
    response_basis: str,
    response_units: str,
    response_rank: int,
    physical_parameter_dimension: int,
) -> ResponseBoundObservableState:
    """Bind metadata only; no response matrix is evaluated or inverted here."""

    if type(observable_state) is not ObservableIrrepState:
        raise TypeError("observable_state must be an exact ObservableIrrepState")
    observable_dimension = _observable_dimension(observable_state)
    rank = _integer(response_rank, "response_rank", minimum=0)
    dimension = _integer(
        physical_parameter_dimension,
        "physical_parameter_dimension",
        minimum=1,
    )
    status = (
        ResponseIdentificationStatus.POINT_IDENTIFIED
        if rank == dimension
        else ResponseIdentificationStatus.IDENTIFIED_SET
    )
    semantics = (
        "FULL_COLUMN_RANK_POINT_IDENTIFICATION_CONDITIONAL_ON_BOUND_RESPONSE"
        if status is ResponseIdentificationStatus.POINT_IDENTIFIED
        else "RANK_DEFICIENT_RESPONSE_IDENTIFIED_SET"
    )
    return ResponseBoundObservableState(
        observable_state=observable_state,
        observable_content_id=observable_state.content_id,
        observable_channel_key=_channel_key(
            observable_channel_key,
            "observable_channel_key",
        ),
        response_identity=_sha256_identity(response_identity, "response_identity"),
        response_channel_key=_channel_key(
            response_channel_key,
            "response_channel_key",
        ),
        response_frame=response_frame,
        response_basis=response_basis,
        response_units=response_units,
        response_rank=rank,
        physical_parameter_dimension=dimension,
        observable_dimension=observable_dimension,
        identification_status=status,
        identified_set_semantics=semantics,
        _construction_token=_BOUND_TOKEN,
    )


__all__ = [
    "ResponseBindingError",
    "ResponseBoundObservableState",
    "ResponseIdentificationStatus",
    "bind_response_to_observable_state",
]
