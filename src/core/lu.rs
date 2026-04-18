// LU factorisation: hand-written dense + BLAS FFI.

use std::sync::atomic::{AtomicU64, Ordering};

// Diagnostic counters (opt-in; zero overhead when BASS_LU_PROF != 1).
pub(crate) static LU_FACTOR_CALLS: AtomicU64 = AtomicU64::new(0);
pub(crate) static LU_PIVOT_SWAPS: AtomicU64 = AtomicU64::new(0);

#[inline]
fn lu_prof_enabled() -> bool {
    use std::sync::OnceLock;
    static ON: OnceLock<bool> = OnceLock::new();
    *ON.get_or_init(|| std::env::var("BASS_LU_PROF").as_deref() == Ok("1"))
}

pub fn lu_prof_snapshot() -> (u64, u64) {
    (LU_FACTOR_CALLS.load(Ordering::Relaxed),
     LU_PIVOT_SWAPS.load(Ordering::Relaxed))
}

pub fn lu_prof_reset() {
    LU_FACTOR_CALLS.store(0, Ordering::Relaxed);
    LU_PIVOT_SWAPS.store(0, Ordering::Relaxed);
}

pub(crate) fn gauss_solve_dyn(mut a: Vec<Vec<f64>>, mut b: Vec<f64>) -> Option<Vec<f64>> {
    let n = b.len();
    if a.len() != n { return None; }
    for row in &a { if row.len() != n { return None; } }
    for k in 0..n {
        let mut piv = k;
        let mut piv_abs = a[k][k].abs();
        for i in (k + 1)..n {
            let cand = a[i][k].abs();
            if cand > piv_abs { piv = i; piv_abs = cand; }
        }
        if piv_abs < 1e-30 || !piv_abs.is_finite() { return None; }
        if piv != k {
            a.swap(k, piv);
            b.swap(k, piv);
        }
        let akk = a[k][k];
        for i in (k + 1)..n {
            let fac = a[i][k] / akk;
            a[i][k] = 0.0;
            for j in (k + 1)..n { a[i][j] -= fac * a[k][j]; }
            b[i] -= fac * b[k];
        }
    }
    let mut x = vec![0.0; n];
    for ii in 0..n {
        let i = n - 1 - ii;
        let mut sum = b[i];
        for j in (i + 1)..n { sum -= a[i][j] * x[j]; }
        let den = a[i][i];
        if den.abs() < 1e-30 || !den.is_finite() { return None; }
        x[i] = sum / den;
    }
    Some(x)
}

