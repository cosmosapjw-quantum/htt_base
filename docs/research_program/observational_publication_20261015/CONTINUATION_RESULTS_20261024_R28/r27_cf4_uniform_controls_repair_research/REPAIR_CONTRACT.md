# One bounded correction of the CF4 quotient covariance control

This is the read-only scientific framing and approval for one targeted lower-tier repair and continuation of the already acknowledged, unstarted consumer. It is not an executed test result, scientific admission, a new consumer allocation, an ultra escalation, or a reset of a failed attempt. The actual research packet is 2d095345d88e976aff3933f2938bf63570afa8dee0849b3698908360c2e2b748; task R27-CF4-UNIFORM-SUPPORT-CALIBRATION-QUOTIENT; input sha256:570383ac224808090c57b356ee21cc7f114a27d712ee725c5c42850bf00d61fd. Research agent /root/r27_cf4_uniform_controls_repair_research; requested gpt-6-astra/xhigh, observed UNKNOWN. The lower coding worker is the existing numeric owner; root requests gpt-6-sol/high and must record observation separately. No children or simultaneous production writers.

## Frozen authority and exact first failure

NEXT_CONTRACT.md remains SHA256 80611699ffb4226b295c5dcb3a0c8ba9e5526a3f807747a17f24ba53b06c2678 and PRE_ACK_CLARIFICATION.md remains SHA256 52fea066faafef05cdbd7db391897861b9cb0fbf8ca8b35e17a2cf4ab1b59143, both in /mnt/extdrive/workdir/htt_open_data/r27_remaining_science_frontier_independent_audit/. Their full scientific and source requirements remain binding. The numeric directory is /mnt/extdrive/workdir/htt_open_data/r27_cf4_uniform_calibration_quotient_numeric/.

Original source identities: consume.py d8c3a7526f97f196bcc29b5fbd0ead26aadb1a0230268ea9f2736074c8fcf798; test_controls.py 9999b21ba314ba9cf2cc1724155f5dbaae56dbe5dcaa56e693760053fd4f064b; runner.py ee00bff886ba8cc4595e1cf36bc9ee6c48ac2eb056b30f33220658c9ae4f9312. Original execution packet 696c2d10e057c4481e831218e1a6d57d41b2b29e0908080445088302d26b213e and candidate a67ab06bced8fb40a6e0eef0692bb38cebf757ae76005c4bed76905c53c0c92d are historical evidence and are not rebound.

The actual first failure is test_controls.py:76: norm(k @ cross @ ka.T) = 3.9630100305325295e-17, failing an absolute 1e-24 comparison. The covariance-only assertion immediately before it passed; the transpose cross term, direct-channel shift and row/channel permutation assertions after it were not reached. The original raw receipt records only test_controls.py as started. No actual consumer, real-data fit, rendering or scientific output has started. The raw directory contains only WHOLE_COMMAND_RECEIPT.json, test_controls.stdout and test_controls.stderr; products and FIRST_FAILURE.json did not exist at inspection.

The defect is CONTROL_ASSERTION_ABSOLUTE_THRESHOLD_CONFLICT, an implementation-level mismatch with the frozen test criterion. It is not a counterexample to the exact ideal-operator identity and it is not proof that the binary operator is exact. Cross terms are linear in E=K_hat A; their rounding residual need not meet a squared-small-residual absolute threshold. The actual nonzero 3.9630100305325295e-17 must remain visible, without rounding it to zero or asserting that the intended normalized check already passed.

The frozen contract says verbatim: “Report raw/scaled errors; algebra checks use normalized≤1e-10, source/information checks as above.” It also requires: “A small joint residual/calibration PSD covariance with nonzero cross block verifies cancellation of both calibration and cross terms by K A=0; do not assume independence to obtain the result.” The pre-ACK clarification states that numerical residual checks do not establish K_hat A=0, or unrestricted-Gamma protection of the stored binary matrix.

## Exactly allowed scientific test correction

Create numeric/repair_01/ and copy the original test_controls.py to test_controls_repair.py there. Preserve the original file and all other test logic. Within the copied failed method only, replace the three absolute 1e-24 covariance comparisons with the following precise normalized binary64 consistency checks, plus raw/scaled diagnostic reporting. Do not change fixture values, estimator routines, source family, rank policy, the other assertions, or pass criteria for completed methods.

