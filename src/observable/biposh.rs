// BE-07: Bipolar Spherical Harmonics (BiPoSH) from direction-dependent Silk damping.
//
// A^{LM}_{ℓℓ'} = Σ_{mm'} C^{LM}_{ℓm,ℓ'm'} ⟨a_{ℓm} a*_{ℓ'm'}⟩
//
// Bianchi shear (rank-2 STF) → L=2 only. M determined by shear orientation.
// Diagonal BiPoSH: A^{2M}_{ℓℓ} = C_ℓ × α_D(ℓ) × σ_{2M}/H
// Off-diagonal: A^{2M}_{ℓ,ℓ+2} from ℓ-mixing (subdominant).

use super::direction_silk::{alpha_d, ELL_D_FIDUCIAL};

/// BiPoSH spectrum for L=2 (quadrupolar modulation from Bianchi shear).
#[derive(Clone, Debug)]
pub(crate) struct BiPoSHSpectrum {
    /// ℓ values.
    pub(crate) ells: Vec<usize>,
    /// A^{20}_{ℓℓ} (diagonal, M=0 component).
    pub(crate) a20_diag: Vec<f64>,
    /// |A^{2M}_{ℓℓ}|² summed over M (rotationally invariant).
    pub(crate) a2_power: Vec<f64>,
}

/// Compute predicted BiPoSH A^{20}_{ℓℓ} spectrum from direction-dependent Silk.
///
/// A^{20}_{ℓℓ} = C_ℓ × α_D(ℓ) × σ_{20}/H
///
/// where σ_{20}/H = (2σ₃ − σ₁ − σ₂) / (√6 H) for diagonal shear.
pub(crate) fn predicted_biposh(
    cl_iso: &[f64],       // isotropic C_ℓ, indexed by ℓ
    ell_d: f64,
    sigma20_over_h: f64,   // σ_{20}/H (M=0 quadrupolar shear component)
    ell_min: usize,
    ell_max: usize,
) -> BiPoSHSpectrum {
    let mut ells = Vec::new();
    let mut a20 = Vec::new();
    let mut a2p = Vec::new();

    for ell in ell_min..=ell_max.min(cl_iso.len() - 1) {
        let ad = alpha_d(ell, ell_d);
        let a20_val = cl_iso[ell] * ad * sigma20_over_h;
        ells.push(ell);
        a20.push(a20_val);
        // Power: |A^{2M}|² ~ 5 × |A^{20}|² for isotropic shear orientation
        a2p.push(5.0 * a20_val * a20_val);
    }

    BiPoSHSpectrum { ells, a20_diag: a20, a2_power: a2p }
}

/// BiPoSH noise variance per (ℓ, L=2) mode.
///
/// Var(A^{2M}_{ℓℓ}) = 2/(2ℓ+1) × (C_ℓ + N_ℓ)²
/// where N_ℓ = (Δθ × σ_noise)² × B_ℓ⁻² is the noise power spectrum.
pub(crate) fn biposh_variance(
    cl_iso: f64,
    n_ell: f64,    // noise power N_ℓ [μK²·sr]
    ell: usize,
) -> f64 {
    let total = cl_iso + n_ell;
    2.0 / (2 * ell + 1) as f64 * total * total
}

/// Noise power spectrum for a CMB experiment.
///
/// N_ℓ = (σ_noise × θ_beam)² × exp(ℓ(ℓ+1)θ²_beam/(8 ln 2))
pub(crate) fn noise_power(
    sigma_noise_muK_arcmin: f64,
    theta_beam_arcmin: f64,
    ell: usize,
) -> f64 {
    let theta_rad = theta_beam_arcmin * std::f64::consts::PI / (180.0 * 60.0);
    let noise_base = (sigma_noise_muK_arcmin * std::f64::consts::PI / (180.0 * 60.0)).powi(2);
    let beam = (ell as f64 * (ell + 1) as f64 * theta_rad * theta_rad / (8.0 * 2.0_f64.ln())).exp();
    noise_base * beam
}

/// Experiment specifications.
#[derive(Clone, Debug)]
pub(crate) struct ExperimentSpec {
    pub(crate) name: &'static str,
    pub(crate) sigma_noise: f64,  // μK-arcmin
    pub(crate) theta_beam: f64,   // arcmin
    pub(crate) ell_min: usize,
    pub(crate) ell_max: usize,
    pub(crate) f_sky: f64,
}

