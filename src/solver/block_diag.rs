// Block-diagonal LU solver: BlockDecomp, BlockDiagScratch, step.
// BA-03: Extracted from profile.rs (PR-14B).

use crate::core::config::*;
use crate::core::lu::*;
use super::rodas5p::*;

// ── PR-14B: Block-diagonal LU decomposition ──
// The stacked system decouples into:
//   Block A: photon (F) + baryon (v_b) + polarisation (E)
//   Block B: neutrino (N) + CDM (δ_c, v_c)
// eta is solved trivially: k_eta = rhs[d-1] * gamma * h
// Then RHS is corrected for the eta column before block solves.

pub(crate) struct BlockDecomp {
    /// Real indices belonging to Block A (sorted)
    pub(crate) idx_a: Vec<usize>,
    /// Real indices belonging to Block B (sorted)
    pub(crate) idx_b: Vec<usize>,
    pub(crate) d_a: usize,
    pub(crate) d_b: usize,
}

impl BlockDecomp {
    pub(crate) fn from_ell_max(ell_max_gamma: usize, ell_max_nu: usize, ell_max_pol: usize, include_pol: bool) -> Self {
        let n_gamma = ell_max_gamma + 1;
        let n_nu = ell_max_nu + 1;
        let n_e = if include_pol { ell_max_pol + 1 } else { 0 };
        // Complex offsets (same as build_stacked_state_layout)
        let off_f = 0;
        let off_vb = n_gamma;
        let off_n = off_vb + 1;
        let off_dc = off_n + n_nu;
        let off_vc = off_dc + 1;
        let off_e = off_vc + 1;
        let n_total = off_e + n_e;

        // Block A complex indices: photon + v_b + E
        let mut ca: Vec<usize> = (off_f..off_f + n_gamma).collect();
        ca.push(off_vb);
        if n_e > 0 {
            ca.extend(off_e..off_e + n_e);
        }
        // Block B complex indices: neutrino + CDM
        let mut cb: Vec<usize> = (off_n..off_n + n_nu).collect();
        cb.push(off_dc);
        cb.push(off_vc);

        // Real indices: re part + im part (eta excluded)
        let mut idx_a: Vec<usize> = ca.iter().map(|&i| i).collect();
        idx_a.extend(ca.iter().map(|&i| i + n_total));
        idx_a.sort();
        let mut idx_b: Vec<usize> = cb.iter().map(|&i| i).collect();
        idx_b.extend(cb.iter().map(|&i| i + n_total));
        idx_b.sort();

        let d_a = idx_a.len();
        let d_b = idx_b.len();
        BlockDecomp { idx_a, idx_b, d_a, d_b }
    }
}

pub(crate) struct BlockDiagScratch {
    pub(crate) w_a: Vec<f64>,
    pub(crate) w_b: Vec<f64>,
    pub(crate) piv_a: Vec<usize>,
    pub(crate) piv_b: Vec<usize>,
    pub(crate) rhs_a: Vec<f64>,
    pub(crate) rhs_b: Vec<f64>,
    pub(crate) sol_a: Vec<f64>,
    pub(crate) sol_b: Vec<f64>,
    pub(crate) eta_col: Vec<f64>,  // W[i][d-1] for i < d-1
}

impl BlockDiagScratch {
    pub(crate) fn new(decomp: &BlockDecomp, d: usize) -> Self {
        Self {
            w_a: vec![0.0; decomp.d_a * decomp.d_a],
            w_b: vec![0.0; decomp.d_b * decomp.d_b],
            piv_a: vec![0usize; decomp.d_a],
            piv_b: vec![0usize; decomp.d_b],
            rhs_a: vec![0.0; decomp.d_a],
            rhs_b: vec![0.0; decomp.d_b],
            sol_a: vec![0.0; decomp.d_a],
            sol_b: vec![0.0; decomp.d_b],
            eta_col: vec![0.0; d],
        }
    }
}

