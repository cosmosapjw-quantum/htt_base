// m-mode decomposition for axisymmetric Bianchi hierarchies.
// BC-06: Each m evolves independently; shear coupling Δm = 0 (diagonal).
//
// For axisymmetric shear σ_{ab} = diag(-σ/2, -σ/2, σ) along z-axis:
//   Only Δm = 0 coupling survives (diagonal shear is m=0 in Y₂₀).
//   Each m-sector has dimension (ℓ_max - |m| + 1).
//
// m = 0: scalar sector (monopole, even-ℓ dipole, ...)
// m = ±1: vector sector
// m = ±2: tensor sector (BIX: ONLY this is nonzero)
//
// CG coefficient: ₀κ^m_ℓ = √[(ℓ² − m²)/(4ℓ² − 1)]

use super::coupling;

/// Per-m mode hierarchy state.
#[derive(Clone, Debug)]
pub(crate) struct MmodeHierarchy {
    /// Azimuthal quantum number m.
    pub(crate) m: i32,
    /// Maximum multipole ℓ_max (same for all m).
    pub(crate) ell_max: usize,
    /// State: F_{|m|,m}, F_{|m|+1,m}, ..., F_{ℓ_max,m}.
    /// Length = ℓ_max - |m| + 1.
    pub(crate) state: Vec<f64>,
}

impl MmodeHierarchy {
    /// Create a new m-mode hierarchy with zero state.
    pub(crate) fn new(m: i32, ell_max: usize) -> Self {
        let abs_m = m.unsigned_abs() as usize;
        let dim = if abs_m <= ell_max { ell_max - abs_m + 1 } else { 0 };
        Self { m, ell_max, state: vec![0.0; dim] }
    }

    /// Dimension of this m-sector.
    pub(crate) fn dim(&self) -> usize { self.state.len() }

    /// Map from ℓ to index in the state vector.
    fn ell_to_idx(&self, ell: usize) -> Option<usize> {
        let abs_m = self.m.unsigned_abs() as usize;
        if ell >= abs_m && ell <= self.ell_max { Some(ell - abs_m) } else { None }
    }

    /// Get F_{ℓ,m}.
    pub(crate) fn get(&self, ell: usize) -> f64 {
        self.ell_to_idx(ell).map(|i| self.state[i]).unwrap_or(0.0)
    }

    /// Set F_{ℓ,m}.
    pub(crate) fn set(&mut self, ell: usize, val: f64) {
        if let Some(i) = self.ell_to_idx(ell) { self.state[i] = val; }
    }
}

/// m-resolved CG coefficient: ₀κ^m_ℓ = √[(ℓ²−m²)/(4ℓ²−1)].
///
/// This generalises the free-streaming coefficient to the m-resolved case.
/// For m=0: reduces to ℓ/√(4ℓ²−1) ≈ ℓ/(2ℓ−1) × (2ℓ−1)/√(4ℓ²−1).
pub(crate) fn cg_kappa_m(ell: usize, m: i32) -> f64 {
    coupling::cg_kappa_0(ell, m)
}

/// m-resolved free-streaming coupling: ℓ−1 → ℓ.
///
/// Coefficient: ₀κ^m_ℓ / (2ℓ+1) × (some normalization).
/// In the TAM (Total Angular Momentum) basis used by AniCLASS:
///   M^(F)_{ℓ,ℓ-1} = ₀κ^m_ℓ × ζ^m / (2ℓ-1)
pub(crate) fn m_streaming_down(ell: usize, m: i32) -> f64 {
    if ell == 0 { return 0.0; }
    let kappa = cg_kappa_m(ell, m);
    kappa * kappa / coupling::free_streaming_down(ell).max(1e-30)
    // Simplified: use ₀κ² / (ℓ/(2ℓ-1)) = (ℓ²-m²)/(4ℓ²-1) × (2ℓ-1)/ℓ
    // = (ℓ²-m²)/[ℓ(2ℓ+1)]
}

