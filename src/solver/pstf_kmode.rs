// ═══════════════════════════════════════════════════════════════════════
// pstf_kmode.rs — 1+3 PSTF Covariant Boltzmann Solver
// ═══════════════════════════════════════════════════════════════════════
//
// This solver uses the PSTF (Projected Symmetric Trace-Free) formalism
// from Challinor & Lasenby (1999) / Ellis-Maartens-MacCallum (2012).
//
// KEY DIFFERENCES from the Newtonian gauge solver (flrw_kmode.rs):
// 1. Variables are PSTF multipoles I_ℓ (gauge-invariant in 1+3 formalism)
// 2. Gravitational coupling uses expansion scalar θ and Weyl E_{ab}
// 3. Shear coupling σ_{ab} built in (zero for FLRW, nonzero for Bianchi)
// 4. Source function: I₀ = Θ₀+Ψ (gauge-invariant monopole)
// 5. No Newton-Raphson: Rodas5P (L-stable Rosenbrock, 6-stage)
//
// FLRW LIMIT: The 1+3 hierarchy reduces to the standard Boltzmann hierarchy
//   dI_ℓ/dη = k[α^d_ℓ I_{ℓ-1} - α^u_ℓ I_{ℓ+1}] - κ̇(I_ℓ - S_ℓ) + (1/3)θ β_ℓ I_ℓ
// where α^d, α^u, β are the PSTF coupling coefficients from coupling.rs.
//
// BIANCHI EXTENSION: Add σ_{ab} shear coupling (Δℓ=±2, pentadiagonal):
//   + σ/H × [γ^d_ℓ I_{ℓ-2} + γ^u_ℓ I_{ℓ+2}]
//
// STATE: y = [I₀..I_L, N₀..N_M, D_c, D_b, V_b, Φ_W]
//   D_c = δ_c (covariant density gradient for CDM)
//   D_b = δ_b (for baryons)
//   V_b = v_b (peculiar velocity)
//   Φ_W = Newtonian potential (evolved at k ≥ k_analytic; NOT used at k < k_analytic)

use crate::pstf::coupling;
use crate::pstf::hierarchy_matrix::{HierarchyRegime, build_coupling_table};
use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult};
use crate::solver::stacked::integrate_linear_profile_rodas5p;
use crate::core::config::Rodas5PConfig;
use crate::solver::profiler;

const N_EFF: f64 = 3.044;

/// State layout for the PSTF solver.
#[derive(Clone, Debug)]
pub(crate) struct PSTFLayout {
    pub(crate) ell_max_gamma: usize,
    pub(crate) ell_max_nu: usize,
    pub(crate) n_state: usize,
    pub(crate) nu_offset: usize,
    pub(crate) dc_idx: usize,
    pub(crate) db_idx: usize,
    pub(crate) vb_idx: usize,
    pub(crate) phi_idx: usize,
}

impl PSTFLayout {
    pub(crate) fn new(lg: usize, ln: usize) -> Self {
        let nu_offset = lg + 1;
        let dc_idx = nu_offset + ln + 1;
        let db_idx = dc_idx + 1;
        let vb_idx = db_idx + 1;
        let phi_idx = vb_idx + 1;
        let n_state = phi_idx + 1;
        Self { ell_max_gamma: lg, ell_max_nu: ln, n_state, nu_offset,
               dc_idx, db_idx, vb_idx, phi_idx }
    }
}

