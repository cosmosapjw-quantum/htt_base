// BE-05g: Direction-dependent Thomson scattering for tilted Bianchi models.
//
// For tilted fluid with baryon 4-velocity u_b^a = γ_b(n^a + v_b^a):
//   κ̇_eff(ê,t) = n_e σ_T c γ_b (1 − v_b · ê)
//
// Orthogonal limit (v_b = 0): κ̇_eff = n_e σ_T c (scalar, isotropic).
// Tilted: dipolar modulation δκ̇/κ̇ ≈ −v_b · ê at leading order (ℓ=1).

const SIGMA_T: f64 = 6.6524587321e-29; // m²
const C_LIGHT: f64 = 2.99792458e8;     // m/s

/// Tilted Thomson scattering state.
#[derive(Clone, Debug)]
pub(crate) struct TiltedThomson {
    /// Lorentz factor γ_b = 1/√(1 − v²).
    pub(crate) gamma_b: f64,
    /// Baryon spatial velocity in the normal frame [v_x, v_y, v_z].
    pub(crate) v_b: [f64; 3],
}

impl TiltedThomson {
    /// Orthogonal (no tilt): v_b = 0, γ_b = 1.
    pub(crate) fn orthogonal() -> Self {
        Self { gamma_b: 1.0, v_b: [0.0; 3] }
    }

    /// Tilted with given velocity.
    pub(crate) fn tilted(v_b: [f64; 3]) -> Self {
        let v2 = v_b[0] * v_b[0] + v_b[1] * v_b[1] + v_b[2] * v_b[2];
        let gamma = 1.0 / (1.0 - v2).max(1e-30).sqrt();
        Self { gamma_b: gamma, v_b }
    }

    /// Speed |v_b|.
    pub(crate) fn speed(&self) -> f64 {
        (self.v_b[0].powi(2) + self.v_b[1].powi(2) + self.v_b[2].powi(2)).sqrt()
    }

    /// Direction-dependent Thomson scattering rate [s⁻¹].
    ///
    /// κ̇_eff(ê) = n_e σ_T c γ_b (1 − v_b · ê)
    pub(crate) fn kappa_dot_eff(&self, n_e: f64, e_hat: &[f64; 3]) -> f64 {
        let v_dot_e = self.v_b[0] * e_hat[0] + self.v_b[1] * e_hat[1] + self.v_b[2] * e_hat[2];
        n_e * SIGMA_T * C_LIGHT * self.gamma_b * (1.0 - v_dot_e)
    }

    /// Direction-averaged Thomson rate [s⁻¹].
    ///
    /// ⟨κ̇_eff⟩_Ω = n_e σ_T c γ_b  (v_b · ê averages to zero on S²)
    pub(crate) fn kappa_dot_avg(&self, n_e: f64) -> f64 {
        n_e * SIGMA_T * C_LIGHT * self.gamma_b
    }

    /// Fractional modulation δκ̇/κ̇ for direction ê.
    ///
    /// δκ̇/κ̇ = (κ̇(ê) − ⟨κ̇⟩) / ⟨κ̇⟩ = −v_b · ê / (1 − v_b · ê)
    /// Leading order (|v_b| ≪ 1): δκ̇/κ̇ ≈ −v_b · ê (dipolar, ℓ=1)
    pub(crate) fn kappa_dot_modulation(&self, e_hat: &[f64; 3]) -> f64 {
        let v_dot_e = self.v_b[0] * e_hat[0] + self.v_b[1] * e_hat[1] + self.v_b[2] * e_hat[2];
        -v_dot_e / (1.0 - v_dot_e).max(1e-15)
    }
}

/// Direction-dependent optical depth τ(ê) from a visibility history.
///
/// τ(ê, η) = ∫_η^{η₀} κ̇_eff(ê, η') dη'
pub(crate) fn tau_direction(
    e_hat: &[f64; 3],
    eta_grid: &[f64],     // conformal time grid [Mpc]
    ne_grid: &[f64],      // electron density grid [m⁻³]
    tilt_grid: &[TiltedThomson], // tilt state at each η
    eta_start_idx: usize, // index of η in the grid
) -> f64 {
    let n = eta_grid.len();
    let mut tau = 0.0;
    for i in (eta_start_idx + 1)..n {
        let deta = eta_grid[i] - eta_grid[i - 1]; // [Mpc]
        let deta_m = deta * 3.086e22; // convert Mpc → m
        let kd_prev = tilt_grid[i - 1].kappa_dot_eff(ne_grid[i - 1], e_hat);
        let kd_curr = tilt_grid[i].kappa_dot_eff(ne_grid[i], e_hat);
        tau += 0.5 * (kd_prev + kd_curr) * deta_m / C_LIGHT; // κ̇ dη/c → dimensionless
    }
    tau
}

/// Direction-dependent visibility function g(ê, η).
///
/// g(ê, η) = κ̇_eff(ê, η) × exp(−τ(ê, η))
pub(crate) fn visibility_direction(
    e_hat: &[f64; 3],
    eta_idx: usize,
    eta_grid: &[f64],
    ne_grid: &[f64],
    tilt_grid: &[TiltedThomson],
) -> f64 {
    let kd = tilt_grid[eta_idx].kappa_dot_eff(ne_grid[eta_idx], e_hat);
    let tau = tau_direction(e_hat, eta_grid, ne_grid, tilt_grid, eta_idx);
    kd * (-tau).exp()
}

