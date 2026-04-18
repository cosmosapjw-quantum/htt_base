// Frame guards: runtime prohibition checks.
// BB-05: Enforces G3, G6, G7, G8, G12, G13.
//
// These guards panic in debug mode when physics prohibitions are violated.

use crate::bianchi::types::BianchiType;

/// G8: Single-fluid Bianchi I cannot support tilt.
///
/// Panics (debug) if beta > 0 for BI with single fluid.
pub(crate) fn guard_g8_bi_no_single_fluid_tilt(
    btype: &BianchiType,
    beta: f64,
    n_fluids: usize,
) {
    if let BianchiType::I = btype {
        if n_fluids <= 1 && beta.abs() > 1e-15 {
            debug_assert!(
                false,
                "G8 VIOLATION: Bianchi I single-fluid tilt β={:.2e} is forbidden. \
                 The momentum constraint forces β=0 for single perfect fluid in BI. \
                 Two or more fluids are required for BI tilt (Sandin-Uggla 2008, FMO 2025).",
                beta
            );
        }
    }
}

/// G3: Do NOT use frame hopping to process tilt.
///
/// Checks that the tilt is processed in a single frame throughout.
/// frame_id should remain constant within a single computation.
pub(crate) fn guard_g3_no_frame_hopping(
    frame_id_start: u32,
    frame_id_current: u32,
) {
    debug_assert!(
        frame_id_start == frame_id_current,
        "G3 VIOLATION: Frame hopping detected (frame {} → {}). \
         Process tilt entirely in one frame; η≠0 closure fails under frame switch.",
        frame_id_start, frame_id_current
    );
}

/// G7: Do NOT claim dust "grows" tilt in single-fluid models.
///
/// Validates that dust tilt is decaying (dβ/dN < 0 for β > 0).
pub(crate) fn guard_g7_dust_tilt_decays(w: f64, beta: f64, dbeta_dn: f64) {
    if w.abs() < 0.01 && beta > 1e-10 {
        debug_assert!(
            dbeta_dn <= 1e-15,
            "G7 VIOLATION: Dust (w={:.3}) tilt at β={:.4e} has dβ/dN={:.4e} > 0. \
             Single-fluid dust tilt must DECAY: tanhβ ∝ a⁻¹.",
            w, beta, dbeta_dn
        );
    }
}

/// G12: Do NOT claim "radiation tilt frozen" as universal exact statement.
///
/// Returns true if the context allows the "frozen" approximation
/// (zero shear, zero curvature). Returns false otherwise.
pub(crate) fn g12_radiation_frozen_valid(sigma_h: f64, omega_k: f64) -> bool {
    // "Frozen" is valid only in the weak-anisotropy, zero-curvature limit
    sigma_h.abs() < 1e-6 && omega_k.abs() < 1e-6
}

/// G6: Flag if the reduced King-Ellis equation is being used
/// outside its domain of validity.
pub(crate) fn guard_g6_reduced_validity(beta: f64, w: f64) -> bool {
    // Tier C is valid when sinh²β ≪ 1/(1-w) (for w < 1)
    if (1.0 - w).abs() < 1e-10 { return true; } // stiff: always valid
    let threshold = 1.0 / (1.0 - w);
    beta.sinh().powi(2) < 0.01 * threshold
}

/// G13: Attribution guard — mark that exact equations are from
/// "later descendant formulations" not directly King-Ellis 1973.
pub(crate) const KING_ELLIS_ATTRIBUTION: &str =
    "Exact tilt evolution equations follow later descendant formulations \
     (Hewitt-Wainwright 1992, Coley-Hervik 2005), building on the King-Ellis 1973 framework.";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_g8_bi_zero_tilt_ok() {
        // BI with zero tilt: no panic
        guard_g8_bi_no_single_fluid_tilt(&BianchiType::I, 0.0, 1);
    }

    #[test]
    fn test_g8_bi_two_fluid_tilt_ok() {
        // BI with two fluids: tilt allowed
        guard_g8_bi_no_single_fluid_tilt(&BianchiType::I, 0.01, 2);
    }

    #[test]
    #[should_panic(expected = "G8 VIOLATION")]
    #[cfg(debug_assertions)]
    fn test_g8_bi_single_fluid_tilt_panics() {
        guard_g8_bi_no_single_fluid_tilt(&BianchiType::I, 0.01, 1);
    }

    #[test]
    fn test_g7_dust_decay() {
        guard_g7_dust_tilt_decays(0.0, 0.1, -0.05);
    }

    #[test]
    #[should_panic(expected = "G7 VIOLATION")]
    #[cfg(debug_assertions)]
    fn test_g7_dust_growth_panics() {
        guard_g7_dust_tilt_decays(0.0, 0.1, 0.05);
    }

    #[test]
    fn test_g12_frozen_valid() {
        assert!(g12_radiation_frozen_valid(0.0, 0.0));
        assert!(!g12_radiation_frozen_valid(0.01, 0.0));
    }

    #[test]
    fn test_g6_reduced_validity() {
        assert!(guard_g6_reduced_validity(0.01, 0.0)); // small β, dust
        assert!(!guard_g6_reduced_validity(2.0, 0.0)); // large β, dust
        assert!(guard_g6_reduced_validity(2.0, 1.0));  // stiff: always valid
    }

    #[test]
    fn test_g3_same_frame() {
        guard_g3_no_frame_hopping(1, 1);
    }

    #[test]
    #[should_panic(expected = "G3 VIOLATION")]
    #[cfg(debug_assertions)]
    fn test_g3_frame_hop_panics() {
        guard_g3_no_frame_hopping(1, 2);
    }
}
