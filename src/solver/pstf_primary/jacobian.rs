// ═══════════════════════════════════════════════════════════════════════
// PSTF Primary — Analytical Sparse Jacobian (PR-022c)
// ═══════════════════════════════════════════════════════════════════════
//
// Jacobian of the combined RHS (PR-022a free-streaming + PR-022b collision)
// with respect to the full PSTF state vector.  Rodas5P-compatible.
//
// ## Scope (PR-022c)
//
// For FLRW m=0 photon/neutrino hierarchy + baryon v_b drag, this module
// computes J[i,j] = ∂(dy[i]/dη)/∂y[j] analytically.
//
// Since the RHS (PR-022a + PR-022b, linear in state) produces linear
// equations, J is state-independent here.  The `state` parameter is
// accepted for interface consistency with nonlinear extensions (PR-023
// metric coupling may introduce mild state dependence via background).
//
// ## Sparsity
//
// Photon free-streaming (ℓ=0..ℓ_max, m=0):
//   - ℓ=0:      J[Θ_0, Θ_1] = −k
//   - ℓ=1:      J[Θ_1, Θ_0] = k/3,  J[Θ_1, Θ_2] = −2k/3
//   - 2≤ℓ<lmax: J[Θ_ℓ, Θ_{ℓ−1}] = k·ℓ/(2ℓ+1),  J[Θ_ℓ, Θ_{ℓ+1}] = −k·(ℓ+1)/(2ℓ+1)
//   - ℓ=lmax:   J[Θ_lmax, Θ_{lmax−1}] = k,  J[Θ_lmax, Θ_lmax] = −(lmax+1)/τ
// (Plus a structurally identical block for neutrinos.)
//
// Collision (photon only, pol-off default):
//   - ℓ=1:  J[Θ_1, Θ_1] += −κ̇,  J[Θ_1, v_b] += +κ̇/3
//   - ℓ=2:  J[Θ_2, Θ_2] += −κ̇  (or −0.9κ̇ + pol cross if pol on)
//   - ℓ≥3:  J[Θ_ℓ, Θ_ℓ] += −κ̇
//
// Baryon drag reaction:
//   - J[v_b, Θ_1] += 3κ̇/r_b
//   - J[v_b, v_b] += −κ̇/r_b
//
// ## What is NOT here
//
// - Metric coupling Jacobian:     PR-023
// - Jacobian caching across time: PR-024 (production)
// - Matrix-free Jacobian-vector:  future optimization
//
// ## Why linear state dependence
//
// Both PR-022a (free-streaming) and PR-022b (collision) are LINEAR in
// the photon/baryon state variables.  Background quantities (k, τ, κ̇,
// r_b) enter as parameters only.  So J = ∂(M·y)/∂y = M is just the
// linear operator matrix.  Nonlinear terms (if any, via T_eff or
// tilt²) are deferred to later PRs.

#![allow(dead_code)]

use super::layout::PstfFlrwLayout;
use super::rhs_free::{RhsInputs, pstf_free_streaming_rhs};
use super::collision::{CollisionInputs, FrameConvention, pstf_thomson_collision};
use super::metric::BackgroundQuantities;

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Jacobian inputs
// ═══════════════════════════════════════════════════════════════════════

/// Unified inputs for the Jacobian computation.
///
/// PR-022c-era scope: free-streaming (k, tau, metric_monopole_source) +
/// Thomson collision (kappa_dot, r_b, use_pol_feedback, frame).
///
/// PR-024c-PERF extension: metric + fluid Jacobian blocks need the
/// background energy densities and baryon sound speed.  These are
/// optional; if `extended = false`, metric/fluid contributions are
/// skipped (legacy PR-022c behaviour).
#[derive(Clone, Copy, Debug)]
pub(crate) struct JacobianInputs {
    pub(crate) k: f64,
    pub(crate) tau: f64,
    pub(crate) metric_monopole_source: f64,   // PR-023 placeholder
    pub(crate) kappa_dot: f64,
    pub(crate) r_b: f64,
    pub(crate) use_pol_feedback: bool,
    pub(crate) frame: FrameConvention,
    /// PR-024c-PERF: background for metric + fluid blocks.  Zero by
    /// default; call `with_metric_fluid_bg()` to populate.
    pub(crate) bg: BackgroundQuantities,
    /// PR-024c-PERF: baryon sound speed² for fluid block.
    pub(crate) cs2b: f64,
    /// PR-024c-PERF: when true, `pstf_analytical_jacobian` emits
    /// metric + fluid + metric-monopole-source triplets in addition
    /// to the PR-022c free-streaming + collision entries.
    pub(crate) use_metric_fluid_blocks: bool,
}

impl JacobianInputs {
    pub(crate) fn from_rhs_and_collision(
        rhs: &RhsInputs,
        collision: &CollisionInputs,
    ) -> Self {
        Self {
            k: rhs.k,
            tau: rhs.tau,
            metric_monopole_source: rhs.metric_monopole_source,
            kappa_dot: collision.kappa_dot,
            r_b: collision.r_b,
            use_pol_feedback: collision.use_pol_feedback,
            frame: collision.frame,
            bg: BackgroundQuantities::zero(),
            cs2b: 0.0,
            use_metric_fluid_blocks: false,
        }
    }

    /// PR-024c-PERF: enable metric + fluid Jacobian blocks.
    ///
    /// After calling this, `pstf_analytical_jacobian` produces a full-RHS
    /// Jacobian (free + collision + metric + fluid + monopole source).
    /// The resulting dense matrix is interchangeable with the unit-vector
    /// result from `build_pstf_matrix_into`, up to FP roundoff (not
    /// bit-identical; see §5 FD check).
    pub(crate) fn with_metric_fluid_bg(
        mut self,
        bg: BackgroundQuantities,
        cs2b: f64,
    ) -> Self {
        self.bg = bg;
        self.cs2b = cs2b;
        self.use_metric_fluid_blocks = true;
        self
    }

    /// Extract RhsInputs for forwarding to `pstf_free_streaming_rhs`.
    pub(crate) fn rhs_inputs(&self) -> RhsInputs {
        RhsInputs {
            k: self.k,
            tau: self.tau,
            metric_monopole_source: self.metric_monopole_source,
        }
    }

