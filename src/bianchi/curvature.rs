// Spatial curvature for Bianchi models.
// BB-03: ³R, ³R_{ab}, ³S_{ab}, Ω_k from Ellis-MacCallum parameters.
//
// All formulas algebraic — computed directly from (n₁,n₂,n₃,a).
// No Riemann tensor computation needed.
//
// Key identity: ³R_{αα} = −n_α(n_β+n_γ) + n_βn_γ + (4/3)a²
// where (α,β,γ) cyclic. Verified for all 9 types.

use super::types::*;

/// Spatial Ricci scalar:
///   ³R = −(1/2)[(n^α_α)² − n_{αβ}n^{αβ}] + 4a²
///      = −(n₁n₂ + n₁n₃ + n₂n₃) + 4a²
pub(crate) fn spatial_ricci_scalar(n: &[f64; 3], a_mag: f64) -> f64 {
    -(n[0]*n[1] + n[0]*n[2] + n[1]*n[2]) + 4.0 * a_mag * a_mag
}

/// Diagonal spatial Ricci tensor components ³R_{αα}.
///
/// ³R_{αα} = −n_α(n_β + n_γ) + n_βn_γ + (4/3)a²
///
/// Returns [³R_{11}, ³R_{22}, ³R_{33}].
/// Off-diagonal components vanish in the canonical diagonal frame.
pub(crate) fn spatial_ricci_diagonal(n: &[f64; 3], a_mag: f64) -> [f64; 3] {
    let a2_term = (4.0 / 3.0) * a_mag * a_mag;
    [
        -n[0]*(n[1]+n[2]) + n[1]*n[2] + a2_term,
        -n[1]*(n[0]+n[2]) + n[0]*n[2] + a2_term,
        -n[2]*(n[0]+n[1]) + n[0]*n[1] + a2_term,
    ]
}

/// Trace-free spatial Ricci tensor ³S_{ab} = ³R_{ab} − (1/3)³R δ_{ab}.
///
/// Returns diagonal components [³S_{11}, ³S_{22}, ³S_{33}].
/// Satisfies S₁₁ + S₂₂ + S₃₃ = 0 identically.
pub(crate) fn spatial_ricci_tracefree(n: &[f64; 3], a_mag: f64) -> [f64; 3] {
    let r_diag = spatial_ricci_diagonal(n, a_mag);
    let r3 = spatial_ricci_scalar(n, a_mag);
    let r3_third = r3 / 3.0;
    [
        r_diag[0] - r3_third,
        r_diag[1] - r3_third,
        r_diag[2] - r3_third,
    ]
}

/// Curvature density parameter Ω_k = −³R / (6H²).
pub(crate) fn omega_k(r3: f64, h: f64) -> f64 {
    -r3 / (6.0 * h * h)
}

