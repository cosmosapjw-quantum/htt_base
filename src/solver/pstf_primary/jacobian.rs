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

// ═══════════════════════════════════════════════════════════════════════
//   §1.  Jacobian inputs
// ═══════════════════════════════════════════════════════════════════════

/// Unified inputs for the Jacobian computation.  Combines PR-022a +
/// PR-022b parameters.
#[derive(Clone, Copy, Debug)]
pub(crate) struct JacobianInputs {
    pub(crate) k: f64,
    pub(crate) tau: f64,
    pub(crate) metric_monopole_source: f64,   // PR-023 placeholder
    pub(crate) kappa_dot: f64,
    pub(crate) r_b: f64,
    pub(crate) use_pol_feedback: bool,
    pub(crate) frame: FrameConvention,
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
        }
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

    jac
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
