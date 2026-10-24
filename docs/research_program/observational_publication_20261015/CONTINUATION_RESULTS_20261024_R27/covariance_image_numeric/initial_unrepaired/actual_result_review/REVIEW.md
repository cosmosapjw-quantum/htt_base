# Independent generic covariance-image implementation review

Decision: **HOLD — one reproduced numeric blocker**. Candidate `sha256:aa2b12403a41d999d805b7efba0d7233879a42b2847b45346a5e35258d4eac67` must not receive generic-interface acceptance before the bounded repair below. This is a read-only review of the actual implementation and first execution, not a controller result packet or scientific admission.

Reviewer: `/root/r26_covariance_image_actual_result_review`. Requested runtime: `gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`. No children, repository/Git/controller mutations, consumer rerun, actual CF4 execution, or implementation repair were performed. Review outputs are confined to this directory.

## Blocking finding

**F1 — high severity, reproduced: norm underflow manufactures a finite zero upper bound for an unbounded covariance class.**

Path: `/mnt/extdrive/workdir/htt_open_data/r26_covariance_image_capability_numeric/covariance_image.py`, lines 249–256. The function computes `v=m.T@u`, then `norm=np.linalg.norm(v)`, and chooses zero upper variance whenever `norm==0`.

Independent input: `M=[[1e-200]]`, `u=[1.0]`, `covariance_class='unbounded_psd'`.

Actual output: `{'status':'NUMERICAL_NEAR_NULL','upper':0.0,'exact_protection_proved':False,'response_norm':0.0,'diagnostic_threshold':1e-12}`. The nonzero stored scalar response admits the ray `Gamma_t=[t]`, whose variance is `t*M[0,0]^2`; its supremum over all finite t>=0 is +infinity in real arithmetic. The boolean disclaimer does not make the returned finite upper bound correct. The norm squares the tiny value and loses it to underflow. Existing `1e-12` tests do not expose this defect.

Raw evidence: `FIRST_COUNTEREXAMPLE.json`. The single probe completed with exit code 0, 3.43949557794258 seconds including imports, and 56.296875 MiB process lifetime high-water RSS from `ru_maxrss`. Numerical probing stopped after this first counterexample.

**Necessary repair condition:** changing only `norm==0` to a floating `v==0` check is insufficient. For `M=[[1e-200]]`, `u=[1e-200]`, the contraction itself can underflow even though the exact contraction of the supplied binary floats is nonzero. Cancellation can likewise round a nonzero contraction to zero. Certify the supplied finite binary-float contraction exactly, or return a truthful unresolved/null-uncertified result with no finite zero bound. A robust scaled norm alone does not certify dot-product zeros. Preserve literal zero-map behavior only when its zero follows from supplied values, and retain the distinction between that finite-array statement and physical structural protection.

## Resource evidence requiring the same bounded repair

**R1 — acceptance evidence gap, not an observed resource breach.** `/mnt/extdrive/workdir/htt_open_data/r26_covariance_image_capability_numeric/run_checks.py`, lines 25–32 and 79–96, samples `/proc/<pid>/status` VmRSS every 20 ms. Reported `64.7890625 MiB` is correctly labelled sampled, but cannot establish the frozen lifetime RSS <=512 MiB requirement. The first run's true lifetime high-water RSS is UNKNOWN; retain its successful fixture count and sampled metric without promoting the latter.

In the same authorized repair, collect the test child's lifetime high-water RSS on reaping, using `wait4` resource usage or the clean single-child runner's `RUSAGE_CHILDREN.ru_maxrss`, with explicit Linux KiB conversion. Keep the sampler as an early stop, and classify the final repair validation HOLD/FAIL if the lifetime peak exceeds 512 MiB or is unavailable. Do not overwrite or retrofit the original receipt with a new measurement. This calls for no separate governance task.

## Assumptions and conventions

The reviewed formulas assume real finite-dimensional matrices, symmetric PSD central covariances, a fixed Euclidean channel coordinate convention for the trace cap, and the full stated joint covariance including cross blocks. The fixtures use synthetic magnitude channels and outputs, hence covariance units mag^2. No physical frame, actual STF response, observational M7, mean model, covariance source, sampling law, or physical functional is supplied. A general trace cap is not invariant under an untransformed nonorthogonal channel reparametrization.

