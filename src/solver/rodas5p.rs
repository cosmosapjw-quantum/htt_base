// Pure Rodas5P stepper: LinearProfileDyn, scratch, dense step, error norm.
// BA-03: Extracted from profile.rs.

use crate::core::config::*;
use crate::core::controller::*;
use crate::core::lu::*;

#[derive(Clone)]
pub(crate) struct LinearProfileDyn {
    pub(crate) eta: Vec<f64>,
    pub(crate) mats_flat: Vec<f64>, // flattened row-major n_state x n_state per sample
    pub(crate) n_state: usize,
    pub(crate) stride: usize,
}

impl LinearProfileDyn {
    pub(crate) fn new(eta: Vec<f64>, mats_flat: Vec<f64>, n_state: usize) -> Result<Self, String> {
        if eta.len() < 2 { return Err("eta profile must contain at least two samples".to_string()); }
        for i in 1..eta.len() {
            if eta[i] <= eta[i - 1] { return Err("eta profile must be strictly increasing".to_string()); }
        }
        let stride = n_state * n_state;
        let expected = eta.len() * stride;
        if mats_flat.len() != expected {
            return Err(format!("matrix profile size mismatch: got {}, expected {}", mats_flat.len(), expected));
        }
        Ok(Self { eta, mats_flat, n_state, stride })
    }

    pub(crate) fn locate(&self, eta_now: f64) -> usize {
        if eta_now <= self.eta[0] { return 0; }
        let n = self.eta.len();
        if eta_now >= self.eta[n - 1] { return n - 2; }
        let mut lo = 0usize;
        let mut hi = n - 1;
        while hi - lo > 1 {
            let mid = (hi + lo) >> 1;
            if self.eta[mid] <= eta_now { lo = mid; } else { hi = mid; }
        }
        lo.min(n - 2)
    }

    fn locate_with_hint(&self, eta_now: f64, hint: &mut usize) -> usize {
        let n = self.eta.len();
        if eta_now <= self.eta[0] { *hint = 0; return 0; }
        if eta_now >= self.eta[n - 1] { *hint = n - 2; return n - 2; }
        let mut i = (*hint).min(n - 2);
        if eta_now < self.eta[i] {
            while i > 0 && eta_now < self.eta[i] { i -= 1; }
            if eta_now < self.eta[i] {
                i = self.locate(eta_now);
            } else {
                while i + 1 < n - 1 && eta_now >= self.eta[i + 1] { i += 1; }
            }
        } else {
            while i + 1 < n - 1 && eta_now >= self.eta[i + 1] { i += 1; }
        }
        *hint = i;
        i
    }

    pub(crate) fn sample_matrix_only_into_hint(&self, eta_now: f64, hint: &mut usize, a_out: &mut [f64]) {
        let i = self.locate_with_hint(eta_now, hint);
        let e0 = self.eta[i];
        let e1 = self.eta[i + 1];
        let w = ((eta_now - e0) / (e1 - e0)).clamp(0.0, 1.0);
        let base0 = i * self.stride;
        let base1 = (i + 1) * self.stride;
        for k in 0..self.stride {
            let v0 = self.mats_flat[base0 + k];
            let v1 = self.mats_flat[base1 + k];
            a_out[k] = v0 + w * (v1 - v0);
        }
    }

    pub(crate) fn sample_into_hint(&self, eta_now: f64, hint: &mut usize, a_out: &mut [f64], da_out: &mut [f64]) {
        let i = self.locate_with_hint(eta_now, hint);
        let e0 = self.eta[i];
        let e1 = self.eta[i + 1];
        let w = ((eta_now - e0) / (e1 - e0)).clamp(0.0, 1.0);
        let denom = (e1 - e0).max(1e-30);
        let base0 = i * self.stride;
        let base1 = (i + 1) * self.stride;
        for k in 0..self.stride {
            let v0 = self.mats_flat[base0 + k];
            let v1 = self.mats_flat[base1 + k];
            a_out[k] = v0 + w * (v1 - v0);
            da_out[k] = (v1 - v0) / denom;
        }
    }

    fn sample_matrix_only_into(&self, eta_now: f64, a_out: &mut [f64]) {
        let mut hint = self.locate(eta_now);
        self.sample_matrix_only_into_hint(eta_now, &mut hint, a_out);
    }

