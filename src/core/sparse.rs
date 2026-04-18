// Compressed Sparse Row (CSR) matrix infrastructure.
// BA-04: For PSTF hierarchy at ℓ_max = 30, d ~ 500.
// Tri/pentadiagonal structure from shear ℓ↔ℓ±2 coupling gives bandwidth ≤ 30,
// so sparse storage uses < 10% of dense at d = 500.

/// Builder for CSR matrices. Accumulates (row, col, val) triplets,
/// then finalizes into a CsrMatrix sorted by row.
pub(crate) struct SparseMatrixBuilder {
    nrows: usize,
    ncols: usize,
    triplets: Vec<(usize, usize, f64)>,
}

impl SparseMatrixBuilder {
    /// Create a builder with estimated non-zero count.
    pub(crate) fn new(nrows: usize, ncols: usize, nnz_estimate: usize) -> Self {
        Self {
            nrows,
            ncols,
            triplets: Vec::with_capacity(nnz_estimate),
        }
    }

    /// Push a (row, col, value) entry. Duplicate (row,col) pairs are summed
    /// during finalization.
    pub(crate) fn push(&mut self, row: usize, col: usize, val: f64) {
        debug_assert!(row < self.nrows, "row {} out of range 0..{}", row, self.nrows);
        debug_assert!(col < self.ncols, "col {} out of range 0..{}", col, self.ncols);
        if val.abs() > 0.0 {
            self.triplets.push((row, col, val));
        }
    }

    /// Finalize into a CsrMatrix. Sorts triplets by (row, col) and sums
    /// duplicate entries.
    pub(crate) fn finalize(mut self) -> CsrMatrix {
        // Sort by (row, col)
        self.triplets.sort_by(|a, b| a.0.cmp(&b.0).then(a.1.cmp(&b.1)));

        let mut row_ptr = vec![0usize; self.nrows + 1];
        let mut col_ind = Vec::with_capacity(self.triplets.len());
        let mut values = Vec::with_capacity(self.triplets.len());

        if !self.triplets.is_empty() {
            let mut prev_row = self.triplets[0].0;
            let mut prev_col = self.triplets[0].1;
            let mut acc = self.triplets[0].2;

            for &(r, c, v) in &self.triplets[1..] {
                if r == prev_row && c == prev_col {
                    // Duplicate: sum values
                    acc += v;
                } else {
                    // Flush previous entry
                    if acc.abs() > 0.0 {
                        col_ind.push(prev_col);
                        values.push(acc);
                        row_ptr[prev_row + 1] += 1;
                    }
                    prev_row = r;
                    prev_col = c;
                    acc = v;
                }
            }
            // Flush last entry
            if acc.abs() > 0.0 {
                col_ind.push(prev_col);
                values.push(acc);
                row_ptr[prev_row + 1] += 1;
            }
        }

        // Cumulative sum for row_ptr
        for i in 0..self.nrows {
            row_ptr[i + 1] += row_ptr[i];
        }

        CsrMatrix {
            nrows: self.nrows,
            ncols: self.ncols,
            row_ptr,
            col_ind,
            values,
        }
    }
}

/// Immutable CSR matrix. Created via SparseMatrixBuilder::finalize().
pub(crate) struct CsrMatrix {
    pub(crate) nrows: usize,
    pub(crate) ncols: usize,
    pub(crate) row_ptr: Vec<usize>,
    pub(crate) col_ind: Vec<usize>,
    pub(crate) values: Vec<f64>,
}

impl CsrMatrix {
    /// Number of stored non-zeros.
    pub(crate) fn nnz(&self) -> usize {
        self.values.len()
    }

    /// Memory footprint in bytes (excluding struct overhead).
    pub(crate) fn memory_bytes(&self) -> usize {
        (self.row_ptr.len() * std::mem::size_of::<usize>())
            + (self.col_ind.len() * std::mem::size_of::<usize>())
            + (self.values.len() * std::mem::size_of::<f64>())
    }

    /// Dense storage equivalent in bytes.
    pub(crate) fn dense_memory_bytes(&self) -> usize {
        self.nrows * self.ncols * std::mem::size_of::<f64>()
    }

    /// Memory ratio: sparse / dense.
    pub(crate) fn memory_ratio(&self) -> f64 {
        self.memory_bytes() as f64 / self.dense_memory_bytes().max(1) as f64
    }

    /// y = A · x
    /// Panics if x.len() < ncols or y.len() < nrows.
    pub(crate) fn spmv(&self, x: &[f64], y: &mut [f64]) {
        debug_assert!(x.len() >= self.ncols);
        debug_assert!(y.len() >= self.nrows);
        for i in 0..self.nrows {
            let mut acc = 0.0;
            let start = self.row_ptr[i];
            let end = self.row_ptr[i + 1];
            for idx in start..end {
                acc += self.values[idx] * x[self.col_ind[idx]];
            }
            y[i] = acc;
        }
    }

