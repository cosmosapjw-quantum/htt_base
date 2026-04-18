// BE-01: Source function S_{ℓm}(η) for LoS integration.
//
// Standard decomposition (Seljak & Zaldarriaga 1996):
//   S(k,η) = S_SW + S_Dop + S_ISW + S_pol
//
// where:
//   S_SW  = g(η) [Θ₀(k,η) + Ψ(k,η)]             (Sachs-Wolfe monopole)
//   S_Dop = −g'(η) v_b(k,η) / k                    (Doppler)
//   S_ISW = e^{−τ} [Ψ'(k,η) + Φ'(k,η)]            (integrated Sachs-Wolfe)
//   S_pol = (3/(4k²)) g''(η) Π(k,η)                (polarization, Π=Θ₂+E₂)
//
// For Bianchi: the source is m-dependent through the PSTF hierarchy:
//   S_{ℓm}(η) = g(η) F_{ℓm}(η) + e^{−τ} σ̇_{Hm}(η)  (shear-ISW)

/// Visibility provider trait (accepts BA-02 Peebles or BE-05c HyRec-2).
pub(crate) trait VisibilityProvider {
    /// Visibility function g(η) [Mpc⁻¹].
    fn g(&self, eta: f64) -> f64;
    /// dg/dη [Mpc⁻²].
    fn g_dot(&self, eta: f64) -> f64;
    /// d²g/dη² [Mpc⁻³].
    fn g_ddot(&self, eta: f64) -> f64;
    /// Optical depth τ(η) from today.
    fn tau(&self, eta: f64) -> f64;
    /// Thomson rate κ̇(η) [Mpc⁻¹].
    fn kappa_dot(&self, eta: f64) -> f64;
    /// Conformal time today η₀ [Mpc].
    fn eta_0(&self) -> f64;
    /// Redshift of last scattering.
    fn z_star(&self) -> f64;
}

/// Perturbation data at a single (k, η) point.
#[derive(Clone, Debug)]
pub(crate) struct PerturbationSnapshot {
    /// Photon monopole Θ₀.
    pub(crate) theta_0: f64,
    /// Photon quadrupole Θ₂.
    pub(crate) theta_2: f64,
    /// E-mode polarization quadrupole E₂.
    pub(crate) e_2: f64,
    /// Baryon velocity v_b (dimensionless, divided by c).
    pub(crate) v_b: f64,
    /// Newtonian potential Φ.
    pub(crate) phi: f64,
    /// Newtonian potential Ψ (= −Φ if no anisotropic stress).
    pub(crate) psi: f64,
    /// dΦ/dη.
    pub(crate) phi_dot: f64,
    /// dΨ/dη.
    pub(crate) psi_dot: f64,
    /// Shear σ/H (Bianchi only, 0 for FLRW).
    pub(crate) sigma_h: f64,
    /// dσ/dη (Bianchi only).
    pub(crate) sigma_dot: f64,
}

impl PerturbationSnapshot {
    /// FLRW snapshot with minimal data.
    pub(crate) fn flrw(theta_0: f64, theta_2: f64, v_b: f64, phi: f64, phi_dot: f64) -> Self {
        Self {
            theta_0, theta_2, e_2: 0.0, v_b, phi, psi: -phi,
            phi_dot, psi_dot: -phi_dot,
            sigma_h: 0.0, sigma_dot: 0.0,
        }
    }

    /// Bianchi snapshot with shear.
    pub(crate) fn bianchi(
        theta_0: f64, theta_2: f64, v_b: f64, phi: f64, phi_dot: f64,
        sigma_h: f64, sigma_dot: f64,
    ) -> Self {
        Self {
            theta_0, theta_2, e_2: 0.0, v_b, phi, psi: -phi,
            phi_dot, psi_dot: -phi_dot, sigma_h, sigma_dot,
        }
    }

    /// Polarization combination Π = Θ₂ + E₂.
    pub(crate) fn pi_pol(&self) -> f64 { self.theta_2 + self.e_2 }
}

