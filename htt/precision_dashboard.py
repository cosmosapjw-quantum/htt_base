"""
precision_dashboard.py  (Week 3 Day 5a, merged v4.1)
=====================================================

L0 precision-verification dashboard. Oracle is analytic Paper I closed-form
moments + ch05 cross-reference table — no CAMB dependency.

Purpose
-------
The L0 gate (v4.1 MERGED §3, Amendment 01) is the first rung of the precision
ladder. Before W4 entry, every distribution-level numerical primitive that
downstream layers consume must be shown to match its analytical oracle at
machine precision. Subsequent ladder rungs (L1 source-level, L2 $D_\\ell$
gate, L3 three-way consensus) do not reach their own oracles if L0 is not
green, so a non-trivial L0 failure is a gate block.

Oracle library (analytic, closed form)
--------------------------------------
At $\\eta = 0$:

  BE : I_n = Γ(n+1) × ζ(n+1)                  (Planck integral)
  FD : I_n = (1 - 2^{-n}) × Γ(n+1) × ζ(n+1)   (Fermi-Dirac)
  MB : I_n = Γ(n+1) = n!                      (classical Maxwell-Boltzmann)

Ratios:

  (I_4 / I_3) = 4 × ζ(5) / ζ(4)        for BE
              = (30/7) × ζ(5) / ζ(4)   for FD
              = 4                      for MB (exact)

Shear source (ch05 Eq.):

  Σ_2^{(s)} = (8/15) × I_4/I_3

Laguerre MB orthogonality (Paper I §V):

  ⟨ L_s^α, L_{s'}^α ⟩_{MB} = Γ(s+α+1)/s! × δ_{ss'}

These are the only oracles allowed at L0 — no CAMB comparison enters here.

Output artifacts
----------------
- `DashboardReport` (frozen dataclass) with per-check verdicts
- `to_markdown(report)` — human-readable summary table
- `to_json(report)` — machine-readable for downstream tooling

The report's `all_passed` is the L0 gate verdict.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Tuple, List

import numpy as np
from scipy.special import zeta

from tsc.charts.laguerre_basis import (
    xi_moment,
    I4_over_I3,
    shear_source_coeff,
    build_stiffness_table,
    verify_mb_orthogonality,
    gram_matrix,
    laguerre_norm_squared,
)
from tsc.charts.inverse_T_to_F_mc import run_sweep, aggregate_by_cell


# ============================================================================
# Section 1 - Version pin
# ============================================================================

L0_DASHBOARD_VERSION: str = "v1.0-w3d5a"
"""Version tag for the dashboard schema. Bump on any CheckResult shape change."""


# ============================================================================
# Section 2 - Analytic oracle values
# ============================================================================

_ZETA_4: float = float(zeta(4))   # = π⁴/90
_ZETA_5: float = float(zeta(5))


def analytic_I_n(statistics: str, n: int) -> float:
    """Closed-form I_n at η = 0 per statistics label.

    Parameters
    ----------
    statistics : str
        One of 'BE', 'MB', 'FD'.
    n : int
        Moment order.

    Returns
    -------
    float
    """
    if statistics == "BE":
        return math.gamma(n + 1) * float(zeta(n + 1))
    if statistics == "MB":
        return math.gamma(n + 1)
    if statistics == "FD":
        return (1.0 - 2.0 ** (-n)) * math.gamma(n + 1) * float(zeta(n + 1))
    raise ValueError(f"unknown statistics: {statistics}")


def analytic_I4_over_I3(statistics: str) -> float:
    """Closed-form I_4 / I_3 at η = 0."""
    return analytic_I_n(statistics, 4) / analytic_I_n(statistics, 3)


def analytic_Sigma_2(statistics: str) -> float:
    """ch05 shear-source coefficient Σ_2 = (8/15) × I_4/I_3."""
    return (8.0 / 15.0) * analytic_I4_over_I3(statistics)


# ============================================================================
# Section 3 - CheckResult container
# ============================================================================

@dataclass(frozen=True)
class CheckResult:
    """One oracle-vs-observed row in the dashboard."""
    check_id: str
    category: str
    statistics: Optional[str]
    oracle_value: Optional[float]
    observed_value: float
    tolerance: Optional[float]
    passed: bool
    notes: str = ""

    @property
    def relative_error(self) -> Optional[float]:
        """Rel err vs oracle when oracle is meaningful, else None."""
        if self.oracle_value is None or self.oracle_value == 0:
            return None
        return abs(self.observed_value - self.oracle_value) / abs(self.oracle_value)


@dataclass(frozen=True)
class DashboardReport:
    """L0 dashboard output."""
    checks: Tuple[CheckResult, ...]
    all_passed: bool
    n_total: int
    n_passed: int
    n_warnings: int   # rows with non-empty notes but still passed
    spec_version: str
    generated_at: str


# ============================================================================
# Section 4 - Individual check implementations
# ============================================================================

def _check_Xi_moments() -> List[CheckResult]:
    """Verify I_3 and I_4 per statistics against closed-form."""
    checks: List[CheckResult] = []
    tol = 1e-10
    for stats_label, xi in [("BE", +1), ("MB", 0), ("FD", -1)]:
        for n in (3, 4):
            oracle = analytic_I_n(stats_label, n)
            observed = xi_moment(n, xi, 0.0)
            rel_err = abs(observed - oracle) / abs(oracle)
            checks.append(CheckResult(
                check_id=f"I_{n}[{stats_label}, eta=0]",
                category="moment",
                statistics=stats_label,
                oracle_value=oracle,
                observed_value=observed,
                tolerance=tol,
                passed=rel_err < tol,
                notes=f"rel_err={rel_err:.2e}",
            ))
    return checks


def _check_I4_over_I3() -> List[CheckResult]:
    """Stiffness ratio I_4 / I_3 vs closed form, per statistics."""
    checks: List[CheckResult] = []
    tol = 1e-10
    for stats_label, xi in [("BE", +1), ("MB", 0), ("FD", -1)]:
        oracle = analytic_I4_over_I3(stats_label)
        observed = I4_over_I3(xi, 0.0)
        rel_err = abs(observed - oracle) / abs(oracle)
        checks.append(CheckResult(
            check_id=f"I_4/I_3[{stats_label}]",
            category="ratio",
            statistics=stats_label,
            oracle_value=oracle,
            observed_value=observed,
            tolerance=tol,
            passed=rel_err < tol,
            notes=f"rel_err={rel_err:.2e}",
        ))
    return checks


def _check_Sigma_2() -> List[CheckResult]:
    """Shear source coefficient Σ_2 = (8/15) I_4/I_3 vs ch05."""
    checks: List[CheckResult] = []
    tol = 1e-10
    for stats_label, xi in [("BE", +1), ("MB", 0), ("FD", -1)]:
        oracle = analytic_Sigma_2(stats_label)
        observed = shear_source_coeff(xi, 0.0)
        rel_err = abs(observed - oracle) / abs(oracle)
        checks.append(CheckResult(
            check_id=f"Sigma_2[{stats_label}]",
            category="ch05_cross_ref",
            statistics=stats_label,
            oracle_value=oracle,
            observed_value=observed,
            tolerance=tol,
            passed=rel_err < tol,
            notes=f"ch05 Eq.; rel_err={rel_err:.2e}",
        ))
    return checks


def _check_mb_gram_orthogonality() -> List[CheckResult]:
    """Paper I §V: MB Laguerre Gram diagonal / off-diagonal check."""
    n_basis = 5
    alpha = 2.0
    is_ortho, G, diag_expected = verify_mb_orthogonality(
        n_basis=n_basis, alpha=alpha, rtol=1e-13,
    )
    # Extract numerical values for the report
    observed_diag = np.diag(G)
    diag_rel_err = float(np.max(
        np.abs(observed_diag - diag_expected) / np.abs(diag_expected)
    ))
    # Off-diagonal max ratio
    off_max = 0.0
    for i in range(n_basis):
        for j in range(n_basis):
            if i != j:
                denom = math.sqrt(diag_expected[i] * diag_expected[j])
                off_max = max(off_max, abs(G[i, j]) / denom)

    checks = [
        CheckResult(
            check_id="MB_gram_diag[n=5, alpha=2]",
            category="gram",
            statistics="MB",
            oracle_value=float(diag_expected[0]),
            observed_value=float(observed_diag[0]),
            tolerance=1e-13,
            passed=bool(diag_rel_err < 1e-13),
            notes=f"diag_rel_err_max={diag_rel_err:.2e}",
        ),
        CheckResult(
            check_id="MB_gram_offdiag[n=5, alpha=2]",
            category="gram",
            statistics="MB",
            oracle_value=0.0,
            observed_value=off_max,
            tolerance=1e-13,
            passed=bool(off_max < 1e-13),
            notes=f"off_diag_max={off_max:.2e}",
        ),
    ]
    return checks


def _check_mb_twofield_gram_kappa() -> CheckResult:
    """MB TWO_FIELD Gram κ reproducibility check (no pass/fail threshold).

    W2D5 documented κ = 54.3 at η = 0. This check records the current κ
    value for drift detection; there is no analytic tolerance since Gram
    conditioning is a computed property.
    """
    basis_twofield = [
        lambda x: np.ones_like(np.asarray(x, dtype=float)),
        lambda x: np.asarray(x, dtype=float),
    ]
    # Build 2x2 Gram for [1, x] under MB
    from tsc.diagnostics.tangency import weighted_inner_product
    G = np.zeros((2, 2))
    for i, f in enumerate(basis_twofield):
        for j, g in enumerate(basis_twofield):
            G[i, j] = weighted_inner_product(
                f, g, xi=0, eta=0.0, alpha=2.0,
            )
    kappa_observed = float(np.linalg.cond(G))
    expected = 54.3
    rel_err = abs(kappa_observed - expected) / expected
    return CheckResult(
        check_id="MB_twofield_Gram_kappa",
        category="reproducibility",
        statistics="MB",
        oracle_value=expected,
        observed_value=kappa_observed,
        tolerance=0.05,   # 5% reproducibility band
        passed=rel_err < 0.05,
        notes=f"W2D5 reference 54.3; rel_err={rel_err:.3f}",
    )


def _check_roundtrip_closure(
    n_draws_per_cell: int,
    seed: int,
) -> List[CheckResult]:
    """F⁻¹ ∘ F closure across the (xi, n, amp) product space.

    Two checks per amp tier:
      - p95 across cells at that amp     (must pass < 1e-8)
      - worst-case max across cells       (documented, non-blocking outlier band)
    """
    records = run_sweep(n_draws_per_cell=n_draws_per_cell, seed=seed)
    stats = aggregate_by_cell(records)

    checks: List[CheckResult] = []
    amp_tol_p95 = 1e-8
    amp_tol_worst = 1e-7   # one decade below 1e-8; known BE-n=2-amp=0.2 outlier sits at ~4e-8

    for amp in (0.05, 0.10, 0.20):
        # Worst p95 across all 9 (xi, n) cells at this amp
        cells_at_amp = [s for s in stats if s.amp == amp]
        worst_p95 = max(s.max_rel_error_p95 for s in cells_at_amp)
        worst_max = max(s.max_rel_error_max for s in cells_at_amp)

        checks.append(CheckResult(
            check_id=f"roundtrip_p95[amp={amp}]",
            category="roundtrip",
            statistics=None,
            oracle_value=0.0,
            observed_value=worst_p95,
            tolerance=amp_tol_p95,
            passed=worst_p95 < amp_tol_p95,
            notes=f"worst p95 across 9 (xi, n) cells",
        ))
        checks.append(CheckResult(
            check_id=f"roundtrip_worst[amp={amp}]",
            category="roundtrip",
            statistics=None,
            oracle_value=0.0,
            observed_value=worst_max,
            tolerance=amp_tol_worst,
            passed=worst_max < amp_tol_worst,
            notes=(
                "worst max across 9 cells; single-trial outliers documented"
                if worst_max < amp_tol_worst else
                "worst-case outlier exceeds 1e-7 band — investigate"
            ),
        ))
    return checks


# ============================================================================
# Section 5 - Main driver
# ============================================================================

def run_l0_dashboard(
    n_draws_per_cell: int = 50,
    seed: int = 20260417,
    include_roundtrip: bool = True,
) -> DashboardReport:
    """Execute the full L0 check battery and assemble a report.

    Parameters
    ----------
    n_draws_per_cell : int
        MC draws per cell for the roundtrip closure check. Set lower (e.g.,
        5) for fast pytest runs; 50 for production.
    seed : int
        RNG seed passed through to `run_sweep`.
    include_roundtrip : bool
        If False, skip the MC roundtrip tier (for fast reproducibility
        snapshots of analytic oracles only).

    Returns
    -------
    DashboardReport
    """
    all_checks: List[CheckResult] = []
    all_checks.extend(_check_Xi_moments())
    all_checks.extend(_check_I4_over_I3())
    all_checks.extend(_check_Sigma_2())
    all_checks.extend(_check_mb_gram_orthogonality())
    all_checks.append(_check_mb_twofield_gram_kappa())
    if include_roundtrip:
        all_checks.extend(
            _check_roundtrip_closure(
                n_draws_per_cell=n_draws_per_cell, seed=seed,
            )
        )

    n_total = len(all_checks)
    n_passed = sum(1 for c in all_checks if c.passed)
    n_warnings = sum(
        1 for c in all_checks
        if c.passed and c.notes and "rel_err" not in c.notes
    )

    return DashboardReport(
        checks=tuple(all_checks),
        all_passed=all(c.passed for c in all_checks),
        n_total=n_total,
        n_passed=n_passed,
        n_warnings=n_warnings,
        spec_version=L0_DASHBOARD_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# Section 6 - Output formatting
# ============================================================================

def to_markdown(report: DashboardReport) -> str:
    """Render the report as a Markdown document."""
    verdict = "✅ PASS" if report.all_passed else "❌ FAIL"
    lines: List[str] = []
    lines.append(f"# L0 Precision Dashboard — {verdict}")
    lines.append("")
    lines.append(f"- **Spec version**: `{report.spec_version}`")
    lines.append(f"- **Generated**: {report.generated_at}")
    lines.append(
        f"- **Checks**: {report.n_passed} / {report.n_total} passed "
        f"({report.n_warnings} with warnings)"
    )
    lines.append("")
    lines.append("## Check table")
    lines.append("")
    lines.append(
        "| check_id | category | stat | oracle | observed | tol | verdict | notes |"
    )
    lines.append(
        "|----------|----------|------|--------|----------|-----|---------|-------|"
    )
    for c in report.checks:
        verdict_cell = "PASS" if c.passed else "FAIL"
        oracle_str = (
            f"{c.oracle_value:.6g}" if c.oracle_value is not None else "—"
        )
        tol_str = f"{c.tolerance:.1e}" if c.tolerance is not None else "—"
        stat_str = c.statistics if c.statistics else "—"
        lines.append(
            f"| `{c.check_id}` | {c.category} | {stat_str} | "
            f"{oracle_str} | {c.observed_value:.6g} | {tol_str} | "
            f"{verdict_cell} | {c.notes} |"
        )
    lines.append("")
    return "\n".join(lines)


def to_json(report: DashboardReport) -> str:
    """Render the report as a JSON string."""
    return json.dumps(asdict(report), indent=2, default=str)