/// Reionization EE/TE polarisation source.
///
/// S_E(η) = g(η) × Σ_m F_{2m} × W_{2m}(ê)
/// where F_{2m} is the local radiation quadrupole from the hierarchy.
pub(crate) fn reionization_ee_source(
    g_rei: f64,
    f_2m: &[f64; 5], // F_{2,-2}, F_{2,-1}, F_{2,0}, F_{2,1}, F_{2,2}
    projection: f64,
) -> f64 {
    // Total quadrupole power (rotationally invariant)
    let q2: f64 = f_2m.iter().map(|&f| f * f).sum();
    g_rei * q2.sqrt() * projection
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_orthogonal_isotropic() {
        let tt = TiltedThomson::orthogonal();
        let ne = 1e6; // m⁻³
        let e1 = [1.0, 0.0, 0.0];
        let e2 = [0.0, 1.0, 0.0];
        let kd1 = tt.kappa_dot_eff(ne, &e1);
        let kd2 = tt.kappa_dot_eff(ne, &e2);
        assert!((kd1 - kd2).abs() < 1e-30, "Orthogonal: isotropic κ̇");
        assert!((kd1 - ne * SIGMA_T * C_LIGHT).abs() < 1e-20);
    }

    #[test]
    fn test_tilted_dipolar() {
        let v = 1e-3; // β = 10⁻³
        let tt = TiltedThomson::tilted([v, 0.0, 0.0]);
        let ne = 1e6;
        // Along v: κ̇(ê‖v) = n_e σ_T c γ (1 − v) < ⟨κ̇⟩
        let kd_par = tt.kappa_dot_eff(ne, &[1.0, 0.0, 0.0]);
        // Against v: κ̇(ê anti-v) = n_e σ_T c γ (1 + v) > ⟨κ̇⟩
        let kd_anti = tt.kappa_dot_eff(ne, &[-1.0, 0.0, 0.0]);
        let kd_avg = tt.kappa_dot_avg(ne);
        assert!(kd_par < kd_avg, "Along v: less scattering");
        assert!(kd_anti > kd_avg, "Against v: more scattering");
        // Dipolar amplitude ~ v
        let mod_par = tt.kappa_dot_modulation(&[1.0, 0.0, 0.0]);
        assert!((mod_par + v).abs() / v < 0.01,
            "δκ̇/κ̇ = {:.4e} (expect {:.4e})", mod_par, -v);
    }

    #[test]
    fn test_modulation_average_zero() {
        let tt = TiltedThomson::tilted([0.01, -0.005, 0.003]);
        // Average modulation over S² should be ~0
        let dirs = crate::recombination::aniso_sobolev::gauss_legendre_s2(12);
        let mut sum = 0.0;
        let mut wsum = 0.0;
        for &(e, w) in &dirs {
            sum += tt.kappa_dot_modulation(&e) * w;
            wsum += w;
        }
        let avg = sum / wsum;
        assert!(avg.abs() < 1e-4, "⟨δκ̇/κ̇⟩ = {:.4e} (expect 0)", avg);
    }

    #[test]
    fn test_tilted_bi_beta_1e3() {
        // BI tilted with β = 10⁻³
        let beta = 1e-3;
        let tt = TiltedThomson::tilted([beta, 0.0, 0.0]);
        let mod_max = tt.kappa_dot_modulation(&[1.0, 0.0, 0.0]).abs();
        assert!((mod_max - beta).abs() / beta < 0.01,
            "δκ̇/κ̇ = {:.4e} (expect β = {:.4e})", mod_max, beta);
    }

    #[test]
    fn test_orthogonal_tau_scalar() {
        // For v_b = 0: τ(ê) should be same for all directions
        let n = 100;
        let eta: Vec<f64> = (0..n).map(|i| i as f64 * 0.1).collect();
        let ne: Vec<f64> = (0..n).map(|_| 1e6).collect(); // constant n_e
        let tilt: Vec<TiltedThomson> = (0..n).map(|_| TiltedThomson::orthogonal()).collect();
        let tau_x = tau_direction(&[1.0, 0.0, 0.0], &eta, &ne, &tilt, 0);
        let tau_z = tau_direction(&[0.0, 0.0, 1.0], &eta, &ne, &tilt, 0);
        assert!((tau_x - tau_z).abs() < 1e-20, "Orthogonal: τ isotropic");
    }

    #[test]
    fn test_gamma_b_correct() {
        let v = 0.1;
        let tt = TiltedThomson::tilted([v, 0.0, 0.0]);
        let expected = 1.0 / (1.0 - v * v).sqrt();
        assert!((tt.gamma_b - expected).abs() < 1e-12);
    }

    #[test]
    fn test_ee_source_zero_quadrupole() {
        let s = reionization_ee_source(0.1, &[0.0; 5], 1.0);
        assert_eq!(s, 0.0, "No quadrupole → no EE source");
    }

    #[test]
    fn test_ee_source_positive() {
        let f2m = [0.01, 0.02, 0.03, 0.02, 0.01];
        let s = reionization_ee_source(0.1, &f2m, 1.0);
        assert!(s > 0.0, "EE source must be positive with nonzero quadrupole");
    }
}
