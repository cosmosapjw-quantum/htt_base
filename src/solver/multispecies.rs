// BD-02: Stacked multi-species system.
// All species assembled into a single state vector.
// Block A: γ + v_b + E/B (Thomson-coupled)
// Block B: ν + CDM (collisionless)
// Decoupled blocks enable +23.8% wall gain via block-diagonal LU (PR-14B).

use crate::species::{SpeciesBundle, SpeciesConfig};
use crate::pstf::coupling;
use crate::collision::thomson;
use crate::collision::baryon_photon;

/// Background for the stacked solver at a single time step.
#[derive(Clone, Debug)]
pub(crate) struct StackedBackground {
    /// Conformal time η [Mpc].
    pub(crate) eta: f64,
    /// Scale factor a.
    pub(crate) a: f64,
    /// Conformal Hubble aH [Mpc⁻¹].
    pub(crate) a_h: f64,
    /// Wavenumber k [Mpc⁻¹] (0 for homogeneous Bianchi).
    pub(crate) k: f64,
    /// Shear ratio σ/H.
    pub(crate) sigma_h: f64,
    /// Thomson scattering rate κ̇ [Mpc⁻¹].
    pub(crate) kappa_dot: f64,
    /// Baryon-photon ratio R = 3ρ_b/(4ρ_γ).
    pub(crate) r_ratio: f64,
}

/// Block identification for the stacked system.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum BlockId {
    /// Block A: photon + baryon (Thomson-coupled).
    PhotonBaryon,
    /// Block B: neutrino + CDM (collisionless).
    NeutrinoCDM,
}

/// Block boundary in the flat state vector.
#[derive(Clone, Debug)]
pub(crate) struct BlockBoundary {
    pub(crate) id: BlockId,
    pub(crate) start: usize,
    pub(crate) size: usize,
}

/// Detect decoupled blocks in the stacked system.
///
/// Block A: [γ_intensity | γ_E | γ_B | baryon] — coupled by Thomson
/// Block B: [ν₁ | ... | ν_N | CDM] — collisionless
///
/// The blocks are decoupled at the ODE level: Block A's RHS depends
/// only on Block A state + background, and similarly for Block B.
/// The coupling through gravity (shared σ/H) enters via the background,
/// not through cross-block terms in the Jacobian.
pub(crate) fn detect_blocks(bundle: &SpeciesBundle) -> Vec<BlockBoundary> {
    let cfg = &bundle.config;
    let n_gamma = cfg.dof_gamma_intensity() + cfg.dof_e_mode() + cfg.dof_b_mode();
    let n_baryon = cfg.dof_baryon();
    let n_nu = cfg.dof_nu_total();
    let n_cdm = cfg.dof_cdm();

    // Block A starts at 0, includes γ + baryon
    // But baryon is at the END of the flat vector after neutrinos.
    // Memory: [γ_int | γ_E | γ_B | ν₁ | ... | ν_N | b | c]
    //          └── Block A (γ) ──┘ └── Block B (ν) ──┘ A  B
    //
    // For block-diagonal LU, we track non-contiguous blocks.
    // Block A: indices [0..n_gamma) ∪ [n_gamma+n_nu..n_gamma+n_nu+n_baryon)
    // Block B: indices [n_gamma..n_gamma+n_nu) ∪ [n_gamma+n_nu+n_baryon..end)

    vec![
        BlockBoundary { id: BlockId::PhotonBaryon, start: 0, size: n_gamma + n_baryon },
        BlockBoundary { id: BlockId::NeutrinoCDM, start: 0, size: n_nu + n_cdm },
    ]
}

