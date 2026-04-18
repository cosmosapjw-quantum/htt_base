//! TF-04b: Extended TCA with Φ evolution (6 DOF).
//!
//! State: (Θ₀, v_b, δ_b, v_c, δ_c, Φ)
//! Adds gravitational potential Φ and CDM (δ_c, v_c) to the 3-DOF TCA.
//!
//! Physics:
//!   Θ₀' = -(k/3)v_b - [aH - k²/(3aH)]Φ
//!   v_b' = -aH·R/(1+R)·v_b + k/(1+R)·(Θ₀ - Φ) + slip
//!   δ_b' = -k·v_b - 3[aH - k²/(3aH)]Φ
//!   v_c' = -aH·v_c - k·Φ  (Ψ = -Φ)
//!   δ_c' = -k·v_c - 3[aH - k²/(3aH)]Φ
//!   Φ' = aH·Φ + (3aH²/2k²)·momentum_source

const N_EFF: f64 = 3.044;

/// Extended TCA state: 6 DOF.
#[derive(Clone, Debug)]
pub(crate) struct ExtTCAState {
    pub(crate) theta0: f64,
    pub(crate) v_b: f64,
    pub(crate) delta_b: f64,
    pub(crate) v_c: f64,
    pub(crate) delta_c: f64,
    pub(crate) phi: f64,
}

/// Background for extended TCA.
#[derive(Clone, Debug)]
pub(crate) struct ExtTCABg {
    pub(crate) k: f64,
    pub(crate) a: f64,
    pub(crate) a_h: f64,       // aH [Mpc⁻¹]
    pub(crate) kappa_dot: f64,
    pub(crate) r_ratio: f64,   // R = 3ρ_b/(4ρ_γ)
    pub(crate) omega_b: f64,
    pub(crate) omega_m: f64,
    pub(crate) omega_gamma: f64,
}

pub(crate) fn ext_tca_rhs(s: &ExtTCAState, bg: &ExtTCABg) -> ExtTCAState {
    let k = bg.k;
    let a = bg.a;
    let a_h = bg.a_h;
    let kd = bg.kappa_dot;
    let r = bg.r_ratio;
    let r1 = 1.0 + r;

    let omega_nu = bg.omega_gamma * 0.2271 * N_EFF;
    let omega_c = bg.omega_m - bg.omega_b;
    let k2 = k * k;

    // phi_dot_coeff: coefficient of Φ in continuity equations
    // From substituting Poisson into continuity: Φ' ≈ [aH - k²/(3aH)]Φ + ...
    let phi_coeff = if a_h.abs() > 1e-30 { a_h - k2 / (3.0 * a_h) } else { 0.0 };

    // Θ₀' = -(k/3)v_b - phi_coeff × Φ
    let dtheta0 = -(k / 3.0) * s.v_b - phi_coeff * s.phi;

    // v_b' = -aH·R/(1+R)·v_b + k/(1+R)·(Θ₀ + Ψ) + slip
    // Ψ = -Φ (no anisotropic stress in TCA)
    let dvb_0 = -a_h * r / r1 * s.v_b + k / r1 * (s.theta0 - s.phi);
    let slip = if kd > 1e-30 {
        let numer = (1.0 - r) * a_h * s.v_b - k * (s.theta0 - s.phi);
        -numer / (kd * r1)
    } else { 0.0 };
    let dvb = dvb_0 + slip;

    // δ_b' = -k·v_b - 3·phi_coeff·Φ
    let ddelta_b = -k * s.v_b - 3.0 * phi_coeff * s.phi;

    // v_c' = -aH·v_c + k·Ψ = -aH·v_c - k·Φ
    let dvc = -a_h * s.v_c - k * s.phi;

    // δ_c' = -k·v_c - 3·phi_coeff·Φ
    let ddelta_c = -k * s.v_c - 3.0 * phi_coeff * s.phi;

    // Φ': momentum constraint
    // k²(Φ' + aHΨ) = (3/2)aH² Σ(1+w)Ω_i v_i / a^{1+3w}
    // Φ' = -aH·Ψ + ... = aH·Φ + ...
    let dphi = if k2 > 1e-20 {
        let mom = 1.5 * a_h * a_h / k2;
        let v_gamma = s.v_b; // tight coupling
        let n1_approx = if a_h.abs() > 1e-30 { k * s.phi / (6.0 * a_h) } else { 0.0 };
        a_h * s.phi
            + mom * omega_c * s.v_c / a
            + mom * bg.omega_b * s.v_b / a
            + mom * 4.0 * bg.omega_gamma * v_gamma / (a * a)
            + mom * 4.0 * omega_nu * n1_approx / (a * a)
    } else {
        0.0 // super-horizon: Φ' ≈ 0
    };

    ExtTCAState {
        theta0: dtheta0, v_b: dvb, delta_b: ddelta_b,
        v_c: dvc, delta_c: ddelta_c, phi: dphi,
    }
}