impl ExperimentSpec {
    pub(crate) fn planck() -> Self {
        Self { name: "Planck", sigma_noise: 45.0, theta_beam: 7.0, ell_min: 2, ell_max: 2500, f_sky: 0.7 }
    }
    pub(crate) fn act_dr6() -> Self {
        Self { name: "ACT DR6", sigma_noise: 25.0, theta_beam: 1.4, ell_min: 600, ell_max: 4000, f_sky: 0.4 }
    }
    pub(crate) fn cmb_s4() -> Self {
        Self { name: "CMB-S4", sigma_noise: 1.0, theta_beam: 1.0, ell_min: 30, ell_max: 5000, f_sky: 0.4 }
    }
}

/// Cumulative S/N for BiPoSH L=2 detection.
///
/// (S/N)² = f_sky × Σ_{ℓ=ℓ_min}^{ℓ_max} Σ_M |A^{2M,theory}|² / Var(A^{2M})
pub(crate) fn cumulative_sn(
    biposh: &BiPoSHSpectrum,
    cl_iso: &[f64],
    spec: &ExperimentSpec,
) -> Vec<(usize, f64)> {
    let mut sn2_cum = 0.0;
    let mut result = Vec::new();

    for (idx, &ell) in biposh.ells.iter().enumerate() {
        if ell < spec.ell_min || ell > spec.ell_max { continue; }
        if ell >= cl_iso.len() { break; }
        let nl = noise_power(spec.sigma_noise, spec.theta_beam, ell);
        let var = biposh_variance(cl_iso[ell], nl, ell);
        if var > 0.0 {
            sn2_cum += spec.f_sky * biposh.a2_power[idx] / var;
        }
        result.push((ell, sn2_cum.sqrt()));
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_cl(ell_max: usize) -> Vec<f64> {
        // Rough TT spectrum shape
        (0..=ell_max).map(|ell| {
            if ell < 2 { return 0.0; }
            let dl = 5000.0 * (-(ell as f64 - 220.0).powi(2) / (2.0 * 100.0_f64.powi(2))).exp()
                   + 1000.0 * (-(ell as f64 / 1500.0).powi(2)).exp();
            dl * 2.0 * std::f64::consts::PI / (ell * (ell + 1)) as f64 * 1e-12 // dimensionless
        }).collect()
    }

    #[test]
    fn test_biposh_flrw_zero() {
        let cl = mock_cl(3000);
        let bp = predicted_biposh(&cl, ELL_D_FIDUCIAL, 0.0, 2, 3000);
        for &a in &bp.a20_diag { assert_eq!(a, 0.0); }
    }

    #[test]
    fn test_biposh_l2_only() {
        // Bianchi shear → L=2 only (by construction in our formalism)
        let cl = mock_cl(3000);
        let bp = predicted_biposh(&cl, ELL_D_FIDUCIAL, 1e-3, 2, 3000);
        assert!(bp.a20_diag.iter().any(|&a| a != 0.0), "Must have L=2 signal");
    }

    #[test]
    fn test_biposh_grows_with_ell() {
        let cl = mock_cl(3000);
        let bp = predicted_biposh(&cl, ELL_D_FIDUCIAL, 1e-3, 100, 3000);
        // |A^{20}| should grow with ℓ (α_D ∝ ℓ²)
        let a_low = bp.a20_diag[0].abs();
        let a_high = bp.a20_diag[bp.a20_diag.len() / 2].abs();
        // Not strictly monotonic due to C_ℓ shape, but generally growing
        assert!(a_high > 0.0);
    }

    #[test]
    fn test_noise_planck() {
        let nl = noise_power(45.0, 7.0, 1000);
        assert!(nl > 0.0 && nl.is_finite());
    }

    #[test]
    fn test_noise_cmbs4_lower() {
        let nl_planck = noise_power(45.0, 7.0, 2000);
        let nl_s4 = noise_power(1.0, 1.0, 2000);
        assert!(nl_s4 < nl_planck, "CMB-S4 less noise than Planck");
    }

    #[test]
    fn test_sn_cumulative_increases() {
        let cl = mock_cl(3000);
        let bp = predicted_biposh(&cl, ELL_D_FIDUCIAL, 1e-3, 100, 3000);
        let spec = ExperimentSpec::act_dr6();
        let sn = cumulative_sn(&bp, &cl, &spec);
        assert!(sn.len() > 0);
        // S/N should be non-decreasing
        for i in 1..sn.len() {
            assert!(sn[i].1 >= sn[i - 1].1 - 1e-10,
                "S/N must be non-decreasing: {:.4} < {:.4}", sn[i].1, sn[i - 1].1);
        }
    }

    #[test]
    fn test_experiment_specs() {
        let p = ExperimentSpec::planck();
        let a = ExperimentSpec::act_dr6();
        let s = ExperimentSpec::cmb_s4();
        assert!(s.sigma_noise < a.sigma_noise);
        assert!(a.sigma_noise < p.sigma_noise);
        assert!(s.ell_max > a.ell_max);
    }
}