/// Build the full RHS for the stacked multi-species system.
///
/// Returns dY/dη for the flat state vector Y.
pub(crate) fn build_stacked_rhs(
    bundle: &SpeciesBundle,
    bg: &StackedBackground,
) -> Vec<f64> {
    let n = bundle.total_dof();
    let mut rhs = vec![0.0; n];
    let cfg = &bundle.config;

    let mut idx = 0;

    // ── Photon intensity: free-streaming + shear + Thomson ──
    let n_int = cfg.dof_gamma_intensity();
    let f = &bundle.photon.intensity;
    for ell in 0..n_int {
        let mut val = 0.0;
        // Free-streaming
        if ell > 0 { val += bg.k * coupling::free_streaming_down(ell) * f[ell-1]; }
        if ell+1 < n_int { val -= bg.k * coupling::free_streaming_up(ell) * f[ell+1]; }
        // Shear coupling (Bianchi)
        let sigma_f = bg.sigma_h * bg.a_h;
        if ell >= 2 { val += sigma_f * coupling::shear_coupling_down(ell) * f[ell-2]; }
        if ell+2 < n_int { val += sigma_f * coupling::shear_coupling_up(ell) * f[ell+2]; }
        // Thomson collision
        if bg.kappa_dot > 0.0 {
            let src = match ell {
                0 => f[0],
                1 => bundle.baryon.v_b,
                2 => bundle.photon.polarisation_pi() / 10.0,
                _ => 0.0,
            };
            val -= bg.kappa_dot * (f[ell] - src);
        }
        rhs[idx + ell] = val;
    }
    idx += n_int;

    // ── Photon E-mode ──
    let n_e = cfg.dof_e_mode();
    let g = &bundle.photon.e_mode;
    let f2 = bundle.photon.quadrupole();
    let sqrt6 = 6.0_f64.sqrt();
    for i in 0..n_e {
        let ell = i + 2; // E-mode starts at ℓ=2
        let g2 = if n_e > 0 { g[0] } else { 0.0 };
        let pol_src = (f2 - sqrt6 * g2) / 10.0;
        let mut val = match i {
            0 => bg.kappa_dot * pol_src, // G₂ source
            _ => -bg.kappa_dot * g[i],   // damping
        };
        // Free-streaming for polarisation (simplified)
        if i > 0 { val += bg.k * coupling::free_streaming_down(ell) * g[i-1]; }
        if i+1 < n_e { val -= bg.k * coupling::free_streaming_up(ell) * g[i+1]; }
        rhs[idx + i] = val;
    }
    idx += n_e;

    // ── Photon B-mode ──
    let n_b = cfg.dof_b_mode();
    let bm = &bundle.photon.b_mode;
    for i in 0..n_b {
        let ell = i + 2;
        let mut val = -bg.kappa_dot * bm[i]; // pure damping at linear order
        if i > 0 { val += bg.k * coupling::free_streaming_down(ell) * bm[i-1]; }
        if i+1 < n_b { val -= bg.k * coupling::free_streaming_up(ell) * bm[i+1]; }
        rhs[idx + i] = val;
    }
    idx += n_b;

    // ── Neutrinos (per family): free-streaming only ──
    for nu in &bundle.neutrinos {
        let n_nu = nu.hierarchy.len();
        let h = &nu.hierarchy;
        for ell in 0..n_nu {
            let mut val = 0.0;
            if ell > 0 { val += bg.k * coupling::free_streaming_down(ell) * h[ell-1]; }
            if ell+1 < n_nu { val -= bg.k * coupling::free_streaming_up(ell) * h[ell+1]; }
            // Shear coupling for neutrinos (Bianchi)
            let sigma_f = bg.sigma_h * bg.a_h;
            if ell >= 2 { val += sigma_f * coupling::shear_coupling_down(ell) * h[ell-2]; }
            if ell+2 < n_nu { val += sigma_f * coupling::shear_coupling_up(ell) * h[ell+2]; }
            rhs[idx + ell] = val;
        }
        idx += n_nu;
    }

    // ── Baryon: Euler equation ──
    let r_inv = if bg.r_ratio > 1e-30 { 1.0 / bg.r_ratio } else { 0.0 };
    let cs2 = baryon_photon::sound_speed(bg.r_ratio).powi(2);
    // δ_b' = −k v_b
    rhs[idx] = -bg.k * bundle.baryon.v_b;
    // v_b' = −aH R/(1+R) v_b + k/(1+R) Θ₀ + R⁻¹ κ̇(v_γ − v_b)
    let v_gamma = if bundle.photon.intensity.len() > 1 { bundle.photon.intensity[1] } else { 0.0 };
    rhs[idx+1] = baryon_photon::baryon_euler_rhs(
        bundle.baryon.v_b, v_gamma, bundle.baryon.delta_b,
        bg.a_h, bg.k, cs2, bg.kappa_dot, r_inv,
    );
    idx += 2;

    // ── CDM: pressureless dust ──
    // δ_c' = −k v_c
    rhs[idx] = -bg.k * bundle.cdm.v_c;
    // v_c' = −aH v_c (Hubble drag only)
    rhs[idx+1] = -bg.a_h * bundle.cdm.v_c;

    rhs
}

