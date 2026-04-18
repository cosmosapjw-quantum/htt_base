// D₂ / Σ² / σ/H NORMALIZATION CONVENTION LEDGER
// ═══════════════════════════════════════════════════
// Last verified: CL-08 audit (2026-04-04)
// SINGLE SOURCE OF TRUTH for all bass_rs modules.
//
// ┌──────────────────┬────────────────────────────────────────────────┐
// │ Symbol           │ Definition                                     │
// ├──────────────────┼────────────────────────────────────────────────┤
// │ Σ²               │ σ_{ab}σ^{ab} / (6H²)        [dimensionless]  │
// │                  │ where σ_{ab} = full shear tensor,             │
// │                  │ σ^{ab}σ_{ab} = 2σ² (twice the half-contrac.) │
// │                  │ H = Θ/3 (Hubble).                             │
// ├──────────────────┼────────────────────────────────────────────────┤
// │ σ̄/Θ             │ √(2Σ²/3)   [dimensionless]                   │
// │                  │ σ̄ = √(σ_{ab}σ^{ab}), Θ = 3H.                │
// │                  │ Equivalently: (σ̄/Θ)² = 2Σ²/3.               │
// │                  │ NOTE: σ̄/Θ ≠ σ/H. σ/H = √(3Σ²).             │
// ├──────────────────┼────────────────────────────────────────────────┤
// │ D₂               │ ℓ(ℓ+1)C₂^TT / (2π)  [μK²]                  │
// │                  │ The standard CMB angular power spectrum.       │
// │                  │ ALWAYS in μK². NEVER dimensionless.           │
// ├──────────────────┼────────────────────────────────────────────────┤
// │ T₂               │ Transfer function [μK per unit (σ̄/Θ)]        │
// │                  │ D₂ = (6/2π) × (T₂ × σ̄/Θ)²                  │
// │                  │ T₂_TOTAL_DECAY = 5247.5 (AniCLASS-calibrated)│
// ├──────────────────┼────────────────────────────────────────────────┤
// │ C₁, C₂           │ Route B parametric transfer:                  │
// │                  │   D₂[μK²] = C₁ Σ² / (1 + C₂ Σ²)            │
// │                  │   C₁ = 1.753×10⁷ [μK²]                      │
// │                  │   C₂ = 6.825×10⁵ [dimensionless]             │
// │                  │ Derivation: C₁ = (2/π)T₂² = (2/π)×5247.5²   │
// │                  │           = 1.7530×10⁷. ✓                     │
// ├──────────────────┼────────────────────────────────────────────────┤
// │ F₂, N₂           │ PSTF hierarchy multipoles [dimensionless]     │
// │                  │ F₂ = (2ℓ+1)Θ₂ = 5Θ₂ (bass_rs convention)    │
// │                  │ N₂ = 5N₂^{phys} (neutrino quadrupole)        │
// │                  │ NOT directly observable. Requires LoS + T₀².  │
// └──────────────────┴────────────────────────────────────────────────┘
//
// MAPPING: raw solver → observable D₂
// ────────────────────────────────────
// The Phase 1.0 solver outputs a dimensionless coherent sum
//   |I_γ + f_ν I_ν + I_ISW|²
// in internal (ΔT/T₀) units. This is NOT D₂ in μK².
//
// The Route B transfer function maps Σ² → D₂[μK²] directly,
// absorbing T₀², the LoS integration, and all cascade effects
// into the calibrated C₁ coefficient.
//
// ACCEPTED VALUES AT Σ² = 10⁻⁸:
// ───────────────────────────────
//   D₂ = C₁ × 10⁻⁸ / (1 + C₂ × 10⁻⁸) = 0.1741 μK²
//
// The historical value "6.822×10⁻⁸ μK²" is the Phase 1.0 solver
// raw output in INTERNAL UNITS. It is NOT D₂ in μK².
// Quoting 6.822e-8 as "μK²" is a UNIT ERROR.
//
// SATURATION:
//   D₂ → C₁/C₂ = 25.68 μK²  as Σ² → ∞
//
// LINEARITY CHECK:
//   D₂/Σ² = const for C₂Σ² ≪ 1, i.e. Σ² ≪ 1.5×10⁻⁶.
//   At Σ²=10⁻⁸: C₂Σ² = 6.825e-3 ≪ 1 → linear regime. ✓

/// The ACCEPTED D₂ at the reference point Σ² = 10⁻⁸.
/// D₂ = C₁ × 10⁻⁸ / (1 + C₂ × 10⁻⁸) = 0.17411 μK².
pub(crate) const D2_REFERENCE_UK2: f64 = 0.17411;

/// Reference Σ² for the register.
pub(crate) const SIGMA2_REFERENCE: f64 = 1e-8;

