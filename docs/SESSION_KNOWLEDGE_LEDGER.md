# BASS Rust Solver — Session Knowledge Ledger

**Purpose**: capture, as explicit in-repo documentation, all project-level
knowledge that previously lived only in conversational memory across Claude
sessions. Reading this file plus [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md)
gives a new session the full operating context without needing to inherit any
prior chat state.

**Scope**: knowledge specifically relevant to Rust-side bass_rs CMB solver
work. Python-side (bass_py / HTT / TSC / LB-N lowell_bianchi) rules are noted
when they affect shared resources (notably the shared git repo) but their
development plan is out of scope here — see
[`docs/BASS_PY_FAST_TRACK_2026-04-18.md`](BASS_PY_FAST_TRACK_2026-04-18.md).

**Structure**: this document is organised by *invariant kind*. Each entry
states the rule, its origin, the evidence / incident that motivated it, and
how to apply it. If a rule is superseded, mark it so and keep the history
here — do not delete.

---

## §0. Document status

This is v1 of the ledger. It supersedes the implicit memory entries that
previously carried this context. Updates land additively: new rules at the
bottom of the relevant section, with date and the commit or conversation that
introduced them.

---

## §1. User profile

### §1.1 Identity and domain

- **Who**: Jiwon, PhD researcher at **Soongsil University OMEG Institute**.
- **Thesis**: *"Tetrad-Based Departure Decomposition for FLRW Departure in
  Bianchi Anisotropic Cosmologies"*.
- **Language**: Korean primarily; English technical terms used freely.
- **Technical depth**: expert in
  - PSTF (Projected Symmetric Trace-Free) 1+3 covariant formalism,
  - Maartens–Ellis–Stoeger kinematic bounds,
  - MB-95 synchronous-gauge linearized Boltzmann hierarchy (Ma & Bertschinger 1995),
  - Rodas5P implicit ODE integration (Hairer–Wanner II §IV.7),
  - CMB T+E+B spectrum production.
- **Rust fluency**: high — no need to explain language fundamentals.
- **Reference codebases**: CAMB / CLASS for performance benchmarking; SymBoltz
  for approximation-free throughput comparison.

### §1.2 Work style preferences

- **Correctness before performance**. Bit-identical regression guards must be
  preserved across optimisation. Specific anchor: `D_2 = 1002.086744 μK²` held
  bit-identical across 14 consecutive commits — must not be broken by a
  "speed win".
- **Roadmap-driven**. User operates via numbered PR ladders with weighted
  scorecards (`PR-020` … `PR-026` were the prior cycle; the current cycle is
  IMEX-00 … IMEX-09, see §3 of [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md)).
- **Parallel tracks**. Rust main-line and Python side-track run in the same
  repository, interleaved by commit. Do not propose reorganising the repo or
  splitting into separate projects — see §5 on git workflow.

### §1.3 How to tailor responses

- Assume a senior-cosmologist audience. Do not explain what PSTF, MB-95, ISW,
  polarisation hierarchies, or Bianchi models are. Do explain numerical
  choices and Rust-specific tradeoffs.
- When a numerical decision has a physics consequence, lead with the physics
  consequence.
- When a Rust refactor has a bit-identicity risk, call that out first.

---

## §2. Project identity and invariants

### §2.1 What BASS is

- **BASS** = "Boltzmann And Spectrum Solver" / "Bianchi Anisotropy Solver".
- **Phase 1** = PSTF Primary Migration: move the production CMB spectrum
  pipeline from the legacy MB-95 synchronous-gauge solver
  (`src/solver/sync_gauge_camb.rs`, ~7.3 kL) to the 1+3 covariant PSTF
  primary solver (`src/solver/pstf_primary/`, 12 modules, ~5.6 kL).
- **Beyond Phase 1**: Bianchi-anisotropic extension is the research goal.
  Every design decision is pre-committed to being Bianchi-ready, not FLRW-only.

### §2.2 Architecture mandate (frozen)

