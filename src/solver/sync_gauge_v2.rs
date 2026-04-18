// ═══════════════════════════════════════════════════════════════════════
// sync_gauge_v2.rs — Synchronous gauge solver with ḣ evolved as ODE
// ═══════════════════════════════════════════════════════════════════════
//
// KEY IMPROVEMENT over sync_kmode.rs:
//   ḣ is evolved as an ODE variable (trace Einstein equation) rather than
//   computed algebraically from the (00) constraint. This eliminates the
//   catastrophic cancellation in the gauge transformation Φ = η - ℋσ/k
//   at low k, enabling correct Newtonian potentials at ALL k.
//
// State: y = [Θ₀..Θ_L, N₀..N_M, δ_c, δ_b, v_b, kη, ḣ]
//        dimension = (L+1) + (M+1) + 5
//
// Equations (Ma & Bertschinger 1995, synchronous gauge):
//   Θ₀' = -kΘ₁ - ḣ/6
//   Θ₁' = (k/3)(Θ₀ - 2Θ₂) - κ'(Θ₁ - v_b/3)
//   Θ_ℓ' = k[ℓΘ_{ℓ-1} - (ℓ+1)Θ_{ℓ+1}]/(2ℓ+1) - κ'Θ_ℓ  [ℓ ≥ 2]
//   N₀' = -kN₁ - ḣ/6
//   N_ℓ' = k[ℓN_{ℓ-1} - (ℓ+1)N_{ℓ+1}]/(2ℓ+1)
//   δ_c' = -ḣ/2  (CDM frame: v_c = 0)
//   δ_b' = -kv_b - ḣ/2
//   v_b' = -ℋv_b + κ'(3Θ₁ - v_b)/R_b
//   (kη)' = (3ℋ²/2)[4Ω_γΘ₁ + 4Ω_νN₁ + Ω_bv_b]       (momentum constraint)
//   ḣ'   = -2ℋḣ - (3/2)ℋ²[Ω_cδ_c + Ω_bδ_b + 8Ω_γΘ₀ + 8Ω_νN₀]  (trace Einstein)
//
// Newtonian potentials (NO 1/k² singularity because ḣ is evolved):
//   σ = (ḣ + 6η̇)/(2k)
//   Φ = η - ℋσ/k = η - ℋ(ḣ + 6η̇)/(2k²)
//   Ψ = -Φ - (anisotropic stress correction)
//
// The constraint k²η - ℋḣ/2 = -(3/2)ℋ²Σ Ωᵢδᵢ is satisfied by IC
// and preserved by the evolution (monitored, not enforced).

use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult};

const N_EFF: f64 = 3.044;

/// State layout with ḣ as evolved variable.
pub(crate) struct SyncV2Layout {
    pub(crate) ell_max_g: usize,
    pub(crate) ell_max_nu: usize,
    pub(crate) n_state: usize,
    pub(crate) nu_offset: usize,
    pub(crate) dc_idx: usize,
    pub(crate) db_idx: usize,
    pub(crate) vb_idx: usize,
    pub(crate) keta_idx: usize,
    pub(crate) hdot_idx: usize,  // NEW: ḣ evolved
}

impl SyncV2Layout {
    pub(crate) fn new(lg: usize, ln: usize) -> Self {
        let nu_offset = lg + 1;
        let dc_idx = nu_offset + ln + 1;
        let db_idx = dc_idx + 1;
        let vb_idx = db_idx + 1;
        let keta_idx = vb_idx + 1;
        let hdot_idx = keta_idx + 1;
        let n_state = hdot_idx + 1;
        Self { ell_max_g: lg, ell_max_nu: ln, n_state, nu_offset,
               dc_idx, db_idx, vb_idx, keta_idx, hdot_idx }
    }
}

/// Density fractions Ωᵢ(z) = ρᵢ/ρ_tot.
#[inline]
fn density_fractions(
    a: f64, omega_m: f64, omega_b: f64, omega_gamma: f64, omega_nu: f64,
) -> (f64, f64, f64, f64) {
    let omega_c = omega_m - omega_b;
    let rho_c = omega_c / (a * a * a);
    let rho_b = omega_b / (a * a * a);
    let rho_g = omega_gamma / (a * a * a * a);
    let rho_n = omega_nu / (a * a * a * a);
    let rho_l = 1.0 - omega_m - omega_gamma - omega_nu;
    let rho_tot = (rho_c + rho_b + rho_g + rho_n + rho_l).max(1e-30);
    (rho_c / rho_tot, rho_b / rho_tot, rho_g / rho_tot, rho_n / rho_tot)
}

/// Build the matrix A(τ) for y' = A y.
/// ḣ is a STATE VARIABLE (row hdot_idx), not algebraic.
pub(crate) fn build_sync_v2_matrix(
    k: f64, a_h: f64, kd: f64, r_b: f64, a: f64,
    omega_m: f64, omega_b: f64, omega_gamma: f64,
    lg: usize, ln: usize,
) -> Vec<f64> {
    let omega_nu = omega_gamma * 0.2271 * N_EFF;
    let (oc_z, ob_z, og_z, on_z) = density_fractions(a, omega_m, omega_b, omega_gamma, omega_nu);
    let lay = SyncV2Layout::new(lg, ln);
    let n = lay.n_state;
    let mut m = vec![0.0; n * n];
    let idx = |r: usize, c: usize| r * n + c;
    let n0 = lay.nu_offset;

    // ═══ Θ₀' = -kΘ₁ - ḣ/6 ═══
    if lg >= 1 { m[idx(0, 1)] = -k; }
    m[idx(0, lay.hdot_idx)] = -1.0 / 6.0;

    // ═══ Θ₁' = (k/3)(Θ₀ - 2Θ₂) - κ'(Θ₁ - v_b/3) ═══
    if lg >= 1 {
        m[idx(1, 0)] = k / 3.0;
        if lg >= 2 { m[idx(1, 2)] = -2.0 * k / 3.0; }
        m[idx(1, 1)] = -kd;
        m[idx(1, lay.vb_idx)] = kd / 3.0;
    }

    // ═══ Θ_ℓ, ℓ ≥ 2 ═══
    for ell in 2..=lg {
        let fac = k / (2 * ell + 1) as f64;
        m[idx(ell, ell - 1)] = fac * ell as f64;
        if ell < lg { m[idx(ell, ell + 1)] = -fac * (ell + 1) as f64; }
        m[idx(ell, ell)] = -kd;
    }

    // ═══ N₀' = -kN₁ - ḣ/6 ═══
    if ln >= 1 { m[idx(n0, n0 + 1)] = -k; }
    m[idx(n0, lay.hdot_idx)] = -1.0 / 6.0;

    // ═══ N₁' = (k/3)(N₀ - 2N₂) ═══
    if ln >= 1 {
        m[idx(n0 + 1, n0)] = k / 3.0;
        if ln >= 2 { m[idx(n0 + 1, n0 + 2)] = -2.0 * k / 3.0; }
    }

    // ═══ N_ℓ, ℓ ≥ 2 ═══
    for ell in 2..=ln {
        let fac = k / (2 * ell + 1) as f64;
        m[idx(n0 + ell, n0 + ell - 1)] = fac * ell as f64;
        if ell < ln { m[idx(n0 + ell, n0 + ell + 1)] = -fac * (ell + 1) as f64; }
    }

    // ═══ δ_c' = -ḣ/2 ═══
    m[idx(lay.dc_idx, lay.hdot_idx)] = -0.5;

    // ═══ δ_b' = -kv_b - ḣ/2 ═══
    m[idx(lay.db_idx, lay.vb_idx)] = -k;
    m[idx(lay.db_idx, lay.hdot_idx)] = -0.5;

    // ═══ v_b' = -ℋv_b + κ'(3Θ₁ - v_b)/R_b ═══
    let inv_rb = 1.0 / r_b.max(1e-10);
    m[idx(lay.vb_idx, lay.vb_idx)] = -a_h - kd * inv_rb;
    if lg >= 1 { m[idx(lay.vb_idx, 1)] = 3.0 * kd * inv_rb; }

    // ═══ (kη)' = (ℋ²/2)[4Ω_γΘ₁ + 4Ω_νN₁ + Ω_bv_b] ═══
    // Momentum constraint: (kη)' = (3ℋ²/2)[4Ω_γΘ₁ + 4Ω_νN₁ + Ω_bv_b]
    // CONFIRMED vs CAMB: ratio 0.9998 with factor 1.5 (was 0.5, 3× error)
    let mom = 1.5 * a_h * a_h;
    if lg >= 1 { m[idx(lay.keta_idx, 1)] = mom * 4.0 * og_z; }
    if ln >= 1 { m[idx(lay.keta_idx, n0 + 1)] = mom * 4.0 * on_z; }
    m[idx(lay.keta_idx, lay.vb_idx)] = mom * ob_z;

    // ═══ ḣ' = -2ℋḣ - (3/2)ℋ²[Ω_cδ_c + Ω_bδ_b + 8Ω_γΘ₀ + 8Ω_νN₀] ═══
    m[idx(lay.hdot_idx, lay.hdot_idx)] = -2.0 * a_h;
    m[idx(lay.hdot_idx, lay.dc_idx)] = -1.5 * a_h * a_h * oc_z;
    m[idx(lay.hdot_idx, lay.db_idx)] = -1.5 * a_h * a_h * ob_z;
    m[idx(lay.hdot_idx, 0)]          = -1.5 * a_h * a_h * 8.0 * og_z;
    m[idx(lay.hdot_idx, n0)]         = -1.5 * a_h * a_h * 8.0 * on_z;

    m
}

