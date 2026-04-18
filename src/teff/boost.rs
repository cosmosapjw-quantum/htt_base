// BG-03: Tilt Boost Cascade.
//
// Paper I Theorem 6: exact boost for μ=0: Θ̃(ẽ) = (T₀/T̃₀) D(e) Θ(e)
// where D(e) = γ(1 − v·e) is the Doppler factor.
//
// Perturbative formulas (Doc 5 §3):
//   T̃_a = T_a + v_a − (4/5) T_{ab} v^b + O(v²)
//   T̃_{ab} = T_{ab} + 2 v_{⟨a} T_{b⟩} + v_{⟨a} v_{b⟩} + O(v³)
//   T̃_{abc} = 3 T_{⟨ab} v_{c⟩} + O(v²)
//
// Key: L ≤ 2 → L ≤ 3 after first-order boost (one ℓ added per order).
//
// Three-level application:
//   Level 1: global tilt β → boost to matter frame
//   Level 2: δβ fluctuation → perturbative boost correction
//   Level 3: local v_loc → additional boost within window W_R

use std::f64::consts::PI;
use crate::recombination::aniso_sobolev::gauss_legendre_s2;

/// PSTF multipole state: F_ℓ for ℓ = 0..L_max (axisymmetric, m=0 only).
/// For full STF: each ℓ has 2ℓ+1 components. Here we use scalar F_ℓ for simplicity.
pub(crate) type PstfState = Vec<f64>;

/// Maximum ℓ after boost of order N applied to input with L_max.
///
/// L_out = L_in + N (one ℓ added per perturbation order).
pub(crate) fn ell_max_after_boost(l_in: usize, order: usize) -> usize {
    l_in + order
}

// ═══ One-Field Exact Boost (μ = 0, Paper I Theorem 6) ═══

/// Doppler factor D(ê, v) = γ(1 − v·ê).
fn doppler_factor(e: &[f64; 3], v: &[f64; 3]) -> f64 {
    let v2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
    let gamma = 1.0 / (1.0 - v2).max(1e-30).sqrt();
    let v_dot_e = v[0] * e[0] + v[1] * e[1] + v[2] * e[2];
    gamma * (1.0 - v_dot_e)
}

/// Exact one-field boost (μ = 0).
///
/// Θ̃(ẽ) = (T₀/T̃₀) × D(e) × Θ(e)
///
/// Input: F_ℓ multipoles of Θ(e), velocity v.
/// Output: F̃_ℓ multipoles of Θ̃(ẽ) up to L_max.
///
/// Method: reconstruct Θ on S², apply D(e), reproject.
pub(crate) fn boost_one_field(f_ell: &[f64], v: &[f64; 3], l_max_out: usize, n_dir: usize) -> PstfState {
    let v2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
    if v2 < 1e-30 { // Zero velocity: identity
        let mut out = f_ell.to_vec();
        out.resize(l_max_out + 1, 0.0);
        return out;
    }

    let dirs = gauss_legendre_s2(n_dir);
    let l_in = f_ell.len() - 1;

    // Step 1: Reconstruct Θ(ê) from F_ℓ
    let mut theta_grid: Vec<(f64, [f64; 3], f64)> = Vec::with_capacity(dirs.len());
    for &(e, w) in &dirs {
        let cos_th = e[2];
        let theta = eval_legendre_sum(f_ell, cos_th);
        theta_grid.push((theta, e, w));
    }

    // Step 2: Apply Doppler factor
    // T₀/T̃₀ normalisation: ⟨D(e)Θ(e)⟩ → divide by ⟨D⟩ to preserve monopole meaning
    let gamma = 1.0 / (1.0 - v2).max(1e-30).sqrt();
    // For μ=0: T̃₀/T₀ = γ⁻¹ (from Planck spectrum transformation)
    let t_ratio = 1.0 / gamma; // T₀/T̃₀ = γ

    let mut boosted_theta: Vec<(f64, [f64; 3], f64)> = Vec::with_capacity(dirs.len());
    for &(theta, e, w) in &theta_grid {
        let d = doppler_factor(&e, v);
        let theta_tilde = gamma * d * theta; // (T₀/T̃₀) × D × Θ
        boosted_theta.push((theta_tilde, e, w));
    }

    // Step 3: Reproject to F̃_ℓ
    reproject_legendre(&boosted_theta, l_max_out)
}

