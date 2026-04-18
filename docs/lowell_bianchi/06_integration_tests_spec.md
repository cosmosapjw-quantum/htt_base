# LB-6 — Integration Test Suite and Validation Specification

**Session LB-6**. Produces `bass/integration/test_lowell_bianchi.py` — the end-to-end regression suite pinning the Kolb-Turner thermal history, HyRec recombination, Planck 2018 τ_reion, and the Bianchi I shear-decay invariants.

**Prerequisites**: LB-1 through LB-5 all green.

**Size estimate**: ~400 LoC test suite. No new physics code.

**Reference material**:

- **Kolb §3.5** — thermal history table (z, T, t, key events)
- **Kolb §5.4 / Table 5.3** — recombination history
- **Kolb §5.5** — neutrino temperature ratio
- **Planck 2018 results I** (Aghanim+ 2018) — τ_reion = 0.0544 ± 0.0073
- **HyRec-2 output** (bass_py fixture) — x_e(z), T_m(z), τ̇(z)
- **Ellis §18.3** — Bianchi I shear-decay invariant
- **CAMB Planck 2018 reference** (`data/camb_ref_planck2018.npz`) — η_*, η_0

---

## Table of contents

1. Philosophy — what we test and why
2. The Kolb-Turner thermal history table
3. HyRec recombination reference
4. Planck 2018 τ_reion
5. Bianchi I shear-decay invariant
6. CAMB geometry reference match
7. Neutrino temperature ratio
8. Friedmann invariant at all outputs
9. Test suite file structure
10. Test listing with exact numerical targets
11. Implementation checklist
12. What failure means — diagnostic playbook

---

## 1. Philosophy

LB-6 is the **gate**: no LB-5 integration result reaches downstream consumers unless it passes LB-6. The tests here are:

1. **Not unit tests** — they are full end-to-end integrations taking seconds each
2. **Pinned to textbook or observational values** — every target has a citation
3. **Tolerances are generous at LB-6** (1-5%) because LB-5 is not a CAMB-equivalent integrator; tight-coupling and full neutrino hierarchy are limited in scope
4. **Invariants are enforced to machine precision** — Friedmann, continuity, PSTF invariants

**If any LB-6 test fails**, the physics output is considered *untrustworthy*, even if individual LB-1..LB-5 unit tests pass.

---

## 2. The Kolb-Turner thermal history table

From Kolb-Turner *Early Universe* (1990), reproduced here with the exact values we pin against:

| Event | z | T_γ [K] | t [years] | Conformal time η [Mpc] |
|---|---|---|---|---|
| Matter-radiation equality | **3400** | 9274 | 5.1 × 10⁴ | ~100 |
| Recombination (peak x_e drop) | **1089** | 2970 | 3.8 × 10⁵ | ~280 |
| Drag epoch (baryons decouple) | ~1060 | 2890 | 4.0 × 10⁵ | ~290 |
| Compton decoupling | ~150 | 410 | 1.4 × 10⁷ | ~1500 |
| Reionization onset | ~8 | ~25 | 5.2 × 10⁸ | ~13700 |
| Today | 0 | **2.7255** | 1.38 × 10¹⁰ | **~14153** |

**Pinned values** (must match these with stated tolerance):

| Quantity | Target | Tolerance | Citation |
|---|---|---|---|
| z_eq | 3400 | ±50 | Kolb §3.5; derived from Ω_m / Ω_r |
| z_* | 1089.94 | ±0.30 | HyRec fixture / Planck 2018 |
| T_γ(z=0) | 2.7255 K | ±1e-4 | Fixsen 2009 / SSOT |
| T_γ × a = const | T_γ,0 × a(η) at all η | 1e-12 rel | Kolb eq (3.78) |
| T_ν / T_γ | (4/11)^{1/3} = 0.71377 | 1e-12 | Kolb eq (5.14) |
| η(z_eq) | ~100 Mpc | ±10 | derived from Friedmann |
| η(z_*) | ~280 Mpc | ±5 | HyRec + Friedmann integration |
| η_today | 14153 Mpc | ±10 | CAMB reference (`data/camb_ref_planck2018.npz`) |

---

## 3. HyRec recombination reference

