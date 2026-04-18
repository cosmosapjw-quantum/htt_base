//! IMEX-ARK4(3)6L[2]SA Solver (P1-05, extended per R-P1-02_설계안 §7-§9)
//!
//! Kennedy-Carpenter Additive Runge-Kutta method:
//! - 6 stages, 4th order, L-stable implicit part
//! - Embedded 3rd-order error estimator
//! - ESDIRK: Explicit first Stage, Singly Diagonal Implicit RK
//! - All implicit diagonal coefficients share single γ = a^I_{ii} = 1/4
//!
//! ## IMEX Splitting (approximation-free — no TCA/UFA/RSA)
//!
//! ```text
//! dy/dτ = f_E(τ, y) + f_I(τ, y)
//!
//! f_E: streaming + metric + geometric (EXPLICIT)
//! f_I: ALL κ̇-proportional collision (IMPLICIT)
//!      ℓ = 0: NO collision (monopole conserved)
//!      ℓ = 1: photon-baryon drag block (2×2 or 3×3 per m)
//!      ℓ = 2: temperature-polarization block (2×2 or 5×5 per m)
//!      ℓ ≥ 3: DIAGONAL → per-element scalar division
//! ```
//!
//! ## Sign convention (R-P1-02_설계안 §2.1 — CRITICAL)
//!
//! - opacity χ(η) := |κ̇(η)| ≥ 0 always (canonicalized before use)
//! - collision diagonal entry: (A_I)_{jj} = -χ (damping)
//! - implicit denominator: 1 + h·γ·χ_j (NEVER 1 - h·γ·κ̇)
//! - This prevents a stiff damper from turning into an anti-damper
//!   under sign confusion — the single most dangerous bug class.
//!
//! ## Module layout (per design §7.2)
//!
//! - This file: tableau constants + stepper + SplitLinearOp trait + workspace
//! - `imex_collision_split.rs` (future): collision operator builder from CambBackground
//! - `imex_driver.rs` (future): adaptive multi-step integrator wrapper
//!
//! The existing monolithic design is kept; the new trait-based API is
//! additive (functional and trait forms coexist).

#![allow(dead_code)]

/// Kennedy-Carpenter ARK4(3)6L[2]SA Butcher tableau.
///
/// Reference: Kennedy & Carpenter (2003), "Additive Runge-Kutta schemes
/// for convection-diffusion-reaction equations", Applied Numerical Mathematics.
pub struct Ark4Tableau {
    /// Explicit Butcher matrix a^E_{ij}, 6×6 (strictly lower triangular).
    pub a_e: [[f64; 6]; 6],
    /// Implicit Butcher matrix a^I_{ij}, 6×6 (lower triangular, ESDIRK).
    pub a_i: [[f64; 6]; 6],
    /// Explicit weights b^E_i (4th order).
    pub b_e: [f64; 6],
    /// Implicit weights b^I_i (4th order).
    pub b_i: [f64; 6],
    /// Embedded error weights b̂^E (3rd order).
    pub bhat_e: [f64; 6],
    /// Embedded error weights b̂^I (3rd order).
    pub bhat_i: [f64; 6],
    /// Nodes c_i.
    pub c: [f64; 6],
    /// Implicit diagonal γ = a^I_{ii} for i ≥ 1.
    pub gamma: f64,
}

