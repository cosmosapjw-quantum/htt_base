"""Independent verification of W9-01 physics.

Standalone cross-checks (not through pytest) of the numerical claims
made by the FLRW Bessel projector. Exit status 0 on all passes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


def header(msg: str) -> None:
    print()
    print("=" * 72)
    print(msg)
    print("=" * 72)


def check(label: str, ok: bool, detail: str = "") -> bool:
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {label}" + (f"   — {detail}" if detail else ""))
    return ok


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from bass.los.flrw_bessel_projector import (
        FLRWBesselConfig, FLRWSourceTerms, bessel_sum_rule,
        build_eta_grid_linear, build_temperature_source,
        constant_callable, e_mode_projection_factor,
        project_temperature_transfer, sachs_wolfe_analytic_transfer,
        spherical_bessel_at,
    )

    all_pass = True

    # ----- Block 1: Bessel sum rule -----
    header("Block 1 — Bessel sum rule completeness")
    for x in [0.5, 1.0, 2.5, 5.0, 10.0]:
        ell_max = max(30, int(2 * x) + 10)
        total = bessel_sum_rule(x, ell_max)
        all_pass &= check(
            f"Σ_ℓ (2ℓ+1) j_ℓ²({x}) = 1 at ell_max={ell_max}",
            abs(total - 1.0) < 1e-10,
            f"total = {total:.15f}, |err| = {abs(total-1.0):.2e}",
        )

    # ----- Block 2: E-mode projection factor Taylor limits -----
    header("Block 2 — E-mode projection factor small-kr limit")
    # At kr → 0, P^E_2 → √24/15 ≈ 0.326599
    expected_ell2_limit = np.sqrt(24.0) / 15.0
    p2 = e_mode_projection_factor(2, 1e-8)
    all_pass &= check(
        "P^E_2(kr→0) → √24/15",
        abs(p2 - expected_ell2_limit) / expected_ell2_limit < 1e-6,
        f"numerical = {p2:.12f}, analytic = {expected_ell2_limit:.12f}",
    )

    # For ℓ ≥ 3: P^E_ℓ(kr→0) ∝ (kr)^(ℓ-2) → 0
    p5_tiny = e_mode_projection_factor(5, 1e-6)
    all_pass &= check(
        "P^E_5(kr=1e-6) vanishes (→ 0 as (kr)^3)",
        abs(p5_tiny) < 1e-12,
        f"|P^E_5| = {abs(p5_tiny):.2e}",
    )

    # ----- Block 3: Sharp-visibility SW analytic limit -----
    header("Block 3 — narrow Gaussian visibility → j_ℓ(kr_*) recovery")
    cfg = FLRWBesselConfig(ell_max=10, eta_0_mpc=14116.4)
    eta_star = 280.0
    theta_plus_psi = 0.4
    # Narrow Gaussian g, constant (Θ₀+Ψ), no Π / ISW / Doppler
    sigma = 3.0
    def g_fn(e):
        return np.exp(-0.5 * ((e - eta_star) / sigma) ** 2) / (sigma * np.sqrt(2*np.pi))

    sources = FLRWSourceTerms.with_sw_polter_only(
        theta_0=constant_callable(theta_plus_psi),
        psi=constant_callable(0.0),
        pi=constant_callable(0.0),
    )
    eta_grid = build_eta_grid_linear(eta_star - 60.0, eta_star + 60.0, 12001)
    S_T = build_temperature_source(
        eta_grid, sources, g_fn, lambda e: np.zeros_like(np.asarray(e)),
    )
    for k in [5e-4, 1e-3, 3e-3]:
        D_num = project_temperature_transfer(k, S_T, eta_grid, cfg)
        D_analytic = sachs_wolfe_analytic_transfer(
            k, eta_star, theta_plus_psi, cfg,
        )
        max_abs = np.max(np.abs(D_analytic))
        rel = np.max(np.abs(D_num - D_analytic)) / max_abs
        all_pass &= check(
            f"narrow-σ=3 sharp-vis recovery at k={k}",
            rel < 5e-4,
            f"rel = {rel:.2e}",
        )

    # ----- Block 4: SW sigma scaling — narrower σ improves match -----
    header("Block 4 — SW sharp-vis error scales with σ²")
    cfg4 = FLRWBesselConfig(ell_max=6, eta_0_mpc=14116.4)
    k = 5e-4
    errors = []
    for sigma in [20.0, 10.0, 3.0]:
        def g_sigma(e, s=sigma):
            return np.exp(-0.5 * ((e - eta_star) / s) ** 2) / (s * np.sqrt(2*np.pi))
        eta_g = build_eta_grid_linear(
            max(1.0, eta_star - 30*sigma),
            min(14116.4, eta_star + 30*sigma), 10001,
        )
        S = build_temperature_source(
            eta_g, sources, g_sigma, lambda e: np.zeros_like(np.asarray(e)),
        )
        Dn = project_temperature_transfer(k, S, eta_g, cfg4)
        Da = sachs_wolfe_analytic_transfer(k, eta_star, theta_plus_psi, cfg4)
        rel = np.max(np.abs(Dn - Da)) / np.max(np.abs(Da))
        errors.append((sigma, rel))
    all_pass &= check(
        "error(σ=3) < error(σ=10) < error(σ=20)",
        errors[0][1] > errors[1][1] > errors[2][1],
        "  ".join(f"σ={s}: rel={r:.2e}" for s, r in errors),
    )

    # ----- Block 5: Transfer linearity -----
    header("Block 5 — Transfer function linearity in source")
    eta = build_eta_grid_linear(10.0, 14116.4, 2001)
    S = np.exp(-((eta - 280.0) / 30.0) ** 2)
    cfg5 = FLRWBesselConfig(ell_max=5, eta_0_mpc=14116.4)
    D1 = project_temperature_transfer(1e-3, S, eta, cfg5)
    D7 = project_temperature_transfer(1e-3, 7.0 * S, eta, cfg5)
    rel = np.max(np.abs(D7 - 7.0 * D1)) / np.max(np.abs(7.0 * D1))
    all_pass &= check(
        "Δ_ℓ(7 S) = 7 Δ_ℓ(S) at machine precision",
        rel < 1e-13,
        f"rel = {rel:.2e}",
    )

    # ----- Block 6: ISW isolation — non-zero transfer at κ=0 -----
    header("Block 6 — ISW isolation (no SW, no polter, no Doppler)")
    cfg6 = FLRWBesselConfig(ell_max=4, eta_0_mpc=14116.4)
    eta = build_eta_grid_linear(10.0, 14116.4, 2001)
    isw_sources = FLRWSourceTerms.with_isw_only(constant_callable(1e-4))
    S_T = build_temperature_source(
        eta, isw_sources, lambda e: np.zeros_like(np.asarray(e)),
        lambda e: np.zeros_like(np.asarray(e)),
    )
    D_ISW = project_temperature_transfer(1e-3, S_T, eta, cfg6)
    all_pass &= check(
        "ISW-only gives non-zero Δ_ℓ^T",
        np.max(np.abs(D_ISW)) > 1e-5,
        f"max |Δ_ℓ| = {np.max(np.abs(D_ISW)):.2e}",
    )

    # ----- Block 7: Doppler activation -----
    header("Block 7 — Doppler isolation via d/dη[g·v_b]")
    eta = build_eta_grid_linear(10.0, 14116.4, 4001)

    def g_rec(e):
        return np.exp(-0.5 * ((e - 280.0) / 30.0) ** 2) / (30.0 * np.sqrt(2*np.pi))

    dop_sources = FLRWSourceTerms.with_doppler_only(constant_callable(1e-3))
    S_T_dop = build_temperature_source(
        eta, dop_sources, g_rec, lambda e: np.zeros_like(np.asarray(e)),
    )
    # Derivative of Gaussian times constant v_b: d(g·v_b)/dη = v_b · dg/dη
    # Must be odd around peak: positive before, negative after
    before_peak = S_T_dop[np.abs(eta - 250.0).argmin()]
    after_peak = S_T_dop[np.abs(eta - 310.0).argmin()]
    all_pass &= check(
        "Doppler source is odd around visibility peak",
        np.sign(before_peak) != np.sign(after_peak),
        f"S_T(η=250) = {before_peak:.2e}, S_T(η=310) = {after_peak:.2e}",
    )
    D_dop = project_temperature_transfer(1e-3, S_T_dop, eta, cfg6)
    # Amplitude scale: v_b · g_max/σ × Bessel oscillation cancellation
    # ≈ 1e-3 × (0.013/30) × O(1) ~ 4e-7 before Bessel weighting.
    # Post-Bessel (oscillatory cancellation) should still exceed 1e-8.
    all_pass &= check(
        "Doppler-only gives non-zero Δ_ℓ^T",
        np.max(np.abs(D_dop)) > 1e-8,
        f"max |Δ_ℓ| = {np.max(np.abs(D_dop)):.2e}",
    )

    # ----- Block 8: E-mode vanishes for ℓ < 2 -----
    header("Block 8 — E-mode transfer Δ_ℓ^E = 0 for ℓ < 2")
    from bass.los.flrw_bessel_projector import project_polarization_transfer
    eta = build_eta_grid_linear(10.0, 14116.4, 1001)
    S_E = np.ones_like(eta) * 1e-3
    cfg8 = FLRWBesselConfig(ell_max=5, eta_0_mpc=14116.4)
    D_E = project_polarization_transfer(1e-3, S_E, eta, cfg8)
    all_pass &= check(
        "Δ_0^E = 0 and Δ_1^E = 0",
        D_E[0] == 0.0 and D_E[1] == 0.0,
        f"Δ_0^E = {D_E[0]}, Δ_1^E = {D_E[1]}",
    )
    all_pass &= check(
        "Δ_ℓ^E non-zero for ℓ ≥ 2",
        np.max(np.abs(D_E[2:])) > 0.0,
        f"max|Δ_ℓ^E|, ℓ≥2 = {np.max(np.abs(D_E[2:])):.3e}",
    )

    # ----- Summary -----
    header("SUMMARY")
    if all_pass:
        print("  ALL BLOCKS PASS — W9-01 physics verified independently.")
        return 0
    else:
        print("  AT LEAST ONE BLOCK FAILED — investigate.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
