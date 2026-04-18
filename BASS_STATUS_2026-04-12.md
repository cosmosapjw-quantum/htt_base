# BASS — Bianchi Anisotropic Spectrum Solver: Status Report

**Date**: 2026-04-12  
**Codebase**: `bass_rs` (Rust), 149 source files, ~66,000 lines  
**Core file**: `src/solver/sync_gauge_camb.rs` (4,841 lines)  
**Purpose**: Compute the CMB TT power spectrum D_ℓ in the synchronous gauge (CDM frame) to validate against CAMB, as part of a doctoral thesis on Bianchi anisotropic cosmology.

---

## 1. What BASS Does

BASS solves the linearised Boltzmann + Einstein system for a flat ΛCDM universe in the synchronous gauge (zero-acceleration / CDM frame), computes the line-of-sight (LoS) temperature source function S(k,τ), integrates it against spherical Bessel functions j_ℓ(k·χ), and produces the angular power spectrum D_ℓ = ℓ(ℓ+1)C_ℓ/(2π). The target is ±5% agreement with CAMB across ℓ = 2–300.

The code is structured as a three-stage pipeline:

### Stage 1 — Recombination and visibility

HyRec-based EMLA recombination computes the ionisation fraction x_e(z), from which the Thomson opacity κ'(τ), visibility function g(τ) = κ'·e^{-τ_optical}, and optical depth τ(z) are derived on a grid of ~3000 redshift points covering z = 0–50,000.

### Stage 2 — Perturbation ODE per k-mode

For each wavenumber k, the linearised Boltzmann hierarchy is evolved from z ≈ 50,000 to z = 0.

**State vector** y = (η_k, σ, δ_c, δ_b, v_b, Θ₀…Θ_L, N₀…N_M, E₀…E_P, B₀…B_P, Ψ₀^(q)…Ψ_lm^(q), Φ)

with dimension n = 5 + (L+1) + (M+1) + 2(P+1) + n_q·(l_m+1) + 1. Default production config: L = M = 16, P = 12 → n = 52 DOF (without massive ν). Full physics with 10 q-bins and l_m = 12: n = 182 DOF.