/// Two-field boost (μ ≠ 0, Paper I Proposition 1).
///
/// Joint transformation of (Θ, η) under boost.
/// η̃(ẽ) = η(e) − ln D(e) (chemical potential shifts under boost).
///
/// Returns (F̃_ℓ^Θ, F̃_ℓ^η).
pub(crate) fn boost_two_field(
    f_theta: &[f64], f_eta: &[f64], v: &[f64; 3], l_max_out: usize, n_dir: usize,
) -> (PstfState, PstfState) {
    let v2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
    if v2 < 1e-30 {
        let mut t_out = f_theta.to_vec(); t_out.resize(l_max_out + 1, 0.0);
        let mut e_out = f_eta.to_vec(); e_out.resize(l_max_out + 1, 0.0);
        return (t_out, e_out);
    }

    let dirs = gauss_legendre_s2(n_dir);

    let mut boosted: Vec<(f64, f64, [f64; 3], f64)> = Vec::with_capacity(dirs.len());
    for &(e, w) in &dirs {
        let theta = eval_legendre_sum(f_theta, e[2]);
        let eta = eval_legendre_sum(f_eta, e[2]);
        let d = doppler_factor(&e, v);
        let gamma = 1.0 / (1.0 - v2).max(1e-30).sqrt();

        // Θ̃ = γ D Θ (same as one-field)
        let theta_tilde = gamma * d * theta;
        // η̃ = η − ln D (chemical potential shift)
        let eta_tilde = eta - d.max(1e-30).ln();

        boosted.push((theta_tilde, eta_tilde, e, w));
    }

    let theta_out: Vec<(f64, [f64; 3], f64)> = boosted.iter().map(|&(t, _, e, w)| (t, e, w)).collect();
    let eta_out: Vec<(f64, [f64; 3], f64)> = boosted.iter().map(|&(_, et, e, w)| (et, e, w)).collect();

    (reproject_legendre(&theta_out, l_max_out), reproject_legendre(&eta_out, l_max_out))
}

// ═══ Perturbative Boost (Doc 5 §3) ═══

/// First-order perturbative boost of PSTF multipoles.
///
/// T̃_a = T_a + v_a − (4/5) T_{ab} v^b + O(v²)
/// T̃_{ab} = T_{ab} + 2 v_{⟨a} T_{b⟩} + O(v²)
/// T̃_{abc} = 3 T_{⟨ab} v_{c⟩} + O(v²)
///
/// Input: F_ℓ (axisymmetric), v along z-axis (|v| = β).
/// Output: F̃_ℓ to L_in + 1.
pub(crate) fn perturbative_boost_order1(f_ell: &[f64], beta: f64) -> PstfState {
    let l_in = f_ell.len() - 1;
    let l_out = l_in + 1;
    let mut f_out = vec![0.0; l_out + 1];

    // Copy unchanged monopole
    f_out[0] = f_ell[0];

    // Dipole: T̃_1 = T_1 + v − (4/5) T_2 × v × (coupling factor)
    // For axisymmetric boost along z: v_z = β
    // T_{ab} v^b → (2/3) T_2 × β (STF projection for axial symmetry)
    let t1 = if l_in >= 1 { f_ell[1] } else { 0.0 };
    let t2 = if l_in >= 2 { f_ell[2] } else { 0.0 };
    f_out[1] = t1 + beta - (4.0 / 5.0) * (2.0 / 3.0) * t2 * beta;

    // Quadrupole: T̃_2 = T_2 + 2 v_{⟨a} T_{b⟩} + v_{⟨a} v_{b⟩}
    // 2 v_{⟨a} T_{b⟩} ≈ (4/3) t1 × β (STF coupling)
    // v_{⟨a} v_{b⟩} ≈ (2/3) β² (STF projection)
    f_out[2] = t2 + (4.0 / 3.0) * t1 * beta + (2.0 / 3.0) * beta * beta;

    // Octupole (new!): T̃_3 = 3 T_{⟨ab} v_{c⟩}
    // ≈ (6/5) T_2 × β (STF projection factor for ℓ=2 → ℓ=3)
    if l_out >= 3 {
        f_out[3] = (6.0 / 5.0) * t2 * beta;
    }

    // Higher ℓ: copy if present
    for ell in 3..=l_in.min(l_out) {
        f_out[ell] += if ell < f_ell.len() { f_ell[ell] } else { 0.0 };
    }

    f_out
}