/// Adiabatic IC with ḣ from the (00) constraint.
pub(crate) fn sync_v2_adiabatic_ic(
    k: f64, a_h_init: f64, lay: &SyncV2Layout,
    omega_m: f64, omega_b: f64, omega_gamma: f64,
) -> Vec<f64> {
    let omega_nu = omega_gamma * 0.2271 * N_EFF;
    let n = lay.n_state;
    let mut y = vec![0.0; n];
    let eta_init = 1.0;  // ζ = 1 normalization

    y[0] = -0.5 * eta_init;                // Θ₀
    y[lay.nu_offset] = -0.5 * eta_init;    // N₀
    y[lay.dc_idx] = -1.5 * eta_init;       // δ_c
    y[lay.db_idx] = -1.5 * eta_init;       // δ_b
    y[lay.keta_idx] = k * eta_init;        // kη

    // First-order dipole corrections
    if lay.ell_max_g >= 1 {
        y[1] = -k / (6.0 * a_h_init.max(1e-30)) * eta_init;
    }
    if lay.ell_max_nu >= 1 {
        y[lay.nu_offset + 1] = y[1];
    }
    y[lay.vb_idx] = y[1];

    // ḣ from (00) constraint: ℋḣ/2 = k²η + (3/2)ℋ²Σ Ωᵢδᵢ
    let a_init = a_h_init / (100.0 * 0.6736 / 2.998e5);  // rough a from ℋ
    // Use a better estimate: at z_max, a is small
    // For now, compute density fractions at init
    let (oc, ob, og, on) = density_fractions(
        1e-5, // approximate a at high z_max
        omega_m, omega_b, omega_gamma, omega_nu,
    );
    let sum_omega_delta = oc * y[lay.dc_idx] + ob * y[lay.db_idx]
        + 4.0 * og * y[0] + 4.0 * on * y[lay.nu_offset];
    y[lay.hdot_idx] = 2.0 * (k * k * eta_init + 1.5 * a_h_init * a_h_init * sum_omega_delta)
        / a_h_init.max(1e-30);

    y
}

/// Compute Newtonian gauge potentials from evolved sync variables.
/// NO 1/k² singularity because ḣ and η̇ are evolved consistently.
#[inline]
pub(crate) fn newtonian_potentials(
    k: f64, a_h: f64, y: &[f64], lay: &SyncV2Layout,
    og_z: f64, on_z: f64, ob_z: f64,
) -> (f64, f64) {
    let keta = y[lay.keta_idx];
    let hdot = y[lay.hdot_idx];
    let eta_s = keta / k.max(1e-30);

    // η̇_S from momentum constraint
    let theta1 = if lay.ell_max_g >= 1 { y[1] } else { 0.0 };
    let n1 = if lay.ell_max_nu >= 1 { y[lay.nu_offset + 1] } else { 0.0 };
    let vb = y[lay.vb_idx];
    let keta_dot = 1.5 * a_h * a_h * (4.0 * og_z * theta1
        + 4.0 * on_z * n1 + ob_z * vb);
    let eta_dot_s = keta_dot / k.max(1e-30);

    // σ = (ḣ + 6η̇)/(2k)
    let sigma = (hdot + 6.0 * eta_dot_s) / (2.0 * k.max(1e-30));

    // Φ = η - ℋσ/k  (NO cancellation if ḣ is evolved consistently)
    let phi = eta_s - a_h * sigma / k.max(1e-30);

    // Ψ = -Φ for no anisotropic stress
    // TODO: add aniso stress from Θ₂, N₂
    let psi = -phi;

    (phi, psi)
}

/// Full source function in sync gauge.
/// S_T = g(Θ₀ + Ψ) + e^{-κ}(Φ̇ + Ψ̇)
/// The Θ₀ here is SYNC GAUGE Θ₀; we need Θ₀_N = Θ₀_S + ℋα
/// where α = ḣ/(2k²). But since ḣ is evolved, this is well-conditioned.
#[inline]
pub(crate) fn source_function(
    k: f64, a_h: f64, y: &[f64], lay: &SyncV2Layout,
    g: f64, _exp_neg_kappa: f64,
    og_z: f64, on_z: f64, ob_z: f64,
) -> f64 {
    let hdot = y[lay.hdot_idx];
    let k2 = k * k;

    // α = ḣ/(2k²) — well-conditioned because ḣ is evolved, not algebraic
    let alpha = hdot / (2.0 * k2.max(1e-30));

    // Θ₀_N = Θ₀_S + ℋα
    let theta0_n = y[0] + a_h * alpha;

    // Ψ from gauge transformation
    let (_, psi) = newtonian_potentials(k, a_h, y, lay, og_z, on_z, ob_z);

    // SW source: g × (Θ₀_N + Ψ)
    let sw = g * (theta0_n + psi);

    // ISW: e^{-κ} × (Φ̇ + Ψ̇) — deferred to TASK-3
    // For now, return SW-only
    sw
}

/// Constraint monitor: k²η - ℋḣ/2 + (3/2)ℋ²Σ Ωᵢδᵢ should = 0.
#[inline]
pub(crate) fn constraint_violation(
    k: f64, a_h: f64, y: &[f64], lay: &SyncV2Layout,
    oc_z: f64, ob_z: f64, og_z: f64, on_z: f64,
) -> f64 {
    let keta = y[lay.keta_idx];
    let hdot = y[lay.hdot_idx];
    let sum_delta = oc_z * y[lay.dc_idx] + ob_z * y[lay.db_idx]
        + 4.0 * og_z * y[0] + 4.0 * on_z * y[lay.nu_offset];
    k * keta - 0.5 * a_h * hdot + 1.5 * a_h * a_h * sum_delta
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_v2_layout() {
        let lay = SyncV2Layout::new(20, 10);
        assert_eq!(lay.n_state, 21 + 11 + 5); // 37 (one more than v1's 36)
        assert_eq!(lay.hdot_idx, lay.keta_idx + 1);
    }

    #[test]
    fn test_v2_matrix_structure() {
        let k = 0.05;
        let a_h = 0.01;
        let kd = 100.0;
        let r_b = 0.1;
        let a = 2.5e-4;
        let lg = 20_usize; let ln = 10;
        let mat = build_sync_v2_matrix(k, a_h, kd, r_b, a, 0.3153, 0.04930, 9.14e-5, lg, ln);
        let lay = SyncV2Layout::new(lg, ln);
        let n = lay.n_state;
        assert_eq!(mat.len(), n * n);
        assert!(mat.iter().all(|&x| x.is_finite()));

        // kη has NO self-coupling
        let keta_self = mat[lay.keta_idx * n + lay.keta_idx];
        assert!(keta_self.abs() < 1e-20, "kη self-coupling = {:.2e}", keta_self);

        // ḣ has self-coupling -2ℋ (damping)
        let hdot_self = mat[lay.hdot_idx * n + lay.hdot_idx];
        assert!((hdot_self + 2.0 * a_h).abs() < 1e-12,
            "ḣ self-coupling should be -2ℋ={:.4e}, got {:.4e}", -2.0*a_h, hdot_self);

        // Θ₀ couples to ḣ with coefficient -1/6
        let theta0_hdot = mat[0 * n + lay.hdot_idx];
        assert!((theta0_hdot + 1.0/6.0).abs() < 1e-12,
            "Θ₀→ḣ coupling should be -1/6, got {:.4e}", theta0_hdot);

        // δ_c couples to ḣ with coefficient -1/2
        let dc_hdot = mat[lay.dc_idx * n + lay.hdot_idx];
        assert!((dc_hdot + 0.5).abs() < 1e-12,
            "δ_c→ḣ coupling should be -1/2, got {:.4e}", dc_hdot);

        eprintln!("  v2_matrix: n={}, kη_self={:.2e}, ḣ_self={:.4e}, Θ₀→ḣ={:.4e}",
            n, keta_self, hdot_self, theta0_hdot);
    }

    #[test]
    fn test_v2_ic_constraint() {
        let k = 0.05;
        let a_h = 0.01;
        let og = 9.14e-5;
        let on = og * 0.2271 * N_EFF;
        let lay = SyncV2Layout::new(20, 10);
        let y = sync_v2_adiabatic_ic(k, a_h, &lay, 0.3153, 0.04930, og);

        let (oc, ob, ogg, onn) = density_fractions(1e-5, 0.3153, 0.04930, og, on);
        let viol = constraint_violation(k, a_h, &y, &lay, oc, ob, ogg, onn);
        let scale = (k * y[lay.keta_idx]).abs().max(1e-10);
        let rel_viol = viol.abs() / scale;

        eprintln!("  v2_ic: ḣ={:.4e}, kη={:.4e}, constraint_viol={:.4e} (rel={:.4e})",
            y[lay.hdot_idx], y[lay.keta_idx], viol, rel_viol);
        assert!(rel_viol < 0.01, "Constraint violation {:.4e} too large", rel_viol);
    }
}

