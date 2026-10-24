# Proposed bounded proof and finite-check unit

Status: **PROPOSED, not dispatched or acknowledged**. This file is an executable handoff definition, not a controller packet or permission to modify historical tasks. A controller must assign its actual worker/output directory and any accounting debit before execution. The existing allocation/task ancestry, original acceptances, first failures, R9 UNKNOWN, and Gamma/PV/physical-functional HOLD states remain unchanged.

## Purpose and ownership

Verify the exact generic covariance-image and seven-channel gauge propositions from `DERIVATION.md`, then expose a small reusable matrix membership/support interface for a future qualified operator. The named consuming decision is: can the specified covariance class give finite conditional variance, and which output directions are structurally protected? No actual M7 exists in this input package, so actual CF4 rank/support numbers and original H02 remain unavailable.

Requested implementation worker: available lower-tier native `gpt-6.1-sol/medium`, or an explicitly recorded supported controller-selected lower-tier route. Requested and observed identities remain separate; unknown observation stays UNKNOWN. The theory/review owner remains read-only on implementation. No children. One writer owns only a new controller-assigned subdirectory under this external theory work root; the writer is not alone in the shared workspace and must preserve others' edits. No repository, Git, controller-state, existing evidence, native ODE, physical model, or completed adjacent-unit mutation.

Inputs are this derivation, this contract, the source response specification SHA `cdf94aaf6d39a01baae0d2fc03342032b1eb5f82ef34555e83ca8631d43f7992`, and primary source references in `CITATIONS.md`. Before execution the controller binds the actual final bytes of these two theory files in its existing handoff mechanism; no new permanent registry/gate is required. The covariance conventions and formulas below are frozen scientific choices. Missing source identity, ambiguity, or a substantive counterexample returns to the theory owner; do not change a bound or tolerance to obtain a passing test.

## Scope and hard limits

One implementation/test invocation, optional one targeted repair only after an explicit reviewer finding and bounded theory-owner definition. No fit, resampling, MCMC, random scientific ensemble, large-data scan, external source intake, package installation, actual CF4 run, physical inference, or numerical production response. Exact small fixtures first; matrix dimensions at most seven for the synthetic tests. One BLAS thread, cumulative check execution wall time at most 60 seconds including any authorized repair, RSS at most 512 MiB. Any controller-provided remaining allocation or stricter cap takes precedence; charge every started command that its existing policy charges. These bounds do not allocate/reset the historical source-response budget and do not assert a fabricated debit. If no compatible budget is available, prepare without running and return the exact constraint.

The worker may use the already installed project Python/SymPy/NumPy stack. Check availability once without installing; if a required package is absent, return that fact. No generic SDP solver is needed to test the closed-form results. Finite fixtures support implementation correctness, not universal theorem or four-axis CAS admission. Symbolic formula checks and exact rational constructions must be labeled according to their actual scope.

## Minimal interface

Preserve full signed M, full C/Gamma, source class identity, input units, rank semantics, and every cross block. The generic routines should compute only:

1. Exact-fixture cone membership `C PSD and range(C) subset range(M)` and the canonical lift `M^dagger C (M^dagger)^T`.
2. Exact-fixture trace-cap matrix membership using the range condition and `tr(canonical lift) <= tau^2`. A pseudoinverse cost alone is insufficient.
3. Loewner-cap matrix membership `0 <= C <= M G M^T`, with a lift obtained using `N=M G^(1/2)` when a square root is available.
4. Full-matrix support values for trace/spectral/Loewner/unbounded classes, plus a feasible attaining covariance or an explicit unbounded ray where given by the derivation.
5. Full-block congruence and fixed-direction known-marginal upper/lower bounds. The consumer must accept a stated complete PSD joint block rather than default missing cross blocks to zero.

Use separate statuses for an exact algebraic null, numerical near-null, absent covariance bound, unavailable physical map, and undefined input domain. In a floating interface, `rank at tolerance` is a diagnostic. An unbounded class must never get a finite upper variance from thresholding a small nonzero M^T u to zero. Do not create a physical Pi, posterior, x_C, F or G_F from these matrix interfaces.

## Required fixtures and exact expected outcomes

Every fixture is synthetic and declared as such. Test expectations below are derived here, not measurements.

