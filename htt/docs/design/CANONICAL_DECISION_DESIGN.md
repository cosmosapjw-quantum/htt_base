# CANONICAL DECISION DESIGN SPEC

**Date**: 2026-04-17
**Status**: PROPOSED (blocker for revised W3D1 start)
**Scope**: Python bass-py runtime only. Rust BASS 영역 제외.
**Authority**: Supersedes any ad-hoc decision logic in W1-W2 modules once W3D5 freeze commit lands.

---

## §1 Purpose

`CanonicalDecision` is the **single owner of allow/block verdicts** across the bass-py integration. Every downstream consumer (forward strata caller, likelihood runner, figure generator, future MIO/HTT clients) that needs to know "is this mode/species/timestep usable?" MUST route the question through `make_canonical_decision(...)`. No alternative validation path is sanctioned.

Without this contract, multiple callers develop divergent validation logic, and the decision space fractures. execution plan v3 §7 A1 formalizes BASS as the sole allow/block owner; this document operationalizes that principle in Python.

---

## §2 The three inputs — sources, semantics, thresholds

### 2.1 `beta_policy_pass: bool`

**Semantic**: Does the tilt dipole strength β stay inside the frame-attribution-corrected safe route?

**Source module**: `bass/tilt/baryon_only_policy.py` — new gate API on top of existing `SpeciesRegistry` + `activate_baryon_tilt`. The gate function to introduce:

```python
def beta_policy_gate(
    beta: float,
    epsilon_1: float,
    eta_u_dot: float,
    safety_margin: float = 1.0,
) -> tuple[bool, dict]:
    """VT-07 frame-attribution-corrected safe-route check.

    Safe route: beta <= safety_margin * epsilon_1 / (1 + eta_u_dot)

    Returns
    -------
    passed : bool
    diagnostics : dict with keys
        - 'beta', 'threshold', 'margin_used', 'fractional_slack'
    """
```

**Threshold semantics**:
- Safe route (VT-07): $\beta \leq \epsilon_1 / (1 + \eta_{\dot u})$
- `safety_margin = 1.0`: at the boundary. Production VER06 should use `safety_margin = 0.5` (factor-2 buffer).
- Inputs $\epsilon_1, \eta_{\dot u}$ are per-mode; the caller supplies them from the ongoing evaluation context.

**Current code status**: gate function to be added in W3D1-b (same day as `canonical_decision.py` skeleton, or as part of the `baryon_only_policy.py` extension in the `bass/tilt/` move).

**SSOT**: `obs_defaults.json` should carry the production `safety_margin` value; `ssot.py` exposes it; `beta_policy_gate` reads from there unless overridden.

### 2.2 `sigma_min_above_floor: bool`

**Semantic**: Is the minimum shear magnitude over the evaluated domain above the Sobolev-validity floor? Below the floor, the Sobolev cancellation theorem's O(10⁻⁷) correction bound ceases to be safe.

**Source module**: `bass/runtime/sigma_floor.py` — **new module**, not a repurposing. The check:

```python
SIGMA_FLOOR_DEFAULT = 1e-6   # From Sobolev validity region (see userMemories)

def sigma_min_gate(
    sigma_squared: float | np.ndarray,
    floor: float = SIGMA_FLOOR_DEFAULT,
) -> tuple[bool, dict]:
    """Check Σ² ≥ floor at every evaluation point.

    The Sobolev cancellation scope (validity conditions A1–A5) is conditional
    on Σ² sufficiently above the noise floor. At Σ² ~ 10⁻⁶ the correction is
    O(10⁻⁷) — safe. Below ~10⁻⁶ the cancellation theorem label becomes an
    overclaim.

    Returns
    -------
    passed : bool
    diagnostics : dict with 'sigma_min', 'floor', 'margin_factor'
    """
```

**Threshold semantics**:
- Floor: $10^{-6}$ default. This matches the Sobolev validity bound recorded in userMemories and `consolidated_baryon_CDM_EFT_boundary_notes.md`.
- For arrays: the gate fails if **any** entry drops below floor.
- Failure diagnostic includes the index/location of the minimum so callers can locate the offending mode.

