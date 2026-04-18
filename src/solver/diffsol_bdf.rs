// diffsol solver wrapper for linear Boltzmann hierarchy y' = A(τ)y.
//
// Provides two A-stable implicit solver backends:
//   1. ESDIRK34 (default): 3rd-order, A-L stable, stiffly accurate.
//      No order ambiguity — stable on the entire left half-plane + imaginary axis.
//      Recommended by SymBoltz/diffrax for stiff+oscillatory systems.
//   2. BDF (backup): Variable-order 1–5. BDF-1/2 are A-stable but BDF-3+ are NOT
//      (Dahlquist barrier). Use with order cap for truth engine.
//
// Design: MatrixProfile::matvec is the O(n²) hot path, isolated for future GPU.
// Differentiability: diffsol supports forward/adjoint sensitivity natively.

use std::sync::Arc;
use diffsol::{
    OdeBuilder, OdeSolverMethod, OdeSolverStopReason,
    NalgebraLU, NalgebraMat, NalgebraVec, NalgebraContext,
    VectorHost, Tableau, DenseMatrix,
};

/// Solver backend selection.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum SolverBackend {
    /// ESDIRK34: A-L stable, order 3(4). Default for truth engine.
    Esdirk34,
    /// TR-BDF2: A-L stable, order 2. Very robust, slight damping.
    TrBdf2,
    /// BDF: Variable-order 1–5. BDF-1/2 A-stable, BDF-3+ NOT A-stable.
    Bdf,
}

#[derive(Clone, Debug)]
pub(crate) struct DiffsolConfig {
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
    pub(crate) h_init: f64,
    pub(crate) backend: SolverBackend,
}

impl Default for DiffsolConfig {
    fn default() -> Self {
        Self {
            rtol: 1e-6, atol: 1e-9, h_init: 0.1,
            backend: SolverBackend::Esdirk34,  // A-L stable default
        }
    }
}

/// Matrix profile: precomputed A(τ) on a grid, linearly interpolated.
struct MatrixProfile {
    tau_profile: Vec<f64>,
    mats_flat: Vec<f64>,
    n_state: usize,
}

impl MatrixProfile {
    #[inline]
    fn matvec(&self, tau: f64, x: &[f64], y: &mut [f64]) {
        let n = self.n_state;
        let np = self.tau_profile.len();
        let stride = n * n;
        let lo = match self.tau_profile.binary_search_by(|v| v.partial_cmp(&tau).unwrap()) {
            Ok(i) => i.min(np - 2),
            Err(i) => if i == 0 { 0 } else { (i - 1).min(np - 2) },
        };
        let t0 = self.tau_profile[lo];
        let t1 = self.tau_profile[lo + 1];
        let dt = t1 - t0;
        let w = if dt.abs() > 1e-30 { ((tau - t0) / dt).clamp(0.0, 1.0) } else { 0.0 };
        let w1 = 1.0 - w;
        let base0 = lo * stride;
        let base1 = (lo + 1) * stride;
        for i in 0..n {
            let mut sum = 0.0;
            let row_off = i * n;
            for j in 0..n {
                let a_ij = w1 * self.mats_flat[base0 + row_off + j]
                         + w  * self.mats_flat[base1 + row_off + j];
                sum += a_ij * x[j];
            }
            y[i] = sum;
        }
    }
}

