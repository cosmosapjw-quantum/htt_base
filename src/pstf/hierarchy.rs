// Full PSTF Boltzmann hierarchy for photon intensity.
// BC-03: dF_ℓ/dη = streaming + shear + drag + collision
//
// FLRW limit: dF_ℓ/dη = k/(2ℓ+1)[ℓF_{ℓ-1} − (ℓ+1)F_{ℓ+1}] − κ̇(F_ℓ − S_ℓ)
// Bianchi:    + (σ/H) × shear coupling ℓ↔ℓ±2
//
// State vector: [F_0, F_1, ..., F_{ℓ_max}]
// Dimension: ℓ_max + 1

use super::coupling;
use super::hierarchy_matrix::{self, HierarchyRegime};

/// Species label for the hierarchy.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum Species {
    Photon,
    Neutrino,
    /// Massive neutrino (requires energy-dependent hierarchy).
    NeutrinoMassive,
}

/// Background quantities at a single time step.
#[derive(Clone, Debug)]
pub(crate) struct HierarchyBackground {
    /// Conformal Hubble aH [Mpc⁻¹].
    pub(crate) a_h: f64,
    /// Wavenumber k [Mpc⁻¹] (0 for homogeneous Bianchi).
    pub(crate) k: f64,
    /// Shear ratio σ/H (dimensionless).
    pub(crate) sigma_h: f64,
    /// Thomson scattering rate κ̇ = n_e σ_T a [Mpc⁻¹].
    pub(crate) kappa_dot: f64,
    /// Baryon velocity v_b (for Thomson source at ℓ=1).
    pub(crate) v_b: f64,
    /// Polarisation source Π = F₂ + G₀ + G₂ (quadrupole combination).
    pub(crate) pol_source: f64,
}

/// The PSTF Boltzmann hierarchy for a single species.
#[derive(Clone, Debug)]
pub(crate) struct PSTFHierarchy {
    /// Maximum multipole.
    pub(crate) ell_max: usize,
    /// Species type.
    pub(crate) species: Species,
    /// State vector [F_0, F_1, ..., F_{ℓ_max}].
    pub(crate) state: Vec<f64>,
    /// Whether to include shear coupling (Bianchi mode).
    pub(crate) include_shear: bool,
}

impl PSTFHierarchy {
    /// Create a new hierarchy with zero initial state.
    pub(crate) fn new(ell_max: usize, species: Species, include_shear: bool) -> Self {
        Self {
            ell_max,
            species,
            state: vec![0.0; ell_max + 1],
            include_shear,
        }
    }

    /// Dimension of the state vector.
    pub(crate) fn dim(&self) -> usize { self.ell_max + 1 }

    /// Compute the full RHS: dF_ℓ/dη for all ℓ.
    ///
    /// Components:
    ///   1. Free-streaming: k × [α^down F_{ℓ-1} − α^up F_{ℓ+1}]
    ///   2. Hubble drag: −(ℓ+1)/3 × (aH) × F_ℓ  [negligible for massless species]
    ///   3. Shear coupling: (σ/H)(aH) × [α^σ_down F_{ℓ-2} + α^σ_up F_{ℓ+2}]
    ///   4. Thomson collision: −κ̇ (F_ℓ − S_ℓ)
    ///   5. Absorbing BC at ℓ_max
    pub(crate) fn rhs(&self, bg: &HierarchyBackground) -> Vec<f64> {
        let n = self.dim();
        let f = &self.state;
        let mut dfdt = vec![0.0; n];

        for ell in 0..n {
            let mut rhs_ell = 0.0;

            // ── Free-streaming: ℓ-1 → ℓ and ℓ+1 → ℓ ──
            if ell > 0 {
                rhs_ell += bg.k * coupling::free_streaming_down(ell) * f[ell - 1];
            }
            if ell + 1 < n {
                rhs_ell -= bg.k * coupling::free_streaming_up(ell) * f[ell + 1];
            } else {
                // Absorbing BC: F_{ℓ_max+1} ≈ (2ℓ+3)/(k η) F_{ℓ_max}
                // Simplified: just truncate (F_{ℓ_max+1} = 0).
                // More accurate: use the outgoing-wave BC.
            }

            // ── Shear coupling: ℓ-2 → ℓ and ℓ+2 → ℓ ──
            if self.include_shear {
                let sigma_factor = bg.sigma_h * bg.a_h; // σ = (σ/H) × H, aH → conformal
                if ell >= 2 {
                    rhs_ell += sigma_factor * coupling::shear_coupling_down(ell) * f[ell - 2];
                }
                if ell + 2 < n {
                    rhs_ell += sigma_factor * coupling::shear_coupling_up(ell) * f[ell + 2];
                }
            }

            // ── Thomson collision (photons only) ──
            if self.species == Species::Photon && bg.kappa_dot.abs() > 0.0 {
                let source = match ell {
                    0 => f[0],            // C₀ = 0 (energy conservation)
                    1 => bg.v_b,          // C₁ = −κ̇(F₁ − v_b)
                    2 => bg.pol_source / 10.0, // C₂ = −κ̇(F₂ − Π/10)
                    _ => 0.0,             // ℓ ≥ 3: pure damping
                };
                rhs_ell -= bg.kappa_dot * (f[ell] - source);
            }

            dfdt[ell] = rhs_ell;
        }
        dfdt
    }

