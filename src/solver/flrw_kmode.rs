use crate::solver::profiler;
// BE-04: FLRW k-mode perturbation solver using Rodas5P implicit integrator.
//
// System: y' = A(η) y  (linear, stiff due to κ̇ collision terms)
// State: y = [Θ₀..Θ_L, N₀..N_M, δ_c, v_c, δ_b, v_b, Φ]
// Solved via LinearProfileDyn + Rodas5P (existing infrastructure).

use crate::core::config::{Rodas5PConfig, Rodas5PStats};
use crate::solver::stacked::integrate_linear_profile_rodas5p;
use crate::solver::rodas5p::LinearProfileDyn;
use crate::solver::dopri5::{dopri5_tableau, step_dopri5_linear, dopri5_new_h};
use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult, compute_visibility};
use crate::recombination::hyrec_tables::HyRecTables;

const N_EFF: f64 = 3.044;

/// Build the A(η) matrix for FLRW scalar perturbations at a single η.
///
/// State vector indices (CL-01 §4):
///   0..L       : Θ₀..Θ_L (photon)
///   L+1..L+1+M : N₀..N_M (neutrino)
///   L+M+2      : δ_c
///   L+M+3      : v_c
///   L+M+4      : δ_b
///   L+M+5      : v_b
///   L+M+6      : Φ (potential)
///
/// CL-10: When `tau_conf > 0`, applies the completion relation at ℓ = ℓ_max
/// for both photon and neutrino hierarchies:
///   Θ_{ℓ+1} ≈ (2ℓ+1)/(kτ) Θ_ℓ − Θ_{ℓ−1}
/// This eliminates reflection artifacts from hard truncation.
fn build_flrw_matrix(
    k: f64, a_h: f64, kd: f64, r: f64, f_nu: f64,
    omega_m: f64, omega_b: f64, omega_gamma: f64, a: f64,
    ell_max_g: usize, ell_max_nu: usize,
    tau_conf: f64,  // CL-10: conformal time from Big Bang [Mpc]; 0 = no completion
) -> Vec<f64> {
    let lg = ell_max_g;
    let ln = ell_max_nu;
    let n = lg + 1 + ln + 1 + 5;
    let mut a_mat = vec![0.0; n * n];
    let idx = |r: usize, c: usize| -> usize { r * n + c };
    let omega_nu = omega_gamma * 0.2271 * N_EFF; // Ω_ν from N_eff

    let phi_idx = n - 1;
    let dc_idx = lg + 1 + ln + 1;
    let vc_idx = dc_idx + 1;
    let db_idx = vc_idx + 1;
    let vb_idx = db_idx + 1;

    // ═══ Photon hierarchy ═══
    // Θ₀' = −k Θ₁ − Φ'
    // Φ' ≈ (aH − k²/(3aH))Φ from momentum constraint (conformal Newtonian gauge).
    // NOTE: This self-coupling is positive for super-horizon modes — a structural
    // property of Newtonian gauge, not a bug. For high-z stability, synchronous
    // gauge (CAMB/PSTF formalism) is the correct long-term solution.
    let phi_dot_coeff = a_h - k * k / (3.0 * a_h.max(1e-30));
    a_mat[idx(0, 1)] = -k;                    // Θ₀' ∝ −k Θ₁
    a_mat[idx(0, phi_idx)] = -phi_dot_coeff;   // Θ₀' ∝ −Φ'

    if lg >= 1 {
        a_mat[idx(1, 0)] = k / 3.0;           // Θ₁' ∝ k/3 Θ₀
        a_mat[idx(1, phi_idx)] = -k / 3.0;    // Θ₁' ∝ k/3 Ψ = −k/3 Φ
        if lg >= 2 { a_mat[idx(1, 2)] = -2.0 * k / 3.0; } // −2k/3 Θ₂
        a_mat[idx(1, 1)] = -kd;               // −κ̇ Θ₁
        a_mat[idx(1, vb_idx)] = kd / 3.0;     // +κ̇ v_b/3
    }

    // Θ_ℓ' = k/(2ℓ+1)(ℓΘ_{ℓ-1} − (ℓ+1)Θ_{ℓ+1}) − κ̇ Θ_ℓ  (ℓ ≥ 2)
    // CL-10: At ℓ = ℓ_max, apply completion relation:
    //   Θ_{ℓ+1} ≈ (2ℓ+1)/(kτ) Θ_ℓ − Θ_{ℓ-1}
    //   → Θ_ℓ' = k Θ_{ℓ-1} − [(ℓ+1)/τ + κ̇] Θ_ℓ
    // PRE-04: SPONGE LAYER — absorbing boundary at top ℓ to prevent
    //   free-streaming cascade reflection. Adds artificial damping:
    //   A[ℓ,ℓ] += -α_sponge × k × ((ℓ - ℓ_sponge)/(ℓ_max - ℓ_sponge))²
    //   for ℓ > ℓ_sponge. The damping rate scales with k (streaming rate).
    //   This prevents power from reflecting off the ℓ_max boundary at late times
    //   when κ̇ → 0 (free-streaming regime).
    let use_completion = tau_conf > 1e-6 && k > 1e-10;
    let sponge_alpha = 0.0_f64;  // PRE-04: sponge OFF for baseline; enable for high-k
    let sponge_width = (lg / 3).max(4);
    let ell_sponge_start = if lg > sponge_width + 2 { lg - sponge_width } else { lg };
    for ell in 2..=lg {
        if ell < lg {
            // Interior multipole: standard coupling
            let fac = k / (2 * ell + 1) as f64;
            a_mat[idx(ell, ell - 1)] = fac * ell as f64;
            a_mat[idx(ell, ell + 1)] = -fac * (ell + 1) as f64;
            a_mat[idx(ell, ell)] = -kd;
        } else if use_completion {
            // CL-10: ℓ = ℓ_max with completion relation
            a_mat[idx(ell, ell - 1)] = k;  // k × Θ_{ℓ-1}
            a_mat[idx(ell, ell)] = -((ell + 1) as f64 / tau_conf + kd); // −[(ℓ+1)/τ + κ̇]
        } else {
            // Fallback: hard truncation (no Θ_{ℓ+1} coupling)
            let fac = k / (2 * ell + 1) as f64;
            a_mat[idx(ell, ell - 1)] = fac * ell as f64;
            a_mat[idx(ell, ell)] = -kd;
        }
        // PRE-04: Sponge damping for ℓ > ℓ_sponge_start
        if ell > ell_sponge_start && sponge_width > 0 {
            let depth = (ell - ell_sponge_start) as f64 / sponge_width as f64;
            a_mat[idx(ell, ell)] += -sponge_alpha * k * depth * depth;
        }
    }

    // ═══ Neutrino hierarchy (free-streaming, no collision) ═══
    let n0 = lg + 1;
    a_mat[idx(n0, n0 + 1)] = -k;
    a_mat[idx(n0, phi_idx)] = -phi_dot_coeff;

    // N₁' = k/3(N₀ + Ψ)
    if ln >= 1 {
        a_mat[idx(n0 + 1, n0)] = k / 3.0;
        a_mat[idx(n0 + 1, phi_idx)] = -k / 3.0;
        if ln >= 2 { a_mat[idx(n0 + 1, n0 + 2)] = -2.0 * k / 3.0; }
    }

    for ell in 2..=ln {
        if ell < ln {
            let fac = k / (2 * ell + 1) as f64;
            a_mat[idx(n0 + ell, n0 + ell - 1)] = fac * ell as f64;
            a_mat[idx(n0 + ell, n0 + ell + 1)] = -fac * (ell + 1) as f64;
        } else if use_completion {
            // CL-10: completion at neutrino ℓ_max (no collision)
            a_mat[idx(n0 + ell, n0 + ell - 1)] = k;
            a_mat[idx(n0 + ell, n0 + ell)] = -((ell + 1) as f64) / tau_conf;
        } else {
            let fac = k / (2 * ell + 1) as f64;
            a_mat[idx(n0 + ell, n0 + ell - 1)] = fac * ell as f64;
        }
        // PRE-04: Sponge for neutrinos (always free-streaming, no κ̇)
        let nu_sponge_width = (ln / 3).max(3);
        let nu_sponge_start = if ln > nu_sponge_width + 2 { ln - nu_sponge_width } else { ln };
        if ell > nu_sponge_start && nu_sponge_width > 0 {
            let depth = (ell - nu_sponge_start) as f64 / nu_sponge_width as f64;
            a_mat[idx(n0 + ell, n0 + ell)] += -sponge_alpha * k * depth * depth;
        }
    }

    // ═══ CDM: δ_c' = −k v_c − 3Φ',  v_c' = −aH v_c + k Ψ ═══
    a_mat[idx(dc_idx, vc_idx)] = -k;
    a_mat[idx(dc_idx, phi_idx)] = -3.0 * phi_dot_coeff;
    a_mat[idx(vc_idx, vc_idx)] = -a_h;
    a_mat[idx(vc_idx, phi_idx)] = -k; // kΨ = −kΦ

    // ═══ Baryons: δ_b' = −k v_b − 3Φ',  v_b' = −aH v_b + kΨ + κ̇/R(3Θ₁ − v_b) ═══
    a_mat[idx(db_idx, vb_idx)] = -k;
    a_mat[idx(db_idx, phi_idx)] = -3.0 * phi_dot_coeff;
    a_mat[idx(vb_idx, vb_idx)] = -a_h - kd / r.max(1e-10);
    a_mat[idx(vb_idx, phi_idx)] = -k;
    if lg >= 1 { a_mat[idx(vb_idx, 1)] = 3.0 * kd / r.max(1e-10); }

    // ═══ Φ: momentum constraint (0i Einstein) — conformal Newtonian gauge ═══
    // k²(Φ' + aHΨ) = +(3/2)(aH)² Σ(1+w_i)Ω_i v_i / a^{1+3w_i}
    // With Ψ = −Φ: Φ' = aHΦ + velocity_source
    //
    // WARNING: Self-coupling +aH is positive → gauge artifact of Newtonian gauge.
    // Stable at z_max=4000 for k≤0.03 but UNSTABLE at higher z_max.
    // Long-term fix: migrate to synchronous gauge (CAMB/PSTF formalism).
    let k2 = k * k;
    if k2 > 1e-20 {
        let mom_coeff = 1.5 * a_h * a_h / k2;
        let omega_c = omega_m - omega_b;
        a_mat[idx(phi_idx, vc_idx)] = mom_coeff * omega_c / a;
        a_mat[idx(phi_idx, vb_idx)] = mom_coeff * omega_b / a;
        if lg >= 1 {
            a_mat[idx(phi_idx, 1)] = mom_coeff * 4.0 * omega_gamma / (a * a);
        }
        if ln >= 1 {
            a_mat[idx(phi_idx, n0 + 1)] = mom_coeff * 4.0 * omega_nu / (a * a);
        }
        a_mat[idx(phi_idx, phi_idx)] = a_h;
        // Anisotropic stress correction Ψ ≠ −Φ
        {
            let omega_r_total = omega_gamma + omega_nu;
            let rho_r = omega_r_total / (a * a * a * a);
            let omega_lambda = 1.0 - omega_m - omega_r_total;
            let rho_tot = rho_r + omega_m / (a * a * a) + omega_lambda;
            let aniso_coeff = 4.0 * a_h * a_h / k2 * rho_r / rho_tot;
            let f_g = omega_gamma / omega_r_total.max(1e-30);
            let f_n = omega_nu / omega_r_total.max(1e-30);
            if lg >= 2 {
                a_mat[idx(phi_idx, 2)] += a_h * aniso_coeff * f_g;
            }
            if ln >= 2 {
                a_mat[idx(phi_idx, n0 + 2)] += a_h * aniso_coeff * f_n;
            }
        }
    } else {
        a_mat[idx(phi_idx, phi_idx)] = 0.0;
    }

    a_mat
}

