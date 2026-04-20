# BASS Rust Solver — Per-PR Work Breakdown (SDD)

**Purpose**: the concrete, merge-gate-level design for every upcoming PR on the
bass_rs main-line, plus the parallel infrastructure PRs and the backup
branch. Each entry follows the template defined in
[`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) §4.

**Reading rule**: before starting a PR, read only the section for that PR
plus every PR listed under its **Depends on** line. That is sufficient to
pick up and execute the work cold.

**Cross-references**:

- Hub: [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md).
- Session knowledge (constraints, killed directions, invariants):
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md).
- Audit + doc-update procedure invoked at each merge:
  [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md).
- Solver-choice rationale: [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md).
- Roadmap phases: [`ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md).
- Architectural charter: [`../project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안).

---

## Conventions for every entry

### Status taxonomy

| Label | Meaning |
|---|---|
| `PLANNED` | SDD written, not started. |
| `IN PROGRESS` | Work has begun on a specific commit. Note the branch or commit prefix. |
| `DONE {sha}` | Merged. `{sha}` is the authoritative commit. |
| `BLOCKED by <reason>` | Work paused. Named blocker with a pointer. |
| `SUPERSEDED by <PR-id or doc>` | Obsolete. Keep the entry for history. |

### Universal invariants (not repeated per-PR)

From [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §5, §2:

- Additive commits only. Explicit pathspec form `git commit -- <paths>`.
- Approximation-free defaults. No TCA/UFA/RSA.
- `D_2 = 1002.086744 μK²` regression anchor bit-identical.
- Never hardcode FLRW into PSTF primary.
- Edit `src/solver/pstf_primary/`, never `src/pstf_primary/`.

### Universal merge rule

Every PR must leave `cargo test --release` green across the full
`solver::pstf_primary` suite plus whatever new tests the PR adds. The PR
description lists the baseline test count before the PR and the new count
after. A merge that drops any previously-green test is **rejected**.

### Universal audit rule

At every PR merge, self-trigger
[`docs/audits/AUDIT_PROMPT.md`](audits/AUDIT_PROMPT.md) with the PR tag (e.g.
`IMEX-03`). Protocol in
[`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) §1. Skip-audit
is allowed only when the `Audit:` line says so explicitly with justification.

### Universal doc-update rule

After the PR lands, update:

1. [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) §1 commit ledger.
2. This file: change the PR's `Status:` line to `DONE {sha}` and add an
   `Evidence:` bullet pointing to the merge gate tests that passed.
3. Any PR-specific doc listed under the entry's `Doc updates:` heading.

Procedure: [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) §2.

---

## Part I — IMEX mainline ladder

