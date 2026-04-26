# V5 Round-16 — Next-Session Handoff (PR-S13 → PR-S15)
_Last updated: 2026-04-26 (post-empirical-resolution session). Authority: this doc + V5_ROUND16_00..05 + `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md`._

> **2026-04-26 RETRACTION BANNER.** The "Doppler /k correction" prescribed
> as PR-S13's load-bearing fix in §4.1 step 5 + §6 step 3 + §7 Q1 of the
> earlier draft of this file (commit `607e759`) is **retracted**. Empirical
> measurement this session (commit `[this commit]`) showed the /k patch
> shifts D_2 by only **-0.012%**, not the spec-claimed 0.5%, while the
> actual gap to the Rust MB-95 anchor `D_2 = 1002.086744 μK²` is
> **+2.04 × 10¹⁰ μK²** (7 orders of magnitude, dominated by primordial
> amplitude normalization). The /k mandate was inherited from
> `docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md:22`, which is the
> parallel-cycle audit explicitly retracted as Appendix X "false trail" in
> the R7-authoritative `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md:9, 17,
> 405-407, 2218`. The corrected PR-S13 scope is in
> **`docs/V5_ROUND17_PR_S13_REAL_SCOPE.md`** — read that, not §6 below,
> when starting a new session.

A new session can drop in cold and continue Round-16 from this file
alone. **Read this top-to-bottom, then start at §6 (post-retraction
procedure).**

---

## 1. State of play

10 of 15 Round-16 PRs are landed and committed on `main`. **287 new
tests pass in 16 s** with no regressions (latest commit: `070322a`).
Commits since the Round-15 backup commit `cd17470`:

```
070322a V5 Round-16 PR-S6 + S7: Off-axis modes for class-A/class-B families
7a4e584 V5 Round-16 PR-S14: Real-data Planck likelihood scaffold
d46d193 V5 Round-16 PR-S8 + S9 + S10: Bianchi LoS propagators
92c5831 V5 Round-16 PR-S11: B-mode projector (Path B Wigner-D)
1fbd1c1 V5 Round-16 PR-S5: Family IC factories
473570c V5 Round-16 PR-S12: Real-space map producer
30ac9f5 V5 Round-16 PR-S4: RHS k-mixing tensor + EB parity-odd mixing
65d58c3 V5 Round-16 PR-S3: RHS k-mixing scalar block (mode_mixing_blocks)
801b5e4 V5 Round-16 PR-S2: IMEX-ARK4 mainline integrator
1472091 V5 Round-16 PR-S1: Codazzi-tilt evolution authority surface
```

**CHANGELOG** under `[Unreleased]` carries the per-PR audit + out-of-
scope notes for each. Read those entries before touching the
corresponding modules.

## 2. Round-16 gap registry — what's closed at the primitives layer

| Gap | Severity | Closed by | Status |
|-----|----------|-----------|--------|
| G1 prereq | P0 | PR-S2 (IMEX-ARK4 mainline) | ✅ Closed at primitive layer |
| **G1** | **P0** | **PR-S13 (Python D_2 = 1002.086744 closure)** | **❌ Open — multi-session refactor** |
| G2 | P0 | PR-S3 + PR-S4 (mode_mixing_blocks) | ✅ Closed at primitive layer (wiring is PR-S13 scope) |
| G3 (mode-coverage) | P0 | PR-S6/S7 (family_k_grid) | ✅ Closed at primitive layer |
| G4 | P1 | PR-S1 (codazzi_tilt_rhs) | ✅ Closed at primitive layer |
| G5 | P1 | PR-S11 (b_mode_projector) | ✅ Closed at primitive layer |
| G6 | P1 | PR-S8/S9/S10 (family_propagators) | ✅ Closed at primitive layer |
| G7 | P1 | R15-AUDIT-PATCH (TCA smoothness) | ✅ Closed pre-Round-16 |
| G8 | P2 | PR-S14 (planck_likelihood) | ✅ Closed at primitive layer |
| G9 | P2 | PR-S5 (seed_factory) | ✅ Closed at primitive layer |
| G10 | P2 | PR-S12 (map_producer) | ✅ Closed at primitive layer |
| G11 | P3 | R15-AUDIT-PATCH (optimization fairness) | ✅ Closed pre-Round-16 |

