# WEEK 7-01 PACKET — E-mode hierarchy + spin-2 streaming
## Date: 2026-04-18
## Scope: MASTER_PROMPT_LIST_bass_py_v1.2 §4 W7-01

---

## §1. Deliverables

| Artefact | Path | Lines |
|----------|------|-------|
| Module | `bass/transport/emode_hierarchy.py` | 403 |
| Tests | `bass/transport/test_emode_hierarchy.py` | 602 |

Total new LoC: **1,005**.  
New tests: **62** (target from roadmap §4 W7-01 was ~55; extra from
dedicated `TestW604CrossCheck` and `TestPhysicalSignAssertions`
classes per v1.2 patterns).

---

## §2. Public API surface

```python
# bass/transport/emode_hierarchy.py

# Spin-2 streaming coefficients (pure utility, no gate)
pstf_emode_coupling_coeffs(ell, m=0) → (α^E_ℓ, β^E_ℓ)

# Containers
EModeParameters          # (thomson_rate, k_eff, ell_max, ell2_damping_factor)
EModeState               # (amplitudes shape (ell_max−1,), ell_max)

# Factories
zero_emode_state(ell_max) → EModeState

# Matrix/vector primitives (no gate)
build_emode_streaming_matrix(params)                   → ndarray(dim, dim)
build_emode_damping_vector(params)                     → ndarray(dim,)
build_emode_source_vector(params, theta_2_external=0) → ndarray(dim,)

# Evolution and steady state (W3-gated)
euler_step_emode(state, params, theta_2, dt, decision)        → EModeState
compute_emode_steady_state(params, theta_2, decision)         → EModeState
integrate_emode_to_steady_state(...)                          → EModeIntegrationResult

# Diagnostics (no gate)
cfl_max_dt_emode(params)                              → float
subleading_cross_check_ratio(state, theta_2_external) → float
```

Three W3-gated entries (`euler_step`, `steady_state`, `integrate`).
Six pure utilities + two diagnostics do NOT gate, enforced by
`test_utilities_have_no_gate`.

---

## §3. Physics core

### 3.1 Spin-2 PSTF streaming coefficients

For axisymmetric m=0:

$$\alpha^E_\ell = \frac{\sqrt{\ell^2 - 4}}{2\ell+1}, \qquad \beta^E_\ell = \frac{\sqrt{(\ell+1)^2 - 4}}{2\ell+1}$$

Boundary: $\alpha^E_2 = 0$ (spin-2 requires $\ell \geq 2$). Verified:

- $\alpha^E_2 = \sqrt{0}/5 = 0$ ✓
- $\beta^E_2 = \sqrt{5}/5$
- $\alpha^E_3 = \sqrt{5}/7$
- $\beta^E_3 = 2\sqrt{3}/7$

Asymptotic: $\alpha^E_\ell, \beta^E_\ell \to 1/2$ as $\ell \to \infty$
(consistent with scalar limit).

### 3.2 Evolution equation

$$\dot E_\ell + k[\alpha^E_\ell E_{\ell-1} - \beta^E_\ell E_{\ell+1}] = -\Gamma^E_\ell E_\ell + S^E_\ell$$

with

$$\Gamma^E_2 = \frac{2}{5}\Gamma_T, \quad \Gamma^E_{\ell \geq 3} = \Gamma_T$$

$$S^E_{\ell = 2} = -\frac{3}{5\sqrt{6}}\Gamma_T \Theta_2^{\rm external}, \quad S^E_{\ell \geq 3} = 0$$

### 3.3 The W6-04 subleading cross-check

At isolated $\ell=2$ ($k_{\rm eff} = 0$, ell_max=2), steady state gives

$$0 = -\Gamma^E_2 E_2 + S^E_2 \implies E_2 = \frac{S^E_2}{\Gamma^E_2} = \frac{-(3/(5\sqrt{6}))\Gamma_T\Theta_2}{(2/5)\Gamma_T} = -\frac{\sqrt{6}}{4}\Theta_2$$