    /// Extract CollisionInputs for forwarding to `pstf_thomson_collision`.
    pub(crate) fn collision_inputs(&self) -> CollisionInputs {
        CollisionInputs {
            kappa_dot: self.kappa_dot,
            r_b: self.r_b,
            use_pol_feedback: self.use_pol_feedback,
            frame: self.frame,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §2.  Sparse Jacobian (triplet list)
// ═══════════════════════════════════════════════════════════════════════

/// Sparse Jacobian as (row, col, value) triplets.
#[derive(Clone, Debug)]
pub(crate) struct SparseJacobian {
    pub(crate) entries: Vec<(usize, usize, f64)>,
    pub(crate) n: usize,
}

impl SparseJacobian {
    fn push(&mut self, row: usize, col: usize, val: f64) {
        self.entries.push((row, col, val));
    }

    /// Count of non-zero entries stored.
    pub(crate) fn nnz(&self) -> usize {
        self.entries.len()
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §3.  Main analytical Jacobian
// ═══════════════════════════════════════════════════════════════════════

/// Compute the analytical sparse Jacobian of (free-streaming + Thomson
/// collision) RHS.
///
/// Since the RHS is linear, `state` is not actually consulted in this
/// implementation.  The argument is retained for interface consistency
/// with future nonlinear extensions.
pub(crate) fn pstf_analytical_jacobian(
    _state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
) -> SparseJacobian {
    let mut jac = SparseJacobian {
        entries: Vec::with_capacity(200),
        n: layout.n_state,
    };

    let k = inputs.k;
    let tau = inputs.tau;
    let kd = inputs.kappa_dot.abs();
    let inv_rb = if kd == 0.0 { 0.0 } else { 1.0 / inputs.r_b.max(1e-10) };

    // ──── Photon intensity free-streaming block ────────────────────
    free_streaming_block(&mut jac, layout.ell_max_gamma,
        |ell| layout.i_photon_i_m0(ell), k, tau);

    // ──── Neutrino free-streaming block (identical structure) ──────
    free_streaming_block(&mut jac, layout.ell_max_nu,
        |ell| layout.i_neutrino_m0(ell), k, tau);

    // ──── Photon collision contributions ───────────────────────────
    if kd > 0.0 {
        let idx_vb = layout.inner.baryon_start + 2;

        // ℓ = 1: drag  C[Θ_1] = −κ̇·(Θ_1 − v_b/3)
        //   ∂/∂Θ_1 = −κ̇,  ∂/∂v_b = +κ̇/3
        let row_theta1 = layout.i_photon_i_m0(1);
        jac.push(row_theta1, row_theta1, -kd);
        jac.push(row_theta1, idx_vb, kd / 3.0);

        // Baryon drag reaction: dv_b/dη |_drag = (κ̇/r_b)·(3·Θ_1 − v_b)
        //   ∂/∂Θ_1 = +3κ̇/r_b,  ∂/∂v_b = −κ̇/r_b
        jac.push(idx_vb, row_theta1, 3.0 * kd * inv_rb);
        jac.push(idx_vb, idx_vb, -kd * inv_rb);

        // ℓ = 2: either pure damping or pol feedback
        if layout.ell_max_gamma >= 2 {
            let row_theta2 = layout.i_photon_i_m0(2);
            if inputs.use_pol_feedback && layout.has_pol() {
                // C[Θ_2] = −(9/10)κ̇·Θ_2 + (3/20)κ̇·E_2
                jac.push(row_theta2, row_theta2, -0.9 * kd);
                let col_e2 = layout.i_photon_e_m0(2);
                jac.push(row_theta2, col_e2, 3.0 * kd / 20.0);
            } else {
                // Pure damping: C[Θ_2] = −κ̇·Θ_2
                jac.push(row_theta2, row_theta2, -kd);
            }
        }

        // ℓ ≥ 3: pure diagonal damping
        for ell in 3..=layout.ell_max_gamma {
            let row = layout.i_photon_i_m0(ell);
            jac.push(row, row, -kd);
        }
    }

    // ──── PR-024c-PERF: metric + fluid + monopole-source blocks ────
    if inputs.use_metric_fluid_blocks {
        metric_fluid_block(&mut jac, inputs, layout);
    }

    jac
}

/// PR-024c-PERF: metric + fluid Jacobian block.
///
/// Writes analytical partial derivatives for the PR-023a metric sector,
/// PR-023b fluid sector, and the metric-monopole-source feedback into
/// photon/ν ℓ=0 (added to entries already created by free-streaming).
///
/// ## Derivation
///
/// With background densities ρ_γ, ρ_ν, ρ_b, conformal Hubble ℋ, and
/// baryon sound-speed² c_s²_b, the helper quantities are
///   dgq  = (16/3)(ρ_γ Θ₁ + ρ_ν N₁) + ρ_b v_b
///   dgs  = 4(ρ_γ Θ₂ + ρ_ν N₂)
///   hdot = 2·k·σ − 3·dgq/k
///
/// and the derivatives are (written as ∂(rhs)/∂(var)):
///
/// **Metric block** (PR-023a `pstf_metric_rhs`):
///   ∂(etakdot)/∂Θ₁ = (8/3)ρ_γ
///   ∂(etakdot)/∂N₁ = (8/3)ρ_ν
///   ∂(etakdot)/∂v_b = ρ_b / 2
///   ∂(sigmadot)/∂σ     = −2·ℋ
///   ∂(sigmadot)/∂Θ₂    = −4·ρ_γ / k
///   ∂(sigmadot)/∂N₂    = −4·ρ_ν / k
///   ∂(sigmadot)/∂etak  = 1
///
/// **Fluid block** (PR-023b `pstf_fluid_rhs`, Thomson drag in free+collision block):
///   ∂(clxcdot)/∂σ     = −k                ( from −hdot/2 = −kσ + 3·dgq/(2k) )
///   ∂(clxcdot)/∂Θ₁    =  8·ρ_γ/k
///   ∂(clxcdot)/∂N₁    =  8·ρ_ν/k
///   ∂(clxcdot)/∂v_b   =  3·ρ_b/(2k)
///   ∂(clxbdot)/∂σ     = −k
///   ∂(clxbdot)/∂Θ₁    =  8·ρ_γ/k
///   ∂(clxbdot)/∂N₁    =  8·ρ_ν/k
///   ∂(clxbdot)/∂v_b   =  3·ρ_b/(2k) − k   ( includes −k·v_b continuity term )
///   ∂(vbdot)/∂v_b     = −ℋ                ( non-drag fluid part only )
///   ∂(vbdot)/∂clxb    =  c_s²_b · k
///
/// **Metric monopole source** (−hdot/6 fed into photon/ν ℓ=0):
///   ∂(Θ₀_dot)/∂σ   += −k/3
///   ∂(Θ₀_dot)/∂Θ₁  +=  (8/3)ρ_γ/k
///   ∂(Θ₀_dot)/∂N₁  +=  (8/3)ρ_ν/k
///   ∂(Θ₀_dot)/∂v_b +=  ρ_b/(2k)
///   (identical pattern for N₀_dot)
///
/// All 25 entries are state-independent linear constants of the background.
/// Triplet list allows duplicate (row, col) keys; the dense aggregator
/// sums them via `out[i*n+j] += v`.
fn metric_fluid_block(
    jac: &mut SparseJacobian,
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
) {
    let k = inputs.k;
    let rg = inputs.bg.grho_gamma;
    let rn = inputs.bg.grho_nu;
    let rb = inputs.bg.grho_b;
    let h_conf = inputs.bg.h_conformal;
    let cs2b = inputs.cs2b;

    // Cache indices
    let i_etak  = layout.i_metric_etak();
    let i_sigma = layout.i_metric_sigma();
    let i_delta_c = layout.i_cdm_delta();
    let i_delta_b = layout.i_baryon_delta();
    let i_v_b   = layout.i_baryon_v_m0();
    let i_theta1 = layout.i_photon_i_m0(1);
    let i_theta0 = layout.i_photon_i_m0(0);
    let i_nu1    = layout.i_neutrino_m0(1);
    let i_nu0    = layout.i_neutrino_m0(0);

    // ──── Metric sector ────────────────────────────────────────────
    // etakdot = dgq/2
    jac.push(i_etak, i_theta1, (8.0 / 3.0) * rg);
    jac.push(i_etak, i_nu1,    (8.0 / 3.0) * rn);
    jac.push(i_etak, i_v_b,    0.5 * rb);

    // sigmadot = −2ℋσ − dgs/k + etak
    jac.push(i_sigma, i_sigma, -2.0 * h_conf);
    if layout.ell_max_gamma >= 2 {
        let i_theta2 = layout.i_photon_i_m0(2);
        jac.push(i_sigma, i_theta2, -4.0 * rg / k);
    }
    if layout.ell_max_nu >= 2 {
        let i_nu2 = layout.i_neutrino_m0(2);
        jac.push(i_sigma, i_nu2, -4.0 * rn / k);
    }
    jac.push(i_sigma, i_etak, 1.0);

    // ──── Fluid sector ─────────────────────────────────────────────
    // Shared hdot derivatives (reusable): ∂hdot/∂(var)/(-2) pattern
    let d_by_sig = -k;                // = -hdot/2 contribution from ∂σ: -(2k)/2
    let d_by_t1  = 8.0 * rg / k;      // = -hdot/2 ∂Θ₁: -(-16ρ_γ/k)/2
    let d_by_n1  = 8.0 * rn / k;
    let d_by_vb_from_hdot = 3.0 * rb / (2.0 * k);  // = -hdot/2 ∂v_b

    // clxcdot = -hdot/2
    jac.push(i_delta_c, i_sigma,  d_by_sig);
    jac.push(i_delta_c, i_theta1, d_by_t1);
    jac.push(i_delta_c, i_nu1,    d_by_n1);
    jac.push(i_delta_c, i_v_b,    d_by_vb_from_hdot);

    // clxbdot = -k·v_b - hdot/2
    jac.push(i_delta_b, i_sigma,  d_by_sig);
    jac.push(i_delta_b, i_theta1, d_by_t1);
    jac.push(i_delta_b, i_nu1,    d_by_n1);
    jac.push(i_delta_b, i_v_b,    d_by_vb_from_hdot - k);

    // vbdot (non-drag part): -ℋ·v_b + c_s²_b·k·clxb
    // Drag part (∂Θ₁ and ∂v_b from +κ̇/r_b) already in collision block.
    jac.push(i_v_b, i_v_b,     -h_conf);
    jac.push(i_v_b, i_delta_b, cs2b * k);

    // ──── Metric monopole source into photon/ν ℓ=0 ─────────────────
    // dy[Θ₀] += -hdot/6; half the magnitudes of the clxc/clxb block
    // (factor 1/3 instead of 1/2 · 2 from the -hdot/6 vs -hdot/2 ratio).
    let m_sig = -k / 3.0;                  // = -(2k)/6
    let m_t1  = (8.0 / 3.0) * rg / k;      // = -(-16ρ_γ/k)/6
    let m_n1  = (8.0 / 3.0) * rn / k;
    let m_vb  = rb / (2.0 * k);            // = -(-3ρ_b/k)/6

    // Photon monopole
    jac.push(i_theta0, i_sigma,  m_sig);
    jac.push(i_theta0, i_theta1, m_t1);
    jac.push(i_theta0, i_nu1,    m_n1);
    jac.push(i_theta0, i_v_b,    m_vb);

    // Neutrino monopole (identical source coupling)
    jac.push(i_nu0, i_sigma,  m_sig);
    jac.push(i_nu0, i_theta1, m_t1);
    jac.push(i_nu0, i_nu1,    m_n1);
    jac.push(i_nu0, i_v_b,    m_vb);
}

/// Helper: fill the free-streaming tridiagonal + truncation rows.
fn free_streaming_block(
    jac: &mut SparseJacobian,
    ell_max: usize,
    idx: impl Fn(usize) -> usize,
    k: f64,
    tau: f64,
) {
    // ℓ = 0: ∂(dy[0])/∂y[1] = −k   (monopole depends only on dipole)
    if ell_max >= 1 {
        jac.push(idx(0), idx(1), -k);
    }

    // ℓ = 1: ∂(dy[1])/∂y[0] = k/3, ∂(dy[1])/∂y[2] = −2k/3
    if ell_max >= 1 {
        jac.push(idx(1), idx(0), k / 3.0);
        if ell_max >= 2 {
            jac.push(idx(1), idx(2), -2.0 * k / 3.0);
        }
    }

    // ℓ ∈ [2, ell_max − 1]
    for ell in 2..ell_max {
        let row = idx(ell);
        let two_ell_plus_one = (2 * ell + 1) as f64;
        let coeff = k / two_ell_plus_one;
        jac.push(row, idx(ell - 1), coeff * (ell as f64));
        jac.push(row, idx(ell + 1), -coeff * ((ell + 1) as f64));
    }

    // ℓ = ell_max: truncation dΘ_lmax/dη = k·Θ_{lmax−1} − (lmax+1)/τ·Θ_lmax
    if ell_max >= 2 {
        let row = idx(ell_max);
        jac.push(row, idx(ell_max - 1), k);
        jac.push(row, idx(ell_max), -((ell_max + 1) as f64) / tau);
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §4.  Dense output (Rodas5P row-major)
// ═══════════════════════════════════════════════════════════════════════

/// Compute dense Jacobian in row-major layout: `out[i*n + j] = J[i,j]`.
/// Zeroes the output buffer first.
pub(crate) fn pstf_jacobian_dense(
    state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
    out: &mut [f64],
) {
    let n = layout.n_state;
    assert_eq!(out.len(), n * n,
        "dense Jacobian output buffer size {} != n² = {}", out.len(), n * n);

    out.fill(0.0);
    let sparse = pstf_analytical_jacobian(state, inputs, layout);
    for &(i, j, v) in &sparse.entries {
        out[i * n + j] += v;   // += handles any duplicate triplets
    }
}

// ═══════════════════════════════════════════════════════════════════════
//   §5.  Finite-difference check
// ═══════════════════════════════════════════════════════════════════════

/// Compute numerical Jacobian column `j` via 5-point stencil.
/// Returns `J_num[i, j]` for all i in a vector of length n_state.
fn fd_column_5pt(
    state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
    j: usize,
    h: f64,
) -> Vec<f64> {
    let n = layout.n_state;
    let mut f_p1 = vec![0.0_f64; n];
    let mut f_p2 = vec![0.0_f64; n];
    let mut f_m1 = vec![0.0_f64; n];
    let mut f_m2 = vec![0.0_f64; n];

    let mut perturbed = state.to_vec();
    let x0 = state[j];

    // Helper: compute combined RHS = free_streaming + collision
    let rhs_at = |st: &[f64], out: &mut [f64]| {
        out.fill(0.0);
        pstf_free_streaming_rhs(st, out, &inputs.rhs_inputs(), layout);
        pstf_thomson_collision(st, out, &inputs.collision_inputs(), layout);
    };

    perturbed[j] = x0 + 2.0 * h;
    rhs_at(&perturbed, &mut f_p2);
    perturbed[j] = x0 + h;
    rhs_at(&perturbed, &mut f_p1);
    perturbed[j] = x0 - h;
    rhs_at(&perturbed, &mut f_m1);
    perturbed[j] = x0 - 2.0 * h;
    rhs_at(&perturbed, &mut f_m2);
    perturbed[j] = x0;  // restore

    // 5-point: f'(x) ≈ [−f(x+2h) + 8f(x+h) − 8f(x−h) + f(x−2h)] / (12h)
    let mut col = vec![0.0_f64; n];
    for i in 0..n {
        col[i] = (-f_p2[i] + 8.0 * f_p1[i] - 8.0 * f_m1[i] + f_m2[i])
               / (12.0 * h);
    }
    col
}

/// PR-024c-PERF: FD column for the FULL RHS (free + collision + metric
/// + fluid + monopole source), using `pstf_full_rhs`.
///
/// Use this for checking the extended analytical Jacobian.
fn fd_column_5pt_full(
    state: &[f64],
    full_inputs: &super::full_rhs::FullRhsInputs,
    layout: &PstfFlrwLayout,
    j: usize,
    h: f64,
) -> Vec<f64> {
    use super::full_rhs::pstf_full_rhs;
    let n = layout.n_state;
    let mut f_p1 = vec![0.0_f64; n];
    let mut f_p2 = vec![0.0_f64; n];
    let mut f_m1 = vec![0.0_f64; n];
    let mut f_m2 = vec![0.0_f64; n];

    let mut perturbed = state.to_vec();
    let x0 = state[j];

    perturbed[j] = x0 + 2.0 * h;
    pstf_full_rhs(&perturbed, &mut f_p2, full_inputs, layout);
    perturbed[j] = x0 + h;
    pstf_full_rhs(&perturbed, &mut f_p1, full_inputs, layout);
    perturbed[j] = x0 - h;
    pstf_full_rhs(&perturbed, &mut f_m1, full_inputs, layout);
    perturbed[j] = x0 - 2.0 * h;
    pstf_full_rhs(&perturbed, &mut f_m2, full_inputs, layout);
    perturbed[j] = x0;

    let mut col = vec![0.0_f64; n];
    for i in 0..n {
        col[i] = (-f_p2[i] + 8.0 * f_p1[i] - 8.0 * f_m1[i] + f_m2[i])
               / (12.0 * h);
    }
    col
}

/// PR-024c-PERF: FD check against `pstf_full_rhs`.
///
/// This is the extended analogue of `jacobian_fd_check`: uses the full
/// dispatcher as the reference RHS, and is appropriate when
/// `inputs.use_metric_fluid_blocks == true`.
///
/// Returns `(max_rel_err, i_max, j_max)` over stored triplets.
pub(crate) fn jacobian_fd_check_full(
    state: &[f64],
    inputs: &JacobianInputs,
    full_inputs: &super::full_rhs::FullRhsInputs,
    layout: &PstfFlrwLayout,
    h: f64,
) -> (f64, usize, usize) {
    let sparse = pstf_analytical_jacobian(state, inputs, layout);
    let _n = layout.n_state;

    let used_cols: std::collections::BTreeSet<usize> =
        sparse.entries.iter().map(|&(_, j, _)| j).collect();

    let mut fd_cols: std::collections::BTreeMap<usize, Vec<f64>> =
        std::collections::BTreeMap::new();
    for &j in &used_cols {
        fd_cols.insert(j, fd_column_5pt_full(state, full_inputs, layout, j, h));
    }

    let mut analytical: std::collections::BTreeMap<(usize, usize), f64> =
        std::collections::BTreeMap::new();
    for &(i, j, v) in &sparse.entries {
        *analytical.entry((i, j)).or_insert(0.0) += v;
    }

    let mut max_rel_err = 0.0_f64;
    let mut i_max = 0;
    let mut j_max = 0;
    for ((i, j), &j_ana) in &analytical {
        let j_num = fd_cols.get(j).unwrap()[*i];
        let abs_err = (j_ana - j_num).abs();
        let scale = j_ana.abs().max(1e-10);
        let rel_err = if j_ana.abs() > 1e-10 {
            abs_err / scale
        } else {
            abs_err
        };
        if rel_err > max_rel_err {
            max_rel_err = rel_err;
            i_max = *i;
            j_max = *j;
        }
    }
    (max_rel_err, i_max, j_max)
}

/// Check analytical Jacobian against 5-point finite-difference.
///
/// Returns `(max_rel_err, i_max, j_max)`:
///   - `max_rel_err`: maximum relative error over all stored triplets
///     (with absolute threshold for near-zero analytical values)
///   - `(i_max, j_max)`: entry where the maximum occurs
///
/// `h` should be approximately `1e-6 · ||state||_∞`.  Typical range
/// that balances truncation error (~h⁴ for 5-point) vs roundoff.
pub(crate) fn jacobian_fd_check(
    state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
    h: f64,
) -> (f64, usize, usize) {
    let sparse = pstf_analytical_jacobian(state, inputs, layout);
    let n = layout.n_state;

    // For efficiency: only evaluate FD columns that actually appear in
    // the analytical pattern.
    let used_cols: std::collections::BTreeSet<usize> =
        sparse.entries.iter().map(|&(_, j, _)| j).collect();

    let mut max_rel_err = 0.0_f64;
    let mut i_max = 0;
    let mut j_max = 0;

    // Precompute FD columns for all used j
    let mut fd_cols: std::collections::BTreeMap<usize, Vec<f64>> =
        std::collections::BTreeMap::new();
    for &j in &used_cols {
        fd_cols.insert(j, fd_column_5pt(state, inputs, layout, j, h));
    }

    // Aggregate analytical by (i, j) in case of duplicate triplets
    let mut analytical: std::collections::BTreeMap<(usize, usize), f64> =
        std::collections::BTreeMap::new();
    for &(i, j, v) in &sparse.entries {
        *analytical.entry((i, j)).or_insert(0.0) += v;
    }

    for ((i, j), &j_ana) in &analytical {
        let j_num = fd_cols.get(j).unwrap()[*i];
        let abs_err = (j_ana - j_num).abs();
        let scale = j_ana.abs().max(1e-10);
        let rel_err = if j_ana.abs() > 1e-10 {
            abs_err / scale
        } else {
            abs_err  // absolute error for zero/near-zero entries
        };
        if rel_err > max_rel_err {
            max_rel_err = rel_err;
            i_max = *i;
            j_max = *j;
        }
        let _ = n;  // silence unused
    }

    (max_rel_err, i_max, j_max)
}

// ═══════════════════════════════════════════════════════════════════════
//   §6.  Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};
    use super::super::collision::CollisionInputs;

    fn test_fixture() -> (PstfFlrwLayout, Vec<f64>, JacobianInputs) {
        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();
        let ic = PstfIcInputs::default_adiabatic(0.01, 500.0);
        let mut state = pstf_adiabatic_ic(&ic, &layout);
        state[layout.inner.baryon_start + 2] = 0.001;
        let rhs_in = RhsInputs::free_streaming(0.01, 100.0);
        let coll_in = CollisionInputs::pol_off(0.5, 0.6);
        let jac_in = JacobianInputs::from_rhs_and_collision(&rhs_in, &coll_in);
        (layout, state, jac_in)
    }

    // ─── PR-024c-PERF Step 1: extended inputs API ───────────────────

    /// `from_rhs_and_collision` produces legacy (no-extension) config.
    #[test]
    fn perf_step1_legacy_inputs_have_extension_off() {
        let (_, _, inputs) = test_fixture();
        assert!(!inputs.use_metric_fluid_blocks,
            "legacy constructor must not enable metric/fluid extension");
        assert_eq!(inputs.cs2b, 0.0);
        assert_eq!(inputs.bg.h_conformal, 0.0);
        assert_eq!(inputs.bg.grho_gamma, 0.0);
        assert_eq!(inputs.bg.grho_nu, 0.0);
        assert_eq!(inputs.bg.grho_b, 0.0);
    }

    /// `with_metric_fluid_bg` builder turns on extension + sets bg/cs2b.
    #[test]
    fn perf_step1_with_metric_fluid_bg_populates_fields() {
        use super::super::metric::BackgroundQuantities;
        let (_, _, inputs) = test_fixture();
        let bg = BackgroundQuantities::representative();
        let cs2b = 3.3e-10;
        let ext = inputs.with_metric_fluid_bg(bg, cs2b);
        assert!(ext.use_metric_fluid_blocks);
        assert_eq!(ext.bg.h_conformal, bg.h_conformal);
        assert_eq!(ext.bg.grho_gamma, bg.grho_gamma);
        assert_eq!(ext.bg.grho_nu, bg.grho_nu);
        assert_eq!(ext.bg.grho_b, bg.grho_b);
        assert_eq!(ext.cs2b, cs2b);
        // Legacy fields preserved
        assert_eq!(ext.k, inputs.k);
        assert_eq!(ext.tau, inputs.tau);
        assert_eq!(ext.kappa_dot, inputs.kappa_dot);
    }

    // ─── PR-024c-PERF Step 2: metric_fluid_block internal checks ────

    /// Direct call to `metric_fluid_block`: verify the 25 triplets match
    /// hand-derived formulas for a non-trivial configuration.
    ///
    /// This tests the function in isolation — `pstf_analytical_jacobian`
    /// wiring is Step 3.
    #[test]
    fn perf_step2_metric_fluid_triplets_hand_derived() {
        use super::super::metric::BackgroundQuantities;
        let (layout, _state, legacy_inputs) = test_fixture();
        let bg = BackgroundQuantities::representative();
        let cs2b = 3.3e-10_f64;
        let inputs = legacy_inputs.with_metric_fluid_bg(bg, cs2b);

        // Call metric_fluid_block directly into a fresh sparse container
        let mut jac = SparseJacobian { entries: Vec::new(), n: layout.n_state };
        super::metric_fluid_block(&mut jac, &inputs, &layout);

        // Aggregate by (row, col)
        use std::collections::BTreeMap;
        let mut agg: BTreeMap<(usize, usize), f64> = BTreeMap::new();
        for &(i, j, v) in &jac.entries {
            *agg.entry((i, j)).or_insert(0.0) += v;
        }

        let k = inputs.k;
        let rg = bg.grho_gamma;
        let rn = bg.grho_nu;
        let rb = bg.grho_b;
        let h_conf = bg.h_conformal;
        let eps = 1e-18_f64;

        // Expected set of (row, col, value) tuples
        let i_etak = layout.i_metric_etak();
        let i_sigma = layout.i_metric_sigma();
        let i_deltac = layout.i_cdm_delta();
        let i_deltab = layout.i_baryon_delta();
        let i_vb = layout.i_baryon_v_m0();
        let i_t0 = layout.i_photon_i_m0(0);
        let i_t1 = layout.i_photon_i_m0(1);
        let i_t2 = layout.i_photon_i_m0(2);
        let i_n0 = layout.i_neutrino_m0(0);
        let i_n1 = layout.i_neutrino_m0(1);
        let i_n2 = layout.i_neutrino_m0(2);

        let expected: Vec<((usize, usize), f64)> = vec![
            // etakdot
            ((i_etak, i_t1), (8.0/3.0)*rg),
            ((i_etak, i_n1), (8.0/3.0)*rn),
            ((i_etak, i_vb), 0.5*rb),
            // sigmadot
            ((i_sigma, i_sigma), -2.0*h_conf),
            ((i_sigma, i_t2), -4.0*rg/k),
            ((i_sigma, i_n2), -4.0*rn/k),
            ((i_sigma, i_etak), 1.0),
            // clxcdot = -hdot/2
            ((i_deltac, i_sigma), -k),
            ((i_deltac, i_t1), 8.0*rg/k),
            ((i_deltac, i_n1), 8.0*rn/k),
            ((i_deltac, i_vb), 3.0*rb/(2.0*k)),
            // clxbdot = -k·v_b - hdot/2
            ((i_deltab, i_sigma), -k),
            ((i_deltab, i_t1), 8.0*rg/k),
            ((i_deltab, i_n1), 8.0*rn/k),
            ((i_deltab, i_vb), 3.0*rb/(2.0*k) - k),
            // vbdot non-drag
            ((i_vb, i_vb), -h_conf),
            ((i_vb, i_deltab), cs2b*k),
            // Θ₀ monopole source
            ((i_t0, i_sigma), -k/3.0),
            ((i_t0, i_t1), (8.0/3.0)*rg/k),
            ((i_t0, i_n1), (8.0/3.0)*rn/k),
            ((i_t0, i_vb), rb/(2.0*k)),
            // N₀ monopole source
            ((i_n0, i_sigma), -k/3.0),
            ((i_n0, i_t1), (8.0/3.0)*rg/k),
            ((i_n0, i_n1), (8.0/3.0)*rn/k),
            ((i_n0, i_vb), rb/(2.0*k)),
        ];

        assert_eq!(expected.len(), 25, "expected 25 metric-fluid entries");

        for ((i, j), v_exp) in &expected {
            let v_got = *agg.get(&(*i, *j))
                .unwrap_or_else(|| panic!("missing entry ({},{})", i, j));
            assert!((v_got - v_exp).abs() < eps,
                "({},{}): got {:.6e}, expected {:.6e}", i, j, v_got, v_exp);
        }

        // Nothing else should be written
        assert_eq!(agg.len(), 25,
            "metric_fluid_block wrote {} distinct entries, expected 25", agg.len());
    }

    /// With extension OFF, analytical Jacobian nnz unchanged (regression
    /// guard on PR-022c behaviour).
    #[test]
    fn perf_step1_extension_off_preserves_nnz() {
        let (layout, state, inputs) = test_fixture();
        assert!(!inputs.use_metric_fluid_blocks);
        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);
        // Matches caveat_sparsity_count expectation
        let lg = layout.ell_max_gamma;
        let ln = layout.ell_max_nu;
        let fs_photon = 1 + 2 + 2 * (lg - 2) + 2;
        let fs_neutrino = 1 + 2 + 2 * (ln - 2) + 2;
        let coll_photon = 2 + 1 + (lg - 2);
        let baryon = 2;
        assert_eq!(sparse.nnz(), fs_photon + fs_neutrino + coll_photon + baryon);
    }

    // ─── PR-024c-PERF Step 3: extended Jacobian FD regression ──────

    fn full_inputs_fixture(inputs: &JacobianInputs) -> super::super::full_rhs::FullRhsInputs {
        use super::super::collision::FrameConvention;
        super::super::full_rhs::FullRhsInputs {
            k: inputs.k,
            tau: inputs.tau,
            bg: inputs.bg,
            kappa_dot: inputs.kappa_dot,
            r_b: inputs.r_b,
            use_pol_feedback: inputs.use_pol_feedback,
            frame: FrameConvention::ElectronRestFrame,
            cs2b: inputs.cs2b,
        }
    }

    /// Extended sparsity: 25 metric+fluid entries added on top of PR-022c.
    #[test]
    fn perf_step3_extended_sparsity_count() {
        use super::super::metric::BackgroundQuantities;
        let (layout, state, legacy) = test_fixture();
        let ext = legacy.with_metric_fluid_bg(BackgroundQuantities::representative(), 3.3e-10);
        let sparse = pstf_analytical_jacobian(&state, &ext, &layout);

        let lg = layout.ell_max_gamma;
        let ln = layout.ell_max_nu;
        let legacy_nnz = (1 + 2 + 2*(lg-2) + 2) + (1 + 2 + 2*(ln-2) + 2)
                       + (2 + 1 + (lg-2)) + 2;
        let expected = legacy_nnz + 25;
        assert_eq!(sparse.nnz(), expected,
            "extended nnz: expected {}, got {}", expected, sparse.nnz());
    }

    /// FD regression: extended analytical Jacobian matches
    /// `pstf_full_rhs` finite-difference to < 1e-6.
    #[test]
    fn perf_step3_fd_regression_full_rhs() {
        use super::super::metric::BackgroundQuantities;
        let (layout, state, legacy) = test_fixture();
        let ext = legacy.with_metric_fluid_bg(BackgroundQuantities::representative(), 3.3e-10);
        let full_in = full_inputs_fixture(&ext);

        let norm = state.iter().fold(0.0_f64, |a, &b| a.max(b.abs())).max(1.0);
        let h = 1e-6 * norm;
        let (max_err, i, j) = jacobian_fd_check_full(&state, &ext, &full_in, &layout, h);
        assert!(max_err < 1e-6,
            "extended FD regression max rel err {} at ({},{})", max_err, i, j);
    }

    /// FD regression at multiple k values — ensures no k-dependent bug.
    #[test]
    fn perf_step3_fd_regression_multiple_k() {
        use super::super::metric::BackgroundQuantities;
        use super::super::ic::{PstfIcInputs, pstf_adiabatic_ic};
        use super::super::collision::CollisionInputs;
        use super::super::rhs_free::RhsInputs;

        let layout = PstfFlrwLayout::new(16, 16, 16);
        layout.validate();

        for &k in &[1e-3_f64, 1e-2, 5e-2, 1e-1] {
            let ic = PstfIcInputs::default_adiabatic(k, 500.0);
            let mut state = pstf_adiabatic_ic(&ic, &layout);
            state[layout.inner.baryon_start + 2] = 0.001;
            state[layout.i_metric_etak()] = -k * 1e-3;
            state[layout.i_metric_sigma()] = 1e-5;

            let rhs_in = RhsInputs::free_streaming(k, 100.0);
            let coll_in = CollisionInputs::pol_off(0.5, 0.6);
            let legacy = JacobianInputs::from_rhs_and_collision(&rhs_in, &coll_in);
            let ext = legacy.with_metric_fluid_bg(BackgroundQuantities::representative(), 3.3e-10);
            let full_in = full_inputs_fixture(&ext);

            let norm = state.iter().fold(0.0_f64, |a, &b| a.max(b.abs())).max(1.0);
            let h = 1e-6 * norm;
            let (max_err, i, j) = jacobian_fd_check_full(&state, &ext, &full_in, &layout, h);
            assert!(max_err < 1e-6,
                "k={}: extended FD max rel err {} at ({},{})", k, max_err, i, j);
        }
    }

    // ─── Identity tests (3) ─────────────────────────────────────────

    /// Photon free-streaming rows have non-zero cols exactly at {ℓ−1, ℓ+1}
    /// (plus ℓ_max truncation row with {ℓ_max−1, ℓ_max}).  For collision=0
    /// the pattern is strictly tridiagonal.
    #[test]
    fn identity_free_streaming_tridiagonal_pattern() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.kappa_dot = 0.0;  // no collision
        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);

        // Collect photon intensity non-zero column sets
        use std::collections::BTreeMap;
        let mut cols_by_row: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
        for &(i, j, _) in &sparse.entries {
            cols_by_row.entry(i).or_default().push(j);
        }

        // Check ℓ = 5 row (middle): cols should be {idx(4), idx(6)}
        let row_5 = layout.i_photon_i_m0(5);
        let expected_5 = vec![layout.i_photon_i_m0(4), layout.i_photon_i_m0(6)];
        let got_5 = cols_by_row.get(&row_5).unwrap().clone();
        let mut got_sorted = got_5.clone();
        got_sorted.sort();
        let mut exp_sorted = expected_5.clone();
        exp_sorted.sort();
        assert_eq!(got_sorted, exp_sorted,
            "ℓ=5 row cols: expected {:?}, got {:?}", exp_sorted, got_sorted);

        // Check ℓ = ℓ_max row: cols should be {idx(ℓ_max−1), idx(ℓ_max)}
        let lg = layout.ell_max_gamma;
        let row_max = layout.i_photon_i_m0(lg);
        let expected_max = vec![layout.i_photon_i_m0(lg - 1), layout.i_photon_i_m0(lg)];
        let got_max = cols_by_row.get(&row_max).unwrap().clone();
        let mut got_m_sorted = got_max.clone();
        got_m_sorted.sort();
        let mut exp_m_sorted = expected_max.clone();
        exp_m_sorted.sort();
        assert_eq!(got_m_sorted, exp_m_sorted,
            "ℓ=ℓ_max row cols: expected {:?}, got {:?}", exp_m_sorted, got_m_sorted);
    }

    /// Collision-only (k=0): ℓ=1 has cross with v_b, ℓ≥2 is diagonal
    /// (pol off default).
    #[test]
    fn identity_collision_diagonal_pattern() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.k = 0.0;  // no free-streaming
        inputs.tau = 1.0;  // avoid div-zero in truncation
        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);

        // Collect all entries keyed by row
        use std::collections::BTreeMap;
        let mut cols_by_row: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
        for &(i, j, _) in &sparse.entries {
            cols_by_row.entry(i).or_default().push(j);
        }

        // Free-streaming tridiagonal at k=0: coefficient is 0 but entry may
        // be present with value 0 (harmless, does not affect numerics).
        // However, truncation row still has −(ℓ_max+1)/τ entry at ℓ_max.
        // Focus on collision: ℓ=5 photon (ℓ≥3) should have
        // diagonal self-entry −κ̇ from collision.
        let row_5 = layout.i_photon_i_m0(5);
        let entries_5 = cols_by_row.get(&row_5).unwrap();
        assert!(entries_5.contains(&row_5),
            "ℓ=5 must have diagonal damping entry");

        // ℓ=1 must have cross-coupling to v_b
        let row_1 = layout.i_photon_i_m0(1);
        let idx_vb = layout.inner.baryon_start + 2;
        let entries_1 = cols_by_row.get(&row_1).unwrap();
        assert!(entries_1.contains(&idx_vb),
            "ℓ=1 row must have v_b cross-coupling entry at idx {}", idx_vb);

        // Baryon row must have cross-coupling to Θ_1
        let entries_vb = cols_by_row.get(&idx_vb).unwrap();
        assert!(entries_vb.contains(&row_1),
            "v_b row must have Θ_1 cross-coupling entry");
    }

    /// Specific coefficient values for ℓ=3 and ℓ=5.
    ///   ℓ=3: J[Θ_3, Θ_2] = 3k/7,  J[Θ_3, Θ_4] = −4k/7
    ///   ℓ=5: J[Θ_5, Θ_4] = 5k/11, J[Θ_5, Θ_6] = −6k/11
    #[test]
    fn identity_coefficient_values_match_formula() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.kappa_dot = 0.0;  // isolate free-streaming
        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);

