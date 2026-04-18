// Bianchi background evolution: Hubble, shear, conformal time.
// BB-02: Type-ignorant ODE with type-specific curvature source.
//
// Physics: dΣ/dN = -(2-q)Σ + S(type), N = ln a
// q = Ω_r + Ω_m/2 - Ω_Λ + 2Σ² (deceleration parameter)
// BI: S = 0. Curved types: S from ³R_{⟨ab⟩} via structure constants.

use crate::core::math::{natural_cubic_second_derivatives, cubic_spline_eval};
use super::types::*;

/// Cosmological parameters for background evolution.
#[derive(Clone, Debug)]
pub(crate) struct CosmologyParams {
    pub(crate) h0_si: f64,       // H₀ [s⁻¹]
    pub(crate) h0_mpc: f64,      // H₀ [km/s/Mpc] converted to [Mpc⁻¹]
    pub(crate) omega_r: f64,     // Ω_r (radiation)
    pub(crate) omega_m: f64,     // Ω_m (matter)
    pub(crate) omega_lambda: f64,// Ω_Λ
    pub(crate) omega_k: f64,     // Ω_k (spatial curvature, type-dependent)
}

impl CosmologyParams {
    /// Standard ΛCDM-like cosmology.
    pub(crate) fn standard(h0_km_s_mpc: f64, omega_r: f64, omega_m: f64, omega_lambda: f64) -> Self {
        let h0_si = h0_km_s_mpc * 1e3 / 3.085677581e22; // km/s/Mpc → s⁻¹
        let h0_mpc = h0_km_s_mpc / 299792.458;           // → Mpc⁻¹
        let omega_k = 1.0 - omega_r - omega_m - omega_lambda;
        Self { h0_si, h0_mpc, omega_r, omega_m, omega_lambda, omega_k }
    }

    /// Hubble parameter H(a) from the Friedmann equation (neglecting σ² backreaction).
    pub(crate) fn hubble_of_a(&self, a: f64) -> f64 {
        let a2 = a * a;
        let e2 = self.omega_r / (a2 * a2)
               + self.omega_m / (a2 * a)
               + self.omega_lambda
               + self.omega_k / a2;
        self.h0_si * e2.max(1e-300).sqrt()
    }

    /// Dimensionless E²(a) = H²(a)/H₀².
    pub(crate) fn e2_of_a(&self, a: f64) -> f64 {
        let a2 = a * a;
        (self.omega_r / (a2 * a2)
       + self.omega_m / (a2 * a)
       + self.omega_lambda
       + self.omega_k / a2).max(1e-300)
    }

    /// Deceleration parameter q(a) = Ω_r(a) + Ω_m(a)/2 − Ω_Λ(a) + 2Σ².
    /// For Σ ≪ 1 the last term is negligible.
    pub(crate) fn deceleration_of_a(&self, a: f64, sigma_sq: f64) -> f64 {
        let e2 = self.e2_of_a(a);
        let a2 = a * a;
        let omega_r_a = self.omega_r / (a2 * a2) / e2;
        let omega_m_a = self.omega_m / (a2 * a) / e2;
        let omega_l_a = self.omega_lambda / e2;
        omega_r_a + 0.5 * omega_m_a - omega_l_a + 2.0 * sigma_sq
    }
}

/// Result of background evolution.
pub(crate) struct BianchiBackground {
    /// Scale factor grid (strictly increasing).
    pub(crate) a_grid: Vec<f64>,
    /// Conformal time grid η(a), strictly increasing.
    pub(crate) eta_grid: Vec<f64>,
    /// Hubble parameter H(a) [s⁻¹].
    pub(crate) h_grid: Vec<f64>,
    /// Dimensionless shear ratio σ/H(a) = √6 Σ(a).
    pub(crate) sigma_h_grid: Vec<f64>,
    /// Friedmann constraint violation: |1 − Σ² − Ω_r − Ω_m − Ω_Λ − Ω_k|.
    pub(crate) constraint_grid: Vec<f64>,
    /// Spline data for η(a) interpolation.
    eta_y2: Vec<f64>,
    /// Spline data for σ/H(a) interpolation.
    sigma_h_y2: Vec<f64>,
}

impl BianchiBackground {
    /// Interpolate σ/H at arbitrary scale factor.
    pub(crate) fn sigma_h_of_a(&self, a: f64) -> f64 {
        cubic_spline_eval(&self.a_grid, &self.sigma_h_grid, &self.sigma_h_y2, a)
    }

    /// Interpolate η at arbitrary scale factor.
    pub(crate) fn eta_of_a(&self, a: f64) -> f64 {
        cubic_spline_eval(&self.a_grid, &self.eta_grid, &self.eta_y2, a)
    }

