// Polarisation collision terms in the PSTF formalism.
// BC-04: E-mode source from intensity quadrupole, B-mode generation.
//
// E-mode source: S_E = (κ̇/10)(F₂ − √6 E₂)
// B-mode: zero at linear order for scalar perturbations.
//         Nonzero for tensor modes (Bianchi shear generates B through σ coupling).
//
// The polarisation source Π = F₂ + G₀ + G₂ enters the intensity C₂.

/// Compute the E-mode polarisation collision term.
///
/// dG_ℓ/dη|_collision:
///   G₀: κ̇(1/10)(F₂ − √6 G₂)  [source from intensity quadrupole]
///   G₂: κ̇(1/10)(F₂ − √6 G₂)  [same source, different projection]
///   G_ℓ (ℓ≥3): −κ̇ G_ℓ         [pure damping]
///
/// Here G_ℓ are the E-mode polarisation multipoles.
pub(crate) fn emode_collision(
    g_ell: &[f64],    // E-mode multipoles [G₀, G₁, G₂, ...]
    f2: f64,          // Intensity quadrupole F₂
    kappa_dot: f64,
) -> Vec<f64> {
    let n = g_ell.len();
    let mut c = vec![0.0; n];

    // Polarisation source: (1/10)(F₂ − √6 G₂)
    let sqrt6 = 6.0_f64.sqrt();
    let g2 = if n > 2 { g_ell[2] } else { 0.0 };
    let pol_source_e = (f2 - sqrt6 * g2) / 10.0;

    for ell in 0..n {
        c[ell] = match ell {
            0 => kappa_dot * pol_source_e,     // G₀ source
            1 => -kappa_dot * g_ell[1],        // G₁ damping (no dipole source for E-mode)
            2 => kappa_dot * pol_source_e,     // G₂ source (same as G₀)
            _ => -kappa_dot * g_ell[ell],      // Pure damping
        };
    }
    c
}

/// B-mode collision: zero at linear order for scalar/vector modes.
///
/// Nonzero only for tensor modes (Bianchi shear) at second order,
/// where E→B conversion through free-streaming generates B-modes.
pub(crate) fn bmode_collision_linear(
    b_ell: &[f64],
    kappa_dot: f64,
) -> Vec<f64> {
    // At linear order: pure damping for all ℓ
    b_ell.iter().map(|&b| -kappa_dot * b).collect()
}

/// Compute the full polarisation source Π = F₂ + G₀ + G₂.
///
/// This enters the intensity quadrupole collision term C₂.
pub(crate) fn polarisation_pi(f2: f64, g0: f64, g2: f64) -> f64 {
    f2 + g0 + g2
}

/// Check if polarisation is consistent: G₀ and G₂ should be
/// sourced by the same combination (1/10)(F₂ − √6 G₂).
pub(crate) fn polarisation_consistency(g0: f64, g2: f64, f2: f64) -> f64 {
    // In equilibrium: G₀ = G₂ = source → check ratio
    if g0.abs() < 1e-30 { return 0.0; }
    (g0 - g2).abs() / g0.abs()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_emode_source_from_f2() {
        let g = vec![0.0, 0.0, 0.0, 0.0];
        let f2 = 0.1;
        let kd = 100.0;
        let c = emode_collision(&g, f2, kd);
        // G₀ source = κ̇(1/10)F₂ = 100 × 0.01 = 1.0
        assert!((c[0] - 1.0).abs() < 1e-12, "G₀ source: {:.6}", c[0]);
        // G₂ source = same
        assert!((c[2] - 1.0).abs() < 1e-12, "G₂ source: {:.6}", c[2]);
    }

    #[test]
    fn test_emode_equilibrium() {
        // In equilibrium: (1/10)(F₂ − √6 G₂) = 0 → G₂ = F₂/√6
        let f2 = 0.1;
        let g2_eq = f2 / 6.0_f64.sqrt();
        let g = vec![g2_eq, 0.0, g2_eq];
        let c = emode_collision(&g, f2, 100.0);
        // Source should vanish
        assert!(c[0].abs() < 1e-12, "Equilibrium G₀: {:.2e}", c[0]);
        assert!(c[2].abs() < 1e-12, "Equilibrium G₂: {:.2e}", c[2]);
    }

    #[test]
    fn test_bmode_zero_linear() {
        let b = vec![0.01, 0.005, 0.001];
        let c = bmode_collision_linear(&b, 100.0);
        // Pure damping: C_ℓ = −κ̇ B_ℓ
        assert!((c[0] + 1.0).abs() < 1e-12);
        assert!((c[1] + 0.5).abs() < 1e-12);
    }

    #[test]
    fn test_pi_composition() {
        let pi = polarisation_pi(0.1, 0.02, 0.03);
        assert!((pi - 0.15).abs() < 1e-15);
    }

    #[test]
    fn test_no_scattering() {
        let g = vec![0.1, 0.05, 0.01];
        let c = emode_collision(&g, 0.1, 0.0);
        for &ci in &c { assert!(ci.abs() < 1e-15); }
    }
}
