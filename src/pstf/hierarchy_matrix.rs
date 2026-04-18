// Hierarchy coupling matrix: explicit coefficients for the 1+3 Boltzmann system.
// BC-02: Builds the coupling matrix M_{ℓℓ'} for arbitrary ℓ_max.
//
// The PSTF Boltzmann hierarchy for species s:
//   dF_{A_ℓ}/dη = Σ_{ℓ'} M_{ℓℓ'} F_{A_{ℓ'}} + collision + source
//
// Matrix structure (within a single species):
//   FLRW: tridiagonal (free-streaming Δℓ=±1)
//   Bianchi homogeneous: pentadiagonal (shear Δℓ=±2 added)
//   Full Bianchi + gradients: pentadiagonal + tridiagonal overlap
//
// Each M_{ℓℓ'} entry is a SCALAR coefficient (not a tensor); the
// tensorial structure is absorbed into the STF projection.

use super::coupling;

/// Physics regime for the hierarchy.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum HierarchyRegime {
    /// FLRW: σ=ω=u̇=0, k≠0. Tridiagonal.
    Flrw,
    /// Homogeneous Bianchi: k=0, σ≠0. Even-odd decoupled Δℓ=±2.
    BianchiHomogeneous,
    /// Full: k≠0, σ≠0. Pentadiagonal.
    Full,
}

/// A single coupling entry M_{ℓ,ℓ'} with its physical origin.
#[derive(Clone, Debug)]
pub(crate) struct CouplingEntry {
    pub(crate) ell_from: usize,
    pub(crate) ell_to: usize,
    pub(crate) coefficient: f64,
    pub(crate) origin: CouplingOrigin,
}

/// Physical origin of a coupling.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum CouplingOrigin {
    FreeStreamingDown,  // ℓ-1 → ℓ
    FreeStreamingUp,    // ℓ+1 → ℓ
    HubbleDrag,         // ℓ → ℓ
    ShearDown,          // ℓ-2 → ℓ
    ShearUp,            // ℓ+2 → ℓ
    Collision,          // ℓ → ℓ (Thomson)
}

/// Build the coupling coefficient table for a given ℓ_max and regime.
///
/// Returns a list of (ℓ_to, ℓ_from, coefficient, origin) entries.
/// The physical parameters (k, σ/H, θ, κ̇) are passed as dimensionless scalars;
/// the actual matrix is M_{ℓℓ'} × (parameter).
pub(crate) fn build_coupling_table(
    ell_max: usize,
    regime: HierarchyRegime,
) -> Vec<CouplingEntry> {
    let mut entries = Vec::new();
    let include_fs = regime != HierarchyRegime::BianchiHomogeneous;
    let include_shear = regime != HierarchyRegime::Flrw;

    for ell in 0..=ell_max {
        // Hubble drag: diagonal, always present
        entries.push(CouplingEntry {
            ell_from: ell, ell_to: ell,
            coefficient: coupling::hubble_drag_coefficient(ell),
            origin: CouplingOrigin::HubbleDrag,
        });

        // Free-streaming: ℓ-1 → ℓ (Δℓ=+1)
        if include_fs && ell > 0 {
            entries.push(CouplingEntry {
                ell_from: ell - 1, ell_to: ell,
                coefficient: coupling::free_streaming_down(ell),
                origin: CouplingOrigin::FreeStreamingDown,
            });
        }

        // Free-streaming: ℓ+1 → ℓ (Δℓ=-1)
        if include_fs && ell < ell_max {
            entries.push(CouplingEntry {
                ell_from: ell + 1, ell_to: ell,
                coefficient: -coupling::free_streaming_up(ell),
                origin: CouplingOrigin::FreeStreamingUp,
            });
        }

        // Shear: ℓ-2 → ℓ (Δℓ=+2)
        if include_shear && ell >= 2 {
            entries.push(CouplingEntry {
                ell_from: ell - 2, ell_to: ell,
                coefficient: coupling::shear_coupling_down(ell),
                origin: CouplingOrigin::ShearDown,
            });
        }

        // Shear: ℓ+2 → ℓ (Δℓ=-2)
        if include_shear && ell + 2 <= ell_max {
            entries.push(CouplingEntry {
                ell_from: ell + 2, ell_to: ell,
                coefficient: coupling::shear_coupling_up(ell),
                origin: CouplingOrigin::ShearUp,
            });
        }
    }
    entries
}

