// Tilt mechanics: King-Ellis evolution, first integral, vorticity.
// BB-05: Three-tier tilt equation + three-level local patch.
//
// Tier A: Exact (shear + curvature coupling)
// Tier B: Zero-shear, finite-β denominator
// Tier C: Doubly-reduced (small-β approximation)
//
// Prohibitions enforced: G3, G6, G7, G8, G12, G13.

pub(crate) mod global;
pub(crate) mod fluctuation;
pub(crate) mod local_patch;
pub(crate) mod boost_cascade;
pub(crate) mod frame_guard;

/// Tilt state: rapidity β and derived quantities.
#[derive(Clone, Debug)]
pub(crate) struct TiltState {
    /// Tilt rapidity β (cosh β = −u_a n^a).
    pub(crate) beta: f64,
    /// Spatial tilt velocity components v^α = tanh β · ê^α.
    pub(crate) v_spatial: [f64; 3],
    /// Lorentz factor γ = cosh β.
    pub(crate) gamma: f64,
}

impl TiltState {
    /// Construct from rapidity and tilt direction (unit vector).
    pub(crate) fn from_beta(beta: f64, direction: [f64; 3]) -> Self {
        let v = beta.tanh();
        let gamma = beta.cosh();
        let norm = (direction[0]*direction[0]+direction[1]*direction[1]+direction[2]*direction[2]).sqrt().max(1e-30);
        Self {
            beta,
            v_spatial: [v*direction[0]/norm, v*direction[1]/norm, v*direction[2]/norm],
            gamma,
        }
    }

    /// Construct zero tilt.
    pub(crate) fn zero() -> Self {
        Self { beta: 0.0, v_spatial: [0.0; 3], gamma: 1.0 }
    }

    /// Tilt velocity magnitude v = tanh β.
    pub(crate) fn v(&self) -> f64 { self.beta.tanh() }
}

// ═══════════════════════════════════════════
// §1. King-Ellis tilt evolution: three tiers
// ═══════════════════════════════════════════

/// Tier A: Exact tilt evolution with shear and curvature.
///
/// dβ/dN = −[(1−3w)sinhβ coshβ + S·sinhβ coshβ] / [cosh²β − w·sinh²β]
///        − (curvature term)
///
/// where S = σ_{ab}ê^a ê^b / H is the shear projected along the tilt direction,
/// and the curvature term involves A₀ (Bianchi V curvature parameter).
///
/// The denominator [cosh²β − w·sinh²β] = [1 + (1−w)sinh²β] is ESSENTIAL
/// for large β and is NOT unity except for stiff fluid (w=1).
pub(crate) fn king_ellis_exact_rhs(
    beta: f64,
    w: f64,        // equation of state p = wρ
    _h: f64,       // Hubble rate (for dimensional terms)
    sigma_proj: f64, // S = σ_{ab}ê^a ê^b / H (shear projected along tilt)
    _a0: f64,      // curvature parameter (BV)
    _a: f64,       // scale factor
    _b: f64,       // directional scale factor
) -> f64 {
    if beta.abs() < 1e-30 { return 0.0; }
    let sh = beta.sinh();
    let ch = beta.cosh();
    let denom = ch*ch - w*sh*sh; // = 1 + (1-w)sinh²β
    if denom.abs() < 1e-30 { return 0.0; }
    let numerator = -((1.0 - 3.0*w) + sigma_proj) * sh * ch;
    // Curvature term (BV-specific): −2wA₀ a⁻¹ e^{-2b} tanhβ / denom
    // Omitted in generic form; added in type-specific wrappers.
    numerator / denom
}

/// Tier B: Zero-shear, finite-β denominator.
///
/// dβ/dN = (3w−1) sinhβ coshβ / [cosh²β − w sinh²β]
///
/// Valid when σ_{ab} = 0 (FLRW background) but β can be large.
/// The denominator modifies dynamics at large tilt for w ≠ 1.
///
/// WARNING (G6): This is NOT the universal exact law — it omits
/// shear and curvature coupling terms.
pub(crate) fn king_ellis_zero_shear_rhs(beta: f64, w: f64) -> f64 {
    if beta.abs() < 1e-30 { return 0.0; }
    let sh = beta.sinh();
    let ch = beta.cosh();
    let denom = ch*ch - w*sh*sh;
    if denom.abs() < 1e-30 { return 0.0; }
    (3.0*w - 1.0) * sh * ch / denom
}

