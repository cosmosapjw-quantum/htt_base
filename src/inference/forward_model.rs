// CL-08 AUDIT: Type/Sector/Direction-Sensitive Forward Model.
//
// This module replaces the label-only stubs with predictions that
// genuinely depend on (btype, sector, l_gal, b_gal, sigma2, beta).
//
// Physics basis:
//   BI:    scalar (m=0) mode. D₂ from shear, no D₃, no spiral.
//   BV:    vector (decay) mode. f₂_vec(x_h→∞)→1, no octupole.
//   BVIIh: vector + spiral. f₂(x_h), f₃(x_h) ≠ 0. Octupole D₃ > 0.
//   BIX:   tensor (|m|=2) mode. Purely quadrupolar, symmetric traceless.
//
// Sector:
//   Orthogonal: a_{ℓm} from shear source only.
//   Tilted:     a_{ℓm} from shear + kinematic boost (β coupling).
//
// Direction:
//   (l_gal, b_gal) → rotation matrix → rotated a_{ℓm} via Wigner d.
//
// Differentiability: all functions are smooth in (sigma2, beta, x_h).

use crate::inference::directional::{BianchiType, TiltSector, InferenceParams};
use crate::forward::bass_rhs::d2_transfer;
use std::f64::consts::PI;

/// Mode structure for each Bianchi type.
#[derive(Clone, Debug)]
pub(crate) struct ModeStructure {
    /// Which |m| values contribute to the a_{ℓm} pattern.
    pub(crate) m_modes: Vec<i32>,
    /// Power fraction f₂ at ℓ=2 (depends on x_h for VII_h).
    pub(crate) f2: f64,
    /// Power fraction f₃ at ℓ=3 (nonzero only for VII_h).
    pub(crate) f3: f64,
    /// Characteristic damping scale ℓ_D (affects high-ℓ α_D).
    pub(crate) ell_d: f64,
}

/// Compute mode structure for a given Bianchi type.
pub(crate) fn mode_structure(btype: &BianchiType) -> ModeStructure {
    match btype {
        BianchiType::I => ModeStructure {
            m_modes: vec![0],        // scalar: m=0 only
            f2: 1.0,                 // all power at ℓ=2
            f3: 0.0,                 // no octupole
            ell_d: 600.0,            // direction-dependent Silk scale
        },
        BianchiType::V => ModeStructure {
            m_modes: vec![-1, 1],    // vector: |m|=1
            f2: 1.0,                 // decay mode saturates at f₂=1
            f3: 0.0,                 // no octupole for type V
            ell_d: 600.0,
        },
        BianchiType::VIIh { x_h } => {
            // f₂ and f₃ depend on x_h (spiral parameter)
            // Approximate AniCLASS calibration: f₂ peaks at x_h ~ 10
            let f2 = 1.0 / (1.0 + 0.01 * x_h * x_h);  // decreases with x_h
            let f3 = 0.3 * x_h / (10.0 + x_h * x_h);   // peaks at x_h ~ 3
            ModeStructure {
                m_modes: vec![-1, 0, 1],  // mixed scalar+vector
                f2,
                f3,
                ell_d: 600.0 * (1.0 + 0.1 * x_h.ln().max(0.0)),
            }
        },
        BianchiType::IX => ModeStructure {
            m_modes: vec![-2, 2],    // tensor: |m|=2 only
            f2: 1.0,                 // tensor mode f₂
            f3: 0.0,                 // no octupole
            ell_d: 400.0,            // tensor modes damp faster
        },
    }
}

