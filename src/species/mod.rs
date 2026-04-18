// BD-01: Multi-species state management.
// Species: photon (γ), neutrino (ν), baryon (b), CDM (c), Λ.
// Memory layout: [γ_intensity | γ_E | γ_B | ν₁ | ... | ν_N | b | c]

pub(crate) mod photon;
pub(crate) mod neutrino;
pub(crate) mod baryon;
pub(crate) mod cdm;
pub(crate) mod lambda;

use photon::PhotonState;
use neutrino::NeutrinoState;
use baryon::BaryonState;
use cdm::CDMState;
use lambda::LambdaState;

/// Species configuration parameters.
#[derive(Clone, Debug)]
pub(crate) struct SpeciesConfig {
    /// Photon intensity ℓ_max.
    pub(crate) ell_max_gamma: usize,
    /// Polarisation ℓ_max (E and B modes).
    pub(crate) ell_max_pol: usize,
    /// Neutrino ℓ_max per family.
    pub(crate) ell_max_nu: usize,
    /// Number of massless neutrino families.
    pub(crate) n_nu_families: usize,
    /// Whether to include B-mode polarisation.
    pub(crate) include_b_mode: bool,
}

impl SpeciesConfig {
    /// Minimal ΛCDM configuration matching ET-08 Theorem 2.1.5 scalar version.
    pub(crate) fn minimal() -> Self {
        Self { ell_max_gamma: 10, ell_max_pol: 6, ell_max_nu: 8, n_nu_families: 3, include_b_mode: true }
    }

    /// Production configuration with higher truncation.
    pub(crate) fn production() -> Self {
        Self { ell_max_gamma: 25, ell_max_pol: 8, ell_max_nu: 15, n_nu_families: 3, include_b_mode: true }
    }

    /// DOF for photon intensity: ℓ = 0..ℓ_max_γ.
    pub(crate) fn dof_gamma_intensity(&self) -> usize { self.ell_max_gamma + 1 }

    /// DOF for E-mode: ℓ = 2..ℓ_max_pol.
    pub(crate) fn dof_e_mode(&self) -> usize {
        if self.ell_max_pol >= 2 { self.ell_max_pol - 1 } else { 0 }
    }

    /// DOF for B-mode: same as E-mode.
    pub(crate) fn dof_b_mode(&self) -> usize {
        if self.include_b_mode { self.dof_e_mode() } else { 0 }
    }

    /// DOF per neutrino family: ℓ = 0..ℓ_max_ν.
    pub(crate) fn dof_nu_per_family(&self) -> usize { self.ell_max_nu + 1 }

    /// Total neutrino DOF: n_families × (ℓ_max_ν + 1).
    pub(crate) fn dof_nu_total(&self) -> usize { self.n_nu_families * self.dof_nu_per_family() }

    /// Baryon DOF: 2 (δ_b, v_b).
    pub(crate) fn dof_baryon(&self) -> usize { 2 }

    /// CDM DOF: 2 (δ_c, v_c).
    pub(crate) fn dof_cdm(&self) -> usize { 2 }

    /// Total DOF for the scalar (m=0) stacked state.
    pub(crate) fn total_dof(&self) -> usize {
        self.dof_gamma_intensity() + self.dof_e_mode() + self.dof_b_mode()
            + self.dof_nu_total() + self.dof_baryon() + self.dof_cdm()
    }

    /// Full PSTF DOF (all m modes, for ET-08 comparison).
    /// N_γ = 3L² + 6L - 5 (Theorem 2.1.5)
    pub(crate) fn dof_gamma_pstf(l: usize) -> usize {
        3 * l * l + 6 * l - 5
    }

    /// Full PSTF neutrino DOF: N_ν = 2 + L_Θ² + 2L_Θ + L_η² + 2L_η
    pub(crate) fn dof_nu_pstf(l_theta: usize, l_eta: usize) -> usize {
        2 + l_theta * l_theta + 2 * l_theta + l_eta * l_eta + 2 * l_eta
    }
}

/// Bundle of all species states.
#[derive(Clone, Debug)]
pub(crate) struct SpeciesBundle {
    pub(crate) config: SpeciesConfig,
    pub(crate) photon: PhotonState,
    pub(crate) neutrinos: Vec<NeutrinoState>,
    pub(crate) baryon: BaryonState,
    pub(crate) cdm: CDMState,
    pub(crate) lambda: LambdaState,
}

impl SpeciesBundle {
    /// Create a new bundle with zero initial state.
    pub(crate) fn new(config: SpeciesConfig) -> Self {
        let photon = PhotonState::new(config.ell_max_gamma, config.ell_max_pol, config.include_b_mode);
        let neutrinos: Vec<_> = (0..config.n_nu_families)
            .map(|i| NeutrinoState::new(config.ell_max_nu, i))
            .collect();
        let baryon = BaryonState::new();
        let cdm = CDMState::new();
        let lambda = LambdaState::new(0.685);
        Self { config, photon, neutrinos, baryon, cdm, lambda }
    }

    /// Total DOF.
    pub(crate) fn total_dof(&self) -> usize { self.config.total_dof() }

    /// Serialize to flat state vector.
    pub(crate) fn to_flat(&self) -> Vec<f64> {
        let mut v = Vec::with_capacity(self.total_dof());
        v.extend_from_slice(&self.photon.intensity);
        v.extend_from_slice(&self.photon.e_mode);
        v.extend_from_slice(&self.photon.b_mode);
        for nu in &self.neutrinos { v.extend_from_slice(&nu.hierarchy); }
        v.push(self.baryon.delta_b); v.push(self.baryon.v_b);
        v.push(self.cdm.delta_c); v.push(self.cdm.v_c);
        v
    }

