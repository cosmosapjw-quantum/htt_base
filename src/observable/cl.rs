// BE-03: Angular power spectrum C_ℓ from a_{ℓm}.
//
// C_ℓ = (1/(2ℓ+1)) Σ_{m=-ℓ}^{ℓ} |a_{ℓm}|²
//
// For FLRW with primordial spectrum:
// C_ℓ = 4π ∫ dk/k Δ²_ζ(k) |Δ_ℓ(k)|²
//
// D_ℓ = ℓ(ℓ+1) C_ℓ / (2π)  [μK²]

use super::alm::{AlmSet, Complex};

/// Angular power spectrum.
#[derive(Clone, Debug)]
pub(crate) struct ClSpectrum {
    pub(crate) ell_max: usize,
    /// C_ℓ values for ℓ = 0..ℓ_max.
    pub(crate) cl: Vec<f64>,
}

impl ClSpectrum {
    pub(crate) fn new(ell_max: usize) -> Self {
        Self { ell_max, cl: vec![0.0; ell_max + 1] }
    }

    /// Compute C_ℓ from a_{ℓm}.
    pub(crate) fn from_alm(alm: &AlmSet) -> Self {
        let ell_max = alm.ell_max;
        let mut spec = Self::new(ell_max);
        for ell in 0..=ell_max {
            let mut sum = 0.0;
            for m in -(ell as i32)..=(ell as i32) {
                sum += alm.get(ell, m).norm_sq();
            }
            spec.cl[ell] = sum / (2 * ell + 1) as f64;
        }
        spec
    }

    /// Compute C_ℓ from FLRW transfer functions Δ_ℓ(k).
    ///
    /// C_ℓ = 4π ∫ dk/k Δ²_ζ(k) |Δ_ℓ(k)|²
    /// with Δ²_ζ = A_s (k/k_pivot)^{n_s−1}.
    pub(crate) fn from_transfer(
        ell_max: usize,
        k_grid: &[f64],       // k values [Mpc⁻¹]
        transfers: &[Vec<f64>], // transfers[ik][ell] = Δ_ℓ(k)
        a_s: f64,
        n_s: f64,
        k_pivot: f64,
    ) -> Self {
        let mut spec = Self::new(ell_max);
        let n_k = k_grid.len();
        if n_k < 2 { return spec; }

        for ell in 2..=ell_max {
            let mut sum = 0.0;
            for ik in 0..n_k {
                let k = k_grid[ik];
                let delta2 = a_s * (k / k_pivot).powf(n_s - 1.0);
                let dl = if ell < transfers[ik].len() { transfers[ik][ell] } else { 0.0 };

                // dk/k = d(ln k) for log-spaced grid
                let dlnk = if ik < n_k - 1 {
                    (k_grid[ik + 1] / k).ln()
                } else {
                    (k / k_grid[ik - 1]).ln()
                };

                sum += 4.0 * std::f64::consts::PI * delta2 * dl * dl * dlnk;
            }
            spec.cl[ell] = sum;
        }
        spec
    }

    /// D_ℓ = ℓ(ℓ+1) C_ℓ / (2π) [same units as C_ℓ].
    pub(crate) fn dl(&self) -> Vec<f64> {
        self.cl.iter().enumerate().map(|(ell, &c)| {
            if ell < 2 { 0.0 } else { ell as f64 * (ell + 1) as f64 * c / (2.0 * std::f64::consts::PI) }
        }).collect()
    }

    /// Convert to μK²: multiply by T_CMB² [μK²].
    pub(crate) fn to_muK2(&self, t_cmb: f64) -> Self {
        let t_uk = t_cmb * 1e6;
        let t2 = t_uk * t_uk;
        Self {
            ell_max: self.ell_max,
            cl: self.cl.iter().map(|&c| c * t2).collect(),
        }
    }

    /// Check rotational invariance: C_ℓ should be identical before and after rotation.
    pub(crate) fn max_relative_difference(&self, other: &ClSpectrum) -> f64 {
        let mut max_diff = 0.0_f64;
        let n = self.cl.len().min(other.cl.len());
        for ell in 2..n {
            if self.cl[ell].abs() > 1e-30 {
                let rel = (self.cl[ell] - other.cl[ell]).abs() / self.cl[ell].abs();
                max_diff = max_diff.max(rel);
            }
        }
        max_diff
    }
}

