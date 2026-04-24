"""V5-RUNTIME Round-9 R9-D per-k diagnostic.

For a single k value (or short list), runs the linear-probe extraction
and compares the measured α(k, ℓ) against the analytic Sachs-Wolfe
prediction:

    T_SW(k, ℓ) = -(1/5) · j_ℓ(k · (η_0 − η_*))

(Pure SW, no ISW / Doppler / acoustic correction; exact only in the
matter-dominated era for super-horizon modes.) The ratio α / T_SW
isolates the convention factor without the N_k quadrature artefact
present in the C_ℓ-summed audit, and is the cleanest empirical
diagnostic for closing the R9-B/D B_K² ↔ ζ² convention.

Cosmological anchors (Planck-2018):
    η_*       ≈ 281 Mpc  (z_* = 1089.94)
    η_today   ≈ 14147 Mpc
    η_0 − η_* ≈ 13866 Mpc

Usage:
    venv/bin/python scripts/v5_round9_per_k_diagnostic.py
    venv/bin/python scripts/v5_round9_per_k_diagnostic.py --k 1e-3
    venv/bin/python scripts/v5_round9_per_k_diagnostic.py --probe 1.0 --ks 1e-4 1e-3 5e-2
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
from scipy.special import spherical_jn


def _log(msg: str) -> None:
    print(msg, flush=True)


def t_sw_prediction(k_mpc: float, ell: int, *, eta_los: float) -> float:
    """Sachs-Wolfe-only transfer prediction.

    Δ_ℓ^SW(k) ≈ -(1/5) · ζ · j_ℓ(k · (η_0 - η_*))

    Returns the transfer per unit ζ — i.e., α_SW(k, ℓ).
    """
    arg = float(k_mpc) * float(eta_los)
    return -0.2 * float(spherical_jn(int(ell), arg))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ks",
        type=float,
        nargs="+",
        default=[1.0e-4, 1.0e-3, 5.0e-2],
        help="k values in Mpc^-1 to probe",
    )
    parser.add_argument(
        "--probe", type=float, default=1.0, help="probe_b_k_sq amplitude"
    )
    args = parser.parse_args(argv)

    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_linear_probe_transfer_function,
    )
    from bass.species.registry import SpeciesBackgroundRegistry
    from bass.runtime.cosmological_config import cosmological_critical_etas

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()

    anchors = cosmological_critical_etas(species)
    eta_star = float(anchors["eta_star"])
    eta_today = float(anchors["eta_today"])
    eta_los = eta_today - eta_star
    _log(
        f"Cosmological anchors: η_* = {eta_star:.2f} Mpc, "
        f"η_today = {eta_today:.2f} Mpc, η_LoS = {eta_los:.2f} Mpc"
    )
    _log(f"probe_b_k_sq = {args.probe}")
    _log("")

    # Force unit_amplitude_normalization=False for the diagnostic — the
    # default True divides by the seed-amp floor 1e-6 and inflates α by
    # ~1e+6 (R9-A/B finding). The new wrapper does this automatically;
    # the standalone single-k API does not, so we set it explicitly here.
    cfg = FLRWPipelineConfig(
        L_max_tower=4,
        ell_max_transfer=4,
        unit_amplitude_normalization=False,
    )

    rows: list[dict[str, float]] = []
    for k_mpc in args.ks:
        _log(f"--- k = {k_mpc:.3e} Mpc^-1 ---")
        t0 = time.monotonic()
        alpha = compute_linear_probe_transfer_function(
            species, k_mpc, config=cfg, probe_b_k_sq=args.probe
        )
        dt = time.monotonic() - t0
        _log(f"  solver done in {dt:.1f} s")
        for ell in range(5):
            measured = float(alpha.delta_T_m0[ell])
            predicted = t_sw_prediction(k_mpc, ell, eta_los=eta_los)
            ratio = measured / predicted if abs(predicted) > 1.0e-30 else float("nan")
            _log(
                f"  ℓ={ell:1d}  α_meas={measured: .4e}  "
                f"α_SW={predicted: .4e}  ratio={ratio: .4e}"
            )
            rows.append(
                {
                    "k_mpc": float(k_mpc),
                    "ell": ell,
                    "measured": measured,
                    "predicted": predicted,
                    "ratio": ratio,
                }
            )

    _log("")
    _log("=" * 64)
    _log("Per-k summary table (α_meas / α_SW):")
    _log(f"  {'k_mpc':>10s}  {'ℓ':>2s}  {'α_meas':>14s}  {'α_SW':>14s}  {'ratio':>14s}")
    for row in rows:
        _log(
            f"  {row['k_mpc']:>10.3e}  {row['ell']:>2d}  "
            f"{row['measured']:>14.4e}  {row['predicted']:>14.4e}  "
            f"{row['ratio']:>14.4e}"
        )
    _log("=" * 64)
    _log("Interpretation:")
    _log("  - If ratios cluster around a single constant: that's the")
    _log("    convention factor (B_K_sq → ζ scale).")
    _log("  - If ratios vary by ℓ at fixed k: the SW approximation is")
    _log("    inadequate (need full ISW + Doppler + acoustic prediction).")
    _log("  - If ratios vary by k: the convention is k-dependent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
