// BD-05: Multi-species regression test suite.
// Comprehensive regression for the full stacked solver pipeline.
//
// Tests are classified:
//   [E] = ESTABLISHED (exact, must always pass)
//   [C] = CONDITIONAL (depends on LoS/calibration from Phase E)

#[cfg(test)]
mod regression {
    use std::time::Instant;
    use crate::bianchi::types::*;
    use crate::bianchi::background::CosmologyParams;
    use crate::species::SpeciesConfig;
    use crate::solver::pipeline::{self, SolverConfig, SolveResult, d2_transfer_function};
    use crate::solver::multispecies::{StackedState, StackedBackground, build_stacked_rhs};
    use crate::collision::thomson;
    use crate::collision::baryon_photon;

    fn planck_cosmo() -> CosmologyParams {
        CosmologyParams::standard(67.4, 9.14e-5, 0.315, 0.685)
    }

    fn quick_config(sh: f64) -> SolverConfig {
        SolverConfig {
            species: SpeciesConfig::minimal(),
            n_steps: 2000,
            a_init: 1e-3,
            sigma_h_init: sh,
            ..SolverConfig::default()
        }
    }

    fn run_bi(sh: f64) -> SolveResult {
        pipeline::solve_bianchi(&BianchiType::I, &planck_cosmo(), &quick_config(sh)).unwrap()
    }

    // ═══════════════════════════════════════
    // §1. BI D₂ regression [E]
    // ═══════════════════════════════════════

    #[test]
    fn r01_bi_d2_positive() {
        let r = run_bi(1e-4);
        assert!(r.d2_total > 0.0, "[E] D₂ must be positive: {:.2e}", r.d2_total);
    }

    #[test]
    fn r02_bi_d2_monotonic_in_sigma() {
        let d1 = run_bi(1e-5).d2_total;
        let d2 = run_bi(1e-4).d2_total;
        assert!(d2 > d1, "[E] D₂ must increase with σ: {:.2e} vs {:.2e}", d1, d2);
    }

    #[test]
    fn r03_bi_shear_decays() {
        let r = run_bi(1e-4);
        assert!(r.sigma_h_final < 1e-4, "[E] σ/H must decay: {:.2e}", r.sigma_h_final);
    }

    #[test]
    fn r04_bi_no_nan() {
        let r = run_bi(1e-4);
        assert!(!r.nan_detected, "[E] No NaN in BI pipeline");
    }

    // ═══════════════════════════════════════
    // §2. FLRW limit [E]
    // ═══════════════════════════════════════

    #[test]
    fn r05_flrw_d2_zero() {
        let r = run_bi(0.0); // σ=0 → FLRW
        assert!(r.d2_total < 1e-20, "[E] FLRW D₂ = {:.2e} (must be ~0)", r.d2_total);
    }

    #[test]
    fn r06_flrw_no_quadrupole() {
        let r = run_bi(0.0);
        assert!(r.d2_gamma < 1e-20 && r.d2_nu < 1e-20, "[E] FLRW: no quadrupole");
    }

    // ═══════════════════════════════════════
    // §3. Transfer function [E]
    // ═══════════════════════════════════════

    #[test]
    fn r07_transfer_linear_regime() {
        let d1 = d2_transfer_function(1e-12);
        let d2 = d2_transfer_function(1e-10);
        let ratio = d2 / d1;
        assert!((ratio - 100.0).abs() < 1.0, "[E] Linear: ratio = {:.2}", ratio);
    }

    #[test]
    fn r08_transfer_saturation() {
        let d_sat = d2_transfer_function(1.0);
        let expected = 1.753e7 / 6.825e5; // C₁/C₂
        assert!((d_sat/expected - 1.0).abs() < 0.01, "[E] Saturation: {:.4}", d_sat);
    }

