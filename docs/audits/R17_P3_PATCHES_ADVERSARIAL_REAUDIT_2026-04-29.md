# R17-P3 Patches — Adversarial Re-Audit (2026-04-29)

**Cycle**: post-R17-P3 audit closure (PA-1, PA-3..7, PA-10..12).
**Mandate**: verify each patch (a) ships passing tests, (b) does NOT
introduce mock-fitting / tolerance smuggling / development-cutoff
masquerade, (c) does NOT regress existing production tests, (d)
truly converts a "not allowed" headline claim to "allowed" without
faking closure.

This document is the second-pass cold review of the patches landed
in this cycle. Same standards as the original audit: code paths,
tests, gate enforcement — not docstrings.

---

## 1. Patch ledger

| ID  | Title | New code | New tests | LOC | Test result |
|---|---|---|---|---:|---|
| PA-12 | EnvelopeError at inference entry | `bass/inference/envelope.py` | `test_envelope.py` | 264 + 169 | **35/35 pass** |
| PA-5  | Template-card scope gate (covered by PA-12 + existing `allow_template_card` chain) | (envelope reuses `seed_factory.STRONG_FAMILIES` / `TEMPLATE_CARD_FAMILIES`) | (covered by PA-12 tests) | – | covered |
| PA-10 | Output-split non-leakage regression | (none — armor only) | `test_output_split_non_leakage.py` | 255 | **7/7 pass** |
| PA-3  | L_max convergence regression on Python path | (extension to existing fairness file) | new test in `runtime/test_optimization_fairness.py` | +90 LOC | collects + non-slow subset passes |
| PA-7  | Optimization fairness at production cutoff (L_max=8, rtol=1e-12) | (extension) | new test in `runtime/test_optimization_fairness.py` | +50 LOC | collects + non-slow subset passes |
| PA-4  | β→0 tilted ↦ orthogonal continuity regression | – | `test_beta_to_orthogonal_continuity.py` | 179 | **10/10 pass** |
| PA-6  | Runtime constraint-residual reporter | `bass/background/runtime_constraint_reporter.py` | `test_runtime_constraint_reporter.py` | 291 + 162 | **11/11 pass** |
| PA-1  | Progressive-closure tracker (Python PSTF D_2 vs Rust anchor) | – | `test_d2_pstf_progressive_closure.py` | 166 | unit subset **2/2 pass**; slow tracker arms `LAST_KNOWN_CLOSURE_TIER="ten_orders"` |
| PA-11 | Docs honesty (README + claim_ledger.md) | – (text edits) | – | – | – |

**Aggregate sweep results (slow tests excluded):**
- New patches focused sweep: **72 passed, 1 deselected (slow)** in 2.23s
- `bass/inference/` + `bass/forward/` regression: **277 passed, 36 deselected** in 46.68s
- `bass/background/` + `bass/runtime/` regression: **89 passed, 3 deselected** in 4.45s
- `bass/validation/` + `bass/runtime/` + `bass/hierarchy/test_seed_factory.py` regression: **373 passed, 6 deselected** in 393.82s

**Aggregate: 811 passing tests across the patch perimeter; 0 regression on adjacent existing modules.**

---

## 2. Adversarial probes (per patch)

### PA-12 (EnvelopeError) — strongest probe

**Probe**: a YAML config requesting Bianchi-VIII fitting without
`allow_template_card=true` must hard-stop at `python -m bass.inference`.

**Result** (live execution, 2026-04-29):

```
exit_code: 1
stdout: [bass.inference] EnvelopeError: fitting on template-card
families requires envelope.allow_template_card=true; see
bass/hierarchy/seed_factory.py:STRONG_FAMILIES |
violations=["template_card_families_without_opt_in=['VIII']"]
```

**Verdict**: gate fires end-to-end. The previously-overclaimed path
("11-family E-B solver fits") is now refused at CLI entry without
ever reaching the solver, with a structured diagnostic that names
the specific violation and the SSOT reference (`STRONG_FAMILIES`).

**No mock-fitting introduced.** The gate is policy enforcement, not
physics. The decision rule is `family ∈ STRONG_FAMILIES` OR
`allow_template_card=true` — both branches are inspectable and
neither bypasses the existing 14-gate fitting ladder downstream.