    /// y += α · A · x
    /// Panics if x.len() < ncols or y.len() < nrows.
    pub(crate) fn spmv_add(&self, x: &[f64], y: &mut [f64], alpha: f64) {
        debug_assert!(x.len() >= self.ncols);
        debug_assert!(y.len() >= self.nrows);
        for i in 0..self.nrows {
            let mut acc = 0.0;
            let start = self.row_ptr[i];
            let end = self.row_ptr[i + 1];
            for idx in start..end {
                acc += self.values[idx] * x[self.col_ind[idx]];
            }
            y[i] += alpha * acc;
        }
    }

    /// Convert to dense row-major flat array (for testing/comparison).
    #[cfg(test)]
    pub(crate) fn to_dense_flat(&self) -> Vec<f64> {
        let mut out = vec![0.0; self.nrows * self.ncols];
        for i in 0..self.nrows {
            let start = self.row_ptr[i];
            let end = self.row_ptr[i + 1];
            for idx in start..end {
                out[i * self.ncols + self.col_ind[idx]] = self.values[idx];
            }
        }
        out
    }
}

/// Dense mat-vec: y = A · x, where A is row-major flat [n × n].
pub(crate) fn dense_matvec(a: &[f64], x: &[f64], y: &mut [f64], n: usize) {
    for i in 0..n {
        let mut acc = 0.0;
        let row = i * n;
        for j in 0..n {
            acc += a[row + j] * x[j];
        }
        y[i] = acc;
    }
}

