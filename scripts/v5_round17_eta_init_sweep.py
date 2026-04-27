"""V5-RUNTIME Round-17 audit follow-up — η_init sweep counter-test for D-2.

This is V0d in `docs/V5_ROUND17_AUDIT_VERDICT_AND_REVISED_PLAN.md §5.1`.
Both external auditors (Report 2 §2.3, Report 1 Test C) recommended this
counter-test as the cheapest GO/NO-GO gate for the multi-month δ
sub-track BEFORE committing to it.

Hypothesis. If D-2 (Lowell §13.2 leading-order seed validity at
sub-horizon ``x = k·η_init``) is the dominant cause of the 6.43×
linear-probe residual, then shrinking η_init at fixed k-grid should
collapse the residual monotonically: at η_init ≈ 30 Mpc the validity
boundary k_crit = 1/η_init ≈ 0.033 Mpc⁻¹ exceeds the test grid's
k_max = 0.0316 Mpc⁻¹, so the entire k-grid lands in valid Lowell
territory and `D_2/D_anchor → ~1`.

Counter-test design.
  - Sweep η_init ∈ {261, 200, 150, 100, 70, 50} Mpc.
  - For each, run `compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)`
    on the same N_k=65 k-grid as `htt/bass/spectrum/test_d2_pstf_closure.py`.
  - Override `IntegratorConfig.eta_initial_mpc` via a monkey-patch on
    `build_cosmological_integrator_config` so the rest of the pipeline
    (species table, source extractor, LoS projector, C_ℓ assembly) is
    untouched.
  - Tabulate `D_2(η_init)`, `D_2 / D_anchor`, `x_max = k_max · η_init`.

Predictions.
  - D-2 confirmed: ratio drops monotonically from ≈ 6.43 (η_init = 261)
    toward ≈ 1.0 (η_init ≈ 30-50). Power-law slope on log-log axes.
  - D-2 not dominant: ratio sticks near 6.43 across the sweep, or moves
    in the wrong direction.

GO/NO-GO criterion (audit Report 2): at η_init ≈ 50 Mpc, ratio ≤ 2 →
D-2 confirmed, δ proceed; ratio still > 5 → D-2 not dominant, replan
δ scope before committing multi-month effort.

Wall time. ~3 h on 4 workers (6 sweeps × ~31 min each, sequential).
Run in background; check periodically.

Caveat. The species background table covers the full η range of the
sweep; HYREC visibility is centered at recombination (η ≈ 281 Mpc) and
remains finite-but-small for η < 281. The Round-15 P0 LoS grid builder
adapts to k automatically. The integrator's internal `_approx_tau_c`
heuristic at `regular_adiabatic_ic.py:94-101` is a placeholder; below
η_init ≈ 50 Mpc its inaccuracy may inject a separate small defect,
which is why the sweep stops at 50 Mpc (per Report 2 §2.3).

Usage::

    cd /home/cosmosapjw/Dropbox/bianchi/htt_base
    venv/bin/python scripts/v5_round17_eta_init_sweep.py
"""
from __future__ import annotations

import os

# Round-17 P3.5 perf: cap BLAS threads at 1 BEFORE numpy import so that
# 24 ProcessPoolExecutor workers don't each spawn ~12-24 OpenBLAS
# threads (default MAX_THREADS=64 → ~288 threads on 24 cores → context-
# switching kills throughput). Per-worker single-threaded BLAS lets
# the cores cleanly partition across the bias-subtraction tasks.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import dataclasses
import sys
import time
from pathlib import Path

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

ETA_INIT_SWEEP_MPC = (261.0, 200.0, 150.0, 100.0, 70.0, 50.0)


def _patched_builder_factory(eta_init_override_mpc: float):
    """Return a `build_cosmological_integrator_config` replacement that
    forces `eta_initial_mpc = eta_init_override_mpc` while preserving
    every other field the production builder produces.
    """
    from bass.runtime import (
        build_cosmological_integrator_config as _orig_builder,
    )

    def _patched(species, **kwargs):
        base_cfg = _orig_builder(species, **kwargs)
        return dataclasses.replace(
            base_cfg, eta_initial_mpc=float(eta_init_override_mpc),
        )

    return _patched


