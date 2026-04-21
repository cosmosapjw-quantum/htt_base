# WEEK 8-03 PACKET — Visibility source g·Π (LOS source at recombination)
## Date: 2026-04-18
## Scope: MASTER_PROMPT_LIST_bass_py_v1.2 §4 W8-03

---

## §1. Deliverables

| Artefact | Path | Lines |
|----------|------|-------|
| Module | `bass/transport/visibility_polter_source.py` | 534 |
| Tests | `bass/transport/test_visibility_polter_source.py` | 673 |
| Independent verification script | `scripts/verify_w8_03.py` | 224 |
| R2 fixture (staged from handoff) | `bass/recombination/fixtures/recombination_ref_planck2018.csv` | 520 KB |

Total new LoC: **1,431** (module 534 + test 673 + script 224).
New tests: **65** (roadmap target ~40; extras from `TestRealRecombinationPhysics`, `TestPiClosedForm`, `TestFourPathCrossCheck`, `TestW3Surface`).

---

## §2. Public API surface

```python
# bass/transport/visibility_polter_source.py

# Config
VisibilityPolterConfig            # frozen: recomb_interp, use_camb_polter, polter_camb_normalization
    .is_camb_mode

# Π combiners (four independent paths)
pi_pstf(theta_2, E_2)             → Θ_2 − √6 E_2                  (Path A)
pi_subleading_limit(theta_2)      → (5/2) Θ_2                     (Path B)
pi_from_tca_sources(S_T, S_E, Γ_T, decision=None) → Π via solve   (Path C)
pi_closed_form_from_sources(S_T, S_E, Γ_T) → (10/(3Γ_T))(S_T−√6S_E) (Path D)
polter_camb_at(pig, E_2)          → pig/10 + 9 E_2/15

# Visibility-weighted source
g_weighted_pi_pstf(z, Θ_2, E_2, config)        → g(z) · Π
g_weighted_polter_camb(z, pig, E_2, config)    → g(z) · polter_camb
g_weighted_pi_on_grid(z_grid, Θ_fn, E_fn, config) → ndarray

# Diagnostics
gpi_peak_in_z(Θ_fn, E_fn, config, ...)         → (z_peak, gpi_peak)
gpi_integral_trap_in_z(z_grid, Θ_vals, E_vals, config) → ∫ g·Π dz

# Sign assertions (v1.2 pattern)
assert_visibility_positive(config, n_samples, atol)
assert_pi_sign_matches_theta2_at_subleading(theta_2, atol)
assert_gpi_peak_near_last_scattering(config, Θ_fn, E_fn, z_exp, z_tol)

# Cross-check residuals
three_way_pi_residual_at_subleading(theta_2, gamma_T) → dict
four_path_pi_residual_general(S_T, S_E, gamma_T)      → dict

# η(z) light utility (flat ΛCDM, W9-01 upgrade point)
conformal_time_at_z(z, cosmology, z_upper, quad_limit)    → float Mpc
conformal_lookback_at_z(z, cosmology, z_upper, quad_limit) → float Mpc

# Scope guards (raise OutOfScopeError)
full_los_integral(...)     # W9-01
isw_source(...)           # W9-02
doppler_source(...)       # W9-01
```

No W3 gate on the data-transformation surface (`g_weighted_*`, `gpi_*`, `pi_pstf`, `pi_subleading_limit`, `pi_closed_form_from_sources`). `pi_from_tca_sources` inherits the W3 gate from `solve_tca_closure`; supplies a permissive default decision.

---

## §3. Physics core

### 3.1 Source at recombination (LOS integrand node)

Synchronous-gauge temperature LOS source (Ma-Bertschinger 1995, Lewis-Challinor 2002):

$$S_T(\eta) = g(\eta)\left[\Theta_0 + \Psi + \tfrac{1}{4}\Pi\right] + e^{-\kappa}(\dot\Psi+\dot\Phi) + \tfrac{d}{d\eta}[g(\eta)\,v_b]$$

E-mode LOS source:

$$S_E(\eta) = -g(\eta)\cdot\tfrac{\sqrt{6}}{4}\,\Pi$$

with PSTF combined source $\Pi = \Theta_2 - \sqrt{6}\,E_2$ (Pontzen-Challinor 2007 Eq. 6.2).

**W8-03 delivers only the $g\cdot\Pi$ node.** ISW, Doppler, monopole/SW, and the full Bessel-weighted LOS quadrature are explicitly out of scope and raise `OutOfScopeError` via stub functions with W9-01 / W9-02 pointers.

### 3.2 Four independent paths for Π

At arbitrary source doublet $(S_T, S_E, \Gamma_T)$:

**Path A** (direct PSTF): given $(\Theta_2, E_2)$ from any source, $\Pi_A = \Theta_2 - \sqrt{6}E_2$.

**Path B** (analytic subleading): at $S_E=0$, closure gives $E_2=-(\sqrt{6}/4)\Theta_2$, so $\Pi_B = (5/2)\Theta_2$.

**Path C** (LAPACK solve): $(\Theta_2, E_2) = \mathrm{solve}(\Gamma_T M, (S_T, S_E))$ then Path A.

**Path D** (closed form): inverting the W6-04 $2\times 2$ system analytically and substituting yields
$$\boxed{\;\Pi = \frac{10}{3\Gamma_T}\left(S_T - \sqrt{6}\,S_E\right)\;}$$
verified by: (i) at $S_E=0$, reduces to $(5/2)\Theta_2$ via amplification $S_T=(3/4)\Gamma_T\Theta_2$; (ii) at $\Theta_2=0$ pure E source, reduces to $-\sqrt{6}E_2$ exactly.

All four paths must agree at machine precision. This is the **genuine cross-check** — four distinct numerical routes to the same physical quantity.

### 3.3 Synthetic vs real fixture — an analyzed asymmetry

The synthetic `make_synthetic_tanh_table` fixture (W8-01, pre-session VALIDATED) uses $d\kappa/dz = 10^{-2}\cdot\dot\tau(z)$ as an artificial scale factor in place of the physical $c/((1+z)H(z))$. Closed-form peak-equation analysis:

$$\frac{d\ln\dot\tau}{dz}\bigg|_{z_{\rm peak}} = \frac{d\kappa}{dz}\bigg|_{z_{\rm peak}} \implies \frac{2}{1+z_{\rm peak}} = 10^{-2}\cdot\dot\tau(z_{\rm peak})$$

(for $z\gg z_{\rm tr}$ so $d\ln x_e/dz\to 0$) places the synthetic peak at $z\approx 1361$, not $1089$. This is a **mathematical consequence of the fixture construction**, not a physics bug. R0 synthetic is used only for algebra / linearity / broadcast / self-consistency tests; R2 HyRec-derived fixture (Planck 2018 cosmology via HyRec-2 sandbox) is used for all physics-range asserts.

This asymmetry was uncovered when the first draft of `test_peak_near_recombination` assumed the synthetic peak would coincide with real recombination. Closed-form analysis recovered the true synthetic peak at 1361 analytically; the test was then restructured into R0 self-consistency + R2 physics-calibrated tiers.

### 3.4 Reionization contribution

$g(\eta)$ folds reionization natively via `extend_table_with_reionization` (W8-02). On the R2 fixture the late-time bump at $z\sim 7$ adds $\tau_{\rm reion}\approx 0.054$ to $\kappa(z=0)$, suppressing the recombination-era visibility by $e^{-\tau_{\rm reion}}\approx 0.947$. The W8-03 module consumes the extended $g$ without change; the reion suppression at $z\approx 1089$ is checked directly in `TestRealRecombinationPhysics` and in the independent verification script.

### 3.5 Out of scope (declared deferred)

- Full LOS quadrature $\int d\eta\,S_T(\eta)\,j_\ell[k(\eta_0-\eta)]$ → W9-01
- ISW term $e^{-\kappa}(\dot\Psi+\dot\Phi)$ → W9-02
- Doppler term $d(g\cdot v_b)/d\eta$ → W9-01 (needs $v_b$ spline)
- Bianchi-I direction-dependent $\tilde g(\eta,\hat e)\cdot\tilde\zeta_{ab}$ → W11+
- $m\neq 0$ polter recoupling → future
- PSTF-to-CAMB polter normalization constant → W10-02

---

## §4. Test inventory (65 tests, all PASSING)

| Class | Tests | Tier | Focus |
|-------|-------|------|-------|
| `TestVisibilityPolterConfig` | 5 | — | Frozen, defaults, validation |
| `TestPiPSTF` | 3 | algebra | Path A re-export, linearity |
| `TestPiSubleadingLimit` | 3 | algebra | Path B (5/2)Θ, sign, reject NaN |
| `TestPiClosedForm` | 3 | algebra | Path D reductions at limits |
| `TestPiFromTCASources` | 2 | algebra | Path C vs closed form |
| `TestGWeightedPiPSTF` | 5 | R0 | Scalar/array/sign/zero/peak-synth |
| `TestCAMBPolterCoexistence` | 3 | R0 | Re-export + mode switch |
| `TestGPiOnGrid` | 3 | R0 | Callable inputs, shape guard |
| `TestGPiPeak` | 3 | R0 | Synthetic peak, range guard |
| `TestGPiIntegral` | 3 | R0 | Sign preservation, shape validation |
| **`TestThreeWayAtSubleading`** | **3** | algebra | **3 paths residual exact** |
| **`TestFourPathCrossCheck`** | **4** | algebra | **4 paths residual ~1e-16 rel** |
| **`TestPhysicalSignAssertions`** | **5** | v1.2 | **Sign assertions pass/fail** |
| `TestEtaOfZLight` | 4 | utility | η(0), monotone, bound checks |
| `TestScopeGuards` | 3 | interface | Deferred features raise |
| `TestReionizationFoldedIntoG` | 2 | R2-aware | Low-z bump + R2 suppression |
| **`TestRealRecombinationPhysics`** | **8** | **R2** | **z_peak≈1088.8, z_*≈1089.9 Planck** |
| `TestW3Surface` | 3 | gate | Decision propagation |

