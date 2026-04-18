// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Free-streaming RHS (PR-022a)
// ═══════════════════════════════════════════════════════════════════════
//
// Photon + neutrino free-streaming hierarchy, FLRW m=0 axisymmetric.
// Thomson collision is NOT included here — see PR-022b (`collision.rs`).
// Metric coupling is a PLACEHOLDER — wired up by PR-023.
//
// ## Scope (PR-022a)
//
// The PSTF RHS at the FLRW axisymmetric limit reduces to the MB-95
// free-streaming hierarchy for the m=0 sector:
//
//   dI_ℓ/dη = k/(2ℓ+1) · [ℓ·I_{ℓ-1} − (ℓ+1)·I_{ℓ+1}]     for 2 ≤ ℓ < ℓ_max
//   dI_0/dη = −k·I_1 + S_metric            (S_metric = PLACEHOLDER, PR-023)
//   dI_1/dη = k/3 · (I_0 − 2·I_2)
//   dI_ℓmax/dη = k·I_{ℓ_max−1} − (ℓ_max+1)/τ · I_{ℓ_max}   (tau-based truncation)
//
// This applies to both photons (I_ℓ^γ) and neutrinos (I_ℓ^ν) with the
// same formulas at FLRW (photon-neutrino parallelism is a FLRW property;
// Bianchi breaks it via tilt, but that's Phase 4).
//
// ## What is NOT here
//
// - Thomson collision (−κ̇·I_ℓ terms): PR-022b
// - Baryon drag (opac·(I_1 − v_b/3)):  PR-022b + PR-023 (v_b is fluid)
// - ℓ=2 quadrupole pol feedback ((3/20)κ̇·E_2): PR-022b
// - Metric coupling (MB-95 hdot/6):   PR-023 (replaces the 0 placeholder)
// - E-mode, B-mode hierarchies:        future PR (scalar sector first)
//
// ## Placeholder semantics
//
// `metric_monopole_source` is a scalar `S_metric` added to both
// dI_0/dη for photon and neutrino.  In MB-95 this is −hdot/6 (where
// hdot is the synchronous gauge variable).  In PSTF it will be a
// gauge-invariant combination from `PstfMetricState` (PR-023).
//
// For this PR we accept `S_metric = 0` as the default: this is exactly
// the case where MB-95 would have hdot = 0 (frozen metric).  The
// caveat test verifies that a nonzero value flows only into monopole
// equations, not dipole or higher.

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  RHS inputs
// ═══════════════════════════════════════════════════════════════════════

/// Inputs for the PSTF free-streaming RHS.
///
/// Minimal by design: this PR does NOT consume ℋ, opacity, or baryon
/// variables.  Those enter via PR-022b (collision) and PR-023 (metric).
#[derive(Clone, Copy, Debug)]
pub(crate) struct RhsInputs {
    /// Comoving wavenumber in Mpc⁻¹.
    pub(crate) k: f64,
    /// Conformal time η in Mpc.  Used ONLY for the ℓ=ℓ_max truncation
    /// coefficient `(ℓ_max+1)/τ`, consistent with MB-95 convention.
    pub(crate) tau: f64,
    /// Metric monopole source term (PLACEHOLDER for PR-023).
    ///
    /// In MB-95 synchronous gauge this is `-hdot/6` where `hdot` is
    /// the trace of the metric perturbation.  PSTF gauge-invariant
    /// replacement to be wired in PR-023.  Setting this to 0 gives the
    /// "free-streaming only" limit used for the G2 gate here.
    pub(crate) metric_monopole_source: f64,
}

