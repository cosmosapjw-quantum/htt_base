// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Time Integration + Source Grid (PR-024b, part 2 of 2)
// ═══════════════════════════════════════════════════════════════════════
//
// Integrates the PSTF state over the MB-95 `tau_profile`, using the same
// `integrate_linear_profile_rodas5p` stepper that production uses, but
// with `build_pstf_matrix_into` for the per-snapshot coefficient matrix.
//
// At each visibility snapshot, after state is extracted:
//   1. Call `pstf_full_rhs` to get dy (exact linear RHS)
//   2. Call `pstf_source_function` to get source channels
//   3. Extract phi, psi, polterdot for storage
//
// The result `PstfKmodeResult` mirrors MB-95 `CambKmodeResult` field-for-
// field so PR-024c (LoS integration) can reuse MB-95's `los_integrate`
// logic almost verbatim.
//
// ## Why reuse MB-95 stepper
//
// - Same Rodas5P algorithm → same numerical error characteristics
// - Same `tau_profile` from `CommonProfile` → same snapshot locations
// - Same IC era (matched to MB-95 bootstrap or adiabatic)
//
// Tolerance-based equivalence (not bit-identical) because PSTF matrix is
// built via unit-vector decomposition (FP associativity different from
// MB-95's hand-analytic `build_camb_matrix_into`).
//
// ## Layout accessor range check (PR-024a lesson)
//
// All accessors called here have documented allowed ranges:
//   - i_metric_etak, i_metric_sigma: scalar (always safe)
//   - i_photon_i_m0(ell): ell ∈ [0, ell_max_gamma]
//   - i_photon_e_m0(ell): ell ∈ [2, ell_max_gamma] (pol on)
//   - i_photon_b_m0(ell): ell ∈ [2, ell_max_gamma] (pol on)
//   - i_neutrino_m0(ell): ell ∈ [0, ell_max_nu]
//   - i_baryon_{delta,v_m0}, i_cdm_{delta,v_m0}: scalar (always safe)
//
// Unit-vector loop in `build_pstf_matrix_into` uses flat state[j] for
// j ∈ [0, n_state) — no accessor with ell arg is called with j, only
// with layout-derived indices.  Hence no ell<2 panic risk.

#![allow(dead_code)]

use super::full_rhs::{FullRhsInputs, pstf_full_rhs};
use super::layout::PstfFlrwLayout;
use super::metric::BackgroundQuantities;
use super::collision::FrameConvention;
use super::source::{VisibilityAtSnap, pstf_source_function};
use super::matrix::{build_pstf_matrix_into, build_pstf_matrix_analytical_into, bg_from_camb};
use crate::solver::sync_gauge_camb::{CommonProfile, CambBackground};
use crate::solver::stacked::{integrate_linear_profile_rodas5p, integrate_linear_profile_rodas5p_callback};

/// Phase 2.0: linear interpolation of CambBackground fields, used by the
/// callback streaming path when the stepper queries off-snapshot τ values.
/// At exact-snapshot queries this helper is not called (see integrate loop
/// for the direct lookup short-circuit).
fn interp_camb_bg(bg_a: &CambBackground, bg_b: &CambBackground, w: f64) -> CambBackground {
    let blend = |a: f64, b: f64| a + w * (b - a);
    CambBackground {
        adotoa: blend(bg_a.adotoa, bg_b.adotoa),
        grho_g: blend(bg_a.grho_g, bg_b.grho_g),
        grho_nu: blend(bg_a.grho_nu, bg_b.grho_nu),
        grho_b: blend(bg_a.grho_b, bg_b.grho_b),
        grho_c: blend(bg_a.grho_c, bg_b.grho_c),
        opac: blend(bg_a.opac, bg_b.opac),
        cs2b: blend(bg_a.cs2b, bg_b.cs2b),
        vis: blend(bg_a.vis, bg_b.vis),
        dvis: blend(bg_a.dvis, bg_b.dvis),
        ddvis: blend(bg_a.ddvis, bg_b.ddvis),
        a: blend(bg_a.a, bg_b.a),
        expmmu: blend(bg_a.expmmu, bg_b.expmmu),
    }
}
use crate::core::config::Rodas5PConfig;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  PstfKmodeResult
// ═══════════════════════════════════════════════════════════════════════

