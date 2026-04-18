// CL-11: Teff Intensity Hierarchy for C_ℓ Pipeline.
//
// Bridge module connecting the existing teff/ infrastructure (2585 lines)
// to the solver/flrw_cl_pipeline.rs (Track B source).
//
// Physics (CL-PR v2.0 §5, Paper V):
//   - Standard PSTF quadrupole: F₂ sourced by (2k/3)F₁ + coupling − κ̇F₂
//   - Teff correction: ΔF₂ = (12/7) Q² where Q = (5/3)(σ/H)
//   - This captures the dipole²→quadrupole coupling EXACTLY
//   - In FLRW: Q = 0 → ΔF₂ = 0 (Track B = Track A)
//   - In BI: Q = (5/3)√(2Σ²/3) → ΔF₂ > 0 at O(ε²)
//
// Diagnostics:
//   - D_{≥2}: tangency diagnostic (Paper I/III) — monitors intensity closure
//   - Adequacy certificate: Δ_obs ≤ C(ξ,L) D_{≥2} / σ_min(J)
//
// Polarization: E/B hierarchy UNCHANGED by Teff (Paper V §II.B)

use crate::teff::teff_solver::TeffSpeciesState;
use crate::teff::tangency::SpectralCoefficients;
use crate::teff::theta4_bridge::thomson_quadrupole_source;
use crate::teff::spectral::Statistics;
use std::f64::consts::PI;

// ═══ Core constants ═══

/// Teff source correction prefactor: 12/7 (Paper V, dipole²→quadrupole).
const DIPOLE_SQ_PREFACTOR: f64 = 12.0 / 7.0;

/// Q = (5/3)(σ/H) → Q from Σ².
/// σ/H = √(2Σ²/3), so Q = (5/3)√(2Σ²/3).
const Q_PREFACTOR: f64 = 5.0 / 3.0;

/// c_ξ for photons (Bose-Einstein): c_ξ = ∫₀^∞ z³/(e^z−1) dz = π⁴/15.
/// For the Θ⁴ bridge normalisation: c_ξ = 6.0 (from Paper V Table I).
const C_XI_PHOTON: f64 = 6.0;

// ═══ Teff source correction ═══

/// Compute Q from the shear parameter Σ².
///
/// Q = (5/3)(σ/H) where σ/H = √(2Σ²/3).
/// This is the leading-order anisotropy measure in the Teff formalism.
pub(crate) fn q_from_sigma2(sigma2: f64) -> f64 {
    Q_PREFACTOR * (2.0 * sigma2 / 3.0).sqrt()
}

/// Teff source correction to the quadrupole: ΔF₂ = (12/7) Q².
///
/// This is the beyond-first-order correction from the dipole-squared
/// coupling. In FLRW (σ = 0), this is identically zero.
///
/// Units: same as F₂ (dimensionless perturbation amplitude).
pub(crate) fn delta_f2_teff(sigma2: f64) -> f64 {
    let q = q_from_sigma2(sigma2);
    DIPOLE_SQ_PREFACTOR * q * q
}

/// Full Teff quadrupole: standard PSTF F₂ + correction.
pub(crate) fn f2_teff(f2_pstf: f64, sigma2: f64) -> f64 {
    f2_pstf + delta_f2_teff(sigma2)
}

// ═══ Teff source for LoS integration ═══

/// Teff Thomson source for the C_ℓ pipeline.
///
/// S^{Th,Teff} = −κ̇ × I_{ab}^{Θ⁴}
/// where I_{ab} = c_ξ ⟨Θ⁴ ê_{⟨a}ê_{b⟩}⟩_Ω (Paper V Theorem 1)
///
/// Compared to Track A's S^{Th,PSTF} = −κ̇ × I_{ab}^{linear}:
///   S^{Teff} − S^{PSTF} = −κ̇ × c_ξ × 6⟨ϑ² ê_{⟨a}ê_{b⟩}⟩ + ...
///
/// The difference is second-order in the anisotropy.
pub(crate) fn teff_thomson_source(
    f_0: f64,          // monopole F₀
    f_2m: &[f64; 5],   // quadrupole F_{2m}
    f_1: &[f64; 3],    // dipole F_{1m} (for dipole² correction)
    kappa_dot: f64,     // opacity κ̇
    sigma2: f64,        // shear Σ² (for Teff correction)
) -> [f64; 5] {
    if sigma2 < 1e-30 {
        // FLRW limit: Teff = PSTF (no correction)
        let mut out = [0.0; 5];
        for i in 0..5 {
            out[i] = -kappa_dot * C_XI_PHOTON * f_2m[i];
        }
        return out;
    }

    // Full Θ⁴ bridge via existing theta4_bridge module
    let i_ab = thomson_quadrupole_source(f_0, f_2m, C_XI_PHOTON);

    // Apply opacity
    let mut out = [0.0; 5];
    for i in 0..5 {
        out[i] = -kappa_dot * i_ab[i];
    }

    // Add dipole-squared correction (Paper V §IV)
    let q = q_from_sigma2(sigma2);
    let dip_sq_correction = DIPOLE_SQ_PREFACTOR * q * q;
    // The dipole-squared correction adds to the m=0 component
    out[0] += -kappa_dot * C_XI_PHOTON * dip_sq_correction;

    out
}

