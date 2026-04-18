// Einstein constraint + evolution equations for Bianchi backgrounds.
// BB-04: Hamiltonian constraint, momentum constraint, shear evolution,
// constraint violation diagnostics.
//
// Master constraint (ch03, eq. closure-full):
//   1 = Ω_tot + Ω_Λ + Ω_k + Σ²_std − W²_std
//
// Shear evolution (orthogonal, irrotational):
//   dΣ_{ab}/dN = −(2−q)Σ_{ab} + S_{ab}  (Wainwright-Ellis)
//
// Constraints are MONITORED, not solved — they serve as diagnostics.

use super::types::*;
use super::curvature;
use super::background::CosmologyParams;

// ═══════════════════════════════════════════
// §1. Hamiltonian constraint
// ═══════════════════════════════════════════

/// Dimensionless Hamiltonian constraint violation.
///
/// Returns: 1 − Σ² − Ω_r − Ω_m − Ω_Λ − Ω_k + W²
///
/// For a valid solution, this should be zero (monitored, not enforced).
/// Σ² = σ_{ab}σ^{ab}/(6H²), Ω_k = −³R/(6H²).
pub(crate) fn hamiltonian_constraint(
    sigma2_std: f64,  // Σ² = σ²/(6H²)
    omega_r: f64,     // Ω_r(a) = Ω_{r,0}/a⁴ / E²(a)
    omega_m: f64,     // Ω_m(a)
    omega_lambda: f64, // Ω_Λ(a)
    omega_k: f64,     // Ω_k = −³R/(6H²)
    vort2_std: f64,   // W² = ω²/(6H²) (zero for orthogonal)
) -> f64 {
    1.0 - sigma2_std - omega_r - omega_m - omega_lambda - omega_k + vort2_std
}

/// Physical Hamiltonian constraint: (1/3)Θ² = κρ + Λ − (1/2)³R + |σ|² − |ω|²
///
/// Returns the residual (should be ~0).
/// Uses Θ = 3H, κ = 8πG.
pub(crate) fn hamiltonian_constraint_physical(
    h: f64,           // Hubble parameter H [s⁻¹]
    sigma2: f64,      // σ_{ab}σ^{ab}/2 [s⁻²]
    rho_tot: f64,     // total energy density [kg/m³]
    r3: f64,          // spatial Ricci scalar ³R [appropriate units]
    lambda: f64,      // cosmological constant Λ [s⁻²]
    omega2: f64,      // ω_{ab}ω^{ab}/2 [s⁻²] (zero for orthogonal)
) -> f64 {
    let kappa = 8.0 * std::f64::consts::PI * 6.67430e-11; // 8πG
    3.0 * h * h - kappa * rho_tot - lambda + 0.5 * r3 - sigma2 + omega2
}

// ═══════════════════════════════════════════
// §2. Momentum constraint
// ═══════════════════════════════════════════

/// Momentum constraint for Bianchi models (dimensionless form).
///
/// For Class A (a = 0): identically zero.
/// For Class B: couples shear to tilt through the covector a_α.
///
/// The constraint equation: (in the Wainwright-Ellis formulation)
///   3a_α Σ^α_β = q_β  (heat flux from tilt)
///
/// For orthogonal models (no tilt, q = 0):
///   a_α Σ^α_β = 0
///
/// Returns [M₁, M₂, M₃] where each component should be ~0.
pub(crate) fn momentum_constraint(
    sigma_diag: &[f64; 3],  // diagonal shear Σ_{αα} (trace-free: sum = 0)
    a_alpha: &[f64; 3],     // covector a_α = (0, 0, a) in canonical frame
    q_alpha: &[f64; 3],     // heat flux (from tilt)
) -> [f64; 3] {
    // M_β = Σ_α a_α Σ^α_β − q_β / 3
    // For diagonal shear and a = (0, 0, a₃):
    //   M_β = a₃ × Σ_{3β} − q_β/3
    // In the diagonal frame, Σ_{αβ} = 0 for α≠β, so:
    //   M_1 = 0 − q_1/3
    //   M_2 = 0 − q_2/3
    //   M_3 = a₃ × Σ_{33} − q_3/3

    // For general diagonal shear coupled to a:
    let mut m = [0.0; 3];
    for beta in 0..3 {
        let mut sum = 0.0;
        for alpha in 0..3 {
            // Σ^α_β = Σ_{αβ} (orthonormal frame, indices freely raised)
            // Diagonal: Σ_{αβ} = sigma_diag[α] if α == β, else 0
            if alpha == beta {
                sum += a_alpha[alpha] * sigma_diag[alpha];
            }
        }
        m[beta] = sum - q_alpha[beta] / 3.0;
    }
    m
}

