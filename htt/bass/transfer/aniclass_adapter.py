"""Transfer-conditional wrappers for legacy AniCLASS-calibrated paths.

The adapters in this module attach PR-014 transfer provenance to existing
legacy BASS/HTT callables.  They do not call CLASS/AniCLASS, implement a native
low-ell solver, or promote external calibration to native validation.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from importlib import import_module
import math
from typing import Any

from common.transfer_registry import (
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
    validate_transfer_dependent_result,
)


@dataclass(frozen=True)
class TransferEvaluation:
    """Value plus transfer provenance for a wrapped legacy callable."""

    value: Any
    transfer_metadata: dict[str, object]
    claim_tier: str = "conditional"
    transfer_conditional: bool = True
    native_solver_result: bool = False


@dataclass(frozen=True)
class ExternalTransferAdapter:
    """Attach transfer-conditional metadata to one legacy callable."""

    transfer_spec: TransferFunctionSpec
    callable_path: str
    parameter_range: Mapping[str, object] | None = None
    implementation_scope: str = "bass_py"
    claim_tier: str = "conditional"
    production_status: str = "diagnostic_only"

    def __post_init__(self) -> None:
        if not isinstance(self.transfer_spec, TransferFunctionSpec):
            raise TypeError(
                "ExternalTransferAdapter.transfer_spec must be TransferFunctionSpec"
            )
        if self.transfer_spec.is_native:
            raise ValueError("external transfer adapter cannot wrap native transfer")
        if self.transfer_spec.source not in _ALLOWED_ADAPTER_SOURCES:
            raise ValueError(
                "external transfer adapter requires external or empirical_proxy source"
            )
        if self.claim_tier != "conditional":
            raise ValueError("external transfer adapter claim_tier must be conditional")
        if self.production_status != "diagnostic_only":
            raise ValueError(
                "external transfer adapter production_status must be diagnostic_only"
            )
        if ":" not in self.callable_path:
            raise ValueError("callable_path must have form 'module:function'")
        metadata = self.transfer_spec.to_metadata()
        validate_transfer_dependent_result(metadata)

    @property
    def transfer_id(self) -> str:
        return self.transfer_spec.transfer_id

    def metadata(self) -> dict[str, object]:
        """Return transfer metadata plus adapter-specific provenance fields."""

        metadata = self.transfer_spec.to_metadata()
        metadata.update(
            {
                "claim_tier": self.claim_tier,
                "production_status": self.production_status,
                "implementation_scope": self.implementation_scope,
                "transfer_conditional": True,
                "native_solver_result": False,
                "callable_path": self.callable_path,
                "parameter_range": dict(self.parameter_range or {}),
                "callable_input_domain": dict(self.parameter_range or {}),
                "valid_range_role": (
                    "pr014_transfer_spec_ell_range; callable input domain is "
                    "callable_input_domain"
                ),
            }
        )
        validate_transfer_dependent_result(metadata)
        return metadata

    def evaluate(self, *args: Any, **kwargs: Any) -> TransferEvaluation:
        """Run the legacy callable and attach validated transfer metadata."""

        self._validate_input_domain(args, kwargs)
        value = _load_callable(self.callable_path)(*args, **kwargs)
        metadata = self.metadata()
        return TransferEvaluation(
            value=value,
            transfer_metadata=metadata,
            claim_tier=self.claim_tier,
            transfer_conditional=True,
            native_solver_result=False,
        )

    def _validate_input_domain(
        self,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> None:
        domain = dict(self.parameter_range or {})
        if "x_h_min" in domain or "x_h_max" in domain:
            value = _first_argument(args, kwargs, "x_h")
            _require_in_domain(
                value,
                lower=_optional_domain_bound(domain, "x_h_min", -math.inf),
                upper=_optional_domain_bound(domain, "x_h_max", math.inf),
                label="x_h",
            )
        if "Sigma2_min" in domain or "Sigma2_max" in domain:
            value = _first_argument(args, kwargs, "Sigma2")
            _require_in_domain(
                value,
                lower=_optional_domain_bound(domain, "Sigma2_min", -math.inf),
                upper=_optional_domain_bound(domain, "Sigma2_max", math.inf),
                label="Sigma2",
            )


class ExternalTransferAdapterRegistry:
    """Registry pairing PR-014 specs with lazy legacy-callable adapters."""

    def __init__(self, adapters: Iterable[ExternalTransferAdapter] = ()) -> None:
        self._adapters: dict[str, ExternalTransferAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ExternalTransferAdapter) -> ExternalTransferAdapter:
        if not isinstance(adapter, ExternalTransferAdapter):
            raise TypeError(
                "ExternalTransferAdapterRegistry.register requires ExternalTransferAdapter"
            )
        if adapter.transfer_id in self._adapters:
            raise ValueError(f"duplicate transfer_id {adapter.transfer_id!r}")
        self._adapters[adapter.transfer_id] = adapter
        return adapter

    def get(self, transfer_id: str) -> ExternalTransferAdapter:
        try:
            return self._adapters[transfer_id]
        except KeyError as exc:
            raise KeyError(f"unknown transfer_id {transfer_id!r}") from exc

    def transfer_ids(self) -> tuple[str, ...]:
        return tuple(self._adapters)

    def all(self) -> tuple[ExternalTransferAdapter, ...]:
        return tuple(self._adapters.values())

    def as_transfer_registry(self) -> TransferRegistry:
        return TransferRegistry(adapter.transfer_spec for adapter in self.all())

    def evaluate(
        self,
        transfer_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> TransferEvaluation:
        return self.get(transfer_id).evaluate(*args, **kwargs)


def _load_callable(path: str) -> Callable[..., Any]:
    module_name, function_name = path.split(":", 1)
    module = import_module(module_name)
    function = getattr(module, function_name)
    if not callable(function):
        raise TypeError(f"{path!r} does not resolve to a callable")
    return function


def _first_argument(
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
    name: str,
) -> Any:
    if args:
        return args[0]
    if name in kwargs:
        return kwargs[name]
    raise ValueError(f"{name} input is required for transfer adapter evaluation")


def _require_in_domain(value: Any, *, lower: float, upper: float, label: str) -> None:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} input must be numeric") from exc
    if not math.isfinite(numeric) or not (lower <= numeric <= upper):
        raise ValueError(
            f"{label} input {numeric!r} outside transfer adapter domain "
            f"[{lower}, {upper}]"
        )


def _optional_domain_bound(
    domain: Mapping[str, object],
    key: str,
    default: float,
) -> float:
    if key not in domain:
        return default
    try:
        bound = float(domain[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} transfer adapter domain bound must be numeric") from exc
    if math.isnan(bound):
        raise ValueError(f"{key} transfer adapter domain bound must be finite or inf")
    return bound


_ALLOWED_ADAPTER_SOURCES = {
    TransferSource.ANICLASS_EXTERNAL,
    TransferSource.EXTERNAL_TRANSFER,
    TransferSource.EMPIRICAL_PROXY,
}


__all__ = [
    "ExternalTransferAdapter",
    "ExternalTransferAdapterRegistry",
    "TransferEvaluation",
]
