// BE-09: Anisotropic Spectral Distortion from Direction-Dependent Silk Damping.
//
// Silk damping dissipates acoustic energy → μ-type (z > 5×10⁴) and y-type distortion.
// Direction-dependent k_D(ê) from BE-05e → anisotropic μ(ê), y(ê).
//
// μ(ê) = μ_iso × (1 + f_μ × α_D × σ_{ab}ê^aê^b / H)
//
// This is an L=2 quadrupolar anisotropic spectral distortion.
// Independent of BiPoSH (power spectrum modulation) — different measurement channel.
// Same σ_{2m} direction → cross-check with BE-07 BiPoSH.

use std::f64::consts::PI;
use super::direction_silk::{alpha_d, ELL_D_FIDUCIAL};

/// Spectral distortion result.
#[derive(Clone, Debug)]
pub(crate) struct SpectralDistortion {
    /// Isotropic μ-distortion (dimensionless).
    pub(crate) mu_iso: f64,
    /// Isotropic y-distortion (Compton-y).
    pub(crate) y_iso: f64,
    /// Quadrupolar μ_{2m} (5 components, m = -2..+2).
    pub(crate) mu_quad: [f64; 5],
    /// Quadrupolar y_{2m}.
    pub(crate) y_quad: [f64; 5],
    /// RMS fractional μ-anisotropy |δμ/μ|_rms.
    pub(crate) delta_mu_rms: f64,
}

/// Compute isotropic μ and y from primordial power spectrum + Silk damping.
///
/// μ_iso ≈ 1.4 × ∫ d(k_D⁻²) Δ²_R(k_D) dz  over μ-era (z > 5×10⁴)
/// y_iso ≈ (1/4) × ∫ d(k_D⁻²) Δ²_R(k_D) dz  over y-era (z < 5×10⁴)
///
/// For standard Planck 2018: μ ≈ 2.3 × 10⁻⁸, y ≈ 1.5 × 10⁻⁶.
pub(crate) fn compute_isotropic(a_s: f64, n_s: f64, _k_pivot: f64) -> (f64, f64) {
    // Calibrated to standard Planck 2018 values (Chluba et al. 2012, 2016):
    // μ ≈ 2.3 × 10⁻⁸ × (A_s / 2.1e-9) × ns_correction
    // y ≈ 1.5 × 10⁻⁶ × (A_s / 2.1e-9) × ns_correction
    let a_s_fid = 2.1e-9;
    let ratio = a_s / a_s_fid;

    // n_s correction: slightly red spectrum enhances dissipation at small scales
    let ns_corr = 1.0 + 2.0 * (n_s - 0.9649); // linear approximation

    let mu = 2.3e-8 * ratio * ns_corr;
    let y = 1.5e-6 * ratio * ns_corr;

    (mu, y)
}

/// n_s correction for μ-distortion.
/// μ ∝ A_s × (k_D/k_pivot)^{n_s-1} integrated over μ-era k_D range.
fn ns_correction_mu(n_s: f64) -> f64 {
    // k_D range for μ-era: ~50 to ~10⁴ Mpc⁻¹
    // <(k/k_piv)^{n_s-1}> ~ (k_D_eff/k_piv)^{n_s-1}
    // k_D_eff ~ 500 Mpc⁻¹, k_piv = 0.05 → ratio ~ 10⁴
    let k_ratio: f64 = 1e4;
    k_ratio.powf(n_s - 1.0)
}

/// n_s correction for y-distortion.
fn ns_correction_y(n_s: f64) -> f64 {
    // k_D range for y-era: ~1 to ~50 Mpc⁻¹
    let k_ratio: f64 = 100.0;
    k_ratio.powf(n_s - 1.0)
}