    /// Maximum Friedmann constraint violation across grid.
    pub(crate) fn max_constraint_violation(&self) -> f64 {
        self.constraint_grid.iter().fold(0.0f64, |m, &c| m.max(c))
    }
}

/// Type-specific shear source S(type, a, Σ, cosmo).
///
/// Wainwright-Ellis curvature source for the scalar shear Σ:
///   S_curv = −³S_{33} × Ω_k(a) / ³R_canonical
///
/// where ³S, ³R are from the canonical (n,a) parameters (BB-03)
/// and Ω_k(a) = Ω_{k,0}/(a² E²(a)).
///
/// Types with isotropic curvature (³S = 0): S = 0. These are:
///   BI (n=0,a=0), BII (n=(1,0,0),a=0), BIV (n=(1,0,0),a=1),
///   BV (n=0,a≠0), BIX (n=(1,1,1),a=0).
///
/// Types with anisotropic curvature (³S ≠ 0): S ≠ 0. These are:
///   BIII, BVI₀, BVII₀, BVIII, BVI_h, BVII_h.
fn shear_source(
    params: &BianchiParams,
    cosmo: &CosmologyParams,
    a: f64,
    _sigma: f64,
) -> f64 {
    let n = &params.n_eigenvalues;
    let a_mag = params.a_magnitude;

    // Canonical curvature quantities (algebraic, from BB-03)
    let r3_can = super::curvature::spatial_ricci_scalar(n, a_mag);
    let s_can = super::curvature::spatial_ricci_tracefree(n, a_mag);

    // If ³R_canonical = 0, the curvature scale is undefined but ³S = 0 too.
    if r3_can.abs() < 1e-30 {
        return 0.0;
    }

    // If ³S = 0 (isotropic curvature), no anisotropic source.
    let s_norm2 = s_can[0]*s_can[0] + s_can[1]*s_can[1] + s_can[2]*s_can[2];
    if s_norm2 < 1e-30 {
        return 0.0;
    }

    // Ω_k(a) = Ω_{k,0} / (a² E²(a))
    let a2 = a * a;
    let e2 = cosmo.e2_of_a(a);
    let omega_k_a = cosmo.omega_k / (a2 * e2);

    // Scalar curvature source (projection along 3rd axis for LRS):
    //   S = −³S_{33,can} × Ω_k(a) / ³R_can
    -s_can[2] * omega_k_a / r3_can
}

