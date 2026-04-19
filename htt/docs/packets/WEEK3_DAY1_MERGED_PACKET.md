# WEEK 3 DAY 1 PACKET — merged v4.1

**Date**: 2026-04-17
**Scope**: `bass/runtime/` skeleton per `CANONICAL_DECISION_DESIGN.md`
**Modules**: `canonical_decision.py` (245 LoC), `validation_labels.py` (145 LoC)
**Tests**: 47 (27 canonical + 20 labels), 7 classes
**Status**: ✅ VALIDATED, 0 P0 / 0 P1 findings
**Cumulative**: 627 tests, 4.29 s runtime

> **Note on week numbering.** Under the merged v4.1 plan (approved 2026-04-17), this is the
> *revised* W3D1. The v4-baseline W3D1 work (`inverse_T_to_F.py`, 48 tests) is now retroactively
> classified as W3D3-partial per `BASS_PY_INTEGRATION_v4_1_MERGED.md` §8. Both efforts land on
> 2026-04-17 in the same calendar day, but only the runtime skeleton documented here is the
> authoritative W3D1 deliverable going forward.

---

## §1 — Scope and architectural role

Per `CANONICAL_DECISION_DESIGN.md` §1 and execution plan v3 §7 A1, bass-py requires a **single
owner of allow/block verdicts** before any downstream consumer (forward strata, likelihood, figure
generators, future MIO/HTT clients) can route validation questions deterministically. Before this
module lands, every consumer would need to know how to query the beta policy, shear-floor policy,
and tangency diagnostic separately, and would develop divergent heuristics. After this module
lands, the question reduces to `decision.allow_reduction`.

Scope of Day 1:

- **CanonicalDecision dataclass** (frozen, version-pinned at `v1.0-w3d1`)
- **make_canonical_decision factory** — sole sanctioned construction path
- **source_Dge2_gate** — thin wrapper around Paper I Teff tangency diagnostic
- **ValidationLabel enum** — 8 labels per execution plan §6 D3
- **derive_labels** — deterministic emission rules per design spec §4.2
- **CanonicalBlockError + require_allow_reduction** — consumer-facing raise helpers

Deferred to D2:

- `beta_policy_gate` in `baryon_only_policy.py` (VT-07 formula with `safety_margin`)
- `sigma_min_gate` in new `bass/runtime/sigma_floor.py` (Σ² ≥ 10⁻⁶ Sobolev floor)

Both deferred gates are consumed through the existing `(bool, dict)` tuple API; no change to
`canonical_decision.py` is required to wire them in at D2.

---

## §2 — Mathematical and architectural construction

### 2.1 The AND-of-three invariant

$$\mathrm{allow\_reduction} \equiv \mathrm{beta\_policy\_pass} \wedge \mathrm{sigma\_min\_above\_floor} \wedge \mathrm{source\_D_{\geq 2}\_gate\_pass}$$

This invariant is enforced in two places: (a) the factory constructs `allow_reduction` as the
explicit AND; (b) `__post_init__` re-verifies and raises if the dataclass is constructed
directly with a mis-claimed value. No consumer can "overrule" the AND by manual construction.

### 2.2 Version-pin contract

`SPEC_VERSION = "v1.0-w3d1"`. Consumers must check this tag and refuse to operate under a
mismatched version. W6 entry may bump to `v1.1` after a formal re-audit covering the three
pending items in design spec §7.

### 2.3 Label derivation is a pure function

`derive_labels(beta, sigma, source, diagnostics) → frozenset` has **no hidden state**. Given the
same four inputs it returns a set that compares equal. This is asserted by
`TestDeterminism::test_idempotent_across_calls` which interleaves different inputs and checks
the original call's result is still reproducible.

Rule table (design spec §4.2, mechanized):