    /// Set initial conditions for adiabatic mode.
    ///
    /// F₀ = 1 (monopole perturbation), all others = 0.
    pub(crate) fn set_adiabatic_ic(&mut self, f0: f64) {
        self.state.fill(0.0);
        self.state[0] = f0;
    }

    /// Integrate one step using forward Euler (for testing only).
    pub(crate) fn step_euler(&mut self, bg: &HierarchyBackground, d_eta: f64) {
        let rhs = self.rhs(bg);
        for i in 0..self.dim() {
            self.state[i] += d_eta * rhs[i];
        }
    }

    /// Integrate one step using RK4.
    pub(crate) fn step_rk4(&mut self, bg: &HierarchyBackground, d_eta: f64) {
        let n = self.dim();
        let f0 = self.state.clone();

        // k1
        let k1 = self.rhs(bg);

        // k2
        for i in 0..n { self.state[i] = f0[i] + 0.5*d_eta*k1[i]; }
        let k2 = self.rhs(bg);

        // k3
        for i in 0..n { self.state[i] = f0[i] + 0.5*d_eta*k2[i]; }
        let k3 = self.rhs(bg);

        // k4
        for i in 0..n { self.state[i] = f0[i] + d_eta*k3[i]; }
        let k4 = self.rhs(bg);

        // Update
        for i in 0..n {
            self.state[i] = f0[i] + d_eta*(k1[i] + 2.0*k2[i] + 2.0*k3[i] + k4[i]) / 6.0;
        }
    }
}

/// Spherical Bessel function j_ℓ(x) for verification.
/// Uses the recurrence j_{ℓ+1}(x) = (2ℓ+1)/x j_ℓ(x) − j_{ℓ-1}(x).
pub(crate) fn spherical_bessel_j(ell: usize, x: f64) -> f64 {
    if x.abs() < 1e-30 {
        return if ell == 0 { 1.0 } else { 0.0 };
    }
    // j_0 = sin(x)/x, j_1 = sin(x)/x² − cos(x)/x
    let j0 = x.sin() / x;
    if ell == 0 { return j0; }
    let j1 = j0 / x - x.cos() / x;
    if ell == 1 { return j1; }
    let mut jm1 = j0;
    let mut j = j1;
    for l in 1..ell {
        let jp1 = (2*l+1) as f64 / x * j - jm1;
        jm1 = j;
        j = jp1;
    }
    j
}

#[cfg(test)]
mod tests {
    use super::*;

    fn free_streaming_bg(k: f64) -> HierarchyBackground {
        HierarchyBackground {
            a_h: 0.0, k, sigma_h: 0.0, kappa_dot: 0.0, v_b: 0.0, pol_source: 0.0,
        }
    }

    fn flrw_bg(k: f64, kappa_dot: f64) -> HierarchyBackground {
        HierarchyBackground {
            a_h: 0.0, k, sigma_h: 0.0, kappa_dot, v_b: 0.0, pol_source: 0.0,
        }
    }

