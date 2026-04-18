// Peebles recombination and scalar Rodas5P.

use crate::core::constants::*;
use crate::core::config::*;
use crate::core::math::*;
use crate::core::controller::*;

pub(crate) fn saha_ratio(t: f64, chi_ev: f64) -> f64 {
    let thermal = (M_E * K_B * t / (2.0 * std::f64::consts::PI * HBAR * HBAR)).powf(1.5);
    thermal * (-chi_ev / (K_B_EV * t)).exp()
}

pub(crate) fn helium_contribution(_t_cmb: f64, _n_h_0: f64, z: f64, _x_e_h: f64) -> f64 {
    let f_he = Y_P / (4.0 * X_P);
    let heiii = 0.5 * (1.0 + ((z - 5000.0) / 600.0).tanh());
    let heii_or_more = 0.5 * (1.0 + ((z - 1850.0) / 120.0).tanh());
    f_he * heii_or_more + f_he * heiii
}

pub(crate) fn reionization_fraction(z: f64, z_re: f64, delta_z: f64) -> f64 {
    let dz = delta_z.abs().max(1e-12);
    let y = (1.0 + z_re).powf(1.5) - (1.0 + z).powf(1.5);
    let denom = 1.5 * (1.0 + z_re).sqrt() * dz;
    0.5 * (1.0 + (y / denom.max(1e-12)).tanh())
}

pub(crate) fn critical_density(h0_si: f64) -> f64 {
    3.0 * h0_si * h0_si / (8.0 * std::f64::consts::PI * G_N)
}

pub(crate) fn n_h0_from_params(h0_si: f64, omega_b: f64) -> f64 {
    X_P * critical_density(h0_si) * omega_b / M_P
}

pub(crate) fn h_of_z(params: &PeeblesParams, z: f64) -> f64 {
    let zp1 = 1.0 + z;
    let e2 = params.omega_r * zp1.powi(4)
        + params.omega_m * zp1.powi(3)
        + params.omega_k * zp1.powi(2)
        + params.omega_lambda;
    params.h0_si * e2.max(1e-300).sqrt()
}

pub(crate) fn t_of_z(params: &PeeblesParams, z: f64) -> f64 {
    params.t_cmb * (1.0 + z)
}

pub(crate) fn n_h_of_z(params: &PeeblesParams, z: f64) -> f64 {
    params.n_h_0 * (1.0 + z).powi(3)
}

pub(crate) fn alpha_b(t: f64) -> f64 {
    let tt = t / 1e4;
    let a_coeff = 4.309;
    let b_coeff = -0.6166;
    let c_coeff = 0.6703;
    let d_coeff = 0.5300;
    let f = 1.14;
    f * 1e-19 * a_coeff * tt.powf(b_coeff) / (1.0 + c_coeff * tt.powf(d_coeff))
}

pub(crate) fn beta_b(t: f64) -> f64 {
    let alpha = alpha_b(t);
    let thermal = (M_E * K_B * t / (2.0 * std::f64::consts::PI * HBAR * HBAR)).powf(1.5);
    alpha * thermal * (-B2 / (K_B_EV * t)).exp()
}

pub(crate) fn c_r(params: &PeeblesParams, z: f64, x_e: f64) -> f64 {
    let t = t_of_z(params, z);
    let beta = beta_b(t);
    let n_h = n_h_of_z(params, z);
    let h = h_of_z(params, z);
    let n_1s = ((1.0 - x_e) * n_h).max(1.0);
    let e_lya_j = E_LYA * EV_TO_J;
    let lambda_alpha = h * e_lya_j.powi(3)
        / (3.0 * std::f64::consts::PI.powi(2) * n_1s * HBAR.powi(3) * C_SI.powi(3));
    (LAMBDA_2S + lambda_alpha) / (LAMBDA_2S + lambda_alpha + beta)
}

pub(crate) fn c_r_and_dcr_dx(params: &PeeblesParams, z: f64, x_e: f64) -> (f64, f64) {
    let x = clip(x_e, 1e-15, 1.0 - 1e-12);
    let t = t_of_z(params, z);
    let beta = beta_b(t);
    let n_h = n_h_of_z(params, z);
    let h = h_of_z(params, z);
    let e_lya_j = E_LYA * EV_TO_J;
    let raw_n_1s = (1.0 - x) * n_h;
    let n_1s = raw_n_1s.max(1.0);
    let lambda_alpha = h * e_lya_j.powi(3)
        / (3.0 * std::f64::consts::PI.powi(2) * n_1s * HBAR.powi(3) * C_SI.powi(3));
    let denom = LAMBDA_2S + lambda_alpha + beta;
    let cr = (LAMBDA_2S + lambda_alpha) / denom;
    let d_lambda_dx = if raw_n_1s > 1.0 {
        lambda_alpha / (1.0 - x).max(1e-12)
    } else {
        0.0
    };
    let dcr_dx = beta * d_lambda_dx / (denom * denom).max(1e-300);
    (cr, dcr_dx)
}