| Fixture | Required result / defect caught |
|---|---|
| M=0 with C=0 and C=diag(1,0) | Only C=0 is in the cone; all output directions protected; avoids dividing by zero singular values |
| M=diag(1,0), C=[[2,0],[0,0]] | C is in the cone; canonical lift is diag(2,0); minimum latent trace is 2 |
| Same M, C=diag(0,1) | C fails the range test although canonical-lift cost is zero; no false trace-class admission |
| M=[1,1], C=[1] | Canonical lift is the 2-by-2 all-1/4 matrix, trace 1/2; adding t times the projector onto (1,-1), t>=0, preserves C and increases trace by t |
| M=I_2, trace cap 1, H=diag(2,-3) | Support 2, attained by diag(1,0); test negative/zero H also gives zero at Gamma=0 |
| Same M, H=I_2 | Trace-cap support 1; spectral-cap support 2; both directional maxima in e1,e2 are 1, but C=I_2 belongs only to the spectral class |
| Singular G=diag(4,0), M=I_2, H=diag(2,-3) | Loewner support 8; image contains diag(c,0) for 0<=c<=4, rejects nonzero second-axis covariance |
| M7=[I_5,0_5,-1_5], A7=I_7 | M7 1_7=0, rank five, M6 1_6=1_5, anchor column=-1_5; no protected output contrast despite gauge |
| M=[1,1], Gamma=[[1,rho],[rho,1]], rho=-1,0,1 | Variances 0,2,4; off-diagonal retention matters |
| M=[1/10^12], u=1, unbounded Gamma | Exact nonzero response, directional supremum +infinity despite being below 1e-10; a cutoff must not manufacture protection |
| Three scalar marginal variances 1,4,9 | Upper variance (1+2+3)^2=36; lower variance zero; construct PSD rank-one extremizers using coefficient vectors (1,2,3) and (1,2,-3) |
| Three scalar marginal variances 16,1,1 | Lower variance (4-1-1)^2=4; upper 36 |
| Two vector marginals diag(1,0), diag(0,1) | Directions (1,1) and (1,-1) require opposite cross correlations to attain upper 4; no simultaneous covariance maximizer |
| Full 3-by-3 correlation matrix, all off-diagonals -3/4 | Reject as non-PSD despite pairwise 2-by-2 PSD; exhibit eigenvector (1,1,1) with eigenvalue -1/2 |
| Two centered scalar laws: {-1,+1} equal weights; {0,-sqrt(2),+sqrt(2)} weights {1/2,1/4,1/4} | Same variance one, strict-tail Pr(|X|>1) respectively 0 and 1/2; covariance does not supply Pi |

Additionally check the trace identity and PSD lift on at least one nontrivial exact rectangular rank-deficient rational M with C=M K K^T M^T. Verify `range(C)` before trusting the pseudoinverse. Use a rational orthogonal row/column change or permutation to confirm covariance congruence and invariant trace membership in the fixed Euclidean coordinate convention. If using arbitrary nonorthogonal channel changes, transform the covariance-class metric too; an untransformed trace cap is a different scientific class.

No random numerical matrix sweep is required. For optional floating equivalents of exact fixtures, use rtol=1e-12, atol=1e-12 in the normalized synthetic units and preserve residuals; these are implementation tolerances only. An exact fixture failure is not repaired by widening them. The future CF4 application retains its original 1e-10 rank/algebra tolerance and saved-F rtol=1e-9/atol=1e-10; this contract does not amend that source task.

## Proof obligations beyond finite checks

The worker must map each executed fixture to the following statements without claiming finite tests prove them:

- PSD/range necessity and pseudoinverse sufficiency, including M=0 and singular covariance.
- Fixed row-space block and minimal trace among every PSD lift; range condition required separately; Loewner-image converse with singular G.
- Distinction between right-null channel gauge and left-null tensor contrast; direct-calibrator column identity.
- Variational trace/spectral/Loewner supports; explicit maximizers; pointwise versus joint attainment.
- Full Omega PSD, all cross terms, and marginal covariance attainment including zero projected variances; arbitrary covariance marginals versus specified full marginal laws.
- Unbounded possible total variance requires an admitted unbounded family such as the block-diagonal completion; cancellation does not establish a universal upper bound.
- Covariance-law nonuniqueness, unknown means, response/domain status, common-law functional coupling, and coverage versus Pi.

## Independent review and stop rule

Send the actual final candidate files, raw first output/error, elapsed-time/resource receipt from the runner, and exact diff to a fresh Astra-tier read-only reviewer who did not implement them. Requested review `gpt-6-astra/xhigh`; observed identity remains independently recorded or UNKNOWN. Do not send a prior verdict as evidence. The reviewer checks the formulas and counterexamples, source-contract compatibility, interface preservation of correlations/domains, exact versus numerical null semantics, and all claim ceilings. No full four-axis protocol is being claimed or replaced.

Stop on immutable input change, first substantive mathematical counterexample, ambiguous physical convention, missing required runtime/input, or the hard cap. Preserve the first failure before repair. One concrete authorized repair can return to the lower-tier worker and then to review within the same identity/accounting; do not restart/relabel exhausted work.

Required consuming outputs are the compact implementation/fixture checks, actual raw execution outcome, and an independent decision on this **generic mathematical interface only**. An implementation PASS does not close H02 or qualify actual M7. If all generic checks pass, the next dependency-safe transition is to await/consume a separately accepted actual seven-channel response, then classify its covariance image under an explicitly sourced class. Until that exists, the concrete missing input is `qualified signed M7 and stated bounded Gamma/Omega source`; a physical-functional continuation additionally requires the joint physical response/law/domain. Other independent authorized branches continue through the parent controller.