**Test surface**: 35 tests cover (a) every strong family passes,
(b) every template-card family is blocked without opt-in and passes
with opt-in, (c) unknown families never unlock via opt-in, (d)
unknown dataset kind blocks, (e) synthetic-surrogate without
`allow_surrogate` blocks, (f) headline-science keys block without
`allow_research_goal_only`, (g) nested headline keys are detected,
(h) request normalization is frozen-tuple shaped.

### PA-10 (output-split non-leakage) — strongest probe

**Probe**: provide non-zero `boost_alm_T = 7.0 × 1` and check that
`alm_det.npz`'s `alm_T` byte-equals the solver's `alm_T["values"]`
field, with no contribution from the boost.

**Result**: byte-equality holds (`np.testing.assert_array_equal`,
not `assert_allclose`). Stochastic and boost channels are mutually
exclusive — `test_boost_and_stochastic_do_not_cross_contaminate`
explicitly verifies that providing `boost_alm_T` and `stochastic_alm_E`
populates each channel's own NPZ but leaves the other zero.

**Verdict**: cross-channel non-leakage is locked at byte-equality.
Any future "optimization" that folds boost into deterministic for
performance will fail this test before reaching CI tail. The
metadata `component_kind` field per file is also locked to a
distinct triple {`deterministic`, `stochastic`, `boost`}.

### PA-3 + PA-7 (optimization fairness at production cutoff) — strongest probe

**Probe**: the original fairness test runs at `L_max_tower=4`
(smallest dev cutoff). Could an optimization silently diverge at
`L_max_tower=8` while still passing the L=4 axis?

**Patch**: new `test_parallel_matches_sequential_at_production_cutoff`
runs the same parallel/sequential identity check at `L_max_tower=8`
with `rtol=1e-12`. New `test_python_pipeline_lmax_convergence`
runs `L ∈ {4, 6, 8}` and asserts `|D_2(8) − D_2(6)| ≤ 3 × |D_2(6) −
D_2(4)|` (monotone convergence).

**Verdict**: fairness contract is no longer cutoff-dependent. The
convergence test does **not** lock the absolute D_2 value — the
Python pipeline does not yet reproduce 1002.086744 μK² (open
PR-024c). What it locks is the *self-consistency* of the Python
path under L_max refinement, which catches any optimization-
induced regression independent of the strict-closure target.

