// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Metric Sector (PR-023a, sub-track a of PR-023)
// ═══════════════════════════════════════════════════════════════════════
//
// 1+3 covariant scalar metric variables (FLRW m=0 axisymmetric).
// Synchronous-gauge equivalent: `etak` (= η·k, scalar metric
// perturbation × wavenumber) and `σ` (shear scalar).
//
// ## State layout in metric block (11 DOF reserved)
//
//   metric[0]    = etak   ← active (MB-95 equivalent to i_etak)
//   metric[1]    = σ      ← active (MB-95 equivalent to i_sigma)
//   metric[2..=10] = 0   ← reserved for Bianchi-I Z_{ab} tensor (Phase 4)
//
// ## RHS (MB-95 sync-gauge equivalent)
//
//   dgq = (16/3)·(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b        [momentum constraint]
//   etakdot = dgq / 2
//   dgs = 4·(ρ_γ·Θ_2 + ρ_ν·N_2)                        [anisotropic stress]
//   sigmadot = −2·ℋ·σ − dgs/k + etak
//   hdot = 2·k·σ − 6·etakdot/k      [DERIVED, not in state]
//
//   metric_monopole_source = −hdot/6 = −k·σ/3 + etakdot/k
//                          = photon/ν ℓ=0 coupling for PR-022a wire-up
//
// ## What is NOT here (PR-023 sub-track split)
//
// - Fluid RHS (clxc, clxb, v_b):     PR-023b
// - Full RHS composition + wire-up:  PR-023c (also retrospective
//   upgrade of PR-022a's G2 partial → full)
// - Bianchi Z_{ab} tensor coupling:  Phase 4
//
// ## Primary oracle
//
// MB-95 `camb_rhs` at `sync_gauge_camb.rs:462-481` — direct port of
// momentum constraint + σ evolution.  No alternative convention, no
// `collision_lm`-style bug suspects (sync-gauge metric is unambiguous).

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Background quantities
// ═══════════════════════════════════════════════════════════════════════

/// Background cosmological quantities entering the metric RHS.
///
/// All densities are `8πG·ρ·a²` equivalents (MB-95 `bg.grho_*`
/// convention), giving `[Mpc⁻²]` dimensions that combine with `k`
/// `[Mpc⁻¹]` naturally.
///
/// `h_conformal = ℋ = a·H` in `[Mpc⁻¹]`.
#[derive(Clone, Copy, Debug)]
pub(crate) struct BackgroundQuantities {
    /// ℋ = a·H [Mpc⁻¹]
    pub(crate) h_conformal: f64,
    /// grho_γ = 8πG·ρ_γ·a² [Mpc⁻²]
    pub(crate) grho_gamma: f64,
    /// grho_ν = 8πG·ρ_ν·a² [Mpc⁻²], massless ν only in PR-023a
    pub(crate) grho_nu: f64,
    /// grho_b = 8πG·ρ_b·a² [Mpc⁻²]
    pub(crate) grho_b: f64,
}

impl BackgroundQuantities {
    /// Zero background (for limit/identity testing).
    pub(crate) fn zero() -> Self {
        Self {
            h_conformal: 0.0,
            grho_gamma: 0.0,
            grho_nu: 0.0,
            grho_b: 0.0,
        }
    }

