// BG-02: Positivity Enforcement for Teff Closure.
//
// Paper V Proposition 1: Θ(ê) > 0 guarantees f > 0 everywhere.
// When PSTF truncation drives f < 0, reconstruct Θ from F_ℓ,
// enforce Θ > Θ_floor, recompute corrected moments.
//
// Algorithm:
//   1. Reconstruct Θ(ê) = Σ_ℓ F_ℓ P_ℓ(cos θ) on angular grid
//   2. Identify violations: Θ(ê) < Θ_floor
//   3. Enforce: Θ_corr(ê) = max(Θ(ê), Θ_floor)
//   4. Reproject: F_ℓ^{corr} = ∫ Θ_corr(ê) P_ℓ(cos θ) dΩ

use std::f64::consts::PI;
use crate::recombination::aniso_sobolev::gauss_legendre_s2;

/// Default positivity floor: Θ > 0 (physical: temperature must be positive).
pub(crate) const THETA_FLOOR: f64 = 1e-10;

/// Result of positivity enforcement.
#[derive(Clone, Debug)]
pub(crate) struct PositivityResult {
    /// Number of angular directions that violated positivity.
    pub(crate) n_violations: usize,
    /// Maximum violation depth: min(Θ) before enforcement.
    pub(crate) min_theta_before: f64,
    /// Corrected F_ℓ multipoles.
    pub(crate) f_ell_corrected: Vec<f64>,
    /// Energy conservation check: |ΔF_0/F_0|.
    pub(crate) energy_conservation_error: f64,
}

/// Reconstruct Θ(ê) on angular grid from PSTF multipoles F_ℓ.
///
/// Θ(ê) = Σ_{ℓ=0}^{L_max} (2ℓ+1)/(4π) F_ℓ P_ℓ(cos θ)
///
/// For axially symmetric case (only m=0 modes): F_ℓ are scalar.
/// Returns (directions, theta_values, weights).
pub(crate) fn reconstruct_theta(
    f_ell: &[f64],
    n_dir: usize,
) -> (Vec<[f64; 3]>, Vec<f64>, Vec<f64>) {
    let dirs = gauss_legendre_s2(n_dir);
    let l_max = f_ell.len() - 1;
    let mut theta_vals = Vec::with_capacity(dirs.len());
    let mut directions = Vec::with_capacity(dirs.len());
    let mut weights = Vec::with_capacity(dirs.len());

    for &(e, w) in &dirs {
        let cos_theta = e[2]; // z-component = cos θ
        let mut theta = 0.0;
        // Evaluate Σ F_ℓ P_ℓ(cos θ) (no (2ℓ+1)/4π factor — F_ℓ already normalised)
        let mut p_prev = 1.0; // P_0
        let mut p_curr = cos_theta; // P_1
        theta += f_ell[0] * p_prev;
        if l_max >= 1 { theta += f_ell[1] * p_curr; }
        for ell in 2..=l_max {
            let p_next = ((2 * ell - 1) as f64 * cos_theta * p_curr
                         - (ell - 1) as f64 * p_prev) / ell as f64;
            theta += f_ell[ell] * p_next;
            p_prev = p_curr;
            p_curr = p_next;
        }
        theta_vals.push(theta);
        directions.push(e);
        weights.push(w);
    }

    (directions, theta_vals, weights)
}

/// Enforce positivity: Θ_corr(ê) = max(Θ(ê), Θ_floor).
pub(crate) fn enforce_positivity(theta_vals: &[f64], floor: f64) -> (Vec<f64>, usize) {
    let mut corrected = Vec::with_capacity(theta_vals.len());
    let mut n_violations = 0;
    for &t in theta_vals {
        if t < floor {
            corrected.push(floor);
            n_violations += 1;
        } else {
            corrected.push(t);
        }
    }
    (corrected, n_violations)
}