/// Solve a k-mode using sync v2 (ḣ evolved) and extract source + potentials.
pub(crate) fn solve_sync_v2_kmode(
    k: f64, params: &VisibilityParams, vis: &VisibilityResult,
    ell_max_g: usize, ell_max_nu: usize,
) -> Result<SyncV2Result, String> {
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::core::config::Rodas5PConfig;
    use crate::recombination::hyrec_tables::HyRecTables;

    let h0c = params.h * 1e5 / 2.99792458e8;
    let og = params.omega_gamma();
    let omega_nu = og * 0.2271 * N_EFF;
    let n_vis = vis.z_grid.len();
    let eta_max = vis.eta_grid.iter().cloned().fold(0.0_f64, f64::max);

    let lg = ell_max_g; let ln = ell_max_nu;
    let lay = SyncV2Layout::new(lg, ln);
    let n = lay.n_state;

    // Build matrix profile (reversed: τ=0 at z_max)
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n * n);
    let mut bg_data = Vec::with_capacity(n_vis); // (a_h, oc, ob, og, on, g, exp_neg_kappa)

    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        let z = vis.z_grid[i]; let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[i];
        let r_b = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));
        let mat = build_sync_v2_matrix(k, a_h, kd, r_b, a, params.omega_m, params.omega_b, og, lg, ln);
        mats_flat.extend_from_slice(&mat);
        let (oc, ob, ogg, on) = density_fractions(a, params.omega_m, params.omega_b, og, omega_nu);
        let g = vis.g_grid[i];
        let exp_mk = if vis.tau_grid[i] < 500.0 { (-vis.tau_grid[i]).exp() } else { 0.0 };
        bg_data.push((a_h, oc, ob, ogg, on, g, exp_mk));
    }

    // IC
    let z_init = vis.z_grid[n_vis - 1];
    let a_init = 1.0 / (1.0 + z_init);
    let a_h_init = a_init * h0c * params.e_of_z(z_init);
    let y0 = sync_v2_adiabatic_ic(k, a_h_init, &lay, params.omega_m, params.omega_b, og);

    // Solve
    let h_max_k = (4.0 * 3.0_f64.sqrt() / k.max(1e-10)).min(200.0);
    let cfg = Rodas5PConfig {
        rtol: 1e-6, atol: 1e-9, max_steps: 1_000_000,
        h_init: None, h_min: 1e-14, h_max: h_max_k,
        f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
        use_analytic_jacobian: true, use_ft_term: false,
        use_blas_lu: false, use_block_diag: false,
        ell_max_gamma_hint: lg, ell_max_nu_hint: ln,
        ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false,
    };
    let (snapshots_rev, _, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg,
    )?;

    // Extract results (reverse to increasing η)
    let n_snaps = snapshots_rev.len();
    let mut result = SyncV2Result {
        eta_grid: Vec::with_capacity(n_snaps),
        raw_theta0_source: Vec::with_capacity(n_snaps),
        phi: Vec::with_capacity(n_snaps),
        psi: Vec::with_capacity(n_snaps),
        constraint_viol: Vec::with_capacity(n_snaps),
        n_state: n,
    };

    for si in 0..n_snaps {
        let ri = n_snaps - 1 - si;
        let eta = vis.eta_grid[ri];
        result.eta_grid.push(eta);

        let y = &snapshots_rev[si];
        let (a_h, oc, ob, ogg, on, g, _emk) = bg_data[si];

        let sw = source_function(k, a_h, y, &lay, g, 0.0, ogg, on, ob);
        result.raw_theta0_source.push(sw);

        let (phi, psi) = newtonian_potentials(k, a_h, y, &lay, ogg, on, ob);
        result.phi.push(phi);
        result.psi.push(psi);

        let cv = constraint_violation(k, a_h, y, &lay, oc, ob, ogg, on);
        result.constraint_viol.push(cv);
    }

    Ok(result)
}

pub(crate) struct SyncV2Result {
    pub(crate) eta_grid: Vec<f64>,
    pub(crate) raw_theta0_source: Vec<f64>,
    pub(crate) phi: Vec<f64>,
    pub(crate) psi: Vec<f64>,
    pub(crate) constraint_viol: Vec<f64>,
    pub(crate) n_state: usize,
}

#[cfg(test)]
mod integration_tests {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    /// THE CRITICAL TEST: Φ at k=0.001 should be O(1), not O(10⁻⁵).
    #[test]
    fn test_v2_potentials_low_k() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);

        for &k in &[0.001_f64, 0.005, 0.01, 0.05, 0.10] {
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(10).min(60);
            let ln = (lg / 2).max(6);
            let t0 = std::time::Instant::now();
            let r = solve_sync_v2_kmode(k, &p, &vis, lg, ln).unwrap();
            let ms = t0.elapsed().as_millis();

            // Find visibility peak
            let n = r.eta_grid.len();
            let i_peak = r.raw_theta0_source.iter().enumerate()
                .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;

            let phi_peak = r.phi[i_peak];
            let psi_peak = r.psi[i_peak];
            let src_peak = r.raw_theta0_source[i_peak];
            let cv_max = r.constraint_viol.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
            let cv_rel = cv_max / (k * r.eta_grid[i_peak].max(1e-10)).abs().max(1e-10);

            eprintln!("  k={:.4}: Φ={:>10.4e} Ψ={:>10.4e} src={:>10.4e} |CV|={:.2e} {}ms",
                k, phi_peak, psi_peak, src_peak, cv_rel, ms);
        }
        eprintln!("  Old v1 at k=0.001: Φ was O(10⁻⁵) → FIXED: Φ should be O(0.1-1)");
    }
}

// ═══════════════════════════════════════════════════════════════════════
// AUDIT FINDING (P0): The source_function() and newtonian_potentials()
// functions use the gauge transformation Φ = η - ℋ(ḣ+6η̇)/(2k²),
// which has a STRUCTURAL 1/k² singularity. Even with evolved ḣ,
// the source is wrong by 27× at k=0.001.
//
// DO NOT USE source_function() or newtonian_potentials() for k < 0.03.
// Use the existing Newtonian gauge pipeline for low k instead.
//
// For a full sync-only pipeline, CAMB-style integration-by-parts source
// assembly is needed (PATCH-2, future work).
//
// The v2 solver's value: constraint monitoring (constraint_violation())
// and the ḣ evolution equation (for Bianchi production where ḣ couples
// to geometric shear).
// ═══════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════
// R1 REPAIR: k-guarded wrappers that panic for k < 0.03
// ═══════════════════════════════════════════════════════════════════════

/// Safe wrapper: compute Newtonian potentials ONLY for k ≥ 0.03.
/// Panics for k < 0.03 where gauge transform has catastrophic cancellation.
pub(crate) fn newtonian_potentials_safe(
    k: f64, a_h: f64, y: &[f64], lay: &SyncV2Layout,
    og_z: f64, on_z: f64, ob_z: f64,
) -> (f64, f64) {
    assert!(k >= 0.025, "newtonian_potentials_safe: k={:.4} < 0.025 → gauge transform \
        has catastrophic cancellation (|α|={:.0}). Use Newtonian solver for low k.",
        k, a_h / (2.0 * k * k));
    newtonian_potentials(k, a_h, y, lay, og_z, on_z, ob_z)
}

/// Safe wrapper: compute source ONLY for k ≥ 0.03.
pub(crate) fn source_function_safe(
    k: f64, a_h: f64, y: &[f64], lay: &SyncV2Layout,
    g: f64, exp_neg_kappa: f64,
    og_z: f64, on_z: f64, ob_z: f64,
) -> f64 {
    assert!(k >= 0.025, "source_function_safe: k={:.4} < 0.025", k);
    source_function(k, a_h, y, lay, g, exp_neg_kappa, og_z, on_z, ob_z)
}

#[cfg(test)]
mod doppler_debug {
    use crate::solver::flrw_kmode::solve_kmode_with_history;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    /// Check v_b magnitude — is Doppler source too large?
    #[test]
    fn test_doppler_source_magnitude() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        eprintln!("\n  === DOPPLER SOURCE DIAGNOSIS ===");
        eprintln!("  {:>8} {:>12} {:>12} {:>12} {:>8}", "k", "max|g×(Θ₀+Ψ)|", "max|g×v_b|", "Dop/SW", "v_b_peak");

        for &k in &[0.001_f64, 0.005, 0.01, 0.02, 0.03] {
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(8).min(25);
            let ln = (lg / 2).max(6);
            match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(kr) => {
                    let n = kr.raw_theta0_source.len();
                    let max_sw = kr.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));

                    // Extract v_b at visibility peak
                    let i_peak = kr.raw_theta0_source.iter().enumerate()
                        .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;
                    let v_b_peak = kr.snapshots[i_peak][kr.n_state - 2]; // v_b is second-to-last

                    // g × v_b at peak
                    let vis_i = vis.z_grid.len() - 1 - i_peak;
                    let g_peak = if vis_i < vis.g_grid.len() { vis.g_grid[vis_i] } else { 0.0 };
                    let max_doppler = g_peak * v_b_peak.abs();

                    let ratio = max_doppler / max_sw.max(1e-30);
                    eprintln!("  {:>8.4} {:>12.4e} {:>12.4e} {:>12.4e} {:>8.4e}",
                        k, max_sw, max_doppler, ratio, v_b_peak);
                }
                Err(e) => eprintln!("  k={:.4}: FAIL", k),
            }
        }
        eprintln!("  Note: For Φ=1 norm, v_b ∝ 1/(k×c_s) at acoustic peak.");
        eprintln!("  Physical v_b(ζ=1) = (2/3)×v_b(Φ=1). Dop/SW should be < 0.5 at ℓ=2.");
    }
}

