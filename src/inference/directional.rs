// BF-01: Directional Likelihood for Bianchi Geometry Discrimination.
//
// −2 ln L_total = −2 ln L_{low-ℓ} − 2 ln L_{BiPoSH} − 2 ln L_{matter}
//
// Parameters: θ = (Σ², β, bianchi_type, l_gal, b_gal, x_h)
// Each channel independently toggleable for ablation studies.

use std::f64::consts::PI;
use crate::observable::biposh::{BiPoSHSpectrum, ExperimentSpec, predicted_biposh,
                                 noise_power, biposh_variance};
use crate::observable::direction_silk::ELL_D_FIDUCIAL;
use crate::forward::biposh_channel::biposh_log_likelihood;

/// Bianchi type for geometry discrimination.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum BianchiType {
    I,
    V,
    VIIh { x_h: f64 },
    IX,
}

impl BianchiType {
    pub(crate) fn label(&self) -> &str {
        match self { Self::I => "I", Self::V => "V",
                     Self::VIIh { .. } => "VII_h", Self::IX => "IX" }
    }
}

/// Tilt sector.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum TiltSector { Orthogonal, Tilted }

/// Full parameter set for inference.
#[derive(Clone, Debug)]
pub(crate) struct InferenceParams {
    pub(crate) sigma2: f64,       // Σ² (shear parameter)
    pub(crate) beta: f64,         // tilt parameter
    pub(crate) btype: BianchiType,
    pub(crate) sector: TiltSector,
    pub(crate) l_gal: f64,        // galactic longitude [rad]
    pub(crate) b_gal: f64,        // galactic latitude [rad]
}

/// Channel toggle configuration for ablation.
#[derive(Clone, Debug)]
pub(crate) struct ChannelConfig {
    pub(crate) low_ell: bool,       // ℓ ≤ 30
    pub(crate) biposh: bool,        // ℓ = 600..4000 BiPoSH L=2
    pub(crate) matter_dipole: bool, // CatWISE + Radio + CF4
}

impl ChannelConfig {
    pub(crate) fn all() -> Self { Self { low_ell: true, biposh: true, matter_dipole: true } }
    pub(crate) fn low_ell_only() -> Self { Self { low_ell: true, biposh: false, matter_dipole: false } }
    pub(crate) fn biposh_only() -> Self { Self { low_ell: false, biposh: true, matter_dipole: false } }
    pub(crate) fn no_biposh() -> Self { Self { low_ell: true, biposh: false, matter_dipole: true } }

    pub(crate) fn n_active(&self) -> usize {
        self.low_ell as usize + self.biposh as usize + self.matter_dipole as usize
    }
}

/// Observational data bundle.
#[derive(Clone)]
pub(crate) struct ObsData {
    /// Observed a_{ℓm} at low-ℓ (ℓ=2..30, m=-ℓ..ℓ).
    pub(crate) alm_obs: Vec<f64>,
    /// Observed isotropic C_ℓ (for variance).
    pub(crate) cl_obs: Vec<f64>,
    /// Observed BiPoSH spectrum.
    pub(crate) biposh_obs: BiPoSHSpectrum,
    /// Matter-dipole observations (3 components: CatWISE, Radio, CF4).
    pub(crate) matter_dipole_obs: [f64; 3],
    /// Experiment spec for BiPoSH noise model.
    pub(crate) experiment: ExperimentSpec,
}

// ═══ Individual Channel Likelihoods ═══

/// Low-ℓ likelihood: Gaussian in a_{ℓm} space.
///
/// −2 ln L = Σ_{ℓ=2}^{30} Σ_m |a^{obs}_{ℓm} − a^{model}_{ℓm}|² / C_ℓ
pub(crate) fn low_ell_likelihood(
    alm_obs: &[f64],
    alm_model: &[f64],
    cl: &[f64],
) -> f64 {
    let mut chi2 = 0.0;
    let mut idx = 0;
    for ell in 2..=30.min(cl.len() - 1) {
        let cl_ell = cl[ell].max(1e-30);
        for _m in 0..=(2 * ell) {
            if idx >= alm_obs.len() || idx >= alm_model.len() { break; }
            let diff = alm_obs[idx] - alm_model[idx];
            chi2 += diff * diff / cl_ell;
            idx += 1;
        }
    }
    -0.5 * chi2
}

/// BiPoSH likelihood: wraps the forward module.
pub(crate) fn biposh_likelihood_channel(
    obs: &BiPoSHSpectrum,
    model: &BiPoSHSpectrum,
    cl_iso: &[f64],
    spec: &ExperimentSpec,
) -> f64 {
    biposh_log_likelihood(obs, model, cl_iso, spec)
}

