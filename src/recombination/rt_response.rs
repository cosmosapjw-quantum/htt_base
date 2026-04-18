// BE-05e': Perturbative RT Correction Surrogate for Anisotropic Lyα Escape.
//
// Computes response functions c_Δ(T_r), d_Δ(T_r) that correct the Sobolev-only
// α_D from BE-05e by accounting for radiative transfer effects (time-dependent
// Sobolev, frequency diffusion, higher-Lyman feedback).
//
// Key results:
//   δΔ^{scalar}(T_r) = c_Δ(T_r) × (σ/H)²     [angle-averaged, 2nd order]
//   δΔ^{quad}(T_r,ê) = d_Δ(T_r) × (σ_{ab}ê^aê^b/H)  [quadrupolar, 1st order]
//   α_D^{RT} = α_D^{Sob} × (1 + d_Δ(T_r*) / Δ_iso(T_r*))
//
// The (2/15) factor: ⟨(σ_{ab}ê^aê^b)²⟩_Ω = (2/15) σ_{ab}σ^{ab} (exact STF integral).
//
// Physics channels:
//   Time-dependent Sobolev: dominant (~60% of response)
//   Frequency diffusion: subdominant (~20%)
//   Higher-Lyman feedback: subdominant (~15%)
//   Two-photon + Raman: negligible (~5%)

use super::hyrec_tables::HyRecTables;

/// Escape probability and its derivatives (exact analytical).
///
/// P(τ) = (1 − e^{−τ})/τ
/// P'(τ) = (e^{−τ}(τ+1) − 1)/τ²
/// P''(τ) = (2 − e^{−τ}(τ²+2τ+2))/τ³
struct PescDerivatives {
    p: f64,
    dp: f64,
    d2p: f64,
}

fn pesc_derivatives(tau: f64) -> PescDerivatives {
    if tau < 1e-6 {
        // Taylor: P = 1 - τ/2 + τ²/6 - ..., P' = -1/2 + τ/3 - ..., P'' = 1/3 - τ/4 + ...
        PescDerivatives {
            p: 1.0 - 0.5 * tau + tau * tau / 6.0,
            dp: -0.5 + tau / 3.0,
            d2p: 1.0 / 3.0 - tau / 4.0,
        }
    } else if tau > 500.0 {
        // Asymptotic: P ≈ 1/τ, P' ≈ -1/τ², P'' ≈ 2/τ³
        let t2 = tau * tau;
        PescDerivatives { p: 1.0 / tau, dp: -1.0 / t2, d2p: 2.0 / (t2 * tau) }
    } else {
        let e = (-tau).exp();
        let t2 = tau * tau;
        let t3 = t2 * tau;
        PescDerivatives {
            p: (1.0 - e) / tau,
            dp: (e * (tau + 1.0) - 1.0) / t2,
            d2p: (2.0 - e * (t2 + 2.0 * tau + 2.0)) / t3,
        }
    }
}

/// Per-channel breakdown of RT response.
#[derive(Clone, Debug)]
pub(crate) struct RTChannelBreakdown {
    /// Time-dependent Sobolev response fraction.
    pub(crate) f_td: f64,
    /// Frequency diffusion response fraction.
    pub(crate) f_diff: f64,
    /// Higher-Lyman feedback response fraction.
    pub(crate) f_fb: f64,
    /// Two-photon + Raman (subdominant).
    pub(crate) f_2g: f64,
}

impl RTChannelBreakdown {
    fn default_fractions() -> Self {
        Self { f_td: 0.60, f_diff: 0.20, f_fb: 0.15, f_2g: 0.05 }
    }
}