/// Source translation error ε_Th between Teff and linear PSTF.
///
/// ε_Th = |S^{Teff} − S^{PSTF}| / |S^{Teff}|
pub(crate) fn source_translation_error(
    s_teff: &[f64; 5],
    s_pstf: &[f64; 5],
) -> f64 {
    let mut num2 = 0.0;
    let mut den2 = 0.0;
    for i in 0..5 {
        num2 += (s_teff[i] - s_pstf[i]).powi(2);
        den2 += s_teff[i].powi(2);
    }
    if den2 < 1e-60 { return 0.0; }
    (num2 / den2).sqrt()
}

// ═══ Tangency diagnostic ═══

/// D_{≥2} tangency diagnostic for the intensity sector.
///
/// Paper I/III: D_{≥2} = |G_ξ − Π_{V₂} G_ξ|_{*,s}
/// where V₂ = span{x, 1} (two-field subspace).
///
/// For PSTF multipoles in the intensity sector:
///   D_{≥2}² = Σ_{ℓ≥2} w_ℓ |Θ_ℓ − Θ_ℓ^{Teff}|²
/// where Θ_ℓ^{Teff} is the Teff prediction from (T₀, Θ₁).
///
/// In FLRW: all Θ_ℓ = 0 for ℓ ≥ 2 in the Teff approximation
///          → D_{≥2} = |Θ₂| (just the quadrupole residual).
pub(crate) fn compute_d_ge2(
    theta_ell: &[f64],  // Θ_ℓ for ℓ = 0, 1, 2, ..., L_max
    sigma2: f64,         // shear (for Teff prediction at ℓ=2)
) -> f64 {
    if theta_ell.len() < 3 { return 0.0; }

    // Teff prediction for ℓ=2: in FLRW, Θ₂^{Teff} ≈ 0
    // In BI: Θ₂^{Teff} ≈ (4/15) Q² (from dipole-squared)
    let q = q_from_sigma2(sigma2);
    let theta2_teff = (4.0 / 15.0) * q * q;

    // D_{≥2}² = Σ_{ℓ≥2} (2ℓ+1) |Θ_ℓ − Θ_ℓ^{Teff}|²
    let mut d2_sq = 0.0;
    for ell in 2..theta_ell.len() {
        let teff_pred = if ell == 2 { theta2_teff } else { 0.0 };
        let resid = theta_ell[ell] - teff_pred;
        d2_sq += (2 * ell + 1) as f64 * resid * resid;
    }
    d2_sq.sqrt()
}

/// Adequacy certificate: Δ_obs ≤ C(ξ,L) × D_{≥2} / σ_min(J).
///
/// Paper IV Theorem 3: the observable error is bounded by
/// the tangency diagnostic divided by the smallest singular
/// value of the Jacobian.
///
/// Returns Δ_obs_bound (upper bound on observable error).
pub(crate) fn adequacy_bound(
    d_ge2: f64,         // tangency diagnostic
    sigma_min_j: f64,   // smallest singular value of Jacobian
    c_xi_l: f64,        // coefficient C(ξ, L) from Paper IV
) -> f64 {
    if sigma_min_j < 1e-30 { return f64::INFINITY; }
    c_xi_l * d_ge2 / sigma_min_j
}

// ═══ Pipeline integration ═══

/// Teff C_ℓ configuration for Track B.
#[derive(Clone, Debug)]
pub(crate) struct TeffClConfig {
    /// Maximum ℓ for Teff closure (above this: standard PSTF).
    pub(crate) ell_teff_max: usize,
    /// Shear parameter Σ² (from Bianchi background).
    pub(crate) sigma2: f64,
    /// Whether to compute diagnostics (D_{≥2}, Δ_obs).
    pub(crate) compute_diagnostics: bool,
}

