// ─────────────────────────────────────────────────────────────
// CL-01: PSTF Convention Table + Index Mapping
// ─────────────────────────────────────────────────────────────
//! CL-01 Convention Reference: CAMB / CLASS / bass_rs variable dictionary.
//!
//! See inline comments for full three-way mapping table,
//! index assignments, TCA prefactors, and gauge caveats.

// CRITICAL: bass_rs has TWO multipole conventions coexisting:
//
//   (A) flrw_kmode.rs:  Θ_ℓ  (raw temperature multipoles, Ma & Bertschinger)
//   (B) stacked.rs / collision/:  F_ℓ = (2ℓ+1)Θ_ℓ  (PSTF convention)
//
// Convention (A) matches CLASS's internal δ_γ=4Θ₀, θ_γ=3kΘ₁.
// Convention (B) matches the thesis PSTF hierarchy.
// All new C_ℓ pipeline code (CL-02 onwards) uses Convention (A).
//
// ═══════════════════════════════════════════════════════════════
// §1. Three-Way Variable Dictionary
// ═══════════════════════════════════════════════════════════════
//
// ┌───────────────┬──────────────────┬──────────────────┬────────────────────────┐
// │ Physical qty   │ CAMB (I_ℓ=4Θ_ℓ) │ CLASS (MB)       │ bass_rs                │
// ├───────────────┼──────────────────┼──────────────────┼────────────────────────┤
// │ γ monopole    │ Δ_γ = I₀ = 4Θ₀  │ δ_γ = 4Θ₀       │ y[0] = Θ₀  (kmode)     │
// │               │                  │                  │ F₀ = Θ₀    (stacked)   │
// │ γ dipole      │ q_γ=I₁=(4/3)v_γ │ θ_γ=kv_γ=3kΘ₁   │ y[1] = Θ₁  (kmode)     │
// │               │                  │                  │ F₁ = 3Θ₁   (stacked)   │
// │ γ quadrupole  │ π_γ=I₂=2σ_γ     │ σ_γ=F_{γ,2}/2    │ y[2] = Θ₂  (kmode)     │
// │               │                  │                  │ F₂ = 5Θ₂   (stacked)   │
// │ γ general ℓ   │ I_ℓ = 4Θ_ℓ      │ F_{γ,ℓ} = 4Θ_ℓ  │ y[ℓ] = Θ_ℓ (kmode)     │
// │               │                  │                  │ F_ℓ=(2ℓ+1)Θ_ℓ(stacked)│
// │ ν monopole    │ Δ_ν = 4N₀       │ δ_ν = 4N₀       │ y[L+1] = N₀ (kmode)    │
// │ ν dipole      │ q_ν = (4/3)v_ν  │ θ_ν = 3kN₁      │ y[L+2] = N₁ (kmode)    │
// │ baryon δ      │ Δ_b = δ_b       │ δ_b              │ y[L+M+2+2] = δ_b       │
// │ baryon v      │ v_b              │ θ_b = kv_b       │ y[L+M+2+3] = v_b       │
// │ CDM δ         │ Δ_c = δ_c       │ δ_c              │ y[L+M+2] = δ_c         │
// │ CDM v         │ v_c              │ θ_c = kv_c       │ y[L+M+2+1] = v_c       │
// │ potential     │ Φ (lapse)        │ φ (sync η)       │ y[L+M+2+4] = Φ (Newt)  │
// │ time          │ d/dτ (conformal) │ d/dτ (conformal) │ d/dτ (kmode)            │
// │               │                  │                  │ d/dN (stacked)          │
// │ opacity       │ κ'=an_eσ_T      │ κ'=an_eσ_T      │ κ̇=n_eσ_Tc/H (stacked)  │
// │               │                  │                  │ κ̇=an_eσ_T   (kmode)    │
// │ gauge         │ Sync (CDM)       │ Sync (default)   │ Conf. Newtonian         │
// │ R param       │ R=4ρ_γ/(3ρ_b)   │ R_b=3ρ_b/(4ρ_γ) │ r=R_b=3ρ_b/(4ρ_γ)      │
// └───────────────┴──────────────────┴──────────────────┴────────────────────────┘
//
// ═══════════════════════════════════════════════════════════════
// §2. Conversion Formulae
// ═══════════════════════════════════════════════════════════════
//
//   CAMB I_ℓ  →  bass_rs Θ_ℓ (kmode):  Θ_ℓ = I_ℓ / 4
//   CAMB I_ℓ  →  bass_rs F_ℓ (stacked): F_ℓ = (2ℓ+1) I_ℓ / 4
//   CLASS σ_γ →  bass_rs Θ₂ (kmode):   Θ₂ = σ_γ / 2
//   CLASS θ_γ →  bass_rs Θ₁ (kmode):   Θ₁ = θ_γ / (3k)
//   stacked κ̇  →  kmode κ̇:  κ̇_kmode = ℋ × κ̇_stacked
//   d/dN     →  d/dτ:   d/dτ = ℋ × d/dN
//
// ═══════════════════════════════════════════════════════════════
// §3. TCA Quadrupole Prefactors
// ═══════════════════════════════════════════════════════════════
//
// Two distinct regimes, BOTH correct:
//
//   Route A (C_ℓ pipeline, FLRW perturbative, streaming + polarization):
//     Θ₂ = (8/15)(k/κ')Θ₁       [kmode convention]
//     F₂ = (8/9)(k/κ')F₁        [stacked convention]
//     I₂ = (32/45)(k/κ')(v_b+σ)  [CAMB convention]
//
//   Route B (Bianchi homogeneous, shear-only, no streaming, no polarization):
//     F₂ = (10/9) × S₂ / κ'     [stacked convention, existing code]
//     This is (9/10)⁻¹ — inverse of the no-pol collision coefficient.
//
//   With polarization on Bianchi background:
//     F₂ = (4/3) × S₂ / κ'      [stacked, (3/4)⁻¹]
//
// ═══════════════════════════════════════════════════════════════
// §4. flrw_kmode.rs State Vector Index Map
// ═══════════════════════════════════════════════════════════════
//
// Given ell_max_g = L, ell_max_nu = M:
//   n = L + 1 + M + 1 + 5 = L + M + 7 total DOF.
//
// ┌─────────┬───────────┬───────────────────────────────────────┐
// │ Index   │ Variable  │ Physical meaning                      │
// ├─────────┼───────────┼───────────────────────────────────────┤
// │ 0       │ Θ₀        │ Photon temperature monopole           │
// │ 1       │ Θ₁        │ Photon temperature dipole             │
// │ 2       │ Θ₂        │ Photon temperature quadrupole         │
// │ ...     │ Θ_ℓ       │ Photon multipole ℓ                    │
// │ L       │ Θ_L       │ Photon truncation multipole           │
// │ L+1     │ N₀        │ Neutrino temperature monopole         │
// │ L+2     │ N₁        │ Neutrino temperature dipole           │
// │ ...     │ N_ℓ       │ Neutrino multipole ℓ                  │
// │ L+1+M   │ N_M       │ Neutrino truncation multipole         │
// │ L+M+2   │ δ_c       │ CDM density contrast                  │
// │ L+M+3   │ v_c       │ CDM velocity (conformal, dim'less)    │
// │ L+M+4   │ δ_b       │ Baryon density contrast               │
// │ L+M+5   │ v_b       │ Baryon velocity (conformal, dim'less) │
// │ L+M+6   │ Φ         │ Newtonian potential (≈ −Ψ)            │
// └─────────┴───────────┴───────────────────────────────────────┘
//
// Mapping to PerturbationSnapshot:
//   theta_0  ← y[0]
//   theta_2  ← y[2]        (only exists if L ≥ 2)
//   v_b      ← y[L+M+5]
//   phi      ← y[L+M+6]
//   psi      = −phi         (Ψ = −Φ, no anisotropic stress approx.)
//   phi_dot  = phi_dot_coeff × phi  (from momentum constraint, L47)
//   psi_dot  = −phi_dot
//   e_2      = 0.0          (no polarization in current kmode solver)
//   sigma_h  = 0.0          (FLRW: no shear)
//   sigma_dot= 0.0
//
// ═══════════════════════════════════════════════════════════════
// §5. Critical Caveats
// ═══════════════════════════════════════════════════════════════
//
// 1. flrw_kmode uses CONFORMAL TIME d/dτ. The stacked solver uses
//    e-fold time d/dN. All conversions must include ℋ factors.
//
// 2. flrw_kmode velocity v_b is the PHYSICAL peculiar velocity
//    (dimensionless, v_b/c). CLASS's θ_b = k·v_b is the velocity
//    divergence. The baryon Euler equation in flrw_kmode (L94–99)
//    uses v_b directly: v_b' = −aH·v_b + k·Ψ + (κ̇/R)(3Θ₁ − v_b).
//
// 3. The Φ evolution in flrw_kmode (L46–47) uses a simplified
//    momentum constraint: Φ' = (aH − k²/(3aH))Φ with Ψ = −Φ.
//    This is NOT self-consistent Poisson — it ignores density
//    source terms. Accuracy: ~8% deviation from CAMB (known,
//    documented in ch10 §6.3). Phase 2.0 will replace this.
//
// 4. σ_γ = 2Θ₂ is GAUGE-INVARIANT (sync = Newtonian). The TCA
//    shear from CLASS can be used directly.
//
// 5. The monopole and dipole are NOT gauge-invariant:
//    Θ₀^(N) = Θ₀^(S) − ℋα,  Θ₁^(N) = Θ₁^(S) + kα/3.
//    Direct comparison with CLASS (sync) requires gauge transform.

