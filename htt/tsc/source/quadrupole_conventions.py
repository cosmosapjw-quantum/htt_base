"""Quadrupole-convention registry for TSC trace-source artifacts."""
from __future__ import annotations

from dataclasses import dataclass

from common.contracts import QuadrupoleConvention, QuadrupoleParameterName


@dataclass(frozen=True)
class QuadrupoleConventionMetadata:
    """Frozen metadata describing one supported quadrupole convention."""

    convention: QuadrupoleConvention
    quadrupole_parameter_name: QuadrupoleParameterName
    conversion_to_legendre_q: float


_REGISTRY: dict[QuadrupoleConvention, QuadrupoleConventionMetadata] = {
    "mu2_minus_one_third": QuadrupoleConventionMetadata(
        convention="mu2_minus_one_third",
        quadrupole_parameter_name="Q_mu",
        conversion_to_legendre_q=2.0 / 3.0,
    ),
    "legendre_P2": QuadrupoleConventionMetadata(
        convention="legendre_P2",
        quadrupole_parameter_name="q",
        conversion_to_legendre_q=1.0,
    ),
}


def quadrupole_convention_metadata(
    convention: QuadrupoleConvention,
) -> QuadrupoleConventionMetadata:
    """Return the frozen metadata for one supported convention."""
    try:
        return _REGISTRY[convention]
    except KeyError as exc:
        raise ValueError(f"unsupported quadrupole convention {convention!r}") from exc


def to_legendre_q(
    quadrupole_parameter: float,
    convention: QuadrupoleConvention,
) -> float:
    """Convert a quadrupole parameter into the Legendre ``q`` convention."""
    metadata = quadrupole_convention_metadata(convention)
    return float(quadrupole_parameter) * metadata.conversion_to_legendre_q


def from_legendre_q(
    q: float,
    convention: QuadrupoleConvention,
) -> float:
    """Convert a Legendre-``q`` parameter into the requested convention."""
    metadata = quadrupole_convention_metadata(convention)
    return float(q) / metadata.conversion_to_legendre_q


def linear_intensity_quadrupole_from_parameter(
    quadrupole_parameter: float,
    convention: QuadrupoleConvention,
) -> float:
    """Return the linearized intensity quadrupole coefficient ``I_2``.

    In the Legendre convention ``Theta = 1 + A mu + q P_2(mu)``, the
    linearized intensity quadrupole is ``4 q``. In the alternate
    ``Q_mu (mu^2 - 1/3)`` convention, ``q = 2 Q_mu / 3`` and the same
    physical value becomes ``8 Q_mu / 3``.
    """
    return 4.0 * to_legendre_q(quadrupole_parameter, convention)


__all__ = [
    "QuadrupoleConventionMetadata",
    "from_legendre_q",
    "linear_intensity_quadrupole_from_parameter",
    "quadrupole_convention_metadata",
    "to_legendre_q",
]