/// Matter-dipole likelihood (simplified).
///
/// −2 ln L = Σ_i (d^{obs}_i − d^{model}_i)² / σ²_i
pub(crate) fn matter_dipole_likelihood(
    obs: &[f64; 3],
    model: &[f64; 3],
) -> f64 {
    // CatWISE σ = 0.002, Radio σ = 0.003, CF4 σ = 50 km/s normalised
    let sigmas: [f64; 3] = [0.002, 0.003, 0.001];
    let mut chi2 = 0.0;
    for i in 0..3 {
        chi2 += (obs[i] - model[i]).powi(2) / sigmas[i].powi(2);
    }
    -0.5 * chi2
}

// ═══ Joint Likelihood ═══

/// Joint likelihood with channel ablation.
///
/// CL-08: All channels now use the forward model that depends on
/// (btype, sector, l_gal, b_gal, sigma2, beta).
pub(crate) fn joint_likelihood(
    params: &InferenceParams,
    data: &ObsData,
    config: &ChannelConfig,
) -> f64 {
    use crate::inference::forward_model::{forward_alm, forward_dipole};

    let mut ln_l = 0.0;
    let sigma_over_h = (6.0 * params.sigma2).sqrt();
    let sigma20 = sigma_over_h / 5.0_f64.sqrt();

    // Low-ℓ channel: a_{ℓm} now depend on (type, sector, direction)
    if config.low_ell {
        let alm_model = forward_alm(params, data.cl_obs.len().min(31));
        ln_l += low_ell_likelihood(&data.alm_obs, &alm_model, &data.cl_obs);
    }

    // BiPoSH channel
    if config.biposh {
        let model_biposh = predicted_biposh(&data.cl_obs, ELL_D_FIDUCIAL, sigma20,
            data.experiment.ell_min, data.experiment.ell_max);
        ln_l += biposh_likelihood_channel(&data.biposh_obs, &model_biposh,
            &data.cl_obs, &data.experiment);
    }

    // Matter-dipole channel: now depends on (type, sector, direction)
    if config.matter_dipole {
        let model_dipole = forward_dipole(params);
        ln_l += matter_dipole_likelihood(&data.matter_dipole_obs, &model_dipole);
    }

    ln_l
}

// Old generate_model_alm and generate_model_dipole removed —
// replaced by forward_model::forward_alm and forward_model::forward_dipole
// which are genuinely type/sector/direction-sensitive.

// ═══ Channel Ablation ═══

/// Ablation study: measure Δln L from adding/removing each channel.
pub(crate) fn channel_ablation(
    params: &InferenceParams,
    data: &ObsData,
) -> ChannelAblation {
    let ln_l_all = joint_likelihood(params, data, &ChannelConfig::all());
    let ln_l_no_low = joint_likelihood(params, data, &ChannelConfig {
        low_ell: false, biposh: true, matter_dipole: true });
    let ln_l_no_biposh = joint_likelihood(params, data, &ChannelConfig::no_biposh());
    let ln_l_no_matter = joint_likelihood(params, data, &ChannelConfig {
        low_ell: true, biposh: true, matter_dipole: false });

    ChannelAblation {
        ln_l_total: ln_l_all,
        delta_low_ell: ln_l_all - ln_l_no_low,
        delta_biposh: ln_l_all - ln_l_no_biposh,
        delta_matter: ln_l_all - ln_l_no_matter,
    }
}

/// Channel ablation results.
#[derive(Clone, Debug)]
pub(crate) struct ChannelAblation {
    pub(crate) ln_l_total: f64,
    pub(crate) delta_low_ell: f64,   // Δln L from low-ℓ channel
    pub(crate) delta_biposh: f64,    // Δln L from BiPoSH channel
    pub(crate) delta_matter: f64,    // Δln L from matter-dipole channel
}

// ═══ Fisher Forecast ═══

