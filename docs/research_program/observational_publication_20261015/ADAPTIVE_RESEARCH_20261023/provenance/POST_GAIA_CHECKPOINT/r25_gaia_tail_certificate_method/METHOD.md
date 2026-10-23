# Gaia finite-matrix tail-certificate method study

Status: METHOD_FEASIBLE_FOR_EXPLICIT_FINITE_RESPONSE_LAW; NOT_EXECUTED; NOT_INDEPENDENT_ADMISSION.
Requested Astra/xhigh; observed runtime UNKNOWN.
Read-only study: no production/pair traversal, fitting, numerical proof implementation, candidate/STATE/Git edits, or children. This external method note is not a new mandatory gate. The existing conditional diagnostic candidate may be reviewed unchanged.

## Frozen evidence and actual inspection

Repository branch research/htt-adaptive-methods-20261023, HEAD d93605e66adfececa89b90681124b232a5f90220; existing dirty/untracked state preserved.
Candidate sha256:0baef3b6b3fe45f459c1eb2476fbaa67ff47e4e824456ad7c67843da622c67c7.
Active frozen input bytes verified: sha256:620d92030d235ee6ed8fb5e6d7ff999f4777f7540abbcb1841c23af50e878d50.
RETURN's manifest_sha256 field is 441df34cae65acac1157e01809148a0a2d1010a51335a1a6d5e67bc7897e0d69; preserve its semantic role, not a newly observed manifest-byte digest.
MANIFEST inventory lists arrays.npz d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5 and RESULT.json ea603a35ccc95e78577ef1c20c695f14ab8ebffc1b48c299ac81623b8e8e5194. No large arrays rehashed.

Inspected active INPUT, RETURN, RESULT, REPORT, MANIFEST, RAW_RECEIPT, compute.py and package.py. No archived matrix algebra was run. Stored diagnostics:

- W has 88 rows in 117 response coordinates; covariance threshold counts 71/88/107.
- full13 singular extrema 0.06093891897962603 and 0.1631894200557531.
- E1 singular values 0.1560461047337004, 0.1450171638031867, 0.12754211543247837.
- T_E1=87.00260228836888; T_full=75.07862294730029; Delta=11.923979341068588.
- Empirical whitening residual 1.689145494493033e-13 after correction, initially 1.1503640740078012e-7: neither certified.
- Floating checks: max|d-Hy|=2.398081733190338e-14, max|D-HX|=2.55351295663786e-15, max|HB|=7.806255641895632e-17, covariance asymmetry=5.329070518200751e-15.

The model spectra make Gram positivity promising; they do not prove rank. Covariance threshold counts need not be stable to analyze the fixed declared 88-dimensional projection. No preservation of all original observable modes is asserted.

RAW_RECEIPT has one 11,307,390-pair pass, 43.16 cumulative numeric seconds, max RSS 165117952 bytes. It lists SEVEN numeric_command_metrics, not six: test_01,test_02,production_01,whitening_probe_01,package_01,package_02,typed_01. At that snapshot 256.84 of 300 seconds remain, subject to live reconciliation before future execution. No new numeric execution in this study.

## Exact target: finite response law versus source pushforward

Bars denote exact dyadic rational values represented by stored binary64 entries.

A. Minimal archive-identity-bound finite response proxy:

  C=(bar(Cd)+bar(Cd)^T)/2 exactly,
  M=bar(W)bar(D), z_obs=bar(W)bar(d), S=bar(W)C bar(W)^T,
  Z ~ N_88(M beta,S), beta unrestricted in R^13,

conditional on fixed design, projection and covariance. Symmetrization interprets a nonsymmetric rounded covariance record; it does not edit it. S positive definite suffices for this projected law. If a full 117-dimensional Gaussian law is additionally asserted, C PSD must also be certified. Stored M,z are rounded products and cannot silently replace the exact products.

A is feasible using small saved matrices. Its exact mean/covariance law must be explicit in the execution contract. It is not automatically an exact consequence of the source block-Gaussian model. The method author does not self-authorize that interpretation or scientific admission.

B. Literal finite source-block Gaussian pushforward:

  Y ~ N(bar(X)beta+bar(B)omega, blockdiag(bar(C_i))),
  Z=bar(W)bar(H)Y,
  M_H=bar(W)bar(H)bar(X), K_H=bar(W)bar(H)bar(B),
  S_H=bar(W)bar(H)blockdiag(bar(C_i))bar(H)^T bar(W)^T.

