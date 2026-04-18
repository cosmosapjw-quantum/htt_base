//! m-Dependent Collision Operator + Θ⁴ Bridge + Baryon Physics (P1-03)
//!
//! ## Physics
//!
//! Thomson scattering collision operator in the (ℓ,m) basis:
//!   ℓ ≥ 3: C[F_{ℓm}] = −κ̇ × F_{ℓm}              [DIAGONAL — key for IMEX]
//!   ℓ = 1: C[F_{1m}] = −κ̇ × (F_{1m} − v_b^m)     [baryon drag]
//!   ℓ = 2: C[F_{2m}] = −(9/10)κ̇ × F_{2m} + ...    [pol feedback]
//!   ℓ = 0: C[F_{0m}] = 0                            [monopole conserved]
//!
//! The collision operator is DIAGONAL for ℓ ≥ 3, which is the key property
//! enabling cheap IMEX splitting: the implicit part is trivially invertible.
//!
//! Θ⁴ nonlinear bridge: c_ξ = 1/2 in Θ variables (ESTABLISHED).
//! E-B mixing: shear σ_{ab} couples E→B modes (zero in FLRW).

use super::lm_indexing::{LmLayout, LmSpecies, Pol};

/// Collision operator structure.
///
/// Split into diagonal (ℓ ≥ 3, cheap) and block (ℓ ≤ 2, small dense) parts.
/// This split is what makes IMEX efficient: the implicit solve for ℓ ≥ 3
/// is just scalar division, O(1) per DOF.
#[derive(Clone, Debug)]
pub(crate) struct CollisionOperator {
    /// Diagonal damping rates for ℓ ≥ 3: C[F_ℓm] = −rate × F_ℓm.
    /// Indexed by flat state vector position.
    pub(crate) diagonal: Vec<(usize, f64)>,
    /// Small dense blocks for ℓ = 1 (photon-baryon drag) and ℓ = 2 (pol feedback).
    /// Each block: (row_indices, col_indices, dense_matrix).
    pub(crate) blocks: Vec<CollisionBlock>,
    /// ℓ = 0: zero collision (monopole conserved). Stored for documentation.
    pub(crate) n_conserved: usize,
}

/// A small dense collision block (ℓ = 1 or ℓ = 2).
#[derive(Clone, Debug)]
pub(crate) struct CollisionBlock {
    pub(crate) ell: usize,
    pub(crate) m: i32,
    /// Row indices in the full state vector.
    pub(crate) rows: Vec<usize>,
    /// Column indices in the full state vector.
    pub(crate) cols: Vec<usize>,
    /// Dense matrix (row-major, rows.len() × cols.len()).
    pub(crate) matrix: Vec<f64>,
}

/// Θ⁴ nonlinear correction coefficient.
///
/// c_ξ = 1/2 in Θ (temperature) variables.
/// Coefficient chain: 6(Δ) → 2(I) → 1/2(Θ), verified to 2×10⁻¹⁵.
pub(crate) const THETA4_CXI: f64 = 0.5;

