## OWNER APPROVED — T2 token restoration and bounded presentation-assertion repair

Work unit: `HTT_T2_TOKEN_ASSERTION_REPAIR_V1`.

The owner has now explicitly approved **“T2 수식 토큰 세 곳 복원 + 두 presentation-sensitive assertion의 한정 수리”**. This advances the proposed next scope in comment 5552398491 to an authorised local implementation task. It does not relabel the previous 37-PASS/3-FAIL run, approve new science, or authorise a merge.

### Three-way ownership and fixed base

Discussion thread: scope and final result interpretation. WORK_THREAD: forward this same contract to LOCAL_CODEX, review its actual returned bytes/results, and manage the single publication. LOCAL_CODEX: sole authored-source writer and native executor. Work and discussion must not write the same source concurrently with local. A result-informed review is not blind.

Repository: `cosmosapjw-quantum/htt_base`.
Base commit: `93576d976d6e70b44df80a07fe2d7472af1611d3`.
Base tree: `26d68c52997cff838670ccea9dc05d15f7bda75f`.
Suggested new branch: `implementation/htt-t2-token-assertion-repair-20260905-r1`.
Target for a later Draft PR: `implementation/htt-authority-citation-reconciliation-20260905-r1` (PR454 branch).

Fresh reads in this approval turn found PR454 unchanged and no proposed remote repair branch. Local must still inspect worktrees/unpushed work and reuse an existing matching task. Read AGENTS.md and applicable repository scientific-code/provenance rules. Use a clean isolated worktree at the fixed base and a new evidence directory outside it; preserve the main checkout, venv/data and prior evidence. No partial/promisor clone or competing source writer. Do not silently follow a newer branch head instead of the execution pin.

### Exactly two authored source paths

1. `docs/research_reports/theory_packs/T2_QO_ORBIT_RECONSTRUCTION_THEOREM_PACK.md`
   - Original Git blob: `8e66a7bb698932a060cc60057e3541b782167d83`.
   - Restore only the three malformed fraction tokens described below.
2. `tests/contracts/test_report_a_r4a0_source.py`
   - Original Git blob: `9e89bd74dce87a17b9f5d97940b7b2ad68061efd`.
   - Repair only the two presentation-sensitive assertions and add the necessary local helpers/control-character guard and focused regression cases in this same file.
   - Retain all three original test function/node names and their scientific requirements. Do not delete or weaken the complete Cayley–Hamilton/moment checks.

New execution/review artifacts are allowed in this task's isolated evidence namespace; they are not extra authored source changes. No new permanent validator, module, workflow, schema gate or general cleanup.

Protected inputs include the repaired V3 contract `c66a43f94330ca62b0044b0c7f6e919adf12c17a`, repaired citation `5087d39edf094f3adf7d72eed3061521ecf0b78d`, T9 v4, R3 manuscript, revision-2 manuscript, bibliography, all other tests/configuration and all historical artifacts. No additional hash repinning is authorised. Do a targeted read-only check for active consumers of the changed T2/test identities. Historical receipts stay bound to their original bytes. If an additional live pin really must change, preserve the two-file candidate and report that specific scope extension rather than silently editing a third source.

### Intact source authority for the three restored tokens

Read, do not modify:
`docs/research_reports/HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md`, blob `16f8fdd4db4dac384c5c64a8d3f86e0dbbf62e34`, at the same fixed base.

Its Cayley–Hamilton/moment passage (approximately LF-based lines 260–272) already contains:

```latex
\bar Q^3=\frac{s_2}{2}\bar Q+\frac{s_3}{3}I,
\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0,
\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1.
```

The required coefficients are therefore not inferred from a test or silently supplied by general knowledge. Restore T2's own surrounding punctuation and layout unchanged. The previous byte review reports U+000C followed by `rac` in T2 at LF-based lines 234, 241 and 245. Inspect complete Git bytes locally: line-ranged connector views may render form-feed as a newline and are not byte authority.

Expected byte replacement at each of those three sites:

```text
old: 0c 72 61 63 7b       (FORM FEED, r, a, c, {)
new: 5c 66 72 61 63 7b   (backslash, f, r, a, c, {)
```

Require the expected original blob and three matching, context-confirmed sites before editing. Record offsets and LF-based line numbers using LF, not a generic splitlines operation that also treats form-feed as a line boundary. Perform no whole-file reserialization, Unicode normalisation or newline cleanup. For exactly this replacement, the output is three bytes longer and all other bytes must be identical. Reversing only the three documented replacements must recover the original bytes/hash. If local bytes differ from this description, return the exact mismatch; do not guess the repair.

The preserved T2 equations after restoration are its displayed `\bar Q^3` relation and its two `\mu_3`, `\mu_4` recurrences, with coefficients s_2/2 and s_3/3 unchanged. This is mathematical-text restoration, not a new Cayley–Hamilton proof or Q/O implementation validation.

