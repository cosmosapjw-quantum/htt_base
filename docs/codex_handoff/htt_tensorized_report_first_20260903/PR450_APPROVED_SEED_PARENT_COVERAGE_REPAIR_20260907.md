# PR450 — approved seed-parent amendment, coverage-reader repair and real-object replay

Date: 2026-09-07
Work unit: HTT_PR450_REGISTERED_SOURCE_REPLAY_V1
Continuation: APPROVED_SEED_PARENT_AND_COVERAGE_REPAIR_R1
Status: OWNER_APPROVED_EXECUTION_HANDOFF; NOT_A_REPAIR_OR_PASS_RECEIPT

## 1. Owner decision and immediate action

After MAIN identified the protected parent-reference mismatch and the real-matrix coverage nesting mismatch, the owner explicitly approved continuation: "승인할게. 이어서 진행해줘."

That approval authorises the single protected seed-parent correction specified below. Combine it with the already permitted ordinary extractor/fixture/regression repair and finish the existing real-object replay. Do not stop to request the same seed approval again. Do not manufacture a new governance gate, audit-only loop, scientific claim or separate WORK_THREAD.

This instruction amends Sections 2 and 5 of the prior PR450 handoff at commit `111fa431924c4bf55e608826912dfef2e765fffa`, path `docs/codex_handoff/htt_tensorized_report_first_20260903/PR450_MAIN_LOCAL_GIT_REPLAY_HANDOFF_20260907.md`, blob `db0322f674b5cef75d4a250cec4d6a22e4b9c181`. The original failed run remains immutable. Its seed prohibition is lifted ONLY for the named value; other protected inputs and scientific limits remain unchanged. The previous "await owner amendment" next action in PR457 is now superseded.

MAIN prepares the source-grounded repair contract and reviews the returned bytes here. LOCAL_CODEX is the sole implementation/ref writer during this delegated correction, runs native validation, fixes demonstrated in-scope defects, and publishes the result directly to Git. No approval-only work-thread relay is required. The owner's explicit task-level Git publication permission governs this isolated task despite older generic no-agent-publication text in the pinned AGENTS; do not rewrite AGENTS or bypass credential/security controls.

## 2. Baseline, evidence and source authority

Repository: `cosmosapjw-quantum/htt_base`.

Use a new isolated child of the published failure evidence so the original failed source and logs remain directly available:

```yaml
original_failed_source: ba84912bea165896ec8f0c0e5793b47d1736f512
original_failed_tree: 55065b3b9ff075f8a58a5bda5f3d11d85ba21ab5
continuation_base: bf09ba531b3afde184ded85c7e147839bf572c85
continuation_base_tree: 116bd8461edf33ae5d83698ca91e790e5c9bae49
failure_evidence_pr: 457
suggested_new_branch: repair/pr450-seed-parent-coverage-basis-20260907-r1
draft_pr_target: validation/pr450-main-local-source-replay-20260907-r1
```

The continuation base adds evidence only to the failed source. It is not the report-branch commit carrying this handoff. Preserve the original PR450 and PR457 refs. Inspect current remote/local worktrees and same-task results first; reuse an already matching correction or active sole writer, do not compete with it or overwrite its branch. A matching unpushed task is discoverable only locally. A source change requires its own actual candidate identity, not a claim to retain the baseline tree.

Original failure evidence prefix at the continuation base:
`artifacts/research_reports/pr450_main_local_HTT_PR450_REGISTERED_SOURCE_REPLAY_V1_20260906T234737Z/`.
Read `RETURN_TO_MAIN.md`, `pr450_result.json`, `source-identity-diagnosis.json`, `baseline-tests.stdout`, `pr450-tests.xml`, and before/after source manifests. Reuse the verified 14-node result (13 PASS/1 FAIL) as the seed RED baseline; do not rerun the full unchanged failed suite merely to obtain the same RED.

Frozen matrix authority:

```yaml
matrix_commit: 463f0999949bf8534c60ad7973b7342705c2e3d6
matrix_path: docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json
matrix_git_blob: 56af1713ef8c4718598e10012819d5ab62c6e37a
previously_measured_sha256: 8d92325a72b83dd96d1b78df071c47687426bfe1d10bfbe6768a3ab6f9bb244a
```

Acquire/reuse the complete real Git object, not manually retyped excerpts or a synthetic Git history. The supplied object contains 152 broad rows plus 5 scoped candidates. That 157-row source universe is distinct from the selected 37-row output and the Report-A forty claims.

Protected/source baseline files:

| Path | Original Git blob |
|---|---|
| `docs/research_program/theory_promotion/closeout/REGISTERED_SURVIVOR_SEED.json` | `76d0a2396c2cb7e0b514264fe6322a2316adfa69` |
| `scripts/extract_theory_survivor_surface.py` | `9d5bee9b1926e35216b95ab1384dc28f7a25592f` |
| `tests/contracts/test_theory_survivor_triage.py` | `26ab6150de552bd7d083cdb0118b1d251bcf17fd` |
| `tests/contracts/test_theory_survivor_seed_schema.py` (unchanged) | `dd31c5e9f5d2e8348a6c8405de04a5b8685594fa` |
| `.github/workflows/theory-survivor-triage.yml` (unchanged) | `c0a165c1d150c522b946e47c253f41ab53090b09` |

Read AGENTS.md, the applicable scientific-code/claim/provenance rules and the original WU-001 at the real checkout. This is a continuation of that source-extraction objective, not permission to update unrelated DAG entries or old receipts.

## 3. Exact approved seed change

In `REGISTERED_SURVIVOR_SEED.json`, uniquely select the row whose `candidate_id` is `PR284_NEW:FINITE-REGISTERED-PATH`. Change only:

```diff
-      "parent_candidate_id": "PILLAR_S:I-3.2",
+      "parent_candidate_id": "PILLAR_S:II-3.2",
```

The frozen matrix's same scoped-child row declares `source_candidate_id: PILLAR_S:II-3.2`. The two broad IDs are different statements, not spelling variants: I-3.2 concerns a comparator-sign constraint, II-3.2 the reverse-martingale/Doob mask-ladder source. The declared child relationship, not title similarity, is the correction authority.

Preserve every other seed field and byte. A targeted byte edit must increase length by one; reversing the one insertion must recover the exact old seed blob. Independently compare parsed structures with that one field restored. Avoid JSON reserialization of the entire file, global search/replace, or changing other occurrences of I-3.2.

Preserve the child ID, kind, DEFERRED disposition, all other 36 rows, source references, counts, and historical registry-check block. The seed's `wolfram_registry_check` is an inherited record of its own original disposition object, not a new CAS run or proof of the repaired whole seed; identify that limitation in the return receipt rather than editing or silently extending the old evidence. Measure the new seed blob/SHA-256 explicitly.

Do not modify the frozen matrix or its scoped-child statement, statement hash, UNRESOLVED/NOT_ELIGIBLE_CAS_CONFLICT status, evidence references or observed-data flag. No PR284 CAS conflict, Doob theorem or comparator-sign theorem is adjudicated by this amendment.

## 4. Coverage-reader correction: explicit real layout and legacy compatibility

The actual matrix stores the two declared counts at:

```text
candidate_coverage_proof.coverage_basis.supplemental_scoped_candidates_expected
candidate_coverage_proof.coverage_basis.supplemental_scoped_candidates_classified
```

The current extractor reads them directly under `candidate_coverage_proof`; the old synthetic `matrix()` fixture uses that direct layout. That discrepancy was source-reviewed, not yet an observed production CLI failure. Preserve that evidence distinction.

Implement the smallest local reader change in the existing extractor, using the existing `SurvivorTriageError`, `_mapping` and `_integer` rules. Keep the original fixture and all original test functions/assertions intact; add focused cases in the same triage test file.

The selected compatibility policy is deliberately explicit:

1. If `coverage_basis` is present, require a mapping containing BOTH valid counts there. Present-but-null, malformed, empty, missing or invalid nested counts are failures, even when valid flat aliases also exist. No fallback from invalid nested data.
2. If either flat alias also appears alongside a valid nested declaration, require BOTH flat counts, validate their types and require exact agreement with the nested pair. Conflicting or partial duplicate declarations fail closed. Consistent duplicates are permitted.
3. Only if `coverage_basis` is absent may the existing complete, valid flat pair be used as the supported legacy layout. Missing/partial/invalid pairs fail. This preserves original positive fixture behavior rather than rewriting its tests to a new oracle.
4. Keep `coverage_complete` at the original enclosing level and preserve its existing check. Preserve the existing comparison of source-declared expected/classified counts with the actual scoped-row length. Do not hard-code 5, infer missing declarations from length, coerce strings/floats/bools to integers, or normalise an invalid count into zero.
5. Do not mutate the input matrix in place. Layout normalisation selects/validates the two declarations only; it does not reclassify rows, change selection, drop semantic relations or change canonical output serialization/content-id semantics.

A small internal helper returning the checked pair is sufficient; no new parser framework or public schema is required. This policy is an implementation specification, not a claimed tested patch.

## 5. RED/GREEN coverage and productive correction

Normal authored-source changes are exactly the seed, the extractor and `tests/contracts/test_theory_survivor_triage.py`. Keep the seed-schema test file, workflow, pytest config and unrelated source unchanged. New text execution evidence is published separately.

