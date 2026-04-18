//! Optimized spherical Bessel j_ℓ(x) kernel for LoS integration.
//!
//! Three-regime hybrid: small-x series / upward recurrence / Miller downward.
//! Single-value API + array API (one backward pass for entire 0..=ℓ_max ladder).

use std::sync::atomic::{AtomicU64, Ordering};

/// Branch-level profiling counters (only incremented when BASS_BESSEL_PROF=1 at runtime).
/// Zero overhead when disabled (single atomic load + branch).
pub static BESSEL_ARRAY_CALLS: AtomicU64 = AtomicU64::new(0);
pub static BESSEL_UPWARD_CALLS: AtomicU64 = AtomicU64::new(0);
pub static BESSEL_MILLER_CALLS: AtomicU64 = AtomicU64::new(0);
pub static BESSEL_SMALLX_CALLS: AtomicU64 = AtomicU64::new(0);
pub static BESSEL_ZERO_CALLS: AtomicU64 = AtomicU64::new(0);
/// Total Miller iterations (≈ Σ l_start, dominates Miller cost)
pub static BESSEL_MILLER_ITERS: AtomicU64 = AtomicU64::new(0);
/// Total Miller rescale events (should be rare — counts cost anomaly)
pub static BESSEL_MILLER_RESCALES: AtomicU64 = AtomicU64::new(0);
/// Total upward recurrence iterations (≈ Σ lmax)
pub static BESSEL_UPWARD_ITERS: AtomicU64 = AtomicU64::new(0);

/// Check the BASS_BESSEL_PROF env var once at startup (cached in static bool)
#[inline]
fn bessel_prof_enabled() -> bool {
    use std::sync::OnceLock;
    static CACHE: OnceLock<bool> = OnceLock::new();
    *CACHE.get_or_init(|| {
        std::env::var("BASS_BESSEL_PROF").map_or(false, |v| v == "1")
    })
}

/// Reset all counters to zero.
pub fn bessel_prof_reset() {
    BESSEL_ARRAY_CALLS.store(0, Ordering::Relaxed);
    BESSEL_UPWARD_CALLS.store(0, Ordering::Relaxed);
    BESSEL_MILLER_CALLS.store(0, Ordering::Relaxed);
    BESSEL_SMALLX_CALLS.store(0, Ordering::Relaxed);
    BESSEL_ZERO_CALLS.store(0, Ordering::Relaxed);
    BESSEL_MILLER_ITERS.store(0, Ordering::Relaxed);
    BESSEL_MILLER_RESCALES.store(0, Ordering::Relaxed);
    BESSEL_UPWARD_ITERS.store(0, Ordering::Relaxed);
}

/// Snapshot current counters as (calls, upward, miller, smallx, zero, miller_iters, rescales, upward_iters)
pub fn bessel_prof_snapshot() -> (u64, u64, u64, u64, u64, u64, u64, u64) {
    (
        BESSEL_ARRAY_CALLS.load(Ordering::Relaxed),
        BESSEL_UPWARD_CALLS.load(Ordering::Relaxed),
        BESSEL_MILLER_CALLS.load(Ordering::Relaxed),
        BESSEL_SMALLX_CALLS.load(Ordering::Relaxed),
        BESSEL_ZERO_CALLS.load(Ordering::Relaxed),
        BESSEL_MILLER_ITERS.load(Ordering::Relaxed),
        BESSEL_MILLER_RESCALES.load(Ordering::Relaxed),
        BESSEL_UPWARD_ITERS.load(Ordering::Relaxed),
    )
}

const SERIES_MAX_ITERS: usize = 80;
const UPWARD_MARGIN: f64 = 8.0;
// PR-PERF-03: tuned from (32, 0.5) based on Miller accuracy sweep
// (see profile_miller_param_sweep). Sweep confirmed:
//   (32, 0.5): max_rel 2.78e-12  (previous)
//   (16, 0.4): max_rel 4.75e-13  ← chosen — BETTER accuracy AND lower cost
//   ( 8, 0.2): max_rel 5.91e-12  (aggressive; marginally fails 1e-10 test,
//                                 wall benefit ~0 vs (16,0.4), not worth)
//   ( 4, 0.1): max_rel 1.58e-5   (broken — do not touch)
//
// For lmax=300 x=100 typical: l_start 332 vs 382 prior = 13% iter savings
// per Miller call. Measured effect on primary 200k: 37.1s → 35.5s (-4.3%).
// Accuracy margin: 4.75e-13 vs production need (1% at high ℓ) — 11 orders
// of magnitude. All existing Bessel tests pass unchanged.
const MILLER_EXTRA_BASE: usize = 16;
const MILLER_EXTRA_SLOPE: f64 = 0.4;

