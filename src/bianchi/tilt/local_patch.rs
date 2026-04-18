// Level 3: Local peculiar velocity patch with window function W_R.
// BB-05: W_R(x)·v_loc^a(t,x) bounded by the window.
//
// Three-level structure:
//   Level 1: V̄_m^a(t) — global tilt β
//   Level 2: δV_{cos}^a(t,x) — fluctuation δβ
//   Level 3: W_R(x)·v_loc^a(t,x) — local peculiar velocity

/// Top-hat window function in Fourier space: W_R(kR) = 3(sin x − x cos x)/x³
pub(crate) fn window_tophat(kr: f64) -> f64 {
    if kr.abs() < 1e-6 {
        1.0 - kr*kr/10.0 // Taylor expansion for small x
    } else {
        3.0 * (kr.sin() - kr * kr.cos()) / (kr * kr * kr)
    }
}

/// Gaussian window: W_R(kR) = exp(−k²R²/2)
pub(crate) fn window_gaussian(kr: f64) -> f64 {
    (-0.5 * kr * kr).exp()
}

/// Local patch velocity bound: |v_loc| < v_max(R, z)
///
/// The local peculiar velocity is bounded by the window-smoothed
/// velocity field. At scale R [Mpc/h]:
///   σ_v(R) = H₀f(Ω) σ₈ × (8/R)^α
/// with α ≈ 0.5 for ΛCDM.
pub(crate) fn local_velocity_bound(
    r_mpc_h: f64,
    sigma8: f64,
    h0_km_s_mpc: f64,
    f_omega: f64, // growth rate f ≈ Ω_m^{0.55}
) -> f64 {
    // σ_v(R) ≈ H₀ f σ₈ × (8/R)^0.5 [km/s]
    let sigma_v = h0_km_s_mpc * f_omega * sigma8 * (8.0 / r_mpc_h.max(0.1)).sqrt();
    sigma_v / 299792.458 // Convert to v/c (dimensionless)
}

/// Total tilt at a point: v_total = V̄ + δV + W_R · v_loc.
pub(crate) fn total_tilt_velocity(
    v_global: f64,
    delta_v: f64,
    v_local: f64,
    w_r: f64,
) -> f64 {
    v_global + delta_v + w_r * v_local
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_window_tophat_normalization() {
        // W(0) = 1
        assert!((window_tophat(0.0) - 1.0).abs() < 1e-15);
    }

    #[test]
    fn test_window_gaussian_normalization() {
        assert!((window_gaussian(0.0) - 1.0).abs() < 1e-15);
    }

    #[test]
    fn test_local_velocity_bound() {
        // At R=8 Mpc/h: σ_v ≈ H₀ × f × σ₈ ≈ 67 × 0.5 × 0.8 ≈ 27 km/s → v/c ≈ 9e-5
        let vb = local_velocity_bound(8.0, 0.8, 67.0, 0.5);
        assert!(vb > 1e-5 && vb < 1e-3, "v_bound = {:.2e}", vb);
    }
}
