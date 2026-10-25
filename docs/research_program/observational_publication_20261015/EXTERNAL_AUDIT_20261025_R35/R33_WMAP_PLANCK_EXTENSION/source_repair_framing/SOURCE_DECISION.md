# R33 quotient failure: source decision and one bounded repair specification

Preparation only, 2026-10-25. Owner: obsstat; claim tier C0; transfer source none. Requested framer gpt-6-astra/xhigh; observed runtime UNKNOWN. No actual research packet, ACK, or GO has been received for this framing. This is not a controller result, executed numerical repair, independent scientific acceptance, or four-axis CAS verification.

## Physics/math audit verdict

**One targeted numerical implementation repair is justified, conditional on real controller dispatch and the existing cumulative account. The cause of the recorded failure remains unmeasured.** Preserve R33 as HOLD until the repaired producer and independent checker supply the frozen evidence. No physical foreground obstruction or finite-model quotient success can be inferred from the assertion.

The verified source has a cancellation-prone evaluation of a mathematically valid projector: `produce.py:152` subtracts `U_r(U_r^T a)` from `a`; line 170 divides by `a^T p`. Near the nuisance span, the useful component is small and its squared norm appears in the denominator. This can amplify subtraction/orthogonality error into the nuisance constraint. The code does not explicitly form normal equations `G^T G`; calling this an observed normal-equations failure would be inaccurate.

There is also a definite evidence-loss defect: line 176 combines two checks without recording their components, and lines 178–182 populate residual fields only after both assertions pass. The only final write is at lines 304–306. Thus the actual failure provides neither the failed residual component nor matrices, singular values, principal angle, weights, or complete controls. Those quantities must be preserved before the repaired gate can fail.

## Assumptions and conventions

The controlling contract is `WMAP_PLANCK_F2_CONTRACT.md` SHA256 `986e558508ef7691d3286e9eb6cab48a38c9ded6645fe8c3e1486280a2e14686`; immutable scientific input SHA256 `d1ef7598449adff41ba8f950d048b5290efaf0f66ae056e61c8549544c763ce1`. Its 12/17 frequency rows, nine free signed F2 moments, Euclidean response geometry, SI constants, nominal detector averaging, signed tails, W0/W1 conventions, and all24 signed E2/E3/B2/B3 coordinates are unchanged. Metric/tetrad conventions are not active in this finite spectral calculation. Frequency is not depth.

The producer continues in IEEE binary64. All 201 nodes of every released detector curve and both WMAP branches remain; six accepted Planck branches provide their exact stored seven binary64 rows without reintegration. All twelve paired response conventions and both 12/17 systems remain in scope. No row noise, physical map response, extra foreground family, or alternative physical precision model is introduced.

## Equation and definition audit

| Item | Source finding | Required action |
|---|---|---|
| Column normalization | `G=F/scales`, lines 145–147, preserves the exact nuisance span. | Retain positive finite scales and raw F. |
| SVD shape and basis signs | Full U is already requested at line 148; complement columns are available. No source-level transposition or sign defect is established. | Use the complement explicitly; sign changes/orthogonal rotations cancel in the final projection. |
| Subtractive projection | Lines 152 and 170 evaluate a small complement and a small denominator through cancellation. | Replace with the orthogonal-complement formula below, in binary64. |
| Rank/angle rules | Resolved >=1e-10, unresolved <=1e-12, intermediate HOLD; angle gates unchanged. | Preserve spectra, classifications, and all boundary holds. |
| Confounding witness | Line 184 uses `lstsq` on unnormalized F with a fresh relative cutoff. Its effective rank need not equal the already classified normalized rank. This path did not cause the recorded quotient failure. | In the same normalized-factorization repair, construct the confounding witness from the retained normalized SVD and undo column scales. Do not choose a second rank cutoff. |
| Dust t and second t derivative | Lines 44–48 and 120–123 are algebraically consistent with t=(T-Td)/Td. | No derivative change; retain independent derivative controls. |
| Full24 nulling | Lines 167–177 check raw F, while line 176 additionally checks normalized G. Large raw column scales can matter. | Preserve both checks and their arrays; a normalized pass cannot replace the raw full24 gate. |
| Synthetic controls | Duplicate, injected-blackbody, rescaling, and explicit full24 blackbody action are present. Some checks can themselves fail numerically. | Keep their current thresholds and save inputs, spectra/residuals and failure identity before gating. No automatic control success. |
| Compression/lifting | C and C-transpose lifting follow the stipulated arithmetic averages. | Keep all basis-action checks and save raw and normalized response components before the existing gates. |

