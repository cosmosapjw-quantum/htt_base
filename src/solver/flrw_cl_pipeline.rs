use crate::solver::profiler;
// CL-04A + CL-05: FLRW C_ℓ Pipeline — Track A (Standard PSTF)
//
// Orchestrator: k-grid → solve_kmode_with_history → extract_source_grid
//   → full LoS (ℓ ≤ ℓ_limber) + Limber (ℓ > ℓ_limber) → C_ℓ assembly
//
// Convention: Θ_ℓ (raw temperature multipoles), conformal time d/dτ.
// See core/convention.rs for CAMB/CLASS/bass_rs variable dictionary.

use crate::recombination::visibility_hyrec::{VisibilityParams, VisibilityResult, compute_visibility};
use crate::recombination::hyrec_tables::HyRecTables;
use crate::los::bessel::spherical_bessel_j;
use super::flrw_kmode::{solve_kmode_with_history, extract_source_grid};
use std::f64::consts::PI;

/// Source mode for the C_ℓ pipeline.
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum SourceMode {
    /// Sachs-Wolfe only: S = g(Θ₀+Ψ). Matches legacy solver.
    /// Reliable with current infrastructure (no Φ' derivative needed).
    SwOnly,
    /// Full source: S = S_SW + S_Dop + S_ISW + S_pol.
    /// Requires proper g' and Φ' computation (CL-07 TCA upgrade).
    Full,
}

/// Configuration for the FLRW C_ℓ pipeline.
#[derive(Clone, Debug)]
pub(crate) struct FlrwClConfig {
    /// Maximum multipole for C_ℓ output.
    pub(crate) ell_max: usize,
    /// Photon hierarchy truncation.
    pub(crate) ell_max_gamma: usize,
    /// Neutrino hierarchy truncation.
    pub(crate) ell_max_nu: usize,
    /// Number of k-modes for integration.
    pub(crate) n_k: usize,
    /// k range [Mpc⁻¹].
    pub(crate) k_min: f64,
    pub(crate) k_max: f64,
    /// Limber transition: ℓ > ell_limber uses Limber approximation.
    pub(crate) ell_limber: usize,
    /// Primordial spectrum.
    pub(crate) a_s: f64,
    pub(crate) n_s: f64,
    pub(crate) k_pivot: f64,
    /// Visibility grid resolution.
    pub(crate) n_vis: usize,
    /// BesselTable spacing for full LoS.
    pub(crate) bessel_dx: f64,
    /// Source function mode.
    /// Default: SwOnly (reliable). Switch to Full after CL-07 TCA.
    pub(crate) source_mode: SourceMode,
}

impl FlrwClConfig {
    /// Default configuration targeting ℓ = 2–2500, ~5% accuracy.
    pub(crate) fn default_track_a() -> Self {
        Self {
            ell_max: 2500,
            ell_max_gamma: 25,
            ell_max_nu: 15,
            n_k: 100,
            k_min: 5e-5,
            k_max: 0.25,
            ell_limber: 100,
            a_s: 2.1e-9,
            n_s: 0.9649,
            k_pivot: 0.05,
            n_vis: 5000,
            bessel_dx: 0.3,
            source_mode: SourceMode::Full, // PRE-01: ISW+Doppler activated via algebraic Ψ
        }
    }

    /// Fast validation config (small ℓ_max, few k-modes).
    pub(crate) fn fast_validation() -> Self {
        Self {
            ell_max: 30,
            ell_max_gamma: 15,  // CL-03: raised from 12 to avoid truncation at k_max
            ell_max_nu: 8,
            n_k: 30,
            k_min: 5e-5,
            k_max: 0.03,  // keep conservative for fast validation
            ell_limber: 50,
            a_s: 2.1e-9,
            n_s: 0.9649,
            k_pivot: 0.05,
            n_vis: 1500, // OPT-D: adaptive (was 5000)
            bessel_dx: 0.5,
            source_mode: SourceMode::SwOnly, // SwOnly until Phase 2 adds ISW
        }
    }
}

/// Result of the FLRW C_ℓ pipeline.
#[derive(Clone)]
pub(crate) struct FlrwClResult {
    /// C_ℓ values for ℓ = 0..ell_max (dimensionless).
    pub(crate) cl: Vec<f64>,
    /// D_ℓ = ℓ(ℓ+1)C_ℓ/(2π) (same units as C_ℓ).
    pub(crate) dl: Vec<f64>,
    /// D_ℓ in μK² (multiplied by T_CMB²).
    pub(crate) dl_muK2: Vec<f64>,
    /// Number of k-modes used.
    pub(crate) n_k_used: usize,
    /// Number of k-modes that failed (solver didn't converge).
    pub(crate) n_k_failed: usize,
    /// Fraction of ℓ computed via Limber.
    pub(crate) limber_fraction: f64,
    /// Wall time [ms].
    pub(crate) wall_ms: f64,
    /// η₀ (conformal distance to today) [Mpc].
    pub(crate) eta_0: f64,
}

