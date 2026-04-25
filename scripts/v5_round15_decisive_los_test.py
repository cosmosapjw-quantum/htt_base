"""V5-RUNTIME Round-15 §10 decisive 1-hour test (per Claude Opus R14 audit).

After 4 audit cycles converged on the diagnosis "three independent
defects (D-1, D-2, D-3)" but no path to a single fix, this test
isolates whether the BASS LoS projector + grid is healthy enough to
reproduce CAMB Δ_T given the *correct* CAMB-computed source. If yes,
defect is 100% in `tier_b_source_extraction.py` (D-2 + D-3); if no,
D-1 (LoS grid) is also contributing.

CAMB is used as **audit oracle only** — no production code dependency.

Test design:

  Step 1  Extract CAMB's already-computed Newtonian-gauge LoS source
          T_source(η, k) at Planck-2018 cosmology, on a fine η-grid
          interpolated to the BASS integrator η-grid (n_output=64,
          uniform-linear from η_init=260 to η_today=14147).

  Step 2  Wrap the CAMB T_source as a callable and pass through
          BASS's existing project_temperature_transfer routine
          (np.trapezoid on 64 points). The Bessel kernel and
          quadrature are byte-identical to the BASS native pipeline;
          only the source values differ (CAMB instead of BASS).

  Step 3  Compare per-(k, ℓ):
            α_camb_source_bass_grid(k, ℓ)  -- new
            α_camb_direct(k, ℓ)            -- CAMB's own Δ_T
            α_bass_native(k, ℓ)            -- existing BASS pipeline

Cases:
  A  α_camb_source_bass_grid ≈ α_camb_direct (≤ 5%) at all (k, ℓ)
     → BASS LoS projector + grid is healthy
     → defect is 100% in BASS source extraction (D-2 + D-3)
     → Round-15 priority: D-3 first (sub-week), D-2 next (multi-month)

  B  α_camb_source_bass_grid 10-100× larger than α_camb_direct at
     sub-horizon
     → D-1 (LoS undersampling) is dominant
     → Round-15 priority: D-1 first (1-2 weeks), then D-3, D-2

  C  Low-k matches CAMB, high-k diverges
     → D-1 dominates at high k, source extraction at low k
     → Round-15 priority: D-1 + D-3 in parallel

  D  Sign flips appear in α_camb_source_bass_grid relative to direct
     → D-1 severity confirmed (220 Mpc grid on 19 Mpc visibility FWHM)
     → Round-15 priority: D-1 critical first

Wall time: ~3 minutes (CAMB ~30s, BASS ~3 minutes for 4 k native runs).
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


def get_camb_results():
    """Set up CAMB at Planck-2018 + tau≈0 baseline, return CAMBdata + transfer."""
    import camb
    pars = camb.set_params(
        H0=67.36, ombh2=0.02237, omch2=0.12, mnu=0.06, omk=0,
        tau=1.0e-5, As=2.1e-9, ns=0.9649,
    )
    pars.set_for_lmax(10, lens_potential_accuracy=0)
    pars.WantTransfer = True
    t0 = time.monotonic()
    results = camb.get_results(pars)
    _log(f"CAMB compute done in {time.monotonic() - t0:.2f} s")
    trans = results.get_cmb_transfer_data(tp='scalar')
    return results, trans


def camb_t_source_on_bass_grid(camb_results, k: float, eta_grid: np.ndarray) -> np.ndarray:
    """Extract CAMB's T_source(η, k) sampled on BASS's η-grid.

    CAMB's `get_time_evolution` accepts a list of conformal times; we
    request T_source at the BASS grid points directly. This bypasses
    any interpolation issues — CAMB returns its internal source value
    at exactly the η values we ask for.
    """
    ks = np.array([float(k)])
    etas = np.asarray(eta_grid, dtype=np.float64)
    evo = camb_results.get_time_evolution(ks, etas, ['T_source'])
    # shape: (n_k, n_eta, n_vars) → (1, n_eta, 1)
    return np.asarray(evo[0, :, 0], dtype=np.float64)


def get_bass_alpha_native(species, ks: list[float]) -> dict:
    """Existing BASS pipeline α(k, ℓ) at default n_output=64."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_linear_probe_transfer_function,
    )
    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
        n_output=64,
    )
    out: dict = {}
    for k in ks:
        t0 = time.monotonic()
        tf = compute_linear_probe_transfer_function(
            species, k, config=cfg, probe_b_k_sq=1.0,
        )
        dt = time.monotonic() - t0
        out[k] = np.asarray(tf.delta_T_m0, dtype=np.float64)
        _log(f"  k={k:.3e}: BASS native done in {dt:.1f} s, α[ℓ=2]={out[k][2]:+.4e}")
    return out