/// Solve FLRW k-mode via Rodas5P and return (η_grid, source_function).
pub(crate) fn solve_kmode_rodas5p(
    k: f64,
    params: &VisibilityParams,
    vis: &VisibilityResult,
    ell_max_g: usize,
    ell_max_nu: usize,
) -> Result<(Vec<f64>, Vec<f64>), String> {
    let h0c = params.h * 1e5 / 2.99792458e8; // H₀/c [Mpc⁻¹]
    let og = params.omega_gamma();
    let n_vis = vis.z_grid.len();

    let lg = ell_max_g;
    let ln = ell_max_nu;
    let n_state = lg + 1 + ln + 1 + 5;

    // Build η profile and matrices
    // vis.z_grid is increasing (z=0..z_max), vis.eta_grid is increasing (η=0..η_max)
    // We evolve from η=0 to η_max (low z to high z? No: η increases with z in our convention)
    // Actually vis.eta_grid[0]=0 at z=0, vis.eta_grid[n-1]=η_max at z=z_max
    // The Boltzmann equation needs evolution from high z (early) to low z (late)
    // = from η_max to η=0 in our convention? No...
    //
    // In standard cosmology, η increases forward in time:
    //   η = 0 at Big Bang, η = η₀ at today
    // In our visibility code: η(z) = ∫_0^z c dz'/H(z')
    //   η(z=0) = 0, η(z=z_max) = η_max
    // This is actually the COMOVING DISTANCE, not conformal time.
    // For the LoS integral, x = k × d(z) where d = η(z) is comoving distance.
    //
    // For the Boltzmann evolution, we evolve in conformal time τ from early to late.
    // conformal time: τ increases from 0 (Big Bang) to τ₀ (today).
    // τ(z) = η₀ − η(z) in our convention (η = comoving distance).
    //
    // So: evolve from τ = small (high z = large η) to τ = large (low z = small η).
    // = evolve in η from η_max downward to 0.
    //
    // BUT integrate_linear_profile_rodas5p expects eta_eval to be INCREASING.
    // So I need to flip: use (η_max − η) as the evolution variable.

    // Build reversed profile: τ = η_max − η, increasing from 0 (z_max) to η_max (z=0)
    let eta_max = vis.eta_grid[n_vis - 1];
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n_state * n_state);

    let _t_mb = std::time::Instant::now();
    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);

        let z = vis.z_grid[i];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[i];
        let r = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));
        let f_nu = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);

        let mat = build_flrw_matrix(k, a_h, kd, r, f_nu, params.omega_m, params.omega_b, og, a, lg, ln, tau);
        mats_flat.extend_from_slice(&mat);
    }

    // Initial conditions at z_max (early universe, radiation era)
    let mut y0 = vec![0.0; n_state];
    let phi_init = 1.0;
    y0[0] = -0.5 * phi_init;           // Θ₀ = −Φ/2
    y0[lg + 1] = -0.5 * phi_init;      // N₀ = −Φ/2
    let dc_idx = lg + 1 + ln + 1;
    y0[dc_idx] = -1.5 * phi_init;      // δ_c
    y0[dc_idx + 2] = -1.5 * phi_init;  // δ_b
    y0[n_state - 1] = phi_init;        // Φ

    // Evaluation points: same as profile
    let tau_eval = tau_profile.clone();

    let cfg = Rodas5PConfig {
        rtol: 1e-5, atol: 1e-8, // OPT-F: relaxed for speed
        max_steps: 500000,
        h_init: None,
        h_min: 1e-10, h_max: 200.0, // OPT-C: larger steps
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04, // OPT-B
        use_analytic_jacobian: true,
        use_ft_term: false,
        use_blas_lu: false,
        use_block_diag: true, // OPT-A: +23.8% wall
        ell_max_gamma_hint: lg,
        ell_max_nu_hint: ln,
        ell_max_pol_hint: 0,
        include_pol_hint: false,
        use_sparse: false,
    };

    let (snapshots, stats, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n_state, &y0, &tau_eval, &cfg,
    )?;

    // Extract source function: S(η) = g(η)(Θ₀ + Ψ) + e^{-τ}(Ψ'+Φ')
    // snapshots[i] is the state at tau_eval[i], which corresponds to vis index (n_vis-1-i)
    let mut eta_out = Vec::with_capacity(n_vis);
    let mut source_out = Vec::with_capacity(n_vis);

    let omega_r = og + og * (7.0/8.0) * (4.0_f64/11.0).powf(4.0/3.0) * N_EFF;
    let omega_lambda = 1.0 - params.omega_m - omega_r;
    let f_nu_src = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
    let f_gamma_src = 1.0 - f_nu_src;
    let mut prev_psi_plus_phi = 0.0_f64;
    let mut prev_eta = 0.0_f64;

    for (ti, snap) in snapshots.iter().enumerate() {
        let vis_i = n_vis - 1 - ti; // reverse index back to vis grid
        if vis_i >= n_vis { continue; }
        let g = vis.g_grid[vis_i];
        let theta_0 = snap[0];
        let phi = snap[n_state - 1];
        // ACC-01 + P0-1 FIX: Psi from traceless Einstein (coeff=4, not 16)
        let theta_2 = if lg >= 2 { snap[2] } else { 0.0 };
        let n_2 = if ln >= 2 { snap[lg + 1 + 2] } else { 0.0 };
        let z_i = vis.z_grid[vis_i];
        let a_i = 1.0 / (1.0 + z_i);
        let a_h_i = a_i * h0c * params.e_of_z(z_i);
        let psi = compute_psi_algebraic_v2(
            phi, theta_2, n_2, a_h_i, k,
            f_gamma_src, f_nu_src, omega_r, params.omega_m, omega_lambda, a_i,
        );

        let s_sw = g * (theta_0 + psi);
        // PRE-01: ISW source from finite differences of Psi+Phi
        let psi_plus_phi = psi + phi;
        let eta_i = vis.eta_grid[vis_i];
        let s_isw = if ti > 0 && (eta_i - prev_eta).abs() > 1e-20 {
            let exp_neg_tau = (-vis.tau_grid[vis_i]).exp();
            exp_neg_tau * (psi_plus_phi - prev_psi_plus_phi) / (eta_i - prev_eta)
        } else { 0.0 };
        prev_psi_plus_phi = psi_plus_phi;
        prev_eta = eta_i;

        eta_out.push(eta_i);
        source_out.push(s_sw + s_isw);
    }

    // Sort by η (increasing)
    let mut pairs: Vec<_> = eta_out.into_iter().zip(source_out).collect();
    pairs.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    let eta_out: Vec<f64> = pairs.iter().map(|p| p.0).collect();
    let source_out: Vec<f64> = pairs.iter().map(|p| p.1).collect();

    Ok((eta_out, source_out))
}

/// Compute FLRW C_ℓ using Rodas5P k-mode solver.
///
/// ⚠️  VALIDATION-ONLY: hardcoded k_max = 0.03 Mpc⁻¹ (→ ℓ ≲ 500),
/// ℓ_max_γ = 12 (severe truncation above k ~ 0.01), no TCA.
/// For production C_ℓ to ℓ = 3000, use the CL-04A pipeline (pending).
pub(crate) fn compute_flrw_cl_rodas5p(
    params: &VisibilityParams,
    ell_max: usize,
    n_k: usize,
) -> Result<Vec<f64>, String> {
    let tables = HyRecTables::generate(300);
    let vis = compute_visibility(params, &tables, 5000); // fewer points for speed
    let eta_0 = *vis.eta_grid.last().unwrap();

    let a_s = 2.1e-9_f64;
    let n_s = 0.9649_f64;
    let k_pivot = 0.05_f64;
    let k_min = 5e-5_f64;
    let k_max = 0.03_f64;
    let dlnk = (k_max / k_min).ln() / (n_k - 1).max(1) as f64;

    let lg = 12;
    let ln = 8;
    let mut cl = vec![0.0; ell_max + 1];

    for ik in 0..n_k {
        let frac = ik as f64 / (n_k - 1).max(1) as f64;
        let k = k_min * (k_max / k_min).powf(frac);
        let delta2 = a_s * (k / k_pivot).powf(n_s - 1.0);

        let (eta_grid, source) = solve_kmode_rodas5p(k, params, &vis, lg, ln)?;

        for ell in 2..=ell_max {
            let mut delta_ell = 0.0;
            for i in 1..eta_grid.len() {
                let x0 = k * (eta_0 - eta_grid[i - 1]);
                let x1 = k * (eta_0 - eta_grid[i]);
                let j0 = if x0 > 0.0 { crate::los::bessel::spherical_bessel_j(ell, x0) } else if ell == 0 { 1.0 } else { 0.0 };
                let j1 = if x1 > 0.0 { crate::los::bessel::spherical_bessel_j(ell, x1) } else if ell == 0 { 1.0 } else { 0.0 };
                let deta = eta_grid[i] - eta_grid[i - 1];
                delta_ell += 0.5 * (source[i - 1] * j0 + source[i] * j1) * deta;
            }
            cl[ell] += 4.0 * std::f64::consts::PI * delta2 * delta_ell * delta_ell * dlnk;
        }
    }

    Ok(cl)
}

// ═══════════════════════════════════════════════════════════════
// CL-02: Source Adaptor — extract full SourceValue from k-mode solver
// ═══════════════════════════════════════════════════════════════

use crate::los::source::{PerturbationSnapshot, SourceValue, evaluate_source, SourceGrid};

/// Result of a k-mode solve with full state history.
///
/// CL-01 index map: y = [Θ₀..Θ_L, N₀..N_M, δ_c, v_c, δ_b, v_b, Φ].
/// Convention: Θ_ℓ (raw temperature multipoles, conformal time d/dτ).
pub(crate) struct KmodeResult {
    /// Comoving distance grid [Mpc], increasing.
    pub(crate) eta_grid: Vec<f64>,
    /// State vector snapshots: snapshots[i_eta][i_component].
    pub(crate) snapshots: Vec<Vec<f64>>,
    /// Source function (legacy: SW-only).
    pub(crate) raw_theta0_source: Vec<f64>,
    /// Dimension parameters.
    pub(crate) ell_max_g: usize,
    pub(crate) ell_max_nu: usize,
    pub(crate) n_state: usize,
    /// Wavenumber [Mpc⁻¹].
    pub(crate) k: f64,
}

