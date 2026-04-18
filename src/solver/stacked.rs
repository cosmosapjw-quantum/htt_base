// Integration loops: full-dense and block-diagonal variants.
// BA-03: Extracted from profile.rs.

use crate::core::config::*;
use crate::core::controller::*;
use super::rodas5p::*;
use super::block_diag::*;

pub(crate) fn interpolate_linear_history_to_targets(history_eta: &[f64], history_y: &[Vec<f64>], target_eta: &[f64], n_state: usize) -> Vec<Vec<f64>> {
    let mut out = Vec::with_capacity(target_eta.len());
    let mut j = 0usize;
    for &et in target_eta {
        while j + 1 < history_eta.len() && history_eta[j + 1] < et { j += 1; }
        let mut row = vec![0.0; n_state];
        if j + 1 >= history_eta.len() {
            row.copy_from_slice(&history_y[history_y.len() - 1][..n_state]);
            out.push(row);
            continue;
        }
        let e0 = history_eta[j];
        let e1 = history_eta[j + 1];
        let w = if (e1 - e0).abs() < 1e-30 { 0.0 } else { (et - e0) / (e1 - e0) };
        for i in 0..n_state { row[i] = history_y[j][i] + w * (history_y[j + 1][i] - history_y[j][i]); }
        out.push(row);
    }
    out
}

/// PERF-01: flat-storage variant. `history_y_flat` is laid out as
/// `[step0_y0, step0_y1, ..., step0_y(stride-1), step1_y0, ...]` so
/// step `j` occupies `history_y_flat[j*stride .. (j+1)*stride]`.
///
/// Numerically identical to `interpolate_linear_history_to_targets` —
/// only the input layout changes.
pub(crate) fn interpolate_linear_history_flat_to_targets(
    history_eta: &[f64],
    history_y_flat: &[f64],
    stride: usize,
    target_eta: &[f64],
    n_state: usize,
) -> Vec<Vec<f64>> {
    let mut out = Vec::with_capacity(target_eta.len());
    let n_steps = history_eta.len();
    debug_assert!(history_y_flat.len() == n_steps * stride,
                  "history_y_flat layout mismatch");
    let mut j = 0usize;
    for &et in target_eta {
        while j + 1 < n_steps && history_eta[j + 1] < et { j += 1; }
        let mut row = vec![0.0; n_state];
        if j + 1 >= n_steps {
            let last = (n_steps - 1) * stride;
            row.copy_from_slice(&history_y_flat[last..last + n_state]);
            out.push(row);
            continue;
        }
        let e0 = history_eta[j];
        let e1 = history_eta[j + 1];
        let w = if (e1 - e0).abs() < 1e-30 { 0.0 } else { (et - e0) / (e1 - e0) };
        let base_a = j * stride;
        let base_b = (j + 1) * stride;
        for i in 0..n_state {
            row[i] = history_y_flat[base_a + i]
                   + w * (history_y_flat[base_b + i] - history_y_flat[base_a + i]);
        }
        out.push(row);
    }
    out
}

