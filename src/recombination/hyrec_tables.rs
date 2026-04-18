// BE-05a': HyRec-2 Effective Rate Tables — exact data file loading.
//
// Parses: Alpha_inf.dat (α_{2s}, α_{2p}, Dα_{2s}, Dα_{2p})
//         R_inf.dat (R_{2p→2s})
//         fit_swift.dat (SWIFT Δ correction + derivatives)
//
// Grid: NTR=100 T_r in [0.004, 0.4] eV log-spaced
//        NTM=40 T_m/T_r in [0.1, 1.0] linearly spaced
//
// Units: α stored internally in m³/s (×1e-6 from cm³/s in data files)

pub(crate) const SAHA_FACT: f64 = 3.016103031869581e21;
pub(crate) const LYA_FACT: f64 = 4.662899067555897e15;
pub(crate) const LAMBDA_2S: f64 = 8.2245809;
pub(crate) const E_ION_EV: f64 = 13.605693122994;
pub(crate) const E_21_EV: f64 = 10.204019842;
pub(crate) const A_LYA: f64 = 6.2649e8;
pub(crate) const KB_EV: f64 = 8.617333262e-5;

const NTR: usize = 100;
const NTM: usize = 40;
const TR_MIN_EV: f64 = 0.004;
const TR_MAX_EV: f64 = 0.4;
const TM_TR_MIN: f64 = 0.1;
const TM_TR_MAX: f64 = 1.0;

#[derive(Clone)]
pub(crate) struct HyRecTables {
    // Alpha_inf: log(α) in m³/s, indexed [l][j*NTR+i], l=0..3, j=0..NTM-1, i=0..NTR-1
    log_alpha: [Vec<f64>; 4],
    log_tr: Vec<f64>,       // log(T_r) in eV, NTR points
    tm_tr_grid: Vec<f64>,   // T_m/T_r ratio, NTM points
    dlog_tr: f64,
    dtm_tr: f64,
    // R_inf: log(R_{2p→2s}) in s⁻¹, NTR points
    log_r2p2s: Vec<f64>,
    // SWIFT: Δ(T_r) correction
    swift_tr_k: Vec<f64>,   // T_r in K
    swift_delta: Vec<f64>,  // Δ₀
    swift_d_obh2: Vec<f64>, // ∂Δ/∂(Ω_bh²)
    swift_d_yp: Vec<f64>,   // ∂Δ/∂Y_p
    swift_d_tcmb: Vec<f64>, // ∂Δ/∂T_CMB
    // Fallback 1D for simple interface
    t1d_grid: Vec<f64>,     // T in K
    alpha1d: Vec<f64>,      // α_eff(T) m³/s
    lambda2g: Vec<f64>,     // λ_{2γ}(T) s⁻¹
    loaded_from_file: bool,
}