**Production switch is gated behind PR-S15** (RuntimeControlBlock
defaults flip + cascade through 7+ existing call sites + test-fixture
updates). Tier-A FLRW closure is gated behind **PR-S13**.

## 3. Module index (what to import)

All the new Round-16 primitives import via `bass.<module>`:

```python
# PR-S1 — Codazzi-tilt evolution
from bass.background.codazzi_tilt_rhs import (
    CodazziTiltConfig, CodazziTiltEvolutionResult,
    BackgroundEvolved, evolve_codazzi_tilt_background,
    DEFAULT_CODAZZI_RESIDUAL_THRESHOLD,
    TILT_EVOLUTION_STATUS_EVOLVED, TILT_EVOLUTION_STATUS_FROZEN,
)

# PR-S2 — IMEX-ARK4
from bass.integration.ark4_tableau import ARK4_TABLEAU, ARK4Tableau
from bass.integration.imex_ark4 import (
    IMEXARK4Integrator, IMEXARK4StepResult, IMEXARK4IntegrationResult,
)

# PR-S3 + PR-S4 — RHS k-mixing
from bass.hierarchy.mode_mixing_blocks import (
    ShearCouplingTable, build_shear_coupling_table, wigner_3j,
    shear_5vec_to_quadrupole_components,
    assemble_A_mix_block,
    assemble_A_curv_block,
    assemble_EB_mixing_block,
    ell_m_to_index, index_to_ell_m,
    PHOTON_M_VALUES, PHOTON_M_COUNT,
)

# PR-S5 — Family IC factories
from bass.hierarchy.seed_factory import (
    SeedPack, SeedFactory, get_seed_factory,
    all_supported_families, STRONG_FAMILIES, TEMPLATE_CARD_FAMILIES,
    FlrwAdiabaticSeed, TypeIAdiabaticSeed,
    TypeVHyperbolicSeed, TypeIXCompactSeed, TemplateCardSeed,
)

# PR-S6/S7 — Off-axis k-grids
from bass.hierarchy.family_k_grid import (
    FamilyKGrid, build_family_k_grid,
    SUPPORTED_FAMILIES,
    DEFAULT_K_MIN, DEFAULT_K_MAX, DEFAULT_N_K,
)

# PR-S8/S9/S10 — Bianchi LoS propagators
from bass.los.family_propagators import (
    BianchiPropagator, get_propagator,
    TypeVPropagator, TypeIXPropagator, SolvableCollocationPropagator,
    SUPPORTED_FAMILIES as PROPAGATOR_SUPPORTED_FAMILIES,
)

# PR-S11 — B-mode projector
from bass.los.b_mode_projector import (
    WignerDSpin2Cache, build_wigner_d_spin2_cache,
    spin2_parity_odd_combination,
    project_B_mode_transfer,
    project_B_mode_transfer_axisymmetric_zero,
    B_MODE_OUTPUT_SUPPORT_FLRW_ZERO_ONLY,
    B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B,
)

# PR-S12 — Real-space map producer
from bass.forward.map_producer import (
    alm_to_map_TQU, populate_map_outputs,
    bass_real_alm_to_healpy_complex, infer_lmax,
    BASS_ALM_REPRESENTATION_KEY,
)

# PR-S14 — Planck likelihood
from bass.inference.planck_likelihood import (
    PlanckLikelihood, PlanckDataset, GateLadderDecision,
    FittingBlockedError,
    ALLOWED_DATASET_KINDS, PLANCK_2018_LOWL_TT_DATASET_KIND,
    make_synthetic_dataset,
)

# Round-16 RuntimeControlBlock fields (PR-S1)
# (still imported from bass.runtime.ver2_execution.RuntimeControlBlock,
#  with seven new keyword-only fields with safe defaults:
#    tilt_freeze=False
#    codazzi_projection_cadence="every_step"
#    codazzi_residual_threshold=1.0e-6
#    allow_template_card=False
#    map_output_nside=0
#    b_mode_projector="flrw_zero_only"
#    massive_neutrino_quadrature_nq=50)
```

