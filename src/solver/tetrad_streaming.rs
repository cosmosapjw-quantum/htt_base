//! TF-02: Tetrad-based streaming matrix with shear coupling.
//!
//! Builds the full hierarchy matrix A(η) including:
//!   - Free-streaming: ℓ ↔ ℓ±1 (coefficient: k × α_ℓ)
//!   - Shear streaming: ℓ ↔ ℓ±2 (coefficient: σ × β_ℓ)  ← NEW
//!   - Hubble drag: −(ℓ+1)H/3 on diagonal
//!   - Thomson collision: −κ̇ for ℓ ≥ 2 (photon only)
//!
//! This replaces `build_flrw_matrix` for the tetrad-based solver.
//! FLRW limit (σ=0): reduces to tridiagonal (bandwidth=1).
//! Bianchi limit (σ≠0): pentadiagonal (bandwidth=2).
//!
//! Convention: PSTF with F_ℓ = (2ℓ+1)Θ_ℓ (CAMB-compatible).

use crate::pstf::coupling;
use crate::bianchi::tetrad::TetradShear;

/// Species block descriptor.
#[derive(Clone, Debug)]
pub(crate) struct SpeciesBlock {
    /// Starting index in the state vector.
    pub(crate) offset: usize,
    /// Number of multipoles (ℓ = 0..ell_max).
    pub(crate) ell_max: usize,
    /// Whether Thomson collision applies (photon: yes, neutrino: no).
    pub(crate) has_collision: bool,
}

/// Tetrad streaming background at a single time step.
#[derive(Clone, Debug)]
pub(crate) struct TetradStreamingBg {
    /// Wavenumber k [Mpc⁻¹].
    pub(crate) k: f64,
    /// Conformal Hubble aH [Mpc⁻¹].
    pub(crate) a_h: f64,
    /// Thomson scattering rate κ̇ [Mpc⁻¹].
    pub(crate) kappa_dot: f64,
    /// Full tensor shear.
    pub(crate) shear: TetradShear,
    /// Scalar shear magnitude σ = √(σ²) for isotropic coupling.
    /// For Bianchi I axisymmetric: σ = √2 |σ₊|.
    pub(crate) sigma_scalar: f64,
}

/// Build the streaming+collision matrix for a single species block.
///
/// Returns flat row-major matrix of size (ell_max+1)².
/// This is the PHOTON or NEUTRINO block independently.
///
/// Physics:
///   dF_ℓ/dη = Σ_ℓ' A_{ℓℓ'} F_ℓ'
///
/// where:
///   A_{ℓ,ℓ-1} = +k × ℓ/(2ℓ-1)                    [free-streaming down]
///   A_{ℓ,ℓ+1} = −k × (ℓ+1)/(2ℓ+3)                 [free-streaming up]
///   A_{ℓ,ℓ-2} = +σ × ℓ(ℓ-1)/[(2ℓ-1)(2ℓ+1)]       [shear coupling down]
///   A_{ℓ,ℓ+2} = −σ × (ℓ+1)(ℓ+2)/[(2ℓ+1)(2ℓ+3)]   [shear coupling up]
///   A_{ℓ,ℓ}   = −κ̇ (ℓ ≥ 2, photon only)           [Thomson damping]
///                −(ℓ+1)aH/3                         [Hubble drag, optional]
pub(crate) fn build_species_streaming_matrix(
    bg: &TetradStreamingBg,
    ell_max: usize,
    has_collision: bool,
    include_hubble_drag: bool,
) -> Vec<f64> {
    let n = ell_max + 1;
    let mut mat = vec![0.0_f64; n * n];
    let idx = |i: usize, j: usize| i * n + j;

    for ell in 0..=ell_max {
        // ── Free-streaming: ℓ ↔ ℓ±1 ──
        if ell > 0 {
            // Coupling from ℓ-1 → ℓ: +k × α_ℓ^{down}
            mat[idx(ell, ell - 1)] += bg.k * coupling::free_streaming_down(ell);
        }
        if ell < ell_max {
            // Coupling from ℓ+1 → ℓ: −k × α_ℓ^{up}
            mat[idx(ell, ell + 1)] -= bg.k * coupling::free_streaming_up(ell);
        }

        // ── Shear streaming: ℓ ↔ ℓ±2 (TF-02: NEW) ──
        if ell >= 2 {
            // Coupling from ℓ-2 → ℓ: +σ × β_ℓ^{down}
            mat[idx(ell, ell - 2)] += bg.sigma_scalar * coupling::shear_coupling_down(ell);
        }
        if ell + 2 <= ell_max {
            // Coupling from ℓ+2 → ℓ: −σ × β_ℓ^{up}
            mat[idx(ell, ell + 2)] -= bg.sigma_scalar * coupling::shear_coupling_up(ell);
        }

        // ── Diagonal: collision + Hubble drag ──
        if has_collision && ell >= 2 {
            mat[idx(ell, ell)] -= bg.kappa_dot;
        }
        if include_hubble_drag {
            mat[idx(ell, ell)] -= (ell + 1) as f64 * bg.a_h / 3.0;
        }
    }
    mat
}

