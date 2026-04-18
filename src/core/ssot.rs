// ═══════════════════════════════════════════════════════════════════════
// BASS Core SSOT — Single Source of Truth for source channel primitives
// ═══════════════════════════════════════════════════════════════════════
//
// Added for PR-010 Stage B / PR-020 through PR-024b (PSTF primary work).
//
// All source channel helpers used by both:
//   - `sync_gauge_camb::production_source_v1` (MB-95 production path)
//   - `source::registry` (PR-010 SSOT routing)
//   - `solver::pstf_primary::source` (PSTF LoS source function)
//
// live here as pure functions.  No struct, no state — just named formulae
// with a bit-identical contract.
//
// ## Bit-identical contract
//
// Each function's body is the canonical form for its formula.  Any call
// site that computes the same quantity MUST route through this module
// (no inline recomputation).  This guarantees:
//
//   1. Single point of modification (change once, propagates everywhere)
//   2. Bit-identical numerical result across call sites
//   3. Unit tests can verify the formula at one point

#![allow(dead_code)]

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Layout constants (referenced by pstf_primary::layout::validate)
// ═══════════════════════════════════════════════════════════════════════

pub(crate) mod constants {
    /// Minimum ℓ_max for photon hierarchy.  Below this the ℓ=2 quadrupole
    /// source (polter) lacks the ℓ=3 decay channel needed for numerical
    /// stability.  Historical convention: CAMB default = 10, minimum = 3.
    pub(crate) const MIN_LMAX_G: usize = 3;

    /// Minimum ℓ_max for polarization hierarchy when polarization is ON.
    /// E-mode and B-mode only exist for ℓ ≥ 2, so ℓ_max ≥ 2 required.
    pub(crate) const MIN_LMAX_POL_WHEN_ON: usize = 2;
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  polter / polter_dot primitives (CAMB-style)
// ═══════════════════════════════════════════════════════════════════════

/// `polter = 2·Θ_2/5 + 3·E_2/5`  (CAMB-style)
///
/// When polarization is OFF: `polter = 4·Θ_2/10 = 2·Θ_2/5`
/// (Matches `pig/10` form with `pig = 4·Θ_2`.)
#[inline]
pub(crate) fn polter(theta2: f64, e2: f64, has_pol: bool) -> f64 {
    if has_pol {
        // Matches production_source_v1 line 341:
        //   let polter = 2.0 * theta2 / 5.0 + 3.0 * e2 / 5.0
        2.0 * theta2 / 5.0 + 3.0 * e2 / 5.0
    } else {
        // Matches production_source_v1 line 343 (pig/10 with pig = 4·Θ_2):
        //   let polter = 4.0 * theta2 / 10.0
        4.0 * theta2 / 10.0
    }
}

/// Time derivative of `polter`.  `pigdot = 4 · dΘ_2/dη`, `e2dot = dE_2/dη`.
#[inline]
pub(crate) fn polter_dot(pigdot: f64, e2dot: f64, has_pol: bool) -> f64 {
    if has_pol {
        // Matches production:
        //   2.0 * (pigdot / 4.0) / 5.0 + 3.0 * e2dot / 5.0
        2.0 * (pigdot / 4.0) / 5.0 + 3.0 * e2dot / 5.0
    } else {
        // Matches production:
        //   pigdot / 10.0
        pigdot / 10.0
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Π_BASS primitive (HW/TAM-style)
// ═══════════════════════════════════════════════════════════════════════

/// `Π_BASS = Θ_2 + E_0 + E_2`  (exact HW-style polarization primitive)
///
/// When polarization is OFF: `Π_BASS = Θ_2`.
#[inline]
pub(crate) fn pi_bass(theta2: f64, e0: f64, e2: f64, has_pol: bool) -> f64 {
    if has_pol {
        theta2 + e0 + e2
    } else {
        theta2
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §4.  Source channels
// ═══════════════════════════════════════════════════════════════════════

/// Doppler source channel.
///
/// `Dop = [(σ + v_b) · g' + (σ̇ + v̇_b) · g] / k`
#[inline]
pub(crate) fn doppler_source(
    sigma: f64, sigmadot: f64, v_b: f64, v_b_dot: f64,
    g: f64, g_prime: f64, k: f64,
) -> f64 {
    assert!(k.abs() > 1e-30, "ssot::doppler_source: k must be > 0 (got {:e})", k);
    ((sigma + v_b) * g_prime + (sigmadot + v_b_dot) * g) / k
}

/// Quadrupole polterbased source channel (CAMB `s_quad`), WITHOUT the
/// polter_ddot term (that term is deferred to post-pass FD, bug E3).
///
/// `Quad = (5 / (8·k²))[k²·polter·g + 3·polter·g'' + 6·polter'·g']`
#[inline]
pub(crate) fn quad_source_no_polterddot(
    polter: f64, polter_dot: f64,
    g: f64, g_prime: f64, g_ddprime: f64,
    k: f64,
) -> f64 {
    assert!(k.abs() > 1e-30, "ssot::quad_source_no_polterddot: k must be > 0 (got {:e})", k);
    let k2 = k * k;
    (5.0 / (8.0 * k2)) * (
        k2 * polter * g
        + 3.0 * polter * g_ddprime
        + 6.0 * polter_dot * g_prime
    )
}

/// HW-style visibility × Π_BASS E-mode source.
///
/// `S_E = (3/4) · g · Π_BASS`
#[inline]
pub(crate) fn hw_visibility_source_emode(g: f64, pi_bass_val: f64) -> f64 {
    0.75 * g * pi_bass_val
}

// ═══════════════════════════════════════════════════════════════════════
//   §5.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_polter_pol_on() {
        let r = polter(0.1, 0.2, true);
        let expected = 2.0 * 0.1 / 5.0 + 3.0 * 0.2 / 5.0;
        assert!((r - expected).abs() < 1e-18);
    }

    #[test]
    fn test_polter_pol_off() {
        let r = polter(0.1, 0.2, false);
        // E_2 ignored
        let expected = 4.0 * 0.1 / 10.0;
        assert!((r - expected).abs() < 1e-18);
    }

    #[test]
    fn test_polter_dot_consistency() {
        // When pigdot = 0 and e2dot = 0, polter_dot = 0
        assert_eq!(polter_dot(0.0, 0.0, true), 0.0);
        assert_eq!(polter_dot(0.0, 0.0, false), 0.0);
    }

    #[test]
    fn test_pi_bass() {
        let r = pi_bass(0.5, 0.1, 0.2, true);
        assert!((r - 0.8).abs() < 1e-18);
        let r = pi_bass(0.5, 0.1, 0.2, false);
        assert!((r - 0.5).abs() < 1e-18);
    }

    #[test]
    fn test_doppler_matches_inline_formula() {
        let sigma = 1e-5; let sigmadot = -1e-7;
        let vb = 0.001; let vbdot = -1e-6;
        let g = 3e-3; let gp = 0.0;
        let k = 0.01;
        let r = doppler_source(sigma, sigmadot, vb, vbdot, g, gp, k);
        let expected = ((sigma + vb) * gp + (sigmadot + vbdot) * g) / k;
        assert!((r - expected).abs() < 1e-18);
    }

    #[test]
    #[should_panic(expected = "k must be > 0")]
    fn test_doppler_panics_on_zero_k() {
        doppler_source(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    }
}
