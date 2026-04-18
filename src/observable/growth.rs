// BE-08: Matter growth function D(η) on Bianchi background.
//
// Growth ODE: D'' + 2HD' − (3/2)Ω_m H² D = 0  (FLRW)
// Bianchi correction: shear σ enters as additional damping and source:
//   D'' + (2H + σ²/(3H))D' − (3/2)Ω_m H² D = −σ_{ab}∂^a∂^b Ψ/(a²H²)
//
// Direction-dependent modulation:
//   δD/D(ê,η) ≈ ∫₀^η dη' G(η,η') σ_{ab}(η') ê^a ê^b / H(η')
//
// Shear decay: σ/H ∝ a^{−2} in matter era (exact for BI).

use std::f64::consts::PI;

/// Isotropic growth function D(η) and derivatives.
#[derive(Clone)]
pub(crate) struct GrowthFunction {
    /// Conformal time grid [Mpc].
    pub(crate) eta_grid: Vec<f64>,
    /// D(η) normalised to D(η₀) = 1.
    pub(crate) d_vals: Vec<f64>,
    /// D'(η).
    pub(crate) dd_vals: Vec<f64>,
    /// f(η) = d ln D / d ln a (growth rate).
    pub(crate) f_vals: Vec<f64>,
}

impl GrowthFunction {
    /// Solve growth ODE on FLRW background.
    ///
    /// D'' + aH D' − (3/2) Ω_m H₀² / a D = 0
    /// Using conformal time η, with ' = d/dη.
    pub(crate) fn solve_flrw(
        h0: f64,        // H₀ [s⁻¹]
        omega_m: f64,
        omega_l: f64,
        eta_grid: &[f64],
        a_grid: &[f64], // a(η)
    ) -> Self {
        let n = eta_grid.len();
        let mut d = vec![0.0; n];
        let mut dd = vec![0.0; n];
        let mut f = vec![0.0; n];

        // Initial conditions: D ∝ a in matter era
        d[0] = a_grid[0];
        dd[0] = a_grid[0]; // D' ~ a' ~ aH at early times

        // RK4 for D'' = −aH D' + (3/2) Ω_m H₀² a D
        for i in 0..n - 1 {
            let deta = eta_grid[i + 1] - eta_grid[i];
            let a = a_grid[i];
            let h_conf = hubble_conformal(a, h0, omega_m, omega_l);

            let rhs = |d_val: f64, dd_val: f64, a_val: f64| -> f64 {
                let hc = hubble_conformal(a_val, h0, omega_m, omega_l);
                -a_val * hc * dd_val / a_val.max(1e-30) // simplified: −ℋ D'
                    + 1.5 * omega_m * h0 * h0 * a_val * d_val // + (3/2)Ω_m H₀² a D
            };

            // Simple Euler (adequate for growth function smoothness)
            let ddd = rhs(d[i], dd[i], a);
            d[i + 1] = d[i] + dd[i] * deta;
            dd[i + 1] = dd[i] + ddd * deta;

            if d[i + 1].abs() > 1e30 {
                d[i + 1] *= 1e-20; dd[i + 1] *= 1e-20;
            }
        }

        // Normalise: D(η₀) = 1
        let d0 = d[n - 1].abs().max(1e-30);
        for i in 0..n { d[i] /= d0; dd[i] /= d0; }

        // Growth rate: f = a D'/(D a') ≈ D'/(DH)
        for i in 0..n {
            let a = a_grid[i];
            let hc = hubble_conformal(a, h0, omega_m, omega_l);
            f[i] = if d[i].abs() > 1e-30 && hc > 0.0 {
                dd[i] / (d[i] * hc)
            } else { 1.0 };
        }

        Self { eta_grid: eta_grid.to_vec(), d_vals: d, dd_vals: dd, f_vals: f }
    }

    /// Evaluate D(η) by interpolation.
    pub(crate) fn eval(&self, eta: f64) -> f64 {
        lin_interp(&self.eta_grid, &self.d_vals, eta)
    }