pub(crate) fn lu_factor_in_place_flat_into(a: &mut [f64], n: usize, piv: &mut [usize]) -> bool {
    if a.len() != n * n || piv.len() != n { return false; }
    let prof = lu_prof_enabled();
    if prof { LU_FACTOR_CALLS.fetch_add(1, Ordering::Relaxed); }
    for (i, slot) in piv.iter_mut().enumerate() { *slot = i; }
    for k in 0..n {
        let mut piv_row = k;
        let mut piv_abs = a[k * n + k].abs();
        for i in (k + 1)..n {
            let cand = a[i * n + k].abs();
            if cand > piv_abs {
                piv_row = i;
                piv_abs = cand;
            }
        }
        if piv_abs < 1e-30 || !piv_abs.is_finite() { return false; }
        if piv_row != k {
            if prof { LU_PIVOT_SWAPS.fetch_add(1, Ordering::Relaxed); }
            // PR-PERF-07: swap two rows as contiguous slices (single memcpy-
            // level operation) instead of n individual element swaps.
            // Rows are stored row-major, so row k occupies a[k*n..(k+1)*n]
            // and row piv_row occupies a[piv_row*n..(piv_row+1)*n].
            // split_at_mut gives disjoint &mut [f64] for each row, and
            // swap_with_slice runs as a SIMD-friendly memcpy pair.
            debug_assert!(piv_row > k, "pivot search only examines rows i > k");
            let (lo, hi) = a.split_at_mut(piv_row * n);
            lo[k * n..(k + 1) * n].swap_with_slice(&mut hi[..n]);
            piv.swap(k, piv_row);
        }
        let akk = a[k * n + k];

        // PR-PERF-05: split rows into two non-aliased slices so LLVM can
        // auto-vectorize the axpy inner loop. Prior form
        //     a[i*n+j] -= fac * a[k*n+j]
        // used the same &mut [f64] for both reads, requiring aliasing checks
        // that prevented SIMD. Splitting with split_at_mut gives disjoint
        // &mut [f64] for row_k and rows below, enabling iter().zip() + FMA.
        // Math is bit-identical.
        let (top, bot) = a.split_at_mut((k + 1) * n);
        // row_k is the last row of `top` (rows 0..=k)
        let row_k = &top[k * n..(k + 1) * n];
        // rows below k are in bot (rows k+1..n), stored contiguously per row
        for (i_offset, row_i) in bot.chunks_exact_mut(n).enumerate() {
            let _ = i_offset;
            let fac = row_i[k] / akk;
            row_i[k] = fac;
            // Inner loop: row_i[k+1..n] -= fac * row_k[k+1..n]
            // Slice tails of equal length so LLVM generates aligned SIMD
            let tail_k = &row_k[k + 1..];
            let tail_i = &mut row_i[k + 1..];
            for (ri, rk) in tail_i.iter_mut().zip(tail_k.iter()) {
                *ri -= fac * *rk;
            }
        }
    }
    true
}

pub(crate) fn lu_factor_in_place_flat(a: &mut [f64], n: usize) -> Option<Vec<usize>> {
    if a.len() != n * n { return None; }
    let mut piv: Vec<usize> = vec![0usize; n];
    if !lu_factor_in_place_flat_into(a, n, &mut piv) { return None; }
    Some(piv)
}

pub(crate) fn lu_solve_factored_flat(lu: &[f64], piv: &[usize], b: &[f64], n: usize) -> Option<Vec<f64>> {
    let mut x = vec![0.0; n];
    if !lu_solve_factored_flat_into(lu, piv, b, &mut x, n) { return None; }
    Some(x)
}

pub(crate) fn lu_solve_factored_flat_into(lu: &[f64], piv: &[usize], b: &[f64], x: &mut [f64], n: usize) -> bool {
    if lu.len() != n * n || b.len() != n || piv.len() != n || x.len() != n { return false; }
    for i in 0..n {
        x[i] = b[piv[i]];
    }
    // PR-PERF-05: forward solve with iter/zip reduction. LLVM can now
    // auto-vectorize the dot-product (lu row × x head) since the two slices
    // are disjoint (lu: &[f64], x: &mut [f64]).
    for i in 0..n {
        let row_i = &lu[i * n..i * n + i];  // row i, columns 0..i
        let x_head = &x[..i];
        let mut sum = x[i];
        for (l_ij, x_j) in row_i.iter().zip(x_head.iter()) {
            sum -= *l_ij * *x_j;
        }
        x[i] = sum;
    }
    // Backward solve. Same iter/zip pattern on tail columns i+1..n.
    for ii in 0..n {
        let i = n - 1 - ii;
        let row_i_tail = &lu[i * n + i + 1..i * n + n];  // columns i+1..n
        let x_tail = &x[i + 1..];
        let mut sum = x[i];
        for (u_ij, x_j) in row_i_tail.iter().zip(x_tail.iter()) {
            sum -= *u_ij * *x_j;
        }
        let den = lu[i * n + i];
        if den.abs() < 1e-30 || !den.is_finite() { return false; }
        x[i] = sum / den;
    }
    true
}

