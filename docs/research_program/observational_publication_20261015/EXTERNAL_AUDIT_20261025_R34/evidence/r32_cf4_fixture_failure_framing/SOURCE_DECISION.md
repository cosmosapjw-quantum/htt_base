# Source decision: R32 CF4 antipodal fixture and array-layout failure

Owner: /root/r32_cf4_fixture_failure_framing. Independent source/theory blocker framing only. Repository and original execution tree read-only. Requested role: Astra research review (gpt-6-astra/xhigh); independently observed runtime UNKNOWN / NOT_INDEPENDENTLY_OBSERVED. This preparation has no actual research packet, ACK, GO or controller result. The controller must bind and consume it after the real research dispatch. It is not permission to start numerical work now.

## Physics/math audit verdict

ONE_BOUNDED_TARGETED_REPAIR_JUSTIFIED, prospective and conditional on real controller binding, source freeze, executor ACK/GO, and fresh cumulative accounting. Two source findings explain the observed failure classes: the antipodal expectation has the wrong sign for the defined real-coefficient window; the FINUFFT call passes strided source columns and elicits same-dtype copying warnings. No numerical transform, fixture, independent checker, CAS campaign, benchmark or package import was run by this framing agent. Corrected numerical parity and all downstream controls remain UNMEASURED.

The actual earlier producer completed HOLD, not timeout. RESULT.json records passing full angular A/B and radial B/C comparisons, then driver.py:349 FIXTURE_ANTIPODAL_HOLD. The supervisor separately records NUMERICAL_METHOD_ACCURACY_HOLD from the C-contiguity warnings. Retain both first-failure records and all saved windows/stages as UNQUALIFIED. The old failed residual magnitude was not serialized and remains NOT_MEASURED; do not replace it with a theoretical or later-run number.

## Assumptions and conventions

Keep the original R30 contract, immutable scientific input sha256:5da5fe9adeee84d6615cf9127a91ff5bccff6172e43716680ae0792ef480c5d3, exact L Ddiff, real L/j/g/n/positions, positive exp(+i k u.x), k in physical Mpc^-1, positions in Mpc and window in Mpc^-1. Source/frame, J2000 directions, redshift/depth, fixed EH98 no-wiggle dust+Lambda background, angular normalization 1/(4pi), radial normalization 1/(2pi^2), and every prior tolerance remain fixed. No metric-signature, boost/tilt, physical-model or transfer change is proposed.

## Equation and definition audit

Write q_i(u)=j_i g_i (n_i.u) exp(+i k u.x_i). The window is w_a(k,u)=sum_p L_ap [q_i(p)(u)-q_r(p)(u)]. Because all prefactors and phases before multiplication by i are real, q_i(-u)=-conj(q_i(u)); a real linear difference and contraction preserve this identity. Therefore w_a(k,-u)=-conj(w_a(k,u)). Equivalently Re(w) is odd and Im(w) is even in u. The refactored representation agrees: F_ad(-xi)=conj(F_ad(xi)), the reference sum has the same property, and its outer factor u_d changes sign.

| Item | Status | Issue | Required fix |
|---|---|---|---|
| driver.py:109-126 direct_oracle | Source-consistent | Real n.u and positive phase implement minus-conjugation | Preserve formula |
| fast_science.py:178-206 run_pair | Source-consistent algebra | The final u contraction supplies the odd sign | Preserve formula and numerical method |
| driver.py:347-350 antipodal assertion | Defect established | It expects antipodal=conj(baseline) | Test abs(antipodal+baseline.conj()) with the identical 1e-9 relative threshold and 1e-30 floor |
| driver.py:377 diagnostic | Defect established | It reports the same wrong residual | Use corrected residual and preserve old-sign residual as labelled diagnostic |
| fast_science.py:192-193 setpts | Array-layout defect established | xscaled[:,d] is a strided column | Supply individually C-contiguous per-axis arrays with unchanged dtype and bit patterns |
| runner.py:220-226 warning rule | Frozen requirement | Any warning keeps the run on HOLD | Leave unchanged; do not whitelist, filter or suppress warnings |

