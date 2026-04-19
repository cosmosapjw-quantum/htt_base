# BASS Rust Solver — Audit and Documentation-Update Procedure

**Purpose**: the procedural contract that every PR, and every phase-boundary
commit, must follow. This document supplements
[`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md) and
[`PR_WBS_SDD.md`](PR_WBS_SDD.md) with the how-to-run-the-audit, how-to-
update-the-docs, and what-to-do-when-they-disagree rules.

**Scope**: bass_rs Rust solver main-line (IMEX-NN), parallel infrastructure
(Phase 2.x), and bass_py bridge (Phase 4). The LB-N (Python) lane has an
analogous but separate procedure; the *commit-pattern* part of the hook
shared between both lanes is documented in §1.4.

---

## Table of contents

- §1. Phase-boundary / PR audit — self-triggered.
- §2. Documentation update — what changes after every PR.
- §3. Document-freshness audit — staleness check.
- §4. Plan-before-act rule.
- §5. Commit message conventions.
- §6. Automation infrastructure.
- §7. When procedures disagree.

---

## §1. Phase-boundary / PR audit

### §1.1 Trigger (any one)

Self-trigger if any of the following holds. **Never wait for a human to
remind you** — the user has explicitly forbidden relying on reminders
(see [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §6.1).

1. About to make a commit whose message matches any of:
   - `^IMEX-\d+:` (Rust main-line PR)
   - `^P2\.\d+:` or `^Phase 2\.\d+` (Rust parallel infrastructure)
   - `^P4\.\d+:` or `^Phase 4` (Rust bridge)
   - `^LB-\d+:` (Python LB-N lane)
   - `^FB-\d+(\.\d+)?:` or `^FB-BOOTSTRAP:`
   - `^Phase LB complete`
   - `^.*rotate NEXT_SESSION_PROMPT`
2. Work spans multiple commits and the user signals phase closure (e.g.
   "IMEX-03 complete", "이 phase 끝", "LB-5 완료").
3. About to rotate `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md` §2 to the
   next phase template.
4. A PR in [`PR_WBS_SDD.md`](PR_WBS_SDD.md) has a non-`NO` `Audit:` line
   and the work is about to be committed.

### §1.2 Procedure (do all steps without asking)

1. Load [`docs/audits/AUDIT_PROMPT.md`](audits/AUDIT_PROMPT.md) and execute
   STEPs 0–8 inline. Audit is **pre-authorised**; do not ask permission.
   The STEPs cover:
   - STEP 0 — Audit target reconstruction.
   - STEP 1 — Contract / interface audit.
   - STEP 2 — Phys-math audit.
   - STEP 3 — Equation-to-code mapping audit.
   - STEP 4 — Numerical / pipeline audit.
   - STEP 5 — Failure-mode synthesis.
   - STEP 6 — Verifier filter.
   - STEP 7 — Minimal repair plan.
   - STEP 8 — Minimal test set.
2. For each P0 or P1 finding:
   1. Produce the minimal repair plan (max 3 patches).
   2. Implement the repair.
   3. Add a regression test that would have caught the finding.
   4. Run the full relevant test suite (`cargo test --release` on the
      Rust lane; `pytest -xvs bass_py/` on the Python lane).
   5. Confirm green baseline on the **previously-green** tests.
3. For each P2 or P3 finding: log in
   `docs/audits/AUDIT_PHASE_<tag>_<YYYY-MM-DD>.md` under "P2/P3 carry-
   forward", following the format of
   [`docs/audits/AUDIT_PHASE_LB1_2026-04-18.md`](audits/AUDIT_PHASE_LB1_2026-04-18.md).
   These become next-phase prerequisites; do NOT attempt to fix in the
   current phase.
4. Commit the P0/P1 fixes as **separate** commits with the prefix
   `AUDIT(<tag>):` — e.g. `AUDIT(IMEX-03): 2×2 block sign convention`.
   The hook [`.claude/hooks/check_phase_boundary_audit.py`](../.claude/hooks/check_phase_boundary_audit.py)
   detects if a phase-boundary commit is attempted without a preceding
   `AUDIT` commit and emits a reminder via `additionalContext`. Do not
   rely on the hook — self-trigger.
5. If no P0/P1 findings exist, add a line
   **"Audit: clean (no P0/P1 findings)"** to the phase commit body so the
   audit fact is discoverable from `git log` alone.
6. Stamp [`docs/lowell_bianchi/NEXT_SESSION_PROMPT.md`](lowell_bianchi/NEXT_SESSION_PROMPT.md)
   §1 with `Last audited: <ISO date>` (Python-lane convention; mirror to
   an equivalent Rust-lane banner if introduced).
7. Only after STEPs 1–6 are done, produce the phase-closing commit
   (`IMEX-NN: …` / `LB-N: …` / `Phase LB complete …`). The audit commit
   and the phase-closing commit are **separate commits**.

### §1.3 Non-negotiables

- Do not propose framework swaps, mass refactors, or structural aesthetic
  fixes as the primary audit response.
- Do not conflate "the equation is correct" with "the code implements it"
  with "the numeric result is trustworthy" — these are three distinct
  verifications.
- A passing test whose default mode is tautological is not a passing test.
  Verify the test actually probes what its name claims (see
  [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §6.4 and
  the `friedmann_residual` incident).
- Never skip the audit because "the tests pass" or "the PR was small".
  Passing tests are not sufficient evidence — that is the entire premise
  of the audit.
- Do not extend the audit scope beyond the PR's delivered artefacts.
  The audit is bounded by the PR's `Audit:` line in
  [`PR_WBS_SDD.md`](PR_WBS_SDD.md).

### §1.4 Skip-audit criteria (allowed, must be explicit)

An audit can be skipped only if **all** of the following hold:

- The PR's `Audit:` line in [`PR_WBS_SDD.md`](PR_WBS_SDD.md) says
  `Applies: NO` with a written justification.
- The PR changes no RHS, no Jacobian, no tableau, no tolerance, no unit
  convention, no physics constant, no integrator.
- The PR adds no test that fails before the change.
- The PR does not cross a phase boundary as defined in §1.1.

If any one of the above is not met, the audit runs.

### §1.5 Why the audit is load-bearing

The first audit cycle on LB-1 caught two P1 findings that would have
silently propagated to LB-5:

- `_PLANCK18` SSOT drift (Ω sum = 1.000092, not flat).
- `friedmann_residual` default-mode tautology.

Both passed all existing tests. Without the audit, a latently-broken flat
closure would have cascaded through the integrator. The Rust lane has the
identical exposure at every IMEX-NN boundary — the audit is the only
load-bearing mechanism catching "passes for the wrong reason" bugs.

---

## §2. Documentation update — what must change after every PR

### §2.1 Mandatory doc edits on every PR

Every merged PR must include the following doc updates in the **same
commit** as the PR, or in the immediately-following `docs:` commit (never
in a separate session — losing the linkage is the failure mode):

1. **[`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md) §1 commit ledger**:
   add a new row with the PR's SHA, title, summary, evidence link. The
   row format is fixed by §1 of that file.

