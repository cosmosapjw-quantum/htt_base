# Independent covariance-cone mathematics review

Decision: **SCOPED_THEORY_PASS** for the generic, finite-dimensional mathematical statements and the bounded exact-fixture implementation contract. No blocking mathematical counterexample was found. This is a theory-component decision, not an implementation result, actual-M7 result, original-H02 admission, physical variance bound, probability-law qualification, controller acceptance, or historical four-axis CAS verdict.

Requested reviewer: `gpt-6-astra/xhigh`. Observed runtime identity: `UNKNOWN`; the requested profile is not runtime evidence. Review date: 2026-10-24. Independent read-only review; no other review verdict was read. Only this assigned review directory was written. No repository, author artifact, Git, controller, source array, production scientific test, ODE, or native-solver execution was modified or run.

## Exact scope and input binding

| Reviewed artifact | SHA-256 |
|---|---|
| `../r26_tensor_covariance_cone_theory/DERIVATION.md` | `3bf3a279384fb58fedeb01e7a8cf731c66979031a29f5ed44d2f26026b2d75ab` |
| `../r26_tensor_covariance_cone_theory/CITATIONS.md` | `48b311162c793aadeae98faf0830ca35a7f844dccedfad98790ea9ffbf24d6ff` |
| `../r26_tensor_covariance_cone_theory/LOWER_PROOF_FINITE_CHECK_CONTRACT.md` | `f94671b022b1254fc7999000e9129db8fb9903bb3b84b823ee1f8a14ab8348b0` |
| Controlling prospective source-response `../r26_cf4_actual_source_model_review/CONTRACT.md` | `cdf94aaf6d39a01baae0d2fc03342032b1eb5f82ef34555e83ca8631d43f7992` |

The source contract was read for response/gauge, units, qualification, tolerance and ceiling compatibility. No execution result or actual signed M7 was supplied by it. Relevant already-written report sections were read to compare reuse and functional domains; their checked hashes match the citation record:

- `REPORT_20261024_REV1/sections/07_mathematical_details.tex`: `9035b5f6bbac599c50c861110be730fb6678a2b112337e5935a3f686b23a1cd0`.
- `P1_SELECTED_TENSOR_LAW_20261024/sections/02_identification.tex`: `865712c29b5de95704b06622dd116e1b0548fc6abaf543abfaa033fa70f963bd`.
- `P1_SELECTED_TENSOR_LAW_20261024/sections/05_coupled_functionals.tex`: `515d934b7ae5b3ab284ea84900a8f5ed1743db2490d0fdea574218ba581e70d0`.

These report paths are relative to `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/`. This is a bounded overlap/domain comparison, not a repository-wide novelty search.

## Independent proof checks

### PSD image and unique minimum-trace lift

Take a compact SVD `M=U_r D V_r^T`, where D is positive diagonal, and complete V_r by an orthonormal basis V_0 of ker(M). In this basis write a PSD lift as

`[V_r,V_0]^T Gamma [V_r,V_0] = [[A,B],[B^T,E]]`.

Its output is exactly `U_r D A D U_r^T`. Thus a possible C is PSD and supported on range(M). Conversely, for every such C, `A=D^(-1) U_r^T C U_r D^(-1)` is PSD, and setting B=E=0 constructs a lift. This proves the entire cone equality, including the necessity of the range condition.

Every lift fixes A. Its trace is `tr(A)+tr(E)`, with E PSD. Hence the minimum is tr(A), reached by `Gamma_0=V_r A V_r^T=M^dagger C (M^dagger)^T`. At minimum E=0. PSD forces B=0: otherwise the quadratic form of `[x,t y]` has a nonzero term linear in t and no quadratic t term, and takes a negative value for one sign of sufficiently large t. Therefore the minimum-trace lift is unique. This independently proves Proposition 2a. With rank zero, M=0, the only feasible output is C=0 and its unique minimum-trace lift is zero. At tau=0, only zero Gamma is permitted and only zero C is in either bounded image.

The canonical-lift trace is not a standalone range test. The stated `M=diag(1,0), C=diag(0,1)` counterexample is exact. Arbitrary nonorthogonal channel changes also require changing the cap metric: under `eta'=A eta`, one has `M'=M A^(-1)`, `Gamma'=A Gamma A^T`, and the original trace cap becomes `tr(A^(-1) Gamma' A^(-T))<=tau^2`. An unchanged ordinary trace would define a different class.

### Singular Loewner image

Let `N=M G^(1/2)` and use its compact SVD `N=U_s D_s V_s^T`. If `0<=C<=NN^T`, then every vector in ker(N^T) has zero C quadratic form and hence lies in ker(C). Therefore C is supported on range(N). On that range,

`0 <= A_s=D_s^(-1) U_s^T C U_s D_s^(-1) <= I_s`.

Set `Z=V_s A_s V_s^T`, extended by zero on the remaining channel space, and `Gamma=G^(1/2) Z G^(1/2)`. Then `0<=Gamma<=G` and `M Gamma M^T=C`. The forward implication is congruence monotonicity. This proves the stated exact image without requiring G or M to be invertible or to commute. Zero G, zero M and rank-zero N all give the singleton zero image. The non-axis-aligned singular probe below checks a concrete instance, rather than only diagonal matrices.

