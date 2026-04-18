// BE-03: a_{ℓm} coefficient storage.
//
// Complex spherical harmonic coefficients a_{ℓm} for ℓ=0..ℓ_max, m=-ℓ..+ℓ.
// Conjugation symmetry: a_{ℓ,-m} = (−1)^m a*_{ℓm} (real field on sky).
// Storage: only m ≥ 0 stored; m < 0 derived from symmetry.

/// Complex number (Re, Im).
#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct Complex {
    pub(crate) re: f64,
    pub(crate) im: f64,
}

impl Complex {
    pub(crate) fn new(re: f64, im: f64) -> Self { Self { re, im } }
    pub(crate) fn zero() -> Self { Self { re: 0.0, im: 0.0 } }
    pub(crate) fn from_real(r: f64) -> Self { Self { re: r, im: 0.0 } }
    pub(crate) fn norm_sq(&self) -> f64 { self.re * self.re + self.im * self.im }
    pub(crate) fn conj(&self) -> Self { Self { re: self.re, im: -self.im } }
    pub(crate) fn scale(&self, s: f64) -> Self { Self { re: self.re * s, im: self.im * s } }

    pub(crate) fn mul(&self, other: &Complex) -> Complex {
        Complex {
            re: self.re * other.re - self.im * other.im,
            im: self.re * other.im + self.im * other.re,
        }
    }

    pub(crate) fn add(&self, other: &Complex) -> Complex {
        Complex { re: self.re + other.re, im: self.im + other.im }
    }
}

/// Set of a_{ℓm} coefficients.
///
/// Storage: flat array indexed by ℓ(ℓ+1)/2 + m for m ≥ 0.
/// Total size: (ℓ_max+1)(ℓ_max+2)/2 complex numbers.
#[derive(Clone, Debug)]
pub(crate) struct AlmSet {
    /// Maximum multipole.
    pub(crate) ell_max: usize,
    /// Stored coefficients for m ≥ 0.
    data: Vec<Complex>,
}

impl AlmSet {
    /// Create a zero-initialized AlmSet.
    pub(crate) fn new(ell_max: usize) -> Self {
        let size = (ell_max + 1) * (ell_max + 2) / 2;
        Self { ell_max, data: vec![Complex::zero(); size] }
    }

    /// Flat index for (ℓ, m) with m ≥ 0.
    fn idx(&self, ell: usize, m: usize) -> usize {
        ell * (ell + 1) / 2 + m
    }

    /// Get a_{ℓm} for any m (uses conjugation for m < 0).
    pub(crate) fn get(&self, ell: usize, m: i32) -> Complex {
        if ell > self.ell_max { return Complex::zero(); }
        let abs_m = m.unsigned_abs() as usize;
        if abs_m > ell { return Complex::zero(); }

        let val = self.data[self.idx(ell, abs_m)];
        if m >= 0 {
            val
        } else {
            // a_{ℓ,-m} = (−1)^m a*_{ℓm}
            let sign = if abs_m % 2 == 0 { 1.0 } else { -1.0 };
            val.conj().scale(sign)
        }
    }

    /// Set a_{ℓm} for m ≥ 0.
    pub(crate) fn set(&mut self, ell: usize, m: usize, val: Complex) {
        if ell <= self.ell_max && m <= ell {
            let i = self.idx(ell, m);
            self.data[i] = val;
        }
    }

    /// Set from real value (m=0 mode).
    pub(crate) fn set_real(&mut self, ell: usize, m: usize, val: f64) {
        self.set(ell, m, Complex::from_real(val));
    }

    /// Total number of stored coefficients.
    pub(crate) fn n_stored(&self) -> usize { self.data.len() }

    /// Check conjugation symmetry: a_{ℓ,-m} = (−1)^m a*_{ℓm}.
    pub(crate) fn check_conjugation(&self) -> f64 {
        let mut max_err = 0.0_f64;
        for ell in 0..=self.ell_max {
            for m in 1..=ell {
                let a_pos = self.get(ell, m as i32);
                let a_neg = self.get(ell, -(m as i32));
                let sign = if m % 2 == 0 { 1.0 } else { -1.0 };
                let expected = a_pos.conj().scale(sign);
                let err = ((a_neg.re - expected.re).powi(2) + (a_neg.im - expected.im).powi(2)).sqrt();
                max_err = max_err.max(err);
            }
        }
        max_err
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_alm_new() {
        let a = AlmSet::new(10);
        assert_eq!(a.ell_max, 10);
        assert_eq!(a.n_stored(), 66); // 11×12/2
    }

    #[test]
    fn test_alm_set_get() {
        let mut a = AlmSet::new(5);
        a.set(2, 1, Complex::new(3.0, 4.0));
        let v = a.get(2, 1);
        assert!((v.re - 3.0).abs() < 1e-15);
        assert!((v.im - 4.0).abs() < 1e-15);
    }

    #[test]
    fn test_alm_conjugation() {
        let mut a = AlmSet::new(5);
        a.set(3, 2, Complex::new(1.0, 2.0));
        // a_{3,-2} = (−1)² a*_{3,2} = a*_{3,2} = (1, −2)
        let v = a.get(3, -2);
        assert!((v.re - 1.0).abs() < 1e-15);
        assert!((v.im - (-2.0)).abs() < 1e-15);
    }

    #[test]
    fn test_alm_conjugation_odd_m() {
        let mut a = AlmSet::new(5);
        a.set(3, 1, Complex::new(1.0, 2.0));
        // a_{3,-1} = (−1)¹ a*_{3,1} = −(1, −2) = (−1, 2)
        let v = a.get(3, -1);
        assert!((v.re - (-1.0)).abs() < 1e-15);
        assert!((v.im - 2.0).abs() < 1e-15);
    }

    #[test]
    fn test_alm_conjugation_check() {
        let a = AlmSet::new(10);
        // Zero alm satisfies conjugation trivially
        assert!(a.check_conjugation() < 1e-15);
    }

    #[test]
    fn test_alm_m0_real() {
        let mut a = AlmSet::new(5);
        a.set_real(2, 0, 1.5);
        let v = a.get(2, 0);
        assert!((v.re - 1.5).abs() < 1e-15);
        assert!(v.im.abs() < 1e-15);
    }
}
