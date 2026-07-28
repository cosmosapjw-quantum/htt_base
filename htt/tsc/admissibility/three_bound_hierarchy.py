"""
tsc/admissibility/three_bound_hierarchy.py  (TSC-03, Week 7)
=============================================================

Independent (from ``htt``) derivation of the MES three-bound hierarchy

    B_sigma  >  B_omega  >  B_accel       (Maartens-Ellis-Stoeger 1995,
                                           Paper II, Theorem 3.4)

together with the induced hierarchy on the MES ceilings

    Sigma2_max  >  W2_max  >  A2_max,     Sigma2_max = (3/2) B_sigma^2,
                                          W2_max     = (3/2) B_omega^2,
                                          A2_max     = (3/2) B_accel^2,

and a type-by-type evaluation for the nine Bianchi classes we work with
in the manuscript (I, II, V, VI_0, VII_0, VIII, IX, VII_h, III).

Role
----
TSC-03 is the *tsc-side* re-derivation of the bounds enumerated in
``tsc_legacy.htt_core_bounds``; the two legacy implementations must agree to
``rtol = 1e-10`` on arbitrary (eps1, eps2, eps3) triples. The
cross-check anchor ``test_three_bound_hierarchy_matches_htt_bounds``
asserts this agreement and fires the TSC-03 regression gate listed in
`INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Days 1-2.

Why re-derive independently
---------------------------
The MES bounds collapse a chain of closed-form Clebsch-Gordan /
Legendre-orthogonality manipulations into three rational-coefficient
linear combinations of (eps1, eps2, eps3). Stating them in two places
with two different authors and asserting bit-identity is the
epistemic anchor: any future drift in either side would have to
re-prove Theorem 3.4 first.

Public API
----------
* :data:`BIANCHI_TYPES` --- 9-entry SSOT tuple naming the Bianchi
  types this module covers.
* :data:`COEFFS` --- SSOT rational coefficients (tuple-of-Fractions)
  for B_sigma, B_omega, B_accel. Consumers can introspect exactness.
* :func:`B_sigma`, :func:`B_omega`, :func:`B_accel` --- scalar
  evaluators; no htt dependency.
* :func:`Sigma2_max`, :func:`W2_max`, :func:`A2_max` --- the induced
  MES ceilings.
* :class:`ThreeBoundReport` --- frozen dataclass carrying bounds,
  ceilings, hierarchy flag, type label, provenance.
* :func:`compute_three_bound_hierarchy(eps1, eps2, eps3, *,
  type_name=None, strict=True)` --- core evaluator; raises
  ``ValueError`` on hierarchy violation when ``strict=True``.
* :func:`evaluate_all_bianchi_types(eps1, eps2, eps3)` --- dict keyed
  by Bianchi type, values are :class:`ThreeBoundReport` instances.
* :func:`compare_against_htt_bounds(eps1, eps2, eps3, *, rtol=1e-10)`
  --- integration helper used by the cross-check test.

All functions are pure; no I/O, no global state.

References
----------
Maartens, Ellis, & Stoeger (1995). ApJ 453, 545.  Theorems 3.1-3.4.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping

import numpy as np

__all__ = [
    "BIANCHI_TYPES",
    "COEFFS",
    "B_sigma",
    "B_omega",
    "B_accel",
    "Sigma2_max",
    "W2_max",
    "A2_max",
    "ThreeBoundReport",
    "compute_three_bound_hierarchy",
    "evaluate_all_bianchi_types",
    "compare_against_htt_bounds",
    "HierarchyViolationError",
]


# ---------------------------------------------------------------------------
# SSOT: Bianchi type roster + rational MES coefficients
# ---------------------------------------------------------------------------

#: Nine Bianchi classes covered by the TSC-03 hierarchy check.
#: Matches ``tsc_legacy.htt_core_bounds._TYPE_INFO`` keys (up to ordering).
BIANCHI_TYPES: tuple[str, ...] = (
    "I", "II", "V", "VI0", "VII0", "VIII", "IX", "VIIh", "III",
)


def _F(num: int, den: int) -> Fraction:
    return Fraction(num, den)


#: Rational coefficients for (eps1, eps2, eps3) in the three bound
#: combinations. Kept as ``Fraction`` tuples so downstream audits can
#: assert exactness without hitting float round-off.
COEFFS: Mapping[str, tuple[Fraction, Fraction, Fraction]] = {
    # B_sigma = (5/3) eps1 + 3 eps2 + (3/7) eps3       (Thm 3.1, Eq. 3.7)
    "sigma": (_F(5, 3), _F(3, 1), _F(3, 7)),
    # B_omega = (3/4) eps1 + 2 eps2 + (2/7) eps3       (Thm 3.2, Eq. 3.12)
    "omega": (_F(3, 4), _F(2, 1), _F(2, 7)),
    # B_accel = (3/4) eps1 +   eps2 + (3/14) eps3      (Thm 3.3, Eq. 3.15)
    "accel": (_F(3, 4), _F(1, 1), _F(3, 14)),
}


# ---------------------------------------------------------------------------
# Exception type
# ---------------------------------------------------------------------------


class HierarchyViolationError(ValueError):
    """Raised when ``B_sigma > B_omega > B_accel`` is not satisfied.

    Subclass of :class:`ValueError` so existing `except ValueError`
    guards continue to work.
    """


# ---------------------------------------------------------------------------
# Scalar bound evaluators
# ---------------------------------------------------------------------------


def _as_float(x: Fraction) -> float:
    return float(x.numerator) / float(x.denominator)


def _evaluate(coef: tuple[Fraction, Fraction, Fraction],
              e1: float, e2: float, e3: float) -> float:
    c1, c2, c3 = coef
    return _as_float(c1) * e1 + _as_float(c2) * e2 + _as_float(c3) * e3


def B_sigma(eps1: float, eps2: float, eps3: float) -> float:
    """MES shear bound: (5/3) eps1 + 3 eps2 + (3/7) eps3."""
    _validate_epsilons(eps1, eps2, eps3)
    return _evaluate(COEFFS["sigma"], eps1, eps2, eps3)


def B_omega(eps1: float, eps2: float, eps3: float) -> float:
    """MES vorticity bound: (3/4) eps1 + 2 eps2 + (2/7) eps3."""
    _validate_epsilons(eps1, eps2, eps3)
    return _evaluate(COEFFS["omega"], eps1, eps2, eps3)


def B_accel(eps1: float, eps2: float, eps3: float) -> float:
    """MES four-acceleration bound: (3/4) eps1 + eps2 + (3/14) eps3."""
    _validate_epsilons(eps1, eps2, eps3)
    return _evaluate(COEFFS["accel"], eps1, eps2, eps3)


def Sigma2_max(eps1: float, eps2: float, eps3: float) -> float:
    """Shear MES ceiling: (3/2) B_sigma^2."""
    b = B_sigma(eps1, eps2, eps3)
    return 1.5 * b * b


def W2_max(eps1: float, eps2: float, eps3: float) -> float:
    """Vorticity MES ceiling: (3/2) B_omega^2."""
    b = B_omega(eps1, eps2, eps3)
    return 1.5 * b * b


def A2_max(eps1: float, eps2: float, eps3: float) -> float:
    """Acceleration MES ceiling: (3/2) B_accel^2."""
    b = B_accel(eps1, eps2, eps3)
    return 1.5 * b * b


def _validate_epsilons(eps1: float, eps2: float, eps3: float) -> None:
    for name, val in (("eps1", eps1), ("eps2", eps2), ("eps3", eps3)):
        v = float(val)
        if not np.isfinite(v):
            raise ValueError(f"{name} must be finite; got {val}")
        if v < 0.0:
            raise ValueError(f"{name} must be >= 0; got {val}")


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ThreeBoundReport:
    """Bundle of MES bounds, ceilings, hierarchy flag, provenance.

    Attributes
    ----------
    type_name
        Bianchi classification label (member of :data:`BIANCHI_TYPES`)
        or ``"generic"`` when no type is pinned.
    eps1, eps2, eps3
        Temperature-anisotropy amplitudes used to evaluate the bounds
        (dimensionless ΔT/T_0). All non-negative.
    B_sigma_val, B_omega_val, B_accel_val
        Scalar bounds.
    Sigma2_max_val, W2_max_val, A2_max_val
        Derived MES ceilings ``(3/2) B_X^2``.
    ratio_omega_over_sigma
        ``B_omega / B_sigma`` (strict hierarchy requires < 1).
    ratio_accel_over_omega
        ``B_accel / B_omega`` (strict hierarchy requires < 1).
    hierarchy_strict
        ``True`` iff ``B_sigma > B_omega > B_accel`` strictly (the
        threshold for the hierarchy check; ``rtol`` handled elsewhere).
    config
        Echo of the evaluation context (caller, coefficient source,
        strict/soft mode, etc.). Present for provenance; not used
        in the hierarchy decision.
    """

    type_name: str
    eps1: float
    eps2: float
    eps3: float
    B_sigma_val: float
    B_omega_val: float
    B_accel_val: float
    Sigma2_max_val: float
    W2_max_val: float
    A2_max_val: float
    ratio_omega_over_sigma: float
    ratio_accel_over_omega: float
    hierarchy_strict: bool
    config: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialisable dict view (floats + plain types only)."""
        return {
            "type_name": str(self.type_name),
            "eps1": float(self.eps1),
            "eps2": float(self.eps2),
            "eps3": float(self.eps3),
            "B_sigma": float(self.B_sigma_val),
            "B_omega": float(self.B_omega_val),
            "B_accel": float(self.B_accel_val),
            "Sigma2_max": float(self.Sigma2_max_val),
            "W2_max": float(self.W2_max_val),
            "A2_max": float(self.A2_max_val),
            "ratio_omega_over_sigma": float(self.ratio_omega_over_sigma),
            "ratio_accel_over_omega": float(self.ratio_accel_over_omega),
            "hierarchy_strict": bool(self.hierarchy_strict),
            "config": {str(k): v for k, v in self.config.items()},
        }


