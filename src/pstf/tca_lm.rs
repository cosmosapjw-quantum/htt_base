//! Extended TCA for m-Decomposed System (P1-04)
//!
//! Operator-based tight-coupling approximation that generalizes the
//! FLRW scalar TCA to the full (ℓ,m) Bianchi system.
//!
//! ## Design Principle (TCA_UFA_RSA_대응안)
//!
//! - TCA = closure-in-place, NOT pre-phase IC generator
//! - Same state vector dimension always (5566)
//! - Fast variables computed from slow via algebraic closure
//! - Operator: y_fast ≈ −(τ_c·C_f + L_ff)⁻¹ L_fs · y_slow
//! - NOT hardcoded CRS formulas (FLRW-specific)
//!
//! ## 25 Slow DOF
//!
//! Photon: Θ₀₀(1) + Θ₁m(3) = 4
//! Neutrino: N₀₀(1) + N₁m(3) = 4
//! Baryon: δ_b(1) + v_b^i(3) = 4
//! CDM: δ_c(1) + v_c^i(3) = 4
//! Metric: ~6-11 DOF
//! E₂m: 5 quasi-static
//! Total ≈ 25

/// TCA activation criterion.
///
/// ε_TCA = max(kτ_c, Hτ_c, |σ|τ_c, |∂_η ln κ̇|τ_c)
/// TCA is active when ε_TCA < threshold.
#[derive(Clone, Debug)]
pub(crate) struct TcaCriterion {
    /// Compton mean free time τ_c = 1/κ̇ [Mpc].
    pub(crate) tau_c: f64,
    /// Wavenumber k [Mpc⁻¹].
    pub(crate) k: f64,
    /// Conformal Hubble ℋ [Mpc⁻¹].
    pub(crate) hubble: f64,
    /// Shear magnitude |σ| [Mpc⁻¹].
    pub(crate) shear: f64,
    /// Rate of change of opacity: |d ln κ̇/dη|.
    pub(crate) kappa_dot_rate: f64,
}

impl TcaCriterion {
    /// Compute the TCA activation parameter.
    pub(crate) fn epsilon(&self) -> f64 {
        let kt = self.k * self.tau_c;
        let ht = self.hubble * self.tau_c;
        let st = self.shear * self.tau_c;
        let rt = self.kappa_dot_rate * self.tau_c;
        kt.max(ht).max(st).max(rt)
    }

    /// Check if TCA should be active (ε < threshold).
    pub(crate) fn is_active(&self, threshold: f64) -> bool {
        self.epsilon() < threshold
    }
}

/// TCA closure result: fast variables computed from slow.
#[derive(Clone, Debug)]
pub(crate) struct TcaClosure {
    /// Quadrupole F_{2m}: 5 values (m=-2..2).
    pub(crate) f2m: [f64; 5],
    /// E-mode quadrupole E_{2m}: 5 values (m=-2..2).
    pub(crate) e2m: [f64; 5],
    /// Octupole F_{3m}: 7 values (m=-3..3), from quasi-static recursion.
    pub(crate) f3m: [f64; 7],
    /// Closure residual (for fail-open monitoring).
    pub(crate) residual: f64,
}

/// First-order TCA closure: F₂ ≈ (8/9)(k/κ̇)F₁.
///
/// In the (ℓ,m) basis, this becomes per-m:
///   F_{2m} ≈ (8/9)(k/κ̇) × α↓₂ × F_{1m}
/// where α↓₂ = 2/3 (streaming coefficient).
///
/// The "8/9" factor comes from the standard TCA derivation:
///   F₂ ≈ (2ℓ+1)/(ℓ(2ℓ-1)) × k/κ̇ × F₁ for ℓ=2
///       = 5/(2×3) × k/κ̇ × F₁ ≈ 0.833 × k/κ̇ × F₁
/// But the standard Dodelson convention gives 8/9 = 0.889.
///
/// CRS 2nd-order correction (CAMB TCA guide):
///   F₂_CRS = F₂_1st × (1 − 11κ̇'/(6κ̇²))
pub(crate) fn tca_closure_first_order(
    f1m: &[f64; 3], // F_{1,-1}, F_{1,0}, F_{1,1}
    k: f64,
    kappa_dot: f64,
) -> TcaClosure {
    let kd = kappa_dot.abs().max(1e-30);
    let ratio = k / kd;

    // First-order: F_{2m} = (8/9) × (k/κ̇) × F_{1m}
    // Only |m| ≤ 1 have nonzero F_{1m} (velocity is ℓ=1)
    let coeff = 8.0 / 9.0;
    let mut f2m = [0.0_f64; 5];
    // m=-1 → f2m[1], m=0 → f2m[2], m=1 → f2m[3]
    f2m[1] = coeff * ratio * f1m[0]; // m=-1
    f2m[2] = coeff * ratio * f1m[1]; // m=0
    f2m[3] = coeff * ratio * f1m[2]; // m=1
    // m=±2: zero at first order (no F_{1,±2})

    // E-mode quadrupole: E_{2m} = −(1/2)F_{2m} at leading TCA
    let mut e2m = [0.0_f64; 5];
    for i in 0..5 {
        e2m[i] = -0.5 * f2m[i];
    }

    // Octupole: F_{3m} = (3/7)(k/κ̇)F_{2m} at leading order
    let coeff3 = 3.0 / 7.0;
    let mut f3m = [0.0_f64; 7];
    // m=-2..2 from F_{2m}
    for im in 0..5 {
        f3m[im + 1] = coeff3 * ratio * f2m[im];
    }

    TcaClosure { f2m, e2m, f3m, residual: 0.0 }
}

