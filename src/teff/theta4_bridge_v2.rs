// CL-12: Θ⁴ Thomson Bridge — Corrected Quartic Implementation.
//
// Paper V Theorem 1: I_{ab} = c_ξ ⟨Θ⁴ ê_{⟨a}ê_{b⟩}⟩_Ω
//
// TWO COEFFICIENT LAYERS (ER-CL-03 §1):
//   Raw tensor layer:  I_{ab}|_{dip²} = 6 c_ξ T₀⁴ T_{⟨a}T_{b⟩}
//   Scalar Legendre:   a₂|_{dip²} = 4 A²
//   Related by Gaunt:  6 × (P₁² → P₂ = 2/3) = 4
//
// VERIFIED QUARTIC (ER-CL-03 §2, 800-pt Gauss-Legendre, < 10⁻¹⁰):
//   a₂ = 4Q + 4A² + (12/7)Q² + (44/7)A²Q + (12/7)Q³
//       + (4/7)A⁴ + (16/7)A²Q² + (20/77)Q⁴
//
// P1 FIXES from ER-CL-03:
//   c_{A²Q}: 24/5 → 44/7  (P1-A)
//   c_{A⁴}:  12/5 → 4/7   (P1-B)
//   c_{Q³}:  108/77 → 12/7 (P2-a)
//
// NEW terms (not in original code):
//   c_{A²Q²} = 16/7
//   c_{Q⁴}   = 20/77

use std::f64::consts::PI;

// ═══ Verified Quartic Coefficients (ER-CL-03 Table, row by row) ═══

/// a₂ coefficient for the quartic Θ⁴ bridge.
///
/// a₂ = (5/2) ∫₋₁¹ (1 + AP₁ + QP₂)⁴ P₂ dμ
///
/// where A = dipole amplitude, Q = quadrupole amplitude.
///
/// All coefficients verified by N=800 Gauss-Legendre quadrature
/// against analytic Gaunt algebra (ER-CL-03 v3).
pub(crate) fn corrected_a2(a: f64, q: f64) -> f64 {
    let a2 = a * a;
    let a4 = a2 * a2;
    let q2 = q * q;
    let q3 = q2 * q;
    let q4 = q2 * q2;

    4.0 * q                          // 4θ   linear
        + 4.0 * a2                   // 6θ²  dipole²:     6×(2/3) = 4
        + (12.0 / 7.0) * q2         // 6θ²  quadrupole²: 6×(2/7) = 12/7
        + (44.0 / 7.0) * a2 * q     // 4θ³: 12×(11/21) = 44/7     [P1-A fix]
        + (12.0 / 7.0) * q3         // 4θ³: 4×(3/7) = 12/7        [P2-a fix]
        + (4.0 / 7.0) * a4          // θ⁴:  P₂(P₁⁴) = 4/7         [P1-B fix]
        + (16.0 / 7.0) * a2 * q2    // θ⁴:  6×P₂(P₁²P₂²) = 16/7  [NEW]
        + (20.0 / 77.0) * q4        // θ⁴:  P₂(P₂⁴) = 20/77       [NEW]
}

/// Linear-order a₂ (standard PSTF: only the 4Q term).
pub(crate) fn linear_a2(q: f64) -> f64 {
    4.0 * q
}

/// Quadratic-order a₂ (includes dipole-squared and quadrupole-squared).
pub(crate) fn quadratic_a2(a: f64, q: f64) -> f64 {
    4.0 * q + 4.0 * a * a + (12.0 / 7.0) * q * q
}

// ═══ Source translation error ═══

/// Source translation error: |a₂^{exact} − a₂^{linear}| / |a₂^{exact}|
///
/// This quantifies how much the linear PSTF bridge misses.
/// At (A, Q) = (0.30, 0.15): ε_Th^{lin} ≈ 52.5% (Paper V Table II).
pub(crate) fn eps_th_linear(a: f64, q: f64) -> f64 {
    let exact = corrected_a2(a, q);
    let lin = linear_a2(q);
    if exact.abs() < 1e-30 { return 0.0; }
    (exact - lin).abs() / exact.abs()
}

