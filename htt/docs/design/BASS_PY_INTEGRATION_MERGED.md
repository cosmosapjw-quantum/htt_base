# BASS-py Integration Plan — MERGED

**Date**: 2026-04-17
**Supersedes**: `BASS_PY_INTEGRATION_v4.md` (baseline), `BASS_PY_INTEGRATION_AMENDMENT_01.md`, ad-hoc v4.1 ownership refactor
**Combines**:
  - v4 baseline 10-week milestone structure
  - Amendment 01: precision ladder L0–L3 with hard gate at L2 and three-way consensus at L3
  - v4.1 ownership refactor: `bass/` vs `tsc/` split + `CanonicalDecision` runtime owner
**Design spec dependency**: `CANONICAL_DECISION_DESIGN.md` (blocker before revised W3D1)

---

## §1 What this document does

Two orthogonal amendments were drafted against v4: one for precision verification, one for architectural ownership. They do not conflict and neither subsumes the other. This merged document consolidates them into a single authoritative plan so that:

1. There is one schedule, not three overlapping ones.
2. The W6 gate semantics (duplicated between amendments) are defined once.
3. The retroactive classification of already-completed W1-W2 work is explicit.
4. Delivery timeline remains **10 weeks** with net **+0.5 day** from both amendments combined.

Anywhere this document disagrees with v4 baseline or either amendment in isolation, this document wins.

---

## §2 Ownership redistribution (from v4.1 refactor)

### 2.1 `bass/` vs `tsc/` split