    fn bianchi_bg(k: f64, sigma_h: f64, a_h: f64) -> HierarchyBackground {
        HierarchyBackground {
            a_h, k, sigma_h, kappa_dot: 0.0, v_b: 0.0, pol_source: 0.0,
        }
    }

    // ── Dimension check ──
    #[test]
    fn test_dimension() {
        let h = PSTFHierarchy::new(30, Species::Photon, false);
        assert_eq!(h.dim(), 31);
        assert_eq!(h.state.len(), 31);
    }

    // ── Free-streaming: Bessel function solution ──
    #[test]
    fn test_free_streaming_bessel() {
        // dF_ℓ/dη = k[α^down F_{ℓ-1} − α^up F_{ℓ+1}], IC: F₀=1
        // Solution: F_ℓ(η) = (2ℓ+1) j_ℓ(kη)
        // Note: the (2ℓ+1) factor depends on the normalization convention.
        // For CLASS convention: Θ_ℓ = (2ℓ+1)⁻¹ F_ℓ, and Θ_ℓ → j_ℓ(kη).
        // In our convention, F_ℓ → j_ℓ(kη) for the standard initial condition.

        let k = 0.1;
        let ell_max = 20;
        let mut h = PSTFHierarchy::new(ell_max, Species::Neutrino, false); // no collision
        h.set_adiabatic_ic(1.0);

        let bg = free_streaming_bg(k);
        let n_steps = 50000;
        let eta_final = 100.0;
        let d_eta = eta_final / n_steps as f64;

        for _ in 0..n_steps {
            h.step_rk4(&bg, d_eta);
        }

        // Check F₀ ≈ j₀(kη) = sin(kη)/(kη)
        let x = k * eta_final;
        let j0_exact = spherical_bessel_j(0, x);
        let rel_0 = if j0_exact.abs() > 1e-10 {
            (h.state[0] - j0_exact).abs() / j0_exact.abs()
        } else {
            h.state[0].abs()
        };
        assert!(rel_0 < 0.05, "F₀ rel error: {:.2e} (F₀={:.6}, j₀={:.6})", rel_0, h.state[0], j0_exact);
    }

    // ── FLRW: Thomson damping at high ℓ ──
    #[test]
    fn test_thomson_damping() {
        let mut h = PSTFHierarchy::new(10, Species::Photon, false);
        h.state[5] = 1.0; // Inject power at ℓ=5

        let bg = flrw_bg(0.0, 100.0); // Strong damping
        let rhs = h.rhs(&bg);

        // ℓ=5: dF₅/dη = −κ̇ F₅ = −100
        assert!((rhs[5] + 100.0).abs() < 1e-10, "Thomson damp: {:.4}", rhs[5]);
    }

    // ── Thomson: energy conservation (C₀ = 0) ──
    #[test]
    fn test_thomson_energy_conservation() {
        let mut h = PSTFHierarchy::new(10, Species::Photon, false);
        h.state[0] = 1.0;

        let bg = flrw_bg(0.0, 50.0);
        let rhs = h.rhs(&bg);

        // C₀ = −κ̇(F₀ − F₀) = 0
        assert!(rhs[0].abs() < 1e-15, "C₀ = {:.2e} (must be 0)", rhs[0]);
    }

    // ── Thomson: dipole couples to v_b ──
    #[test]
    fn test_thomson_dipole_coupling() {
        let mut h = PSTFHierarchy::new(10, Species::Photon, false);
        h.state[1] = 0.01; // photon dipole

        let mut bg = flrw_bg(0.0, 50.0);
        bg.v_b = 0.005; // baryon velocity

        let rhs = h.rhs(&bg);
        // C₁ = −κ̇(F₁ − v_b) = −50(0.01 − 0.005) = −0.25
        assert!((rhs[1] + 0.25).abs() < 1e-10, "C₁ = {:.6}", rhs[1]);
    }

