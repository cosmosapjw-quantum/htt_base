# WEEK 6-03 PACKET — CDM fluid (collisionless dust closure)
## Date: 2026-04-18
## Scope: MASTER_PROMPT_LIST_bass_py_v1.1 §3 W6-03

---

## §1. Deliverables

| Artefact | Path | Lines |
|----------|------|-------|
| Module | `bass/perturbation/cdm_fluid.py` | 214 |
| Tests | `bass/perturbation/test_cdm_fluid.py` | 412 |

Total new LoC: **626**.  
New tests: **38** (target from §3 W6-03 was ~20; extra from
differentiation-from-baryon regression-guard class).

---

## §2. Public API surface

```python
# bass/perturbation/cdm_fluid.py

# Containers
CDMFluidState       # frozen: (δ_c, v_c, axis)
CDMParameters       # frozen: (H,) — single parameter

# Factories
zero_cdm_state(axis=Z)                    → CDMFluidState
make_cdm_parameters(H_conformal, decision) → CDMParameters  [W3-gated]

# Evolution RHS (W3-gated)
cdm_continuity_rhs(state, phi_dot, decision)   → float
cdm_euler_rhs(state, params, decision)         → float
cdm_step(state, phi_dot, params, dt, decision) → CDMFluidState

# Diagnostics (no gate)
cdm_v_c_analytic_decay(v0, params, d_eta)      → float
cdm_is_collisionless(state)                    → bool   [identity]
```

Four W3-gated entries, two pure diagnostics.

Notice: `cdm_euler_rhs` takes **only** `(state, params, decision)` —
no external velocity parameter. This is a structural enforcement of
the collisionless property (test class 9 explicitly guards this).

---

## §3. Physics core

### 3.1 Evolution equations (homogeneous Bianchi limit)

$$\dot\delta_c = -3\dot\Phi, \qquad \dot v_c + Hv_c = 0$$

The continuity equation is structurally identical to the baryon
continuity (W6-01): both species follow the same metric perturbation
$\Phi$. The Euler equation differs dramatically — no Thomson drag,
no sound speed.

### 3.2 Expansion damping solution

With constant $H$ over $[\eta, \eta + \Delta\eta]$:

$$v_c(\eta + \Delta\eta) = v_c(\eta) \exp(-H\Delta\eta)$$

Exposed as `cdm_v_c_analytic_decay` for convergence testing. Forward
Euler converges to this at rate $O(\mathrm{d}t)$ as verified by
`test_forward_euler_converges_to_analytic`.

### 3.3 Dust closure discipline

$\pi_c = 0$ is exact for single-stream cold matter. At second order,
velocity-dispersion streaming introduces $\sigma^{(v)}_{ij} \neq 0$,
violating dust closure. This kinetic-theory upgrade is
**explicitly deferred to bass_rs** — bass_py's first-order orthogonal
Bianchi scope treats dust closure as exact within the model.

The module encodes this commitment structurally:
- `CDMParameters` has exactly ONE field (`H`); no `tau_dot`, no `R_b`,
  no velocity-dispersion tensor parameter.
- `cdm_euler_rhs` has NO external-velocity parameter (unlike
  `baryon_euler_rhs` which takes `theta_1_photon`).

Test class 9 (`TestDifferentiationFromBaryon`) explicitly verifies
both properties through `inspect.signature` introspection — a
regression guard against accidental coupling introduction.

### 3.4 Out of scope

- Velocity dispersion tensor $\sigma^{(v)}_{ij}$ → bass_rs
- CDM tilt on tilted Bianchi backgrounds → W12+
- Gradient terms $D_a\Psi$ → W9 line-of-sight
- Cross-coupling to baryons at first order (gravity coupling enters
  through shared $\Psi$, not directly through this module)

---

## §4. Test inventory (38 tests, all PASSING after one tolerance fix)

| Class | Tests | Focus |
|-------|-------|-------|
| `TestCDMFluidState` | 5 | Container invariants |
| `TestZeroCDMState` | 1 | Factory defaults |
| `TestCDMParameters` | 4 | H validation |
| `TestMakeCDMParameters` | 2 | Factory + W3 gate |
| `TestCDMContinuityRHS` | 4 | $\dot\delta_c = -3\dot\Phi$ |
| `TestCDMEulerRHS` | 4 | Pure expansion damping |
| `TestCDMStepForwardEuler` | 4 | Combined step, axis preservation |
| `TestAnalyticDecay` | 4 | $v_c(\eta) = v_0 \exp(-H\eta)$ convergence |
| `TestDifferentiationFromBaryon` | 3 | **Structural collisionless check** |
| `TestCDMIsCollisionlessIdentity` | 2 | Regression guard |
| `TestRuntimeGatingW3` | 5 | Gating discipline |