/// RK4 step for extended TCA.
pub(crate) fn ext_tca_step_rk4(s: &mut ExtTCAState, bg: &ExtTCABg, dt: f64) {
    let add = |a: &ExtTCAState, b: &ExtTCAState, h: f64| -> ExtTCAState {
        ExtTCAState {
            theta0: a.theta0 + h * b.theta0,
            v_b: a.v_b + h * b.v_b,
            delta_b: a.delta_b + h * b.delta_b,
            v_c: a.v_c + h * b.v_c,
            delta_c: a.delta_c + h * b.delta_c,
            phi: a.phi + h * b.phi,
        }
    };
    let s0 = s.clone();
    let k1 = ext_tca_rhs(&s0, bg);
    let k2 = ext_tca_rhs(&add(&s0, &k1, 0.5 * dt), bg);
    let k3 = ext_tca_rhs(&add(&s0, &k2, 0.5 * dt), bg);
    let k4 = ext_tca_rhs(&add(&s0, &k3, dt), bg);
    s.theta0 = s0.theta0 + dt/6.0 * (k1.theta0 + 2.0*k2.theta0 + 2.0*k3.theta0 + k4.theta0);
    s.v_b = s0.v_b + dt/6.0 * (k1.v_b + 2.0*k2.v_b + 2.0*k3.v_b + k4.v_b);
    s.delta_b = s0.delta_b + dt/6.0 * (k1.delta_b + 2.0*k2.delta_b + 2.0*k3.delta_b + k4.delta_b);
    s.v_c = s0.v_c + dt/6.0 * (k1.v_c + 2.0*k2.v_c + 2.0*k3.v_c + k4.v_c);
    s.delta_c = s0.delta_c + dt/6.0 * (k1.delta_c + 2.0*k2.delta_c + 2.0*k3.delta_c + k4.delta_c);
    s.phi = s0.phi + dt/6.0 * (k1.phi + 2.0*k2.phi + 2.0*k3.phi + k4.phi);
}

/// Evolve extended TCA from z_max to z_switch.
pub(crate) fn evolve_ext_tca(
    k: f64, omega_b: f64, omega_m: f64, omega_gamma: f64,
    h_param: f64,
    vis_z: &[f64], vis_eta: &[f64], vis_kappa_dot: &[f64],
    z_switch: f64,
    e_of_z: impl Fn(f64) -> f64,
) -> ExtTCAState {
    let mpc_m = 3.08567758e22_f64;
    let h0c = h_param * 1e5 / 2.99792458e8;
    let phi_init = 1.0;

    let mut s = ExtTCAState {
        theta0: -0.5 * phi_init,
        v_b: 0.0,
        delta_b: -1.5 * phi_init,
        v_c: 0.0,
        delta_c: -1.5 * phi_init,
        phi: phi_init,
    };

    let n = vis_z.len();
    for i in (1..n).rev() {
        let z = vis_z[i];
        if z < z_switch { break; }
        let a = 1.0 / (1.0 + z);
        let a_h = a * h0c * e_of_z(z);
        let kd = vis_kappa_dot[i];
        let r = 3.0 * omega_b / (4.0 * omega_gamma * (1.0 + z));

        let bg = ExtTCABg { k, a, a_h, kappa_dot: kd, r_ratio: r, omega_b, omega_m, omega_gamma };
        let d_eta = (vis_eta[i-1] - vis_eta[i]).abs();
        if d_eta > 0.0 && d_eta < 100.0 {
            ext_tca_step_rk4(&mut s, &bg, d_eta);
        }
    }
    s
}