| Input state | Emitted labels |
|-------------|----------------|
| All 3 pass, $D/\|G\| < 10^{-7}$ | `TRACE_SOURCE_ADEQUATE` |
| All 3 pass, $10^{-7} \leq D/\|G\| < 10^{-6}$ | `TRACE_SOURCE_ADEQUATE`, `RESOLVED_SPIN2_INVISIBILITY_RISK` |
| source fails, others pass | `TRACE_SOURCE_INADEQUATE`, `SOURCE_DGE2_GATE`, `UPGRADE_TO_TWOFIELD_CANDIDATE` |
| beta fails | `BETA_POLICY_BLOCK` (+ other failure flags) |
| sigma fails | `SIGMA_MIN_BELOW_FLOOR` (+ other failure flags) |
| any fail, fraction > 0.99 | + `MIXED_CHANNEL_PROPAGATION_PENDING` |

---

## §3 — Implementation ledger

| Component | Location | Role |
|-----------|----------|------|
| `SPEC_VERSION` constant | `canonical_decision.py` §1 | Interface version pin |
| `CanonicalBlockError` | `canonical_decision.py` §2 | Consumer exception type |
| `CanonicalDecision` dataclass | `canonical_decision.py` §3 | Frozen, post-init-validated verdict |
| `_freeze_diagnostics` | `canonical_decision.py` §3 | `MappingProxyType` top-level readonly |
| `source_Dge2_gate` | `canonical_decision.py` §4 | `TangencyResult` → `(bool, dict)` wrapper |
| `make_canonical_decision` | `canonical_decision.py` §5 | Sole sanctioned factory |
| `require_allow_reduction` | `canonical_decision.py` §6 | Consumer raise-on-block helper |
| `ValidationLabel` Enum | `validation_labels.py` §1 | 8-member pinned-value enum |
| Band-edge constants | `validation_labels.py` §2 | Design spec §4.2 thresholds centralized |
| `derive_labels` | `validation_labels.py` §3 | Pure-function emission |
| `labels_indicate_block` / `_upgrade_path` | `validation_labels.py` §4 | Consumer convenience predicates |

### 3.1 Import graph

```
canonical_decision  ──→  tangency (TangencyResult)        [existing W2D3]
canonical_decision  ──→  validation_labels                 [new D1]
validation_labels   ──→  (stdlib only)
```

No circular dependencies. `validation_labels` is a pure sink — it imports nothing outside
stdlib, so it can be moved under `bass/runtime/` at W3D5 freeze without ripple effects.

### 3.2 Directory placement (pre-freeze)

Both files live at the current flat repo root until the W3D5 freeze commit. Post-freeze paths
per `BASS_PY_INTEGRATION_v4_1_MERGED.md` §2.2:

- `canonical_decision.py` → `bass/runtime/canonical_decision.py`
- `validation_labels.py` → `bass/runtime/validation_labels.py`

---

## §4 — Verified behaviour

### 4.1 AND truth table (parametrized over 8 rows)

`TestAllowReductionAND::test_AND_truth_table` exercises all $2^3 = 8$ combinations of the three
gate booleans. Every row verifies `allow_reduction` matches the AND and that the three per-gate
flags are preserved into the dataclass.

### 4.2 Label emission sanity

| Scenario | Expected labels observed |
|----------|--------------------------|
| All pass, tight rel_res | `{TRACE_SOURCE_ADEQUATE}` |
| All pass, rel_res = 5e-7 | + `RESOLVED_SPIN2_INVISIBILITY_RISK` |
| Source-only fail | `{TRACE_SOURCE_INADEQUATE, SOURCE_DGE2_GATE, UPGRADE_TO_TWOFIELD_CANDIDATE}` |
| Source + beta fail | No upgrade candidate (correctly suppressed) |
| Beta + sigma fail with fraction 0.995 | + `MIXED_CHANNEL_PROPAGATION_PENDING` |

The `UPGRADE_TO_TWOFIELD_CANDIDATE` is correctly gated on *sole source failure* — if any policy
fails alongside, the upgrade signal is withheld (per design spec §4.2).

### 4.3 Band-edge half-open semantics

