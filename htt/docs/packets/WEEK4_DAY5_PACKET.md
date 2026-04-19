# WEEK 4 DAY 5 PACKET — W4 Close-Out

**Date**: 2026-04-17
**Scope**: Three deliverables closing W4 — Lebedev quadrature, entropy invariants, and P2-W4-01 refactor
**New modules**: 3 (`tsc/diagnostics/spherical_quadrature.py`, `tsc/diagnostics/entropy_invariants.py`, `tsc/charts/boost_coefficients.py`)
**Tests**: 54 + 27 + 3 ownership = 84
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: **1,094 tests**, 51.73 s runtime
**Ticket retired**: P2-W4-01 (whitelist exception cleared)

---

## §1 — Part 1: Lebedev spherical quadrature

### 1.1 Scope

Discrete-node quadrature on $S^2$ for angular integration. Orders 3 (6 nodes), 5 (14 nodes), and 7 (26 nodes) — the octahedral-symmetry sub-tables of the full Lebedev family. All weights $w_i > 0$, $\sum w_i = 1$ exactly. All nodes on the unit sphere to machine precision.

### 1.2 Physical verification

**Spherical-harmonic exactness** (scipy `sph_harm_y` reference):

| Order | Exact up to | ℓ = order + 1 |
|-------|-------------|-------------|
| 3 | ℓ ≤ 3 | noticeable error at ℓ = 4 |
| 5 | ℓ ≤ 5 | noticeable error at ℓ = 6 (err > 0.01) |
| 7 | ℓ ≤ 7 | noticeable error at ℓ = 8 (err > 0.1) |

All $Y_\ell^0$ with $\ell \leq \text{order}$ integrate to their analytic values with err $< 10^{-12}$ (typically $\sim 10^{-17}$).

**Monomial exactness** — analytic formula $\langle x^a y^b z^c \rangle_{S^2} = [(a-1)!!(b-1)!!(c-1)!!] / (a+b+c+1)!!$ for even $(a,b,c)$, zero otherwise. All degree-≤5 monomials under order-5 rule pass. Octahedral permutation symmetry verified: $\langle x^2 y^2 \rangle = \langle y^2 z^2 \rangle = \langle x^2 z^2 \rangle$ bit-exact.

### 1.3 API

```python
q = lebedev_quadrature(5)           # LebedevQuadrature(order, nodes (N,3), weights (N,))
result = integrate_on_sphere(f, q)   # callable API
result = integrate_vectorized(f_vals, q)  # pre-evaluated values
passes, err = verify_spherical_harmonic_exactness(q, ell)
passes, obs, exp = verify_monomial_integration(q, (a, b, c))
```

No gating. Pure TSC arithmetic.

### 1.4 Deliverable ledger

| Item | Value |
|------|-------|
| Module | `tsc/diagnostics/spherical_quadrature.py` (~230 LoC) |
| Tests | 54 across 6 classes |
| Supported orders | {3, 5, 7} (next available 9, 11, 15, 23 — W5+) |
| scipy API | `sph_harm_y(n, m, theta_polar, phi_azim)` (new convention) |

### 1.5 Bug caught during smoke test

Initial octahedral weight for order 5 was set to $1/30$ (incorrect). Correct value is $1/15$ — verified against standard Lebedev 14-node rule ($6 \times 1/15 = 2/5$, $8 \times 3/40 = 3/5$, sum = 1). Fixed in `_lebedev_order_5()`. All 5 order-5 exactness tests then passed.

---

## §2 — Part 2: Entropy invariants

### 2.1 Scope

Three scalar diagnostics on the exponential-family chart:

1. **Entropy-density / number-density ratio**: $s/n = I_3/I_2 + 1 - \eta$
2. **Gram-matrix admissibility**: $\lambda_{\min}, \lambda_{\max}, \kappa$ of a Gram matrix with threshold admissibility test
3. **MB η-independence**: for Maxwell-Boltzmann $I_n(\xi=0, \eta) = e^\eta\,n!$, so all moment ratios $I_{n_1}/I_{n_2}$ are exactly $\eta$-independent

### 2.2 Numerical verification

**$s/n$ values at $\eta = 0$**:

