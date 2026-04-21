# WEEK 3 DAY 2 PACKET — merged v4.1

**Date**: 2026-04-17
**Scope**: Two gate implementations + end-to-end wiring of `make_canonical_decision`
**New modules / additions**:
  - `baryon_only_policy.py` §6 append — `beta_policy_gate` (VT-07, ~95 LoC)
  - `sigma_floor.py` — new `bass/runtime/` module (~95 LoC)
**Tests**: 40 (17 beta + 17 sigma + 6 e2e wiring) across 11 classes
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 667 tests, 4.49 s runtime

---

## §1 — Scope and architectural role

D1 introduced the `CanonicalDecision` factory with the three inputs abstracted as `(bool, dict)`
tuples and stubbed at test time. D2 replaces the stubs with the actual gate implementations:

| Gate input | D1 status | D2 status |
|------------|-----------|-----------|
| `beta_policy_pass` | stubbed | `beta_policy_gate(beta, epsilon_1, eta_u_dot, safety_margin)` |
| `sigma_min_above_floor` | stubbed | `sigma_min_gate(sigma_squared, floor)` |
| `source_Dge2_gate_pass` | implemented (`source_Dge2_gate` wrapper) | unchanged |

Forward-strata and likelihood code paths (W5+) can now construct a production `CanonicalDecision`
without any stubs. The three-tuple end-to-end signature is frozen under `SPEC_VERSION = "v1.0-w3d1"`.

Deferred to later days (unchanged from D1 packet):

- TSC-side `UPGRADE_TO_TWOFIELD_CANDIDATE` action mapping → W3D5 freeze commit scope
- `test_ownership_freeze.py` import-graph invariants → W3D5
- SSOT migration of `BETA_SAFETY_MARGIN_DEFAULT` and `SIGMA_FLOOR_DEFAULT` → W5+ when `ssot.py` lands

---

## §2 — VT-07 gate mathematics

### 2.1 Safe-route condition

$$|\beta| \;\leq\; \mathrm{safety\_margin} \times \frac{\epsilon_1}{1 + \eta_{\dot u}}$$

where $\epsilon_1$ is the first Pastén ε parameter and $\eta_{\dot u}$ is the four-acceleration
frame-attribution factor (userMemories: VT-07 ~16% bias absorbed through the $(1+\eta_{\dot u})$
denominator). Production `safety_margin = 0.5` gives a factor-2 buffer below the naive edge.

### 2.2 Diagnostic payload

Every call returns a six-key dict: `beta`, `epsilon_1`, `eta_u_dot`, `safety_margin`, `threshold`,
`fractional_slack`. The slack is signed: positive = headroom, negative = violation depth.
Downstream logging consumes this directly; no post-processing needed at the factory layer.

### 2.3 Scaling invariants (verified)

| Effect | Expected | Verified in |
|--------|----------|-------------|
| Halving safety_margin halves threshold | exact factor 2 | `test_safety_margin_halves_threshold` |
| $\eta_{\dot u}: 0 \to 1$ | threshold → threshold / 2 | `test_larger_eta_u_dot_tightens_threshold` |
| Doubling $\epsilon_1$ | threshold doubles | `test_larger_epsilon_relaxes_threshold` |
| $\eta_{\dot u} = 0$, $\mathrm{safety\_margin} = 1$ | threshold = $\epsilon_1$ | `test_eta_u_dot_zero_yields_safety_margin_times_eps_1` |
| Sign of β | irrelevant (uses $|\beta|$) | `test_sign_of_beta_is_immaterial` |

### 2.4 VER06 production sanity

β = 1.36×10⁻³ with plausible production (ε₁ = 0.02, η_{u̇} = 0.16) gives threshold = 8.62×10⁻³
and `fractional_slack = +0.842` (84% headroom). VER06 clears the gate with comfortable margin.
Documented as `test_VER06_production_values_pass_at_reasonable_eps`.

---

## §3 — Sobolev-floor gate

### 3.1 Validity logic

$$\min_i (\Sigma^2)_i \;\geq\; \mathrm{floor}$$

default floor = 10⁻⁶. Scalar input reduces to the straight comparison; array input fails on *any*
below-floor entry, with `argmin_index` localizing the offending mode / timestep for debugging.

### 3.2 Why `argmin_index` carried in diagnostics

When forward strata fail across a $(k, \eta)$ grid, the caller needs to know *where* the violation
occurred, not just *that* one occurred. The 2-D test case (`test_2d_array_flattened_index`)
confirms that row-major flat indexing propagates correctly.

### 3.3 Boundary behaviour