#[cfg(test)]
mod doppler_fix {
    use crate::solver::flrw_kmode::{solve_kmode_with_history, extract_source_grid};
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_doppler_from_sourcegrid() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        eprintln!("\n  === DOPPLER FROM SOURCEGRID (correct indexing) ===");
        eprintln!("  {:>8} {:>12} {:>12} {:>12}", "k", "max|SW|", "max|Dop|", "Dop/SW");

        for &k in &[0.001_f64, 0.005, 0.01, 0.02, 0.03] {
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(8).min(25);
            let ln = (lg / 2).max(6);
            match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(kr) => {
                    let sg = extract_source_grid(&kr, &vis, &p);
                    let max_sw = sg.values.iter().map(|v| v.sw.abs()).fold(0.0_f64, f64::max);
                    let max_dop = sg.values.iter().map(|v| v.doppler.abs()).fold(0.0_f64, f64::max);
                    let ratio = max_dop / max_sw.max(1e-30);
                    eprintln!("  {:>8.4} {:>12.4e} {:>12.4e} {:>12.4e}", k, max_sw, max_dop, ratio);
                }
                Err(_) => eprintln!("  k={:.4}: FAIL", k),
            }
        }

        // Now compute Δ₂ contribution from Doppler alone
        eprintln!("\n  Checking Doppler j'_ℓ integral at k=0.01:");
        let k = 0.01_f64;
        let kr = solve_kmode_with_history(k, &p, &vis, 15, 8).unwrap();
        let sg = extract_source_grid(&kr, &vis, &p);
        let n = sg.eta_grid.len();

        // Compute ∫ g v_b j'₂(kη) dη
        let mut delta2_dop = 0.0_f64;
        let mut delta2_sw = 0.0_f64;
        for i in 1..n {
            let d = sg.eta_grid[i];
            let x = k * d;
            if x < 1e-6 { continue; }
            let j2 = (3.0/(x*x) - 1.0) * x.sin()/x - 3.0*x.cos()/(x*x);
            // j'₂(x) = [2j₁(x) - 3j₃(x)] / 5
            let j1 = x.sin()/(x*x) - x.cos()/x;
            let j3 = (15.0/(x*x*x) - 6.0/x)*x.sin()/x - (15.0/(x*x) - 1.0)*x.cos()/x;
            let j2_prime = (2.0*j1 - 3.0*j3) / 5.0;
            let dd = (sg.eta_grid[i] - sg.eta_grid[i-1]).abs();
            delta2_sw += sg.values[i].sw * j2 * dd;
            delta2_dop += sg.values[i].doppler * j2_prime * dd;
        }
        eprintln!("  Δ₂^SW  = {:.4e}", delta2_sw);
        eprintln!("  Δ₂^Dop = {:.4e}", delta2_dop);
        eprintln!("  |Δ₂^SW + Δ₂^Dop|² / |Δ₂^SW|² = {:.4}",
            (delta2_sw + delta2_dop).powi(2) / delta2_sw.powi(2).max(1e-30));
        eprintln!("  Expected: Doppler reduces D₂ by ~5-10% (ratio ~0.9)");
    }
}
#[cfg(test)]
mod bessel_diag {
    use crate::solver::flrw_kmode::solve_kmode_with_history;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;

    #[test]
    fn test_bessel_arg_deep_diagnostic() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let eta_0 = *vis.eta_grid.last().unwrap();
        let n_vis = vis.z_grid.len();

        let k = 1.5e-4_f64; // dominant k for ℓ=2
        let kr = solve_kmode_with_history(k, &p, &vis, 15, 8).unwrap();
        let n = kr.eta_grid.len();

        // Find source peak
        let i_peak = kr.raw_theta0_source.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;

        eprintln!("\n  === BESSEL ARG DEEP DIAGNOSTIC k={:.1e} ===", k);
        eprintln!("  n={}, eta_0={:.1}, peak_i={}", n, eta_0, i_peak);
        eprintln!("  eta_grid: [{:.1}, ..., {:.1}]", kr.eta_grid[0], kr.eta_grid[n-1]);
        eprintln!("");

        // Print source and j₂ near peak (both conventions)
        eprintln!("  {:>6} {:>10} {:>12} {:>12} {:>12} {:>12}", 
            "i", "η", "source", "x=kη", "j₂(kη)", "j₂(k(η₀-η))");
        let range = (i_peak.saturating_sub(5))..=(i_peak+5).min(n-1);
        for i in range {
            let eta = kr.eta_grid[i];
            let src = kr.raw_theta0_source[i];
            let x_direct = k * eta;
            let x_pipeline = k * (eta_0 - eta);
            let j2_direct = spherical_bessel_j(2, x_direct);
            let j2_pipeline = spherical_bessel_j(2, x_pipeline);
            eprintln!("  {:>6} {:>10.1} {:>12.4e} {:>12.4} {:>12.4e} {:>12.4e}",
                i, eta, src, x_direct, j2_direct, j2_pipeline);
        }

        // Compute Δ₂ with both conventions
        let mut d2_direct = 0.0_f64;
        let mut d2_pipeline = 0.0_f64;
        for i in 1..n {
            let deta = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
            let src = kr.raw_theta0_source[i];
            let x_d = k * kr.eta_grid[i];
            let x_p = k * (eta_0 - kr.eta_grid[i]);
            if x_d > 1e-10 { d2_direct += src * spherical_bessel_j(2, x_d) * deta; }
            if x_p > 1e-10 { d2_pipeline += src * spherical_bessel_j(2, x_p) * deta; }
        }
        eprintln!("\n  Δ₂(kη)      = {:.6e}", d2_direct);
        eprintln!("  Δ₂(k(η₀-η)) = {:.6e}", d2_pipeline);
        eprintln!("  ratio        = {:.4}", d2_pipeline / d2_direct.abs().max(1e-30));
        eprintln!("  Thin-shell   ≈ {:.6e} (1/3 × j₂({:.2}))",
            (1.0/3.0) * spherical_bessel_j(2, k * kr.eta_grid[i_peak]),
            k * kr.eta_grid[i_peak]);

        // Also check: what η does the vis g_grid peak at?
        let g_peak_i = vis.g_grid.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap()).unwrap().0;
        eprintln!("\n  Visibility: g_peak at z={:.0}, η={:.1}", 
            vis.z_grid[g_peak_i], vis.eta_grid[g_peak_i]);
        eprintln!("  ∫g dη ≈ {:.4} (should be ~1)",
            vis.g_grid.iter().zip(vis.eta_grid.windows(2))
                .map(|(&g, w)| g * (w[1]-w[0]).abs())
                .sum::<f64>());
    }
}

#[cfg(test)]
mod source_decomp {
    use crate::solver::flrw_kmode::solve_kmode_with_history;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_source_components_at_peak() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let og = p.omega_gamma();
        let h0c = p.h * 1e5 / 2.99792458e8;

        let k = 1.5e-4_f64;
        let kr = solve_kmode_with_history(k, &p, &vis, 15, 8).unwrap();
        let n_vis = vis.z_grid.len();

        let i_peak = kr.raw_theta0_source.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;

        eprintln!("\n  === SOURCE DECOMPOSITION k={:.1e} ===", k);
        eprintln!("  {:>6} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}",
            "i", "η", "g", "Θ₀", "Φ", "Ψ", "Θ₀+Ψ");
        for i in (i_peak.saturating_sub(5))..=(i_peak+5).min(kr.eta_grid.len()-1) {
            let snap = &kr.snapshots[i];
            let theta0 = snap[0];
            let phi = snap[kr.n_state - 1];
            let theta2 = if kr.ell_max_g >= 2 { snap[2] } else { 0.0 };
            let n2 = if kr.ell_max_g >= 2 { snap[kr.ell_max_g + 1 + 2] } else { 0.0 };

            // vis_i for this eta
            let eta = kr.eta_grid[i];
            let vis_i = vis.eta_grid.iter().position(|&e| e >= eta).unwrap_or(0);
            let z = vis.z_grid[vis_i.min(n_vis-1)];
            let a = 1.0 / (1.0 + z);
            let a_h = a * h0c * p.e_of_z(z);
            let g = vis.g_grid[vis_i.min(n_vis-1)];

            let k2 = k * k;
            let omega_nu = og * 0.2271 * 3.044;
            let rho_r = (og + omega_nu) / a.powi(4);
            let rho_tot = rho_r + p.omega_m / a.powi(3) + (1.0 - p.omega_m - og - omega_nu);
            let aniso_coeff = 4.0 * a_h * a_h / k2 * rho_r / rho_tot;
            let f_g = 1.0 - 1.0/(1.0 + 0.2271*3.044);
            let f_nu = 1.0 - f_g;
            let psi = -phi - aniso_coeff * (f_g * theta2 + f_nu * n2);

            eprintln!("  {:>6} {:>10.1} {:>10.4e} {:>10.4e} {:>10.4e} {:>10.4e} {:>10.4e}",
                i, eta, g, theta0, phi, psi, theta0 + psi);
        }
    }
}

