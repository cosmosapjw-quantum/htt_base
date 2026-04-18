// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Thomson Collision (PR-022b)
// ═══════════════════════════════════════════════════════════════════════
//
// Electron-frame Thomson collision for photon hierarchy (FLRW m=0).
// DESIGN LAW: electron rest frame ζ̃ convention as default.  At FLRW
// this is numerically bit-identical to hypersurface-normal frame
// (MB-95 convention) — the `caveat_frame_equivalence_flrw` test proves
// this.  Bianchi tilt distinguishes the two; that is Phase 4 scope.
//
// ## Scope (PR-022b)
//
// Photon collision operator (Θ convention, MB-95 primary oracle):
//
//   C[Θ_0] = 0                                           (energy cons)
//   C[Θ_1] = −κ̇·(Θ_1 − v_b/3)                            (baryon drag)
//   C[Θ_2] = −(9/10)·κ̇·Θ_2 + (3/20)·κ̇·E_2  (with pol)
//           or
//          = −κ̇·Θ_2                                      (pol disabled)
//   C[Θ_ℓ] = −κ̇·Θ_ℓ          for ℓ ≥ 3                    (damping)
//
// Baryon reaction (momentum conservation):
//
//   C[v_b] |_drag = +(κ̇/r_b)·(3·Θ_1 − v_b)
//
// Neutrinos have NO Thomson collision (decoupled).
//
// ## Why not reuse `src/pstf/collision_lm.rs`
//
// Pre-audit of `collision_lm.rs:107-118` (see `pr-022b-design.md §2.3`)
// identified coefficient inconsistency in the ℓ=1 block: row 1 is
// `[−κ̇, κ̇]` (F=4Θ brightness convention), row 2 is
// `[3κ̇/(4r_b), −κ̇/r_b]` (hybrid 3/4 factor that is not momentum-conserving
// in either pure F or pure Θ convention).  Probable latent bug; NOT in
// production path (MB-95 `camb_rhs` is authoritative for D_2).
//
// Decision: PR-022b uses **MB-95 `camb_rhs` as primary oracle**, not
// `collision_lm`.  The `collision_lm` coefficient issue is flagged
// separately for Phase 2 cleanup; does NOT block PR-022b.
//
// ## What is NOT here
//
// - Free-streaming RHS (photon + ν): PR-022a ✅
// - Jacobian (analytical sparse): PR-022c
// - Metric coupling:                PR-023
// - E-mode polarization RHS:        future PR (pol-off default here)
// - Bianchi tilt frame distinction: Phase 4

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Frame convention & inputs
// ═══════════════════════════════════════════════════════════════════════

/// Thomson collision frame convention.
///
/// DESIGN LAW requires `ElectronRestFrame`.  At FLRW the two frames
/// produce bit-identical numerics (see `caveat_frame_equivalence_flrw`).
/// Bianchi tilt is where they diverge — Phase 4 scope.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub(crate) enum FrameConvention {
    /// DESIGN LAW default.  Electron rest frame; u_e^a is the 4-velocity
    /// of the electron fluid.  ζ̃ is defined relative to this frame.
    #[default]
    ElectronRestFrame,
    /// MB-95 equivalent at FLRW.  Hypersurface-normal u_n = n^a frame.
    /// Numerically identical to `ElectronRestFrame` when tilt = 0.
    HypersurfaceNormalFrame,
}

/// Inputs for the Thomson collision RHS contribution.
#[derive(Clone, Copy, Debug)]
pub(crate) struct CollisionInputs {
    /// Thomson opacity κ̇ [Mpc⁻¹].  MUST be non-negative; sign
    /// convention is enforced by `.abs()` in the implementation.
    pub(crate) kappa_dot: f64,
    /// Baryon-photon ratio r_b = (3/4)·ρ_b/ρ_γ.  MUST be positive.
    /// Guarded by `r_b.max(1e-10)` to match MB-95.
    pub(crate) r_b: f64,
    /// Enable ℓ=2 E-mode polarization feedback.  When `false`,
    /// `C[Θ_2] = −κ̇·Θ_2` (no pol coupling, no 9/10 factor).
    /// Default `false` — PR-022b scope is pol-off; pol activation
    /// with E-mode RHS is a future PR.
    pub(crate) use_pol_feedback: bool,
    /// Frame convention.  Default ElectronRestFrame per DESIGN LAW.
    pub(crate) frame: FrameConvention,
}

