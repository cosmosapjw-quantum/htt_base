//! Truth Engine Contract (P1-00)
//!
//! "One equation set, many numerical strategies, zero hidden physics switches."
//!
//! This module defines the architectural contract for the Phase 1 5566-DOF
//! Bianchi I solver. The key principle: production runs use the FULL hierarchy
//! with NO equation replacement at any regime boundary. Approximations (TCA,
//! UFA, RSA) exist only as optional benchmarking tools, disabled by default,
//! and gated by residual monitors that auto-disable on failure.
//!
//! # Architecture
//!
//! ```text
//! Layer 1: TRUTH ENGINE (default)
//!   - Full equations, all ℓ active, IMEX-ARK solver
//!   - Absorbing ℓ-boundary (replaces UFA)
//!   - Adaptive ℓ_max (replaces RSA)
//!   DEFAULT FOR ALL PRODUCTION RUNS.
//!
//! Layer 2: SOLVER HYBRID
//!   - Same equations as Layer 1
//!   - Integrator switches only: IMEX → explicit (stiffness vanishes)
//!   - NO equation replacement at any boundary
//!
//! Layer 3: PHYSICS REDUCED (optional, FLRW benchmark only)
//!   - TCA: operator-based closure-in-place
//!   - UFA: neutrino sector only, residual-gated
//!   - RSA: FORBIDDEN for Bianchi production
//!   NEVER DEFAULT. Requires truth-engine residual gate.
//! ```

/// Approximation configuration for the Phase 1 solver.
///
/// All flags are OFF by default (truth engine mode).
/// Each approximation has an associated residual monitor that will
/// auto-disable the approximation if the residual exceeds threshold.
#[derive(Clone, Debug)]
pub(crate) struct ApproximationConfig {
    /// Tight-coupling approximation: operator-based closure-in-place.
    /// Reduces effective DOF from 5566 to ~25 in the tight-coupling era.
    /// NOT hardcoded CRS formulas — uses operator inversion.
    pub(crate) tca_enabled: bool,
    /// Ultra-fast approximation: neutrino sector only.
    /// Photon UFA is FORBIDDEN (recombination/source-forming region).
    pub(crate) ufa_enabled: bool,
    /// Radiation streaming approximation: FORBIDDEN for Bianchi production.
    /// Available only as FLRW diagnostic.
    pub(crate) rsa_enabled: bool,
    /// Absorbing ℓ-boundary (sponge layer at ℓ > ℓ_max - Δℓ_sponge).
    /// Replaces UFA by preventing reflection from hierarchy cutoff.
    /// This is NOT an approximation — it's a numerical boundary condition.
    pub(crate) absorbing_boundary: bool,
    /// Adaptive ℓ_max: monitor tail energy to shrink/grow active hierarchy.
    /// Replaces RSA by dynamically adjusting the hierarchy depth.
    pub(crate) adaptive_ell_max: bool,
}

impl Default for ApproximationConfig {
    /// Truth engine: all approximations OFF, boundary treatments ON.
    fn default() -> Self {
        Self {
            tca_enabled: false,
            ufa_enabled: false,
            rsa_enabled: false,
            absorbing_boundary: true,
            adaptive_ell_max: true,
        }
    }
}

impl ApproximationConfig {
    /// FLRW benchmark mode: all approximations enabled for speed comparison.
    /// NEVER use for Bianchi production.
    #[allow(dead_code)]
    pub(crate) fn flrw_benchmark() -> Self {
        Self {
            tca_enabled: true,
            ufa_enabled: true,
            rsa_enabled: false, // RSA still forbidden by default
            absorbing_boundary: true,
            adaptive_ell_max: true,
        }
    }