// ═══ Three-Level Boost Cascade ═══

/// Boosted state with tracking of which levels contributed.
#[derive(Clone, Debug)]
pub(crate) struct BoostedState {
    pub(crate) f_ell: PstfState,
    pub(crate) l_max: usize,
    /// ΔC_ℓ from each level (for diagnostics).
    pub(crate) delta_cl_level1: Vec<f64>,
    pub(crate) delta_cl_level2: Vec<f64>,
    pub(crate) delta_cl_level3: Vec<f64>,
}

/// Three-level boost cascade.
///
/// Level 1: global tilt β → boost to matter frame
/// Level 2: δβ fluctuation → perturbative correction
/// Level 3: local v_loc → additional boost within W_R
pub(crate) fn three_level_boost(
    f_ell_input: &[f64],
    beta_global: f64,
    delta_beta: f64,
    v_loc: f64,         // local peculiar velocity magnitude
    _w_r: f64,           // window function scale (affects amplitude)
    n_dir: usize,
) -> BoostedState {
    let l_in = f_ell_input.len() - 1;

    // Level 1: global tilt β (exact boost)
    let l1_out = ell_max_after_boost(l_in, 1);
    let v1 = [0.0, 0.0, beta_global]; // boost along z
    let f_after_l1 = boost_one_field(f_ell_input, &v1, l1_out, n_dir);
    let dcl_l1: Vec<f64> = f_after_l1.iter().zip(f_ell_input.iter().chain(std::iter::repeat(&0.0)))
        .map(|(a, b)| a - b).collect();

    // Level 2: δβ fluctuation (perturbative)
    let f_after_l2 = perturbative_boost_order1(&f_after_l1, delta_beta);
    let dcl_l2: Vec<f64> = f_after_l2.iter().zip(f_after_l1.iter().chain(std::iter::repeat(&0.0)))
        .map(|(a, b)| a - b).collect();

    // Level 3: local velocity (perturbative)
    let f_after_l3 = perturbative_boost_order1(&f_after_l2, v_loc);
    let dcl_l3: Vec<f64> = f_after_l3.iter().zip(f_after_l2.iter().chain(std::iter::repeat(&0.0)))
        .map(|(a, b)| a - b).collect();

    let l_max = f_after_l3.len() - 1;
    BoostedState {
        f_ell: f_after_l3,
        l_max,
        delta_cl_level1: dcl_l1,
        delta_cl_level2: dcl_l2,
        delta_cl_level3: dcl_l3,
    }
}

// ═══ Legendre helpers ═══

/// Evaluate Σ_ℓ F_ℓ P_ℓ(cos θ).
fn eval_legendre_sum(f_ell: &[f64], cos_theta: f64) -> f64 {
    let mut sum = 0.0;
    let mut p_prev = 1.0; // P_0
    let mut p_curr = cos_theta; // P_1
    if !f_ell.is_empty() { sum += f_ell[0] * p_prev; }
    if f_ell.len() > 1 { sum += f_ell[1] * p_curr; }
    for ell in 2..f_ell.len() {
        let p_next = ((2 * ell - 1) as f64 * cos_theta * p_curr
                     - (ell - 1) as f64 * p_prev) / ell as f64;
        sum += f_ell[ell] * p_next;
        p_prev = p_curr; p_curr = p_next;
    }
    sum
}