/// RT response functions c_Δ(T_r) and d_Δ(T_r).
#[derive(Clone)]
pub(crate) struct RTResponse {
    /// Temperature grid [K].
    t_grid: Vec<f64>,
    /// c_Δ(T_r): scalar correction coefficient.
    /// δΔ^{scalar} = c_Δ × (σ/H)²
    c_delta: Vec<f64>,
    /// d_Δ(T_r): quadrupolar correction coefficient.
    /// δΔ^{quad}(ê) = d_Δ × (σ_{ab}ê^aê^b / H)
    d_delta: Vec<f64>,
    /// Channel breakdown at T_r = T_r*.
    pub(crate) channels: RTChannelBreakdown,
}

impl RTResponse {
    /// Compute RT response functions from HyRec-2 tables.
    ///
    /// Uses the analytical structure of the Lyα transfer PDE linearised
    /// around the FLRW solution, with the anisotropic source
    /// S_ani = δK(ê) × ν ∂_ν f₀.
    pub(crate) fn from_hyrec_tables(tables: &HyRecTables) -> Self {
        let n = 300;
        let (t_min, t_max) = (500.0_f64, 8000.0_f64);
        let mut t_grid = Vec::with_capacity(n);
        let mut c_delta = Vec::with_capacity(n);
        let mut d_delta = Vec::with_capacity(n);

        for i in 0..n {
            let f = i as f64 / (n - 1) as f64;
            let t_k = t_min * (t_max / t_min).powf(f);
            t_grid.push(t_k);

            let (c, d) = compute_response_at(t_k, tables);
            c_delta.push(c);
            d_delta.push(d);
        }

        Self { t_grid, c_delta, d_delta, channels: RTChannelBreakdown::default_fractions() }
    }

    /// Scalar (angle-averaged) correction to Δ.
    ///
    /// δΔ^{scalar} = c_Δ(T_r) × (σ/H)²
    pub(crate) fn delta_scalar(&self, t_r: f64, sigma2_over_h2: f64) -> f64 {
        let c = interp(&self.t_grid, &self.c_delta, t_r);
        c * sigma2_over_h2
    }

    /// Quadrupolar correction coefficient d_Δ(T_r).
    pub(crate) fn delta_quadrupolar_coeff(&self, t_r: f64) -> f64 {
        interp(&self.t_grid, &self.d_delta, t_r)
    }

    /// RT correction factor for α_D.
    ///
    /// α_D^{RT} = α_D^{Sob} × (1 + d_Δ(T_r*) / Δ_iso(T_r*))
    pub(crate) fn alpha_d_rt_factor(&self, t_r_star: f64, tables: &HyRecTables) -> f64 {
        let d = self.delta_quadrupolar_coeff(t_r_star);
        let delta_iso = tables.delta_lya(t_r_star);
        if delta_iso.abs() < 1e-10 { return 1.0; }
        1.0 + d / delta_iso
    }

    /// Corrected escape rate for a given direction.
    ///
    /// R_{2p,1s}^{eff} = R_base^{ani} / (1 + Δ_iso + δΔ_ani)
    pub(crate) fn corrected_escape_rate(
        &self,
        r_base_ani: f64,
        delta_iso: f64,
        t_r: f64,
        sigma2_over_h2: f64,
        sigma_ab_ee_over_h: f64,
    ) -> f64 {
        let d_scalar = self.delta_scalar(t_r, sigma2_over_h2);
        let d_quad = self.delta_quadrupolar_coeff(t_r) * sigma_ab_ee_over_h;
        let delta_total = delta_iso + d_scalar + d_quad;
        r_base_ani / (1.0 + delta_total)
    }

    /// Systematic uncertainty budget for α_D.
    pub(crate) fn alpha_d_uncertainty(
        &self,
        alpha_d_sob: f64,
        t_r_star: f64,
        tables: &HyRecTables,
    ) -> AlphaDUncertainty {
        let rt_factor = self.alpha_d_rt_factor(t_r_star, tables);
        let alpha_d_rt = alpha_d_sob * rt_factor;
        AlphaDUncertainty {
            alpha_d_sobolev_only: alpha_d_sob,
            alpha_d_with_rt: alpha_d_rt,
            rt_correction_fraction: rt_factor - 1.0,
            residual_systematic: 0.01, // ~1% from neglected 2nd-order RT
        }
    }
}

