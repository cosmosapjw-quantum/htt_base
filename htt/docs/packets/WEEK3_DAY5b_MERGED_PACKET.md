# WEEK 3 DAY 5b PACKET — merged v4.1 (Ownership Freeze Commit)

**Date**: 2026-04-17
**Scope**: Mechanical refactor locking in the v4.1 ownership model — `bass/` vs `tsc/` directory split with AST-level import-graph invariants
**New test file**: `test_ownership_freeze.py` (~290 LoC)
**Directory moves**: 17 source modules + 17 test files relocated
**Import rewrites**: 34 files updated across two regex passes
**Tests**: 48 across 5 classes
**Status**: ✅ OWNERSHIP FROZEN, 0 P0 / 1 P2 (documented) findings
**Cumulative**: 820 tests, 48.05 s runtime

---

## §1 — What D5b did

v4.1 MERGED §2.2 classified every W1–W3 module under either `bass/` or `tsc/`. D1–D5a left
the files at the flat repo root but built the new modules (`canonical_decision`, `sigma_floor`,
`species_tangency`, `precision_dashboard`) under the *logical* ownership. D5b executes the
physical directory migration and freezes the ownership boundary as an executable invariant.

Three mechanical steps plus one verification layer:

1. **Directory scaffolding**: created `bass/{background,transport,tilt,validation,runtime}` and
   `tsc/{charts,diagnostics,admissibility}` with `__init__.py` at every level.
2. **File moves**: 17 source modules + 17 test files `mv`'d into their classified directories.
   No code content changed during the move.
3. **Import-path rewrites**: two AST-regex passes updated 34 files to the fully-qualified
   package paths (`from tangency → from tsc.diagnostics.tangency`, etc.).
4. **Invariant layer**: new `test_ownership_freeze.py` with 48 tests verifying the boundary
   holds structurally and via import-graph inspection.

---

## §2 — Final directory structure

```
bass_py_monorepo/
├── conftest.py                    ← pytest package discovery root
├── precision_dashboard.py         ← L0 gate (integrates across layers)
├── test_precision_dashboard.py
├── test_ownership_freeze.py       ← D5b invariant layer
├── bass/
│   ├── __init__.py
│   ├── background/
│   │   ├── bianchi_types.py
│   │   ├── einstein_bianchi.py
│   │   └── test_bianchi_types.py
│   ├── transport/
│   │   ├── shear_sources.py
│   │   └── test_shear_sources.py
│   ├── tilt/
│   │   ├── baryon_only_policy.py
│   │   ├── test_baryon_only_policy.py
│   │   └── test_beta_policy_gate.py
│   ├── validation/
│   │   ├── comparator_policy.py
│   │   ├── channel_routing.py
│   │   ├── test_comparator_policy.py
│   │   └── test_channel_routing.py
│   └── runtime/
│       ├── canonical_decision.py
│       ├── validation_labels.py
│       ├── sigma_floor.py
│       ├── test_canonical_decision.py
│       ├── test_validation_labels.py
│       ├── test_sigma_floor.py
│       └── test_end_to_end_wiring.py
└── tsc/
    ├── __init__.py
    ├── charts/
    │   ├── laguerre_basis.py
    │   ├── forward_F_to_T.py
    │   ├── boost_perturbative.py
    │   ├── inverse_T_to_F.py
    │   ├── inverse_T_to_F_mc.py
    │   └── test_*.py
    ├── diagnostics/
    │   ├── tangency.py
    │   ├── species_tangency.py
    │   └── test_*.py
    └── admissibility/
        ├── realizability.py
        └── test_realizability.py
```

Packet files (`WEEK*_PACKET.md`), CSV outputs, and the L0 report live at the repo root.

---

## §3 — Invariants enforced (`test_ownership_freeze.py`)

### 3.1 TestDirectoryStructure (21 tests)

Parametrized over the 10 expected packages: each must exist with an `__init__.py`. Plus a
"no stray root-level solver modules" check — after the freeze, only 4 .py files belong at
the root (`conftest.py`, `precision_dashboard.py`, `test_precision_dashboard.py`, this file).

### 3.2 TestBASSRuntimeOwnership (4 tests)

- `CanonicalDecision(…)` construction appears only in `bass/runtime/`
- `ValidationLabel(…)` constructor call appears only in `bass/runtime/`
- TSC modules never import `bass.runtime.canonical_decision`
- TSC modules never import `bass.runtime.validation_labels`

The first two checks use AST-walked line-level scanning to catch the forbidden pattern even
when it appears inside a function body or class method. The latter two are import-graph
inspections via `ast.Import` / `ast.ImportFrom` nodes.

### 3.3 TestTSCDoesNotOwnRuntime (2 tests)

- TSC source modules never import from `bass.runtime`, `bass.tilt`, or `bass.validation`
- `bass/background/` and `bass/transport/` never import from `tsc/`