Before editing the reader, add a focused case that moves the original fixture's two counts into `coverage_basis` and requires the same surface as the original flat fixture. Execute it against the unchanged reader and preserve the actual failure. That real-layout RED is separate from the already archived seed-parent RED. Do not fabricate a CLI failure or add it to the old 13/1 result.

Use parameterized regression cases as appropriate, measuring their real node IDs and totals rather than prescribing a cosmetic test count. Cover at least:

- nested real layout and flat legacy layout produce identical source-normalized outputs;
- consistent duplicated declarations pass, conflicts and partial duplicates fail;
- malformed/present nested data cannot be rescued by valid flat aliases;
- expected/classified mismatch and matching-but-wrong counts fail against actual row count;
- missing fields, nulls, bools, strings, fractional numbers and negative counts fail with the existing typed error;
- input objects are unchanged after processing;
- the original protected-parent test passes after the one-field seed change, without altering its expected II-3.2 assertion.

Preserve all original fourteen nodes, their assertions and selection. Do not change expected counts, lower identity checks, skip/xfail/deselect failures, fabricate a source.mode, or alter truth/novelty/release flags.

Continue evidence-driven edit -> targeted test -> diagnose -> edit as needed within these invariants. One bounded repair episode is not one edit or one test invocation. Fix ordinary directly related implementation/fixture/invocation/packaging defects autonomously; do not return just because another in-scope correction is needed. If a different protected input, mathematical meaning, unowned active writer, privilege/destructive operation, unrelated harness policy or reserved work unit must change, preserve the actual result and return that precise boundary.

## 6. Actual execution and real Git-object double replay

Use the existing successful CPython 3.12 environment if still available. The previous runtime was CPython 3.12.3 / pytest 8.4.2 / PyYAML 6.0.3 at `/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python`; verify it rather than assuming availability. The workflow does not impose a pytest/PyYAML patch-version lock. Do not reinstall a general mathematics stack or revisit the earlier failed interpreter locators.

Use a clean isolated worktree of the continuation base and a unique external run directory. Preserve the original user checkout, dirty files, venv, data and the complete PR457 failure evidence. Do not reset/clean/stash unrelated work or use a partial/promisor clone. Keep caches outside authored source. Verify the existing WU-001 ancestor relations to `2dce66ca019609e6d07625bc6382bc347fbf5a8c` and `bdad91a204c424030cd6d0e562232b6965a42900`, reusing authenticated baseline ancestry evidence where unchanged.

After final relevant edits, freeze and identify the actual candidate. Run the original read-only DAG mirror check, syntax, actual collection and the full existing two-file suite plus additions in fresh processes. Resolve REPO, PY and OUT to real absolute paths:

```bash
cd "$REPO"
"$PY" -B scripts/codex_harness/sync_pr_dag_mirrors.py --check
"$PY" -m py_compile scripts/extract_theory_survivor_surface.py
"$PY" -B -m pytest --collect-only -q \
  tests/contracts/test_theory_survivor_triage.py \
  tests/contracts/test_theory_survivor_seed_schema.py
"$PY" -B -m pytest -q \
  tests/contracts/test_theory_survivor_triage.py \
  tests/contracts/test_theory_survivor_seed_schema.py \
  --junitxml="$OUT/pr450-repaired-tests.xml"
```

Record real argv/cwd/version/exit/timeout/invocation count and raw stdout/stderr for each command. Preserve the original checkout's actual pytest/conftest/import behavior. Do not let a shell pipeline or later command hide a preceding failure. The existing fifteen-minute validation/replay ceiling remains; record consumed command time and preserve the historical baseline consumption separately. No retroactive timeout increase; no repeated unchanged infrastructure probes.

Once required final checks pass, run the original production CLI twice against the SAME untouched historical object, with distinct fresh output paths and individual command records:

```bash
"$PY" -B scripts/extract_theory_survivor_surface.py \
  --repo "$REPO" \
  --matrix-ref 463f0999949bf8534c60ad7973b7342705c2e3d6 \
  --matrix-path docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json \
  --expect-git-blob 56af1713ef8c4718598e10012819d5ab62c6e37a \
  --output "$OUT/surface-a.json"

"$PY" -B scripts/extract_theory_survivor_surface.py \
  --repo "$REPO" \
  --matrix-ref 463f0999949bf8534c60ad7973b7342705c2e3d6 \
  --matrix-path docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json \
  --expect-git-blob 56af1713ef8c4718598e10012819d5ab62c6e37a \
  --output "$OUT/surface-b.json"

cmp "$OUT/surface-a.json" "$OUT/surface-b.json"
```

