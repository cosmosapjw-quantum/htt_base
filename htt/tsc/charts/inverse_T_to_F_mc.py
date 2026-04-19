"""
tsc/charts/inverse_T_to_F_mc.py  (Week 3 Day 3, merged v4.1)
=============================================================

Monte Carlo stress-test of the F⁻¹ ∘ F closure across the full Paper I
product space

    (xi, moment_order n, anisotropy amplitude) ∈ {-1, 0, +1} × {2, 3, 4} × {0.05, 0.1, 0.2}

For each (27) cell, `n_draws` random Θ(μ) coefficient vectors are generated,
forward-mapped to T_ℓ, and then inverted. The Monte Carlo output characterizes
the precision floor and iteration cost across the full operating envelope.

Role in Paper I / thesis
-------------------------
Absorbed from v4's original Week 3 Day 2 scope. The sweep's purpose is *not*
to discover new physics but to lock down the closure property as a stable
baseline before downstream (forward strata, likelihood, figure) consumers
start relying on the inverse map. Every subsequent precision claim about the
inverse at amplitude ≤ 0.2 traces back to this report.

Admissibility handling
----------------------
Random coefficient draws can produce Θ(μ) that violates positivity.
Rejection sampling on a dense μ grid ensures all realized draws are
physically admissible. Rejected draws are counted (not silently dropped)
and surfaced in the per-cell diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    axisymmetric_F,
    check_theta_positive,
)
from tsc.charts.inverse_T_to_F import (
    invert_T_to_Theta_axisymmetric,
    InverseResult,
)


# ============================================================================
# Section 1 - Sweep parameterization
# ============================================================================

XI_LIST: Tuple[int, ...] = (-1, 0, +1)
"""Statistics parameter values probed in the sweep."""

MOMENT_ORDER_LIST: Tuple[int, ...] = (2, 3, 4)
"""I_n moment orders probed in the sweep. n=2 (number), 3 (energy), 4 (stress)."""

AMP_LIST: Tuple[float, ...] = (0.05, 0.10, 0.20)
"""Anisotropy amplitudes. |Θ_ℓ| ≤ amp for ℓ ≥ 1; Θ_0 fixed at 1.0."""

L_THETA_DEFAULT: int = 3
"""Highest Legendre multipole retained (square system L_T = L_Θ)."""

REJECTION_CAP: int = 200
"""Maximum coefficient-draw rejections per successful sample."""


# ============================================================================
# Section 2 - Per-trial record
# ============================================================================

@dataclass(frozen=True)
class TrialRecord:
    """One successful roundtrip trial."""
    xi: int
    moment_order: int
    amp: float
    draw_idx: int
    seed: int
    theta_true: Tuple[float, ...]
    theta_rec: Tuple[float, ...]
    max_rel_error: float
    max_abs_error: float
    n_iter: int
    final_residual: float
    jacobian_cond: float
    converged: bool
    n_rejected_draws: int


@dataclass
class CellStats:
    """Aggregate statistics per (xi, moment_order, amp) cell."""
    xi: int
    moment_order: int
    amp: float
    n_trials: int
    max_rel_error_p50: float
    max_rel_error_p95: float
    max_rel_error_max: float
    n_iter_mean: float
    n_iter_max: int
    jacobian_cond_mean: float
    jacobian_cond_max: float
    converged_fraction: float
    total_rejected_draws: int


# ============================================================================
# Section 3 - Random Θ draw with rejection sampling
# ============================================================================

def draw_admissible_theta(
    amp: float,
    L_Theta: int,
    rng: np.random.Generator,
    rejection_cap: int = REJECTION_CAP,
) -> Tuple[AxisymmetricField, int]:
    """Uniformly sample Θ_ℓ ∈ [-amp, +amp] for ℓ ≥ 1; reject non-positive Θ(μ).

    Θ_0 is fixed at 1.0 so the background is isotropic unit temperature.
    The draw is retried until admissible or `rejection_cap` is exhausted.

    Returns
    -------
    (field, n_rejected) : (AxisymmetricField, int)
        `field` — admissible Θ.
        `n_rejected` — number of rejected draws before success.

    Raises
    ------
    RuntimeError
        If `rejection_cap` draws all fail admissibility.
    """
    for attempt in range(rejection_cap):
        coeffs = np.zeros(L_Theta + 1)
        coeffs[0] = 1.0
        coeffs[1:] = rng.uniform(-amp, amp, size=L_Theta)
        field = AxisymmetricField(
            coeffs=coeffs, name=f"Theta_mc_{attempt}",
        )
        if check_theta_positive(field):
            return field, attempt
    raise RuntimeError(
        f"rejection sampling exhausted at cap={rejection_cap}, "
        f"amp={amp}, L_Theta={L_Theta}"
    )


# ============================================================================
# Section 4 - Per-trial forward-inverse cycle
# ============================================================================

def run_trial(
    xi: int,
    moment_order: int,
    amp: float,
    draw_idx: int,
    seed: int,
    L_Theta: int = L_THETA_DEFAULT,
    tol: float = 1e-11,
) -> TrialRecord:
    """Execute a single roundtrip and record diagnostics.

    Parameters
    ----------
    xi, moment_order, amp : cell coordinates
    draw_idx : int
        Index within the cell (for reproducibility).
    seed : int
        RNG seed; realized as `seed + draw_idx` for per-draw variation.
    L_Theta : int
        Highest Legendre multipole; defaults to 3.
    tol : float
        Newton tolerance.

    Returns
    -------
    TrialRecord
    """
    rng = np.random.default_rng(seed + draw_idx)
    theta_true, n_rejected = draw_admissible_theta(
        amp=amp, L_Theta=L_Theta, rng=rng,
    )

    fwd = axisymmetric_F(
        xi=xi, Theta=theta_true, L_out=L_Theta, moment_order=moment_order,
    )
    result: InverseResult = invert_T_to_Theta_axisymmetric(
        T_ell_obs=fwd.T_ell,
        xi=xi,
        moment_order=moment_order,
        L_Theta=L_Theta,
        tol=tol,
    )

    true_coeffs = theta_true.coeffs
    rec_coeffs = result.Theta.coeffs
    abs_err = np.abs(rec_coeffs - true_coeffs)
    rel_scale = np.maximum(np.abs(true_coeffs), 1e-12)
    per_mode_rel = abs_err / rel_scale

    return TrialRecord(
        xi=xi,
        moment_order=moment_order,
        amp=amp,
        draw_idx=draw_idx,
        seed=seed,
        theta_true=tuple(float(x) for x in true_coeffs),
        theta_rec=tuple(float(x) for x in rec_coeffs),
        max_rel_error=float(np.max(per_mode_rel)),
        max_abs_error=float(np.max(abs_err)),
        n_iter=int(result.n_iter),
        final_residual=float(result.final_residual),
        jacobian_cond=float(result.jacobian_cond),
        converged=bool(result.converged),
        n_rejected_draws=int(n_rejected),
    )


# ============================================================================
# Section 5 - Full sweep
# ============================================================================

def run_sweep(
    n_draws_per_cell: int,
    seed: int = 20260417,
    L_Theta: int = L_THETA_DEFAULT,
    tol: float = 1e-11,
    xi_list: Tuple[int, ...] = XI_LIST,
    moment_order_list: Tuple[int, ...] = MOMENT_ORDER_LIST,
    amp_list: Tuple[float, ...] = AMP_LIST,
) -> List[TrialRecord]:
    """Run the Monte Carlo sweep across the (xi, moment_order, amp) cells.

    Parameters
    ----------
    n_draws_per_cell : int
        Number of random Θ draws per cell. Must be ≥ 1.
    seed : int
        Base RNG seed; individual trials use `seed + cell_offset + draw_idx`.
    L_Theta : int
        Legendre multipole cap (default 3).
    tol : float
        Newton tolerance forwarded to the inverse.
    xi_list, moment_order_list, amp_list : tuple
        Cell coordinates; defaults defined at module level.

    Returns
    -------
    List[TrialRecord]
        Flat list of every successful trial in deterministic order.
    """
    if n_draws_per_cell < 1:
        raise ValueError(
            f"n_draws_per_cell must be >= 1, got {n_draws_per_cell}"
        )

    records: List[TrialRecord] = []
    for xi_idx, xi in enumerate(xi_list):
        for n_idx, n in enumerate(moment_order_list):
            for amp_idx, amp in enumerate(amp_list):
                cell_offset = 1000 * (
                    xi_idx
                    + 10 * n_idx
                    + 100 * amp_idx
                )
                cell_seed = seed + cell_offset
                for draw_idx in range(n_draws_per_cell):
                    rec = run_trial(
                        xi=xi,
                        moment_order=n,
                        amp=amp,
                        draw_idx=draw_idx,
                        seed=cell_seed,
                        L_Theta=L_Theta,
                        tol=tol,
                    )
                    records.append(rec)
    return records


# ============================================================================
# Section 6 - Aggregation
# ============================================================================

def aggregate_by_cell(records: List[TrialRecord]) -> List[CellStats]:
    """Compute per-cell summary statistics from a flat trial list."""
    if not records:
        return []

    # Group by (xi, moment_order, amp)
    buckets: dict = {}
    for r in records:
        key = (r.xi, r.moment_order, r.amp)
        buckets.setdefault(key, []).append(r)

    stats: List[CellStats] = []
    for (xi, n, amp), trials in sorted(buckets.items()):
        rel_errs = np.array([t.max_rel_error for t in trials])
        n_iters = np.array([t.n_iter for t in trials])
        cond_nums = np.array([t.jacobian_cond for t in trials])
        converged = np.array([t.converged for t in trials])
        rejected = np.array([t.n_rejected_draws for t in trials])

        stats.append(CellStats(
            xi=xi, moment_order=n, amp=amp,
            n_trials=len(trials),
            max_rel_error_p50=float(np.median(rel_errs)),
            max_rel_error_p95=float(np.percentile(rel_errs, 95)),
            max_rel_error_max=float(np.max(rel_errs)),
            n_iter_mean=float(np.mean(n_iters)),
            n_iter_max=int(np.max(n_iters)),
            jacobian_cond_mean=float(np.mean(cond_nums)),
            jacobian_cond_max=float(np.max(cond_nums)),
            converged_fraction=float(np.mean(converged)),
            total_rejected_draws=int(np.sum(rejected)),
        ))
    return stats


# ============================================================================
# Section 7 - CSV / Markdown output
# ============================================================================

def records_to_csv(
    records: List[TrialRecord], path: str,
) -> None:
    """Write flat trial records to a CSV file."""
    import csv
    fieldnames = [
        "xi", "moment_order", "amp", "draw_idx", "seed",
        "max_rel_error", "max_abs_error",
        "n_iter", "final_residual", "jacobian_cond",
        "converged", "n_rejected_draws",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow({
                "xi": r.xi,
                "moment_order": r.moment_order,
                "amp": r.amp,
                "draw_idx": r.draw_idx,
                "seed": r.seed,
                "max_rel_error": r.max_rel_error,
                "max_abs_error": r.max_abs_error,
                "n_iter": r.n_iter,
                "final_residual": r.final_residual,
                "jacobian_cond": r.jacobian_cond,
                "converged": r.converged,
                "n_rejected_draws": r.n_rejected_draws,
            })


def render_report_markdown(
    stats: List[CellStats],
    n_draws_per_cell: int,
    seed: int,
    title: str = "inverse_T_to_F roundtrip MC sweep",
) -> str:
    """Produce a Markdown summary from aggregated cell statistics."""
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        f"Sweep parameters: `n_draws_per_cell = {n_draws_per_cell}`, "
        f"`seed = {seed}`, L_Θ = {L_THETA_DEFAULT}."
    )
    lines.append("")
    lines.append(
        f"Total cells: {len(stats)}; "
        f"total trials: {sum(s.n_trials for s in stats)}."
    )
    lines.append("")
    lines.append("## Per-cell summary")
    lines.append("")
    lines.append(
        "| xi | n | amp | p50 err | p95 err | max err | iter mean | "
        "iter max | cond mean | cond max | conv | rejected |"
    )
    lines.append(
        "|----|---|-----|---------|---------|---------|-----------|"
        "----------|-----------|----------|------|----------|"
    )
    for s in stats:
        xi_label = {-1: "FD", 0: "MB", +1: "BE"}[s.xi]
        lines.append(
            f"| {xi_label} | {s.moment_order} | {s.amp} | "
            f"{s.max_rel_error_p50:.2e} | "
            f"{s.max_rel_error_p95:.2e} | "
            f"{s.max_rel_error_max:.2e} | "
            f"{s.n_iter_mean:.2f} | "
            f"{s.n_iter_max} | "
            f"{s.jacobian_cond_mean:.2f} | "
            f"{s.jacobian_cond_max:.2f} | "
            f"{s.converged_fraction:.1%} | "
            f"{s.total_rejected_draws} |"
        )
    lines.append("")
    lines.append("## Precision floor per amplitude tier")
    lines.append("")
    by_amp: dict = {}
    for s in stats:
        by_amp.setdefault(s.amp, []).append(s.max_rel_error_max)
    lines.append("| amp | worst max rel error across xi, n |")
    lines.append("|-----|---------------------------------|")
    for amp in sorted(by_amp.keys()):
        worst = max(by_amp[amp])
        lines.append(f"| {amp} | {worst:.2e} |")
    lines.append("")
    return "\n".join(lines)