Use the Frobenius norm for every matrix and the ordinary Euclidean norm for vectors, matching np.linalg.norm with its default matrix norm and the existing consume.scaled_residual implementation. Let

    E = K_hat A
    Gamma = H_eta H_eta^T
    X = H_e H_eta^T
    T_cal = E Gamma E^T
    T_cross = K_hat X E^T
    T_cross_T = E X^T K_hat^T

Retain the original H_e and H_eta entries. The joint covariance is the Gram matrix of the stacked factors [H_e; H_eta], so it is PSD in its mathematical factor definition; X is nonzero. This finite deterministic fixture is not a newly admitted physical covariance law or a cap on arbitrary Gamma.

Define the denominator scales using the unannihilated factors, never the tiny response E:

    s_cal = ||K_hat||_F^2 ||A||_F^2 ||Gamma||_F
    s_cross = ||K_hat||_F^2 ||X||_F ||A||_F
    r_cal = ||T_cal||_F / max(s_cal, finfo(float).tiny)
    r_cross = ||T_cross||_F / max(s_cross, finfo(float).tiny)
    r_cross_T = ||T_cross_T||_F / max(s_cross, finfo(float).tiny)

For this nondegenerate fixture require the raw norms and the denominator scales to be finite and each scale strictly positive. Every r must be finite and <=1e-10. Report the three raw norms, denominators and normalized residuals at full ordinary floating representation. Retain the measured ||E||_F and its existing K/A normalization as a diagnostic if already available. The denominator is a product scale for the original multilinear operator expression; it must not be ||E|| or a fitted scale, and may not depend on whether the resulting test passes. This explicitly instantiates the original normalized algebra criterion; no rank threshold, source check, information tolerance or scientific acceptance is relaxed. No numerical result is predicted here.

All earlier assertions within the failed method and all previously unreached assertions after the covariance block must execute unchanged. Run only this selector:

    /home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python -B -m unittest -v test_controls_repair.QuotientControls.test_full_rank_uniform_invariance_and_cross_covariance

Use cwd=numeric/repair_01; resolve `consume` to the unchanged original numeric/consume.py (explicit source path binding/PYTHONPATH), not an installed duplicate or copied algorithm. Merely importing unittest must not run the other test methods. A metadata-only copied-test diff and source binding are allowed preparation; do not execute a preview test before the single acknowledged continuation.

## Reuse of completed evidence and output ownership

The original raw stderr SHA256 6fa4a6eb07357c158548857e32cfb7065323b5bd928cc64c5a010f2ca2cf0a77 and WHOLE_COMMAND_RECEIPT.json SHA256 25df7205e60f5ec707b3cff1b2e55ac88c495c74121506214c043fe786290a5c bind these three PASS methods under the unchanged consume/test source identities:

- test_exact_support_decomposition
- test_rank4_rank0_and_unstable
- test_stf_decode_rotation

Reuse them; do not rerun them, including as part of a full unittest suite. The failed method itself is one incomplete control and may be executed once in full to reach its remaining assertions. The original stdout is an empty file with SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. The resource receipt is ACTUAL_LIFETIME_RESOURCE.txt SHA256 f692d3c4e4c4145df63a78dbe75aff41c877692bee575f2518c52507d22a8aae. Preserve all of them, original RETURN/ACK/packet files, original test and runner, and the first failed assertion.

The worker owns the numeric directory only and is not alone in the shared checkout. Make the copied repair test, a continuation runner and its new receipts/logs under numeric/repair_01/. Do not modify repository files, controller state, original INPUT.json or original consume.py. No Git action, source replay, old consumer, old source reconstruction, old scenarios, extra calibration map, Monte Carlo campaign, solver/ODE run or new input family is authorized.

If and only if the corrected failed method completes successfully, the same continuation runner executes the original unchanged command exactly once:

    /home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python -B /mnt/extdrive/workdir/htt_open_data/r27_cf4_uniform_calibration_quotient_numeric/consume.py

This is the original consumer's first execution. Its existing create-only output location numeric/actual_run/products is permitted because it is uncreated; do not rewrite any old logs/receipt. If its unmodified failure handler creates the previously absent numeric/actual_run/FIRST_FAILURE.json, retain that new failure too. Do not change its output-path binding or copy the consumer. The new runner must persist new stdout/stderr and its receipt under repair_01/actual_run, and fsync the new original-consumer products as well as its own logs/receipt. The original runner cannot be rerun because its create-only actual_run already exists.

## One continuation, unchanged cumulative account