### Presentation checks: tolerate layout, retain the actual propositions

The R3 source is correct in the two relevant passages and remains byte-identical. Do not insert a newline into it after `Let` or change its `HEALPix` spelling merely to satisfy tests.

- Cholesky: accept permitted ASCII space/tab/LF/CR wrapping of the complete existing sentence about the **unique upper-triangular Cholesky factor with positive diagonal**. Continue checking `B_+^TB_+=G`, `det B_+=|chi|`, the signed diagonal orientation map, `B=S_chi B_+`, orthogonality and the exclusion of the old nonunique choice. Keep mathematical symbol case, transpose/order, coefficients and sign meaningful.
- Scope: accept exactly the existing `HEALPix` and historical `HEALPIX` proper-name forms in the complete **negative** sentence denying a finite-HEALPix no-go theorem. Preserve all exact machine-readable boundary constants and the explicit native-BASS denial. Do not case-fold the entire mathematical document or accept a bare keyword without its negation.
- Raw source control characters must be checked before whitespace processing. At minimum reject U+000C; reject C0 controls other than tab/LF/CR and DEL in the checked text. Do not allow `str.split()` or a broad whitespace expression to turn a damaged control token into accepted formatting. Do not silently sanitise input in a reader.
- The existing Cayley–Hamilton/moment checks must continue to require all three intact formulas. Retain the original truncated-token rejection and supplement it with raw control-character rejection; passing the new guard is not a replacement for checking the formulas.

Refactoring these assertions into small private helpers inside this test file is allowed so the original three tests and new mutation fixtures exercise the same check. No separate framework is requested.

### Focused regression evidence

Add directly relevant positive/negative cases in the same test file. Report actual node/fixture counts instead of prescribing an artificial total.

Positive controls: the intact pinned R3 one-line sentence, allowed newline-wrapped equivalent, and the two permitted HEALPix spellings must be accepted without changing equations or negative meaning.

Negative controls must make an effective change (`mutated != original`) and be rejected by the same helpers used by the original tests. Cover:

1. Reintroduce each of T2's three form-feed fraction corruptions separately; also retain rejection of an actually truncated `rac{` token. Detect corruption before whitespace handling.
2. Alter a coefficient or moment index in each of the three displayed formulas; do not accept a wrong formula merely because `frac` tokens exist.
3. Remove uniqueness/positive-diagonal language or alter the signed orientation relation. The canonical-section check must still reject loss of the deterministic proper-oriented section.
4. Remove or reverse the finite-HEALPix denial, change the unresolved boundary constant, or remove the native-BASS denial. Correct capitalisation alone must not make these mutations pass.
5. Inject a forbidden control character into otherwise acceptable checked text and reject it rather than normalising it away.

These are documentary/semantic-regression checks, not formal theorem proofs or security certifications. Preserve real failure/exception details; an unrelated import/runtime failure is not evidence that a negative fixture rejected its intended mutation.

### Existing evidence reuse and native execution

The prior local replay is already durable at this base under
`artifacts/research_reports/authority_citation_replay_20260905_local_130332z/local_return/result/`.
Read the original `EXECUTION_RECEIPT.json`, `authority-replay.stdout`, `authority-replay.xml`, collection/node accounting and before/after identities. It is the existing RED evidence: 40 original nodes, 37 PASS / 3 FAIL. Do not rerun the whole unchanged suite solely to reproduce that known result or call archived RED a fresh run.

Use the existing installed CPython 3.12 environment; previous accepted local versions were CPython 3.12.3, pytest 8.4.2 and PyYAML 6.0.3. Record actual versions and paths, and use these already available matching dependencies without broad package provisioning. No Lean, Wolfram, Rust, Docker or PDF setup is needed.

Capture new commands/source identities before edits. Freeze the new focused regression source before the final GREEN run. Execute focused checks to demonstrate rejection of corrupt inputs and acceptance of the bounded valid variations, then execute the **existing entire eight-file authority suite** against the repaired source, with all original 40 node IDs present and executed. Added nodes belong to this new run and are counted separately from those original 40.

```bash
cd "$REPO"
"$PY" -B -m pytest -q \
  tests/contracts/test_report_a_t9_v4.py \
  tests/contracts/test_report_a_citation_matrix_r4a1nf.py \
  tests/contracts/test_report_a_r3_flattened.py \
  tests/contracts/test_report_a_r4a0_source.py \
  tests/contracts/test_report_a_r4a1n_notation.py \
  tests/contracts/test_report_a_r4a1nf_flattened.py \
  tests/contracts/test_report_a_r4a1_authority_v3.py \
  tests/contracts/test_report_a_r4a1v0_formal_verifiers.py \
  --junitxml="$OUT/authority-replay.xml"
```