    /// Representative early-matter-era background (z ~ 1100, after BBN).
    /// Approximate values for adiabatic IC-era test fixtures.
    pub(crate) fn representative() -> Self {
        Self {
            h_conformal: 1.0e-4,  // Mpc⁻¹
            grho_gamma: 4.0e-8,
            grho_nu: 4.0e-8 * 0.68,  // N_eff·(7/8)·(4/11)^(4/3) factor
            grho_b: 1.0e-6,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Metric inputs
// ═══════════════════════════════════════════════════════════════════════

#[derive(Clone, Copy, Debug)]
pub(crate) struct MetricInputs {
    /// Comoving wavenumber [Mpc⁻¹].
    pub(crate) k: f64,
    /// Background quantities.
    pub(crate) bg: BackgroundQuantities,
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Helpers — dgq, dgs, hdot, monopole source
// ═══════════════════════════════════════════════════════════════════════

/// Compute the momentum constraint integrand:
///
///   dgq = (16/3)·(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b
///
/// Matches MB-95 `camb_rhs:466-469` with v_γ = 4·Θ_1 substituted:
///   dgq = (4/3)·ρ_γ · (4·Θ_1) + (4/3)·ρ_ν · (4·N_1) + ρ_b · v_b
///       = (16/3)·(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b
pub(crate) fn pstf_momentum_constraint_dgq(
    state: &[f64],
    v_b: f64,
    bg: &BackgroundQuantities,
    layout: &PstfFlrwLayout,
) -> f64 {
    let theta_1 = state[layout.i_photon_i_m0(1)];
    let n_1 = state[layout.i_neutrino_m0(1)];
    (16.0 / 3.0) * (bg.grho_gamma * theta_1 + bg.grho_nu * n_1)
        + bg.grho_b * v_b
}

/// Compute the anisotropic stress integrand:
///
///   dgs = 4·(ρ_γ·Θ_2 + ρ_ν·N_2)
///
/// Matches MB-95 `camb_rhs:477-479` with π_γ = 4·Θ_2, π_ν = 4·N_2:
///   dgs = ρ_γ · (4·Θ_2) + ρ_ν · (4·N_2) = 4·(ρ_γ·Θ_2 + ρ_ν·N_2)
fn pstf_anisotropic_stress_dgs(
    state: &[f64],
    bg: &BackgroundQuantities,
    layout: &PstfFlrwLayout,
) -> f64 {
    // Guard: ℓ_max ≥ 2 for quadrupole access (enforced by layout invariant)
    let theta_2 = if layout.ell_max_gamma >= 2 {
        state[layout.i_photon_i_m0(2)]
    } else { 0.0 };
    let n_2 = if layout.ell_max_nu >= 2 {
        state[layout.i_neutrino_m0(2)]
    } else { 0.0 };
    4.0 * (bg.grho_gamma * theta_2 + bg.grho_nu * n_2)
}

/// Compute hdot algebraically (not in state):
///
///   hdot = 2·k·σ − 6·etakdot/k = 2·k·σ − 3·dgq/k
///
/// This is the "raw" synchronous-gauge `hdot` used in MB-95
/// `camb_rhs:473`.  It appears in photon/ν ℓ=0 RHS as `−hdot/6`
/// (exported by `pstf_metric_monopole_source` below).
pub(crate) fn pstf_hdot(
    state: &[f64],
    v_b: f64,
    inputs: &MetricInputs,
    layout: &PstfFlrwLayout,
) -> f64 {
    let sigma = state[layout.i_metric_sigma()];
    let dgq = pstf_momentum_constraint_dgq(state, v_b, &inputs.bg, layout);
    2.0 * inputs.k * sigma - 3.0 * dgq / inputs.k
}

/// Metric monopole source for PR-022a wire-up.
///
/// Returns `−hdot/6`, which is the metric coupling term in
///   dΘ_0/dη = −k·Θ_1 + metric_monopole_source
///   dN_0/dη = −k·N_1 + metric_monopole_source
///
/// Analytic simplification:
///   −hdot/6 = −(2·k·σ − 3·dgq/k)/6 = −k·σ/3 + dgq/(2k) = −k·σ/3 + etakdot/k
pub(crate) fn pstf_metric_monopole_source(
    state: &[f64],
    v_b: f64,
    inputs: &MetricInputs,
    layout: &PstfFlrwLayout,
) -> f64 {
    -pstf_hdot(state, v_b, inputs, layout) / 6.0
}

// ═══════════════════════════════════════════════════════════════════════
//   §4.  Metric RHS
// ═══════════════════════════════════════════════════════════════════════

/// Accumulate metric RHS contributions into `dy`.
///
/// Writes:
///   dy[i_metric_etak]   += etakdot  = dgq / 2
///   dy[i_metric_sigma]  += sigmadot = −2·ℋ·σ − dgs/k + etak
///
/// Untouched:
///   - dy[i_metric_*] for indices 2..=10 (reserved for Bianchi Z_{ab})
///   - photon/ν/fluid/polarization sectors (those RHS are in PR-022a/b,
///     fluid RHS is PR-023b)
///
/// The metric coupling into photon/ν ℓ=0 (`−hdot/6`) is NOT applied
/// here — it is exported by `pstf_metric_monopole_source` and fed
/// into `RhsInputs::metric_monopole_source` by the caller (PR-023c
/// dispatcher).
pub(crate) fn pstf_metric_rhs(
    state: &[f64],
    dy: &mut [f64],
    v_b: f64,
    inputs: &MetricInputs,
    layout: &PstfFlrwLayout,
) {
    assert_eq!(state.len(), layout.n_state,
        "state length {} != layout.n_state {}", state.len(), layout.n_state);
    assert_eq!(dy.len(), layout.n_state,
        "dy length {} != layout.n_state {}", dy.len(), layout.n_state);
    assert!(inputs.k > 0.0,
        "k must be positive for metric RHS (got {})", inputs.k);

    let etak = state[layout.i_metric_etak()];
    let sigma = state[layout.i_metric_sigma()];

    // ── Momentum constraint: etakdot = dgq / 2 ───────────────────
    let dgq = pstf_momentum_constraint_dgq(state, v_b, &inputs.bg, layout);
    let etakdot = dgq / 2.0;
    dy[layout.i_metric_etak()] += etakdot;

    // ── Shear evolution: sigmadot = −2·ℋ·σ − dgs/k + etak ─────────
    let dgs = pstf_anisotropic_stress_dgs(state, &inputs.bg, layout);
    let sigmadot = -2.0 * inputs.bg.h_conformal * sigma - dgs / inputs.k + etak;
    dy[layout.i_metric_sigma()] += sigmadot;
}

// ═══════════════════════════════════════════════════════════════════════
//   §5.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};

    /// Test fixture: layout + adiabatic IC state + representative bg.
    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, f64, MetricInputs) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic, &layout);
        // Inject baryon v_b
        state[layout.inner.baryon_start + 2] = 0.001;
        let v_b = 0.001;
        // Inject metric state (MB-95 IC-style small values)
        state[layout.i_metric_etak()] = -0.01 * 0.01;  // ≈ −0.01·k
        state[layout.i_metric_sigma()] = 1e-5;
        let inputs = MetricInputs {
            k: 0.01,
            bg: BackgroundQuantities::representative(),
        };
        (layout, state, v_b, inputs)
    }