`TestAllPassEmission::test_band_edges_are_half_open` explicitly probes $\mathrm{rel\_res} = 10^{-7}$
(lower inclusive), $\mathrm{rel\_res} = 0.9 \times 10^{-7}$ (just below, excluded), and
$\mathrm{rel\_res} = 10^{-6} \times (1 - 10^{-9})$ (just below upper exclusive edge). The
half-open interval $[10^{-7}, 10^{-6})$ behaves as specified.

### 4.4 Factory type gating

Five test paths in `TestFactoryPath` reject malformed inputs:
- non-tuple for `beta_result`
- wrong-length tuple (3 elements instead of 2)
- int instead of bool at position 0
- string instead of dict at position 1
- happy-path types preserved

### 4.5 Frozen-instance enforcement

`TestFrozenContract::test_dataclass_is_frozen` confirms attribute write raises. The
`__post_init__` lies-catcher is exercised by
`test_allow_reduction_consistency_enforced` (claims `allow_reduction=True` with
`source=False` → `ValueError`).

---

## §5 — Verified vs conditional (three-tier taxonomy)

### 5.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| AND-of-three invariant holds for all 8 input combinations | `TestAllowReductionAND` (parametrized ×8) |
| `emitted_labels` matches `derive_labels` on same inputs | `TestDiagnosticsFlow::test_labels_match_derive_labels_oracle` |
| Band-edge half-open $[10^{-7}, 10^{-6})$ | `test_band_edges_are_half_open` |
| `derive_labels` is stateless / idempotent | `TestDeterminism::test_idempotent_across_calls` |
| Frozen dataclass + spec_version pin | `TestFrozenContract` (4 tests) |
| Factory rejects malformed inputs | `TestFactoryPath` (5 tests) |
| `CanonicalBlockError` carries decision context | `TestConsumerAPI::test_CanonicalBlockError_carries_decision` |
| All 8 ValidationLabel values pinned to stable strings | `test_enum_values_are_pinned` |

### 5.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| `beta_policy_pass` input is semantically meaningful | Depends on D2 `beta_policy_gate` implementation (VT-07 formula) |
| `sigma_min_above_floor` input is semantically meaningful | Depends on D2 `sigma_min_gate` in new `sigma_floor.py` |
| `RESOLVED_SPIN2_INVISIBILITY_RISK` band edges $[10^{-7}, 10^{-6})$ | Current choice is design spec §7 open item (may tune at W4D5) |
| `MIXED_CHANNEL_FRACTION_FLOOR = 0.99` | Placeholder; may tune when real per-mode $\langle G, G \rangle$ distributions are available |

### 5.3 NOT ESTABLISHED (deferred)

- `beta_policy_gate` concrete implementation (D2)
- `sigma_min_gate` concrete implementation (D2)
- Cross-module import-graph ownership tests (`test_ownership_freeze.py` at W3D5)
- TSC-side `UPGRADE_TO_TWOFIELD_CANDIDATE` action mapping (deferred to TSC refactor)

---

## §6 — Self-audit (PHYS-MATH-CODE)

### 6.1 Design-spec compliance

| Design spec §  | Item | Status |
|----------------|------|--------|
| §2.1 source | `beta_policy_pass` via `(bool, dict)` tuple | ✅ contract matches |
| §2.2 source | `sigma_min_above_floor` via `(bool, dict)` tuple | ✅ contract matches |
| §2.3 source | `source_Dge2_gate` wraps `TangencyResult.is_tangent` | ✅ implemented |
| §3 dataclass | `SPEC_VERSION = "v1.0-w3d1"` | ✅ |
| §3 dataclass | Frozen, `__post_init__` validates AND + version | ✅ |
| §3 dataclass | `allow_reduction` = AND of three gates | ✅ |
| §3 dataclass | `emitted_labels` = `derive_labels(...)` output | ✅ enforced in `__post_init__` |
| §3 dataclass | `diagnostics` top-level readonly | ✅ `MappingProxyType` |
| §4.1 enum | 8 labels with pinned string values | ✅ |
| §4.2 rules | Deterministic from 4 inputs | ✅ verified |
| §6.1 tests | ≥ 18 structural tests | ✅ 27 delivered |
| §6.2 tests | Label emission combinatorics | ✅ 20 delivered (D1 scope) |

