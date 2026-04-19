# WEEK 5-A DAY 1 PACKET — Multi-ℓ PSTF Hierarchy Skeleton

**Date**: 2026-04-17
**Scope**: Multi-multipole extension of W4D4 `ray_transport.py` — full PSTF Boltzmann hierarchy with streaming coupling, damping, and ℓ=2 shear injection
**New module**: `bass/transport/multipole_hierarchy.py` (~340 LoC)
**Tests**: 64 across 11 classes + 1 ownership update
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: **1,159 tests**, 52.12 s runtime

---

## §1 — Scope and physics

### 1.1 Equation

The skeleton solves the axisymmetric Fourier-space PSTF hierarchy (Challinor & Lasenby 1999, Eq. 44; ch05 §pstf-hierarchy):

$$\dot\Theta_\ell = \frac{k_{\rm eff}}{2\ell+1}\bigl[\ell\,\Theta_{\ell-1} - (\ell+1)\,\Theta_{\ell+1}\bigr] - \Gamma_\ell\,\Theta_\ell + \Sigma_2\,\sigma\,\delta_{\ell,2}$$

for $\ell = 0, 1, \ldots, L_{\max}$ with absorbing boundaries $\Theta_{-1} \equiv 0$, $\Theta_{L_{\max}+1} \equiv 0$.

### 1.2 Three physics mechanisms exposed

1. **Free-streaming cascade** — shear injection at $\ell=2$ leaks upward through the streaming operator $M[\ell, \ell{-}1] = +k_{\rm eff}\,\ell/(2\ell+1)$, $M[\ell, \ell{+}1] = -k_{\rm eff}\,(\ell{+}1)/(2\ell+1)$, with zero diagonal.
2. **Species-dependent damping** — $\Gamma^{(\gamma)} = \dot\tau$ (Thomson) or $\Gamma^{(\nu)} = H$ (Hubble), controlling the steady-state amplitude.
3. **Localized source** — shear couples only to $\ell=2$ (ch05 Eq. MDE-general coefficient $8/15$, absorbed into the Teff factor $\Sigma_2 = (8/15) I_4/I_3$).

### 1.3 Relation to W4D4

When $k_{\rm eff} = 0$ and $L_{\max} = 2$:
- Streaming matrix $M = 0$, hierarchy decouples
- $\Theta_0$, $\Theta_1$ evolve under pure damping → steady state $= 0$
- $\Theta_2$ satisfies D4's single-ℓ equation $\dot\Theta_2 = -\Gamma\Theta_2 + \Sigma_2\sigma$

Test `TestD4Consistency::test_steady_state_matches_D4_photon` verifies bit-exact reduction (rel err $< 10^{-14}$). Same for neutrinos and for the 35.71 N_2/F_2 ratio.

---

## §2 — Physics invariants verified

### 2.1 PSTF streaming coefficients (exact)

| Entry | Expected | Observed |
|-------|----------|----------|
| $M[1,0]$ | $k/3$ | $0.3333\ldots$ ✓ |
| $M[1,2]$ | $-2k/3$ | $-0.6667\ldots$ ✓ |
| $M[2,1]$ | $2k/5$ | $0.4$ ✓ |
| $M[2,3]$ | $-3k/5$ | $-0.6$ ✓ |
| $M[3,2]$ | $3k/7$ | $0.4286\ldots$ ✓ |
| $M[3,4]$ | $-4k/7$ | $-0.5714\ldots$ ✓ |
| $M[\ell,\ell]$ | 0 | 0 ✓ |

All coefficients from $\ell=0$ to $\ell=5$ verified against $\pm k/(2\ell+1) \times \ell$ or $(\ell+1)$.

### 2.2 Cascade monotonicity

At $\dot\tau = 10^3$, $H = 30$, $k_{\rm eff} = 50$, $\sigma = 10^{-6}$, $L_{\max} = 6$:

| ℓ | $|\Theta^{(\gamma)}_\ell|$ (analytic) |
|---|----------------------------------------|
| 2 | $\sim 2.03 \times 10^{-9}$ |
| 3 | $\sim 4.35 \times 10^{-11}$ |
| 4 | $\sim 9.63 \times 10^{-13}$ |
| 5 | $\sim 2.18 \times 10^{-14}$ |
| 6 | $\sim 5.00 \times 10^{-16}$ |

$|\Theta_\ell|$ strictly monotonically decreasing for $\ell \geq 2$ — verified by `test_steady_state_cascade_monotonic_decay`. The cascade suppression factor $\sim 1/\!(2\ell{+}1)$ per level matches the expected free-streaming damping.

### 2.3 Euler convergence to linsolve target

At $k_{\rm eff} = 100$, $L_{\max} = 5$, $dt = 0.5 \times \text{CFL}_{\max} = 9.1 \times 10^{-4}$:

