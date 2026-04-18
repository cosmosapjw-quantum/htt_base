// ═══════════════════════════════════════════════════════════════════════
// boundary_eft.rs — PSTF Boundary EFT: ℓ-space tail self-energy
// ═══════════════════════════════════════════════════════════════════════
//
// Implements the exact continued-fraction self-energy Σ_L(s) from
// integrating out the ℓ > L angular UV tail of the Boltzmann hierarchy.
//
// Physical motivation: even when the ODE solver is stable, truncating
// at ℓ_max << k×η₀ discards ~2000 multipoles whose backreaction on
// the retained sector (ℓ ≤ L) is non-zero. This module quantifies
// that backreaction exactly (in the collisionless free-streaming limit)
// via the Mori-Zwanzig / Schur complement formalism.
//
// Key formula (scalar FLRW, collisionless):
//   Σ_L(s) = -ω² × (L+1)²/[(2L+1)(2L+3)] × R_{L+1}(s)
//   R_ℓ(s) = 1 / [s + ω²(ℓ+1)²/((2ℓ+1)(2ℓ+3)) × R_{ℓ+1}(s)]
//
// The self-energy modifies the top-shell equation:
//   I_L' = [exact retained terms] + Σ_L(s) × I_L  (in Laplace domain)
//
// In time domain, Σ_L(s) becomes a memory kernel — non-Markovian.
// Few-pole rational approximation converts it to auxiliary ODEs.

/// Evaluate the continued fraction resolvent R_ℓ(s) for the
/// collisionless free-streaming tail, truncated at ℓ_tail_max.
///
/// R_ℓ(s) = 1 / [s + α_{ℓ+1} × R_{ℓ+1}(s)]
/// where α_ℓ = ω² × ℓ² / [(2ℓ-1)(2ℓ+1)]
///
/// Evaluated bottom-up from ℓ_tail_max (where R = 1/s).
pub fn resolvent_continued_fraction(
    s: f64,      // Laplace variable (frequency)
    omega: f64,  // ω = k/S (streaming rate)
    ell_start: usize,  // L+1: first unresolved shell
    ell_tail_max: usize,  // truncation of the continued fraction
) -> f64 {
    let mut r = 1.0 / s;  // R at ℓ_tail_max: 1/s (free endpoint)
    
    for ell in (ell_start..=ell_tail_max).rev() {
        let l = ell as f64;
        let alpha = omega * omega * (l + 1.0).powi(2)
            / ((2.0 * l + 1.0) * (2.0 * l + 3.0));
        let denom = s + alpha * r;
        if denom.abs() < 1e-30 { r = 1.0 / 1e-30; }
        else { r = 1.0 / denom; }
    }
    r
}

/// Compute the exact self-energy Σ_L(s) for the top retained shell.
///
/// Σ_L(s) = -ω² × (L+1)² / [(2L+1)(2L+3)] × R_{L+1}(s)
pub fn self_energy(
    s: f64,
    omega: f64,
    ell_max: usize,      // L: last retained shell
    ell_tail_max: usize,  // where to truncate the continued fraction
) -> f64 {
    let l = ell_max as f64;
    let coupling = omega * omega * (l + 1.0).powi(2)
        / ((2.0 * l + 1.0) * (2.0 * l + 3.0));
    let r = resolvent_continued_fraction(s, omega, ell_max + 1, ell_tail_max);
    -coupling * r
}

/// Compute Σ_L(s) on a frequency grid and return (s_grid, Σ_grid).
/// Useful for diagnosing the frequency dependence / memory structure.
pub fn self_energy_spectrum(
    omega: f64,
    ell_max: usize,
    ell_tail_max: usize,
    s_grid: &[f64],
) -> Vec<f64> {
    s_grid.iter()
        .map(|&s| self_energy(s, omega, ell_max, ell_tail_max))
        .collect()
}