#[inline]
fn is_small_x(l: usize, x: f64) -> bool {
    let r0 = x * x / (2.0 * (2 * l + 3) as f64);
    x < 0.5 || r0 < 0.125
}

#[inline]
fn j0_seed(x: f64) -> f64 {
    if x.abs() < 1e-4 {
        let x2 = x * x;
        1.0 - x2 / 6.0 + x2 * x2 / 120.0 - x2 * x2 * x2 / 5040.0
    } else {
        x.sin() / x
    }
}

#[inline]
fn j1_seed(x: f64) -> f64 {
    if x.abs() < 1e-4 {
        let x2 = x * x;
        x / 3.0 - x * x2 / 30.0 + x * x2 * x2 / 840.0
    } else {
        let (s, c) = x.sin_cos();
        s / (x * x) - c / x
    }
}

fn series_jl(l: usize, x: f64) -> f64 {
    if x == 0.0 { return if l == 0 { 1.0 } else { 0.0 }; }
    let x2 = x * x;
    let mut term = 1.0_f64;
    for m in 0..l { term *= x / (2 * m + 3) as f64; }
    let mut sum = term;
    for k in 0..SERIES_MAX_ITERS {
        let denom = 2.0 * (k + 1) as f64 * (2 * l + 2 * k + 3) as f64;
        term *= -x2 / denom;
        sum += term;
        if term.abs() <= 2.0 * f64::EPSILON * sum.abs().max(1e-300) { break; }
    }
    sum
}

/// Compute j_ℓ(x) — single value, auto-dispatched.
pub(crate) fn spherical_bessel_j(l: usize, x: f64) -> f64 {
    if x.abs() < 1e-15 { return if l == 0 { 1.0 } else { 0.0 }; }
    let ax = x.abs();
    if is_small_x(l, ax) { return series_jl(l, ax); }
    if ax > l as f64 + UPWARD_MARGIN {
        // Upward recurrence
        let mut jm1 = j0_seed(ax);
        if l == 0 { return jm1; }
        let mut j = j1_seed(ax);
        if l == 1 { return j; }
        for n in 1..l {
            let jp1 = ((2 * n + 1) as f64 / ax) * j - jm1;
            jm1 = j; j = jp1;
        }
        return j;
    }
    // Miller downward
    let l_start = l + MILLER_EXTRA_BASE + (MILLER_EXTRA_SLOPE * ax).ceil() as usize;
    let mut fp1 = 0.0_f64;
    let mut f = 1.0_f64;
    let mut raw_l = 0.0_f64;
    let mut raw0 = 0.0_f64;
    let mut raw1 = 0.0_f64;
    for n in (0..=l_start).rev() {
        if n == l { raw_l = f; }
        if n == 1 { raw1 = f; }
        if n == 0 { raw0 = f; break; }
        let fm1 = ((2 * n + 1) as f64 / ax) * f - fp1;
        fp1 = f; f = fm1;
        if n - 1 == l { raw_l = fm1; }
        if n - 1 == 0 { raw0 = fm1; }
        if n - 1 == 1 { raw1 = fm1; }
        // Rescale to prevent overflow/underflow
        if f.abs() > 1e100 {
            f *= 1e-100; fp1 *= 1e-100;
            raw_l *= 1e-100; raw0 *= 1e-100; raw1 *= 1e-100;
        }
    }
    let scale = if raw0.abs() >= raw1.abs() { j0_seed(ax) / raw0 }
                else { j1_seed(ax) / raw1 };
    raw_l * scale
}

/// Fill out[0..=lmax] with j_0(x)..j_lmax(x) in ONE backward pass.
/// This is O(lmax) total — dramatically faster than lmax separate calls.
pub(crate) fn spherical_bessel_j_array(lmax: usize, x: f64, out: &mut [f64]) {
    spherical_bessel_j_array_tuned(lmax, x, out, MILLER_EXTRA_BASE, MILLER_EXTRA_SLOPE);
}