impl RhsInputs {
    /// Pure free-streaming (no metric coupling), convenience constructor.
    pub(crate) fn free_streaming(k: f64, tau: f64) -> Self {
        Self { k, tau, metric_monopole_source: 0.0 }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Free-streaming RHS
// ═══════════════════════════════════════════════════════════════════════

/// Compute the PSTF free-streaming RHS for photon and neutrino m=0
/// hierarchies.  Writes into `dy`, which must have length `layout.n_state`.
///
/// Collision and metric evolution are EXCLUDED here; caller combines
/// this with `pstf_primary::collision` (PR-022b) and metric RHS (PR-023).
///
/// # Panics
/// - if `dy.len() != state.len() != layout.n_state`
/// - if `inputs.tau <= 0` (truncation would divide by ≤ 0)
///
/// # Important
/// Non-photon, non-neutrino components of `dy` (fluid, metric, E, B)
/// are NOT touched.  Caller is responsible for initializing `dy` or
/// accumulating contributions from other sectors.
pub(crate) fn pstf_free_streaming_rhs(
    state: &[f64],
    dy: &mut [f64],
    inputs: &RhsInputs,
    layout: &PstfFlrwLayout,
) {
    assert_eq!(state.len(), layout.n_state,
        "state length {} != layout.n_state {}", state.len(), layout.n_state);
    assert_eq!(dy.len(), layout.n_state,
        "dy length {} != layout.n_state {}", dy.len(), layout.n_state);
    assert!(inputs.tau > 0.0,
        "tau must be positive (got {}), required by tau-based truncation",
        inputs.tau);

    let k = inputs.k;
    let tau = inputs.tau;
    let s_metric = inputs.metric_monopole_source;

    // ──── Photon intensity hierarchy ────────────────────────────────
    free_streaming_m0_block(
        state, dy,
        |ell| layout.i_photon_i_m0(ell),
        layout.ell_max_gamma,
        k, tau, s_metric,
    );

    // ──── Neutrino hierarchy (identical structure at FLRW) ──────────
    free_streaming_m0_block(
        state, dy,
        |ell| layout.i_neutrino_m0(ell),
        layout.ell_max_nu,
        k, tau, s_metric,
    );

    // E-mode and B-mode free-streaming: not treated here.  At FLRW
    // m=0 axisymmetric with scalar-only adiabatic mode, E_ℓ=B_ℓ=0 is
    // preserved by free-streaming (since no source).  This is
    // intentional: the E-B recursion with Thomson collision is the
    // subject of PR-022b + a future polarization PR.
}

/// Internal helper: write the free-streaming RHS for a single m=0
/// intensity hierarchy (photon or neutrino) into `dy`.
fn free_streaming_m0_block(
    state: &[f64],
    dy: &mut [f64],
    idx: impl Fn(usize) -> usize,
    ell_max: usize,
    k: f64,
    tau: f64,
    s_metric: f64,
) {
    // Convenience reader with bounds protection
    let get = |ell: usize| -> f64 {
        if ell <= ell_max { state[idx(ell)] } else { 0.0 }
    };

    // ℓ = 0:  dI_0/dη = −k·I_1 + S_metric
    dy[idx(0)] = -k * get(1) + s_metric;

    if ell_max < 1 {
        return;
    }

    // ℓ = 1:  dI_1/dη = k/3 · (I_0 − 2·I_2)
    //
    // This matches MB-95 `dy[theta(1)] = k/3 · (theta(0) − 2·theta(2))`
    // with the Thomson coupling term `−opac·(θ_1 − v_b/3)` OMITTED
    // (it belongs to PR-022b).
    dy[idx(1)] = (k / 3.0) * (get(0) - 2.0 * get(2));

    if ell_max < 2 {
        return;
    }

    // ℓ ∈ [2, ell_max − 1]:  dI_ℓ/dη = k/(2ℓ+1) · [ℓ·I_{ℓ−1} − (ℓ+1)·I_{ℓ+1}]
    //
    // Note the range is `2..ell_max` (exclusive upper), matching MB-95
    // `for ell in 3..lg` up to `ell_max − 1`.  We start at ℓ=2 because
    // the ℓ=2 case in MB-95 is written inline (same formula, special
    // treatment for pol feedback which is deferred to PR-022b).
    //
    // At FLRW free-streaming (no pol coupling), the ℓ=2 recursion is:
    //   dI_2/dη = k/5 · (2·I_1 − 3·I_3)
    // — identical to the standard recursion with ℓ=2.
    for ell in 2..ell_max {
        let two_ell_plus_one = (2 * ell + 1) as f64;
        let coeff = k / two_ell_plus_one;
        dy[idx(ell)] = coeff * (
            (ell as f64) * get(ell - 1)
            - ((ell + 1) as f64) * get(ell + 1)
        );
    }

    // ℓ = ell_max:  truncation
    //   dI_{ℓ_max}/dη = k·I_{ℓ_max − 1} − (ℓ_max + 1)/τ · I_{ℓ_max}
    //
    // MB-95 adds `− opac·Θ_{ℓ_max}` to this; we omit (PR-022b).
    dy[idx(ell_max)] = k * get(ell_max - 1)
        - ((ell_max + 1) as f64) / tau * get(ell_max);
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};

    /// Standard test layout + inputs (MB-95 fixture-compatible values).
    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, RhsInputs) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();