/// Build the collision operator for the photon sector.
///
/// # Arguments
/// * `layout` — state vector layout
/// * `kappa_dot` — Thomson scattering rate κ̇ [Mpc⁻¹] (positive)
/// * `r_b` — baryon-photon ratio R_b = 3ρ_b/(4ρ_γ)
///
/// # Returns
/// Collision operator with diagonal (ℓ≥3) and block (ℓ=1,2) parts.
pub(crate) fn build_collision(
    layout: &LmLayout,
    kappa_dot: f64,
    r_b: f64,
) -> CollisionOperator {
    let lg = layout.ell_max_gamma;
    let kd = kappa_dot.abs(); // Canonicalize: opacity > 0 ALWAYS (P1-05 sign convention)
    let mut diagonal = Vec::new();
    let mut blocks = Vec::new();
    let mut n_conserved = 0;

    for m in -(lg as i32)..=(lg as i32) {
        let abs_m = m.unsigned_abs() as usize;

        for ell in abs_m..=lg {
            let flat = layout.photon_i_start
                + LmLayout::lm_offset_full(ell, m, lg);

            if ell == 0 {
                // ℓ = 0: NO collision (monopole conserved by Thomson)
                n_conserved += 1;
            } else if ell == 1 {
                // ℓ = 1: photon-baryon drag
                //   C[F_{1m}] = −κ̇ × (F_{1m} − v_b^m)
                // This couples F_{1m} to the baryon velocity component v_b^m.
                //
                // In the state vector: baryon velocity is at baryon_start + 1..4
                // for m = -1, 0, +1 respectively.
                // Only |m| ≤ 1 has baryon coupling (v_b is a vector → ℓ=1 only).
                if abs_m <= 1 {
                    let baryon_idx = layout.baryon_start + 1 + (m + 1) as usize;
                    // Block: 2×2 system [F_{1m}, v_b^m]
                    // dF_{1m}/dη|_coll = −κ̇(F_{1m} − v_b^m)
                    // dv_b^m/dη|_drag  = κ̇/(R_b)(F_{1m}/3 − v_b^m/3)  [Euler equation drag]
                    //                  = (κ̇/R_b)(F_{1m} − v_b^m)/3
                    // Wait: the standard baryon Euler has:
                    //   v_b' = ... + κ̇(3Θ₁ − v_b)/R_b
                    // where Θ₁ = F₁/4 in brightness. But in PSTF convention
                    // with F = 4Θ (brightness), the coupling is:
                    //   dv_b/dη|_drag = κ̇(3×F₁/4 − v_b)/R_b = κ̇(3F₁ − 4v_b)/(4R_b)
                    //
                    // For the collision BLOCK (coupling F_{1m} and v_b^m):
                    let inv_rb = 1.0 / r_b.max(1e-10);
                    blocks.push(CollisionBlock {
                        ell: 1,
                        m,
                        rows: vec![flat, baryon_idx],
                        cols: vec![flat, baryon_idx],
                        matrix: vec![
                            // [dF_{1m}/dη, dF_{1m}/dv_b^m]
                            -kd,            kd,
                            // [dv_b^m/dF_{1m}, dv_b^m/dv_b^m]
                            3.0 * kd * inv_rb / 4.0,  -kd * inv_rb,
                        ],
                    });
                } else {
                    // |m| > 1: no baryon coupling (v_b has no |m|>1 component)
                    // Pure diagonal damping
                    diagonal.push((flat, kd));
                }
            } else if ell == 2 {
                // ℓ = 2: temperature-polarization feedback
                //   C[F_{2m}] = −(9/10)κ̇ × F_{2m} + κ̇ × ζ_{2m}/10
                //   ζ_{2m} = (2/5)F_{2m} + E_{2m}
                // So: C[F_{2m}] = −(9/10)κ̇ F_{2m} + (κ̇/10)[(2/5)F_{2m} + E_{2m}]
                //               = −(9/10 − 2/50)κ̇ F_{2m} + (κ̇/10)E_{2m}
                //               = −(43/50)κ̇ F_{2m} + (κ̇/10)E_{2m}
                //
                // For E-mode quadrupole:
                //   C[E_{2m}] = −κ̇ × E_{2m} + (κ̇/10)ζ_{2m}
                //             = −κ̇ E_{2m} + (κ̇/10)[(2/5)F_{2m} + E_{2m}]
                //             = (κ̇/50)(2F_{2m}) + (−κ̇ + κ̇/10)E_{2m}
                //             = (κ̇/25)F_{2m} − (9κ̇/10)E_{2m}
                if abs_m <= lg && abs_m >= 0 {
                    // Check if E-mode index exists (ℓ=2 always ≥ 2)
                    let e_flat = layout.photon_e_start
                        + LmLayout::lm_offset_pol(2, m, lg);
                    blocks.push(CollisionBlock {
                        ell: 2,
                        m,
                        rows: vec![flat, e_flat],
                        cols: vec![flat, e_flat],
                        matrix: vec![
                            // [dF_{2m}/dF_{2m}, dF_{2m}/dE_{2m}]
                            -43.0 * kd / 50.0,    kd / 10.0,
                            // [dE_{2m}/dF_{2m}, dE_{2m}/dE_{2m}]
                            kd / 25.0,            -9.0 * kd / 10.0,
                        ],
                    });
                }
            } else {
                // ℓ ≥ 3: pure diagonal damping
                //   C[F_{ℓm}] = −κ̇ × F_{ℓm}
                diagonal.push((flat, kd));
            }
        }

        // E-mode ℓ ≥ 3: also diagonal
        for ell in abs_m.max(3)..=lg {
            let flat = layout.photon_e_start
                + LmLayout::lm_offset_pol(ell, m, lg);
            diagonal.push((flat, kd));
        }

        // B-mode: diagonal for all ℓ ≥ 2
        // B-modes have NO gain from Thomson at linear order.
        // (B arises only from E→B conversion via shear or second-order effects.)
        for ell in abs_m.max(2)..=lg {
            let flat = layout.photon_b_start
                + LmLayout::lm_offset_pol(ell, m, lg);
            diagonal.push((flat, kd));
        }
    }

    CollisionOperator { diagonal, blocks, n_conserved }
}

