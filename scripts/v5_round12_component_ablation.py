"""V5-RUNTIME Round-12 Phase B-fix: source-component ablation diagnostic.

After Option I (n_output sweep) FAILED — BASS doesn't converge with
n_output, signs flip, std/|mean| stays 140-350% — this script isolates
each source-term contribution (SW + polter, ISW, Doppler) to find which
one is the dominant cause of the per-(k, ℓ) discrepancy with CAMB.

Strategy:
  Build BASS source callables via extract_flrw_sources_from_tier_b
  Then construct three FLRWSourceTerms variants:
    (1) SW + polter only (with_sw_polter_only)
    (2) ISW only (with_isw_only)
    (3) Doppler only (with_doppler_only)
  Project each via project_temperature_transfer → Δ_ℓ
  Compare each component's Δ_ℓ vs the FULL BASS Δ_ℓ vs CAMB Δ_T.

If one component dominates the discrepancy, that's the root cause to fix.

Wall time: ~5-7 min (one BASS solver run per k × 4 ks = 4 × 45s ≈ 3 min,
plus LoS projection per component ≈ instant).
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
    """CAMB Δ_T(ℓ, k) interpolators ℓ ∈ {2, 3, 4}, Planck-2018 + tau≈0."""
    import camb
    from scipy.interpolate import interp1d
    pars = camb.set_params(
        H0=67.36, ombh2=0.02237, omch2=0.12, mnu=0.06, omk=0,
        tau=1.0e-5, As=2.1e-9, ns=0.9649,
    )
    pars.set_for_lmax(10, lens_potential_accuracy=0)
    pars.WantTransfer = True
    results = camb.get_results(pars)
    trans = results.get_cmb_transfer_data(tp='scalar')
    delta_T_lk = trans.delta_p_l_k[0]
    interps = {}
    for ell in (2, 3, 4):
        l_idx = np.where(trans.L == ell)[0]
        if len(l_idx) > 0:
            interps[ell] = interp1d(
                np.log(trans.q), delta_T_lk[int(l_idx[0]), :],
                kind='cubic', bounds_error=False, fill_value=np.nan,
            )
    return interps


def project_with_components(species, k: float, n_output: int = 64) -> dict:
    """Run BASS solver, then project Δ_ℓ from each isolated component."""
    from bass.spectrum.flrw_pipeline import (
        FLRWPipelineConfig,
        build_visibility_and_kappa_callables,
    )
    from bass.spectrum.tier_b_source_extraction import (
        extract_flrw_sources_from_tier_b,
    )
    from bass.los.flrw_bessel_projector import (
        FLRWBesselConfig,
        FLRWSourceTerms,
        build_temperature_source,
        project_temperature_transfer,
    )
    from bass.runtime import (
        build_cosmological_integrator_config,
        execute_tier_b_solver,
    )
    from bass.background.bianchi_types import get_type
    from bass.background.einstein_bianchi import BianchiCosmology
    from bass.spectrum.flrw_pipeline import (
        _pipeline_manifest, _pipeline_release,
        _pipeline_runtime_controls, _pipeline_feature_flags,
    )

    cfg = FLRWPipelineConfig(
        L_max_tower=4, ell_max_transfer=4,
        unit_amplitude_normalization=False,
        n_output=n_output,
        primordial_b_k_sq=1.0,
    )
    integrator_config = build_cosmological_integrator_config(
        species, L_max=cfg.L_max_tower,
        n_output=cfg.n_output, rtol=cfg.rtol, atol=cfg.atol,
        bianchi_cosmo=BianchiCosmology(structure=get_type("I"), beta=0.0),
        gamma_T_over_H_threshold=cfg.gamma_T_over_H_threshold,
        adiabatic_mode_seed=cfg.adiabatic_mode_seed,
        primordial_b_k_sq=1.0,
    )
    k_pair = np.array([float(k), 2.0 * float(k)], dtype=np.float64)
    t0 = time.monotonic()
    run = execute_tier_b_solver(
        manifest=_pipeline_manifest(f"ablation-k{k:.3e}"),
        bianchi_type="I", species=species,
        integrator_config=integrator_config,
        runtime_controls=_pipeline_runtime_controls(cfg),
        feature_flags=_pipeline_feature_flags(),
        release=_pipeline_release(f"ablation-k{k:.3e}", cfg.random_seed),
        k_grid_mpc=k_pair,
    )
    dt = time.monotonic() - t0

    sources_full = extract_flrw_sources_from_tier_b(
        run.integration_result, species, k=float(k),
        anisotropic_stress=cfg.anisotropic_stress,
    )
    g_of_eta, kappa_of_eta = build_visibility_and_kappa_callables(species)
    eta_grid = np.asarray(run.integration_result.eta, dtype=np.float64)
    eta_0 = float(species.bg_table.eta_today)
    eta_for_los = np.clip(eta_grid, 0.0, eta_0)
    bessel_cfg = FLRWBesselConfig(
        ell_max=cfg.ell_max_transfer, eta_0_mpc=eta_0,
        quadrature=cfg.quadrature,
    )

    # Build component-isolated source variants
    variants = {
        "FULL": sources_full,
        "SW+polter": FLRWSourceTerms.with_sw_polter_only(
            theta_0=sources_full.theta_0, psi=sources_full.psi,
            pi=sources_full.pi,
        ),
        "ISW": FLRWSourceTerms.with_isw_only(
            phi_dot_plus_psi_dot=sources_full.phi_dot_plus_psi_dot,
        ),
        "Doppler": FLRWSourceTerms.with_doppler_only(v_b=sources_full.v_b),
    }
    out = {"_dt": dt}
    for name, src in variants.items():
        s_T = build_temperature_source(eta_for_los, src, g_of_eta, kappa_of_eta)
        delta_T = project_temperature_transfer(
            float(k), s_T, eta_for_los, bessel_cfg,
        )
        out[name] = np.asarray(delta_T, dtype=np.float64)
    return out


def main() -> int:
    from bass.species.registry import SpeciesBackgroundRegistry

    _log("Loading Planck-2018 species registry...")
    species = SpeciesBackgroundRegistry.from_planck2018()
    _log("species ready.\n")

    bass_ks = [1.0e-3, 1.0e-2, 3.0e-2, 5.0e-2]

    _hr("Component ablation: SW+polter / ISW / Doppler / FULL")
    interps = get_camb_transfer()
    _log("CAMB Δ_T interpolators ready (Planck-2018, tau=1e-5)")

    results = {}
    for k in bass_ks:
        _log(f"\n--- k = {k:.3e} Mpc⁻¹ ---")
        results[k] = project_with_components(species, k, n_output=64)
        _log(f"  solver done in {results[k]['_dt']:.1f} s")
        for ell in (2, 3, 4):
            full = float(results[k]["FULL"][ell])
            sw = float(results[k]["SW+polter"][ell])
            isw = float(results[k]["ISW"][ell])
            dop = float(results[k]["Doppler"][ell])
            sum_components = sw + isw + dop
            camb_delta = float(interps[ell](np.log(k))) if ell in interps else float('nan')
            _log(
                f"  ℓ={ell}: FULL={full:+.4e}  SW+polter={sw:+.4e}  "
                f"ISW={isw:+.4e}  Doppler={dop:+.4e}  "
                f"|sum-FULL|={abs(sum_components-full):.2e}"
            )
            _log(
                f"        CAMB={camb_delta:+.4e}  "
                f"FULL/CAMB={full/camb_delta:+.3f}  "
                f"SW/CAMB={sw/camb_delta:+.3f}  "
                f"ISW/CAMB={isw/camb_delta:+.3f}  "
                f"Dop/CAMB={dop/camb_delta:+.3f}"
            )

    _hr("Per-component dominance map (which component drives FULL?)")
    for k in bass_ks:
        for ell in (2, 3, 4):
            full = float(results[k]["FULL"][ell])
            sw = float(results[k]["SW+polter"][ell])
            isw = float(results[k]["ISW"][ell])
            dop = float(results[k]["Doppler"][ell])
            mag_total = abs(sw) + abs(isw) + abs(dop)
            if mag_total > 1e-30:
                pct_sw = 100.0 * abs(sw) / mag_total
                pct_isw = 100.0 * abs(isw) / mag_total
                pct_dop = 100.0 * abs(dop) / mag_total
                _log(
                    f"  k={k:.0e} ℓ={ell}: "
                    f"|SW|={pct_sw:5.1f}%  |ISW|={pct_isw:5.1f}%  "
                    f"|Dop|={pct_dop:5.1f}%   FULL/CAMB={full/float(interps[ell](np.log(k))):+.3f}"
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
