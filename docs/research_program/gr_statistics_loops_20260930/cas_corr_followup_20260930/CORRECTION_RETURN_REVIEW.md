# Corrected CAS return: bounded source review

Run reviewed: `GRSTAT-CAS-CORR-20260930-1420KST`.
Source publication: `11602167b64e4f0c50c1f57c37fe9df2292f9725`.

This is an independent read-only source review of the selected returned contracts, scripts and logs present in `intake/`. No CAS engine was executed during this review. It does not complete the registered local reviewer admission that `REVIEW_ROUTING.json` records as `NOT_COMPLETED` / `NO_SUPPORTED_WORKER_WITHIN_DECLARED_COST_SCOPE`. The review is source-informed, not blind, and does not certify unexamined files from the original 466-file manifest.

## Decisions

| Scope | Decision supported by inspected source |
|---|---|
| CAS03 exact / polynomial / truncated domain split | Accept the correction. The exact solve only needs invertible D; H_D=0 is allowed. Only the quotient truncation requires H_D nonzero. The polynomial identity alone does not define a quotient at H_D=0. |
| CAS03 corrected geodesic family | Accept the source repair: r_chi is spacelike, u_chi is timelike, and B u is directly checked. The old time-dyad substitution is no longer hidden by slope differencing. |
| CAS03 complete original contract | Remains open. These are explicitly reported focused diagnostics; general Lorentz eigenline/fibre and physical Taylor remainder obligations remain open. |
| CAS11 recursion cause | Accept the demonstrated implementation diagnosis. The self-referential Array head reproduces RecursionLimit while disjoint head/vector names do not. |
| CAS11 wrapper repair | Accept the observed nonzero-exit and missing-marker failure-path repair. Those paths now exit nonzero without synthesizing false scientific checks. This is not a guarantee covering every possible Wolfram message accompanied by an otherwise valid marker payload. |
| CAS11 arbitrary-dimensional mathematics | Remains open at the four-axis contract level. Fixed-dimensional diagnostics are labelled as such and cannot close the new universal components. |
| CAS13-C04 Wolfram and Lean scope | Full atomic statement is represented: every interval point, both endpoints, every real competing predictor, and L=U. Source and observed logs support these two axis results. |
| CAS13-C04 SymPy and Sage | Their inspected scripts still omit sign/branch implications; MISALIGNED_ASSUMPTIONS is correct. There is no mathematical obstruction found to completing these two finite certificates. |

No new mathematical counterexample was found in this bounded review. No original aggregate is overwritten, no whole parent contract is closed, and no physical or observational claim is promoted.

## CAS03 scope details

For h1_lin=-2 D beta, the exact identity is immediate from invertibility of D. With D=H_D I+Sigma, the denominator-free product identity is

`-(H_D I-Sigma) h1_lin/2 = (H_D^2 I-Sigma^2) beta`.

It holds at H_D=0 as a polynomial identity. Dividing requires H_D nonzero and yields `beta-beta_trunc=Sigma^2 beta/H_D^2`. For fixed nonzero shear the error can be first order in beta; the diagonal control returns 3t/4 instead of t, correctly exposing this.

The SymPy source checks the full symbolic six-entry symmetric matrix adjugate identity. Its `truncation_regular_branch` repeats the cross-multiplied polynomial identity, so domain enforcement comes from the contract rather than an executed invalid-domain API test. Its `general_six_rest_components` is only a parameter-count/nonidentical-trace diagnostic. Neither is a proof of the unresolved general Lorentz statement.

The Wolfram C02 script now uses r=(sinh chi,cosh chi,0,0), verifies u.u=-1, r.r=1, r.u=0, and B.u=0. Its key `wrong_Bu_nonzero` actually verifies `B_wrong u=-epsilon u_flat`; nonvanishing follows from the contract's epsilon>0 and unit timelike u. A future complete component runner should record that implication explicitly. This naming limitation does not invalidate the accepted family repair or justify whole-component promotion.

## CAS11 observed failure repair

`repro_self_reference.wl` contains `aa=Array[aa,3]`; its stored stdout contains `TerminatedEvaluation[RecursionLimit]` and the recursion-limit diagnostic. `repro_disjoint.wl` uses `aVec=Array[aSym,3]` and prints the intended three symbols. Both recorded processes exit zero, which demonstrates why exit code alone was insufficient.

`wolfram_wrapper.py` now requires zero engine exit, both markers, parseable JSON and a dictionary-valued checks field. Missing marker and nonzero exit produce exit 3 without a scientific JSON payload. The inspected stderr files show these two paths. Source review supports the narrow repair; this review did not rerun it.

`check_fixed.wl` still uses fixed finite dimensions, a special retained subspace, a diagonal rank-two example and a fixed-dimensional Cauchy identity. It also proves a three-point form different from the new C01 display; these forms are mathematically related, but the script does not explicitly establish the new complete target. The return correctly labels all of this diagnostic only.

## CAS13-C04 closure route

The Lean theorem quantifies real L,U with 0<L and L<=U, every m in the interval, and every real t. The stored axiom report lists `propext`, `Classical.choice`, `Quot.sound`, with no `sorryAx`; the stored execution exit is zero. The source represents `(a-x)/x` while the contract uses `a/x-1`; these are equal for x>0. This is a preserved proof rerun, not new independent authorship.

The Wolfram script uses quantified real implications for the same three targets and stored raw forms are all `True`. The earlier unpinned Lean version timeout is unrelated to mathematical validity; `OBSERVED_RUNTIME.json` separately records successful pinned Lean 4.31.0 preflight and execution.

Set A=2LU/(L+U), R=(U-L)/(L+U), with 0<L<=U. A complete finite certificate can verify these rational identities and their signs:

1. For L<=x<=U,
   `R-(A/x-1)=2U(x-L)/((L+U)x)` and
   `R+(A/x-1)=2L(U-x)/((L+U)x)`.
   Both right sides are nonnegative because every denominator is positive and both interval slacks are nonnegative. These prove the full uniform absolute-value bound.
2. At x=L and x=U, the signed errors are respectively R and -R; R>=0 gives both absolute endpoint equalities, including L=U.
3. Every real a satisfies a>=A or a<=A. In the first branch,
   `a/L-1=R+(a-A)/L>=R`;
   in the second,
   `1-a/U=R+(A-a)/U>=R`.
   Applying the appropriate signed lower bound on absolute value proves the endpoint maximum bound for all real competitors, including negative and zero competitors.

A program which only factors these identities and prints a success boolean has not discharged the order implications. Completion should explicitly check positive-denominator obligations, nonnegative products, the exhaustive competitor split, and the absolute-value inference. Polynomial positive-orthant certificates or an independently inspected small ordered-field certificate checker can do this; a general quantifier eliminator is unnecessary. The proof checker and its connection to the unchanged atomic contract must be reviewable.

No interval construction/coverage, floating-point error bound, physical application or other CAS13 component follows from this theorem.

## Minimal next action

Complete only CAS13-C04 SymPy/Sage certificate sources, then run the same atomic four-axis contract in a new local run. Retain the current CAS_CONFLICT as historical evidence. Do not rewrite the already-correct Wolfram/Lean proof bodies merely to manufacture fresh authorship. Whether a prior axis result can be reused is a runner/provenance policy decision; a fresh four-axis run is the cleanest source-aligned observation.

CAS03 physical remainder and CAS11 arbitrary-dimensional components can proceed separately; they are not mathematical dependencies of this interval theorem.
