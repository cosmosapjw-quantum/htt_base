## Existing T9 authority replay — three-lane execution handoff

This is the next task already selected in parent intake comment 5551797917, not a new R2 run or an expanded scientific gate. The discussion thread freshly read PR449/453, the fixed V3 authority contract, the repaired citation file, the actual authority test and `.github/workflows/report-a-ledger.yml`. The proposed remote implementation branch is not present in the current matching-ref query; an unpushed local task may still exist and must be checked by the local writer. No new authority replay or source edit was performed by this comment.

### Roles and fixed input

- Discussion thread: scope and final evidence reconciliation.
- WORK_THREAD: forward this same instruction, inspect the returned delta/raw results, and manage the explicitly bounded publication below. Do not edit the running local source.
- LOCAL_CODEX: sole authored-source writer and actual native executor. Use the existing installed packages at the required versions, without broad provisioning or package census.

Repository: `cosmosapjw-quantum/htt_base`.
Base: `9a37311cc97a9f670ab6c7f300b0cf74ccabe121`.
Tree: `8a0641939dc6e49c1b0f949837e7ce2a3555757a`.
Suggested branch: `implementation/htt-authority-citation-reconciliation-20260905-r1`.

Read live PRs and any existing branch/worktree before writing. Reuse a matching task already in progress; do not create a competing writer. A coordination-only change to another branch is not a reason to silently repin this executable base. Read AGENTS.md and the relevant repo-local validation/provenance rules. Use a clean isolated worktree and a new external evidence directory. Preserve the user's main checkout, venv, data and existing results.

Let `P=docs/codex_handoff/htt_tensorized_report_first_20260903`.

Required fixed sources:

| Path | Git blob |
|---|---|
| `P/R4A1_SUPPORTED_RUNTIME_AUTHORITY_CONTRACT_V3.yaml` | `3c5ea8e7e21c5180b60313e47db2474cdf4d6744` |
| `P/REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml` | `5087d39edf094f3adf7d72eed3061521ecf0b78d` |
| `.github/workflows/report-a-ledger.yml` | `0647f96a65246f691d47f1bf22ca3e7a4f7b07d3` |
| `tests/contracts/test_report_a_r4a1_authority_v3.py` | `f44f49f96481aca26437ce7be97e5e2fc2be4fc3` |
| `artifacts/research_reports/k2fr_20260905/old_to_new_identities.json` | `e163148f962c55f6b0dc97d23f0a812954a1dbe4` |

Also read the published R4A1ER scope review at this base. The original local instruction `NEXT_LOCAL_AUTHORITY_REPLAY_KO.md` remains unchanged in the parent delivery; SHA-256 `9c101afdf7c27d9dce783847e217d2cf0b2fff4026fba746796fc921ad76e82a`. This comment makes that existing execution reachable from GitHub and specifies its work-review/publication route; it does not report its completion.

### One-file source repair only

Only the existing `P/R4A1_SUPPORTED_RUNTIME_AUTHORITY_CONTRACT_V3.yaml` is an authorised authored-source change.

Change `source_blobs.citation_matrix.git_blob_sha1` from:

`3fbaa2f97522cca6d0ad60e0c96655d293ca0d74`

to the already reviewed repaired citation identity:

`5087d39edf094f3adf7d72eed3061521ecf0b78d`.

In a separate top-level `citation_pin_reconciliation` field, record the prior contract commit/blob, old/new citation identity, the existing three-title quoting repair, and unchanged science/claim/runtime scope. Preserve the original schema, creation date/head, supersession and execution-history fields as history. Prefer a targeted edit rather than an unrelated whole-file reserialization. A new contract byte revision gets a new blob and SHA-256; it is not byte-identical to the old V3.

Keep the other six source pins, all tests, all claim statements/counts, existing history, runtime contract, scientific firewalls and expected 30-ID digest unchanged:

`e103c581ce353b5102af81834831ac292105f18699671e8eb75b171acd97f01e`.

Do not edit the already repaired citation, any `.bib`, the R2 contract/receipts, K2FR original bundle/findings/annex, manuscript or PDF. Do not globally replace the old hash. Do not create another compiler, generic validator, workflow or test suite.

### Actual local execution

