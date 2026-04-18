// BG-04: Induced Tail at High Perturbation Order.
//
// Paper I Theorem 2: Teff truncation at ℓ ≤ L, applied at N-th perturbation
// order, generates angular support ℓ ≤ NL.
//
// Paper I Proposition 2: F(Θ) = Σ_{n=0}^N a_n ϑ^n has support ℓ ≤ NL
// when Θ = 1 + ϑ with ϑ having support ℓ ≤ L.
//
// Physical importance: L=2 (quadrupole seed) + N=2 (second order)
// → ℓ=4 contribution that PSTF at ℓ_max=2 completely misses.
//
// Mechanism: P_ℓ(cos θ) × P_{ℓ'}(cos θ) couples to P_{ℓ+ℓ'} via
// Clebsch-Gordan / Gaunt integrals. Θ² with ℓ_max=2 → P_2² → P_4.

use std::f64::consts::PI;
use crate::recombination::aniso_sobolev::gauss_legendre_s2;

/// Maximum ℓ from induced tail: ℓ_max = N × L.
pub(crate) fn induced_tail_ell_max(l_teff: usize, perturbation_order: usize) -> usize {
    perturbation_order * l_teff
}

/// Compute induced tail F_ℓ for ℓ > L from N-th order Teff operation.
///
/// For Θ(ê) = Σ_{ℓ=0}^L F_ℓ P_ℓ(cos θ):
///   Θ^N(ê) has support ℓ ≤ NL.
///   The "tail" is F_ℓ for L < ℓ ≤ NL.
///
/// Method: reconstruct Θ on S², compute Θ^N, reproject.
pub(crate) fn compute_tail_correction(
    f_ell: &[f64],       // F_ℓ for ℓ = 0..L
    l_teff: usize,        // L (Teff truncation)
    n_order: usize,       // N (perturbation order)
    n_dir: usize,
) -> Vec<f64> {
    let l_out = induced_tail_ell_max(l_teff, n_order);
    let dirs = gauss_legendre_s2(n_dir);

    // Reconstruct Θ(ê) and compute Θ^N(ê)
    let mut vals: Vec<(f64, [f64; 3], f64)> = Vec::with_capacity(dirs.len());
    for &(e, w) in &dirs {
        let theta = eval_legendre_sum(f_ell, e[2]);
        let theta_n = theta.powi(n_order as i32);
        vals.push((theta_n, e, w));
    }

    // Reproject Θ^N to F_ℓ up to NL
    let f_full = reproject_legendre(&vals, l_out);

    // Return only the TAIL (ℓ > L)
    let mut tail = vec![0.0; l_out + 1];
    for ell in (l_teff + 1)..=l_out {
        if ell < f_full.len() { tail[ell] = f_full[ell]; }
    }
    tail
}

/// Compare PSTF (truncated at ℓ_max) vs Teff (with induced tail).
#[derive(Clone, Debug)]
pub(crate) struct TailComparisonResult {
    /// L_teff: Teff truncation level.
    pub(crate) l_teff: usize,
    /// N: perturbation order.
    pub(crate) n_order: usize,
    /// ℓ_max of induced tail.
    pub(crate) l_tail_max: usize,
    /// Tail F_ℓ for ℓ > L.
    pub(crate) tail_f_ell: Vec<f64>,
    /// |tail| / |seed|: relative magnitude.
    pub(crate) relative_magnitude: f64,
    /// PSTF at ℓ_max = L misses this fraction of angular power.
    pub(crate) missed_power_fraction: f64,
}

