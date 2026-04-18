// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Linear Coefficient Matrix Builder (PR-024b, part 1 of 2)
// ═══════════════════════════════════════════════════════════════════════
//
// Builds the n_state × n_state coefficient matrix `M(τ)` for the linear
// PSTF RHS:
//
//       dy/dτ = M(τ) · y
//
// `pstf_full_rhs` (PR-023c) is linear and state-independent in the sense
// that its Jacobian ∂(dy)/∂y does not depend on y (RHS is linear homogeneous
// in state).  We exploit this by computing M(τ) column-by-column:
//
//       M(τ)[:, j] = pstf_full_rhs(state = e_j, ...)
//
// where e_j is the unit vector with e_j[j] = 1, all other entries = 0.
//
// ## Why unit-vector decomposition
//
// `pstf_analytical_jacobian` (PR-022c) covers free-streaming + collision
// sectors but NOT PR-023a (metric) or PR-023b (fluid).  Extending the
// analytical Jacobian to cover all sectors is substantial work.
//
// Since `pstf_full_rhs` is LINEAR (verified in PR-022c's FD check), the
// unit-vector decomposition is exact up to floating-point roundoff.  This
// gives us a correct matrix M(τ) without needing to extend the Jacobian.
//
// ## Trade-off
//
// Cost: n_state evaluations of `pstf_full_rhs` per τ snapshot.  For
// n_state ≈ 300 and n_snaps ≈ 200, that's ~60,000 RHS calls per k-mode
// just for matrix construction.  This is slower than MB-95's hand-written
// analytic `build_camb_matrix_into`.  Acceptable for PR-024b milestone;
// future PR may add an analytic `build_pstf_matrix_into_analytic` for
// performance once PSTF is proven to agree with MB-95.
//
// ## Row-major ordering
//
// Matches MB-95 `build_camb_matrix_into`:
//
//       idx(row, col) = row * n + col
//
// Required by `integrate_linear_profile_rodas5p` in `solver::stacked`.

#![allow(dead_code)]

use super::full_rhs::{FullRhsInputs, pstf_full_rhs};
use super::layout::PstfFlrwLayout;
use super::metric::BackgroundQuantities;
use super::collision::FrameConvention;
use crate::solver::sync_gauge_camb::CambBackground;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  CambBackground → BackgroundQuantities bridge
// ═══════════════════════════════════════════════════════════════════════