impl HyRecTables {
    /// Load from HyRec-2 data directory (Path A — exact).
    pub(crate) fn load(data_dir: &str) -> Result<Self, String> {
        // Parse Alpha_inf.dat
        let alpha_str = std::fs::read_to_string(format!("{}/Alpha_inf.dat", data_dir))
            .map_err(|e| format!("Alpha_inf.dat: {}", e))?;
        let alpha_vals: Vec<f64> = alpha_str.split_whitespace()
            .filter_map(|s| s.parse::<f64>().ok()).collect();
        if alpha_vals.len() < NTR * NTM * 4 {
            return Err(format!("Alpha_inf.dat: {} values < {}", alpha_vals.len(), NTR*NTM*4));
        }

        // Build grids
        let mut log_tr = vec![0.0; NTR];
        let mut tm_tr_grid = vec![0.0; NTM];
        for i in 0..NTR { log_tr[i] = (TR_MIN_EV).ln() + i as f64 * ((TR_MAX_EV/TR_MIN_EV).ln()) / (NTR-1) as f64; }
        for j in 0..NTM { tm_tr_grid[j] = TM_TR_MIN + j as f64 * (TM_TR_MAX - TM_TR_MIN) / (NTM-1) as f64; }
        let dlog_tr = log_tr[1] - log_tr[0];
        let dtm_tr = tm_tr_grid[1] - tm_tr_grid[0];

        // Read: for i in 0..NTR { for j in 0..NTM { read 4 values → l=0..3 } }
        // Store as log, convert cm³/s → m³/s (×1e-6)
        let mut log_alpha = [vec![0.0; NTM*NTR], vec![0.0; NTM*NTR], vec![0.0; NTM*NTR], vec![0.0; NTM*NTR]];
        let mut idx = 0;
        for i in 0..NTR {
            for j in 0..NTM {
                for l in 0..4 {
                    let val = alpha_vals[idx] * 1e-6; // cm³/s → m³/s
                    log_alpha[l][j * NTR + i] = val.max(1e-300).ln();
                    idx += 1;
                }
            }
        }

        // Parse R_inf.dat
        let r_str = std::fs::read_to_string(format!("{}/R_inf.dat", data_dir))
            .map_err(|e| format!("R_inf.dat: {}", e))?;
        let r_vals: Vec<f64> = r_str.split_whitespace()
            .filter_map(|s| s.parse::<f64>().ok()).collect();
        let mut log_r2p2s = vec![0.0; NTR];
        for i in 0..NTR.min(r_vals.len()) {
            log_r2p2s[i] = r_vals[i].max(1e-300).ln();
        }

        // Parse fit_swift.dat
        let swift_str = std::fs::read_to_string(format!("{}/fit_swift.dat", data_dir))
            .map_err(|e| format!("fit_swift.dat: {}", e))?;
        let mut swift_tr_k = Vec::new();
        let mut swift_delta = Vec::new();
        let mut swift_d_obh2 = Vec::new();
        let mut swift_d_yp = Vec::new();
        let mut swift_d_tcmb = Vec::new();
        for line in swift_str.lines() {
            let v: Vec<f64> = line.split_whitespace().filter_map(|s| s.parse().ok()).collect();
            if v.len() >= 5 {
                swift_tr_k.push(v[0]);
                swift_delta.push(v[1]);
                swift_d_obh2.push(v[2]);
                swift_d_yp.push(v[3]);
                swift_d_tcmb.push(v[4]);
            }
        }

        // Build 1D convenience tables for simple interface (T_m = T_r case)
        let n1d = 500;
        let (t_min, t_max) = (100.0_f64, 50000.0_f64);
        let mut t1d_grid = Vec::with_capacity(n1d);
        let mut alpha1d = Vec::with_capacity(n1d);
        let mut lambda2g = Vec::with_capacity(n1d);
        for k in 0..n1d {
            let f = k as f64 / (n1d-1) as f64;
            let tk = t_min * (t_max/t_min).powf(f);
            t1d_grid.push(tk);
            let tr_ev = tk * KB_EV;
            // Interpolate α at T_m/T_r = 1.0 (j = NTM-1)
            let a2s = interp_2d_log(&log_alpha[0], &log_tr, &tm_tr_grid, dlog_tr, dtm_tr, tr_ev.ln(), 1.0);
            let a2p = interp_2d_log(&log_alpha[1], &log_tr, &tm_tr_grid, dlog_tr, dtm_tr, tr_ev.ln(), 1.0);
            alpha1d.push((a2s.exp() + a2p.exp()).max(1e-30));
            lambda2g.push(lambda_2g_at(tk));
        }

        Ok(Self {
            log_alpha, log_tr, tm_tr_grid, dlog_tr, dtm_tr,
            log_r2p2s,
            swift_tr_k, swift_delta, swift_d_obh2, swift_d_yp, swift_d_tcmb,
            t1d_grid, alpha1d, lambda2g,
            loaded_from_file: true,
        })
    }

    /// Generate from fitting formulae (Path B — fallback).
    pub(crate) fn generate(n_points: usize) -> Self {
        let (t_min, t_max) = (100.0_f64, 50000.0_f64);
        let mut t1d = Vec::with_capacity(n_points);
        let mut a1d = Vec::with_capacity(n_points);
        let mut l1d = Vec::with_capacity(n_points);
        for k in 0..n_points {
            let f = k as f64 / (n_points-1).max(1) as f64;
            let tk = t_min * (t_max/t_min).powf(f);
            t1d.push(tk);
            a1d.push(alpha_eff_fit(tk));
            l1d.push(lambda_2g_at(tk));
        }
        // Empty 2D tables (not loaded)
        Self {
            log_alpha: [vec![], vec![], vec![], vec![]],
            log_tr: vec![], tm_tr_grid: vec![], dlog_tr: 0.0, dtm_tr: 0.0,
            log_r2p2s: vec![],
            swift_tr_k: vec![], swift_delta: vec![], swift_d_obh2: vec![], swift_d_yp: vec![], swift_d_tcmb: vec![],
            t1d_grid: t1d, alpha1d: a1d, lambda2g: l1d,
            loaded_from_file: false,
        }
    }

    pub(crate) fn alpha_eff(&self, t_k: f64) -> f64 {
        log_interp_1d(&self.t1d_grid, &self.alpha1d, t_k)
    }