/// Source translation error: |a₂^{exact} − a₂^{quadratic}| / |a₂^{exact}|
pub(crate) fn eps_th_quadratic(a: f64, q: f64) -> f64 {
    let exact = corrected_a2(a, q);
    let quad = quadratic_a2(a, q);
    if exact.abs() < 1e-30 { return 0.0; }
    (exact - quad).abs() / exact.abs()
}

// ═══ Full Thomson bridge with dipole input ═══

/// Full Θ⁴ Thomson bridge including dipole → quadrupole coupling.
///
/// Uses the corrected quartic a₂ formula to compute the nonlinear
/// Thomson source I_{ab} = c_ξ × a₂(A, Q) × (normalization).
///
/// This replaces the old thomson_quadrupole_source which had no
/// dipole input (ER-CL-03 P2-b).
pub(crate) fn full_thomson_bridge(
    theta_0: f64,       // Θ₀ = 1 + perturbation (monopole)
    theta_1: f64,       // |Θ₁| = dipole amplitude A
    theta_2m: &[f64; 5], // quadrupole F_{2m}
    c_xi: f64,           // statistics coefficient
) -> [f64; 5] {
    // Compute (A, Q) from the PSTF multipoles
    let a = theta_1.abs(); // dipole amplitude
    // Q from the quadrupole: |Q| ~ |F_{20}| (m=0 axisymmetric approximation)
    // For the general case, Q ~ sqrt(sum |F_{2m}|²) / normalization
    let q2_sq: f64 = theta_2m.iter().map(|x| x * x).sum();
    let q = q2_sq.sqrt();

    // Full quartic a₂
    let a2_val = corrected_a2(a, q);
    let a2_lin = linear_a2(q);

    // Scale each F_{2m} by the ratio a₂_full / a₂_linear
    // so that the m-structure is preserved while the total amplitude
    // is corrected by the nonlinear terms.
    let mut i_2m = [0.0; 5];
    if a2_lin.abs() > 1e-30 {
        let scale = c_xi * a2_val / a2_lin;
        for m in 0..5 {
            i_2m[m] = scale * theta_2m[m];
        }
    } else {
        // Pure dipole case: a₂ = 4A², no Q structure to preserve
        // Distribute as (2/3) into m=0 component (axial symmetry)
        i_2m[2] = c_xi * 4.0 * a * a; // m=0 component
    }
    i_2m
}

// ═══ Gaunt product table (ER-CL-03 §3, ground truth) ═══

/// Gaunt coefficient: ∫P_a P_b P₂ dμ / ∫P₂² dμ = (5/2)∫P_a P_b P₂ dμ.
/// Verified by N=800 Gauss-Legendre.
pub(crate) mod gaunt {
    /// P₁² → P₂ coefficient: 2/3
    pub const P1_SQ_TO_P2: f64 = 2.0 / 3.0;

    /// P₂² → P₂ coefficient: 2/7
    pub const P2_SQ_TO_P2: f64 = 2.0 / 7.0;

    /// P₁⁴ → P₂ coefficient: 4/7
    pub const P1_4TH_TO_P2: f64 = 4.0 / 7.0;

    /// P₂³ → P₂ coefficient: 3/7
    pub const P2_CUBE_TO_P2: f64 = 3.0 / 7.0;

    /// P₁²P₂ → P₂ coefficient: 11/21
    pub const P1SQ_P2_TO_P2: f64 = 11.0 / 21.0;

    /// P₁P₂ → P₂ coefficient: 0 (parity kills this)
    pub const P1_P2_TO_P2: f64 = 0.0;

    /// P₁²P₂² → P₂ coefficient: 8/21
    pub const P1SQ_P2SQ_TO_P2: f64 = 8.0 / 21.0;

    /// P₂⁴ → P₂ coefficient: 20/77
    pub const P2_4TH_TO_P2: f64 = 20.0 / 77.0;
}

// ═══ Exact quadrature reference ═══

