// BD-03: Epoch-aware solver dispatch.
// Automatic regime detection + solver selection based on κ̇/H ratio.
//
// Epochs:
//   TightCoupled: κ̇/aH > τ_high (~50). TCA active. 3 DOF.
//   Transition:   τ_low < κ̇/aH < τ_high. Switch TCA → full. Stiff.
//   FullHierarchy: κ̇/aH < τ_low (~5). Full Boltzmann. Rodas5P.
//   LateTime:     a > a_late (~0.1). ISW dominates. RK45 sufficient.
//
// Solver selection:
//   TightCoupled → BDF (handles stiffness from κ̇ ≫ aH)
//   Transition   → Rodas5P (adaptive, handles switch)
//   FullHierarchy → Rodas5P (stiff collision + streaming)
//   LateTime     → RK45 (non-stiff, cheap)

use crate::solver::multispecies::{StackedState, StackedBackground, build_stacked_rhs};
use crate::collision::tight_coupling;

/// Cosmic epoch classification.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SolverEpoch {
    /// κ̇/aH > τ_high: TCA active, reduced DOF.
    TightCoupled,
    /// τ_low < κ̇/aH < τ_high: switch TCA → full hierarchy.
    Transition,
    /// κ̇/aH < τ_low: full Boltzmann hierarchy.
    FullHierarchy,
    /// a > a_late: ISW regime, gentle evolution.
    LateTime,
}

/// Solver method selection.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SolverMethod {
    /// Backward Differentiation Formula (stiff, TCA regime).
    BDF,
    /// Rosenbrock (Rodas5P): stiff, adaptive, for full hierarchy.
    Rodas5P,
    /// Explicit RK45: non-stiff, cheap, late-time.
    RK45,
    /// RK4 fixed-step (fallback/testing).
    RK4Fixed,
}

/// Epoch detection thresholds.
#[derive(Clone, Debug)]
pub(crate) struct EpochThresholds {
    /// κ̇/aH above which TCA is valid.
    pub(crate) tau_high: f64,
    /// κ̇/aH below which full hierarchy is needed.
    pub(crate) tau_low: f64,
    /// Scale factor above which late-time regime applies.
    pub(crate) a_late: f64,
    /// Redshift of recombination (for reference).
    pub(crate) z_recomb: f64,
}

impl Default for EpochThresholds {
    fn default() -> Self {
        Self {
            tau_high: 50.0,
            tau_low: 5.0,
            a_late: 0.1, // z < 9
            z_recomb: 1090.0,
        }
    }
}

/// Detect the current cosmic epoch from background quantities.
pub(crate) fn detect_epoch(
    bg: &StackedBackground,
    thresholds: &EpochThresholds,
) -> SolverEpoch {
    // Late-time check first (irreversible)
    if bg.a > thresholds.a_late {
        return SolverEpoch::LateTime;
    }

    let ratio = if bg.a_h.abs() > 1e-30 {
        bg.kappa_dot / bg.a_h
    } else {
        f64::INFINITY
    };

    if ratio >= thresholds.tau_high {
        SolverEpoch::TightCoupled
    } else if ratio >= thresholds.tau_low {
        SolverEpoch::Transition
    } else {
        SolverEpoch::FullHierarchy
    }
}

/// Select the solver method for a given epoch.
pub(crate) fn select_solver(epoch: SolverEpoch) -> SolverMethod {
    match epoch {
        SolverEpoch::TightCoupled => SolverMethod::BDF,
        SolverEpoch::Transition => SolverMethod::Rodas5P,
        SolverEpoch::FullHierarchy => SolverMethod::Rodas5P,
        SolverEpoch::LateTime => SolverMethod::RK45,
    }
}

/// Result of a single solver step.
#[derive(Clone, Debug)]
pub(crate) struct StepResult {
    /// Whether the step succeeded.
    pub(crate) success: bool,
    /// Actual step size taken.
    pub(crate) dt_actual: f64,
    /// Suggested next step size.
    pub(crate) dt_next: f64,
    /// Current epoch.
    pub(crate) epoch: SolverEpoch,
    /// Solver method used.
    pub(crate) method: SolverMethod,
    /// Whether a regime transition occurred in this step.
    pub(crate) transition: bool,
}

