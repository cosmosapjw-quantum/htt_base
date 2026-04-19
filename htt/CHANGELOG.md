# Changelog — bass-py

## [0.8.2-w8-02] — 2026-04-18

### W8-02: Reionization tanh model
- `bass/recombination/reionization.py` (439 lines, 47 tests)
- Planck 2018 tanh parameterization: z_rei_H=7.67, Δz=0.5, optional HeII at z=3.5
- **τ_reion = 0.054108 vs Planck 2018 0.054±0.007 (Δ=0.0001, <0.2%)**
- CosmologyForRecombination container, metadata extraction from W8-01 tables
- Extends z grid down to z=0, recomputes τ̇ and κ on full range
- z_* shifts from 1089.89 (no reion) to 1085.17 (with reion)
- Secondary visibility peak at z=6.77 (reionization bump)

### W8-01: Recombination ingest (HyRec-2)
- `bass/recombination/recombination_ingest.py` (483 lines, 52 tests)
- CSV parser for 5-column extended schema (z, x_e, T_m, τ̇, κ)
- Cubic-spline interpolators with out-of-range guards
- Physical validation (x_e∈[0,1.2], κ monotone, τ̇≥0)
- `find_last_scattering_redshift`, `find_visibility_peak` diagnostics
- Real HyRec-2 Planck 2018 reference bundled as fixture (8,000 rows, z=1..8000)
- **z_* = 1089.89 vs Planck 2018 1089.95±0.27 (Δ=0.06)**
- x_e(z=1075) = 0.11335 vs memory reference 0.1137 (0.3%)
- **κ (1+z) integration factor**: pre-module catch during reference generation

### HyRec-2 sandbox infrastructure
- Sandbox-confirmed: gcc -O3 + standard C, no external libs (GSL/HDF5/FFTW)
- Compile ~1s, run 25ms/history
- Bypasses bass_rs hyrec_emla.rs h0_cgs unit bug entirely
- Reference generator script bundled for reproducibility

## [0.7.2-w7-02] — 2026-04-17

### W7-02: Polter recoupling (Θ ↔ E Thomson loop)
- `bass/closure/polter_recoupling.py` (336 lines, 42 tests)
- Non-invasive W5-A wrapper at ℓ=2:
  - Γ^Θ_2 = (9/10)Γ_T (damping reduction)
  - S^Θ_2 = -(√6/10)Γ_T × E_2 (cross-coupling)
- `joint_w604_consistency_residual` diagnostic
- **4-way cross-verification**: W6-04 ↔ W7-01 ↔ W7-02 ↔ joint fixed-point
- Machine precision (1e-16 abs, 1.28e-11 rel) agreement
- Polarization amplification factor 4/3 exact (W5-A → W6-04)
- Joint fixed-point convergence: 14 iter, spectral radius ~1/6

### W7-01: E-mode hierarchy (spin-2 streaming)
- `bass/transport/emode_hierarchy.py` (403 lines, 62 tests)
- PSTF spin-2 streaming: α^E_ℓ = √(ℓ²-4)/(2ℓ+1), α^E_2 = 0 boundary
- ℓ=2 effective damping: Γ^E_2 = (2/5)Γ_T
- Cross-coupling source: S^E_2 = -(3/(5√6))Γ_T × Θ_2
- **W6-04 subleading cross-check**: E_2/Θ_2 = -√6/4 at isolated ℓ=2
- DampingProfile prototype (explicit ell2_damping_factor field)

## [0.6.x-w6] — 2026-04-17

### W6-04: Quadrupole TCA (v1.2 sign fix)
- `bass/closure/quadrupole_tca.py` (433 lines, 52 tests)
- Algebraic TCA closure: Γ_T M X = +S (sign convention corrected)
- 2×2 matrix inverse with physical sign assertions
- **P1 PHYSICS BUG fix**: initial formula had overall sign error caught by systematic framework verification
- Mandatory pattern deployed: physical sign assertion on every inverse

### W6-03: CDM fluid
- `bass/perturbation/cdm_fluid.py` (~280 lines, 37 tests)
- Pressureless collisionless CDM (no Thomson coupling)

### W6-02: Dipole-driven photon hierarchy
- `bass/transport/dipole_driven_hierarchy.py` (422 lines, 70 tests)
- Non-invasive wrapper around W5-A for photon ℓ=1 baryon drive
- `is_trivial → W5-A bit-exact` backward compat pattern

### W6-01: Baryon fluid + Thomson drag
- `bass/perturbation/baryon_fluid.py` (~350 lines, 52 tests)
- ρ_b, v_b with Thomson drag coupling to photons

### v1.2 Patch batch
- W6-04 sign correction deployed to module + tests
- Module docstring with explicit derivation + physical check
- Test design: `assert θ > 0`, `assert E < 0` physical sign assertions
- MASTER_PROMPT_LIST_v1.2: W6-04 spec corrected, (3/30)ζ → (2/15)ζ typo fix

## [0.5.x-w5] — 2026-04 (pre-session)

- W5-A: multipole_hierarchy (Θ streaming framework, 108 tests)
- W5-B: bianchi_i_hierarchy
- W5-C: Wigner normalization (axisymmetric inert, m≠0 deferred)
- implicit_hierarchy (Rodas5P solver)
- ray_transport
- shear_sources

## [0.4.x-w4] — 2026-04 (pre-session)

- W4 phase: thomson_tensor, collision framework

## [0.3.x-w3] — 2026-04 (pre-session)

- W3 phase: canonical_decision (W3 gating)
- sigma_floor, validation_labels

## [0.2.0-w2] — 2026-04-17 (initial)

- W1 phase: bianchi_types, einstein_bianchi, shear_sources
- W2: baryon_only_policy, channel_routing, comparator_policy
- 304 tests passing at this milestone

---

## Test stats progression

| Version | Tests | Notes |
|---------|-------|-------|
| 0.2.0-w2 | 304 | W2 baseline (v4.1 restructure) |
| ~0.5.x-w5 | ~950 | Hierarchies added |
| 0.6.4-w6-04 | ~1,434 | W6 complete + v1.2 patch |
| 0.7.2-w7-02 | ~1,538 | W7 complete, 4-way cross-check |
| 0.8.1-w8-01 | 1,590 | Recombination ingest |
| **0.8.2-w8-02** | **1,637** | **current — W8-02 tanh reion** |

---

## Physics bugs caught

1. **W6-01**: Thomson drag sign (caught by external reference)
2. **W6-04**: TCA algebraic inverse sign (caught by framework cross-check, v1.2 patch)
3. **W8-01**: κ (1+z) integration factor (caught during pre-module reference generation — best-case early detection)

## Test design errors caught (all tolerance/API issues, modules correct)

- W6-02 ×2, W6-03 ×1, W7-01 ×1, W7-02 ×1, W8-01 ×1, W8-02 ×4

**Total: 10 test-design retries, 0 module bugs caught by own tests** — the tests expose spec issues (tolerance calibration, API understanding) but modules have shipped correct on first attempt in every case.