/// Integrate y' = A(τ)y. Returns (snapshots, n_steps, n_rejects).
pub(crate) fn integrate_linear_diffsol(
    tau_profile: &[f64],
    mats_flat: &[f64],
    n_state: usize,
    y0: &[f64],
    tau_eval: &[f64],
    cfg: &DiffsolConfig,
) -> Result<(Vec<Vec<f64>>, usize, usize), String> {
    let n = n_state;
    let n_eval = tau_eval.len();
    if n_eval == 0 { return Ok((Vec::new(), 0, 0)); }

    let profile = Arc::new(MatrixProfile {
        tau_profile: tau_profile.to_vec(),
        mats_flat: mats_flat.to_vec(),
        n_state: n,
    });
    let p1 = Arc::clone(&profile);
    let p2 = Arc::clone(&profile);
    let y0v = y0.to_vec();

    let problem = OdeBuilder::<NalgebraMat<f64>>::new()
        .t0(tau_eval[0])
        .h0(cfg.h_init)
        .rtol(cfg.rtol)
        .atol(vec![cfg.atol; n])
        .p(Vec::<f64>::new())
        .rhs_implicit(
            move |x: &NalgebraVec<f64>, _p: &NalgebraVec<f64>, t: f64, y: &mut NalgebraVec<f64>| {
                p1.matvec(t, x.as_slice(), y.as_mut_slice());
            },
            move |_x: &NalgebraVec<f64>, _p: &NalgebraVec<f64>, t: f64,
                  v: &NalgebraVec<f64>, y: &mut NalgebraVec<f64>| {
                p2.matvec(t, v.as_slice(), y.as_mut_slice());
            },
        )
        .init(
            move |_p: &NalgebraVec<f64>, _t: f64, y: &mut NalgebraVec<f64>| {
                let s = y.as_mut_slice();
                for i in 0..y0v.len() { s[i] = y0v[i]; }
            },
            n,
        )
        .build()
        .map_err(|e| format!("diffsol build: {}", e))?;

    // Dispatch to selected solver backend
    let mut snapshots = Vec::with_capacity(n_eval);
    let mut n_steps = 0_usize;

    match cfg.backend {
        SolverBackend::Bdf => {
            let mut solver = problem
                .bdf::<NalgebraLU<f64>>()
                .map_err(|e| format!("bdf init: {}", e))?;
            snapshots.push(solver.state().y.as_slice().to_vec());
            for i in 1..n_eval {
                solver.set_stop_time(tau_eval[i]).map_err(|e| format!("set_stop: {}", e))?;
                loop {
                    match solver.step() {
                        Ok(OdeSolverStopReason::TstopReached) => break,
                        Ok(OdeSolverStopReason::InternalTimestep) => { n_steps += 1; }
                        Ok(OdeSolverStopReason::RootFound(_)) => break,
                        Err(e) => return Err(format!("BDF step τ={:.2}: {}", tau_eval[i], e)),
                    }
                }
                n_steps += 1;
                snapshots.push(solver.state().y.as_slice().to_vec());
            }
        }
        SolverBackend::Esdirk34 | SolverBackend::TrBdf2 => {
            let ctx = NalgebraContext;
            let tableau = match cfg.backend {
                SolverBackend::Esdirk34 => Tableau::<NalgebraMat<f64>>::esdirk34(ctx),
                SolverBackend::TrBdf2 => Tableau::<NalgebraMat<f64>>::tr_bdf2(ctx),
                _ => unreachable!(),
            };
            let state = problem.rk_state::<NalgebraMat<f64>>(&tableau)
                .map_err(|e| format!("rk_state: {}", e))?;
            let mut solver = problem
                .sdirk_solver::<NalgebraLU<f64>, NalgebraMat<f64>>(state, tableau)
                .map_err(|e| format!("sdirk init: {}", e))?;
            snapshots.push(solver.state().y.as_slice().to_vec());
            for i in 1..n_eval {
                solver.set_stop_time(tau_eval[i]).map_err(|e| format!("set_stop: {}", e))?;
                loop {
                    match solver.step() {
                        Ok(OdeSolverStopReason::TstopReached) => break,
                        Ok(OdeSolverStopReason::InternalTimestep) => { n_steps += 1; }
                        Ok(OdeSolverStopReason::RootFound(_)) => break,
                        Err(e) => return Err(format!("ESDIRK step τ={:.2}: {}", tau_eval[i], e)),
                    }
                }
                n_steps += 1;
                snapshots.push(solver.state().y.as_slice().to_vec());
            }
        }
    }

    Ok((snapshots, n_steps, 0))
}

// Keep old name as alias for backward compatibility
pub(crate) fn integrate_linear_bdf(
    tau_profile: &[f64], mats_flat: &[f64], n_state: usize,
    y0: &[f64], tau_eval: &[f64], cfg: &DiffsolBdfConfig,
) -> Result<(Vec<Vec<f64>>, usize, usize), String> {
    let new_cfg = DiffsolConfig {
        rtol: cfg.rtol, atol: cfg.atol, h_init: cfg.h_init,
        backend: SolverBackend::Bdf,  // BDF for production (ESDIRK34 has Newton convergence issues on Boltzmann system)
    };
    integrate_linear_diffsol(tau_profile, mats_flat, n_state, y0, tau_eval, &new_cfg)
}

