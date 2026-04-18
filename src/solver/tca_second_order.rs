//! TF-05: CRS Second-Order TCA Corrections.
//!
//! Implements Cyr-Racine & Sigurdson (PRD 83, 103521, 2011) corrections:
//!   1. Quasi-static F₂ with (1 + 11κ̈/(6κ'²)) factor
//!   2. F₃, E₂, E₃ initialization at switch point
//!
//! These reduce TCA→full transition error from ~0.3% to ~0.03% in C_ℓ^TT.

/// Compute dκ̇/dη numerically from the visibility grid.
///
/// Uses centered differences away from boundaries.
pub(crate) fn compute_dopacity(
    vis_kappa_dot: &[f64],
    vis_eta: &[f64],
    i: usize,
) -> f64 {
    let n = vis_kappa_dot.len();
    if n < 2 { return 0.0; }
    if i == 0 {
        let deta = vis_eta[1] - vis_eta[0];
        if deta.abs() < 1e-30 { return 0.0; }
        (vis_kappa_dot[1] - vis_kappa_dot[0]) / deta
    } else if i >= n - 1 {
        let deta = vis_eta[n-1] - vis_eta[n-2];
        if deta.abs() < 1e-30 { return 0.0; }
        (vis_kappa_dot[n-1] - vis_kappa_dot[n-2]) / deta
    } else {
        let deta = vis_eta[i+1] - vis_eta[i-1];
        if deta.abs() < 1e-30 { return 0.0; }
        (vis_kappa_dot[i+1] - vis_kappa_dot[i-1]) / deta
    }
}

/// CRS second-order F₂ (quasi-static photon quadrupole).
///
/// F₂ = F₂⁽¹⁾ × (1 + 11κ̈/(6κ'²)) + F₂_time_deriv
///
/// In bass_rs convention (F_ℓ = (2ℓ+1)Θ_ℓ, conformal Newtonian gauge):
///   F₂⁽¹⁾ = (8/9)(k/κ̇)v_b + shear_term
///   CRS correction: multiply by (1 + 11·dκ̇/(6κ̇²))
///   Time derivative term: -(8/9)(k/κ̇²) × dv_b/dη × (11/6)
pub(crate) fn f2_second_order(
    k: f64,
    v_b: f64,
    dv_b_deta: f64,
    kappa_dot: f64,
    dkappa_dot: f64,  // dκ̇/dη
    sigma_h: f64,
    a_h: f64,
) -> f64 {
    if kappa_dot.abs() < 1e-30 { return 0.0; }
    let kd = kappa_dot;

    // First-order streaming + shear
    let f2_stream_1st = (8.0 / 9.0) * k * v_b / kd;
    let f2_shear_1st = (8.0 / 15.0) * sigma_h * a_h / kd;
    let f2_1st = f2_stream_1st + f2_shear_1st;

    // CRS correction factor: (1 + 11·dκ̇/(6κ̇²))
    let crs_factor = 1.0 + 11.0 * dkappa_dot / (6.0 * kd * kd);

    // Time derivative term: -(8/9)(k/κ̇²)(11/6)·dv_b/dη
    let f2_time_deriv = -(8.0 / 9.0) * k * dv_b_deta * 11.0 / (6.0 * kd * kd);

    f2_1st * crs_factor + f2_time_deriv
}

/// CRS second-order switch initialization: F₃, E₂, E₃.
///
/// From CAMB Notes §3.2 + CRS (2011):
///   I₃ = (3/7)π_γ(k/κ')(1 + κ̈/κ'²) − (3/7)π̇_γ(k/κ'²)
///   E₂ = π_γ/4 − (5/8)(π̇_γ/κ')(1 + 5κ̈/(2κ'²)) − (5/56)π_γ(k/κ')²
///   E₃ = (3/7)(k/κ')E₂(1 + κ̈/κ'²)
///
/// Converted to bass_rs F_ℓ = (2ℓ+1)I_ℓ/4:
///   F₃ = 7·I₃/4, F_E₂ = 5·E₂/4
pub(crate) struct CRSSwitchValues {
    pub(crate) f3: f64,
    pub(crate) e2: f64,
    pub(crate) e3: f64,
}

pub(crate) fn crs_switch_init(
    f2: f64,         // F₂ at switch point (bass_rs convention)
    df2_deta: f64,   // dF₂/dη at switch
    k: f64,
    kappa_dot: f64,
    dkappa_dot: f64,
) -> CRSSwitchValues {
    if kappa_dot.abs() < 1e-30 {
        return CRSSwitchValues { f3: 0.0, e2: 0.0, e3: 0.0 };
    }
    let kd = kappa_dot;

    // Convert F₂ → π_γ (CAMB convention): π_γ = (4/5)F₂
    let pig = (4.0 / 5.0) * f2;
    let pigdot = (4.0 / 5.0) * df2_deta;

    let dkd_ratio = dkappa_dot / (kd * kd);

    // I₃ = (3/7)π_γ(k/κ')(1 + κ̈/κ'²) − (3/7)π̇_γ(k/κ'²)
    let i3 = (3.0 / 7.0) * pig * (k / kd) * (1.0 + dkd_ratio)
           - (3.0 / 7.0) * pigdot * k / (kd * kd);

    // E₂ = π_γ/4 − (5/8)(π̇_γ/κ')(1 + 5κ̈/(2κ'²)) − (5/56)π_γ(k/κ')²
    let e2_camb = pig / 4.0
        - (5.0 / 8.0) * (pigdot / kd) * (1.0 + 2.5 * dkd_ratio)
        - (5.0 / 56.0) * pig * (k / kd).powi(2);

    // E₃ = (3/7)(k/κ')E₂(1 + κ̈/κ'²) − (3/7)(k/κ'²)(π̇_γ/4)(1 + 5κ̈/(2κ'²))
    let e3_camb = (3.0 / 7.0) * (k / kd) * e2_camb * (1.0 + dkd_ratio)
        - (3.0 / 7.0) * (k / (kd * kd)) * (pigdot / 4.0) * (1.0 + 2.5 * dkd_ratio);

    // Convert to bass_rs: F₃ = 7·I₃/4, F_E₂ = 5·E₂/4
    CRSSwitchValues {
        f3: 7.0 * i3 / 4.0,
        e2: 5.0 * e2_camb / 4.0,
        e3: 7.0 * e3_camb / 4.0,
    }
}