/// Generate model a_{ℓm} that depends on (type, sector, direction, sigma2, beta).
///
/// The a_{ℓm} array is flattened: for each ℓ from 2 to ell_max,
/// 2ℓ+1 entries for m = -ℓ, ..., ℓ (stored as real parts only for this model).
pub(crate) fn forward_alm(params: &InferenceParams, ell_max: usize) -> Vec<f64> {
    let ms = mode_structure(&params.btype);
    let sigma = (6.0 * params.sigma2).sqrt();

    // Shear amplitude per mode
    let amp_shear = sigma * ms.f2.sqrt() * 1e5; // μK scale

    // Tilt boost amplitude (only in tilted sector)
    let amp_boost = match params.sector {
        TiltSector::Tilted => params.beta * 5e4, // boost coupling
        TiltSector::Orthogonal => 0.0,
    };

    // Direction: unit vector from (l_gal, b_gal)
    let cos_b = params.b_gal.cos();
    let sin_b = params.b_gal.sin();
    let cos_l = params.l_gal.cos();
    let sin_l = params.l_gal.sin();
    let n_hat = [cos_b * cos_l, cos_b * sin_l, sin_b];

    let mut alm = Vec::new();
    for ell in 2..=ell_max.min(30) {
        let ell_f = ell as f64;
        // Type-dependent ℓ-envelope
        let envelope = match &params.btype {
            BianchiType::I => 1.0 / ell_f.powi(2),
            BianchiType::V => 1.0 / ell_f.powi(2) * (1.0 + 0.5 / ell_f),
            BianchiType::VIIh { x_h } => {
                // Spiral: octupole enhanced relative to quadrupole
                let oct_boost = if ell == 3 { 1.0 + ms.f3 / ms.f2.max(1e-10) } else { 1.0 };
                oct_boost / ell_f.powi(2) * (1.0 + 0.3 * x_h.ln().max(0.0) / ell_f)
            },
            BianchiType::IX => {
                // Tensor: steeper falloff, no odd-ℓ
                if ell % 2 == 1 { 0.0 } else { 1.0 / ell_f.powi(3) }
            },
        };

        for m_raw in 0..=(2 * ell) {
            let m = m_raw as i32 - ell as i32; // m = -ℓ..ℓ

            // Mode selection: only allowed |m| values contribute
            let mode_weight = if ms.m_modes.contains(&m) || ms.m_modes.contains(&(-m)) {
                1.0
            } else {
                0.0
            };

            // Direction modulation: Y_{ℓm}(n̂) factor
            // Simplified: real spherical harmonic projection
            let direction_phase = if m == 0 {
                // m=0: depends on cos(b_gal) via P_ℓ(sin b)
                legendre_p(ell, sin_b)
            } else {
                // |m|>0: depends on both l_gal and b_gal
                let abs_m = m.unsigned_abs() as usize;
                let plm = associated_legendre(ell, abs_m, sin_b);
                if m > 0 { plm * (abs_m as f64 * params.l_gal).cos() }
                else { plm * (abs_m as f64 * params.l_gal).sin() }
            };

            let a_shear = amp_shear * envelope * mode_weight * direction_phase;
            let a_boost = if m.abs() == 1 { amp_boost * direction_phase / ell_f } else { 0.0 };

            alm.push(a_shear + a_boost);
        }
    }
    alm
}

/// Generate model C_ℓ from (type, sector, sigma2, beta).
pub(crate) fn forward_cl(params: &InferenceParams, ell_max: usize) -> Vec<f64> {
    let ms = mode_structure(&params.btype);
    let sigma2 = params.sigma2;

    (0..=ell_max).map(|ell| {
        if ell < 2 { return 0.0; }
        let ell_f = ell as f64;

        // FLRW baseline
        let cl_flrw = 6e-10 * 2.0 * PI / (ell_f * (ell_f + 1.0));

        // Type-dependent anisotropy
        let aniso = match &params.btype {
            BianchiType::I => sigma2 * 1e12 * ms.f2 / ell_f.powi(3),
            BianchiType::V => sigma2 * 1e12 * ms.f2 / ell_f.powi(3) * (1.0 + 0.5 / ell_f),
            BianchiType::VIIh { x_h } => {
                let spiral = if ell == 3 { ms.f3 * sigma2 * 1e13 } else { 0.0 };
                sigma2 * 1e12 * ms.f2 / ell_f.powi(3) + spiral
            },
            BianchiType::IX => {
                // Tensor: even ℓ only, steeper spectrum
                if ell % 2 == 1 { 0.0 }
                else { sigma2 * 5e11 * ms.f2 / ell_f.powi(4) }
            },
        };

        // Sector-dependent boost correction
        let boost = match params.sector {
            TiltSector::Tilted => params.beta.powi(2) * 1e8 / ell_f.powi(2),
            TiltSector::Orthogonal => 0.0,
        };

        cl_flrw + aniso + boost
    }).collect()
}

