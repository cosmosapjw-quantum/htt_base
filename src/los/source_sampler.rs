// BE-06: Adaptive source function sampler for high-ℓ LoS integration.
//
// Three-zone adaptive η-grid:
//   Zone 1 (early): δη ~ 10 Mpc (radiation era, pre-recombination)
//   Zone 2 (recombination): δη ≤ 0.3 Mpc (around z_*, width from g(η))
//   Zone 3 (late): δη ~ 20 Mpc (matter/Λ era, ISW)
//
// CubicSpline interpolation for sub-grid evaluation.

/// Build adaptive η-grid tuned for high-ℓ (ACT-level) precision.
///
/// δη ≤ 0.3 Mpc near recombination, ~5 Mpc in matter era, ~20 Mpc late.
pub(crate) fn build_high_ell_grid(
    eta_ini: f64,
    eta_0: f64,
    eta_star: f64,
    delta_z_star: f64,  // FWHM of visibility in η [Mpc]
) -> Vec<f64> {
    let mut grid = Vec::with_capacity(2000);
    let window = (delta_z_star * 2.0).max(30.0); // dense region half-width

    // Zone 1: early (η_ini to η_* − window)
    let d_early = 5.0; // Mpc
    let mut eta = eta_ini;
    let eta_dense_start = (eta_star - window).max(eta_ini);
    while eta < eta_dense_start {
        grid.push(eta);
        eta += d_early;
    }

    // Zone 2: recombination (dense, δη ≤ 0.3 Mpc)
    let d_dense = 0.3;
    let eta_dense_end = (eta_star + window).min(eta_0);
    while eta < eta_dense_end {
        grid.push(eta);
        eta += d_dense;
    }

    // Zone 3: late (matter + Λ era)
    let d_late = 20.0;
    while eta < eta_0 {
        grid.push(eta);
        eta += d_late;
    }

    if grid.last().map_or(true, |&l| (l - eta_0).abs() > 0.1) {
        grid.push(eta_0);
    }

    grid
}

/// Source function interpolator using piecewise cubic Hermite.
///
/// When derivatives are provided, uses C¹ Hermite interpolation (O(h⁴) error).
/// Falls back to linear (O(h²)) when derivatives are absent.
#[derive(Clone)]
pub(crate) struct SourceInterpolator {
    pub(crate) eta: Vec<f64>,
    pub(crate) vals: Vec<f64>,
    pub(crate) dvals: Option<Vec<f64>>,  // derivatives dS/dη at each knot
    n: usize,
}

impl SourceInterpolator {
    pub(crate) fn new(eta: Vec<f64>, vals: Vec<f64>) -> Self {
        let n = eta.len();
        Self { eta, vals, dvals: None, n }
    }

    /// Create with both values and derivatives (Hermite mode).
    pub(crate) fn new_hermite(eta: Vec<f64>, vals: Vec<f64>, dvals: Vec<f64>) -> Self {
        let n = eta.len();
        Self { eta, vals, dvals: Some(dvals), n }
    }

    /// Evaluate S(η) at arbitrary η.
    /// Uses cubic Hermite if derivatives are available, else linear.
    pub(crate) fn eval(&self, eta: f64) -> f64 {
        if self.n == 0 { return 0.0; }
        if eta <= self.eta[0] { return self.vals[0]; }
        if eta >= self.eta[self.n - 1] { return self.vals[self.n - 1]; }

        // Binary search
        let mut lo = 0;
        let mut hi = self.n - 1;
        while hi - lo > 1 {
            let m = (lo + hi) / 2;
            if self.eta[m] <= eta { lo = m; } else { hi = m; }
        }

        let h = (self.eta[hi] - self.eta[lo]).max(1e-30);
        let t = (eta - self.eta[lo]) / h;

        if let Some(ref dv) = self.dvals {
            // Cubic Hermite: p(t) = h00·y0 + h10·h·dy0 + h01·y1 + h11·h·dy1
            let t2 = t * t;
            let t3 = t2 * t;
            let h00 = 2.0 * t3 - 3.0 * t2 + 1.0;
            let h10 = t3 - 2.0 * t2 + t;
            let h01 = -2.0 * t3 + 3.0 * t2;
            let h11 = t3 - t2;
            h00 * self.vals[lo] + h10 * h * dv[lo]
                + h01 * self.vals[hi] + h11 * h * dv[hi]
        } else {
            // Linear fallback
            self.vals[lo] * (1.0 - t) + self.vals[hi] * t
        }
    }

