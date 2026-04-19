# A46 · Three-lane race stress-test protocol

**Appendix**: A46 (§11.14.7 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W18D5 design dossier (documentation-only;
no code landing — the protocol specifies an **audit-time** check,
not a run-time guard; the existing scoped-`git commit -- <paths>`
rule from W15D1 is the load-bearing mitigation).
**Status**: **deferred-to-observation** — landing trigger is the
first phase where all three lanes (ind-tracks, bass, gallery) land
commits into the same audit window. Until that phase occurs, §6 of
every phase-boundary audit carries the existing two-lane recurrence
check (W12 F1 / W14 F1) unchanged; the three-lane extension is a
superset applied only when observed.
**Governance anchors**:
memory `feedback_git_workflow.md` (durable first-order rules —
additive-commits, pre-commit `git status --short` gate, scoped
`git commit -- <paths>`);
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 (copy-pasted rules);
`docs/INDEPENDENT_TRACKS_PLAN.md` §21 (Week-10 + Week-11 entries
spelling out the post-W8-FM1 `/project` rule).
**Parent references**:
W12 F1 (cross-lane contamination, W12D3 `99465e5`; mitigated W13D1
`41b7200` via `git status --short` gate);
W14 F1 (recurrence under the brief reset→commit gap, W14D3 `4eb044b`;
mitigated W15D1 `d48b920` via scoped-pathspec rule);
W16 F1 / W16D7 addendum (cross-lane `4c50313` landed between
W16D5 landing and audit commit — first real adversarial stress
test of W15D1, **PASSED**);
W17 audit §6 check #1 + W17D3 (scoped-pathspec rule excluded four
unstaged `bass_py/bass/hierarchy/*` files by construction — second
distinct adversarial stress test, working-tree-drift variant,
**PASSED**);
W17 F3 (three-lane race not yet observed — landing trigger for the
code-side of this dossier).

---

## A46.1 Purpose

The W15D1 scoped-`git commit -- <paths>` rule closes the brief race
window between a pre-commit `git status --short` check and the
subsequent `git commit` invocation. Two distinct adversarial
scenarios have already been observed in the repository's history:

* **W16D7 concurrent-commit scenario**: a sibling lane's commit
  landed in the short gap between our `git status` snapshot and
  our `git commit` invocation (cross-lane `4c50313` between W16D5
  `484ffed` and audit commit `646784b`; neither contaminated the
  other).
* **W17D3 working-tree-drift scenario**: a sibling lane left four
  unstaged modifications in the working tree; the scoped pathspec
  excluded them by construction (W17D3 `3137cc0` shipped with only
  `bass_py/mio/tests/test_sigma_cone_provenance.py`; the bass-lane
  drift under `bass_py/bass/hierarchy/` was ignored).

The third scenario — all three lanes (ind-tracks + bass + gallery)
landing commits in the **same** audit window — has not yet occurred
in the repo's history (W17 F3). This appendix specifies the audit-
time inspection protocol, the `§6 recurrence check` row template,
and the failure-pattern fingerprint for the first three-lane
observation, so the audit author does not have to invent a format
in the moment.

## A46.2 Definition — "same audit window"

Let `T_prev` = the phase-boundary audit commit sha from the previous
phase (e.g. `IND_TRACKS_W17` audit `6f6df1c`). Let `T_curr` = the
phase-boundary audit commit sha for the current phase. The "audit
window" is the set of commits `{c : T_prev < c <= T_curr}` on
`main`.

A commit `c` is in **lane L** if `git show --stat c` touches a
disjoint subset of the three ownership lanes:

* **ind-tracks** — `bass_py/mio/**`, `bass_py/workspace/**`,
  `bass_py/src/common/**`, `bass_py/tsc/**`, `docs/dossier/A*`,
  `docs/INDEPENDENT_TRACKS_*`, `docs/audits/AUDIT_PHASE_IND_TRACKS_*`,
  `project/00_manuscript/ch{03,11,12}_*.tex`, this appendix.
* **bass** — `bass_py/bass/**` and bass-side plan/audit paths.
* **gallery** — `plots/physics_gallery/**`.

A commit that touches **multiple** lanes is a cross-lane
contamination by construction — recorded as a `Fx` finding in the
current phase's audit and cross-referenced here.

The **three-lane race** is the case where the audit window contains
at least one commit per lane (three pairwise-disjoint commits, or
equivalently one triple-contaminated commit — the latter would
fail the W15D1 scoped rule and the pre-commit gate simultaneously).

## A46.3 Adversarial recipe (for the first observed window)

When a reviewer deliberately tries to trigger a three-lane race
post-observation (to lock the §6 row against regression), reproduce
the failure mode as follows:

1. Set three terminals, one per lane, with disjoint staging.
2. Each terminal runs `git status --short` (passes the pre-commit
   gate — each sees only its own staged paths).
3. Each terminal runs `git commit -- <own-paths>` in close
   succession.
4. `git log --oneline main` shows three commits in rapid order; the
   order of arrival is non-deterministic.

The scoped-pathspec rule guarantees that **no commit's diff is
contaminated**, regardless of the arrival order — step 3's
pathspec form makes `git commit` treat only those paths from the
index. Any files staged by a concurrent lane between our
`git status` and our `git commit` are excluded by construction.
The three-lane case is therefore a **non-finding by design**; it
is still audit-worthy because it is the first observation of the
scenario and future readers should be able to verify the non-
finding directly.

## A46.4 Audit §6 row template (three-lane case)