/// Source function components at a single (k, η) evaluation.
#[derive(Clone, Debug, Default)]
pub(crate) struct SourceValue {
    /// Sachs-Wolfe: g × (Θ₀ + Ψ).
    pub(crate) sw: f64,
    /// Doppler: −g' × v_b / k.
    pub(crate) doppler: f64,
    /// ISW: e^{−τ} × (Ψ' + Φ').
    pub(crate) isw: f64,
    /// Polarization: (3/(4k²)) × g'' × Π.
    pub(crate) pol: f64,
    /// Shear-ISW: e^{−τ} × σ̇_H (Bianchi only).
    pub(crate) shear_isw: f64,
    /// Total S = SW + Dop + ISW + pol + shear_ISW.
    pub(crate) total: f64,
}

impl SourceValue {
    pub(crate) fn compute_total(&mut self) {
        self.total = self.sw + self.doppler + self.isw + self.pol + self.shear_isw;
    }
}

/// Evaluate the source function at a single (k, η) point.
pub(crate) fn evaluate_source(
    k: f64,
    eta: f64,
    vis: &dyn VisibilityProvider,
    pert: &PerturbationSnapshot,
) -> SourceValue {
    let g = vis.g(eta);
    let g_dot = vis.g_dot(eta);
    let g_ddot = vis.g_ddot(eta);
    let tau = vis.tau(eta);

    let mut sv = SourceValue::default();

    // Sachs-Wolfe monopole
    sv.sw = g * (pert.theta_0 + pert.psi);

    // Doppler (requires k > 0)
    if k.abs() > 1e-30 {
        sv.doppler = -g_dot * pert.v_b / k;
    }

    // ISW
    sv.isw = (-tau).exp() * (pert.psi_dot + pert.phi_dot);

    // Polarization source
    if k.abs() > 1e-30 {
        sv.pol = 0.75 / (k * k) * g_ddot * pert.pi_pol();
    }

    // Shear-ISW (Bianchi)
    sv.shear_isw = (-tau).exp() * pert.sigma_dot;

    sv.compute_total();
    sv
}

/// Source function sampled on an η-grid for a single k-mode.
///
/// Dense output interface: stores S(η) on an adaptive grid
/// with δη ≤ 1 Mpc near the recombination peak.
#[derive(Clone, Debug)]
pub(crate) struct SourceGrid {
    /// k-mode [Mpc⁻¹].
    pub(crate) k: f64,
    /// η grid [Mpc].
    pub(crate) eta_grid: Vec<f64>,
    /// Source function values at each η.
    pub(crate) values: Vec<SourceValue>,
}

impl SourceGrid {
    /// Create an empty grid for a given k.
    pub(crate) fn new(k: f64) -> Self {
        Self { k, eta_grid: Vec::new(), values: Vec::new() }
    }

    /// Push a (η, source) pair.
    pub(crate) fn push(&mut self, eta: f64, sv: SourceValue) {
        self.eta_grid.push(eta);
        self.values.push(sv);
    }

    /// Number of stored samples.
    pub(crate) fn len(&self) -> usize { self.eta_grid.len() }

    /// Maximum spacing δη near the peak (quality check).
    pub(crate) fn max_delta_eta_near_peak(&self, eta_star: f64, window: f64) -> f64 {
        let mut max_d = 0.0_f64;
        for i in 1..self.eta_grid.len() {
            let mid = 0.5 * (self.eta_grid[i] + self.eta_grid[i - 1]);
            if (mid - eta_star).abs() < window {
                let d = (self.eta_grid[i] - self.eta_grid[i - 1]).abs();
                max_d = max_d.max(d);
            }
        }
        max_d
    }

    /// Total of the SW component (diagnostic).
    pub(crate) fn sw_integral(&self) -> f64 {
        let mut sum = 0.0;
        for i in 1..self.len() {
            let deta = self.eta_grid[i] - self.eta_grid[i - 1];
            sum += 0.5 * (self.values[i].sw + self.values[i - 1].sw) * deta;
        }
        sum
    }