/// Compute anisotropic spectral distortion from direction-dependent k_D.
///
/// μ(ê) = μ_iso × (1 + f_μ × α_D × σ_{ab}ê^aê^b / H)
/// f_μ ≈ 2 (dissipation response: Q̇ ∝ k_D² → δQ̇/Q̇ = 2 δk_D/k_D)
///
/// μ_{2m} = μ_iso × f_μ × ᾱ_D × σ_{2m} / H
/// where ᾱ_D is the μ-era weighted average of α_D.
pub(crate) fn compute_anisotropic(
    mu_iso: f64,
    y_iso: f64,
    sigma_2m: &[f64; 5],
    h: f64,
) -> SpectralDistortion {
    // f_μ = 2: dissipation rate Q̇ ∝ k_D² → δQ̇/Q̇ = 2 δk_D/k_D
    let f_mu = 2.0;
    // ᾱ_D at μ-era effective ℓ: k_D ~ 500 Mpc⁻¹, corresponding ℓ ~ 500-2000
    let alpha_d_eff_mu = alpha_d(1000, ELL_D_FIDUCIAL); // ~ 0.24

    // f_y = 2 (same dissipation mechanism, different epoch)
    let f_y = 2.0;
    let alpha_d_eff_y = alpha_d(500, ELL_D_FIDUCIAL); // ~ 0.06

    let mut mu_quad = [0.0; 5];
    let mut y_quad = [0.0; 5];
    for m in 0..5 {
        mu_quad[m] = mu_iso * f_mu * alpha_d_eff_mu * sigma_2m[m] / h.max(1e-30);
        y_quad[m] = y_iso * f_y * alpha_d_eff_y * sigma_2m[m] / h.max(1e-30);
    }

    // RMS: |δμ/μ| = f_μ × α_D × |σ/H|
    let sigma_power: f64 = sigma_2m.iter().map(|s| s * s).sum();
    let sigma_rms = sigma_power.sqrt() / h.max(1e-30);
    let delta_mu_rms = f_mu * alpha_d_eff_mu * sigma_rms;

    SpectralDistortion { mu_iso, y_iso, mu_quad, y_quad, delta_mu_rms }
}

/// y-parameter from Teff Θ⁴ angular cumulants (BG-02 cross-check).
///
/// Local y ∝ ⟨ϑ²⟩ (temperature variance → Comptonisation).
/// y_local = (1/4) × ⟨Θ⁴⟩ − ⟨Θ⟩⁴) / ⟨Θ⟩⁴ ≈ (1/4) × 6⟨ϑ²⟩ = (3/2)⟨ϑ²⟩
pub(crate) fn y_from_teff_cumulants(vartheta2: f64) -> f64 {
    1.5 * vartheta2
}

/// Cross-check: μ-quadrupole direction vs BiPoSH L=2 direction.
///
/// Both ∝ σ_{2m}/H → directions must match.
/// Returns cos(angle) between the two 5-vectors (should be ~1).
pub(crate) fn direction_alignment(mu_quad: &[f64; 5], biposh_a2m: &[f64; 5]) -> f64 {
    let dot: f64 = mu_quad.iter().zip(biposh_a2m.iter()).map(|(a, b)| a * b).sum();
    let norm_mu: f64 = mu_quad.iter().map(|x| x * x).sum::<f64>().sqrt();
    let norm_bp: f64 = biposh_a2m.iter().map(|x| x * x).sum::<f64>().sqrt();
    if norm_mu < 1e-30 || norm_bp < 1e-30 { return 1.0; } // both zero = aligned
    dot / (norm_mu * norm_bp)
}

// ═══ Forecast ═══

/// Spectral distortion experiment specifications.
#[derive(Clone, Debug)]
pub(crate) enum DistortionExperiment {
    /// PIXIE: δμ ~ 5 × 10⁻⁹ (1σ per pixel, ~400 pixels for ℓ=2)
    Pixie,
    /// Voyage 2050: δμ ~ 10⁻⁹
    Voyage2050,
    /// Hypothetical super-PIXIE: δμ ~ 10⁻¹⁰
    SuperPixie,
}

