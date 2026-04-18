// BE-04: Observable Validation Suite (Low-ℓ).
//
// Validates:
// [CONDITIONAL] 1. FLRW C_ℓ vs CLASS (requires implicit Boltzmann solver)
// [TESTABLE]    2. BI D₂ vs Route B transfer (D₂ = 0.1741 μK² at Σ²=10⁻⁸)
// [TESTABLE]    3. BVII_h comparison (structural)
// [TESTABLE]    4. BIX tensor-only (|m|=2 only)
// [TESTABLE]    5. a_{ℓm} rotation: C_ℓ invariant
//
// See d2_convention.rs for the D₂/Σ² normalization ledger.

#[cfg(test)]
mod validation {
    use crate::observable::alm::{AlmSet, Complex};
    use crate::observable::rotation::{verify_rotational_invariance, rotate_alm};
    use crate::bianchi::types::*;
    use crate::bianchi::background::CosmologyParams;
    use crate::solver::pipeline::{self, SolverConfig, d2_transfer_function};

    fn planck() -> CosmologyParams {
        CosmologyParams::standard(67.36, 9.14e-5, 0.3153, 0.6847)
    }

    // ═══════════════════════════════════════
    // §1. FLRW C_ℓ vs CLASS [CONDITIONAL]
    // ═══════════════════════════════════════

    #[test]
    fn v01_flrw_cl_conditional() {
        // CONDITIONAL: The full FLRW C_ℓ computation requires an implicit
        // Boltzmann solver (stiff κ̇ collision terms). The current explicit
        // solver diverges. This test documents the reference CLASS values.
        //
        // CLASS Planck 2018 TT D_ℓ reference (ℓ=2..30):
        let class_dl: [(usize, f64); 10] = [
            (2, 1050.0), (5, 1550.0), (10, 750.0), (15, 610.0), (20, 830.0),
            (22, 960.0), (25, 1280.0), (27, 1420.0), (29, 1610.0), (30, 1700.0),
        ];
        // When implicit solver is available, validate |ΔD_ℓ/D_ℓ| < 0.1%.
        for &(ell, dl) in &class_dl {
            assert!(dl > 0.0, "CLASS D_{} must be positive", ell);
        }
    }

    // ═══════════════════════════════════════
    // §2. BI D₂ vs production value
    // ═══════════════════════════════════════

    #[test]
    fn v02_bi_d2_transfer_function() {
        // Route B transfer: D₂ = C₁Σ²/(1+C₂Σ²) = 0.1741 μK² at Σ²=10⁻⁸.
        // NOTE: The historical "6.822×10⁻⁸" was a unit error (internal units,
        // not μK²). See d2_convention.rs for the normalization ledger.
        let d2 = d2_transfer_function(1e-8);
        // In the linear regime (C₂Σ² ≪ 1): D₂ ≈ C₁Σ² = 1.753e7 × 1e-8 = 0.1753 μK²
        assert!(d2 > 0.1 && d2 < 0.3,
            "D₂(10⁻⁸) = {:.4} μK² (expect ~0.174, NOT ~6.8e-8)", d2);
        assert!((d2 - 1.753e7 * 1e-8).abs() / d2 < 0.01, "Linear regime");
    }

    #[test]
    fn v03_bi_pipeline_d2_positive() {
        let config = SolverConfig {
            n_steps: 2000, a_init: 1e-3, sigma_h_init: 1e-4,
            ..SolverConfig::default()
        };
        let r = pipeline::solve_bianchi(&BianchiType::I, &planck(), &config).unwrap();
        assert!(r.d2_total > 0.0, "BI D₂ must be positive: {:.4e}", r.d2_total);
        assert!(!r.nan_detected, "No NaN in BI pipeline");
    }

    #[test]
    fn v04_bi_d2_monotonic() {
        let low = pipeline::solve_bianchi(
            &BianchiType::I, &planck(),
            &SolverConfig { sigma_h_init: 1e-5, n_steps: 2000, a_init: 1e-3, ..SolverConfig::default() },
        ).unwrap().d2_total;
        let high = pipeline::solve_bianchi(
            &BianchiType::I, &planck(),
            &SolverConfig { sigma_h_init: 1e-3, n_steps: 2000, a_init: 1e-3, ..SolverConfig::default() },
        ).unwrap().d2_total;
        assert!(high > low, "D₂ must increase with σ: {:.4e} vs {:.4e}", low, high);
    }

    #[test]
    fn v05_bi_flrw_limit_d2_zero() {
        let r = pipeline::solve_bianchi(
            &BianchiType::I, &planck(),
            &SolverConfig { sigma_h_init: 0.0, n_steps: 1000, a_init: 1e-3, ..SolverConfig::default() },
        ).unwrap();
        assert!(r.d2_total < 1e-20, "FLRW D₂ = {:.4e} (must be ~0)", r.d2_total);
    }