/// Markovian (local) approximation: Σ_L(s) ≈ Σ_L(s₀) for some reference s₀.
/// Returns the effective damping rate Γ_eff = -Re[Σ_L(s₀)].
///
/// If s₀ = ω (streaming frequency), this gives the "outgoing flux" rate.
pub fn markovian_damping_rate(
    omega: f64,
    ell_max: usize,
    ell_tail_max: usize,
) -> f64 {
    // Evaluate at s = ω (characteristic streaming frequency)
    let sigma = self_energy(omega, omega, ell_max, ell_tail_max);
    -sigma  // positive = damping
}

/// Measure the ℓ_max-dependent correction magnitude.
///
/// Returns: (Γ_local, Σ_dc, Σ_streaming) — three characterizations:
///   Γ_local: Markovian damping rate at s=ω
///   Σ_dc: DC correction Σ(s→0⁺) (static backreaction)
///   Σ_streaming: correction at the streaming frequency s=ω
pub fn correction_magnitudes(
    k: f64,
    a_h: f64,  // ℋ = aH
    ell_max: usize,
    ell_tail_max: usize,
) -> (f64, f64, f64) {
    let omega = k;  // In conformal time, ω = k (streaming rate = wavenumber)
    let gamma = markovian_damping_rate(omega, ell_max, ell_tail_max);
    let sigma_dc = self_energy(1e-6 * omega, omega, ell_max, ell_tail_max);
    let sigma_stream = self_energy(omega, omega, ell_max, ell_tail_max);
    (gamma, sigma_dc, sigma_stream)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Verify continued fraction convergence as tail length increases.
    #[test]
    fn test_cf_convergence() {
        let omega = 0.05;  // k = 0.05 Mpc⁻¹
        let ell_max = 20;
        let s = omega;

        eprintln!("\n  === Continued fraction convergence (k={}, ℓ_max={}, s=ω) ===", omega, ell_max);
        for &tail_max in &[25_usize, 50, 100, 200, 500, 1000, 2000] {
            let sigma = self_energy(s, omega, ell_max, tail_max);
            let gamma = -sigma;
            eprintln!("  tail_max={:>5}: Σ={:>12.6e}, Γ_eff={:.6e}, Γ/ω={:.4}",
                tail_max, sigma, gamma, gamma / omega);
        }
    }

    /// Measure correction magnitude across k and ℓ_max.
    #[test]
    fn test_correction_vs_lmax() {
        eprintln!("\n  === Self-energy correction: Γ/ω as function of ℓ_max ===");
        eprintln!("  {:>6} | {:>6} {:>6} {:>6} {:>6} {:>6}",
            "ℓ_max", "k=0.01", "k=0.05", "k=0.10", "k=0.15", "k=0.20");
        eprintln!("  {}", "-".repeat(50));

        for &lmax in &[10_usize, 20, 40, 60, 80, 100, 150, 200] {
            let mut row = format!("  {:>6} |", lmax);
            for &k in &[0.01_f64, 0.05, 0.10, 0.15, 0.20] {
                let omega = k;
                let tail_max = 3000;
                let gamma = markovian_damping_rate(omega, lmax, tail_max);
                let ratio = gamma / omega;
                row += &format!(" {:>6.3}", ratio);
            }
            eprintln!("{}", row);
        }
    }

    /// Frequency-dependent Σ_L(s): check non-Markovianity.
    #[test]
    fn test_frequency_dependence() {
        let omega = 0.10;
        let ell_max = 40;
        let tail_max = 2000;

        eprintln!("\n  === Σ_L(s) frequency dependence (k={}, ℓ_max={}) ===", omega, ell_max);
        for &ratio in &[0.01_f64, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0] {
            let s = ratio * omega;
            let sigma = self_energy(s, omega, ell_max, tail_max);
            eprintln!("  s/ω={:>5.2}: Σ={:>12.6e}, Σ/ω={:>8.4}", ratio, sigma, sigma / omega);
        }
    }

    /// Compare: source with vs without Σ_L correction (diagnostic).
    /// This measures how much the truncated tail WOULD change the
    /// top-shell evolution rate.
    #[test]
    fn test_relative_correction_to_source() {
        eprintln!("\n  === Relative correction: |Σ_L × I_L| / |streaming term| ===");
        eprintln!("  At recombination (z≈1090): ω=k, κ'≈0 (post-decoupling)");
        
        for &(k, lmax) in &[(0.05_f64, 42_usize), (0.10, 80), (0.15, 80), (0.20, 100)] {
            let omega = k;
            let tail_max = 3000;
            let sigma = self_energy(omega, omega, lmax, tail_max);
            // Streaming term for top shell: ω × L/(2L+1) × I_{L-1}
            // Ratio: |Σ × I_L| / |ω × L/(2L+1) × I_{L-1}|
            // For well-behaved hierarchy, I_L ~ I_{L-1} × (ωτ/(2L+1))
            // So ratio ≈ |Σ| / (ω × L/(2L+1)) = |Σ|×(2L+1) / (ω×L)
            let streaming_rate = omega * lmax as f64 / (2 * lmax + 1) as f64;
            let ratio = sigma.abs() / streaming_rate;
            eprintln!("  k={:.2} ℓ={:>3}: |Σ|/ω={:.4e}, |Σ|/stream={:.4e} ({})",
                k, lmax, sigma.abs()/omega, ratio,
                if ratio > 0.01 { "SIGNIFICANT" } else { "negligible" });
        }
    }
}