/// Full comparison: what PSTF at ℓ_max = L misses vs Teff at order N.
pub(crate) fn compare_pstf_vs_teff(
    f_ell: &[f64],
    l_pstf: usize,
    l_teff: usize,
    n_order: usize,
    n_dir: usize,
) -> TailComparisonResult {
    let l_tail_max = induced_tail_ell_max(l_teff, n_order);
    let tail = compute_tail_correction(f_ell, l_teff, n_order, n_dir);

    // Seed power: Σ (2ℓ+1) F_ℓ²
    let seed_power: f64 = f_ell.iter().enumerate()
        .map(|(ell, &f)| (2 * ell + 1) as f64 * f * f).sum();

    // Tail power: Σ_{ℓ > L} (2ℓ+1) F_ℓ²
    let tail_power: f64 = tail.iter().enumerate()
        .filter(|&(ell, _)| ell > l_pstf)
        .map(|(ell, &f)| (2 * ell + 1) as f64 * f * f).sum();

    // Full Θ^N power
    let full_tail = compute_tail_correction(f_ell, l_teff, n_order, n_dir);
    let full_power: f64 = {
        let dirs = gauss_legendre_s2(n_dir);
        let mut sum = 0.0;
        let mut wsum = 0.0;
        for &(e, w) in &dirs {
            let theta = eval_legendre_sum(f_ell, e[2]);
            let theta_n = theta.powi(n_order as i32);
            sum += theta_n * theta_n * w;
            wsum += w;
        }
        sum / wsum
    };

    let relative_magnitude = if seed_power > 1e-30 {
        tail_power.sqrt() / seed_power.sqrt()
    } else { 0.0 };

    let missed_power_fraction = if full_power > 1e-30 {
        tail_power / full_power
    } else { 0.0 };

    TailComparisonResult {
        l_teff, n_order, l_tail_max,
        tail_f_ell: tail,
        relative_magnitude,
        missed_power_fraction,
    }
}

/// Parity analysis: which ℓ are generated from even/odd seeds.
///
/// Even seed (ℓ = 0, 2, 4, ...): Θ^N has only even ℓ.
/// Odd seed (ℓ = 1, 3, 5, ...): Θ^N has ℓ of same parity as N.
/// Mixed: all ℓ up to NL possible.
pub(crate) fn parity_selection(l_seed_parity: &str, n_order: usize) -> Vec<bool> {
    // Returns which ℓ are nonzero (true) for ℓ = 0..NL
    // For "even" seed: only even ℓ
    // For "odd" seed: parity of N determines result
    // For "mixed": all ℓ
    match l_seed_parity {
        "even" => {
            // Even seed (ℓ=0,2): Θ^N only has even ℓ regardless of N
            // P_2^2 = (1/5)(2P_0 + 4P_2 + (18/7)P_4) — all even
            vec![true] // placeholder: even ℓ only
        }
        _ => vec![true],
    }
}

// ═══ Legendre helpers (shared with boost.rs) ═══