No extra global i may be inserted to make the old assertion true. Such a change alters the frozen complex-window convention even if an auto-covariance happens to cancel the global phase. An identically zero field cannot discriminate signs; the algebra, rather than a fitted fixture expectation, determines this repair.

## Dimensional/sign/limit checks

The antipodal transformation changes neither dimensions nor normalization. At k=0 the real window is odd under u reversal. For the actual covariance integrand, w(-u)w(-u)^dagger=conj(w(u)w(u)^dagger), so its real part is unchanged; paired/unpaired angular integration remains a valid control. Real smoothing weights preserve this statement for all cross-radius blocks. No scalar, tensor coordinate, rank or smoothing block is removed. This is an elementary algebraic derivation for the defined finite sum, not a new four-axis CAS claim or numerical validation.

## Exact warning diagnosis

The installed, pinned FINUFFT 2.5.0 _interfaces.py:222-227 sends all six axes through _ensure_array_type. Lines 414-415 reject the wrong dtype; lines 417-430 test the C flag, emit the observed warning, then perform np.array(x,dtype=dtype,order="C"). The same-dtype copy preserves each finite binary64 element and its order. Preparing a tuple of np.ascontiguousarray(xscaled[:,d]) for d=0,1,2 before setpts performs that layout operation explicitly. Target arrays are already returned as a C-contiguous transposed matrix; preserve them, or apply the same no-conversion operation to each target axis. Require the same float64 dtype and bitwise element/order equality with every source view (including signed zero), and C-contiguous flags, as part of the actual producer's affected controls. Do not round, sort, rescale again, fold coordinates, alter targets or convert precision.

This removes the specific copying-warning cause by construction; it is not an accuracy certification or a prediction that no other warnings can occur. Leave showwarn=1, debug=1, both eps values and the blanket warning gate intact. The pinned local implementation is the primary evidence for this version-specific conclusion; no current package upgrade or external API assumption is needed.

## One bounded lower-tier repair plan

1. After the actual controller consumes this source decision, one lower-tier author owns a fresh sibling directory /mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window_fixture_repair. Preserve the entire original fast_window tree and its first failures. A sibling keeps driver.PREVIOUS pointed at the same normalization_repair evidence. Reuse the pinned dependency tree through a read-only reference/symlink; no installation or version change. Copy only the small frozen execution sources needed for this continuation, with old/new identities. Do not copy the repository or create a Git worktree.
2. Change only driver.py's antipodal assertion, its reported residual, and failure-measure serialization; change fast_science.py only to supply and verify same-value contiguous per-axis arrays. Before the antipodal demand, atomically serialize the corrected max-absolute residual, old-sign max-absolute residual, baseline scale, exact unchanged threshold/floor and eps/mapping identifiers. If an input/residual is nonfinite, preserve a typed failure without inventing a finite magnitude. The returned antipodal_max_abs must mean the corrected residual. Keep permutation, rotation, scaling, paired/unpaired, direct, Bessel, exact-reference/cancellation and common-field PSD checks unchanged.
3. Source-only preparation, static syntax/diff/sealing and all started command overhead are capped at 10 seconds in total. No transforms, separate fixture pilot or numerical import side effects before numerical GO. Retain byte-identical science.py, runner.py and existing checker source. This framing does not qualify the old checker as an independent reviewer; a fresh nonauthor must own actual numerical review and any separately authored checks.
4. Freeze new source identities and a new derived executable INPUT through the existing acyclic stable-core -> lineage -> real executor ACK -> ROOT_GO -> final INPUT plus detached sidecar binding. Bind this decision/result and the refreshed account in lineage; preserve the historical method_contract/method_result and original input/task identities. Prior GO, old consumed packet and old derived input cannot authorize this continuation. No source changes after numerical GO.
5. Run the complete producer once in a fresh empty output directory with a sealed whole-command cap at most 30 seconds. Include startup, controls, all A/B/C full windows at eps=1e-9 and 1e-12, matrix construction, fixture, fsync/reaping/receipt and any external wrapper overhead. Existing optional D rules and forecast/stop logic remain unchanged; do not force optional D. Retain one computing process, all threads=1, MemAvailable>=10 GiB and process-tree RSS<=6 GiB. No restart, tuning or hidden diagnostic producer.
6. Reserve the full 60 seconds for a different, fresh independent checker who did not author this repair or execute the producer. Check original/operator identities, both complex-window conventions, full saved spectral-to-joint reconstruction, changed representation and Bessel/direct controls, both sensitivity levels and all original convergence/support/PSD gates. Component PASS, if earned, leads to the already named conditional H02/M7 gap assessment; no extra assurance ladder is required.