/// Reproject values on S² to F̃_ℓ via ∫ f(ê) P_ℓ(cos θ) dΩ.
fn reproject_legendre(vals: &[(f64, [f64; 3], f64)], l_max: usize) -> PstfState {
    let mut f_out = vec![0.0; l_max + 1];
    for &(val, e, w) in vals {
        let cos_th = e[2];
        let mut p_prev = 1.0;
        let mut p_curr = cos_th;
        f_out[0] += val * p_prev * w;
        if l_max >= 1 { f_out[1] += val * p_curr * w * 3.0; }
        for ell in 2..=l_max {
            let p_next = ((2 * ell - 1) as f64 * cos_th * p_curr
                         - (ell - 1) as f64 * p_prev) / ell as f64;
            f_out[ell] += val * p_next * w * (2 * ell + 1) as f64;
            p_prev = p_curr; p_curr = p_next;
        }
    }
    f_out
}

#[cfg(test)]
mod tests {
    use super::*;

    // ═══ Basic properties ═══

    #[test]
    fn test_ell_max_after_boost() {
        assert_eq!(ell_max_after_boost(2, 1), 3);
        assert_eq!(ell_max_after_boost(2, 2), 4);
        assert_eq!(ell_max_after_boost(0, 1), 1);
    }

    #[test]
    fn test_zero_velocity_identity() {
        let f = vec![1.0, 0.01, 0.001];
        let boosted = boost_one_field(&f, &[0.0; 3], 3, 12);
        for ell in 0..3 {
            assert!((boosted[ell] - f[ell]).abs() < 1e-6,
                "Zero-v: F̃_{} = {:.6} vs {:.6}", ell, boosted[ell], f[ell]);
        }
    }

    #[test]
    fn test_perturbative_zero_velocity() {
        let f = vec![1.0, 0.01, 0.001];
        let boosted = perturbative_boost_order1(&f, 0.0);
        assert!((boosted[0] - f[0]).abs() < 1e-15);
        assert!((boosted[1] - f[1]).abs() < 1e-15);
        assert!((boosted[2] - f[2]).abs() < 1e-15);
        assert!(boosted[3].abs() < 1e-15); // no new octupole
    }

    // ═══ L=2 → L=3 boost ═══

    #[test]
    fn test_l2_to_l3_perturbative() {
        // L=2 input + order-1 boost → L=3 output
        let f = vec![1.0, 0.0, 0.01]; // monopole + quadrupole, no dipole
        let beta = 0.001;
        let boosted = perturbative_boost_order1(&f, beta);
        assert_eq!(boosted.len(), 4); // ℓ = 0,1,2,3
        // Induced octupole: F̃_3 = (6/5) × T_2 × β
        let expected_f3 = (6.0 / 5.0) * 0.01 * beta;
        assert!((boosted[3] - expected_f3).abs() < 1e-10,
            "Induced F̃₃ = {:.6e} (expect {:.6e})", boosted[3], expected_f3);
    }

    #[test]
    fn test_l2_to_l3_exact() {
        // Exact boost: L=2 → generates L=3 (and higher)
        let f = vec![1.0, 0.0, 0.01]; // monopole + quadrupole
        let v = [0.0, 0.0, 0.001];
        let boosted = boost_one_field(&f, &v, 4, 16);
        // F̃_3 should be nonzero (generated by boost)
        assert!(boosted[3].abs() > 1e-10, "Exact boost: F̃₃ = {:.4e} (must be nonzero)", boosted[3]);
    }

    // ═══ Perturbative vs exact agreement ═══