impl DistortionExperiment {
    /// μ-distortion sensitivity per pixel [dimensionless].
    pub(crate) fn delta_mu(&self) -> f64 {
        match self {
            Self::Pixie => 5e-9,
            Self::Voyage2050 => 1e-9,
            Self::SuperPixie => 1e-10,
        }
    }

    /// Number of effective pixels for ℓ=2 mode (f_sky × (2ℓ+1)).
    pub(crate) fn n_eff_l2(&self) -> f64 {
        match self {
            Self::Pixie => 0.7 * 5.0,       // f_sky=0.7, 2×2+1=5
            Self::Voyage2050 => 0.8 * 5.0,
            Self::SuperPixie => 0.9 * 5.0,
        }
    }

    pub(crate) fn name(&self) -> &'static str {
        match self {
            Self::Pixie => "PIXIE",
            Self::Voyage2050 => "Voyage 2050",
            Self::SuperPixie => "SuperPIXIE",
        }
    }
}

/// S/N for μ-quadrupole detection.
///
/// (S/N)² = Σ_m |μ_{2m}|² / σ²_μ
/// σ²_μ = (δμ)² / N_eff
pub(crate) fn mu_quadrupole_sn(mu_quad: &[f64; 5], experiment: &DistortionExperiment) -> f64 {
    let sigma2 = experiment.delta_mu().powi(2) / experiment.n_eff_l2();
    let signal2: f64 = mu_quad.iter().map(|m| m * m).sum();
    (signal2 / sigma2).sqrt()
}

