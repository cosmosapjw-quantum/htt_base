// Level 1: Global tilt evolution β(N).
// BB-05: Integrates King-Ellis ODE over e-fold time N = ln a.

use super::*;

/// Evolve global tilt β from N_start to N_end using Tier B (zero-shear).
///
/// Returns (N_grid, beta_grid, first_integral_grid).
pub(crate) fn evolve_global_tilt_tier_b(
    beta_init: f64,
    w: f64,
    n_start: f64,  // N = ln(a_start)
    n_end: f64,    // N = ln(a_end) = 0 for today
    n_points: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let dn = (n_end - n_start) / (n_points as f64 - 1.0);
    let mut n_grid = Vec::with_capacity(n_points);
    let mut beta_grid = Vec::with_capacity(n_points);
    let mut fi_grid = Vec::with_capacity(n_points);

    let mut beta = beta_init;
    for i in 0..n_points {
        let n = n_start + i as f64 * dn;
        let a = n.exp();
        n_grid.push(n);
        beta_grid.push(beta);
        fi_grid.push(first_integral(a, w, beta));

        if i < n_points - 1 {
            // RK4
            let k1 = king_ellis_zero_shear_rhs(beta, w);
            let k2 = king_ellis_zero_shear_rhs(beta + 0.5*dn*k1, w);
            let k3 = king_ellis_zero_shear_rhs(beta + 0.5*dn*k2, w);
            let k4 = king_ellis_zero_shear_rhs(beta + dn*k3, w);
            beta += dn * (k1 + 2.0*k2 + 2.0*k3 + k4) / 6.0;
            beta = beta.max(0.0); // β ≥ 0
        }
    }
    (n_grid, beta_grid, fi_grid)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dust_decay_profile() {
        let (_, beta, _) = evolve_global_tilt_tier_b(0.1, 0.0, -10.0, 0.0, 5000);
        assert!(beta.last().unwrap() < &0.01, "Dust tilt must decay");
        // Monotonic decay
        for i in 1..beta.len() {
            assert!(beta[i] <= beta[i-1] + 1e-15, "Non-monotonic at i={}", i);
        }
    }

    #[test]
    fn test_radiation_frozen_evolution() {
        let (_, beta, _) = evolve_global_tilt_tier_b(0.1, 1.0/3.0, -10.0, 0.0, 1000);
        // β should remain constant
        for &b in &beta {
            assert!((b - 0.1).abs() < 1e-10, "Radiation β drifted to {:.6e}", b);
        }
    }

    #[test]
    fn test_first_integral_conservation_dust() {
        let (_, _, fi) = evolve_global_tilt_tier_b(0.01, 0.0, -6.0, 0.0, 10000);
        let fi_init = fi[0];
        let max_drift = fi.iter().map(|&f| (f - fi_init).abs() / fi_init.abs().max(1e-30)).fold(0.0f64, |a, b| a.max(b));
        assert!(max_drift < 1e-8, "First integral drift: {:.2e}", max_drift);
    }
}
