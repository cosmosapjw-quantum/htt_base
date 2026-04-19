# WEEK 4 DAY 4 PACKET — Ray Transport Axisymmetric Skeleton

**Date**: 2026-04-17
**Scope**: Free-streaming ℓ=2 transport equation for photon (collision-coupled) and neutrino (collision-free) quadrupoles, with W3 runtime gating on every public entry
**New module**: `bass/transport/ray_transport.py` (~340 LoC)
**Tests**: 52 across 10 classes + 1 ownership update
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 1,010 tests (first 4-digit milestone), 53.41 s runtime

---

## §1 — Scope and relation to D3

D3 built the **collision source** (Thomson tensor). D4 builds the **transport equation** that the collision source enters as an inhomogeneous driver. Together they form the single-multipole building block of the full Bianchi Boltzmann hierarchy.

The transport equation is single-species, single-multipole (ℓ=2), axisymmetric:

$$\dot\Theta^{(s)}_{ab} + \Gamma^{(s)}\,\Theta^{(s)}_{ab} = \Sigma^{(s)}_2\,\sigma_{ab} + O(\ell=4)$$

with species-dependent damping rate:

- **Photon** (collision-coupled): $\Gamma^{(\gamma)} = \dot\tau$ — Thomson damping from D3
- **Neutrino** (collision-free): $\Gamma^{(\nu)} \sim H$ — Hubble damping only

Σ²_s encodes species spectral stiffness:

- $\Sigma^{(\gamma)}_2 \approx 2.044$ (BE, η=0) — reused from D3
- $\Sigma^{(\nu)}_2 \approx 2.190$ (FD, η=0) — new constant

The $O(\ell=4)$ leakage is absorbed at the absorbing boundary; this skeleton truncates at ℓ=2.

---

## §2 — Physical verification of key invariants

### 2.1 Neutrino dominance (N_2/F_2 ratio) — ch05 §nu-dominance

Scalar analog of the full ch05 result $N_2/F_2 \simeq \dot\tau/H$ at recombination:

$$\frac{N_2}{F_2} = \frac{\Theta^{(\nu)}_\infty}{\Theta^{(\gamma)}_\infty} = \frac{\Sigma^{(\nu)}_2}{\Sigma^{(\gamma)}_2} \cdot \frac{\dot\tau}{H}$$

Smoke test at $\dot\tau = 10^3$, $H = 30$, $\sigma = 10^{-6}$:

| Quantity | Observed | Expected |
|----------|----------|----------|
| $\Theta^{(\gamma)}_\infty$ | $2.044 \times 10^{-9}$ | $\Sigma^{(\gamma)}_2 \sigma / \dot\tau = 2.044\times10^{-9}$ ✓ |
| $\Theta^{(\nu)}_\infty$ | $7.300 \times 10^{-8}$ | $\Sigma^{(\nu)}_2 \sigma / H = 7.300\times10^{-8}$ ✓ |
| **$N_2/F_2$ ratio** | **35.71** | $1.07 \times 33.3 = 35.71$ ✓ |

The numerical ratio matches $(\Sigma_\nu/\Sigma_\gamma) \times (\dot\tau/H)$ bit-exactly, confirming the ch05 physical mechanism (Thomson suppression of photon quadrupole vs. free-streaming neutrino accumulation).

### 2.2 D3 cross-validation

$$\texttt{compute\_steady\_state(photon\_params)} = \texttt{compute\_quasi\_static\_theta(shear, }\dot\tau)$$

Both modules must produce bit-identical photon quasi-static amplitudes for the same inputs. Verified in `test_photon_steady_reproduces_D3_quasi_static`.

### 2.3 Euler convergence to analytic steady state

Zero initial → steady state via Euler integration (1e-4 dt, tolerance 1e-8):

| Quantity | Observed |
|----------|----------|
| Converged | True |
| Steps | 154 |
| Final amplitude | $2.0439 \times 10^{-9}$ |
| Target amplitude | $2.0439 \times 10^{-9}$ |
| rel err vs target | $8.98 \times 10^{-8}$ |

### 2.4 Free-streaming decay

Analytic $\Theta(t) = \Theta_0\,e^{-\Gamma t}$ at zero source. Numerical Euler at $dt=10^{-3}$, $\Gamma=1$, $t=1$:

- Numerical: $\Theta(1) = 0.3677$
- Analytic: $e^{-1} = 0.3679$
- Rel err: $5 \times 10^{-4}$, matching expected $O(dt) \approx dt/2$ Euler truncation

---

## §3 — Implementation ledger