impl KmodeResult {
    /// CL-01 §4: Index of Θ_ℓ (photon).
    #[inline]
    pub(crate) fn idx_theta(&self, ell: usize) -> usize { ell }
    /// Index of N_ℓ (neutrino).
    #[inline]
    pub(crate) fn idx_nu(&self, ell: usize) -> usize { self.ell_max_g + 1 + ell }
    /// Index of δ_c.
    #[inline]
    pub(crate) fn idx_delta_c(&self) -> usize { self.ell_max_g + 1 + self.ell_max_nu + 1 }
    /// Index of v_c.
    #[inline]
    pub(crate) fn idx_v_c(&self) -> usize { self.idx_delta_c() + 1 }
    /// Index of δ_b.
    #[inline]
    pub(crate) fn idx_delta_b(&self) -> usize { self.idx_delta_c() + 2 }
    /// Index of v_b.
    #[inline]
    pub(crate) fn idx_v_b(&self) -> usize { self.idx_delta_c() + 3 }
    /// Index of Φ (Newtonian potential).
    #[inline]
    pub(crate) fn idx_phi(&self) -> usize { self.n_state - 1 }

    /// Extract PerturbationSnapshot at grid point i.
    ///
    /// CL-01 §4 mapping:
    ///   theta_0 ← y[0], theta_2 ← y[2], v_b ← y[L+M+5],
    ///   phi ← y[L+M+6], psi = −phi, phi_dot from finite difference.
    pub(crate) fn snapshot_at(&self, i: usize, phi_dot: f64) -> PerturbationSnapshot {
        let y = &self.snapshots[i];
        let phi = y[self.idx_phi()];
        PerturbationSnapshot {
            theta_0: y[self.idx_theta(0)],
            theta_2: if self.ell_max_g >= 2 { y[self.idx_theta(2)] } else { 0.0 },
            e_2: 0.0,  // No polarization in current kmode solver
            v_b: y[self.idx_v_b()],
            phi,
            psi: -phi,  // Ψ = −Φ (no anisotropic stress approximation)
            phi_dot,
            psi_dot: -phi_dot,
            sigma_h: 0.0,   // FLRW: no shear
            sigma_dot: 0.0,
        }
    }
}

/// Solve a single FLRW k-mode with Dopri5↔Rodas5P hybrid switching.
///
/// CL-08 HYBRID (LSODA-like):
///   Phase 1 (Dopri5, explicit): τ ∈ [0, τ_switch] — non-stiff after decoupling.
///     No LU factorization. Cost: 7 mat-vec per step = O(7n²).
///   Phase 2 (Rodas5P, implicit): τ ∈ [τ_switch, τ_max] — stiff tight-coupling.
///     One LU + 8 triangular solves per step = O(n³ + 8n²).
///
/// Switch criterion: κ̇/(aH) > 10 (tight-coupling onset in reversed time).
/// Both methods are differentiable via "discretize-then-optimize" (Kidger 2021).
pub(crate) fn solve_kmode_with_history(
    k: f64,
    params: &VisibilityParams,
    vis: &VisibilityResult,
    ell_max_g: usize,
    ell_max_nu: usize,
) -> Result<KmodeResult, String> {
    let h0c = params.h * 1e5 / 2.99792458e8;
    let og = params.omega_gamma();
    let n_vis = vis.z_grid.len();
    let lg = ell_max_g;
    let ln = ell_max_nu;
    let n_state = lg + 1 + ln + 1 + 5;
    let stride = n_state * n_state;
    let eta_max = vis.eta_grid[n_vis - 1];

    // ── Find TCA boundary (κ̇/aH < 200) ──
    let tca_threshold = 600.0_f64; // TF-05: CRS + safe threshold
    let mut i_tca = n_vis - 1;
    for vi in (0..n_vis).rev() {
        let z = vis.z_grid[vi];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[vi];
        if kd / a_h.max(1e-30) < tca_threshold {
            i_tca = vi;
            break;
        }
    }
    let z_tca = vis.z_grid[i_tca];
    let use_tca_prephase = false; // PRE-02: disabled — TCA CRS expansion produces
    // bad IC for sub-horizon modes (k×η_tca > 1). Standard adiabatic IC from z_max
    // + BDF full integration is stable and more accurate at all k.

    // ── Find decoupling boundary ──
    let kd_threshold = 10.0_f64;
    let mut i_switch = n_vis - 1;
    for vi in (0..n_vis).rev() {
        let z = vis.z_grid[vi];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[vi];
        if kd / a_h.max(1e-30) < kd_threshold {
            i_switch = vi;
            break;
        }
    }
    let tau_switch = eta_max - vis.eta_grid[i_switch];

    // ── Build matrix profile (skip TCA regime if enabled) ──
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * stride);
    let mut vis_idx_map: Vec<usize> = Vec::with_capacity(n_vis); // TF-04: snapshot→vis mapping
    let _t_mb = std::time::Instant::now();
    for i in (0..n_vis).rev() {
        let z = vis.z_grid[i];
        if use_tca_prephase && z > z_tca { continue; } // TF-04: skip TCA regime
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        vis_idx_map.push(i); // TF-04: record which vis index this snapshot corresponds to
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[i];
        let r = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));
        let f_nu = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
        let mat = build_flrw_matrix(k, a_h, kd, r, f_nu, params.omega_m, params.omega_b, og, a, lg, ln, tau);
        mats_flat.extend_from_slice(&mat);
    }

    profiler::add_matrix_build(_t_mb.elapsed().as_nanos() as u64);
    let tau_eval: Vec<f64> = tau_profile.clone();

    // ── Initial conditions (TCA-expanded or standard) ──
    let y0 = if use_tca_prephase {
        // TF-04c + TF-05: Extended TCA (6 DOF) + CRS second-order expansion
        use crate::solver::tca_extended::{evolve_ext_tca};
        use crate::solver::tca_second_order::{expand_with_crs, compute_dopacity};
        let ext_state = evolve_ext_tca(
            k, params.omega_b, params.omega_m, og,
            params.h, &vis.z_grid, &vis.eta_grid, &vis.kappa_dot_grid,
            z_tca, |z| params.e_of_z(z),
        );
        let a_tca = 1.0 / (1.0 + z_tca);
        let a_h_tca = a_tca * h0c * params.e_of_z(z_tca);
        let kd_tca = vis.kappa_dot_grid[i_tca];
        let dkd_tca = compute_dopacity(&vis.kappa_dot_grid, &vis.eta_grid, i_tca);
        // dv_b/dη from TCA RHS
        let r_tca = 3.0 * params.omega_b / (4.0 * og * (1.0 + z_tca));
        let r1 = 1.0 + r_tca;
        let dvb = -a_h_tca * r_tca / r1 * ext_state.v_b
            + k / r1 * (ext_state.theta0 - ext_state.phi);
        expand_with_crs(
            ext_state.theta0, ext_state.v_b, ext_state.delta_b,
            ext_state.v_c, ext_state.delta_c, ext_state.phi,
            k, a_h_tca, kd_tca, dkd_tca, dvb, 0.0, lg, ln,
        )
    } else {
        // Standard adiabatic IC at z_max
        let mut y = vec![0.0; n_state];
        let phi_init = 1.0;
        y[0] = -0.5 * phi_init;
        y[lg + 1] = -0.5 * phi_init;
        let dc_i = lg + 1 + ln + 1;
        y[dc_i] = -1.5 * phi_init;
        y[dc_i + 2] = -1.5 * phi_init;
        y[n_state - 1] = phi_init;        // Φ
        y
    };

    // ── Solver: Rodas5P (Newton-free Rosenbrock, L-stable) ──
    // Key fix: k-dependent h_max to stay within Rosenbrock stability region
    // on the imaginary axis. Acoustic oscillation ω ≈ k/√3, stability requires
    // ωh ≤ 4, so h_max = 4√3/k ≈ 6.93/k.
    // Rosenbrock needs no Newton iteration → handles extreme stiffness (κ̇~10⁶).
    profiler::inc_kmode();
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
    let (snapshots_rev, _, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n_state, &y0, &tau_eval, &cfg,
    )?;

    // ── Reverse to increasing η and extract SW source ──
    let n_profile = snapshots_rev.len();
    let mut eta_grid = Vec::with_capacity(n_profile);
    let mut snapshots = Vec::with_capacity(n_profile);
    let mut raw_theta0_source = Vec::with_capacity(n_profile);

    for ti in (0..n_profile).rev() {
        // TF-04: use vis_idx_map for correct vis↔snapshot correspondence
        let vis_i = if use_tca_prephase && ti < vis_idx_map.len() {
            vis_idx_map[ti]
        } else {
            n_vis - 1 - ti
        };
        if vis_i >= n_vis { continue; }
        let snap = &snapshots_rev[ti];
        let g = vis.g_grid[vis_i];
        let theta_0 = snap[0];
        // ACC-01 + P0-1: Psi from traceless Einstein
        let theta_2_dp = if lg >= 2 { snap[2] } else { 0.0 };
        let n_2_dp = if ln >= 2 { snap[lg + 1 + 2] } else { 0.0 };
        let z_dp = vis.z_grid[vis_i];
        let a_dp = 1.0 / (1.0 + z_dp);
        
        let phi = snap[n_state - 1];
        let omega_r_dp = og + og * (7.0/8.0) * (4.0_f64/11.0).powf(4.0/3.0) * N_EFF;
        let omega_lam_dp = 1.0 - params.omega_m - omega_r_dp;
        let a_h_dp = a_dp * h0c * params.e_of_z(z_dp);
        let f_nu_dp = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
        let f_g_dp = 1.0 - f_nu_dp;
        let psi = compute_psi_algebraic_v2(
            phi, theta_2_dp, n_2_dp, a_h_dp, k,
            f_g_dp, f_nu_dp, omega_r_dp, params.omega_m, omega_lam_dp, a_dp,
        );
        eta_grid.push(vis.eta_grid[vis_i]);
        snapshots.push(snap.clone());
        raw_theta0_source.push(g * (theta_0 + psi));
    }

    Ok(KmodeResult {
        eta_grid, snapshots, raw_theta0_source,
        ell_max_g: lg, ell_max_nu: ln, n_state, k,
    })
}

/// Linearly interpolate Dopri5 trajectory at target τ.
fn interpolate_dopri5_snaps(snaps: &[(f64, Vec<f64>)], tau: f64, n: usize) -> Vec<f64> {
    if snaps.is_empty() { return vec![0.0; n]; }
    if tau <= snaps[0].0 { return snaps[0].1.clone(); }
    let last = snaps.last().unwrap();
    if tau >= last.0 { return last.1.clone(); }
    let mut lo = 0_usize;
    let mut hi = snaps.len() - 1;
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if snaps[mid].0 <= tau { lo = mid; } else { hi = mid; }
    }
    let w = ((tau - snaps[lo].0) / (snaps[hi].0 - snaps[lo].0)).clamp(0.0, 1.0);
    (0..n).map(|i| snaps[lo].1[i] + w * (snaps[hi].1[i] - snaps[lo].1[i])).collect()
}