2. **[`PR_WBS_SDD.md`](PR_WBS_SDD.md)**: the PR's entry flips
   `Status: PLANNED` → `Status: DONE {sha}`. Add an `Evidence:` bullet
   pointing to the merge-gate test names.

3. **Conditional** — one or more of the following, depending on what the
   PR changes:
   - [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §6 —
     mark the IMEX-NN row DONE.
   - [`ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`](ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md) —
     mark P2.X / P4.X DONE.
   - [`RODAS5P_HYBRID_BACKUP_PLAN.md`](RODAS5P_HYBRID_BACKUP_PLAN.md) —
     for hybrid-branch A-NN updates.
   - [`PERF_FRESH_2026-04-18.md`](PERF_FRESH_2026-04-18.md) — if wall
     time or RSS materially changes.
   - [`ENV_VARS.md`](ENV_VARS.md) — if env toggles change.
   - [`PHYSICS_REFERENCES.md`](PHYSICS_REFERENCES.md) — if a convention
     note is discovered during audit.
   - [`CHANGELOG.md`](../CHANGELOG.md) — always, one line.

4. **If the PR introduces a new constraint or kills a direction**:
   edit [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md)
   §2 (constraints) or §8 (killed directions). Do NOT just save it to
   Claude memory — memory persistence is session-scoped; project
   knowledge lives in this document.

5. **Phase-boundary commits only (triggers per §1.1)**: also add an audit
   log entry `docs/audits/AUDIT_PHASE_<tag>_<YYYY-MM-DD>.md` even if the
   audit was clean (then the file is a single-line "Audit: clean"
   record).

### §2.2 Editing workflow

Order of operations matters because of the git-workflow rule (no
history rewrites):

1. Implement the code change. Run the tests green.
2. Run the audit per §1.
3. If audit finds P0/P1 → fix, commit as `AUDIT(<tag>):`.
4. Edit the docs per §2.1. Stage **only** the code + doc files for this
   PR. Verify with `git status --short`.
5. Commit with the explicit pathspec form
   `git commit -- <path1> <path2> ...` (never bare `git commit`, per
   [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §5.1
   rule 5).

### §2.3 Documentation "what belongs where" rubric

To prevent accidentally duplicating the same fact in two places:

| If the fact is … | It belongs in … |
|---|---|
| A commit-level event (SHA, title, what changed) | `DEVELOPMENT_PLAN_v1.md` §1 commit ledger |
| The design for an unstarted PR | `PR_WBS_SDD.md` PR entry |
| A universal rule the PR has to obey | `SESSION_KNOWLEDGE_LEDGER.md` (numbered section) |
| A numerical / physical reference (D_2 = 1002.086744 μK²) | `SESSION_KNOWLEDGE_LEDGER.md` §2 |
| A measured perf number | `PERF_FRESH_<date>.md` |
| An env-var toggle | `ENV_VARS.md` |
| An architectural charter statement | `project/04_implementation_specs/TCA_UFA_RSA_대응안` (frozen; do not edit) |
| A killed direction | `SESSION_KNOWLEDGE_LEDGER.md` §8 |
| An audit finding | `docs/audits/AUDIT_PHASE_<tag>_<date>.md` |
| A solver-choice addendum | **new** `IMEX_DECISION_<date>_addendum.md`, never edit the frozen decision |
| A bridge-schema decision | `BASS_PY_BRIDGE_SPEC.md` (P4.1+) |

If a fact would plausibly go in two places, put it in the more
specific document and add a one-line cross-reference from the other.
Duplicates get out of sync.

---

## §3. Document-freshness audit

### §3.1 Triggers

Run this at any of:

- Start of a new session (after loading
  [`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md)).
- Before starting a PR if more than 5 commits have landed since the last
  doc update on the target doc.
- As part of a phase-boundary audit if the PR touches planning docs.

### §3.2 Procedure

1. `git log --oneline -20` to see the recent commit series.
2. Compare against `DEVELOPMENT_PLAN_v1.md` §1. If the most-recent commit
   in the plan is more than **two** commits behind the most-recent commit
   in `git log`, the plan is **stale**.
3. If stale: reconstruct the missing rows from `git log --stat` and
   commit as `docs: refresh DEVELOPMENT_PLAN ledger` (not an audit
   commit; this is doc hygiene).
4. If the most-recent SHA in §1 is present in `git log` and the commit
   message matches the §1 row, plan is fresh — no action needed.

### §3.3 Automation surface

A check-script (to be written as `scripts/check_docs_fresh.py`) can
mechanise step 2. It returns a non-zero exit code if staleness is
detected. Suggested additions when the script lands:

- CI hook running on every push.
- A PreToolUse hook paralleling
  [`.claude/hooks/check_phase_boundary_audit.py`](../.claude/hooks/check_phase_boundary_audit.py),
  reminding the session to refresh before a new commit if staleness >2.

The script is not a blocker for the docs to be useful today; staleness
is caught manually until the script lands.

---

## §4. Plan-before-act rule

If work is proposed that does not fit any entry in
[`PR_WBS_SDD.md`](PR_WBS_SDD.md):

1. **Stop**. Do not start implementation.
2. Write the SDD entry first, slotted at the right place in
   [`PR_WBS_SDD.md`](PR_WBS_SDD.md) (new PR-id if needed).
3. Add a dependency-graph entry in
   [`DEVELOPMENT_PLAN_v1.md`](DEVELOPMENT_PLAN_v1.md) §3.
4. Commit the new SDD entry as `docs: plan <new PR-id>` **before** any
   code change lands.
5. Only then start implementation.

Rationale: the user's explicit workflow preference is "plan → implement
→ commit with docs", never "implement → retrofit plan → commit" (the
latter loses the decision record and leads to the same class of drift
that §3 exists to catch).

---

## §5. Commit-message conventions

### §5.1 Required prefixes

- `IMEX-NN:` — Rust main-line PR.
- `P2.N:` — Rust parallel-infrastructure PR (Phase 2.X).
- `P4.N:` — Rust bridge PR (Phase 4).
- `A-NN:` or `Hybrid-ANN:` — RODAS5P hybrid backup branch PR.
- `LB-N:` — Python LB-N lane phase commit.
- `FB-N(.M)?:` — Python FB phase commit.
- `AUDIT(<tag>):` — P0/P1 repair commit from an audit cycle.
  `<tag>` is the phase tag being audited (e.g. `IMEX-03`, `LB2`, `W22 R1`).
- `docs:` — documentation-only commit.
- `chore:` — non-load-bearing maintenance.

### §5.2 Body requirements

Every commit body should include, in order:

1. One-sentence summary (what changed).
2. One-sentence rationale (why).
3. Test evidence (test names + result: `test_foo PASS`, etc.).
4. Audit line: one of
   - `Audit: self-triggered, clean (no P0/P1)` — normal case.
   - `Audit: self-triggered, findings in AUDIT(<tag>) <sha>` — if
     prior audit commit exists.
   - `Audit: skipped per AUDIT_AND_UPDATE_PROCEDURE §1.4 — <reason>` —
     skip case.
5. `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
   trailer (per user workflow preference in
   [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §5.1
   rule 8).

### §5.3 Staging rules (binding)

From [`SESSION_KNOWLEDGE_LEDGER.md`](SESSION_KNOWLEDGE_LEDGER.md) §5.1.
Reproduced here so the audit procedure is self-contained:

- Never `git add .` / `git add -u` / wildcard.
- Always `git status --short` before commit. If unexpected staged items
  appear, flag to user but default to keep-as-is unless they say
  otherwise.
- Always `git commit -- <path1> <path2> ...` with explicit pathspec.
- Never `git reset --soft` / `git rebase` / branch cleanup unless user
  explicitly asks.
- Never `git commit --amend` to fix a problem — create a new forward
  commit.

---

## §6. Automation infrastructure

### §6.1 Hook — `check_phase_boundary_audit.py`

File: [`.claude/hooks/check_phase_boundary_audit.py`](../.claude/hooks/check_phase_boundary_audit.py).

- Scope: `PreToolUse` hook on the `Bash` tool.
- Fires when the Bash command matches a phase-boundary commit pattern
  (the list in §1.1 condition 1).
- Checks the last 5 commits for an `AUDIT(` prefix.
- If a phase-boundary commit is about to fire without a preceding audit
  commit, emits `additionalContext` reminding the session to execute
  the audit + (for LB-N lane) the physics-gallery refresh.
- **Advisory**, not blocking. The load-bearing mechanism remains the
  self-trigger rule in §1.
- Install via `.claude/settings.json` `hooks.PreToolUse` (when the user
  enables it; the memory rule holds regardless).

### §6.2 Hook — regex extension policy

If new commit prefixes are introduced (e.g. a new `IMEX-` style), the
hook's `PHASE_COMMIT_PATTERNS` list must be updated in the same commit
that introduces the prefix. Rationale: otherwise the hook silently
stops reminding for the new class of commits. The rule that catches
regex-co-edit failures in general is §A49.9 of
[`docs/audits/AUDIT_PHASE_IND_TRACKS_W22_2026-04-19.md`](audits/AUDIT_PHASE_IND_TRACKS_W22_2026-04-19.md).

### §6.3 Planned hook — `check_pr_sdd_exists.py`

**Not yet implemented.** Proposed scope:

- Fires on every `git commit` whose subject matches the PR-ladder
  prefixes (`IMEX-\d+:`, `P2\.\d+:`, etc.).
- Parses [`PR_WBS_SDD.md`](PR_WBS_SDD.md) to verify the PR id has a
  `Status: IN PROGRESS` or `Status: PLANNED` entry.
- If missing, emits `additionalContext` per §4's plan-before-act rule.
- Implementation slot: `.claude/hooks/check_pr_sdd_exists.py`.

### §6.4 Planned hook — `check_docs_fresh.py`

**Not yet implemented.** Proposed scope:

- Fires on `SessionStart` or at `PreToolUse` for the first commit of a
  session.
- Runs the staleness check from §3.2.
- If stale > 2 commits, emits a reminder.

### §6.5 Manual invocation

The audit prompt can be run manually at any time via
`cat docs/audits/AUDIT_PROMPT.md` and following the STEP list. The
self-trigger rule makes manual invocation unnecessary at phase boundaries
but useful for spot-checking.

---

## §7. When procedures disagree

### §7.1 Document vs code

Code wins for *runtime behaviour*, documents win for *intent*. If you
observe:

- Test assertion does not match the documented `Merge gate` in
  `PR_WBS_SDD.md` → fix the test or the doc, depending on which expresses
  the original design intent. Document the fix.
- Env-var read in code does not match [`ENV_VARS.md`](ENV_VARS.md) →
  refresh `ENV_VARS.md`. The source of truth for env vars is the code.
- A PR completed differently from its SDD → edit the SDD entry to
  reflect the landed design, with a one-line "Changed from PLANNED scope
  because <reason>" note in the PR commit body.

### §7.2 Memory vs document

Always trust the document. Memory is session-scoped; it can be stale or
missing. If memory says X and the repo says not-X, the repo wins.
Update or delete the memory entry in the same session.

### §7.3 Audit finding vs existing test

If the audit finds a latent bug that an existing test claimed to cover:

- The test is tautological or broken.
- Fix the test **and** the bug in the `AUDIT(<tag>):` commit.
- Add a new regression test that would have caught the finding.
- Note in the audit log which test was tautological.

---

## §8. Checklist card (printable summary)

At every PR:

- [ ] Implement code. Run `cargo test --release`. Green.
- [ ] Self-trigger audit per §1.
- [ ] P0/P1 → `AUDIT(<tag>):` commit. P2/P3 → log file.
- [ ] Edit `DEVELOPMENT_PLAN_v1.md` §1 (add row).
- [ ] Edit `PR_WBS_SDD.md` (flip Status → DONE, add Evidence).
- [ ] Edit conditionals per §2.1.3 (IMEX_DECISION §6 / ROADMAP / PERF /
      ENV / PHYSICS_REFERENCES / CHANGELOG).
- [ ] If new constraint or killed direction →
      `SESSION_KNOWLEDGE_LEDGER.md`.
- [ ] `git status --short` — verify staged set.
- [ ] `git commit -- <explicit paths>` with the message format from §5.
- [ ] Verify commit body has `Audit:` line.

---

*End of AUDIT_AND_UPDATE_PROCEDURE.md.*
