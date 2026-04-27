"""V5-RUNTIME Round-17 audit follow-up — bias-floor reprobe at b_k_sq=0.

This is V0e in `docs/V5_ROUND17_AUDIT_VERDICT_AND_REVISED_PLAN.md §5.2`.
Both audit reports (Report 1 §3, Report 2 §5.5) flagged that the
post-R10/R11 ν seed bug-fix was never re-measured at the bias-floor
probe level, and the post-R15-P0 + post-R16 codebase has not been
checked for residual amplitude-independent bias contamination.

Background. Round-9 §5d (`docs/V5_ROUND9_FINDINGS.md:271-308`) located
a real seed-formula bug: `pi_nu` and `G_3` in
`htt/bass/perturbation/regular_adiabatic_ic.py::_seed_formulae`
were missing the `B_K_sq` linear factor present everywhere else,
which produced an amplitude-independent visibility-source floor that
contaminated bias-subtracted extraction. Pre-fix at `k = 10⁻⁴`,
ℓ = 2: `|Δ_bias|/|Δ_target| = 3.08`. Round-10/Round-11 added the
missing `B_K_sq *` factor; convention-audit residual ratio dropped
1.36e+4 → 7.57e+2 (18× improvement).

Open question. Has the bias-floor stayed small post-R11, or has some
*other* amplitude-independent term in the IMEX startup, in `eta_cov`,
or in the IC consistency surface introduced a new floor that survives
bias-subtraction at very-low k?

Counter-test design.
  - Run `compute_transfer_function_at_k(b_k_sq=0.0)` directly at
    k ∈ {10⁻⁵, 10⁻⁴, 10⁻³, 10⁻², 10⁻¹·⁵} on the post-R15-P0,
    post-R16 codebase.
  - Run the same at `b_k_sq=1.0` to get Δ_target.
  - Tabulate `|Δ_bias|/|Δ_target|` per (k, ℓ) for ℓ ∈ {0, 1, 2, 3, 4}.

Predictions.
  - Bias-floor closed: ratios ≪ 1 (say, < 10⁻³) across the grid.
    Implies the 6.43× residual is genuinely D-2, not contaminated by
    a residual amplitude-independent floor.
  - Bias-floor still leaks: ratios > 0.1 at very-low k. Implies a
    secondary defect coexists with D-2; closing D-2 alone would not
    flip `test_d2_pstf_closure.py` to xpass.

Wall time. ~5-10 minutes (5 k-values × 2 amplitude probes = 10
single-k pipeline runs at L_max=8).

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base
    venv/bin/python scripts/v5_round17_bias_floor_reprobe.py
"""
from __future__ import annotations

import os

# Round-17 P3.5 perf: cap BLAS threads at 1 before numpy import (see
# v5_round17_eta_init_sweep.py for rationale).
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import sys
import time
from dataclasses import replace as _dc_replace
from pathlib import Path

_HTT_ROOT = Path(__file__).resolve().parents[1] / "htt"
_HTT_SRC = _HTT_ROOT / "src"
if _HTT_SRC.is_dir() and str(_HTT_SRC) not in sys.path:
    sys.path.insert(0, str(_HTT_SRC))
if str(_HTT_ROOT) not in sys.path:
    sys.path.insert(0, str(_HTT_ROOT))

import numpy as np

from bass.species.registry import SpeciesBackgroundRegistry
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    compute_transfer_function_at_k,
)


K_PROBES_MPC = (1.0e-5, 1.0e-4, 1.0e-3, 1.0e-2, 10.0 ** -1.5)
ELL_REPORT = (0, 1, 2, 3, 4)


def _delta_T_at_ell(transfer, ell: int) -> float:
    """Extract Δ_ℓ^T (m=0 channel) from BianchiTransferFunctions.
    Treats out-of-range or missing components as 0.
    """
    arr = np.asarray(transfer.delta_T_m0, dtype=np.float64)
    if ell < 0 or ell >= arr.size:
        return 0.0
    return float(arr[ell])