    // ─── Identity tests (3) ─────────────────────────────────────────

    /// `dgq` formula matches MB-95 `camb_rhs:466-469`:
    ///   dgq = (4/3)·ρ_γ·(4·Θ_1) + (4/3)·ρ_ν·(4·N_1) + ρ_b·v_b
    ///       = (16/3)·(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b
    #[test]
    fn identity_dgq_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let got = pstf_momentum_constraint_dgq(&state, v_b, &inputs.bg, &layout);

        let theta_1 = state[layout.i_photon_i_m0(1)];
        let n_1 = state[layout.i_neutrino_m0(1)];
        // Expected (MB-95 form verbatim)
        let v_gamma = 4.0 * theta_1;
        let v_nu = 4.0 * n_1;
        let expected = (4.0 / 3.0) * inputs.bg.grho_gamma * v_gamma
                     + (4.0 / 3.0) * inputs.bg.grho_nu * v_nu
                     + inputs.bg.grho_b * v_b;
        assert!((got - expected).abs() < 1e-18,
            "dgq: got {}, expected {}, diff {:.3e}",
            got, expected, (got - expected).abs());
    }

    /// `etakdot = dgq/2` matches MB-95 `camb_rhs:470`.
    #[test]
    fn identity_etakdot_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_metric_rhs(&state, &mut dy, v_b, &inputs, &layout);

        let dgq = pstf_momentum_constraint_dgq(&state, v_b, &inputs.bg, &layout);
        let expected = dgq / 2.0;
        let got = dy[layout.i_metric_etak()];
        assert!((got - expected).abs() < 1e-18,
            "etakdot: got {}, expected {}", got, expected);
    }

    /// `sigmadot` formula matches MB-95 `camb_rhs:480`.
    #[test]
    fn identity_sigmadot_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![0.0; layout.n_state];
        pstf_metric_rhs(&state, &mut dy, v_b, &inputs, &layout);

        let etak = state[layout.i_metric_etak()];
        let sigma = state[layout.i_metric_sigma()];
        let theta_2 = state[layout.i_photon_i_m0(2)];
        let n_2 = state[layout.i_neutrino_m0(2)];
        let pig = 4.0 * theta_2;
        let pir = 4.0 * n_2;
        let dgs = inputs.bg.grho_gamma * pig + inputs.bg.grho_nu * pir;
        let expected = -2.0 * inputs.bg.h_conformal * sigma
                     - dgs / inputs.k + etak;
        let got = dy[layout.i_metric_sigma()];
        assert!((got - expected).abs() < 1e-16,
            "sigmadot: got {}, expected {}", got, expected);
    }

    // ─── Limit tests (2) ────────────────────────────────────────────

    /// Zero state ⇒ all metric RHS entries are zero.
    #[test]
    fn limit_zero_state_trivial() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let state = vec![0.0; layout.n_state];
        let inputs = MetricInputs {
            k: 0.01,
            bg: BackgroundQuantities::representative(),
        };
        let mut dy = vec![0.0; layout.n_state];
        pstf_metric_rhs(&state, &mut dy, 0.0, &inputs, &layout);

        assert_eq!(dy[layout.i_metric_etak()], 0.0);
        assert_eq!(dy[layout.i_metric_sigma()], 0.0);
        assert_eq!(pstf_hdot(&state, 0.0, &inputs, &layout), 0.0);
    }

    /// No anisotropic stress (Θ_2 = N_2 = 0) ⇒ sigmadot = −2ℋ·σ + etak.
    /// If also etak = 0: sigmadot = −2ℋ·σ (pure damping).
    #[test]
    fn limit_no_anisotropic_stress_sigma_decays() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let mut state = vec![0.0; layout.n_state];
        state[layout.i_metric_sigma()] = 1e-5;
        // Θ_2 = N_2 = 0 by default zero state; etak = 0
        let inputs = MetricInputs {
            k: 0.01,
            bg: BackgroundQuantities::representative(),
        };
        let mut dy = vec![0.0; layout.n_state];
        pstf_metric_rhs(&state, &mut dy, 0.0, &inputs, &layout);

        let expected_sigmadot = -2.0 * inputs.bg.h_conformal * 1e-5;
        let got = dy[layout.i_metric_sigma()];
        assert!((got - expected_sigmadot).abs() < 1e-18,
            "no-anisotropic sigmadot: got {}, expected {}",
            got, expected_sigmadot);
    }

    // ─── Regression tests (3) — G2 full FLRW ────────────────────────

    /// `hdot` matches MB-95 `camb_rhs:473`:
    ///   hdot = 2·k·σ − 6·etakdot/k
    #[test]
    fn regression_hdot_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let got = pstf_hdot(&state, v_b, &inputs, &layout);

        let sigma = state[layout.i_metric_sigma()];
        let dgq = pstf_momentum_constraint_dgq(&state, v_b, &inputs.bg, &layout);
        let etakdot = dgq / 2.0;
        let expected = 2.0 * inputs.k * sigma - 6.0 * etakdot / inputs.k;
        let rel = if expected.abs() > 1e-20 {
            (got - expected).abs() / expected.abs()
        } else {
            (got - expected).abs()
        };
        assert!(rel < 1e-14,
            "hdot rel err {}: got {}, expected {}", rel, got, expected);
    }

    /// `pstf_metric_monopole_source` == `−hdot/6` bit-identical.
    /// This is the value PR-022a `metric_monopole_source` placeholder
    /// will be wired to in PR-023c.
    #[test]
    fn regression_monopole_source_matches_mb95() {
        let (layout, state, v_b, inputs) = test_fixture();
        let got = pstf_metric_monopole_source(&state, v_b, &inputs, &layout);
        let hdot = pstf_hdot(&state, v_b, &inputs, &layout);
        let expected = -hdot / 6.0;
        assert!((got - expected).abs() < 1e-18,
            "monopole source: got {}, expected {}", got, expected);
    }

    /// `etakdot`, `sigmadot` match MB-95 across multiple k values.
    /// Tight G2 evidence — inline MB-95 formula reconstruction.
    #[test]
    fn regression_metric_rhs_multiple_k() {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        let mut state = vec![0.0; layout.n_state];
        state[layout.i_metric_etak()] = -1e-4;
        state[layout.i_metric_sigma()] = 1e-5;
        state[layout.i_photon_i_m0(1)] = 0.0003;
        state[layout.i_photon_i_m0(2)] = 0.00001;
        state[layout.i_neutrino_m0(1)] = 0.0003;
        state[layout.i_neutrino_m0(2)] = 0.00001;
        state[layout.inner.baryon_start + 2] = 0.001;
        let v_b = 0.001;

        for &k in &[1e-4_f64, 1e-2, 1e-1] {
            let inputs = MetricInputs {
                k,
                bg: BackgroundQuantities::representative(),
            };
            let mut dy = vec![0.0; layout.n_state];
            pstf_metric_rhs(&state, &mut dy, v_b, &inputs, &layout);

            // Expected (MB-95 formulas inline)
            let theta_1 = state[layout.i_photon_i_m0(1)];
            let n_1 = state[layout.i_neutrino_m0(1)];
            let theta_2 = state[layout.i_photon_i_m0(2)];
            let n_2 = state[layout.i_neutrino_m0(2)];
            let etak = state[layout.i_metric_etak()];
            let sigma = state[layout.i_metric_sigma()];

            let dgq_exp = (4.0/3.0) * inputs.bg.grho_gamma * (4.0 * theta_1)
                        + (4.0/3.0) * inputs.bg.grho_nu * (4.0 * n_1)
                        + inputs.bg.grho_b * v_b;
            let etakdot_exp = dgq_exp / 2.0;
            let dgs_exp = inputs.bg.grho_gamma * (4.0 * theta_2)
                        + inputs.bg.grho_nu * (4.0 * n_2);
            let sigmadot_exp = -2.0 * inputs.bg.h_conformal * sigma
                             - dgs_exp / k + etak;

            let got_etakdot = dy[layout.i_metric_etak()];
            let got_sigmadot = dy[layout.i_metric_sigma()];
            assert!((got_etakdot - etakdot_exp).abs() < 1e-18,
                "k={}: etakdot got {} vs expected {}", k, got_etakdot, etakdot_exp);
            assert!((got_sigmadot - sigmadot_exp).abs() / sigmadot_exp.abs().max(1e-20) < 1e-13,
                "k={}: sigmadot got {} vs expected {}", k, got_sigmadot, sigmadot_exp);
        }
    }

    // ─── Channelwise (2) ────────────────────────────────────────────

    /// Metric RHS does NOT touch photon/neutrino sectors.
    #[test]
    fn channelwise_photon_nu_untouched() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![1.0; layout.n_state];  // pre-fill to detect writes
        pstf_metric_rhs(&state, &mut dy, v_b, &inputs, &layout);

        // Photon intensity sector
        for ell in 0..=layout.ell_max_gamma {
            let idx = layout.i_photon_i_m0(ell);
            assert_eq!(dy[idx], 1.0,
                "metric RHS should not touch photon ℓ={} at idx {}", ell, idx);
        }
        // Neutrino sector
        for ell in 0..=layout.ell_max_nu {
            let idx = layout.i_neutrino_m0(ell);
            assert_eq!(dy[idx], 1.0,
                "metric RHS should not touch ν ℓ={} at idx {}", ell, idx);
        }
    }

    /// Metric RHS does NOT touch fluid sectors (cdm, baryon).
    /// (Fluid RHS is PR-023b scope.)
    #[test]
    fn channelwise_fluid_untouched() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![1.0; layout.n_state];
        pstf_metric_rhs(&state, &mut dy, v_b, &inputs, &layout);

        // CDM sector
        for i in 0..4 {
            let idx = layout.inner.cdm_start + i;
            assert_eq!(dy[idx], 1.0,
                "metric RHS should not touch cdm[{}] at idx {}", i, idx);
        }
        // Baryon sector
        for i in 0..4 {
            let idx = layout.inner.baryon_start + i;
            assert_eq!(dy[idx], 1.0,
                "metric RHS should not touch baryon[{}] at idx {}", i, idx);
        }
    }

    // ─── Caveat (1) ────────────────────────────────────────────────

    /// Metric block indices 2..=10 are reserved for Bianchi and must
    /// not receive writes from PR-023a FLRW metric RHS.
    #[test]
    fn caveat_metric_block_reserved_for_bianchi() {
        let (layout, state, v_b, inputs) = test_fixture();
        let mut dy = vec![42.0; layout.n_state];  // sentinel
        pstf_metric_rhs(&state, &mut dy, v_b, &inputs, &layout);

        // metric[0] = etak ✓ touched (subject to += accumulation)
        // metric[1] = σ    ✓ touched
        // metric[2..=10]   ✗ must remain at sentinel 42.0
        for i in 2..11 {
            assert_eq!(dy[i], 42.0,
                "metric[{}] (Bianchi reserve) should not be touched, got {}",
                i, dy[i]);
        }
    }
}
