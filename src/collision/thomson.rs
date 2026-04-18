// Thomson scattering collision operator for photon intensity.
// BC-04: C^(γ)_ℓ = −κ̇(F_ℓ − S_ℓ) with ℓ-dependent source.
//
// Source structure:
//   S₀ = F₀  (energy conservation → C₀ = 0)
//   S₁ = v_b (baryon velocity coupling)
//   S₂ = Π/10 (polarisation source, Π = F₂ + G₀ + G₂)
//   S_ℓ = 0 for ℓ ≥ 3 (pure damping)
//
// The Θ⁴ Thomson bridge (Paper V, Theorem 1):
//   I_{ab} = c_ξ ⟨Θ⁴ e_{⟨a}e_{b⟩}⟩
//   Coefficient: c_ξ = C(4,2) = 6 from the binomial expansion.

/// Compute the Thomson collision term for the photon intensity hierarchy.
///
/// Returns C_ℓ for ℓ = 0, 1, ..., ℓ_max.
///
/// # Arguments
/// * `f_ell` - Photon intensity multipoles [F₀, F₁, ..., F_{ℓ_max}]
/// * `kappa_dot` - Thomson scattering rate κ̇ = n_e σ_T a [Mpc⁻¹]
/// * `v_b` - Baryon velocity (monopole of baryon momentum)
/// * `pol_source` - Polarisation source Π = F₂ + G₀ + G₂
pub(crate) fn thomson_collision(
    f_ell: &[f64],
    kappa_dot: f64,
    v_b: f64,
    pol_source: f64,
) -> Vec<f64> {
    let n = f_ell.len();
    let mut c = vec![0.0; n];

    for ell in 0..n {
        let source = match ell {
            0 => f_ell[0],               // C₀ = −κ̇(F₀ − F₀) = 0 exactly
            1 => v_b,                    // C₁ = −κ̇(F₁ − v_b)
            2 => pol_source / 10.0,      // C₂ = −κ̇(F₂ − Π/10)
            _ => 0.0,                    // ℓ ≥ 3: pure damping
        };
        c[ell] = -kappa_dot * (f_ell[ell] - source);
    }
    c
}

/// Thomson collision term WITHOUT polarisation (Π = 0).
///
/// Useful for testing or when polarisation is not tracked.
pub(crate) fn thomson_collision_no_pol(
    f_ell: &[f64],
    kappa_dot: f64,
    v_b: f64,
) -> Vec<f64> {
    thomson_collision(f_ell, kappa_dot, v_b, 0.0)
}

/// Compute the photon momentum transfer rate to baryons.
///
/// The photon ℓ=1 collision term drives baryon velocity:
///   C^(γ)_1 = −κ̇(F₁ − v_b)
///
/// The baryon receives the negative: (4ρ_γ)/(3ρ_b) × κ̇(v_b − F₁)
pub(crate) fn photon_momentum_transfer(f1: f64, kappa_dot: f64, v_b: f64) -> f64 {
    -kappa_dot * (f1 - v_b)
}

/// Θ⁴ Thomson bridge coefficient.
///
/// From Paper V, Theorem 1: the exact nonlinear Thomson source for the
/// quadrupole involves the fourth power of the temperature:
///   I_{ab} = c_ξ ⟨Θ⁴ e_{⟨a}e_{b⟩}⟩
///
/// The coefficient c_ξ = C(4,2) = 6 from the binomial expansion of
/// (1 + ΔT/T)⁴ = Σ C(4,k)(ΔT/T)^k.
///
/// At linear order, the Θ⁴ bridge reduces to the standard (1/10)Π source.
/// The nonlinear correction is O(ΔT/T)² ~ 10⁻¹⁰ and enters through
/// the quadrupole-squared terms.
pub(crate) const THETA4_BRIDGE_COEFFICIENT: f64 = 6.0;

/// Compute the nonlinear Θ⁴ Thomson quadrupole source.
///
/// At second order:
///   S₂^{NL} = (1/10)Π + (6/10) × Σ_{ℓ₁ℓ₂} CG × F_{ℓ₁}F_{ℓ₂}
///
/// For the BASS solver, this enters through the T_eff formalism
/// where the quadrupole-squared coupling is exact.
pub(crate) fn theta4_quadrupole_source(
    f2: f64,
    pol_source: f64,
    f_monopole_sq: f64, // ⟨Θ²⟩ ~ F₀² + ...
) -> f64 {
    // Linear: (1/10)Π
    let linear = pol_source / 10.0;
    // Nonlinear: (6/10) × ⟨Θ²⟩ × (1/5) (angular projection)
    let nonlinear = (THETA4_BRIDGE_COEFFICIENT / 10.0) * f_monopole_sq / 5.0;
    linear + nonlinear
}