    /// Growth modulation from Bianchi shear.
    ///
    /// δD/D(ê,η) ≈ ∫₀^η dη' G(η,η') σ_{ab}(η') ê^a ê^b / H(η')
    ///
    /// Leading order: δD/D ~ (σ/H) × (growth integral factor)
    /// The growth integral factor is O(1) over the lensing kernel range.
    pub(crate) fn modulation(&self, sigma_ab_ee_over_h: f64) -> f64 {
        // Leading-order: δD/D ~ 0.5 × σ_{ab}ê^aê^b/H
        // The factor 0.5 accounts for the time-averaged shear coupling
        // over the growth history (approximate).
        0.5 * sigma_ab_ee_over_h
    }
}

/// Conformal Hubble parameter ℋ = aH [s⁻¹].
fn hubble_conformal(a: f64, h0: f64, omega_m: f64, omega_l: f64) -> f64 {
    let omega_r = 9.14e-5; // radiation (approximate)
    a * h0 * (omega_r / a.powi(4) + omega_m / a.powi(3) + omega_l).max(1e-30).sqrt()
}

fn lin_interp(xg: &[f64], yg: &[f64], x: f64) -> f64 {
    let n = xg.len();
    if n == 0 { return 0.0; }
    if x <= xg[0] { return yg[0]; }
    if x >= xg[n - 1] { return yg[n - 1]; }
    let mut lo = 0; let mut hi = n - 1;
    while hi - lo > 1 { let m = (lo + hi) / 2; if xg[m] <= x { lo = m; } else { hi = m; } }
    let t = (x - xg[lo]) / (xg[hi] - xg[lo]).max(1e-30);
    yg[lo] * (1.0 - t) + yg[hi] * t
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;

    pub(crate) fn make_grid_pub() -> (Vec<f64>, Vec<f64>) {
        make_grid()
    }

    fn make_grid() -> (Vec<f64>, Vec<f64>) {
        let n = 500;
        let h0: f64 = 67.36e3 / 3.086e22;
        let om: f64 = 0.3153;
        let ol: f64 = 0.6847;
        let eta: Vec<f64> = (0..n).map(|i| 1.0 + i as f64 * 28.0).collect();
        let a: Vec<f64> = eta.iter().map(|&e| {
            // Rough a(η): a ~ η² H₀ Ω_m / 4 at early times
            let x = e * h0 * om.sqrt() / 2.0;
            (x * x).min(1.0).max(1e-6)
        }).collect();
        (eta, a)
    }

    #[test]
    fn test_growth_normalised() {
        let (eta, a) = make_grid();
        let h0: f64 = 67.36e3 / 3.086e22;
        let g = GrowthFunction::solve_flrw(h0, 0.3153, 0.6847, &eta, &a);
        let d_final = *g.d_vals.last().unwrap();
        assert!((d_final - 1.0).abs() < 1e-6, "D(η₀) = {:.6}", d_final);
    }

    #[test]
    fn test_growth_increases() {
        let (eta, a) = make_grid();
        let h0: f64 = 67.36e3 / 3.086e22;
        let g = GrowthFunction::solve_flrw(h0, 0.3153, 0.6847, &eta, &a);
        // D should generally increase (structure grows)
        assert!(g.d_vals[g.d_vals.len() / 2] < g.d_vals[g.d_vals.len() - 1],
            "D must increase with time");
    }

    #[test]
    fn test_modulation_linear_in_shear() {
        let (eta, a) = make_grid();
        let h0: f64 = 67.36e3 / 3.086e22;
        let g = GrowthFunction::solve_flrw(h0, 0.3153, 0.6847, &eta, &a);
        let m1 = g.modulation(1e-3);
        let m2 = g.modulation(2e-3);
        assert!((m2 / m1 - 2.0).abs() < 0.01, "Linear scaling: {:.4}", m2 / m1);
    }

    #[test]
    fn test_modulation_flrw_zero() {
        let (eta, a) = make_grid();
        let h0: f64 = 67.36e3 / 3.086e22;
        let g = GrowthFunction::solve_flrw(h0, 0.3153, 0.6847, &eta, &a);
        assert_eq!(g.modulation(0.0), 0.0, "FLRW: δD/D = 0");
    }
}