/// Anisotropic curvature contribution: Ω_{k,aniso} = ³S_{ab}³S^{ab} / (6H⁴).
pub(crate) fn omega_k_aniso(s_diag: &[f64; 3], h: f64) -> f64 {
    let s2 = s_diag[0]*s_diag[0] + s_diag[1]*s_diag[1] + s_diag[2]*s_diag[2];
    s2 / (6.0 * h.powi(4))
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Type I: everything zero ──
    #[test]
    fn test_bi_all_zero() {
        let n = [0.0, 0.0, 0.0];
        assert_eq!(spatial_ricci_scalar(&n, 0.0), 0.0);
        let r = spatial_ricci_diagonal(&n, 0.0);
        assert_eq!(r, [0.0, 0.0, 0.0]);
        let s = spatial_ricci_tracefree(&n, 0.0);
        assert_eq!(s, [0.0, 0.0, 0.0]);
    }

    // ── Type V: ³R = 4a² > 0, ³S = 0 ──
    #[test]
    fn test_bv_isotropic() {
        let n = [0.0, 0.0, 0.0];
        let a = 1.0;
        let r3 = spatial_ricci_scalar(&n, a);
        assert!((r3 - 4.0).abs() < 1e-15, "BV: ³R = {} (expect 4)", r3);
        let s = spatial_ricci_tracefree(&n, a);
        for i in 0..3 {
            assert!(s[i].abs() < 1e-15, "BV: ³S_{}{} = {:.2e} (must be 0)", i, i, s[i]);
        }
        // Ω_k < 0 (open)
        let ok = omega_k(r3, 1.0);
        assert!(ok < 0.0, "BV: Ω_k = {} must be < 0 (open)", ok);
    }

    // ── Type IX: ³R = −3, Ω_k > 0, ³S = 0 ──
    #[test]
    fn test_bix_closed() {
        let n = [1.0, 1.0, 1.0];
        let r3 = spatial_ricci_scalar(&n, 0.0);
        assert!((r3 - (-3.0)).abs() < 1e-15, "BIX: ³R = {} (expect -3)", r3);
        let ok = omega_k(r3, 1.0);
        assert!((ok - 0.5).abs() < 1e-15, "BIX: Ω_k = {} (expect 0.5)", ok);
        let s = spatial_ricci_tracefree(&n, 0.0);
        for i in 0..3 { assert!(s[i].abs() < 1e-15, "BIX: ³S_{}{} = {:.2e}", i, i, s[i]); }
    }

    // ── Type VIII: anisotropic ³S ≠ 0 ──
    #[test]
    fn test_bviii_anisotropic() {
        let n = [1.0, 1.0, -1.0]; // VIII: −,+,+
        let r3 = spatial_ricci_scalar(&n, 0.0);
        assert!((r3 - 1.0).abs() < 1e-15, "BVIII: ³R = {} (expect 1)", r3);
        let s = spatial_ricci_tracefree(&n, 0.0);
        let s_norm = (s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt();
        assert!(s_norm > 0.1, "BVIII: ||³S|| = {} must be > 0", s_norm);
        // Trace-free check
        let tr = s[0]+s[1]+s[2];
        assert!(tr.abs() < 1e-15, "BVIII: tr(³S) = {:.2e}", tr);
    }

    // ── Type II: ³R = 0 ──
    #[test]
    fn test_bii_zero_scalar() {
        let n = [1.0, 0.0, 0.0];
        let r3 = spatial_ricci_scalar(&n, 0.0);
        assert!(r3.abs() < 1e-15, "BII: ³R = {:.2e} (expect 0)", r3);
    }

    // ── Trace-free property for all types ──
    #[test]
    fn test_tracefree_all() {
        for btype in all_canonical_types() {
            let p = btype.canonical_params();
            let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
            let tr = s[0] + s[1] + s[2];
            assert!(tr.abs() < 1e-14, "{}: tr(³S) = {:.2e}", btype.label(), tr);
        }
    }

    // ── Trace matches scalar for all types ──
    #[test]
    fn test_trace_matches_scalar() {
        for btype in all_canonical_types() {
            let p = btype.canonical_params();
            let r3 = spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude);
            let r_diag = spatial_ricci_diagonal(&p.n_eigenvalues, p.a_magnitude);
            let tr = r_diag[0] + r_diag[1] + r_diag[2];
            let diff = (tr - r3).abs();
            assert!(diff < 1e-14, "{}: tr(³R_ab)={:.6e} vs ³R={:.6e}", btype.label(), tr, r3);
        }
    }

    // ── BV: ³S = 0 (algebraic identity) ──
    #[test]
    fn test_bv_tracefree_zero() {
        let p = BianchiType::V.canonical_params();
        let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
        let norm = (s[0]*s[0]+s[1]*s[1]+s[2]*s[2]).sqrt();
        assert!(norm < 1e-15, "BV: ||³S|| = {:.2e} (algebraic identity: must be 0)", norm);
    }

    // ── Class B: positive ³R contribution from a ──
    #[test]
    fn test_class_b_positive_contribution() {
        let p = BianchiType::V.canonical_params();
        assert!(spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude) > 0.0);
    }

    // ── Parametric VII_h tests ──
    #[test]
    fn test_viih_curvature() {
        for &h in &[0.01, 0.1, 0.5, 1.0, 10.0] {
            let p = BianchiType::VIIh(h).canonical_params();
            let r3 = spatial_ricci_scalar(&p.n_eigenvalues, p.a_magnitude);
            let s = spatial_ricci_tracefree(&p.n_eigenvalues, p.a_magnitude);
            let tr = s[0]+s[1]+s[2];
            assert!(tr.abs() < 1e-14, "VII_h({}): tr(³S) = {:.2e}", h, tr);
            // VII_h has n₁=n₂=1, n₃=0, a=√h → ³R = -(1+0+0) + 4h = -1+4h
            let expected = -1.0 + 4.0*h;
            assert!((r3-expected).abs() < 1e-12, "VII_h({}): ³R={:.4} (expect {:.4})", h, r3, expected);
        }
    }
}