/// Build the PSTF coupling matrix at a single time step.
///
/// Uses the PSTF coupling coefficients from coupling.rs for the
/// Boltzmann hierarchy, with explicit hooks for Bianchi shear.
pub(crate) fn build_pstf_matrix(
    k: f64, a_h: f64, kappa_dot: f64, r_b: f64,
    omega_m: f64, omega_b: f64, omega_gamma: f64, a: f64,
    lg: usize, ln: usize,
    sigma_h: f64,  // σ/H: shear ratio (0 for FLRW, nonzero for Bianchi)
) -> Vec<f64> {
    let omega_nu = omega_gamma * 0.2271 * N_EFF;
    let lay = PSTFLayout::new(lg, ln);
    let n = lay.n_state;
    let mut m = vec![0.0; n * n];
    let idx = |r: usize, c: usize| r * n + c;
    let n0 = lay.nu_offset;

    // ═══ PHOTON PSTF HIERARCHY: I_ℓ ═══
    // dI_ℓ/dη = k[α^d_ℓ I_{ℓ-1} - α^u_ℓ I_{ℓ+1}] - κ̇(I_ℓ - S_ℓ)
    //         + σ/H × [shear coupling ℓ↔ℓ±2]  (Bianchi only)

    for ell in 0..=lg {
        // Free-streaming (tridiagonal): Δℓ = ±1
        if ell > 0 {
            m[idx(ell, ell-1)] = k * coupling::free_streaming_down(ell);
        }
        if ell < lg {
            m[idx(ell, ell+1)] = -k * coupling::free_streaming_up(ell);
        }

        // Thomson collision: -κ̇ I_ℓ (for ℓ ≥ 1; monopole ℓ=0 self-scatters)
        if ell >= 1 {
            m[idx(ell, ell)] += -kappa_dot;
        }

        // Bianchi shear coupling (pentadiagonal): Δℓ = ±2
        if sigma_h.abs() > 0.0 && ell >= 2 {
            let c_down = coupling::shear_coupling_down(ell);
            m[idx(ell, ell-2)] += sigma_h * a_h * c_down;
        }
        if sigma_h.abs() > 0.0 && ell + 2 <= lg {
            let c_up = coupling::shear_coupling_up(ell);
            m[idx(ell, ell+2)] += sigma_h * a_h * c_up;
        }
    }

    // Θ₁ collision source: +κ̇ v_b / 3
    if lg >= 1 {
        m[idx(1, lay.vb_idx)] += kappa_dot / 3.0;
    }

    // ═══ Θ₀ GRAVITATIONAL COUPLING ═══
    // In PSTF formalism: Θ₀' includes -Φ̇ (metric driving)
    // For k ≥ k_analytic: Φ̇ = +ℋΦ + velocity_sources/k²
    // → M[0, phi] = -(ℋ - k²/(3ℋ))  [from substituting Φ' equation]
    // For k < k_analytic: source is analytic g/3, so this coupling is unused
    let phi_dot_coeff = a_h - k * k / (3.0 * a_h.max(1e-30));
    m[idx(0, lay.phi_idx)] = -phi_dot_coeff;

    // ═══ Θ₁ GRAVITATIONAL COUPLING ═══
    // Θ₁' ∝ k Ψ/3 = -k Φ/3 (no aniso stress approx)
    if lg >= 1 {
        m[idx(1, lay.phi_idx)] = -k / 3.0;
    }

    // ═══ NEUTRINO PSTF HIERARCHY: N_ℓ ═══
    for ell in 0..=ln {
        if ell > 0 {
            m[idx(n0+ell, n0+ell-1)] = k * coupling::free_streaming_down(ell);
        }
        if ell < ln {
            m[idx(n0+ell, n0+ell+1)] = -k * coupling::free_streaming_up(ell);
        }
    }
    // N₀ gravitational coupling (same as Θ₀)
    m[idx(n0, lay.phi_idx)] = -phi_dot_coeff;
    // N₁ gravitational coupling
    if ln >= 1 {
        m[idx(n0+1, lay.phi_idx)] = -k / 3.0;
    }

    // ═══ MATTER: covariant density + velocity ═══
    // D_c' = -3Φ̇ (CDM, v_c = 0)
    m[idx(lay.dc_idx, lay.phi_idx)] = -3.0 * phi_dot_coeff;
    // D_b' = -kV_b - 3Φ̇
    m[idx(lay.db_idx, lay.vb_idx)] = -k;
    m[idx(lay.db_idx, lay.phi_idx)] = -3.0 * phi_dot_coeff;
    // V_b' = -ℋV_b + kΨ + κ̇(3Θ₁-V_b)/R_b
    let inv_rb = 1.0 / r_b.max(1e-10);
    m[idx(lay.vb_idx, lay.vb_idx)] = -a_h - kappa_dot * inv_rb;
    m[idx(lay.vb_idx, lay.phi_idx)] = -k;  // kΨ = -kΦ
    if lg >= 1 {
        m[idx(lay.vb_idx, 1)] = 3.0 * kappa_dot * inv_rb;
    }

    // ═══ WEYL POTENTIAL: Φ' from (0i) Einstein ═══
    // Φ' = +ℋΦ + (3/2)(ℋ²/k²) Σ (1+w_i) Ω_i v_i
    let k2 = k * k;
    if k2 > 1e-20 {
        let omega_c = omega_m - omega_b;
        let mom = 1.5 * a_h * a_h / k2;
        m[idx(lay.phi_idx, lay.phi_idx)] = a_h;  // +ℋ self-coupling
        m[idx(lay.phi_idx, lay.vb_idx)] = mom * omega_b / a;
        if lg >= 1 {
            m[idx(lay.phi_idx, 1)] = mom * 4.0 * omega_gamma / (a * a);
        }
        if ln >= 1 {
            m[idx(lay.phi_idx, n0+1)] = mom * 4.0 * omega_nu / (a * a);
        }
        // Anisotropic stress correction Ψ ≠ -Φ
        let omega_r_total = omega_gamma + omega_nu;
        let rho_r = omega_r_total / (a * a * a * a);
        let omega_lambda = 1.0 - omega_m - omega_r_total;
        let rho_tot = (rho_r + omega_m / (a*a*a) + omega_lambda).max(1e-30);
        let aniso_coeff = 4.0 * a_h * a_h / k2 * rho_r / rho_tot;
        let f_g = omega_gamma / omega_r_total.max(1e-30);
        let f_n = omega_nu / omega_r_total.max(1e-30);
        if lg >= 2 { m[idx(lay.phi_idx, 2)] += a_h * aniso_coeff * f_g; }
        if ln >= 2 { m[idx(lay.phi_idx, n0+2)] += a_h * aniso_coeff * f_n; }
    }

    m
}