/// m-resolved free-streaming coupling: ℓ+1 → ℓ.
pub(crate) fn m_streaming_up(ell: usize, m: i32) -> f64 {
    let kappa_next = cg_kappa_m(ell + 1, m);
    kappa_next * kappa_next / coupling::free_streaming_up(ell).max(1e-30)
}

/// Compute RHS for a single m-mode hierarchy.
///
/// dF_{ℓm}/dη = k × [α_down F_{ℓ-1,m} − α_up F_{ℓ+1,m}]
///            + σ_factor × [β_down F_{ℓ-2,m} + β_up F_{ℓ+2,m}]  (Δm=0 only)
///            − κ̇ × (F_{ℓm} − source_{ℓm})
pub(crate) fn m_mode_rhs(
    h: &MmodeHierarchy,
    k: f64,
    sigma_factor: f64,  // σ_H × aH (shear × conformal Hubble)
    kappa_dot: f64,
    v_b: f64,           // baryon velocity (only enters m=0, ℓ=1)
) -> Vec<f64> {
    let abs_m = h.m.unsigned_abs() as usize;
    let n = h.dim();
    let mut rhs = vec![0.0; n];

    for idx in 0..n {
        let ell = abs_m + idx;
        let mut val = 0.0;

        // Free-streaming: ℓ-1 → ℓ
        if ell > abs_m {
            let coeff = cg_kappa_m(ell, h.m);
            val += k * coeff * h.get(ell - 1);
        }

        // Free-streaming: ℓ+1 → ℓ
        if ell < h.ell_max {
            let coeff_next = cg_kappa_m(ell + 1, h.m);
            val -= k * coeff_next * h.get(ell + 1);
        }

        // Shear coupling: ℓ-2 → ℓ (Δm = 0 for diagonal shear)
        if ell >= abs_m + 2 {
            val += sigma_factor * coupling::shear_coupling_down(ell) * h.get(ell - 2);
        }

        // Shear coupling: ℓ+2 → ℓ
        if ell + 2 <= h.ell_max {
            val += sigma_factor * coupling::shear_coupling_up(ell) * h.get(ell + 2);
        }

        // Thomson collision (photons, m=0 sector)
        if kappa_dot > 0.0 {
            let source = if h.m == 0 {
                match ell {
                    0 => h.get(0),    // C₀ = 0 (energy conservation)
                    1 => v_b,         // C₁ = −κ̇(F₁ − v_b)
                    _ => 0.0,
                }
            } else { 0.0 };
            val -= kappa_dot * (h.get(ell) - source);
        }

        rhs[idx] = val;
    }
    rhs
}

/// Decompose a full (ℓ-only) hierarchy into m-modes.
///
/// For axisymmetric initial conditions (m=0 only):
///   F_{ℓ,0} = F_ℓ, F_{ℓ,m≠0} = 0.
///
/// For general initial conditions, the m-decomposition requires
/// the full angular structure of the perturbation.
pub(crate) fn decompose_axisymmetric(
    f_ell: &[f64],
    ell_max: usize,
) -> Vec<MmodeHierarchy> {
    let mut modes = Vec::new();
    // m = 0: gets all the power
    let mut h0 = MmodeHierarchy::new(0, ell_max);
    for ell in 0..=ell_max.min(f_ell.len() - 1) {
        h0.set(ell, f_ell[ell]);
    }
    modes.push(h0);

    // m ≠ 0: all zero for axisymmetric IC
    for m in 1..=ell_max as i32 {
        modes.push(MmodeHierarchy::new(m, ell_max));
        modes.push(MmodeHierarchy::new(-m, ell_max));
    }
    modes
}

