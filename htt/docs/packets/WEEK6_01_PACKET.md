# WEEK 6-01 PACKET — Baryon fluid state + continuity + Euler
## Date: 2026-04-18
## Scope: MASTER_PROMPT_LIST_bass_py_v1.1 §3 W6-01

---

## §1. Deliverables

| Artefact | Path | Lines |
|----------|------|-------|
| Module | `bass/perturbation/__init__.py` | (empty sentinel) |
| Module | `bass/perturbation/baryon_fluid.py` | 321 |
| Tests | `bass/perturbation/test_baryon_fluid.py` | 541 |
| Roadmap patch | `MASTER_PROMPT_LIST_bass_py_v1.0.md` (→ v1.1 revision) | — |

Total new LoC: **862**.  
New tests: **49** (target from §3 W6-01 was ~35; the additional 14
came from expanded sign-discipline and gating coverage).

---

## §2. Public API surface

```python
# bass/perturbation/baryon_fluid.py

# Enums & containers
SymmetryAxis               # local enum, matches transport convention
BaryonFluidState           # frozen dataclass: (δ_b, v_b, axis)
BaryonParameters           # frozen dataclass: (R_b, τ̇, H)

# Factories
zero_baryon_state(axis=Z)                → BaryonFluidState
make_baryon_parameters(rho_b, rho_gamma,
                       n_e_sigma_T, scale_factor,
                       H_conformal, decision) → BaryonParameters

# Evolution RHS
baryon_continuity_rhs(state, phi_dot, decision)          → float
baryon_euler_rhs(state, theta_1_photon, params, decision) → float
baryon_step(state, theta_1_photon, phi_dot,
            params, dt, decision)                         → BaryonFluidState

# Diagnostics
tight_coupling_v_b_steady_state(theta_1_photon,
                                params, decision) → float
tight_coupling_residual(state, theta_1_photon)    → float (NO gate)
```

Six of seven public entries gate on `CanonicalDecision`. The seventh
(`tight_coupling_residual`) is a pure diagnostic with no side effects
and no physical evolution; its non-gate status is itself enforced by
`test_residual_is_pure_diagnostic_no_gate`.

---

## §3. Physics core (what this module computes)

### 3.1 Continuity equation

In the homogeneous Bianchi limit, the first-order continuity equation
for baryons is

$$\dot\delta_b = -3\dot\Phi$$

The spatial divergence term $-kv_b$ (Fourier) vanishes because $D_a$
acting on the homogeneous zeroth-order background is zero. The
k-gradient source re-enters at W9 line-of-sight and is not part of
this module.

### 3.2 Euler equation

$$\dot v_b + H v_b = +\frac{\dot\tau}{R_b}(3\Theta_1^\gamma - v_b)$$

where the **positive** sign on the Thomson drag is the correction
introduced by this PR over the v1.0 roadmap text (details in §8).

### 3.3 Steady-state analytic solution

Setting $\dot v_b = 0$,

$$v_b^{ss} = \frac{(\dot\tau/R_b) \cdot 3\Theta_1^\gamma}{H + \dot\tau/R_b}$$

which approaches $3\Theta_1^\gamma$ in the tight-coupling limit
$\dot\tau/R_b \gg H$ and approaches $0$ in the free-streaming limit
$\dot\tau \to 0$. The denominator is strictly non-negative since both
$H$ and $\dot\tau$ are validated non-negative by
`BaryonParameters.__post_init__`.

### 3.4 What this module does NOT do

- CDM fluid (→ W6-03)
- Photon dipole evolution $\Theta_1^\gamma$ (→ W6-02; here it is an
  external input)
- Spatial gradient terms $D_a\Psi$, $D_a\delta_b$ (→ W9
  line-of-sight)
- Local peculiar velocity $W_R v_{\rm loc}$ (→ W12; not merged into
  baryon tilt here)
- Baryon tilt in Bianchi background (orthogonal only at this stage)
- Velocity dispersion tensor $\sigma^{(v)}_{ij}$ (→ bass_rs only;
  first-order dust closure is exact within the model assumption)

---