/// Minimum detectable Σ² from μ-anisotropy (S/N = 1).
pub(crate) fn sigma2_min_from_mu(
    mu_iso: f64,
    experiment: &DistortionExperiment,
) -> f64 {
    // μ_{2m} = μ_iso × f_μ × α_D × σ_{2m}/H
    // |μ_{2m}| ~ μ_iso × 2 × α_D(1000) × σ/H
    // σ/H = √(6Σ²)
    // S/N = |μ_quad| / (δμ/√N_eff) = 1
    let f_mu = 2.0;
    let ad = alpha_d(1000, ELL_D_FIDUCIAL);
    let sigma_mu = experiment.delta_mu() / experiment.n_eff_l2().sqrt();

    // |μ_{2m}| ~ μ_iso × f_μ × α_D × √(6Σ²) / √5 (per component)
    // S/N = √5 × |μ_{2m}| / σ_μ = √5 × μ_iso × f_μ × α_D × √(6Σ²) / (√5 σ_μ)
    // S/N = μ_iso × f_μ × α_D × √(6Σ²) / σ_μ = 1
    // → Σ² = σ_μ² / (6 × (μ_iso × f_μ × α_D)²)
    let denominator = mu_iso * f_mu * ad;
    if denominator.abs() < 1e-30 { return f64::INFINITY; }
    sigma_mu.powi(2) / (6.0 * denominator.powi(2))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_isotropic_mu_order() {
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        // μ ~ 2 × 10⁻⁸ (standard literature value)
        assert!(mu > 1e-9 && mu < 1e-6,
            "μ_iso = {:.4e} (expect ~2e-8)", mu);
    }

    #[test]
    fn test_isotropic_y_order() {
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        assert!(y > 1e-8 && y < 1e-4,
            "y_iso = {:.4e} (expect ~1.5e-6)", y);
    }

    #[test]
    fn test_flrw_no_anisotropy() {
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let sd = compute_anisotropic(mu, y, &[0.0; 5], 1.0);
        for m in 0..5 { assert_eq!(sd.mu_quad[m], 0.0); }
        for m in 0..5 { assert_eq!(sd.y_quad[m], 0.0); }
        assert_eq!(sd.delta_mu_rms, 0.0);
    }

    #[test]
    fn test_mu_quad_proportional_to_sigma() {
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let s1 = [1e-4, 0.0, 5e-5, 0.0, 0.0];
        let s2 = [2e-4, 0.0, 1e-4, 0.0, 0.0]; // doubled
        let sd1 = compute_anisotropic(mu, y, &s1, 1.0);
        let sd2 = compute_anisotropic(mu, y, &s2, 1.0);
        let ratio = sd2.mu_quad[0] / sd1.mu_quad[0];
        assert!((ratio - 2.0).abs() < 0.01, "mu_2m prop sigma: ratio = {:.4}", ratio);
    }

    #[test]
    fn test_delta_mu_order_bi() {
        // BI at Σ² = 10⁻⁶: σ/H ~ 10⁻³
        // δμ/μ ~ 2 × α_D(1000) × σ/H ~ 2 × 0.24 × 10⁻³ ~ 5 × 10⁻⁴
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let soh = 1e-3;
        let sd = compute_anisotropic(mu, y, &[soh, 0.0, 0.0, 0.0, 0.0], 1.0);
        assert!(sd.delta_mu_rms > 1e-5 && sd.delta_mu_rms < 1e-2,
            "δμ/μ = {:.4e} (expect ~5e-4)", sd.delta_mu_rms);
    }

    #[test]
    fn test_y_from_teff() {
        let vt2 = 1e-6;
        let y = y_from_teff_cumulants(vt2);
        assert!((y - 1.5e-6).abs() < 1e-10, "y_local = {:.4e}", y);
    }

    #[test]
    fn test_direction_alignment_perfect() {
        let a = [1.0, 0.0, 0.5, 0.0, 0.0];
        let b = [2.0, 0.0, 1.0, 0.0, 0.0]; // parallel
        let cos = direction_alignment(&a, &b);
        assert!((cos - 1.0).abs() < 1e-10, "Parallel: cos = {:.6}", cos);
    }

    #[test]
    fn test_direction_alignment_mu_vs_biposh() {
        // Both ∝ σ_{2m}/H → same direction → cos = 1
        let sigma_2m = [1e-4, -5e-5, 3e-5, 0.0, 2e-5];
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let sd = compute_anisotropic(mu, y, &sigma_2m, 1.0);
        // BiPoSH A^{2M} ∝ σ_{2m} (from BE-07)
        let cos = direction_alignment(&sd.mu_quad, &sigma_2m);
        assert!((cos - 1.0).abs() < 1e-6,
            "μ-quad vs σ alignment: cos = {:.8}", cos);
    }

    #[test]
    fn test_sn_pixie() {
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let soh = 1e-3; // σ/H ~ 10⁻³
        let sd = compute_anisotropic(mu, y, &[soh, 0.0, 0.0, 0.0, 0.0], 1.0);
        let sn = mu_quadrupole_sn(&sd.mu_quad, &DistortionExperiment::Pixie);
        assert!(sn >= 0.0 && sn.is_finite(), "PIXIE S/N = {:.4e}", sn);
    }

    #[test]
    fn test_voyage_better_than_pixie() {
        let (mu, y) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let sd = compute_anisotropic(mu, y, &[1e-3, 0.0, 0.0, 0.0, 0.0], 1.0);
        let sn_p = mu_quadrupole_sn(&sd.mu_quad, &DistortionExperiment::Pixie);
        let sn_v = mu_quadrupole_sn(&sd.mu_quad, &DistortionExperiment::Voyage2050);
        assert!(sn_v > sn_p, "Voyage ({:.2e}) must beat PIXIE ({:.2e})", sn_v, sn_p);
    }

    #[test]
    fn test_sigma2_min_finite() {
        let (mu, _) = compute_isotropic(2.1e-9, 0.9649, 0.05);
        let s2_min = sigma2_min_from_mu(mu, &DistortionExperiment::Voyage2050);
        assert!(s2_min > 0.0 && s2_min < 1.0 && s2_min.is_finite(),
            "Min Σ² (Voyage) = {:.4e}", s2_min);
    }
}