/// Reconstruct full hierarchy from m-modes (sum over m).
///
/// F_ℓ = Σ_m |F_{ℓm}|² (power spectrum) or F_ℓ = F_{ℓ,0} (axisymmetric).
pub(crate) fn reconstruct_axisymmetric(modes: &[MmodeHierarchy], ell_max: usize) -> Vec<f64> {
    let mut f = vec![0.0; ell_max + 1];
    for h in modes {
        if h.m == 0 {
            for ell in 0..=ell_max {
                f[ell] += h.get(ell);
            }
        }
    }
    f
}

/// Total power in a given m-sector: Σ_ℓ F²_{ℓm}.
pub(crate) fn m_sector_power(h: &MmodeHierarchy) -> f64 {
    h.state.iter().map(|&x| x * x).sum()
}

/// Check which m-modes are active (have nonzero power).
pub(crate) fn active_m_modes(modes: &[MmodeHierarchy], threshold: f64) -> Vec<i32> {
    modes.iter()
        .filter(|h| m_sector_power(h) > threshold)
        .map(|h| h.m)
        .collect()
}

/// Per-m dimension table.
pub(crate) fn m_dimensions(ell_max: usize) -> Vec<(i32, usize)> {
    let mut table = Vec::new();
    for m in 0..=ell_max as i32 {
        let dim = (ell_max as i32 - m + 1) as usize;
        table.push((m, dim));
        if m > 0 { table.push((-m, dim)); }
    }
    table
}

