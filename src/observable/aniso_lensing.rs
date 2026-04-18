// BE-08: Anisotropic CMB Lensing from Bianchi Growth.
//
// Direction-dependent lensing potential from anisotropic matter growth.
// β_L(ℓ): lensing anisotropy coefficient (analogue of α_D from Silk damping).
//
// C_ℓ^{φφ}(ê) = C_ℓ^{φφ,iso} × (1 + β_L(ℓ) × σ_{ab}ê^aê^b/H)
//
// Combined BiPoSH = Silk (BE-07) + Lensing (this) + cross term.
// Two channels probe shear at different epochs:
//   Silk → z ~ 1100 (recombination)
//   Lensing → z ~ 0.5-5 (structure formation)

use std::f64::consts::PI;
use super::direction_silk::{alpha_d, ELL_D_FIDUCIAL};

/// Lensing anisotropy coefficient β_L(ℓ).
///
/// β_L(ℓ) = 2 ∫ dη W²(η) × (δD/D per unit σê²/H) / ∫ dη W²(η)
///
/// The growth modulation δD/D ~ 0.5 × σ_{ab}ê^aê^b/H (from growth.rs).
/// The lensing-weighted average of this modulation gives β_L.
///
/// β_L is approximately constant in ℓ (unlike α_D ∝ ℓ²) because lensing
/// is an integrated effect over the growth history.
pub(crate) fn beta_l(ell: usize) -> f64 {
    // β_L ≈ 2 × 0.5 × (lensing efficiency factor) ≈ 0.5-1.0
    // The factor 2 comes from C^{φφ} ∝ D² → δC^{φφ}/C^{φφ} = 2 δD/D.
    // The lensing efficiency factor accounts for the kernel-weighted average
    // of σ(η)/H(η) over the lensing kernel.
    //
    // For σ/H ∝ a⁻² (matter era): the lensing-weighted σ/H is dominated
    // by high-z part of the kernel where σ/H is largest.
    //
    // Mild ℓ-dependence from the k=ℓ/η Limber mapping changing the
    // effective redshift weight. Approximate as constant.
    let base = 0.7; // lensing-weighted growth modulation coefficient
    // Mild ℓ-dependence: slightly larger at low ℓ (deeper kernel)
    let ell_correction = 1.0 + 0.1 * (500.0 / ell.max(10) as f64).min(2.0);
    base * ell_correction
}

/// Direction-dependent C_ℓ^{φφ}(ê).
///
/// C_ℓ^{φφ}(ê) = C_ℓ^{φφ,iso} × (1 + β_L(ℓ) × σ_{ab}ê^aê^b/H)
pub(crate) fn phiphi_directional(
    cl_phiphi_iso: f64,
    ell: usize,
    sigma_ab_ee_over_h: f64,
) -> f64 {
    cl_phiphi_iso * (1.0 + beta_l(ell) * sigma_ab_ee_over_h)
}

/// Lensing contribution to BiPoSH L=2.
///
/// A^{2M,lens}_{ℓℓ} from direction-dependent φφ propagated to lensed C_ℓ.
///
/// The chain: δC^{φφ}(ê) → δC̃_ℓ(ê) via lensing convolution.
/// At leading order: δC̃_ℓ/C̃_ℓ ≈ β̃_L(ℓ) × σ_{ab}ê^aê^b/H
/// where β̃_L includes the lensing-to-Cl transfer.
///
/// β̃_L(ℓ) = β_L × ℓ(ℓ+1) R_φ / (1 − ℓ(ℓ+1)R_φ)  [very approximate]
/// More accurate: β̃_L ~ β_L × (lensed fraction at ℓ)
pub(crate) fn biposh_lensing(
    ell: usize,
    cl_lensed: f64,
    cl_phiphi_iso: f64,
    sigma_2m: &[f64; 5],
    h: f64,
    r_phi: f64,
) -> [f64; 5] {
    let bl = beta_l(ell);
    // Effective lensing transfer: how much of the lensed C_ℓ comes from lensing
    let ll1 = (ell * (ell + 1)) as f64;
    let lensing_fraction = (ll1 * r_phi).min(0.5); // capped at 50%

    let mut a_2m = [0.0; 5];
    for m in 0..5 {
        // A^{2M,lens} = C̃_ℓ × β̃_L × σ_{2M}/H
        a_2m[m] = cl_lensed * bl * lensing_fraction * sigma_2m[m] / h.max(1e-30);
    }
    a_2m
}

/// Combined BiPoSH decomposition: Silk + Lensing + Cross.
#[derive(Clone, Debug)]
pub(crate) struct CombinedBiPoSH {
    pub(crate) silk: [f64; 5],
    pub(crate) lensing: [f64; 5],
    pub(crate) cross: [f64; 5],
    pub(crate) total: [f64; 5],
}