This **exactly** matches W6-04's subleading-$S_E$ formula
$E_2/\Theta_2 = -\sqrt{6}/4$, derived from a completely independent
algebraic matrix inversion. The cross-check is verified to
**machine precision (1.30e-16 relative difference)** in
`TestW604CrossCheck::test_isolated_ell_2_agrees_with_w604_subleading`.

### 3.4 DampingProfile pattern prep (Finding B.1/C.1 response)

Per v1.2 revision history, `EModeParameters` introduces an explicit
`ell2_damping_factor` (default 2/5) rather than embedding the factor
implicitly in a scalar `damping_rate`. This is the **first
deployment of the DampingProfile pattern** — the full retrofit to
W5-A is still scheduled for W7-phase API consolidation, but the
design is now prototyped in production.

### 3.5 Out of scope (declared deferred)

- $m \neq 0$ channels (requires B-mode mixing + rotation coefficients) → W9+
- B-mode hierarchy (vector mode) → W9
- **Bidirectional** closure between $\Theta_2$ and $E_2$ (polter
  recoupling loop) → W7-02
- Tilted-frame boost of spin-2 harmonics → W12
- Line-of-sight polarization source $g\cdot\Pi$ → W8-03

---

## §4. Test inventory (62 tests, all PASSING)

| Class | Tests | Focus |
|-------|-------|-------|
| `TestSpin2CouplingCoeffs` | 8 | α, β formulas, boundary, asymptotic |
| `TestEModeParameters` | 6 | Container invariants, ell2 factor |
| `TestEModeState` | 6 | Shape, access, frozen |
| `TestZeroEModeState` | 3 | Factory |
| `TestStreamingMatrixStructure` | 6 | Dim, boundary, truncation |
| `TestDampingVector` | 4 | (2/5) factor at ℓ=2 |
| `TestSourceVector` | 4 | Θ_2 → E_2 coupling |
| `TestEulerStepEMode` | 3 | Formula, gates, shape |
| `TestSteadyState` | 5 | linsolve, trivial handling |
| **`TestW604CrossCheck`** | **3** | **Independent verification vs W6-04** |
| `TestIntegrationConvergence` | 2 | Euler → analytic |
| **`TestPhysicalSignAssertions`** | **4** | **v1.2 NEW PATTERN** |
| `TestCFLDiagnostic` | 2 | CFL bound |
| `TestSubleadingCrossCheckRatio` | 2 | Diagnostic |
| `TestRuntimeGatingW3` | 4 | Gating discipline |

**Runtime**: 2.29 s (after one test design fix).

---

## §5. Cross-module verification (critical)

### 5.1 W6-04 ↔ W7-01 independent agreement

Two independent derivation paths must agree at the isolated
$\ell=2$, $k=0$ limit. Independent verification script output:

```
W6-04: algebraic TCA closure with S_T=1e-3, S_E=0
  Θ_2 = +1.333333e-06  (POSITIVE ✓)
  E_2 = -8.164966e-07  (NEGATIVE ✓)
  E_2/Θ_2 = -0.612372  (target -0.612372 ✓)

W7-01: ODE steady state at isolated ℓ=2, fed with W6-04's Θ_2
  E_2 = -8.164966e-07

Cross-check:
  |E_2(W7-01) - E_2(W6-04)| / |E_2(W6-04)| = 1.30e-16 (machine precision) ✓
```

### 5.2 Streaming cascade demonstration

At $k_{\rm eff} = 100$, $L_{\rm max} = 5$, $\Gamma_T = 10^3$:

```
  E_2 = -8.136e-07 (slightly less than isolated due to cascade)
  E_3 = -2.594e-08 (populated by streaming)
  E_4 = -9.963e-10 (further cascade)
```

The cascade magnitude ratio $|E_3/E_2| \approx 3\%$ at these
parameters is consistent with the coupling strength
$\alpha^E_3 \cdot k_{\rm eff}/\Gamma_T = (\sqrt{5}/7)(100/10^3) \approx 0.032$.