The fixture `bass_py/bass/recombination/fixtures/recombination_ref_planck2018.csv` is the oracle. LB-6 tests that `LowellBianchiIntegrator` at Planck 2018 cosmology reproduces the key moments from this fixture when the temperature history is derived from the integrator (not read from the fixture).

### 3.1 Recombination timing

| Quantity | Target | Tolerance |
|---|---|---|
| z_* ≡ peak of g(z) | 1089.94 | ±0.30 |
| z_drag ≡ peak of baryon visibility | 1059.9 | ±1.0 |
| g(z_*) peak width (FWHM in z) | ~80 | ±10 |

### 3.2 x_e(z) critical points

| z | x_e (HyRec) | Tolerance |
|---|---|---|
| 2000 | ~0.999 | 1e-3 |
| 1200 | ~0.15 | 1e-3 |
| 1089 | 0.50 (halfway during the drop) | 0.05 |
| 1000 | 0.02 | 0.01 |
| 500 | 2e-4 | 1e-5 |
| 100 | 1.5e-4 | 1e-5 |

---

## 4. Planck 2018 τ_reion

| Quantity | Planck 2018 central | 1σ | Tolerance at LB-6 |
|---|---|---|---|
| τ_reion | 0.0544 | 0.0073 | ±0.003 (within 1σ) |

bass_py's `reionization.py` uses `z_reion = 7.68` with `Δz = 0.5` (tanh profile) to produce τ_reion = 0.054108. LB-6 integrates this forward and confirms the integrated optical depth matches.

---

## 5. Bianchi I shear-decay invariant

For orthogonal Bianchi I in the flat limit (k_spatial = 0), the shear amplitude evolves as σ² ∝ a⁻⁶ (Ellis §18.3). In our **Σ² = σ²/(6H²)** normalisation:

```
Σ²(a) × a⁴ = constant      (Bianchi I flat, Planck cosmology)
```

because Σ² ~ σ²/H² ~ a⁻⁶ / a⁻⁴ = a⁻² when radiation-dominated, more complex at later times.

Actually more precisely, the conformal shear Σ = a σ evolves in LCDM as a decaying mode with Σ × a = const. So:

```
Σ²(a) × a² = constant      (Bianchi I flat, conformal shear)
σ²(a) × a⁶ = constant      (physical shear, a⁻⁶ decay)
```

The test pins: at two well-separated η values (η = 50 Mpc and η = 5000 Mpc), the dimensionless shear invariant σ² × a⁶ agrees within 1%.

---

## 6. CAMB geometry reference match