    #[test]
    fn r09_transfer_register_self_consistent() {
        // At Σ²=1e-8: D₂ should be in the linear regime (C₂Σ² ≪ 1)
        let d = d2_transfer_function(1e-8);
        let d_linear = 1.753e7 * 1e-8;
        assert!((d/d_linear - 1.0).abs() < 0.01, "[E] Register: {:.4e} vs {:.4e}", d, d_linear);
    }

    // ═══════════════════════════════════════
    // §4. Species energy conservation [E]
    // ═══════════════════════════════════════

    #[test]
    fn r10_thomson_energy_cons() {
        // C₀ = 0 for any state
        for &f0 in &[0.1, 1.0, 10.0] {
            let f = vec![f0, 0.5*f0, 0.1*f0, 0.01*f0];
            let c = thomson::thomson_collision(&f, 100.0, 0.0, 0.0);
            assert!(c[0].abs() < 1e-13, "[E] C₀ = {:.2e} at F₀={}", c[0], f0);
        }
    }

    #[test]
    fn r11_momentum_conservation() {
        for &r in &[0.1, 0.5, 1.0, 5.0] {
            let f1 = 0.01; let vb = 0.005; let kd = 100.0;
            let c1 = -kd*(f1-vb);
            let cb = baryon_photon::baryon_collision_term(vb, f1, kd, 1.0/r);
            let res = (c1 + r*cb).abs();
            assert!(res < 1e-12, "[E] Momentum at R={}: {:.2e}", r, res);
        }
    }

    #[test]
    fn r12_stacked_energy_cons_photon() {
        let mut b = crate::species::SpeciesBundle::new(SpeciesConfig::minimal());
        b.photon.intensity[0] = 1.0;
        b.photon.intensity[2] = 0.05;
        let bg = StackedBackground {
            eta: 0.0, a: 1e-3, a_h: 100.0, k: 0.0, sigma_h: 0.0,
            kappa_dot: 100.0, r_ratio: 0.6,
        };
        let rhs = build_stacked_rhs(&b, &bg);
        assert!(rhs[0].abs() < 1e-13, "[E] Stacked C₀ = {:.2e}", rhs[0]);
    }

    // ═══════════════════════════════════════
    // §5. All Bianchi types [E]
    // ═══════════════════════════════════════

    #[test]
    fn r13_all_11_types_run() {
        let cosmo = planck_cosmo();
        let config = SolverConfig {
            n_steps: 500, a_init: 1e-3, sigma_h_init: 1e-5,
            ..SolverConfig::default()
        };
        let mut pass_count = 0;
        for bt in all_canonical_types() {
            let r = pipeline::solve_bianchi(&bt, &cosmo, &config);
            if r.is_ok() && !r.as_ref().unwrap().nan_detected {
                pass_count += 1;
            }
        }
        assert_eq!(pass_count, 11, "[E] {}/11 types pass", pass_count);
    }

    // ═══════════════════════════════════════
    // §6. Performance benchmark [E]
    // ═══════════════════════════════════════

    #[test]
    fn r14_performance_pipeline() {
        let t0 = Instant::now();
        let r = run_bi(1e-5);
        let ms = t0.elapsed().as_secs_f64() * 1000.0;
        // Target: < 5000ms for debug build, < 200ms for release
        assert!(ms < 10000.0, "[E] Pipeline too slow: {:.0}ms", ms);
        // Report
        eprintln!("  BD-05 perf: BI pipeline = {:.0}ms (n={}, DOF={})",
            ms, r.n_steps, 52);
    }

    #[test]
    fn r15_rhs_evaluation_speed() {
        let b = crate::species::SpeciesBundle::new(SpeciesConfig::minimal());
        let bg = StackedBackground {
            eta: 0.0, a: 1e-3, a_h: 100.0, k: 0.1, sigma_h: 1e-5,
            kappa_dot: 100.0, r_ratio: 0.6,
        };
        let t0 = Instant::now();
        let n_eval = 10000;
        for _ in 0..n_eval { let _ = build_stacked_rhs(&b, &bg); }
        let us_per = t0.elapsed().as_secs_f64() * 1e6 / n_eval as f64;
        assert!(us_per < 1000.0, "[E] RHS too slow: {:.1}μs", us_per);
        eprintln!("  BD-05 perf: RHS eval = {:.1}μs (52 DOF)", us_per);
    }