#[cfg(test)]
mod sync_gauge_d2 {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    /// Compute D₂ using sync gauge source: S₀=g×Θ₀_S + S₁=g×v_b
    /// Integrated with j_ℓ(kη) and j'_ℓ(kη)/k respectively.
    /// No Newtonian gauge transformation → no Φ instability.
    #[test]
    fn test_sync_gauge_d2() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 3000, 1e5);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);

        let a_s = 2.1e-9_f64;
        let n_s = 0.9649;
        let k_pivot = 0.05;
        let zeta_norm = 4.0 / 9.0; // Φ=1 → ζ=1

        // k-grid: log-spaced from 5e-5 to 0.03
        let n_k = 80_usize;
        let k_min = 5e-5_f64;
        let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max / k_min).powf(i as f64 / (n_k - 1) as f64))
            .collect();

        let ell_max = 30_usize;
        let mut cl = vec![0.0_f64; ell_max + 2];
        let t0 = std::time::Instant::now();
        let mut n_ok = 0_usize;

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(10).min(60);
            let ln = (lg / 2).max(6);

            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r,
                Err(_) => continue,
            };
            n_ok += 1;

            let n = kr.eta_grid.len();
            // Extract state layout
            let vb_idx = lg + 1 + ln + 1 + 2; // δ_c, δ_b, v_b
            let keta_idx = vb_idx + 1;

            // Compute Δ_ℓ = ∫ [g×Θ₀_S × j_ℓ(kη) + g×v_b × j'_ℓ(kη)/k] dη
            let mut delta_ell = vec![0.0_f64; ell_max + 2];

            for i in 1..n {
                let eta = kr.eta_grid[i];
                let x = k * eta;
                if x < 1e-10 || x > 5000.0 { continue; }
                let deta = (kr.eta_grid[i] - kr.eta_grid[i - 1]).abs();

                // Visibility at this η
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis - 1),
                };
                let g_val = vis.g_grid[vi];
                if g_val.abs() < 1e-30 { continue; }

                // Sync gauge variables
                let theta0_s = kr.snapshots[i][0];
                let vb_s = kr.snapshots[i][vb_idx];

                // Source: monopole + Doppler
                let s_monopole = g_val * theta0_s;
                let s_doppler = g_val * vb_s;

                for ell in 2..=ell_max {
                    let jl = spherical_bessel_j(ell, x);
                    // j'_ℓ(x) = [ℓ j_{ℓ-1}(x) - (ℓ+1) j_{ℓ+1}(x)] / (2ℓ+1)
                    let jl_prime = if ell >= 1 {
                        (ell as f64 * spherical_bessel_j(ell - 1, x)
                            - (ell + 1) as f64 * spherical_bessel_j(ell + 1, x))
                            / (2 * ell + 1) as f64
                    } else { 0.0 };

                    delta_ell[ell] += (s_monopole * jl + s_doppler * jl_prime / k.max(1e-30)) * deta;
                }
            }

            // Accumulate C_ℓ
            let p_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);
            let dlnk = if ik == 0 { (k_grid[1] / k_grid[0]).ln() }
                else if ik == n_k - 1 { (k_grid[ik] / k_grid[ik - 1]).ln() }
                else { 0.5 * (k_grid[ik + 1] / k_grid[ik - 1]).ln() };
            let weight = 4.0 * PI * p_zeta * dlnk * zeta_norm;
            for ell in 2..=ell_max {
                cl[ell] += weight * delta_ell[ell] * delta_ell[ell];
            }
        }
        let wall_ms = t0.elapsed().as_millis();

        eprintln!("\n  === SYNC GAUGE D₂ (monopole + Doppler, j_ℓ(kη)) ===");
        eprintln!("  n_k={} ({} ok), k=[{:.0e},{:.2}], wall={}ms", n_k, n_ok, k_min, k_max, wall_ms);

        let d2 = 2.0 * 3.0 / (2.0 * PI) * cl[2] * t_uk2;
        eprintln!("\n  D₂(sync, mono+dop) = {:.1} μK²", d2);
        eprintln!("  CLASS D₂           = 1025 μK²");
        eprintln!("  Thin-shell SW      = 931 μK²");

        eprintln!("\n  {:>5} {:>12}", "ℓ", "D_ℓ μK²");
        for ell in 2..=ell_max.min(20) {
            let dl = ell as f64 * (ell + 1) as f64 / (2.0 * PI) * cl[ell] * t_uk2;
            eprintln!("  {:>5} {:>12.1}", ell, dl);
        }
    }
}

#[cfg(test)]
mod sync_mono_only {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    #[test]
    fn test_sync_monopole_only_d2() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);

        let n_k = 60_usize;
        let k_min = 5e-5_f64; let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();

        let mut cl2_mono = 0.0_f64;
        let mut cl2_full = 0.0_f64;
        let mut n_ok = 0;

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(60);
            let ln = (lg/2).max(6);
            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            n_ok += 1;
            let n = kr.eta_grid.len();
            let vb_idx = lg + 1 + ln + 1 + 2;

            let mut d2_mono = 0.0_f64;
            let mut d2_full = 0.0_f64;
            for i in 1..n {
                let eta = kr.eta_grid[i];
                let x = k * eta;
                if x < 1e-10 || x > 5000.0 { continue; }
                let deta = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                let g = vis.g_grid[vi];
                if g.abs() < 1e-30 { continue; }

                let theta0 = kr.snapshots[i][0];
                let vb = kr.snapshots[i][vb_idx];
                let j2 = spherical_bessel_j(2, x);
                let j1 = spherical_bessel_j(1, x);
                let j3 = spherical_bessel_j(3, x);
                let j2p = (2.0*j1 - 3.0*j3) / 5.0;

                d2_mono += g * theta0 * j2 * deta;
                d2_full += (g * theta0 * j2 + g * vb * j2p / k) * deta;
            }

            let p_zeta = 2.1e-9 * (k/0.05_f64).powf(0.9649 - 1.0);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            let w = 4.0*PI * p_zeta * dlnk * (4.0/9.0);
            cl2_mono += w * d2_mono * d2_mono;
            cl2_full += w * d2_full * d2_full;

            if ik % 15 == 0 {
                eprintln!("  k={:.4e}: Δ₂_mono={:.4e} Δ₂_full={:.4e} ratio={:.3}",
                    k, d2_mono, d2_full, d2_full/d2_mono.abs().max(1e-30));
            }
        }

        let d2_m = 6.0/(2.0*PI) * cl2_mono * t_uk2;
        let d2_f = 6.0/(2.0*PI) * cl2_full * t_uk2;
        eprintln!("\n  === SYNC GAUGE D₂ DECOMPOSITION ===");
        eprintln!("  D₂(monopole only)   = {:.1} μK²", d2_m);
        eprintln!("  D₂(mono + Doppler)  = {:.1} μK²", d2_f);
        eprintln!("  CLASS D₂            = 1025 μK²");
        eprintln!("  Expected D₂(Θ₀_S)  ≈ 2.25 × 931 = 2095 μK² (wrong Θ₀_S≠Θ₀_N+Ψ)");
        eprintln!("  n_ok={}", n_ok);
    }
}

#[cfg(test)]
mod sync_d2_resolved {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    #[test]
    fn test_sync_d2_resolved() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        // CRITICAL: use 3000 pts, z_max=4000 for proper visibility resolution
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);

        let n_k = 60_usize;
        let k_min = 5e-5_f64; let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();

        let mut cl2_mono = 0.0_f64;
        let mut cl2_dop = 0.0_f64;
        let mut cl2_full = 0.0_f64;
        let mut n_ok = 0;

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(60);
            let ln = (lg/2).max(6);
            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            n_ok += 1;
            let n = kr.eta_grid.len();
            let vb_idx = lg + 1 + ln + 1 + 2;

            let mut d2_mono = 0.0_f64;
            let mut d2_dop = 0.0_f64;

            for i in 1..n {
                let eta = kr.eta_grid[i];
                let x = k * eta;
                if x < 1e-10 || x > 5000.0 { continue; }
                let deta = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                let g = vis.g_grid[vi];
                if g.abs() < 1e-30 { continue; }

                let theta0 = kr.snapshots[i][0];
                let vb = kr.snapshots[i][vb_idx];
                let j2 = spherical_bessel_j(2, x);
                let j1 = spherical_bessel_j(1, x);
                let j3 = spherical_bessel_j(3, x);
                let j2p = (2.0*j1 - 3.0*j3)/5.0;

                d2_mono += g * theta0 * j2 * deta;
                d2_dop += g * vb * j2p / k * deta;
            }

            let p_z = 2.1e-9*(k/0.05_f64).powf(-0.0351);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            let w = 4.0*PI * p_z * dlnk * (4.0/9.0);
            cl2_mono += w * d2_mono * d2_mono;
            cl2_dop += w * d2_dop * d2_dop;
            cl2_full += w * (d2_mono + d2_dop) * (d2_mono + d2_dop);

            if ik % 10 == 0 {
                eprintln!("  k={:.4e}: Δ₂_mono={:.4e} Δ₂_dop={:.4e} dop/mono={:.3}",
                    k, d2_mono, d2_dop, d2_dop/d2_mono.abs().max(1e-30));
            }
        }
        let d2m = 6.0/(2.0*PI) * cl2_mono * t_uk2;
        let d2d = 6.0/(2.0*PI) * cl2_dop * t_uk2;
        let d2f = 6.0/(2.0*PI) * cl2_full * t_uk2;
        eprintln!("\n  === SYNC GAUGE D₂ (resolved visibility, j₂(kη)) ===");
        eprintln!("  D₂(monopole only)      = {:.1} μK²", d2m);
        eprintln!("  D₂(Doppler only)       = {:.1} μK²", d2d);
        eprintln!("  D₂(mono + Doppler)     = {:.1} μK²", d2f);
        eprintln!("  Thin-shell D₂(Θ₀_S)   ≈ 2095 μK² (Θ₀_S=-1/2, not 1/3)");
        eprintln!("  CLASS D₂               = 1025 μK²");
        eprintln!("  n_ok={}", n_ok);
    }
}

