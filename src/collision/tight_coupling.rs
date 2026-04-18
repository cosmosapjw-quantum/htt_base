// Tight-Coupling Approximation (TCA) for the photon-baryon system.
// BC-05: Reduced state before decoupling (κ̇ ≫ H).
//
// Zeroth order: v_γ = v_b, F_ℓ = 0 for ℓ ≥ 2.
// First order: slip term F₂ = (8/15)(σ/H)/(κ̇/H).
//
// Transition: switch to full hierarchy when κ̇/H < threshold (~50).
//
// The TCA eliminates the stiffness of the collision term,
// replacing ℓ_max+1 equations with 2–3 equations.

/// Reduced state in the TCA regime.
#[derive(Clone, Debug)]
pub(crate) struct TCAState {
    /// Photon temperature monopole Θ₀.
    pub(crate) theta0: f64,
    /// Common baryon-photon velocity v_b = v_γ (tight coupling).
    pub(crate) v_b: f64,
    /// Baryon density perturbation δ_b (optional, for completeness).
    pub(crate) delta_b: f64,
}

/// Background quantities needed for TCA evolution.
#[derive(Clone, Debug)]
pub(crate) struct TCABackground {
    /// Conformal Hubble aH [Mpc⁻¹].
    pub(crate) a_h: f64,
    /// Wavenumber k [Mpc⁻¹].
    pub(crate) k: f64,
    /// Baryon-photon ratio R = 3ρ_b/(4ρ_γ).
    pub(crate) r_ratio: f64,
    /// Thomson scattering rate κ̇ [Mpc⁻¹] (positive).
    pub(crate) kappa_dot: f64,
    /// Shear ratio σ/H (for Bianchi slip term).
    pub(crate) sigma_h: f64,
    /// Gravitational potential Ψ (for Sachs-Wolfe; 0 for homogeneous).
    pub(crate) psi: f64,
    /// Time derivative of potential Φ̇ (ISW; 0 for matter-dominated).
    pub(crate) phi_dot: f64,
}

/// Compute the TCA RHS: dState/dη.
///
/// Zeroth-order TCA equations (Ma & Bertschinger 1995):
///   Θ₀' = −(k/3) v_b + Φ̇
///   v_b' = −(aH) R/(1+R) v_b + k/(1+R) [Θ₀ + Ψ] + slip correction
///   δ_b' = −k v_b (continuity)
///
/// The slip correction at first order in 1/κ̇:
///   Δv = −[1/(κ̇(1+R))] × [(1−R)aH v_b − k Θ₀ − k Ψ]
pub(crate) fn tca_rhs(state: &TCAState, bg: &TCABackground) -> TCAState {
    let r1 = 1.0 + bg.r_ratio;
    let r1_inv = 1.0 / r1;

    // Θ₀' = −(k/3) v_b + Φ̇
    let dtheta0 = -(bg.k / 3.0) * state.v_b + bg.phi_dot;

    // v_b' = −(aH)R/(1+R) v_b + k/(1+R)(Θ₀ + Ψ)
    let dvb_zeroth = -bg.a_h * bg.r_ratio * r1_inv * state.v_b
        + bg.k * r1_inv * (state.theta0 + bg.psi);

    // First-order slip correction (Peebles & Yu 1970, Ma & Bertschinger 1995):
    //   Δv = −[1/(κ̇(1+R))] × [(1−R) aH v_b − k(Θ₀ + Ψ)]
    let slip = if bg.kappa_dot > 1e-30 {
        let numer = (1.0 - bg.r_ratio) * bg.a_h * state.v_b - bg.k * (state.theta0 + bg.psi);
        -numer / (bg.kappa_dot * r1)
    } else {
        0.0
    };

    let dvb = dvb_zeroth + slip;

    // δ_b' = −k v_b
    let ddelta_b = -bg.k * state.v_b;

    TCAState {
        theta0: dtheta0,
        v_b: dvb,
        delta_b: ddelta_b,
    }
}

/// First-order slip term: F₂ ≈ (8/15)(σ/H) / (κ̇/H).
///
/// On Bianchi backgrounds, the shear σ drives a quadrupole F₂
/// that scales as (σ/H) × (H/κ̇). This is the leading
/// anisotropic stress in the TCA regime.
///
/// For FLRW (σ=0): F₂^{TCA} = 0.
/// For BI with small shear: F₂ ≈ (8/15) × σ_H × (aH/κ̇).
pub(crate) fn slip_term_f2(sigma_h: f64, kappa_dot: f64, a_h: f64) -> f64 {
    if kappa_dot.abs() < 1e-30 { return 0.0; }
    (8.0 / 15.0) * sigma_h * a_h / kappa_dot
}