    /// Total source integral (diagnostic: should be finite, O(1) for unit perturbation).
    pub(crate) fn total_integral(&self) -> f64 {
        let mut sum = 0.0;
        for i in 1..self.len() {
            let deta = self.eta_grid[i] - self.eta_grid[i - 1];
            sum += 0.5 * (self.values[i].total + self.values[i - 1].total) * deta;
        }
        sum
    }
}

/// Build an adaptive η-grid: dense near recombination, coarse elsewhere.
///
/// Grid structure:
///   [η_ini, ..., η_star−50Mpc]: coarse (δη ~ 10 Mpc)
///   [η_star−50Mpc, η_star+50Mpc]: dense (δη ~ 0.5 Mpc)
///   [η_star+50Mpc, ..., η_0]: coarse (δη ~ 20 Mpc)
pub(crate) fn build_adaptive_eta_grid(
    eta_ini: f64,
    eta_0: f64,
    eta_star: f64,
    delta_eta_dense: f64,  // δη in dense region (target: 0.5 Mpc)
    delta_eta_coarse: f64, // δη in coarse regions (target: 10-20 Mpc)
    window: f64,            // half-width of dense region around η_* (target: 50 Mpc)
) -> Vec<f64> {
    let mut grid = Vec::new();

    // Early region: coarse
    let mut eta = eta_ini;
    let eta_dense_start = (eta_star - window).max(eta_ini);
    while eta < eta_dense_start {
        grid.push(eta);
        eta += delta_eta_coarse;
    }

    // Dense region around recombination
    let eta_dense_end = (eta_star + window).min(eta_0);
    while eta < eta_dense_end {
        grid.push(eta);
        eta += delta_eta_dense;
    }

    // Late region: coarse (ISW sampling)
    while eta < eta_0 {
        grid.push(eta);
        eta += delta_eta_coarse * 2.0; // even coarser for late ISW
    }

    if grid.last().map_or(true, |&last| (last - eta_0).abs() > 0.01) {
        grid.push(eta_0);
    }

    grid
}

/// Bianchi m-mode source: S_{ℓm}(η) = g F_{ℓm} + e^{−τ} σ̇_{Hm}.
///
/// For Bianchi types with vector (m=±1) and tensor (m=±2) modes,
/// the source decomposes into m-channels with different F_{ℓm}.
#[derive(Clone, Debug)]
pub(crate) struct BianchiMSource {
    /// m-value (−2, −1, 0, +1, +2).
    pub(crate) m: i32,
    /// Source grid for this m-mode.
    pub(crate) grid: SourceGrid,
}

impl BianchiMSource {
    pub(crate) fn new(m: i32, k: f64) -> Self {
        Self { m, grid: SourceGrid::new(k) }
    }
}

// ═══ Simple visibility implementation for testing ═══

/// Gaussian visibility function for unit tests.
#[derive(Clone)]
pub(crate) struct GaussianVisibility {
    pub(crate) eta_star: f64,  // peak position [Mpc]
    pub(crate) sigma_eta: f64, // width [Mpc]
    pub(crate) eta_total: f64, // η₀ [Mpc]
}

impl GaussianVisibility {
    pub(crate) fn planck_like() -> Self {
        Self { eta_star: 285.0, sigma_eta: 20.0, eta_total: 14050.0 }
    }

    fn g_unnorm(&self, eta: f64) -> f64 {
        (-(eta - self.eta_star).powi(2) / (2.0 * self.sigma_eta.powi(2))).exp()
    }

    fn norm(&self) -> f64 {
        // ∫g dη ≈ σ√(2π)
        self.sigma_eta * (2.0 * std::f64::consts::PI).sqrt()
    }
}

impl VisibilityProvider for GaussianVisibility {
    fn g(&self, eta: f64) -> f64 {
        self.g_unnorm(eta) / self.norm()
    }

    fn g_dot(&self, eta: f64) -> f64 {
        let g = self.g(eta);
        -g * (eta - self.eta_star) / self.sigma_eta.powi(2)
    }

