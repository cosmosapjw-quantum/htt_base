# A50 · Addendum protocol notice memory-promotion spec

**Appendix**: A50 (§11.14.11 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W22D5 design dossier (documentation-only;
no code landing — this appendix specifies the **promotion
workflow** that lifts the A49.5 "Addendum protocol notice"
discipline from audit-body convention into durable memory-rule
status).
**Status**: **promoted (patient path fired W25D7)** — the strict
§A50.2 gate was formally evaluated against the W23/W24/W25 sliding
window and returned a third consecutive `(1)(2)(3) PASS + (4) FAIL`
defer; the parallel §A50.2a patient gate then fired with
dogfooding count = **5** (W21–W25), audit-evaluated strict-defer
count = **3** (W23–W25), and zero §A49.6 failures across the
five-phase window. The paired §A50.4 landing updated A49.3 /
A49.5 citations, retired A49.9 trigger #4, and landed the durable
memory + NEXT_SESSION §0 bullet on 2026-04-20.
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
promotion itself — the memory bullet lands in the paired
promotion commit at W<N>D7 (or the immediate W<N>D(7+ε)
follow-up if the audit author chooses to separate the audit
body from the promotion edit) once §A50.2 or §A50.2a fires.

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
   least once). **Sliding-window clarification (W22 R1 / W23D1)**:
   the "three-window span" is strictly the currently-evaluated
   W<N-2> / W<N-1> / W<N> audit windows — addendum precedents
   from prior spans (e.g. W19 F4 / W20 F4 when evaluating a W24+
   promotion) do **not** carry forward past their window's
   eviction from the three-audit sliding window. Re-evaluate
   condition (4) fresh on each promotion-gate firing against the
   three specific audits being counted by condition (1). As of
   2026-04-19, W19 F4 + W20 F4 satisfied condition (4) for the
   W20 / W21 / W22 span (W20 was the terminal audit of that
   window containing W20 F4); for the W21 / W22 / W23 span
   evaluated at W23D1, condition (4) requires an addendum inside
   W21, W22, or W23 — W21 §6 check #3 and W22 §6 check #3 both
   returned zero cross-lane arrivals, so the condition is
   currently **unsatisfied** and waits on a W23 trigger or later
   re-evaluation. The plan's "As of 2026-04-19" phrasing above is
   a point-in-time snapshot of the W20 / W21 / W22 evaluation,
   not a permanent free pass.

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

## A50.2a Alternate promotion path — "patient promotion" (W23 F4 / W24D1)

### Problem

The W23D1 sliding-window clarification (W22 R1) correctly tightened
§A50.2 condition (4) to require an addendum trigger **within the
currently-evaluated three-window span**. This is the right
semantic for maturity — each promotion decision looks at fresh
evidence, not historical carry-forward. However, the W23 audit's
formal §A50.2 evaluation exposed a **starvation risk**: in a
quiet-lane-activity period (no concurrent bass or gallery
commits arriving between audit-write and audit-commit), condition
(4) can never fire — the discipline `A49.3 → clean §6 #3 → no
addendum needed` returns PASSED on every phase, but the hedge is
never "load-bearing in practice" in the sense condition (4)
requires.

The W21/W22/W23 span at W23D1 evaluation returned (1)(2)(3) PASS
+ (4) FAIL; if W24/W25/W26/... all continue the clean-window
streak, condition (4) stays FAIL indefinitely, even though the
discipline is **demonstrably working correctly** (eight
consecutive stress-tests of the W15D1 scoped-pathspec rule PASSED
through W23; three consecutive A49.3 dogfoodings returned clean).
The gate becomes effectively unfireable despite the discipline
being exactly the load-bearing rule A50 was designed to promote.

### Alternate fire condition

§A50.2a fires when **all** of the following hold at audit-commit
time for phase W<N>:

1. Conditions **(1)–(3)** from §A50.2 hold (unchanged: three
   consecutive notices without drift + §A49.3 dogfooded in ≥ two
   of those three + zero §A49.6 failures).
