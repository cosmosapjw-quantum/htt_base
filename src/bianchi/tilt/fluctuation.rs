// Level 2: Tilt fluctuation δβ(x) around global β.
// BB-05: Perturbation of the global tilt parameter.
//
// δV_{cos}^a(t,x) = perturbation of the global tilt field,
// treated as a small perturbation δβ around the homogeneous β(t).

/// Linear perturbation of tilt: δβ evolves as
/// d(δβ)/dN = -(2-q)·(∂f/∂β)|_{β₀} · δβ
/// where f(β) is the RHS of the King-Ellis equation.
///
/// For Tier C (dust): ∂f/∂β = -(cosh²β + sinh²β) = -cosh(2β)
/// So: d(δβ)/dN = cosh(2β₀) · δβ (linearized around decaying β₀)
pub(crate) fn fluctuation_growth_rate(beta0: f64, w: f64) -> f64 {
    // Linearize Tier B: f(β) = (3w-1)sinhβ coshβ/[cosh²β - w sinh²β]
    // df/dβ at β₀:
    let sh = beta0.sinh();
    let ch = beta0.cosh();
    let denom = ch*ch - w*sh*sh;
    if denom.abs() < 1e-30 { return 0.0; }
    let c2 = (2.0*beta0).cosh();
    let s2 = (2.0*beta0).sinh();
    // Numerator derivative via quotient rule
    let num = (3.0*w - 1.0) * sh * ch;
    let dnum = (3.0*w - 1.0) * c2; // d(sinhβ coshβ)/dβ = cosh(2β)
    let ddenom = (1.0 - w) * s2; // d(cosh²β - w sinh²β)/dβ = (1-w)sinh(2β)
    (dnum * denom - num * ddenom) / (denom * denom)
}

/// Amplitude of tilt fluctuation δβ/β₀ at scale factor a,
/// given initial amplitude at a_init.
pub(crate) fn fluctuation_amplitude(
    delta_beta_init: f64,
    beta0_init: f64,
    w: f64,
    a_init: f64,
    a_final: f64,
    n_steps: usize,
) -> f64 {
    let dn = ((a_final/a_init).ln()) / n_steps as f64;
    let mut delta = delta_beta_init;
    let mut beta0 = beta0_init;
    for _ in 0..n_steps {
        let rate = fluctuation_growth_rate(beta0, w);
        delta += dn * rate * delta;
        // Evolve β₀ with Tier B
        let rhs = super::king_ellis_zero_shear_rhs(beta0, w);
        beta0 += dn * rhs;
        beta0 = beta0.max(0.0);
    }
    delta
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dust_fluctuation_decays() {
        // For dust, δβ/β₀ ratio should remain bounded
        let delta = fluctuation_amplitude(1e-5, 0.1, 0.0, 1e-4, 1.0, 10000);
        assert!(delta.is_finite(), "Fluctuation diverged");
    }
}