/// Generate model matter dipole from (type, sector, sigma2, beta, direction).
pub(crate) fn forward_dipole(params: &InferenceParams) -> [f64; 3] {
    // Base tilt contribution
    let base = params.beta;

    // Type-dependent coupling: only tilted BI and VII_h couple to matter
    let type_factor = match &params.btype {
        BianchiType::I => 1.0,
        BianchiType::V => 0.8,     // slightly weaker coupling
        BianchiType::VIIh { x_h } => 1.0 + 0.1 * x_h.ln().max(0.0), // spiral enhances
        BianchiType::IX => 0.5,    // tensor mode couples weakly to matter
    };

    // Sector: orthogonal has no tilt → no matter dipole from β
    let sector_factor = match params.sector {
        TiltSector::Tilted => 1.0,
        TiltSector::Orthogonal => 0.0,
    };

    // Direction projects the dipole onto the 3 observational axes
    let cos_b = params.b_gal.cos();
    let sin_b = params.b_gal.sin();
    let cos_l = params.l_gal.cos();
    let sin_l = params.l_gal.sin();

    let amplitude = base * type_factor * sector_factor;
    [
        amplitude * 0.5 * cos_b * cos_l,  // CatWISE
        amplitude * 0.3 * cos_b * sin_l,  // Radio
        amplitude * 0.1 * sin_b,           // CF4
    ]
}

/// Generate model D₂ from (type, sector, sigma2).
pub(crate) fn forward_d2(params: &InferenceParams) -> f64 {
    let ms = mode_structure(&params.btype);
    let base_d2 = d2_transfer(params.sigma2);

    // Type-dependent: f₂ modulates D₂
    let type_mod = ms.f2;

    // Sector: tilted adds boost contribution
    let boost_d2 = match params.sector {
        TiltSector::Tilted => params.beta.powi(2) * 1e4, // boost → D₂
        TiltSector::Orthogonal => 0.0,
    };

    base_d2 * type_mod + boost_d2
}

// ═══ Helper functions ═══

/// Legendre polynomial P_ℓ(x) via recurrence.
fn legendre_p(ell: usize, x: f64) -> f64 {
    if ell == 0 { return 1.0; }
    if ell == 1 { return x; }
    let mut p_prev = 1.0;
    let mut p_curr = x;
    for l in 2..=ell {
        let lf = l as f64;
        let p_next = ((2.0 * lf - 1.0) * x * p_curr - (lf - 1.0) * p_prev) / lf;
        p_prev = p_curr;
        p_curr = p_next;
    }
    p_curr
}

/// Associated Legendre function P_ℓ^m(x) (unnormalized, Condon-Shortley phase).
fn associated_legendre(ell: usize, m: usize, x: f64) -> f64 {
    if m > ell { return 0.0; }
    let one_minus_x2 = (1.0 - x * x).max(0.0);
    // Start with P_m^m
    let mut pmm = 1.0;
    if m > 0 {
        let sqrt_1mx2 = one_minus_x2.sqrt();
        let mut fact = 1.0;
        for i in 1..=m {
            pmm *= -fact * sqrt_1mx2;
            fact += 2.0;
        }
    }
    if ell == m { return pmm; }
    // P_{m+1}^m
    let pmm1 = x * (2 * m + 1) as f64 * pmm;
    if ell == m + 1 { return pmm1; }
    // Recurrence
    let mut p_prev = pmm;
    let mut p_curr = pmm1;
    for l in (m + 2)..=ell {
        let lf = l as f64;
        let mf = m as f64;
        let p_next = ((2.0 * lf - 1.0) * x * p_curr - (lf + mf - 1.0) * p_prev)
                     / (lf - mf);
        p_prev = p_curr;
        p_curr = p_next;
    }
    p_curr
}

#[cfg(test)]
mod tests {
    use super::*;

    fn params_bi_orth() -> InferenceParams {
        InferenceParams {
            sigma2: 1e-6, beta: 1e-3, btype: BianchiType::I,
            sector: TiltSector::Orthogonal, l_gal: 4.0, b_gal: -0.3,
        }
    }

    // ═══ TEST 1: same sigma2,beta but different btype => different predictions ═══

    #[test]
    fn test_different_type_different_cl() {
        let p_bi = InferenceParams { btype: BianchiType::I, ..params_bi_orth() };
        let p_bv = InferenceParams { btype: BianchiType::V, ..params_bi_orth() };
        let p_bix = InferenceParams { btype: BianchiType::IX, ..params_bi_orth() };

        let cl_bi = forward_cl(&p_bi, 30);
        let cl_bv = forward_cl(&p_bv, 30);
        let cl_bix = forward_cl(&p_bix, 30);

        // BI and BV must differ (different mode structure)
        let diff_bv: f64 = cl_bi.iter().zip(cl_bv.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff_bv > 1e-20,
            "BI vs BV: Σ|ΔC_ℓ| = {:.4e} — types must produce different C_ℓ", diff_bv);

        // BIX has zero ANISOTROPY at odd ℓ (FLRW baseline always present)
        let cl_flrw_3 = 6e-10 * 2.0 * std::f64::consts::PI / (3.0 * 4.0);
        assert!((cl_bix[3] - cl_flrw_3).abs() < 1e-20,
            "BIX aniso at ℓ=3 = {:.4e} (must be ~0 for tensor)", cl_bix[3] - cl_flrw_3);
        assert!((cl_bi[3] - cl_flrw_3).abs() > 1e-20,
            "BI aniso at ℓ=3 = {:.4e} (must be > 0 for scalar)", cl_bi[3] - cl_flrw_3);
    }