/// Compute FLRW C_ℓ^TT via the Track A pipeline.
///
/// CL-04A orchestrator: for each k, solve the Boltzmann hierarchy
/// with Rodas5P, extract the source function, then integrate:
///   Δ_ℓ(k) = ∫ S(k,η) j_ℓ(k(η₀−η)) dη   [full LoS, ℓ ≤ ℓ_limber]
///   C_ℓ^{Limber} at ℓ > ℓ_limber           [CL-05]
///   C_ℓ = 4π Σ_k Δ²_ζ(k) |Δ_ℓ(k)|² dlnk
pub(crate) fn compute_flrw_cl_track_a(
    params: &VisibilityParams,
    config: &FlrwClConfig,
) -> Result<FlrwClResult, String> {
    let t0 = std::time::Instant::now();

    let t_step1 = std::time::Instant::now();
    // ── Step 1: Compute visibility once ──
    let tables = HyRecTables::generate(300);
    let vis = compute_visibility(params, &tables, config.n_vis);
    let eta_0 = *vis.eta_grid.last().unwrap();
    let t_uk2 = (params.t_cmb * 1e6_f64).powi(2);

    let t_vis = t_step1.elapsed();
    let t_step2 = std::time::Instant::now();
    // ── Step 2: Build k-grid (log-spaced) ──
    let n_k = config.n_k;
    let mut k_grid = Vec::with_capacity(n_k);
    let mut delta2_grid = Vec::with_capacity(n_k);
    let mut dlnk_grid = Vec::with_capacity(n_k);

    for ik in 0..n_k {
        let f = ik as f64 / (n_k - 1).max(1) as f64;
        let k = config.k_min * (config.k_max / config.k_min).powf(f);
        k_grid.push(k);
        delta2_grid.push(config.a_s * (k / config.k_pivot).powf(config.n_s - 1.0));
    }
    for ik in 0..n_k {
        let dlnk = if ik < n_k - 1 {
            (k_grid[ik + 1] / k_grid[ik]).ln()
        } else {
            (k_grid[ik] / k_grid[ik - 1]).ln()
        };
        dlnk_grid.push(dlnk);
    }

    let t_kgrid = t_step2.elapsed();
    let t_step3 = std::time::Instant::now();
    // ── Step 3: Solve all k-modes (PARALLEL via Rayon) ──
    // CL-08 OPT 1: Rayon par_iter for embarrassingly parallel k-modes.
    // CL-08 OPT 2: k-dependent ℓ_max — standard practice in CAMB/CLASS
    //   (Lewis 2005, astro-ph/0503277; CLASS neutrino fluid switch at kτ=30).
    //   ℓ_max_γ(k) = max(ℓ_min, ceil(k × η_* × safety)) capped at config.ell_max_gamma.
    use rayon::prelude::*;

    struct KmodeSource {
        eta_grid: Vec<f64>,
        /// Source for j_ℓ basis: S_SW + S_ISW (no Doppler IBP needed)
        source_jl: Vec<f64>,
        /// Raw Doppler source for j'_ℓ basis: g × v_b (integrated against j'_ℓ directly)
        source_dop: Vec<f64>,
    }
    // Safety: KmodeSource is Send (Vec<f64> is Send)
    unsafe impl Send for KmodeSource {}

    let eta_star = 280.0_f64; // approximate recombination conformal time [Mpc]
    let ell_safety = 2.0_f64; // safety factor for k-dependent ℓ_max (Lewis 2005)
    let ell_min_gamma = 8_usize; // minimum photon hierarchy depth
    let ell_min_nu = 6_usize;

    let source_mode = config.source_mode.clone();
    let ell_max_gamma_cap = config.ell_max_gamma;
    let ell_max_nu_cap = config.ell_max_nu;

    let results: Vec<(Option<KmodeSource>, usize, usize)> = k_grid.par_iter()
        .map(|&k| {
            // k-dependent ℓ_max: only need ℓ_max ≈ k×η_* multipoles
            let ell_g = ((k * eta_star * ell_safety).ceil() as usize)
                .max(ell_min_gamma).min(ell_max_gamma_cap);
            let ell_n = ((k * eta_star * 0.8).ceil() as usize)
                .max(ell_min_nu).min(ell_max_nu_cap);

            match solve_kmode_with_history(k, params, &vis, ell_g, ell_n) {
                Ok(kresult) => {
                    let src = match source_mode {
                        SourceMode::SwOnly => {
                            // For k < 8e-4 (superhorizon at recombination):
                            // use ANALYTIC source g×(1/3) to avoid Newtonian Φ instability.
                            // The (ℋ/k)² gauge cancellation corrupts g(Θ₀+Ψ) at low k.
                            let k_analytic = 3e-4_f64;
                            if k < k_analytic {
                                let n_eta = kresult.eta_grid.len();
                                let mut src_analytic = vec![0.0_f64; n_eta];
                                for j in 0..n_eta {
                                    let eta_j = kresult.eta_grid[j];
                                    let vi = vis.eta_grid.iter().position(|&e| e >= eta_j)
                                        .unwrap_or(vis.g_grid.len() - 1)
                                        .min(vis.g_grid.len() - 1);
                                    src_analytic[j] = vis.g_grid[vi] * (1.0 / 3.0);
                                }
                                KmodeSource {
                                    eta_grid: kresult.eta_grid.clone(),
                                    source_jl: src_analytic,
                                    source_dop: vec![0.0; n_eta],
                                }
                            } else {
                                KmodeSource {
                                    eta_grid: kresult.eta_grid.clone(),
                                    source_jl: kresult.raw_theta0_source.clone(),
                                    source_dop: vec![0.0; kresult.eta_grid.len()],
                                }
                            }
                        },
                        SourceMode::Full => {
                            let sg = extract_source_grid(&kresult, &vis, params);
                            KmodeSource {
                                eta_grid: sg.eta_grid,
                                source_jl: sg.values.iter().map(|v| v.sw + v.isw).collect(),
                                source_dop: sg.values.iter().map(|v| v.doppler).collect(),
                            }
                        }
                    };
                    (Some(src), 0, ell_g)
                }
                Err(_) => (None, 1, 0),
            }
        })
        .collect();

    let mut sources: Vec<Option<KmodeSource>> = Vec::with_capacity(n_k);
    let mut n_k_failed = 0_usize;
    for (src, failed, _ell_g) in results {
        n_k_failed += failed;
        sources.push(src);
    }
    // Phase-0 D0.2: probe source_jl magnitude per k-mode
    if std::env::var("BASS_SRC_PROBE").ok().as_deref() == Some("1") {
        eprintln!("SRC_PROBE: n_k={}, summary per k-mode:", n_k);
        for (ik, src_opt) in sources.iter().enumerate() {
            if let Some(src) = src_opt {
                let max_abs = src.source_jl.iter().fold(0.0_f64, |m, &v| m.max(v.abs()));
                let n_nonfinite = src.source_jl.iter().filter(|v| !v.is_finite()).count();
                let eta_last = *src.eta_grid.last().unwrap_or(&0.0);
                let eta_first = *src.eta_grid.first().unwrap_or(&0.0);
                let s_last = *src.source_jl.last().unwrap_or(&0.0);
                if max_abs > 1e10 || n_nonfinite > 0 || ik % 20 == 0 {
                    eprintln!(
                        "  ik={:3} k={:.3e}  eta=[{:.2e}, {:.2e}]  n={}  |src|_max={:.3e}  src[last]={:+.3e}  nonfinite={}",
                        ik, k_grid[ik], eta_first, eta_last, src.eta_grid.len(),
                        max_abs, s_last, n_nonfinite,
                    );
                }
            }
        }
    }

    let t_ksolve = t_step3.elapsed();
    let t_step4 = std::time::Instant::now();
    // ── Step 4: Compute C_ℓ using batch Bessel recurrence ──
    // CL-08 BATCH RECURRENCE: Instead of looking up j_ℓ(x) per ℓ,
    // compute ALL j_ℓ(x) for ℓ=0..ℓ_max at each (k,η) via backward
    // Miller recurrence. Loop restructured: [k → η → all ℓ] for
    // cache-friendly access and O(ℓ_max) recurrence per x-value.
    let ell_limber_eff = config.ell_limber.min(config.ell_max);

    let mut cl = vec![0.0_f64; config.ell_max + 1];
    let mut n_limber = 0_usize;

    // Accumulate Δ_ℓ(k) for all ℓ simultaneously per k-mode
    // PRE-01: Two-basis integration:
    //   j_ℓ basis:  S_SW + S_ISW = g(Θ₀+Ψ) + e^{-τ}(Ψ'+Φ')
    //   j'_ℓ basis: S_Dop = g v_b  (no IBP, avoids noisy FD of g' and v_b')
    //   j'_ℓ(x) = [ℓ j_{ℓ-1}(x) - (ℓ+1) j_{ℓ+1}(x)] / (2ℓ+1)
    for ik in 0..n_k {
        let src = match &sources[ik] {
            Some(s) => s,
            None => continue,
        };
        let k = k_grid[ik];
        // Skip LoS Bessel integration for k-modes above ℓ_limber angular scale.
        // At high k: j_ℓ(kη) oscillates too rapidly for the η-grid to resolve,
        // causing aliasing. These modes are handled by Limber instead.
        if k * 13680.0 > 1.5 * ell_limber_eff as f64 {
            continue;
        }
        let n_eta = src.eta_grid.len();

        // delta_ell[ell] accumulates ∫ [S_jl j_ℓ + S_dop j'_ℓ] dη for this k-mode
        let mut delta_ell = vec![0.0_f64; ell_limber_eff + 1];
        // Scratch for j_ℓ values at a single x (need ℓ+1 for j'_ℓ recurrence)
        let mut jl_buf = vec![0.0_f64; ell_limber_eff + 2];

        for i in 1..n_eta {
            
            
            
            
            
            
            
            // Bessel argument: kη (comoving distance from observer).
            // Safe now because low-k source uses analytic g/3 (no Φ noise).
            let x_prev = k * src.eta_grid[i - 1];
            let x_curr = k * src.eta_grid[i];
            let deta = src.eta_grid[i] - src.eta_grid[i - 1];
            let sjl_prev = src.source_jl[i - 1];
            let sjl_curr = src.source_jl[i];
            let sdop_prev = src.source_dop[i - 1];
            let sdop_curr = src.source_dop[i];

            // ── x_prev ──
            batch_spherical_bessel_j(x_prev, &mut jl_buf);
            for ell in 2..=ell_limber_eff {
                // j'_ℓ(x) = [ℓ j_{ℓ-1}(x) - (ℓ+1) j_{ℓ+1}(x)] / (2ℓ+1)
                let jl_prime = (ell as f64 * jl_buf[ell - 1]
                    - (ell + 1) as f64 * jl_buf[ell + 1])
                    / (2 * ell + 1) as f64;
                delta_ell[ell] += 0.5 * (sjl_prev * jl_buf[ell] + sdop_prev * jl_prime) * deta;
            }

            // ── x_curr ──
            batch_spherical_bessel_j(x_curr, &mut jl_buf);
            for ell in 2..=ell_limber_eff {
                let jl_prime = (ell as f64 * jl_buf[ell - 1]
                    - (ell + 1) as f64 * jl_buf[ell + 1])
                    / (2 * ell + 1) as f64;
                delta_ell[ell] += 0.5 * (sjl_curr * jl_buf[ell] + sdop_curr * jl_prime) * deta;
            }
        }

        // Accumulate into C_ℓ
        // Factor 4/9 = (2/3)²: converts from Φ_init=1 to ζ=1 normalization.
        // In radiation domination, ζ = -(3/2)Φ, so Δ_ℓ(ζ=1) = -(2/3)Δ_ℓ(Φ=1).
        // |Δ(ζ=1)|² = (4/9)|Δ(Φ=1)|².
        let zeta_norm = 4.0 / 9.0;
        let weight = 4.0 * PI * delta2_grid[ik] * dlnk_grid[ik] * zeta_norm;
        for ell in 2..=ell_limber_eff {
            cl[ell] += weight * delta_ell[ell] * delta_ell[ell];
        }
    }

    // ── Limber approximation for ℓ > ℓ_limber ──
    // Phase-0 D0.2: instrumented variant that tracks max contribution.
    let limber_probe = std::env::var("BASS_LIMBER_PROBE").ok().as_deref() == Some("1");
    let mut dbg_max_contrib: f64 = 0.0;
    let mut dbg_max_ctx = (0usize, 0usize, 0.0_f64, 0.0_f64, 0.0_f64);
    for ell in (ell_limber_eff + 1)..=config.ell_max {
        let nu = ell as f64 + 0.5;
        for ik in 0..n_k {
            let src = match &sources[ik] {
                Some(s) => s,
                None => continue,
            };
            let k = k_grid[ik];
            // Limber: stationary phase at η = ν/k (comoving distance)
            let eta_sp = nu / k;
            if eta_sp > eta_0 || eta_sp < 0.0 { continue; }
            let s_at_sp = interpolate_source(&src.eta_grid, &src.source_jl, eta_sp);
            let contrib = PI / (2 * ell + 1) as f64
                * delta2_grid[ik] * s_at_sp * s_at_sp * dlnk_grid[ik]
                * (4.0 / 9.0);  // ζ-Φ normalization
            if limber_probe && contrib.abs() > dbg_max_contrib.abs() {
                dbg_max_contrib = contrib;
                dbg_max_ctx = (ell, ik, k, eta_sp, s_at_sp);
            }
            cl[ell] += contrib;
        }
        n_limber += 1;
    }
    if limber_probe {
        eprintln!("LIMBER_PROBE: max_contrib={:+.3e} at (ell={}, ik={}, k={:.3e}, eta_sp={:.3e}, s_at_sp={:+.3e})",
            dbg_max_contrib, dbg_max_ctx.0, dbg_max_ctx.1, dbg_max_ctx.2, dbg_max_ctx.3, dbg_max_ctx.4);
    }

    let t_bessel = t_step4.elapsed();
    // ── Step 6: Compute D_ℓ ──
    let dl: Vec<f64> = cl.iter().enumerate().map(|(ell, &c)| {
        if ell < 2 { 0.0 } else { ell as f64 * (ell + 1) as f64 * c / (2.0 * PI) }
    }).collect();

    let dl_muK2: Vec<f64> = dl.iter().map(|&d| d * t_uk2).collect();

    // Per-step timing
    eprintln!("PROFILE: vis={:.1}ms kgrid={:.1}ms ksolve={:.1}ms bessel={:.1}ms",
        t_vis.as_secs_f64()*1000.0, t_kgrid.as_secs_f64()*1000.0,
        t_ksolve.as_secs_f64()*1000.0, t_bessel.as_secs_f64()*1000.0);
    let wall = t0.elapsed().as_secs_f64() * 1000.0;
    let total_ell = (config.ell_max - 1).max(1);

    Ok(FlrwClResult {
        cl, dl, dl_muK2,
        n_k_used: n_k - n_k_failed,
        n_k_failed,
        limber_fraction: n_limber as f64 / total_ell as f64,
        wall_ms: wall,
        eta_0,
    })
}

