# Independent blind contract review: R25 Gaia source quotient

Decision: **SCOPED_EXECUTABLE_CONTRACT — no blocking mathematical or source-binding finding.** This is a decision about the proposed conditional contract, not a numerical certificate, successful execution, parent completion, or scientific admission.

Reviewer assignment: /root/r25_blind_source_quotient_contract. Requested profile: gpt-6-astra/xhigh. Observed runtime: UNKNOWN. The reviewer did not author the proposal. No repo skill, harness verdict, author RETURN, or previous review verdict was used to establish correctness. The primary method text was treated as a proposition to check, including its explicit assumptions.

## Reviewed identity and evidence boundary

Reviewed proposal:
- INPUT.json SHA-256: 4df217b0798bbb247523dae173fc4026b966a6208496929477085305a44653ba.
- FRONTIER.json SHA-256: 76b6893c4c630774ceaf16820460aa6e267f21effdedf274b686b2c1f36611bc.
- METHOD.md SHA-256: 1fa32590a8e31d83caf08ecbb9f9fa08be92a54235911d74f2b157fc0197e25b.
- Declared base HEAD: d93605e66adfececa89b90681124b232a5f90220. This review does not assert that HEAD or controller STATE was independently refreshed.

Independently rehashed and matched the frozen parent INPUT, archived arrays, three source files, original manifest bytes, original raw receipt, relocation receipt, compute.py and package.py against the proposal. The array carrier resolves to the declared external packaged/arrays.npz and matches d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5.

Inspected actual NPZ headers for H, B, X, C, y, W, D, d, Cd and source_id. Shapes/dtypes/order agree after the ordinary tuple-versus-JSON-list normalization. In particular H is (9,13,9512), X is (4756,2,13), B is (4756,2,3), C is (4756,2,2), y is (4756,2), and W is (88,117). Inspected code establishes source-major tangent ordering, sorted source IDs, saved unit conversion, and covariance/geometry-only construction of H and W. No compute/package module was imported or executed.

This review read schema headers and source code; it did not calculate any archived matrix product, rank, eigenvalue, determinant, fit, statistic, interval, probability or quantile. Actual finiteness, source-block positivity, B rank, full/E1 ranks, delta and numerical certificate values remain future execution obligations. Hash equality and an inspected formula do not discharge them.

## Independent mathematical assessment

### 1. Exact nuisance quotient and nearest operator

With B of full column rank, R=(B^T B)^(-1) is symmetric and P=B R B^T is an orthogonal projector. Thus Q=I-P is symmetric/idempotent and QB=0. H_star=HQ therefore satisfies H_star B=0 identically. This is an algebraic identity under the certified inverse premise; it need not be demonstrated by a floating residual or by an interval computation fortuitously returning the singleton zero.

For any competing operator K with KB=0, KP=0 and K=KQ. Consequently

    ||H-K||_F^2 = ||HP||_F^2 + ||HQ-K||_F^2.

The orthogonal decomposition proves the stated unique minimizer K=HQ. This is a Euclidean source-coordinate Frobenius result. It supplies no claim of optimal physical weighting.

No bound on omega or beta is required. Under the explicitly assumed source law,

    E[W H_star Y] = W H_star X beta,
    Cov[W H_star Y] = W H_star C0 H_star^T W^T.

The proposal therefore derives the response law from a specified source law and operator. It does not silently declare the old rounded D/Cd law exact. Whether H_star differs nontrivially from H for the archived inputs is unmeasured; a newly explicit definition does not require inventing a measured difference.

### 2. Covariance, contractions and arithmetic

Expanding (H-J R B^T) C0 (H-J R B^T)^T gives exactly

    V - J R L - L^T R J^T + J R K R J^T,

using symmetry of C0 and R. The direct F_star route gives the identical covariance. All four mandatory correction identities are algebraically correct and retain the independently accumulated d versus Hy and D versus HX discrepancies. Rounded Cd is used only as a comparison, not as the new source covariance.

The source-block prerequisite must mean actual positive definiteness. For a symmetric 2 by 2 block [[a,b],[b,c]], an exact sufficient-and-necessary SPD check is a>0 and ac-b^2>0. A positive 2 by 2 determinant alone would accept -I and would not meet the existing positivity obligation. No change to the contract is required; this spells out the stated obligation for execution review. Nonsymmetric blocks explicitly cause HOLD; silent symmetrization is excluded.

For symmetric E=S_star-I, max_i sum_j |E_ij| is a valid spectral-norm upper bound. Interval entry magnitudes and their sums must be rounded outward. Algebraically known symmetry can justify this inequality even when a separately stored floating product is not exactly symmetric. The contract requires a bound on the exact target, not on an empirical residual.

Delta<1 is not mathematically necessary for every conservative upper-tail inequality, but it is a valid, explicitly chosen sufficient acceptance condition that also proves S_star positive definite. Failure of this particular condition is properly HOLD, not proof of a physical or mathematical impossibility. Neither a specific tiny whitening residual nor a particular multiplication order is required.

### 3. Complete model images and rank loss

Let V0 be the complete image of the first three columns and V1 the complete image of all thirteen columns. Then V0 is contained in V1 regardless of rank. For their orthogonal projectors, Q_model=P1-P0 is an orthogonal projector with rank

    k = dim(V1)-dim(V0), 0 <= k <= 10.

