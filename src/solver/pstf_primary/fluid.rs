// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Fluid (CDM + Baryon) RHS (PR-023b, sub-track b of PR-023)
// ═══════════════════════════════════════════════════════════════════════
//
// Synchronous-gauge-equivalent fluid continuity + baryon Euler equations
// (pre-Thomson drag).  Thomson drag on baryon v_b is handled separately
// by PR-022b `pstf_thomson_collision` and composes additively.
//
// ## RHS (MB-95 `camb_rhs:483-487` equivalent, Thomson drag excluded)
//
//   dy[clxc] = −hdot / 2
//   dy[clxb] = −k · v_b − hdot / 2
//   dy[v_b]  = −ℋ · v_b + c_s²_b · k · clxb
//
// Thomson drag (`+opac·(3·Θ_1 − v_b)/r_b` on v_b) is in PR-022b —
// `pstf_thomson_collision` writes that into the same `dy[i_baryon_v_m0()]`
// slot.  Summed in PR-023c dispatcher.
//
// ## Synchronous gauge: v_c = 0
//
// In synchronous gauge the CDM velocity is fixed to zero by gauge choice.
// PR-023b does NOT write to `dy[i_cdm_v_m0()]` — that slot remains zero.
// Verified by `caveat_cdm_velocity_zero_at_sync_gauge` test.
//
// ## hdot wiring
//
// `hdot` is NOT in the state vector; it is derived algebraically by
// PR-023a `pstf_hdot()`.  The caller (test or PR-023c dispatcher)
// computes `hdot` first, then passes it via `FluidInputs.hdot`.
// Design choice: explicit passing > struct nesting (cleaner inter-
// sector dependency, easier to test in isolation).

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Fluid inputs
// ═══════════════════════════════════════════════════════════════════════

/// Inputs for the fluid (CDM + baryon) RHS contribution.
///
/// `hdot` is obtained from PR-023a `pstf_hdot(state, v_b, &metric_inputs,
/// layout)` by the caller.
#[derive(Clone, Copy, Debug)]
pub(crate) struct FluidInputs {
    /// Comoving wavenumber k [Mpc⁻¹].
    pub(crate) k: f64,
    /// Conformal Hubble ℋ = a·H [Mpc⁻¹].
    pub(crate) h_conformal: f64,
    /// Baryon sound-speed squared c_s²_b (dimensionless).
    pub(crate) cs2b: f64,
    /// hdot derived from PR-023a `pstf_hdot` [Mpc⁻¹].
    pub(crate) hdot: f64,
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Main fluid RHS
// ═══════════════════════════════════════════════════════════════════════

/// Accumulate CDM + baryon fluid RHS contributions into `dy`.
///
/// Writes:
///   dy[i_cdm_delta]    += −hdot / 2
///   dy[i_baryon_delta] += −k · v_b − hdot / 2
///   dy[i_baryon_v_m0]  += −ℋ · v_b + c_s²_b · k · clxb
///
/// Untouched:
///   - dy[i_cdm_v_m0]       (v_c = 0 at sync gauge, no evolution)
///   - metric sector         (PR-023a scope)
///   - photon/ν sectors      (PR-022a/b scope)
///   - polarization          (separate RHS, not in PR-023b)
///   - Bianchi reserve       (metric[2..=10])
///
/// Thomson drag on v_b is NOT added here — `pstf_thomson_collision`
/// (PR-022b) writes `+opac·(3·Θ_1 − v_b)/r_b` additively into the
/// same dy slot.  Composition happens in PR-023c dispatcher.
pub(crate) fn pstf_fluid_rhs(
    state: &[f64],
    dy: &mut [f64],
    inputs: &FluidInputs,
    layout: &PstfFlrwLayout,
) {
    assert_eq!(state.len(), layout.n_state,
        "state length {} != layout.n_state {}", state.len(), layout.n_state);
    assert_eq!(dy.len(), layout.n_state,
        "dy length {} != layout.n_state {}", dy.len(), layout.n_state);

    let clxb = state[layout.i_baryon_delta()];
    let v_b = state[layout.i_baryon_v_m0()];

    // ── CDM continuity: dy[clxc] = −hdot / 2 ───────────────────────
    dy[layout.i_cdm_delta()] += -inputs.hdot / 2.0;

    // ── Baryon continuity: dy[clxb] = −k · v_b − hdot / 2 ──────────
    dy[layout.i_baryon_delta()] += -inputs.k * v_b - inputs.hdot / 2.0;

    // ── Baryon Euler (Thomson drag excluded): ──────────────────────
    //   dy[v_b] = −ℋ · v_b + c_s²_b · k · clxb
    // Thomson drag `+opac·(3·Θ_1 − v_b)/r_b` is in PR-022b (additive).
    dy[layout.i_baryon_v_m0()] += -inputs.h_conformal * v_b
                                 + inputs.cs2b * inputs.k * clxb;

    // v_c = 0 at synchronous gauge → no write to dy[i_cdm_v_m0()]
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};
    use super::super::metric::{BackgroundQuantities, MetricInputs, pstf_hdot};

