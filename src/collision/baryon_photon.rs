// Baryon-photon momentum coupling.
// BC-04: Baryon Euler equation with Thomson drag.
//
// Baryon Euler: v̇_b = −Hv_b + c²_s k δ_b + R⁻¹ κ̇(v_b − v_γ)
// where R = 3ρ_b/(4ρ_γ) is the baryon-to-photon ratio.
//
// Momentum conservation: C^(γ)₁ + R × C^(b) = 0
// (photon momentum loss = baryon momentum gain)
//
// Sound speed: c_s = 1/√(3(1+R))
// At recombination R ≈ 0.6, c_s ≈ 0.46.

/// Baryon-to-photon energy density ratio: R = 3ρ_b/(4ρ_γ).
///
/// R(a) = (3/4)(Ω_b/Ω_γ)a = R₀ × a
///
/// Typical values: R(z=1090) ≈ 0.6, R(z=0) ≈ 600.
pub(crate) fn baryon_photon_ratio(omega_b: f64, omega_gamma: f64, a: f64) -> f64 {
    if omega_gamma.abs() < 1e-30 { return f64::INFINITY; }
    0.75 * (omega_b / omega_gamma) * a
}

/// Baryon-photon sound speed: c_s = 1/√(3(1+R)).
///
/// In the tight-coupling limit, the photon-baryon fluid oscillates
/// with this characteristic speed. For pure radiation (R=0): c_s = 1/√3.
pub(crate) fn sound_speed(r_ratio: f64) -> f64 {
    (3.0 * (1.0 + r_ratio)).recip().sqrt()
}

/// Sound horizon: r_s = ∫₀^η c_s dη.
///
/// For constant c_s: r_s = c_s × η.
/// For variable c_s(a): numerical integration required.
pub(crate) fn sound_horizon_approx(cs: f64, eta: f64) -> f64 {
    cs * eta
}

/// Baryon Euler equation RHS:
///   dv_b/dη = −(aH)v_b + c²_s k δ_b + R⁻¹ κ̇(v_b − v_γ)
///
/// # Arguments
/// * `v_b` - Baryon velocity
/// * `v_gamma` - Photon dipole (= F₁ in our convention)
/// * `delta_b` - Baryon density perturbation
/// * `a_h` - Conformal Hubble aH [Mpc⁻¹]
/// * `k` - Wavenumber [Mpc⁻¹]
/// * `cs2` - Sound speed squared c²_s
/// * `kappa_dot` - Thomson rate [Mpc⁻¹]
/// * `r_inv` - 1/R = (4ρ_γ)/(3ρ_b) (inverse baryon-photon ratio)
pub(crate) fn baryon_euler_rhs(
    v_b: f64,
    v_gamma: f64,
    delta_b: f64,
    a_h: f64,
    k: f64,
    cs2: f64,
    kappa_dot: f64,
    r_inv: f64,
) -> f64 {
    -a_h * v_b + cs2 * k * delta_b + r_inv * kappa_dot * (v_gamma - v_b)
}

/// Baryon momentum collision term: C_b = R⁻¹ κ̇(v_γ − v_b).
///
/// This is the momentum transferred FROM photons TO baryons per unit time.
/// Sign: photons drag baryons TOWARDS photon velocity (friction).
/// Note: our κ̇ > 0 (scattering rate), so (v_γ − v_b) gives the correct drag.
pub(crate) fn baryon_collision_term(
    v_b: f64,
    v_gamma: f64,
    kappa_dot: f64,
    r_inv: f64,
) -> f64 {
    r_inv * kappa_dot * (v_gamma - v_b)
}

/// Verify photon-baryon momentum conservation.
///
/// The total momentum change must vanish:
///   C^(γ)₁ + R × C^(b) = 0
///
/// Returns |C^(γ)₁ + R × C^(b)|.
pub(crate) fn momentum_conservation_check(
    c_photon_1: f64,
    c_baryon: f64,
    r_ratio: f64,
) -> f64 {
    (c_photon_1 + r_ratio * c_baryon).abs()
}

/// Coupled photon-baryon oscillation frequency (WKB).
///
/// ω² = k² c²_s = k²/(3(1+R))
pub(crate) fn oscillation_frequency(k: f64, r_ratio: f64) -> f64 {
    k * sound_speed(r_ratio)
}