The bound follows because V1 adds only ten columns. A rank threshold that drops a small but nonzero mode does not establish either complete image. Positive-definite full Gram evidence would prove ranks 13 and 3; a rank-deficient branch instead needs a complete basis and dependence evidence, or it remains unresolved. The proposed policy makes that distinction correctly.

For a nonempty coefficient preimage, every beta0+ker(A_star) fiber is retained. A nonzero kernel prevents a bounded coefficient region. A projected mean ball remains meaningful without injectivity and without asserting that discarded directions vanish physically.

### 4. Delta tail, probability enclosure and mean ball

Under the matching E1 null, Q_model annihilates the mean. In an orthonormal basis of its range the covariance eigenvalues are at most 1+delta, giving

    Delta <=st (1+delta) chi-square_k <=st (1+delta) chi-square_10.

For k<10 the last step follows by adding independent nonnegative squared standard normals; for k=0, Delta is identically zero and the stated upper-tail p=1 is correct. There is no requirement to manufacture rank ten. A positive lower spectral bound supplies the corresponding lower domination when desired.

For L_Delta<=Delta_obs, using a nonnegative downward lower argument a<=max(0,L_Delta)/(1+delta_upper) and an upward survival value yields a conservative p-value. An interval whose lower endpoint is negative is compatible with a nonnegative exact statistic; max(0,L_Delta) is legitimate. A proved negative exact statistic would instead contradict the projector identities and must not be clipped into success. The proposal distinguishes these cases.

The even-degree survival polynomials and the stated exponential remainder bound are correct: beyond term N+1 successive ratios are bounded above by x/(N+2)<1. Rational evaluation and reciprocal interval inversion therefore give outward bounds. A lower argument must stay in the stated nonnegative domain, or a nonpositive argument must return survival 1 without applying the positive-domain polynomial formula. No general CAS or special-function stack is required.

An outward sf_88(q_U)<=1/20 proves the requested quantile upper bound. For arbitrary mean m the covariance domination gives at least 95% coverage of the exact-center ball. If the displayed center differs by at most eta, the triangle inequality justifies adding eta to the outward radius. Model rank is irrelevant to this mean-ball proof. No residual-independence/F-ratio conclusion is licensed. The contract correctly withholds df75/85 numerical probabilities unless their separate arithmetic is supplied; they are not prerequisites for Delta and the mean ball.

## Budget, execution transition and claim boundary

The frozen raw receipt's seven metrics match the proposed baseline: 7.44, 9.39, 7.38, 0.07, 10.88, 7.29 and 0.71 seconds, including both failed commands. Their total is 43.16 seconds. This establishes the historical snapshot only; it does not establish the live remaining budget.

The proposed scalar incremental cap is a cumulative allowance for this certificate work, not a fresh 120 seconds for each command, retry, control or review. The next dispatcher must reconcile all subsequent original-task numerical work and bound the remaining certificate work by BOTH the remaining incremental allowance and the remaining original 300-second allowance. Future reviewer arithmetic is charged; changing agent/task identity does not reset either allowance. Finite term/bisection caps and concrete command timeouts are ordinary pre-execution choices already required by INPUT.json:425, not a new scientific gate. No benchmark or successful 120-second completion is asserted.

FRONTIER.json:29-35 requires the parent R25-GAIA-PAIR-SEPARATION to be completed. I did not inspect controller STATE or establish that transition here. An execution-success RETURN alone cannot satisfy it, as the proposal already says. The original descriptive candidate can independently complete unchanged; this new numerical child cannot convert its own contract approval into parent completion.

Zero new pair passes, zero downloads, no original fit replay, one thread, RSS<=1GiB, no ultra and no candidate mutation are explicit. The allowed contraction alternatives avoid a 9512 by 9512 projector and do not require another pair traversal. Actual runtime and memory feasibility remain unmeasured. Exhaustion or an unproved arithmetic premise causes component HOLD.

Physical cross-source covariance, the post-selection source law, unrounded geometry/bin clearance and physical significance/coverage remain UNKNOWN or NOT_ESTABLISHED. All derived probabilities remain conditional on the finite Gaussian/C0 working model. Neither 17/42 nor analytic 18/42 is promoted. This contract is a substantive explicit observable/method proposal, with source-level nuisance annihilation and covariance propagation, rather than merely renaming an arbitrary rounded-response Gaussian proxy.

## Decision and falsifiers

No proposal repair is required before the next authorized transition, subject to the already stated parent-completion and live-accounting requirements. An actual certificate still requires bounded execution and fresh independent scrutiny of the produced arithmetic.

Concrete failures that falsify an attempted certificate include: a changed source/operator identity; a nonsymmetric or non-SPD source block admitted as valid; unproved B rank; use of a threshold-truncated model image; substituting saved D/Cd/M/z for exact source contractions; an inward probability/statistic/center-error bound; an unsupported arithmetic backend; or replenishing the cumulative allowance. The existing minimal response is to preserve the first evidence and report the affected HOLD component, with a bounded repair only under remaining authorized limits. None of these failures was demonstrated by this read-only contract review.

Only this external REVIEW.md was written. No scientific numerical command, pair pass, fit, implementation, candidate/STATE/Git edit or child-agent dispatch occurred.