/// Few-pole rational approximation to Σ_L(s):
///   Σ_L(s) ≈ Σ_∞ + Σ_n R_n / (s + λ_n)
///
/// Fit by sampling Σ_L(s) on a grid and matching poles.
/// Returns (sigma_inf, poles: Vec<(lambda_n, R_n)>)
pub fn fit_few_pole(
    omega: f64,
    ell_max: usize,
    n_poles: usize,
) -> (f64, Vec<(f64, f64)>) {
    let tail_max = 3000_usize;
    
    // Σ_∞ = lim_{s→∞} Σ_L(s) = 0 (self-energy vanishes at high frequency)
    let sigma_inf = self_energy(100.0 * omega, omega, ell_max, tail_max);
    
    // For n_poles=1: single-pole fit matching at s=ω
    // Σ(s) ≈ Σ_∞ + R₁/(s + λ₁)
    // Two constraints: Σ(ω) and Σ'(ω) 
    // Or: match Σ at two frequencies
    if n_poles == 1 {
        let s1 = 0.5 * omega;
        let s2 = 2.0 * omega;
        let sig1 = self_energy(s1, omega, ell_max, tail_max) - sigma_inf;
        let sig2 = self_energy(s2, omega, ell_max, tail_max) - sigma_inf;
        
        // Σ(s) - Σ_∞ = R/(s+λ)
        // sig1 = R/(s1+λ), sig2 = R/(s2+λ)
        // sig1/sig2 = (s2+λ)/(s1+λ)
        // sig1*(s1+λ) = sig2*(s2+λ)
        // λ(sig1-sig2) = sig2*s2 - sig1*s1
        let lambda = (sig2 * s2 - sig1 * s1) / (sig1 - sig2).max(1e-30);
        let r = sig1 * (s1 + lambda);
        
        if lambda > 0.0 {
            return (sigma_inf, vec![(lambda, r)]);
        }
        // Fallback: simple Markovian
        let gamma = -self_energy(omega, omega, ell_max, tail_max);
        return (sigma_inf, vec![(omega, -gamma * omega)]);
    }
    
    // For n_poles=2: sample at 3 frequencies, fit iteratively
    if n_poles >= 2 {
        let freqs = [0.3 * omega, omega, 3.0 * omega];
        let vals: Vec<f64> = freqs.iter()
            .map(|&s| self_energy(s, omega, ell_max, tail_max) - sigma_inf)
            .collect();
        
        // Two-pole fit: Σ(s) = R1/(s+λ1) + R2/(s+λ2)
        // Use initial guess from single-pole, then split
        let (_, p1) = fit_few_pole(omega, ell_max, 1);
        let lam0 = p1[0].0;
        let r0 = p1[0].1;
        
        // Split into fast and slow poles
        let lambda1 = lam0 * 0.3;  // slow memory
        let lambda2 = lam0 * 3.0;  // fast memory
        
        // Solve for R1, R2 from two frequency samples
        let a11 = 1.0 / (freqs[0] + lambda1);
        let a12 = 1.0 / (freqs[0] + lambda2);
        let a21 = 1.0 / (freqs[1] + lambda1);
        let a22 = 1.0 / (freqs[1] + lambda2);
        
        let det = a11 * a22 - a12 * a21;
        if det.abs() > 1e-30 {
            let r1 = (vals[0] * a22 - vals[1] * a12) / det;
            let r2 = (vals[1] * a11 - vals[0] * a21) / det;
            return (sigma_inf, vec![(lambda1, r1), (lambda2, r2)]);
        }
        
        // Fallback
        return (sigma_inf, vec![(lambda1, r0 * 0.5), (lambda2, r0 * 0.5)]);
    }
    
    (sigma_inf, vec![])
}