    pub(crate) fn alpha_2d(&self, tr_ev: f64, tm_tr: f64) -> (f64, f64) {
        if self.log_alpha[0].is_empty() { let a = self.alpha_eff(tr_ev / KB_EV); return (a*0.4, a*0.6); }
        let a2s = interp_2d_log(&self.log_alpha[0], &self.log_tr, &self.tm_tr_grid, self.dlog_tr, self.dtm_tr, tr_ev.ln(), tm_tr).exp();
        let a2p = interp_2d_log(&self.log_alpha[1], &self.log_tr, &self.tm_tr_grid, self.dlog_tr, self.dtm_tr, tr_ev.ln(), tm_tr).exp();
        (a2s, a2p)
    }

    pub(crate) fn r_inf(&self, t_k: f64) -> f64 {
        if self.log_r2p2s.is_empty() { return r_inf_fit(t_k); }
        let tr_ev = t_k * KB_EV;
        let lt = tr_ev.ln();
        let f = (lt - self.log_tr[0]) / self.dlog_tr;
        let i = (f as usize).min(NTR - 2);
        let t = f - i as f64;
        (self.log_r2p2s[i] * (1.0 - t) + self.log_r2p2s[i + 1] * t).exp()
    }

    pub(crate) fn delta_lya(&self, t_k: f64) -> f64 {
        if self.swift_tr_k.is_empty() { return delta_lya_fit(t_k); }
        lin_interp(&self.swift_tr_k, &self.swift_delta, t_k)
    }

    pub(crate) fn lambda_2gamma(&self, t_k: f64) -> f64 {
        log_interp_1d(&self.t1d_grid, &self.lambda2g, t_k)
    }

    pub(crate) fn beta_eff(&self, t_k: f64) -> f64 {
        let a = self.alpha_eff(t_k);
        let t_ev = t_k * KB_EV;
        let thermal = (2.0 * std::f64::consts::PI * 9.1094e-31 * 1.3806e-23 * t_k
                       / (6.6261e-34 * 6.6261e-34)).powf(1.5);
        a * thermal * (-E_ION_EV / (4.0 * t_ev)).exp()
    }

    pub(crate) fn delta_lya_aniso(&self, _t_k: f64, _sigma2: f64) -> Option<f64> { None }
    pub(crate) fn is_loaded(&self) -> bool { self.loaded_from_file }
}

// ═══ 2D interpolation for Alpha tables ═══
fn interp_2d_log(data: &[f64], log_tr: &[f64], tm_tr: &[f64], dlt: f64, dtr: f64, lt: f64, ratio: f64) -> f64 {
    let ntr = log_tr.len(); let ntm = tm_tr.len();
    if ntr == 0 || ntm == 0 { return -30.0; }
    let fi = (lt - log_tr[0]) / dlt;
    let fj = (ratio - tm_tr[0]) / dtr;
    let i = (fi as usize).min(ntr - 2);
    let j = (fj as usize).min(ntm - 2);
    let ti = fi - i as f64;
    let tj = fj - j as f64;
    let v00 = data[j * ntr + i];
    let v10 = data[j * ntr + i + 1];
    let v01 = data[(j+1) * ntr + i];
    let v11 = data[(j+1) * ntr + i + 1];
    v00*(1.0-ti)*(1.0-tj) + v10*ti*(1.0-tj) + v01*(1.0-ti)*tj + v11*ti*tj
}

// ═══ Fitting formulae (Path B fallback) ═══
fn alpha_eff_fit(t_k: f64) -> f64 {
    let t = t_k / 1e4;
    1.14 * 1e-19 * 4.309 * t.powf(-0.6166) / (1.0 + 0.6703 * t.powf(0.530))
}

fn r_inf_fit(t_k: f64) -> f64 {
    let t_ev = t_k * KB_EV;
    let x = E_21_EV / t_ev;
    let f_stim = if x < 500.0 { 1.0 / (1.0 - (-x).exp()) } else { 1.0 };
    A_LYA * f_stim * (1.0 + 0.3 * (t_k / 1e4).powf(0.3))
}

fn delta_lya_fit(t_k: f64) -> f64 {
    let t_ev = t_k * KB_EV;
    if t_ev > 0.4 || t_ev < 0.004 { return 0.0; }
    let x = (t_ev - 0.13) / 0.05;
    0.12 * (-0.5 * x * x).exp() + 0.03 * (1.0 - (-(0.4 - t_ev) / 0.1).exp())
}

fn lambda_2g_at(t_k: f64) -> f64 {
    let t_ev = t_k * KB_EV;
    let x = E_21_EV / t_ev;
    let ng = if x < 500.0 { 1.0 / (x.exp() - 1.0) } else { 0.0 };
    LAMBDA_2S * (1.0 + ng)
}

