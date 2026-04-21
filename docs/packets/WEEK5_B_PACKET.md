# WEEK 5-B PACKET — Implicit Integrators for Stiff Hierarchy

**Date**: 2026-04-17
**Scope**: Three implicit integrators for the multi-ℓ hierarchy decoupling stability from accuracy in the pre-recombination stiff regime; exponential integrator as exact-for-linear-TI validation oracle
**Module**: `bass/transport/implicit_hierarchy.py` (~340 LoC)
**Tests**: 49 across 10 classes + 1 ownership parametrized
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings (single-pass green)
**Cumulative**: **1,209 tests**, 54.52 s runtime

---

## §1 — Core mathematical observation

For frozen-background shear the hierarchy equation

$$\frac{d\vec\Theta}{dt} = (M - \Gamma I)\vec\Theta + \vec b = A\vec\Theta + \vec b$$

is a **linear time-invariant ODE**. The analytic solution is

$$\vec\Theta(t + h) = e^{A h}\vec\Theta(t) + A^{-1}\left(e^{A h} - I\right)\vec b$$

This closed-form lets the exponential integrator serve as a **validation oracle**: it produces the exact answer at any $h$ regardless of stiffness. Backward Euler and Crank–Nicolson are approximations that converge to the exact result as $h \to 0$.

Implementation avoids the explicit $A^{-1}$ via the **augmented-matrix trick**: embed $(A, \vec b)$ in an $(L+2)\times(L+2)$ block

$$\begin{pmatrix} A & \vec b \\ 0 & 0 \end{pmatrix} \xrightarrow{\exp} \begin{pmatrix} e^{Ah} & \varphi_1(Ah)\,h\,\vec b \\ 0 & 1 \end{pmatrix}$$

so a single `scipy.linalg.expm(aug × h)` call produces both $e^{Ah}$ and the forced term simultaneously, gracefully handling near-singular $A$.

---

## §2 — Three integrators + stability functions

| Method | Step equation | Order | Stability class | Use case |
|--------|---------------|-------|------------------|----------|
| Backward Euler | $(I - hA)\Theta^{n+1} = \Theta^n + h\vec b$ | 1 | A-stable, **L-stable** | Most robust; stiff stability |
| Crank–Nicolson | $(I - \frac{h}{2}A)\Theta^{n+1} = (I + \frac{h}{2}A)\Theta^n + h\vec b$ | 2 | A-stable, not L-stable | Mildly stiff + accuracy |
| Exponential | Exact $\exp$ formula | ∞ | Exact | Oracle; frozen-A production |

Stability functions verified numerically:

| $z = hA$ eigenvalue | $\vert R_{\rm BE}\vert = \frac{1}{\vert 1-z\vert}$ | $\vert R_{\rm CN}\vert = \left\vert\frac{1+z/2}{1-z/2}\right\vert$ | $\vert R_{\rm EXP}\vert = \vert e^z\vert$ |
|---------------------|-----------------|------------------|---------|
| −0.1 | 0.909 | 0.905 | 0.905 |
| −1 | 0.500 | 0.333 | 0.368 |
| −10 | 0.091 | 0.667 | 4.5e-05 |
| −100 | 0.010 | **0.961** | 3.7e-44 |
| $-10^{10}$ | $10^{-10}$ | **≈1.000** | 0 |

The $|R_{\rm CN}(-\infty)| \to 1$ behavior is the diagnostic signature that CN is A-stable but NOT L-stable — in extremely stiff regimes CN preserves mode amplitude rather than damping it, which can produce spurious oscillations. BE's $|R(-\infty)| \to 0$ is the L-stability hallmark.

---

## §3 — Stiff-regime stability verification

Critical test: pre-recombination scenario with $\dot\tau = 10^4$, $H = 30$, $k_{\rm eff} = 10$, $L_{\max} = 5$, $\sigma = 10^{-6}$. CFL limit: $dt_{\rm CFL} = 2/(\Gamma + k_{\rm eff}) \approx 2 \times 10^{-4}$.

### 3.1 50 steps at $dt = 10 \times dt_{\rm CFL}$

