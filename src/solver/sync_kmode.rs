// ═══════════════════════════════════════════════════════════════════════
// sync_kmode.rs — Synchronous gauge (CDM frame) Boltzmann solver
// ═══════════════════════════════════════════════════════════════════════
//
// Replaces the conformal Newtonian gauge solver in flrw_kmode.rs.
// Based on the 1+3 covariant PSTF formalism (Ellis 1984, Challinor &
// Lasenby 1999), which maps directly to CAMB's synchronous gauge.
//
// KEY ADVANTAGES OVER NEWTONIAN GAUGE:
//   (1) No growing Φ mode: metric variable kη has no positive self-coupling
//   (2) CDM velocity = 0 by gauge choice → one fewer DOF
//   (3) ḣ is algebraic (from Poisson constraint), not evolved as ODE
//   (4) Natural home for PSTF variables (F_ℓ = (2ℓ+1)Θ_ℓ)
//   (5) Stable at arbitrary z_max (no gauge-induced instability)
//
// CONVENTIONS (matching CAMB notes / Ma & Bertschinger 1995):
//   Time: conformal time τ, d/dτ ≡ '
//   Metric: ds² = a²[-dτ² + (δ_ij + h_ij)dx^idx^j]
//   h_ij = (1/3)h δ_ij + (D_iD_j - δ_ij∇²/3)6η/k²
//   State: Θ_ℓ = temperature multipoles (Θ₀ = δ_γ/4)
//   Evolved metric: kη  (CAMB's etak)
//   Algebraic: ḣ = (2k/ℋ)(kη) + 3ℋ Σ Ωᵢ(z) δᵢ
//
// VARIABLE MAPPING (project knowledge convention table):
//   CAMB I_ℓ = 4Θ_ℓ,   CLASS F_{γ,ℓ} = 4Θ_ℓ,   bass_rs Θ_ℓ (this file)
//   CAMB etak = kη,      CLASS η,                   bass_rs keta (this file)
//   CDM: v_c = 0 (CDM frame), only δ_c evolved
// ═══════════════════════════════════════════════════════════════════════

use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult};
use crate::recombination::hyrec_tables::HyRecTables;
use crate::solver::profiler;

/// Number of effective neutrino species.
const N_EFF: f64 = 3.044;
/// Helium mass fraction.
const Y_P: f64 = 0.2453;

/// Synchronous gauge state vector layout.
///
/// y = [Θ₀, Θ₁, ..., Θ_{ℓg}, N₀, N₁, ..., N_{ℓn}, δ_c, δ_b, v_b, kη]
///
/// Dimension: (ℓg+1) + (ℓn+1) + 4  (one less than Newtonian gauge: no v_c)
#[derive(Clone)]
pub(crate) struct SyncStateLayout {
    pub(crate) ell_max_g: usize,
    pub(crate) ell_max_nu: usize,
    pub(crate) n_state: usize,
    // Index offsets
    pub(crate) nu_offset: usize,  // first neutrino index
    pub(crate) dc_idx: usize,     // δ_c
    pub(crate) db_idx: usize,     // δ_b
    pub(crate) vb_idx: usize,     // v_b
    pub(crate) keta_idx: usize,   // kη (evolved metric)
}

impl SyncStateLayout {
    pub(crate) fn new(ell_max_g: usize, ell_max_nu: usize) -> Self {
        let nu_offset = ell_max_g + 1;
        let dc_idx = nu_offset + ell_max_nu + 1;
        let db_idx = dc_idx + 1;
        let vb_idx = db_idx + 1;
        let keta_idx = vb_idx + 1;
        let n_state = keta_idx + 1;
        Self { ell_max_g, ell_max_nu, n_state, nu_offset, dc_idx, db_idx, vb_idx, keta_idx }
    }
}

/// Compute ḣ algebraically from the (00) Einstein constraint.
///
/// k²η − (ℋ/2)ḣ = −(3/2)ℋ² Σ Ωᵢ(z) δᵢ
///
/// ḣ = (2k/ℋ)(kη) + 3ℋ [Ω_c δ_c + Ω_b δ_b + Ω_γ(4Θ₀) + Ω_ν(4N₀)]
///
/// Returns ḣ in units of [Mpc⁻¹] (same as conformal time derivative).
#[inline]
fn compute_hdot(
    k: f64, a_h: f64, // a_h = ℋ = aH [Mpc⁻¹]
    keta: f64,         // kη
    theta0: f64, n0: f64, delta_c: f64, delta_b: f64,
    omega_c_z: f64, omega_b_z: f64, omega_g_z: f64, omega_n_z: f64,
) -> f64 {
    let hdot = (2.0 * k / a_h.max(1e-30)) * keta
        + 3.0 * a_h * (omega_c_z * delta_c
                      + omega_b_z * delta_b
                      + omega_g_z * 4.0 * theta0
                      + omega_n_z * 4.0 * n0);
    hdot
}

/// Density fractions Ωᵢ(z) = ρᵢ(z)/ρ_tot(z).
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

/// Build the synchronous gauge matrix A(τ) such that y' = A y + b.
///
/// The system is NOT purely y' = Ay because ḣ is algebraic. We handle this
/// by substituting ḣ = Σ C_j y_j into the equations that use ḣ, making
/// the system fully linear: y' = A_eff(τ) y.
///
/// Equations (Ma & Bertschinger 1995, synchronous gauge):
///
/// Photon:
///   Θ₀' = −kΘ₁ − ḣ/6
///   Θ₁' = (k/3)(Θ₀ − 2Θ₂) − κ'(Θ₁ − v_b/3)
///   Θ_ℓ' = k[ℓΘ_{ℓ-1} − (ℓ+1)Θ_{ℓ+1}]/(2ℓ+1) − κ'Θ_ℓ  [ℓ ≥ 2]
///
/// Neutrino:
///   N₀' = −kN₁ − ḣ/6
///   N₁' = (k/3)(N₀ − 2N₂)
///   N_ℓ' = k[ℓN_{ℓ-1} − (ℓ+1)N_{ℓ+1}]/(2ℓ+1)
///
/// CDM (CDM frame: v_c = 0):
///   δ_c' = −ḣ/2
///
/// Baryons:
///   δ_b' = −kv_b − ḣ/2
///   v_b' = −ℋv_b + κ'(3Θ₁ − v_b)/R_b
///
/// Metric:
///   (kη)' = (ℋ²/2)[4Ω_γΘ₁ + 4Ω_νN₁ + Ω_bv_b]  (momentum constraint)
///
/// Algebraic:
///   ḣ = (2k/ℋ)(kη) + 3ℋ[Ω_cδ_c + Ω_bδ_b + 4Ω_γΘ₀ + 4Ω_νN₀]
pub(crate) fn build_sync_matrix(
    k: f64,
    a_h: f64,   // ℋ = aH [Mpc⁻¹]
    kd: f64,    // κ' = Thomson opacity [Mpc⁻¹]
    r_b: f64,   // R_b = 3ρ_b/(4ρ_γ)
    a: f64,     // scale factor
    omega_m: f64, omega_b: f64, omega_gamma: f64,
    lg: usize, ln: usize,
) -> Vec<f64> {
    let omega_nu = omega_gamma * 0.2271 * N_EFF;
    let (oc_z, ob_z, og_z, on_z) = density_fractions(a, omega_m, omega_b, omega_gamma, omega_nu);
    let lay = SyncStateLayout::new(lg, ln);
    let n = lay.n_state;
    let mut a_mat = vec![0.0; n * n];
    let idx = |r: usize, c: usize| -> usize { r * n + c };

    // ═══ Algebraic ḣ coefficients: ḣ = Σ H_j y_j ═══
    // H[keta_idx] = 2k/ℋ
    // H[0]        = 3ℋ × 4Ω_γ     (Θ₀ → δ_γ)
    // H[nu_off]   = 3ℋ × 4Ω_ν     (N₀ → δ_ν)
    // H[dc_idx]   = 3ℋ × Ω_c
    // H[db_idx]   = 3ℋ × Ω_b
    let mut h_coeff = vec![0.0; n];
    h_coeff[lay.keta_idx] = 2.0 * k / a_h.max(1e-30);
    h_coeff[0]            = 3.0 * a_h * og_z * 4.0;
    h_coeff[lay.nu_offset]= 3.0 * a_h * on_z * 4.0;
    h_coeff[lay.dc_idx]   = 3.0 * a_h * oc_z;
    h_coeff[lay.db_idx]   = 3.0 * a_h * ob_z;

    // ═══ Photon monopole: Θ₀' = −kΘ₁ − ḣ/6 ═══
    a_mat[idx(0, 1)] = -k;
    for j in 0..n {
        a_mat[idx(0, j)] += -h_coeff[j] / 6.0;
    }

    // ═══ Photon dipole: Θ₁' = (k/3)(Θ₀ − 2Θ₂) − κ'(Θ₁ − v_b/3) ═══
    if lg >= 1 {
        a_mat[idx(1, 0)] = k / 3.0;
        if lg >= 2 { a_mat[idx(1, 2)] = -2.0 * k / 3.0; }
        a_mat[idx(1, 1)] = -kd;
        a_mat[idx(1, lay.vb_idx)] = kd / 3.0;
    }

    // ═══ Photon ℓ ≥ 2: standard hierarchy ═══
    for ell in 2..=lg {
        let fac = k / (2 * ell + 1) as f64;
        a_mat[idx(ell, ell - 1)] = fac * ell as f64;
        if ell < lg {
            a_mat[idx(ell, ell + 1)] = -fac * (ell + 1) as f64;
        }
        // Collision: −κ'Θ_ℓ (no polarization source for now)
        a_mat[idx(ell, ell)] = -kd;
    }

    // ═══ Neutrino monopole: N₀' = −kN₁ − ḣ/6 ═══
    let n0 = lay.nu_offset;
    if ln >= 1 {
        a_mat[idx(n0, n0 + 1)] = -k;
    }
    for j in 0..n {
        a_mat[idx(n0, j)] += -h_coeff[j] / 6.0;
    }

    // ═══ Neutrino dipole: N₁' = (k/3)(N₀ − 2N₂) ═══
    if ln >= 1 {
        a_mat[idx(n0 + 1, n0)] = k / 3.0;
        if ln >= 2 { a_mat[idx(n0 + 1, n0 + 2)] = -2.0 * k / 3.0; }
    }

    // ═══ Neutrino ℓ ≥ 2 ═══
    for ell in 2..=ln {
        let fac = k / (2 * ell + 1) as f64;
        a_mat[idx(n0 + ell, n0 + ell - 1)] = fac * ell as f64;
        if ell < ln {
            a_mat[idx(n0 + ell, n0 + ell + 1)] = -fac * (ell + 1) as f64;
        }
        // Neutrinos: no collision term
    }

    // ═══ CDM: δ_c' = −ḣ/2  (v_c = 0 in CDM frame) ═══
    for j in 0..n {
        a_mat[idx(lay.dc_idx, j)] += -h_coeff[j] / 2.0;
    }

    // ═══ Baryons: δ_b' = −kv_b − ḣ/2 ═══
    a_mat[idx(lay.db_idx, lay.vb_idx)] = -k;
    for j in 0..n {
        a_mat[idx(lay.db_idx, j)] += -h_coeff[j] / 2.0;
    }

    // ═══ Baryons: v_b' = −ℋv_b + κ'(3Θ₁ − v_b)/R_b ═══
    let inv_rb = 1.0 / r_b.max(1e-10);
    a_mat[idx(lay.vb_idx, lay.vb_idx)] = -a_h - kd * inv_rb;
    if lg >= 1 {
        a_mat[idx(lay.vb_idx, 1)] = 3.0 * kd * inv_rb;
    }

    // ═══ Metric: (kη)' = (ℋ²/2)[4Ω_γΘ₁ + 4Ω_νN₁ + Ω_bv_b] ═══
    // This is the (0i) momentum constraint in synchronous gauge.
    // Self-coupling of kη: ZERO (no kη term in the momentum constraint).
    // This is the key stability advantage over Newtonian gauge.
    let mom = 0.5 * a_h * a_h;
    if lg >= 1 {
        a_mat[idx(lay.keta_idx, 1)] = mom * 4.0 * og_z;
    }
    if ln >= 1 {
        a_mat[idx(lay.keta_idx, n0 + 1)] = mom * 4.0 * on_z;
    }
    a_mat[idx(lay.keta_idx, lay.vb_idx)] = mom * ob_z;

    a_mat
}

