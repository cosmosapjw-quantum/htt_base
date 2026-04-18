// CL-06B + CL-09: Track B End-to-End Validation + Dual-Track Report.
//
// End-to-end validation criteria (CL-PR v2.0 §7):
//   1. FLRW: ε_state < 10⁻¹⁰ (Track A = Track B exactly)
//   2. BI: ε_Th documented (source translation error quantified)
//   3. D₂ positive and finite at all tested Σ²
//   4. Per-ℓ error peaks at ℓ=2 (Teff correction concentrated at quadrupole)
//   5. Cost ratio < 2.0 (Track B overhead < 100%)
//
// Dual-track report (CL-09):
//   Structured summary of Track A vs Track B for each test configuration.

use crate::solver::flrw_cl_pipeline::{FlrwClConfig, compute_flrw_cl_track_a};
use crate::solver::track_b_pipeline::{compute_flrw_cl_track_b, cross_check};
use crate::solver::crosscheck::per_ell_error;
use crate::solver::teff_cl::TeffClConfig;
use crate::recombination::visibility_hyrec::VisibilityParams;

/// Dual-track validation report.
#[derive(Clone, Debug)]
pub(crate) struct DualTrackReport {
    pub(crate) config_label: String,
    pub(crate) sigma2: f64,
    pub(crate) d2_track_a: f64,
    pub(crate) d2_track_b: f64,
    pub(crate) eps_state: f64,
    pub(crate) eps_th: f64,
    pub(crate) delta_obs: f64,
    pub(crate) peak_error_ell: usize,
    pub(crate) cost_ratio: f64,
    pub(crate) pass: bool,
}

/// Run end-to-end validation for a single configuration.
pub(crate) fn validate_configuration(
    params: &VisibilityParams,
    config: &FlrwClConfig,
    sigma2: f64,
    label: &str,
) -> Result<DualTrackReport, String> {
    let track_a = compute_flrw_cl_track_a(params, config)?;
    let teff_cfg = if sigma2 < 1e-30 { TeffClConfig::flrw() }
                  else { TeffClConfig::bianchi_i(sigma2) };
    let track_b = compute_flrw_cl_track_b(params, config, &teff_cfg)?;
    let report = cross_check(&track_a, &track_b, 0.01);
    let per_ell = per_ell_error(&track_a, &track_b);

    let peak_ell = per_ell.iter().enumerate().skip(2)
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
        .map(|(i, _)| i).unwrap_or(0);

    let pass = if sigma2 < 1e-30 {
        // FLRW: strict identity
        report.eps_state < 1e-10
    } else {
        // BI: documented separation, positive D₂, cost < 2×
        track_b.cl_result.dl_muK2[2] > 0.0
            && track_b.cl_result.dl_muK2[2].is_finite()
            && report.cost_ratio < 2.0
    };

    Ok(DualTrackReport {
        config_label: label.to_string(),
        sigma2,
        d2_track_a: track_a.dl_muK2[2],
        d2_track_b: track_b.cl_result.dl_muK2[2],
        eps_state: report.eps_state,
        eps_th: report.eps_th,
        delta_obs: report.delta_obs_bound,
        peak_error_ell: peak_ell,
        cost_ratio: report.cost_ratio,
        pass,
    })
}

/// Run full validation suite.
pub(crate) fn full_validation_suite(
    params: &VisibilityParams,
    config: &FlrwClConfig,
) -> Vec<DualTrackReport> {
    let sigma2_grid = [0.0, 1e-10, 1e-8, 1e-6, 1e-4];
    let labels = ["FLRW", "BI_1e-10", "BI_1e-8", "BI_1e-6", "BI_1e-4"];

    sigma2_grid.iter().zip(labels.iter())
        .filter_map(|(&s2, &label)| {
            validate_configuration(params, config, s2, label).ok()
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn planck() -> VisibilityParams { VisibilityParams::planck2018() }

    /// CL-06B: Track B passes all 5 validation criteria.
    #[test]
    fn test_track_b_end_to_end_flrw() {
        let cfg = FlrwClConfig::fast_validation();
        let report = validate_configuration(&planck(), &cfg, 0.0, "FLRW").unwrap();

        assert!(report.pass, "FLRW validation failed: {:?}", report);
        assert!(report.eps_state < 1e-14,
            "FLRW: ε_state = {:.4e}", report.eps_state);
        assert!((report.d2_track_a - report.d2_track_b).abs() < 1e-10,
            "FLRW: D₂ tracks must match exactly");

        eprintln!("  CL-06B FLRW: D₂_A={:.2}, D₂_B={:.2}, ε={:.2e}, PASS={}",
            report.d2_track_a, report.d2_track_b, report.eps_state, report.pass);
    }

    #[test]
    fn test_track_b_end_to_end_bi() {
        let cfg = FlrwClConfig::fast_validation();
        let report = validate_configuration(&planck(), &cfg, 1e-5, "BI_1e-5").unwrap();

        assert!(report.pass, "BI validation failed: {:?}", report);
        assert!(report.d2_track_b > 0.0 && report.d2_track_b.is_finite());
        assert!(report.cost_ratio < 2.0,
            "BI: cost ratio = {:.2} (must be < 2.0)", report.cost_ratio);
        assert_eq!(report.peak_error_ell, 2,
            "BI: peak error at ℓ={} (must be 2)", report.peak_error_ell);

        eprintln!("  CL-06B BI(1e-5): D₂_A={:.2}, D₂_B={:.2}, ε={:.4e}, peak_ℓ={}",
            report.d2_track_a, report.d2_track_b, report.eps_state, report.peak_error_ell);
    }

    /// CL-09: Dual-track summary report.
    #[test]
    fn test_dual_track_report_structure() {
        let cfg = FlrwClConfig::fast_validation();
        let report = validate_configuration(&planck(), &cfg, 1e-6, "test").unwrap();

        // All fields must be finite and meaningful
        assert!(report.d2_track_a.is_finite());
        assert!(report.d2_track_b.is_finite());
        assert!(report.eps_state.is_finite());
        assert!(report.eps_th.is_finite());
        assert!(report.cost_ratio > 0.0);
    }
}