/// Verify energy conservation: C₀ must be exactly zero.
pub(crate) fn verify_energy_conservation(c_ell: &[f64]) -> f64 {
    if c_ell.is_empty() { return 0.0; }
    c_ell[0].abs()
}

/// Verify momentum conservation for the photon-baryon system.
///
/// Total momentum: C^(γ)₁ + (3ρ_b)/(4ρ_γ) × C^(b) = 0
///
/// Returns the residual (should be ~0).
pub(crate) fn verify_momentum_conservation(
    c_photon_1: f64,
    c_baryon: f64,
    r_ratio: f64, // R = 3ρ_b/(4ρ_γ)
) -> f64 {
    (c_photon_1 + r_ratio * c_baryon).abs()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_energy_conservation_exact() {
        let f = vec![1.0, 0.5, 0.1, 0.01, 0.001];
        let c = thomson_collision(&f, 100.0, 0.0, 0.0);
        assert!(c[0].abs() < 1e-15, "C₀ = {:.2e} (must be 0)", c[0]);
    }

    #[test]
    fn test_dipole_coupling() {
        let f = vec![0.0, 0.01, 0.0];
        let v_b = 0.005;
        let c = thomson_collision(&f, 50.0, v_b, 0.0);
        // C₁ = −50(0.01 − 0.005) = −0.25
        assert!((c[1] + 0.25).abs() < 1e-14, "C₁ = {:.6}", c[1]);
    }

    #[test]
    fn test_quadrupole_with_polarisation() {
        let f = vec![0.0, 0.0, 0.1, 0.0];
        let pol = 0.5; // Π = F₂ + G₀ + G₂
        let c = thomson_collision(&f, 100.0, 0.0, pol);
        // C₂ = −100(0.1 − 0.5/10) = −100(0.1 − 0.05) = −5
        assert!((c[2] + 5.0).abs() < 1e-12, "C₂ = {:.6}", c[2]);
    }

    #[test]
    fn test_pure_damping_high_ell() {
        let f = vec![0.0, 0.0, 0.0, 0.05, 0.02, 0.01];
        let c = thomson_collision(&f, 100.0, 0.0, 0.0);
        // ℓ ≥ 3: C_ℓ = −κ̇ F_ℓ
        assert!((c[3] + 5.0).abs() < 1e-12);  // −100 × 0.05
        assert!((c[4] + 2.0).abs() < 1e-12);  // −100 × 0.02
        assert!((c[5] + 1.0).abs() < 1e-12);  // −100 × 0.01
    }

    #[test]
    fn test_no_scattering_zero_kappa() {
        let f = vec![1.0, 0.5, 0.1];
        let c = thomson_collision(&f, 0.0, 0.0, 0.0);
        for &ci in &c { assert!(ci.abs() < 1e-15); }
    }

    #[test]
    fn test_momentum_conservation_photon_baryon() {
        // Photon C₁ = −κ̇(F₁ − v_b)
        // Baryon C_b = R⁻¹ κ̇(v_γ − v_b) = R⁻¹ κ̇(F₁ − v_b)
        // Conservation: C₁ + R × C_b = −κ̇(F₁−v_b) + κ̇(F₁−v_b) = 0 ✓
        let f1 = 0.01; let v_b = 0.005; let kd = 50.0; let r = 0.6;
        let c1 = photon_momentum_transfer(f1, kd, v_b); // = −50(0.01−0.005) = −0.25
        let cb = kd * (f1 - v_b) / r; // = 50×0.005/0.6 = +0.4167
        let residual = verify_momentum_conservation(c1, cb, r);
        assert!(residual < 1e-14, "Momentum residual: {:.2e}", residual);
    }

    #[test]
    fn test_theta4_coefficient() {
        assert_eq!(THETA4_BRIDGE_COEFFICIENT, 6.0);
    }

    #[test]
    fn test_theta4_linear_limit() {
        // At linear order (f_monopole_sq = 0): reduces to (1/10)Π
        let s = theta4_quadrupole_source(0.1, 0.5, 0.0);
        assert!((s - 0.05).abs() < 1e-15, "Linear limit: {:.6}", s);
    }
}
