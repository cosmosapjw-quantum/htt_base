// BE-05f: Teff Radiation Temperature Correction.
//
// T_{γ,4}⁴ = T₀⁴ ⟨Θ⁴⟩_Ω replaces T_r⁴ in the Compton heating term.
//
// Θ⁴ bridge (P-V.T1): ⟨Θ⁴⟩ = 1 + 6⟨ϑ²⟩ + 4⟨ϑ³⟩ + ⟨ϑ⁴⟩
// where ϑ = Θ − 1 = ΔT/T₀ is the temperature perturbation.
// The coefficient 6 = C(4,2) is exact (binomial).
//
// For Bianchi backgrounds: ϑ(ê) has ℓ=0 (monopole shift) and ℓ=2
// (quadrupolar) components from the shear σ_{ab}.
//
// Angular cumulants {⟨ϑ²⟩, ⟨κ²⟩, ⟨ϑκ⟩} where κ = K(ê)/H − 1
// encode the 2nd-order backreaction on x_e and T_m.
//
// Off-manifold bound (P-IV.T5): |Δẋ_e^off| ≤ |h_{x_e}'| × D_{≥2}

use std::f64::consts::PI;

// ═══ Physical constants ═══
const SIGMA_T: f64 = 6.6524587321e-29;  // Thomson cross section [m²]
const A_RAD: f64 = 7.5657e-16;          // radiation constant [J/m³/K⁴]
const M_E_C2: f64 = 8.187e-14;          // m_e c² [J]
const C_LIGHT: f64 = 2.99792458e8;      // [m/s]
const F_HE: f64 = 0.0813;               // helium fraction Y_p/(4(1−Y_p))
const KB: f64 = 1.380649e-23;           // [J/K]

// ═══ Θ⁴ Bridge ═══

/// Angular cumulant set for Teff backreaction.
#[derive(Clone, Debug, Default)]
pub(crate) struct CumulantSet {
    /// ⟨ϑ²⟩_Ω: variance of temperature perturbation.
    pub(crate) vartheta2: f64,
    /// ⟨ϑ³⟩_Ω: skewness (3rd cumulant).
    pub(crate) vartheta3: f64,
    /// ⟨ϑ⁴⟩_Ω: kurtosis (4th cumulant, not excess).
    pub(crate) vartheta4: f64,
    /// ⟨κ²⟩_Ω: variance of K(ê)/H − 1 = σ_{ab}ê^aê^b/H.
    pub(crate) kappa2: f64,
    /// ⟨ϑκ⟩_Ω: cross-correlation of temperature and line-shift.
    pub(crate) vartheta_kappa: f64,
}

/// Compute ⟨Θ⁴⟩_Ω from angular cumulants.
///
/// ⟨Θ⁴⟩ = ⟨(1+ϑ)⁴⟩ = 1 + 4⟨ϑ⟩ + 6⟨ϑ²⟩ + 4⟨ϑ³⟩ + ⟨ϑ⁴⟩
///
/// For Bianchi: ⟨ϑ⟩ = 0 (no monopole perturbation at leading order).
/// The coefficient 6 = C(4,2) is the Θ⁴ bridge (P-V.T1).
pub(crate) fn theta4_moment(c: &CumulantSet) -> f64 {
    1.0 + 6.0 * c.vartheta2 + 4.0 * c.vartheta3 + c.vartheta4
}

/// Effective radiation temperature to the 4th power.
///
/// T_{γ,4}⁴ = T₀⁴ × ⟨Θ⁴⟩_Ω
pub(crate) fn radiation_temp_4th(t_r: f64, c: &CumulantSet) -> f64 {
    t_r.powi(4) * theta4_moment(c)
}

/// Leading-order approximation for small anisotropy.
///
/// ⟨Θ⁴⟩ ≈ 1 + 6⟨ϑ²⟩ to O(ϑ²)
pub(crate) fn theta4_leading_order(vartheta2: f64) -> f64 {
    1.0 + 6.0 * vartheta2
}

// ═══ Compton Heating Correction ═══