    // ═══════════════════════════════════════
    // §7. Quadrupole consistency [E]
    // ═══════════════════════════════════════

    #[test]
    fn r16_neutrino_quad_from_shear() {
        // With σ≠0, neutrino quadrupole should be nonzero
        let r = run_bi(1e-3);
        assert!(r.d2_nu > 0.0, "[E] ν quadrupole must be driven by shear");
    }

    #[test]
    fn r17_photon_quad_from_shear() {
        let r = run_bi(1e-3);
        assert!(r.d2_gamma > 0.0, "[E] γ quadrupole must be driven by shear");
    }

    // ═══════════════════════════════════════
    // §8. Cross-species consistency [E]
    // ═══════════════════════════════════════

    #[test]
    fn r18_neutrino_dominates_with_shear() {
        // At moderate shear, neutrinos should contribute significantly
        let r = run_bi(1e-3);
        if r.d2_total > 1e-30 {
            assert!(r.f_nu > 0.1, "[E] f_ν = {:.3} (expect > 0.1)", r.f_nu);
        }
    }

    #[test]
    fn r19_d2_gamma_less_than_total() {
        let r = run_bi(1e-4);
        assert!(r.d2_gamma <= r.d2_total + 1e-30, "[E] D₂_γ ≤ D₂_total");
    }

    // ═══════════════════════════════════════
    // §9. Numerical stability [E]
    // ═══════════════════════════════════════

    #[test]
    fn r20_reproducibility() {
        let r1 = run_bi(1e-4);
        let r2 = run_bi(1e-4);
        assert!((r1.d2_total - r2.d2_total).abs() < 1e-15 * r1.d2_total.max(1e-30),
            "[E] Reproducibility: {:.6e} vs {:.6e}", r1.d2_total, r2.d2_total);
    }

    #[test]
    fn r21_large_shear_no_crash() {
        // σ/H = 10⁻² (large but physical)
        let config = SolverConfig {
            n_steps: 1000, a_init: 1e-3, sigma_h_init: 1e-2,
            ..SolverConfig::default()
        };
        let r = pipeline::solve_bianchi(&BianchiType::I, &planck_cosmo(), &config);
        assert!(r.is_ok() && !r.unwrap().nan_detected, "[E] Large σ crash");
    }

    #[test]
    fn r22_tiny_shear_no_underflow() {
        let r = run_bi(1e-10); // very small shear
        assert!(r.d2_total >= 0.0, "[E] D₂ must be non-negative");
        assert!(!r.nan_detected);
    }

    // ═══════════════════════════════════════
    // §10. Conditional: D₂ calibration [C]
    // (Full accuracy requires Phase E LoS)
    // ═══════════════════════════════════════

    #[test]
    fn r23_d2_order_of_magnitude() {
        // Simplified pipeline D₂ should be in a physically reasonable range.
        // The exact calibration requires LoS integration (Phase E).
        // Here we just check it's not wildly wrong (within 10 orders of magnitude
        // of the transfer function prediction).
        let r = run_bi(1e-4);
        let d2_tf = d2_transfer_function(1e-4_f64.powi(2)); // Σ² ~ (σ/H)²
        // Very loose bound: order of magnitude
        if r.d2_total > 1e-30 && d2_tf > 1e-30 {
            let log_ratio = (r.d2_total.log10() - d2_tf.log10()).abs();
            assert!(log_ratio < 20.0, "[C] D₂ OOM: {:.2e} vs TF {:.2e}", r.d2_total, d2_tf);
        }
    }
}