| Method | $\max\|\Theta\|$ | Relative error vs analytic target |
|--------|-------------------|-----------------------------------|
| Explicit Euler (W5-A) | $1.7 \times 10^{54}$ | **DIVERGES** (+64 orders) |
| Backward Euler | $2.04 \times 10^{-10}$ | $8.5 \times 10^{-16}$ (machine precision) |
| Exponential | $2.04 \times 10^{-10}$ | $3.6 \times 10^{-16}$ (machine precision) |

### 3.2 BE survival at $100 \times dt_{\rm CFL}$

At $dt = 100 \times dt_{\rm CFL}$, 30 steps: max $\|\Theta\| < 10^{-5}$, fully finite. BE remains stable at **arbitrarily large** $dt$ — exactly the L-stability promise.

### 3.3 Driver step counts at 10× CFL

| Method | Steps to converge (tolerance $10^{-8}$) |
|--------|----------------------------------------|
| BE | 8–9 |
| CN | 96 |
| EXP | **2** (single big step nearly reaches $\Theta_\infty$) |

Exponential integrator's 2-step convergence reflects its exactness: after the first step we land close enough to $\Theta_\infty$ that the relative change meets tolerance immediately.

---

## §4 — Cross-method agreement at small dt

All three methods converge at $dt \to 0$. Single-step verification at $dt = 10^{-5}$ (well below CFL):

| Method | Result at ℓ=2 (truth $2.04283 \times 10^{-11}$) | Error vs EXP |
|--------|----------------------------------|--------------|
| Explicit Euler | $2.04386 \times 10^{-11}$ | $1.0 \times 10^{-14}$ |
| Backward Euler | $2.04181 \times 10^{-11}$ | $1.0 \times 10^{-14}$ |
| Crank–Nicolson | $2.04283 \times 10^{-11}$ | $1.7 \times 10^{-18}$ |
| Exponential | $2.04283 \times 10^{-11}$ | reference |

CN's error at small $dt$ is 4 orders of magnitude smaller than BE/explicit — the signature of 2nd-order vs 1st-order accuracy. Verified via the 2nd-order convergence test in `test_second_order_accuracy`.

### Composition law check

Two exponential steps of $dt$ reproduce one exponential step of $2\,dt$ to machine precision ($|\Delta| < 10^{-15}$). This is the exact-semigroup property $e^{A(t+s)} = e^{At}\,e^{As}$.

---

## §5 — Implementation ledger

### 5.1 Public API (5 gated entry points)

| Function | Role |
|----------|------|
| `backward_euler_step` | One BE step; raises `CanonicalBlockError` if blocked |
| `crank_nicolson_step` | One CN step |
| `exponential_step` | One exact exponential step (uses `scipy.linalg.expm`) |
| `integrate_implicit_to_steady_state` | Generic driver taking `ImplicitMethod` enum |
| `stability_function_ratio` | Evaluate $R(z)$ for analysis (no gating — pure math) |

### 5.2 Types

| Component | Role |
|-----------|------|
| `ImplicitMethod` enum | `{BACKWARD_EULER, CRANK_NICOLSON, EXPONENTIAL}` |
| Reuses `MultipoleState`, `HierarchyParameters`, `HierarchyIntegrationResult` from W5-A | |

### 5.3 Internal helpers

- `_assemble_system(params)` returns $(A, \vec b)$ tuple
- `_backward_euler_unchecked`, `_crank_nicolson_unchecked`, `_exponential_unchecked` — gate-bypassing versions used inside the driver loop
- `_validate_step_inputs` — shared input validation

### 5.4 Import graph

```
bass/transport/implicit_hierarchy  ──→  bass/transport/multipole_hierarchy (W5-A)
                                    ──→  bass/collision/thomson_tensor (W4D3)
                                    ──→  bass/runtime/canonical_decision (W3D1)
                                    ──→  scipy.linalg.expm
```

Clean BASS-internal dependencies. Ownership freeze enforces TSC→bass/runtime forbidden path (already satisfied).

---

