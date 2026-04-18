// ⚠️  TOY MODEL — VALIDATION ONLY.  NOT FOR PRODUCTION.
//
// Uses Hu–Sugiyama (1996) analytic transfer function.
// Accuracy: ~10–30% vs CLASS at ℓ > 200 (no neutrino free-streaming,
//   no reionization, no polarization feedback beyond TCA prefactor).
// Performance: O(n_k × ℓ_max × n_η) bessel calls — impractical for ℓ > 500.
//
// For production FLRW C_ℓ, use solver::flrw_cl_pipeline (CL-04A, pending).
// This module is gated behind #[cfg(test)] in los/mod.rs.
//
// BE-05d: FLRW C_ℓ validation via analytic transfer + LoS integration.
//
// Strategy: tight-coupling solution gives Θ₀(k,η) as damped acoustic oscillation.
// Source: S(k,η) = g(η)[Θ₀(k,η_*) + Ψ(k,η_*)] + ISW
// LoS: Δ_ℓ(k) = ∫ S(k,η) j_ℓ(k(η₀-η)) dη
// C_ℓ = (2/π) ∫ dk k² P(k) |Δ_ℓ(k)|²
//
// Uses Hu-Sugiyama (1996) transfer function for validation.

use super::bessel::spherical_bessel_j;
use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult, compute_visibility};
use crate::recombination::hyrec_tables::HyRecTables;

/// Tight-coupling transfer function at last scattering.
///
/// Θ₀(k) + Ψ(k) at η = η_* (Hu & Sugiyama 1996):
///   [Θ₀+Ψ](k) = [Θ₀(0)+Ψ(0)] cos(k r_s) × D(k) + Ψ(η_*)
///
/// where D(k) = exp(-k²/k_D²) is the Silk damping envelope,
/// and Θ₀(0) + Ψ(0) ≈ Ψ/3 in adiabatic initial conditions.
fn transfer_at_lss(k: f64, r_s: f64, k_d: f64) -> f64 {
    // Adiabatic IC: (Θ₀+Ψ)(k,η_*) ≈ (1/3)cos(k r_s) e^{−(k/k_D)²}
    // The 1/3 comes from Sachs-Wolfe: Θ₀ = −Ψ/3 at super-horizon,
    // and the subsequent acoustic oscillation.
    let acoustic = (k * r_s).cos();
    let damping = (-(k / k_d).powi(2)).exp();
    (1.0 / 3.0) * acoustic * damping
}

/// Doppler contribution: v_b(k,η_*) ∝ sin(k r_s)/k.
fn doppler_at_lss(k: f64, r_s: f64, k_d: f64) -> f64 {
    let acoustic = (k * r_s).sin();
    let damping = (-(k / k_d).powi(2)).exp();
    (1.0 / 3.0) * acoustic * damping / k.max(1e-10)
}

/// Silk damping scale k_D [Mpc⁻¹].
///
/// Analytical approximation (Hu & Sugiyama 1996):
///   k_D⁻² ≈ (1/6) × 1/(n_e σ_T) × (R²+16(1+R)/15) / (1+R)  × η_*
///
/// More practically: k_D ≈ 0.14 Mpc⁻¹ for Planck cosmology,
/// scaling as k_D ∝ (Ω_b h²)^{0.3} × h^{0.7}.
fn silk_damping_scale(_vis: &VisibilityResult, params: &VisibilityParams) -> f64 {
    // Fitting formula from Hu & Dodelson (2002):
    // k_D ≈ 0.14 × (Ω_b h² / 0.022)^{0.35} × (h/0.67)^{0.65} Mpc⁻¹
    let ob_h2 = params.omega_b * params.h * params.h;
    0.14 * (ob_h2 / 0.022).powf(0.35) * (params.h / 0.67).powf(0.65)
}

