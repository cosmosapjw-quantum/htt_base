// BG-01: Teff Spectral Utilities.
//
// Polylogarithmic spectral integrals I_n^(ξ)(η) — foundation of all Teff calculations.
//
// Three statistics:
//   BE (ξ=+1): I_n = Γ(n+1) Li_{n+1}(e^η)        [Bose-Einstein]
//   FD (ξ=−1): I_n = −Γ(n+1) Li_{n+1}(−e^η)       [Fermi-Dirac]
//   MB (ξ= 0): I_n = Γ(n+1) e^η                     [Maxwell-Boltzmann]
//
// All I_n > 0 (manifest positivity).
// Standard values: I₃^{(+1)}(0) = π⁴/15, I₃^{(−1)}(0) = 7π⁴/120.
//
// x-coordinate: x = E/(k_B T₀) > 0, mandatory for multi-component two-field.

use std::f64::consts::PI;

/// Statistics label.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum Statistics {
    BoseEinstein, // ξ = +1
    FermiDirac,   // ξ = −1
    MaxwellBoltzmann, // ξ = 0
}

// ═══ Polylogarithm Li_s(z) ═══

/// Polylogarithm Li_s(z) for real s > 0 and real z.
///
/// Li_s(z) = Σ_{k=1}^∞ z^k / k^s  for |z| ≤ 1.
/// For |z| > 1: use identity Li_s(z) + (-1)^s Li_s(1/z) = ... (Jonquière).
/// For z = e^η with η > 0 (BE case): use the integral representation.
pub(crate) fn polylog(s: f64, z: f64) -> f64 {
    if z.abs() < 1e-30 { return 0.0; }

    // Special cases for integer s
    if (s - 1.0).abs() < 1e-10 { return polylog_1(z); }

    if z.abs() <= 0.9 {
        // Direct series: Li_s(z) = Σ z^k / k^s
        polylog_series(s, z)
    } else if z > 0.0 && z < 1.5 {
        // Near z=1: use Bose integral representation via series with Bernoulli
        polylog_near_one(s, z)
    } else if z < 0.0 && z > -1.5 {
        // Fermi case: Li_s(-|z|)
        polylog_series_slow(s, z)
    } else if z > 1.5 {
        // Large positive z: asymptotic expansion
        polylog_large_positive(s, z)
    } else {
        // Large negative z
        polylog_series_slow(s, z)
    }
}

/// Li_1(z) = −ln(1−z) (exact).
fn polylog_1(z: f64) -> f64 {
    if z >= 1.0 { return f64::INFINITY; }
    -(1.0 - z).ln()
}

/// Series for |z| < 1: Li_s(z) = Σ_{k=1}^N z^k/k^s.
fn polylog_series(s: f64, z: f64) -> f64 {
    let mut sum = 0.0;
    let mut zk = z;
    for k in 1..=500 {
        let term = zk / (k as f64).powf(s);
        sum += term;
        if term.abs() < 1e-15 * sum.abs() { break; }
        zk *= z;
    }
    sum
}

/// Slow series for any z with |z| not too large.
fn polylog_series_slow(s: f64, z: f64) -> f64 {
    let mut sum = 0.0;
    let mut zk = z;
    for k in 1..=2000 {
        let term = zk / (k as f64).powf(s);
        sum += term;
        if term.abs() < 1e-14 * sum.abs().max(1e-30) && k > 10 { break; }
        zk *= z;
        // Prevent overflow
        if zk.abs() > 1e100 { break; }
    }
    sum
}

/// Near z = 1: Li_s(z) ≈ Γ(1−s)(−ln z)^{s−1} + Σ ζ(s−k)(ln z)^k/k!
fn polylog_near_one(s: f64, z: f64) -> f64 {
    if (z - 1.0).abs() < 1e-12 {
        // Li_s(1) = ζ(s)
        return riemann_zeta(s);
    }
    // For z near 1 but not exactly 1: use series with care
    let ln_z = z.ln();
    if ln_z.abs() < 0.5 {
        // Expansion around z=1: Li_s(e^η) for small η
        // Li_s(e^η) = Γ(1-s)(-η)^{s-1} + Σ_{k=0} ζ(s-k) η^k/k!
        // For integer s: the Γ pole gives a logarithmic term
        let si = s.round() as i32;
        if (s - si as f64).abs() < 1e-10 && si >= 2 {
            return polylog_integer_near_one(si as usize, ln_z);
        }
    }
    // Fallback to slow series
    polylog_series_slow(s, z)
}

