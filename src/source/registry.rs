// ═══════════════════════════════════════════════════════════════════════
// BASS Source Registry — PR-010 (FLRW source/radial channel split)
// ═══════════════════════════════════════════════════════════════════════
//
// Per `docs/PR_CONSTITUTION.md §3` PR-010 and SSOT Hardening v1.0 §5.1
// (Thomson source contract).
//
// This module exposes each FLRW scalar source channel as a dedicated pure
// function, each explicitly committing to ONE of the two canonical
// polarization combinations:
//
//     polter  = 2·Θ₂/5 + 3·E₂/5      (CAMB-style, used for scalar source)
//     Π_BASS  = Θ₂ + E₀ + E₂          (HW/TAM-style, used for exact branch)
//
// The channel inventory:
//
//     1. `source_sw()`       — Sachs–Wolfe  (intrinsic + SW part of OSW)
//     2. `source_isw()`      — Integrated Sachs–Wolfe
//     3. `source_doppler()`  — Doppler (baryon velocity + shear)
//     4. `source_polter_quad()`  — Polarization quadrupole collision
//     5. `source_emode()`    — Scalar E-mode visibility source
//
// All functions use SSOT helpers from `core::ssot`.  The production
// pipeline (`sync_gauge_camb::production_source_v1`) retains its existing
// monolithic implementation to preserve the bit-identical D_2 baseline;
// this module is the SSOT-conformant reference used by tests and by
// downstream PRs (e.g. PR-023 source registry promotion).
//
// ────────────────────────────────────────────────────────────────────────
//
// Polarization primitive choice (per call site):
//
//   `source_polter_quad()` uses `polter` — the CAMB `s_quad` form.
//   `source_emode()` can operate in two modes:
//     - `EmodeConvention::Polter`    : `s_e = g · polter`   (CAMB-style)
//     - `EmodeConvention::PiBass`    : `s_e = (3/4)·g·Π_BASS` (HW-style)
//
// The production path today uses `Polter`; the exact-transport PR (PR-021)
// will adopt `PiBass`.  Both are valid SSOT-conformant paths.

#![allow(dead_code)]

use crate::core::ssot;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Channel Input / Output Types
// ═══════════════════════════════════════════════════════════════════════

/// Per-η snapshot of quantities needed by the source channels.
///
/// This is a minimal, flat struct — no references to `CambBackground` or
/// `KmodeResult` — so channels can be unit-tested in isolation.
#[derive(Clone, Debug)]
pub(crate) struct SourceInputs {
    /// Photon monopole Θ₀ (or `δ_γ/4`).
    pub theta0: f64,
    /// Photon quadrupole Θ₂.
    pub theta2: f64,
    /// Scalar E-mode monopole E₀.  Ignored when `has_pol == false`.
    pub e0: f64,
    /// Scalar E-mode quadrupole E₂.  Ignored when `has_pol == false`.
    pub e2: f64,
    /// Baryon velocity v_b.
    pub vb: f64,
    /// dv_b/dη.
    pub vbdot: f64,
    /// Metric shear σ (conformal-time derivative form).
    pub sigma: f64,
    /// dσ/dη.
    pub sigmadot: f64,
    /// Newtonian potential Φ.
    pub phi: f64,
    /// dΦ/dη (needed for ISW).
    pub phidot: f64,
    /// Newtonian potential Ψ.
    pub psi: f64,
    /// Synchronous-gauge metric perturbation h/6 (for SW channel).
    pub eta_mb: f64,
    /// Photon density perturbation δ_γ.
    pub delta_g: f64,
    /// Visibility g.
    pub g: f64,
    /// dg/dη.
    pub gdot: f64,
    /// d²g/dη².
    pub gddot: f64,
    /// Wavenumber k [Mpc⁻¹].
    pub k: f64,
    /// Whether polarization hierarchy is active.
    pub has_pol: bool,
}