pub(crate) fn integrate_linear_profile_rodas5p(
    eta_profile: &[f64],
    mats_flat: &[f64],
    n_state: usize,
    y0: &[f64],
    eta_eval: &[f64],
    cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, ControllerDiagnostics), String> {
    if y0.len() != n_state { return Err(format!("y0 must have length {}", n_state)); }
    if eta_eval.len() < 2 { return Err("eta_eval must contain at least two samples".to_string()); }
    for i in 1..eta_eval.len() {
        if eta_eval[i] <= eta_eval[i - 1] { return Err("eta_eval must be strictly increasing".to_string()); }
    }
    let profile = LinearProfileDyn::new(eta_profile.to_vec(), mats_flat.to_vec(), n_state)?;
    let d = n_state + 1;
    let mut y = vec![0.0; d];
    y[..n_state].copy_from_slice(y0);
    y[d - 1] = eta_eval[0];
    let eta_start = eta_eval[0];
    let eta_end = *eta_eval.last().unwrap();
    let tab = rodas5p_tableau();
    let mut h = cfg.h_init.unwrap_or_else(|| ((eta_end - eta_start).abs() / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut history_eta = vec![eta_start];
    let mut history_y = vec![y.clone()];
    let mut scratch = LinearStepScratch::new(n_state, profile.stride);
    let mut cdiag = ControllerDiagnostics::default();
    let mut reject_streak = 0usize;
    while y[d - 1] < eta_end - 1e-14 {
        if n_steps >= cfg.max_steps { return Err(format!("Max steps reached at eta={}", y[d - 1])); }
        let remaining = eta_end - y[d - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;
        let (err, ok, n_f_stage) = step_linear_profile_rodas5p_into(&profile, &y, h_try, cfg, &tab, &mut scratch);
        n_f_eval += n_f_stage;
        if !ok || !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 { return Err(format!("h_min reached at eta={}", y[d - 1])); }
            continue;
        }
        y.copy_from_slice(&scratch.y_new);
        n_steps += 1;
        reject_streak = 0;
        history_eta.push(y[d - 1]);
        history_y.push(y.clone());
        let (h_new, q_raw, q_clipped) = new_h_with_diag(h, err, prev_err, cfg);
        cdiag.record_clip(q_raw, q_clipped, cfg.f_min, cfg.f_max);
        cdiag.record_accept(err, h_try, q_raw, q_clipped);
        h = h_new;
        prev_err = err.max(1e-30);
    }
    let out = interpolate_linear_history_to_targets(&history_eta, &history_y, eta_eval, n_state);
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }, cdiag))
}

/// Phase 2.0 (2026-04-19): streaming callback variant.
///
/// Same numerics as `integrate_linear_profile_rodas5p` but replaces the
/// pre-materialized `mats_flat` (O(N_snap · n²) memory) with an on-demand
/// `builder(eta, &mut out)` callback.  Internally wraps a
/// `LinearProfileCallback` that caches exactly TWO adjacent bracket
/// matrices (O(2·n²) memory).
///
/// The builder must write M(eta) row-major into `out` (length n_state²).
/// Same step-controller and accept/reject logic as the mats_flat path.
pub(crate) fn integrate_linear_profile_rodas5p_callback<F>(
    eta_profile: &[f64],
    builder: F,
    n_state: usize,
    y0: &[f64],
    eta_eval: &[f64],
    cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, ControllerDiagnostics), String>
where
    F: FnMut(f64, &mut [f64]),
{
    if y0.len() != n_state { return Err(format!("y0 must have length {}", n_state)); }
    if eta_eval.len() < 2 { return Err("eta_eval must contain at least two samples".to_string()); }
    for i in 1..eta_eval.len() {
        if eta_eval[i] <= eta_eval[i - 1] { return Err("eta_eval must be strictly increasing".to_string()); }
    }
    let profile = LinearProfileCallback::new(eta_profile.to_vec(), n_state, builder)?;
    let d = n_state + 1;
    let mut y = vec![0.0; d];
    y[..n_state].copy_from_slice(y0);
    y[d - 1] = eta_eval[0];
    let eta_start = eta_eval[0];
    let eta_end = *eta_eval.last().unwrap();
    let tab = rodas5p_tableau();
    let mut h = cfg.h_init.unwrap_or_else(|| ((eta_end - eta_start).abs() / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut history_eta = vec![eta_start];
    let mut history_y = vec![y.clone()];
    let mut scratch = LinearStepScratch::new(n_state, profile.stride);
    let mut cdiag = ControllerDiagnostics::default();
    let mut reject_streak = 0usize;
    while y[d - 1] < eta_end - 1e-14 {
        if n_steps >= cfg.max_steps { return Err(format!("Max steps reached at eta={}", y[d - 1])); }
        let remaining = eta_end - y[d - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;
        let (err, ok, n_f_stage) = step_linear_profile_rodas5p_into_generic(&profile, &y, h_try, cfg, &tab, &mut scratch);
        n_f_eval += n_f_stage;
        if !ok || !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 { return Err(format!("h_min reached at eta={}", y[d - 1])); }
            continue;
        }
        y.copy_from_slice(&scratch.y_new);
        n_steps += 1;
        reject_streak = 0;
        history_eta.push(y[d - 1]);
        history_y.push(y.clone());
        let (h_new, q_raw, q_clipped) = new_h_with_diag(h, err, prev_err, cfg);
        cdiag.record_clip(q_raw, q_clipped, cfg.f_min, cfg.f_max);
        cdiag.record_accept(err, h_try, q_raw, q_clipped);
        h = h_new;
        prev_err = err.max(1e-30);
    }
    let out = interpolate_linear_history_to_targets(&history_eta, &history_y, eta_eval, n_state);
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }, cdiag))
}