## 4. Critical context for PR-S13 (the next deliverable)

PR-S13 closes **G1**: Python-side D_2 = 1002.086744 µK² PSTF closure
bit-identical to the Rust MB-95 anchor. The existing test
[htt/bass/spectrum/test_d2_pstf_closure.py](htt/bass/spectrum/test_d2_pstf_closure.py)
is currently **xfail**; PR-S13's success criterion is making it
**xpass** (and removing the xfail marker).

### 4.1 The state-layout migration

**Load-bearing problem**: the existing photon hierarchy state vector
in [htt/bass/hierarchy/pack_unpack.py](htt/bass/hierarchy/pack_unpack.py)
and [htt/bass/hierarchy/hierarchy_rhs.py](htt/bass/hierarchy/hierarchy_rhs.py)
carries m=0 only. The Round-16 primitives (mode_mixing_blocks,
seed_factory, b_mode_projector) all assume m∈{-2..+2} (5-channel PSTF
stripe per V5_ROUND16_02 §1).

PR-S13 must:

1. **Migrate the state vector**: extend `pack_combined_state` /
   `unpack_combined_state` from m=0 to m∈{-2..+2}, preserving the
   FLRW limit at the m=0 slice exactly (so existing FLRW tests stay
   bit-identical).
2. **Wire mode_mixing_blocks into hierarchy_rhs**: extend
   [htt/bass/hierarchy/hierarchy_rhs.py](htt/bass/hierarchy/hierarchy_rhs.py)
   to call `assemble_A_mix_block` + `assemble_A_curv_block` +
   `assemble_EB_mixing_block` per η, contracting against the
   evolved background `σ_2M(η)` from
   `BackgroundEvolved.sigma_squared_at(η)` (PR-S1) — but note that
   PR-S1 only exposes `sigma_squared_at` (scalar). For the full
   5-vector `σ_2M(η)` PR-S13 also needs a small extension to
   `BackgroundEvolved`.
3. **Wire seed_factory into ic.py**: replace the existing FLRW-only
   IC build in [htt/bass/hierarchy/ic.py](htt/bass/hierarchy/ic.py) with
   the per-family dispatch from `bass.hierarchy.seed_factory.get_seed_factory`.
4. **Wire family_propagators into the LoS pipeline**: the existing
   [htt/bass/los/flrw_bessel_projector.py](htt/bass/los/flrw_bessel_projector.py)
   is the FLRW production path. For non-FLRW families, dispatch to
   `bass.los.family_propagators.get_propagator(family)`.
5. ~~**Apply the Doppler /k correction**~~ **RETRACTED 2026-04-26.**
   This step instructed `d/dη[g v_b] → (1/k) d/dη[g v_b]` as the
   load-bearing fix. Empirical measurement disproved this: the /k patch
   shifts D_2 by only -0.012% (−2.5 × 10⁶ μK² of a +2.04 × 10¹⁰ μK²
   gap). The actual gap is dominated by primordial-amplitude
   normalization, not Doppler convention. The R7-authoritative Opus
   derivation explicitly bans the /k patch and the in-tree
   regression-armor test
   `test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`
   enforces the canonical `(g v_b)'` form. PR-S13 closure work is
   re-scoped in `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md`.
6. **Run [htt/bass/spectrum/test_d2_pstf_closure.py](htt/bass/spectrum/test_d2_pstf_closure.py)**;
   it currently fails at config validation
   (`L_max_tower=4 < ell_max_transfer=8`) — that latent bug was fixed
   2026-04-26. The test now actually exercises the pipeline and yields
   the +2.04 × 10¹⁰ μK² xfail signal, which is the real PR-S13 gap.

### 4.2 What's *already done* and shouldn't be redone

- ARK4 stepper exists ([htt/bass/integration/imex_ark4.py](htt/bass/integration/imex_ark4.py))
  but is not yet the production stepper — Rodas5P remains in
  `RuntimeControlBlock.integrator_family` default.
  PR-S13 may *optionally* switch FLRW closure to ARK4 to test bit-
  identity, but the existing Rodas5P path should also reach the anchor
  with the Doppler /k fix alone. Keep the integrator switch as a
  follow-on knob, not the load-bearing fix.