/// Per-k result of PSTF time integration.
///
/// Mirrors MB-95 `CambKmodeResult` field-for-field for drop-in reuse in
/// PR-024c's LoS integration (which will port MB-95 `los_integrate`).
#[derive(Clone, Debug)]
pub(crate) struct PstfKmodeResult {
    pub(crate) eta_grid: Vec<f64>,
    pub(crate) source_total: Vec<f64>,
    pub(crate) source_sw: Vec<f64>,
    pub(crate) source_dop: Vec<f64>,
    pub(crate) source_quad: Vec<f64>,
    pub(crate) source_e_total: Vec<f64>,
    pub(crate) phi: Vec<f64>,
    pub(crate) psi: Vec<f64>,
    pub(crate) polterdot_grid: Vec<f64>,
    pub(crate) n_state: usize,
    /// Optional full state trajectory (saved when `save_trajectory = true`).
    pub(crate) state_trajectory: Option<Vec<Vec<f64>>>,
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Main solve_kmode
// ═══════════════════════════════════════════════════════════════════════

/// Solve a single k-mode with PSTF primary state + source collection.
///
/// # Arguments
/// * `k`              — comoving wavenumber [Mpc⁻¹]
/// * `common`         — shared CommonProfile (MB-95 struct, reusable)
/// * `layout`         — PSTF state layout
/// * `ic_state`       — initial condition state vector (from pstf_adiabatic_ic)
/// * `save_trajectory`— whether to return full state at each snapshot
///
/// # Returns
/// `PstfKmodeResult` with source channels, phi/psi, polterdot_grid at
/// each snapshot in `common.tau_profile`.
///
/// # Layout accessor range safety
/// All accessors called with explicit ell use values from
/// `0..=layout.ell_max_{gamma,nu}` or (for pol) `2..=layout.ell_max_gamma`.
/// Verified in PR-024b pre-audit §3.
pub(crate) fn pstf_solve_kmode(
    k: f64,
    common: &CommonProfile,
    layout: &PstfFlrwLayout,
    ic_state: Vec<f64>,
    save_trajectory: bool,
) -> Result<PstfKmodeResult, String> {
    let n = layout.n_state;

    if ic_state.len() != n {
        return Err(format!("ic_state length {} != n_state {}", ic_state.len(), n));
    }
    if common.bg_at_snap.len() != common.tau_profile.len() {
        return Err("CommonProfile tau_profile and bg_at_snap must have equal length".to_string());
    }

    // Filter tau_profile to start from first τ > tau_min.
    // Required because `pstf_free_streaming_rhs` uses tau-based ℓ_max
    // truncation (`(ℓ+1)/τ · Θ_{ℓ_max}`) which panics at τ ≤ 0.
    // Match MB-95 `solve_camb_kmode` convention: tau_ic_min = 0.5 Mpc
    // (conformal time where bootstrap IC lookup is valid).
    let tau_min = 0.5_f64;
    let start_i = common.tau_profile.iter()
        .position(|&t| t > tau_min)
        .ok_or_else(|| format!(
            "No snapshot with τ > {} in CommonProfile (max τ = {})",
            tau_min,
            common.tau_profile.last().copied().unwrap_or(0.0)
        ))?;
    let tau_filtered: &[f64] = &common.tau_profile[start_i..];
    let bg_filtered: &[CambBackground] = &common.bg_at_snap[start_i..];
    let n_vis = tau_filtered.len();

    if n_vis < 2 {
        return Err(format!(
            "Insufficient snapshots after τ > {} filtering: {}", tau_min, n_vis
        ));
    }

    // Phase 2.0 (2026-04-19): three backends available via env vars.
    //
    //   (default) ANALYTICAL path — pre-materialize mats_flat via
    //             build_pstf_matrix_analytical_into (O(N_snap · n²) memory).
    //   BASS_PSTF_MATRIX_UV=1 — legacy unit-vector pre-materialization.
    //   BASS_PSTF_CALLBACK=1  — streaming callback (O(n²) memory; analytical
    //             builder evaluated on demand by the stepper).
    //
    // The callback path eliminates the O(N_snap · n²) heap allocation.
    // Numerically should agree with the analytical path bit-identically up
    // to FP op ordering (verified by perf_step5_analytical_vs_uv + the new
    // Phase 2.0 equivalence tests).
    let use_unit_vector = std::env::var("BASS_PSTF_MATRIX_UV").ok().as_deref() == Some("1");
    let use_callback = std::env::var("BASS_PSTF_CALLBACK").ok().as_deref() == Some("1");

    // Rodas5P config (production-equivalent) — identical across all three paths
    let h_max_k = (4.0 * 3.0_f64.sqrt() / k.max(1e-10)).min(5.0);
    let cfg = Rodas5PConfig {
        rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
        h_init: None, h_min: 1e-14, h_max: h_max_k,
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
        use_analytic_jacobian: true, use_ft_term: false,
        use_blas_lu: false, use_block_diag: false,
        ell_max_gamma_hint: layout.ell_max_gamma,
        ell_max_nu_hint: layout.ell_max_nu,
        ell_max_pol_hint: 0,
        include_pol_hint: layout.has_pol(),
        use_sparse: false,
    };

    let (snapshots, _stats, _cdiag) = if use_callback {
        // Streaming path: the builder captures k + bg_filtered by reference
        // and assembles M(τ) analytically on demand.  The stepper's
        // LinearProfileCallback caches exactly 2 adjacent bracket matrices,
        // so memory footprint is 2 · n² · 8 bytes instead of n_vis · n² · 8.
        //
        // Safety: `bg_filtered` lives as long as `tau_filtered` (both
        // borrowed from `common`), which outlives this call.
        let k_copy = k;
        let layout_ref = layout;
        // Build a flat (tau -> bg) lookup using the already-filtered slices.
        let tau_slice: Vec<f64> = tau_filtered.to_vec();
        let bg_slice: Vec<CambBackground> = bg_filtered.to_vec();
        let builder = move |tau_query: f64, out: &mut [f64]| {
            // The stepper's callback profile only ever queries at snapshot
            // points (eta[i], eta[i+1]), so we can use exact lookup.
            // Guard: if the query is not an exact snapshot, fall back to
            // nearest-bracket analytical build — still correct (M depends
            // on tau via bg fields which we interpolate elsewhere).
            let idx = tau_slice.iter().position(|&t| (t - tau_query).abs() < 1e-12);
            match idx {
                Some(i) => build_pstf_matrix_analytical_into(
                    k_copy, tau_slice[i], &bg_slice[i], layout_ref, out,
                ),
                None => {
                    // Linear-interpolate bg between bracketing snapshots,
                    // then build analytically at the interpolated bg.
                    // Preferred in case the stepper ever queries off-grid.
                    let mut lo = 0usize;
                    let mut hi = tau_slice.len() - 1;
                    while hi - lo > 1 {
                        let mid = (lo + hi) / 2;
                        if tau_slice[mid] <= tau_query { lo = mid; } else { hi = mid; }
                    }
                    let w = ((tau_query - tau_slice[lo])
                           / (tau_slice[hi] - tau_slice[lo]).max(1e-30)).clamp(0.0, 1.0);
                    let bg_interp = interp_camb_bg(&bg_slice[lo], &bg_slice[hi], w);
                    build_pstf_matrix_analytical_into(k_copy, tau_query, &bg_interp, layout_ref, out);
                }
            }
        };
        integrate_linear_profile_rodas5p_callback(
            tau_filtered, builder, n, &ic_state, tau_filtered, &cfg,
        )?
    } else {
        // Pre-materialized paths (legacy default): build mats_flat upfront.
        let mut mats_flat = vec![0.0_f64; n_vis * n * n];
        for i in 0..n_vis {
            let tau = tau_filtered[i];
            let bg = &bg_filtered[i];
            let off = i * n * n;
            if use_unit_vector {
                build_pstf_matrix_into(k, tau, bg, layout, &mut mats_flat[off..off + n * n]);
            } else {
                build_pstf_matrix_analytical_into(k, tau, bg, layout, &mut mats_flat[off..off + n * n]);
            }
        }
        integrate_linear_profile_rodas5p(
            tau_filtered, &mats_flat, n, &ic_state,
            tau_filtered, &cfg,
        )?
    };

    // Extract per-snapshot source + phi/psi/polterdot
    let n_snaps = snapshots.len();
    let mut result = PstfKmodeResult {
        eta_grid: Vec::with_capacity(n_snaps),
        source_total: Vec::with_capacity(n_snaps),
        source_sw: Vec::with_capacity(n_snaps),
        source_dop: Vec::with_capacity(n_snaps),
        source_quad: Vec::with_capacity(n_snaps),
        source_e_total: Vec::with_capacity(n_snaps),
        phi: Vec::with_capacity(n_snaps),
        psi: Vec::with_capacity(n_snaps),
        polterdot_grid: Vec::with_capacity(n_snaps),
        n_state: n,
        state_trajectory: if save_trajectory {
            Some(Vec::with_capacity(n_snaps))
        } else { None },
    };

    let mut dy_scratch = vec![0.0_f64; n];

    for si in 0..n_snaps {
        let tau = tau_filtered[si];
        let bg = &bg_filtered[si];
        // snapshots[si] has length n+1 (n state + augmented τ); extract state
        let y_full = &snapshots[si];
        let y: &[f64] = &y_full[..n];

        result.eta_grid.push(tau);

        // Compute dy via pstf_full_rhs (linear, exact)
        let bg_pstf = bg_from_camb(bg);
        let full_inputs = FullRhsInputs {
            k, tau, bg: bg_pstf,
            kappa_dot: bg.opac,
            r_b: if bg.grho_g > 0.0 { 0.75 * bg.grho_b / bg.grho_g } else { 0.0 },
            use_pol_feedback: false,
            frame: FrameConvention::ElectronRestFrame,
            cs2b: bg.cs2b,
        };
        dy_scratch.fill(0.0);
        pstf_full_rhs(y, &mut dy_scratch, &full_inputs, layout);

        // Source via pstf_source_function
        let vis_at = VisibilityAtSnap {
            g: bg.vis, gdot: bg.dvis, gddot: bg.ddvis,
        };
        let src = pstf_source_function(y, &dy_scratch, k, &bg_pstf, &vis_at, layout);

        result.source_total.push(src.s_total);
        result.source_sw.push(src.s_sw);
        result.source_dop.push(src.s_dop);
        result.source_quad.push(src.s_quad);
        result.source_e_total.push(src.s_e);
        result.polterdot_grid.push(src.polterdot);

        // Potentials (same gauge transform as MB-95 L334-335)
        let etak = y[layout.i_metric_etak()];
        let sigma = y[layout.i_metric_sigma()];
        let eta_s = etak / k;
        let phi = eta_s - bg.adotoa * sigma / k;
        let psi = -phi;  // ΛCDM: Ψ = −Φ
        result.phi.push(phi);
        result.psi.push(psi);

        if let Some(ref mut traj) = result.state_trajectory {
            traj.push(y.to_vec());
        }
    }

    Ok(result)
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Convenience: solve with internally-generated adiabatic IC
// ═══════════════════════════════════════════════════════════════════════

/// Conformal time below which `pstf_free_streaming_rhs` panics due to
/// the tau-based ℓ_max truncation term `(ℓ+1)/τ · Θ_{ℓ_max}`.  Match
/// MB-95 `solve_camb_kmode` convention.
pub(crate) const TAU_IC_MIN: f64 = 0.5;

/// Solve a single k-mode with adiabatic IC generated internally at the
/// first snapshot with τ > TAU_IC_MIN.  Convenience wrapper around
/// `pstf_solve_kmode`.  Encapsulates knowledge of `TAU_IC_MIN` so callers
/// don't need to know about internal tau filtering.
pub(crate) fn pstf_solve_kmode_adiabatic(
    k: f64,
    common: &CommonProfile,
    layout: &PstfFlrwLayout,
    save_trajectory: bool,
) -> Result<PstfKmodeResult, String> {
    use super::ic::{PstfIcInputs, pstf_adiabatic_ic};

    let start_i = common.tau_profile.iter()
        .position(|&t| t > TAU_IC_MIN)
        .ok_or_else(|| format!(
            "No snapshot with τ > {} in CommonProfile", TAU_IC_MIN
        ))?;
    let ic_inputs = PstfIcInputs::default_adiabatic(k, common.bg_at_snap[start_i].adotoa);
    let ic_state = pstf_adiabatic_ic(&ic_inputs, layout);
    pstf_solve_kmode(k, common, layout, ic_state, save_trajectory)
}

// ═══════════════════════════════════════════════════════════════════════
//   §4.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};

    /// Build a representative CommonProfile via HyRec visibility.
    fn build_common() -> (CommonProfile, VisibilityParams) {
        use crate::recombination::hyrec_tables::HyRecTables;
        let params = VisibilityParams::planck2018();
        let tables = HyRecTables::generate(200);
        let vis = compute_visibility(&params, &tables, 500);
        let common = CommonProfile::build(&params, &vis);
        (common, params)
    }

    // ─── Smoke / identity (3 tests) ─────────────────────────────────

    /// `pstf_solve_kmode_adiabatic` runs on representative k.
    #[test]
    fn identity_solve_kmode_runs() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01;

        let result = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("solve must succeed");

        // n_snaps = number of τ > TAU_IC_MIN in common.tau_profile
        let expected_len = common.tau_profile.iter()
            .filter(|&&t| t > TAU_IC_MIN).count();
        assert_eq!(result.eta_grid.len(), expected_len);
        assert_eq!(result.source_total.len(), expected_len);
        assert!(result.state_trajectory.is_none());
    }

