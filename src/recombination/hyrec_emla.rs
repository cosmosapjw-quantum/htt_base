//! HyRec EMLA2s2p: Effective MultiLevel Atom with 2s/2p interface states.
//!
//! Physics from Ali-Haïmoud & Hirata (2011), Lee & Ali-Haïmoud (2020).
//! Uses pre-computed effective rates from Alpha_inf.dat and R_inf.dat
//! that encode all n≥3 cascade contributions.
//!
//! Key differences from simple Peebles/RECFAST:
//! 1. State-resolved effective rates α_{2s}(Tm,Tr), α_{2p}(Tm,Tr) (not single α_B)
//! 2. Effective 2p↔2s transition rate R_{2p,2s}(Tr)  
//! 3. Generalized C-factors with cross-channel coupling
//! 4. Saha-subtracted formulation for numerical stability
//! 5. β from detailed balance at Tr (thermodynamic consistency)
//!
//! Future extension (anisotropic_recombination.md §10):
//!   - Replace scalar H → directional Ξ_∥(ê) = Θ/3 + σ_{ab}ê^aê^b
//!   - Replace scalar P_esc → directional escape operator
//!   - Atomic rates (α, β, R2p2s) remain geometry-blind

use super::hyrec_emla_tables::*;

// ═══ Physical constants (CGS + eV, matching HyRec convention) ═══
const EI: f64 = 13.598286071938324;       // H ionization energy [eV]
const KBOLTZ: f64 = 8.617343e-5;          // Boltzmann constant [eV/K]
const L2S1S: f64 = 8.2206;               // 2s→1s two-photon rate [s⁻¹]
const SAHA_FACT: f64 = 3.016103031869581e21; // (2πμ_e EI)^{3/2}/h³ [eV^{-3/2} cm⁻³]
const LYA_FACT: f64 = 4.662899067555897e15;  // 8π/(3λ_Lyα³) [cm⁻³]
const SIGMA_T: f64 = 6.6524587321e-29;    // Thomson cross section [m²]  
const SIGMA_T_CGS: f64 = 6.6524587321e-25; // [cm²]
const A_RAD_CGS: f64 = 7.5657e-15;        // radiation constant [erg/(cm³·K⁴)]
const ME_CGS: f64 = 9.1093837015e-28;     // electron mass [g]
const C_CGS: f64 = 2.99792458e10;         // speed of light [cm/s]
const MPC_M: f64 = 3.085677581e22;        // Mpc in meters

/// Cubic interpolation coefficients (HyRec convention).
fn cubic4(frac: f64) -> [f64; 4] {
    [frac * (frac - 1.0) * (2.0 - frac) / 6.0,
     (1.0 + frac) * (1.0 - frac) * (2.0 - frac) / 2.0,
     (1.0 + frac) * frac * (2.0 - frac) / 2.0,
     (1.0 + frac) * frac * (frac - 1.0) / 6.0]
}

/// Interpolated effective rates from HyRec tables.
pub(crate) struct EffectiveRates {
    pub alpha: [f64; 2],    // α_{2s}, α_{2p} [cm³/s]
    pub dalpha: [f64; 2],   // α(Tm,Tr) - α(Tr,Tr)
    pub beta: [f64; 2],     // β_{2s}, β_{2p} [s⁻¹]
    pub r2p2s: f64,         // R_{2p→2s} [s⁻¹]
}