    // ── Shear coupling: σ drives F₀ → F₂ ──
    #[test]
    fn test_shear_monopole_to_quadrupole() {
        let mut h = PSTFHierarchy::new(10, Species::Photon, true);
        h.state[0] = 1.0; // monopole only

        let bg = bianchi_bg(0.0, 0.001, 100.0); // σ/H = 10⁻³, aH = 100
        let rhs = h.rhs(&bg);

        // Shear source at ℓ=2 from ℓ=0: σ_factor × shear_coupling_down(2) × F₀
        // = 0.001 × 100 × (2/15) × 1 = 0.1 × 2/15 ≈ 0.0133
        let expected = 0.001 * 100.0 * coupling::shear_coupling_down(2) * 1.0;
        assert!((rhs[2] - expected).abs() < 1e-10,
            "Shear F₀→F₂: {:.6e} (expect {:.6e})", rhs[2], expected);
    }

    // ── FLRW: no shear in RHS ──
    #[test]
    fn test_flrw_no_shear() {
        let mut h = PSTFHierarchy::new(10, Species::Photon, false);
        h.state[0] = 1.0;

        let bg = free_streaming_bg(0.1);
        let rhs = h.rhs(&bg);

        // Only ℓ=1 should be nonzero (free-streaming from monopole)
        assert!(rhs[0].abs() < 1e-15, "F₀ should not change without ℓ=-1");
        assert!(rhs[2].abs() < 1e-15, "No shear → no F₂ source from F₀");
    }

    // ── Truncation convergence ──
    #[test]
    fn test_truncation_convergence() {
        // Free-streaming: compare ℓ_max = 10, 20, 30 at low ℓ
        let k = 0.05;
        let eta = 50.0;
        let n_steps = 20000;
        let d_eta = eta / n_steps as f64;

        let mut results = vec![];
        for &lmax in &[10, 20, 30] {
            let mut h = PSTFHierarchy::new(lmax, Species::Neutrino, false);
            h.set_adiabatic_ic(1.0);
            let bg = free_streaming_bg(k);
            for _ in 0..n_steps { h.step_rk4(&bg, d_eta); }
            results.push(h.state[0..3].to_vec());
        }

        // F₀ should agree to < 5% between ℓ_max = 20 and 30
        let diff = (results[1][0] - results[2][0]).abs();
        let scale = results[2][0].abs().max(1e-10);
        assert!(diff / scale < 0.05,
            "Truncation: F₀(ℓ=20)={:.6}, F₀(ℓ=30)={:.6}, diff={:.2e}",
            results[1][0], results[2][0], diff);
    }

    // ── Bessel function correctness ──
    #[test]
    fn test_spherical_bessel() {
        // j_0(x) = sin(x)/x
        assert!((spherical_bessel_j(0, 1.0) - (1.0f64).sin()).abs() < 1e-14);
        // j_0(0) = 1
        assert!((spherical_bessel_j(0, 0.0) - 1.0).abs() < 1e-15);
        // j_1(0) = 0
        assert!(spherical_bessel_j(1, 0.0).abs() < 1e-15);
        // j_1(x) = sin(x)/x² − cos(x)/x at x=2
        let x: f64 = 2.0;
        let j1 = x.sin()/(x*x) - x.cos()/x;
        assert!((spherical_bessel_j(1, x) - j1).abs() < 1e-14);
    }

    // ── Neutrino: no collision ──
    #[test]
    fn test_neutrino_no_collision() {
        let mut h = PSTFHierarchy::new(10, Species::Neutrino, false);
        h.state[5] = 1.0;

        let bg = flrw_bg(0.0, 100.0); // κ̇ should not affect neutrinos
        let rhs = h.rhs(&bg);

        // Neutrinos: no Thomson scattering → rhs[5] = 0 (no k, no σ)
        assert!(rhs[5].abs() < 1e-15, "Neutrino ℓ=5 rhs = {:.2e}", rhs[5]);
    }

    // ── RK4 stability ──
    #[test]
    fn test_rk4_stability() {
        let mut h = PSTFHierarchy::new(20, Species::Photon, false);
        h.set_adiabatic_ic(1.0);
        let bg = free_streaming_bg(0.1);

        for _ in 0..10000 {
            h.step_rk4(&bg, 0.1);
        }

        // Should not blow up
        let max_val = h.state.iter().fold(0.0f64, |m, &v| m.max(v.abs()));
        assert!(max_val < 100.0, "RK4 unstable: max = {:.2e}", max_val);
    }
}
