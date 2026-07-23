"""
tsc/charts/theta4_bridge_verify.py  (TSC-04, Week 4)
=====================================================

Independent derivation of the ``a_2`` coefficients of the :math:`\\Theta^4`
moment map expansion, for cross-checking against ``htt.core.teff_extended``.

Role
----
The effective-temperature field is expanded in Legendre modes

.. math::
   \\Theta(\\mu) = 1 + A\\, P_1(\\mu) + Q\\, P_2(\\mu) + \\ldots,

and the quadrupole of :math:`\\Theta^4` — the ``a_2`` Legendre coefficient
— carries the nonlinear ``T_eff`` signal that the BASS pipeline reads as
its shear-like quadrupole witness. To low order in ``A, Q`` the
expansion (parent plan §11.3 ch03 §3.X+3) reads

.. math::
   a_2[\\Theta^4] \\;=\\; 4Q + 4A^2
     \\;+\\; \\frac{12}{7} Q^2
     \\;+\\; \\frac{44}{7} A^2 Q
     \\;+\\; \\mathcal O((A,Q)^4).

TSC-04 re-derives each coefficient from first principles (closed-form
``∫ P_l P_m P_2 dμ`` Gaunt integrals) and separately re-derives them by
high-order Gauss-Legendre numerical quadrature on :math:`\\Theta^4 P_2`.
A mismatch between the closed-form and the htt numerical extraction
raises a clearly-labelled discrepancy report.

No gating — pure arithmetic. TSC-06 consumes these coefficients to
audit the ``fig_theta4_bridge`` figure produced by ch03 §3.X+3.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import platform
from typing import Any, Mapping

import numpy as np
from scipy.special import legendre

__all__ = [
    "THETA4_A2_COEFFS_EXACT",
    "BridgeCoefficientReport",
    "gaunt_P_ell_int",
    "theta4_a2_numerical",
    "theta4_a2_expansion_numerical",
    "verify_theta4_a2_coefficients",
    "theta4_bridge_coeffs_artifact",
]


# ---------------------------------------------------------------------------
# Exact (closed-form) reference coefficients for a_2[Θ^4]
# ---------------------------------------------------------------------------

#: Closed-form reference from the Gaunt / Legendre-orthogonality derivation.
#: Keys are the (m, n) powers of (A, Q) in the monomial A^m Q^n.
THETA4_A2_COEFFS_EXACT: Mapping[tuple[int, int], float] = {
    (0, 1): 4.0,               # 4 Q     — linear-in-Q piece
    (2, 0): 4.0,               # 4 A²    — dipole-squared piece
    (0, 2): 12.0 / 7.0,        # (12/7) Q²
    (2, 1): 44.0 / 7.0,        # (44/7) A² Q
}


def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for report configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BridgeCoefficientReport:
    """Audit report for one a_2[Θ^4] coefficient.

    Attributes
    ----------
    monomial
        (m, n) power of (A, Q).
    exact
        Closed-form rational value.
    numerical
        High-order Gauss-Legendre extraction from ⟨Θ⁴ P₂⟩.
    htt_extracted
        Optional extracted value from ``htt.core.teff_extended``; ``None``
        when not audited this run.
    rel_err_vs_exact
        |numerical − exact| / |exact|.
    passed
        ``True`` iff the numerical value agrees with the exact rational
        to within ``tol`` (default 1e-6).
    """

    monomial: tuple[int, int]
    exact: float
    numerical: float
    htt_extracted: float | None
    rel_err_vs_exact: float
    passed: bool
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.rel_err_vs_exact < 0.0:
            raise ValueError(
                f"rel_err_vs_exact must be ≥ 0; got {self.rel_err_vs_exact}"
            )


# ---------------------------------------------------------------------------
# Closed-form Gaunt-style integrals (∫ P_l^a P_m^b P_2 dμ for small a, b)
# ---------------------------------------------------------------------------

def gaunt_P_ell_int(exponents_P1: int, exponents_P2: int, N: int = 256) -> float:
    """Numerical ``∫_{-1}^{1} P_1^a · P_2^b · P_2(μ) dμ`` (a = exponents_P1,
    b = exponents_P2).

    Used by :func:`theta4_a2_expansion_numerical` to extract the coefficient
    of :math:`A^a Q^b` in the ``a_2`` expansion. Gauss-Legendre quadrature
    at order ``N`` is exact for polynomials of degree ``≤ 2N−1``, so
    ``N = 64`` already gives machine precision for ``(a, b) ≤ (4, 4)``.
    """
    if exponents_P1 < 0 or exponents_P2 < 0:
        raise ValueError(
            f"exponents must be ≥ 0; got ({exponents_P1}, {exponents_P2})"
        )
    mu, w = np.polynomial.legendre.leggauss(int(N))
    P1 = mu                           # P_1(μ) = μ
    P2 = 1.5 * mu * mu - 0.5          # P_2(μ)
    integrand = (P1 ** exponents_P1) * (P2 ** exponents_P2) * P2
    return float((w * integrand).sum())


# ---------------------------------------------------------------------------
# Numerical a_2 extraction
# ---------------------------------------------------------------------------

def theta4_a2_numerical(A: float, Q: float, *, N: int = 256) -> float:
    """``a_2 = (5/2) ∫ Θ^4 P_2 dμ`` via Gauss-Legendre quadrature.

    The Legendre convention is ``f(μ) = Σ_ℓ a_ℓ P_ℓ(μ)`` with
    ``a_ℓ = (2ℓ+1)/2 ∫_{-1}^{1} f(μ) P_ℓ(μ) dμ``.
    """
    mu, w = np.polynomial.legendre.leggauss(int(N))
    Theta = 1.0 + A * mu + Q * (1.5 * mu * mu - 0.5)
    P2 = 1.5 * mu * mu - 0.5
    integral = float((w * Theta ** 4 * P2).sum())
    return (5.0 / 2.0) * integral


def theta4_a2_expansion_numerical(*, N: int = 256) -> dict[tuple[int, int], float]:
    """Extract each ``a_2`` expansion coefficient by Gauss-Legendre.

    Uses the ``Θ^4`` multinomial expansion

    .. math::
       \\Theta^4 = \\sum_{i+j+k=4}\\binom{4}{i,j,k}\\, A^j Q^k\\,
                    P_1(\\mu)^j P_2(\\mu)^k

    and computes, for each ``(j, k)``,

    .. math::
       c_{j,k} = \\frac{5}{2}\\,\\binom{4}{4-j-k,j,k}\\,
                 \\int P_1^j P_2^k P_2\\,d\\mu.

    Returns the coefficients with the same keys as
    :data:`THETA4_A2_COEFFS_EXACT`.
    """
    from math import comb

    # Enumerate (j, k) with j + k ≤ 4 and j + k ≥ 1 (skip the constant 1).
    coefficients: dict[tuple[int, int], float] = {}
    for j in range(0, 5):
        for k in range(0, 5 - j):
            if j + k == 0:
                continue
            i = 4 - j - k                      # exponent on the constant 1
            multinom = comb(4, i) * comb(j + k, j)
            gaunt = gaunt_P_ell_int(j, k, N=N)
            coeff = (5.0 / 2.0) * multinom * gaunt
            if abs(coeff) < 1e-12:
                coeff = 0.0
            coefficients[(j, k)] = float(coeff)
    return coefficients


# ---------------------------------------------------------------------------
# Bridge verifier (exact vs numerical vs htt)
# ---------------------------------------------------------------------------

def _extract_htt_a2_coefficient(monomial: tuple[int, int]) -> float | None:
    """Pull ``c_{j,k}`` from ``htt.core.teff_extended.TeffMomentMap``.

    Newer htt builds may expose a native ``_a2_coefficient_table`` helper;
    when present we use that exact table first. Older builds fall back to
    finite-difference extraction from ``TeffMomentMap``. Returns ``None``
    if htt is not importable in the current environment.
    """
    try:
        from htt.core import teff_extended as htt_teff
    except ImportError:
        return None
    table_fn = getattr(htt_teff, "_a2_coefficient_table", None)
    if callable(table_fn):
        coeffs = table_fn()
        if monomial in coeffs:
            return float(coeffs[monomial])
    TeffMomentMap = getattr(htt_teff, "TeffMomentMap", None)
    if TeffMomentMap is None:
        return None
    mm = TeffMomentMap(N_theta=200, N_phi=8)

    def a2_from_htt(A_val: float, Q_val: float) -> float:
        # htt's moment map integrates ⟨Θ^α⟩ over the full sphere with
        # its own weight normalisation (÷ 4π). For axisymmetric Θ, the
        # φ-integral is trivial and cancels; the μ-integral convention
        # in htt is (∫₋₁¹ · w_mu), matching Gauss-Legendre on [-1, 1].
        mu = mm.mu[:, 0]
        w_mu = mm.weights[:, 0] * (2.0 * np.pi / mm.N_phi) ** -1 * (4.0 * np.pi)
        # w_mu now recovers the 1-D Gauss-Legendre weights on [-1, 1].
        Theta = 1.0 + A_val * mu + Q_val * (1.5 * mu * mu - 0.5)
        P2 = 1.5 * mu * mu - 0.5
        return (5.0 / 2.0) * float((w_mu * Theta ** 4 * P2).sum())

    j, k = monomial
    # Central-difference extraction at (A, Q) = (0, 0) using suitable step
    # sizes. The coefficient of A^j Q^k is ∂^{j+k} a_2 / (∂A^j ∂Q^k) / (j! k!).
    h = 1e-2
    if (j, k) == (0, 1):
        return (a2_from_htt(0.0, +h) - a2_from_htt(0.0, -h)) / (2.0 * h)
    if (j, k) == (2, 0):
        return (a2_from_htt(+h, 0.0) - 2.0 * a2_from_htt(0.0, 0.0)
                + a2_from_htt(-h, 0.0)) / (h * h)
    if (j, k) == (0, 2):
        return (a2_from_htt(0.0, +h) - 2.0 * a2_from_htt(0.0, 0.0)
                + a2_from_htt(0.0, -h)) / (h * h)
    if (j, k) == (2, 1):
        # Third-order mixed: coefficient of A²Q = (1/2) ∂³a_2/(∂A² ∂Q) |_{0,0}.
        g_plus = (a2_from_htt(+h, +h) - 2.0 * a2_from_htt(0.0, +h)
                  + a2_from_htt(-h, +h)) / (h * h)
        g_minus = (a2_from_htt(+h, -h) - 2.0 * a2_from_htt(0.0, -h)
                   + a2_from_htt(-h, -h)) / (h * h)
        return (g_plus - g_minus) / (2.0 * h) / 2.0   # divide by 2! for A²
    return None


def verify_theta4_a2_coefficients(
    *,
    tol: float = 1e-6,
    tol_htt: float = 5e-3,
    audit_htt: bool = True,
    N_quad: int = 256,
) -> dict[tuple[int, int], BridgeCoefficientReport]:
    """Audit each closed-form coefficient against numerical + htt extractions.

    Parameters
    ----------
    tol
        Relative tolerance for numerical vs closed-form agreement.
    tol_htt
        Relative tolerance for htt vs closed-form — slightly looser to
        accommodate htt's finite-difference step size (1e-2).
    audit_htt
        When ``False``, skip htt cross-check entirely (useful in contexts
        where htt isn't importable). When ``True``, unavailable htt audit
        support is an error rather than a silently skipped cross-check.
    N_quad
        Gauss-Legendre order for the tsc-side numerical extraction.

    Returns
    -------
    dict
        ``{(m, n): BridgeCoefficientReport}`` for the four audited monomials.
    """
    numerical = theta4_a2_expansion_numerical(N=N_quad)
    reports: dict[tuple[int, int], BridgeCoefficientReport] = {}
    for monomial, exact in THETA4_A2_COEFFS_EXACT.items():
        num = numerical.get(monomial, 0.0)
        rel = abs(num - exact) / max(abs(exact), 1e-300)
        passed = rel <= tol
        htt_val = None
        if audit_htt:
            htt_val = _extract_htt_a2_coefficient(monomial)
            if htt_val is None:
                raise RuntimeError(
                    "audit_htt=True requires an importable htt coefficient "
                    "table or TeffMomentMap"
                )
            rel_htt = abs(htt_val - exact) / max(abs(exact), 1e-300)
            passed = passed and (rel_htt <= tol_htt)
        reports[monomial] = BridgeCoefficientReport(
            monomial=monomial,
            exact=float(exact),
            numerical=float(num),
            htt_extracted=float(htt_val) if htt_val is not None else None,
            rel_err_vs_exact=float(rel),
            passed=bool(passed),
            config={
                "N_quad": int(N_quad),
                "tol": float(tol),
                "tol_htt": float(tol_htt),
                "audit_htt": bool(audit_htt),
            },
        )
    return reports


def theta4_bridge_coeffs_artifact(
    *,
    tol: float = 1e-6,
    tol_htt: float = 5e-3,
    audit_htt: bool = True,
    N_quad: int = 256,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``theta4_bridge_coeffs_v1.json`` from the TSC bridge audit."""
    reports = verify_theta4_a2_coefficients(
        tol=tol,
        tol_htt=tol_htt,
        audit_htt=audit_htt,
        N_quad=N_quad,
    )
    serialised_reports = []
    for monomial, report in reports.items():
        serialised_reports.append({
            "monomial": [int(monomial[0]), int(monomial[1])],
            "exact": float(report.exact),
            "numerical": float(report.numerical),
            "htt_extracted": (
                None if report.htt_extracted is None else float(report.htt_extracted)
            ),
            "rel_err_vs_exact": float(report.rel_err_vs_exact),
            "passed": bool(report.passed),
            "config": dict(report.config),
        })

    extra = dict(metadata or {})
    config_payload = {
        "tol": tol,
        "tol_htt": tol_htt,
        "audit_htt": audit_htt,
        "N_quad": N_quad,
        "metadata": extra,
    }
    return _jsonify({
        "artifact_name": "theta4_bridge_coeffs_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "tsc.charts.theta4_bridge_verify.theta4_bridge_coeffs_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "REPORT"),
        "scope_label": extra.get("scope_label", "report"),
        "production_allowed": False,
        "all_passed": bool(all(report.passed for report in reports.values())),
        "coefficients_exact": {
            f"A^{m}_Q^{n}": float(value)
            for (m, n), value in THETA4_A2_COEFFS_EXACT.items()
        },
        "reports": serialised_reports,
    })