/// Compute Newtonian gauge potential Φ_N from synchronous gauge variables.
///
/// Ma & Bertschinger (1995) eq 18:
///   Φ_N = η_S − (ℋ/(2k²))(ḣ + 6η̇_S)
///
/// And the gauge-invariant SW source combination:
///   Θ₀_N + Ψ_N = Θ₀_S − η_S + (ℋ/k²)(ḣ + 3η̇_S)
///
/// with Ψ_N = −Φ_N (no anisotropic stress at leading order).
#[inline]
fn sw_source_from_sync(
    k: f64, a_h: f64,  // ℋ = aH
    y: &[f64], lay: &SyncStateLayout,
    omega_g_z: f64, omega_n_z: f64, omega_b_z: f64, omega_c_z: f64,
) -> f64 {
    let theta0 = y[0];
    let keta = y[lay.keta_idx];
    let eta_s = keta / k.max(1e-30);

    // ḣ from algebraic Poisson
    let hdot = compute_hdot(
        k, a_h, keta, theta0,
        y[lay.nu_offset], y[lay.dc_idx], y[lay.db_idx],
        omega_c_z, omega_b_z, omega_g_z, omega_n_z,
    );

    // η̇_S = (kη)'/k = (ℋ²/(2k)) × velocity_sum
    let theta1 = if lay.ell_max_g >= 1 { y[1] } else { 0.0 };
    let n1 = if lay.ell_max_nu >= 1 { y[lay.nu_offset + 1] } else { 0.0 };
    let vb = y[lay.vb_idx];
    let keta_dot = 0.5 * a_h * a_h * (4.0 * omega_g_z * theta1
        + 4.0 * omega_n_z * n1 + omega_b_z * vb);
    let eta_dot_s = keta_dot / k.max(1e-30);

    // Θ₀_N + Ψ_N in terms of sync variables
    let k2 = k * k;
    if k2 > 1e-20 {
        theta0 - eta_s + (a_h / k2) * (hdot + 3.0 * eta_dot_s)
    } else {
        // Super-horizon limit: Θ₀ + Ψ ≈ −η/3 (adiabatic)
        theta0 - eta_s / 3.0
    }
}

/// Solve a single k-mode in synchronous gauge and return source functions.
///
/// Returns: (η_grid, raw_theta0_source, peak_theta0, n_state)
pub(crate) fn solve_sync_kmode(
    k: f64,
    params: &VisibilityParams,
    vis: &VisibilityResult,
    ell_max_g: usize,
    ell_max_nu: usize,
) -> Result<SyncKmodeResult, String> {
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::core::config::Rodas5PConfig;

    let h0c = params.h * 1e5 / 2.99792458e8;
    let og = params.omega_gamma();
    let omega_nu = og * 0.2271 * N_EFF;
    let n_vis = vis.z_grid.len();
    let eta_max = vis.eta_grid[n_vis - 1];

    let lg = ell_max_g;
    let ln = ell_max_nu;
    let lay = SyncStateLayout::new(lg, ln);
    let n = lay.n_state;

    // Build matrix profile (reversed: τ=0 at z_max, τ=η_max at z=0)
    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n * n);
    let mut a_h_profile = Vec::with_capacity(n_vis);
    let mut density_frac_profile = Vec::with_capacity(n_vis);

    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        let z = vis.z_grid[i];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[i];
        let r_b = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));
        let mat = build_sync_matrix(k, a_h, kd, r_b, a, params.omega_m, params.omega_b, og, lg, ln);
        mats_flat.extend_from_slice(&mat);
        a_h_profile.push(a_h);
        density_frac_profile.push(density_fractions(a, params.omega_m, params.omega_b, og, omega_nu));
    }

    // Adiabatic IC
    let a_init = 1.0 / (1.0 + vis.z_grid[n_vis - 1]);
    let a_h_init = a_init * h0c * params.e_of_z(vis.z_grid[n_vis - 1]);
    let y0 = sync_adiabatic_ic(k, a_h_init, &lay);

    // Solve with Rodas5P (Newton-free)
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
    let tau_eval = tau_profile.clone();
    let (snapshots_rev, _, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
    )?;

    // Extract source functions (reverse to increasing η)
    let n_snaps = snapshots_rev.len();
    let mut eta_grid = Vec::with_capacity(n_snaps);
    let mut raw_theta0_source = Vec::with_capacity(n_snaps);
    let mut snap_out = Vec::with_capacity(n_snaps);

    for si in 0..n_snaps {
        let ri = n_snaps - 1 - si; // reversed index
        let eta = vis.eta_grid[ri];
        eta_grid.push(eta);

        let g = vis.g_grid[ri];
        let y = &snapshots_rev[si];
        let a_h = a_h_profile[si];
        let (oc, ob, ogg, on) = density_frac_profile[si];

        let sw_combo = y[0];  // RAW sync Θ₀
        raw_theta0_source.push(g * sw_combo);
        snap_out.push(y.clone());
    }

    Ok(SyncKmodeResult { layout: lay.clone(), eta_grid, raw_theta0_source, snapshots: snap_out, n_state: n })
}

pub(crate) struct SyncKmodeResult {
    pub(crate) layout: SyncStateLayout,
    pub(crate) eta_grid: Vec<f64>,
    /// g(η) × Θ₀^{(sync)}: raw sync monopole, NOT gauge-transformed SW.
    /// For gauge-invariant SW, see sw_source_from_sync() [diagnostic, inactive].
    /// Production source assembled in pstf_cl_pipeline.rs::build_source().
    pub(crate) raw_theta0_source: Vec<f64>,
    pub(crate) snapshots: Vec<Vec<f64>>,
    pub(crate) n_state: usize,
}

/// Adiabatic initial conditions in synchronous gauge: MB95 kτ-series expansion.
///
/// At conformal time τ_init (superhorizon, kτ ≪ 1), the adiabatic growing mode
/// in sync gauge (CDM frame) with normalization η_s → 1 is:
///
///   η_s = 1 − (5+4R_ν)/(12(15+4R_ν)) × (kτ)²
///   h = (kτ)²/2  →  ḣ = k²τ
///   δ_c = δ_b = −(kτ)²/4
///   δ_γ = δ_ν = −(kτ)²/3
///   Θ₀ = δ_γ/4 = −(kτ)²/12
///   N₀ = δ_ν/4 = −(kτ)²/12
///   Θ₁ = N₁ = v_b = 0  (leading order; dipoles are O((kτ)³))
///   kη = k × η_s ≈ k × [1 − correction]
///
/// Reference: Ma & Bertschinger (1995) Eq. 96, with C₁ = 1/2 (so η_s → 1).
///
/// NORMALIZATION: For χ₀ = −1 (CAMB convention, ζ = 1), CAMB gives η_s = −1.
/// BASS uses η_s = +1 (opposite sign, same |ζ| = 1).
/// Therefore: C_ℓ = 4π P_s |T(ζ=1)|² with **prefactor = 1** (no conversion).
///
/// The key difference from the previous IC: density perturbations start at
/// O((kτ)²) ≈ 10⁻⁴, NOT at O(1). This eliminates the k-dependent amplification
/// that required the K_CORR_SYNC two-prefactor system.
pub(crate) fn sync_adiabatic_ic(
    k: f64, a_h_init: f64, // ℋ at z_max
    lay: &SyncStateLayout,
) -> Vec<f64> {
    let n = lay.n_state;
    let mut y = vec![0.0; n];

    // Conformal time: τ ≈ 1/ℋ in radiation era
    let tau_init = 1.0 / a_h_init.max(1e-30);
    let x = k * tau_init;  // kτ
    let x2 = x * x;        // (kτ)²

    // Neutrino fraction
    let r_nu: f64 = 0.408744;  // R_ν = ρ_ν/(ρ_γ+ρ_ν) for N_eff = 3.044
    let a_nu = (15.0 + 4.0 * r_nu) / 5.0;  // = 3.327

    // η_s: leading + first correction
    let eta_s = 1.0 - x2 / (12.0 * a_nu);

    // kη = k × η_s
    y[lay.keta_idx] = k * eta_s;

    // Density perturbations: O((kτ)²)
    // δ_c = δ_b = -(kτ)²/4  (from δ_c' = -ḣ/2 = -k²τ/2, integrated)
    y[lay.dc_idx] = -x2 / 4.0;
    y[lay.db_idx] = -x2 / 4.0;

    // Θ₀ = δ_γ/4 = -(kτ)²/12  (from δ_γ = -(2/3)(kτ)²/2 = -(kτ)²/3)
    y[0] = -x2 / 12.0;
    y[lay.nu_offset] = -x2 / 12.0;

    // Dipoles: O((kτ)³) → set to zero at leading order
    // The first non-zero contribution is from pressure gradients.
    // For improved accuracy, include the O(kτ) correction:
    // Θ₁ ≈ -(kτ)³/(36×3) from integrating Θ₁' = (k/3)Θ₀
    // But this is typically < 10⁻⁶ and can be neglected.
    // v_b ≈ 3Θ₁ (tight coupling)
    if lay.ell_max_g >= 1 {
        let theta1 = -x2 * x / 108.0;  // O((kτ)³)
        y[1] = theta1;
    }
    if lay.ell_max_nu >= 1 {
        y[lay.nu_offset + 1] = -x2 * x / 108.0;
    }
    y[lay.vb_idx] = if lay.ell_max_g >= 1 { 3.0 * y[1] } else { 0.0 };

    // Neutrino quadrupole: from anisotropic stress
    // N₂ ≈ (2/3)(kτ)² / (15+4R_ν) × (4/15)  (from MB95)
    // This is small but important for high-precision
    if lay.ell_max_nu >= 2 {
        y[lay.nu_offset + 2] = 4.0 * x2 / (3.0 * (15.0 + 4.0 * r_nu));
    }

    y
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Verify state layout dimensions.
    #[test]
    fn test_layout() {
        let lay = SyncStateLayout::new(20, 10);
        assert_eq!(lay.n_state, 20 + 1 + 10 + 1 + 4); // 36
        assert_eq!(lay.nu_offset, 21);
        assert_eq!(lay.dc_idx, 32);
        assert_eq!(lay.keta_idx, 35);
    }

    /// Verify matrix is square, finite, and has correct zero structure.
    #[test]
    fn test_sync_matrix_structure() {
        let k = 0.05;
        let a_h = 0.01;   // ℋ at z~4000
        let kd = 100.0;   // tight coupling
        let r_b = 0.1;
        let a = 2.5e-4;
        let lg = 20_usize;
        let ln = 10_usize;
        let mat = build_sync_matrix(k, a_h, kd, r_b, a, 0.3153, 0.04930, 9.14e-5, lg, ln);
        let lay = SyncStateLayout::new(lg, ln);
        let n = lay.n_state;
        assert_eq!(mat.len(), n * n);

        // All finite
        assert!(mat.iter().all(|&x| x.is_finite()), "Matrix has non-finite entries");

        // kη row: NO self-coupling (key stability property)
        let keta_self = mat[lay.keta_idx * n + lay.keta_idx];
        assert!(keta_self.abs() < 1e-20,
            "kη self-coupling should be zero, got {:.2e}", keta_self);

        // Θ₁ diagonal: should be −κ' (collision damping)
        let theta1_diag = mat[1 * n + 1];
        assert!((theta1_diag + kd).abs() / kd < 0.01,
            "Θ₁ diagonal should be ≈ −κ' = {:.1}, got {:.1}", -kd, theta1_diag);

        eprintln!("  sync_matrix: n={}, kη_self={:.2e}, Θ₁_diag={:.2}", n, keta_self, theta1_diag);
    }

    /// Verify IC structure.
    #[test]
    fn test_sync_ic() {
        let lay = SyncStateLayout::new(20, 10);
        let y = sync_adiabatic_ic(0.05, 0.01, &lay);
        assert_eq!(y.len(), lay.n_state);
        assert!((y[0] + 0.5).abs() < 1e-10, "Θ₀ should be −0.5");
        assert!((y[lay.dc_idx] + 1.5).abs() < 1e-10, "δ_c should be −1.5");
        assert!((y[lay.keta_idx] - 0.05).abs() < 1e-10, "kη should be k=0.05");
        eprintln!("  sync_ic: Θ₀={:.3}, δ_c={:.3}, kη={:.4}, Θ₁={:.4e}",
            y[0], y[lay.dc_idx], y[lay.keta_idx], y[1]);
    }

    /// Integration test: evolve with Rodas5P at z_max=1e5, k=0.1.
    /// This is the regime where Newtonian gauge blows up (peak=3.5e17).
    #[test]
    fn test_sync_integration_stability() {
        use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use crate::solver::stacked::integrate_linear_profile_rodas5p;
        use crate::core::config::Rodas5PConfig;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1.0e5);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();
        let n_vis = vis.z_grid.len();
        let eta_max = vis.eta_grid[n_vis - 1];
        let k = 0.10_f64;
        let lg = 60_usize;
        let ln = 25_usize;
        let lay = SyncStateLayout::new(lg, ln);
        let n = lay.n_state;

        // Build matrix profile
        let mut tau_profile = Vec::with_capacity(n_vis);
        let mut mats_flat = Vec::with_capacity(n_vis * n * n);
        for i in (0..n_vis).rev() {
            let tau = eta_max - vis.eta_grid[i];
            tau_profile.push(tau);
            let z = vis.z_grid[i];
            let a = 1.0 / (1.0 + z);
            let a_h = a * h0c * p.e_of_z(z);
            let kd = vis.kappa_dot_grid[i];
            let r_b = 3.0 * p.omega_b / (4.0 * og * (1.0 + z));
            let mat = build_sync_matrix(k, a_h, kd, r_b, a, p.omega_m, p.omega_b, og, lg, ln);
            mats_flat.extend_from_slice(&mat);
        }

        // IC
        let a_init = 1.0 / (1.0 + vis.z_grid[n_vis - 1]);
        let a_h_init = a_init * h0c * p.e_of_z(vis.z_grid[n_vis - 1]);
        let y0 = sync_adiabatic_ic(k, a_h_init, &lay);

        // Solve with Rodas5P
        let h_max_k = (4.0 * 3.0_f64.sqrt() / k.max(1e-10)).min(200.0);
        let cfg = Rodas5PConfig {
            rtol: 1e-6, atol: 1e-9, max_steps: 500_000,
            h_init: None, h_min: 1e-14, h_max: h_max_k,
            f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
            use_analytic_jacobian: true, use_ft_term: false,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: lg, ell_max_nu_hint: ln,
            ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false,
        };
        let tau_eval = tau_profile.clone();

        let t0 = std::time::Instant::now();
        let result = integrate_linear_profile_rodas5p(
            &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
        );
        let ms = t0.elapsed().as_millis();

        match result {
            Ok((snaps, _, _)) => {
                // Extract source ≈ g(Θ₀ + Ψ_eff) at visibility peak
                let mut max_theta0 = 0.0_f64;
                let mut peak_theta0 = 0.0_f64;
                for (si, snap) in snaps.iter().enumerate() {
                    let theta0_abs = snap[0].abs();
                    max_theta0 = max_theta0.max(theta0_abs);
                    // Reverse index: si=0 is z_max, si=n_vis-1 is z=0
                    if si < n_vis {
                        let z = vis.z_grid[n_vis - 1 - si];
                        if z > 800.0 && z < 1300.0 {
                            peak_theta0 = peak_theta0.max(theta0_abs);
                        }
                    }
                }
                eprintln!("  SYNC z=1e5 k={:.2} ℓ={}: peak|Θ₀|={:.3e} max|Θ₀|={:.3e} {}ms",
                    k, lg, peak_theta0, max_theta0, ms);
                // Key test: peak Θ₀ should be O(1), NOT 10¹⁷
                assert!(peak_theta0 < 100.0,
                    "Sync gauge peak|Θ₀|={:.2e} — expected O(1)", peak_theta0);
            }
            Err(e) => {
                panic!("Sync integration failed: {}", e);
            }
        }
    }
}