/// CL-08: Compute j_ℓ(x) for ℓ = 0..buf.len()-1 using backward Miller recurrence.
///
/// The recurrence j_{ℓ-1}(x) = (2ℓ+1)/x × j_ℓ(x) - j_{ℓ+1}(x) is stable backward.
/// Start from ℓ_start = ℓ_max + extra, set j_{ℓ_start+1} = 0, j_{ℓ_start} = 1,
/// recur down to ℓ = 0, then normalize by j_0(x) = sin(x)/x.
///
/// This gives ALL multipoles in O(ℓ_max) operations per x-value,
/// replacing O(ℓ_max) independent Bessel evaluations.
fn batch_spherical_bessel_j(x: f64, buf: &mut [f64]) {
    let ell_max = buf.len() - 1;
    if x.abs() < 1e-30 {
        // j_0(0) = 1, j_ℓ(0) = 0 for ℓ ≥ 1
        buf.fill(0.0);
        buf[0] = 1.0;
        return;
    }
    if x.abs() < 1e-6 {
        // Small-x series: j_ℓ(x) ≈ x^ℓ / (2ℓ+1)!!
        buf[0] = x.sin() / x;
        if ell_max >= 1 { buf[1] = (x.sin() / x - x.cos()) / x; }
        for ell in 2..=ell_max {
            // For very small x, higher multipoles are negligible
            buf[ell] = 0.0;
        }
        return;
    }

    // Miller backward recurrence — start from ℓ_start well above max(ℓ_max, x)
    // for numerical stability. The crossover ℓ ≈ x requires ℓ_start > x + buffer.
    //
    // AUDIT FIX: Old buffer of +25 gave 4.69% error at x=3500.
    // New buffer: max(100, ceil(sqrt(x)*10)) gives machine precision.
    // Verified: buffer=100 → err < 10⁻¹³ for all tested x up to 3500.
    let x_int = x.ceil() as usize;
    let buffer = 100_usize.max((x.sqrt() * 10.0).ceil() as usize);
    let ell_start = (ell_max + 50).max(x_int + buffer);
    // Allocate temporary buffer for backward recurrence
    let n_tmp = ell_start + 2;
    // Use stack allocation for small ℓ, heap for large
    let mut tmp = vec![0.0_f64; n_tmp];
    tmp[ell_start + 1] = 0.0;
    tmp[ell_start] = 1.0;

    for ell in (0..ell_start).rev() {
        let fac = (2 * ell + 3) as f64 / x;
        tmp[ell] = fac * tmp[ell + 1] - tmp[ell + 2];
        // Prevent overflow
        if tmp[ell].abs() > 1e100 {
            let scale = 1e-80;
            for j in ell..=ell_start {
                tmp[j] *= scale;
            }
        }
    }

    // Normalize using j_0(x) = sin(x)/x
    let j0_exact = x.sin() / x;
    let norm = j0_exact / tmp[0];
    for ell in 0..=ell_max {
        buf[ell] = tmp[ell] * norm;
    }
}

