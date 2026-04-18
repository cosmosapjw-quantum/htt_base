//! (ℓ,m) State Vector Layout — m-MAJOR with contiguous ℓ-runs (P1-01)
//!
//! State ordering designed to minimize memory bandwidth for Bianchi coupling:
//!
//! ```text
//! y = [metric(11) | baryon(4) | CDM(4) |
//!      γ_I(m=-L..L: for each m, ℓ=|m|..L contiguous) |
//!      γ_E(ℓ=max(2,|m|)..L per m) |
//!      γ_B(same as E) |
//!      ν_Θ(m=-L_ν..L_ν: ℓ=|m|..L_ν per m) |
//!      ν_η(same)]
//! ```
//!
//! Why m-major:
//! - Streaming (ℓ±1 at fixed m) → contiguous memory
//! - Axisymmetric shear σ₊ (ℓ±2 at fixed m) → contiguous
//! - Non-axisymmetric shear σ₋ (m±2) → nearby memory blocks

/// Polarization type.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum Pol {
    /// Intensity (Stokes I): ℓ = 0..L
    I,
    /// E-mode polarization: ℓ = 2..L
    E,
    /// B-mode polarization: ℓ = 2..L
    B,
}

/// Species type.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum LmSpecies {
    Photon(Pol),
    NeutrinoTheta,
    NeutrinoEta,
    Baryon,
    Cdm,
    Metric,
}

/// Full (ℓ,m) index for a single DOF.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct LmIndex {
    pub(crate) species: LmSpecies,
    pub(crate) ell: u32,
    pub(crate) m: i32,
}

/// Layout for the full 5566-DOF state vector.
#[derive(Clone, Debug)]
pub(crate) struct LmLayout {
    pub(crate) ell_max_gamma: usize,
    pub(crate) ell_max_nu: usize,
    // Block start offsets
    pub(crate) metric_start: usize,    // 0
    pub(crate) baryon_start: usize,    // 11
    pub(crate) cdm_start: usize,      // 15
    pub(crate) photon_i_start: usize,  // 19
    pub(crate) photon_e_start: usize,
    pub(crate) photon_b_start: usize,
    pub(crate) nu_theta_start: usize,
    pub(crate) nu_eta_start: usize,
    pub(crate) total_dof: usize,
}

impl LmLayout {
    pub(crate) fn new(ell_max_gamma: usize, ell_max_nu: usize) -> Self {
        let lg = ell_max_gamma;
        let ln = ell_max_nu;

        let n_metric = 11;
        let n_baryon = 4;
        let n_cdm = 4;

        // Photon I: ℓ=0..L_γ, m=-ℓ..ℓ → (L_γ+1)²
        let n_photon_i = (lg + 1) * (lg + 1);
        // Photon E: ℓ=2..L_γ, m=-ℓ..ℓ → (L_γ+1)² - 4 (missing ℓ=0: 1 + ℓ=1: 3)
        let n_photon_e = (lg + 1) * (lg + 1) - 4;
        let n_photon_b = n_photon_e;
        // Neutrino: ℓ=0..L_ν, m=-ℓ..ℓ → (L_ν+1)²
        let n_nu_theta = (ln + 1) * (ln + 1);
        let n_nu_eta = n_nu_theta;

        let metric_start = 0;
        let baryon_start = metric_start + n_metric;
        let cdm_start = baryon_start + n_baryon;
        let photon_i_start = cdm_start + n_cdm;
        let photon_e_start = photon_i_start + n_photon_i;
        let photon_b_start = photon_e_start + n_photon_e;
        let nu_theta_start = photon_b_start + n_photon_b;
        let nu_eta_start = nu_theta_start + n_nu_theta;
        let total_dof = nu_eta_start + n_nu_eta;

        Self {
            ell_max_gamma: lg,
            ell_max_nu: ln,
            metric_start, baryon_start, cdm_start,
            photon_i_start, photon_e_start, photon_b_start,
            nu_theta_start, nu_eta_start,
            total_dof,
        }
    }