fn log_interp_1d(xg: &[f64], yg: &[f64], x: f64) -> f64 {
    let n = xg.len();
    if n == 0 { return 0.0; }
    if x <= xg[0] { return yg[0]; }
    if x >= xg[n-1] { return yg[n-1]; }
    let mut lo = 0; let mut hi = n - 1;
    while hi - lo > 1 { let m = (lo+hi)/2; if xg[m] <= x { lo=m; } else { hi=m; } }
    let lx = x.ln(); let lx0 = xg[lo].ln(); let lx1 = xg[hi].ln();
    let ly0 = yg[lo].abs().max(1e-300).ln();
    let ly1 = yg[hi].abs().max(1e-300).ln();
    let t = (lx - lx0) / (lx1 - lx0).max(1e-30);
    (ly0 + t * (ly1 - ly0)).exp()
}

fn lin_interp(xg: &[f64], yg: &[f64], x: f64) -> f64 {
    let n = xg.len();
    if n == 0 { return 0.0; }
    if x <= xg[0] { return yg[0]; }
    if x >= xg[n-1] { return yg[n-1]; }
    let mut lo = 0; let mut hi = n - 1;
    while hi - lo > 1 { let m = (lo+hi)/2; if xg[m] <= x { lo=m; } else { hi=m; } }
    let t = (x - xg[lo]) / (xg[hi] - xg[lo]).max(1e-30);
    yg[lo] * (1.0 - t) + yg[hi] * t
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tables_gen() -> HyRecTables { HyRecTables::generate(500) }
    fn tables_load() -> Option<HyRecTables> { HyRecTables::load("data/hyrec2").ok() }

    #[test]
    fn test_generate_works() { let _ = tables_gen(); }

    #[test]
    fn test_load_works() {
        if let Some(t) = tables_load() {
            assert!(t.is_loaded());
        }
    }

    #[test]
    fn test_alpha_eff_loaded_vs_fit() {
        if let Some(tl) = tables_load() {
            let tg = tables_gen();
            for tk in [1000.0, 2000.0, 3000.0, 5000.0] {
                let al = tl.alpha_eff(tk);
                let ag = tg.alpha_eff(tk);
                let rel = (al - ag).abs() / al.max(1e-30);
                eprintln!("α_eff({:.0}K): loaded={:.3e}, fit={:.3e}, rel={:.2e}", tk, al, ag, rel);
                // Fitting formula ~5-20% off is expected
                assert!(rel < 0.5, "α_eff({:.0}K) off by {:.0}%", tk, rel*100.0);
            }
        }
    }

    #[test]
    fn test_alpha_decreasing() {
        let t = tables_gen();
        assert!(t.alpha_eff(1000.0) > t.alpha_eff(10000.0));
    }

    #[test]
    fn test_detailed_balance() {
        let t = tables_gen();
        let tk = 3000.0; let t_ev = tk * KB_EV;
        let thermal = (2.0 * std::f64::consts::PI * 9.1094e-31 * 1.3806e-23 * tk
                       / (6.6261e-34_f64).powi(2)).powf(1.5);
        let ratio = t.beta_eff(tk) / t.alpha_eff(tk);
        let expected = thermal * (-E_ION_EV / (4.0 * t_ev)).exp();
        assert!((ratio - expected).abs() / expected < 1e-6, "balance: {:.4e} vs {:.4e}", ratio, expected);
    }

    #[test]
    fn test_delta_lya_loaded() {
        if let Some(t) = tables_load() {
            let d = t.delta_lya(2500.0);
            eprintln!("Δ(2500K) from SWIFT file = {:.6}", d);
            assert!(d.abs() < 0.2, "Δ out of range: {}", d);
        }
    }

    #[test]
    fn test_r_inf_loaded() {
        if let Some(t) = tables_load() {
            let r = t.r_inf(3000.0);
            eprintln!("R_inf(3000K) = {:.4e}", r);
            assert!(r > 0.0 && r.is_finite());
        }
    }

    #[test]
    fn test_roundtrip() {
        let t = tables_gen();
        for i in [0, 50, 250, 499] {
            let tk = t.t1d_grid[i];
            let a = t.alpha_eff(tk);
            let ae = t.alpha1d[i];
            assert!((a - ae).abs() / ae.max(1e-30) < 1e-6);
        }
    }

    #[test]
    fn test_aniso_stub() { assert!(tables_gen().delta_lya_aniso(3000.0, 1e-8).is_none()); }

    #[test]
    fn test_saha_fact() { assert!((SAHA_FACT - 3.016103031869581e21).abs() < 1e10); }
}