### Support functions and attainable matrix sets

For every symmetric H, cyclicity gives `tr(H M Gamma M^T)=tr((M^T H M) Gamma)`. Diagonalizing the latter symmetric matrix proves the unbounded-cone and trace-cap rows: a positive eigenvalue supplies an unbounded PSD rank-one ray; absence of positive eigenvalues makes zero optimal; a trace cap allocates all allowed trace to a largest positive eigenvector. The zero choice is essential for negative H.

For the Loewner cap, write `Gamma=G^(1/2) Z G^(1/2)` with `0<=Z<=I`. In the eigenbasis of `G^(1/2) M^T H M G^(1/2)`, the objective is the sum of eigenvalues times diagonal entries between zero and one. The projector onto its strictly positive eigenspaces attains the sum of positive eigenvalues. This also proves the singular and spectral cases and their attaining lifts.

The distinction between the full matrix image and directional envelopes is substantive. With `M=I_2`, tau=1, the trace and spectral classes have identical upper values in every rank-one test `H=uu^T`, yet their supports at `H=I_2` are respectively 1 and 2. The matrix `I_2` belongs only to the spectral class. Thus independently optimizing each direction cannot reconstruct the trace-class covariance set. The derivation preserves this distinction correctly.

### Seven-channel gauge and protected contrasts

The source assumptions `A7 1_7=1_n` and `1_n in range(N)` imply that the whitened constant is annihilated by P, hence `L 1_n=0` and `M7 1_7=0`. Splitting off the anchor column gives `M6 1_6=-m_cal`, not zero in general. These are right-kernel channel identities. A protected output contrast is instead a vector in ker(M7^T); it is a left-kernel property.

The exact `M7=[I_5,0,-1_5]` fixture has rank five, has the seven-channel common-mode null, and has no nonzero protected output contrast. It is even compatible with the estimator form, rather than merely an arbitrary row map: choose D=I, nuisance span containing only the constant, and `B=L^T(LL^T)^(-1)` for this full-row-rank L. Then P B=B and `(B^T P B)^(-1) B^T P=L`. This does not supply a CF4 response.

For unbounded Gamma, every nonzero `v=M^T u` permits arbitrarily large variance. A small exact nonzero v remains unbounded; no floating rank threshold may change that statement. Structural common-mode cancellation does not certify other numerical nulls. The stated error-plus-trace-cap sensitivity bound follows directly from `||M^T u||<=||M_hat^T u||+epsilon ||u||`; epsilon requires independent justification and is not established by two representatives.

### Full block covariance and marginal extrema

The complete joint PSD Omega and all six cross terms are correctly retained. Pairwise PSD does not establish joint PSD; the stated correlation example has eigenvalue -1/2 along the all-ones vector. Exact cross cancellation also refutes any universal inequality `C_total>=M Gamma M^T`.

For fixed finite marginal covariances, write the projected contributions in L2. Their lengths are s_i. The triangle and reverse-triangle inequalities give the upper `sum(s_i)` and lower `max(2 max(s_i)-sum(s_i),0)` possible standard deviations. Vector segments of those lengths can align or form the required minimum-resultant polygon in a plane. Lifting these scalar projected variables to full marginals using `g_i=C_i a_i/s_i` is valid because `C_i-g_i g_i^T` is PSD and has zero projected variance. The zero-s_i branch needs no division. Thus both extrema are attained with exactly the prescribed full marginal covariance matrices. Prescribed full marginal distributions would be a stronger problem and are correctly excluded from this attainment claim.

The rank-two three-unit-segment probe checks a polygon-closure case beyond the collinear boundary examples in the proposed worker fixtures. The arbitrary-dependence upper bound and the warning about distinct projection extremizers already appear at lines 126–132 of the first report's section 07 and are explicitly credited here. The distinct proposed application is the exact response-specific matrix cone, latent trace-cost membership, bounded Loewner image and anchor-aware seven-channel gauge. No mathematical-foundations novelty follows.

### Tensor and joint-functional interpretation

The fourth-order tensor covariance construction and common-latent stacking across windows preserve full signed information. The support function describes a closed convex hull and does not define a law; the note correctly states this limit. Two equal-variance laws with different strict-tail probabilities suffice to refute deriving Pi from covariance alone.

The law-set construction keeps covariance, state/response assumptions and one common P together before applying a measurable joint map. It does not mix independently extremizing Q, F, Pi or G_F into one realizable law. The physical x_C conventions, U>0 normalization, separate eligibility of F, strict threshold, unknown-versus-undefined distinction, and retained undefined mass agree with the inspected P1 domains, subject to clarification 1 below. Confidence-set unions inherit coverage through membership of the true covariance/class member; they do not supply interior probability mass, a posterior or a physical response.

## Nonblocking clarifications