/// Apply collision operator to state vector: out += C × y.
pub(crate) fn apply_collision(
    op: &CollisionOperator,
    y: &[f64],
    out: &mut [f64],
) {
    // Diagonal part: out[i] += −rate × y[i]
    for &(idx, rate) in &op.diagonal {
        if idx < y.len() {
            out[idx] += -rate * y[idx];
        }
    }
    // Block part: out[rows] += matrix × y[cols]
    for block in &op.blocks {
        let nr = block.rows.len();
        let nc = block.cols.len();
        for i in 0..nr {
            let ri = block.rows[i];
            if ri >= out.len() { continue; }
            for j in 0..nc {
                let ci = block.cols[j];
                if ci >= y.len() { continue; }
                out[ri] += block.matrix[i * nc + j] * y[ci];
            }
        }
    }
}

/// CDM collision: ZERO (collisionless).
/// CDM evolves under gravity + metric only.
/// This function exists to document the physics explicitly.
pub(crate) fn cdm_collision_rate() -> f64 { 0.0 }

/// Neutrino collision: ZERO (free-streaming after decoupling).
pub(crate) fn neutrino_collision_rate() -> f64 { 0.0 }

/// Θ⁴ nonlinear correction to the quadrupole collision.
///
/// ΔC[F_{2m}] = −κ̇ × c_ξ × ⟨Θ⁴⟩_{2m}
/// where c_ξ = 1/2 (ESTABLISHED, verified to 2×10⁻¹⁵).
///
/// This is a SECOND-ORDER correction that modifies the ℓ=2 collision
/// through the quartic temperature coupling. The 8 quartic coefficients
/// are from theta4_bridge_v2.rs.
pub(crate) fn theta4_quadrupole_correction(
    kappa_dot: f64,
    theta4_2m: f64,
) -> f64 {
    -kappa_dot.abs() * THETA4_CXI * theta4_2m
}