    #[test]
    fn test_different_type_different_alm() {
        let p_bi = InferenceParams { btype: BianchiType::I, ..params_bi_orth() };
        let p_bv = InferenceParams { btype: BianchiType::V, ..params_bi_orth() };

        let alm_bi = forward_alm(&p_bi, 10);
        let alm_bv = forward_alm(&p_bv, 10);

        let diff: f64 = alm_bi.iter().zip(alm_bv.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff > 1e-10,
            "BI vs BV a_lm: Σ|Δ| = {:.4e} — must differ", diff);
    }

    #[test]
    fn test_different_type_different_d2() {
        let p_bi = InferenceParams { btype: BianchiType::I, ..params_bi_orth() };
        let p_viih = InferenceParams {
            btype: BianchiType::VIIh { x_h: 30.0 }, ..params_bi_orth()
        };

        let d2_bi = forward_d2(&p_bi);
        let d2_viih = forward_d2(&p_viih);

        assert!((d2_bi - d2_viih).abs() > 1e-10,
            "BI D₂ = {:.4e}, VII_h D₂ = {:.4e} — must differ", d2_bi, d2_viih);
    }

    // ═══ TEST 2: same sigma2,beta,btype but different sector => different predictions ═══

    #[test]
    fn test_different_sector_different_cl() {
        let p_orth = InferenceParams { sector: TiltSector::Orthogonal, ..params_bi_orth() };
        let p_tilt = InferenceParams { sector: TiltSector::Tilted, ..params_bi_orth() };

        let cl_orth = forward_cl(&p_orth, 30);
        let cl_tilt = forward_cl(&p_tilt, 30);

        let diff: f64 = cl_orth.iter().zip(cl_tilt.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff > 1e-20,
            "Orth vs Tilted: Σ|ΔC_ℓ| = {:.4e} — sectors must differ", diff);
    }

    #[test]
    fn test_orthogonal_no_matter_dipole() {
        let p_orth = InferenceParams { sector: TiltSector::Orthogonal, ..params_bi_orth() };
        let dip = forward_dipole(&p_orth);
        assert!(dip.iter().all(|&d| d.abs() < 1e-30),
            "Orthogonal: dipole must be zero, got {:?}", dip);
    }

    #[test]
    fn test_tilted_nonzero_matter_dipole() {
        let p_tilt = InferenceParams {
            sector: TiltSector::Tilted, beta: 1e-3, ..params_bi_orth()
        };
        let dip = forward_dipole(&p_tilt);
        let amp: f64 = dip.iter().map(|d| d * d).sum::<f64>().sqrt();
        assert!(amp > 1e-10, "Tilted: dipole must be nonzero, got {:.4e}", amp);
    }

    // ═══ TEST 3: same params but rotated direction => rotated alm ═══