Use the installed CPython 3.12 environment and existing pytest/PyYAML, recording exact versions and interpreter path. Do not use a Python 3.13 run as this contract's accepted execution. Lean/Wolfram are not prerequisites for this distinct Python authority replay; do not repeat the completed R2 run.

Set `REPO`, `OUT`, and `PY` to actual isolated repository, external output-directory and interpreter paths. Save the initial identities and commands before the first run. In the original pinned checkout, execute the existing targeted test once and preserve its actual outcome:

```bash
cd "$REPO"
"$PY" -B -m pytest -q \
  tests/contracts/test_report_a_r4a1_authority_v3.py::test_r4a1nf_binds_the_exact_declared_git_blobs
```

Classify the real failure: the expected source-identity mismatch is different from an import/runtime/fixture failure. Do not fabricate RED or overwrite old evidence. Apply only the permitted contract edit. Then use a fresh process for the entire existing workflow suite:

```bash
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

Preserve raw stdout/stderr, command/cwd, exact exit/timeout, invocation counts and actually collected/executed node IDs. These are eight test **files**, not eight cases and not the prior K2FER1 fifty-five tests. Do not delete, skip, xfail or deselect required nodes; do not replace conftest/config/import paths. An additional failure is returned with its original error and minimal next action, not automatically repaired beyond this scope. Do not disguise failure with `|| true` or an unchecked pipeline.

Compare the parsed original and changed contract: after excluding the new reconciliation field and replacing the one citation digest with its original value, the objects must agree. Separately inspect the textual diff and protected-source before/after identities.

The existing hash test intentionally asserts `canonical_sorted_id_sha256 is None` and `PENDING_SUPPORTED_RUNTIME_REPLAY`. A successfully computed 30-ID hash goes into the new execution receipt; it is not written into the canonical ledger here. Scope is the retained thirty-claim source/cross-surface validation, not a forty-claim theorem certificate.

Return exact contract patch and old/new identity, raw RED and subsequent suite logs/JUnit, node accounting, actual versions, the computed ID digest, source-invariance evidence and a result package with checksums. Preserve historical receipts, logs and failed outcomes. Do not upload private keys/tokens or unrelated user files. LOCAL_CODEX returns without remote mutation.

### Work-thread review and bounded publication

WORK_THREAD reads the actual returned bytes rather than reconstructing the patch from this description. Confirm the one-file delta, six preserved pins, unchanged tests/ledger/manuscript, actual RED cause, suite results and identifier hash. Record reviewer independence honestly; a result-informed review is not blind. Do not rerun an already successful full suite merely to repeat the same evidence.

After a matching result and source review, WORK_THREAD may manage publication of the exact reviewed one-file repair and new noncanonical text evidence on a **new isolated child branch based on the fixed PR453 commit**, with a Draft PR targeting `review/htt-r4a1er-local-result-scope-20260905-r1`. Do not modify existing PR449/452/453 source or branch refs. If publication is explicitly delegated back to local, transfer that role before either lane writes the ref; only one publisher acts. Read back every newly published payload. A publication blocker does not erase a completed local result. A failed suite remains a failed-suite result, not authority validation PASS.

No merge, force-push, ready transition, canonical promotion, physical claim promotion or observation is authorised. Preserve completed R2, K2FER1, K2FR and K5. Do not query or change REI/BASS/REC, rerun PDF/CAS, or execute PR450/451/444 as an automatic scope extension.

### Return to discussion

Return `authority_replay_result` with actual base/candidate identity, original/repaired contract blobs and SHA-256, citation blob, raw RED and post-repair status, node IDs/counts, errors/skips/xfail/deselect, command exits/timeouts/invocations, actual Python/pytest/PyYAML versions, 30-ID digest, protected-source checks, patch/log/JUnit paths, and published commit/tree/Draft PR or exact blocker.

Keep `canonical_ledger_modified: false`, canonical 30, candidate 40, `new_CAS_executions: 0`, `K2FER1_repeated: false`, `K5_rebuilt: false`, and `publication_or_merge_promoted: false`.

The next consuming decision is the scope-limited acceptance of the existing T9 authority replay. Remaining registered PR450/451 reviews, workflow-pin freeze work and applicable PR444/error-class limits remain separate obligations; no new research programme is introduced.