/// Evaluate the few-pole approximation at frequency s.
pub fn eval_few_pole(s: f64, sigma_inf: f64, poles: &[(f64, f64)]) -> f64 {
    let mut result = sigma_inf;
    for &(lambda, r) in poles {
        result += r / (s + lambda);
    }
    result
}

/// Measure fit quality: max relative error over a frequency range.
pub fn fit_quality(
    omega: f64,
    ell_max: usize,
    sigma_inf: f64,
    poles: &[(f64, f64)],
) -> f64 {
    let tail_max = 3000;
    let mut max_err = 0.0_f64;
    for i in 0..50 {
        let s = omega * 10.0_f64.powf(-2.0 + 4.0 * i as f64 / 49.0);
        let exact = self_energy(s, omega, ell_max, tail_max);
        let approx = eval_few_pole(s, sigma_inf, poles);
        let err = (exact - approx).abs() / exact.abs().max(1e-30);
        max_err = max_err.max(err);
    }
    max_err
}

/// Compute the ℓ_max-convergence of the integrated source ∫ g×Θ₀×j₂ dη.
/// This measures the ACTUAL hidden physics: does increasing ℓ_max change D₂?
///
/// Returns Vec<(ℓ_max, |Δ₂|, wall_ms)>
pub fn lmax_convergence_source(
    k: f64,
    params: &crate::recombination::visibility_hyrec::VisibilityParams,
    vis: &crate::recombination::visibility_hyrec::VisibilityResult,
    lmax_grid: &[usize],
) -> Vec<(usize, f64, u128)> {
    use crate::solver::sync_kmode::solve_sync_kmode;
    
    let eta_0 = vis.eta_grid[vis.eta_grid.len() - 1];
    let mut results = Vec::new();
    
    for &lg in lmax_grid {
        let ln = (lg / 2).max(6);
        let t0 = std::time::Instant::now();
        match solve_sync_kmode(k, params, vis, lg, ln) {
            Ok(r) => {
                let ms = t0.elapsed().as_millis();
                // Compute Δ₂(k) = ∫ source × j₂(kη) dη
                let mut delta2 = 0.0_f64;
                for i in 1..r.eta_grid.len() {
                    let x = k * r.eta_grid[i];
                    let j2 = if x.abs() < 1e-10 { 0.0 }
                        else { (3.0/(x*x) - 1.0) * x.sin()/x - 3.0 * x.cos()/(x*x) };
                    let deta = r.eta_grid[i] - r.eta_grid[i-1];
                    delta2 += r.raw_theta0_source[i] * j2 * deta;
                }
                results.push((lg, delta2, ms));
            }
            Err(_) => results.push((lg, f64::NAN, 0)),
        }
    }
    results
}

#[cfg(test)]
mod advanced_tests {
    use super::*;

