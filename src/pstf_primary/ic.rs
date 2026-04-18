// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Adiabatic Initial Conditions (PR-021)
// ═══════════════════════════════════════════════════════════════════════
//
// Standard ΛCDM adiabatic mode at early times (kτ ≪ 1), expressed in
// PSTF state variables.
//
// ## Scope (PR-021)
//
// This PR is restricted to the PHOTON and NEUTRINO sectors.  Fluid
// variables (δ_c, δ_b, v_b) are deferred to PR-023 (metric + fluid).
//
// The adiabatic regular series from Ma & Bertschinger (1995) §5 gives,
// for kτ ≪ 1 with ζ = 1 normalization:
//
//   Θ_0 = N_0 = 1/2         (= δ_γ / 4, δ_ν / 4)
//   Θ_1 = N_1 = k / (6·ℋ)   (photon/neutrino dipole)
//   Θ_ℓ = N_ℓ = 0   for ℓ ≥ 2
//   E_ℓ = B_ℓ = 0   for all ℓ      (adiabatic, no polarization)
//
// In PSTF FLRW-limit, we set the state-vector components to these same
// numerical values: the PSTF-to-MB-95 projection at FLRW limit is exact
// at the state-value level for the m=0 axisymmetric sector.
//
// ## Normalization strategy (pr-021-design.md §3.3)
//
// We do NOT attempt a full STF-to-spherical-harmonic normalization chain
// here.  Following the lesson from PR-020 (`flrw_norm_ratio_down`
// factor-9 failure), we keep state-level values identical to MB-95 and
// compare on PHYSICAL OBSERVABLES (δ_γ, v_γ) instead.  The observable
// projection is encoded in `PstfObservables::from_state`.
//
// Full normalization of higher multipoles and the complete PSTF↔MB-95
// equivalence chain is the subject of PR-025.

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  IC inputs and observables
// ═══════════════════════════════════════════════════════════════════════

/// Inputs required to generate the PSTF adiabatic IC.
///
/// Kept minimal: we need only `k` and `adotoa` at η_init.
/// No full `CambBackground` struct is required — see `pr-021-design.md §9`.
#[derive(Clone, Copy, Debug)]
pub(crate) struct PstfIcInputs {
    /// Wavenumber in Mpc⁻¹.
    pub(crate) k: f64,
    /// ℋ ≡ a·H at η_init (conformal Hubble rate, Mpc⁻¹).
    pub(crate) adotoa: f64,
    /// Curvature perturbation amplitude (default ζ = 1 for adiabatic).
    pub(crate) zeta: f64,
}

impl PstfIcInputs {
    /// Default adiabatic IC inputs at the standard ζ = 1 normalization.
    pub(crate) fn default_adiabatic(k: f64, adotoa: f64) -> Self {
        Self { k, adotoa, zeta: 1.0 }
    }
}

/// Physical observables projected from the PSTF state vector at the
/// FLRW adiabatic initial time.
///
/// These are the quantities that CAN be compared against MB-95 without
/// worrying about the full PSTF normalization chain — they are gauge-
/// invariant density contrasts and bulk velocities at leading order.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) struct PstfObservables {
    /// Photon density contrast: δ_γ = 4 · I_0^{(γ)}(m=0).
    pub(crate) delta_gamma: f64,
    /// Photon bulk velocity: v_γ = 3 · I_1^{(γ)}(m=0) (tight-coupling limit).
    pub(crate) v_gamma: f64,
    /// Photon quadrupole: Θ_2 = I_2^{(γ)}(m=0) (≡ 0 at adiabatic init).
    pub(crate) quad_gamma: f64,
    /// Neutrino density contrast.
    pub(crate) delta_nu: f64,
    /// Neutrino bulk velocity.
    pub(crate) v_nu: f64,
}

