"""V5-RUNTIME Round-13 follow-up Phase B-fix diagnostics.

After the Round-13 external audit (3/3 REFUTED Option A as a numerical
patch), three new diagnostics to localize the real root cause:

  D1+D2-FIXED  Ψ at proper η_* using the PCHIP callable directly
               (the Round-12 Phase A script measured Ψ at η_init due
               to ``idx_star = argmin(|eta - 281|) = 0`` on the
               64-point uniform-linear grid Δη = 220 Mpc — Opus
               auditor's idx_star bug finding)

  D7  4√2 trial: apply ``calibration_factor = 1/(4√2) = 0.1768`` to
      the convention audit at multiple k_min and check whether the
      sub-horizon ratio collapses to ~unity (Codex auditor's
      ``sqrt(32) = 4√2`` PSTF-normalization hypothesis)

  D6  n_output sweep: test n_output ∈ {64, 256, 1024} at canonical
      k_grid = 12 log-spaced [1e-4, 1e-1] (Opus auditor's η-grid
      undersampling hypothesis — visibility g(η) of width ~19 Mpc
      sampled on Δη = 220 Mpc grid → 19% retention)

Wall time: ~15-25 min on 8 cores (n_output=1024 dominant).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np

ROUTE_B_D2 = 1002.086744


def _hr(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}", flush=True)


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ------------------------------------------------------------------------
# D1+D2 FIXED — Ψ via callable at proper η_*
# ------------------------------------------------------------------------


def diagnostic_1_and_2_fixed(species, ks: list[float]) -> None:
    """Resample Ψ at multiple physically-meaningful η using the PCHIP
    callable from extract_flrw_sources_from_tier_b — bypassing the
    grid-aligned idx_star bug.

    Probe points (per Opus auditor's Gate-2 spec):
      η_init       = 260.14  (existing buggy sample point)
      η_*          ≈ 281     (true recombination)
      η_*+10       ≈ 291     (mid-recombination, after peak)
      η_*+30       ≈ 311     (post-recombination, ~Δη_recomb FWHM)
      η = 1000               (early matter era)
      η = 5000               (mid matter era)
      η_today      = 14147

    Analytic super-horizon adiabatic Ψ in matter era (deep MD):
      Ψ_MD ≈ -10/(4·R_ν+15) ≈ -0.601  (CAMB Notes eq. 9.9, χ_0=-1)
    Note SIGN: Opus auditor confirmed CAMB convention gives -0.601,
    and BASS reading -0.34 is the SAME sign — earlier comparison
    against +0.6 was wrong reference."""

    from bass.spectrum.flrw_pipeline import FLRWPipelineConfig
    from bass.spectrum.tier_b_source_extraction import (
        extract_flrw_sources_from_tier_b,
    )
    from bass.runtime import (
        build_cosmological_integrator_config,
        execute_tier_b_solver,
    )
    from bass.background.bianchi_types import get_type
    from bass.background.einstein_bianchi import BianchiCosmology
    from bass.spectrum.flrw_pipeline import (
        _pipeline_manifest,
        _pipeline_release,
        _pipeline_runtime_controls,
        _pipeline_feature_flags,
    )

    _hr("D1+D2 FIXED — Ψ via PCHIP callable at proper η_*")
    _log("Analytic deep-MD: Ψ ≈ -10/(4·R_ν+15) ≈ -0.601 (CAMB Notes χ_0=-1)")
    _log("(Opus correction: previous +0.6 reference was wrong sign)")

    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
        primordial_b_k_sq=1.0,
    )

    eta_star_actual = float(species.bg_table.eta_at_a(1.0 / 1090.94))
    eta_today = float(species.bg_table.eta_today)
    probe_etas = [
        260.14,           # η_init (buggy sample point)
        eta_star_actual,  # ~281, true recombination peak
        eta_star_actual + 10.0,
        eta_star_actual + 30.0,  # post-recombination
        1000.0,
        5000.0,
        eta_today,        # ~14147
    ]
    probe_labels = ["η_init", "η_*", "η_*+10", "η_*+30", "η=1000", "η=5000", "η_today"]

    for k in ks:
        _log(f"\n--- k = {k:.3e} Mpc⁻¹, b_k_sq = 1.0 ---")
        t0 = time.monotonic()

        integrator_config = build_cosmological_integrator_config(
            species, L_max=cfg.L_max_tower,
            n_output=cfg.n_output, rtol=cfg.rtol, atol=cfg.atol,
            bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
            gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
            adiabatic_mode_seed=cfg.adiabatic_mode_seed,
            primordial_b_k_sq=1.0,
        )
        k_grid_pair = np.array([float(k), 2.0 * float(k)], dtype=np.float64)
        run = execute_tier_b_solver(
            manifest=_pipeline_manifest(f"D12-fix-k{k:.3e}"),
            bianchi_type="I",
            species=species,
            integrator_config=integrator_config,
            runtime_controls=_pipeline_runtime_controls(cfg),
            feature_flags=_pipeline_feature_flags(),
            release=_pipeline_release(f"D12-fix-k{k:.3e}", cfg.random_seed),
            k_grid_mpc=k_grid_pair,
        )
        dt = time.monotonic() - t0
        _log(f"  solver done in {dt:.1f} s, n_output = {cfg.n_output}")

        sources = extract_flrw_sources_from_tier_b(
            run.integration_result, species, k=float(k),
            anisotropic_stress=cfg.anisotropic_stress,
        )
        psi_callable = sources.psi
        theta_0_callable = sources.theta_0

        _log(f"  {'point':>8s}  {'η [Mpc]':>10s}  {'Ψ(η)':>14s}  {'Θ_0(η)':>14s}  {'SW=Θ_0+Ψ':>14s}")
        for label, eta_val in zip(probe_labels, probe_etas):
            psi_val = float(psi_callable(np.array([eta_val]))[0])
            theta_0_val = float(theta_0_callable(np.array([eta_val]))[0])
            sw = theta_0_val + psi_val
            _log(
                f"  {label:>8s}  {eta_val:>10.2f}  "
                f"{psi_val:>+14.6e}  {theta_0_val:>+14.6e}  {sw:>+14.6e}"
            )


# ------------------------------------------------------------------------
# D7 — 4√2 trial calibration (Codex hypothesis)
# ------------------------------------------------------------------------


def diagnostic_7(species) -> None:
    """Apply calibration_factor = 1/(4√2) = 0.1768 to the convention
    audit at two k_min values. If Codex's hypothesis is correct (PSTF
    tower → MB scalar multipole conversion missing 4√2 factor):

      k_min=1e-3, calibration_factor=1     → ratio ≈ 32  (current)
      k_min=1e-3, calibration_factor=1/4√2 → ratio ≈ 1   (predicted)
      k_min=1e-4, calibration_factor=1/4√2 → ratio ≈ 24  (super-horizon
                                                          spike still
                                                          present)

    Falsifiable test of the 4√2 PSTF normalization hypothesis."""

    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_flrw_d_ell_linear_probe,
    )

    _hr("D7 — 4√2 trial calibration (Codex hypothesis)")
    _log(f"calibration_factor = 1/(4√2) = {1.0 / (4.0 * np.sqrt(2)):.6f}")
    _log("D_ℓ scales as calibration² = 1/32 = 0.03125")
    _log("If hypothesis correct: ratio should drop by ~32× at sub-horizon-only")

    cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)
    cal_4sqrt2 = 1.0 / (4.0 * np.sqrt(2))

    test_cases = [
        # (k_min, calibration_factor, label, expected_ratio_if_4sqrt2)
        (1.0e-3, 1.0, "baseline (cal=1.0)", 32.0),
        (1.0e-3, cal_4sqrt2, "4√2 trial (cal=1/4√2)", "≈ 1.0"),
        (1.0e-4, 1.0, "full grid baseline (cal=1.0)", 760.0),
        (1.0e-4, cal_4sqrt2, "4√2 trial full grid", "≈ 24.0"),
    ]

    for k_min, cal, label, predicted in test_cases:
        k_grid = np.logspace(np.log10(k_min), -1.0, 12)
        _log(f"\n--- k_min={k_min:.0e}, {label}, predicted ratio: {predicted} ---")
        t0 = time.monotonic()
        bundle = compute_flrw_d_ell_linear_probe(
            species, k_grid_mpc=k_grid,
            pipeline_config=cfg,
            probe_b_k_sq=1.0,
            calibration_factor=float(cal),
        )
        dt = time.monotonic() - t0
        d2 = float(bundle["d_tt"][2])
        ratio = d2 / ROUTE_B_D2
        _log(f"  done in {dt:.1f} s")
        _log(
            f"  D_2 = {d2:.4e} μK²,  ratio = {ratio:.4f},  "
            f"sqrt(ratio) = {np.sqrt(abs(ratio)):.4f}"
        )


# ------------------------------------------------------------------------
# D6 — n_output sweep (Opus η-grid hypothesis)
# ------------------------------------------------------------------------


def diagnostic_6(species, n_outputs: list[int]) -> None:
    """Convention audit at canonical k_min=1e-4 with varying n_output
    of the IMEX integrator. If Opus's hypothesis is correct (η-output
    grid undersampling of recombination zone), raising n_output should
    change D_2 substantially.

    The grid type is `np.linspace(η_init, η_today, n_output)` (uniform
    linear). Keeping that fixed but raising the density: 64→256→1024
    reduces Δη from 220 Mpc to 14 Mpc, which is comparable to the
    visibility FWHM ~19 Mpc.

    Wall time: 12 k-grid × 2 (bias subtraction) × ~per-solver cost.
    Per-solver cost scales roughly linearly with n_output above ~256
    (where output sampling exceeds typical adaptive step count)."""

    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_flrw_d_ell_linear_probe,
    )

    _hr("D6 — n_output sweep (Opus η-grid hypothesis)")
    _log("Visibility g(η) FWHM ~19 Mpc; n_output=64 gives Δη=220 Mpc")
    _log("Required: Δη ≪ 19 Mpc → n_output ≳ 14000/19 ≈ 730")

    k_grid = np.logspace(-4.0, -1.0, 12)
    for n_out in n_outputs:
        delta_eta = (14147.35 - 260.14) / (n_out - 1)
        _log(f"\n--- n_output = {n_out}, Δη = {delta_eta:.1f} Mpc ---")
        cfg = FLRWPipelineConfig(
            L_max_tower=4, ell_max_transfer=4,
            n_output=n_out,
        )
        t0 = time.monotonic()
        bundle = compute_flrw_d_ell_linear_probe(
            species, k_grid_mpc=k_grid,
            pipeline_config=cfg,
            probe_b_k_sq=1.0,
        )
        dt = time.monotonic() - t0
        d2 = float(bundle["d_tt"][2])
        ratio = d2 / ROUTE_B_D2
        _log(f"  done in {dt:.1f} s")
        _log(
            f"  D_2 = {d2:.4e} μK²,  ratio = {ratio:.4f},  "
            f"conv = sqrt(1/ratio) = {np.sqrt(1.0 / max(ratio, 1e-300)):.4f}"
        )


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.")

    # Run order: cheap → expensive
    diagnostic_1_and_2_fixed(species, [1.0e-4, 1.0e-3])
    diagnostic_7(species)  # ~5 min
    diagnostic_6(species, [64, 256, 1024])  # ~10-20 min

    _hr("ALL PHASE B-FIX DIAGNOSTICS COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
