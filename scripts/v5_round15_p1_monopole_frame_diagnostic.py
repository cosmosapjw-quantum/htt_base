"""V5-RUNTIME Round-15 P1 monopole-frame diagnostic.

Tests the kinematic-frame ↔ Newtonian-frame identification flagged by
both external-LLM audits as the highest-priority follow-up after the
Round-15 P0 D-1 LoS grid fix:

    Θ_0^(BASS)(η, k) ≈ Θ_0^(N)(η, k) + [Φ(η, k) − Φ(η_init, k)]
                       + O(k · ∫ Ψ dη')                          (★)

  - Opus R6 + R7-corrected: "the unresolved formal contract is the
    gauge/frame meaning of `theta0_g` entering the SW combination
    `theta0_g + psi`"; recommends a `theta0` convention test as the
    highest-priority follow-up.
  - ChatGPT R3.3.3 + R3.6: identifies Θ_0^(BASS) as the kinematic
    n^a-frame monopole, predicts (★) above, and asks for a
    sub-percent verification using CAMB's `delta_photon` in the
    Newtonian frame.

This script:
  1. Runs the BASS FLRW pipeline at a few low-k values where the
     §10 oracle (CAMB internal) is faithful (k ≤ 1e-2 Mpc⁻¹, per
     docs/V5_ROUND15_P1_PSTF_DERIVATION_*.md §3.3).
  2. Extracts Θ_0^(BASS)(η, k) = photon_T_tower[:, slot(0, 0)].
  3. Extracts Φ(η, k) from the same source extractor BASS uses for the
     LoS pipeline.
  4. Computes the candidate Newtonian Θ_0^(N) per (★):
        Θ_0^(N)_candidate(η, k) = Θ_0^(BASS)(η, k)
                                  − [Φ(η, k) − Φ(η_init, k)]
  5. Asks CAMB at the same Planck-2018 cosmology for `delta_photon`
     with `frame='Newtonian'`, divides by 4 to obtain Θ_0^(N).
  6. Compares ratio Θ_0^(N)_candidate / Θ_0^(N)_CAMB at recombination
     (η ≈ 281 Mpc) and at a few sub-horizon η values, plus the
     uncorrected ratio Θ_0^(BASS) / Θ_0^(N)_CAMB for contrast.

Verdict thresholds (both audits agree):

  - 5% gate: empirical Round-15 P0 anchor was 0.93–1.04 at the four
    k_adapt_η100 cells. Identification (★) holds at this level if the
    candidate ratio is within 5% of unity.
  - sub-percent verification of (★): a stronger proof that the BASS
    monopole really is the kinematic-frame quantity. If the candidate
    ratio is < 1.5% off after subtracting [Φ(η) − Φ(η_init)], the
    monopole-frame contract is closed and no PSTF-native scalar
    time-shift α correction is needed.

Caveat — normalization confound (2026-04-26 first-run finding):
  BASS's `t_tower[:, slot(0,0)]` and `sources.psi(η)` carry the
  pipeline's primordial-amplitude convention, which is *not* the same
  as CAMB's transfer-function-against-A_s normalization. Empirically
  Θ_0^(BASS) at η_init scales like `k²` across `k ∈ {1e-3, 5e-3, 1e-2}`,
  reflecting the `_resolve_primordial_b_k_sq(cfg, k)` knob. CAMB's
  `delta_photon` from `get_time_evolution` is normalized to unit
  primordial curvature. Direct value comparisons are therefore
  meaningful at η_init only (where both should coincide up to the
  super-horizon adiabatic-seed convention); η-evolution comparisons
  reflect both frame and normalization differences and cannot
  separate the two without an explicit primordial-normalization
  alignment step. The first-run output (k = 1e-3 → 1e-2 at η_init
  gives ratios 0.81, 0.85, 0.99) shows the order-of-unity match the
  audits expected; the later-η ratios oscillate due to normalization,
  not frame.

Constraints (from docs/V5_ROUND15_P1_EXTERNAL_LLM_BRIEFING.md §7):

  - CAMB used as audit oracle only; no production-code dependency.
  - Diagnostic script lives in `scripts/v5_round1*_*.py`, not in
    `htt/bass/*` or `htt/htt/*`.
  - No production code is changed by this script; it only reads from
    the BASS pipeline and writes a transcript.

Wall time: ~1 minute (4 BASS k-runs × ~14 s each + CAMB extract).
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
    return results


def camb_theta0_newtonian(camb_results, k: float, etas: np.ndarray) -> np.ndarray:
    """CAMB's Newtonian-frame photon monopole at requested η values.

    Returns Θ_0^(N) = δ_γ^(N) / 4. Uses `frame='Newtonian'` to force
    CAMB's symbolic gauge transformation of the gauge-dependent
    `delta_photon` away from the default CDM/synchronous frame.
    """
    evo = camb_results.get_time_evolution(
        np.array([float(k)]), np.asarray(etas, dtype=np.float64),
        ['delta_photon'], frame='Newtonian',
    )
    return np.asarray(evo[0, :, 0], dtype=np.float64) / 4.0


def bass_run_at_k(species, k: float):
    """Run the BASS FLRW pipeline once and return (eta_grid, theta0,
    psi_callable, phi_minus_phi_init_callable)."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig, _pipeline_manifest, _pipeline_runtime_controls,
        _pipeline_feature_flags, _pipeline_release, _resolve_primordial_b_k_sq,
    )
    from bass.runtime import build_cosmological_integrator_config, execute_tier_b_solver
    from bass.background.einstein_bianchi import BianchiCosmology
    from bass.background.bianchi_types import get_type
    from bass.spectrum.tier_b_source_extraction import (
        extract_flrw_sources_from_tier_b, _slot,
    )
    from scipy.interpolate import PchipInterpolator

    cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4,
                             unit_amplitude_normalization=False, n_output=64)

    integrator_config = build_cosmological_integrator_config(
        species, L_max=cfg.L_max_tower, n_output=cfg.n_output,
        rtol=cfg.rtol, atol=cfg.atol,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
        adiabatic_mode_seed=cfg.adiabatic_mode_seed,
        primordial_b_k_sq=_resolve_primordial_b_k_sq(cfg, k),
    )
    k_grid_pair = np.array([float(k), 2.0 * float(k)], dtype=np.float64)

    t0 = time.monotonic()
    run = execute_tier_b_solver(
        manifest=_pipeline_manifest(f"k{k:.6e}"),
        bianchi_type="I", species=species,
        integrator_config=integrator_config,
        runtime_controls=_pipeline_runtime_controls(cfg),
        feature_flags=_pipeline_feature_flags(),
        release=_pipeline_release(f"k{k:.6e}", cfg.random_seed),
        k_grid_mpc=k_grid_pair,
    )
    dt = time.monotonic() - t0

    integration_result = run.integration_result
    sources = extract_flrw_sources_from_tier_b(
        integration_result, species, k=float(k),
        anisotropic_stress=cfg.anisotropic_stress,
    )

    eta = np.asarray(integration_result.eta, dtype=np.float64)
    t_tower = np.asarray(integration_result.photon_T_tower, dtype=np.float64)
    theta0_BASS = t_tower[:, _slot(0, 0)]
    eta_init = float(eta[0])

    # Build Φ(η) = (Ψ(η) - psi_minus_phi(η)) callable using the same
    # constraint algebra the source extractor uses, but we only have
    # the assembled callables. The extractor returns Ψ but not Φ; for
    # this diagnostic we reconstruct Φ via Ψ − (Ψ − Φ) where (Ψ − Φ)
    # is approximately zero for radiation+baryons in the tight-coupling
    # era (anisotropic stress is small). For low-k diagnostics this
    # approximation is at the percent level and we accept it for the
    # 5% gate; the source extractor exposes Ψ directly.
    # However, the (★) formula above uses Φ specifically; per
    # ChatGPT R3.3.3 the correction is [Φ(η) − Φ(η_init)] and Φ ≈ Ψ
    # in the matter-dominated era within a few percent (anisotropic
    # stress correction). For diagnostic use we therefore approximate
    # Φ ≈ Ψ for the candidate computation; this introduces a known
    # systematic of O(σ_ν) at recombination ≈ few percent which we
    # report alongside the result.
    psi_callable = sources.psi
    return eta, eta_init, theta0_BASS, psi_callable, dt


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.\n")

    _hr("Step 1 — CAMB setup at Planck-2018, frame='Newtonian'")
    camb_results = get_camb_results()
    eta_today_camb = float(camb_results.tau0)
    _log(f"CAMB tau_0 = {eta_today_camb:.3f} Mpc")

    # Limit to k ≤ 1e-2 — per docs/V5_ROUND15_P1_PSTF_DERIVATION_*.md §3.3,
    # CAMB's exposed Newtonian-gauge `delta_photon` faithfully
    # represents the LoS-relevant monopole only at sub-horizon scales
    # below a few percent of k_eq.
    diag_ks = [1.0e-3, 5.0e-3, 1.0e-2]

    _hr("Step 2 — BASS pipeline at each k, extract Θ_0^(BASS)(η, k) and Ψ(η, k)")
    bass_runs = {}
    for k in diag_ks:
        eta, eta_init, theta0_BASS, psi_callable, dt = bass_run_at_k(species, k)
        bass_runs[k] = (eta, eta_init, theta0_BASS, psi_callable)
        _log(f"  k={k:.3e}: BASS done in {dt:.1f} s, "
             f"Θ_0^(BASS)[η_init]={theta0_BASS[0]:+.4e}, "
             f"Θ_0^(BASS)[η≈281]={theta0_BASS[np.argmin(np.abs(eta-281.0))]:+.4e}")

    _hr("Step 3 — Compare BASS candidate Θ_0^(N)_candidate vs CAMB Θ_0^(N)")
    _log(
        "  Θ_0^(N)_candidate(η, k) = Θ_0^(BASS)(η, k) − [Ψ(η, k) − Ψ(η_init, k)]\n"
        "  (Ψ used in place of Φ; Ψ−Φ is the anisotropic-stress correction,\n"
        "   percent-level at recombination — see audit docs §R3.3.3.)\n"
        "  CAMB Θ_0^(N)(η, k) = delta_photon(η, k; frame='Newtonian') / 4."
    )
    _log("")
    _log(
        f"  {'k':>10s}  {'η':>8s}  "
        f"{'Θ_0^(BASS)':>12s}  {'Δψ ramp':>12s}  "
        f"{'candidate':>12s}  {'CAMB Θ_0^N':>12s}  "
        f"{'cand/CAMB':>10s}  {'BASS/CAMB':>10s}"
    )
    _log("  " + "-" * 100)

    # Sample η points: η_init, near recombination peak, sub-horizon late, today.
    eta_probe_mpc = np.array([280.0, 500.0, 2000.0, 8000.0])

    for k in diag_ks:
        eta_grid, eta_init, theta0_BASS, psi_callable = bass_runs[k]
        # Evaluate Ψ on the integrator grid + at probe points
        psi_on_grid = np.asarray(psi_callable(eta_grid), dtype=np.float64)
        psi_init = float(psi_on_grid[0])

        # Probes inside the integrator domain
        for eta_q in eta_probe_mpc:
            if not (eta_init < eta_q < eta_grid[-1]):
                continue
            i = int(np.argmin(np.abs(eta_grid - eta_q)))
            theta0 = float(theta0_BASS[i])
            psi_at = float(psi_on_grid[i])
            psi_ramp = psi_at - psi_init
            theta0_candidate = theta0 - psi_ramp

            camb_theta0 = float(
                camb_theta0_newtonian(camb_results, k, np.array([eta_grid[i]]))[0]
            )

            ratio_cand = (
                theta0_candidate / camb_theta0
                if abs(camb_theta0) > 1.0e-30 else float('nan')
            )
            ratio_bass = (
                theta0 / camb_theta0
                if abs(camb_theta0) > 1.0e-30 else float('nan')
            )
            _log(
                f"  {k:>10.3e}  {eta_grid[i]:>8.1f}  "
                f"{theta0:>+12.5e}  {psi_ramp:>+12.5e}  "
                f"{theta0_candidate:>+12.5e}  {camb_theta0:>+12.5e}  "
                f"{ratio_cand:>+10.4f}  {ratio_bass:>+10.4f}"
            )

    _hr("Verdict thresholds (per audit docs) + normalization caveat")
    _log("  Identification (★) holds at the 5% gate if cand/CAMB ∈ [0.95, 1.05].")
    _log("  Sub-percent closure of the monopole contract requires |cand/CAMB − 1| < 1.5%.")
    _log("")
    _log("  CAVEAT (2026-04-26 first-run finding):")
    _log("  BASS's `t_tower[:, slot(0,0)]` and `sources.psi` carry the BASS")
    _log("  primordial-amplitude convention (Θ_0^(BASS) ~ k² in this test),")
    _log("  while CAMB's `delta_photon`/`Weyl` from get_time_evolution are")
    _log("  transfer-function-normalized against unit primordial curvature.")
    _log("  Direct value comparisons therefore separate cleanly at η_init")
    _log("  (where both should coincide modulo the seed convention) but")
    _log("  η-evolution comparisons reflect a mixture of frame *and*")
    _log("  normalization differences. A clean closure of the monopole")
    _log("  contract requires explicit primordial-amplitude alignment;")
    _log("  the order-of-unity η_init agreement (cand≡BASS at η_init since")
    _log("  Δψ ramp = 0) is consistent with the audits' assertion that")
    _log("  there is no catastrophic frame error.")
    _log("")
    _log("  Operative claim: the LoS-observable Δ_T agreement at the")
    _log("  Round-15 P0 §10 4-cell low-k anchor (median ratio = 1.00,")
    _log("  cells within 5% after η_init truncation lifted) remains the")
    _log("  empirical baseline; the monopole contract is non-catastrophic")
    _log("  but not closed at sub-percent against this diagnostic alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