/// Route B C₁ [μK²]. Derivation: C₁ = (2/π) × T₂² where T₂ = 5247.5 μK/(σ̄/Θ).
pub(crate) const ROUTE_B_C1: f64 = 1.753e7;

/// Route B C₂ [dimensionless].
pub(crate) const ROUTE_B_C2: f64 = 6.825e5;

/// D₂ transfer function: Σ² → D₂ [μK²].
///
/// D₂ = C₁ Σ² / (1 + C₂ Σ²)
/// Returns D₂ in μK² (ALWAYS).
pub fn d2_from_sigma2(sigma2: f64) -> f64 {
    ROUTE_B_C1 * sigma2 / (1.0 + ROUTE_B_C2 * sigma2)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_d2_reference_value() {
        let d2 = d2_from_sigma2(SIGMA2_REFERENCE);
        let rel = (d2 - D2_REFERENCE_UK2).abs() / D2_REFERENCE_UK2;
        assert!(rel < 1e-3,
            "D₂(10⁻⁸) = {:.6} μK² (expect {:.5}), rel = {:.4e}", d2, D2_REFERENCE_UK2, rel);
    }

    #[test]
    fn test_d2_units_are_uK2() {
        // At Σ²=10⁻⁸, D₂ must be O(0.1) μK², NOT O(10⁻⁸)
        let d2 = d2_from_sigma2(1e-8);
        assert!(d2 > 0.1 && d2 < 0.3,
            "D₂(10⁻⁸) = {:.6e}: must be ~0.17 μK², not ~10⁻⁸", d2);
    }

    #[test]
    fn test_d2_is_not_6e_minus_8() {
        // REGRESSION: The historical value 6.822e-8 is an internal solver
        // diagnostic in dimensionless units. It is NOT D₂ in μK².
        // This test FAILS if anyone re-introduces the old number.
        let d2 = d2_from_sigma2(1e-8);
        assert!((d2 - 6.822e-8).abs() / d2 > 0.99,
            "D₂ must NOT be ~6.822e-8 (that's internal units, not μK²)");
    }

    #[test]
    fn test_d2_saturation() {
        let d2 = d2_from_sigma2(1.0);
        let sat = ROUTE_B_C1 / ROUTE_B_C2;
        assert!((d2 - sat).abs() / sat < 0.01);
    }

    #[test]
    fn test_d2_linear_regime() {
        // For Σ² ≪ 1/C₂ ≈ 1.5e-6: D₂ ∝ Σ² (ratio ~ 100 over 2 decades)
        let d2_a = d2_from_sigma2(1e-10);
        let d2_b = d2_from_sigma2(1e-8);
        let ratio = d2_b / d2_a;
        assert!(ratio > 99.0 && ratio < 101.0,
            "Linear regime: D₂ ratio = {:.2} (expect ~100)", ratio);
    }

    #[test]
    fn test_c1_derivation_from_t2() {
        // C₁ = (2/π) × T₂²
        let t2 = 5247.5_f64; // μK per unit (σ̄/Θ)
        let c1 = (2.0 / std::f64::consts::PI) * t2 * t2;
        assert!((c1 - ROUTE_B_C1).abs() / ROUTE_B_C1 < 1e-4,
            "C₁ derivation: {:.4e} vs {:.4e}", c1, ROUTE_B_C1);
    }

    #[test]
    fn test_sigma_bar_over_theta() {
        // σ̄/Θ = √(2Σ²/3)
        let sigma2 = 1e-8;
        let s = (2.0 * sigma2 / 3.0_f64).sqrt();
        assert!((s - 8.165e-5).abs() / 8.165e-5 < 1e-3);
    }

    #[test]
    fn test_all_three_d2_functions_agree() {
        // Three copies of the transfer function exist:
        //   1. d2_convention::d2_from_sigma2 (SSOT)
        //   2. bass_rhs::d2_transfer
        //   3. pipeline::d2_transfer_function
        // All must give identical results.
        use crate::forward::bass_rhs::d2_transfer;
        use crate::solver::pipeline::d2_transfer_function;

        for &s2 in &[1e-12, 1e-10, 1e-8, 1e-6, 1e-4, 1e-2, 1.0] {
            let d_ssot = d2_from_sigma2(s2);
            let d_rhs  = d2_transfer(s2);
            let d_pipe = d2_transfer_function(s2);
            let tol = 1e-10 * d_ssot.max(1e-30);
            assert!((d_ssot - d_rhs).abs() < tol,
                "bass_rhs disagrees at Σ²={:.0e}: {:.6e} vs {:.6e}", s2, d_rhs, d_ssot);
            assert!((d_ssot - d_pipe).abs() < tol,
                "pipeline disagrees at Σ²={:.0e}: {:.6e} vs {:.6e}", s2, d_pipe, d_ssot);
        }
    }
}