/// Block-diagonal step: factor two smaller blocks + trivial eta solve.
pub(crate) fn step_blockdiag_rodas5p_into(
    profile: &LinearProfileDyn, y: &[f64], h: f64, cfg: &Rodas5PConfig,
    tab: &Rodas5PTableau, scratch: &mut LinearStepScratch,
    decomp: &BlockDecomp, bscratch: &mut BlockDiagScratch,
) -> (f64, bool, usize) {
    let n_state = profile.n_state;
    let d = n_state + 1;
    let gamma_h = tab.gamma * h;

    // Build full W matrix in scratch.w (same as before)
    scratch.eta_hint = profile.locate(y[d - 1]);
    linear_profile_rhs_jac_flat_into(y, profile, &mut scratch.eta_hint,
        &mut scratch.a_buf, &mut scratch.da_buf, &mut scratch.rhs0, &mut scratch.j0);
    for i in 0..d {
        let row = i * d;
        for j in 0..d {
            scratch.w[row + j] = -scratch.j0[row + j];
        }
        scratch.w[row + i] += 1.0 / gamma_h;
    }

    // Save eta column for later correction
    for i in 0..d {
        bscratch.eta_col[i] = scratch.w[i * d + (d - 1)];
    }

    // Extract Block A sub-matrix
    for (bi, &gi) in decomp.idx_a.iter().enumerate() {
        for (bj, &gj) in decomp.idx_a.iter().enumerate() {
            bscratch.w_a[bi * decomp.d_a + bj] = scratch.w[gi * d + gj];
        }
    }
    // Extract Block B sub-matrix
    for (bi, &gi) in decomp.idx_b.iter().enumerate() {
        for (bj, &gj) in decomp.idx_b.iter().enumerate() {
            bscratch.w_b[bi * decomp.d_b + bj] = scratch.w[gi * d + gj];
        }
    }

    // Factor both blocks
    if !lu_factor_in_place_flat_into(&mut bscratch.w_a, decomp.d_a, &mut bscratch.piv_a) {
        return (f64::INFINITY, false, 0);
    }
    if !lu_factor_in_place_flat_into(&mut bscratch.w_b, decomp.d_b, &mut bscratch.piv_b) {
        return (f64::INFINITY, false, 0);
    }

    // Stage loop
    scratch.ks_flat.fill(0.0);
    let mut n_f_eval = 0usize;
    for i_stage in 0..8 {
        // Build y_stage and RHS (same as original)
        scratch.y_stage.copy_from_slice(y);
        for j in 0..i_stage {
            let aij = tab.a[i_stage][j];
            if aij == 0.0 { continue; }
            let base_j = j * d;
            for m in 0..d {
                scratch.y_stage[m] += aij * scratch.ks_flat[base_j + m];
            }
        }
        linear_profile_rhs_only_into(&scratch.y_stage, profile, &mut scratch.eta_hint,
            &mut scratch.a_buf, &mut scratch.f_stage);
        scratch.rhs.copy_from_slice(&scratch.f_stage);
        for j in 0..i_stage {
            let cij = tab.c[i_stage][j];
            if cij == 0.0 { continue; }
            let scale = cij / h;
            let base_j = j * d;
            for m in 0..d {
                scratch.rhs[m] += scale * scratch.ks_flat[base_j + m];
            }
        }
        n_f_eval += 1;

        // 1. Solve eta trivially
        let k_eta = scratch.rhs[d - 1] * gamma_h;

        // 2. Correct RHS for eta column: rhs'[i] = rhs[i] - W[i][d-1] * k_eta
        for i in 0..(d - 1) {
            scratch.rhs[i] -= bscratch.eta_col[i] * k_eta;
        }

        // 3. Scatter RHS into block vectors
        for (bi, &gi) in decomp.idx_a.iter().enumerate() {
            bscratch.rhs_a[bi] = scratch.rhs[gi];
        }
        for (bi, &gi) in decomp.idx_b.iter().enumerate() {
            bscratch.rhs_b[bi] = scratch.rhs[gi];
        }

        // 4. Solve both blocks
        if !lu_solve_factored_flat_into(&bscratch.w_a, &bscratch.piv_a,
                &bscratch.rhs_a, &mut bscratch.sol_a, decomp.d_a) {
            return (f64::INFINITY, false, n_f_eval);
        }
        if !lu_solve_factored_flat_into(&bscratch.w_b, &bscratch.piv_b,
                &bscratch.rhs_b, &mut bscratch.sol_b, decomp.d_b) {
            return (f64::INFINITY, false, n_f_eval);
        }

        // 5. Gather into full k vector
        let base_i = i_stage * d;
        for (bi, &gi) in decomp.idx_a.iter().enumerate() {
            scratch.ks_flat[base_i + gi] = bscratch.sol_a[bi];
        }
        for (bi, &gi) in decomp.idx_b.iter().enumerate() {
            scratch.ks_flat[base_i + gi] = bscratch.sol_b[bi];
        }
        scratch.ks_flat[base_i + d - 1] = k_eta;
    }

    // Compute y_new and error estimate (same as original)
    scratch.y_new.copy_from_slice(y);
    scratch.err_est.fill(0.0);
    for i in 0..8 {
        let base_i = i * d;
        for m in 0..d {
            let kim = scratch.ks_flat[base_i + m];
            scratch.y_new[m] += tab.b[i] * kim;
            scratch.err_est[m] += tab.bhat[i] * kim;
        }
    }
    scratch.y_new[d - 1] = y[d - 1] + h;
    scratch.err_est[d - 1] = 0.0;
    if !scratch.y_new.iter().all(|v| v.is_finite()) { return (f64::INFINITY, false, n_f_eval); }
    let err = linear_err_norm(&scratch.err_est, &scratch.y_new, n_state, cfg.rtol, cfg.atol);
    (err, true, n_f_eval)
}