    /// Test the few-pole rational fit quality.
    #[test]
    fn test_few_pole_fit() {
        eprintln!("\n  === Few-pole rational approximation to Σ_L(s) ===");
        
        for &(k, lmax) in &[(0.05_f64, 40_usize), (0.10, 80), (0.15, 80)] {
            let omega = k;
            let tail_max = 3000;
            
            for n_poles in 1..=2 {
                let (sig_inf, poles) = fit_few_pole(omega, lmax, n_poles);
                let quality = fit_quality(omega, lmax, sig_inf, &poles);
                
                eprintln!("  k={:.2} ℓ={:>3} N_pole={}: Σ_∞={:.3e}, max_err={:.1}%",
                    k, lmax, n_poles, sig_inf, quality * 100.0);
                for (i, &(lam, r)) in poles.iter().enumerate() {
                    eprintln!("    pole {}: λ/ω={:.3}, R/ω²={:.4e}", 
                        i, lam/omega, r/(omega*omega));
                }
            }
        }
    }
    
    /// The critical test: ℓ_max convergence of the transfer function Δ₂(k).
    /// This reveals whether hidden physics exists above ℓ_max.
    #[test]
    fn test_lmax_convergence_delta2() {
        use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);
        
        let lmax_grid = vec![15_usize, 20, 30, 40, 60, 80, 100, 120, 150];
        
        eprintln!("\n  === ℓ_max convergence of Δ₂(k) — hidden physics diagnostic ===");
        
        for &k in &[0.01_f64, 0.05, 0.10, 0.15] {
            let results = lmax_convergence_source(k, &p, &vis, &lmax_grid);
            let ref_val = results.last().unwrap().1;
            
            eprintln!("  k={:.3}  (ref ℓ_max={}, Δ₂_ref={:.6e}):", k, lmax_grid.last().unwrap(), ref_val);
            for &(lg, d2, ms) in &results {
                let rel_err = if ref_val.abs() > 1e-30 { 
                    (d2 - ref_val) / ref_val * 100.0 
                } else { 0.0 };
                let converged = rel_err.abs() < 1.0;
                eprintln!("    ℓ={:>4}: Δ₂={:>11.6e}  err={:>7.2}%  {}ms  {}",
                    lg, d2, rel_err, ms,
                    if converged { "✓" } else { "←NOT CONVERGED" });
            }
        }
    }

    /// Measure the STREAMING correction: what changes when we add
    /// the Markovian Σ_L damping to the top shell vs no correction.
    #[test]
    fn test_eft_vs_baseline_detailed() {
        use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
        use crate::recombination::hyrec_tables::HyRecTables;
        use crate::solver::sync_kmode::{solve_sync_kmode, solve_sync_kmode_eft};

        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);

        eprintln!("\n  === EFT vs Baseline: per-multipole comparison ===");
        
        for &k in &[0.05_f64, 0.10] {
            let lg = ((k * 280.0 * 3.0).ceil() as usize).max(15).min(80);
            let ln = (lg / 2).max(6);
            
            let r_base = solve_sync_kmode(k, &p, &vis, lg, ln).unwrap();
            let r_eft = solve_sync_kmode_eft(k, &p, &vis, lg, ln, true).unwrap();
            
            // Compare source at visibility peak region
            let n = r_base.raw_theta0_source.len();
            let mut max_diff = 0.0_f64;
            let mut rms_diff = 0.0_f64;
            let mut n_pts = 0;
            let peak_region_start = n / 3;
            let peak_region_end = 2 * n / 3;
            
            for i in peak_region_start..peak_region_end {
                let diff = (r_eft.raw_theta0_source[i] - r_base.raw_theta0_source[i]).abs();
                let scale = r_base.raw_theta0_source[i].abs().max(1e-30);
                max_diff = max_diff.max(diff / scale);
                rms_diff += (diff / scale).powi(2);
                n_pts += 1;
            }
            rms_diff = (rms_diff / n_pts as f64).sqrt();
            
            eprintln!("  k={:.2} ℓ={}: peak-region max_Δ={:.2}%, rms_Δ={:.2}%",
                k, lg, max_diff * 100.0, rms_diff * 100.0);
        }
    }
}

#[cfg(test)]
mod epoch_split {
    use super::*;
    use crate::recombination::visibility_hyrec::{compute_visibility_ext, VisibilityParams};
    use crate::recombination::hyrec_tables::HyRecTables;
    use crate::solver::sync_kmode::solve_sync_kmode;

