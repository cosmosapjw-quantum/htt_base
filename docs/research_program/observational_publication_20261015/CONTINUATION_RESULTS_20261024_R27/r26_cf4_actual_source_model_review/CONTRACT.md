# Bounded next scientific unit: release-stage identification and anchor-aware response

This is a proposed executable research contract, not an acknowledged controller packet. Owner/controller retains dispatch, naming and bookkeeping authority. Requested preparation/execution worker: an available lower-tier native coding agent with explicit model/effort; requested and observed runtime remain separate. Fresh independent review follows actual execution. No children, extra ultra escalation, old-task relaunch, reset, completed adjacent science rerun, or controller modification is authorized by this document.

## Scientific question and distinct scope

Can the *released* table3 be represented by one common set of additive relative offsets and one absolute zero point, identified from singleton groups and then tested on untouched mixed-method groups? If so, what seven-channel calibration response does the fixed full E1 estimator have when the documented direct-calibrator branch is included?

This replaces the rejected assumption that an unbound notebook's exact coefficients generated the CDS release. It neither silently alters that frozen contract nor declares the original six-channel task completed. The source basis is CDS ReadMe table3 Notes 1–2 plus the primary paper's relative-method/absolute-anchor separation; the release-specific coefficient values are identified data summaries under explicit assumptions, not authoritative producer parameters. Mixed groups supply a deterministic held-out reconstruction check, not a statistically independent validation sample or coverage test.

## Immutable inputs and permitted outputs

Use the same local table2/table3/table4/ReadMe, selected NPZ, E1 result/model and runner source already bound by `FROZEN_INPUT_SOURCE_LAYOUT.json` SHA `bdb71210368d44cf4fc52e844d4d1e2577e07d306fb25a1de3d202c04b0e2adf`. Preserve full 35,970 ID order and SHA `f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88`, five STF columns, 14 nuisances, H0=74.6, Omega_m=.3153 and E1 D. Reuse the actual operator's source tokens, nominal weights and old-54 annotations where valid. Do not use its nonexistent witnesses as finite inputs.

Use one new additive worker-owned output directory inside the same existing external work root, assigned explicitly by the controller; no worktree/clone/repo source edits. Required consuming artifacts only: source/assumption input file, implementation plus focused tests, release identification/held-out result JSON, full cohort operator NPZ, signed response and concise report/plot, actual execution receipt. Old files remain byte-preserved. This review and its counterexample may be an input source to a genuinely new conditional frontier that depends on available published cohort H01; do not pretend the blocked old reconstruction goal is a passed prerequisite.

## Assumptions, conventions, and deterministic identification

For each rounding convention separately, use exact rational closed intervals of half a printed unit and one full printed unit. Do not broaden them. Error intervals must remain strictly positive. Missing mean/error values remain missing; counts never decide numeric availability. Channels are [SNIa,FP,TFR,SBFm,SBFir,SNII]. All quantities below are in mag unless otherwise marked.

For noncalibrator group g with q_gc=e_gc^−2 and A_gc=q_gc/sum(q_g), postulate:

    mu_av,g = sum_c A_gc (mu_gc + delta_c)
    e_av,g^2 = 1/sum_c q_gc
    mu_zp,g = mu_av,g - zeta

Fix delta_SNIa=0 as the reference convention supported by the source, and test its compatibility. Derive global parameters using **only rows with exactly one available numeric method pair** (the actual product reports 36,691); do not use the 1,134 multi-method groups to choose or revise parameters.

For each singleton row in method c, with intervals I_av, I_m, I_zp, require jointly:

    delta_c in I_av - I_m
    zeta in I_av - I_zp
    delta_c - zeta in I_zp - I_m.

These three interval-difference constraints are sufficient as well as necessary for one common latent mu_av per singleton: the three intervals for mu_av have pairwise intersections, hence a common intersection in one dimension. Independently require the source method-error and e_av intervals to intersect; singleton q is then realizable. Intersect constraints over all singleton rows. Denote the resulting method intervals D_c for delta_c, H_c for delta_c-zeta, and Z for zeta. Enforce D_SNIa={0} after checking its admissibility.

Compute the global feasible zeta interval exactly:

    Zstar = Z intersect intersection_c [D_c.low-H_c.high, D_c.high-H_c.low].

If any required interval is empty, any method has no singleton support, or an error interval fails, report the exact source witness and stop this model; no extra constants or sample cuts. Otherwise freeze zeta_star at the midpoint of Zstar and delta_c_star at the midpoint of D_c intersect (zeta_star+H_c), with delta_SNIa_star=0. This supplies a deterministic feasible *joint* representative and retains the complete singleton-identified constraint set. It is not a likelihood fit or statistical uncertainty estimate. Record the locked representatives before loading/evaluating mixed-group means.

## Held-out common-frame reconstruction

For each convention, use its single frozen delta_star/zeta_star for **every** group. For every multi-method row, solve the same exact local mean/error/DMzp feasibility problem as the previous consumer, now with these frozen values. Shared weights must simultaneously satisfy printed means, combined uncertainty, and target. Reuse the mathematically valid precision extrema/witness construction with explicit offset arguments; no per-group offset choices, midpoint substitution for intervals, or separate-mean/error false positives.