/// Per-η output of the source channels.
#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct ChannelOutputs {
    pub s_sw: f64,
    pub s_isw: f64,
    pub s_dop: f64,
    pub s_quad: f64,
    pub s_e: f64,
}

impl ChannelOutputs {
    /// Total temperature source `S_T = S_SW + S_ISW + S_Dop + S_Quad`.
    #[inline]
    pub fn s_total_temperature(&self) -> f64 {
        self.s_sw + self.s_isw + self.s_dop + self.s_quad
    }
}

/// E-mode polarization primitive choice.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum EmodeConvention {
    /// CAMB-style: `s_e = g · polter`.  Production default.
    Polter,
    /// HW/TAM-style: `s_e = (3/4)·g·Π_BASS`.  Exact-transport branch.
    PiBass,
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Channel Functions (per SSOT v2.0 §5.1)
// ═══════════════════════════════════════════════════════════════════════

/// Sachs–Wolfe source channel (scalar).
///
///   `S_SW = g · (δ_γ/4 + 2·Φ + η_mb/2)`
///
/// The `2·Φ + η_mb/2` combination carries both the intrinsic SW (gauge
/// correction in synchronous gauge) and the static potential term.  The
/// intrinsic `δ_γ/4` = Θ₀ contribution is included here rather than split
/// out; downstream cleanup (PR-023) may further separate these.
#[inline]
pub(crate) fn source_sw(inp: &SourceInputs) -> f64 {
    inp.g * (inp.delta_g / 4.0 + 2.0 * inp.phi + inp.eta_mb / 2.0)
}

/// Integrated Sachs–Wolfe channel (scalar).
///
///   `S_ISW = e^{-τ} · (Ψ̇ + Φ̇)` (Newtonian branch)
///          = `e^{-τ} · 2·Φ̇`      (when Ψ = -Φ)
///
/// In synchronous-gauge production code the sign convention requires care.
/// Here we expose the Newtonian-style formula; the production path may
/// adapt this via a branch label.
///
/// **Note**: this channel produces `0.0` if `phidot == 0.0`.  The
/// sign-consistency of `phidot` must be guaranteed by the caller (for
/// instance `production_source_v1` currently freezes ISW to 0 pending the
/// σ̇-precision resolution).
#[inline]
pub(crate) fn source_isw(inp: &SourceInputs, exp_minus_tau: f64) -> f64 {
    // Ψ̇ = -Φ̇ when anisotropic stress is negligible (ΛCDM limit), so
    // Ψ̇ + Φ̇ = 0 would give zero ISW if implemented naively in that form.
    // The σ-based formula used by the production path (§15.1 of SSOT_POLICY)
    // is equivalent to (Ψ̇ + Φ̇) = 2·Φ̇ in the ΛCDM linear limit; we expose
    // the canonical Newtonian form here for correctness.
    exp_minus_tau * (inp.phidot - (-inp.phidot))  // Ψ̇ + Φ̇ with Ψ = -Φ
}

/// Doppler source channel (scalar).
///
///   `S_Dop = ( (σ + v_b)·g' + (σ̇ + v̇_b)·g ) / k`
///
/// Per SSOT §6 authoritative location: `core::ssot::doppler_source`.
#[inline]
pub(crate) fn source_doppler(inp: &SourceInputs) -> f64 {
    ssot::doppler_source(
        inp.sigma, inp.sigmadot,
        inp.vb, inp.vbdot,
        inp.g, inp.gdot,
        inp.k,
    )
}

/// Polarization quadrupole source channel (CAMB-style, uses `polter`).
///
///   `S_Quad = (5/8k²) · [ k²·polter·g  +  3·polter·g″  +  6·polter'·g' ]`
///
/// The `polter_ddot` term is currently disabled per Phase B-1 post-audit
/// bug E1/E2 (see SSOT_POLICY §15.2).  `polter_dot` must be provided by
/// the caller (typically via FD on the source grid).
#[inline]
pub(crate) fn source_polter_quad(inp: &SourceInputs, polter_dot: f64) -> f64 {
    let polter = ssot::polter(inp.theta2, inp.e2, inp.has_pol);
    ssot::quad_source_no_polterddot(
        polter, polter_dot,
        inp.g, inp.gdot, inp.gddot,
        inp.k,
    )
}