/// Interpolate effective rates at given (Tr, Tm) in eV.
pub(crate) fn interpolate_rates(tr_ev: f64, tm_ev: f64) -> EffectiveRates {
    let mut tm_tr = tm_ev / tr_ev;
    let i_off = if tm_tr > 1.0 { tm_tr = 1.0 / tm_tr; 2 } else { 0 };
    let t_ratio = tm_tr.clamp(HYREC_T_RATIO_MIN, 1.0);
    let tr_clamped = tr_ev.clamp(HYREC_TR_MIN, HYREC_TR_MAX);
    
    let log_tr = tr_clamped.ln();
    let dlog_tr = (HYREC_TR_MAX.ln() - HYREC_TR_MIN.ln()) / (HYREC_NTR as f64 - 1.0);
    let dt_ratio = (1.0 - HYREC_T_RATIO_MIN) / (HYREC_NTM as f64 - 1.0);
    
    // TR interpolation
    let itr_f = (log_tr - HYREC_TR_MIN.ln()) / dlog_tr;
    let itr = (itr_f as usize).max(1).min(HYREC_NTR - 3);
    let c2 = cubic4(itr_f - itr as f64);
    
    // TM/TR interpolation
    let itm_f = (t_ratio - HYREC_T_RATIO_MIN) / dt_ratio;
    let itm = (itm_f as usize).max(1).min(HYREC_NTM - 3);
    let c1 = cubic4(itm_f - itm as f64);
    
    let mut rates = EffectiveRates {
        alpha: [0.0; 2], dalpha: [0.0; 2], beta: [0.0; 2], r2p2s: 0.0,
    };
    
    let tables: [&[f64]; 4] = [
        &HYREC_LOG_ALPHA_2S_TM_LE_TR,
        &HYREC_LOG_ALPHA_2P_TM_LE_TR,
        &HYREC_LOG_ALPHA_2S_TM_GT_TR,
        &HYREC_LOG_ALPHA_2P_TM_GT_TR,
    ];
    
    for l in 0..2 {
        // Alpha at Tm=Tr (equilibrium): use last TM row (T_RATIO=1)
        let alpha_eq = {
            let mut s = 0.0;
            for k in 0..4 {
                s += c2[k] * tables[l][(HYREC_NTM - 1) * HYREC_NTR + itr - 1 + k];
            }
            s.exp()
        };
        
        // Beta from detailed balance at Tr
        rates.beta[l] = alpha_eq * SAHA_FACT * tr_clamped * tr_clamped.sqrt()
                        * (-0.25 * EI / tr_clamped).exp() / (2 * l + 1) as f64;
        
        // Alpha(Tm, Tr): bicubic interpolation
        let mut temp = [0.0f64; 4];
        for k in 0..4 {
            for j in 0..4 {
                temp[k] += c2[j] * tables[l + i_off][(itm - 1 + k) * HYREC_NTR + itr - 1 + j];
            }
        }
        let mut log_alpha = 0.0;
        for k in 0..4 { log_alpha += c1[k] * temp[k]; }
        rates.alpha[l] = log_alpha.exp();
        rates.dalpha[l] = rates.alpha[l] - alpha_eq;
    }
    
    // R_{2p→2s}
    let mut log_r = 0.0;
    for k in 0..4 { log_r += c2[k] * HYREC_LOG_R2P2S[itr - 1 + k]; }
    rates.r2p2s = log_r.exp();
    
    rates
}

/// HyRec EMLA2s2p RHS: d(xHII)/d(ln a).
///
/// Inputs: xe (total free electron fraction), xHII (H ionized fraction),
///         nH [cm⁻³], H [s⁻¹], TM [eV], TR [eV].
///
/// Uses the Saha-subtracted form for numerical stability:
///   Dxe2 = xe·xHII − s·(1−xHII)  where s = Saha equilibrium
pub(crate) fn hmla_dxhii_dlna(xe: f64, x_hii: f64, n_h: f64, h_rate: f64,
                               tm_ev: f64, tr_ev: f64) -> f64 {
    let rates = interpolate_rates(tr_ev, tm_ev);
    
    let r_lya = LYA_FACT * h_rate / n_h / (1.0 - x_hii).max(1e-30);
    
    let gamma_2s = rates.beta[0] + 3.0 * rates.r2p2s + L2S1S;
    let gamma_2p = rates.beta[1] + rates.r2p2s + r_lya;
    
    let denom_s = gamma_2s - 3.0 * rates.r2p2s * rates.r2p2s / gamma_2p;
    let denom_p = gamma_2p - 3.0 * rates.r2p2s * rates.r2p2s / gamma_2s;
    
    if denom_s.abs() < 1e-30 || denom_p.abs() < 1e-30 { return 0.0; }
    
    let c2s = (L2S1S + 3.0 * rates.r2p2s * r_lya / gamma_2p) / denom_s;
    let c2p = (r_lya + rates.r2p2s * L2S1S / gamma_2s) / denom_p;
    
    let s = SAHA_FACT * tr_ev * tr_ev.sqrt() * (-EI / tr_ev).exp() / n_h;
    let dxe2 = xe * x_hii - s * (1.0 - x_hii);
    
    -n_h / h_rate * ((s * (1.0 - x_hii) * rates.dalpha[0] + rates.alpha[0] * dxe2) * c2s
                   + (s * (1.0 - x_hii) * rates.dalpha[1] + rates.alpha[1] * dxe2) * c2p)
}