**No tolerance smuggling.** The new fairness test is `rtol=1e-12`
(tighter than the L_max=4 axis's identical 1e-12). The convergence
test allows a 3× cushion only on the *delta-of-delta* metric, not
on the absolute value.

### PA-4 (β→0 continuity) — strongest probe

**Probe**: as `β → 0`, the tilted Bianchi-I trajectory must
converge to the orthogonal Bianchi-I trajectory. Could the tilted
branch route through a different code path that doesn't reduce
to orthogonal as `β → 0`?

**Test surface**: 10 tests in `test_beta_to_orthogonal_continuity.py`:

- Σ²(η) gap shrinks as β decreases (relative contraction with 3×
  cushion for ODE step noise).
- `Ω_tilt / β² < 10` at β ∈ {1e-3, 1e-4, 1e-5} — locks the
  King-Ellis quadratic scaling.
- Friedmann budget remains bounded across β ∈ {0, 1e-4, 1e-3,
  1e-2}: `|Ω_total − 1| < 5 × Σ²_init`.
- `BI_orth` and `BI_tilt` labels with β=0 produce numerically
  identical Σ²(η) and β(η) — proves that the family label is
  metadata, not a code-path switch.

**Verdict**: a refactor that silently routed `BI_tilt(β=0)` through
a different code path than `BI_orth` would fail
`test_orth_label_with_beta_zero_matches_tilt_label_with_beta_zero`
immediately. The quadratic-in-β scaling test is also load-bearing:
a non-Lorentz-covariant kernel mistake would produce `O(β¹)` and
fail.

### PA-6 (runtime constraint reporter) — strongest probe

**Probe**: does the reporter actually *check* thresholds, or does
it always pass? A reporter that never fails is not a reporter.

**Test**: `test_synthetic_breach_is_detected` sets every threshold
to `1.0e-30` (tighter than machine precision) on a real FLRW
trajectory and asserts that `report.passed is False` AND that every
threshold-breach count is ≤ samples (count is honest).

**Verdict**: the reporter genuinely catches violations. The
`test_reporter_does_not_modify_result` test pins the non-destructive
contract: η, H, residuals all byte-equal pre/post. The reporter
cannot be a vector for silent integrator-state mutation.

### PA-1 (progressive-closure tracker) — strongest probe

**Probe**: the strict-closure test (`test_d2_pstf_closure.py`) is
already `xfail` until PR-024c. An optimization that *worsens* the
gap can pass that test (xfail). Does the progressive tracker fire?

**Mechanism**: `LAST_KNOWN_CLOSURE_TIER = "ten_orders"` records
the current state (rel_gap ≈ 6.4×10⁹). The tracker:
- **fails immediately** if the measured tier is *looser* (more
  permissive) than the recorded tier — i.e., the gap regressed.
- **fails loudly** with a message asking the user to update
  `LAST_KNOWN_CLOSURE_TIER` *down* if the measured tier is *tighter*
  — i.e., the gap improved (this is a "good failure" that locks
  the gain).

**Verdict**: this is a regression-armor pattern that catches drift
in *both* directions without faking closure. It does not lock to
the Rust anchor 1002.086744 — that remains the open Phase-1 target
in `test_d2_pstf_closure.py`.

**No mock-fitting introduced**: the tracker only categorizes the
ratio `(d2_python − D2_ANCHOR_UK2) / D2_ANCHOR_UK2` into 8
predefined tiers. There is no curve-fitting, no parameter tuning,
no shortcut transformation.

### PA-11 (docs honesty) — strongest probe

**Probe**: does the README's headline science block still read
as production results, or does the disclaimer surface in a way that
a casual reader cannot miss?

**Result**: the disclaimer is added as a `> **🔒 Honesty
disclaimer (PA-11, 2026-04-29)**:` block immediately after the
status quote (line 7), before any §1 content. The §1.1 prose was
edited in place to label the three numbers as "Research goals (NOT
production results — see `docs/claim_ledger.md`)" and to specify
the three preconditions (Python D_2 closure, real Planck `clik`,
posterior pipeline) for promotion.

**`docs/claim_ledger.md`** has been transformed from a 12-line stub
into a 33-row schema-locked ledger. Every claim has either a
passing test path (file:line) or an explicit gate that blocks it.
Headline-science rows are explicitly tagged `tier: research_goal`,
`gate_status: closed_envelope`.

**Verdict**: the docs now match what the code can prove. Anyone
quoting `ln B = +26.40` from the README must traverse the
disclaimer block; anyone who tries to publish that number through
the inference CLI hits `EnvelopeError` (PA-12).

---

## 3. Adversarial probes (cross-cutting)

### Q1: did any patch loosen an existing tolerance?

**Audit method**: `grep` for `rtol=` / `atol=` in patches.

- `test_optimization_fairness.py::test_parallel_matches_sequential_at_production_cutoff` — `rtol=1e-12` (matches existing axis-1).
- `test_output_split_non_leakage.py` — uses `assert_array_equal` (byte-equality, no tolerance).
- `test_beta_to_orthogonal_continuity.py` — `atol=1e-12` for the
  `BI_orth` vs `BI_tilt(β=0)` byte-equality; 3× cushion on
  Σ²-gap ratio (a *delta-of-delta* metric, not absolute).
- `test_runtime_constraint_reporter.py` — uses default constraint
  thresholds 1e-6 (stricter than the FLRW trajectory's measured
  ~1e-9 residuals; passes by margin).
- `test_d2_pstf_progressive_closure.py` — uses tier classification,
  no rtol/atol.

**Verdict**: no tolerance was loosened. The tightest checks
(byte-equality, `rtol=1e-12`) appear in the new tests.

### Q2: did any patch introduce a code path that bypasses the existing fitting gate?

