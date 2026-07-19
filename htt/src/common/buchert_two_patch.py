"""Exact PR-170 Buchert and two-patch scalar algebra.

This COMMON module implements externally attributed scalar identities over
``fractions.Fraction``.  It does not construct a Bianchi spacetime, solve the
Einstein equations, or certify physical patch matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final, Mapping


Rational = Fraction

BIANCHI_TYPES: Final[tuple[str, ...]] = (
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI_0",
    "VI_h",
    "VII_0",
    "VII_h",
    "VIII",
    "IX",
)

# This registry is a provenance gate, not a numerical BASS result.  Only the
# exact external constructions authenticated by PR-170 receive a PASS.
TYPE_CURVATURE_PROVENANCE: Final[Mapping[str, str]] = {
    "I": "INTERNAL_EXACT_DEFINITIONAL_FLAT_THREE_CURVATURE",
    "II": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "III": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "IV": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "V": "PASS_ISOTROPIC_THREE_CURVATURE_REGISTERED_CONSTRUCTION",
    "VI_0": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "VI_h": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "VII_0": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "VII_h": "UNRESOLVED_GENERIC_TRACEFREE_CURVATURE_CONTRACTION",
    "VIII": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
    "IX": "UNRESOLVED_EXTERNAL_TYPE_BRIDGE",
}


def _q(value: int | str | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _weight(weight: int | str | Fraction) -> Fraction:
    value = _q(weight)
    if not Fraction(0) < value < Fraction(1):
        raise ValueError("two-patch volume weight must satisfy 0 < lambda < 1")
    return value


@dataclass(frozen=True)
class TwoPatchState:
    """Exact scalar state for two disjoint patches on one declared slice."""

    volume_weight_1: Fraction
    hubble_1: Fraction
    hubble_2: Fraction
    shear_sq_1: Fraction
    shear_sq_2: Fraction

    def __post_init__(self) -> None:
        weight = _weight(self.volume_weight_1)
        values = tuple(
            _q(value)
            for value in (
                self.hubble_1,
                self.hubble_2,
                self.shear_sq_1,
                self.shear_sq_2,
            )
        )
        if values[2] < 0 or values[3] < 0:
            raise ValueError("squared shear must be nonnegative")
        object.__setattr__(self, "volume_weight_1", weight)
        object.__setattr__(self, "hubble_1", values[0])
        object.__setattr__(self, "hubble_2", values[1])
        object.__setattr__(self, "shear_sq_1", values[2])
        object.__setattr__(self, "shear_sq_2", values[3])

    @property
    def volume_weight_2(self) -> Fraction:
        return Fraction(1) - self.volume_weight_1

    @property
    def hubble_domain(self) -> Fraction:
        return (
            self.volume_weight_1 * self.hubble_1
            + self.volume_weight_2 * self.hubble_2
        )

    @property
    def expansion_variance(self) -> Fraction:
        """Domain variance of theta=3H for patchwise-constant expansion."""

        return (
            9
            * self.volume_weight_1
            * self.volume_weight_2
            * (self.hubble_1 - self.hubble_2) ** 2
        )

    @property
    def mean_shear_sq(self) -> Fraction:
        return (
            self.volume_weight_1 * self.shear_sq_1
            + self.volume_weight_2 * self.shear_sq_2
        )

    @property
    def q_buchert(self) -> Fraction:
        return Fraction(2, 3) * self.expansion_variance - 2 * self.mean_shear_sq

    def _normalization(self) -> Fraction:
        if self.hubble_domain == 0:
            raise ZeroDivisionError("H_D=0: normalized Buchert coordinates undefined")
        return self.hubble_domain**2

    @property
    def omega_q_buchert(self) -> Fraction:
        return -self.q_buchert / (6 * self._normalization())

    @property
    def sigma2_domain_rms(self) -> Fraction:
        # sigma_sq=(1/2)sigma_ab sigma^ab, hence this equals
        # <sigma_ab sigma^ab>/(6 H_D^2).
        return self.mean_shear_sq / (3 * self._normalization())

    @property
    def bridge_residual(self) -> Fraction:
        return self.omega_q_buchert - self.sigma2_domain_rms

    @property
    def expected_bridge_residual(self) -> Fraction:
        return -self.expansion_variance / (9 * self._normalization())

    @property
    def cancellation_residual(self) -> Fraction:
        return self.expansion_variance - 3 * self.mean_shear_sq

    def swapped(self) -> "TwoPatchState":
        return TwoPatchState(
            self.volume_weight_2,
            self.hubble_2,
            self.hubble_1,
            self.shear_sq_2,
            self.shear_sq_1,
        )

    def exact_record(self) -> dict[str, str]:
        values = {
            "lambda_1": self.volume_weight_1,
            "lambda_2": self.volume_weight_2,
            "H_D": self.hubble_domain,
            "expansion_variance": self.expansion_variance,
            "mean_sigma_sq": self.mean_shear_sq,
            "Q_D_B": self.q_buchert,
            "Omega_Q_D_B": self.omega_q_buchert,
            "Sigma2_D_rms": self.sigma2_domain_rms,
            "bridge_residual": self.bridge_residual,
            "expected_bridge_residual": self.expected_bridge_residual,
            "cancellation_residual": self.cancellation_residual,
        }
        return {key: canonical_rational(value) for key, value in values.items()}


def canonical_rational(value: Fraction) -> str:
    value = _q(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def barrow_tsagas_residual_q(
    expansion_variance: Fraction,
    mean_sigma_sq: Fraction,
    mean_sigma: Fraction,
) -> Fraction:
    """Typed Barrow--Tsagas residual Q, distinct from Buchert total Q."""

    mean_sigma_sq = _q(mean_sigma_sq)
    mean_sigma = _q(mean_sigma)
    if mean_sigma < 0 or mean_sigma_sq < mean_sigma**2:
        raise ValueError(
            "shear moments must satisfy mean_sigma >= 0 and "
            "mean_sigma_sq >= mean_sigma^2"
        )
    variance_sigma = mean_sigma_sq - mean_sigma**2
    return Fraction(2, 3) * _q(expansion_variance) - 2 * variance_sigma


def buchert_total_q(expansion_variance: Fraction, mean_sigma_sq: Fraction) -> Fraction:
    return Fraction(2, 3) * _q(expansion_variance) - 2 * _q(mean_sigma_sq)


def external_type_closure_summary() -> dict[str, object]:
    externally_authenticated = tuple(
        type_id
        for type_id in BIANCHI_TYPES
        if TYPE_CURVATURE_PROVENANCE[type_id].startswith("PASS_")
    )
    internal_exact = tuple(
        type_id
        for type_id in BIANCHI_TYPES
        if TYPE_CURVATURE_PROVENANCE[type_id].startswith("INTERNAL_EXACT_")
    )
    resolved = externally_authenticated + internal_exact
    unresolved = tuple(type_id for type_id in BIANCHI_TYPES if type_id not in resolved)
    return {
        "registered_type_count": len(BIANCHI_TYPES),
        "resolved_type_count": len(resolved),
        "unresolved_type_count": len(unresolved),
        "resolved_types": resolved,
        "unresolved_types": unresolved,
        "externally_authenticated_type_count": len(externally_authenticated),
        "externally_authenticated_types": externally_authenticated,
        "internal_exact_type_count": len(internal_exact),
        "internal_exact_types": internal_exact,
        "all_types_externally_closed": not unresolved,
    }