/// Reproject corrected Θ(ê) back to PSTF multipoles F_ℓ.
///
/// F_ℓ^{corr} = (2ℓ+1) ∫ Θ_corr(ê) P_ℓ(cos θ) dΩ/(4π)
///            = (2ℓ+1) Σ_i Θ_corr(ê_i) P_ℓ(cos θ_i) w_i
pub(crate) fn reproject_to_pstf(
    theta_corrected: &[f64],
    directions: &[[f64; 3]],
    weights: &[f64],
    l_max: usize,
) -> Vec<f64> {
    let mut f_ell = vec![0.0; l_max + 1];

    for (i, (&t, &w)) in theta_corrected.iter().zip(weights.iter()).enumerate() {
        let cos_theta = directions[i][2];
        let mut p_prev = 1.0;
        let mut p_curr = cos_theta;

        f_ell[0] += t * p_prev * w;
        if l_max >= 1 { f_ell[1] += t * p_curr * w * 3.0; }

        for ell in 2..=l_max {
            let p_next = ((2 * ell - 1) as f64 * cos_theta * p_curr
                         - (ell - 1) as f64 * p_prev) / ell as f64;
            f_ell[ell] += t * p_next * w * (2 * ell + 1) as f64;
            p_prev = p_curr;
            p_curr = p_next;
        }
    }

    f_ell
}

/// Full positivity enforcement pipeline.
///
/// F_ℓ → Θ(ê) → enforce Θ > floor → F_ℓ^{corr}
pub(crate) fn enforce_and_reproject(
    f_ell: &[f64],
    n_dir: usize,
    floor: f64,
) -> PositivityResult {
    let l_max = f_ell.len() - 1;
    let (dirs, theta_vals, weights) = reconstruct_theta(f_ell, n_dir);

    let min_before = theta_vals.iter().cloned().fold(f64::INFINITY, f64::min);
    let (theta_corr, n_viol) = enforce_positivity(&theta_vals, floor);

    let f_corr = reproject_to_pstf(&theta_corr, &dirs, &weights, l_max);

    // Energy conservation: |ΔF_0/F_0|
    let energy_err = if f_ell[0].abs() > 1e-30 {
        (f_corr[0] - f_ell[0]).abs() / f_ell[0].abs()
    } else { 0.0 };

    PositivityResult {
        n_violations: n_viol,
        min_theta_before: min_before,
        f_ell_corrected: f_corr,
        energy_conservation_error: energy_err,
    }
}