# ---------------------------------------------------------------------------
# Core evaluator
# ---------------------------------------------------------------------------


def compute_three_bound_hierarchy(
    eps1: float,
    eps2: float,
    eps3: float,
    *,
    type_name: str | None = None,
    strict: bool = True,
) -> ThreeBoundReport:
    """Compute the three-bound hierarchy at fixed (eps1, eps2, eps3).

    Parameters
    ----------
    eps1, eps2, eps3
        Dimensionless temperature-anisotropy amplitudes. All must be
        finite and non-negative.
    type_name
        Optional Bianchi classification label. If supplied, must be a
        member of :data:`BIANCHI_TYPES`. Defaults to ``"generic"``.
    strict
        When ``True`` (default), a hierarchy violation raises
        :class:`HierarchyViolationError`. When ``False``, the report
        is returned with ``hierarchy_strict=False`` and no exception.

    Returns
    -------
    ThreeBoundReport
    """
    if type_name is None:
        label = "generic"
    else:
        if type_name not in BIANCHI_TYPES:
            raise ValueError(
                f"type_name {type_name!r} not in BIANCHI_TYPES "
                f"{BIANCHI_TYPES}"
            )
        label = type_name

    bs = B_sigma(eps1, eps2, eps3)
    bo = B_omega(eps1, eps2, eps3)
    ba = B_accel(eps1, eps2, eps3)

    hierarchy_ok = (bs > bo) and (bo > ba)

    # Guard against divide-by-zero when eps = 0 everywhere.
    ratio_omega_over_sigma = (bo / bs) if bs > 0.0 else float("nan")
    ratio_accel_over_omega = (ba / bo) if bo > 0.0 else float("nan")

    report = ThreeBoundReport(
        type_name=label,
        eps1=float(eps1),
        eps2=float(eps2),
        eps3=float(eps3),
        B_sigma_val=bs,
        B_omega_val=bo,
        B_accel_val=ba,
        Sigma2_max_val=1.5 * bs * bs,
        W2_max_val=1.5 * bo * bo,
        A2_max_val=1.5 * ba * ba,
        ratio_omega_over_sigma=ratio_omega_over_sigma,
        ratio_accel_over_omega=ratio_accel_over_omega,
        hierarchy_strict=bool(hierarchy_ok),
        config={
            "strict": bool(strict),
            "coefficient_source": "tsc.admissibility.three_bound_hierarchy.COEFFS",
            "reference": "MES 1995 Paper II Thm 3.1-3.4",
        },
    )

    if strict and not hierarchy_ok:
        raise HierarchyViolationError(
            "MES three-bound hierarchy violated: "
            f"B_sigma={bs:.3e}, B_omega={bo:.3e}, B_accel={ba:.3e}; "
            f"require B_sigma > B_omega > B_accel. Inputs: "
            f"eps1={eps1}, eps2={eps2}, eps3={eps3}."
        )

    return report