The exact interface rejects floating entries and undecidable spectral/PSD signs. The intended exact-fixture domain is concrete decidable values. A residual input-domain concern is recorded below rather than silently extending that domain to unqualified symbolic branches.

## Equation and definition audit

| Item | Review result | Evidence and limit |
|---|---|---|
| PSD/range necessity and pseudoinverse sufficiency | Consistent | `cone_membership` checks range separately; canonical lift is returned only on membership; zero/singular cases included. Indefinite input covariance is rejected as outside the supported covariance domain. |
| Canonical minimum trace | Consistent | Lift is M-dagger C M-dagger-transpose. Derivation fixes the row-space block; PSD null block has nonnegative trace and zero null-block trace forces cross-block zero. No least-norm cost substitutes for the range gate. |
| Trace versus spectral classes | Consistent | Trace support is cap times positive maximal eigenvalue, with rank-one attainer; spectral support sums positive eigenvalues and uses a projector. I2 separates joint membership despite equal directional maxima. |
| Singular Loewner cap and lift | Consistent | N=M G^(1/2); Z=N-dagger C N-dagger-transpose; lift G^(1/2) Z G^(1/2). The range and 0<=Z<=I proof covers singular G. |
| Full matrix unbounded support | Consistent in concrete exact cases | Positive eigenvector supplies a normalized PSD ray; negative-semidefinite K has support zero attained by zero covariance. |
| Right gauge versus protected output contrast | Consistent | Seven-channel fixture has a right-null common mode but full output rank five, and nonzero six-channel sum equal to minus anchor column. |
| Complete joint covariance | Consistent | Full Omega is required and tested for PSD; no default cross-block zero filling; pairwise-valid but jointly indefinite example rejected. |
| Known marginal directional bounds | Consistent | Bounds use sum of projected standard deviations and polygon lower bound; no division by zero in implementation; attainment assumes unrestricted PSD cross-block completion and fixed direction. |
| Near-null floating diagnostics | **HOLD F1** | Numerically computed zero is incorrectly used as a finite upper bound. |
| Law/physical functional boundaries | Preserved | Covariance does not create a law, Pi, coverage, posterior, physical x/F/G, or source-qualified response. |

## Fixture coverage and limits

All 15 rows in the frozen required table are represented across 13 test methods: the zero/range rows are grouped in `test_zero_and_range_gate`; canonical lift and null projector family; trace/spectral separation; singular Loewner cap; seven-channel gauge; full cross-block examples; tiny exact response; both three-scalar marginal sets; opposite vector-marginal extremizers; jointly indefinite correlation matrix; and the two variance-one laws with different strict tails. The optional floating check uses only 1e-12 and zero, leaving the reproduced extreme-scale failure uncovered.

The additional rectangular rational rank-deficient fixture and row/column permutations are present. Its trace check at test lines 60 and 66 compares returned trace with the same lift and permutation, rather than an independent expected value. For M=[[1,2,0],[2,4,0]] and the stated K, C=26*[1,2]*[1,2]^T and the canonical lift is (26/25)*[1,2,0]*[1,2,0]^T, with trace **26/5**. Add that independent expected value during the same repair test edit. Existing tests meaningfully check reconstruction and PSD; they do not prove universal minimality or all symbolic branches.

No further numerical test was executed after F1. Noncommuting caps, repeated eigenvalues, zero projected marginal variances, and arbitrary symbolic branches were examined only through the formulas/source; they are not additional observed fixture passes. Finite fixtures do not prove the universal propositions or replace four-axis CAS.

## Residual static domain concern

At `covariance_image.py:24-32`, real/finite assumptions alone do not certify every rank/zero branch. A real symbolic x can satisfy those entry predicates without x!=0. A generic pseudoinverse/rank for M=[[x]] may yield the x!=0 branch, while x=0 is also in the declared assumptions. This potential specialization error was **not executed** after the stop rule and is not presented as a second reproduced failure. The small safe domain clarification is to reject free-symbol inputs unless all branch conditions are explicitly carried/proven. Concrete exact algebraic fixtures remain supported. Unsupported symbolic parameters must not silently produce unconditional membership/protected-dimension claims.

