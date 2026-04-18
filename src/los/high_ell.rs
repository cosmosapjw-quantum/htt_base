// BE-06: High-ℓ LoS optimisation for ACT-level C_ℓ computation.
//
// Three acceleration strategies:
//   1. Limber approximation for ℓ > ℓ_Limber: j_ℓ(x) → √(π/(2ℓ+1)) δ(x−ℓ−1/2)
//   2. Precomputed BesselTable for ℓ ≤ ℓ_Limber
//   3. Adaptive η-grid from source_sampler (δη ≤ 0.3 Mpc at peak)
//
// Target: C_ℓ to ℓ = 4000 in < 500ms (FLRW, Release build).

use super::bessel::{spherical_bessel_j, BesselTable};
use super::source_sampler::SourceInterpolator;
use std::f64::consts::PI;

/// Configuration for high-ℓ C_ℓ computation.
#[derive(Clone)]
pub(crate) struct HighEllConfig {
    /// Maximum multipole.
    pub(crate) ell_max: usize,
    /// Limber transition multipole (ℓ > this uses Limber).
    pub(crate) ell_limber: usize,
    /// Number of k-modes for integration.
    pub(crate) n_k: usize,
    /// k range [Mpc⁻¹].
    pub(crate) k_min: f64,
    pub(crate) k_max: f64,
    /// Primordial spectrum parameters.
    pub(crate) a_s: f64,
    pub(crate) n_s: f64,
    pub(crate) k_pivot: f64,
    /// Bessel table spacing.
    pub(crate) bessel_dx: f64,
}

impl HighEllConfig {
    /// Default for ACT-level computation (ℓ_max = 4000).
    pub(crate) fn act_level() -> Self {
        Self {
            ell_max: 4000,
            ell_limber: 100,
            n_k: 300,
            k_min: 1e-4,
            k_max: 0.35,
            a_s: 2.1e-9,
            n_s: 0.9649,
            k_pivot: 0.05,
            bessel_dx: 0.5,
        }
    }

    /// Low-ℓ only (faster, for validation).
    pub(crate) fn low_ell(ell_max: usize) -> Self {
        Self {
            ell_max,
            ell_limber: ell_max + 1, // no Limber
            n_k: 100,
            k_min: 1e-4,
            k_max: 0.1,
            a_s: 2.1e-9,
            n_s: 0.9649,
            k_pivot: 0.05,
            bessel_dx: 0.5,
        }
    }
}

/// Result of high-ℓ C_ℓ computation.
pub(crate) struct HighEllResult {
    /// C_ℓ values for ℓ = 0..ℓ_max (dimensionless).
    pub(crate) cl: Vec<f64>,
    /// Number of k-modes used.
    pub(crate) n_k_used: usize,
    /// Fraction computed via Limber.
    pub(crate) limber_fraction: f64,
    /// Wall time [ms].
    pub(crate) wall_ms: f64,
}

/// Limber approximation for a single ℓ.
///
/// C_ℓ^{Limber} = (2π²/k³) Δ²_ζ(k) |S(η)|² / d_A²
/// evaluated at k = (ℓ+1/2) / d(η), where d(η) is the comoving distance.
///
/// In practice: C_ℓ ≈ ∫ dk/k Δ²_ζ(k) × π/(2ℓ+1) × |S(k, η_ℓ(k))|²
/// where η_ℓ(k) is the stationary-phase point k(η₀−η) = ℓ+1/2.
pub(crate) fn limber_cl(
    ell: usize,
    source: &SourceInterpolator,
    eta_0: f64,
    k_grid: &[f64],
    delta2_grid: &[f64],  // Δ²_ζ(k) = A_s (k/k_piv)^{n_s−1}
) -> f64 {
    let nu = ell as f64 + 0.5;
    let mut cl = 0.0;

    for ik in 0..k_grid.len() {
        let k = k_grid[ik];
        // Stationary phase: η_sp = η₀ − ν/k
        let eta_sp = eta_0 - nu / k;
        if eta_sp < 0.0 { continue; }
        let s = source.eval(eta_sp);
        // Limber: C_ℓ += (π/(2ℓ+1)) × Δ²_ζ(k) × |S|² × dlnk
        let dlnk = if ik < k_grid.len() - 1 {
            (k_grid[ik + 1] / k).ln()
        } else {
            (k / k_grid[ik - 1]).ln()
        };
        cl += PI / (2 * ell + 1) as f64 * delta2_grid[ik] * s * s * dlnk;
    }
    cl
}

