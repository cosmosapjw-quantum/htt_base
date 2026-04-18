// Adaptive step-size controller.
// BA-02: initial_step moved to recombination/peebles.rs (resolves cross-boundary dep).

use crate::core::config::*;

pub(crate) fn err_norm_scalar(err_est: f64, y: f64, rtol: f64, atol: f64) -> f64 {
    let sc = atol + rtol * y.abs();
    (err_est / sc).abs()
}

pub(crate) fn new_h(h: f64, err: f64, prev_err: f64, cfg: &Rodas5PConfig) -> f64 {
    if err < 1e-30 {
        return (h * cfg.f_max).min(cfg.h_max).max(cfg.h_min);
    }
    let mut fac = cfg.f_safety * (1.0 / err).powf(1.0 / 5.0);
    if prev_err > 0.0 {
        fac *= prev_err.powf(cfg.beta);
    }
    fac = fac.max(cfg.f_min).min(cfg.f_max);
    (h * fac).max(cfg.h_min).min(cfg.h_max)
}

/// Like new_h but returns (new_h, q_raw, q_clipped) for controller diagnostics.
pub(crate) fn new_h_with_diag(h: f64, err: f64, prev_err: f64, cfg: &Rodas5PConfig) -> (f64, f64, f64) {
    if err < 1e-30 {
        let q_raw = cfg.f_max;
        let q_clipped = cfg.f_max;
        return ((h * q_clipped).min(cfg.h_max).max(cfg.h_min), q_raw, q_clipped);
    }
    let mut fac_raw = cfg.f_safety * (1.0 / err).powf(1.0 / 5.0);
    if prev_err > 0.0 {
        fac_raw *= prev_err.powf(cfg.beta);
    }
    let fac_clipped = fac_raw.max(cfg.f_min).min(cfg.f_max);
    ((h * fac_clipped).max(cfg.h_min).min(cfg.h_max), fac_raw, fac_clipped)
}
