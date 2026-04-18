// BE-05c: Visibility function, Thomson opacity, and derived observables.
//
// Chain: EMLA x_e(z) → κ̇(η) → τ(η) → g(η) = κ̇ e^{−τ}
// Derived: z_*, Δz (LSS width), r_s(z_*) (sound horizon), τ_reio.
//
// CONFORMAL TIME:
//   η [Mpc] = ∫_0^z c dz' / H(z')
//   Derivation: dt = −dz/((1+z)H), dη = dt/a = (1+z)dt = −dz/H
//   ⟹ dη = c dz / H(z) when η in distance units [Mpc]
//
// OPACITY:
//   κ̇ [Mpc⁻¹] = n_e σ_T a × Mpc_m = x_e n_{H,0} σ_T (1+z)² × Mpc_m
//
// SOUND HORIZON:
//   r_s(z_*) = ∫_{z_*}^∞ c_s(z) c dz / H(z)  [Mpc]
//   c_s = c/√(3(1+R)),  R = 3Ω_b/(4Ω_γ(1+z))

use crate::core::math::{natural_cubic_second_derivatives, cubic_spline_eval};
use super::hyrec_tables::HyRecTables;
use super::hyrec_emla;

const SIGMA_T: f64 = 6.6524587321e-29;
const C_LIGHT: f64 = 2.99792458e8;
const MPC_M: f64 = 3.085677581e22;
const M_P: f64 = 1.67262192e-27;
const Y_P: f64 = 0.2454;
const F_HE: f64 = 0.0813;
const N_EFF: f64 = 3.044;

/// Cosmological parameters.
#[derive(Clone, Debug)]
pub(crate) struct VisibilityParams {
    pub(crate) h: f64,
    pub(crate) omega_b: f64,
    pub(crate) omega_m: f64,
    pub(crate) omega_r: f64,
    pub(crate) omega_l: f64,
    pub(crate) t_cmb: f64,
    pub(crate) z_reio: f64,
    pub(crate) delta_z_reio: f64,
}

impl VisibilityParams {
    pub(crate) fn planck2018() -> Self {
        Self {
            h: 0.6736, omega_b: 0.04930, omega_m: 0.3153,
            omega_r: 9.14e-5, omega_l: 0.6847, t_cmb: 2.7255,
            z_reio: 7.67, delta_z_reio: 0.5,
        }
    }
    fn h0_si(&self) -> f64 { self.h * 100.0e3 / MPC_M }
    fn n_h0(&self) -> f64 {
        let rho_c = 3.0 * self.h0_si().powi(2) / (8.0 * std::f64::consts::PI * 6.674e-11);
        (1.0 - Y_P) * self.omega_b * rho_c / M_P
    }
    pub(crate) fn omega_gamma(&self) -> f64 { self.omega_r / (1.0 + 0.2271 * N_EFF) }
    pub(crate) fn e_of_z(&self, z: f64) -> f64 {
        let a = 1.0 / (1.0 + z);
        let a2 = a * a;
        (self.omega_r / (a2 * a2) + self.omega_m / (a2 * a) + self.omega_l).max(1e-30).sqrt()
    }
    fn hubble(&self, z: f64) -> f64 { self.h0_si() * self.e_of_z(z) }
}

/// Full visibility result.
#[derive(Clone, Debug)]
pub(crate) struct VisibilityResult {
    pub(crate) z_grid: Vec<f64>,
    pub(crate) eta_grid: Vec<f64>,
    pub(crate) xe_grid: Vec<f64>,
    pub(crate) kappa_dot_grid: Vec<f64>,
    pub(crate) tau_grid: Vec<f64>,
    pub(crate) g_grid: Vec<f64>,
    pub(crate) z_star: f64,
    pub(crate) delta_z: f64,
    pub(crate) r_s: f64,
    pub(crate) tau_reio: f64,
    pub(crate) g_norm: f64,
}

/// Tanh reionization model.
pub(crate) fn reionization_xe(z: f64, z_re: f64, dz: f64) -> f64 {
    let f = 1.0 + F_HE;
    let y = (1.0 + z).powf(1.5);
    let yr = (1.0 + z_re).powf(1.5);
    let dy = 1.5 * (1.0 + z_re).sqrt() * dz;
    f * 0.5 * (1.0 - ((y - yr) / dy).tanh())
}

/// Compute visibility function from EMLA recombination.
///
/// PRE-03: Extended to z_max_ext for sub-horizon k-modes.
/// EMLA recombination is computed for z=0..4000 where it matters.
/// For z > 4000: Saha equilibrium (x_e ≈ 1, fully ionized).
/// The high-z extension ensures k/(aH) ≪ 1 at z_max for all k ≤ 0.25.
pub(crate) fn compute_visibility(
    p: &VisibilityParams,
    tables: &HyRecTables,
    n: usize,
) -> VisibilityResult {
    compute_visibility_ext(p, tables, n, 50000.0)
}