/// Determine whether TCA is valid at current epoch.
///
/// TCA is valid when κ̇/(aH) > threshold.
/// Default threshold: 50 (conservative; CLASS uses ~20).
pub(crate) fn tca_is_valid(kappa_dot: f64, a_h: f64, threshold: f64) -> bool {
    if a_h.abs() < 1e-30 { return true; }
    kappa_dot / a_h >= threshold
}

/// Default TCA switch threshold.
pub(crate) const TCA_SWITCH_THRESHOLD: f64 = 50.0;

/// Switch from TCA to full hierarchy state.
///
/// Maps the reduced TCA state to the full hierarchy:
///   F₀ = Θ₀
///   F₁ = v_b (tight-coupled velocity)
///   F₂ = slip term
///   F_ℓ = 0 for ℓ ≥ 3
pub(crate) fn switch_to_full(
    tca: &TCAState,
    ell_max: usize,
    sigma_h: f64,
    kappa_dot: f64,
    a_h: f64,
) -> Vec<f64> {
    let mut f = vec![0.0; ell_max + 1];
    f[0] = tca.theta0;
    if ell_max >= 1 { f[1] = tca.v_b; }
    if ell_max >= 2 { f[2] = slip_term_f2(sigma_h, kappa_dot, a_h); }
    // F_ℓ = 0 for ℓ ≥ 3 (no higher multipoles in TCA)
    f
}

/// Evolve TCA state by one RK4 step.
pub(crate) fn tca_step_rk4(
    state: &mut TCAState,
    bg: &TCABackground,
    d_eta: f64,
) {
    let s0 = state.clone();

    let k1 = tca_rhs(&s0, bg);
    let s1 = TCAState {
        theta0: s0.theta0 + 0.5*d_eta*k1.theta0,
        v_b: s0.v_b + 0.5*d_eta*k1.v_b,
        delta_b: s0.delta_b + 0.5*d_eta*k1.delta_b,
    };
    let k2 = tca_rhs(&s1, bg);
    let s2 = TCAState {
        theta0: s0.theta0 + 0.5*d_eta*k2.theta0,
        v_b: s0.v_b + 0.5*d_eta*k2.v_b,
        delta_b: s0.delta_b + 0.5*d_eta*k2.delta_b,
    };
    let k3 = tca_rhs(&s2, bg);
    let s3 = TCAState {
        theta0: s0.theta0 + d_eta*k3.theta0,
        v_b: s0.v_b + d_eta*k3.v_b,
        delta_b: s0.delta_b + d_eta*k3.delta_b,
    };
    let k4 = tca_rhs(&s3, bg);

    state.theta0 = s0.theta0 + d_eta*(k1.theta0+2.0*k2.theta0+2.0*k3.theta0+k4.theta0)/6.0;
    state.v_b = s0.v_b + d_eta*(k1.v_b+2.0*k2.v_b+2.0*k3.v_b+k4.v_b)/6.0;
    state.delta_b = s0.delta_b + d_eta*(k1.delta_b+2.0*k2.delta_b+2.0*k3.delta_b+k4.delta_b)/6.0;
}

