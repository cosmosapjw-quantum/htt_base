# Self-audit & docs-update automation

**Purpose**: pin the per-PR discipline that (a) self-triggers the
integrated audit template, (b) appends the PR's row to the
development log, (c) updates the forward plan, and (d) extends the
physics gallery — all in one commit stream, so the bundle's
consistency contract in [INDEX.md](INDEX.md) never has a moment of
drift.

**Parent**: [INDEX.md](INDEX.md).
**Upstream templates**: [docs/audits/AUDIT_PROMPT.md](../../audits/AUDIT_PROMPT.md).
**Hook**: [`.claude/hooks/check_phase_boundary_audit.py`](../../../.claude/hooks/check_phase_boundary_audit.py).

---

## 1. Scope

Every PR in the extended bundle fits into one of three shapes:

- **Rotation PR** — closes a sub-phase (e.g. `FB-8.2`); must run the
  full protocol of this document.
- **AUDIT PR** — lands as `AUDIT(<tag>): <short>` to fix a P0 / P1
  finding from the immediately preceding rotation PR. Must update
  the affected audit document's §7 "repair plan" ledger.
- **Carry-forward closure PR** — lands as
  `AUDIT(<tag>): close carry <ref>` when a previously-carried P2 /
  P3 item is addressed in its reserved session.

The protocol below is stated for rotation PRs; AUDIT PRs and
carry-forward PRs execute a reduced subset.

## 2. PR preflight — before writing any code

Complete these steps **in order**, in a single session:

1. **Load the audit template** at
   [docs/audits/AUDIT_PROMPT.md](../../audits/AUDIT_PROMPT.md) and
   read it as the system prompt for the session.
2. **Reconstruct the contract** for the surface the PR will touch.
   The reconstruction is the answer to the §0 "audit target
   reconstruction" table and goes into the top of the new audit
   document.
3. **Identify the invariant that must be preserved byte-for-byte**
   across the PR. (Example: for FB-3.2 it was "β=0 adapter-fed driver
   == FB-2.4 no-kwargs anchor on 12 labels".) Encode the invariant
   as a regression test before writing the new code.
4. **Plan the PR as three commits**:
   a. the implementation + tests + docs,
   b. the audit document,
   c. (if any P0/P1 surfaces) the `AUDIT(<tag>)` repair commit.
   Commits a and b *may* be combined when the audit finds zero P0/P1
   — confirm that by running the verifier filter before deciding.

## 3. PR audit template (mandatory)

Every rotation PR appends a new `AUDIT_PHASE_<tag>_<date>.md` (or a
"Supplement" section on the existing Phase file) with the following
sections. Copy the skeleton below verbatim and fill in every box.

```markdown
## §<tag>.0 Audit target reconstruction
| Layer | Claim | Implementation | Output |
|---|---|---|---|
| Physics | <equation + reference> | <file::symbol> | <scalar/tensor/array> |
| Invariant | <byte-identical invariant> | <short-circuit / guard / test> | <test name> |
| Routing | <which existing consumer this hooks into> | <unchanged / extended> | <regression test> |
| Overlap | <any overlapping module or convention> | <resolution> | <test name> |

## §<tag>.1 Contract / interface table
(shape, dtype, units, admissible-range for every new public surface)

## §<tag>.2 Phys-math audit ledger
(eight-point checklist from AUDIT_PROMPT.md STEP 2)

## §<tag>.3 Equation-to-code mapping audit

## §<tag>.4 Numerical / pipeline audit
(cancellation, conditioning, determinism, OOD risk)

## §<tag>.5 Ranked failure modes
| # | Type | Severity | Symptom | Root cause | Cheap probe | Misinterpretation |
|---|---|---|---|---|---|---|

## §<tag>.6 Verifier filter
| Verifier | Verdict | Evidence |
|---|---|---|
| A. Physics — known-limit recovery | Passed / Suspect / Failed | … |
| A. Physics — dimensional consistency | … | … |
| A. Physics — sign / normalisation | … | … |
| A. Physics — alternative explanation | … | … |
| B. Code — contract satisfaction | … | … |
| B. Code — actual code-path usage | … | … |
| B. Code — regression risk | … | … |
| B. Code — reproducibility | … | … |
| C. Numerical — tolerance robustness | … | … |
| C. Numerical — convergence / stability | … | … |
| C. Numerical — baseline reproducibility | … | … |

## §<tag>.7 Minimal repair plan
(if all verifiers pass: "No P0 / P1 detected"; else the smallest
patch that closes each non-passing verifier)

## §<tag>.8 Minimal test set (executed)
| Test | Role | Verdict |

## §<tag>.9 Final verdict
- **Status**: Pass / Fail / Partial
- **Implement now**: …
- **Do NOT touch**: <deferred items with their reserved session>
- **Gallery status**: regenerated / no-op / deferred
- **Baseline movement**: <N_before> → <N_after> (<± delta> tests)
- **Carry-forward ledger**: …
```

## 4. Docs-update checklist (mandatory)

Before the rotation PR is allowed to commit, confirm every row:

- [ ] **DEVELOPMENT_LOG** ([DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)
      if tag ≤ FB-7, or the successor `DEVELOPMENT_LOG_FB8_ONWARD.md`
      once FB-7 closes) receives a new row.
- [ ] **Forward plan** ([EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md))
      has the matching PR row annotated with `✅ shipped @ <hash>`
      (or `⚠ descope — <reason>`).
- [ ] **NEXT_SESSION_PROMPT.md** §2 rotated to the next sub-phase.
- [ ] **Audit document** committed under `docs/audits/`.
- [ ] **Gallery**: either a new PNG batch committed under
      `figures/physics_gallery/` with `README.md` updated, or an
      explicit no-op justification in the audit's §9.
- [ ] **Bundle index** ([INDEX.md](INDEX.md)) updated only if the PR
      changes the bundle's navigation surface (new doc, renamed doc,
      deleted doc). Most PRs will not touch it.