/// Standard Compton heating/cooling rate [K/s].
///
/// Ṫ_m^{Compton} = Γ_C × (T_r − T_m) / H
///
/// where Γ_C = (8 σ_T a_R T_r⁴) / (3 m_e c) × x_e / (1 + f_He + x_e)
pub(crate) fn compton_rate(t_r: f64, x_e: f64) -> f64 {
    8.0 * SIGMA_T * A_RAD * t_r.powi(4) / (3.0 * M_E_C2 / C_LIGHT)
        * x_e / (1.0 + F_HE + x_e)
}

/// Corrected Compton heating with Teff replacement.
///
/// Replace T_r⁴ → T_{γ,4}⁴ = T_r⁴ ⟨Θ⁴⟩ in the Compton rate.
/// The temperature difference remains (T_r − T_m) at leading order;
/// the correction enters through the energy exchange rate prefactor.
///
/// Returns Ṫ_m [K/s] (divide by H for dT_m/dη).
pub(crate) fn compton_heating_corrected(
    t_m: f64,
    t_r: f64,
    x_e: f64,
    cumulants: &CumulantSet,
) -> f64 {
    let theta4 = theta4_moment(cumulants);
    let gamma_c = 8.0 * SIGMA_T * A_RAD * t_r.powi(4) * theta4
        / (3.0 * M_E_C2 / C_LIGHT) * x_e / (1.0 + F_HE + x_e);
    gamma_c * (t_r - t_m)
}

/// Fractional correction to Compton rate from anisotropy.
///
/// δΓ_C/Γ_C = ⟨Θ⁴⟩ − 1 ≈ 6⟨ϑ²⟩ at leading order.
pub(crate) fn compton_rate_correction(cumulants: &CumulantSet) -> f64 {
    theta4_moment(cumulants) - 1.0
}

// ═══ Angular Cumulants from Multipoles ═══

/// Compute angular cumulants from PSTF multipole coefficients.
///
/// For Bianchi I with only ℓ=2 shear:
///   ⟨ϑ²⟩ = Σ_{m=-2}^{2} |ϑ_{2m}|² / (2×2+1) = |ϑ₂|²/5
///   ⟨κ²⟩ = (2/15)(σ/H)² (exact from STF angular integral)
///
/// The PSTF multipoles ϑ_{Aℓ} encode the angular structure of ΔT/T.
pub(crate) fn angular_cumulants_from_sigma(sigma2_over_h2: f64, vartheta2_ell2: f64) -> CumulantSet {
    CumulantSet {
        vartheta2: vartheta2_ell2,
        vartheta3: 0.0,  // Bianchi shear is symmetric → odd cumulants small
        vartheta4: 3.0 * vartheta2_ell2 * vartheta2_ell2, // Gaussian approximation
        kappa2: 2.0 / 15.0 * sigma2_over_h2, // exact STF integral
        vartheta_kappa: 0.0, // ϑ and κ uncorrelated at leading order
    }
}

/// Compute ⟨ϑ²⟩ from Bianchi I shear-induced CMB anisotropy.
///
/// For BI: ΔT/T ~ D₂^{1/2} where D₂ is the departure power.
/// ⟨ϑ²⟩ ≈ D₂ / (T_CMB)² in (ΔT/T)² units ≈ C₂ (angular power).
pub(crate) fn vartheta2_from_d2(d2_muK2: f64, t_cmb: f64) -> f64 {
    // D₂ in μK² → (ΔT/T)² = D₂ / (T_CMB in μK)²
    d2_muK2 / (t_cmb * 1e6).powi(2)
}

// ═══ 2nd-Order Backreaction on Recombination ═══

/// Rate derivatives for 2nd-order backreaction.
#[derive(Clone, Debug)]
pub(crate) struct RateDerivatives {
    /// ∂ẋ_e/∂T_r: sensitivity of recombination rate to radiation temperature.
    pub(crate) dxe_dtr: f64,
    /// ∂ẋ_e/∂H: sensitivity to Hubble rate (via escape probability).
    pub(crate) dxe_dh: f64,
    /// ∂²ẋ_e/∂T_r²: curvature (for Jensen correction).
    pub(crate) d2xe_dtr2: f64,
}