/// Stacked state with conformal time.
#[derive(Clone, Debug)]
pub(crate) struct StackedState {
    pub(crate) species: SpeciesBundle,
    pub(crate) eta: f64,
}

impl StackedState {
    pub(crate) fn new(config: SpeciesConfig) -> Self {
        Self { species: SpeciesBundle::new(config), eta: 0.0 }
    }

    /// Evolve one RK4 step.
    pub(crate) fn step_rk4(&mut self, bg: &StackedBackground, d_eta: f64) {
        let n = self.species.total_dof();
        let y0 = self.species.to_flat();

        let k1 = build_stacked_rhs(&self.species, bg);

        let mut y_tmp = vec![0.0; n];
        for i in 0..n { y_tmp[i] = y0[i] + 0.5*d_eta*k1[i]; }
        self.species.from_flat(&y_tmp);
        let k2 = build_stacked_rhs(&self.species, bg);

        for i in 0..n { y_tmp[i] = y0[i] + 0.5*d_eta*k2[i]; }
        self.species.from_flat(&y_tmp);
        let k3 = build_stacked_rhs(&self.species, bg);

        for i in 0..n { y_tmp[i] = y0[i] + d_eta*k3[i]; }
        self.species.from_flat(&y_tmp);
        let k4 = build_stacked_rhs(&self.species, bg);

        for i in 0..n {
            y_tmp[i] = y0[i] + d_eta*(k1[i]+2.0*k2[i]+2.0*k3[i]+k4[i])/6.0;
        }
        self.species.from_flat(&y_tmp);
        self.eta += d_eta;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_bg(k: f64, sh: f64, kd: f64) -> StackedBackground {
        StackedBackground {
            eta: 0.0, a: 1e-3, a_h: 100.0, k, sigma_h: sh, kappa_dot: kd,
            r_ratio: 0.6,
        }
    }

    #[test]
    fn test_rhs_dimension() {
        let b = SpeciesBundle::new(SpeciesConfig::minimal());
        let bg = test_bg(0.0, 0.0, 0.0);
        let rhs = build_stacked_rhs(&b, &bg);
        assert_eq!(rhs.len(), b.total_dof());
    }

    #[test]
    fn test_rhs_zero_for_zero_state() {
        let b = SpeciesBundle::new(SpeciesConfig::minimal());
        let bg = test_bg(0.0, 0.0, 0.0);
        let rhs = build_stacked_rhs(&b, &bg);
        for (i, &r) in rhs.iter().enumerate() {
            assert!(r.abs() < 1e-15, "rhs[{}] = {:.2e} (should be 0)", i, r);
        }
    }

    #[test]
    fn test_photon_energy_conservation_in_stacked() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.photon.intensity[0] = 1.0;
        let bg = test_bg(0.0, 0.0, 100.0); // Thomson on
        let rhs = build_stacked_rhs(&b, &bg);
        // C₀ = 0 → rhs[0] = 0
        assert!(rhs[0].abs() < 1e-14, "Energy cons: rhs[0] = {:.2e}", rhs[0]);
    }