/// Dominant physical channel at given ℓ.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum BiPoSHChannel {
    LensingDominated,  // ℓ < 800
    Mixed,             // 800 ≤ ℓ ≤ 1500
    SilkDominated,     // ℓ > 1500
}

impl CombinedBiPoSH {
    /// Decompose total BiPoSH into Silk + Lensing + Cross.
    pub(crate) fn decompose(
        ell: usize,
        cl_unlensed: f64,
        cl_lensed: f64,
        cl_phiphi_iso: f64,
        sigma_2m: &[f64; 5],
        h: f64,
        r_phi: f64,
    ) -> Self {
        // Silk BiPoSH (from BE-07): A^{2M,Silk} = C_ℓ × α_D × σ_{2M}/H
        let ad = alpha_d(ell, ELL_D_FIDUCIAL);
        let mut silk = [0.0; 5];
        for m in 0..5 { silk[m] = cl_unlensed * ad * sigma_2m[m] / h.max(1e-30); }

        // Lensing BiPoSH
        let lensing = biposh_lensing(ell, cl_lensed, cl_phiphi_iso, sigma_2m, h, r_phi);

        // Cross term (Silk × Lensing): subdominant, ~ product of small quantities
        let mut cross = [0.0; 5];
        for m in 0..5 { cross[m] = silk[m] * beta_l(ell) * 0.01; } // ~1% of Silk

        let mut total = [0.0; 5];
        for m in 0..5 { total[m] = silk[m] + lensing[m] + cross[m]; }

        Self { silk, lensing, cross, total }
    }

    /// Identify dominant channel.
    pub(crate) fn dominant_channel(ell: usize) -> BiPoSHChannel {
        if ell < 800 { BiPoSHChannel::LensingDominated }
        else if ell <= 1500 { BiPoSHChannel::Mixed }
        else { BiPoSHChannel::SilkDominated }
    }

    /// Check total = sum of components (consistency).
    pub(crate) fn consistency_error(&self) -> f64 {
        let mut err = 0.0_f64;
        for m in 0..5 {
            let sum = self.silk[m] + self.lensing[m] + self.cross[m];
            err = err.max((sum - self.total[m]).abs());
        }
        err
    }
}

/// Shear time-evolution diagnostic.
///
/// Silk BiPoSH ∝ σ/H(z~1100), Lensing BiPoSH ∝ σ/H(z~2).
/// Ratio tests shear decay law σ/H ∝ a^{−2} (matter era).
#[derive(Clone, Debug)]
pub(crate) struct ShearDecayResult {
    pub(crate) ratio_observed: f64,      // |A^{lens}| / |A^{Silk}| at some ℓ
    pub(crate) ratio_predicted: f64,     // (1+z_Silk)^{−2} / (1+z_lens)^{−2}
    pub(crate) decay_index: f64,          // best-fit n in σ/H ∝ a^{−n}
    pub(crate) consistent_with_gr: bool, // n = 2 within uncertainty?
}