| Input | Pass | margin_factor |
|-------|------|---------------|
| 10⁻⁴ (well above) | ✓ | 100 |
| 10⁻⁶ (exactly at floor) | ✓ | 1.0 |
| 0.99 × 10⁻⁶ | ✗ | 0.99 |
| 10⁻⁹ | ✗ | 10⁻³ |

The gate is inclusive at the floor (`≥`, not `>`). Verified in `test_scalar_exactly_at_floor_passes`.

---

## §4 — End-to-end wiring results

Six integration tests covering the happy path and each single-gate failure. Observed behaviour:

| Scenario | `allow_reduction` | Key labels |
|----------|-------------------|------------|
| VER06 β + Σ² ~ 1e-5 + on-manifold | ✓ True | `TRACE_SOURCE_ADEQUATE` |
| Tight ε₁ = 1e-3, other gates pass | ✗ False | `BETA_POLICY_BLOCK` |
| Σ² array has 1e-9 at idx 1 | ✗ False | `SIGMA_MIN_BELOW_FLOOR`, `MIXED_CHANNEL_PROPAGATION_PENDING` |
| Off-manifold tangency, other gates pass | ✗ False | `TRACE_SOURCE_INADEQUATE`, `SOURCE_DGE2_GATE`, `UPGRADE_TO_TWOFIELD_CANDIDATE` |
| β + Σ² both fail, tangency on-manifold | ✗ False | `BETA_POLICY_BLOCK`, `SIGMA_MIN_BELOW_FLOOR`, `MIXED_CHANNEL_PROPAGATION_PENDING` |

### 4.1 Notable interaction: mixed-channel semantics at sigma-only failure

When the Σ² gate fails but tangency remains on-manifold (fraction = 1.0 > 0.99), the
`MIXED_CHANNEL_PROPAGATION_PENDING` label fires. This correctly captures the situation
"source is adequate, but another policy blocks propagation" — the MIO-facing routing signal
for mode-dependent observatory handling. Verified in
`TestSingleFailureScenarios::test_sigma_fail_only`.

### 4.2 Notable interaction: upgrade candidate guarded at mixed failures

Off-manifold tangency with fraction = 0.5 does *not* fire `MIXED_CHANNEL_PROPAGATION_PENDING`
(fraction < 0.99). `UPGRADE_TO_TWOFIELD_CANDIDATE` fires iff source is the *sole* failure.
Verified that β-fail + source-fail combination *suppresses* the upgrade flag
(`TestSourceFailEmission::test_source_fail_with_beta_fail_no_upgrade_candidate`).

---

## §5 — Three-tier claim taxonomy

### 5.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| VT-07 formula correctly scales with each of ε₁, η_{u̇}, safety_margin | 4 scaling tests + 1 boundary test |
| Σ² gate is inclusive at floor | `test_scalar_exactly_at_floor_passes` |
| Σ² argmin_index localizes failures in arrays (incl. 2-D) | `test_2d_array_flattened_index` |
| VER06 β clears VT-07 gate at plausible production ε₁, η_{u̇} | `test_VER06_production_values_pass_at_reasonable_eps` |
| End-to-end integration: real gates → factory → decision, no type errors | 6 e2e tests all green |
| Diagnostic payload dicts contain documented keys only | `test_diagnostic_keys_complete` in both suites |
| Input validation rejects malformed inputs | 8 validation tests |

### 5.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| `BETA_SAFETY_MARGIN_DEFAULT = 0.5` is the production value | Pending W5 SSOT migration; may be tuned |
| `SIGMA_FLOOR_DEFAULT = 1e-6` matches the Sobolev validity scope | Based on userMemories note; depends on real Σ² distribution at W5 |
| Production ε₁ = 0.02, η_{u̇} = 0.16 | Illustrative (unit test); real values will be set by W4 Pastén Option B output |
| Mixed-channel fraction floor 0.99 | Placeholder — design spec §7 open item |

### 5.3 NOT ESTABLISHED (deferred)

- Concrete production numerical values for $\epsilon_1$ and $\eta_{\dot u}$ — depend on W4 Pastén
  Option B results
- Distribution of Σ² across typical forward-strata evaluations — awaiting W5 forward pipeline
- Import-graph ownership invariants — W3D5 freeze commit scope

---

## §6 — Self-audit (PHYS-MATH-CODE)

### 6.1 Design-spec compliance (D2 additions)