/// Exact a₂ via Gauss-Legendre quadrature (N-point).
///
/// a₂ = (5/2) ∫₋₁¹ (1 + AP₁(μ) + QP₂(μ))⁴ P₂(μ) dμ
///
/// This is the oracle for testing corrected_a2.
pub(crate) fn exact_a2_quadrature(a: f64, q: f64, n_pts: usize) -> f64 {
    // Gauss-Legendre nodes and weights
    let (nodes, weights) = gauss_legendre_nodes(n_pts);
    let mut integral = 0.0;
    for i in 0..n_pts {
        let mu = nodes[i];
        let w = weights[i];
        let p1 = mu;
        let p2 = 0.5 * (3.0 * mu * mu - 1.0);
        let theta = 1.0 + a * p1 + q * p2;
        integral += theta.powi(4) * p2 * w;
    }
    2.5 * integral // (5/2) factor
}

/// Gauss-Legendre nodes and weights on [-1, 1].
fn gauss_legendre_nodes(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut nodes = vec![0.0; n];
    let mut weights = vec![0.0; n];

    for i in 0..n {
        // Initial guess
        let mut x = ((i as f64 + 0.75) / (n as f64 + 0.5) * PI).cos();

        // Newton iteration for Legendre root
        for _ in 0..50 {
            let mut p0 = 1.0;
            let mut p1_val = x;
            for j in 2..=n {
                let jf = j as f64;
                let p2_val = ((2.0 * jf - 1.0) * x * p1_val - (jf - 1.0) * p0) / jf;
                p0 = p1_val;
                p1_val = p2_val;
            }
            let pp = n as f64 * (p0 - x * p1_val) / (1.0 - x * x);
            let dx = p1_val / pp;
            x -= dx;
            if dx.abs() < 1e-15 { break; }
        }
        nodes[i] = x;
        let mut p0 = 1.0;
        let mut p1_val = x;
        for j in 2..=n {
            let jf = j as f64;
            let p2_val = ((2.0 * jf - 1.0) * x * p1_val - (jf - 1.0) * p0) / jf;
            p0 = p1_val;
            p1_val = p2_val;
        }
        let pp = n as f64 * (p0 - x * p1_val) / (1.0 - x * x);
        weights[i] = 2.0 / ((1.0 - x * x) * pp * pp);
    }
    (nodes, weights)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ═══ Gauss-Legendre regression at (A,Q) = (0.30, 0.15) ═══
    // ER-CL-03 §2: exact a₂ = 1.098603 at this point

    #[test]
    fn test_corrected_a2_regression_point() {
        let a2_exact = exact_a2_quadrature(0.30, 0.15, 800);
        let a2_formula = corrected_a2(0.30, 0.15);

        eprintln!("  (A,Q) = (0.30, 0.15):");
        eprintln!("    a₂ exact  = {:.10}", a2_exact);
        eprintln!("    a₂ quartic = {:.10}", a2_formula);
        eprintln!("    rel err   = {:.2e}", (a2_formula - a2_exact).abs() / a2_exact);

        // Must agree to < 10⁻⁴ (quartic truncation at moderate A,Q)
        assert!((a2_formula - a2_exact).abs() / a2_exact < 1e-4,
            "a₂ quartic = {:.8}, exact = {:.8}", a2_formula, a2_exact);
    }

    #[test]
    fn test_corrected_a2_small_regime() {
        // At small (A, Q), quartic should match exact to machine precision
        for &(a, q) in &[(0.01, 0.01), (0.001, 0.001), (0.05, 0.02)] {
            let exact = exact_a2_quadrature(a, q, 200);
            let formula = corrected_a2(a, q);
            let rel = (formula - exact).abs() / exact.abs().max(1e-30);
            assert!(rel < 1e-6,
                "(A,Q)=({:.3},{:.3}): rel = {:.2e}", a, q, rel);
        }
    }

    // ═══ Gaunt product table verification ═══

    #[test]
    fn test_gaunt_p1_sq_to_p2() {
        // P₁² = (1/3)P₀ + (2/3)P₂ → projection onto P₂ = 2/3
        let (nodes, weights) = gauss_legendre_nodes(100);
        let mut integral = 0.0;
        for i in 0..nodes.len() {
            let mu = nodes[i];
            let p1 = mu;
            let p2 = 0.5 * (3.0 * mu * mu - 1.0);
            integral += p1 * p1 * p2 * weights[i];
        }
        let proj = 2.5 * integral; // (5/2) normalization
        assert!((proj - gaunt::P1_SQ_TO_P2).abs() < 1e-12,
            "P₁²→P₂: {:.10} vs {:.10}", proj, gaunt::P1_SQ_TO_P2);
    }

    #[test]
    fn test_gaunt_p2_sq_to_p2() {
        let (nodes, weights) = gauss_legendre_nodes(100);
        let mut integral = 0.0;
        for i in 0..nodes.len() {
            let mu = nodes[i];
            let p2 = 0.5 * (3.0 * mu * mu - 1.0);
            integral += p2 * p2 * p2 * weights[i]; // P₂² × P₂ = P₂³
        }
        let proj = 2.5 * integral;
        assert!((proj - gaunt::P2_SQ_TO_P2).abs() < 1e-12,
            "P₂²→P₂: {:.10} vs {:.10}", proj, gaunt::P2_SQ_TO_P2);
    }

    #[test]
    fn test_gaunt_p1p2_zero() {
        // P₁P₂ → P₂ = 0 by parity (kills AQ term)
        let (nodes, weights) = gauss_legendre_nodes(100);
        let mut integral = 0.0;
        for i in 0..nodes.len() {
            let mu = nodes[i];
            let p1 = mu;
            let p2 = 0.5 * (3.0 * mu * mu - 1.0);
            integral += p1 * p2 * p2 * weights[i]; // P₁ × P₂ × P₂
        }
        let proj = 2.5 * integral;
        assert!(proj.abs() < 1e-14,
            "P₁P₂→P₂: {:.4e} (must be 0 by parity)", proj);
    }

    #[test]
    fn test_gaunt_p1_4th_to_p2() {
        let (nodes, weights) = gauss_legendre_nodes(100);
        let mut integral = 0.0;
        for i in 0..nodes.len() {
            let mu = nodes[i];
            let p1 = mu;
            let p2 = 0.5 * (3.0 * mu * mu - 1.0);
            integral += p1.powi(4) * p2 * weights[i];
        }
        let proj = 2.5 * integral;
        assert!((proj - gaunt::P1_4TH_TO_P2).abs() < 1e-12,
            "P₁⁴→P₂: {:.10} vs {:.10}", proj, gaunt::P1_4TH_TO_P2);
    }

    #[test]
    fn test_gaunt_p1sq_p2_to_p2() {
        let (nodes, weights) = gauss_legendre_nodes(100);
        let mut integral = 0.0;
        for i in 0..nodes.len() {
            let mu = nodes[i];
            let p1 = mu;
            let p2 = 0.5 * (3.0 * mu * mu - 1.0);
            integral += p1 * p1 * p2 * p2 * weights[i]; // P₁²P₂ × P₂
        }
        let proj = 2.5 * integral;
        assert!((proj - gaunt::P1SQ_P2_TO_P2).abs() < 1e-12,
            "P₁²P₂→P₂: {:.10} vs {:.10}", proj, gaunt::P1SQ_P2_TO_P2);
    }

    // ═══ Individual coefficient verification ═══

    #[test]
    fn test_each_coefficient_against_quadrature() {
        // Test each term individually by setting appropriate (A, Q)
        // and checking that the formula matches quadrature.

        // Pure Q: a₂ = 4Q + (12/7)Q² + (12/7)Q³ + (20/77)Q⁴
        let q = 0.10;
        let exact_q = exact_a2_quadrature(0.0, q, 400);
        let formula_q = corrected_a2(0.0, q);
        assert!((formula_q - exact_q).abs() / exact_q.abs() < 1e-8,
            "Pure Q: formula={:.8}, exact={:.8}", formula_q, exact_q);

        // Pure A: a₂ = 4A² + (4/7)A⁴
        let a = 0.20;
        let exact_a = exact_a2_quadrature(a, 0.0, 400);
        let formula_a = corrected_a2(a, 0.0);
        assert!((formula_a - exact_a).abs() / exact_a.abs() < 1e-8,
            "Pure A: formula={:.8}, exact={:.8}", formula_a, exact_a);
    }

    // ═══ Source translation error ═══

    #[test]
    fn test_eps_th_linear_at_cf4() {
        // At CF4 parameters: A ~ 0.001, Q ~ 0.001
        // Linear error should be negligible
        let eps = eps_th_linear(0.001, 0.001);
        assert!(eps < 0.01, "CF4: eps_Th^lin = {:.4e} (must be < 1%)", eps);
    }

    #[test]
    fn test_eps_th_linear_large() {
        // At (A, Q) = (0.30, 0.15): eps_Th^lin should be ~52% (Paper V Table II)
        let eps = eps_th_linear(0.30, 0.15);
        assert!(eps > 0.3, "(0.30, 0.15): eps_Th^lin = {:.1}% (expect >30%)", eps * 100.0);
    }

    #[test]
    fn test_eps_th_quadratic_better() {
        // Quadratic approximation should be much better than linear
        let a = 0.20; let q = 0.10;
        let eps_lin = eps_th_linear(a, q);
        let eps_quad = eps_th_quadratic(a, q);
        assert!(eps_quad < eps_lin,
            "Quadratic ({:.4e}) must beat linear ({:.4e})", eps_quad, eps_lin);
    }

    // ═══ Physical limits ═══

    #[test]
    fn test_isotropic_zero() {
        // Θ = const → A = 0, Q = 0 → a₂ = 0
        assert_eq!(corrected_a2(0.0, 0.0), 0.0);
    }

    #[test]
    fn test_linear_limit() {
        // Θ = 1 + εP₂ → a₂ ≈ 4ε at leading order
        let eps = 1e-6;
        let a2 = corrected_a2(0.0, eps);
        assert!((a2 - 4.0 * eps).abs() / (4.0 * eps) < 1e-5,
            "Linear limit: a₂ = {:.6e} vs 4ε = {:.6e}", a2, 4.0 * eps);
    }

    #[test]
    fn test_dipole_squared_generates_quadrupole() {
        // Θ = 1 + εP₁ → a₂ = 4ε² (dipole² → quadrupole)
        let eps = 0.01;
        let a2 = corrected_a2(eps, 0.0);
        let expected = 4.0 * eps * eps;
        assert!((a2 - expected).abs() / expected < 0.01,
            "Dipole²: a₂ = {:.6e} vs 4A² = {:.6e}", a2, expected);
    }

    // ═══ Full bridge test ═══

    #[test]
    fn test_full_bridge_flrw() {
        let result = full_thomson_bridge(1.0, 0.0, &[0.0; 5], 6.0);
        for m in 0..5 {
            assert!(result[m].abs() < 1e-30, "FLRW: I_{{2m}} = {:.4e}", result[m]);
        }
    }

    #[test]
    fn test_full_bridge_pure_quadrupole() {
        let f2 = [0.01, 0.0, 0.0, 0.0, 0.0];
        let result = full_thomson_bridge(1.0, 0.0, &f2, 1.0);
        // With only quadrupole input, a₂ linear → I_{2m} ∝ F_{2m}
        assert!(result[0].abs() > 0.0, "Pure quad: must be nonzero");
    }

    #[test]
    fn test_full_bridge_dipole_creates_quadrupole() {
        let f2 = [0.0; 5]; // no quadrupole input
        let result = full_thomson_bridge(1.0, 0.1, &f2, 1.0);
        // Pure dipole: a₂ = 4A² = 0.04, distributed to m=0
        assert!(result[2].abs() > 0.0,
            "Dipole → quadrupole: I_{{20}} = {:.4e}", result[2]);
    }
}