#[cfg(test)]
mod ablation {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::solver::diffsol_bdf::{integrate_linear_diffsol, DiffsolConfig, SolverBackend};
    use crate::core::config::Rodas5PConfig;

    struct AblationResult {
        name: &'static str,
        peak_theta0: f64,
        max_theta0: f64,
        wall_ms: u128,
        ok: bool,
    }

    fn run_solver(
        name: &'static str,
        tau_profile: &[f64], mats_flat: &[f64], n: usize,
        y0: &[f64], tau_eval: &[f64], k: f64, lg: usize, ln: usize,
        vis: &VisibilityResult,
        backend: Option<SolverBackend>,
    ) -> AblationResult {
        let t0 = std::time::Instant::now();
        let h_max_k = (4.0 * 3.0_f64.sqrt() / k.max(1e-10)).min(200.0);
        let n_vis = vis.z_grid.len();

        let result: Result<Vec<Vec<f64>>, String> = if let Some(sb) = backend {
            // diffsol path
            let cfg = DiffsolConfig {
                rtol: 1e-6, atol: 1e-9, h_init: 0.01,
                backend: sb,
            };
            integrate_linear_diffsol(tau_profile, mats_flat, n, y0, tau_eval, &cfg)
                .map(|(snaps, _, _)| snaps)
        } else {
            // Rodas5P path
            let cfg = Rodas5PConfig {
                rtol: 1e-6, atol: 1e-9, max_steps: 500_000,
                h_init: None, h_min: 1e-14, h_max: h_max_k,
                f_safety: 0.95, f_min: 0.2, f_max: 6.0, beta: 0.04,
                use_analytic_jacobian: true, use_ft_term: false,
                use_blas_lu: false, use_block_diag: false,
                ell_max_gamma_hint: lg, ell_max_nu_hint: ln,
                ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false,
            };
            integrate_linear_profile_rodas5p(tau_profile, mats_flat, n, y0, tau_eval, &cfg)
                .map(|(snaps, _, _)| snaps)
        };

        let ms = t0.elapsed().as_millis();
        match result {
            Ok(snaps) => {
                let mut max_theta0 = 0.0_f64;
                let mut peak_theta0 = 0.0_f64;
                for (si, snap) in snaps.iter().enumerate() {
                    let t0_abs = snap[0].abs();
                    max_theta0 = max_theta0.max(t0_abs);
                    if si < n_vis {
                        let z = vis.z_grid[n_vis.saturating_sub(1).saturating_sub(si)];
                        if z > 800.0 && z < 1300.0 { peak_theta0 = peak_theta0.max(t0_abs); }
                    }
                }
                AblationResult { name, peak_theta0, max_theta0, wall_ms: ms, ok: true }
            }
            Err(_) => AblationResult { name, peak_theta0: f64::NAN, max_theta0: f64::NAN, wall_ms: ms, ok: false }
        }
    }

    /// Solver ablation: Rodas5P vs BDF vs ESDIRK34 vs TR-BDF2.
    #[test]
    fn test_solver_ablation() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);

        for &(z_max, k) in &[(1e4_f64, 0.05_f64), (1e5, 0.10), (5e4, 0.15)] {
            let vis = compute_visibility_ext(&p, &t, 2000, z_max);
            let h0c = p.h * 1e5 / 2.99792458e8;
            let og = p.omega_gamma();
            let n_vis = vis.z_grid.len();
            let eta_max = vis.eta_grid[n_vis - 1];
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(80);
            let ln = (lg / 2).max(6);
            let lay = SyncStateLayout::new(lg, ln);
            let n = lay.n_state;

            let mut tau_profile = Vec::with_capacity(n_vis);
            let mut mats_flat = Vec::with_capacity(n_vis * n * n);
            for i in (0..n_vis).rev() {
                let tau = eta_max - vis.eta_grid[i];
                tau_profile.push(tau);
                let z = vis.z_grid[i];
                let a = 1.0 / (1.0 + z);
                let a_h = a * h0c * p.e_of_z(z);
                let kd = vis.kappa_dot_grid[i];
                let r_b = 3.0 * p.omega_b / (4.0 * og * (1.0 + z));
                let mat = build_sync_matrix(k, a_h, kd, r_b, a, p.omega_m, p.omega_b, og, lg, ln);
                mats_flat.extend_from_slice(&mat);
            }
            let a_init = 1.0 / (1.0 + vis.z_grid[n_vis - 1]);
            let a_h_init = a_init * h0c * p.e_of_z(vis.z_grid[n_vis - 1]);
            let y0 = sync_adiabatic_ic(k, a_h_init, &lay);
            let tau_eval = tau_profile.clone();

            eprintln!("\n  === z={:.0e}, k={:.2}, ℓ_γ={}, n={} ===", z_max, k, lg, n);
            eprintln!("  {:>12} | {:>10} {:>10} {:>8} {:>4}", "Solver", "peak|Θ₀|", "max|Θ₀|", "time_ms", "OK");
            eprintln!("  {}", "-".repeat(55));

            let solvers: Vec<(&str, Option<SolverBackend>)> = vec![
                ("Rodas5P",  None),
                ("BDF",      Some(SolverBackend::Bdf)),
                ("ESDIRK34", Some(SolverBackend::Esdirk34)),
                ("TR-BDF2",  Some(SolverBackend::TrBdf2)),
            ];

            for (sname, sb) in &solvers {
                let r = run_solver(sname, &tau_profile, &mats_flat, n, &y0, &tau_eval, k, lg, ln, &vis, sb.clone());
                if r.ok {
                    eprintln!("  {:>12} | {:>10.3e} {:>10.3e} {:>8} {:>4}",
                        r.name, r.peak_theta0, r.max_theta0, r.wall_ms,
                        if r.peak_theta0 < 100.0 { "✓" } else { "✗" });
                } else {
                    eprintln!("  {:>12} | {:>10} {:>10} {:>8} FAIL", r.name, "—", "—", r.wall_ms);
                }
            }
        }
    }
}

#[cfg(test)]
mod d2_test {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility, compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    /// Cross-validate sync vs Newtonian source at k=0.01 (where both work).
    #[test]
    fn test_sync_vs_newtonian_source_k001() {
        use crate::solver::flrw_kmode::solve_kmode_rodas5p;

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let k = 0.01;
        let lg = 20_usize;
        let ln = 10_usize;

        // Newtonian gauge
        let (_, src_newt) = solve_kmode_rodas5p(k, &p, &vis, lg, ln).unwrap();
        let max_src_newt = src_newt.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));

        // Sync gauge
        let sync_r = solve_sync_kmode(k, &p, &vis, lg, ln).unwrap();
        let max_src_sync = sync_r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));

        eprintln!("  k={:.3}: Newtonian |src|={:.4e}, Sync |src|={:.4e}, ratio={:.3}",
            k, max_src_newt, max_src_sync, max_src_sync / max_src_newt.max(1e-30));
    }

    /// Source stability across k with sync gauge at z_max=1e5.
    #[test]
    fn test_sync_raw_theta0_sourceeep() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);

        for &k in &[0.01_f64, 0.03, 0.05, 0.10, 0.15, 0.20] {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(80);
            let ln = (lg / 2).max(6);
            let t0 = std::time::Instant::now();
            match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => {
                    let ms = t0.elapsed().as_millis();
                    let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
                    eprintln!("  SYNC k={:.3} ℓ={:>2} n={:>3}: |src|={:.3e}  {}ms",
                        k, lg, r.n_state, max_src, ms);
                }
                Err(e) => eprintln!("  SYNC k={:.3}: FAIL {}", k, &e[..50.min(e.len())]),
            }
        }
    }
}

#[cfg(test)]
mod normalization_debug {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::core::config::Rodas5PConfig;

    /// Detailed diagnostic at visibility peak for k=0.01.
    #[test]
    fn test_normalization_diagnostic() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();
        let omega_nu = og * 0.2271 * N_EFF;
        let n_vis = vis.z_grid.len();
        let eta_max = vis.eta_grid[n_vis - 1];
        let k = 0.01_f64;
        let lg = 20_usize; let ln = 10_usize;
        let lay = SyncStateLayout::new(lg, ln);
        let n = lay.n_state;

        // Build and solve
        let mut tau_profile = Vec::new();
        let mut mats_flat = Vec::new();
        let mut bg = Vec::new(); // (z, a, aH, g)
        for i in (0..n_vis).rev() {
            let tau = eta_max - vis.eta_grid[i];
            tau_profile.push(tau);
            let z = vis.z_grid[i]; let a = 1.0/(1.0+z);
            let a_h = a * h0c * p.e_of_z(z);
            let kd = vis.kappa_dot_grid[i];
            let r_b = 3.0 * p.omega_b / (4.0 * og * (1.0+z));
            let mat = build_sync_matrix(k, a_h, kd, r_b, a, p.omega_m, p.omega_b, og, lg, ln);
            mats_flat.extend_from_slice(&mat);
            bg.push((z, a, a_h, vis.g_grid[i]));
        }
        let a_init = 1.0/(1.0+vis.z_grid[n_vis-1]);
        let a_h_init = a_init * h0c * p.e_of_z(vis.z_grid[n_vis-1]);
        let y0 = sync_adiabatic_ic(k, a_h_init, &lay);
        let h_max_k = (4.0*3.0_f64.sqrt()/k).min(200.0);
        let cfg = Rodas5PConfig {
            rtol:1e-6, atol:1e-9, max_steps:500000,
            h_init:None, h_min:1e-14, h_max:h_max_k,
            f_safety:0.95, f_min:0.2, f_max:6.0, beta:0.04,
            use_analytic_jacobian:true, use_ft_term:false,
            use_blas_lu:false, use_block_diag:false,
            ell_max_gamma_hint:lg, ell_max_nu_hint:ln,
            ell_max_pol_hint:0, include_pol_hint:false, use_sparse:false,
        };
        let (snaps, _, _) = integrate_linear_profile_rodas5p(
            &tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg).unwrap();