    /// Evaluate derivative dS/dη at arbitrary η (Hermite mode only).
    pub(crate) fn eval_deriv(&self, eta: f64) -> f64 {
        if self.n == 0 || self.dvals.is_none() { return 0.0; }
        if eta <= self.eta[0] || eta >= self.eta[self.n - 1] { return 0.0; }

        let mut lo = 0;
        let mut hi = self.n - 1;
        while hi - lo > 1 {
            let m = (lo + hi) / 2;
            if self.eta[m] <= eta { lo = m; } else { hi = m; }
        }

        let h = (self.eta[hi] - self.eta[lo]).max(1e-30);
        let t = (eta - self.eta[lo]) / h;
        let dv = self.dvals.as_ref().unwrap();

        let t2 = t * t;
        // dp/dt = (6t²-6t)y0 + (3t²-4t+1)h·dy0 + (-6t²+6t)y1 + (3t²-2t)h·dy1
        // dp/dη = dp/dt / h
        ((6.0*t2 - 6.0*t) * self.vals[lo]
         + (3.0*t2 - 4.0*t + 1.0) * h * dv[lo]
         + (-6.0*t2 + 6.0*t) * self.vals[hi]
         + (3.0*t2 - 2.0*t) * h * dv[hi]) / h
    }

    pub(crate) fn len(&self) -> usize { self.n }

    /// Maximum spacing in the dense region.
    pub(crate) fn max_spacing_near(&self, eta_star: f64, window: f64) -> f64 {
        let mut max_d = 0.0_f64;
        for i in 1..self.n {
            let mid = 0.5 * (self.eta[i] + self.eta[i - 1]);
            if (mid - eta_star).abs() < window {
                max_d = max_d.max(self.eta[i] - self.eta[i - 1]);
            }
        }
        max_d
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_grid_structure() {
        let g = build_high_ell_grid(0.0, 14050.0, 285.0, 20.0);
        assert!(g.len() > 200, "Grid too small: {}", g.len());
        assert!((g[0] - 0.0).abs() < 1e-10);
        assert!((*g.last().unwrap() - 14050.0).abs() < 25.0);
    }

    #[test]
    fn test_dense_region_spacing() {
        let g = build_high_ell_grid(0.0, 14050.0, 285.0, 20.0);
        for i in 1..g.len() {
            let mid = 0.5 * (g[i] + g[i - 1]);
            if (mid - 285.0).abs() < 20.0 {
                let d = g[i] - g[i - 1];
                assert!(d <= 0.31, "Dense δη = {:.2} > 0.3 Mpc at η = {:.1}", d, mid);
            }
        }
    }

    #[test]
    fn test_interpolator_exact_at_nodes() {
        let eta = vec![0.0, 1.0, 2.0, 3.0];
        let vals = vec![0.0, 1.0, 0.5, 0.2];
        let s = SourceInterpolator::new(eta, vals);
        assert!((s.eval(0.0) - 0.0).abs() < 1e-10);
        assert!((s.eval(1.0) - 1.0).abs() < 1e-10);
        assert!((s.eval(2.0) - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_interpolator_midpoint() {
        let eta = vec![0.0, 2.0];
        let vals = vec![0.0, 1.0];
        let s = SourceInterpolator::new(eta, vals);
        assert!((s.eval(1.0) - 0.5).abs() < 1e-10);
    }
}