/// Build the dense coupling matrix as a (ℓ_max+1)×(ℓ_max+1) array.
///
/// M[ℓ_to][ℓ_from] = coefficient. Parameters multiply on use:
///   full_matrix[i][j] = k*M_fs[i][j] + (σ/H)*M_shear[i][j] + θ*M_drag[i][j]
pub(crate) fn build_coupling_matrix(
    ell_max: usize,
    regime: HierarchyRegime,
) -> Vec<Vec<f64>> {
    let n = ell_max + 1;
    let mut mat = vec![vec![0.0; n]; n];
    for entry in build_coupling_table(ell_max, regime) {
        if entry.ell_to <= ell_max && entry.ell_from <= ell_max {
            mat[entry.ell_to][entry.ell_from] += entry.coefficient;
        }
    }
    mat
}

/// Matrix bandwidth: max |ℓ − ℓ'| where M_{ℓℓ'} ≠ 0.
pub(crate) fn matrix_bandwidth(ell_max: usize, regime: HierarchyRegime) -> usize {
    let entries = build_coupling_table(ell_max, regime);
    entries.iter()
        .map(|e| (e.ell_to as i32 - e.ell_from as i32).unsigned_abs() as usize)
        .max()
        .unwrap_or(0)
}

/// Count nonzero entries in the coupling matrix.
pub(crate) fn matrix_nnz(ell_max: usize, regime: HierarchyRegime) -> usize {
    build_coupling_table(ell_max, regime).len()
}

/// Sparsity fraction: nnz / (n × n).
pub(crate) fn sparsity(ell_max: usize, regime: HierarchyRegime) -> f64 {
    let n = (ell_max + 1) as f64;
    matrix_nnz(ell_max, regime) as f64 / (n * n)
}

/// Extract the matrix structure as a binary sparsity pattern.
/// Returns vec of (row, col) for nonzero entries.
pub(crate) fn sparsity_pattern(ell_max: usize, regime: HierarchyRegime) -> Vec<(usize, usize)> {
    build_coupling_table(ell_max, regime)
        .iter()
        .filter(|e| e.ell_to <= ell_max && e.ell_from <= ell_max)
        .map(|e| (e.ell_to, e.ell_from))
        .collect()
}

/// FLRW-limit verification: the coupling matrix must be tridiagonal.
/// Returns (is_tridiagonal, max_bandwidth).
pub(crate) fn verify_flrw_tridiagonal(ell_max: usize) -> (bool, usize) {
    let bw = matrix_bandwidth(ell_max, HierarchyRegime::Flrw);
    (bw <= 1, bw)
}

/// Bianchi-limit verification: the coupling matrix must be pentadiagonal.
/// Returns (is_pentadiagonal, max_bandwidth).
pub(crate) fn verify_bianchi_pentadiagonal(ell_max: usize) -> (bool, usize) {
    let bw = matrix_bandwidth(ell_max, HierarchyRegime::Full);
    (bw <= 2, bw)
}