    /// Test fixture: layout + adiabatic IC state + representative bg + hdot.
    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, f64, FluidInputs) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic, &layout);
        // Inject baryon δ_b and v_b, metric state
        state[layout.i_baryon_delta()] = 0.002;
        state[layout.i_baryon_v_m0()] = 0.001;
        state[layout.i_metric_etak()] = -0.01 * 0.01;
        state[layout.i_metric_sigma()] = 1e-5;
        let v_b = state[layout.i_baryon_v_m0()];

        // Compute hdot via PR-023a (integration test pattern)
        let metric_inputs = MetricInputs {
            k: 0.01,
            bg: BackgroundQuantities::representative(),
        };
        let hdot = pstf_hdot(&state, v_b, &metric_inputs, &layout);

        let fluid_inputs = FluidInputs {
            k: 0.01,
            h_conformal: 1.0e-4,
            cs2b: 3.3e-10,  // representative c_s²_b for z~1100
            hdot,
        };
        (layout, state, v_b, fluid_inputs)
    }

    // ─── Identity tests (3) ─────────────────────────────────────────

    /// `clxcdot = -hdot/2` matches MB-95 `camb_rhs:483`.
    #[test]
    fn identity_clxcdot_matches_mb95() {
        let (layout, state, _v_b, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        let expected = -inputs.hdot / 2.0;
        let got = dy[layout.i_cdm_delta()];
        assert!((got - expected).abs() < 1e-18,
            "clxcdot: got {}, expected {}", got, expected);
    }

    /// `clxbdot = -k·v_b - hdot/2` matches MB-95 `camb_rhs:484`.
    #[test]
    fn identity_clxbdot_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        let expected = -inputs.k * v_b - inputs.hdot / 2.0;
        let got = dy[layout.i_baryon_delta()];
        assert!((got - expected).abs() < 1e-18,
            "clxbdot: got {}, expected {}", got, expected);
    }

    /// `vbdot = -ℋ·v_b + c_s²_b·k·clxb` matches MB-95 `camb_rhs:486-487`
    /// WITHOUT the Thomson drag term (drag is in PR-022b).
    #[test]
    fn identity_vbdot_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        let clxb = state[layout.i_baryon_delta()];
        let expected = -inputs.h_conformal * v_b + inputs.cs2b * inputs.k * clxb;
        let got = dy[layout.i_baryon_v_m0()];
        assert!((got - expected).abs() < 1e-18,
            "vbdot (pre-drag): got {}, expected {}", got, expected);
    }

    // ─── Limit tests (2) ────────────────────────────────────────────

    /// Zero state + zero hdot ⇒ all fluid dy entries are zero.
    #[test]
    fn limit_zero_state_trivial() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let state = vec![0.0; layout.n_state];
        let inputs = FluidInputs {
            k: 0.01,
            h_conformal: 1e-4,
            cs2b: 3.3e-10,
            hdot: 0.0,
        };
        let mut dy = vec![0.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        assert_eq!(dy[layout.i_cdm_delta()], 0.0);
        assert_eq!(dy[layout.i_baryon_delta()], 0.0);
        assert_eq!(dy[layout.i_baryon_v_m0()], 0.0);
    }

    /// hdot = 0 ⇒ clxcdot = 0 (CDM continuity trivial, since no v_c coupling).
    #[test]
    fn limit_zero_hdot_clxcdot_zero() {
        let (layout, state, _v_b, mut inputs) = test_fixture();
        inputs.hdot = 0.0;
        let mut dy = vec![0.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        assert_eq!(dy[layout.i_cdm_delta()], 0.0,
            "hdot=0 should give clxcdot=0");
    }

    // ─── Regression tests (2) — G2 full FLRW ────────────────────────

    /// Across k ∈ {1e-4, 1e-2, 1e-1}, fluid RHS matches MB-95 formulas
    /// bit-identically.
    #[test]
    fn regression_fluid_rhs_multiple_k() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let mut state = vec![0.0; layout.n_state];
        state[layout.i_baryon_delta()] = 0.002;
        state[layout.i_baryon_v_m0()] = 0.001;

        for &k in &[1e-4_f64, 1e-2, 1e-1] {
            let inputs = FluidInputs {
                k,
                h_conformal: 1e-4,
                cs2b: 3.3e-10,
                hdot: -2.5e-7,  // representative
            };
            let mut dy = vec![0.0; layout.n_state];
            pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

            let clxb = state[layout.i_baryon_delta()];
            let v_b = state[layout.i_baryon_v_m0()];

            let exp_clxc = -inputs.hdot / 2.0;
            let exp_clxb = -k * v_b - inputs.hdot / 2.0;
            let exp_vb = -inputs.h_conformal * v_b + inputs.cs2b * k * clxb;

            assert!((dy[layout.i_cdm_delta()] - exp_clxc).abs() < 1e-18,
                "k={}: clxcdot", k);
            assert!((dy[layout.i_baryon_delta()] - exp_clxb).abs() < 1e-18,
                "k={}: clxbdot", k);
            assert!((dy[layout.i_baryon_v_m0()] - exp_vb).abs() < 1e-18,
                "k={}: vbdot, got {}, expected {}",
                k, dy[layout.i_baryon_v_m0()], exp_vb);
        }
    }

    /// Integration test: use PR-023a `pstf_hdot` to compute hdot, feed to
    /// PR-023b fluid RHS, verify end-to-end matches MB-95.
    #[test]
    fn regression_with_pr023a_hdot() {
        let (layout, state, v_b, fluid_inputs) = test_fixture();
        let metric_inputs = MetricInputs {
            k: 0.01,
            bg: BackgroundQuantities::representative(),
        };

        // Recompute hdot to verify consistency with fluid_inputs.hdot
        let hdot_recomputed = pstf_hdot(&state, v_b, &metric_inputs, &layout);
        assert!((fluid_inputs.hdot - hdot_recomputed).abs() < 1e-18,
            "fluid_inputs.hdot and recomputed hdot must match: {} vs {}",
            fluid_inputs.hdot, hdot_recomputed);

        // Compute fluid dy and compare against MB-95 formulas with
        // the PR-023a-derived hdot
        let mut dy = vec![0.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &fluid_inputs, &layout);

        let clxb = state[layout.i_baryon_delta()];
        let exp_clxc = -hdot_recomputed / 2.0;
        let exp_clxb = -fluid_inputs.k * v_b - hdot_recomputed / 2.0;
        let exp_vb = -fluid_inputs.h_conformal * v_b
                   + fluid_inputs.cs2b * fluid_inputs.k * clxb;

        assert!((dy[layout.i_cdm_delta()] - exp_clxc).abs() < 1e-18);
        assert!((dy[layout.i_baryon_delta()] - exp_clxb).abs() < 1e-18);
        assert!((dy[layout.i_baryon_v_m0()] - exp_vb).abs() < 1e-18);
    }

    // ─── Channelwise tests (2) ──────────────────────────────────────

    /// Fluid RHS does NOT touch metric sector (including Bianchi reserve).
    #[test]
    fn channelwise_metric_untouched() {
        let (layout, state, _v_b, inputs) = test_fixture();
        let mut dy = vec![42.0; layout.n_state];  // sentinel
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        // Metric block: indices 0..=10
        for i in 0..11 {
            assert_eq!(dy[i], 42.0,
                "fluid RHS touched metric[{}]", i);
        }
    }

    /// Fluid RHS does NOT touch photon/neutrino sectors.
    #[test]
    fn channelwise_photon_nu_untouched() {
        let (layout, state, _v_b, inputs) = test_fixture();
        let mut dy = vec![42.0; layout.n_state];
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        // Photon intensity
        for ell in 0..=layout.ell_max_gamma {
            let idx = layout.i_photon_i_m0(ell);
            assert_eq!(dy[idx], 42.0,
                "fluid RHS touched photon ℓ={}", ell);
        }
        // Neutrino
        for ell in 0..=layout.ell_max_nu {
            let idx = layout.i_neutrino_m0(ell);
            assert_eq!(dy[idx], 42.0,
                "fluid RHS touched ν ℓ={}", ell);
        }
    }

    // ─── Caveat test (1) ────────────────────────────────────────────

    /// CDM velocity v_c is identically zero at synchronous gauge.
    /// PR-023b fluid RHS must NOT write to dy[i_cdm_v_m0()].
    #[test]
    fn caveat_cdm_velocity_zero_at_sync_gauge() {
        let (layout, state, _v_b, inputs) = test_fixture();
        let mut dy = vec![42.0; layout.n_state];  // sentinel
        pstf_fluid_rhs(&state, &mut dy, &inputs, &layout);

        let idx_vc = layout.i_cdm_v_m0();
        assert_eq!(dy[idx_vc], 42.0,
            "fluid RHS must not touch v_c (sync gauge); dy[idx_vc={}] = {}",
            idx_vc, dy[idx_vc]);
    }
}