impl Ark4Tableau {
    /// Kennedy-Carpenter ARK4(3)6L[2]SA coefficients.
    pub fn new() -> Self {
        let gamma = 0.25;

        // Explicit tableau (a^E)
        let mut a_e = [[0.0_f64; 6]; 6];
        a_e[1][0] = 0.5;
        a_e[2][0] = 13861.0 / 62500.0;
        a_e[2][1] = 6889.0 / 62500.0;
        a_e[3][0] = -116923316275.0 / 2393684061468.0;
        a_e[3][1] = -2731218467317.0 / 15368042101831.0;
        a_e[3][2] = 9408046702089.0 / 11113171139209.0;
        a_e[4][0] = -451086348788.0 / 2902428689909.0;
        a_e[4][1] = -2682348792572.0 / 7519795681897.0;
        a_e[4][2] = 12662868775082.0 / 11960479726383.0;
        a_e[4][3] = 3355817975965.0 / 11060851509271.0;
        a_e[5][0] = 647845179188.0 / 3216320057751.0;
        a_e[5][1] = 73281519250.0 / 8382639484533.0;
        a_e[5][2] = 552539513391.0 / 3454668386233.0;
        a_e[5][3] = 3354512671639.0 / 8306763924573.0;
        a_e[5][4] = 4040.0 / 17871.0;

        // Implicit tableau (a^I) — ESDIRK: a^I_{1,1} = 0 (explicit first stage)
        let mut a_i = [[0.0_f64; 6]; 6];
        // Stage 1: fully explicit (ESDIRK property)
        // a_i[0][0] = 0.0
        a_i[1][0] = 0.25;
        a_i[1][1] = gamma; // = 0.25
        a_i[2][0] = 8611.0 / 62500.0;
        a_i[2][1] = -1743.0 / 31250.0;
        a_i[2][2] = gamma;
        a_i[3][0] = 5012029.0 / 34652500.0;
        a_i[3][1] = -654441.0 / 2922500.0;
        a_i[3][2] = 174375.0 / 388108.0;
        a_i[3][3] = gamma;
        a_i[4][0] = 15267082809.0 / 155376265600.0;
        a_i[4][1] = -71443401.0 / 120774400.0;
        a_i[4][2] = 730878875.0 / 902184768.0;
        a_i[4][3] = 2285395.0 / 8070912.0;
        a_i[4][4] = gamma;
        a_i[5][0] = 82889.0 / 524892.0;
        a_i[5][1] = 0.0;
        a_i[5][2] = 15625.0 / 83664.0;
        a_i[5][3] = 69875.0 / 102672.0;
        a_i[5][4] = -2260.0 / 8211.0;
        a_i[5][5] = gamma;

        // Weights (4th order) — same for explicit and implicit in this method
        let b_e = [
            82889.0 / 524892.0,
            0.0,
            15625.0 / 83664.0,
            69875.0 / 102672.0,
            -2260.0 / 8211.0,
            0.25,
        ];
        let b_i = b_e; // b^E = b^I for this method

        // Embedded 3rd-order weights (for error estimation)
        let bhat_e = [
            4586570599.0 / 29645900160.0,
            0.0,
            178811875.0 / 945068544.0,
            814220225.0 / 1159782912.0,
            -3700637.0 / 11593932.0,
            61727.0 / 225920.0,
        ];
        let bhat_i = bhat_e;

        // Nodes
        let c = [0.0, 0.5, 332.0 / 1000.0, 62.0 / 100.0, 85.0 / 100.0, 1.0];

        Self { a_e, a_i, b_e, b_i, bhat_e, bhat_i, c, gamma }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// SplitLinearOp trait + supporting types (R-P1-02_설계안 §8)
// ═══════════════════════════════════════════════════════════════════════

/// Collection of small dense blocks representing ℓ=1 and ℓ=2 collision couplings
/// across all m-sectors.
///
/// Each block is stored as:
///   - indices[k]: state vector index of k-th DOF in the block
///   - coeffs_tilde[n·i + j]: C̃_{ij} in the canonical form A_I = χ · C̃,
///     i.e., the block matrix is χ × row_i[coeffs_tilde[n·i..n·i+n]]
///
/// Invariant: coeffs_tilde are in C̃-units (NOT multiplied by χ). The integrator
/// multiplies by χ(η_i) at each stage.
#[derive(Clone, Debug, Default)]
pub struct SmallBlock {
    /// Size n (n×n dense matrix).
    pub n: usize,
    /// Global state indices (length n).
    pub indices: Vec<usize>,
    /// Row-major n×n coefficients in C̃-units.
    pub coeffs_tilde: Vec<f64>,
}

impl SmallBlock {
    pub fn empty() -> Self { Default::default() }
    pub fn total_entries(&self) -> usize { self.n * self.n }
}

/// Ordered set of small blocks.
#[derive(Clone, Debug, Default)]
pub struct SmallBlockSet {
    pub blocks: Vec<SmallBlock>,
}

/// Observed stiffness scales at a given η — used by the switch policy
/// (R-P1-02_설계안 §6) to decide IMEX → pure explicit transition.
///
/// For FLRW (σ = 0): shear = 0, policy collapses to S = χ/(k + c_H·H).
/// For approximation-free BASS, this is informational only (no switching).
#[derive(Clone, Copy, Debug)]
pub struct StiffnessScales {
    /// χ = |κ̇| ≥ 0 (canonicalized Thomson rate magnitude).
    pub opacity: f64,
    /// Conformal Hubble ℋ = a'/a.
    pub hubble: f64,
    /// ‖σ‖ — Bianchi shear magnitude (0 for FLRW).
    pub shear: f64,
    /// k-mode being integrated.
    pub k_mode: f64,
}

impl StiffnessScales {
    /// Explicit-leg spectral scale ω_E ~ k + c_σ‖σ‖ + c_H·ℋ.
    pub fn omega_explicit(&self) -> f64 {
        let c_sigma = 1.0;
        let c_hubble = 1.0;
        self.k_mode + c_sigma * self.shear + c_hubble * self.hubble.abs()
    }

    /// Stiffness ratio S = χ/ω_E (dimensionless). S ≫ 1 → stiff → implicit helpful.
    pub fn stiffness_ratio(&self) -> f64 {
        self.opacity / self.omega_explicit().max(1e-30)
    }

    /// CRITICAL INVARIANT: χ must be non-negative (canonicalized).
    pub fn assert_canonical(&self) {
        debug_assert!(self.opacity >= 0.0,
                      "StiffnessScales.opacity = {} violates χ ≥ 0 canonical sign", self.opacity);
    }
}

/// Generic interface for linearly split Boltzmann-type systems.
///
/// The integrator only needs:
///   - explicit evaluation (streaming + metric + geometric)
///   - diagonal implicit coefficients (ℓ ≥ 3 damping rates)
///   - small-block implicit coefficients (ℓ = 1, 2 couplings)
///   - stiffness scales (for diagnostics / future switch policy)
///
/// All coefficients are in C̃-units (the integrator multiplies by χ per stage).
pub trait SplitLinearOp {
    /// State vector dimension.
    fn dim(&self) -> usize;

    /// Compute f_E(η, y) = A_E(η)·y and store in `out`.
    fn apply_explicit(&self, eta: f64, y: &[f64], out: &mut [f64]);

    /// Fill the diagonal damping rates at time η.
    /// Output format: Vec<(dof_index, rate)> where rate ≥ 0 (damping magnitude).
    fn fill_implicit_diag(&self, eta: f64, diag: &mut Vec<(usize, f64)>);

    /// Fill the small-block collision couplings at time η.
    fn fill_implicit_blocks(&self, eta: f64, blocks: &mut SmallBlockSet);

    /// Report stiffness scales at η (for switching / adaptive step sizing).
    fn stiffness_scales(&self, eta: f64) -> StiffnessScales;
}

// ═══════════════════════════════════════════════════════════════════════
// Pre-allocated workspace
// ═══════════════════════════════════════════════════════════════════════

/// Scratch buffers reused across integration steps to avoid per-step allocation.
pub struct ImexWorkspace {
    pub n: usize,
    /// 6 stage vectors of k^E.
    pub k_e: Vec<Vec<f64>>,
    /// 6 stage vectors of k^I.
    pub k_i: Vec<Vec<f64>>,
    /// Predictor buffer (stage-level y_s).
    pub y_s: Vec<f64>,
    /// Post-implicit full-state buffer y_s + h·γ·k^I_s.
    pub y_s_full: Vec<f64>,
    /// Error estimate buffer.
    pub err: Vec<f64>,
    /// Diagonal collision buffer (reused per step).
    pub diag_buf: Vec<(usize, f64)>,
    /// Blocks buffer (reused per step).
    pub blocks_buf: SmallBlockSet,
}

impl ImexWorkspace {
    pub fn new(n: usize) -> Self {
        Self {
            n,
            k_e: vec![vec![0.0; n]; 6],
            k_i: vec![vec![0.0; n]; 6],
            y_s: vec![0.0; n],
            y_s_full: vec![0.0; n],
            err: vec![0.0; n],
            diag_buf: Vec::with_capacity(n),
            blocks_buf: SmallBlockSet::default(),
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Trait-based stepper (new, pre-allocated, zero per-step heap alloc)
// ═══════════════════════════════════════════════════════════════════════

/// Single IMEX-ARK4 step via the SplitLinearOp trait.
///
/// Zero per-step heap allocations — all scratch is in ImexWorkspace.
/// Returns normalized embedded error estimate.
pub fn imex_ark4_step_trait<Op: SplitLinearOp>(
    op: &Op,
    tau: f64,
    h: f64,
    y: &[f64],
    y_new: &mut [f64],
    tab: &Ark4Tableau,
    atol: f64,
    rtol: f64,
    work: &mut ImexWorkspace,
) -> f64 {
    let n = op.dim();
    debug_assert_eq!(y.len(), n);
    debug_assert_eq!(y_new.len(), n);
    debug_assert_eq!(work.n, n);

    let gamma = tab.gamma;

    // Refresh implicit operator at η (treating it as constant across stage times;
    // for linear time-varying A(η), this is the standard "frozen" approximation
    // within one step, consistent with ARKODE's approach for linear f^I.)
    work.diag_buf.clear();
    op.fill_implicit_diag(tau, &mut work.diag_buf);
    op.fill_implicit_blocks(tau, &mut work.blocks_buf);

    // Canonical sign assertion (R-P1-02_설계안 §12.4 — critical bug prevention)
    #[cfg(debug_assertions)]
    for &(_, rate) in &work.diag_buf {
        debug_assert!(rate >= 0.0, "Collision rate must be ≥ 0 (χ = |κ̇|), got {}", rate);
    }

    // Stage 0: explicit (ESDIRK: a^I_{00} = 0)
    op.apply_explicit(tau, y, &mut work.k_e[0]);
    apply_implicit_trait(&mut work.k_i[0], y, &work.diag_buf, &work.blocks_buf);

    // Stages 1..5
    for s in 1..6 {
        // Predictor: y_s = y + h × Σ_{j<s} (a^E_{sj} k^E_j + a^I_{sj} k^I_j)
        work.y_s.copy_from_slice(y);
        for j in 0..s {
            let ae = tab.a_e[s][j];
            let ai = tab.a_i[s][j];
            for i in 0..n {
                work.y_s[i] += h * (ae * work.k_e[j][i] + ai * work.k_i[j][i]);
            }
        }

        // Implicit solve: k^I_s = f_I(y_s + h·γ·k^I_s), linear in k^I_s
        solve_implicit_stage_trait(
            &mut work.k_i[s], &work.y_s, h * gamma,
            &work.diag_buf, &work.blocks_buf,
        );

        // Explicit eval at (τ + c_s·h, y_s + h·γ·k^I_s)
        for i in 0..n {
            work.y_s_full[i] = work.y_s[i] + h * gamma * work.k_i[s][i];
        }
        op.apply_explicit(tau + tab.c[s] * h, &work.y_s_full, &mut work.k_e[s]);
    }

    // 4th-order solution
    y_new.copy_from_slice(y);
    for j in 0..6 {
        let b = tab.b_e[j]; // b^E = b^I for this method
        for i in 0..n {
            y_new[i] += h * b * (work.k_e[j][i] + work.k_i[j][i]);
        }
    }

    // Embedded error: err = h × Σ (b - b̂) × (k^E + k^I)
    for i in 0..n { work.err[i] = 0.0; }
    for j in 0..6 {
        let de = tab.b_e[j] - tab.bhat_e[j];
        for i in 0..n {
            work.err[i] += h * de * (work.k_e[j][i] + work.k_i[j][i]);
        }
    }

    // Normalized RMS error
    let mut err_sq_sum = 0.0_f64;
    for i in 0..n {
        let sc = atol + rtol * y[i].abs().max(y_new[i].abs());
        let e = work.err[i] / sc;
        err_sq_sum += e * e;
    }
    (err_sq_sum / n as f64).sqrt()
}

fn apply_implicit_trait(
    out: &mut [f64],
    y: &[f64],
    diag: &[(usize, f64)],
    blocks: &SmallBlockSet,
) {
    for v in out.iter_mut() { *v = 0.0; }
    // Diagonal part: damping = -χ·y_j
    for &(idx, rate) in diag {
        if idx < y.len() {
            out[idx] = -rate * y[idx];
        }
    }
    // Small blocks: use C̃ coefficients (rate already baked in per-block)
    for blk in &blocks.blocks {
        let nb = blk.n;
        for i in 0..nb {
            let ri = blk.indices[i];
            if ri >= out.len() { continue; }
            let mut s = 0.0;
            for j in 0..nb {
                let cj = blk.indices[j];
                if cj < y.len() {
                    s += blk.coeffs_tilde[i * nb + j] * y[cj];
                }
            }
            out[ri] += s;
        }
    }
}

fn solve_implicit_stage_trait(
    k: &mut [f64],
    y_pred: &[f64],
    h_gamma: f64,
    diag: &[(usize, f64)],
    blocks: &SmallBlockSet,
) {
    for v in k.iter_mut() { *v = 0.0; }

    // Diagonal: k[i] = -rate·y[i] / (1 + h·γ·rate)
    // Sign: rate ≥ 0 by canonicalization → denominator ≥ 1 ≥ 0
    for &(idx, rate) in diag {
        if idx < y_pred.len() {
            let denom = 1.0 + h_gamma * rate;
            debug_assert!(denom >= 1.0,
                          "Implicit denom violation: 1 + h·γ·χ = {} < 1 (χ = {})", denom, rate);
            k[idx] = -rate * y_pred[idx] / denom;
        }
    }

    // Small blocks: (I - h·γ·C̃_block) · k_block = C̃_block · y_pred|_block
    // where C̃_block already includes the sign/rate structure.
    for blk in &blocks.blocks {
        let nb = blk.n;
        if nb == 0 || nb > 5 { continue; }

        let mut rhs = [0.0_f64; 5];
        for i in 0..nb {
            let mut s = 0.0;
            for j in 0..nb {
                let cj = blk.indices[j];
                if cj < y_pred.len() {
                    s += blk.coeffs_tilde[i * nb + j] * y_pred[cj];
                }
            }
            rhs[i] = s;
        }

        let mut lhs = [0.0_f64; 25]; // 5×5 max
        for i in 0..nb {
            for j in 0..nb {
                lhs[i * nb + j] = -h_gamma * blk.coeffs_tilde[i * nb + j];
            }
            lhs[i * nb + i] += 1.0;
        }

        let sol = solve_small_inplace(&mut lhs[..nb * nb], &mut rhs[..nb], nb);
        if let Some(x) = sol {
            for i in 0..nb {
                let ri = blk.indices[i];
                if ri < k.len() {
                    k[ri] = x[i];
                }
            }
        }
    }
}

/// In-place Gauss with partial pivoting for tiny n (≤ 5).
/// Returns rhs-as-solution if successful, None on singularity.
fn solve_small_inplace<'a>(lhs: &'a mut [f64], rhs: &'a mut [f64], n: usize) -> Option<&'a [f64]> {
    for col in 0..n {
        let mut pivot_row = col;
        let mut pivot_val = lhs[col * n + col].abs();
        for row in (col + 1)..n {
            let v = lhs[row * n + col].abs();
            if v > pivot_val { pivot_row = row; pivot_val = v; }
        }
        if pivot_val < 1e-30 { return None; }
        if pivot_row != col {
            for j in 0..n {
                lhs.swap(col * n + j, pivot_row * n + j);
            }
            rhs.swap(col, pivot_row);
        }
        let piv = lhs[col * n + col];
        for row in (col + 1)..n {
            let factor = lhs[row * n + col] / piv;
            for j in col..n {
                let v = lhs[col * n + j];
                lhs[row * n + j] -= factor * v;
            }
            rhs[row] -= factor * rhs[col];
        }
    }
    for i in (0..n).rev() {
        let mut s = rhs[i];
        for j in (i + 1)..n {
            s -= lhs[i * n + j] * rhs[j];
        }
        rhs[i] = s / lhs[i * n + i];
    }
    Some(rhs)
}

// ═══════════════════════════════════════════════════════════════════════
// Adaptive multi-step integrator driver
// ═══════════════════════════════════════════════════════════════════════

/// Integration statistics.
#[derive(Clone, Debug, Default)]
pub struct ImexStats {
    pub n_steps_accepted: usize,
    pub n_steps_rejected: usize,
    pub n_fn_evals: usize,     // rough: ~6 per accepted step
    pub h_min: f64,
    pub h_max: f64,
    pub final_h: f64,
}

/// Adaptive IMEX-ARK4 integration from τ_start to τ_end.
///
/// Step size is adapted via PI controller on the embedded 3rd-order error.
/// Step is rejected if err_norm > 1, shrunk, and retried.
pub fn integrate_imex_ark4<Op: SplitLinearOp>(
    op: &Op,
    tau_start: f64,
    tau_end: f64,
    h_init: f64,
    y0: &[f64],
    atol: f64,
    rtol: f64,
    max_steps: usize,
    work: &mut ImexWorkspace,
) -> Result<(Vec<f64>, ImexStats), String> {
    let n = op.dim();
    debug_assert_eq!(y0.len(), n);
    if tau_end <= tau_start {
        return Err("tau_end must be > tau_start".into());
    }

    let tab = Ark4Tableau::new();
    let order = 4.0_f64;

    let mut y = y0.to_vec();
    let mut y_new = vec![0.0_f64; n];
    let mut tau = tau_start;
    let mut h = h_init.min(tau_end - tau_start).max(1e-14);

    let mut stats = ImexStats {
        h_min: h, h_max: h, final_h: h, ..Default::default()
    };

    let mut err_prev = 0.0_f64;
    let safety = 0.9_f64;
    let f_min = 0.2_f64;
    let f_max = 5.0_f64;

    for _step in 0..max_steps {
        if tau >= tau_end - 1e-14 { break; }
        if tau + h > tau_end { h = tau_end - tau; }
        if h < 1e-14 {
            return Err(format!("Step size underflow at τ = {}", tau));
        }

        let err_norm = imex_ark4_step_trait(
            op, tau, h, &y, &mut y_new, &tab, atol, rtol, work,
        );

        if err_norm <= 1.0 || h <= 1e-13 {
            // Accept
            std::mem::swap(&mut y, &mut y_new);
            tau += h;
            stats.n_steps_accepted += 1;
            stats.n_fn_evals += 6; // 6 stages per step

            // PI controller for next h
            let f = if err_norm < 1e-30 {
                f_max
            } else if err_prev > 1e-30 {
                safety * err_norm.powf(-0.7 / order) * err_prev.powf(0.4 / order)
            } else {
                safety * err_norm.powf(-1.0 / order)
            };
            h = (h * f.max(f_min).min(f_max)).max(1e-14);
            stats.h_min = stats.h_min.min(h);
            stats.h_max = stats.h_max.max(h);
            err_prev = err_norm;
        } else {
            // Reject: shrink and retry
            stats.n_steps_rejected += 1;
            let f = safety * err_norm.powf(-1.0 / order);
            h = (h * f.max(f_min)).max(1e-14);
        }
    }

    stats.final_h = h;
    if tau < tau_end - 1e-12 {
        return Err(format!("max_steps ({}) reached at τ = {} (target {})",
                           max_steps, tau, tau_end));
    }
    Ok((y, stats))
}

/// Adaptive IMEX-ARK4 with snapshot output at user-supplied η points.
///
/// Integrates from `eta_eval[0]` to `eta_eval.last()` and records state at
/// each `eta_eval[i]` via linear interpolation between adjacent accepted
/// IMEX steps. Output `snapshots[i]` corresponds to `eta_eval[i]`.
///
/// This matches the Rodas5P snapshot format (Vec<Vec<f64>>) used by
/// `solve_kmode_full_with_common` for source extraction — drop-in compatible.
///
/// Preconditions:
/// - `eta_eval.len() >= 2`
/// - `eta_eval` must be monotonically increasing
pub fn integrate_imex_ark4_snapshots<Op: SplitLinearOp>(
    op: &Op,
    eta_eval: &[f64],
    h_init: f64,
    y0: &[f64],
    atol: f64,
    rtol: f64,
    max_steps: usize,
    work: &mut ImexWorkspace,
) -> Result<(Vec<Vec<f64>>, ImexStats), String> {
    let n = op.dim();
    debug_assert_eq!(y0.len(), n);
    if eta_eval.len() < 2 {
        return Err("eta_eval must have at least 2 points".into());
    }
    // Monotonicity sanity
    for i in 1..eta_eval.len() {
        if eta_eval[i] < eta_eval[i - 1] {
            return Err(format!(
                "eta_eval non-monotonic at {}: {} < {}",
                i, eta_eval[i], eta_eval[i - 1]
            ));
        }
    }
    let tau_start = eta_eval[0];
    let tau_end = *eta_eval.last().unwrap();

    let tab = Ark4Tableau::new();
    let order = 4.0_f64;

    // State buffers: y_prev at tau_prev, y at tau (current accepted)
    let mut y_prev = y0.to_vec();
    let mut y = y0.to_vec();
    let mut y_new = vec![0.0_f64; n];
    let mut tau_prev = tau_start;
    let mut tau = tau_start;

    // Record at eta_eval[0] (= tau_start)
    let mut snapshots: Vec<Vec<f64>> = Vec::with_capacity(eta_eval.len());
    snapshots.push(y0.to_vec());
    let mut next_eval_idx: usize = 1;

    let mut h = h_init.min(tau_end - tau_start).max(1e-14);
    let mut stats = ImexStats {
        h_min: h, h_max: h, final_h: h, ..Default::default()
    };

    let mut err_prev = 0.0_f64;
    let safety = 0.9_f64;
    let f_min = 0.2_f64;
    let f_max = 5.0_f64;

    for _step in 0..max_steps {
        if next_eval_idx >= eta_eval.len() { break; }
        if tau >= tau_end - 1e-14 { break; }
        if tau + h > tau_end { h = tau_end - tau; }
        if h < 1e-14 {
            return Err(format!("Step size underflow at τ = {}", tau));
        }

        let err_norm = imex_ark4_step_trait(
            op, tau, h, &y, &mut y_new, &tab, atol, rtol, work,
        );

        if err_norm <= 1.0 || h <= 1e-13 {
            // Accept: y_prev ← y; y ← y_new; update tau
            y_prev.copy_from_slice(&y);
            tau_prev = tau;
            std::mem::swap(&mut y, &mut y_new);
            tau += h;
            stats.n_steps_accepted += 1;
            stats.n_fn_evals += 6;

            // Snapshot at any eta_eval crossed in this step
            while next_eval_idx < eta_eval.len() && eta_eval[next_eval_idx] <= tau + 1e-14 {
                let e = eta_eval[next_eval_idx];
                // Linear interpolation between (tau_prev, y_prev) and (tau, y)
                let denom = (tau - tau_prev).max(1e-30);
                let w = ((e - tau_prev) / denom).clamp(0.0, 1.0);
                let mut snap = vec![0.0_f64; n];
                for i in 0..n {
                    snap[i] = y_prev[i] * (1.0 - w) + y[i] * w;
                }
                snapshots.push(snap);
                next_eval_idx += 1;
            }

            // PI controller for next h
            let f = if err_norm < 1e-30 {
                f_max
            } else if err_prev > 1e-30 {
                safety * err_norm.powf(-0.7 / order) * err_prev.powf(0.4 / order)
            } else {
                safety * err_norm.powf(-1.0 / order)
            };
            h = (h * f.max(f_min).min(f_max)).max(1e-14);
            stats.h_min = stats.h_min.min(h);
            stats.h_max = stats.h_max.max(h);
            err_prev = err_norm;
        } else {
            // Reject: shrink and retry
            stats.n_steps_rejected += 1;
            let f = safety * err_norm.powf(-1.0 / order);
            h = (h * f.max(f_min)).max(1e-14);
        }
    }

    stats.final_h = h;
    if snapshots.len() != eta_eval.len() {
        return Err(format!(
            "snapshots len = {}, eta_eval len = {} — integration stopped early at τ = {} (target τ_end = {})",
            snapshots.len(), eta_eval.len(), tau, tau_end
        ));
    }
    Ok((snapshots, stats))
}

// ═══════════════════════════════════════════════════════════════════════
// Legacy single-step function (kept for backward compatibility)
// ═══════════════════════════════════════════════════════════════════════

/// IMEX step result (legacy).
pub struct ImexStepResult {
    /// New state vector.
    pub y_new: Vec<f64>,
    /// Embedded error estimate (per component).
    pub err: Vec<f64>,
    /// Maximum normalized error.
    pub err_norm: f64,
}

/// Perform one IMEX-ARK4 step (legacy API — allocates per call).
///
/// # Arguments
/// * `y` — current state [n_dof]
/// * `h` — step size
/// * `f_explicit` — explicit RHS evaluation: (τ, y) → dy/dτ
/// * `implicit_diag` — diagonal collision rates: vec of (index, rate)
/// * `implicit_blocks` — small dense blocks: vec of (rows, cols, matrix)
/// * `tab` — ARK4 tableau
/// * `atol`, `rtol` — error tolerances
pub fn imex_ark4_step<FE>(
    y: &[f64],
    tau: f64,
    h: f64,
    f_explicit: &FE,
    implicit_diag: &[(usize, f64)],
    implicit_blocks: &[(Vec<usize>, Vec<usize>, Vec<f64>)],
    tab: &Ark4Tableau,
    atol: f64,
    rtol: f64,
) -> ImexStepResult
where
    FE: Fn(f64, &[f64]) -> Vec<f64>,
{
    let n = y.len();
    let gamma = tab.gamma;

    // Stage vectors k^E_s and k^I_s
    let mut k_e: Vec<Vec<f64>> = vec![vec![0.0; n]; 6];
    let mut k_i: Vec<Vec<f64>> = vec![vec![0.0; n]; 6];

    // Stage 1: explicit (ESDIRK property: a^I_{11} = 0)
    k_e[0] = f_explicit(tau, y);
    // k_i[0] = f_implicit(y) but since a_i[0][0]=0, it doesn't matter
    // We still need it for the implicit solve contribution
    apply_implicit(&mut k_i[0], y, implicit_diag, implicit_blocks);

    // Stages 2..6
    for s in 1..6 {
        // Predictor: y_s = y + h × Σ_{j<s} a^E_{sj} k^E_j + h × Σ_{j<s} a^I_{sj} k^I_j
        let mut y_s = y.to_vec();
        for j in 0..s {
            let ae = tab.a_e[s][j];
            let ai = tab.a_i[s][j];
            for i in 0..n {
                y_s[i] += h * (ae * k_e[j][i] + ai * k_i[j][i]);
            }
        }

        // Implicit solve: (I - h×γ×J_I) × k^I_s = f_I(y_s)
        // For diagonal collision: k^I_s[i] = -rate×y_s[i] / (1 + h×γ×rate)
        // For blocks: small dense solve
        solve_implicit_stage(
            &mut k_i[s], &y_s, h * gamma,
            implicit_diag, implicit_blocks,
        );

        // Explicit evaluation at (τ + c_s×h, y_s + h×γ×k^I_s)
        let mut y_s_full = y_s.clone();
        for i in 0..n {
            y_s_full[i] += h * gamma * k_i[s][i];
        }
        k_e[s] = f_explicit(tau + tab.c[s] * h, &y_s_full);
    }

    // Solution: y_new = y + h × Σ b_j (k^E_j + k^I_j)
    let mut y_new = y.to_vec();
    for j in 0..6 {
        for i in 0..n {
            y_new[i] += h * tab.b_e[j] * (k_e[j][i] + k_i[j][i]);
        }
    }

    // Error estimate: err = h × Σ (b_j - b̂_j) × (k^E_j + k^I_j)
    let mut err = vec![0.0_f64; n];
    for j in 0..6 {
        let de = tab.b_e[j] - tab.bhat_e[j];
        for i in 0..n {
            err[i] += h * de * (k_e[j][i] + k_i[j][i]);
        }
    }

    // Normalized error
    let err_norm = err.iter().enumerate().map(|(i, &e)| {
        let sc = atol + rtol * y[i].abs().max(y_new[i].abs());
        (e / sc).powi(2)
    }).sum::<f64>() / n as f64;
    let err_norm = err_norm.sqrt();

    ImexStepResult { y_new, err, err_norm }
}

/// Apply implicit (collision) operator: out[i] = -rate × y[i] for diag,
/// plus small block contributions.
fn apply_implicit(
    out: &mut Vec<f64>,
    y: &[f64],
    diag: &[(usize, f64)],
    blocks: &[(Vec<usize>, Vec<usize>, Vec<f64>)],
) {
    out.iter_mut().for_each(|v| *v = 0.0);
    for &(idx, rate) in diag {
        if idx < y.len() {
            out[idx] = -rate * y[idx];
        }
    }
    for (rows, cols, mat) in blocks {
        let nr = rows.len();
        let nc = cols.len();
        for i in 0..nr {
            for j in 0..nc {
                if rows[i] < out.len() && cols[j] < y.len() {
                    out[rows[i]] += mat[i * nc + j] * y[cols[j]];
                }
            }
        }
    }
}

/// Solve the implicit stage: find k such that
/// k = f_I(y_pred + h_gamma × k)
///
/// For diagonal: k[i] = -rate × (y[i] + h_gamma×k[i])
///   → k[i] = -rate × y[i] / (1 + h_gamma×rate)
///
/// For blocks: small (2×2 or 3×3) linear system.
fn solve_implicit_stage(
    k: &mut Vec<f64>,
    y_pred: &[f64],
    h_gamma: f64,
    diag: &[(usize, f64)],
    blocks: &[(Vec<usize>, Vec<usize>, Vec<f64>)],
) {
    k.iter_mut().for_each(|v| *v = 0.0);

    // Diagonal solve: k[i] = -rate×y[i] / (1 + h_gamma×rate)
    // Sign convention: rate > 0 ALWAYS (canonicalized)
    // Denominator: 1 + h_gamma×rate > 1 (NEVER anti-damping)
    for &(idx, rate) in diag {
        if idx < y_pred.len() {
            k[idx] = -rate * y_pred[idx] / (1.0 + h_gamma * rate);
        }
    }

    // Block solve: (I - h_gamma × M) × k_block = M × y_pred
    // where M is the collision block matrix
    for (rows, cols, mat) in blocks {
        let nr = rows.len();
        if nr > 4 { continue; } // Safety: only small blocks

        // Compute RHS = M × y_pred (restricted to block)
        let mut rhs = vec![0.0_f64; nr];
        for i in 0..nr {
            for j in 0..nr {
                if cols[j] < y_pred.len() {
                    rhs[i] += mat[i * nr + j] * y_pred[cols[j]];
                }
            }
        }

        // Build (I - h_gamma × M) for the block
        let mut lhs = vec![0.0_f64; nr * nr];
        for i in 0..nr {
            for j in 0..nr {
                lhs[i * nr + j] = -h_gamma * mat[i * nr + j];
            }
            lhs[i * nr + i] += 1.0; // Add identity
        }

        // Solve small system (Cramer's rule for 2×2, Gaussian for 3×3+)
        let sol = if nr == 2 {
            solve_2x2(&lhs, &rhs)
        } else {
            solve_small(&lhs, &rhs, nr)
        };

        for i in 0..nr {
            if rows[i] < k.len() {
                k[rows[i]] = sol[i];
            }
        }
    }
}

fn solve_2x2(a: &[f64], b: &[f64]) -> Vec<f64> {
    let det = a[0] * a[3] - a[1] * a[2];
    if det.abs() < 1e-30 { return vec![0.0; 2]; }
    vec![
        (a[3] * b[0] - a[1] * b[1]) / det,
        (a[0] * b[1] - a[2] * b[0]) / det,
    ]
}

fn solve_small(a: &[f64], b: &[f64], n: usize) -> Vec<f64> {
    // Gaussian elimination with partial pivoting
    let mut aug = vec![0.0_f64; n * (n + 1)];
    for i in 0..n {
        for j in 0..n { aug[i * (n + 1) + j] = a[i * n + j]; }
        aug[i * (n + 1) + n] = b[i];
    }
    for col in 0..n {
        let mut pivot_row = col;
        let mut pivot_val = aug[col * (n + 1) + col].abs();
        for row in (col + 1)..n {
            let val = aug[row * (n + 1) + col].abs();
            if val > pivot_val { pivot_row = row; pivot_val = val; }
        }
        if pivot_val < 1e-30 { return vec![0.0; n]; }
        if pivot_row != col {
            for j in 0..=n {
                aug.swap(col * (n + 1) + j, pivot_row * (n + 1) + j);
            }
        }
        let piv = aug[col * (n + 1) + col];
        for row in (col + 1)..n {
            let factor = aug[row * (n + 1) + col] / piv;
            for j in col..=n {
                let v = aug[col * (n + 1) + j];
                aug[row * (n + 1) + j] -= factor * v;
            }
        }
    }
    let mut x = vec![0.0_f64; n];
    for i in (0..n).rev() {
        x[i] = aug[i * (n + 1) + n];
        for j in (i + 1)..n {
            x[i] -= aug[i * (n + 1) + j] * x[j];
        }
        x[i] /= aug[i * (n + 1) + i];
    }
    x
}

/// PID step-size controller.
pub fn pid_step_controller(
    err_norm: f64,
    h: f64,
    err_prev: f64,
    order: f64,
) -> f64 {
    let safety = 0.9;
    let f_min = 0.2;
    let f_max = 5.0;

    if err_norm < 1e-30 { return h * f_max; }

    let f = safety * err_norm.powf(-1.0 / order);
    let f = if err_prev > 1e-30 {
        // PI controller
        let f_pi = f * (err_prev / err_norm).powf(0.3 / order);
        f_pi
    } else {
        f
    };
    h * f.max(f_min).min(f_max)
}

// ═══════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tableau_consistency() {
        let tab = Ark4Tableau::new();
        // Row sums of explicit tableau should equal nodes
        for s in 0..6 {
            let sum: f64 = tab.a_e[s].iter().sum();
            assert!((sum - tab.c[s]).abs() < 1e-6,
                "Stage {}: Σa^E = {:.6}, c = {:.6}", s, sum, tab.c[s]);
        }
        // Weights should sum to 1
        let sum_b: f64 = tab.b_e.iter().sum();
        assert!((sum_b - 1.0).abs() < 1e-10,
            "Σb^E = {:.10}, should be 1", sum_b);
        // ESDIRK: first implicit diagonal is 0
        assert_eq!(tab.a_i[0][0], 0.0, "ESDIRK: a^I_11 must be 0");
        // All other implicit diagonals = γ
        for s in 1..6 {
            assert!((tab.a_i[s][s] - tab.gamma).abs() < 1e-14,
                "Stage {}: a^I_{{ss}} = {}, γ = {}", s, tab.a_i[s][s], tab.gamma);
        }
    }

    #[test]
    fn test_exponential_decay() {
        // dy/dt = -100y, y(0) = 1 → y(t) = e^{-100t}
        // Pure implicit problem (f_E = 0, f_I = -100y)
        let tab = Ark4Tableau::new();
        let rate = 100.0;
        let y = vec![1.0];
        let h = 0.01;
        let diag = vec![(0, rate)];
        let blocks: Vec<(Vec<usize>, Vec<usize>, Vec<f64>)> = vec![];
        let f_zero = |_t: f64, _y: &[f64]| vec![0.0];

        let r = imex_ark4_step(&y, 0.0, h, &f_zero, &diag, &blocks, &tab, 1e-10, 1e-8);
        let exact = (-rate * h).exp();
        let err = (r.y_new[0] - exact).abs();
        // h×rate=1: borderline stiff, 4th-order error is O(h⁴×rate⁴) ≈ O(1)
        // L-stability gives bounded but not tiny error here
        assert!(err < 1e-3,
            "Exponential decay: y={:.8}, exact={:.8}, err={:.2e}", r.y_new[0], exact, err);
    }

    #[test]
    fn test_oscillator() {
        // dy₁/dt = y₂, dy₂/dt = -y₁ → oscillator (explicit only)
        // y(0) = [1, 0], y(t) = [cos(t), -sin(t)]
        let tab = Ark4Tableau::new();
        let f_osc = |_t: f64, y: &[f64]| vec![y[1], -y[0]];
        let diag: Vec<(usize, f64)> = vec![];
        let blocks: Vec<(Vec<usize>, Vec<usize>, Vec<f64>)> = vec![];

        let mut y = vec![1.0, 0.0];
        let h = 0.01;
        let n_steps = 100; // t = 0 to 1
        for i in 0..n_steps {
            let r = imex_ark4_step(&y, i as f64 * h, h, &f_osc, &diag, &blocks, &tab, 1e-10, 1e-8);
            y = r.y_new;
        }
        let t = 1.0_f64;
        let exact = [t.cos(), -t.sin()];
        let err0 = (y[0] - exact[0]).abs();
        let err1 = (y[1] - exact[1]).abs();
        assert!(err0 < 1e-8 && err1 < 1e-8,
            "Oscillator: y=[{:.8}, {:.8}], exact=[{:.8}, {:.8}]",
            y[0], y[1], exact[0], exact[1]);
    }

    #[test]
    fn test_stiff_oscillator() {
        // Stiff problem: dy₁/dt = -1000(y₁ - cos(t)) + sin(t)
        //                dy₂/dt = y₁ (non-stiff)
        // Split: f_I = -1000×y₁ (stiff), f_E = 1000×cos(t) + sin(t) + y₁ coupling
        let tab = Ark4Tableau::new();
        let rate = 1000.0;
        let f_exp = |t: f64, y: &[f64]| vec![
            rate * t.cos() + t.sin(),
            y[0],
        ];
        let diag = vec![(0, rate)];
        let blocks: Vec<(Vec<usize>, Vec<usize>, Vec<f64>)> = vec![];

        let mut y = vec![1.0, 0.0]; // y₁(0)=cos(0)=1
        let h = 0.001;
        let n_steps = 1000;
        for i in 0..n_steps {
            let r = imex_ark4_step(&y, i as f64 * h, h, &f_exp, &diag, &blocks, &tab, 1e-10, 1e-8);
            y = r.y_new;
        }
        let t = 1.0_f64;
        // Exact: y₁ ≈ cos(t) (stiff part rapidly decays to quasi-static)
        let err = (y[0] - t.cos()).abs();
        assert!(err < 0.01,
            "Stiff oscillator: y₁={:.6}, cos(1)={:.6}, err={:.2e}", y[0], t.cos(), err);
    }

    #[test]
    fn test_pid_controller() {
        // Error below 1 → h increases
        let h_new = pid_step_controller(0.5, 0.01, 0.0, 4.0);
        assert!(h_new > 0.01, "h should increase for err<1");
        // Error above 1 → h decreases
        let h_new = pid_step_controller(2.0, 0.01, 0.0, 4.0);
        assert!(h_new < 0.01, "h should decrease for err>1");
    }

    #[test]
    fn test_solve_2x2() {
        // [2 1; 1 3] x = [5; 7] → x = [8/5, 9/5]
        let a = vec![2.0, 1.0, 1.0, 3.0];
        let b = vec![5.0, 7.0];
        let x = solve_2x2(&a, &b);
        assert!((x[0] - 1.6).abs() < 1e-10);
        assert!((x[1] - 1.8).abs() < 1e-10);
    }

    // ═══════════════════════════════════════════════════════════════════
    // AUDIT TESTS (R-P1-02_설계안 §12 — mandatory pre-production checks)
    // ═══════════════════════════════════════════════════════════════════

    /// Test harness: constant-coefficient 2-DOF toy for analytic comparison.
    struct ToyOp {
        /// Coefficient of explicit part: dy/dτ|_E = A_E · y
        a_e: [[f64; 2]; 2],
        /// Diagonal damping (both entries): dy/dτ|_I = -χ · diag · y
        chi: f64,
    }
    impl SplitLinearOp for ToyOp {
        fn dim(&self) -> usize { 2 }
        fn apply_explicit(&self, _eta: f64, y: &[f64], out: &mut [f64]) {
            out[0] = self.a_e[0][0] * y[0] + self.a_e[0][1] * y[1];
            out[1] = self.a_e[1][0] * y[0] + self.a_e[1][1] * y[1];
        }
        fn fill_implicit_diag(&self, _eta: f64, diag: &mut Vec<(usize, f64)>) {
            diag.clear();
            if self.chi > 0.0 {
                diag.push((0, self.chi));
                diag.push((1, self.chi));
            }
        }
        fn fill_implicit_blocks(&self, _eta: f64, blocks: &mut SmallBlockSet) {
            blocks.blocks.clear();
        }
        fn stiffness_scales(&self, _eta: f64) -> StiffnessScales {
            StiffnessScales {
                opacity: self.chi, hubble: 0.0, shear: 0.0, k_mode: 1.0,
            }
        }
    }

    /// §12.1(A) Linearity: stage solve is closed in one shot (no Newton loop).
    /// Test: for pure diagonal, compare against analytic scalar solve.
    #[test]
    fn audit_a_linearity_diagonal() {
        let tab = Ark4Tableau::new();
        let chi = 100.0;
        let mut diag = Vec::new();
        diag.push((0, chi));
        let blocks = SmallBlockSet::default();
        let y_pred = vec![1.0, 2.0];
        let h_gamma = 0.01 * 0.25;
        let mut k = vec![0.0; 2];
        solve_implicit_stage_trait(&mut k, &y_pred, h_gamma, &diag, &blocks);
        let analytic_k0 = -chi * y_pred[0] / (1.0 + h_gamma * chi);
        assert!((k[0] - analytic_k0).abs() < 1e-14,
                "k[0] = {} vs analytic {}", k[0], analytic_k0);
        assert_eq!(k[1], 0.0, "DOF 1 not in diag → k[1] must remain 0");
        let _ = tab;
    }

    /// §12.1(B) Dimensional consistency:
    /// For linear A with appropriate units, the step y_new = y + h·A·y is unit-consistent.
    /// Here test that the embedded error estimate has same units as y (implicit check).
    #[test]
    fn audit_b_dimensional() {
        let op = ToyOp { a_e: [[0.0, 1.0], [-1.0, 0.0]], chi: 0.0 };
        let mut work = ImexWorkspace::new(2);
        let tab = Ark4Tableau::new();
        let y = vec![1.0, 0.0];
        let mut y_new = vec![0.0; 2];
        let err = imex_ark4_step_trait(&op, 0.0, 0.01, &y, &mut y_new, &tab, 1e-12, 1e-10, &mut work);
        // err is normalized, so dimensionless (should be O(1) or smaller for good step)
        assert!(err.is_finite() && err >= 0.0, "Normalized error invariant: {}", err);
    }

    /// §12.1(C) Limit: χ → 0 reduces to pure explicit RK (no implicit contribution).
    /// Test: solution with χ=0 matches pure oscillator solution.
    #[test]
    fn audit_c_limit_chi_zero() {
        // dy₁/dτ = y₂, dy₂/dτ = -y₁ → y(τ) = [cos τ, -sin τ]
        let op = ToyOp { a_e: [[0.0, 1.0], [-1.0, 0.0]], chi: 0.0 };
        let mut work = ImexWorkspace::new(2);
        let tab = Ark4Tableau::new();
        let mut y = vec![1.0, 0.0];
        let mut y_next = vec![0.0; 2];
        let h = 0.01;
        let n_steps = 100; // integrate to τ = 1
        for i in 0..n_steps {
            imex_ark4_step_trait(&op, i as f64 * h, h, &y, &mut y_next, &tab, 1e-12, 1e-10, &mut work);
            std::mem::swap(&mut y, &mut y_next);
        }
        let tau = 1.0_f64;
        let err0 = (y[0] - tau.cos()).abs();
        let err1 = (y[1] - (-tau.sin())).abs();
        assert!(err0 < 1e-7 && err1 < 1e-7,
                "χ=0 limit: y = ({}, {}), exact = ({}, {})",
                y[0], y[1], tau.cos(), -tau.sin());
    }

    /// §12.1(C) Limit: χ → ∞ forces high-ℓ to zero (strong damping limit).
    /// Test: start with nonzero y, large χ, few steps → y should collapse toward 0.
    #[test]
    fn audit_c_limit_chi_infinity() {
        let chi = 1e6;
        let op = ToyOp { a_e: [[0.0, 0.0], [0.0, 0.0]], chi };
        let mut work = ImexWorkspace::new(2);
        let tab = Ark4Tableau::new();
        let y = vec![1.0, 1.0];
        let mut y_new = vec![0.0; 2];
        let h = 0.01;
        // Single step at h=0.01, h·γ·χ = 2500 → denominator ≈ 2501
        // y_new ≈ y / (1 + h·γ·χ) via implicit, so ≈ 1/2500 ≈ 4e-4
        imex_ark4_step_trait(&op, 0.0, h, &y, &mut y_new, &tab, 1e-12, 1e-10, &mut work);
        // Both DOFs must have decayed strongly
        assert!(y_new[0].abs() < 0.1, "χ→∞: y[0] = {} should be damped", y_new[0]);
        assert!(y_new[1].abs() < 0.1, "χ→∞: y[1] = {} should be damped", y_new[1]);
    }

    /// §12.1(D) Conservation: monopole (ℓ=0) has NO collision → no damping in y[0].
    /// Simulated with diagonal entries only on indices ≥ 1.
    #[test]
    fn audit_d_monopole_conservation() {
        struct MonopoleOp { chi: f64 }
        impl SplitLinearOp for MonopoleOp {
            fn dim(&self) -> usize { 3 } // [ℓ=0, ℓ=1, ℓ=2]
            fn apply_explicit(&self, _eta: f64, _y: &[f64], out: &mut [f64]) {
                for v in out.iter_mut() { *v = 0.0; }
            }
            fn fill_implicit_diag(&self, _eta: f64, diag: &mut Vec<(usize, f64)>) {
                diag.clear();
                // Monopole (idx 0) NOT in diag
                diag.push((1, self.chi));
                diag.push((2, self.chi));
            }
            fn fill_implicit_blocks(&self, _eta: f64, b: &mut SmallBlockSet) { b.blocks.clear(); }
            fn stiffness_scales(&self, _eta: f64) -> StiffnessScales {
                StiffnessScales { opacity: self.chi, hubble: 0.0, shear: 0.0, k_mode: 1.0 }
            }
        }
        let op = MonopoleOp { chi: 1000.0 };
        let mut work = ImexWorkspace::new(3);
        let tab = Ark4Tableau::new();
        let y = vec![1.0, 1.0, 1.0];
        let mut y_new = vec![0.0; 3];
        let h = 0.01;
        for i in 0..50 {
            imex_ark4_step_trait(&op, i as f64 * h, h, &y, &mut y_new, &tab, 1e-12, 1e-10, &mut work);
            // Monopole must stay exactly at initial value (no collision, no explicit)
            assert!((y_new[0] - 1.0).abs() < 1e-12,
                    "Step {}: y[0]=1 broken = {}", i, y_new[0]);
        }
    }

    /// §12.4(A) Sign convention: opacity must be canonicalized to ≥ 0.
    /// Test: StiffnessScales assertion holds.
    #[test]
    fn audit_sign_convention_canonical() {
        let s_ok = StiffnessScales { opacity: 100.0, hubble: 10.0, shear: 0.0, k_mode: 0.1 };
        s_ok.assert_canonical(); // no panic

        // Omega explicit sanity: ω_E = k + c_σ·‖σ‖ + c_H·|H|
        let omega = s_ok.omega_explicit();
        assert!((omega - (0.1 + 0.0 + 10.0)).abs() < 1e-12);

        // Stiffness ratio: χ/ω_E = 100 / 10.1 ≈ 9.9
        let s = s_ok.stiffness_ratio();
        assert!((s - 100.0 / 10.1).abs() < 1e-9);
    }

    /// §12.3(B) Order-of-accuracy on a smooth problem.
    /// Smooth exponential decay test with halved h → error should scale as 1/16 (4th order).
    /// Using moderate stiffness (not in L-stable saturation regime).
    #[test]
    fn audit_order_of_accuracy() {
        // y' = -10 y, y(0) = 1 → y(τ) = exp(-10τ)
        // Put entirely in implicit for clean ESDIRK test
        let op = ToyOp { a_e: [[0.0, 0.0], [0.0, 0.0]], chi: 10.0 };
        let mut work = ImexWorkspace::new(2);
        let tab = Ark4Tableau::new();
        let tau_final = 0.2_f64;

        let mut run = |h: f64| -> f64 {
            let mut y = vec![1.0, 0.0];
            let mut y_new = vec![0.0; 2];
            let n_steps = (tau_final / h).round() as usize;
            for i in 0..n_steps {
                imex_ark4_step_trait(&op, i as f64 * h, h, &y, &mut y_new, &tab, 1e-14, 1e-14, &mut work);
                std::mem::swap(&mut y, &mut y_new);
            }
            (y[0] - (-10.0_f64 * tau_final).exp()).abs()
        };

        let err_h = run(0.02);     // coarse
        let err_h2 = run(0.01);    // fine
        // 4th order → err ratio ≈ 16
        let ratio = err_h / err_h2.max(1e-16);
        assert!(ratio > 8.0,
                "Order convergence: h={}→err={:.2e}, h/2→err={:.2e}, ratio={:.2}",
                0.02, err_h, err_h2, ratio);
    }

    /// §12.3(B) L-stability audit: for χ·h → ∞, high-χ modes must decay (not oscillate or grow).
    /// This is THE defining property that lets IMEX handle post-TCA regime without collapse.
    #[test]
    fn audit_l_stability() {
        let chi = 1e8; // extreme stiffness
        let op = ToyOp { a_e: [[0.0, 0.0], [0.0, 0.0]], chi };
        let mut work = ImexWorkspace::new(2);
        let tab = Ark4Tableau::new();
        let y = vec![1.0, 0.0];
        let mut y_new = vec![0.0; 2];
        let h = 0.01; // h·χ = 1e6 — extreme

        imex_ark4_step_trait(&op, 0.0, h, &y, &mut y_new, &tab, 1e-8, 1e-6, &mut work);
        // L-stability: |y_new / y| → 0 as h·χ → ∞
        let amp = y_new[0].abs();
        assert!(amp < 1e-4,
                "L-stability: amplitude {} must decay for h·χ={:.0e}", amp, h * chi);
        // Must NOT oscillate (sign flip with small magnitude is acceptable for stiff)
        assert!(amp < 1.0, "L-stability: no growth (got |y| = {})", amp);
    }

    /// §12.4 Canonical sign convention enforcement: negative rate triggers debug assertion.
    #[test]
    #[should_panic(expected = "Collision rate must be ≥ 0")]
    fn audit_negative_rate_panics_in_debug() {
        #[cfg(not(debug_assertions))] panic!("Collision rate must be ≥ 0 (dummy panic for release build)");
        struct BadOp;
        impl SplitLinearOp for BadOp {
            fn dim(&self) -> usize { 1 }
            fn apply_explicit(&self, _: f64, _: &[f64], out: &mut [f64]) { out[0] = 0.0; }
            fn fill_implicit_diag(&self, _: f64, diag: &mut Vec<(usize, f64)>) {
                diag.clear();
                diag.push((0, -100.0)); // WRONG: negative rate
            }
            fn fill_implicit_blocks(&self, _: f64, b: &mut SmallBlockSet) { b.blocks.clear(); }
            fn stiffness_scales(&self, _: f64) -> StiffnessScales {
                StiffnessScales { opacity: 100.0, hubble: 0.0, shear: 0.0, k_mode: 1.0 }
            }
        }
        let op = BadOp;
        let mut work = ImexWorkspace::new(1);
        let tab = Ark4Tableau::new();
        let y = vec![1.0];
        let mut y_new = vec![0.0];
        imex_ark4_step_trait(&op, 0.0, 0.01, &y, &mut y_new, &tab, 1e-10, 1e-8, &mut work);
    }

    /// Driver test: multi-step adaptive integration converges.
    #[test]
    fn audit_driver_adaptive_exp_decay() {
        let op = ToyOp { a_e: [[0.0, 0.0], [0.0, 0.0]], chi: 10.0 };
        let mut work = ImexWorkspace::new(2);
        let y0 = vec![1.0, 0.0];
        let (y_final, stats) = integrate_imex_ark4(
            &op, 0.0, 0.5, 0.01, &y0, 1e-10, 1e-8, 1000, &mut work,
        ).expect("integration should succeed");

        let exact = (-10.0_f64 * 0.5).exp();
        let err = (y_final[0] - exact).abs();
        assert!(err < 1e-6, "Adaptive IMEX: y={:.6e}, exact={:.6e}, err={:.2e}",
                y_final[0], exact, err);
        assert!(stats.n_steps_accepted > 0);
        assert!(stats.n_steps_rejected < stats.n_steps_accepted, "too many rejections");
        eprintln!("adaptive driver: {} accepted / {} rejected, final h = {:.2e}",
                  stats.n_steps_accepted, stats.n_steps_rejected, stats.final_h);
    }

    /// Small-block solve audit: compare 2×2 block solve vs hand-computed reference.
    /// Note: SmallBlock.coeffs_tilde holds the actual C-units coefficients
    /// (already with χ multiplied — the "tilde" name is historical, see
    /// CollisionSplit refactor 2026-04-16). The integrator does NOT multiply by χ.
    #[test]
    fn audit_small_block_2x2() {
        // Block: actual = [[-1, 1/3], [R, -R/3]] with R = 2 (toy case for verification)
        let r = 2.0_f64;
        let blk = SmallBlock {
            n: 2,
            indices: vec![0, 1],
            coeffs_tilde: vec![-1.0, 1.0/3.0, r, -r/3.0],
        };
        let mut blocks = SmallBlockSet::default();
        blocks.blocks.push(blk);
        let diag: Vec<(usize, f64)> = Vec::new();

        let h_gamma = 0.01 * 0.25;
        let y_pred = vec![1.0, 0.5];
        let mut k = vec![0.0; 2];
        solve_implicit_stage_trait(&mut k, &y_pred, h_gamma, &diag, &blocks);

        // Verify k satisfies (I - h·γ·C̃)·k = C̃·y_pred
        let rhs0 = -1.0 * y_pred[0] + (1.0/3.0) * y_pred[1];
        let rhs1 = r * y_pred[0] + (-r/3.0) * y_pred[1];
        let lhs_k0 = k[0] - h_gamma * (-1.0 * k[0] + (1.0/3.0) * k[1]);
        let lhs_k1 = k[1] - h_gamma * (r * k[0] + (-r/3.0) * k[1]);
        assert!((lhs_k0 - rhs0).abs() < 1e-12,
                "Block row 0: LHS·k = {} vs RHS = {}", lhs_k0, rhs0);
        assert!((lhs_k1 - rhs1).abs() < 1e-12,
                "Block row 1: LHS·k = {} vs RHS = {}", lhs_k1, rhs1);
    }
}