/// Parametric variant for Miller-branch tuning experiments.
/// Production path calls spherical_bessel_j_array (fixed constants).
#[inline]
pub(crate) fn spherical_bessel_j_array_tuned(
    lmax: usize, x: f64, out: &mut [f64],
    miller_base: usize, miller_slope: f64,
) {
    debug_assert!(out.len() >= lmax + 1);
    // Profile-enabled instrumentation (zero-overhead when BASS_BESSEL_PROF!=1)
    let prof = bessel_prof_enabled();
    if prof { BESSEL_ARRAY_CALLS.fetch_add(1, Ordering::Relaxed); }

    if x.abs() < 1e-15 {
        if prof { BESSEL_ZERO_CALLS.fetch_add(1, Ordering::Relaxed); }
        out[0] = 1.0;
        for v in out[1..=lmax].iter_mut() { *v = 0.0; }
        return;
    }
    let ax = x.abs();

    if is_small_x(lmax, ax) {
        if prof { BESSEL_SMALLX_CALLS.fetch_add(1, Ordering::Relaxed); }
        for l in 0..=lmax { out[l] = series_jl(l, ax); }
        return;
    }

    if ax > lmax as f64 + UPWARD_MARGIN {
        // Upward recurrence for entire ladder
        if prof {
            BESSEL_UPWARD_CALLS.fetch_add(1, Ordering::Relaxed);
            BESSEL_UPWARD_ITERS.fetch_add(lmax as u64, Ordering::Relaxed);
        }
        out[0] = j0_seed(ax);
        if lmax >= 1 { out[1] = j1_seed(ax); }
        for n in 1..lmax {
            out[n + 1] = ((2 * n + 1) as f64 / ax) * out[n] - out[n - 1];
        }
        return;
    }

    // Miller downward for entire ladder — tuned variant
    let l_start = lmax + miller_base + (miller_slope * ax).ceil() as usize;
    if prof {
        BESSEL_MILLER_CALLS.fetch_add(1, Ordering::Relaxed);
        BESSEL_MILLER_ITERS.fetch_add(l_start as u64, Ordering::Relaxed);
    }
    for v in out[0..=lmax].iter_mut() { *v = 0.0; }
    let mut fp1 = 0.0_f64;
    let mut f = 1.0_f64;
    if l_start <= lmax { out[l_start] = f; }

    for n in (1..=l_start).rev() {
        if n <= lmax { out[n] = f; }
        let fm1 = ((2 * n + 1) as f64 / ax) * f - fp1;
        if n - 1 <= lmax { out[n - 1] = fm1; }
        fp1 = f; f = fm1;
        // Rescale
        if f.abs() > 1e100 {
            if prof { BESSEL_MILLER_RESCALES.fetch_add(1, Ordering::Relaxed); }
            f *= 1e-100; fp1 *= 1e-100;
            let lo = n.saturating_sub(1).min(lmax);
            for v in &mut out[lo..=lmax] { *v *= 1e-100; }
        } else if f.abs() != 0.0 && f.abs() < 1e-100 {
            if prof { BESSEL_MILLER_RESCALES.fetch_add(1, Ordering::Relaxed); }
            f *= 1e100; fp1 *= 1e100;
            let lo = n.saturating_sub(1).min(lmax);
            for v in &mut out[lo..=lmax] { *v *= 1e100; }
        }
    }
    let scale = if out[0].abs() >= out.get(1).copied().unwrap_or(0.0).abs() {
        j0_seed(ax) / out[0]
    } else {
        j1_seed(ax) / out[1]
    };
    for v in out[0..=lmax].iter_mut() { *v *= scale; }
}




