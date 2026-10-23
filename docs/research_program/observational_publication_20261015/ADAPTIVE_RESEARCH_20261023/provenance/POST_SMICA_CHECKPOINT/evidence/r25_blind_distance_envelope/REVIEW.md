# Independent finite-library arithmetic review

Verdict: `PASS_FINITE_ARCHIVED_SCALAR_ARITHMETIC_ONLY`.
Original scientific admission and the inherited original 20-fit-cap violation (at least 21) remain `HOLD`.
Requested reviewer: `gpt-6-astra/xhigh`. Observed reviewer runtime: `UNKNOWN`.

For fold j, let L_jk be the exact binary64 value parsed from the archived component log_density and A_j the exact binary64 archived max_null_logdensity. Define q_jk=exp(L_jk)>0, D_j=exp(A_j)>0 and q_equal,j=(sum_k q_jk)/8. For all w_jk>=0 with sum_k w_jk=1,

    q_w,j/D_j <= max_k(q_jk/D_j) <= sum_k(q_jk/D_j) = 8 q_equal,j/D_j.

The first inequality is the convex-combination bound; the second follows from nonnegativity. Averaging with the fixed five weights 1/5 preserves both inequalities. Independent per-fold vertex choices attain the average of the fold maxima, so this is the exact supremum for the stated finite-library reweighting problem. No numerical optimization is required.

The archive seals, exactly eight unique scenario/model components in every fold, five folds with sizes [47,55,53,69,50], four null entries per fold, and equality of the archived denominator log with the maximum archived null log were checked. This checks the scalar structure and identities, not the accuracy of the fitted logs.

The independent implementation uses only Python integer and Fraction arithmetic. Exact rational subtraction forms L_jk-A_j. For d<=0, reduce x=-d/2^s to [0,1]. The alternating exponential series has S_181(x)<=exp(-x)<=S_180(x). The exact rational Taylor endpoints are rounded outward to the 10^-240 grid, then squared s times with outward rounding after each square. Exact rational averaging preserves enclosure. The reported 40-place decimals are separately rounded outward. No floating exponential function is used. This is a finite arithmetic certificate trusting Python integer/Fraction implementation, not a four-axis CAS or fitted-denominator certificate.

Certified intervals:

- tight_arbitrary_per_fold_convex_reweighting_maximum: [0.0006872371499359424075546278173516995795, 0.0006872371499359424075546278173516995796]
- exact_reconstructed_equal_mixture_average: [0.0001832183587553190271928827609298888449, 0.0001832183587553190271928827609298888450]
- eight_times_exact_equal_mixture_average: [0.0014657468700425522175430620874391107594, 0.0014657468700425522175430620874391107595]
- average_exp_archived_fold_logE: [0.0001832183587553190653340778335266106440, 0.0001832183587553190653340778335266106441]
- exact_reconstructed_equal_minus_archived_E_summary: [0.0000000000000000000436190873059855004060, 0.0000000000000000000436190873059855004061]

The tight bound is below 0.001 and therefore below 1 for every convex reweighting of this archived eight-component library under the fixed archived denominators and fixed equal fold average. That finite reweighting route is closed as a way to reach 1 on these values. The rounded archived Ebar is not the exact reconstructed equal-mixture mean: the positive discrepancy above is retained, with no tolerance-based identification.

This conclusion is pointwise. Normalization and training-only status of the component density functions remain inherited from the original input contract; evaluating archived scalar densities does not establish them. Held-out-data-dependent weights also satisfy the pointwise inequality, but do not thereby define a normalized training-only numerator or a valid e-value. The selected-source law, conditional-null domination, optimizer accuracy, physical interpretation, calibrated inference, and original acceptance remain outside this component. Full tensor coefficients, covariance cross blocks and component means remain in the sealed source RESULT; scalar evidence is a decision summary only.

No new fits, candidate module import/execution, old test suite, optimizer, data acquisition, source edits, STATE edits, or Git mutation occurred. Author blocker-research files and prior reviewer verdicts were not inspected. All review artifacts are on the external drive.

Raw executed command:

    PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -v -o /mnt/extdrive/workdir/htt_open_data/r25_blind_distance_envelope/raw.time python3 -B /mnt/extdrive/workdir/htt_open_data/r25_blind_distance_envelope/verify_archived_arithmetic.py > /mnt/extdrive/workdir/htt_open_data/r25_blind_distance_envelope/raw.stdout 2> /mnt/extdrive/workdir/htt_open_data/r25_blind_distance_envelope/raw.stderr

Observed command exit status 0; stderr empty; /usr/bin/time wall time 2.57 seconds; maximum RSS 17044 KiB. The internal elapsed field excludes final serialization and later subprocess completion; the raw time record is retained. Source seals were rechecked after execution without rerunning the arithmetic.

Source seals:

- `docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/distance_conditional_evidence/MANIFEST.json`: `735f35ad7b1cf3eab48abd5ded2e52dbceccb813f1caf504b35c9f058c4725fb`
- `docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-DISTANCE-CONDITIONAL-EVIDENCE_INPUT.json`: `77439c5b5966f6f0c6a4d4e2819b28b76b7a3c24523e9b08ec9f7e12fd5ca2b8`
- `docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/distance_conditional_evidence/RESULT.json`: `8977027b573794b3b85cc2cb4ff12491f553451f9572358ae92b0d0a99700a8b`