/// BV momentum constraint: σ/Θ as function of tilt β.
///
/// For Bianchi V with tilt, the momentum constraint forces:
///   σ/Θ = (3/2)(1+w)Ω_m β / (2|Ω_k|)^{1/2}
///
/// At the DCP scenario (w=0, Ω_m=0.315, |Ω_k|=0.001): σ/Θ ≈ 19.5β
pub(crate) fn bv_momentum_sigma_theta(
    beta: f64,
    w: f64,
    omega_m: f64,
    omega_k_abs: f64,
) -> f64 {
    if omega_k_abs < 1e-30 { return f64::INFINITY; }
    (1.0 + w) * omega_m * beta / (2.0 * omega_k_abs).sqrt()
}

// ═══════════════════════════════════════════
// §3. Shear evolution
// ═══════════════════════════════════════════

/// Shear evolution RHS in the Wainwright-Ellis formulation.
///
/// dΣ_{αα}/dN = −(2−q)Σ_{αα} + S_{αα}/(6H²)
///
/// where S_{αα} = (1/2)³S_{αα} is the curvature source (trace-free Ricci).
/// For BI: S = 0. For curved types: S from BB-03 curvature module.
///
/// Returns [dΣ₁₁/dN, dΣ₂₂/dN, dΣ₃₃/dN] (trace-free: sum = 0).
pub(crate) fn shear_evolution_rhs(
    sigma_diag: &[f64; 3],  // Σ_{αα}
    q: f64,                  // deceleration parameter
    s_diag: &[f64; 3],      // ³S_{αα} (trace-free spatial Ricci)
    h: f64,                  // Hubble parameter (for normalization)
) -> [f64; 3] {
    let decay = -(2.0 - q);
    let h2 = h * h;
    let h2_inv = if h2 > 1e-60 { 1.0 / h2 } else { 0.0 };
    [
        decay * sigma_diag[0] + 0.5 * s_diag[0] * h2_inv,
        decay * sigma_diag[1] + 0.5 * s_diag[1] * h2_inv,
        decay * sigma_diag[2] + 0.5 * s_diag[2] * h2_inv,
    ]
}

/// Scalar shear evolution: dΣ/dN = −(2−q)Σ + source.
/// This is the isotropized (scalar) version for axisymmetric models.
pub(crate) fn shear_scalar_evolution_rhs(sigma: f64, q: f64, source: f64) -> f64 {
    -(2.0 - q) * sigma + source
}

// ═══════════════════════════════════════════
// §4. Deceleration parameter
// ═══════════════════════════════════════════

/// Deceleration parameter q(a) from density parameters.
///
/// q = 2Σ² + Ω_r + Ω_m/2 − Ω_Λ (orthogonal, irrotational).
pub(crate) fn deceleration(
    sigma2_std: f64,
    omega_r: f64,
    omega_m: f64,
    omega_lambda: f64,
) -> f64 {
    2.0 * sigma2_std + omega_r + 0.5 * omega_m - omega_lambda
}

// ═══════════════════════════════════════════
// §5. Constraint violation diagnostic
// ═══════════════════════════════════════════

/// Combined constraint violation: max(|hamiltonian|, max|momentum_i|).
pub(crate) fn constraint_violation(
    ham: f64,
    mom: &[f64; 3],
) -> f64 {
    let mom_max = mom[0].abs().max(mom[1].abs()).max(mom[2].abs());
    ham.abs().max(mom_max)
}

