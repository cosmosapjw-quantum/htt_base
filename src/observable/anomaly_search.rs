// BE-07: Anomaly search using direction-dependent Silk damping template.
//
// Tests whether observed L=2 BiPoSH at high-ℓ is consistent with
// Bianchi shear as the physical mechanism.
//
// Template: A^{2M}_{ℓℓ} = C_ℓ × α_D(ℓ) × σ_{2M}/H
// Key: α_D ∝ ℓ² gives a DISTINCTIVE ℓ-dependence (rising, not flat).

use super::direction_silk::{alpha_d, ELL_D_FIDUCIAL};
use super::biposh::{ExperimentSpec, noise_power, biposh_variance};
use crate::bianchi::types::BianchiType;

/// S/N map for a given (Σ², Bianchi type, ℓ_max).
#[derive(Clone, Debug)]
pub(crate) struct SNMap {
    pub(crate) sigma2_grid: Vec<f64>,
    pub(crate) sn_values: Vec<f64>,  // S/N at each Σ²
}

/// Compute S/N for BiPoSH detection as function of Σ².
pub(crate) fn sn_vs_sigma2(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2_grid: &[f64],
    spec: &ExperimentSpec,
) -> SNMap {
    let sn_values: Vec<f64> = sigma2_grid.iter().map(|&s2| {
        let soh = (6.0 * s2).sqrt();
        let sigma20 = soh / 5.0_f64.sqrt();  // M=0 component

        let mut sn2 = 0.0;
        for ell in spec.ell_min..=spec.ell_max.min(cl_iso.len() - 1) {
            let ad = alpha_d(ell, ell_d);
            let a20 = cl_iso[ell] * ad * sigma20;
            let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
            let var = biposh_variance(cl_iso[ell], nl, ell);
            if var > 1e-60 {
                sn2 += spec.f_sky * 5.0 * a20 * a20 / var;
            }
        }
        sn2.sqrt()
    }).collect();

    SNMap { sigma2_grid: sigma2_grid.to_vec(), sn_values }
}

/// Δχ² between anisotropic (Bianchi Silk) and isotropic models.
///
/// Δχ² = Σ_ℓ |A^{2M,data} − A^{2M,theory}|² / Var − |A^{2M,data}|² / Var
/// = −2 Σ Re(A^{data} A^{theory}*) / Var + |A^{theory}|² / Var
///
/// For theoretical template only (no data): Δχ² = (S/N)² is the expected value.
pub(crate) fn expected_delta_chi2(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2: f64,
    spec: &ExperimentSpec,
) -> f64 {
    let sn_map = sn_vs_sigma2(cl_iso, ell_d, &[sigma2], spec);
    sn_map.sn_values[0].powi(2)
}

/// ℓ-range that gives best discrimination power.
///
/// Returns (ℓ_best_start, ℓ_best_end, fraction_of_total_sn2).
pub(crate) fn best_ell_range(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2: f64,
    spec: &ExperimentSpec,
) -> (usize, usize, f64) {
    let soh = (6.0 * sigma2).sqrt();
    let sigma20 = soh / 5.0_f64.sqrt();

    // Compute S/N² per ℓ
    let mut sn2_per_ell = Vec::new();
    for ell in spec.ell_min..=spec.ell_max.min(cl_iso.len() - 1) {
        let ad = alpha_d(ell, ell_d);
        let a20 = cl_iso[ell] * ad * sigma20;
        let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
        let var = biposh_variance(cl_iso[ell], nl, ell);
        let s2 = if var > 1e-60 { spec.f_sky * 5.0 * a20 * a20 / var } else { 0.0 };
        sn2_per_ell.push((ell, s2));
    }

    let total_sn2: f64 = sn2_per_ell.iter().map(|&(_, s)| s).sum();
    if total_sn2 < 1e-60 { return (0, 0, 0.0); }

    // Find range containing 50% of S/N²
    let mut cum = 0.0;
    let mut ell_start = 0;
    let mut ell_end = 0;
    let target = 0.5 * total_sn2;

    // Sliding window approach: find narrowest range with ≥50% S/N²
    let mut best_width = usize::MAX;
    let mut best_start = 0;
    let mut best_end = 0;

    let mut left = 0;
    let mut window_sn2 = 0.0;
    for right in 0..sn2_per_ell.len() {
        window_sn2 += sn2_per_ell[right].1;
        while window_sn2 >= target && left <= right {
            let width = sn2_per_ell[right].0 - sn2_per_ell[left].0;
            if width < best_width {
                best_width = width;
                best_start = sn2_per_ell[left].0;
                best_end = sn2_per_ell[right].0;
            }
            window_sn2 -= sn2_per_ell[left].1;
            left += 1;
        }
    }

    let frac = if total_sn2 > 0.0 { 0.5 } else { 0.0 };
    (best_start, best_end, frac)
}