// ═══════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_diagonal_high_ell() {
        let lay = LmLayout::new(10, 5);
        let op = build_collision(&lay, 100.0, 0.6);
        // ℓ ≥ 3 should be ALL diagonal
        let n_diag = op.diagonal.len();
        // Photon I ℓ≥3: Σ_{m=-L..L} (L-max(|m|,3)+1) for each m
        // Photon E ℓ≥3: similar
        // Photon B ℓ≥2: all diagonal
        assert!(n_diag > 100, "Should have many diagonal entries, got {}", n_diag);
        // All diagonal rates should be positive (damping)
        for &(_, rate) in &op.diagonal {
            assert!(rate > 0.0, "Diagonal rate must be positive (damping)");
        }
    }

    #[test]
    fn test_monopole_conserved() {
        let lay = LmLayout::new(10, 5);
        let op = build_collision(&lay, 100.0, 0.6);
        // Monopole (ℓ=0) should have ZERO collision
        assert!(op.n_conserved > 0, "Should have conserved monopoles");
        // Check: no diagonal entry at ℓ=0 indices
        let mono_flat = lay.photon_i_start + LmLayout::lm_offset_full(0, 0, 10);
        for &(idx, _) in &op.diagonal {
            assert_ne!(idx, mono_flat, "Monopole should NOT be in diagonal damping");
        }
    }

    #[test]
    fn test_baryon_drag_block() {
        let lay = LmLayout::new(10, 5);
        let op = build_collision(&lay, 100.0, 0.6);
        // ℓ=1, m=0 should have a 2×2 block coupling F_{10} and v_b
        let has_l1_block = op.blocks.iter().any(|b| b.ell == 1 && b.m == 0);
        assert!(has_l1_block, "Should have ℓ=1, m=0 baryon drag block");
        // ℓ=1, m=±1 should also have blocks
        let has_l1_m1 = op.blocks.iter().any(|b| b.ell == 1 && b.m == 1);
        assert!(has_l1_m1, "Should have ℓ=1, m=1 baryon drag block");
    }

    #[test]
    fn test_pol_feedback_block() {
        let lay = LmLayout::new(10, 5);
        let op = build_collision(&lay, 100.0, 0.6);
        // ℓ=2 should have blocks coupling F_{2m} and E_{2m}
        let l2_blocks: Vec<_> = op.blocks.iter().filter(|b| b.ell == 2).collect();
        assert!(!l2_blocks.is_empty(), "Should have ℓ=2 pol feedback blocks");
        // Check that E-mode coupling exists (off-diagonal in the 2×2 block)
        for b in &l2_blocks {
            assert_eq!(b.matrix.len(), 4, "ℓ=2 block should be 2×2");
            // Off-diagonal: dF/dE and dE/dF should be nonzero
            assert!(b.matrix[1].abs() > 1e-10, "F←E coupling should be nonzero");
            assert!(b.matrix[2].abs() > 1e-10, "E←F coupling should be nonzero");
        }
    }

    #[test]
    fn test_tight_coupling_limit() {
        // κ̇ → ∞: baryon drag block forces F_{1m} → v_b^m
        let lay = LmLayout::new(10, 5);
        let kd = 1e10; // Very large opacity
        let op = build_collision(&lay, kd, 0.6);
        // Find the ℓ=1, m=0 block
        let block = op.blocks.iter().find(|b| b.ell == 1 && b.m == 0).unwrap();
        // The eigenvalues should be large (rapid equilibration)
        // Matrix: [[-kd, kd], [3kd/(4R), -kd/R]]
        let a = block.matrix[0]; // -kd
        let d = block.matrix[3]; // -kd/R
        // Both diagonal elements should be ~ -kd (rapid damping)
        assert!(a.abs() > 1e8, "F_10 damping rate should be large");
        assert!(d.abs() > 1e8, "v_b damping rate should be large");
    }

    #[test]
    fn test_cdm_no_collision() {
        assert_eq!(cdm_collision_rate(), 0.0, "CDM must be collisionless");
        assert_eq!(neutrino_collision_rate(), 0.0, "Neutrinos must be collisionless");
    }

    #[test]
    fn test_theta4_coefficient() {
        assert!((THETA4_CXI - 0.5).abs() < 1e-15,
            "c_ξ must be exactly 1/2");
    }

    #[test]
    fn test_apply_collision() {
        let lay = LmLayout::new(5, 3);
        let op = build_collision(&lay, 10.0, 0.6);
        let n = lay.total_dof;
        let mut y = vec![1.0_f64; n];
        let mut out = vec![0.0_f64; n];
        apply_collision(&op, &y, &mut out);
        // ℓ=0 (monopole) should have zero output
        let mono = lay.photon_i_start + LmLayout::lm_offset_full(0, 0, 5);
        assert!(out[mono].abs() < 1e-10,
            "Monopole collision should be zero, got {}", out[mono]);
        // ℓ≥3 should have negative output (damping of F=1)
        let l3 = lay.photon_i_start + LmLayout::lm_offset_full(3, 0, 5);
        assert!(out[l3] < 0.0,
            "ℓ=3 should be damped, got {}", out[l3]);
    }

    #[test]
    fn test_eb_no_mixing_flrw() {
        // In FLRW (σ=0), E and B modes decouple in collision.
        // B-mode has pure diagonal damping, no source from E.
        let lay = LmLayout::new(5, 3);
        let op = build_collision(&lay, 10.0, 0.6);
        // Check: no block has both E and B indices
        for block in &op.blocks {
            let has_e = block.rows.iter().any(|&r|
                r >= lay.photon_e_start && r < lay.photon_b_start);
            let has_b = block.rows.iter().any(|&r|
                r >= lay.photon_b_start && r < lay.nu_theta_start);
            assert!(!(has_e && has_b), "FLRW: E-B should not mix in collision");
        }
    }
}