| Component | Role |
|-----------|------|
| `TransportSpecies` enum | PHOTON / NEUTRINO |
| `SIGMA_2_NEUTRINO_FD` | 2.190 (FD at η=0) |
| `photon_damping_rate(n_e σ_T)` | returns τ̇ (gated) |
| `neutrino_damping_rate(H)` | returns H (gated) |
| `species_shear_coefficient(species)` | default Σ_2 per species |
| `TransportParameters` frozen dataclass | species, Γ, Σ_2, σ |
| `make_photon_parameters(τ̇, σ)` | factory with default Σ_2 |
| `make_neutrino_parameters(H, σ)` | factory with default Σ_2 |
| `euler_step(θ, params, dt)` | one explicit Euler step (gated) |
| `_euler_step_unchecked(...)` | internal helper, bypasses gate (used inside loops) |
| `compute_steady_state(params)` | analytic Θ_∞ = Σ_2 σ / Γ (gated) |
| `integrate_to_steady_state(...)` | Euler loop with convergence detection (gated once) |
| `IntegrationResult` frozen dataclass | final state, steps, converged, residual, target |
| `free_streaming_decay_factor(Γ, t)` | exp(-Γt) (no gate, pure math helper) |

### 3.1 Internal optimization — private un-gated helper

`integrate_to_steady_state` gates at entry, then calls `_euler_step_unchecked(...)` internally. This avoids redundant gate checks across thousands of loop iterations while preserving the contract: if a caller drives the Euler step directly through `euler_step`, the gate enforces per-call. The un-gated helper is `_`-prefixed and never imported outside the module.

### 3.2 Import graph

```
bass/transport/ray_transport  ──→  bass/collision/thomson_tensor
                               ──→  bass/runtime/canonical_decision
                               ──→  stdlib only (math, enum, dataclasses)
```

Clean BASS-internal chain. No TSC imports. Verified by `test_ownership_freeze`.

---

## §4 — Three-tier claim taxonomy

### 4.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| Euler step formula $\Theta^{n+1} = \Theta^n + dt(-\Gamma\Theta^n + \Sigma_2\sigma)$ | `test_bit_exact_formula` with explicit rel err $< 10^{-14}$ |
| Species damping mapping: $\Gamma^{(\gamma)} = \dot\tau$, $\Gamma^{(\nu)} = H$ | 5 tests in `TestDampingRateHelpers` |
| Σ_2 values: photon 2.044 (BE), neutrino 2.190 (FD); ratio 1.07 | 4 tests in `TestSigmaCoefficients` |
| Photon steady state = D3 quasi-static (bit-exact) | `test_photon_steady_reproduces_D3_quasi_static` |
| Euler integration converges to analytic target within O(dt) | `test_euler_converged_within_O_dt_of_analytic` |
| N_2/F_2 ratio = (Σ_ν/Σ_γ)(τ̇/H) | `test_neutrino_photon_amplitude_ratio_follows_gamma_ratio` |
| All 5 public entry points gate on `CanonicalDecision` | 6 tests in `TestRuntimeGating` |
| `CanonicalBlockError` carries full decision | `test_blocked_error_carries_decision` |
| Free-streaming decay matches exp(-Γt) to Euler O(dt) | 5 tests in `TestFreeStreamingDecay` |
| Sign convention: damping decreases Θ, source grows Θ | 2 dedicated tests |
| Axis preservation across all arithmetic and integration | 4 tests across classes |
| Input validation on all numerical parameters | 10 dedicated validation tests |
| No regression in 957 prior tests | 1,010/1,010 green |

### 4.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| Explicit Euler stability | Requires $dt < 2/\Gamma$ for the damping term. Not enforced at module boundary — caller's responsibility. Documented in `euler_step` docstring. Production solver uses implicit methods (W5+). |
| Single-ℓ truncation | Valid only when the $O(\ell=4)$ leakage is absorbed. The absorbing boundary condition is a W5+ module. Current truncation captures the primary shear-driven amplitude but drops streaming-cascade tail. |
| Axisymmetric approximation | Adequate for Bianchi I with aligned shear; off-axis shear components deferred to full Bianchi implementation (W5+). |
| Frozen-background σ | Valid on timescales $\Delta t \ll 1/(\dot\sigma/\sigma)$. Production cosmological evolution requires time-varying σ; this skeleton holds σ constant over each `integrate_to_steady_state` call. |

### 4.3 NOT ESTABLISHED (deferred)

- Multi-ℓ hierarchy (streaming cascade $D^b\,\Theta_{bA_\ell}$)
- E ↔ B mixing through free-streaming operator
- Nonlinear Θ⁴ bridge coupling
- Off-axis tensor components
- Higher-order time integrators (W5+ uses Rodas5P or IMEX-ARK)
- Tight-coupling approximation (TCA) — separate concern; CAMB mapping doc covers

---

## §5 — Self-audit (PHYS-MATH-CODE)

