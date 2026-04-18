// Cosmological constant state.
// BD-01: 0 dynamic DOF (constant density).

#[derive(Clone, Debug)]
pub(crate) struct LambdaState {
    /// Cosmological constant density parameter Ω_Λ.
    pub(crate) omega_lambda: f64,
}

impl LambdaState {
    pub(crate) fn new(omega_lambda: f64) -> Self { Self { omega_lambda } }
    /// Λ has 0 dynamic DOF (constant).
    pub(crate) fn dof(&self) -> usize { 0 }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn test_lambda_zero_dof() { assert_eq!(LambdaState::new(0.685).dof(), 0); }
}