For the dust derivative, let L(t)=log[B_nu(Td(1+t))/B_nud(Td(1+t))], D=g(x)-g(xd), E=x g'(x)-xd g'(xd), g(x)=x/(1-exp(-x)). At t=0, L'=D and L''=-D-E, so dust''=dust*(D^2-D-E). This explains the existing sign and normalized-temperature factor; it is an analytic source check, not executed symbolic verification.

## Stable equivalent quotient formula

For the already computed normalized SVD G=U S V^T and resolved rank r, partition U=[U_r,Z]. Define z=Z^T a and rho=||z||2. In the quotient candidate r=9 and n is 12 or17. Evaluate

    d = rho / ||a||2
    q = z / rho
    w = (Z q) / rho

Only construct w when the existing rank and angle conditions permit it and rho is finite and positive. Use a stable vector norm implementation; do not form a small squared denominator or subtract nearly equal n-vectors. The projector need not be materialized. Save Z and z for the small diagnostic bundle so its shape and action are auditable.

In exact arithmetic, Z^T Z=I and P=ZZ^T, so a^T P a=z^T z and w=Pa/(a^T Pa). Also G^T w=0 and a^T w=1. It is the same minimum-Euclidean-norm constrained weight: every nuisance-null weight is Z v, and minimizing ||v|| subject to z^T v=1 gives v=z/(z^T z). With Z replaced by ZR for any orthogonal R, z becomes R^T z and w is unchanged. No sign convention is chosen to obtain a pass.

A schematic first-order comparison explains why this repair is justified: subtraction error of scale u||a|| can contribute to old constraint error with a factor proportional to 1/d^2, while direct complement construction avoids that particular subtraction and squared-small-denominator cancellation. Orthogonality, subspace conditioning, large ||w||, and final dot-product cancellation still limit the repaired computation. This is not an error bound or a diagnosis of the actual unrecorded branch. No condition number or d has been measured by this preparation.

For a confounding branch already allowed by the unchanged classification, use the same normalized SVD factors to form b=V_r S_r^-1 U_r^T a and c_j=b_j/scales_j. This is an ordinary factor-based solve, not normal equations, and uses exactly the rank already selected by the frozen rule. Preserve the existing raw reconstruction and all24 cancellation requirements. If the witness is inadequate, retain HOLD.

## One bounded lower-tier implementation/execution plan

1. Preserve the failed source, PREPARATION identity, failed attempt directory, RETURN, RAW_OUTCOME and OUTER_RAW. If the active producer file is edited, first retain its original bytes in a small immutable backup; never repoint the first attempt to the repair. Keep task/scientific-input/account ancestry. Only the controller chooses the bounded repair packet and new empty attempt location.
2. Change the normalized SVD kernel and quotient/witness construction as specified above. Do not reintegrate the seven Planck rows, change spectra/derivatives, add/drop nodes or rows, change precision, thresholds, branch ordering, or permitted moment amplitudes. No opportunistic fallback, iterative retry, alternate tolerance, or high-precision producer is included.
3. Before any scientific gate can raise or return HOLD, atomically persist the currently available matrices, factors and control measurements. Replace the lossy combined assertion with separately named unchanged checks whose values and thresholds are serialized first. A branch-local numerical failure remains HOLD; it may continue only through the other already frozen branches/controls within this same bounded invocation. Source/input identity failure, invalid denominator, nonfinite construction, timeout or memory breach stops the run with retained partial evidence. No failed branch may receive a resolved status.
4. Retain all existing independent source checks, detector normalization/RJ controls, derivative controls, exact old-row reuse, compression, synthetic controls and all24 actions. Serialize derivative-control values and source matrices as they become available instead of waiting until the final branch. Retain every first failing measurement, including a failure before quotient construction.
5. Prepare the corrected source and exact invocation without scientific imports or execution. Parent binds the new preparation/source hashes and real ACK/GO after account refresh. Then permit **one repaired producer invocation <=180s**, one thread, <=1GiB process RSS, MemAvailable>=4GiB and disk>=2GiB, under the existing enforced supervisor. No separate diagnostic run or SVD probe precedes it.
6. The already reserved **one independent checker <=180s** remains separate and does not import producer scientific code. It independently reconstructs new WMAP responses at 80 then120 decimal digits, retaining the accepted seven rows as exact binary64 rationals, and applies all frozen comparison and decision criteria. It should evaluate exported producer w against the exact promoted binary64 producer F/a as part of checking the existing residuals. Applying that same w to the independently assembled decimal-source matrix is an additional sensitivity diagnostic, not a replacement input or a newly invented tolerance gate. Any claimed producer residual disagreement must be reported, not averaged away.
7. The root obtains one independent scoped decision on the actual repaired candidate and checker evidence. A second producer failure or missing checker evidence leaves the exact HOLD payload; this preparation does not authorize another numerical repair, new bank, renamed attempt, or admission. Safe independent campaign work may continue.

## Required pre-gate diagnostic payload