/// PR-14B: Block-diagonal variant — factors two smaller LU systems per step.
pub(crate) fn integrate_linear_profile_rodas5p_blockdiag(
    eta_profile: &[f64], mats_flat: &[f64], n_state: usize, y0: &[f64], eta_eval: &[f64],
    cfg: &Rodas5PConfig, decomp: &BlockDecomp,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, ControllerDiagnostics), String> {
    if y0.len() != n_state { return Err(format!("y0 must have length {}", n_state)); }
    if eta_eval.len() < 2 { return Err("eta_eval must contain at least two samples".to_string()); }
    for i in 1..eta_eval.len() {
        if eta_eval[i] <= eta_eval[i - 1] { return Err("eta_eval must be strictly increasing".to_string()); }
    }
    let profile = LinearProfileDyn::new(eta_profile.to_vec(), mats_flat.to_vec(), n_state)?;
    let d = n_state + 1;
    let mut y = vec![0.0; d];
    y[..n_state].copy_from_slice(y0);
    y[d - 1] = eta_eval[0];
    let eta_start = eta_eval[0];
    let eta_end = *eta_eval.last().unwrap();
    let tab = rodas5p_tableau();
    let mut h = cfg.h_init.unwrap_or_else(|| ((eta_end - eta_start).abs() / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut history_eta = Vec::with_capacity(16384);
    history_eta.push(eta_start);
    let mut history_y_flat: Vec<f64> = Vec::with_capacity(16384 * d);
    history_y_flat.extend_from_slice(&y);
    let mut scratch = LinearStepScratch::new(n_state, profile.stride);
    let mut bscratch = BlockDiagScratch::new(decomp, d);
    let mut cdiag = ControllerDiagnostics::default();
    let mut reject_streak = 0usize;
    while y[d - 1] < eta_end - 1e-14 {
        if n_steps >= cfg.max_steps { return Err(format!("Max steps reached at eta={}", y[d - 1])); }
        let remaining = eta_end - y[d - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;
        let (err, ok, n_f_stage) = step_blockdiag_rodas5p_into(
            &profile, &y, h_try, cfg, &tab, &mut scratch, decomp, &mut bscratch);
        n_f_eval += n_f_stage;
        if !ok || !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 { return Err(format!("h_min reached at eta={}", y[d - 1])); }
            continue;
        }
        y.copy_from_slice(&scratch.y_new);
        n_steps += 1;
        reject_streak = 0;
        history_eta.push(y[d - 1]);
        history_y_flat.extend_from_slice(&y);
        let (h_new, q_raw, q_clipped) = new_h_with_diag(h, err, prev_err, cfg);
        cdiag.record_clip(q_raw, q_clipped, cfg.f_min, cfg.f_max);
        cdiag.record_accept(err, h_try, q_raw, q_clipped);
        h = h_new;
        prev_err = err.max(1e-30);
    }
    let out = interpolate_linear_history_flat_to_targets(
        &history_eta, &history_y_flat, d, eta_eval, n_state);
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }, cdiag))
}