2. **§A49.3 dogfooded in *five* consecutive phases** (stronger
   than §A50.2 (2)'s "≥ two of three" — §A50.2a requires strict
   five-in-a-row accumulation). Baseline begins at W21 (first
   dogfooding per W21 audit §6 check #3). Earliest count: W21 +
   W22 + W23 + W24 + W25 = five.
3. **Three consecutive audit-evaluated §A50.2 strict-gate
   evaluations returned (1)(2)(3) PASS + (4) FAIL**, i.e., the
   strict gate has been attempted and explicitly deferred three
   times under the W23D1 sliding-window reading, with the defer
   reason always being condition (4) (absent-trigger), never
   condition (1) drift or (2) skipped dogfooding or (3) observed
   failure. The accumulator counts the **phase-audit** row for
   each phase (W23 audit = first defer, W24 audit = second, W25
   audit = third), even if an earlier commit body in that same
   phase also recorded the provisional outcome.
4. Zero §A49.6 failure mode observations across the **five-phase
   window** used for condition 2, not just the three-phase span
   from §A50.2 (1).

Earliest §A50.2a fire date given the 2026-04-20 W23 baseline:
**W25 audit**. Baseline: W21 dogfooding = 1; W22 = 2; W23 = 3;
W24 = 4; W25 = 5 — satisfies condition 2. W23 audit strict-gate
defer = 1; W24 audit = 2; W25 audit = 3 — satisfies condition 3.
W25 audit-commit time is the earliest instant when all four
§A50.2a conditions hold.

### Relationship to §A50.2 (strict gate)

§A50.2 and §A50.2a are **parallel paths**; either can fire the
promotion. The strict gate (§A50.2) fires **immediately** on any
phase where a real cross-lane addendum-triggering arrival lands
in the three-window span — this is the fast path when the
discipline demonstrates load-bearing on a real event. The
patient path (§A50.2a) fires when accumulated clean-window
maturity exceeds the five-dogfooding + three-defer threshold,
even in the absence of any real trigger — this is the slow path
for quiet lane-activity periods.

If the strict gate fires first (e.g., W24 sees a cross-lane
arrival in its §6 check #3), §A50.2a becomes moot for that
promotion cycle. If the patient path fires first, condition (4)
of §A50.2 is retroactively "satisfied by maturity accumulation"
for logging purposes, and the memory bullet records the
promotion basis as patient (see §A50.3 below).

### Patient-promotion memory bullet basis clause

When §A50.2a fires, the §A50.3 memory bullet is **identical in
rule text** but gains a trailing basis clause:

> `(Promotion basis: patient — five consecutive A49.3 dogfoodings
> W21–W25, three consecutive audit-evaluated strict-gate defers
> W23–W25 with
> condition (4) absent-trigger; zero real addendum events in the
> promotion window.)`

The basis clause is machine-readable for future A50 re-audits and
§A50.5 de-promotion reviews. If §A50.5 fires on a patient-
promoted bullet, the de-promotion author checks **first** whether
the false positive indicates patient-path under-specification
(vs discipline-per-se failure); the basis clause guides that
distinction.

### Rationale for the five / three thresholds

* **Five consecutive A49.3 dogfoodings** mirrors §A51.4's
  "1–5 phases dense watch" threshold (§A51 is the post-
  promotion verification protocol; §A50.2a borrows its
  dense-watch count as the pre-promotion maturity threshold).
  Five phases is ~5 weeks of flawless discipline under the
  weekly-audit cadence; below 5 the evidence is thin, above 5
  the threshold becomes gratuitously conservative.
* **Three consecutive audit-evaluated strict-gate defers**
  demonstrates the strict gate was honestly attempted (not
  bypassed) and explicitly fell short three times on condition
  (4). Without this sub-condition, §A50.2a could be read as a
  way to circumvent §A50.2 from the start; requiring three
  audit-verified defers preserves §A50.2's primary authority.
* **Zero §A49.6 failures across the five-phase window** (not
  just three) is the only condition §A50.2a strictly
  *strengthens* beyond §A50.2. Rationale: patient promotion
  grants durability without a load-bearing demonstration, so
  the evidence window must be broader in the one dimension
  that *can* be observed (absence of failure modes).

### Step-by-step execution at W<N>D7 (when §A50.2a fires)

1. Verify conditions 1–4 of §A50.2a at audit-write time;
   record each PASS explicitly in audit §6 check #4 or a new
   §6 check #5 row.
2. Execute the §A50.4 paired dossier edits + NEXT_SESSION §0
   edit (identical to §A50.2 strict-gate firing).
3. Append the patient-promotion basis clause to the §A50.3
   memory bullet body verbatim from the template above.
4. Strike through **both** §A49.9 trigger #4 (per §A50.4 step
   3) **and** add a note in the strikethrough "(FIRED W<N>D7
   via §A50.2a patient path — strict gate §A50.2 still
   available for post-promotion re-audit if false positive
   observed per §A50.5)".
5. Record the W<N>D7 commit body with the per-phase evaluation
   history of both §A50.2 and §A50.2a conditions; this becomes
   the durable record for later §A50.5 reviews.

§A50.5 de-promotion applies identically to §A50.2- and §A50.2a-
promoted bullets; the only post-promotion difference is the
basis clause (which §A50.5 step 1 reads to classify the false
positive).

## A50.3 Memory bullet body

When §A50.2 or §A50.2a fires at W<N>D7, a new bullet is appended
to memory `feedback_git_workflow.md` under the "How to apply:"
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
  dogfooding promoted to durable rule W<N>D7, YYYY-MM-DD.)