## §6 — Three-tier claim taxonomy

### 6.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| $R_{\rm BE}(z) = 1/(1-z)$, $R_{\rm CN}(z) = (1+z/2)/(1-z/2)$, $R_{\rm EXP}(z) = e^z$ | 6 tests in `TestStabilityFunctions` |
| BE formula $(I - hA)\Theta' = \Theta + h\vec b$ | `test_formula_single_ell` analytic cross-check |
| CN formula $(I - \frac{h}{2}A)\Theta' = (I + \frac{h}{2}A)\Theta + h\vec b$ | analytic cross-check |
| Exponential step exact for pure damping $\Theta(h) = e^{-\Gamma h}\Theta(0)$ | `test_exact_for_zero_source_pure_damping` |
| Exponential composition law $e^{A(2h)} = e^{Ah}\,e^{Ah}$ | `test_composition_law` to $10^{-15}$ |
| Exponential always stable; reaches $\Theta_\infty$ at $dt \to \infty$ | `test_always_stable_arbitrary_dt` at $dt = 10^{10}$ |
| BE always stable at $100 \times dt_{\rm CFL}$ | `test_always_stable` |
| At 10× CFL: explicit diverges to $10^{54}$, BE and EXP reach $\Theta_\infty$ | `TestStiffRegimeStability` 4 tests |
| CN 2nd-order convergence vs exponential | `test_second_order_accuracy` (err halving ≈ factor 4) |
| All 5 public entries gate on `CanonicalDecision` | 5 tests in `TestRuntimeGating` |
| Driver's analytic target matches `compute_steady_state_hierarchy` (W5-A) | `test_target_matches_compute_steady_state` |
| Input validation rejects dt≤0, ell mismatch, axis mismatch, tolerance≤0, max_steps<1 | 7 tests in `TestValidation` |
| No regression in 1,159 prior tests | 1,209/1,209 green |

### 6.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| Exponential integrator exactness | Holds exactly for linear time-invariant $A$. Breaks when $A$ becomes time-dependent (evolving $\Gamma(t)$ or $k(t)$). For slowly-varying $A$ the error is bounded by $O(h^2 \dot A)$; full nonlinear systems need Magnus expansion or exp-RK variants |
| CN A-stability | Not L-stable. In extremely stiff regimes CN does NOT damp high-frequency modes monotonically — use BE or EXP there |
| Linear-solve cost | $O(L^3)$ per step for BE/CN, $O((L+2)^3)$ for EXP. Fine for $L \lesssim 30$; for $L \sim 100$+ sparse/iterative solvers needed |
| Single-$k$ validation | Tests exercise single-Fourier-mode hierarchy. Full Bianchi I requires coupling across $m \neq 0$ channels (W5-C deferral) |

### 6.3 NOT ESTABLISHED

- Time-varying $A$ (Rodas5P or IMEX-ARK with changing $\Gamma$, $k$, $\sigma$) — W5-B extension
- Newton iteration for nonlinear implicit steps (no nonlinearity in current hierarchy)
- Krylov subspace methods for $e^{Ah}\vec v$ at large $L$ (W6+ scaling)
- Off-axis (m ≠ 0) couplings — W5-C

---

## §7 — Self-audit

| Check | Status |
|-------|--------|
| ASCII banners | ✅ |
| Banned vocab scan (module + test) | ✅ clean |
| Type hints on all public API | ✅ |
| Docstrings with explicit formulas + references | ✅ |
| All 5 entry points gate runtime | ✅ |
| Internal `_unchecked` helpers are `_`-prefixed and not re-exported | ✅ |
| Reuses W5-A types (no duplication) | ✅ |
| Tests: single-pass green, no debug iterations | ✅ 49/49 first run |
| Ownership freeze updated (BASS_MODULES + parametrized test) | ✅ |
| Cross-module consistency: BE/EXP steady state = W5-A linsolve target | ✅ |
| No cross-layer leakage | ✅ |
| Full-suite regression | ✅ 1,209/1,209 |

**P0 / P1 findings: 0 / 0.**

---

## §8 — API surface

