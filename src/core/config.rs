// Solver configuration, statistics, and Rodas5P tableau.

use crate::core::constants::*;

#[derive(Clone, Copy)]
pub(crate) struct PeeblesParams {
    pub(crate) h0_si: f64,
    pub(crate) omega_b: f64,
    pub(crate) omega_m: f64,
    pub(crate) omega_r: f64,
    pub(crate) omega_k: f64,
    pub(crate) omega_lambda: f64,
    pub(crate) t_cmb: f64,
    pub(crate) n_h_0: f64,
}

#[derive(Clone, Copy)]
pub(crate) struct Rodas5PConfig {
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
    pub(crate) max_steps: usize,
    pub(crate) h_init: Option<f64>,
    pub(crate) h_min: f64,
    pub(crate) h_max: f64,
    pub(crate) f_safety: f64,
    pub(crate) f_min: f64,
    pub(crate) f_max: f64,
    pub(crate) beta: f64,
    pub(crate) use_analytic_jacobian: bool,
    pub(crate) use_ft_term: bool,
    pub(crate) use_blas_lu: bool,  // PR-14A: use LAPACK dgetrf/dgetrs
    pub(crate) use_block_diag: bool,  // PR-14B: block-diagonal LU
    pub(crate) ell_max_gamma_hint: usize,  // needed for BlockDecomp construction
    pub(crate) ell_max_nu_hint: usize,
    pub(crate) ell_max_pol_hint: usize,
    pub(crate) include_pol_hint: bool,
    pub(crate) use_sparse: bool,  // BA-04: sparse CSR mat-vec path
}

#[derive(Clone, Copy)]
pub(crate) struct Rodas5PStats {
    pub(crate) n_steps: usize,
    pub(crate) n_rejected: usize,
    pub(crate) n_jac: usize,
    pub(crate) n_f_eval: usize,
    pub(crate) h_final: f64,
}

pub(crate) struct Rodas5PDiagnosticResult {
    pub(crate) out: Vec<f64>,
    pub(crate) history_z: Vec<f64>,
    pub(crate) history_y: Vec<f64>,
    pub(crate) stats: Rodas5PStats,
}

#[derive(Clone, Copy, Default)]
pub(crate) struct NativeSolveTiming {
    pub(crate) matrix_build_s: f64,
    pub(crate) integrate_s: f64,
}

// ── PR-13A controller diagnostics ──
#[derive(Clone, Default)]
pub(crate) struct ControllerDiagnostics {
    pub(crate) n_attempted: usize,
    pub(crate) max_reject_streak: usize,
    pub(crate) err_accepted_sum: f64,
    pub(crate) err_accepted_max: f64,
    pub(crate) err_accepted_count: usize,
    pub(crate) q_raw_sum: f64,
    pub(crate) q_after_clip_sum: f64,
    pub(crate) clip_fmin_count: usize,
    pub(crate) clip_fmax_count: usize,
    pub(crate) dt_accept_sum: f64,
    pub(crate) dt_reject_sum: f64,
}

impl ControllerDiagnostics {
    pub(crate) fn record_accept(&mut self, err: f64, h: f64, q_raw: f64, q_clipped: f64) {
        self.n_attempted += 1;
        self.err_accepted_sum += err;
        self.err_accepted_count += 1;
        if err > self.err_accepted_max { self.err_accepted_max = err; }
        self.q_raw_sum += q_raw;
        self.q_after_clip_sum += q_clipped;
        self.dt_accept_sum += h;
    }
    pub(crate) fn record_reject(&mut self, h: f64, streak: usize) {
        self.n_attempted += 1;
        self.dt_reject_sum += h;
        if streak > self.max_reject_streak { self.max_reject_streak = streak; }
    }
    pub(crate) fn record_clip(&mut self, q_raw: f64, q_clipped: f64, f_min: f64, f_max: f64) {
        if q_raw < f_min { self.clip_fmin_count += 1; }
        if q_raw > f_max { self.clip_fmax_count += 1; }
        let _ = q_clipped; // used in record_accept
    }
    pub(crate) fn err_accepted_mean(&self) -> f64 {
        if self.err_accepted_count > 0 { self.err_accepted_sum / self.err_accepted_count as f64 } else { 0.0 }
    }
    pub(crate) fn q_raw_mean(&self) -> f64 {
        if self.err_accepted_count > 0 { self.q_raw_sum / self.err_accepted_count as f64 } else { 0.0 }
    }
    pub(crate) fn q_after_clip_mean(&self) -> f64 {
        if self.err_accepted_count > 0 { self.q_after_clip_sum / self.err_accepted_count as f64 } else { 0.0 }
    }
    pub(crate) fn dt_accept_mean(&self) -> f64 {
        if self.err_accepted_count > 0 { self.dt_accept_sum / self.err_accepted_count as f64 } else { 0.0 }
    }
    pub(crate) fn dt_reject_mean(&self) -> f64 {
        let n_rej = self.n_attempted.saturating_sub(self.err_accepted_count);
        if n_rej > 0 { self.dt_reject_sum / n_rej as f64 } else { 0.0 }
    }
}