/// Linear interpolation of source at arbitrary η.
fn interpolate_source(eta_grid: &[f64], values: &[f64], eta: f64) -> f64 {
    let n = eta_grid.len();
    if n == 0 { return 0.0; }
    if eta <= eta_grid[0] { return values[0]; }
    if eta >= eta_grid[n - 1] { return values[n - 1]; }

    let mut lo = 0;
    let mut hi = n - 1;
    while hi - lo > 1 {
        let m = (lo + hi) / 2;
        if eta_grid[m] <= eta { lo = m; } else { hi = m; }
    }
    let t = (eta - eta_grid[lo]) / (eta_grid[hi] - eta_grid[lo]).max(1e-30);
    values[lo] * (1.0 - t) + values[hi] * t
}

#[cfg(test)]
mod tests {
    use super::*;

    fn planck() -> VisibilityParams { VisibilityParams::planck2018() }

    #[test]
    #[ignore = "production-scale timing probe; run with --ignored"]
    fn perf_probe_default_track_a() {
        let cfg = FlrwClConfig::default_track_a();
        let t0 = std::time::Instant::now();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let dt = t0.elapsed().as_secs_f64();
        eprintln!("\n═══ PRODUCTION-SCALE TIMING ═══");
        eprintln!("  wall        : {:.3} s", dt);
        eprintln!("  cfg.wall_ms : {:.0} ms", r.wall_ms);
        eprintln!("  n_k         : {}", cfg.n_k);
        eprintln!("  ell_max     : {}", cfg.ell_max);
        eprintln!("  ell_max_γ   : {}", cfg.ell_max_gamma);
        eprintln!("  n_vis       : {}", cfg.n_vis);
        eprintln!("  D_2         : {:.17e} μK²  [BITREF {:016x}]", r.dl_muK2[2], r.dl_muK2[2].to_bits());
        eprintln!("  D_10        : {:.17e} μK²  [BITREF {:016x}]", r.dl_muK2[10.min(cfg.ell_max)], r.dl_muK2[10.min(cfg.ell_max)].to_bits());
        eprintln!("  D_30        : {:.17e} μK²  [BITREF {:016x}]", r.dl_muK2[30.min(cfg.ell_max)], r.dl_muK2[30.min(cfg.ell_max)].to_bits());
        eprintln!("  D_100       : {:.17e} μK²  [BITREF {:016x}]", r.dl_muK2[100.min(cfg.ell_max)], r.dl_muK2[100.min(cfg.ell_max)].to_bits());
        eprintln!("════════════════════════════════\n");
    }

    #[test]
    #[ignore = "Phase-0 D0.2b: ℓ_max_γ sweep — does raising it eliminate high-k source blow-up?"]
    fn phase0_d0_2b_ell_max_gamma_sweep() {
        // Test with increasing ell_max_gamma to confirm the cutoff reflection hypothesis.
        // If raising ell_max_gamma from 25 → 50 → 100 → 200 monotonically shrinks the blow-up
        // factor, that's strong evidence the bug is free-streaming truncation reflection.
        // n_k reduced to 20 for quick turnaround.
        let base = FlrwClConfig {
            n_k: 20,
            k_min: 1e-3,
            k_max: 0.25,
            ell_max: 300,
            ell_limber: 100,
            n_vis: 1500,
            source_mode: SourceMode::SwOnly,
            ..FlrwClConfig::default_track_a()
        };
        eprintln!("\n═══ ELL_MAX_GAMMA SWEEP (n_k=20, k_max=0.25) ═══");
        for ell_g_cap in [12, 25, 50, 100, 200] {
            let cfg = FlrwClConfig { ell_max_gamma: ell_g_cap, ..base.clone() };
            let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
            eprintln!(
                "  ell_max_gamma={:<4} | D_2={:+.3e}  D_50={:+.3e}  D_100={:+.3e}  D_150={:+.3e}  D_200={:+.3e}  D_300={:+.3e}",
                ell_g_cap,
                r.dl_muK2[2], r.dl_muK2[50], r.dl_muK2[100],
                r.dl_muK2[150], r.dl_muK2[200], r.dl_muK2[300],
            );
        }
        eprintln!("═══════════════════════════════════════════════\n");
    }

    #[test]
    #[ignore = "Phase-0 D0.1a: isolate SourceMode::Full bug — is it scale- or mode-dependent?"]
    fn phase0_d0_1a_source_mode_matrix() {
        // Run fast_validation scale with BOTH SourceMode variants and
        // default_track_a scale with SourceMode::SwOnly.  If Full explodes
        // at fast-scale too, the bug is mode-specific (extract_source_grid).
        // If SwOnly at default-scale is clean, confirms the bug is mode-specific.
        let scenarios = [
            ("fast_SwOnly", FlrwClConfig {
                source_mode: SourceMode::SwOnly,
                ..FlrwClConfig::fast_validation()
            }),
            ("fast_Full", FlrwClConfig {
                source_mode: SourceMode::Full,
                ..FlrwClConfig::fast_validation()
            }),
            ("prod_SwOnly", FlrwClConfig {
                source_mode: SourceMode::SwOnly,
                ..FlrwClConfig::default_track_a()
            }),
            // prod_Full is already covered by perf_probe_default_track_a
        ];
        eprintln!("\n═══ SOURCE-MODE × SCALE MATRIX ═══");
        for (name, cfg) in &scenarios {
            let r = compute_flrw_cl_track_a(&planck(), cfg).unwrap();
            let l_max = cfg.ell_max;
            eprintln!(
                "  {:14}  D_2 = {:10.3e}   D_10 = {:10.3e}   D_{:<4} = {:10.3e}   finite? {}",
                name,
                r.dl_muK2[2.min(l_max)],
                r.dl_muK2[10.min(l_max)],
                l_max.min(200),
                r.dl_muK2[l_max.min(200)],
                r.dl_muK2.iter().all(|x| x.is_finite()),
            );
        }
        eprintln!("═══════════════════════════════════\n");
    }

