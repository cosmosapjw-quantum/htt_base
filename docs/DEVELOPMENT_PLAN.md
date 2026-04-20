# BASS Rust Solver — Development Plan (master hub)

**Status**: authoritative plan for ongoing and upcoming work on the bass_rs (Rust)
CMB Einstein-Boltzmann solver, spanning the approximation-free FLRW truth engine
and its extension to Bianchi anisotropic backgrounds.

**How to read this document set**:

- This file is the **hub**: a ledger of completed work, a pointer to the upcoming
  PR sequence, and the procedural contract (audit + documentation maintenance)
  that every PR follows.
- Detailed designs live in companion files referenced here. Read them in the
  order they are cited; each one is self-contained for its scope.
- Memory-only context from prior sessions is now captured explicitly in
  [`docs/SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md).
- Per-PR work breakdown + merge gates live in [`docs/PR_WBS_SDD.md`](PR_WBS_SDD.md).
- Audit + doc-update procedure (self-triggered at every PR boundary) lives in
  [`docs/AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md).
- **Automated execution prompt** (skeleton scaffolding + per-PR triple-
  verification + commit automation driver) lives in
  [`docs/AUTOMATED_EXECUTION_PROMPT.md`](AUTOMATED_EXECUTION_PROMPT.md).

**Reading minimum**: §1 (history) + §3 (next-up PR) + `PR_WBS_SDD.md`
entry for the next-up PR. That alone is enough to pick up the work cold.

---

## §0. Why this document exists

Earlier sessions accumulated planning artifacts across multiple loosely-
linked documents (`ROADMAP_v3`, `IMEX_DECISION`, `RODAS5P_HYBRID_BACKUP_PLAN`,
`PHASE0_D0_AUDIT_REPORT`, `PERF_FRESH`, etc.) and in Claude's memory index
(`user_profile`, `project_arch_constraints`, `feedback_git_workflow`, …).
The constraints, decisions, and measured facts behind every commit must be
reproducible **from the repository alone**, without relying on a
particular Claude session's memory.

This file is the canonical entry point. It consolidates the cross-references,
the completed-work ledger, and the forward PR sequence in one place so that
a new session (or a human reader) can reconstruct context fully.

---

## §1. Completed work — commit ledger