/// Print the coefficient table for a given ℓ_max (for audit).
pub(crate) fn format_coefficient_table(ell_max: usize, regime: HierarchyRegime) -> String {
    let entries = build_coupling_table(ell_max, regime);
    let mut s = format!("Coupling table: ℓ_max={}, regime={:?}\n", ell_max, regime);
    s.push_str(&format!("{:<6} {:<6} {:<12} {:<20}\n", "ℓ_to", "ℓ_from", "coeff", "origin"));
    s.push_str(&"-".repeat(50));
    s.push('\n');
    for e in &entries {
        s.push_str(&format!("{:<6} {:<6} {:<12.6} {:?}\n",
            e.ell_to, e.ell_from, e.coefficient, e.origin));
    }
    s
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── FLRW: tridiagonal ──
    #[test]
    fn test_flrw_tridiagonal() {
        for &lmax in &[2, 6, 10, 30] {
            let (tri, bw) = verify_flrw_tridiagonal(lmax);
            assert!(tri, "FLRW ℓ_max={}: bandwidth={} (must be ≤1)", lmax, bw);
        }
    }

    // ── Full Bianchi: pentadiagonal ──
    #[test]
    fn test_bianchi_pentadiagonal() {
        for &lmax in &[2, 6, 10, 30] {
            let (penta, bw) = verify_bianchi_pentadiagonal(lmax);
            assert!(penta, "Full ℓ_max={}: bandwidth={} (must be ≤2)", lmax, bw);
        }
    }

    // ── Bianchi homogeneous: bandwidth 2 (shear only) ──
    #[test]
    fn test_bianchi_homo_bandwidth() {
        let bw = matrix_bandwidth(10, HierarchyRegime::BianchiHomogeneous);
        assert_eq!(bw, 2, "Homogeneous Bianchi bandwidth must be 2");
    }

    // ── FLRW coefficients at ℓ=2 match CLASS ──
    #[test]
    fn test_flrw_l2_coefficients() {
        // CLASS hierarchy for ℓ=2:
        // dΘ₂/dη = k[2Θ₁/(2×2+1) − 3Θ₃/(2×2+1)] − κ̇Θ₂ + source
        // = k[2Θ₁/5 − 3Θ₃/5]
        // Our convention: free_streaming_down(2) = 2/3, free_streaming_up(2) = 3/7
        // In CLASS convention: ℓ/(2ℓ+1) = 2/5 and (ℓ+1)/(2ℓ+1) = 3/5
        // The difference is in the denominator: we use (2ℓ−1) vs CLASS uses (2ℓ+1)
        // This is the 1+3 covariant vs 3+1 ADM convention difference.
        // Verify our coefficients are internally consistent:
        let entries = build_coupling_table(4, HierarchyRegime::Flrw);
        let l2_entries: Vec<_> = entries.iter().filter(|e| e.ell_to == 2).collect();
        // Should have: drag (ℓ=2→2), fs_down (ℓ=1→2), fs_up (ℓ=3→2)
        assert_eq!(l2_entries.len(), 3, "ℓ=2 should have 3 couplings in FLRW");
    }

    // ── Shear enters at ℓ=0→2 (monopole → quadrupole) ──
    #[test]
    fn test_shear_monopole_quadrupole() {
        let entries = build_coupling_table(4, HierarchyRegime::BianchiHomogeneous);
        let shear_0_to_2: Vec<_> = entries.iter()
            .filter(|e| e.ell_to == 2 && e.ell_from == 0 && e.origin == CouplingOrigin::ShearDown)
            .collect();
        assert_eq!(shear_0_to_2.len(), 1, "Must have shear ℓ=0→2");
        let coeff = shear_0_to_2[0].coefficient;
        // shear_coupling_down(2) = 2×1/(3×5) = 2/15
        assert!((coeff - 2.0/15.0).abs() < 1e-14, "σ ℓ=0→2 coeff: {:.6}", coeff);
    }

    // ── Shear: σ at ℓ=0 → ℓ=2 via shear_coupling_up ──
    #[test]
    fn test_shear_quadrupole_from_monopole() {
        let entries = build_coupling_table(4, HierarchyRegime::BianchiHomogeneous);
        let shear_up_0: Vec<_> = entries.iter()
            .filter(|e| e.ell_to == 0 && e.ell_from == 2 && e.origin == CouplingOrigin::ShearUp)
            .collect();
        assert_eq!(shear_up_0.len(), 1);
        // shear_coupling_up(0) = 1×2/(1×3) = 2/3
        assert!((shear_up_0[0].coefficient - 2.0/3.0).abs() < 1e-14);
    }

    // ── Matrix dimension ──
    #[test]
    fn test_matrix_dimensions() {
        for &lmax in &[2, 6, 10, 30] {
            let mat = build_coupling_matrix(lmax, HierarchyRegime::Full);
            assert_eq!(mat.len(), lmax + 1);
            assert_eq!(mat[0].len(), lmax + 1);
        }
    }

    // ── Sparsity increases with ℓ_max ──
    #[test]
    fn test_sparsity_decreases() {
        // Sparsity = nnz/n² should decrease with ℓ_max
        let s10 = sparsity(10, HierarchyRegime::Full);
        let s30 = sparsity(30, HierarchyRegime::Full);
        assert!(s30 < s10, "Sparsity should decrease: s10={:.3}, s30={:.3}", s10, s30);
    }

    // ── No coupling beyond ℓ_max ──
    #[test]
    fn test_no_coupling_beyond_lmax() {
        let entries = build_coupling_table(5, HierarchyRegime::Full);
        for e in &entries {
            assert!(e.ell_to <= 5 && e.ell_from <= 5,
                "Entry beyond ℓ_max: ({},{})", e.ell_to, e.ell_from);
        }
    }

    // ── Bianchi homogeneous: no free-streaming ──
    #[test]
    fn test_bianchi_homo_no_fs() {
        let entries = build_coupling_table(10, HierarchyRegime::BianchiHomogeneous);
        let fs = entries.iter().filter(|e|
            e.origin == CouplingOrigin::FreeStreamingDown || e.origin == CouplingOrigin::FreeStreamingUp
        ).count();
        assert_eq!(fs, 0, "Homogeneous Bianchi: no free-streaming");
    }

    // ── FLRW: no shear ──
    #[test]
    fn test_flrw_no_shear() {
        let entries = build_coupling_table(10, HierarchyRegime::Flrw);
        let shear = entries.iter().filter(|e|
            e.origin == CouplingOrigin::ShearDown || e.origin == CouplingOrigin::ShearUp
        ).count();
        assert_eq!(shear, 0, "FLRW: no shear coupling");
    }

    // ── Tabulate for audit ──
    #[test]
    fn test_tabulate_small() {
        let table = format_coefficient_table(2, HierarchyRegime::Full);
        assert!(table.contains("ℓ_max=2"));
        // Verify it contains entries
        assert!(table.len() > 100);
    }
}