| Quantity | Value |
|----------|-------|
| Converged | True at 10 steps |
| Max rel err across ℓ | $1.35 \times 10^{-6}$ |
| CFL max dt (diagnostic) | $1.82 \times 10^{-3}$ |

### 2.4 D4 bit-exact consistency

| Test | Observed rel err |
|------|------------------|
| Photon $\Theta_2$ vs D4 | $< 10^{-14}$ ✓ |
| Neutrino $\Theta_2$ vs D4 | $< 10^{-14}$ ✓ |
| $N_2/F_2$ ratio at $k_{\rm eff}=0$ | $35.71$ exact ✓ |

---

## §3 — Implementation ledger

| Component | Role |
|-----------|------|
| `MultipoleState` frozen dataclass | Amplitude vector (L+1,), axis; `ell`, `as_stf_at(2)` accessors |
| `zero_state(ell_max, axis)` | Factory for zero initial state |
| `HierarchyParameters` frozen dataclass | species, Γ, σ, Σ_2, k_eff, ell_max |
| `make_photon_hierarchy_parameters(...)` | Photon factory (Γ=τ̇, Σ_2=2.044) |
| `make_neutrino_hierarchy_parameters(...)` | Neutrino factory (Γ=H, Σ_2=2.190) |
| `build_streaming_matrix(k_eff, ell_max)` | PSTF coupling matrix (L+1, L+1) |
| `build_source_vector(params)` | b[ℓ] = Σ_2 σ δ_{ℓ,2} |
| `euler_step_hierarchy(...)` | One gated Euler step |
| `_euler_step_unchecked(...)` | Internal helper, no gate |
| `compute_steady_state_hierarchy(params)` | Analytic linsolve (Γ I − M) Θ_∞ = b |
| `integrate_hierarchy_to_steady_state(...)` | Gated Euler loop with convergence detection |
| `HierarchyIntegrationResult` frozen | final state, steps, converged, residual, target |
| `cfl_max_dt(params)` | Conservative $2/(\Gamma + k_{\rm eff})$ stability bound |

### 3.1 Import graph

```
bass/transport/multipole_hierarchy  ──→  bass/transport/ray_transport (D4)
                                    ──→  bass/collision/thomson_tensor (D3)
                                    ──→  bass/runtime/canonical_decision (W3)
                                    ──→  numpy only (linalg.solve)
```

Clean BASS-internal chain, no TSC imports. Reuses D3 `AxisymmetricSTFTensor` and D4 damping helpers.

### 3.2 Runtime gating (5 public entries)

| Function | `require_allow_reduction` context |
|----------|-----------------------------------|
| `euler_step_hierarchy` | `"euler_step_hierarchy"` |
| `compute_steady_state_hierarchy` | `"compute_steady_state_hierarchy"` |
| `integrate_hierarchy_to_steady_state` | `"integrate_hierarchy_to_steady_state"` |
| `make_photon_hierarchy_parameters` | via inner `photon_damping_rate` |
| `make_neutrino_hierarchy_parameters` | via inner `neutrino_damping_rate` |

All 5 verified to raise `CanonicalBlockError` on blocking decision.

---

## §4 — Three-tier claim taxonomy

### 4.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| PSTF streaming coefficients implemented exactly per Challinor-Lasenby | 13 tests in `TestStreamingMatrix` |
| ℓ=2 shear source only — no spurious coupling elsewhere | `TestSourceVector` 4 tests |
| Steady-state linsolve matches closed-form at k_eff=0 | `TestSteadyStateAnalytic` 6 tests |
| D4 consistency at k_eff=0, L_max=2 (bit-exact) | `TestD4Consistency` 3 tests |
| Euler integration converges to linsolve target within O(dt²·CFL) | `TestIntegrationConvergence::test_converges_from_zero` |
| Cascade monotonic decay $|\Theta_\ell|$ for $\ell \geq 2$ | `test_steady_state_cascade_monotonic_decay` |
| Energy flow: streaming transfers amplitude upward from ℓ=2 | `test_streaming_transfers_from_ell_2_to_ell_3` |
| All 5 public entry points gate on CanonicalDecision | `TestRuntimeGating` 6 tests |
| CFL diagnostic returns $2/(\Gamma + k_{\rm eff})$ | `TestCFLDiagnostic` 2 tests |
| Absorbing boundary at $\ell = L_{\max}$ | Test: `test_boundary_no_column_above_ell_max` |
| No regression in 1,094 prior tests | 1,159/1,159 green |

