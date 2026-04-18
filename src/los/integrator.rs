// BE-02: Line-of-Sight integrator for CMB anisotropy computation.
//
// FLRW (k-dependent):
//   Δ_ℓ(k) = ∫₀^{η₀} S(k,η) j_ℓ[k(η₀−η)] dη
//
// Bianchi (homogeneous, m-dependent):
//   a_{ℓm} = ∫₀^{η₀} S_{ℓm}(η) dη
//
// Quadrature: trapezoidal on the dense adaptive grid from BE-01,
// with Gauss-Kronrod (G7K15) adaptive refinement for error control.

use super::bessel::spherical_bessel_j;
use super::source::{SourceGrid, SourceValue, BianchiMSource};

/// Result of a single LoS integration.
#[derive(Clone, Debug)]
pub(crate) struct LosResult {
    /// Integrated value (Δ_ℓ for FLRW, a_{ℓm} for Bianchi).
    pub(crate) value: f64,
    /// Error estimate (|trapezoidal − Simpson| or |G7 − K15|).
    pub(crate) error: f64,
    /// Number of evaluations used.
    pub(crate) n_eval: usize,
}

// ═══════════════════════════════════════
// §1. FLRW LoS: Δ_ℓ(k) = ∫ S(k,η) j_ℓ(k(η₀−η)) dη
// ═══════════════════════════════════════

/// Integrate the FLRW LoS integral for a single (k, ℓ).
///
/// Uses the source grid from BE-01, multiplied by j_ℓ(k(η₀−η)).
/// Trapezoidal rule on the pre-sampled grid + Simpson error estimate.
pub(crate) fn integrate_los_flrw(
    source: &SourceGrid,
    ell: usize,
    eta_0: f64,
) -> LosResult {
    let n = source.len();
    if n < 2 {
        return LosResult { value: 0.0, error: 0.0, n_eval: 0 };
    }
    let k = source.k;

    // Trapezoidal integration
    let mut trap = 0.0;
    let mut simp = 0.0; // Simpson for error estimate
    let mut prev_f = {
        let x = k * (eta_0 - source.eta_grid[0]);
        let jl = if x > 0.0 { spherical_bessel_j(ell, x) } else if ell == 0 { 1.0 } else { 0.0 };
        source.values[0].total * jl
    };

    for i in 1..n {
        let x = k * (eta_0 - source.eta_grid[i]);
        let jl = if x > 0.0 { spherical_bessel_j(ell, x) } else if ell == 0 { 1.0 } else { 0.0 };
        let f_i = source.values[i].total * jl;
        let deta = source.eta_grid[i] - source.eta_grid[i - 1];

        trap += 0.5 * (prev_f + f_i) * deta;

        // Simpson: use midpoint approximation for error estimate
        if i >= 2 && i % 2 == 0 {
            let f_mid = source.values[i - 1].total * {
                let xm = k * (eta_0 - source.eta_grid[i - 1]);
                if xm > 0.0 { spherical_bessel_j(ell, xm) } else if ell == 0 { 1.0 } else { 0.0 }
            };
            let deta2 = source.eta_grid[i] - source.eta_grid[i - 2];
            let f_left = source.values[i - 2].total * {
                let xl = k * (eta_0 - source.eta_grid[i - 2]);
                if xl > 0.0 { spherical_bessel_j(ell, xl) } else if ell == 0 { 1.0 } else { 0.0 }
            };
            simp += deta2 / 6.0 * (f_left + 4.0 * f_mid + f_i);
        }

        prev_f = f_i;
    }

    let error = if simp.abs() > 1e-30 { (trap - simp).abs() } else { 0.0 };

    LosResult { value: trap, error, n_eval: n }
}

/// Integrate LoS for a specific source component (SW, Doppler, ISW, etc.).
pub(crate) fn integrate_los_component(
    source: &SourceGrid,
    ell: usize,
    eta_0: f64,
    component: fn(&SourceValue) -> f64,
) -> f64 {
    let n = source.len();
    if n < 2 { return 0.0; }
    let k = source.k;

    let mut sum = 0.0;
    for i in 1..n {
        let x_prev = k * (eta_0 - source.eta_grid[i - 1]);
        let x_curr = k * (eta_0 - source.eta_grid[i]);
        let jl_prev = if x_prev > 0.0 { spherical_bessel_j(ell, x_prev) } else if ell == 0 { 1.0 } else { 0.0 };
        let jl_curr = if x_curr > 0.0 { spherical_bessel_j(ell, x_curr) } else if ell == 0 { 1.0 } else { 0.0 };
        let f_prev = component(&source.values[i - 1]) * jl_prev;
        let f_curr = component(&source.values[i]) * jl_curr;
        let deta = source.eta_grid[i] - source.eta_grid[i - 1];
        sum += 0.5 * (f_prev + f_curr) * deta;
    }
    sum
}