| Statistics | $s/n$ | Formula check |
|------------|-------|---------------|
| MB (ξ=0) | $4.000000$ | $I_3/I_2 = 6/2 = 3$, $+1 = 4$ ✓ |
| BE (ξ=+1) | $3.701178$ | $I_3/I_2 = 6.494/2.404 = 2.701$ |
| FD (ξ=−1) | $4.151374$ | $I_3/I_2 = 5.682/1.803 = 3.151$ |

MB $\eta$ shift: $s/n(\text{MB}, \eta = -1) = 5.0$, $s/n(\text{MB}, \eta = -2) = 6.0$ — linear in $-\eta$ as predicted.

**Gram admissibility**: symmetric matrix $[[2,1],[1,2]]$ has eigenvalues $\{1, 3\}$, $\kappa = 3$. Singular $[[1,1],[1,1]]$ has $\lambda_{\min} = 0$, correctly flagged as not admissible.

**MB η-independence**: max deviation across $\eta \in \{-5, -2, -1, 0, 1, 2, 5\}$ for pairs $\{(3,2), (4,3), (4,2), (5,2)\}$ is **$1.78 \times 10^{-15}$** (machine precision). Ratios at $\eta = 0$ are exactly $3, 4, 12$ as expected.

### 2.3 Theorem-label note (CONDITIONAL)

The D4 packet described D5 Part 2 as "Paper I Thm 9/10/11 entropy invariants". The project knowledge does not contain a numbered statement matching these exactly. The module covers the **substantive content** that is standard in exponential-family theory (entropy-density ratio, Gram positivity, MB η-independence), but the **theorem-label mapping** to specific numbered statements in Paper I is marked **CONDITIONAL**. The mathematical content is established from exponential-family identities (I_n integrals, Fisher information geometry); only the cross-reference to specific theorem numbers is unverified.

### 2.4 Deliverable ledger

| Item | Value |
|------|-------|
| Module | `tsc/diagnostics/entropy_invariants.py` (~170 LoC) |
| Tests | 27 across 5 classes |
| Admissibility threshold | $\lambda_{\min} > 10^{-14}$ |
| Max MB deviation | $1.78 \times 10^{-15}$ (machine precision) |

---

## §3 — Part 3: P2-W4-01 refactor (ticket closed)

### 3.1 Problem

Whitelist entry in `test_ownership_freeze.py::test_tsc_source_never_imports_bass_runtime_family`:

```python
KNOWN_EXCEPTIONS = {
    ("tsc/charts/boost_perturbative.py",
     "bass.validation.channel_routing"),
}
```

`tsc/charts/boost_perturbative.py` was importing Prop 5 boost coefficients from `bass/validation/channel_routing.py`. The coefficients physically belong to the TSC chart layer; their placement in bass/validation was a pre-v4.1 layout artifact.

### 3.2 Resolution

1. Created `tsc/charts/boost_coefficients.py` with the extracted definitions:
   - 3 constants: `PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE`, `PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE`, `PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE`
   - 3 functions: `boost_mixing_matrix`, `boost_additive_velocity_terms`, `apply_boost_to_teff`
2. `bass/validation/channel_routing.py` replaced inline definitions with a re-export block (6 symbols). The `bass → tsc` direction is architecturally permitted; only reverse (`tsc → bass/runtime, bass/tilt, bass/validation`) is enforced.
3. `tsc/charts/boost_perturbative.py` switched its import source from `bass.validation.channel_routing` to `tsc.charts.boost_coefficients`.
4. Removed the `KNOWN_EXCEPTIONS` dict entirely from `test_tsc_source_never_imports_bass_runtime_family` — test now runs with **zero whitelist exceptions**.
5. Added `tsc.charts.boost_coefficients` to the ownership-freeze `TSC_MODULES` parametrized import test.

### 3.3 Backward compatibility

All existing callers of `PROP5_COEFF_*`, `boost_mixing_matrix(...)`, `boost_additive_velocity_terms(...)`, `apply_boost_to_teff(...)` via `bass.validation.channel_routing` continue to work — the re-export preserves the public surface. Migration of callers to the new canonical source is optional but recommended for new code.

### 3.4 Verification

Running the full 1,094-test suite post-refactor shows **zero regressions**:

```
====================== 1094 passed, 7 warnings in 51.73s =======================
```

Specifically:
- Boost tests in `test_boost_perturbative.py` (previously importing via channel_routing) pass unchanged
- `test_tsc_source_never_imports_bass_runtime_family` now asserts empty offending list, which it does