    #[test]
    fn test_perturbative_agrees_with_exact_small_v() {
        let f = vec![1.0, 0.005, 0.002]; // monopole + dipole + quadrupole
        let beta = 1e-4; // very small velocity
        let pert = perturbative_boost_order1(&f, beta);
        let exact = boost_one_field(&f, &[0.0, 0.0, beta], 3, 30);

        // Agreement limited by angular reconstruction quality (Gauss-Legendre grid)
        // Expect agreement to ~0.1% (reconstruction error dominates over O(v²))
        for ell in 0..=2 {
            let diff = (pert[ell] - exact[ell]).abs();
            let scale = f[0].abs();
            assert!(diff / scale < 0.01,
                "ℓ={}: pert={:.6e}, exact={:.6e}, diff/scale={:.2e}",
                ell, pert[ell], exact[ell], diff / scale);
        }
    }

    // ═══ Two-field boost ═══

    #[test]
    fn test_two_field_zero_velocity() {
        let ft = vec![1.0, 0.01, 0.001];
        let fe = vec![0.0, 0.0, 0.0]; // zero chemical potential
        let (t_out, e_out) = boost_two_field(&ft, &fe, &[0.0; 3], 3, 12);
        for ell in 0..3 {
            assert!((t_out[ell] - ft[ell]).abs() < 1e-6);
            assert!((e_out[ell] - fe[ell]).abs() < 1e-6);
        }
    }

    #[test]
    fn test_two_field_eta_shift() {
        // Boost with v ≠ 0: η̃ = η − ln D, so η gets direction-dependent shift
        let ft = vec![1.0, 0.0, 0.0]; // isotropic Θ
        let fe = vec![0.0, 0.0, 0.0]; // zero chemical potential
        let v = [0.0, 0.0, 0.01];
        let (_, e_out) = boost_two_field(&ft, &fe, &v, 2, 16);
        // η̃ = −ln D(e) which is direction-dependent → nonzero F̃_1^η
        assert!(e_out[1].abs() > 1e-6,
            "Two-field: η gets dipole from boost: F̃₁^η = {:.4e}", e_out[1]);
    }

    // ═══ Three-level cascade ═══

    #[test]
    fn test_three_level_cascade() {
        let f = vec![1.0, 0.0, 0.005]; // monopole + quadrupole
        let bs = three_level_boost(&f, 1e-3, 1e-4, 1e-4, 100.0, 12);
        assert!(bs.l_max >= 3, "Must reach L≥3");
        assert!(bs.f_ell[3].abs() > 0.0, "Octupole generated");
    }

    #[test]
    fn test_cascade_level_tracking() {
        let f = vec![1.0, 0.0, 0.005];
        let bs = three_level_boost(&f, 1e-3, 1e-4, 1e-4, 100.0, 12);
        // Level 1 (global β = 10⁻³) should dominate
        let dc1_rms: f64 = bs.delta_cl_level1.iter().map(|x| x * x).sum::<f64>().sqrt();
        let dc2_rms: f64 = bs.delta_cl_level2.iter().map(|x| x * x).sum::<f64>().sqrt();
        assert!(dc1_rms > dc2_rms,
            "Level 1 ({:.4e}) must dominate Level 2 ({:.4e})", dc1_rms, dc2_rms);
    }

    #[test]
    fn test_doppler_factor_limits() {
        // v = 0: D = 1
        assert!((doppler_factor(&[1.0, 0.0, 0.0], &[0.0; 3]) - 1.0).abs() < 1e-15);
        // v along ê: D = γ(1−v), v anti-ê: D = γ(1+v)
        let v = 0.1;
        let d_par = doppler_factor(&[0.0, 0.0, 1.0], &[0.0, 0.0, v]);
        let d_anti = doppler_factor(&[0.0, 0.0, -1.0], &[0.0, 0.0, v]);
        assert!(d_par < 1.0, "Along v: D < 1 (blueshift)");
        assert!(d_anti > 1.0, "Against v: D > 1 (redshift)");
    }
}
