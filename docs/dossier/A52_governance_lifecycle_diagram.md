# A52 · A49-A50-A51 governance lifecycle diagram

**Appendix**: A52 (§11.14.13 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-20 W24D5 design dossier (documentation-only;
no code landing — this appendix is a block-diagram companion to
the A49/A50/A51 triad, capturing the lifecycle states and
transition triggers of an audit-body discipline as it matures
from ad-hoc convention into a durable memory rule and, eventually,
into a battle-tested steady-state rule).
**Status**: **descriptive** — A52 adds no new rule, gate, or
body-shape requirement beyond A49/A50/A51; it is a single-page
navigational aid for the audit author who arrives at a phase-
boundary audit §6 and needs to know which state the current
discipline is in and what the next transition would look like.
**Governance anchors**:
[A49 audit §6 post-commit recurrence-check addendum protocol](A49_audit_post_commit_addendum_protocol.md)
(convention → gate-specified transition);
[A50 addendum protocol notice memory-promotion spec](A50_addendum_notice_memory_promotion_spec.md)
(gate-specified → promoted transitions — strict §A50.2 and patient §A50.2a);
[A51 post-promotion memory-rule stability protocol](A51_post_promotion_memory_stability_protocol.md)
(promoted → post-promotion verified → de-promoted transitions).
**Parent references**: W24D5 §2 unpicked-option-pool "A50-A51
governance lifecycle diagram" option (selected for W24D5 landing
as the third-of-three A5x dossier candidates alongside the W18 F3
anchor-location and cross-check channel-catalogue extension
carries).

---

## A52.1 Purpose

The A49/A50/A51 triad specifies a **six-state lifecycle** for an
audit-body discipline, but each appendix only paints one leg of
the arc: A49 formalises the ad-hoc convention; A50 specifies the
promotion gate and de-promotion reversal; A51 specifies the post-
promotion verification discipline. The audit author who lands at
a W<N>D7 §6 row needs to answer two questions to pick the correct
paste-template:

1. **Which state is the discipline currently in?** (determines
   whether §A49.5's inline notice or §A51.2's per-phase check is
   the correct §6 body shape.)
2. **What transition, if any, is firing *this* phase?** (determines
   whether the §A50.4 paired landing or the §A50.5 three-phase
   de-promotion walk is in scope.)

A52 answers both with a single block diagram, a per-state
responsibility row, and a transition-trigger table. It is
explicitly **non-prescriptive** — every rule lives in A49/A50/A51;
A52 only assembles the existing rules into a navigable map.

## A52.2 State diagram

```
                                    ┌─────────────────────┐
                                    │ §A50.5 step 3       │
                                    │ (false-positive     │
                                    │  recurrence lands)  │
                                    │                     ▼
┌──────────┐  A49.1   ┌─────────┐  A50.2 / A50.2a   ┌──────────────┐
│ [S0]     │ ───────▶ │ [S1]    │ ─────────────────▶│ [S3]         │
│ AD-HOC   │          │ GATE-   │                   │ PROMOTED     │
│ CONVEN-  │  ◀───────│ SPECIFI │◀──────────────────│ (durable     │
│ TION     │   A49.9  │ ED      │  A50.5 (3 phases  │  memory rule │
│          │  trigger │         │   observe/wait/   │  active)     │
│          │  #4     │         │   revert)         │              │
└──────────┘  fires   └─────────┘                   └──────────────┘
                          ▲                                │
                          │  A50.2 / A50.2a gate evaluated │  A51.5
                          │  but defers (conditions        │  maturation
                          │  unmet — strict gate in W23;   │  threshold
                          │  patient gate in W24)          │  passed
                          │                                ▼
                     ┌─────────┐                   ┌──────────────┐
                     │ [S2]    │                   │ [S4]         │
                     │ GATE-   │                   │ POST-PROMO   │
                     │ DEFERRED│                   │ VERIFIED     │
                     │         │                   │ (§A51.2 per- │
                     │         │                   │  phase check │
                     │         │                   │  running)    │
                     └─────────┘                   └──────────────┘
                                                          │
                                                  A51.4 ledger
                                                  counter > A51.5
                                                  floor
                                                          ▼
                                                   ┌──────────────┐
                                                   │ [S5]         │
                                                   │ BATTLE-TESTED│
                                                   │ (quarterly   │
                                                   │  spot-check  │
                                                   │  only)       │
                                                   └──────────────┘
```

## A52.3 Per-state responsibilities

| State | Audit author's §6 paste-template | Memory rule active? | NEXT_SESSION.md §0 updated? |
|---|---|---|---|
| [S0] AD-HOC CONVENTION | none — the convention exists only in `git log` narrative | no | no |
| [S1] GATE-SPECIFIED | §A49.5 inline Addendum protocol notice (cumulative across audits) | no (memory bullet drafted but not landed) | no |
| [S2] GATE-DEFERRED | identical to [S1] — §A49.5 inline notice carried forward; strict-defer or patient-accumulator row added to §6 | no | no |
| [S3] PROMOTED | §A50.4 paired commit just landed — audit body rewrites notice to cite the memory bullet rather than restate the discipline inline | yes (just landed) | yes (just landed) |
| [S4] POST-PROMO VERIFIED | §A51.2 per-phase §6 check (positive verification + drift detection) | yes (load-bearing) | yes |
| [S5] BATTLE-TESTED | §A51.5 relaxed quarterly spot-check; not every phase | yes (stable) | yes |