**Runtime**: 1.88 s.

---

## §5. Four-path cross-verification matrix

Independent of tests, the script `scripts/verify_w8_03.py` cross-checks key numerical claims from standalone code paths:

| Block | Check | Result |
|-------|-------|--------|
| 1 | Π(Θ=3.7, E=-√6/4·Θ) == (5/2)Θ | rel 0, exact |
| 2 | 200 random configs, Path C vs Path D | **worst rel 3.85e-15** |
| 3 | 4-path residual at physical / extreme magnitudes | **worst rel 3.26e-16** |
| 4 | R2 z_peak and z_* vs Planck 2018 | z_peak=1088.79, z_*=1089.89 |
| 5 | Synthetic peak satisfies its analytic root equation | LHS=1.468e-3, RHS=1.555e-3 |
| 6 | R2 g·Π peak tracks g peak for constant profile | \|Δ\|=0.028 |
| 7 | R2 reion suppression ratio vs e^{-0.054} | 0.9483 vs 0.9474 |
| 8 | Flat ΛCDM η_0 vs literature 14.15 Gpc | 14.12 Gpc |

All blocks: **PASS**.

---

## §6. Score card

```
PR-W8-03: Visibility source g·Π (LOS source at recombination)
Status:            VALIDATED
Tests:             65 / 65 (one test-assumption iteration, not a module bug)
Honest scope:      YES (§3.5 + module docstring + OutOfScopeError stubs)
V-gate status:     N/A (physics cross-check only; CAMB V-gate is W10-02)
Lines:             1,431 (module 534 + test 673 + script 224)
Depends complete:  YES (W6-04, W7-02, W8-01, W8-02)
Production ready:  YES for LOS integrand node at recombination
Cross-verification: 4-path analytical + R2 Planck 2018 agreement ✓
Physical sign assertions: 5 (v1.2 pattern continued)
R0/R2 fixture separation: YES
Banned vocab scan: CLEAN
```

---

## §7. Test design iteration (two corrective cycles)

### Cycle 1 — fixture-vs-assumption mismatch (R0/R2 tier separation)

**Initial failure** (first draft): `test_peak_near_recombination` asserted synthetic-fixture g peak at z ∈ (1000, 1200). The synthetic fixture's peak is at z ≈ 1361 — a mathematical consequence of `dκ/dz = 10⁻² · τ̇(z)` (non-physical scale factor) combined with `τ̇ ∝ x_e(z)(1+z)²` growth.

**Root cause**: test assumption "parameter `z_transition=1089` ⇒ peak at 1089" conflated the synthetic fixture's shape parameter with real-physics visibility peak location. Real physics needs `(1+z)^{-5/2}` damping from `c/((1+z)H)` to keep the peak at z_transition; synthetic lacks this damping.

**Corrective action** (per attached production-path document):

1. Promoted the R2 HyRec-CSV fixture (handoff reference) to a module-scoped pytest fixture.
2. Split `test_peak_near_recombination` into:
   - `test_peak_in_synthetic_matches_analytic_root` (R0 self-consistency, checks the synthetic peak equation analytically)
   - `TestRealRecombinationPhysics::test_real_g_peak_at_last_scattering` (R2 physics, checks z_peak ∈ (1080, 1100))
3. Updated `assert_gpi_peak_near_last_scattering` docstring to flag R2-only usage.
4. Restricted `TestReionizationFoldedIntoG::test_gpi_near_recomb_largely_unchanged_by_reion` to the R2 fixture (the synthetic+reion hybrid double-counts κ and is arithmetically inconsistent).
5. Relaxed `assert_visibility_positive` from `g > 0` (strict) to `g ≥ 0` (physics truth), accommodating deep-opacity underflow at z >> z_*.
6. Strengthened `test_visibility_positive_raises_on_broken_interp` to force a genuine negative spline undershoot.

### Cycle 2 — canonical decision production merge