- [ ] **00_conventions cross-reference table**
      ([../00_conventions.md §2](../00_conventions.md)) updated if
      the PR adds a new consumer of a conventional default
      (e.g. `V_HAT_E_DEFAULT`).
- [ ] **Carry-forward ledger** — every P2 / P3 item added this PR has
      a named reserved session; every P2 / P3 closed this PR is
      struck in both the current audit's §9 and in the audit where
      it was first raised.

## 5. Hook wiring (belt-and-suspenders)

The `.claude/hooks/check_phase_boundary_audit.py` hook fires on every
`git commit` Bash invocation and injects an `additionalContext`
reminder when the commit message matches a phase-boundary pattern
and the last five commits contain no `AUDIT(…)` entry.

**Hook coverage matrix** (update when a new tag range lands):

| Pattern | Matches | Hook action |
|---|---|---|
| `git commit.*LB-\d+:` | LB-0 … LB-6 | inject audit reminder |
| `git commit.*Phase LB complete` | LB exit | inject audit reminder |
| `git commit.*rotate NEXT_SESSION_PROMPT` | any rotation | inject audit reminder |
| `git commit.*FB-\d+(\.\d+)?:` | FB-0.1 … FB-11.N (post-discard of FB-10 / FB-12 / FB-13 per [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md)) | inject audit reminder (extension landed in bundle bootstrap PR — see §6 below) |

The hook is advisory; the load-bearing rule is the user's feedback
memory that was transcribed to
[PROJECT_MEMORY_EXPLICIT.md §4](PROJECT_MEMORY_EXPLICIT.md). The
hook exists to catch the case where the assistant forgets to
self-trigger.

## 6. Hook extension for the FB-N range

The default pattern list in the hook covers `LB-\d+:` only. The
bundle bootstrap PR (`FB-BOOTSTRAP`; see
[EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §1](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md))
adds `FB-\d+(\.\d+)?:` and `FB-BOOTSTRAP:` to
`PHASE_COMMIT_PATTERNS` in
[`.claude/hooks/check_phase_boundary_audit.py`](../../../.claude/hooks/check_phase_boundary_audit.py)
so that every FB commit also triggers the advisory reminder.

**Shipped state** (as of the bundle commit): the two new patterns
are already present in `PHASE_COMMIT_PATTERNS`. A future sub-phase
that needs a different message prefix (`post-extended`, for example)
appends a new pattern with the same shape — one regex per line,
anchored to `git\s+commit.*` at the left and a capturing tag at the
right.

## 7. Gallery automation template

When a new physical quantity lands, add a new plotter to
[scripts/make_physics_gallery.py](../../../scripts/make_physics_gallery.py)
following the existing structure (one function per figure, returning
a matplotlib Figure). The function must:

- **Accept a keyword-only `output_dir: Path`** for the target
  directory (typically `figures/physics_gallery/<topic>/`).
- **Pin the RNG seed** if any stochasticity is involved.
- **Call `savefig(..., bbox_inches='tight', dpi=180)`**.
- **Return the saved path** so the driver can record it.

After adding, regenerate:

```bash
../venv/bin/python scripts/make_physics_gallery.py
```

Visually inspect the new PNG(s). If a plot fails sanity inspection
(wrong units, wrong sign, misleading colour scale), fix the issue
before committing; do *not* commit a broken plot to address in a
follow-up.

Update `figures/physics_gallery/README.md` with the new entry.

## 8. Carry-forward ledger discipline

Every P2 / P3 item raised in §5 of an audit document must:

1. Carry a **reserved session tag** (e.g. "FB-5.1", "post-FB
   devops").
2. Have a matching row in the forward plan
   ([EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md))
   or in the parent [FULL_BIANCHI_COVERAGE_PLAN.md §2 / §10](../FULL_BIANCHI_COVERAGE_PLAN.md).
3. Be closed by an `AUDIT(<tag>): close carry <ref>` commit when the
   reserved session executes. That commit updates both (a) the
   original audit's §5 / §9 to strike the item and (b) the closing
   audit's §9 carry-forward ledger to note the closure.

No P2 / P3 item is allowed to live in "tribal knowledge" — if it is
not in the audit ledger with a reserved session tag, it is not
carried. New collaborators are expected to rely on the ledger as the
single source of truth for what is still owed.

## 9. Self-check — before declaring a rotation complete

Run through this nine-point checklist immediately before the final
commit:

1. All new / modified public surfaces have updated docstrings with
   citations (every citation traceable to a file path or literature
   reference).
2. Every new test uses either `np.array_equal` for byte-identity
   claims, `rtol=0 atol=0` for closed-form claims, or an explicit
   tolerance argument with a comment justifying the chosen value.
3. No new silent fallback. Every `None` default is either documented
   as preserving a byte-identical regression anchor or raises a
   `ValueError`/`NotImplementedError` before the code reaches a
   numerically unsafe path.
4. Byte-identical anchor verified against the named commit hash
   (e.g. `d7d25da` for the FB-2.4 anchor, `fdb1d86` for the FB-3.2
   anchor).
5. Full regression green (`bass/ tsc/` pytest suite).
6. Audit document written; verifier filter unanimously passing.
7. `NEXT_SESSION_PROMPT.md §2` rotated to the successor tag with an
   archived `<details>` block preserving the current prompt.
8. Gallery regenerated or justified-no-op in the audit.
9. Docs-update checklist in §4 unanimously ticked.

Only then create the rotation commit.