/// Fill out_j[0..=lmax] = j_ℓ(x) and out_jp[0..=lmax] = j'_ℓ(x).
/// Uses the stable ladder from spherical_bessel_j_array and the recursion
///   j'_ℓ(x) = j_{ℓ-1}(x) - (ℓ+1) j_ℓ(x)/x
/// with j'_0(x) = -j_1(x).
pub(crate) fn spherical_bessel_j_and_jprime_array(
    lmax: usize,
    x: f64,
    out_j: &mut [f64],
    out_jp: &mut [f64],
) {
    debug_assert!(out_j.len() >= lmax + 1);
    debug_assert!(out_jp.len() >= lmax + 1);
    spherical_bessel_j_array(lmax, x, out_j);
    if x.abs() < 1e-15 {
        out_jp[0] = 0.0;
        for l in 1..=lmax { out_jp[l] = 0.0; }
        return;
    }
    if lmax == 0 {
        out_jp[0] = if out_j.len() > 1 { -out_j[1] } else { -spherical_bessel_j(1, x) };
        return;
    }
    out_jp[0] = -out_j[1];
    for l in 1..=lmax {
        out_jp[l] = out_j[l - 1] - ((l + 1) as f64 / x) * out_j[l];
    }
}
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
    fn test_basic_values() {
        let j0 = spherical_bessel_j(0, 1.0);
        assert!((j0 - 1.0_f64.sin()).abs() < 1e-14);
        assert_eq!(spherical_bessel_j(5, 0.0), 0.0);
        assert_eq!(spherical_bessel_j(0, 0.0), 1.0);
    }

    #[test]
    fn test_derivative_array_matches_identity() {
        let x = 3.5_f64;
        let lmax = 20;
        let mut j = vec![0.0; lmax + 1];
        let mut jp = vec![0.0; lmax + 1];
        spherical_bessel_j_and_jprime_array(lmax, x, &mut j, &mut jp);
        assert!((jp[0] + j[1]).abs() < 1e-12);
        for l in 1..=lmax {
            let rhs = j[l - 1] - ((l + 1) as f64 / x) * j[l];
            assert!((jp[l] - rhs).abs() < 1e-12,
                "derivative identity failed at l={l}: {} vs {}", jp[l], rhs);
        }
    }

    #[test]
    fn test_array_matches_single() {
        for &x in &[0.3_f64, 1.5, 5.0, 15.0, 50.0, 200.0] {
            let lmax = 60;
            let mut arr = vec![0.0; lmax + 1];
            spherical_bessel_j_array(lmax, x, &mut arr);
            for l in 0..=lmax {
                let single = spherical_bessel_j(l, x);
                let diff = (arr[l] - single).abs();
                let tol = 1e-10 * arr[l].abs().max(single.abs()).max(1e-300);
                assert!(diff <= tol, "mismatch l={l} x={x}: arr={} single={}", arr[l], single);
            }
        }
    }

    /// PR-PERF-03: Miller branch parameter sweep.
    /// For each (lmax, x) in a production-realistic grid, compute error of
    /// tuned parameters vs high-precision reference (base=256, slope=4.0)
    /// restricted to values above a "significance floor" (values near zero
    /// are dominated by fp noise, irrelevant for D_ℓ integration).
    ///
    /// Output: decision table showing max rel error per (base, slope).
    #[test]
    #[ignore]
    fn profile_miller_param_sweep() {
        // Production lmax range: ell_max up to 300 at primary size
        let lmax_set = [50usize, 100, 200, 300];
        // x range: recombination regime gives x = k·(eta_0-eta_rec) ~ 0-5000
        // but Miller is only called when x <= lmax+8, so x grid here bounded
        let x_frac_set = [0.05_f64, 0.1, 0.2, 0.5, 0.8, 0.95];  // x = frac * lmax

        // Parameter grid to sweep
        let param_set: Vec<(usize, f64)> = vec![
            (32, 0.5),  // CURRENT
            (24, 0.4),
            (16, 0.3),
            (12, 0.25),
            (8,  0.2),
            (4,  0.1),
            (16, 0.5),
            (16, 0.4),
        ];

        eprintln!("[MILLER-SWEEP] reference: base=256 slope=4.0");
        eprintln!("[MILLER-SWEEP] significance floor: |j_l| >= 1e-15 (below, fp noise)");
        eprintln!("[MILLER-SWEEP] {:>5} {:>5} {:>10} {:>10} {:>12}",
                  "base", "slope", "max_rel", "p99_rel", "max_ell_affected");

        for &(base, slope) in &param_set {
            let mut max_rel = 0.0_f64;
            let mut all_rels = Vec::new();
            let mut max_ell = 0usize;

            for &lmax in &lmax_set {
                for &frac in &x_frac_set {
                    let x = frac * lmax as f64;
                    if x < 0.5 { continue; } // small-x series, not Miller

                    let mut ref_out = vec![0.0_f64; lmax + 1];
                    spherical_bessel_j_array_tuned(lmax, x, &mut ref_out, 256, 4.0);
                    let mut test_out = vec![0.0_f64; lmax + 1];
                    spherical_bessel_j_array_tuned(lmax, x, &mut test_out, base, slope);

                    for l in 0..=lmax {
                        let r = ref_out[l].abs();
                        if r < 1e-15 { continue; } // fp noise floor
                        let rel = (test_out[l] - ref_out[l]).abs() / r;
                        all_rels.push(rel);
                        if rel > max_rel {
                            max_rel = rel;
                            max_ell = l;
                        }
                    }
                }
            }
            // p99
            all_rels.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let p99 = all_rels.get(all_rels.len() * 99 / 100).copied().unwrap_or(0.0);

            let marker = if (base, slope) == (32, 0.5) { " ← CURRENT" } else { "" };
            eprintln!("[MILLER-SWEEP] {:>5} {:>5.2} {:>10.2e} {:>10.2e} {:>12}{}",
                      base, slope, max_rel, p99, max_ell, marker);
        }
    }
}