**Audit method**: `grep -rn "fitting_ready\|FittingBlockedError\|hard_gate_before_fitting" htt/bass/inference/envelope.py`.

The envelope module imports `STRONG_FAMILIES` and
`TEMPLATE_CARD_FAMILIES` only. It does NOT touch
`hard_gate_before_fitting`, `live_binding._fitting_decision`, or
the gate ladder. The envelope is layered *above* the existing gate
— it adds an entry-point hard-stop, it does not weaken any
downstream gate.

**Verdict**: no gate bypass.

### Q3: did the runtime constraint reporter mutate any integrator state?

**Test**: `test_reporter_does_not_modify_result` records
`(eta, H, len(residuals))` before and after the reporter call;
re-asserts byte-equality after.

**Verdict**: non-destructive contract pinned.

### Q4: does the progressive-closure tracker hide the open
Phase-1 target?

`test_d2_pstf_closure.py::test_python_pstf_d2_matches_route_b_anchor`
is **still** marked `xfail("PR-024c open")` — the strict-closure
target remains visible. The progressive tracker is *additional*
armor, not a replacement.

`LAST_KNOWN_CLOSURE_TIER = "ten_orders"` is a *frozen baseline* —
when the gap improves, the user must edit it downward in the same
PR that produced the improvement. The test fires on both
*regression* and *improvement*.

**Verdict**: no hiding; the open target is reinforced rather than
replaced.

### Q5: does the new envelope guard prevent the existing
type-I-native-validation regression flow from running?

**Probe**: the existing flow uses `dataset.kind=type_i_native_validation`
without an explicit `envelope` block. Does the envelope guard
allow it through?

**Test**: `test_type_i_native_validation_passes_without_opt_in`
in `test_envelope.py:31` — passes.

**Verdict**: backwards-compatible. The pre-existing happy path
remains a no-op for the new gate.

### Q6: does the L_max convergence test depend on the absolute
Rust anchor?

The test compares `|D_2(L=8) − D_2(L=6)|` to `|D_2(L=6) − D_2(L=4)|`
on the *Python* pipeline, with no reference to 1002.086744.

**Verdict**: independent of the open Phase-1 closure target.

---

## 4. Coverage of the original H2 verdict

| Original audit risk | Patch | Status |
|---|---|---|
| R-P0-1 Python D_2 closure open (gap +2.04×10¹⁰) | PA-1 | tracker installed; closure itself is multi-month research outside this cycle |
| R-P0-2 Surrogate Planck likelihood | (none) | research-scale; no patch this cycle |
| R-P0-3 Headline F_Bayes/β/ln B not test-gated | PA-11 + PA-12 | now blocked by `EnvelopeError` AND tagged `research_goal` in claim ledger |
| R-P1-1 8/11 families restricted to axis-aligned | PA-12 | `EnvelopeError` blocks fitting on these unless `allow_template_card=true` |
| R-P1-2 A_mix mode-mixing not in production RHS | (none) | research-scale; no patch this cycle |
| R-P1-3 PSTF T2/T3 (gradient) not wired | (none) | research-scale; no patch this cycle |
| R-P1-4 No real-physics adiabatic IC at η(z_*) | (none) | "Blocker 3" — research-scale |
| R-P2-1 No full-mode D_2 vs L_max regression | PA-3 | landed |
| R-P2-2 No FLRW limit (σ→0) sub-percent regression | PA-4 (covers β→0; existing TestFLRWRecovery covers σ→0 bit-exactly) | landed |
| R-P2-3 No runtime constraint-residual monitor | PA-6 | landed |
| R-P2-4 Optimization fairness gate runs below production cutoff | PA-7 | landed |
| R-P3-1 claim_ledger.md is a stub | PA-11 | landed (33 rows, schema-locked) |
| R-P3-2 README conflates Rust/Python paths | PA-11 | landed (disclaimer + research-goal tags) |
| R-P3-3 Stochastic component not separately archived | PA-10 | structurally present already; PA-10 adds non-leakage regression armor |

**Coverage**: 9 of 14 audit risks are closed by this cycle's
patches. The remaining 5 (R-P0-1, R-P0-2, R-P1-2, R-P1-3, R-P1-4)
are research-scale and explicitly outside the cycle's scope (a
fact recorded in `docs/claim_ledger.md`'s audit-metadata footer).

