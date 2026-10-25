# Exact-factor zero-leverage metadata: one bounded copy repair

Decision: approve one metadata-only repair of the existing candidate, followed by one fresh independent changed-candidate closeout. This contract resolves NEW_ZERO_LEVERAGE_MASK_MISMATCH; it changes neither the observable nor its numerical or exact values. Scientific admission remains pending the closeout.

## Bound identity and evidence

Campaign: 2b9c0b11dab33758e0ad8c7711376ae29949a345e111df7820fcc8c7cac75ea4. Task: R28-CF4-EXACT-CALIBRATION-FACTOR-ACTUAL-CONSUMER. Research packet: 7867948ee59b8055a9e751498730e9283f0911b82056b7b9dbc79200d1cb55e2. Input identity: sha256:db1f79b73d50c9ea3dfbfa814d6c9759b6bedaa7851fc8f9224266fc0b20abe5. Requested researcher gpt-6-astra/xhigh; observed runtime UNKNOWN.

- ACK/GO packet: /mnt/extdrive/workdir/htt_open_data/r28_exact_factor_dispatch/ACTUAL_ACKNOWLEDGED_METADATA_RESEARCH_PACKET.json; SHA256 e06b988182716ebc661d2a4a634a212aed94ffb00d89aeb908fa03d67496fbd9.
- Unchanged original scientific contract: /mnt/extdrive/workdir/htt_open_data/r27_remaining_science_frontier_independent_audit/EXACT_CALIBRATION_FACTOR_CONTRACT.md; SHA256 1ae79d17ba8ce31b10ac9a6182771b4dd9587f915b9b76999e6fa957fa28f4ba.
- Original candidate RESULT: /mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_numeric/actual_run/products/RESULT.json; SHA256 ce46049e719e15749ee9adf8b5101f5cb4f439de6751a6285fa26eeeb6920e02.
- Original factor: same products directory, FACTOR.npz; SHA256 b152c216d287d278014b3f94cbe0d3d1d74a1312cb42b2555d2bf59d47209a80.
- Actual first-failure review: /mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_actual_review/RESULT.json; SHA256 4b654b613105679a0d3e0c93eed82d5c781afc44b37d336da05d59876c55b312. Its check.py:161 fails NEW_ZERO_LEVERAGE_MASK_MISMATCH; factor.py:176 copied the parent mask.
- Settled account: /mnt/extdrive/workdir/htt_open_data/r28_exact_factor_dispatch/ROOT_ACCOUNT_HEAD_AFTER_FIRST_REVIEW_FAILURE.json; SHA256 dcc8baee536be28fdd62722334a62ba452d8971b811222a562aac82f30390e31.

The retained checker reached line161. Earlier assertions completed, including full five-component exact contractions, exact sums/correction/price, display/tensor checks and numerical B/N responses. The later permutation, subnormal witnesses, final rehash and success serialization were NOT_RUN. Do not label the failed whole review PASS. Row1484/group11274 in the one-singleton SBFm channel is a concrete missing exact-zero witness. The complete mismatch set is UNKNOWN until the repair's full mask derivation; do not presume exactly one erroneous row.

## Exact mask definition from the stored factor

The unchanged factor defines K_fact=L D_diff over exact rationals named by the finite binary64 L entries. Each integer difference uses the nonreference row i and its same-channel reference r(c). No rounded materialized reference coefficient is authoritative.

Derive an n=35970 boolean full mask Z, retaining every row and its original ID/order:

1. Every mixed row has Z=true because its column in D_diff is structurally absent.
2. For each stored nonreference position j, its column is exactly L[:,j]. Set Z[i_j]=true iff every finite stored coefficient equals zero exactly. Signed binary zero is rational zero; nonzero subnormals remain nonzero. Reject nonfinite values. Do not use a norm, squared norm, SVD, magnitude threshold or approximate equality.
3. For each nonempty channel c with reference r(c), its column is the negative exact sum of L[:,j] over that channel's nonreferences. Sum all five components using exact dyadic integer/rational arithmetic and set Z[r(c)]=true iff all five exact sums vanish. An empty sum is zero, which handles a one-singleton channel. An empty channel with reference=-1 has no row; never index -1 as a reference.
4. Validate the original mixed/reference/nonreference sets partition the full cohort, and that stored integer index pairs preserve their original channel support. Do not rebuild the references or support, drop rows, change weights, or infer masks from the old carrier or old rounded K_hat.

