// CDM state: δ_c, v_c.
// BD-01: 2 DOF (pressureless dust).

#[derive(Clone, Debug)]
pub(crate) struct CDMState {
    /// CDM density perturbation δ_c.
    pub(crate) delta_c: f64,
    /// CDM velocity v_c (small in standard model).
    pub(crate) v_c: f64,
}

impl CDMState {
    pub(crate) fn new() -> Self { Self { delta_c: 0.0, v_c: 0.0 } }
    pub(crate) fn dof(&self) -> usize { 2 }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn test_cdm_dof() { assert_eq!(CDMState::new().dof(), 2); }
}