/// Li_n(e^η) for integer n ≥ 2, small η = ln(z).
fn polylog_integer_near_one(n: usize, eta: f64) -> f64 {
    // Li_n(e^η) = ζ(n) + ζ(n-1)η + ζ(n-2)η²/2! + ... + η^{n-1}/(n-1)! × (H_{n-1} − ln(−η))
    // For η → 0+: use direct numerical evaluation
    let z = eta.exp();
    if z > 0.0 && z < 2.0 {
        polylog_series_slow(n as f64, z)
    } else {
        polylog_series_slow(n as f64, z)
    }
}

/// Large positive z: Li_s(z) ~ (ln z)^s / Γ(s+1) + π²(ln z)^{s-2}/(6Γ(s-1)) + ...
fn polylog_large_positive(s: f64, z: f64) -> f64 {
    let eta = z.ln();
    if eta <= 0.0 { return polylog_series_slow(s, z); }
    // Sommerfeld expansion for Li_s(e^η), η > 0:
    // Li_s(e^η) = η^s/Γ(s+1) + π²η^{s-2}/(6Γ(s-1)) + 7π⁴η^{s-4}/(360Γ(s-3)) + ...
    let g = gamma(s + 1.0);
    let mut sum = eta.powf(s) / g;
    if s > 2.0 {
        let g2 = gamma(s - 1.0);
        sum += PI * PI / 6.0 * eta.powf(s - 2.0) / g2;
    }
    if s > 4.0 {
        let g4 = gamma(s - 3.0);
        sum += 7.0 * PI.powi(4) / 360.0 * eta.powf(s - 4.0) / g4;
    }
    sum
}

/// Riemann zeta function for real s > 1 (small integer cases + series).
pub(crate) fn riemann_zeta(s: f64) -> f64 {
    let si = s.round() as i32;
    if (s - si as f64).abs() < 1e-10 {
        match si {
            2 => return PI * PI / 6.0,
            3 => return 1.2020569031595942, // Apéry's constant
            4 => return PI.powi(4) / 90.0,
            5 => return 1.0369277551433699,
            6 => return PI.powi(6) / 945.0,
            _ => {}
        }
    }
    // Series: ζ(s) = Σ 1/k^s (slow convergence, use for non-integer s)
    let mut sum = 0.0;
    for k in 1..=10000 {
        let term = 1.0 / (k as f64).powf(s);
        sum += term;
        if term < 1e-14 * sum { break; }
    }
    sum
}

/// Gamma function Γ(x) for real x > 0 (Lanczos approximation).
pub(crate) fn gamma(x: f64) -> f64 {
    if x <= 0.0 { return f64::INFINITY; }
    // For positive integers
    let xi = x.round() as i64;
    if (x - xi as f64).abs() < 1e-12 && xi > 0 && xi <= 20 {
        let mut f = 1.0;
        for k in 2..xi { f *= k as f64; }
        return f;
    }
    // Lanczos with g=7
    let p = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
             771.32342877765313, -176.61502916214059, 12.507343278686905,
             -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    let x = x - 1.0;
    let mut y = p[0];
    for i in 1..9 { y += p[i] / (x + i as f64); }
    let t = x + 7.5;
    (2.0 * PI).sqrt() * t.powf(x + 0.5) * (-t).exp() * y
}

// ═══ Spectral Integrals I_n^(ξ)(η) ═══

/// Spectral integral I_n^(ξ)(η).
///
/// BE: I_n = Γ(n+1) Li_{n+1}(e^η)       [η ≤ 0 for convergence]
/// FD: I_n = −Γ(n+1) Li_{n+1}(−e^η)     [manifestly positive: −Li(−z) > 0]
/// MB: I_n = Γ(n+1) e^η
///
/// For FD at large positive η: Sommerfeld expansion.
pub(crate) fn spectral_integral(n: usize, stat: Statistics, eta: f64) -> f64 {
    let gn1 = gamma(n as f64 + 1.0);
    match stat {
        Statistics::BoseEinstein => {
            // BE: only physical for η ≤ 0 (otherwise divergent)
            let z = eta.exp();
            gn1 * polylog(n as f64 + 1.0, z)
        }
        Statistics::FermiDirac => {
            if eta > 2.0 {
                // Sommerfeld expansion for degenerate Fermi gas:
                // I_n^FD(η) = η^{n+1}/(n+1) + π²n η^{n-1}/6 + 7π⁴n(n-1)(n-2)η^{n-3}/360 + ...
                fd_sommerfeld(n, eta)
            } else {
                // Series: -Γ(n+1) Li_{n+1}(-e^η)
                let z = eta.exp();
                -gn1 * polylog(n as f64 + 1.0, -z)
            }
        }
        Statistics::MaxwellBoltzmann => {
            gn1 * eta.exp()
        }
    }
}