## A52.4 Transition triggers

| From | To | Trigger (citation) |
|---|---|---|
| [S0] | [S1] | A49.1's "three observations" threshold met and A49 dossier lands (convention lifted into named protocol). |
| [S1] | [S2] | §A50.2 strict gate or §A50.2a patient gate formally evaluated at W<N>D1 / W<N>D7 and conditions not all met (W23D1 strict defer; W24D1+ patient accumulator). |
| [S2] | [S1] | Evaluation cycle resets for next phase (no actual state change — [S1] and [S2] are the same substantive state, with [S2] annotating the transient defer observation). |
| [S1]/[S2] | [S3] | §A50.2 all four sub-conditions PASS **or** §A50.2a all four sub-conditions PASS; §A50.4 paired dossier + memory commit lands in same W<N>D1 commit as the memory-rule write. |
| [S3] | [S4] | First post-promotion W<N>D7 audit executes §A51.2 per-phase check cleanly; §A51.4 ledger initialises at 1. |
| [S4] | [S4] | Each subsequent post-promotion W<N>D7 audit increments the §A51.4 ledger by 1 (no state change). |
| [S4] | [S5] | §A51.4 counter exceeds §A51.5 mandatory-floor threshold with zero §A51.3 drift-detection flags. |
| [S5] | [S4] | §A51.3 drift detection flags on a quarterly spot-check; discipline reverts to per-phase check for three consecutive phases minimum. |
| [S3]/[S4]/[S5] | [S1] | §A50.5 three-phase de-promotion walk completes: (1) Fx finding, (2) one-phase wait, (3) recurrence lands → W<N>D1 commit removes memory bullet, restores §A49.3/§A49.5 inline form, un-strikethroughs A49.9 trigger #4. |

## A52.5 Current state (2026-04-20 W24D5)

The Addendum-protocol-notice discipline is in **[S2] GATE-
DEFERRED** as of the W23D1 §A50.2 strict-gate formal evaluation
(W23 audit §6 check #4 returned (1)(2)(3) PASS + (4) FAIL). W24D1
`2f02d1f` landed §A50.2a (patient promotion path, 179 L addition
to A50); the patient gate's accumulators currently stand at
dogfooding count ≥ 4 (W21–W24 expected) + strict-defer count 1
(W23D1) with W24D1 not counting as a strict defer (it landed
§A50.2a, not a strict-gate re-evaluation). W24D7 audit §6 check
#4 (strict) + new check #5 (patient accumulators) decide whether
the state advances toward [S3] or stays at [S2]; §A50.2a earliest
fire is W25D1 (patient) per A50.2a's "5-dogfooding + 3-defer"
baseline. A51 therefore remains **dormant** (trigger-gated) as
of W24D5.

## A52.6 No code landing in this appendix

A52 adds no test, no code, no new gate, and no new body-shape
requirement. It is a single-page navigational aid. The §A52.2
state diagram reproduces transitions already spelled out in
A49.9 triggers + A50.2 / A50.2a / A50.5 + A51.4 / A51.5; the
§A52.3 responsibilities table reproduces the paste-template rules
already in A49.5 + A51.2; the §A52.4 trigger table reproduces
gate conditions already in A50.2 / A50.2a / A51.5. A52's value-
add is **assembly**, not new specification.

## A52.7 Re-audit triggers

A52 must be rewritten if any of the following happens:

* A new state is added to the lifecycle (e.g., a "frozen" state
  between [S5] and an eventual deprecation, or a "probationary"
  sub-state of [S3] specified by a future A50 addendum).
* A new transition trigger is added (e.g., a fast-track
  promotion path parallel to strict §A50.2 / patient §A50.2a, or
  a zero-phase emergency de-promotion shortcut for catastrophic
  false positives).
* A49 or A50 or A51 is materially re-scoped (version bump in
  their respective §x.1 Purpose sections) — A52's diagram + tables
  must stay in sync with the authoritative appendices.
* A second governance lifecycle emerges (e.g., a new audit-body
  discipline unrelated to the Addendum protocol notice that
  follows the same S0→S5 arc) — at that point A52 is generalised
  or forked into A52a / A52b.

## A52.8 Relation to other appendices

A52 is **strictly downstream** of A49 / A50 / A51. It adds no
requirement any of the three need to honour; it assembles their
rules for the audit author's convenience. In particular:

* A52 does not alter A50.3's memory bullet body, A50.4's paired
  edit list, or A50.5's three-phase de-promotion walk.
* A52 does not alter A51.2's per-phase §6 check template, A51.3's
  drift-detection logic, or A51.5's mandatory floor.
* A52 does not alter A49.3's audit-commit-time re-snapshot or
  A49.5's cumulative-across-audits notice body shape.

If a future audit author finds a contradiction between A52's
diagram/tables and any of A49/A50/A51's prose, **the prose in
A49/A50/A51 is authoritative** and A52 is re-audited per §A52.7.