**Known exception — P2-W4-01**: `tsc/charts/boost_perturbative.py` imports Prop 5 boost-mixing
coefficients from `bass.validation.channel_routing`. These coefficients physically belong to
the TSC chart layer but landed in `channel_routing.py` under the pre-v4.1 flat ontology.
Whitelisted in the test with explicit P2 ticket tracking; resolution scheduled for W4+
refactor (move coefficients to `tsc/charts/boost_coefficients.py`).

### 3.4 TestSpecVersionConsistency (3 tests)

- `bass.runtime.canonical_decision.SPEC_VERSION == "v1.0-w3d1"`
- `precision_dashboard.L0_DASHBOARD_VERSION == "v1.0-w3d5a"`
- Both version strings share the `v1.0-` family prefix

### 3.5 TestPackageImportsResolve (18 tests, parametrized)

Every package-qualified module (9 BASS + 8 TSC + precision_dashboard) imports cleanly via
`importlib.import_module`. If a module's import chain breaks after a move, this test catches
it immediately.

---

## §4 — Import-rewrite pipeline

### 4.1 Pass 1 — 30 files updated

Regex template:

```regex
(^from\s+){OLD_NAME}(\s+import\s)  →  \1{NEW_PATH}\2
(^import\s+){OLD_NAME}(\s+as\b)    →  \1{NEW_PATH}\2
(^import\s+){OLD_NAME}(\s*(?:#|$|,)) →  \1{NEW_PATH}\2
```

Caught all top-level (module-header) imports, longest-first substitution order to avoid
collisions like `tangency ⊂ species_tangency` producing nonsense replacements.

### 4.2 Pass 2 — 4 additional files updated

Pass 1 used `^` anchor which matched only line-start. Indented local imports (e.g.,
`from tangency import weighted_inner_product` buried inside a function) were missed.
Pass 2 relaxed to `((?:^|(?<=\n))[ \t]*from\s+)…` to cover any indentation.

### 4.3 Residual manual fix

One test file used `import tsc.charts.inverse_T_to_F` followed by bare `inverse_T_to_F.__file__`
access. The dotted-import form does not bind the tail name, so this was hand-edited to
`from tsc.charts import inverse_T_to_F` to preserve the bare-name access.

No other manual fixes required — the regex pipeline handled the remaining ~34 files
automatically.

---

## §5 — Test count trajectory

| Stage | Count |
|-------|-------|
| Post-D3 cumulative | 703 |
| Post-D4 cumulative | 743 |
| Post-D5a cumulative | 772 |
| Directory moves + import rewrites (no new tests) | 772 |
| **D5b: `test_ownership_freeze.py` (+48)** | **820** |

W3 end target was 775 tests. Delivered 820 (**+45 over target**). The bulk of the overshoot
is in the ownership freeze test file — 18 parametrized package-import tests plus 21
parametrized directory-structure tests alone contribute 39 of the 48 total.

---

## §6 — P-level findings ledger

| ID | Level | Description | Status |
|----|-------|-------------|--------|
| **P2-W4-01** | P2 | `tsc/charts/boost_perturbative.py` imports Prop 5 coefficients from `bass/validation/channel_routing.py` | WHITELISTED with W4+ resolution plan |

No P0 or P1 findings. The single P2 is a known ontological legacy from the pre-v4.1 flat
layout, whitelisted explicitly in the ownership freeze test with a tracked resolution target.

---

## §7 — Three-tier claim taxonomy

### 7.1 ESTABLISHED

| Claim | Evidence |
|-------|----------|
| All 17 W1-W2 source modules live at their v4.1-classified paths | `TestDirectoryStructure` + `TestPackageImportsResolve` |
| All test modules live alongside their subject | File listing + package import tests |
| `CanonicalDecision` / `ValidationLabel` construction is BASS-exclusive | 2 AST line-scan tests |
| No TSC → bass/runtime, bass/tilt, or bass/validation imports (modulo P2-W4-01) | 2 import-graph tests with explicit whitelist |
| No bass/background or bass/transport → tsc/ imports | 1 import-graph test |
| `SPEC_VERSION` pins are consistent across canonical_decision and L0 dashboard | 3 version tests |
| Every module loads under its new qualified path | 18 parametrized package-import tests |
| 820 tests pass cumulatively | Full suite 48.05 s |

### 7.2 CONDITIONAL

| Claim | Condition |
|-------|-----------|
| Ownership invariants cover the full MIO / HTT boundary | These layers do not exist yet. When they land in W6+, the freeze tests will be extended to include `TestNoMIODirectPath`, `TestNoHTTToTSCDirectPath`. |
| P2-W4-01 whitelist stays small | Single entry today. Any new whitelist entry requires a documented P2 ticket and packet update. |
| Import-path rewrite captured all call sites | Verified indirectly by 820-test green run. Untested code paths (if any) would manifest as runtime ImportError on first execution. |

### 7.3 NOT ESTABLISHED (by design)

- MIO-facing and HTT-facing ownership invariants — deferred to when those layers exist
- Runtime protection against `CanonicalDecision` bypass via reflection (`type(x)(...)`) — AST
  inspection catches literal source calls only. Reflection-based bypass would require
  runtime sentinels, out of scope for W3.

---

## §8 — Self-audit