## Why the affected main transforms may rerun

The changed source-column preparation is in run_pair, the actual API path for every cohort and fixture transform. The previous producer's main transforms used this path and emitted warnings. The old contract and runner define those warning-bearing runs as HOLD. Promoting their stored windows after only fixing the fixture would require a new warning-policy exception; none is granted here. Therefore the single fresh full producer rerun is justified by an affected-source defect and is the chosen repair. Old full matrices/windows remain useful diagnostic comparisons and retained evidence but do not supply qualified candidate stages. This explicitly avoids retrospective warning reclassification and keeps runner.py unchanged.

Reuse the separately frozen PASS scalar/amplitude/background controls and amplitude 765245.0820764016, verifying their bound identities. The existing background64 input construction may repeat to provide arrays but is not another normalization/convergence experiment. The three prior direct matrices remain identity-verified comparison controls. Do not rerun completed unrelated science units.

## Resources and stopping rule

Same R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE lifetime bank of 600 seconds; no reset/new bank/ultra. The cited settled head reports 450.4927776466445 used; parent reports a pending +2.4 enclosure correction, so the pre-framing lower bound is 452.8927776466445 used and at most 147.1072223533555 remaining. This is a lower bound, not a fresh GO account. Root must reconcile every subsequent actual command/tool window, including this framing and all controller/author/executor/checker closeout costs, and preserve the 69.9>20 preparation HOLD.

The conservative existing producer charges 14+17+14.2 remain. A further <=30 gives <=75.2 for these four producers, beneath 280; adding the reserved 60 gives <=135.2 beneath 340 for these listed producer/checker charges. Include any other applicable incurred charges; these arithmetic subtotals are not an audit of the whole bank. At the cited lower bound, maximum 10 framing +10 source preparation +30 producer +60 checker leaves at most 37.1072223533555 for other control/receipt costs, before intervening charges. This proves only prospective feasibility.

Immediately before GO, let R be freshly reconciled lifetime remaining after incurred charges and C the explicit reserve for all still-unspent controller/binding/receipt work, plus any not-yet-spent preparation. Seal P=min(30,R-60-C,remaining_280,remaining_340_after_checker). Require P>0 and a documented feasible complete producer; otherwise RESOURCE_HOLD without starting. Do not increase P after GO. An external whole-command observer must enforce the complete envelope because the runner's internal timer excludes some startup/closing work. No accounting debit may disappear because an assertion or preflight failed.

## Claim-tier implications, fatal blockers and safe claims

Safe claim now: source analysis establishes the minus-conjugation law for the frozen finite window and identifies a value-preserving way to satisfy FINUFFT's C-layout requirement. Not established now: corrected fixture pass, numerical completion, independently qualified covariance, rigorous all-target type3 error enclosure, physical x/F/Pi/Q/G_F or original H02/H04 acceptance. The latter remain UNDEFINED/HOLD; global_rigorous_type3_error_enclosure=NOT_ESTABLISHED; scientific_admission=false; acceptance_met=false.

Any changed immutable input, ambiguous implementation beyond these two findings, nonidentical axis values, warning, failed direct/Bessel/parity/sensitivity/support/PSD/convergence gate, cap exhaustion or unavailable independent reviewer returns the exact HOLD. There is no automatic second repair or rerun. The next executable transition, after real controller consumption, is the single lower-tier source repair and actual bounded producer, not another source-assurance review.