    fn g_ddot(&self, eta: f64) -> f64 {
        let g = self.g(eta);
        let s2 = self.sigma_eta.powi(2);
        let x = eta - self.eta_star;
        g * (x * x / (s2 * s2) - 1.0 / s2)
    }

    fn tau(&self, eta: f64) -> f64 {
        // Approximate: τ large before η_*, small after
        if eta < self.eta_star { 5.0 * (self.eta_star - eta) / self.sigma_eta } else { 0.1 }
    }

    fn kappa_dot(&self, eta: f64) -> f64 {
        self.g(eta) * self.tau(eta).exp()
    }

    fn eta_0(&self) -> f64 { self.eta_total }
    fn z_star(&self) -> f64 { 1090.0 }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn vis() -> GaussianVisibility { GaussianVisibility::planck_like() }

    #[test]
    fn test_gaussian_vis_normalized() {
        let v = vis();
        let n = 10000;
        let deta = v.eta_total / n as f64;
        let mut integral = 0.0;
        for i in 0..n {
            let eta = (i as f64 + 0.5) * deta;
            integral += v.g(eta) * deta;
        }
        assert!((integral - 1.0).abs() < 0.01, "∫g dη = {:.4}", integral);
    }

    #[test]
    fn test_gaussian_vis_peaked() {
        let v = vis();
        let g_peak = v.g(v.eta_star);
        let g_off = v.g(v.eta_star + 100.0);
        assert!(g_peak > g_off * 10.0, "Peak must dominate");
    }

    #[test]
    fn test_raw_theta0_source_only() {
        let v = vis();
        let pert = PerturbationSnapshot::flrw(1.0, 0.0, 0.0, -1.0, 0.0);
        // Θ₀ + Ψ = 1.0 + 1.0 = 2.0 (Ψ = −Φ = 1.0)
        let sv = evaluate_source(0.01, v.eta_star, &v, &pert);
        assert!((sv.sw - 2.0 * v.g(v.eta_star)).abs() < 1e-10,
            "SW = {:.6e}, expect {:.6e}", sv.sw, 2.0 * v.g(v.eta_star));
    }

    #[test]
    fn test_source_doppler() {
        let v = vis();
        let pert = PerturbationSnapshot::flrw(0.0, 0.0, 0.5, 0.0, 0.0);
        let k = 0.01;
        let sv = evaluate_source(k, v.eta_star, &v, &pert);
        let expected = -v.g_dot(v.eta_star) * 0.5 / k;
        assert!((sv.doppler - expected).abs() < 1e-10,
            "Dop = {:.6e}, expect {:.6e}", sv.doppler, expected);
    }

    #[test]
    fn test_source_isw() {
        let v = vis();
        let pert = PerturbationSnapshot::flrw(0.0, 0.0, 0.0, 0.0, 1.0);
        // Ψ' + Φ' = −1.0 + 1.0 = 0 when Ψ = −Φ
        let sv = evaluate_source(0.01, v.eta_star + 200.0, &v, &pert);
        // ISW = e^{−τ} × (Ψ' + Φ') = e^{−τ} × 0 = 0
        assert!(sv.isw.abs() < 1e-10, "ISW should vanish when Ψ = −Φ");
    }

    #[test]
    fn test_source_isw_nonzero() {
        let v = vis();
        let mut pert = PerturbationSnapshot::flrw(0.0, 0.0, 0.0, 0.0, 1.0);
        pert.psi_dot = 0.5; // Break Ψ = −Φ
        let sv = evaluate_source(0.01, v.eta_star + 200.0, &v, &pert);
        assert!(sv.isw.abs() > 0.0, "ISW must be nonzero when Ψ' ≠ −Φ'");
    }

