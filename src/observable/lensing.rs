// BE-08: Isotropic CMB Lensing.
//
// C_ℓ^{φφ} from Limber approximation:
//   C_ℓ^{φφ} = (8π²/ℓ³) ∫ dη W²(η)/η² P_Φ(k=ℓ/η, η)
//
// Lensing convolution (leading-order series):
//   C̃_ℓ ≈ C_ℓ [1 − ℓ(ℓ+1)R_φ] + power redistribution
//   R_φ = Σ_L (2L+1)L(L+1)C_L^{φφ}/(4π)

use std::f64::consts::PI;

/// Lensing kernel W^κ(η) = (η₀ − η)η / η₀  (flat geometry).
pub(crate) fn lensing_kernel_flat(eta: f64, eta_0: f64) -> f64 {
    if eta <= 0.0 || eta >= eta_0 { return 0.0; }
    (eta_0 - eta) * eta / eta_0
}

/// Matter power spectrum P_Φ(k, η) = (3Ω_m H₀²/(2k²))² P_R(k) T²(k) D²(η)/a².
///
/// Simplified: use BBKS transfer function T(k).
fn matter_power_phi(k: f64, d_eta: f64, a: f64, a_s: f64, n_s: f64, k_pivot: f64,
                     omega_m: f64, h0: f64) -> f64 {
    if k < 1e-10 { return 0.0; }
    // Primordial: P_R(k) = (2π²/k³) A_s (k/k_piv)^{n_s−1}
    let p_r = 2.0 * PI * PI / k.powi(3) * a_s * (k / k_pivot).powf(n_s - 1.0);
    // Transfer: BBKS T(k) (approximate)
    let q = k / (omega_m * (h0 / (100.0e3 / 3.086e22))); // k in h/Mpc equivalent
    let t_k = (1.0 + 3.89 * q + (16.1 * q).powi(2) + (5.46 * q).powi(3) + (6.71 * q).powi(4))
        .powf(-0.25);
    // Poisson: Φ = (3/2)(Ω_m H₀²/k²) δ/a
    let poisson = 1.5 * omega_m * h0 * h0 / (k * k);
    poisson * poisson * p_r * t_k * t_k * d_eta * d_eta / (a * a).max(1e-30)
}

/// Compute isotropic C_ℓ^{φφ} via Limber approximation.
///
/// C_ℓ^{φφ} = (2/π) ∫₀^{η₀} dη W²(η) P_Φ(k=ν/η, η) / η²
/// where ν = ℓ + 1/2.
pub(crate) fn compute_cl_phiphi(
    ell_max: usize,
    eta_0: f64,
    a_s: f64, n_s: f64, k_pivot: f64,
    omega_m: f64, h0: f64,
    growth: &super::growth::GrowthFunction,
) -> Vec<f64> {
    let mut cl = vec![0.0; ell_max + 1];

    // η integration grid
    let n_eta = 200;
    let eta_min = eta_0 * 0.01; // skip very early (kernel ~ 0)

    for ell in 2..=ell_max {
        let nu = ell as f64 + 0.5;
        let mut sum = 0.0;

        for i in 0..n_eta {
            let f = (i as f64 + 0.5) / n_eta as f64;
            let eta = eta_min + f * (eta_0 - eta_min);
            let w = lensing_kernel_flat(eta, eta_0);
            let k = nu / eta.max(1.0);
            let d = growth.eval(eta);
            // a(η) approximation: a ~ (η/η₀)² in matter era, saturates at 1
            let a = (eta / eta_0).powi(2).min(1.0).max(1e-6);
            let p_phi = matter_power_phi(k, d, a, a_s, n_s, k_pivot, omega_m, h0);

            let deta = (eta_0 - eta_min) / n_eta as f64;
            sum += w * w * p_phi / (eta * eta).max(1e-30) * deta;
        }

        cl[ell] = 2.0 / PI * sum;
    }
    cl
}

/// Lensing deflection power R_φ.
///
/// R_φ = (1/4π) Σ_L (2L+1) L(L+1) C_L^{φφ}
pub(crate) fn deflection_power(cl_phiphi: &[f64]) -> f64 {
    let mut r = 0.0;
    for ell in 1..cl_phiphi.len() {
        r += (2 * ell + 1) as f64 * (ell * (ell + 1)) as f64 * cl_phiphi[ell];
    }
    r / (4.0 * PI)
}