| Check | Status |
|-------|--------|
| All W1-W2 module content byte-identical after move | ✅ `git mv`-equivalent; no code edits inside the move step |
| Import rewrites preserve line count and indentation | ✅ regex-only substitutions |
| Two-pass pipeline documentation accurate | ✅ §4.1 / §4.2 |
| Whitelist entries tracked with P-level IDs | ✅ single entry, explicit P2-W4-01 |
| `conftest.py` at root enables pytest discovery | ✅ verified by 820 test pass |
| No regression against 772-test D5a baseline | ✅ |
| `test_ownership_freeze.py` parametrization covers all 10 packages | ✅ `EXPECTED_PACKAGES` tuple |
| Banned vocabulary absent | ✅ clean |

P0 / P1 findings: **0 / 0**.

---

## §9 — Week 3 closing summary

### 9.1 Daily throughput

| Day | Deliverable | Test delta | Cumulative |
|-----|-------------|------------|------------|
| D1 | `canonical_decision.py` + `validation_labels.py` | +47 | 627 |
| D2 | `beta_policy_gate` + `sigma_floor.py` + e2e wiring | +40 | 667 |
| D3 | `inverse_T_to_F_mc.py` + 1350-trial sweep + report | +36 | 703 |
| D4 | `species_tangency.py` (γ + 3ν flavors) | +40 | 743 |
| D5a | `precision_dashboard.py` (L0 gate, 21 checks) | +29 | 772 |
| D5b | Directory migration + `test_ownership_freeze.py` | +48 | 820 |
| **Week 3 net** | **6 new modules + L0 report + 48 invariants** | **+240** | **820** |

### 9.2 Architectural milestones locked

- **Single allow/block owner** (`bass/runtime/canonical_decision.py`) — W3D1
- **Deterministic 8-label emission** from 3 gate bools — W3D1
- **Three concrete gates** (β policy, Σ² floor, source $D_{\geq 2}$) with realistic inputs — W3D2
- **F ↔ T cycle closure** quantified at $10^{-9}$ typical, $10^{-7}$ worst-case across 27-cell product space — W3D3
- **Species-resolved diagnostic** over γ + 3ν — W3D4
- **L0 precision gate** passing at production seed — W3D5a
- **Ownership freeze** with AST-enforced invariants — W3D5b

### 9.3 Ladder / gate status

| Rung | Status | Gate verdict |
|------|--------|--------------|
| L0 (distribution-level) | Complete | ✅ PASS (21/21 checks green) |
| L1 (CAMB source bisection) | Not started | Scheduled W5 closing |
| L2 ($D_\ell$ hard gate) | Not started | Scheduled W6.5 |
| L3 (three-way consensus) | Not started | Scheduled W8 D4 |

### 9.4 Open items carried to W4

| ID | Description | Target |
|----|-------------|--------|
| P2-W4-01 | Move Prop 5 boost coefficients from `bass/validation/channel_routing.py` to `tsc/charts/boost_coefficients.py` | W4 early |
| W4 D1-D2 | Pastén Option B — Planck ε₁, ε₂ re-derivation | Already scheduled |
| W4 D3 | `bass/collision/thomson_tensor.py` skeleton | Already scheduled |
| W4 D4 | `bass/transport/ray_transport.py` skeleton | Already scheduled |
| W4 D5 | `entropy_invariants.py` (Thm 9/10/11) + `spherical_quadrature.py` (Lebedev) | Carried from W3 deferrals |

---

## §10 — Numerical ledger

| Quantity | Value |
|----------|-------|
| Week 3 new modules | 6 (canonical_decision, validation_labels, sigma_floor, inverse_T_to_F_mc, species_tangency, precision_dashboard) |
| Week 3 new tests | 240 |
| Cumulative tests | 820 |
| Full-suite runtime | 48.05 s |
| Directory migration target files | 34 (17 source + 17 test) |
| Import rewrite automated pipeline | 2 passes, 34 files touched |
| Manual fixes after automated pipeline | 1 (dotted-import → from-import) |
| Whitelist entries in ownership freeze | 1 (P2-W4-01) |
| W3 end target vs delivered | 775 vs 820 (**+45 over target**) |
| P0 / P1 findings across Week 3 | 0 / 0 |

---

## §11 — Next: W4 kickoff

Per v4.1 MERGED §4.3, Week 4 rolls:

| Day | Scope |
|-----|-------|
| D1 | Pastén Option B (part 1) |
| D2 | Pastén Option B (part 2) |
| D3 | `bass/collision/thomson_tensor.py` — axisymmetric Python skeleton |
| D4 | `bass/transport/ray_transport.py` — axisymmetric Python skeleton |
| D5 | TSC cleanup: `entropy_invariants.py` (Thm 9/10/11) + `spherical_quadrature.py` (Lebedev) + P2-W4-01 refactor |

The W4D3-D4 skeletons are the first real consumers of the W3 runtime machinery — every
collision RHS and transport step will call `require_allow_reduction(...)` gated on a
`CanonicalDecision`. W3's contract holds firm going forward.

---

**End of W3D5b packet and Week 3 close-out. Ready for W4 on approval.**