## §4. Test inventory (49 tests, all PASSING)

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestBaryonFluidState` | 6 | Container invariants, frozen dataclass, finiteness |
| `TestZeroBaryonState` | 2 | Factory defaults |
| `TestBaryonParameters` | 5 | Parameter validation, R_b>0, τ̇≥0, H≥0 |
| `TestMakeBaryonParameters` | 7 | Derivation formulas, blocking decision |
| `TestContinuityRHS` | 5 | δ̇_b = -3Φ̇ exact, homogeneous limit |
| `TestEulerRHS` | 6 | Drag sign, lock condition, R_b scaling |
| `TestBaryonStepForwardEuler` | 4 | Forward Euler, axis preservation |
| `TestTightCouplingLimit` | 6 | Steady-state, τ̇→∞ lock, integration convergence |
| `TestMomentumConservationSign` | 2 | Drag direction discipline |
| `TestRuntimeGatingW3` | 6 | All public entries gate |

**Runtime**: 2.76 s (49 tests, well within budget).

---

## §5. Validation against external references

| Claim | Reference | Status |
|-------|-----------|--------|
| Thomson drag sign | Ma-Bertschinger 1995 Eq. 29 | ESTABLISHED |
| Thomson drag sign | CAMB notes §7.3 | ESTABLISHED |
| Tight-coupling $v_b = 3\Theta_1$ | Document 11 (CAMB regular adiabatic IC) | ESTABLISHED |
| $R_b = 3\rho_b/(4\rho_\gamma)$ | CAMB notes §7.3 | ESTABLISHED |
| Homogeneous-limit $\dot\delta_b = -3\dot\Phi$ | ch05_teff_corrections.tex §thomson-coupling | ESTABLISHED |

Explicitly NOT claimed:
- CAMB-equivalent accuracy beyond this module's scope
- Correct behavior under tilted Bianchi (→ W12+)
- Stability under stiff implicit integration (→ W5-B already handles
  this class; baryon-specific implicit helper is out of W6-01 scope)

---

## §6. Dependencies satisfied

| Depends on | Status |
|------------|--------|
| W3 `CanonicalDecision` infrastructure | VALIDATED (prior work) |
| W4 `beta_policy` numerical values | VALIDATED (prior work) |
| W5-A `multipole_hierarchy` conventions | VALIDATED (prior work); this module reuses the PSTF $\Theta_1$ convention |
| W5-C `bianchi_i_hierarchy` axis system | VALIDATED; this module defines its own local `SymmetryAxis` enum which matches |

Downstream consumers blocked on W6-01:
- W6-02 (ℓ=1 dipole drive in photon hierarchy): needs `v_b` as input to Thomson drag
- W6-04 (quadrupole-aware TCA): needs self-consistent baryon drag
- W13 (β→D_2 transfer): needs full first-order fluid sector

---

## §7. Score card

```
PR-W6-01: Baryon state + continuity + Euler equations
Status:   VALIDATED
Tests:    49 / 49
Honest scope declared: YES (§3.4 in this packet + module docstring)
V-gate status: N/A (V1 activates after W10-02)
Lines:    862 (module 321 + test 541)
Depends complete: YES
Production ready: YES
```

---

## §8. Physics finding — P1-level sign error in v1.0 roadmap

The v1.0 roadmap text (§3 W6-01) prescribed

$$\dot v_b + H v_b = -\frac{\dot\tau}{R_b}(3\Theta_1 - v_b)$$

This propagated the sign appearing in `ch05_teff_corrections.tex
§thomson-coupling`. However, the correct sign is **+**, as established
by:

1. **Ma-Bertschinger 1995 Eq. 29** (synchronous-gauge reference): the
   Thomson drag in the baryon Euler equation is $+(4\rho_\gamma/3\rho_b)
   \dot\tau(\theta_\gamma - \theta_b)$.
2. **CAMB notes §7.3**: the equal-and-opposite drag on photons, $-\dot
   \tau(\Theta_1 - v_b/3)$, requires the corresponding baryon drag to
   be $+(\dot\tau/R_b)(3\Theta_1 - v_b)$ for momentum conservation.
3. **Physical consistency**: photons move faster than baryons at
   recombination ($3\Theta_1 > v_b$); Thomson scattering transfers
   momentum from photons to baryons, so $\dot v_b > 0$ when $v_b < 3
   \Theta_1$. Only the **+** sign produces this.

### How the test caught it

`test_thomson_drag_sign_pushes_v_b_toward_3_theta` constructs a state
with $v_b = 0$ and $\Theta_1 > 0$ under pure Thomson drag ($H = 0$) and
asserts $\dot v_b > 0$. The incorrect **−** sign gave $\dot v_b = -5.0$,
immediately failing. Three other tests (`...pushes_v_b_down_if_above`,
`test_integration_locks_over_time`,
`test_drag_drives_toward_lock_not_away`) provided orthogonal
confirmation.

### Remediation

- Module code: `baryon_euler_rhs` sign corrected to **+**
- Steady-state formula `tight_coupling_v_b_steady_state`: denominator
  sign flipped accordingly to `H + τ̇/R_b` (now always positive;
  NaN guard retained only for degenerate $H=\dot\tau=0$ case)
- Module docstring: three passages updated (main equation block,
  Euler RHS docstring, momentum conservation note)
- Roadmap: `MASTER_PROMPT_LIST_bass_py_v1.0.md` patched to v1.1,
  §18 revision history records the correction
- Manuscript: `ch05_teff_corrections.tex` §thomson-coupling should be
  reviewed in a future retrofit task (not blocking W6-02)

### Why it mattered

If the tests had been weaker (e.g., only checking that $|\dot v_b|$
scales correctly with $R_b$, which the incorrect version does satisfy
by symmetry), the sign error would have propagated to W6-02 and
beyond, producing unstable or backwards-integrated baryon-photon
dynamics. The explicit sign-discipline tests are therefore a
structural gate, not cosmetic.

---

## §9. Next actions

1. **W6-02 start**: ℓ=1 dipole drive in photon hierarchy with
   corrected Thomson drag sign on the photon side (equal-and-opposite
   to this module's baryon-side convention). Depends: W6-01 (this
   packet) + W5-A.

2. **Deferred ch05 manuscript review**: schedule a ch05 retrofit
   mini-task to verify the sign in `§thomson-coupling` against
   Ma-Bertschinger. This is NOT a blocker for W6-02 because bass_py
   code is now physically correct; it is a manuscript hygiene item.

3. **W5 honest-scope docstring retrofit** (from §19 of roadmap):
   still pending, scheduled after W10-02 V1 gate per agreed policy.

4. **Parallel track note**: W6-02 does not require V2 bass_rs
   cross-check. Per confirmed default policy, W12+ can also begin as
   soon as W11-03 gate is reached (V2 soft-optional if bass_rs
   unavailable).
