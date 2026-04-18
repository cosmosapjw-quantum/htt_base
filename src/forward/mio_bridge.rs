// BH-02: BASS → MIO Forward Interface.
//
// MIO (Model-Independent Observatory) produces departure reports with claim taxonomy.
// 6-level error hierarchy: ε₁..ε₅ (original) + ε₆ = ε_{BiPoSH} (NEW).
//
// Claim taxonomy:
//   ESTABLISHED: converged + cross-check + HyRec-2 + BiPoSH validated
//   CONDITIONAL: single solver OR Peebles recomb, conditions stated
//   NOT_ESTABLISHED: tilted baryon-frame chemistry (P4 future)

use super::bass_rhs::{BassResult, BassDiagnostics, RecombTier};

// ═══ Claim Taxonomy ═══

/// Three-tier claim status (mandatory throughout manuscript).
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum ClaimStatus {
    Established,
    Conditional { conditions: Vec<String> },
    NotEstablished { reason: String },
}

impl ClaimStatus {
    pub(crate) fn label(&self) -> &'static str {
        match self {
            Self::Established => "ESTABLISHED",
            Self::Conditional { .. } => "CONDITIONAL",
            Self::NotEstablished { .. } => "NOT ESTABLISHED",
        }
    }
}

/// Determine claim status from diagnostics.
pub(crate) fn classify_claim(diag: &MioDiagnostics) -> ClaimStatus {
    // Gate 1: convergence
    if !diag.converged {
        return ClaimStatus::NotEstablished {
            reason: "Solver did not converge".into(),
        };
    }

    // Gate 2: energy conservation
    if diag.energy_error > 1e-6 {
        return ClaimStatus::Conditional {
            conditions: vec![format!("Energy error {:.2e} > 1e-6", diag.energy_error)],
        };
    }

    // Gate 3: cross-check
    let mut conditions = Vec::new();
    if diag.teff_pstf_discrepancy > 0.001 {
        conditions.push(format!("Teff-PSTF discrepancy {:.2e} > 0.1%", diag.teff_pstf_discrepancy));
    }

    // Gate 4: recombination tier
    match diag.recomb_tier {
        RecombTier::Peebles => {
            conditions.push("Peebles recombination (valid ℓ < 1500 only)".into());
        }
        RecombTier::HyRec2 => {} // acceptable
        RecombTier::AnisoSobolev => {} // best
    }

    // Gate 5: BiPoSH validation
    if diag.direction_dependent.biposh_sn > 0.0 && !diag.direction_dependent.biposh_validated {
        conditions.push("BiPoSH signal detected but not cross-validated".into());
    }

    // Gate 6: tilted chemistry (always NOT ESTABLISHED at present)
    // This is a separate claim about baryon-frame recombination

    if conditions.is_empty() {
        ClaimStatus::Established
    } else {
        ClaimStatus::Conditional { conditions }
    }
}

// ═══ 6-Level Error Hierarchy ═══

/// Error measurement hierarchy (project_extension_plan §6 + BiPoSH).
#[derive(Clone, Debug)]
pub(crate) struct ErrorHierarchy {
    /// ε₁: Background integration error.
    pub(crate) eps1_background: f64,
    /// ε₂: Perturbation hierarchy truncation error.
    pub(crate) eps2_truncation: f64,
    /// ε₃: Recombination model error.
    pub(crate) eps3_recombination: f64,
    /// ε₄: Line-of-sight integration error.
    pub(crate) eps4_los: f64,
    /// ε₅: Statistical inference error.
    pub(crate) eps5_inference: f64,
    /// ε₆ (NEW): Direction-dependent observable error (BiPoSH).
    pub(crate) eps6_biposh: f64,
}

impl ErrorHierarchy {
    /// Total error budget (quadrature sum).
    pub(crate) fn total(&self) -> f64 {
        (self.eps1_background.powi(2)
         + self.eps2_truncation.powi(2)
         + self.eps3_recombination.powi(2)
         + self.eps4_los.powi(2)
         + self.eps5_inference.powi(2)
         + self.eps6_biposh.powi(2)).sqrt()
    }

    /// Dominant error level.
    pub(crate) fn dominant(&self) -> (usize, f64) {
        let levels = [
            self.eps1_background, self.eps2_truncation, self.eps3_recombination,
            self.eps4_los, self.eps5_inference, self.eps6_biposh,
        ];
        let (idx, &val) = levels.iter().enumerate()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap()).unwrap();
        (idx + 1, val)
    }

    /// Default from diagnostics.
    pub(crate) fn from_diagnostics(diag: &MioDiagnostics) -> Self {
        Self {
            eps1_background: diag.energy_error.min(1e-10),
            eps2_truncation: 1e-4, // from solver ℓ_max setting
            eps3_recombination: match diag.recomb_tier {
                RecombTier::Peebles => 0.01,       // ~1% at ℓ > 1500
                RecombTier::HyRec2 => 0.001,       // ~0.1%
                RecombTier::AnisoSobolev => 0.0003, // ~0.03% (direction-dependent)
            },
            eps4_los: 1e-4,
            eps5_inference: 0.002, // dynesty convergence (~0.2%)
            eps6_biposh: diag.direction_dependent.biposh_error,
        }
    }
}