Set REPO, OUT and PY to real isolated absolute paths. Preserve existing pytest.ini/conftest/import handling; no node deletion, skip, xfail, deselection, filtering the old failures or bypass. The existing suite's formal-source checks are not an instruction to launch CAS axes. Keep raw stdout/stderr, argv/cwd, exits, timing/timeout and invocation counts. Preserve the actual exit under shell error handling rather than hiding failure with `|| true` or an unchecked pipeline.

Run relevant syntax and `git diff --check`; compare the actual authored-file set with the two allowed paths and record protected-source hashes before/after. The 30-ID digest should still be computed by the unchanged existing test; keep the canonical ledger hash field null/pending. The earlier citation fix, original six-file candidate, five findings/scope annex, R2 receipts and delivered K5 remain unchanged.

If the final suite reveals an additional unrelated failure or active binding outside the two-file scope, retain the candidate and original error, label NONPASS or SCOPE_EXTENSION_REQUIRED and stop this slice. In-scope P0/P1 review corrections go back to the same local writer under the existing bounded repair policy, not a parallel writer. Do not expand this into PR450/451/444, Q/O implementation work, a CAS rerun or a full repository audit.

### Return, review and publication

LOCAL_CODEX returns a durable archive with the exact two-file patch and repaired bytes, old/new Git blob and SHA-256 identities, three token byte offsets/context and reversal proof, node/fixture inventories, unmodified raw logs/JUnit, actual runtime/command records, before/after source checks and a concise result. Preserve the old NONPASS evidence. The manifest must cover actual returned files without self-hash cycles; return the outer ZIP digest separately. Do not include credentials, private keys, unrelated data or package binaries.

WORK_THREAD verifies the returned bytes and the two-file scope; performs one provenance/claim-ceiling review and one code/test review, recorded as sequential/result-informed where applicable; and checks original-node preservation, actual mutation rejection and the full suite result. No automatic repetition of a successful full suite merely to confirm it.

For a reviewed result within this approval, WORK_THREAD may publish the exact two-file candidate and new noncanonical text evidence on the suggested **new isolated child branch based on the fixed PR454 commit**, creating a Draft PR targeting the PR454 branch. LOCAL_CODEX is not to mutate remote refs in parallel; either work is sole publisher or explicitly transfers that single role to local. Read back complete new/changed payloads and record commit/tree/PR identities. Failed test results can only be published with their actual NONPASS status, not promoted to GREEN. Preserve existing #449/#452/#453/#454 source refs and original evidence.

No merge, ready transition, force-push, canonical or scientific-publication promotion. No original report/PDF rebuild, K2 rematerialisation, R2 replay, observation or BASS/REC/REI work. This assignment ends with the bounded repair's actual regression and review/publication result; no next scope runs automatically.

Return `t2_repair_result` with at least:

```yaml
work_unit: HTT_T2_TOKEN_ASSERTION_REPAIR_V1
base_commit: 93576d976d6e70b44df80a07fe2d7472af1611d3
base_tree: 26d68c52997cff838670ccea9dc05d15f7bda75f
source_writer: LOCAL_CODEX
changed_paths: []
old_new_identities: []
intact_formula_authority_blob: 16f8fdd4db4dac384c5c64a8d3f86e0dbbf62e34
token_sites_restored: null
only_three_token_replacements_in_T2: null
original_40_nodes_preserved: null
original_node_results: null
new_focused_node_results: null
positive_fixture_results: null
negative_fixture_results: null
suite_exit: null
errors_skips_xfail_deselect_timeouts: null
canonical_30_id_digest: null
protected_sources_unchanged: null
raw_log_and_junit_paths: []
review_independence: null
publication: null
return_archive_sha256: null
canonical_claims: 30
candidate_claims: 40
canonical_ledger_modified: false
new_CAS_executions: 0
K2FER1_repeated: false
K5_rebuilt: false
publication_or_merge_promoted: false
overall: null
```

Use actual values and an honest overall such as `T2_TOKENS_AND_ASSERTIONS_REPAIRED_AUTHORITY_PASS_PENDING_REVIEW`, `REPAIRED_AUTHORITY_NONPASS`, `SOURCE_DRIFT`, `SCOPE_EXTENSION_REQUIRED` or a precise runtime/publication blocker. No PASS is supplied by this approval itself.

### Discussion-turn action record

This turn freshly read PR454, searched for related progress, read the intact R3 equations/section and the existing test, and checked that the proposed remote branch prefix was absent. The two local attempts to create a delivery directory (shell then independent Python) returned ClientError; no local file/artifact or source execution is claimed. The authoritative instruction is this GitHub comment. Discussion has not edited the two source files or started local Codex automatically.