/// Evolve a simple photon-baryon oscillator in the tight-coupling limit.
///
/// State: [Θ₀, v_b] where Θ₀ = F₀ (temperature monopole).
/// In TCA: v_γ ≈ v_b, so the system reduces to:
///   Θ̇₀ = −k v_b / 3
///   v̇_b = k Θ₀ / (1+R) − (aH) v_b  (neglecting δ_b for simplicity)
///
/// Returns (Θ₀, v_b) after n_steps of RK4 evolution.
pub(crate) fn evolve_tca_oscillator(
    theta0_init: f64,
    vb_init: f64,
    k: f64,
    r_ratio: f64,
    a_h: f64,
    eta_final: f64,
    n_steps: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let d_eta = eta_final / n_steps as f64;
    let cs2 = sound_speed(r_ratio).powi(2);

    let mut theta0 = theta0_init;
    let mut vb = vb_init;

    let mut eta_hist = Vec::with_capacity(n_steps + 1);
    let mut t0_hist = Vec::with_capacity(n_steps + 1);
    let mut vb_hist = Vec::with_capacity(n_steps + 1);

    eta_hist.push(0.0); t0_hist.push(theta0); vb_hist.push(vb);

    for step in 0..n_steps {
        let rhs = |t: f64, v: f64| -> (f64, f64) {
            (-k * v / 3.0, k * t * cs2 * 3.0 - a_h * v)
            // Θ̇₀ = −k v_b/3, v̇_b = k c²_s×3 Θ₀ − aH v_b
            // (factor 3 because cs2 = 1/(3(1+R)), and k Θ₀/(1+R) = k×3cs2×Θ₀)
        };

        let (k1t, k1v) = rhs(theta0, vb);
        let (k2t, k2v) = rhs(theta0 + 0.5*d_eta*k1t, vb + 0.5*d_eta*k1v);
        let (k3t, k3v) = rhs(theta0 + 0.5*d_eta*k2t, vb + 0.5*d_eta*k2v);
        let (k4t, k4v) = rhs(theta0 + d_eta*k3t, vb + d_eta*k3v);

        theta0 += d_eta * (k1t + 2.0*k2t + 2.0*k3t + k4t) / 6.0;
        vb += d_eta * (k1v + 2.0*k2v + 2.0*k3v + k4v) / 6.0;

        eta_hist.push((step + 1) as f64 * d_eta);
        t0_hist.push(theta0);
        vb_hist.push(vb);
    }

    (eta_hist, t0_hist, vb_hist)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_r_ratio() {
        // At a=1: R ≈ (3/4)(0.049/6.5e-5) ≈ 565
        let r = baryon_photon_ratio(0.049, 6.5e-5, 1.0);
        assert!(r > 500.0 && r < 700.0, "R(a=1) = {:.1}", r);
    }

    #[test]
    fn test_sound_speed_pure_radiation() {
        // R = 0: c_s = 1/√3 ≈ 0.577
        let cs = sound_speed(0.0);
        assert!((cs - 1.0/3.0_f64.sqrt()).abs() < 1e-14);
    }

    #[test]
    fn test_sound_speed_recombination() {
        // R ≈ 0.6: c_s = 1/√(3×1.6) ≈ 0.456
        let cs = sound_speed(0.6);
        let expected = 1.0 / (3.0 * 1.6_f64).sqrt();
        assert!((cs - expected).abs() < 1e-14, "c_s = {:.4}", cs);
    }

    #[test]
    fn test_momentum_conservation() {
        let f1 = 0.01; let vb = 0.005; let kd = 50.0; let r = 0.6;
        let c_photon_1 = -kd * (f1 - vb); // = −0.25
        let c_baryon = baryon_collision_term(vb, f1, kd, 1.0/r); // = R⁻¹ κ̇(v_γ-v_b)
        let residual = momentum_conservation_check(c_photon_1, c_baryon, r);
        assert!(residual < 1e-14, "Momentum: {:.2e}", residual);
    }

    #[test]
    fn test_tca_oscillation_frequency() {
        // Oscillation period: T = 2π/(k c_s)
        // For k=0.1, R=0: T = 2π/(0.1/√3) ≈ 109
        let k = 0.1;
        let omega = oscillation_frequency(k, 0.0);
        let period = 2.0 * std::f64::consts::PI / omega;
        assert!((period - 108.8).abs() < 1.0, "Period = {:.1}", period);
    }

    #[test]
    fn test_tca_oscillator_runs() {
        let (eta, t0, vb) = evolve_tca_oscillator(1.0, 0.0, 0.1, 0.0, 0.0, 200.0, 10000);
        // Should oscillate with period ~109 and not blow up
        let max_t = t0.iter().fold(0.0f64, |m, &v| m.max(v.abs()));
        assert!(max_t < 2.0, "TCA oscillator blew up: max = {:.2e}", max_t);
        assert!(eta.len() == 10001);
    }

    #[test]
    fn test_tca_sound_speed_correct() {
        // After one quarter period, Θ₀ should have transferred to v_b
        let k = 0.1;
        let cs = sound_speed(0.0);
        let quarter = std::f64::consts::PI / (2.0 * k * cs);
        let (_, t0, vb) = evolve_tca_oscillator(1.0, 0.0, k, 0.0, 0.0, quarter, 5000);
        // At quarter period: Θ₀ ≈ 0, v_b ≈ max
        assert!(t0.last().unwrap().abs() < 0.15,
            "Quarter period Θ₀ = {:.4} (expect ~0)", t0.last().unwrap());
    }

    #[test]
    fn test_baryon_euler_hubble_drag() {
        // Pure Hubble drag: v̇_b = −aH × v_b
        let rhs = baryon_euler_rhs(0.01, 0.0, 0.0, 100.0, 0.0, 0.0, 0.0, 0.0);
        assert!((rhs + 1.0).abs() < 1e-14, "Hubble drag: {:.4}", rhs);
    }
}