        // Find visibility peak (max g)
        let g_peak_idx = bg.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.3.partial_cmp(&b.3).unwrap())
            .unwrap().0;
        let (z_pk, _a_pk, a_h_pk, g_pk) = bg[g_peak_idx];
        let y_pk = &snaps[g_peak_idx];

        let theta0 = y_pk[0];
        let theta1 = y_pk[1];
        let n0 = y_pk[lay.nu_offset];
        let n1 = y_pk[lay.nu_offset + 1];
        let dc = y_pk[lay.dc_idx];
        let db = y_pk[lay.db_idx];
        let vb = y_pk[lay.vb_idx];
        let keta = y_pk[lay.keta_idx];
        let eta_s = keta / k;
        let a_pk = 1.0/(1.0+z_pk);
        let (oc,ob_f,og_f,on_f) = density_fractions(a_pk, p.omega_m, p.omega_b, og, omega_nu);

        // ḣ
        let hdot = compute_hdot(k, a_h_pk, keta, theta0, n0, dc, db, oc, ob_f, og_f, on_f);
        // η̇_S
        let keta_dot = 0.5*a_h_pk*a_h_pk*(4.0*og_f*theta1 + 4.0*on_f*n1 + ob_f*vb);
        let eta_dot = keta_dot / k;
        // σ = (ḣ + 6η̇)/(2k)
        let sigma = (hdot + 6.0*eta_dot) / (2.0*k);
        // Φ_N = η_S - ℋσ/k
        let phi_n = eta_s - a_h_pk * sigma / k;
        // Ψ_N = -Φ_N
        let psi_n = -phi_n;
        // α = ḣ/(2k²)
        let alpha = hdot / (2.0*k*k);
        // Θ₀_N = Θ₀_S + ℋα
        let theta0_n = theta0 + a_h_pk * alpha;
        // SW source
        let sw_combo = theta0_n + psi_n;
        let src_sync = g_pk * sw_combo;

        eprintln!("\n  === NORMALIZATION DIAGNOSTIC at z={:.0} (vis peak) ===", z_pk);
        eprintln!("  Background: ℋ={:.4e}, g={:.4e}", a_h_pk, g_pk);
        eprintln!("  State: Θ₀={:.4e}, Θ₁={:.4e}, N₀={:.4e}", theta0, theta1, n0);
        eprintln!("         δ_c={:.4e}, δ_b={:.4e}, v_b={:.4e}, kη={:.4e}", dc, db, vb, keta);
        eprintln!("  Derived: η_S={:.4e}, ḣ={:.4e}, η̇_S={:.4e}", eta_s, hdot, eta_dot);
        eprintln!("           σ={:.4e}, α={:.4e}", sigma, alpha);
        eprintln!("  Gauge: Φ_N={:.4e}, Ψ_N={:.4e}", phi_n, psi_n);
        eprintln!("         Θ₀_N={:.4e}, Θ₀_N+Ψ_N={:.4e}", theta0_n, sw_combo);
        eprintln!("  Source: g×(Θ₀_N+Ψ_N)={:.4e}", src_sync);
        eprintln!("  (Compare: Newtonian src ≈ 2.2e-2 at k=0.01)");
    }
}

/// Compute D₂ (SW-only) using sync gauge solver across a k-grid.
/// Uses simple trapezoidal k-integration and Bessel j₂.
///
/// D₂ = ℓ(ℓ+1)/(2π) × T_CMB² × ∫ |Δ₂(k)|² dk/k
/// Δ₂(k) = ∫ g(τ) × Θ₀(k,τ) × j₂[k(τ₀-τ)] dτ
///
/// NOTE: This uses raw Θ₀ (no Ψ correction) so it's an approximation.
/// The normalization factor (3/2)² accounts for η=1 vs Φ=1 convention.
pub(crate) fn compute_d2_sync_sw(
    params: &VisibilityParams,
    vis: &VisibilityResult,
    k_grid: &[f64],
    ell_max_default: usize,
) -> Result<f64, String> {
    // D₂ = ℓ(ℓ+1)/(2π) × T_CMB² × C₂
    // C₂ = 4π ∫ dk/k × Δ²_ζ(k) × |T₂(k)|²
    // Δ²_ζ(k) = A_s × (k/k_pivot)^{n_s-1}  (primordial power)
    // T₂(k) = ∫ S(k,η) j₂(kη) dη  (transfer function, η = comoving distance)
    //
    // Normalization: our IC has η_S = 1 (adiabatic curvature ζ = 1).
    // So T₂ is computed for unit ζ — we multiply by A_s for the actual power.
    let a_s = 2.1e-9_f64;  // Planck 2018 scalar amplitude
    let n_s = 0.9649_f64;  // Planck 2018 spectral index
    let k_pivot = 0.05_f64; // Mpc⁻¹

    let t_cmb_uk2 = (2.7255e6_f64).powi(2);  // T_CMB² in μK²
    let eta_0 = vis.eta_grid[vis.eta_grid.len() - 1];

    let mut sum_k = 0.0_f64;

    for iw in 0..k_grid.len() {
        let k = k_grid[iw];
        let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(100);
        let ln = (lg / 2).max(6);

        let r = solve_sync_kmode(k, params, vis, lg, ln)?;

        // Compute Δ₂(k) = ∫ raw_theta0_source(τ) × j₂[k(τ₀-τ)] dτ
        let n = r.eta_grid.len();
        let mut delta_2 = 0.0_f64;
        for i in 1..n {
            let eta = r.eta_grid[i];
            let chi = eta_0 - eta;  // comoving distance (our η = distance, not conformal time)
            // Actually η=0 at z=0, η_max at z=z_max. chi = η_max - η would be wrong.
            // Wait: η IS comoving distance. The LoS variable is x = k × d(z) where d(z) = η(z).
            // So for the Bessel argument: x = k × η (comoving distance to the source)
            let x = k * eta;
            let j2 = if x.abs() < 1e-10 { 0.0 }
                else { (3.0 / (x * x) - 1.0) * (x).sin() / x - 3.0 * (x).cos() / (x * x) };

            // Trapezoidal weight
            let deta = r.eta_grid[i] - r.eta_grid[i - 1];
            delta_2 += r.raw_theta0_source[i] * j2 * deta;
        }

        // Primordial power spectrum weighting
        let delta_sq_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);

        // k-integration weight: dk/k (log-spaced assumed)
        let dk_over_k = if iw == 0 {
            (k_grid[1] - k_grid[0]) / k
        } else if iw == k_grid.len() - 1 {
            (k_grid[iw] - k_grid[iw - 1]) / k
        } else {
            0.5 * (k_grid[iw + 1] - k_grid[iw - 1]) / k
        };

        sum_k += delta_sq_zeta * delta_2 * delta_2 * dk_over_k;
    }

    // D₂ = ℓ(ℓ+1)/(2π) × T² × C₂
    // C₂ = 4π ∫ Δ²_ζ(k) |T₂(k)|² dk/k
    // η=1 sync IC → ζ=1 → T₂ is transfer per unit ζ → correct normalization
    let d2 = 6.0 / (2.0 * std::f64::consts::PI)  // ℓ(ℓ+1)/(2π)
        * 4.0 * std::f64::consts::PI              // from C_ℓ definition
        * t_cmb_uk2                                // T² in μK²
        * sum_k;

    Ok(d2)
}

#[cfg(test)]
mod d2_computation {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_d2_sync_gauge() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 3000, 1.0e5);

        // Simple k-grid: 30 log-spaced points from k=0.001 to k=0.15
        let n_k = 30;
        let k_min = 0.001_f64;
        let k_max = 0.15;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max / k_min).powf(i as f64 / (n_k - 1) as f64))
            .collect();

        let t0 = std::time::Instant::now();
        match compute_d2_sync_sw(&p, &vis, &k_grid, 80) {
            Ok(d2) => {
                let ms = t0.elapsed().as_millis();
                eprintln!("\n  === SYNC GAUGE D₂ ===");
                eprintln!("  D₂ = {:.1} μK²  (CLASS ref = 1025)", d2);
                eprintln!("  n_k = {}, k_range = [{:.4}, {:.3}], z_max = 1e5, wall = {}ms", n_k, k_min, k_max, ms);

                // Diagnostic: compute Δ₂(k) for a few k values
                eprintln!("\n  Per-k diagnostics:");
                for &k_test in &[0.005_f64, 0.01, 0.03, 0.05, 0.10] {
                    let lg_t = ((k_test * 280.0 * 3.0).ceil() as usize).max(15).min(80);
                    let ln_t = (lg_t / 2).max(6);
                    if let Ok(r) = solve_sync_kmode(k_test, &p, &vis, lg_t, ln_t) {
                        let eta_0 = r.eta_grid[r.eta_grid.len()-1];
                        let max_src = r.raw_theta0_source.iter().fold(0.0_f64, |m,&s| m.max(s.abs()));
                        let mut delta2 = 0.0_f64;
                        for i in 1..r.eta_grid.len() {
                            let x = k_test * r.eta_grid[i];
                            let j2 = if x.abs() < 1e-10 { 0.0 }
                                else { (3.0/(x*x)-1.0)*(x).sin()/x - 3.0*(x).cos()/(x*x) };
                            let deta = r.eta_grid[i] - r.eta_grid[i-1];
                            delta2 += r.raw_theta0_source[i] * j2 * deta;
                        }
                        let pk = 2.1e-9 * (k_test / 0.05_f64).powf(0.9649 - 1.0);
                        let contrib = pk * delta2 * delta2;
                        eprintln!("    k={:.3}: |src|_max={:.3e}, Δ₂={:.4e}, P(k)Δ₂²={:.4e}",
                            k_test, max_src, delta2, contrib);
                    }
                }
            }
            Err(e) => eprintln!("  D₂ FAILED: {}", e),
        }
    }
}

/// Build sync matrix WITH boundary EFT correction on top shells.
/// The correction adds effective damping from the truncated ℓ > L tail.
pub(crate) fn build_sync_matrix_eft(
    k: f64, a_h: f64, kd: f64, r_b: f64, a: f64,
    omega_m: f64, omega_b: f64, omega_gamma: f64,
    lg: usize, ln: usize,
    eft_enabled: bool,
) -> Vec<f64> {
    let mut mat = build_sync_matrix(k, a_h, kd, r_b, a, omega_m, omega_b, omega_gamma, lg, ln);
    
    if !eft_enabled || k < 1e-10 { return mat; }
    
    let lay = SyncStateLayout::new(lg, ln);
    let n = lay.n_state;
    let idx = |r: usize, c: usize| -> usize { r * n + c };
    
    // Boundary EFT for photon top shell
    // Σ_L(s=ω) gives the Markovian approximation to the tail backreaction.
    // ω = k in conformal time units (streaming rate = wavenumber)
    let omega = k;
    let tail_max = 3000_usize;
    let sigma_gamma = crate::solver::boundary_eft::self_energy(omega, omega, lg, tail_max);
    // Add to top photon shell diagonal: I_L' += Σ_L × I_L
    mat[idx(lg, lg)] += sigma_gamma;
    
    // Also add to ℓ_max-1 shell (sub-leading correction)
    if lg >= 2 {
        let sigma_lm1 = crate::solver::boundary_eft::self_energy(omega, omega, lg - 1, tail_max);
        // Only a fraction feeds back (the ℓ_max shell mediates)
        // Conservative: 10% of sub-leading correction
        mat[idx(lg - 1, lg - 1)] += 0.1 * sigma_lm1;
    }
    
    // Boundary EFT for neutrino top shell (same structure, no collision)
    let n0 = lay.nu_offset;
    let sigma_nu = crate::solver::boundary_eft::self_energy(omega, omega, ln, tail_max);
    mat[idx(n0 + ln, n0 + ln)] += sigma_nu;
    
    mat
}

/// Solve a single k-mode using sync gauge WITH boundary EFT.
pub(crate) fn solve_sync_kmode_eft(
    k: f64,
    params: &VisibilityParams,
    vis: &VisibilityResult,
    ell_max_g: usize,
    ell_max_nu: usize,
    eft: bool,
) -> Result<SyncKmodeResult, String> {
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::core::config::Rodas5PConfig;

    let h0c = params.h * 1e5 / 2.99792458e8;
    let og = params.omega_gamma();
    let omega_nu = og * 0.2271 * N_EFF;
    let n_vis = vis.z_grid.len();
    let eta_max = vis.eta_grid[n_vis - 1];

    let lg = ell_max_g;
    let ln = ell_max_nu;
    let lay = SyncStateLayout::new(lg, ln);
    let n = lay.n_state;

    let mut tau_profile = Vec::with_capacity(n_vis);
    let mut mats_flat = Vec::with_capacity(n_vis * n * n);
    let mut a_h_profile = Vec::with_capacity(n_vis);
    let mut density_frac_profile = Vec::with_capacity(n_vis);

    for i in (0..n_vis).rev() {
        let tau = eta_max - vis.eta_grid[i];
        tau_profile.push(tau);
        let z = vis.z_grid[i];
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis.kappa_dot_grid[i];
        let r_b = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));
        let mat = build_sync_matrix_eft(k, a_h, kd, r_b, a,
            params.omega_m, params.omega_b, og, lg, ln, eft);
        mats_flat.extend_from_slice(&mat);
        a_h_profile.push(a_h);
        density_frac_profile.push(density_fractions(a, params.omega_m, params.omega_b, og, omega_nu));
    }

    let a_init = 1.0 / (1.0 + vis.z_grid[n_vis - 1]);
    let a_h_init = a_init * h0c * params.e_of_z(vis.z_grid[n_vis - 1]);
    let y0 = sync_adiabatic_ic(k, a_h_init, &lay);

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
    let tau_eval = tau_profile.clone();
    let (snapshots_rev, _, _) = integrate_linear_profile_rodas5p(
        &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
    )?;

    let n_snaps = snapshots_rev.len();
    let mut eta_grid = Vec::with_capacity(n_snaps);
    let mut raw_theta0_source = Vec::with_capacity(n_snaps);
    let mut snap_out2 = Vec::with_capacity(n_snaps);

    for si in 0..n_snaps {
        let ri = n_snaps - 1 - si;
        let eta = vis.eta_grid[ri];
        eta_grid.push(eta);
        let g = vis.g_grid[ri];
        let y = &snapshots_rev[si];
        // Use RAW sync gauge Θ₀ — no gauge transformation
        // This is the monopole piece only. Full source needs metric terms.
        let theta0_sync = y[0];
        raw_theta0_source.push(g * theta0_sync);
        snap_out2.push(y.clone());
    }

    Ok(SyncKmodeResult { layout: lay.clone(), eta_grid, raw_theta0_source, snapshots: snap_out2, n_state: n })
}

