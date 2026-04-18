// BE-05g: General-Bianchi Reionization Module.
//
// Flexible x_e(z) parametrization for reionization:
//   Tanh: standard single-step (CAMB/CLASS default)
//   ManyTanh: multi-step reionization
//   Interpolated: arbitrary x_e(z) from table
//
// Combined with recombination x_e: x_e_total = max(x_e_rec, x_e_rei).

const F_HE_DEFAULT: f64 = 0.0813; // Y_p/(4(1−Y_p)) for Y_p=0.2454

/// Reionization parametrization.
#[derive(Clone)]
pub(crate) enum ReionizationModel {
    /// Standard tanh step: x_e = (1+f_He)/2 × [1 + tanh((y_re−y)/Δy)]
    /// where y = (1+z)^{3/2}.
    Tanh { z_re: f64, delta_z: f64, f_he: f64 },
    /// Multi-step reionization: sum of tanh steps.
    ManyTanh { steps: Vec<(f64, f64, f64)> }, // (z_i, δz_i, Δx_e_i)
    /// Interpolated from table.
    Interpolated { z_grid: Vec<f64>, xe_grid: Vec<f64> },
}

impl ReionizationModel {
    /// Standard Planck 2018 reionization.
    pub(crate) fn planck2018() -> Self {
        Self::Tanh { z_re: 7.67, delta_z: 0.5, f_he: F_HE_DEFAULT }
    }

    /// x_e from reionization at redshift z.
    pub(crate) fn x_e_reion(&self, z: f64) -> f64 {
        match self {
            Self::Tanh { z_re, delta_z, f_he } => {
                let y_re = (1.0 + z_re).powf(1.5);
                let y = (1.0 + z).powf(1.5);
                let dy = 1.5 * (1.0 + z_re).sqrt() * delta_z;
                let x_full = 1.0 + *f_he; // fully ionised H + He
                x_full * 0.5 * (1.0 + ((y_re - y) / dy).tanh())
            }
            Self::ManyTanh { steps } => {
                let mut xe = 0.0;
                for &(z_i, dz_i, dx_i) in steps {
                    let y_i = (1.0 + z_i).powf(1.5);
                    let y = (1.0 + z).powf(1.5);
                    let dy_i = 1.5 * (1.0 + z_i).sqrt() * dz_i;
                    xe += dx_i * 0.5 * (1.0 + ((y_i - y) / dy_i).tanh());
                }
                xe
            }
            Self::Interpolated { z_grid, xe_grid } => {
                lin_interp(z_grid, xe_grid, z)
            }
        }
    }

    /// dx_e/dz (for visibility function computation).
    pub(crate) fn dx_e_dz(&self, z: f64) -> f64 {
        let h = 0.01 * (1.0 + z).max(0.1);
        let xp = self.x_e_reion(z + h);
        let xm = self.x_e_reion((z - h).max(0.0));
        (xp - xm) / (2.0 * h)
    }
}

/// Combined recombination + reionization x_e.
///
/// Uses max(x_e_rec, x_e_rei) for smooth joining.
pub(crate) fn x_e_total(x_e_rec: f64, x_e_rei: f64) -> f64 {
    x_e_rec.max(x_e_rei)
}

/// Compute τ_reio from reionization model.
///
/// τ_reio = ∫ n_e(z) σ_T c |dt/dz| dz
pub(crate) fn tau_reion(
    model: &ReionizationModel,
    z_start: f64,
    z_end: f64,
    n_h0: f64,      // hydrogen number density today [m⁻³]
    h0: f64,         // Hubble constant [s⁻¹]
    omega_m: f64,
    omega_r: f64,
    omega_l: f64,
) -> f64 {
    let sigma_t = 6.6524587321e-29; // [m²]
    let c = 2.99792458e8; // [m/s]
    let n_steps = 5000;
    let dz = (z_start - z_end) / n_steps as f64;
    let mut tau = 0.0;

    for i in 0..n_steps {
        let z = z_end + (i as f64 + 0.5) * dz;
        let a = 1.0 / (1.0 + z);
        let xe = model.x_e_reion(z);
        let ne = xe * n_h0 / (a * a * a); // n_e(z) = x_e × n_H(z)
        let e_z = (omega_r / (a * a * a * a) + omega_m / (a * a * a) + omega_l).max(1e-30).sqrt();
        let h_z = h0 * e_z;
        // |dt/dz| = 1/(H(z)(1+z))
        let dt_dz = 1.0 / (h_z * (1.0 + z));
        tau += ne * sigma_t * c * dt_dz * dz;
    }
    tau
}