**Current code status**: does not exist. Needs to be created in W3D1 as part of the runtime skeleton.

**Dependency**: existing `shear_sources.py` computes the shear magnitude but does not expose a gate. The new module imports `shear_sources` only for types; the floor check itself is pure policy.

### 2.3 `source_Dge2_gate_pass: bool`

**Semantic**: Is the collision source $\ell \geq 2$ content on-manifold within the Paper I Teff chart? If off-manifold by more than the Gram-quadrature floor, the forward F map cannot faithfully represent the source and we are in **source-adequate-but-propagation-pending** territory (validation label §4.3 below).

**Source module**: `tsc/diagnostics/tangency.py` (existing W2D3 module, post-move path). Reuse:

```python
from tsc.diagnostics.tangency import compute_D_diagnostic, TangencyResult

def source_Dge2_gate(tangency_result: TangencyResult) -> tuple[bool, dict]:
    """Wrap TangencyResult.is_tangent as a gate boolean.

    Threshold is fixed at relative_residual < 1e-6 inside is_tangent (W2D3
    convention: quadrature floor ~10⁻⁹, gate at 1e-6 for 3 decades of margin).

    Returns
    -------
    passed : bool
    diagnostics : dict with 'D', 'relative_residual', 'fraction_on_manifold'
    """
```

**Threshold semantics**:
- Reuse the `TangencyResult.is_tangent` property (W2D3 established threshold 10⁻⁶).
- No new threshold introduced — this gate is a thin wrapper so that the decision consumer never touches `TangencyResult` directly.

**Current code status**: `TangencyResult.is_tangent` exists. The gate wrapper is a ~10-line addition in `bass/runtime/canonical_decision.py`.

---

## §3 `CanonicalDecision` data class spec

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet

SPEC_VERSION = "v1.0-w3d1"   # bump on any field change, even reordering

@dataclass(frozen=True)
class CanonicalDecision:
    """Single allow/block verdict owner. Emitted by bass/runtime only.

    spec_version : str
        Must equal SPEC_VERSION at construction time. Consumers pin
        compatibility via this tag.
    beta_policy_pass : bool
        VT-07 safe-route outcome (§2.1).
    sigma_min_above_floor : bool
        Sobolev validity check (§2.2).
    source_Dge2_gate_pass : bool
        Paper I Teff chart faithfulness (§2.3).
    allow_reduction : bool
        Equals AND(three pass bools). No other logic.
    emitted_labels : frozenset[ValidationLabel]
        Subset of the 8 labels (see §4). Derived deterministically from the
        three pass bools and side-channel diagnostics.
    diagnostics : dict
        Read-only dict of per-input diagnostic info. Opaque to the consumer
        beyond logging/debugging.

    All fields are frozen; to change state, construct a new instance.
    """
    spec_version: str
    beta_policy_pass: bool
    sigma_min_above_floor: bool
    source_Dge2_gate_pass: bool
    allow_reduction: bool
    emitted_labels: FrozenSet["ValidationLabel"]
    diagnostics: dict = field(default_factory=dict)

    def __post_init__(self):
        expected = (
            self.beta_policy_pass
            and self.sigma_min_above_floor
            and self.source_Dge2_gate_pass
        )
        if self.allow_reduction != expected:
            raise ValueError(
                f"allow_reduction must equal AND(three inputs); "
                f"got {self.allow_reduction}, expected {expected}"
            )
        if self.spec_version != SPEC_VERSION:
            raise ValueError(
                f"spec_version mismatch: got {self.spec_version}, "
                f"expected {SPEC_VERSION}"
            )
```

**Factory API**:

```python
def make_canonical_decision(
    beta_context: BetaContext,
    sigma_context: SigmaContext,
    tangency_result: TangencyResult,
) -> CanonicalDecision:
    """The sole construction path. All three gates evaluated here."""