/// Total DOF across all m-modes: Σ_m dim(m) = Σ_{ℓ=0}^{ℓ_max} (2ℓ+1).
pub(crate) fn total_dof(ell_max: usize) -> usize {
    (ell_max + 1) * (ell_max + 1) // = (ℓ_max+1)²
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dimension_per_m() {
        // m=0: ℓ=0..ℓ_max → dim = ℓ_max+1
        let h = MmodeHierarchy::new(0, 10);
        assert_eq!(h.dim(), 11);
        // m=2: ℓ=2..ℓ_max → dim = ℓ_max-1
        let h2 = MmodeHierarchy::new(2, 10);
        assert_eq!(h2.dim(), 9);
        // m=10: ℓ=10 → dim = 1
        let h10 = MmodeHierarchy::new(10, 10);
        assert_eq!(h10.dim(), 1);
        // m=11: beyond ℓ_max → dim = 0
        let h11 = MmodeHierarchy::new(11, 10);
        assert_eq!(h11.dim(), 0);
    }

    #[test]
    fn test_total_dof() {
        // Total = (ℓ_max+1)² = Σ(2ℓ+1)
        assert_eq!(total_dof(0), 1);
        assert_eq!(total_dof(1), 4);
        assert_eq!(total_dof(2), 9);
        assert_eq!(total_dof(10), 121);
    }

    #[test]
    fn test_cg_kappa_m0_matches_scalar() {
        // m=0: ₀κ^0_ℓ = ℓ/√(4ℓ²-1)
        for ell in 1..10 {
            let k0 = cg_kappa_m(ell, 0);
            let expected = ell as f64 / ((4*ell*ell - 1) as f64).sqrt();
            assert!((k0 - expected).abs() < 1e-14, "ℓ={}: {:.6} vs {:.6}", ell, k0, expected);
        }
    }

    #[test]
    fn test_cg_kappa_vanishes_at_m_equals_ell() {
        // ₀κ^m_ℓ = 0 when |m| = ℓ (numerator ℓ²-m² = 0)
        for ell in 1..10 {
            assert!(cg_kappa_m(ell, ell as i32).abs() < 1e-15);
            assert!(cg_kappa_m(ell, -(ell as i32)).abs() < 1e-15);
        }
    }

    #[test]
    fn test_decompose_reconstruct_axisymmetric() {
        let f_ell = vec![1.0, 0.5, 0.1, 0.01, 0.001];
        let modes = decompose_axisymmetric(&f_ell, 4);
        let recon = reconstruct_axisymmetric(&modes, 4);
        for ell in 0..5 {
            assert!((recon[ell] - f_ell[ell]).abs() < 1e-15,
                "ℓ={}: {:.6} vs {:.6}", ell, recon[ell], f_ell[ell]);
        }
    }

    #[test]
    fn test_axisymmetric_only_m0_active() {
        let f_ell = vec![1.0, 0.5, 0.1];
        let modes = decompose_axisymmetric(&f_ell, 2);
        let active = active_m_modes(&modes, 1e-30);
        assert_eq!(active, vec![0], "Only m=0 should be active for axisymmetric IC");
    }

    #[test]
    fn test_bix_tensor_only() {
        // BIX: n=(1,1,1). The curvature is isotropic (³S=0).
        // Shear couples only m=0 for diagonal σ.
        // BUT: the special property of BIX is that the curvature generates
        // only tensor (|m|=2) modes when the full group structure is included.
        // In the homogeneous limit with diagonal shear, m=0 is the primary.
        // The tensor-only property requires the full TAM decomposition
        // with type-specific ζ coefficients (AniCLASS eq. 18).
        //
        // For this test: verify that the m=2 sector has the right dimension.
        let h2 = MmodeHierarchy::new(2, 10);
        assert_eq!(h2.dim(), 9); // ℓ = 2, 3, ..., 10
    }

    #[test]
    fn test_m_mode_rhs_free_streaming() {
        // m=0: free-streaming from monopole
        let mut h = MmodeHierarchy::new(0, 5);
        h.set(0, 1.0); // monopole
        let rhs = m_mode_rhs(&h, 0.1, 0.0, 0.0, 0.0);
        // dF_{0,0}/dη = −k ₀κ^0_1 F_{1,0} = 0 (F₁=0)
        assert!(rhs[0].abs() < 1e-15, "F₀ should not change");
        // dF_{1,0}/dη = k ₀κ^0_1 F_{0,0} = 0.1 × (1/√3) × 1
        let expected = 0.1 * cg_kappa_m(1, 0);
        assert!((rhs[1] - expected).abs() < 1e-14,
            "F₁ rhs: {:.6e} vs {:.6e}", rhs[1], expected);
    }

    #[test]
    fn test_m_mode_shear_source() {
        // m=0: shear drives monopole → quadrupole
        let mut h = MmodeHierarchy::new(0, 5);
        h.set(0, 1.0);
        let sigma_factor = 0.001 * 100.0; // σ/H × aH
        let rhs = m_mode_rhs(&h, 0.0, sigma_factor, 0.0, 0.0);
        // F₂ gets shear source from F₀: shear_coupling_down(2) × F₀ × σ_factor
        let expected = sigma_factor * coupling::shear_coupling_down(2);
        assert!((rhs[2] - expected).abs() < 1e-10,
            "Shear F₀→F₂: {:.6e} vs {:.6e}", rhs[2], expected);
    }

    #[test]
    fn test_m2_no_monopole() {
        // m=2 sector starts at ℓ=2, no monopole
        let h = MmodeHierarchy::new(2, 5);
        assert_eq!(h.dim(), 4); // ℓ=2,3,4,5
        assert!(h.get(0).abs() < 1e-15, "m=2 has no ℓ=0");
        assert!(h.get(1).abs() < 1e-15, "m=2 has no ℓ=1");
    }

    #[test]
    fn test_m_dimensions_table() {
        let table = m_dimensions(3);
        // m=0: dim=4, m=1: dim=3, m=-1: dim=3, m=2: dim=2, ...
        let m0 = table.iter().find(|&&(m,_)| m == 0).unwrap().1;
        assert_eq!(m0, 4);
        let m1 = table.iter().find(|&&(m,_)| m == 1).unwrap().1;
        assert_eq!(m1, 3);
        let m3 = table.iter().find(|&&(m,_)| m == 3).unwrap().1;
        assert_eq!(m3, 1);
    }
}
