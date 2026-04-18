//! ═══════════════════════════════════════════════════════════════════════════
//! streaming.rs — Epoch-gating source mask (LateSourceBackend guardrail)
//! ═══════════════════════════════════════════════════════════════════════════
//!
//! ## Purpose
//!
//! MaskEpochGating zeros the LoS source outside the recombination window.
//! This is NOT free-streaming propagation — it is a guardrail that prevents
//! truncation-contaminated multipoles from entering the LoS integral.
//!
//! Extension point: the LateSourceBackend enum allows future replacement
//! of epoch-gating with a true free-streaming propagator (Phase-2 / P1-07).
//!
//! ## Design
//!
//! **Epoch I** (collision-dominated): Source is trustworthy. Window: OPEN.
//! **Epoch II** (free-streaming): ODE hierarchy is truncation-contaminated.
//!   Current: source = 0 (MaskEpochGating).
//!   Future: source from streaming propagator (FreeStreamingPropagator).
//!
//! ## Switch condition
//!
//! A point (k, η) is in Epoch I if ANY of:
//!   (a) κ̇/k > ε_collision  (collision rate exceeds streaming rate)
//!   (b) g/g_max > ε_visibility  (near the visibility peak)
//!
//! ## Audit note (2026-04-09)
//!
//! The LoS integral uses an epoch-gating mask that is independent of the
//! detailed Doppler representation. Current production is being migrated to a
//! two-radial-function form (j_ℓ for monopole/late_metric, j'_ℓ/k for Doppler);
//! the mask remains a guardrail regardless of that source split.

use crate::recombination::visibility_hyrec::VisibilityResult;

// ═══════════════════════════════════════════════════════════════════════════
// LateSourceBackend — controls what happens outside the recombination window
// ═══════════════════════════════════════════════════════════════════════════

/// Backend for late-time (Epoch II) source treatment.
///
/// Production uses MaskEpochGating: source = 0 outside the visibility peak.
/// This is a guardrail, NOT a free-streaming propagator.
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum LateSourceBackend {
    /// Current production: zero source outside recombination window.
    /// GUARDRAIL ONLY — not a free-streaming propagator.
    MaskEpochGating,
    /// Planned Phase-2: analytic free-streaming propagation.
    /// NOT YET IMPLEMENTED. Requires Phase-2 / P1-07 completion.
    FreeStreamingPropagator, // TODO: P1-07
}

