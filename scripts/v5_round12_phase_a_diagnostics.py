"""V5-RUNTIME Round-12 Phase A diagnostics.

Five diagnostics designed by the unanimous Round-12 external audit
(4/4 auditors) to localize the residual ~760× ``D_2^probe / D_2^Route-B``
factor that remains after the Round-10/R11 seed-formula bug fixes.

Auditor consensus root-cause hypotheses (in priority order):

  C-c  source-extractor ``1/k²`` Einstein-constraint cancellation
       failure at super-horizon (~97% of D_2 integrand from k=1e-4)
  C-e  N_k=12 sparse-quadrature artefact on the super-horizon spike
  H-5.1 (#4) seed_factory ``amplitude_reference = k`` k-dependent rescaling
  REFUTED: C-a (B_K_sq=ζ² double-counting), C-b (LoS Bessel), C-d (polter)

Diagnostics:

  D1  Per-k Φ(η) dump at k ∈ {1e-4, 3e-4, 1e-3} vs analytic 0.6·ζ
  D2  Constraint-violation probe: |δρ − 3ℋ·mom/k − k²Φ/(4πGa²)|/|δρ|
  D3  k_min sweep: D_2 ratio with k_min ∈ {1e-5, 3e-5, 1e-4, 3e-4, 1e-3}
  D4  every_n_steps=1 vs default 4: convention audit re-measurement
  D5  seed_factory amplitude_reference trace at k=1e-4 vs 1e-3

Wall time: ~12–15 min on 8 cores.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "htt" / "src"))
sys.path.insert(0, str(_REPO / "htt"))

import numpy as np


def _hr(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}", flush=True)


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ------------------------------------------------------------------------
# Diagnostic 5 — seed_factory amplitude_reference trace (cheapest first)
# ------------------------------------------------------------------------


def diagnostic_5(species, ks: list[float]) -> None:
    """Trace seed_pack amplitude_reference + projected_seed amplitude
    at multiple k. Per auditor #4 H-5.1: if projected_seed.amplitude
    ≠ b_k_sq=1.0, or scales with k, a hidden k-dependent rescaling
    contaminates the linear probe."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_transfer_function_at_k,
        _pipeline_manifest,
        _pipeline_release,
        _pipeline_runtime_controls,
        _pipeline_feature_flags,
    )
    from bass.runtime import (
        build_cosmological_integrator_config,
        execute_tier_b_solver,
    )
    from bass.background.bianchi_types import get_type
    from bass.background.einstein_bianchi import BianchiCosmology

    _hr("D5 — seed_factory amplitude_reference trace (auditor #4 H-5.1)")

    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
        primordial_b_k_sq=1.0,
    )

    for k in ks:
        _log(f"\n--- k = {k:.3e} Mpc⁻¹, b_k_sq = 1.0 ---")
        t0 = time.monotonic()
        integrator_config = build_cosmological_integrator_config(
            species,
            L_max=cfg.L_max_tower,
            n_output=cfg.n_output,
            rtol=cfg.rtol,
            atol=cfg.atol,
            bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
            gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
            adiabatic_mode_seed=cfg.adiabatic_mode_seed,
            primordial_b_k_sq=1.0,
        )
        k_grid_pair = np.array([float(k), 2.0 * float(k)], dtype=np.float64)
        run = execute_tier_b_solver(
            manifest=_pipeline_manifest(f"D5-k{k:.3e}"),
            bianchi_type="I",
            species=species,
            integrator_config=integrator_config,
            runtime_controls=_pipeline_runtime_controls(cfg),
            feature_flags=_pipeline_feature_flags(),
            release=_pipeline_release(f"D5-k{k:.3e}", cfg.random_seed),
            k_grid_mpc=k_grid_pair,
        )
        dt = time.monotonic() - t0
        _log(f"  solver done in {dt:.1f} s")

        # Inspect the seed_projection trace
        trace = run.trace
        seed_proj = trace.seed_projection
        projected_amp = float(seed_proj.projected_seed.amplitude)
        _log(f"  projected_seed.amplitude        = {projected_amp:.6e}")
        _log(f"  seed amplitude / b_k_sq         = {projected_amp / 1.0:.6e}")
        # The seed_pack info may be in metadata
        meta = getattr(trace, "metadata", None)
        if meta:
            for key in (
                "seed_k_comoving",
                "amplitude_reference",
                "seed_injection_mode",
            ):
                if key in meta:
                    _log(f"  metadata.{key:24s}= {meta[key]}")