def main() -> None:
    print("[t=0.0 min] V5 Round-17 V0e — bias-floor reprobe")
    print("            building Planck 2018 species registry...")
    t_start = time.perf_counter()

    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )

    # Round-17 P3.5 perf: keep production tolerances (rtol/atol relaxation
    # introduced 2× D_2 drift in V0d sweep — see v5_round17_perf_smoke_test.py).
    base_cfg = FLRWPipelineConfig(
        L_max_tower=8,
        ell_max_transfer=8,
    )

    # Probe pairs: (b_k_sq=0 → bias) and (b_k_sq=1 → target). Disable
    # `unit_amplitude_normalization` so the raw response is returned
    # without the spurious 1e-6 floor that the linear-probe path also
    # disables.
    bias_cfg = _dc_replace(
        base_cfg,
        primordial_b_k_sq=0.0,
        primordial_b_k_sq_fn=None,
        bias_subtraction=False,
        unit_amplitude_normalization=False,
    )
    target_cfg = _dc_replace(
        base_cfg,
        primordial_b_k_sq=1.0,
        primordial_b_k_sq_fn=None,
        bias_subtraction=False,
        unit_amplitude_normalization=False,
    )

    rows = []
    for k in K_PROBES_MPC:
        elapsed_min = (time.perf_counter() - t_start) / 60.0
        print(f"[t={elapsed_min:.2f} min] k = {k:.3e} Mpc⁻¹")

        try:
            bias_xfer = compute_transfer_function_at_k(
                species, k, config=bias_cfg, bianchi_type="I",
            )
            target_xfer = compute_transfer_function_at_k(
                species, k, config=target_cfg, bianchi_type="I",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"               FAILED: {type(exc).__name__}: {exc}")
            for ell in ELL_REPORT:
                rows.append(
                    {
                        "k": k,
                        "ell": ell,
                        "delta_bias": float("nan"),
                        "delta_target": float("nan"),
                        "ratio_abs": float("nan"),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            continue

        for ell in ELL_REPORT:
            d_b = _delta_T_at_ell(bias_xfer, ell)
            d_t = _delta_T_at_ell(target_xfer, ell)
            denom = abs(d_t)
            ratio = abs(d_b) / denom if denom > 1e-300 else float("inf")
            rows.append(
                {
                    "k": k,
                    "ell": ell,
                    "delta_bias": d_b,
                    "delta_target": d_t,
                    "ratio_abs": ratio,
                }
            )

    elapsed_min = (time.perf_counter() - t_start) / 60.0

    print()
    print("=" * 90)
    print("V5 Round-17 V0e — bias-floor reprobe RESULT TABLE")
    print("=" * 90)
    print(
        f"{'k [Mpc⁻¹]':>12} {'ℓ':>3} "
        f"{'Δ_bias(b=0)':>14} {'Δ_target(b=1)':>16} "
        f"{'|Δ_bias/Δ_target|':>20}"
    )
    print("-" * 90)
    last_k = None
    for r in rows:
        if "error" in r:
            print(
                f"{r['k']:>12.3e} {r['ell']:>3d}   (failed: {r['error']})"
            )
            continue
        if last_k is not None and r["k"] != last_k:
            print()
        last_k = r["k"]
        ratio_str = (
            f"{r['ratio_abs']:.3e}"
            if np.isfinite(r["ratio_abs"]) else "inf"
        )
        print(
            f"{r['k']:>12.3e} {r['ell']:>3d} "
            f"{r['delta_bias']:>14.6e} {r['delta_target']:>16.6e} "
            f"{ratio_str:>20}"
        )
    print("=" * 90)
    print(f"Total wall time: {elapsed_min:.2f} min")
    print()

    # Verdict heuristic per audit Report 2 §5.5.
    finite_ratios = [
        r["ratio_abs"]
        for r in rows
        if "error" not in r and np.isfinite(r["ratio_abs"])
    ]
    if finite_ratios:
        max_ratio = max(finite_ratios)
        max_locus = max(
            (r for r in rows if r.get("ratio_abs") == max_ratio),
            key=lambda r: 0,
        )
        print(
            f"Max |Δ_bias|/|Δ_target| across (k, ℓ): {max_ratio:.3e} "
            f"at k={max_locus['k']:.3e}, ℓ={max_locus['ell']}"
        )
        if max_ratio < 1e-3:
            print(
                "  >> Bias-floor CLOSED post-R10/R11 + post-R15-P0. "
                "The 6.43× residual is genuinely D-2, not floor leak."
            )
        elif max_ratio < 1e-1:
            print(
                "  >> Bias-floor SMALL but non-trivial. δ measurement "
                "should account for ~percent-level floor contamination "
                "at very-low k."
            )
        else:
            print(
                "  >> Bias-floor STILL LEAKS post-R11. A secondary "
                "amplitude-independent defect coexists with D-2; "
                "closing D-2 alone will not flip the closure xpass."
            )
    print()


if __name__ == "__main__":
    main()
