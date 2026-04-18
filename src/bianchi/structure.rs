// Bianchi structure constants and Jacobi identity verification.
// BB-01: Ellis-MacCallum decomposition for all 9 types.
//
// C^α_{βγ} = ε_{βγδ} n^{δα} + δ^α_β a_γ − δ^α_γ a_β
//
// Canonical frame: n^{αβ} = diag(n₁, n₂, n₃), a_α = (0, 0, a₃).
// Jacobi identity: n^{αβ} a_β = 0 ⟹ n₃ = 0 for Class B.

use super::types::*;

/// 3D Levi-Civita symbol: ε_{ijk} = +1 for even permutations of (0,1,2).
fn levi_civita(i: usize, j: usize, k: usize) -> f64 {
    if i == j || j == k || i == k {
        return 0.0;
    }
    // (0,1,2) → +1, (1,2,0) → +1, (2,0,1) → +1
    // (0,2,1) → -1, (2,1,0) → -1, (1,0,2) → -1
    let idx = i * 9 + j * 3 + k;
    match idx {
        5 | 15 | 19 => 1.0,   // (0,1,2)=5, (1,2,0)=15, (2,0,1)=19
        7 | 11 | 21 => -1.0,  // (0,2,1)=7, (1,0,2)=11, (2,1,0)=21
        _ => 0.0,
    }
}

/// Compute C^α_{βγ} for the given Bianchi parameters.
///
/// Returns `c[alpha][beta][gamma]` with α the upper index, (β,γ) lower.
/// The array is antisymmetric in (β,γ): c[a][b][g] = −c[a][g][b].
pub(crate) fn structure_constants(params: &BianchiParams) -> [[[f64; 3]; 3]; 3] {
    let n = params.n_eigenvalues; // (n₁, n₂, n₃)
    let a_mag = params.a_magnitude;
    // Canonical frame: a_α = (0, 0, a_mag)
    let a = [0.0, 0.0, a_mag];

    let mut c = [[[0.0f64; 3]; 3]; 3];

    for alpha in 0..3 {
        for beta in 0..3 {
            for gamma in 0..3 {
                // First term: ε_{βγδ} n^{δα}
                // n^{δα} = n[δ] if δ == α, else 0 (diagonal)
                let term1 = levi_civita(beta, gamma, alpha) * n[alpha];

                // Second term: δ^α_β a_γ − δ^α_γ a_β
                let kron_ab = if alpha == beta { 1.0 } else { 0.0 };
                let kron_ag = if alpha == gamma { 1.0 } else { 0.0 };
                let term2 = kron_ab * a[gamma] - kron_ag * a[beta];

                c[alpha][beta][gamma] = term1 + term2;
            }
        }
    }
    c
}

/// Verify the Jacobi identity: C^d_{e[a} C^e_{bc]} = 0.
///
/// Returns the L∞ norm of the Jacobi violation tensor J_d:
///   J_d = Σ_e [C^d_{e0} C^e_{12} + C^d_{e1} C^e_{20} + C^d_{e2} C^e_{01}]
///
/// In 3D the totally antisymmetric part [abc] has only one independent
/// component (a,b,c) = (0,1,2), so we compute J_d for d = 0,1,2 and
/// return max |J_d|.
pub(crate) fn jacobi_check(c: &[[[f64; 3]; 3]; 3]) -> f64 {
    let mut max_viol = 0.0f64;
    // (a,b,c) = (0,1,2) is the only independent component in 3D
    for d in 0..3 {
        let mut j_d = 0.0;
        for e in 0..3 {
            // Cyclic: C^d_{ea} C^e_{bc} + C^d_{eb} C^e_{ca} + C^d_{ec} C^e_{ab}
            // (a,b,c) = (0,1,2)
            j_d += c[d][e][0] * c[e][1][2]
                 + c[d][e][1] * c[e][2][0]
                 + c[d][e][2] * c[e][0][1];
        }
        max_viol = max_viol.max(j_d.abs());
    }
    max_viol
}

/// Verify the Jacobi constraint n^{αβ} a_β = 0 directly.
///
/// Returns max_α |n_α · a_α| (for diagonal n with a along 3rd axis,
/// this reduces to |n₃ · a|).
pub(crate) fn jacobi_na_check(params: &BianchiParams) -> f64 {
    // n^{αβ} = diag(n₁, n₂, n₃), a_β = (0, 0, a)
    // n^{αβ} a_β = (0, 0, n₃ · a)
    let n = params.n_eigenvalues;
    let a = params.a_magnitude;
    // In canonical frame with a along 3rd axis:
    (n[2] * a).abs()
}

/// Classify the Bianchi type from its parameters.
pub(crate) fn class(params: &BianchiParams) -> BianchiClass {
    params.btype.class()
}