impl PstfObservables {
    /// Project PSTF state vector to physical observables (FLRW limit).
    ///
    /// # FLRW-limit projection
    ///
    /// At the axisymmetric (m = 0) limit, the PSTF state values coincide
    /// with MB-95 brightness multipoles for the monopole and dipole:
    ///
    /// ```text
    ///     δ_γ   =  4 · I_0^{(γ)}(m=0)       (same as  4·Θ_0)
    ///     v_γ   =  3 · I_1^{(γ)}(m=0)       (same as  3·Θ_1)
    ///     Θ_2   =      I_2^{(γ)}(m=0)       (identical)
    /// ```
    ///
    /// Full validity across all ℓ and m requires the PSTF↔MB-95 equivalence
    /// proof — the subject of PR-025.  For PR-021 we use this projection
    /// only for ℓ ∈ {0, 1, 2}.
    pub(crate) fn from_state(
        state: &[f64],
        layout: &PstfFlrwLayout,
        _k: f64,
    ) -> Self {
        let delta_gamma = 4.0 * state[layout.i_photon_i_m0(0)];
        let v_gamma = 3.0 * state[layout.i_photon_i_m0(1)];
        let quad_gamma = if layout.ell_max_gamma >= 2 {
            state[layout.i_photon_i_m0(2)]
        } else {
            0.0
        };
        let delta_nu = 4.0 * state[layout.i_neutrino_m0(0)];
        let v_nu = 3.0 * state[layout.i_neutrino_m0(1)];
        Self {
            delta_gamma,
            v_gamma,
            quad_gamma,
            delta_nu,
            v_nu,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Adiabatic IC generator
// ═══════════════════════════════════════════════════════════════════════

/// Generate PSTF adiabatic initial conditions (FLRW limit).
///
/// Returns a state vector of length `layout.n_state`.  Only the photon
/// and neutrino m=0 components are written; fluid and metric sectors
/// remain zero (to be set by PR-023).
///
/// # Panics
/// If `inputs.adotoa ≤ 0` — ℋ must be positive at η_init.
///
/// # Regularization
/// None needed at ℋ > 0.  The dipole scales linearly in k and inversely
/// in ℋ, so very small k or very large ℋ simply gives a small dipole.
pub(crate) fn pstf_adiabatic_ic(
    inputs: &PstfIcInputs,
    layout: &PstfFlrwLayout,
) -> Vec<f64> {
    assert!(
        inputs.adotoa > 0.0,
        "pstf_adiabatic_ic: adotoa must be positive, got {}",
        inputs.adotoa
    );
    layout.validate();

    let mut state = vec![0.0_f64; layout.n_state];

    // Monopole:  I_0 = ζ/2  (ζ = 1 default → 1/2)
    let monopole = 0.5 * inputs.zeta;
    state[layout.i_photon_i_m0(0)] = monopole;
    state[layout.i_neutrino_m0(0)] = monopole;

    // Dipole:  I_1 = ζ · k / (6·ℋ)
    let dipole = inputs.zeta * inputs.k / (6.0 * inputs.adotoa);
    state[layout.i_photon_i_m0(1)] = dipole;
    state[layout.i_neutrino_m0(1)] = dipole;

    // Higher multipoles: left as 0 (adiabatic + no TCA closure yet).
    // Polarization (E_ℓ, B_ℓ) all zero at adiabatic init.
    // Fluid sector (baryon, cdm) untouched — PR-023.

    state
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    /// Test fixture matching MB-95 `test_adiabatic_ic` representative values.
    fn test_inputs() -> PstfIcInputs {
        PstfIcInputs::default_adiabatic(0.01, 500.0)
    }

    fn test_layout() -> PstfFlrwLayout {
        let lay = PstfFlrwLayout::new(16, 16, 16);
        lay.validate();
        lay
    }

    // ─── Identity tests (2) ─────────────────────────────────────────────

    /// PR-021 Identity #1: Photon monopole equals ζ/2.
    #[test]
    fn identity_photon_monopole_equals_half() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(&test_inputs(), &layout);
        let i_mono = layout.i_photon_i_m0(0);
        assert!((state[i_mono] - 0.5).abs() < 1e-15,
            "I_0^(γ) should be 0.5, got {}", state[i_mono]);
    }

    /// PR-021 Identity #2: Dipole is linear in k and inverse in ℋ.
    #[test]
    fn identity_photon_dipole_proportional_to_k_over_h() {
        let layout = test_layout();
        let k1 = 0.01; let h1 = 500.0;
        let s1 = pstf_adiabatic_ic(&PstfIcInputs::default_adiabatic(k1, h1), &layout);
        let v1 = s1[layout.i_photon_i_m0(1)];

        // Double k → dipole doubles
        let s2 = pstf_adiabatic_ic(&PstfIcInputs::default_adiabatic(2.0*k1, h1), &layout);
        let v2 = s2[layout.i_photon_i_m0(1)];
        assert!((v2/v1 - 2.0).abs() < 1e-12,
            "Dipole should scale linearly with k: ratio = {}", v2/v1);

        // Double ℋ → dipole halves
        let s3 = pstf_adiabatic_ic(&PstfIcInputs::default_adiabatic(k1, 2.0*h1), &layout);
        let v3 = s3[layout.i_photon_i_m0(1)];
        assert!((v3/v1 - 0.5).abs() < 1e-12,
            "Dipole should scale as 1/ℋ: ratio = {}", v3/v1);
    }

    // ─── Limit tests (2) ─────────────────────────────────────────────────

    /// PR-021 Limit #1: At k = 0, the dipole vanishes (but monopole remains).
    #[test]
    fn limit_k_zero_dipole_vanishes() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(
            &PstfIcInputs::default_adiabatic(0.0, 500.0), &layout);
        let mono = state[layout.i_photon_i_m0(0)];
        let dipole = state[layout.i_photon_i_m0(1)];
        assert!((mono - 0.5).abs() < 1e-15,
            "Monopole should remain 0.5 at k=0, got {}", mono);
        assert!(dipole.abs() < 1e-15,
            "Dipole should vanish at k=0, got {}", dipole);
    }

    /// PR-021 Limit #2: In adiabatic mode, photon and neutrino monopole and
    /// dipole are identical (no isocurvature perturbation).
    #[test]
    fn limit_neutrino_matches_photon_adiabatic() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(&test_inputs(), &layout);
        for ell in 0..=1 {
            let g = state[layout.i_photon_i_m0(ell)];
            let n = state[layout.i_neutrino_m0(ell)];
            assert!((g - n).abs() < 1e-15,
                "Adiabatic mode: photon[{}]={} must equal neutrino[{}]={}",
                ell, g, ell, n);
        }
    }