## Source and actual execution evidence

Controlling hashes independently match: contract `f94671b022b1254fc7999000e9129db8fb9903bb3b84b823ee1f8a14ab8348b0`; derivation `7542fc2efa7a109560d2bd8a16e8867408589d0600dea916efc72178568710d7`. All eight source/input entries in the actual raw receipt matched live bytes. PREPARATION SHA is `f827413d29aebb63ce80ecfb94e1b0695b2edc85c44a760c43d12645857f9987`. The four candidate file hashes match RESULT and the packet-bound supplied candidate composite. No alternate verifier scripts/results or prior verdict were read.

Execution packet: `904f758af1f76063d6f46edf06f882e9d8bc6384c42035d0e028544824c23346`; task: `r26_covariance_image_capability_numeric`; allocation: `2b9c0b11dab33758e0ad8c7711376ae29949a345e111df7820fcc8c7cac75ea4/r26-generic-covariance-image-single-check-unit`.

Original runner evidence is internally consistent: `/usr/bin/python3 -m unittest -v test_covariance_image`, exit 0, 13/13 tests, unittest-reported 0.286 s, runner-observed 0.9285153758246452 s, no stop reason, sampled VmRSS 64.7890625 MiB. Five thread environment controls are set to one in the runner. These are configured BLAS-thread controls, not independent runtime thread telemetry. Raw stdout is empty; unittest evidence is in raw stderr. The preparation files remain historical NOT_RUN descriptions; actual ACK/receipt/RESULT supply the later execution state. Requested/selected identity remains separate from observed UNKNOWN. The implementation's custom RESULT outcome is factual evidence only and cannot auto-admit this node.

## One bounded targeted repair definition

Retain the same task/allocation and original source contracts. One lower-tier writer may repair `floating_directional_diagnostic`, its targeted tests, and the existing runner's lifetime-RSS measurement; update the handoff explanation and prepare new revision seals only as required by the existing controller mechanism. Preserve the full pre-repair source and first RAW_STDOUT/RAW_STDERR/RAW_RECEIPT/RESULT, plus this independent FIRST_COUNTEREXAMPLE. Do not edit the theory, physical conventions, exact mathematical formulas, tolerances, historical task identities, or any repository/controller state from the worker.

The repair must distinguish exact nonzero supplied binary-float contractions from uncertified numerical zeros, and must use scaled norm/variance arithmetic or truthful typed refusal when intermediate underflow/overflow would manufacture a finite wrong bound. For trace-cap diagnostic extremes, avoid an underflowed norm square multiplied by a large cap returning zero when the result is representable. Add small regressions for reproduced norm underflow; dot-product underflow; cancellation-to-zero; literal zero response; and extreme-scale trace evaluation or explicit typed refusal. Include the independent 26/5 trace value. Clarify/reject unsupported free-symbol exact inputs unless branch conditions are explicitly supported. No tolerance widening or scientific-policy change is allowed.

Run one bounded repair validation invocation, including the affected original fixtures and new targeted regressions, with one BLAS thread and <=512 MiB lifetime high-water RSS. Keep dimensions <=7, no full data consumer, fit, simulation ensemble, installs, or CF4 scientific execution. Stop on first substantive failure or limit, retain its raw output, and return the actual candidate and resource evidence to independent review. This review does not execute or self-admit that repair.

Budget: original check 0.9285153758246452 s + independent counterexample 3.43949557794258 s = **4.368010953767225 s cumulative**, leaving **55.631989046232775 s** of the same 60 s bank, before any further chargeable command. No historical source-response budget or task identity is reset. Metadata/source reads are not scientific check invocations. Parent acknowledged this conservative cumulative debit.

## Claim-tier implications and next transition

Generic-interface acceptance remains HOLD. No CF4 qualification, H02 closeout, universal theorem certification, four-axis CAS admission, covariance source, law, Pi, native solver result, or physical claim follows. Safe current statement: the original 13 synthetic fixtures passed; independent review then found a floating-point counterexample. After repair and actual independent review, the next scientific input remains **qualified signed M7 and stated bounded Gamma/Omega source**, with a joint physical response/law/domain additionally required for physical-functional work. Independent campaign branches may continue under the controller.