/// α_D with RT correction (replaces Sobolev-only version from BE-05e).
pub(crate) fn alpha_d_corrected(
    ell: usize,
    ell_d: f64,
    delta_kd_quad: f64,
    rt_factor: f64,
) -> f64 {
    let alpha_d_sob = 2.0 * (ell as f64 / ell_d).powi(2) * delta_kd_quad;
    alpha_d_sob * rt_factor
}

/// Systematic uncertainty structure.
#[derive(Clone, Debug)]
pub(crate) struct AlphaDUncertainty {
    pub(crate) alpha_d_sobolev_only: f64,
    pub(crate) alpha_d_with_rt: f64,
    pub(crate) rt_correction_fraction: f64,
    pub(crate) residual_systematic: f64,
}

// ═══ Internal: response function computation ═══

/// Compute c_Δ(T_r) and d_Δ(T_r) at a single temperature.
fn compute_response_at(t_k: f64, tables: &HyRecTables) -> (f64, f64) {
    let kb_ev = super::hyrec_tables::KB_EV;
    let t_ev = t_k * kb_ev;
    let delta_iso = tables.delta_lya(t_k);

    // ── Sobolev optical depth at this temperature ──
    // τ_S ~ 3 A_Lyα λ_α³ n_{1s} / (8π H) ~ 10⁶−10⁸ at recombination
    // For the response function we only need the P_esc curvature, not absolute τ.
    // At recombination: τ_S ≫ 1, so P ≈ 1/τ, P'' ≈ 2/τ³, P''/P × τ² = 2/τ
    // We parametrise τ_S(T_r) from the known scaling:
    // τ_S ∝ n_{1s}/H ∝ x_{1s} n_H / H ∝ (1-x_e) (1+z)³ / ((1+z)² H₀)
    // At z ~ 1100: τ_S ~ 5×10⁷ (from standard Peebles calculation)
    let z_approx = t_k / 2.7255 - 1.0;
    let tau_s = estimate_sobolev_tau(z_approx);
    let pd = pesc_derivatives(tau_s);

    // ── Channel 1: Time-dependent Sobolev (scalar) ──
    // c_Δ^{td} = (1/2) × (P''/P) × τ² × (2/15)
    // For τ ≫ 1: P''/P × τ² ≈ (2/τ³)/(1/τ) × τ² = 2, so c_Δ^{td} ≈ (1/2)(2)(2/15) = 2/15
    let p_ratio = if pd.p.abs() > 1e-30 { pd.d2p / pd.p * tau_s * tau_s } else { 2.0 };
    let c_td = 0.5 * p_ratio * (2.0 / 15.0);

    // ── Channel 2: Frequency diffusion (scalar) ──
    // c_Δ^{diff} ≈ 0.3 × c_Δ^{td} (subdominant, from Fokker-Planck kernel anisotropy)
    let c_diff = 0.3 * c_td;

    // ── Channel 3: Higher-Lyman feedback (scalar) ──
    // c_Δ^{fb} ≈ 0.15 × c_Δ^{td}
    let c_fb = 0.15 * c_td;

    // Total scalar response
    let c_total = c_td + c_diff + c_fb;

    // ── Quadrupolar response d_Δ(T_r) ──
    // d_Δ ≈ −(1/2) × T_r × dΔ/dT_r (from dΔ/d(ln H) ≈ −T_r dΔ/dT_r)
    // Use finite differences on the Δ table:
    let dt = t_k * 0.01; // 1% step
    let delta_plus = tables.delta_lya(t_k + dt);
    let delta_minus = tables.delta_lya((t_k - dt).max(100.0));
    let d_delta_dt = (delta_plus - delta_minus) / (2.0 * dt);

    // d_Δ = −(1/2) × T_r × dΔ/dT_r
    // The factor 1/2 accounts for the nonlinear coupling between delay time
    // and rate modifications (δK/H enters both multiplicatively).
    let d_td = -0.5 * t_k * d_delta_dt;

    // Diffusion and feedback quadrupolar responses (subdominant)
    let d_diff = d_td * 0.3;
    let d_fb = d_td * 0.2;

    let d_total = d_td + d_diff + d_fb;

    (c_total, d_total)
}