Entries are in reverse chronological order (most recent first). The full
narrative for each commit is captured in
[`docs/SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md).

| SHA | Title | What changed | Evidence |
|---|---|---|---|
| **`661044d`** | IMEX-01: ARK4 tableau validation | Added Prothero-Robinson 4th-order convergence test + embedded-estimator monotone-in-h test on top of the existing 17 audits in `src/solver/imex_ark4.rs`. | `imex01_split_order_of_accuracy_prothero_robinson` (ratio 10.3→12.3), `imex01_embedded_estimator_monotone_in_h` (8.57e9→2.90e5 strict monotone). Total 19/19 module tests green. |
| **`cc35fbd`** | IMEX-00: baseline contract freeze | New `StepperStats` struct surfaced through `PstfKmodeResult`. Reference counters frozen at `(layout=(8,6,0), k=0.01, Planck2018)`: `n_steps=3334`, `n_rejected=253`, `n_jac=3587`, `n_f_eval=28696`, `n_snaps=583`. | 3 new tests — `imex00_baseline_capture` (#[ignore], regeneration), `imex00_baseline_verify_shape_and_counters`, `imex00_baseline_invariant_across_backends`. All green. |
| **`883f22a`** | Phase 2.0: callback-based stage assembly backend | New `LinearProfileSampler` trait + `LinearProfileCallback<F>` streaming profile in `src/solver/rodas5p.rs`. Stepper becomes agnostic to whether matrices are pre-stored or rebuilt on demand. Env-toggle `BASS_PSTF_CALLBACK=1` in PSTF primary. | Measured at PSTF FLRW: (8,6,0) n=352 551 MB → 1.9 MB (**292×**), wall +12 %. (12,8,0) n=680 2057 MB → 7.1 MB (**292×**), wall +3.7 %. 115 → 117 tests (+2 Phase 2.0 equivalence at 1e-14 / 1e-12). |
| **`3e79310`** | Solver decision: IMEX-ARK4 mainline, RODAS5P hybrid backup | Authoritative numerical-method direction selected. Pure IMEX-ARK4 (Kennedy–Carpenter) is the mainline reference path; RODAS5P-centered partitioned hybrid is the frozen backup/benchmark branch. | [`docs/IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §4. Corrections from critique in [`docs/IMEX_DECISION_CRITIQUE_NOTES.md`](IMEX_DECISION_CRITIQUE_NOTES.md). |
| **`c5ae4f9`** | PSTF matrix build: analytical Jacobian path | `pstf_analytical_jacobian` extended to metric + fluid + metric-monopole-source (25 new triplets). `build_pstf_matrix_analytical_into` replaces the unit-vector decomposition. | **Speedups (5900X)**: (8,6,0) 0.190→0.011 ms ×17. (12,8,0) 0.88→0.20 ms ×4.3. (16,16,16) 5.0→0.93 ms ×5.4. (25,15,25) 21.0→2.82 ms **×7.5**. FD regression matches `pstf_full_rhs` to ≤ 1e-6 rel at 4 k-values. |
| **`8310c73`** | Phase 0 correctness audit | Three independent bugs isolated in `compute_flrw_cl_track_a` (MB-95 path). B: ODE solver diverges at k > ~0.03 (`source_jl` → 1e101 at k=0.25). C: Limber formula η_sp sign wrong + 1/k² missing. A: `SourceMode::Full` drops D_2 from 690 → 3.9. | [`docs/PHASE0_D0_AUDIT_REPORT.md`](PHASE0_D0_AUDIT_REPORT.md). Cross-check: PSTF primary does NOT inherit Bug B (verified in `phase0_d0_3_cross_check_pstf_high_k`). |

### 1.1 Pre-session foundation (older commits, not rewritten)

The Rust solver this work builds on was already at the state captured in
[`README.md`](../README.md) and [`PSTF_PRIMARY_INTEGRATION.md`](../PSTF_PRIMARY_INTEGRATION.md).
Specifically:

- `src/solver/sync_gauge_camb.rs` — MB-95 synchronous-gauge CAMB-style solver, ~7300 L.
- `src/solver/pstf_primary/` — 12 modules, PSTF 1+3 covariant primary path.
- `src/solver/rodas5p.rs` — Rodas5P linearly implicit stepper.
- `src/solver/imex_ark4.rs` — Kennedy-Carpenter ARK4(3)6L[2]SA (pre-existing 1417 L scaffold).

The pre-session history is **not replicated here** (it is already in git log).
This ledger covers only the current-session Rust-side solver work.

### 1.2 Parallel Python-side work (not in this document's scope)

The user runs bass_py / HTT / TSC development in the same repository but on
separate code paths (`bass_py/`, `docs/lowell_bianchi/`,
`plots/physics_gallery/`, etc.). Commits from that lane interleave with the
Rust-side commits above. This plan **does not direct Python-side work**;
references are informational only. The
[`docs/BASS_PY_FAST_TRACK_2026-04-18.md`](BASS_PY_FAST_TRACK_2026-04-18.md)
side-track plan remains the reference for the Python track.

---

## §2. Strategic direction (frozen)

The solver direction was fixed in commit `3e79310`. The three non-negotiable
pillars below propagate into every PR that follows.

### 2.1 Approximation-free truth engine (architectural mandate)

Source: [`project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안).

- **Banned as defaults**: TCA pre-phase as IC generator, standard FLRW UFA,
  photon RSA, any FLRW-specific closure formula copied into Bianchi paths.
- **Mandated**: one equation set, many numerical strategies, zero hidden
  physics switches. Solver switches allowed; equation switches forbidden by
  default.

### 2.2 Pure IMEX-ARK4 mainline + RODAS5P hybrid backup

Source: [`docs/IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md).

- **Mainline** — Kennedy–Carpenter ARK4(3)6L[2]SA (pure IMEX). Implicit block:
  Thomson collision (diagonal ℓ ≥ 3 + small dense at ℓ ≤ 2). Explicit: transport
  + metric + fluid + neutrinos.
- **Backup** — RODAS5P-centered partitioned hybrid, implemented only to the
  extent needed for A/B benchmarking at IMEX mainline exit gates. Reference
  at [`docs/RODAS5P_HYBRID_BACKUP_PLAN.md`](RODAS5P_HYBRID_BACKUP_PLAN.md).

### 2.3 Callback-based backend (solver-neutral prerequisite)

Source: Phase 2.0 commit `883f22a`.

`mats_flat ∼ O(N_snap · n²)` pre-materialization is replaced by
`LinearProfileCallback` streaming. The stepper asks for M(η) at arbitrary η via
trait dispatch; each implementation chooses whether to pre-store, cache a pair,
or rebuild on demand. This refactor applies to both mainline (IMEX) and backup
(hybrid) branches identically.

### 2.4 Hard constraints on every PR

From [`docs/SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §2, the
following rules must be obeyed by every PR (not repeated in individual PR
descriptions — they are universal):

- No FLRW-specific approximations as default behaviour.
- No equation-set switching at runtime (kernel/solver switching only).
- No `git reset --soft`, `git rebase`, or other history-rewriting operations.
- Additive commits only; explicit pathspec form `git commit -- <paths>`.
- No branch cleanup unless user explicitly asks.

---

## §3. Upcoming work — PR sequence

Detailed design, inputs/outputs, and merge gates for every PR below are in
[`docs/PR_WBS_SDD.md`](PR_WBS_SDD.md). This section is a high-level index and
dependency graph.

### 3.1 Primary critical path — IMEX mainline

Numbered per [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6.

```
  IMEX-00 (done, cc35fbd)     baseline contract freeze
       │
       ▼
  IMEX-01 (done, 661044d)     ARK4 tableau validation
       │
       ▼
  IMEX-02  ←── NEXT UP        operator split A = A_stiff + A_stream identity check
       │
       ▼
  IMEX-03                     single-k FLRW PSTF primary solve via IMEX-ARK4
       │
       ▼
  IMEX-04                     multi-k end-to-end BASS_IMEX=1 toggle
       │
       ▼
  IMEX-05                     callback-based stage assembly as production default
       │
       ▼
  IMEX-06                     polarization activation (Θ₂↔E₂ recoupling)
       │
       ▼
  IMEX-07                     production truncation scale-up (Lγ=25, Lν=15, Lpol=25)
       │
       ▼
  IMEX-08                     Bianchi I m-major extension
       │
       ▼
  IMEX-09                     massive-ν momentum bins
```

### 3.2 Parallel infrastructure — ROADMAP_v3 Phase 2.1–2.5

These can overlap with IMEX-02..07 since they share the callback backend
introduced by Phase 2.0. Open as capacity permits; not on the critical path.

- **P2.1** (ℓ, m) m-major layout formalization (`LmLayout` full, m ∈ {-m_max..+m_max})
- **P2.3** sparse Jacobian backend (`faer-sparse` preferred)
- **P2.4** adaptive ℓ_max + sponge boundary (replaces UFA)
- **P2.5** matrix line-of-sight projector (Bianchi-ready)
- **P2.2** is DONE at FLRW m=0 in `c5ae4f9`; m ≠ 0 extension is folded into IMEX-08.

### 3.3 Integration — Phase 4 (bass_py bridge)

- **P4.1** `BianchiTransferFunctions(k)` JSON/CSV producer
- **P4.2** Atlas HDF5 generator for HTT consumption
- **P4.3** Route B anti-regression guard (already present)

Triggered after IMEX-07 succeeds. See
[`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md)
Phase 4 for the interface specification.

### 3.4 Backup branch — RODAS5P hybrid (A0, A5, A8)

The hybrid backup keeps a minimal A/B baseline:

- **A0** shared with IMEX-00 (done).
- **A5** unified full-state acceptance — required before any A/B comparison at IMEX-07.
- **A8** production scale-up benchmark — only if IMEX-07 signals trouble.

Other ablation steps (A1–A4, A6) are deferred indefinitely. Status tracked in
[`docs/RODAS5P_HYBRID_BACKUP_PLAN.md`](RODAS5P_HYBRID_BACKUP_PLAN.md).

---

## §4. Per-PR SDD template

Every PR in [`PR_WBS_SDD.md`](PR_WBS_SDD.md) follows the template below.
Authors add new entries by copying the template and filling it in.

```markdown
## PR-XX — Title

### Status
<PLANNED | IN PROGRESS | DONE {commit-sha}>

### Depends on
- <previous PR id>, <prerequisite docs>

### Goal (one sentence)
Exactly what this PR delivers in one line.

### Inputs (what already exists)
- Source files touched: `src/...`
- Tests that must remain green: <list>
- Reference baseline: IMEX_00_REFERENCE_* (or equivalent)

### Outputs (what this PR produces)
- New source files / symbols
- New tests (name + merge-gate claim)
- New env vars / toggles

### WBS — concrete work items
1. <atomic task> — file(s)
2. <atomic task> — file(s)
...

### Merge gate (automated checks)
- <assertion 1>: test name, threshold
- <assertion 2>: test name, threshold
- Regression: full pstf_primary suite still green (N passed, 0 failed)

### Audit (self-triggered; see AUDIT_AND_UPDATE_PROCEDURE §1)
- Applies: <YES / NO — skip audit reasoning>
- If YES, scope: <which files / which claims>

### Doc updates (self-triggered; see AUDIT_AND_UPDATE_PROCEDURE §2)
- `docs/DEVELOPMENT_PLAN.md` §1 commit ledger: add row with SHA
- `docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md` §P2.6 / P2.X: mark PR DONE
- <any other doc affected>

### Killed directions (learned during this PR)
<optional — what won't work and why>
```

---

## §5. Self-audit and documentation automation

Full procedure in [`docs/AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md).
Summary:

- **Every PR boundary** → run the integrated phys-math-code audit from
  [`docs/audits/AUDIT_PROMPT.md`](audits/AUDIT_PROMPT.md). Self-triggered; do not
  wait for user reminder. P0/P1 findings fixed in the same session as
  `AUDIT(<pr-tag>): ...` commits before the phase-closing commit.
- **Every commit** → append a row to §1 of this file. Update
  [`ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md)
  if the PR lives in its phase list. For Rust-side solver PRs, also update
  [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6 if the PR
  lands on the mainline ladder.
- **Rotating task list** — `TodoWrite` tracks the current session's subgoals;
  after commit, the PR entry in [`PR_WBS_SDD.md`](PR_WBS_SDD.md) changes status
  from PLANNED → DONE with the commit SHA and an "evidence" link to the
  relevant test.

---

## §6. Glossary — conventions used across this document set

| Term | Definition |
|---|---|
| **PSTF primary** | 1+3 covariant Projected Symmetric Trace-Free solver (`src/solver/pstf_primary/`). The production target. |
| **MB-95** | Synchronous-gauge CAMB-style solver in `src/solver/sync_gauge_camb.rs` + `flrw_cl_pipeline.rs`. Now reclassified as reference prototype (pre-session trajectory). |
| **Callback backend** | Phase 2.0 `LinearProfileCallback<F>` streaming matrix profile. Replaces `mats_flat` pre-materialization. |
| **IMEX mainline** | Kennedy–Carpenter ARK4(3)6L[2]SA additive Runge-Kutta as the Phase 2+ production solver. |
| **Hybrid backup** | RODAS5P-centered partitioned hybrid (`docs/RODAS5P_HYBRID_BACKUP_PLAN.md`) kept as frozen A/B benchmark branch. |
| **Truth engine** | The approximation-free solver configuration. No TCA/UFA/RSA. |
| **LB-N** | Lowell-Bianchi development phases (`docs/lowell_bianchi/`), Python-side. Not in this plan's scope. |
| **Phase X.Y** (ROADMAP_v3) | Rust-side roadmap phase numbered per `ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`. |
| **Baseline contract** | IMEX-00 frozen reference counters + sample-index hex-packed values used as comparison anchor for all subsequent PRs. |

---

## §7. Related documents (read-order index)

1. **Read first**: this file. Get overview + history + next-up PR.
2. **Next**: [`docs/SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) — all user-provided constraints, project invariants, killed directions.
3. **Next**: [`docs/PR_WBS_SDD.md`](PR_WBS_SDD.md) — detailed design for the PR you are about to start.
4. **Next**: [`docs/AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) — the audit + doc-update contract you will follow.

Authoritative reference documents (already frozen):

- [`docs/IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) — solver-choice authority.
- [`docs/IMEX_DECISION_CRITIQUE_NOTES.md`](IMEX_DECISION_CRITIQUE_NOTES.md) — critique that refined the decision; historical record only.
- [`docs/RODAS5P_HYBRID_BACKUP_PLAN.md`](RODAS5P_HYBRID_BACKUP_PLAN.md) — backup branch specification; frozen.
- [`docs/PHASE0_D0_AUDIT_REPORT.md`](PHASE0_D0_AUDIT_REPORT.md) — three bugs located in `compute_flrw_cl_track_a`, baseline-freeze reference for correctness work.
- [`docs/PERF_FRESH_2026-04-18.md`](PERF_FRESH_2026-04-18.md) — measured performance baseline; supersedes legacy `PERF_NOTES.md`.
- [`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md) — phase-structured roadmap; updated per §5 at every PR.
- [`project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안) — architectural charter (bans).
- [`project/04_implementation_specs/solver_strategy_5566dof_v2.md`](../project/04_implementation_specs/solver_strategy_5566dof_v2.md) — IMEX cost analysis.
- [`docs/audits/AUDIT_PROMPT.md`](audits/AUDIT_PROMPT.md) — the self-audit template.

---

## §8. How this plan evolves

This plan itself is a living document. The update protocol:

1. **Adding a PR**: write the SDD entry in `PR_WBS_SDD.md` first, then add a
   pointer row in §3 of this file.
2. **Closing a PR**: move the SDD entry to DONE, add a row to §1 of this file.
3. **Adding a new constraint / killed direction**: edit
   `SESSION_KNOWLEDGE_LEDGER.md` first, then reference from §2.4 of this file.
4. **Changing the solver direction**: do not edit this file directly — open
   a new IMEX_DECISION addendum and link it from §2.

The plan is considered stale if the most-recent commit in §1 is more than two
commits behind `git log --oneline -1`. This is caught by the audit procedure
(see `AUDIT_AND_UPDATE_PROCEDURE.md` §3).

---

*End of DEVELOPMENT_PLAN.md.*