    // ─── Channelwise test (1) ────────────────────────────────────────────

    /// PR-021 Channelwise: at adiabatic init, polarization (E_ℓ, B_ℓ) is
    /// zero for all ℓ — no polarization is sourced prior to Thomson scattering.
    #[test]
    fn channelwise_polarization_zero_at_init() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(&test_inputs(), &layout);
        for ell in 2..=layout.ell_max_gamma {
            let e = state[layout.i_photon_e_m0(ell)];
            let b = state[layout.i_photon_b_m0(ell)];
            assert!(e.abs() < 1e-15, "E_{} = {} should be 0", ell, e);
            assert!(b.abs() < 1e-15, "B_{} = {} should be 0", ell, b);
        }
    }

    // ─── Regression tests (2) — G2 FLRW gate evidence ───────────────────

    /// PR-021 G2 #1: Observable δ_γ matches MB-95 adiabatic value exactly.
    ///
    /// MB-95 `adiabatic_ic` (src/solver/sync_gauge_camb.rs:3303) sets
    /// Θ_0 = 1/2, so δ_γ = 4·Θ_0 = 2.0 at ζ = 1.
    ///
    /// PSTF projection `from_state().delta_gamma = 4 · I_0^{(γ)}(m=0)`
    /// with I_0^{(γ)}(m=0) = 1/2 gives 2.0 as well.  This must hold to
    /// machine precision since state-level values are identical.
    #[test]
    fn regression_delta_gamma_matches_mb95_adiabatic() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(&test_inputs(), &layout);
        let obs = PstfObservables::from_state(&state, &layout, 0.01);
        // MB-95 reference: δ_γ = 4 · 0.5 = 2.0
        let mb95_delta_gamma = 2.0;
        let rel = (obs.delta_gamma - mb95_delta_gamma).abs() / mb95_delta_gamma;
        assert!(rel < 1e-15,
            "δ_γ mismatch: PSTF = {}, MB-95 = {}, rel err = {:e}",
            obs.delta_gamma, mb95_delta_gamma, rel);
    }

    /// PR-021 G2 #2: Observable v_γ matches MB-95 adiabatic value.
    ///
    /// MB-95 sets Θ_1 = k/(6·ℋ), so v_γ = 3·Θ_1 = k/(2·ℋ).
    /// PSTF: v_γ = 3 · I_1^{(γ)}(m=0) = 3 · k/(6·ℋ) = k/(2·ℋ).
    #[test]
    fn regression_v_gamma_matches_mb95_adiabatic() {
        let layout = test_layout();
        let inputs = test_inputs();
        let state = pstf_adiabatic_ic(&inputs, &layout);
        let obs = PstfObservables::from_state(&state, &layout, inputs.k);
        // MB-95 reference: v_γ = k/(2·ℋ)
        let mb95_v_gamma = inputs.k / (2.0 * inputs.adotoa);
        let rel = (obs.v_gamma - mb95_v_gamma).abs() / mb95_v_gamma.abs();
        assert!(rel < 1e-15,
            "v_γ mismatch: PSTF = {}, MB-95 = {}, rel err = {:e}",
            obs.v_gamma, mb95_v_gamma, rel);
    }

    // ─── Caveat tests (2) ────────────────────────────────────────────────

    /// PR-021 Caveat #1: IC function does NOT write to fluid sectors.
    ///
    /// PSTF fluid variables (baryon, CDM) are deferred to PR-023.
    /// This PR's IC must leave those regions untouched (zero from
    /// initial `vec![0.0; n_state]`).
    #[test]
    fn caveat_fluid_sector_untouched_by_ic() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(&test_inputs(), &layout);
        // Baryon block: 4 DOF starting at baryon_start
        for i in 0..4 {
            let idx = layout.inner.baryon_start + i;
            assert!(state[idx] == 0.0,
                "baryon[{}] at index {} must remain 0, got {}", i, idx, state[idx]);
        }
        // CDM block: 4 DOF starting at cdm_start
        for i in 0..4 {
            let idx = layout.inner.cdm_start + i;
            assert!(state[idx] == 0.0,
                "cdm[{}] at index {} must remain 0, got {}", i, idx, state[idx]);
        }
        // Metric block: 11 DOF starting at metric_start=0
        for i in 0..11 {
            assert!(state[i] == 0.0,
                "metric[{}] must remain 0, got {}", i, state[i]);
        }
    }

    /// PR-021 Caveat #2: Higher multipoles (ℓ ≥ 2) for photon and neutrino
    /// are zero at adiabatic init.  The Θ_2 TCA closure value
    /// (≈ (32/45)·k·τ_c·v_b) is applied by PR-022, NOT here.
    #[test]
    fn caveat_higher_multipoles_zero() {
        let layout = test_layout();
        let state = pstf_adiabatic_ic(&test_inputs(), &layout);
        for ell in 2..=layout.ell_max_gamma {
            let g = state[layout.i_photon_i_m0(ell)];
            assert!(g.abs() < 1e-15,
                "Photon I_{}(m=0) must be 0 at IC, got {}", ell, g);
        }
        for ell in 2..=layout.ell_max_nu {
            let n = state[layout.i_neutrino_m0(ell)];
            assert!(n.abs() < 1e-15,
                "Neutrino I_{}(m=0) must be 0 at IC, got {}", ell, n);
        }
    }

    // ─── Validation test (defensive) ────────────────────────────────────

    /// Defensive: negative ℋ should panic.
    #[test]
    #[should_panic(expected = "adotoa must be positive")]
    fn validation_rejects_negative_adotoa() {
        let layout = test_layout();
        let bad = PstfIcInputs::default_adiabatic(0.01, -1.0);
        let _ = pstf_adiabatic_ic(&bad, &layout);
    }
}
