# A50 · Addendum protocol notice memory-promotion spec

**Appendix**: A50 (§11.14.11 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W22D5 design dossier (documentation-only;
no code landing — this appendix specifies the **promotion
workflow** that lifts the A49.5 "Addendum protocol notice"
discipline from audit-body convention into durable memory-rule
status).
**Status**: **gate-specified, trigger-pending** — the promotion
gate is "notice carried forward in ≥ 3 consecutive audit bodies
without drift" (§A50.2). As of 2026-04-19 (W21 audit), the count
is **2** (W20 first occurrence + W21 first carry-over / dogfooding).
W22's audit is the earliest possible promotion trigger; W23 or W24
is the expected real trigger if the discipline holds through W22.
**Governance anchors**:
memory `feedback_git_workflow.md` (durable first-order rules —
additive-commits, pre-commit `git status --short` gate, scoped
`git commit -- <paths>`); A50.3 specifies the exact body shape of
the new memory bullet this appendix promotes;
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 first-order rules
(the bullet list that memory entries are copy-pasted into; A50.4
specifies the paired §0 edit).
**Parent references**:
[A49 audit §6 post-commit recurrence-check addendum protocol](A49_audit_post_commit_addendum_protocol.md)
(the discipline being promoted — §A49.3 audit-commit-time check +
§A49.5 in-body notice template);
[A49.9 re-audit trigger #4](A49_audit_post_commit_addendum_protocol.md)
("Memory `feedback_git_workflow.md` adds an 'audit-commit-time
status-gate' entry… §A49.3 / §A49.5 are updated to cite the memory
entry rather than restate the rule" — A50 specifies exactly how
this trigger fires);
[A46 three-lane race stress-test protocol](A46_three_lane_race_stress_test.md)
(§A46.2 lane-classification — A49.3's re-snapshot consumes it;
A50 does not touch A46);
W19 F4 + W20 F4 post-audit addendums (named the memory-promotion
as an **optional** carry-forward — A50 resolves the "optional"
into a trigger-gated promotion procedure).

---

## A50.1 Purpose

§A49.5 documents the Addendum protocol notice as **cumulative
across audits**: each phase-boundary audit inherits the previous
phase's notice body, updates the precedent list, and carries it
forward. The discipline has been exercised twice as of 2026-04-19
— W20 (first in-body notice; pre-A49) and W21 (first carry-over +
first dogfooding of §A49.3 audit-commit-time re-snapshot). Until
A49, the discipline was convention-only; §A49.5 documented the
convention but A49.9 trigger #4 specifies that once the discipline
has held for "two consecutive audit bodies" the promotion to
memory `feedback_git_workflow.md` becomes the authoritative
expression.

A50 resolves the ambiguity in A49.9 trigger #4 ("adds an
'audit-commit-time status-gate' entry" — no body shape, no gate
threshold, no §A49.3/§A49.5 update procedure) into a full
promotion workflow: §A50.2 gate threshold, §A50.3 memory bullet
body, §A50.4 downstream dossier edits, §A50.5 de-promotion
protocol. The appendix is a **promotion spec**, not the
promotion itself — the memory bullet lands in a separate W<N>D1
commit once §A50.2's gate fires.

A50 is **strictly procedural**: it adds no code, no test, and no
audit-side discipline beyond the already-documented A49.5 notice.
It standardises how the notice graduates from dossier-prose to
memory-durable.

## A50.2 Promotion gate

The memory-promotion trigger fires when **all** of the following
hold at audit-commit time for phase W<N>:

1. The in-body "Addendum protocol notice" section has been
   carried forward into three consecutive phase-boundary audit
   bodies (W<N-2>, W<N-1>, W<N>) **without drift** — each audit's
   §A49.5 notice inherits the previous one's precedent list,
   appends the new phase's entry, and preserves the template
   wording per §A49.5.
2. §A49.3's audit-commit-time check has been dogfooded in at
   least **two** of those three audits (W<N-1> + W<N> suffice;
   W21 was the first dogfooding per W21 audit §6 check #3).
3. No §A49.6 failure mode observed in any of the three audit
   windows (the W15D1 scoped-pathspec rule held; no cross-lane
   file landed inside an audit commit's diff).
4. At least **one** post-audit addendum was actually triggered
   across the three-window span (the notice's hedge fired at
   least once). As of 2026-04-19, W19 F4 + W20 F4 already count;
   W21 did not trigger an addendum (see W21 audit §6 check #3 —
   audit-commit-time re-snapshot found zero cross-lane arrivals
   during W21 window). So condition (4) is already satisfied;
   conditions (1)-(3) are the gate going forward.

If (1) fails (notice dropped or drifted on any of the three
audits), §A49.9 trigger #3 fires instead ("notice dropped from
two consecutive audit bodies") and A49 is re-audited rather than
promoted. If (2) fails (audit-commit-time check skipped),
§A49.3's dogfooding discipline is the failure — memory promotion
waits one more cycle.

Earliest fire date given the 2026-04-19 W21 baseline: W<N> = W23
(W21 was notice carry #2; W22 must carry #3 to count as the
third consecutive). W22 is therefore the **earliest eligible
carry-forward audit**, not the earliest promotion audit.

## A50.3 Memory bullet body

When §A50.2's gate fires at W<N>D1, a new bullet is appended to
memory `feedback_git_workflow.md` under the "How to apply:"
list (immediately after the W14 F1 / W15 D1 scoped-pathspec
bullet — sibling discipline, same lineage). Paste-ready template:

```markdown
- **Before issuing any `docs/audits/AUDIT_PHASE_IND_TRACKS_*.md`
  commit, re-run `git log <T_prev>..HEAD --oneline`** where
  `T_prev` is the previous phase's audit-commit sha. Compare the
  resulting sha list against the audit body's §6 recurrence-check
  narrative; if the snapshot has more shas than the §6 list (i.e.
  a cross-lane commit arrived after the audit was drafted but
  before the audit is committed), append a post-audit addendum
  per `docs/dossier/A49_audit_post_commit_addendum_protocol.md`
  §A49.4 rather than pushing the audit commit with a stale §6
  narrative. Rationale: observed four times in the repo's history
  (W16D7 → W16 audit; W19D5 → W19 audit; W20D5 → W20 audit;
  additional precedents as they accumulate) — a cross-lane commit
  landing on `main` between audit-draft and audit-commit
  invalidates the §6 narrative at the moment of committing; the
  addendum is the standard reconciliation. (A49.3 / A49.5
  dogfooding promoted to durable rule W<N>D1, YYYY-MM-DD.)
```

Body-field rules the promoting author fills at W<N>D1:

* `<T_prev>` is the concrete sha of the previous phase's audit
  commit (named literally in the bullet for reviewer clarity).
* Precedent list in the "Rationale" clause is the cumulative
  list from §A49.5 at W<N> (three to four entries minimum).
* `W<N>D1, YYYY-MM-DD` stamp follows the existing memory
  convention (see the W14 F1 / W15 D1 sibling bullet).

The body is stable under A46.2 v1; an A46.2 lane-ownership-prefix
change (A49.9 trigger #2) does not invalidate the memory bullet
(it invalidates §A49.3's reference-fidelity check, not the
re-snapshot discipline itself).

## A50.4 Downstream dossier edits (paired W<N>D1 commit)

When §A50.2's gate fires, the single W<N>D1 commit that lands
the memory bullet (§A50.3) **also** lands three dossier edits
in the same scoped pathspec per W15D1:

1. **A49.3 citation rewrite** — replace §A49.3's imperative
   re-snapshot paragraph (currently restates the rule inline)
   with a one-sentence pointer: "Per memory
   `feedback_git_workflow.md` bullet on audit-commit-time
   re-snapshot (promoted W<N>D1), the check below is a durable
   rule; the pseudocode is preserved as reference." The pseudocode
   itself is **kept** (removing it would break §A49.9 trigger #4's
   self-reference — A49.3 still canonicalises the implementation).
2. **A49.5 citation rewrite** — identical treatment: §A49.5's
   notice template is kept verbatim (still the authoritative body
   shape for the in-body notice), but the introductory paragraph
   gains a "(durable rule; see memory `feedback_git_workflow.md`)"
   citation.
3. **A49.9 trigger #4 retirement** — cross out trigger #4
   ("Memory `feedback_git_workflow.md` adds an 'audit-commit-time
   status-gate' entry…") with `~~strikethrough~~` and append
   "(FIRED W<N>D1 — memory bullet landed; §A49.3 / §A49.5
   citations updated per A50.4; A50 §A50.5 de-promotion protocol
   is now the only avenue back.)". Keep the strikethrough text so
   the trigger history is auditable; do not delete.

**Paired `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 edit**: add
a new first-order rule bullet mirroring §A50.3's memory bullet
(NEXT_SESSION §0 is the copy-pasted authoritative rule list for
fresh-session bootstrapping; the memory bullet and the §0 bullet
are always kept in sync by convention). This is **not** a
separate dossier file — the §0 edit lands in the same W<N>D1
commit.

## A50.5 De-promotion protocol

If the durable memory rule later produces a false positive — e.g.
the rule triggers a spurious addendum on a phase where the
arriving commit is a no-op (docs typo fix that retroactively
meets A46.2 ind-tracks classification), or the precedent list
grows too long to carry practically — the de-promotion path is:

1. Open a new `Fx` finding in the phase's audit §3 carry-forward
   table naming the specific false-positive symptom.
2. Wait one full phase (the discipline's stability under this
   false-positive must be observable before reverting the rule).
3. If the false positive recurs in the subsequent phase, land a
   W<N>D1 commit that (a) removes the memory bullet, (b) restores
   §A49.3 / §A49.5 to their pre-A50.4 inline form, (c) un-
   strikethrough A49.9 trigger #4 (it becomes an active trigger
   again), (d) opens a new A49.9 trigger #5 naming the specific
   false-positive for future guidance.
4. Update A50.2's gate conditions to reflect the observed
   failure mode (e.g. add a "no-op commit classification" check
   before the promotion trigger fires again).

De-promotion is therefore a **three-phase** operation (observe,
wait, revert) — never a single-phase panic revert. This mirrors
the W15D1 scoped-pathspec rule's own promotion trajectory
(observed twice, deliberated, landed — never retroactively
reverted).

## A50.6 No code landing in this appendix

A50 is specification-only. The memory bullet in §A50.3 is
paste-ready for a future W<N>D1 commit; §A50.4 specifies the
paired dossier edits; §A50.5 specifies the de-promotion. None of
the three steps requires code. A pre-commit hook that programm-
atically enforces the rule is already specified in A49.8.1
(W22D3) as a **different** escalation path (triggered by §A49.6
failure, not by A50.2 promotion gate); the two paths are
orthogonal — A50 is discipline promotion, A49.8.1 is failure
reaction.

## A50.7 Re-audit triggers

A50 must be rewritten if any of the following happens:

* **A50.2 gate fires and the promotion lands** (the §A50.4
  paired dossier edits execute successfully). §A50.3 / §A50.4 /
  §A50.5 are frozen as of this appendix's version; the post-
  promotion state of the A49/A50 pair is captured by the W<N>
  audit log and memory `feedback_git_workflow.md` version
  history (not by a new A50 revision).
* **§A50.5 de-promotion fires** (false-positive recurs and the
  rule is reverted). A50 is re-audited with an additional
  §A50.2 gate condition codifying the observed false-positive
  shape.
* **Memory system format changes** (e.g. the memory storage
  moves from flat markdown to a structured schema, or the
  `feedback_git_workflow.md` file is split into two). A50.3 /
  A50.4 paste templates need field updates to reflect the new
  storage surface.
* **A49.5 notice is deprecated in favour of a different
  discipline** (unlikely but possible — e.g. if a fully
  automated pre-commit hook per A49.8.1 makes the notice
  redundant). A50 becomes moot; appendix is marked
  **superseded** with a forward pointer to the replacement.

Until one of these triggers fires, A50 is stable and the
promotion gate (§A50.2) remains the authoritative condition for
lifting the Addendum protocol notice discipline into durable
memory-rule status. The earliest realistic fire date is **W23
audit** (2026-04-19 + 2 plan weeks, given the W21 → W22 → W23
carry-forward sequence required by §A50.2 condition (1)).

## A50.8 Relation to other appendices

* **A49 audit §6 post-commit recurrence-check addendum
  protocol** — parent appendix. A49 specifies the discipline;
  A50 specifies the promotion-to-memory of that discipline.
  §A49.9 trigger #4 is what A50 operationalises.
* **A46 three-lane race stress-test protocol** — upstream
  dependency. §A46.2's lane-ownership prefixes are consumed by
  §A49.3's re-snapshot classification, which is consumed by
  A50.3's memory bullet. A46.2 changes invalidate A49.3/A49.5
  but not A50.3 (the re-snapshot discipline itself is format-
  independent).
* **A48 MIO → HTT dependency-wait contract** — orthogonal. A48
  is forward-looking (blocked-artefact ledger); A50 is
  governance-discipline promotion. No content overlap.
* **A47 HJ-03 acceptance-test paste-replace protocol** —
  orthogonal. A47 is PR-landing-time; A50 is audit-commit-time
  discipline graduation. Different phase of the repo lifecycle.
* **memory `feedback_git_workflow.md`** — the target surface.
  A50.3 / A50.4 specify the exact promotion edits; the memory
  file receives the bullet when §A50.2 gate fires.
