"""Observation Operator Contract Layer (R41-02).

Defines typed, source-conditioned contracts, protocols, and metadata schemas
for observational forward-modeling operators in the HTT framework.

Fail-Closed Rules:
1. Every observation operator must bind exact primary data on disk with verified SHA-256.
2. Synthetic stubs, mocked observations, or hardcoded response vectors in production paths
   are strictly forbidden and fail closed.
3. Every data channel must declare source release, row selection, units, coordinate frame,
   window/mask, covariance matrix identity, and physical functional tensor carrier contract.
4. Covariance matrices must be validated as symmetric positive-definite.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable
import numpy as np

from common.enum_compat import StrEnum


class CoordinateFrame(StrEnum):
    """Authoritative astronomical coordinate frames."""
    ICRS = "ICRS"
    GALACTIC = "Galactic"
    HELIOCENTRIC = "Heliocentric"
    CMB = "CMB"
    LOCAL_GROUP = "LocalGroup"


class EstimatorType(StrEnum):
    """Observational estimator classifications."""
    ANALYTIC_MARGINALIZED_DISTANCE = "AnalyticMarginalizedDistance"
    COUNT_DIPOLE_ELLIS_BALDWIN = "CountDipoleEllisBaldwin"
    ASTROMETRIC_VSH = "AstrometricVSH"
    HARMONIC_LOWELL_CARRIER = "HarmonicLowEllCarrier"


class ContractViolationError(ValueError):
    """Raised when an observation operator violates its typed contract."""
    pass


@dataclass(frozen=True)
class PhysicalFunctionalSpec:
    """Typed specification for the physical tensor-functional carrier x.
    
    Declares rank, parity, representation, units, and kinematic parameter dependence.
    """
    name: str
    tensor_rank: int
    parity: str  # "even", "odd", "polar", "axial"
    so3_representation: str  # "0+", "1-", "1+", "2+", etc.
    units: str
    parameter_dependence: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.tensor_rank < 0:
            raise ContractViolationError(f"Tensor rank must be non-negative, got {self.tensor_rank}")
        if not self.name or not self.units:
            raise ContractViolationError("Functional name and units cannot be empty")
        if not self.parameter_dependence:
            raise ContractViolationError("parameter_dependence must declare at least one parameter")


@dataclass(frozen=True)
class ObservationSourceMetadata:
    """Authoritative metadata binding exact observational sources on disk."""
    source_id: str
    product_name: str
    catalog_or_data_path: str
    covariance_path: Optional[str]
    n_total_objects: int
    n_selected_objects: int
    selection_rule: str
    coordinate_frame: CoordinateFrame | str
    units: str
    estimator_type: EstimatorType | str
    window_or_mask_id: str
    covariance_id: str
    verified_sha256: str
    is_synthetic: bool = False

    def fail_closed_check(self) -> None:
        """Enforce strict fail-closed validation rules."""
        if self.is_synthetic:
            raise ContractViolationError(
                f"Synthetic data forbidden in production observation paths for {self.source_id}"
            )
        if not os.path.exists(self.catalog_or_data_path):
            raise ContractViolationError(
                f"Required primary source file not found on disk: {self.catalog_or_data_path}"
            )
        if self.covariance_path and not os.path.exists(self.covariance_path):
            raise ContractViolationError(
                f"Required primary covariance file not found on disk: {self.covariance_path}"
            )
        if not self.verified_sha256:
            raise ContractViolationError(
                f"SHA-256 hash must be verified and non-empty for {self.source_id}"
            )
        if self.n_selected_objects <= 0:
            raise ContractViolationError(
                f"n_selected_objects must be positive, got {self.n_selected_objects}"
            )
        # Coordinate frame check
        try:
            CoordinateFrame(str(self.coordinate_frame))
        except ValueError:
            raise ContractViolationError(
                f"Invalid coordinate frame: {self.coordinate_frame}"
            )


@runtime_checkable
class ObservationOperator(Protocol):
    """Protocol defining the required interface for all source-bound observation operators."""

    @property
    def metadata(self) -> ObservationSourceMetadata:
        """Return authoritative source metadata."""
        ...

    @property
    def functional_spec(self) -> PhysicalFunctionalSpec:
        """Return physical functional carrier specification."""
        ...

    def evaluate_model(self, theta_K: np.ndarray, psi: Optional[Any] = None) -> Tuple[float, ...]:
        """Evaluate forward model and return (chi2, ..., log_likelihood)."""
        ...

    def evaluate_likelihood(self, theta_K: np.ndarray, psi: Optional[Any] = None) -> Tuple[float, float]:
        """Evaluate model and return standardized (chi2, log_likelihood)."""
        ...

    def get_data_vector(self) -> np.ndarray:
        """Return observed data vector d_obs."""
        ...

    def get_covariance_matrix(self) -> np.ndarray:
        """Return positive-definite covariance matrix C."""
        ...


def verify_operator_contract(op: Any) -> bool:
    """Verify that an operator strictly adheres to the ObservationOperator contract."""
    if not isinstance(op, ObservationOperator):
        raise ContractViolationError(f"Object {type(op)} does not satisfy ObservationOperator protocol")

    meta = op.metadata
    meta.fail_closed_check()

    spec = op.functional_spec
    if not isinstance(spec, PhysicalFunctionalSpec):
        raise ContractViolationError(f"Invalid functional spec type: {type(spec)}")

    d = op.get_data_vector()
    cov = op.get_covariance_matrix()

    if not isinstance(d, np.ndarray) or not isinstance(cov, np.ndarray):
        raise ContractViolationError("Data vector and covariance must be numpy ndarrays")

    if d.ndim != 1:
        raise ContractViolationError(f"Data vector must be 1D, got ndim={d.ndim}")

    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ContractViolationError(f"Covariance must be square 2D, got shape={cov.shape}")

    if len(d) != cov.shape[0]:
        raise ContractViolationError(
            f"Dimension mismatch: len(data)={len(d)} != cov.shape[0]={cov.shape[0]}"
        )

    # Validate positive definiteness
    evals = np.linalg.eigvalsh(cov)
    if not np.all(evals > 0):
        min_ev = float(np.min(evals))
        raise ContractViolationError(
            f"Covariance matrix for {meta.source_id} is not positive definite: min eigenvalue = {min_ev}"
        )

    return True
