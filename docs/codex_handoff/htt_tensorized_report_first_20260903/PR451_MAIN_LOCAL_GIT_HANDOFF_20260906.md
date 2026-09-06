# PR451 — main conversation / Local Codex, Git-based handoff and return

Date: 2026-09-06
Work unit: `HTT_PR451_EXACT_SOURCE_DECODER_VALIDATION_V1`
Status of this file: executable assignment and delivery instruction, NOT an execution receipt.

## 1. Current owner direction and precedence

The main conversation does all feasible research, derivations, source preparation, checks, review, interpretation and publication management. Only work requiring the actual local checkout/toolchain is delegated. No separate WORK_THREAD is required.

The owner now explicitly requests Git-published handoff files AND Git-published local results so that a commit/PR/file link or a short Codex output can be shared directly with the main conversation. Downloading a ZIP and re-uploading it between conversations is not the default delivery path.

This file consolidates the current PR451 assignment. It replaces the no-remote-push/manual-ZIP-return part of PR451 comment 5559783713 and the older mandatory WORK routing/execution-only restrictions in comment 5557718181. The remaining scientific scope and in-scope automatic-repair permission are preserved. Comment 5557723200 remains historical provenance clarification: the archived SymPy exact-basis proof and numerical source-equivalent tests/stress retain different grades.

Historical instructions are not rewritten. A later explicit owner amendment takes precedence. A handoff-file commit is a coordination identity, not the execution-source commit. This file is intentionally published on the report branch, outside any running local decoder candidate.

For future assignments, apply the same delivery default within their own authorised repository and scope: publish the handoff before delegation when possible, publish readable return evidence after execution, and return immutable links. This does not authorise editing unrelated repositories or globally rewriting their policies.

## 2. Fixed execution baseline

Repository: `cosmosapjw-quantum/htt_base`.
Parent PR: #451.
Parent branch: `repair/qo-krylov-packet-image-syzygy-20260903`.
Baseline commit: `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`.
Baseline tree: `6f2fdfd5b8fbf5e4ee3579288fb5aa3da1bb1060`.

Read AGENTS.md and the applicable repo-local scientific-code/provenance instructions at the actual source. Inspect current PR/local worktree/task state first. Reuse a matching completed or active assignment instead of starting a second writer. A documentation-only remote change does not silently repin this baseline.

| Baseline file | Git blob |
|---|---|
| `htt/src/common/mes_krylov_completion.py` | `f22132c7a3f247abd00f01cf1cce13dcad091070` |
| `tests/common/test_mes_krylov_completion.py` | `32ff53f371b9f5d79c94cfad2073906df0dd34ad` |
| `tests/common/test_mes_krylov_stable_decoder.py` | `6834e6c658b828d6e442d9b12785ccbb75d67c1d` |
| `.github/workflows/qo-krylov-packet-image.yml` | `08d8d868bb971721016e2071c0eb2d943ac30a8a` |
| `docs/research_program/theory_promotion/closeout/PR451_STABLE_STF_DECODER_RECEIPT.json` | `9954d918f1fc63c8b3df89fbff1b9e1448305150` |

The actual missing result is execution of this decoder, followed by any necessary in-scope repair and main-conversation review. Do not substitute a copy transcribed from a chat excerpt for an authenticated checkout.

## 3. Protected mathematical and numerical meaning

Preserve the SO(3) observable-orbit interpretation, unit-Frobenius Q/O normalization and positive amplitudes, triple ordering, STF symmetry/trace/norm, signed orientation, `O_bar:Q_bar = B e0`, complete forward replay, existing tolerance/condition-limit/rcond values and typed inverse-domain semantics.

An inconsistent packet must not be made valid through silent projection. Do not broaden `OrbitChartUnavailable` to conceal malformed inputs or failed positive controls. The two stable-forward tests permit replay OR genuine typed chart unavailability. That PASS is not universal successful inversion. The unavailable exception subclasses `OrbitInputError`, so classify the specific subclass first. Report a decoded/unavailable branch count only when actually observed.

The fixed seven-tensor STF3 basis and row-scaled ten-by-seven least-squares method already exist. Do not redesign them, add a physical-source inference, implement an all-strata atlas, or infer uniform conditioning from exact rank seven.

The historical numerical 28-test/10,000-pair result remains `LOCAL_SOURCE_EQUIVALENT`. The historical SymPy basis verification remains an exact-arithmetic record, not a fresh execution of the new candidate. Do not reconstruct a missing stress generator from aggregate values or repeat the old CAS/stress as an invented prerequisite.

## 4. Actual local execution and bounded automatic repair

LOCAL_CODEX is the sole source writer for the delegated candidate. MAIN does not edit the same candidate or ref while local owns it.

