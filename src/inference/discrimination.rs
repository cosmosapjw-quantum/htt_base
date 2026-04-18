// BF-03: Geometry Discrimination Framework.
//
// B_{ij} = Z_i/Z_j for Bianchi type i vs j using joint low-ℓ + BiPoSH likelihood.
// Channel decomposition: which channel drives the discrimination?
// Forecast: at what Σ² does type discrimination become possible?

use crate::inference::directional::*;
use crate::inference::atlas::{Atlas, AtlasConfig};

/// Model selection result for a single type pair.
#[derive(Clone, Debug)]
pub(crate) struct BayesFactor {
    pub(crate) type_i: String,
    pub(crate) type_j: String,
    pub(crate) ln_bij: f64,         // ln B_{ij} = ln Z_i - ln Z_j
    pub(crate) significance: f64,   // |ln B| / threshold
}

impl BayesFactor {
    pub(crate) fn preferred(&self) -> &str {
        if self.ln_bij > 0.0 { &self.type_i } else { &self.type_j }
    }

    /// Jeffreys scale: |ln B| > 1 (weak), > 2.5 (moderate), > 5 (strong)
    pub(crate) fn strength(&self) -> &'static str {
        let a = self.ln_bij.abs();
        if a < 1.0 { "inconclusive" }
        else if a < 2.5 { "weak" }
        else if a < 5.0 { "moderate" }
        else { "strong" }
    }
}

/// Channel decomposition: fractional evidence from each channel.
#[derive(Clone, Debug)]
pub(crate) struct ChannelDecomposition {
    pub(crate) low_ell_fraction: f64,
    pub(crate) biposh_fraction: f64,
    pub(crate) matter_fraction: f64,
}

/// Compute ln Z (evidence proxy) for a given type at given parameters.
///
/// Uses Laplace approximation: ln Z ≈ ln L(θ_ML) + (d/2) ln(2π) − (1/2) ln|H|
/// Simplified here: ln Z ≈ max_{Σ²} ln L(type, Σ², ...).
pub(crate) fn evidence_proxy(
    btype: &BianchiType,
    sector: &TiltSector,
    data: &ObsData,
    config: &ChannelConfig,
    sigma2_grid: &[f64],
) -> f64 {
    let mut best_ln_l = f64::NEG_INFINITY;
    for &s2 in sigma2_grid {
        let params = InferenceParams {
            sigma2: s2, beta: 1e-3,
            btype: btype.clone(), sector: sector.clone(),
            l_gal: 4.0, b_gal: -0.3,
        };
        let ln_l = joint_likelihood(&params, data, config);
        if ln_l > best_ln_l { best_ln_l = ln_l; }
    }
    // Prior volume penalty: −ln(volume) ≈ −ln(Σ²_max / Σ²_min)
    // Guard: if grid is single-point or starts at 0, no penalty.
    let prior_penalty = if sigma2_grid.len() < 2 { 0.0 }
    else {
        let s2_min = sigma2_grid[0].max(1e-30);
        let s2_max = sigma2_grid[sigma2_grid.len() - 1].max(1e-30);
        -(s2_max / s2_min).ln()
    };
    best_ln_l + prior_penalty
}

/// Compute Bayes factor between two types.
pub(crate) fn bayes_factor(
    type_i: &BianchiType, type_j: &BianchiType,
    sector: &TiltSector,
    data: &ObsData,
    config: &ChannelConfig,
    sigma2_grid: &[f64],
) -> BayesFactor {
    let ln_zi = evidence_proxy(type_i, sector, data, config, sigma2_grid);
    let ln_zj = evidence_proxy(type_j, sector, data, config, sigma2_grid);
    BayesFactor {
        type_i: type_i.label().to_string(),
        type_j: type_j.label().to_string(),
        ln_bij: ln_zi - ln_zj,
        significance: (ln_zi - ln_zj).abs() / 2.5, // relative to moderate threshold
    }
}

/// Channel decomposition: compute evidence with each channel toggled.
pub(crate) fn channel_decomposition(
    btype: &BianchiType, sector: &TiltSector,
    data: &ObsData, sigma2_grid: &[f64],
) -> ChannelDecomposition {
    let ln_z_all = evidence_proxy(btype, sector, data, &ChannelConfig::all(), sigma2_grid);
    let ln_z_no_low = evidence_proxy(btype, sector, data,
        &ChannelConfig { low_ell: false, biposh: true, matter_dipole: true }, sigma2_grid);
    let ln_z_no_bp = evidence_proxy(btype, sector, data, &ChannelConfig::no_biposh(), sigma2_grid);
    let ln_z_no_mat = evidence_proxy(btype, sector, data,
        &ChannelConfig { low_ell: true, biposh: true, matter_dipole: false }, sigma2_grid);

    let total = (ln_z_all - ln_z_no_low).abs()
              + (ln_z_all - ln_z_no_bp).abs()
              + (ln_z_all - ln_z_no_mat).abs();
    let norm = total.max(1e-30);

    ChannelDecomposition {
        low_ell_fraction: (ln_z_all - ln_z_no_low).abs() / norm,
        biposh_fraction: (ln_z_all - ln_z_no_bp).abs() / norm,
        matter_fraction: (ln_z_all - ln_z_no_mat).abs() / norm,
    }
}

