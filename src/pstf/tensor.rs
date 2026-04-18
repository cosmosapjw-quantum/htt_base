// STF (Symmetric Trace-Free) tensor operations in 3D.
// BC-01: Core algebraic operations for the PSTF Boltzmann hierarchy.
//
// A rank-ℓ STF tensor in 3D has (2ℓ+1) independent components.
// Representations:
//   ℓ=0: scalar (f64)
//   ℓ=1: vector [f64; 3]
//   ℓ=2: 3×3 symmetric trace-free matrix [[f64; 3]; 3], 5 dof
//   General ℓ: Vec<f64> of length (2ℓ+1)
//
// The PSTF projection onto spatial indices:
//   A_{⟨ab⟩} = A_{(ab)} - (1/3)h_{ab} h^{cd}A_{cd}
// where h_{ab} = δ_{ab} in the orthonormal spatial frame.

/// Number of independent components of a rank-ℓ STF tensor in 3D.
pub(crate) fn stf_components(ell: usize) -> usize {
    2 * ell + 1
}

// ═══════════════════════════════════════════
// §1. Rank-2 STF operations (most common)
// ═══════════════════════════════════════════

/// Project a 3×3 matrix to its symmetric trace-free part.
///
/// A_{⟨ab⟩} = (1/2)(A_{ab} + A_{ba}) − (1/3)δ_{ab} tr(A)
pub(crate) fn stf_project_rank2(a: &[[f64; 3]; 3]) -> [[f64; 3]; 3] {
    let tr = a[0][0] + a[1][1] + a[2][2];
    let mut s = [[0.0f64; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            let sym = 0.5 * (a[i][j] + a[j][i]);
            let delta = if i == j { 1.0 } else { 0.0 };
            s[i][j] = sym - (1.0 / 3.0) * delta * tr;
        }
    }
    s
}

/// Full contraction of two rank-2 STF tensors: A_{⟨ab⟩} B^{⟨ab⟩}.
pub(crate) fn stf_contract_rank2(a: &[[f64; 3]; 3], b: &[[f64; 3]; 3]) -> f64 {
    let mut sum = 0.0;
    for i in 0..3 {
        for j in 0..3 {
            sum += a[i][j] * b[i][j];
        }
    }
    sum
}

/// Trace of a 3×3 matrix.
pub(crate) fn trace_3x3(a: &[[f64; 3]; 3]) -> f64 {
    a[0][0] + a[1][1] + a[2][2]
}

/// Frobenius norm of a 3×3 matrix.
pub(crate) fn frobenius_3x3(a: &[[f64; 3]; 3]) -> f64 {
    stf_contract_rank2(a, a).sqrt()
}

/// Check if a matrix is symmetric to tolerance.
pub(crate) fn is_symmetric_3x3(a: &[[f64; 3]; 3], tol: f64) -> bool {
    (a[0][1] - a[1][0]).abs() < tol
        && (a[0][2] - a[2][0]).abs() < tol
        && (a[1][2] - a[2][1]).abs() < tol
}

// ═══════════════════════════════════════════
// §2. STF outer product: ℓ → ℓ+1
// ═══════════════════════════════════════════

/// Outer product of a rank-1 tensor (vector) with direction e_a,
/// projected to STF: v_{⟨a} e_{b⟩}.
///
/// This produces a rank-2 STF tensor from a vector and a direction.
pub(crate) fn stf_outer_v1_e(v: &[f64; 3], e: &[f64; 3]) -> [[f64; 3]; 3] {
    let mut outer = [[0.0; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            outer[i][j] = v[i] * e[j];
        }
    }
    stf_project_rank2(&outer)
}

/// Outer product of a rank-2 STF tensor with direction e_c,
/// producing a rank-3 object (returned as flat [7] in real-Y_3m basis).
///
/// For the Boltzmann hierarchy, this enters through the spatial gradient
/// operator coupling ℓ to ℓ+1.
///
/// Result: T_{⟨abc⟩} = STF projection of T_{ab} e_c.
/// We store as [T_{111}, T_{112}, T_{113}, T_{122}, T_{123}, T_{133}, T_{222}]
/// but note that rank-3 STF has 7 independent components, not 10.
/// Here we return the full contraction sum ∑ T_{ab} e_b instead,
/// which is the inner product (ℓ→ℓ−1 operation) used in the hierarchy.
pub(crate) fn stf_rank2_contract_e(t: &[[f64; 3]; 3], e: &[f64; 3]) -> [f64; 3] {
    let mut result = [0.0; 3];
    for i in 0..3 {
        for j in 0..3 {
            result[i] += t[i][j] * e[j];
        }
    }
    result
}

// ═══════════════════════════════════════════
// §3. STF inner product: ℓ → ℓ−1
// ═══════════════════════════════════════════

/// Inner product (contraction) of a rank-2 STF with a direction:
/// T_{⟨ab⟩} e^b → rank-1 vector.
///
/// For STF T_{ab}: result_a = Σ_b T_{ab} e_b
pub(crate) fn stf_inner_rank2(t: &[[f64; 3]; 3], e: &[f64; 3]) -> [f64; 3] {
    stf_rank2_contract_e(t, e)
}