/// 2nd-order backreaction on recombination rate.
///
/// δ²ẋ_e = (1/2) ∂²ẋ_e/∂T_r² × T_r² × ⟨ϑ²⟩
///        + (1/2) ∂²ẋ_e/∂H² × H² × ⟨κ²⟩
///        + ∂²ẋ_e/(∂T_r∂H) × T_r H × ⟨ϑκ⟩
///
/// At leading order: dominant term is the T_r curvature (Jensen effect).
pub(crate) fn recombination_backreaction_2nd(
    cumulants: &CumulantSet,
    rate_derivs: &RateDerivatives,
    t_r: f64,
    h: f64,
) -> f64 {
    // Temperature Jensen correction
    let delta_tr = 0.5 * rate_derivs.d2xe_dtr2 * t_r * t_r * cumulants.vartheta2;

    // Hubble Jensen correction (via escape probability curvature)
    let delta_h = 0.5 * rate_derivs.dxe_dh * h * cumulants.kappa2;

    // Cross term
    let delta_cross = rate_derivs.dxe_dtr * t_r * h * cumulants.vartheta_kappa;

    delta_tr + delta_h + delta_cross
}

// ═══ Off-Manifold Bound (P-IV.T5) ═══

/// Off-manifold deviation bound for Teff closure.
///
/// |Δẋ_e^off| ≤ |h_{x_e}'| × D_{≥2}^{(2D)}
///
/// where:
///   h_{x_e}' = ∂ẋ_e/∂x_e (rate Jacobian)
///   D_{≥2}^{(2D)} = tangency diagnostic (how far from invariant manifold)
///
/// If this bound is small compared to ẋ_e itself, the Teff closure is safe.
pub(crate) fn off_manifold_bound(
    rate_jacobian: f64,     // |∂ẋ_e/∂x_e| [s⁻¹]
    tangency_d2: f64,       // D_{≥2}^{(2D)} (dimensionless, from solver)
) -> f64 {
    rate_jacobian.abs() * tangency_d2
}

/// Relative off-manifold deviation.
///
/// Ratio = |Δẋ_e^off| / |ẋ_e|. If < ε, closure is valid to precision ε.
pub(crate) fn off_manifold_relative(
    rate_jacobian: f64,
    tangency_d2: f64,
    xe_dot: f64,
) -> f64 {
    if xe_dot.abs() < 1e-30 { return 0.0; }
    off_manifold_bound(rate_jacobian, tangency_d2) / xe_dot.abs()
}

// ═══ Impact Quantification ═══

/// Fractional matter temperature shift from Teff correction.
///
/// δT_m/T_m ≈ (Γ_C/H) × δΓ_C/Γ_C × (T_r−T_m)/T_m × Δt
///
/// At Compton equilibrium (T_m ≈ T_r): the correction enters through
/// the decoupling time — a slightly different Γ_C shifts when T_m
/// departs from T_r.
///
/// Order estimate: δT_m/T_m ~ 6⟨ϑ²⟩ × (Γ_C Δt_dec)
/// For BI at Σ² = 10⁻⁶: ⟨ϑ²⟩ ~ Σ² ~ 10⁻⁶, Γ_C Δt ~ O(1) at decoupling
/// → δT_m/T_m ~ 6 × 10⁻⁶
pub(crate) fn delta_tm_estimate(sigma2: f64) -> f64 {
    // ⟨ϑ²⟩ ~ Σ² for Bianchi-induced CMB anisotropy
    6.0 * sigma2
}

// ═══ BG-02 Bridge: PSTF F_ℓ → Angular Cumulants → Teff Correction ═══

