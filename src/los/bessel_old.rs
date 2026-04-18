// Spherical Bessel functions j_ℓ(x) for LoS integration.
//
// Three regimes:
//   1. Miller backward recurrence: exact, used for ℓ ≤ 30 or validation
//   2. WKB/asymptotic: fast, for ℓ > 30 and x > ℓ
//   3. Precomputed table: fastest, for repeated evaluation at many x

use std::f64::consts::PI;

/// Compute j_ℓ(x) — auto-dispatches to best method.
pub(crate) fn spherical_bessel_j(ell: usize, x: f64) -> f64 {
    if x.abs() < 1e-15 {
        return if ell == 0 { 1.0 } else { 0.0 };
    }
    if ell == 0 { return x.sin() / x; }
    if ell == 1 { return x.sin() / (x * x) - x.cos() / x; }

    // Small x: j_ℓ(x) ≈ x^ℓ / (2ℓ+1)!!
    if x < 0.1 * (ell as f64) {
        let mut val = 1.0;
        for i in 0..ell { val *= x / (2 * i + 3) as f64; }
        return val;
    }

    // For high ℓ with x > ℓ: WKB asymptotic (fast)
    if ell > 30 && x > ell as f64 * 1.1 {
        return bessel_j_wkb(ell, x);
    }

    // Default: Miller backward recurrence (exact, slower)
    bessel_j_miller(ell, x)
}

/// Miller backward recurrence (exact for all ℓ, x).
pub(crate) fn bessel_j_miller(ell: usize, x: f64) -> f64 {
    let l_start = ell + 20 + (x as usize);
    let l_start = l_start.max(ell + 30);
    let mut j_prev = 0.0_f64;
    let mut j_curr = 1e-30_f64;
    let mut result = 0.0;

    for l in (0..=l_start).rev() {
        let j_next = (2 * l + 3) as f64 / x * j_curr - j_prev;
        j_prev = j_curr;
        j_curr = j_next;
        if l == ell { result = j_next; }
        if j_curr.abs() > 1e100 {
            j_curr *= 1e-100; j_prev *= 1e-100; result *= 1e-100;
        }
    }
    let j0_exact = x.sin() / x;
    result * j0_exact / j_curr
}

/// WKB asymptotic approximation for j_ℓ(x) when x > ℓ.
///
/// j_ℓ(x) ≈ 1/√(x² − ν²) × cos(√(x²−ν²) − ν arccos(ν/x) − π/4)
/// where ν = ℓ + 1/2. Valid for x > ν (oscillatory regime).
fn bessel_j_wkb(ell: usize, x: f64) -> f64 {
    let nu = ell as f64 + 0.5;
    if x <= nu { return bessel_j_miller(ell, x); }

    let q = (x * x - nu * nu).sqrt();
    let phase = q - nu * (nu / x).acos() - PI / 4.0;
    phase.cos() / q
}

/// Precomputed Bessel table for fast repeated evaluation.
///
/// Stores j_ℓ(x) on a uniform x-grid for each ℓ.
pub(crate) struct BesselTable {
    ell_max: usize,
    x_max: f64,
    dx: f64,
    nx: usize,
    /// data[ell][ix] = j_ℓ(ix × dx)
    data: Vec<Vec<f64>>,
}

impl BesselTable {
    /// Build table for ℓ = 0..ℓ_max, x = 0..x_max with spacing dx.
    pub(crate) fn new(ell_max: usize, x_max: f64, dx: f64) -> Self {
        let nx = (x_max / dx) as usize + 1;
        let mut data = Vec::with_capacity(ell_max + 1);
        for ell in 0..=ell_max {
            let mut row = Vec::with_capacity(nx);
            for ix in 0..nx {
                let x = ix as f64 * dx;
                row.push(spherical_bessel_j(ell, x));
            }
            data.push(row);
        }
        Self { ell_max, x_max, dx, nx, data }
    }

    /// Look up j_ℓ(x) with linear interpolation.
    pub(crate) fn eval(&self, ell: usize, x: f64) -> f64 {
        if ell > self.ell_max || x < 0.0 { return 0.0; }
        if x >= self.x_max { return spherical_bessel_j(ell, x); }
        let fx = x / self.dx;
        let ix = fx as usize;
        if ix >= self.nx - 1 { return self.data[ell][self.nx - 1]; }
        let t = fx - ix as f64;
        self.data[ell][ix] * (1.0 - t) + self.data[ell][ix + 1] * t
    }

    pub(crate) fn ell_max(&self) -> usize { self.ell_max }
    pub(crate) fn memory_bytes(&self) -> usize { self.data.len() * self.nx * 8 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_j0() {
        let x = 3.0;
        let j = spherical_bessel_j(0, x);
        let exact = x.sin() / x;
        assert!((j - exact).abs() < 1e-12, "j₀(3) = {:.10} vs {:.10}", j, exact);
    }

    #[test]
    fn test_j1() {
        let x = 2.5;
        let j = spherical_bessel_j(1, x);
        let exact = x.sin() / (x * x) - x.cos() / x;
        assert!((j - exact).abs() < 1e-12, "j₁(2.5) = {:.10} vs {:.10}", j, exact);
    }

    #[test]
    fn test_j0_at_zero() {
        assert!((spherical_bessel_j(0, 0.0) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn test_jl_at_zero() {
        for ell in 1..10 {
            assert!(spherical_bessel_j(ell, 0.0).abs() < 1e-12);
        }
    }

    #[test]
    fn test_j10() {
        // j_10(10) = 0.06460515 (scipy.special.spherical_jn)
        let j = spherical_bessel_j(10, 10.0);
        assert!((j - 0.06460515).abs() < 1e-5, "j_10(10) = {:.8}", j);
    }

    #[test]
    fn test_j_large_ell() {
        // j_100(50) should be very small (x < ℓ regime)
        let j = spherical_bessel_j(100, 50.0);
        assert!(j.abs() < 1e-5, "j_100(50) = {:.4e}", j);
    }

    #[test]
    fn test_j_large_x() {
        // j_2(100) should be oscillatory, |j| < 1/100
        let j = spherical_bessel_j(2, 100.0);
        assert!(j.abs() < 0.02, "j_2(100) = {:.6}", j);
    }
}