    fn sample_into(&self, eta_now: f64, a_out: &mut [f64], da_out: &mut [f64]) {
        let mut hint = self.locate(eta_now);
        self.sample_into_hint(eta_now, &mut hint, a_out, da_out);
    }
}

pub(crate) fn linear_profile_rhs_only_into(y_ext: &[f64], profile: &LinearProfileDyn, eta_hint: &mut usize, a_buf: &mut [f64], rhs: &mut [f64]) {
    let n_state = profile.n_state;
    let d = n_state + 1;
    let eta_now = y_ext[d - 1];
    profile.sample_matrix_only_into_hint(eta_now, eta_hint, a_buf);
    // PR-PERF-05: iter/zip matvec. a_buf and y_ext are distinct slices so
    // LLVM can auto-vectorize (SSE2 at minimum; AVX2 with -C target-cpu=v3).
    // The row slice is contiguous n_state entries; zip with y_ext[0..n_state]
    // produces a clean SIMD-friendly reduction.
    let y_head = &y_ext[..n_state];
    for (i, row) in a_buf.chunks_exact(n_state).enumerate().take(n_state) {
        let mut acc = 0.0_f64;
        for (a_ij, y_j) in row.iter().zip(y_head.iter()) {
            acc += *a_ij * *y_j;
        }
        rhs[i] = acc;
    }
    rhs[d - 1] = 1.0;
}

pub(crate) fn linear_profile_rhs_jac_flat_into(y_ext: &[f64], profile: &LinearProfileDyn, eta_hint: &mut usize, a_buf: &mut [f64], da_buf: &mut [f64], rhs: &mut [f64], jac: &mut [f64]) {
    let n_state = profile.n_state;
    let d = n_state + 1;
    let eta_now = y_ext[d - 1];
    profile.sample_into_hint(eta_now, eta_hint, a_buf, da_buf);
    jac.fill(0.0);
    // PR-PERF-05: combined matvec + Jacobian copy + τ-derivative dot.
    // Reuses the same iter/zip idiom — four slices (a_row, da_row, jac_row,
    // y_head) are mutually disjoint so LLVM can vectorize all three reductions.
    let y_head = &y_ext[..n_state];
    let mut a_iter = a_buf.chunks_exact(n_state);
    let mut da_iter = da_buf.chunks_exact(n_state);
    let mut jac_iter = jac.chunks_exact_mut(d);
    for i in 0..n_state {
        let a_row = a_iter.next().expect("a_buf chunks");
        let da_row = da_iter.next().expect("da_buf chunks");
        let jac_row = jac_iter.next().expect("jac chunks");
        // jac[row + 0..n_state] = a_row
        jac_row[..n_state].copy_from_slice(a_row);
        // acc = a_row · y_head
        let mut acc = 0.0_f64;
        for (a_ij, y_j) in a_row.iter().zip(y_head.iter()) {
            acc += *a_ij * *y_j;
        }
        rhs[i] = acc;
        // dacc = da_row · y_head  (written into last column of jac row)
        let mut dacc = 0.0_f64;
        for (da_ij, y_j) in da_row.iter().zip(y_head.iter()) {
            dacc += *da_ij * *y_j;
        }
        jac_row[d - 1] = dacc;
    }
    rhs[d - 1] = 1.0;
}

pub(crate) struct LinearStepScratch {
    pub(crate) rhs0: Vec<f64>,
    pub(crate) j0: Vec<f64>,
    pub(crate) a_buf: Vec<f64>,
    pub(crate) da_buf: Vec<f64>,
    pub(crate) w: Vec<f64>,
    pub(crate) piv: Vec<usize>,
    pub(crate) ipiv_blas: Vec<i32>,  // PR-14A: LAPACK pivot indices
    pub(crate) ks_flat: Vec<f64>,
    pub(crate) y_stage: Vec<f64>,
    pub(crate) f_stage: Vec<f64>,
    pub(crate) rhs: Vec<f64>,
    pub(crate) y_new: Vec<f64>,
    pub(crate) err_est: Vec<f64>,
    pub(crate) eta_hint: usize,
}

impl LinearStepScratch {
    pub(crate) fn new(n_state: usize, stride: usize) -> Self {
        let d = n_state + 1;
        Self {
            rhs0: vec![0.0; d],
            j0: vec![0.0; d * d],
            a_buf: vec![0.0; stride],
            da_buf: vec![0.0; stride],
            w: vec![0.0; d * d],
            piv: vec![0usize; d],
            ipiv_blas: vec![0i32; d],
            ks_flat: vec![0.0; 8 * d],
            y_stage: vec![0.0; d],
            f_stage: vec![0.0; d],
            rhs: vec![0.0; d],
            y_new: vec![0.0; d],
            err_est: vec![0.0; d],
            eta_hint: 0usize,
        }
    }