// ═══════════════════════════════════════════════════════════════
// §5. C_ℓ Normalization Constants (PR-01)
// ═══════════════════════════════════════════════════════════════

/// R_ν = ρ_ν/(ρ_γ+ρ_ν) in radiation era, N_eff = 3.044.
pub const R_NU: f64 = 0.408744;

/// Superhorizon adiabatic ratio Φ/η, MB95 eq. (96).
/// R_φη = (10 + 4R_ν)/(15 + 4R_ν).
pub const R_PHI_ETA: f64 = 0.6994284812914667;

/// C_ℓ prefactor for Zone A (analytic SW) and near-horizon modes: (2/3)².
/// Relates P_Φ to P_ζ via Φ = (2/3)ζ at superhorizon.
pub const CL_PREFACTOR_NEWT: f64 = 4.0 / 9.0;

/// C_ℓ prefactor for sub-horizon sync modes (k > K_CORR_SYNC): (4/9)R²_φη.
///
/// R-NORM-01 STATUS: OPEN (k-dependent amplification)
///
/// CAMB numerical verification: χ₀ = -1 gives η_s = -1.0 at ζ = 1.
/// Therefore ζ = -η_s (NOT 2η_s — the factor-2 derivation was incorrect).
/// BASS η_init = +1 → |ζ| = 1. No overall factor needed.
///
/// However, BASS IC uses the asymptotic superhorizon ratios (Θ₀ = -η/2,
/// δ_c = -3η/2), which are 3× the MB95 leading-order kτ-expansion values
/// (Θ₀ = -η_s/6, δ_c = -η_s/2). Since the Boltzmann equations are linear,
/// the evolved source function is amplified by a k-DEPENDENT factor:
///   - Superhorizon: amplification = 3 (exact, from IC scaling)
///   - Sub-horizon: amplification < 3 (ḣ kη-term breaks scaling)
///
/// The (4/9)R²_φη value for sub-horizon modes is empirically validated:
///   D₂₂₀ = 86% of CAMB (with Ψ = -Φ approximation in SW source)
///   D₂₂₀ = 91% with CL_PREFACTOR_SYNC = 1/4 = 0.25
///
/// The remaining ~9-14% deficit comes from the discrete two-value
/// approximation (should be continuous in k) and the Zone A/B boundary.
///
/// Resolution path: replace the step-function prefactor with a
/// k-continuous P(k) that interpolates between 1/9 (superhorizon)
/// and (4/9)R²_φη (sub-horizon). This requires Phase 1 solver.
pub const CL_PREFACTOR_SYNC: f64 = CL_PREFACTOR_NEWT * R_PHI_ETA * R_PHI_ETA;

