# PR450 — existing registered-source replay, MAIN / Local Codex, Git return

Date: 2026-09-07
Work unit: HTT_PR450_REGISTERED_SOURCE_REPLAY_V1
This is an execution assignment, not an execution receipt or new governance gate.

## 1. Objective and current checkpoint

Execute the already implemented PR408 WU-001 / PR450 source extractor against the frozen PR405 Git object, using the existing two-file test suite and two-run deterministic replay. Return the actual generated source surface and raw evidence through Git. MAIN reviews the results directly; no WORK_THREAD detour or manual ZIP transfer is required.

Registered output: 37 source rows = 24 exact/conditional broad + 8 synthetic broad + 5 scoped; 36 INCLUDED and one DEFERRED (`PR284_NEW:FINITE-REGISTERED-PATH`). These are source dispositions, not 37 unique theorems and not the Report-A forty-claim candidate registry. Preserve semantic-duplicate links and broad-parent/scoped-child distinctions. Do not resolve the deferred PR284 conflict, adjudicate novelty/truth, or alter report claims.

The source matrix's broader candidate universe is not the 37-row selected surface. Its source counts/qualification are inherited, not silently replaced by fixture counts. The existing tests use synthetic matrices and a temporary Git repository; their PASS alone does not demonstrate replay of the actual PR405 object. Both tests and real-object replay are required by the existing workflow.

Completed K5 PDF, K2FER1/K2FR, R2 four supporting lemmas, PR455 authority replay and PR451 exact-source 28-node validation accepted via PR456 are retained, not rerun. The new contraction-fibre notes are supplementary direct derivations, outside this execution task.

## 2. Fixed inputs; do not confuse execution and coordination commits

Repository: cosmosapjw-quantum/htt_base
PR: 450
Execution baseline: ba84912bea165896ec8f0c0e5793b47d1736f512
Execution tree: 55065b3b9ff075f8a58a5bda5f3d11d85ba21ab5
Source branch: analysis/pr408-wu001-registered-survivor-triage-20260903
Approved PR408 merge lineage: 2dce66ca019609e6d07625bc6382bc347fbf5a8c
WU-001 required ancestor: bdad91a204c424030cd6d0e562232b6965a42900

PR405 matrix commit: 463f0999949bf8534c60ad7973b7342705c2e3d6
Matrix path: docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json
Expected matrix blob: 56af1713ef8c4718598e10012819d5ab62c6e37a

Read these at the execution baseline:

| Path | Git blob |
|---|---|
| `scripts/extract_theory_survivor_surface.py` | `9d5bee9b1926e35216b95ab1384dc28f7a25592f` |
| `tests/contracts/test_theory_survivor_triage.py` | `26ab6150de552bd7d083cdb0118b1d251bcf17fd` |
| `tests/contracts/test_theory_survivor_seed_schema.py` | `dd31c5e9f5d2e8348a6c8405de04a5b8685594fa` |
| `docs/research_program/theory_promotion/closeout/REGISTERED_SURVIVOR_SEED.json` | `76d0a2396c2cb7e0b514264fe6322a2316adfa69` |
| `.github/workflows/theory-survivor-triage.yml` | `c0a165c1d150c522b946e47c253f41ab53090b09` |
| `docs/codex_handoff/pr408_final/WU-001.yaml` | `45ee133372bcc7256887c6300c37b2cc6ef8c32d` |
| `AGENTS.md` | `24e666c89e38159790b659b4b4e75502e50b5f2c` |

Read applicable repo-local scientific validation/provenance instructions. The handoff lives on the report coordination branch; it is not the execution baseline and does not change a local candidate's parent.

Fresh PR/local task inspection comes first. Reuse any fully matching completed result or active sole writer. A targeted MAIN search located no new published PR450 replay; this says nothing about unpushed local work. Do not start a competing writer or overwrite another branch.

## 3. What requires local execution

MAIN read the source extractor, both tests, workflow, seed header, original WU-001, AGENTS and pinned PR405 matrix header. Shell and independent Python each returned ClientError here; no repository verifier ran. Actual Git subprocess access to the historical object and CPython 3.12 validation are delegated for that reason, not because this task is too large.

Use the existing checkout (previous locator `$HOME/Dropbox/bianchi/htt_base`) and a fresh isolated worktree plus a unique external evidence directory (previous run-area locator `/mnt/sn850x2t/htt_base_e2e/`). Verify actual paths. Preserve original checkout, dirty work, venv, data and historical evidence; no reset/clean/stash of user work, partial/promisor clone, root/apt operation or unrelated package census.