All can in principle be certified from archived source operators without another pair pass. However, norm-small D-HX and HB do not prove exact mean-image containment or spin annihilation with unrestricted beta and omega. A nonzero operator error times an unrestricted coefficient can be arbitrarily large. The floating nonzero HB check does not itself prove the exact product nonzero; the exact question is unresolved.

To obtain the original central references under B, prove the exact required mean-image containments, including nuisance K_H; or use exact M_H projectors and resolve nuisance treatment explicitly. Adding nuisance columns, changing W, bounding beta/omega, or changing the source law is a new scientific choice, not an arithmetic repair. Source-law B is not licensed by certifying A.

Unrounded analytic pair geometry is a third target. Its geometry/trigonometric/accumulation error and pair-bin boundary clearance are not certified by these finite matrices. No bridge to that target is claimed.

## Sufficient-condition theorem

Let r=88, M1 be fixed r by 13, M0 its first three columns, and S symmetric. Assume:

1. G1=M1^T M1 is positive definite. Thus full image dimensions are 13 and 3, with exact nesting.
2. A certified upper bound delta satisfies 0<=delta<1 and ||S-I||_2<=delta.
3. The relevant null is exactly Gaussian with its mean in the specified image. All observed statistic/evaluation error is enclosed.

Define exact projectors Pj=Mj(Gj)^(-1)Mj^T. Their symmetry, idempotence and image follow algebraically. Nesting yields P1 P0=P0=P0 P1, so Q=P1-P0 is a rank-10 orthogonal projector. Consequently

  T1=||(I-P1)Z||^2, T0=||(I-P0)Z||^2,
  Delta=T0-T1=Z^T Q Z>=0.

Under E1 null, Q mean=0. If U is an orthonormal basis for range(Q), Delta=||U^T epsilon||^2 with epsilon~N(0,S). The ten eigenvalues of U^T S U lie in [1-delta,1+delta]. Diagonalizing gives Delta distributed as sum(lambda_j*g_j^2), independent standard Gaussian g_j. Coupling using the same g_j proves

  (1-delta)chi2_10 <=st Delta <=st (1+delta)chi2_10.

Similarly T1 <=st (1+delta)chi2_75 under full13 null, and T0 <=st (1+delta)chi2_85 under E1 null. Delta is central ONLY under E1 null. These are marginal statements; delta>0 does not imply independence or justify usual F ratios. Exact chi-square laws require exact identity covariance on the applicable subspace.

For a certified observed enclosure L<=Delta_obs<=U, calculate a downward-rounded lower bound a<=max(0,L)/(1+delta_upper). An outward-rounded upper bound on sf_chi2_10(a), capped at 1, is a conservative conditional reference p-value. It dominates pointwise sf_chi2_10(Delta_obs/(1+delta_upper)); the latter is superuniform by stochastic domination. Analogous formulas use df75/85 only under their matching null.

For arbitrary projected mean m, ||Z-m||^2 <=st (1+delta)chi2_88. A certified q_U>=chi2_88(.95) gives at least 95% working-law coverage for

  {m: ||z_obs-m||^2 <= (1+delta_upper)*q_U}.

If displaying rounded center z_hat with certified ||z_hat-z_obs||<=eta, inflate radius to at least sqrt((1+delta_upper)*q_U)+eta using outward arithmetic. This joint mean ball does NOT need model-image/rank certification; model-specific tails do.

The coefficient preimage contains every fiber beta0+ker(M1). It is bounded only once ker(M1)={0} is certified for the exact target. If certified full rank, a finite conditional coefficient region becomes mathematically possible; it is still not physical coverage. If rank/kernel remains unproved, do not assert boundedness. In ambient R117, all ker(W) directions stay unconstrained. Since delta<1 proves W has row rank88, dim ker(W)=29; this does not label discarded modes exact null or physically absent.

## Proposed minimal implementation contract for A

Later lower-tier execution and fresh read-only review are required. Retain candidate arrays/files frozen. Produce a separate derived certificate and raw arithmetic evidence in the external allocation; parent decides publication/admission. No generic new gate.