| Check | Status |
|-------|--------|
| ASCII banners | ✅ |
| Banned vocabulary (module + test) | ✅ clean |
| Frozen dataclasses for `TransportParameters`, `IntegrationResult` | ✅ |
| Type hints on all public functions | ✅ |
| Docstrings cite primary references (ch05 Eq. references) | ✅ |
| Every public function gates runtime | ✅ 5/5 |
| Internal `_euler_step_unchecked` well-marked | ✅ |
| Private helper does NOT escape module | ✅ not re-exported |
| Input validation on dt, tolerance, max_steps, damping, shear_coefficient | ✅ |
| No cross-layer leakage (TSC import) | ✅ enforced by ownership_freeze |
| Ownership freeze updated with new module | ✅ 1 parametrized test added |
| Full-suite regression | ✅ 1,010/1,010 |

**P0 / P1 findings: 0 / 0.**

---

## §6 — API surface

```python
from bass.transport.ray_transport import (
    # Enum
    TransportSpecies,

    # Species coefficients
    SIGMA_2_NEUTRINO_FD,
    species_shear_coefficient,

    # Damping rates (gated)
    photon_damping_rate,
    neutrino_damping_rate,

    # Parameter container
    TransportParameters,
    make_photon_parameters,
    make_neutrino_parameters,

    # Integrators (gated)
    euler_step,
    compute_steady_state,
    integrate_to_steady_state,
    IntegrationResult,

    # Pure helper
    free_streaming_decay_factor,
)

# Typical usage
shear = AxisymmetricSTFTensor(amplitude=1e-6, axis=SymmetryAxis.Z)
params = make_photon_parameters(
    n_e_sigmaT=1e3, shear=shear, decision=decision,
)
initial = AxisymmetricSTFTensor(amplitude=0.0, axis=SymmetryAxis.Z)
result = integrate_to_steady_state(
    initial=initial, params=params, dt=1e-4, decision=decision,
    max_steps=5000, tolerance=1e-8,
)
# result.final_state.amplitude ≈ 2.044e-9  (matches D3 quasi-static)
# result.converged is True in ~154 steps
```

---

## §7 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 52 (10 classes) + 1 ownership update |
| Cumulative tests | **1,010** (first 4-digit milestone) |
| Full-suite runtime | 53.41 s |
| New module LoC | ~340 |
| $\Sigma^{(\nu)}_2$ FD | 2.190 |
| $\Sigma_\nu / \Sigma_\gamma$ | 1.0714 (7% species independence, ch05 §nu-dominance) |
| Euler convergence steps (typical) | 154 at dt = 1e-4, tolerance 1e-8 |
| Free-streaming decay rel err | $5 \times 10^{-4}$ at dt = $10^{-3}$ (O(dt)) |
| Gating calls per module | 5 public entries |
| P0 / P1 findings | 0 / 0 |

---

## §8 — W4 progress snapshot

| Day | Deliverable | Δ tests | Cumulative |
|-----|-------------|---------|------------|
| D1 | `planck_mes_bounds.py` | +47 | 867 |
| D2 | `beta_threshold.py` + Pastén Option B artifacts | +37 | 904 |
| D3 | `thomson_tensor.py` (first W3 consumer) | +53 | 957 |
| **D4** | **`ray_transport.py` (Euler transport skeleton)** | **+53** | **1,010** |
| D5 | `entropy_invariants.py` + `spherical_quadrature.py` + P2-W4-01 | — | → ~1,070+ |

W4 end target was ~1000 by D5; we crossed it one day early.

---

## §9 — Next action (W4D5 — entropy invariants + Lebedev + P2-W4-01)

D5 scope per v4.1 MERGED §4.3:

### 9.1 `tsc/diagnostics/entropy_invariants.py` (~~150 LoC, ~20 tests)

Paper I Thm 9/10/11 entropy invariants — scalar diagnostics on the exponential-family chart:

- Thm 9: entropy-density relation $s/n$ vs $I_n$ moments
- Thm 10: admissibility invariant via Gram eigenvalue bounds
- Thm 11: η-independence of bolometric quantities at $\eta \le 0$

These are **pure TSC diagnostics** (no gating, no runtime coupling). Role: extend the L0 precision dashboard with additional oracle cross-checks.

### 9.2 `tsc/diagnostics/spherical_quadrature.py` (~~200 LoC, ~25 tests)

Lebedev quadrature on $S^2$ — discrete sphere integration for pixel-space source assembly:

- Core Lebedev node / weight tables (degrees 3, 5, 7, 9, 11, 15, 23)
- Spherical polynomial integration exactness verification
- Future use: angular source assembly, HEALPix connection (W6+)

### 9.3 P2-W4-01 refactor

Extract Prop 5 boost coefficients from `bass/validation/channel_routing.py` into
new `tsc/charts/boost_coefficients.py` — resolves the lone ownership_freeze
whitelist entry.

Target: ~50 new tests, cumulative ~1,060+.

---

**End of W4D4 packet. Awaiting approval for D5 (W4 close-out).**