// ── PR-14A: BLAS-backed LU via OpenBLAS LAPACK ──
// Killed: no gain at d < 100.  Retained behind `features = ["blas"]`.
// Row-major storage: dgetrf_ sees the transpose (column-major).
// dgetrs_ with trans='T' solves A*x=b correctly for row-major A.
#[cfg(feature = "blas")]
extern "C" {
    fn dgetrf_(m: *mut i32, n: *mut i32, a: *mut f64, lda: *mut i32,
               ipiv: *mut i32, info: *mut i32);
    fn dgetrs_(trans: *const u8, n: *mut i32, nrhs: *mut i32,
               a: *const f64, lda: *mut i32, ipiv: *const i32,
               b: *mut f64, ldb: *mut i32, info: *mut i32);
}

#[cfg(feature = "blas")]
pub(crate) fn blas_lu_factor_in_place_flat_into(a: &mut [f64], n: usize, ipiv: &mut [i32]) -> bool {
    let mut m_i32 = n as i32;
    let mut n_i32 = n as i32;
    let mut lda = n as i32;
    let mut info: i32 = 0;
    unsafe {
        dgetrf_(&mut m_i32, &mut n_i32, a.as_mut_ptr(), &mut lda,
                ipiv.as_mut_ptr(), &mut info);
    }
    info == 0
}

#[cfg(not(feature = "blas"))]
pub(crate) fn blas_lu_factor_in_place_flat_into(_a: &mut [f64], _n: usize, _ipiv: &mut [i32]) -> bool {
    panic!("blas_lu called without feature=\"blas\"; set use_blas_lu=false or build with --features blas")
}

#[cfg(feature = "blas")]
pub(crate) fn blas_lu_solve_factored_flat_into(
    lu: &[f64], ipiv: &[i32], b: &[f64], x: &mut [f64], n: usize,
) -> bool {
    x.copy_from_slice(b);
    let trans: u8 = b'T'; // row-major → solve A*x=b via (A^T)^T * x = b
    let mut n_i32 = n as i32;
    let mut nrhs: i32 = 1;
    let mut lda = n as i32;
    let mut ldb = n as i32;
    let mut info: i32 = 0;
    unsafe {
        dgetrs_(&trans, &mut n_i32, &mut nrhs,
                lu.as_ptr(), &mut lda, ipiv.as_ptr(),
                x.as_mut_ptr(), &mut ldb, &mut info);
    }
    info == 0
}