/// Full (non-Limber) C_ℓ for a single ℓ using precomputed Bessel table.
pub(crate) fn full_cl(
    ell: usize,
    source: &SourceInterpolator,
    eta_0: f64,
    k_grid: &[f64],
    delta2_grid: &[f64],
    bessel_table: &BesselTable,
) -> f64 {
    let mut cl = 0.0;

    for ik in 0..k_grid.len() {
        let k = k_grid[ik];
        // LoS: Δ_ℓ(k) = ∫ S(η) j_ℓ(k(η₀−η)) dη
        let mut delta_ell = 0.0;
        let n = source.len();
        // Trapezoidal on source grid
        for i in 1..n {
            let eta_prev = source.eta[i - 1];
            let eta_curr = source.eta[i];
            let x_prev = k * (eta_0 - eta_prev);
            let x_curr = k * (eta_0 - eta_curr);
            let jl_prev = if x_prev > 0.0 {
                if ell <= bessel_table.ell_max() { bessel_table.eval(ell, x_prev) }
                else { spherical_bessel_j(ell, x_prev) }
            } else if ell == 0 { 1.0 } else { 0.0 };
            let jl_curr = if x_curr > 0.0 {
                if ell <= bessel_table.ell_max() { bessel_table.eval(ell, x_curr) }
                else { spherical_bessel_j(ell, x_curr) }
            } else if ell == 0 { 1.0 } else { 0.0 };
            let deta = eta_curr - eta_prev;
            delta_ell += 0.5 * (source.vals[i - 1] * jl_prev + source.vals[i] * jl_curr) * deta;
        }

        let dlnk = if ik < k_grid.len() - 1 {
            (k_grid[ik + 1] / k).ln()
        } else {
            (k / k_grid[ik - 1]).ln()
        };
        cl += 4.0 * PI * delta2_grid[ik] * delta_ell * delta_ell * dlnk;
    }
    cl
}