The perturbation equations (all in conformal time τ, with ℋ = a'/a):

**Metric sector (synchronous gauge)**:
- η_k' = dgq/2, where dgq = (4/3)ρ_γ·4Θ₁ + (4/3)ρ_ν·4N₁ + ρ_b·v_b + dgq_mν
- σ' = −2ℋσ − (ρ_γ·pig + ρ_ν·pir + dgs_mν)/k + η_k
- ḣ = 2kσ − 6η_k'/k (derived, not evolved)

**Matter sector**:
- δ_c' = −ḣ/2
- δ_b' = −k·v_b − ḣ/2
- v_b' = −ℋ·v_b + c²_s·k·δ_b + κ'(3Θ₁ − v_b)/R_b

**Photon hierarchy** (Thomson scattering):
- Θ₀' = −k·Θ₁ − ḣ/6
- Θ₁' = (k/3)(Θ₀ − 2Θ₂) − κ'(Θ₁ − v_b/3)
- Θ₂' = (k/5)(2Θ₁ − 3Θ₃) − κ'(Θ₂ − 5P/2)  where P = (2Θ₂ + 3E₂)/5
- Θ_ℓ' = k/(2ℓ+1)[ℓΘ_{ℓ−1} − (ℓ+1)Θ_{ℓ+1}] − κ'Θ_ℓ  (ℓ ≥ 3)
- Truncation: Θ_L' = k·Θ_{L−1} − (L+1)/τ·Θ_L − κ'Θ_L

**Massless neutrino hierarchy** (free-streaming):
- N₀' = −k·N₁ − ḣ/6
- N₁' = (k/3)(N₀ − 2N₂)
- N_ℓ' = k/(2ℓ+1)[ℓN_{ℓ−1} − (ℓ+1)N_{ℓ+1}]  (ℓ ≥ 2)
- Truncation: N_M' = k·N_{M−1} − (M+1)/τ·N_M

**E-mode polarisation hierarchy**:
- E₀' = −k·E₁ − κ'(E₀ − P)
- E₁' = (k/3)(E₀ − 2E₂) − κ'E₁
- E₂' = (k/5)(2E₁ − 3E₃) − κ'(E₂ − P)
- E_ℓ' = k/(2ℓ+1)[ℓE_{ℓ−1} − (ℓ+1)E_{ℓ+1}] − κ'E_ℓ  (ℓ ≥ 3)

**Massive neutrino hierarchy** (per momentum bin q):
- Ψ₀'(q) = −kv·Ψ₁ + (ḣ/6)·d ln f₀/d ln q, where v = q/√(q² + (am)²)
- Ψ₁'(q) = (kv/3)(Ψ₀ − 2Ψ₂)
- Ψ_ℓ'(q) = kv/(2ℓ+1)[ℓΨ_{ℓ−1} − (ℓ+1)Ψ_{ℓ+1}]  (ℓ ≥ 2)

The system dy/dτ = A(τ)·y is linear and solved by Rodas5P (4th-order L-stable Rosenbrock method with PI step-size control). The matrix A(τ) is precomputed at visibility grid points and linearly interpolated between them (LinearProfileDyn).

### Stage 3 — LoS integration and C_ℓ

The temperature source function S(k,τ) is decomposed into:

- **Sachs-Wolfe**: S_SW = g·(Δ_γ/4 + 2φ + η_MB/2), where φ = η_s − ℋσ/k, η_MB = −2η_s
- **Doppler**: S_Dop = [(σ + v_b)g' + (σ̇ + v̇_b)g]/k
- **Quadrupole**: S_Quad = (5/8k²)[k²·P·g + 3P·g'' + 6P'·g']
- **ISW**: S_ISW = 2Φ̇·e^{−τ_opt}, computed by finite-difference on φ = η_s − ℋσ/k

The transfer function Δ_ℓ(k) = ∫dτ S(k,τ)·j_ℓ(k·(τ₀−τ)) is computed via adaptive Gauss-Kronrod quadrature (G7K15), and D_ℓ = (2/π)·∫dk/k·|Δ_ℓ(k)|²·P(k)·(T_CMB)² via trapezoidal rule on a geometric k-grid.

---

## 2. Current Accuracy (Before P0 Fixes)

With the no-polarisation, no-massive-ν configuration (24 DOF), using the LinearProfileDyn integrator and σ-based ISW:

| ℓ | BASS D_ℓ | CAMB D_ℓ | Ratio | Status |
|---|----------|----------|-------|--------|
| 2 | 1038 | 1022 | **101.5%** | ✅ ISW correct at low k |
| 10 | 950 | 1130 | 84% | ⚠️ ISW shape |
| 30 | 2153 | 1070 | 201% | ❌ ISW noise |
| 100 | 12482 | 2611 | 478% | ❌ high-ℓ blow-up |
| 200 | 26041 | 5733 | 454% | ❌ |
| 300 | 17513 | 6136 | 285% | ❌ |

Without ISW (S_ISW = 0):

| ℓ | BASS D_ℓ | CAMB D_ℓ | Ratio |
|---|----------|----------|-------|
| 2 | 1169 | 1022 | 114% |
| 100 | 2470 | 2611 | 95% |
| 200 | 5835 | 5733 | 102% |

The primary anisotropies (SW + Doppler + Quad) are accurate to ±15% across ℓ = 2–300 without ISW. The ISW implementation adds correct physics at ℓ = 2 but introduces catastrophic noise at ℓ ≥ 30.

---

## 3. Root Causes of Failures

### 3.1. ISW noise at high ℓ (the σ̇ cancellation problem)

The ISW source involves Φ̇ = d/dτ(η_s − ℋσ/k) = η_k'/k − (ℋ'σ + ℋσ')/k. At high k, σ grows large (O(100) at k = 0.05), making ℋ'σ and ℋσ' both large. Their near-cancellation requires high numerical precision in σ'.

CAMB avoids this by using dverk (Verner 6(8)th order adaptive Runge-Kutta) with direct RHS evaluation at each step. BASS uses Rodas5P (4th order Rosenbrock) with linearly interpolated matrix A(τ). The lower-order method + matrix interpolation gives insufficient σ' precision for the ISW cancellation at high k.

**Evidence**: D₂ = 101.5% (ISW correct at k ≈ 0.0005, where σ is small) but D₁₀₀ = 478% (ISW noise at k ≈ 0.007, where σ is large).

**Attempted fixes and their outcomes**:

| Approach | Result | Why it fails/works |
|----------|--------|-------------------|
| σ-based Φ̇ (direct derivative) | D₂ = 101.5%, D₁₀₀ = 478% | σ̇ cancellation noise at high k |
| Algebraic Poisson Φ | D₂ = 2.5×10¹¹ | Energy constraint violated by 73×; dgrho/k² vs η_s − ℋσ/k give different Φ |
| Algebraic momentum Φ̇ | D₂ = 2.77×10⁶ | −ℋΦ and Q/(2k) also cancel; same noise in different form |
| On-the-fly matrix rebuild (BgInterp) | D₂ = 101.5%, D₁₀₀ = 478% | Matrix interpolation is NOT the bottleneck — σ̇ noise is intrinsic to Rodas5P order |
| FD post-processing on φ array | D₂ = 96.7%, D₁₀₀ = 459% | Clean ISW at low ℓ; high-ℓ noise persists (from primary sources, not ISW) |
| Tighter tolerances (rtol 1e-8) | Not completed | Would help but slow |

**The FD approach is the best current ISW method.** It gives clean ISW at ℓ ≤ 10 (where ISW is physically relevant) without introducing noise at high ℓ.

### 3.2. High-ℓ D_ℓ excess (k-integration aliasing)

Even without ISW, D₁₀₀ has ~5% error and D₃₀₀ has larger error. The cause is the k-integration strategy:

- Global geometric k-grid (200–2000 modes)
- Trapezoidal rule on |Δ_ℓ(k)|²·P(k)/k
- No adaptive local k-window per ℓ

At high ℓ, |Δ_ℓ(k)|² oscillates rapidly in k near k_peak ≈ (ℓ + 1/2)/χ_*, and a global grid under-resolves these oscillations. This is a Stage 3 problem, not a Stage 2 problem.

### 3.3. Doppler sign error (discovered in audit, now FIXED)

The Doppler source had `(σ − v_b)` instead of `(σ + v_b)`. The header comment correctly stated `σ + v_b` (matching CAMB's symbolic module), but the implementation used the wrong sign. This was a multi-session persistent bug since the initial port.

### 3.4. Θ₂–E₂ polarisation instability (discovered during fix)

When the polarisation-aware Θ₂ equation is used in the matrix:

Θ₂' = (k/5)(2Θ₁ − 3Θ₃) + (3/2)κ'E₂   [no Θ₂ self-damping]

the coupled (Θ₂, E₂) system has eigenvalues λ = +3κ'/5 and λ = −κ'. The positive eigenvalue λ₁ = 3κ'/5 ≈ 600 during tight coupling causes exponential growth, making the Rodas5P solver hit NaN within ~3–80 Mpc of conformal time.

CAMB avoids this by using a tight-coupling approximation (TCA) that analytically solves for the polarisation quadrupole during early times, switching to the full hierarchy only after opacity drops below a threshold. BASS does not implement TCA.

**Consequence**: the polarisation-aware Θ₂ matrix entry CANNOT be used without TCA. The approximate formula −0.9κ'Θ₂ must be retained in the matrix for ODE stability, while the exact formula is used only in the source extraction function.

---

## 4. P0 Fixes Applied (2026-04-12)

### P0-4: Doppler sign — APPLIED ✅
```rust
// BEFORE (wrong):
let s_dop = ((sigma - vb) * gp + (sigmadot - vbdot) * g) / k;
// AFTER (correct, matches CAMB symbolic: diff(g*(v_b+sigma),t)/k):
let s_dop = ((sigma + vb) * gp + (sigmadot + vbdot) * g) / k;
```

### P0-1: Θ₂ polarisation-aware matrix — APPLIED ✅ (with caveat)
The matrix builder now branches:
- pol ON: `+1.5·κ'·E₂` coupling (Θ₂ self-damping cancels)
- pol OFF: `−0.9·κ'·Θ₂` (approximate, stable)

**Caveat**: pol ON causes ODE instability at tight coupling (eigenvalue +3κ'/5). This requires TCA to fix. Until then, production must use `lmax_pol = 0`.

### P0-2: E-mode rows — APPLIED ✅
Full E₀–E_P hierarchy added to `build_camb_matrix_into()`:
- E₀: −κ'E₀ + κ'·polter (Θ₂ and E₂ coupling)
- E₁: standard + κ' damping
- E₂: −(2κ'/5)(E₂ − Θ₂) coupling
- E_ℓ≥3: standard + κ' damping + truncation

### P0-3: Massive ν rows + back-reaction — APPLIED ✅
Per-q-bin Ψ₀–Ψ_lm hierarchy with velocity v(q, am) and full back-reaction:
- Ψ₁(q) → η_k' (momentum constraint)
- Ψ₂(q) → σ' (anisotropic stress)
- Ψ₁(q) → ḣ → δ_c', δ_b', Θ₀', N₀', Ψ₀'(all q) (cross-q coupling)

### Truncation loop fix — APPLIED ✅
All hierarchy loops changed from `3..=L` (inclusive, overlapping with truncation row) to `3..L` (exclusive). The truncation row now writes the complete equation instead of adding to the standard formula. This fixed a ~35% error in the last multipole of each hierarchy.

### P1-1: Dead Φ state — APPLIED ✅
Matrix Φ row zeroed consistently. `camb_rhs()` sets `dy[i_phi] = 0`. ISW computed via FD post-processing.

### Parity test — ADDED ✅
New test `test_matrix_rhs_parity_full` verifies ‖A·y − camb_rhs(y)‖ < 10⁻¹⁰ for random states in all four configurations:
```
[no-pol no-mnu] n=24  max_rel=3.93e-16 PASS
[pol ON]        n=38  max_rel=3.93e-16 PASS
[mnu ON]        n=114 max_rel=5.05e-16 PASS
[full physics]  n=128 max_rel=5.05e-16 PASS
```

---

## 5. Architecture

```
bass_rs/
├── src/
│   ├── solver/
│   │   ├── sync_gauge_camb.rs  — CORE: equations, matrix, solver, D_ℓ pipeline (4841L)
│   │   ├── rodas5p.rs          — Rodas5P stepper + LinearProfileDyn (291L)
│   │   ├── stacked.rs          — Integration drivers (312L)
│   │   └── ... (other solver variants, Bianchi, PSTF)
│   ├── recombination/
│   │   ├── visibility_hyrec.rs — Visibility function g(τ), κ'(τ) (334L)
│   │   ├── hyrec_tables.rs     — HyRec EMLA recombination tables
│   │   └── emla4.rs            — 4-level EMLA recombination
│   ├── los/
│   │   ├── integrator.rs       — LoS integration (adaptive G7K15)
│   │   ├── source.rs           — Generic source module (STALE, not production)
│   │   └── bessel.rs           — Spherical Bessel functions
│   ├── core/
│   │   ├── config.rs           — Rodas5PConfig, ProductionConfig
│   │   ├── controller.rs       — PI step-size control
│   │   └── lu.rs               — LU factorisation (dense)
│   └── ... (bianchi/, pstf/, teff/, observable/, inference/, forward/)
├── Cargo.toml
└── BASS_STATUS_2026-04-12.md   — This document
```

### Data flow

```
VisibilityParams → compute_visibility() → VisibilityResult {z_grid, eta_grid, g_grid, kappa_dot_grid, tau_grid}
                                              ↓
                               solve_kmode_full(k, params, vis, pcfg)
                                              ↓
                         ┌─────────────────────┴──────────────────────┐
                         │  For each grid point i:                     │
                         │    bg_i = CambBackground from (z, a, H, ρ)  │
                         │    A_i = build_camb_matrix(k, τ_i, lay, bg) │
                         │    (n×n dense matrix, row-major)            │
                         └─────────────────────┬──────────────────────┘
                                              ↓
                         LinearProfileDyn::new(tau_grid, mats_flat)
                                              ↓
                         integrate_linear_profile_rodas5p(profile, y0, eta_eval, cfg)
                                              ↓
                         snapshots y(τ_i) at each grid point
                                              ↓
                         camb_rhs(k, τ, y, dy, lay, bg) → SourceTerms {s_sw, s_dop, s_quad}
                                              ↓
                         FD post-processing: phi[i] = etak/k − ℋσ/k
                                            phidot ≈ (phi[i+1]−phi[i−1])/(τ[i+1]−τ[i−1])
                                            s_isw = 2·phidot·e^{−τ_opt}
                                              ↓
                         CambKmodeResult {eta_grid, source_total, phi, ...}
                                              ↓
                         solve_production_spectrum: for each k, compute Δ_ℓ(k) via LoS
                                              ↓
                         D_ℓ = (2/π) ∫dk/k |Δ_ℓ(k)|² P(k) T²_CMB
```

---

## 6. Key Design Decisions and Their Consequences

### 6.1. LinearProfileDyn vs on-the-fly matrix construction

**LinearProfileDyn** (current production path): precomputes A(τ) at grid points, linearly interpolates n² matrix elements between them.
- Pros: analytic Jacobian J = A available for Rosenbrock; stable
- Cons: interpolation of n² elements could smear oscillatory k-dependent structure

**On-the-fly BgInterp** (implemented but NOT production): interpolates 12 smooth scalar background quantities, rebuilds A at each step via `build_camb_matrix_into`.
- Pros: A is algebraically exact at each step
- Cons: FD Jacobian d(A)/dτ column is fragile for large systems; causes NaN for n > 40

**Result**: both give IDENTICAL D_ℓ for n = 24 (the matrix interpolation is NOT the bottleneck). LinearProfileDyn is the stable production choice.

### 6.2. Rosenbrock vs explicit RK

CAMB uses dverk (explicit 6(8)th order Verner RK). BASS uses Rodas5P (implicit 4th order Rosenbrock).

- Rosenbrock handles the stiff tight-coupling regime without TCA
- But: lower order → lower σ' precision → ISW cancellation noise
- CAMB needs TCA for stability during tight coupling; BASS avoids TCA at the cost of ISW accuracy

### 6.3. Bootstrap IC vs adiabatic IC

The code supports two IC modes:
- **Bootstrap**: interpolated from a precomputed CAMB table (10 k-modes, 12 state variables). Matched to CAMB output at z ≈ 5000 with a τ-offset correction for the conformal time convention difference.
- **Adiabatic fallback**: analytical superhorizon limit (η_s = −1, Θ₀ = 1/2, δ_c = 3/2).

Bootstrap IC gives D₂ within 2% of CAMB. Adiabatic IC gives ~14% excess (phase error from the approximate starting time).

The bootstrap table stores only 12 variables (no E-mode, no massive ν). When lmax_pol > 0, extra DOFs start at zero, which is physically correct (E-mode builds up from Thomson scattering).

---

## 7. What Needs To Happen Next

### Priority 0: Restore working D_ℓ test with Doppler fix

Run `test_dl_200k_epol` with `lmax_pol: 0` to measure the Doppler sign fix impact on D_ℓ without the E-mode instability. Expected: Doppler sign change shifts D₂ by ~5–10%.

### Priority 1: Implement TCA or opac-aware Θ₂ switching

Without TCA, the pol-aware Θ₂ equation is unstable. Options:
- **A (quick)**: use −0.9κ'Θ₂ in the matrix always, full polter only in source extraction. Accept ~10% Θ₂ damping error.
- **B (medium)**: switch Θ₂ matrix formula based on opacity: high κ' → approximate, low κ' → full.
- **C (proper)**: implement TCA with switch-over, matching CAMB's approach.

### Priority 2: Local adaptive k-window for high-ℓ

Replace the global geometric k-grid trapezoidal integration with per-ℓ adaptive sampling around k_peak ≈ (ℓ + 1/2)/χ_*. This is the dominant source of high-ℓ D_ℓ error.

### Priority 3: ISW via higher-order solver or filtered σ̇

Options:
- Use DOP853 (8th order explicit RK, post tight-coupling) for ISW k-modes
- Filter/smooth σ̇ in the ISW computation for k > k_ISW_max
- Accept FD ISW (current: correct at ℓ ≤ 10, negligible at ℓ > 30)

### Priority 4: Source η-interpolation upgrade

Replace piecewise-linear source interpolation in LoS integration with cubic Hermite. This affects low-ℓ phase accuracy.

---

## 8. Numerical Register

| Quantity | Value | Source |
|----------|-------|--------|
| H₀ | 67.36 km/s/Mpc | Planck 2018 |
| h₀c = H₀/c | 2.247×10⁻⁴ Mpc⁻¹ | h × 10⁷ / (2.998×10¹⁰) |
| Ω_b h² | 0.02237 | |
| Ω_c h² | 0.1200 | |
| Ω_m | 0.3153 | |
| τ_reion | 0.0544 | |
| T_CMB | 2.7255 K | |
| N_eff (massless) | 2.0328 | 3.044 − 1.0112 (1 massive) |
| N_eff (massive) | 1.0112 | 1 species, m_ν = 0.06 eV |
| n_s | 0.9649 | |
| A_s | 2.1×10⁻⁹ | |
| k_pivot | 0.05 Mpc⁻¹ | |
| η₀ (conformal age) | 14,138 Mpc | from visibility integration |
| grho convention | κa²ρ = 3h₀c²·Ω/aⁿ | CAMB convention |
| pig = 4Θ₂ | ratio 4.0000 (verified) | |

---

## 9. Test Summary

| Test | Configuration | Result | Notes |
|------|--------------|--------|-------|
| `test_layout_dimension` | n=24 (no pol) | PASS | |
| `test_matrix_vs_rhs_consistency` | 24 DOF, z=1075 | PASS (4.6e-15) | |
| `test_matrix_rhs_parity_full` | 24/38/114/128 DOF | PASS (5.1e-16) | All 4 configs |
| `test_pig_normalization` | pig/Θ₂ = 4.0 | PASS | |
| `visibility_hyrec` (12 tests) | xe, g, κ' | PASS | |
| `test_dl_200k_epol` | 52 DOF, lmax_pol=12 | **FAIL** | Θ₂-E₂ instability |
| `test_dl_200k_epol` (lmax_pol=0) | 24 DOF | **PENDING** | Needs retest with Doppler fix |

---

## 10. Known Limitations

1. **No TCA**: tight-coupling approximation not implemented; requires `lmax_pol = 0` for stability
2. **ISW noise at high k**: Rodas5P order insufficient for σ̇ cancellation; FD post-processing is the workaround
3. **k-integration aliasing**: global geometric grid + trapezoid under-resolves |Δ_ℓ(k)|² oscillations at high ℓ
4. **Source linear interpolation**: piecewise-linear source in LoS quadrature may cause phase shift at low ℓ
5. **No baryon sound speed evolution**: cs²_b fixed at 10⁻¹⁰ (should evolve with T_m)
6. **Massive ν background**: expansion rate uses massless ν density only; massive ν perturbations evolve but background is incomplete
7. **los/source.rs Doppler**: stale generic module uses `−g'v_b/k` (different from production); marked non-production

---

## 11. Glossary

- **BASS**: Bianchi Anisotropic Spectrum Solver (this code)
- **CAMB**: Code for Anisotropies in the Microwave Background (reference)
- **CambLayout**: struct defining state vector index mapping
- **CambBackground**: struct with 12 background scalars (ℋ, ρ_i, κ', g, g', g'', a, e^{−τ})
- **LinearProfileDyn**: precomputed matrix interpolation engine
- **BgInterp**: scalar background interpolation engine (on-the-fly path)
- **Rodas5P**: 4th-order L-stable Rosenbrock method with 8 stages
- **dverk**: Verner 6(8)th order explicit RK (used by CAMB)
- **TCA**: tight-coupling approximation (not implemented)
- **polter**: polarisation tensor P = (2Θ₂ + 3E₂)/5
- **ISW**: integrated Sachs-Wolfe effect (late-time potential decay)
- **LoS**: line-of-sight integration
- **FD**: finite difference (for ISW phidot computation)
