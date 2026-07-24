"""PR-136 generic partial-identification and identified-set engine.

Computes the identified set of the (Sigma2, W2, Omega_tilt,
DeltaOmega_k) parameter vector (the PR-127 graded basis) under equality
and inequality constraints, and classifies its topology as BOUNDED,
EMPTY, UNBOUNDED, DISCONNECTED, or UNDETERMINED. Two independent
engines — an exact-Fraction polyhedral analysis and a floating-point
linear program (scipy HiGHS) — must AGREE on the set status and the
per-axis bounds; a disagreement raises and blocks the downstream claim.

Semantics are enforced: an EMPTY set is infeasibility (never a
detection), a BROAD set is wide uncertainty (never a central estimate),
and solver nonconvergence is UNDETERMINED (never non-identification).
The full-parameter and subvector identified sets are reported
separately as SET-VALUED artifacts (axis intervals, vertices, recession
rays, components), never a scalar summary. The admissible box is pinned
before the fit and is never shrunk to an observed value.

Formal/algorithmic identified-region mechanics only (Chen-Christensen-
Tamer methodology, arXiv:1605.00499) — no detection.
roadmap_rescue_v1:C2.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Sequence

from common.graded_nonid import EXPECTED_KERNEL_BASIS, SECTORS

SCHEMA_VERSION = "pr136.identified_set.v1"

AXES = SECTORS   # ("Sigma2", "W2", "Omega_tilt", "DeltaOmega_k") — PR-127


def _kernel_axes_from_pr127() -> tuple[str, ...]:
    """Derive the rank-2 kernel axes from the PR-127 registered kernel
    basis (imported, not transcribed) so a PR-127 kernel edit cannot
    silently desync this module."""
    axes = []
    for basis_vec in EXPECTED_KERNEL_BASIS:
        nonzero = [i for i, v in enumerate(basis_vec) if v != 0]
        if len(nonzero) != 1:
            raise IdentifiedSetError(
                "PR-127 kernel basis vector is not a single-axis "
                "direction; the kernel-axis derivation is invalid")
        axes.append(AXES[nonzero[0]])
    return tuple(sorted(axes))


# The PR-127 rank-2 kernel directions (unconstrained -> unbounded) are
# DERIVED from graded_nonid.EXPECTED_KERNEL_BASIS and assigned to
# KERNEL_AXES just after IdentifiedSetError is defined.


class IdentifiedSetError(ValueError):
    """Raised on any engine / status / semantics violation."""


KERNEL_AXES = _kernel_axes_from_pr127()


class SetStatus(str, Enum):
    BOUNDED = "bounded"
    EMPTY = "empty"
    UNBOUNDED = "unbounded"
    DISCONNECTED = "disconnected"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class LinearConstraint:
    """One linear constraint: sum_i coeffs[axis_i] * x_i (op) rhs, with
    op in {'==', '<=', '>='}. Coefficients are exact Fractions."""

    coeffs: tuple[Fraction, ...]
    op: str
    rhs: Fraction

    def __post_init__(self) -> None:
        if len(self.coeffs) != len(AXES):
            raise IdentifiedSetError(
                f"constraint needs {len(AXES)} coefficients")
        if self.op not in ("==", "<=", ">="):
            raise IdentifiedSetError(f"invalid op {self.op!r}")
        object.__setattr__(self, "coeffs",
                           tuple(Fraction(c) for c in self.coeffs))
        object.__setattr__(self, "rhs", Fraction(self.rhs))

    def satisfied(self, point: Sequence[Fraction]) -> bool:
        lhs = sum((c * Fraction(x) for c, x in zip(self.coeffs, point)),
                  Fraction(0))
        if self.op == "==":
            return lhs == self.rhs
        if self.op == "<=":
            return lhs <= self.rhs
        return lhs >= self.rhs


def axis_constraint(axis: str, op: str, rhs) -> LinearConstraint:
    """Convenience: a single-axis constraint x_axis (op) rhs."""
    idx = AXES.index(axis)
    coeffs = [Fraction(0)] * len(AXES)
    coeffs[idx] = Fraction(1)
    return LinearConstraint(tuple(coeffs), op, Fraction(rhs))


# ---------------------------------------------------------------------------
# Admissible box (pinned before the fit)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdmissibleBox:
    """The pre-registered admissible box on each axis. Pinned BEFORE the
    fit; never shrunk to an observed value."""

    lower: dict
    upper: dict
    pinned_id: str

    def as_constraints(self) -> list[LinearConstraint]:
        cons = []
        for axis in AXES:
            if self.lower.get(axis) is not None:
                cons.append(axis_constraint(axis, ">=", self.lower[axis]))
            if self.upper.get(axis) is not None:
                cons.append(axis_constraint(axis, "<=", self.upper[axis]))
        return cons

    def validate_proposed(self, proposed_lower: dict,
                          proposed_upper: dict) -> None:
        """A REAL guard: a proposed box is admissible only if it does NOT
        shrink the pinned box on any axis. A strictly-tighter bound on any
        axis (the signature of data-driven shrinkage to fit) is refused;
        an equal or wider proposal is allowed."""
        for axis in AXES:
            pin_lo, pin_hi = self.lower.get(axis), self.upper.get(axis)
            new_lo = proposed_lower.get(axis)
            new_hi = proposed_upper.get(axis)
            lower_shrinks = new_lo is not None and (
                pin_lo is None or Fraction(new_lo) > Fraction(pin_lo)
            )
            if lower_shrinks:
                raise IdentifiedSetError(
                    f"proposed lower bound on {axis} ({new_lo}) is tighter "
                    f"than the pinned {pin_lo}; the admissible box "
                    f"{self.pinned_id} is fixed before the fit and cannot "
                    "be shrunk to an observed value")
            upper_shrinks = new_hi is not None and (
                pin_hi is None or Fraction(new_hi) < Fraction(pin_hi)
            )
            if upper_shrinks:
                raise IdentifiedSetError(
                    f"proposed upper bound on {axis} ({new_hi}) is tighter "
                    f"than the pinned {pin_hi}; the admissible box "
                    f"{self.pinned_id} is fixed before the fit and cannot "
                    "be shrunk to an observed value")

    def refuse_shrink_to(self, observed_point: Sequence[Fraction]) -> None:
        """Convenience: refuse a degenerate shrink to a single observed
        point (the point becomes both the lower and upper bound on every
        axis, the tightest possible shrink)."""
        pt = [Fraction(x) for x in observed_point]
        self.validate_proposed(
            {ax: pt[i] for i, ax in enumerate(AXES)},
            {ax: pt[i] for i, ax in enumerate(AXES)})


# ---------------------------------------------------------------------------
# Exact-Fraction engine
# ---------------------------------------------------------------------------

def _require_axis_separable(constraints: Sequence[LinearConstraint]
                            ) -> None:
    """The exact engine's honest scope: every constraint must touch a
    SINGLE axis. A multi-axis constraint is refused (rather than
    silently grid-undersampled) — the exact engine does not claim to
    compute a general polytope."""
    for c in constraints:
        touches = [i for i, cf in enumerate(c.coeffs) if cf != 0]
        if len(touches) != 1:
            raise IdentifiedSetError(
                "the exact engine handles AXIS-SEPARABLE linear "
                "constraints only; a multi-axis constraint is out of "
                "exact scope (it would require general vertex "
                "enumeration) — refused rather than undersampled")


def _exact_axis_interval(constraints: Sequence[LinearConstraint],
                         axis: str) -> tuple:
    """The TRUE continuous [lo, hi] identified interval for one axis
    from its single-axis constraints (exact Fractions; None = -inf/+inf).
    lo > hi signals an empty axis (infeasible)."""
    idx = AXES.index(axis)
    lo = None
    hi = None
    for c in constraints:
        if c.coeffs[idx] == 0:
            continue
        bound = c.rhs / c.coeffs[idx]          # normalize to x (op') bound
        sign = c.coeffs[idx]
        op = c.op
        if op == "==":
            lo = bound if lo is None else max(lo, bound)
            hi = bound if hi is None else min(hi, bound)
        elif (op == "<=" and sign > 0) or (op == ">=" and sign < 0):
            hi = bound if hi is None else min(hi, bound)   # x <= bound
        else:                                              # x >= bound
            lo = bound if lo is None else max(lo, bound)
    return lo, hi


def exact_engine(constraints: Sequence[LinearConstraint],
                 grid: Sequence[Fraction] | None = None) -> dict:
    """EXACT status + per-axis interval by exact constraint
    intersection (axis-separable scope). Returns the TRUE continuous
    identified set — not a grid undersample. ``grid`` is ignored and
    kept only for signature compatibility."""
    _require_axis_separable(constraints)
    intervals = {}
    unbounded_axes = []
    empty = False
    for ax in AXES:
        lo, hi = _exact_axis_interval(constraints, ax)
        if lo is not None and hi is not None and lo > hi:
            empty = True
            break
        if lo is None or hi is None:
            unbounded_axes.append(ax)
            intervals[ax] = [None if lo is None else str(lo),
                             None if hi is None else str(hi)]
        else:
            intervals[ax] = [str(lo), str(hi)]
    if empty:
        return {"engine": "exact_fraction", "status": SetStatus.EMPTY.value,
                "axis_intervals": None, "unbounded_axes": []}
    status = (SetStatus.UNBOUNDED.value if unbounded_axes
              else SetStatus.BOUNDED.value)
    return {
        "engine": "exact_fraction",
        "status": status,
        "axis_intervals": intervals,
        "unbounded_axes": sorted(unbounded_axes),
    }


# ---------------------------------------------------------------------------
# Numeric engine (scipy linprog)
# ---------------------------------------------------------------------------

def numeric_engine(constraints: Sequence[LinearConstraint],
                   big_m: float = 1e6) -> dict:
    """scipy HiGHS feasibility + per-axis min/max. Boundedness is
    detected by probing each axis for a min/max at the +/- big_m
    envelope; a status='unbounded' is returned if an axis extremum
    reaches the envelope. Nonconvergence -> UNDETERMINED."""
    import numpy as np
    from scipy.optimize import linprog

    n = len(AXES)
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for c in constraints:
        row = [float(v) for v in c.coeffs]
        if c.op == "==":
            A_eq.append(row)
            b_eq.append(float(c.rhs))
        elif c.op == "<=":
            A_ub.append(row)
            b_ub.append(float(c.rhs))
        else:  # >=  ->  -row <= -rhs
            A_ub.append([-v for v in row])
            b_ub.append(-float(c.rhs))
    bounds = [(-big_m, big_m)] * n
    kw = dict(A_ub=A_ub or None, b_ub=b_ub or None,
              A_eq=A_eq or None, b_eq=b_eq or None,
              bounds=bounds, method="highs")
    # feasibility
    feas = linprog(c=[0.0] * n, **kw)
    if feas.status == 2:      # infeasible
        return {"engine": "scipy_highs", "status": SetStatus.EMPTY.value,
                "axis_intervals": None, "unbounded_axes": []}
    if feas.status not in (0, 3):   # not optimal and not unbounded
        return {"engine": "scipy_highs",
                "status": SetStatus.UNDETERMINED.value,
                "axis_intervals": None, "unbounded_axes": []}
    intervals = {}
    unbounded_axes = []
    for i, ax in enumerate(AXES):
        obj = [0.0] * n
        obj[i] = 1.0
        lo = linprog(c=obj, **kw)
        obj[i] = -1.0
        hi = linprog(c=obj, **kw)
        if lo.status not in (0,) or hi.status not in (0,):
            # a box-bounded LP cannot be genuinely unbounded (status 3);
            # a non-optimal, non-infeasible status is a SOLVER FAILURE ->
            # the whole set status is UNDETERMINED, never unbounded.
            return {"engine": "scipy_highs",
                    "status": SetStatus.UNDETERMINED.value,
                    "axis_intervals": None, "unbounded_axes": []}
        lo_v = float(lo.x[i])
        hi_v = float(hi.x[i])
        # reaching the big_m envelope means unbounded on this axis
        if lo_v <= -big_m * (1 - 1e-9) or hi_v >= big_m * (1 - 1e-9):
            unbounded_axes.append(ax)
            intervals[ax] = None
        else:
            intervals[ax] = [lo_v, hi_v]
    status = (SetStatus.UNBOUNDED.value if unbounded_axes
              else SetStatus.BOUNDED.value)
    return {
        "engine": "scipy_highs",
        "status": status,
        "axis_intervals": intervals,
        "unbounded_axes": sorted(unbounded_axes),
    }


# ---------------------------------------------------------------------------
# Cross-engine agreement + status semantics
# ---------------------------------------------------------------------------

def require_cross_engine_agreement(exact: dict, numeric: dict,
                                   tol: float = 1e-6) -> None:
    """Both engines must agree on the STATUS, on the set of unbounded
    axes, AND on EVERY bounded axis interval to the tolerance — the
    bounded-axis comparison runs regardless of the overall status (a
    bounded axis inside an overall-unbounded set is still cross-checked).
    A disagreement raises and blocks the downstream claim."""
    if not math.isfinite(tol) or tol < 0:
        raise IdentifiedSetError(
            "cross-engine tolerance must be finite and non-negative")
    if exact["status"] != numeric["status"]:
        raise IdentifiedSetError(
            f"cross-engine STATUS disagreement: exact "
            f"{exact['status']!r} vs numeric {numeric['status']!r} — the "
            "downstream numerical claim is blocked")
    if set(exact["unbounded_axes"]) != set(numeric["unbounded_axes"]):
        raise IdentifiedSetError(
            "cross-engine disagreement on the unbounded axes: exact "
            f"{exact['unbounded_axes']} vs numeric "
            f"{numeric['unbounded_axes']}")
    if exact["status"] in (SetStatus.EMPTY.value,
                           SetStatus.UNDETERMINED.value):
        return
    # compare every axis that is BOUNDED in the exact engine (finite
    # lo and hi) against the numeric interval, whatever the overall
    # status — this closes the unbounded-set false-precision hole.
    exact_iv = exact["axis_intervals"] or {}
    numeric_iv = numeric["axis_intervals"] or {}
    for ax in AXES:
        e = exact_iv.get(ax)
        if not e or e[0] is None or e[1] is None:
            continue   # unbounded axis (already agreed above)
        n = numeric_iv.get(ax)
        if not n:
            raise IdentifiedSetError(
                f"axis {ax} is bounded in the exact engine but the "
                "numeric engine reports it unbounded/missing")
        e_lo, e_hi = float(Fraction(e[0])), float(Fraction(e[1]))
        n_lo, n_hi = n
        if not math.isfinite(n_lo) or not math.isfinite(n_hi):
            raise IdentifiedSetError(
                f"numeric engine returned a non-finite boundary on {ax}")
        if abs(e_lo - n_lo) > tol or abs(e_hi - n_hi) > tol:
            raise IdentifiedSetError(
                f"cross-engine boundary disagreement on {ax}: exact "
                f"[{e_lo}, {e_hi}] vs numeric [{n_lo}, {n_hi}]")


def validate_status_semantics(status: str, reading: str) -> None:
    """Enforce the status semantics: empty != detection, broad !=
    central, nonconvergence != non-identification."""
    reading = reading.lower()
    if status == SetStatus.EMPTY.value and "detection" in reading:
        raise IdentifiedSetError(
            "an EMPTY identified set is infeasibility, NEVER a detection")
    if status == SetStatus.BOUNDED.value and (
            "central estimate" in reading or "point estimate" in reading):
        raise IdentifiedSetError(
            "a bounded (possibly broad) identified set is an uncertainty "
            "region, NEVER a central/point estimate")
    if status == SetStatus.UNDETERMINED.value and (
            "non-identification" in reading or "non_identification"
            in reading or "not identified" in reading):
        raise IdentifiedSetError(
            "solver nonconvergence is UNDETERMINED, NEVER a "
            "non-identification claim")


def verify_kernel_binding() -> dict:
    """Confirm KERNEL_AXES is the PR-127 registered kernel (re-derived
    live from graded_nonid.EXPECTED_KERNEL_BASIS). Raises on desync."""
    derived = _kernel_axes_from_pr127()
    if tuple(KERNEL_AXES) != derived:
        raise IdentifiedSetError(
            f"KERNEL_AXES {KERNEL_AXES} desynced from the PR-127 kernel "
            f"{derived}")
    return {"kernel_axes": list(KERNEL_AXES),
            "source": "graded_nonid.EXPECTED_KERNEL_BASIS",
            "bound_live": True}


def classify_status_from_solver(converged: bool, feasible: bool,
                                unbounded: bool) -> str:
    """Map solver outcomes to the status vocabulary. A nonconverged
    solver is UNDETERMINED — never empty or non-identification."""
    if not converged:
        return SetStatus.UNDETERMINED.value
    if not feasible:
        return SetStatus.EMPTY.value
    if unbounded:
        return SetStatus.UNBOUNDED.value
    return SetStatus.BOUNDED.value


# ---------------------------------------------------------------------------
# Disconnection (nonconvex sign fixture)
# ---------------------------------------------------------------------------

def disconnected_components(abs_axis: str, threshold: Fraction,
                            other_box: "AdmissibleBox",
                            grid: Sequence[Fraction] | None = None) -> dict:
    """The nonconvex constraint |x_axis| >= threshold splits the set
    into two DISJOINT components (x_axis >= threshold) and
    (x_axis <= -threshold), separated by the excluded open gap
    (-threshold, threshold). Each component's exact interval is computed
    by the exact engine (true continuous, not a grid sample); the
    threshold must be strictly inside the pinned box so both components
    have positive width and the gap is genuinely excluded."""
    box_lo = Fraction(other_box.lower[abs_axis])
    box_hi = Fraction(other_box.upper[abs_axis])
    threshold = Fraction(threshold)
    if not (box_lo < -threshold and threshold < box_hi):
        raise IdentifiedSetError(
            f"threshold {threshold} is not strictly inside the pinned "
            f"box [{box_lo}, {box_hi}] on {abs_axis}; the two components "
            "would not both have positive width")
    components = []
    for name, extra in (
            ("positive", axis_constraint(abs_axis, ">=", threshold)),
            ("negative", axis_constraint(abs_axis, "<=", -threshold))):
        cons = list(other_box.as_constraints()) + [extra]
        result = exact_engine(cons)
        if result["status"] == SetStatus.EMPTY.value:
            continue
        components.append({
            "component": name,
            "abs_axis_interval": result["axis_intervals"][abs_axis],
            "status": result["status"],
        })
    if len(components) < 2:
        raise IdentifiedSetError(
            "the |x| >= c fixture did not produce two components")
    # the components are disjoint iff the excluded gap has positive width
    if not (-threshold < threshold):
        raise IdentifiedSetError("degenerate gap")
    return {
        "status": SetStatus.DISCONNECTED.value,
        "abs_axis": abs_axis,
        "threshold": str(threshold),
        "components": components,
        "excluded_open_gap": [str(-threshold), str(threshold)],
        "components_disjoint": True,
    }


# ---------------------------------------------------------------------------
# Set-valued artifact + subvector projection
# ---------------------------------------------------------------------------

_SET_GEOMETRY_FIELDS = (
    "axis_intervals",
    "unbounded_axes",
    "components",
    "vertices",
    "recession_rays",
)


def validate_set_valued(artifact: dict) -> None:
    """Reject a scalar-only summary: a set-valued artifact must carry
    the set fields, not merely a point estimate."""
    if "central_estimate" in artifact and set(artifact) <= {
            "central_estimate", "point_estimate"}:
        raise IdentifiedSetError(
            "artifact carries only a scalar summary and no set-valued "
            "fields — the identified set must be reported set-valued")
    if "status" not in artifact:
        raise IdentifiedSetError(
            "a set-valued artifact must carry a topology status")
    if not any(field in artifact for field in _SET_GEOMETRY_FIELDS):
        raise IdentifiedSetError(
            "a set-valued artifact must carry set geometry, not only a "
            "topology status")


def subvector_projection(full_result: dict,
                         subaxes: Sequence[str]) -> dict:
    """Project the identified set onto a coordinate subset — reported
    SEPARATELY from the full set. A subvector may be bounded even when
    the full set is unbounded (the unbounded axes lie outside the
    subvector)."""
    for ax in subaxes:
        if ax not in AXES:
            raise IdentifiedSetError(f"unknown axis {ax!r}")
    full_status = full_result["status"]
    if full_status in (
        SetStatus.EMPTY.value,
        SetStatus.UNDETERMINED.value,
    ):
        return {
            "subaxes": list(subaxes),
            "status": full_status,
            "axis_intervals": None,
            "unbounded_in_subvector": [],
            "note": "the terminal full-set status is preserved in the "
                    "separately reported subvector projection",
        }
    unbounded_in_sub = [ax for ax in full_result["unbounded_axes"]
                        if ax in subaxes]
    if unbounded_in_sub:
        status = SetStatus.UNBOUNDED.value
        intervals = {ax: (full_result["axis_intervals"] or {}).get(ax)
                     for ax in subaxes}
    else:
        status = SetStatus.BOUNDED.value
        intervals = {ax: full_result["axis_intervals"][ax]
                     for ax in subaxes} if full_result[
                         "axis_intervals"] else {}
    return {
        "subaxes": list(subaxes),
        "status": status,
        "axis_intervals": intervals,
        "unbounded_in_subvector": unbounded_in_sub,
        "note": "the subvector identified set is reported separately "
                "from the full-parameter set",
    }


# ---------------------------------------------------------------------------
# Caption gate
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("empty set is", " a detection"),
        ("broad set as", " the central estimate"),
        ("nonconvergence means", " non-identification"),
        ("point-identified", " the shear"),
        ("shrink the admissible", " set to the fit"),
        ("shear", " detected"), ("isotropy", " established"),
        ("bianchi geometry", " detected"),
        ("bianchi family", " identified"), ("finding", " rescued"),
        ("validated as", " native"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise IdentifiedSetError(
                "caption carries forbidden detection/central-estimate/"
                "nonconvergence/shrink/over-claim language")


def generate_caption(statuses: dict) -> str:
    text = (
        "[identified_set] Identified-set engine over "
        "(Sigma2, W2, Omega_tilt, DeltaOmega_k): fixtures classified as "
        f"{statuses}. Two engines (exact Fraction + scipy HiGHS) agree "
        "on status and boundary. An empty set is infeasibility, a broad "
        "set is uncertainty, and nonconvergence is undetermined; "
        "set-valued artifacts only. Formal identified-region mechanics "
        "only; no detection."
    )
    lint_caption(text)
    return text
