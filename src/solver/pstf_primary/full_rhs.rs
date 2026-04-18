// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Full RHS Dispatcher (PR-023c, sub-track c of PR-023)
// ═══════════════════════════════════════════════════════════════════════
//
// Composes all PSTF primary sectors into a single RHS evaluation:
//   1. Free-streaming (PR-022a)  with metric coupling wired up
//   2. Thomson collision (PR-022b)
//   3. Metric (PR-023a)
//   4. Fluid (PR-023b)
//
// ## Composition pattern
//
// `pstf_free_streaming_rhs` uses assignment (`dy[idx] = ...`) at the
// slots it touches (photon intensity + neutrino).  The other three
// sectors use additive `+=`.  To avoid overwriting sector contributions:
//
//   1. dy is zero-initialized
//   2. Free-streaming is called FIRST (sets photon + ν slots via `=`)
//   3. Collision / metric / fluid are called in ANY order
//      (they accumulate into non-conflicting or already-set slots via `+=`)
//
// ## hdot compute-once
//
// Three sectors need `hdot` (free-streaming via `metric_monopole_source`,
// fluid via `clxcdot` / `clxbdot`).  `pstf_hdot` is called ONCE here
// and its value is reused.  This is not just efficiency — it guarantees
// numerical consistency (same hdot value feeds both sectors).
//
// ## Retrospective significance for PR-022a
//
// Before PR-023c, PR-022a was called with `RhsInputs.metric_monopole_source
// = 0.0` placeholder (G2 partial).  PR-023c wires the actual PR-023a
// `pstf_metric_monopole_source()` value in, closing PR-022a's G2 gap.
// The new test `regression_rhs_matches_mb95_full_path_with_metric` in
// `rhs_free.rs` (added by this PR) demonstrates the full-FLRW match.

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;
use super::rhs_free::{RhsInputs, pstf_free_streaming_rhs};
use super::collision::{CollisionInputs, FrameConvention, pstf_thomson_collision};
use super::metric::{BackgroundQuantities, MetricInputs, pstf_hdot, pstf_metric_rhs};
use super::fluid::{FluidInputs, pstf_fluid_rhs};

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Full RHS inputs
// ═══════════════════════════════════════════════════════════════════════

/// Superset of all sector-specific inputs.  The dispatcher extracts
/// sub-structs for each sector.
#[derive(Clone, Copy, Debug)]
pub(crate) struct FullRhsInputs {
    /// Comoving wavenumber [Mpc⁻¹]
    pub(crate) k: f64,
    /// Conformal time [Mpc]
    pub(crate) tau: f64,
    /// Background cosmology (ℋ, ρ_γ, ρ_ν, ρ_b)
    pub(crate) bg: BackgroundQuantities,
    /// Thomson opacity κ̇ [Mpc⁻¹]
    pub(crate) kappa_dot: f64,
    /// Baryon-photon ratio r_b = (3/4)·ρ_b/ρ_γ
    pub(crate) r_b: f64,
    /// Whether to include ℓ=2 E-mode polarization feedback in collision
    pub(crate) use_pol_feedback: bool,
    /// Thomson frame convention
    pub(crate) frame: FrameConvention,
    /// Baryon sound speed squared c_s²_b
    pub(crate) cs2b: f64,
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Dispatcher
// ═══════════════════════════════════════════════════════════════════════

/// Full PSTF primary RHS (free-streaming + collision + metric + fluid).
///
/// Zero-initializes `dy`, then calls sectors in the required order
/// (free-streaming first because it uses assignment at photon/ν slots).
///
/// `hdot` is computed ONCE via `pstf_hdot` and reused in both the
/// free-streaming metric source and the fluid continuity equations.
pub(crate) fn pstf_full_rhs(
    state: &[f64],
    dy: &mut [f64],
    inputs: &FullRhsInputs,
    layout: &PstfFlrwLayout,
) {
    assert_eq!(state.len(), layout.n_state,
        "state length {} != layout.n_state {}", state.len(), layout.n_state);
    assert_eq!(dy.len(), layout.n_state,
        "dy length {} != layout.n_state {}", dy.len(), layout.n_state);

    // ──── Step 1: zero-initialize dy ─────────────────────────────
    dy.fill(0.0);

    // ──── Step 2: read v_b (needed by metric + fluid sectors) ────
    let v_b = state[layout.i_baryon_v_m0()];

    // ──── Step 3: compute hdot ONCE via PR-023a ──────────────────
    let metric_inputs = MetricInputs {
        k: inputs.k,
        bg: inputs.bg,
    };
    let hdot = pstf_hdot(state, v_b, &metric_inputs, layout);
    let metric_monopole_source = -hdot / 6.0;

    // ──── Step 4: free-streaming FIRST (assignment-based) ────────
    // Wire PR-022a placeholder to the actual PR-023a-derived source.
    let rhs_inputs = RhsInputs {
        k: inputs.k,
        tau: inputs.tau,
        metric_monopole_source,
    };
    pstf_free_streaming_rhs(state, dy, &rhs_inputs, layout);

    // ──── Step 5: Thomson collision (additive) ───────────────────
    let collision_inputs = CollisionInputs {
        kappa_dot: inputs.kappa_dot,
        r_b: inputs.r_b,
        use_pol_feedback: inputs.use_pol_feedback,
        frame: inputs.frame,
    };
    pstf_thomson_collision(state, dy, &collision_inputs, layout);

    // ──── Step 6: metric RHS (additive, disjoint slots) ──────────
    pstf_metric_rhs(state, dy, v_b, &metric_inputs, layout);

    // ──── Step 7: fluid RHS (additive, disjoint slots except
    //            v_b which receives drag from collision in Step 5) ─
    let fluid_inputs = FluidInputs {
        k: inputs.k,
        h_conformal: inputs.bg.h_conformal,
        cs2b: inputs.cs2b,
        hdot,  // reuse from Step 3
    };
    pstf_fluid_rhs(state, dy, &fluid_inputs, layout);
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};

