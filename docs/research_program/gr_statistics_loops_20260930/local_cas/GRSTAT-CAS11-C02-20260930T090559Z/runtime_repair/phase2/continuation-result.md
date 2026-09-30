# Same registered author continuation — source closeout

Implemented and tested the missing direct-author continuation path. No live
installation, continuation, scientific execution or admission was performed.

**Cause:** FOLLOWUP_TOOLS required a workspace reservation even for already-bound
direct authors with matched completed runtime and `continuation_context=null`.
The dirty review-closeout branch only covered reviewers. The new author branch
uses the existing parent/launch/child/task/profile binding and actual terminal
runtime metadata, with no fake workspace job, replacement identity or reregistration.

**Total owned delta relative to the supplied source-baseline.json:**

- `src/cuhg/codex_hooks/global_dispatch.py`: prior event-local child fix retained;
  direct-author followup branch added, including child followup rejection.
- `src/cuhg/codex_hooks/direct_author_continuation.py`: new consumption, inspection
  and metadata-only return accounting helper.
- `tests/unit/test_registered_child_author_routing.py`: prior four tests retained.
- `tests/unit/test_direct_author_continuation.py`: eleven continuation tests added.

`repair-total.diff` contains this total delta. Preexisting review closeout code,
scripts and installer changes remain unchanged. The new branch precedes the
review/workspace alternatives; their existing implementations remain intact.
Source preimage checks found no concurrent changes on owned hunks. Other ongoing
RAM/fleet edits were not touched.

**Semantics:** A real parent followup atomically appends a
`CONSUMED_OUTCOME_UNKNOWN` record under `direct_author_continuations`. Another
followup cannot consume the same invocation or ended turn, including concurrent
calls. A new terminal transcript turn and matching normal lifecycle exit are
required to close it. No model setting is selected or changed. Author role comes
from the registered worker profile; review and workspace paths retain their limits.
Wrong parent/child/task-role metadata, mismatched settings, unfinished/unobserved
runtime, decreasing usage and existing source/validator violations are rejected.
Existing source/validator checks are reused, with no new transcript, prompt,
candidate or launch-record hash gate. Cosmetic transcript changes are accepted.

Prior cumulative tokens and failures remain charged. Read-only observation of the
actual three transcripts returned 570,219 / 600,021 / 346,319 cumulative tokens for
Wolfram / SymPy / Sage. Monetary cost remains **NOT_MEASURED**. Missing counters
and deltas remain NOT_MEASURED, never zero. Current continuous policy has an
adaptive 100,000-token soft target and no explicit hard limit; no implicit old
workspace cap is imported. Applicable explicit token caps aggregate the same
registered task's observed threads and remain binding even if a later default
removes the cap. This is a pre-dispatch accounting check, not mid-turn quota
enforcement. Original launches and exits are not rewritten by the helper.

**Actual validation:**

- Before: one reproduced `CHILD_CONTINUATION_NOT_RESERVED` failure in
  `continuation-before-regression.log`.
- After: **107 passed, 98 subtests passed** in `continuation-after-tests.log`:
  direct author, prior child-author routing, parent routing, global dispatch,
  lifecycle, direct reviewer closeout and reviewer successor suites.
- The cap-persistence counterexample failed during development and was fixed;
  its original output remains in `continuation-intermediate-tests.log`.
- Standalone overlay subprocess fixture passed against unchanged immutable
  dependencies: first followup allowed, duplicate denied, original launch preserved.
- `git diff --check` passed. No harness review loop or child was invoked.

**Activation artifact and positive path:** `author-continuation-runtime/` contains
only the repaired handler/helper and excludes unrelated dirty reviewer changes.
`runtime-author-continuation.patch` is the corresponding isolated runtime patch.
See `continuation-activation.md` for the exact handler command and an exact native
followup of existing Wolfram child `01a0f192-3705-7bd2-a9db-240f78953765`; no new
reservation or task registration is required once the original parent loads it.

**External limit:** the existing parent still calls its cached old handler, and
no live reload tool is exposed. Staging is not activation. The same parent client
must load the corrected PreToolUse command and retain its existing child handles;
this was not verified here. No immutable bundle, descriptor, hooks.json or trust
was changed. There is no authorization gap in this source repair.

The live lifecycle hash changed externally while other work was active. Direct
comparison with the earlier snapshot confirms all three completed author records
and C04 unchanged; no live `direct_author_continuations` ledger exists. Lean is
now bound compared with the original snapshot and was not edited or dispatched
by this repair. HTT files, mathematical candidates, Host derivations and proof
results were not inspected or changed. All outcomes remain non-admission.