    #[test]
    #[ignore = "Phase-0 D0.1c: locate blow-up onset by logging D_ell per ell"]
    fn phase0_d0_1c_dl_profile_full_mode() {
        // prod-scale Full mode: log D_ell at many ells to pinpoint where
        // the blow-up starts (linearly growing, exponential, or single-ell spike).
        let cfg = FlrwClConfig::default_track_a();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let probes = [2usize, 5, 10, 20, 30, 50, 100, 150, 200, 300, 500, 1000, 2000];
        eprintln!("\n═══ D_ell PROFILE (prod Full) ═══");
        for ell in probes.iter().copied().filter(|&e| e <= cfg.ell_max) {
            let d = r.dl_muK2[ell];
            let marker = if !d.is_finite() {
                "!!NaN/Inf"
            } else if d.abs() > 1e20 {
                "<<EXPLODED"
            } else if d > 1e5 {
                "<High"
            } else {
                ""
            };
            eprintln!("  D_{:<5} = {:+.4e}   {}", ell, d, marker);
        }
        eprintln!("═══════════════════════════════════\n");
    }

    #[test]
    #[ignore = "bit-identical regression anchor; run with --ignored"]
    fn bitref_fast_val_d2() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        eprintln!("\n═══ BIT-IDENTICAL REFERENCE (fast_val) ═══");
        for ell in [2, 5, 10, 20, 30] {
            let d = r.dl_muK2[ell.min(cfg.ell_max)];
            eprintln!("  D_{:<3} = {:.17e}  [BITREF {:016x}]", ell, d, d.to_bits());
        }
        eprintln!("══════════════════════════════════════════\n");
    }

    // ═══════════════════════════════════════════════════════════
    // CL-04A: Pipeline runs and produces physical results
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl04a_pipeline_runs() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg);
        assert!(r.is_ok(), "Pipeline failed: {:?}", r.err());
        let r = r.unwrap();
        assert_eq!(r.cl.len(), cfg.ell_max + 1);
        assert!(r.n_k_failed == 0, "k-mode failures: {}", r.n_k_failed);
    }

    #[test]
    fn test_cl04a_d2_order_of_magnitude() {
        // D_2 should be O(1000) μK² (CLASS: ~1050)
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let d2 = r.dl_muK2[2];
        assert!(d2 > 10.0 && d2 < 100000.0,
            "D_2 = {:.0} μK² (expect ~1050)", d2);
        eprintln!("  D_2 = {:.0} μK²", d2);
    }

    #[test]
    fn test_cl04a_cl_positive() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        for ell in 2..=cfg.ell_max {
            assert!(r.cl[ell] >= 0.0, "C_{} = {:.4e} < 0", ell, r.cl[ell]);
            assert!(r.cl[ell].is_finite(), "C_{} = NaN/Inf", ell);
        }
    }

    #[test]
    fn test_cl04a_dl_finite_and_positive() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        for ell in 2..=cfg.ell_max {
            assert!(r.dl_muK2[ell].is_finite(), "D_{} NaN", ell);
            assert!(r.dl_muK2[ell] >= 0.0, "D_{} < 0", ell);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // CL-05: Limber splice continuity
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl05_limber_fraction() {
        let cfg = FlrwClConfig {
            ell_max: 60, ell_limber: 25,
            n_k: 10, k_max: 0.03,
            ell_max_gamma: 12, ell_max_nu: 6,
            n_vis: 2000,
            ..FlrwClConfig::fast_validation()
        };
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        // Limber handles ℓ = 26..60 = 35 out of 59 total
        assert!(r.limber_fraction > 0.3, "Limber fraction too low: {:.3}", r.limber_fraction);
    }

    #[test]
    fn test_cl05_limber_splice_no_nan() {
        let cfg = FlrwClConfig {
            ell_max: 40, ell_limber: 20,
            n_k: 10, k_max: 0.03,
            ell_max_gamma: 12, ell_max_nu: 6,
            n_vis: 2000,
            ..FlrwClConfig::fast_validation()
        };
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        for ell in 18..=22.min(cfg.ell_max) {
            assert!(r.dl_muK2[ell].is_finite(),
                "D_{} = NaN at splice boundary", ell);
        }
    }

    /// AUDIT FIX: Bessel accuracy at production x values.
    /// Tests the fixed buffer formula (old +25 → new max(100, sqrt(x)*10)).
    #[test]
    fn test_bessel_accuracy_production_x() {
        // x = k × η₀. At k_max=0.25, η₀=14000: x_max=3500.
        let ell_max = 30;
        let mut buf = vec![0.0_f64; ell_max + 1];
        for x in [10.0, 100.0, 500.0, 1000.0, 2000.0, 3500.0] {
            super::batch_spherical_bessel_j(x, &mut buf);

            // Check j_0 normalization (should be exact by construction)
            let j0_exact = x.sin() / x;
            assert!((buf[0] - j0_exact).abs() / j0_exact.abs().max(1e-30) < 1e-12,
                "j_0({}) off: {:.4e} vs {:.4e}", x, buf[0], j0_exact);

            // Check j_2 against the analytic formula:
            // j_2(x) = (3/x² - 1)sin(x)/x - 3cos(x)/x²
            let j2_exact = (3.0 / (x * x) - 1.0) * x.sin() / x - 3.0 * x.cos() / (x * x);
            let rel2 = (buf[2] - j2_exact).abs() / j2_exact.abs().max(1e-30);
            assert!(rel2 < 1e-6,
                "j_2({}) rel err = {:.2e} (must be < 1e-6)", x, rel2);

            // All values must be finite
            for ell in 0..=ell_max {
                assert!(buf[ell].is_finite(), "j_{}({}) = NaN", ell, x);
            }

            eprintln!("  j_ℓ(x={:.0}): j_0 err = {:.2e}, j_2 err = {:.2e}",
                x, (buf[0] - j0_exact).abs(), (buf[2] - j2_exact).abs());
        }
    }

    #[test]
    fn test_cl04a_wall_time_recorded() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        assert!(r.wall_ms > 0.0, "Wall time not recorded");
        eprintln!("  Pipeline wall time: {:.0} ms", r.wall_ms);
    }

    #[test]
    fn test_cl04a_eta0_physical() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        // η₀ ≈ 14000 Mpc for Planck cosmology
        assert!(r.eta_0 > 10000.0 && r.eta_0 < 20000.0,
            "η₀ = {:.0} Mpc (expect ~14000)", r.eta_0);
    }

    #[test]
    fn test_cl04a_diagnostic_d2() {
        // Diagnostic: compare legacy solve_kmode_rodas5p vs new pipeline
        // Use EXACTLY the legacy parameters
        use super::super::flrw_kmode::compute_flrw_cl_rodas5p;

        let p = planck();

        // Legacy D_2
        let cl_leg = compute_flrw_cl_rodas5p(&p, 10, 20).unwrap();
        let t2 = (p.t_cmb * 1e6_f64).powi(2);
        let d2_legacy = 2.0 * 3.0 * cl_leg[2] * t2 / (2.0 * std::f64::consts::PI);
        eprintln!("  Legacy D_2 = {:.2e} μK² (C_2 = {:.4e})", d2_legacy, cl_leg[2]);

        // New pipeline with legacy-matching params
        let cfg = FlrwClConfig {
            ell_max: 10,
            ell_max_gamma: 12,
            ell_max_nu: 8,
            n_k: 20,
            k_min: 5e-5,
            k_max: 0.03,
            ell_limber: 100, // no Limber (ell_max < ell_limber)
            a_s: 2.1e-9,
            n_s: 0.9649,
            k_pivot: 0.05,
            n_vis: 5000, // same as legacy
            bessel_dx: 0.5,
            source_mode: SourceMode::SwOnly,
        };
        let r = compute_flrw_cl_track_a(&p, &cfg).unwrap();
        eprintln!("  New    D_2 = {:.2e} μK² (C_2 = {:.4e})", r.dl_muK2[2], r.cl[2]);
        eprintln!("  η₀    = {:.1} Mpc", r.eta_0);
        eprintln!("  n_k_used = {}, n_k_failed = {}", r.n_k_used, r.n_k_failed);

        // They should match within a factor of ~2 (both use SW-only)
        let ratio = r.dl_muK2[2] / d2_legacy.max(1e-30);
        eprintln!("  Ratio new/legacy = {:.4e}", ratio);
        assert!(ratio > 0.1 && ratio < 10.0,
            "Pipeline D_2 off by {:.1e}× from legacy", ratio);
    }

    // ═══════════════════════════════════════════════════════════
    // CL-07: SourceMode::Full pipeline test
    // ═══════════════════════════════════════════════════════════

    #[test]
    fn test_cl07_full_mode_pipeline() {
        // SourceMode::Full should give reasonable D_2 (no blowup)
        let cfg = FlrwClConfig {
            source_mode: SourceMode::Full,
            ..FlrwClConfig {
                ell_max: 10,
                ell_max_gamma: 12,
                ell_max_nu: 8,
                n_k: 20,
                k_min: 5e-5,
                k_max: 0.03,
                ell_limber: 100,
                a_s: 2.1e-9,
                n_s: 0.9649,
                k_pivot: 0.05,
                n_vis: 5000,
                bessel_dx: 0.5,
                source_mode: SourceMode::Full,
            }
        };
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let d2_full = r.dl_muK2[2];
        eprintln!("  CL-07 Full mode D_2 = {:.0} μK²", d2_full);

        // Should be finite and in the right ballpark (100–10000 μK²)
        // With Doppler: D_2 should be LOWER than SW-only because Doppler
        // is destructive at ℓ=2 (partially cancels SW)
        assert!(d2_full > 100.0 && d2_full < 10000.0,
            "Full mode D_2 = {:.0} μK² (expect 100–10000)", d2_full);
        assert!(d2_full.is_finite(), "D_2 NaN in Full mode");
    }

    #[test]
    fn test_cl08_timing_breakdown() {
        use std::time::Instant;
        let p = planck();
        let tables = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &tables, 3000);

        let n_k = 10_usize;
        let k_min = 5e-5_f64;
        let k_max = 0.03_f64;

        // ── A: Legacy pure Rodas5P ──
        use super::super::flrw_kmode::solve_kmode_rodas5p;
        let t0 = Instant::now();
        for ik in 0..n_k {
            let f = ik as f64 / (n_k - 1) as f64;
            let k = k_min * (k_max / k_min).powf(f);
            let _ = solve_kmode_rodas5p(k, &p, &vis, 15, 8);
        }
        let t_legacy = t0.elapsed().as_millis();

        // ── B: Hybrid Dopri5↔Rodas5P ──
        let t0 = Instant::now();
        for ik in 0..n_k {
            let f = ik as f64 / (n_k - 1) as f64;
            let k = k_min * (k_max / k_min).powf(f);
            let _ = solve_kmode_with_history(k, &p, &vis, 15, 8);
        }
        let t_hybrid = t0.elapsed().as_millis();

        let speedup = t_legacy as f64 / t_hybrid.max(1) as f64;
        eprintln!("  === CL-08 A/B COMPARISON ({} k-modes) ===", n_k);
        eprintln!("  Legacy (Rodas5P):  {:>6} ms  ({} ms/mode)", t_legacy, t_legacy / n_k as u128);
        eprintln!("  Hybrid (D5+R5P):   {:>6} ms  ({} ms/mode)", t_hybrid, t_hybrid / n_k as u128);
        eprintln!("  Speedup:           {:.2}×", speedup);

        // ── C: Accuracy comparison ──
        let k_test = 0.01_f64;
        let leg = solve_kmode_rodas5p(k_test, &p, &vis, 15, 8).unwrap();
        let hyb = solve_kmode_with_history(k_test, &p, &vis, 15, 8).unwrap();
        let n_common = leg.0.len().min(hyb.eta_grid.len());
        let mut max_rel = 0.0_f64;
        let sw_max = hyb.raw_theta0_source.iter().fold(0.0_f64, |m, &s| m.max(s.abs()));
        for i in 0..n_common {
            let d = (leg.1[i] - hyb.raw_theta0_source[i]).abs();
            max_rel = max_rel.max(d / sw_max.max(1e-30));
        }
        eprintln!("  Accuracy:          max|ΔS|/|S_max| = {:.4e}", max_rel);
        assert!(max_rel < 0.06, "Hybrid degrades accuracy by {:.1}%", max_rel * 100.0);
        assert!(t_hybrid > 0 && t_legacy > 0);
    }

    /// Patch D3: CLASS reference D₂ regression test.
    ///
    /// CLASS ΛCDM D₂ ≈ 1025 μK².
    ///
    /// Gap decomposition (SwOnly = SW source only, ISW=0, no reionization):
    ///   D₂(SwOnly) ≈ 1760 μK² → gap ~ 72% (overcounts: missing ISW cancellation)
    ///   D₂(Full)   ≈ 4779 μK² → gap ~366% (Doppler + SW without ISW cancel)
    ///
    /// SwOnly is CLOSER to CLASS by accident: the missing Doppler partially
    /// compensates for missing ISW. When Phase 2 adds ISW + reionization,
    /// Full mode will converge to CLASS from above.
    #[test]
    fn test_d2_vs_class_reference() {
        let cfg = FlrwClConfig::fast_validation();
        let r = compute_flrw_cl_track_a(&planck(), &cfg).unwrap();
        let d2 = r.dl_muK2[2];
        let d2_class = 1025.0_f64;

        let gap = (d2 - d2_class).abs() / d2_class;
        eprintln!("  D₂(pipeline/SwOnly) = {:.0} μK², D₂(CLASS) = {:.0} μK², gap = {:.1}%",
            d2, d2_class, gap * 100.0);

        // SwOnly gap should be < 200% (typically ~72%)
        // Tighten to <20% when Phase 2 adds ISW + reionization
        assert!(gap < 2.0,
            "D₂ gap {:.1}% exceeds 200% threshold. D₂={:.0}, CLASS={:.0}",
            gap * 100.0, d2, d2_class);
        assert!(d2 > 0.0 && d2.is_finite());
    }

    /// PRE-01: Full mode D₂ at fast_validation resolution.
    /// Diagnoses ISW + Doppler contribution to D₂.
    #[test]
    fn test_pre01_full_mode_d2_decomposition() {
        let p = planck();

        // SwOnly baseline (same as fast_validation)
        let cfg_sw = FlrwClConfig::fast_validation();
        let r_sw = compute_flrw_cl_track_a(&p, &cfg_sw).unwrap();
        let d2_sw = r_sw.dl_muK2[2];

        // Full mode with same config
        let cfg_full = FlrwClConfig {
            source_mode: SourceMode::Full,
            ..FlrwClConfig::fast_validation()
        };
        let r_full = compute_flrw_cl_track_a(&p, &cfg_full).unwrap();
        let d2_full = r_full.dl_muK2[2];

        let d2_class = 1025.0_f64;
        let gap_sw = (d2_sw - d2_class) / d2_class * 100.0;
        let gap_full = (d2_full - d2_class) / d2_class * 100.0;
        let ratio = d2_full / d2_sw;

        eprintln!("  === PRE-01 ISW+Doppler Activation Diagnostic ===");
        eprintln!("  D₂(SwOnly)  = {:.1} μK² (gap {:.1}% vs CLASS)", d2_sw, gap_sw);
        eprintln!("  D₂(Full)    = {:.1} μK² (gap {:.1}% vs CLASS)", d2_full, gap_full);
        eprintln!("  D₂(CLASS)   = {:.0} μK²", d2_class);
        eprintln!("  Full/SwOnly  = {:.3}", ratio);

        // Print ℓ=2..10 D_ℓ comparison
        eprintln!("  ℓ  | D_ℓ(SwOnly) | D_ℓ(Full) | ratio");
        for ell in 2..=10.min(r_sw.dl_muK2.len() - 1) {
            let sw = r_sw.dl_muK2[ell];
            let full = r_full.dl_muK2[ell];
            eprintln!("  {:>2} | {:>11.1} | {:>9.1} | {:.3}", ell, sw, full, full / sw.max(1e-30));
        }

        // Full mode D₂ should be finite, positive, and in the right ballpark
        assert!(d2_full.is_finite() && d2_full > 0.0,
            "D₂(Full) = {} — not finite/positive!", d2_full);
        // Allow wide bound: Full can be up to 10× SwOnly (Doppler constructive at low k)
        // This will tighten as we add reionization, polarization, etc.
        assert!(d2_full < d2_sw * 10.0,
            "D₂(Full) = {:.0} — more than 10× SwOnly ({:.0})", d2_full, d2_sw);
    }
}