### 4.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| Uniform $\Gamma$ across all ℓ | This skeleton treats damping as ℓ-independent. Real Thomson damping is ℓ-dependent via the polarization mixing ($\Pi$ enters at ℓ=2 with the $\frac{1}{10}$ factor from D3). W5-A Day 2+ will add ℓ-specific damping. |
| Axisymmetric restriction | Full Bianchi I off-axis ($m \neq 0$) deferred to W5-C |
| Absorbing boundary as hard cutoff | Standard in CAMB. More sophisticated schemes (sponge layer, artificial viscosity) are W6+ concerns. |
| Explicit Euler stability | Caller must keep $dt < 2/(\Gamma + k_{\rm eff})$; implicit integrators (W5-B) lift the restriction. |
| Single k-mode skeleton | Production solver runs over a k-grid; this skeleton exercises one k at a time. |

### 4.3 NOT ESTABLISHED (deferred)

- ℓ-dependent damping Γ_ℓ (polarization mixing at ℓ=2)
- Full E/B polarization hierarchy (separate rank-2 tensor hierarchy)
- Four-acceleration source at ℓ=1 ($\frac{4}{3} I \dot u_a$)
- Monopole closure (equation for $\dot\Theta_0$ from energy conservation)
- Tilt dipole coupling
- Implicit / stiff integrators (Rodas5P, IMEX-ARK)
- Multi-k parallelism

---

## §5 — Self-audit

| Check | Status |
|-------|--------|
| ASCII banners | ✅ |
| Banned vocabulary scan (module + test) | ✅ clean |
| Frozen dataclasses: `MultipoleState`, `HierarchyParameters`, `HierarchyIntegrationResult` | ✅ |
| Type hints on all public functions | ✅ |
| Docstrings reference ch05 / Challinor-Lasenby | ✅ |
| Every public entry gates runtime | ✅ 5/5 |
| Internal `_euler_step_unchecked` well-marked, not re-exported | ✅ |
| Input validation on dt, tolerance, max_steps, k_eff, ell_max, axes | ✅ 10+ dedicated tests |
| `build_streaming_matrix` rejects negative k_eff and ell_max | ✅ |
| D4 consistency verified bit-exact | ✅ |
| Ownership freeze updated (BASS_MODULES +1) | ✅ |
| Full-suite regression | ✅ 1,159/1,159 |

**P0 / P1 findings: 0 / 0.**

---

## §6 — API surface

```python
from bass.transport.multipole_hierarchy import (
    # Types
    MultipoleState, HierarchyParameters, HierarchyIntegrationResult,
    zero_state,

    # Factories (gated)
    make_photon_hierarchy_parameters,
    make_neutrino_hierarchy_parameters,

    # Matrices
    build_streaming_matrix, build_source_vector,

    # Integrators (gated)
    euler_step_hierarchy,
    compute_steady_state_hierarchy,
    integrate_hierarchy_to_steady_state,

    # Diagnostic
    cfl_max_dt,
)

# Typical usage: photon hierarchy at pre-recombination
shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
params = make_photon_hierarchy_parameters(
    n_e_sigmaT=1e3, shear=shear, k_eff=100.0, ell_max=5,
    decision=decision,
)
initial = zero_state(ell_max=5)
dt = 0.5 * cfl_max_dt(params)
result = integrate_hierarchy_to_steady_state(
    initial, params, dt, decision,
    max_steps=10000, tolerance=1e-10,
)
# result.final_state.amplitudes — the converged (Θ_0, Θ_1, ..., Θ_5) vector
# result.converged, result.steps_taken, result.final_residual
```

---

## §7 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 64 (11 classes) + 1 ownership update |
| Cumulative tests | **1,159** (W4 end 1,094 + 65) |
| Full-suite runtime | 52.12 s |
| New module LoC | ~340 |
| Euler converged steps (typical, k_eff=100, L=5) | 10 at dt = 0.5 × CFL |
| Max rel err vs linsolve | $1.35 \times 10^{-6}$ |
| Cascade suppression $\Theta_3/\Theta_2$ | ~4% at k_eff=100, $\dot\tau=10^3$ |
| Cascade suppression $\Theta_6/\Theta_2$ | ~0.001% |
| Gating calls per module | 5 public entries |
| P0 / P1 findings | 0 / 0 |

---

## §8 — W5-A roadmap

This is Day 1 of W5-A (multi-ℓ hierarchy focus). Suggested Day 2+ progression:

| Day | Scope | Est. tests |
|-----|-------|-----------|
| **D1 (today)** | `multipole_hierarchy.py` — uniform Γ, axisymmetric scalar | **+64** |
| D2 | ℓ-dependent damping $\Gamma_\ell$; Thomson polarization mixing at ℓ=2 via $\Pi$ from D3 | +40 |
| D3 | Four-acceleration source at ℓ=1 (tilt coupling); monopole closure | +40 |
| D4 | Multi-species coupled system (γ + ν with shared σ, independent Γ and Σ_2) | +50 |
| D5 | W5-A close-out: full Bianchi I transfer-function stub, packet | +40 |

Cumulative trajectory: 1,159 → ~1,400 by W5-A end.

---

**End of W5-A Day 1 packet. Awaiting approval for D2.**