1. Bind current input/candidate/inventory identities and validate shape/finite entries. Read only small saved members d,D,Cd,W,M,z. No compute/package main, pair geometry, eigenbasis rerun, or source refit.
2. Convert binary64 entries exactly to dyadic rationals. Form exact C,M,z,S. Common powers-of-two denominator scaling plus integer matrix products avoid repeated Fraction reductions. A verified interval alternative is acceptable only if its rounding/library premises and all operation bounds are established; extra precision alone is not certification.
3. Exact rational LDL^T of G1 with every pivot positive proves rank13. Its leading 3 by 3 Gram block proves rank3. A verified Cholesky/QR alternative must prove image completeness/invertibility, not just return a successful factorization or small residual. No numerical rank threshold substitutes.
4. Exact E=S-I is symmetric. Compute delta_inf=max_i sum_j abs(E_ij) as a rational. Then ||E||_2<=delta_inf. Require delta_inf<1; retain its actual value even if much larger than the empirical 1.69e-13. If the bound fails, stop with HOLD instead of silently altering W or the target.
5. Exact rational statistic evaluation uses b_j=Mj^T z and Tj=z^Tz-b_j^T Gj^(-1)b_j. Delta=T0-T1 is exact rational for this target. Compare archived floating values and emit outward decimal enclosures. Negative exact T/Delta indicates a defect and must not be clipped away. This certifies the declared LS functional, with no new model/optimization/source fit.
6. For df10 use sf_10(t)=exp(-t/2)*sum_{k=0}^4 (t/2)^k/k!. For df88 use the analogous sum through43. For rational x>=0 and N+2>x, let S_N=sum_{k=0}^N x^k/k!. Then exp(x) is between S_N and S_N+[x^(N+1)/(N+1)!]/[1-x/(N+2)]. Reciprocals enclose exp(-x) rigorously. Thus no general special-function library is required. Certify a quantile upper bound by sf_88(q_U)<=1/20. Freeze maximum terms/bisections before execution; failure to enclose is HOLD. Full residual df75/85 tails need a separately certified half-integer gamma/erfc evaluation or remain unissued; Delta and mean-ball certificates do not depend on them.
7. Controls should expose actual failure classes: exact full rank; rank-deficient M=(1,0) and unbounded fiber; small positive model mode [[1,1],[0,2^-44]] with unrestricted coefficients; exact S=1.5 I requiring inflation; indeterminate/failing bound branch; rounded center inflation; exact nesting identity. Reuse existing fixtures where obligations match; no production rerun.
8. Suggested single bounded attempt: incremental numerical allowance <=60 seconds, one thread, RSS<=1GiB, also bounded by remaining ORIGINAL 300-second cumulative cap. This planning allowance is not a benchmark guarantee. Count controls/failures/interruption and applicable review arithmetic; reconcile live total first. No new one-use pair pass, renamed task, reset costs or automatic ultra attempt.
9. Success is an independently reviewed, archive-identity-bound certificate for the explicit finite conditional law, recording Gram evidence, delta, statistic enclosure, conservative tails/quantile and center error. It does not validate real Gaia cross-source covariance, selected-law Gaussianity, physical significance, unrounded analytic geometry, native solver claims or original campaign acceptance.

## Exact outstanding assumptions and source-law route

If the next obligation specifically requires source-block law B, do not dispatch A as a substitute. Freeze its exact mean/nuisance interpretation first. Then verify C_i positivity, M_H/K_H/S_H products, exact required image containments and observed W H y statistic using archived H,C,X,B,y. This requires no pair traversal mathematically, but runtime and robust nuisance certification have not been measured here. A finite observed-y statistic discrepancy can be enclosed; that cannot prove mean-image equality uniformly in unrestricted beta/omega.

Missing for unrounded geometry: certified pair-bin clearance and accumulation/geometry error bounds. Actual source cross covariance and post-selection error law remain UNKNOWN independently of any arithmetic success. Retain the existing candidate TAIL_UNRESOLVED until any later certificate is actually executed, reviewed, and explicitly admitted in its narrow scope.

## Primary method sources

The Gaussian domination/fiber proof above is self-contained. A verified floating-point alternative is S. M. Rump, Verification of Positive Definiteness, BIT Numerical Mathematics 46 (2006), 433-452:
https://www.tuhh.de/ti3/paper/rump/Ru06c.pdf .
It addresses rounding and underflow; an ordinary successful Cholesky is not equivalent evidence.

Even-degree upper-gamma sums are NIST DLMF 8.4.10 and 8.4.11:
https://dlmf.nist.gov/8.4#E10 and https://dlmf.nist.gov/8.4#E11 .
Their statistical use is described at https://dlmf.nist.gov/8.23 .

These primary references were accessed after no directly relevant cached method source was located. No broad literature reanalysis. The initial shell heredoc could not create its temporary file because the root filesystem was full; this note was written directly via Python argv to the authorized external directory, without cleanup or candidate mutation.