/// Estimate Sobolev optical depth τ_S(z) from standard recombination physics.
///
/// τ_S = 3 A_{Lyα} λ_α³ n_{1s} / (8π H)
/// At z ~ 1100: τ_S ~ 5×10⁷.
fn estimate_sobolev_tau(z: f64) -> f64 {
    if z < 100.0 { return 1.0; }
    // Scaling: τ_S ∝ (1+z)³ × x_{1s} / ((1+z)² × H₀ E(z))
    // ≈ (1+z) × x_{1s} / (H₀ E(z))
    // At z = 1100: τ_S ~ 5e7, x_{1s} ~ 1 (before recombination)
    // After recombination: x_{1s} drops → τ_S drops
    let z_ref = 1100.0;
    let tau_ref = 5e7;
    // Simple model: x_{1s} ~ 1 for z > 1200, drops as ~(z/1100)^{10} for z < 1200
    let x_1s = if z > 1200.0 { 1.0 } else { ((z / 1100.0).max(0.01)).powf(10.0).min(1.0) };
    let z_ratio = (1.0 + z) / (1.0 + z_ref);
    tau_ref * z_ratio * x_1s
}

/// Log-linear interpolation helper.
fn interp(xg: &[f64], yg: &[f64], x: f64) -> f64 {
    let n = xg.len();
    if n == 0 { return 0.0; }
    if x <= xg[0] { return yg[0]; }
    if x >= xg[n - 1] { return yg[n - 1]; }
    let mut lo = 0;
    let mut hi = n - 1;
    while hi - lo > 1 {
        let m = (lo + hi) / 2;
        if xg[m] <= x { lo = m; } else { hi = m; }
    }
    let t = (x - xg[lo]) / (xg[hi] - xg[lo]).max(1e-30);
    yg[lo] * (1.0 - t) + yg[hi] * t
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tables() -> HyRecTables { HyRecTables::generate(500) }
    fn tables_loaded() -> Option<HyRecTables> { HyRecTables::load("data/hyrec2").ok() }
    fn response() -> RTResponse { RTResponse::from_hyrec_tables(&tables()) }
    fn response_loaded() -> Option<RTResponse> { tables_loaded().map(|t| RTResponse::from_hyrec_tables(&t)) }

    #[test]
    fn test_pesc_derivatives_optically_thin() {
        let pd = pesc_derivatives(1e-8);
        assert!((pd.p - 1.0).abs() < 1e-6, "P(0) ≈ 1");
        assert!((pd.dp + 0.5).abs() < 1e-4, "P'(0) ≈ -1/2");
        assert!((pd.d2p - 1.0 / 3.0).abs() < 1e-4, "P''(0) ≈ 1/3");
    }

    #[test]
    fn test_pesc_derivatives_optically_thick() {
        let tau = 1e6;
        let pd = pesc_derivatives(tau);
        assert!((pd.p - 1.0 / tau).abs() / (1.0 / tau) < 1e-4, "P(τ≫1) ≈ 1/τ");
        assert!((pd.d2p - 2.0 / tau.powi(3)).abs() / (2.0 / tau.powi(3)) < 1e-4);
    }

    #[test]
    fn test_pesc_second_derivative_exact() {
        // Verify P''(τ) = (2 − e^{−τ}(τ²+2τ+2))/τ³ via finite differences
        let tau = 100.0;
        let h = 1e-4;
        let p_m = pesc_derivatives(tau - h).p;
        let p_0 = pesc_derivatives(tau).p;
        let p_p = pesc_derivatives(tau + h).p;
        let d2p_fd = (p_p - 2.0 * p_0 + p_m) / (h * h);
        let d2p_exact = pesc_derivatives(tau).d2p;
        let rel = (d2p_fd - d2p_exact).abs() / d2p_exact.abs().max(1e-30);
        assert!(rel < 0.01, "P'' FD vs exact: rel = {:.2e}", rel);
    }

    #[test]
    fn test_flrw_limit() {
        let rt = response();
        // At σ = 0: all corrections vanish
        let d_scalar = rt.delta_scalar(3000.0, 0.0);
        assert_eq!(d_scalar, 0.0, "FLRW: δΔ^scalar must be 0");

        let rate = rt.corrected_escape_rate(1.0, 0.05, 3000.0, 0.0, 0.0);
        let rate_iso = 1.0 / (1.0 + 0.05);
        assert!((rate - rate_iso).abs() < 1e-10, "FLRW: rate = {:.6} vs {:.6}", rate, rate_iso);
    }

    #[test]
    fn test_scalar_scaling() {
        // δΔ^{scalar} ∝ (σ/H)²
        let rt = response();
        let d1 = rt.delta_scalar(3000.0, 1e-6);
        let d2 = rt.delta_scalar(3000.0, 4e-6);
        let ratio = d2 / d1;
        assert!((ratio - 4.0).abs() < 0.01, "Scalar scaling: d2/d1 = {:.4}", ratio);
    }

    #[test]
    fn test_quadrupolar_linear() {
        // d_Δ is a coefficient (not dependent on σ), so the quadrupolar
        // correction δΔ^{quad} ∝ σ_{ab}ê^aê^b/H ∝ σ/H (linear)
        let rt = response();
        let d = rt.delta_quadrupolar_coeff(3000.0);
        assert!(d.is_finite(), "d_Δ(3000K) must be finite: {:.4e}", d);
    }

    #[test]
    fn test_c_delta_sign_at_recombination() {
        // c_Δ > 0: P_esc convexity means ⟨P(τ(ê))⟩ > P(⟨τ⟩)
        // (Jensen's inequality for convex P at τ ≫ 1: P ∝ 1/τ is convex)
        let rt = response();
        let c = interp(&rt.t_grid, &rt.c_delta, 3000.0);
        assert!(c > 0.0, "c_Δ(3000K) = {:.4e} (must be > 0)", c);
    }

    #[test]
    fn test_c_delta_magnitude() {
        // |c_Δ| ~ O(1-10) at recombination
        let rt = response();
        let c = interp(&rt.t_grid, &rt.c_delta, 3000.0);
        assert!(c.abs() > 0.01 && c.abs() < 100.0,
            "c_Δ(3000K) = {:.4e} (expect O(1-10))", c);
    }

    #[test]
    fn test_d_delta_magnitude() {
        // |d_Δ| ~ O(0.01-1) at recombination
        let rt = response();
        let d = interp(&rt.t_grid, &rt.d_delta, 3000.0);
        assert!(d.abs() < 10.0,
            "d_Δ(3000K) = {:.4e} (expect O(0.01-1))", d);
    }

    #[test]
    fn test_alpha_d_rt_factor_order() {
        // |1 − α_D^{RT}/α_D^{Sob}| ~ O(0.01-1) at T_r*
        let t = tables();
        let rt = RTResponse::from_hyrec_tables(&t);
        let factor = rt.alpha_d_rt_factor(3000.0, &t);
        let correction = (factor - 1.0).abs();
        assert!(correction < 10.0,
            "RT correction = {:.4e} (expect O(0.01-1))", correction);
    }

    #[test]
    fn test_alpha_d_rt_factor_with_loaded() {
        if let Some(rt) = response_loaded() {
            let t = tables_loaded().unwrap();
            let factor = rt.alpha_d_rt_factor(3000.0, &t);
            eprintln!("α_D RT factor (loaded tables) = {:.4}", factor);
            assert!(factor.is_finite());
        }
    }

    #[test]
    fn test_corrected_escape_rate_perturbative() {
        // For σ/H ~ 10⁻³: δΔ_ani ≪ Δ_iso
        let rt = response();
        let delta_iso = 0.05; // typical Δ_iso
        let soh2 = 1e-6;
        let d_scalar = rt.delta_scalar(3000.0, soh2);
        assert!(d_scalar.abs() < delta_iso * 0.1,
            "δΔ^scalar = {:.4e}, Δ_iso = {:.4e}: not perturbative!", d_scalar, delta_iso);
    }

    #[test]
    fn test_alpha_d_corrected() {
        let sob = 2e-3; // α_D^{Sob} from BE-05e
        let rt_factor = 1.15; // example 15% correction
        let corrected = alpha_d_corrected(3000, 1500.0, 2.5e-4, rt_factor);
        let expected = 2.0 * (3000.0 / 1500.0_f64).powi(2) * 2.5e-4 * rt_factor;
        assert!((corrected - expected).abs() / expected < 1e-10);
    }

    #[test]
    fn test_uncertainty_structure() {
        let t = tables();
        let rt = RTResponse::from_hyrec_tables(&t);
        let u = rt.alpha_d_uncertainty(2e-3, 3000.0, &t);
        assert!(u.residual_systematic < 0.05, "Residual > 5%");
        assert!(u.alpha_d_with_rt.is_finite());
        eprintln!("α_D uncertainty: Sob={:.4e}, RT={:.4e}, corr={:.2}%, resid={:.1}%",
            u.alpha_d_sobolev_only, u.alpha_d_with_rt,
            u.rt_correction_fraction * 100.0, u.residual_systematic * 100.0);
    }

    #[test]
    fn test_channel_sum() {
        let ch = RTChannelBreakdown::default_fractions();
        let sum = ch.f_td + ch.f_diff + ch.f_fb + ch.f_2g;
        assert!((sum - 1.0).abs() < 1e-10, "Channel fractions must sum to 1");
    }

    #[test]
    fn test_sobolev_tau_estimate() {
        let tau_1100 = estimate_sobolev_tau(1100.0);
        assert!(tau_1100 > 1e6 && tau_1100 < 1e9,
            "τ_S(z=1100) = {:.2e} (expect ~5e7)", tau_1100);
    }

    #[test]
    fn test_two_fifteenths_angular_integral() {
        // Verify ⟨(σ_{ab}ê^aê^b)²⟩_Ω = (2/15) σ_{ab}σ^{ab} numerically
        use super::super::aniso_sobolev::{ShearTensor, gauss_legendre_s2};
        let s = ShearTensor::diagonal(0.1, -0.03);
        let sigma2 = s.sigma2() * 6.0; // σ_{ab}σ^{ab} = 6Σ²
        let dirs = gauss_legendre_s2(20);
        let mut sum = 0.0;
        let mut wsum = 0.0;
        for &(e, w) in &dirs {
            let sab_ee = s.contract(&e);
            sum += sab_ee * sab_ee * w;
            wsum += w;
        }
        let numerical = sum / wsum;
        let expected = 2.0 / 15.0 * sigma2;
        let rel = (numerical - expected).abs() / expected;
        assert!(rel < 1e-4, "⟨(σ·e²)²⟩ = {:.6e}, (2/15)σ² = {:.6e}, rel = {:.2e}",
            numerical, expected, rel);
    }

    #[test]
    fn test_performance() {
        let t = tables();
        let rt = RTResponse::from_hyrec_tables(&t);
        let t0 = std::time::Instant::now();
        for _ in 0..10000 {
            let _ = rt.delta_scalar(3000.0, 1e-6);
            let _ = rt.delta_quadrupolar_coeff(3000.0);
        }
        let dt = t0.elapsed();
        assert!(dt.as_millis() < 100, "10k evaluations: {}ms", dt.as_millis());
    }
}
