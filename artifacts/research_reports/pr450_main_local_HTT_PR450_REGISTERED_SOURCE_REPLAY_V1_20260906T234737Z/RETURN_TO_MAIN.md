# PR450 return to MAIN

**NONPASS_PROTECTED_SEED_PARENT_IDENTITY_MISMATCH.** The original full two-file suite collected 14 nodes and executed once: 13 passed, 1 failed. No generated source surface or workflow PASS receipt exists. MAIN review is pending.

The failing original node is `tests/contracts/test_theory_survivor_triage.py::test_repository_source_id_seed_has_37_unique_rows_and_pr284_deferred`. Its expected parent is `PILLAR_S:II-3.2`; the pinned seed records `PILLAR_S:I-3.2`. The complete PR405 Git object records `PILLAR_S:II-3.2`. Both parent IDs exist in that matrix as distinct source rows. The protected seed and original assertions were preserved. See `source-identity-diagnosis.json`, `baseline-tests.stdout`, and `pr450-tests.xml`.

Execution source: `ba84912bea165896ec8f0c0e5793b47d1736f512`, tree `55065b3b9ff075f8a58a5bda5f3d11d85ba21ab5`. All seven requested file blobs matched, both required ancestry relations passed, and worktree status was empty before and after validation. `source-before.json` and `source-after.json` contain complete file identities. The original user checkout status was preserved. Fresh PR and local worktree/ref inspection found no matching completed replay or competing task writer. The missing exact baseline was fetched normally; no branch owned by another actor was changed.

Source matrix: commit `463f0999949bf8534c60ad7973b7342705c2e3d6`, blob `56af1713ef8c4718598e10012819d5ab62c6e37a`, measured SHA-256 `8d92325a72b83dd96d1b78df071c47687426bfe1d10bfbe6768a3ab6f9bb244a`, 292456 bytes. The complete Git-read payload is `before-matrix.stdout`; acquisition alone is not extractor execution. The inherited universe has 152 broad rows plus 5 scoped candidates (157), with source terminal counts PROMOTED=36, REFUTED=1, UNRESOLVED=107, DEFERRED=2, NOT_ATTEMPTED=11. These inherited source dispositions are neither the selected 37-row surface nor 157 new mathematical verdicts. Fixture counts were not substituted.

| Operation | Actual result |
|---|---|
| WU-001 DAG mirrors `--check` | PASS; no mirrors changed |
| Extractor py_compile | PASS |
| Full two-file collection | PASS, 14 original nodes |
| Full two-file execution | FAIL, 13 PASS / 1 FAIL, 0 skipped or deselected |
| Actual PR405 CLI replays | NOT_RUN, 0 invocations; required suite failed |
| Byte comparison and original workflow receipt block | NOT_RUN |
| Source diff and diff check | Empty / PASS |

Runtime: CPython 3.12.3 at `/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python` (real executable `/usr/bin/python3.12`), pytest 8.4.2. Exact import paths are in `tested-runtime-import.stdout`. The initial user-site pytest failed because pygments was absent; a nonexistent sharedVenv locator failed before process start. Those environment failures were retained, then an existing compatible environment was used without package installation. Pytest configuration, original node selection, assertions and import behavior were retained; only Python bytecode and pytest caches were redirected outside source.

Validation command time consumed: 3.254192 seconds of 900 seconds; no timeout. Preparation/publication are not replay invocations. Each recorded command has argv, cwd, stdout, stderr, exit/timeout and timing. The nonexistent-interpreter launch has no process exit or measurable process time; its record explicitly identifies that logger limitation. Preliminary interactive inspection was not an execution receipt.

No source repair was attempted: the next edit would alter a protected source-parent relationship or weaken an original assertion. This assignment requires a durable NONPASS at that boundary. No unchanged failed suite was repeated. The PR284 mathematical conflict remains unresolved. No generated content_id, surface digest, replay equality, generated coverage or source.mode is claimed; their fields are null. The registered expectation remains 24 exact/conditional broad + 8 synthetic broad + 5 scoped, with 36 INCLUDED and PR284 child DEFERRED. Semantic links and historical statement identities were not changed or re-proved.

Self-review checked raw suite/JUnit/node agreement, exact pins, source diff, failure classification, budget, absent generated artifacts and publication scope. Review is local self-review, not a blind independent review. The scientific validation, claim firewall/provenance and handoff skills were applied to this noncanonical result pack. The explicit task publication permission governs this own Draft PR; no merge or ready transition is authorized. Canonical claims remain 30 and Report-A candidate claims remain 40; truth, novelty, observational and scientific release authority are unassigned. Prior K5/K2/R2/PR455/PR451 results were not rerun.

**Next consuming decision:** MAIN reads the failure and exact seed/matrix parent identity and decides whether to authorize a specific protected seed correction under a separately scoped continuation. No automatic next work unit follows.

Git publication commit/tree and immutable return links are reported after push, avoiding self-hash commit cycles. Hosted CI is observed separately from this local failure.

Publication review: staged `git diff --check` returned 2 solely for preserved raw pytest/JUnit trailing whitespace and the original worktree-list final blank line. These raw bytes are retained as requested. The source-only diff check passed. The artifacts directory is ignored by default, so only this explicitly authorized result directory was added with `git add -f`. The bounded contract check passed with STOP_INVALID and zero applicable protected-source repair allowance; this is a source-authority stop, not resource exhaustion.