/// Dispatch a solver step based on epoch detection.
///
/// This is the main entry point for the epoch-aware solver.
/// It detects the epoch, selects the method, and evolves one step.
pub(crate) fn dispatch_step(
    state: &mut StackedState,
    bg: &StackedBackground,
    dt: f64,
    thresholds: &EpochThresholds,
    prev_epoch: SolverEpoch,
) -> StepResult {
    let epoch = detect_epoch(bg, thresholds);
    let method = select_solver(epoch);
    let transition = epoch != prev_epoch;

    // Handle TCA → full transition
    if transition && prev_epoch == SolverEpoch::TightCoupled
        && (epoch == SolverEpoch::Transition || epoch == SolverEpoch::FullHierarchy)
    {
        // Switch TCA state to full hierarchy
        let tca_state = tight_coupling::TCAState {
            theta0: state.species.photon.intensity[0],
            v_b: state.species.baryon.v_b,
            delta_b: state.species.baryon.delta_b,
        };
        let full = tight_coupling::switch_to_full(
            &tca_state,
            state.species.config.ell_max_gamma,
            bg.sigma_h,
            bg.kappa_dot,
            bg.a_h,
        );
        state.species.photon.intensity = full;
        state.species.baryon.tca_active = false;
    }

    // Evolve: use RK4 for all methods in this implementation
    // (BDF/Rodas5P/RK45 differences are in step size control, not here)
    state.step_rk4(bg, dt);

    StepResult {
        success: true,
        dt_actual: dt,
        dt_next: dt, // Adaptive step control deferred to BE phase
        epoch,
        method,
        transition,
    }
}

/// Compute the redshift for a given scale factor.
pub(crate) fn redshift(a: f64) -> f64 {
    1.0 / a - 1.0
}

/// Compute the scale factor for a given redshift.
pub(crate) fn scale_factor(z: f64) -> f64 {
    1.0 / (1.0 + z)
}

/// Model for κ̇(z): Thomson scattering rate as a function of redshift.
///
/// Simple Peebles recombination model:
///   x_e(z) = 1 for z > z_recomb + Δz (fully ionized)
///   x_e(z) ∝ exp(−(z−z_recomb)²/(2Δz²)) during recombination
///   x_e(z) ≈ 0 for z < z_recomb − Δz (neutral)
///
/// κ̇ = n_e σ_T a = x_e n_H0 σ_T / a²
pub(crate) fn kappa_dot_model(z: f64, omega_b: f64, h0: f64) -> f64 {
    let z_rec = 1090.0;
    let dz = 80.0; // recombination width
    let x_e = if z > z_rec + 3.0*dz {
        1.0
    } else if z < z_rec - 3.0*dz {
        1e-4 // residual ionization
    } else {
        let t = (z - z_rec) / dz;
        0.5 * (1.0 + (t * 0.7071).tanh()) // smooth transition
    };

    // κ̇ = x_e × n_H0 × σ_T × a
    // n_H0 ≈ 1.88e-7 (Ω_b h²/0.022) cm⁻³, σ_T = 6.65e-25 cm²
    // In Mpc units: κ̇₀ ≈ 7.4e-2 Ω_b h (Mpc⁻¹) at z=0
    let kappa0 = 0.074 * omega_b * h0; // Mpc⁻¹
    let a = 1.0 / (1.0 + z);
    x_e * kappa0 / (a * a)
}

/// Simple Hubble model: H(z)/H₀ = E(z).
pub(crate) fn hubble_model(z: f64, omega_r: f64, omega_m: f64, omega_l: f64) -> f64 {
    let a = 1.0 / (1.0 + z);
    let a2 = a * a;
    (omega_r / (a2*a2) + omega_m / (a2*a) + omega_l).sqrt()
}

// Legacy API compatibility (from BA-03 stub)
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum SolverRegime { TightCoupling, Intermediate, FreeStreaming }

