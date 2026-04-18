// BE-07: Direction-Dependent Silk Damping from Anisotropic Recombination.
//
// First-ever numerical prediction of direction-dependent C_ℓ from Bianchi shear.
// Gap #7: no existing code computes σ_{ab} → K(ê) → P_esc(ê) → k_D(ê) → C_ℓ(ê) → BiPoSH.
//
// C_ℓ(ê) = C_ℓ^{iso} × exp(−2(ℓ/ℓ_D)² × δk_D(ê)/k_D)
// ≈ C_ℓ^{iso} × (1 − α_D(ℓ) × σ_{ab}ê^aê^b / H)  for small σ/H.

use crate::recombination::aniso_sobolev::{ShearTensor, diffusion_scale_modulation};
use crate::recombination::rt_response::RTResponse;
use crate::recombination::hyrec_tables::HyRecTables;

/// Silk damping scale (approximate).
pub(crate) const ELL_D_FIDUCIAL: f64 = 1450.0; // Planck 2018

/// Direction-modulated C_ℓ.
///
/// C_ℓ(ê) = C_ℓ^{iso} × exp(−2(ℓ/ℓ_D)² × δk_D(ê)/k_D)
pub(crate) fn modulated_cl(
    cl_iso: f64,
    ell: usize,
    ell_d: f64,
    delta_kd_over_kd: f64, // direction-dependent δk_D(ê)/k_D
) -> f64 {
    let exponent = -2.0 * (ell as f64 / ell_d).powi(2) * delta_kd_over_kd;
    cl_iso * exponent.exp()
}

/// α_D master coefficient (P-V.P3): fractional C_ℓ modulation per unit σ_{ab}ê^aê^b/H.
///
/// ΔC_ℓ/C_ℓ = α_D(ℓ) × σ_{ab}ê^aê^b/H
/// α_D(ℓ) = 2(ℓ/ℓ_D)² × (δk_D/k_D per unit σ/H)
pub(crate) fn alpha_d(ell: usize, ell_d: f64) -> f64 {
    let f_kd = 0.25; // δk_D/k_D = f_kd × σ/H (from BE-05e chain)
    2.0 * (ell as f64 / ell_d).powi(2) * f_kd
}

/// α_D with RT correction factor (from BE-05e').
pub(crate) fn alpha_d_rt(ell: usize, ell_d: f64, rt_factor: f64) -> f64 {
    alpha_d(ell, ell_d) * rt_factor
}

/// Quadrupolar C_ℓ modulation: δC_ℓ^{(2m)} for m = −2..+2.
///
/// For diagonal shear σ = diag(σ₁, σ₂, −σ₁−σ₂):
///   σ_{ab}ê^aê^b = σ₁ sin²θ cos²φ + σ₂ sin²θ sin²φ + σ₃ cos²θ
///
/// The ℓ=2 spherical harmonic decomposition gives 5 coefficients.
pub(crate) fn delta_cl_quadrupolar(
    cl_iso: f64,
    ell: usize,
    ell_d: f64,
    sigma: &ShearTensor,
    h: f64,
) -> [f64; 5] {
    let ad = alpha_d(ell, ell_d);
    // σ_{2m}/H components from the STF decomposition of σ_{ab}
    // For diagonal: σ_{20} ∝ (2σ₃ − σ₁ − σ₂)/√6 = −3σ₃/√6
    //               σ_{22} ∝ (σ₁ − σ₂)/2 (real part)
    let s = &sigma.s;
    let sigma2_over_h = [
        (s[0] - s[1]) / (2.0 * h),        // Re(σ_{22})
        s[4] / h,                            // Re(σ_{21}) (from σ_{13})
        (2.0 * s[2] - s[0] - s[1]) / (6.0_f64.sqrt() * h), // σ_{20}
        -s[5] / h,                           // Im(σ_{21}) (from σ_{23})
        -s[3] / h,                           // Im(σ_{22}) (from σ_{12})
    ];

    let mut dcl = [0.0; 5];
    for m in 0..5 {
        dcl[m] = cl_iso * ad * sigma2_over_h[m];
    }
    dcl
}

/// Compute α_D for a grid of ℓ values and shear amplitudes.
pub(crate) fn alpha_d_grid(
    ell_values: &[usize],
    ell_d: f64,
    sigma2_values: &[f64],
) -> Vec<Vec<f64>> {
    let mut result = Vec::with_capacity(sigma2_values.len());
    for &s2 in sigma2_values {
        let soh = (6.0 * s2).sqrt(); // σ/H from Σ²
        let row: Vec<f64> = ell_values.iter()
            .map(|&ell| alpha_d(ell, ell_d) * soh)
            .collect();
        result.push(row);
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_flrw_no_modulation() {
        let cl = modulated_cl(1000.0, 100, ELL_D_FIDUCIAL, 0.0);
        assert!((cl - 1000.0).abs() < 1e-10, "FLRW: C_ℓ unchanged");
    }

    #[test]
    fn test_positive_shear_less_damping() {
        // Positive δk_D/k_D → more damping → less power
        let cl_more = modulated_cl(1000.0, 2000, ELL_D_FIDUCIAL, 1e-3);
        let cl_less = modulated_cl(1000.0, 2000, ELL_D_FIDUCIAL, -1e-3);
        assert!(cl_more < 1000.0, "More damping → less power");
        assert!(cl_less > 1000.0, "Less damping → more power");
    }

    #[test]
    fn test_alpha_d_ell_squared() {
        let a1 = alpha_d(1000, ELL_D_FIDUCIAL);
        let a2 = alpha_d(2000, ELL_D_FIDUCIAL);
        assert!((a2 / a1 - 4.0).abs() < 0.01, "α_D ∝ ℓ²");
    }

    #[test]
    fn test_alpha_d_at_ell_d() {
        let a = alpha_d(ELL_D_FIDUCIAL as usize, ELL_D_FIDUCIAL);
        // α_D(ℓ_D) = 2 × 1² × 0.25 = 0.5
        assert!((a - 0.5).abs() < 0.01, "α_D(ℓ_D) = {:.4}", a);
    }

    #[test]
    fn test_quadrupolar_flrw_zero() {
        let sigma = ShearTensor::zero();
        let dcl = delta_cl_quadrupolar(1000.0, 2000, ELL_D_FIDUCIAL, &sigma, 1.0);
        for m in 0..5 { assert_eq!(dcl[m], 0.0); }
    }

    #[test]
    fn test_quadrupolar_nonzero() {
        let sigma = ShearTensor::diagonal(1e-4, -3e-5);
        let dcl = delta_cl_quadrupolar(1000.0, 2000, ELL_D_FIDUCIAL, &sigma, 1.0);
        let total: f64 = dcl.iter().map(|d| d * d).sum::<f64>().sqrt();
        assert!(total > 0.0, "Must have quadrupolar signal");
    }

    #[test]
    fn test_alpha_d_grid_scaling() {
        let ells = vec![1000, 2000, 3000];
        let s2s = vec![1e-8, 1e-6];
        let grid = alpha_d_grid(&ells, ELL_D_FIDUCIAL, &s2s);
        // σ/H scales as √Σ², so ratio should be 10
        let ratio = grid[1][0] / grid[0][0];
        assert!((ratio - 10.0).abs() < 0.1, "Σ² scaling: {:.1}", ratio);
    }
}