/// Apply leading-order lensing to unlensed C_ℓ.
///
/// C̃_ℓ ≈ C_ℓ × [1 − ℓ(ℓ+1) R_φ] + Σ_{ℓ'} C_{ℓ'} × lensing_coupling(ℓ, ℓ')
///
/// Simplified: use the smoothing approximation:
///   C̃_ℓ ≈ C_ℓ × [1 − ℓ(ℓ+1) R_φ] + redistribution
/// where redistribution ≈ R_φ × ℓ(ℓ+1) × C_ℓ^{smoothed}
pub(crate) fn lens_spectrum_approx(
    cl_unlensed: &[f64],
    cl_phiphi: &[f64],
) -> Vec<f64> {
    let r_phi = deflection_power(cl_phiphi);
    let n = cl_unlensed.len();
    let mut cl_lensed = vec![0.0; n];

    // Smoothed C_ℓ (5-point running average for redistribution term)
    let mut cl_smooth = cl_unlensed.to_vec();
    for ell in 3..n.saturating_sub(3) {
        cl_smooth[ell] = (cl_unlensed[ell - 2] + cl_unlensed[ell - 1]
            + cl_unlensed[ell] + cl_unlensed[ell + 1] + cl_unlensed[ell + 2]) / 5.0;
    }

    for ell in 2..n {
        let ll1 = (ell * (ell + 1)) as f64;
        // Peak smoothing: subtract from peaks
        let suppression = 1.0 - ll1 * r_phi;
        // Power redistribution: add to troughs
        let redistribution = ll1 * r_phi * cl_smooth[ell];
        cl_lensed[ell] = cl_unlensed[ell] * suppression.max(0.0) + redistribution;
        cl_lensed[ell] = cl_lensed[ell].max(0.0);
    }
    cl_lensed
}

/// B-mode power from lensing (standard formula).
///
/// C_ℓ^{BB,lens} ≈ (1/4) Σ_{ℓ'} ℓ'(ℓ'+1) C_{ℓ'}^{EE} C_{|ℓ−ℓ'|}^{φφ} × coupling
///
/// Approximate: C_ℓ^{BB} ~ R_φ × ℓ(ℓ+1) × C_ℓ^{EE} / (4π)
pub(crate) fn bb_from_lensing(cl_ee: &[f64], cl_phiphi: &[f64]) -> Vec<f64> {
    let r_phi = deflection_power(cl_phiphi);
    let n = cl_ee.len();
    let mut cl_bb = vec![0.0; n];
    for ell in 2..n {
        cl_bb[ell] = r_phi * (ell * (ell + 1)) as f64 * cl_ee[ell] / (4.0 * PI);
    }
    cl_bb
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lensing_kernel_boundary() {
        assert_eq!(lensing_kernel_flat(0.0, 14000.0), 0.0);
        assert_eq!(lensing_kernel_flat(14000.0, 14000.0), 0.0);
    }

    #[test]
    fn test_lensing_kernel_peak() {
        let eta_0 = 14000.0;
        // Peak at η = η₀/2
        let w_half = lensing_kernel_flat(eta_0 / 2.0, eta_0);
        let w_quarter = lensing_kernel_flat(eta_0 / 4.0, eta_0);
        assert!(w_half > w_quarter, "Kernel peaks near η₀/2");
        assert!((w_half - eta_0 / 4.0).abs() < 1.0, "W(η₀/2) = η₀/4");
    }

    #[test]
    fn test_cl_phiphi_positive() {
        let (eta, a) = super::super::growth::tests::make_grid_pub();
        let h0: f64 = 67.36e3 / 3.086e22;
        let g = super::super::growth::GrowthFunction::solve_flrw(h0, 0.3153, 0.6847, &eta, &a);
        let cl = compute_cl_phiphi(100, 14000.0, 2.1e-9, 0.9649, 0.05, 0.3153, h0, &g);
        for ell in 2..=100 {
            assert!(cl[ell] >= 0.0 && cl[ell].is_finite(),
                "C_{}^φφ = {:.4e}", ell, cl[ell]);
        }
    }

    #[test]
    fn test_deflection_power_positive() {
        let cl_pp = vec![0.0, 0.0, 1e-7, 5e-8, 3e-8];
        let r = deflection_power(&cl_pp);
        assert!(r > 0.0, "R_φ = {:.4e}", r);
    }

    #[test]
    fn test_lensing_preserves_positivity() {
        let cl_unl = vec![0.0, 0.0, 1000.0, 900.0, 800.0, 700.0];
        let cl_pp = vec![0.0, 0.0, 1e-7, 5e-8, 3e-8, 2e-8];
        let cl_lensed = lens_spectrum_approx(&cl_unl, &cl_pp);
        for ell in 2..6 { assert!(cl_lensed[ell] >= 0.0); }
    }

    #[test]
    fn test_bb_from_lensing_positive() {
        let cl_ee = vec![0.0, 0.0, 100.0, 80.0, 60.0];
        let cl_pp = vec![0.0, 0.0, 1e-7, 5e-8, 3e-8];
        let cl_bb = bb_from_lensing(&cl_ee, &cl_pp);
        for ell in 2..5 { assert!(cl_bb[ell] >= 0.0 && cl_bb[ell].is_finite()); }
    }
}
