// CL-13 + CL-04B: Track B C_ℓ Pipeline (Teff-Backed) + Cross-Check Layer.
//
// Architecture (CL-PR v2.0 §1):
//   Track B reuses Track A infrastructure (k-mode solver, LoS, Limber)
//   but applies the Teff source correction at the quadrupole level:
//
//     S^{Track B}(k,η) = S^{Track A}(k,η) + ΔS^{Teff}(k,η)
//
//   where ΔS^{Teff} = −κ̇ × (I_{ab}^{Θ⁴} − I_{ab}^{linear})
//
// In FLRW (Σ² = 0): ΔS = 0 → Track A = Track B (exact).
// In BI (Σ² > 0): ΔS ∝ Σ² → Track B captures dipole²→quadrupole.
//
// 5 error metrics (CL-14):
//   ε_state:    |F_ℓ^A − F_ℓ^B| / |F_ℓ^A|
//   ε_Th:       |S^{Teff} − S^{linear}| / |S^{Teff}|
//   Δ_obs:      C(ξ,L) × D_{≥2} / σ_min(J)
//   ε_{C_ℓ}:    |C_ℓ^A − C_ℓ^B| / C_ℓ^A
//   cost ratio:  wall_B / wall_A

use super::flrw_cl_pipeline::{FlrwClConfig, FlrwClResult, compute_flrw_cl_track_a};
use crate::solver::teff_cl::{
    TeffClConfig, TeffDiagnostics, delta_f2_teff, compute_d_ge2, adequacy_bound,
    apply_teff_correction,
};
use crate::teff::theta4_bridge_v2::{corrected_a2, eps_th_linear, eps_th_quadratic};
use crate::recombination::visibility_hyrec::VisibilityParams;
use std::f64::consts::PI;

// ═══ Track B pipeline ═══

/// Track B result: Track A C_ℓ + Teff diagnostics.
#[derive(Clone)]
pub(crate) struct TrackBResult {
    /// C_ℓ result (same structure as Track A).
    pub(crate) cl_result: FlrwClResult,
    /// Teff diagnostics.
    pub(crate) diagnostics: TeffDiagnostics,
    /// Source correction amplitude at each ℓ: ΔC_ℓ/C_ℓ.
    pub(crate) relative_correction: Vec<f64>,
}

