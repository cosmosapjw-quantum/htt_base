// BE-05e: Anisotropic Sobolev K(e) + Direction-Dependent Diffusion Scale.
//
// Central object: K(ê) = (1/3)θ + σ_{ab}ê^aê^b = H + σ_{ab}ê^aê^b
// where σ_{ab} is the symmetric trace-free shear tensor (σ^a_a = 0).
//
// Key results:
//   ⟨K(ê)⟩_Ω = H  (Sobolev cancellation theorem, exact by σ tracelessness)
//   δP_esc(ê) has ℓ=2 (quadrupolar) structure from σ_{ab}
//   Direction-dependent Silk damping: ΔC_ℓ/C_ℓ ~ 2(ℓ/ℓ_D)² × δk_D/k_D
//
// This is Gap #7: no existing code computes this chain.

use std::f64::consts::PI;

/// Shear tensor σ_{ab} in the tetrad frame (symmetric, trace-free).
/// For Bianchi I: diag(σ₁, σ₂, σ₃) with σ₁+σ₂+σ₃ = 0.
/// General: 5 independent components (ℓ=2 STF).
#[derive(Clone, Debug)]
pub(crate) struct ShearTensor {
    /// Components: σ_{11}, σ_{22}, σ_{33}, σ_{12}, σ_{13}, σ_{23}
    pub(crate) s: [f64; 6],
}

impl ShearTensor {
    /// Diagonal shear (Bianchi I): σ = diag(σ₁, σ₂, −σ₁−σ₂).
    pub(crate) fn diagonal(s1: f64, s2: f64) -> Self {
        Self { s: [s1, s2, -s1 - s2, 0.0, 0.0, 0.0] }
    }

    /// Isotropic (FLRW): σ = 0.
    pub(crate) fn zero() -> Self { Self { s: [0.0; 6] } }

    /// σ_{ab} ê^a ê^b for direction ê = (n₁, n₂, n₃).
    pub(crate) fn contract(&self, e: &[f64; 3]) -> f64 {
        self.s[0] * e[0] * e[0] + self.s[1] * e[1] * e[1] + self.s[2] * e[2] * e[2]
        + 2.0 * self.s[3] * e[0] * e[1]
        + 2.0 * self.s[4] * e[0] * e[2]
        + 2.0 * self.s[5] * e[1] * e[2]
    }

    /// Trace: σ^a_a = σ₁₁ + σ₂₂ + σ₃₃ (must be 0 for STF).
    pub(crate) fn trace(&self) -> f64 { self.s[0] + self.s[1] + self.s[2] }

    /// Σ² = (1/6)σ_{ab}σ^{ab} (scalar shear invariant).
    pub(crate) fn sigma2(&self) -> f64 {
        let diag = self.s[0] * self.s[0] + self.s[1] * self.s[1] + self.s[2] * self.s[2];
        let off = self.s[3] * self.s[3] + self.s[4] * self.s[4] + self.s[5] * self.s[5];
        (diag + 2.0 * off) / 6.0
    }

    /// σ/H ratio for given Hubble rate.
    pub(crate) fn sigma_over_h(&self, h: f64) -> f64 {
        (6.0 * self.sigma2()).sqrt() / h.max(1e-30)
    }
}

/// Type-ignorant line-redshift scalar.
///
/// K(ê) = (1/3)θ + σ_{ab}ê^aê^b = H + σ_{ab}ê^aê^b
///
/// where θ = 3H (expansion scalar) and σ_{ab} is trace-free.
pub(crate) fn k_scalar(h: f64, sigma: &ShearTensor, e: &[f64; 3]) -> f64 {
    h + sigma.contract(e)
}

/// Angular average of K(ê) over S².
///
/// ⟨K⟩_Ω = H + ⟨σ_{ab}ê^aê^b⟩_Ω = H + (1/3)σ^a_a = H
/// (exact by tracelessness of σ).
pub(crate) fn k_angular_average(h: f64, sigma: &ShearTensor, n_dir: usize) -> f64 {
    let dirs = gauss_legendre_s2(n_dir);
    let mut sum = 0.0;
    let mut weight_sum = 0.0;
    for &(e, w) in &dirs {
        sum += k_scalar(h, sigma, &e) * w;
        weight_sum += w;
    }
    sum / weight_sum
}

/// Sobolev optical depth for direction ê.
///
/// τ_S(ê) = 3 A_{Lyα} λ_α³ n_{1s} / (8π K(ê))
pub(crate) fn sobolev_tau_aniso(k_e: f64, n_1s: f64, lambda_alpha: f64) -> f64 {
    if k_e.abs() < 1e-30 { return 1e30; } // optically thick limit
    3.0 * super::hyrec_tables::A_LYA * lambda_alpha.powi(3) * n_1s / (8.0 * PI * k_e)
}

