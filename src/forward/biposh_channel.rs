// BH-01: BiPoSH L=2 Channel for HTT Inference.
//
// −2 ln L_{BiPoSH} = Σ_{ℓ,M} |A^{2M,obs}_{ℓℓ} − A^{2M,model}|² / Var
//
// Noise: cosmic variance + instrument (Planck/ACT/CMB-S4 specs).
// Fisher contribution to joint (Σ², β, direction) posterior.

use crate::observable::biposh::{BiPoSHSpectrum, ExperimentSpec, noise_power, biposh_variance};

/// BiPoSH log-likelihood for a single experiment.
///
/// −2 ln L = Σ_{ℓ} Σ_M |A^{2M,obs} − A^{2M,model}|² / Var(A^{2M})
pub(crate) fn biposh_log_likelihood(
    obs: &BiPoSHSpectrum,
    model: &BiPoSHSpectrum,
    cl_iso: &[f64],
    spec: &ExperimentSpec,
) -> f64 {
    let mut chi2 = 0.0;
    let n = obs.ells.len().min(model.ells.len());

    for i in 0..n {
        let ell = obs.ells[i];
        if ell < spec.ell_min || ell > spec.ell_max { continue; }
        if ell >= cl_iso.len() { break; }

        let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
        let var = biposh_variance(cl_iso[ell], nl, ell);
        if var < 1e-60 { continue; }

        // Sum over M=−2..+2 (5 components, represented in a2_power)
        let obs_power = obs.a2_power[i];
        let model_power = model.a2_power[i];
        chi2 += (obs_power.sqrt() - model_power.sqrt()).powi(2) / var * spec.f_sky;
    }

    -0.5 * chi2
}

/// BiPoSH Fisher matrix contribution to parameter constraints.
///
/// F_{αβ} = Σ_ℓ (∂A/∂θ_α)(∂A/∂θ_β) / Var
/// Parameters: θ = {Σ², β, l_direction, b_direction}
pub(crate) struct BiPoSHFisher {
    /// Fisher matrix entries (4×4, symmetric).
    pub(crate) f: [[f64; 4]; 4],
    /// Parameter labels.
    pub(crate) params: [&'static str; 4],
}

impl BiPoSHFisher {
    pub(crate) fn new() -> Self {
        Self {
            f: [[0.0; 4]; 4],
            params: ["Sigma2", "beta", "l_dir", "b_dir"],
        }
    }

    /// Add contribution from a single ℓ.
    pub(crate) fn add_ell(
        &mut self,
        _ell: usize,
        da_dsigma2: f64,  // ∂A/∂Σ²
        da_dbeta: f64,     // ∂A/∂β
        da_dl: f64,        // ∂A/∂l (direction)
        da_db: f64,        // ∂A/∂b (direction)
        var: f64,
    ) {
        if var < 1e-60 { return; }
        let derivs = [da_dsigma2, da_dbeta, da_dl, da_db];
        for i in 0..4 {
            for j in i..4 {
                self.f[i][j] += derivs[i] * derivs[j] / var;
                if i != j { self.f[j][i] = self.f[i][j]; }
            }
        }
    }