```

Direct instantiation of `CanonicalDecision(...)` is allowed only in tests (a module-level `_is_test_context()` check can be added if drift appears).

---

## §4 Validation label emission (8 labels, §6 D3 of execution plan)

### 4.1 Enum definition (lives in `bass/runtime/validation_labels.py`)

```python
class ValidationLabel(Enum):
    TRACE_SOURCE_ADEQUATE = "trace_source_adequate"
    TRACE_SOURCE_INADEQUATE = "trace_source_inadequate"
    UPGRADE_TO_TWOFIELD_CANDIDATE = "upgrade_to_twofield_candidate"
    RESOLVED_SPIN2_INVISIBILITY_RISK = "resolved_spin2_invisibility_risk"
    MIXED_CHANNEL_PROPAGATION_PENDING = "mixed_channel_propagation_pending"
    BETA_POLICY_BLOCK = "beta_policy_block"
    SOURCE_DGE2_GATE = "source_Dge2_gate"
    SIGMA_MIN_BELOW_FLOOR = "sigma_min_below_floor"
```

### 4.2 Emission rules (deterministic, no hidden state)

| Input state | Labels emitted |
|-------------|----------------|
| All three pass, $D_{s,\geq 2}/\|G\|$ < 1e-7 | `TRACE_SOURCE_ADEQUATE` |
| All three pass, 1e-7 ≤ $D/\|G\|$ < 1e-6 | `TRACE_SOURCE_ADEQUATE`, `RESOLVED_SPIN2_INVISIBILITY_RISK` |
| `source_Dge2_gate_pass=False` while other two pass | `TRACE_SOURCE_INADEQUATE`, `SOURCE_DGE2_GATE`, `UPGRADE_TO_TWOFIELD_CANDIDATE` |
| `beta_policy_pass=False` | `BETA_POLICY_BLOCK` (+ others that also failed) |
| `sigma_min_above_floor=False` | `SIGMA_MIN_BELOW_FLOOR` (+ others that also failed) |
| Mixed-channel case (any gate fails but `fraction_on_manifold > 0.99`) | + `MIXED_CHANNEL_PROPAGATION_PENDING` |

`UPGRADE_TO_TWOFIELD_CANDIDATE` — chart-level meaning owner is **TSC** (per execution plan §6 D3). `bass/runtime/` emits the label; TSC decides what upgrade action means.

### 4.3 Ownership invariants (enforced by `test_ownership_freeze.py`)

- Only `bass/runtime/canonical_decision.py` constructs `CanonicalDecision` (import-graph check)
- Only `bass/runtime/validation_labels.py` emits `ValidationLabel` values outside of tests
- TSC modules may *read* `ValidationLabel` but must not instantiate or return them

---

## §5 Consumer contract

### 5.1 W3–W5 consumers (Python, currently planned)

| Consumer | How it uses `CanonicalDecision` |
|----------|--------------------------------|
| `tsc/charts/inverse_T_to_F.py` (W3D3) | On `allow_reduction=False`, raise `CanonicalBlockError`; forwards labels in exception payload |
| `bass/transport/ray_transport.py` (W4D4) | Same pattern, ODE step refuses to advance |
| `bass/collision/thomson_tensor.py` (W4D3) | Same pattern, collision RHS returns zero tensor |
| Forward strata caller (W5) | Aggregates decisions per mode; mode-wise mask |

### 5.2 W6+ consumers (future, contract pinned now)

| Consumer | Interface stability requirement |
|----------|--------------------------------|
| Likelihood runner (W6) | Queries `allow_reduction` per timestep |
| Figure generator (W9) | Refuses to plot modes with `allow_reduction=False` |
| MIO client (W6+) | Consumes `emitted_labels`, routes `MIXED_CHANNEL_PROPAGATION_PENDING` to observatory flag |
| HTT client (W6+) | Consumes `UPGRADE_TO_TWOFIELD_CANDIDATE` to trigger local-patch refinement |

**Stability**: `SPEC_VERSION` is pinned at `v1.0-w3d1` until W5 end. W6 entry may bump to `v1.1` if new fields are required; consumers must check version on construction.

---

## §6 Test plan (required before W3D1 module is considered PASSED)

### 6.1 Structural (18 tests target — `test_canonical_decision.py`)

1. `test_CanonicalDecision_is_frozen` — attribute write raises
2. `test_allow_reduction_is_AND` — all 8 truth-table rows
3. `test_spec_version_mismatch_raises` — wrong version in constructor
4. `test_allow_reduction_mismatch_raises` — mis-claim in `__post_init__`
5. `test_diagnostics_readonly_by_convention` — dict copy on mutation attempt
6. `test_make_canonical_decision_returns_only_via_factory` — import path check
7. `test_beta_policy_gate_VT07` — VT-07 formula check at boundary
8. `test_sigma_floor_gate_threshold` — 1e-6 boundary, array input
9. `test_source_Dge2_gate_wraps_is_tangent` — consistency with `TangencyResult`
10. `test_emission_rule_all_pass` — `TRACE_SOURCE_ADEQUATE` emitted
11. `test_emission_rule_source_fail` — `TRACE_SOURCE_INADEQUATE` + `SOURCE_DGE2_GATE` + `UPGRADE_TO_TWOFIELD_CANDIDATE`
12. `test_emission_rule_beta_fail` — `BETA_POLICY_BLOCK`
13. `test_emission_rule_sigma_fail` — `SIGMA_MIN_BELOW_FLOOR`
14. `test_emission_rule_mixed_channel` — `MIXED_CHANNEL_PROPAGATION_PENDING` when fraction > 0.99
15. `test_emission_rule_resolved_spin2_risk` — borderline D range
16. `test_no_label_duplication` — `frozenset` semantics
17. `test_label_enum_stability` — values stable across versions
18. `test_diagnostics_carries_source_info` — all three gate diagnostic dicts preserved

### 6.2 Behavioural (paired with W3D2 validation_labels suite, 15 tests)

Covers label emission combinatorics, cross-module wiring, and the ownership invariants (import-graph tests).

### 6.3 Ownership freeze (W3D5 deliverable, 12 tests)

- `test_BASS_is_sole_allow_block_owner`
- `test_TSC_does_not_emit_final_labels`
- `test_TSC_upgrade_recommendation_visible_to_BASS`
- `test_no_TSC_to_MIO_direct_path`
- `test_no_HTT_to_TSC_direct_path`
- `test_spec_version_pin_across_modules`
- `test_all_consumers_check_allow_reduction_before_proceeding`
- (5 more covering directory structure and `__init__` exports)

**Implementation of import-graph tests**: AST-level inspection (`ast.parse` on all .py files, collect `Import`/`ImportFrom` nodes, check against an allowed adjacency table).

---

## §7 Open items (to be resolved during W3D1 implementation)

| Item | Decision deferred to | Default |
|------|---------------------|---------|
| Production `safety_margin` for VT-07 gate | W5 forward strata wiring | 0.5 (factor-2 buffer) |
| `SIGMA_FLOOR_DEFAULT` refinement | W5 when we have real Σ² ranges | 1e-6 |
| `RESOLVED_SPIN2_INVISIBILITY_RISK` D-band edges | W4D5 cleanup | [1e-7, 1e-6] |
| Whether to promote `CanonicalBlockError` to a typed exception hierarchy | W5 if multiple consumers need distinct catch-patterns | single class |
| CRAG integration of execution plan v3 content | When the reference doc is shared | out of scope here |

---

## §8 Non-goals (explicit)

- This document does not define how MIO/HTT **use** labels — only how bass runtime emits them.
- This document does not define the Rust BASS `CanonicalDecision` struct (separate concern).
- Tier A 3D angular PDE ownership — Rust domain, not this spec.
- TSC-side `UPGRADE_TO_TWOFIELD_CANDIDATE` mapping — deferred to `tsc/` refactor at W3D5.

---

## §9 Acceptance for W3D1 start

W3D1 begins **only when all items below are green**:

- [x] §2.1, §2.2, §2.3 each identify a concrete source module
- [x] §3 `CanonicalDecision` shape is frozen (version `v1.0-w3d1`)
- [x] §4.2 emission rules are deterministic (no hidden state)
- [x] §6 test plan enumerates ≥ 18 structural tests
- [ ] User approval of this spec document (← **blocker**)

On approval, revised W3D1 opens with `bass/runtime/canonical_decision.py` implementation matching §3 exactly. Any deviation requires spec-version bump.

---

**End of design spec. Awaiting approval.**
