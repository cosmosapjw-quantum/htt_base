"""MIO diagnostic bridge for COMMON-owned tensor functionals.

The implementation and anchor authority remain in :mod:`common`.  MIO may
consume the typed diagnostic results but gains no posterior, likelihood, or
evidence operation.
"""

from __future__ import annotations

from common.tensor_functionals import (
    FUNCTIONAL_ALLOWED_USE,
    FUNCTIONAL_CLAIM_CEILING,
    FUNCTIONAL_FORBIDDEN_USE,
    FunctionalAdmissibilityReport,
    FunctionalAdmissibilityStatus,
    FunctionalAnchorReport,
    FunctionalAnchorStatus,
    FunctionalCodomainReport,
    FunctionalDomainReport,
    FunctionalDomainStatus,
    FunctionalO3Type,
    FunctionalSignClass,
    FunctionalStressReport,
    FunctionalStressStatus,
    TensorFunctionalError,
    TensorFunctionalOperator,
    TensorFunctionalResult,
    TensorFunctionalSpec,
    build_tensor_functional_spec,
    evaluate_tensor_functional,
    revalidate_tensor_functional_result,
)

__mio_owned__ = True

__all__ = [
    "FUNCTIONAL_ALLOWED_USE",
    "FUNCTIONAL_CLAIM_CEILING",
    "FUNCTIONAL_FORBIDDEN_USE",
    "FunctionalAdmissibilityReport",
    "FunctionalAdmissibilityStatus",
    "FunctionalAnchorReport",
    "FunctionalAnchorStatus",
    "FunctionalCodomainReport",
    "FunctionalDomainReport",
    "FunctionalDomainStatus",
    "FunctionalO3Type",
    "FunctionalSignClass",
    "FunctionalStressReport",
    "FunctionalStressStatus",
    "TensorFunctionalError",
    "TensorFunctionalOperator",
    "TensorFunctionalResult",
    "TensorFunctionalSpec",
    "build_tensor_functional_spec",
    "evaluate_tensor_functional",
    "revalidate_tensor_functional_result",
]