Use installed CPython 3.12 and compatible pytest, recording exact versions/executable and imported module path. The workflow does not pin a pytest version. Do not manufacture an exact package lock, tune dependencies until green, or make NumPy/Lean/Wolfram prerequisites for this standard-library extractor. Normal non-destructive fetch of missing exact commits is allowed.

Record actual HEAD/tree, relevant complete file identities, clean tracked state, and the two ancestry relations above. Run the existing WU-001 `sync_pr_dag_mirrors.py --check` in read-only check mode and record its actual result; do not modify or append DAG mirrors. The historical `-k evidence_mutation` prose selector is not a replacement for the actual full two-file suite; execute the named mutation test through that suite. Preserve actual drift failures rather than expanding into harness cleanup.

## 4. Existing execution, not a rewritten extractor

Resolve REPO, OUT and PY to actual absolute paths. OUT is external to the checkout and unique to this run. Capture raw stdout/stderr, cwd, argv, real exit/timeout, invocation count and timestamps. Do not use unchecked pipes or `|| true`. Keep pytest config/conftest/import behaviour and original nodes intact. Cache redirection outside tracked source is permitted.

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
  --junitxml="$OUT/pr450-tests.xml"
```

Source inspection gives thirteen triage functions plus one seed-schema function, consistent with the historical fourteen tests; use actual collection/node results, not this expectation, in the receipt. Git subprocess fixture tests are not evidence that the real matrix was replayed.

After required baseline checks pass, execute the existing CLI against the actual historical Git object, twice in fresh processes and distinct output files:

```bash
for suffix in a b; do
  "$PY" -B scripts/extract_theory_survivor_surface.py \
    --repo "$REPO" \
    --matrix-ref 463f0999949bf8534c60ad7973b7342705c2e3d6 \
    --matrix-path docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json \
    --expect-git-blob 56af1713ef8c4718598e10012819d5ab62c6e37a \
    --output "$OUT/surface-${suffix}.json"