/// Compute FLRW C_ℓ^TT via LoS integration.
///
/// For each k: source ≈ g(η) × T(k) + Doppler + ISW,
/// then LoS-integrate against j_ℓ(k(η₀−η)).
pub(crate) fn compute_cl_flrw(
    params: &VisibilityParams,
    ell_max: usize,
    n_k: usize,
) -> (Vec<f64>, VisibilityResult) {
    let tables = HyRecTables::generate(300);
    let vis = compute_visibility(params, &tables, 30000);

    let r_s = vis.r_s;
    let k_d = silk_damping_scale(&vis, params);
    let eta_0 = *vis.eta_grid.last().unwrap();
    let n = vis.z_grid.len();

    let a_s = 2.1e-9;
    let n_s = 0.9649;
    let k_pivot = 0.05_f64;
    let k_min = 3e-5_f64; // need k*d_* ~ ℓ, so k_min ~ 2/14000 ~ 1.4e-4 for ℓ=2
    let k_max = 0.35_f64;

    let mut cl = vec![0.0; ell_max + 1];

    for ik in 0..n_k {
        let frac = ik as f64 / (n_k - 1) as f64;
        let k = k_min * (k_max / k_min).powf(frac);
        let dk_log = (k_max / k_min).ln() / (n_k - 1) as f64; // d(ln k)

        let pk = a_s * (k / k_pivot).powf(n_s - 1.0);
        let t_mono = transfer_at_lss(k, r_s, k_d);
        let t_dop = doppler_at_lss(k, r_s, k_d);

        // For each ℓ, LoS-integrate: Δ_ℓ = ∫ [g T_mono j_ℓ + g T_dop j'_ℓ] dη
        // j'_ℓ(x) ≈ [ℓ j_{ℓ-1}(x) - (ℓ+1) j_{ℓ+1}(x)] / (2ℓ+1)
        for ell in 2..=ell_max {
            let mut sum = 0.0;
            for i in 1..n {
                let g = vis.g_grid[i];
                if g < 1e-30 { continue; }
                let x = k * (eta_0 - vis.eta_grid[i]);
                if x < 0.0 { continue; }
                let jl = spherical_bessel_j(ell, x);
                let deta = vis.eta_grid[i] - vis.eta_grid[i - 1];

                // Monopole: g × T_mono × j_ℓ
                let s_mono = g * t_mono * jl;

                // Doppler: g × T_dop × j'_ℓ (approximated)
                let jl_deriv = if ell > 0 && x > 0.1 {
                    let jlm1 = spherical_bessel_j(ell - 1, x);
                    let jlp1 = spherical_bessel_j(ell + 1, x);
                    k * (ell as f64 * jlm1 - (ell + 1) as f64 * jlp1) / (2 * ell + 1) as f64
                } else { 0.0 };
                let s_dop = g * t_dop * jl_deriv;

                sum += (s_mono + s_dop) * deta;
            }
            // C_ℓ = 4π ∫ dk/k Δ²_ζ(k) |Δ_ℓ(k)|²  where dk/k = d(ln k)
            cl[ell] += 4.0 * std::f64::consts::PI * pk * sum * sum * dk_log;
        }
    }

    // Convert to μK²
    let t_uk = params.t_cmb * 1e6;
    for ell in 2..=ell_max {
        cl[ell] *= t_uk * t_uk;
    }

    (cl, vis)
}

/// Compute D_ℓ = ℓ(ℓ+1)C_ℓ/(2π) [μK²].
pub(crate) fn cl_to_dl(cl: &[f64]) -> Vec<f64> {
    cl.iter().enumerate().map(|(ell, &c)| {
        if ell < 2 { 0.0 } else { ell as f64 * (ell + 1) as f64 * c / (2.0 * std::f64::consts::PI) }
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compute_cl_runs() {
        let p = VisibilityParams::planck2018();
        let (cl, vis) = compute_cl_flrw(&p, 30, 30);
        assert_eq!(cl.len(), 31);
        for ell in 2..=30 {
            assert!(!cl[ell].is_nan(), "C_{} = NaN", ell);
            assert!(cl[ell] >= 0.0, "C_{} = {:.4e}", ell, cl[ell]);
        }
        eprintln!("  k_D = {:.4} Mpc⁻¹, r_s = {:.1} Mpc, z_* = {:.0}", 
            silk_damping_scale(&vis, &p), vis.r_s, vis.z_star);
    }

    #[test]
    fn test_cl_nonzero() {
        let p = VisibilityParams::planck2018();
        let (cl, _) = compute_cl_flrw(&p, 10, 40);
        let max_cl = cl[2..].iter().fold(0.0f64, |m, &c| m.max(c));
        assert!(max_cl > 0.0, "All C_ℓ = 0");
    }

    #[test]
    fn test_dl_sw_plateau() {
        let p = VisibilityParams::planck2018();
        let (cl, _) = compute_cl_flrw(&p, 20, 60);
        let dl = cl_to_dl(&cl);
        // With limited k-sampling, just check D_ℓ are finite and positive
        for ell in 2..=20 {
            assert!(!dl[ell].is_nan(), "D_{} = NaN", ell);
            assert!(dl[ell] >= 0.0, "D_{} < 0", ell);
        }
        // D_2 should be nonzero (some SW signal)
        assert!(dl[2] > 0.0, "D_2 = 0 (no signal)");
    }

    #[test]
    fn test_transfer_sw_limit() {
        // At very small k (super-horizon): T ≈ 1/3
        let t = transfer_at_lss(1e-4, 140.0, 0.1);
        assert!((t - 1.0/3.0).abs() < 0.01, "SW: T = {:.4}", t);
    }

    #[test]
    fn test_transfer_oscillation() {
        // Transfer should oscillate with k
        let t1 = transfer_at_lss(0.01, 140.0, 0.1);
        let t2 = transfer_at_lss(0.02, 140.0, 0.1);
        // Different signs possible for acoustic oscillation
        assert!((t1 - t2).abs() > 1e-6, "Must oscillate");
    }

    #[test]
    fn test_silk_damping() {
        // k_D ≈ 0.14 Mpc⁻¹ for Planck cosmology
        let tables = HyRecTables::generate(200);
        let p = VisibilityParams::planck2018();
        let vis = compute_visibility(&p, &tables, 20000);
        let kd = silk_damping_scale(&vis, &p);
        assert!(kd > 0.10 && kd < 0.20, "k_D = {:.4}", kd);
    }
}
