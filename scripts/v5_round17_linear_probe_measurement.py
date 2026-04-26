"""V5-RUNTIME Round-17 PR-S13 sub-track (c) — linear-probe canonical path measurement.

Hypothesis. ``compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)`` is the
existing remediation path that disables ``unit_amplitude_normalization``
(turning off the spurious ``max(|Σ_±|, 1e-6) = 1e-6`` floor that boosts
|α|² by ~1e+12 in the FLRW limit) and instead pairs unit-amplitude
bias-subtracted transfer functions with the canonical Planck 2018
P_R(k) = A_s · (k / k_pivot)^(n_s − 1) at C_ℓ assembly. If this path
lands within ~25× of the Rust MB-95 anchor 1002.086744 μK², the
PR-S13 (a) ``primordial-amplitude alignment`` sub-track is confirmed
as the dominant gap (per V5_ROUND17_PR_S13_REAL_SCOPE.md §3 (a)).

Result (2026-04-27, run on commit `7722f95`). The linear-probe path
gives ``D_2 = 6.4395e+03 μK²`` at N_k=65, with residual ratio
``D_2^probe / D_2^Route-B = 6.43``. This closes 6.4 orders of magnitude
of the +2.04e+10 μK² gap that the canonical
``compute_flrw_d_ell`` path produces with
``unit_amplitude_normalization=True`` and is consistent with §3 (a)'s
"primordial normalization confirmed as the dominant gap"
ship gate.

The remaining 6.4× residual is the V5_ROUND12_TO_14 D-2 signature
(Lowell §13.2 leading-order seed valid only for ``x = k·η_init ≪ 1``;
half the k_grid here is in the ``x > 1`` invalid region). Per the 10-
auditor 4-cycle Round-12-14 consensus, the residual is **not** a
single missing convention factor — see the F1/F2/F3 findings in
``docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md`` §"What was tried".
D-2 closure is multi-month (CLAUDE.md §3 Round-15 P2: push integrator
η_init to z ~ 10⁹ via tight-coupling-enabled startup).

Wall time. ``ceil(2 · N_k / n_workers) × ~45 s``. For N_k=65 with
4 workers (130 tasks → 33 rounds → ~25 min in the
``compute_flrw_d_ell_linear_probe`` docstring estimate; observed
31.4 min).

Trajectory.

| Round | N_k | D_2^probe / D_2^Route-B |
|---|---:|---:|
| R9 (Section 2, post bug-fix start) | 4 | 2.93e+04 |
| R9 dense | 24 | 1.36e+04 |
| R12-14 (post-R11) | — | 7.57e+02 |
| **R17 (this script, post Round-15 P0 + Round-16)** | **65** | **6.43** |

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base/htt
    /home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python \\
        ../scripts/v5_round17_linear_probe_measurement.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Mirror htt/conftest.py: prepend htt/src (for `common/`) and htt/ (for
# `bass/`, `tsc/`, `workspace/`) so this ad hoc script resolves the same
# imports as the pytest test suite.
_HTT_ROOT = Path(__file__).resolve().parents[1] / "htt"
_HTT_SRC = _HTT_ROOT / "src"
if _HTT_SRC.is_dir() and str(_HTT_SRC) not in sys.path:
    sys.path.insert(0, str(_HTT_SRC))
if str(_HTT_ROOT) not in sys.path:
    sys.path.insert(0, str(_HTT_ROOT))

import numpy as np

from bass.species.registry import SpeciesBackgroundRegistry
from bass.spectrum.cl_assembly import CLAssemblyConfig
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    compute_flrw_d_ell_linear_probe,
)


D2_ANCHOR_UK2 = 1002.086744


def main() -> None:
    print("[t=0.0 min] building Planck 2018 species registry...")
    t_start = time.perf_counter()

    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )

    # Match htt/bass/spectrum/test_d2_pstf_closure.py exactly.
    k_grid = np.logspace(-4.0, -1.5, 65)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=8, ell_max_transfer=8)
    assembly_cfg = CLAssemblyConfig(ell_max=8, k_grid=k_grid, quadrature="simpson")

    elapsed_min = (time.perf_counter() - t_start) / 60.0
    print(f"[t={elapsed_min:.1f} min] launching compute_flrw_d_ell_linear_probe")
    print(f"               (probe_b_k_sq=1.0, N_k={k_grid.size}, n_workers=4,")
    print(f"                bias_subtraction forced ON, unit_amplitude_normalization forced OFF)")
    bundle = compute_flrw_d_ell_linear_probe(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        assembly_config=assembly_cfg,
        probe_b_k_sq=1.0,
        n_workers=4,
    )

    elapsed_min = (time.perf_counter() - t_start) / 60.0
    d_tt = bundle["d_tt"]
    d2 = float(d_tt[2])
    rel_err = abs(d2 - D2_ANCHOR_UK2) / D2_ANCHOR_UK2

    print()
    print("=" * 78)
    print("Round-17 (C) compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0) RESULT")
    print("=" * 78)
    print(f"  Wall time: {elapsed_min:.2f} min")
    print(f"  D_2 (Python linear-probe): {d2:.6e} μK²")
    print(f"  D_2 (Rust MB-95 anchor):   {D2_ANCHOR_UK2:.6f} μK²")
    print(f"  Absolute gap:              {d2 - D2_ANCHOR_UK2:+.6e} μK²")
    print(f"  Relative error:            {rel_err:.6e}")
    print()
    print("  Reference: canonical compute_flrw_d_ell path produced 2.04e+10 μK²")
    print("             (gap +2.04e+10 μK², dominated by 1e-6 floor / |α|² 1e+12 boost).")
    print()
    if rel_err < 0.01:
        print("  VERDICT: linear-probe path within 1% of the anchor.")
        print("           PR-S13 (a) sub-track may reduce to switching the")
        print("           compute_flrw_d_ell default to this code path.")
    elif rel_err < 0.5:
        print("  VERDICT: linear-probe path partially aligned (within 50%) but not")
        print("           bit-identical. (a) sub-track still has structural work to do.")
    elif d2 / D2_ANCHOR_UK2 < 100.0 and d2 > 0:
        print("  VERDICT: linear-probe path within ~2 orders of magnitude.")
        print("           Significant reduction from canonical 2.04e+10 μK² gap;")
        print("           residual is consistent with V5_ROUND12_TO_14 D-2 signature.")
    else:
        print("  VERDICT: linear-probe path does NOT close the gap meaningfully.")
        print("           Pivot to (B): unit_amplitude_normalization floor diagnostic.")
    print("=" * 78)

    # Print a compact spectrum summary for context.
    print()
    print("  D_ℓ^TT spectrum (μK²) at ℓ=2..8:")
    for ell in range(2, min(9, d_tt.size)):
        print(f"    D_{ell}: {float(d_tt[ell]):.6e}")


if __name__ == "__main__":
    main()