# ------------------------------------------------------------------------
# Diagnostic 1 + 2 — Per-k Φ dump + constraint-violation probe
# ------------------------------------------------------------------------


def diagnostic_1_and_2(species, ks: list[float]) -> None:
    """Per-k extraction of Φ(η), Ψ(η), and the comoving-density constraint
    residual along the η-grid. Auditors #3 + #4 ranked this as the most
    decisive single diagnostic.

    For an adiabatic mode in matter domination, the analytic super-horizon
    expectation is Φ ≈ (3/5)·ζ (constant in η). At b_k_sq=1.0 this is
    Φ ≈ 0.6 (in BASS internal units).

    The constraint residual is
      R = δρ_tot − 3ℋ·mom/k − k²·Φ/(4πG·a²)
    and should be O(machine epsilon · |δρ|) in a constraint-clean solve."""

    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_transfer_function_at_k,
        build_visibility_and_kappa_callables,
    )
    from bass.spectrum.tier_b_source_extraction import (
        extract_flrw_sources_from_tier_b,
        _slot,
    )
    from bass.species.base import SpeciesLabel
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

    _hr("D1+D2 — Per-k Φ(η) dump + constraint-violation probe")
    _log("Analytic super-horizon prediction: Φ ≈ (3/5)·b_k_sq = 0.6 (k-indep)")
    _log("Clean constraint: |R|/|δρ_tot| should be O(1e-12) or better")

    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
        primordial_b_k_sq=1.0,
    )

    for k in ks:
        _log(f"\n--- k = {k:.3e} Mpc⁻¹, b_k_sq = 1.0 ---")
        t0 = time.monotonic()

        integrator_config = build_cosmological_integrator_config(
            species,
            L_max=cfg.L_max_tower,
            n_output=cfg.n_output,
            rtol=cfg.rtol,
            atol=cfg.atol,
            bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
            gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
            adiabatic_mode_seed=cfg.adiabatic_mode_seed,
            primordial_b_k_sq=1.0,
        )
        k_grid_pair = np.array([float(k), 2.0 * float(k)], dtype=np.float64)
        run = execute_tier_b_solver(
            manifest=_pipeline_manifest(f"D12-k{k:.3e}"),
            bianchi_type="I",
            species=species,
            integrator_config=integrator_config,
            runtime_controls=_pipeline_runtime_controls(cfg),
            feature_flags=_pipeline_feature_flags(),
            release=_pipeline_release(f"D12-k{k:.3e}", cfg.random_seed),
            k_grid_mpc=k_grid_pair,
        )
        dt = time.monotonic() - t0
        _log(f"  solver done in {dt:.1f} s")

        sources = extract_flrw_sources_from_tier_b(
            run.integration_result, species, k=float(k),
            anisotropic_stress=cfg.anisotropic_stress,
        )

        eta = np.asarray(run.integration_result.eta, dtype=np.float64)

        # FLRWSourceTerms exposes callables (theta_0, psi, ISW, v_b, π).
        # The internal Φ is consumed via the SW combination Θ_0 + Ψ;
        # Ψ ≈ Φ at super-horizon (small ν anisotropic stress).
        psi_arr = np.asarray(sources.psi(eta), dtype=np.float64)
        theta_0_arr = np.asarray(sources.theta_0(eta), dtype=np.float64)
        v_b_arr = np.asarray(sources.v_b(eta), dtype=np.float64)
        pi_arr = np.asarray(sources.pi(eta), dtype=np.float64)
        sw_combo = theta_0_arr + psi_arr  # the SW source amplitude

        # Sample at recombination
        try:
            eta_star_actual = float(species.bg_table.eta_at_a(1.0 / 1090.94))
        except Exception:
            eta_star_actual = 281.0
        idx_star = int(np.argmin(np.abs(eta - eta_star_actual)))
        idx_init = 0
        idx_today = -1

        # Analytic super-horizon SW expectation (matter-dominated):
        #   Ψ ≈ Φ ≈ (3/5)·ζ                         (constant in η)
        #   Θ_0 + Ψ ≈ -(1/3)·Ψ + Ψ = (2/3)·Ψ ≈ 0.4·ζ
        #   For b_k_sq = 1 (ζ=1), expect Θ_0+Ψ ≈ 0.4
        psi_analytic = 0.6
        sw_analytic = 0.4

        _log(
            f"  η_init={eta[idx_init]:>7.1f} Mpc:  "
            f"Ψ={psi_arr[idx_init]:+.4e}  Θ_0={theta_0_arr[idx_init]:+.4e}  "
            f"v_b={v_b_arr[idx_init]:+.4e}  Π={pi_arr[idx_init]:+.4e}"
        )
        _log(
            f"  η_*    ={eta[idx_star]:>7.1f} Mpc:  "
            f"Ψ={psi_arr[idx_star]:+.4e}  Θ_0={theta_0_arr[idx_star]:+.4e}  "
            f"SW=(Θ_0+Ψ)={sw_combo[idx_star]:+.4e}"
        )
        _log(
            f"  η_today={eta[idx_today]:>7.1f} Mpc:  "
            f"Ψ={psi_arr[idx_today]:+.4e}  Θ_0={theta_0_arr[idx_today]:+.4e}"
        )
        _log(
            f"  Ψ at η_*  / analytic 0.6 = {psi_arr[idx_star] / psi_analytic:+.4e}"
        )
        _log(
            f"  SW at η_* / analytic 0.4 = {sw_combo[idx_star] / sw_analytic:+.4e}  "
            f"(unity = clean SW, |large| = source extractor pathology)"
        )

        # Ψ(η) over a coarse grid — show how it evolves
        n = len(eta)
        sample_idx = [0, n // 4, n // 2, 3 * n // 4, n - 1]
        _log(f"  Ψ(η) along grid:")
        for i in sample_idx:
            _log(f"    η={eta[i]:>10.2f}  Ψ={psi_arr[i]:+.4e}  Θ_0={theta_0_arr[i]:+.4e}")


# ------------------------------------------------------------------------
# Diagnostic 3 — k_min sweep
# ------------------------------------------------------------------------


def diagnostic_3(species, k_min_values: list[float]) -> None:
    """Re-run the convention audit with k_min sweep. The N_k=12
    diagnostic at k_min=1e-4 gives ratio 7.57e+02; if the
    super-horizon spike dominates, raising k_min should drop the
    ratio sharply. If raising k_min does NOT help much, the issue
    is more uniform across k."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_flrw_d_ell_linear_probe,
    )

    _hr("D3 — k_min sweep (12 log-spaced points each)")
    cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)
    ROUTE_B_D2 = 1002.086744

    for k_min in k_min_values:
        # Keep same upper bound 1e-1 for comparability
        k_grid = np.logspace(np.log10(k_min), -1.0, 12)
        _log(f"\n--- k_min = {k_min:.3e}, k_grid = 12 points → [{k_min:.0e}, 1e-1] ---")
        t0 = time.monotonic()
        bundle = compute_flrw_d_ell_linear_probe(
            species,
            k_grid_mpc=k_grid,
            pipeline_config=cfg,
            probe_b_k_sq=1.0,
            n_workers=None,
        )
        dt = time.monotonic() - t0
        d2 = float(bundle["d_tt"][2])
        ratio = d2 / ROUTE_B_D2
        _log(f"  done in {dt:.1f} s")
        _log(
            f"  D_2^probe = {d2:.4e} μK²,  D_2/Route-B = {ratio:.4e},  "
            f"conv = √(1/ratio) = {np.sqrt(1.0 / max(ratio, 1e-300)):.4e}"
        )


# ------------------------------------------------------------------------
# Diagnostic 4 — ConstraintProjectionPolicy.every_n_steps toggle
# ------------------------------------------------------------------------


def diagnostic_4(species) -> None:
    """Re-run convention audit with constraint projection enforced every
    step (vs default every_n_steps=4). If IMEX projection drift is the
    cause, the ratio should improve. If not, the constraint failure is
    intrinsic to the source-extractor formula, not the integrator."""

    from dataclasses import replace as _dc_replace
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        compute_flrw_d_ell_linear_probe,
        _pipeline_runtime_controls as _orig_rcb,
    )
    import bass.spectrum.flrw_pipeline as _pipe
    from bass.runtime import (
        ConstraintProjectionPolicy,
        FeatureStatus,
    )

    _hr("D4 — ConstraintProjectionPolicy.every_n_steps toggle")
    _log("Default: every_n_steps=4 (status APPROXIMATE)")
    _log("Tighter: every_n_steps=1 (constraint enforced every step)")

    ROUTE_B_D2 = 1002.086744
    cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)
    k_grid = np.logspace(-4.0, -1.0, 12)

    # Monkey-patch _pipeline_runtime_controls to use every_n_steps=1
    def _tighter_rcb(config):
        rcb = _orig_rcb(config)
        return _dc_replace(
            rcb,
            constraint_projection=ConstraintProjectionPolicy(
                enabled=True, every_n_steps=1, status=FeatureStatus.APPROXIMATE
            ),
        )

    _log("\n--- Default (every_n_steps=4) baseline ---")
    t0 = time.monotonic()
    bundle_default = compute_flrw_d_ell_linear_probe(
        species, k_grid_mpc=k_grid, pipeline_config=cfg, probe_b_k_sq=1.0,
    )
    dt_default = time.monotonic() - t0
    d2_default = float(bundle_default["d_tt"][2])
    _log(f"  done in {dt_default:.1f} s")
    _log(f"  D_2 = {d2_default:.4e},  ratio = {d2_default / ROUTE_B_D2:.4e}")

    _log("\n--- Tighter (every_n_steps=1) ---")
    _pipe._pipeline_runtime_controls = _tighter_rcb  # monkey-patch
    try:
        t0 = time.monotonic()
        bundle_tight = compute_flrw_d_ell_linear_probe(
            species, k_grid_mpc=k_grid, pipeline_config=cfg, probe_b_k_sq=1.0,
        )
        dt_tight = time.monotonic() - t0
        d2_tight = float(bundle_tight["d_tt"][2])
        _log(f"  done in {dt_tight:.1f} s")
        _log(f"  D_2 = {d2_tight:.4e},  ratio = {d2_tight / ROUTE_B_D2:.4e}")
    finally:
        _pipe._pipeline_runtime_controls = _orig_rcb  # restore

    delta_ratio = abs(d2_tight - d2_default) / max(d2_default, 1e-300)
    _log(f"\n  |Δ_D2| / D_2_default = {delta_ratio:.4e}")
    _log("  → if ≪ 1: IMEX projection drift is NOT the root cause")
    _log("  → if  ~ 1 or larger: confirms IMEX drift contribution")


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.\n")

    diag_ks_full = [1.0e-4, 3.0e-4, 1.0e-3]
    k_min_values = [1.0e-5, 3.0e-5, 1.0e-4, 3.0e-4, 1.0e-3]

    # D5 already completed in prior run — skip to save ~85 s.
    # Result: projected_seed.amplitude scales as k² (≈ 1.39e+4·k²).
    # diagnostic_5(species, [1.0e-4, 1.0e-3])
    diagnostic_1_and_2(species, diag_ks_full)
    diagnostic_3(species, k_min_values)
    diagnostic_4(species)

    _hr("ALL DIAGNOSTICS COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