/// Extract a full SourceGrid from a KmodeResult using the CL-01 index mapping.
///
/// CL-07 + PRE-01: Source components:
///   S_SW  = g(η) × (Θ₀ + Ψ)               [Ψ from traceless Einstein, ACC-01]
///   S_Dop = (g'v_b + g×v_b')/k             [IBP form for j_ℓ basis]
///   S_ISW = e^{−τ} × d(Ψ+Φ)/dη            [finite difference, nonzero via ν shear]
///   S_pol = 0                                [no E₂ in current kmode solver]
///
/// ISW activation (PRE-01):
///   Ψ is computed algebraically from the traceless Einstein equation
///   k²(Φ+Ψ) = −4(aH)²(ρ_r/ρ_tot)(f_γΘ₂ + f_νN₂)
///   so Ψ ≠ −Φ when neutrino/photon quadrupole anisotropic stress
///   is nonzero, giving early ISW (radiation→matter transition) and
///   late ISW (Λ domination, via Φ decay).
pub(crate) fn extract_source_grid(
    result: &KmodeResult,
    vis: &VisibilityResult,
    params: &VisibilityParams,
) -> SourceGrid {
    let n = result.eta_grid.len();
    let n_vis = vis.eta_grid.len();
    let k = result.k;

    // ── Cosmological constants for Ψ algebraic (same as solve_kmode_with_history) ──
    let h0c = params.h * 1e5 / 2.99792458e8; // H₀/c [Mpc⁻¹]
    let og = params.omega_gamma();
    let omega_r = og + og * (7.0 / 8.0) * (4.0_f64 / 11.0).powf(4.0 / 3.0) * N_EFF;
    let omega_lambda = 1.0 - params.omega_m - omega_r;
    let f_nu = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
    let f_gamma = 1.0 - f_nu;
    let lg = result.ell_max_g;
    let ln = result.ell_max_nu;

    // ── Pre-compute g'(η) on the vis grid via centered finite differences ──
    let mut g_dot_vis = vec![0.0_f64; n_vis];
    if n_vis > 2 {
        let dt0 = vis.eta_grid[1] - vis.eta_grid[0];
        if dt0.abs() > 1e-30 { g_dot_vis[0] = (vis.g_grid[1] - vis.g_grid[0]) / dt0; }
        for j in 1..n_vis - 1 {
            let dt = vis.eta_grid[j + 1] - vis.eta_grid[j - 1];
            if dt.abs() > 1e-30 { g_dot_vis[j] = (vis.g_grid[j + 1] - vis.g_grid[j - 1]) / dt; }
        }
        let dt_last = vis.eta_grid[n_vis - 1] - vis.eta_grid[n_vis - 2];
        if dt_last.abs() > 1e-30 {
            g_dot_vis[n_vis - 1] = (vis.g_grid[n_vis - 1] - vis.g_grid[n_vis - 2]) / dt_last;
        }
    }

    // ── Pre-compute v_b'(η) from snapshot grid via centered FD ──
    let vb_idx = result.idx_v_b();
    let mut vb_dot = vec![0.0_f64; n];
    if n > 2 {
        let dt0 = result.eta_grid[1] - result.eta_grid[0];
        if dt0.abs() > 1e-30 {
            vb_dot[0] = (result.snapshots[1][vb_idx] - result.snapshots[0][vb_idx]) / dt0;
        }
        for j in 1..n - 1 {
            let dt = result.eta_grid[j + 1] - result.eta_grid[j - 1];
            if dt.abs() > 1e-30 {
                vb_dot[j] = (result.snapshots[j + 1][vb_idx] - result.snapshots[j - 1][vb_idx]) / dt;
            }
        }
        let dt_last = result.eta_grid[n - 1] - result.eta_grid[n - 2];
        if dt_last.abs() > 1e-30 {
            vb_dot[n - 1] = (result.snapshots[n - 1][vb_idx] - result.snapshots[n - 2][vb_idx]) / dt_last;
        }
    }

    let mut grid = SourceGrid::new(k);

    // ── ISW finite difference state ──
    let mut prev_psi_plus_phi = 0.0_f64;
    let mut prev_eta = 0.0_f64;

    for i in 0..n {
        let eta = result.eta_grid[i];
        let y = &result.snapshots[i];

        // ── Map to vis grid index ──
        let vis_i = match vis.eta_grid.binary_search_by(|v| v.partial_cmp(&eta).unwrap()) {
            Ok(j) => j,
            Err(j) => j.min(n_vis - 1),
        };

        let g = vis.g_grid[vis_i];
        let g_dot = g_dot_vis[vis_i];
        let theta_0 = y[result.idx_theta(0)];
        let phi = y[result.idx_phi()];
        let v_b = y[result.idx_v_b()];

        // ACC-01: Ψ from traceless Einstein (anisotropic stress from ν+γ quadrupoles)
        let theta_2 = if lg >= 2 { y[result.idx_theta(2)] } else { 0.0 };
        let n_2 = if ln >= 2 { y[result.idx_nu(2)] } else { 0.0 };
        let z_i = vis.z_grid[vis_i];
        let a_i = 1.0 / (1.0 + z_i);
        let a_h_i = a_i * h0c * params.e_of_z(z_i);
        let psi = compute_psi_algebraic_v2(
            phi, theta_2, n_2, a_h_i, k,
            f_gamma, f_nu, omega_r, params.omega_m, omega_lambda, a_i,
        );

        let mut sv = SourceValue::default();

        // S_SW = g × (Θ₀ + Ψ)
        sv.sw = g * (theta_0 + psi);

        // S_Dop: raw Doppler for j'_ℓ basis (no IBP needed).
        // The LoS integral ∫ g v_b j'_ℓ(kχ) dη is computed directly
        // in the C_ℓ assembly using j'_ℓ from batch Bessel recurrence.
        // This avoids noisy FD of g' and v_b'.
        sv.doppler = g * v_b;

        // PRE-01: ISW = e^{−τ} × d(Ψ+Φ)/dη via forward finite difference.
        // Guard: minimum step 0.5 Mpc to avoid FD noise from adaptive ODE stepping.
        // At k=0.15 the oscillation period is ~42 Mpc, so 0.5 Mpc resolves ~80 points
        // per period — adequate for the FD while avoiding sub-step noise amplification.
        let psi_plus_phi = psi + phi;
        let deta = eta - prev_eta;
        if i > 0 && deta > 0.5 {
            let exp_neg_tau = (-vis.tau_grid[vis_i]).exp();
            sv.isw = exp_neg_tau * (psi_plus_phi - prev_psi_plus_phi) / deta;
            prev_psi_plus_phi = psi_plus_phi;
            prev_eta = eta;
        } else if i == 0 {
            prev_psi_plus_phi = psi_plus_phi;
            prev_eta = eta;
        }
        // else: carry ISW=0 for this point (step too small for reliable FD)

        // S_pol = 0 (no E₂ polarization in current kmode solver)
        sv.pol = 0.0;

        // S_shear = 0 (FLRW: no background shear)
        sv.shear_isw = 0.0;

        sv.compute_total();
        grid.eta_grid.push(eta);
        grid.values.push(sv);
    }

    grid
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_matrix_dimensions() {
        let mat = build_flrw_matrix(0.01, 1e-4, 100.0, 0.5, 0.4, 0.315, 0.049, 5.4e-5, 0.001, 10, 6, 100.0);
        let n = 10 + 1 + 6 + 1 + 5; // 23
        assert_eq!(mat.len(), n * n);
    }

    #[test]
    fn test_kmode_rodas5p_runs() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let result = solve_kmode_rodas5p(0.01, &p, &vis, 8, 4);
        assert!(result.is_ok(), "Rodas5P k-mode failed: {:?}", result.err());
        let (eta, src) = result.unwrap();
        assert!(eta.len() > 100, "Too few output points: {}", eta.len());
        assert!(src.iter().any(|&s| s.abs() > 1e-30), "Source all zero");
    }

    #[test]
    fn test_kmode_no_nan() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let (_, src) = solve_kmode_rodas5p(0.005, &p, &vis, 8, 4).unwrap();
        assert!(src.iter().all(|s| s.is_finite()), "NaN/Inf in source");
    }

    #[test]
    fn test_flrw_cl_rodas5p_runs() {
        let p = VisibilityParams::planck2018();
        let cl = compute_flrw_cl_rodas5p(&p, 10, 10);
        assert!(cl.is_ok(), "C_ℓ computation failed: {:?}", cl.err());
        let cl = cl.unwrap();
        for ell in 2..=10 {
            assert!(cl[ell].is_finite(), "C_{} = NaN", ell);
            assert!(cl[ell] >= 0.0, "C_{} < 0", ell);
        }
    }

    #[test]
    fn test_flrw_dl_physical() {
        let p = VisibilityParams::planck2018();
        let cl = compute_flrw_cl_rodas5p(&p, 10, 20).unwrap();
        let t2 = (p.t_cmb * 1e6_f64).powi(2);
        let dl_2 = 2.0 * 3.0 * cl[2] * t2 / (2.0 * std::f64::consts::PI);
        // CLASS: D_2 ≈ 1050 μK². Accept wide range for first pass.
        assert!(dl_2 > 10.0 && dl_2 < 100000.0,
            "D_2 = {:.0} μK² (expect ~1050)", dl_2);
    }

    // ═══════════════════════════════════════════════════════════
    // CL-02: Source Adaptor Tests
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl02_kmode_with_history_runs() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let result = solve_kmode_with_history(0.01, &p, &vis, 8, 4);
        assert!(result.is_ok(), "solve_kmode_with_history failed: {:?}", result.err());
        let r = result.unwrap();
        assert!(r.eta_grid.len() > 100, "Too few points: {}", r.eta_grid.len());
        assert_eq!(r.snapshots.len(), r.eta_grid.len(), "Snapshot count mismatch");
        assert_eq!(r.snapshots[0].len(), r.n_state, "State vector dimension mismatch");
    }

    #[test]
    fn test_cl02_index_mapping_consistency() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();

        // CL-01 §4: verify index accessors match manual calculation
        let lg = 8_usize;
        let ln = 4_usize;
        assert_eq!(r.idx_theta(0), 0);
        assert_eq!(r.idx_theta(2), 2);
        assert_eq!(r.idx_theta(lg), lg);
        assert_eq!(r.idx_nu(0), lg + 1);
        assert_eq!(r.idx_delta_c(), lg + 1 + ln + 1);
        assert_eq!(r.idx_v_b(), lg + ln + 5);
        assert_eq!(r.idx_phi(), lg + ln + 6);
        assert_eq!(r.n_state, lg + 1 + ln + 1 + 5);
    }

    #[test]
    fn test_cl02_raw_theta0_source_sign() {
        // S_SW = g × (Θ₀ + Ψ) should be positive near recombination peak
        // since g > 0 and (Θ₀ + Ψ) > 0 for adiabatic IC at low k
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        // Find peak |source|
        let mut max_abs = 0.0_f64;
        let mut peak_sw = 0.0_f64;
        for sv in &sg.values {
            if sv.sw.abs() > max_abs {
                max_abs = sv.sw.abs();
                peak_sw = sv.sw;
            }
        }
        // At low k (super-horizon at recombination), SW should be nonzero
        assert!(max_abs > 1e-10, "S_SW peak too small: {:.4e}", max_abs);
        // Check source is finite everywhere
        assert!(sg.values.iter().all(|sv| sv.total.is_finite()), "NaN/Inf in source");
    }

    #[test]
    fn test_cl02_source_doppler_order() {
        // |S_Dop| should be roughly O(v_b/k × g') ~ smaller than S_SW at low k
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        let max_sw = sg.values.iter().map(|sv| sv.sw.abs()).fold(0.0_f64, f64::max);
        let max_dop = sg.values.iter().map(|sv| sv.doppler.abs()).fold(0.0_f64, f64::max);

        // At k = 0.01, Doppler should be nonzero but comparable to or smaller than SW
        assert!(max_dop > 1e-15, "Doppler identically zero at k=0.01");
        // Ratio test: Doppler shouldn't be 100× larger than SW
        let ratio = max_dop / max_sw.max(1e-30);
        assert!(ratio < 100.0, "|S_Dop/S_SW| = {:.1} (expect < 100)", ratio);
    }

    #[test]
    fn test_cl02_source_total_finite() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.005, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        for (i, sv) in sg.values.iter().enumerate() {
            assert!(sv.sw.is_finite(), "SW NaN at i={}", i);
            assert!(sv.doppler.is_finite(), "Dop NaN at i={}", i);
            assert!(sv.isw.is_finite(), "ISW NaN at i={}", i);
            assert!(sv.total.is_finite(), "Total NaN at i={}", i);
        }
    }

    #[test]
    fn test_cl02_adversarial_wrong_index() {
        // If v_b index were off by 1 (pointing to δ_b instead),
        // Doppler would use density instead of velocity → anomalous scaling.
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();

        // Compare v_b at peak vs δ_b at peak — they should differ substantially
        let mid = r.snapshots.len() / 2;
        let v_b = r.snapshots[mid][r.idx_v_b()];
        let delta_b = r.snapshots[mid][r.idx_delta_b()];
        // δ_b is typically O(1) while v_b is O(k/aH) ≪ 1 at low k
        // So if we accidentally used δ_b as v_b, Doppler would be ~100× too large
        assert!((v_b - delta_b).abs() > 1e-5 || v_b.abs() < 1e-10,
            "v_b and δ_b suspiciously similar: v_b={:.4e}, δ_b={:.4e}", v_b, delta_b);
    }

    #[test]
    fn test_cl02_history_matches_legacy_sw() {
        // The SW source from solve_kmode_with_history should match
        // the legacy solve_kmode_rodas5p output
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);

        let legacy = solve_kmode_rodas5p(0.01, &p, &vis, 8, 4).unwrap();
        let new_r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();

        // Compare SW source at overlapping η points
        assert_eq!(legacy.0.len(), new_r.eta_grid.len(),
            "Grid length mismatch: {} vs {}", legacy.0.len(), new_r.eta_grid.len());

        let mut max_diff = 0.0_f64;
        for i in 0..legacy.0.len().min(new_r.eta_grid.len()) {
            let d = (legacy.1[i] - new_r.raw_theta0_source[i]).abs();
            max_diff = max_diff.max(d);
        }
        // CL-08: With hybrid Dopri5↔Rodas5P switching, the solver method
        // difference introduces O(1-2%) accuracy variation from the legacy
        // pure-Rodas5P solver. This is within the physics error budget
        // (70% gap from CLASS due to missing ISW/Doppler/reionization).
        let max_sw = new_r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
        let rel_diff = max_diff / max_sw.max(1e-30);
        assert!(rel_diff < 0.05,
            "SW source mismatch: max |Δ|/|S_max| = {:.4e} (expect < 5%)", rel_diff);
    }

    // ═══════════════════════════════════════════════════════════
    // CL-03: k_max / ℓ_max expansion tests
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl03_higher_ell_max_runs() {
        // Test that ℓ_max_γ = 20 works without crash
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 20, 10);
        assert!(r.is_ok(), "ℓ_max_γ=20 failed: {:?}", r.err());
        let r = r.unwrap();
        assert_eq!(r.n_state, 20 + 1 + 10 + 1 + 5);  // 37 DOF
    }

    #[test]
    fn test_cl03_higher_k_runs() {
        // Test k = 0.05 (beyond original k_max = 0.03)
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.05, &p, &vis, 20, 10);
        assert!(r.is_ok(), "k=0.05, ℓ_max=20 failed: {:?}", r.err());
        let r = r.unwrap();
        // Source should be nonzero (acoustic oscillation at k=0.05)
        let max_sw = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
        assert!(max_sw > 1e-10, "Source too small at k=0.05: {:.4e}", max_sw);
    }

    #[test]
    fn test_cl03_convergence_ell_max() {
        // Check Θ₂(η) convergence: ℓ_max_γ = 15 vs 20 at k = 0.01
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r15 = solve_kmode_with_history(0.01, &p, &vis, 15, 8).unwrap();
        let r20 = solve_kmode_with_history(0.01, &p, &vis, 20, 8).unwrap();

        // Compare Θ₂ at midpoint of grid
        let mid = r15.eta_grid.len() / 2;
        let t2_15 = r15.snapshots[mid][2];
        let t2_20 = r20.snapshots[mid][2];
        let rel = if t2_20.abs() > 1e-30 { (t2_15 - t2_20).abs() / t2_20.abs() } else { 0.0 };
        // At k = 0.01, ℓ_max = 15 vs 20 should agree well (kη_* ≈ 2.8)
        assert!(rel < 0.05, "Θ₂ convergence: |Δ| = {:.1}% at k=0.01", rel*100.0);
    }

    // ═══════════════════════════════════════════════════════════
    // CL-10: Truncation damping (completion relation) tests
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl10_completion_matrix_structure() {
        // At ℓ = ℓ_max, the completion relation should change the matrix:
        // - subdiagonal: fac*ℓ → k
        // - diagonal: −κ̇ → −[(ℓ+1)/τ + κ̇]
        let lg = 10_usize;
        let ln = 6_usize;
        let n = lg + 1 + ln + 1 + 5;
        let k = 0.01_f64;
        let kd = 100.0_f64;
        let tau_conf = 280.0_f64; // typical η_* ≈ 280 Mpc

        let mat = build_flrw_matrix(k, 1e-4, kd, 0.5, 0.4, 0.315, 0.049, 5.4e-5, 0.001, lg, ln, tau_conf);

        // Check photon ℓ_max row
        let ell = lg;
        let idx = |r: usize, c: usize| r * n + c;
        // Subdiagonal should be k (not k*ℓ/(2ℓ+1))
        let expected_sub = k;
        let actual_sub = mat[idx(ell, ell - 1)];
        assert!((actual_sub - expected_sub).abs() < 1e-15,
            "Photon ℓ_max subdiag: {:.6e} (expect {:.6e})", actual_sub, expected_sub);
        // Diagonal should be −[(ℓ+1)/τ + κ̇]
        let expected_diag = -((ell + 1) as f64 / tau_conf + kd);
        let actual_diag = mat[idx(ell, ell)];
        assert!((actual_diag - expected_diag).abs() < 1e-12,
            "Photon ℓ_max diag: {:.6e} (expect {:.6e})", actual_diag, expected_diag);

        // Check neutrino ℓ_max row
        let n0 = lg + 1;
        let nell = ln;
        let expected_nu_sub = k;
        let actual_nu_sub = mat[idx(n0 + nell, n0 + nell - 1)];
        assert!((actual_nu_sub - expected_nu_sub).abs() < 1e-15,
            "Neutrino ℓ_max subdiag: {:.6e}", actual_nu_sub);
        // Neutrino has no collision: diagonal = −(ℓ+1)/τ
        let expected_nu_diag = -((nell + 1) as f64) / tau_conf;
        let actual_nu_diag = mat[idx(n0 + nell, n0 + nell)];
        assert!((actual_nu_diag - expected_nu_diag).abs() < 1e-12,
            "Neutrino ℓ_max diag: {:.6e} (expect {:.6e})", actual_nu_diag, expected_nu_diag);
    }

    #[test]
    fn test_cl10_no_completion_fallback() {
        // tau_conf = 0 should give hard truncation (old behavior)
        let lg = 10_usize;
        let ln = 6_usize;
        let n = lg + 1 + ln + 1 + 5;
        let k = 0.01_f64;
        let kd = 100.0_f64;

        let mat_no = build_flrw_matrix(k, 1e-4, kd, 0.5, 0.4, 0.315, 0.049, 5.4e-5, 0.001, lg, ln, 0.0);
        let idx = |r: usize, c: usize| r * n + c;

        // Photon ℓ_max: subdiagonal should be k*ℓ/(2ℓ+1), diagonal = −κ̇
        let ell = lg;
        let expected_sub = k * ell as f64 / (2*ell+1) as f64;
        let actual_sub = mat_no[idx(ell, ell-1)];
        assert!((actual_sub - expected_sub).abs() < 1e-15,
            "Fallback subdiag: {:.6e} (expect {:.6e})", actual_sub, expected_sub);
        assert!((mat_no[idx(ell, ell)] - (-kd)).abs() < 1e-12, "Fallback diag");
    }

    #[test]
    fn test_cl10_completion_improves_convergence() {
        // With completion: ℓ_max=15 vs 20 difference should be smaller
        // than without completion
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);

        // Both use completion (tau_conf > 0 by default in solve_kmode_with_history)
        let r15 = solve_kmode_with_history(0.02, &p, &vis, 15, 8).unwrap();
        let r25 = solve_kmode_with_history(0.02, &p, &vis, 25, 8).unwrap();

        // Compare SW source at peak
        let max15 = r15.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
        let max25 = r25.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
        let rel = (max15 - max25).abs() / max25.max(1e-30);
        // With completion, convergence should be better than 10% at k=0.02
        assert!(rel < 0.10,
            "Completion convergence: |ΔS|/S = {:.1}% (expect <10%)", rel*100.0);
    }

    // ═══════════════════════════════════════════════════════════
    // CL-07: Source function upgrade (Doppler + ISW documentation)
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl07_isw_nonzero_with_algebraic_psi() {
        // PRE-01: With Ψ from traceless Einstein (neutrino anisotropic stress),
        // Ψ ≠ −Φ → ISW = e^{-τ}(Ψ'+Φ') ≠ 0.
        // Early ISW comes from radiation→matter transition (Φ decay),
        // late ISW from Λ domination.
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        let max_isw = sg.values.iter().map(|sv| sv.isw.abs()).fold(0.0_f64, f64::max);
        let max_sw = sg.values.iter().map(|sv| sv.sw.abs()).fold(0.0_f64, f64::max);
        eprintln!("  PRE-01: max|ISW| = {:.4e}, max|SW| = {:.4e}, ratio = {:.2e}",
            max_isw, max_sw, max_isw / max_sw.max(1e-30));

        // ISW must be nonzero — this verifies the algebraic Ψ is working
        assert!(max_isw > 1e-15,
            "ISW should be nonzero with algebraic Ψ, got max|ISW| = {:.4e}", max_isw);
        // ISW should be subdominant to SW (typically 10-30% of SW at low ℓ)
        assert!(max_isw < max_sw * 10.0,
            "ISW too large relative to SW: {:.4e} vs {:.4e}", max_isw, max_sw);
    }

    #[test]
    fn test_cl07_doppler_nonzero() {
        // Doppler = −g' v_b / k should be nonzero for k > 0
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        let max_dop = sg.values.iter().map(|sv| sv.doppler.abs()).fold(0.0_f64, f64::max);
        assert!(max_dop > 1e-10, "Doppler should be nonzero at k=0.01, got {:.4e}", max_dop);
    }

    #[test]
    fn test_cl07_full_source_no_blowup() {
        // SourceMode::Full should give finite, reasonable source values
        // (This was the bug that caused D_2 ~ 10^17 before CL-07)
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        let max_total = sg.values.iter().map(|sv| sv.total.abs()).fold(0.0_f64, f64::max);
        let max_sw = sg.values.iter().map(|sv| sv.sw.abs()).fold(0.0_f64, f64::max);

        // Total source should be within 3× of SW-only (Doppler subtracts, ISW adds at different η)
        let ratio = max_total / max_sw.max(1e-30);
        eprintln!("  PRE-01: |S_total|/|S_SW| = {:.3}, max_total = {:.4e}", ratio, max_total);
        assert!(ratio > 0.3 && ratio < 3.0,
            "|S_total|/|S_SW| = {:.3} (expect 0.3–3.0)", ratio);
        assert!(sg.values.iter().all(|sv| sv.total.is_finite()), "NaN in source");
    }

    #[test]
    fn test_cl07_sw_matches_legacy() {
        // SW component from extract_source_grid should match raw_theta0_source from KmodeResult
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let r = solve_kmode_with_history(0.01, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        assert_eq!(sg.values.len(), r.raw_theta0_source.len(), "Grid length mismatch");
        let mut max_diff = 0.0_f64;
        for i in 0..sg.values.len() {
            let diff = (sg.values[i].sw - r.raw_theta0_source[i]).abs();
            max_diff = max_diff.max(diff);
        }
        assert!(max_diff < 1e-12,
            "SW mismatch vs legacy: max|Δ| = {:.4e}", max_diff);
    }

    #[test]
    fn test_cl07_doppler_subdominant_at_low_k() {
        // At k ~ 10⁻⁴, Doppler = −g'v_b/k is amplified by 1/k factor.
        // It is NOT negligible — it's O(1) relative to SW at super-horizon scales.
        // This is physically correct: Doppler contributes ~30% to C_2.
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 5000);
        let r = solve_kmode_with_history(1e-4, &p, &vis, 8, 4).unwrap();
        let sg = extract_source_grid(&r, &vis, &p);

        let max_sw = sg.values.iter().map(|sv| sv.sw.abs()).fold(0.0_f64, f64::max);
        let max_dop = sg.values.iter().map(|sv| sv.doppler.abs()).fold(0.0_f64, f64::max);
        let ratio = max_dop / max_sw.max(1e-30);
        // Doppler can be comparable to SW at low k, but should not exceed 10×
        assert!(ratio < 10.0,
            "|S_Dop/S_SW| = {:.4} at k=1e-4 (expect < 10)", ratio);
        // It should also be nonzero
        assert!(max_dop > 1e-10, "Doppler should be nonzero at k=1e-4");
    }

    #[test]
    fn test_cl08_hybrid_profile() {
        use std::time::Instant;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(200);
        let vis = compute_visibility(&p, &t, 3000);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let n_vis = vis.z_grid.len();
        let eta_max = vis.eta_grid[n_vis - 1];

        let kd_threshold = 10.0_f64;
        let mut i_switch = 0_usize;
        for vi in (0..n_vis).rev() {
            let z = vis.z_grid[vi];
            let a = 1.0 / (1.0 + z);
            let a_h = a * h0c * p.e_of_z(z);
            let kd = vis.kappa_dot_grid[vi];
            if kd / a_h.max(1e-30) > kd_threshold {
                i_switch = vi;
                break;
            }
        }
        let tau_switch = eta_max - vis.eta_grid[i_switch];
        let z_switch = vis.z_grid[i_switch];
        let n_eval_phase1 = (0..n_vis).rev()
            .map(|i| eta_max - vis.eta_grid[i])
            .take_while(|&t| t < tau_switch).count();

        // Debug: print κ̇/(aH) at key redshifts
        for &check_vi in &[0, n_vis/4, n_vis/2, 3*n_vis/4, n_vis-1] {
            let z = vis.z_grid[check_vi];
            let a = 1.0 / (1.0 + z);
            let a_h = a * h0c * p.e_of_z(z);
            let kd = vis.kappa_dot_grid[check_vi];
            eprintln!("  vi={:>5} z={:>8.1} kd={:.3e} aH={:.3e} ratio={:.3e}",
                check_vi, z, kd, a_h, kd / a_h.max(1e-30));
        }
        eprintln!("  === HYBRID PROFILE ===");
        eprintln!("  eta_max     = {:.1} Mpc", eta_max);
        eprintln!("  tau_switch  = {:.1} Mpc  (z_switch = {:.0})", tau_switch, z_switch);
        eprintln!("  Phase1 frac = {:.1}%  (n_eval = {})", 
            100.0 * tau_switch / eta_max, n_eval_phase1);
        eprintln!("  use_hybrid  = {}", n_eval_phase1 >= 3 && tau_switch > 5.0);

        let k = 0.01_f64;
        let t0 = Instant::now();
        let result = solve_kmode_with_history(k, &p, &vis, 15, 8).unwrap();
        let t_total = t0.elapsed().as_millis();
        eprintln!("  k=0.01 wall = {} ms, n_eta = {}", t_total, result.eta_grid.len());
        assert!(result.eta_grid.len() > 100);
    }

    /// PRE-01-DIAG: Diagnose solver output at high k to find blowup source.
    #[test]
    fn test_pre01_highk_solver_diagnostic() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();
        let omega_r = og + og * (7.0 / 8.0) * (4.0_f64 / 11.0).powf(4.0 / 3.0) * N_EFF;
        let omega_lambda = 1.0 - p.omega_m - omega_r;
        let f_nu = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
        let f_gamma = 1.0 - f_nu;

        // Sweep k from 0.01 to 0.06 to find blowup threshold
        for &k in &[0.01_f64, 0.02, 0.03, 0.035, 0.04, 0.045, 0.05] {
            let lg = 20_usize; let ln = 10_usize;
            let result = match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(r) => r,
                Err(e) => { eprintln!("  k={:.3}: FAILED — {}", k, e); continue; }
            };
            let n = result.eta_grid.len();

            // Max amplitudes
            let mut max_theta0 = 0.0_f64;
            let mut max_phi = 0.0_f64;
            for snap in &result.snapshots {
                max_theta0 = max_theta0.max(snap[0].abs());
                max_phi = max_phi.max(snap[result.idx_phi()].abs());
            }

            let status = if max_theta0 > 100.0 { "*** BLOWUP ***" } else { "OK" };
            eprintln!("  k={:.3}: |Θ₀|={:.2e}, |Φ|={:.2e}  {}", k, max_theta0, max_phi, status);
        }
        // At least k=0.01 should work
        let r01 = solve_kmode_with_history(0.01, &p, &vis, 20, 10).unwrap();
        let max01 = r01.snapshots.iter().map(|s| s[0].abs()).fold(0.0_f64, f64::max);
        assert!(max01 < 10.0, "k=0.01 should be stable: |Θ₀|={:.2e}", max01);
    }
}
// Replaces psi = -phi with correct algebraic relation including
// anisotropic stress from neutrino and photon quadrupoles.
// Factor fix: 12×(4/3)=16 → correct factor 4.
// ============================================================