```python
from bass.transport.implicit_hierarchy import (
    # Method selector
    ImplicitMethod,

    # Single-step functions (all gated)
    backward_euler_step,
    crank_nicolson_step,
    exponential_step,

    # Driver (dispatches on method enum, gated)
    integrate_implicit_to_steady_state,

    # Stability analysis (no gate — pure math)
    stability_function_ratio,
)

# Typical usage — pre-recombination with stiff τ̇
params = make_photon_hierarchy_parameters(
    n_e_sigmaT=1e4, shear=shear, k_eff=10.0, ell_max=10,
    decision=decision,
)
initial = zero_state(ell_max=10)
dt = cfl_max_dt(params) * 20   # 20× explicit's CFL bound is FINE for BE
result = integrate_implicit_to_steady_state(
    initial, params, dt=dt, decision=decision,
    method=ImplicitMethod.BACKWARD_EULER,
    max_steps=500, tolerance=1e-8,
)
# result.converged = True, result.final_state ≈ analytic target
```

---

## §9 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 49 (10 classes) + 1 ownership parametrized |
| Cumulative tests | **1,209** |
| Full-suite runtime | 54.52 s |
| New module LoC | ~340 |
| Stability verification at 10× CFL | explicit diverges ×$10^{54}$; BE, EXP err < $10^{-15}$ |
| BE stable at 100× CFL (30 steps) | finite, $\|\Theta\| < 10^{-5}$ |
| EXP convergence at 10× CFL | 2 steps |
| BE convergence at 10× CFL | 8–9 steps |
| CN 2nd-order error ratio at dt halving | ≈ 4× (consistent with $O(h^2)$) |
| Composition law precision | $10^{-15}$ (machine) |
| Gated entries | 5 |
| P0 / P1 | 0 / 0 |

---

## §10 — W5 progress snapshot

| Day | Deliverable | Δ tests | Cumulative |
|-----|-------------|---------|------------|
| W5-A | `multipole_hierarchy.py` — multi-ℓ explicit | +65 | 1,159 |
| **W5-B** | **`implicit_hierarchy.py` — 3 implicit integrators** | **+50** | **1,209** |
| W5-C (proposed) | Full Bianchi I (off-axis m ≠ 0) | — | → ~1,310 |
| W5-D (proposed) | HEALPix bridge | — | → ~1,260 |
| W5-E (proposed) | Production Gram application | — | → ~1,250 |

---

## §11 — Next action

Suggested W5-C: **Full Bianchi I off-axis (m ≠ 0) extension**.

### 11.1 Motivation

Current hierarchy restricts to $m = 0$ (axisymmetric projection onto a single symmetry axis). Full Bianchi I shear has three eigenvalues:
$$\sigma_{xx}, \sigma_{yy}, \sigma_{zz} \quad \text{with } \sigma_{xx} + \sigma_{yy} + \sigma_{zz} = 0$$

The general case is **axisymmetric only when two eigenvalues are equal**. For the general anisotropic Bianchi I background, the shear source couples to $m \in \{-2, -1, 0, +1, +2\}$ channels of each $\ell$. This is required for the full thesis Bianchi evaluation.

### 11.2 Scope estimate

- New module: `bass/transport/bianchi_i_hierarchy.py` with full-$(\ell, m)$ state
- Shear tensor representation lifted from `AxisymmetricSTFTensor` to a new `DiagonalShearTensor` with three eigenvalues
- $(\ell, m)$ streaming matrix with $m$-channel mixing
- Cross-validation: at $\sigma_{xx} = \sigma_{yy}$, results reduce to current axisymmetric bit-exact
- Target: ~100 tests, cumulative ~1,310

### 11.3 Alternative: W5-E (shorter, production-oriented)

If preferring to consolidate: **Production Gram application** — connect `entropy_invariants.py` (W4D5) to a real Teff production pipeline Gram matrix for first end-to-end validation of the admissibility diagnostic on live data. 2–3 days, ~40 tests.

---

**End of W5-B packet. Awaiting approval for W5-C (off-axis Bianchi I) or alternative selection.**