Accounting parent R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE retains its 600-second lifetime cap. Before the failed control 177.80777764664458 seconds were used. The failed invocation is charged 3.485 seconds once, the maximum of available overlapping authentic caller/provider/host/kernel observations; the caller wall is nonmonotonic and must remain labelled that way. Current used=181.29277764664458, remaining=418.7072223533554 seconds. No failed work is removed.

The original consumer subcap is still 120 seconds, with 3.485 used and 116.515 remaining for this entire continuation, including imports, checks, the corrected control, actual consumer/render, output persistence and wrapper termination. The independent result-checker reserve is still 30 seconds unused. The original 150-second aggregate has 146.515 seconds remaining. The same bank must also cover both. Root reconciles any intervening authentic charge before actual continuation ACK and lowers the allowance if necessary; a stale snapshot must not increase it.

Prepare the complete copied test and new runner first, bind their source hashes and this contract in the actual continuation packet, then execute one instrumented command. One BLAS thread; RSS<=2GiB. Start caller/host whole-command timing before Python imports, and keep it running through child exit/reap, all new output fsync, receipt fsync, wrapper exit and kernel time receipt. Use the official existing interpreter and an externally started /usr/bin/time -v observation. The new wrapper uses the remaining 116.515-second all-inclusive allowance and a 110.515-second child deadline, leaving the existing six-second closeout reserve. Charge actual observed time, not the reservation. Any tighter reconciled allowance reduces both appropriately. No invented 0.5-second tail cap or unmeasured zero finalization cost is allowed.

The runner records both started commands, raw return codes, deadline/RSS stops, monotonic intervals and actual resource metadata. Flush/fsync captured output and wait/reap every child. Charge overlapping timing envelopes once by their maximum, retaining each observation and distinguishing monotonic measurement from nonmonotonic caller observation or a conservative bound. If the genuine total exceeds the residual cap or timing is not established, preserve the result and return the exact resource HOLD; do not claim budget compliance, rerun, or alter the account. Final receipt-writing/timing cost cannot be silently excluded. If a conservative finalization bound is used, state and charge it explicitly instead of calling it observed. A six-second reserve is not proof that finalization consumed six or zero seconds.

Stop on the first remaining control failure, any source drift, rank ambiguity, real-data validation failure, resource limit, or output problem. Preserve its raw counterexample and return to the controller with no automatic retry. Completing the control alone is not task completion: when it passes, start the already authorized original consumer in the same bounded continuation.

## Frozen scientific acceptance and immediate downstream transition

Retain the complete original input seals; all 35,970 selected IDs/order and channels; support-simplex family; original H0=74.6, Omega_m=.3153, five STF basis columns and fourteen nuisance columns; original D working metric and centring; exact structural mixed-row zeros; nuisance column normalization; SVD rank counts at 1e-12,1e-10,1e-8 with unchanged external preprojection target scale; NUMERICAL_RANK_UNCERTAIN/partial/rank-zero branches; saved-F agreement rtol1e-9/atol1e-10; normalized operator checks<=1e-10; information monotonicity scaled1e-9 and un-clipped generalized values in [-1e-9,1+1e-9]. This repair does not edit those calculations or tolerances.

The source decomposition A=C+E_M A[M,:] and the ideal K_star annihilator remain exact mathematical model identities. The computed K_hat residuals, signed estimates, tensors and working covariance remain numerical selected-source outputs. Exact annihilation/protection of the binary matrix under unrestricted Gamma, finite calibration covariance bounds and binary cross-term cancellation remain NOT_ESTABLISHED. No Gamma cap or mean-error cap is supplied. K_hat A that is small or nonzero must never be reported as exactly zero. Physical residual covariance, selection, PV/source-null law and H02/H03/H04 physical claim gates remain unresolved; no native solver/family or CAS certification is admitted.

After execution, root gives the exact final copied-test/runner diff, unchanged original consumer/input, raw first and continuation outcomes and final product identities to a fresh independent reviewer who did not author or frame this repair. Its already reserved <=30-second small checker does not rerun the old CF4 campaigns or the completed adjacent controls. Its decision is independent and scoped to the actual output, not supplied by this repair approval. Then root returns the new apparent observable or exact residual HOLD to the original H02 decision and continues independent READY branches. Baseline22/42, restricted alternate23/42, R9 UNKNOWN, old SMICA/CF4 failures and broader claim ceilings remain preserved.