The oracle file `data/camb_ref_planck2018.npz` (from LB-0 session's `scripts/generate_camb_reference.py`) stores `z_star`, `eta_star`, `eta_0` from CAMB. LB-6 asserts:

| Quantity | Our value | CAMB value | Tolerance |
|---|---|---|---|
| z_* | from LB-5 integration | 1089.94 | 0.5 |
| η_* | η at z = z_* | 13872.79 | 20 Mpc |
| η_0 | η at a = 1 | 14153.26 | 10 Mpc |

---

## 7. Neutrino temperature ratio

```
T_ν / T_γ = (4/11)^{1/3} ≈ 0.71377
```

Pinned in `bass.species.neutrino.NeutrinoBackground` at construction; LB-6 verifies the integrator's **output** satisfies this at all η (not just at construction).

---

## 8. Friedmann invariant at all outputs

For flat LCDM (our baseline):

```
𝓗² = (8πG a² / 3) × ρ_total × c⁻²     (geometric units)
```

or equivalently

```
𝓗² × c² / a² = (8πG / 3) × ρ_total
```

LB-6 verifies the residual `|LHS - RHS| / LHS < 1e-6` at every output η.

For Bianchi I, the Friedmann equation gets modified:

```
𝓗² = (8πG a² / 3)(ρ_total + σ²/(2 a²))
```

where the σ² term is the shear energy contribution. LB-6 uses the version appropriate to the test's Bianchi type.

---

## 9. Test suite file structure

```
bass_py/bass/integration/
└── test_lowell_bianchi.py        — all LB-6 tests (one file for integration clarity)
```

Some tests will be **slow** (full integration runs). Mark them with `@pytest.mark.slow` and add to the standard regression run via a config update.

```python
import pytest

class TestLBSmokeFLRW:
    """Fast: FLRW baseline integration succeeds."""
    ...

class TestLBThermalHistory:
    """Medium: z_eq, z_*, τ_reion verification."""
    ...

class TestLBBianchiI:
    """Medium: Bianchi I shear-decay test."""
    ...

@pytest.mark.slow
class TestLBCAMBMatch:
    """Slow: geometry values match CAMB reference."""
    ...

@pytest.mark.slow
class TestLBConvergence:
    """Slow: L=6 vs L=8 convergence."""
    ...
```

---

## 10. Test listing with exact numerical targets

### 10.1 FLRW smoke (class `TestLBSmokeFLRW`)

| # | Test | Target | Tolerance |
|---|---|---|---|
| LB-6-01 | `integrator.run()` completes successfully in FLRW | no exception | — |
| LB-6-02 | `result.a[-1]` == 1.0 (today) | 1.0 | 1e-6 |
| LB-6-03 | `result.Sigma_plus[-1]` == 0 | 0 | 1e-12 |
| LB-6-04 | `result.photon_T_tower[-1]` all finite | finite | exact |
| LB-6-05 | `result.invariant_residuals['friedmann']` max < 1e-6 | < 1e-6 | — |
| LB-6-06 | `result.invariant_residuals['species_sum']` max < 1e-5 | < 1e-5 | — |

### 10.2 Thermal history (class `TestLBThermalHistory`)

| # | Test | Target | Tolerance |
|---|---|---|---|
| LB-6-07 | `result.critical_events['z_eq']` | 3400 | ±50 |
| LB-6-08 | `result.critical_events['z_star']` | 1089.94 | ±0.30 |
| LB-6-09 | `result.critical_events['eta_star']` | 13873 Mpc | ±20 |
| LB-6-10 | `result.critical_events['eta_today']` | 14153 Mpc | ±10 |
| LB-6-11 | `result.critical_events['z_drag']` | 1059.9 | ±1.0 |
| LB-6-12 | `T_nu[-1] / T_gamma[-1]` | 0.71377 | 1e-6 |
| LB-6-13 | `T_gamma[-1]` | 2.7255 K | 1e-4 |
| LB-6-14 | Integrated τ_reion from HyRec + integrator | 0.0544 | ±0.003 |

### 10.3 Bianchi I shear decay (class `TestLBBianchiI`)

| # | Test | Target | Tolerance |
|---|---|---|---|
| LB-6-15 | Bianchi I, Σ_+(η_init) = 1e-4: `Σ_+(η_today) * a_today² / (Σ_+(η_init) * a_init²)` | 1.0 (conformal shear conserves) | 1% |
| LB-6-16 | σ²(η_init) × a_init⁶ == σ²(η_today) × a_today⁶ | constant | 1% |
| LB-6-17 | Bianchi I: Friedmann invariant including Σ² term < 1e-6 rel | < 1e-6 | — |
| LB-6-18 | Bianchi I, Σ_+(0) = 1e-4: `Π_2(η ~ 280)` order of magnitude matches `route_b_d2_lookup(Σ²(280))` | match to 1 sig fig | — |

### 10.4 CAMB geometry match (class `TestLBCAMBMatch`, @slow)

| # | Test | Target | Tolerance |
|---|---|---|---|
| LB-6-19 | `result.critical_events['eta_today']` vs CAMB `eta_0` | equal | ±10 Mpc |
| LB-6-20 | `result.critical_events['eta_star']` vs CAMB `eta_star` | equal | ±20 Mpc |
| LB-6-21 | `result.critical_events['z_star']` vs CAMB `z_star` | equal | ±0.5 |

### 10.5 Convergence (class `TestLBConvergence`, @slow)

| # | Test | Target | Tolerance |
|---|---|---|---|
| LB-6-22 | Run at L=6 and L=8; max relative difference in Π_2 at recombination | < 1% | — |
| LB-6-23 | Run at L=6 and L=4; max relative difference in Π_2 at recombination | < 20% | — |

### 10.6 Closure strategy robustness

| # | Test | Target | Tolerance |
|---|---|---|---|
| LB-6-24 | Run with `HardCutClosure` vs `TCAClosure` composite: Π_2 in Γ_T/H > 100 regime agrees | bit-identical in algebraic-mode regime | 1e-4 |

---

## 11. Implementation checklist

- [ ] Verify LB-1 through LB-5 all green (prerequisite)
- [ ] Create `bass/integration/test_lowell_bianchi.py`
- [ ] Import `LowellBianchiIntegrator`, `IntegratorConfig`, LB-1 species, Y-Block tetrad_state
- [ ] Build helper fixture: `default_config_flrw()`, `default_config_bianchi_i(Sigma_plus_init)`
- [ ] Build helper fixture: load `data/camb_ref_planck2018.npz`
- [ ] Write LB-6-01 through LB-6-24 tests
- [ ] Run in isolation with `pytest bass/integration/test_lowell_bianchi.py -v`
- [ ] Tag slow tests with `@pytest.mark.slow`
- [ ] Verify full bass_py regression including LB-6 passes
- [ ] Commit as `LB-6: end-to-end integration tests (Kolb thermal history + CAMB geometry)`

---

## 12. What failure means — diagnostic playbook

When an LB-6 test fails, the playbook is:

| Failure | First diagnostic | Likely root cause |
|---|---|---|
| LB-6-05 (Friedmann residual) | inspect `result.invariant_residuals['friedmann']` vs η | missing energy source or wrong Ω_X,0 values |
| LB-6-07 (z_eq off) | check Ω_r,0 and Ω_m,0 at t=0 in `species.registry` | bug in LB-1 species density scaling |
| LB-6-08 (z_* off) | check `recombination_ingest` table range and spline at recombination | HyRec table corruption or integrator rtol too loose |
| LB-6-14 (τ_reion off) | check `reionization.py` tanh parameters | bug in reionization implementation or integrator missing the reion bump |
| LB-6-15 (Σ_+ decay) | compare to `solve_bianchi_background` in isolation | LB-5 background RHS + hierarchy coupled the shear incorrectly |
| LB-6-18 (Π_2 source strength) | compare to `route_b_d2_lookup` in isolation | hierarchy T9 term sign error or missing factor |
| LB-6-19, LB-6-20 (η mismatch with CAMB) | check Ω_γ,0, Ω_ν,0 and derived Ω_r,0 | LB-0 constants SSOT drift |
| LB-6-22 (L=6 vs L=8 disagree) | check closure strategy and truncation handling at ℓ = L | LB-3 closure wrongly zeroing out Π_{L+1} |

Each diagnostic points to exactly one LB-N session; re-open that session's unit tests first before touching LB-5 or LB-6.

---

## 13. Cite map

| Test | Citation |
|---|---|
| LB-6-07 (z_eq) | Kolb §3.5 table; derived from Ω_m/Ω_r |
| LB-6-08 (z_*) | HyRec fixture metadata; Planck 2018 |
| LB-6-12 (T_ν/T_γ) | Kolb §5.5 eq (5.14) |
| LB-6-13 (T_γ) | Fixsen 2009 ApJ 707:916 |
| LB-6-14 (τ_reion) | Planck 2018 I (Aghanim+ 2018) |
| LB-6-15 (Σ conservation) | Ellis §18.3 |
| LB-6-16 (σ² × a⁶) | Ellis §18.3 eq (18.xx) |
| LB-6-18 (Route B) | `bass.spectrum.cl_assembly` SSOT |
| LB-6-19, -20 (CAMB η) | `data/camb_ref_planck2018.npz` — derived from CAMB 1.6.6 |

---

## 14. Beyond LB-6 (preview of next phase)

When LB-6 passes, the following downstream can begin:

- **Line-of-sight projection**: extract C_ℓ from the integrated PSTF tower (still within the lowell reference scope)
- **Direction-dependent likelihood**: use the integrated C_ℓ^{off-diagonal} for sky-map likelihood (lowell §14)
- **k-dependent modes**: add `∇̃` structure-constant dispatch for Types VI_h, VIII, IX
- **Perturbation sector**: CAMB-regular seeds + tilted-boost IC (lowell §13)

Each of these is a **separate multi-session effort**. LB-6 gates them all.
