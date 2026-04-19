# A49 · Audit §6 post-commit recurrence-check addendum protocol

**Appendix**: A49 (§11.14.10 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W21D5 design dossier (documentation-only;
no code landing — this protocol formalises an audit-time / post-
audit-commit-time discipline already exercised three times in the
repo's history).
**Status**: **active** — the addendum pattern this appendix
formalises has now occurred three times (W16 F1 / W16D7, W19 F4 /
W19D7, W20 F4 / W20D7) and was pre-emptively documented as a
"protocol notice" in the body of the W20 audit prior to its
post-commit recurrence. A49 lifts that ad-hoc discipline into a
named protocol so future audit authors do not re-invent the
addendum body shape per phase.
**Governance anchors**:
memory `feedback_git_workflow.md` (durable first-order rules —
additive-commits, pre-commit `git status --short` gate, scoped
`git commit -- <paths>`);
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §0 (copy-pasted rules);
A46 three-lane race stress-test protocol (companion appendix —
A49 is the temporal companion to A46's structural classifier).
**Parent references**:
W16 F1 / W16D7 post-audit addendum (first observation; bass-lane
`4c50313` arrived between W16D5 `484ffed` and audit `646784b`);
W19 F4 / W19D7 post-audit addendum (second observation; bass-lane
`d7d25da` arrived between W19D5 `6d87082` and audit `bb82dd3`);
W20 F4 / W20D7 post-audit addendum (third observation; bass-lane
`9336280` arrived between W20D5 `4d7a3ed` and audit `5dfcf2d`;
**pre-documented** by an "Addendum protocol notice" paragraph in
the audit body before the recurrence happened).

---

## A49.1 Purpose

Every phase-boundary audit's §6 recurrence check (W12 F1 / W14 F1
cross-lane-contamination check + A46.2 lane-classification check)
is written against `git log T_prev..HEAD` at **audit-write time**.
The audit is then committed; the commit itself becomes the new
`T_curr`. If a cross-lane commit lands on `main` in the brief
interval between audit-write and audit-commit, the §6 narrative
becomes stale at the moment it is committed:

* The audit body declares "zero cross-lane commits during the
  W<N> window" (true at write-time);
* `git log T_prev..T_curr` at audit-commit time includes the
  arriving cross-lane commit (so the declaration is false against
  the steady-state record).

This pattern has now occurred three times. A49 specifies the
mechanical workflow that detects the staleness, the addendum body
shape that corrects it, and the pre-emption discipline that lets
the audit author hedge against the recurrence at write-time.

A49 is **strictly procedural**: it adds no run-time guard, no
test, and no code. The W15D1 scoped-`git commit -- <paths>` rule
remains the load-bearing mitigation (no observed phase has had
the addendum-detected commit *contaminate* the audit commit; the
rule held through all three precedents). A49 ensures the audit
*record* matches the steady-state DAG even when the write-window
underestimates the lane footprint.

## A49.2 Trigger condition

Let `T_prev` = the previous phase's audit-commit sha. Let `T_write`
= the moment the audit body's §6 paragraph is written; let
`T_curr` = the audit commit's sha (issued post-write). The
addendum is **required** iff:

```
git log T_prev..T_curr   ⊋   git log T_prev..T_write
```

(strict superset) **and** the additional commits in the symmetric
difference touch any lane other than ind-tracks per A46.2. The
relevant subset is:

```
{c ∈ git log T_prev..T_curr  :  c ∉ git log T_prev..T_write
                                 ∧ A46.2(c) ≠ "ind-tracks"}
```

If this set is empty (zero commits arrived during the write→commit
gap, or the only arrivals are themselves ind-tracks audit-side
commits), no addendum is needed and the audit body's §6 narrative
holds verbatim.

In practice the audit author cannot snapshot `T_write` (that
moment has no sha); the operational check is "re-run
`git log T_prev..HEAD` immediately before issuing
`git commit -- docs/audits/AUDIT_PHASE_IND_TRACKS_W<N>_*.md
docs/INDEPENDENT_TRACKS_NEXT_SESSION.md`" — see §A49.5.

## A49.3 Trigger detection — the audit-commit-time check

The mechanical check that should precede every audit commit:

```bash
# Just before issuing the audit commit:
git log T_prev..HEAD --oneline           # snapshot of the window
                                          # at audit-commit time
# Compare against the §6 paragraph's window-commit list.
# If the snapshot has more shas than the §6 list, the addendum is
# required; if the new shas are all ind-tracks audit-side commits,
# no addendum needed (just update the §6 list); otherwise A49.4.
```

`T_prev` is the previous phase's audit-commit sha (e.g.
`AUDIT_PHASE_IND_TRACKS_W19_*` audit commit `bb82dd3`'s parent
chain back to `AUDIT_PHASE_IND_TRACKS_W18_*` audit commit). `HEAD`
at this stage is the staging-index-pending audit commit's parent.

The check has two failure modes:

1. **Forgot to re-run.** The audit body's §6 paragraph is treated
   as authoritative; the staleness goes unnoticed until the next
   phase's audit author runs A46.2 against the previous window
   and discovers the missing commit. In all three observed
   precedents the *next-phase* audit author re-ran the window and
   appended the addendum within ≤ 30 min of the prior phase's
   audit commit; this is acceptable but suboptimal — the same-
   phase author has the local context to write a faithful
   addendum.
2. **Re-ran but mis-classified.** If the new commit's sha touches
   `docs/audits/AUDIT_PHASE_FB*` or `docs/lowell_bianchi/*` (the
   bass-lane audit/plan paths), A46.2 classifies it as bass, not
   as ind-tracks audit — see W20D7 precedent where bass-lane
   `9336280` touched `docs/audits/AUDIT_PHASE_FB3_*.md` +
   `docs/lowell_bianchi/*` and required the addendum.

## A49.4 Addendum body shape — the paste-ready template

The addendum sits at the bottom of the audit file, after the
existing §8 / §10 closing sections, following the additive-commit
rule (never `--amend`; per memory `feedback_git_workflow.md`).

Paste-ready template (substitute placeholders enclosed in
`<...>`):

```markdown
## Post-audit addendum (W<N> F<NN> — A46.2 window re-classification)

**Committed <YYYY-MM-DD>, post `<audit-commit-sha>`.** The audit
body above was written against the then-current
`git log <T_prev-sha>..HEAD` output and declared the W<N> window
**<single-lane | two-lane | …>** (W<N> §6 check #1 narrative:
"<verbatim quote>"; W<N> §6 check #2 classification:
"<verbatim quote>"). That declaration held at the time of writing
but was invalidated by the <bass | gallery>-lane commit
**`<arrival-sha>`** (`<arrival-commit-message-subject>`,
`<YYYY-MM-DD HH:MM:SS +TZ>`), which landed on `main` between
W<N>D<M> `<last-landing-sha>` (`<HH:MM>`) and the audit commit
`<audit-commit-sha>` (`<HH:MM>`) — <approximate-gap> before the
audit commit.

This mirrors the <list of prior addendum precedents> post-audit
addendum pattern (<n>th occurrence of the same scenario; the
addendum protocol notice [in the audit body | absent — re-add for
W<N+1>] pre-documented the expected recurrence). Mechanical
re-verification:

- `git show --stat <arrival-sha>` returns: `<file 1>` + `<file 2>`
  + … . <Per A46.2 lane classification reasoning>. **All <n>
  paths are <lane>-lane per A46.2.** Zero <other-lane> paths.
- `git show --stat <audit-commit-sha>` returns:
  `<docs/audits/AUDIT_PHASE_IND_TRACKS_W<N>_<DATE>.md>` +
  `<docs/INDEPENDENT_TRACKS_NEXT_SESSION.md>` — **both
  ind-tracks-owned per A46.2**. Zero bass or gallery paths.
  <Optional: add "The W15D1 scoped-pathspec rule excluded the
  same drift vectors that …">.

### Revised §6 check #1 — W12 F1 / W14 F1 recurrence check

**PASSED** (unchanged verdict). `git show --stat` on the <n>
W<N>-window shas (`<sha-1>`, … `<sha-n>`) shows each commit
scoped to a single lane:

- ind-tracks: `{<sha-list>}` — <n> commits, each touching <…>.
- bass: `{<sha-list>}` — <n> commits, touching only <…>.
- gallery: `{<sha-list>}` — <n> commits, touching only <…>.

Zero file overlap between <lane> commit sets. <Optional drift-
vector observations>.

### Revised §6 check #2 — A46.2 lane classification

A46.2 applied to the <n> W<N>-window shas produces:
`{ind-tracks: <n_i>, bass: <n_b>, gallery: <n_g>}`. **<k> lane(s)
observed, not three.** A46.4's first-three-lane-observation
template <remains paste-ready | TRIGGERED — see §A46.4 paste in §6
above>.

### Stress-test ledger update

The W15D1 scoped-pathspec rule has now been exercised under the
following adversarial windows:

- **W16D7** — concurrent-commit (bass-lane `4c50313` between
  W16D5 and audit).
- **W17D3** — working-tree-drift (four unstaged
  `bass_py/bass/hierarchy/*` files at commit time).
- **W18D5→W18D7** — second concurrent-commit observation
  (bass-lane `92cefa2`).
- **W19D5→W19D7** — third concurrent-commit observation +
  staging-index drift.
- **W20D5→W20D7** — fourth concurrent-commit observation +
  staging-index drift + working-tree drift (three independent
  drift vectors).
- **<W<N>D…→W<N>D…>** — <Nth> <description>.

### Carry-forward W<N> F<NN> → §3 table

W<N> F<NN> (this addendum — stale <X-lane> declaration in the
audit body, corrected here) is **RESOLVED by this addendum**;
<no W<N+1> repair is required beyond … | a W<N+1> R<n> repair
row is opened to …>. <Optional memory-update note.>

Phase `IND_TRACKS_W<N>` closure re-affirmed with the corrected
<X-lane> window narrative; no gate re-test needed (all five items
remain green under the corrected classification).
```

The body fields the author always fills:

* `<audit-commit-sha>`, `<arrival-sha>`, `<last-landing-sha>` —
  three shas naming the window's two endpoints + the arriving
  commit.
* `<arrival-commit-message-subject>` — verbatim from
  `git show --no-patch --pretty=%s <arrival-sha>`.
* `<HH:MM>` timestamps — for the gap, name the rough order of
  magnitude (≤ 2 min, ≤ 30 min, ≤ 1 h).
* `<list of prior addendum precedents>` — for the second
  occurrence cite W16; for the third, cite W16 + W19; for the
  fourth, cite W16 + W19 + W20; etc.

## A49.5 Pre-emption discipline — the "Addendum protocol notice"

W20 introduced the discipline of pre-documenting the addendum
hazard in the audit body itself, before the addendum has been
triggered. The verbatim W20 paragraph is reproduced here as the
template:

```markdown
## Addendum protocol notice

The W<N-1> post-audit addendum observed a <lane>-lane commit
(`<sha>`) landing on `main` between W<N-1>D<M> and the audit
commit (`<sha>`), <approximate gap> before audit-commit. The
pattern — a cross-lane commit arriving after the audit body is
written but before the audit is committed — has now occurred
<n> times (<list precedents>). This audit's §6 W<N> check #1 is
written against `git log <T_prev>..HEAD` at the time of drafting
(<n> W<N> commits, <m> bass-lane arrivals). **If a cross-lane
commit arrives between audit-write and audit-commit**, a
W<N> F<NN> post-audit addendum is appended with the revised
A46.2 classification, following the W<N-1> F<n> precedent. This
note is kept explicit here so the addendum pattern is protocol-
level, not improvised per-phase.
```

Placement: the notice goes between the §10 closing section and
any addendum that subsequently lands. It is **kept** (not
deleted) on a phase where no addendum is needed, so future
phases inherit the cumulative ledger of precedents.

## A49.6 Failure-pattern fingerprint

If the addendum-detected commit ever **does** contaminate the
audit commit (which it should not under the W15D1 scoped-
pathspec rule), the fingerprint is:

* `git show --stat <audit-commit-sha>` lists files outside
  `docs/audits/AUDIT_PHASE_IND_TRACKS_*.md` /
  `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` — typically
  `bass_py/bass/*` or `plots/physics_gallery/*`;
* the audit body's §6 ind-tracks-only file list does not match
  the actual diff;
* the addendum body's "Revised §6 check #1" cannot honestly
  return PASSED — it must instead open a new `Fx` finding
  documenting the contamination.

On observation, the audit author's responsibilities expand:

1. Write the §6 contamination-row addendum per A46.5's
   fingerprint format (not A49.4's clean-window format);
2. Open a new `Fx` finding in the §3 carry-forward table with
   severity = **P0** (the W15D1 mitigation has failed);
3. Re-read the audit-commit invocation to identify which of the
   §A46.5.1 bypass shapes was used (missing `--`, `-am`,
   `add -A` + `-m`);
4. Add a memory `feedback_git_workflow.md` reinforcement entry
   naming the specific shape;
5. Re-issue the audit's mitigation as a follow-up commit
   re-asserting the scoped-pathspec rule per §A46.5.

This failure mode has **never** been observed (W16/W19/W20 all
held; the audit commits were single-lane ind-tracks). A49.6 is
specified for protocol completeness; if it ever fires, A49 is
itself re-audited and the workflow tightens (candidate: a
git pre-commit hook that rejects an audit commit whose stat
spans more than one lane prefix).

## A49.7 Relation to other appendices

* **A46 three-lane race stress-test protocol** — companion. A46
  is the *structural* classifier (which lanes touched the
  window); A49 is the *temporal* protocol (when to re-snapshot
  the window). A46.2's lane-ownership prefix tables are reused
  verbatim by A49.4's classification step. A46.4's first-three-
  lane-observation template fires *inside* A49.4's "Revised §6
  check #2" body when the addendum's re-snapshot is the first to
  cross all three lanes.
* **A44 MIO → HTT handshake sequence** — orthogonal axis. A44
  governs at-instantiation invariants on the certificate; A49
  governs at-audit-commit-time invariants on the §6 narrative.
  No content overlap.
* **A45 cache-replay drift protocol** — orthogonal axis. A45 is
  content-level on artefacts; A49 is record-level on audits.
* **A47 HJ-03 acceptance-test paste-replace protocol** —
  orthogonal axis. A47 is the *PR-time* checklist for the HJ-03
  landing; A49 is the *audit-time* checklist for the
  phase-boundary commit.
* **A48 MIO → HTT dependency-wait contract** — orthogonal axis.
  A48 is the *forward-looking* SSOT ledger of blocked artefacts;
  A49 is the *backward-looking* SSOT discipline for audit
  reconciliation.
* **memory `feedback_git_workflow.md`** — durable rule store;
  A49.5's pre-emption discipline becomes a memory entry once the
  addendum-protocol notice has been adopted in two consecutive
  audit bodies (W20 was the first; W21 is the second
  opportunity).

## A49.8 No code landing in this appendix

A49 is specification-only. The §A49.4 addendum template is prose
that the audit author paste-copies into `docs/audits/
AUDIT_PHASE_IND_TRACKS_W<N>_<DATE>.md` on observation of the
trigger condition (§A49.2). Re-audit trigger: if §A49.6's failure
mode is ever observed (a cross-lane commit's content lands inside
the audit commit's diff), this appendix is rewritten to specify a
code-side guard (candidate: a pre-commit hook scoped to
`docs/audits/AUDIT_PHASE_IND_TRACKS_*` that rejects any commit
whose `git diff --cached --name-only` includes paths outside the
ind-tracks ownership prefix per A46.2). The hook would close the
last loophole the W15D1 scoped-pathspec rule cannot reach
(authors who manually pathspec a non-ind-tracks file into the
audit commit by mistake).

### A49.8.1 Candidate pre-commit hook — per-stage skeleton (W22D3 / W21 R2)

Paste-ready skeleton for the §A49.8 candidate hook, kept pre-
implemented so that a §A49.6 failure-mode observation does not
force hook authorship under time pressure. The hook is **not
installed** until §A49.6 fires; the W15D1 scoped-pathspec rule
remains the load-bearing mitigation until then. The skeleton below
is prose-level pseudocode — field paths (especially the lane-prefix
regex) against A46.2 before deployment.

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit — audit-commit lane enforcement (A49.8.1).
# Purpose: reject an audit-commit whose staged diff spans more than
# one lane per A46.2.  Only fires when the commit touches a path
# matching the audit-commit recogniser (step 2); a non-audit commit
# short-circuits immediately.
set -euo pipefail

# (1) Snapshot the staged diff once.
staged="$(git diff --cached --name-only)"
[ -z "$staged" ] && exit 0

# (2) Audit-commit recogniser: at least one staged path under the
# ind-tracks audit prefix.  A commit that does NOT touch any audit
# file is out of scope for this hook and exits 0 immediately.
if ! printf '%s\n' "$staged" | grep -qE \
    '^docs/audits/AUDIT_PHASE_IND_TRACKS_W[0-9]+_.*\.md$'; then
    exit 0
fi

# (3) Ind-tracks ownership prefix (mirrors A46.2 verbatim).
ind_tracks_re='^(bass_py/(mio|workspace|src/common|tsc)/|'
ind_tracks_re+='docs/(dossier/A|INDEPENDENT_TRACKS_|'
ind_tracks_re+='audits/AUDIT_PHASE_IND_TRACKS_)|'
ind_tracks_re+='project/00_manuscript/ch(03|11|12)_)'

# (4) Any staged path outside the ind-tracks prefix fails the hook.
offenders="$(printf '%s\n' "$staged" | grep -vE "$ind_tracks_re" \
             || true)"
if [ -n "$offenders" ]; then
    printf 'A49.8.1: audit-commit blocked — non-ind-tracks paths '
    printf 'staged alongside AUDIT_PHASE_IND_TRACKS_*.md.\n'
    printf 'Offending paths:\n%s\n' "$offenders"
    printf 'Remediation: unstage the offenders (git restore '
    printf '--staged <path>) and re-issue the audit commit with a '
    printf 'scoped pathspec per W15D1.\n'
    exit 1
fi

exit 0
```

Per-stage responsibilities of the skeleton:

* **(a) shebang** — `#!/usr/bin/env bash` + `set -euo pipefail` so
  an unbound variable or failing subcommand aborts the hook
  rather than silently passing.
* **(b) staged-diff capture** — `git diff --cached --name-only`
  emits one staged path per line. Captured once; reused for
  recogniser + enforcement.
* **(c) audit-commit recogniser** — short-circuit on any commit
  not touching `docs/audits/AUDIT_PHASE_IND_TRACKS_W<N>_<DATE>.md`.
  Without this gate the hook would reject every non-audit commit
  that touches a bass or gallery path, which is the entire point
  of the two sibling lanes' daily work.
* **(d) ownership-prefix filter + exit-1 on offender** —
  `grep -vE` against the A46.2 prefix regex; any remaining line is
  an offender; nonempty set → exit 1 with an offender list and a
  remediation pointer to the W15D1 scoped-pathspec workflow. The
  regex mirrors A46.2's ind-tracks bullet verbatim (five prefix
  alternations); update this stanza when A46.2 is revised (A49.9
  bullet 2 — lane-ownership-prefixes-change re-audit trigger).
* **(e) installation note** — two delivery paths:
  * **Manual `.git/hooks/pre-commit`**: per-clone install;
    `chmod +x .git/hooks/pre-commit`; never tracked by git so
    each contributor opts in. Recommended for the first post-
    §A49.6 deployment (lowest-ceremony verification).
  * **`pre-commit` framework** (`.pre-commit-config.yaml` with a
    `repo: local` hook block). Tracked in the repo; runs on every
    contributor's clone once they `pre-commit install`. Preferred
    for steady-state deployment after the hook has survived ≥ 2
    audit cycles without false-positives (A49.9 candidate trigger
    for this promotion). False-positive risk: the recogniser in
    (2) is prefix-based; a future audit filename schema change
    (e.g. a W100+ overflow or a date-format rotation) would
    silently disable the hook until the regex is updated.

The skeleton is stable under A46.2 v1; a lane-ownership-prefix
change (A49.9 trigger #2) propagates into the `(3)` regex. The
hook does **not** replace the W15D1 scoped-pathspec rule — it is a
second line of defence that catches the specific A49.6 failure
shape (author manually pathspec'd a non-ind-tracks file into the
audit commit by mistake).

## A49.9 Re-audit triggers

A49 must be rewritten if any of the following happens:

* **§A49.6 failure mode is observed** (cross-lane file contained
  inside an audit commit's diff). Trigger fires immediately;
  rewrite scope is the §A49.8 candidate hook + the §A49.6
  responsibilities.
* **A46.2 lane-ownership prefixes change** (e.g. a fourth lane
  is created, or `docs/dossier/A*` is split between two
  ownership prefixes). §A49.4 / §A49.5 paste templates require
  field updates to reflect the new lane vocabulary; §A49.7
  cross-reference to A46 is updated.
  * **Co-edit target (W22 R2 / W23D3)**: §A49.8.1 stage-(d)
    `ind_tracks_re` regex **must** be updated in the same PR as
    the A46.2 prefix change — the regex mirrors A46.2's ind-
    tracks ownership-prefix list verbatim and silently disables
    the hook if it drifts. Closes W22 F1.
* **The addendum-protocol notice is dropped from two
  consecutive audit bodies**. §A49.5 was introduced because
  the discipline was load-bearing (W20 hedged the W19 → W20
  pattern); if the practice is abandoned, A49 must either
  re-justify the discipline or remove §A49.5 to reflect
  reality.
* **Memory `feedback_git_workflow.md` adds an "audit-commit-time
  status-gate" entry** (currently optional W19 F4 / W20 F4
  carry-forward). If the discipline is lifted into durable
  rules, §A49.3 / §A49.5 are updated to cite the memory entry
  rather than restate the rule.

Until one of these triggers fires, A49 is stable and its
addendum-protocol templates remain the authoritative format for
phase-boundary audit reconciliation.
