//! TF-03: TCA Pre-Phase with proper state expansion.
//!
//! Evolves the TCA (3 DOF) + neutrino (free-streaming) system from z_max
//! to z_switch, then expands to full hierarchy for Rodas5P.
//!
//! Key insight: TCA only applies to photon-baryon (Compton coupling).
//! Neutrinos are always free-streaming, so we use analytical IC for them.
//!
//! State expansion at switch point (CAMB-style):
//!   Photon: F₀=Θ₀, F₁=v_b, F₂=(8/15)(σ+v_b·k)/κ̇, F₃=(3/7)k·F₂/κ̇
//!   Neutrino: N₀=-Φ/2, N₁=kΦ/(6aH), N₂=(k/(2aH))²·Φ/3 (radiation-era)
//!   CDM: δ_c=−3Φ/2, v_c=kΦ/(2aH)
//!   Baryon: δ_b=−3Φ/2, v_b (from TCA)
//!   Φ: from Poisson or initial value

use crate::collision::tight_coupling::*;
use crate::recombination::visibility_hyrec::VisibilityParams;

/// Construct the full state vector at the TCA→full switch point.
///
/// This is the corrected version that properly initializes ALL species,
/// not just the photon block.
///
/// Arguments:
///   - tca: TCA state at switch (Θ₀, v_b, δ_b)
///   - k: wavenumber [Mpc⁻¹]
///   - a_h: conformal Hubble aH at switch [Mpc⁻¹]
///   - kappa_dot: Thomson opacity at switch [Mpc⁻¹]
///   - sigma_h: σ/H at switch
///   - phi: gravitational potential at switch
///   - lg: photon ℓ_max
///   - ln: neutrino ℓ_max
pub(crate) fn expand_tca_to_full(
    tca: &TCAState,
    k: f64,
    a_h: f64,
    kappa_dot: f64,
    sigma_h: f64,
    phi: f64,
    lg: usize,
    ln: usize,
) -> Vec<f64> {
    let n_state = lg + 1 + ln + 1 + 5;
    let mut y = vec![0.0; n_state];

    // ── Photon block: F₀..F_lg ──
    y[0] = tca.theta0;                          // F₀ = Θ₀
    if lg >= 1 { y[1] = tca.v_b; }              // F₁ ≈ v_b (tight-coupled)
    if lg >= 2 {
        // F₂: quasi-static quadrupole (CAMB Eq. 7.4)
        // F₂ = (8/15)(k/κ̇)(v_b) for scalar streaming
        //     + (8/15)(σ/H)(aH/κ̇) for Bianchi shear
        let f2_stream = if kappa_dot.abs() > 1e-30 {
            (8.0 / 15.0) * k * tca.v_b / kappa_dot
        } else { 0.0 };
        let f2_shear = slip_term_f2(sigma_h, kappa_dot, a_h);
        y[2] = f2_stream + f2_shear;
    }
    if lg >= 3 {
        // F₃: next-order correction (CAMB CRS initialization)
        // F₃ ≈ (3/7)(k/κ̇) F₂
        if kappa_dot.abs() > 1e-30 {
            y[3] = (3.0 / 7.0) * k * y[2] / kappa_dot;
        }
    }
    // F_ℓ = 0 for ℓ ≥ 4

    // ── Neutrino block: N₀..N_ln (free-streaming since z ~ 10¹⁰) ──
    let n0 = lg + 1;
    y[n0] = -0.5 * phi;                         // N₀ ≈ −Φ/2 (adiabatic)
    if ln >= 1 && a_h.abs() > 1e-30 {
        y[n0 + 1] = k * phi / (6.0 * a_h);      // N₁ ≈ kΦ/(6aH)
    }
    if ln >= 2 && a_h.abs() > 1e-30 {
        // N₂ ≈ (k/(2aH))² × Φ/3 (next order, radiation era)
        let x = k / (2.0 * a_h);
        y[n0 + 2] = x * x * phi / 3.0;
    }
    // N_ℓ = 0 for ℓ ≥ 3 (negligible at z_switch ~ 1200)

    // ── CDM block ──
    let dc_idx = n0 + ln + 1;
    y[dc_idx] = -1.5 * phi;                     // δ_c = −3Φ/2
    if a_h.abs() > 1e-30 {
        y[dc_idx + 1] = k * phi / (2.0 * a_h);  // v_c ≈ kΦ/(2aH)
    }

    // ── Baryon block ──
    y[dc_idx + 2] = tca.delta_b;                // δ_b from TCA
    y[dc_idx + 3] = tca.v_b;                    // v_b from TCA

    // ── Gravitational potential ──
    y[n_state - 1] = phi;                        // Φ

    y
}