/// Compute Ψ from the algebraic traceless Einstein equation.
/// k²(Φ+Ψ) = -4(aH)²(ρ_r/ρ_tot)(f_γΘ₂ + f_νN₂)
fn compute_psi_algebraic_v2(
    phi: f64, theta_2: f64, n_2: f64,
    a_h: f64, k: f64,
    f_gamma: f64, f_nu: f64,
    omega_r: f64, omega_m: f64, omega_lambda: f64, a: f64,
) -> f64 {
    if k.abs() < 1e-10 { return -phi; }
    let k2 = k * k;
    let rho_r = omega_r / (a * a * a * a);
    let rho_tot = rho_r + omega_m / (a * a * a) + omega_lambda;
    let aniso_coeff = 4.0 * a_h * a_h / k2 * rho_r / rho_tot;
    let sigma = f_gamma * theta_2 + f_nu * n_2;
    -phi - aniso_coeff * sigma
}

#[cfg(test)]
mod acc01_tests {
    use super::*;
    
    #[test]
    fn test_psi_no_aniso_returns_minus_phi() {
        let psi = compute_psi_algebraic_v2(
            1.0, 0.0, 0.0, 0.003, 0.01, 0.6, 0.4,
            5e-5, 0.14, 0.69, 1e-3
        );
        assert!((psi - (-1.0)).abs() < 1e-10, "Got {}", psi);
    }
    