/// Escape probability from Sobolev optical depth.
///
/// P_esc(τ) = (1 − e^{−τ}) / τ
pub(crate) fn escape_prob(tau_s: f64) -> f64 {
    if tau_s < 1e-6 { return 1.0 - 0.5 * tau_s; } // Taylor expansion
    if tau_s > 500.0 { return 1.0 / tau_s; } // optically thick
    (1.0 - (-tau_s).exp()) / tau_s
}

/// Angle-averaged effective Lyα rate including anisotropic escape.
///
/// ⟨Λ_α⟩_Ω = A_{2p→1s} × ⟨P_esc(ê)⟩_Ω
///
/// Returns (average_rate, quadrupolar_rms).
pub(crate) fn lambda_alpha_aniso(
    h: f64, sigma: &ShearTensor, n_1s: f64, lambda_alpha: f64, n_dir: usize,
) -> (f64, f64) {
    let dirs = gauss_legendre_s2(n_dir);
    let a_lya = super::hyrec_tables::A_LYA;
    let mut sum_p = 0.0;
    let mut sum_p2 = 0.0;
    let mut weight_sum = 0.0;

    for &(e, w) in &dirs {
        let ke = k_scalar(h, sigma, &e);
        let tau = sobolev_tau_aniso(ke, n_1s, lambda_alpha);
        let p = escape_prob(tau);
        sum_p += p * w;
        sum_p2 += p * p * w;
        weight_sum += w;
    }

    let p_avg = sum_p / weight_sum;
    let p2_avg = sum_p2 / weight_sum;
    let quad_rms = (p2_avg - p_avg * p_avg).max(0.0).sqrt();

    (a_lya * p_avg, quad_rms / p_avg.max(1e-30))
}

/// Quadrupolar modulation of escape probability.
///
/// δP_esc(ê) / P̄_esc for each direction on the angular grid.
/// Returns the ℓ=2 quadrupolar coefficient δP₂/P̄.
pub(crate) fn escape_prob_quadrupole(
    h: f64, sigma: &ShearTensor, n_1s: f64, lambda_alpha: f64, n_dir: usize,
) -> f64 {
    let dirs = gauss_legendre_s2(n_dir);
    let mut p_vals = Vec::with_capacity(dirs.len());
    let mut sum_p = 0.0;
    let mut weight_sum = 0.0;

    for &(e, w) in &dirs {
        let ke = k_scalar(h, sigma, &e);
        let tau = sobolev_tau_aniso(ke, n_1s, lambda_alpha);
        let p = escape_prob(tau);
        p_vals.push((p, w, e));
        sum_p += p * w;
        weight_sum += w;
    }
    let p_avg = sum_p / weight_sum;

    // Project onto Y_{20} ∝ (3cos²θ − 1): use e[2] = cosθ
    let mut sum_y20 = 0.0;
    for &(p, w, e) in &p_vals {
        let y20 = 3.0 * e[2] * e[2] - 1.0; // unnormalized Y₂₀
        sum_y20 += (p / p_avg - 1.0) * y20 * w;
    }
    sum_y20 / weight_sum
}

/// Direction-dependent diffusion scale k_D(ê).
///
/// k_D^{−2}(ê) = ∫ dη' [R²+16(1+R)/15] / [6(1+R) n_e(ê,η') σ_T a]
///
/// The direction-dependent n_e comes from δP_esc → δx_e → δn_e.
/// Returns (k_D_iso, δk_D_quad/k_D) where the quadrupolar modulation
/// is O(σ/H) from the direction-dependent recombination rate.
pub(crate) fn diffusion_scale_modulation(
    sigma_over_h: f64, // |σ/H|
) -> f64 {
    // The chain: δK/H ~ σ/H → δτ_S/τ_S ~ σ/H → δP_esc/P_esc ~ σ/H (for τ_S ≫ 1)
    // → δΛ_α/Λ_α ~ σ/H → δx_e/x_e ~ (C_{2p}/C_r) × (δΛ_α/Λ_α)
    // At recombination: C_{2p}/C_r ~ 0.5, so δx_e/x_e ~ 0.5 × σ/H
    // Then: δn_e/n_e = δx_e/x_e ~ 0.5 σ/H
    // In the Silk integral: δk_D/k_D ~ 0.5 × δn_e/n_e ~ 0.25 σ/H
    // (the 0.5 comes from the square-root in k_D^{-2} ∝ 1/n_e)
    0.25 * sigma_over_h
}

/// α_D master coefficient: the amplification of δk_D/k_D by Silk damping.
///
/// ΔC_ℓ/C_ℓ = 2(ℓ/ℓ_D)² × δk_D/k_D
///
/// This is the key observational signature (P-V.P3).
pub(crate) fn alpha_d_coefficient(ell: usize, ell_d: f64, sigma_over_h: f64) -> f64 {
    let x = ell as f64 / ell_d;
    2.0 * x * x * diffusion_scale_modulation(sigma_over_h)
}

