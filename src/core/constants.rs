// Physical constants and SSOT controller defaults.

pub(crate) const K_B_EV: f64 = 8.617333262e-5;
pub(crate) const K_B: f64 = 1.380649e-23;
pub(crate) const HBAR: f64 = 1.054571817e-34;
pub(crate) const M_E: f64 = 9.1093837015e-31;
pub(crate) const M_P: f64 = 1.67262192369e-27;
pub(crate) const G_N: f64 = 6.67430e-11;
pub(crate) const C_SI: f64 = 2.99792458e8;
pub(crate) const EV_TO_J: f64 = 1.602176634e-19;
pub(crate) const B1: f64 = 13.605693122994;
pub(crate) const B2: f64 = B1 / 4.0;
pub(crate) const E_LYA: f64 = B1 - B2;
pub(crate) const LAMBDA_2S: f64 = 8.2245;
pub(crate) const CHI_HEI: f64 = 24.587387;
pub(crate) const CHI_HEII: f64 = 54.417763;
pub(crate) const Y_P: f64 = 0.245;
pub(crate) const X_P: f64 = 1.0 - Y_P;
pub(crate) const X_E_MAX: f64 = 1.0 + 2.0 * (Y_P / (4.0 * X_P));
pub(crate) const SIGMA_T: f64 = 6.6524587321e-29;
pub(crate) const MPC: f64 = 3.085677581e22;

// ── SSOT controller defaults (PR-13A) ──
// Global default for all Rodas5P configs (Peebles, hierarchy, etc.)
pub(crate) const DEFAULT_F_SAFETY: f64 = 0.9;
// Stacked solver promoted value from PR-13A sweep:
//   pol: +8.2% wall gain, drift delta < 0.001% (PASS)
pub(crate) const STACKED_F_SAFETY: f64 = 0.95;
pub(crate) const DEFAULT_F_MIN: f64 = 0.2;
pub(crate) const DEFAULT_F_MAX: f64 = 6.0;
pub(crate) const DEFAULT_BETA: f64 = 0.04;

// ── CL-01: TCA and convention constants ──

/// TCA quadrupole prefactor WITH polarization feedback (Route A / C_ℓ pipeline).
/// Θ₂ = TCA_QUAD_PREFACTOR_STREAMING × (k/κ') × Θ₁
/// Derivation: (3/4)κ'Θ₂ = (2k/5)Θ₁ → Θ₂ = (8/15)(k/κ')Θ₁.
/// In F_ℓ = (2ℓ+1)Θ_ℓ convention: F₂ = (8/9)(k/κ')F₁.
pub(crate) const TCA_QUAD_PREFACTOR_STREAMING: f64 = 8.0 / 15.0;

/// Same prefactor in the F_ℓ = (2ℓ+1)Θ_ℓ convention: 5×(8/15)/(3×1) = 8/9.
pub(crate) const TCA_QUAD_PREFACTOR_F_STREAMING: f64 = 8.0 / 9.0;

/// TCA quadrupole prefactor WITHOUT polarization (for reference/debugging).
/// From (9/10)κ'Θ₂ = (2k/5)Θ₁ → Θ₂ = (4/9)(k/κ')Θ₁.
pub(crate) const TCA_QUAD_PREFACTOR_NO_POL: f64 = 4.0 / 9.0;

/// Bianchi homogeneous shear source prefactor (Route B, no streaming, no pol).
/// F₂ = TCA_SHEAR_PREFACTOR_BIANCHI_NOPOL × S₂ / κ'  where S₂ = (8/15)Σ.
/// = (9/10)⁻¹ = 10/9.
pub(crate) const TCA_SHEAR_PREFACTOR_BIANCHI_NOPOL: f64 = 10.0 / 9.0;

/// Bianchi homogeneous shear source prefactor WITH polarization.
/// F₂ = TCA_SHEAR_PREFACTOR_BIANCHI_POL × S₂ / κ'
/// = (3/4)⁻¹ = 4/3.
pub(crate) const TCA_SHEAR_PREFACTOR_BIANCHI_POL: f64 = 4.0 / 3.0;

/// CLASS-equivalent TCA switch: τ_c/τ_H threshold.
/// TCA active when τ_c/τ_H < this value. (CLASS default: 0.005.)
pub(crate) const TCA_TAU_C_OVER_TAU_H: f64 = 0.005;

/// CLASS-equivalent TCA switch: τ_c × k threshold.
/// TCA active when τ_c × k < this value. (CLASS default: 0.008.)
pub(crate) const TCA_TAU_C_TIMES_K: f64 = 0.008;