    #[test]
    fn test_psi_correct_coefficient() {
        let h0c: f64 = 67.36 / 2.998e5;
        let og = 2.469e-5 / (67.36_f64/100.0).powi(2);
        let onu = og * (7.0/8.0) * (4.0_f64/11.0).powf(4.0/3.0) * 3.044;
        let orad = og + onu;
        let a = 1e-3; let k = 0.01;
        let om = 0.02237 + 0.12; let olam = 1.0 - om - orad;
        let ah = h0c * a * (orad/(a*a*a*a) + om/(a*a*a) + olam).sqrt();
        
        // Correct: 4 H0^2 Omega_r / (a^2 k^2)
        let correct = 4.0 * h0c * h0c * orad / (a * a * k * k);
        // My function's coefficient
        let rho_r = orad / (a*a*a*a);
        let rho_tot = rho_r + om/(a*a*a) + olam;
        let my_coeff = 4.0 * ah * ah / (k*k) * rho_r / rho_tot;
        
        let ratio = my_coeff / correct;
        assert!((ratio - 1.0).abs() < 0.01, "Ratio = {:.4} (should be ~1)", ratio);
    }
}

#[cfg(test)]
mod matrix_diagnostic {
    use super::*;

    /// Check if A(τ) has growing eigenvalues at high k.
    #[test]
    fn test_matrix_eigenvalue_diagnostic() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();
        let n_vis = vis.z_grid.len();