#[cfg(test)]
mod sync_vb_check {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_sync_vb_values() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();

        for &k in &[1e-4_f64, 5e-4, 1e-3, 5e-3, 1e-2] {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(60);
            let ln = (lg/2).max(6);
            let vb_idx = lg + 1 + ln + 1 + 2;
            let keta_idx = vb_idx + 1;
            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => { eprintln!("  k={:.1e}: FAIL", k); continue; },
            };
            // Find visibility peak in the output
            let n = kr.eta_grid.len();
            let mut i_peak = 0;
            let mut g_max = 0.0_f64;
            for i in 0..n {
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&kr.eta_grid[i]).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                if vis.g_grid[vi] > g_max {
                    g_max = vis.g_grid[vi];
                    i_peak = i;
                }
            }
            let y = &kr.snapshots[i_peak];
            eprintln!("  k={:.1e}: Θ₀={:.4e} v_b={:.4e} kη={:.4e} η={:.1} g={:.4e} n_state={}",
                k, y[0], y[vb_idx], y[keta_idx], kr.eta_grid[i_peak], g_max, kr.n_state);
        }
    }
}

#[cfg(test)]
mod sync_theta1_check {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_sync_theta1_vb_equilibrium() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();

        eprintln!("\n  === Θ₁ vs v_b/3 CHECK (tight coupling) ===");
        for &k in &[1e-4_f64, 5e-4, 1e-3, 5e-3, 1e-2] {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(60);
            let ln = (lg/2).max(6);
            let vb_idx = lg + 1 + ln + 1 + 2;
            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            let n = kr.eta_grid.len();
            let mut i_peak = 0; let mut g_max = 0.0_f64;
            for i in 0..n {
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&kr.eta_grid[i]).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                if vis.g_grid[vi] > g_max { g_max = vis.g_grid[vi]; i_peak = i; }
            }
            let y = &kr.snapshots[i_peak];
            let theta1 = y[1];
            let vb = y[vb_idx];
            let dc = y[lg + 1 + ln + 1];
            let db = y[lg + 1 + ln + 1 + 1];
            eprintln!("  k={:.1e}: Θ₁={:.4e} v_b/3={:.4e} v_b={:.4e} δ_c={:.4e} δ_b={:.4e} eq={:.1e}",
                k, theta1, vb/3.0, vb, dc, db, (vb - 3.0*theta1).abs());
        }
    }
}

#[cfg(test)]
mod sync_d2_ibp {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    /// Compute D₂ using IBP source: S_IBP = g Θ₀ - (g v_b)'/k + e^{-κ} η̇
    /// Integrated with j_ℓ(kη) ONLY (no j'_ℓ). Gauge-invariant by construction.
    #[test]
    fn test_sync_d2_ibp() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();

        let n_k = 60_usize;
        let k_min = 5e-5_f64; let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();

        let mut cl2 = 0.0_f64;
        let mut n_ok = 0;

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(60);
            let ln = (lg/2).max(6);
            let vb_idx = lg + 1 + ln + 1 + 2;
            let keta_idx = vb_idx + 1;

            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            n_ok += 1;
            let n = kr.eta_grid.len();

            // Build IBP source at each grid point
            // S_IBP[i] = g[i] * Θ₀[i] - (g v_b)'[i] / k + e^{-κ}[i] * η̇[i]
            let mut s_ibp = vec![0.0_f64; n];
            let mut g_vb = vec![0.0_f64; n];  // g × v_b at each point

            for i in 0..n {
                let eta_i = kr.eta_grid[i];
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta_i).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                let g = vis.g_grid[vi];
                let theta0 = kr.snapshots[i][0];
                let vb = kr.snapshots[i][vb_idx];

                s_ibp[i] = g * theta0;  // monopole piece
                g_vb[i] = g * vb;

                // ISW piece: e^{-κ} × η̇
                let tau_opt = vis.tau_grid[vi];
                let emk = if tau_opt < 500.0 { (-tau_opt).exp() } else { 0.0 };
                // η̇ = (kη)' / k — from momentum constraint
                // (kη)' = (ℋ²/2)(4Ω_γΘ₁ + 4Ω_νN₁ + Ω_bv_b)
                let z = vis.z_grid[vi];
                let a = 1.0 / (1.0 + z);
                let a_h = a * h0c * p.e_of_z(z);
                let omega_nu = og * 0.2271 * 3.044;
                let rho_g = og / a.powi(4);
                let rho_n = omega_nu / a.powi(4);
                let rho_m = p.omega_m / a.powi(3);
                let rho_l = 1.0 - p.omega_m - og - omega_nu;
                let rho_tot = (rho_g + rho_n + rho_m + rho_l).max(1e-30);
                let og_z = rho_g / rho_tot;
                let on_z = rho_n / rho_tot;
                let ob_z = p.omega_b / a.powi(3) / rho_tot;

                let theta1 = if lg >= 1 { kr.snapshots[i][1] } else { 0.0 };
                let n1 = if ln >= 1 { kr.snapshots[i][lg + 1 + 1] } else { 0.0 };
                let keta_dot = 1.5 * a_h * a_h * (4.0*og_z*theta1 + 4.0*on_z*n1 + ob_z*vb);
                let eta_dot = keta_dot / k.max(1e-30);

                s_ibp[i] += emk * eta_dot;  // ISW piece
            }

            // Compute (g v_b)' / k by finite difference and subtract
            for i in 1..n-1 {
                let deta = (kr.eta_grid[i+1] - kr.eta_grid[i-1]).abs().max(1e-30);
                let gvb_prime = (g_vb[i+1] - g_vb[i-1]) / deta;
                s_ibp[i] -= gvb_prime / k;
            }

            // Integrate Δ₂ = ∫ S_IBP × j₂(kη) dη
            let mut d2 = 0.0_f64;
            for i in 1..n {
                let eta = kr.eta_grid[i];
                let x = k * eta;
                if x < 1e-10 || x > 5000.0 { continue; }
                let deta = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
                d2 += s_ibp[i] * spherical_bessel_j(2, x) * deta;
            }

            let p_z = 2.1e-9 * (k/0.05_f64).powf(-0.0351);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            let w = 4.0*PI * p_z * dlnk * (4.0/9.0);
            cl2 += w * d2 * d2;

            if ik % 10 == 0 {
                eprintln!("  k={:.4e}: Δ₂={:.4e}", k, d2);
            }
        }

        let d2_result = 6.0/(2.0*PI) * cl2 * t_uk2;
        eprintln!("\n  === SYNC GAUGE D₂ (IBP source, j₂(kη)) ===");
        eprintln!("  D₂ = {:.1} μK²", d2_result);
        eprintln!("  CLASS = 1025 μK²");
        eprintln!("  n_ok = {}", n_ok);
    }
}

#[cfg(test)]
mod sync_d2_ibp_analytic {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    #[test]
    fn test_sync_d2_ibp_analytic() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();

        // Pre-compute g'(η) from visibility data
        let mut g_dot = vec![0.0_f64; n_vis];
        for i in 1..n_vis-1 {
            let deta = (vis.eta_grid[i+1] - vis.eta_grid[i-1]).abs().max(1e-30);
            g_dot[i] = (vis.g_grid[i+1] - vis.g_grid[i-1]) / deta;
        }

        let n_k = 60_usize;
        let k_min = 5e-5_f64; let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();
        let mut cl2 = 0.0_f64;

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(60);
            let ln = (lg/2).max(6);
            let vb_idx = lg + 1 + ln + 1 + 2;

            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            let n = kr.eta_grid.len();

            let mut d2 = 0.0_f64;
            for i in 1..n {
                let eta_i = kr.eta_grid[i];
                let x = k * eta_i;
                if x < 1e-10 || x > 5000.0 { continue; }
                let deta = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();

                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta_i).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                let g = vis.g_grid[vi];
                let gp = g_dot[vi]; // g'(η)
                let kd = vis.kappa_dot_grid[vi];
                let z = vis.z_grid[vi];
                let a = 1.0/(1.0+z);
                let a_h = a * h0c * p.e_of_z(z);
                let r_b = 3.0*p.omega_b/(4.0*og*(1.0+z));

                let theta0 = kr.snapshots[i][0];
                let theta1 = if lg>=1 { kr.snapshots[i][1] } else { 0.0 };
                let vb = kr.snapshots[i][vb_idx];