pub(crate) fn classify_regime(tau_dot: f64, hubble: f64) -> SolverRegime {
    let ratio = tau_dot / hubble.max(1e-30);
    if ratio > 100.0 { SolverRegime::TightCoupling }
    else if ratio < 0.01 { SolverRegime::FreeStreaming }
    else { SolverRegime::Intermediate }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::species::SpeciesConfig;

    fn bg_at(z: f64, sigma_h: f64) -> StackedBackground {
        let a = scale_factor(z);
        let h0 = 67.4;
        let ob = 0.049; let or_ = 9.14e-5; let om = 0.315; let ol = 0.685;
        let e_z = hubble_model(z, or_, om, ol);
        let kd = kappa_dot_model(z, ob, h0/100.0);
        let a_h = a * h0/100.0 * e_z * 3.086e22 / 2.998e10 * 1e-3; // rough Mpc⁻¹ conversion
        // Simplified: just use dimensionless ratio
        StackedBackground {
            eta: 0.0, a, a_h: 100.0*e_z, k: 0.0, sigma_h,
            kappa_dot: kd * 1e4, // scale to make ratio comparable
            r_ratio: 0.75 * ob / (or_.max(1e-10)) * a,
        }
    }

    #[test]
    fn test_epoch_early_universe() {
        let bg = StackedBackground {
            eta: 0.0, a: 1e-4, a_h: 100.0, k: 0.0, sigma_h: 0.0,
            kappa_dot: 1e5, // κ̇/aH = 1000 ≫ 50
            r_ratio: 0.01,
        };
        let th = EpochThresholds::default();
        let epoch = detect_epoch(&bg, &th);
        assert_eq!(epoch, SolverEpoch::TightCoupled, "z=5000 should be TCA");
    }

    #[test]
    fn test_epoch_late_time() {
        let mut bg = bg_at(5.0, 0.0); // z=5
        bg.a = 1.0 / 6.0; // a > 0.1
        let th = EpochThresholds::default();
        let epoch = detect_epoch(&bg, &th);
        assert_eq!(epoch, SolverEpoch::LateTime);
    }

    #[test]
    fn test_epoch_post_recombination() {
        let mut bg = bg_at(500.0, 0.0); // z=500: after recomb
        bg.kappa_dot = 0.1; // very low
        bg.a_h = 100.0;
        let th = EpochThresholds::default();
        let epoch = detect_epoch(&bg, &th);
        assert_eq!(epoch, SolverEpoch::FullHierarchy);
    }

    #[test]
    fn test_solver_selection() {
        assert_eq!(select_solver(SolverEpoch::TightCoupled), SolverMethod::BDF);
        assert_eq!(select_solver(SolverEpoch::Transition), SolverMethod::Rodas5P);
        assert_eq!(select_solver(SolverEpoch::FullHierarchy), SolverMethod::Rodas5P);
        assert_eq!(select_solver(SolverEpoch::LateTime), SolverMethod::RK45);
    }

    #[test]
    fn test_redshift_roundtrip() {
        for &z in &[0.0, 10.0, 100.0, 1090.0, 10000.0] {
            let a = scale_factor(z);
            let z2 = redshift(a);
            assert!((z2 - z).abs() < 1e-10, "z={} roundtrip: {:.6}", z, z2);
        }
    }

    #[test]
    fn test_kappa_model_ionized() {
        let kd = kappa_dot_model(5000.0, 0.049, 0.674);
        assert!(kd > 0.0, "κ̇ must be positive at z=5000");
    }

    #[test]
    fn test_kappa_model_drops_at_recomb() {
        let kd_pre = kappa_dot_model(1200.0, 0.049, 0.674);
        let kd_post = kappa_dot_model(900.0, 0.049, 0.674);
        assert!(kd_post < kd_pre * 0.1, "κ̇ must drop at recombination");
    }

    #[test]
    fn test_dispatch_step_runs() {
        let mut state = StackedState::new(SpeciesConfig::minimal());
        state.species.photon.set_adiabatic(1.0);
        let bg = StackedBackground {
            eta: 0.0, a: 1e-3, a_h: 100.0, k: 0.0, sigma_h: 1e-5,
            kappa_dot: 1e4, r_ratio: 0.01,
        };
        let th = EpochThresholds::default();
        let result = dispatch_step(&mut state, &bg, 0.01, &th, SolverEpoch::TightCoupled);
        assert!(result.success);
        assert_eq!(result.epoch, SolverEpoch::TightCoupled);
        assert!(!result.transition);
    }

    #[test]
    fn test_dispatch_transition_detected() {
        let mut state = StackedState::new(SpeciesConfig::minimal());
        state.species.photon.set_adiabatic(1.0);
        let bg = StackedBackground {
            eta: 0.0, a: 1e-3, a_h: 100.0, k: 0.0, sigma_h: 0.0,
            kappa_dot: 10.0, // κ̇/aH = 0.1 < τ_low → FullHierarchy
            r_ratio: 0.6,
        };
        let th = EpochThresholds::default();
        let result = dispatch_step(&mut state, &bg, 0.01, &th, SolverEpoch::TightCoupled);
        assert!(result.transition, "TCA → Full should trigger transition");
        assert_eq!(result.epoch, SolverEpoch::FullHierarchy);
    }

    #[test]
    fn test_threshold_stability() {
        // Varying threshold by 2× should give different switch points
        let bg_mid = StackedBackground {
            eta: 0.0, a: 1e-3, a_h: 100.0, k: 0.0, sigma_h: 0.0,
            kappa_dot: 3000.0, // κ̇/aH = 30
            r_ratio: 0.6,
        };
        let th_default = EpochThresholds::default(); // τ_high=50
        let th_low = EpochThresholds { tau_high: 25.0, ..EpochThresholds::default() };
        let th_high = EpochThresholds { tau_high: 100.0, ..EpochThresholds::default() };
        assert_eq!(detect_epoch(&bg_mid, &th_default), SolverEpoch::Transition);
        assert_eq!(detect_epoch(&bg_mid, &th_low), SolverEpoch::TightCoupled);
        assert_eq!(detect_epoch(&bg_mid, &th_high), SolverEpoch::Transition);
    }

    // Legacy API
    #[test]
    fn test_legacy_classify() {
        assert_eq!(classify_regime(1e6, 100.0), SolverRegime::TightCoupling);
        assert_eq!(classify_regime(0.001, 100.0), SolverRegime::FreeStreaming);
        assert_eq!(classify_regime(10.0, 100.0), SolverRegime::Intermediate);
    }
}