/// Test shear decay law from Silk vs Lensing BiPoSH amplitudes.
pub(crate) fn shear_decay_test(
    silk_amplitude: f64,     // |A^{2M,Silk}| at reference ℓ
    lensing_amplitude: f64,  // |A^{2M,lens}| at reference ℓ
    z_silk: f64,             // ~ 1100
    z_lens_eff: f64,         // ~ 2 (effective lensing redshift)
    alpha_d_at_ell: f64,     // α_D at reference ℓ (from BE-07)
    beta_l_at_ell: f64,      // β_L at reference ℓ
    r_phi: f64,              // R_φ deflection power
) -> ShearDecayResult {
    // Silk amplitude ∝ α_D × σ/H(z_silk)
    // Lensing amplitude ∝ β_L × R_φ × σ/H(z_lens)
    // Ratio: A_lens/A_silk = (β_L R_φ)/(α_D) × σ(z_lens)/σ(z_silk)

    let coefficient_ratio = if alpha_d_at_ell.abs() > 1e-30 {
        beta_l_at_ell * r_phi / alpha_d_at_ell
    } else { 0.0 };

    let observed_shear_ratio = if coefficient_ratio.abs() > 1e-30 && silk_amplitude.abs() > 1e-30 {
        (lensing_amplitude / silk_amplitude) / coefficient_ratio
    } else { 0.0 };

    // For σ/H ∝ a^{−n}: σ(z_lens)/σ(z_silk) = ((1+z_lens)/(1+z_silk))^n
    let predicted_for_n2 = ((1.0 + z_lens_eff) / (1.0 + z_silk)).powi(2);

    // Best-fit decay index
    let decay_index = if observed_shear_ratio > 0.0 && z_silk > z_lens_eff {
        let log_ratio = observed_shear_ratio.ln();
        let log_a_ratio = ((1.0 + z_lens_eff) / (1.0 + z_silk)).ln();
        if log_a_ratio.abs() > 1e-10 { log_ratio / log_a_ratio } else { 2.0 }
    } else { 2.0 };

    ShearDecayResult {
        ratio_observed: observed_shear_ratio,
        ratio_predicted: predicted_for_n2,
        decay_index,
        consistent_with_gr: (decay_index - 2.0).abs() < 0.5,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_beta_l_positive() {
        for ell in [100, 500, 1000, 2000, 4000] {
            let b = beta_l(ell);
            assert!(b > 0.0 && b < 5.0, "β_L({}) = {:.4}", ell, b);
        }
    }

    #[test]
    fn test_beta_l_mild_ell_dependence() {
        let b100 = beta_l(100);
        let b2000 = beta_l(2000);
        let ratio = b100 / b2000;
        // Should be O(1), not ℓ² like α_D
        assert!(ratio > 0.5 && ratio < 5.0,
            "β_L ratio: {:.2} (must be ~O(1))", ratio);
    }

    #[test]
    fn test_phiphi_flrw_isotropic() {
        let cl = phiphi_directional(1e-7, 1000, 0.0);
        assert!((cl - 1e-7).abs() < 1e-20, "FLRW: no modulation");
    }

    #[test]
    fn test_biposh_lensing_flrw_zero() {
        let a = biposh_lensing(1000, 1000.0, 1e-7, &[0.0; 5], 1.0, 1e-6);
        for m in 0..5 { assert_eq!(a[m], 0.0); }
    }

    #[test]
    fn test_combined_flrw_zero() {
        let cb = CombinedBiPoSH::decompose(1000, 1000.0, 1000.0, 1e-7, &[0.0; 5], 1.0, 1e-6);
        for m in 0..5 { assert_eq!(cb.total[m], 0.0); }
    }

    #[test]
    fn test_combined_consistency() {
        let s2m = [1e-4, 0.0, 5e-5, 0.0, -3e-5];
        let cb = CombinedBiPoSH::decompose(2000, 1000.0, 1050.0, 1e-7, &s2m, 1.0, 1e-6);
        assert!(cb.consistency_error() < 1e-20, "Total != sum: err={:.2e}", cb.consistency_error());
    }

    #[test]
    fn test_silk_dominates_high_ell() {
        let s2m = [1e-4, 0.0, 5e-5, 0.0, 0.0];
        let cb = CombinedBiPoSH::decompose(3000, 100.0, 105.0, 1e-8, &s2m, 1.0, 1e-6);
        let silk_power: f64 = cb.silk.iter().map(|x| x * x).sum();
        let lens_power: f64 = cb.lensing.iter().map(|x| x * x).sum();
        assert!(silk_power > lens_power,
            "ℓ=3000: Silk={:.4e} must > Lensing={:.4e}", silk_power, lens_power);
    }

    #[test]
    fn test_channel_classification() {
        assert_eq!(CombinedBiPoSH::dominant_channel(500), BiPoSHChannel::LensingDominated);
        assert_eq!(CombinedBiPoSH::dominant_channel(1000), BiPoSHChannel::Mixed);
        assert_eq!(CombinedBiPoSH::dominant_channel(2500), BiPoSHChannel::SilkDominated);
    }

    #[test]
    fn test_shear_decay_gr_consistent() {
        // For σ/H ∝ a^{−2}: σ(z=2)/σ(z=1100) = ((1+2)/(1+1100))^2 ≈ 7.4e-6
        // Silk amplitude ∝ α_D × σ(z_silk), Lensing ∝ β_L × R_φ × σ(z_lens)
        let alpha_d_val = 0.5;
        let beta_l_val = 0.7;
        let r_phi = 1e-6;
        let coeff_ratio = beta_l_val * r_phi / alpha_d_val; // ≈ 1.4e-6
        let shear_ratio_gr = ((1.0 + 2.0) / (1.0 + 1100.0_f64)).powi(2); // ≈ 7.4e-6
        let silk_amp = 1e-5;
        let lens_amp = silk_amp * coeff_ratio * shear_ratio_gr;

        let result = shear_decay_test(silk_amp, lens_amp, 1100.0, 2.0,
            alpha_d_val, beta_l_val, r_phi);
        assert!(result.consistent_with_gr,
            "Decay index = {:.2} (expect ~2)", result.decay_index);
    }

    #[test]
    fn test_different_ell_dependence() {
        // α_D ∝ ℓ² but β_L ~ const → they have different ℓ-dependence
        let ad_500 = alpha_d(500, ELL_D_FIDUCIAL);
        let ad_2000 = alpha_d(2000, ELL_D_FIDUCIAL);
        let bl_500 = beta_l(500);
        let bl_2000 = beta_l(2000);

        let silk_ratio = ad_2000 / ad_500;     // should be ~16
        let lens_ratio = bl_2000 / bl_500;     // should be ~1

        assert!(silk_ratio > 10.0, "Silk: ℓ² growth, ratio = {:.1}", silk_ratio);
        assert!(lens_ratio < 3.0, "Lensing: ~constant, ratio = {:.1}", lens_ratio);
    }
}