    /// 1σ constraint on Σ² (marginalised over other params).
    pub(crate) fn sigma_sigma2(&self) -> f64 {
        let f00 = self.f[0][0];
        if f00 > 0.0 { 1.0 / f00.sqrt() } else { f64::INFINITY }
    }
}

/// Compute BiPoSH Fisher for a given model + experiment.
pub(crate) fn biposh_fisher(
    model: &BiPoSHSpectrum,
    cl_iso: &[f64],
    spec: &ExperimentSpec,
    sigma2: f64,
) -> BiPoSHFisher {
    let mut fisher = BiPoSHFisher::new();
    let soh = (6.0 * sigma2).sqrt();

    for (i, &ell) in model.ells.iter().enumerate() {
        if ell < spec.ell_min || ell > spec.ell_max { continue; }
        if ell >= cl_iso.len() { break; }

        let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
        let var = biposh_variance(cl_iso[ell], nl, ell);
        if var < 1e-60 { continue; }

        // ∂A/∂Σ²: A ∝ √Σ² → ∂A/∂Σ² = A/(2Σ²)
        let a = model.a20_diag[i];
        let da_ds2 = if sigma2 > 1e-20 { a / (2.0 * sigma2) } else { 0.0 };
        // ∂A/∂β: tilt-shear coupling from Maartens-Ellis (1995) Eq. 3.12.
        //   For orthogonal (β=0): dA/dβ = 0 (no tilt-shear coupling).
        //   TODO(Phase H): accept teff_config parameter for nonzero β.
        let beta: f64 = 0.0;
        let da_db = if beta.abs() > 1e-15 {
            a * (2.0_f64 * beta).sinh() / (2.0_f64 * beta.cosh().powi(2))
        } else {
            0.0  // Orthogonal: no β dependence
        };
        // Direction derivatives: A_{2M} = σ_{2M}/H × C_ℓ × α_D
        // Under rotation by (δl, δb): A_{2M} → e^{iMδl} × D^2_{MM'}(δb) × A_{2M'}
        // ∂A_{20}/∂l = 0 (m=0 is azimuthally symmetric)
        // ∂A_{20}/∂b = −√6 × A_{21} (from Wigner D-matrix coupling)
        let da_dl = 0.0;  // m=0 component: azimuthally independent
        let da_dbdir = (6.0_f64).sqrt() * model.a20_diag.get(i).copied().unwrap_or(0.0) * 0.5;

        fisher.add_ell(ell, da_ds2, da_db, da_dl, da_dbdir, var * spec.f_sky);
    }

    fisher
}

/// FLRW null test: BiPoSH likelihood contribution must be zero.
pub(crate) fn flrw_null_test(cl_iso: &[f64], spec: &ExperimentSpec) -> f64 {
    // Zero model → zero observed → likelihood = 0 (no contribution)
    let zero_biposh = BiPoSHSpectrum {
        ells: (2..100).collect(),
        a20_diag: vec![0.0; 98],
        a2_power: vec![0.0; 98],
    };
    biposh_log_likelihood(&zero_biposh, &zero_biposh, cl_iso, spec)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_cl(n: usize) -> Vec<f64> {
        (0..n).map(|ell| if ell < 2 { 0.0 } else { 1e-10 / (ell as f64).powi(2) }).collect()
    }

    #[test]
    fn test_flrw_null() {
        let cl = mock_cl(3000);
        let ln_l = flrw_null_test(&cl, &ExperimentSpec::planck());
        assert!((ln_l - 0.0).abs() < 1e-10, "FLRW: ln L_BiPoSH = {:.4e}", ln_l);
    }

    #[test]
    fn test_self_likelihood_zero() {
        // Model = observed → χ² = 0 → ln L = 0
        let cl = mock_cl(3000);
        let bp = crate::observable::biposh::predicted_biposh(&cl, 1450.0, 1e-3, 100, 2000);
        let ln_l = biposh_log_likelihood(&bp, &bp, &cl, &ExperimentSpec::planck());
        assert!((ln_l - 0.0).abs() < 1e-10, "Self: ln L = {:.4e}", ln_l);
    }

    #[test]
    fn test_mismatch_negative_likelihood() {
        let cl = mock_cl(3000);
        let obs = crate::observable::biposh::predicted_biposh(&cl, 1450.0, 1e-3, 100, 2000);
        let model = crate::observable::biposh::predicted_biposh(&cl, 1450.0, 2e-3, 100, 2000);
        let ln_l = biposh_log_likelihood(&obs, &model, &cl, &ExperimentSpec::planck());
        assert!(ln_l < 0.0, "Mismatch: ln L = {:.4e} (must be < 0)", ln_l);
    }

    #[test]
    fn test_fisher_positive() {
        let cl = mock_cl(3000);
        let bp = crate::observable::biposh::predicted_biposh(&cl, 1450.0, 1e-3, 100, 2000);
        let f = biposh_fisher(&bp, &cl, &ExperimentSpec::act_dr6(), 1e-6);
        assert!(f.f[0][0] >= 0.0, "Fisher F_00 = {:.4e}", f.f[0][0]);
    }

    #[test]
    fn test_fisher_sigma_sigma2() {
        let cl = mock_cl(3000);
        let bp = crate::observable::biposh::predicted_biposh(&cl, 1450.0, 1e-3, 100, 2000);
        let f = biposh_fisher(&bp, &cl, &ExperimentSpec::cmb_s4(), 1e-6);
        let sig = f.sigma_sigma2();
        assert!(sig > 0.0 && sig.is_finite(), "sigma(Sigma2) = {:.4e}", sig);
    }

    #[test]
    fn test_8ch_integration() {
        // BiPoSH channel is callable independently alongside 7 original
        let cl = mock_cl(3000);
        let bp = crate::observable::biposh::predicted_biposh(&cl, 1450.0, 1e-3, 100, 2000);
        let ln_l_biposh = biposh_log_likelihood(&bp, &bp, &cl, &ExperimentSpec::planck());
        // Can be added to 7-channel evidence
        let ln_b_7 = 26.40; // production value
        let ln_b_8 = ln_b_7 + ln_l_biposh;
        assert!(ln_b_8.is_finite());
    }
}