// ═══ Direction-Dependent Diagnostics (NEW) ═══

/// Direction-dependent Silk damping diagnostics.
#[derive(Clone, Debug)]
pub(crate) struct DirectionDependentDiag {
    /// Maximum α_D over computed ℓ range.
    pub(crate) alpha_d_max: f64,
    /// BiPoSH cumulative S/N.
    pub(crate) biposh_sn: f64,
    /// Silk modulation amplitude δC_ℓ/C_ℓ at reference ℓ.
    pub(crate) silk_modulation_amplitude: f64,
    /// BiPoSH validated by cross-check (Teff vs PSTF agreement).
    pub(crate) biposh_validated: bool,
    /// BiPoSH error level ε₆.
    pub(crate) biposh_error: f64,
}

impl DirectionDependentDiag {
    /// FLRW: all zeros (no direction dependence).
    pub(crate) fn flrw() -> Self {
        Self {
            alpha_d_max: 0.0, biposh_sn: 0.0,
            silk_modulation_amplitude: 0.0,
            biposh_validated: true, biposh_error: 0.0,
        }
    }

    /// From BiPoSH analysis results.
    pub(crate) fn from_biposh(
        alpha_d_max: f64, biposh_sn: f64,
        silk_mod: f64, cross_check_ok: bool,
    ) -> Self {
        // ε₆ scales with inverse S/N: well-detected → small error
        let biposh_error = if biposh_sn > 1.0 { 1.0 / biposh_sn } else { 1.0 };
        Self {
            alpha_d_max, biposh_sn,
            silk_modulation_amplitude: silk_mod,
            biposh_validated: cross_check_ok,
            biposh_error,
        }
    }
}

// ═══ Full MIO Diagnostics Bundle ═══

/// Complete MIO diagnostics (original + new).
#[derive(Clone, Debug)]
pub(crate) struct MioDiagnostics {
    /// Solver convergence.
    pub(crate) converged: bool,
    /// Energy conservation error.
    pub(crate) energy_error: f64,
    /// Teff vs PSTF discrepancy.
    pub(crate) teff_pstf_discrepancy: f64,
    /// Eigenvalue conditioning number.
    pub(crate) eigenvalue_condition: f64,
    /// D_{s,≥2} tangency diagnostic (from BG-07).
    pub(crate) tangency_d2: f64,
    /// Recombination precision tier.
    pub(crate) recomb_tier: RecombTier,
    /// Direction-dependent diagnostics (NEW).
    pub(crate) direction_dependent: DirectionDependentDiag,
}

impl MioDiagnostics {
    /// Convert from BASS diagnostics.
    pub(crate) fn from_bass(bass_diag: &BassDiagnostics, dd: DirectionDependentDiag) -> Self {
        Self {
            converged: bass_diag.converged,
            energy_error: bass_diag.energy_error,
            teff_pstf_discrepancy: bass_diag.teff_pstf_discrepancy,
            eigenvalue_condition: 1.0, // default
            tangency_d2: 0.0,
            recomb_tier: bass_diag.recomb_tier.clone(),
            direction_dependent: dd,
        }
    }
}

/// Generate MIO report section for direction-dependent Silk.
pub(crate) fn silk_report_section(dd: &DirectionDependentDiag) -> String {
    let mut report = String::new();
    report.push_str("=== Direction-Dependent Silk Damping ===\n");
    report.push_str(&format!("alpha_D_max = {:.4e}\n", dd.alpha_d_max));
    report.push_str(&format!("BiPoSH S/N = {:.2}\n", dd.biposh_sn));
    report.push_str(&format!("Silk modulation = {:.4e}\n", dd.silk_modulation_amplitude));
    report.push_str(&format!("BiPoSH validated = {}\n", dd.biposh_validated));
    report.push_str(&format!("eps_BiPoSH = {:.4e}\n", dd.biposh_error));
    report
}

#[cfg(test)]
mod tests {
    use super::*;

    fn flrw_diag() -> MioDiagnostics {
        MioDiagnostics {
            converged: true, energy_error: 1e-12,
            teff_pstf_discrepancy: 1e-6, eigenvalue_condition: 1.0,
            tangency_d2: 0.0, recomb_tier: RecombTier::HyRec2,
            direction_dependent: DirectionDependentDiag::flrw(),
        }
    }

    fn bi_diag() -> MioDiagnostics {
        MioDiagnostics {
            converged: true, energy_error: 1e-10,
            teff_pstf_discrepancy: 5e-4, eigenvalue_condition: 10.0,
            tangency_d2: 1e-6, recomb_tier: RecombTier::AnisoSobolev,
            direction_dependent: DirectionDependentDiag::from_biposh(0.24, 5.0, 1e-3, true),
        }
    }