#[derive(Clone, Copy)]
pub(crate) struct Rodas5PTableau {
    pub(crate) gamma: f64,
    pub(crate) a: [[f64; 8]; 8],
    pub(crate) c: [[f64; 8]; 8],
    pub(crate) b: [f64; 8],
    pub(crate) bhat: [f64; 8],
}

pub(crate) fn rodas5p_tableau() -> Rodas5PTableau {
    let mut a = [[0.0; 8]; 8];
    a[1][0] = 3.0;
    a[2][0] = 2.849394379747939;
    a[2][1] = 0.45842242204463923;
    a[3][0] = -6.954028509809101;
    a[3][1] = 2.489845061869568;
    a[3][2] = -10.358996098473584;
    a[4][0] = 2.8029986275628964;
    a[4][1] = 0.5072464736228206;
    a[4][2] = -0.3988312541770524;
    a[4][3] = -0.04721187230404641;
    a[5][0] = -7.502846399306121;
    a[5][1] = 2.561846144803919;
    a[5][2] = -11.627539656261098;
    a[5][3] = -0.18268767659942256;
    a[5][4] = 0.030198172008377946;
    for j in 0..5 {
        a[6][j] = a[5][j];
        a[7][j] = a[5][j];
    }
    a[6][5] = 1.0;
    a[7][5] = 1.0;
    a[7][6] = 1.0;

    let mut c = [[0.0; 8]; 8];
    c[1][0] = -14.155112264123755;
    c[2][0] = -17.97296035885952;
    c[2][1] = -2.859693295451294;
    c[3][0] = 147.12150275711716;
    c[3][1] = -1.41221402718213;
    c[3][2] = 71.68940251302358;
    c[4][0] = 165.43517024871676;
    c[4][1] = -0.4592823456491126;
    c[4][2] = 42.90938336958603;
    c[4][3] = -5.961986721573306;
    c[5][0] = 24.854864614690072;
    c[5][1] = -3.0009227002832186;
    c[5][2] = 47.4931110020768;
    c[5][3] = 5.5814197821558125;
    c[5][4] = -0.6610691825249471;
    c[6][0] = 30.91273214028599;
    c[6][1] = -3.1208243349937974;
    c[6][2] = 77.79954646070892;
    c[6][3] = 34.28646028294783;
    c[6][4] = -19.097331116725623;
    c[6][5] = -28.087943162872662;
    c[7][0] = 37.80277123390563;
    c[7][1] = -3.2571969029072276;
    c[7][2] = 112.26918849496327;
    c[7][3] = 66.9347231244047;
    c[7][4] = -40.06618937091002;
    c[7][5] = -54.66780262877968;
    c[7][6] = -9.48861652309627;

    let b = [
        -7.502846399306121,
        2.561846144803919,
        -11.627539656261098,
        -0.18268767659942256,
        0.030198172008377946,
        1.0,
        1.0,
        1.0,
    ];
    let bhat = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0];
    Rodas5PTableau {
        gamma: 0.21193756319429014,
        a,
        c,
        b,
        bhat,
    }
}