/// Enhanced state expansion with CRS second-order corrections.
pub(crate) fn expand_with_crs(
    theta0: f64, v_b: f64, delta_b: f64, v_c: f64, delta_c: f64, phi: f64,
    k: f64, a_h: f64, kappa_dot: f64, dkappa_dot: f64,
    dv_b_deta: f64, sigma_h: f64,
    lg: usize, ln: usize,
) -> Vec<f64> {
    let n_state = lg + 1 + ln + 1 + 5;
    let mut y = vec![0.0; n_state];

    // Photon
    y[0] = theta0;
    if lg >= 1 { y[1] = v_b; }
    if lg >= 2 {
        y[2] = f2_second_order(k, v_b, dv_b_deta, kappa_dot, dkappa_dot, sigma_h, a_h);
    }
    if lg >= 3 {
        let df2 = 0.0; // approximate: df₂/dη small at switch
        let crs = crs_switch_init(y[2], df2, k, kappa_dot, dkappa_dot);
        y[3] = crs.f3;
    }

    // Neutrino
    let n0 = lg + 1;
    y[n0] = -0.5 * phi;
    if ln >= 1 && a_h.abs() > 1e-30 { y[n0+1] = k * phi / (6.0 * a_h); }
    if ln >= 2 && a_h.abs() > 1e-30 { y[n0+2] = (k / (2.0 * a_h)).powi(2) * phi / 3.0; }

    // CDM
    let dc = n0 + ln + 1;
    y[dc] = delta_c;
    y[dc+1] = v_c;

    // Baryon
    y[dc+2] = delta_b;
    y[dc+3] = v_b;

    // Phi
    y[n_state-1] = phi;
    y
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_f2_first_order_limit() {
        // When dκ̇=0 and dv_b=0: reduces to first-order
        let f2_2nd = f2_second_order(0.01, 0.01, 0.0, 1e4, 0.0, 0.0, 100.0);
        let f2_1st = (8.0 / 9.0) * 0.01 * 0.01 / 1e4;
        assert!((f2_2nd - f2_1st).abs() < 1e-15, "Should reduce to 1st order");
    }

    #[test]
    fn test_crs_correction_sign() {
        // κ̈ < 0 (opacity decreasing) → correction factor < 1
        let f2_neg = f2_second_order(0.01, 0.01, 0.0, 1e4, -1e6, 0.0, 100.0);
        let f2_zero = f2_second_order(0.01, 0.01, 0.0, 1e4, 0.0, 0.0, 100.0);
        assert!(f2_neg.abs() < f2_zero.abs(), "Decreasing opacity should reduce F₂");
    }

    #[test]
    fn test_crs_switch_first_order_limit() {
        // dκ̇=0, pigdot=0: I₃ = (3/7)pig(k/κ'), E₂ = pig/4
        let f2 = 1e-6;
        let crs = crs_switch_init(f2, 0.0, 0.01, 1e4, 0.0);
        let pig = (4.0 / 5.0) * f2;
        let i3_expected = (3.0 / 7.0) * pig * 0.01 / 1e4;
        let f3_expected = 7.0 * i3_expected / 4.0;
        assert!((crs.f3 - f3_expected).abs() < 1e-20, "F₃ 1st order: {:.4e} vs {:.4e}", crs.f3, f3_expected);
        let e2_expected = 5.0 * (pig / 4.0) / 4.0;
        assert!((crs.e2 - e2_expected).abs() / e2_expected.abs().max(1e-30) < 0.01,
            "E₂ 1st order: {:.4e} vs {:.4e}", crs.e2, e2_expected);
    }

    #[test]
    fn test_expand_with_crs_dimensions() {
        let y = expand_with_crs(-0.5, 0.01, -1.5, 0.005, -1.5, 0.8,
            0.01, 100.0, 1e4, -1e6, 0.001, 0.0, 15, 8);
        assert_eq!(y.len(), 30);
    }

    #[test]
    fn test_dopacity_centered() {
        let kd = vec![1e5, 1e4, 1e3, 1e2, 10.0];
        let eta = vec![0.0, 100.0, 200.0, 300.0, 400.0];
        let dkd = compute_dopacity(&kd, &eta, 2);
        // Centered: (1e2 - 1e4) / (300 - 100) = -9900/200 = -49.5
        assert!((dkd - (-49.5)).abs() < 0.1, "dκ̇ = {:.2}", dkd);
    }
}