/// Hydrogen Saha equilibrium xHII.
pub(crate) fn saha_xhii(n_h: f64, tr_ev: f64) -> f64 {
    let s = SAHA_FACT * tr_ev * tr_ev.sqrt() * (-EI / tr_ev).exp() / n_h;
    if s > 1e10 { return 1.0; }
    if s < 1e-30 { return 0.0; }
    (-s + (s * s + 4.0 * s).sqrt()) / 2.0
}

/// Compute recombination history using HyRec EMLA2s2p physics.
///
/// Integration: Saha tracking → Rodas5P adaptive (4th order, L-stable).
/// Tm=Tr approximation (Compton coupling, <1% for z>800).
///
/// Returns (z_grid descending, xe_grid, tm_grid)
pub(crate) fn compute_recombination_history(
    h: f64, t0_k: f64, omega_b: f64, omega_m: f64, omega_r: f64, omega_l: f64,
    y_he: f64, _n_steps: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    use crate::solver::nonlinear_rodas5p::{ScalarOde, integrate_scalar_adaptive};
    use crate::core::config::Rodas5PConfig;
    
    let f_he = y_he / (4.0 * (1.0 - y_he));
    let mpc_cm = MPC_M * 100.0;
    let h0_cgs = h * 1.0e7 / mpc_cm;
    let rho_crit = 3.0 * h0_cgs * h0_cgs / (8.0 * std::f64::consts::PI * 6.674e-8);
    let n_h0 = (1.0 - y_he) * omega_b * rho_crit / 1.6726e-24;
    let he_xe = |z: f64| -> f64 {
        f_he * (0.5 * (1.0 + ((z - 1600.0) / 200.0).tanh())).max(0.0)
    };
    
    // Phase 1: Saha tracking
    let z_start = 3400.0_f64;
    let dlna_saha = 4e-3_f64;
    let mut z_hist = Vec::with_capacity(4000);
    let mut xe_hist = Vec::with_capacity(4000);
    let mut tm_hist = Vec::with_capacity(4000);
    let mut x_hii = 1.0_f64;
    let mut tm_k = t0_k * (1.0 + z_start);
    let mut z = z_start;
    z_hist.push(z); xe_hist.push(x_hii + he_xe(z)); tm_hist.push(tm_k);
    
    let mut z_saha_exit = z_start;
    while z > 0.0 {
        let z_next = ((1.0 + z) * (-dlna_saha).exp() - 1.0).max(0.0);
        let n_h = n_h0 * (1.0 + z).powi(3);
        let tr_ev = KBOLTZ * t0_k * (1.0 + z);
        let x_saha = saha_xhii(n_h, tr_ev);
        if x_saha < 0.995 { z_saha_exit = z; x_hii = x_saha; break; }
        x_hii = saha_xhii(n_h0*(1.0+z_next).powi(3), KBOLTZ*t0_k*(1.0+z_next));
        tm_k = t0_k * (1.0 + z_next);
        z = z_next;
        z_hist.push(z); xe_hist.push(x_hii + he_xe(z)); tm_hist.push(tm_k);
    }
    
    // Phase 2: Two-stage ODE integration
    // Phase 2a (z>200): 1-DOF Rodas5P (xHII only) with Tm = Tm_steady_state
    //   Tm_ss captures Compton cooling without stiff ODE:
    //   Tm_ss = Tr × Γ_C_ratio / (Γ_C_ratio + 2)  where Γ_C_ratio = Γ_C × xe/(1+fHe+xe) / H
    // Phase 2b (z<200): freeze xe, evolve Tm separately (Compton decoupling)
    
    struct Hmla1Dof {
        n_h0: f64, h0_cgs: f64, t0_k: f64,
        or_: f64, om: f64, ol: f64, f_he: f64,
    }
    
    impl Hmla1Dof {
        fn hz(&self, z: f64) -> f64 {
            let a = 1.0 / (1.0 + z);
            self.h0_cgs * (self.or_/(a*a*a*a) + self.om/(a*a*a) + self.ol).max(1e-30).sqrt()
        }
        /// Compton steady-state Tm [K]
        fn tm_ss(&self, z: f64, xe: f64) -> f64 {
            let tr_k = self.t0_k * (1.0 + z);
            let hv = self.hz(z);
            let gamma_c = 8.0 * SIGMA_T_CGS * A_RAD_CGS * tr_k.powi(4) / (3.0 * ME_CGS * C_CGS);
            let gc_ratio = gamma_c * xe / ((1.0 + self.f_he + xe) * hv);
            // Steady state: 0 = -2Tm + gc_ratio(Tr - Tm) → Tm = Tr × gc_ratio/(gc_ratio + 2)
            tr_k * gc_ratio / (gc_ratio + 2.0)
        }
    }
    
    impl ScalarOde for Hmla1Dof {
        fn rhs(&self, z: f64, x_hii: f64) -> f64 {
            if z < 1.0 { return 0.0; }
            let n_h = self.n_h0 * (1.0 + z).powi(3);
            let hv = self.hz(z);
            let tr_ev = (KBOLTZ * self.t0_k * (1.0 + z))
                .clamp(HYREC_TR_MIN * 1.01, HYREC_TR_MAX * 0.99);
            // Use Tm from steady-state Compton equilibrium
            let tm_k = self.tm_ss(z, x_hii);
            let tm_ev = (KBOLTZ * tm_k)
                .clamp(tr_ev * HYREC_T_RATIO_MIN * 1.01, tr_ev / HYREC_T_RATIO_MIN * 0.99);
            let dx = hmla_dxhii_dlna(x_hii, x_hii.clamp(1e-10, 1.0 - 1e-10), n_h, hv, tm_ev, tr_ev);
            -dx / (1.0 + z)
        }
        fn jac(&self, z: f64, x: f64) -> f64 {
            let eps = (x.abs() * 1e-7).max(1e-10);
            (self.rhs(z, (x+eps).min(1.0)) - self.rhs(z, (x-eps).max(1e-10))) / (2.0 * eps)
        }
        fn dfdt(&self, z: f64, x: f64) -> f64 {
            let eps = (z.abs() * 1e-7).max(0.1);
            (self.rhs(z+eps, x) - self.rhs(z-eps, x)) / (2.0 * eps)
        }
        fn clip(&self, y: f64) -> f64 { y.clamp(1e-10, 1.0) }
    }
    
    let ode = Hmla1Dof { n_h0, h0_cgs, t0_k, or_: omega_r, om: omega_m, ol: omega_l, f_he };
    let cfg = Rodas5PConfig {
        rtol: 1e-6, atol: 1e-10, h_init: Some(1.0), h_min: 1e-4, h_max: 20.0,
        max_steps: 50000, f_safety: 0.9, f_min: 0.2, f_max: 5.0, beta: 0.04,
        use_analytic_jacobian: false, use_ft_term: true,
        use_blas_lu: false, use_block_diag: false,
        ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0,
        include_pol_hint: false, use_sparse: false,
    };
    
    match integrate_scalar_adaptive(&ode, z_saha_exit, x_hii, 0.5, &cfg) {
        Ok(res) => {
            for i in 0..res.t_hist.len() {
                let zi = res.t_hist[i];
                let xi = res.y_hist[i];
                let tmi = ode.tm_ss(zi, xi);
                z_hist.push(zi); xe_hist.push(xi + he_xe(zi)); tm_hist.push(tmi);
            }
        }
        Err(msg) => {
            eprintln!("HyRec Rodas5P failed: {}", msg);
        }
    }
    
    // Extend to z=0
    if z_hist.last().map_or(true, |&z| z > 0.1) {
        let last_xe = xe_hist.last().copied().unwrap_or(0.001);
        z_hist.push(0.0); xe_hist.push(last_xe); tm_hist.push(t0_k);
    }
    
    (z_hist, xe_hist, tm_hist)
}