### 6.2 PHYS-MATH-CODE findings

| Check | Status | Remark |
|-------|--------|--------|
| ASCII section banners | ✅ | `============` dividers throughout |
| Banned vocabulary absent | ✅ | Full wordlist scanned |
| Type hints on all public functions | ✅ | `FrozenSet`, `Optional`, `Tuple` |
| Frozen dataclass for result container | ✅ | `frozen=True` |
| No wildcard imports | ✅ | Explicit `from X import Y` |
| Error paths raise informative exceptions | ✅ | 5 distinct error paths tested |
| No regression in W1/W2/W3D1(v4) tests | ✅ | 627 cumulative pass |
| Import graph: `bass/runtime` imports only stdlib + `tangency` + `validation_labels` | ✅ | Confirmed |
| `validation_labels` imports only stdlib | ✅ | No circular risk |
| Design spec §9 open items carried to D2/W4D5 | ✅ | Logged under §5.2 / §5.3 |

**Findings: 0 P0 / 0 P1.** Module cleared for D2 dependency.

---

## §7 — API surface (reference)

```python
from canonical_decision import (
    SPEC_VERSION,            # "v1.0-w3d1"
    CanonicalDecision,       # frozen dataclass
    CanonicalBlockError,     # exception carrying decision context
    make_canonical_decision, # sole construction path
    source_Dge2_gate,        # TangencyResult wrapper
    require_allow_reduction, # raise-on-block helper
)
from validation_labels import (
    ValidationLabel,         # 8-member enum
    ALL_LABELS,              # frozenset of all values
    derive_labels,           # pure-function emission
    labels_indicate_block,
    labels_indicate_upgrade_path,
)

# Typical consumer usage
decision = make_canonical_decision(
    beta_result=(beta_pass, beta_diag),       # D2 gate output
    sigma_result=(sigma_pass, sigma_diag),    # D2 gate output
    tangency_result=tangency_diagnostic,      # tangency.compute_D_diagnostic(...)
)

require_allow_reduction(decision, context="forward-strata")  # raises if blocked

# Otherwise proceed with reduction, knowing:
#   decision.allow_reduction is True
#   decision.emitted_labels includes TRACE_SOURCE_ADEQUATE
```

---

## §8 — Numerical ledger (quick-reference)

| Quantity | Value |
|----------|-------|
| New tests | 47 (27 canonical + 20 labels) |
| Cumulative tests | 627 |
| Full-suite runtime | 4.29 s |
| Module LoC | 390 total (245 + 145) |
| Design spec §6.1 target vs delivered | 18 vs 27 |
| Design spec §6.2 target vs delivered | 15 vs 20 |
| AND truth table rows | 8 / 8 verified |
| ValidationLabel members | 8 / 8 with pinned strings |
| Cyclic imports | 0 |
| Banned vocabulary hits | 0 |

---

## §9 — Next action (W3D2, merged v4.1)

D2 completes the two deferred gates and begins wiring:

1. **`bass/tilt/baryon_only_policy.py`** extension — add `beta_policy_gate(beta, eps_1, eta_u_dot, safety_margin=0.5)` implementing VT-07 safe-route check. Current `activate_baryon_tilt` stays; the gate is a new public API on top.
2. **`bass/runtime/sigma_floor.py`** (new module, ~80 LoC) — `sigma_min_gate(sigma_squared, floor=1e-6)` per design spec §2.2.
3. **Wiring** — update test scaffolding so that `make_canonical_decision` can be called with real D2 gate outputs end-to-end (replacing today's stubbed `(bool, dict)` inputs).
4. **Expected tests**: ~30 new (15 beta gate + 12 sigma floor + 3 end-to-end wiring). Cumulative target ~657 by end of D2.

D3 then takes up the TSC-side reclassification of today's completed `inverse_T_to_F.py` work
(directory move prep) alongside the roundtrip MC sweep absorbed from v4's original W3D2.

---

**End of W3D1 packet. Awaiting approval for D2.**