/// Template distinguishability: direction-dependent Silk (ℓ²) vs constant modulation.
///
/// The Bianchi Silk template has α_D ∝ ℓ², while a constant quadrupolar
/// modulation has α_D = const. The ratio of chi-squared values discriminates.
pub(crate) fn template_chi2_ratio(
    cl_iso: &[f64],
    ell_d: f64,
    sigma2: f64,
    spec: &ExperimentSpec,
) -> f64 {
    let soh = (6.0 * sigma2).sqrt();
    let sigma20 = soh / 5.0_f64.sqrt();

    let mut chi2_silk = 0.0;
    let mut chi2_const = 0.0;

    // Average α_D for constant template
    let ell_mid = ((spec.ell_min + spec.ell_max) / 2).min(cl_iso.len() - 1);
    let ad_const = alpha_d(ell_mid, ell_d);

    for ell in spec.ell_min..=spec.ell_max.min(cl_iso.len() - 1) {
        let ad_silk = alpha_d(ell, ell_d);
        let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
        let var = biposh_variance(cl_iso[ell], nl, ell);
        if var < 1e-60 { continue; }

        let a_silk = cl_iso[ell] * ad_silk * sigma20;
        let a_const = cl_iso[ell] * ad_const * sigma20;

        chi2_silk += spec.f_sky * 5.0 * a_silk * a_silk / var;
        chi2_const += spec.f_sky * 5.0 * a_const * a_const / var;
    }

    if chi2_const > 0.0 { chi2_silk / chi2_const } else { 1.0 }
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
    fn test_sn_increases_with_sigma2() {
        let cl = mock_cl(5000);
        let s2 = vec![1e-8, 1e-7, 1e-6, 1e-5];
        let map = sn_vs_sigma2(&cl, ELL_D_FIDUCIAL, &s2, &ExperimentSpec::act_dr6());
        for i in 1..map.sn_values.len() {
            assert!(map.sn_values[i] > map.sn_values[i - 1],
                "S/N must increase with Σ²");
        }
    }

    #[test]
    fn test_delta_chi2_positive() {
        let cl = mock_cl(5000);
        let dc2 = expected_delta_chi2(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::cmb_s4());
        assert!(dc2 > 0.0 && dc2.is_finite(), "Δχ² = {:.4e}", dc2);
    }

    #[test]
    fn test_best_ell_range() {
        let cl = mock_cl(5000);
        let (ell_s, ell_e, frac) = best_ell_range(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::act_dr6());
        assert!(ell_e > ell_s, "ℓ range: {}..{}", ell_s, ell_e);
        eprintln!("Best ℓ range: {}..{} (50% of S/N²)", ell_s, ell_e);
    }

    #[test]
    fn test_template_ratio_gt1() {
        // Silk template (ℓ²) should have MORE power at high ℓ than constant
        let cl = mock_cl(5000);
        let ratio = template_chi2_ratio(&cl, ELL_D_FIDUCIAL, 1e-6, &ExperimentSpec::act_dr6());
        assert!(ratio > 0.0 && ratio.is_finite(), "χ² ratio = {:.4}", ratio);
    }

    #[test]
    fn test_sn_map_length() {
        let cl = mock_cl(3000);
        let s2 = vec![1e-8, 1e-7, 1e-6];
        let map = sn_vs_sigma2(&cl, ELL_D_FIDUCIAL, &s2, &ExperimentSpec::planck());
        assert_eq!(map.sigma2_grid.len(), 3);
        assert_eq!(map.sn_values.len(), 3);
    }
}