Use the existing repository (previous locator `$HOME/Dropbox/bianchi/htt_base`) and a clean isolated worktree. A previous external run-area locator is `/mnt/sn850x2t/htt_base_e2e/`; verify actual writable paths. Preserve the user's original checkout, dirty work, venv, data and previous evidence. No reset/clean/stash of unrelated work, partial/promisor clone or repository-wide cleanup.

Use installed CPython 3.12. Record actual Python, NumPy, pytest, module paths, NumPy/BLAS configuration and relevant thread settings. The workflow fixes Python 3.12 but does not pin NumPy/pytest; do not invent a package lock or change versions until an error disappears. Do not perform a broad package census, reinstall Rust, require Lean/Wolfram, or rebuild the PDF environment for this Python-only task.

Set `REPO`, `PY` and `OUT` to actual absolute paths. Keep cache/bytecode output isolated and preserve the checkout's actual pytest configuration, conftest and imports. Record command/cwd, actual exit, timeout, stdout/stderr and JUnit. Reuse a fully matching prior baseline execution instead of duplicating it; otherwise execute the existing baseline:

```bash
cd "$REPO"
"$PY" -m py_compile htt/src/common/mes_krylov_completion.py
"$PY" -B -m pytest --collect-only -q \
  tests/common/test_mes_krylov_completion.py \
  tests/common/test_mes_krylov_stable_decoder.py
"$PY" -B -m pytest -q \
  tests/common/test_mes_krylov_completion.py \
  tests/common/test_mes_krylov_stable_decoder.py \
  --junitxml="$OUT/pr451-baseline.xml"
```

The historical count is 28; record actual collected/executed IDs. Do not count fixture subcases twice. Preserve the baseline outcome even if a subsequent candidate succeeds.

When an execution-discovered implementation, directly related fixture/import/invocation or packaging defect can be fixed within this objective and the protected semantics, diagnose and repair it without another routine approval round trip. The normal authored surface is the decoder and its two tests. A directly necessary Q/O helper/import or isolated invocation fix needs a reproduced causal link and an explicit diff, not a new framework or adjacent work unit.

Preserve the first failure, add a focused regression for the real defect, then continue evidence-driven edit/test/diagnose iterations until the acceptance criteria are met or a genuine boundary is reached. One bounded repair episode is not one edit or a two-iteration limit. Do not delete nodes, use skip/xfail/deselection, weaken oracles, enlarge tolerances, change rcond/conditioning domains or manufacture abstention to obtain GREEN.

After the final relevant edit, freeze the actual candidate and run the full existing two-file suite plus added regressions in a fresh process. Keep original node IDs separate from additions. Record source bytes before/after execution. Identify the actually tested commit/tree or worktree manifest; a repaired candidate's PASS is not a PASS for the original baseline.

Preserve the prior resource ceiling: at most 900 seconds per spawned validation/diagnostic command and 3600 cumulative command seconds including diagnosis, unless a stricter accepted cap applies. These are ceilings, not predicted completion times or edit-count limits. Do not extend them retroactively. A repeated equivalent infrastructure failure permits one diagnostic alternative, not indefinite identical retries.

Stop only for a real boundary: protected scientific meaning must change, unresolved authority, a separately reserved work unit, destructive/new privilege action, competing writer or resource exhaustion. Return the best tested state and exact unresolved issue. A counterexample to a theorem is not repaired by altering the theorem to fit it.

## 5. Publish readable results from local — authorised in this assignment

Local may commit the in-scope candidate and text evidence, non-force push ONE isolated task branch, and create or update its own Draft PR. This permission explicitly replaces the prior return-before-push restriction. Evidence publication does not require an intermediate WORK review; MAIN reviews the real returned Git objects after publication.

Suggested branch: `validation/pr451-main-local-git-return-20260906-r1`.
Base: the fixed PR451 baseline above, not the handoff-document commit.
Draft PR target: `repair/qo-krylov-packet-image-syzygy-20260903`.

Inspect for an existing same-task branch/PR and reuse it when appropriate. Do not overwrite another actor's branch. Only local writes this candidate/ref. Keep original PR #451 and report/evidence parent refs unchanged. MAIN's updates to coordination documents do not authorise changing the candidate base.

Review the actual delta and recorded outcomes before commit. Push genuine PASS, NONPASS or blocked-result evidence with its true status. A failed run may be shared as failure evidence; it is not labelled a passing implementation. If source is unfinished, mark it explicitly as a nonaccepted candidate and preserve the first failure. Do not fabricate reviewer approval. MAIN performs subsequent result-informed review, not blind certification.

Use a unique evidence directory, for example:

`artifacts/research_reports/pr451_main_local_<actual_run_id>/`

Publish the actual small text evidence necessary for MAIN to review without an archive download:

- `RETURN_TO_MAIN.md`: result, diagnosis, repaired paths, preserved invariants, limits, next minimum action and relative links to the supporting files.
- The existing-style machine-readable `pr451_result.json` or YAML: actual baseline/tested-candidate identities, versions, commands, node outcomes, first failure, repairs, final result, source invariance and unperformed work.
- Original relevant stdout/stderr/exit records and JUnit, preserving baseline and final results separately. Keep raw contents; do not silently replace full logs with a passing tail.
- Actual code/test changes in the Git diff, plus the focused patch when useful, and a compact input/output identity index with hashes for the evidence payloads.

These are delivery contents for this existing task, not a new permanent validation framework. Reuse equivalent existing filenames/receipt styles rather than creating duplicates. `RETURN_TO_MAIN.md` is the entry point; it must not send MAIN to an unavailable local path for every decisive result.

The executed source commit/tree and evidence-publication commit/tree can differ. Record both truthfully. Adding logs does not mean the combined publication commit was rerun. Do not create a self-hash cycle or repeated commits merely to put the publication commit's own hash inside a file; report final publication identity in Codex's final output. The entry point can use relative links, which are resolved at its immutable commit.

A PR is useful for source review, but a pushed branch and immutable commit/file links suffice for transport if PR creation is unavailable. A PR API failure after a successful push is `GIT_PUBLISHED_PR_CREATION_BLOCKED`, not total publication failure.

Do not merge, force-push, mark ready, change existing PR bases, canonicalise the ledger, rewrite historical receipts, approve scientific publication, or run unrelated tasks. Normal push can trigger existing CI automatically; record actually observed hosted results separately from local tests. Do not claim CI PASS or retry workflows merely to make the transport look complete.

## 6. Large artifacts, readback and publication failures

The repository-text route is primary because MAIN can read it through the GitHub connector. A ZIP is optional backup, not the only container of the decisive evidence. Do not put only a ZIP, opaque LFS pointer or local filesystem path in Git and call the return connector-readable.

Keep raw observational data, entire environments, build caches, unrelated files, credentials/tokens/private keys and font files out of the commit. Avoid copying huge historical archives. For legitimately large binary artifacts, preserve an approved durable artifact location and checksums if already available, while keeping the decisive receipt, interpretation, links and necessary logs as readable Git text. Do not introduce a new storage service, public release or upload private data without applicable authority. This task does not require regenerating any prior PDF or publishing any new large binary.

After push, verify the remote ref equals the intended publication commit, and read back the new entry point, receipt and changed/evidence payloads using the available authenticated path. Verify the relevant content identities and record actual readback coverage. Do not turn ref existence into a claim that all bytes were checked. MAIN can independently read the exact commit through its connector once the user pastes the output/link.

When a push fails, preserve the local commit/result and raw error. Diagnose the one relevant transport issue; no blind retry loop, permission broadening or changes to protected source. If text publication is still blocked, clearly distinguish `EXECUTION_COMPLETE_PUBLICATION_BLOCKED` from an execution failure. Offer the local package only as a genuine fallback after the Git path is unavailable. No mandatory user download/re-upload step is introduced when links already work.

## 7. Return only the navigation information the user needs to paste

Codex's final output should give the actual result and a compact block like this, with observed values and immutable URLs, not placeholders presented as results:

```yaml
pr451_git_return:
  overall: <actual PASS/NONPASS/blocked classification>
  repository: cosmosapjw-quantum/htt_base
  baseline_commit: 9f7d06dec0fce1c3a8a53fa5372c84d9c679c037
  tested_candidate_commit_or_manifest: <actual>
  tested_source_tree: <actual>
  published_branch: <actual or null>
  publication_commit: <actual or null>
  publication_tree: <actual or null>
  draft_pr_url: <actual or null>
  return_to_main_url: <github.com/.../blob/FULL_COMMIT/.../RETURN_TO_MAIN.md>
  receipt_url: <immutable actual receipt URL>
  evidence_directory_url: <github.com/.../tree/FULL_COMMIT/...>
  tests: <actual counts, no historical substitution>
  remote_readback: <actual coverage/result>
  publication_blocker: <actual or null>
  canonical_claims: 30
  candidate_claims: 40
  merge_or_scientific_promotion: false
```

The user should normally paste just this block or the `RETURN_TO_MAIN.md` link into the main conversation. MAIN then fetches the underlying source, diff, logs, JUnit and receipts through the connector; it does not accept a prose summary as a replacement for available evidence. No manual archive transfer or intermediary thread is required for this standard path.

## 8. Completion retained; no automatic next work

K5's delivered review PDF, K2FER1/K2FR and its preserved five scope findings, R2's four supporting lemmas and PR455's local authority replay retain their original accepted scope. Do not repeat them to test the new delivery route. PR450 and other reserved work do not start automatically. Canonical remains T9 v4/30; candidate remains 40. Hosted-CI success, all-claim scientific validation, merge and release are not granted by a successful push.

This file changes how the existing task is transferred and returned. Its publication is not evidence that Codex has been started, the decoder has run, a repair has passed, or an independent review has occurred. When the return arrives, MAIN reviews it here and retains only genuine remaining issues.