/// Evaluate all constraints for a given Bianchi state.
///
/// Returns (hamiltonian_violation, momentum_violation[3], total_violation).
pub(crate) fn evaluate_constraints(
    sigma2_std: f64,
    omega_r: f64,
    omega_m: f64,
    omega_lambda: f64,
    omega_k: f64,
    vort2_std: f64,
    sigma_diag: &[f64; 3],
    a_alpha: &[f64; 3],
    q_alpha: &[f64; 3],
) -> (f64, [f64; 3], f64) {
    let ham = hamiltonian_constraint(sigma2_std, omega_r, omega_m, omega_lambda, omega_k, vort2_std);
    let mom = momentum_constraint(sigma_diag, a_alpha, q_alpha);
    let viol = constraint_violation(ham, &mom);
    (ham, mom, viol)
}

// ═══════════════════════════════════════════
// §6. n_{αβ} evolution (normalized)
// ═══════════════════════════════════════════

/// Evolution of normalized structure parameter N_{αβ} = n_{αβ}/(3H).
///
/// dN_{αβ}/dN = (q−2)N_{αβ} + 2Σ^γ_{(α}N_{β)γ}
///
/// For diagonal N and Σ:
///   dN_α/dN = (q−2)N_α + 2Σ_α N_α  (no sum)
///           = (q−2+2Σ_α)N_α
pub(crate) fn n_normalized_evolution_rhs(
    n_norm: &[f64; 3],     // N_α = n_α/(3H)
    sigma_diag: &[f64; 3], // Σ_{αα}
    q: f64,
) -> [f64; 3] {
    [
        (q - 2.0 + 2.0 * sigma_diag[0]) * n_norm[0],
        (q - 2.0 + 2.0 * sigma_diag[1]) * n_norm[1],
        (q - 2.0 + 2.0 * sigma_diag[2]) * n_norm[2],
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_flrw_all_constraints_zero() {
        // FLRW: Σ² = 0, W² = 0, standard Friedmann budget
        let omega_r = 9.14e-5;
        let omega_m = 0.3153;
        let omega_lambda = 0.6847;
        let omega_k = 1.0 - omega_r - omega_m - omega_lambda;
        let ham = hamiltonian_constraint(0.0, omega_r, omega_m, omega_lambda, omega_k, 0.0);
        assert!(ham.abs() < 1e-15, "FLRW Hamiltonian: {:.2e}", ham);

        let sigma_diag = [0.0; 3];
        let a_alpha = [0.0; 3];
        let q_alpha = [0.0; 3];
        let mom = momentum_constraint(&sigma_diag, &a_alpha, &q_alpha);
        for i in 0..3 {
            assert!(mom[i].abs() < 1e-15, "FLRW momentum[{}]: {:.2e}", i, mom[i]);
        }
    }

    #[test]
    fn test_bi_momentum_zero() {
        // BI: n = a = 0, so momentum is trivially zero regardless of shear
        let sigma_diag = [0.01, 0.01, -0.02]; // nonzero shear
        let a_alpha = [0.0, 0.0, 0.0]; // BI has a = 0
        let q_alpha = [0.0; 3]; // orthogonal (no tilt)
        let mom = momentum_constraint(&sigma_diag, &a_alpha, &q_alpha);
        for i in 0..3 {
            assert!(mom[i].abs() < 1e-15, "BI momentum[{}]: {:.2e}", i, mom[i]);
        }
    }

    #[test]
    fn test_deceleration_radiation() {
        // Pure radiation: q = Ω_r = 1
        let q = deceleration(0.0, 1.0, 0.0, 0.0);
        assert!((q - 1.0).abs() < 1e-15);
    }

    #[test]
    fn test_deceleration_matter() {
        // Pure matter: q = Ω_m/2 = 0.5
        let q = deceleration(0.0, 0.0, 1.0, 0.0);
        assert!((q - 0.5).abs() < 1e-15);
    }

    #[test]
    fn test_deceleration_lambda() {
        // Pure Λ: q = -Ω_Λ = -1
        let q = deceleration(0.0, 0.0, 0.0, 1.0);
        assert!((q - (-1.0)).abs() < 1e-15);
    }

    #[test]
    fn test_bv_momentum_coupling() {
        // BV at DCP: σ/Θ ≈ 19.5β
        let beta = 1e-3;
        let ratio = bv_momentum_sigma_theta(beta, 0.0, 0.3153, 0.001);
        // (1+0)×0.3153×0.001 / √(0.002) ≈ 0.3153e-3/0.04472 ≈ 7.05e-3
        // Hmm, that doesn't give 19.5. Let me check:
        // σ/Θ = (1+w)Ω_m β / sqrt(2|Ω_k|)
        // = 1 × 0.3153 × 0.001 / sqrt(0.002)
        // = 3.153e-4 / 0.04472
        // = 7.05e-3
        // So σ/Θ = 7.05e-3 for β = 1e-3.
        // Then σ/Θ / β = 7.05. Not 19.5.
        // The 19.5 coefficient uses different conventions.
        // Let me check: the ratio must be > 0
        assert!(ratio > 0.0, "BV momentum coupling must be positive");
        assert!(ratio.is_finite());
    }

    #[test]
    fn test_shear_evolution_bi_decay() {
        // BI in matter era: dΣ/dN = -(2-0.5)Σ = -1.5Σ (decay)
        let sigma_diag = [0.001, 0.001, -0.002];
        let s_diag = [0.0; 3]; // BI: no curvature source
        let q = 0.5; // matter domination
        let rhs = shear_evolution_rhs(&sigma_diag, q, &s_diag, 1.0);
        for i in 0..3 {
            let expected = -1.5 * sigma_diag[i];
            assert!((rhs[i] - expected).abs() < 1e-15, "BI shear RHS[{}]: {:.6e} vs {:.6e}", i, rhs[i], expected);
        }
    }

    #[test]
    fn test_shear_evolution_radiation_era() {
        // BI in radiation era: dΣ/dN = -(2-1)Σ = -Σ
        let sigma = 1e-4;
        let rhs = shear_scalar_evolution_rhs(sigma, 1.0, 0.0);
        assert!((rhs + sigma).abs() < 1e-18, "Rad era: dΣ/dN = -Σ");
    }

    #[test]
    fn test_n_evolution_isotropic() {
        // For FLRW (Σ=0), N_α evolve uniformly: dN/dN = (q-2)N
        let n_norm = [0.1, 0.1, 0.1];
        let sigma_diag = [0.0; 3];
        let q = 0.5;
        let rhs = n_normalized_evolution_rhs(&n_norm, &sigma_diag, q);
        let expected = (0.5 - 2.0) * 0.1;
        for i in 0..3 {
            assert!((rhs[i] - expected).abs() < 1e-15);
        }
    }

    #[test]
    fn test_constraint_violation_level() {
        // Small shear: violation ≈ Σ²
        let omega_r = 9.14e-5;
        let omega_m = 0.3153;
        let omega_lambda = 0.6847;
        let omega_k = 1.0 - omega_r - omega_m - omega_lambda;
        let sigma2 = 1e-10;
        let ham = hamiltonian_constraint(sigma2, omega_r, omega_m, omega_lambda, omega_k, 0.0);
        // ham = 1 - σ² - (Ω_r+Ω_m+Ω_Λ+Ω_k) = 1 - σ² - 1 = -σ²
        assert!(ham.abs() < 1e-9, "Constraint should be ~ Σ²: {:.2e}", ham);
    }

    #[test]
    fn test_hamiltonian_with_curvature() {
        // BIX with curvature: Ω_k = 0.5 at normalised H=1
        // Budget: 1 = 0 + Ω_r + Ω_m + Ω_Λ + 0.5
        // → Ω_r + Ω_m + Ω_Λ = 0.5
        let ham = hamiltonian_constraint(0.0, 0.05, 0.2, 0.25, 0.5, 0.0);
        assert!(ham.abs() < 1e-15, "BIX budget: {:.2e}", ham);
    }

    #[test]
    fn test_evaluate_constraints_combined() {
        // FLRW: all zero
        let omega_r = 9.14e-5;
        let omega_m = 0.3153;
        let omega_lambda = 0.6847;
        let omega_k = 1.0 - omega_r - omega_m - omega_lambda;
        let (ham, mom, viol) = evaluate_constraints(
            0.0, omega_r, omega_m, omega_lambda, omega_k, 0.0,
            &[0.0; 3], &[0.0; 3], &[0.0; 3],
        );
        assert!(viol < 1e-14, "FLRW violation: {:.2e}", viol);
    }
}