/// Bianchi departure power D₂ from a_{ℓm}.
///
/// D₂ = Σ_{m=-2}^{2} |a_{2m}|² [μK² or (ΔT/T)²].
pub(crate) fn compute_d2(alm: &AlmSet) -> f64 {
    let mut d2 = 0.0;
    for m in -2..=2_i32 {
        d2 += alm.get(2, m).norm_sq();
    }
    d2
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cl_from_alm_zero() {
        let a = AlmSet::new(10);
        let cl = ClSpectrum::from_alm(&a);
        for ell in 0..=10 { assert_eq!(cl.cl[ell], 0.0); }
    }

    #[test]
    fn test_cl_from_alm_m0_only() {
        let mut a = AlmSet::new(5);
        a.set_real(2, 0, 3.0);
        let cl = ClSpectrum::from_alm(&a);
        // C_2 = |a_{20}|²/(2×2+1) = 9/5 = 1.8
        assert!((cl.cl[2] - 1.8).abs() < 1e-12, "C_2 = {:.4}", cl.cl[2]);
    }

    #[test]
    fn test_cl_from_alm_all_m() {
        let mut a = AlmSet::new(2);
        // Set a_{2,0} = 1, a_{2,1} = (1, 1), a_{2,2} = (0.5, 0)
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(1.0, 1.0));
        a.set(2, 2, Complex::from_real(0.5));
        let cl = ClSpectrum::from_alm(&a);
        // Σ|a_{2m}|² = |a_{20}|² + |a_{21}|² + |a_{22}|² + |a_{2,-1}|² + |a_{2,-2}|²
        // = 1 + 2 + 0.25 + 2 + 0.25 = 5.5  (conjugation gives same norm)
        // C_2 = 5.5/5 = 1.1
        assert!((cl.cl[2] - 1.1).abs() < 1e-12, "C_2 = {:.4}", cl.cl[2]);
    }

    #[test]
    fn test_dl_conversion() {
        let mut cl = ClSpectrum::new(10);
        cl.cl[2] = 1.0;
        let dl = cl.dl();
        // D_2 = 2×3/(2π) = 3/π ≈ 0.9549
        assert!((dl[2] - 3.0 / std::f64::consts::PI).abs() < 1e-12);
    }

    #[test]
    fn test_d2_from_alm() {
        let mut a = AlmSet::new(5);
        a.set(2, 0, Complex::from_real(1.0));
        a.set(2, 1, Complex::new(0.5, 0.5));
        let d2 = compute_d2(&a);
        // D₂ = |a_{20}|² + |a_{21}|² + |a_{22}|² + |a_{2,-1}|² + |a_{2,-2}|²
        //     = 1 + 0.5 + 0 + 0.5 + 0 = 2.0
        assert!((d2 - 2.0).abs() < 1e-12, "D₂ = {:.4}", d2);
    }

    #[test]
    fn test_muK2_conversion() {
        let mut cl = ClSpectrum::new(5);
        cl.cl[2] = 1e-10;
        let cl_uk = cl.to_muK2(2.7255);
        // T_CMB² in μK² = (2.7255e6)² = 7.428e12
        let expected = 1e-10 * 2.7255e6_f64.powi(2);
        assert!((cl_uk.cl[2] - expected).abs() / expected < 1e-10);
    }

    #[test]
    fn test_cl_from_transfer() {
        let k_grid = vec![0.001, 0.01, 0.1];
        let transfers = vec![
            vec![0.0, 0.0, 0.3, 0.0], // k=0.001: Δ₂=0.3
            vec![0.0, 0.0, 0.2, 0.0], // k=0.01: Δ₂=0.2
            vec![0.0, 0.0, 0.05, 0.0],// k=0.1: Δ₂=0.05
        ];
        let cl = ClSpectrum::from_transfer(3, &k_grid, &transfers, 2.1e-9, 0.965, 0.05);
        assert!(cl.cl[2] > 0.0, "C_2 must be positive");
        assert!(cl.cl[2].is_finite());
    }
}