/// Anisotropic stress coefficient in traceless Einstein equation:
///   Φ + Ψ = -PSI_ANISO_COEFF × (ℋ/k)² × (Ω_γΘ₂ + Ω_νN₂)
/// = 12 from 3+1 decomposition of the trace-free spatial Einstein equation.
pub const PSI_ANISO_COEFF: f64 = 12.0;

/// Thomson quadrupole coefficient in SW source: Π/4 ≈ Θ₂/4.
/// From Seljak & Zaldarriaga (1996) eq. 13 (no-polarization approx).
pub const SW_QUAD_COEFF: f64 = 0.25;

/// Sub-horizon onset boundary for sync normalization correction.
/// For k > K_CORR_SYNC: use CL_PREFACTOR_SYNC (= 4/9 × R_φη²).
/// For k ≤ K_CORR_SYNC: use CL_PREFACTOR_NEWT (= 4/9).
/// Value 0.02 Mpc⁻¹ ≈ ℋ(η_rec): empirical — analytic derivation pending (R-NORM-01).
pub const K_CORR_SYNC: f64 = 0.02_f64;

// ═══════════════════════════════════════════════════════════════
// §6. Zone C Blocking Issue — Sign Convention Documentation
// ═══════════════════════════════════════════════════════════════
//
// BASS Newtonian solver: compute_psi_algebraic_v2 returns Ψ = −Φ − aniso.
// This is the Bardeen convention (Ψ_A = −Φ_H), NOT the MB95 (ψ = φ).
// The gauge transform sync→Newt depends on this sign convention.
// Until the full transform is re-derived in BASS convention,
// Zone C carrier extraction is BLOCKED.
//
// Overlap test at k=0.02 showed:
//   Zone B source peak: −3.32e-2 (correct)
//   Zone C source peak: +7.56e-2 (WRONG SIGN)
// This sign flip is the primary Zone C failure.