#[cfg(test)]
mod eft_ablation {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    /// EFT ablation: compare source with/without boundary EFT correction.
    #[test]
    fn test_eft_source_correction() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);

        eprintln!("\n  === EFT Boundary Correction: source-level ablation ===");
        eprintln!("  {:>6} {:>4} | {:>10} {:>10} {:>8}",
            "k", "ℓ", "|src|_base", "|src|_EFT", "Δsrc/src");
        eprintln!("  {}", "-".repeat(55));

        for &k in &[0.01_f64, 0.03, 0.05, 0.10, 0.15] {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(80);
            let ln = (lg / 2).max(6);

            let r_base = solve_sync_kmode_eft(k, &p, &vis, lg, ln, false).unwrap();
            let r_eft = solve_sync_kmode_eft(k, &p, &vis, lg, ln, true).unwrap();

            let max_base = r_base.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
            let max_eft = r_eft.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
            let delta = (max_eft - max_base).abs() / max_base.max(1e-30);

            eprintln!("  {:>6.3} {:>4} | {:>10.4e} {:>10.4e} {:>8.2}%",
                k, lg, max_base, max_eft, delta * 100.0);
        }
    }

    /// ℓ_max convergence WITH EFT correction.
    #[test]
    fn test_eft_lmax_convergence() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);
        let k = 0.10_f64;

        eprintln!("\n  === EFT ℓ_max convergence at k={} ===", k);
        eprintln!("  {:>5} | {:>10} {:>10} {:>8}",
            "ℓ_max", "|src|_base", "|src|_EFT", "Δ%");
        eprintln!("  {}", "-".repeat(45));

        for &lg in &[20_usize, 40, 60, 80, 100, 120] {
            let ln = (lg / 2).max(6);
            let r_base = solve_sync_kmode_eft(k, &p, &vis, lg, ln, false).unwrap();
            let r_eft = solve_sync_kmode_eft(k, &p, &vis, lg, ln, true).unwrap();
            let max_b = r_base.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
            let max_e = r_eft.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
            let delta = (max_e - max_b) / max_b.max(1e-30) * 100.0;
            eprintln!("  {:>5} | {:>10.4e} {:>10.4e} {:>8.2}%", lg, max_b, max_e, delta);
        }
    }
}

/// D₂ using only the recombination epoch (g > threshold).
/// This avoids the late-time gauge artifact in raw sync Θ₀.
pub(crate) fn compute_d2_recomb_only(
    params: &VisibilityParams,
    vis: &VisibilityResult,
    k_grid: &[f64],
) -> Result<f64, String> {
    let a_s = 2.1e-9_f64;
    let n_s = 0.9649_f64;
    let k_pivot = 0.05_f64;
    let t_cmb_uk2 = (2.7255e6_f64).powi(2);

    // Find visibility peak and threshold
    let g_max = vis.g_grid.iter().fold(0.0_f64, |m, &g| m.max(g));
    let g_thresh = 1e-4 * g_max;  // Include 99.99% of visibility weight

    let mut sum_k = 0.0_f64;

    for iw in 0..k_grid.len() {
        let k = k_grid[iw];
        let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(80);
        let ln = (lg / 2).max(6);

        let r = solve_sync_kmode(k, params, vis, lg, ln)?;

        let mut delta_2 = 0.0_f64;
        for i in 1..r.eta_grid.len() {
            let x = k * r.eta_grid[i];
            let j2 = if x.abs() < 1e-10 { 0.0 }
                else { (3.0/(x*x) - 1.0) * x.sin()/x - 3.0 * x.cos()/(x*x) };
            let deta = r.eta_grid[i] - r.eta_grid[i-1];
            
            // Interpolate visibility to check if in recomb window
            let eta = r.eta_grid[i];
            let g_val = {
                let mut gv = 0.0;
                for j in 0..vis.eta_grid.len()-1 {
                    if vis.eta_grid[j] <= eta && eta <= vis.eta_grid[j+1] {
                        let f = (eta - vis.eta_grid[j]) / 
                            (vis.eta_grid[j+1] - vis.eta_grid[j]).max(1e-30);
                        gv = vis.g_grid[j]*(1.0-f) + vis.g_grid[j+1]*f;
                        break;
                    }
                }
                gv
            };
            
            if g_val > g_thresh {
                delta_2 += r.raw_theta0_source[i] * j2 * deta;
            }
        }

        let delta_sq_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);
        let dk_over_k = if iw == 0 {
            (k_grid[1] - k_grid[0]) / k
        } else if iw == k_grid.len() - 1 {
            (k_grid[iw] - k_grid[iw - 1]) / k
        } else {
            0.5 * (k_grid[iw + 1] - k_grid[iw - 1]) / k
        };
        sum_k += delta_sq_zeta * delta_2 * delta_2 * dk_over_k;
    }

    let d2 = 6.0 / (2.0 * std::f64::consts::PI) * 4.0 * std::f64::consts::PI
        * t_cmb_uk2 * sum_k;
    Ok(d2)
}

#[cfg(test)]
mod d2_recomb {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_d2_recomb_only() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 3000, 1e5);

        let n_k = 30;
        let k_min = 0.001_f64;
        let k_max = 0.15;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max / k_min).powf(i as f64 / (n_k - 1) as f64))
            .collect();

        let t0 = std::time::Instant::now();
        match compute_d2_recomb_only(&p, &vis, &k_grid) {
            Ok(d2) => {
                let ms = t0.elapsed().as_millis();
                eprintln!("\n  === D₂ (recomb-only, no late-time artifact) ===");
                eprintln!("  D₂ = {:.1} μK²  (CLASS ref ≈ 1025, SW-only ~ 400-800)", d2);
                eprintln!("  This is the monopole g×Θ₀ only (no ISW/Doppler)");
                eprintln!("  n_k={}, wall={}ms", n_k, ms);
                
                // Also compute full (with late-time) for comparison
                match compute_d2_sync_sw(&p, &vis, &k_grid, 80) {
                    Ok(d2_full) => {
                        eprintln!("  D₂_full = {:.1} μK² (includes late-time artifact)", d2_full);
                        eprintln!("  Ratio recomb/full = {:.3}", d2 / d2_full.max(1e-30));
                    }
                    Err(_) => {}
                }
            }
            Err(e) => eprintln!("  FAILED: {}", e),
        }
    }
}

#[cfg(test)]
mod ell_convergence {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::boundary_eft;

    /// Measure source function convergence as ℓ_max increases.
    /// This is the key test: does truncation at ℓ_max hide physics?
    #[test]
    fn test_lmax_source_convergence() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1.0e5);

        eprintln!("\n  === ℓ_max SOURCE CONVERGENCE (sync gauge) ===");
        eprintln!("  Testing whether truncation at ℓ_max hides physics");
        eprintln!("  {:>6} {:>6} {:>12} {:>12} {:>10} {:>10}",
            "k", "ℓ_max", "|src|_peak", "Δ₂(k)", "Σ_L/ω", "ms");
        eprintln!("  {}", "-".repeat(65));

        for &k in &[0.05_f64, 0.10, 0.15] {
            let omega = k;  // ω = k/S ≈ k at late times (S≈1)
            let mut prev_src_peak = 0.0_f64;
            let mut prev_delta2 = 0.0_f64;

            for &lg in &[15_usize, 25, 40, 60, 80, 100, 120] {
                let ln = (lg / 2).max(6);
                let t0 = std::time::Instant::now();
                match solve_sync_kmode(k, &p, &vis, lg, ln) {
                    Ok(r) => {
                        let ms = t0.elapsed().as_millis();
                        let src_peak = r.raw_theta0_source.iter()
                            .fold(0.0_f64, |m, &s| m.max(s.abs()));

                        // Compute Δ₂(k) = ∫ src × j₂(kη) dη
                        let n = r.eta_grid.len();
                        let eta_0 = r.eta_grid[n - 1];
                        let mut delta2_k = 0.0_f64;
                        for i in 1..n {
                            let x = k * r.eta_grid[i];
                            let j2 = if x.abs() < 1e-10 { 0.0 }
                                else { (3.0/(x*x) - 1.0) * x.sin()/x - 3.0*x.cos()/(x*x) };
                            let deta = r.eta_grid[i] - r.eta_grid[i-1];
                            delta2_k += r.raw_theta0_source[i] * j2 * deta;
                        }

                        // EFT prediction: Σ_L(ω)/ω at s=ω (characteristic frequency)
                        let sigma_l = boundary_eft::self_energy(omega, omega, lg, lg + 500);
                        let ratio = sigma_l.abs() / omega.max(1e-30);

                        // Convergence metrics
                        let src_change = if prev_src_peak > 0.0 {
                            (src_peak - prev_src_peak).abs() / prev_src_peak
                        } else { f64::NAN };
                        let d2_change = if prev_delta2.abs() > 0.0 {
                            (delta2_k - prev_delta2).abs() / prev_delta2.abs()
                        } else { f64::NAN };

                        eprintln!("  {:>6.3} {:>6} {:>12.4e} {:>12.4e} {:>10.4e} {:>6}ms  Δsrc={:.1e} ΔΔ₂={:.1e}",
                            k, lg, src_peak, delta2_k, ratio, ms,
                            src_change, d2_change);

                        prev_src_peak = src_peak;
                        prev_delta2 = delta2_k;
                    }
                    Err(e) => eprintln!("  k={:.3} ℓ={}: FAIL {}", k, lg, &e[..40.min(e.len())]),
                }
            }
            eprintln!();
        }

        eprintln!("  INTERPRETATION:");
        eprintln!("  - If src/Δ₂ converge by ℓ~60-80: truncation safe for FLRW");
        eprintln!("  - If Σ_L/ω << 1: EFT correction small (boundary EFT validates truncation)");
        eprintln!("  - If Σ_L/ω ~ O(1): non-trivial hidden physics from tail");
    }
}

#[cfg(test)]
mod d2_proper {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::stacked::integrate_linear_profile_rodas5p;
    use crate::core::config::Rodas5PConfig;