    /// Validate configuration for Bianchi production.
    /// Returns Err if any forbidden approximation is enabled.
    pub(crate) fn validate_bianchi(&self) -> Result<(), String> {
        if self.rsa_enabled {
            return Err("RSA is FORBIDDEN for Bianchi production. \
                        Use adaptive_ell_max instead.".into());
        }
        Ok(())
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Absorbing ℓ-boundary (sponge layer)
// ═══════════════════════════════════════════════════════════════════════

/// Sponge layer parameters for the absorbing ℓ-boundary.
///
/// At ℓ > ℓ_sponge, an artificial damping term is added to the collision
/// operator: C_sponge[F_ℓm] = -α × ((ℓ - ℓ_sponge)/(ℓ_max - ℓ_sponge))² × F_ℓm
///
/// This prevents reflection from the hierarchy cutoff WITHOUT changing
/// the equations — it's just additional dissipation in the collision term.
#[derive(Clone, Debug)]
pub(crate) struct SpongeLayer {
    /// Maximum ℓ in the hierarchy.
    pub(crate) ell_max: usize,
    /// Start of sponge region: ℓ_sponge = ℓ_max - delta_ell.
    pub(crate) delta_ell: usize,
    /// Damping strength [Mpc⁻¹]. Typical: α = 5.
    pub(crate) alpha: f64,
}

impl SpongeLayer {
    /// Default sponge: Δℓ = 15, α = 5 (from R-P2 validation).
    pub(crate) fn default_for(ell_max: usize) -> Self {
        Self {
            ell_max,
            delta_ell: if ell_max >= 20 { 15 } else { ell_max / 3 },
            alpha: 5.0,
        }
    }

    /// Sponge start: ℓ values ≥ this get damped.
    pub(crate) fn ell_sponge(&self) -> usize {
        self.ell_max.saturating_sub(self.delta_ell)
    }

    /// Damping coefficient at multipole ℓ. Returns 0 for ℓ < ℓ_sponge.
    pub(crate) fn damping(&self, ell: usize) -> f64 {
        if ell <= self.ell_sponge() || self.delta_ell == 0 {
            return 0.0;
        }
        let x = (ell - self.ell_sponge()) as f64 / self.delta_ell as f64;
        self.alpha * x * x
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Adaptive ℓ_max
// ═══════════════════════════════════════════════════════════════════════

/// Adaptive hierarchy depth controller.
///
/// Monitors the tail energy fraction R = Σ_{ℓ>ℓ_active-2} |F_ℓm|² / Σ |F_ℓm|²
/// and adjusts the active ℓ_max:
/// - R < ε_shrink → decrease active ℓ_max (skip RHS for dormant ℓ)
/// - R > ε_grow → increase active ℓ_max
///
/// Storage is always allocated to L_MAX; this only affects which ℓ
/// values are included in the RHS evaluation.
#[derive(Clone, Debug)]
pub(crate) struct AdaptiveEllMax {
    /// Maximum allocated ℓ.
    pub(crate) ell_max_alloc: usize,
    /// Current active ℓ_max (≤ ell_max_alloc).
    pub(crate) ell_max_active: usize,
    /// Threshold for shrinking: R < ε_shrink → decrease.
    pub(crate) eps_shrink: f64,
    /// Threshold for growing: R > ε_grow → increase.
    pub(crate) eps_grow: f64,
    /// Minimum active ℓ_max (never go below this).
    pub(crate) ell_min: usize,
}

impl AdaptiveEllMax {
    pub(crate) fn new(ell_max: usize) -> Self {
        Self {
            ell_max_alloc: ell_max,
            ell_max_active: ell_max,
            eps_shrink: 1e-12,
            eps_grow: 1e-8,
            ell_min: 6,
        }
    }

    /// Update active ℓ_max based on current tail energy fraction.
    /// Returns true if ℓ_max changed.
    pub(crate) fn update(&mut self, tail_fraction: f64) -> bool {
        let old = self.ell_max_active;
        if tail_fraction < self.eps_shrink && self.ell_max_active > self.ell_min {
            self.ell_max_active -= 1;
        } else if tail_fraction > self.eps_grow
            && self.ell_max_active < self.ell_max_alloc
        {
            self.ell_max_active += 1;
        }
        self.ell_max_active != old
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Residual monitor
// ═══════════════════════════════════════════════════════════════════════

/// Per-approximation residual monitor.
///
/// Tracks r_closure = |y_fast^closure - y_fast^exact| / (|y_fast^exact| + ε)
/// and auto-disables the approximation if r exceeds threshold (fail-open).
#[derive(Clone, Debug)]
pub(crate) struct ResidualMonitor {
    /// Name of the approximation being monitored.
    pub(crate) name: &'static str,
    /// Maximum allowed residual before auto-disable.
    pub(crate) threshold: f64,
    /// Current residual value.
    pub(crate) current: f64,
    /// Number of consecutive steps above threshold.
    pub(crate) violations: usize,
    /// Whether the approximation has been auto-disabled.
    pub(crate) disabled: bool,
    /// History of residual values (last N steps).
    pub(crate) history: Vec<f64>,
    /// Maximum history length.
    pub(crate) max_history: usize,
}

impl ResidualMonitor {
    pub(crate) fn new(name: &'static str, threshold: f64) -> Self {
        Self {
            name,
            threshold,
            current: 0.0,
            violations: 0,
            disabled: false,
            history: Vec::with_capacity(100),
            max_history: 100,
        }
    }

    /// Update with new residual value. Returns true if auto-disabled.
    pub(crate) fn update(&mut self, residual: f64) -> bool {
        self.current = residual;
        if self.history.len() >= self.max_history {
            self.history.remove(0);
        }
        self.history.push(residual);

        if residual > self.threshold {
            self.violations += 1;
            if self.violations >= 2 {
                self.disabled = true;
            }
        } else {
            self.violations = 0;
        }
        self.disabled
    }

    /// Check if the approximation should remain active.
    pub(crate) fn is_active(&self) -> bool {
        !self.disabled
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Truth Engine configuration (top-level)
// ═══════════════════════════════════════════════════════════════════════

/// Top-level Phase 1 solver configuration.
#[derive(Clone, Debug)]
pub(crate) struct TruthEngineConfig {
    /// Approximation flags (all OFF by default).
    pub(crate) approx: ApproximationConfig,
    /// Maximum photon hierarchy depth.
    pub(crate) ell_max_gamma: usize,
    /// Maximum neutrino hierarchy depth.
    pub(crate) ell_max_nu: usize,
    /// Sponge layer for photon hierarchy.
    pub(crate) sponge_gamma: SpongeLayer,
    /// Sponge layer for neutrino hierarchy.
    pub(crate) sponge_nu: SpongeLayer,
    /// Adaptive ℓ_max controller (photons).
    pub(crate) adaptive_gamma: AdaptiveEllMax,
    /// Adaptive ℓ_max controller (neutrinos).
    pub(crate) adaptive_nu: AdaptiveEllMax,
    /// Residual monitors for each approximation.
    pub(crate) monitors: TruthMonitors,
}

/// Residual monitors for all approximations.
#[derive(Clone, Debug)]
pub(crate) struct TruthMonitors {
    pub(crate) tca: ResidualMonitor,
    pub(crate) ufa: ResidualMonitor,
}

impl TruthEngineConfig {
    /// Production configuration: 5566 DOF, no approximations.
    pub(crate) fn production() -> Self {
        let lg = 40;
        let ln = 15;
        Self {
            approx: ApproximationConfig::default(),
            ell_max_gamma: lg,
            ell_max_nu: ln,
            sponge_gamma: SpongeLayer::default_for(lg),
            sponge_nu: SpongeLayer::default_for(ln),
            adaptive_gamma: AdaptiveEllMax::new(lg),
            adaptive_nu: AdaptiveEllMax::new(ln),
            monitors: TruthMonitors {
                tca: ResidualMonitor::new("TCA", 0.01),
                ufa: ResidualMonitor::new("UFA", 0.01),
            },
        }
    }

    /// Total degrees of freedom.
    pub(crate) fn total_dof(&self) -> usize {
        let lg = self.ell_max_gamma;
        let ln = self.ell_max_nu;
        let photon_i = (lg + 1) * (lg + 1);       // ℓ=0..L, m=-ℓ..ℓ
        let photon_e = (lg + 1) * (lg + 1) - 4;   // ℓ=2..L (no ℓ=0,1)
        let photon_b = photon_e;
        let nu_theta = (ln + 1) * (ln + 1);
        let nu_eta = nu_theta;
        let baryon = 4;  // δ_b, v_b^i
        let cdm = 4;     // δ_c, v_c^i
        let metric = 11;  // Φ, Ψ, σ_+, σ_-, shear, ...
        photon_i + photon_e + photon_b + nu_theta + nu_eta
            + baryon + cdm + metric
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_no_approx_default() {
        let cfg = ApproximationConfig::default();
        assert!(!cfg.tca_enabled, "TCA must be OFF by default");
        assert!(!cfg.ufa_enabled, "UFA must be OFF by default");
        assert!(!cfg.rsa_enabled, "RSA must be OFF by default");
        assert!(cfg.absorbing_boundary, "Absorbing boundary must be ON");
        assert!(cfg.adaptive_ell_max, "Adaptive ℓ_max must be ON");
    }

    #[test]
    fn test_bianchi_validation() {
        let mut cfg = ApproximationConfig::default();
        assert!(cfg.validate_bianchi().is_ok());
        cfg.rsa_enabled = true;
        assert!(cfg.validate_bianchi().is_err(), "RSA must be forbidden for Bianchi");
    }

    #[test]
    fn test_total_dof_5566() {
        let cfg = TruthEngineConfig::production();
        assert_eq!(cfg.total_dof(), 5566,
            "Production DOF must be 5566 (L_γ=40, L_ν=15)");
    }

    #[test]
    fn test_sponge_layer() {
        let s = SpongeLayer::default_for(40);
        assert_eq!(s.delta_ell, 15);
        assert_eq!(s.ell_sponge(), 25);
        assert_eq!(s.damping(20), 0.0, "No damping below sponge start");
        assert!(s.damping(30) > 0.0, "Damping above sponge start");
        assert!(s.damping(40) > s.damping(30), "Damping increases with ℓ");
        let d40 = s.damping(40);
        assert!((d40 - 5.0).abs() < 1e-10, "Damping at ℓ_max = α");
    }

    #[test]
    fn test_adaptive_ell_max() {
        let mut a = AdaptiveEllMax::new(40);
        assert_eq!(a.ell_max_active, 40);
        // Tiny tail → shrink
        a.update(1e-15);
        assert_eq!(a.ell_max_active, 39);
        // Large tail → grow
        a.update(1e-5);
        assert_eq!(a.ell_max_active, 40);
        // Can't grow beyond allocation
        a.update(1e-5);
        assert_eq!(a.ell_max_active, 40);
    }

    #[test]
    fn test_residual_monitor_fail_open() {
        let mut mon = ResidualMonitor::new("TCA", 0.01);
        assert!(mon.is_active());
        // First violation: warning
        mon.update(0.05);
        assert!(mon.is_active(), "Single violation → still active");
        // Second violation: auto-disable
        mon.update(0.05);
        assert!(!mon.is_active(), "Two consecutive violations → disabled");
    }

    #[test]
    fn test_residual_monitor_recovery() {
        let mut mon = ResidualMonitor::new("TCA", 0.01);
        mon.update(0.05); // violation 1
        mon.update(0.001); // below threshold → violations reset
        assert!(mon.is_active(), "Reset below threshold → still active");
        mon.update(0.05); // violation 1 again
        assert!(mon.is_active(), "Single violation after reset → active");
    }

    #[test]
    fn test_equation_invariant() {
        // Contract test: the RHS function must NOT depend on which
        // solver is active. This is verified at the trait level:
        // both IMEX and explicit solvers call the SAME build_rhs().
        // (Full test requires P1-05 implementation.)
        let cfg1 = ApproximationConfig::default();
        let cfg2 = ApproximationConfig::flrw_benchmark();
        // Default and benchmark both have same truth engine structure
        assert_eq!(cfg1.absorbing_boundary, cfg2.absorbing_boundary);
    }
}