```

Body-field rules the promoting author fills at W<N>D7:

* `<T_prev>` is the concrete sha of the previous phase's audit
  commit (named literally in the bullet for reviewer clarity).
* Precedent list in the "Rationale" clause is the cumulative
  list from §A49.5 at W<N> (three to four entries minimum).
* `W<N>D7, YYYY-MM-DD` stamp follows the existing memory
  convention; if the author splits the promotion into an
  immediate W<N>D(7+ε) follow-up commit, the stamp still uses
  the phase's audit day rather than inventing a new pseudo-day.

The body is stable under A46.2 v1; an A46.2 lane-ownership-prefix
change (A49.9 trigger #2) does not invalidate the memory bullet
(it invalidates §A49.3's reference-fidelity check, not the
re-snapshot discipline itself).

## A50.4 Downstream dossier edits (paired promotion commit)

When §A50.2 or §A50.2a fires, the single W<N>D7 promotion commit
that lands the memory bullet (§A50.3) **also** lands three
dossier edits in the same scoped pathspec per W15D1:

1. **A49.3 citation rewrite** — replace §A49.3's imperative
   re-snapshot paragraph (currently restates the rule inline)
   with a one-sentence pointer: "Per memory
   `feedback_git_workflow.md` bullet on audit-commit-time
   re-snapshot (promoted W<N>D7), the check below is a durable
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
   "(FIRED W<N>D7 — memory bullet landed; §A49.3 / §A49.5
   citations updated per A50.4; A50 §A50.5 de-promotion protocol
   is now the only avenue back.)". Keep the strikethrough text so
   the trigger history is auditable; do not delete.

**Paired `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 edit**: add
a new first-order rule bullet mirroring §A50.3's memory bullet
(NEXT_SESSION §0 is the copy-pasted authoritative rule list for
fresh-session bootstrapping; the memory bullet and the §0 bullet
are always kept in sync by convention). This is **not** a
separate dossier file — the §0 edit lands in the same W<N>D7
commit.

## A50.5 De-promotion protocol

If the durable memory rule later produces a false positive — e.g.
the rule triggers a spurious addendum on a phase where the
arriving commit is a no-op (docs typo fix that retroactively
meets A46.2 ind-tracks classification), or the precedent list
grows too long to carry practically — the de-promotion path is:

1. Open a new `Fx` finding in the phase's audit §3 carry-forward
   table naming the specific false-positive symptom. **Read the
   promotion basis clause first** (appended to the §A50.3 bullet
   body at promotion time): if the clause records "Promotion
   basis: patient" (§A50.2a fire), evaluate whether the false
   positive is an artefact of patient-path under-specification
   (e.g., the five-dogfooding threshold was too low for the
   quiet-period evidence shape) vs a genuine discipline failure;
   if strict (§A50.2 fire), the false positive is discipline-per-
   se and §A50.5 proceeds directly to step 2.
2. Wait one full phase (the discipline's stability under this
   false-positive must be observable before reverting the rule).
3. If the false positive recurs in the subsequent phase, land a
   W<N>D1 commit that (a) removes the memory bullet, (b) restores
   §A49.3 / §A49.5 to their pre-A50.4 inline form, (c) un-
   strikethrough A49.9 trigger #4 (it becomes an active trigger
   again), (d) opens a new A49.9 trigger #5 naming the specific
   false-positive for future guidance.
4. Update A50.2's gate conditions **or** §A50.2a's gate conditions
   (whichever path fired) to reflect the observed failure mode
   (e.g. add a "no-op commit classification" check before the
   strict-gate trigger fires again, or tighten the §A50.2a
   dogfooding-count threshold if patient-path under-specification
   was the root cause).

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
* **§A50.2a patient-promotion gate fires and the promotion lands**
  (W24D1 addition). Identical to the strict-gate trigger above —
  §A50.3 / §A50.4 / §A50.5 freeze; post-promotion record lives in
  the audit log + memory version history. The only difference is
  that the memory bullet carries the §A50.2a patient-promotion
  basis clause, which §A50.5 de-promotion reviews read first.
* **§A50.5 de-promotion fires** (false-positive recurs and the
  rule is reverted). A50 is re-audited with an additional
  §A50.2 or §A50.2a gate condition codifying the observed
  false-positive shape. The basis clause (strict vs patient)
  guides which gate section gets the new condition.
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
* **§A50.2a patient gate stalls past W30** (new trigger; fires if
  neither §A50.2 nor §A50.2a fires by W30 audit — i.e., quiet
  lane activity continues for 10+ weeks past the 2026-04-20 W23
  baseline without any strict-gate trigger, and the patient-path
  threshold has been hit but the evaluation revealed a spec gap).
  A50 is re-audited to consider a further-relaxed §A50.2b or a
  deliberate sunset of the promotion pathway.

Until one of these triggers fires, A50 is stable and the
promotion gates (§A50.2 strict + §A50.2a patient) remain the
authoritative conditions for lifting the Addendum protocol
notice discipline into durable memory-rule status. The earliest
realistic fire date under **§A50.2 (strict)** is W24 audit (per
the W23D1 sliding-window clarification); under **§A50.2a
(patient)** is W25 audit (five consecutive A49.3 dogfoodings +
three consecutive audit-evaluated strict-gate defers =
W21/W22/W23/W24/W25 + W23-audit/W24-audit/W25-audit).

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