    #[inline]
    fn ks_stage(&self, stage: usize, d: usize) -> &[f64] {
        let base = stage * d;
        &self.ks_flat[base..base + d]
    }

    #[inline]
    fn ks_stage_mut(&mut self, stage: usize, d: usize) -> &mut [f64] {
        let base = stage * d;
        &mut self.ks_flat[base..base + d]
    }
}
pub(crate) fn linear_err_norm(err_est: &[f64], y: &[f64], n_state: usize, rtol: f64, atol: f64) -> f64 {
    let mut worst = 0.0_f64;
    for i in 0..n_state {
        let sc = atol + rtol * y[i].abs();
        worst = worst.max((err_est[i] / sc).abs());
    }
    worst
}

pub(crate) fn linear_vec_add_scaled(base: &[f64], ks: &[Vec<f64>], coeffs: &[[f64; 8]; 8], i_stage: usize) -> Vec<f64> {
    let mut out = base.to_vec();
    for j in 0..i_stage {
        let aij = coeffs[i_stage][j];
        if aij == 0.0 { continue; }
        for m in 0..out.len() { out[m] += aij * ks[j][m]; }
    }
    out
}

pub(crate) fn linear_c_sum_term(ks: &[Vec<f64>], coeffs: &[[f64; 8]; 8], i_stage: usize, h: f64, d: usize) -> Vec<f64> {
    let mut out = vec![0.0; d];
    for j in 0..i_stage {
        let cij = coeffs[i_stage][j];
        if cij == 0.0 { continue; }
        for m in 0..d { out[m] += cij * ks[j][m] / h; }
    }
    out
}

pub(crate) fn step_linear_profile_rodas5p_into(profile: &LinearProfileDyn, y: &[f64], h: f64, cfg: &Rodas5PConfig, tab: &Rodas5PTableau, scratch: &mut LinearStepScratch) -> (f64, bool, usize) {
    let n_state = profile.n_state;
    let d = n_state + 1;
    scratch.eta_hint = profile.locate(y[d - 1]);
    linear_profile_rhs_jac_flat_into(y, profile, &mut scratch.eta_hint, &mut scratch.a_buf, &mut scratch.da_buf, &mut scratch.rhs0, &mut scratch.j0);
    for i in 0..d {
        let row = i * d;
        for j in 0..d {
            scratch.w[row + j] = -scratch.j0[row + j];
        }
        scratch.w[row + i] += 1.0 / (tab.gamma * h);
    }
    if cfg.use_blas_lu {
        if !blas_lu_factor_in_place_flat_into(&mut scratch.w, d, &mut scratch.ipiv_blas) { return (f64::INFINITY, false, 0usize); }
    } else {
        if !lu_factor_in_place_flat_into(&mut scratch.w, d, &mut scratch.piv) { return (f64::INFINITY, false, 0usize); }
    }
    scratch.ks_flat.fill(0.0);
    let mut n_f_eval = 0usize;
    for i_stage in 0..8 {
        scratch.y_stage.copy_from_slice(y);
        for j in 0..i_stage {
            let aij = tab.a[i_stage][j];
            if aij == 0.0 { continue; }
            let base_j = j * d;
            for m in 0..d {
                scratch.y_stage[m] += aij * scratch.ks_flat[base_j + m];
            }
        }
        linear_profile_rhs_only_into(&scratch.y_stage, profile, &mut scratch.eta_hint, &mut scratch.a_buf, &mut scratch.f_stage);
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
        let base_i = i_stage * d;
        let solve_ok = if cfg.use_blas_lu {
            blas_lu_solve_factored_flat_into(&scratch.w, &scratch.ipiv_blas, &scratch.rhs, &mut scratch.ks_flat[base_i..base_i + d], d)
        } else {
            lu_solve_factored_flat_into(&scratch.w, &scratch.piv, &scratch.rhs, &mut scratch.ks_flat[base_i..base_i + d], d)
        };
        if !solve_ok {
            return (f64::INFINITY, false, n_f_eval);
        }
    }
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