- All primitives are tested in isolation (287 tests pass). PR-S13 only
  needs *integration* tests for the full pipeline.

### 4.3 Existing tests to honor

These end-to-end tests exist and must continue to pass after PR-S13:

```
htt/bass/spectrum/test_d2_pstf_closure.py            # currently xfail
htt/bass/spectrum/test_flrw_pipeline.py              # FLRW C_ℓ regression
htt/bass/spectrum/test_production_cutoff_convergence.py  # L_max sweep
htt/bass/spectrum/test_flrw_external_camb.py         # CAMB anchor
htt/bass/runtime/test_cosmological_smoke.py          # Tier-B smoke
htt/bass/runtime/test_ver2_tier_b_execution.py       # full Tier-B
                                                     # (2 known-flaky off-axis
                                                     #  tests pre-Round-16,
                                                     #  unrelated)
```

Specifically, **433 background tests + 50 RuntimeControlBlock-touching
tests must continue to pass** (all PR-S1 tests, all PR-S5 tests, etc.).

## 5. Critical context for PR-S15 (production switch)

PR-S15 flips `RuntimeControlBlock` defaults to the Round-16 production
stance per V5_ROUND16_04 §9:

```python
# Current (Round-15 stance, preserved by PR-S1 for backwards compat):
tilt_background_owner: str = "fixed_velocity_closure"
tilt_freeze: bool = False                  # already Round-16-correct
codazzi_projection_cadence: str = "every_step"  # already Round-16-correct
b_mode_projector: str = "flrw_zero_only"
map_output_nside: int = 0
allow_template_card: bool = False          # already Round-16-correct
massive_neutrino_quadrature_nq: int = 50   # already Round-16-correct
```

The flips that **break existing tests** (need careful migration):

1. `tilt_background_owner = "nonperturbative_tilt_rhs"` — breaks
   `test_ver2_tier_b_execution.py:512, 835` (asserting metadata =
   "fixed_velocity_closure") and `test_ver2_solver_output.py:223`.
   Migration: update those assertions to the new default + add a
   `_runtime_controls_with_legacy_owner()` helper for tests that
   need the old behaviour.
2. `b_mode_projector = "wigner_d_path_b"` — risk: any test asserting
   `b_mode_output_support="flrw_zero_only"` in
   `SolverCoreOutput.metadata`. Search-grep first.
3. `map_output_nside = 64` — risk: changes
   `SolverCoreOutput.map_output_support` default behaviour. Need to
   wire `populate_map_outputs` (PR-S12) into
   [htt/bass/runtime/ver2_execution.py](htt/bass/runtime/ver2_execution.py)
   when nside > 0.

Approach: do these **one at a time**, run the affected test subset
after each flip, fix or update the assertions, commit per flip.
**Don't bundle all three flips into one commit** — the cascade is
messy.

## 6. Start here (PR-S13 procedure — post-retraction 2026-04-26)

The earlier procedure in this section instructed a Doppler /k patch as
the load-bearing fix. That instruction was retracted; see the banner
at the top of this file and `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md` for
the corrected scope.

Updated entry procedure for a fresh session:

```bash
# 0. Verify clean baseline.
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
git log --oneline -1   # should show the doc-retraction commit or later
git status             # should be clean

cd htt
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -m pytest \
  bass/background/test_codazzi_tilt_rhs.py \
  bass/integration/test_imex_ark4.py \
  bass/hierarchy/test_mode_mixing_blocks.py \
  bass/hierarchy/test_seed_factory.py \
  bass/hierarchy/test_family_k_grid.py \
  bass/los/test_b_mode_projector.py \
  bass/los/family_propagators/ \
  bass/forward/test_map_producer.py \
  bass/inference/test_planck_likelihood.py \
  -q --tb=line
# Expected: 287 passed in ~16 s.

# 1. Read the corrected scope.
#    docs/V5_ROUND17_PR_S13_REAL_SCOPE.md             ← real PR-S13 scope
#    docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md       ← R7-authoritative
#                                                       (do not apply /k)
#    docs/V5_ROUND16_02_SOLVER_LAYER.md §1            ← state-layout migration
#    CLAUDE.md §3                                     ← Round-15 P2 pointer
#                                                       on η_init extension /
#                                                       primordial alignment

# 2. Decide which PR-S13 sub-track to enter (each is multi-day; do not
#    enter without explicit user confirmation):
#    (a) Primordial-amplitude alignment (CLAUDE.md §3 Round-15 P2 lift)
#    (b) State-layout migration m=0 → m∈{-2..+2} (V5_ROUND16_02 §1)
#    (c) Real-IC injection at η(z_*) (Blocker 3 from R15 diagnosis)

# 3. Forbidden moves (always):
#    - Do NOT add a Doppler /k factor (re-introduces parallel-cycle false trail).
#    - Do NOT mark test_d2_pstf_closure.py xpass without verifying the
#      actual numerical value against the Rust anchor.
#    - Do NOT enter (a)/(b)/(c) above without explicit user confirmation.
```

Empirical context for the next session: the current Python-side D_2
on the canonical `(g v_b)'` Doppler form is **2.04 × 10¹⁰ μK²**, vs
the Rust MB-95 anchor **1002.086744 μK²**. The 7-orders-of-magnitude
gap is the real PR-S13 closure target.

## 7. Open questions for the human

These must be raised explicitly with the user before progress on the
hard parts of PR-S13/S15:

- **Q1 (PR-S13)**: ~~After applying the Doppler /k fix~~ **RESOLVED
  empirically 2026-04-26.** /k patch shifts D_2 by only -0.012% and the
  gap to the Rust anchor is 7 orders of magnitude (+2.04 × 10¹⁰ μK²).
  The /k mandate is retracted. Real PR-S13 scope and per-sub-track
  open questions live in `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md`.

- **Q2 (PR-S15)**: The three default flips break different test sets.
  Should they ship as three separate commits (gradual migration) or
  one bundled commit (atomic switch)? Recommend three separate.

- **Q3 (Round-17 follow-on)**: Several primitive deferrals are
  documented in the per-PR CHANGELOG entries (full hyperbolic-
  Legendre kernel for V; Frobenius series for II + VIII; per-axis
  Codazzi residual; etc.). Confirm these stay deferred to Round-17,
  or escalate any that block Tier-B/C ship.

## 8. Forbidden moves (regression catalogue)

Per V5_ROUND16_05 §4 forbidden patterns + the gap-history catalogue:

- **Do not** drop the existing m=0 FLRW path during the state-layout
  migration. Keep both paths until PR-S13 closes; then deprecate.
- **Do not** wire the new primitives into `hierarchy_rhs.py` without
  also extending `pack_unpack.py` — partial wiring breaks the FLRW
  bit-identity invariant.
- **Do not** flip `tilt_background_owner` default in PR-S15 without
  first updating the 7 callsite assertions; running the runtime
  test suite to check coverage; and adding a fallback constructor
  helper for legacy callers.
- **Do not** mark `test_d2_pstf_closure.py` xpass without verifying
  the actual numerical value against the Rust anchor (run
  `bass_rs dump_dl_spectrum_sparse` and compare; do not just
  remove the xfail marker on a test that returns a different value).

## 9. References (what to read for each PR)

| PR | Primary spec | Audit | Tests path |
|----|--------------|-------|-----------|
| S13 | `docs/V5_ROUND16_03_OBSERVABLES_LAYER.md §1`, `04 §8` | `05 §3` | `htt/bass/spectrum/` |
| S15 | `docs/V5_ROUND16_04_NUMERICS_AND_RUNTIME.md §9`, `05 §1` | `05 §3.1 A4/A5` | `htt/bass/runtime/` |

Round-16 master `docs/V5_ROUND16_00_MASTER_PLAN.md`. Each layer has
its own doc (01..05). The CHANGELOG `[Unreleased]` section is the
authoritative per-PR closure record.

---

**End of handoff.** Begin at §6.