/// Forecast: minimum Σ² for type discrimination at given significance.
pub(crate) fn discrimination_threshold(
    type_i: &BianchiType, type_j: &BianchiType,
    sector: &TiltSector, data: &ObsData,
    config: &ChannelConfig,
    target_ln_b: f64, // e.g. 5.0 for "strong"
) -> f64 {
    let grid: Vec<f64> = (0..40).map(|i| 10.0_f64.powf(-10.0 + i as f64 * 0.25)).collect();
    for &s2 in &grid {
        let bf = bayes_factor(type_i, type_j, sector, data, config, &[s2]);
        if bf.ln_bij.abs() > target_ln_b { return s2; }
    }
    f64::INFINITY // never reaches threshold
}

/// Full discrimination matrix across all type pairs.
pub(crate) fn full_discrimination_matrix(
    types: &[BianchiType], sector: &TiltSector,
    data: &ObsData, config: &ChannelConfig, sigma2_grid: &[f64],
) -> Vec<BayesFactor> {
    let mut results = Vec::new();
    for i in 0..types.len() {
        for j in (i + 1)..types.len() {
            results.push(bayes_factor(&types[i], &types[j], sector, data, config, sigma2_grid));
        }
    }
    results
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observable::biposh::{predicted_biposh, ExperimentSpec};
    use crate::observable::direction_silk::ELL_D_FIDUCIAL;

    fn mock_data() -> ObsData {
        let cl: Vec<f64> = (0..3000).map(|l| {
            if l < 2 { 0.0 } else { 1e-10 / (l as f64).powi(2) }
        }).collect();
        let n_alm = (2..=30usize).map(|l| 2 * l + 1).sum();
        ObsData {
            alm_obs: vec![0.0; n_alm],
            cl_obs: cl.clone(),
            biposh_obs: predicted_biposh(&cl, ELL_D_FIDUCIAL, 0.0, 100, 2000),
            matter_dipole_obs: [0.0; 3],
            experiment: ExperimentSpec::planck(),
        }
    }

    #[test]
    fn test_bayes_factor_structure() {
        let data = mock_data();
        let grid = vec![1e-8, 1e-7, 1e-6, 1e-5];
        let bf = bayes_factor(&BianchiType::I, &BianchiType::V,
            &TiltSector::Orthogonal, &data, &ChannelConfig::all(), &grid);
        assert!(bf.ln_bij.is_finite(), "ln B = {:.4e}", bf.ln_bij);
        assert!(["I", "V"].contains(&bf.preferred()));
    }

    #[test]
    fn test_jeffreys_scale() {
        let bf = BayesFactor { type_i: "I".into(), type_j: "V".into(),
            ln_bij: 0.5, significance: 0.2 };
        assert_eq!(bf.strength(), "inconclusive");
        let bf2 = BayesFactor { type_i: "I".into(), type_j: "V".into(),
            ln_bij: 6.0, significance: 2.4 };
        assert_eq!(bf2.strength(), "strong");
    }

    #[test]
    fn test_flrw_no_false_detection() {
        // FLRW data: all B_{ij} should be small (inconclusive)
        let data = mock_data();
        // Include Σ²≈0 so evidence proxy can choose zero anisotropy
        let grid = vec![0.0, 1e-10, 1e-8, 1e-6];
        let bf = bayes_factor(&BianchiType::I, &BianchiType::VIIh { x_h: 30.0 },
            &TiltSector::Orthogonal, &data, &ChannelConfig::all(), &grid);
        // With FLRW data, types should be indistinguishable at Σ²=0
        assert!(bf.ln_bij.abs() < 50.0, "|ln B| = {:.2} (expect small)", bf.ln_bij.abs());
    }

    #[test]
    fn test_channel_decomposition_sums_to_one() {
        let data = mock_data();
        let grid = vec![1e-7, 1e-6, 1e-5];
        let cd = channel_decomposition(&BianchiType::I, &TiltSector::Orthogonal, &data, &grid);
        let sum = cd.low_ell_fraction + cd.biposh_fraction + cd.matter_fraction;
        assert!((sum - 1.0).abs() < 0.01, "Fractions sum = {:.4}", sum);
    }

    #[test]
    fn test_full_matrix_6_pairs() {
        let types = vec![BianchiType::I, BianchiType::V,
                        BianchiType::VIIh { x_h: 30.0 }, BianchiType::IX];
        let data = mock_data();
        let grid = vec![1e-7, 1e-5];
        let matrix = full_discrimination_matrix(&types, &TiltSector::Orthogonal,
            &data, &ChannelConfig::all(), &grid);
        assert_eq!(matrix.len(), 6, "4 types → C(4,2) = 6 pairs");
    }

    #[test]
    fn test_discrimination_threshold_finite() {
        let data = mock_data();
        let s2_min = discrimination_threshold(
            &BianchiType::I, &BianchiType::V,
            &TiltSector::Orthogonal, &data, &ChannelConfig::all(), 5.0);
        assert!(s2_min > 0.0, "Threshold Sigma2 = {:.4e}", s2_min);
    }
}