/// Compute FLRW C_ℓ via Track B (Teff-backed).
///
/// Track B = Track A + Teff source correction.
/// In FLRW: correction = 0 → identical to Track A.
pub(crate) fn compute_flrw_cl_track_b(
    params: &VisibilityParams,
    config: &FlrwClConfig,
    teff_config: &TeffClConfig,
) -> Result<TrackBResult, String> {
    // Step 1: Run Track A to get the baseline C_ℓ
    let track_a = compute_flrw_cl_track_a(params, config)?;

    // Step 2: Apply Teff PERTURBATIVE correction to C_ℓ.
    //
    // PHYSICS STATUS: This is a FIRST-ORDER PERTURBATIVE correction,
    // NOT a full Track B re-solve. A proper Track B requires modifying
    // the Thomson collision integral in the Boltzmann hierarchy (flrw_kmode.rs)
    // to include the Teff quadrupole source ΔF₂, then re-integrating the
    // line-of-sight integral. The perturbative correction is valid when
    // |ΔF₂| ≪ F₂, i.e. Σ² ≲ 10⁻⁴.
    //
    // Derivation (first-order perturbation in ΔF₂):
    //   C_ℓ = |Δ_ℓ|² where Δ_ℓ(k) = ∫ S(k,η) jℓ(k(η₀-η)) dη
    //   δC_ℓ/C_ℓ = 2 × δΔ_ℓ/Δ_ℓ (from |Δ+δΔ|² ≈ |Δ|² + 2Re(Δ*δΔ))
    //
    // The Teff correction adds δS₂ = ΔF₂ × g(η) to the ℓ=2 source.
    // Through the LoS integral, this contributes to C_ℓ at all ℓ via the
    // Bessel overlap ∫ g(η) j₂(x) jℓ(x) dη, which peaks at ℓ=2 and
    // falls off as ℓ(ℓ+1)|_{ℓ=2} / [ℓ(ℓ+1)] = 6/[ℓ(ℓ+1)] for ℓ>2.
    //
    // Net correction: δC_ℓ/C_ℓ ≈ 2 × ΔF₂ × 6/[ℓ(ℓ+1)]
    //   At ℓ=2: δC₂/C₂ = 2 × ΔF₂ (full quadrupole modification)
    //   At ℓ=3: δC₃/C₃ = 2 × ΔF₂ × 6/12 = ΔF₂ (cascade coupling)
    //   At ℓ≥4: rapidly negligible
    let df2 = delta_f2_teff(teff_config.sigma2);

    let mut cl_b = track_a.cl.clone();
    let mut relative_correction = vec![0.0_f64; config.ell_max + 1];

    if teff_config.sigma2 > 1e-30 {
        for ell in 2..=config.ell_max {
            let ell_f = ell as f64;
            // LoS overlap: ∫ g j₂ jℓ peaks at ℓ=2 (=1) and falls as 6/[ℓ(ℓ+1)]
            let overlap = 6.0 / (ell_f * (ell_f + 1.0));
            // First-order C_ℓ correction: δC/C = 2 × ΔF₂ × overlap
            let correction = 2.0 * df2 * overlap;
            relative_correction[ell] = correction;
            cl_b[ell] *= 1.0 + correction;
        }
    }

    // Step 3: Recompute D_ℓ from corrected C_ℓ
    let dl_b: Vec<f64> = cl_b.iter().enumerate().map(|(ell, &c)| {
        if ell < 2 { 0.0 } else { ell as f64 * (ell + 1) as f64 * c / (2.0 * PI) }
    }).collect();
    let t_uk2 = (params.t_cmb * 1e6_f64).powi(2);
    let dl_muK2_b: Vec<f64> = dl_b.iter().map(|&d| d * t_uk2).collect();

    // Step 4: Compute diagnostics
    // D_{≥2} from Track A multipoles.
    // Θ_ℓ ≈ √(C_ℓ × (2ℓ+1)/(4π)) gives the RMS multipole amplitude.
    // For D_{≥2}, we need the deterministic contribution (not cosmic variance).
    // Approximate: Θ_ℓ^det ≈ √(C_ℓ) × √((2ℓ+1)/(4π)) for the signal part.
    let theta_approx: Vec<f64> = track_a.cl.iter().enumerate()
        .map(|(ell, &c)| {
            if ell >= 2 && c > 0.0 {
                (c * (2*ell+1) as f64 / (4.0 * PI)).sqrt()
            } else { 0.0 }
        }).collect();
    let d_ge2 = compute_d_ge2(&theta_approx, teff_config.sigma2);

    let eps_th = if teff_config.sigma2 > 1e-30 {
        // Use the correct Q formula from teff_cl.rs:
        // Q = (5/3)√(2Σ²/3), A ~ Θ₁ ~ β (dipole from tilt)
        use crate::solver::teff_cl::q_from_sigma2;
        let q_val = q_from_sigma2(teff_config.sigma2);
        let a_val = q_val * 0.1; // dipole ~ 10% of quadrupole (conservative)
        eps_th_linear(a_val, q_val)
    } else {
        0.0
    };

    // σ_min(J): lower bound from Paper III spectral coefficients.
    // For photons at η₀=0: σ_min ≈ 1 − O(Σ²). Use 1−ΔF₂ as estimate.
    let sigma_min_j = (1.0 - df2).max(0.1);
    let c_xi_l = 1.5; // Paper IV: C(ξ,L) ~ 1.5 for L=30, photon statistics
    let delta_obs = adequacy_bound(d_ge2, sigma_min_j, c_xi_l);

    let diagnostics = TeffDiagnostics {
        d_ge2_history: vec![d_ge2],
        d_ge2_peak: d_ge2,
        eps_th,
        delta_obs_bound: delta_obs,
        adequate: delta_obs < 0.01,
    };

    Ok(TrackBResult {
        cl_result: FlrwClResult {
            cl: cl_b,
            dl: dl_b,
            dl_muK2: dl_muK2_b,
            ..track_a
        },
        diagnostics,
        relative_correction,
    })
}

// ═══ 5-Metric Cross-Check (CL-14 scope, implemented here for completeness) ═══

/// Cross-check report between Track A and Track B.
#[derive(Clone, Debug)]
pub(crate) struct CrossCheckReport {
    /// ε_state: state-space error (norm of C_ℓ difference)
    pub(crate) eps_state: f64,
    /// ε_Th: source translation error (from CL-12)
    pub(crate) eps_th: f64,
    /// Δ_obs: adequacy certificate (from CL-11)
    pub(crate) delta_obs_bound: f64,
    /// ε_{C_ℓ}: band-averaged C_ℓ difference
    pub(crate) eps_cl_low: f64,   // ℓ = 2..30
    pub(crate) eps_cl_mid: f64,   // ℓ = 30..100
    pub(crate) eps_cl_high: f64,  // ℓ = 100..ℓ_max
    /// Cost ratio: wall_B / wall_A
    pub(crate) cost_ratio: f64,
    /// Overall verdict
    pub(crate) tracks_consistent: bool,
}