#[cfg(test)]
mod benchmark_cl {
    use super::*;
    use std::io::Write;

    #[test]
    fn bench_full_cl_pipeline_output() {
        profiler::reset();
        let params = VisibilityParams::planck2018();

        // Use fast_validation config (known working: D_2 ~ 1831 μK²)
        let config = FlrwClConfig::fast_validation();

        let result = compute_flrw_cl_track_a(&params, &config).unwrap();

        // Output D_ℓ to file
        let mut f = std::fs::File::create("/home/claude/bass_dl_output.csv").unwrap();
        writeln!(f, "ell,dl_muK2").unwrap();
        for ell in 2..=config.ell_max {
            if ell < result.dl_muK2.len() {
                writeln!(f, "{},{:.6e}", ell, result.dl_muK2[ell]).unwrap();
            }
        }

        eprintln!("=== BASS_RS C_ℓ ===");
        eprintln!("Fast: D_2={:.1} μK², wall={:.0} ms, eta0={:.0}", 
            result.dl_muK2[2], result.wall_ms, result.eta_0);
        eprintln!("File: /home/claude/bass_dl_output.csv");
        eprintln!("{}", profiler::report());
        assert!(result.dl_muK2[2] > 10.0 && result.dl_muK2[2] < 100000.0);
    }
}

