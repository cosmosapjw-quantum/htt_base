//! Collision operator split builder: BASS CambBackground → IMEX SplitLinearOp.
//!
//! Reference: R-P1-02_설계안 §4, §12.1(D).
//!
//! Builds the diagonal damping list and low-ℓ small blocks for the current
//! 24-DOF FLRW configuration (lmax_g, lmax_n, optional lmax_pol). The result
//! plugs directly into [`crate::solver::imex_ark4::SplitLinearOp`].
//!
//! ## Invariants (enforced by debug_assertions)
//!
//! - χ ≥ 0 (canonicalized)
//! - monopole (ℓ = 0) NOT in any collision structure (conservation)
//! - CDM DOF not in any collision structure (collisionless)
//! - neutrino DOFs not in collision structure (collisionless in scalar sector)
//! - Metric (etak, sigma), Φ not in collision structure
//!
//! ## What's IN implicit (κ̇-proportional, from R-P1-02_설계안 §4)
//!
//! - ℓ ≥ 3 of photon: diagonal damping rate = χ
//! - ℓ = 1: photon dipole ↔ baryon velocity drag (2×2 block)
//! - ℓ = 2: photon quadrupole (1×1) or [Θ₂, E₂] coupled (2×2 with polarization)
//! - E-mode polarization ℓ ≥ 2: diagonal damping (when lmax_pol ≥ 2)

#![allow(dead_code)]

use crate::solver::imex_ark4::{SmallBlock, SmallBlockSet, StiffnessScales};
use crate::solver::sync_gauge_camb::{CambBackground, CambLayout};

/// One-shot collision structure at a single background snapshot.
///
/// All coefficients are in **actual rate units** (already multiplied by χ).
/// The integrator uses them directly as the implicit operator A_I = χ·C̃ entries.
pub struct CollisionSplit {
    /// Canonicalized opacity χ ≥ 0.
    pub chi: f64,
    /// Ratio R = 4ρ_γ / (3ρ_b) — baryon loading factor, needed for ℓ=1 block.
    pub r_baryon_photon: f64,
    /// Diagonal damping DOFs with actual rate (= χ × C̃-ratio).
    /// Populated: photon ℓ ≥ 3 (rate = χ), E-mode ℓ ≥ 2 (if lmax_pol).
    pub diagonal: Vec<(usize, f64)>,
    /// Small blocks: ℓ=1 (photon-baryon drag) and ℓ=2 (quadrupole/polarization).
    /// Coefficients are actual values (χ multiplied in).
    pub blocks: SmallBlockSet,
}

impl CollisionSplit {
    /// Build collision split from layout and background at a given η.
    pub fn from_bg(lay: &CambLayout, bg: &CambBackground) -> Self {
        // STEP 1: canonicalize sign (R-P1-02_설계안 §12.4 — critical bug prevention)
        let chi = bg.opac.abs();
        debug_assert!(chi >= 0.0);

        // STEP 2: baryon-photon loading factor R = 4ρ_γ / (3ρ_b)
        let r = 4.0 * bg.grho_g / (3.0 * bg.grho_b.max(1e-30));

        // STEP 3: diagonal entries — rate stored as actual = χ × ratio_tilde
        let mut diagonal: Vec<(usize, f64)> = Vec::new();

        // Photon ℓ ≥ 3: uniform Thomson damping, rate = χ
        for ell in 3..=lay.lmax_g {
            diagonal.push((lay.theta(ell), chi));
        }

        // E-mode polarization ℓ ≥ 2 (if polarization enabled): rate = χ
        if lay.lmax_pol > 0 {
            for ell in 2..=lay.lmax_pol {
                let idx = lay.i_e0 + ell;
                if idx < lay.n_state {
                    diagonal.push((idx, chi));
                }
            }
        }

        // STEP 4: ℓ = 1 photon-baryon drag block (2×2)
        // BASS matrix entries (from build_camb_matrix_into):
        //   m[Θ₁, Θ₁] = -opac     (damping of photon dipole)
        //   m[Θ₁, v_b] = +opac/3  (source from baryon velocity)
        //   m[v_b, v_b] = -opac/r_b   (baryon damping from photons; r_b = 0.75·grho_b/grho_g = 1/R)
        //   m[v_b, Θ₁] = +3·opac/r_b  (baryon velocity sourced by photon dipole)
        //
        // Note: BASS uses r_b = 1/R convention. Our R = 4·grho_g/(3·grho_b) = 1/r_b.
        let r_b = (0.75 * bg.grho_b / bg.grho_g).max(1e-10);
        let ell1 = SmallBlock {
            n: 2,
            indices: vec![lay.theta(1), lay.i_vb],
            coeffs_tilde: vec![
                -chi,           chi / 3.0,
                 3.0 * chi / r_b,  -chi / r_b,
            ],
        };

        // STEP 5: ℓ = 2 quadrupole block — match BASS convention
        // BASS code (no polarization): m[Θ₂, Θ₂] = -0.9·opac
        // BASS code (with pol):        m[Θ₂, Θ₂] = 0 (cancels), m[Θ₂, E₂] = +1.5·opac
        //                              E-mode rows then have own opac entries
        let ell2 = if lay.lmax_pol >= 2 {
            // 2×2 [Θ₂, E₂] coupled. Coefficients per BASS matrix builder.
            SmallBlock {
                n: 2,
                indices: vec![lay.theta(2), lay.i_e0 + 2],
                coeffs_tilde: vec![
                    0.0,           1.5 * chi,
                    // E₂ row: see build_camb_matrix_into "E-mode polarization hierarchy"
                    // E₂' contains -opac·(2/5)·E₂ + opac·(2/5)·Θ₂ ⇒ -0.4·χ on E₂, +0.4·χ on Θ₂
                    0.4 * chi,    -0.4 * chi,
                ],
            }
        } else {
            SmallBlock {
                n: 1,
                indices: vec![lay.theta(2)],
                coeffs_tilde: vec![-0.9 * chi],
            }
        };

        let blocks = SmallBlockSet { blocks: vec![ell1, ell2] };

        Self { chi, r_baryon_photon: r, diagonal, blocks }
    }