| Layer | Owns | Does NOT own |
|-------|------|--------------|
| **bass/** | background geometry, transport, collision, tilt policy, validation, runtime decision, label emission | distribution-level chart math, Fisher/Laguerre inner products, tangency diagnostics |
| **tsc/** | Paper I Teff chart (Laguerre basis, forward F, boost), tangency diagnostics, realizability audit | allow/block verdicts, final label emission, runtime wiring |

The boundary derives from execution plan v3 §7 A1: BASS is the **sole allow/block owner**; TSC is a **mathematical chart** over distributions.

### 2.2 Module reclassification (W1-W2 completed work)

No code changes. Directory move executed at W3D5 freeze commit only.

| Module | Origin | New path |
|--------|--------|----------|
| `bianchi_types.py` | W1D1 | `bass/background/bianchi_types.py` |
| `shear_sources.py` | W1D2 | `bass/transport/shear_sources.py` |
| `comparator_policy.py` | W1D3 | `bass/validation/comparator_policy.py` |
| `einstein_bianchi.py` | W1D3 | `bass/background/einstein_bianchi.py` |
| `baryon_only_policy.py` | W1D4 | `bass/tilt/baryon_only_policy.py` |
| `channel_routing.py` | W1D5 | `bass/validation/channel_routing.py` |
| `laguerre_basis.py` | W2D1 | `tsc/charts/laguerre_basis.py` |
| `forward_F_to_T.py` | W2D2 | `tsc/charts/forward_F_to_T.py` |
| `tangency.py` | W2D3 | `tsc/diagnostics/tangency.py` |
| `boost_perturbative.py` | W2D4 | `tsc/charts/boost_perturbative.py` |
| `realizability.py` | W2D5 | `tsc/admissibility/realizability.py` |
| **`inverse_T_to_F.py`** | **W3D1 (v4)** | `tsc/charts/inverse_T_to_F.py` |

The `inverse_T_to_F.py` row is new: completed on 2026-04-17 under v4 baseline, retroactively classified as TSC chart layer. No logic change. See §8 for W3D1 packet retrofit.

---

## §3 Precision ladder (from Amendment 01)

Four levels, each with oracle, tolerance, and binding failure protocol. Unchanged from Amendment 01 §3–§6 except for one rename: the W6 gate is now universally called **L2 gate** (was duplicated as "W6.5 precision gate" in v4.1 refactor).

| Level | When | Oracle | Tolerance |
|-------|------|--------|-----------|
| **L0** | W3D5 epilogue | Analytic + ch05 cross-ref (no CAMB) | 10⁻¹⁰ analytic, 10⁻⁸ roundtrip |
| **L1** | W5 closing | CAMB source/transfer at $(k, \eta)$ | ±5% for $\ell \leq 30$ |
| **L2** | **W6.5 hard gate** | CAMB $D_\ell$ end-to-end + Σ² perturbative | **±2% for $\ell \in [2, 30]$** — sampling runs blocked until green |
| **L3** | W8 Phase 3 validation | bass-py ∥ Rust Track A ∥ Rust Track B with CAMB anchor | **±3% envelope** |

### 3.1 L2 gate criteria (all must pass — binding)

| Criterion | Target |
|-----------|--------|
| C1 | $D_\ell$ TT vs CAMB ±2% for $\ell \in [2, 30]$ |
| C2 | Σ²=10⁻⁸ perturbative linearization matches Fisher-linear prediction to ±10% |
| C3 | FLRW baseline $D_2$ within ±2% of CAMB |
| C4 | `WEEK6_PRECISION_REPORT.md` filed with RCA for any failed attempt |

### 3.2 L2 failure protocol (binding)

```
IF any of C1–C4 fails:
  HALT all sampling runs
  Bisect via L1 diagnostic
  Patch and re-run L0 → L1 → L2 sequentially
  Log every failed attempt
  NO sampling runs until L2 green
  Gate re-review requires PHYS-MATH + PHYS-MATH-CODE audit
```

Bypassing this protocol is a retroactive P0 finding.

---

## §4 Revised schedule (Week 3 onward)

v4 baseline W1 and W2 are complete. Below tracks the Week 3–Week 10 deltas.

### 4.1 Week 3 — most-changed week

| Day | v4 baseline (retired) | v4.1 MERGED |
|-----|----------------------|-------------|
| D1 | `inverse_T_to_F.py` | `bass/runtime/canonical_decision.py` (18 tests) |
| D2 | roundtrip + MC sweep | `bass/runtime/validation_labels.py` (15 tests) |
| D3 | `entropy_invariants.py` | `tsc/charts/inverse_T_to_F.py` **move** + **MC sweep absorbed from v4 D2** (~40 tests) |
| D4 | `species_tangency.py` | `tsc/diagnostics/species_tangency.py` (γ + 3ν flavors, ~40 tests) |
| D5 | `spherical_quadrature.py` | **split**: D5a = L0 precision dashboard + D5b = ownership freeze commit (total ~32 tests) |

### 4.2 Deferred to Week 4

- `entropy_invariants.py` (Thm 9/10/11) → W4D5
- `spherical_quadrature.py` (Lebedev) → W4D5

### 4.3 Week 4 — reconfigured

| Day | Scope |
|-----|-------|
| D1 | Pastén Option B — Planck ε₂, ε₃ re-derivation (part 1) |
| D2 | Pastén Option B (part 2) |
| D3 | `bass/collision/thomson_tensor.py` — axisymmetric Python skeleton |
| D4 | `bass/transport/ray_transport.py` — axisymmetric Python skeleton |
| D5 | TSC cleanup: `entropy_invariants.py` + `spherical_quadrature.py` |

### 4.4 Week 5 — closing gate added

Forward model strata S1–S4 unchanged. Closing day adds **L1 precision gate**:
- `l1_source_comparison.py` utility: extract bass-py source terms vs CAMB `get_source_function` point-by-point
- Target ±5% at $\ell \leq 30$, localize failures to ODE / source / visibility layer
- Gate fail → halt W6 entry

### 4.5 Week 6 — L2 hard gate inserted

| Day | Scope |
|-----|-------|
| D1 | Likelihood infrastructure (dynesty setup, priors) |
| D2 | Likelihood infrastructure (priors + sanity runs) |
| **D2.5** | **L2 precision gate (binding)** — C1–C4 + `WEEK6_PRECISION_REPORT.md` |
| D3–D5 | 32 nested sampling runs (begin ONLY after L2 green) |

### 4.6 Week 7 — unchanged

Phase 3 full 10-type $a_{\ell m}$ forward pipeline. All callers route through `bass/runtime/canonical_decision.py` (~50 LoC wiring).

### 4.7 Week 8 — L3 three-way consensus added

| Day | Scope |
|-----|-------|
| D1–D3 | Phase 3 validation sweep |
| D4 | **L3 three-way run**: bass-py FLRW vs Rust Track A vs Rust Track B vs CAMB anchor |
| D5 | L3 envelope report, manuscript numbers freeze |

### 4.8 Week 9–10 — figures + manuscript

Unchanged, with the proviso: figures may not claim precision beyond the L3-established envelope.

### 4.9 Net schedule impact

| Source | Days |
|--------|------|
| v4.1 ownership refactor | +0 (absorbed in W3 restructure) |
| L0 dashboard (W3D5a) | +0 (half-day) |
| L1 gate (W5 closing day) | +0 (absorbed in closing day) |
| L2 gate (W6D2.5) | +0.5 |
| L3 three-way (W8D4) | +0 (absorbed in W8) |
| **Total net** | **+0.5 day** |

---

## §5 Acceptance criteria (merged from both amendments)

| ID | Criterion | Source |
|----|-----------|--------|
| A1' | allow/block owner is `bass/runtime/canonical_decision.py` only | v4.1 refactor |
| A2' | `global_tilt` (MIO) vs `local_boost_patch` (HTT) field separation | v4.1 refactor |
| A3' | `source adequate, propagation pending` expressible via label combo | v4.1 refactor |
| A4' | `sigma_min_above_floor` check required before inverse map use | v4.1 refactor |
| A5' | TSC language bounded to "intensity-side exact source hook" | v4.1 refactor |
| A6' | L2 precision gate must pass before any figure with quantitative claim | Amendment 01 §8 |
| **PA1** | L0 all-green before W4 entry | Amendment 01 L0 |
| **PA2** | L1 all-green before W6 entry | Amendment 01 L1 |
| **PA3** | L2 all-green (C1–C4) before sampling runs | Amendment 01 L2 + v4.1 §3.1 |
| **PA4** | L3 envelope ≤ ±3% reported in manuscript | Amendment 01 L3 |
| **PA5** | Every precision claim in manuscript traces to an L-level + explicit oracle | Amendment 01 §8 |

---

## §6 Non-claims (explicit, binding)

| Non-claim | Authority |
|-----------|-----------|
| "Python bass-py is a full nonperturbative solver" | execution plan §2.3 |
| "TSC closes full polarization" | execution plan §5.4 D |
| "Tier A 3D angular PDE implemented in Python" | Rust domain (user-stated) |
| "TSC decides runtime allow/block" | execution plan §7 A1 |
| "Teff suffices for BB trace semantics" | execution plan §5.4 D |
| "bass-py agrees with CAMB" without L-level attribution | PA5 |
| "Precision established" without reporting L3 envelope | PA4 |

---

## §7 Risk register (merged)

| Risk | Pre-merge | Post-merge status |
|------|-----------|-------------------|
| TSC treated as runtime owner | HIGH | ELIMINATED (ownership test) |
| No final allow/block owner | HIGH | RESOLVED (`canonical_decision.py`) |
| BASS runtime core empty | HIGH | PARTIALLY RESOLVED (Python skeleton W3-W4) |
| Likelihood run without precision evidence | HIGH | RESOLVED (L2 binding gate) |
| Rust duplication/conflict | MEDIUM | ELIMINATED (Python axisymmetric only) |
| Tier A Python attempt | n/a | EXPLICITLY FORBIDDEN (§6) |
| Precision claim without oracle attribution | MEDIUM | RESOLVED (PA5) |
| `CanonicalDecision` interface bitrot before W6 consumer exists | NEW — MEDIUM | `SPEC_VERSION` pin + W6 entry re-audit |
| `TSC` nomenclature undefined | NEW — LOW | `CANONICAL_DECISION_DESIGN.md` §2 pins semantics; full execution plan v3 CRAG deferred |

---

## §8 W3D1 (v4) → W3D3 (merged) retrofit

The work completed on 2026-04-17 is retroactively classified as follows:

| v4 attribution | Merged attribution |
|----------------|---------------------|
| Module: `inverse_T_to_F.py` at repo root | `tsc/charts/inverse_T_to_F.py` (move at W3D5) |
| Packet: `WEEK3_DAY1_PACKET.md` | Remains as W3D1(v4) artifact + retrofit note |
| 48 tests accepted, cumulative 580 | Unchanged — these 48 land under W3D3 in the merged schedule |
| Roundtrip closure scope | Present at smoke-test level (5 roundtrip tests in `TestRoundtripClosure`); **full MC sweep still owed** — lands in merged W3D3 |

**Retrofit action**: add a header section to `WEEK3_DAY1_PACKET.md` noting reclassification. No code change. Directory move executes at W3D5b freeze commit, not now.

The original v4 W3D2 scope (roundtrip MC sweep, ~40 tests) is absorbed into merged W3D3, alongside the directory move itself. Merged W3D3 is therefore a combined "move-and-harden" day.

---

## §9 Immediate action queue

In order, from now:

1. **[BLOCKER]** Approve `CANONICAL_DECISION_DESIGN.md`
2. Approve this merged plan document
3. Add retrofit note to `WEEK3_DAY1_PACKET.md`
4. **Start merged W3D1**: implement `bass/runtime/canonical_decision.py` per design spec
5. Merged W3D2: `bass/runtime/validation_labels.py`
6. Merged W3D3: inverse_T_to_F move + MC sweep (absorbs today's scope + original W3D2 scope)
7. Merged W3D4: species_tangency
8. Merged W3D5a: L0 dashboard; W3D5b: ownership freeze commit

Expected cumulative test count at end of revised W3: **~725** (currently 580, +~145 over D1–D5).

---

## §10 CRAG-pending items

These reference documents need integration when shared:

| Doc | Content consumed | Priority |
|-----|------------------|----------|
| `BASS_MIO_HTT_execution_plan.md` v3 | TSC definition, 8-label semantics, §6 D3 emission rules, §7 A1–A6 | HIGH (W5 entry) |
| Rust BASS Track A σ̇ precision report | L3 oracle values at $\ell = 2, 100$ | MEDIUM (W8) |
| CAMB v1.6.6 `get_source_function` API | L1 oracle implementation | HIGH (W5 closing) |

Until CRAG integration, SSOT for these items is `CANONICAL_DECISION_DESIGN.md` §2 for label inputs.

---

## §11 Version & amendment history

| Version | Date | Change |
|---------|------|--------|
| v4 | 2026-04-15 | Baseline approved |
| v4 + Amendment 01 | 2026-04-17 | L0–L3 precision ladder (proposed) |
| v4.1 refactor draft | 2026-04-17 | `bass/` vs `tsc/` + `CanonicalDecision` (proposed) |
| **v4.1 MERGED (this doc)** | **2026-04-17** | **Integration of both amendments** |

On approval, this document becomes the authoritative baseline. The prior three version labels are archived references.

---

**End of merged plan. Awaits two approvals: (1) `CANONICAL_DECISION_DESIGN.md`, (2) this document.**