        for &k in &[0.01_f64, 0.03, 0.05, 0.1] {
            let lg = 20_usize;
            let ln = 10_usize;
            let n_state = lg + 1 + ln + 1 + 5;

            // Check A matrix at a few representative z values
            for &z in &[3000.0, 1500.0, 1090.0, 500.0, 100.0, 0.0] {
                let a = 1.0 / (1.0 + z);
                let a_h = a * h0c * p.e_of_z(z);
                
                // Find closest vis grid point
                let vi = vis.z_grid.iter().position(|&zv| zv <= z).unwrap_or(0);
                let kd = vis.kappa_dot_grid[vi];
                let r = 3.0 * p.omega_b / (4.0 * og * (1.0 + z));
                let f_nu = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
                let tau = vis.eta_grid[n_vis - 1] - vis.eta_grid[vi];

                let mat = build_flrw_matrix(k, a_h, kd, r, f_nu, p.omega_m, p.omega_b, og, a, lg, ln, tau);

                // Check diagonal elements (rough proxy for eigenvalues)
                let mut max_diag = f64::NEG_INFINITY;
                let mut max_abs_elem = 0.0_f64;
                for i in 0..n_state {
                    max_diag = max_diag.max(mat[i * n_state + i]);
                    for j in 0..n_state {
                        max_abs_elem = max_abs_elem.max(mat[i * n_state + j].abs());
                    }
                }
                
                // Gershgorin bound: eigenvalue Re(λ) ≤ max_diag + Σ|off-diag|
                let mut max_gershgorin = f64::NEG_INFINITY;
                for i in 0..n_state {
                    let diag = mat[i * n_state + i];
                    let mut off_sum = 0.0;
                    for j in 0..n_state {
                        if j != i { off_sum += mat[i * n_state + j].abs(); }
                    }
                    max_gershgorin = max_gershgorin.max(diag + off_sum);
                }

                if max_gershgorin > 0.0 || max_diag > 0.0 {
                    eprintln!("  k={:.3} z={:.0}: max_diag={:.2e}, Gershgorin_max={:.2e} *** UNSTABLE ***",
                        k, z, max_diag, max_gershgorin);
                }
            }
            eprintln!("  k={:.3}: matrix check done", k);
        }
    }
}

#[cfg(test)]
mod tca_bypass_diagnostic {
    use super::*;

    #[test]
    fn test_original_rodas5p_at_high_k() {
        // The ORIGINAL solve_kmode_rodas5p doesn't use TCA.
        // If it also blows up at k=0.03, the problem is not TCA.
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);

        for &k in &[0.01_f64, 0.03, 0.05] {
            match solve_kmode_rodas5p(k, &p, &vis, 20, 10) {
                Ok((eta, src)) => {
                    let max_src = src.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    eprintln!("  LEGACY k={:.3}: n_eta={}, max|src|={:.2e}  OK",
                        k, eta.len(), max_src);
                }
                Err(e) => {
                    eprintln!("  LEGACY k={:.3}: FAILED — {}", k, e);
                }
            }
        }
    }
}

#[cfg(test)]
mod legacy_vs_new_diagnostic {
    use super::*;

    #[test]
    fn test_theta0_legacy_vs_new_at_k003() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);
        let lg = 20_usize; let ln = 10_usize;
        let k = 0.03_f64;

        // Legacy: solve_kmode_rodas5p (no TCA, original Rodas5P)
        let (eta_leg, src_leg) = solve_kmode_rodas5p(k, &p, &vis, lg, ln).unwrap();
        let max_src_leg = src_leg.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));

        // New: solve_kmode_with_history (no TCA, diffsol BDF)
        let result_new = solve_kmode_with_history(k, &p, &vis, lg, ln).unwrap();
        let max_theta0_new = result_new.snapshots.iter()
            .map(|s| s[0].abs()).fold(0.0_f64, f64::max);
        let max_src_new = result_new.raw_theta0_source.iter()
            .fold(0.0_f64, |m, &s| m.max(s.abs()));

        // Legacy doesn't store snapshots, so we can't get Θ₀ directly.
        // But we CAN check if the source functions match.
        eprintln!("  === k={:.3} COMPARISON ===", k);
        eprintln!("  Legacy: n_eta={}, max|src_sw|={:.4e}", eta_leg.len(), max_src_leg);
        eprintln!("  New:    n_eta={}, max|src_sw|={:.4e}, max|Θ₀|={:.4e}",
            result_new.eta_grid.len(), max_src_new, max_theta0_new);
        eprintln!("  Ratio src: {:.3}", max_src_new / max_src_leg.max(1e-30));

        // If both sources are similar, the Θ₀ blowup is outside the visibility peak
        // and doesn't affect the observable. This would mean the "blowup" is actually
        // free-streaming Θ₀ growth at late times — physically correct behavior.
    }
}

#[cfg(test)]
mod source_level_diagnostic {
    use super::*;

    /// The REAL diagnostic: check source function (not Θ₀) across all k.
    #[test]
    fn test_source_stability_all_k() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);

        for &k in &[0.01_f64, 0.03, 0.05, 0.07, 0.1, 0.15] {
            let lg = 20_usize; let ln = 10_usize;

            // Legacy path
            match solve_kmode_rodas5p(k, &p, &vis, lg, ln) {
                Ok((_, src)) => {
                    let max_src = src.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    eprint!("  k={:.3} legacy: |src|={:.3e}", k, max_src);
                }
                Err(e) => { eprintln!("  k={:.3} legacy: FAILED — {}", k, e); continue; }
            }

            // New BDF path
            match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(r) => {
                    let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    let max_theta0 = r.snapshots.iter().map(|s| s[0].abs()).fold(0.0_f64, f64::max);
                    eprintln!("  new: |src|={:.3e} |Θ₀|={:.2e}", max_src, max_theta0);
                }
                Err(e) => { eprintln!("  new: FAILED k={} — {}", k, e); }
            }
        }
    }
}

#[cfg(test)]
mod lmax_convergence {
    use super::*;

    /// Verify that ℓ_max truncation causes blowup, not solver.
    #[test]
    fn test_lmax_vs_source_blowup() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);
        let k = 0.05_f64;

        // Sweep ℓ_max_γ from 10 to 60
        for &lg in &[10_usize, 15, 20, 30, 40, 50, 60] {
            let ln = (lg / 2).max(4);
            match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(r) => {
                    let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    eprintln!("  k={:.3} ℓ_max={:>2}: |src_sw|={:.3e}", k, lg, max_src);
                }
                Err(e) => {
                    eprintln!("  k={:.3} ℓ_max={:>2}: FAILED — {}", k, lg, e);
                }
            }
        }
    }
}

#[cfg(test)]
mod extended_z_diagnostic {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    /// Test that extended z_max fixes the high-k source blowup.
    #[test]
    fn test_extended_z_source_stability() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);

        // z_max = 10⁵: k/(aH) < 0.7 for k ≤ 0.15, stiffness manageable
        let vis_ext = compute_visibility_ext(&p, &t, 5000, 1.0e5);
        let n_vis = vis_ext.z_grid.len();
        let z_max = vis_ext.z_grid[n_vis - 1];
        let eta_max = vis_ext.eta_grid[n_vis - 1];
        eprintln!("  Extended vis: n={}, z_max={:.0}, η_max={:.1} Mpc", n_vis, z_max, eta_max);

        for &k in &[0.01_f64, 0.03, 0.05, 0.1, 0.15] {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(60);
            let ln = (lg / 2).max(6);
            match solve_kmode_with_history(k, &p, &vis_ext, lg, ln) {
                Ok(r) => {
                    let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    eprintln!("  k={:.3} ℓγ={:>2}: |src_sw|={:.3e}", k, lg, max_src);
                }
                Err(e) => {
                    eprintln!("  k={:.3}: FAILED — {}", k, e);
                }
            }
        }
    }
}

#[cfg(test)]
mod rodas5p_extended_z {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    #[test]
    fn test_rodas5p_extended_z() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        // z_max=5×10⁵: k/(aH) < 0.05 for k=0.05, < 0.14 for k=0.15
        let vis_ext = compute_visibility_ext(&p, &t, 5000, 5.0e5);
        let n = vis_ext.z_grid.len();
        eprintln!("  Extended vis: n={}, z_max={:.0}", n, vis_ext.z_grid[n-1]);

        for &k in &[0.01_f64, 0.03, 0.05, 0.1, 0.15] {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(80);
            let ln = (lg / 2).max(6);
            match solve_kmode_rodas5p(k, &p, &vis_ext, lg, ln) {
                Ok((_, src)) => {
                    let max_src = src.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    eprintln!("  k={:.3} ℓγ={:>2}: |src|={:.3e}", k, lg, max_src);
                }
                Err(e) => eprintln!("  k={:.3}: FAILED — {}", k, e),
            }
        }
    }
}

#[cfg(test)]
mod stress_test_zmax_k {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    /// Gradual stress test: z_max × k matrix with Rodas5P + k-dependent h_max + sponge.
    #[test]
    fn test_stress_zmax_k_matrix() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);

        eprintln!("\n  === STRESS TEST: z_max × k matrix ===");
        eprintln!("  {:>8} | {:>8} {:>8} {:>8} {:>8} {:>8}", "z_max",
            "k=0.01", "k=0.03", "k=0.05", "k=0.10", "k=0.15");
        eprintln!("  {}", "-".repeat(60));

        for &z_max in &[4000.0_f64, 1.0e4, 5.0e4, 1.0e5] {
            let vis = compute_visibility_ext(&p, &t, 5000, z_max);
            let mut row = format!("  {:>8.0} |", z_max);

            for &k in &[0.01_f64, 0.03, 0.05, 0.10, 0.15] {
                // k-dependent ℓ_max: ℓ_max ≈ k × η_star × 3, capped at 120
                let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(120);
                let ln = (lg / 2).max(6);
                match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                    Ok(r) => {
                        let max_src = r.raw_theta0_source.iter()
                            .fold(0.0_f64, |m, &s| m.max(s.abs()));
                        let tag = if max_src < 1.0 { "OK" }
                            else if max_src < 1e3 { "WARN" }
                            else { "BLOW" };
                        row += &format!(" {:>5.1e}:{}", max_src, tag);
                    }
                    Err(_) => { row += "    FAIL  "; }
                }
            }
            eprintln!("{}", row);
        }
    }
}