fn lin_interp(xg: &[f64], yg: &[f64], x: f64) -> f64 {
    let n = xg.len();
    if n == 0 { return 0.0; }
    if x <= xg[0] { return yg[0]; }
    if x >= xg[n - 1] { return yg[n - 1]; }
    let mut lo = 0;
    let mut hi = n - 1;
    while hi - lo > 1 { let m = (lo + hi) / 2; if xg[m] <= x { lo = m; } else { hi = m; } }
    let t = (x - xg[lo]) / (xg[hi] - xg[lo]).max(1e-30);
    yg[lo] * (1.0 - t) + yg[hi] * t
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tanh_fully_ionised_low_z() {
        let m = ReionizationModel::planck2018();
        let xe = m.x_e_reion(0.0);
        assert!((xe - (1.0 + F_HE_DEFAULT)).abs() < 0.01,
            "z=0: x_e = {:.4} (expect {:.4})", xe, 1.0 + F_HE_DEFAULT);
    }

    #[test]
    fn test_tanh_neutral_high_z() {
        let m = ReionizationModel::planck2018();
        let xe = m.x_e_reion(30.0);
        assert!(xe < 0.01, "z=30: x_e = {:.4} (expect ~0)", xe);
    }

    #[test]
    fn test_tanh_midpoint() {
        let m = ReionizationModel::Tanh { z_re: 8.0, delta_z: 0.5, f_he: F_HE_DEFAULT };
        let xe = m.x_e_reion(8.0);
        let expected = (1.0 + F_HE_DEFAULT) * 0.5;
        assert!((xe - expected).abs() < 0.05,
            "z=z_re: x_e = {:.4} (expect {:.4})", xe, expected);
    }

    #[test]
    fn test_tau_reion_planck() {
        let m = ReionizationModel::planck2018();
        let h0_si: f64 = 67.36e3 / 3.086e22; // H₀ [s⁻¹]
        let n_h0: f64 = (1.0 - 0.2454) * 0.0493 * 3.0 * h0_si.powi(2)
                   / (8.0 * std::f64::consts::PI * 6.674e-11) / 1.673e-27;
        let tau = tau_reion(&m, 30.0, 0.0, n_h0, h0_si, 0.3153, 9.14e-5, 0.6847);
        assert!(tau > 0.03 && tau < 0.08,
            "τ_reio = {:.4} (expect 0.054 ± 0.007)", tau);
    }

    #[test]
    fn test_many_tanh_3step() {
        let m = ReionizationModel::ManyTanh {
            steps: vec![
                (10.0, 0.5, 0.5),  // first step: half ionisation at z=10
                (7.0, 0.5, 0.3),   // second step at z=7
                (3.5, 0.5, 0.2813), // third step: complete He reionisation
            ],
        };
        let xe_0 = m.x_e_reion(0.0);
        assert!((xe_0 - 1.0813).abs() < 0.05, "z=0: x_e = {:.4}", xe_0);
        let xe_15 = m.x_e_reion(15.0);
        assert!(xe_15 < 0.1, "z=15: x_e = {:.4}", xe_15);
    }

    #[test]
    fn test_interpolated() {
        let m = ReionizationModel::Interpolated {
            z_grid: vec![0.0, 5.0, 10.0, 20.0],
            xe_grid: vec![1.08, 1.08, 0.5, 0.001],
        };
        assert!((m.x_e_reion(0.0) - 1.08).abs() < 1e-10);
        assert!((m.x_e_reion(7.5) - 0.79).abs() < 0.01); // linear interp
    }

    #[test]
    fn test_x_e_total() {
        assert!((x_e_total(0.0001, 1.08) - 1.08).abs() < 1e-10);
        assert!((x_e_total(0.5, 0.3) - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_dx_e_dz() {
        let m = ReionizationModel::planck2018();
        let d = m.dx_e_dz(7.67);
        // At z_re: steepest descent, dx/dz should be negative (x_e increases as z decreases)
        assert!(d < 0.0, "dx_e/dz at z_re should be < 0: {:.4e}", d);
    }
}