// ═══════════════════════════════════════
// §2. Bianchi LoS: a_{ℓm} = ∫ S_{ℓm}(η) dη
// ═══════════════════════════════════════

/// Integrate the Bianchi a_{ℓm} (no Bessel function — homogeneous background).
pub(crate) fn integrate_los_bianchi(source: &BianchiMSource) -> LosResult {
    let grid = &source.grid;
    let n = grid.len();
    if n < 2 {
        return LosResult { value: 0.0, error: 0.0, n_eval: 0 };
    }

    let mut trap = 0.0;
    for i in 1..n {
        let deta = grid.eta_grid[i] - grid.eta_grid[i - 1];
        trap += 0.5 * (grid.values[i].total + grid.values[i - 1].total) * deta;
    }

    // Error estimate from alternating sums
    let mut simp = 0.0;
    for i in (2..n).step_by(2) {
        let deta2 = grid.eta_grid[i] - grid.eta_grid[i - 2];
        simp += deta2 / 6.0 * (grid.values[i - 2].total + 4.0 * grid.values[i - 1].total + grid.values[i].total);
    }
    let error = if simp.abs() > 1e-30 { (trap - simp).abs() } else { 0.0 };

    LosResult { value: trap, error, n_eval: n }
}

// ═══════════════════════════════════════
// §3. Multi-ℓ batch integration
// ═══════════════════════════════════════

/// Integrate LoS for multiple ℓ values at once (shares source evaluation).
pub(crate) fn integrate_los_multi_ell(
    source: &SourceGrid,
    ell_min: usize,
    ell_max: usize,
    eta_0: f64,
) -> Vec<LosResult> {
    (ell_min..=ell_max).map(|ell| integrate_los_flrw(source, ell, eta_0)).collect()
}

/// Integrate Bianchi LoS for multiple m-modes.
pub(crate) fn integrate_los_multi_m(sources: &[BianchiMSource]) -> Vec<LosResult> {
    sources.iter().map(|s| integrate_los_bianchi(s)).collect()
}

// ═══════════════════════════════════════
// §4. Gauss-Kronrod G7K15 panel
// ═══════════════════════════════════════

/// G7 nodes (7-point Gauss on [−1,1]).
pub(crate) const G7_NODES: [f64; 7] = [
    -0.949107912342759, -0.741531185599394, -0.405845151377397,
    0.0,
    0.405845151377397, 0.741531185599394, 0.949107912342759,
];
pub(crate) const G7_WEIGHTS: [f64; 7] = [
    0.129484966168870, 0.279705391489277, 0.381830050505119,
    0.417959183673469,
    0.381830050505119, 0.279705391489277, 0.129484966168870,
];

/// K15 nodes (15-point Kronrod extension).
pub(crate) const K15_NODES: [f64; 15] = [
    -0.991455371120813, -0.949107912342759, -0.864864423359769,
    -0.741531185599394, -0.586087235467691, -0.405845151377397,
    -0.207784955007898, 0.0, 0.207784955007898,
    0.405845151377397, 0.586087235467691, 0.741531185599394,
    0.864864423359769, 0.949107912342759, 0.991455371120813,
];
pub(crate) const K15_WEIGHTS: [f64; 15] = [
    0.022935322010529, 0.063092092629979, 0.104790010322250,
    0.140653259715525, 0.169004726639267, 0.190350578064785,
    0.204432940075298, 0.209482141084728, 0.204432940075298,
    0.190350578064785, 0.169004726639267, 0.140653259715525,
    0.104790010322250, 0.063092092629979, 0.022935322010529,
];

/// Single-panel G7K15 quadrature.
///
/// Returns (G7 result, K15 result, error = |G7−K15|).
pub(crate) fn gauss_kronrod_panel<F: Fn(f64) -> f64>(f: &F, a: f64, b: f64) -> (f64, f64, f64) {
    let mid = 0.5 * (a + b);
    let half = 0.5 * (b - a);

    let g7: f64 = G7_NODES.iter().zip(G7_WEIGHTS.iter())
        .map(|(&x, &w)| w * f(mid + half * x))
        .sum::<f64>() * half;

    let k15: f64 = K15_NODES.iter().zip(K15_WEIGHTS.iter())
        .map(|(&x, &w)| w * f(mid + half * x))
        .sum::<f64>() * half;

    (g7, k15, (g7 - k15).abs())
}