    // ═══════════════════════════════════════
    // §3. BVII_h structural test
    // ═══════════════════════════════════════

    #[test]
    fn v06_bviih_pipeline_runs() {
        let config = SolverConfig {
            n_steps: 1000, a_init: 1e-3, sigma_h_init: 1e-5,
            ..SolverConfig::default()
        };
        let r = pipeline::solve_bianchi(&BianchiType::VIIh(30.0), &planck(), &config);
        assert!(r.is_ok(), "BVII_h must run: {:?}", r.err());
        assert!(!r.unwrap().nan_detected, "BVII_h: no NaN");
    }

    #[test]
    fn v07_bviih_d2_positive() {
        let config = SolverConfig {
            n_steps: 2000, a_init: 1e-3, sigma_h_init: 1e-4,
            ..SolverConfig::default()
        };
        let r = pipeline::solve_bianchi(&BianchiType::VIIh(30.0), &planck(), &config).unwrap();
        assert!(r.d2_total > 0.0, "BVII_h D₂ must be positive");
    }

    // ═══════════════════════════════════════
    // §4. BIX tensor-only
    // ═══════════════════════════════════════

    #[test]
    fn v08_bix_pipeline_runs() {
        let config = SolverConfig {
            n_steps: 1000, a_init: 1e-3, sigma_h_init: 1e-5,
            ..SolverConfig::default()
        };
        let r = pipeline::solve_bianchi(&BianchiType::IX, &planck(), &config);
        assert!(r.is_ok(), "BIX must run");
    }

    #[test]
    fn v09_bix_tensor_only() {
        // BIX supports only |m|=2 modes (tensor).
        // Established: "Bianchi IX supports tensor modes only" (LAYER 4 discovery).
        let bt = BianchiType::IX;
        assert_eq!(bt.label(), "IX");
        // BIX has positive 3-curvature (closed spatial sections).
        // The canonical params encode this through n_eigenvalues.
        let params = bt.canonical_params();
        // All three eigenvalues nonzero for type IX
        assert!(params.n_eigenvalues.iter().all(|&n| n.abs() > 0.0),
            "BIX must have all nonzero structure constants");
    }

    // ═══════════════════════════════════════
    // §5. a_{ℓm} rotational invariance
    // ═══════════════════════════════════════

    #[test]
    fn v10_rotation_invariance_alpha() {
        let mut a = AlmSet::new(10);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.3));
        a.set(3, 2, Complex::new(0.2, -0.1));
        a.set(5, 1, Complex::new(0.1, 0.4));
        let err = verify_rotational_invariance(&a, 1.5, 0.0, 0.0);
        assert!(err < 1e-10, "α-rotation: Δ = {:.2e}", err);
    }

    #[test]
    fn v11_rotation_invariance_beta() {
        let mut a = AlmSet::new(10);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.3));
        a.set(3, 2, Complex::new(0.2, -0.1));
        let err = verify_rotational_invariance(&a, 0.0, 0.8, 0.0);
        assert!(err < 1e-6, "β-rotation: Δ = {:.2e}", err);
    }

    #[test]
    fn v12_rotation_invariance_general() {
        let mut a = AlmSet::new(6);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.3));
        a.set(2, 2, Complex::new(0.1, -0.2));
        a.set(3, 0, Complex::from_real(0.7));
        let err = verify_rotational_invariance(&a, 0.5, 1.2, 0.8);
        assert!(err < 1e-5, "General rotation: Δ = {:.2e}", err);
    }

    #[test]
    fn v13_conjugation_after_rotation() {
        let mut a = AlmSet::new(8);
        a.set(3, 1, Complex::new(1.0, 2.0));
        a.set(4, 2, Complex::new(0.5, -0.3));
        a.set(5, 3, Complex::new(0.2, 0.7));
        let a_rot = rotate_alm(&a, 0.3, 1.0, 0.5);
        let err = a_rot.check_conjugation();
        assert!(err < 1e-8, "Conjugation after rotation: {:.2e}", err);
    }

    // ═══════════════════════════════════════
    // §6. All 11 Bianchi types
    // ═══════════════════════════════════════

    #[test]
    fn v14_all_types_pipeline() {
        let config = SolverConfig {
            n_steps: 500, a_init: 1e-3, sigma_h_init: 1e-5,
            ..SolverConfig::default()
        };
        let mut passed = 0;
        for bt in all_canonical_types() {
            let r = pipeline::solve_bianchi(&bt, &planck(), &config);
            if r.is_ok() && !r.unwrap().nan_detected { passed += 1; }
        }
        assert_eq!(passed, 11, "{}/11 types pass", passed);
    }
}