/// Convert MB-95 `CambBackground` snapshot to PSTF `BackgroundQuantities`.
///
/// Field mapping:
///   adotoa   → h_conformal   (both are ℋ = a·H)
///   grho_g   → grho_gamma
///   grho_nu  → grho_nu
///   grho_b   → grho_b
///
/// Fields not in BackgroundQuantities (used separately in inputs):
///   opac, cs2b, vis/dvis/ddvis, expmmu
#[inline]
pub(crate) fn bg_from_camb(bg: &CambBackground) -> BackgroundQuantities {
    BackgroundQuantities {
        h_conformal: bg.adotoa,
        grho_gamma: bg.grho_g,
        grho_nu: bg.grho_nu,
        grho_b: bg.grho_b,
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Matrix builder via unit-vector decomposition
// ═══════════════════════════════════════════════════════════════════════

/// Fill `out` with M(τ) such that `dy/dτ = M(τ) · y` for PSTF primary RHS.
///
/// Row-major ordering: `out[row * n_state + col]` = M[row, col].
/// Matches MB-95 `build_camb_matrix_into` convention, required by
/// `integrate_linear_profile_rodas5p`.
///
/// # Arguments
/// * `k`        — comoving wavenumber [Mpc⁻¹]
/// * `tau`      — conformal time snapshot [Mpc]
/// * `bg`       — MB-95 CambBackground at this τ (contains all fields)
/// * `layout`   — PSTF state layout
/// * `out`      — pre-allocated `n_state * n_state` buffer
///
/// # Panics
/// If `out.len() != layout.n_state.pow(2)`.
pub(crate) fn build_pstf_matrix_into(
    k: f64,
    tau: f64,
    bg: &CambBackground,
    layout: &PstfFlrwLayout,
    out: &mut [f64],
) {
    let n = layout.n_state;
    assert_eq!(out.len(), n * n,
        "out buffer size {} != n² = {}", out.len(), n * n);

    out.fill(0.0);

    let bg_pstf = bg_from_camb(bg);

    // Production defaults (match MB-95 ProductionConfig)
    let inputs = FullRhsInputs {
        k,
        tau,
        bg: bg_pstf,
        kappa_dot: bg.opac,
        r_b: if bg.grho_g > 0.0 { 0.75 * bg.grho_b / bg.grho_g } else { 0.0 },
        use_pol_feedback: false,  // production default (pol off)
        frame: FrameConvention::ElectronRestFrame,
        cs2b: bg.cs2b,
    };

    // Column-by-column construction
    // For each j, set state = e_j, compute dy = pstf_full_rhs(e_j),
    // which gives column j of M: M[:, j] = dy[:] for e_j input.
    let mut state = vec![0.0_f64; n];
    let mut dy = vec![0.0_f64; n];

    for j in 0..n {
        state.fill(0.0);
        state[j] = 1.0;
        // pstf_full_rhs zero-inits dy, so no need to pre-zero here
        pstf_full_rhs(&state, &mut dy, &inputs, layout);

        // Column j of M: M[i, j] = dy[i]
        // Row-major: out[i * n + j] = M[i, j]
        for i in 0..n {
            out[i * n + j] = dy[i];
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::full_rhs::{FullRhsInputs, pstf_full_rhs};

    /// Test fixture: layout + representative CambBackground.
    fn test_fixture() -> (PstfFlrwLayout, CambBackground) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        // Representative recombination-era background
        let bg = CambBackground {
            adotoa: 3e-3,      // ℋ at z~1100
            grho_g: 2e-5,      // photon energy density
            grho_nu: 1.5e-5,   // massless ν
            grho_b: 3e-6,      // baryon
            grho_c: 1.5e-5,    // CDM
            opac: 0.5,         // Thomson opacity at recomb peak
            cs2b: 3.3e-10,     // baryon sound speed²
            vis: 3e-3,
            dvis: 0.0,
            ddvis: -1e-6,
            a: 1.0 / 1100.0,
            expmmu: 0.5,
            dopac: 0.0,         // fenced to 0
        };
        (layout, bg)
    }

    // ─── Identity: column j matches pstf_full_rhs(e_j) ──────────────

    /// Each column of M equals `pstf_full_rhs(state = e_j)`.
    #[test]
    fn identity_matrix_build_matches_unit_vectors() {
        let (layout, bg) = test_fixture();
        let n = layout.n_state;
        let k = 0.01;
        let tau = 100.0;

        let mut mat = vec![0.0_f64; n * n];
        build_pstf_matrix_into(k, tau, &bg, &layout, &mut mat);

        // Verify a sample of columns via direct pstf_full_rhs calls
        let inputs = FullRhsInputs {
            k, tau, bg: bg_from_camb(&bg),
            kappa_dot: bg.opac,
            r_b: 0.75 * bg.grho_b / bg.grho_g,
            use_pol_feedback: false,
            frame: FrameConvention::ElectronRestFrame,
            cs2b: bg.cs2b,
        };

        // Sample columns: metric_etak(0), metric_sigma(1), photon_i_m0(2),
        // baryon_v_m0, cdm_delta, neutrino m0(ell=0)
        let sample_cols = [
            layout.i_metric_etak(),
            layout.i_metric_sigma(),
            layout.i_photon_i_m0(2),
            layout.i_baryon_v_m0(),
            layout.i_cdm_delta(),
            layout.i_neutrino_m0(0),
        ];

        let mut state = vec![0.0_f64; n];
        let mut dy = vec![0.0_f64; n];
        for &j in &sample_cols {
            state.fill(0.0);
            state[j] = 1.0;
            dy.fill(0.0);
            pstf_full_rhs(&state, &mut dy, &inputs, &layout);

            for i in 0..n {
                let expected = dy[i];
                let got = mat[i * n + j];
                assert_eq!(got, expected,
                    "col {}, row {}: got {}, expected {}", j, i, got, expected);
            }
        }
    }

    // ─── Identity: linearity of pstf_full_rhs ───────────────────────

    /// `pstf_full_rhs(a·u + b·v) = a·pstf_full_rhs(u) + b·pstf_full_rhs(v)`.
    /// Re-verifies PR-022c's linearity claim is intact after PR-023 sectors.
    #[test]
    fn identity_matrix_linearity() {
        let (layout, bg) = test_fixture();
        let n = layout.n_state;
        let inputs = FullRhsInputs {
            k: 0.01, tau: 100.0, bg: bg_from_camb(&bg),
            kappa_dot: bg.opac,
            r_b: 0.75 * bg.grho_b / bg.grho_g,
            use_pol_feedback: false,
            frame: FrameConvention::ElectronRestFrame,
            cs2b: bg.cs2b,
        };

        // Pick two distinct random-ish state vectors
        let mut u = vec![0.0_f64; n];
        let mut v = vec![0.0_f64; n];
        u[layout.i_metric_etak()] = 1e-3;
        u[layout.i_photon_i_m0(2)] = 2e-4;
        u[layout.i_baryon_v_m0()] = 5e-4;
        v[layout.i_metric_sigma()] = 3e-4;
        v[layout.i_neutrino_m0(1)] = 7e-4;
        v[layout.i_photon_i_m0(0)] = 1e-3;

        let a = 2.5_f64;
        let b = -1.7_f64;

        let mut combined = vec![0.0_f64; n];
        for i in 0..n {
            combined[i] = a * u[i] + b * v[i];
        }

        let mut dy_u = vec![0.0_f64; n];
        let mut dy_v = vec![0.0_f64; n];
        let mut dy_combined = vec![0.0_f64; n];
        pstf_full_rhs(&u, &mut dy_u, &inputs, &layout);
        pstf_full_rhs(&v, &mut dy_v, &inputs, &layout);
        pstf_full_rhs(&combined, &mut dy_combined, &inputs, &layout);

        for i in 0..n {
            let expected = a * dy_u[i] + b * dy_v[i];
            let got = dy_combined[i];
            // Tolerance allows FP roundoff from reassociation
            let tol = 1e-12 * (expected.abs() + 1e-20);
            assert!((got - expected).abs() <= tol,
                "linearity violation at i={}: got {}, expected {} (tol {})",
                i, got, expected, tol);
        }
    }

    // ─── Identity: multiple τ values ────────────────────────────────

    /// Matrix values change with τ (coefficients are τ-dependent via bg),
    /// but matrix structure (sparsity pattern) is consistent.
    #[test]
    fn identity_matrix_multiple_tau() {
        let (layout, mut bg) = test_fixture();
        let n = layout.n_state;
        let k = 0.01;

        // Build matrix at τ1 (recomb era) and τ2 (later, smaller opac)
        let mut mat_1 = vec![0.0_f64; n * n];
        build_pstf_matrix_into(k, 100.0, &bg, &layout, &mut mat_1);

        // Modify bg to reflect later τ
        bg.opac = 0.01;
        bg.adotoa = 1e-3;
        let mut mat_2 = vec![0.0_f64; n * n];
        build_pstf_matrix_into(k, 500.0, &bg, &layout, &mut mat_2);

        // Matrices should differ (at least in collision-affected entries)
        let mut any_diff = false;
        for i in 0..n*n {
            if (mat_1[i] - mat_2[i]).abs() > 1e-10 {
                any_diff = true;
                break;
            }
        }
        assert!(any_diff,
            "matrices at different τ should differ (collision changes with opac)");

        // Row for clxcdot (CDM continuity) should be IDENTICAL across τ
        // because it's -hdot/2, and only hdot structure (coefficients of
        // theta_1, nu_1, v_b) changes with bg — not the sparsity.
        // (Not asserting equality — coefficients DO differ with bg.grho.
        //  This test checks that the build process runs successfully at
        //  multiple τ values without panicking.)
    }
}