/// Bisection rollback: halve dt until no positivity violations.
///
/// Returns the safe dt fraction (1.0 = full step, 0.5 = half step, etc.).
pub(crate) fn bisection_rollback(
    f_ell_start: &[f64],
    f_ell_end: &[f64],
    n_dir: usize,
    floor: f64,
    max_iterations: usize,
) -> f64 {
    let l_max = f_ell_start.len() - 1;
    let mut frac = 1.0;

    for _ in 0..max_iterations {
        // Interpolate: F_ℓ(frac) = (1−frac) F_start + frac F_end
        let f_interp: Vec<f64> = (0..=l_max).map(|ell| {
            (1.0 - frac) * f_ell_start[ell] + frac * f_ell_end[ell]
        }).collect();

        let (_, theta_vals, _) = reconstruct_theta(&f_interp, n_dir);
        let min_theta = theta_vals.iter().cloned().fold(f64::INFINITY, f64::min);

        if min_theta >= floor { return frac; }
        frac *= 0.5;
    }
    frac
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reconstruct_isotropic() {
        // F_0 = 1, F_{ℓ>0} = 0 → Θ(ê) = 1 everywhere
        let f = vec![1.0, 0.0, 0.0, 0.0];
        let (_, theta, _) = reconstruct_theta(&f, 8);
        for &t in &theta {
            assert!((t - 1.0).abs() < 1e-10, "Isotropic: Θ = {:.6}", t);
        }
    }

    #[test]
    fn test_reconstruct_dipole() {
        // F_0 = 1, F_1 = 0.01 → Θ(ê) = 1 + 0.01 cos θ
        let f = vec![1.0, 0.01, 0.0];
        let (dirs, theta, _) = reconstruct_theta(&f, 8);
        for (i, &t) in theta.iter().enumerate() {
            let expected = 1.0 + 0.01 * dirs[i][2];
            assert!((t - expected).abs() < 1e-8,
                "Dipole: Θ = {:.6}, expected {:.6}", t, expected);
        }
    }

    #[test]
    fn test_positivity_no_violation() {
        let vals = vec![1.0, 0.9, 1.1, 0.8];
        let (corr, n) = enforce_positivity(&vals, THETA_FLOOR);
        assert_eq!(n, 0);
        assert_eq!(corr, vals);
    }

    #[test]
    fn test_positivity_with_violation() {
        let vals = vec![1.0, -0.1, 0.5, -0.001];
        let (corr, n) = enforce_positivity(&vals, THETA_FLOOR);
        assert_eq!(n, 2);
        assert!(corr[1] >= THETA_FLOOR);
        assert!(corr[3] >= THETA_FLOOR);
    }

    #[test]
    fn test_roundtrip_isotropic() {
        let f_orig = vec![1.0, 0.0, 0.0];
        let (dirs, theta, weights) = reconstruct_theta(&f_orig, 12);
        let f_back = reproject_to_pstf(&theta, &dirs, &weights, 2);
        assert!((f_back[0] - 1.0).abs() < 1e-6, "F_0 roundtrip: {:.8}", f_back[0]);
        assert!(f_back[1].abs() < 1e-6, "F_1 roundtrip: {:.8}", f_back[1]);
    }

    #[test]
    fn test_enforce_reproject_no_violation() {
        let f = vec![1.0, 0.001, 0.0001, 0.0];
        let result = enforce_and_reproject(&f, 12, THETA_FLOOR);
        assert_eq!(result.n_violations, 0);
        assert!(result.energy_conservation_error < 1e-4,
            "Energy conservation: {:.2e}", result.energy_conservation_error);
    }

    #[test]
    fn test_enforce_reproject_with_violation() {
        // Large F_2 makes Θ negative at some angles
        let f = vec![0.1, 0.0, 0.5]; // F_2 > F_0 → violation
        let result = enforce_and_reproject(&f, 12, THETA_FLOOR);
        assert!(result.n_violations > 0, "Must detect violations");
        assert!(result.min_theta_before < THETA_FLOOR);
        // After single correction: F_ℓ^corr exists and F_0 is approximately conserved
        // (Perfect post-correction positivity requires iteration — Gibbs effect)
        assert!(result.f_ell_corrected[0] > 0.0, "F_0^corr > 0");
        // The correction increases F_0 (fills in negative regions)
        assert!(result.f_ell_corrected[0] >= f[0] - 0.01,
            "F_0^corr = {:.4} (original {:.4})", result.f_ell_corrected[0], f[0]);
    }

    #[test]
    fn test_bisection_rollback_safe() {
        let f_start = vec![1.0, 0.0, 0.0];
        let f_end = vec![1.0, 0.001, 0.0];
        let frac = bisection_rollback(&f_start, &f_end, 8, THETA_FLOOR, 10);
        assert!((frac - 1.0).abs() < 1e-10, "No violation: frac = 1.0");
    }

    #[test]
    fn test_bisection_rollback_unsafe() {
        let f_start = vec![1.0, 0.0, 0.0];
        let f_end = vec![0.01, 0.0, 0.5]; // violation at end
        let frac = bisection_rollback(&f_start, &f_end, 8, THETA_FLOOR, 20);
        assert!(frac < 1.0, "Must reduce step: frac = {:.4}", frac);
        assert!(frac > 0.0, "Must have some safe step");
    }

    #[test]
    fn test_flrw_bridge_zero() {
        // FLRW: F_0 = 1, all F_{ℓ>0} = 0 → no violations, no correction
        let f = vec![1.0, 0.0, 0.0, 0.0, 0.0];
        let result = enforce_and_reproject(&f, 12, THETA_FLOOR);
        assert_eq!(result.n_violations, 0);
        assert!((result.f_ell_corrected[0] - 1.0).abs() < 1e-4);
    }
}