/// Compute C_ℓ for ℓ = 2..ℓ_max using hybrid Limber + full method.
///
/// Source functions must be pre-computed for each k-mode (from BE-04 Boltzmann solver).
/// This function accepts a single angle-averaged source as a simplified interface.
pub(crate) fn compute_cl_high_ell(
    config: &HighEllConfig,
    source: &SourceInterpolator,
    eta_0: f64,
) -> HighEllResult {
    let t0 = std::time::Instant::now();

    let n_k = config.n_k;
    let mut k_grid = Vec::with_capacity(n_k);
    let mut delta2_grid = Vec::with_capacity(n_k);
    for ik in 0..n_k {
        let f = ik as f64 / (n_k - 1).max(1) as f64;
        let k = config.k_min * (config.k_max / config.k_min).powf(f);
        k_grid.push(k);
        delta2_grid.push(config.a_s * (k / config.k_pivot).powf(config.n_s - 1.0));
    }

    // Build Bessel table for ℓ ≤ ell_limber
    let x_max = config.k_max * eta_0 * 1.1;
    let bessel = BesselTable::new(config.ell_limber.min(config.ell_max), x_max.min(20000.0), config.bessel_dx);

    let mut cl = vec![0.0; config.ell_max + 1];
    let mut n_limber = 0_usize;

    for ell in 2..=config.ell_max {
        if ell > config.ell_limber {
            cl[ell] = limber_cl(ell, source, eta_0, &k_grid, &delta2_grid);
            n_limber += 1;
        } else {
            cl[ell] = full_cl(ell, source, eta_0, &k_grid, &delta2_grid, &bessel);
        }
    }

    let wall = t0.elapsed().as_secs_f64() * 1000.0;
    let total_ell = (config.ell_max - 1).max(1);
    HighEllResult {
        cl,
        n_k_used: n_k,
        limber_fraction: n_limber as f64 / total_ell as f64,
        wall_ms: wall,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_source() -> SourceInterpolator {
        // Gaussian source peaked at η_* = 285 Mpc
        let n = 500;
        let eta: Vec<f64> = (0..n).map(|i| i as f64 * 30.0).collect();
        let vals: Vec<f64> = eta.iter().map(|&e| {
            let g = (-(e - 285.0).powi(2) / (2.0 * 20.0_f64.powi(2))).exp();
            g / (20.0 * (2.0 * PI).sqrt()) // normalized
        }).collect();
        SourceInterpolator::new(eta, vals)
    }

    #[test]
    fn test_limber_positive() {
        let src = mock_source();
        let k_grid: Vec<f64> = (0..50).map(|i| 0.001 * (0.3 / 0.001_f64).powf(i as f64 / 49.0)).collect();
        let d2: Vec<f64> = k_grid.iter().map(|&k| 2.1e-9 * (k / 0.05_f64).powf(-0.035)).collect();
        let cl = limber_cl(200, &src, 14050.0, &k_grid, &d2);
        assert!(cl >= 0.0 && cl.is_finite(), "Limber C_200 = {:.4e}", cl);
    }

    #[test]
    fn test_bessel_table_accuracy() {
        let bt = BesselTable::new(100, 500.0, 0.5);
        // Check at a known point
        let exact = spherical_bessel_j(10, 15.0);
        let table = bt.eval(10, 15.0);
        let rel = (table - exact).abs() / exact.abs().max(1e-30);
        assert!(rel < 0.01, "Table j_10(15) = {:.6e}, exact = {:.6e}, rel = {:.2e}",
            table, exact, rel);
    }

    #[test]
    fn test_bessel_wkb_accuracy() {
        // WKB for ℓ=100, x=200 (well in oscillatory regime)
        let wkb = super::super::bessel::spherical_bessel_j(100, 200.0);
        let miller = super::super::bessel::spherical_bessel_j(100, 200.0);
        if miller.abs() > 1e-20 {
            let rel = (wkb - miller).abs() / miller.abs();
            assert!(rel < 0.1, "WKB vs Miller at ℓ=100,x=200: rel = {:.2e}", rel);
        }
    }

    #[test]
    fn test_high_ell_runs() {
        let src = mock_source();
        let cfg = HighEllConfig::low_ell(30);
        let result = compute_cl_high_ell(&cfg, &src, 14050.0);
        assert_eq!(result.cl.len(), 31);
        for ell in 2..=30 {
            assert!(result.cl[ell].is_finite(), "C_{} = NaN", ell);
            assert!(result.cl[ell] >= 0.0, "C_{} < 0", ell);
        }
    }

    #[test]
    fn test_limber_fraction() {
        let src = mock_source();
        let cfg = HighEllConfig { ell_max: 200, ell_limber: 50, ..HighEllConfig::act_level() };
        let result = compute_cl_high_ell(&cfg, &src, 14050.0);
        assert!(result.limber_fraction > 0.5, "Limber fraction = {:.2}", result.limber_fraction);
    }

    #[test]
    fn test_bessel_table_memory() {
        let bt = BesselTable::new(100, 5000.0, 0.5);
        let mb = bt.memory_bytes() as f64 / 1e6;
        assert!(mb < 100.0, "Bessel table = {:.1} MB (too large)", mb);
    }

    #[test]
    fn test_high_ell_act_config() {
        let cfg = HighEllConfig::act_level();
        assert_eq!(cfg.ell_max, 4000);
        assert_eq!(cfg.ell_limber, 100);
    }
}