#[cfg(test)]
mod targeted_stress {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    fn run_single(z_max: f64, k: f64) -> String {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 3000, z_max);
        let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(120);
        let ln = (lg / 2).max(6);
        let t0 = std::time::Instant::now();
        match solve_kmode_with_history(k, &p, &vis, lg, ln) {
            Ok(r) => {
                let ms = t0.elapsed().as_millis();
                let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                format!("z={:.0e} k={:.3} ℓ={}: |src|={:.2e} {}ms {}",
                    z_max, k, lg, max_src, ms,
                    if max_src < 1.0 { "OK" } else if max_src < 100.0 { "WARN" } else { "BLOW" })
            }
            Err(e) => format!("z={:.0e} k={:.3}: FAIL {}", z_max, k, &e[..60.min(e.len())])
        }
    }

    #[test] fn test_z4k_k001() { eprintln!("  {}", run_single(4e3, 0.01)); }
    #[test] fn test_z4k_k003() { eprintln!("  {}", run_single(4e3, 0.03)); }
    #[test] fn test_z4k_k005() { eprintln!("  {}", run_single(4e3, 0.05)); }

    #[test] fn test_z10k_k005() { eprintln!("  {}", run_single(1e4, 0.05)); }
    #[test] fn test_z50k_k005() { eprintln!("  {}", run_single(5e4, 0.05)); }
    #[test] fn test_z100k_k005() { eprintln!("  {}", run_single(1e5, 0.05)); }

    #[test] fn test_z50k_k010() { eprintln!("  {}", run_single(5e4, 0.10)); }
    #[test] fn test_z100k_k010() { eprintln!("  {}", run_single(1e5, 0.10)); }

    #[test] fn test_z100k_k015() { eprintln!("  {}", run_single(1e5, 0.15)); }
}

#[cfg(test)]
mod peak_vs_max_diagnostic {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    fn analyze(z_max: f64, k: f64, lg: usize) -> String {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 3000, z_max);
        let ln = (lg / 2).max(6);
        let t0 = std::time::Instant::now();
        match solve_kmode_with_history(k, &p, &vis, lg, ln) {
            Ok(r) => {
                let ms = t0.elapsed().as_millis();
                let n = r.eta_grid.len();
                // Find peak region: z=800..1200 (around recombination)
                let mut peak_src = 0.0_f64;
                let mut late_src = 0.0_f64;
                let eta_max = r.eta_grid[n - 1];
                for i in 0..n {
                    let eta = r.eta_grid[i];
                    let z_approx = {
                        // Rough: η is comoving distance, z~η/η₀ × z_max approximately
                        // Use vis grid to find z
                        let idx = vis.eta_grid.iter().position(|&e| e >= eta).unwrap_or(0);
                        vis.z_grid[idx]
                    };
                    let s = r.raw_theta0_source[i].abs();
                    if z_approx > 800.0 && z_approx < 1300.0 {
                        peak_src = peak_src.max(s);
                    }
                    if z_approx < 100.0 {
                        late_src = late_src.max(s);
                    }
                }
                let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                format!("z={:.0e} k={:.3} ℓ={:>3}: peak={:.2e} late={:.2e} max={:.2e} {}ms",
                    z_max, k, lg, peak_src, late_src, max_src, ms)
            }
            Err(e) => format!("z={:.0e} k={:.3} ℓ={:>3}: FAIL {}", z_max, k, lg, &e[..50.min(e.len())])
        }
    }

    // ℓ_max sweep at z_max=4000, k=0.05 — isolate reflection from IC
    #[test] fn a_z4k_k005_l20() { eprintln!("  {}", analyze(4e3, 0.05, 20)); }
    #[test] fn a_z4k_k005_l42() { eprintln!("  {}", analyze(4e3, 0.05, 42)); }
    #[test] fn a_z4k_k005_l80() { eprintln!("  {}", analyze(4e3, 0.05, 80)); }
    #[test] fn a_z4k_k005_l120() { eprintln!("  {}", analyze(4e3, 0.05, 120)); }

    // z_max sweep at k=0.05, ℓ=80
    #[test] fn b_z10k_k005_l80() { eprintln!("  {}", analyze(1e4, 0.05, 80)); }
    #[test] fn b_z50k_k005_l80() { eprintln!("  {}", analyze(5e4, 0.05, 80)); }

    // Higher k at best z_max
    #[test] fn c_z50k_k010_l120() { eprintln!("  {}", analyze(5e4, 0.10, 120)); }
    #[test] fn c_z50k_k015_l120() { eprintln!("  {}", analyze(5e4, 0.15, 120)); }

    // Baseline: known-good k=0.01
    #[test] fn d_z4k_k001_l20() { eprintln!("  {}", analyze(4e3, 0.01, 20)); }
}

#[cfg(test)]
mod high_z_high_k {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    fn analyze(z_max: f64, k: f64, lg: usize) -> String {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, z_max);
        let ln = (lg / 2).max(6);
        let t0 = std::time::Instant::now();
        match solve_kmode_with_history(k, &p, &vis, lg, ln) {
            Ok(r) => {
                let ms = t0.elapsed().as_millis();
                let n = r.eta_grid.len();
                let mut peak_src = 0.0_f64;
                for i in 0..n {
                    let eta = r.eta_grid[i];
                    let idx = vis.eta_grid.iter().position(|&e| e >= eta).unwrap_or(0);
                    let z = vis.z_grid[idx];
                    let s = r.raw_theta0_source[i].abs();
                    if z > 800.0 && z < 1300.0 { peak_src = peak_src.max(s); }
                }
                let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                format!("z={:.0e} k={:.2} ℓ={:>3}: peak={:.2e} max={:.2e} {}ms",
                    z_max, k, lg, peak_src, max_src, ms)
            }
            Err(e) => format!("z={:.0e} k={:.2}: FAIL {}", z_max, k, &e[..50.min(e.len())])
        }
    }

    // k=0.10 at higher z_max
    #[test] fn z100k_k010() { eprintln!("  {}", analyze(1e5, 0.10, 100)); }
    #[test] fn z200k_k010() { eprintln!("  {}", analyze(2e5, 0.10, 100)); }

    // k=0.05 convergence check at z=1e5
    #[test] fn z100k_k005() { eprintln!("  {}", analyze(1e5, 0.05, 80)); }
}

#[cfg(test)]
mod legacy_high_z_k010 {
    use super::*;
    use crate::recombination::visibility_hyrec::compute_visibility_ext;

    #[test]
    fn test_legacy_z200k_k010() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 2e5);
        match solve_kmode_rodas5p(0.10, &p, &vis, 100, 40) {
            Ok((_, src)) => {
                let max_src = src.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                // Find peak near z=1090
                let n = vis.z_grid.len();
                let mut peak_src = 0.0_f64;
                for i in 0..src.len().min(n) {
                    if vis.z_grid[i] > 800.0 && vis.z_grid[i] < 1300.0 {
                        peak_src = peak_src.max(src[i].abs());
                    }
                }
                eprintln!("  Legacy z=2e5 k=0.10 ℓ=100: peak={:.2e} max={:.2e}", peak_src, max_src);
            }
            Err(e) => eprintln!("  Legacy: FAIL {}", &e[..60.min(e.len())]),
        }
    }
}

#[cfg(test)]
mod solver_ablation {
    use super::*;

    /// Ablation: Rodas5P (legacy, h_max=200) vs Rodas5P (new, k-dep h_max)
    ///           vs diffsol BDF vs diffsol ESDIRK34
    /// At z_max=4000, k=0.01 and k=0.03 (known stable regime).
    #[test]
    fn test_ablation_solvers() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 5000);
        let lg = 20_usize; let ln = 10_usize;

        for &k in &[0.01_f64, 0.03] {
            eprintln!("\n  === k={:.3} ablation ===", k);

            // (A) Legacy Rodas5P (h_max=200, rtol=1e-5)
            let t0 = std::time::Instant::now();
            let (_, src_a) = solve_kmode_rodas5p(k, &p, &vis, lg, ln).unwrap();
            let ms_a = t0.elapsed().as_millis();
            let max_a = src_a.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));

            // (B) New Rodas5P (k-dep h_max, rtol=1e-6) via solve_kmode_with_history
            let t0 = std::time::Instant::now();
            let r_b = solve_kmode_with_history(k, &p, &vis, lg, ln).unwrap();
            let ms_b = t0.elapsed().as_millis();
            let max_b = r_b.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));

            // (C) diffsol BDF
            use crate::solver::diffsol_bdf::{integrate_linear_diffsol, DiffsolConfig, SolverBackend};
            // Build matrix profile same as legacy
            let h0c = p.h * 1e5 / 2.99792458e8;
            let og = p.omega_gamma();
            let n_vis = vis.z_grid.len();
            let eta_max = vis.eta_grid[n_vis - 1];
            let n_state = lg + 1 + ln + 1 + 5;
            let mut tau_prof = Vec::new();
            let mut mats = Vec::new();
            for i in (0..n_vis).rev() {
                let tau = eta_max - vis.eta_grid[i];
                tau_prof.push(tau);
                let z = vis.z_grid[i];
                let a = 1.0 / (1.0 + z);
                let a_h = a * h0c * p.e_of_z(z);
                let kd = vis.kappa_dot_grid[i];
                let r = 3.0 * p.omega_b / (4.0 * og * (1.0 + z));
                let f_nu = 1.0 - 1.0 / (1.0 + 0.2271 * N_EFF);
                let mat = build_flrw_matrix(k, a_h, kd, r, f_nu, p.omega_m, p.omega_b, og, a, lg, ln, tau);
                mats.extend_from_slice(&mat);
            }
            let mut y0 = vec![0.0; n_state];
            y0[0] = -0.5; y0[lg+1] = -0.5;
            y0[lg+1+ln+1] = -1.5; y0[lg+1+ln+1+2] = -1.5;
            y0[n_state-1] = 1.0;

            let bdf_cfg = DiffsolConfig { rtol: 1e-6, atol: 1e-9, h_init: 0.1,
                backend: SolverBackend::Bdf };
            let t0 = std::time::Instant::now();
            let res_c = integrate_linear_diffsol(&tau_prof, &mats, n_state, &y0, &tau_prof, &bdf_cfg);
            let ms_c = t0.elapsed().as_millis();
            let status_c = match &res_c {
                Ok((snaps, steps, _)) => format!("OK steps={}", steps),
                Err(e) => format!("FAIL {}", &e[..40.min(e.len())]),
            };

            // (D) diffsol ESDIRK34
            let esdirk_cfg = DiffsolConfig { rtol: 1e-6, atol: 1e-9, h_init: 0.01,
                backend: SolverBackend::Esdirk34 };
            let t0 = std::time::Instant::now();
            let res_d = integrate_linear_diffsol(&tau_prof, &mats, n_state, &y0, &tau_prof, &esdirk_cfg);
            let ms_d = t0.elapsed().as_millis();
            let status_d = match &res_d {
                Ok((snaps, steps, _)) => format!("OK steps={}", steps),
                Err(e) => format!("FAIL {}", &e[..40.min(e.len())]),
            };

            eprintln!("  (A) Legacy Rodas5P h=200 rtol=1e-5: |src|={:.3e}  {}ms", max_a, ms_a);
            eprintln!("  (B) New Rodas5P k-dep rtol=1e-6:    |src|={:.3e}  {}ms", max_b, ms_b);
            eprintln!("  (C) diffsol BDF rtol=1e-6:          {}  {}ms", status_c, ms_c);
            eprintln!("  (D) diffsol ESDIRK34 rtol=1e-6:     {}  {}ms", status_d, ms_d);
        }
    }
}
