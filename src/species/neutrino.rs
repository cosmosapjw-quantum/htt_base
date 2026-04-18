// Neutrino state: free-streaming hierarchy N_ℓ.
// BD-01: one hierarchy per family (massless).

#[derive(Clone, Debug)]
pub(crate) struct NeutrinoState {
    /// Hierarchy N₀, N₁, ..., N_{ℓ_max}.
    pub(crate) hierarchy: Vec<f64>,
    /// ℓ_max.
    pub(crate) ell_max: usize,
    /// Family index (0-based).
    pub(crate) family_idx: usize,
}

impl NeutrinoState {
    pub(crate) fn new(ell_max: usize, family_idx: usize) -> Self {
        Self { hierarchy: vec![0.0; ell_max + 1], ell_max, family_idx }
    }
    pub(crate) fn dof(&self) -> usize { self.hierarchy.len() }
    pub(crate) fn set_adiabatic(&mut self, n0: f64) { self.hierarchy.fill(0.0); self.hierarchy[0] = n0; }
    /// Neutrino anisotropic stress: π_ν ∝ N₂.
    pub(crate) fn anisotropic_stress(&self) -> f64 { if self.hierarchy.len()>2{self.hierarchy[2]}else{0.0} }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn test_nu_dof() { assert_eq!(NeutrinoState::new(8,0).dof(),9); }
    #[test] fn test_nu_ic() { let mut n=NeutrinoState::new(8,0); n.set_adiabatic(1.0); assert_eq!(n.hierarchy[0],1.0); }
}