/// Compute angular cumulants from PSTF multipoles F_ℓ via BG-02 reconstruction.
///
/// Uses reconstruct_theta to build Θ(ê) on S², then computes
/// {⟨ϑ²⟩, ⟨ϑ³⟩, ⟨ϑ⁴⟩} where ϑ = Θ − 1.
///
/// This replaces the analytical `angular_cumulants_from_sigma` (which uses
/// the approximation ⟨ϑ²⟩ ~ Σ²) with exact numerical integration.
pub(crate) fn angular_cumulants_from_pstf(
    f_ell: &[f64],
    sigma2_over_h2: f64,
    n_dir: usize,
) -> CumulantSet {
    let (_, theta_vals, weights) =
        crate::teff::positivity::reconstruct_theta(f_ell, n_dir);

    // Compute ⟨ϑ^k⟩ where ϑ = Θ − 1
    let mut sum_vt2 = 0.0;
    let mut sum_vt3 = 0.0;
    let mut sum_vt4 = 0.0;
    let mut wsum = 0.0;

    for (&theta, &w) in theta_vals.iter().zip(weights.iter()) {
        let vt = theta - 1.0; // ϑ = Θ − 1
        sum_vt2 += vt * vt * w;
        sum_vt3 += vt * vt * vt * w;
        sum_vt4 += vt * vt * vt * vt * w;
        wsum += w;
    }

    CumulantSet {
        vartheta2: sum_vt2 / wsum,
        vartheta3: sum_vt3 / wsum,
        vartheta4: sum_vt4 / wsum,
        kappa2: 2.0 / 15.0 * sigma2_over_h2, // exact STF integral (unchanged)
        vartheta_kappa: 0.0, // cross-cumulant: compute if F_ℓ × κ correlated
    }
}

/// Compute ⟨Θ⁴⟩ directly from PSTF multipoles via BG-02 reconstruction.
///
/// This is the numerical counterpart of `theta4_moment(CumulantSet)`.
pub(crate) fn theta4_from_pstf(f_ell: &[f64], n_dir: usize) -> f64 {
    let (_, theta_vals, weights) =
        crate::teff::positivity::reconstruct_theta(f_ell, n_dir);

    let mut sum = 0.0;
    let mut wsum = 0.0;
    for (&theta, &w) in theta_vals.iter().zip(weights.iter()) {
        sum += theta.powi(4) * w;
        wsum += w;
    }
    sum / wsum
}

/// Full Compton heating pipeline from PSTF state vector.
///
/// F_ℓ → Θ(ê) [BG-02] → CumulantSet → corrected Γ_C [BE-05f]
///
/// Includes positivity check: if Θ < 0 detected, uses enforced F_ℓ^{corr}.
pub(crate) fn compton_heating_from_pstf(
    f_ell: &[f64],
    t_m: f64,
    t_r: f64,
    x_e: f64,
    sigma2_over_h2: f64,
    n_dir: usize,
) -> (f64, bool) {
    // Step 1: Positivity check via BG-02
    let pos_result = crate::teff::positivity::enforce_and_reproject(
        f_ell, n_dir, crate::teff::positivity::THETA_FLOOR);

    let f_ell_safe = if pos_result.n_violations > 0 {
        &pos_result.f_ell_corrected
    } else {
        f_ell
    };

    // Step 2: Angular cumulants from corrected F_ℓ
    let cumulants = angular_cumulants_from_pstf(f_ell_safe, sigma2_over_h2, n_dir);

    // Step 3: Corrected Compton heating
    let rate = compton_heating_corrected(t_m, t_r, x_e, &cumulants);

    (rate, pos_result.n_violations > 0)
}