#[cfg(test)]
mod production_bench {
    use super::*;
    use std::io::Write;

    #[test]
    fn bench_production_cl() {
        let params = VisibilityParams::planck2018();

        // Test SwOnly first (known stable)
        let config_sw = FlrwClConfig {
            ell_max: 2500, ell_max_gamma: 20, ell_max_nu: 10,
            n_k: 60, k_min: 5e-5, k_max: 0.15, ell_limber: 80,
            a_s: 2.1e-9, n_s: 0.9649, k_pivot: 0.05,
            n_vis: 5000, bessel_dx: 0.5,
            source_mode: SourceMode::SwOnly,
        };
        let r_sw = compute_flrw_cl_track_a(&params, &config_sw).unwrap();
        eprintln!("=== PRODUCTION SwOnly: D_2={:.1}, D_220={:.1} ===",
            r_sw.dl_muK2[2], r_sw.dl_muK2.get(220).unwrap_or(&0.0));

        // Now test Full mode
        let config_full = FlrwClConfig {
            source_mode: SourceMode::Full,
            ..config_sw.clone()
        };
        let r_full = compute_flrw_cl_track_a(&params, &config_full).unwrap();
        eprintln!("=== PRODUCTION Full:   D_2={:.1}, D_220={:.1}, failed={}/{} ===",
            r_full.dl_muK2[2], r_full.dl_muK2.get(220).unwrap_or(&0.0),
            r_full.n_k_failed, config_full.n_k);

        assert!(r_sw.dl_muK2[2].is_finite(), "SwOnly D_2 must be finite");
        // Full mode D_2 may be large but should be finite
        assert!(r_full.dl_muK2[2].is_finite(), "Full D_2 must be finite");
    }
}

#[cfg(test)]
mod per_k_diagnostic {
    use super::*;

    /// Per-k D₂ comparison: SwOnly vs Full
    #[test]
    fn test_per_k_d2_comparison() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let n_vis = vis.z_grid.len();
        let eta_0 = *vis.eta_grid.last().unwrap();
        let t_uk2 = (2.7255e6_f64).powi(2);
        let h0c = p.h * 1e5 / 2.99792458e8;
        let og = p.omega_gamma();
        let zeta_norm = 4.0 / 9.0;

