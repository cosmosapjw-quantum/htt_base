// Baryon state: δ_b, v_b + TCA interface.
// BD-01: 2 DOF (density + velocity).

#[derive(Clone, Debug)]
pub(crate) struct BaryonState {
    /// Baryon density perturbation δ_b.
    pub(crate) delta_b: f64,
    /// Baryon velocity v_b.
    pub(crate) v_b: f64,
    /// Whether TCA is currently active.
    pub(crate) tca_active: bool,
}

impl BaryonState {
    pub(crate) fn new() -> Self { Self { delta_b: 0.0, v_b: 0.0, tca_active: true } }
    pub(crate) fn dof(&self) -> usize { 2 }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn test_baryon_dof() { assert_eq!(BaryonState::new().dof(), 2); }
    #[test] fn test_baryon_tca_default() { assert!(BaryonState::new().tca_active); }
}