/// Run TCA pre-phase from z_start to z_switch.
///
/// Returns the TCA state at z_switch.
pub(crate) fn evolve_tca_phase(
    k: f64,
    params: &VisibilityParams,
    vis_z: &[f64],
    vis_eta: &[f64],
    vis_kappa_dot: &[f64],
    z_switch: f64,
) -> TCAState {
    let mpc_m = 3.08567758e22_f64;
    let h0_si = params.h * 100.0e3 / mpc_m;
    let h0c = h0_si / 2.99792458e8 * mpc_m;
    let og = params.omega_gamma();
    let phi_init = 1.0;

    // IC at z_start (highest z in vis grid)
    let mut state = TCAState {
        theta0: -0.5 * phi_init,
        v_b: 0.0,
        delta_b: -1.5 * phi_init,
    };

    // Evolve through vis grid from high z to z_switch
    let n = vis_z.len();
    for i in (1..n).rev() {
        let z = vis_z[i];
        if z < z_switch { break; }

        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * params.e_of_z(z);
        let kd = vis_kappa_dot[i];
        let r = 3.0 * params.omega_b / (4.0 * og * (1.0 + z));

        let bg = TCABackground {
            a_h,
            k,
            r_ratio: r,
            kappa_dot: kd,
            sigma_h: 0.0,
            psi: -phi_init, // Ψ = −Φ (no anisotropic stress)
            phi_dot: 0.0,   // Φ̇ ≈ 0 in radiation era
        };

        // Step size from vis grid spacing
        let d_eta = (vis_eta[i-1] - vis_eta[i]).abs();
        if d_eta > 0.0 && d_eta < 100.0 {
            tca_step_rk4(&mut state, &bg, d_eta);
        }
    }
    state
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_expand_dimensions() {
        let tca = TCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5 };
        let y = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 1e-3, 1.0, 15, 8);
        assert_eq!(y.len(), 15 + 1 + 8 + 1 + 5);
        assert_eq!(y.len(), 30);
    }

    #[test]
    fn test_expand_photon_block() {
        let tca = TCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5 };
        let y = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 0.0, 1.0, 6, 4);
        assert_eq!(y[0], -0.5);  // F₀ = Θ₀
        assert_eq!(y[1], 0.01);  // F₁ = v_b
        // F₂ = (8/15)(k/κ̇)v_b = (8/15)(0.01/1e4)(0.01) = 5.33e-8
        assert!((y[2] - (8.0/15.0)*0.01*0.01/1e4).abs() < 1e-12);
    }

    #[test]
    fn test_expand_neutrino_block() {
        let tca = TCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5 };
        let phi = 1.0;
        let y = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 0.0, phi, 6, 4);
        let n0 = 7; // neutrino offset = lg+1
        assert_eq!(y[n0], -0.5 * phi);  // N₀ = −Φ/2
        assert!((y[n0+1] - 0.01*phi/(6.0*100.0)).abs() < 1e-14);  // N₁ = kΦ/(6aH)
    }

    #[test]
    fn test_expand_cdm_block() {
        let tca = TCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5 };
        let phi = 1.0;
        let y = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 0.0, phi, 6, 4);
        let dc_idx = 7 + 4 + 1; // lg+1 + ln+1
        assert_eq!(y[dc_idx], -1.5 * phi);  // δ_c = −3Φ/2
        assert!((y[dc_idx+1] - 0.01/(2.0*100.0)).abs() < 1e-14);  // v_c = kΦ/(2aH)
    }

    #[test]
    fn test_expand_phi() {
        let tca = TCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5 };
        let y = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 0.0, 1.0, 6, 4);
        assert_eq!(y[y.len()-1], 1.0);  // Φ at end
    }

    #[test]
    fn test_expand_flrw_limit() {
        // σ_h = 0 → F₂ is pure streaming slip, no shear contribution
        let tca = TCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5 };
        let y_flrw = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 0.0, 1.0, 6, 4);
        let y_bianchi = expand_tca_to_full(&tca, 0.01, 100.0, 1e4, 1e-3, 1.0, 6, 4);
        // Only F₂ should differ (shear slip term)
        assert_eq!(y_flrw[0], y_bianchi[0]);
        assert_eq!(y_flrw[1], y_bianchi[1]);
        assert!(y_flrw[2] != y_bianchi[2]); // F₂ differs
        assert_eq!(y_flrw[y_flrw.len()-1], y_bianchi[y_bianchi.len()-1]);
    }
}