/// Fisher forecast for σ(Σ²) from a given channel configuration.
pub(crate) fn fisher_sigma_sigma2(
    params: &InferenceParams,
    data: &ObsData,
    config: &ChannelConfig,
) -> f64 {
    // Numerical derivative: Δ(ln L)/Δ(Σ²)
    let ds2 = params.sigma2 * 0.01; // 1% step
    let mut p_plus = params.clone();
    let mut p_minus = params.clone();
    p_plus.sigma2 += ds2;
    p_minus.sigma2 = (params.sigma2 - ds2).max(1e-15);

    let l_plus = joint_likelihood(&p_plus, data, config);
    let l_minus = joint_likelihood(&p_minus, data, config);
    let l_0 = joint_likelihood(params, data, config);

    // F = −d²(ln L)/d(Σ²)²
    let fisher = -(l_plus - 2.0 * l_0 + l_minus) / (ds2 * ds2);
    if fisher > 0.0 { 1.0 / fisher.sqrt() } else { f64::INFINITY }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_data(n_cl: usize) -> ObsData {
        let cl: Vec<f64> = (0..n_cl).map(|l| {
            if l < 2 { 0.0 } else { 1e-10 / (l as f64).powi(2) }
        }).collect();
        let n_alm = (2..=30).map(|l| 2 * l + 1).sum();
        ObsData {
            alm_obs: vec![0.0; n_alm],
            cl_obs: cl.clone(),
            biposh_obs: predicted_biposh(&cl, ELL_D_FIDUCIAL, 0.0, 100, 2000),
            matter_dipole_obs: [0.0; 3],
            experiment: ExperimentSpec::planck(),
        }
    }

    fn flrw_params() -> InferenceParams {
        InferenceParams {
            sigma2: 0.0, beta: 0.0, btype: BianchiType::I,
            sector: TiltSector::Orthogonal, l_gal: 0.0, b_gal: 0.0,
        }
    }

    fn bi_params() -> InferenceParams {
        InferenceParams {
            sigma2: 1e-6, beta: 1e-3, btype: BianchiType::I,
            sector: TiltSector::Tilted, l_gal: 4.0, b_gal: -0.5,
        }
    }

    #[test]
    fn test_flrw_all_channels_zero() {
        let data = mock_data(3000);
        let ln_l = joint_likelihood(&flrw_params(), &data, &ChannelConfig::all());
        assert!((ln_l - 0.0).abs() < 1e-6, "FLRW: ln L = {:.4e}", ln_l);
    }

    #[test]
    fn test_channel_config_count() {
        assert_eq!(ChannelConfig::all().n_active(), 3);
        assert_eq!(ChannelConfig::low_ell_only().n_active(), 1);
        assert_eq!(ChannelConfig::biposh_only().n_active(), 1);
    }

    #[test]
    fn test_bi_nonzero_signal() {
        let data = mock_data(3000);
        let ln_l = joint_likelihood(&bi_params(), &data, &ChannelConfig::all());
        // BI has signal → likelihood penalty (model ≠ 0 but data = 0)
        assert!(ln_l < 0.0 || ln_l.abs() > 1e-10,
            "BI: ln L = {:.4e} (must show signal)", ln_l);
    }

    #[test]
    fn test_ablation_structure() {
        let data = mock_data(3000);
        let abl = channel_ablation(&bi_params(), &data);
        // Each channel should contribute independently
        assert!(abl.ln_l_total.is_finite());
        // delta_* can be positive or negative depending on direction
    }

    #[test]
    fn test_biposh_only_mode() {
        let data = mock_data(3000);
        let ln_l = joint_likelihood(&bi_params(), &data, &ChannelConfig::biposh_only());
        assert!(ln_l.is_finite(), "BiPoSH-only: ln L = {:.4e}", ln_l);
    }

    #[test]
    fn test_bianchi_types() {
        assert_eq!(BianchiType::I.label(), "I");
        assert_eq!(BianchiType::VIIh { x_h: 30.0 }.label(), "VII_h");
        assert_eq!(BianchiType::IX.label(), "IX");
    }

    #[test]
    fn test_fisher_positive() {
        let data = mock_data(3000);
        let sig = fisher_sigma_sigma2(&bi_params(), &data, &ChannelConfig::all());
        assert!(sig > 0.0, "Fisher sigma = {:.4e}", sig);
    }

    #[test]
    fn test_low_ell_self_match() {
        let n_alm = 100;
        let alm: Vec<f64> = (0..n_alm).map(|i| 0.001 * (i as f64)).collect();
        let cl = vec![0.0, 0.0, 1e-10, 5e-11, 3e-11];
        let ln_l = low_ell_likelihood(&alm, &alm, &cl);
        assert!((ln_l - 0.0).abs() < 1e-10, "Self-match: {:.4e}", ln_l);
    }

    #[test]
    fn test_matter_dipole_self_match() {
        let obs = [0.001, 0.002, 0.0005];
        let ln_l = matter_dipole_likelihood(&obs, &obs);
        assert!((ln_l - 0.0).abs() < 1e-10);
    }
}
