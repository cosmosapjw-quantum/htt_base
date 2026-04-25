"""V5-RUNTIME Round-12 Phase B-fix CAMB direct comparison.

After 4√2 trial calibration in `v5_round13_phase_b_diagnostics.py` D7
gave D_2 ratio = 1.005 (sub-horizon only) — confirming Codex auditor's
``sqrt(32) = 4√2`` PSTF normalization hypothesis empirically.

Code archaeology revealed BASS Q-17 audit comment: ``σ_γ = 2·Θ_2``
combined with MB95 eq. 22a (``σ_γ = F_2/2``) gives **BASS Θ_ℓ = F_ℓ_MB / 4**
for ℓ ≥ 1. That accounts for factor 4. The √2 origin is unclear without
direct comparison.

This script does the cleanest possible test: extract CAMB Δ_T(ℓ, k) at
matching k values and compare per-(k, ℓ) with BASS α_meas to nail down
the exact convention factor.

Cosmology: Planck-2018 baseline (H0=67.36, ombh2=0.02237, omch2=0.12,
mnu=0.06, omk=0, As=2.1e-9, ns=0.9649). Reionization tau set to 1e-5
(essentially zero, matches MB-95 sync-gauge production).

Wall time: ~3 min (CAMB fast + 5 BASS solver runs ~225 s).
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
    """Set up CAMB with Planck-2018 + tau=0 baseline; return interpolators
    Δ_T(ℓ, k) for ℓ ∈ {2, 3, 4} via SciPy interp1d in log(k)."""
    import camb
    from scipy.interpolate import interp1d

    _hr("CAMB Planck-2018 setup (tau=1e-5, matching BASS MB-95 baseline)")
    pars = camb.set_params(
        H0=67.36, ombh2=0.02237, omch2=0.12, mnu=0.06, omk=0,
        tau=1.0e-5, As=2.1e-9, ns=0.9649,
    )
    pars.set_for_lmax(10, lens_potential_accuracy=0)
    pars.WantTransfer = True

    t0 = time.monotonic()
    results = camb.get_results(pars)
    trans = results.get_cmb_transfer_data(tp='scalar')
    dt = time.monotonic() - t0
    _log(f"CAMB compute done in {dt:.2f} s")
    _log(f"  L range:  {int(trans.L[0])} to {int(trans.L[-1])} ({len(trans.L)} values)")
    _log(f"  q range:  {trans.q[0]:.3e} to {trans.q[-1]:.3e} Mpc⁻¹ ({len(trans.q)} values)")
    _log(f"  delta_p_l_k shape: {trans.delta_p_l_k.shape}")

    # source 0 = temperature
    delta_T_lk = trans.delta_p_l_k[0]  # shape (n_l, n_q)
    L_arr = trans.L
    q_arr = trans.q

    # Build interpolator per ℓ
    interps = {}
    for ell in (2, 3, 4):
        l_idx = np.where(L_arr == ell)[0]
        if len(l_idx) == 0:
            _log(f"  ℓ={ell} not in CAMB L array — skipping")
            continue
        l_idx = int(l_idx[0])
        delta_at_l = delta_T_lk[l_idx, :]  # shape (n_q,)
        # interp in log-k for stability
        valid = q_arr > 0
        interps[ell] = interp1d(
            np.log(q_arr[valid]), delta_at_l[valid],
            kind='cubic', bounds_error=False, fill_value=np.nan,
        )

    return interps, q_arr


def get_bass_alpha(species, ks: list[float]) -> dict:
    """Run BASS linear-probe at multiple k, return α(k, ℓ) for ℓ ∈ {0..4}.
    Reuses scripts/v5_round9_per_k_diagnostic.py logic."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_linear_probe_transfer_function,
    )

    _hr("BASS linear-probe extraction")
    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
    )

    alpha_dict: dict = {}
    for k in ks:
        _log(f"\n--- k = {k:.3e} Mpc⁻¹ ---")
        t0 = time.monotonic()
        alpha_tf = compute_linear_probe_transfer_function(
            species, k, config=cfg, probe_b_k_sq=1.0,
        )
        dt = time.monotonic() - t0
        delta_T_m0 = np.asarray(alpha_tf.delta_T_m0, dtype=np.float64)
        _log(
            f"  done in {dt:.1f} s, "
            f"α[ℓ=0..4] = "
            + ", ".join(f"{v:+.3e}" for v in delta_T_m0)
        )
        alpha_dict[k] = delta_T_m0

    return alpha_dict


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.")

    # CAMB k range goes up to ~0.085 — pick BASS k values within that
    bass_ks = [1.0e-3, 1.0e-2, 3.0e-2, 5.0e-2]

    interps, camb_q = get_camb_transfer()
    bass_alpha = get_bass_alpha(species, bass_ks)

    _hr("Per-(k, ℓ) ratio: BASS α_meas vs CAMB Δ_T")
    _log(f"  {'k [Mpc⁻¹]':>10s}  {'ℓ':>2s}  "
         f"{'BASS α':>14s}  {'CAMB Δ_T':>14s}  "
         f"{'ratio':>10s}  {'sqrt(|ratio|²)':>14s}")
    _log("  " + "-" * 70)

    ratios_per_ell = {2: [], 3: [], 4: []}
    for k in bass_ks:
        alpha_arr = bass_alpha[k]
        for ell in (2, 3, 4):
            if ell not in interps:
                continue
            camb_delta = float(interps[ell](np.log(k)))
            bass_alpha_val = float(alpha_arr[ell])
            ratio = (bass_alpha_val / camb_delta) if abs(camb_delta) > 1e-30 else float('nan')
            sqrt_ratio = np.sqrt(abs(ratio)) if not np.isnan(ratio) else float('nan')
            _log(
                f"  {k:>10.3e}  {ell:>2d}  "
                f"{bass_alpha_val:>+14.6e}  {camb_delta:>+14.6e}  "
                f"{ratio:>+10.4f}  {sqrt_ratio:>14.4f}"
            )
            if not np.isnan(ratio):
                ratios_per_ell[ell].append((k, ratio))

    _hr("Summary: ratio per ℓ across k")
    for ell, ratios in ratios_per_ell.items():
        if not ratios:
            continue
        ratio_vals = np.array([r for _, r in ratios])
        mean_ratio = float(np.mean(ratio_vals))
        std_ratio = float(np.std(ratio_vals))
        sqrt_mean = float(np.sqrt(abs(mean_ratio)))
        _log(
            f"  ℓ={ell}:  mean ratio = {mean_ratio:+.4f}  std = {std_ratio:.4f}  "
            f"|ratio_mean|^(1/2) = {sqrt_mean:.4f}"
        )

    _log("\nConvention factor candidates:")
    _log(f"  4·sqrt(2) = {4 * np.sqrt(2):.6f}")
    _log(f"  sqrt(32)  = {np.sqrt(32):.6f}")
    _log(f"  sqrt(24)  = {np.sqrt(24):.6f}  (PSTF spin-2 = 2√6)")
    _log(f"  16/3      = {16/3:.6f}")
    _log(f"  4         = {4.0:.6f}  (BASS Θ_ℓ = F_ℓ_MB / 4)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
