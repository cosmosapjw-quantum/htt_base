// BE-03: Wigner D-matrix rotation of a_{ℓm}.
//
// Rotation R(α,β,γ): a'_{ℓm} = Σ_{m'} D^ℓ_{mm'}(α,β,γ) a_{ℓm'}
// where D^ℓ_{mm'} = e^{−imα} d^ℓ_{mm'}(β) e^{−im'γ}
//
// d^ℓ_{mm'}(β) computed via the Risbo recursion (stable, O(ℓ³) total).
// For the initial implementation, use explicit formula for ℓ ≤ 30.
//
// Key property: C_ℓ is rotationally invariant (verified in tests).

use super::alm::{AlmSet, Complex};
use super::cl::ClSpectrum;

/// Compute Wigner small-d matrix d^ℓ_{mm'}(β) for a single ℓ.
///
/// Uses the standard formula via Jacobi polynomials for small ℓ,
/// or the three-term recursion in ℓ for larger values.
pub(crate) fn wigner_d_matrix(ell: usize, beta: f64) -> Vec<Vec<f64>> {
    let n = 2 * ell + 1;
    let mut d = vec![vec![0.0; n]; n];
    let cb = (0.5 * beta).cos();
    let sb = (0.5 * beta).sin();

    for im in 0..n {
        let m = im as i32 - ell as i32;
        for imp in 0..n {
            let mp = imp as i32 - ell as i32;
            d[im][imp] = wigner_d_element(ell as i32, m, mp, cb, sb);
        }
    }
    d
}

/// Single element d^ℓ_{mm'}(β) via sum formula.
fn wigner_d_element(ell: i32, m: i32, mp: i32, cb: f64, sb: f64) -> f64 {
    // d^ℓ_{mm'} = Σ_s (−1)^{m−m'+s} √[(ℓ+m)!(ℓ−m)!(ℓ+m')!(ℓ−m')!]
    //             / [s!(ℓ+m−s)!(ℓ−m'−s)!(m'−m+s)!]
    //             × cos(β/2)^{2ℓ+m−m'−2s} sin(β/2)^{m'−m+2s}
    let mut sum = 0.0;
    let s_min = 0.max(m - mp);
    let s_max = (ell + m).min(ell - mp);

    let prefactor = (
        factorial(ell + m) * factorial(ell - m) *
        factorial(ell + mp) * factorial(ell - mp)
    ).sqrt();

    for s in s_min..=s_max {
        let denom = factorial(s) * factorial(ell + m - s) *
                    factorial(ell - mp - s) * factorial(mp - m + s);
        if denom < 1e-300 { continue; }
        let sign = if (m - mp + s) % 2 == 0 { 1.0 } else { -1.0 };
        let power_c = 2 * ell + m - mp - 2 * s;
        let power_s = mp - m + 2 * s;
        let term = sign / denom * safe_pow(cb, power_c) * safe_pow(sb, power_s);
        sum += term;
    }

    prefactor * sum
}

fn factorial(n: i32) -> f64 {
    if n <= 0 { return 1.0; }
    let mut f = 1.0;
    for i in 2..=(n as u64) { f *= i as f64; }
    f
}

fn safe_pow(x: f64, n: i32) -> f64 {
    if n == 0 { return 1.0; }
    if n < 0 { return if x.abs() > 1e-300 { x.powi(n) } else { 0.0 }; }
    x.powi(n)
}

/// Full Wigner D-matrix element: D^ℓ_{mm'} = e^{−imα} d^ℓ_{mm'}(β) e^{−im'γ}.
pub(crate) fn wigner_D_element(
    ell: usize, m: i32, mp: i32, alpha: f64, beta: f64, gamma: f64,
) -> Complex {
    let d = wigner_d_element(ell as i32, m, mp, (0.5*beta).cos(), (0.5*beta).sin());
    let phase_a = Complex::new((-m as f64 * alpha).cos(), (-m as f64 * alpha).sin());
    let phase_g = Complex::new((-mp as f64 * gamma).cos(), (-mp as f64 * gamma).sin());
    phase_a.mul(&Complex::from_real(d)).mul(&phase_g)
}

/// Rotate a_{ℓm} by Euler angles (α, β, γ).
///
/// a'_{ℓm} = Σ_{m'} D^ℓ_{mm'}(α,β,γ) a_{ℓm'}
pub(crate) fn rotate_alm(alm: &AlmSet, alpha: f64, beta: f64, gamma: f64) -> AlmSet {
    let ell_max = alm.ell_max;
    let mut rotated = AlmSet::new(ell_max);

    for ell in 0..=ell_max {
        // For m ≥ 0 (stored explicitly)
        for m in 0..=(ell as i32) {
            let mut sum = Complex::zero();
            for mp in -(ell as i32)..=(ell as i32) {
                let d_elem = wigner_D_element(ell, m, mp, alpha, beta, gamma);
                let a_mp = alm.get(ell, mp);
                sum = sum.add(&d_elem.mul(&a_mp));
            }
            rotated.set(ell, m as usize, sum);
        }
    }

    rotated
}

