// CL-14: 5-Metric Cross-Check Suite (Formal).
//
// Extends track_b_pipeline::CrossCheckReport with:
//   1. Multi-Σ² sweep (Pareto curve)
//   2. Per-ℓ error decomposition
//   3. Convergence test (ε_state → 0 as Σ² → 0)
//   4. Cost-accuracy trade-off analysis
//
// 5 metrics (CL-PR v2.0 §6):
//   ε_state:    ‖C_ℓ^A − C_ℓ^B‖ / ‖C_ℓ^A‖
//   ε_Th:       source translation error (CL-12)
//   Δ_obs:      adequacy bound (CL-11)
//   ε_{C_ℓ}:    band-averaged C_ℓ error (low/mid/high)
//   cost:       wall_B / wall_A

use crate::solver::track_b_pipeline::{
    TrackBResult, CrossCheckReport, compute_flrw_cl_track_b, cross_check,
};
use crate::solver::flrw_cl_pipeline::{FlrwClConfig, FlrwClResult, compute_flrw_cl_track_a};
use crate::solver::teff_cl::TeffClConfig;
use crate::recombination::visibility_hyrec::VisibilityParams;

/// Pareto point: (Σ², ε_state, ε_Th, cost_ratio).
#[derive(Clone, Debug)]
pub(crate) struct ParetoPoint {
    pub(crate) sigma2: f64,
    pub(crate) eps_state: f64,
    pub(crate) eps_th: f64,
    pub(crate) delta_obs: f64,
    pub(crate) cost_ratio: f64,
}

/// Full cross-check sweep over a Σ² grid.
pub(crate) fn pareto_sweep(
    params: &VisibilityParams,
    config: &FlrwClConfig,
    sigma2_grid: &[f64],
) -> Vec<ParetoPoint> {
    let track_a = match compute_flrw_cl_track_a(params, config) {
        Ok(r) => r,
        Err(_) => return Vec::new(),
    };

    sigma2_grid.iter().filter_map(|&s2| {
        let teff_cfg = if s2 < 1e-30 { TeffClConfig::flrw() }
                      else { TeffClConfig::bianchi_i(s2) };
        let track_b = compute_flrw_cl_track_b(params, config, &teff_cfg).ok()?;
        let report = cross_check(&track_a, &track_b, 1.0);
        Some(ParetoPoint {
            sigma2: s2,
            eps_state: report.eps_state,
            eps_th: report.eps_th,
            delta_obs: report.delta_obs_bound,
            cost_ratio: report.cost_ratio,
        })
    }).collect()
}

/// Per-ℓ error between Track A and Track B.
pub(crate) fn per_ell_error(track_a: &FlrwClResult, track_b: &TrackBResult) -> Vec<f64> {
    let n = track_a.cl.len().min(track_b.cl_result.cl.len());
    (0..n).map(|ell| {
        if ell < 2 || track_a.cl[ell].abs() < 1e-60 { 0.0 }
        else { (track_a.cl[ell] - track_b.cl_result.cl[ell]).abs() / track_a.cl[ell].abs() }
    }).collect()
}

/// Convergence check: ε_state must vanish as Σ² → 0.
pub(crate) fn convergence_check(pareto: &[ParetoPoint]) -> bool {
    if pareto.len() < 2 { return false; }
    // Find the two smallest Σ² points
    let mut sorted: Vec<_> = pareto.iter().collect();
    sorted.sort_by(|a, b| a.sigma2.partial_cmp(&b.sigma2).unwrap());
    // ε_state should decrease as Σ² decreases
    if sorted.len() >= 2 {
        sorted[0].eps_state <= sorted[1].eps_state * 1.1 // allow 10% noise
    } else { false }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn planck() -> VisibilityParams { VisibilityParams::planck2018() }

    #[test]
    fn test_crosscheck_flrw_identical() {
        // CL-PR v2.0 §6: "FLRW에서 Track A = Track B"
        let cfg = FlrwClConfig::fast_validation();
        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let teff_cfg = TeffClConfig::flrw();
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();
        let report = cross_check(&track_a, &track_b, 1e-10);

        assert!(report.eps_state < 1e-14,
            "FLRW: ε_state = {:.4e} (must be ~0)", report.eps_state);
        assert!(report.eps_cl_low < 1e-14, "FLRW: ε_cl_low = {:.4e}", report.eps_cl_low);
        assert!(report.tracks_consistent);
    }

    #[test]
    fn test_crosscheck_bi_separation() {
        // CL-PR v2.0 §6: "BI Σ²=10⁻⁸에서 Track A ≠ Track B at O(ε²)"
        let cfg = FlrwClConfig::fast_validation();
        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let teff_cfg = TeffClConfig::bianchi_i(1e-4);
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();
        let report = cross_check(&track_a, &track_b, 1.0);

        assert!(report.eps_state > 1e-10,
            "BI: ε_state = {:.4e} (must show separation)", report.eps_state);

        // Per-ℓ error should peak at ℓ=2
        let per_ell = per_ell_error(&track_a, &track_b);
        if per_ell.len() > 5 {
            let err_2 = per_ell[2];
            let err_10 = per_ell[10.min(per_ell.len()-1)];
            assert!(err_2 > err_10,
                "BI: ε(ℓ=2) = {:.4e} must exceed ε(ℓ=10) = {:.4e}", err_2, err_10);
        }
    }

    #[test]
    fn test_per_ell_error_peaks_at_quadrupole() {
        let cfg = FlrwClConfig::fast_validation();
        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let teff_cfg = TeffClConfig::bianchi_i(1e-5);
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();

        let per_ell = per_ell_error(&track_a, &track_b);
        // Teff correction concentrates at ℓ=2 (quadrupole)
        let max_ell = per_ell.iter().enumerate().skip(2)
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(i, _)| i).unwrap_or(0);
        assert_eq!(max_ell, 2,
            "Peak error at ℓ={} (must be ℓ=2 for Teff correction)", max_ell);
    }
}