---

## §6. Physical sign discipline (v1.2 pattern, first deployment)

New test class `TestPhysicalSignAssertions` makes externally-known
signs into explicit test assertions:

```python
def test_positive_theta_2_gives_negative_E_2_at_steady(self):
    # Externally predictable: Θ_2 > 0 → E_2 < 0 (cross-coupling sign)
    ss = compute_emode_steady_state(..., theta_2=+1e-4, ...)
    assert ss.E_ell(2) < 0.0  # hard sign assertion

def test_negative_theta_2_gives_positive_E_2_at_steady(self):
    ss = compute_emode_steady_state(..., theta_2=-1e-4, ...)
    assert ss.E_ell(2) > 0.0

def test_source_coefficient_magnitude(self):
    # Magnitude 3/(5√6) ≈ 0.2449 is a pure analytic constant
    assert abs(abs(s[0]) - 3.0/(5.0*SQRT6)) < 1e-14

def test_effective_damping_at_ell_2_is_two_fifths_gamma(self):
    # 2/5 = 0.4 exactly from document §3.3
    assert abs(gamma[0] - 0.4) < 1e-14
```

These assertions would have caught the W6-04 sign error (W6-04's
sign-flipped formula would give $\Theta_2 < 0$ for $S_T > 0$). The
pattern is now **mandatory** for every algebraic inverse or steady-
state formula going forward.

---

## §7. Score card

```
PR-W7-01: E-mode hierarchy + spin-2 streaming
Status:   VALIDATED
Tests:    62 / 62 (1 test design retry)
Honest scope declared: YES (§3.5 in packet + module docstring)
V-gate status: N/A
Lines:    1,005 (module 403 + test 602)
Depends complete: YES (W5-A streaming framework, W6-04 Π source)
Production ready: YES
Cross-module cross-check: ✓ (W6-04 ↔ W7-01 at machine precision)
Physical sign assertions: ✓ (4 tests, v1.2 pattern)
DampingProfile prep: ✓ (ell2_damping_factor explicit field)
```

---

## §8. Test design retry (one correction)

`test_trivial_dynamics_rejects_nonzero_source` initially expected
`ValueError` when `thomson_rate=0`, `k_eff=0`, `theta_2 ≠ 0`. But the
source vector $s = -(3/(5\sqrt{6}))\Gamma_T\Theta_2$ **auto-zeros**
when $\Gamma_T = 0$, so the scenario "trivial dynamics + non-zero
source" is **structurally impossible** in this API.

This is correct physics: without Thomson scattering, no coupling
path from $\Theta_2$ to $E_2$ exists. Test corrected to verify the
correct behavior (zero state returned, no error).

No module change required; one test correction only.

---

## §9. Next actions

1. **W7-02 (polter recoupling)** next prompt. Adds bidirectional
   closure: W7-01 treats $\Theta_2$ as external; W7-02 wraps both
   W7-01 and W6-04 TCA to close the loop self-consistently. Target
   ~300 lines, ~35 tests.

2. **W8-01 (recombination ingest)** unblocked. Will consume
   `thomson_rate` from W7-01's `EModeParameters`.

3. **Deferred** (unchanged):
   - Full `DampingProfile` retrofit to W5-A (end of W7 phase)
   - B-mode hierarchy (W9)
   - W5-C m=±2 Wigner normalization (W7+ as needed)
   - ch05 manuscript sign retrofit

4. **Cumulative state**:
   - Total tests: **1,496** (+62)
   - bass/ modules: **19** (+ `transport/emode_hierarchy`)
   - W7-01: COMPLETE
   - Document 12 ceiling items: 1/3 delivered (W6-04)
   - No P0/P1 findings outstanding
   - v1.2 patterns successfully deployed: physical sign assertions,
     W6-04 cross-check, DampingProfile prototype
   - Full regression runtime: ~36s

---

**End of WEEK7_01 packet.**