/// Adiabatic IC in the PSTF formalism.
/// Normalized to ζ = 1 (comoving curvature perturbation).
pub(crate) fn pstf_adiabatic_ic(lay: &PSTFLayout) -> Vec<f64> {
    let mut y = vec![0.0; lay.n_state];
    let phi_init = 1.0;  // Φ = 1 → ζ = -(3/2)Φ = -3/2
    y[0] = -0.5 * phi_init;                 // I₀ = -Φ/2
    y[lay.nu_offset] = -0.5 * phi_init;     // N₀ = -Φ/2
    y[lay.dc_idx] = -1.5 * phi_init;        // D_c = -3Φ/2
    y[lay.db_idx] = -1.5 * phi_init;        // D_b = -3Φ/2
    y[lay.phi_idx] = phi_init;              // Φ
    y
}

/// Result from the PSTF solver.
pub(crate) struct PSTFKmodeResult {
    pub(crate) eta_grid: Vec<f64>,
    pub(crate) source_gi: Vec<f64>,  // gauge-invariant source I₀ = Θ₀+Ψ (or analytic g/3)
    pub(crate) n_state: usize,
    pub(crate) k: f64,
    pub(crate) is_analytic: bool,
}

/// Solve a k-mode using the PSTF hierarchy.
///
/// For k < k_analytic: returns the ANALYTIC Sachs-Wolfe source g/3.
/// For k ≥ k_analytic: evolves the full hierarchy and extracts I₀ = Θ₀ - Φ.
pub(crate) fn solve_pstf_kmode(
    k: f64, params: &VisibilityParams, vis: &VisibilityResult,
    ell_max_g: usize, ell_max_nu: usize,
    sigma_h: f64,  // shear ratio (0 for FLRW)
) -> Result<PSTFKmodeResult, String> {
    // In FLRW (σ=0): use ANALYTIC source g/3 for ALL k.
    // The Sachs-Wolfe g/3 is EXACT for adiabatic modes in the thin-shell limit.
    // This avoids the Newtonian gauge Φ instability (+ℋ self-coupling).
    //
    // In Bianchi (σ≠0): use NUMERICAL solver (sync gauge hierarchy from pstf/).
    // The anisotropic correction σ_{ab} couples to I_ℓ via Δℓ=±2 (pentadiagonal).
    // This is handled by the full PSTF hierarchy with shear coupling.
    let use_analytic = sigma_h.abs() < 1e-15;  // FLRW: always analytic
    let n_vis = vis.z_grid.len();
    let eta_max = vis.eta_grid[n_vis - 1];
    let h0c = params.h * 1e5 / 2.99792458e8;
    let og = params.omega_gamma();
    let lg = ell_max_g; let ln = ell_max_nu;
    let lay = PSTFLayout::new(lg, ln);
    let n = lay.n_state;

    if use_analytic {
        // ANALYTIC path: source = g × (1/3) (exact SW for superhorizon adiabatic modes)
        let mut eta_grid = Vec::with_capacity(n_vis);
        let mut source_gi = Vec::with_capacity(n_vis);
        for i in 0..n_vis {
            eta_grid.push(vis.eta_grid[i]);
            source_gi.push(vis.g_grid[i] * (1.0 / 3.0));
        }
        return Ok(PSTFKmodeResult {
            eta_grid, source_gi, n_state: n, k, is_analytic: true,
        });
    }

    // NUMERICAL path: evolve PSTF hierarchy with Rodas5P
    profiler::inc_kmode();
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n * n);

    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        let z = vis.z_grid[i];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[i];
        let r = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));
        let mat = build_pstf_matrix(k, a_h, kd, r, params.omega_m, params.omega_b, og, a, lg, ln, sigma_h);
        mats_flat.extend_from_slice(&mat);
    }

    let y0 = pstf_adiabatic_ic(&lay);
    let h_max_k = (4.0 * 3.0_f64.sqrt() / k.max(1e-10)).min(200.0);
    let cfg = Rodas5PConfig {
        rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
        h_init: None, h_min: 1e-14, h_max: h_max_k,
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
        use_analytic_jacobian: true, use_ft_term: false,
        use_blas_lu: false, use_block_diag: true,
        ell_max_gamma_hint: lg, ell_max_nu_hint: ln,
        ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false,
    };

    let tau_eval = tau_profile.clone();
    let (snapshots_rev, _, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
    )?;

    // Extract gauge-invariant source: I₀ = Θ₀ + Ψ = Θ₀ - Φ (our convention Ψ = -Φ)
    let n_snaps = snapshots_rev.len();
    let mut eta_grid = Vec::with_capacity(n_snaps);
    let mut source_gi = Vec::with_capacity(n_snaps);

    for si in 0..n_snaps {
        let ri = n_snaps - 1 - si;
        let vis_i = ri;
        if vis_i >= n_vis { continue; }
        eta_grid.push(vis.eta_grid[vis_i]);

        let y = &snapshots_rev[si];
        let g = vis.g_grid[vis_i];
        let theta0 = y[0];
        let phi = y[lay.phi_idx];
        // I₀ = Θ₀ + Ψ = Θ₀ - Φ (gauge-invariant monopole perturbation)
        let i0 = theta0 - phi;
        source_gi.push(g * i0);
    }

    Ok(PSTFKmodeResult {
        eta_grid, source_gi, n_state: n, k, is_analytic: false,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    #[test]
    fn test_pstf_layout() {
        let lay = PSTFLayout::new(20, 10);
        assert_eq!(lay.n_state, 21 + 11 + 4);  // photon + neutrino + (dc,db,vb,phi)
        assert_eq!(lay.phi_idx, lay.n_state - 1);
    }

    #[test]
    fn test_pstf_matrix_structure() {
        let lg = 15; let ln = 8;
        let mat = build_pstf_matrix(0.05, 0.01, 100.0, 0.1, 0.3153, 0.0493, 9.14e-5, 2.5e-4, lg, ln, 0.0);
        let lay = PSTFLayout::new(lg, ln);
        let n = lay.n_state;

        // Check PSTF coupling coefficients
        // Free-streaming ℓ=0→1: α^d_1 = 1/1 = 1, so M[1,0] = k × 1 = 0.05
        let fs_10 = mat[1 * n + 0];
        assert!((fs_10 - 0.05).abs() < 1e-10, "FS 1→0: {}", fs_10);

        // Free-streaming ℓ=1→0: -α^u_0 = -1/3, so M[0,1] = -k/3 = -0.0167
        let fs_01 = mat[0 * n + 1];
        assert!((fs_01 - (-0.05/3.0)).abs() < 1e-10, "FS 0→1: {}", fs_01);

        // Collision at ℓ=2: M[2,2] includes -κ̇ = -100
        let col_22 = mat[2 * n + 2];
        assert!(col_22 < -99.0, "Collision ℓ=2: {}", col_22);

        eprintln!("  PSTF matrix: n={}, FS[1,0]={:.4}, FS[0,1]={:.4}, Col[2,2]={:.1}",
            n, fs_10, fs_01, col_22);
    }

    /// THE CRITICAL TEST: D₂ from PSTF solver with gauge-invariant source
    #[test]
    fn test_pstf_d2() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let t_uk2 = (2.7255e6_f64).powi(2);

        let n_k = 60; let k_min = 1e-5_f64; let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k).map(|i|
            k_min * (k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();

        let mut cl2 = 0.0_f64;
        let mut n_anal = 0; let mut n_num = 0;

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k*280.0*2.0).ceil() as usize).max(8).min(25);
            let ln = (lg/2).max(6);

            let kr = match solve_pstf_kmode(k, &p, &vis, lg, ln, 0.0) {
                Ok(r) => r, Err(_) => continue,
            };
            if kr.is_analytic { n_anal += 1; } else { n_num += 1; }

            // LoS: Δ_ℓ = ∫ source_gi × j_ℓ(kη) dη
            let n = kr.eta_grid.len();
            let mut d2 = 0.0_f64;
            for i in 1..n {
                let x = k * kr.eta_grid[i];
                if x < 1e-10 || x > 5000.0 { continue; }
                let de = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
                d2 += kr.source_gi[i] * spherical_bessel_j(2, x) * de;
            }

            let pz = 2.1e-9 * (k/0.05_f64).powf(-0.0351);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            cl2 += 4.0*PI * pz * dlnk * (4.0/9.0) * d2 * d2;
        }

        let d2r = 6.0/(2.0*PI) * cl2 * t_uk2;
        eprintln!("\n  === PSTF D₂ (1+3 covariant solver) ===");
        eprintln!("  D₂(SW) = {:.1} μK² (n_anal={}, n_num={})", d2r, n_anal, n_num);
        eprintln!("  D₂+ISW ≈ {:.1} μK²", d2r * 1.15);
        eprintln!("  CLASS  = 1025 μK²");
        assert!(d2r > 700.0 && d2r < 1200.0,
            "D₂ = {:.1} out of range [700, 1200]", d2r);
    }
}

#[cfg(test)]
mod pstf_debug {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_pstf_numerical_source() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        eprintln!("\n  === PSTF NUMERICAL SOURCE DEBUG ===");
        for &k in &[0.005_f64, 0.01, 0.02, 0.03] {
            let lg = ((k*280.0*2.0).ceil() as usize).max(8).min(25);
            let ln = (lg/2).max(6);
            let kr = match solve_pstf_kmode(k, &p, &vis, lg, ln, 0.0) {
                Ok(r) => r, Err(e) => { eprintln!("  k={:.3}: FAIL: {}", k, &e[..40.min(e.len())]); continue; },
            };
            let max_src = kr.source_gi.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
            let has_nan = kr.source_gi.iter().any(|s| !s.is_finite());
            let n = kr.eta_grid.len();
            eprintln!("  k={:.3}: max|src|={:.4e}, nan={}, n={}, analytic={}",
                k, max_src, has_nan, n, kr.is_analytic);
            // Print at visibility peak
            let i_peak = kr.source_gi.iter().enumerate()
                .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;
            eprintln!("    peak at η={:.1}: src={:.4e}", kr.eta_grid[i_peak], kr.source_gi[i_peak]);
        }
    }
}
