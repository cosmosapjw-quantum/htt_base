// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — LoS Source Function (PR-024a, sub-track a of PR-024)
// ═══════════════════════════════════════════════════════════════════════
//
// Extracts `SourceInputs` from PSTF state + dy at a single η snapshot,
// then calls SSOT helpers in `crate::source::registry` to assemble the
// CMB temperature source S(k,η) = SW + Doppler + quadrupole + E-mode.
//
// ## Bit-identical contract with MB-95 `production_source_v1`
//
// PR-024a routes through the same SSOT registry that MB-95
// `production_source_v1` uses (post PR-010 Stage B).  Given identical
// inputs (same state-level values — guaranteed by PR-021 IC and verified
// by PR-023c dispatcher), the source outputs are bit-identical.
//
// This is the PSTF-side mirror of `sync_gauge_camb.rs:315-404`.
//
// ## What is NOT here (PR-024 sub-track split)
//
// - Time integration (ODE evolve over η grid):  PR-024b
// - LoS integration (∫dη S·j_ℓ):                PR-024c
// - C_ℓ spectrum assembly:                       PR-024c
// - ISW term (deferred to post-pass FD on Φ, same as MB-95)
//
// ## Gauge-invariant potential Φ extraction (from MB-95 `L334`)
//
//   η_s   = etak / k
//   Φ     = η_s − ℋ · σ / k        (synchronous → Newtonian transform)
//   Ψ     = −Φ                     (ΛCDM, no anisotropic stress)
//   η_MB  = −2 · η_s
//   δ_γ   = 4 · Θ_0

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;
use super::metric::BackgroundQuantities;
use crate::source::registry::{
    SourceInputs, EmodeConvention,
    source_sw, source_doppler, source_polter_quad, source_emode,
};

// ═══════════════════════════════════════════════════════════════════════
//   §0.  PSTF-side SourceTerms (local — superset of MB-95 SourceTerms)
// ═══════════════════════════════════════════════════════════════════════
//
// `sync_gauge_camb::SourceTerms` in this snapshot only has 4 fields
// (s_total, s_sw, s_dop, s_quad).  PR-024a needs `s_e` and `polterdot`.
//
// Rather than modify the existing MB-95 struct (risky for existing
// call sites), we define a PSTF-specific superset here.  At PR-025 /
// PR-026 equivalence tests, conversion can be done via
// `PstfSourceTerms::as_mb95() -> SourceTerms` or similar helper.

/// Source function output for PSTF primary.
///
/// Superset of MB-95 `sync_gauge_camb::SourceTerms` with two extra
/// fields:
///   - `s_e`        : E-mode visibility source (CAMB `s_e`)
///   - `polterdot`  : polter_dot captured for post-pass FD → polter_ddot
///
/// These extras are needed for PR-024c LoS integration of E-mode
/// spectrum and for the PATCH 3B polter_ddot correction.
#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct PstfSourceTerms {
    pub(crate) s_total: f64,
    pub(crate) s_sw: f64,
    pub(crate) s_dop: f64,
    pub(crate) s_quad: f64,
    pub(crate) s_e: f64,
    pub(crate) polterdot: f64,
}

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Visibility snapshot
// ═══════════════════════════════════════════════════════════════════════

/// Visibility function at a single η snapshot.
///
/// Mirrors the subset of MB-95 `VisibilityResult` fields that
/// `production_source_v1` accesses: `vis_at[i]`, `dot_vis_at[i]`,
/// `ddot_vis_at[i]`.  Kept as a flat snapshot struct so PR-024a can be
/// tested without pulling in the full visibility machinery.
///
/// Field naming mirrors MB-95 `SourceInputs`:
///   g     = visibility function  κ̇·e^{-κ}
///   gdot  = d/dη · g
///   gddot = d²/dη² · g
#[derive(Clone, Copy, Debug)]
pub(crate) struct VisibilityAtSnap {
    pub(crate) g: f64,
    pub(crate) gdot: f64,
    pub(crate) gddot: f64,
}

impl VisibilityAtSnap {
    /// Zero visibility (for limit/identity testing).
    pub(crate) fn zero() -> Self {
        Self { g: 0.0, gdot: 0.0, gddot: 0.0 }
    }