/// Sommerfeld expansion for Fermi-Dirac spectral integral at large η > 0.
///
/// I_n^{FD}(η) = η^{n+1}/(n+1) + (π²/6) n η^{n-1} + (7π⁴/360) n(n-1)(n-2) η^{n-3} + ...
fn fd_sommerfeld(n: usize, eta: f64) -> f64 {
    let nf = n as f64;
    let mut sum = eta.powf(nf + 1.0) / (nf + 1.0);
    if n >= 1 {
        sum += PI * PI / 6.0 * nf * eta.powf((nf - 1.0).max(0.0));
    }
    if n >= 3 {
        sum += 7.0 * PI.powi(4) / 360.0 * nf * (nf - 1.0) * (nf - 2.0) * eta.powf((nf - 3.0).max(0.0));
    }
    sum
}

/// First derivative: dI_n/dη = I_{n−1}^(ξ)(η).
///
/// This is the recurrence relation of spectral integrals.
pub(crate) fn d_spectral_deta(n: usize, stat: Statistics, eta: f64) -> f64 {
    if n == 0 {
        // dI_0/dη = 1/(e^{−η} ± 1) — direct computation
        let z = eta.exp();
        match stat {
            Statistics::BoseEinstein => z / (1.0 - z).max(1e-30),
            Statistics::FermiDirac => z / (1.0 + z),
            Statistics::MaxwellBoltzmann => z,
        }
    } else {
        spectral_integral(n - 1, stat, eta)
    }
}

/// Second derivative: d²I_n/dη² = I_{n−2}^(ξ)(η).
pub(crate) fn d2_spectral_deta2(n: usize, stat: Statistics, eta: f64) -> f64 {
    if n < 2 {
        // Numerical fallback for n < 2
        let h = 1e-5;
        let ip = spectral_integral(n, stat, eta + h);
        let im = spectral_integral(n, stat, eta - h);
        let i0 = spectral_integral(n, stat, eta);
        (ip - 2.0 * i0 + im) / (h * h)
    } else {
        spectral_integral(n - 2, stat, eta)
    }
}

/// Spectral factor: F_n = Θ^{n+1} I_n(η).
///
/// Θ = T/T₀ (dimensionless temperature), η = μ/(k_B T₀) (chemical potential).
pub(crate) fn spectral_factor(n: usize, theta: f64, eta: f64, stat: Statistics) -> f64 {
    theta.powi(n as i32 + 1) * spectral_integral(n, stat, eta)
}

#[cfg(test)]
mod tests {
    use super::*;
    use Statistics::*;

    // ═══ Polylogarithm tests ═══

    #[test]
    fn test_polylog_li2_small() {
        // Li_2(0.5) = π²/12 − (ln 2)²/2 ≈ 0.58225
        let li2 = polylog(2.0, 0.5);
        let exact = PI * PI / 12.0 - 0.5 * 2.0_f64.ln().powi(2);
        assert!((li2 - exact).abs() < 1e-8, "Li_2(0.5) = {:.8} vs {:.8}", li2, exact);
    }

    #[test]
    fn test_polylog_zeta2() {
        // Li_2(1) = ζ(2) = π²/6
        let li2 = polylog(2.0, 1.0);
        assert!((li2 - PI * PI / 6.0).abs() < 1e-6, "Li_2(1) = {:.8}", li2);
    }

    #[test]
    fn test_polylog_zeta4() {
        // Li_4(1) = ζ(4) = π⁴/90
        let li4 = polylog(4.0, 1.0);
        assert!((li4 - PI.powi(4) / 90.0).abs() < 1e-6, "Li_4(1) = {:.8}", li4);
    }

    #[test]
    fn test_polylog_fd_sign() {
        // Li_4(−1) = −7π⁴/720
        let li4 = polylog(4.0, -1.0);
        assert!(li4 < 0.0, "Li_4(-1) must be < 0: {:.8}", li4);
        let expected = -7.0 * PI.powi(4) / 720.0;
        assert!((li4 - expected).abs() < 1e-4, "Li_4(-1) = {:.8} vs {:.8}", li4, expected);
    }

    // ═══ Spectral integral tests ═══

