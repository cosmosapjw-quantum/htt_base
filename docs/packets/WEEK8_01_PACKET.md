# WEEK 8-01 PACKET — Recombination ingest (HyRec-2 reference)
## Date: 2026-04-18
## Scope: MASTER_PROMPT_LIST_bass_py_v1.2 §4 W8-01

---

## §1. Deliverables

| Artefact | Path | Size |
|----------|------|------|
| Module | `bass/recombination/recombination_ingest.py` | 483 lines |
| Tests | `bass/recombination/test_recombination_ingest.py` | 565 lines |
| Fixture CSV | `bass/recombination/fixtures/recombination_ref_planck2018.csv` | 8,000 rows, 520 KB |
| New package init | `bass/recombination/__init__.py` | 1 line |

Plus sandbox-side utilities (in `/mnt/user-data/outputs/`):
- `hyrec2_xe_planck2018_default.dat` — raw HyRec-2 output
- `hyrec2_input_planck2018_default.dat` — input cosmology
- `hyrec2_SESSION_NOTES.md` — reproducibility record
- `recombination_ref_planck2018.csv` — production reference (same as fixture)

New tests: **52** (roadmap target ~50).

---

## §2. Public API surface

```python
# bass/recombination/recombination_ingest.py

# Header parsing
parse_recombination_header(lines) → (metadata_dict, unparsed_list)

# Table container (frozen dataclass)
RecombinationTable                   # (z, x_e, T_m, tau_dot, kappa, metadata, source_path)
    .n_points, .z_min, .z_max

# CSV loader
load_recombination_table(path)       → RecombinationTable

# Physical validation
validate_recombination_table(table)  → List[str] (empty = passes)

# Interpolation (cubic spline)
RecombinationInterp
    .query_x_e(z), query_T_m(z), query_tau_dot(z), query_kappa(z)
    .query_visibility(z)  # g(z) = τ̇ exp(-κ)
build_interpolators(table)           → RecombinationInterp

# Derived diagnostics
find_last_scattering_redshift(interp, target_kappa=1.0) → float
find_visibility_peak(interp)         → (z_peak, g_peak)

# Test fixture generator
make_synthetic_tanh_table(...)       → RecombinationTable
```

**No W3 gating**: pure data ingest + interpolation; no σ² reduction.

---

## §3. Physics core

### 3.1 Schema decision (x_e 포함 확장)