    /// Representative recombination-peak snapshot (z~1100).
    pub(crate) fn representative() -> Self {
        Self {
            g: 3e-3,        // peak of visibility function
            gdot: 0.0,      // at peak, g' = 0
            gddot: -1e-6,   // negative curvature at peak
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Extract SourceInputs from PSTF state + dy
// ═══════════════════════════════════════════════════════════════════════

/// Extract `SourceInputs` from PSTF state and dy at a single η snapshot.
///
/// Mirrors MB-95 `production_source_v1:320-382` logic:
///   - theta0, theta2 from photon intensity state
///   - e0, e2 from E-mode state (if pol enabled)
///   - vb, vbdot from baryon state/dy
///   - sigma, sigmadot from metric state/dy
///   - eta_s = etak/k, phi = eta_s − ℋ·σ/k, psi = −phi
///   - eta_mb = −2·eta_s, delta_g = 4·theta0
///   - phidot = 0 (production: ISW deferred to post-pass FD)
pub(crate) fn pstf_extract_source_inputs(
    state: &[f64],
    dy: &[f64],
    k: f64,
    bg: &BackgroundQuantities,
    vis: &VisibilityAtSnap,
    layout: &PstfFlrwLayout,
) -> SourceInputs {
    assert_eq!(state.len(), layout.n_state);
    assert_eq!(dy.len(), layout.n_state);
    assert!(k > 0.0, "k must be positive for source extraction");

    let theta0 = state[layout.i_photon_i_m0(0)];
    let theta2 = if layout.ell_max_gamma >= 2 {
        state[layout.i_photon_i_m0(2)]
    } else { 0.0 };

    // PSTF E-mode layout stores ℓ≥2 only (n_photon_e = (lg+1)²−4 excludes
    // ℓ=0,1 slots that are physically zero for scalar perturbations).
    // MB-95 retains an `e_mode(0)` slot but production (Polter convention)
    // does NOT use E_0: polter = 2·Θ_2/5 + 3·E_2/5.  So E_0 is
    // unconditionally 0 in PSTF extraction — bit-identical with MB-95
    // production source output.
    let e0 = 0.0;
    let e2 = if layout.has_pol() && layout.ell_max_gamma >= 2 {
        state[layout.i_photon_e_m0(2)]
    } else { 0.0 };

    let vb = state[layout.i_baryon_v_m0()];
    let vbdot = dy[layout.i_baryon_v_m0()];

    let sigma = state[layout.i_metric_sigma()];
    let sigmadot = dy[layout.i_metric_sigma()];

    // Gauge transform (MB-95 `L333-335`)
    let etak = state[layout.i_metric_etak()];
    let eta_s = etak / k;
    let phi = eta_s - bg.h_conformal * sigma / k;
    let eta_mb = -2.0 * eta_s;
    let delta_g = 4.0 * theta0;

    SourceInputs {
        theta0, theta2,
        e0, e2,
        vb, vbdot,
        sigma, sigmadot,
        phi,
        phidot: 0.0,     // production: ISW via post-processing FD
        psi: -phi,       // ΛCDM: Ψ = −Φ when π_aniso = 0
        eta_mb,
        delta_g,
        g: vis.g,
        gdot: vis.gdot,
        gddot: vis.gddot,
        k,
        has_pol: layout.has_pol(),
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Main source function
// ═══════════════════════════════════════════════════════════════════════

/// Compute the LoS source function `S(k,η)` at a single η snapshot.
///
/// Bit-identical contract with MB-95 `production_source_v1` when given
/// corresponding inputs.  Both route through `source::registry` SSOT.
///
/// Components (matching MB-95 L285-303):
///   SW   = g · (δ_γ/4 + 2φ + η_MB/2)
///   Dop  = [(σ+v_b)·g' + (σ̇+v̇_b)·g] / k
///   Quad = CAMB-style polter quadrupole (3B: polterddot deferred)
///   ISW  = 0 (post-pass FD, same as MB-95)
///   E    = g · polter (Polter convention, production default)
///
/// # Note on `polterdot`
/// `polterdot` is computed via SSOT `core::ssot::polter_dot(pigdot, e2dot, has_pol)`.
/// `pigdot = 4·dΘ_2/dη` is read from dy.
pub(crate) fn pstf_source_function(
    state: &[f64],
    dy: &[f64],
    k: f64,
    bg: &BackgroundQuantities,
    vis: &VisibilityAtSnap,
    layout: &PstfFlrwLayout,
) -> PstfSourceTerms {
    let inp = pstf_extract_source_inputs(state, dy, k, bg, vis, layout);

    // polterdot computation (mirror of MB-95 L348)
    let e2dot = if layout.has_pol() { dy[layout.i_photon_e_m0(2)] } else { 0.0 };
    let pigdot = if layout.ell_max_gamma >= 2 { 4.0 * dy[layout.i_photon_i_m0(2)] } else { 0.0 };
    let polterdot = crate::core::ssot::polter_dot(pigdot, e2dot, layout.has_pol());

    // SSOT-routed channel assembly (mirror of MB-95 L385-389)
    let s_sw = source_sw(&inp);
    let s_dop = source_doppler(&inp);
    let s_quad = source_polter_quad(&inp, polterdot);
    let s_e = source_emode(&inp, EmodeConvention::Polter);

    // ISW = 0 (post-pass FD, same as MB-95 L397)
    let s_isw = 0.0_f64;

    PstfSourceTerms {
        s_total: s_sw + s_dop + s_quad + s_isw,
        s_sw, s_dop, s_quad, s_e,
        polterdot,
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §4.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};

    /// Representative test fixture: IC state + injected metric/baryon +
    /// representative background + representative visibility.
    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, Vec<f64>, f64,
                          BackgroundQuantities, VisibilityAtSnap) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic, &layout);
        state[layout.i_baryon_delta()] = 0.002;
        state[layout.i_baryon_v_m0()] = 0.001;
        state[layout.i_metric_etak()] = -1e-4;
        state[layout.i_metric_sigma()] = 1e-5;

        // Representative dy (non-trivial values to exercise source formula)
        let mut dy = vec![0.0; layout.n_state];
        dy[layout.i_metric_sigma()] = -2e-7;     // sigmadot
        dy[layout.i_baryon_v_m0()] = -1e-6;      // vbdot
        dy[layout.i_photon_i_m0(2)] = 1e-8;      // dTheta_2 (for pigdot)
        if layout.has_pol() {
            dy[layout.i_photon_e_m0(2)] = 5e-9;  // dE_2
        }

        let k = 0.01;
        let bg = BackgroundQuantities::representative();
        let vis = VisibilityAtSnap::representative();
        (layout, state, dy, k, bg, vis)
    }

    // ─── Identity (3 tests) ─────────────────────────────────────────

    /// `phi = eta_s - ℋ·σ/k` matches MB-95 `L334`.
    #[test]
    fn identity_phi_extraction_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);

        let etak = state[layout.i_metric_etak()];
        let sigma = state[layout.i_metric_sigma()];
        let eta_s = etak / k;
        let expected = eta_s - bg.h_conformal * sigma / k;

        assert!((inp.phi - expected).abs() < 1e-18,
            "phi: got {}, expected {}", inp.phi, expected);
        // Ψ = −Φ in ΛCDM (no π_aniso)
        assert!((inp.psi - (-expected)).abs() < 1e-18,
            "psi = -phi: got {}, expected {}", inp.psi, -expected);
    }