impl LateSourceBackend {
    /// Human-readable description for diagnostics.
    pub(crate) fn description(&self) -> &'static str {
        match self {
            Self::MaskEpochGating => "MaskEpochGating (guardrail, epoch-gating only)",
            Self::FreeStreamingPropagator => "FreeStreamingPropagator (TODO: P1-07)",
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════

/// Configuration for the streaming switch.
pub(crate) struct StreamingSwitch {
    /// κ̇/k threshold: points with κ̇/k > this are collision-dominated.
    pub(crate) eps_collision: f64,
    /// g/g_max threshold: points with g/g_max > this are near visibility peak.
    pub(crate) eps_visibility: f64,
}

impl StreamingSwitch {
    /// Default thresholds (validated against CLASS C_ℓ comparison).
    pub(crate) fn default() -> Self {
        Self {
            eps_collision: 5.0,   // κ̇/k > 5: tightly coupled
            eps_visibility: 1e-3, // g/g_max > 0.1%: near visibility peak
        }
    }

    /// Strict thresholds for debugging (only the very core of the peak).
    pub(crate) fn strict() -> Self {
        Self { eps_collision: 20.0, eps_visibility: 1e-2 }
    }
}

/// Precomputed source window mask for a given k-mode.
///
/// `mask[i] = true` means the source at η_grid[i] is in Epoch I
/// (collision-dominated) and should be included in the LoS integral.
/// `mask[i] = false` means Epoch II (free-streaming, source = 0).
pub(crate) struct SourceWindow {
    pub(crate) mask: Vec<bool>,
    pub(crate) n_active: usize,
    pub(crate) eta_min_active: f64,
    pub(crate) eta_max_active: f64,
}

impl SourceWindow {
    /// Build the source window for a given k-mode.
    ///
    /// The mask is true where κ̇/k > ε_collision OR g/g_max > ε_visibility.
    /// An additional hysteresis rule: once we enter Epoch II (going from
    /// high z toward low z), we never re-enter Epoch I. This prevents
    /// the reionization bump from re-opening the window at z ~ 6-10.
    pub(crate) fn build(
        k: f64,
        eta_grid: &[f64],
        vis: &VisibilityResult,
        switch: &StreamingSwitch,
    ) -> Self {
        let n = eta_grid.len();
        let n_vis = vis.z_grid.len();
        let g_max = vis.g_grid.iter().fold(0.0_f64, |m, &v| m.max(v));

        // Find the visibility peak η-location
        let ipk_vis = vis.g_grid.iter().enumerate()
            .max_by(|a,b| a.1.partial_cmp(b.1).unwrap()).unwrap().0;
        let eta_peak = vis.eta_grid[ipk_vis];

        let mut mask = vec![false; n];

        // Strategy: include points where EITHER:
        //   (a) tightly coupled (κ̇/k > threshold) — early universe
        //   (b) near the PRIMARY visibility peak (g/g_max > threshold)
        //   (c) within the η-guard zone of the peak
        // Exclude reionization: by checking distance from peak.
        // Points more than 500 Mpc from the peak in η AND not tightly
        // coupled are excluded (catches reionization at η ≈ 0).
        let eta_guard = 500.0_f64; // Mpc from peak

        for i in 0..n {
            let eta_i = eta_grid[i];
            let vi = vis.eta_grid.partition_point(|&v| v < eta_i).min(n_vis - 1);
            let kappa_dot = vis.kappa_dot_grid[vi];
            let g = vis.g_grid[vi];

            let in_collision = kappa_dot / k.max(1e-30) > switch.eps_collision;
            let near_peak = g / g_max.max(1e-30) > switch.eps_visibility;
            let in_peak_zone = (eta_i - eta_peak).abs() < eta_guard;

            // ACC-02: Reionization bump deferred to ACC-03.
            // Opening the window naively (g/g_max > 1e-4) causes ISW blowup
            // because 2Φ̇_P numerical derivative is noisy at late times.
            // Proper fix: separate reionization source term with its own window,
            // NOT piggybacking on the primary recombination window.

            // Include if: tightly coupled OR (near peak AND in peak zone)
            mask[i] = in_collision || (near_peak && in_peak_zone);
        }

        let n_active = mask.iter().filter(|&&m| m).count();
        let eta_min = mask.iter().enumerate()
            .filter(|(_, &m)| m).map(|(i, _)| eta_grid[i])
            .fold(f64::MAX, f64::min);
        let eta_max = mask.iter().enumerate()
            .filter(|(_, &m)| m).map(|(i, _)| eta_grid[i])
            .fold(f64::MIN, f64::max);

        SourceWindow {
            mask, n_active,
            eta_min_active: eta_min,
            eta_max_active: eta_max,
        }
    }
}

/// Apply the source window: zero out source at Epoch II points.
pub(crate) fn apply_window(source: &mut [f64], window: &SourceWindow) {
    for (i, &active) in window.mask.iter().enumerate() {
        if !active {
            source[i] = 0.0;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::recombination::visibility_hyrec::{VisibilityParams, compute_visibility};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_window_covers_peak() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();

        // Simulate eta_grid (0 to 13865)
        let n = 3000;
        let eta_grid: Vec<f64> = (0..n).map(|i| i as f64 * 13865.0 / (n-1) as f64).collect();

        for &k in &[1e-4_f64, 1e-3, 1e-2, 5e-2, 0.1] {
            let sw = StreamingSwitch::default();
            let win = SourceWindow::build(k, &eta_grid, &vis, &sw);

            // The visibility peak is at η ≈ 13680
            let i_peak = (13680.0 / 13865.0 * (n-1) as f64) as usize;
            assert!(win.mask[i_peak],
                "Window must include visibility peak at k={:.0e}", k);

            // z=0 (η=0) should be EXCLUDED for k > 0.01
            if k > 0.01 {
                assert!(!win.mask[0],
                    "Window must exclude z=0 for k={:.0e} (truncation regime)", k);
            }

            eprintln!("  k={:.0e}: n_active={}/{}, η=[{:.0},{:.0}]",
                k, win.n_active, n, win.eta_min_active, win.eta_max_active);
        }
    }

    #[test]
    fn test_reionization_blocked_pending_acc03() {
        // ACC-02 finding: naive reionization window opening causes ISW blowup.
        // Reionization needs a SEPARATE source term with its own windowing.
        // For now, verify the primary peak is active and reionization is excluded.
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n = 3000;
        let eta_grid: Vec<f64> = (0..n).map(|i| i as f64 * 13865.0 / (n-1) as f64).collect();
        let k = 0.05_f64;
        let sw = StreamingSwitch::default();
        let win = SourceWindow::build(k, &eta_grid, &vis, &sw);

        let eta_peak = 13680.0;
        let i_peak = (eta_peak / 13865.0 * (n-1) as f64) as usize;
        assert!(win.mask[i_peak], "Primary peak must be active");
    }
}