def main() -> None:
    print("[t=0.0 min] V5 Round-17 V0d — η_init sweep counter-test")
    print("            building Planck 2018 species registry...")
    t_start = time.perf_counter()

    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )

    # Match htt/bass/spectrum/test_d2_pstf_closure.py k-grid exactly.
    k_grid = np.logspace(-4.0, -1.5, 65)
    # Round-17 P3.5 perf: production tolerances preserved (rtol=1e-4
    # was tested and gave 2× D_2 drift; LSODA's adaptive step-size
    # picks the same wrong-bucket path at any rtol > 1e-6 for this
    # problem). The 1.7× speedup vs 4-worker baseline comes purely from
    # n_workers=None (auto = 24 on Ryzen 9 5900X) plus the OpenBLAS
    # thread cap set at script top.
    pipeline_cfg = FLRWPipelineConfig(
        L_max_tower=8,
        ell_max_transfer=8,
    )
    assembly_cfg = CLAssemblyConfig(
        ell_max=8, k_grid=k_grid, quadrature="simpson",
    )

    results = []

    # We monkeypatch in `bass.spectrum.flrw_pipeline` because that's
    # the import-binding the production callers see.
    import bass.spectrum.flrw_pipeline as flrw_pipeline_module

    for eta_init_mpc in ETA_INIT_SWEEP_MPC:
        elapsed_min = (time.perf_counter() - t_start) / 60.0
        x_max = float(k_grid.max()) * eta_init_mpc
        print(
            f"[t={elapsed_min:.1f} min] η_init = {eta_init_mpc:.1f} Mpc; "
            f"x_max = k_max · η_init = {x_max:.3f}"
        )

        # Patch the import-bound builder for this sweep entry.
        original = flrw_pipeline_module.build_cosmological_integrator_config
        flrw_pipeline_module.build_cosmological_integrator_config = (
            _patched_builder_factory(eta_init_mpc)
        )
        try:
            bundle = compute_flrw_d_ell_linear_probe(
                species,
                k_grid_mpc=k_grid,
                pipeline_config=pipeline_cfg,
                assembly_config=assembly_cfg,
                probe_b_k_sq=1.0,
                # Round-17 P3.5 perf: auto-detect cpu_count (24 on
                # Ryzen 9 5900X) instead of hard-coded 4-worker.
                # Bias-subtraction dispatches 2·N_k = 130 tasks per
                # sweep; with 24 workers that's ~6 rounds vs 33 at 4w.
                n_workers=None,
            )
            d_tt = bundle["d_tt"]
            d2 = float(d_tt[2])
            ratio = d2 / D2_ANCHOR_UK2
            results.append(
                {
                    "eta_init_mpc": eta_init_mpc,
                    "x_max": x_max,
                    "d2_uK2": d2,
                    "ratio": ratio,
                }
            )
            print(
                f"               D_2 = {d2:.6e} μK²   ratio = {ratio:.3f}"
            )
        except Exception as exc:  # noqa: BLE001
            print(
                f"               FAILED: {type(exc).__name__}: {exc}"
            )
            results.append(
                {
                    "eta_init_mpc": eta_init_mpc,
                    "x_max": x_max,
                    "d2_uK2": float("nan"),
                    "ratio": float("nan"),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        finally:
            flrw_pipeline_module.build_cosmological_integrator_config = (
                original
            )

    elapsed_min = (time.perf_counter() - t_start) / 60.0

    print()
    print("=" * 78)
    print("V5 Round-17 V0d — η_init sweep RESULT TABLE")
    print("=" * 78)
    print(
        f"{'η_init [Mpc]':>14}  {'x_max':>8}  "
        f"{'D_2 [μK²]':>14}  {'D_2/anchor':>12}"
    )
    print("-" * 78)
    for row in results:
        if "error" in row:
            print(
                f"{row['eta_init_mpc']:>14.1f}  {row['x_max']:>8.3f}  "
                f"{'(failed)':>14}  {'(failed)':>12}"
            )
        else:
            print(
                f"{row['eta_init_mpc']:>14.1f}  {row['x_max']:>8.3f}  "
                f"{row['d2_uK2']:>14.4e}  {row['ratio']:>12.4f}"
            )
    print("=" * 78)
    print(f"Total wall time: {elapsed_min:.1f} min")
    print()

    # Verdict heuristic — matches audit Report 2 §2.3 GO/NO-GO criterion.
    finite_results = [r for r in results if "error" not in r]
    if len(finite_results) >= 2:
        ratios = [r["ratio"] for r in finite_results]
        eta_inits = [r["eta_init_mpc"] for r in finite_results]
        # Monotone decrease (within tolerance) check.
        deltas = [
            ratios[i + 1] - ratios[i] for i in range(len(ratios) - 1)
        ]
        monotone_decrease = all(d <= 1e-6 for d in deltas)

        # GO/NO-GO at η_init ≈ 50 Mpc (Report 2 §2.3): ratio ≤ 2 → confirm.
        last_ratio = ratios[-1]
        last_eta = eta_inits[-1]

        print("Verdict heuristics:")
        print(
            f"  Monotone collapse with shrinking η_init: "
            f"{'YES' if monotone_decrease else 'NO'}"
        )
        print(
            f"  Final ratio at η_init = {last_eta:.0f} Mpc: "
            f"{last_ratio:.3f}"
        )
        if last_ratio <= 2.0 and monotone_decrease:
            print("  >> D-2 CONFIRMED. δ sub-track GO.")
        elif last_ratio <= 5.0 and monotone_decrease:
            print(
                "  >> D-2 PARTIAL. ratio collapsing but not yet near 1; "
                "extend sweep below 50 Mpc OR couple with D-3 closure."
            )
        else:
            print(
                "  >> D-2 NOT DOMINANT. δ as-planned does NOT close the "
                "residual; replan before committing multi-month work."
            )
    print()


if __name__ == "__main__":
    main()
