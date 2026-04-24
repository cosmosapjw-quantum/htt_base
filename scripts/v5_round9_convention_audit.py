"""V5-RUNTIME Round-9 R9-B convention audit.

Runs ``compute_flrw_d_ell_linear_probe`` on a small Planck-2018 k-grid and
prints ``D_2_probe / D_2_RouteB`` plus the implied ``B_K² ↔ ζ²`` calibration
factor needed to reconcile the two paths.

Route-B anchor: ``D_2 = 1002.086744 μK²`` (Planck-2018 FLRW).

The CLAssemblyConfig defaults to Planck-2018 P_R(k):
    A_s = 2.1e-9, n_s = 0.9649, k_pivot = 0.05 Mpc^-1.

If B_K² is the Lowell §13.2 unit-amplitude convention with B_K_sq = ζ²,
the ratio should be 1.0 (up to k-grid quadrature error). Any departure
gives the empirical conversion factor for R9-C.

Usage:
    venv/bin/python scripts/v5_round9_convention_audit.py
    venv/bin/python scripts/v5_round9_convention_audit.py --n-k 8 --probe 1.0
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np

ROUTE_B_D2_MUK2 = 1002.086744  # Planck-2018 anchor


def _log(msg: str) -> None:
    print(msg, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-k", type=int, default=6, help="k-grid size")
    parser.add_argument(
        "--k-min", type=float, default=1.0e-4, help="k_min in Mpc^-1"
    )
    parser.add_argument(
        "--k-max", type=float, default=1.0e-1, help="k_max in Mpc^-1"
    )
    parser.add_argument(
        "--probe", type=float, default=1.0, help="probe_b_k_sq amplitude"
    )
    parser.add_argument(
        "--n-workers", type=int, default=None, help="ProcessPool workers"
    )
    parser.add_argument(
        "--no-unit-amp-norm",
        action="store_true",
        help="Disable unit_amplitude_normalization (divide-by-seed_amp_floor)",
    )
    args = parser.parse_args(argv)

    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_flrw_d_ell_linear_probe,
    )
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    t0 = time.monotonic()
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log(f"  species ready in {time.monotonic() - t0:.2f} s")

    k_grid = np.logspace(
        np.log10(args.k_min), np.log10(args.k_max), args.n_k
    )
    _log(
        f"k-grid (N_k={args.n_k}, log-spaced): "
        f"k_min={k_grid[0]:.3e}, k_max={k_grid[-1]:.3e}"
    )
    _log(f"probe_b_k_sq = {args.probe} (Round-8 linear regime)")

    cfg = FLRWPipelineConfig(
        L_max_tower=4,
        ell_max_transfer=4,
        unit_amplitude_normalization=not args.no_unit_amp_norm,
    )
    _log(f"unit_amplitude_normalization = {cfg.unit_amplitude_normalization}")

    _log(
        f"Dispatching 2 × N_k = {2 * args.n_k} parallel solver runs..."
    )
    t0 = time.monotonic()
    bundle = compute_flrw_d_ell_linear_probe(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=cfg,
        probe_b_k_sq=args.probe,
        n_workers=args.n_workers,
    )
    dt = time.monotonic() - t0
    _log(f"  done in {dt:.1f} s")

    d_tt = bundle["d_tt"]
    cl_tt = bundle["cl_tt"]
    alphas = bundle["alpha_transfer_functions"]
    _log("")
    _log("α(k) per-k (T-monopole, ℓ=0..4):")
    for ki, (k_val, tf) in enumerate(zip(k_grid, alphas)):
        a = tf.delta_T_m0
        _log(
            f"  k={k_val:.3e}  α[ℓ=0]={a[0]: .3e}  α[ℓ=1]={a[1]: .3e}  "
            f"α[ℓ=2]={a[2]: .3e}  α[ℓ=3]={a[3]: .3e}  α[ℓ=4]={a[4]: .3e}"
        )
    _log("")
    _log("Per-ℓ output:")
    for ell in range(min(len(d_tt), 5)):
        _log(
            f"  ℓ={ell:2d}  C_ℓ^TT = {cl_tt[ell]: .6e}   "
            f"D_ℓ^TT = {d_tt[ell]: .6e} μK²"
        )

    d2_probe = float(d_tt[2])
    ratio = d2_probe / ROUTE_B_D2_MUK2
    _log("")
    _log("=" * 64)
    _log(f"R9-B convention audit:")
    _log(f"  D_2^probe       = {d2_probe:.6e} μK²")
    _log(f"  D_2^Route-B     = {ROUTE_B_D2_MUK2:.6e} μK²")
    _log(f"  D_2^probe / D_2^Route-B = {ratio:.6e}")
    _log("")
    _log("Calibration interpretation (B_K² = α(k) · ζ² mapping):")
    _log(
        f"  conversion_factor = sqrt(1 / ratio) = "
        f"{np.sqrt(1.0 / max(ratio, 1.0e-300)):.6e}"
    )
    _log(
        f"  [if ratio ≈ 1: B_K² = ζ², calibration trivial]"
    )
    _log(
        f"  [if ratio ≫ 1: B_K² is amplified vs ζ²; α(k) needs /sqrt(ratio)]"
    )
    _log(
        f"  [if ratio ≪ 1: B_K² is suppressed vs ζ²; α(k) needs sqrt(1/ratio)]"
    )
    _log("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
