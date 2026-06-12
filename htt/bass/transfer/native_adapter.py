"""Fail-closed adapter stub for a future low-ell solver artifact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .native_schema import NativeLowEllSchema, default_native_lowell_schema

_NOT_ATTACHED = (
    "future low-ell solver artifact is not attached to htt_base; "
    "PR-081 exposes schema metadata only and cannot return solver values"
)


@dataclass(frozen=True)
class FutureNativeLowEllAdapterStub:
    """Metadata-only native adapter placeholder.

    This class intentionally has execution-shaped methods so accidental callers
    fail with a precise error instead of receiving synthetic native data.
    """

    schema: NativeLowEllSchema
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    production_status: str = "schema_only"

    def __post_init__(self) -> None:
        if not isinstance(self.schema, NativeLowEllSchema):
            raise TypeError(
                "FutureNativeLowEllAdapterStub.schema must be NativeLowEllSchema"
            )
        if self.claim_tier != "diagnostic_only":
            raise ValueError(
                "FutureNativeLowEllAdapterStub.claim_tier must be diagnostic_only"
            )
        if self.production_status != "schema_only":
            raise ValueError(
                "FutureNativeLowEllAdapterStub.production_status must be schema_only"
            )

    def metadata(self) -> dict[str, object]:
        metadata = self.schema.to_metadata()
        metadata.update(
            {
                "implementation_scope": self.implementation_scope,
                "claim_tier": self.claim_tier,
                "production_status": self.production_status,
                "native_solver_result": False,
                "returns_values": False,
                "outputs_available": False,
                "adapter_status": "not_attached_schema_only",
                "execution_status": "not_implemented_until_external_solver_arrives",
            }
        )
        return metadata

    def transfer_ids(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.metadata()["transfer_ids"])

    def evaluate(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError(_NOT_ATTACHED)

    def solve(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError(_NOT_ATTACHED)

    def load_solver_output(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError(_NOT_ATTACHED)

    def __call__(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError(_NOT_ATTACHED)


def default_native_lowell_adapter_stub() -> FutureNativeLowEllAdapterStub:
    """Return the default fail-closed native low-ell adapter stub."""

    return FutureNativeLowEllAdapterStub(schema=default_native_lowell_schema())


__all__ = [
    "FutureNativeLowEllAdapterStub",
    "default_native_lowell_adapter_stub",
]
