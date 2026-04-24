"""V5-RUNTIME Round-9 R9-D bias-floor probe.

Runs ``compute_transfer_function_at_k`` directly with
``primordial_b_k_sq = 0`` at a super-horizon k-grid to measure the
visibility-source bias floor Δ_bias(k, ℓ) — the seed-independent
contribution from the amplitude-independent ν π/G_3 terms in the
Lowell §13.2 startup formulas.

R9-D 5-k sweep found `α_meas(ℓ=2)` constant at ~10 across `k = 1e-5
… 1e-4`, instead of the canonical `k²` super-horizon decay. Three
hypotheses for this 1/k² ratio scaling vs SW prediction; this script
tests **hypothesis 1**: the bias floor dominates the linear-probe
extraction at small k. Specifically: if `|Δ_bias(k, ℓ)|` is
comparable to or larger than `|α(k, ℓ) × probe_b_k_sq|` at small k,
the bias subtraction is subtracting two numerically-equal terms and
the "linear coefficient" is noise.

Usage:
    venv/bin/python scripts/v5_round9_bias_floor_probe.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np


def _log(msg: str) -> None:
    print(msg, flush=True)


# Comparison anchors from the R9-D 5-k sweep (commit 36ec8e9):
#   α_meas(ℓ=2) at probe_b_k_sq=1.0
ALPHA_AT_PROBE_1: dict[float, dict[int, float]] = {
    1.0e-5: {0: -8.6357e+03, 1: -3.5592e+02, 2: -8.8255e+00, 3: -1.5641e-01, 4: -2.1549e-03},
    3.0e-5: {0: -1.1065e+03, 1: -1.3971e+02, 2: -1.0565e+01, 3: -5.7050e-01, 4: -2.3951e-02},
    1.0e-4: {0: -8.3930e+01, 1: -3.9517e+01, 2: -1.0454e+01, 3: -1.9360e+00, 4: -2.7636e-01},
    3.0e-4: {0:  1.2979e+00, 1: -1.7078e+00, 2: -2.6978e+00, 3: -1.9315e+00, 4: -9.4305e-01},
    1.0e-3: {0:  7.0042e-03, 1:  6.9675e-02, 2:  1.2718e-02, 3: -6.2016e-02, 4: -4.3404e-02},
}


def main() -> int:
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_transfer_function_at_k,
    )
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()

    cfg = FLRWPipelineConfig(
        L_max_tower=4,
        ell_max_transfer=4,
        primordial_b_k_sq=0.0,
        unit_amplitude_normalization=False,
    )
    _log("Config: primordial_b_k_sq=0.0 (bias-only), unit_amp_norm=False")
    _log("")

    ks = sorted(ALPHA_AT_PROBE_1.keys())
    rows: list[dict[str, object]] = []
    for k_mpc in ks:
        _log(f"--- k = {k_mpc:.3e} Mpc^-1 (bias-only, b_k_sq=0) ---")
        t0 = time.monotonic()
        bias_tf = compute_transfer_function_at_k(species, k_mpc, config=cfg)
        dt = time.monotonic() - t0
        _log(f"  solver done in {dt:.1f} s")
        for ell in range(5):
            d_bias = float(bias_tf.delta_T_m0[ell])
            alpha = ALPHA_AT_PROBE_1[k_mpc][ell]
            target = alpha + d_bias
            ratio = abs(d_bias) / max(abs(target), 1.0e-30)
            _log(
                f"  ℓ={ell:1d}  Δ_bias={d_bias: .4e}  "
                f"Δ_target={target: .4e}  α={alpha: .4e}  "
                f"|Δ_bias|/|Δ_target|={ratio: .4f}"
            )
            rows.append(
                {
                    "k_mpc": float(k_mpc),
                    "ell": ell,
                    "Delta_bias": d_bias,
                    "Delta_target": target,
                    "alpha": alpha,
                    "bias_fraction": ratio,
                }
            )
        _log("")

    _log("=" * 84)
    _log("Bias-vs-target dominance map (focus on ℓ=2):")
    _log(
        f"  {'k_mpc':>10s}  {'Δ_bias(ℓ=2)':>14s}  "
        f"{'Δ_target(ℓ=2)':>14s}  {'α(ℓ=2)':>14s}  "
        f"{'|Δ_b|/|Δ_t|':>12s}"
    )
    for row in rows:
        if row["ell"] != 2:
            continue
        _log(
            f"  {row['k_mpc']:>10.3e}  {row['Delta_bias']:>14.4e}  "
            f"{row['Delta_target']:>14.4e}  {row['alpha']:>14.4e}  "
            f"{row['bias_fraction']:>12.4f}"
        )
    _log("=" * 84)
    _log("Interpretation:")
    _log("  - |Δ_bias|/|Δ_target| ≈ 1: bias DOMINATES; linear extraction")
    _log("    is differencing two numerically-equal terms → noise.")
    _log("  - |Δ_bias|/|Δ_target| ≪ 1: bias is a small correction;")
    _log("    α extraction is reliable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
