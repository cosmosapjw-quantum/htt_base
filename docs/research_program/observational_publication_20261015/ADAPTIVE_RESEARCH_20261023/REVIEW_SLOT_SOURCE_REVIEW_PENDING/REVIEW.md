# Independent source review: HOLD

This decision binds external controller SHA-256 `c44e0cd153831358b51766f3084ad85f7c18737c3188c8a47fa8675a2a2e8302`, focused test SHA-256 `c654cd378b4adc2bb38cd8c1a1d097dcce75e0fbc6dff008ca52a8e938ff6282`, controller diff SHA-256 `424f0f74a18f81828243e60f37a7cb37fafc38a8c9e9cb6e9a3b28c287a977bb`, and repair contract SHA-256 `640e130017170175c36c24e13161c23a917875bc86b6c3c8b250b3c65cb47aec`. Canonical baseline remains `d682f64d9aefba6251dc75037588669c0d193fc1ac12bf348bdfc02094cb46e5`.

Requested reviewer: gpt-6-astra/xhigh. Observed runtime: UNKNOWN. The reviewer did not frame or implement the candidate. Repository skills/harness were audit subjects, not approval authority. All writes were confined to this review directory. No real task was reserved, acknowledged, recorded, replayed, or dispatched. No science code/result was reviewed or modified; no Git, installation, native solver, numerical fit, or download operation occurred.

## Blocking findings

### F1 — P1: actual quotient candidate inventory is unsealed

Candidate controller lines 1224–1227 recognize only `files`, `products_sha256`, and `products`. The actual quotient manifest SHA `55e9d6bd8d9ca98d5736baf9327a51d00d8c01dac14fa8de63a26cb489022404` declares ten products through `inventory: [{path, sha256, size_bytes}, ...]`; its task has empty `candidate_products`. The accepted context contains one candidate seal, for MANIFEST.json, and omits all ten products, including the 32,254,030-byte INTERVALS.npz, RESULT.json, source code, and receipts.

The exact actual manifest and products were only read. A disposable manifest using the same inventory form was then tested: changing its declared product preserves context equality and `_review_context_matches=True`. Full disposable controller transitions subsequently return the planned packet, accept ACK, and record successful completion after the product changes. ACK and outcome mutate their fixture state rather than reject it. See `RAW_PROBES.json` and `LIFECYCLE_AND_BOUNDS.json`, `inventory_replay`, `inventory_ack`, and `inventory_outcome`.

Required repair: generically parse this actual inventory form with the same path/SHA/size/conflict/overlap and 64MiB candidate checks as the existing supported forms. Mixed inventories must all be checked. Unknown or malformed present inventory forms must refuse. Do not rewrite the frozen scientific manifest or special-case its task or hash.

### F2 — P1: explicit contract role does not cause metadata traversal

Lines 1043–1044 accept `role=contract` or `role=manifest`, but lines 1094–1095 skip every non-`.json` file irrespective of those roles. An explicitly sealed `typed_contract.dat` containing JSON `inputs` is accepted as an opaque source. Its nested leaf can be owned by the active acquisition and remain absent from the review closure.

`RAW_PROBES.json:typed_contract_nonjson` reproduces accepted context plus omitted acquisition-owned leaf. Required repair: explicit contract/manifest type must control bounded JSON traversal irrespective of extension, or the unsupported combination must refuse before approval. Preserve existing untyped non-JSON leaf behavior and exact frozen property-table compatibility.

### F3 — P1: mapping-key alias is discarded before final race check

Lines 1163–1166 verify that a source inventory mapping key and embedded `path` resolve equally, then `{ "path": name, **value }` discards the mapping key when `value` contains `path`. Only the embedded path is retained in `source_aliases`. In the disposable probe the key is a symlink initially resolving to the embedded leaf; while that leaf is being hashed, the key alias is retargeted to an acquisition-owned, same-byte file. The final context is still accepted because the key alias is absent from the final alias check.

`RAW_PROBES.json:inventory_alias_race` reports all four observations: acceptance, discarded key alias, triggered retarget, and now-owned target. Required repair: retain both declared lexical aliases and their resolved identities, validate each declaration and each overlap before reads, and recheck every alias before returning the proof. Deduplicate hashing only, never declaration/alias validation. Refusing a redundant embedded-path form is acceptable only if no frozen actual input requires that form.

### F4 — P2: the previous 256-local-scope limit is exceeded

Lines 1048–1049 apply the bound before owned paths are included; lines 1172–1175 then append owned paths without checking it. A root contract plus 255 distinct local inputs plus one declared owned candidate path yields an accepted context with 257 read paths. The original code counted owned paths before traversing inputs.