Report training and held-out counts, all actual failures and first raw witnesses, full-cohort selected statuses, and all 54 old exceptions without excluding them. A compatible midpoint representative proves existence for this stated reconstruction model. A failed representative rejects that representative only; do not claim the entire singleton-identified coefficient family is empty unless proved. Do not search another point in the family or retune on held-out data in this unit.

The two selected direct-calibrator rows must follow the ReadMe branch mu_zp=mu_cal and remain in their original selected positions; source equality was already directly observed. Their zero DMav/e_DMav tokens are structural, not zero distance or zero uncertainty. Do not pool them into the six-method weighted mean. Table4 errors remain the frozen E1 working errors, with table2 .180/.560 versus table4 .100/.100 discrepancy explicitly retained.

## Seven-channel conditional response

Proceed to response only if every selected noncalibrator row is jointly compatible under both conventions and the documented direct branch is valid. Otherwise return the actual scientific failure; do not manufacture M or mark this unit complete at a response acceptance that was not met.

Define seven *final calibrated channel perturbations* eta=(eta_1,...,eta_6,eta_cal), with conditional row map A7:

- Noncalibrator row: [A_g1,...,A_g6,0].
- Documented direct-calibrator row: [0,0,0,0,0,0,1].

These are explicit partial derivatives of two source-supported branches. The anchor row is complete and sums to one; it is not an unknown row filled with zero. eta_cal is a **common direct-calibrator-scale perturbation** only. Two maser measurement residuals and their correlations are not thereby represented by a single stochastic error or assumed independent. Keep those effects in an unresolved residual covariance block.

Construct both nominal A7 using printed method errors and compatible witness A7 from exact per-row witnesses. The nominal map is a working representative; it need not be the producer's actual map. Report both signed M7 matrices, not only their norms; do not call the witness unique or the difference a certified bound.

With Bw=D^−1/2 B, Nw=D^−1/2 N, P=I-Q_N Q_N^T and saved F=Bw^T P Bw, compute for each representative:

    M7 = F^−1 Bw^T P D^−1/2 A7.

Reuse the existing five-dimensional STF coordinate convention. Preserve saved-F agreement rtol=1e−9/atol=1e−10, scaled rank/algebra tolerance 1e−10, all 14 nuisances and no refit. Verify A7*1_7=1_n and M7*1_7≈0. **Do not require M6*1_6≈0** after excluding the seventh column: the two direct rows do not respond to simultaneous shifts of only the six other channels. Report nuisance-containment residuals and signed response ranks at the stated tolerance.

Gamma7 remains an arbitrary unknown PSD calibration covariance in mag^2, including all off-diagonal channel correlations; M7 Gamma7 M7^T is a conditional contribution, not an empirical covariance estimate. With epsilon for residual measurement/selection errors and v for peculiar velocities, write the full candidate covariance as the pushforward of Cov(epsilon,eta,v), including every cross block. Do not set calibration–velocity, measurement–calibration, measurement–velocity, or two-anchor residual correlations to zero by omission. The existing D is only a working diagonal reference. No finite numerical covariance bound is claimed without a stated bounded covariance class.

## Minimal tests, actual execution, budget and stopping rule

Focused tests must cover: the singleton joint-interval constraint reduction (including a pairwise-difference inconsistency); exact fixed reference; empty global interval; no-singleton channel; error-interval rejection; a mixed-row separate-interval false positive; a valid exact shared-weight witness; invariant PGC/column permutations; direct-calibrator row sums; M7 common-shift cancellation and the intentionally different M6 test; old-54 retention; full cohort identity and saved Fisher. These are a small suite, not a full test/consumer rerun from the old task. One production invocation and one render, followed by fresh independent result review; no fit, MCMC, nulls/mocks/draws, ODE/native solver, membership subset search, or new big data.

Honor the unchanged shared scientific allocation: actual baseline at least **103.50328065082431/600 seconds**, leaving at most **496.4967193491757 seconds** before later charges. One new invocation subcap is min(120 seconds, then-current remaining), one BLAS thread, RSS≤2 GiB. Charge every started execution according to the current controller; carry forward all task/allocation ancestry, earlier failures, attempt costs and one-use receipts. Source preparation/review timing must be reported without invented debit. Stop on exact immutable-source change, unknown scientific convention, exhausted budget, or substantive failure; return the concrete witness and continue independent DAG work through the parent.

## Acceptance and scientific ceiling

A scoped PASS requires compatible held-out reconstruction, complete 35,970-row seven-channel maps, actual full signed 5×7 nominal/witness responses, saved-F checks and independent review of the actual result. If any is absent, report the corresponding partial result/HOLD; do not equate useful negative evidence with completed-response acceptance. This new conditional component does not close old six-channel acceptance or original H02. Producer genealogy, upstream FP membership/count closure, empirical Gamma, full peculiar-velocity and cross covariance, source-null reproduction, physical x/F/Pi/Q/G_F, native solver and family-identification claims remain unresolved.