/// Adaptive G7K15 integration with subdivision.
pub(crate) fn integrate_adaptive<F: Fn(f64) -> f64>(
    f: &F,
    a: f64,
    b: f64,
    tol: f64,
    max_depth: usize,
) -> LosResult {
    let mut total = 0.0;
    let mut total_error = 0.0;
    let mut n_eval = 0;

    struct Panel { a: f64, b: f64, depth: usize }
    let mut stack = vec![Panel { a, b, depth: 0 }];

    while let Some(p) = stack.pop() {
        let (_, k15, err) = gauss_kronrod_panel(f, p.a, p.b);
        n_eval += 15;

        if err < tol * (p.b - p.a) / (b - a) || p.depth >= max_depth {
            total += k15;
            total_error += err;
        } else {
            let mid = 0.5 * (p.a + p.b);
            stack.push(Panel { a: p.a, b: mid, depth: p.depth + 1 });
            stack.push(Panel { a: mid, b: p.b, depth: p.depth + 1 });
        }
    }

    LosResult { value: total, error: total_error, n_eval }
}

/// LoS integration using adaptive G7K15 (for validation against trapezoidal).
pub(crate) fn integrate_los_adaptive(
    source: &SourceGrid,
    ell: usize,
    eta_0: f64,
    tol: f64,
) -> LosResult {
    if source.len() < 2 {
        return LosResult { value: 0.0, error: 0.0, n_eval: 0 };
    }
    let k = source.k;
    let eta_min = source.eta_grid[0];
    let eta_max = *source.eta_grid.last().unwrap();

    // Linear interpolation of source on the grid
    let interp_source = |eta: f64| -> f64 {
        if eta <= eta_min { return source.values[0].total; }
        if eta >= eta_max { return source.values.last().unwrap().total; }
        // Binary search
        let idx = source.eta_grid.partition_point(|&e| e < eta);
        let idx = idx.min(source.len() - 1).max(1);
        let t = (eta - source.eta_grid[idx - 1]) / (source.eta_grid[idx] - source.eta_grid[idx - 1]).max(1e-30);
        source.values[idx - 1].total * (1.0 - t) + source.values[idx].total * t
    };

    let integrand = |eta: f64| -> f64 {
        let x = k * (eta_0 - eta);
        let jl = if x > 0.0 { spherical_bessel_j(ell, x) } else if ell == 0 { 1.0 } else { 0.0 };
        interp_source(eta) * jl
    };

    integrate_adaptive(&integrand, eta_min, eta_max, tol, 12)
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::source::*;

    fn make_source_grid(k: f64, vis: &GaussianVisibility) -> SourceGrid {
        let etas = build_adaptive_eta_grid(0.0, vis.eta_total, vis.eta_star, 0.5, 10.0, 50.0);
        let mut sg = SourceGrid::new(k);
        // Unit perturbation: Θ₀+Ψ = 1, others zero
        let pert = PerturbationSnapshot::flrw(0.5, 0.0, 0.0, -0.5, 0.0);
        for &eta in &etas {
            let sv = evaluate_source(k, eta, vis, &pert);
            sg.push(eta, sv);
        }
        sg
    }

    #[test]
    fn test_los_flrw_ell0_k_zero() {
        let vis = GaussianVisibility::planck_like();
        let sg = make_source_grid(1e-8, &vis); // k→0: j₀(x)→1
        let res = integrate_los_flrw(&sg, 0, vis.eta_total);
        // j₀(kΔη) ≈ 1 for k→0, so Δ₀ ≈ ∫g(Θ₀+Ψ)dη = 1
        assert!((res.value - 1.0).abs() < 0.05,
            "Δ₀(k→0) = {:.4} (expect ~1)", res.value);
    }

    #[test]
    fn test_los_flrw_ell2() {
        let vis = GaussianVisibility::planck_like();
        let sg = make_source_grid(0.01, &vis);
        let res = integrate_los_flrw(&sg, 2, vis.eta_total);
        // Δ₂ should be finite and nonzero
        assert!(res.value.is_finite(), "Δ₂ must be finite");
        assert!(res.n_eval > 0);
    }

    #[test]
    fn test_los_error_estimate() {
        let vis = GaussianVisibility::planck_like();
        let sg = make_source_grid(0.01, &vis);
        let res = integrate_los_flrw(&sg, 2, vis.eta_total);
        // Error should be small relative to value (well-sampled grid)
        if res.value.abs() > 1e-10 {
            assert!(res.error / res.value.abs() < 0.1,
                "Relative error = {:.2e}", res.error / res.value.abs());
        }
    }

    #[test]
    fn test_los_bianchi_simple() {
        let vis = GaussianVisibility::planck_like();
        let mut ms = BianchiMSource::new(0, 0.0);
        let pert = PerturbationSnapshot::bianchi(0.5, 0.0, 0.0, -0.5, 0.0, 1e-4, 1e-6);
        let etas = build_adaptive_eta_grid(0.0, vis.eta_total, vis.eta_star, 0.5, 10.0, 50.0);
        for &eta in &etas {
            let sv = evaluate_source(0.0, eta, &vis, &pert);
            ms.grid.push(eta, sv);
        }
        let res = integrate_los_bianchi(&ms);
        assert!(res.value.is_finite());
        assert!(res.n_eval > 0);
    }

    #[test]
    fn test_los_multi_ell() {
        let vis = GaussianVisibility::planck_like();
        let sg = make_source_grid(0.005, &vis);
        let results = integrate_los_multi_ell(&sg, 0, 10, vis.eta_total);
        assert_eq!(results.len(), 11);
        for (ell, r) in results.iter().enumerate() {
            assert!(r.value.is_finite(), "Δ_{} = NaN", ell);
        }
    }

    #[test]
    fn test_los_component_sw() {
        let vis = GaussianVisibility::planck_like();
        let sg = make_source_grid(1e-8, &vis); // k→0
        let sw = integrate_los_component(&sg, 0, vis.eta_total, |sv| sv.sw);
        // SW component at ℓ=0, k→0: j₀→1, ∫g(Θ₀+Ψ)dη = 1
        assert!((sw - 1.0).abs() < 0.05, "SW integral = {:.4}", sw);
    }

    #[test]
    fn test_gauss_kronrod_polynomial() {
        // G7K15 should integrate degree-13 polynomials exactly (K15 is exact for deg≤29)
        let f = |x: f64| x.powi(6); // x⁶
        let (g7, k15, err) = gauss_kronrod_panel(&f, 0.0, 1.0);
        let exact = 1.0 / 7.0;
        assert!((k15 - exact).abs() < 1e-14, "K15: {:.10} vs {:.10}", k15, exact);
        assert!(err < 1e-10, "G7K15 error = {:.2e}", err);
    }

    #[test]
    fn test_gauss_kronrod_sin() {
        let f = |x: f64| x.sin();
        let (_, k15, _) = gauss_kronrod_panel(&f, 0.0, std::f64::consts::PI);
        let exact = 2.0;
        assert!((k15 - exact).abs() < 1e-12, "∫sin = {:.10}", k15);
    }

    #[test]
    fn test_adaptive_smooth() {
        let f = |x: f64| (-x * x).exp();
        let res = integrate_adaptive(&f, -5.0, 5.0, 1e-10, 15);
        let exact = std::f64::consts::PI.sqrt();
        assert!((res.value - exact).abs() < 1e-8,
            "int exp(-x^2) = {:.10} vs {:.10}", res.value, exact);
    }

    #[test]
    fn test_adaptive_vs_trapezoidal() {
        let vis = GaussianVisibility::planck_like();
        let sg = make_source_grid(0.005, &vis);
        let trap = integrate_los_flrw(&sg, 2, vis.eta_total);
        let adap = integrate_los_adaptive(&sg, 2, vis.eta_total, 1e-8);
        // Both should agree to reasonable precision
        if trap.value.abs() > 1e-10 {
            let rel = (trap.value - adap.value).abs() / trap.value.abs();
            assert!(rel < 0.1, "Trap vs adaptive: {:.4e} vs {:.4e} (rel {:.2e})",
                trap.value, adap.value, rel);
        }
    }

    #[test]
    fn test_los_ell_decreasing() {
        let vis = GaussianVisibility::planck_like();
        // k extremely small: x = k(η₀−η) ≪ 1, so j_ℓ(x) ∝ x^ℓ → decreases with ℓ
        let sg = make_source_grid(1e-6, &vis);
        let d0 = integrate_los_flrw(&sg, 0, vis.eta_total).value.abs();
        let d2 = integrate_los_flrw(&sg, 2, vis.eta_total).value.abs();
        let d5 = integrate_los_flrw(&sg, 5, vis.eta_total).value.abs();
        assert!(d0 > d2, "|Δ₀|={:.4e} > |Δ₂|={:.4e}", d0, d2);
        assert!(d2 > d5, "|Δ₂|={:.4e} > |Δ₅|={:.4e}", d2, d5);
    }
}