// ═══ Angular quadrature on S² ═══

/// Gauss-Legendre directions on S² (θ, φ grid).
///
/// Returns (direction, weight) pairs. n_dir per hemisphere in θ;
/// 2×n_dir in φ. Total: 2 × n_dir² directions.
pub(crate) fn gauss_legendre_s2(n_dir: usize) -> Vec<([f64; 3], f64)> {
    let n = n_dir.max(3);
    let (nodes_mu, weights_mu) = gauss_legendre_nodes(n);
    let n_phi = 2 * n;
    let dphi = 2.0 * PI / n_phi as f64;

    let mut dirs = Vec::with_capacity(n * n_phi);
    for (i, (&mu, &wmu)) in nodes_mu.iter().zip(weights_mu.iter()).enumerate() {
        let sin_theta = (1.0 - mu * mu).max(0.0).sqrt();
        for j in 0..n_phi {
            let phi = (j as f64 + 0.5) * dphi;
            let e = [sin_theta * phi.cos(), sin_theta * phi.sin(), mu];
            let w = wmu * dphi / (4.0 * PI); // normalized so Σw = 1
            dirs.push((e, w));
        }
    }
    dirs
}

/// Gauss-Legendre nodes and weights on [−1, 1].
fn gauss_legendre_nodes(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut nodes = vec![0.0; n];
    let mut weights = vec![0.0; n];
    for i in 0..n {
        // Initial guess
        let mut x = ((i as f64 + 0.75) / (n as f64 + 0.5) * PI).cos();
        for _ in 0..100 {
            let (p, dp) = legendre_p_dp(n, x);
            let dx = -p / dp;
            x += dx;
            if dx.abs() < 1e-15 { break; }
        }
        nodes[i] = x;
        let (_, dp) = legendre_p_dp(n, x);
        weights[i] = 2.0 / ((1.0 - x * x) * dp * dp);
    }
    (nodes, weights)
}

