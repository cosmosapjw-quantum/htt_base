# PR451 native decoder return to MAIN

**EXACT_SOURCE_DECODER_TESTS_PASS_PENDING_MAIN_REVIEW — 28 collected, 28 executed, 28 PASS.**

This publishes the completed native run `HTT_PR451_EXACT_SOURCE_DECODER_VALIDATION_V1_20260906T085720Z`. The new handoff explicitly requires reuse of a fully matching prior baseline. Its 59 archived evidence checksums, eight registered source/configuration identities, raw collection and JUnit were checked before publication. No source defect was found, no repair was needed, and no additional native test run was performed. Baseline and final refer to the same passing run and are counted once.

## Read the actual return

- [Current machine-readable receipt](pr451_result.json)
- [Original native execution receipt](native_run/EXECUTION_RECEIPT.json), with cwd, argv, PID, timing, timeout and exits
- [Full suite stdout](native_run/suite.stdout), [stderr](native_run/suite.stderr), [exit](native_run/suite.exit), [JUnit](native_run/pr451-decoder.xml)
- [Collection stdout](native_run/collection.stdout), [stderr](native_run/collection.stderr), [exit](native_run/collection.exit), [executed node IDs](native_run/executed-node-ids.txt), [all node outcomes](native_run/NODE_RESULTS.json)
- [Syntax command](native_run/syntax.command.json), [stdout](native_run/syntax.stdout), [stderr](native_run/syntax.stderr), [exit](native_run/syntax.exit)
- [Native runtime and actual module import paths](native_run/runtime-manifest.json), [NumPy/BLAS configuration](native_run/numpy_show_config.txt), [thread settings](native_run/execution-environment.json)
- [Source before](native_run/source-manifest.before.json), [source after](native_run/source-manifest.after.json), [current reuse verification](reuse-verification.json)
- [Original expected-exception accounting](native_run/EXPECTED_EXCEPTION_ACCOUNTING.json), [historical provenance grades](native_run/HISTORICAL_PROVENANCE.json)
- [Executor delivery self-review](DELIVERY_REVIEW.md), [copied original byte identities](copied-evidence-identities.json), [all payload SHA-256 values](SHA256SUMS)

## Source and delivery identities

Executed commit: `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`.
Executed tree: `6f2fdfd5b8fbf5e4ee3579288fb5aa3da1bb1060`.

The [controlling handoff](PR451_MAIN_LOCAL_GIT_HANDOFF_20260906.md) is from coordination commit `af5d79ad572211247bd78ec4c1667f02b62bc087`, blob `b2b270a636ebc087142810524c9e16d3f0252b1f`. It is separate from the tested source. PR #451's head still matched the fixed baseline at intake. The existing isolated native worktree was reused on `validation/pr451-main-local-git-return-20260906-r1`.

**Changed production source/tests/workflows: zero.** This branch adds only this evidence directory. Existing tracked source, historical receipts, tolerances, rcond, conditioning domain, normalization, signed orientation, O:Q consistency, trilinear/STF checks and complete forward replay remain byte-identical. No patches or additional regressions were necessary. The publication commit adds text evidence; it has not been represented as a newly tested execution commit. Codex returns its final commit/tree and authenticated readback coverage after push, without a self-hash commit cycle.

## What the PASS establishes and its limits

The native run used CPython 3.12.3, NumPy 2.4.6 and pytest 8.4.2, with float64 and recorded OpenBLAS configuration. NumPy and pytest are unpinned in the workflow. Both unchanged test loaders resolved their decoder module to the pinned checkout in a separate native import probe. The fresh suite executed all 28 collected nodes, with no failures, errors, skips, xfail, xpass, deselection or timeouts. This is local numerical test evidence.

The forged-image regression passed its unchanged `O:Q vector disagrees` exception-message check. Both stable-forward tests passed their existing **replay OR typed chart-unavailable** contract. Their successful-replay/unavailable branch counts were not recorded and remain unavailable; passing them is not universal successful inversion. `OrbitChartUnavailable` is an `OrbitInputError` subclass and must be accounted for first when exact exception types are observed.

Inherited thread settings were recorded without tuning. The dynamic BLAS worker count was not observed (the optional threadpoolctl package was absent); the build's MAX_THREADS value is not a measured worker count. No cross-BLAS last-bit identity or uniform stability guarantee follows from this run.

The old source-equivalent 28-test/10,000-pair record remains `LOCAL_SOURCE_EQUIVALENT`; the old SymPy exact Gram/trace/symmetry/rank check remains historical exact arithmetic. Neither historical block was executed again or relabelled. The native JUnit here is separate actual exact-source execution evidence.

During branch creation an auxiliary shared-Lean post-checkout hook emitted a nonblocking cache-link warning ([original stderr](branch-create.stderr)). Git switch exited 0; a read-only query found the Cli checkout at its own revision ([output](auxiliary-hook-diagnostic.stdout)). No Lean build or repair was required or run for this Python-only delivery. This warning is separate from the completed decoder validation.

## Next minimum action

MAIN can review these readable Git files and the evidence-only delta directly at the immutable publication commit. This is the executor's result-informed self-review, with no claimed independent or blind approval. No intermediary WORK_THREAD or ZIP transfer is required. Local PASS does not assert hosted CI PASS. Canonical remains 30 and candidate remains 40; merge, ready transition, scientific/publication promotion and other reserved work units are not performed.