done
cmp "$OUT/surface-a.json" "$OUT/surface-b.json"
```

Capture each CLI separately rather than allowing the last loop command to hide an earlier failure. Neither output may pre-exist; do not pass --replace. The two runs are the pre-existing deterministic-replay obligation, not blind retries. The CLI's stdout includes its different output filename; compare the generated JSON file bytes and content_id, not the two path-bearing stdout strings. This distinction prevents a false nondeterminism diagnosis.

Use the original workflow's `Validate exact generated surface` Python block to create its existing-schema EXECUTION_RECEIPT.json, adapting only output-directory locations. Check schema, exact source commit/blob, the original ten-field coverage dictionary, 37 unique IDs, 36 included/one deferred, exact PR284 child and no observational/release authority. `unique_theorem_count` must remain null. Do not manufacture this receipt when a previous required operation failed.

Additionally, the result reader should confirm `source.mode == GIT_OBJECT`, the complete matrix's locally measured digest, and recompute the generated content_id using the extractor's canonical JSON convention excluding the content_id field itself. The complete file SHA-256 and internal content_id are different hashes with different inputs. Compare generated candidate IDs and common disposition/kind/parent fields with the existing seed without requiring unrelated historical metadata to match. Keep statement-identity strings and semantic links as source-carried provenance; do not claim this operation re-proves their mathematical meanings.

DIRECT_FILE and BOUND_METADATA are legitimate code paths but do not satisfy this real-object execution assignment. Do not replace --repo with a fixture/file and label it GIT_OBJECT. Do not populate a fake repository to imitate a historical commit. A true acquisition blocker is returned with exact command/error.

## 5. In-scope automatic repair and stopping boundaries

LOCAL_CODEX is the sole writer of the delegated candidate. If an actual execution reveals an ordinary extractor, directly related fixture/loader/invocation or packaging defect that can be corrected within WU-001's meaning, preserve the first failure, add a focused regression and repair autonomously. Continue evidence-driven edits within this single bounded episode; a second productive edit is not a new approval request.

The normal source surface is the existing extractor and its two tests. A seed change is not authorised merely to match output: its registered candidate identities and dispositions are protected inputs. Do not edit the PR405 matrix, thresholds/semantic classifications, historical statements/hashes, existing evidence, canonical ledgers, existing DAG nodes/edges, or the Report-A manuscript/PDF. Do not skip, xfail, deselect or weaken original assertions. Do not relabel historical source-equivalent tests as exact-source execution.

After the final relevant edit, freeze the actual candidate and rerun the complete affected two-file suite and both actual-object replays. Preserve baseline and candidate results separately. No mandatory re-execution is needed for evidence-only publication after an unchanged successful source run.

Respect the existing workflow's 15-minute execution budget as the validation/replay ceiling, including any targeted correction runs, unless an already authorised stricter limit applies. Record timeout and consumed command time; do not extend limits retroactively or repeat unchanged failures indefinitely. One diagnostic alternative for the same infrastructure failure is enough. Stop with a durable best-tested result for mathematical/source-authority changes, unrelated harness drift, competing writer, additional privilege, scope expansion or resource exhaustion. Do not enter PR444, observer CAS, decoder, GPU, rootfs or observation work.

## 6. Direct Git return, including an honest NONPASS

After local self-review, commit/non-force push one isolated task branch, e.g. `validation/pr450-main-local-source-replay-20260907-r1`, based on the execution baseline (or its explicitly repaired candidate). Create/update only its own Draft PR targeting `analysis/pr408-wu001-registered-survivor-triage-20260903`. No merge, ready transition, rebase of another actor's branch, force-push, canonical migration or scientific release. Existing parent/report/evidence refs stay unchanged. The local writer is the one publisher; MAIN does not concurrently modify that candidate.

Publish readable text, not only a ZIP:

- RETURN_TO_MAIN.md with actual outcome, scope, sources, executed operations, diagnosis, repairs, limits and one next consuming decision;
- existing REGISTERED_SURVIVOR_SURFACE.json and EXECUTION_RECEIPT.json if actually generated;
- both original replay files, command stdout/stderr/exit records, JUnit and collected/executed nodes;
- runtime/source before-and-after identities, actual patch or explicit no-source-change record, compact checksums;
- pr450_result.json or equivalent current receipt style including baseline versus tested candidate and source-matrix versus execution-source identity.

Use a unique noncanonical directory such as `artifacts/research_reports/pr450_main_local_<run_id>/`. Large unrelated archives, credentials, private keys, installed environments and user data do not belong in the commit. Do not rewrite raw logs for whitespace cleanup. Avoid self-hash commit cycles: report the final publication commit/tree in Codex output after push.

Read back the remote ref and complete new decisive text payloads and record actual byte coverage. A pushed immutable commit remains usable if Draft-PR creation is blocked. On push failure preserve local commit/results and the exact publication blocker; do not treat transport failure as a failed computation. ZIP/manual transfer is fallback only when the Git path genuinely fails.

Return a compact block with actual values:

```yaml
pr450_git_return:
  overall: <actual result>
  baseline_commit: ba84912bea165896ec8f0c0e5793b47d1736f512
  tested_candidate_commit_or_manifest: <actual>
  matrix_commit: 463f0999949bf8534c60ad7973b7342705c2e3d6
  matrix_git_blob: 56af1713ef8c4718598e10012819d5ab62c6e37a
  tests: <actual original/added node counts and outcomes>
  replay_invocations: <actual>
  replay_bytes_equal: <actual>
  generated_coverage: <actual or null>
  deferred_candidate: <actual or null>
  source_mode: <actual or null>
  source_changes: <actual>
  publication_commit: <actual or null>
  publication_tree: <actual or null>
  draft_pr_url: <actual or null>
  return_to_main_url: <full-commit Git URL or null>
  receipt_url: <full-commit Git URL or null>
  hosted_CI: <observed separately; never inherited from local PASS>
  canonical_claims: 30
  candidate_claims: 40
  truth_novelty_publication_assigned: false
  merge_or_scientific_promotion: false
```

The successful workflow terminal is `PASS_REGISTERED_SURVIVOR_SURFACE_TRIAGE`; MAIN review remains pending until the returned actual evidence is read. NONPASS, source acquisition, environment and publication failures must retain their real classifications. No automatic next work unit follows this one.

## 7. MAIN action record

This handoff was prepared from actual source/workflow/tests, not a generalized replacement. MAIN did not execute its commands, generate the real 37-row output, start a Local Codex session, or obtain new CI/CAS evidence in this turn. The supplementary mathematical note developed in parallel is not a prerequisite or a new test obligation here. The current route is MAIN <-> Local Codex with Git-published handoff and return, superseding the old mandatory WORK_THREAD transport without claiming blind review.