    /// Convert (ℓ,m) within an (L+1)²-sized block (ℓ_min=0) to flat offset.
    /// m-major: for each m from -L to L, ℓ runs from |m| to L.
    pub(crate) fn lm_offset_full(ell: usize, m: i32, ell_max: usize) -> usize {
        // For m from -L to (m-1), count DOF: Σ_{m'=-L}^{m-1} (L - |m'| + 1)
        let mut offset = 0;
        for mp in -(ell_max as i32)..m {
            offset += ell_max + 1 - mp.unsigned_abs() as usize;
        }
        // Within this m-sector: ℓ runs from |m| to L, current position = ℓ - |m|
        offset + ell - m.unsigned_abs() as usize
    }

    /// Convert (ℓ,m) within a block with ℓ_min=2 to flat offset.
    pub(crate) fn lm_offset_pol(ell: usize, m: i32, ell_max: usize) -> usize {
        let mut offset = 0;
        for mp in -(ell_max as i32)..m {
            let abs_mp = mp.unsigned_abs() as usize;
            let ell_start = abs_mp.max(2);
            if ell_max >= ell_start {
                offset += ell_max - ell_start + 1;
            }
        }
        let ell_start = (m.unsigned_abs() as usize).max(2);
        offset + ell - ell_start
    }

    /// Get flat index for an LmIndex.
    pub(crate) fn flat_index(&self, idx: &LmIndex) -> usize {
        let ell = idx.ell as usize;
        let m = idx.m;
        match idx.species {
            LmSpecies::Metric => {
                assert!(ell == 0 && m == 0, "Metric: only ℓ=0,m=0 components via dedicated slots");
                0 // Individual metric DOF accessed by specific sub-index
            }
            LmSpecies::Baryon => {
                assert!(ell <= 1, "Baryon: δ_b(ℓ=0) + v_b^i(ℓ=1)");
                self.baryon_start + if ell == 0 { 0 } else { 1 + (m + 1) as usize }
            }
            LmSpecies::Cdm => {
                assert!(ell <= 1, "CDM: δ_c(ℓ=0) + v_c^i(ℓ=1)");
                self.cdm_start + if ell == 0 { 0 } else { 1 + (m + 1) as usize }
            }
            LmSpecies::Photon(Pol::I) => {
                self.photon_i_start + Self::lm_offset_full(ell, m, self.ell_max_gamma)
            }
            LmSpecies::Photon(Pol::E) => {
                assert!(ell >= 2, "E-mode starts at ℓ=2");
                self.photon_e_start + Self::lm_offset_pol(ell, m, self.ell_max_gamma)
            }
            LmSpecies::Photon(Pol::B) => {
                assert!(ell >= 2, "B-mode starts at ℓ=2");
                self.photon_b_start + Self::lm_offset_pol(ell, m, self.ell_max_gamma)
            }
            LmSpecies::NeutrinoTheta => {
                self.nu_theta_start + Self::lm_offset_full(ell, m, self.ell_max_nu)
            }
            LmSpecies::NeutrinoEta => {
                self.nu_eta_start + Self::lm_offset_full(ell, m, self.ell_max_nu)
            }
        }
    }

    /// FLRW limit: m=0 only DOF count.
    pub(crate) fn flrw_dof(&self) -> usize {
        let lg = self.ell_max_gamma;
        let ln = self.ell_max_nu;
        // metric(11) + baryon(2: δ_b, v_b^z) + CDM(2) +
        // γ_I(L+1) + γ_E(L-1) + γ_B(L-1) + ν_Θ(L_ν+1) + ν_η(L_ν+1)
        11 + 2 + 2 + (lg + 1) + (lg - 1) + (lg - 1) + (ln + 1) + (ln + 1)
    }