/// Inner product of a rank-1 tensor with a direction (scalar):
/// v_a e^a = dot product.
pub(crate) fn stf_inner_rank1(v: &[f64; 3], e: &[f64; 3]) -> f64 {
    v[0]*e[0] + v[1]*e[1] + v[2]*e[2]
}

// ═══════════════════════════════════════════
// §4. Angular integrals on S²
// ═══════════════════════════════════════════

/// ⟨e_a e_b⟩ = (1/3) δ_{ab}  (rank-2 angular average).
///
/// This is the fundamental angular integral for the PSTF formalism.
pub(crate) fn angular_average_ee() -> [[f64; 3]; 3] {
    let mut result = [[0.0; 3]; 3];
    for i in 0..3 {
        result[i][i] = 1.0 / 3.0;
    }
    result
}

/// ⟨e_a e_b e_c e_d⟩ = (1/15)(δ_{ab}δ_{cd} + δ_{ac}δ_{bd} + δ_{ad}δ_{bc}).
///
/// Returns the value for given indices (a, b, c, d).
pub(crate) fn angular_average_eeee(a: usize, b: usize, c: usize, d: usize) -> f64 {
    let d_ab = if a == b { 1.0 } else { 0.0 };
    let d_cd = if c == d { 1.0 } else { 0.0 };
    let d_ac = if a == c { 1.0 } else { 0.0 };
    let d_bd = if b == d { 1.0 } else { 0.0 };
    let d_ad = if a == d { 1.0 } else { 0.0 };
    let d_bc = if b == c { 1.0 } else { 0.0 };
    (d_ab * d_cd + d_ac * d_bd + d_ad * d_bc) / 15.0
}

/// Numerical angular average via Monte Carlo on S².
/// Computes ⟨f(ê)⟩ = (1/4π) ∫ f(ê) dΩ using uniform sampling.
///
/// `f`: function from direction [f64; 3] to f64.
/// `n_samples`: number of MC samples (Fibonacci sphere).
pub(crate) fn angular_average_mc<F: Fn(&[f64; 3]) -> f64>(f: F, n_samples: usize) -> f64 {
    // Fibonacci sphere for uniform sampling
    let phi = (1.0 + 5.0_f64.sqrt()) / 2.0; // golden ratio
    let mut sum = 0.0;
    for i in 0..n_samples {
        let theta = ((2.0 * i as f64 + 1.0) / (2.0 * n_samples as f64) - 0.5).acos()
            .max(0.0).min(std::f64::consts::PI);
        // Use a different formula for better uniformity
        let z = 1.0 - 2.0 * (i as f64 + 0.5) / n_samples as f64;
        let r = (1.0 - z * z).sqrt();
        let phi_i = 2.0 * std::f64::consts::PI * (i as f64) / phi;
        let e = [r * phi_i.cos(), r * phi_i.sin(), z];
        sum += f(&e);
    }
    sum / n_samples as f64
}

// ═══════════════════════════════════════════
// §5. STF orthogonality
// ═══════════════════════════════════════════