## Preferred source-bound route: explicit exact spin-quotient observable

Controller-requested method refinement: prefer this route over target A. The rounded D,Cd response proxy is NOT the recommended next execution target. This addendum changes the proposed mathematical observable openly; it does not claim automatic equivalence to the existing candidate. No matrix computation was performed.

Let H,X,B,C0,y,W denote exact archived finite values, with C0 the block diagonal of saved C_i. Assume exact B^T B is positive definite, and define

  R=(B^T B)^(-1), P_B=B R B^T, Q_B=I-P_B,
  H_star=H Q_B,
  Z_star=W H_star Y,
  A_star=W H_star X,
  z_star_obs=W H_star y,
  S_star=W H_star C0 H_star^T W^T.

Keep W exactly the existing covariance-only projection. It need not be reselected or exactly whiten S_star; the new certificate measures its actual spectral departure from identity.

Under the SAME finite source working law Y~N(X beta+B omega,C0), with beta and omega both unrestricted,

  E Z_star=A_star beta, Cov Z_star=S_star,

because Q_B B=0 and H_star B=0 exactly. Thus arbitrary spin nuisance is removed algebraically, without a physically unsupported bound on omega and without inventing a Gaussian response law disconnected from source data.

P_B is the exact Euclidean orthogonal projector onto the archived spin design. H_star is the unique Frobenius-nearest operator to H among operators A satisfying A B=0: each row is projected onto range(B) perpendicular. Euclidean source-coordinate metric is an explicit fixed numerical convention, not a statement of optimal physical weighting. No 9512 by 9512 projector need be stored; apply its rank-three factors. The source covariance changes with the operator and MUST be propagated, rather than reusing rounded Cd as its exact covariance.

The declared full image is range(A_star) and E1 is its first three columns. If A_star^T A_star is certified positive definite, all existing theorem conclusions apply with M1=A_star, M0=A_star[:,:3], S=S_star and z=z_star_obs: Delta has the conservative chi2_10 reference only under E1; full/E1 residual degrees are 75/85; the arbitrary-mean ball has dimension88. This is an exact source-pushforward theorem for the finite archived model. The projected mean ball still needs no model-rank certificate.

A rank loss is a scientific discriminator of this observable. Do not remove small columns to manufacture df10. If full rank cannot be certified, return its exact/proved rank or unresolved status and preserve coefficient fibers. For a certified complete rank-deficient image, use actual q_full-q_E1 for Delta and r-q for residuals. Since the full model adds only ten columns to E1, k=q_full-q_E1<=10; once both COMPLETE projectors are certified, chi2_10 remains a conservative (possibly loose) upper domination even for k<10. State actual k explicitly. For k=0 Delta is identically zero and upper-tail p=1, never p=0.

### Frozen finite quantities to certify and corrections to report later

Use exact/verified source aggregates, not an assumed exact equality to saved D,Cd:

  J=H B, U=H X, v=H y, V=H C0 H^T,
  E_BX=B^T X, e_By=B^T y,
  L=B^T C0 H^T, K=B^T C0 B.

Then

  H_star X=U-J R E_BX,
  H_star y=v-J R e_By,
  C_star=V-J R L-L^T R J^T+J R K R J^T,
  A_star=W(H_star X), z_star=W(H_star y), S_star=W C_star W^T.

These low-rank expressions avoid constructing Q_B, avoid any pair traversal, and keep H,D,Cd and all source arrays intact. Exact symmetries of the 2 by 2 C_i must be checked, with their exact positivity; if nonsymmetric, stop and obtain an explicitly defined source covariance interpretation rather than silently symmetrizing the source law.

Report certified observed corrections to BOTH exact source-pushforward and saved-response quantities:

  z_star-W H y = -W J R e_By,
  z_star-W d = W(H y-d)-W J R e_By,
  A_star-W D = W(H X-D)-W J R E_BX,
  S_star-W sym(Cd) W^T = W(C_star-sym(Cd))W^T.

The second and third expressions include the independently accumulated d,D versus H y,H X discrepancy. For source observables, response values are defined by exact H_star y; stored old residuals cannot be promoted without certifying this new statistic and reporting the correction.

Optional useful norm bounds, all to be evaluated rigorously in a future run:

  F=W H, F_star=W H_star, DeltaF=F_star-F,
  ||DeltaF||_2 <= ||W H B||_2 / sigma_min(B),
  ||S_star-F C0 F^T||_2
    <= ||C0||_2 [2||F||_2 ||DeltaF||_2 + ||DeltaF||_2^2].