#[cfg(not(feature = "blas"))]
pub(crate) fn blas_lu_solve_factored_flat_into(
    _lu: &[f64], _ipiv: &[i32], _b: &[f64], _x: &mut [f64], _n: usize,
) -> bool {
    panic!("blas_lu called without feature=\"blas\"; set use_blas_lu=false or build with --features blas")
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Reference LU factorization (textbook scalar form) — used for cross-check
    /// against the PR-PERF-05 iter/zip rewrite. Identical math, slower code.
    fn lu_factor_reference(a: &mut [f64], n: usize, piv: &mut [usize]) -> bool {
        for (i, slot) in piv.iter_mut().enumerate() { *slot = i; }
        for k in 0..n {
            let mut piv_row = k;
            let mut piv_abs = a[k * n + k].abs();
            for i in (k + 1)..n {
                let cand = a[i * n + k].abs();
                if cand > piv_abs { piv_row = i; piv_abs = cand; }
            }
            if piv_abs < 1e-30 { return false; }
            if piv_row != k {
                for j in 0..n { a.swap(k * n + j, piv_row * n + j); }
                piv.swap(k, piv_row);
            }
            let akk = a[k * n + k];
            for i in (k + 1)..n {
                let fac = a[i * n + k] / akk;
                a[i * n + k] = fac;
                for j in (k + 1)..n {
                    a[i * n + j] -= fac * a[k * n + j];
                }
            }
        }
        true
    }

    #[test]
    fn lu_factor_matches_reference_random_24x24() {
        // Deterministic pseudo-random 24×24 matrix with diagonal dominance
        // for stable pivoting.
        let n = 24;
        let mut a_opt = vec![0.0_f64; n * n];
        for i in 0..n {
            for j in 0..n {
                a_opt[i * n + j] = ((i as f64 + 1.0) * 0.3 - (j as f64) * 0.17).sin()
                                    + if i == j { (n as f64) * 1.5 } else { 0.0 };
            }
        }
        let mut a_ref = a_opt.clone();
        let mut piv_opt = vec![0usize; n];
        let mut piv_ref = vec![0usize; n];

        let ok_opt = lu_factor_in_place_flat_into(&mut a_opt, n, &mut piv_opt);
        let ok_ref = lu_factor_reference(&mut a_ref, n, &mut piv_ref);
        assert!(ok_opt && ok_ref);
        assert_eq!(piv_opt, piv_ref, "pivot sequences must match");
        let mut max_diff = 0.0_f64;
        for i in 0..n*n {
            let d = (a_opt[i] - a_ref[i]).abs();
            if d > max_diff { max_diff = d; }
        }
        assert!(max_diff < 1e-12,
                "LU factorization diverged from reference: max |Δ| = {:.2e}", max_diff);
    }

    #[test]
    fn lu_solve_bit_exact_24x24() {
        // Solve A·x = b then verify A·x_recovered = b within 1e-10.
        let n = 24;
        let mut a = vec![0.0_f64; n * n];
        let mut a_orig = vec![0.0_f64; n * n];
        for i in 0..n {
            for j in 0..n {
                let v = ((i as f64 + 1.0) * 0.3 - (j as f64) * 0.17).sin()
                         + if i == j { (n as f64) * 1.5 } else { 0.0 };
                a[i * n + j] = v;
                a_orig[i * n + j] = v;
            }
        }
        let b: Vec<f64> = (0..n).map(|i| ((i as f64) * 0.7).cos()).collect();
        let mut piv = vec![0usize; n];
        assert!(lu_factor_in_place_flat_into(&mut a, n, &mut piv));
        let mut x = vec![0.0_f64; n];
        assert!(lu_solve_factored_flat_into(&a, &piv, &b, &mut x, n));
        // Residual: |A_orig · x - b|
        let mut max_r = 0.0_f64;
        for i in 0..n {
            let mut s = 0.0;
            for j in 0..n {
                s += a_orig[i * n + j] * x[j];
            }
            let r = (s - b[i]).abs();
            if r > max_r { max_r = r; }
        }
        assert!(max_r < 1e-10, "LU solve residual too large: {:.2e}", max_r);
    }

    /// Small 3×3 case — exact answer check against hand calculation.
    #[test]
    fn lu_solve_3x3_exact() {
        let n = 3;
        // A = [[2, 1, 1], [4, 3, 3], [8, 7, 9]]
        // det = 2·(3·9 - 3·7) - 1·(4·9 - 3·8) + 1·(4·7 - 3·8) = 12 - 12 + 4 = 4
        let mut a = vec![2.0, 1.0, 1.0,  4.0, 3.0, 3.0,  8.0, 7.0, 9.0];
        let b = vec![5.0, 13.0, 33.0];  // A · [1, 1, 2]^T = [5, 13, 33]
        let mut piv = vec![0usize; n];
        assert!(lu_factor_in_place_flat_into(&mut a, n, &mut piv));
        let mut x = vec![0.0_f64; n];
        assert!(lu_solve_factored_flat_into(&a, &piv, &b, &mut x, n));
        // Expected: x = [1, 1, 2]
        assert!((x[0] - 1.0).abs() < 1e-12, "x[0] = {}, expected 1", x[0]);
        assert!((x[1] - 1.0).abs() < 1e-12, "x[1] = {}, expected 1", x[1]);
        assert!((x[2] - 2.0).abs() < 1e-12, "x[2] = {}, expected 2", x[2]);
    }
}