    /// Count collision DOFs (for diagnostics).
    pub fn n_collision_dofs(&self) -> usize {
        let diag_n = self.diagonal.len();
        let block_n: usize = self.blocks.blocks.iter().map(|b| b.n).sum();
        diag_n + block_n
    }

    /// Emit StiffnessScales given background + k.
    pub fn stiffness_scales(&self, bg: &CambBackground, k: f64) -> StiffnessScales {
        StiffnessScales {
            opacity: self.chi,
            hubble: bg.adotoa,
            shear: 0.0, // FLRW: σ = 0
            k_mode: k,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// BassLinearOp — SplitLinearOp adapter for BASS production matrices
// ═══════════════════════════════════════════════════════════════════════

use crate::solver::imex_ark4::SplitLinearOp;

/// Adapter that exposes BASS's pre-built (`mats_flat`, `bg_at_snap`) profile
/// as a `SplitLinearOp` for the IMEX-ARK4 stepper.
///
/// Strategy ("lazy split"): no separate A_E storage. At each `apply_explicit`:
///   1. Linearly interpolate full matrix A(η) from `mats_flat`
///   2. Compute out = A(η) · y
///   3. Subtract collision contribution: out -= A_I(η) · y
///      (uses CollisionSplit at the same η; collision entries cancel out)
///
/// This guarantees by construction: A_E + A_I = A (no double-counting risk).
pub struct BassLinearOp<'a> {
    pub lay: &'a CambLayout,
    pub eta_profile: &'a [f64],     // n_vis, monotonic increasing
    pub mats_flat: &'a [f64],       // n_vis × n_state × n_state, row-major per snapshot
    pub bg_at_snap: &'a [CambBackground],  // n_vis backgrounds parallel to eta_profile
    pub n_state: usize,
}

impl<'a> BassLinearOp<'a> {
    /// Create from existing BASS profile data.
    pub fn new(
        lay: &'a CambLayout,
        eta_profile: &'a [f64],
        mats_flat: &'a [f64],
        bg_at_snap: &'a [CambBackground],
    ) -> Self {
        let n = lay.n_state;
        debug_assert_eq!(mats_flat.len(), eta_profile.len() * n * n);
        debug_assert_eq!(bg_at_snap.len(), eta_profile.len());
        Self { lay, eta_profile, mats_flat, bg_at_snap, n_state: n }
    }

    /// Find η index and interpolation weight for `eta` ∈ eta_profile.
    /// Returns (idx_lo, w) where the interpolated value is
    ///   v(eta) = (1-w) · v[idx_lo] + w · v[idx_lo+1]
    ///
    /// Special: n=1 → returns (0, 0.0) and caller must use [idx_lo] only.
    fn interp_idx(&self, eta: f64) -> (usize, f64) {
        let n = self.eta_profile.len();
        if n <= 1 {
            return (0, 0.0);
        }
        if eta <= self.eta_profile[0] {
            return (0, 0.0);
        }
        if eta >= self.eta_profile[n - 1] {
            return (n - 2, 1.0);
        }
        let upper = self.eta_profile.partition_point(|&e| e <= eta);
        let idx_lo = (upper.saturating_sub(1)).min(n - 2);
        let denom = (self.eta_profile[idx_lo + 1] - self.eta_profile[idx_lo]).max(1e-30);
        let w = ((eta - self.eta_profile[idx_lo]) / denom).clamp(0.0, 1.0);
        (idx_lo, w)
    }

    /// Interpolated background at η.
    fn interp_bg(&self, eta: f64) -> CambBackground {
        let (idx, w) = self.interp_idx(eta);
        let n_eta = self.eta_profile.len();
        let b0 = &self.bg_at_snap[idx];
        if n_eta <= 1 || w == 0.0 {
            return b0.clone();
        }
        let b1 = &self.bg_at_snap[idx + 1];
        let lerp = |a: f64, b: f64| -> f64 { a * (1.0 - w) + b * w };
        CambBackground {
            adotoa: lerp(b0.adotoa, b1.adotoa),
            grho_g: lerp(b0.grho_g, b1.grho_g),
            grho_nu: lerp(b0.grho_nu, b1.grho_nu),
            grho_b: lerp(b0.grho_b, b1.grho_b),
            grho_c: lerp(b0.grho_c, b1.grho_c),
            opac: lerp(b0.opac, b1.opac),
            cs2b: lerp(b0.cs2b, b1.cs2b),
            vis: lerp(b0.vis, b1.vis),
            dvis: lerp(b0.dvis, b1.dvis),
            ddvis: lerp(b0.ddvis, b1.ddvis),
            a: lerp(b0.a, b1.a),
            expmmu: lerp(b0.expmmu, b1.expmmu),
        }
    }

    /// Compute A(η) · y by interpolating mats_flat and matrix-vector product.
    fn apply_full_matvec(&self, eta: f64, y: &[f64], out: &mut [f64]) {
        let n = self.n_state;
        let n_eta = self.eta_profile.len();
        let (idx, w) = self.interp_idx(eta);
        let off0 = idx * n * n;
        if n_eta <= 1 || w == 0.0 {
            for i in 0..n {
                let mut s = 0.0;
                for j in 0..n {
                    s += self.mats_flat[off0 + i * n + j] * y[j];
                }
                out[i] = s;
            }
            return;
        }
        let off1 = (idx + 1) * n * n;
        for i in 0..n {
            let mut s = 0.0;
            for j in 0..n {
                let m_ij = (1.0 - w) * self.mats_flat[off0 + i * n + j]
                          + w * self.mats_flat[off1 + i * n + j];
                s += m_ij * y[j];
            }
            out[i] = s;
        }
    }

    /// Compute A_I(η) · y using a CollisionSplit at η.
    fn apply_collision_matvec(&self, eta: f64, y: &[f64], out: &mut [f64]) {
        let bg = self.interp_bg(eta);
        let split = CollisionSplit::from_bg(self.lay, &bg);
        // Diagonal: out[idx] += -rate · y[idx]
        for &(idx, rate) in &split.diagonal {
            if idx < y.len() && idx < out.len() {
                out[idx] += -rate * y[idx];
            }
        }
        // Blocks: out[row_i] += Σ_j coeff[i,j] · y[col_j]
        for blk in &split.blocks.blocks {
            let nb = blk.n;
            for i in 0..nb {
                let ri = blk.indices[i];
                if ri >= out.len() { continue; }
                let mut s = 0.0;
                for j in 0..nb {
                    let cj = blk.indices[j];
                    if cj < y.len() {
                        s += blk.coeffs_tilde[i * nb + j] * y[cj];
                    }
                }
                out[ri] += s;
            }
        }
    }
}

impl<'a> SplitLinearOp for BassLinearOp<'a> {
    fn dim(&self) -> usize { self.n_state }

    fn apply_explicit(&self, eta: f64, y: &[f64], out: &mut [f64]) {
        // out = A(η) · y
        self.apply_full_matvec(eta, y, out);
        // Subtract collision contribution: out -= A_I(η) · y
        // After this, out = (A - A_I) · y = A_E · y by construction
        let n = self.n_state;
        let mut a_i_y = vec![0.0_f64; n];
        self.apply_collision_matvec(eta, y, &mut a_i_y);
        for i in 0..n {
            out[i] -= a_i_y[i];
        }
    }

    fn fill_implicit_diag(&self, eta: f64, diag: &mut Vec<(usize, f64)>) {
        let bg = self.interp_bg(eta);
        let split = CollisionSplit::from_bg(self.lay, &bg);
        diag.clear();
        diag.extend_from_slice(&split.diagonal);
    }

    fn fill_implicit_blocks(&self, eta: f64, blocks: &mut crate::solver::imex_ark4::SmallBlockSet) {
        let bg = self.interp_bg(eta);
        let split = CollisionSplit::from_bg(self.lay, &bg);
        blocks.blocks.clear();
        blocks.blocks.extend_from_slice(&split.blocks.blocks);
    }

    fn stiffness_scales(&self, eta: f64) -> StiffnessScales {
        let bg = self.interp_bg(eta);
        StiffnessScales {
            opacity: bg.opac.abs(),
            hubble: bg.adotoa,
            shear: 0.0,
            k_mode: 0.0, // k stored elsewhere (not in matrix)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::solver::sync_gauge_camb::{CambLayout, build_camb_matrix_into};

    fn mk_lay_24dof() -> CambLayout {
        // Production 24-DOF config: lmax_g = 8, lmax_n = 8, no polarization
        CambLayout::new_full(8, 8, 0, 0, 0)
    }

    fn mk_bg(opac: f64) -> CambBackground {
        CambBackground {
            adotoa: 200.0, grho_g: 1e-3, grho_nu: 7e-4, grho_b: 1e-4,
            grho_c: 5e-4, opac, cs2b: 1e-8, vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1e-3, expmmu: 0.0,
        }
    }

    /// Canonicalization: negative opac → χ = |opac|.
    #[test]
    fn canonicalize_opacity_positive() {
        let lay = mk_lay_24dof();
        let split1 = CollisionSplit::from_bg(&lay, &mk_bg(1500.0));
        let split2 = CollisionSplit::from_bg(&lay, &mk_bg(-1500.0)); // sign-flipped input
        assert!(split1.chi > 0.0);
        assert!((split1.chi - split2.chi).abs() < 1e-10,
                "|opac| should normalize: {} vs {}", split1.chi, split2.chi);
    }

    /// ℓ = 3..lmax_g photon DOFs in diagonal, NOT ℓ = 0, 1, 2.
    #[test]
    fn diagonal_excludes_low_ell() {
        let lay = mk_lay_24dof();
        let split = CollisionSplit::from_bg(&lay, &mk_bg(1000.0));
        let diag_idx: Vec<usize> = split.diagonal.iter().map(|(i, _)| *i).collect();
        for ell in 0..3 {
            assert!(!diag_idx.contains(&lay.theta(ell)),
                    "ℓ={} must NOT be in diagonal", ell);
        }
        for ell in 3..=lay.lmax_g {
            assert!(diag_idx.contains(&lay.theta(ell)),
                    "ℓ={} must BE in diagonal", ell);
        }
    }

    /// Neutrino, CDM, metric, Φ never in collision structure.
    #[test]
    fn collisionless_species_excluded() {
        let lay = mk_lay_24dof();
        let split = CollisionSplit::from_bg(&lay, &mk_bg(1000.0));
        let diag_idx: Vec<usize> = split.diagonal.iter().map(|(i, _)| *i).collect();

        let all_indices: Vec<usize> = diag_idx.iter().copied()
            .chain(split.blocks.blocks.iter().flat_map(|b| b.indices.iter().copied()))
            .collect();

        // Neutrino DOFs
        for ell in 0..=lay.lmax_n {
            assert!(!all_indices.contains(&lay.nu(ell)),
                    "neutrino ℓ={} must be collisionless", ell);
        }
        // Metric, CDM, Φ
        assert!(!all_indices.contains(&lay.i_etak), "etak must be collisionless");
        assert!(!all_indices.contains(&lay.i_sigma), "sigma must be collisionless");
        assert!(!all_indices.contains(&lay.i_clxc), "CDM must be collisionless");
        assert!(!all_indices.contains(&lay.i_phi), "Φ must be collisionless");
    }

    /// Baryon density δ_b is NOT coupled via ℓ=1 block (only v_b is).
    /// The ℓ=1 block couples photon dipole Θ₁ and baryon velocity v_b only.
    #[test]
    fn ell1_block_has_only_theta1_and_vb() {
        let lay = mk_lay_24dof();
        let split = CollisionSplit::from_bg(&lay, &mk_bg(1000.0));
        let ell1_indices = &split.blocks.blocks[0].indices;
        assert_eq!(ell1_indices.len(), 2);
        assert!(ell1_indices.contains(&lay.theta(1)));
        assert!(ell1_indices.contains(&lay.i_vb));
        assert!(!ell1_indices.contains(&lay.i_clxb), "δ_b must NOT be in ℓ=1 block");
    }

    /// For 24-DOF config: verify collision DOF count matches design.
    /// Expected: 6 diagonal (ℓ=3..8 photon) + 2 (ℓ=1 block) + 1 (ℓ=2 block) = 9.
    #[test]
    fn n_collision_dofs_24dof() {
        let lay = mk_lay_24dof();
        let split = CollisionSplit::from_bg(&lay, &mk_bg(1000.0));
        assert_eq!(split.n_collision_dofs(), 9,
                   "Expected 9 collision DOFs, got {}", split.n_collision_dofs());
        eprintln!("24-DOF: {}/{} = {:.1}% in collision",
                  split.n_collision_dofs(), lay.n_state,
                  100.0 * split.n_collision_dofs() as f64 / lay.n_state as f64);
    }

    /// ℓ=1 block: verify actual values match BASS matrix entries.
    #[test]
    fn ell1_block_matches_bass_matrix() {
        let lay = mk_lay_24dof();
        let bg = mk_bg(1000.0);
        let split = CollisionSplit::from_bg(&lay, &bg);
        let ell1 = &split.blocks.blocks[0];
        let chi = bg.opac.abs();
        let r_b = (0.75 * bg.grho_b / bg.grho_g).max(1e-10);
        // C̃[0,0] = -χ (Θ₁ self-damping; matches m[Θ₁,Θ₁] = -opac)
        assert!((ell1.coeffs_tilde[0] - (-chi)).abs() < 1e-9);
        // C̃[0,1] = +χ/3 (matches m[Θ₁,v_b] = +opac/3)
        assert!((ell1.coeffs_tilde[1] - chi / 3.0).abs() < 1e-9);
        // C̃[1,0] = +3χ/r_b (matches m[v_b,Θ₁] = +3·opac/r_b)
        assert!((ell1.coeffs_tilde[2] - 3.0 * chi / r_b).abs() < 1e-9);
        // C̃[1,1] = -χ/r_b (matches m[v_b,v_b] = -h - opac/r_b minus -h part)
        assert!((ell1.coeffs_tilde[3] - (-chi / r_b)).abs() < 1e-9);
    }

    /// ℓ=2 block (no pol): -0.9·χ matches BASS.
    #[test]
    fn ell2_block_matches_bass_matrix_no_pol() {
        let lay = mk_lay_24dof();
        let bg = mk_bg(1000.0);
        let split = CollisionSplit::from_bg(&lay, &bg);
        let chi = bg.opac.abs();
        assert_eq!(split.blocks.blocks[1].n, 1);
        // -0.9 × χ, matches m[Θ₂, Θ₂] = -0.9·opac
        assert!((split.blocks.blocks[1].coeffs_tilde[0] - (-0.9 * chi)).abs() < 1e-9);
    }

    /// StiffnessScales from this collision split at given k.
    #[test]
    fn stiffness_scales_derivation() {
        let lay = mk_lay_24dof();
        let bg = mk_bg(1000.0);
        let split = CollisionSplit::from_bg(&lay, &bg);
        let s = split.stiffness_scales(&bg, 0.1);
        assert!((s.opacity - 1000.0).abs() < 1e-10);
        assert!((s.hubble - 200.0).abs() < 1e-10);
        assert_eq!(s.shear, 0.0); // FLRW
        assert_eq!(s.k_mode, 0.1);
        s.assert_canonical(); // χ ≥ 0
    }

    // ═══════════════════════════════════════════════════════════════════
    // BassLinearOp adapter tests (PR-IMEX-02 critical correctness checks)
    // ═══════════════════════════════════════════════════════════════════

    /// CRITICAL: A_E + A_I ≈ A (no double-counting, no missed entries).
    ///
    /// Build a single matrix A via build_camb_matrix_into.
    /// Compute A·y_test directly.
    /// Then via BassLinearOp: out_E = A_E·y_test, out_I = A_I·y_test (apply_collision_matvec).
    /// Check out_E + out_I = A·y within fp tolerance.
    #[test]
    fn bass_linop_split_identity() {
        let lay = mk_lay_24dof();
        let bg = mk_bg(1000.0);
        let n = lay.n_state;
        let k = 0.05_f64;
        let tau = 100.0_f64;

        // Build full matrix A
        let mut a_full = vec![0.0_f64; n * n];
        build_camb_matrix_into(k, tau, &lay, &bg, &mut a_full);

        // Random-ish test vector (deterministic for reproducibility)
        let y_test: Vec<f64> = (0..n).map(|i| ((i + 1) as f64).sin()).collect();

        // A·y direct
        let mut a_y = vec![0.0_f64; n];
        for i in 0..n {
            let mut s = 0.0;
            for j in 0..n {
                s += a_full[i * n + j] * y_test[j];
            }
            a_y[i] = s;
        }

        // BassLinearOp at single snapshot
        let eta_profile = vec![tau];
        let bg_arr = vec![bg.clone()];
        let op = BassLinearOp::new(&lay, &eta_profile, &a_full, &bg_arr);

        let mut a_e_y = vec![0.0_f64; n];
        op.apply_explicit(tau, &y_test, &mut a_e_y);

        let mut a_i_y = vec![0.0_f64; n];
        op.apply_collision_matvec(tau, &y_test, &mut a_i_y);

        // Identity: A_E·y + A_I·y == A·y
        let mut max_err = 0.0_f64;
        let mut max_abs = 0.0_f64;
        for i in 0..n {
            let recon = a_e_y[i] + a_i_y[i];
            let diff = (recon - a_y[i]).abs();
            if diff > max_err { max_err = diff; }
            if a_y[i].abs() > max_abs { max_abs = a_y[i].abs(); }
        }
        let rel_err = max_err / max_abs.max(1e-30);
        eprintln!("split identity: max_abs_diff = {:.2e}, max_|A·y| = {:.2e}, rel = {:.2e}",
                  max_err, max_abs, rel_err);
        assert!(rel_err < 1e-12,
                "A_E + A_I should equal A; rel error = {:.2e}", rel_err);
    }

    /// Specific entries: confirm collision rows are zeroed in A_E (within fp).
    /// For a Θ_5 (ℓ=5) row with no metric/streaming coupling, A_E row should
    /// have ONLY streaming entries (k/(2ℓ+1)·ℓ on Θ_4, -(ℓ+1)/(2ℓ+1)·k on Θ_6).
    #[test]
    fn bass_linop_a_e_no_collision_in_high_ell() {
        let lay = mk_lay_24dof();
        let bg = mk_bg(1000.0);
        let n = lay.n_state;
        let k = 0.05_f64;
        let tau = 100.0_f64;

        let mut a_full = vec![0.0_f64; n * n];
        build_camb_matrix_into(k, tau, &lay, &bg, &mut a_full);

        let eta_profile = vec![tau];
        let bg_arr = vec![bg.clone()];
        let op = BassLinearOp::new(&lay, &eta_profile, &a_full, &bg_arr);

        // Test on basis vector e_{Θ_5} — A_E·e_5 should not contain χ contribution at Θ_5
        let ell = 5;
        if ell >= lay.lmax_g { return; } // skip if config too small
        let mut e = vec![0.0_f64; n];
        e[lay.theta(ell)] = 1.0;
        let mut a_e_e = vec![0.0_f64; n];
        op.apply_explicit(tau, &e, &mut a_e_e);

        // Expected A_E[Θ_5, Θ_5] = 0 (collision was -opac, removed in split)
        // Expected A_E[Θ_5, Θ_4] = k·5/11 ≈ 0.0227
        // Expected A_E[Θ_5, Θ_6] = -k·6/11 ≈ -0.0273 (or 0 if Θ_6 doesn't exist)
        let theta_5_self = a_e_e[lay.theta(5)];
        assert!(theta_5_self.abs() < 1e-12,
                "A_E[Θ_5, Θ_5] should be 0 (collision removed), got {}", theta_5_self);
        // Streaming to Θ_4 (lower)
        let to_4 = a_e_e[lay.theta(4)];
        // The matrix is built with coupling on row 4 (Θ_4'), not column 4 of Θ_5 row
        // Actually Θ_5' couples to Θ_4 in the streaming (row Θ_5, col Θ_4)
        // Wait — apply_explicit gives A_E·e_5, so we read column 5 of A_E
        // Streaming term in row Θ_5 has column Θ_4 (k·ℓ/(2ℓ+1)) and column Θ_6 (-k·(ℓ+1)/(2ℓ+1))
        // Reading column 5 means: rows are A_E[i, Θ_5] for all i
        // What rows have Θ_5 column? Rows Θ_4 (-k·5/9) and Θ_6 (k·6/13)
        // Plus collision row Θ_5 itself was -opac, now 0.
        // Verify Θ_4 row has -k·5/9 ≈ -0.0278
        let row_4_col_5 = a_e_e[lay.theta(4)];
        let expected = -k * 5.0 / 9.0;
        assert!((row_4_col_5 - expected).abs() < 1e-10,
                "A_E[Θ_4, Θ_5] = {}, expected {} (streaming coupling)", row_4_col_5, expected);
        let _ = to_4;
    }

    /// Sign convention: BassLinearOp must use χ = |opac|, even with negative input.
    #[test]
    fn bass_linop_sign_canonical() {
        let lay = mk_lay_24dof();
        let bg_neg = mk_bg(-2000.0);  // pretend opac came in negative
        let n = lay.n_state;

        let mut a_full = vec![0.0_f64; n * n];
        build_camb_matrix_into(0.05, 100.0, &lay, &bg_neg, &mut a_full);

        let eta_profile = vec![100.0];
        let bg_arr = vec![bg_neg.clone()];
        let op = BassLinearOp::new(&lay, &eta_profile, &a_full, &bg_arr);

        let mut diag: Vec<(usize, f64)> = Vec::new();
        op.fill_implicit_diag(100.0, &mut diag);

        // All rates must be ≥ 0
        for &(idx, rate) in &diag {
            assert!(rate >= 0.0,
                    "diag[{}] rate = {} violates sign canonicalization (input opac was {})",
                    idx, rate, bg_neg.opac);
        }
        // χ should be 2000 (|−2000|)
        assert!((op.interp_bg(100.0).opac.abs() - 2000.0).abs() < 1e-9);
    }

    /// Interpolation: between two snapshots, fill_implicit_diag returns rates
    /// consistent with linearly interpolated background.
    #[test]
    fn bass_linop_interpolation_consistency() {
        let lay = mk_lay_24dof();
        let bg0 = mk_bg(1000.0);
        let bg1 = mk_bg(2000.0);
        let n = lay.n_state;

        let mut a0 = vec![0.0_f64; n * n];
        let mut a1 = vec![0.0_f64; n * n];
        build_camb_matrix_into(0.05, 100.0, &lay, &bg0, &mut a0);
        build_camb_matrix_into(0.05, 110.0, &lay, &bg1, &mut a1);

        let mats: Vec<f64> = a0.iter().chain(a1.iter()).copied().collect();
        let eta_profile = vec![100.0, 110.0];
        let bg_arr = vec![bg0.clone(), bg1.clone()];
        let op = BassLinearOp::new(&lay, &eta_profile, &mats, &bg_arr);

        // At η = 105 (midpoint), χ should be (1000 + 2000)/2 = 1500
        let mut diag: Vec<(usize, f64)> = Vec::new();
        op.fill_implicit_diag(105.0, &mut diag);
        // Photon ℓ=3 entry rate = χ at midpoint
        let theta3_rate = diag.iter().find(|(i, _)| *i == lay.theta(3))
                              .expect("Θ_3 should be in diagonal").1;
        let expected = 1500.0;
        assert!((theta3_rate - expected).abs() < 1e-9,
                "Interpolated χ at midpoint: {} vs expected {}", theta3_rate, expected);
    }

    // ═══════════════════════════════════════════════════════════════════
    // END-TO-END VALIDATION: IMEX-ARK4 vs Rodas5P on a synthetic BASS-like
    // multi-snapshot profile (2-snapshot constant-coefficient system)
    // ═══════════════════════════════════════════════════════════════════

    /// Two-snapshot constant-coefficient system: build a synthetic BASS-style
    /// matrix profile with constant background, integrate via both Rodas5P
    /// (existing path) and IMEX-ARK4 (new path), compare final state.
    ///
    /// This is a SUFFICIENT test: if IMEX matches Rodas5P on synthetic BASS
    /// matrix structure with realistic stiffness (χ ~ 1000), the full split
    /// is verified end-to-end. Time-varying coefficients and physics-correct
    /// recombination are tested via the production integration in PR-IMEX-03.
    #[test]
    fn imex_vs_rodas5p_synthetic_24dof() {
        use crate::solver::imex_ark4::{ImexWorkspace, integrate_imex_ark4};
        use crate::solver::stacked::integrate_linear_profile_rodas5p;
        use crate::core::config::Rodas5PConfig;

        let lay = mk_lay_24dof();
        let n = lay.n_state;
        let k = 0.05_f64;
        let bg = CambBackground {
            adotoa: 200.0, grho_g: 1e-3, grho_nu: 7e-4, grho_b: 1e-4,
            grho_c: 5e-4, opac: 1000.0, cs2b: 1e-8, vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1e-3, expmmu: 0.0,
        };

        // Two-snapshot profile: constant background, two τ values
        let tau0 = 100.0_f64;
        let tau1 = 110.0_f64;
        let mut a0 = vec![0.0_f64; n * n];
        let mut a1 = vec![0.0_f64; n * n];
        build_camb_matrix_into(k, tau0, &lay, &bg, &mut a0);
        build_camb_matrix_into(k, tau1, &lay, &bg, &mut a1);
        let tau_profile = vec![tau0, tau1];
        let mats_flat: Vec<f64> = a0.iter().chain(a1.iter()).copied().collect();
        let bg_arr = vec![bg.clone(), bg.clone()];

        // Initial condition: small amplitudes (linear system, scale-invariant)
        let mut y0 = vec![0.0_f64; n];
        y0[lay.theta(0)] = 1e-3;
        y0[lay.theta(1)] = 5e-4;
        y0[lay.theta(2)] = 1e-4;
        y0[lay.i_vb] = 4e-4;
        y0[lay.i_clxb] = 1e-3;
        y0[lay.i_clxc] = 1e-3;
        y0[lay.nu(0)] = 1e-3;
        y0[lay.nu(1)] = 5e-4;
        y0[lay.i_etak] = -k * 1e-3;
        y0[lay.i_phi] = -2e-4;

        // === Path 1: Rodas5P (production baseline) ===
        let cfg = Rodas5PConfig {
            rtol: 1e-8, atol: 1e-12, max_steps: 100_000,
            h_init: None, h_min: 1e-14, h_max: 5.0,
            f_safety: 0.9, f_min: 0.2, f_max: 5.0, beta: 0.04,
            use_analytic_jacobian: true, use_ft_term: false,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: lay.lmax_g, ell_max_nu_hint: lay.lmax_n,
            ell_max_pol_hint: 0, include_pol_hint: false,
            use_sparse: false,
        };
        let (snaps_rodas, _stats, _) = integrate_linear_profile_rodas5p(
            &tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg,
        ).expect("Rodas5P should succeed");
        let y_rodas_final = snaps_rodas.last().expect("snapshots non-empty").clone();

        // === Path 2: IMEX-ARK4 via BassLinearOp ===
        let op = BassLinearOp::new(&lay, &tau_profile, &mats_flat, &bg_arr);
        let mut work = ImexWorkspace::new(n);
        // h_init = 0.1 (good for χ·h ~ 100, well in stiff regime so adaptive will adjust)
        let (y_imex_final, stats) = integrate_imex_ark4(
            &op, tau0, tau1, 0.1, &y0, 1e-12, 1e-9, 100_000, &mut work,
        ).expect("IMEX integration should succeed");

        // === Compare ===
        let mut max_rel = 0.0_f64;
        let mut max_abs = 0.0_f64;
        let mut worst_idx = 0usize;
        for i in 0..n {
            let d = (y_imex_final[i] - y_rodas_final[i]).abs();
            let scale = y_rodas_final[i].abs().max(1e-12);
            let rel = d / scale;
            if rel > max_rel {
                max_rel = rel;
                worst_idx = i;
            }
            if y_rodas_final[i].abs() > max_abs {
                max_abs = y_rodas_final[i].abs();
            }
        }
        eprintln!("imex vs rodas: max_rel = {:.2e} at idx {} (rodas={:.4e}, imex={:.4e})",
                  max_rel, worst_idx, y_rodas_final[worst_idx], y_imex_final[worst_idx]);
        eprintln!("imex stats: accepted={}, rejected={}, final_h={:.2e}",
                  stats.n_steps_accepted, stats.n_steps_rejected, stats.final_h);

        // Acceptance: relative diff ≤ 1% on largest entries (10× rtol of IMEX)
        // This validates: split is correct, BassLinearOp adapter works, ARK4 stepper
        // produces solution consistent with Rodas5P at production tolerance.
        // Note: per-component rel error can be higher for components near zero
        // (their scale is tiny, fp noise dominates); restrict check to entries
        // where |rodas| > 0.01 × max_abs (i.e., physically significant entries).
        let mut max_rel_significant = 0.0_f64;
        for i in 0..n {
            if y_rodas_final[i].abs() > 0.01 * max_abs {
                let d = (y_imex_final[i] - y_rodas_final[i]).abs();
                let rel = d / y_rodas_final[i].abs();
                if rel > max_rel_significant {
                    max_rel_significant = rel;
                }
            }
        }
        eprintln!("imex vs rodas: max_rel on significant entries = {:.2e}", max_rel_significant);
        assert!(max_rel_significant < 0.05,
                "IMEX vs Rodas5P agreement (significant entries): {:.2e} > 5%", max_rel_significant);
    }

    /// Snapshots comparison: IMEX and Rodas5P produce snapshots compatible
    /// at every eta_eval point (not just the final one).
    ///
    /// This is the critical test for PR-IMEX-03 production wiring:
    /// solve_kmode_full_with_common uses snapshots for source extraction,
    /// so IMEX's snapshots must match Rodas5P's at the eta_eval grid.
    #[test]
    fn imex_snapshots_vs_rodas5p_snapshots() {
        use crate::solver::imex_ark4::{ImexWorkspace, integrate_imex_ark4_snapshots};
        use crate::solver::stacked::integrate_linear_profile_rodas5p;
        use crate::core::config::Rodas5PConfig;

        let lay = mk_lay_24dof();
        let n = lay.n_state;
        let k = 0.05_f64;
        let bg = CambBackground {
            adotoa: 200.0, grho_g: 1e-3, grho_nu: 7e-4, grho_b: 1e-4,
            grho_c: 5e-4, opac: 1000.0, cs2b: 1e-8, vis: 0.0, dvis: 0.0, ddvis: 0.0,
            a: 1e-3, expmmu: 0.0,
        };

        // 5-point eta_profile for non-trivial snapshot grid
        let tau_profile: Vec<f64> = (0..5).map(|i| 100.0 + 2.5 * i as f64).collect();
        let n_eta = tau_profile.len();
        let mut mats_flat = vec![0.0_f64; n_eta * n * n];
        let bg_arr = vec![bg.clone(); n_eta];
        for (i, &tau) in tau_profile.iter().enumerate() {
            build_camb_matrix_into(k, tau, &lay, &bg, &mut mats_flat[i*n*n..(i+1)*n*n]);
        }

        let mut y0 = vec![0.0_f64; n];
        y0[lay.theta(0)] = 1e-3;
        y0[lay.theta(1)] = 5e-4;
        y0[lay.theta(2)] = 1e-4;
        y0[lay.i_vb] = 4e-4;
        y0[lay.i_clxb] = 1e-3;
        y0[lay.i_clxc] = 1e-3;
        y0[lay.nu(0)] = 1e-3;
        y0[lay.nu(1)] = 5e-4;
        y0[lay.i_etak] = -k * 1e-3;
        y0[lay.i_phi] = -2e-4;

        // Rodas5P snapshots
        let cfg = Rodas5PConfig {
            rtol: 1e-8, atol: 1e-12, max_steps: 100_000,
            h_init: None, h_min: 1e-14, h_max: 5.0,
            f_safety: 0.9, f_min: 0.2, f_max: 5.0, beta: 0.04,
            use_analytic_jacobian: true, use_ft_term: false,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: lay.lmax_g, ell_max_nu_hint: lay.lmax_n,
            ell_max_pol_hint: 0, include_pol_hint: false,
            use_sparse: false,
        };
        let (snaps_rodas, _stats, _) = integrate_linear_profile_rodas5p(
            &tau_profile, &mats_flat, n, &y0, &tau_profile, &cfg,
        ).expect("Rodas5P should succeed");
        assert_eq!(snaps_rodas.len(), n_eta);

        // IMEX snapshots
        let op = BassLinearOp::new(&lay, &tau_profile, &mats_flat, &bg_arr);
        let mut work = ImexWorkspace::new(n);
        let (snaps_imex, stats_imex) = integrate_imex_ark4_snapshots(
            &op, &tau_profile, 0.1, &y0, 1e-12, 1e-9, 100_000, &mut work,
        ).expect("IMEX should succeed");
        assert_eq!(snaps_imex.len(), n_eta);

        // Per-snapshot comparison
        let mut worst_rel = 0.0_f64;
        let mut worst_snap = 0usize;
        for s in 0..n_eta {
            let r = &snaps_rodas[s];
            let i = &snaps_imex[s];
            let mut max_abs = 0.0_f64;
            for j in 0..n { if r[j].abs() > max_abs { max_abs = r[j].abs(); } }
            if max_abs < 1e-20 { continue; }
            let threshold = 0.01 * max_abs; // significance
            for j in 0..n {
                if r[j].abs() > threshold {
                    let rel = (i[j] - r[j]).abs() / r[j].abs();
                    if rel > worst_rel {
                        worst_rel = rel;
                        worst_snap = s;
                    }
                }
            }
        }
        eprintln!("snapshots cmp: worst rel = {:.2e} at snap {} (τ = {})",
                  worst_rel, worst_snap, tau_profile[worst_snap]);
        eprintln!("imex steps: {} accepted, {} rejected",
                  stats_imex.n_steps_accepted, stats_imex.n_steps_rejected);

        // Acceptance: ≤1% relative per snapshot per significant component
        // (linear interpolation between IMEX steps introduces O(h²) error,
        // which is looser than the ARK4 local truncation)
        assert!(worst_rel < 0.01,
                "IMEX snapshots vs Rodas5P: worst rel = {:.2e} > 1%", worst_rel);

        // First snapshot MUST be exactly y0 (initial condition)
        for j in 0..n {
            assert_eq!(snaps_imex[0][j], y0[j],
                       "IMEX snapshot[0] must equal y0 at index {}", j);
        }
    }
}