    #[test]
    fn test_source_shear_isw() {
        let v = vis();
        let pert = PerturbationSnapshot::bianchi(0.0, 0.0, 0.0, 0.0, 0.0, 1e-4, 1e-6);
        let sv = evaluate_source(0.01, v.eta_star + 200.0, &v, &pert);
        assert!(sv.shear_isw.abs() > 0.0, "Shear-ISW must be nonzero for Bianchi");
    }

    #[test]
    fn test_source_flrw_no_shear() {
        let v = vis();
        let pert = PerturbationSnapshot::flrw(1.0, 0.1, 0.01, -0.5, 0.0);
        let sv = evaluate_source(0.01, v.eta_star, &v, &pert);
        assert_eq!(sv.shear_isw, 0.0, "FLRW: no shear-ISW");
    }

    #[test]
    fn test_source_total_is_sum() {
        let v = vis();
        let pert = PerturbationSnapshot::bianchi(1.0, 0.1, 0.05, -0.5, 0.01, 1e-4, 1e-6);
        let sv = evaluate_source(0.01, v.eta_star, &v, &pert);
        let sum = sv.sw + sv.doppler + sv.isw + sv.pol + sv.shear_isw;
        assert!((sv.total - sum).abs() < 1e-15, "Total = sum of parts");
    }

    #[test]
    fn test_adaptive_grid_structure() {
        let grid = build_adaptive_eta_grid(0.0, 14050.0, 285.0, 0.5, 10.0, 50.0);
        assert!(grid.len() > 100, "Grid too small: {}", grid.len());
        assert!((grid[0] - 0.0).abs() < 1e-10, "Starts at η_ini");
        assert!((*grid.last().unwrap() - 14050.0).abs() < 50.0, "Ends near η₀");

        // Check dense region has δη ≤ 1 Mpc near η_*
        for i in 1..grid.len() {
            let mid = 0.5 * (grid[i] + grid[i - 1]);
            if (mid - 285.0).abs() < 30.0 {
                let d = grid[i] - grid[i - 1];
                assert!(d <= 1.0 + 1e-10,
                    "Dense δη = {:.2} > 1 Mpc at η = {:.1}", d, mid);
            }
        }
    }

    #[test]
    fn test_source_grid_sampling() {
        let v = vis();
        let k = 0.01;
        let grid_etas = build_adaptive_eta_grid(0.0, v.eta_total, v.eta_star, 0.5, 10.0, 50.0);
        let mut sg = SourceGrid::new(k);

        let pert = PerturbationSnapshot::flrw(1.0, 0.05, 0.01, -0.5, 0.0);
        for &eta in &grid_etas {
            let sv = evaluate_source(k, eta, &v, &pert);
            sg.push(eta, sv);
        }

        assert!(sg.len() == grid_etas.len());
        let max_d = sg.max_delta_eta_near_peak(v.eta_star, 30.0);
        assert!(max_d <= 1.0, "Max δη near peak = {:.2} Mpc (target ≤ 1)", max_d);
    }

    #[test]
    fn test_source_grid_sw_integral() {
        let v = vis();
        let k = 0.01;
        let grid_etas = build_adaptive_eta_grid(0.0, v.eta_total, v.eta_star, 0.5, 10.0, 50.0);
        let mut sg = SourceGrid::new(k);

        // Constant Θ₀+Ψ = 1 everywhere → ∫g×1 dη = 1 (normalization)
        let pert = PerturbationSnapshot::flrw(0.5, 0.0, 0.0, -0.5, 0.0);
        // Θ₀ + Ψ = 0.5 + 0.5 = 1.0
        for &eta in &grid_etas {
            let sv = evaluate_source(k, eta, &v, &pert);
            sg.push(eta, sv);
        }

        let sw_int = sg.sw_integral();
        assert!((sw_int - 1.0).abs() < 0.05,
            "∫g(Θ₀+Ψ)dη = {:.4} (expect 1.0 for unit perturbation)", sw_int);
    }

    #[test]
    fn test_bianchi_m_source() {
        let ms = BianchiMSource::new(0, 0.01);
        assert_eq!(ms.m, 0);
        assert_eq!(ms.grid.len(), 0);
    }
}