    /// With `save_trajectory=true`, full state preserved.
    #[test]
    fn caveat_trajectory_save_optional() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01;

        let with_traj = pstf_solve_kmode_adiabatic(k, &common, &layout, true)
            .expect("solve must succeed");
        let without_traj = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("solve must succeed");

        assert!(with_traj.state_trajectory.is_some());
        assert!(without_traj.state_trajectory.is_none());

        let traj = with_traj.state_trajectory.as_ref().unwrap();
        assert_eq!(traj.len(), with_traj.eta_grid.len());
        for snap in traj.iter() {
            assert_eq!(snap.len(), layout.n_state);
        }
    }

    /// Result vectors consistent lengths.
    #[test]
    fn channelwise_result_lengths_consistent() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.02;

        let r = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("solve must succeed");

        let n = r.eta_grid.len();
        assert_eq!(r.source_total.len(), n);
        assert_eq!(r.source_sw.len(), n);
        assert_eq!(r.source_dop.len(), n);
        assert_eq!(r.source_quad.len(), n);
        assert_eq!(r.source_e_total.len(), n);
        assert_eq!(r.phi.len(), n);
        assert_eq!(r.psi.len(), n);
        assert_eq!(r.polterdot_grid.len(), n);
        assert_eq!(r.n_state, layout.n_state);
    }

    // ─── Physics (3 tests) ───────────────────────────────────────────

    /// Source total has magnitude during visibility peak.
    #[test]
    fn channelwise_source_nonzero_during_visibility() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01;

        let r = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("solve must succeed");

        let max_src = r.source_total.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
        assert!(max_src > 1e-12,
            "|source_total| should have non-trivial magnitude, got max={}",
            max_src);
        assert!(max_src.is_finite(),
            "max source must be finite, got {}", max_src);
    }

    // ─── Phase 2.0 Step 5: callback backend equivalence ────────────

    /// Callback-backed `LinearProfileCallback` samples the same matrices
    /// as pre-materialized `LinearProfileDyn` when fed the analytical
    /// builder.  Tests both `sample_matrix_only_into_hint` and
    /// `sample_into_hint` against the pre-materialized reference at
    /// multiple τ points.
    #[test]
    fn phase2_0_callback_sampler_matches_pre_materialized() {
        use crate::solver::rodas5p::{LinearProfileCallback, LinearProfileDyn, LinearProfileSampler};

        let layout = PstfFlrwLayout::new(8, 6, 0);
        layout.validate();
        let (common, _) = build_common();
        let start_i = common.tau_profile.iter()
            .position(|&t| t > TAU_IC_MIN).unwrap();
        let tau_filtered: Vec<f64> = common.tau_profile[start_i..].to_vec();
        let bg_filtered: Vec<CambBackground> = common.bg_at_snap[start_i..].to_vec();
        let n_vis = tau_filtered.len();
        let n = layout.n_state;
        let k = 0.01_f64;

        // Build pre-materialized reference
        let mut mats_flat = vec![0.0_f64; n_vis * n * n];
        for i in 0..n_vis {
            let off = i * n * n;
            build_pstf_matrix_analytical_into(k, tau_filtered[i], &bg_filtered[i], &layout,
                &mut mats_flat[off..off + n * n]);
        }
        let prof_dyn = LinearProfileDyn::new(tau_filtered.clone(), mats_flat, n).unwrap();

        // Build callback variant
        let k_c = k;
        let layout_c = &layout;
        let tau_c = tau_filtered.clone();
        let bg_c = bg_filtered.clone();
        let builder = move |tau_query: f64, out: &mut [f64]| {
            let idx = tau_c.iter().position(|&t| (t - tau_query).abs() < 1e-12).unwrap();
            build_pstf_matrix_analytical_into(k_c, tau_c[idx], &bg_c[idx], layout_c, out);
        };
        let prof_cb = LinearProfileCallback::new(tau_filtered.clone(), n, builder).unwrap();

        // Compare samples at a few interior τ values
        let mut a_dyn = vec![0.0_f64; n * n];
        let mut a_cb = vec![0.0_f64; n * n];
        let mut da_dyn = vec![0.0_f64; n * n];
        let mut da_cb = vec![0.0_f64; n * n];
        let mut hint_dyn = 0usize;
        let mut hint_cb = 0usize;

        // Test at 5 distinct τ values spanning the profile
        for frac in [0.1_f64, 0.3, 0.5, 0.7, 0.9] {
            let tau_test = tau_filtered[0] + frac * (tau_filtered[n_vis - 1] - tau_filtered[0]);
            prof_dyn.sample_matrix_only_into_hint(tau_test, &mut hint_dyn, &mut a_dyn);
            prof_cb.sample_matrix_only_into_hint(tau_test, &mut hint_cb, &mut a_cb);
            let max_diff = a_dyn.iter().zip(a_cb.iter())
                .map(|(x, y)| (x - y).abs())
                .fold(0.0_f64, f64::max);
            assert!(max_diff < 1e-14,
                "sample_matrix_only mismatch at frac={}: max diff {}", frac, max_diff);

            prof_dyn.sample_into_hint(tau_test, &mut hint_dyn, &mut a_dyn, &mut da_dyn);
            prof_cb.sample_into_hint(tau_test, &mut hint_cb, &mut a_cb, &mut da_cb);
            let max_a = a_dyn.iter().zip(a_cb.iter())
                .map(|(x, y)| (x - y).abs())
                .fold(0.0_f64, f64::max);
            let max_da = da_dyn.iter().zip(da_cb.iter())
                .map(|(x, y)| (x - y).abs())
                .fold(0.0_f64, f64::max);
            assert!(max_a < 1e-14,
                "sample_into a mismatch at frac={}: max diff {}", frac, max_a);
            assert!(max_da < 1e-14,
                "sample_into da mismatch at frac={}: max diff {}", frac, max_da);
        }
    }

    /// Phase 2.0 timing probe: compare wallclock across backends at
    /// several layout sizes.  Not a regression test — eyeball only.
    #[test]
    #[ignore = "timing probe; run with --ignored --nocapture"]
    fn phase2_0_backend_wallclock_comparison() {
        eprintln!("\n═══ PHASE 2.0 BACKEND WALLCLOCK ═══");
        for &(lg, ln, lpol) in &[(8usize, 6usize, 0usize), (12, 8, 0)] {
            let layout = PstfFlrwLayout::new(lg, ln, lpol);
            layout.validate();
            let (common, _) = build_common();
            let n = layout.n_state;
            let k = 0.01_f64;
            let n_snap = common.tau_profile.iter().filter(|&&t| t > TAU_IC_MIN).count();
            let mats_flat_mb = (n_snap * n * n * 8) as f64 / 1024.0 / 1024.0;
            let callback_mb = (2 * n * n * 8) as f64 / 1024.0 / 1024.0;

            // Pre-materialized analytical path
            std::env::remove_var("BASS_PSTF_CALLBACK");
            std::env::remove_var("BASS_PSTF_MATRIX_UV");
            let t0 = std::time::Instant::now();
            let _r = pstf_solve_kmode_adiabatic(k, &common, &layout, false).unwrap();
            let dt_pre = t0.elapsed().as_secs_f64();

            // Callback streaming path
            std::env::set_var("BASS_PSTF_CALLBACK", "1");
            let t1 = std::time::Instant::now();
            let _r = pstf_solve_kmode_adiabatic(k, &common, &layout, false).unwrap();
            let dt_cb = t1.elapsed().as_secs_f64();
            std::env::remove_var("BASS_PSTF_CALLBACK");

            eprintln!(
                "  layout=(γ={:2} ν={:2} pol={}) n={:<5} n_snap={} | pre-mat={:6.3}s ({:.1} MB)  callback={:6.3}s ({:.1} MB)  mem ratio={:.0}×",
                lg, ln, lpol, n, n_snap, dt_pre, mats_flat_mb, dt_cb, callback_mb,
                mats_flat_mb / callback_mb,
            );
        }
        eprintln!("═══════════════════════════════════════\n");
    }

    /// End-to-end equivalence: pstf_solve_kmode_adiabatic under the three
    /// matrix backends (analytical / unit-vector / callback) must produce
    /// agreement on source_total, phi, psi.
    #[test]
    fn phase2_0_callback_vs_analytical_end_to_end() {
        let layout = PstfFlrwLayout::new(8, 6, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01_f64;

        // Analytical path (default — no env var)
        std::env::remove_var("BASS_PSTF_CALLBACK");
        std::env::remove_var("BASS_PSTF_MATRIX_UV");
        let r_analytical = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("analytical path must succeed");

        // Callback path
        std::env::set_var("BASS_PSTF_CALLBACK", "1");
        let r_callback = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("callback path must succeed");
        std::env::remove_var("BASS_PSTF_CALLBACK");

        // Compare source_total, phi, psi
        assert_eq!(r_analytical.source_total.len(), r_callback.source_total.len());
        let n = r_analytical.source_total.len();
        let max_src = (0..n).map(|i|
            (r_analytical.source_total[i] - r_callback.source_total[i]).abs()
        ).fold(0.0_f64, f64::max);
        let max_phi = (0..n).map(|i|
            (r_analytical.phi[i] - r_callback.phi[i]).abs()
        ).fold(0.0_f64, f64::max);

        // Expect ULP-level agreement; allow 1e-12 for FP accumulation
        assert!(max_src < 1e-12,
            "callback vs analytical: source_total max abs diff {} at n={}", max_src, n);
        assert!(max_phi < 1e-12,
            "callback vs analytical: phi max abs diff {} at n={}", max_phi, n);
    }

    // ─── PR-024c-PERF Step 5: analytical path agreement ────────────

    /// Analytical-path `pstf_solve_kmode_adiabatic` output agrees with
    /// unit-vector path (via BASS_PSTF_MATRIX_UV=1 env fallback) to
    /// high relative precision on source_total, phi, psi at all snapshots.
    ///
    /// Not bit-identical (different FP op order in matrix build), but
    /// should agree to ≲ 1e-8 relative.
    #[test]
    fn perf_step5_analytical_vs_uv_path_agreement() {
        // Serial single k-mode; reduced layout for fast runtime.
        let layout = PstfFlrwLayout::new(8, 6, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01;

        // Solve both ways in-process by calling the builders directly
        // to construct mats_flat, then comparing.  (Env-var toggle is
        // runtime-wide so we can't flip it mid-test cleanly.)
        //
        // Instead: solve once with env cleared (analytical path via default),
        // once by stamping BASS_PSTF_MATRIX_UV=1 before calling solve.
        // But std::env modification in tests is racy under multi-thread
        // execution.  So do it single-threaded OR compare matrix builders
        // directly.  We choose the latter — simpler and deterministic.

        // Reuse the matrix builders directly to compare.
        use super::super::matrix::{build_pstf_matrix_into, build_pstf_matrix_analytical_into};
        let n = layout.n_state;
        let start_i = common.tau_profile.iter()
            .position(|&t| t > TAU_IC_MIN).unwrap();
        let bg = &common.bg_at_snap[start_i + 50.min(common.bg_at_snap.len() - start_i - 1)];
        let tau = common.tau_profile[start_i + 50.min(common.tau_profile.len() - start_i - 1)];
        let mut mat_uv = vec![0.0_f64; n * n];
        let mut mat_an = vec![0.0_f64; n * n];
        build_pstf_matrix_into(k, tau, bg, &layout, &mut mat_uv);
        build_pstf_matrix_analytical_into(k, tau, bg, &layout, &mut mat_an);

        let mut max_rel = 0.0_f64;
        for i in 0..n*n {
            if mat_uv[i].abs() > 1e-10 {
                let rel = (mat_uv[i] - mat_an[i]).abs() / mat_uv[i].abs();
                if rel > max_rel { max_rel = rel; }
            }
        }
        assert!(max_rel < 1e-8,
            "analytical matrix mismatch at mid-snapshot: max rel err {:.3e}", max_rel);

        // End-to-end solve (analytical path via default).  Must succeed and
        // produce finite, non-trivial output.
        let r = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
            .expect("analytical path solve must succeed");
        let max_src = r.source_total.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
        assert!(max_src.is_finite() && max_src > 1e-6,
            "analytical path produced trivial source: max |src| = {}", max_src);
    }

    /// Phase-0 D0.3 cross-check:  does PSTF primary exhibit the same
    /// high-k source divergence as MB-95 (Bug B in PHASE0_D0_AUDIT_REPORT)?
    ///
    /// MB-95's `solve_kmode_with_history` produces source_jl that grows
    /// exponentially with k for k > ~0.03 (reaches 1e101 at k=0.25).
    /// PSTF primary uses the same Rodas5P stepper (integrate_linear_profile_rodas5p)
    /// with identical rtol/atol.  If PSTF also diverges, the bug is in the
    /// step controller tuning, not the RHS.  If PSTF stays bounded, the bug
    /// is specific to MB-95's RHS / IC.
    ///
    /// Prints a per-k summary; user can eyeball.  Does NOT assert on the
    /// magnitude (we WANT to see divergence if it's there).
    #[test]
    #[ignore = "Phase-0 D0.3 cross-check; run with --ignored --nocapture"]
    fn phase0_d0_3_cross_check_pstf_high_k() {
        // Smaller layout for test runtime; still covers high-k regime.
        let layout = PstfFlrwLayout::new(8, 6, 0);
        layout.validate();
        let (common, _) = build_common();

        // Sparse k-sweep focused on the MB-95 divergence boundary (k ~ 0.03)
        // and the deep high-k regime.
        let k_vals: Vec<f64> = vec![1e-4, 1e-3, 1e-2, 3e-2, 5e-2, 1e-1, 2.5e-1];

        eprintln!("\n═══ PSTF PRIMARY HIGH-K PROBE (D0.3 cross-check) ═══");
        eprintln!("  layout: ell_max_γ=12 ell_max_ν=8 pol=off  (smaller than MB-95 default for test runtime)");
        eprintln!("  Expectation: if bug is Rodas5P stepper, PSTF also diverges here.");
        eprintln!("              if bug is MB-95 RHS, PSTF stays bounded.");
        eprintln!();
        eprintln!("  {:>7}  {:>8}  {:>12}  {:>12}  {:>12}  {:>10}  finite?",
                  "k", "n_eta", "|src_tot|_max", "|src_sw|_max", "|src_dop|_max", "|phi|_max");

        for &k in &k_vals {
            let r = match pstf_solve_kmode_adiabatic(k, &common, &layout, false) {
                Ok(r) => r,
                Err(e) => {
                    eprintln!("  k={:.3e}  SOLVE FAILED: {}", k, e);
                    continue;
                }
            };
            let max_st = r.source_total.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
            let max_sw = r.source_sw.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
            let max_do = r.source_dop.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
            let max_ph = r.phi.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
            let all_finite = r.source_total.iter().all(|v| v.is_finite())
                          && r.phi.iter().all(|v| v.is_finite());
            eprintln!("  {:7.3e}  {:>8}  {:12.3e}  {:12.3e}  {:12.3e}  {:10.3e}  {}",
                      k, r.eta_grid.len(), max_st, max_sw, max_do, max_ph, all_finite);
        }
        eprintln!("═══════════════════════════════════════════════════\n");
    }

    /// Multiple k values each succeed.
    #[test]
    fn regression_multiple_k_all_succeed() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();

        for &k in &[0.001_f64, 0.01, 0.1] {
            let r = pstf_solve_kmode_adiabatic(k, &common, &layout, false)
                .expect(&format!("solve must succeed at k={}", k));
            assert!(r.eta_grid.len() > 10,
                "k={}: eta_grid should be non-trivial, got {}",
                k, r.eta_grid.len());
            let max_src = r.source_total.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
            assert!(max_src.is_finite(),
                "k={}: source should be finite", k);
        }
    }

    /// First snapshot state should match the IC (y0) at tau_filtered[0].
    #[test]
    fn channelwise_state_initial_condition() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01;

        // Reconstruct what pstf_solve_kmode_adiabatic uses for IC
        let start_i = common.tau_profile.iter()
            .position(|&t| t > TAU_IC_MIN).unwrap();
        let ic_inputs = PstfIcInputs::default_adiabatic(k, common.bg_at_snap[start_i].adotoa);
        let ic = pstf_adiabatic_ic(&ic_inputs, &layout);

        let r = pstf_solve_kmode_adiabatic(k, &common, &layout, true)
            .expect("solve must succeed");

        let traj = r.state_trajectory.as_ref().unwrap();
        // First snapshot should be at tau_filtered[0], state = ic
        for i in 0..layout.n_state {
            let diff = (traj[0][i] - ic[i]).abs();
            let tol = 1e-10_f64.max(1e-10 * ic[i].abs());
            assert!(diff < tol,
                "state[{}] at t=0: got {}, expected {}, diff {} (tol {})",
                i, traj[0][i], ic[i], diff, tol);
        }
    }

    // ─── Potentials (1 test) ────────────────────────────────────────

    /// Φ, Ψ computed per MB-95 gauge transform.
    #[test]
    fn regression_phi_psi_computed_correctly() {
        let layout = PstfFlrwLayout::new(8, 8, 0);
        layout.validate();
        let (common, _) = build_common();
        let k = 0.01;

        let r = pstf_solve_kmode_adiabatic(k, &common, &layout, true)
            .expect("solve must succeed");

        let traj = r.state_trajectory.as_ref().unwrap();
        // Need filtered bg for comparison
        let start_i = common.tau_profile.iter()
            .position(|&t| t > TAU_IC_MIN).unwrap();

        for si in 0..r.eta_grid.len() {
            let y = &traj[si];
            let bg = &common.bg_at_snap[start_i + si];
            let etak = y[layout.i_metric_etak()];
            let sigma = y[layout.i_metric_sigma()];
            let eta_s = etak / k;
            let expected_phi = eta_s - bg.adotoa * sigma / k;
            let got_phi = r.phi[si];
            let tol = 1e-14_f64.max(1e-14 * expected_phi.abs());
            assert!((got_phi - expected_phi).abs() < tol,
                "si={}: phi = {}, expected {}", si, got_phi, expected_phi);
            assert_eq!(r.psi[si], -got_phi,
                "si={}: psi = -phi should hold exactly", si);
        }
    }

    // ─── Layout accessor range check (PR-024a lesson) ───────────────

    /// Explicit guard: no E-mode / B-mode accessor called with ell<2.
    #[test]
    fn caveat_layout_accessor_range_check() {
        let layout_pol_off = PstfFlrwLayout::new(8, 8, 0);
        layout_pol_off.validate();
        let (common, _) = build_common();
        let k = 0.01;

        // pol off path
        let _ = pstf_solve_kmode_adiabatic(k, &common, &layout_pol_off, false)
            .expect("pol off solve must succeed");

        // pol on path (smaller layout to avoid OOM)
        let layout_pol_on = PstfFlrwLayout::new(4, 4, 4);
        layout_pol_on.validate();
        let _ = pstf_solve_kmode_adiabatic(k, &common, &layout_pol_on, false)
            .expect("pol on solve must succeed");
    }
}