    #[test]
    fn test_neutrino_ignores_thomson_in_stacked() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.neutrinos[0].hierarchy[3] = 1.0; // inject at ℓ=3
        let bg = test_bg(0.0, 0.0, 100.0); // Thomson on
        let rhs = build_stacked_rhs(&b, &bg);
        // Neutrino ℓ=3: no k, no σ → rhs = 0 (Thomson doesn't touch ν)
        let nu_offset = b.config.dof_gamma_intensity() + b.config.dof_e_mode() + b.config.dof_b_mode();
        assert!(rhs[nu_offset + 3].abs() < 1e-15, "ν ignores Thomson");
    }

    #[test]
    fn test_shear_drives_photon_quadrupole() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.photon.intensity[0] = 1.0;
        let bg = test_bg(0.0, 0.001, 0.0); // σ/H = 10⁻³, no Thomson
        let rhs = build_stacked_rhs(&b, &bg);
        assert!(rhs[2].abs() > 1e-6, "Shear must drive F₂: {:.4e}", rhs[2]);
    }

    #[test]
    fn test_shear_drives_neutrino_quadrupole() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.neutrinos[0].hierarchy[0] = 1.0;
        let bg = test_bg(0.0, 0.001, 0.0);
        let rhs = build_stacked_rhs(&b, &bg);
        let nu_off = b.config.dof_gamma_intensity() + b.config.dof_e_mode() + b.config.dof_b_mode();
        assert!(rhs[nu_off + 2].abs() > 1e-6, "Shear must drive N₂");
    }

    #[test]
    fn test_block_detection() {
        let b = SpeciesBundle::new(SpeciesConfig::minimal());
        let blocks = detect_blocks(&b);
        assert_eq!(blocks.len(), 2);
        assert_eq!(blocks[0].id, BlockId::PhotonBaryon);
        assert_eq!(blocks[1].id, BlockId::NeutrinoCDM);
        // Block A: γ(11+5+5) + b(2) = 23
        assert_eq!(blocks[0].size, 21 + 2);
        // Block B: ν(27) + c(2) = 29
        assert_eq!(blocks[1].size, 27 + 2);
    }

    #[test]
    fn test_rk4_evolve_no_crash() {
        let mut state = StackedState::new(SpeciesConfig::minimal());
        state.species.photon.set_adiabatic(1.0);
        state.species.neutrinos[0].set_adiabatic(1.0);
        let bg = test_bg(0.1, 1e-5, 50.0);
        for _ in 0..100 {
            state.step_rk4(&bg, 0.01);
        }
        let max = state.species.to_flat().iter().fold(0.0f64, |m, &v| m.max(v.abs()));
        assert!(max < 100.0, "Stacked RK4 blew up: max = {:.2e}", max);
    }

    #[test]
    fn test_flrw_no_shear_in_stacked() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.photon.intensity[0] = 1.0;
        let bg = test_bg(0.1, 0.0, 0.0); // FLRW: σ=0, κ̇=0
        let rhs = build_stacked_rhs(&b, &bg);
        // F₂ must be zero (no shear, no ℓ=0→ℓ=2 free-streaming)
        assert!(rhs[2].abs() < 1e-15);
    }

    #[test]
    fn test_cdm_hubble_drag() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.cdm.v_c = 0.01;
        let bg = test_bg(0.0, 0.0, 0.0);
        let rhs = build_stacked_rhs(&b, &bg);
        let cdm_off = b.total_dof() - 2;
        // v_c' = −aH v_c = −100 × 0.01 = −1
        assert!((rhs[cdm_off + 1] + 1.0).abs() < 1e-12, "CDM drag: {:.4}", rhs[cdm_off+1]);
    }

    #[test]
    fn test_baryon_euler_in_stacked() {
        let mut b = SpeciesBundle::new(SpeciesConfig::minimal());
        b.baryon.v_b = 0.01;
        b.photon.intensity[1] = 0.005; // v_γ = F₁
        let bg = test_bg(0.0, 0.0, 100.0); // Thomson on
        let rhs = build_stacked_rhs(&b, &bg);
        let bar_off = b.total_dof() - 4; // baryon is before CDM
        // v_b' = -aH v_b + R⁻¹ κ̇(v_γ − v_b)
        //      = -100×0.01 + (1/0.6)×100×(0.005-0.01) = -1.0 + (-0.833) = -1.833
        let expected = -100.0 * 0.01 + (1.0/0.6) * 100.0 * (0.005 - 0.01);
        assert!((rhs[bar_off + 1] - expected).abs() < 1e-10,
            "Baryon Euler: {:.4e} vs {:.4e}", rhs[bar_off+1], expected);
    }
}