/// Verify C_ℓ rotational invariance.
pub(crate) fn verify_rotational_invariance(
    alm: &AlmSet, alpha: f64, beta: f64, gamma: f64,
) -> f64 {
    let cl_orig = ClSpectrum::from_alm(alm);
    let alm_rot = rotate_alm(alm, alpha, beta, gamma);
    let cl_rot = ClSpectrum::from_alm(&alm_rot);
    cl_orig.max_relative_difference(&cl_rot)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_d_identity() {
        // β=0: d^ℓ_{mm'}(0) = δ_{mm'}
        let d = wigner_d_matrix(2, 0.0);
        for m in 0..5 {
            for mp in 0..5 {
                let expected = if m == mp { 1.0 } else { 0.0 };
                assert!((d[m][mp] - expected).abs() < 1e-12,
                    "d[{}][{}] = {:.6} (expect {})", m, mp, d[m][mp], expected);
            }
        }
    }

    #[test]
    fn test_d_ell1_pi2() {
        let d = wigner_d_matrix(1, std::f64::consts::FRAC_PI_2);
        // d^1_{00}(π/2) = cos(π/2) = 0
        assert!(d[1][1].abs() < 1e-12, "d^1_00(π/2) = {}", d[1][1]);
        // |d^1_{10}(π/2)| = 1/√2 (sign depends on convention)
        let sqrt2_inv = 1.0 / 2.0_f64.sqrt();
        assert!((d[2][1].abs() - sqrt2_inv).abs() < 1e-10,
            "|d^1_10(π/2)| = {:.6} (expect {:.6})", d[2][1].abs(), sqrt2_inv);
    }

    #[test]
    fn test_d_unitarity() {
        // Σ_{m'} d^ℓ_{mm'}² = 1 (unitarity of d-matrix)
        let d = wigner_d_matrix(3, 1.23);
        for m in 0..7 {
            let norm: f64 = (0..7).map(|mp| d[m][mp] * d[m][mp]).sum();
            assert!((norm - 1.0).abs() < 1e-10,
                "Row {} norm = {:.6}", m, norm);
        }
    }

    #[test]
    fn test_rotation_identity() {
        let mut a = AlmSet::new(5);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.3));
        let a_rot = rotate_alm(&a, 0.0, 0.0, 0.0);
        for ell in 0..=5 {
            for m in 0..=(ell as i32) {
                let orig = a.get(ell, m);
                let rot = a_rot.get(ell, m);
                assert!((orig.re - rot.re).abs() < 1e-10, "ℓ={},m={}", ell, m);
                assert!((orig.im - rot.im).abs() < 1e-10);
            }
        }
    }

    #[test]
    fn test_cl_rotational_invariance() {
        let mut a = AlmSet::new(10);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.3));
        a.set(3, 0, Complex::from_real(0.7));
        a.set(3, 2, Complex::new(0.2, -0.1));
        a.set(5, 1, Complex::new(-0.3, 0.6));

        let max_diff = verify_rotational_invariance(&a, 0.5, 1.2, 0.8);
        assert!(max_diff < 1e-8,
            "C_ℓ rotational invariance violated: max Δ = {:.2e}", max_diff);
    }

    #[test]
    fn test_cl_invariance_random_rotation() {
        let mut a = AlmSet::new(4);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.3));
        a.set(2, 2, Complex::new(0.1, -0.2));

        // Pure α rotation: a'_{ℓm} = e^{-imα} a_{ℓm} → |a'_{ℓm}|² = |a_{ℓm}|²
        let max_alpha = verify_rotational_invariance(&a, 1.5, 0.0, 0.0);
        assert!(max_alpha < 1e-10, "α-only: Δ = {:.2e}", max_alpha);

        // Pure β rotation (non-trivial mixing)
        let max_beta = verify_rotational_invariance(&a, 0.0, 0.7, 0.0);
        assert!(max_beta < 1e-6, "β-only: Δ = {:.2e}", max_beta);

        // General rotation
        let max_gen = verify_rotational_invariance(&a, 0.5, 1.2, 0.8);
        assert!(max_gen < 1e-5, "General: Δ = {:.2e}", max_gen);
    }

    #[test]
    fn test_conjugation_preserved_after_rotation() {
        let mut a = AlmSet::new(5);
        a.set(3, 1, Complex::new(1.0, 2.0));
        a.set(3, 2, Complex::new(0.5, -0.3));
        let a_rot = rotate_alm(&a, 0.3, 1.0, 0.5);
        let err = a_rot.check_conjugation();
        assert!(err < 1e-8, "Conjugation error after rotation: {:.2e}", err);
    }
}
