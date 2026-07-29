"""Degree-bounded sigma-omega-beta orbit diagnostics for PR-257.

The catalogue in this module is deliberately narrower than an invariant-ring
or inverse-atlas claim.  It records twelve preregistered polynomials for the
representation

``V2_sigma (STF) + V1_omega (axial) + V1_beta (polar)``

and checks their O(3) parity together with trace-free 3x3
Cayley--Hamilton syzygies.  Passing these checks does not prove generic orbit
separation, catalogue completeness, a physical source, or a Bianchi family.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Mapping

import numpy as np

from common.orbit_nonlinearity import (
    DEPARTURE_O3_PARITY,
    DEPARTURE_O3_UNITS,
    STF5_CARTESIAN_BASIS,
    OrbitNonlinearityError,
    stf5_to_matrix,
)
from common.statistical_foundations import DepartureState


class OrbitCatalogueV2Error(ValueError):
    """Raised when the PR-257 orbit contract is incomplete or inconsistent."""


class PolynomialParity(str, Enum):
    EVEN = "EVEN"
    ODD = "ODD"


class CatalogueClaimStatus(str, Enum):
    PREREGISTERED_DEGREE_BOUNDED = "PREREGISTERED_DEGREE_BOUNDED"
    UNPROVEN = "UNPROVEN"


PR257_POLYNOMIAL_NAMES = (
    "tr_sigma2",
    "tr_sigma3",
    "beta2",
    "beta_sigma_beta",
    "beta_sigma2_beta",
    "det_beta_sigma_beta_sigma2_beta",
    "omega2",
    "omega_sigma_omega",
    "omega_sigma2_omega",
    "beta_dot_omega",
    "beta_sigma_omega",
    "beta_sigma2_omega",
)

PR257_PARITY_BY_NAME: Mapping[str, PolynomialParity] = {
    "tr_sigma2": PolynomialParity.EVEN,
    "tr_sigma3": PolynomialParity.EVEN,
    "beta2": PolynomialParity.EVEN,
    "beta_sigma_beta": PolynomialParity.EVEN,
    "beta_sigma2_beta": PolynomialParity.EVEN,
    "det_beta_sigma_beta_sigma2_beta": PolynomialParity.ODD,
    "omega2": PolynomialParity.EVEN,
    "omega_sigma_omega": PolynomialParity.EVEN,
    "omega_sigma2_omega": PolynomialParity.EVEN,
    "beta_dot_omega": PolynomialParity.ODD,
    "beta_sigma_omega": PolynomialParity.ODD,
    "beta_sigma2_omega": PolynomialParity.ODD,
}

PR257_MULTIPLICITY_METHOD = "MAX_ABS_Z_FIXED_CATALOGUE_V1"
PR257_REPRESENTATION = (
    "V2_SIGMA_STF_PLUS_V1_AXIAL_OMEGA_PLUS_V1_POLAR_BETA"
)
PR257_GENERIC_SEPARATION_STATUS = CatalogueClaimStatus.UNPROVEN
PR257_DEGREE_COMPLETENESS_STATUS = CatalogueClaimStatus.UNPROVEN
_REPORT_TOKEN = object()
_ALLOWED_USE = (
    "degree-bounded orbit morphology diagnostic",
    "O(3) parity regression",
    "Cayley-Hamilton syzygy regression",
)
_FORBIDDEN_USE = (
    "complete invariant basis",
    "generic orbit separation",
    "inverse morphology atlas",
    "source attribution",
    "Bianchi family identification",
)


def _trimmed_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OrbitCatalogueV2Error(f"{name} must be non-empty trimmed text")
    return value


def _positive_tolerance(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise OrbitCatalogueV2Error(f"{name} must not be boolean")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise OrbitCatalogueV2Error(f"{name} must be a finite real") from exc
    if not math.isfinite(out) or out <= 0.0:
        raise OrbitCatalogueV2Error(f"{name} must be finite and positive")
    if out > 1.0e-8:
        raise OrbitCatalogueV2Error(f"{name} must be at most 1e-8")
    return out


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _state_payload(state: DepartureState) -> dict[str, object]:
    return {
        "sigma_ab": [float(value).hex() for value in state.sigma_ab],
        "omega_a": [float(value).hex() for value in state.omega_a],
        "beta_a": [float(value).hex() for value in state.beta_a],
        "delta_omega_k": float(state.delta_omega_k).hex(),
        "frame": state.frame,
        "congruence": state.congruence,
        "epoch_window": state.epoch_window,
        "averaging_scale": state.averaging_scale,
        "basis": state.basis,
        "units": state.units,
        "parity": state.parity,
        "perturbative_order": state.perturbative_order,
    }


@dataclass(frozen=True)
class OrbitCatalogueV2Spec:
    """Frozen catalogue and multiplicity declaration made before test skies."""

    catalog_id: str
    polynomial_names: tuple[str, ...]
    multiplicity_method: str
    alignment_null_id: str
    preregistration_id: str
    cas_contract_id: str
    representation: str = PR257_REPRESENTATION
    generic_orbit_separation_status: CatalogueClaimStatus = (
        PR257_GENERIC_SEPARATION_STATUS
    )
    degree_completeness_status: CatalogueClaimStatus = (
        PR257_DEGREE_COMPLETENESS_STATUS
    )
    syzygy_relative_tolerance: float = 1.0e-12

    def __post_init__(self) -> None:
        for name in (
            "catalog_id",
            "alignment_null_id",
            "preregistration_id",
            "cas_contract_id",
        ):
            _trimmed_text(getattr(self, name), name)
        names = tuple(self.polynomial_names)
        if names != PR257_POLYNOMIAL_NAMES:
            raise OrbitCatalogueV2Error(
                "polynomial_names/order must match the frozen PR-257 catalogue"
            )
        if self.multiplicity_method != PR257_MULTIPLICITY_METHOD:
            raise OrbitCatalogueV2Error(
                "multiplicity_method must use the frozen max-statistic rule"
            )
        if self.representation != PR257_REPRESENTATION:
            raise OrbitCatalogueV2Error(
                "representation must match the registered sigma-omega-beta type"
            )
        if (
            self.generic_orbit_separation_status
            is not CatalogueClaimStatus.UNPROVEN
        ):
            raise OrbitCatalogueV2Error(
                "generic orbit separation must remain UNPROVEN"
            )
        if (
            self.degree_completeness_status
            is not CatalogueClaimStatus.UNPROVEN
        ):
            raise OrbitCatalogueV2Error(
                "degree completeness must remain UNPROVEN"
            )
        object.__setattr__(
            self,
            "syzygy_relative_tolerance",
            _positive_tolerance(
                self.syzygy_relative_tolerance,
                "syzygy_relative_tolerance",
            ),
        )

    @property
    def spec_id(self) -> str:
        return _sha256_payload(
            {
                "alignment_null_id": self.alignment_null_id,
                "cas_contract_id": self.cas_contract_id,
                "catalog_id": self.catalog_id,
                "degree_completeness_status": (
                    self.degree_completeness_status.value
                ),
                "generic_orbit_separation_status": (
                    self.generic_orbit_separation_status.value
                ),
                "polynomial_names": list(self.polynomial_names),
                "multiplicity_method": self.multiplicity_method,
                "preregistration_id": self.preregistration_id,
                "representation": self.representation,
                "schema": "PR257_ORBIT_CATALOGUE_V2_SPEC_V1",
                "syzygy_relative_tolerance_hex": (
                    self.syzygy_relative_tolerance.hex()
                ),
            }
        )


@dataclass(frozen=True)
class OrbitCatalogueV2Report:
    """Factory-derived polynomial values and numerical syzygy residuals."""

    state: DepartureState
    catalog: OrbitCatalogueV2Spec
    polynomial_values: tuple[float, ...]
    parity: tuple[PolynomialParity, ...]
    cayley_hamilton_relative_residual: float
    beta_contraction_relative_residual: float
    omega_contraction_relative_residual: float
    mixed_contraction_relative_residual: float
    beta_krylov_gram_relative_residual: float
    state_id: str
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise OrbitCatalogueV2Error(
                "OrbitCatalogueV2Report must be created by orbit_catalogue_v2"
            )
        if not isinstance(self.state, DepartureState):
            raise OrbitCatalogueV2Error("state must be a DepartureState")
        if not isinstance(self.catalog, OrbitCatalogueV2Spec):
            raise OrbitCatalogueV2Error(
                "catalog must be an OrbitCatalogueV2Spec"
            )
        values = tuple(float(value) for value in self.polynomial_values)
        if len(values) != len(PR257_POLYNOMIAL_NAMES) or not all(
            math.isfinite(value) for value in values
        ):
            raise OrbitCatalogueV2Error(
                "polynomial_values must be twelve finite reals"
            )
        expected_parity = tuple(
            PR257_PARITY_BY_NAME[name] for name in PR257_POLYNOMIAL_NAMES
        )
        if tuple(self.parity) != expected_parity:
            raise OrbitCatalogueV2Error(
                "parity must match the frozen PR-257 polynomial parity"
            )
        tolerance = self.catalog.syzygy_relative_tolerance
        for name in (
            "cayley_hamilton_relative_residual",
            "beta_contraction_relative_residual",
            "omega_contraction_relative_residual",
            "mixed_contraction_relative_residual",
            "beta_krylov_gram_relative_residual",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0 or value > tolerance:
                raise OrbitCatalogueV2Error(
                    f"{name} exceeds the registered syzygy tolerance"
                )
        if self.state_id != _sha256_payload(_state_payload(self.state)):
            raise OrbitCatalogueV2Error("state_id does not bind state bytes")
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise OrbitCatalogueV2Error(
                "orbit report must retain the diagnostic claim boundary"
            )
        object.__setattr__(self, "polynomial_values", values)
        object.__setattr__(self, "parity", expected_parity)

    @property
    def values_by_name(self) -> dict[str, float]:
        return dict(
            zip(PR257_POLYNOMIAL_NAMES, self.polynomial_values, strict=True)
        )

    @property
    def even_values(self) -> tuple[float, ...]:
        return tuple(
            value
            for value, parity in zip(
                self.polynomial_values, self.parity, strict=True
            )
            if parity is PolynomialParity.EVEN
        )

    @property
    def odd_values(self) -> tuple[float, ...]:
        return tuple(
            value
            for value, parity in zip(
                self.polynomial_values, self.parity, strict=True
            )
            if parity is PolynomialParity.ODD
        )

    @property
    def report_id(self) -> str:
        return _sha256_payload(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "catalog_id": self.catalog.catalog_id,
            "catalog_spec_id": self.catalog.spec_id,
            "degree_completeness_status": (
                self.catalog.degree_completeness_status.value
            ),
            "forbidden_use": list(self.forbidden_use),
            "generic_orbit_separation_status": (
                self.catalog.generic_orbit_separation_status.value
            ),
            "typed_polynomials": {
                name: {
                    "parity": parity.value,
                    "value": value,
                }
                for name, value, parity in zip(
                    PR257_POLYNOMIAL_NAMES,
                    self.polynomial_values,
                    self.parity,
                    strict=True,
                )
            },
            "multiplicity_method": self.catalog.multiplicity_method,
            "representation": self.catalog.representation,
            "schema": "PR257_ORBIT_CATALOGUE_V2_REPORT_V1",
            "state_id": self.state_id,
            "syzygy_relative_residuals": {
                "beta_contraction": self.beta_contraction_relative_residual,
                "beta_krylov_gram": (
                    self.beta_krylov_gram_relative_residual
                ),
                "cayley_hamilton": self.cayley_hamilton_relative_residual,
                "mixed_contraction": self.mixed_contraction_relative_residual,
                "omega_contraction": self.omega_contraction_relative_residual,
            },
        }


def _relative_residual(residual: object, *scales: object) -> float:
    residual_array = np.asarray(residual, dtype=float)
    numerator = float(np.linalg.norm(residual_array))
    denominator = max(
        1.0,
        *(
            float(np.linalg.norm(np.asarray(scale, dtype=float)))
            for scale in scales
        ),
    )
    return numerator / denominator


def _quadratic(vector: np.ndarray, matrix: np.ndarray) -> float:
    return float(vector @ matrix @ vector)


def orbit_catalogue_v2(
    state: DepartureState,
    catalog: OrbitCatalogueV2Spec,
) -> OrbitCatalogueV2Report:
    """Evaluate the frozen degree-bounded catalogue on one signed state."""

    if not isinstance(state, DepartureState):
        raise TypeError("state must be a DepartureState")
    if not isinstance(catalog, OrbitCatalogueV2Spec):
        raise TypeError("catalog must be an OrbitCatalogueV2Spec")
    if state.basis != STF5_CARTESIAN_BASIS:
        raise OrbitCatalogueV2Error(
            "orbit catalogue requires the registered STF5 Cartesian basis"
        )
    if state.units != DEPARTURE_O3_UNITS:
        raise OrbitCatalogueV2Error(
            "orbit catalogue requires registered dimensionless units"
        )
    if state.parity != DEPARTURE_O3_PARITY:
        raise OrbitCatalogueV2Error(
            "orbit catalogue requires STF/polar/axial parity metadata"
        )

    sigma = stf5_to_matrix(state.sigma_ab)
    sigma2 = sigma @ sigma
    sigma3 = sigma2 @ sigma
    sigma4 = sigma2 @ sigma2
    beta = np.asarray(state.beta_a, dtype=float)
    omega = np.asarray(state.omega_a, dtype=float)
    tr_sigma2 = float(np.trace(sigma2))
    tr_sigma3 = float(np.trace(sigma3))
    beta_sigma = sigma @ beta
    beta_sigma2 = sigma2 @ beta

    values = (
        tr_sigma2,
        tr_sigma3,
        float(beta @ beta),
        float(beta @ sigma @ beta),
        float(beta @ sigma2 @ beta),
        float(
            np.linalg.det(
                np.column_stack((beta, beta_sigma, beta_sigma2))
            )
        ),
        float(omega @ omega),
        float(omega @ sigma @ omega),
        float(omega @ sigma2 @ omega),
        float(beta @ omega),
        float(beta @ sigma @ omega),
        float(beta @ sigma2 @ omega),
    )

    identity = np.eye(3)
    ch_rhs = 0.5 * tr_sigma2 * sigma + (tr_sigma3 / 3.0) * identity
    ch_residual = sigma3 - ch_rhs
    ch_relative = _relative_residual(ch_residual, sigma3, ch_rhs)

    def contraction_relative(left: np.ndarray, right: np.ndarray) -> float:
        lhs = float(left @ sigma3 @ right)
        rhs = float(
            0.5 * tr_sigma2 * (left @ sigma @ right)
            + (tr_sigma3 / 3.0) * (left @ right)
        )
        return abs(lhs - rhs) / max(1.0, abs(lhs), abs(rhs))

    beta_contraction = contraction_relative(beta, beta)
    omega_contraction = contraction_relative(omega, omega)
    mixed_contraction = contraction_relative(beta, omega)

    krylov = np.column_stack((beta, sigma @ beta, sigma2 @ beta))
    gram = np.array(
        (
            (
                _quadratic(beta, identity),
                _quadratic(beta, sigma),
                _quadratic(beta, sigma2),
            ),
            (
                _quadratic(beta, sigma),
                _quadratic(beta, sigma2),
                _quadratic(beta, sigma3),
            ),
            (
                _quadratic(beta, sigma2),
                _quadratic(beta, sigma3),
                _quadratic(beta, sigma4),
            ),
        )
    )
    determinant_sq = float(np.linalg.det(krylov)) ** 2
    gram_determinant = float(np.linalg.det(gram))
    gram_relative = abs(determinant_sq - gram_determinant) / max(
        1.0, abs(determinant_sq), abs(gram_determinant)
    )

    return OrbitCatalogueV2Report(
        state=state,
        catalog=catalog,
        polynomial_values=values,
        parity=tuple(
            PR257_PARITY_BY_NAME[name] for name in PR257_POLYNOMIAL_NAMES
        ),
        cayley_hamilton_relative_residual=ch_relative,
        beta_contraction_relative_residual=beta_contraction,
        omega_contraction_relative_residual=omega_contraction,
        mixed_contraction_relative_residual=mixed_contraction,
        beta_krylov_gram_relative_residual=gram_relative,
        state_id=_sha256_payload(_state_payload(state)),
        _construction_token=_REPORT_TOKEN,
    )


def revalidate_orbit_catalogue_v2(
    report: OrbitCatalogueV2Report,
) -> OrbitCatalogueV2Report:
    """Recompute a report from its bound state and catalogue."""

    if type(report) is not OrbitCatalogueV2Report:
        raise OrbitCatalogueV2Error(
            "report must be an exact OrbitCatalogueV2Report"
        )
    rebuilt = orbit_catalogue_v2(report.state, report.catalog)
    if rebuilt.as_payload() != report.as_payload():
        raise OrbitCatalogueV2Error(
            "orbit report fields do not match the bound state and catalogue"
        )
    return rebuilt


__all__ = [
    "CatalogueClaimStatus",
    "OrbitCatalogueV2Error",
    "OrbitCatalogueV2Report",
    "OrbitCatalogueV2Spec",
    "PR257_DEGREE_COMPLETENESS_STATUS",
    "PR257_GENERIC_SEPARATION_STATUS",
    "PR257_POLYNOMIAL_NAMES",
    "PR257_MULTIPLICITY_METHOD",
    "PR257_PARITY_BY_NAME",
    "PR257_REPRESENTATION",
    "PolynomialParity",
    "orbit_catalogue_v2",
    "revalidate_orbit_catalogue_v2",
]
