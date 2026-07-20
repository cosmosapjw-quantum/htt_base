"""Exact PR-171 class-conditional tilt mechanics and fail-closed routing."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any


class TiltRelaxationError(ValueError):
    """Raised when a PR-171 domain or promotion guard is violated."""


@dataclass(frozen=True)
class LinearTiltSystem:
    alpha: Fraction
    beta: Fraction
    kappa: Fraction
    lam: Fraction

    def __post_init__(self) -> None:
        if self.alpha <= 0 or self.beta <= 0:
            raise TiltRelaxationError("alpha and beta must be positive")

    @property
    def trace(self) -> Fraction:
        return -(self.alpha + self.beta)

    @property
    def determinant(self) -> Fraction:
        return self.alpha * self.beta - self.kappa * self.lam

    @property
    def characteristic_coefficients(self) -> tuple[Fraction, Fraction, Fraction]:
        return (Fraction(1), self.alpha + self.beta, self.determinant)

    @property
    def strictly_stable(self) -> bool:
        return self.trace < 0 and self.determinant > 0


@dataclass(frozen=True)
class DragTiltSystem:
    """Frozen near-FLRW two-fluid linear drag model."""

    a: Fraction
    x: Fraction
    y: Fraction

    def __post_init__(self) -> None:
        if self.a <= 0 or self.x < 0 or self.y < 0:
            raise TiltRelaxationError("require a>0 and x,y>=0")

    @property
    def trace(self) -> Fraction:
        return -(self.a + self.x + self.y + 1)

    @property
    def determinant(self) -> Fraction:
        return self.a * (1 + self.y) + self.x

    @property
    def characteristic_coefficients(self) -> tuple[Fraction, Fraction, Fraction]:
        return (Fraction(1), self.a + self.x + self.y + 1, self.determinant)

    @property
    def strictly_stable(self) -> bool:
        return self.trace < 0 and self.determinant > 0


def rw_velocity_rhs(v: Fraction, w: Fraction) -> Fraction:
    """Return dv/dN in the frozen flat-RW, constant-w source class."""

    if not -1 < w < Fraction(1, 3):
        raise TiltRelaxationError("w must satisfy -1 < w < 1/3")
    if abs(v) >= 1:
        raise TiltRelaxationError("speed must satisfy abs(v) < 1")
    denominator = 1 - w * v * v
    if denominator <= 0:
        raise TiltRelaxationError("RW denominator is not positive")
    return (1 - v * v) * (3 * w - 1) * v / denominator


def rw_relaxation_sign(v: Fraction, w: Fraction) -> bool:
    """Check the exact Lyapunov sign v*dv/dN<0 away from equilibrium."""

    if v == 0:
        raise TiltRelaxationError("sign witness requires nonzero tilt")
    return v * rw_velocity_rhs(v, w) < 0


def phenomenological_alpha(w: Fraction, g: Fraction) -> Fraction:
    if not -1 < w < Fraction(1, 3):
        raise TiltRelaxationError("w must satisfy -1 < w < 1/3")
    if g < 0:
        raise TiltRelaxationError("g=Gamma/H must be nonnegative")
    return 1 - 3 * w + g


def source_counterexample_fixture() -> dict[str, Any]:
    gamma = Fraction(5, 4)
    w = gamma - 1
    return {
        "gamma": str(gamma),
        "w": str(w),
        "Gamma": "0",
        "w_less_than_one_third": w < Fraction(1, 3),
        "Gamma_nonnegative": True,
        "sound_speed_squared": str(w),
        "weak_energy_condition": w >= -1,
        "dominant_energy_condition": abs(w) <= 1,
        "source_asymptotic_result": "GENERIC_EXTREME_TILT",
        "blanket_no_go_disposition": "RETIRED_BY_PUBLISHED_COUNTEREXAMPLE",
    }


def suppression_functional(
    *, w: Fraction, g: Fraction, delta_n: Fraction | None
) -> dict[str, Any]:
    """Describe, but do not invent, the linear suppression functional."""

    alpha = phenomenological_alpha(w, g)
    if delta_n is None:
        return {
            "status": "SUPPRESSION_CEILING_NOT_IDENTIFIED",
            "alpha": str(alpha),
            "value": None,
            "missing_inputs": ["N_f-N_i"],
        }
    if delta_n < 0:
        raise TiltRelaxationError("future interval requires delta_n >= 0")
    return {
        "status": "SYMBOLIC_ONLY",
        "alpha": str(alpha),
        "value": f"exp(-({alpha})*({delta_n}))",
        "missing_inputs": [],
    }


def route_terminal_result(
    cas_status: str,
    *,
    provenance_ok: bool,
    counterexample_gate: bool,
    source_space_closed: bool,
) -> dict[str, Any]:
    if not provenance_ok:
        return _route("FAIL", "none", None, "NOT_ESTABLISHED")
    if cas_status == "CAS_BLOCKED":
        return _route("BLOCKED", "source_provenance_audit_only", None, "WITHHELD_CAS_BLOCKED")
    if cas_status == "CAS_CONFLICT":
        return _route("BLOCKED", "conflict_receipt_only", None, "WITHHELD_CAS_CONFLICT")
    if cas_status == "CAS_FAIL":
        return _route("FAIL", "failed_registered_exact_target", None, "NOT_ESTABLISHED")
    if cas_status != "CAS_4AXIS_PASS":
        raise TiltRelaxationError(f"unknown CAS status: {cas_status}")
    if counterexample_gate:
        return _route(
            "PASS",
            "CLASS_CONDITIONAL_NO_GO_RETIRED_BY_COUNTEREXAMPLE",
            None,
            "RETIRED",
        )
    if not source_space_closed:
        return _route("PASS", "algebraic_only_or_non_informative", None, "NO_CLASS_WIDE_NO_GO")
    return _route("PASS", "CLASS_CONDITIONAL_STABILITY", "FROZEN_INPUTS_REQUIRED", "FROZEN_CLASS_ONLY")


def _route(process: str, result: str, suppression: str | None, disposition: str) -> dict[str, Any]:
    return {
        "process_gate_status": process,
        "scientific_result": result,
        "suppression_result": suppression,
        "candidate_disposition": disposition,
        "public_use": False,
    }
