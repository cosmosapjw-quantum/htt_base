"""Thin workspace aliases for canonical COMMON transfer contracts."""

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
    TransferValidRange,
    validate_transfer_dependent_result,
)

__all__ = [
    "CalibrationStatus",
    "ObservableKind",
    "TransferFunctionSpec",
    "TransferRegistry",
    "TransferSource",
    "TransferValidRange",
    "validate_transfer_dependent_result",
]