pub(crate) fn rhs_peebles_scalar(params: &PeeblesParams, z: f64, x_e: f64) -> f64 {
    let x = clip(x_e, 1e-15, 1.0);
    let t = t_of_z(params, z);
    let n_h = n_h_of_z(params, z);
    let h = h_of_z(params, z);
    let k_t_ev = K_B_EV * t;
    let alpha = alpha_b(t);
    let beta = beta_b(t);
    let cr = c_r(params, z, x);
    let lya_boltz = (-E_LYA / k_t_ev).exp();
    let ionisation = beta * lya_boltz * (1.0 - x);
    let recombination = alpha * n_h * x * x;
    let net = cr * (ionisation - recombination);
    -net / ((1.0 + z) * h)
}

/// Peebles-specific initial step size estimate for the scalar Rodas5P.
/// BA-02: Moved from core/controller.rs to resolve cross-boundary dependency.
pub(crate) fn initial_step(z0: f64, y0: f64, z_end: f64, params: &PeeblesParams, cfg: &Rodas5PConfig) -> f64 {
    if let Some(h) = cfg.h_init {
        return h.abs().max(cfg.h_min).min(cfg.h_max);
    }
    let f0 = rhs_peebles_scalar(params, z0, y0);
    let sc = cfg.atol + cfg.rtol * y0.abs();
    let d0 = (y0 / sc).abs();
    let d1 = (f0 / sc).abs();
    let mut h = if d0 > 1e-10 {
        0.01 * d0 / d1.max(1e-30)
    } else {
        1e-6
    };
    h = h.min(cfg.h_max).min((z0 - z_end).abs() * 0.1);
    h.max(cfg.h_min)
}

pub(crate) fn jac_peebles_scalar_analytic(params: &PeeblesParams, z: f64, x_e: f64) -> f64 {
    let x = clip(x_e, 1e-15, 1.0 - 1e-12);
    let t = t_of_z(params, z);
    let n_h = n_h_of_z(params, z);
    let h = h_of_z(params, z);
    let k_t_ev = K_B_EV * t;
    let alpha = alpha_b(t);
    let beta = beta_b(t);
    let (cr, dcr_dx) = c_r_and_dcr_dx(params, z, x);
    let lya_boltz = (-E_LYA / k_t_ev).exp();
    let ionisation = beta * lya_boltz * (1.0 - x);
    let recombination = alpha * n_h * x * x;
    let dion_dx = -beta * lya_boltz;
    let drec_dx = 2.0 * alpha * n_h * x;
    let dnet_dx = dcr_dx * (ionisation - recombination) + cr * (dion_dx - drec_dx);
    -dnet_dx / ((1.0 + z) * h)
}

pub(crate) fn dfdz_peebles_scalar_fd(params: &PeeblesParams, z: f64, x_e: f64) -> f64 {
    let z_safe = z.abs().max(1e-6);
    let dz = (1e-6 * z_safe).max(1e-5);
    let zp = z + dz;
    let zm = (z - dz).max(0.0);
    let fp = rhs_peebles_scalar(params, zp, x_e);
    let fm = rhs_peebles_scalar(params, zm, x_e);
    (fp - fm) / (zp - zm).max(1e-15)
}

pub(crate) fn jac_peebles_scalar_fd(params: &PeeblesParams, z: f64, x_e: f64) -> f64 {
    let x_safe = x_e.abs().max(1e-8);
    let dx = (1e-6 * x_safe).max(1e-8);
    let xp = clip(x_e + dx, 1e-15, 1.0);
    let xm = clip(x_e - dx, 1e-15, 1.0);
    let fp = rhs_peebles_scalar(params, z, xp);
    let fm = rhs_peebles_scalar(params, z, xm);
    (fp - fm) / (xp - xm).max(1e-15)
}

pub(crate) fn x_e_saha_h(params: &PeeblesParams, z: f64) -> f64 {
    let t = t_of_z(params, z);
    let k_t_ev = K_B_EV * t;
    if k_t_ev > B1 {
        return 1.0;
    }
    let n_h = n_h_of_z(params, z);
    let thermal = (M_E * K_B * t / (2.0 * std::f64::consts::PI * HBAR * HBAR)).powf(1.5);
    let boltzmann = (-B1 / k_t_ev).exp();
    let s = thermal * boltzmann / n_h.max(1e-300);
    clip((-s + (s * s + 4.0 * s).sqrt()) / 2.0, 1e-15, 1.0)
}