/// Compute Thomson opacity κ' [Mpc⁻¹] from xe(z).
pub(crate) fn kappa_dot_from_xe(xe: f64, z: f64, n_h0_m3: f64) -> f64 {
    xe * n_h0_m3 * SIGMA_T * (1.0 + z) * (1.0 + z) * MPC_M
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_hyrec_emla_recomb() {
        let (z, xe, tm) = compute_recombination_history(
            0.6736, 2.7255, 0.04930, 0.3153, 9.14e-5, 0.6847, 0.2454, 80000,
        );
        
        // Find xe at key redshifts
        for &zc in &[1500.0, 1300.0, 1200.0, 1100.0, 1075.0, 1050.0, 1000.0, 900.0] {
            // Binary search (z is descending)
            let mut lo = 0usize; let mut hi = z.len() - 1;
            if zc > z[0] || zc < z[hi] { 
                eprintln!("  z={}: OUT OF RANGE [{}, {}]", zc, z[0], z[hi]);
                continue;
            }
            while hi - lo > 1 {
                let mid = (lo + hi) / 2;
                if z[mid] > zc { lo = mid; } else { hi = mid; }
            }
            let w = (z[lo] - zc) / (z[lo] - z[hi]).max(1e-30);
            let xe_interp = xe[lo] + w * (xe[hi] - xe[lo]);
            eprintln!("  z={:.0}: xe={:.6}", zc, xe_interp);
        }
        
        // Basic sanity
        eprintln!("  z_range: [{:.0}, {:.0}], {} points", z[0], z[z.len()-1], z.len());
        eprintln!("  xe[0]={:.4} (z={:.0}), xe[last]={:.4} (z={:.0})", 
                  xe[0], z[0], xe[xe.len()-1], z[z.len()-1]);
    }
}

    #[test]
    fn test_hmla_rhs_at_z1100() {
        // Known-good conditions from Python verification
        let h = 0.6736_f64; let t0 = 2.7255_f64; let yp = 0.2454_f64;
        let ob = 0.04930_f64; let om = 0.3153_f64;
        let mpc_cm = MPC_M * 100.0;
        let h0_cgs = h * 1e7 / mpc_cm;
        let rho_crit = 3.0 * h0_cgs * h0_cgs / (8.0 * std::f64::consts::PI * 6.674e-8);
        let n_h0 = (1.0 - yp) * ob * rho_crit / 1.6726e-24;
        
        let z = 1100.0_f64;
        let n_h = n_h0 * (1.0+z).powi(3);
        let or_ = 9.14e-5_f64; let ol = 1.0 - om - or_;
        let a = 1.0/(1.0+z);
        let h_val = h0_cgs * (or_/(a*a*a*a) + om/(a*a*a) + ol).sqrt();
        let tr_ev = KBOLTZ * t0 * (1.0+z);
        let tm_ev = tr_ev; // Tm ≈ Tr
        let xe = 0.1452_f64; // from HyRec output
        let x_hii = xe;
        
        let result = hmla_dxhii_dlna(xe, x_hii, n_h, h_val, tm_ev, tr_ev);
        
        // Python gave: dxHII/dlna = -1.510790e+00
        eprintln!("  z=1100 test:");
        eprintln!("    n_h = {:.4e}", n_h);
        eprintln!("    H   = {:.4e}", h_val);
        eprintln!("    Tr  = {:.6} eV", tr_ev);
        eprintln!("    dxHII/dlna = {:.6e}", result);
        eprintln!("    Python ref = -1.510790e+00");
        eprintln!("    ratio = {:.4}", result / (-1.510790e+00_f64));
        
        // Also test interpolated rates
        let rates = interpolate_rates(tr_ev, tm_ev);
        eprintln!("    Alpha[0] = {:.4e} (Python: 1.8947e-13)", rates.alpha[0]);
        eprintln!("    Alpha[1] = {:.4e} (Python: 4.8646e-13)", rates.alpha[1]);
        eprintln!("    Beta[0]  = {:.4e} (Python: 1.4668e+02)", rates.beta[0]);
        eprintln!("    R2p2s    = {:.4e} (Python: 7.7050e+02)", rates.r2p2s);
    }

    #[test]
    fn test_vis_peak_diagnostic() {
        use crate::recombination::visibility_hyrec::{compute_visibility, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        
        // Find visibility peak
        let mut max_g = 0.0_f64;
        let mut z_peak = 0.0_f64;
        for i in 0..vis.z_grid.len() {
            if vis.g_grid[i] > max_g {
                max_g = vis.g_grid[i];
                z_peak = vis.z_grid[i];
            }
        }
        eprintln!("  Visibility peak: g_max={:.6e} at z={:.1}", max_g, z_peak);
        eprintln!("  CAMB reference:  g_max≈0.0092 at z≈1060");
        
        // xe near recombination
        for &z in &[1100.0, 1075.0, 1050.0] {
            let mut lo = 0; let mut hi = vis.z_grid.len()-1;
            while hi - lo > 1 {
                let mid = (lo+hi)/2;
                if vis.z_grid[mid] < z { lo = mid; } else { hi = mid; }
            }
            let w = (z - vis.z_grid[lo])/(vis.z_grid[hi]-vis.z_grid[lo]).max(1e-30);
            let xe = vis.xe_grid[lo] + w*(vis.xe_grid[hi]-vis.xe_grid[lo]);
            let kd = vis.kappa_dot_grid[lo] + w*(vis.kappa_dot_grid[hi]-vis.kappa_dot_grid[lo]);
            let g = vis.g_grid[lo] + w*(vis.g_grid[hi]-vis.g_grid[lo]);
            eprintln!("  z={:.0}: xe={:.6}, kd={:.4e}, g={:.4e}", z, xe, kd, g);
        }
    }