Define current extra_zero_leverage_mask = Z AND NOT mixed_zero_leverage_mask. Store Z as exact_zero_leverage_mask. Preserve the original extra_zero_leverage_mask bit-for-bit under legacy_parent_extra_zero_leverage_mask, whose meaning is inherited parent K_hat metadata, not current factor leverage. These definitions cover exact reference cancellations as well as the singleton-channel witness. They do not certify any response, rank, covariance or physical law.

## Allowed new candidate and invariant payload

Use only the bound original factor/result and retained evidence. Write a NEW candidate under /mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_numeric/metadata_repair_run/products/; implementation/receipt may occupy sibling paths inside that metadata_repair_run directory. Never overwrite or relabel actual_run, factor.py, the original inputs, previous contracts, or first-failure review. The lower worker is not alone and must preserve other edits. This research agent only writes its own research directory.

For the new FACTOR.npz, replace only extra_zero_leverage_mask and add exact_zero_leverage_mask and legacy_parent_extra_zero_leverage_mask. Every other array must retain its dtype, shape and raw element bytes, including L, y, d, all IDs/support/index arrays and the full signed five-tensor basis. Container hash/size will change; that is an explicitly authorized generated metadata change, not a change of source identity.

For the new RESULT.json, preserve every existing field and value except factor_product_sha256 and factor_product_bytes, which must bind the new factor. Add one metadata_repair object with original factor/result identities, this contract identity, mask semantics/counts, complete added/removed mismatch row indices and group IDs relative to the inherited mask, the SBFm witness outcome, and the unchanged scientific-payload comparison result. Preserve the existing pending-independent-review status and claim ceiling. All exact numerator/denominator values, old channel sums, actual five-vector, correction/price, display approximations/errors, tensor, parent differences and response_numerical are copied unchanged. Compare unchanged JSON subtrees exactly, including binary64 float bit patterns where numeric representation matters; do not recompute their values.

Perform only mask derivation, packaging, unchanged-array/JSON comparison, hash/size binding and whole-command receipt. No catalogue/source fit, full data contraction, old controls, design rebuild, SVD, numerical B/N recomputation, producer import/execution or producer replay. Exact reference sums for deciding zero-column metadata are the sole necessary coefficient arithmetic; they are not a new exact five-vector evaluation. Fail once on any unexpected identity, partition, invariance, time or memory issue; preserve that raw evidence and return to root without retry or widening the repair.

## Fresh independent closeout

Root assigns a different independent reviewer who did not author this repair or its framing. Its new artifacts belong in /mnt/extdrive/workdir/htt_open_data/r28_cf4_exact_factor_metadata_repair_review/. The reviewer independently derives the entire exact mask from the saved factor, checks all three mask meanings and the complete mismatch report, and verifies every unaffected array and scientific result field against the immutable original candidate. It checks new product/result/contract bindings and final input hashes. This unchanged-payload comparison transfers the specifically recorded successful pre-line161 evidence; it does not convert the failed whole review into an earlier PASS.

Complete the originally unexecuted combined row/channel reference-remapping and exact subnormal/tiny-nonzero boundary checks using independently written small controls or the retained read-only definitions. No rerun of passed actual five-vector contractions or numerical B/N responses is needed or authorized. Targeted exact-zero controls should include a one-row channel, empty channel, a reference cancellation, and nonzero subnormal L, either folded into these controls or checked directly. No full producer/old-review rerun. Report actual reached checks and failures, not inferred completion. One fresh closeout qualifies the changed candidate only; do not create another review ladder.

## Cumulative limits and claim ceiling

Use the same R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE 600-second account. Settled use is211.39277764664456 seconds, remaining388.60722235335544. The unchanged exact-factor unit has consumer7.1/60 seconds used and review3/20 used; aggregate cap80 seconds. Approve ONE metadata repair command at most10 seconds, from remaining consumer52.9, and ONE fresh closeout at most17 seconds, the entire remaining original review allowance. No new60/20/80/600 allocation, borrowing from the other phase, new ultra, free retry or budget reset. Use1 BLAS thread and RSS<=2GiB. Charge every started command/failure once using root's authentic later head, external whole-command monotonic timing including persistence/reap, and preserved receipts; the quoted head is not authority to ignore later charges.

Acceptance for the repair is corrected full-factor leverage metadata, byte-preserved scientific arrays, unchanged exact/numerical result values, new identity bindings and the fresh scoped independent closeout within those remaining caps. This research approval alone does not pass that acceptance. Exact annihilation remains limited to the existing rational factored functional and fixed additive support-simplex calibration family. N/B response, unrestricted nuisance, residual covariance, selection/PV/null, original H02/H03/H04, physical/native-family and old four-axis CAS statuses remain unchanged. No permanent gate or new original-science completion is created.