`RAW_PROBES.json:scope_bound` reproduces 256 source seals and 257 read paths. Restore the existing combined declared source/owned-scope limit. Keep separate candidate inventory behavior as prescribed; do not silently reinterpret the existing bound.

## Successful checks and limits

- Reproduced original actual tag refusal and isolated oversized data-leaf refusal against the frozen canonical baseline. Disposable original nested, source inventory, mixed URL/local, and same-size source mutation defects also reproduce on baseline and are corrected by this candidate.
- Exact tag candidate `3d2e96774c28cb5c3aa4d00757e022d61d1d696f50ff50e1b4dcdd31fc181793`: 45 source seals, 26 candidate seals, 72 read paths, all 25 declared candidate members sealed.
- Exact quotient candidate `55e9d6bd8d9ca98d5736baf9327a51d00d8c01dac14fa8de63a26cb489022404`: 19 source seals, 1 candidate seal, 21 read paths; missing products are F1. These contexts use a read-only current STATE snapshot with only the running S4 task's scheduling state changed to held in memory. This is a scheduling fixture, not real dispatch eligibility while S4 is running.
- All 37 frozen declared source records were independently rehashed: SHA, size, resolved aliases, context seals, and context aliases match. No actual input byte mismatch was found.
- Source mutation is rejected at plan replay, ACK, and outcome with fixture state unchanged. Same-byte source symlink retarget tests pass. Overlap-before-open controls pass for nested records and all tested source inventory forms.
- Separate 40MiB source and 40MiB candidate proofs pass. More than 64MiB in either budget refuses. Metadata per-document 1MiB, aggregate 4MiB, 64-document, and depth-16 refusal probes pass. A source-growth-during-sealing probe refuses atomically.
- Full selected candidate/controller/checkpoint run: 102 passed, 6 skipped, 105 subtests passed in 14.10s. Five frontier skips arise because external module-relative production snapshots are unavailable; the checkpoint live-acquisition case is conditional on a historical running state. These skipped tests do not prove current live lifecycle execution. Exact current tag/quotient inputs were tested separately above.
- Ordinary serial semantics and existing candidate inventories are covered by that suite. This diff does not add numerical task dispatch or change route/cost identity.

Two additional observations are preserved in raw probes, not needed to establish HOLD: literal `https://` is accepted as a reference although malformed, and an exact-root `role=data` can hide source-bearing JSON content. The latter requires retaining the contract's explicit distinction between authorized raw data and dependency contracts; this review does not propose interpreting arbitrary data contents as new dependencies.

## Bounded targeted repair and closeout

One lower-tier repair may modify only the external candidate controller and its focused tests, under the existing repair contract, addressing F1–F4. The canonical controller remains root-owned. No scientific input/manifest rewrite, task recreation, numerical replay, allocation reset, validator relaxation, or expanded metadata/source/candidate bounds is authorized by this review.

1. Extend the candidate inventory normalization to the actual quotient `inventory` list. Preserve each form's declared hash and size, duplicate/conflict checks, complete read closure and overlap-before-read checks. Preserve ordinary serial behavior.
2. Honor explicit contract/manifest roles or refuse unsupported combinations. Maintain exact sealed property-table leaf compatibility and generic sealed future data support without granting extension-only exemptions or downgrading dependency contracts.
3. Preserve every mapping-key and embedded lexical alias through declaration validation and final alias-race checks; hash each resolved target once per source budget.
4. Restore the combined source/owned 256-scope bound and retain the separate 64MiB source/candidate caps and existing metadata caps.
5. Add focused tests reproducing these failures. For `inventory`, test every unchanged/mutation/removal/conflict/size failure at planning, replay, ACK, and outcome; reject transitions must leave state unchanged. Include active-acquisition product overlap rejection before read. Test both explicit metadata roles using non-json filenames, and the inventory-key alias race with same bytes.
6. Re-run the focused/controller/checkpoint suites once after the repair. On a read-only STATE copy, check the exact actual tag and actual quotient identities and all 37 frozen source records. Both candidates' complete inventories must be sealed and fit the separate budgets. Mutate only disposable fixtures using the exact inventory form for lifecycle counterexamples; never mutate actual scientific products to test rejection.
7. Return final source/test/diff hashes and raw evidence for independent closeout. PASS would cover this source repair only; real independent scientific result reviews, root integration, installation/activation, and original acceptances remain separate.

The `17/42` original acceptance, `18/42` analytic alternate, historical 48-task accounting, consumed ultra allocations, and `R9 UNKNOWN` are unchanged by this review. No source PASS or scientific admission is issued.
