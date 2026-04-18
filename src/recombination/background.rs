// BackgroundProvider trait and BI-flat implementation.
// BA-02: Abstraction layer for all future Bianchi type backgrounds.

use crate::core::math::{natural_cubic_second_derivatives, cubic_spline_eval};

/// Cached natural cubic spline over a 1D grid.
/// Stores x, y, y'' for O(log n) point evaluation.
#[derive(Clone)]
pub(crate) struct CubicSplineCache {
    x: Vec<f64>,
    y: Vec<f64>,
    y2: Vec<f64>,
}

impl CubicSplineCache {
    /// Build cache from (x, y) data. x must be strictly increasing.
    pub(crate) fn new(x: Vec<f64>, y: Vec<f64>) -> Result<Self, String> {
        let y2 = natural_cubic_second_derivatives(&x, &y)?;
        Ok(Self { x, y, y2 })
    }

    /// Evaluate the spline at a single point.
    #[inline]
    pub(crate) fn eval(&self, xp: f64) -> f64 {
        cubic_spline_eval(&self.x, &self.y, &self.y2, xp)
    }

    /// Number of grid points.
    pub(crate) fn len(&self) -> usize {
        self.x.len()
    }
}

/// Trait for background quantities evaluated at conformal time η.
///
/// Every Bianchi type must provide these five functions. The hierarchy
/// solver and LoS integrator consume BackgroundProvider without knowing
/// the underlying geometry.
pub(crate) trait BackgroundProvider {
    /// Hubble parameter H(η) in SI units [s⁻¹].
    fn hubble(&self, eta: f64) -> f64;

    /// Shear-to-Hubble ratio σ/H at conformal time η.
    /// Returns 0.0 for FLRW.
    fn sigma_h(&self, eta: f64) -> f64;

    /// Free-electron fraction x_e(η) (total, including reionisation).
    fn x_e(&self, eta: f64) -> f64;

    /// Normalised visibility function g(η), with ∫g dη = 1.
    fn visibility(&self, eta: f64) -> f64;

    /// Thomson scattering rate dτ/dη(η) [Mpc⁻¹].
    fn tau_dot(&self, eta: f64) -> f64;
}

/// BI-flat (Bianchi I, k = 0) background with CubicSpline caches.
///
/// Constructed from pre-computed grids over η. The shear profile
/// σ/H is externally supplied (from the initial Σ₀ parameter),
/// not self-consistently evolved — appropriate for the perturbative
/// BI regime where σ/H ≪ 1 throughout.
///
/// Cache grid size: n_grid = 10000 (inherited from Phase 1.0).
pub(crate) struct FlatBIBackground {
    h_cache: CubicSplineCache,
    sigma_h_cache: CubicSplineCache,
    x_e_cache: CubicSplineCache,
    g_cache: CubicSplineCache,
    tau_dot_cache: CubicSplineCache,
}

impl FlatBIBackground {
    /// Build from pre-computed η-ordered grids.
    ///
    /// All input vectors must have identical length and share the same
    /// strictly-increasing η grid.
    pub(crate) fn new(
        eta_grid: Vec<f64>,
        h_grid: Vec<f64>,
        sigma_h_grid: Vec<f64>,
        x_e_grid: Vec<f64>,
        g_grid: Vec<f64>,
        tau_dot_grid: Vec<f64>,
    ) -> Result<Self, String> {
        let n = eta_grid.len();
        if h_grid.len() != n || sigma_h_grid.len() != n
            || x_e_grid.len() != n || g_grid.len() != n || tau_dot_grid.len() != n
        {
            return Err("All background grids must have the same length as eta_grid".into());
        }
        Ok(Self {
            h_cache: CubicSplineCache::new(eta_grid.clone(), h_grid)?,
            sigma_h_cache: CubicSplineCache::new(eta_grid.clone(), sigma_h_grid)?,
            x_e_cache: CubicSplineCache::new(eta_grid.clone(), x_e_grid)?,
            g_cache: CubicSplineCache::new(eta_grid.clone(), g_grid)?,
            tau_dot_cache: CubicSplineCache::new(eta_grid, tau_dot_grid)?,
        })
    }

    /// Number of grid points in the cache.
    pub(crate) fn n_grid(&self) -> usize {
        self.h_cache.len()
    }
}

impl BackgroundProvider for FlatBIBackground {
    #[inline]
    fn hubble(&self, eta: f64) -> f64 {
        self.h_cache.eval(eta)
    }

    #[inline]
    fn sigma_h(&self, eta: f64) -> f64 {
        self.sigma_h_cache.eval(eta)
    }

    #[inline]
    fn x_e(&self, eta: f64) -> f64 {
        self.x_e_cache.eval(eta)
    }

    #[inline]
    fn visibility(&self, eta: f64) -> f64 {
        self.g_cache.eval(eta)
    }

    #[inline]
    fn tau_dot(&self, eta: f64) -> f64 {
        self.tau_dot_cache.eval(eta)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cubic_spline_cache_linear() {
        // Linear data: spline must reproduce exactly.
        let x: Vec<f64> = (0..100).map(|i| i as f64 * 0.01).collect();
        let y: Vec<f64> = x.iter().map(|&xi| 3.0 * xi + 1.0).collect();
        let cache = CubicSplineCache::new(x, y).unwrap();
        assert!((cache.eval(0.0) - 1.0).abs() < 1e-12);
        assert!((cache.eval(0.5) - 2.5).abs() < 1e-12);
        assert!((cache.eval(0.99) - 3.97).abs() < 1e-10);
    }

    #[test]
    fn test_flat_bi_background_construction() {
        let n = 100;
        let eta: Vec<f64> = (0..n).map(|i| 1.0 + i as f64).collect();
        let h: Vec<f64> = eta.iter().map(|&e| 1.0 / e).collect();
        let sigma_h = vec![0.0; n];  // FLRW limit
        let x_e = vec![1.0; n];
        let g: Vec<f64> = eta.iter().map(|&e| if (e - 50.0).abs() < 5.0 { 1.0 } else { 0.0 }).collect();
        let tau_dot = vec![0.1; n];
        let bg = FlatBIBackground::new(eta, h, sigma_h, x_e, g, tau_dot).unwrap();
        assert_eq!(bg.n_grid(), 100);
        // σ/H = 0 in FLRW limit
        assert!(bg.sigma_h(50.0).abs() < 1e-10);
    }

    #[test]
    fn test_background_provider_trait_object() {
        // Verify the trait is object-safe (can be used as dyn BackgroundProvider).
        let n = 50;
        let eta: Vec<f64> = (0..n).map(|i| i as f64 + 1.0).collect();
        let ones = vec![1.0; n];
        let zeros = vec![0.0; n];
        let bg = FlatBIBackground::new(
            eta, ones.clone(), zeros.clone(), ones.clone(), zeros.clone(), ones,
        ).unwrap();
        let provider: &dyn BackgroundProvider = &bg;
        assert!((provider.hubble(25.0) - 1.0).abs() < 1e-10);
    }
}