On the first observed three-lane window, the phase-boundary audit
§6 row reads:

> **§6.1 W12 F1 / W14 F1 recurrence check** — `git show --stat`
> on every sha in the audit window confirms each commit's diff is
> scoped to a single lane. **Three-lane observation**: the audit
> window contains at least one commit from each of ind-tracks,
> bass, and gallery (shas `<ind>`, `<bass>`, `<gallery>`). Per
> A46.2 this is the first three-lane observation in the repo's
> history; per A46.3 the scoped-pathspec rule (W15D1) is a non-
> finding by design; per A46.5 the failure-pattern fingerprint is
> absent (no cross-lane paths in any of the three `git show
> --stat` outputs). **Closes W17 F3.** Returns **PASSED** — third
> adversarial stress-test scenario (W16D7 concurrent-commit, W17D3
> working-tree-drift, W<NN>D<M> three-lane race).

Subsequent phase audits drop the "first three-lane observation"
language and resume the steady-state phrasing.

## A46.5 Failure-pattern fingerprint

If the three-lane window produces a cross-lane contamination
(i.e. the scoped-pathspec rule fails — which it should not), the
fingerprint on `git show --stat <sha>` is:

* the commit message body describes changes in exactly one lane
  (the author's intended lane);
* the stat output lists files from two or three lanes;
* the gap between lanes is characterised by ownership prefix
  (e.g. `bass_py/mio/*` ind-tracks row adjacent to `bass_py/bass/*`
  bass row).

On observation, the audit § records the event as a new `Fx`
finding, the mitigation is a re-read of the `git commit -- <paths>`
command used (scan for a missing trailing `--`, a glob that fired
wider than intended, or a `-a` / `--all` shorthand that bypassed
the pathspec form), and the next-session plan carries an
`R<n>` repair row if the habit needs reinforcement.

### A46.5.1 Common failure-mode invocations (W19D3 / W18 R2)

Three invocation shapes are known to bypass the W15D1 scoped-
pathspec rule and should be checked first when the fingerprint
above is observed:

1. **Missing trailing `--`** — e.g. `git commit -m "..." bass_py/mio/foo.py`
   without the separator. Git accepts this when no path matches a
   revision, but a path that collides with a branch/ref name
   causes silent misinterpretation. The separator `--` is the
   documented "everything after this is a pathspec" marker and
   the W15D1 rule depends on it.
2. **`git add -A` + `git commit -m` (no pathspec)** — the `commit`
   invocation carries no pathspec at all; the entire staged index
   goes in, including any files a concurrent lane's `git add`
   dropped into the index during the gap. This is the exact
   failure mode W12 F1 / W14 F1 exhibited. The W15D1 rule
   requires the trailing `-- <path1> <path2> …` list to close the
   race window, so the `-m`-only form is non-compliant by
   construction.
3. **`git commit -am`** — the `-a` flag stages every tracked
   modification before committing. It looks like a scoped invocation
   because a `-m "..."` message is still required, but there is no
   pathspec at all and tracked modifications from other lanes (e.g.
   a bass-lane edit to `bass_py/bass/hierarchy/*` sitting in the
   working tree) sweep in silently. The W17D3 working-tree-drift
   scenario would have failed under `-am` exactly as W14 F1 did
   under `add -A` + `commit -m`; the scoped pathspec form is the
   only invocation that excludes such drift by construction.

When any of the three shapes is identified in the audit's
`git reflog` inspection, the `R<n>` repair row calls for an
explicit reinforcement entry in memory `feedback_git_workflow.md`
naming the specific shape, rather than a generic "re-read the
rule" entry.

## A46.6 Relation to other appendices

* **A41 report_type extension protocol** — §A41.6's HJ-03 worked
  example is a multi-path ind-tracks landing that could
  incidentally coincide with a bass or gallery window; A46's §6
  template is the audit vehicle for verifying the coincidence did
  not contaminate the HJ-03 commit's diff. Concretely, the HJ-03
  PR is a three-file ind-tracks landing — `docs/dossier/
  A42_evidence_anatomy.md` (the HJ-03 design dossier updates),
  §A41.6 step 6.5 (the freeze-the-replay-harness-signature row
  introduced W18D3), and §A45.6's paste-ready five-test block.
  All three paths fall under the ind-tracks ownership prefix, so
  their bundle commit remains single-lane even if bass or gallery
  lanes are committing in the same audit window; A46.2's lane-
  classification therefore resolves the HJ-03 commit to
  ind-tracks regardless of concurrent lane activity.
* **A44 MIO → HTT handshake sequence** — A44's `git_commit`
  capture-time invariant (W6 FM6 / W11 F5 / W17D1) is an
  *at-instantiation* property of the certificate; A46's scoped-
  pathspec rule is an *at-commit* property of the git DAG.
  Independent axes; no overlap.
* **memory `feedback_git_workflow.md`** — durable rule store;
  this appendix is the paste-ready audit §6 template that the
  memory entry points at when the three-lane case first occurs.

## A46.7 No code landing in this appendix

A46 is specification-only. The `§6` audit template is prose that
the audit author paste-copies into `docs/audits/
AUDIT_PHASE_IND_TRACKS_W<NN>_<DATE>.md` on the first three-lane
observation. Re-audit trigger: if the scoped-pathspec rule ever
fails under a three-lane window, A46.5's fingerprint becomes
load-bearing and this appendix must be rewritten to specify the
code-side guard (candidate: a pre-commit hook that rejects any
`git commit` invocation whose pathspec list spans more than one
lane-ownership prefix).