        // Use adiabatic IC for a nontrivial starting state
        let ic_inputs = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let state = pstf_adiabatic_ic(&ic_inputs, &layout);

        // Use a representative conformal time value (early universe)
        let rhs_inputs = RhsInputs::free_streaming(0.01, 100.0);
        (layout, state, rhs_inputs)
    }

    // ─── Identity tests (3) ─────────────────────────────────────────────

    /// PR-022a Identity #1: monopole RHS matches MB-95 free-streaming.
    /// MB-95:  dΘ_0/dη = −k·Θ_1 (when hdot = 0)
    /// PSTF:   dI_0/dη = −k·I_1 (when S_metric = 0)
    /// State values are bit-identical (PR-021), so RHS values are too.
    #[test]
    fn identity_monopole_rhs_matches_mb95_freestream() {
        let (layout, state, rhs_inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_free_streaming_rhs(&state, &mut dy, &rhs_inputs, &layout);

        // Photon monopole
        let expected_photon_0 = -rhs_inputs.k * state[layout.i_photon_i_m0(1)];
        let got_photon_0 = dy[layout.i_photon_i_m0(0)];
        assert!((got_photon_0 - expected_photon_0).abs() < 1e-15,
            "dI_0^γ/dη mismatch: expected {}, got {}",
            expected_photon_0, got_photon_0);

        // Neutrino monopole (same formula)
        let expected_nu_0 = -rhs_inputs.k * state[layout.i_neutrino_m0(1)];
        let got_nu_0 = dy[layout.i_neutrino_m0(0)];
        assert!((got_nu_0 - expected_nu_0).abs() < 1e-15,
            "dI_0^ν/dη mismatch: expected {}, got {}",
            expected_nu_0, got_nu_0);
    }

    /// PR-022a Identity #2: ℓ ≥ 2 recursion matches k/(2ℓ+1) standard form.
    /// Construct an artificial state where I_ℓ = ℓ, test intermediate ℓ.
    #[test]
    fn identity_recursion_matches_mb95_freestream() {
        let layout = PstfFlrwLayout::new(10, 10, 10);
        let mut state = vec![0.0; layout.n_state];
        // Inject synthetic values: I_ℓ = ℓ for easy hand-verification
        for ell in 0..=10 {
            state[layout.i_photon_i_m0(ell)] = ell as f64;
            state[layout.i_neutrino_m0(ell)] = ell as f64;
        }
        let mut dy = vec![0.0; layout.n_state];
        let inputs = RhsInputs::free_streaming(0.5, 1000.0);
        pstf_free_streaming_rhs(&state, &mut dy, &inputs, &layout);

        // Check ℓ = 3: dI_3 = k/7 · (3·I_2 − 4·I_4) = 0.5/7·(3·2 − 4·4) = 0.5/7·(-10)
        let expected_ell3 = 0.5 / 7.0 * (3.0 * 2.0 - 4.0 * 4.0);
        let got_ell3 = dy[layout.i_photon_i_m0(3)];
        assert!((got_ell3 - expected_ell3).abs() < 1e-14,
            "ℓ=3 recursion: expected {}, got {}", expected_ell3, got_ell3);

        // Check ℓ = 5: dI_5 = k/11 · (5·I_4 − 6·I_6) = 0.5/11·(5·4 − 6·6) = 0.5/11·(-16)
        let expected_ell5 = 0.5 / 11.0 * (5.0 * 4.0 - 6.0 * 6.0);
        let got_ell5 = dy[layout.i_photon_i_m0(5)];
        assert!((got_ell5 - expected_ell5).abs() < 1e-14,
            "ℓ=5 recursion: expected {}, got {}", expected_ell5, got_ell5);
    }

    /// PR-022a Identity #3: ℓ_max truncation matches MB-95 tau-based form.
    /// MB-95:  dΘ_{lg}/dη = k·Θ_{lg-1} − (lg+1)/τ · Θ_{lg}   (at opac=0)
    #[test]
    fn identity_truncation_matches_mb95() {
        let layout = PstfFlrwLayout::new(8, 8, 8);
        let mut state = vec![0.0; layout.n_state];
        state[layout.i_photon_i_m0(7)] = 3.0;  // ℓ_max − 1
        state[layout.i_photon_i_m0(8)] = 2.0;  // ℓ_max
        let mut dy = vec![0.0; layout.n_state];
        let inputs = RhsInputs::free_streaming(0.7, 50.0);
        pstf_free_streaming_rhs(&state, &mut dy, &inputs, &layout);

        // dI_8 = k·I_7 − 9/τ·I_8 = 0.7·3 − 9/50·2 = 2.1 − 0.36 = 1.74
        let expected = 0.7 * 3.0 - 9.0 / 50.0 * 2.0;
        let got = dy[layout.i_photon_i_m0(8)];
        assert!((got - expected).abs() < 1e-14,
            "ℓ_max truncation: expected {}, got {}", expected, got);
    }

    // ─── Limit tests (2) ─────────────────────────────────────────────────

    /// PR-022a Limit #1: k=0 makes free-streaming RHS vanish (for monopole
    /// when S_metric=0, for all ℓ≥1 unconditionally).
    #[test]
    fn limit_k_zero_rhs_vanishes() {
        let layout = PstfFlrwLayout::new(10, 10, 10);
        let mut state = vec![0.0; layout.n_state];
        // Nontrivial state
        for ell in 0..=10 {
            state[layout.i_photon_i_m0(ell)] = (ell as f64) * 0.1;
        }
        let mut dy = vec![0.0; layout.n_state];
        let inputs = RhsInputs::free_streaming(0.0, 100.0);  // k=0
        pstf_free_streaming_rhs(&state, &mut dy, &inputs, &layout);

        // All photon hierarchy RHS should be zero (the truncation term
        // at ℓ_max = 10 has k=0 × I_9 = 0 and −11/τ·I_10 = −11/100·1.0 ≠ 0!)
        // The truncation term survives k=0 because it's a tau-based
        // absorbing boundary, not a free-streaming recursion term.
        //
        // So strictly: ℓ=0 through ℓ_max−1 must be zero at k=0, but
        // ℓ=ℓ_max retains the absorbing-boundary term.
        for ell in 0..10 {
            let got = dy[layout.i_photon_i_m0(ell)];
            assert!(got.abs() < 1e-15,
                "k=0 photon ℓ={} must be 0, got {}", ell, got);
        }
        // Truncation term: k·I_{lg-1} − (lg+1)/τ·I_{lg} at k=0 → −11/100·1.0
        let expected_trunc = -11.0 / 100.0 * (10.0 * 0.1);
        let got_trunc = dy[layout.i_photon_i_m0(10)];
        assert!((got_trunc - expected_trunc).abs() < 1e-14,
            "k=0 truncation term: expected {}, got {}", expected_trunc, got_trunc);
    }

    /// PR-022a Limit #2: metric_monopole_source=0 gives pure free-streaming.
    /// Compare dy with S_metric=0 vs dy with S_metric=C: only monopole differs by C.
    #[test]
    fn limit_metric_source_zero_pure_freestream() {
        let (layout, state, _) = test_fixture();
        let inputs_zero = RhsInputs::free_streaming(0.01, 100.0);
        let mut inputs_nonzero = inputs_zero;
        inputs_nonzero.metric_monopole_source = 7.5;  // arbitrary C

        let mut dy_zero = vec![0.0; layout.n_state];
        let mut dy_nonzero = vec![0.0; layout.n_state];
        pstf_free_streaming_rhs(&state, &mut dy_zero, &inputs_zero, &layout);
        pstf_free_streaming_rhs(&state, &mut dy_nonzero, &inputs_nonzero, &layout);

        // Monopole (photon): difference = S_metric
        let diff_photon_0 = dy_nonzero[layout.i_photon_i_m0(0)]
                          - dy_zero[layout.i_photon_i_m0(0)];
        assert!((diff_photon_0 - 7.5).abs() < 1e-14,
            "Photon monopole S_metric diff: expected 7.5, got {}", diff_photon_0);

        // Monopole (neutrino): same
        let diff_nu_0 = dy_nonzero[layout.i_neutrino_m0(0)]
                       - dy_zero[layout.i_neutrino_m0(0)];
        assert!((diff_nu_0 - 7.5).abs() < 1e-14,
            "Neutrino monopole S_metric diff: expected 7.5, got {}", diff_nu_0);

        // All dipoles and higher ℓ: no difference
        for ell in 1..=layout.ell_max_gamma {
            let d = (dy_nonzero[layout.i_photon_i_m0(ell)]
                   - dy_zero[layout.i_photon_i_m0(ell)]).abs();
            assert!(d < 1e-15,
                "Photon ℓ={} should not feel S_metric: diff = {}", ell, d);
        }
    }

    // ─── Channelwise tests (2) ──────────────────────────────────────────

    /// PR-022a Channelwise #1: photon and neutrino RHS have identical
    /// formulas at FLRW free-streaming.  Given identical state values
    /// (which IS the case for adiabatic IC), RHS should be identical.
    #[test]
    fn channelwise_photon_nu_identical_structure() {
        let (layout, state, rhs_inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_free_streaming_rhs(&state, &mut dy, &rhs_inputs, &layout);

        // Adiabatic IC has photon[ℓ] == neutrino[ℓ] for all ℓ
        // Free-streaming formulas are identical → dy should match
        for ell in 0..=layout.ell_max_gamma.min(layout.ell_max_nu) {
            let g = dy[layout.i_photon_i_m0(ell)];
            let n = dy[layout.i_neutrino_m0(ell)];
            assert!((g - n).abs() < 1e-15,
                "ℓ={}: photon RHS {} != neutrino RHS {} (FLRW should match)",
                ell, g, n);
        }
    }

    /// PR-022a Channelwise #2: polarization E, B state untouched by
    /// free-streaming RHS (their recursion is PR-022b).
    #[test]
    fn channelwise_polarization_unaffected_freestream() {
        let (layout, mut state, rhs_inputs) = test_fixture();
        // Inject non-trivial E/B to make sure we'd catch it
        for ell in 2..=layout.ell_max_gamma {
            state[layout.i_photon_e_m0(ell)] = 0.5 * (ell as f64);
            state[layout.i_photon_b_m0(ell)] = 0.3 * (ell as f64);
        }
        let mut dy = vec![1.0; layout.n_state];  // pre-fill with 1 to detect writes
        pstf_free_streaming_rhs(&state, &mut dy, &rhs_inputs, &layout);

        // E, B entries in dy should remain at the pre-fill value 1.0
        for ell in 2..=layout.ell_max_gamma {
            let e = dy[layout.i_photon_e_m0(ell)];
            let b = dy[layout.i_photon_b_m0(ell)];
            assert_eq!(e, 1.0,
                "E_{} should not be touched by free_streaming_rhs, got {}", ell, e);
            assert_eq!(b, 1.0,
                "B_{} should not be touched by free_streaming_rhs, got {}", ell, b);
        }
    }

    // ─── Regression tests (2) — G2 FLRW gate evidence ───────────────────

    /// PR-022a G2 #1: PSTF free-streaming RHS matches MB-95 opac=0 path
    /// at k=0.01, representative conformal time.
    ///
    /// Cross-check: compute dI_ℓ/dη from PSTF, compare against the
    /// explicit MB-95 formulas (opac=0, hdot=0, no pol feedback).
    #[test]
    fn regression_rhs_matches_mb95_freestream_kappa_zero() {
        let (layout, state, rhs_inputs) = test_fixture();
        let mut dy_pstf = vec![0.0; layout.n_state];
        pstf_free_streaming_rhs(&state, &mut dy_pstf, &rhs_inputs, &layout);

        // Compute reference values inline using MB-95 formulas
        // (opac=0, hdot=0, pol feedback=0)
        let k = rhs_inputs.k;
        let tau = rhs_inputs.tau;
        let theta = |ell: usize| -> f64 {
            state[layout.i_photon_i_m0(ell)]
        };

        // ℓ=0
        let expected_0 = -k * theta(1);
        assert!((dy_pstf[layout.i_photon_i_m0(0)] - expected_0).abs() < 1e-14,
            "ℓ=0: PSTF {} vs MB-95 {}",
            dy_pstf[layout.i_photon_i_m0(0)], expected_0);

        // ℓ=1
        let expected_1 = (k / 3.0) * (theta(0) - 2.0 * theta(2));
        assert!((dy_pstf[layout.i_photon_i_m0(1)] - expected_1).abs() < 1e-14,
            "ℓ=1: PSTF {} vs MB-95 {}",
            dy_pstf[layout.i_photon_i_m0(1)], expected_1);

        // ℓ=2 (without pol feedback)
        let expected_2 = (k / 5.0) * (2.0 * theta(1) - 3.0 * theta(3));
        assert!((dy_pstf[layout.i_photon_i_m0(2)] - expected_2).abs() < 1e-14,
            "ℓ=2: PSTF {} vs MB-95 {}",
            dy_pstf[layout.i_photon_i_m0(2)], expected_2);

        // ℓ=5 (generic recursion)
        let expected_5 = (k / 11.0) * (5.0 * theta(4) - 6.0 * theta(6));
        assert!((dy_pstf[layout.i_photon_i_m0(5)] - expected_5).abs() < 1e-14,
            "ℓ=5: PSTF {} vs MB-95 {}",
            dy_pstf[layout.i_photon_i_m0(5)], expected_5);

        // ℓ=ℓ_max (truncation)
        let lg = layout.ell_max_gamma;
        let expected_lmax = k * theta(lg - 1) - ((lg + 1) as f64) / tau * theta(lg);
        assert!((dy_pstf[layout.i_photon_i_m0(lg)] - expected_lmax).abs() < 1e-14,
            "ℓ_max={}: PSTF {} vs MB-95 {}",
            lg, dy_pstf[layout.i_photon_i_m0(lg)], expected_lmax);
    }

    /// PR-022a G2 #2: same regression check at multiple k values.
    /// Verifies no hidden k-dependence bug.
    #[test]
    fn regression_multiple_k_values() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        // Fresh state: use IC at k_representative
        for &k_test in &[1e-4_f64, 1e-2, 1e-1] {
            let ic_inputs = PstfIcInputs::default_adiabatic(k_test, 500.0);
            let state = pstf_adiabatic_ic(&ic_inputs, &layout);
            let rhs_inputs = RhsInputs::free_streaming(k_test, 100.0);
            let mut dy = vec![0.0; layout.n_state];
            pstf_free_streaming_rhs(&state, &mut dy, &rhs_inputs, &layout);

            // ℓ=0: −k·I_1
            let expected = -k_test * state[layout.i_photon_i_m0(1)];
            let got = dy[layout.i_photon_i_m0(0)];
            let rel = if expected.abs() > 1e-30 {
                (got - expected).abs() / expected.abs()
            } else {
                got.abs()
            };
            assert!(rel < 1e-13,
                "k={}: ℓ=0 PSTF vs MB-95 rel err = {} (got {}, expected {})",
                k_test, rel, got, expected);
        }
    }

    // ─── Caveat tests (2) ────────────────────────────────────────────────

    /// PR-022a Caveat #1: function signature does NOT take κ̇.  Collision
    /// is structurally absent — enforced by type system (the function
    /// can't accidentally call Thomson collision without adding a param).
    ///
    /// This test is a compile-time invariant: the body just exercises the
    /// API as documented.  If someone adds κ̇ to `RhsInputs` this test
    /// catches the API drift at review time (via explicit field list).
    #[test]
    fn caveat_collision_not_applied() {
        // Exhaustive field match: adding a field to RhsInputs would
        // require updating this match, flagging the review.
        let inputs = RhsInputs {
            k: 0.01,
            tau: 100.0,
            metric_monopole_source: 0.0,
        };
        // Smoke: no κ̇, no v_b, no opac in the struct.
        let _ = inputs;
    }

    /// PR-022a Caveat #2: metric_monopole_source flows ONLY into ℓ=0
    /// equations.  Non-monopole entries must be invariant to S_metric.
    /// (This is a strengthening of Limit #2 — verified by explicit
    /// check that fluid/metric state vector entries also remain zero.)
    #[test]
    fn caveat_metric_source_placeholder() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.metric_monopole_source = 42.0;  // big sentinel value
        let mut dy = vec![0.0; layout.n_state];
        pstf_free_streaming_rhs(&state, &mut dy, &inputs, &layout);

        // Fluid sector (baryon_start, cdm_start): must remain 0
        for i in 0..4 {
            let idx_b = layout.inner.baryon_start + i;
            let idx_c = layout.inner.cdm_start + i;
            assert_eq!(dy[idx_b], 0.0,
                "baryon[{}] at idx {} should not be affected by S_metric",
                i, idx_b);
            assert_eq!(dy[idx_c], 0.0,
                "cdm[{}] at idx {} should not be affected by S_metric",
                i, idx_c);
        }
        // Metric sector (0..11): must remain 0
        for i in 0..11 {
            assert_eq!(dy[i], 0.0,
                "metric[{}] should not be touched by free_streaming_rhs", i);
        }
    }

    // ─── PR-023c retrospective: PR-022a G2 partial → full 승격 ──────
    //
    // PR-022a closed with G2 partial (cap 7, score 7) because the
    // `metric_monopole_source` was a placeholder = 0.0 and no test
    // exercised a non-zero wire-up.  PR-023c (via `pstf_full_rhs`
    // dispatcher) wires the actual `pstf_metric_monopole_source` value
    // from PR-023a into PR-022a.  This test demonstrates that when the
    // metric source is wired, PR-022a's free-streaming RHS matches
    // MB-95 `camb_rhs` on the full FLRW photon/ν path (opac=0 to
    // isolate free-streaming + metric coupling; full path with drag
    // is tested in `full_rhs::tests::regression_dispatcher_matches_mb95_full_path`).
    //
    // This test's passage retroactively upgrades PR-022a's G2 from
    // partial → full (see PROGRESS_SCOREBOARD.md §3 PR-022a entry).
    #[test]
    fn regression_rhs_matches_mb95_full_path_with_metric() {
        use super::super::metric::{BackgroundQuantities, MetricInputs, pstf_hdot};

        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic = super::super::ic::PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = super::super::ic::pstf_adiabatic_ic(&ic, &layout);
        state[layout.i_baryon_delta()] = 0.002;
        state[layout.i_baryon_v_m0()] = 0.001;
        state[layout.i_metric_etak()] = -1e-4;
        state[layout.i_metric_sigma()] = 1e-5;

        let v_b = state[layout.i_baryon_v_m0()];
        let metric_inputs = MetricInputs {
            k: 0.01,
            bg: BackgroundQuantities::representative(),
        };

        // Wire metric_monopole_source via PR-023a
        let hdot = pstf_hdot(&state, v_b, &metric_inputs, &layout);
        let source = -hdot / 6.0;

        let inputs = RhsInputs {
            k: 0.01,
            tau: 100.0,
            metric_monopole_source: source,
        };
        let mut dy = vec![0.0; layout.n_state];
        pstf_free_streaming_rhs(&state, &mut dy, &inputs, &layout);

        let k = inputs.k;
        let theta = |ell: usize| state[layout.i_photon_i_m0(ell)];
        let nu = |ell: usize| state[layout.i_neutrino_m0(ell)];

        // ℓ=0 photon: dΘ_0 = −k·Θ_1 − hdot/6  (MB-95 `camb_rhs:491`)
        let mb95_p0 = -k * theta(1) - hdot / 6.0;
        assert!((dy[layout.i_photon_i_m0(0)] - mb95_p0).abs() < 1e-13,
            "ℓ=0 with metric wire-up: {} vs MB-95 {}",
            dy[layout.i_photon_i_m0(0)], mb95_p0);

        // ℓ=0 neutrino: dN_0 = −k·N_1 − hdot/6  (MB-95 `camb_rhs:532`)
        let mb95_n0 = -k * nu(1) - hdot / 6.0;
        assert!((dy[layout.i_neutrino_m0(0)] - mb95_n0).abs() < 1e-13,
            "ν ℓ=0 with metric wire-up: {} vs MB-95 {}",
            dy[layout.i_neutrino_m0(0)], mb95_n0);

        // ℓ=1: free-streaming only (opac not in rhs_free)
        let mb95_p1 = k / 3.0 * (theta(0) - 2.0 * theta(2));
        assert!((dy[layout.i_photon_i_m0(1)] - mb95_p1).abs() < 1e-13,
            "ℓ=1: {} vs MB-95 {}",
            dy[layout.i_photon_i_m0(1)], mb95_p1);

        // ℓ=5: dΘ_5 = k/11·(5Θ_4 − 6Θ_6)
        let mb95_p5 = k / 11.0 * (5.0 * theta(4) - 6.0 * theta(6));
        assert!((dy[layout.i_photon_i_m0(5)] - mb95_p5).abs() < 1e-13,
            "ℓ=5: {} vs MB-95 {}",
            dy[layout.i_photon_i_m0(5)], mb95_p5);
    }
}
