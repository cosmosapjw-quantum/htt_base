"""V5-RUNTIME Round-12 Phase B-fix: CAMB comparison with n_output sweep.

Following the Round-13 audit (3/3 REFUTED Option A) and the
Phase B-fix CAMB comparison (per-(k, ℓ) ratio std/mean = 109% — no
clean 4√2), this script tests Opus's η-grid undersampling hypothesis:
re-measure BASS α(k, ℓ) at n_output ∈ {64, 256, 1024} and compare to
CAMB Δ_T(ℓ, k) per-mode.

If raising n_output collapses the per-(k, ℓ) discrepancy:
  → η-grid undersampling is dominant; fix = raise n_output default
If discrepancy persists at n_output=256+:
  → η-grid is not the dominant root cause; need component ablation
    (Option II) to localize Doppler / ISW / source extractor

Wall time: ~10-15 min (CAMB ~30s + BASS at 3 n_output × 4 k × 2 (bias)
× per-solver scaling with n_output).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np


def _hr(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}", flush=True)


def _log(msg: str = "") -> None:
    print(msg, flush=True)


def get_camb_transfer():
    """CAMB Δ_T(ℓ, k) interpolators for ℓ ∈ {2, 3, 4}, Planck-2018 + tau≈0."""
    import camb
    from scipy.interpolate import interp1d

    _hr("CAMB Planck-2018 setup (tau=1e-5, matching MB-95 anchor)")
    pars = camb.set_params(
        H0=67.36, ombh2=0.02237, omch2=0.12, mnu=0.06, omk=0,
        tau=1.0e-5, As=2.1e-9, ns=0.9649,
    )
    pars.set_for_lmax(10, lens_potential_accuracy=0)
    pars.WantTransfer = True
    t0 = time.monotonic()
    results = camb.get_results(pars)
    trans = results.get_cmb_transfer_data(tp='scalar')
    _log(f"CAMB done in {time.monotonic() - t0:.2f} s, q range "
         f"[{trans.q[0]:.2e}, {trans.q[-1]:.2e}]")
    delta_T_lk = trans.delta_p_l_k[0]
    L_arr = trans.L
    q_arr = trans.q
    interps = {}
    for ell in (2, 3, 4):
        l_idx = np.where(L_arr == ell)[0]
        if len(l_idx) == 0:
            continue
        interps[ell] = interp1d(
            np.log(q_arr), delta_T_lk[int(l_idx[0]), :],
            kind='cubic', bounds_error=False, fill_value=np.nan,
        )
    return interps


def get_bass_alpha(species, ks: list[float], n_output: int) -> dict:
    """BASS α(k, ℓ) at given n_output, ℓ ∈ {0..4}."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_linear_probe_transfer_function,
    )
    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
        n_output=n_output,
    )
    out: dict = {}
    for k in ks:
        t0 = time.monotonic()
        alpha_tf = compute_linear_probe_transfer_function(
            species, k, config=cfg, probe_b_k_sq=1.0,
        )
        dt = time.monotonic() - t0
        out[k] = np.asarray(alpha_tf.delta_T_m0, dtype=np.float64)
        _log(f"  k={k:.3e}, n_out={n_output}: done in {dt:.1f} s, "
             f"α[ℓ=2]={out[k][2]:+.4e}")
    return out


def report_per_kl_table(label: str, bass_alpha: dict, interps: dict, ks: list[float]) -> None:
    _log(f"\n--- {label} ---")
    _log(f"  {'k [Mpc⁻¹]':>10s}  {'ℓ':>2s}  "
         f"{'BASS α':>14s}  {'CAMB Δ_T':>14s}  "
         f"{'ratio':>10s}  {'sqrt|r|':>9s}")
    _log("  " + "-" * 70)
    ratios_per_ell = {2: [], 3: [], 4: []}
    for k in ks:
        alpha_arr = bass_alpha[k]
        for ell in (2, 3, 4):
            if ell not in interps:
                continue
            camb_delta = float(interps[ell](np.log(k)))
            bass_a = float(alpha_arr[ell])
            ratio = bass_a / camb_delta if abs(camb_delta) > 1e-30 else float('nan')
            sqrt_r = float(np.sqrt(abs(ratio))) if not np.isnan(ratio) else float('nan')
            _log(
                f"  {k:>10.3e}  {ell:>2d}  "
                f"{bass_a:>+14.6e}  {camb_delta:>+14.6e}  "
                f"{ratio:>+10.4f}  {sqrt_r:>9.4f}"
            )
            if not np.isnan(ratio):
                ratios_per_ell[ell].append(ratio)
    _log(f"\n  Per-ℓ summary across k:")
    for ell, ratios in ratios_per_ell.items():
        if not ratios:
            continue
        rv = np.array(ratios)
        _log(f"    ℓ={ell}: mean = {np.mean(rv):+8.4f},  std = {np.std(rv):8.4f},  "
             f"std/|mean| = {np.std(rv) / max(abs(np.mean(rv)), 1e-30):.2%}")


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.")

    bass_ks = [1.0e-3, 1.0e-2, 3.0e-2, 5.0e-2]
    interps = get_camb_transfer()

    n_outputs = [64, 256, 1024]
    all_alpha: dict = {}
    for n_out in n_outputs:
        _hr(f"BASS linear-probe at n_output = {n_out}")
        all_alpha[n_out] = get_bass_alpha(species, bass_ks, n_out)

    _hr("Per-(k, ℓ) ratio: BASS α / CAMB Δ_T (n_output sweep)")
    for n_out in n_outputs:
        report_per_kl_table(
            f"n_output = {n_out}",
            all_alpha[n_out],
            interps, bass_ks,
        )

    _hr("Per-(k, ℓ) BASS-vs-BASS comparison (n_output convergence)")
    _log(f"  {'k':>10s}  {'ℓ':>2s}  "
         f"{'α(64)':>12s}  {'α(256)':>12s}  {'α(1024)':>12s}  "
         f"{'256/64':>10s}  {'1024/256':>10s}")
    for k in bass_ks:
        for ell in (2, 3, 4):
            a64 = float(all_alpha[64][k][ell])
            a256 = float(all_alpha[256][k][ell])
            a1024 = float(all_alpha[1024][k][ell])
            r1 = a256 / a64 if abs(a64) > 1e-30 else float('nan')
            r2 = a1024 / a256 if abs(a256) > 1e-30 else float('nan')
            _log(
                f"  {k:>10.3e}  {ell:>2d}  "
                f"{a64:>+12.4e}  {a256:>+12.4e}  {a1024:>+12.4e}  "
                f"{r1:>+10.4f}  {r2:>+10.4f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