/// Tier C: Doubly-reduced (denominator ≈ 1).
///
/// dβ/dN ≈ (3w−1) sinhβ coshβ
///
/// Valid when σ = 0 AND sinh²β ≪ 1/(1−w).
/// For dust (w=0): valid when β ≪ 1.
///
/// WARNING (G6): This is the LEAST accurate tier.
pub(crate) fn king_ellis_reduced_rhs(beta: f64, w: f64) -> f64 {
    (3.0*w - 1.0) * beta.sinh() * beta.cosh()
}

// ═══════════════════════════════════════════
// §2. First integral (reduced system)
// ═══════════════════════════════════════════

/// First integral of the reduced (Tier C) tilt equation.
///
/// I = a^{1−3w} · sinhβ = const  (for constant w).
///
/// This is conserved along Tier C evolution. Tier A/B evolution
/// with shear and curvature does NOT conserve this integral.
pub(crate) fn first_integral(a: f64, w: f64, beta: f64) -> f64 {
    a.powf(1.0 - 3.0*w) * beta.sinh()
}

/// First integral using the full form from ER-01:
/// I = ρ^{w/(1+w)} · a · e^{2b} · sinh β
pub(crate) fn first_integral_full(rho: f64, w: f64, a: f64, b: f64, beta: f64) -> f64 {
    let rho_factor = if (1.0 + w).abs() > 1e-30 {
        rho.powf(w / (1.0 + w))
    } else {
        1.0
    };
    rho_factor * a * (2.0 * b).exp() * beta.sinh()
}

// ═══════════════════════════════════════════
// §3. Vorticity from tilt
// ═══════════════════════════════════════════

/// King-Ellis vorticity condition: ω̂ ≠ 0 iff n_{αβ}v^α ≠ 0.
///
/// For diagonal n = diag(n₁, n₂, n₃) and v = (v₁, v₂, v₃):
///   (n·v)_β = n_β v_β  (no sum, diagonal)
///
/// Returns the 3-vector n_{αβ}v^β. Nonzero components generate vorticity.
pub(crate) fn vorticity_from_tilt(
    n_eigenvalues: &[f64; 3],
    v_alpha: &[f64; 3],
) -> [f64; 3] {
    [
        n_eigenvalues[0] * v_alpha[0],
        n_eigenvalues[1] * v_alpha[1],
        n_eigenvalues[2] * v_alpha[2],
    ]
}

/// Check if tilt generates vorticity for a given Bianchi type.
pub(crate) fn tilt_generates_vorticity(
    n_eigenvalues: &[f64; 3],
    v_alpha: &[f64; 3],
) -> bool {
    let nv = vorticity_from_tilt(n_eigenvalues, v_alpha);
    nv[0]*nv[0] + nv[1]*nv[1] + nv[2]*nv[2] > 1e-30
}

// ═══════════════════════════════════════════
// §4. Tilt density parameter
// ═══════════════════════════════════════════