def project_camb_source_on_bass_grid(camb_results, species, k: float) -> np.ndarray:
    """Pass CAMB's T_source through BASS's project_temperature_transfer
    on the BASS integrator η-grid. Returns Δ_T(k, ℓ=0..4)."""
    from bass.spectrum.flrw_pipeline import FLRWPipelineConfig
    from bass.los.flrw_bessel_projector import (
        FLRWBesselConfig,
        project_temperature_transfer,
    )

    cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4, n_output=64)

    # Reproduce the same η-grid BASS would use (uniform-linear)
    eta_init = 260.14  # consistent with build_cosmological_integrator_config default
    eta_today = float(species.bg_table.eta_today)
    eta_grid = np.linspace(eta_init, eta_today, cfg.n_output)
    eta_for_los = np.clip(eta_grid, 0.0, eta_today)

    # CAMB T_source at these exact η points
    s_T_camb = camb_t_source_on_bass_grid(camb_results, k, eta_for_los)

    bessel_cfg = FLRWBesselConfig(
        ell_max=cfg.ell_max_transfer,
        eta_0_mpc=eta_today,
        quadrature=cfg.quadrature,
    )
    delta_T = project_temperature_transfer(
        float(k), s_T_camb, eta_for_los, bessel_cfg,
    )
    return np.asarray(delta_T, dtype=np.float64)


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry
    from scipy.interpolate import interp1d

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.\n")

    bass_ks = [1.0e-3, 1.0e-2, 3.0e-2, 5.0e-2]

    _hr("Step 1 — CAMB setup + direct Δ_T(k, ℓ)")
    camb_results, trans = get_camb_results()
    _log(f"CAMB L range: {int(trans.L[0])}..{int(trans.L[-1])} ({len(trans.L)} values)")
    _log(f"CAMB q range: {trans.q[0]:.3e} .. {trans.q[-1]:.3e}")

    delta_T_lk = trans.delta_p_l_k[0]  # (n_l, n_q)
    interps = {}
    for ell in (2, 3, 4):
        l_idx = np.where(trans.L == ell)[0]
        if len(l_idx) > 0:
            interps[ell] = interp1d(
                np.log(trans.q), delta_T_lk[int(l_idx[0]), :],
                kind='cubic', bounds_error=False, fill_value=np.nan,
            )

    _hr("Step 2 — BASS native pipeline α(k, ℓ)")
    bass_alpha = get_bass_alpha_native(species, bass_ks)

    _hr("Step 3 — CAMB source through BASS LoS projector")
    camb_through_bass = {}
    for k in bass_ks:
        t0 = time.monotonic()
        camb_through_bass[k] = project_camb_source_on_bass_grid(
            camb_results, species, k,
        )
        dt = time.monotonic() - t0
        _log(f"  k={k:.3e}: project done in {dt:.2f} s, "
             f"Δ_T[ℓ=2]={camb_through_bass[k][2]:+.4e}")

    _hr("DECISIVE COMPARISON")
    _log(f"  {'k [Mpc⁻¹]':>10s}  {'ℓ':>2s}  "
         f"{'CAMB direct':>14s}  {'CAMB→BASS LoS':>14s}  "
         f"{'BASS native':>14s}  {'C/B-LoS / direct':>18s}")
    _log("  " + "-" * 86)

    case_signals = []  # collect ratios for later case-classification
    for k in bass_ks:
        for ell in (2, 3, 4):
            camb_direct = float(interps[ell](np.log(k))) if ell in interps else float('nan')
            camb_through_bass_val = float(camb_through_bass[k][ell])
            bass_native = float(bass_alpha[k][ell])
            ratio_cb_to_direct = (
                camb_through_bass_val / camb_direct
                if abs(camb_direct) > 1e-30 else float('nan')
            )
            _log(
                f"  {k:>10.3e}  {ell:>2d}  "
                f"{camb_direct:>+14.6e}  {camb_through_bass_val:>+14.6e}  "
                f"{bass_native:>+14.6e}  {ratio_cb_to_direct:>+18.4f}"
            )
            case_signals.append((k, ell, ratio_cb_to_direct))

    _hr("Case classification (per Claude Opus R14 §10)")
    _log("  Case A: |CAMB→BASS LoS / CAMB direct| ≈ 1 ± 5%  → projector healthy")
    _log("  Case B: |ratio| 10-100× too large at sub-horizon → D-1 dominant")
    _log("  Case C: low-k OK, high-k diverges → D-1 high-k, source low-k")
    _log("  Case D: sign flips → D-1 severity confirmed (220 Mpc on 19 Mpc FWHM)")
    _log("")

    # Compute summary
    valid = [(k, ell, r) for (k, ell, r) in case_signals if not np.isnan(r)]
    if valid:
        ratios = np.array([r for _, _, r in valid])
        sign_flips = sum(1 for _, _, r in valid if r < 0)
        within_5pct = sum(1 for _, _, r in valid if 0.95 < r < 1.05)
        order_10_to_100 = sum(1 for _, _, r in valid if 10 < abs(r) < 100)
        order_over_100 = sum(1 for _, _, r in valid if abs(r) > 100)
        _log(f"  Total (k, ℓ) cells: {len(valid)}")
        _log(f"    within 1.0 ± 5%:                {within_5pct}")
        _log(f"    sign-flipped (negative ratio):   {sign_flips}")
        _log(f"    |ratio| in [10, 100]:           {order_10_to_100}")
        _log(f"    |ratio| > 100:                   {order_over_100}")
        _log(f"    overall |ratio| stats: min={np.min(np.abs(ratios)):.3e}  "
             f"max={np.max(np.abs(ratios)):.3e}  median={np.median(np.abs(ratios)):.3e}")

        if within_5pct == len(valid):
            _log(f"\n  ★ CASE A — projector is healthy. Defect is 100% in source extraction.")
            _log(f"    Recommended Round-15 priority: D-3 first (gauge fix), then D-2.")
        elif sign_flips > len(valid) // 4:
            _log(f"\n  ★ CASE D — sign flips dominate. D-1 (LoS grid) critical.")
            _log(f"    Recommended Round-15 priority: D-1 first.")
        elif order_over_100 > 0 and within_5pct == 0:
            _log(f"\n  ★ CASE B — pervasive over-amplification. D-1 dominant.")
            _log(f"    Recommended Round-15 priority: D-1 first, then D-3, D-2.")
        else:
            _log(f"\n  ★ MIXED CASE (likely C) — examine per-k pattern above.")
            _log(f"    Recommended Round-15 priority: D-1 + D-3 in parallel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