/// Evolve the Bianchi background from a_min to a_max = 1.
///
/// Uses N = ln(a) as integration variable with RK4 for the shear ODE:
///   dΣ/dN = -(2-q)Σ + S(type)
///
/// Then integrates η(a) = ∫ da/(a²H) by trapezoidal rule.
pub(crate) fn evolve(
    params: &BianchiParams,
    cosmo: &CosmologyParams,
    sigma_h_init: f64,   // σ/H at a = a_min
    a_min: f64,
    n_points: usize,
) -> Result<BianchiBackground, String> {
    if n_points < 10 {
        return Err("n_points must be ≥ 10".into());
    }
    if a_min <= 0.0 || a_min >= 1.0 {
        return Err(format!("a_min must be in (0, 1), got {}", a_min));
    }

    // Build uniform grid in ln(a) from ln(a_min) to 0
    let ln_a_min = a_min.ln();
    let ln_a_max = 0.0_f64; // a = 1 today
    let d_ln_a = (ln_a_max - ln_a_min) / (n_points as f64 - 1.0);

    let mut a_grid = Vec::with_capacity(n_points);
    let mut h_grid = Vec::with_capacity(n_points);
    let mut sigma_h_grid = Vec::with_capacity(n_points);
    let mut constraint_grid = Vec::with_capacity(n_points);

    // Initial condition: Σ₀ = (σ/H)₀ / √6
    let sigma_init = sigma_h_init / 6.0_f64.sqrt();

    // RK4 integration of dΣ/dN = -(2-q)Σ + S
    let mut sigma_cur = sigma_init;

    for i in 0..n_points {
        let ln_a = ln_a_min + i as f64 * d_ln_a;
        let a = ln_a.exp();
        let h = cosmo.hubble_of_a(a);
        let sigma_sq = sigma_cur * sigma_cur;
        let sigma_h = sigma_cur * 6.0_f64.sqrt();

        // Friedmann constraint: 1 = Σ² + Ω_r + Ω_m + Ω_Λ + Ω_k
        let e2 = cosmo.e2_of_a(a);
        let a2 = a * a;
        let omega_r_a = cosmo.omega_r / (a2 * a2) / e2;
        let omega_m_a = cosmo.omega_m / (a2 * a) / e2;
        let omega_l_a = cosmo.omega_lambda / e2;
        let omega_k_a = cosmo.omega_k / a2 / e2;
        let constraint = (1.0 - sigma_sq - omega_r_a - omega_m_a - omega_l_a - omega_k_a).abs();

        a_grid.push(a);
        h_grid.push(h);
        sigma_h_grid.push(sigma_h);
        constraint_grid.push(constraint);

        // RK4 step for Σ evolution (skip last point)
        if i < n_points - 1 {
            let rhs = |a_val: f64, sig: f64| -> f64 {
                let sig_sq = sig * sig;
                let q = cosmo.deceleration_of_a(a_val, sig_sq);
                let source = shear_source(params, cosmo, a_val, sig);
                -(2.0 - q) * sig + source
            };

            let h_step = d_ln_a;
            let k1 = rhs(a, sigma_cur);
            let a_mid = (ln_a + 0.5 * h_step).exp();
            let k2 = rhs(a_mid, sigma_cur + 0.5 * h_step * k1);
            let k3 = rhs(a_mid, sigma_cur + 0.5 * h_step * k2);
            let a_next = (ln_a + h_step).exp();
            let k4 = rhs(a_next, sigma_cur + h_step * k3);
            sigma_cur += h_step * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0;
        }
    }

    // Integrate conformal time: η(a) = ∫ da/(a²H)
    // Using trapezoidal rule on the ln(a) grid:
    //   dη = da/(a²H) = d(ln a)/(aH)
    let mut eta_grid = Vec::with_capacity(n_points);
    let mut eta_acc = 0.0;
    eta_grid.push(eta_acc);
    for i in 1..n_points {
        let integrand_prev = 1.0 / (a_grid[i - 1] * h_grid[i - 1] / cosmo.h0_si * cosmo.h0_mpc);
        let integrand_cur = 1.0 / (a_grid[i] * h_grid[i] / cosmo.h0_si * cosmo.h0_mpc);
        // Convert H from SI to Mpc⁻¹ units: H_mpc = H_si / (c/Mpc) → dη in Mpc
        // Actually: dη = d(ln a) × c/(aH) in comoving Mpc
        // c/(aH) where H in s⁻¹: c/(aH) in meters, divide by Mpc → Mpc
        let c_over_ah_prev = 299792.458 / (a_grid[i - 1] * h_grid[i - 1] / cosmo.h0_si * cosmo.h0_mpc).max(1e-300);
        let c_over_ah_cur = 299792.458 / (a_grid[i] * h_grid[i] / cosmo.h0_si * cosmo.h0_mpc).max(1e-300);
        // Simpler: use H in Mpc⁻¹ units directly
        // H_mpc_inv = H_si × Mpc / c = (h0_si × E) × Mpc/c
        // But we have h0_mpc = h0_km_s_mpc / c_km_s. And H(a) = h0_si × E(a).
        // In Mpc: dη = da/(a²H_Mpc) where H_Mpc = h0_mpc × E(a)
        let h_mpc_prev = cosmo.h0_mpc * cosmo.e2_of_a(a_grid[i - 1]).sqrt();
        let h_mpc_cur = cosmo.h0_mpc * cosmo.e2_of_a(a_grid[i]).sqrt();
        let f_prev = 1.0 / (a_grid[i - 1] * h_mpc_prev).max(1e-300);
        let f_cur = 1.0 / (a_grid[i] * h_mpc_cur).max(1e-300);
        eta_acc += 0.5 * (f_prev + f_cur) * d_ln_a;
        eta_grid.push(eta_acc);
    }

    // Build splines
    let eta_y2 = natural_cubic_second_derivatives(&a_grid, &eta_grid)
        .map_err(|e| format!("eta spline: {}", e))?;
    let sigma_h_y2 = natural_cubic_second_derivatives(&a_grid, &sigma_h_grid)
        .map_err(|e| format!("sigma_h spline: {}", e))?;

    Ok(BianchiBackground {
        a_grid, eta_grid, h_grid, sigma_h_grid, constraint_grid,
        eta_y2, sigma_h_y2,
    })
}