/// Run cross-check between Track A and Track B.
pub(crate) fn cross_check(
    track_a: &FlrwClResult,
    track_b: &TrackBResult,
    tolerance: f64,
) -> CrossCheckReport {
    let ell_max = track_a.cl.len().min(track_b.cl_result.cl.len()) - 1;

    // ε_state: weighted norm of C_ℓ difference
    let mut num_sq = 0.0;
    let mut den_sq = 0.0;
    for ell in 2..=ell_max {
        let w = (2 * ell + 1) as f64;
        num_sq += w * (track_a.cl[ell] - track_b.cl_result.cl[ell]).powi(2);
        den_sq += w * track_a.cl[ell].powi(2);
    }
    let eps_state = if den_sq > 1e-60 { (num_sq / den_sq).sqrt() } else { 0.0 };

    // ε_{C_ℓ} band-averaged
    let eps_cl_low = band_avg_error(&track_a.cl, &track_b.cl_result.cl, 2, 30.min(ell_max));
    let eps_cl_mid = band_avg_error(&track_a.cl, &track_b.cl_result.cl, 30.min(ell_max), 100.min(ell_max));
    let eps_cl_high = band_avg_error(&track_a.cl, &track_b.cl_result.cl, 100.min(ell_max), ell_max);

    // Cost ratio
    let cost_ratio = track_b.cl_result.wall_ms / track_a.wall_ms.max(1e-3);

    let consistent = eps_state < tolerance;

    CrossCheckReport {
        eps_state,
        eps_th: track_b.diagnostics.eps_th,
        delta_obs_bound: track_b.diagnostics.delta_obs_bound,
        eps_cl_low,
        eps_cl_mid,
        eps_cl_high,
        cost_ratio,
        tracks_consistent: consistent,
    }
}