/// Cross-validation: compare analytical vs numerical ⟨Θ⁴⟩.
///
/// Returns (analytical, numerical, relative_error).
pub(crate) fn cross_validate_theta4(
    cumulants: &CumulantSet,
    f_ell: &[f64],
    n_dir: usize,
) -> (f64, f64, f64) {
    let analytical = theta4_moment(cumulants);
    let numerical = theta4_from_pstf(f_ell, n_dir);
    let rel = (analytical - numerical).abs() / numerical.abs().max(1e-30);
    (analytical, numerical, rel)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ═══ Θ⁴ bridge tests ═══

    #[test]
    fn test_flrw_theta4_is_one() {
        let c = CumulantSet::default();
        assert!((theta4_moment(&c) - 1.0).abs() < 1e-15, "FLRW: ⟨Θ⁴⟩ = 1");
    }

    #[test]
    fn test_flrw_radiation_temp() {
        let c = CumulantSet::default();
        let t_r = 3000.0;
        let t4 = radiation_temp_4th(t_r, &c);
        assert!((t4 - t_r.powi(4)).abs() < 1e-10, "FLRW: T_gamma4 = T_r^4");
    }

    #[test]
    fn test_theta4_bridge_coefficient() {
        // Verify the coefficient 6 = C(4,2) in the binomial expansion
        let c = CumulantSet { vartheta2: 0.01, ..Default::default() };
        let theta4 = theta4_moment(&c);
        // ⟨Θ⁴⟩ = 1 + 6 × 0.01 = 1.06
        assert!((theta4 - 1.06).abs() < 1e-10,
            "Θ⁴ bridge: ⟨Θ⁴⟩ = {:.6} (expect 1.06)", theta4);
    }

    #[test]
    fn test_theta4_leading_order() {
        let vt2 = 1e-6;
        let lo = theta4_leading_order(vt2);
        let full = theta4_moment(&CumulantSet { vartheta2: vt2, ..Default::default() });
        assert!((lo - full).abs() < 1e-12, "Leading order matches full at small ϑ²");
    }

    #[test]
    fn test_theta4_full_expansion() {
        // Full: 1 + 6⟨ϑ²⟩ + 4⟨ϑ³⟩ + ⟨ϑ⁴⟩
        let c = CumulantSet {
            vartheta2: 0.01, vartheta3: 0.001, vartheta4: 0.0003, ..Default::default()
        };
        let expected = 1.0 + 6.0 * 0.01 + 4.0 * 0.001 + 0.0003;
        assert!((theta4_moment(&c) - expected).abs() < 1e-12);
    }

    // ═══ Compton heating tests ═══

    #[test]
    fn test_compton_rate_positive() {
        let rate = compton_rate(3000.0, 0.1);
        assert!(rate > 0.0, "Compton rate must be positive: {:.4e}", rate);
    }

    #[test]
    fn test_compton_heating_flrw() {
        let c = CumulantSet::default();
        let corrected = compton_heating_corrected(2900.0, 3000.0, 0.1, &c);
        let standard = compton_rate(3000.0, 0.1) * (3000.0 - 2900.0);
        assert!((corrected - standard).abs() / standard.abs() < 1e-10,
            "FLRW: corrected = standard");
    }

    #[test]
    fn test_compton_correction_sign() {
        // ⟨Θ⁴⟩ > 1 means MORE energy transfer → faster equilibration
        let c = CumulantSet { vartheta2: 1e-4, ..Default::default() };
        let corr = compton_rate_correction(&c);
        assert!(corr > 0.0, "Anisotropy increases Compton rate: δΓ/Γ = {:.4e}", corr);
    }

    #[test]
    fn test_compton_correction_magnitude() {
        // δΓ_C/Γ_C ≈ 6⟨ϑ²⟩ at leading order
        let vt2 = 1e-6;
        let c = CumulantSet { vartheta2: vt2, ..Default::default() };
        let corr = compton_rate_correction(&c);
        assert!((corr - 6.0 * vt2).abs() / (6.0 * vt2) < 0.01,
            "δΓ/Γ = {:.4e}, 6⟨ϑ²⟩ = {:.4e}", corr, 6.0 * vt2);
    }

    // ═══ Angular cumulant tests ═══

    #[test]
    fn test_kappa2_from_shear() {
        // ⟨κ²⟩ = (2/15)(σ/H)²
        let soh2 = 1e-6;
        let c = angular_cumulants_from_sigma(soh2, 1e-8);
        assert!((c.kappa2 - 2.0 / 15.0 * soh2).abs() < 1e-20,
            "⟨κ²⟩ = {:.4e}, (2/15)(σ/H)² = {:.4e}", c.kappa2, 2.0 / 15.0 * soh2);
    }

    #[test]
    fn test_gaussian_kurtosis() {
        // Gaussian: ⟨ϑ⁴⟩ = 3⟨ϑ²⟩²
        let vt2 = 1e-4;
        let c = angular_cumulants_from_sigma(1e-6, vt2);
        assert!((c.vartheta4 - 3.0 * vt2 * vt2).abs() < 1e-20);
    }

    #[test]
    fn test_vartheta2_from_d2() {
        // D₂ = 1000 μK², T_CMB = 2.7255 K → ⟨ϑ²⟩ = 1000 / (2.7255e6)² ≈ 1.35e-10
        let vt2 = vartheta2_from_d2(1000.0, 2.7255);
        let expected = 1000.0 / (2.7255e6_f64).powi(2);
        assert!((vt2 - expected).abs() / expected < 1e-10);
    }

    // ═══ 2nd-order backreaction tests ═══

    #[test]
    fn test_backreaction_flrw_zero() {
        let c = CumulantSet::default();
        let rd = RateDerivatives { dxe_dtr: 1e-5, dxe_dh: 1e-3, d2xe_dtr2: 1e-8 };
        let delta = recombination_backreaction_2nd(&c, &rd, 3000.0, 1e-4);
        assert_eq!(delta, 0.0, "FLRW: δ²ẋ_e = 0");
    }

    #[test]
    fn test_backreaction_scaling() {
        let c1 = angular_cumulants_from_sigma(1e-6, 1e-8);
        let c2 = angular_cumulants_from_sigma(4e-6, 4e-8);
        let rd = RateDerivatives { dxe_dtr: 1e-5, dxe_dh: 1e-3, d2xe_dtr2: 1e-8 };
        let d1 = recombination_backreaction_2nd(&c1, &rd, 3000.0, 1e-4);
        let d2 = recombination_backreaction_2nd(&c2, &rd, 3000.0, 1e-4);
        // Should scale as ⟨ϑ²⟩ ∝ Σ²: d2/d1 ≈ 4
        if d1.abs() > 1e-30 {
            let ratio = d2 / d1;
            assert!((ratio - 4.0).abs() < 0.1,
                "Backreaction scaling: d2/d1 = {:.4}", ratio);
        }
    }

    // ═══ Off-manifold bound tests ═══

    #[test]
    fn test_off_manifold_bound_positive() {
        let b = off_manifold_bound(1e-3, 1e-6);
        assert!(b > 0.0 && b == 1e-9, "Bound = {:.4e}", b);
    }

    #[test]
    fn test_off_manifold_relative_small() {
        // If tangency diagnostic is tiny, closure is safe
        let rel = off_manifold_relative(1e-3, 1e-10, 1e-5);
        assert!(rel < 1e-2, "Relative off-manifold = {:.4e}", rel);
    }

    // ═══ Impact quantification tests ═══

    #[test]
    fn test_delta_tm_bi_sigma2_1e6() {
        // BI at Σ² = 10⁻⁶: δT_m/T_m ~ 6 × 10⁻⁶
        let dtm = delta_tm_estimate(1e-6);
        assert!((dtm - 6e-6).abs() < 1e-7, "δT_m/T_m = {:.4e}", dtm);
    }

    #[test]
    fn test_delta_tm_flrw_zero() {
        assert_eq!(delta_tm_estimate(0.0), 0.0);
    }

    #[test]
    fn test_delta_tm_tracked_not_dismissed() {
        let dtm_frac = delta_tm_estimate(1e-6);
        let dtm_abs = dtm_frac * 3000.0;
        assert!(dtm_abs < 1.0, "δT_m = {:.4} K (must < 1K at Σ²=10⁻⁶)", dtm_abs);
        assert!(dtm_abs > 0.0, "Must be tracked, not zero");
    }

    // ═══ BG-02 ↔ BE-05f Integration Tests ═══

    #[test]
    fn test_cumulants_from_pstf_isotropic() {
        // F_0 = 1, F_{ℓ>0} = 0 → Θ = 1 → ϑ = 0 → all cumulants = 0
        let f = vec![1.0, 0.0, 0.0, 0.0];
        let c = angular_cumulants_from_pstf(&f, 0.0, 8);
        assert!(c.vartheta2.abs() < 1e-10, "FLRW: ⟨ϑ²⟩ = {:.2e}", c.vartheta2);
        assert!(c.vartheta3.abs() < 1e-10);
        assert!(c.vartheta4.abs() < 1e-10);
    }

    #[test]
    fn test_cumulants_from_pstf_with_quadrupole() {
        // F_0 = 1, F_2 = 0.01 → ϑ has ℓ=2 structure → ⟨ϑ²⟩ > 0
        let f = vec![1.0, 0.0, 0.01, 0.0, 0.0];
        let c = angular_cumulants_from_pstf(&f, 0.0, 12);
        assert!(c.vartheta2 > 0.0, "⟨ϑ²⟩ = {:.4e} must be > 0", c.vartheta2);
    }

    #[test]
    fn test_theta4_from_pstf_flrw() {
        let f = vec![1.0, 0.0, 0.0];
        let t4 = theta4_from_pstf(&f, 8);
        assert!((t4 - 1.0).abs() < 1e-8, "FLRW: ⟨Θ⁴⟩ = {:.10}", t4);
    }

    #[test]
    fn test_theta4_analytical_vs_numerical() {
        // Small quadrupole: verify analytical 1 + 6⟨ϑ²⟩ matches numerical ⟨Θ⁴⟩
        let f = vec![1.0, 0.0, 0.005];
        let c = angular_cumulants_from_pstf(&f, 0.0, 16);
        let (ana, num, rel) = cross_validate_theta4(&c, &f, 16);
        assert!(rel < 0.05,
            "Cross-validation: analytical={:.8}, numerical={:.8}, rel={:.2e}", ana, num, rel);
    }

    #[test]
    fn test_compton_from_pstf_flrw() {
        let f = vec![1.0, 0.0, 0.0, 0.0];
        let (rate, violated) = compton_heating_from_pstf(&f, 2900.0, 3000.0, 0.1, 0.0, 8);
        assert!(!violated, "FLRW: no positivity violation");
        let standard = compton_rate(3000.0, 0.1) * (3000.0 - 2900.0);
        assert!((rate - standard).abs() / standard.abs() < 1e-4,
            "FLRW pipeline: rate={:.4e}, standard={:.4e}", rate, standard);
    }

    #[test]
    fn test_compton_from_pstf_with_anisotropy() {
        let f = vec![1.0, 0.0, 0.01]; // small F_2
        let (rate_aniso, _) = compton_heating_from_pstf(&f, 2900.0, 3000.0, 0.1, 1e-6, 12);
        let (rate_iso, _) = compton_heating_from_pstf(
            &vec![1.0, 0.0, 0.0], 2900.0, 3000.0, 0.1, 0.0, 12);
        // Anisotropy increases Compton rate (⟨Θ⁴⟩ > 1)
        assert!(rate_aniso > rate_iso,
            "Aniso rate {:.4e} must > iso rate {:.4e}", rate_aniso, rate_iso);
    }

    #[test]
    fn test_positivity_triggers_in_pipeline() {
        // Large F_2 ≫ F_0 → forces positivity violation → correction applied
        let f = vec![0.1, 0.0, 0.5];
        let (rate, violated) = compton_heating_from_pstf(&f, 2900.0, 3000.0, 0.1, 0.0, 12);
        assert!(violated, "Must detect positivity violation");
        assert!(rate.is_finite(), "Rate must be finite after correction: {:.4e}", rate);
    }

    #[test]
    fn test_cumulant_consistency_sigma_vs_pstf() {
        // Compare analytical (from σ/H) vs numerical (from F_ℓ) cumulants
        // For small F_2 ~ (σ/H), both should give similar ⟨ϑ²⟩
        let eps = 0.001; // small perturbation
        let f = vec![1.0, 0.0, eps];
        let c_pstf = angular_cumulants_from_pstf(&f, eps * eps, 16);
        // ⟨ϑ²⟩ from F_2 = eps: ⟨(eps × P_2)²⟩_Ω = eps² × ⟨P_2²⟩ = eps² / 5
        let expected_vt2 = eps * eps / 5.0;
        let rel = (c_pstf.vartheta2 - expected_vt2).abs() / expected_vt2.max(1e-30);
        assert!(rel < 0.1,
            "⟨ϑ²⟩: PSTF={:.4e}, expected={:.4e}, rel={:.2e}", c_pstf.vartheta2, expected_vt2, rel);
    }
}