    /// Split Δ₂ integral into recombination vs late-time contributions.
    /// This tests whether the ℓ_max non-convergence comes from 
    /// late-time gauge artifacts or real physics at recombination.
    #[test]
    fn test_epoch_split_convergence() {
        let p = VisibilityParams::planck2018();
        let t = HyRecTables::generate(300);
        let vis = compute_visibility_ext(&p, &t, 2000, 1e5);

        eprintln!("\n  === Epoch split: recombination vs late-time contribution ===");
        eprintln!("  Recomb = η where g(η) > 0.001 × g_max; Late = rest");
        
        // Find visibility peak and define recombination window
        let g_max = vis.g_grid.iter().fold(0.0_f64, |m, &g| m.max(g));
        let g_thresh = 0.001 * g_max;
        
        for &k in &[0.01_f64, 0.05, 0.10] {
            eprintln!("\n  k={:.3}:", k);
            eprintln!("  {:>5} | {:>11} {:>11} {:>11} | {:>7} {:>7}",
                "ℓ_max", "Δ₂_recomb", "Δ₂_late", "Δ₂_total", "Δrec%", "Δlat%");
            eprintln!("  {}", "-".repeat(75));
            
            let mut ref_recomb = 0.0_f64;
            let mut ref_late = 0.0_f64;
            
            for &lg in &[20_usize, 40, 60, 80, 120, 150] {
                let ln = (lg / 2).max(6);
                match solve_sync_kmode(k, &p, &vis, lg, ln) {
                    Ok(r) => {
                        let mut d2_recomb = 0.0_f64;
                        let mut d2_late = 0.0_f64;
                        
                        for i in 1..r.eta_grid.len() {
                            let x = k * r.eta_grid[i];
                            let j2 = if x.abs() < 1e-10 { 0.0 }
                                else { (3.0/(x*x)-1.0)*x.sin()/x - 3.0*x.cos()/(x*x) };
                            let deta = r.eta_grid[i] - r.eta_grid[i-1];
                            let contrib = r.raw_theta0_source[i] * j2 * deta;
                            
                            // Check if this η is in the recombination window
                            // Find corresponding visibility value
                            let eta = r.eta_grid[i];
                            // vis.eta_grid is in same direction as r.eta_grid
                            let g_here = r.raw_theta0_source[i].abs() / 
                                (if r.raw_theta0_source[i].abs() > 1e-30 { 1.0 } else { 1.0 });
                            // Actually, source = g * Θ₀, so |source|/|Θ₀| = g
                            // But we don't know Θ₀ separately. Use vis grid directly.
                            let g_val = {
                                let mut gv = 0.0;
                                for j in 0..vis.eta_grid.len()-1 {
                                    if vis.eta_grid[j] <= eta && eta <= vis.eta_grid[j+1] {
                                        let frac = (eta - vis.eta_grid[j]) / 
                                            (vis.eta_grid[j+1] - vis.eta_grid[j]).max(1e-30);
                                        gv = vis.g_grid[j] * (1.0-frac) + vis.g_grid[j+1] * frac;
                                        break;
                                    }
                                }
                                gv
                            };
                            
                            if g_val > g_thresh {
                                d2_recomb += contrib;
                            } else {
                                d2_late += contrib;
                            }
                        }
                        
                        let d2_total = d2_recomb + d2_late;
                        
                        if lg == 150 {
                            ref_recomb = d2_recomb;
                            ref_late = d2_late;
                        }
                        
                        let err_rec = if ref_recomb.abs() > 1e-30 {
                            (d2_recomb - ref_recomb) / ref_recomb * 100.0
                        } else { 0.0 };
                        let err_lat = if ref_late.abs() > 1e-30 {
                            (d2_late - ref_late) / ref_late * 100.0
                        } else { 0.0 };
                        
                        eprintln!("  {:>5} | {:>11.4e} {:>11.4e} {:>11.4e} | {:>7.1} {:>7.1}",
                            lg, d2_recomb, d2_late, d2_total, err_rec, err_lat);
                    }
                    Err(e) => eprintln!("  {:>5} | FAIL: {}", lg, &e[..40.min(e.len())]),
                }
            }
        }
    }
}