/// Extended visibility with configurable z_max.
/// z_max_ext > 4000 extends the grid using Saha equilibrium.
pub(crate) fn compute_visibility_ext(
    p: &VisibilityParams,
    tables: &HyRecTables,
    n_recomb: usize,
    z_max_ext: f64,
) -> VisibilityResult {
    let z_max_emla = 4000.0_f64;
    let h0 = p.h0_si();
    let n_h0 = p.n_h0();
    let og = p.omega_gamma();

    // Step 1: HyRec EMLA2s2p recombination (Ali-Haïmoud & Hirata 2011)
    // Replaces simple Peebles/emla4 with effective multilevel atom rates
    let (z_emla_vec, xe_emla_vec, _tm_vec) = hyrec_emla::compute_recombination_history(
        p.h, p.t_cmb, p.omega_b, p.omega_m, p.omega_r, p.omega_l, Y_P,
        80000,
    );
    let n_emla = z_emla_vec.len();
    let z_emla = &z_emla_vec;
    let xe_emla = &xe_emla_vec;

    // Step 2: Build z grid
    // Dense in [0, 4000] (n_recomb points), log-sparse in [4000, z_max_ext]
    let z_max = z_max_ext.max(z_max_emla);
    let n_ext = if z_max > z_max_emla + 1.0 {
        // ~20 points per decade above z=4000
        let decades = (z_max / z_max_emla).log10();
        (decades * 20.0).ceil() as usize
    } else { 0 };
    let n_total = n_recomb + n_ext;

    let dz_recomb = z_max_emla / (n_recomb - 1).max(1) as f64;
    let mut z_g = Vec::with_capacity(n_total + n_recomb); // extra capacity for refinement
    // Dense region: z=0 to z=4000
    for i in 0..n_recomb {
        z_g.push(i as f64 * dz_recomb);
    }
    // Recombination refinement: insert midpoints in z=800..1300
    // This doubles resolution where visibility peaks (tight-coupling → free-streaming transition)
    {
        let mut extra = Vec::new();
        for i in 1..z_g.len() {
            let z_mid = 0.5 * (z_g[i - 1] + z_g[i]);
            if z_mid > 800.0 && z_mid < 1300.0 {
                extra.push(z_mid);
            }
        }
        z_g.extend(extra);
        z_g.sort_by(|a, b| a.partial_cmp(b).unwrap());
        z_g.dedup_by(|a, b| (*a - *b).abs() < 1e-6);
    }
    // Extended region: z=4000 to z_max (log-spaced)
    if n_ext > 0 {
        let log_start = z_max_emla.ln();
        let log_end = z_max.ln();
        for i in 1..=n_ext {
            let frac = i as f64 / n_ext as f64;
            z_g.push((log_start + frac * (log_end - log_start)).exp());
        }
    }
    let n = z_g.len();

    // Step 3: Interpolate x_e onto grid
    // For z ≤ z_max_emla: from HyRec EMLA. For z > z_max_emla: Saha
    let mut xe_g = Vec::with_capacity(n);
    for &z in &z_g {
        let xr = if z <= z_max_emla && z <= z_emla[0] {
            // Binary search in z_emla (descending order)
            let mut lo = 0usize;
            let mut hi = n_emla - 1;
            // z_emla is descending: z_emla[0] is largest
            if z >= z_emla[0] {
                xe_emla[0]
            } else if z <= z_emla[n_emla - 1] {
                xe_emla[n_emla - 1]
            } else {
                // Find bracket: z_emla[lo] > z >= z_emla[hi] 
                while hi - lo > 1 {
                    let mid = (lo + hi) / 2;
                    if z_emla[mid] > z { lo = mid; } else { hi = mid; }
                }
                let w = (z_emla[lo] - z) / (z_emla[lo] - z_emla[hi]).max(1e-30);
                xe_emla[lo] + w * (xe_emla[hi] - xe_emla[lo])
            }
        } else {
            1.0 + Y_P / (4.0 * (1.0 - Y_P))
        };
        let xreio = reionization_xe(z, p.z_reio, p.delta_z_reio);
        xe_g.push(xr.max(xreio));
    }

    // Step 4: κ̇ [Mpc⁻¹] = x_e n_{H,0} σ_T (1+z)² × MPC_M
    let kd_g: Vec<f64> = z_g.iter().zip(xe_g.iter())
        .map(|(&z, &xe)| xe * n_h0 * SIGMA_T * (1.0 + z).powi(2) * MPC_M)
        .collect();

    // Step 5: η(z) [Mpc] = ∫_0^z c dz' / H(z')
    // Sub-step any interval with dz > 0.1 for accurate integration.
    // Critical at z<10 where c/H varies from 4451 to ~3000 Mpc/unit-z.
    let mut eta_g = vec![0.0; n];
    for i in 1..n {
        let dz_total = z_g[i] - z_g[i - 1];
        let nsub = ((dz_total / 0.1).ceil() as usize).max(1);
        let dz_sub = dz_total / nsub as f64;
        let mut acc = 0.0_f64;
        for j in 0..nsub {
            let zm = z_g[i - 1] + (j as f64 + 0.5) * dz_sub;
            let hm = p.hubble(zm);
            acc += C_LIGHT * dz_sub / hm / MPC_M;
        }
        eta_g[i] = eta_g[i - 1] + acc;
    }

    // Step 6: τ(z) = ∫_0^z κ̇ dη' (trapezoidal)
    let mut tau_g = vec![0.0; n];
    for i in 1..n {
        let de = eta_g[i] - eta_g[i - 1];
        tau_g[i] = tau_g[i - 1] + 0.5 * (kd_g[i] + kd_g[i - 1]) * de;
    }

    // Step 7: g(z) = κ̇ e^{−τ}
    let g_g: Vec<f64> = kd_g.iter().zip(tau_g.iter())
        .map(|(&k, &t)| k * (-t).exp())
        .collect();

    // Step 8: z_* = argmax(g)
    let (mut z_star, mut g_max) = (0.0, 0.0_f64);
    for i in 0..n {
        if g_g[i] > g_max { g_max = g_g[i]; z_star = z_g[i]; }
    }

    // Step 9: Δz (FWHM)
    let hm = g_max * 0.5;
    let mut z_lo = z_star;
    let mut z_hi = z_star;
    for i in 0..n {
        if z_g[i] <= z_star && g_g[i] >= hm { z_lo = z_g[i]; break; }
    }
    for i in (0..n).rev() {
        if z_g[i] >= z_star && g_g[i] >= hm { z_hi = z_g[i]; break; }
    }
    let delta_z = z_hi - z_lo;

    // Step 10: r_s(z_*) = ∫_{z_*}^{z_max} c_s c dz / H(z) [Mpc]
    let mut r_s = 0.0;
    for i in 1..n {
        if z_g[i] <= z_star { continue; }
        let dz = z_g[i] - z_g[i - 1];
        let zm = 0.5 * (z_g[i] + z_g[i - 1]);
        if zm < z_star { continue; }
        let r = 3.0 * p.omega_b / (4.0 * og * (1.0 + zm));
        let cs = 1.0 / (3.0 * (1.0 + r)).sqrt();
        let hm_val = p.hubble(zm);
        r_s += cs * C_LIGHT * dz / hm_val / MPC_M;
    }

    // Step 11: ∫g dη
    let mut g_norm = 0.0;
    for i in 1..n {
        let de = eta_g[i] - eta_g[i - 1];
        g_norm += 0.5 * (g_g[i] + g_g[i - 1]) * de;
    }

    // Step 12: τ_reio
    let i_reio = z_g.iter().position(|&z| z >= p.z_reio).unwrap_or(0);
    let tau_reio = tau_g[i_reio];

    VisibilityResult {
        z_grid: z_g, eta_grid: eta_g, xe_grid: xe_g,
        kappa_dot_grid: kd_g, tau_grid: tau_g, g_grid: g_g,
        z_star, delta_z, r_s, tau_reio, g_norm,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run() -> VisibilityResult {
        let t = HyRecTables::generate(300);
        compute_visibility(&VisibilityParams::planck2018(), &t, 50000)
    }

    #[test] fn test_runs() { let v = run(); assert!(v.z_grid.len() >= 50000); }

    #[test] fn test_eta_total() {
        let v = run();
        let e = *v.eta_grid.last().unwrap();
        assert!(e > 10000.0 && e < 20000.0, "η = {:.0} Mpc", e);
    }

    #[test] fn test_tau_large() {
        let v = run();
        let t = *v.tau_grid.last().unwrap();
        assert!(t > 50.0, "τ(z_max) = {:.1}", t);
    }

    #[test] fn test_tau_monotonic() {
        let v = run();
        for i in 1..v.tau_grid.len() { assert!(v.tau_grid[i] >= v.tau_grid[i-1] - 1e-10); }
    }

    #[test] fn test_g_positive() {
        let v = run();
        for &g in &v.g_grid { assert!(g >= 0.0); }
    }

    #[test] fn test_g_norm() {
        let v = run();
        assert!((v.g_norm - 1.0).abs() < 0.05, "∫g = {:.6}", v.g_norm);
    }

    #[test] fn test_z_star() {
        let v = run();
        assert!(v.z_star > 1050.0 && v.z_star < 1200.0, "z_* = {:.1}", v.z_star);
    }

    #[test] fn test_delta_z() {
        let v = run();
        assert!(v.delta_z > 30.0 && v.delta_z < 300.0, "Δz = {:.1}", v.delta_z);
    }

    #[test] fn test_sound_horizon() {
        let v = run();
        assert!(v.r_s > 70.0 && v.r_s < 200.0, "r_s = {:.1}", v.r_s);
    }

    #[test] fn test_reionization() {
        assert!(reionization_xe(20.0, 7.67, 0.5) < 0.01);
        assert!(reionization_xe(2.0, 7.67, 0.5) > 1.0);
    }

    #[test] fn test_tau_reio() {
        let v = run();
        assert!(v.tau_reio > 0.01 && v.tau_reio < 0.3, "τ_re = {:.4}", v.tau_reio);
    }

    #[test] fn test_kd_drops() {
        let v = run();
        let n = v.kappa_dot_grid.len();
        assert!(v.kappa_dot_grid[n-1] > v.kappa_dot_grid[0] * 100.0);
    }
}