---

## §4 — W4 retrospective

### 4.1 Day-by-day Δ

| Day | Deliverable | Δ tests | Cumulative |
|-----|-------------|---------|------------|
| D1 | `planck_mes_bounds.py` — Pastén Option B MES bounds | +47 | 867 |
| D2 | `beta_threshold.py` + Pastén Option B artifacts | +37 | 904 |
| D3 | `thomson_tensor.py` — first real W3 runtime consumer | +53 | 957 |
| D4 | `ray_transport.py` — axisymmetric Euler transport | +53 | 1,010 |
| D5 | Lebedev + entropy invariants + P2-W4-01 refactor | +84 | **1,094** |
| **W4 total** | 5 new production modules + 2 reports + 1 refactor | **+274** | **from 820** |

### 4.2 New subpackages

| Subpackage | Introduced | Count after W4 |
|------------|------------|----------------|
| `bass/observational/` | D1 | 2 modules |
| `bass/collision/` | D3 | 1 module |

### 4.3 Architectural landmarks

| Milestone | Day | Significance |
|-----------|-----|--------------|
| First W3 runtime consumer | D3 | `thomson_tensor` proved `CanonicalDecision` contract works end-to-end in production; 3 entry points gate correctly |
| 1,000-test crossing | D4 | `ray_transport` put BASS-py into its first 4-digit cumulative test count |
| N_2/F_2 scalar analog | D4 | Bit-exact match to ch05 §nu-dominance mechanism; 35.71 observed = $(\Sigma_\nu/\Sigma_\gamma)(\dot\tau/H)$ expected |
| P2 whitelist zero | D5 | Ownership freeze now enforces a clean TSC ↛ bass/restricted boundary with zero exceptions |
| Lebedev for S² | D5 | Angular-quadrature infrastructure ready for HEALPix bridge and pixel-space source assembly (W6+) |

### 4.4 Physics invariants validated across W4

| Invariant | Day | Agreement |
|-----------|-----|-----------|
| Planck 2018 Commander MES bounds ($\varepsilon_2, \varepsilon_3$) reproduce documented values | D1 | <0.7% rel err |
| Production β = 1.36×10⁻³ against 5 Epsilon1Policy variants | D2 | 4/5 BLOCK, 1 PASS (illustrative) as expected |
| Thomson $C_{ab} = -\dot\tau(\Theta - \Pi/10)$ | D3 | bit-exact (rel err < 10⁻¹⁴) |
| Quasi-static $\Theta_\infty = \Sigma_2 \sigma / \dot\tau$ | D3, D4 | bit-exact (cross-module) |
| Neutrino dominance $N_2/F_2 = (\Sigma_\nu/\Sigma_\gamma)(\dot\tau/H)$ | D4 | 35.71 = 35.71 exact |
| Free-streaming Euler decay $\Theta(t) = \Theta_0 e^{-\Gamma t}$ | D4 | $O(dt)$ (5×10⁻⁴ at $dt = 10^{-3}$) |
| Lebedev S² quadrature Y_ℓ exactness | D5 | err < 10⁻¹² up to rule order |
| MB moment-ratio η-independence | D5 | max deviation 1.78×10⁻¹⁵ |

### 4.5 Tech debt retired

- **P2-W4-01**: TSC ↛ bass/validation whitelist exception — retired D5
- Test suite no longer contains any documented `KNOWN_EXCEPTIONS` entries

### 4.6 Runtime budget

Full suite: 51.73 s at 1,094 tests → **47.3 ms/test average**. Still well within the <100 ms/test threshold. No test exceeds 5 s individually.

---

## §5 — Three-tier claim taxonomy (consolidated W4)

### 5.1 ESTABLISHED (W4)

- Pastén Option B MES bounds reproduce Planck 2018 documented values
- VT-07 β threshold policy variants block production β at 156.6× margin under Planck constraints
- Thomson collision formula $C_{ab} = -\dot\tau(\Theta - \Pi/10)$ implemented bit-exact with STF projection
- Photon / neutrino $\Sigma_2$ coefficients match closed-form spectral integrals
- Ray-transport Euler integrator converges to analytic steady state within $O(dt)$
- N_2/F_2 scalar analog reproduces ch05 neutrino dominance mechanism
- Lebedev order-3/5/7 quadratures are polynomial-exact up to their rule order
- MB η-independence holds to machine precision across wide $\eta$ range
- Gram-matrix admissibility returns correct eigenvalue bounds (verified on identity, positive-definite, singular)
- `CanonicalDecision` enforcement is active at 8 public entry points across `thomson_tensor.py` (3) + `ray_transport.py` (5)
- Ownership freeze passes with **zero whitelist exceptions**

