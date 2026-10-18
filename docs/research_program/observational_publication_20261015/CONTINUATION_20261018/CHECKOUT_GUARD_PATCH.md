# Explicit continuation-ref correction

Requested by parent after the L01 native handoff exposed an actual blocker.
The original guard exposed `--expected-ref` but rejected every value except the
historical #559 origin branch. Its failure message also recommended a new
worktree, contrary to current primary-checkout policy.

Integrated replacement files, relative to the real repository root:

1. `docs/research_program/observational_publication_20261015/L01_R10_C10_RUNTIME_RECOVERY_20261017/scripts/l01_checkout_guard.py`
2. `docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017/tests/test_l01_repo_checkout_guard.py`
3. `docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017/tests/test_l01_checkout_guard_continuation.py`

Original source blob: `ed1c466522cac5537b958fa07137c2685b2407f5`.
Original existing pytest test blob: `462a4daf2a3e2fd7c1d7589bf08b221d266d2c95`.
Both were read at `967ef7c8f0b132ecaaba343045d333d4ebf299c1`.
The original versions remain resolvable by the pinned Git blobs above; they are not replacement files.

The `check_checkout(root, expected_ref=EXPECTED_REF, *, smoke=True)` API and
default ref remain unchanged. A caller may now explicitly select an authorized
`origin/<branch>` (including `origin/main` after an authorized integration).
Git validates the ref format. Revision expressions, implicit HEAD aliases and
non-origin refs are rejected. Resolution uses the full `refs/remotes/...` name,
so a same-named local tag cannot shadow a stale remote branch. There is no
fallback to HEAD or the current branch when the selected ref is missing.

All existing exact-HEAD, clean checkout, top-level identity, required-file and
CLI-import checks remain. Git dubious-ownership errors remain blocking; no
`safe.directory`, ownership, trust, branch, fetch or installation mutation is
performed. The new failure guidance says to preserve user edits and prepare the
existing primary checkout. Selection of a CLI ref records the caller's explicit
task choice; it does not assert that a branch is scientifically validated.

Caller inspection covered the original guard itself, its six existing pytest
tests, the `R10_C10_SCIENCE_AND_REPO_HANDOFF_KO.md`/`STAGE_DAG_PROGRESS.json`
references, and `MATCHED_SPLIT_STREAM_KO.md` (CLI call using the default). The
existing pytest test expecting all alternate refs to fail was updated; the other
five tests are preserved. This was targeted caller inspection, not a claimed
whole-repository call-graph search.

The eight new standard-library unittests initially produced six failures, one
error and one pass against the exact old guard. In particular, a clean correct
explicit continuation fixture was rejected with `UNEXPECTED_BRANCH_REF` before
any other contract was evaluated. After the patch: **8/8 passed in 0.319 s**.
They cover default/explicit branch success, actual CLI + import-smoke execution,
stale branch/tag-shadow rejection, dirty-file preservation, invalid ref syntax,
missing refs, top-level/committed-missing-file rejection, and propagation of Git
trust failure. Fixtures are tiny disposable repositories, not copies/worktrees
of the project. No owner checkout was accessed or modified.

Run from the repository root:

```bash
python -m unittest discover -s docs/research_program/observational_publication_20261015/L01_R8_C8_TWO_MASK_STABILITY_20261017/tests -p test_l01_checkout_guard_continuation.py -v
```

The old pytest suite was source-inspected and its contradictory expectation
updated, but not run here because pytest and the complete native predecessor
tree are unavailable. Scoped independent review is recorded in INDEPENDENT_REVIEW.md. Primary-checkout execution remains NOT_RUN. The native helper now takes an explicit continuation ref and retains
the guard before tests/data computation.