    /// Test fixture: layout + adiabatic IC + non-trivial metric + baryon state.
    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, FullRhsInputs) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic, &layout);
        state[layout.i_baryon_delta()] = 0.002;
        state[layout.i_baryon_v_m0()] = 0.001;
        state[layout.i_metric_etak()] = -1e-4;
        state[layout.i_metric_sigma()] = 1e-5;
        let inputs = FullRhsInputs {
            k: 0.01,
            tau: 100.0,
            bg: BackgroundQuantities::representative(),
            kappa_dot: 0.5,
            r_b: 0.6,
            use_pol_feedback: false,
            frame: FrameConvention::ElectronRestFrame,
            cs2b: 3.3e-10,
        };
        (layout, state, inputs)
    }

    // ─── Identity: dispatcher composes sectors correctly ────────────

    /// `pstf_full_rhs()` result equals sum of individual sector calls
    /// (with correct ordering & zero-init).
    #[test]
    fn identity_dispatcher_composes_all_sectors() {
        let (layout, state, inputs) = test_fixture();

        // Dispatcher result
        let mut dy_full = vec![0.0; layout.n_state];
        pstf_full_rhs(&state, &mut dy_full, &inputs, &layout);

        // Manual composition (same order as dispatcher)
        let v_b = state[layout.i_baryon_v_m0()];
        let metric_in = MetricInputs { k: inputs.k, bg: inputs.bg };
        let hdot = pstf_hdot(&state, v_b, &metric_in, &layout);

        let mut dy_manual = vec![0.0; layout.n_state];
        let rhs_in = RhsInputs {
            k: inputs.k, tau: inputs.tau,
            metric_monopole_source: -hdot / 6.0,
        };
        pstf_free_streaming_rhs(&state, &mut dy_manual, &rhs_in, &layout);

        let coll_in = CollisionInputs {
            kappa_dot: inputs.kappa_dot, r_b: inputs.r_b,
            use_pol_feedback: inputs.use_pol_feedback, frame: inputs.frame,
        };
        pstf_thomson_collision(&state, &mut dy_manual, &coll_in, &layout);
        pstf_metric_rhs(&state, &mut dy_manual, v_b, &metric_in, &layout);

        let fluid_in = FluidInputs {
            k: inputs.k, h_conformal: inputs.bg.h_conformal,
            cs2b: inputs.cs2b, hdot,
        };
        pstf_fluid_rhs(&state, &mut dy_manual, &fluid_in, &layout);

        // Verify bit-identical
        for i in 0..layout.n_state {
            assert_eq!(dy_full[i], dy_manual[i],
                "dispatcher[{}] = {} != manual {}",
                i, dy_full[i], dy_manual[i]);
        }
    }

    // ─── G2 full: dispatcher vs MB-95 camb_rhs end-to-end ───────────

    /// `pstf_full_rhs()` matches MB-95 `camb_rhs` formulas for photon
    /// ℓ=0/1/2/3/5/ℓ_max, metric (etakdot, sigmadot), and fluid
    /// (clxcdot, clxbdot, vbdot WITH Thomson drag) bit-identically.
    ///
    /// This is the PR-023c flagship G2 test — the first Phase 1 test
    /// covering ALL sectors in one comparison.
    #[test]
    fn regression_dispatcher_matches_mb95_full_path() {
        let (layout, state, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_full_rhs(&state, &mut dy, &inputs, &layout);

        let k = inputs.k;
        let tau = inputs.tau;
        let theta = |ell: usize| state[layout.i_photon_i_m0(ell)];
        let nu = |ell: usize| state[layout.i_neutrino_m0(ell)];
        let v_b = state[layout.i_baryon_v_m0()];
        let clxb = state[layout.i_baryon_delta()];
        let etak = state[layout.i_metric_etak()];
        let sigma = state[layout.i_metric_sigma()];
        let opac = inputs.kappa_dot;

        // Expected hdot from PR-023a
        let metric_in = MetricInputs { k, bg: inputs.bg };
        let hdot = pstf_hdot(&state, v_b, &metric_in, &layout);

        // ── Photon hierarchy (MB-95 `camb_rhs:491-535`) ─────────
        // ℓ=0: dΘ_0 = −k·Θ_1 − hdot/6
        let mb95_p0 = -k * theta(1) - hdot / 6.0;
        assert!((dy[layout.i_photon_i_m0(0)] - mb95_p0).abs() < 1e-13,
            "ℓ=0: {} vs {}", dy[layout.i_photon_i_m0(0)], mb95_p0);

        // ℓ=1: dΘ_1 = k/3·(Θ_0 − 2Θ_2) − opac·(Θ_1 − v_b/3)
        let mb95_p1 = k/3.0 * (theta(0) - 2.0*theta(2))
                    - opac * (theta(1) - v_b/3.0);
        assert!((dy[layout.i_photon_i_m0(1)] - mb95_p1).abs() < 1e-13,
            "ℓ=1: {} vs {}", dy[layout.i_photon_i_m0(1)], mb95_p1);

        // ℓ=2 (pol off): dΘ_2 = k/5·(2Θ_1 − 3Θ_3) − opac·Θ_2
        let mb95_p2 = k/5.0 * (2.0*theta(1) - 3.0*theta(3)) - opac * theta(2);
        assert!((dy[layout.i_photon_i_m0(2)] - mb95_p2).abs() < 1e-13,
            "ℓ=2: {} vs {}", dy[layout.i_photon_i_m0(2)], mb95_p2);

        // ℓ=3: dΘ_3 = k/7·(3Θ_2 − 4Θ_4) − opac·Θ_3
        let mb95_p3 = k/7.0 * (3.0*theta(2) - 4.0*theta(4)) - opac * theta(3);
        assert!((dy[layout.i_photon_i_m0(3)] - mb95_p3).abs() < 1e-13,
            "ℓ=3: {} vs {}", dy[layout.i_photon_i_m0(3)], mb95_p3);

        // ℓ=5: dΘ_5 = k/11·(5Θ_4 − 6Θ_6) − opac·Θ_5
        let mb95_p5 = k/11.0 * (5.0*theta(4) - 6.0*theta(6)) - opac * theta(5);
        assert!((dy[layout.i_photon_i_m0(5)] - mb95_p5).abs() < 1e-13,
            "ℓ=5: {} vs {}", dy[layout.i_photon_i_m0(5)], mb95_p5);

        // ℓ=ℓ_max: truncation + opac damping
        let lg = layout.ell_max_gamma;
        let mb95_plg = k * theta(lg-1) - ((lg+1) as f64)/tau * theta(lg)
                     - opac * theta(lg);
        assert!((dy[layout.i_photon_i_m0(lg)] - mb95_plg).abs() < 1e-13,
            "ℓ=lmax: {} vs {}", dy[layout.i_photon_i_m0(lg)], mb95_plg);

        // ── Neutrino ℓ=0 (MB-95 `camb_rhs:532`, same pattern) ────
        let mb95_n0 = -k * nu(1) - hdot / 6.0;
        assert!((dy[layout.i_neutrino_m0(0)] - mb95_n0).abs() < 1e-13,
            "ν ℓ=0: {} vs {}", dy[layout.i_neutrino_m0(0)], mb95_n0);

        // ── Metric (MB-95 `camb_rhs:462-481`) ─────────────────────
        let theta_1 = theta(1);
        let n_1 = nu(1);
        let theta_2 = theta(2);
        let n_2 = nu(2);
        let dgq = (4.0/3.0) * inputs.bg.grho_gamma * (4.0 * theta_1)
                + (4.0/3.0) * inputs.bg.grho_nu * (4.0 * n_1)
                + inputs.bg.grho_b * v_b;
        let etakdot_exp = dgq / 2.0;
        let dgs = inputs.bg.grho_gamma * (4.0 * theta_2)
                + inputs.bg.grho_nu * (4.0 * n_2);
        let sigmadot_exp = -2.0 * inputs.bg.h_conformal * sigma
                         - dgs / k + etak;
        assert!((dy[layout.i_metric_etak()] - etakdot_exp).abs() < 1e-18,
            "etakdot: {} vs {}",
            dy[layout.i_metric_etak()], etakdot_exp);
        assert!((dy[layout.i_metric_sigma()] - sigmadot_exp).abs() < 1e-16,
            "sigmadot: {} vs {}",
            dy[layout.i_metric_sigma()], sigmadot_exp);

        // ── Fluid (MB-95 `camb_rhs:483-487`) — drag INCLUDED ──────
        let clxcdot_exp = -hdot / 2.0;
        let clxbdot_exp = -k * v_b - hdot / 2.0;
        // Full vbdot includes Thomson drag from PR-022b
        let vbdot_exp = -inputs.bg.h_conformal * v_b
                      + inputs.cs2b * k * clxb
                      + opac * (3.0 * theta_1 - v_b) / inputs.r_b;
        assert!((dy[layout.i_cdm_delta()] - clxcdot_exp).abs() < 1e-18,
            "clxcdot: {} vs {}",
            dy[layout.i_cdm_delta()], clxcdot_exp);
        assert!((dy[layout.i_baryon_delta()] - clxbdot_exp).abs() < 1e-18,
            "clxbdot: {} vs {}",
            dy[layout.i_baryon_delta()], clxbdot_exp);
        assert!((dy[layout.i_baryon_v_m0()] - vbdot_exp).abs() < 1e-13,
            "vbdot (drag included): {} vs {}",
            dy[layout.i_baryon_v_m0()], vbdot_exp);
    }

    /// Same dispatcher vs MB-95 check across multiple k values.
    #[test]
    fn regression_dispatcher_multiple_k() {
        let (layout, state, inputs_base) = test_fixture();
        for &k in &[1e-4_f64, 1e-2, 1e-1] {
            let mut inputs = inputs_base;
            inputs.k = k;
            let mut dy = vec![0.0; layout.n_state];
            pstf_full_rhs(&state, &mut dy, &inputs, &layout);

            // Spot check on photon ℓ=1 (most sensitive)
            let metric_in = MetricInputs { k, bg: inputs.bg };
            let v_b = state[layout.i_baryon_v_m0()];
            let _hdot = pstf_hdot(&state, v_b, &metric_in, &layout);
            let theta_0 = state[layout.i_photon_i_m0(0)];
            let theta_1 = state[layout.i_photon_i_m0(1)];
            let theta_2 = state[layout.i_photon_i_m0(2)];
            let mb95_p1 = k/3.0 * (theta_0 - 2.0*theta_2)
                        - inputs.kappa_dot * (theta_1 - v_b/3.0);
            let got = dy[layout.i_photon_i_m0(1)];
            assert!((got - mb95_p1).abs() < 1e-13,
                "k={}: ℓ=1 {} vs MB-95 {}", k, got, mb95_p1);
        }
    }

    // ─── Limit: κ̇=0 eliminates all collision terms ───────────────

    /// With κ̇=0, photon ℓ=1 reduces to free-streaming + metric only
    /// (no drag, v_b slot receives only fluid vbdot, no Thomson drag).
    #[test]
    fn limit_zero_kappa_dot_free_plus_metric_only() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.kappa_dot = 0.0;
        let mut dy = vec![0.0; layout.n_state];
        pstf_full_rhs(&state, &mut dy, &inputs, &layout);

        // Photon ℓ=1: dΘ_1 = k/3·(Θ_0 − 2Θ_2) (no drag, no source on ℓ=1)
        let k = inputs.k;
        let theta_0 = state[layout.i_photon_i_m0(0)];
        let theta_2 = state[layout.i_photon_i_m0(2)];
        let expected = k/3.0 * (theta_0 - 2.0 * theta_2);
        let got = dy[layout.i_photon_i_m0(1)];
        assert!((got - expected).abs() < 1e-15,
            "κ̇=0 ℓ=1: {} vs {}", got, expected);

        // v_b: dy receives only fluid vbdot (no drag)
        let clxb = state[layout.i_baryon_delta()];
        let v_b = state[layout.i_baryon_v_m0()];
        let vbdot_exp = -inputs.bg.h_conformal * v_b
                      + inputs.cs2b * k * clxb;
        let got_vb = dy[layout.i_baryon_v_m0()];
        assert!((got_vb - vbdot_exp).abs() < 1e-18,
            "κ̇=0 v_b: {} vs {}", got_vb, vbdot_exp);
    }

    // ─── Caveat: dy is zero-initialized by dispatcher ────────────

    /// Pre-filled dy must be overwritten — dispatcher zero-inits.
    #[test]
    fn caveat_dispatcher_zero_inits_dy() {
        let (layout, state, inputs) = test_fixture();
        let mut dy_prefilled = vec![42.0; layout.n_state];
        pstf_full_rhs(&state, &mut dy_prefilled, &inputs, &layout);

        // After dispatcher, dy should reflect RHS values (42.0 erased)
        // Specifically slots untouched by any sector must be 0, not 42
        let idx_vc = layout.i_cdm_v_m0();
        assert_eq!(dy_prefilled[idx_vc], 0.0,
            "CDM v_c slot should be zero (no sector writes), got {}",
            dy_prefilled[idx_vc]);
        // Bianchi reserve
        for i in 2..11 {
            assert_eq!(dy_prefilled[i], 0.0,
                "Bianchi reserve metric[{}] should be zero, got {}",
                i, dy_prefilled[i]);
        }
    }

    // ─── Caveat: hdot is computed once (implicit via consistency) ─

    /// Free-streaming source and fluid both use the SAME hdot value.
    /// This test verifies via consistency: metric_monopole_source
    /// (wired into free-streaming) is consistent with clxcdot = −hdot/2
    /// (used in fluid).
    #[test]
    fn caveat_hdot_computed_once() {
        let (layout, state, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_full_rhs(&state, &mut dy, &inputs, &layout);

        let clxcdot = dy[layout.i_cdm_delta()];
        // clxcdot = −hdot/2 ⇒ hdot = −2 · clxcdot
        let implied_hdot = -2.0 * clxcdot;

        // Photon ℓ=0 contribution from metric = −hdot/6
        // ⇒ total dΘ_0 = −k·Θ_1 + (−hdot/6)
        // ⇒ implied source = dΘ_0 + k·Θ_1 = −hdot/6
        let k = inputs.k;
        let theta_1 = state[layout.i_photon_i_m0(1)];
        let implied_source = dy[layout.i_photon_i_m0(0)] + k * theta_1;
        let expected_source = -implied_hdot / 6.0;
        assert!((implied_source - expected_source).abs() < 1e-15,
            "hdot consistency: fluid implies hdot={}, source implies {}",
            implied_hdot, -6.0 * implied_source);
    }
}