/// Verify STF orthogonality: ⟨e^{⟨A_ℓ⟩} e^{⟨B_ℓ'⟩}⟩ ∝ δ_{ℓℓ'}.
///
/// For ℓ=1, ℓ'=2: ⟨e_a (e_b e_c - (1/3)δ_{bc})⟩ = 0
/// (odd integrand vanishes).
///
/// Returns the numerical MC estimate for the cross-integral.
pub(crate) fn stf_orthogonality_check_12(n_samples: usize) -> f64 {
    // Compute ⟨e_1 × (e_1 e_2 - (1/3)δ_{12})⟩
    // = ⟨e_1 e_1 e_2⟩ - (1/3)×0 = ⟨e_1 e_1 e_2⟩
    // = 0 (odd function)
    angular_average_mc(|e| e[0] * (e[0]*e[1] - 0.0), n_samples)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Component counting ──
    #[test]
    fn test_component_count() {
        assert_eq!(stf_components(0), 1);  // scalar
        assert_eq!(stf_components(1), 3);  // vector
        assert_eq!(stf_components(2), 5);  // rank-2 STF
        assert_eq!(stf_components(3), 7);  // rank-3 STF
        assert_eq!(stf_components(10), 21);
        assert_eq!(stf_components(30), 61);
    }

    // ── STF projection: trace-free ──
    #[test]
    fn test_stf_project_tracefree() {
        let a = [[1.0, 0.5, 0.0], [0.5, 2.0, 0.3], [0.0, 0.3, 3.0]];
        let s = stf_project_rank2(&a);
        let tr = trace_3x3(&s);
        assert!(tr.abs() < 1e-15, "STF trace: {:.2e}", tr);
    }

    // ── STF projection: symmetric ──
    #[test]
    fn test_stf_project_symmetric() {
        let a = [[1.0, 0.5, 0.2], [0.3, 2.0, 0.7], [0.1, 0.4, 3.0]];
        let s = stf_project_rank2(&a);
        assert!(is_symmetric_3x3(&s, 1e-15));
    }

    // ── STF of identity is zero ──
    #[test]
    fn test_stf_identity_zero() {
        let id = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]];
        let s = stf_project_rank2(&id);
        assert!(frobenius_3x3(&s) < 1e-15, "STF(δ) must be 0");
    }

    // ── STF idempotent ──
    #[test]
    fn test_stf_idempotent() {
        let a = [[2.0, 0.5, 0.3], [0.5, -1.0, 0.7], [0.3, 0.7, -1.0]];
        let s1 = stf_project_rank2(&a);
        let s2 = stf_project_rank2(&s1);
        for i in 0..3 {
            for j in 0..3 {
                assert!((s1[i][j] - s2[i][j]).abs() < 1e-14, "Not idempotent at ({},{})", i, j);
            }
        }
    }

    // ── Angular average ⟨e_a e_b⟩ = (1/3)δ_{ab} ──
    #[test]
    fn test_angular_ee() {
        let avg = angular_average_ee();
        for i in 0..3 {
            for j in 0..3 {
                let expected = if i == j { 1.0/3.0 } else { 0.0 };
                assert!((avg[i][j] - expected).abs() < 1e-15);
            }
        }
    }

    // ── Angular average ⟨e_a e_b⟩ verified by MC ──
    #[test]
    fn test_angular_ee_mc() {
        let n = 100_000;
        let avg_11 = angular_average_mc(|e| e[0]*e[0], n);
        let avg_12 = angular_average_mc(|e| e[0]*e[1], n);
        assert!((avg_11 - 1.0/3.0).abs() < 0.01, "⟨e₁²⟩ = {:.4}", avg_11);
        assert!(avg_12.abs() < 0.01, "⟨e₁e₂⟩ = {:.4}", avg_12);
    }

    // ── Angular average ⟨e_a e_b e_c e_d⟩ ──
    #[test]
    fn test_angular_eeee() {
        // ⟨e₁²e₁²⟩ = (1/15)(1+1+1) = 3/15 = 1/5
        assert!((angular_average_eeee(0,0,0,0) - 1.0/5.0).abs() < 1e-15);
        // ⟨e₁²e₂²⟩ = (1/15)(0+1+0) = 1/15
        assert!((angular_average_eeee(0,0,1,1) - 1.0/15.0).abs() < 1e-15);
        // ⟨e₁e₂e₁e₂⟩ = (1/15)(0+1+0) = 1/15
        assert!((angular_average_eeee(0,1,0,1) - 1.0/15.0).abs() < 1e-15);
        // ⟨e₁e₂e₃e₁⟩ = (1/15)(0+0+0) = 0
        assert!(angular_average_eeee(0,1,2,0).abs() < 1e-15);
    }

    // ── ⟨e_a e_b e_c e_d⟩ verified by MC ──
    #[test]
    fn test_angular_eeee_mc() {
        let n = 200_000;
        let avg_1111 = angular_average_mc(|e| e[0].powi(4), n);
        let avg_1122 = angular_average_mc(|e| e[0]*e[0]*e[1]*e[1], n);
        assert!((avg_1111 - 1.0/5.0).abs() < 0.01, "⟨e₁⁴⟩ = {:.4}", avg_1111);
        assert!((avg_1122 - 1.0/15.0).abs() < 0.01, "⟨e₁²e₂²⟩ = {:.4}", avg_1122);
    }

    // ── Orthogonality: ⟨e_a (e_be_c)_{STF}⟩ = 0 ──
    #[test]
    fn test_orthogonality_l1_l2() {
        let n = 100_000;
        // ⟨e₁(e₁e₂ - (1/3)δ₁₂)⟩ = ⟨e₁²e₂⟩ = 0 (odd)
        let cross = angular_average_mc(|e| e[0] * (e[0]*e[1]), n);
        assert!(cross.abs() < 0.01, "ℓ=1,ℓ=2 orthogonality: {:.4}", cross);
    }

    // ── Outer product produces STF ──
    #[test]
    fn test_outer_product_stf() {
        let v = [1.0, 0.0, 0.0];
        let e = [0.0, 1.0, 0.0];
        let s = stf_outer_v1_e(&v, &e);
        assert!(trace_3x3(&s).abs() < 1e-15);
        assert!(is_symmetric_3x3(&s, 1e-15));
    }

    // ── Inner product: contraction ──
    #[test]
    fn test_inner_product() {
        let t = [[0.1, 0.02, 0.0], [0.02, -0.05, 0.01], [0.0, 0.01, -0.05]];
        let e = [1.0, 0.0, 0.0];
        let result = stf_inner_rank2(&t, &e);
        assert!((result[0] - 0.1).abs() < 1e-15);
        assert!((result[1] - 0.02).abs() < 1e-15);
        assert!((result[2] - 0.0).abs() < 1e-15);
    }
}
