// BE-07: Fisher forecast for Σ² constraint from direction-dependent Silk damping.
//
// σ(Σ²) from BiPoSH L=2 at high-ℓ, complementary to low-ℓ quadrupole constraint.

use super::direction_silk::{alpha_d, ELL_D_FIDUCIAL};
use super::biposh::{ExperimentSpec, noise_power, biposh_variance};

/// Fisher information for Σ² from BiPoSH L=2.
///
/// F(Σ²) = Σ_ℓ (∂A^{20}/∂Σ²)² / Var(A^{20})
///
/// ∂A^{20}/∂Σ² = C_ℓ × α_D(ℓ) × ∂(σ_{20}/H)/∂Σ²
/// For diagonal BI: σ_{20}/H ∝ √Σ², so ∂(σ_{20}/H)/∂Σ² ∝ 1/(2√Σ²)
pub(crate) fn fisher_sigma2(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2_fid: f64,     // fiducial Σ² for Fisher evaluation
    spec: &ExperimentSpec,
) -> f64 {
    let soh = (6.0 * sigma2_fid).sqrt();
    let dsoh_dsigma2 = if sigma2_fid > 1e-20 { 3.0 / soh } else { 1e10 };

    let mut fisher = 0.0;
    for ell in spec.ell_min..=spec.ell_max.min(cl_iso.len() - 1) {
        let ad = alpha_d(ell, ell_d);
        let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
        let var = biposh_variance(cl_iso[ell], nl, ell);
        if var < 1e-60 { continue; }

        // ∂A^{20}/∂Σ² = C_ℓ × α_D × (∂σ_{20}/∂Σ²) / H
        // For simplicity: σ_{20}/H ~ soh/√5, so ∂(σ_{20}/H)/∂Σ² ~ dsoh_dsigma2/√5
        let da_dsigma2 = cl_iso[ell] * ad * dsoh_dsigma2 / 5.0_f64.sqrt();

        // Sum over 5 M-values (factor 5)
        fisher += spec.f_sky * 5.0 * da_dsigma2 * da_dsigma2 / var;
    }
    fisher
}

/// 1σ constraint on Σ² from Fisher forecast.
pub(crate) fn sigma_sigma2(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2_fid: f64,
    spec: &ExperimentSpec,
) -> f64 {
    let f = fisher_sigma2(cl_iso, ell_d, sigma2_fid, spec);
    if f > 0.0 { 1.0 / f.sqrt() } else { f64::INFINITY }
}

/// Minimum detectable Σ² (S/N = 1 threshold).
///
/// Iteratively finds Σ² where S/N(Σ²) = 1.
pub(crate) fn min_detectable_sigma2(
    cl_iso: &[f64],
    ell_d: f64,
    spec: &ExperimentSpec,
) -> f64 {
    // Binary search: S/N = σ_{20}/σ(σ_{20})
    // Start from large Σ² and decrease
    let mut s2_hi: f64 = 1e-3;
    let mut s2_lo: f64 = 1e-12;

    for _ in 0..60 {
        let s2_mid = (s2_hi * s2_lo).sqrt(); // geometric mean
        let sigma = sigma_sigma2(cl_iso, ell_d, s2_mid, spec);
        if sigma < s2_mid { s2_hi = s2_mid; } else { s2_lo = s2_mid; }
    }
    (s2_hi * s2_lo).sqrt()
}

/// Comparison: low-ℓ (VER06) vs high-ℓ (BiPoSH) constraint.
#[derive(Clone, Debug)]
pub(crate) struct ConstraintComparison {
    pub(crate) experiment: &'static str,
    pub(crate) sigma_sigma2_low_ell: f64,   // from VER06 ℓ ≤ 30
    pub(crate) sigma_sigma2_high_ell: f64,  // from BiPoSH ℓ = ℓ_min..ℓ_max
    pub(crate) improvement_factor: f64,      // low/high (>1 means high-ℓ better)
}

pub(crate) fn compare_constraints(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2_fid: f64,
    spec: &ExperimentSpec,
) -> ConstraintComparison {
    let sigma_high = sigma_sigma2(cl_iso, ell_d, sigma2_fid, spec);
    // VER06 low-ℓ constraint: σ(Σ²) ~ 3×10⁻⁶ from ℓ ≤ 30 (production value)
    let sigma_low = 3e-6;
    ConstraintComparison {
        experiment: spec.name,
        sigma_sigma2_low_ell: sigma_low,
        sigma_sigma2_high_ell: sigma_high,
        improvement_factor: sigma_low / sigma_high,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_cl(n: usize) -> Vec<f64> {
        (0..n).map(|ell| {
            if ell < 2 { return 0.0; }
            let dl = 5000.0 * (-(ell as f64 - 220.0).powi(2) / 20000.0).exp()
                   + 1000.0 * (-(ell as f64 / 1500.0).powi(2)).exp();
            dl * 2.0 * std::f64::consts::PI / (ell * (ell + 1)) as f64 * 1e-12
        }).collect()
    }

    #[test]
    fn test_fisher_positive() {
        let cl = mock_cl(3000);
        let f = fisher_sigma2(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::planck());
        assert!(f > 0.0 && f.is_finite(), "Fisher = {:.4e}", f);
    }

    #[test]
    fn test_sigma_finite() {
        let cl = mock_cl(5000);
        let s = sigma_sigma2(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::act_dr6());
        assert!(s > 0.0 && s.is_finite(), "σ(Σ²) = {:.4e}", s);
    }

    #[test]
    fn test_cmbs4_better_than_planck() {
        let cl = mock_cl(5000);
        let s_planck = sigma_sigma2(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::planck());
        let s_s4 = sigma_sigma2(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::cmb_s4());
        assert!(s_s4 < s_planck, "CMB-S4 ({:.2e}) must beat Planck ({:.2e})", s_s4, s_planck);
    }

    #[test]
    fn test_min_detectable() {
        let cl = mock_cl(5000);
        let s2_min = min_detectable_sigma2(&cl, ELL_D_FIDUCIAL, &ExperimentSpec::cmb_s4());
        assert!(s2_min > 1e-12 && s2_min < 1e-3,
            "Min Σ² (CMB-S4) = {:.4e}", s2_min);
    }

    #[test]
    fn test_compare_constraints() {
        let cl = mock_cl(5000);
        let comp = compare_constraints(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::cmb_s4());
        assert!(comp.sigma_sigma2_high_ell > 0.0);
        eprintln!("Constraint comparison (CMB-S4): low-ℓ σ={:.2e}, high-ℓ σ={:.2e}, factor={:.2}",
            comp.sigma_sigma2_low_ell, comp.sigma_sigma2_high_ell, comp.improvement_factor);
    }
}