#[derive(Clone, Debug)]
pub(crate) struct DiffsolBdfConfig {
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
    pub(crate) h_init: f64,
}
impl Default for DiffsolBdfConfig {
    fn default() -> Self { Self { rtol: 1e-6, atol: 1e-9, h_init: 1.0 } }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run_exp_decay(backend: SolverBackend) {
        let alpha = 2.0;
        let mf = vec![-alpha, -alpha];
        let cfg = DiffsolConfig { rtol: 1e-8, atol: 1e-10, h_init: 0.01, backend: backend.clone() };
        let tau_eval: Vec<f64> = (0..=50).map(|i| i as f64 * 0.1).collect();
        let (snaps, steps, _) = integrate_linear_diffsol(
            &[0.0, 10.0], &mf, 1, &[1.0], &tau_eval, &cfg,
        ).unwrap();
        eprintln!("  {:?} exp_decay: {} steps", backend, steps);
        for &i in &[10, 50] {
            let exact = (-alpha * tau_eval[i]).exp();
            let err = (snaps[i][0] - exact).abs() / exact.max(1e-30);
            eprintln!("    t={:.1}: err={:.2e}", tau_eval[i], err);
            assert!(err < 1e-3, "{:?} err {:.2e}", backend, err);
        }
    }

    fn run_oscillator(backend: SolverBackend) {
        let omega = 5.0;
        let a = vec![0.0, omega, -omega, 0.0];
        let mut mf = Vec::new(); mf.extend_from_slice(&a); mf.extend_from_slice(&a);
        let cfg = DiffsolConfig { rtol: 1e-6, atol: 1e-9, h_init: 0.001, backend: backend.clone() };
        let tau_eval: Vec<f64> = (0..=200).map(|i| i as f64 * 0.1).collect();
        let (snaps, steps, _) = integrate_linear_diffsol(
            &[0.0, 20.0], &mf, 2, &[1.0, 0.0], &tau_eval, &cfg,
        ).unwrap();
        eprintln!("  {:?} oscillator: {} steps", backend, steps);
        for period in 1..=3 {
            let t = 2.0 * std::f64::consts::PI / omega * period as f64;
            let i = (t / 0.1).round() as usize;
            if i >= snaps.len() { continue; }
            let amp = (snaps[i][0].powi(2) + snaps[i][1].powi(2)).sqrt();
            eprintln!("    {}T: amp={:.4}", period, amp);
            assert!(amp > 0.8, "{:?} amp collapse: {:.4}", backend, amp);
        }
    }

    fn run_stiff_osc(backend: SolverBackend) {
        let a = vec![-100.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, -10.0, 0.0];
        let mut mf = Vec::new(); mf.extend_from_slice(&a); mf.extend_from_slice(&a);
        let cfg = DiffsolConfig { rtol: 1e-6, atol: 1e-9, h_init: 1e-4, backend: backend.clone() };
        let tau_eval: Vec<f64> = (0..=500).map(|i| i as f64 * 0.01).collect();
        let (snaps, steps, _) = integrate_linear_diffsol(
            &[0.0, 5.0], &mf, 3, &[1.0, 1.0, 0.0], &tau_eval, &cfg,
        ).unwrap();
        eprintln!("  {:?} stiff+osc: {} steps", backend, steps);
        assert!(snaps[10][0].abs() < 1e-3, "stiff not decayed");
        let osc = (snaps[10][1].powi(2) + snaps[10][2].powi(2)).sqrt();
        assert!(osc > 0.5, "osc died: {:.3}", osc);
    }

    #[test] fn test_bdf_decay() { run_exp_decay(SolverBackend::Bdf); }
    #[test] fn test_bdf_osc() { run_oscillator(SolverBackend::Bdf); }
    #[test] fn test_bdf_stiff() { run_stiff_osc(SolverBackend::Bdf); }

    #[test] fn test_esdirk34_decay() { run_exp_decay(SolverBackend::Esdirk34); }
    #[test] fn test_esdirk34_osc() { run_oscillator(SolverBackend::Esdirk34); }
    #[test] fn test_esdirk34_stiff() { run_stiff_osc(SolverBackend::Esdirk34); }

    #[test] fn test_trbdf2_decay() { run_exp_decay(SolverBackend::TrBdf2); }
    #[test] fn test_trbdf2_osc() { run_oscillator(SolverBackend::TrBdf2); }
    #[test] fn test_trbdf2_stiff() { run_stiff_osc(SolverBackend::TrBdf2); }
}