/// The type-ignorant redshift scalar K = (1/3)θ + σ_{ab}e^a e^b.
///
/// For an observer comoving with the Hubble flow along direction ê:
///   K = H + σ_{ab} ê^a ê^b
/// In the isotropic limit, K = H. With shear, K is direction-dependent.
pub(crate) fn redshift_scalar(h: f64, sigma_h: f64, cos_theta: f64) -> f64 {
    // For axisymmetric shear (BI), σ_{ab} ê^a ê^b = σ_+ (3cos²θ − 1)/2
    // With σ_+ ≈ (2/3) × σ, and σ/H known:
    // K ≈ H [1 + (σ/H) × (3cos²θ − 1)/3]
    let p2 = 0.5 * (3.0 * cos_theta * cos_theta - 1.0);
    h * (1.0 + (2.0 / 3.0) * sigma_h * p2)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn standard_cosmo() -> CosmologyParams {
        // Planck 2018-like
        CosmologyParams::standard(67.36, 9.14e-5, 0.3153, 0.6847)
    }

    #[test]
    fn test_flrw_limit() {
        let cosmo = standard_cosmo();
        let params = BianchiType::I.canonical_params();
        let bg = evolve(&params, &cosmo, 0.0, 1e-4, 5000).unwrap();
        // σ/H = 0 throughout (FLRW)
        for &sh in &bg.sigma_h_grid {
            assert!(sh.abs() < 1e-14, "FLRW: σ/H = {:.2e} (want 0)", sh);
        }
        // H(a=1) = H₀
        let h_today = *bg.h_grid.last().unwrap();
        let rel = (h_today - cosmo.h0_si).abs() / cosmo.h0_si;
        assert!(rel < 1e-6, "H(a=1) off by {:.2e}", rel);
    }

    #[test]
    fn test_bi_shear_decay() {
        let cosmo = standard_cosmo();
        let params = BianchiType::I.canonical_params();
        let sigma_h_init = 1e-4; // small σ/H at a_min
        let bg = evolve(&params, &cosmo, sigma_h_init, 1e-4, 10000).unwrap();

        // σ/H should decay from a_min to a=1
        let sh_init = bg.sigma_h_grid[0];
        let sh_final = *bg.sigma_h_grid.last().unwrap();
        assert!(sh_final < sh_init, "Shear should decay: {:.2e} → {:.2e}", sh_init, sh_final);

        // Find σ/H at a_rec ≈ 1/1091
        let a_rec = 1.0 / 1091.0;
        let sh_rec = bg.sigma_h_of_a(a_rec);
        let sh_today = bg.sigma_h_of_a(1.0);
        let ratio = sh_today / sh_rec;

        // The physical scaling is between a⁻¹ (rad) and a⁻³/² (mat).
        // From a_rec to a=1 (mostly matter era): ratio ≈ (a_rec)^{3/2} ≈ 3×10⁻⁵
        // Allow generous tolerance for the transition
        assert!(ratio < 1e-3, "σ/H decay ratio = {:.2e} (expect ≪ 1)", ratio);
        assert!(ratio > 1e-8, "σ/H decay ratio = {:.2e} (too small)", ratio);
    }

    #[test]
    fn test_friedmann_constraint() {
        let cosmo = standard_cosmo();
        let params = BianchiType::I.canonical_params();
        let bg = evolve(&params, &cosmo, 1e-5, 1e-4, 5000).unwrap();
        let max_viol = bg.max_constraint_violation();
        // For BI with flat cosmology and small shear, constraint ≈ Σ²
        assert!(max_viol < 1e-8, "Friedmann violation = {:.2e}", max_viol);
    }

    #[test]
    fn test_conformal_time_increasing() {
        let cosmo = standard_cosmo();
        let params = BianchiType::I.canonical_params();
        let bg = evolve(&params, &cosmo, 0.0, 1e-4, 1000).unwrap();
        for i in 1..bg.eta_grid.len() {
            assert!(
                bg.eta_grid[i] > bg.eta_grid[i - 1],
                "η not increasing at i={}: {:.6} ≤ {:.6}",
                i, bg.eta_grid[i], bg.eta_grid[i - 1]
            );
        }
    }

    #[test]
    fn test_hubble_today() {
        let cosmo = standard_cosmo();
        // H₀ = 67.36 km/s/Mpc
        let h_expected = 67.36 * 1e3 / 3.085677581e22;
        let h_computed = cosmo.hubble_of_a(1.0);
        let rel = (h_computed - h_expected).abs() / h_expected;
        assert!(rel < 1e-10, "H₀ mismatch: {:.6e} vs {:.6e}", h_computed, h_expected);
    }

    #[test]
    fn test_radiation_era_shear_const() {
        // Deep in radiation era, σ/H should be approximately constant
        // (actually decays as a⁻¹, but very slowly for small Δ ln a)
        let cosmo = standard_cosmo();
        let params = BianchiType::I.canonical_params();
        let bg = evolve(&params, &cosmo, 1e-4, 1e-6, 5000).unwrap();
        // Check at a ~ 10⁻⁵ (deep radiation)
        let a1 = 1e-5;
        let a2 = 2e-5;
        let sh1 = bg.sigma_h_of_a(a1);
        let sh2 = bg.sigma_h_of_a(a2);
        // In radiation era: σ/H ∝ a⁻¹, so sh2/sh1 ≈ a1/a2 = 0.5
        // (NOT constant! The "constant" statement applies to σ_phys/H, not Σ)
        let ratio = sh2 / sh1;
        assert!(
            (ratio - 0.5).abs() < 0.1,
            "Radiation-era σ/H ratio: {:.4} (expect ~0.5 for ∝a⁻¹)",
            ratio
        );
    }
}