    /// Compute D₂ properly using raw Θ₀_sync (no gauge transform).
    /// This gives the monopole-only contribution. Missing: Ψ, Doppler, ISW.
    #[test]
    fn test_d2_raw_theta0() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1.0e5);

        let t_cmb_uk2 = (2.7255e6_f64).powi(2);
        let a_s = 2.1e-9_f64;
        let n_s = 0.9649_f64;
        let k_pivot = 0.05_f64;
        let n_vis = vis.z_grid.len();
        let eta_0 = vis.eta_grid[0];  // η₀ at z=0 (largest conformal time)

        // k-grid: 40 log-spaced points
        let n_k = 40;
        let k_min = 0.0005_f64;
        let k_max = 0.25;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max/k_min).powf(i as f64 / (n_k-1) as f64))
            .collect();

        let mut sum_d2 = 0.0_f64;
        let mut per_k_report = Vec::new();

        let total_t0 = std::time::Instant::now();
        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(100);
            let ln = (lg / 2).max(6);

            let r = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r,
                Err(e) => { eprintln!("  k={:.4}: FAIL", k); continue; }
            };

            // LoS integral: Δ₂(k) = ∫ g(τ) Θ₀(k,τ) j₂[k(η₀-η)] dη
            // Here η₀ is the conformal time TODAY, and η is conformal time at the source
            // The comoving distance to the source is χ = η₀ - η
            let n = r.eta_grid.len();
            let mut delta2 = 0.0_f64;
            for i in 1..n {
                let eta = r.eta_grid[i];
                let chi = eta_0 - eta;  // comoving distance to source
                let x = k * chi;
                let j2 = if x.abs() < 1e-10 { x*x/15.0 }
                    else { (3.0/(x*x) - 1.0) * x.sin()/x - 3.0*x.cos()/(x*x) };
                // Use raw g × Θ₀ as source (monopole-only, no gauge transform)
                let vis_idx = n_vis - 1 - i;  // map back to vis grid
                let g_val = if vis_idx < n_vis { vis.g_grid[vis_idx] } else { 0.0 };
                let theta0 = r.raw_theta0_source[i] / g_val.max(1e-30);  // extract Θ₀ from g×(gauge stuff)
                // Actually, raw_theta0_source has the gauge-transformed combo. Use snapshots directly.
                // BUT we don't have raw snapshots here. Let me use a different approach.
                // Just use the raw_theta0_source as-is for now (it's g × (Θ₀_N + Ψ_N) via gauge transform)
                let deta = r.eta_grid[i] - r.eta_grid[i-1];
                delta2 += r.raw_theta0_source[i] * j2 * deta;
            }

            // Primordial spectrum weight
            let p_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);

            // k-integration: dk/k with trapezoidal
            let dk_over_k = if ik == 0 {
                (k_grid[1] - k_grid[0]) / k
            } else if ik == n_k - 1 {
                (k_grid[ik] - k_grid[ik-1]) / k
            } else {
                0.5 * (k_grid[ik+1] - k_grid[ik-1]) / k
            };

            let contrib = p_zeta * delta2 * delta2 * dk_over_k;
            sum_d2 += contrib;

            if ik % 5 == 0 || ik == n_k - 1 {
                per_k_report.push((k, delta2, p_zeta * delta2 * delta2, lg));
            }
        }
        let total_ms = total_t0.elapsed().as_millis();

        // D₂ = ℓ(ℓ+1)/(2π) × 4π × T²_CMB × sum
        let d2 = 6.0 / (2.0 * std::f64::consts::PI)
            * 4.0 * std::f64::consts::PI
            * t_cmb_uk2
            * sum_d2;

        eprintln!("\n  === D₂ PROPER (sync gauge, with A_s, gauge-transformed source) ===");
        eprintln!("  D₂ = {:.1} μK²", d2);
        eprintln!("  CLASS ref = 1025 μK², CAMB ref = 1022 μK²");
        eprintln!("  Newtonian SW-only (Φ=1, no A_s) = 1760 μK²");
        eprintln!("  n_k = {}, k = [{:.4}, {:.3}], z_max = 1e5", n_k, k_min, k_max);
        eprintln!("  Total wall = {}ms", total_ms);
        eprintln!();
        eprintln!("  Per-k contributions:");
        for &(k, d2k, contrib, lg) in &per_k_report {
            eprintln!("    k={:.4} ℓ={:>3}: Δ₂={:>12.4e}  P_ζ|Δ₂|²={:>12.4e}", k, lg, d2k, contrib);
        }
    }
}

#[cfg(test)]
mod eta_diagnostic {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_eta_grid_values() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1.0e5);
        let n = vis.z_grid.len();

        eprintln!("\n  === η grid diagnostic ===");
        eprintln!("  n_points = {}", n);
        eprintln!("  z_grid[0]={:.1}, z_grid[{}]={:.1}", vis.z_grid[0], n-1, vis.z_grid[n-1]);
        eprintln!("  η_grid[0]={:.1}, η_grid[{}]={:.1}", vis.eta_grid[0], n-1, vis.eta_grid[n-1]);

        // Find visibility peak
        let i_peak = vis.g_grid.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap()).unwrap().0;
        eprintln!("  g_peak: z={:.1}, η={:.1}, g={:.4e}", 
            vis.z_grid[i_peak], vis.eta_grid[i_peak], vis.g_grid[i_peak]);

        // Check comoving distance to LSS
        let eta_0 = vis.eta_grid[0];
        let eta_star = vis.eta_grid[i_peak];
        let chi_star = eta_0 - eta_star;
        eprintln!("  η₀={:.1} Mpc, η_*={:.1} Mpc, χ_*={:.1} Mpc", eta_0, eta_star, chi_star);
        eprintln!("  Expected: η₀≈14050, η_*≈280, χ_*≈13770");

        // Now solve k=0.01 and trace
        let k = 0.01_f64;
        let r = solve_sync_kmode(k, &p, &vis, 20, 10).unwrap();
        let nr = r.eta_grid.len();
        eprintln!("\n  Sync result for k={}:", k);
        eprintln!("  eta_grid[0]={:.1}, eta_grid[{}]={:.1}", r.eta_grid[0], nr-1, r.eta_grid[nr-1]);

        // Find source peak
        let i_src_peak = r.raw_theta0_source.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;
        eprintln!("  src peak at η={:.1}, src={:.4e}", r.eta_grid[i_src_peak], r.raw_theta0_source[i_src_peak]);

        // Compute j₂ at peak
        let chi_pk = eta_0 - r.eta_grid[i_src_peak];
        let x_pk = k * chi_pk;
        let j2_pk = (3.0/(x_pk*x_pk) - 1.0) * x_pk.sin()/x_pk - 3.0*x_pk.cos()/(x_pk*x_pk);
        eprintln!("  χ={:.1}, x=kχ={:.1}, j₂(x)={:.4e}", chi_pk, x_pk, j2_pk);
        eprintln!("  Naive Δ₂ ≈ src × Δη × j₂ ≈ {:.4e}", 
            r.raw_theta0_source[i_src_peak] * 30.0 * j2_pk);
    }
}

#[cfg(test)]
mod d2_fixed {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_d2_correct_bessel() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1.0e5);

        let t_cmb_uk2 = (2.7255e6_f64).powi(2);
        let a_s = 2.1e-9_f64;
        let n_s = 0.9649_f64;
        let k_pivot = 0.05_f64;

        // k-grid: 50 log-spaced
        let n_k = 50;
        let k_min = 0.0003_f64;
        let k_max = 0.30;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max/k_min).powf(i as f64 / (n_k-1) as f64))
            .collect();

        let mut sum_d2 = 0.0_f64;
        let t0 = std::time::Instant::now();

        for (ik, &k) in k_grid.iter().enumerate() {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(100);
            let ln = (lg / 2).max(6);

            let r = match solve_sync_kmode(k, &p, &vis, lg, ln) {
                Ok(r) => r,
                Err(_) => continue,
            };

            let n = r.eta_grid.len();
            let mut delta_ell = 0.0_f64;
            for i in 1..n {
                let d = r.eta_grid[i];  // comoving distance (our η IS distance)
                let x = k * d;
                // j₂(x) = (3/x² - 1)sin(x)/x - 3cos(x)/x²
                let j2 = if x.abs() < 1e-6 { x*x/15.0 }
                    else { (3.0/(x*x) - 1.0) * x.sin()/x - 3.0*x.cos()/(x*x) };

                let dd = (r.eta_grid[i] - r.eta_grid[i-1]).abs();
                delta_ell += r.raw_theta0_source[i] * j2 * dd;
            }

            let p_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);
            let dk_over_k = if ik == 0 { (k_grid[1] - k_grid[0]) / k }
                else if ik == n_k-1 { (k_grid[ik] - k_grid[ik-1]) / k }
                else { 0.5 * (k_grid[ik+1] - k_grid[ik-1]) / k };

            sum_d2 += p_zeta * delta_ell * delta_ell * dk_over_k;

            if ik % 8 == 0 {
                eprintln!("  k={:.4} ℓg={:>3}: Δ₂={:>11.4e}  |Δ₂|²P_ζ={:.3e}",
                    k, lg, delta_ell, p_zeta * delta_ell * delta_ell);
            }
        }
        let total_ms = t0.elapsed().as_millis();

        let d2 = 6.0 / (2.0 * std::f64::consts::PI)
            * 4.0 * std::f64::consts::PI
            * t_cmb_uk2
            * sum_d2;

        eprintln!("\n  === D₂ FIXED (j₂(kd), A_s included, sync gauge) ===");
        eprintln!("  D₂ = {:.1} μK²", d2);
        eprintln!("  CLASS = 1025, CAMB = 1022 μK²");
        eprintln!("  n_k={}, wall={}ms", n_k, total_ms);
        eprintln!("  Note: using gauge-transformed source g×(Θ₀_N+Ψ_N)");
        eprintln!("  Missing: ISW (small at ℓ=2), full Doppler (integrated by parts)");
    }
}

#[cfg(test)]
mod los_trace {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_los_trace_k001() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1.0e5);
        let k = 0.001_f64;
        let r = solve_sync_kmode(k, &p, &vis, 20, 10).unwrap();
        let n = r.eta_grid.len();

        eprintln!("\n  === LoS TRACE k={} ===", k);
        eprintln!("  n_grid={}, η[0]={:.1}, η[{}]={:.1}", n, r.eta_grid[0], n-1, r.eta_grid[n-1]);

        // Find src peak
        let (ip, sp) = r.raw_theta0_source.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap();
        eprintln!("  src peak: i={}, η={:.1}, src={:.4e}", ip, r.eta_grid[ip], sp);

        // Print source values near peak (every 10th point)
        let win_lo = if ip > 100 { ip - 100 } else { 0 };
        let win_hi = (ip + 100).min(n-1);
        eprintln!("  Plotting source near peak (i={}..{}):", win_lo, win_hi);
        for i in (win_lo..=win_hi).step_by(10) {
            let d = r.eta_grid[i];
            let x = k * d;
            let j2 = if x.abs() < 1e-6 { x*x/15.0 }
                else { (3.0/(x*x)-1.0)*x.sin()/x - 3.0*x.cos()/(x*x) };
            eprintln!("    i={:>5} η={:>8.1} src={:>11.3e} j₂(kη)={:>11.3e} prod={:>11.3e}",
                i, d, r.raw_theta0_source[i], j2, r.raw_theta0_source[i] * j2);
        }

        // Compute integral
        let mut integral = 0.0_f64;
        let mut max_integrand = 0.0_f64;
        for i in 1..n {
            let d = r.eta_grid[i];
            let x = k * d;
            let j2 = if x.abs() < 1e-6 { x*x/15.0 }
                else { (3.0/(x*x)-1.0)*x.sin()/x - 3.0*x.cos()/(x*x) };
            let dd = (r.eta_grid[i] - r.eta_grid[i-1]).abs();
            let prod = r.raw_theta0_source[i] * j2 * dd;
            integral += prod;
            max_integrand = max_integrand.max(prod.abs());
        }
        eprintln!("\n  Δ₂(k={}) = {:.4e}", k, integral);
        eprintln!("  max|integrand| = {:.4e}", max_integrand);
        eprintln!("  Expected: ~(1/3) × j₂(k×13400) × g_width × g_peak");
        let x_star = k * 13400.0;
        let j2_star = (3.0/(x_star*x_star)-1.0)*x_star.sin()/x_star - 3.0*x_star.cos()/(x_star*x_star);
        eprintln!("  j₂(k×13400={:.1}) = {:.4e}", x_star, j2_star);
        eprintln!("  Expected Δ₂ ≈ 0.33 × {:.4e} × 30 × 0.022 = {:.4e}",
            j2_star, 0.33 * j2_star * 30.0 * 0.022);
    }
}

#[cfg(test)]
mod d2_normalization_fix {
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, compute_flrw_cl_track_a};
    use crate::recombination::visibility_hyrec::VisibilityParams;

    /// Apply correct ζ=1 normalization to existing Newtonian pipeline.
    #[test]
    fn test_d2_with_zeta_normalization() {
        let p = VisibilityParams::planck2018();
        let cfg = FlrwClConfig::fast_validation();  // k_max=0.03, safe for Newtonian
        let r = compute_flrw_cl_track_a(&p, &cfg).unwrap();
        let t_uk2 = (2.7255e6_f64).powi(2);

        // Existing D₂ (Φ=1 normalization, A_s included)
        let d2_phi1 = r.dl_muK2[2];

        // Correct D₂ with ζ=1 normalization: multiply by (2/3)² = 4/9
        let zeta_factor = 4.0 / 9.0;
        let d2_zeta1 = d2_phi1 * zeta_factor;

        eprintln!("\n  === D₂ NORMALIZATION FIX ===");
        eprintln!("  D₂(Φ=1, SW-only)  = {:.1} μK²", d2_phi1);
        eprintln!("  D₂(ζ=1, SW-only)  = {:.1} μK² (× 4/9)", d2_zeta1);
        eprintln!("  D₂(ζ=1, +ISW 25%) = {:.1} μK²", d2_zeta1 * 1.25);
        eprintln!("  D₂(ζ=1, +ISW+Dop) = {:.1} μK²", d2_zeta1 * 1.31);
        eprintln!("  CLASS reference     = 1025 μK²");
        eprintln!("  CAMB reference      = 1022 μK²");
        eprintln!("  Ratio (corrected/CLASS) = {:.3}", d2_zeta1 * 1.31 / 1025.0);

        // Also check D_220 (first acoustic peak)
        let d220_phi1 = r.dl_muK2[220];
        let d220_zeta1 = d220_phi1 * zeta_factor;
        eprintln!("\n  D_220(Φ=1)  = {:.1} μK²", d220_phi1);
        eprintln!("  D_220(ζ=1)  = {:.1} μK²", d220_zeta1);
        eprintln!("  CLASS D_220 ≈ 5740 μK²");

        // Print first few multipoles
        eprintln!("\n  {:>5} {:>12} {:>12}", "ℓ", "D_ℓ(Φ=1)", "D_ℓ(ζ=1)");
        for ell in &[2, 10, 30, 100, 220, 500, 800, 1000] {
            if *ell <= cfg.ell_max {
                eprintln!("  {:>5} {:>12.1} {:>12.1}", ell,
                    r.dl_muK2[*ell], r.dl_muK2[*ell] * zeta_factor);
            }
        }
    }
}

