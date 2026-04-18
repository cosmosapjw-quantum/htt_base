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
use super::jacobian::{JacobianInputs, pstf_jacobian_dense};
use super::layout::PstfFlrwLayout;
use super::metric::BackgroundQuantities;
use super::collision::{CollisionInputs, FrameConvention};
use super::rhs_free::RhsInputs;
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
//   §2.5  Analytical matrix builder (PR-024c-PERF)
// ═══════════════════════════════════════════════════════════════════════

/// PR-024c-PERF: build `M(τ)` analytically via the extended sparse Jacobian.
///
/// Mathematically equivalent to `build_pstf_matrix_into` (the matrix is
/// exactly the Jacobian ∂(dy)/∂y since the RHS is linear homogeneous in
/// state).  Replaces `n_state` unit-vector RHS evaluations with `~O(nnz)`
/// direct triplet writes — expected ~80× speedup per snapshot.
///
/// Not bit-identical to `build_pstf_matrix_into` (different FP operation
/// order); differences are at ULP level and verified via
/// `identity_analytical_matches_unit_vector` test.
///
/// # Arguments
/// Same as `build_pstf_matrix_into`.
///
/// # Panics
/// If `out.len() != layout.n_state.pow(2)`.
pub(crate) fn build_pstf_matrix_analytical_into(
    k: f64,
    tau: f64,
    bg: &CambBackground,
    layout: &PstfFlrwLayout,
    out: &mut [f64],
) {
    let n = layout.n_state;
    assert_eq!(out.len(), n * n,
        "out buffer size {} != n² = {}", out.len(), n * n);

    let bg_pstf = bg_from_camb(bg);
    let r_b = if bg.grho_g > 0.0 { 0.75 * bg.grho_b / bg.grho_g } else { 0.0 };

    // Assemble extended JacobianInputs via the normal builder + extension
    let rhs_in = RhsInputs {
        k,
        tau,
        // metric_monopole_source enters free-streaming RHS at ℓ=0 but
        // produces an AFFINE (state-independent) shift, so does NOT
        // contribute to the Jacobian.  Set to 0 here — the metric
        // monopole's state-DEPENDENT part is handled by metric_fluid_block.
        metric_monopole_source: 0.0,
    };
    let coll_in = CollisionInputs {
        kappa_dot: bg.opac,
        r_b,
        use_pol_feedback: false,  // production default (matches unit-vector builder)
        frame: FrameConvention::ElectronRestFrame,
    };
    let inputs = JacobianInputs::from_rhs_and_collision(&rhs_in, &coll_in)
        .with_metric_fluid_bg(bg_pstf, bg.cs2b);

    // State passed to pstf_jacobian_dense is unused (Jacobian is linear,
    // state-independent).  Pass empty-ish state of correct length.
    let state = vec![0.0_f64; n];
    pstf_jacobian_dense(&state, &inputs, layout, out);
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

    // ─── PR-024c-PERF Step 4: analytical matrix equivalence ────────

    /// Analytical matrix (Jacobian-based) matches unit-vector matrix
    /// element-wise to near-ULP precision.
    ///
    /// Not bit-identical (different FP op order), but should agree to
    /// ~1e-10 relative / 1e-14 absolute on a representative state.
    #[test]
    fn perf_step4_analytical_matches_unit_vector() {
        let (layout, bg) = test_fixture();
        let n = layout.n_state;
        let k = 0.01;
        let tau = 100.0;

        let mut mat_uv = vec![0.0_f64; n * n];
        build_pstf_matrix_into(k, tau, &bg, &layout, &mut mat_uv);

        let mut mat_an = vec![0.0_f64; n * n];
        build_pstf_matrix_analytical_into(k, tau, &bg, &layout, &mut mat_an);

        // Compare element-wise
        let mut max_abs = 0.0_f64;
        let mut max_rel = 0.0_f64;
        let mut i_max = (0usize, 0usize);
        for i in 0..n {
            for j in 0..n {
                let uv = mat_uv[i * n + j];
                let an = mat_an[i * n + j];
                let abs_err = (uv - an).abs();
                let scale = uv.abs().max(an.abs()).max(1e-30);
                let rel_err = abs_err / scale;
                if abs_err > max_abs {
                    max_abs = abs_err;
                    i_max = (i, j);
                }
                if uv.abs() > 1e-10 && rel_err > max_rel {
                    max_rel = rel_err;
                }
            }
        }
        // Relative error tolerance: 1e-10 is achievable given the simple
        // linear expressions; allow 1e-8 headroom for unexpected FP ordering.
        assert!(max_rel < 1e-8,
            "analytical vs unit-vector: max rel err {:.3e} at {:?}, max abs {:.3e}",
            max_rel, i_max, max_abs);
    }

    /// Analytical matrix agreement across multiple k values.
    #[test]
    fn perf_step4_multiple_k_agreement() {
        let (layout, bg) = test_fixture();
        let n = layout.n_state;

        for &k in &[1e-4_f64, 1e-3, 1e-2, 1e-1] {
            let tau = 100.0;
            let mut mat_uv = vec![0.0_f64; n * n];
            let mut mat_an = vec![0.0_f64; n * n];
            build_pstf_matrix_into(k, tau, &bg, &layout, &mut mat_uv);
            build_pstf_matrix_analytical_into(k, tau, &bg, &layout, &mut mat_an);

            let mut max_rel = 0.0_f64;
            for i in 0..n*n {
                let uv = mat_uv[i];
                let an = mat_an[i];
                if uv.abs() > 1e-10 {
                    let rel = (uv - an).abs() / uv.abs();
                    if rel > max_rel { max_rel = rel; }
                }
            }
            assert!(max_rel < 1e-8,
                "k={}: analytical vs unit-vector max rel err {:.3e}", k, max_rel);
        }
    }

    /// Direct head-to-head timing: analytical vs unit-vector matrix build.
    /// Not a correctness test; prints timing for manual inspection.
    #[test]
    #[ignore = "timing probe; run with --ignored --nocapture"]
    fn perf_step4_timing_comparison() {
        // Run timing at multiple layout sizes to characterize when the
        // analytical builder wins decisively.
        eprintln!("\n═══ MATRIX BUILD TIMING ═══");
        let bg = CambBackground {
            adotoa: 3e-3, grho_g: 2e-5, grho_nu: 1.5e-5, grho_b: 3e-6,
            grho_c: 1.5e-5, opac: 0.5, cs2b: 3.3e-10,
            vis: 3e-3, dvis: 0.0, ddvis: -1e-6,
            a: 1.0 / 1100.0, expmmu: 0.5,
        };
        let k = 0.01;
        let tau = 100.0;

        for &(lg, ln, lpol) in &[(8usize, 6usize, 0usize), (12, 8, 0), (16, 16, 16), (25, 15, 25)] {
            let layout = PstfFlrwLayout::new(lg, ln, lpol);
            layout.validate();
            let n = layout.n_state;
            let mut mat = vec![0.0_f64; n * n];

            // Warmup
            for _ in 0..3 {
                build_pstf_matrix_into(k, tau, &bg, &layout, &mut mat);
                build_pstf_matrix_analytical_into(k, tau, &bg, &layout, &mut mat);
            }

            let n_iter = (50_000_000 / (n * n).max(1)).max(5);

            let t0 = std::time::Instant::now();
            for _ in 0..n_iter {
                build_pstf_matrix_into(k, tau, &bg, &layout, &mut mat);
            }
            let dt_uv = t0.elapsed().as_secs_f64() / n_iter as f64;

            let t1 = std::time::Instant::now();
            for _ in 0..n_iter {
                build_pstf_matrix_analytical_into(k, tau, &bg, &layout, &mut mat);
            }
            let dt_an = t1.elapsed().as_secs_f64() / n_iter as f64;

            eprintln!("  (lg={:2} ln={:2} lpol={:2}) n_state={:<5} | uv={:7.3}ms  an={:7.3}ms  speedup={:4.1}×",
                      lg, ln, lpol, n, dt_uv * 1000.0, dt_an * 1000.0, dt_uv / dt_an);
        }
        eprintln!("═══════════════════════════\n");
    }

    /// Analytical matrix sanity: non-trivial entries exist in metric sector.
    /// (Regression guard: if metric_fluid_block is accidentally dropped,
    /// analytical matrix will have empty metric rows.)
    #[test]
    fn perf_step4_metric_rows_populated() {
        let (layout, bg) = test_fixture();
        let n = layout.n_state;
        let mut mat_an = vec![0.0_f64; n * n];
        build_pstf_matrix_analytical_into(0.01, 100.0, &bg, &layout, &mut mat_an);

        let row_etak = layout.i_metric_etak();
        let row_sigma = layout.i_metric_sigma();
        let row_clxc = layout.i_cdm_delta();

        let etak_nz = (0..n).filter(|&j| mat_an[row_etak * n + j] != 0.0).count();
        let sigma_nz = (0..n).filter(|&j| mat_an[row_sigma * n + j] != 0.0).count();
        let clxc_nz = (0..n).filter(|&j| mat_an[row_clxc * n + j] != 0.0).count();

        assert!(etak_nz >= 3, "etak row has {} nonzero entries, expected ≥ 3", etak_nz);
        assert!(sigma_nz >= 4, "sigma row has {} nonzero entries, expected ≥ 4", sigma_nz);
        assert!(clxc_nz >= 4, "clxc row has {} nonzero entries, expected ≥ 4", clxc_nz);
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