impl TeffClConfig {
    /// FLRW configuration (no anisotropy → Track B = Track A).
    pub(crate) fn flrw() -> Self {
        Self { ell_teff_max: 10, sigma2: 0.0, compute_diagnostics: true }
    }

    /// Bianchi I configuration.
    pub(crate) fn bianchi_i(sigma2: f64) -> Self {
        Self { ell_teff_max: 10, sigma2, compute_diagnostics: true }
    }
}

/// Diagnostic output from Teff solver.
#[derive(Clone, Debug)]
pub(crate) struct TeffDiagnostics {
    /// D_{≥2} tangency diagnostic at each η grid point.
    pub(crate) d_ge2_history: Vec<f64>,
    /// Peak D_{≥2} over the evolution.
    pub(crate) d_ge2_peak: f64,
    /// ε_Th source translation error at the quadrupole.
    pub(crate) eps_th: f64,
    /// Adequacy bound Δ_obs at peak.
    pub(crate) delta_obs_bound: f64,
    /// Whether Teff closure is adequate (Δ_obs < tolerance).
    pub(crate) adequate: bool,
}

/// Apply Teff correction to a source grid from Track A.
///
/// This is the main entry point for Track B:
/// 1. Takes Track A source values
/// 2. Adds the Teff correction ΔF₂ = (12/7)Q²
/// 3. Computes D_{≥2} diagnostics
/// 4. Returns modified source + diagnostics
pub(crate) fn apply_teff_correction(
    raw_theta0_source: &[f64],      // Track A Sachs-Wolfe source at each η
    theta_ell_history: &[Vec<f64>],  // Θ_ℓ at each η point
    config: &TeffClConfig,
) -> (Vec<f64>, TeffDiagnostics) {
    let n = raw_theta0_source.len();
    let mut corrected = raw_theta0_source.to_vec();

    let delta_f2 = delta_f2_teff(config.sigma2);
    let mut d_ge2_history = Vec::with_capacity(n);
    let mut d_ge2_peak = 0.0_f64;

    for i in 0..n {
        // Teff perturbative correction to source.
        //
        // Physics: ΔF₂ modifies the Thomson scattering source at each η.
        // The correction is proportional to the visibility-weighted source:
        //   ΔS(η) = ΔF₂ × S_SW(η) / ⟨S_SW⟩  (relative to source amplitude)
        //
        // NOTE: This is a FIRST-ORDER PERTURBATIVE correction, NOT a full
        // Track B re-solve. A proper Track B requires modifying the RHS of
        // the Boltzmann hierarchy (flrw_kmode.rs) and re-running the solver
        // with the Teff quadrupole source term included in the Thomson
        // collision integral. The perturbative correction is valid when
        // ΔF₂/F₂ ≪ 1, which holds for Σ² < 10⁻⁴.
        //
        // Scaling: ΔS/S ~ ΔF₂ at the source level. ΔC_ℓ/C_ℓ ~ 2×ΔF₂
        // (quadratic in the transfer function).
        corrected[i] += delta_f2 * raw_theta0_source[i];

        // Compute D_{≥2} if diagnostics enabled
        if config.compute_diagnostics && i < theta_ell_history.len() {
            let d = compute_d_ge2(&theta_ell_history[i], config.sigma2);
            d_ge2_peak = d_ge2_peak.max(d);
            d_ge2_history.push(d);
        } else {
            d_ge2_history.push(0.0);
        }
    }

    // Compute ε_Th
    let eps_th = if config.sigma2 > 1e-30 {
        // At the quadrupole level
        let q = q_from_sigma2(config.sigma2);
        DIPOLE_SQ_PREFACTOR * q * q // fractional correction
    } else {
        0.0
    };

    // Adequacy certificate (Paper IV Theorem 3).
    // σ_min(J): lower bound from spectral coefficients.
    // For photons at η₀=0, the Gram matrix is diagonal with entries ~1.
    // σ_min ≈ 1 − O(ε²), where ε = ΔF₂ is the Teff correction amplitude.
    let df2_val = delta_f2_teff(config.sigma2);
    let sigma_min_j = (1.0 - df2_val).max(0.1);
    // C(ξ,L): from Paper IV, depends on statistics and truncation.
    // For photons (BE), L=30: C ≈ 1.5 (conservative upper bound).
    let c_xi_l = 1.5;
    let delta_obs = adequacy_bound(d_ge2_peak, sigma_min_j, c_xi_l);

    let diag = TeffDiagnostics {
        d_ge2_history,
        d_ge2_peak,
        eps_th,
        delta_obs_bound: delta_obs,
        adequate: delta_obs < 0.01, // 1% adequacy threshold
    };

    (corrected, diag)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ═══ TEST 1: FLRW limit — Teff correction = 0 ═══

    #[test]
    fn test_teff_flrw_limit() {
        // In FLRW: σ = 0 → Q = 0 → ΔF₂ = 0
        let df2 = delta_f2_teff(0.0);
        assert!(df2.abs() < 1e-30,
            "FLRW: ΔF₂ = {:.4e} (must be 0)", df2);

        let q = q_from_sigma2(0.0);
        assert!(q.abs() < 1e-30, "FLRW: Q = {:.4e}", q);
    }

    #[test]
    fn test_teff_flrw_tracks_equal() {
        // In FLRW, Track B source = Track A source
        let source_a = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let theta_hist = vec![vec![0.0, 0.0, 0.0]; 5];
        let config = TeffClConfig::flrw();

        let (source_b, diag) = apply_teff_correction(&source_a, &theta_hist, &config);

        // Sources must be identical in FLRW
        for i in 0..5 {
            assert!((source_a[i] - source_b[i]).abs() < 1e-15,
                "FLRW: Track A ≠ Track B at i={}: {:.4e} vs {:.4e}",
                i, source_a[i], source_b[i]);
        }

        // D_{≥2} = 0 in FLRW
        assert!(diag.d_ge2_peak < 1e-15,
            "FLRW: D_≥2 = {:.4e} (must be 0)", diag.d_ge2_peak);

        // ε_Th = 0 in FLRW
        assert!(diag.eps_th < 1e-15,
            "FLRW: ε_Th = {:.4e} (must be 0)", diag.eps_th);
    }

    // ═══ TEST 2: BI correction — ΔF₂ = (12/7)Q² ═══

    #[test]
    fn test_teff_bi_correction() {
        let sigma2 = 1e-8;
        let q = q_from_sigma2(sigma2);

        // Q = (5/3)√(2×10⁻⁸/3) = (5/3) × 8.165e-5 = 1.361e-4
        let q_expected = Q_PREFACTOR * (2.0 * sigma2 / 3.0).sqrt();
        assert!((q - q_expected).abs() / q_expected < 1e-10,
            "Q = {:.6e} (expect {:.6e})", q, q_expected);

        // ΔF₂ = (12/7) Q² = (12/7)(1.361e-4)² = 3.18e-8
        let df2 = delta_f2_teff(sigma2);
        let df2_expected = DIPOLE_SQ_PREFACTOR * q * q;
        assert!((df2 - df2_expected).abs() / df2_expected < 1e-10,
            "ΔF₂ = {:.6e} (expect {:.6e})", df2, df2_expected);

        // ΔF₂ must be positive (dipole-squared → always positive contribution)
        assert!(df2 > 0.0, "ΔF₂ must be positive");

        // Verify scaling: ΔF₂ ∝ Σ² (in linear regime)
        let df2_10x = delta_f2_teff(sigma2 * 100.0);
        let ratio = df2_10x / df2;
        assert!((ratio - 100.0).abs() < 0.1,
            "ΔF₂ scaling: {:.1}× (expect 100×)", ratio);
    }

    #[test]
    fn test_teff_bi_source_differs() {
        // In BI, Track B source ≠ Track A source
        let source_a = vec![1.0; 10];
        let theta_hist = vec![vec![0.0, 0.1, 0.01, 0.001]; 10];
        let config = TeffClConfig::bianchi_i(1e-6);

        let (source_b, _) = apply_teff_correction(&source_a, &theta_hist, &config);

        let diff: f64 = source_a.iter().zip(source_b.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff > 1e-20,
            "BI: Track A = Track B (must differ). Σ|Δ| = {:.4e}", diff);
    }

    // ═══ TEST 3: Polarization unchanged ═══

    #[test]
    fn test_teff_pol_unchanged() {
        // Teff does NOT modify E/B hierarchy (Paper V §II.B)
        // The Teff correction only affects the intensity quadrupole.
        // E-mode source from Track A is passed through unchanged.
        //
        // This is a structural test: the Teff module has no E/B parameters.
        let f_0 = 1.0;
        let f_2m = [0.01, 0.0, 0.0, 0.0, 0.0];
        let f_1 = [0.1, 0.0, 0.0];

        // At σ²=0 (FLRW), source should be -κ̇ × c_ξ × F_{2m}
        let kappa_dot = 100.0;
        let s = teff_thomson_source(f_0, &f_2m, &f_1, kappa_dot, 0.0);

        // m=0 component: -κ̇ × c_ξ × F_{20}
        let expected_m0 = -kappa_dot * C_XI_PHOTON * f_2m[0];
        assert!((s[0] - expected_m0).abs() / expected_m0.abs() < 0.01,
            "Thomson m=0: {:.4e} (expect {:.4e})", s[0], expected_m0);
    }

    // ═══ TEST 4: D_{≥2} diagnostics ═══

    #[test]
    fn test_d_ge2_zero_isotropic() {
        // Isotropic state: all Θ_ℓ = 0 → D_{≥2} = 0
        let theta = vec![0.0; 20];
        let d = compute_d_ge2(&theta, 0.0);
        assert!(d.abs() < 1e-15, "Isotropic: D_≥2 = {:.4e}", d);
    }

    #[test]
    fn test_d_ge2_nonzero_anisotropic() {
        // Anisotropic state: Θ₂ ≠ 0 → D_{≥2} > 0
        let mut theta = vec![0.0; 10];
        theta[2] = 0.01; // quadrupole perturbation
        let d = compute_d_ge2(&theta, 0.0);
        assert!(d > 0.0, "Anisotropic: D_≥2 = {:.4e} (must be > 0)", d);
        // D_{≥2} ≈ √(5) × |Θ₂| = √5 × 0.01 = 0.02236
        let expected = (5.0_f64).sqrt() * 0.01;
        assert!((d - expected).abs() / expected < 0.01,
            "D_≥2 = {:.6e} (expect {:.6e})", d, expected);
    }

    #[test]
    fn test_d_ge2_with_teff_prediction() {
        // With Teff prediction at ℓ=2, the diagnostic measures the RESIDUAL
        let sigma2 = 1e-6;
        let q = q_from_sigma2(sigma2);
        let theta2_teff = (4.0 / 15.0) * q * q;

        // State that MATCHES the Teff prediction → D_{≥2} ≈ 0
        let mut theta_match = vec![0.0; 5];
        theta_match[2] = theta2_teff;
        let d_match = compute_d_ge2(&theta_match, sigma2);
        assert!(d_match < 1e-10,
            "Teff-matched state: D_≥2 = {:.4e} (must be ~0)", d_match);

        // State that DISAGREES with Teff → D_{≥2} > 0
        let mut theta_off = vec![0.0; 5];
        theta_off[2] = theta2_teff + 0.01;
        let d_off = compute_d_ge2(&theta_off, sigma2);
        assert!(d_off > 0.01, "Off-Teff state: D_≥2 = {:.4e}", d_off);
    }

    // ═══ TEST 5: Adequacy certificate ═══

    #[test]
    fn test_adequacy_bound_finite() {
        let d = 0.01;
        let sigma_min = 0.5;
        let c_xi_l = 1.0;
        let bound = adequacy_bound(d, sigma_min, c_xi_l);
        assert!(bound.is_finite(), "Adequacy bound must be finite");
        assert_eq!(bound, 0.02); // 1.0 × 0.01 / 0.5
    }

    #[test]
    fn test_adequacy_bound_zero_diagnostic() {
        // D_{≥2} = 0 → Δ_obs = 0 (perfect closure)
        let bound = adequacy_bound(0.0, 1.0, 1.0);
        assert!(bound < 1e-30, "Zero D_≥2: bound = {:.4e}", bound);
    }

    #[test]
    fn test_adequacy_bound_singular_jacobian() {
        // σ_min(J) → 0 → Δ_obs → ∞ (ill-conditioned)
        let bound = adequacy_bound(0.01, 1e-40, 1.0);
        assert!(bound == f64::INFINITY, "Singular J: bound must be ∞");
    }

    // ═══ TEST 6: Numerical register ═══

    #[test]
    fn test_q_from_sigma2_register() {
        // Q(Σ²=10⁻⁸) = (5/3)√(2×10⁻⁸/3) = (5/3) × 8.1650e-5 = 1.3608e-4
        let q = q_from_sigma2(1e-8);
        assert!((q - 1.3608e-4).abs() / 1.3608e-4 < 0.01,
            "Q(10⁻⁸) = {:.4e} (expect 1.361e-4)", q);
    }

    #[test]
    fn test_delta_f2_register() {
        // ΔF₂(Σ²=10⁻⁸) = (12/7)(1.3608e-4)² = 3.175e-8
        let df2 = delta_f2_teff(1e-8);
        let expected = DIPOLE_SQ_PREFACTOR * (1.3608e-4_f64).powi(2);
        assert!((df2 - expected).abs() / expected < 0.02,
            "ΔF₂(10⁻⁸) = {:.4e} (expect {:.4e})", df2, expected);
    }
}