    /// Iterator over all (ℓ,m) indices in a given m-sector for photon I.
    pub(crate) fn photon_i_m_sector(&self, m: i32) -> std::ops::Range<usize> {
        let abs_m = m.unsigned_abs() as usize;
        if abs_m > self.ell_max_gamma { return 0..0; }
        let start = self.photon_i_start
            + Self::lm_offset_full(abs_m, m, self.ell_max_gamma);
        let count = self.ell_max_gamma - abs_m + 1;
        start..(start + count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_total_dof() {
        let lay = LmLayout::new(40, 15);
        assert_eq!(lay.total_dof, 5566);
    }

    #[test]
    fn test_roundtrip_photon_i() {
        let lay = LmLayout::new(40, 15);
        // Check a few specific (ℓ,m) values
        for &(ell, m) in &[(0, 0), (1, 0), (1, -1), (1, 1), (2, 0), (2, 2), (40, 0), (40, -40)] {
            let idx = LmIndex {
                species: LmSpecies::Photon(Pol::I),
                ell, m,
            };
            let flat = lay.flat_index(&idx);
            assert!(flat >= lay.photon_i_start && flat < lay.photon_e_start,
                "Photon I (ℓ={},m={}) → flat={} out of range [{},{})",
                ell, m, flat, lay.photon_i_start, lay.photon_e_start);
        }
    }

    #[test]
    fn test_m_major_locality() {
        let lay = LmLayout::new(40, 15);
        // Adjacent ℓ at same m should be adjacent in memory
        for m in -5_i32..=5 {
            for ell in (m.unsigned_abs() + 1)..10 {
                let idx1 = LmIndex {
                    species: LmSpecies::Photon(Pol::I),
                    ell: ell - 1, m,
                };
                let idx2 = LmIndex {
                    species: LmSpecies::Photon(Pol::I),
                    ell, m,
                };
                let f1 = lay.flat_index(&idx1);
                let f2 = lay.flat_index(&idx2);
                assert_eq!(f2 - f1, 1,
                    "ℓ={},m={}: not contiguous (f1={}, f2={})", ell, m, f1, f2);
            }
        }
    }

    #[test]
    fn test_no_overlap() {
        let lay = LmLayout::new(40, 15);
        assert!(lay.baryon_start == 11);
        assert!(lay.cdm_start == 15);
        assert!(lay.photon_i_start == 19);
        assert!(lay.photon_e_start == 19 + 1681);
        assert!(lay.photon_b_start == lay.photon_e_start + 1677);
        assert!(lay.nu_theta_start == lay.photon_b_start + 1677);
        assert!(lay.nu_eta_start == lay.nu_theta_start + 256);
        assert!(lay.total_dof == lay.nu_eta_start + 256);
    }

    #[test]
    fn test_flrw_dof() {
        let lay = LmLayout::new(40, 15);
        // FLRW m=0: 11 + 2 + 2 + 41 + 39 + 39 + 16 + 16 = 166
        assert_eq!(lay.flrw_dof(), 166);
    }

    #[test]
    fn test_photon_i_m_sector() {
        let lay = LmLayout::new(40, 15);
        // m=0 sector: ℓ=0..40 → 41 DOF
        let range = lay.photon_i_m_sector(0);
        assert_eq!(range.len(), 41);
        // m=40 sector: ℓ=40 only → 1 DOF
        let range = lay.photon_i_m_sector(40);
        assert_eq!(range.len(), 1);
        // m out of range → empty
        let range = lay.photon_i_m_sector(41);
        assert_eq!(range.len(), 0);
    }

    #[test]
    fn test_unique_indices() {
        // Verify no index collision by collecting all photon I indices
        let lay = LmLayout::new(10, 5); // Small layout for speed
        let mut seen = std::collections::HashSet::new();
        let lg = 10_i32;
        for m in -lg..=lg {
            for ell in (m.unsigned_abs())..=10 {
                let idx = LmIndex {
                    species: LmSpecies::Photon(Pol::I),
                    ell, m,
                };
                let flat = lay.flat_index(&idx);
                assert!(seen.insert(flat),
                    "Duplicate flat index {} for (ℓ={},m={})", flat, ell, m);
            }
        }
        assert_eq!(seen.len(), 121); // (10+1)² = 121
    }
}
