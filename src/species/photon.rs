// Photon state: intensity F_ℓ + E-mode G_ℓ + B-mode B_ℓ.
// BD-01: scalar (m=0) hierarchy.

#[derive(Clone, Debug)]
pub(crate) struct PhotonState {
    /// Intensity multipoles F₀, F₁, ..., F_{ℓ_max}.
    pub(crate) intensity: Vec<f64>,
    /// E-mode polarisation G₂, G₃, ..., G_{ℓ_pol}.
    pub(crate) e_mode: Vec<f64>,
    /// B-mode polarisation B₂, B₃, ..., B_{ℓ_pol}.
    pub(crate) b_mode: Vec<f64>,
    /// ℓ_max for intensity.
    pub(crate) ell_max: usize,
    /// ℓ_max for polarisation.
    pub(crate) ell_max_pol: usize,
}

impl PhotonState {
    pub(crate) fn new(ell_max: usize, ell_max_pol: usize, include_b: bool) -> Self {
        let n_e = if ell_max_pol >= 2 { ell_max_pol - 1 } else { 0 };
        Self {
            intensity: vec![0.0; ell_max + 1],
            e_mode: vec![0.0; n_e],
            b_mode: if include_b { vec![0.0; n_e] } else { vec![] },
            ell_max, ell_max_pol,
        }
    }

    /// Total DOF.
    pub(crate) fn dof(&self) -> usize {
        self.intensity.len() + self.e_mode.len() + self.b_mode.len()
    }

    /// Set adiabatic IC: F₀ = amplitude, rest = 0.
    pub(crate) fn set_adiabatic(&mut self, f0: f64) {
        self.intensity.fill(0.0); self.intensity[0] = f0;
        self.e_mode.fill(0.0); self.b_mode.fill(0.0);
    }

    /// Get the quadrupole F₂ (source for polarisation).
    pub(crate) fn quadrupole(&self) -> f64 {
        if self.intensity.len() > 2 { self.intensity[2] } else { 0.0 }
    }

    /// Polarisation source Π = F₂ + G₀ + G₂ (where G₀ = e_mode[0], G₂ = e_mode[0]).
    pub(crate) fn polarisation_pi(&self) -> f64 {
        let f2 = self.quadrupole();
        let g0 = if !self.e_mode.is_empty() { self.e_mode[0] } else { 0.0 };
        let g2 = if !self.e_mode.is_empty() { self.e_mode[0] } else { 0.0 };
        f2 + g0 + g2
    }

    /// FLRW limit check: σ=0 should give standard hierarchy structure.
    pub(crate) fn is_flrw_compatible(&self) -> bool {
        // In FLRW: F_ℓ should decay with ℓ (no shear-driven power at high ℓ)
        if self.intensity.len() < 3 { return true; }
        let f0 = self.intensity[0].abs();
        if f0 < 1e-30 { return true; }
        self.intensity.iter().skip(5).all(|&f| f.abs() < 0.1 * f0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn test_photon_dof() { let p=PhotonState::new(10,6,true); assert_eq!(p.dof(),11+5+5); }
    #[test] fn test_photon_no_b() { let p=PhotonState::new(10,6,false); assert_eq!(p.dof(),11+5); }
    #[test] fn test_adiabatic_ic() { let mut p=PhotonState::new(5,4,true); p.set_adiabatic(1.0); assert_eq!(p.intensity[0],1.0); assert_eq!(p.intensity[1],0.0); }
}