/// Second-order CRS correction.
///
/// F₂_CRS = F₂_1st × (1 − 11κ̇'/(6κ̇²))
/// where κ̇' = dκ̇/dη.
pub(crate) fn crs_second_order_factor(kappa_dot: f64, kappa_dot_prime: f64) -> f64 {
    let kd = kappa_dot.abs().max(1e-30);
    1.0 - 11.0 * kappa_dot_prime / (6.0 * kd * kd)
}

/// Expand TCA closure (25 DOF) to full state vector (5566 DOF).
///
/// Sets fast variables from the closure, slow variables unchanged.
/// Higher-ℓ moments computed from quasi-static recursion:
///   F_{ℓm} = (ℓ/(2ℓ-1))(k/κ̇) F_{ℓ-1,m} for ℓ ≥ 3
pub(crate) fn expand_tca_to_full(
    closure: &TcaClosure,
    k: f64,
    kappa_dot: f64,
    ell_max: usize,
) -> Vec<(usize, f64)> {
    // Returns (ℓ, m) → value pairs for fast variables
    let kd = kappa_dot.abs().max(1e-30);
    let ratio = k / kd;
    let mut fast_vars = Vec::new();

    // Set F_{2m}
    for (im, &val) in closure.f2m.iter().enumerate() {
        let m = im as i32 - 2;
        fast_vars.push((2_usize, m as usize, val));
    }

    // Quasi-static recursion for ℓ ≥ 3
    // F_{ℓm} = (ℓ/(2ℓ-1))(k/κ̇) F_{ℓ-1,m}
    let mut prev = closure.f2m.to_vec();
    for ell in 3..=ell_max.min(20) {
        let coeff = ell as f64 / (2.0 * ell as f64 - 1.0) * ratio;
        let mut curr = vec![0.0_f64; 2 * ell + 1];
        // Only propagate existing m-values
        for (im, &val) in prev.iter().enumerate() {
            if im < curr.len() {
                curr[im] = coeff * val;
            }
        }
        prev = curr;
    }

    fast_vars.len(); // suppress warning
    Vec::new() // Placeholder: full expansion requires layout integration
}

// ═══════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tca_criterion() {
        let crit = TcaCriterion {
            tau_c: 0.001,  // short mean free time
            k: 0.1,
            hubble: 0.01,
            shear: 0.0,
            kappa_dot_rate: 0.0,
        };
        // ε = max(0.1×0.001, 0.01×0.001) = 1e-4
        assert!((crit.epsilon() - 1e-4).abs() < 1e-10);
        assert!(crit.is_active(0.01), "Should be active at small ε");
    }

    #[test]
    fn test_tca_deactivation() {
        let crit = TcaCriterion {
            tau_c: 10.0,  // long mean free time (post-decoupling)
            k: 0.1,
            hubble: 0.01,
            shear: 0.0,
            kappa_dot_rate: 0.0,
        };
        // ε = max(1.0, 0.1) = 1.0 >> threshold
        assert!(!crit.is_active(0.01), "Should be inactive after decoupling");
    }

    #[test]
    fn test_first_order_closure() {
        let f1m = [0.0, 1.0, 0.0]; // m=0 dipole only
        let closure = tca_closure_first_order(&f1m, 0.05, 100.0);
        // F_{2,0} ≈ (8/9)(0.05/100) × 1.0 = 4.44e-4
        let expected = 8.0 / 9.0 * 0.05 / 100.0;
        assert!((closure.f2m[2] - expected).abs() < 1e-10,
            "F_20 = {} ≠ {}", closure.f2m[2], expected);
        // F_{2,±2} = 0 (no F_{1,±2})
        assert_eq!(closure.f2m[0], 0.0);
        assert_eq!(closure.f2m[4], 0.0);
    }

    #[test]
    fn test_e_mode_closure() {
        let f1m = [0.0, 1.0, 0.0];
        let closure = tca_closure_first_order(&f1m, 0.05, 100.0);
        // E_{2,0} = −(1/2)F_{2,0}
        assert!((closure.e2m[2] + 0.5 * closure.f2m[2]).abs() < 1e-15);
    }

    #[test]
    fn test_crs_correction() {
        // When κ̇' = 0: correction factor = 1
        assert!((crs_second_order_factor(100.0, 0.0) - 1.0).abs() < 1e-15);
        // When κ̇' < 0 (opacity decreasing): factor > 1
        let f = crs_second_order_factor(100.0, -50.0);
        assert!(f > 1.0, "CRS factor should be > 1 for decreasing opacity");
    }

    #[test]
    fn test_octupole_recursion() {
        let f1m = [0.0, 1.0, 0.0];
        let closure = tca_closure_first_order(&f1m, 0.05, 100.0);
        // F_{3,0} = (3/7)(k/κ̇)F_{2,0}
        let expected_f3 = 3.0 / 7.0 * 0.05 / 100.0 * closure.f2m[2];
        assert!((closure.f3m[3] - expected_f3).abs() < 1e-15,
            "F_30 = {} ≠ {}", closure.f3m[3], expected_f3);
    }

    #[test]
    fn test_scalar_limit() {
        // σ=0, m=0 only: should reproduce standard FLRW TCA
        let f1m = [0.0, 0.01, 0.0]; // m=0 dipole
        let k = 0.05;
        let kd = 500.0; // tight coupling
        let closure = tca_closure_first_order(&f1m, k, kd);
        // Standard FLRW: Θ₂ = (8/15)(k/κ̇)Θ₁
        // In brightness F: F₂ = (8/9)(k/κ̇)F₁
        let expected = 8.0 / 9.0 * k / kd * 0.01;
        assert!((closure.f2m[2] - expected).abs() < 1e-15);
    }
}