pub(crate) fn interpolate_selected_row(y0: &[f64], y1: &[f64], w: f64, selected_real_indices: &[usize]) -> Vec<f64> {
    let mut row = Vec::with_capacity(selected_real_indices.len());
    for &idx in selected_real_indices.iter() {
        row.push(y0[idx] + w * (y1[idx] - y0[idx]));
    }
    row
}

pub(crate) fn integrate_linear_profile_rodas5p_selected(
    eta_profile: &[f64],
    mats_flat: &[f64],
    n_state: usize,
    y0: &[f64],
    eta_eval: &[f64],
    selected_real_indices: &[usize],
    cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, ControllerDiagnostics), String> {
    if y0.len() != n_state { return Err(format!("y0 must have length {}", n_state)); }
    if eta_eval.len() < 2 { return Err("eta_eval must contain at least two samples".to_string()); }
    for i in 1..eta_eval.len() {
        if eta_eval[i] <= eta_eval[i - 1] { return Err("eta_eval must be strictly increasing".to_string()); }
    }
    for &idx in selected_real_indices.iter() {
        if idx >= n_state { return Err(format!("selected real index {} out of range 0..{}", idx, n_state.saturating_sub(1))); }
    }
    let profile = LinearProfileDyn::new(eta_profile.to_vec(), mats_flat.to_vec(), n_state)?;
    let d = n_state + 1;
    let mut y = vec![0.0; d];
    y[..n_state].copy_from_slice(y0);
    y[d - 1] = eta_eval[0];
    let eta_start = eta_eval[0];
    let eta_end = *eta_eval.last().unwrap();
    let tab = rodas5p_tableau();
    let mut h = cfg.h_init.unwrap_or_else(|| ((eta_end - eta_start).abs() / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut out: Vec<Vec<f64>> = Vec::with_capacity(eta_eval.len());
    out.push(interpolate_selected_row(&y, &y, 0.0, selected_real_indices));
    let mut target_idx = 1usize;
    let mut scratch = LinearStepScratch::new(n_state, profile.stride);
    let mut cdiag = ControllerDiagnostics::default();
    let mut reject_streak = 0usize;
    while y[d - 1] < eta_end - 1e-14 {
        if n_steps >= cfg.max_steps { return Err(format!("Max steps reached at eta={}", y[d - 1])); }
        let y_prev = y.clone();
        let eta_prev = y_prev[d - 1];
        let remaining = eta_end - y[d - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;
        let (err, ok, n_f_stage) = step_linear_profile_rodas5p_into(&profile, &y, h_try, cfg, &tab, &mut scratch);
        n_f_eval += n_f_stage;
        if !ok || !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 { return Err(format!("h_min reached at eta={}", y[d - 1])); }
            continue;
        }
        y.copy_from_slice(&scratch.y_new);
        n_steps += 1;
        reject_streak = 0;
        let eta_new = y[d - 1];
        while target_idx < eta_eval.len() && eta_eval[target_idx] <= eta_new + 1e-14 {
            let et = eta_eval[target_idx];
            let w = if (eta_new - eta_prev).abs() < 1e-30 { 0.0 } else { (et - eta_prev) / (eta_new - eta_prev) };
            out.push(interpolate_selected_row(&y_prev, &y, w, selected_real_indices));
            target_idx += 1;
        }
        let (h_new, q_raw, q_clipped) = new_h_with_diag(h, err, prev_err, cfg);
        cdiag.record_clip(q_raw, q_clipped, cfg.f_min, cfg.f_max);
        cdiag.record_accept(err, h_try, q_raw, q_clipped);
        h = h_new;
        prev_err = err.max(1e-30);
    }
    if out.len() != eta_eval.len() {
        return Err(format!("selected output length mismatch: got {}, expected {}", out.len(), eta_eval.len()));
    }
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }, cdiag))
}