/// Build a banded test matrix (d × d) with given bandwidth.
/// Entry A[i][j] = (i+1)*(j+1) if |i-j| ≤ bandwidth, else 0.
/// Returns (SparseMatrixBuilder ready to finalize, dense flat array).
#[cfg(test)]
fn build_banded_test(d: usize, bandwidth: usize) -> (SparseMatrixBuilder, Vec<f64>) {
    let mut builder = SparseMatrixBuilder::new(d, d, d * (2 * bandwidth + 1));
    let mut dense = vec![0.0; d * d];
    for i in 0..d {
        let j_lo = if i > bandwidth { i - bandwidth } else { 0 };
        let j_hi = (i + bandwidth + 1).min(d);
        for j in j_lo..j_hi {
            let val = ((i + 1) * (j + 1)) as f64 * 1e-6;
            builder.push(i, j, val);
            dense[i * d + j] = val;
        }
    }
    (builder, dense)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_csr_basic() {
        // 3×3 matrix: [[1,0,2],[0,3,0],[4,0,5]]
        let mut b = SparseMatrixBuilder::new(3, 3, 5);
        b.push(0, 0, 1.0);
        b.push(0, 2, 2.0);
        b.push(1, 1, 3.0);
        b.push(2, 0, 4.0);
        b.push(2, 2, 5.0);
        let m = b.finalize();
        assert_eq!(m.nnz(), 5);
        assert_eq!(m.row_ptr, vec![0, 2, 3, 5]);

        let x = vec![1.0, 2.0, 3.0];
        let mut y = vec![0.0; 3];
        m.spmv(&x, &mut y);
        assert!((y[0] - 7.0).abs() < 1e-12);  // 1*1 + 2*3
        assert!((y[1] - 6.0).abs() < 1e-12);  // 3*2
        assert!((y[2] - 19.0).abs() < 1e-12); // 4*1 + 5*3
    }

    #[test]
    fn test_spmv_add() {
        let mut b = SparseMatrixBuilder::new(2, 2, 2);
        b.push(0, 0, 2.0);
        b.push(1, 1, 3.0);
        let m = b.finalize();

        let x = vec![10.0, 20.0];
        let mut y = vec![1.0, 1.0];
        m.spmv_add(&x, &mut y, 0.5);
        assert!((y[0] - 11.0).abs() < 1e-12);  // 1 + 0.5*(2*10)
        assert!((y[1] - 31.0).abs() < 1e-12);  // 1 + 0.5*(3*20)
    }

    #[test]
    fn test_duplicate_sum() {
        let mut b = SparseMatrixBuilder::new(2, 2, 3);
        b.push(0, 0, 1.0);
        b.push(0, 0, 2.0);  // duplicate → summed to 3.0
        b.push(1, 1, 4.0);
        let m = b.finalize();
        assert_eq!(m.nnz(), 2);
        let dense = m.to_dense_flat();
        assert!((dense[0] - 3.0).abs() < 1e-12);
        assert!((dense[3] - 4.0).abs() < 1e-12);
    }

    #[test]
    fn test_zero_skip() {
        let mut b = SparseMatrixBuilder::new(2, 2, 2);
        b.push(0, 0, 0.0);  // zero → skipped
        b.push(1, 1, 5.0);
        let m = b.finalize();
        assert_eq!(m.nnz(), 1);
    }

    #[test]
    fn test_empty_matrix() {
        let b = SparseMatrixBuilder::new(10, 10, 0);
        let m = b.finalize();
        assert_eq!(m.nnz(), 0);
        let x = vec![1.0; 10];
        let mut y = vec![999.0; 10];
        m.spmv(&x, &mut y);
        for &yi in &y { assert!(yi.abs() < 1e-12); }
    }

    fn max_abs_diff(a: &[f64], b: &[f64]) -> f64 {
        a.iter().zip(b.iter()).map(|(x, y)| (x - y).abs()).fold(0.0f64, f64::max)
    }

    #[test]
    fn test_sparse_vs_dense_d100_bw15() {
        let d = 100;
        let bw = 15;
        let (builder, dense) = build_banded_test(d, bw);
        let csr = builder.finalize();

        let x: Vec<f64> = (0..d).map(|i| (i as f64 + 1.0).sqrt()).collect();
        let mut y_sparse = vec![0.0; d];
        let mut y_dense = vec![0.0; d];

        csr.spmv(&x, &mut y_sparse);
        dense_matvec(&dense, &x, &mut y_dense, d);

        let err = max_abs_diff(&y_sparse, &y_dense);
        assert!(err < 1e-10, "d={} bw={}: max err = {:.2e}", d, bw, err);
    }

    #[test]
    fn test_sparse_vs_dense_d200_bw15() {
        let d = 200;
        let bw = 15;
        let (builder, dense) = build_banded_test(d, bw);
        let csr = builder.finalize();

        let x: Vec<f64> = (0..d).map(|i| (i as f64 + 1.0).sqrt()).collect();
        let mut y_sparse = vec![0.0; d];
        let mut y_dense = vec![0.0; d];

        csr.spmv(&x, &mut y_sparse);
        dense_matvec(&dense, &x, &mut y_dense, d);

        let err = max_abs_diff(&y_sparse, &y_dense);
        assert!(err < 1e-10, "d={} bw={}: max err = {:.2e}", d, bw, err);
    }

    #[test]
    fn test_sparse_vs_dense_d500_bw10() {
        // PSTF hierarchy: ℓ↔ℓ±2 coupling gives half-bandwidth ~5 per species,
        // ~10 for full multi-species stacked system.
        let d = 500;
        let bw = 10;
        let (builder, dense) = build_banded_test(d, bw);
        let csr = builder.finalize();

        let x: Vec<f64> = (0..d).map(|i| (i as f64 + 1.0).sqrt()).collect();
        let mut y_sparse = vec![0.0; d];
        let mut y_dense = vec![0.0; d];

        csr.spmv(&x, &mut y_sparse);
        dense_matvec(&dense, &x, &mut y_dense, d);

        let err = max_abs_diff(&y_sparse, &y_dense);
        assert!(err < 1e-10, "d={} bw={}: max err = {:.2e}", d, bw, err);

        // Memory ratio check: sparse < 10% of dense at d=500, bw=30
        let ratio = csr.memory_ratio();
        assert!(ratio < 0.10, "d={} bw={}: memory ratio = {:.4} (want < 0.10)", d, bw, ratio);
    }

    #[test]
    fn test_memory_ratio() {
        let d = 500;
        let bw = 10; // PSTF-realistic half-bandwidth
        let (builder, _) = build_banded_test(d, bw);
        let csr = builder.finalize();
        let ratio = csr.memory_ratio();
        // nnz ≈ d*(2*bw+1) = 500*21 = 10500
        // sparse memory: (501 + 10500 + 10500) * 8 = 172008
        // dense memory: 250000 * 8 = 2000000
        // ratio ≈ 0.086 → passes < 10%
        eprintln!("Memory ratio at d={}, bw={}: {:.4}", d, bw, ratio);
        assert!(ratio < 0.10, "d={} bw={}: memory ratio = {:.4} (want < 0.10)", d, bw, ratio);
    }

    #[test]
    fn test_benchmark_spmv_vs_dense() {
        // Timing benchmark (informational, not a hard pass/fail)
        use std::time::Instant;

        for &(d, bw) in &[(100, 15), (200, 15), (500, 30)] {
            let (builder, dense) = build_banded_test(d, bw);
            let csr = builder.finalize();
            let x: Vec<f64> = (0..d).map(|i| (i as f64 + 1.0).sqrt()).collect();
            let mut y = vec![0.0; d];

            let n_iter = 1000;

            let t0 = Instant::now();
            for _ in 0..n_iter {
                csr.spmv(&x, &mut y);
            }
            let sparse_us = t0.elapsed().as_micros() as f64 / n_iter as f64;

            let t0 = Instant::now();
            for _ in 0..n_iter {
                dense_matvec(&dense, &x, &mut y, d);
            }
            let dense_us = t0.elapsed().as_micros() as f64 / n_iter as f64;

            let speedup = dense_us / sparse_us.max(0.001);
            let ratio = csr.memory_ratio();
            eprintln!(
                "d={:>3} bw={:>2}: sparse {:.1}us, dense {:.1}us, speedup {:.2}x, mem {:.3}",
                d, bw, sparse_us, dense_us, speedup, ratio
            );
        }
    }
}