Source document:
[`project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안)
(2368 lines, the project's architectural charter).

**Hard bans (defaults OFF)**:

- **TCA as pre-phase IC generator** — the "reduced system → reconstruct full
  state → switch to full" pattern is banned. If TCA reappears, it must be
  *closure-in-place* (same equation set; fast variables derived by algebraic
  closure from the Jacobian; no state-dimension change).
- **Standard FLRW UFA** — default OFF. If enabled at all, neutrino sector
  ONLY, behind a residual monitor, with Bianchi mode hard-disabled.
- **Photon RSA** — banned outright. This approximation eats the low-ℓ / ISW /
  reionisation / directional signals the research is hunting.
- **FLRW-specific closure formulas copied verbatim into Bianchi paths** —
  banned. Any closure must be formulated in operator-norm terms, e.g.
  `ε_TCA^op ≈ τ_c · ||Π_fast · L · Π_slow||`.

**Architectural mandate**:

- One equation set, many numerical strategies, **zero hidden physics
  switches**. Solver / preconditioner / kernel switches allowed; equation-set
  switching is forbidden by default.
- Truth engine first. Full hierarchy, no approximations, sparse implicit
  solve. Every approximation is a "reduced-model hypothesis" gated by a
  residual monitor against truth.
- Operator split: `RHS = 𝒞(collision) + ℱ(free-stream) + 𝒢(Bianchi geometry) + ℳ(metric/matter) + s`.
  Solver + preconditioner choices flow from this split, not from FLRW
  intuition.
- Sparse Jacobian is the real battle, not integrator choice. Generated
  analytic Jacobian + exact sparsity pattern + factorization reuse beats
  clever integrators on production-scale CMB problems.
- **(m)-major state ordering**, not species-first. Bianchi (ℓ, m) coupling
  (ℓ → ℓ±1, m → m, m±1, m±2) has band structure that an m-major layout exposes.
- Matrix line-of-sight as primary projector; scalar FLRW LoS is its special
  case — not the other way around.

**How to apply** (on every PR):

> When proposing speed optimisation, ask
> "does this close the reference-code speed gap by approximation (**banned**)
> or by sparse-Jacobian + linear-algebra + operator-split engineering
> (**allowed**)?" Only the second category counts.

### §2.3 Design law for `src/solver/pstf_primary/`

- All code targets Bianchi + tilt from the start. FLRW is a special case via
  parameters (`σ = 0, tilt = 0`), NEVER hardcoded.
- BANNED inside PSTF primary: scalar Bardeen ODE, algebraic Poisson, isotropic
  `c_s²`, scalar `v_b` collision (must use electron-frame ζ̃).
- Never propose changes that sacrifice Bianchi + tilt readiness for an
  FLRW-only speedup.

### §2.4 Sacred regression anchor

- `D_2 = 1002.086744 μK²` is bit-identical across 14 consecutive commits and
  is the Phase-1 SWOO (single-word overlapping oracle) regression anchor.
- Every optimisation PR must run the full PSTF test suite (reference count in
  this file updates per PR) + the `D_2` regression check.
- "It should be equivalent" is not acceptance; only bit-identical passes.
- Future per-k parallelism via rayon is planned; the reduction must remain
  deterministic to keep this invariant under threading.

### §2.5 Two `pstf_primary` directories exist — edit only the canonical one

- `src/pstf_primary/` — original snapshot copy; **stale, do not edit**.
- `src/solver/pstf_primary/` — canonical integrated path (registered via
  `src/solver/mod.rs`). **Edit here**.
- Rationale: integration was performed via
  [`PSTF_PRIMARY_INTEGRATION.md`](../PSTF_PRIMARY_INTEGRATION.md), which
  placed the canonical tree under `src/solver/pstf_primary/`. The top-level
  `src/pstf_primary/` differs in trivial ways (one comment line in
  `matrix.rs`) but edits there silently do not affect production.
- Clean-up direction (not urgent): either delete the top-level copy once all
  references resolve to the canonical path, or convert to a `pub use`
  re-export shim. Track under ROADMAP_v3 P2 hygiene bucket.

---

## §3. Performance landscape (frozen measurement)

### §3.1 Targets and reference points

- **Target wallclock**, single end-to-end run on low-spec hardware: **10–15 s**.
- Reference codes:
  - CAMB ≈ 5 s (achieved via TCA/UFA/RSA — speed bought with approximations
    BASS forbids, so CAMB parity is NOT a valid target).
  - CLASS ≈ 7 s.
  - **SymBoltz (approximation-free)** ≈ 3.1 s — the legitimate comparator.
- Pre-optimisation BASS PSTF projected: ~6 h per run at production scale
  (498 k-modes × 42.79 s/mode), unworkable.
- Nominal improvement needed: ~1500–2000× from the pre-optimisation baseline.

### §3.2 Fresh measured baseline

Measured on AMD Ryzen 9 5900X (24T / 12C), Ubuntu 24.04, rustc 1.94.1. Full
numbers: [`docs/PERF_FRESH_2026-04-18.md`](PERF_FRESH_2026-04-18.md).

| Config | Wallclock | maxRSS |
|---|---|---|
| `fast_validation` (k_max = 0.03, SwOnly) | 5.129 ± 0.135 s (n = 5) | — |
| `default_track_a` (production scale) | 11.119 ± 0.358 s (n = 3) | 5.2 GB |

**Top CPU consumers** (perf record -F 497, prod workload, ~95% total):

1. `lu_solve_factored_flat_into` — 26.3 % self (`src/core/lu.rs:133`)
2. `linear_profile_rhs_only_into` — 23.0 % self (`src/solver/rodas5p.rs:103`)
3. `step_linear_profile_rodas5p_into` — 20.1 % self (`src/solver/rodas5p.rs:237`)
4. `lu_factor_in_place_flat_into` — 17.7 % self (`src/core/lu.rs:62`)
5. `linear_profile_rhs_jac_flat_into` — 5.8 % self (`src/solver/rodas5p.rs:123`)

**Phase-timer breakdown** (pipeline-internal):
`ksolve = 93.3 %`, `bessel = 6.5 %`, `vis = 0.2 %`, `kgrid = 0.0 %`.

### §3.3 The "Bessel 57.7 %" result is superseded

Legacy [`PERF_NOTES.md`](../PERF_NOTES.md) claimed Line-of-Sight Bessel
evaluation at 57.7 % of total. That is **empirically false** on the current
`compute_flrw_cl_track_a` pipeline (maximum 6.5 % at production scale). The
legacy measurement either used a different path (possibly raw
`solve_stacked_native_rodas5p` without LoS) or the code has since evolved past
that bottleneck.

**Consequence for optimisation choices**: do not optimise Bessel first.
Optimise the ODE inner loop (rodas5p + LU). Specifically:

- The 8 RODAS5P stages each re-sample the matrix profile; within a single
  step the matrix is linear in τ and has `a_buf` / `da_buf` available.
  Stage-level Taylor reconstruction is the largest single target.
- `W = I/(γh) − J` assembly can fuse with the Jacobian output.
- LU is already SIMD-friendly (from PR-PERF-05 iter/zip path). Further LU
  wins require small-`d` const-generic unrolling, which risks bit-identicity
  and needs a deliberate trade-off.
- `maxRSS = 5.2 GB` is already uncomfortable for low-spec hardware — the
  per-k-mode history arrays should be streamed into the LoS accumulator
  rather than retained (compare §3.2 row 2).

### §3.4 Build-profile findings

- `lto = "fat"` + `codegen-units = 1` → **+4.6 % regression** on
  `fast_validation` (i-cache pressure). Reverted. Keep `lto = "thin"`.
- `target-cpu=x86-64-v3` on MB-95 production path → regression (i-cache
  pressure on AVX2 paths).
- `target-cpu=native` not re-tested on PSTF primary; legacy doc indicates a
  regression. Retest only if a specific kernel becomes the bottleneck.

---

## §4. Profiling and observability toolchain

User has installed:

**Pre-installed**: `perf`, `valgrind`, `heaptrack`, `cargo-flamegraph`.

**System (apt)**: `linux-tools`, `hotspot` (perf GUI), `massif-visualizer`,
`google-perftools`, `llvm`.

**Cargo (`cargo install`)**: `samply`, `iai-callgrind-runner`, `hyperfine`,
`cargo-show-asm`, `cargo-llvm-lines`, `cargo-bloat`, `cargo-pgo`,
`cargo-machete`, `cargo-udeps`.

**Dev-dependency candidates for `Cargo.toml`** (add when first used, not
pre-emptively): `criterion 0.5`, `iai-callgrind 0.14`, `dhat 0.3`, `pprof 0.13`.

**System tuning already applied**: `kernel.perf_event_paranoid = 1`,
`kernel.kptr_restrict = 0` via `/etc/sysctl.d/99-perf.conf`.

**Tool selection by task**:

| Work | Tool |
|---|---|
| Algorithmic refactor | `samply` (Firefox profiler UI) |
| Microbench A/B | `criterion` + `iai-callgrind` (cycle-precise) |
| End-to-end wallclock | `hyperfine` |
| SIMD / codegen verification | `cargo-show-asm` |
| Heap behaviour | `heaptrack` + `dhat` |
| Final sealed binary | `cargo-pgo` (Profile-Guided Optimization) |

When producing A/B numbers for a PR, prefer `hyperfine` for wallclock and a
criterion bench for cycle-precise kernel comparison. Report `n` samples,
median, and stddev; do not quote a single-run number.

---

## §5. Git workflow — hard constraints

**Why this section exists**: the repository hosts three interleaved lanes
(bass_rs Rust, bass_py Python, `docs/lowell_bianchi/` Python LB-N). History
rewriting or branching creates downstream reconciliation difficulty that the
user has explicitly asked to avoid.

### §5.1 Rules

1. **Additive, forward-only commits**. Never propose `git reset --soft`,
   `git rebase`, or branch cleanup unless the user explicitly asks for them.
2. **If an unintended file bundle lands in a commit and the result is
   functionally correct, leave it**. The user confirmed this with the
   IMEX_DECISION commit `3e79310` which inadvertently bundled
   `docs/lowell_bianchi/` files from an in-flight Python-side task: the user
   chose option (1) "keep as-is" to avoid disturbing their Python integration
   trajectory.
3. **Stage specific files, never `git add .` / `git add -u` / wildcard adds**.
4. **Before every commit, run `git status --short` and visually verify** the
   staged set matches exactly what the commit message describes.
   Rationale: earlier commit `99465e5` (HJ-02b) inadvertently pulled in
   `bass_py/bass/transport/*` + gallery-lane files from the index; per the
   additive-commits rule it could not be retroactively split.
5. **Always invoke** `git commit -- <path1> <path2> …` **with explicit pathspec
   arguments**, never bare `git commit`.
   Rationale: another lane's commit firing between the status check and the
   commit call can repopulate the index. The trailing `-- <paths>` form makes
   git commit exactly the listed paths from the index and closes that race.
   (Incident reference: commit `4eb044b` recurred the earlier stray-bundle
   failure even with the `git status` gate because of this TOCTOU hole.)
6. If `git status` shows unexpected staged items, flag to user but default
   to keep-as-is unless they direct otherwise.
7. Rust + Python files touched in the same session go into a single
   forward-moving commit rather than being split into branches.
8. Commit authorship is the user's git identity; the
   `Co-Authored-By: Claude Opus 4.7` trailer is fine.

### §5.2 `project/` is local-only — never stage it

The `project/` directory is **local workspace only** (manuscript drafts, TeX
sources, planning docs). The `/project` entry in `.gitignore:126` is intentional.

- Never run `git add -f` on a `project/` path.
- Never stage a `project/` path even if `git status` suggests it.
- Manuscript gates like "chapter grows from X to Y lines" or "banned-vocab
  scan passes" are verified by inspecting the working tree + the committed
  audit log; the `.tex` files themselves are not the commit artefact.
- Audits (`docs/audits/AUDIT_PHASE_*.md`) and dossier appendices
  (`docs/dossier/A*.md`) are the committed record of manuscript work — put
  the load-bearing numbers / quotes there.
- If a future plan line reads "ship `project/00_manuscript/chX_*.tex`",
  interpret it as "update the working tree + record the gate verification
  in the audit log".

Rule introduced after two prior commits force-added
`project/00_manuscript/ch11_error_hierarchy.tex` et al. to satisfy a
manuscript-landing gate. The user's response: *"do not add anything inside
'project'. they are local 'inside' things."*

---

## §6. Phase-boundary self-audit (mandatory)

### §6.1 Rule

At every phase-boundary commit (on either the Rust main-line or the Python
LB-N lane), execute the full integrated phys-math-code audit from
[`docs/audits/AUDIT_PROMPT.md`](audits/AUDIT_PROMPT.md) **before** writing
the phase-closing commit. Self-triggered; never wait for the user to remind
or paste the prompt.

### §6.2 Triggering conditions (any one)

- About to make a commit whose message matches `^LB-\d+:`,
  `^Phase LB complete`, `^IMEX-\d+:`, or `^.*rotate NEXT_SESSION_PROMPT`.
- Work spans multiple commits and the user signals phase closure
  (e.g. "LB-2 완료", "Phase B1 done", "이 phase는 끝").
- About to rotate `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md` §2 to the
  next phase template.

### §6.3 Procedure (do without prompting)

1. Load `docs/audits/AUDIT_PROMPT.md` and execute STEPs 0–8 of the audit
   inline. Audit is **pre-authorised**; do not ask permission.
2. Run any Python sanity checks / array-tamper tests needed to confirm
   failure modes empirically (not just by inspection).
3. For every P0/P1 finding: apply the minimal repair plan (max 3 patches),
   add corresponding invariant / regression tests, run the full pytest +
   cargo test suite, confirm green baseline.
4. Commit the fixes as `AUDIT(<phase-tag>): <short>` (e.g.
   `AUDIT(LB2): friedmann_residual tautology fix`). The hook
   [`.claude/hooks/check_phase_boundary_audit.py`](../.claude/hooks/check_phase_boundary_audit.py)
   emits a reminder if a phase-boundary commit is attempted without a
   preceding `AUDIT` commit; do not rely on it, self-trigger.
5. For P2/P3 findings: log them in
   `docs/audits/AUDIT_PHASE_<tag>_<YYYY-MM-DD>.md` using the format in
   [`docs/audits/AUDIT_PHASE_LB1_2026-04-18.md`](audits/AUDIT_PHASE_LB1_2026-04-18.md).
   Carry forward as next-phase prerequisites; do NOT attempt to fix in the
   current phase.
6. Stamp `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §1` with
   `Last audited: <ISO date>`.
7. Only after steps 1–6 is the phase-closing commit produced. Audit commit
   and phase commit are **separate commits**.

### §6.4 Non-negotiables

- Do not propose framework swaps, mass refactors, or structural aesthetics
  fixes as the primary audit response.
- Do not conflate "the equation is correct" with "the code implements it"
  with "the numeric result is trustworthy".
- A passing test whose default mode is tautological is not a passing test —
  verify the test actually probes what its name claims.
- Never skip the audit because "the tests pass" or "the phase was small" —
  the entire point of the audit is that passing tests are not sufficient
  evidence.

### §6.5 Evidence this rule is load-bearing

The first audit cycle (post-LB-1) caught two P1 failure modes that would
have silently propagated: `_PLANCK18` SSOT drift (Ω sum = 1.000092, not
flat) and the `friedmann_residual` tautological default mode. Both passed
all existing tests. Without the audit, LB-5 integrator would have inherited
a latently-broken flat-closure contract.

---

## §7. Phase-boundary physics-gallery refresh

### §7.1 Rule

At every phase boundary on the Python LB-N lane (any commit that rotates
`NEXT_SESSION_PROMPT`), the following gallery extension is **mandatory**:

1. Extend `scripts/make_physics_gallery.py` with either a new topic
   directory `NN_<topic>/` OR new plot functions inside an existing topic
   covering every physical quantity this phase delivered. Prefer
   parameter-swept plots over single-point snapshots.
2. Register the new functions in `CATALOG` at the bottom of that script.
3. Run `venv/bin/python scripts/make_physics_gallery.py`
   (or `--only NN_<topic>`) and confirm every plot renders without
   `[FAIL]` lines.
4. **Visually inspect each new PNG** using the `Read` tool on the saved
   file path. Correct issues (wrong axis ranges, mislabelled legends,
   mathtext errors, misleading titles, missing unit tags,
   physics-convention drift) BEFORE committing.
5. Update `plots/physics_gallery/README.md` with new entries
   (topic header + per-file descriptions) and bump the "Total" line.
6. Commit the extended script + regenerated PNGs + README update in the
   same session, alongside the phase commit.

### §7.2 Why

Plots are the highest-bandwidth phys-math-code cross-check the project owns.
If the code and tests pass but the gallery looks wrong, the unit convention
is drifting. Catching this in the phase that introduced the physics is
dramatically cheaper than debugging it downstream.

### §7.3 No-op phase escape hatch

If a phase introduces no new plottable physics (pure plumbing,
interface-only work, closure without new physics), document that fact in
the phase audit log `docs/audits/AUDIT_PHASE_LB<n>_<date>.md` as an explicit
"gallery: no-op this phase" line — do NOT silently skip.

### §7.4 Infrastructure regression case

If rendering infrastructure (matplotlib version, `plot_style`, bass_py API)
changes under the gallery, regenerate the full set via
`scripts/make_physics_gallery.py` without `--only` and check no pre-existing
plot regresses.

### §7.5 Rust-side applicability

The gallery rule is a Python-lane (LB-N) constraint as of its introduction.
Rust-side solver PRs (IMEX-NN) do not need to touch the Python gallery
unless they change a Python-exposed interface (`pyo3` surface). The
Rust-side equivalent is the audit log in `docs/audits/AUDIT_PHASE_<tag>.md`
plus any committed perf table in `docs/PERF_FRESH_*.md`.

---

## §8. Killed directions (do not re-propose without new evidence)

### §8.1 LTO fat + single codegen unit

Tried: `lto = "fat"`, `codegen-units = 1` in the release profile.
Result: **+4.6 % wallclock regression** on `fast_validation`. Cause: i-cache
pressure on the fused binary.
Action: reverted; keep `lto = "thin"`, default codegen units.
Do not re-propose without first profiling i-cache misses on the current
binary — the balance can shift but has not as of the measurement date.

### §8.2 Phase 1.1 fused interpolation + matvec

Tried: fused `interp(a_buf) · v = interp(mats_flat) · v` at step time.
Implementation preserved FP ops so that bit-identicity held
(`v0 + w·(v1−v0)` hex-matched on 9 `D_ℓ` values).
Result: wallclock A/B within a single binary, `BASS_P11_OFF` toggle, showed
`Δ = +0.094 s` (fused path 0.8 % slower), `Δ/SE = 0.3σ` — no measurable
improvement.
Cause: `mats_flat` fits in L3 (5.76 MB at production). The two-pass form
benefits from streaming-prefetch over `base0` then `base1`; the fused form
interleaves `base0` / `base1` reads across `N²` stride, which is worse for
the hardware prefetcher. The `a_buf` intermediate fits in L1, so
eliminating it saves ~0 wallclock despite a ~50 % on-paper memory-traffic
reduction.
Lesson: "redundant memory materialisation" reasoning fails when the
intermediate fits in L1. Bottleneck is LU kernel intrinsic flop count
(~44 %), not materialisation overhead.
Action: reverted cleanly; bit-reference tests retained for reuse under
future kernel-level optimisations.
Do not re-propose this without a cache-level measurement that shows the
intermediate no longer fits in L1.

### §8.3 `target-cpu=x86-64-v3` on the MB-95 production path

Tried for MB-95's Bessel LoS loop. Result: wallclock regression due to
i-cache pressure on AVX2 paths. Reverted. Not retested on PSTF primary
— retest only if a specific kernel is shown to be the bottleneck.

### §8.4 Fixing `compute_flrw_cl_track_a`

Phase 0 audit found three independent bugs on this path
(see §9). Do **not** attempt to fix them. That path is the reference
prototype that MB-95 occupies; it was already scheduled for demotion in
favour of `compute_pstf_cl_track_a` built from Phase 1 onward. Fixes go
into the new PSTF path, not into the MB-95 reference.

---

## §9. Phase 0 correctness-audit findings (frozen)

Audit report: [`docs/PHASE0_D0_AUDIT_REPORT.md`](PHASE0_D0_AUDIT_REPORT.md).
Three independent bugs were isolated on `compute_flrw_cl_track_a` (MB-95 path).

### §9.1 Bug B (critical) — ODE solver diverges at high k

`solve_kmode_with_history` produces `source_jl` values that grow
exponentially above `k ≈ 0.03`. At `k = 0.25` the source reaches `~10¹⁰¹`
(not NaN, astronomical). Growth rate `≈ 10⁵` per k-octave — hallmark of a
step-size / tolerance instability. An `ell_max_gamma` sweep from 12 to 200
does not fix it, ruling out cutoff reflection.

Likely cause: Rodas5P step controller (`rtol = 1e-6, atol = 1e-9`)
inadequate for oscillatory high-k photon sector.

Cross-check: **PSTF primary does NOT inherit this bug**. Verified in
`phase0_d0_3_cross_check_pstf_high_k`, which ran
`pstf_solve_kmode` at `k ∈ {0.01, 0.03, 0.1, 0.25}` and confirmed bounded
output across the range.

### §9.2 Bug C (high, pipeline level) — Limber formula errors

At `src/solver/flrw_cl_pipeline.rs:345`:

- `eta_sp = ν / k` — wrong. Should be `η₀ − ν / k` (stationary phase of
  `j_ℓ(k(η₀ − η))`).
- `1/k²` factor missing from `cl += π/(2ℓ+1) × Δ² × S² × dlnk × (4/9)`.

### §9.3 Bug A (medium, pipeline level) — Full-mode D₂ collapse

`SourceMode::Full` via `extract_source_grid` drops `D_2` from 690 → 3.9 at
`fast_val` scale vs `SwOnly`. Suspected cause: ISW forward-FD noise or
`(ψ+φ)` sign mismatch. Deferred: the full pipeline is replaced in Phase 1,
so this bug does not block the Phase 1 landing.

### §9.4 Test probes retained in tree

`phase0_d0_1a_source_mode_matrix`, `phase0_d0_1c_dl_profile_full_mode`,
`phase0_d0_2b_ell_max_gamma_sweep`, plus environment gates
`BASS_SRC_PROBE`, `BASS_LIMBER_PROBE`. All `#[ignore]`-marked, opt-in.

### §9.5 Significance for the overall plan

`default_track_a` (k_max = 0.25, `SourceMode::Full`) — the config most
prospective users would try — has **never actually worked**. Only
`fast_validation` (k_max = 0.03, `SwOnly`) produces physical spectra, by
staying under the k-threshold and below the Limber boundary.

This matches the independent demotion of MB-95 → reference prototype and
validates the
[`project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안)
charter's prediction of exactly this failure triad (ISW FD noise, cutoff
reflection, narrow k-grid). Architectural direction confirmed.

---

## §10. Solver infrastructure inventory (frozen snapshot)

This section documents what already existed in the Rust tree at the start
of the current plan cycle. Not a description of what will change — see
[`PR_WBS_SDD.md`](PR_WBS_SDD.md) for forward work.

### §10.1 Crate structure

- `bass_rs` v0.1.0, Rust edition 2021.
- Crate type: **cdylib** (for Python via `pyo3`).
- Key dependencies: `pyo3 0.21`, `numpy 0.21`, `rayon 1.8`, `rayon-core 1.12`,
  `nalgebra 0.34`, `mimalloc 0.1.48` (`default-features = false`),
  **`diffsol 0.10` with the nalgebra feature**.
- Dev dependency: `pprof 0.13` (flamegraph + protobuf).

### §10.2 Custom solver modules (already present)

| File | Role | Size |
|---|---|---|
| [`src/solver/rodas5p.rs`](../src/solver/rodas5p.rs) | Linear-profile Rodas5P stepper. Takes a precomputed `LinearProfileDyn` (M(τ) matrix profile sampled at η nodes, interpolated linearly). | ~304 L (pre-Phase 2.0) |
| [`src/solver/nonlinear_rodas5p.rs`](../src/solver/nonlinear_rodas5p.rs) | Nonlinear stiff stepper. Provides `ScalarOde` + `SmallVectorOde<N≤16>` traits. Implements Hairer–Wanner II §IV.7 Rosenbrock stage equations: `(I/(γh) − J)·kᵢ = f(tₙ + αᵢ·h, yₙ + Σ aᵢⱼ·kⱼ) + J·Σ cᵢⱼ·kⱼ/h + γ·h·fₜ`. 8-stage tableau, embedded error. | ~528 L |
| [`src/solver/diffsol_bdf.rs`](../src/solver/diffsol_bdf.rs) | diffsol BDF wrapper, fallback for very stiff multistep. | ~276 L |
| [`src/solver/imex_ark4.rs`](../src/solver/imex_ark4.rs) | Kennedy–Carpenter ARK4(3)6L[2]SA scaffold. 17 tableau-level audits pre-existing; IMEX-01 adds two end-to-end gates. | ~1.4 kL scaffold |

### §10.3 MB-95 production path (pre-session snapshot)

Performance under the MB-95 production path (PERF_NOTES.md, PR-PERF-05/07):

- Total: ~34.8 s after ODE LU aliasing fix.
- ODE solve: 18.5 s, LoS integration: 16.3 s.
- Bessel = 57.7 % of total (*legacy figure; see §3.3 for correction*).
- `target-cpu=x86-64-v3` made it worse (i-cache pressure on AVX2 paths).
- `mimalloc` already linked.

This snapshot is retained as a historical baseline. **All current
optimisation work targets the PSTF primary path**, not MB-95.

---

## §11. Approved upstream planning documents

Both approved by user on the decision date captured in
[`docs/IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md).

### §11.1 Rust main-line

[`docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md).

Five phases:

- Phase 0 — correctness audit (done; see §9).
- Phase 1 — FLRW truth freeze via PSTF primary.
- Phase 2 — Bianchi-ready infrastructure (callback backend done; see
  `883f22a`).
- Phase 3 — throughput tuning.
- Phase 4 — bass_py bridge.
- Phase 5 — deferred.

This ROADMAP supersedes `MASTER_PROMPT_LIST_v4.0` for solver-side direction.
PSTF primary → production; MB-95 → reference prototype.

Throughput reference: **SymBoltz approximation-free 3.1 s ~ bass_rs 10 s**
(~3× gap). **Not CAMB 0.1 s**. CAMB-class speed is off-limits because it
requires banned approximations.

### §11.2 Python side-track

[`docs/BASS_PY_FAST_TRACK_2026-04-18.md`](BASS_PY_FAST_TRACK_2026-04-18.md).

Runs in parallel. Fast-track to a preliminary figure bundle for
thesis / slides. Four tiers:

- **A** — existing HTT prototype renders.
- **B** — CAMB V-gate.
- **C** — minimal synthetic.
- **D** (optional) — direction-posterior mock.

Python track is out of scope for this document set; the interface that
connects it to the Rust main-line is `BianchiTransferFunctions(k)` JSON/CSV
+ atlas HDF5, activated at Rust Phase 4.

### §11.3 Interaction rule

When the user asks to "start implementation" or "produce plots", refer
back to these two docs for scope + success gates + killed-direction lists.
Main Rust track Phase 0 (D0.1–D0.3) is done. The side-track Tier A can
start in parallel but is not directed by this document set.

---

## §12. Cross-references and maintenance

- This ledger is referenced from
  [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) §1 (history) and
  §2.4 (constraints).
- PR-level WBS: [`docs/PR_WBS_SDD.md`](PR_WBS_SDD.md).
- Audit + doc-update protocol:
  [`docs/AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md).
- When a rule in this file is superseded, mark the old entry as
  **SUPERSEDED by §X of <doc> / commit <sha>** but do not delete — the
  history is load-bearing.

---

*End of SESSION_KNOWLEDGE_LEDGER.md.*