pub(crate) fn step_sciml_rodas5p(params: &PeeblesParams, z: f64, y: f64, h_signed: f64, cfg: &Rodas5PConfig, tab: &Rodas5PTableau) -> (f64, f64, bool, usize) {
    let jac = if cfg.use_analytic_jacobian { jac_peebles_scalar_analytic(params, z, y) } else { jac_peebles_scalar_fd(params, z, y) };
    let dfdz = if cfg.use_ft_term { dfdz_peebles_scalar_fd(params, z, y) } else { 0.0 };
    let w = 1.0 / (tab.gamma * h_signed) - jac;
    if !w.is_finite() || w.abs() < 1e-30 {
        return (y, f64::INFINITY, false, 0);
    }
    let mut k = [0.0_f64; 8];
    let mut n_f_eval = 0usize;
    for i in 0..8 {
        let mut y_st = y;
        let mut c_sum = 0.0;
        for j in 0..i {
            y_st += tab.a[i][j] * k[j];
            c_sum += tab.c[i][j] * k[j] / h_signed;
        }
        let rhs = rhs_peebles_scalar(params, z, y_st) + c_sum + h_signed * tab.gamma * dfdz;
        n_f_eval += 1;
        let ki = rhs / w;
        if !ki.is_finite() {
            return (y, f64::INFINITY, false, n_f_eval);
        }
        k[i] = ki;
    }
    let mut y_new = y;
    let mut err_est = 0.0;
    for i in 0..8 {
        y_new += tab.b[i] * k[i];
        err_est += tab.bhat[i] * k[i];
    }
    if !y_new.is_finite() {
        return (y, f64::INFINITY, false, n_f_eval);
    }
    let y_clipped = clip(y_new, 1e-15, 1.0);
    let err = err_norm_scalar(err_est, y_clipped, cfg.rtol, cfg.atol);
    (y_clipped, err, true, n_f_eval)
}

pub(crate) fn interpolate_desc(history_z: &[f64], history_y: &[f64], target_z: &[f64]) -> Vec<f64> {
    let mut out = Vec::with_capacity(target_z.len());
    let mut j = 0usize;
    for &zt in target_z {
        while j + 1 < history_z.len() && history_z[j + 1] > zt {
            j += 1;
        }
        if j + 1 >= history_z.len() {
            out.push(*history_y.last().unwrap());
            continue;
        }
        let z0 = history_z[j];
        let z1 = history_z[j + 1];
        let y0 = history_y[j];
        let y1 = history_y[j + 1];
        let denom = z1 - z0;
        if denom.abs() < 1e-30 {
            out.push(y0);
        } else {
            let w = (zt - z0) / denom;
            out.push(y0 + w * (y1 - y0));
        }
    }
    out
}

pub(crate) fn integrate_peebles_on_grid(z_grid: &[f64], x_init: Option<f64>, params: &PeeblesParams, cfg: &Rodas5PConfig) -> Result<Rodas5PDiagnosticResult, String> {
    if z_grid.is_empty() {
        return Err("z_grid must be non-empty".to_string());
    }
    if z_grid.len() == 1 {
        let y0 = clip(x_init.unwrap_or_else(|| x_e_saha_h(params, z_grid[0])), 1e-15, 1.0);
        return Ok(Rodas5PDiagnosticResult { out: vec![y0], history_z: vec![z_grid[0]], history_y: vec![y0], stats: Rodas5PStats { n_steps: 0, n_rejected: 0, n_jac: 0, n_f_eval: 0, h_final: cfg.h_init.unwrap_or(0.0) } });
    }
    for i in 1..z_grid.len() {
        if z_grid[i] > z_grid[i - 1] {
            return Err("z_grid must be monotonically non-increasing".to_string());
        }
    }

    let tab = rodas5p_tableau();
    let z_start = z_grid[0];
    let z_end = *z_grid.last().unwrap();
    let mut current_z = z_start;
    let mut current_y = clip(x_init.unwrap_or_else(|| x_e_saha_h(params, current_z)), 1e-15, 1.0);
    let mut h = initial_step(current_z, current_y, z_end, params, cfg);
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut history_z = vec![current_z];
    let mut history_y = vec![current_y];
    let mut n_f_eval = 1usize;

    while current_z - z_end > 1e-12 {
        if n_steps >= cfg.max_steps {
            return Err(format!("Max steps reached at z={current_z}"));
        }
        let remaining = current_z - z_end;
        let ht = h.min(remaining).max(cfg.h_min);
        let h_signed = -ht;
        n_jac += 1;
        let (y_new, err, ok, n_f_stage) = step_sciml_rodas5p(params, current_z, current_y, h_signed, cfg, &tab);
        n_f_eval += n_f_stage;
        if !ok || err > 1.0 || !err.is_finite() {
            n_rejected += 1;
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 {
                return Err(format!("h_min reached at z={current_z}"));
            }
            continue;
        }
        current_z += h_signed;
        if current_z < z_end {
            current_z = z_end;
        }
        current_y = y_new;
        n_steps += 1;
        history_z.push(current_z);
        history_y.push(current_y);
        h = new_h(h, err, prev_err, cfg);
        prev_err = err.max(1e-30);
    }

    let out = interpolate_desc(&history_z, &history_y, z_grid);
    Ok(Rodas5PDiagnosticResult { out, history_z, history_y, stats: Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h } })
}

