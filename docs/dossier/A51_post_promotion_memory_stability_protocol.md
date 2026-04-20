# A51 · Post-promotion memory-rule stability protocol

**Appendix**: A51 (§11.14.12 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W23D5 design dossier (documentation-only;
no code landing — this appendix specifies the **positive
verification discipline** that runs on every Week-N audit AFTER
A50's promotion gate has fired, guarding the durable memory rule
against silent drift).
**Status**: **active from W25D7 onward** — the §A50.2a patient
path fired at the W25 phase audit, the §A50.4 paired landing
executed in the same rotation, and A51's first live per-phase
§6 verification now begins at **W26D7**. The W23/W24
pre-promotion dormancy caveat remains as historical context for
how the template stayed inert before promotion.
**Governance anchors**:
memory `feedback_git_workflow.md` (the durable rule store that
A50.3's bullet lands into — A51's verification target);
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 first-order rules
(the paired copy of A50.3's bullet — kept in sync with memory);
A49.3 audit-commit-time re-snapshot (the discipline A50.3
canonicalises).
**Parent references**:
[A50 Addendum protocol notice memory-promotion spec](A50_addendum_notice_memory_promotion_spec.md)
(§A50.3 memory bullet body — A51's verification subject;
§A50.5 de-promotion protocol — A51's escalation path);
[A49 audit §6 post-commit recurrence-check addendum protocol](A49_audit_post_commit_addendum_protocol.md)
(§A49.3 pre-commit re-snapshot — A51 watches it for compliance
post-promotion);
[A46 three-lane race stress-test protocol](A46_three_lane_race_stress_test.md)
(§A46.2 lane-classification — A51's regression-check compares
the lane classifier's output against the memory bullet's
expectations).

---

## A51.1 Purpose

A50 specifies the **one-time** promotion of the Addendum protocol
notice discipline into a durable memory bullet on
`feedback_git_workflow.md`. A50.5 specifies the **de-promotion**
path (three-phase observe-wait-revert triggered by an observed
false positive). Between those two endpoints, the memory bullet
has a **steady-state lifecycle** — it must be exercised, verified,
and kept in sync with the dossier citations that point to it.
Nothing in A49 or A50 specifies what the audit author does on a
post-promotion Week-N audit to confirm the memory rule is still
load-bearing.

A51 fills that gap with a three-part discipline:

* **Positive verification** (§A51.2) — the audit §6 check the
  author runs every phase to confirm the memory rule was
  consulted, the citations still resolve, and the re-snapshot
  behaviour recorded matches the bullet's rationale clause.
* **Drift detection** (§A51.3) — the two-sided check comparing
  memory `feedback_git_workflow.md`'s bullet body against
  NEXT_SESSION.md §0's paired bullet and against §A49.3 / §A49.5
  citations.
* **Maturation ledger** (§A51.4) — the phase-count counter that
  tracks how many consecutive post-promotion audits have
  observed clean verification; once the counter passes A51.5's
  threshold, the discipline may be relaxed from a per-phase §6
  check to a quarterly spot-check.

A51 is **strictly procedural**: it adds no code, no test, and no
new dossier prose beyond the per-phase §6 rows. It graduates the
§A50.3 memory bullet from "freshly promoted" to "battle-tested".

**Pre-promotion caveat (W23 F1 / W24D3)**: §A51.2's per-phase §6
row template is paste-ready for W<N>D7 audits **only after** the
§A50.2 strict gate *or* the §A50.2a patient gate fires and the
§A50.4 paired dossier + memory landing executes in the same
commit. Before either promotion path fires, A51 remains
**reference material** — the §A51.2 paste-template MUST NOT be
copied into a pre-promotion audit's §6 section, because (a)
there is no durable memory bullet for the "rationale-clause
match" sub-check to resolve against, and (b) citing "A50.3
memory rule compliance" pre-promotion would falsely imply the
gate had already fired. The pre-promotion audit body continues
to carry the §A49.5 inline Addendum-protocol-notice section
verbatim (as W23 / W24 do); the notice is rewritten to cite the
just-landed memory rule only in the same commit that executes
§A50.4.

Historical note: the caveat above was the live rule through W24.
From W25D7 onward the promotion has fired, so W26+ audits use the
§A51.2 / §A51.3 surfaces rather than the pre-promotion A49.5-only
form.

## A51.2 Positive verification — the per-phase §6 check

On every post-promotion Week-N audit, the author performs this
§6 row:

```markdown
| W<N> check #4 | **PASSED** (§A51.2 positive verification) | process (A50.3 memory rule compliance) | §A49.3 pre-commit re-snapshot was executed per the durable rule in memory `feedback_git_workflow.md` (bullet promoted W<P>D7, SHA `<sha>`); `git log T_prev..HEAD --oneline` returned <n> shas matching the §6 check #1 / #2 narratives. Memory bullet's rationale clause currently names <m> precedents (<list>); this phase's precedent <count continues | count + 1 due to addendum trigger>. | the discipline is load-bearing post-promotion and produces clean windows. | n/a — positive finding. | §A51.3 drift check also ran clean. |
```

The check is a **three-question** mechanical audit:

1. **Was §A49.3 actually re-run?** — grep the audit body for
   `git log T_prev..HEAD` or equivalent re-snapshot command
   evidence. Absent → §A49.9 trigger #3 fires (discipline
   abandonment); §A50.5 de-promotion evaluation begins.
2. **Did the snapshot match the §6 narrative?** — verify
   `git log T_prev..HEAD` returns the same sha list the audit
   body's §6 check #1 window-commit narrative names. Mismatch
   with NO addendum → §A49.6 failure mode observed; §A49.8
   candidate hook activates.
3. **Does the memory bullet's precedent list match reality?** —
   the bullet's rationale clause names the known addendum
   precedents at promotion time. After a new addendum triggers
   in a post-promotion phase, the bullet's precedent list must
   be updated to include it (A51.3 drift check catches this if
   skipped).

## A51.3 Drift detection — the three-way consistency check

A50.3's memory bullet has three cross-reference surfaces that
must stay consistent:

1. **memory `feedback_git_workflow.md`** — the durable rule
   itself (source of truth for production enforcement).
2. **`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0** — the paired
   first-order rule bullet (fresh-session bootstrapping source).
3. **`docs/dossier/A49_*.md` §A49.3 / §A49.5 citation
   paragraphs** — the "durable rule; see memory
   `feedback_git_workflow.md`" pointers added per §A50.4.

On every post-promotion audit, the author runs this three-way
diff:

```bash
# (1) Memory bullet body — extract the rule text.
sed -n '/audit-commit-time re-run/,/Rationale:/p' \
    ~/.claude/projects/<path>/memory/feedback_git_workflow.md

# (2) NEXT_SESSION §0 paired bullet — extract the same rule text.
sed -n '/audit-commit-time re-run/,/Rationale:/p' \
    docs/INDEPENDENT_TRACKS_NEXT_SESSION.md

# (3) A49.3 / A49.5 citation paragraphs — verify pointers resolve.
grep -n 'memory `feedback_git_workflow.md`' \
    docs/dossier/A49_audit_post_commit_addendum_protocol.md
```

Expected: (1) and (2) return the same paragraph body (modulo
whitespace); (3) returns ≥ 2 hits (one in §A49.3 citation
paragraph, one in §A49.5 citation paragraph).

Drift patterns and their repair paths:

* **(1) and (2) diverge** — a lane-local edit to either the
  memory file or the NEXT_SESSION §0 entry drifted the paired
  body shape. Repair: land a W<N>D<M> commit that rewrites
  whichever file diverged to match the other; both must point
  at the same rule text. This is a W<N> F<n> finding in the
  audit, severity **P2** (silent downstream confusion).
* **(3) returns < 2 hits** — the §A49.3 / §A49.5 citation
  paragraphs were edited out of A49 (perhaps during an
  unrelated refactor). Repair: restore the citation paragraphs
  per §A50.4 step (1) / (2). Severity **P2**.
* **(1) is absent** — the memory file entry was removed
  outright. §A50.5 de-promotion fires immediately (the rule
  is no longer durable); §A49.9 trigger #4 un-strikes.
  Severity **P0**.
* **All three consistent but one is outdated** (e.g. A49.3
  still has the pre-A50.4 inline rule restatement) — cosmetic
  staleness; **P3** finding; repair opportunistic.

## A51.4 Maturation ledger

Each post-promotion audit increments a phase counter iff all
three §A51.2 questions return PASSED AND §A51.3 drift check
returns clean. The counter resets to 0 on any failure.

| Phases since last failure | Verification discipline |
|---|---|
| 1–5 | Full §A51.2 + §A51.3 per-phase (dense watch). |
| 6–10 | §A51.2 per-phase; §A51.3 every other phase. |
| 11+ | §A51.2 per-phase; §A51.3 quarterly spot-check. |

The density reduces from 1-per-phase to quarterly only after the
discipline has survived 11 consecutive clean phases (~1 quarter of
weekly audits). Resetting to 0 on ANY failure (even P3 cosmetic)
is deliberate — the discipline graduates once, loses trust on
any stumble, and must re-earn the lower density.

A separate A51.5 ceiling caps the relaxation: the per-phase
§A51.2 check is **never** skipped, even at maturity. Only §A51.3
drift detection's cadence relaxes. This mirrors the W15D1 scoped-
pathspec rule's own lifecycle (adopted adversarially, never
retired — density of the per-phase §6 check-1 / check-2 stays
constant).

## A51.5 Mandatory floor

Even at the 11+ phase maturation level (§A51.4), the following
verifications remain per-phase:

1. **§A51.2 question (1)**: "Was §A49.3 actually re-run?" —
   single grep; trivial cost; catches the most severe abandonment
   mode.
2. **Memory file existence check**: `ls
   ~/.claude/projects/<path>/memory/feedback_git_workflow.md` —
   one command; catches accidental memory-store drift (e.g. file
   rename during a memory-system schema change per A49.9 trigger
   #5).
3. **NEXT_SESSION §0 existence check**: `grep -q 'audit-commit-
   time re-run' docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` — one
   command; catches the paired-rule being excised during a
   rotation.

The floor's three checks take < 5 s to run; never skip.

## A51.6 Cross-reference to A50.5 de-promotion

A51's drift detections (§A51.3) and §A51.2 question (1) failures
are inputs to A50.5's three-phase de-promotion evaluation. A51
does **not** itself trigger de-promotion — it only records the
failure in the audit §3 carry-forward table. A50.5 then runs its
own "observe-wait-revert" cycle using A51's observations as
input.

The handoff:

* **A51.3 drift**, repaired in the same audit — A51 records a
  P2/P3 finding; A50.5 does **not** fire.
* **A51.3 drift**, not repaired before the next audit — A51
  escalates to P1; A50.5 starts observing.
* **§A51.2 question (1) fail** (§A49.3 re-snapshot skipped) —
  A51 records P1; A49.9 trigger #3 fires; A50.5 evaluates
  whether the discipline has returned to "convention-only".
* **§A51.2 question (2) fail** (snapshot/narrative mismatch with
  no addendum) — A51 records P0; A49.6 failure mode fires;
  A49.8 candidate hook activates; A50.5 is independent
  (promotion stays; the §A49.8 hook becomes the new enforcement
  surface).

## A51.7 No code landing in this appendix

A51 is specification-only. The §A51.2 per-phase §6 row is prose
the audit author paste-copies into `docs/audits/
AUDIT_PHASE_IND_TRACKS_W<N>_<DATE>.md` once A50.2 or A50.2a has
fired. The §A51.3 three-way diff is three shell commands the
author runs at audit-write time. The §A51.4 maturation ledger
is one sentence in the audit §8 ledger ("A51.4 counter: <n>
consecutive clean phases since A50.2 promotion").

A future candidate code-side surface for A51 is a small
`.github/workflows/` or pre-commit check that runs the §A51.3
three-way diff automatically — deferred until either (a) the
§A51.3 drift pattern is observed once, or (b) the A49.8 hook
lands and A51.3 becomes a natural sibling to it.

## A51.8 Re-audit triggers

A51 must be rewritten if any of the following happens:

* **A50.5 de-promotion fires** — A51's maturation ledger
  resets; the discipline returns to dossier-convention; A51
  itself is marked **suspended** until a re-promotion lands.
* **Memory system format changes** (A49.9 trigger #5 candidate)
  — §A51.3's shell commands need field-path updates.
* **A49.8 candidate hook is installed** — §A51.2 question (2)
  becomes enforced pre-commit; the audit-time check becomes a
  post-hoc sanity rather than the enforcement. §A51 is
  rewritten to reflect the narrower scope.
* **§A51.3 drift observed twice in the same three-window
  span** — indicates the three-surface consistency is fragile;
  A51 is re-audited to add a single-source-of-truth proposal
  (candidate: move the rule body into the memory file and have
  NEXT_SESSION §0 auto-generate from it).

Until one of these triggers fires, A51 is stable and the
positive-verification discipline (§A51.2) remains the
authoritative per-phase §6 check for post-A50-promotion audits.

## A51.9 Relation to other appendices

* **A50 Addendum protocol notice memory-promotion spec** —
  parent. A50 specifies the one-time graduation; A51 specifies
  the per-phase steady-state verification. §A50.5 de-promotion
  is A51's escalation path.
* **A49 audit §6 post-commit recurrence-check addendum
  protocol** — A49.3 / A49.5 are A51.2's verification subjects
  (is the re-snapshot happening? is the notice template still
  inherited?). A49.9 trigger #3 / #4 fire from A51's
  observations.
* **A46 three-lane race stress-test protocol** — A46.2 lane
  classification is consumed by A49.3, which is consumed by
  A51.2. A46.2 prefix changes (A49.9 trigger #2) propagate
  through §A51.3's grep patterns.
* **A47 HJ-03 acceptance-test paste-replace protocol** —
  orthogonal. A47 is PR-time; A51 is audit-time. Different
  phase of the repo lifecycle.
* **A48 MIO → HTT dependency-wait contract** — orthogonal.
  A48 is forward-looking blocked-artefact ledger; A51 is
  backward-looking memory-rule stability.
* **memory `feedback_git_workflow.md`** — the verification
  target surface. A51.3 grep pattern (1) reads from this file;
  A51.5 floor check (2) verifies its existence. De-promotion
  per A50.5 removes the bullet from this file, at which point
  A51 suspends.