    /// Deserialize from flat state vector.
    pub(crate) fn from_flat(&mut self, v: &[f64]) {
        assert_eq!(v.len(), self.total_dof(), "State vector length mismatch");
        let mut idx = 0;
        let n_int = self.photon.intensity.len();
        self.photon.intensity.copy_from_slice(&v[idx..idx+n_int]); idx += n_int;
        let n_e = self.photon.e_mode.len();
        self.photon.e_mode.copy_from_slice(&v[idx..idx+n_e]); idx += n_e;
        let n_b = self.photon.b_mode.len();
        self.photon.b_mode.copy_from_slice(&v[idx..idx+n_b]); idx += n_b;
        for nu in &mut self.neutrinos {
            let n_nu = nu.hierarchy.len();
            nu.hierarchy.copy_from_slice(&v[idx..idx+n_nu]); idx += n_nu;
        }
        self.baryon.delta_b = v[idx]; self.baryon.v_b = v[idx+1]; idx += 2;
        self.cdm.delta_c = v[idx]; self.cdm.v_c = v[idx+1];
    }

    /// Offset table for each species block in the flat vector.
    pub(crate) fn offsets(&self) -> Vec<(&str, usize, usize)> {
        let mut table = Vec::new();
        let mut off = 0;
        let n = self.photon.intensity.len();
        table.push(("γ_intensity", off, n)); off += n;
        let n = self.photon.e_mode.len();
        table.push(("γ_E", off, n)); off += n;
        let n = self.photon.b_mode.len();
        if n > 0 { table.push(("γ_B", off, n)); off += n; }
        for (i, nu) in self.neutrinos.iter().enumerate() {
            let n = nu.hierarchy.len();
            // Leak-free: use a static string
            let label = match i { 0=>"ν₁", 1=>"ν₂", 2=>"ν₃", _=>"ν_N" };
            table.push((label, off, n)); off += n;
        }
        table.push(("baryon", off, 2)); off += 2;
        table.push(("CDM", off, 2));
        table
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_minimal_dof() {
        let c = SpeciesConfig::minimal();
        // γ_int: 11, γ_E: 5, γ_B: 5, ν: 3×9=27, b: 2, c: 2 → 52
        assert_eq!(c.total_dof(), 11+5+5+27+2+2, "DOF={}", c.total_dof());
    }

    #[test]
    fn test_production_dof() {
        let c = SpeciesConfig::production();
        // γ_int: 26, γ_E: 7, γ_B: 7, ν: 3×16=48, b: 2, c: 2 → 92
        assert_eq!(c.total_dof(), 26+7+7+48+2+2);
    }

    #[test]
    fn test_pstf_gamma_dof_theorem() {
        // ET-08 Theorem 2.1.5: N_γ = 3L² + 6L - 5
        assert_eq!(SpeciesConfig::dof_gamma_pstf(2), 19);
        assert_eq!(SpeciesConfig::dof_gamma_pstf(3), 40);
    }

    #[test]
    fn test_pstf_nu_dof_theorem() {
        // N_ν = 2 + L_Θ² + 2L_Θ + L_η² + 2L_η
        assert_eq!(SpeciesConfig::dof_nu_pstf(2, 1), 13);
    }

    #[test]
    fn test_et08_total_98() {
        // Full PSTF: 18 (geom) + 19 (γ) + 52 (ν) + 4 (b) + 4 (c) + 1 (Λ) = 98
        let n_geom = 18;
        let n_gamma = SpeciesConfig::dof_gamma_pstf(2);
        let n_nu = 4 * SpeciesConfig::dof_nu_pstf(2, 1);
        let n_b = 4; let n_c = 4; let n_l = 1;
        assert_eq!(n_geom + n_gamma + n_nu + n_b + n_c + n_l, 98);
    }

    #[test]
    fn test_bundle_roundtrip() {
        let c = SpeciesConfig::minimal();
        let mut b = SpeciesBundle::new(c);
        b.photon.intensity[0] = 1.0;
        b.photon.intensity[2] = 0.01;
        b.neutrinos[0].hierarchy[0] = 0.5;
        b.baryon.delta_b = -0.01;
        b.cdm.v_c = 0.001;
        let flat = b.to_flat();
        assert_eq!(flat.len(), b.total_dof());
        let mut b2 = SpeciesBundle::new(SpeciesConfig::minimal());
        b2.from_flat(&flat);
        assert_eq!(b2.photon.intensity[0], 1.0);
        assert_eq!(b2.photon.intensity[2], 0.01);
        assert_eq!(b2.neutrinos[0].hierarchy[0], 0.5);
        assert_eq!(b2.baryon.delta_b, -0.01);
        assert_eq!(b2.cdm.v_c, 0.001);
    }

    #[test]
    fn test_offsets_contiguous() {
        let b = SpeciesBundle::new(SpeciesConfig::minimal());
        let offsets = b.offsets();
        let mut expected_off = 0;
        for (name, off, sz) in &offsets {
            assert_eq!(*off, expected_off, "{} offset mismatch", name);
            expected_off += sz;
        }
        assert_eq!(expected_off, b.total_dof());
    }
}
