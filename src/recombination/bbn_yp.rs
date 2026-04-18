// BE-05h: Y_p as free parameter + external BBN interface.
//
// Replaces hardcoded Y_P = 0.245 with a configurable parameter.
// BBN consistency: Y_p(ω_b, N_eff) from Planck 2018 relation.

/// Source of Y_p value.
#[derive(Clone, Debug)]
pub(crate) enum YpSource {
    /// Fixed value (default: 0.2454).
    Fixed(f64),
    /// BBN-consistent from (ω_b, N_eff).
    BbnConsistent { omega_b_h2: f64, n_eff: f64 },
    /// External injection (from PArthENoPE, PRIMAT, AlterBBN).
    External(f64),
}

impl YpSource {
    pub(crate) fn y_p(&self) -> f64 {
        match self {
            Self::Fixed(v) => *v,
            Self::BbnConsistent { omega_b_h2, n_eff } => bbn_yp(*omega_b_h2, *n_eff),
            Self::External(v) => *v,
        }
    }
}

impl Default for YpSource {
    fn default() -> Self { Self::Fixed(0.2454) }
}

/// BBN consistency relation (Planck 2018, leading-order analytic).
///
/// Y_p(ω_b, N_eff) ≈ 0.2454 + 0.0130 × (N_eff − 3.046)
///                            + 0.014 × (ω_b − 0.02237) / 0.02237
pub(crate) fn bbn_yp(omega_b_h2: f64, n_eff: f64) -> f64 {
    0.2454
        + 0.0130 * (n_eff - 3.046)
        + 0.014 * (omega_b_h2 - 0.02237) / 0.02237
}

/// Helium-to-hydrogen number ratio: f_He = Y_p / (4(1−Y_p)).
pub(crate) fn f_he(y_p: f64) -> f64 {
    y_p / (4.0 * (1.0 - y_p))
}

/// Hydrogen mass fraction: X_p = 1 − Y_p.
pub(crate) fn x_p(y_p: f64) -> f64 { 1.0 - y_p }

/// Maximum electron fraction: x_e_max = 1 + f_He (fully ionised H + HeII).
pub(crate) fn x_e_max(y_p: f64) -> f64 { 1.0 + f_he(y_p) }

/// Hydrogen number density today [m⁻³] from Y_p and Ω_b.
pub(crate) fn n_h0(y_p: f64, omega_b: f64, h: f64) -> f64 {
    let mpc = 3.085677581e22;
    let m_p = 1.67262192e-27;
    let g_n = 6.674e-11;
    let h0 = h * 1e5 / mpc; // H₀ [s⁻¹] ... no, H₀ = h × 100 km/s/Mpc
    // ρ_crit = 3H₀²/(8πG)
    let rho_c = 3.0 * (h * 1e5 / mpc).powi(2) / (8.0 * std::f64::consts::PI * g_n);
    (1.0 - y_p) * omega_b * rho_c / m_p
}

/// Anisotropic BBN correction (leading order).
///
/// δY_p ∝ (Σ²)^{1/2}: shear changes expansion rate at weak freeze-out.
/// Approximate: δY_p ~ 0.01 × (Σ²/10⁻⁶)^{0.5}
pub(crate) fn delta_yp_aniso(sigma2: f64) -> f64 {
    0.01 * (sigma2 / 1e-6).sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fixed_default() {
        let s = YpSource::default();
        assert!((s.y_p() - 0.2454).abs() < 1e-10);
    }

    #[test]
    fn test_bbn_fiducial() {
        let y = bbn_yp(0.02237, 3.046);
        assert!((y - 0.2454).abs() < 0.0001, "BBN fiducial: Y_p = {:.4}", y);
    }

    #[test]
    fn test_bbn_high_neff() {
        let y = bbn_yp(0.02237, 4.046);
        assert!(y > 0.2454, "Higher N_eff → higher Y_p: {:.4}", y);
        assert!((y - 0.2454 - 0.013).abs() < 0.001);
    }

    #[test]
    fn test_f_he_fiducial() {
        let fh = f_he(0.2454);
        assert!((fh - 0.0813).abs() < 0.001, "f_He = {:.4}", fh);
    }

    #[test]
    fn test_x_e_max() {
        let xm = x_e_max(0.2454);
        assert!((xm - 1.0813).abs() < 0.001);
    }

    #[test]
    fn test_yp_source_bbn() {
        let s = YpSource::BbnConsistent { omega_b_h2: 0.02237, n_eff: 3.046 };
        assert!((s.y_p() - 0.2454).abs() < 0.001);
    }

    #[test]
    fn test_yp_source_external() {
        let s = YpSource::External(0.26);
        assert!((s.y_p() - 0.26).abs() < 1e-15);
    }

    #[test]
    fn test_delta_yp_aniso() {
        let dy = delta_yp_aniso(1e-6);
        assert!((dy - 0.01).abs() < 0.001, "δY_p(Σ²=10⁻⁶) = {:.4}", dy);
    }

    #[test]
    fn test_n_h0_physical() {
        let nh = n_h0(0.2454, 0.0493, 0.6736);
        // n_H0 ~ 1.9e-7 cm⁻³ = 1.9e-1 m⁻³ ... actually much higher
        // ρ_crit ~ 8.5e-27 kg/m³, ρ_b = 0.0493 × ρ_crit ~ 4.2e-28 kg/m³
        // n_H = (1−Y_p)ρ_b/m_p ~ 0.755 × 4.2e-28 / 1.67e-27 ~ 0.19 m⁻³
        assert!(nh > 0.1 && nh < 1.0, "n_H0 = {:.4} m⁻³", nh);
    }

    #[test]
    fn test_yp_high_helium_shift() {
        // Y_p = 0.26 vs 0.245: f_He changes, affecting recombination
        let fh_std = f_he(0.245);
        let fh_high = f_he(0.26);
        assert!(fh_high > fh_std, "More He → larger f_He");
        // δf_He/f_He ~ δY_p / Y_p ~ 6%
        let rel = (fh_high - fh_std) / fh_std;
        assert!(rel > 0.05 && rel < 0.15, "δf_He/f_He = {:.1}%", rel * 100.0);
    }
}
