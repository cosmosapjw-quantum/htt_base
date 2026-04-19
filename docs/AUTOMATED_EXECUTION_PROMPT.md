# BASS Rust Solver — Automated Execution Prompt

**Purpose**: a single self-contained prompt that drives the IMEX-02 → IMEX-09
+ Phase 2.X + Phase 4 + hybrid-backup ladder end-to-end with
(a) pre-transplanted skeleton scaffolding, (b) per-phase triple verification,
(c) hallucination-prevention protocol, (d) local-minima avoidance, and
(e) automated doc-update + commit.

Use this prompt by pasting its body (§§A–G) at the start of a new session, or
by reference:

> "Execute the bass_rs development ladder per
> `docs/AUTOMATED_EXECUTION_PROMPT.md`. Begin with §B (skeleton pass); then
> iterate §C on the next `Status: PLANNED` entry in `docs/PR_WBS_SDD.md`."

This document is the **operator**. The four planning docs remain the
**sources of truth**:
[`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md),
[`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md),
[`PR_WBS_SDD.md`](PR_WBS_SDD.md),
[`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md).

---

## §A. Project context (frozen preamble — pin at top of working memory)

### A.1 Identity

- Repo: `bass_rs` — Bianchi / approximation-free Einstein–Boltzmann CMB
  solver in Rust. Cwd on this machine:
  `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
- User: Jiwon, Soongsil OMEG PhD researcher; domain-expert in PSTF / MB-95 /
  Bianchi / Rodas5P. See
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §1.
- Parallel lanes in the same repo: Rust main-line (this doc),
  `bass_py/` Python side-track, `docs/lowell_bianchi/` LB-N lane. Do NOT
  re-organise the repo.

### A.2 Non-negotiable invariants (abort the task rather than violate)

From [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §2, §5, §6:

1. **Approximation-free truth engine**. BANNED as defaults:
   TCA pre-phase IC generator, standard FLRW UFA, photon RSA, any
   FLRW-specific closure copied into Bianchi paths.
2. **Bit-identical D_2 regression anchor**:
   `D_2 = 1002.086744 μK²`. Never broken for speed. 14-consecutive-commit
   history carried forward.
3. **(m)-major ordering** for Bianchi. Species-first layout is forbidden.
4. **Edit `src/solver/pstf_primary/`**, never `src/pstf_primary/`.
5. **Git workflow**: additive-only forward commits;
   **always** `git commit -- <path1> <path2> ...` explicit pathspec;
   **never** `git reset --soft` / `git rebase` / `git add .` / wildcards /
   `--amend`; `project/` is local-only (`.gitignore:126` intentional).
6. **Self-triggered audit** at every phase boundary. Never wait for a
   reminder. Follow
   [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) §1.

### A.3 Read-order before any work

Load these four files into working memory, in order:

1. [`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md) — commit ledger +
   upcoming PR index + template.
2. [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) — all
   user-provided constraints, measurements, killed directions.
3. [`PR_WBS_SDD.md`](PR_WBS_SDD.md) — per-PR SDD for everything unstarted.
4. [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) —
   the procedural contract.

Then load these reference docs on demand:

- [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) — solver
  choice rationale.
- [`ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md) —
  phase-structured roadmap.
- [`PHASE0_D0_AUDIT_REPORT.md`](PHASE0_D0_AUDIT_REPORT.md) — Phase 0 bugs.
- [`PERF_FRESH_2026-04-18.md`](PERF_FRESH_2026-04-18.md) — measurements.
- [`../project/04_implementation_specs/TCA_UFA_RSA_대응안`](../project/04_implementation_specs/TCA_UFA_RSA_대응안) —
  architectural charter (frozen).
- [`../project/04_implementation_specs/solver_strategy_5566dof_v2.md`](../project/04_implementation_specs/solver_strategy_5566dof_v2.md) —
  IMEX cost model.

### A.4 State of the ladder (as of this doc's creation)

Done: IMEX-00, IMEX-01, Phase 2.0 (callback backend), Phase 2.2 (analytical
Jacobian at FLRW m = 0), Phase 0 audit.

Next up on critical path: **IMEX-02**.

Parallel-eligible (no critical-path dep): P2.1, P2.3, P2.4, P2.5.

---

## §B. Skeleton scaffolding pass (run ONCE at the start of this ladder)

Before any PR's real implementation, pre-transplant empty-but-compiling
skeletons for every unstarted PR. This front-loads the design under the
template and exposes integration misfits early.

### B.1 What to create per PR

For every PR with `Status: PLANNED` in
[`PR_WBS_SDD.md`](PR_WBS_SDD.md):

1. Create the new source files listed under the PR's **Outputs** section,
   as **empty shells** with:
   - `//!`-level crate docstring naming the PR tag, referencing the SDD
     entry and the relevant equation / reference (e.g. *"IMEX-02 operator
     split, Kennedy–Carpenter 2003 eq (2.1), PR_WBS_SDD §IMEX-02"*).
   - Type signatures for every function named in the SDD (parameters +
     return types), with `todo!("IMEX-02: ...")` bodies. The skeleton
     must **compile** but panic on call.
   - A scratch `// CONTRACT:` comment block per function listing what
     the function must produce and what it must **not** do (inlined from
     the SDD).
   - A scratch `// LITERATURE:` comment block per function naming the
     expected reference (paper or repo file + equation / line number)
     that the eventual implementation must cite in its doc comment.
2. Create the new test functions listed under the PR's **Merge gate**
   section, `#[ignore]`-gated with a `todo!()`-returning body. These are
   tombstones so `cargo test -- --ignored --list` shows every future
   merge-gate test by name.
3. Register new modules in the parent `mod.rs` behind a
   `#[cfg(feature = "skeleton_<pr-id>")]` guard if the new module would
   otherwise break the public API.
4. For new env toggles, add the variable name + `// skeleton` note to
   [`ENV_VARS.md`](ENV_VARS.md) under a dedicated "skeleton (not yet
   live)" section. This prevents a second PR from colliding on the name.

### B.2 Skeleton commit

Commit skeleton as **one** additive commit with subject
`chore: skeleton scaffold for PR <id1>..<idN>`. Use the explicit pathspec
form. Include in the body:

- A table listing every PR id whose skeleton landed.
- The `cargo build --release` result (must succeed).
- `Audit: skipped per AUDIT_AND_UPDATE_PROCEDURE §1.4 — skeleton-only,
  no RHS/Jacobian/tableau/tolerance change`.

After the skeleton commit, the ladder entries stay `Status: PLANNED` in
the SDD — skeleton is **not** a PR advancement. Only filling in the
contract qualifies.

### B.3 Skeleton sanity cross-checks (run after the skeleton commit)

1. `cargo build --release` — must succeed.
2. `cargo test --release --no-run` — all targets compile.
3. `cargo test --release -- --ignored --list | wc -l` — the count equals
   the sum of every new `#[ignore]` test across every skeleton entry.

If any cross-check fails, fix in the same commit (re-stage, new forward
commit — never `--amend` per §A.2.5).

---

## §C. Per-PR execution protocol (the main loop)

For each PR in dependency order (IMEX critical path first, then
parallel-eligible, then integration):

### C.1 Select the target PR

Pick the topmost entry in [`PR_WBS_SDD.md`](PR_WBS_SDD.md) whose
`Status: PLANNED` **and** whose `Depends on:` list is all `DONE`. If
none qualify, abort with a written note in
`docs/audits/BLOCKER_<date>.md`.

### C.2 Step 1 — Literature anchoring (mandatory ≥ 2 internal + ≥ 1 external)

Load the PR's literature anchors per the table in §D of this document.
Each anchor is a file path + line range (for internal) or a paper + URL
(for external). Pin the specific equation / lemma / code pattern the PR
relies on.

**Rule**: **do not start implementing until every anchor has been
explicitly loaded** via `Read` (internal) or `WebFetch` (external) in
the same turn as the citation. Never cite from training-data memory.

### C.3 Step 2 — Triple verification pass

Three independent verifications, each written as a separate paragraph in
`docs/audits/VERIFICATION_<PR-id>_<YYYY-MM-DD>.md`:

#### C.3.1 Pass A — Internal literature cross-check

Produce a section **A: Internal lit cross-check** containing:

1. For each internal anchor: quote the exact code / doc line ± 3 lines of
   context, with `file:line`.
2. For each cited equation number or symbol, search the repo
   (`Grep "eq (3.10)" src/`) and list every prior use. If the current PR
   uses a different sign or index convention from a prior use, flag it.
3. Report the set of symbols / constants the PR introduces vs. the set
   already present. Any collision on symbol name means a rename, not a
   shadow.

#### C.3.2 Pass B — Web-fetch verification

Produce a section **B: Web-fetch verification** containing:

1. For each external paper / library / crate citation, run `WebFetch`
   on the canonical URL (arXiv abstract page, crate docs.rs,
   library-guide PDF). Do **not** rely on memory.
2. Quote the equation or API line verbatim, with the URL and
   `retrieved: YYYY-MM-DD`.
3. If the external source contradicts an internal anchor, stop and
   record both positions; pick one with written rationale and a sign
   test that would decide (see §E red-team step).

#### C.3.3 Pass C — Self-CoT

Produce a section **C: Self-CoT** containing, in order:

1. **Contract** (3–5 bullet points): what must this PR's code produce?
   What inputs? What outputs? What invariants must it preserve?
2. **Failure modes** (3–5 bullet points): what could go wrong silently
   (tautological test, wrong sign convention, index off-by-one, wrong
   unit, floating-point non-associativity)?
3. **Alternatives** (minimum 3): independent approaches that could
   satisfy the contract, with a one-line pro and one-line con each.
4. **Chosen approach + red-team counter-argument** (3 sentences
   each-way): why the pick is best; the strongest steelman against it.
5. **Falsification**: a **concrete** measurement, test, or output value
   that would decisively prove the chosen approach wrong (e.g. "if
   `D_2 σ=0` drifts from the IMEX-07 anchor by > 1 ulp after this PR,
   the split is broken and must revert").

**Commit the verification doc** as a separate commit:
`docs: verification log for <PR-id>` with explicit pathspec. This
anchors the reasoning in the repo history before implementation starts
— if the PR later needs rollback, the recorded reasoning survives.

### C.4 Step 3 — Implementation (skeleton → real)

Fill in the skeleton from §B for this PR. Rules:

- Every function body replaces its `todo!()` with real code.
- Every `// CONTRACT:` comment stays in place (or is tightened); do not
  delete.
- Every `// LITERATURE:` comment is replaced by a permanent
  `/// Reference: <paper> eq (X); see also <file:line>` doc comment.
- Skeleton tests drop their `#[ignore]` and get real assertions per the
  SDD's merge gate.
- Bit-identicity guards (`D_2` anchor + any layout-specific anchor from
  the PR's Merge gate) run locally after every meaningful patch.

### C.5 Step 4 — Audit

Execute [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md)
§1.2 in full. P0/P1 findings commit as `AUDIT(<PR-id>): ...` before
the phase commit. P2/P3 findings log in
`docs/audits/AUDIT_PHASE_<PR-id>_<YYYY-MM-DD>.md`.

### C.6 Step 5 — Doc fanout

Apply every doc update from
[`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md) §2.1:

- [`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md) §1 new row.
- [`PR_WBS_SDD.md`](PR_WBS_SDD.md) → `Status: DONE <sha>` + Evidence.
- Conditional docs per the PR's `Doc updates:` line.
- If a new constraint / killed direction emerged, edit
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md)
  §2 / §8 — do NOT park in Claude memory.

### C.7 Step 6 — Commit

Subject per [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md)
§5. Body per §5.2 (summary, rationale, test evidence, `Audit:` line,
`Co-Authored-By:` trailer). Commit via explicit pathspec:

```
git commit -m "$(cat <<'EOF'
<PR-id>: <short title>

<summary>

<rationale>

Test evidence: <test_name_1> PASS, <test_name_2> PASS, ...
D_2 regression: <bit-identical | within 1e-6 rel>

Audit: self-triggered, clean   OR
Audit: self-triggered, findings in AUDIT(<PR-id>) <sha>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" -- <explicit path 1> <explicit path 2> ...
```

Run `git status --short` immediately before the commit and verify the
staged set matches the PR's scope.

### C.8 Step 7 — Confirm + loop

Read `git log -1 --stat`. Confirm the commit and its scope. If green,
return to §C.1 with the next PR. If the merge-gate tests regressed,
triage per §E stuck-threshold rule.

---

## §D. Per-PR literature-anchor table

**Rule**: every anchor must be loaded via `Read` (internal) or `WebFetch`
(external) in the same turn as the PR opens. Do NOT skip. If a citation
cannot be resolved, mark it `UNRESOLVED` in the verification doc and
either (a) find a substitute anchor or (b) escalate to the user.

| PR | Internal anchors (repo paths) | External anchors (papers / crates) |
|---|---|---|
| **IMEX-02** Op-split identity | `src/solver/pstf_primary/rhs.rs`, `src/solver/pstf_primary/jacobian.rs` (post-c5ae4f9), `src/solver/pstf_primary/matrix.rs:build_pstf_matrix_analytical_into`, `project/04_implementation_specs/TCA_UFA_RSA_대응안` §operator split | Kennedy & Carpenter 2003 *Appl. Numer. Math.* §2 additive RK definition; Challinor & Lasenby 2000 arXiv:astro-ph/9903283 eq (3.10)–(3.22) collision term; Ma & Bertschinger 1995 arXiv:astro-ph/9506072 eq (65) Thomson term |
| **IMEX-03** Single-k IMEX | `src/solver/imex_ark4.rs` (tableau); `src/solver/rodas5p.rs` (reference stepper); `src/solver/pstf_primary/integrate.rs` | Kennedy & Carpenter 2003 tableau table; Dimarco & Pareschi 2012 *SINUM* §3 Boltzmann IMEX; Hairer–Wanner *ODE-II* §IV.8 PI controller; SymBoltz.jl source (split step); SUNDIALS ARKODE user guide §3.1.4 |
| **IMEX-04** Multi-k end-to-end | `src/solver/flrw_cl_pipeline.rs`; `src/solver/pstf_primary/imex_driver.rs` (from IMEX-03); `docs/ENV_VARS.md` | ABCMB paper (m-independent collision); SymBoltz.jl multi-k dispatch pattern |
| **IMEX-05** Callback default | `src/solver/rodas5p.rs:LinearProfileSampler` (Phase 2.0); `883f22a` commit message | ARKODE user-supplied `fe`/`fi` pattern (§3.1.3); `dhat` crate docs (memory measurement) |
| **IMEX-06** Polarisation | `bass_py/bass/collision/thomson_*` (Python reference); `src/source/registry.rs` (source SSOT); W7-02 bass_py test | Challinor 2000 §3 E/B decomposition eq (3.18); Kamionkowski et al. 1997 arXiv:astro-ph/9611125 polarisation basis; CAMB `polarization.f90` (as sign-convention oracle) |
| **IMEX-07** Production scale-up | `data/camb_reference/` (confirm provenance); `docs/PERF_FRESH_2026-04-18.md` | Planck 2018 VI cosmological parameters (Aghanim et al. 2018 arXiv:1807.06209); CAMB git SHA of the reference run; CLASS explanatory.ini for target cosmology |
| **IMEX-08** Bianchi I m-major | `src/solver/pstf_primary/layout.rs`; `src/solver/pstf_primary/jacobian.rs` (m=0 CG done); `bass_py` Route B sentinel test | Pereira, Pitrou & Uzan 2007 arXiv:0706.2383 perturbation theory in Bianchi; Pontzen & Challinor 2007 arXiv:0706.2075 / 2011 arXiv:1009.3935 Bianchi CMB; Maartens, Ellis & Stoeger 1996 arXiv:astro-ph/9506086 kinematic bounds |
| **IMEX-09** Massive-ν | `src/solver/pstf_primary/neutrinos.rs` (TBD); existing ncdm code if any | Lesgourgues & Tram 2011 *JCAP* 09, 032 arXiv:1104.2935 ncdm; CLASS source `ncdm.c` |
| **P2.1** m-major layout | `src/solver/pstf_primary/layout.rs`; `SESSION_KNOWLEDGE_LEDGER.md` §2.2 (m-major mandate) | Pereira–Pitrou–Uzan 2007 §III state ordering; Challinor 2000 §5 Bianchi extension |
| **P2.3** Sparse Jacobian | `src/core/lu.rs`; `src/solver/rodas5p.rs`; `Cargo.toml` | faer-sparse docs docs.rs/faer-sparse; nalgebra-sparse comparison; `sprs` crate (fallback) |
| **P2.4** Adaptive ℓ_max + sponge | `project/04_implementation_specs/TCA_UFA_RSA_대응안` §high-ℓ tail | Pitrou 2008 arXiv:0806.0673 absorbing boundary; Shaw & Lewis 2010 arXiv:0911.2714 truncation strategy |
| **P2.5** Matrix LoS | `src/los/` (scalar); Challinor 2000 §4 | Seljak & Zaldarriaga 1996 arXiv:astro-ph/9603033 scalar LoS baseline; Challinor 2000 §4 matrix kernel |
| **P4.1** Transfer JSON/CSV | `bass_py/` consumer surface; `docs/BASS_PY_BRIDGE_SPEC.md` (author in this PR) | `serde_json` docs; `csv` crate docs |
| **P4.2** Atlas HDF5 | `docs/BASS_PY_BRIDGE_SPEC.md` (P4.1) | `hdf5-metno` crate docs (prefer over original `hdf5`); HDF5 library user guide |
| **P4.3** Route B guard | `bass_py` Route B fixture | None (regression maintenance) |
| **A5** Hybrid full-state | `docs/RODAS5P_HYBRID_BACKUP_PLAN.md` §A5; post-IMEX-05 callback surface | Hairer–Wanner *ODE-II* §IV.7 Rosenbrock; `diffsol` 0.10 docs |
| **A8** Hybrid scale-up | `docs/RODAS5P_HYBRID_BACKUP_PLAN.md` §A8; IMEX-07 results | A/B benchmark methodology — `hyperfine` docs |

---

## §E. Hallucination-prevention protocol

### E.1 Citation discipline

- **Rule 1** (load-before-cite): every paper / equation / API reference must
  be loaded via `Read` (internal) or `WebFetch` (external) **in the same
  turn** that it is cited. A citation without a load is treated as
  hallucination and must be removed.
- **Rule 2** (fact vs inference): in verification docs and commit bodies,
  **separate** statements of fact (cite-backed) from inference (author's
  reasoning). Use explicit markers:
  - `FACT [ref: Challinor 2000 eq (3.18)]` — verifiable claim.
  - `INFERENCE [author]` — analytic step, not in the cited source.
- **Rule 3** (convention disclosure): every sign / index / unit
  convention used must be named (`CAMB convention` / `MB-95 convention`
  / `Challinor 2000 convention`) and matched against the repo's
  existing convention before any bit-identicity claim.
- **Rule 4** (crate existence): any external Rust crate cited for
  adoption must be checked via `cargo search <name>` or
  `WebFetch https://crates.io/crates/<name>` for existence + last
  publication date + license before appearing in `Cargo.toml`.
- **Rule 5** (API existence): any external API pattern cited must be
  matched to a concrete line in the current version of the library's
  source or user guide, not a remembered API. Library APIs drift —
  memory is stale by default.

### E.2 Two-candidate fallback (sign / convention ambiguity)

If a sign or convention is ambiguous after Pass A + Pass B:

1. Implement both candidates behind a feature flag or a constant.
2. Run the regression anchor (`D_2`) under both.
3. The candidate that is **not** bit-identical to the anchor is wrong —
   the one that matches is right (and the sign convention just got
   empirically pinned).
4. Document the empirical pinning in the PR verification doc as
   `FACT [empirical: D_2 bit-identical under candidate <A or B>]`.

### E.3 Contradiction-logging rule

If two sources disagree:

1. Do NOT silently pick one.
2. In the verification doc, quote both, cite both, and write the
   rationale for the pick.
3. Mark the pick as a hypothesis: `HYPOTHESIS [pending empirical test]`.
4. Add an explicit falsification test in the PR's merge gate that would
   flip the choice.

### E.4 Tautology guard

From [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §6.4:
"A passing test whose default mode is tautological is not a passing
test." For every new test, explicitly answer in the verification doc:

- What independent state does this test drive the code into?
- What computation is the test assertion **not** re-doing the code's
  computation to verify?
- Would the test fail if the function body were replaced with
  `return ().default()`? (If no — it is tautological.)

---

## §F. Local-minima avoidance

### F.1 Divergence-first rule

Before implementation, `Self-CoT §C.3.3 Alternatives` demands
**≥ 3 independent approaches**. Examples of good diversity:

- Different decomposition (e.g. operator split along ℓ vs along species).
- Different linear-algebra backend (dense vs sparse vs block-diagonal).
- Different control-flow (single-tableau IMEX vs partitioned hybrid vs
  exponential integrator).
- Different language feature (trait dispatch vs `enum`-match vs
  function pointer).

If you can only think of 2, pause and list every dimension along which
the design could vary — then pick an unexplored dimension for the 3rd.

### F.2 Red-team step

After picking an approach, write the strongest case **against** it in
**exactly** 3 sentences. Include at least one concrete scenario where
the approach would break (an input pattern, a regime boundary, a
numerical limit).

### F.3 Falsification step

State, in one sentence, the **specific** measurement or test whose
outcome would decisively force a reversal. Examples:

- "If `D_2` at `σ² = 0` drifts from the IMEX-07 anchor by > 1 ulp after
  this PR, the Bianchi split is broken and must revert."
- "If the wall time under `BASS_IMEX=1` exceeds 3× the Rodas5P baseline
  at `fast_validation`, IMEX-03's 2×2 block solve is too slow and must
  be replaced."

### F.4 Stuck threshold

If the same merge-gate test fails **3 times** with different fix
attempts:

1. **Stop coding.**
2. Write `docs/audits/BLOCKER_<PR-id>_<YYYY-MM-DD>.md` capturing: the
   test, the three failed attempts, the observed vs expected output,
   and the current best hypothesis for the root cause.
3. Switch to a parallel-eligible PR from the ladder (not on the
   critical path).
4. Return to the blocked PR only with new evidence (a fresh web-fetch,
   a user input, a cross-crate sanity result).

### F.5 Scope-creep guard

During implementation, if a "while I'm here" refactor temptation
appears:

1. Stop.
2. Check the PR's SDD entry in [`PR_WBS_SDD.md`](PR_WBS_SDD.md).
3. If the refactor is not in the WBS, either defer it to a new PR entry
   (new `docs: plan <PR-id>` commit per §4 of
   [`AUDIT_AND_UPDATE_PROCEDURE.md`](AUDIT_AND_UPDATE_PROCEDURE.md)), or
   drop it.

From
[`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §8.2:
the Phase 1.1 fused-matvec PR was reverted because a local
optimisation reasoning turned out to be inapplicable at cache-level.
Always re-test at the cache level when the intuition is
memory-traffic reduction.

### F.6 Sanity re-read

Immediately before the commit:

1. Re-open the PR's SDD entry.
2. For every WBS item, mentally check: is it addressed? Where?
3. For every Merge gate line, mentally check: is the test present and
   passing?
4. For every Doc updates line, mentally check: is the edit in the
   staged set?

If any answer is "no", fix before committing.

---

## §G. Per-PR checklist card (paste into every PR commit body or scratch)

- [ ] Dependencies all `Status: DONE` per PR_WBS_SDD (§C.1).
- [ ] Internal anchors loaded via Read (§C.2 + §D).
- [ ] External anchors loaded via WebFetch (§C.2 + §D).
- [ ] VERIFICATION_<PR>_<date>.md created, three sections (A/B/C) (§C.3).
- [ ] Verification doc committed as separate `docs: verification log
      for <PR-id>` commit (§C.3.3).
- [ ] 3 alternatives listed; red-team + falsification written (§F.1–F.3).
- [ ] Skeleton → real implementation filled; `// CONTRACT:` retained,
      `// LITERATURE:` replaced by `///`-doc citation (§C.4).
- [ ] PR's Merge-gate tests pass (listed by name in commit body).
- [ ] `D_2 = 1002.086744 μK²` bit-identical (if PR touches production
      default path).
- [ ] Any previously-green test remains green.
- [ ] Audit self-triggered per §1 of AUDIT_AND_UPDATE_PROCEDURE;
      P0/P1 in `AUDIT(<PR-id>)` commit; P2/P3 in
      `AUDIT_PHASE_<PR-id>_<date>.md`.
- [ ] `DEVELOPMENT_PLAN_v1.md` §1 row added.
- [ ] `PR_WBS_SDD.md` Status → `DONE <sha>`; Evidence bullet added.
- [ ] Conditional docs updated per the PR's `Doc updates:` line.
- [ ] If new constraint / killed direction:
      `SESSION_KNOWLEDGE_LEDGER.md` updated (not just Claude memory).
- [ ] `git status --short` checked before commit; only expected files
      staged.
- [ ] `git commit -m "..." -- <explicit paths>` used (not bare
      `git commit`).
- [ ] Commit body contains `Audit:` line, test evidence, and
      `Co-Authored-By:` trailer.
- [ ] `git log -1 --stat` confirms scope matches §C.8.

---

## §H. Operator entry points

A minimal invocation to run the whole ladder from a fresh session:

```
Execute docs/AUTOMATED_EXECUTION_PROMPT.md.

1. Load §A context; confirm cwd = /home/cosmosapjw/Dropbox/bianchi/htt_base.
2. Read the four planning docs per §A.3.
3. Run §B skeleton pass for every Status: PLANNED PR. Commit as
   `chore: skeleton scaffold for PR <ids>`.
4. For each PR in dependency order per §C.1:
   - Execute §C.2 — §C.7 end-to-end.
   - After the commit, return to step 4 until no PLANNED entry remains
     with satisfied dependencies.
5. When no PR is eligible, write a session summary in
   `docs/audits/SESSION_SUMMARY_<date>.md` and stop.
```

To run a single PR only (e.g. to review its implementation):

```
Execute §C of docs/AUTOMATED_EXECUTION_PROMPT.md for PR <PR-id>. Skip
§B (skeleton already present). Stop after §C.8 confirm.
```

To only produce the verification doc without implementing:

```
Execute §C.2 and §C.3 of docs/AUTOMATED_EXECUTION_PROMPT.md for PR
<PR-id>. Commit the verification doc. Stop before §C.4.
```

---

## §I. What this prompt is NOT

- It is **not** a decision-maker. If a design choice is ambiguous after
  the triple-verification, **ask the user** rather than guessing.
- It is **not** a license to skip `AUDIT_AND_UPDATE_PROCEDURE` — every
  procedural rule there is load-bearing.
- It is **not** frozen. If a step in the procedure turns out to cost
  more than it protects, propose an edit to this file as its own PR
  (prefix `docs:`) with rationale and user approval.

---

*End of AUTOMATED_EXECUTION_PROMPT.md.*