/// Verify bandwidth of the streaming matrix.
/// Returns (bandwidth, is_pentadiagonal).
pub(crate) fn verify_bandwidth(mat: &[f64], n: usize) -> (usize, bool) {
    let mut max_bw = 0usize;
    for i in 0..n {
        for j in 0..n {
            if mat[i * n + j].abs() > 1e-30 {
                let bw = (i as i32 - j as i32).unsigned_abs() as usize;
                max_bw = max_bw.max(bw);
            }
        }
    }
    (max_bw, max_bw <= 2)
}

/// Extract the sparsity pattern as (row, col) pairs.
pub(crate) fn sparsity_pattern(mat: &[f64], n: usize) -> Vec<(usize, usize)> {
    let mut pattern = Vec::new();
    for i in 0..n {
        for j in 0..n {
            if mat[i * n + j].abs() > 1e-30 {
                pattern.push((i, j));
            }
        }
    }
    pattern
}

#[cfg(test)]
mod tests {
    use super::*;

    fn flrw_bg(k: f64) -> TetradStreamingBg {
        TetradStreamingBg {
            k,
            a_h: 100.0,
            kappa_dot: 1e4,
            shear: TetradShear::new(0.0, 0.0),
            sigma_scalar: 0.0,
        }
    }

    fn bianchi_bg(k: f64, sigma: f64) -> TetradStreamingBg {
        TetradStreamingBg {
            k,
            a_h: 100.0,
            kappa_dot: 1e4,
            shear: TetradShear::new(sigma / 2.0_f64.sqrt(), 0.0),
            sigma_scalar: sigma,
        }
    }

    /// TF-02 GATE 1: FLRW limit → tridiagonal (bandwidth=1).
    #[test]
    fn test_flrw_tridiagonal() {
        for ell_max in [4, 8, 15, 30] {
            let bg = flrw_bg(0.01);
            let mat = build_species_streaming_matrix(&bg, ell_max, true, false);
            let (bw, _) = verify_bandwidth(&mat, ell_max + 1);
            assert!(bw <= 1, "FLRW must be tridiagonal, got bandwidth={} at ℓ_max={}", bw, ell_max);
        }
    }

    /// TF-02 GATE 2: Bianchi → pentadiagonal (bandwidth=2).
    #[test]
    fn test_bianchi_pentadiagonal() {
        for ell_max in [4, 8, 15, 30] {
            let bg = bianchi_bg(0.01, 1e-3);
            let mat = build_species_streaming_matrix(&bg, ell_max, true, false);
            let (bw, is_penta) = verify_bandwidth(&mat, ell_max + 1);
            assert_eq!(bw, 2, "Bianchi must be pentadiagonal, got bandwidth={} at ℓ_max={}", bw, ell_max);
            assert!(is_penta);
        }
    }