// ═══════════════════════════════════════════════════════════════
// §7. Node Status
// ═══════════════════════════════════════════════════════════════

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum NodeStatus {
    Validated,      // 3-level: source + transfer + observable
    Provisional,    // some evidence, not all 3 levels
    Blocked,        // known failure, requires fix
    NotImplemented,
}

#[cfg(test)]
mod normalization_tests {
    use super::*;

    #[test]
    fn test_r_nu_derivation() {
        let n_eff = 3.044_f64;
        let ratio = n_eff * (7.0/8.0) * (4.0/11.0_f64).powf(4.0/3.0);
        let r_nu = ratio / (1.0 + ratio);
        assert!((r_nu - R_NU).abs() < 1e-4, "R_ν mismatch: {} vs {}", r_nu, R_NU);
    }

    #[test]
    fn test_r_phi_eta_derivation() {
        let r = (10.0 + 4.0 * R_NU) / (15.0 + 4.0 * R_NU);
        assert!((r - R_PHI_ETA).abs() < 1e-4, "R_φη mismatch: {} vs {}", r, R_PHI_ETA);
    }

    #[test]
    fn test_prefactor_consistency() {
        // CL_PREFACTOR_SYNC = (4/9) × R_φη² (sub-horizon empirical)
        let expected = 4.0/9.0 * R_PHI_ETA * R_PHI_ETA;
        assert!((CL_PREFACTOR_SYNC - expected).abs() < 1e-12,
            "CL_PREFACTOR_SYNC = {}, expected (4/9)R²_φη = {}", CL_PREFACTOR_SYNC, expected);
    }

    #[test]
    fn test_prefactor_direction() {
        assert!(CL_PREFACTOR_SYNC < CL_PREFACTOR_NEWT,
            "SYNC={} must be < NEWT={}", CL_PREFACTOR_SYNC, CL_PREFACTOR_NEWT);
    }

    #[test]
    fn test_ssot_values_pinned() {
        assert!((CL_PREFACTOR_NEWT - 4.0/9.0).abs() < 1e-15,
            "CL_PREFACTOR_NEWT must be 4/9, got {}", CL_PREFACTOR_NEWT);
        assert!((CL_PREFACTOR_SYNC - 4.0/9.0 * R_PHI_ETA * R_PHI_ETA).abs() < 1e-12,
            "CL_PREFACTOR_SYNC must be (4/9)R²_φη, got {}", CL_PREFACTOR_SYNC);
        assert!((K_CORR_SYNC - 0.02_f64).abs() < 1e-15,
            "K_CORR_SYNC pinned at 0.02");
    }

    #[test]
    fn test_psi_aniso_coeff() {
        // PSI_ANISO_COEFF = 12 from traceless Einstein equation
        assert_eq!(PSI_ANISO_COEFF, 12.0);
        assert_eq!(SW_QUAD_COEFF, 0.25);
    }
}