For fixed observed y, ||z_star-W H y||<=||DeltaF|| ||y||. Analogous bound with ||X|| controls model-matrix change, but exact A_star is used for the theorem; no uniform coefficient-bound assumption is introduced. These identities/bounds follow directly from the projector definition and two-product covariance expansion. The stored empirical tiny HB suggests a small correction, but provides no certified value; this study does not quantify it.

### Concrete bounded execution proposal for the source-bound route

One later source-bound execution and fresh independent review; same original R25 accounting, no pair pass, no re-download, no old fit replay, no candidate changes. This supersedes recommending the small saved-D,Cd proxy as the next target.

1. Freeze this new observable, Euclidean quotient convention, source-law interpretation and exact input identities in the execution packet. Bind H,B,X,C,y and original W. The array carrier has now been relocated by the root to external packaged/arrays.npz with the repository path a symlink; root reports original SHA d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5 unchanged, with receipt /mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/GAIA_ARRAY_STORAGE_RELOCATION.json. This method study has not independently rehashed it.
2. Check source C_i exact symmetry and positivity using 2 by 2 determinants. Prove B^T B SPD using exact 3 by 3 LDL. This supports the exact inverse R and exact null identity. Failure is HOLD with the exact object.
3. Compute verified aggregates U,v,J,V,E_BX,e_By,L,K and the low-rank expressions above. Exact integer arithmetic with common powers-of-two denominators is a possible route: keep raw source aggregates dyadic and introduce the 3 by 3 rational R only in the small contractions. V is the dominant cost (117 by 9512 source operator, block size2). It is not a small 117-dimensional-only task; runtime is unmeasured.
4. Verified outward interval matrix products are an alternative for V and other expensive aggregates, with rigorous dot-product rounding/underflow bounds and verified backend assumptions. Exact J can be useful because it is a cancellation quantity. No unconstrained floating-point residual is accepted as an enclosure. Source covariance positivity and interval propagation must cover the exact finite block covariance, never assume saved Cd exact.
5. Prove complete A_star image by exact Gram LDL or verified QR/Gram positivity with intervals. The existing full13 spectral margin is feasibility evidence only; it does not already establish A_star rank. If interval dependence obscures exact cancellation, preserve HOLD or use a preauthorized remaining-budget exact branch, never change rank thresholds.
6. Obtain a symmetric interval enclosure for S_star-I and an outward row-sum bound delta<1. This proves the needed covariance inequalities. No requirement that delta equal the old empirical residual. If it fails, report the value and stop.
7. Enclose z_star and exact least-squares quadratic forms through verified linear solves/projectors; include design, source-product, covariance, observed-response and solver errors. The exact-statistic formula from the theorem applies to the target A_star,z_star; interval use must cover every admissible exact pair consistently. Evaluate corrected chi2_10 tail and chi2_88 quantile with the finite rational exponential bounds above. Do not issue df75/85 probability values until their additional special-function enclosures are supplied.
8. Preserve correction norms/profiles, Gram/rank evidence and all failure outcomes. Tests need a deliberately contaminated operator H=H0+E with H0 B=0, verifying exact H_star B=0 and propagation of C0; a nonuniform/block covariance fixture; and a rank-loss fixture where projecting spin removes a source-model column, ensuring unbounded coefficient fiber and actual k are reported.
9. Freeze an incremental wall-time cap before dispatch (for example <=120 seconds) and enforce min(that cap, current remaining original 300 seconds). One thread and RSS<=1GiB remain. The 120-second figure is a proposed bound, not measured performance. All arithmetic attempts, controls, failures and applicable review computations count cumulatively. Time/memory exhaustion is HOLD; no unapproved alternative model or renamed allowance. Nothing in this method note authorizes an execution by itself.
10. Independently review the final source identities, new observable definition, exact/interval arithmetic premises, nuisance cancellation, complete model image, delta and probability enclosures. Only then can a scoped finite-source working-reference result be admitted. Existing original diagnostic candidate review remains independent and may complete unchanged.

Remaining scientific assumptions: fixed archived geometry/design and W; source Gaussian/block-independence proxy; no selection-induced law correction supplied; actual cross-source covariance UNKNOWN. The quotient does not certify the unrounded analytic pair kernel, bin stability or original Gaussian source law. These limitations stay explicit, even if every finite arithmetic certificate passes.