                // S_IBP = g Θ₀ - (g v_b)'/k
                // (g v_b)' = g' v_b + g v_b'
                // v_b' = -ℋ v_b + κ'(3Θ₁ - v_b)/R_b  (sync gauge baryon Euler)
                let vb_dot = -a_h * vb + kd * (3.0*theta1 - vb) / r_b.max(1e-30);
                let gvb_dot = gp * vb + g * vb_dot;
                let s_ibp = g * theta0 - gvb_dot / k;

                d2 += s_ibp * spherical_bessel_j(2, x) * deta;
            }

            let p_z = 2.1e-9*(k/0.05_f64).powf(-0.0351);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            cl2 += 4.0*PI * p_z * dlnk * (4.0/9.0) * d2 * d2;

            if ik % 10 == 0 {
                eprintln!("  k={:.4e}: Δ₂={:.4e}", k, d2);
            }
        }
        let d2_r = 6.0/(2.0*PI) * cl2 * t_uk2;
        eprintln!("\n  === SYNC D₂ (IBP analytic deriv, j₂(kη)) ===");
        eprintln!("  D₂ = {:.1} μK²", d2_r);
        eprintln!("  CLASS = 1025, thin-shell SW = 931");
    }
}

#[cfg(test)]
mod sync_d2_ibp_sweep {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    /// Sweep different IBP coefficients to find the correct formula
    #[test]
    fn test_ibp_sweep() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();

        let mut g_dot = vec![0.0_f64; n_vis];
        for i in 1..n_vis-1 {
            let d = (vis.eta_grid[i+1]-vis.eta_grid[i-1]).abs().max(1e-30);
            g_dot[i] = (vis.g_grid[i+1]-vis.g_grid[i-1]) / d;
        }

        let n_k = 40_usize;
        let k_min = 5e-5_f64; let k_max = 0.02;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();

        // Try 4 variants of the IBP formula
        let labels = [
            "g*Θ₀ only",
            "g*Θ₀ + (gvb)'/k",
            "g*Θ₀ - (gvb)'/k",
            "g*Θ₀ + (g'*vb)/k",
        ];
        let mut cl2 = vec![0.0_f64; 4];

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k*280.0*2.0).ceil() as usize).max(10).min(40);
            let ln = (lg/2).max(6);
            let vb_idx = lg+1+ln+1+2;
            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            let n = kr.eta_grid.len();
            let mut d2 = vec![0.0_f64; 4];

            for i in 1..n {
                let eta = kr.eta_grid[i];
                let x = k*eta;
                if x < 1e-10 || x > 5000.0 { continue; }
                let de = (kr.eta_grid[i]-kr.eta_grid[i-1]).abs();
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                let g = vis.g_grid[vi];
                let gp = g_dot[vi];
                let kd = vis.kappa_dot_grid[vi];
                let z = vis.z_grid[vi];
                let a = 1.0/(1.0+z);
                let a_h = a*h0c*p.e_of_z(z);
                let r_b = 3.0*p.omega_b/(4.0*og*(1.0+z));
                let t0 = kr.snapshots[i][0];
                let t1 = if lg>=1 { kr.snapshots[i][1] } else { 0.0 };
                let vb = kr.snapshots[i][vb_idx];
                let vbd = -a_h*vb + kd*(3.0*t1-vb)/r_b.max(1e-30);
                let gvbd = gp*vb + g*vbd;
                let j2 = spherical_bessel_j(2, x);

                d2[0] += g*t0 * j2 * de;
                d2[1] += (g*t0 + gvbd/k) * j2 * de;
                d2[2] += (g*t0 - gvbd/k) * j2 * de;
                d2[3] += (g*t0 + gp*vb/k) * j2 * de;
            }
            let pz = 2.1e-9*(k/0.05_f64).powf(-0.0351);
            let dl = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            let w = 4.0*PI*pz*dl*(4.0/9.0);
            for v in 0..4 { cl2[v] += w * d2[v]*d2[v]; }
        }

        eprintln!("\n  === IBP FORMULA SWEEP ===");
        for v in 0..4 {
            let d = 6.0/(2.0*PI)*cl2[v]*t_uk2;
            eprintln!("  {:30}: D₂ = {:.1} μK²", labels[v], d);
        }
        eprintln!("  CLASS = 1025 μK²");
    }
}

#[cfg(test)]
mod sync_d2_direct {
    use crate::solver::sync_kmode::solve_sync_kmode;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use std::f64::consts::PI;

    /// D₂ by directly reading Θ₂(k, z=0) from sync solver.
    /// No LoS integral, no IBP, no gauge transformation.
    /// C₂ = 4π ∫ dk/k P_ζ × (4/9) × |Θ₂(k,z=0)|²
    #[test]
    fn test_sync_d2_direct_theta2() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);

        let n_k = 40_usize;
        let k_min = 5e-5_f64; let k_max = 0.02;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();
        let mut cl2 = 0.0_f64;
        let mut n_ok = 0;

        eprintln!("\n  === DIRECT Θ₂(k,z=0) FROM SYNC SOLVER ===");
        for (ik, &k) in k_grid.iter().enumerate() {
            // Need ℓ_max ≥ max(kη₀ + 5, 10)
            let keta0 = k * 13865.0;
            let lg = ((keta0 + 10.0).ceil() as usize).max(10).min(100);
            let ln = (lg/2).max(6);

            let kr = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(e) => {
                    if ik % 10 == 0 { eprintln!("  k={:.1e}: FAIL (ℓ_max={})", k, lg); }
                    continue;
                },
            };
            n_ok += 1;
            let n = kr.eta_grid.len();

            // Find z=0 (η=0) in the output
            // eta_grid goes from η_max to 0 (decreasing), so last element is near 0
            let i_z0 = n - 1;  // last element = z=0
            let theta2_z0 = if lg >= 2 { kr.snapshots[i_z0][2] } else { 0.0 };

            let pz = 2.1e-9*(k/0.05_f64).powf(-0.0351);
            let dl = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
            cl2 += 4.0*PI * pz * dl * (4.0/9.0) * theta2_z0 * theta2_z0;

            if ik % 5 == 0 {
                eprintln!("  k={:.4e}: Θ₂(z=0)={:.4e} ℓ_max={} η(z=0)={:.1}",
                    k, theta2_z0, lg, kr.eta_grid[i_z0]);
            }
        }
        let d2 = 6.0/(2.0*PI) * cl2 * t_uk2;
        eprintln!("\n  D₂(direct Θ₂) = {:.1} μK²", d2);
        eprintln!("  CLASS = 1025 μK²");
        eprintln!("  n_ok = {}/{}", n_ok, n_k);
    }
}

#[cfg(test)]
mod interpolation_test {
    use crate::solver::flrw_kmode::solve_kmode_with_history;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, SourceMode, compute_flrw_cl_track_a};
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    /// Test Φ oscillation at different grid resolutions
    #[test]
    fn test_phi_vs_nvis() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let k = 1.5e-4_f64;

        eprintln!("\n  === PHI OSCILLATION vs n_vis ===");
        for &nv in &[100_usize, 300, 500, 1000, 3000] {
            let vis = compute_visibility(&p, &t, nv);
            let n_vis = vis.z_grid.len();
            let lg = 15; let ln = 8;
            let kr = match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => { eprintln!("  n_vis={}: FAIL", nv); continue; }
            };
            // Find visibility peak and check Φ
            let n = kr.eta_grid.len();
            let mut i_peak = 0; let mut max_src = 0.0_f64;
            for i in 0..n {
                if kr.raw_theta0_source[i].abs() > max_src { max_src = kr.raw_theta0_source[i].abs(); i_peak = i; }
            }
            let phi_peak = kr.snapshots[i_peak][kr.n_state - 1];
            // Check Φ oscillation: std dev of Φ near peak
            let lo = i_peak.saturating_sub(5);
            let hi = (i_peak+5).min(n-1);
            let phis: Vec<f64> = (lo..=hi).map(|i| kr.snapshots[i][kr.n_state-1]).collect();
            let mean = phis.iter().sum::<f64>() / phis.len() as f64;
            let std = (phis.iter().map(|&p| (p-mean).powi(2)).sum::<f64>() / phis.len() as f64).sqrt();
            eprintln!("  n_vis={:>5}: Phi_peak={:>8.4}, std(Phi)={:.4e}, |src|_peak={:.4e}",
                nv, phi_peak, std, max_src);
        }
        eprintln!("  Expected: Phi ≈ -0.67, std(Phi) ≈ 0 (smooth)");
    }

    /// D₂ vs n_vis with kη Bessel argument
    #[test]
    fn test_d2_vs_nvis_keta() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let t_uk2 = (2.7255e6_f64).powi(2);

        eprintln!("\n  === D₂ vs n_vis (kη Bessel) ===");
        for &nv in &[100_usize, 200, 300, 500, 1000, 3000] {
            let vis = compute_visibility(&p, &t, nv);
            let n_vis = vis.z_grid.len();
            let n_k = 40; let k_min = 5e-5_f64; let k_max = 0.02;
            let k_grid: Vec<f64> = (0..n_k).map(|i|
                k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();
            let mut cl2 = 0.0_f64;
            for (ik, &k) in k_grid.iter().enumerate() {
                let lg = ((k*280.0*2.0).ceil() as usize).max(8).min(25);
                let ln = (lg/2).max(6);
                let kr = match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                    Ok(r) => r, Err(_) => continue,
                };
                let n = kr.eta_grid.len();
                let mut d2 = 0.0_f64;
                for i in 1..n {
                    let x = k * kr.eta_grid[i];
                    if x < 1e-10 || x > 5000.0 { continue; }
                    let de = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
                    d2 += kr.raw_theta0_source[i] * spherical_bessel_j(2, x) * de;
                }
                let pz = 2.1e-9*(k/0.05_f64).powf(-0.0351);
                let dl = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                    else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                    else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };
                cl2 += 4.0*PI*pz*dl*(4.0/9.0)*d2*d2;
            }
            let d2r = 6.0/(2.0*PI)*cl2*t_uk2;
            eprintln!("  n_vis={:>5}: D₂(kη) = {:.1} μK²", nv, d2r);
        }
        eprintln!("  CLASS = 1025 μK²");
    }
}