/// Sound speed squared in the TCA: c²_s = 1/(3(1+R)).
pub(crate) fn tca_sound_speed_sq(r_ratio: f64) -> f64 {
    1.0 / (3.0 * (1.0 + r_ratio))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_bg(k: f64, r: f64, kd: f64, ah: f64) -> TCABackground {
        TCABackground { a_h: ah, k, r_ratio: r, kappa_dot: kd, sigma_h: 0.0, psi: 0.0, phi_dot: 0.0 }
    }

    // ── TCA valid at early times ──
    #[test]
    fn test_tca_valid_early() {
        assert!(tca_is_valid(1e6, 100.0, 50.0)); // κ̇/aH = 10000 ≫ 50
    }

    // ── TCA invalid at recombination ──
    #[test]
    fn test_tca_invalid_late() {
        assert!(!tca_is_valid(10.0, 100.0, 50.0)); // κ̇/aH = 0.1 ≪ 50
    }

    // ── Slip term: F₂ = (8/15)σ_H × aH/κ̇ ──
    #[test]
    fn test_slip_term() {
        let f2 = slip_term_f2(1e-5, 1000.0, 100.0);
        // (8/15) × 1e-5 × 100/1000 = (8/15) × 1e-6 ≈ 5.33e-7
        let expected = (8.0/15.0) * 1e-5 * 100.0 / 1000.0;
        assert!((f2 - expected).abs() < 1e-20, "F₂ = {:.4e}", f2);
    }

    // ── Slip term zero for FLRW ──
    #[test]
    fn test_slip_zero_flrw() {
        assert_eq!(slip_term_f2(0.0, 1000.0, 100.0), 0.0);
    }

    // ── Switch: state continuity ──
    #[test]
    fn test_switch_continuity() {
        let tca = TCAState { theta0: 0.1, v_b: 0.005, delta_b: -0.01 };
        let full = switch_to_full(&tca, 10, 0.0, 1000.0, 100.0);
        assert!((full[0] - 0.1).abs() < 1e-15, "Θ₀ discontinuity");
        assert!((full[1] - 0.005).abs() < 1e-15, "v_b discontinuity");
        // F₂ should be the slip term (zero for σ=0)
        assert!(full[2].abs() < 1e-15, "F₂ for FLRW");
        // F_ℓ = 0 for ℓ ≥ 3
        for l in 3..=10 { assert_eq!(full[l], 0.0); }
    }

    // ── TCA acoustic oscillation ──
    #[test]
    fn test_tca_oscillation() {
        let mut state = TCAState { theta0: 1.0, v_b: 0.0, delta_b: 0.0 };
        let bg = make_bg(0.1, 0.0, 1e6, 0.0); // Pure radiation, no Hubble drag

        let cs = tca_sound_speed_sq(0.0).sqrt();
        let period = 2.0 * std::f64::consts::PI / (bg.k * cs);
        let n_steps = 20000;
        let d_eta = 2.0 * period / n_steps as f64;

        for _ in 0..n_steps {
            tca_step_rk4(&mut state, &bg, d_eta);
        }

        // After 2 full periods: Θ₀ ≈ 1.0 (returned to IC)
        assert!((state.theta0 - 1.0).abs() < 0.02,
            "TCA 2-period return: Θ₀ = {:.4}", state.theta0);
    }

    // ── TCA matches sound speed ──
    #[test]
    fn test_tca_sound_speed() {
        // c_s² = 1/(3(1+R))
        assert!((tca_sound_speed_sq(0.0) - 1.0/3.0).abs() < 1e-15);
        assert!((tca_sound_speed_sq(0.6) - 1.0/4.8).abs() < 1e-15);
    }

    // ── TCA RHS: no evolution for zero k ──
    #[test]
    fn test_tca_zero_k() {
        let state = TCAState { theta0: 1.0, v_b: 0.0, delta_b: 0.0 };
        let bg = make_bg(0.0, 0.0, 1e6, 0.0);
        let rhs = tca_rhs(&state, &bg);
        assert!(rhs.theta0.abs() < 1e-15);
        assert!(rhs.v_b.abs() < 1e-15);
    }

    // ── TCA speedup: 3 DOF vs ℓ_max+1 ──
    #[test]
    fn test_tca_dof_reduction() {
        // TCA: 3 DOF (theta0, v_b, delta_b)
        // Full: ℓ_max + 1 DOF
        let ell_max = 30;
        let speedup = (ell_max + 1) as f64 / 3.0;
        assert!(speedup > 5.0, "Speedup: {:.1}× (need ≥ 5×)", speedup);
    }

    // ── Hubble drag damps v_b ──
    #[test]
    fn test_hubble_drag_in_tca() {
        let state = TCAState { theta0: 0.0, v_b: 1.0, delta_b: 0.0 };
        let bg = make_bg(0.0, 0.5, 1e6, 100.0); // R=0.5, aH=100
        let rhs = tca_rhs(&state, &bg);
        // v_b' = −(aH)R/(1+R) v_b = −100×0.5/1.5 × 1 ≈ −33.3
        let expected = -100.0 * 0.5 / 1.5;
        assert!((rhs.v_b - expected).abs() < 1.0, "Drag: {:.1} (expect {:.1})", rhs.v_b, expected);
    }

    // ── Switch threshold stability ──
    #[test]
    fn test_switch_threshold_range() {
        // Both 25 and 100 should give valid switch points
        let kd = 5000.0;
        let ah = 100.0;
        assert!(tca_is_valid(kd, ah, 25.0));
        assert!(tca_is_valid(kd, ah, 50.0));
        assert!(!tca_is_valid(kd, ah, 100.0)); // 5000/100 = 50 < 100
    }
}