fn eval_legendre_sum(f_ell: &[f64], cos_theta: f64) -> f64 {
    let mut sum = 0.0;
    let mut p_prev = 1.0;
    let mut p_curr = cos_theta;
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

fn reproject_legendre(vals: &[(f64, [f64; 3], f64)], l_max: usize) -> Vec<f64> {
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

    // ═══ Selection rule tests ═══

    #[test]
    fn test_ell_max_formula() {
        assert_eq!(induced_tail_ell_max(2, 1), 2);
        assert_eq!(induced_tail_ell_max(2, 2), 4);
        assert_eq!(induced_tail_ell_max(2, 3), 6);
        assert_eq!(induced_tail_ell_max(3, 2), 6);
    }

    // ═══ L=2, N=2: nonzero F₄ ═══

    #[test]
    fn test_l2_n2_generates_f4() {
        // Θ = 1 + ε P₂(cos θ): Θ² has ℓ=4 from P₂²
        let eps = 0.01;
        let f = vec![1.0, 0.0, eps]; // F_0=1, F_1=0, F_2=ε
        let tail = compute_tail_correction(&f, 2, 2, 20);
        // F_4 should be nonzero (from P_2² → P_4 coupling)
        assert!(tail[4].abs() > 1e-10,
            "L=2,N=2: F₄ = {:.4e} (must be nonzero)", tail[4]);
        // Magnitude: F_4 ~ ε² × (Gaunt coefficient) ~ ε² × 18/(7×5) ~ 0.51 ε²
        eprintln!("Induced F₄ = {:.6e}, ε² = {:.6e}, ratio = {:.4}",
            tail[4], eps*eps, tail[4]/(eps*eps));
    }

    // ═══ L=2, N=1: F₃ = 0 (parity) ═══

    #[test]
    fn test_l2_n1_f3_zero() {
        // At N=1: Θ¹ = Θ, no new ℓ generated beyond input L=2
        let f = vec![1.0, 0.0, 0.01];
        let tail = compute_tail_correction(&f, 2, 1, 16);
        // F_3 should be zero (odd parity from even seed at N=1)
        assert!(tail.len() <= 3 || tail[3].abs() < 1e-8,
            "L=2,N=1: F₃ = {:.4e} (must be ~0)", if tail.len() > 3 { tail[3] } else { 0.0 });
    }

    #[test]
    fn test_even_seed_no_odd_ell() {
        // Even seed (ℓ=0,2): Θ^2 should only have even ℓ (0,2,4)
        let f = vec![1.0, 0.0, 0.01]; // F_0, F_1=0, F_2
        let tail = compute_tail_correction(&f, 2, 2, 20);
        // F_1 and F_3 should be zero (odd parity)
        if tail.len() > 1 { assert!(tail[1].abs() < 1e-8, "F₁ = {:.4e}", tail[1]); }
        if tail.len() > 3 { assert!(tail[3].abs() < 1e-8, "F₃ = {:.4e}", tail[3]); }
    }

    // ═══ Scaling: |tail| ∝ |ϑ|^N ═══

    #[test]
    fn test_tail_scaling_with_amplitude() {
        let f1 = vec![1.0, 0.0, 0.001]; // ε = 10⁻³
        let f2 = vec![1.0, 0.0, 0.002]; // ε = 2×10⁻³
        let tail1 = compute_tail_correction(&f1, 2, 2, 20);
        let tail2 = compute_tail_correction(&f2, 2, 2, 20);
        // At N=2: F₄ ∝ ε² → ratio should be 4
        if tail1[4].abs() > 1e-15 {
            let ratio = tail2[4] / tail1[4];
            assert!((ratio - 4.0).abs() < 0.5,
                "ε² scaling: F₄ ratio = {:.2} (expect 4)", ratio);
        }
    }

    // ═══ PSTF vs Teff comparison ═══

    #[test]
    fn test_pstf_misses_tail() {
        let f = vec![1.0, 0.0, 0.01]; // ε = 10⁻²
        let comp = compare_pstf_vs_teff(&f, 2, 2, 2, 20);
        assert_eq!(comp.l_tail_max, 4);
        assert!(comp.tail_f_ell[4].abs() > 1e-10, "F₄ from tail");
        // PSTF at ℓ_max=2 misses this entirely
        eprintln!("Missed power fraction: {:.4e}", comp.missed_power_fraction);
        eprintln!("Relative magnitude: {:.4e}", comp.relative_magnitude);
    }

    #[test]
    fn test_pstf_at_l4_includes_tail() {
        // PSTF at ℓ_max=4 should capture what Teff at L=2, N=2 generates
        let f = vec![1.0, 0.0, 0.01, 0.0, 0.0]; // ℓ_max=4
        let comp = compare_pstf_vs_teff(&f, 4, 2, 2, 20);
        // With ℓ_max=4 in PSTF, the missed power should be 0 (within Teff's NL=4)
        assert!(comp.missed_power_fraction < 0.01,
            "PSTF at ℓ=4 should capture tail: missed = {:.4e}", comp.missed_power_fraction);
    }

    // ═══ Physical importance ═══

    #[test]
    fn test_recombination_era_magnitude() {
        // At recombination: |ϑ| ~ 10⁻³ (CMB temperature fluctuation)
        // Induced F₄ ~ ε² ~ 10⁻⁶ — small but nonzero
        let eps = 1e-3;
        let f = vec![1.0, 0.0, eps];
        let tail = compute_tail_correction(&f, 2, 2, 20);
        let f4 = tail[4].abs();
        // F₄ ~ ε² × coefficient ~ 10⁻⁶ × O(0.1-1)
        assert!(f4 < 1e-4, "F₄ must be small: {:.4e}", f4);
        assert!(f4 > 1e-10, "F₄ must be nonzero: {:.4e}", f4);
        eprintln!("Recombination: F₄ = {:.4e} from ε = {:.4e}", f4, eps);
    }

    #[test]
    fn test_higher_order_n3() {
        // N=3: Θ³ with L=2 → ℓ_max = 6
        let f = vec![1.0, 0.0, 0.01];
        let tail = compute_tail_correction(&f, 2, 3, 20);
        assert_eq!(induced_tail_ell_max(2, 3), 6);
        // F_6 should be nonzero (from P₂³ → P₆ coupling)
        if tail.len() > 6 {
            assert!(tail[6].abs() > 1e-15,
                "L=2,N=3: F₆ = {:.4e}", tail[6]);
        }
    }
}