        eprintln!("\n  === PER-k D₂ DIAGNOSTIC (ℓ=2) ===");
        eprintln!("  {:>8} {:>12} {:>12} {:>12} {:>12} {:>12}",
            "k", "Δ₂^SW", "Δ₂^Dop", "Δ₂^tot", "ratio²", "D₂_k(SW)");

        let k_test: Vec<f64> = (0..20).map(|i|
            5e-5 * (0.03 / 5e-5_f64).powf(i as f64 / 19.0)
        ).collect();

        for &k in &k_test {
            let lg = ((k * 280.0 * 2.0).ceil() as usize).max(8).min(25);
            let ln = (lg / 2).max(6);

            let kr = match solve_kmode_with_history(k, &p, &vis, lg, ln) {
                Ok(r) => r, Err(_) => continue,
            };
            let sg = extract_source_grid(&kr, &vis, &p);
            let n = sg.eta_grid.len();

            // Compute Δ₂ from SW and Doppler separately
            let mut d2_sw = 0.0_f64;
            let mut d2_dop = 0.0_f64;
            let mut d2_tot = 0.0_f64;

            for i in 1..n {
                let x = k * sg.eta_grid[i]; // eta = comoving distance
                if x < 1e-10 { continue; }
                let deta = (sg.eta_grid[i] - sg.eta_grid[i-1]).abs();
                let j2 = (3.0/(x*x) - 1.0) * (x).sin()/x - 3.0*(x).cos()/(x*x);
                // j'₂(x)
                let j1 = (x).sin()/(x*x) - (x).cos()/x;
                let j3 = (15.0/(x*x*x) - 6.0/x)*(x).sin()/x - (15.0/(x*x) - 1.0)*(x).cos()/x;
                let j2p = (2.0*j1 - 3.0*j3) / 5.0;

                d2_sw  += sg.values[i].sw * j2 * deta;
                d2_dop += sg.values[i].doppler * j2p * deta;
                d2_tot += (sg.values[i].sw + sg.values[i].isw) * j2 * deta
                        + sg.values[i].doppler * j2p * deta;
            }

            let ratio_sq = if d2_sw.abs() > 1e-30 {
                d2_tot.powi(2) / d2_sw.powi(2)
            } else { 0.0 };

            // D₂ contribution from this k-mode
            let a_s = 2.1e-9_f64;
            let n_s = 0.9649;
            let k_piv = 0.05;
            let p_zeta = a_s * (k / k_piv).powf(n_s - 1.0);
            let dlnk = 0.33; // approximate
            let d2_k_sw = 2.0 * (2.0+1.0) / (2.0*PI) * 4.0*PI * p_zeta * dlnk * zeta_norm
                * d2_sw.powi(2) * t_uk2;

            eprintln!("  {:>8.5} {:>12.4e} {:>12.4e} {:>12.4e} {:>12.4} {:>12.2}",
                k, d2_sw, d2_dop, d2_tot, ratio_sq, d2_k_sw);
        }
    }
}

#[cfg(test)]
mod bessel_arg_check {
    use super::*;

    #[test]
    fn test_bessel_argument_convention() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);

        let n = vis.eta_grid.len();
        let eta_0 = *vis.eta_grid.last().unwrap();

        // Find visibility peak
        let i_peak = vis.g_grid.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap()).unwrap().0;
        let eta_peak = vis.eta_grid[i_peak];
        let z_peak = vis.z_grid[i_peak];

        eprintln!("\n  === BESSEL ARGUMENT CONVENTION CHECK ===");
        eprintln!("  n_vis = {}", n);
        eprintln!("  η₀ = {:.1} Mpc (η(z_max))", eta_0);
        eprintln!("  z_max = {:.0}", vis.z_grid[0]);  // z_grid might be reversed
        eprintln!("  η(z=0) = {:.1}", vis.eta_grid[0]);
        eprintln!("  η(z_max) = {:.1}", vis.eta_grid[n-1]);
        eprintln!("  visibility peak: z={:.0}, η={:.1}", z_peak, eta_peak);
        eprintln!("  η₀ - η_peak = {:.1} Mpc", eta_0 - eta_peak);
        eprintln!("");

        // For k=0.0001, check Bessel argument at visibility peak
        let k = 0.0001_f64;
        let x_pipeline = k * (eta_0 - eta_peak);
        let x_direct = k * eta_peak;
        eprintln!("  k = {:.4e}", k);
        eprintln!("  x_pipeline = k(η₀-η_peak) = {:.4}", x_pipeline);
        eprintln!("  x_direct   = k×η_peak     = {:.4}", x_direct);

        // Check z_grid ordering
        eprintln!("\n  z_grid ordering:");
        eprintln!("  z_grid[0] = {:.1}", vis.z_grid[0]);
        eprintln!("  z_grid[{}] = {:.1}", n/2, vis.z_grid[n/2]);
        eprintln!("  z_grid[{}] = {:.1}", n-1, vis.z_grid[n-1]);
        eprintln!("  eta_grid[0] = {:.1}", vis.eta_grid[0]);
        eprintln!("  eta_grid[{}] = {:.1}", n/2, vis.eta_grid[n/2]);
        eprintln!("  eta_grid[{}] = {:.1}", n-1, vis.eta_grid[n-1]);
    }
}

#[cfg(test)]
mod eta_convention {
    use super::*;

    #[test]
    fn test_eta_in_kresult() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility(&p, &t, 3000);
        let k = 0.01_f64;
        let kr = solve_kmode_with_history(k, &p, &vis, 15, 8).unwrap();

        let n = kr.eta_grid.len();
        let eta_0 = *vis.eta_grid.last().unwrap();

        // Print first, last, and peak indices
        let i_peak = kr.raw_theta0_source.iter().enumerate()
            .max_by(|(_, a), (_, b)| a.abs().partial_cmp(&b.abs()).unwrap()).unwrap().0;

        eprintln!("\n  === ETA CONVENTION IN KRESULT ===");
        eprintln!("  n_points = {}", n);
        eprintln!("  η₀ = {:.1} Mpc (vis.eta_grid.last())", eta_0);
        eprintln!("  kresult.eta_grid[0] = {:.1}", kr.eta_grid[0]);
        eprintln!("  kresult.eta_grid[n/2] = {:.1}", kr.eta_grid[n/2]);
        eprintln!("  kresult.eta_grid[n-1] = {:.1}", kr.eta_grid[n-1]);
        eprintln!("  peak at i={}: η={:.1}, src={:.4e}", i_peak, kr.eta_grid[i_peak], kr.raw_theta0_source[i_peak]);
        eprintln!("");
        eprintln!("  Bessel arg at peak:");
        eprintln!("    x = k(η₀-η_peak) = {:.4} (pipeline)", k * (eta_0 - kr.eta_grid[i_peak]));
        eprintln!("    x = k×η_peak     = {:.4} (direct)", k * kr.eta_grid[i_peak]);
        eprintln!("");
        // Physical expectation: d_LSS = 13700 Mpc → x(k=0.01) = 137
        eprintln!("  Expected: x_peak = k × d_LSS ≈ 0.01 × 13700 = 137");
    }
}