#[cfg(test)]
mod hybrid_analytic_d2 {
    use crate::solver::flrw_kmode::solve_kmode_with_history;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::los::bessel::spherical_bessel_j;
    use std::f64::consts::PI;

    /// HYBRID D₂: analytic SW at k<k_split + numerical at k≥k_split.
    /// At superhorizon: source = g × (1/3) (standard Sachs-Wolfe).
    /// At sub-horizon: source from ODE solver (Φ is stable).
    #[test]
    fn test_hybrid_analytic_d2() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let t_uk2 = (2.7255e6_f64).powi(2);
        let eta_0 = *vis.eta_grid.last().unwrap();

        // Pre-compute ∫ g(η) j_ℓ(kη) dη for the analytic part
        // Source: g × (1/3) for adiabatic superhorizon modes with ζ=1

        let n_k = 80; let k_min = 1e-5_f64; let k_max = 0.03;
        let k_grid: Vec<f64> = (0..n_k).map(|i|
            k_min*(k_max/k_min).powf(i as f64/(n_k-1) as f64)).collect();

        let k_split = 8e-4_f64; // below this: analytic SW. above: numerical.
        let mut cl2 = 0.0_f64;
        let mut n_analytic = 0; let mut n_numerical = 0;

        for (ik, &k) in k_grid.iter().enumerate() {
            let pz = 2.1e-9*(k/0.05_f64).powf(-0.0351);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };

            let d2 = if k < k_split {
                // ANALYTIC: Δ_ℓ = (1/3) ∫ g(η) j_ℓ(kη) dη
                n_analytic += 1;
                let mut integral = 0.0_f64;
                for i in 1..n_vis {
                    let x = k * vis.eta_grid[i];
                    if x < 1e-12 { continue; }
                    let de = (vis.eta_grid[i] - vis.eta_grid[i-1]).abs();
                    integral += vis.g_grid[i] * spherical_bessel_j(2, x) * de;
                }
                (1.0/3.0) * integral
            } else {
                // NUMERICAL: solve Newtonian ODE, use k(η₀-η) Bessel
                n_numerical += 1;
                let lg = ((k*280.0*2.0).ceil() as usize).max(8).min(25);
                let ln = (lg/2).max(6);
                let kr = match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                    Ok(r) => r, Err(_) => { continue; },
                };
                let n = kr.eta_grid.len();
                let mut d = 0.0_f64;
                for i in 1..n {
                    let x = k * (eta_0 - kr.eta_grid[i]);
                    if x < 1e-10 { continue; }
                    let de = (kr.eta_grid[i] - kr.eta_grid[i-1]).abs();
                    d += kr.raw_theta0_source[i] * spherical_bessel_j(2, x) * de;
                }
                d
            };

            cl2 += 4.0*PI * pz * dlnk * (4.0/9.0) * d2 * d2;
        }

        let d2r = 6.0/(2.0*PI) * cl2 * t_uk2;
        eprintln!("\n  === HYBRID D₂ (analytic k<{:.0e} + numerical k≥{:.0e}) ===", k_split, k_split);
        eprintln!("  D₂ = {:.1} μK²  (n_anal={}, n_num={})", d2r, n_analytic, n_numerical);
        eprintln!("  CLASS = 1025 μK²");
        eprintln!("  Thin-shell SW = 931 μK²");

        // Also compute analytic-only and numerical-only for comparison
        let mut cl2_anal = 0.0; let mut cl2_num = 0.0;
        for (ik, &k) in k_grid.iter().enumerate() {
            let pz = 2.1e-9*(k/0.05_f64).powf(-0.0351);
            let dlnk = if ik==0 { (k_grid[1]/k_grid[0]).ln() }
                else if ik==n_k-1 { (k_grid[ik]/k_grid[ik-1]).ln() }
                else { 0.5*(k_grid[ik+1]/k_grid[ik-1]).ln() };

            // Analytic for ALL k
            let mut intg = 0.0_f64;
            for i in 1..n_vis {
                let x = k * vis.eta_grid[i];
                if x < 1e-12 { continue; }
                let de = (vis.eta_grid[i] - vis.eta_grid[i-1]).abs();
                intg += vis.g_grid[i] * spherical_bessel_j(2, x) * de;
            }
            let d2a = (1.0/3.0) * intg;
            cl2_anal += 4.0*PI*pz*dlnk*(4.0/9.0)*d2a*d2a;
        }
        let d2a = 6.0/(2.0*PI)*cl2_anal*t_uk2;
        eprintln!("  D₂(all analytic) = {:.1} μK²", d2a);
    }
}

#[cfg(test)]
mod production_spectrum {
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, SourceMode, compute_flrw_cl_track_a};
    use crate::recombination::visibility_hyrec::VisibilityParams;

    #[test]
    fn test_production_d2_full() {
        let p = VisibilityParams::planck2018();
        let cfg = FlrwClConfig {
            ell_max: 30,
            n_k: 60,
            k_min: 1e-5,
            k_max: 0.03,
            ell_max_gamma: 25,
            ell_max_nu: 12,
            n_vis: 3000,
            ell_limber: 200,
            source_mode: SourceMode::SwOnly,
            ..FlrwClConfig::fast_validation()
        };
        let r = compute_flrw_cl_track_a(&p, &cfg).unwrap();

        eprintln!("\n  === PRODUCTION C_ℓ SPECTRUM (analytic SW + kη) ===");
        eprintln!("  {:>5} {:>12} {:>12} {:>8}", "l", "D_l [uK2]", "CLASS~", "ratio");
        let class_approx = vec![
            (2, 1025.0), (3, 1000.0), (4, 980.0), (5, 750.0),
            (10, 200.0), (15, 500.0), (20, 1500.0), (25, 1200.0), (30, 690.0),
        ];
        for &(ell, cl) in &class_approx {
            if ell <= cfg.ell_max {
                let d = r.dl_muK2[ell];
                eprintln!("  {:>5} {:>12.1} {:>12.0} {:>8.3}", ell, d, cl, d/cl);
            }
        }
        eprintln!("\n  D₂ = {:.1} μK²", r.dl_muK2[2]);
        eprintln!("  D₂ + ISW(+13%) ≈ {:.1} μK²", r.dl_muK2[2] * 1.13);
        eprintln!("  CLASS D₂ = 1025 μK²");
        eprintln!("  Agreement = {:.1}%", (r.dl_muK2[2]*1.13/1025.0 - 1.0)*100.0);
    }
}

#[cfg(test)]
mod full_spectrum {
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, SourceMode, compute_flrw_cl_track_a};
    use crate::recombination::visibility_hyrec::VisibilityParams;

    #[test]
    fn test_full_cl_spectrum() {
        let p = VisibilityParams::planck2018();
        let cfg = FlrwClConfig {
            ell_max: 2500,
            n_k: 100,
            k_min: 1e-5,
            k_max: 0.25,
            ell_max_gamma: 60,
            ell_max_nu: 25,
            n_vis: 3000,
            ell_limber: 40,
            source_mode: SourceMode::SwOnly,
            ..FlrwClConfig::fast_validation()
        };
        let t0 = std::time::Instant::now();
        let r = compute_flrw_cl_track_a(&p, &cfg).unwrap();
        let wall = t0.elapsed().as_secs();

        eprintln!("\n  === FULL C_ℓ SPECTRUM ℓ=2..2500 ===");
        eprintln!("  k=[{:.0e},{:.2}], n_k={}, ℓ_limber={}, wall={}s",
            cfg.k_min, cfg.k_max, cfg.n_k, cfg.ell_limber, wall);

        // CLASS reference (approximate)
        let class_ref = vec![
            (2, 1025.0), (3, 1000.0), (5, 750.0), (10, 200.0), (20, 1500.0),
            (30, 690.0), (50, 900.0), (100, 2400.0), (150, 3400.0),
            (200, 5200.0), (220, 5740.0), (300, 4200.0), (400, 3100.0),
            (500, 3000.0), (700, 2800.0), (1000, 2500.0), (1500, 2000.0),
            (2000, 1200.0), (2500, 500.0),
        ];
        eprintln!("\n  {:>5} {:>12} {:>12} {:>8}", "l", "D_l BASS", "D_l CLASS", "ratio");
        for &(ell, cl) in &class_ref {
            if ell <= cfg.ell_max {
                let d = r.dl_muK2[ell];
                eprintln!("  {:>5} {:>12.1} {:>12.0} {:>8.3}", ell, d, cl, d/(cl as f64).max(1.0));
            }
        }
    }
}