Five-column CSV (z, x_e, T_m, τ̇, κ) with optional `# key = value` header:
- **z**: redshift (strictly ascending after parse)
- **x_e**: free electron fraction (bounded [0, 1.20] to accommodate He over-ionization peak at z ≈ 2500)
- **T_m**: matter temperature in Kelvin
- **τ̇**: conformal Thomson opacity in 1/Mpc, $\dot\tau = a\, n_e\,\sigma_T c$
- **κ**: optical depth $\kappa(z) = \int_0^z \dot\tau/H(z')\, dz'$ (dimensionless)

The $(1+z)$ factor carefully accounted for: physical $\dot\tau = n_e \sigma_T c$ integrates with $(-dt/dz) = 1/((1+z)H)$, giving $\kappa = \int \dot\tau_{\rm phys}/((1+z)H) dz = \int \dot\tau_{\rm conf}/H\, dz$ — conformal convention drops the $(1+z)$.

### 3.2 HyRec-2 sandbox reference generation

Planck 2018 fiducial cosmology (from HyRec default input.dat):
- $h = 0.6735837$, $T_{\rm CMB} = 2.7255$ K
- $\Omega_b = 0.04941$, $\Omega_{\rm cb} = 0.31242$, $Y_{\rm He} = 0.245$
- $N_{\rm eff} = 3.046$, $\sum m_\nu = 0.06$ eV
- Derived: $\Omega_m = 0.31384$ (CB + massive ν), $\Omega_r = 9.22 \times 10^{-5}$, $\Omega_\Lambda = 0.68607$
- $n_H(z=0) = 0.1900$ m⁻³ (from $\rho_b (1-Y_{\rm He})/m_H$)

Sandbox execution: 25 ms per run, 8000 rows (z = 1..8000).

### 3.3 Production-value validation (cross-reference table)

| Quantity | W8-01 sandbox | Literature | Agreement |
|----------|---------------|------------|-----------|
| $x_e(z=1075)$ | 0.11335 | 0.1137 (user memory) | 0.3% |
| $x_e(z=1089.9)$ | 0.13142 | — | — |
| $\tau̇(z=1100)$ | 0.0684 /Mpc | 0.06–0.08 /Mpc (CAMB/CLASS) | within range |
| $z_*$ (last scattering, κ=1) | **1089.89** | 1089.95 ± 0.27 (Planck 2018) | **0.06** |
| Visibility peak $z_g$ | 1088.79 | 1080–1090 (standard) | in range |
| $g_{\rm peak}$ | 2.24×10⁻² | — | — |

The $z_*$ agreement (0.06 off from Planck 2018 reference) **confirms correct (1+z) treatment** throughout the τ̇→κ integration chain.

### 3.4 Validation bounds

Physical reasonableness checks in `validate_recombination_table`:
- $x_e \in [0, 1.20]$ (upper bound for HeII→HeI over-ionization)
- $T_m \in [0, 10^6]$ K (generous)
- $\dot\tau \geq 0$ everywhere
- $\kappa \geq 0$ everywhere
- $\kappa$ monotonically non-decreasing with z

### 3.5 Out of scope (declared deferred)

- **Reionization bump** (W8-02): $x_e^{\rm rei}(z)$ added on top of recombination, typically tanh at $z \sim 7$
- **$\eta(z)$ conversion**: requires cosmology (Ω_m, Ω_r, Ω_Λ), handled at integrator layer rather than ingest
- **Derivative fields** ($d\dot\tau/dz$, $dg/dz$): callers compute as needed from spline objects
- **Multi-cosmology grid**: ingest handles one table at a time; higher-level caller builds grids

---

## §4. Test inventory (52 tests, all PASSING)

| Class | Tests | Focus |
|-------|-------|-------|
| `TestParseRecombinationHeader` | 6 | `# key = value` parsing |
| `TestRecombinationTableContainer` | 5 | Shape, monotonicity, finite |
| `TestLoadRecombinationTable` | 7 | CSV parsing, schema, edge cases |
| `TestValidationChecks` | 5 | Physical bounds |
| `TestBuildInterpolators` | 2 | Spline construction |
| `TestQueryMethods` | 4 | Scalar/array queries, out-of-range |
| `TestVisibilityFunction` | 2 | $g = \dot\tau e^{-\kappa}$ |
| `TestSyntheticTanhFixture` | 4 | Generator |
| `TestFindLastScatteringRedshift` | 2 | Brent's method |
| `TestFindVisibilityPeak` | 2 | Parabolic refinement |
| **`TestRealHyRecReference`** | **6** | **Real HyRec data integration** |
| **`TestPhysicalSignAssertions`** | **4** | **v1.2 pattern (continued)** |
| **`TestCrossReferenceKnownValues`** | **3** | **CAMB/Planck literature values** |

**Runtime**: 2.70 s (including 9 tests against 8,000-row real CSV).

### 4.1 Notable tests

- `test_last_scattering_near_1090`: z_ls must be in [1085, 1095] using real HyRec data
- `test_x_e_at_z_1075_matches_reference`: |x_e(1075) − 0.1137| < 0.01
- `test_tau_dot_at_z_1100`: τ̇ in [0.05, 0.10] /Mpc (CAMB range)
- `test_real_table_metadata`: verifies 11 cosmology parameters parsed from header

---

## §5. Score card

```
PR-W8-01: Recombination ingest (HyRec-2 Planck 2018)
Status:   VALIDATED
Tests:    52 / 52 (1 numpy API patch)
Honest scope declared: YES (§3.5)
V-gate status: N/A
Lines:    1,048 (module 483 + test 565)
Depends complete: YES (none — independent ingest module)
Production ready: YES
External data dependency: NONE (fixture bundled, sandbox-reproducible)
Real-data validation: z_* = 1089.89 vs Planck 2018 1089.95 ± 0.27 (0.06 match)
Physical sign assertions: 4 (v1.2 pattern continued)
Cosmology-agnostic: z-space; η(z) deferred to integrator layer
```

---

## §6. Test design retry (one patch)

`test_visibility_integral_approximates_one` used `np.trapz` which was removed in numpy 2.x (renamed to `np.trapezoid`). One-line fix. No substantive issue; the physics was correct.

Running tally:
- Physics bugs caught by external reference: 2 (W6-01 Thomson sign, W6-04 TCA inverse) + **1 this session** (κ integration (1+z) factor caught during sandbox table generation, **before** the module was written — best-case detection)
- Test design errors caught by test runs: 6 (W6-02 ×2, W6-03 ×1, W7-01 ×1, W7-02 ×1, W8-01 ×1)

**The κ integration error is noteworthy**: it was caught during the pre-module reference-table generation, not during module development. This validates the workflow of "generate reference data BEFORE writing the consuming module", since it exposes physics errors at the earliest possible stage.

---

## §7. Sandbox HyRec-2 infrastructure (reusable)

The full HyRec-2 execution chain is now confirmed in the sandbox:

```
Clone:   git clone https://github.com/nanoomlee/HYREC-2.git
Compile: gcc -O3 hyrectools.c helium.c hydrogen.c history.c \
         energy_injection.c hyrec.c -o hyrec -lm
Run:     ./hyrec < input.dat    (25 ms)
```

No external library dependencies (no GSL, HDF5, FFTW). This means:
1. **W10-02 CAMB validation** can use this as a reference table without
   the user having to set up HyRec-2 locally
2. **Cosmology sensitivity studies** possible by varying input.dat in
   the sandbox (each run 25 ms)
3. **bass_rs `hyrec_emla.rs` unit bug** can be fixed at leisure — sandbox
   path is now the canonical reference

---

## §8. Next actions

1. **W8-02 (reionization tanh model)**: next prompt. Adds
   $x_e^{\rm rei}(z) = 0.5 \times [1 + \tanh((z-z_{\rm rei})/\Delta z)]$
   on top of the W8-01 recombination table. Target ~200 lines, ~25 tests.

2. **W8-03 (visibility source $g\cdot\Pi$)**: **Document 12 ceiling item 2/3**.
   Uses W8-01 (visibility) + W7-02 (polter) to build line-of-sight
   source at recombination. Target ~350 lines, ~40 tests.

3. **Deferred** (unchanged):
   - `DampingProfile` full retrofit (end of W7-phase)
   - Full joint (Θ, E) ODE solver → W9

4. **Cumulative state**:
   - Total tests: **1,590** (+52)
   - bass/ modules: **21** (+ `recombination/recombination_ingest`)
   - W6 phase: COMPLETE
   - W7 phase: COMPLETE
   - W8 phase: 1/3 prompts COMPLETE
   - Document 12 ceiling: 1/3 delivered (W6-04)
   - Physics bugs caught: 3 (now with (1+z) κ factor)
   - Test design bugs caught: 6
   - No P0/P1 findings outstanding
   - Full regression runtime: ~60s

---

**End of WEEK8_01 packet.**
