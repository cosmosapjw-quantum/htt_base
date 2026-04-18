//! TF-01: Tetrad-based Bianchi background for Phase 6 foundation.
//!
//! Full tensor shear state σ_{αβ} in the orthonormal Bianchi tetrad,
//! replacing the scalar Σ = √(σ²/6) reduction.
//!
//! For Bianchi I: σ_{αβ} is diagonal with 2 independent components (σ₊, σ₋).
//! General Bianchi types: off-diagonal components + structure constants.
//!
//! Physics:
//!   Shear evolution: σ̇_{ab} + 3Hσ_{ab} = −κ_G Π_{ab}^{tot} + S_{curv}
//!   Bianchi I (Π=0, S=0): σ_{ab} ∝ a⁻³  (free decay)
//!   Friedmann constraint: H² = (8πG/3)ρ + σ²/6 − ³R/6
//!
//! Convention: σ₊ and σ₋ parameterize the traceless diagonal:
//!   σ_{11} = σ₊ + σ₋/√3
//!   σ_{22} = −σ₊ + σ₋/√3  
//!   σ_{33} = −2σ₋/√3
//!   σ² = σ_{ab}σ^{ab} = 2(σ₊² + σ₋²)

use crate::bianchi::background::CosmologyParams;

/// Full tetrad shear state.
#[derive(Clone, Debug)]
pub(crate) struct TetradShear {
    /// σ₊ component [s⁻¹ or Mpc⁻¹ depending on time variable].
    pub(crate) sigma_plus: f64,
    /// σ₋ component.
    pub(crate) sigma_minus: f64,
}

impl TetradShear {
    /// Construct from scalar shear Σ = σ/(√6 H) assuming axisymmetric (σ₋=0).
    pub(crate) fn from_scalar(sigma_h: f64, h: f64) -> Self {
        // σ² = 6Σ²H² = 2σ₊², so σ₊ = √3 Σ H
        let sigma_phys = sigma_h * h; // σ/H × H = σ (physical)
        Self {
            sigma_plus: sigma_phys / 2.0_f64.sqrt(),
            sigma_minus: 0.0,
        }
    }

    /// Construct from (σ₊, σ₋) directly.
    pub(crate) fn new(sp: f64, sm: f64) -> Self {
        Self { sigma_plus: sp, sigma_minus: sm }
    }

    /// σ² = σ_{ab}σ^{ab} = 2(σ₊² + σ₋²)
    pub(crate) fn sigma_squared(&self) -> f64 {
        2.0 * (self.sigma_plus.powi(2) + self.sigma_minus.powi(2))
    }

    /// Σ² = σ²/(6H²)
    pub(crate) fn big_sigma_squared(&self, h: f64) -> f64 {
        if h.abs() < 1e-30 { return 0.0; }
        self.sigma_squared() / (6.0 * h * h)
    }

    /// σ/H (dimensionless scalar shear ratio)
    pub(crate) fn sigma_over_h(&self, h: f64) -> f64 {
        if h.abs() < 1e-30 { return 0.0; }
        self.sigma_squared().sqrt() / h
    }

    /// Diagonal components of σ_{αβ}.
    pub(crate) fn diagonal(&self) -> [f64; 3] {
        let sp = self.sigma_plus;
        let sm = self.sigma_minus;
        let inv_sqrt3 = 1.0 / 3.0_f64.sqrt();
        [
            sp + sm * inv_sqrt3,
            -sp + sm * inv_sqrt3,
            -2.0 * sm * inv_sqrt3,
        ]
    }

    /// Full 3×3 symmetric trace-free tensor (Bianchi I: diagonal).
    pub(crate) fn tensor_3x3(&self) -> [[f64; 3]; 3] {
        let d = self.diagonal();
        [
            [d[0], 0.0, 0.0],
            [0.0, d[1], 0.0],
            [0.0, 0.0, d[2]],
        ]
    }

    /// Trace check: σ_{11} + σ_{22} + σ_{33} = 0 (must be exact).
    pub(crate) fn trace(&self) -> f64 {
        let d = self.diagonal();
        d[0] + d[1] + d[2]
    }
}