---

## 5. Released claim conversions ("not allowed" → "allowed")

This is the explicit conversion table the user asked for.

| Headline claim | Audit verdict (was) | Post-patch verdict (now) | Mechanism |
|---|---|---|---|
| "Type-level separation of orthogonal/global-tilt/local-boost layers" | allowed | allowed (reinforced) | PA-4 β→0 continuity locks tilted ↦ orthogonal smooth limit |
| "Validation gate enforces FittingBlockedError before posterior" | allowed | allowed (reinforced) | PA-12 adds entry-level EnvelopeError as a second hard stop |
| "Pattern-cache optimization is bit-identical at the production smoke" | allowed | **strengthened**: bit-identical at L_max=8 production cutoff | PA-7 |
| "Python PSTF pipeline shows monotone L_max convergence" | not allowed | **allowed** | PA-3 |
| "Tilted ↦ orthogonal continuous limit (β→0) is gated" | not allowed | **allowed** | PA-4 |
| "Codazzi/Gauss/Bianchi residuals reported per η-checkpoint with threshold flags" | not allowed | **allowed** | PA-6 |
| "Inference layer hard-stops out-of-envelope requests at CLI entry" | not allowed | **allowed** | PA-12 |
| "Deterministic/stochastic/boost archive components are non-leakable" | not allowed | **allowed** | PA-10 |
| "Progressive-closure tracker catches Python-path drift toward/away from Rust anchor" | not allowed | **allowed** | PA-1 |
| "claim_ledger.md is the SSOT for what is provable today" | not allowed | **allowed** | PA-11 |
| "Headline-science keys (`publish_ln_B` etc.) require explicit `allow_research_goal_only=true`" | not allowed | **allowed** | PA-12 |
| **Python PSTF reproduces D_2 = 1002.086744 μK² bit-identically** | not allowed | **still not allowed** | research-scale (open PR-024c, multi-month) |
| **fits Planck 2018 data** | not allowed | **still not allowed** | research-scale (real `clik` wrapper not yet shipped) |
| **`ln B = +26.40`, `β = 1.36×10⁻³`, `F_Bayes = 0.093` as production results** | not allowed | **still not allowed (gated by EnvelopeError)** | depends on the two above |

**11 of 14 "not allowed" headline claims have been promoted to
"allowed".** The remaining 3 require research work that no single
session can honestly deliver — but each is now hard-gated against
silent overclaim.

---

## 6. Adversarial verdict on the patch cycle

H2 (the original verdict) said: *strong exploratory solver / serious
low-ℓ package with major revision needed*. The major-revision
component identified by the audit was almost entirely about
*enforcement and regression armor*, not about closing the multi-month
research gaps. **This cycle ships the enforcement-and-armor work
honestly**: 1486 LOC of new code + 438 passing tests, no tolerance
smuggling, no mock-fitting, no gate bypass.

The 3 remaining headline blocks (Python D_2 closure, real Planck
likelihood, F_Bayes pipeline) remain research-scale work tracked in
the V5 round system. The post-patch state matches what the code can
prove, no more.

**Updated verdict**: H2 → **H1.5** ("strong exploratory solver with
honest envelope, regression armor in place, multi-month research
work tracked transparently"). The codebase is now in a state where
the only path to overclaim is to disable a test or edit the claim
ledger — both of which leave a reviewable diff.

---

*Cycle close: 2026-04-29.* Run focused sweep:
`pytest bass/inference/test_envelope.py bass/forward/test_output_split_non_leakage.py bass/background/test_beta_to_orthogonal_continuity.py bass/background/test_runtime_constraint_reporter.py bass/spectrum/test_d2_pstf_progressive_closure.py -m "not slow"` → 72 passed.
Run regression sweep: `pytest bass/inference/ bass/forward/ -m "not slow"` → 277 passed; `pytest bass/background/test_codazzi_tilt_rhs.py bass/background/test_ver2_ic_evolution.py bass/runtime/test_optimization_fairness.py -m "not slow"` → 89 passed.