**Pre-merge state**: the standalone W8-03 workspace used a minimal stub for `bass.runtime.canonical_decision` that allowed direct `CanonicalDecision(allow_reduction=True)` construction. On merge into the full bass_py tree, the real module rejects this — `CANONICAL_DECISION_DESIGN.md` §2 sanctions only `make_canonical_decision(beta_result, sigma_result, tangency_result)` as the construction path. Direct construction is a P0 ownership violation caught by `test_ownership_freeze.py`.

**Corrective action** (pre-merge refactor):

1. `pi_from_tca_sources` now requires `decision: CanonicalDecision` (not `Optional[...] = None`). The stub-era default was deleted.
2. `three_way_pi_residual_at_subleading` and `four_path_pi_residual_general` likewise require an explicit decision argument.
3. Test module now imports `make_canonical_decision` and defines `_allowing_decision()` / `_blocking_decision()` helpers that mirror the factory pattern in `bass/closure/test_quadrupole_tca.py`.
4. `TestW3Surface` class restructured: `test_explicit_decision_accepted`, `test_two_allowing_decisions_give_same_result` (determinism), `test_blocking_decision_raises` (asserts `CanonicalBlockError`, not bare `RuntimeError`).
5. `scripts/verify_w8_03.py` now builds an `_ALLOW` canonical decision via the factory at startup and threads it through Path C and four-path calls.

**Unchanged**: all Π numerical results, all R2 physics checks, all four-path cross-check residuals. The refactor is a type-surface discipline change, not a physics change.

This is the **seventh and eighth** instances in the bass_py project where test-design / integration-surface issues surfaced rather than module-physics issues. Running tally of the audit-driven bug-catch pattern: module physics first-time-right, tests and surface discipline catch assumption drift.

### Why not R1?

The attached doc sketches an R1 "semi-physical calibrated tanh" rung between R0 synthetic and R2 HyRec. W8-01 (`load_recombination_table`) + W8-02 (`extend_table_with_reionization`) already operates on the HyRec CSV with correct `c/((1+z)H)` geometry, so the R1 functionality is absorbed by R2 in our current stack. We document R1 as a valid design point for bass_rs if a sandbox-free baseline is desired (no implementation needed for W8-03).

---

## §8. Outstanding items & next steps

### Immediate successor (W9-01)

Full LOS integral with Bessel weighting, ISW, Doppler. This module's `g·Π` node is one of the integrand terms. W9-01 will:
- Promote `conformal_time_at_z` to production-grade quadrature
- Add `conformal_time_grid` for LOS integration samples
- Replace `full_los_integral` stub with implementation
- Add `doppler_source` implementation using `v_b(η)` spline from fluid hierarchy

### Carried to W10-02

PSTF Π ↔ CAMB polter normalization constant. Both `g_weighted_pi_pstf` and `g_weighted_polter_camb` are pre-wired so the V-gate consumer can swap modes via `VisibilityPolterConfig.use_camb_polter` without touching call sites.

### Optional polish (P3)

- `test_mode_switch_changes_output` currently uses an implicit assertion via `np.isclose`; could be tightened with analytic ratio check. Not blocking.
- Real-fixture reion suppression test allows ratio ∈ (0.88, 0.99); production-path tightening to ±1% of `e^{-τ_reion}` feasible once τ_reion extraction from the extended table is wired (minor W8-02 follow-up, not in W8-03 scope).

---

## §9. MASTER_PROMPT_LIST status delta

| Phase | Before this session | After |
|-------|--------------------|----|
| W6 | 4/4 complete | 4/4 |
| W7 | 2/2 complete | 2/2 |
| W8 | 2/3 complete | **3/3 COMPLETE** |
| W9 | 0/2 | 0/2 (next: W9-01) |
| Overall | 10/24 = 41.7% | **11/24 = 45.8%** |

Document 12 ceiling (LOS wiring items):
- Item 1/3: W7-02 polter loop ✓ (previous session)
- **Item 2/3: W8-03 g·Π node ✓ (this session)**
- Item 3/3: Full LOS → W9-01

**Test total**: 1,575 (pre, measured on uploaded bass_py.zip) + 65 (new) − 0 (removed) = **1,640** (full bass + tsc regression: **1,640 passed in 37.31s, 0 failures**).

**Integration status** (post-merge on uploaded bass_py.zip):
- W8-03 suite standalone: **65 / 65 passed in 2.30s**
- Full bass + tsc regression: **1,640 / 1,640 passed in 37.31s**
- Independent verification script: **8 / 8 blocks PASS**
- Banned vocab scan (module + test + script + packet): **CLEAN**

---

**End of packet.**

Author-of-record: Claude (Opus 4.7) on behalf of Jiwon
Generated: 2026-04-18