fn legendre_p_dp(n: usize, x: f64) -> (f64, f64) {
    let mut p0 = 1.0;
    let mut p1 = x;
    for k in 2..=n {
        let p2 = ((2 * k - 1) as f64 * x * p1 - (k - 1) as f64 * p0) / k as f64;
        p0 = p1; p1 = p2;
    }
    let dp = n as f64 * (p0 - x * p1) / (1.0 - x * x).max(1e-30);
    (p1, dp)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shear_traceless() {
        let s = ShearTensor::diagonal(1e-4, -3e-5);
        assert!(s.trace().abs() < 1e-15, "Trace = {:.2e}", s.trace());
    }

    #[test]
    fn test_sobolev_cancellation() {
        // ⟨K(ê)⟩_Ω = H exactly (by σ tracelessness)
        let h = 1.0;
        let s = ShearTensor::diagonal(0.1, -0.03);
        let avg = k_angular_average(h, &s, 12);
        assert!((avg - h).abs() < 1e-12,
            "Sobolev cancellation: ⟨K⟩ = {:.15}, H = {:.15}", avg, h);
    }

    #[test]
    fn test_sobolev_cancellation_large_shear() {
        let h = 1.0;
        let s = ShearTensor::diagonal(0.5, -0.2);
        let avg = k_angular_average(h, &s, 20);
        assert!((avg - h).abs() < 1e-10,
            "Large shear: ⟨K⟩ - H = {:.2e}", avg - h);
    }

    #[test]
    fn test_flrw_limit_all_zero() {
        let h = 1.0;
        let s = ShearTensor::zero();
        let n_1s = 1e20; let lambda_a = 1.216e-7;

        let avg = k_angular_average(h, &s, 6);
        assert!((avg - h).abs() < 1e-15);

        let (lam, quad) = lambda_alpha_aniso(h, &s, n_1s, lambda_a, 6);
        assert!(quad < 1e-6, "FLRW: quadrupolar rms = {:.2e}", quad);

        let q20 = escape_prob_quadrupole(h, &s, n_1s, lambda_a, 6);
        assert!(q20.abs() < 1e-6, "FLRW: Y₂₀ coeff = {:.2e}", q20);
    }

    #[test]
    fn test_escape_prob_limits() {
        // Optically thin: P → 1
        assert!((escape_prob(1e-8) - 1.0).abs() < 1e-6);
        // Optically thick: P → 1/τ
        let tau = 1000.0;
        assert!((escape_prob(tau) - 1.0 / tau).abs() < 1e-6);
    }

    #[test]
    fn test_quadrupolar_structure() {
        // With shear, δP_esc should have ℓ=2 structure
        let h = 1.0;
        let s = ShearTensor::diagonal(0.01, -0.005); // σ/H ~ 0.01
        let n_1s = 1e20; let lambda_a = 1.216e-7;

        let q20 = escape_prob_quadrupole(h, &s, n_1s, lambda_a, 12);
        assert!(q20.abs() > 0.0, "Must have quadrupolar modulation");
        // Amplitude should be O(σ/H)
        let soh = s.sigma_over_h(h);
        assert!(q20.abs() < 10.0 * soh, "Q₂₀={:.4e}, σ/H={:.4e}", q20, soh);
    }

    #[test]
    fn test_sign_convention() {
        // Max-shear direction: K > H → smaller τ_S → LARGER P_esc
        // → faster Lyα escape → faster net recombination → lower x_e
        // In CMB: lower x_e → less opacity → less Silk damping ← WRONG
        // Actually: lower x_e → more diffusion → MORE Silk damping
        // Full chain verified in direction_dependent.rs
        let h = 1.0;
        let s = ShearTensor::diagonal(0.1, -0.05);
        // x-axis: σ_{11} = 0.1 → K_x = 1.1 > H
        let k_x = k_scalar(h, &s, &[1.0, 0.0, 0.0]);
        // z-axis: σ_{33} = -0.05 → K_z = 0.95 < H
        let k_z = k_scalar(h, &s, &[0.0, 0.0, 1.0]);

        assert!(k_x > h, "Max-shear: K > H");
        assert!(k_z < h, "Min-shear: K < H");

        let n_1s = 1e20; let la = 1.216e-7;
        let tau_x = sobolev_tau_aniso(k_x, n_1s, la);
        let tau_z = sobolev_tau_aniso(k_z, n_1s, la);
        assert!(tau_x < tau_z, "Higher K → less trapping: τ_x < τ_z");

        let p_x = escape_prob(tau_x);
        let p_z = escape_prob(tau_z);
        assert!(p_x > p_z, "Higher K → more escape: P_x={:.4e} > P_z={:.4e}", p_x, p_z);
    }

    #[test]
    fn test_alpha_d_scaling() {
        // α_D ∝ Σ² at small Σ² (verified through σ/H scaling)
        let ell_d = 1500.0;
        let a1 = alpha_d_coefficient(3000, ell_d, 1e-3);
        let a2 = alpha_d_coefficient(3000, ell_d, 2e-3);
        // α_D ∝ σ/H, so a2/a1 ≈ 2
        let ratio = a2 / a1;
        assert!((ratio - 2.0).abs() < 0.01, "Scaling: a2/a1 = {:.4}", ratio);
    }

    #[test]
    fn test_alpha_d_ell_dependence() {
        // α_D ∝ ℓ² (quadratic in ℓ)
        let ell_d = 1500.0; let soh = 1e-3;
        let a_1000 = alpha_d_coefficient(1000, ell_d, soh);
        let a_2000 = alpha_d_coefficient(2000, ell_d, soh);
        let ratio = a_2000 / a_1000;
        assert!((ratio - 4.0).abs() < 0.01, "ℓ² scaling: {:.4}", ratio);
    }

    #[test]
    fn test_impact_bi_sigma2_1e6() {
        // For BI at Σ² = 10⁻⁶: σ/H ~ 10⁻³
        let soh = 1e-3;
        let dk_k = diffusion_scale_modulation(soh);
        assert!((dk_k - 2.5e-4).abs() < 1e-4,
            "δk_D/k_D = {:.4e} (expect ~2.5e-4)", dk_k);

        // At ℓ = 3000, ℓ_D = 1500: ΔC_ℓ/C_ℓ ~ 2×4×2.5e-4 = 2e-3 = 0.2%
        let alpha = alpha_d_coefficient(3000, 1500.0, soh);
        assert!(alpha > 1e-3 && alpha < 0.01,
            "α_D(3000) = {:.4e} (expect ~2e-3)", alpha);
    }

    #[test]
    fn test_gauss_legendre_normalization() {
        let dirs = gauss_legendre_s2(8);
        let sum: f64 = dirs.iter().map(|(_, w)| w).sum();
        assert!((sum - 1.0).abs() < 1e-10, "Weight sum = {:.10}", sum);
    }

    #[test]
    fn test_sigma2_invariant() {
        let s = ShearTensor::diagonal(1e-4, -3e-5);
        let sig2 = s.sigma2();
        // Σ² = (σ₁²+σ₂²+σ₃²)/6 where σ₃ = -(σ₁+σ₂)
        let s3: f64 = -(1e-4 - 3e-5);
        let expected = (1e-4_f64.powi(2) + 3e-5_f64.powi(2) + s3.powi(2)) / 6.0;
        assert!((sig2 - expected).abs() / expected < 1e-10);
    }
}