1. **Literal P1 floor domain.** `DERIVATION.md:184` describes the P1 floored ratio with `delta>0`; the registered P1 example in `02_identification.tex:78–84` specifies `0<delta<=1`. The ratio is mathematically defined for delta>1, but then it collapses to 1 for eligible fractions in [0,1]. For literal reuse retain `0<delta<=1`, or identify the broader positive-delta formula as a generalization. This does not affect any covariance theorem or the proposed matrix-only implementation.
2. **Scope of the final sentence at line 155.** Read “No finite uniform total bound follows from absent cross-block information” in its preceding context: the admitted class contains arbitrarily large Gamma and a block-diagonal completion. Absence of cross-block information alone does not preclude a finite bound when all marginal covariances are fixed and finite; Proposition 3 proves one. Adding “under this unbounded marginal class” would remove possible ambiguity. The preceding explicit construction and the paragraph's stated assumptions already justify the intended conclusion.

Neither clarification requires changing a mathematical acceptance threshold, source model or covariance class. No targeted code repair is requested by this review.

## Acceptable lower-tier finite-check contract

The exact contract with SHA `f94671b022b1254fc7999000e9129db8fb9903bb3b84b823ee1f8a14ab8348b0` is acceptable for the following narrow transition:

1. The controller assigns an actual lower-tier worker, owned output directory, final input-byte binding and available cumulative accounting. This review is not a dispatched packet and creates no budget or reset. Keep the contract's one execution, at most one separately authorized targeted repair, cumulative 60-second check cap, 512 MiB cap, single BLAS thread, dimensions at most seven and no children or package installation. Existing stricter limits take precedence.
2. Implement only the generic exact-fixture matrix membership/lift/support and complete-block covariance interfaces in lines 19–29. Rational or otherwise exactly decidable fixtures come first. If a symbolic sign, source identity or domain cannot be decided, return the precise unresolved condition instead of choosing a branch. A floating diagnostic must expose its tolerance and residual; it cannot establish structural protection or turn an unbounded answer finite.
3. Run all specified fixtures and the required nontrivial rectangular rational fixture. The existing contract permits the additional non-axis-aligned singular Loewner and three-unit polygon fixtures demonstrated here within the same cap; these are useful alternatives/additions, not a new mandatory gate. Zero tau/G/M and negative H must follow the explicitly proved zero cases, without division by zero or taking an eigenvector where none is needed.
4. Require exact support/membership semantics: verify symmetry and PSD, preserve the range condition before using a pseudoinverse cost, return a feasible maximizer or explicit unbounded ray where applicable, and distinguish one attainable full matrix from separate directional extrema. Nonorthogonal channel transformations either carry the class metric or are excluded from the unweighted-trace interface.
5. Require a complete declared joint PSD block for full covariance. Missing cross blocks remain missing. Do not infer Pi, physical x_C, eligible F or G_F, a posterior, or a physical mean/bias bound from these interfaces. If the registered P1 ratio is ever consumed in a later task, apply its exact domain as described above.
6. Preserve first raw output/error, actual execution time/resource evidence and final candidate identity, then obtain independent review of the actual implementation. Finite checks verify the implementation only; the proofs above carry the generic mathematics. No actual-M7 rank, empirical covariance, bounded physical variance, original-H02 completion, 42-node scientific completion, or historical four-axis result follows.

The next matrix application still needs a separately accepted signed M7 and a stated, source-qualified bounded Gamma/Omega class. Physical-functional application additionally needs its joint physical response, law and domain. Independent authorized branches may continue without waiting for these missing inputs.

## Independent exact probe record

The review's own `exact_review_probe.py` was executed once. It contains small exact synthetic algebra checks, not production implementation or universal theorem verification. Its eight groups include rank-deficient rectangular lift/trace decomposition; orthogonal and nonorthogonal coordinates; impossible range; non-axis-aligned singular Loewner lift; support examples; seven-channel gauge; exact near-null behavior; covariance extrema and incompatible directional maximizers.

Command: `env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 timeout 25s python3 exact_review_probe.py > exact_review_probe.stdout.json 2> exact_review_probe.stderr.txt`

Observed outcome: exit 0, eight groups passed, SymPy 1.14.0, internal elapsed `0.4140441450290382` seconds, tool elapsed `0.524333863` seconds, measured peak RSS `47796` KiB, stderr 0 bytes. The script set a 20-second CPU limit and 512 MiB address-space limit, and the command set a 25-second wall timeout. Whole-review wall time was not instrumented; no scientific allocation debit is invented. There was no failed/repaired execution.

## Reference verification limit

The current author-hosted [Semidefinite Programming record](https://stanford.edu/~boyd/papers/sdp.html) independently confirms Vandenberghe and Boyd, SIAM Review 38(1), 49–95, March 1996, and the linear-objective/affine-PSD formulation. The two web attempts to retrieve the book PDF from the supplied Stanford host and its web.stanford.edu alias timed out in this review. Consequently this reviewer does not independently reassert the book's exact page/index verification or downloaded-byte identity. The author's recorded earlier web verification and curl-403 limitation remain attributed historical preparation evidence. The self-contained independent algebra above does not depend on retrieving the PDF.