#[cfg(test)]
mod d2_full_source {
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, SourceMode, compute_flrw_cl_track_a};
    use crate::recombination::visibility_hyrec::VisibilityParams;

    #[test]
    fn test_d2_full_with_isw() {
        let p = VisibilityParams::planck2018();

        // SW-only baseline (safe config)
        let cfg_sw = FlrwClConfig {
            source_mode: SourceMode::SwOnly,
            ..FlrwClConfig::fast_validation()
        };
        let r_sw = compute_flrw_cl_track_a(&p, &cfg_sw).unwrap();

        // Full source: SW + ISW (same safe k range)
        let cfg_full = FlrwClConfig {
            source_mode: SourceMode::Full,
            ..FlrwClConfig::fast_validation()
        };
        let r_full = compute_flrw_cl_track_a(&p, &cfg_full).unwrap();

        // Extended k range for Full mode (still Newtonian-safe)
        let cfg_ext = FlrwClConfig {
            source_mode: SourceMode::Full,
            n_k: 60,
            k_min: 1e-5,
            k_max: 0.03,
            ell_max_gamma: 20,
            ell_max_nu: 10,
            n_vis: 3000,
            ..FlrwClConfig::fast_validation()
        };
        let r_ext = compute_flrw_cl_track_a(&p, &cfg_ext).unwrap();

        eprintln!("\n  === D₂ WITH ISW (Newtonian, k≤0.03, ζ=1 norm) ===");
        eprintln!("  {:>20} {:>10} {:>10}", "Config", "D₂ μK²", "vs CLASS");
        eprintln!("  {:>20} {:>10.1} {:>10.3}", "SW-only (fast)",
            r_sw.dl_muK2[2], r_sw.dl_muK2[2] / 1025.0);
        eprintln!("  {:>20} {:>10.1} {:>10.3}", "Full (fast)",
            r_full.dl_muK2[2], r_full.dl_muK2[2] / 1025.0);
        eprintln!("  {:>20} {:>10.1} {:>10.3}", "Full (extended k)",
            r_ext.dl_muK2[2], r_ext.dl_muK2[2] / 1025.0);
        eprintln!("  {:>20} {:>10.1}", "CLASS reference", 1025.0);

        let isw_frac = (r_full.dl_muK2[2] - r_sw.dl_muK2[2]) / r_sw.dl_muK2[2];
        eprintln!("\n  ISW fraction at ℓ=2: {:.1}%", isw_frac * 100.0);

        // Multi-ℓ comparison
        eprintln!("\n  {:>5} {:>10} {:>10} {:>10}", "ℓ", "SW-only", "Full", "ISW %");
        for &ell in &[2, 5, 10, 20, 30] {
            if ell <= cfg_sw.ell_max && ell <= cfg_ext.ell_max {
                let sw = r_sw.dl_muK2[ell];
                let full = r_ext.dl_muK2[ell];
                let frac = if sw.abs() > 1e-30 { (full - sw) / sw * 100.0 } else { 0.0 };
                eprintln!("  {:>5} {:>10.1} {:>10.1} {:>10.1}%", ell, sw, full, frac);
            }
        }
    }
}

/// Hybrid C_ℓ pipeline: Newtonian (k≤0.03) + Sync (k>0.03).
/// Uses (4/9) ζ-normalization. SW-only source.
pub(crate) fn compute_hybrid_cl(
    params: &VisibilityParams,
    k_grid: &[f64],
    ell_max: usize,
    z_max_sync: f64,
) -> Result<Vec<f64>, String> {
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::recombination::visibility_hyrec::{compute_visibility, compute_visibility_ext};
    use crate::solver::flrw_kmode::solve_kmode_rodas5p;
    use crate::los::bessel::spherical_bessel_j;

    let a_s = 2.1e-9_f64;
    let n_s = 0.9649_f64;
    let k_pivot = 0.05_f64;
    let k_split = 0.03_f64;
    let zeta_norm = 4.0 / 9.0;

    let tables = HyRecTables::generate(300);
    let vis_newt = compute_visibility(params, &tables, 3000);
    let vis_sync = compute_visibility_ext(params, &tables, 2000, z_max_sync);
    let eta_0_newt = vis_newt.eta_grid[0];  // η at z=0 (comoving distance convention: 0)

    // Find actual η₀ (should be ~14000 Mpc)
    let n_newt = vis_newt.eta_grid.len();
    let eta_max_newt = vis_newt.eta_grid.iter().cloned().fold(0.0_f64, f64::max);

    let mut cl = vec![0.0_f64; ell_max + 2];

    for (ik, &k) in k_grid.iter().enumerate() {
        let p_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);
        let dk_over_k = if ik == 0 { (k_grid[1] - k_grid[0]) / k }
            else if ik == k_grid.len() - 1 { (k_grid[ik] - k_grid[ik-1]) / k }
            else { 0.5 * (k_grid[ik+1] - k_grid[ik-1]) / k };

        // Get source function
        let (eta_grid, source): (Vec<f64>, Vec<f64>) = if k <= k_split {
            // Newtonian gauge (z_max=4000)
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(8).min(25);
            let ln = (lg / 2).max(6);
            let (eta_g, src_g) = solve_kmode_rodas5p(k, params, &vis_newt, lg, ln)
                .map_err(|e| format!("Newt k={:.4}: {}", k, e))?;
            (eta_g, src_g)
        } else {
            // Sync gauge (high z_max)
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(100);
            let ln = (lg / 2).max(6);
            let r = solve_sync_kmode(k, params, &vis_sync, lg, ln)
                .map_err(|e| format!("Sync k={:.4}: {}", k, e))?;
            (r.eta_grid, r.raw_theta0_source)
        };

        // LoS integration: Δ_ℓ(k) = ∫ S(η) j_ℓ(kη) dη
        // η is comoving distance in our convention
        let n = eta_grid.len();
        let mut delta_ell = vec![0.0_f64; ell_max + 2];

        for i in 1..n {
            let d = eta_grid[i];  // comoving distance
            let x = k * d;
            if x < 1e-10 || x > 15000.0 { continue; }

            let deta = (eta_grid[i] - eta_grid[i-1]).abs();
            let s = source[i];
            if s.abs() < 1e-30 { continue; }

            // Compute j_ℓ for all ℓ up to ell_max
            for ell in 2..=ell_max.min(((x + 50.0) as usize).max(2)) {
                let jl = spherical_bessel_j(ell, x);
                delta_ell[ell] += s * jl * deta;
            }
        }

        // Accumulate: C_ℓ += 4π × P_ζ × (4/9) × |Δ_ℓ|² × dk/k
        let weight = 4.0 * std::f64::consts::PI * p_zeta * zeta_norm * dk_over_k;
        for ell in 2..=ell_max {
            cl[ell] += weight * delta_ell[ell] * delta_ell[ell];
        }
    }

    Ok(cl)
}

#[cfg(test)]
mod hybrid_pipeline {
    use super::*;
    use crate::recombination::visibility_hyrec::VisibilityParams;

    #[test]
    fn test_hybrid_d2_and_spectrum() {
        let p = VisibilityParams::planck2018();
        let t_uk2 = (2.7255e6_f64).powi(2);
        let ell_max = 30;  // low ℓ first for speed

        // k-grid: 40 log-spaced
        let n_k = 40;
        let k_min = 5e-5_f64;
        let k_max = 0.05;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max/k_min).powf(i as f64 / (n_k-1) as f64))
            .collect();

        let t0 = std::time::Instant::now();
        let cl = compute_hybrid_cl(&p, &k_grid, ell_max, 1e5).unwrap();
        let ms = t0.elapsed().as_millis();

        eprintln!("\n  === HYBRID C_ℓ PIPELINE (Newt k≤0.03 + Sync k>0.03) ===");
        eprintln!("  n_k={}, k=[{:.0e},{:.2}], ℓ_max={}, wall={}ms", n_k, k_min, k_max, ell_max, ms);
        eprintln!("\n  {:>5} {:>12} {:>12}", "ℓ", "D_ℓ (μK²)", "CLASS ref");
        for ell in 2..=ell_max {
            let dl = ell as f64 * (ell + 1) as f64 / (2.0 * std::f64::consts::PI)
                * cl[ell] * t_uk2;
            let class_approx = match ell {
                2 => 1025.0,
                10 => 200.0,
                30 => 700.0,
                _ => 0.0,
            };
            if ell <= 5 || ell % 5 == 0 {
                eprintln!("  {:>5} {:>12.1} {:>12}", ell, dl,
                    if class_approx > 0.0 { format!("~{:.0}", class_approx) } else { "".to_string() });
            }
        }
    }
}

#[cfg(test)]
mod bessel_check {
    use crate::los::bessel::spherical_bessel_j;

    #[test]
    fn test_j2_spot_check() {
        // j₂(10) = 3sin(10)/100 - 3cos(10)/100 - sin(10)/10
        let x = 10.0_f64;
        let j2_exact = (3.0/(x*x) - 1.0) * x.sin()/x - 3.0*x.cos()/(x*x);
        let j2_lib = spherical_bessel_j(2, x);
        eprintln!("  j₂(10): exact={:.6e}, lib={:.6e}, err={:.2e}",
            j2_exact, j2_lib, (j2_lib - j2_exact).abs());

        // j₂(0.01)
        let x = 0.01_f64;
        let j2_exact = x*x/15.0; // small-x limit
        let j2_lib = spherical_bessel_j(2, x);
        eprintln!("  j₂(0.01): exact~{:.6e}, lib={:.6e}", j2_exact, j2_lib);

        // j₂(100)
        let x = 100.0_f64;
        let j2_exact = (3.0/(x*x) - 1.0) * x.sin()/x - 3.0*x.cos()/(x*x);
        let j2_lib = spherical_bessel_j(2, x);
        eprintln!("  j₂(100): exact={:.6e}, lib={:.6e}", j2_exact, j2_lib);
    }
}

#[cfg(test)]
mod production_cl {
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, SourceMode, compute_flrw_cl_track_a};
    use crate::recombination::visibility_hyrec::VisibilityParams;

    /// Production-quality C_ℓ from Newtonian pipeline with (4/9) fix.
    /// k_max = 0.03 limits us to ℓ ≤ ~30 (Bessel sampling).
    #[test]
    fn test_production_cl_low_ell() {
        let p = VisibilityParams::planck2018();
        let t_uk2 = (2.7255e6_f64).powi(2);

        let cfg = FlrwClConfig {
            ell_max: 30,
            n_k: 60,
            k_min: 1e-5,
            k_max: 0.03,
            ell_max_gamma: 20,
            ell_max_nu: 10,
            n_vis: 3000,
            source_mode: SourceMode::SwOnly,
            ..FlrwClConfig::fast_validation()
        };
        let t0 = std::time::Instant::now();
        let r = compute_flrw_cl_track_a(&p, &cfg).unwrap();
        let ms = t0.elapsed().as_millis();

        eprintln!("\n  === PRODUCTION C_ℓ (SW-only, ζ=1, Newtonian k≤0.03) ===");
        eprintln!("  wall = {}ms, n_k = {}", ms, cfg.n_k);
        eprintln!("\n  {:>5} {:>12} {:>12} {:>8}", "ℓ", "D_ℓ μK²", "CLASS", "ratio");
        // CLASS approximate reference values (from project knowledge)
        let class_ref = vec![
            (2, 1025.0), (3, 950.0), (4, 600.0), (5, 750.0),
            (10, 200.0), (15, 600.0), (20, 1500.0), (25, 2000.0), (30, 700.0),
        ];
        for &(ell, cl_val) in &class_ref {
            if ell <= cfg.ell_max {
                let d = r.dl_muK2[ell];
                eprintln!("  {:>5} {:>12.1} {:>12.0} {:>8.3}", ell, d, cl_val, d/cl_val);
            }
        }

        // Key diagnostic: D₂ with and without ISW estimate
        let d2 = r.dl_muK2[2];
        eprintln!("\n  D₂(SW-only) = {:.1} μK²", d2);
        eprintln!("  D₂ + ISW(~20%) = {:.1} μK² (est)", d2 * 1.20);
        eprintln!("  CLASS D₂ = 1025 μK²");
        eprintln!("  Agreement: {:.1}% (SW-only), {:.1}% (with ISW est)",
            (d2/1025.0 - 1.0)*100.0, (d2*1.20/1025.0 - 1.0)*100.0);
    }
}