### 5.2 CONDITIONAL (W4)

- Paper I "Thm 9/10/11" theorem-label alignment (entropy_invariants module) — substance established; number mapping unverified
- Axisymmetric restriction — adequate for Bianchi I aligned shear; full Bianchi I deferred
- Frozen-background $\sigma$ in transport integration — valid on timescales short vs. shear evolution
- $c_\xi = 1$ default in E-mode Thomson source — linear-order Paper VI convention
- Explicit Euler stability — caller's responsibility to satisfy $dt < 2/\Gamma$

### 5.3 NOT ESTABLISHED (still deferred to W5+)

- Multi-ℓ hierarchy streaming cascade ($D^b \Theta_{bA_\ell}$)
- Off-axis ($m \neq 0$) tensor components
- E ↔ B mixing through free-streaming operator
- Nonlinear $\Theta^4$ bridge coupling into collision
- Implicit / higher-order time integrators (Rodas5P, IMEX-ARK)
- Lebedev orders above 7 (9, 11, 15, 23 — available on request)
- Tight-coupling approximation (TCA) as explicit stiffness resolution

---

## §6 — Self-audit (all W4D5 deliverables)

| Check | Part 1 | Part 2 | Part 3 |
|-------|--------|--------|--------|
| ASCII banners | ✅ | ✅ | ✅ |
| Banned vocabulary scan | ✅ | ✅ | ✅ |
| Frozen dataclasses | ✅ (`LebedevQuadrature`) | ✅ (`GramAdmissibility`, `MBIndependenceResult`) | — |
| Type hints on public API | ✅ | ✅ | ✅ |
| Docstrings with mathematical statements | ✅ | ✅ | ✅ |
| Input validation | ✅ (4 dedicated tests) | ✅ (3 dedicated tests) | — (re-export only) |
| Ownership freeze test updated | ✅ | ✅ | ✅ (whitelist removed) |
| Full-suite regression | ✅ | ✅ | ✅ |

**P0 / P1 findings for W4D5: 0 / 0.**

---

## §7 — Artifacts delivered

| File | Purpose |
|------|---------|
| `tsc/diagnostics/spherical_quadrature.py` | Lebedev S² quadrature (orders 3, 5, 7) |
| `tsc/diagnostics/test_spherical_quadrature.py` | 54 tests |
| `tsc/diagnostics/entropy_invariants.py` | $s/n$, Gram admissibility, MB η-independence |
| `tsc/diagnostics/test_entropy_invariants.py` | 27 tests |
| `tsc/charts/boost_coefficients.py` | Prop 5 boost coefficients (extracted from channel_routing) |
| `bass/validation/channel_routing.py` | Refactored: 120 lines of definitions replaced with 10-line re-export block |
| `tsc/charts/boost_perturbative.py` | Import source switched to `tsc.charts.boost_coefficients` |
| `test_ownership_freeze.py` | Whitelist retired, TSC_MODULES + BASS_MODULES updated |
| `WEEK4_DAY5_PACKET.md` | This document |

---

## §8 — W5 preview

Suggested W5 focus (to be finalized upon approval):

1. **Multi-ℓ hierarchy coupling** — extend `ray_transport.py` from single-ℓ (ℓ=2) to $\ell \in \{0, 1, 2, 3, ...\}$ with streaming cascade
2. **Implicit time integrator** — Rodas5P or IMEX-ARK4 for stiff pre-recombination regime
3. **Bianchi I full shear tensor** — lift axisymmetric restriction; add off-axis components
4. **HEALPix bridge** — Lebedev → HEALPix pixel map for N_side = {8, 16, 32}
5. **Matrix `GramAdmissibility` application** — apply the W4D5 diagnostic to real Teff Grams from production pipelines

---

**End of W4D5 packet and W4 close-out. Awaiting approval for W5 scope definition.**