/// Check whether the type admits an FLRW limit.
pub(crate) fn has_flrw_limit(params: &BianchiParams) -> bool {
    params.btype.has_flrw_limit()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn assert_jacobi(btype: BianchiType) {
        let params = btype.canonical_params();
        let c = structure_constants(&params);
        let viol = jacobi_check(&c);
        assert!(
            viol < 1e-15,
            "{}: Jacobi violation = {:.2e} (want < 1e-15)",
            btype.label(), viol
        );
        // Also check n·a = 0
        let na = jacobi_na_check(&params);
        assert!(
            na < 1e-15,
            "{}: n·a violation = {:.2e}",
            btype.label(), na
        );
    }

    #[test]
    fn test_jacobi_all_types() {
        for btype in all_canonical_types() {
            assert_jacobi(btype);
        }
    }

    #[test]
    fn test_class_a() {
        let class_a = [
            BianchiType::I, BianchiType::II, BianchiType::VI0,
            BianchiType::VII0, BianchiType::VIII, BianchiType::IX,
        ];
        for bt in &class_a {
            assert_eq!(bt.class(), BianchiClass::A, "{} should be Class A", bt.label());
        }
    }

    #[test]
    fn test_class_b() {
        let class_b = [
            BianchiType::III, BianchiType::IV, BianchiType::V,
            BianchiType::VIh(-0.5), BianchiType::VIIh(0.5),
        ];
        for bt in &class_b {
            assert_eq!(bt.class(), BianchiClass::B, "{} should be Class B", bt.label());
        }
    }

    #[test]
    fn test_flrw_limits() {
        let with_flrw = [
            BianchiType::I, BianchiType::V, BianchiType::VII0,
            BianchiType::VIIh(0.5), BianchiType::IX,
        ];
        let without_flrw = [
            BianchiType::II, BianchiType::III, BianchiType::IV,
            BianchiType::VI0, BianchiType::VIh(-0.5), BianchiType::VIII,
        ];
        for bt in &with_flrw {
            assert!(bt.has_flrw_limit(), "{} should have FLRW limit", bt.label());
        }
        for bt in &without_flrw {
            assert!(!bt.has_flrw_limit(), "{} should NOT have FLRW limit", bt.label());
        }
    }

    #[test]
    fn test_type_i_trivial() {
        let params = BianchiType::I.canonical_params();
        let c = structure_constants(&params);
        // All structure constants should be exactly zero
        for a in 0..3 {
            for b in 0..3 {
                for g in 0..3 {
                    assert_eq!(c[a][b][g], 0.0, "BI: C^{}_{}{} should be 0", a, b, g);
                }
            }
        }
    }

    #[test]
    fn test_type_ii_heisenberg() {
        // Type II: n₁ = 1, rest zero. Only C^0_{12} = 1.
        let params = BianchiType::II.canonical_params();
        let c = structure_constants(&params);
        assert!((c[0][1][2] - 1.0).abs() < 1e-15);
        assert!((c[0][2][1] + 1.0).abs() < 1e-15);
        // All other independent components zero
        assert!(c[1][0][2].abs() < 1e-15);
        assert!(c[2][0][1].abs() < 1e-15);
    }

    #[test]
    fn test_type_ix_so3() {
        // Type IX: n = (1,1,1), a = 0. Structure constants of SO(3).
        let params = BianchiType::IX.canonical_params();
        let c = structure_constants(&params);
        // C^0_{12} = n₁ = 1
        assert!((c[0][1][2] - 1.0).abs() < 1e-15);
        // C^1_{20} = n₂ = 1  (from ε_{201} n₂ = +1·1)
        assert!((c[1][2][0] - 1.0).abs() < 1e-15);
        // C^2_{01} = n₃ = 1
        assert!((c[2][0][1] - 1.0).abs() < 1e-15);
    }

    #[test]
    fn test_type_v_dilation() {
        // Type V: n = 0, a = 1. C^0_{02} = 1, C^1_{12} = 1.
        let params = BianchiType::V.canonical_params();
        let c = structure_constants(&params);
        assert!((c[0][0][2] - 1.0).abs() < 1e-15);
        assert!((c[1][1][2] - 1.0).abs() < 1e-15);
        // n-dependent terms all zero
        assert!(c[0][1][2].abs() < 1e-15);
        assert!(c[2][0][1].abs() < 1e-15);
    }

    #[test]
    fn test_antisymmetry() {
        // For all types, C^α_{βγ} = −C^α_{γβ}
        for btype in all_canonical_types() {
            let params = btype.canonical_params();
            let c = structure_constants(&params);
            for a in 0..3 {
                for b in 0..3 {
                    for g in 0..3 {
                        let diff = (c[a][b][g] + c[a][g][b]).abs();
                        assert!(
                            diff < 1e-15,
                            "{}: C^{}_{}{} + C^{}_{}{} = {:.2e}",
                            btype.label(), a, b, g, a, g, b, diff
                        );
                    }
                }
            }
        }
    }

    #[test]
    fn test_jacobi_parametric_vih() {
        // Test Jacobi for several VI_h values
        for &h in &[-0.1, -0.5, -2.0, -10.0] {
            assert_jacobi(BianchiType::VIh(h));
        }
    }

    #[test]
    fn test_jacobi_parametric_viih() {
        // Test Jacobi for several VII_h values
        for &h in &[0.01, 0.1, 0.5, 1.0, 10.0] {
            assert_jacobi(BianchiType::VIIh(h));
        }
    }
}