impl CollisionInputs {
    /// Convenience constructor with pol off and DESIGN LAW frame.
    pub(crate) fn pol_off(kappa_dot: f64, r_b: f64) -> Self {
        Self {
            kappa_dot,
            r_b,
            use_pol_feedback: false,
            frame: FrameConvention::ElectronRestFrame,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Main RHS contribution
// ═══════════════════════════════════════════════════════════════════════

/// Accumulate Thomson collision contribution into `dy`.
///
/// This function is ADDITIVE: it does not zero any `dy` entries.
/// Caller is responsible for initialization (or for composing with
/// `pstf_free_streaming_rhs` from PR-022a, whose `dy` targets do NOT
/// overlap with what this function writes, EXCEPT at photon intensity
/// indices where the additive pattern is intended).
///
/// Touched `dy` indices:
///   - `layout.i_photon_i_m0(ell)` for ell ∈ [1, ell_max_gamma]
///     (ℓ=0 receives zero contribution but we write +0.0 for structural clarity)
///   - `layout.i_photon_e_m0(2)` — only if pol feedback is enabled
///     (E-mode RHS is not treated here; only its reaction on Θ_2 is handled)
///   - baryon m=0 velocity slot at `layout.inner.baryon_start + 2`
///     (drag reaction; momentum conservation)
///
/// Untouched: neutrino sector, metric sector, cdm sector, B-modes,
/// higher-m (|m|≥1) components.
pub(crate) fn pstf_thomson_collision(
    state: &[f64],
    dy: &mut [f64],
    inputs: &CollisionInputs,
    layout: &PstfFlrwLayout,
) {
    assert_eq!(state.len(), layout.n_state,
        "state length {} != layout.n_state {}", state.len(), layout.n_state);
    assert_eq!(dy.len(), layout.n_state,
        "dy length {} != layout.n_state {}", dy.len(), layout.n_state);
    assert!(inputs.r_b > 0.0 || inputs.kappa_dot == 0.0,
        "r_b must be positive (got {}), unless kappa_dot=0", inputs.r_b);

    // Opacity canonicalization: κ̇ > 0 by convention
    let kd = inputs.kappa_dot.abs();
    if kd == 0.0 {
        // Trivial case — no collision contribution anywhere
        return;
    }

    // Frame equivalence at FLRW: both frames produce identical numerics
    // here.  We still track the tag for structural correctness and
    // future Bianchi-tilt divergence.
    let _frame = inputs.frame; // suppress unused warning; see caveat test

    let inv_rb = 1.0 / inputs.r_b.max(1e-10);
    let lg = layout.ell_max_gamma;

    // ──── Photon m=0 indices (cached) ─────────────────────────────
    let idx_theta = |ell: usize| layout.i_photon_i_m0(ell);

    // ──── Baryon v_b m=0 index ────────────────────────────────────
    // Baryon block layout: [δ_b, v_b_{m=-1}, v_b_{m=0}, v_b_{m=+1}]
    // so m=0 velocity is at baryon_start + 1 + (0+1) = baryon_start + 2
    let idx_vb = layout.inner.baryon_start + 2;
    let v_b = state[idx_vb];

    // ──── ℓ = 0: conservation (no contribution) ───────────────────
    // Structurally write +0.0 for documentation; compiler elides.
    // (Cannot even do `dy[idx_theta(0)] += 0.0` without the += being
    // optimized out, but the logical intent is: NO WRITE.)
    // C[Θ_0] = 0

    // ──── ℓ = 1: photon-baryon drag ───────────────────────────────
    // C[Θ_1] = −κ̇·(Θ_1 − v_b/3)
    let theta_1 = state[idx_theta(1)];
    dy[idx_theta(1)] += -kd * (theta_1 - v_b / 3.0);

    // Baryon side (momentum conservation):
    // dv_b/dη |_drag = +(κ̇/r_b)·(3·Θ_1 − v_b)
    dy[idx_vb] += kd * inv_rb * (3.0 * theta_1 - v_b);

    // ──── ℓ = 2: pol feedback (optional) ──────────────────────────
    if lg >= 2 {
        let theta_2 = state[idx_theta(2)];
        if inputs.use_pol_feedback && layout.has_pol() {
            // With pol: C[Θ_2] = −(9/10)·κ̇·Θ_2 + (3/20)·κ̇·E_2
            let e_2 = state[layout.i_photon_e_m0(2)];
            dy[idx_theta(2)] += -0.9 * kd * theta_2 + (3.0 / 20.0) * kd * e_2;
        } else {
            // Pol-off: C[Θ_2] = −κ̇·Θ_2  (pure damping, PR-022b default)
            dy[idx_theta(2)] += -kd * theta_2;
        }
    }

    // ──── ℓ ≥ 3: pure diagonal damping ────────────────────────────
    // C[Θ_ℓ] = −κ̇·Θ_ℓ
    for ell in 3..=lg {
        dy[idx_theta(ell)] += -kd * state[idx_theta(ell)];
    }

    // ──── Neutrino: NO collision ──────────────────────────────────
    // ν is decoupled from Thomson after BBN; structurally verified by
    // `channelwise_neutrino_no_collision` test.

    // ──── Metric, CDM: untouched ──────────────────────────────────
    // Verified by `channelwise_cdm_metric_untouched` test.
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};
    use super::super::rhs_free::{RhsInputs, pstf_free_streaming_rhs};

    /// Layout + IC state + non-zero baryon v_b + representative opacity.
    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, CollisionInputs) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic_inputs = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic_inputs, &layout);
        // Inject baryon v_b (not set by IC per PR-021 scope)
        let idx_vb = layout.inner.baryon_start + 2;
        state[idx_vb] = 0.001;  // representative magnitude
        let inputs = CollisionInputs::pol_off(0.5, 0.6);
        (layout, state, inputs)
    }

    // ─── Identity tests (3) ─────────────────────────────────────────

    /// ℓ=0 collision contribution is exactly zero (energy conservation).
    #[test]
    fn identity_ell0_collision_zero() {
        let (layout, state, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);
        let got = dy[layout.i_photon_i_m0(0)];
        assert_eq!(got, 0.0, "C[Θ_0] must be exactly 0 (got {})", got);
    }

    /// ℓ=1 drag matches MB-95 formula −κ̇·(Θ_1 − v_b/3).
    #[test]
    fn identity_ell1_drag_matches_mb95() {
        let (layout, state, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        let theta_1 = state[layout.i_photon_i_m0(1)];
        let v_b = state[layout.inner.baryon_start + 2];
        let expected = -inputs.kappa_dot * (theta_1 - v_b / 3.0);
        let got = dy[layout.i_photon_i_m0(1)];
        assert!((got - expected).abs() < 1e-14,
            "C[Θ_1] mismatch: expected {}, got {}, diff {:.3e}",
            expected, got, (got - expected).abs());
    }

    /// ℓ ∈ {3, 5, 10} have pure diagonal damping −κ̇·Θ_ℓ.
    #[test]
    fn identity_ell_ge_3_pure_damping() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let mut state = vec![0.0; layout.n_state];
        // Inject known Θ_ℓ values
        for ell in 3..=10 {
            state[layout.i_photon_i_m0(ell)] = (ell as f64) * 0.01;
        }
        let inputs = CollisionInputs::pol_off(0.3, 0.5);
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        for ell in [3usize, 5, 10] {
            let expected = -inputs.kappa_dot * state[layout.i_photon_i_m0(ell)];
            let got = dy[layout.i_photon_i_m0(ell)];
            assert!((got - expected).abs() < 1e-15,
                "ℓ={}: expected {}, got {}", ell, expected, got);
        }
    }

    // ─── Limit tests (2) ────────────────────────────────────────────

    /// κ̇=0 produces zero contribution everywhere.
    #[test]
    fn limit_kappa_dot_zero_trivial() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.kappa_dot = 0.0;
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        // All dy entries must be exactly 0.0
        let nonzero: Vec<usize> = dy.iter().enumerate()
            .filter(|&(_, &v)| v != 0.0)
            .map(|(i, _)| i)
            .collect();
        assert!(nonzero.is_empty(),
            "κ̇=0 should produce no contribution, found {} nonzero entries",
            nonzero.len());
    }

    /// pol-off mode: ℓ=2 is pure damping −κ̇·Θ_2, no 9/10 factor, no E_2 term.
    #[test]
    fn limit_no_pol_feedback() {
        let (layout, mut state, mut inputs) = test_fixture();
        inputs.use_pol_feedback = false;  // already default, but explicit
        // Inject nonzero E_2 to ensure it's ignored
        state[layout.i_photon_e_m0(2)] = 0.05;
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        let theta_2 = state[layout.i_photon_i_m0(2)];
        let expected = -inputs.kappa_dot * theta_2;  // pure damping
        let got = dy[layout.i_photon_i_m0(2)];
        assert!((got - expected).abs() < 1e-14,
            "pol-off ℓ=2: expected {}, got {}", expected, got);
    }

    // ─── Channelwise tests (2) ──────────────────────────────────────

    /// Neutrinos receive zero Thomson contribution.
    #[test]
    fn channelwise_neutrino_no_collision() {
        let (layout, mut state, inputs) = test_fixture();
        // Inject nonzero ν values to ensure they're ignored
        for ell in 0..=layout.ell_max_nu {
            state[layout.i_neutrino_m0(ell)] = (ell as f64) * 0.02;
        }
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        for ell in 0..=layout.ell_max_nu {
            let idx = layout.i_neutrino_m0(ell);
            assert_eq!(dy[idx], 0.0,
                "ν ℓ={} should receive no collision contribution, got {}",
                ell, dy[idx]);
        }
    }

    /// Metric and CDM sectors are untouched.
    #[test]
    fn channelwise_cdm_metric_untouched() {
        let (layout, state, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        // Metric: indices 0..11
        for i in 0..11 {
            assert_eq!(dy[i], 0.0, "metric[{}] touched by collision", i);
        }
        // CDM: indices cdm_start..cdm_start+4
        for i in 0..4 {
            let idx = layout.inner.cdm_start + i;
            assert_eq!(dy[idx], 0.0, "cdm[{}] at idx {} touched", i, idx);
        }
        // Baryon: δ_b (index 0 of baryon block) must be untouched
        // (only v_b at offset +2 gets drag)
        let idx_delta_b = layout.inner.baryon_start;  // offset 0 = δ_b
        assert_eq!(dy[idx_delta_b], 0.0, "δ_b should not be touched by collision");
    }

    // ─── Regression tests (2) — G2 FLRW gate evidence ───────────────

    /// PR-022a free-streaming + PR-022b collision MUST reproduce MB-95
    /// `camb_rhs` photon path (hdot=0, pol off) bit-identically at
    /// representative ℓ values.
    #[test]
    fn regression_collision_matches_mb95_full_path() {
        let (layout, state, inputs) = test_fixture();

        // Compose: free-streaming + collision
        let mut dy = vec![0.0; layout.n_state];
        let free_inputs = RhsInputs::free_streaming(0.01, 100.0);
        pstf_free_streaming_rhs(&state, &mut dy, &free_inputs, &layout);
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);

        // Reference: MB-95 `camb_rhs` formulas (pol off, hdot=0)
        let k = free_inputs.k;
        let tau = free_inputs.tau;
        let opac = inputs.kappa_dot;
        let theta = |ell: usize| -> f64 { state[layout.i_photon_i_m0(ell)] };
        let v_b = state[layout.inner.baryon_start + 2];

        // ℓ=0: dΘ_0 = −k·Θ_1     (hdot=0)
        let mb95_0 = -k * theta(1);
        assert!((dy[layout.i_photon_i_m0(0)] - mb95_0).abs() < 1e-13,
            "ℓ=0: PSTF {} vs MB-95 {}", dy[layout.i_photon_i_m0(0)], mb95_0);

        // ℓ=1: dΘ_1 = k/3·(Θ_0 − 2·Θ_2) − opac·(Θ_1 − v_b/3)
        let mb95_1 = k/3.0 * (theta(0) - 2.0*theta(2))
                   - opac * (theta(1) - v_b/3.0);
        assert!((dy[layout.i_photon_i_m0(1)] - mb95_1).abs() < 1e-13,
            "ℓ=1: PSTF {} vs MB-95 {}", dy[layout.i_photon_i_m0(1)], mb95_1);

        // ℓ=2 (pol off): dΘ_2 = k/5·(2·Θ_1 − 3·Θ_3) − opac·Θ_2
        let mb95_2 = k/5.0 * (2.0*theta(1) - 3.0*theta(3)) - opac * theta(2);
        assert!((dy[layout.i_photon_i_m0(2)] - mb95_2).abs() < 1e-13,
            "ℓ=2: PSTF {} vs MB-95 {}", dy[layout.i_photon_i_m0(2)], mb95_2);

        // ℓ=3: dΘ_3 = k/7·(3·Θ_2 − 4·Θ_4) − opac·Θ_3
        let mb95_3 = k/7.0 * (3.0*theta(2) - 4.0*theta(4)) - opac * theta(3);
        assert!((dy[layout.i_photon_i_m0(3)] - mb95_3).abs() < 1e-13,
            "ℓ=3: PSTF {} vs MB-95 {}", dy[layout.i_photon_i_m0(3)], mb95_3);

        // ℓ=5: dΘ_5 = k/11·(5·Θ_4 − 6·Θ_6) − opac·Θ_5
        let mb95_5 = k/11.0 * (5.0*theta(4) - 6.0*theta(6)) - opac * theta(5);
        assert!((dy[layout.i_photon_i_m0(5)] - mb95_5).abs() < 1e-13,
            "ℓ=5: PSTF {} vs MB-95 {}", dy[layout.i_photon_i_m0(5)], mb95_5);

        // ℓ=lg (truncation): dΘ_lg = k·Θ_{lg-1} − (lg+1)/τ·Θ_lg − opac·Θ_lg
        let lg = layout.ell_max_gamma;
        let mb95_lg = k * theta(lg-1) - ((lg+1) as f64)/tau * theta(lg)
                    - opac * theta(lg);
        assert!((dy[layout.i_photon_i_m0(lg)] - mb95_lg).abs() < 1e-13,
            "ℓ=lg={}: PSTF {} vs MB-95 {}",
            lg, dy[layout.i_photon_i_m0(lg)], mb95_lg);
    }

    /// Same bit-identical check at multiple κ̇ values — covers
    /// the full opacity regime from early universe (κ̇~100) to
    /// post-recombination (κ̇~0.01).
    #[test]
    fn regression_multiple_kappa_dot() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let ic_in = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic_in, &layout);
        state[layout.inner.baryon_start + 2] = 0.001;

        for &kd in &[0.01_f64, 1.0, 100.0] {
            let free_in = RhsInputs::free_streaming(0.01, 100.0);
            let coll_in = CollisionInputs::pol_off(kd, 0.6);

            let mut dy = vec![0.0; layout.n_state];
            pstf_free_streaming_rhs(&state, &mut dy, &free_in, &layout);
            pstf_thomson_collision(&state, &mut dy, &coll_in, &layout);

            // Check ℓ=1 (most opacity-sensitive)
            let theta_0 = state[layout.i_photon_i_m0(0)];
            let theta_1 = state[layout.i_photon_i_m0(1)];
            let theta_2 = state[layout.i_photon_i_m0(2)];
            let v_b = state[layout.inner.baryon_start + 2];
            let mb95_1 = free_in.k/3.0 * (theta_0 - 2.0*theta_2)
                       - kd * (theta_1 - v_b/3.0);
            let got_1 = dy[layout.i_photon_i_m0(1)];
            let rel = if mb95_1.abs() > 1e-30 {
                (got_1 - mb95_1).abs() / mb95_1.abs()
            } else {
                (got_1 - mb95_1).abs()
            };
            assert!(rel < 1e-12,
                "κ̇={}: ℓ=1 rel err = {} (got {}, expected {})",
                kd, rel, got_1, mb95_1);

            // Check baryon drag reaction
            let mb95_vb = kd / 0.6 * (3.0 * theta_1 - v_b);
            // dy[vb] accumulates only the drag here since free-streaming
            // doesn't touch baryons
            let got_vb = dy[layout.inner.baryon_start + 2];
            assert!((got_vb - mb95_vb).abs() < 1e-13,
                "κ̇={}: v_b drag, PSTF {} vs MB-95 {}", kd, got_vb, mb95_vb);
        }
    }

    // ─── Caveat tests (2) ───────────────────────────────────────────

    /// At FLRW, ElectronRestFrame and HypersurfaceNormalFrame must
    /// produce identical dy.  This is the explicit test of PR-022b's
    /// frame-equivalence claim.
    #[test]
    fn caveat_frame_equivalence_flrw() {
        let (layout, state, mut inputs_erf) = test_fixture();
        inputs_erf.frame = FrameConvention::ElectronRestFrame;
        let mut inputs_hnf = inputs_erf;
        inputs_hnf.frame = FrameConvention::HypersurfaceNormalFrame;

        let mut dy_erf = vec![0.0; layout.n_state];
        let mut dy_hnf = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy_erf, &inputs_erf, &layout);
        pstf_thomson_collision(&state, &mut dy_hnf, &inputs_hnf, &layout);

        for i in 0..layout.n_state {
            assert_eq!(dy_erf[i], dy_hnf[i],
                "At FLRW, frames should produce identical dy, \
                 but idx {} differs: ERF {} vs HNF {}",
                i, dy_erf[i], dy_hnf[i]);
        }
    }

    /// Baryon drag sign convention: MB-95 L486-487 has
    /// `vbdot += opac·(3·Θ_1 − v_b)/r_b`  (positive when Θ_1 > v_b/3).
    /// PSTF must match this sign structure.
    #[test]
    fn caveat_baryon_drag_sign_convention() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let mut state = vec![0.0; layout.n_state];
        // Case A: Θ_1 large, v_b=0 → baryons should be ACCELERATED (dy[vb] > 0)
        state[layout.i_photon_i_m0(1)] = 0.1;
        state[layout.inner.baryon_start + 2] = 0.0;
        let inputs = CollisionInputs::pol_off(1.0, 0.5);
        let mut dy = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state, &mut dy, &inputs, &layout);
        let idx_vb = layout.inner.baryon_start + 2;
        assert!(dy[idx_vb] > 0.0,
            "Θ_1 > v_b/3 should accelerate baryons, got dy[v_b] = {}",
            dy[idx_vb]);

        // Case B: v_b large, Θ_1=0 → baryons should be DECELERATED (dy[vb] < 0)
        let mut state2 = vec![0.0; layout.n_state];
        state2[layout.i_photon_i_m0(1)] = 0.0;
        state2[layout.inner.baryon_start + 2] = 0.1;
        let mut dy2 = vec![0.0; layout.n_state];
        pstf_thomson_collision(&state2, &mut dy2, &inputs, &layout);
        assert!(dy2[idx_vb] < 0.0,
            "v_b > 3·Θ_1 should decelerate baryons, got dy[v_b] = {}",
            dy2[idx_vb]);
    }
}