# ---------------------------------------------------------------------------
# Type-by-type evaluation
# ---------------------------------------------------------------------------


def evaluate_all_bianchi_types(
    eps1: float,
    eps2: float,
    eps3: float,
    *,
    strict: bool = True,
) -> dict[str, ThreeBoundReport]:
    """Return ``{type: ThreeBoundReport}`` for all nine Bianchi types.

    The bounds themselves depend only on (eps1, eps2, eps3), not on
    the Bianchi type; this helper exists so the manuscript §§ can
    tabulate per-type reports for completeness.

    Raises :class:`HierarchyViolationError` at the first offending
    type when ``strict=True``.
    """
    out: dict[str, ThreeBoundReport] = {}
    for t in BIANCHI_TYPES:
        out[t] = compute_three_bound_hierarchy(
            eps1, eps2, eps3, type_name=t, strict=strict,
        )
    return out


# ---------------------------------------------------------------------------
# Cross-check against the explicit legacy HTT bounds
# ---------------------------------------------------------------------------


def compare_against_htt_bounds(
    eps1: float,
    eps2: float,
    eps3: float,
    *,
    rtol: float = 1e-10,
) -> dict[str, Any]:
    """Evaluate tsc and htt bounds at the same eps-triple and compare.

    Imports ``tsc_legacy.htt_core_bounds`` lazily so that downstream consumers of
    this module (e.g. manuscript tooling) don't need the editable-htt
    install just to evaluate the bounds on the tsc side.

    Parameters
    ----------
    eps1, eps2, eps3
        Non-negative amplitudes.
    rtol
        Relative tolerance for the per-bound comparison. Default
        ``1e-10`` reflects the bit-identity gate; the two sides differ
        only in coefficient-storage layout (tsc: ``Fraction``-routed
        floats, htt: Python-literal floats), so agreement to full
        double precision is expected.

    Returns
    -------
    dict
        Keys: ``'tsc_B_sigma'``, ``'htt_B_sigma'``, ..., plus
        ``'rtol'`` and per-bound ``'abs_error'`` / ``'rel_error'`` /
        ``'agree'`` flags. The convenience boolean ``'all_agree'``
        summarises the three bounds.
    """
    from tsc_legacy.htt_core_bounds import B_sigma as htt_B_sigma
    from tsc_legacy.htt_core_bounds import B_omega as htt_B_omega
    from tsc_legacy.htt_core_bounds import B_accel as htt_B_accel

    tsc_bs = B_sigma(eps1, eps2, eps3)
    tsc_bo = B_omega(eps1, eps2, eps3)
    tsc_ba = B_accel(eps1, eps2, eps3)
    htt_bs = float(htt_B_sigma(eps1, eps2, eps3))
    htt_bo = float(htt_B_omega(eps1, eps2, eps3))
    htt_ba = float(htt_B_accel(eps1, eps2, eps3))

    def _cmp(a: float, b: float) -> tuple[float, float, bool]:
        abs_err = abs(a - b)
        scale = max(abs(a), abs(b), 1.0)
        rel_err = abs_err / scale
        return abs_err, rel_err, (rel_err <= rtol)

    abs_sig, rel_sig, ok_sig = _cmp(tsc_bs, htt_bs)
    abs_om, rel_om, ok_om = _cmp(tsc_bo, htt_bo)
    abs_ac, rel_ac, ok_ac = _cmp(tsc_ba, htt_ba)

    return {
        "tsc_B_sigma": tsc_bs, "htt_B_sigma": htt_bs,
        "tsc_B_omega": tsc_bo, "htt_B_omega": htt_bo,
        "tsc_B_accel": tsc_ba, "htt_B_accel": htt_ba,
        "abs_error": {
            "B_sigma": float(abs_sig),
            "B_omega": float(abs_om),
            "B_accel": float(abs_ac),
        },
        "rel_error": {
            "B_sigma": float(rel_sig),
            "B_omega": float(rel_om),
            "B_accel": float(rel_ac),
        },
        "agree": {
            "B_sigma": bool(ok_sig),
            "B_omega": bool(ok_om),
            "B_accel": bool(ok_ac),
        },
        "rtol": float(rtol),
        "all_agree": bool(ok_sig and ok_om and ok_ac),
    }