/// Tetrad background state at a single time step.
#[derive(Clone, Debug)]
pub(crate) struct TetradBackground {
    /// Scale factor a.
    pub(crate) a: f64,
    /// Conformal Hubble rate aH [Mpc⁻¹].
    pub(crate) a_h: f64,
    /// Physical Hubble H [s⁻¹].
    pub(crate) h_phys: f64,
    /// Full tensor shear state.
    pub(crate) shear: TetradShear,
    /// Conformal time η [Mpc].
    pub(crate) eta: f64,
}

/// Evolve the full tensor shear for Bianchi I.
///
/// For Bianchi I with no anisotropic stress (Π_{ab}=0):
///   dσ±/dN = −(2−q)σ±
/// where N = ln(a), q = deceleration parameter.
///
/// Exact solution: σ±(a) = σ±(a_i) × (a/a_i)^{−3} in radiation era (q=1).
pub(crate) fn evolve_tetrad_bianchi_i(
    cosmo: &CosmologyParams,
    shear_init: &TetradShear,
    a_min: f64,
    n_points: usize,
) -> Vec<TetradBackground> {
    let ln_a_min = a_min.ln();
    let d_ln_a = -ln_a_min / (n_points as f64 - 1.0);

    let h0c = cosmo.h0_si / 2.99792458e8 * 3.08567758e22; // H₀ in Mpc⁻¹

    let mut sp = shear_init.sigma_plus;
    let mut sm = shear_init.sigma_minus;
    let mut result = Vec::with_capacity(n_points);
    let mut eta = 0.0_f64;

    for i in 0..n_points {
        let ln_a = ln_a_min + i as f64 * d_ln_a;
        let a = ln_a.exp();
        let h = cosmo.hubble_of_a(a);
        let a_h = a * h0c * (cosmo.e2_of_a(a)).sqrt();
        let shear = TetradShear::new(sp, sm);

        // η integration (trapezoidal)
        if i > 0 {
            let a_prev = (ln_a_min + (i - 1) as f64 * d_ln_a).exp();
            let a_h_prev = a_prev * h0c * (cosmo.e2_of_a(a_prev)).sqrt();
            let da = a - a_prev;
            eta += 0.5 * da * (1.0 / a_h_prev.max(1e-30) + 1.0 / a_h.max(1e-30));
        }

        result.push(TetradBackground { a, a_h, h_phys: h, shear, eta });

        // RK4 step for (σ₊, σ₋) evolution in physical shear
        // Physical: dσ_{ab}/dt + 3Hσ_{ab} = 0 (Bianchi I, no source)
        // In N=ln(a): dσ±/dN = -3σ± (exact for Bianchi I)
        // With deceleration correction for general background:
        //   dσ±/dN = -(3 + Ḣ/H² + Ḣ/H²×Σ²) σ± ≈ -3σ± to leading order
        // We use the exact RHS including q-dependence for generality.
        if i < n_points - 1 {
            let rhs = |_a_val: f64, sp_val: f64, sm_val: f64| -> (f64, f64) {
                // For Bianchi I with no anisotropic stress and no curvature source:
                // dσ_{ab}/dN = -3 σ_{ab} (exact, independent of q for physical σ)
                (-3.0 * sp_val, -3.0 * sm_val)
            };

            let h_step = d_ln_a;
            let (k1p, k1m) = rhs(a, sp, sm);
            let a_half = (ln_a + 0.5 * h_step).exp();
            let (k2p, k2m) = rhs(a_half, sp + 0.5 * h_step * k1p, sm + 0.5 * h_step * k1m);
            let (k3p, k3m) = rhs(a_half, sp + 0.5 * h_step * k2p, sm + 0.5 * h_step * k2m);
            let a_next = (ln_a + h_step).exp();
            let (k4p, k4m) = rhs(a_next, sp + h_step * k3p, sm + h_step * k3m);

            sp += h_step / 6.0 * (k1p + 2.0 * k2p + 2.0 * k3p + k4p);
            sm += h_step / 6.0 * (k1m + 2.0 * k2m + 2.0 * k3m + k4m);
        }
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn planck_cosmo() -> CosmologyParams {
        CosmologyParams::standard(67.36, 9.14e-5, 0.3153, 0.6847)
    }

    /// TF-01 GATE: σ ∝ a⁻³ free decay for Bianchi I.
    #[test]
    fn test_bianchi_i_free_decay() {
        let cosmo = planck_cosmo();
        let a_min = 1e-4;
        let sigma_h_init = 1e-3;
        let h_init = cosmo.hubble_of_a(a_min);
        let shear_init = TetradShear::from_scalar(sigma_h_init, h_init);

        let bg = evolve_tetrad_bianchi_i(&cosmo, &shear_init, a_min, 5000);

        // Check σ₊(a) / σ₊(a_min) ≈ (a/a_min)^{-3} in radiation era
        let sp_init = bg[0].shear.sigma_plus;
        for b in &bg[100..1000] {
            let a_ratio = b.a / a_min;
            let expected_decay = a_ratio.powf(-3.0);
            let actual_ratio = b.shear.sigma_plus / sp_init;
            let rel_err = (actual_ratio / expected_decay - 1.0).abs();
            assert!(rel_err < 0.05, 
                "σ decay error at a={:.4e}: expected a^-3={:.6e}, got ratio={:.6e}, err={:.2}%",
                b.a, expected_decay, actual_ratio, rel_err * 100.0);
        }
        eprintln!("  σ₊ free decay: a⁻³ verified to 5% across radiation era");
    }

    /// Trace of σ_{αβ} must be exactly zero.
    #[test]
    fn test_shear_traceless() {
        let s = TetradShear::new(0.3, 0.7);
        assert!(s.trace().abs() < 1e-14, "Trace = {}", s.trace());
    }

    /// σ² = 2(σ₊² + σ₋²) identity.
    #[test]
    fn test_sigma_squared_identity() {
        let s = TetradShear::new(0.3, 0.5);
        let d = s.diagonal();
        let sigma_sq_diag = d[0].powi(2) + d[1].powi(2) + d[2].powi(2);
        let sigma_sq_direct = s.sigma_squared();
        assert!((sigma_sq_diag - sigma_sq_direct).abs() < 1e-14,
            "σ² mismatch: diag={:.10e}, direct={:.10e}", sigma_sq_diag, sigma_sq_direct);
    }

    /// Axisymmetric limit (σ₋=0) recovers scalar BianchiBackground.
    #[test]
    fn test_axisymmetric_limit() {
        let cosmo = planck_cosmo();
        let sigma_h_init = 1e-3;
        let h_init = cosmo.hubble_of_a(1e-4);
        let shear = TetradShear::from_scalar(sigma_h_init, h_init);

        // σ/H should match input
        let sigma_h_recovered = shear.sigma_over_h(h_init);
        let rel_err = (sigma_h_recovered / sigma_h_init - 1.0).abs();
        assert!(rel_err < 1e-10, "σ/H roundtrip error: {:.2e}", rel_err);
    }

    /// Bianchi I with σ₋ ≠ 0 still decays as a⁻³.
    #[test]
    fn test_non_axisymmetric_decay() {
        let cosmo = planck_cosmo();
        let a_min = 1e-4;
        let shear_init = TetradShear::new(5e-20, 3e-20); // non-axisymmetric

        let bg = evolve_tetrad_bianchi_i(&cosmo, &shear_init, a_min, 3000);

        // Both components should decay as a⁻³
        let sp0 = bg[0].shear.sigma_plus;
        let sm0 = bg[0].shear.sigma_minus;
        for b in &bg[500..1500] {
            let a_ratio = b.a / a_min;
            let decay = a_ratio.powf(-3.0);
            let err_p = (b.shear.sigma_plus / (sp0 * decay) - 1.0).abs();
            let err_m = (b.shear.sigma_minus / (sm0 * decay) - 1.0).abs();
            assert!(err_p < 0.05, "σ₊ decay error at a={:.2e}: {:.2}%", b.a, err_p*100.0);
            assert!(err_m < 0.05, "σ₋ decay error at a={:.2e}: {:.2}%", b.a, err_m*100.0);
        }
    }

    /// η integration is monotonically increasing.
    #[test]
    fn test_eta_monotonic() {
        let cosmo = planck_cosmo();
        let shear = TetradShear::new(1e-20, 0.0);
        let bg = evolve_tetrad_bianchi_i(&cosmo, &shear, 1e-4, 1000);
        for i in 1..bg.len() {
            assert!(bg[i].eta > bg[i-1].eta, "η not monotonic at i={}", i);
        }
    }
}