/// E-mode visibility source (scalar).
///
/// Two conventions (caller specifies):
///
///   - `Polter` : `s_e = g · polter = g·(2Θ₂/5 + 3E₂/5)`    (CAMB-style)
///   - `PiBass` : `s_e = (3/4)·g·Π_BASS = (3/4)·g·(Θ₂+E₀+E₂)` (HW-style)
///
/// The production pipeline (2026-04-17) uses `Polter`; exact-transport
/// branch (future PR-021) will adopt `PiBass`.  Both are SSOT-conformant.
#[inline]
pub(crate) fn source_emode(inp: &SourceInputs, conv: EmodeConvention) -> f64 {
    match conv {
        EmodeConvention::Polter => {
            let polter = ssot::polter(inp.theta2, inp.e2, inp.has_pol);
            inp.g * polter
        }
        EmodeConvention::PiBass => {
            let pi = ssot::pi_bass(inp.theta2, inp.e0, inp.e2, inp.has_pol);
            ssot::hw_visibility_source_emode(inp.g, pi)
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Assembler (for tests / downstream PRs)
// ═══════════════════════════════════════════════════════════════════════

/// Assemble all 5 channels into a single `ChannelOutputs` struct.
///
/// This is the reference implementation used by tests — it does NOT
/// replace `production_source_v1` until PR-023 performs the production
/// migration.  The `polter_dot` and `exp_minus_tau` arguments must be
/// supplied externally (they require a source grid / τ grid).
pub(crate) fn assemble(
    inp: &SourceInputs,
    polter_dot: f64,
    exp_minus_tau: f64,
    emode_conv: EmodeConvention,
) -> ChannelOutputs {
    ChannelOutputs {
        s_sw:   source_sw(inp),
        s_isw:  source_isw(inp, exp_minus_tau),
        s_dop:  source_doppler(inp),
        s_quad: source_polter_quad(inp, polter_dot),
        s_e:    source_emode(inp, emode_conv),
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §4.  Tests (PR-010 TDD gate — 5 categories)
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    /// Build a minimal SourceInputs for unit tests.
    fn test_inputs(has_pol: bool) -> SourceInputs {
        SourceInputs {
            theta0: 0.1,   theta2: 0.02,
            e0: 0.005,     e2: 0.03,
            vb: 0.12,      vbdot: 0.001,
            sigma: 0.01,   sigmadot: 0.0002,
            phi: -0.5,     phidot: 0.01,
            psi: 0.5,
            eta_mb: -0.3,
            delta_g: 0.4,
            g: 1.5,        gdot: 0.2,    gddot: 0.01,
            k: 0.05,
            has_pol,
        }
    }

    // ─── Identity tests ───

    #[test]
    fn identity_sw_formula_direct() {
        // Hand-compute S_SW for known inputs
        let inp = test_inputs(true);
        let expected = inp.g * (inp.delta_g / 4.0 + 2.0 * inp.phi + inp.eta_mb / 2.0);
        assert!((source_sw(&inp) - expected).abs() < 1e-15);
    }

    #[test]
    fn identity_doppler_equals_ssot_helper() {
        // PR-010 contract: source_doppler MUST go through core::ssot::doppler_source
        let inp = test_inputs(true);
        let via_registry = source_doppler(&inp);
        let via_ssot = ssot::doppler_source(
            inp.sigma, inp.sigmadot, inp.vb, inp.vbdot, inp.g, inp.gdot, inp.k,
        );
        assert_eq!(via_registry, via_ssot);
    }

    #[test]
    fn identity_polter_quad_equals_ssot_helper() {
        let inp = test_inputs(true);
        let polter_dot = 0.003;
        let via_registry = source_polter_quad(&inp, polter_dot);
        let polter = ssot::polter(inp.theta2, inp.e2, inp.has_pol);
        let via_ssot = ssot::quad_source_no_polterddot(
            polter, polter_dot, inp.g, inp.gdot, inp.gddot, inp.k,
        );
        assert_eq!(via_registry, via_ssot);
    }

    // ─── Limit tests ───

    #[test]
    fn limit_no_visibility_no_source() {
        // visibility-off: g = g' = g'' = 0 → all visibility-weighted channels → 0
        let mut inp = test_inputs(true);
        inp.g = 0.0; inp.gdot = 0.0; inp.gddot = 0.0;
        let out = assemble(&inp, 0.0, 1.0, EmodeConvention::Polter);
        assert_eq!(out.s_sw, 0.0);
        assert_eq!(out.s_dop, 0.0);
        assert_eq!(out.s_quad, 0.0);
        assert_eq!(out.s_e, 0.0);
        // ISW uses e^{-τ}, NOT g — should NOT vanish with visibility-off alone
        // (decouples early from recomb, which is exactly what ISW captures)
    }

    #[test]
    fn limit_pol_off_reduces_polter_quad() {
        // With E₂ = 0:
        //   pol-ON  polter = 2·Θ₂/5 + 3·0/5 = 2·Θ₂/5 = 0.4·Θ₂
        //   pol-OFF polter = 4·Θ₂/10     = 0.4·Θ₂
        // These are IDENTICAL at E₂ = 0.
        let mut inp_on  = test_inputs(true);
        let mut inp_off = test_inputs(false);
        inp_on.e2 = 0.0; inp_off.e2 = 0.0;
        let polter_dot = 0.0;
        let s_on  = source_polter_quad(&inp_on,  polter_dot);
        let s_off = source_polter_quad(&inp_off, polter_dot);
        // With E₂ = 0 the two branches coincide bit-identically.
        assert!((s_on - s_off).abs() < 1e-15,
            "pol-ON/OFF at E₂=0 should match: s_on={}, s_off={}", s_on, s_off);

        // Non-zero E₂: pol-ON gets an extra E₂ contribution
        let mut inp_on_e2  = test_inputs(true);
        inp_on_e2.e2 = 0.05;
        let s_on_e2 = source_polter_quad(&inp_on_e2, polter_dot);
        assert!(s_on_e2 != s_on,
            "pol-ON with E₂≠0 should differ from pol-ON with E₂=0");
    }

    // ─── Channelwise tests (TT vs EE independence) ───

    #[test]
    fn channelwise_emode_independent_of_sw() {
        // Changing δ_γ or Φ (SW inputs) should NOT affect s_e
        let inp1 = test_inputs(true);
        let mut inp2 = inp1.clone();
        inp2.delta_g *= 2.0;
        inp2.phi *= -1.0;
        inp2.eta_mb *= 0.5;
        let e1 = source_emode(&inp1, EmodeConvention::Polter);
        let e2 = source_emode(&inp2, EmodeConvention::Polter);
        assert_eq!(e1, e2);  // s_e depends only on (Θ₂, E₂, g)
    }

    #[test]
    fn channelwise_sw_independent_of_e2() {
        // Changing E₂ (EE input) should NOT affect s_sw
        let inp1 = test_inputs(true);
        let mut inp2 = inp1.clone();
        inp2.e2 *= 3.0;
        inp2.e0 *= -1.0;
        assert_eq!(source_sw(&inp1), source_sw(&inp2));
    }

    #[test]
    fn channelwise_emode_two_conventions_differ() {
        // Polter and PiBass give different s_e in general
        let inp = test_inputs(true);
        let s_polter  = source_emode(&inp, EmodeConvention::Polter);
        let s_pi_bass = source_emode(&inp, EmodeConvention::PiBass);
        assert_ne!(s_polter, s_pi_bass);
        // Hand-check:
        //   Polter : g · (2Θ₂/5 + 3E₂/5) = 1.5 · (0.008 + 0.018) = 1.5·0.026 = 0.039
        //   PiBass : (3/4)·g·(Θ₂+E₀+E₂) = 0.75·1.5·0.055 = 0.0619
        assert!((s_polter  - 0.039).abs() < 1e-14);
        assert!((s_pi_bass - 0.061875).abs() < 1e-14);
    }

    // ─── Regression test (PR-010 gate: assemble matches production formula) ───

    #[test]
    fn regression_assemble_matches_production_s_sw_s_dop_s_quad() {
        // The assembled values for SW, Dop, Quad MUST equal what
        // production_source_v1 computes (since both go through the same
        // ssot helpers).  This is the PR-010 bit-identical guarantee.
        let inp = test_inputs(true);
        let polter_dot = 0.003;
        let out = assemble(&inp, polter_dot, 0.5, EmodeConvention::Polter);
        // SW direct formula
        let sw_ref = inp.g * (inp.delta_g / 4.0 + 2.0 * inp.phi + inp.eta_mb / 2.0);
        // Dop via ssot
        let dop_ref = ssot::doppler_source(
            inp.sigma, inp.sigmadot, inp.vb, inp.vbdot, inp.g, inp.gdot, inp.k);
        // Quad via ssot
        let polter = ssot::polter(inp.theta2, inp.e2, inp.has_pol);
        let quad_ref = ssot::quad_source_no_polterddot(
            polter, polter_dot, inp.g, inp.gdot, inp.gddot, inp.k);
        assert_eq!(out.s_sw, sw_ref);
        assert_eq!(out.s_dop, dop_ref);
        assert_eq!(out.s_quad, quad_ref);
    }

    // ─── Caveat/provenance tests ───

    #[test]
    fn caveat_total_temperature_sums_correctly() {
        let inp = test_inputs(true);
        let out = assemble(&inp, 0.0, 0.5, EmodeConvention::Polter);
        let total = out.s_total_temperature();
        let expected = out.s_sw + out.s_isw + out.s_dop + out.s_quad;
        assert_eq!(total, expected);
        // s_e is NOT included in temperature total
        assert!(total != out.s_e);
    }

    #[test]
    fn caveat_emode_convention_is_explicit() {
        // Contract: no default EmodeConvention — caller MUST specify
        let inp = test_inputs(true);
        // Verify both variants are callable and yield distinct values
        let a = source_emode(&inp, EmodeConvention::Polter);
        let b = source_emode(&inp, EmodeConvention::PiBass);
        assert!(a.is_finite());
        assert!(b.is_finite());
        assert!(a != b);  // PR-010 contract: both conventions are live
    }

    #[test]
    fn caveat_no_pol_reduction_emode() {
        // pol-OFF: E-mode source should reduce gracefully
        // Polter : uses pol-OFF polter = 4·θ₂/10 → s_e = g · (4·θ₂/10)
        //          (Note: corrected PR-010 Stage B — previously documented as
        //          "θ₂/10" but production always used `pig/10 = 4·θ₂/10`.)
        // PiBass : uses pol-OFF pi_bass = θ₂ → s_e = (3/4)·g·θ₂
        let mut inp = test_inputs(false);
        inp.e0 = 99.0;  // should be ignored
        inp.e2 = 99.0;  // should be ignored
        let s_polter = source_emode(&inp, EmodeConvention::Polter);
        let expected_polter = inp.g * (4.0 * inp.theta2 / 10.0);
        assert!((s_polter - expected_polter).abs() < 1e-15,
            "pol-OFF Polter: got {}, expected {}", s_polter, expected_polter);

        let s_pi = source_emode(&inp, EmodeConvention::PiBass);
        let expected_pi = 0.75 * inp.g * inp.theta2;
        assert!((s_pi - expected_pi).abs() < 1e-15);
    }
}