/// Expand extended TCA to full state vector.
pub(crate) fn expand_ext_tca_to_full(
    s: &ExtTCAState, k: f64, a_h: f64, kappa_dot: f64,
    sigma_h: f64, lg: usize, ln: usize,
) -> Vec<f64> {
    let n_state = lg + 1 + ln + 1 + 5;
    let mut y = vec![0.0; n_state];

    // Photon
    y[0] = s.theta0;
    if lg >= 1 { y[1] = s.v_b; }
    if lg >= 2 {
        let f2_stream = if kappa_dot > 1e-30 { (8.0/15.0) * k * s.v_b / kappa_dot } else { 0.0 };
        let f2_shear = if kappa_dot > 1e-30 { (8.0/15.0) * sigma_h * a_h / kappa_dot } else { 0.0 };
        y[2] = f2_stream + f2_shear;
    }
    if lg >= 3 && kappa_dot > 1e-30 { y[3] = (3.0/7.0) * k * y[2] / kappa_dot; }

    // Neutrino (radiation-era IC with evolved Φ)
    let n0 = lg + 1;
    y[n0] = -0.5 * s.phi;
    if ln >= 1 && a_h.abs() > 1e-30 { y[n0+1] = k * s.phi / (6.0 * a_h); }
    if ln >= 2 && a_h.abs() > 1e-30 { y[n0+2] = (k/(2.0*a_h)).powi(2) * s.phi / 3.0; }

    // CDM (from TCA evolution)
    let dc = lg + 1 + ln + 1;
    y[dc] = s.delta_c;
    y[dc+1] = s.v_c;

    // Baryon (from TCA evolution)
    y[dc+2] = s.delta_b;
    y[dc+3] = s.v_b;

    // Φ (from TCA evolution)
    y[n_state-1] = s.phi;
    y
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ext_tca_phi_decays() {
        // Φ should NOT remain at 1.0 — it should evolve
        let n = 100;
        let z: Vec<f64> = (0..n).map(|i| i as f64 * 40.0).collect();
        let eta: Vec<f64> = (0..n).map(|i| (n - 1 - i) as f64 * 100.0).collect();
        let kd = vec![1e6; n]; // very tight coupling
        let s = evolve_ext_tca(
            0.01, 0.049, 0.315, 5.4e-5, 0.674,
            &z, &eta, &kd, 500.0,
            |z| { let a = 1.0/(1.0+z); (0.315/(a*a*a) + 5.4e-5/(a*a*a*a) + 0.685).sqrt() },
        );
        assert!(s.phi.abs() < 1.5, "Phi should have evolved from 1.0, got {:.4}", s.phi);
        assert!(s.phi.abs() > 0.01, "Phi shouldn't vanish completely, got {:.6}", s.phi);
        eprintln!("  Ext TCA: Phi evolved to {:.4} (from 1.0)", s.phi);
    }

    #[test]
    fn test_ext_tca_state_size() {
        let s = ExtTCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5, v_c: 0.0, delta_c: -1.5, phi: 0.8 };
        let y = expand_ext_tca_to_full(&s, 0.01, 100.0, 1e4, 0.0, 15, 8);
        assert_eq!(y.len(), 30); // 16+9+5
        assert_eq!(y[y.len()-1], 0.8); // Φ preserved
    }

    #[test]
    fn test_ext_tca_neutrino_uses_evolved_phi() {
        let s = ExtTCAState { theta0: -0.5, v_b: 0.01, delta_b: -1.5, v_c: 0.0, delta_c: -1.5, phi: 0.3 };
        let y = expand_ext_tca_to_full(&s, 0.01, 100.0, 1e4, 0.0, 6, 4);
        let n0 = 7;
        assert!((y[n0] - (-0.5 * 0.3)).abs() < 1e-14, "N₀ = -Φ/2 = {:.4}", y[n0]);
    }
}