/// PR-14B: Block-diagonal variant of the selected-output integration.
pub(crate) fn integrate_linear_profile_rodas5p_selected_blockdiag(
    eta_profile: &[f64], mats_flat: &[f64], n_state: usize, y0: &[f64],
    eta_eval: &[f64], selected_real_indices: &[usize], cfg: &Rodas5PConfig,
    decomp: &BlockDecomp,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, ControllerDiagnostics), String> {
    if y0.len() != n_state { return Err(format!("y0 must have length {}", n_state)); }
    if eta_eval.len() < 2 { return Err("eta_eval must contain at least two samples".to_string()); }
    for i in 1..eta_eval.len() {
        if eta_eval[i] <= eta_eval[i - 1] { return Err("eta_eval must be strictly increasing".to_string()); }
    }
    for &idx in selected_real_indices.iter() {
        if idx >= n_state { return Err(format!("selected real index {} out of range 0..{}", idx, n_state.saturating_sub(1))); }
    }
    let profile = LinearProfileDyn::new(eta_profile.to_vec(), mats_flat.to_vec(), n_state)?;
    let d = n_state + 1;
    let mut y = vec![0.0; d];
    y[..n_state].copy_from_slice(y0);
    y[d - 1] = eta_eval[0];
    let eta_start = eta_eval[0];
    let eta_end = *eta_eval.last().unwrap();
    let tab = rodas5p_tableau();
    let mut h = cfg.h_init.unwrap_or_else(|| ((eta_end - eta_start).abs() / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut out: Vec<Vec<f64>> = Vec::with_capacity(eta_eval.len());
    out.push(interpolate_selected_row(&y, &y, 0.0, selected_real_indices));
    let mut target_idx = 1usize;
    let mut scratch = LinearStepScratch::new(n_state, profile.stride);
    let mut bscratch = BlockDiagScratch::new(decomp, d);
    let mut cdiag = ControllerDiagnostics::default();
    let mut reject_streak = 0usize;
    while y[d - 1] < eta_end - 1e-14 {
        if n_steps >= cfg.max_steps { return Err(format!("Max steps reached at eta={}", y[d - 1])); }
        let y_prev = y.clone();
        let eta_prev = y_prev[d - 1];
        let remaining = eta_end - y[d - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;
        let (err, ok, n_f_stage) = step_blockdiag_rodas5p_into(
            &profile, &y, h_try, cfg, &tab, &mut scratch, decomp, &mut bscratch);
        n_f_eval += n_f_stage;
        if !ok || !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            reject_streak += 1;
            cdiag.record_reject(h_try, reject_streak);
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 { return Err(format!("h_min reached at eta={}", y[d - 1])); }
            continue;
        }
        y.copy_from_slice(&scratch.y_new);
        n_steps += 1;
        reject_streak = 0;
        let eta_new = y[d - 1];
        while target_idx < eta_eval.len() && eta_eval[target_idx] <= eta_new + 1e-14 {
            let et = eta_eval[target_idx];
            let w = if (eta_new - eta_prev).abs() < 1e-30 { 0.0 } else { (et - eta_prev) / (eta_new - eta_prev) };
            out.push(interpolate_selected_row(&y_prev, &y, w, selected_real_indices));
            target_idx += 1;
        }
        let (h_new, q_raw, q_clipped) = new_h_with_diag(h, err, prev_err, cfg);
        cdiag.record_clip(q_raw, q_clipped, cfg.f_min, cfg.f_max);
        cdiag.record_accept(err, h_try, q_raw, q_clipped);
        h = h_new;
        prev_err = err.max(1e-30);
    }
    if out.len() != eta_eval.len() {
        return Err(format!("selected output length mismatch: got {}, expected {}", out.len(), eta_eval.len()));
    }
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }, cdiag))
}