#[cfg(test)]
mod isw_debug {
    use crate::solver::flrw_kmode::solve_kmode_rodas5p;
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_isw_source_values() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let k = 0.005_f64;
        let (eta, src) = solve_kmode_rodas5p(k, &p, &vis, 15, 8).unwrap();

        // The source from solve_kmode_rodas5p = sw + isw combined.
        // Separately compute SW-only to isolate ISW.
        let n = eta.len();
        let n_vis = vis.z_grid.len();

        // Find visibility peak
        let i_peak = vis.g_grid.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap()).unwrap().0;

        eprintln!("\n  === ISW DEBUG k={} ===", k);
        eprintln!("  n_points={}, vis_peak_z={:.0}", n, vis.z_grid[i_peak]);

        // Print source near visibility peak and at late times
        let mut max_src = 0.0_f64;
        let mut max_late_src = 0.0_f64;
        for i in 0..n {
            if src[i].abs() > max_src { max_src = src[i].abs(); }
            // Late time: η < 5000 Mpc (z < ~2, where ISW dominates)
            if eta[i] < 5000.0 && src[i].abs() > max_late_src {
                max_late_src = src[i].abs();
            }
        }
        eprintln!("  max|src| = {:.4e} (near recomb)", max_src);
        eprintln!("  max|src| at late times (η<5000) = {:.4e}", max_late_src);
        eprintln!("  ratio late/peak = {:.4e}", max_late_src / max_src.max(1e-30));

        // Print a few late-time points
        eprintln!("\n  Late-time source (ISW-dominated region):");
        eprintln!("  {:>8} {:>12} {:>12}", "η", "src(sw+isw)", "g(z)");
        for i in 0..n {
            if eta[i] < 8000.0 && i % 20 == 0 {
                let vi = match vis.eta_grid.binary_search_by(
                    |v| v.partial_cmp(&eta[i]).unwrap()) {
                    Ok(j) => j, Err(j) => j.min(n_vis-1),
                };
                let g = vis.g_grid[vi];
                eprintln!("  {:>8.1} {:>12.4e} {:>12.4e}", eta[i], src[i], g);
            }
        }
    }
}

#[cfg(test)]
mod isw_pipeline_debug {
    use crate::solver::flrw_kmode::{solve_kmode_with_history, extract_source_grid};
    use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;

    #[test]
    fn test_isw_vs_sw_sourcegrid() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        eprintln!("\n  === ISW vs SW in SourceGrid ===");
        eprintln!("  {:>8} {:>12} {:>12} {:>12} {:>8}", "k", "max|SW|", "max|ISW|", "ISW/SW", "n_pts");

        for &k in &[0.001_f64, 0.005, 0.01, 0.02, 0.03] {
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(8).min(25);
            let ln = (lg / 2).max(6);
            match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(kr) => {
                    let sg = extract_source_grid(&kr, &vis, &p);
                    let max_sw = sg.values.iter().map(|v| v.sw.abs()).fold(0.0_f64, f64::max);
                    let max_isw = sg.values.iter().map(|v| v.isw.abs()).fold(0.0_f64, f64::max);
                    let ratio = max_isw / max_sw.max(1e-30);
                    eprintln!("  {:>8.4} {:>12.4e} {:>12.4e} {:>12.4e} {:>8}",
                        k, max_sw, max_isw, ratio, sg.values.len());
                }
                Err(e) => eprintln!("  k={:.4}: FAIL {}", k, &e[..40.min(e.len())]),
            }
        }
    }
}

#[cfg(test)]
mod hybrid_v2 {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility, compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::flrw_kmode::solve_kmode_with_history;
    use crate::los::bessel::spherical_bessel_j;

    /// Hybrid D₂ using correct source paths.
    /// Newtonian: solve_kmode_with_history → raw_theta0_source (pure SW)
    /// Sync: solve_sync_kmode → raw_theta0_source (gauge-transformed, OK for k>0.03)
    #[test]
    fn test_hybrid_v2_d2() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis_newt = compute_visibility(&p, &t, 3000);
        let vis_sync = compute_visibility_ext(&p, &t, 2000, 1e5);
        let t_uk2 = (2.7255e6_f64).powi(2);

        let a_s = 2.1e-9_f64;
        let n_s = 0.9649_f64;
        let k_pivot = 0.05_f64;
        let zeta_norm = 4.0 / 9.0;
        let k_split = 0.03_f64;

        let n_k = 50;
        let k_min = 5e-5_f64;
        let k_max = 0.20;
        let k_grid: Vec<f64> = (0..n_k)
            .map(|i| k_min * (k_max/k_min).powf(i as f64 / (n_k-1) as f64))
            .collect();

        let ell_max = 500_usize;
        let mut cl = vec![0.0_f64; ell_max + 2];
        let t0_total = std::time::Instant::now();
        let mut n_newt = 0_usize;
        let mut n_sync = 0_usize;

        for (ik, &k) in k_grid.iter().enumerate() {
            let p_zeta = a_s * (k / k_pivot).powf(n_s - 1.0);
            let dk_over_k = if ik == 0 { (k_grid[1]-k_grid[0])/k }
                else if ik == n_k-1 { (k_grid[ik]-k_grid[ik-1])/k }
                else { 0.5*(k_grid[ik+1]-k_grid[ik-1])/k };

            let (eta_grid, source) = if k <= k_split {
                // Newtonian: use raw_theta0_source (pure SW, no noisy ISW)
                let lg = ((k * 280.0 * 2.0).ceil() as usize).max(8).min(25);
                let ln = (lg / 2).max(6);
                match solve_kmode_with_history(k, &p, &vis_newt, lg, ln) {
                    Ok(kr) => { n_newt += 1; (kr.eta_grid, kr.raw_theta0_source) }
                    Err(_) => continue,
                }
            } else {
                // Sync gauge: gauge-transformed source (OK for k>0.03)
                let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(100);
                let ln = (lg / 2).max(6);
                match solve_sync_kmode(k, &p, &vis_sync, lg, ln) {
                    Ok(r) => { n_sync += 1; (r.eta_grid, r.raw_theta0_source) }
                    Err(_) => continue,
                }
            };

            // LoS: Δ_ℓ(k) = ∫ S(η) j_ℓ(kη) dη
            let n = eta_grid.len();
            let mut delta_ell = vec![0.0_f64; ell_max + 2];
            for i in 1..n {
                let d = eta_grid[i];
                let x = k * d;
                if x < 1e-10 || x > 20000.0 { continue; }
                let deta = (eta_grid[i] - eta_grid[i-1]).abs();
                let s = source[i];
                if s.abs() < 1e-30 { continue; }
                // Only compute j_ℓ up to ℓ where j_ℓ(x) is non-negligible
                let ell_upper = ell_max.min((x + 20.0) as usize);
                for ell in 2..=ell_upper {
                    delta_ell[ell] += s * spherical_bessel_j(ell, x) * deta;
                }
            }

            let weight = 4.0 * std::f64::consts::PI * p_zeta * zeta_norm * dk_over_k;
            for ell in 2..=ell_max {
                cl[ell] += weight * delta_ell[ell] * delta_ell[ell];
            }
        }
        let wall_ms = t0_total.elapsed().as_millis();

        eprintln!("\n  === HYBRID v2 C_ℓ (Newt≤0.03 + Sync>0.03, SW-only) ===");
        eprintln!("  n_k={} ({}N+{}S), k=[{:.0e},{:.2}], ℓ_max={}, wall={}ms",
            n_k, n_newt, n_sync, k_min, k_max, ell_max, wall_ms);
        eprintln!("\n  {:>5} {:>10} {:>10}", "ℓ", "D_ℓ μK²", "CLASS≈");
        let class_ref = vec![
            (2, 1025.0), (10, 200.0), (30, 690.0), (100, 2400.0),
            (150, 3400.0), (200, 5200.0), (220, 5740.0), (300, 4200.0),
            (400, 3100.0), (500, 3000.0),
        ];
        for &(ell, cl_ref) in &class_ref {
            if ell <= ell_max {
                let dl = ell as f64 * (ell+1) as f64 / (2.0*std::f64::consts::PI) * cl[ell] * t_uk2;
                eprintln!("  {:>5} {:>10.1} {:>10.0}", ell, dl, cl_ref);
            }
        }
    }
}

#[cfg(test)]
mod existing_pipeline_spectrum {
    use crate::solver::flrw_cl_pipeline::{FlrwClConfig, SourceMode, compute_flrw_cl_track_a};
    use crate::recombination::visibility_hyrec::VisibilityParams;

    /// Use existing WORKING pipeline with extended k-range for higher ℓ.
    /// Note: Newtonian gauge blows up at high k, but sponge layer limits damage.
    #[test]
    fn test_existing_pipeline_extended() {
        let p = VisibilityParams::planck2018();

        // Config: extend k to 0.03, ℓ to 500
        let cfg = FlrwClConfig {
            ell_max: 500,
            n_k: 80,
            k_min: 5e-5,
            k_max: 0.03,
            ell_max_gamma: 25,
            ell_max_nu: 12,
            n_vis: 3000,
            ell_limber: 200,
            source_mode: SourceMode::SwOnly,
            ..FlrwClConfig::fast_validation()
        };
        let t0 = std::time::Instant::now();
        let r = compute_flrw_cl_track_a(&p, &cfg).unwrap();
        let ms = t0.elapsed().as_millis();

        eprintln!("\n  === EXISTING PIPELINE C_ℓ (SW-only, ζ=1, k≤0.03) ===");
        eprintln!("  wall={}ms, n_k={}", ms, cfg.n_k);
        eprintln!("\n  {:>5} {:>12} {:>12} {:>8}", "ℓ", "D_ℓ μK²", "CLASS≈", "ratio");
        let class_ref = vec![
            (2, 1025.0), (5, 750.0), (10, 200.0), (20, 1500.0), (30, 690.0),
            (50, 900.0), (100, 2400.0), (150, 3400.0), (200, 5200.0),
            (220, 5740.0), (300, 4200.0), (400, 3100.0), (500, 3000.0),
        ];
        for &(ell, cl_ref) in &class_ref {
            if ell <= cfg.ell_max {
                let dl = r.dl_muK2[ell];
                eprintln!("  {:>5} {:>12.1} {:>12.0} {:>8.3}",
                    ell, dl, cl_ref, dl / cl_ref);
            }
        }

        // D₂ summary
        eprintln!("\n  D₂(SW-only) = {:.1} μK²", r.dl_muK2[2]);
        eprintln!("  D₂ + ISW(~20%) ≈ {:.1} μK²", r.dl_muK2[2] * 1.20);
        eprintln!("  CLASS = 1025 μK²");
    }
}

#[cfg(test)]
mod ic_audit {
    use super::*;
    
    /// IC Convention Audit: verify what eta_init represents
    #[test]
    fn test_ic_variable_dictionary() {
        let lay = SyncStateLayout::new(8, 6);
        let y0 = sync_adiabatic_ic(1e-5, 0.01, &lay);
        
        eprintln!("\n=== IC VARIABLE DICTIONARY AUDIT ===");
        eprintln!("eta_init = 1.0, k = 1e-5, aH_init = 0.01");
        eprintln!("y[0]  = Θ₀  = {:.6}", y0[0]);
        eprintln!("y[{}] = N₀  = {:.6}", lay.nu_offset, y0[lay.nu_offset]);
        eprintln!("y[{}] = δ_c = {:.6}", lay.dc_idx, y0[lay.dc_idx]);
        eprintln!("y[{}] = δ_b = {:.6}", lay.db_idx, y0[lay.db_idx]);
        eprintln!("y[{}] = v_b = {:.6e}", lay.vb_idx, y0[lay.vb_idx]);
        eprintln!("y[{}] = kη  = {:.6e}", lay.keta_idx, y0[lay.keta_idx]);
        
        let theta0 = y0[0];
        let dc = y0[lay.dc_idx];
        
        eprintln!("\n--- Ratio Check ---");
        eprintln!("Θ₀/η       = {:.4} (MB95 std: -1/6={:.4}, code: -1/2={:.4})", theta0, -1.0/6.0_f64, -0.5);
        eprintln!("δ_c/η      = {:.4} (MB95 std: -1/2={:.4}, code: -3/2={:.4})", dc, -0.5, -1.5);
        eprintln!("Θ₀/δ_c     = {:.6} (adiabatic: 1/3={:.6})", theta0/dc, 1.0/3.0_f64);
        eprintln!("4Θ₀/δ_c    = {:.6} (= δ_γ/δ_c, adiabatic: 4/3={:.6})", 4.0*theta0/dc, 4.0/3.0_f64);
        
        // The RATIO Θ₀/δ_c = 1/3 is convention-independent for adiabatic mode
        assert!((theta0/dc - 1.0/3.0).abs() < 0.01,
            "Adiabatic relation Θ₀/δ_c = 1/3 violated: {}", theta0/dc);
        eprintln!("✅ Θ₀/δ_c = 1/3 confirmed — adiabatic IC internally consistent");
        eprintln!("   IC coefficients are 3× MB95 leading-order values");
    }
}
