# Existing T9 authority citation reconciliation and replay review

**Review: PASS for the exact one-file delta and faithful returned evidence. Full eight-file authority suite: NONPASS.**

WORK_THREAD reviewed the supplied LOCAL_CODEX return and did not author the contract repair or execute its pytest suite. This is a separate, result-informed review, not blind. The completed local task was reused; no competing writer or repeat replay was dispatched.

The governing instruction is PR453 comment [5551926742](https://github.com/cosmosapjw-quantum/htt_base/pull/453#issuecomment-5551926742). Its work-publication clause permits the exact reviewed repair and new noncanonical text evidence on a new child Draft PR; it expressly preserves a failed suite as failed. This publication carries that NONPASS result and does not accept the full T9 authority component.

The execution base is 9a37311cc97a9f670ab6c7f300b0cf74ccabe121, tree 8a0641939dc6e49c1b0f949837e7ce2a3555757a. LOCAL_CODEX left one uncommitted contract change and made no remote mutation. Applying that exact one-file identity map to the fixed tree gives source-only tree 46fb44f32320c149c291c70a30289d8e7064f2c4, computed by this review and not a local executor commit. The published tree also contains new review evidence.

## Return integrity and exact delta

The actual supplied ZIP is AUTHORITY_CITATION_RECONCILIATION_20260905T130332Z.zip: 1,056,133 bytes, SHA-256 7f5defba11e05aa168bf7ec2cdf9c2e4243061b9bee6af5f05fde5f9864a7853. Safe extraction, CRC and all 52 internal checksums pass over 53 files. The separately supplied patch is byte-identical to the archived patch. The external result YAML matches every field of the original execution receipt and correctly binds the archive, patch and JUnit; it is deliberately outside the archive to avoid circular hashing.

| Object | Original | Reviewed candidate |
| --- | --- | --- |
| V3 contract Git blob | 3c5ea8e7e21c5180b60313e47db2474cdf4d6744 | c66a43f94330ca62b0044b0c7f6e919adf12c17a |
| V3 contract SHA-256 | d6e5caf314390acf98cca3cef04f3280cfa2a795579f8e40e3317c6e5992beea | b53fd22a625ba24d43844fce67b8c0b270329ac54e08caf30478383ec03748a9 |
| Citation pin | 3fbaa2f97522cca6d0ad60e0c96655d293ca0d74 | 5087d39edf094f3adf7d72eed3061521ecf0b78d |

Only docs/codex_handoff/htt_tensorized_report_first_20260903/R4A1_SUPPORTED_RUNTIME_AUTHORITY_CONTRACT_V3.yaml changes. The two-hunk full-index patch changes one citation digest and appends citation_pin_reconciliation. In-memory exact patch application reproduces the returned candidate bytes; read-only git apply --check exits 0. After removing the added mapping and restoring the one old digest, parsed objects agree. The original schema, creation date/head, supersession, execution history, six other pins, expected ID digest, domains, runtime and firewalls remain equal.

The reconciliation accurately names the previously published three-title quote-only repair: RANDOMIZATION_2024, ROLDAN_NOTARI_QUARTIN_2016 and LI_1999. Both complete old/new citation payloads and the published old-to-new identity record were checked. The citation file itself remains unchanged. The old contract's NOT_YET_EXECUTED/PENDING fields are preserved historical fields; new results belong to the separate receipt, and do not silently rewrite history.

## Recorded native execution

Actual local environment: CPython 3.12.3, pytest 8.4.2, PyYAML 6.0.3. Interpreter: /mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python, resolved /usr/bin/python3.12.

| Invocation | Child PID | Exit | Actual result |
| --- | ---: | ---: | --- |
| Original exact-binding RED | 3371898 | 1 | 1 failed: citation_matrix old/new blob mismatch |
| Post-repair exact-binding | 3375989 | 0 | 1 passed |
| Eight-file collection | 3376750 | 0 | 40 unique nodes |
| Entire eight-file authority suite | 3376806 | 1 | 37 passed, 3 failed |

Each pytest command has its own original argv/cwd, start/end times, raw stdout/stderr, exit and 900-second bound. No timeout occurred; stderr is empty. Four distinct process records occur in order, with the suite at 2026-09-05 13:07:36–13:07:37 UTC. JUnit's +09:00 timestamp lies inside the same UTC interval. One invocation of each command is recorded. The exact-binding node appears again, successfully, in the full suite; that is not an unreported second full-suite replay.

All eight file arguments equal the existing workflow command. Source AST registration, raw collection, collected-nodeids.json and all 40 JUnit cases agree in order and identity. No case was deleted, skipped, xfailed or deselected; errors/skips/xfail/xpass/deselection are zero. Existing pytest.ini addopts remain -m "not slow"; none of these 40 nodes has a slow/skip/xfail decorator. No conftest replacement or test source edit occurred. The formal-verifier test file reads existing source/config; this authority run does not invoke the CAS axes.

All six V3 authority nodes pass in the original suite, including runtime, exact binding, canonical hash and cross-surface checks. That narrower result does not convert the full suite to PASS.

Original EXECUTION_RECEIPT.json SHA-256: 55a44f6bccaae5acec6256490ce42297c1e16aef34883215308b01175a737ae7.
Original authority-replay.xml SHA-256: 9a8e10646d24cb89de44b225bbcc7caa67f0efa35350b90e885de8f3c61f1988.
Exact patch SHA-256: bc4ecd22a29a82c1a68958339d9651f6331e61950751545eff62e2e42f1808f7.

## Three retained failures and minimal follow-up

All three failures occur in unchanged tests/contracts/test_report_a_r4a0_source.py, blob 9e89bd74dce87a17b9f5d97940b7b2ad68061efd. Their subjects match the fixed base and both returned manifests.

| Failed node | Verified cause | Remaining action, outside this repair |
| --- | --- | --- |
| test_canonical_krylov_frame_has_a_deterministic_so3_section | Test line 32 requires LF after Let. R3 manuscript line 286 contains the same positive-diagonal Cholesky sentence on one line. | Separately authorize a source/assertion representation reconciliation preserving the deterministic proper-oriented section and all mathematical premises. |
| test_t2_cayley_hamilton_source_has_no_truncated_fraction_tokens | Test line 45 expects a literal backslash-frac. T2 line 234 contains byte 0c, U+000C FORM FEED, followed by rac. | Separately authorize a bounded correction of the malformed fraction tokens; retain the existing assertion and exact old/new source provenance. |
| test_r4a0_repair_preserves_report_scope_firewalls | Test line 55 requires HEALPIX; R3 line 48 spells HEALPix while still denying a finite-HEALPix no-go theorem. | Separately authorize representation reconciliation while keeping the explicit negative firewall. |

R3 manuscript blob: 16f8fdd4db4dac384c5c64a8d3f86e0dbbf62e34.
T2 theorem-pack blob: 8e66a7bb698932a060cc60057e3541b782167d83.

The same T2 form-feed corruption occurs on LF-based lines 234, 241 and 245, in the displayed Cayley–Hamilton relation and the two following moment formulas. This review checked all three actual byte occurrences. The original test stops at its first failed assertion on line 45: later assertions did not execute and are not counted as extra pytest failures or passes. The T2 defect is not merely line wrapping. The other two failures expose exact text representation mismatch; their intended source assertions are visibly present, but the original failures are retained.

No further source/test repair, skip, bypass or retry was performed. These are source/assertion failures, not dependency failure, a new mathematical counterexample or Q/O theorem acceptance. The consuming discussion should authorize any next bounded source/test repair separately, then select the necessary existing replay. The same LOCAL_CODEX remains the authored-source writer.

## IDs, protected source and evidence limits

The reviewer rehashed the actual fixed T9 ledger and exact returned sorted/LF-terminated ID bytes. All 30 IDs are unique; SHA-256 is e103c581ce353b5102af81834831ac292105f18699671e8eb75b171acd97f01e. Citation rows have the same 30 IDs; the unchanged bibliography and R3 citation registry have 17 keys. The forty-claim candidate's separate bibliography/bundle is not substituted here.

The canonical ledger remains byte-identical, with canonical_sorted_id_sha256 null and PENDING_SUPPORTED_RUNTIME_REPLAY unchanged. The computed digest is evidence only.

The original before/after manifests each contain 5811 tracked paths. Their full path/mode/base-blob set matches the freshly fetched complete base Git tree; all 5810 noncontract paths retain their recorded blob and SHA-256. The base tree was independently reconstructed. Complete payloads for 22 relevant current files were fetched and rehashed against both manifests, including all eight tests, the workflow, pytest.ini, the seven bound sources, T2 and revision-2 manuscript. The complete historical citation payload was also rehashed. This is not a fresh rehash of all files on the user's workstation.

Returned main-checkout HEAD/status records agree. Venv/data preservation is the local executor's statement plus relevant source/command evidence; work did not access or rehash the whole environment or data. The supplemental hash-command record contains a prose stdin procedure and a main-checkout cwd, not literal stdin or an absolute resolved ledger input. Its logged ledger SHA-256 and exact output ID bytes match the fixed source independently checked here; the full suite's existing hash node also passed. This limitation does not imply an unrecorded runtime PASS.

## Publication and unchanged boundaries

Publish only the exact one-file candidate plus this run's text evidence on implementation/htt-authority-citation-reconciliation-20260905-r1, parent 9a37311cc97a9f670ab6c7f300b0cf74ccabe121, targeting review/htt-r4a1er-local-result-scope-20260905-r1 as a Draft PR. WORK_THREAD is the sole publisher. Existing PR449/452/453 refs, source and original evidence are preserved. The publication receipt separately identifies the resulting commit/tree and all payload readbacks.

Full authority acceptance remains false. Canonical is T9 v4/30; candidate is 40. New CAS executions: 0. R2, K2FER1, K2FR and K5 were not repeated. No observation, finite-null, physical-response, finite-HEALPix containment or forty-claim acceptance follows. Existing PR450/451 reviews, applicable PR444/error-class limits and workflow-pin freeze work stay separate, without new execution or queries in those lanes. No ready transition, merge, canonical or scientific-publication promotion is granted.