Numbered per [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6.

### IMEX-00 — Baseline contract freeze

- **Status**: DONE `cc35fbd`.
- **Goal**: freeze the production Rodas5P reference so every subsequent IMEX
  PR can prove equivalence against it.
- **Artifacts delivered**:
  - `StepperStats` struct surfaced through `PstfKmodeResult`.
  - Frozen counters at `(layout = (8,6,0), k = 0.01, Planck 2018)`:
    `n_steps = 3334`, `n_rejected = 253`, `n_jac = 3587`,
    `n_f_eval = 28696`, `n_snaps = 583`.
- **Evidence**: `imex00_baseline_capture` (`#[ignore]`, regeneration),
  `imex00_baseline_verify_shape_and_counters`,
  `imex00_baseline_invariant_across_backends`. All green.

### IMEX-01 — ARK4 tableau validation

- **Status**: DONE `661044d`.
- **Goal**: standalone verification of the Kennedy–Carpenter
  ARK4(3)6L[2]SA tableau.
- **Artifacts delivered**: two new end-to-end tests on top of the existing
  17 tableau audits in [`src/solver/imex_ark4.rs`](../src/solver/imex_ark4.rs).
- **Evidence**:
  - `imex01_split_order_of_accuracy_prothero_robinson` (ratios 10.3 → 12.3 —
    4th-order band).
  - `imex01_embedded_estimator_monotone_in_h` (8.57e9 → 2.90e5 strict
    monotone).

### IMEX-02 — Operator split identity check ←── **NEXT UP**

- **Status**: PLANNED.
- **Depends on**: IMEX-00, IMEX-01. No dependency on Phase 2.x parallel
  infrastructure.

#### Goal (one sentence)

Decompose the PSTF primary FLRW RHS into `A_stiff` (Thomson collision block)
and `A_stream` (everything else), and prove that `A_stiff + A_stream ≡ pstf_full_rhs`
to ULP across a representative state set.

#### Inputs (what already exists)

- Source files:
  - [`src/solver/pstf_primary/rhs.rs`](../src/solver/pstf_primary/rhs.rs) — full RHS.
  - [`src/solver/pstf_primary/jacobian.rs`](../src/solver/pstf_primary/jacobian.rs) — analytical Jacobian (includes collision sector since c5ae4f9).
  - [`src/solver/pstf_primary/matrix.rs`](../src/solver/pstf_primary/matrix.rs) — `build_pstf_matrix_analytical_into` with split-sector structure already available.
- Tests that must remain green: the full `solver::pstf_primary::` suite
  (baseline: 117 tests after `883f22a`).
- Reference baseline: `IMEX_00_REFERENCE_*` counters.

#### Outputs (what this PR produces)

- New source:
  - `src/solver/pstf_primary/rhs_split.rs` (new): pub fn
    `pstf_stiff_rhs(state, bg) -> rhs_stiff` and pub fn
    `pstf_stream_rhs(state, bg) -> rhs_stream`, both reusing the internal
    routines that currently contribute their sectors in
    `pstf_full_rhs`.
  - Sector attribution table documented in a top-of-file comment: which
    PSTF multipole slots receive `A_stiff` vs `A_stream` contributions.
- New tests (in `rhs_split.rs` `#[cfg(test)]` mod):
  - `imex02_split_identity_ulp_fast_val`: random state vectors at
    `layout = (8,6,0)` and `(12,8,0)`, assert
    `(A_stiff + A_stream - full).abs().max() == 0.0` **or** ≤ 2·`f64::EPSILON`
    per component with documented operation-order justification.
  - `imex02_split_sector_nonoverlap`: verify that every state index
    receives a contribution from exactly one of the two splits (component
    masks partition the layout).
  - `imex02_split_stiff_zero_when_xe_zero`: at `ne = 0` (post-recombination
    surrogate), `A_stiff ≡ 0` on photon polarisation multipoles.
- No env toggles. Functions are pure and test-only for now.

#### WBS

1. Sector-attribution audit — read [`rhs.rs`](../src/solver/pstf_primary/rhs.rs)
   and annotate each contribution with `[STIFF]` or `[STREAM]` in a scratch
   doc at `docs/notes/imex02_sector_attribution.md` (not committed; working
   reference). Stiff = every Thomson-collision contribution to Θ_ℓ, E_ℓ,
   B_ℓ (and the tilt-projected tight-coupling diagonal if present). Stream
   = transport, metric, fluid, neutrinos, massive-ν.
2. Implement `rhs_split.rs` — two functions that mirror the sector
   attribution.
3. Order-of-operations reproducibility: both the split and the full RHS
   must perform their floating-point operations in identical order for the
   identity to be *bit-exact*. Concretely, write `pstf_full_rhs` as
   `let mut out = A_stream(...); acc_stiff_into(&mut out, ...);` internally
   (a refactor; does not change behaviour). Verify bit-identicity of
   production D_2 on the regression suite before committing any structural
   change.
4. Implement the three tests with fixed RNG seeds.
5. Extend the PSTF-primary `lib.rs` re-export to make `pstf_stiff_rhs` /
   `pstf_stream_rhs` available to crate-level tests (not the public pyo3
   surface).
6. Record `n_tests` delta in PR description.

#### Merge gate

- `imex02_split_identity_ulp_fast_val` passes at both layouts.
- `imex02_split_sector_nonoverlap` passes.
- `imex02_split_stiff_zero_when_xe_zero` passes.
- All 117+ baseline tests remain green. D_2 bit-identical.

#### Audit

- Applies: YES. Scope: "is `A_stiff` actually equal to the collision
  operator in MB-95 / Challinor & Lasenby 2000 terms?" Specifically,
  confirm no tight-coupling-closure term was silently folded in.

#### Doc updates

- [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) §1 commit ledger row with SHA.
- This file: Status → DONE.
- Note in [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6
  IMEX-02 row → DONE.

---

### IMEX-03 — Single-k FLRW PSTF primary solve via IMEX-ARK4

- **Status**: PLANNED.
- **Depends on**: IMEX-02.

#### Goal

Wire the validated ARK4 tableau to the validated `A_stiff / A_stream` split
and integrate one k-mode of the PSTF primary FLRW problem end-to-end at
`layout = (8,6,0)`. Produce a `D_ℓ` that agrees with the Rodas5P baseline
within `1e-6` relative.

#### Inputs

- `src/solver/imex_ark4.rs` (existing, with IMEX-01 gates).
- `rhs_split.rs` from IMEX-02.
- `PstfKmodeResult` with `StepperStats` (IMEX-00).
- Baseline reference: `IMEX_00_REFERENCE_*` counters + `D_2` anchor.

#### Outputs

- `src/solver/pstf_primary/imex_driver.rs` (new): single-k integrator that
  assembles `W_I = I/(γh) − J_stiff` with
  - diagonal entries for ℓ ≥ 3 (Thomson diagonal),
  - dense 2×2 block for ℓ = 2 (Θ_2 ↔ E_2),
  - dense 2×2 block for ℓ = 1 (Θ_1 ↔ v_b),
  and advances one ARK4 step per `BASS_PSTF_IMEX=1` opt-in.
- Tests:
  - `imex03_single_k_d2_vs_rodas5p`: `|D_2_imex − D_2_rodas5p| /
    D_2_rodas5p ≤ 1e-6` at `k = 0.01, 0.03, 0.1` single-mode.
  - `imex03_step_counters_in_band`: `n_steps_imex ∈ [0.5·n_rodas5p,
    2·n_rodas5p]` — spot-check the adaptive controller picks reasonable
    step sizes (not a tight bound; order-of-magnitude sanity).
  - `imex03_stepper_stats_populated`: non-zero `n_steps`, `n_jac`,
    `n_f_eval`, wall seconds.
- Env toggle `BASS_PSTF_IMEX=1` surfaces the path at
  `compute_pstf_cl_track_a` (single-k gate; ignored at multi-k for now).

#### WBS

1. **Implicit block factorisation**. Implement `stiff_block_solve(h, dt,
   y_pred, out)` at `imex_driver.rs` as:
   - Compute the diagonal-only Thomson contributions for ℓ ≥ 3 directly
     (inverse is scalar per slot).
   - Build 2×2 dense block for ℓ = 2 Θ–E; solve via analytical 2×2 inverse
     with determinant guard.
   - Build 2×2 dense block for ℓ = 1 Θ_1–v_b; same.
2. **ARK4 stage loop**. For each stage `i ∈ 1..6`:
   - Predictor: `y_pred = y_n + h · Σ_{j<i} [a_{ij}^E · k_j^E + a_{ij}^I · k_j^I]`.
   - Compute `k_i^E = A_stream(y_pred_at_i)`.
   - Stiff solve: `(I − h·γ·J_stiff)·k_i^I = A_stiff(y_pred_at_i)`.
   - Accumulate.
3. **Error estimator**. Embedded Kennedy–Carpenter 3rd-order
   `err = Σ (b_i − b̂_i)·k_i`. PI controller ala
   `h_new = safety · h · (atol/err)^(1/5) · prev_factor^0.7`.
4. **StepperStats integration**: populate counters as ARK4 advances.
   Reuse the struct from IMEX-00.
5. **Single-k gate** — only activate at single-k calls; multi-k rollout is
   IMEX-04.
6. **Test implementation** — three tests above plus the regression anchor
   check.

#### Merge gate

- `imex03_single_k_d2_vs_rodas5p`: all three k values pass `≤ 1e-6` rel.
- `imex03_step_counters_in_band`: passes.
- Regression: D_2 bit-identical under **default backend** (i.e.
  `BASS_PSTF_IMEX=0` path unchanged).

#### Audit

- Applies: YES. Scope: (a) 2×2 block inversion correctness for the Θ_2–E_2
  coupling sign convention (Challinor 2000 vs MB-95); (b) verify `γ` in
  the stiff block solve matches the Kennedy–Carpenter implicit γ, not a
  stray default.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- [`ENV_VARS.md`](ENV_VARS.md): new `BASS_PSTF_IMEX`.
- [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6.

---

### IMEX-04 — Multi-k end-to-end `compute_pstf_cl_track_a` IMEX variant

- **Status**: PLANNED.
- **Depends on**: IMEX-03.

#### Goal

Extend the IMEX path from single-k to the full `compute_pstf_cl_track_a`
pipeline with the `BASS_IMEX=1` runtime toggle; all `flrw_cl_pipeline`
regression tests pass under that toggle.

#### Inputs

- `src/solver/pstf_primary/imex_driver.rs` (IMEX-03).
- `src/solver/flrw_cl_pipeline.rs` (existing multi-k orchestrator; currently
  Rodas5P).

#### Outputs

- Pipeline-level env toggle `BASS_IMEX ∈ {0 default, 1}`. At `1`, each
  k-mode dispatches to `imex_driver` instead of the Rodas5P path.
- Tests:
  - `imex04_multi_k_d2_matches_baseline`: entire `fast_validation` run
    under `BASS_IMEX=1` gives `D_2` within `5e-6` rel of the
    `BASS_IMEX=0` baseline (tolerance looser than IMEX-03 because
    floating-point commutativity across k-mode accumulation is not
    required).
  - `imex04_runtime_within_factor`: wall time under IMEX ≤ 3× Rodas5P at
    `fast_validation`. (Note: **not** a speed claim; just a sanity bound
    that IMEX didn't accidentally become dramatically slower.)
  - All pre-existing `flrw_cl_pipeline` regression tests under both toggle
    values.

#### WBS

1. Plumb `BASS_IMEX` env read into `flrw_cl_pipeline`'s k-mode dispatch.
2. Thread `BASS_PSTF_IMEX` (the single-k gate from IMEX-03) to be implied
   by `BASS_IMEX=1` but also independently settable; `BASS_PSTF_IMEX=1` at
   single-k contexts should keep working.
3. Thread `StepperStats` aggregation through the k-mode loop — a
   `StepperStatsAccumulator` that sums the per-k counters.
4. Implement the two new tests plus run the pre-existing suite under the
   toggle in CI config (add an env-matrix line).
5. Record baseline and IMEX wallclock via `hyperfine` for the PR
   description (n ≥ 5 per configuration).

#### Merge gate

- `imex04_multi_k_d2_matches_baseline` passes.
- `imex04_runtime_within_factor` passes.
- Every pre-existing `flrw_cl_pipeline` test passes under both toggle
  values.

#### Audit

- Applies: YES. Scope: confirm the k-mode loop retains deterministic
  reduction order under IMEX (matters for the future rayon parallelism).
- Confirm `BASS_IMEX=0` default path is bit-identical to pre-PR behaviour
  (not just equivalent — bit-identical).

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- [`ENV_VARS.md`](ENV_VARS.md): `BASS_IMEX` added.
- [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6.

---

### IMEX-05 — Callback-based stage assembly as production default for both solvers

- **Status**: PLANNED.
- **Depends on**: IMEX-04, Phase 2.0 (callback backend, DONE `883f22a`).

#### Goal

Retire `mats_flat` pre-materialisation on the production path. Both
Rodas5P and IMEX-ARK4 drivers call the `LinearProfileSampler` trait for
`M(η)` evaluation; `mats_flat` remains only as a `#[cfg(test)]` oracle.

#### Inputs

- `LinearProfileSampler` / `LinearProfileCallback<F>` in
  [`src/solver/rodas5p.rs`](../src/solver/rodas5p.rs) (Phase 2.0).
- IMEX driver (IMEX-03, IMEX-04).
- `BASS_PSTF_CALLBACK=1` env toggle, currently opt-in.

#### Outputs

- `BASS_PSTF_CALLBACK` default flipped to `1`. Old behaviour
  (`BASS_PSTF_MATRIX_UV=1`) kept as fallback and test oracle.
- IMEX driver reworked to consume the sampler trait directly (no
  intermediate `mats_flat`).
- Tests:
  - `imex05_callback_default_rss_below_threshold`: at
    `layout = (12,8,0)` peak RSS under the new default ≤ 50 MB (baseline
    without callback was 2057 MB — a **~280× drop** expected).
  - `imex05_callback_d2_bit_identical`: default-backend D_2 bit-identical
    to pre-PR default-backend D_2.
  - Existing Phase 2.0 equivalence tests still pass.

#### WBS

1. Confirm `LinearProfileCallback` supports the RHS / Jacobian sampling
   pattern the IMEX driver needs (it does — it was designed for this).
   If any hint/cache behaviour is IMEX-specific, add it.
2. Flip the env default. Document the old path in
   [`ENV_VARS.md`](ENV_VARS.md) as "legacy oracle backend".
3. Implement the RSS test using `dhat` or `valgrind massif`; assert peak
   below the threshold.
4. Run the production regression suite at both layouts. Record numbers.

#### Merge gate

- `imex05_callback_default_rss_below_threshold` passes.
- `imex05_callback_d2_bit_identical` passes.
- All pre-existing tests green.

#### Audit

- Applies: YES. Scope: the RSS test is fragile to the measurement tool's
  semantics (`dhat` counts differently than `valgrind massif`); make sure
  the threshold is sanity-robust to the tool chosen.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- [`ENV_VARS.md`](ENV_VARS.md): default flipped.
- [`PERF_FRESH_2026-04-18.md`](PERF_FRESH_2026-04-18.md): add a new row
  reflecting the post-IMEX-05 RSS floor.

---

### IMEX-06 — Polarisation activation (Θ₂ ↔ E₂ recoupling)

- **Status**: PLANNED.
- **Depends on**: IMEX-05.

#### Goal

Activate the polarisation hierarchy. `Θ_2 ↔ E_2` recoupling goes through
the dense 2×2 implicit block already structurally in place from IMEX-03.
Produce an EE spectrum that matches the bass_py W7-02 4/3 amplification
regression.

#### Inputs

- IMEX driver with 2×2 implicit block (IMEX-03+).
- bass_py W7-02 reference data (must be extracted / ported into Rust test
  fixtures in `crates/tests/fixtures/polarisation/`).

#### Outputs

- Polarisation-active layout `(L_γ=12, L_ν=12, L_pol=12)` runs through the
  IMEX path.
- Tests:
  - `imex06_ee_4_3_amplification`: EE peak amplitude within ±3 % of the
    bass_py reference (port of W7-02 test).
  - `imex06_ee_leaves_bb_zero`: without sources, `B_2 ≈ 0` to `1e-14`.
  - `imex06_polarisation_sign_convention`: sign of `Θ_2` vs `E_2` in the
    driver matches Challinor 2000 eq. (3.18); regression-tested explicitly
    against a known-sign fixture.

#### WBS

1. Port bass_py W7-02 fixture to `crates/tests/fixtures/polarisation/`.
   Document the extraction script in `docs/notes/imex06_fixture_extract.md`.
2. Extend the layout to `L_pol > 0`. Verify collision diagonal entries at
   ℓ = 3 … L_pol are correctly Thomson-driven.
3. Cross-check Θ_2–E_2 coupling sign against
   [`docs/PHYSICS_REFERENCES.md`](PHYSICS_REFERENCES.md) before running
   the amplification test.
4. Implement tests; record EE amplitude numerically in PR description.

#### Merge gate

- EE amplification test passes.
- B-mode zero-source test passes.
- Sign convention test passes.
- D_2 bit-identical under `L_pol = 0` layout (regression guard).

#### Audit

- Applies: YES. Scope: the Θ_2–E_2 sign is a perennial source of
  confusion between CAMB and Challinor conventions; verify explicitly.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- [`PHYSICS_REFERENCES.md`](PHYSICS_REFERENCES.md) — if the audit uncovers
  a convention note worth recording.

---

### IMEX-07 — Production truncation scale-up (L_γ=25, L_ν=15, L_pol=25)

- **Status**: PLANNED.
- **Depends on**: IMEX-06.

#### Goal

Scale to the production layout and demonstrate CAMB-agreement within ±5 %
at ℓ ≤ 300.

#### Inputs

- IMEX-06 output with polarisation active.
- CAMB reference spectra in
  [`data/camb_reference/`](../data/camb_reference/) — confirm the layout
  and normalisation used.

#### Outputs

- Default production layout changed to `(L_γ=25, L_ν=15, L_pol=25)`.
- Tests:
  - `imex07_d2_within_band`: `D_2 ∈ 1022 ± 50` (Planck-style band).
  - `imex07_d220_within_band`: `D_220 ∈ 5733 ± 300`.
  - `imex07_camb_agreement_l_le_300`: pointwise `|D_ℓ − D_ℓ^CAMB| /
    D_ℓ^CAMB ≤ 0.05` for `2 ≤ ℓ ≤ 300`.
  - `imex07_wall_recorded`: wall time logged to
    `docs/PERF_FRESH_2026-04-18.md` update.

#### WBS

1. Confirm CAMB reference fixture provenance (which Planck 2018
   cosmology, which CAMB git SHA).
2. Run at the new layout under `BASS_IMEX=1`; adjust small-block LU if
   the ℓ ≤ 2 block grows beyond 2×2 due to polarisation coupling (it
   likely stays 2×2 at m = 0, but check the sparsity output from
   IMEX-06's Jacobian).
3. Implement the three band / agreement tests.
4. Measure wall time via `hyperfine` (n ≥ 5).
5. Update `PERF_FRESH` with a production-scale row.

#### Merge gate

- `imex07_d2_within_band` passes.
- `imex07_d220_within_band` passes.
- `imex07_camb_agreement_l_le_300` passes.
- D_2 regression guard: bit-identical at the **previous** default layout
  (regression on legacy `(8,6,0)` not permitted).

#### Audit

- Applies: YES. Scope: the CAMB ±5 % tolerance must be checked against
  known approximation-driven differences (CAMB uses TCA; our solver does
  not, so low-ℓ ISW differences are expected). Document any residual
  bias.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- [`PERF_FRESH_2026-04-18.md`](PERF_FRESH_2026-04-18.md) — new row.
- [`PROGRESS_SCOREBOARD.md`](PROGRESS_SCOREBOARD.md) — mark the
  production-scale milestone.

---

### IMEX-08 — Bianchi I m-major extension (m ∈ {−2..+2})

- **Status**: PLANNED.
- **Depends on**: IMEX-07, Phase 2.1 (m-major layout formalisation —
  critical path prerequisite), Phase 2.2 m ≠ 0 Clebsch-Gordan Jacobian
  (co-landed with this PR).

#### Goal

Extend to Bianchi I with m ∈ {−2..+2}, preserving the split structure
(Thomson collision is m-independent) and demonstrating small-shear
`σ → 0` continuity.

#### Inputs

- IMEX-07 at m = 0.
- Phase 2.1 `LmLayout` with m ∈ {−m_max..+m_max}.
- Phase 2.2 (already done at m = 0 in `c5ae4f9`) must be extended to cover
  m ≠ 0 Clebsch-Gordan κ-factors. Co-landed in this PR.

#### Outputs

- `src/solver/pstf_primary/layout.rs` promoted from `PstfFlrwLayout` to
  full `LmLayout`.
- `jacobian.rs` extended with m ≠ 0 CG coefficients.
- Tests:
  - `imex08_sigma_zero_reproduces_flrw`: with Σ² = 0 input, output D_2 /
    D_220 bit-identical to IMEX-07 output (σ = 0 should reduce exactly to
    FLRW).
  - `imex08_small_sigma_linear_in_sigma_squared`: for Σ² ∈ {1e-10, 1e-8,
    1e-6}, `|D_2(σ) − D_2(0)| / Σ²` is linear within ±5 % across the
    three values (first-order-in-Σ² response).
  - `imex08_collision_is_m_independent`: `A_stiff` matrix entries at
    m = 0 and m = 2 states are identical for identical (Θ_ℓ,m / E_ℓ,m)
    values — regression of the m-independence claim.

#### WBS

1. `LmLayout` rollout — ensure index translation is unit-tested (
   `phase2_1_layout_roundtrip`).
2. Extend CG coefficient calculator to arbitrary (ℓ, m) pairs; reference
   is the [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md)
   §2.2 m-major mandate.
3. Port the σ = 0 continuity test from bass_py's Route B if available
   (`bass_py/bass/hierarchy/test_sigma_zero_limit.py`-style) to Rust.
4. Document the Bianchi I reference cosmology used (a simple σ / β /
   tilt set) in `docs/notes/imex08_bianchi_reference.md`.
5. Run IMEX-04..IMEX-07 tests at σ = 0 to confirm FLRW bit-identicity.

#### Merge gate

- `imex08_sigma_zero_reproduces_flrw` passes.
- `imex08_small_sigma_linear_in_sigma_squared` passes.
- `imex08_collision_is_m_independent` passes.
- All m = 0 regression tests from IMEX-04..07 remain green.

#### Audit

- Applies: YES (first Bianchi-active PR). Scope: confirm no FLRW-specific
  closure leaked into the m ≠ 0 path. Check
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §2.2 banned
  list.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- [`ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md):
  P2.1 DONE, P2.2 (m ≠ 0) DONE.
- [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6.

---

### IMEX-09 — Massive-ν momentum bins

- **Status**: PLANNED.
- **Depends on**: IMEX-08.

#### Goal

Integrate the massive-neutrino momentum grid (~130 DOF) into the m-major
layout. Recover Planck cosmology with the mass-eigenstate sum.

#### Inputs

- `LmLayout` from IMEX-08.
- Existing massive-ν infrastructure if any
  (check `src/solver/pstf_primary/neutrinos.rs` — TBD by PR-start
  inspection).

#### Outputs

- Massive-ν momentum grid plumbed into layout; IMEX driver unchanged in
  structure (massive-ν is in `A_stream`, no extra implicit block).
- Tests:
  - `imex09_massless_limit_reproduces_imex08`: with `m_ν = 0`, D_2
    bit-identical to IMEX-08 output.
  - `imex09_planck_cosmology_recovery`: with `Σ m_ν = 0.06 eV`, D_2 /
    D_220 within ±3 % of CLASS reference.

#### WBS

1. Inventory current massive-ν code. Decide keep-or-rewrite.
2. Plumb momentum grid into `LmLayout`.
3. Extend `pstf_stream_rhs` to handle massive-ν contributions (ensuring
   they do NOT enter `pstf_stiff_rhs` — massive-ν has no collision term).
4. Implement the two tests.
5. Generate CLASS reference at matching cosmology.

#### Merge gate

- `imex09_massless_limit_reproduces_imex08` passes.
- `imex09_planck_cosmology_recovery` passes.
- No regression on IMEX-08 σ ≠ 0 tests.

#### Audit

- Applies: YES. Scope: massive-ν sign conventions, temperature / chemical
  potential normalisation.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`: if the PR closes a phase
  gate, mark it.

---

## Part II — Parallel infrastructure ladder (ROADMAP_v3 Phase 2.1–2.5)

These can run in parallel with the IMEX ladder. They share the callback
backend (Phase 2.0, done) and the analytical Jacobian (Phase 2.2, partial).
None is on the IMEX critical path except where explicitly noted.

### P2.1 — (ℓ, m) m-major layout formalisation

- **Status**: PLANNED. Critical prerequisite of IMEX-08.
- **Depends on**: none (standalone refactor).

#### Goal

Promote `PstfFlrwLayout` to a full `LmLayout` with m ∈ {−m_max..+m_max},
keeping m = 0 as a performance-preserving special case.

#### Outputs

- `src/solver/pstf_primary/layout.rs` extended.
- Tests:
  - `p21_layout_roundtrip`: `(ℓ, m) → flat_idx → (ℓ, m)` round-trip.
  - `p21_layout_m_zero_matches_flrw`: at `m_max = 0`, layout size /
    ordering identical to the pre-PR `PstfFlrwLayout`.
  - `p21_layout_band_metadata_correct`: Bianchi band structure
    (`ℓ → ℓ ± 1, m → m, m ± 1, m ± 2`) matches the hand-derived pattern.

#### WBS

1. Define `LmLayout` struct with `ell_max`, `m_max`, flat-index tables.
2. Implement index helpers `flat_idx(ell, m)`, `unflatten(flat) -> (ell, m)`.
3. FLRW special case: when `m_max == 0`, layout collapses to the old
   `PstfFlrwLayout` order.
4. Tests as above.

#### Merge gate

All three tests pass. Every `layout`-using call site compiles under the
new type.

#### Audit

- Applies: YES. Scope: band metadata is the load-bearing invariant for
  sparse Jacobian and CG coefficient correctness.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P2.1 → DONE.

---

### P2.3 — Sparse Jacobian backend

- **Status**: PLANNED. Not on IMEX critical path (improves IMEX-05/07
  scale but not required).
- **Depends on**: P2.1 for band metadata.

#### Goal

Replace dense `mats_flat`-era matrix storage with `faer-sparse` (preferred
crate; active maintenance, AVX2 microkernels) exact-pattern CSR storage.
LU factorisation reuse policy per
[`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §9 item 3.

#### Outputs

- `Cargo.toml` dep on `faer-sparse` (or `sprs` fallback).
- `src/core/sparse.rs` (new): exact-pattern CSR builder with `LmLayout`
  awareness.
- Tests:
  - `p23_sparsity_pattern_matches_analytical_jac`: computed sparsity
    equals symbolic sparsity (same nnz, same (i, j) set).
  - `p23_sparse_lu_factor_reuse`: LU factor reused across ≥ 3 consecutive
    steps when Newton residual stays below threshold — StepperStats
    counter verifies.
  - `p23_production_scale_memory`: at `(L_γ=25, L_ν=15, L_pol=25, m=0)`,
    Jacobian storage ≤ O(N_snap · nnz) not O(N_snap · n²).

#### WBS

1. Add crate dep, gate behind a feature flag initially (`feature = "sparse"`).
2. Hand-derive nnz pattern for the PSTF primary Jacobian. Document in
   `docs/notes/p23_sparsity_pattern.md`.
3. Implement CSR builder.
4. Plumb into the IMEX / Rodas5P drivers via a trait abstraction
   (the existing `LinearProfileSampler` already decouples storage; this
   adds a sparse implementation).
5. Run production regression under the new backend.

#### Merge gate

Three new tests pass. All existing tests green under both dense and
sparse backends (env toggle `BASS_SPARSE_JAC=1`).

#### Audit

- Applies: YES. Scope: nnz pattern correctness is load-bearing.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P2.3 → DONE.
- [`ENV_VARS.md`](ENV_VARS.md): `BASS_SPARSE_JAC`.

---

### P2.4 — Adaptive ℓ_max + sponge boundary

- **Status**: PLANNED. Replaces the banned UFA (see §8.3 of ROADMAP).
- **Depends on**: none.

#### Goal

Implement an approximation-free high-ℓ tail strategy. Monitor
`R_ℓmax = Σ_m |X_{ℓmax,m}|² / Σ_ℓm |X_{ℓm}|²`. Apply a gentle damping
layer at the top-ℓ shell (sponge) to suppress reflection without low-ℓ
backreaction.

#### Outputs

- `src/solver/pstf_primary/sponge.rs` (new): diagnostic (`R_ℓmax` output)
  + damping operator.
- Tests:
  - `p24_r_lmax_monitor_correct`: synthetic state with known tail energy
    recovers the expected ratio.
  - `p24_sponge_preserves_low_ell`: with sponge active, D_2 stays within
    1e-8 of the no-sponge result at identical truncation.
  - `p24_sponge_suppresses_reflection`: in a controlled-reflection test
    case, tail energy decays with sponge vs grows without.

#### WBS

1. Define the sponge profile (gentle exponential, parameterised by shell
   depth + damping rate).
2. Plumb into `A_stream` — the sponge damping is purely explicit.
3. Add the `R_ℓmax` diagnostic; expose via `StepperStats`-adjacent struct.
4. Tests.

#### Merge gate

Three tests pass. D_2 regression anchor within 1e-10 (sponge OFF must be
bit-identical).

#### Audit

- Applies: YES. Scope: the sponge must not violate the approximation-free
  charter. Cross-check with
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §2.2.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P2.4 → DONE.

---

### P2.5 — Matrix line-of-sight projector

- **Status**: PLANNED. Not on IMEX critical path.
- **Depends on**: P2.1.

#### Goal

Replace scalar `src/los/` with a matrix-valued projector `G_{Aa}(η, k)` so
that FLRW LoS is the `A = a = 0` special case, not the base definition.
This is the structural prerequisite for Bianchi directional signal
reconstruction.

#### Outputs

- `src/los/matrix_projector.rs` (new).
- Tests:
  - `p25_matrix_los_flrw_matches_scalar`: at `A = a = 0`, output
    bit-identical to the existing scalar LoS.
  - `p25_matrix_los_bianchi_nonzero_offdiag`: at synthetic Bianchi input,
    off-diagonal entries are non-zero and carry the expected parity.
  - `p25_matrix_los_parity_preserved`: reflection + inversion
    preservation properties hold.

#### WBS

1. Design the `G_{Aa}` data layout. Reference: PhD-thesis Bianchi LoS
   formalism (ask user for the specific equation if ambiguous).
2. Implement the projector; scalar LoS becomes a wrapper.
3. Tests.

#### Merge gate

All three tests pass. `fast_validation` and production regression remain
bit-identical on the FLRW path.

#### Audit

- Applies: YES. Scope: the matrix LoS is load-bearing for Bianchi
  reconstruction — any sign or parity error here cascades into every
  Bianchi analysis.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P2.5 → DONE.

---

## Part III — Integration (Phase 4 — bass_py bridge)

These PRs run only after IMEX-07 succeeds (i.e. production-scale FLRW is
working). Enables the Python / HTT consumer side.

### P4.1 — `BianchiTransferFunctions(k)` JSON / CSV producer

- **Status**: PLANNED.
- **Depends on**: IMEX-07 (FLRW production works) + IMEX-08 (Bianchi
  active).

#### Goal

Rust-side module emitting transfer functions per `(type, Σ², β, x_h)` grid
point, consumable by bass_py.

#### Outputs

- `src/bridge/transfer.rs` (new).
- Schema pinned in `docs/BASS_PY_BRIDGE_SPEC.md` (new).
- Tests:
  - `p41_json_roundtrip`: write → read → compare equality.
  - `p41_schema_matches_bass_py_consumer`: consumer-side fixture in
    `tests/fixtures/bridge/` parses without error.

#### WBS

1. Author `BASS_PY_BRIDGE_SPEC.md` in docs/ as the authoritative
   schema — including version field, unit conventions, and grid
   specification.
2. Implement the writer in `transfer.rs`.
3. Add a minimal Python consumer test that demonstrates a round-trip.

#### Merge gate

Two tests pass. Schema doc merged as single-source-of-truth.

#### Audit

- Applies: NO (pure I/O; audit triggers only on physics/numerics changes).

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `BASS_PY_BRIDGE_SPEC.md` (new).
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P4.1 → DONE.

---

### P4.2 — Atlas HDF5 generator

- **Status**: PLANNED.
- **Depends on**: P4.1.

#### Goal

Pre-compute `(type × Σ² × β × x_h)` grid for HTT consumption
(`post_bass_programme_v1.md HI-01`).

#### Outputs

- `src/bridge/atlas.rs` (new) — HDF5 writer using `hdf5-metno` or similar
  maintained crate.
- Tests:
  - `p42_atlas_grid_shape`: grid dimensions match the schema.
  - `p42_atlas_roundtrip`: write → read → compare.
  - `p42_atlas_hash_stable`: SHA-256 of canonical grid output is stable
    across runs (deterministic production).

#### WBS

1. Choose HDF5 crate (`hdf5-metno` preferred; `hdf5` original crate is
   unmaintained on recent HDF5).
2. Implement writer.
3. Grid parameters sourced from `BASS_PY_BRIDGE_SPEC.md`.
4. Determinism test via fixed-seed inputs.

#### Merge gate

Three tests pass. Grid reproduces deterministically.

#### Audit

- Applies: NO (I/O only). Unless a physics quantity is computed newly in
  this PR — in that case, YES.

#### Doc updates

- `DEVELOPMENT_PLAN.md` §1.
- This file.
- `BASS_PY_BRIDGE_SPEC.md` — atlas section.
- `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P4.2 → DONE.

---

### P4.3 — Route B anti-regression guard

- **Status**: DONE (pre-session baseline).
- **Maintenance**: ensure the Route B sentinel `D_2(Σ² = 1e-8) = 0.174112 μK²`
  (reference from
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §11.2)
  remains green throughout the IMEX ladder. If broken, treat as a
  regression — not an acceptable change.
- **Doc**: noted in
  `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` P4.3.

---

## Part IV — Hybrid backup branch (minimal A/B maintenance)

The RODAS5P hybrid is the frozen backup from
[`RODAS5P_HYBRID_BACKUP_PLAN.md`](RODAS5P_HYBRID_BACKUP_PLAN.md). Only the
following ablation steps are carried; everything else is deferred.

### A0 — Shared baseline contract

- **Status**: DONE (same artefact as IMEX-00 `cc35fbd`).

### A5 — Unified full-state acceptance

- **Status**: PLANNED. Required before any honest A/B at IMEX-07.
- **Depends on**: IMEX-05 (callback backend on hybrid).

#### Goal

Implement the hybrid's full-state acceptance test on the same backend as
IMEX-05. This is the only way an A/B comparison at IMEX-07 is meaningful:
both branches must share the callback backend, share the layout, share
the tolerance policy.

#### Outputs

- Hybrid-side full-state acceptance gate (mirror of IMEX-05 scope, but
  using the Rodas5P stepper rather than ARK4).
- Tests: `a5_hybrid_full_state_accept_matches_imex_05` — both paths agree
  to `1e-10` rel on a chosen state fixture.

#### WBS

1. Port the hybrid stepper to call the `LinearProfileCallback` backend
   (mostly already landed at `883f22a`).
2. Add the acceptance gate.
3. Implement the comparison test.

#### Merge gate

Test passes. Hybrid branch green under the shared backend.

### A8 — Production scale-up benchmark (conditional)

- **Status**: CONDITIONAL. Triggered **only** if IMEX-07 signals trouble
  (D_ℓ agreement outside ±5 % at ℓ ≤ 300, or wall time > 30 s on the
  reference hardware).
- **Goal**: head-to-head A/B at production scale to decide between
  continuing IMEX development vs reverting to the hybrid.
- **Outputs**: A/B report at `docs/HYBRID_VS_IMEX_AB_REPORT.md`. No code
  change.

---

## Part V — Document maintenance PRs (non-ladder)

### D-01 — Move `src/pstf_primary/` into a re-export shim

- **Status**: PLANNED. Hygiene. No merge pressure.
- **Scope**: delete `src/pstf_primary/*.rs` and replace with a single
  `pub use crate::solver::pstf_primary::*` shim. Prevents "edited the
  wrong file" incidents (see
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §2.5).
- **Merge gate**: `cargo test --release` green; `cargo clippy` no new
  warnings.

### D-02 — `ENV_VARS.md` catalogue refresh

- **Status**: recurring — refresh at every PR that adds or flips an env
  toggle. Ensures the list in [`ENV_VARS.md`](ENV_VARS.md) matches what
  the code reads.

### D-03 — `PERF_FRESH_*.md` refresh

- **Status**: recurring — refresh whenever wall time / RSS materially
  changes. Trigger: IMEX-05, IMEX-07, P2.3.

---

## Part VI — When a PR does not fit this ladder

If an opportunity arises that does not fit any existing entry:

1. Write the SDD entry in this file **first**, slotted where it fits (new
   number if needed; keep numbering gap-free only within a ladder).
2. Update `DEVELOPMENT_PLAN.md` §3 dependency graph.
3. Only then start work.

This is the same rule as the universal "plan before act" in
[`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) §4.

---

*End of PR_WBS_SDD.md.*