    // ═══ Claim taxonomy ═══

    #[test]
    fn test_flrw_established() {
        let status = classify_claim(&flrw_diag());
        assert_eq!(status, ClaimStatus::Established);
    }

    #[test]
    fn test_bi_with_aniso_sobolev_established() {
        let status = classify_claim(&bi_diag());
        assert_eq!(status, ClaimStatus::Established);
    }

    #[test]
    fn test_peebles_conditional() {
        let mut d = flrw_diag();
        d.recomb_tier = RecombTier::Peebles;
        let status = classify_claim(&d);
        assert_eq!(status.label(), "CONDITIONAL");
    }

    #[test]
    fn test_unconverged_not_established() {
        let mut d = flrw_diag();
        d.converged = false;
        let status = classify_claim(&d);
        assert_eq!(status.label(), "NOT ESTABLISHED");
    }

    #[test]
    fn test_biposh_unvalidated_conditional() {
        let mut d = bi_diag();
        d.direction_dependent.biposh_validated = false;
        let status = classify_claim(&d);
        assert_eq!(status.label(), "CONDITIONAL");
    }

    // ═══ Error hierarchy ═══

    #[test]
    fn test_error_6_levels() {
        let d = bi_diag();
        let eh = ErrorHierarchy::from_diagnostics(&d);
        assert!(eh.total() > 0.0 && eh.total().is_finite());
        let (dom, _) = eh.dominant();
        assert!(dom >= 1 && dom <= 6, "Dominant level = {}", dom);
    }

    #[test]
    fn test_error_budget_sum() {
        let eh = ErrorHierarchy {
            eps1_background: 0.001, eps2_truncation: 0.002,
            eps3_recombination: 0.003, eps4_los: 0.001,
            eps5_inference: 0.005, eps6_biposh: 0.004,
        };
        let total = eh.total();
        let manual = (0.001f64.powi(2) + 0.002f64.powi(2) + 0.003f64.powi(2)
            + 0.001f64.powi(2) + 0.005f64.powi(2) + 0.004f64.powi(2)).sqrt();
        assert!((total - manual).abs() < 1e-15, "total={:.6e}, manual={:.6e}", total, manual);
    }

    #[test]
    fn test_hyrec2_lower_error_than_peebles() {
        let mut d_p = flrw_diag();
        d_p.recomb_tier = RecombTier::Peebles;
        let mut d_h = flrw_diag();
        d_h.recomb_tier = RecombTier::HyRec2;
        let eh_p = ErrorHierarchy::from_diagnostics(&d_p);
        let eh_h = ErrorHierarchy::from_diagnostics(&d_h);
        assert!(eh_h.eps3_recombination < eh_p.eps3_recombination);
    }

    #[test]
    fn test_aniso_sobolev_best() {
        let d = bi_diag();
        let eh = ErrorHierarchy::from_diagnostics(&d);
        assert!(eh.eps3_recombination < 0.001, "AnisoSobolev: eps3 = {:.4e}", eh.eps3_recombination);
    }

    // ═══ Direction-dependent diagnostics ═══

    #[test]
    fn test_flrw_dd_all_zero() {
        let dd = DirectionDependentDiag::flrw();
        assert_eq!(dd.alpha_d_max, 0.0);
        assert_eq!(dd.biposh_sn, 0.0);
        assert_eq!(dd.biposh_error, 0.0);
        assert!(dd.biposh_validated);
    }

    #[test]
    fn test_biposh_error_scales_with_sn() {
        let dd_low = DirectionDependentDiag::from_biposh(0.24, 2.0, 1e-3, true);
        let dd_high = DirectionDependentDiag::from_biposh(0.24, 20.0, 1e-3, true);
        assert!(dd_high.biposh_error < dd_low.biposh_error,
            "Higher S/N → lower error: {:.4e} vs {:.4e}", dd_high.biposh_error, dd_low.biposh_error);
    }

    // ═══ Report ═══

    #[test]
    fn test_report_parseable() {
        let dd = DirectionDependentDiag::from_biposh(0.24, 5.0, 1e-3, true);
        let report = silk_report_section(&dd);
        assert!(report.contains("alpha_D_max"));
        assert!(report.contains("BiPoSH S/N"));
        assert!(report.contains("eps_BiPoSH"));
    }

    #[test]
    fn test_from_bass_diagnostics() {
        let bass = BassDiagnostics {
            converged: true, energy_error: 1e-11,
            teff_pstf_discrepancy: 1e-4,
            recomb_tier: RecombTier::HyRec2, wall_ms: 150.0,
        };
        let dd = DirectionDependentDiag::flrw();
        let mio = MioDiagnostics::from_bass(&bass, dd);
        assert!(mio.converged);
        assert_eq!(mio.recomb_tier, RecombTier::HyRec2);
    }
}