    #[test]
    fn test_i3_be_at_zero() {
        // I₃^{(+1)}(0) = Γ(4) Li_4(1) = 6 × π⁴/90 = π⁴/15
        let i3 = spectral_integral(3, BoseEinstein, 0.0);
        let expected = PI.powi(4) / 15.0;
        assert!((i3 - expected).abs() / expected < 1e-6,
            "I₃^BE(0) = {:.10}, π⁴/15 = {:.10}", i3, expected);
    }

    #[test]
    fn test_i3_fd_at_zero() {
        // I₃^{(−1)}(0) = −Γ(4) Li_4(−1) = −6 × (−7π⁴/720) = 7π⁴/120
        let i3 = spectral_integral(3, FermiDirac, 0.0);
        let expected = 7.0 * PI.powi(4) / 120.0;
        assert!((i3 - expected).abs() / expected < 1e-3,
            "I₃^FD(0) = {:.10}, 7π⁴/120 = {:.10}", i3, expected);
    }

    #[test]
    fn test_positivity_be() {
        for eta in [-5.0, -2.0, -1.0, -0.5, -0.1] {
            let i3 = spectral_integral(3, BoseEinstein, eta);
            assert!(i3 > 0.0, "I₃^BE({}) = {:.4e} must be > 0", eta, i3);
        }
    }

    #[test]
    fn test_positivity_fd() {
        for eta in [-10.0, -5.0, 0.0, 2.0, 5.0, 10.0] {
            let i3 = spectral_integral(3, FermiDirac, eta);
            assert!(i3 > 0.0, "I₃^FD({}) = {:.4e} must be > 0", eta, i3);
        }
    }

    #[test]
    fn test_positivity_mb() {
        for eta in [-10.0, 0.0, 5.0] {
            let i3 = spectral_integral(3, MaxwellBoltzmann, eta);
            assert!(i3 > 0.0, "I₃^MB({}) = {:.4e} must be > 0", eta, i3);
        }
    }

    #[test]
    fn test_mb_exact() {
        // I_n^{MB}(η) = Γ(n+1) e^η = n! e^η
        let eta = 2.0;
        let i3 = spectral_integral(3, MaxwellBoltzmann, eta);
        assert!((i3 - 6.0 * eta.exp()).abs() < 1e-10);
    }

    #[test]
    fn test_derivative_recurrence() {
        // dI_n/dη = I_{n−1}
        let eta = -1.0;
        let di3 = d_spectral_deta(3, BoseEinstein, eta);
        let i2 = spectral_integral(2, BoseEinstein, eta);
        assert!((di3 - i2).abs() / i2.abs().max(1e-30) < 1e-4,
            "dI₃/dη = {:.6e}, I₂ = {:.6e}", di3, i2);
    }

    #[test]
    fn test_second_derivative_recurrence() {
        let eta = -1.0;
        let d2i3 = d2_spectral_deta2(3, FermiDirac, eta);
        let i1 = spectral_integral(1, FermiDirac, eta);
        assert!((d2i3 - i1).abs() / i1.abs().max(1e-30) < 1e-4);
    }

    #[test]
    fn test_spectral_factor() {
        let theta = 1.5;
        let eta = -0.5;
        let f3 = spectral_factor(3, theta, eta, BoseEinstein);
        let i3 = spectral_integral(3, BoseEinstein, eta);
        assert!((f3 - theta.powi(4) * i3).abs() < 1e-10);
    }

    // ═══ Helper tests ═══

    #[test]
    fn test_gamma_integers() {
        assert!((gamma(1.0) - 1.0).abs() < 1e-10);
        assert!((gamma(2.0) - 1.0).abs() < 1e-10);
        assert!((gamma(3.0) - 2.0).abs() < 1e-10);
        assert!((gamma(4.0) - 6.0).abs() < 1e-10);
        assert!((gamma(5.0) - 24.0).abs() < 1e-10);
    }

    #[test]
    fn test_zeta_values() {
        assert!((riemann_zeta(2.0) - PI * PI / 6.0).abs() < 1e-10);
        assert!((riemann_zeta(4.0) - PI.powi(4) / 90.0).abs() < 1e-10);
    }

    #[test]
    fn test_fd_sign_compensation() {
        // Li_k(-z) < 0 for z > 0 (small z where series converges), 
        // but I_n^FD = -Γ Li(-z) > 0
        let li4_neg = polylog(4.0, -0.5);
        assert!(li4_neg < 0.0, "Li_4(-0.5) must be < 0: {:.8}", li4_neg);
        let i3_fd = spectral_integral(3, FermiDirac, -0.5);
        assert!(i3_fd > 0.0, "I₃^FD(-0.5) must be > 0: {:.4e}", i3_fd);
    }
}