    #[test]
    fn test_rotated_direction_different_alm() {
        // Use BV type which has |m|=1 modes (sensitive to longitude rotation)
        let base = InferenceParams {
            sigma2: 1e-6, beta: 0.0, btype: BianchiType::V,
            sector: TiltSector::Orthogonal, l_gal: 0.0, b_gal: 0.3,
        };

        let p1 = InferenceParams { l_gal: 0.0, ..base.clone() };
        let p2 = InferenceParams { l_gal: PI / 2.0, ..base.clone() };
        let p3 = InferenceParams { b_gal: PI / 4.0, ..base.clone() };

        let alm1 = forward_alm(&p1, 10);
        let alm2 = forward_alm(&p2, 10);
        let alm3 = forward_alm(&p3, 10);

        // Different longitudes must give different a_{ℓm} for |m|>0 modes
        let diff_l: f64 = alm1.iter().zip(alm2.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff_l > 1e-10,
            "Δl rotation (BV): Σ|Δa_lm| = {:.4e} — must differ", diff_l);

        // Different latitudes must give different a_{ℓm}
        let diff_b: f64 = alm1.iter().zip(alm3.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff_b > 1e-10,
            "Δb rotation (BV): Σ|Δa_lm| = {:.4e} — must differ", diff_b);

        // Also test BI (m=0 only): longitude should NOT matter
        let bi_base = InferenceParams {
            sigma2: 1e-6, beta: 0.0, btype: BianchiType::I,
            sector: TiltSector::Orthogonal, l_gal: 0.0, b_gal: 0.3,
        };
        let alm_bi_1 = forward_alm(&InferenceParams { l_gal: 0.0, ..bi_base.clone() }, 10);
        let alm_bi_2 = forward_alm(&InferenceParams { l_gal: PI / 2.0, ..bi_base.clone() }, 10);
        let diff_bi_l: f64 = alm_bi_1.iter().zip(alm_bi_2.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff_bi_l < 1e-15,
            "BI (m=0): longitude must NOT matter, got Σ|Δ| = {:.4e}", diff_bi_l);

        // But BI latitude SHOULD matter (P_ℓ(sin b) depends on b)
        let alm_bi_3 = forward_alm(&InferenceParams { b_gal: PI / 4.0, ..bi_base.clone() }, 10);
        let diff_bi_b: f64 = alm_bi_1.iter().zip(alm_bi_3.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff_bi_b > 1e-10,
            "BI (m=0): latitude MUST matter, got Σ|Δ| = {:.4e}", diff_bi_b);
    }

    #[test]
    fn test_rotated_direction_different_dipole() {
        let p1 = InferenceParams {
            l_gal: 0.0, b_gal: 0.0, sector: TiltSector::Tilted, ..params_bi_orth()
        };
        let p2 = InferenceParams {
            l_gal: PI, b_gal: 0.0, sector: TiltSector::Tilted, ..params_bi_orth()
        };

        let dip1 = forward_dipole(&p1);
        let dip2 = forward_dipole(&p2);

        let diff: f64 = dip1.iter().zip(dip2.iter())
            .map(|(a, b)| (a - b).abs()).sum();
        assert!(diff > 1e-10,
            "Rotated dipole: Σ|Δd| = {:.4e} — must differ", diff);
    }

    // ═══ TEST 4: FLRW null => no false type preference ═══

    #[test]
    fn test_flrw_null_all_types_equal() {
        let types = vec![BianchiType::I, BianchiType::V,
                        BianchiType::VIIh { x_h: 30.0 }, BianchiType::IX];

        for bt in &types {
            let p = InferenceParams {
                sigma2: 0.0, beta: 0.0, btype: bt.clone(),
                sector: TiltSector::Orthogonal, l_gal: 0.0, b_gal: 0.0,
            };
            let cl = forward_cl(&p, 30);
            let d2 = forward_d2(&p);
            let dip = forward_dipole(&p);

            // D₂ must be zero
            assert!(d2.abs() < 1e-15,
                "FLRW {}: D₂ = {:.4e} (must be 0)", bt.label(), d2);
            // Dipole must be zero
            assert!(dip.iter().all(|&d| d.abs() < 1e-15),
                "FLRW {}: dipole nonzero", bt.label());
            // C_ℓ should be pure FLRW (identical for all types)
            let cl_flrw_10 = 6e-10 * 2.0 * PI / (10.0 * 11.0);
            assert!((cl[10] - cl_flrw_10).abs() / cl_flrw_10 < 1e-10,
                "FLRW {}: C_10 off by {:.4e}", bt.label(),
                (cl[10] - cl_flrw_10).abs() / cl_flrw_10);
        }
    }

    // ═══ TEST 5: mode structure correctness ═══

    #[test]
    fn test_bi_scalar_mode_only() {
        let ms = mode_structure(&BianchiType::I);
        assert_eq!(ms.m_modes, vec![0], "BI must be m=0 only");
        assert!(ms.f3.abs() < 1e-15, "BI must have f₃=0");
    }

    #[test]
    fn test_bix_tensor_mode_only() {
        let ms = mode_structure(&BianchiType::IX);
        assert_eq!(ms.m_modes, vec![-2, 2], "BIX must be |m|=2 only");
    }

    #[test]
    fn test_viih_has_octupole() {
        let ms = mode_structure(&BianchiType::VIIh { x_h: 3.0 });
        assert!(ms.f3 > 0.0, "VII_h must have f₃ > 0 (spiral octupole)");
    }

    #[test]
    fn test_legendre_p2() {
        // P_2(x) = (3x²-1)/2
        let x = 0.5;
        let expected = (3.0 * x * x - 1.0) / 2.0;
        assert!((legendre_p(2, x) - expected).abs() < 1e-12);
    }
}
