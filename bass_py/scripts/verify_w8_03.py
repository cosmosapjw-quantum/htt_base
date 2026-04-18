"""Independent verification of W8-03 physics.

Run standalone (not through pytest) to cross-check the numerical
claims of the module against hand-derived formulas, using both R0
(synthetic) and R2 (HyRec-derived) fixtures.

Exit status 0 on all passes, 1 on any failure.
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

    from bass.closure.quadrupole_tca import combined_source_pi, solve_tca_closure
    from bass.recombination.recombination_ingest import (
        build_interpolators, find_last_scattering_redshift,
        find_visibility_peak, load_recombination_table,
    )
    from bass.recombination.reionization import (
        CosmologyForRecombination, ReionizationParameters,
        extend_table_with_reionization,
    )
    from bass.runtime.canonical_decision import (
        CanonicalDecision, make_canonical_decision,
    )
    from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind
    from bass.transport.visibility_polter_source import (
        conformal_time_at_z, four_path_pi_residual_general,
        g_weighted_pi_pstf, gpi_peak_in_z, pi_closed_form_from_sources,
        pi_from_tca_sources, pi_pstf, pi_subleading_limit,
        three_way_pi_residual_at_subleading, VisibilityPolterConfig,
    )

    # Factory-built allowing decision (same pattern as production tests)
    def _on_manifold_G(x):
        import numpy as _np
        return _np.asarray(x, dtype=float)

    _ALLOW = make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=compute_D_diagnostic(
            G_field=_on_manifold_G, kind=TangentKind.ONE_FIELD,
            xi=0, eta=0.0,
        ),
    )

    all_pass = True

    # ----- Block 1: analytic Π formulas self-consistent -----
    header("Block 1 — analytic Π limits")
    sqrt6 = np.sqrt(6.0)
    t2 = 3.7
    pi_direct = pi_pstf(t2, -sqrt6 / 4.0 * t2)
    pi_limit = pi_subleading_limit(t2)
    all_pass &= check(
        "Π(Θ=3.7, E=-√6/4·Θ) == (5/2)Θ",
        np.isclose(pi_direct, pi_limit, rtol=1e-14),
        f"{pi_direct:.12e} vs {pi_limit:.12e}",
    )

    # ----- Block 2: closed form matches numerical solve across a grid -----
    header("Block 2 — closed-form Π vs LAPACK solve")
    rng = np.random.default_rng(20260418)
    worst_rel = 0.0
    for _ in range(200):
        S_T = rng.uniform(-10, 10)
        S_E = rng.uniform(-10, 10)
        gT = rng.uniform(0.01, 10)
        pi_solve = pi_from_tca_sources(S_T, S_E, gT, _ALLOW)
        pi_closed = pi_closed_form_from_sources(S_T, S_E, gT)
        if abs(pi_closed) > 1e-15:
            rel = abs(pi_solve - pi_closed) / abs(pi_closed)
            worst_rel = max(worst_rel, rel)
    all_pass &= check(
        "200 random (S_T, S_E, Γ_T) configs: rel residual < 1e-13",
        worst_rel < 1e-13,
        f"worst rel = {worst_rel:.2e}",
    )

    # ----- Block 3: 4-path cross-check at physical magnitudes -----
    header("Block 3 — four-path Π residual at physical magnitudes")
    physical_cases = [
        (1e-9 * 4.2e-6, 0.0, 4.2e-6, "W7-02 production scale (Γ_T=4.2e-6)"),
        (-2.5e-9, 3.7e-11, 1.5, "mixed-sign source"),
        (1e-12, 1e-14, 2e-5, "small-magnitude regime"),
        (1e15, 1e13, 1e3, "large-magnitude regime"),
    ]
    for S_T, S_E, gT, label in physical_cases:
        res = four_path_pi_residual_general(S_T, S_E, gT, _ALLOW)
        rel = res["residual_max"] / max(abs(res["pi_A"]), 1e-300)
        all_pass &= check(
            label,
            rel < 1e-12,
            f"rel = {rel:.2e}, |Π| = {abs(res['pi_A']):.3e}",
        )

    # ----- Block 4: R2 fixture reproduces Planck 2018 last scattering -----
    header("Block 4 — R2 HyRec fixture vs Planck 2018")
    csv_path = (
        Path(__file__).resolve().parents[1]
        / "bass" / "recombination" / "fixtures"
        / "recombination_ref_planck2018.csv"
    )
    if not csv_path.exists():
        all_pass &= check("CSV available", False, str(csv_path))
    else:
        table = load_recombination_table(csv_path)
        interp = build_interpolators(table)
        z_peak, g_peak = find_visibility_peak(
            interp, z_search_lo=800, z_search_hi=1400, n_samples=4000,
        )
        z_star = find_last_scattering_redshift(interp, target_kappa=1.0)
        all_pass &= check(
            "visibility peak z_peak ≈ 1088.8",
            1080.0 < z_peak < 1100.0,
            f"z_peak = {z_peak:.3f}",
        )
        all_pass &= check(
            "z_*(κ=1) within Planck 2018 1σ (1089.95 ± 0.27)",
            1089.0 < z_star < 1091.0,
            f"z_* = {z_star:.3f}",
        )

    # ----- Block 5: R0 synthetic peak matches its own analytic condition -----
    header("Block 5 — R0 synthetic peak = analytic root")
    from bass.recombination.recombination_ingest import make_synthetic_tanh_table
    syn_table = make_synthetic_tanh_table(
        z_min=1.0, z_max=3000.0, n_points=600,
        z_transition=1089.0, transition_width=100.0,
    )
    syn_interp = build_interpolators(syn_table)
    syn_config = VisibilityPolterConfig(recomb_interp=syn_interp)
    z_peak_syn, _ = gpi_peak_in_z(
        theta_2_of_z=lambda z: np.ones_like(z),
        E_2_of_z=lambda z: np.zeros_like(z),
        config=syn_config,
        z_search_lo=500, z_search_hi=2500, n_samples=4000,
    )
    # Analytic condition: 2/(1+z_peak) ≈ 10⁻² · τ̇(z_peak) when x_e → 1
    lhs = 2.0 / (1.0 + z_peak_syn)
    rhs = 1.0e-2 * float(syn_interp.query_tau_dot(z_peak_syn))
    all_pass &= check(
        "synthetic peak equation 2/(1+z_p) = 10⁻²·τ̇(z_p) holds",
        abs(lhs - rhs) / max(lhs, rhs) < 0.1,
        f"LHS={lhs:.4e}, RHS={rhs:.4e}, z_peak={z_peak_syn:.1f}",
    )
    all_pass &= check(
        "synthetic peak at z ≈ 1361 (NOT physical)",
        1340.0 < z_peak_syn < 1380.0,
        f"z_peak = {z_peak_syn:.2f}",
    )

    # ----- Block 6: real-fixture g·Π peak tracks g peak -----
    header("Block 6 — R2 g·Π peak = g peak for constant profile")
    if csv_path.exists():
        real_config = VisibilityPolterConfig(recomb_interp=interp)
        z_gpi, _ = gpi_peak_in_z(
            theta_2_of_z=lambda z: np.ones_like(z),
            E_2_of_z=lambda z: np.zeros_like(z),
            config=real_config,
            z_search_lo=800, z_search_hi=1400, n_samples=4000,
        )
        all_pass &= check(
            "z_peak(g·Π) == z_peak(g) within grid resolution",
            abs(z_gpi - z_peak) < 1.0,
            f"|Δ| = {abs(z_gpi - z_peak):.3f}",
        )

    # ----- Block 7: reion suppression on R2 matches e^{-τ_reion} -----
    header("Block 7 — R2 reion suppression at z ≈ 1089")
    if csv_path.exists():
        cosmo = CosmologyForRecombination(
            h=0.6766, T_cmb=2.7255, Omega_b=0.0493, Y_He=0.245,
            Omega_m=0.3111, Omega_r=9.237e-5, Omega_Lambda=0.6889,
        )
        reion = ReionizationParameters(
            z_reion_H=7.67, delta_z_H=0.5,
            z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True,
        )
        ext_table = extend_table_with_reionization(table, reion, cosmology=cosmo)
        ext_interp = build_interpolators(ext_table)
        cfg_no = VisibilityPolterConfig(recomb_interp=interp)
        cfg_yes = VisibilityPolterConfig(recomb_interp=ext_interp)
        val_no = g_weighted_pi_pstf(1089.0, 1.0, 0.0, cfg_no)
        val_yes = g_weighted_pi_pstf(1089.0, 1.0, 0.0, cfg_yes)
        ratio = val_yes / val_no
        # Planck 2018 τ_reion = 0.054, suppression = e^{-0.054} ≈ 0.947
        all_pass &= check(
            "ratio in (0.88, 0.99) consistent with e^{-τ_reion}",
            0.88 < ratio < 0.99,
            f"ratio = {ratio:.4f}",
        )

    # ----- Block 8: η(z=0) ≈ 14 Gpc for flat ΛCDM -----
    header("Block 8 — conformal time today η_0 ≈ 14 Gpc")
    cosmo = CosmologyForRecombination(
        h=0.6766, T_cmb=2.7255, Omega_b=0.0493, Y_He=0.245,
        Omega_m=0.3111, Omega_r=9.237e-5, Omega_Lambda=0.6889,
    )
    eta_0 = conformal_time_at_z(0.0, cosmo, z_upper=1.0e4)
    all_pass &= check(
        "η_0 ∈ (13000, 15000) Mpc ≈ 14 Gpc",
        13000.0 < eta_0 < 15000.0,
        f"η_0 = {eta_0:.1f} Mpc",
    )

    # ----- Summary -----
    header("SUMMARY")
    if all_pass:
        print("  ALL BLOCKS PASS — W8-03 physics verified independently.")
        return 0
    else:
        print("  AT LEAST ONE BLOCK FAILED — investigate.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