/// Ω_tilt = (1+w) Ω_m sinh²β.
///
/// This is the tilt contribution to the departure parameter
/// x = Σ² − W² + Ω_tilt + Ω_{k,aniso}.
pub(crate) fn omega_tilt(w: f64, omega_m: f64, beta: f64) -> f64 {
    (1.0 + w) * omega_m * beta.sinh().powi(2)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Dust: tilt decays (G7 compliance) ──
    #[test]
    fn test_dust_tilt_decays() {
        // Tier C: dβ/dN = (3×0−1)sinhβ coshβ = −sinhβ coshβ < 0 for β > 0
        let beta = 0.1;
        let rhs = king_ellis_reduced_rhs(beta, 0.0);
        assert!(rhs < 0.0, "Dust tilt must DECAY (G7): dβ/dN = {:.4e}", rhs);
    }

    // ── Radiation: tilt frozen in zero-shear limit (G12) ──
    #[test]
    fn test_radiation_frozen_zero_shear() {
        // Tier B at w=1/3: numerator (3×1/3−1) = 0
        let beta = 0.5;
        let rhs = king_ellis_zero_shear_rhs(beta, 1.0/3.0);
        assert!(rhs.abs() < 1e-15, "Radiation frozen (G12 limit): dβ/dN = {:.2e}", rhs);
    }

    // ── Radiation NOT frozen with shear ──
    #[test]
    fn test_radiation_evolves_with_shear() {
        // Tier A with σ ≠ 0: radiation tilt CAN evolve
        let beta = 0.1;
        let sigma_proj = 0.01;
        let rhs = king_ellis_exact_rhs(beta, 1.0/3.0, 1.0, sigma_proj, 0.0, 1.0, 0.0);
        assert!(rhs.abs() > 1e-10, "Radiation with shear must evolve: dβ/dN = {:.4e}", rhs);
    }

    // ── Stiff fluid: tilt grows ──
    #[test]
    fn test_stiff_tilt_grows() {
        let beta = 0.1;
        let rhs = king_ellis_reduced_rhs(beta, 1.0);
        // (3×1−1)sinhβ coshβ = 2×sinhβ coshβ > 0
        assert!(rhs > 0.0, "Stiff tilt must GROW: dβ/dN = {:.4e}", rhs);
    }

    // ── K=1/3 bifurcation ──
    #[test]
    fn test_bifurcation_at_w_one_third() {
        let beta = 0.2;
        // w < 1/3: decay
        assert!(king_ellis_reduced_rhs(beta, 0.0) < 0.0);
        assert!(king_ellis_reduced_rhs(beta, 0.2) < 0.0);
        // w = 1/3: frozen
        assert!(king_ellis_reduced_rhs(beta, 1.0/3.0).abs() < 1e-15);
        // w > 1/3: growth
        assert!(king_ellis_reduced_rhs(beta, 0.5) > 0.0);
        assert!(king_ellis_reduced_rhs(beta, 1.0) > 0.0);
    }

    // ── Tier B vs C agreement at small β ──
    #[test]
    fn test_tier_b_c_agreement_small_beta() {
        let w = 0.0;
        for &beta in &[1e-4, 1e-3, 1e-2] {
            let b = king_ellis_zero_shear_rhs(beta, w);
            let c = king_ellis_reduced_rhs(beta, w);
            let rel = if b.abs() > 1e-30 { (b - c).abs() / b.abs() } else { 0.0 };
            assert!(rel < 0.01, "β={}: Tier B={:.6e}, Tier C={:.6e}, rel={:.2e}", beta, b, c, rel);
        }
    }

    // ── Tier B denominator matters at large β ──
    #[test]
    fn test_tier_b_denominator_large_beta() {
        let w = 0.0; // dust
        let beta = 2.0; // large tilt
        let b = king_ellis_zero_shear_rhs(beta, w);
        let c = king_ellis_reduced_rhs(beta, w);
        // Denominator = cosh²β − 0 = cosh²β ≈ 13.6 → significant correction
        assert!((b/c - 1.0).abs() > 0.1, "Denominator should matter at β=2");
    }

    // ── First integral conservation ──
    #[test]
    fn test_first_integral_dust() {
        // Dust (w=0): I = a · sinhβ. If β evolves as tanh β ∝ a⁻¹:
        // At small β: β ≈ tanh β ∝ a⁻¹, sinh β ≈ β ∝ a⁻¹ → I = a × a⁻¹ = const ✓
        let i1 = first_integral(1.0, 0.0, 0.1);
        let i2 = first_integral(0.5, 0.0, 0.2);  // a halved, β doubled
        assert!((i1 - i2).abs() / i1.abs() < 0.01, "First integral: {:.6e} vs {:.6e}", i1, i2);
    }

    // ── Vorticity: BI has none ──
    #[test]
    fn test_bi_no_vorticity() {
        let n = [0.0, 0.0, 0.0];
        let v = [0.1, 0.0, 0.0];
        assert!(!tilt_generates_vorticity(&n, &v), "BI cannot generate vorticity");
    }

    // ── Vorticity: BV has none (n=0) ──
    #[test]
    fn test_bv_no_vorticity() {
        let n = [0.0, 0.0, 0.0];
        let v = [0.1, 0.05, 0.0];
        assert!(!tilt_generates_vorticity(&n, &v), "BV cannot generate vorticity");
    }

    // ── Vorticity: BVII_h does generate ──
    #[test]
    fn test_bviih_vorticity() {
        let n = [1.0, 1.0, 0.0]; // VII_h has n₁=n₂>0
        let v = [0.1, 0.0, 0.0]; // tilt along e₁
        assert!(tilt_generates_vorticity(&n, &v), "VII_h must generate vorticity");
    }

    // ── Omega_tilt ──
    #[test]
    fn test_omega_tilt() {
        let ot = omega_tilt(0.0, 0.3, 0.001);
        // (1+0)×0.3×sinh²(0.001) ≈ 0.3 × 1e-6
        assert!(ot > 0.0);
        assert!(ot < 1e-5);
    }

    // ── Zero tilt state ──
    #[test]
    fn test_zero_tilt() {
        let ts = TiltState::zero();
        assert_eq!(ts.beta, 0.0);
        assert_eq!(ts.gamma, 1.0);
        assert_eq!(ts.v(), 0.0);
    }
}