## Exact evidence identities

The input and all observed source/evidence hashes are recorded below and in PREPARATION_RESULT.json. The immutable scientific input identity is carried through the old frozen INPUT/runner; its original controller payload bytes were not separately rehashed here. All five execution source hashes were compared to the actual failed run's derived input. The original mathematical contract and INPUT_BINDINGS hashes were rechecked. No original numerical array file was loaded or recomputed during this framing.

- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/driver.py`: `fb30aeb48b1309c86882980a7a035ad1ff624c6c3627ada0392ee827c2cf04ee`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/fast_science.py`: `b160e3684bcebb4cb12a72d9fb19f70e478022a4a84e0a6244d01c2ad576e76b`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/science.py`: `ed9918ef9f2f12c7e6b04d5140ea8e51acd86c5fb6a541d80a27e9f42e3ad982`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/runner.py`: `6ff336ef28a90f6d3d6e315df4b48b055f16d944b5eec6dcbdd25c46c90deb38`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/independent_check.py`: `a825c6e9240d189fa456b5a4868c8cc95801a4983c2b8b90f60659894b9b32a2`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/_deps/finufft/_interfaces.py`: `508eff637d85e8aaaf06e4aff78dd75dbae749421cefea9efd03631be0dc5462`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/DEPENDENCY.json`: `3c47a0982825c6455ca571fa6cc64cfeb184149735f270057d729bad0eecac96`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/INPUT.json`: `ab9cc134af35b5206be7dbaedb46e8a9f398ac1a5a7a4be50c5f46e7ade467e3`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/actual_run/RESULT.json`: `a6e0c9d5538195d9b217725844eb4fbbd08fa7f966e9b299aa858098cc1b911b`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/actual_run/RUN_RECEIPT.json`: `75ae1f0a5bfffdb5f73cd42f89a21dc28759acd6c099c7976c636ba7f7bf99ef`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window/actual_run/stderr.log`: `8ef6d2938f0f53bae24ea25f9f72ee53fe43298352164c9e63e86e906fb0d3bb`
- `/mnt/extdrive/workdir/htt_open_data/r32_cf4_fast_numeric_executor/RETURN.json`: `65e70592cbc7a4983b6a5bd27590facfd5942eb182eaaea413e9616129f6ab66`
- `/mnt/extdrive/workdir/htt_open_data/r32_cf4_fast_numeric_executor/RAW_OUTCOME.json`: `b2561d2c80e04f06788b87a08e84a56e1edf90fbd9fabb4ae488429454eaff56`
- `/mnt/extdrive/workdir/htt_open_data/r32_cf4_fast_window_framing/CONTRACT.md`: `8765ad540341080dbb6da3ec02a0cc9179447df45448b7a12245954c879b4706`
- `/mnt/extdrive/workdir/htt_open_data/r32_cf4_resource_reallocation_review/RESOURCE_ADDENDUM.md`: `3eba5f296412d420d9ab5b0e72068c17cf56d6672f777515fe0159bd0e9fd530`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_framing/CONTRACT.md`: `29f5660bfee2feb379f01da2f51ddb7a87d416b05a2393f4ffaef5858fd6c8e7`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_framing/INPUT_BINDINGS.json`: `d5cfe88bf297ee7d7ab6ae5b6758c951cf2491b189de8c37e6756511232dc2c4`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_dispatch/fast_window_dispatch/ACTUAL_FAST_FAILURE_CONTROLLER_ADAPTER.json`: `41c13d5fffd442b183a5737cfa78560e8f09949cd86fd858f7be09454c5859b3`
- `/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_dispatch/fast_window_dispatch/ROOT_ACCOUNT_HEAD_AFTER_FAST_NUMERIC_FAILURE.json`: `7eac1e3e8eb5c1158f8c50987b1a7939b483dd1e44b75a7fa7c3a5c5d910b57c`