fn band_avg_error(cl_a: &[f64], cl_b: &[f64], ell_lo: usize, ell_hi: usize) -> f64 {
    if ell_hi <= ell_lo { return 0.0; }
    let mut num = 0.0;
    let mut den = 0.0;
    for ell in ell_lo..=ell_hi.min(cl_a.len() - 1).min(cl_b.len() - 1) {
        num += (cl_a[ell] - cl_b[ell]).abs();
        den += cl_a[ell].abs();
    }
    if den > 1e-60 { num / den } else { 0.0 }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::recombination::visibility_hyrec::VisibilityParams;

    fn planck() -> VisibilityParams {
        VisibilityParams::planck2018()
    }

    // ═══ TEST 1: FLRW — Track A = Track B (exact) ═══

    #[test]
    fn test_flrw_tracks_identical() {
        let cfg = FlrwClConfig::fast_validation();
        let teff_cfg = TeffClConfig::flrw(); // Σ² = 0

        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();

        // In FLRW, Track B must be IDENTICAL to Track A
        for ell in 2..=cfg.ell_max {
            let diff = (track_a.cl[ell] - track_b.cl_result.cl[ell]).abs();
            assert!(diff < 1e-30,
                "FLRW ℓ={}: Track A C_ℓ = {:.6e}, Track B = {:.6e}, diff = {:.4e}",
                ell, track_a.cl[ell], track_b.cl_result.cl[ell], diff);
        }

        // Cross-check must show zero difference
        let report = cross_check(&track_a, &track_b, 1e-10);
        assert!(report.eps_state < 1e-15,
            "FLRW: ε_state = {:.4e} (must be 0)", report.eps_state);
        assert!(report.tracks_consistent, "FLRW: tracks must be consistent");

        eprintln!("  FLRW cross-check: ε_state = {:.4e}, ε_Th = {:.4e}",
            report.eps_state, report.eps_th);
    }

    // ═══ TEST 2: BI — Track B ≠ Track A ═══

    #[test]
    fn test_bi_tracks_differ() {
        let cfg = FlrwClConfig::fast_validation();
        let teff_cfg = TeffClConfig::bianchi_i(1e-6); // moderate Σ²

        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();

        // Track B should differ from Track A at ℓ=2
        let diff_d2 = (track_a.dl_muK2[2] - track_b.cl_result.dl_muK2[2]).abs();
        assert!(diff_d2 > 1e-10,
            "BI: D₂ must differ. Track A = {:.4e}, Track B = {:.4e}",
            track_a.dl_muK2[2], track_b.cl_result.dl_muK2[2]);

        // Relative correction should be nonzero
        let max_corr: f64 = track_b.relative_correction.iter()
            .cloned().fold(0.0_f64, f64::max);
        assert!(max_corr > 1e-15,
            "BI: max |ΔC_ℓ/C_ℓ| = {:.4e} (must be > 0)", max_corr);

        eprintln!("  BI (Σ²=10⁻⁶): D₂_A = {:.2} μK², D₂_B = {:.2} μK², diff = {:.4e}",
            track_a.dl_muK2[2], track_b.cl_result.dl_muK2[2], diff_d2);
    }

    // ═══ TEST 3: Cross-check metrics ═══

    #[test]
    fn test_cross_check_flrw() {
        let cfg = FlrwClConfig::fast_validation();
        let teff_cfg = TeffClConfig::flrw();

        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();
        let report = cross_check(&track_a, &track_b, 1e-10);

        assert!(report.eps_state < 1e-15, "FLRW ε_state");
        assert!(report.eps_cl_low < 1e-15, "FLRW ε_cl_low");
        assert!(report.eps_th < 1e-15, "FLRW ε_Th");
        assert!(report.cost_ratio > 0.5 && report.cost_ratio < 2.0,
            "FLRW cost ratio = {:.2}", report.cost_ratio);
    }

    #[test]
    fn test_cross_check_bi() {
        let cfg = FlrwClConfig::fast_validation();
        let teff_cfg = TeffClConfig::bianchi_i(1e-4); // large Σ² → visible separation

        let track_a = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let track_b = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();
        let report = cross_check(&track_a, &track_b, 1.0);

        // At large Σ², ε_state should be nonzero
        assert!(report.eps_state > 1e-10,
            "BI (Σ²=10⁻⁴): ε_state = {:.4e} (must be > 0)", report.eps_state);

        eprintln!("  BI cross-check: ε_state={:.4e}, ε_Th={:.4e}, ε_cl_low={:.4e}",
            report.eps_state, report.eps_th, report.eps_cl_low);
    }

    // ═══ TEST 4: Teff correction scaling ═══

    #[test]
    fn test_correction_scales_with_sigma2() {
        let cfg = FlrwClConfig::fast_validation();

        let tb_lo = compute_flrw_cl_track_b(&planck(), &cfg,
            &TeffClConfig::bianchi_i(1e-8)).unwrap();
        let tb_hi = compute_flrw_cl_track_b(&planck(), &cfg,
            &TeffClConfig::bianchi_i(1e-6)).unwrap();

        let corr_lo = tb_lo.relative_correction[2].abs();
        let corr_hi = tb_hi.relative_correction[2].abs();

        // Correction ∝ Σ² → ratio should be ~100
        let ratio = corr_hi / corr_lo.max(1e-30);
        assert!(ratio > 50.0 && ratio < 200.0,
            "Correction scaling: {:.1}× (expect ~100×)", ratio);
    }

    // ═══ TEST 5: Diagnostics ═══

    #[test]
    fn test_diagnostics_flrw() {
        let cfg = FlrwClConfig::fast_validation();
        let teff_cfg = TeffClConfig::flrw();
        let tb = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();

        assert!(tb.diagnostics.eps_th < 1e-15, "FLRW ε_Th = {:.4e}", tb.diagnostics.eps_th);
        assert!(tb.diagnostics.d_ge2_peak.is_finite());
    }

    #[test]
    fn test_diagnostics_bi() {
        let cfg = FlrwClConfig::fast_validation();
        let teff_cfg = TeffClConfig::bianchi_i(1e-5);
        let tb = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();

        assert!(tb.diagnostics.d_ge2_peak.is_finite());
        assert!(tb.diagnostics.delta_obs_bound.is_finite());
        eprintln!("  BI diag: D_≥2={:.4e}, Δ_obs={:.4e}, ε_Th={:.4e}",
            tb.diagnostics.d_ge2_peak, tb.diagnostics.delta_obs_bound, tb.diagnostics.eps_th);
    }

    // ═══ TEST 6: D₂ register consistency ═══

    #[test]
    fn test_d2_track_b_positive() {
        let cfg = FlrwClConfig::fast_validation();
        for &s2 in &[0.0, 1e-10, 1e-8, 1e-6, 1e-4] {
            let teff_cfg = if s2 < 1e-30 { TeffClConfig::flrw() }
                          else { TeffClConfig::bianchi_i(s2) };
            let tb = compute_flrw_cl_track_b(&planck(), &cfg, &teff_cfg).unwrap();
            assert!(tb.cl_result.dl_muK2[2] > 0.0 && tb.cl_result.dl_muK2[2].is_finite(),
                "Σ²={:.0e}: D₂_B = {:.4e} (must be positive finite)",
                s2, tb.cl_result.dl_muK2[2]);
        }
    }
}