    /// `eta_mb = −2·eta_s` matches MB-95 `L335`.
    #[test]
    fn identity_eta_mb_extraction_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);

        let etak = state[layout.i_metric_etak()];
        let expected = -2.0 * etak / k;
        assert!((inp.eta_mb - expected).abs() < 1e-18,
            "eta_mb: got {}, expected {}", inp.eta_mb, expected);
    }

    /// `delta_g = 4·Θ_0` matches MB-95 `L336`.
    #[test]
    fn identity_delta_g_extraction_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);

        let theta0 = state[layout.i_photon_i_m0(0)];
        let expected = 4.0 * theta0;
        assert!((inp.delta_g - expected).abs() < 1e-18,
            "delta_g: got {}, expected {}", inp.delta_g, expected);
    }

    // ─── Regression (4 tests) — G2 full FLRW ────────────────────────

    /// SW channel bit-identical with direct SSOT call.
    /// Since `pstf_source_function` routes through `source::registry::source_sw`,
    /// and MB-95 `production_source_v1` does the same, they produce identical
    /// values when given equivalent inputs.  This test verifies the routing.
    #[test]
    fn regression_source_sw_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);

        // Direct SSOT call with extracted inputs (same path MB-95 takes)
        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);
        let expected = source_sw(&inp);

        assert!((result.s_sw - expected).abs() < 1e-18,
            "s_sw: got {}, expected {}", result.s_sw, expected);
    }

    /// Doppler channel bit-identical with SSOT.
    #[test]
    fn regression_source_doppler_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);

        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);
        let expected = source_doppler(&inp);

        assert!((result.s_dop - expected).abs() < 1e-18,
            "s_dop: got {}, expected {}", result.s_dop, expected);
    }

    /// polter quadrupole channel bit-identical with SSOT.
    #[test]
    fn regression_source_polter_quad_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);

        // Recompute polterdot to match internal computation
        let e2dot = if layout.has_pol() { dy[layout.i_photon_e_m0(2)] } else { 0.0 };
        let pigdot = 4.0 * dy[layout.i_photon_i_m0(2)];
        let polterdot = crate::core::ssot::polter_dot(pigdot, e2dot, layout.has_pol());

        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);
        let expected = source_polter_quad(&inp, polterdot);

        assert!((result.s_quad - expected).abs() < 1e-18,
            "s_quad: got {}, expected {}", result.s_quad, expected);
    }

    /// s_total = s_sw + s_dop + s_quad (ISW = 0 deferred).
    /// This is the MB-95 `L400` formula bit-identical.
    #[test]
    fn regression_source_total_matches_mb95() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);

        let expected = result.s_sw + result.s_dop + result.s_quad;
        assert!((result.s_total - expected).abs() < 1e-18,
            "s_total: got {}, expected {}", result.s_total, expected);
    }

    // ─── Channelwise (2 tests) ──────────────────────────────────────

    /// ISW contribution to `s_total` is exactly 0 (deferred to post-pass FD).
    /// Same architectural decision as MB-95 `L397`.
    #[test]
    fn channelwise_source_no_isw() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);

        // phidot is 0 in extraction, so any ISW contribution would be 0 anyway.
        // But the architectural invariant is that s_total excludes ISW by construction.
        let no_isw_total = result.s_sw + result.s_dop + result.s_quad;
        assert!((result.s_total - no_isw_total).abs() < 1e-18,
            "s_total must equal s_sw + s_dop + s_quad (ISW = 0)");

        // Also verify inp.phidot = 0 (the mechanism by which ISW is zero even
        // if source_isw were called)
        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);
        assert_eq!(inp.phidot, 0.0,
            "phidot must be 0 in production extraction (ISW via FD post-pass)");
    }

    /// `polterdot` field in SourceTerms equals SSOT `polter_dot()` result.
    #[test]
    fn channelwise_polterdot_export() {
        let (layout, state, dy, k, bg, vis) = test_fixture();
        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);

        let e2dot = if layout.has_pol() { dy[layout.i_photon_e_m0(2)] } else { 0.0 };
        let pigdot = 4.0 * dy[layout.i_photon_i_m0(2)];
        let expected = crate::core::ssot::polter_dot(pigdot, e2dot, layout.has_pol());

        assert!((result.polterdot - expected).abs() < 1e-18,
            "polterdot export: got {}, expected {}",
            result.polterdot, expected);
    }

    // ─── Caveat (1 test) ────────────────────────────────────────────

    /// Pol disabled (ell_max_pol = 0): e0, e2, s_e all zero.
    #[test]
    fn caveat_pol_off_e_source_zero() {
        let layout = PstfFlrwLayout::new(16, 16, 0);  // pol OFF
        layout.validate();
        let ic = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic, &layout);
        state[layout.i_baryon_delta()] = 0.002;
        state[layout.i_baryon_v_m0()] = 0.001;
        state[layout.i_metric_etak()] = -1e-4;
        state[layout.i_metric_sigma()] = 1e-5;
        let dy = vec![0.0; layout.n_state];
        let k = 0.01;
        let bg = BackgroundQuantities::representative();
        let vis = VisibilityAtSnap::representative();

        let inp = pstf_extract_source_inputs(&state, &dy, k, &bg, &vis, &layout);
        assert_eq!(inp.e0, 0.0);
        assert_eq!(inp.e2, 0.0);
        assert!(!inp.has_pol, "has_pol must be false when ell_max_pol=0");

        let result = pstf_source_function(&state, &dy, k, &bg, &vis, &layout);
        assert_eq!(result.s_e, 0.0,
            "s_e must be 0 when polarization disabled, got {}", result.s_e);
    }
}