        // Aggregate by (row, col)
        use std::collections::BTreeMap;
        let mut agg: BTreeMap<(usize, usize), f64> = BTreeMap::new();
        for &(i, j, v) in &sparse.entries {
            *agg.entry((i, j)).or_insert(0.0) += v;
        }

        let k = inputs.k;
        let eps = 1e-15;

        // ℓ=3 row
        let r3 = layout.i_photon_i_m0(3);
        let c2 = layout.i_photon_i_m0(2);
        let c4 = layout.i_photon_i_m0(4);
        let j_32 = *agg.get(&(r3, c2)).unwrap();
        let j_34 = *agg.get(&(r3, c4)).unwrap();
        assert!((j_32 - 3.0 * k / 7.0).abs() < eps,
            "J[3,2]: expected {}, got {}", 3.0*k/7.0, j_32);
        assert!((j_34 + 4.0 * k / 7.0).abs() < eps,
            "J[3,4]: expected {}, got {}", -4.0*k/7.0, j_34);

        // ℓ=5 row
        let r5 = layout.i_photon_i_m0(5);
        let c4_5 = layout.i_photon_i_m0(4);
        let c6 = layout.i_photon_i_m0(6);
        let j_54 = *agg.get(&(r5, c4_5)).unwrap();
        let j_56 = *agg.get(&(r5, c6)).unwrap();
        assert!((j_54 - 5.0 * k / 11.0).abs() < eps,
            "J[5,4]: expected {}, got {}", 5.0*k/11.0, j_54);
        assert!((j_56 + 6.0 * k / 11.0).abs() < eps,
            "J[5,6]: expected {}, got {}", -6.0*k/11.0, j_56);
    }

    // ─── FD regression tests (3) — G3 evidence ──────────────────────

    /// FD check: free-streaming only (κ̇=0).
    #[test]
    fn fd_regression_free_streaming_only() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.kappa_dot = 0.0;
        let norm = state.iter().fold(0.0_f64, |a, &b| a.max(b.abs())).max(1.0);
        let h = 1e-6 * norm;
        let (max_err, i, j) = jacobian_fd_check(&state, &inputs, &layout, h);
        assert!(max_err < 1e-6,
            "FD free-streaming max rel err {} at ({},{})", max_err, i, j);
    }

    /// FD check: collision only (k=0).
    #[test]
    fn fd_regression_collision_only() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.k = 0.0;
        inputs.tau = 1.0;  // avoid div-zero
        let norm = state.iter().fold(0.0_f64, |a, &b| a.max(b.abs())).max(1.0);
        let h = 1e-6 * norm;
        let (max_err, i, j) = jacobian_fd_check(&state, &inputs, &layout, h);
        assert!(max_err < 1e-6,
            "FD collision max rel err {} at ({},{})", max_err, i, j);
    }

    /// FD check: full combined RHS, representative state.
    #[test]
    fn fd_regression_full_combined() {
        let (layout, state, inputs) = test_fixture();
        let norm = state.iter().fold(0.0_f64, |a, &b| a.max(b.abs())).max(1.0);
        let h = 1e-6 * norm;
        let (max_err, i, j) = jacobian_fd_check(&state, &inputs, &layout, h);
        assert!(max_err < 1e-6,
            "FD full combined max rel err {} at ({},{}) (h={})",
            max_err, i, j, h);
    }

    // ─── Limit / Caveat (2) ────────────────────────────────────────

    /// κ̇=0: no collision entries should appear in the sparse list.
    /// (Implementation choice: we skip them entirely, not emit zeros.)
    #[test]
    fn limit_kappa_dot_zero_no_collision_entries() {
        let (layout, state, mut inputs) = test_fixture();
        inputs.kappa_dot = 0.0;
        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);

        // Check: no entry touches v_b (baryon_start + 2)
        let idx_vb = layout.inner.baryon_start + 2;
        for &(i, j, _v) in &sparse.entries {
            assert!(i != idx_vb && j != idx_vb,
                "κ̇=0 should not produce v_b entry, got ({},{})", i, j);
        }
    }

    /// Sparsity count sanity for ℓ_max=16:
    ///   photon free-streaming tridiagonal: ≈ 3·(ℓ_max+1) − 2 = 49
    ///   neutrino same: 49
    ///   photon collision: ℓ=1 drag (2 Θ-v_b) + ℓ=2 damping (1) + ℓ≥3 (ℓ_max−2)
    ///   baryon drag reaction: 2
    #[test]
    fn caveat_sparsity_count() {
        let (layout, state, inputs) = test_fixture();
        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);

        let lg = layout.ell_max_gamma;
        let ln = layout.ell_max_nu;

        // Free-streaming counts: ℓ=0 (1 entry to ℓ=1) + ℓ=1 (2 entries) +
        // ℓ in [2, lg-1] (2 entries each) + ℓ=lg (2 entries)
        let fs_photon = 1 + 2 + 2 * (lg - 2) + 2;       // = 2·lg + 1
        let fs_neutrino = 1 + 2 + 2 * (ln - 2) + 2;

        // Collision photon: ℓ=1 drag (Θ_1 diag + Θ_1 v_b cross) = 2
        //                   ℓ=2 damping = 1
        //                   ℓ=3..lg diag = lg − 2
        let coll_photon = 2 + 1 + (lg - 2);

        // Baryon: 2 (v_b Θ_1 cross + v_b diag)
        let baryon = 2;

        let expected = fs_photon + fs_neutrino + coll_photon + baryon;
        assert_eq!(sparse.nnz(), expected,
            "sparsity count mismatch: expected {}, got {} (lg={}, ln={})",
            expected, sparse.nnz(), lg, ln);
    }

    // ─── Dense/sparse equivalence (1) ──────────────────────────────

    /// `pstf_jacobian_dense` output matches `pstf_analytical_jacobian`
    /// triplets exactly.
    #[test]
    fn equivalence_dense_vs_sparse() {
        let (layout, state, inputs) = test_fixture();
        let n = layout.n_state;
        let mut dense = vec![0.0_f64; n * n];
        pstf_jacobian_dense(&state, &inputs, &layout, &mut dense);

        let sparse = pstf_analytical_jacobian(&state, &inputs, &layout);

        // Aggregate sparse (handle duplicate triplets with +=)
        use std::collections::BTreeMap;
        let mut agg: BTreeMap<(usize, usize), f64> = BTreeMap::new();
        for &(i, j, v) in &sparse.entries {
            *agg.entry((i, j)).or_insert(0.0) += v;
        }

        // Every sparse entry must equal dense entry
        for ((i, j), &v) in &agg {
            assert!((dense[i * n + j] - v).abs() < 1e-15,
                "dense[{},{}] = {} != sparse {}",
                i, j, dense[i * n + j], v);
        }

        // Every non-listed entry in dense must be 0
        let listed: std::collections::BTreeSet<(usize, usize)> =
            agg.keys().copied().collect();
        for i in 0..n {
            for j in 0..n {
                if !listed.contains(&(i, j)) {
                    assert_eq!(dense[i * n + j], 0.0,
                        "dense[{},{}] = {} but not in sparse",
                        i, j, dense[i * n + j]);
                }
            }
        }
    }
}