For every processed convention, preserve exact Planck/WMAP branch labels and row count; 40 detector, 10 DA, 5 band and raw 12/17 matrices; column scales; full nuisance and augmented spectra; resolved/ambiguous classifications; U_r/Z dimensions and preferably the small factors; z, rho, d, angle; retained condition; w or c when constructible; and every applicable control's status and first failure.

For every candidate w, save the vector, ||w||2/1/infinity, w^T a, signed w^T a-1, raw w^T F, normalized w^T G, both nuisance norms, and the separate frozen comparison booleans. Retain HA-I residuals on all24 target bases and HB residuals on all216 nuisance bases; storing the full action matrices or factorization plus complete arrays is acceptable. Save actual binary64 input and weight values with round-trippable JSON floats, not rounded display strings. Nonfinite failures must be recorded explicitly with affected indices while keeping valid JSON.

For the 12-to-17 lift, save lifted coefficients, raw/normalized responses, unity residual, and all existing basis-action arrays. For confounding, save all nine coefficients, raw reconstruction residual vector/norm and all24 cancellation arrays. For synthetic controls, retain duplicate/injected/rescaled singular spectra where computed, ranks, injected witness/control residuals and full24 arrays. A reduced nuisance rank is still HOLD; a duplicate-control rank comparison cannot silently rescue it.

No old unstable weight is recomputed merely for comparison. No numerical probe is needed before the one repaired invocation. The independent checker can determine whether the repaired evidence satisfies the same original requirements; it cannot reconstruct the missing first-attempt residual from the original traceback.

## Dimensional/sign/limit checks and stop rule

The weights operate on dimensionless CMB-normalized responses; a is unity. Scaling a nuisance column leaves its exact span invariant. Exact rho=0 cannot produce a quotient weight. Reduced/ambiguous rank, threshold-straddling precision evidence, unresolved angle, nonfinite or failed residual/control remains HOLD under the original rules. The full24 action is conditional on common spatial response and shared free moment maps; factorization is not actual-sky evidence.

If stable float64 construction fails the frozen constraints, report the complete failing residuals, scales, spectra, d, weight gain and checker comparisons. The resulting missing input is a justified numerical-domain/precision decision for this same finite model; do not silently substitute high precision, a changed tolerance, regularization, row noise or a changed physical model. Actual ill-conditioning is possible and is not assumed away by this repair.

## Claim-tier implications, fatal blockers, and safe claims

Safe now: the first producer failed a combined quotient constraint; source inspection identifies a cancellation-prone evaluation and definite diagnostic loss; an algebraically equivalent complement evaluation is specified for one bounded repair. The actual numerical cause, rank, angle and residual values are UNKNOWN. No new numerical result has been computed.

Fatal admission blockers remain the absent successful producer/checker evidence and absent real map-response/noise/foreground qualification. Physical full (x,F,Pi,Q,G_F) remains undefined as in the original contract; x and observed tensor NOT_MEASURED, Q NOT_EVALUATED, F_physical NOT_EVALUABLE, Pi NOT_CALIBRATED, G_F NOT_APPLICABLE. Original L03/H02/H04/native-atlas acceptance remains HOLD. Real-data-only rank/noise/foreground tests are NOT_RUN. Finite response separation cannot establish family identification, a posterior, physical foreground completeness, or real-noise utility.

## Budget, ownership, and preparation evidence

Source review only; no numerical call, SVD, integration, producer import, solver, ODE, Git mutation, live STATE write, new checkout, child, or external scientific tool was used. Repository guidance was read through `htt-physics-math-audit`. A targeted memory search had no relevant R33 evidence and was not used for this decision. The equations above are derived directly from the frozen contract and inspected source; no new uncertain external method fact required a web fetch.

All new writes belong to `/mnt/extdrive/workdir/htt_open_data/r33_quotient_failure_framing`. The repository and producer files were read-only. Requested/observed identities are separate. No current checkout identity or runtime model observation was independently obtained here.

Preparation command/web ceiling is20s; no web call was made. Individual command tool receipts exist, but this agent has no complete independent outer-wall accounting total and does not claim zero administrative cost. Root accounts this preparation and any outstanding controller overhead against the existing seven900s frequency banks of R26-FULL7-STREAMED-SPIN2-QUADRATURE before dispatch. The historical first failure's external6.80s and internal5.862815350992605s are alternative nested measurements, not additive charges. Preserve the previous source-preparation/precharge60, all other existing costs and first failures; no refunds or new WMAP bank. SMICA is unchanged. The suggested producer/checker180+180s are caps, not an allocation or observed execution.

The paired PREPARATION_RESULT.json lists verified source/failure hashes and the exact dispatch wait state. Parent may include this terminal failure and prepared repair decision in an external audit as HOLD; publication does not activate a repair or promote science.