    /// TF-02 GATE 3: σ=0 exactly recovers FLRW matrix.
    #[test]
    fn test_sigma_zero_equals_flrw() {
        let ell_max = 10;
        let k = 0.01;
        let flrw = build_species_streaming_matrix(&flrw_bg(k), ell_max, true, false);
        let bianchi_zero = build_species_streaming_matrix(&bianchi_bg(k, 0.0), ell_max, true, false);
        let n = ell_max + 1;
        for i in 0..n*n {
            assert!((flrw[i] - bianchi_zero[i]).abs() < 1e-15,
                "Mismatch at [{},{}]: flrw={:.6e}, bianchi(σ=0)={:.6e}",
                i/n, i%n, flrw[i], bianchi_zero[i]);
        }
    }

    /// Coupling coefficients match pstf/coupling.rs values.
    #[test]
    fn test_coupling_coefficients() {
        let bg = bianchi_bg(1.0, 1.0); // k=1, σ=1 for easy coefficient reading
        let ell_max = 6;
        let mat = build_species_streaming_matrix(&bg, ell_max, false, false);
        let n = ell_max + 1;

        // Check ℓ=2 ← ℓ=0 shear coupling: β₂^{down} = 2×1/(3×5) = 2/15
        let expected = coupling::shear_coupling_down(2);
        let actual = mat[2 * n + 0]; // row=2, col=0
        assert!((actual - expected).abs() < 1e-14,
            "Shear ℓ=0→2: expected {:.6}, got {:.6}", expected, actual);

        // Check ℓ=0 ← ℓ=2 shear coupling: −β₀^{up} = −(1×2)/(1×3) = −2/3
        let expected_up = -coupling::shear_coupling_up(0);
        let actual_up = mat[0 * n + 2];
        assert!((actual_up - expected_up).abs() < 1e-14,
            "Shear ℓ=2→0: expected {:.6}, got {:.6}", expected_up, actual_up);
    }

    /// Thomson collision only affects ℓ ≥ 2.
    #[test]
    fn test_collision_ell_ge_2() {
        let bg = flrw_bg(0.01);
        let mat = build_species_streaming_matrix(&bg, 6, true, false);
        let n = 7;
        // ℓ=0, ℓ=1 diagonal should be 0 (no collision)
        assert_eq!(mat[0 * n + 0], 0.0, "ℓ=0 diagonal should be 0");
        assert_eq!(mat[1 * n + 1], 0.0, "ℓ=1 diagonal should be 0");
        // ℓ=2 diagonal should be −κ̇
        assert!((mat[2 * n + 2] + bg.kappa_dot).abs() < 1e-10,
            "ℓ=2 diagonal should be −κ̇, got {}", mat[2 * n + 2]);
    }

    /// Neutrino block: no collision.
    #[test]
    fn test_neutrino_no_collision() {
        let bg = flrw_bg(0.01);
        let mat = build_species_streaming_matrix(&bg, 6, false, false);
        let n = 7;
        for ell in 0..=6 {
            assert_eq!(mat[ell * n + ell], 0.0, "Neutrino ℓ={} diagonal should be 0", ell);
        }
    }

    /// Shear coupling scales linearly with σ.
    #[test]
    fn test_shear_scaling() {
        let ell_max = 6;
        let mat1 = build_species_streaming_matrix(&bianchi_bg(0.01, 1e-3), ell_max, false, false);
        let mat2 = build_species_streaming_matrix(&bianchi_bg(0.01, 2e-3), ell_max, false, false);
        let n = ell_max + 1;
        // Off-diagonal ℓ↔ℓ±2 entries should scale by factor 2
        let entry1 = mat1[2 * n + 0]; // ℓ=0→2 shear
        let entry2 = mat2[2 * n + 0];
        let ratio = entry2 / entry1;
        assert!((ratio - 2.0).abs() < 1e-12, "Shear scaling: expected 2.0, got {:.6}", ratio);
    }
}