**Runtime**: 4.20s (one test does 1000-step Euler integration, that's the budget).

**Cross-regression**: 1,434/1,434 total passing.

---

## §5. Test design observation

### 5.1 Convergence test tolerance

Initial test set `rtol < 1e-3`. Forward Euler on $\dot v = -Hv$ with
$n$ steps of $\mathrm{d}t$ has error scaling

$$|(1-H\mathrm{d}t)^n - \exp(-nH\mathrm{d}t)| \approx \frac{n(H\mathrm{d}t)^2}{2}$$

For $n=1000$, $H\mathrm{d}t = 0.002$: expected relative error
$\approx 2 \times 10^{-3}$. The $10^{-3}$ threshold was tighter than
Euler's own truncation budget.

Fix: relaxed to $5 \times 10^{-3}$, which reflects the $O(\mathrm{d}t)$
convergence rate without being so loose it fails to detect bugs.
This is the third instance (after W6-02) where tests expose the
TEST's design flaw rather than the MODULE's — the module is Euler-
accurate within Euler's inherent precision.

### 5.2 Structural regression guards

`TestDifferentiationFromBaryon` uses `inspect.signature` to verify:

1. `CDMParameters` has field list `["H"]` only
2. `cdm_euler_rhs` signature is `(state, params, decision)` only
3. Changing "any external photon context" produces identical output
   (no hidden coupling via module-level state)

These are cheap tests that catch a specific failure mode: a future
modification that accidentally adds a Thomson-like term to CDM would
change the signature or the parameters, triggering these tests
immediately. Similar pattern used successfully in W6-01 for
`tight_coupling_residual` (asserting absence of gate).

---

## §6. Validation against external references

| Claim | Reference | Status |
|-------|-----------|--------|
| $\dot\delta_c = -3\dot\Phi$ | Ma-Bertschinger 1995 Eq. 38 (homogeneous limit) | ESTABLISHED |
| $\dot v_c + Hv_c = 0$ | Ma-Bertschinger 1995 Eq. 42 (no $k\Psi$ in homogeneous limit) | ESTABLISHED |
| $v_c(\eta) = v_0 \exp(-H\eta)$ | Direct integration | ESTABLISHED |
| Dust closure $\pi_c = 0$ | Ma-Bertschinger §V.B (single-stream assumption) | CONDITIONAL (on single-stream) |

Explicitly NOT claimed:
- Kinetic-theory CDM (velocity dispersion, phase-space effects)
- Tilted CDM on Bianchi background
- Higher-moment truncation (no higher moments exist at dust closure)

---

## §7. Score card

```
PR-W6-03: CDM fluid (collisionless dust closure)
Status:   VALIDATED
Tests:    38 / 38 (1 tolerance retry on Euler convergence)
Honest scope declared: YES (§3.4 + module docstring)
V-gate status: N/A
Lines:    626 (module 214 + test 412)
Depends complete: YES (W5-A runtime, W6-01 SymmetryAxis shared)
Production ready: YES
```

---

## §8. W6 phase summary (now complete)

With W6-03 merged, the W6 phase is complete:

| Prompt | Status | Tests | Role |
|--------|--------|-------|------|
| W6-01 | ✅ VALIDATED | 49 | Baryon fluid + Thomson drag |
| W6-02 | ✅ VALIDATED | 42 | ℓ=1 dipole drive in photon hierarchy |
| W6-03 | ✅ VALIDATED | 38 | **CDM fluid — this packet** |
| W6-04 | ✅ VALIDATED | 52 | Quadrupole-aware TCA closure |

Cumulative W6 delivery: **181 tests, 3,193 LoC** (across 4 modules
plus 4 test suites). The photon + baryon + CDM fluid sector and the
quadrupole TCA closure are now in place. Forward-spectrum critical
path is unblocked.

**Document 12 ceiling progress**: 1 of 3 items delivered (W6-04).
Items 2 (visibility integral) and 3 (L=4/6 hierarchy coverage) are
unblocked — W5-A already covers item 3; W8 delivers item 2.

---

## §9. Next actions

1. **W7-01 (E-mode hierarchy)** — next critical-path step. Introduces
   the polarization multipole state $E_\ell^m$ with spin-2 streaming
   coefficients $\alpha_\ell^{m,E}, \beta_\ell^{m,E}$. Consumes
   `combined_source_pi` from W6-04.

2. **W7-02 (polter recoupling)** — closes the Thomson collision loop
   between intensity and E-mode at $\ell=2$. This is where CAMB's
   `polter` becomes numerically active in the evolution.

3. **Deferred** (unchanged):
   - `polter_camb` normalization pinning (→ W10-02)
   - CRS coefficient audit (→ W10-02)
   - ch05 manuscript sign retrofit (→ post-W10)

4. **Cumulative state**:
   - Total tests: **1,434**
   - bass/ modules: **18** (added `perturbation/cdm_fluid`)
   - W6 phase: COMPLETE
   - Document 12 ceiling: 1/3 delivered
   - No P0/P1 findings outstanding
   - Full regression runtime: ~35s

---

**End of WEEK6_03 packet.**