Do not use --replace, DIRECT_FILE/BOUND_METADATA, a mock Git repository or repaired matrix data as substitutes for this real-object replay. Compare generated JSON bytes, not CLI stdout containing different output filenames.

Use the unchanged workflow's `Validate exact generated surface` block, changing only output-directory locations, to generate its existing-schema receipt after successful replay. Copy one replay to `REGISTERED_SURVIVOR_SURFACE.json`. Confirm the original ten-field coverage object, 37 unique IDs, 36 INCLUDED/one DEFERRED, `unique_theorem_count: null`, no observational data or release authority. Confirm the exact PR284 child parent is II-3.2 and its disposition stays DEFERRED. Compare generated rows to the amended seed by ID/kind/parent/disposition, without inventing equality of unrelated historic metadata.

Verify `source.mode: GIT_OBJECT`, original matrix commit/blob/digest and content_id by the extractor's existing canonical JSON convention excluding only the content_id field. Whole-file SHA-256 and internal content_id have different inputs. Keep statement hashes and semantic links as source-carried provenance, not newly proven theorems. If a later real-object compatibility defect is demonstrated, repair it only within the same declared source semantics and rerun affected validation after the final edit; do not declare success from unit fixtures alone.

## 7. Return and authorised Git publication

After local self-review, commit the actual three-file delta and small readable evidence, non-force push one isolated task branch, and create its own Draft PR targeting PR457's branch specified above. Inspect/reuse a same-task branch instead of creating a duplicate. Local owns this ref; MAIN does not write it concurrently. A source candidate commit/tree and evidence-publication commit/tree may differ: record both. A repaired PASS never retroactively changes baseline 13/1 or means the publication-only commit was rerun.

Publish in a new result directory, for example `artifacts/research_reports/pr450_seed_coverage_repair_<run_id>/`:

- RETURN_TO_MAIN.md: actual outcome, scope, diagnosis, seed authority, reader policy, measured verification and precise remaining boundary;
- original-style result receipt plus the original workflow's surface and execution receipt when actually generated;
- exact patch, old/new source identities, seed one-byte reverse check, final source invariance record;
- the new real-layout RED and final raw logs/JUnit/node lists, both real replay files and comparison;
- compact checksums and actual remote-readback record.

Reference the immutable PR457 baseline logs by commit/path instead of duplicating all 183 files in each new bundle. Preserve those original raw bytes. Avoid one nested archive/manifest per edit; neither installed environments, private keys/tokens, unrelated user files nor broad worktree inventories are needed. Git text is the primary return route; a ZIP is only optional backup.

Read back the intended remote ref and newly published decisive payloads, with exact readback coverage. If Git push succeeds but Draft-PR creation fails, return immutable commit/file links and that separate API blocker. If transport fails, keep the actual local result/checkpoint and error; do not relabel an execution success as an execution failure. Source-only and raw-evidence whitespace findings must be separated; do not rewrite logs for cosmetic diff checks.

Codex's final message should supply `overall`, original baseline, tested candidate commit/tree or manifest, publication commit/tree, changed paths, original/added test counts, actual RED/GREEN and two-replay results, source/matrix checks, Draft PR, immutable RETURN_TO_MAIN.md and receipt URLs, and the observed hosted-CI status separately. Use `PASS_REGISTERED_SURVIVOR_SURFACE_TRIAGE` only after its existing criteria actually pass, with MAIN review pending. Preserve honest NONPASS/blocked results when they occur. Do not claim outside/blind review by local self-review.

This is evidence publication, not merge, ready status, canonical migration, proof adjudication or scientific release. MAIN will review the returned actual bytes directly; no WORK_THREAD or mandatory user ZIP upload.

## 8. Retained scientific boundary and MAIN action record

Canonical T9 v4/30; Report-A candidate 40. PR284's source CAS conflict stays unresolved and its extraction DEFERRED. The 37 source dispositions are not 37 unique theorems. Do not reopen completed K5 PDF, K2FER1/K2FR, R2 four supporting lemmas, PR455 authority replay or PR451/PR456 native decoder validation. The fibre research notes are not new replay prerequisites. No observations, BASS/REC/REI inquiry or implementation, finite-HEALPix admission, new CAS, PDF regeneration or unrelated next work unit is authorised.

MAIN freshly read the relevant PRs, actual extractor/type validators, nested matrix declaration, original fixture, protected seed, workflow and applicable repo policy. One container probe and one independent Python fallback returned ClientError before an observable process result. No implementation patch, pytest or production replay was executed or claimed in MAIN. Only this approved executable handoff and explicit status comments are being published here; the local candidate remains owned by the local writer. The older attached R4A1ER/PDF/runtime snapshots remain historical where later accepted evidence supersedes them.
