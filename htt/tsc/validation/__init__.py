"""Theorem/proof-obligation registry for TSC validation artifacts."""

from .theorem_map import (
    CORE_THEOREM_MAP,
    TSC_VALIDATION_WITNESSES,
    TheoremTestLink,
    TscValidationWitness,
    build_tsc_validation_witnesses,
)

__all__ = [
    "CORE_THEOREM_MAP",
    "TSC_VALIDATION_WITNESSES",
    "TheoremTestLink",
    "TscValidationWitness",
    "build_tsc_validation_witnesses",
]