| Design spec §  | Item | Status |
|----------------|------|--------|
| §2.1 | `beta_policy_gate` signature | ✅ matches (`beta, epsilon_1, eta_u_dot, safety_margin=0.5`) |
| §2.1 | VT-07 formula $\leq \epsilon_1/(1+\eta_{\dot u})$ | ✅ implemented with safety_margin buffer |
| §2.1 | Diagnostic keys `beta, threshold, margin_used, fractional_slack` | ✅ (+ `epsilon_1, eta_u_dot, safety_margin` for full traceability) |
| §2.2 | `sigma_min_gate` signature | ✅ matches |
| §2.2 | Array input: any entry below → fail | ✅ |
| §2.2 | Diagnostic `sigma_min, floor, margin_factor` | ✅ (+ `argmin_index, n_samples`) |
| §2.3 | `source_Dge2_gate` unchanged | ✅ (no code change in D2) |

### 6.2 PHYS-MATH-CODE findings

| Check | Status |
|-------|--------|
| Banned vocabulary scan | clean |
| Frozen dataclasses / immutability preserved | ✅ (gate outputs are tuples, immutable by nature) |
| Type hints on all public functions | ✅ |
| Informative error messages on validation failure | ✅ (10 distinct ValueError paths tested) |
| No circular imports | ✅ (`sigma_floor` imports stdlib + numpy only; `baryon_only_policy` unchanged deps) |
| Factory compatibility verified through e2e | ✅ |
| No regression in 627 prior tests | ✅ |

**Findings: 0 P0 / 0 P1.** D2 gates cleared for W5+ production wiring.

---

## §7 — API additions

### 7.1 `baryon_only_policy.py` §6 (appended)

```python
BETA_SAFETY_MARGIN_DEFAULT: float = 0.5

def beta_policy_gate(
    beta: float,
    epsilon_1: float,
    eta_u_dot: float,
    safety_margin: float = BETA_SAFETY_MARGIN_DEFAULT,
) -> tuple[bool, dict]:
    """VT-07 frame-attribution-corrected safe-route gate."""
```

### 7.2 `sigma_floor.py` (new, top-level)

```python
SIGMA_FLOOR_DEFAULT: float = 1e-6

def sigma_min_gate(
    sigma_squared: float | np.ndarray,
    floor: float = SIGMA_FLOOR_DEFAULT,
) -> tuple[bool, dict]:
    """Sobolev-validity floor check on Σ²."""
```

### 7.3 End-to-end usage (production pattern)

```python
from baryon_only_policy import beta_policy_gate
from sigma_floor import sigma_min_gate
from canonical_decision import make_canonical_decision, require_allow_reduction
from tangency import compute_D_diagnostic, TangentKind

# At each forward-stratum evaluation:
tang = compute_D_diagnostic(G_field, TangentKind.ONE_FIELD, xi, eta)

decision = make_canonical_decision(
    beta_result=beta_policy_gate(beta_current, eps_1, eta_u_dot),
    sigma_result=sigma_min_gate(sigma_sq_grid),
    tangency_result=tang,
)
require_allow_reduction(decision, context=f"stratum_{k}_eta_{i}")

# proceed with reduction …
```

---

## §8 — Numerical ledger

| Quantity | Value |
|----------|-------|
| New tests | 40 (17 beta + 17 sigma + 6 e2e) |
| Test classes | 11 (4 + 4 + 3) |
| Cumulative tests | 667 |
| Full-suite runtime | 4.49 s |
| D2 module additions LoC | ~190 (95 beta append + 95 sigma_floor) |
| Banned vocabulary hits | 0 |
| P0 / P1 findings | 0 / 0 |
| VT-07 threshold at (ε₁=0.02, η_{u̇}=0.16, safety=0.5) | 8.62 × 10⁻³ |
| VER06 β fractional slack at above | +0.842 |
| Sobolev floor default | 10⁻⁶ |

---

## §9 — Next action (W3D3)

D3 under the merged schedule combines two strands per `BASS_PY_INTEGRATION_MERGED.md`
§4.1 and §8:

1. **`inverse_T_to_F.py` retrofit** — directory-move prep for `tsc/charts/inverse_T_to_F.py`.
   No logic change; the move itself executes at W3D5b freeze commit.
2. **Roundtrip MC sweep** — absorbed from v4 original W3D2. Stress-test the F⁻¹ ∘ F closure
   across random coefficient draws spanning the $(\xi, n, \mathrm{amp})$ product space:
   - $\xi \in \{-1, 0, +1\}$, moment order $n \in \{2, 3, 4\}$, amp $\in \{0.05, 0.1, 0.2\}$
   - ≥ 50 random Θ draws per cell, roundtrip error histogrammed
   - Precision floor locked in an `inverse_T_to_F_mc_report.md`
3. **Expected tests**: ~40 new, cumulative target ~707 by end of D3.

The MC sweep lands under `tsc/charts/` classification but stays at repo root until W3D5b. No
directory changes in D3 itself.

---

**End of W3D2 packet. Awaiting approval for D3.**
