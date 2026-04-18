// BH-01: BASS → HTT Forward Interface — Main Solve Entry Point.
//
// bass_solve(params) → BassResult: full BASS pipeline output.
// Carries: C_ℓ (to ℓ~4000), a_{ℓm}, D₂, BiPoSH A^{2M}_{ℓℓ'}, diagnostics.

use crate::observable::direction_silk::{alpha_d, alpha_d_rt, ELL_D_FIDUCIAL};
use crate::observable::biposh::{predicted_biposh, BiPoSHSpectrum, ExperimentSpec};
use crate::recombination::aniso_sobolev::ShearTensor;

/// Full BASS output structure.
#[derive(Clone)]
pub(crate) struct BassResult {
    /// C_ℓ^{TT} unlensed (dimensionless, ℓ=0..ℓ_max).
    pub(crate) cl_tt_unlensed: Vec<f64>,
    /// C_ℓ^{TT} lensed.
    pub(crate) cl_tt_lensed: Vec<f64>,
    /// C_ℓ^{EE} unlensed.
    pub(crate) cl_ee_unlensed: Vec<f64>,
    /// C_ℓ^{φφ} lensing potential.
    pub(crate) cl_phiphi: Vec<f64>,
    /// D₂ departure power [μK²].
    pub(crate) d2: f64,
    /// BiPoSH A^{2M}_{ℓℓ} spectrum (from direction-dependent Silk).
    pub(crate) biposh: Option<BiPoSHSpectrum>,
    /// α_D(ℓ) master coefficient.
    pub(crate) alpha_d: Vec<f64>,
    /// β_L(ℓ) lensing anisotropy coefficient.
    pub(crate) beta_l: Vec<f64>,
    /// Diagnostics.
    pub(crate) diagnostics: BassDiagnostics,
}

/// Diagnostics bundle.
#[derive(Clone, Debug)]
pub(crate) struct BassDiagnostics {
    /// Solver convergence flag.
    pub(crate) converged: bool,
    /// Energy conservation error.
    pub(crate) energy_error: f64,
    /// Teff vs PSTF discrepancy (from BG-06).
    pub(crate) teff_pstf_discrepancy: f64,
    /// Recombination precision tier.
    pub(crate) recomb_tier: RecombTier,
    /// Wall time [ms].
    pub(crate) wall_ms: f64,
}

/// Recombination precision tier.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum RecombTier {
    Peebles,      // basic, ℓ < 1500 only
    HyRec2,       // full EMLA4, good to ℓ ~ 3000
    AnisoSobolev, // direction-dependent (BE-05e), good to ℓ ~ 4000
}

/// D₂ transfer function: maps Σ² → D₂ [μK²].
///
/// D₂ = C₁ Σ² / (1 + C₂ Σ²)  (Route B, VER06 production).
/// C₁ = 1.753×10⁷, C₂ = 6.825×10⁵.
pub(crate) fn d2_transfer(sigma2: f64) -> f64 {
    let c1 = 1.753e7;
    let c2 = 6.825e5;
    c1 * sigma2 / (1.0 + c2 * sigma2)
}

/// D₂ transfer on a grid.
pub(crate) fn d2_transfer_grid(sigma2_grid: &[f64]) -> Vec<(f64, f64)> {
    sigma2_grid.iter().map(|&s2| (s2, d2_transfer(s2))).collect()
}

/// Compute α_D(ℓ) grid for a given ℓ range.
pub(crate) fn alpha_d_grid(ell_max: usize, ell_d: f64) -> Vec<f64> {
    (0..=ell_max).map(|ell| if ell >= 2 { alpha_d(ell, ell_d) } else { 0.0 }).collect()
}

/// Per-type BiPoSH prediction.
pub(crate) fn biposh_for_type(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2: f64,
    _beta: f64,
    ell_min: usize,
    ell_max: usize,
) -> BiPoSHSpectrum {
    let sigma_over_h = (6.0 * sigma2).sqrt();
    let sigma20 = sigma_over_h / 5.0_f64.sqrt();
    predicted_biposh(cl_iso, ell_d, sigma20, ell_min, ell_max)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_d2_transfer_ver06() {
        // VER06: D₂(Σ²=10⁻⁸) = C₁×10⁻⁸/(1+C₂×10⁻⁸) ≈ 0.174 μK²
        // See d2_convention.rs for the normalization ledger.
        let d2 = d2_transfer(1e-8);
        assert!(d2 > 0.1 && d2 < 0.3, "D₂(10⁻⁸) = {:.4} μK²", d2);
    }

    #[test]
    fn test_d2_transfer_saturation() {
        // Large Σ²: D₂ saturates at C₁/C₂ ≈ 25.7
        let d2 = d2_transfer(1.0);
        let sat = 1.753e7 / 6.825e5;
        assert!((d2 - sat).abs() / sat < 0.01, "D₂(1) = {:.2}, sat = {:.2}", d2, sat);
    }

    #[test]
    fn test_d2_transfer_grid() {
        let grid = vec![1e-10, 1e-8, 1e-6, 1e-4];
        let result = d2_transfer_grid(&grid);
        assert_eq!(result.len(), 4);
        // Monotonically increasing
        for i in 1..result.len() {
            assert!(result[i].1 > result[i - 1].1);
        }
    }

    #[test]
    fn test_alpha_d_grid_structure() {
        let ad = alpha_d_grid(3000, ELL_D_FIDUCIAL);
        assert_eq!(ad.len(), 3001);
        assert_eq!(ad[0], 0.0);
        assert_eq!(ad[1], 0.0);
        assert!(ad[1000] > 0.0);
        assert!(ad[2000] > ad[1000]); // grows with ℓ
    }

    #[test]
    fn test_recomb_tiers() {
        assert_ne!(RecombTier::Peebles, RecombTier::HyRec2);
        assert_ne!(RecombTier::HyRec2, RecombTier::AnisoSobolev);
    }
}
